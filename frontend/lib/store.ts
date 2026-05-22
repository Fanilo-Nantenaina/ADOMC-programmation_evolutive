"use client";

import { create } from "zustand";
import type {
  AlgorithmChoice,
  AssetConfig,
  GenerationEvent,
  Mode,
  NeatInferResponse,
  NeatTrainEvent,
  Step,
} from "./types";

const DEFAULT_ASSETS: AssetConfig[] = [
  {
    name: "Actions tech US (croissance)",
    expected_return_pct: 35,
    volatility_pct: 42,
  },
  {
    name: "Actions tech mature (large-cap)",
    expected_return_pct: 22,
    volatility_pct: 25,
  },
  {
    name: "Actions cloud (blue-chip)",
    expected_return_pct: 18,
    volatility_pct: 22,
  },
  {
    name: "Actions Europe (diversifié)",
    expected_return_pct: 15,
    volatility_pct: 24,
  },
  {
    name: "Obligations d'État (long terme)",
    expected_return_pct: 4,
    volatility_pct: 6,
  },
  { name: "Or physique", expected_return_pct: 8, volatility_pct: 15 },
];

const EXTRA_ASSETS: AssetConfig[] = [
  {
    name: "Crypto (BTC dominant)",
    expected_return_pct: 55,
    volatility_pct: 75,
  },
  {
    name: "Immobilier (SCPI diversifiée)",
    expected_return_pct: 10,
    volatility_pct: 12,
  },
  {
    name: "Matières premières (énergie)",
    expected_return_pct: 14,
    volatility_pct: 30,
  },
  {
    name: "Devises (paniers majeurs)",
    expected_return_pct: 3,
    volatility_pct: 5,
  },
  {
    name: "Actions luxe européen",
    expected_return_pct: 16,
    volatility_pct: 20,
  },
  {
    name: "Actions semi-conducteurs (EU)",
    expected_return_pct: 24,
    volatility_pct: 28,
  },
];

function buildDefaultCorrelation(assets: AssetConfig[]): number[][] {
  const n = assets.length;
  const matrix: number[][] = [];
  for (let i = 0; i < n; i++) {
    const row: number[] = [];
    for (let j = 0; j < n; j++) {
      if (i === j) {
        row.push(1.0);
      } else {
        const isSafeHaven =
          /Or |Obligations|Devises|Immobilier/.test(assets[i].name) ||
          /Or |Obligations|Devises|Immobilier/.test(assets[j].name);
        row.push(isSafeHaven ? -0.1 : 0.55);
      }
    }
    matrix.push(row);
  }
  return matrix;
}

interface AppState {
  mode: Mode;
  setMode: (m: Mode) => void;

  step: Step;
  setStep: (s: Step) => void;

  assets: AssetConfig[];
  setAssets: (a: AssetConfig[]) => void;
  updateAsset: (idx: number, patch: Partial<AssetConfig>) => void;
  setNumAssets: (n: number) => void;

  correlation: number[][];
  setCorrelation: (c: number[][]) => void;
  updateCorrelationCell: (i: number, j: number, value: number) => void;

  algorithm: AlgorithmChoice;
  setAlgorithm: (a: AlgorithmChoice) => void;
  popSize: number;
  setPopSize: (n: number) => void;
  nGen: number;
  setNGen: (n: number) => void;
  seed: number;
  setSeed: (n: number) => void;
  maxRiskPct: number | null;
  setMaxRiskPct: (v: number | null) => void;
  wReturn: number;
  setWReturn: (v: number) => void;
  riskFreeRate: number;
  setRiskFreeRate: (v: number) => void;

  frameDelayMs: number;
  setFrameDelayMs: (n: number) => void;

  currentGen: number;
  totalGen: number;
  allEventsByAlgo: Record<string, GenerationEvent[]>;
  latestByAlgo: Record<string, GenerationEvent>;
  finalByAlgo: Record<string, GenerationEvent>;
  isSimulating: boolean;
  simulationError: string | null;
  abortController: AbortController | null;
  viewGen: number | null;
  setViewGen: (g: number | null) => void;
  setSimulating: (b: boolean) => void;
  setSimulationError: (s: string | null) => void;
  setAbortController: (a: AbortController | null) => void;
  pushEvent: (e: GenerationEvent) => void;
  resetSimulation: () => void;

  neatNGenerations: number;
  setNeatNGenerations: (n: number) => void;
  neatNScenarios: number;
  setNeatNScenarios: (n: number) => void;
  neatPerturbStrength: number;
  setNeatPerturbStrength: (n: number) => void;

  neatTrainingHistory: NeatTrainEvent[];
  isTrainingPolicy: boolean;
  policyError: string | null;
  policyAbortController: AbortController | null;
  hasPolicy: boolean;
  latestInference: NeatInferResponse | null;
  pushNeatEvent: (e: NeatTrainEvent) => void;
  setTrainingPolicy: (b: boolean) => void;
  setPolicyError: (s: string | null) => void;
  setPolicyAbortController: (a: AbortController | null) => void;
  setHasPolicy: (b: boolean) => void;
  setLatestInference: (r: NeatInferResponse | null) => void;
  resetTraining: () => void;
}

const DEFAULT_CORR = buildDefaultCorrelation(DEFAULT_ASSETS);

export const useAppStore = create<AppState>((set) => ({
  mode: "expert",
  setMode: (m) => set({ mode: m }),

  step: "config",
  setStep: (s) => set({ step: s }),

  assets: DEFAULT_ASSETS,
  setAssets: (a) => set({ assets: a }),
  updateAsset: (idx, patch) =>
    set((state) => ({
      assets: state.assets.map((a, i) => (i === idx ? { ...a, ...patch } : a)),
    })),
  setNumAssets: (n) =>
    set(() => {
      const ALL = [...DEFAULT_ASSETS, ...EXTRA_ASSETS];
      const clamped = Math.max(2, Math.min(n, ALL.length));
      const newAssets = ALL.slice(0, clamped);
      return {
        assets: newAssets,
        correlation: buildDefaultCorrelation(newAssets),
      };
    }),

  correlation: DEFAULT_CORR,
  setCorrelation: (c) => set({ correlation: c }),
  updateCorrelationCell: (i, j, value) =>
    set((state) => {
      const next = state.correlation.map((row) => [...row]);
      next[i][j] = value;
      next[j][i] = value;
      return { correlation: next };
    }),

  algorithm: "both",
  setAlgorithm: (a) => set({ algorithm: a }),
  popSize: 80,
  setPopSize: (n) => set({ popSize: n }),
  nGen: 50,
  setNGen: (n) => set({ nGen: n }),
  seed: 42,
  setSeed: (n) => set({ seed: n }),
  maxRiskPct: null,
  setMaxRiskPct: (v) => set({ maxRiskPct: v }),
  wReturn: 60,
  setWReturn: (v) => set({ wReturn: v }),
  riskFreeRate: 0.02,
  setRiskFreeRate: (v) => set({ riskFreeRate: v }),

  frameDelayMs: 150,
  setFrameDelayMs: (n) => set({ frameDelayMs: n }),

  currentGen: 0,
  totalGen: 0,
  allEventsByAlgo: {},
  latestByAlgo: {},
  finalByAlgo: {},
  isSimulating: false,
  simulationError: null,
  abortController: null,
  viewGen: null,
  setViewGen: (g) => set({ viewGen: g }),
  setSimulating: (b) => set({ isSimulating: b }),
  setSimulationError: (s) => set({ simulationError: s }),
  setAbortController: (a) => set({ abortController: a }),
  pushEvent: (e) =>
    set((state) => {
      const prev = state.allEventsByAlgo[e.algorithm] ?? [];
      return {
        currentGen: Math.max(state.currentGen, e.gen),
        totalGen: e.n_gen,
        allEventsByAlgo: {
          ...state.allEventsByAlgo,
          [e.algorithm]: [...prev, e],
        },
        latestByAlgo: { ...state.latestByAlgo, [e.algorithm]: e },
        finalByAlgo: e.is_final
          ? { ...state.finalByAlgo, [e.algorithm]: e }
          : state.finalByAlgo,
      };
    }),
  resetSimulation: () =>
    set({
      currentGen: 0,
      totalGen: 0,
      allEventsByAlgo: {},
      latestByAlgo: {},
      finalByAlgo: {},
      isSimulating: false,
      simulationError: null,
      viewGen: null,
    }),

  neatNGenerations: 40,
  setNeatNGenerations: (n) => set({ neatNGenerations: n }),
  neatNScenarios: 8,
  setNeatNScenarios: (n) => set({ neatNScenarios: n }),
  neatPerturbStrength: 0.15,
  setNeatPerturbStrength: (n) => set({ neatPerturbStrength: n }),

  neatTrainingHistory: [],
  isTrainingPolicy: false,
  policyError: null,
  policyAbortController: null,
  hasPolicy: false,
  latestInference: null,
  pushNeatEvent: (e) =>
    set((state) => ({
      neatTrainingHistory: [...state.neatTrainingHistory, e],
    })),
  setTrainingPolicy: (b) => set({ isTrainingPolicy: b }),
  setPolicyError: (s) => set({ policyError: s }),
  setPolicyAbortController: (a) => set({ policyAbortController: a }),
  setHasPolicy: (b) => set({ hasPolicy: b }),
  setLatestInference: (r) => set({ latestInference: r }),
  resetTraining: () =>
    set({
      neatTrainingHistory: [],
      isTrainingPolicy: false,
      policyError: null,
      latestInference: null,
    }),
}));
