"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import { useTheme } from "next-themes";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface AllocationDonutProps {
  weights: number[];
  assetNames: string[];
  algorithm: string;
}

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

export function AllocationDonut({
  weights,
  assetNames,
  algorithm,
}: AllocationDonutProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  const baseColor = useMemo(() => {
    if (algorithm.includes("MOEP")) return isDark ? "#22D3EE" : "#0EA5E9";
    if (algorithm.includes("NSGA")) return isDark ? "#34D399" : "#F97316";
    return isDark ? "#818CF8" : "#0F766E";
  }, [algorithm, isDark]);

  const filtered = useMemo(() => {
    return assetNames
      .map((name, i) => ({ name, pct: (weights[i] || 0) * 100 }))
      .filter((r) => r.pct > 0.1)
      .sort((a, b) => b.pct - a.pct);
  }, [assetNames, weights]);

  const data = useMemo(() => {
    const n = filtered.length;
    const colors = filtered.map((_, i) => {
      const alpha = n > 1 ? 1.0 - (i / (n - 1)) * 0.55 : 1.0;
      return hexToRgba(baseColor, alpha);
    });

    return [
      {
        labels: filtered.map((r) => r.name),
        values: filtered.map((r) => r.pct),
        type: "pie" as const,
        hole: 0.6,
        marker: {
          colors,
          line: { color: isDark ? "#0B0F19" : "#FFFFFF", width: 2 },
        },
        textfont: {
          color: isDark ? "#F3F4F6" : "#1F2937",
          family: "Inter, system-ui, sans-serif",
          size: 11,
        },
        sort: false,
        hovertemplate: "<b>%{label}</b><br>%{value:.2f}%<extra></extra>",
      },
    ];
  }, [filtered, baseColor, isDark]);

  const layout = {
    plot_bgcolor: "rgba(0,0,0,0)",
    paper_bgcolor: "rgba(0,0,0,0)",
    margin: { l: 10, r: 10, t: 10, b: 10 },
    showlegend: true,
    legend: {
      orientation: "v" as const,
      x: 1.0,
      xanchor: "right" as const,
      y: 0.5,
      yanchor: "middle" as const,
      font: {
        color: isDark ? "#9CA3AF" : "#6B7280",
        size: 11,
      },
      bgcolor: "rgba(0,0,0,0)",
    },
    annotations: [
      {
        text: `<b>${algorithm}</b>`,
        x: 0.5,
        y: 0.5,
        font: {
          color: isDark ? "#F3F4F6" : "#1F2937",
          size: 13,
          family: "Inter",
        },
        showarrow: false,
      },
    ],
  };

  return (
    <div className="w-full h-[280px]">
      <Plot
        data={data as any}
        layout={layout as any}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
