from typing import List

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.exact_front import compute_exact_front
from app.core.psd import project_to_psd
from app.schemas.inputs import ExactFrontRequest

router = APIRouter()


class ExactFrontPoint(BaseModel):
    return_pct: float
    risk_pct: float
    weights: List[float]


class ExactFrontResponse(BaseModel):
    points: List[ExactFrontPoint]
    n_points: int
    method: str = "epsilon-constraint (SLSQP)"


@router.post("/exact-front", response_model=ExactFrontResponse)
async def exact_front(req: ExactFrontRequest) -> ExactFrontResponse:
    try:
        mu = np.array([a.expected_return_pct / 100.0 for a in req.assets])
        vol = np.array([a.volatility_pct / 100.0 for a in req.assets])
        corr = np.array(req.correlation_matrix, dtype=float)

        corr = (corr + corr.T) / 2.0
        np.fill_diagonal(corr, 1.0)
        cov = np.diag(vol) @ corr @ np.diag(vol)
        cov, _, _ = project_to_psd(cov)

        front = compute_exact_front(mu, cov, n_points=req.n_points)
        return ExactFrontResponse(
            points=[ExactFrontPoint(**p) for p in front],
            n_points=len(front),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute exact front: {e}",
        )
