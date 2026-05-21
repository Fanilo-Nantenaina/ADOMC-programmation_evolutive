"use client";

import type { ReactNode } from "react";

interface MetricCardProps {
  icon?: ReactNode;
  label: string;
  value: string;
  hint?: string;
}

export function MetricCard({ icon, label, value, hint }: MetricCardProps) {
  return (
    <div className="rounded-lg glass p-4 transition-transform hover:-translate-y-0.5">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground font-semibold">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-2xl font-bold tracking-tight">{value}</div>
      {hint && (
        <div className="text-[10px] text-muted-foreground mt-0.5">{hint}</div>
      )}
    </div>
  );
}
