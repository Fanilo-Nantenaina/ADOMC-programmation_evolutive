"use client";

import { create } from "zustand";
import type {
  AlgorithmChoice,
  AssetConfig,
  GenerationEvent,
  Mode,
  Step,
} from "./types";

const DEFAULT_ASSETS: AssetConfig[] = [
  { name: "NVDA", expected_return_pct: 35, volatility_pct: 42 },
  { name: "AAPL", expected_return_pct: 22, volatility_pct: 25 },
  { name: "MSFT", expected_return_pct: 18, volatility_pct: 22 },
  { name: "GOOGL", expected_return_pct: 15, volatility_pct: 24 },
  { name: "Obligations", expected_return_pct: 4, volatility_pct: 6 },
  { name: "Or", expected_return_pct: 8, volatility_pct: 15 },
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
          assets[i].name.includes("Or") ||
          assets[i].name.includes("Obligations") ||
          assets[j].name.includes("Or") ||
          assets[j].name.includes("Obligations");
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

  currentGen: number;
  totalGen: number;
  latestByAlgo: Record<string, GenerationEvent>;
  finalByAlgo: Record<string, GenerationEvent>;
  isSimulating: boolean;
  simulationError: string | null;
  abortController: AbortController | null;

  setSimulating: (b: boolean) => void;
  setSimulationError: (s: string | null) => void;
  setAbortController: (a: AbortController | null) => void;
  pushEvent: (e: GenerationEvent) => void;
  resetSimulation: () => void;
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
    set((state) => {
      const ALL = [
        ...DEFAULT_ASSETS,
        { name: "BTC", expected_return_pct: 55, volatility_pct: 75 },
        { name: "Immobilier", expected_return_pct: 10, volatility_pct: 12 },
        { name: "Pétrole", expected_return_pct: 14, volatility_pct: 30 },
        { name: "EUR/USD", expected_return_pct: 3, volatility_pct: 5 },
        { name: "LVMH", expected_return_pct: 16, volatility_pct: 20 },
        { name: "ASML", expected_return_pct: 24, volatility_pct: 28 },
      ];
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

  currentGen: 0,
  totalGen: 0,
  latestByAlgo: {},
  finalByAlgo: {},
  isSimulating: false,
  simulationError: null,
  abortController: null,

  setSimulating: (b) => set({ isSimulating: b }),
  setSimulationError: (s) => set({ simulationError: s }),
  setAbortController: (a) => set({ abortController: a }),
  pushEvent: (e) =>
    set((state) => ({
      currentGen: Math.max(state.currentGen, e.gen),
      totalGen: e.n_gen,
      latestByAlgo: { ...state.latestByAlgo, [e.algorithm]: e },
      finalByAlgo: e.is_final
        ? { ...state.finalByAlgo, [e.algorithm]: e }
        : state.finalByAlgo,
    })),
  resetSimulation: () =>
    set({
      currentGen: 0,
      totalGen: 0,
      latestByAlgo: {},
      finalByAlgo: {},
      isSimulating: false,
      simulationError: null,
    }),
}));
