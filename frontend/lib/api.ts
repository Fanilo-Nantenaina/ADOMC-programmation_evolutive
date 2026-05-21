import type {
  GenerationEvent,
  PSDValidationResult,
  SimulationRequest,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export async function validateCorrelation(
  assetNames: string[],
  volatilities: number[],
  correlationMatrix: number[][],
): Promise<PSDValidationResult> {
  const res = await fetch(`${BASE_URL}/api/validate-correlation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      asset_names: assetNames,
      volatilities,
      correlation_matrix: correlationMatrix,
    }),
  });
  if (!res.ok) {
    throw new Error(`Validation failed: HTTP ${res.status}`);
  }
  return res.json();
}

type SSEEventKind = "data" | "start" | "end" | "error";

export interface SSEStartPayload {
  n_gen: number;
  algorithms: string[];
}

export interface SSEErrorPayload {
  message: string;
}

type SSEParsed =
  | { event: "data"; data: GenerationEvent }
  | { event: "start"; data: SSEStartPayload }
  | { event: "end"; data: Record<string, unknown> }
  | { event: "error"; data: SSEErrorPayload };

function parseSSEEvent(rawBlock: string): SSEParsed | null {
  const lines = rawBlock.split("\n").filter((l) => l.length > 0);
  let event: SSEEventKind = "data";
  let rawData: string | null = null;

  for (const line of lines) {
    if (line.startsWith("event: ")) {
      const k = line.slice(7).trim();
      if (k === "start" || k === "end" || k === "error" || k === "data") {
        event = k;
      }
    } else if (line.startsWith("data: ")) {
      rawData = line.slice(6);
    }
  }

  if (rawData === null) return null;

  try {
    const parsed = JSON.parse(rawData) as unknown;
    return { event, data: parsed } as SSEParsed;
  } catch {
    return null;
  }
}

export interface SimulationCallbacks {
  onEvent: (e: GenerationEvent) => void;
  onStart?: (meta: SSEStartPayload) => void;
  onEnd?: () => void;
  onError?: (msg: string) => void;
}

export async function streamSimulation(
  req: SimulationRequest,
  cb: SimulationCallbacks,
  externalSignal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal: externalSignal,
  });

  if (!res.ok || !res.body) {
    throw new Error(`Simulation failed to start: HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      if (block.trim().length === 0) continue;
      const parsed = parseSSEEvent(block);
      if (!parsed) continue;

      switch (parsed.event) {
        case "start":
          cb.onStart?.(parsed.data);
          break;
        case "end":
          cb.onEnd?.();
          break;
        case "error":
          cb.onError?.(parsed.data.message ?? "unknown error");
          break;
        case "data":
          cb.onEvent(parsed.data);
          break;
      }
    }
  }
}

export interface AlgorithmExportPayload {
  weights: number[][];
  returns_pct: number[];
  risks_pct: number[];
  topsis: {
    best_idx: number;
    return_pct: number;
    risk_pct: number;
    sharpe: number;
    weights: number[];
  };
}

export interface IndicatorsExportPayload {
  hv: number;
  igd: number;
}

export async function exportReport(
  config: SimulationRequest,
  results: Record<string, AlgorithmExportPayload>,
  indicators?: Record<string, IndicatorsExportPayload>,
): Promise<Blob> {
  const res = await fetch(`${BASE_URL}/api/export-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ config, results, indicators }),
  });
  if (!res.ok) {
    throw new Error(`Export failed: HTTP ${res.status}`);
  }
  return res.blob();
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
