
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
  frame_delay_ms: number;
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

export type Step = "config" | "theory" | "simulate" | "report" | "policy";

export interface NeatTrainRequest {
  assets: AssetConfig[];
  correlation_matrix: number[][];
  n_generations: number;
  n_scenarios: number;
  perturb_strength: number;
  w_return: number;
  risk_free_rate: number;
  seed: number;
  frame_delay_ms: number;
}

export interface NeatTrainEvent {
  gen: number;
  n_gen: number;
  f_max: number;
  f_mean: number;
  n_species: number;
  is_final: boolean;
}

export interface NeatStartPayload {
  n_gen: number;
  n_scenarios: number;
  n_inputs: number;
  n_outputs: number;
}

export interface NeatInferResponse {
  weights: number[];
  asset_names: string[];
  expected_return_pct: number;
  risk_pct: number;
  sharpe: number;
}

export interface NeatStatus {
  has_policy: boolean;
  asset_names: string[] | null;
  history: { max: number[]; mean: number[]; species: number[] } | null;
}
