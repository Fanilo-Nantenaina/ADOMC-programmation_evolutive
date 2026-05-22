"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAppStore } from "@/lib/store";

interface TooltipPayload {
  payload: { gen: number; f_max: number; f_mean: number; n_species: number };
  color?: string;
  name?: string;
  value?: number;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

function TrainingTooltip({ active, payload }: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0].payload;
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs shadow-lg space-y-0.5">
      <div className="font-semibold mb-1">Génération {d.gen}</div>
      <div className="font-mono">
        f_max : <span className="text-primary">{d.f_max.toFixed(4)}</span>
      </div>
      <div className="font-mono text-muted-foreground">
        f_mean : {d.f_mean.toFixed(4)}
      </div>
      <div className="font-mono text-muted-foreground">
        Espèces : {d.n_species}
      </div>
    </div>
  );
}

export function NeatTrainingChart() {
  const history = useAppStore((s) => s.neatTrainingHistory);
  const mode = useAppStore((s) => s.mode);

  const data = useMemo(
    () =>
      history.map((h) => ({
        gen: h.gen,
        f_max: h.f_max,
        f_mean: h.f_mean,
        n_species: h.n_species,
      })),
    [history],
  );

  if (data.length === 0) {
    return (
      <div className="h-70 flex items-center justify-center text-sm text-muted-foreground">
        {mode === "simple"
          ? "Lancez l'entraînement pour voir la courbe de progression."
          : "La courbe de fitness s'affichera ici une fois l'entraînement lancé."}
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart
        data={data}
        margin={{ top: 10, right: 16, bottom: 30, left: 36 }}
      >
        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" />
        <XAxis
          dataKey="gen"
          stroke="var(--muted-foreground)"
          tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
          label={{
            value: mode === "simple" ? "Étape d'apprentissage" : "Génération",
            position: "insideBottom",
            offset: -16,
            style: { fill: "var(--muted-foreground)", fontSize: 12 },
          }}
        />
        <YAxis
          stroke="var(--muted-foreground)"
          tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
          label={{
            value: "Fitness",
            angle: -90,
            position: "insideLeft",
            offset: -20,
            style: {
              fill: "var(--muted-foreground)",
              fontSize: 12,
              textAnchor: "middle",
            },
          }}
        />
        <Tooltip content={<TrainingTooltip />} />
        <Line
          type="monotone"
          dataKey="f_max"
          stroke="var(--moep-best)"
          strokeWidth={2.5}
          dot={false}
          name={mode === "simple" ? "Meilleur" : "f_max"}
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="f_mean"
          stroke="var(--moep)"
          strokeWidth={1.5}
          strokeDasharray="4 3"
          dot={false}
          name={mode === "simple" ? "Moyenne" : "f_mean"}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
