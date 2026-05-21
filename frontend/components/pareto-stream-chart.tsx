"use client";


import dynamic from "next/dynamic";
import { useMemo } from "react";
import { useTheme } from "next-themes";

import { useAppStore } from "@/lib/store";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const PALETTE = {
  dark: {
    moep: "#22D3EE",
    nsga: "#34D399",
    moep_best: "#F472B6",
    nsga_best: "#FBBF24",
    constraint: "#F87171",
    text: "#F3F4F6",
    text_dim: "#9CA3AF",
    grid: "rgba(255, 255, 255, 0.08)",
    bg: "rgba(0, 0, 0, 0)",
    star_border: "#0B0F19",
  },
  light: {
    moep: "#0EA5E9",
    nsga: "#F97316",
    moep_best: "#0369A1",
    nsga_best: "#C2410C",
    constraint: "#B91C1C",
    text: "#1F2937",
    text_dim: "#6B7280",
    grid: "rgba(0, 0, 0, 0.08)",
    bg: "rgba(0, 0, 0, 0)",
    star_border: "#FFFFFF",
  },
};

export function ParetoStreamChart() {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";
  const p = isDark ? PALETTE.dark : PALETTE.light;

  const latestByAlgo = useAppStore((s) => s.latestByAlgo);
  const currentGen = useAppStore((s) => s.currentGen);
  const totalGen = useAppStore((s) => s.totalGen);
  const isSimulating = useAppStore((s) => s.isSimulating);
  const maxRiskPct = useAppStore((s) => s.maxRiskPct);
  const assets = useAppStore((s) => s.assets);
  const mode = useAppStore((s) => s.mode);

  const data = useMemo(() => {
    const traces: any[] = [];

    for (const [algoName, evt] of Object.entries(latestByAlgo)) {
      const isMoep = algoName === "MOEP";
      const color = isMoep ? p.moep : p.nsga;
      const bestColor = isMoep ? p.moep_best : p.nsga_best;

      traces.push({
        x: evt.population.map((i) => i.risk_pct),
        y: evt.population.map((i) => i.return_pct),
        mode: "markers",
        type: "scatter",
        marker: { color, opacity: 0.55, size: 9 },
        name:
          mode === "simple"
            ? `Portefeuilles testés (${algoName})`
            : `Front (${algoName})`,
        hovertemplate:
          "Risque: %{x:.2f}%<br>Rendement: %{y:.2f}%<extra></extra>",
      });

      traces.push({
        x: [evt.topsis.risk_pct],
        y: [evt.topsis.return_pct],
        mode: "markers",
        type: "scatter",
        marker: {
          color: bestColor,
          size: 22,
          symbol: "star",
          line: { color: p.star_border, width: 2 },
        },
        name:
          mode === "simple"
            ? `Meilleur choix (${algoName})`
            : `Compromis TOPSIS (${algoName})`,
        hovertemplate:
          "<b>Compromis TOPSIS</b><br>Risque: %{x:.2f}%<br>Rendement: %{y:.2f}%<extra></extra>",
      });
    }

    return traces;
  }, [latestByAlgo, p, mode]);

  const xMax = Math.max(...assets.map((a) => a.volatility_pct)) * 1.1;
  const yMax = Math.max(...assets.map((a) => a.expected_return_pct)) * 1.1;

  const layout = useMemo(
    (): any => ({
      title: {
        text: isSimulating
          ? mode === "simple"
            ? `L'IA cherche... étape ${currentGen}/${totalGen}`
            : `Convergence des fronts — Génération ${currentGen}/${totalGen}`
          : currentGen > 0
            ? mode === "simple"
              ? "Résultat final"
              : "Front de Pareto final"
            : mode === "simple"
              ? "Prêt à lancer la recherche"
              : "Espace de recherche bi-objectif",
        font: {
          color: p.text,
          size: 16,
          family: "Inter, system-ui, sans-serif",
        },
        x: 0.02,
        xanchor: "left",
      },
      xaxis: {
        title: {
          text:
            mode === "simple"
              ? "Niveau de risque (%)"
              : "Volatilité σ_p (%) — à minimiser",
          font: { color: p.text_dim, size: 12 },
        },
        range: [0, xMax],
        gridcolor: p.grid,
        zerolinecolor: p.grid,
        tickfont: { color: p.text_dim, size: 11 },
      },
      yaxis: {
        title: {
          text:
            mode === "simple"
              ? "Rendement attendu (%)"
              : "Rendement E[R_p] (%) — à maximiser",
          font: { color: p.text_dim, size: 12 },
        },
        range: [0, yMax],
        gridcolor: p.grid,
        zerolinecolor: p.grid,
        tickfont: { color: p.text_dim, size: 11 },
      },
      plot_bgcolor: p.bg,
      paper_bgcolor: p.bg,
      margin: { l: 60, r: 30, t: 60, b: 60 },
      showlegend: true,
      legend: {
        orientation: "h",
        x: 0.5,
        xanchor: "center",
        y: 1.12,
        font: { size: 11, color: p.text_dim },
        bgcolor: "rgba(0,0,0,0)",
      },
      shapes:
        maxRiskPct !== null
          ? [
              {
                type: "line",
                x0: maxRiskPct * 100,
                x1: maxRiskPct * 100,
                y0: 0,
                y1: yMax,
                line: { color: p.constraint, width: 2, dash: "dash" },
              },
            ]
          : [],
      annotations:
        maxRiskPct !== null
          ? [
              {
                x: maxRiskPct * 100,
                y: yMax * 0.95,
                xanchor: "left",
                text:
                  mode === "simple" ? "Limite sécurité" : "Contrainte σ_max",
                showarrow: false,
                font: { color: p.constraint, size: 11 },
                bgcolor: "rgba(0,0,0,0)",
              },
            ]
          : [],
      uirevision: "pareto-static",
      transition: { duration: 200, easing: "cubic-in-out" },
    }),
    [p, isSimulating, currentGen, totalGen, xMax, yMax, maxRiskPct, mode],
  );

  return (
    <div className="w-full h-[500px] animate-fade-in">
      <Plot
        data={data}
        layout={layout}
        config={{
          responsive: true,
          displayModeBar: false,
          displaylogo: false,
        }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
