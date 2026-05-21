"use client";

import { Settings2, BookOpen, Activity, FileText } from "lucide-react";

import { Hero } from "@/components/hero";
import { ThemeToggle } from "@/components/theme-toggle";
import { ModeToggle } from "@/components/mode-toggle";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

import { ConfigSection } from "@/components/sections/config-section";
import { TheorySection } from "@/components/sections/theory-section";
import { SimulateSection } from "@/components/sections/simulate-section";
import { ReportSection } from "@/components/sections/report-section";

import { useAppStore } from "@/lib/store";

export default function HomePage() {
  const mode = useAppStore((s) => s.mode);
  const step = useAppStore((s) => s.step);
  const setStep = useAppStore((s) => s.setStep);
  const isSimple = mode === "simple";

  return (
    <main className="container max-w-7xl py-6 md:py-10 space-y-8">
      {}
      <div className="flex items-center justify-end gap-3">
        <ModeToggle />
        <ThemeToggle />
      </div>

      {}
      <Hero />

      {}
      <Tabs
        value={step}
        onValueChange={(v) => setStep(v as any)}
        className="w-full"
      >
        <TabsList className="w-full flex flex-wrap md:w-auto">
          <TabsTrigger value="config">
            <Settings2 className="h-4 w-4 mr-2" />
            {isSimple ? "1. Mes placements" : "1. Configuration"}
          </TabsTrigger>
          <TabsTrigger value="theory">
            <BookOpen className="h-4 w-4 mr-2" />
            {isSimple ? "2. Comprendre" : "2. Théorie"}
          </TabsTrigger>
          <TabsTrigger value="simulate">
            <Activity className="h-4 w-4 mr-2" />
            {isSimple ? "3. Lancer l'IA" : "3. Simulation live"}
          </TabsTrigger>
          <TabsTrigger value="report">
            <FileText className="h-4 w-4 mr-2" />
            {isSimple ? "4. Recommandation" : "4. Rapport"}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="config">
          <ConfigSection />
        </TabsContent>

        <TabsContent value="theory">
          <TheorySection />
        </TabsContent>

        <TabsContent value="simulate">
          <SimulateSection />
        </TabsContent>

        <TabsContent value="report">
          <ReportSection />
        </TabsContent>
      </Tabs>

      <footer className="pt-8 pb-4 text-center text-xs text-muted-foreground">
        SID — Optimisation Évolutive Multi-Objectif · Backend FastAPI · Frontend
        Next.js 14
      </footer>
    </main>
  );
}
