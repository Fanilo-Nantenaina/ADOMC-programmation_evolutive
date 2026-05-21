
export interface AssetConfig {
  name: string;
  expected_return_pct: number;
  volatility_pct: number;
}

export type AlgorithmChoice = "moep" | "nsga2" | "both";

export interface SimulationRequest {
  assets: AssetConfig[];
  correlation_matrix: number[][];
  algorithm: AlgorithmChoice;
  pop_size: number;
  n_gen: number;
  seed: number;
  max_risk_pct: number | null;
  w_return: number;
  risk_free_rate: number;
}

export interface IndividualSnapshot {
  return_pct: number;
  risk_pct: number;
}

export interface TOPSISSelection {
  algorithm: string;
  best_idx: number;
  return_pct: number;
  risk_pct: number;
  sharpe: number;
  weights: number[];
}

export interface GenerationEvent {
  gen: number;
  n_gen: number;
  algorithm: string;
  population: IndividualSnapshot[];
  topsis: TOPSISSelection;
  is_final: boolean;
}

export interface PSDValidationResult {
  is_valid: boolean;
  was_corrected: boolean;
  min_eigenvalue: number;
  corrected_matrix: number[][] | null;
  message: string;
}

export type Mode = "simple" | "expert";

export type Step = "config" | "theory" | "simulate" | "report";
