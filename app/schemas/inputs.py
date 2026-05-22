"""Pydantic request models."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AssetConfig(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    expected_return_pct: float = Field(..., ge=-50.0, le=200.0)
    volatility_pct: float = Field(..., ge=0.01, le=200.0)


class CorrelationValidationRequest(BaseModel):
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

    frame_delay_ms: int = Field(default=100, ge=0, le=2000)

    cardinality_max: Optional[int] = Field(default=None, ge=1, le=20)

    criteria_weights: Optional[List[float]] = Field(
        default=None, min_length=5, max_length=5
    )

    early_stop_enabled: bool = Field(default=False)
    stagnation_window: int = Field(default=10, ge=3, le=50)
    stagnation_eps: float = Field(default=1e-3, ge=1e-6, le=1.0)


class ExactFrontRequest(BaseModel):
    assets: List[AssetConfig] = Field(..., min_length=2, max_length=20)
    correlation_matrix: List[List[float]]
    n_points: int = Field(default=30, ge=5, le=100)


class ReportConfig(BaseModel):
    assets: List[AssetConfig]
    correlation_matrix: List[List[float]]
    algorithm: str
    pop_size: int
    n_gen: int
    seed: int
    max_risk_pct: Optional[float] = None
    w_return: float
    risk_free_rate: float
    frame_delay_ms: int = 100
    cardinality_max: Optional[int] = None
    criteria_weights: Optional[List[float]] = None


class ReportExportRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    config: ReportConfig
    results: Dict[str, Any]
    indicators: Optional[Dict[str, Dict[str, Any]]] = None
