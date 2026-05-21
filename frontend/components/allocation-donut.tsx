"use client";

import { useMemo } from "react";
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface AllocationDonutProps {
  weights: number[];
  assetNames: string[];
  algorithm: string;
}

interface DonutDatum {
  name: string;
  value: number;
}

interface TooltipPayload {
  payload: DonutDatum;
  color?: string;
}

interface DonutTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
}

function DonutTooltip({ active, payload }: DonutTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const p = payload[0];
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs shadow-lg">
      <div className="font-semibold" style={{ color: p.color }}>
        {p.payload.name}
      </div>
      <div className="font-mono text-muted-foreground">
        {p.payload.value.toFixed(2)} %
      </div>
    </div>
  );
}

export function AllocationDonut({
  weights,
  assetNames,
  algorithm,
}: AllocationDonutProps) {
  const data: DonutDatum[] = useMemo(() => {
    return assetNames
      .map((name, i) => ({ name, value: (weights[i] ?? 0) * 100 }))
      .filter((row) => row.value > 0.1)
      .sort((a, b) => b.value - a.value);
  }, [assetNames, weights]);

  const baseColor = useMemo(() => {
    if (algorithm.includes("MOEP")) return "var(--moep)";
    if (algorithm.includes("NSGA")) return "var(--nsga)";
    return "var(--primary)";
  }, [algorithm]);

  const opacityScale = (idx: number, total: number) =>
    total <= 1 ? 1 : 1.0 - (idx / (total - 1)) * 0.55;

  return (
    <div className="w-full relative" style={{ height: 280 }}>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={data}
            cx="40%"
            cy="50%"
            innerRadius={55}
            outerRadius={95}
            paddingAngle={2}
            dataKey="value"
            nameKey="name"
            isAnimationActive
            animationDuration={500}
            stroke="var(--background)"
            strokeWidth={2}
          >
            {data.map((_, idx) => (
              <Cell
                key={idx}
                fill={baseColor}
                fillOpacity={opacityScale(idx, data.length)}
              />
            ))}
          </Pie>
          <Tooltip content={<DonutTooltip />} />
          <Legend
            verticalAlign="middle"
            align="right"
            layout="vertical"
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 11, paddingLeft: 16 }}
            formatter={(value) => (
              <span className="text-xs text-muted-foreground">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>

      {}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="text-center ml-[-10%]">
          <div className="text-xs font-bold text-foreground">{algorithm}</div>
        </div>
      </div>
    </div>
  );
}
