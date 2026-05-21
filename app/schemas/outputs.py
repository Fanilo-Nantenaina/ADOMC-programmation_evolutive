from typing import List, Optional

from pydantic import BaseModel


class PSDValidationResult(BaseModel):
    """Result of a correlation matrix validation."""

    is_valid: bool
    was_corrected: bool
    min_eigenvalue: float
    corrected_matrix: Optional[List[List[float]]] = None
    message: str


class IndividualSnapshot(BaseModel):
    """Single solution projected in F-space (returns/risk in %)."""

    return_pct: float
    risk_pct: float


class TOPSISSelection(BaseModel):
    """TOPSIS best-compromise selection at a given generation."""

    algorithm: str
    best_idx: int
    return_pct: float
    risk_pct: float
    sharpe: float
    weights: List[float]


class GenerationEvent(BaseModel):
    """SSE event payload streamed once per generation per algorithm."""

    gen: int
    n_gen: int
    algorithm: str
    population: List[IndividualSnapshot]
    topsis: TOPSISSelection
    is_final: bool = False


class FinalIndicators(BaseModel):
    """Quality indicators for the final fronts."""

    hv: float
    igd: float
