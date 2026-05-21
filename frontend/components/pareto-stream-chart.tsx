"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAppStore } from "@/lib/store";
import type { GenerationEvent } from "@/lib/types";

const CHART_HEIGHT = 480;

type Point = { x: number; y: number };

interface CustomShapeProps {
  cx?: number;
  cy?: number;
  fill?: string;
}

interface TooltipPayload {
  payload: Point;
  name?: string;
  color?: string;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

function StarShape(props: CustomShapeProps) {
  const { cx = 0, cy = 0, fill = "currentColor" } = props;
  const outerR = 11;
  const innerR = outerR / 2.4;
  const points: string[] = [];
  for (let i = 0; i < 10; i++) {
    const angle = (Math.PI / 5) * i - Math.PI / 2;
    const r = i % 2 === 0 ? outerR : innerR;
    points.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
  }
  return (
    <polygon
      points={points.join(" ")}
      fill={fill}
      stroke="var(--background)"
      strokeWidth={1.5}
    />
  );
}

function CircleShape(props: CustomShapeProps) {
  const { cx = 0, cy = 0, fill = "currentColor" } = props;
  return <circle cx={cx} cy={cy} r={5} fill={fill} fillOpacity={0.65} />;
}

function ChartTooltip({ active, payload }: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const p = payload[0];
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs shadow-lg">
      <div className="font-semibold mb-0.5" style={{ color: p.color }}>
        {p.name}
      </div>
      <div className="text-muted-foreground">
        Risque : <span className="font-mono">{p.payload.x.toFixed(2)} %</span>
      </div>
      <div className="text-muted-foreground">
        Rendement :{" "}
        <span className="font-mono">{p.payload.y.toFixed(2)} %</span>
      </div>
    </div>
  );
}

export function ParetoStreamChart() {
  const latestByAlgo = useAppStore((s) => s.latestByAlgo);
  const allEventsByAlgo = useAppStore((s) => s.allEventsByAlgo);
  const viewGen = useAppStore((s) => s.viewGen);
  const currentGen = useAppStore((s) => s.currentGen);
  const totalGen = useAppStore((s) => s.totalGen);
  const isSimulating = useAppStore((s) => s.isSimulating);
  const maxRiskPct = useAppStore((s) => s.maxRiskPct);
  const assets = useAppStore((s) => s.assets);
  const mode = useAppStore((s) => s.mode);

  const displayedEvents = useMemo(() => {
    const result: Record<string, GenerationEvent> = {};

    if (viewGen === null) {
      for (const [algo, evt] of Object.entries(latestByAlgo)) {
        result[algo] = evt;
      }
    } else {
      for (const [algo, list] of Object.entries(allEventsByAlgo)) {
        if (list.length > 0) {
          const idx = Math.min(viewGen - 1, list.length - 1);
          result[algo] = list[idx];
        }
      }
    }
    return result;
  }, [viewGen, latestByAlgo, allEventsByAlgo]);

  const { populations, picks } = useMemo(() => {
    const populations: Record<string, Point[]> = {};
    const picks: Record<string, Point[]> = {};

    for (const [algoName, evt] of Object.entries(displayedEvents)) {
      populations[algoName] = evt.population.map((i) => ({
        x: i.risk_pct,
        y: i.return_pct,
      }));
      picks[algoName] = [{ x: evt.topsis.risk_pct, y: evt.topsis.return_pct }];
    }
    return { populations, picks };
  }, [displayedEvents]);

  const xMax = Math.max(...assets.map((a) => a.volatility_pct), 10) * 1.1;
  const yMax = Math.max(...assets.map((a) => a.expected_return_pct), 5) * 1.1;

  const displayGen = viewGen ?? currentGen;
  const title = isSimulating
    ? mode === "simple"
      ? `L'IA cherche... étape ${currentGen}/${totalGen}`
      : `Convergence des fronts — Génération ${currentGen}/${totalGen}`
    : currentGen > 0
      ? mode === "simple"
        ? `Résultat à l'étape ${displayGen}`
        : `Front de Pareto — Génération ${displayGen}`
      : mode === "simple"
        ? "Prêt à lancer la recherche"
        : "Espace de recherche bi-objectif";

  const colorOf = (algo: string, kind: "pop" | "best") => {
    if (algo === "MOEP")
      return kind === "pop" ? "var(--moep)" : "var(--moep-best)";
    return kind === "pop" ? "var(--nsga)" : "var(--nsga-best)";
  };

  return (
    <div className="w-full animate-fade-in">
      <h3 className="text-base font-semibold text-foreground mb-1">{title}</h3>
      <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
        <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 60 }}>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />

          <XAxis
            type="number"
            dataKey="x"
            domain={[0, xMax]}
            tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
            stroke="var(--muted-foreground)"
            label={{
              value:
                mode === "simple"
                  ? "Niveau de risque (%)"
                  : "Volatilité σₚ (%) — à minimiser",
              position: "insideBottom",
              offset: -20,
              style: { fill: "var(--muted-foreground)", fontSize: 12 },
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={[0, yMax]}
            tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
            stroke="var(--muted-foreground)"
            label={{
              value:
                mode === "simple"
                  ? "Rendement attendu (%)"
                  : "Rendement E[Rₚ] (%) — à maximiser",
              angle: -90,
              position: "insideLeft",
              offset: -40,
              style: {
                fill: "var(--muted-foreground)",
                fontSize: 12,
                textAnchor: "middle",
              },
            }}
          />

          <Tooltip
            content={<ChartTooltip />}
            cursor={{
              stroke: "var(--muted-foreground)",
              strokeDasharray: "3 3",
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: 16 }}
            iconType="circle"
            formatter={(value) => (
              <span className="text-xs text-muted-foreground">{value}</span>
            )}
          />

          {Object.entries(populations).map(([algo, pts]) => (
            <Scatter
              key={`pop-${algo}`}
              name={
                mode === "simple"
                  ? `Portefeuilles (${algo})`
                  : `Front (${algo})`
              }
              data={pts}
              fill={colorOf(algo, "pop")}
              shape={<CircleShape />}
              isAnimationActive={false}
            />
          ))}

          {Object.entries(picks).map(([algo, pts]) => (
            <Scatter
              key={`best-${algo}`}
              name={
                mode === "simple"
                  ? `Meilleur choix (${algo})`
                  : `Compromis TOPSIS (${algo})`
              }
              data={pts}
              fill={colorOf(algo, "best")}
              shape={<StarShape />}
              isAnimationActive={false}
            />
          ))}

          {maxRiskPct !== null && (
            <ReferenceLine
              x={maxRiskPct * 100}
              stroke="var(--destructive)"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: mode === "simple" ? "Limite sécurité" : "σ_max",
                position: "top",
                fill: "var(--destructive)",
                fontSize: 11,
              }}
            />
          )}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
