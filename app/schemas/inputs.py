from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AssetConfig(BaseModel):
    """A single asset with its expected return and volatility (in %)."""

    name: str = Field(..., min_length=1, max_length=64)
    expected_return_pct: float = Field(..., ge=-50.0, le=200.0)
    volatility_pct: float = Field(..., gt=0.0, le=200.0)


class CorrelationValidationRequest(BaseModel):
    """Validate a correlation matrix and detect PSD violations."""

    asset_names: List[str]
    volatilities: List[float]
    correlation_matrix: List[List[float]]


class SimulationRequest(BaseModel):
    """Full configuration for a portfolio optimization run."""

    assets: List[AssetConfig] = Field(..., min_length=2, max_length=20)
    correlation_matrix: List[List[float]]
    algorithm: Literal["moep", "nsga2", "both"] = "both"
    pop_size: int = Field(default=80, ge=20, le=200)
    n_gen: int = Field(default=50, ge=10, le=200)
    seed: int = Field(default=42, ge=0, le=99999)
    max_risk_pct: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    w_return: float = Field(default=60.0, ge=0.0, le=100.0)
    risk_free_rate: float = Field(default=0.02, ge=0.0, le=0.5)


class AlgorithmResults(BaseModel):
    """Final results for one algorithm (used in export)."""

    weights: List[List[float]]
    returns_pct: List[float]
    risks_pct: List[float]
    topsis: dict


class ReportExportRequest(BaseModel):
    """Export the simulation results to Excel."""

    config: SimulationRequest
    results: dict
    indicators: Optional[dict] = None
