import asyncio
import json
from typing import AsyncGenerator, Dict, List, Optional

import numpy as np
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.algorithm import Algorithm

from app.core.algorithms import MOEP
from app.core.indicators import compute_spacing, compute_spread, hv_for_stagnation
from app.core.problem import PortfolioProblem, decode_weights
from app.core.psd import project_to_psd
from app.core.topsis import (
    DEFAULT_DIRECTIONS,
    compute_criteria_matrix,
    topsis_nd,
)
from app.schemas.inputs import SimulationRequest

router = APIRouter()


def _build_covariance(
    volatilities: np.ndarray, correlation_matrix: np.ndarray
) -> tuple[np.ndarray, bool]:
    corr = (correlation_matrix + correlation_matrix.T) / 2.0
    np.fill_diagonal(corr, 1.0)
    cov = np.diag(volatilities) @ corr @ np.diag(volatilities)
    cov, _, was_corrected = project_to_psd(cov)
    return cov, was_corrected


def _build_algorithms(req: SimulationRequest) -> Dict[str, Algorithm]:
    algos: Dict[str, Algorithm] = {}
    if req.algorithm in ("moep", "both"):
        algos["MOEP"] = MOEP(pop_size=req.pop_size)
    if req.algorithm in ("nsga2", "both"):
        algos["NSGA-II"] = NSGA2(pop_size=req.pop_size)
    return algos


def _normalize_criteria_weights(raw: Optional[List[float]]) -> np.ndarray:
    """Frontend ships percentages — return a probability vector of length 5."""
    if raw is None:
        return np.array([0.35, 0.25, 0.20, 0.10, 0.10])
    w = np.asarray(raw, dtype=float)
    total = float(w.sum())
    if total < 1e-8:
        return np.array([0.35, 0.25, 0.20, 0.10, 0.10])
    return w / total


def _build_event(
    algo_name: str,
    gen: int,
    n_gen: int,
    algo: Algorithm,
    req: SimulationRequest,
    criteria_weights: np.ndarray,
) -> dict:

    pop = algo.pop
    X = pop.get("X")
    weights = decode_weights(X, cardinality_max=req.cardinality_max)
    returns_pct = (weights @ algo.problem.mu_vec) * 100.0
    risks_pct = np.sqrt(np.diag(weights @ algo.problem.cov_mat @ weights.T)) * 100.0

    criteria = compute_criteria_matrix(
        weights_matrix=weights,
        returns_pct=returns_pct,
        risks_pct=risks_pct,
        risk_free_rate=req.risk_free_rate,
    )
    best_idx = topsis_nd(
        criteria_matrix=criteria,
        weights=criteria_weights,
        directions=DEFAULT_DIRECTIONS,
    )

    population_payload = [
        {
            "return_pct": float(returns_pct[i]),
            "risk_pct": float(risks_pct[i]),
        }
        for i in range(len(weights))
    ]

    pick_weights = weights[best_idx]
    pick_return = float(returns_pct[best_idx])
    pick_risk = float(risks_pct[best_idx])
    pick_sharpe = (
        (pick_return / 100.0 - req.risk_free_rate) / max(pick_risk / 100.0, 1e-8)
        if pick_risk > 0
        else 0.0
    )
    pick_hhi = float(np.sum(pick_weights**2))
    pick_max_weight = float(np.max(pick_weights))

    F_pymoo = np.column_stack([-returns_pct, risks_pct])
    front_spacing = compute_spacing(F_pymoo)
    front_spread = compute_spread(F_pymoo)

    return {
        "algorithm": algo_name,
        "gen": gen + 1,
        "n_gen": n_gen,
        "population": population_payload,
        "topsis": {
            "best_idx": int(best_idx),
            "return_pct": pick_return,
            "risk_pct": pick_risk,
            "sharpe": float(pick_sharpe),
            "hhi": pick_hhi,
            "max_weight": pick_max_weight,
            "weights": [float(w) for w in pick_weights.tolist()],
        },
        "front_metrics": {
            "spacing": front_spacing,
            "spread": front_spread,
        },
        "is_final": (gen == n_gen - 1),
    }


async def _event_stream(req: SimulationRequest) -> AsyncGenerator[str, None]:
    try:
        mu = np.array([a.expected_return_pct / 100.0 for a in req.assets])
        vol = np.array([a.volatility_pct / 100.0 for a in req.assets])
        corr = np.array(req.correlation_matrix, dtype=float)

        cov, was_corrected = _build_covariance(vol, corr)
        if was_corrected:
            yield (
                f"event: warning\ndata: "
                f"{json.dumps({'message': 'Correlation matrix was non-PSD and has been projected.'})}\n\n"
            )

        problem = PortfolioProblem(
            mu_vec=mu,
            cov_mat=cov,
            max_risk=req.max_risk_pct,
            cardinality_max=req.cardinality_max,
        )

        criteria_weights = _normalize_criteria_weights(req.criteria_weights)

        algos = _build_algorithms(req)
        for name, algo in algos.items():
            algo.setup(problem, termination=("n_gen", req.n_gen), seed=req.seed)

        yield (
            f"event: start\ndata: "
            f"{json.dumps({'n_gen': req.n_gen, 'algorithms': list(algos.keys()), 'cardinality_max': req.cardinality_max})}\n\n"
        )

        vol_max_pct = float(vol.max()) * 100.0
        hv_history: Dict[str, List[float]] = {name: [] for name in algos}
        stagnation_counters: Dict[str, int] = {name: 0 for name in algos}
        converged: Dict[str, bool] = {name: False for name in algos}

        for gen in range(req.n_gen):
            for name, algo in algos.items():
                if converged[name]:
                    continue

                algo.next()
                event = _build_event(name, gen, req.n_gen, algo, req, criteria_weights)
                yield f"data: {json.dumps(event)}\n\n"

                if req.early_stop_enabled:
                    F = algo.pop.get("F")
                    current_hv = hv_for_stagnation(F, vol_max=vol_max_pct / 100.0)
                    hv_history[name].append(current_hv)

                    if len(hv_history[name]) > req.stagnation_window:
                        delta = (
                            hv_history[name][-1]
                            - hv_history[name][-req.stagnation_window - 1]
                        )
                        if abs(delta) < req.stagnation_eps:
                            stagnation_counters[name] += 1
                        else:
                            stagnation_counters[name] = 0

                        if stagnation_counters[name] >= req.stagnation_window:
                            converged[name] = True
                            yield (
                                f"event: converged\ndata: "
                                f"{json.dumps({'algorithm': name, 'gen': gen + 1, 'reason': 'stagnation'})}\n\n"
                            )

            if req.frame_delay_ms > 0:
                await asyncio.sleep(req.frame_delay_ms / 1000.0)
            else:
                await asyncio.sleep(0)

            if req.early_stop_enabled and all(converged.values()):
                break

        yield f"event: end\ndata: {json.dumps({'status': 'completed'})}\n\n"

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"


@router.post("/simulate")
async def simulate(req: SimulationRequest):
    """Stream a multi-objective portfolio optimization run via SSE."""
    return StreamingResponse(
        _event_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
