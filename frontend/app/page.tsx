"use client";

import { Hero } from "@/components/hero";
import { ThemeToggle } from "@/components/theme-toggle";
import { ModeToggle } from "@/components/mode-toggle";
import { SidebarNav, StepperMobile } from "@/components/sidebar-nav";

import { ConfigSection } from "@/components/sections/config-section";
import { TheorySection } from "@/components/sections/theory-section";
import { SimulateSection } from "@/components/sections/simulate-section";
import { ReportSection } from "@/components/sections/report-section";

import { useAppStore } from "@/lib/store";
import type { Step } from "@/lib/types";
import { JSX } from "react";

const SECTIONS: Record<Step, () => JSX.Element> = {
  config: ConfigSection,
  theory: TheorySection,
  simulate: SimulateSection,
  report: ReportSection,
};

export default function HomePage() {
  const step = useAppStore((s) => s.step);
  const ActiveSection = SECTIONS[step];

  return (
    <div className="min-h-screen">
      <main className="mx-auto max-w-7xl px-4 py-6 md:py-10 space-y-6">
        {}
        <div className="flex items-center justify-between gap-3">
          <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
            SID · ADOMC
          </div>
          <div className="flex items-center gap-3">
            <ModeToggle />
            <ThemeToggle />
          </div>
        </div>

        <Hero />

        {}
        <StepperMobile />

        {}
        <div className="flex gap-6">
          <SidebarNav />
          <div className="flex-1 min-w-0">
            <ActiveSection />
          </div>
        </div>

        <footer className="pt-8 pb-4 text-center text-xs text-muted-foreground">
          SID — Optimisation Évolutive Multi-Objectif · FastAPI + Next.js 14
        </footer>
      </main>
    </div>
  );
}
