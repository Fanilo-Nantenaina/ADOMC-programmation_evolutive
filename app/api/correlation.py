import numpy as np
from fastapi import APIRouter, HTTPException

from app.core.psd import project_to_psd, EIGENVALUE_FLOOR
from app.schemas.inputs import CorrelationValidationRequest
from app.schemas.outputs import PSDValidationResult

router = APIRouter()


@router.post("/validate-correlation", response_model=PSDValidationResult)
async def validate_correlation(
    req: CorrelationValidationRequest,
) -> PSDValidationResult:
    n = len(req.asset_names)

    if len(req.volatilities) != n:
        raise HTTPException(
            status_code=400,
            detail=f"volatilities length {len(req.volatilities)} != asset_names length {n}",
        )
    if len(req.correlation_matrix) != n or any(
        len(row) != n for row in req.correlation_matrix
    ):
        raise HTTPException(
            status_code=400,
            detail=f"correlation_matrix must be {n}x{n}",
        )

    vol = np.array(req.volatilities, dtype=float)
    raw_corr = np.array(req.correlation_matrix, dtype=float)

    corr = (raw_corr + raw_corr.T) / 2.0
    np.fill_diagonal(corr, 1.0)

    cov = np.diag(vol) @ corr @ np.diag(vol)
    corrected_cov, min_eig, was_corrected = project_to_psd(cov)

    if was_corrected:
        corrected_corr = corrected_cov / np.outer(vol + 1e-12, vol + 1e-12)
        np.fill_diagonal(corrected_corr, 1.0)
        msg = (
            f"Matrice de corrélation non semi-définie positive "
            f"(λ_min = {min_eig:.2e}). Projection spectrale appliquée — "
            f"valeurs propres < {EIGENVALUE_FLOOR} clippées."
        )
        return PSDValidationResult(
            is_valid=False,
            was_corrected=True,
            min_eigenvalue=min_eig,
            corrected_matrix=corrected_corr.tolist(),
            message=msg,
        )

    return PSDValidationResult(
        is_valid=True,
        was_corrected=False,
        min_eigenvalue=min_eig,
        corrected_matrix=None,
        message=f"Matrice valide (λ_min = {min_eig:.4f}).",
    )
