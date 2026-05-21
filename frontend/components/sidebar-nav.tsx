"use client";


import {
  Settings2,
  BookOpen,
  Activity,
  FileText,
  Check,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";
import type { Step } from "@/lib/types";

interface StepDef {
  id: Step;
  labelExpert: string;
  labelSimple: string;
  description: string;
  icon: LucideIcon;
}

const STEPS: StepDef[] = [
  {
    id: "config",
    labelExpert: "Configuration",
    labelSimple: "Mes placements",
    description: "Actifs et corrélations",
    icon: Settings2,
  },
  {
    id: "theory",
    labelExpert: "Théorie",
    labelSimple: "Comprendre",
    description: "Fondements du modèle",
    icon: BookOpen,
  },
  {
    id: "simulate",
    labelExpert: "Simulation live",
    labelSimple: "Lancer l'IA",
    description: "Évolution en temps réel",
    icon: Activity,
  },
  {
    id: "report",
    labelExpert: "Rapport",
    labelSimple: "Recommandation",
    description: "Arbitrage et export",
    icon: FileText,
  },
];

const STEP_ORDER: Step[] = ["config", "theory", "simulate", "report"];

export function SidebarNav() {
  const step = useAppStore((s) => s.step);
  const setStep = useAppStore((s) => s.setStep);
  const mode = useAppStore((s) => s.mode);
  const isSimple = mode === "simple";

  const currentIdx = STEP_ORDER.indexOf(step);

  return (
    <aside className="hidden lg:block w-64 shrink-0">
      <div className="sticky top-6 space-y-1.5 rounded-2xl glass p-3">
        <div className="px-3 pt-2 pb-3 border-b border-border/40 mb-2">
          <div className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">
            Parcours
          </div>
          <div className="text-sm font-semibold text-foreground mt-0.5">
            {isSimple ? "4 étapes" : "Workflow décisionnel"}
          </div>
        </div>

        {STEPS.map((s, i) => {
          const Icon = s.icon;
          const isActive = s.id === step;
          const isCompleted = i < currentIdx;

          return (
            <button
              key={s.id}
              type="button"
              onClick={() => setStep(s.id)}
              className={cn(
                "group/step w-full flex items-start gap-3 px-3 py-2.5 rounded-lg text-left transition-all",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <span
                className={cn(
                  "shrink-0 flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold border",
                  isActive
                    ? "bg-primary-foreground/15 border-primary-foreground/30 text-primary-foreground"
                    : isCompleted
                      ? "bg-primary/10 border-primary/30 text-primary"
                      : "border-border text-muted-foreground group-hover/step:border-foreground/30",
                )}
              >
                {isCompleted ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Icon className="h-3.5 w-3.5 shrink-0" />
                  <span className="text-sm font-medium truncate">
                    {isSimple ? s.labelSimple : s.labelExpert}
                  </span>
                </div>
                <div
                  className={cn(
                    "text-[11px] mt-0.5 truncate",
                    isActive
                      ? "text-primary-foreground/70"
                      : "text-muted-foreground/70",
                  )}
                >
                  {s.description}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

export function StepperMobile() {
  const step = useAppStore((s) => s.step);
  const setStep = useAppStore((s) => s.setStep);
  const mode = useAppStore((s) => s.mode);
  const isSimple = mode === "simple";

  return (
    <div className="lg:hidden glass rounded-xl p-1 flex gap-1 overflow-x-auto">
      {STEPS.map((s, i) => {
        const Icon = s.icon;
        const isActive = s.id === step;
        return (
          <button
            key={s.id}
            type="button"
            onClick={() => setStep(s.id)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all",
              isActive
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-accent",
            )}
          >
            <span className="text-[10px] opacity-70">{i + 1}.</span>
            <Icon className="h-3.5 w-3.5" />
            <span>{isSimple ? s.labelSimple : s.labelExpert}</span>
          </button>
        );
      })}
    </div>
  );
}
