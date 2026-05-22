from __future__ import annotations

import asyncio
import json
import os
import pickle
from threading import Lock
from typing import AsyncGenerator, List, Optional, Tuple

import neat
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core import neat_core
from app.core.psd import project_to_psd

router = APIRouter()

CONFIG_PATH = os.path.join(os.path.dirname(neat_core.__file__), "config-policy.txt")

_LATEST_POLICY: Optional[Tuple[neat.DefaultGenome, neat.Config, List[str]]] = None
_LATEST_HISTORY: dict = {"max": [], "mean": [], "species": []}
_POLICY_LOCK = Lock()


def _save_policy(
    genome: neat.DefaultGenome, config: neat.Config, asset_names: List[str]
) -> None:
    global _LATEST_POLICY
    with _POLICY_LOCK:
        _LATEST_POLICY = (genome, config, list(asset_names))


def _get_policy() -> Optional[Tuple[neat.DefaultGenome, neat.Config, List[str]]]:
    with _POLICY_LOCK:
        return _LATEST_POLICY


class AssetCfg(BaseModel):
    name: str = Field(..., min_length=1)
    expected_return_pct: float
    volatility_pct: float


class NeatTrainRequest(BaseModel):
    assets: List[AssetCfg]
    correlation_matrix: List[List[float]]
    n_generations: int = Field(default=40, ge=5, le=200)
    n_scenarios: int = Field(default=8, ge=1, le=32)
    perturb_strength: float = Field(default=0.15, ge=0.0, le=0.5)
    w_return: float = Field(default=60.0, ge=0.0, le=100.0)
    risk_free_rate: float = Field(default=0.02, ge=0.0, le=0.5)
    seed: int = Field(default=42, ge=0, le=99999)
    frame_delay_ms: int = Field(default=50, ge=0, le=2000)


class NeatInferRequest(BaseModel):
    assets: List[AssetCfg]
    correlation_matrix: List[List[float]]
    w_return: float = 60.0
    risk_free_rate: float = 0.02


def _build_covariance(
    volatilities: np.ndarray, correlation_matrix: np.ndarray
) -> np.ndarray:
    corr = (correlation_matrix + correlation_matrix.T) / 2.0
    np.fill_diagonal(corr, 1.0)
    cov = np.diag(volatilities) @ corr @ np.diag(volatilities)
    cov, _, _ = project_to_psd(cov)
    return cov


async def _train_event_stream(req: NeatTrainRequest) -> AsyncGenerator[str, None]:
    try:
        mu = np.array([a.expected_return_pct / 100.0 for a in req.assets])
        vol = np.array([a.volatility_pct / 100.0 for a in req.assets])
        corr = np.array(req.correlation_matrix, dtype=float)
        cov = _build_covariance(vol, corr)
        n_assets = len(req.assets)

        if n_assets > neat_core.MAX_N_ASSETS:
            yield f"event: error\ndata: {json.dumps({'message': f'Trop d actifs : NEAT supporte au plus {neat_core.MAX_N_ASSETS} actifs (reçu {n_assets}).'})}\n\n"
            return

        if not os.path.exists(CONFIG_PATH):
            yield f"event: error\ndata: {json.dumps({'message': f'Fichier config-policy.txt introuvable à {CONFIG_PATH}'})}\n\n"
            return
        config = neat_core.load_neat_config(CONFIG_PATH)

        scenarios = neat_core.generate_scenarios(
            base_mu=mu,
            base_vol=vol,
            base_cov=cov,
            n_scenarios=req.n_scenarios,
            perturb_strength=req.perturb_strength,
            seed=req.seed,
        )

        import random

        random.seed(req.seed)
        np.random.seed(req.seed)
        pop = neat.Population(config)

        stats = neat.StatisticsReporter()
        pop.add_reporter(stats)

        eval_fn = neat_core.make_eval_function(
            scenarios, req.w_return, req.risk_free_rate
        )

        yield f"event: start\ndata: {json.dumps({'n_gen': req.n_generations, 'n_scenarios': len(scenarios), 'n_inputs': neat_core.N_INPUTS, 'n_outputs': neat_core.N_OUTPUTS})}\n\n"

        history = {"max": [], "mean": [], "species": []}

        for gen in range(req.n_generations):
            best_genome = pop.run(eval_fn, 1)

            fitnesses = [
                g.fitness for g in pop.population.values() if g.fitness is not None
            ]
            if not fitnesses:
                continue

            f_max = float(max(fitnesses))
            f_mean = float(np.mean(fitnesses))
            n_species = len(pop.species.species)

            history["max"].append(f_max)
            history["mean"].append(f_mean)
            history["species"].append(n_species)

            event = {
                "gen": gen + 1,
                "n_gen": req.n_generations,
                "f_max": f_max,
                "f_mean": f_mean,
                "n_species": n_species,
                "is_final": (gen == req.n_generations - 1),
            }
            yield f"data: {json.dumps(event)}\n\n"

            if req.frame_delay_ms > 0:
                await asyncio.sleep(req.frame_delay_ms / 1000.0)
            else:
                await asyncio.sleep(0)

        if best_genome is not None:
            _save_policy(best_genome, config, [a.name for a in req.assets])
            global _LATEST_HISTORY
            _LATEST_HISTORY = history

        yield f"event: end\ndata: {json.dumps({'status': 'ok', 'final_fitness': history['max'][-1] if history['max'] else None})}\n\n"

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"


@router.post("/neat/train")
async def neat_train(req: NeatTrainRequest):
    """Stream NEAT training one generation at a time via SSE."""
    return StreamingResponse(
        _train_event_stream(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


class NeatInferResponse(BaseModel):
    weights: List[float]
    asset_names: List[str]
    expected_return_pct: float
    risk_pct: float
    sharpe: float


@router.post("/neat/infer", response_model=NeatInferResponse)
async def neat_infer(req: NeatInferRequest) -> NeatInferResponse:
    """Run the latest trained policy against a market state."""
    pol = _get_policy()
    if pol is None:
        raise HTTPException(
            status_code=400,
            detail="Aucune politique entraînée. Lancez d'abord /api/neat/train.",
        )
    genome, config, _trained_names = pol

    mu = np.array([a.expected_return_pct / 100.0 for a in req.assets])
    vol = np.array([a.volatility_pct / 100.0 for a in req.assets])
    corr = np.array(req.correlation_matrix, dtype=float)
    cov = _build_covariance(vol, corr)
    n_assets = len(req.assets)

    weights = neat_core.policy_to_allocation(
        genome,
        config,
        mu,
        vol,
        cov,
        req.w_return,
        req.risk_free_rate,
        n_assets,
    )

    portfolio_return = float(weights @ mu)
    portfolio_risk = float(np.sqrt(weights @ cov @ weights))
    sharpe = (
        (portfolio_return - req.risk_free_rate) / (portfolio_risk + 1e-8)
        if portfolio_risk > 0
        else 0.0
    )

    return NeatInferResponse(
        weights=[float(w) for w in weights.tolist()],
        asset_names=[a.name for a in req.assets],
        expected_return_pct=portfolio_return * 100,
        risk_pct=portfolio_risk * 100,
        sharpe=float(sharpe),
    )


class NeatStatusResponse(BaseModel):
    has_policy: bool
    asset_names: Optional[List[str]] = None
    history: Optional[dict] = None


@router.get("/neat/status", response_model=NeatStatusResponse)
async def neat_status() -> NeatStatusResponse:
    """Tells whether a policy has been trained in this process."""
    pol = _get_policy()
    if pol is None:
        return NeatStatusResponse(has_policy=False)
    _, _, names = pol
    return NeatStatusResponse(
        has_policy=True,
        asset_names=names,
        history=_LATEST_HISTORY if _LATEST_HISTORY["max"] else None,
    )
