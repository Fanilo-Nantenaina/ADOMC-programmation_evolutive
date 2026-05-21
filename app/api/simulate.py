import asyncio
import json
from typing import AsyncGenerator, Dict

import numpy as np
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.algorithm import Algorithm

from app.core.algorithms import MOEP
from app.core.problem import PortfolioProblem
from app.core.psd import project_to_psd
from app.core.topsis import weighted_topsis
from app.schemas.inputs import SimulationRequest

router = APIRouter()


def _build_covariance(
    volatilities: np.ndarray, correlation_matrix: np.ndarray
) -> np.ndarray:
    """Reconstruct PSD-projected covariance from volatilities and correlations."""
    raw_corr = (correlation_matrix + correlation_matrix.T) / 2.0
    np.fill_diagonal(raw_corr, 1.0)
    cov = np.diag(volatilities) @ raw_corr @ np.diag(volatilities)
    cov, _, _ = project_to_psd(cov)
    return cov


def _setup_algorithm(
    name: str, pop_size: int, problem: PortfolioProblem, n_gen: int, seed: int
) -> Algorithm:
    """Initialize one algorithm with explicit termination and setup."""
    if name == "moep":
        algo = MOEP(pop_size=pop_size)
    elif name == "nsga2":
        algo = NSGA2(pop_size=pop_size)
    else:
        raise ValueError(f"Unknown algorithm: {name}")
    algo.setup(problem, termination=("n_gen", n_gen), seed=seed)
    return algo


def _algo_display_name(internal: str) -> str:
    return "MOEP" if internal == "moep" else "NSGA-II"


def _build_event(
    internal_name: str,
    gen: int,
    n_gen: int,
    algo: Algorithm,
    req: SimulationRequest,
) -> dict:
    """Extract the population state and TOPSIS arbitration for the SSE payload."""
    pop = algo.pop
    F = pop.get("F")
    returns_pct = (-F[:, 0] * 100).tolist()
    risks_pct = (F[:, 1] * 100).tolist()

    best_idx = weighted_topsis(
        np.array(returns_pct),
        np.array(risks_pct),
        req.w_return / 100.0,
        (100.0 - req.w_return) / 100.0,
    )

    X_best = pop.get("X")[best_idx]
    weights = X_best / max(X_best.sum(), 1e-8)

    ret = returns_pct[best_idx]
    risk = risks_pct[best_idx]
    sharpe = (
        (ret / 100.0 - req.risk_free_rate) / (risk / 100.0 + 1e-8) if risk > 0 else 0.0
    )

    return {
        "gen": gen + 1,
        "n_gen": n_gen,
        "algorithm": _algo_display_name(internal_name),
        "population": [
            {"return_pct": float(r), "risk_pct": float(k)}
            for r, k in zip(returns_pct, risks_pct)
        ],
        "topsis": {
            "algorithm": _algo_display_name(internal_name),
            "best_idx": int(best_idx),
            "return_pct": float(ret),
            "risk_pct": float(risk),
            "sharpe": float(sharpe),
            "weights": [float(w) for w in weights.tolist()],
        },
        "is_final": (gen == n_gen - 1),
    }


async def _simulation_event_stream(req: SimulationRequest) -> AsyncGenerator[str, None]:
    """Async generator producing SSE-formatted event strings."""
    try:
        mu = np.array([a.expected_return_pct / 100.0 for a in req.assets])
        vol = np.array([a.volatility_pct / 100.0 for a in req.assets])
        corr = np.array(req.correlation_matrix, dtype=float)
        cov = _build_covariance(vol, corr)

        problem = PortfolioProblem(
            mu_vec=mu,
            cov_mat=cov,
            max_risk=req.max_risk_pct,
        )

        algos_to_run = []
        if req.algorithm in ("moep", "both"):
            algos_to_run.append("moep")
        if req.algorithm in ("nsga2", "both"):
            algos_to_run.append("nsga2")

        algos: Dict[str, Algorithm] = {
            name: _setup_algorithm(name, req.pop_size, problem, req.n_gen, req.seed)
            for name in algos_to_run
        }

        yield f"event: start\ndata: {json.dumps({'n_gen': req.n_gen, 'algorithms': [_algo_display_name(a) for a in algos_to_run]})}\n\n"

        for gen in range(req.n_gen):
            for name, algo in algos.items():
                algo.next()
                event = _build_event(name, gen, req.n_gen, algo, req)
                yield f"data: {json.dumps(event)}\n\n"

            await asyncio.sleep(0)

        yield f"event: end\ndata: {json.dumps({'status': 'ok'})}\n\n"

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"


@router.post("/simulate")
async def simulate(req: SimulationRequest):
    """Stream the portfolio optimization, one event per generation per algorithm."""
    return StreamingResponse(
        _simulation_event_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
