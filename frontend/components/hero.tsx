"use client";

import { Activity } from "lucide-react";

import { useAppStore } from "@/lib/store";

export function Hero() {
  const mode = useAppStore((s) => s.mode);
  const isSimple = mode === "simple";

  return (
    <header className="space-y-4 pt-2 pb-6 border-b border-border/60">
      <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass text-xs font-semibold">
        <Activity className="h-3 w-3 text-primary" />
        {isSimple ? "Mode Découverte" : "Mode Expert"}
      </div>

      <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-linear-to-br from-foreground to-primary">
        {isSimple
          ? "Votre Conseiller Financier Intelligent"
          : "SID — Optimisation Évolutive Multi-Objectif"}
      </h1>

      <p className="max-w-2xl text-base text-muted-foreground leading-relaxed">
        {isSimple
          ? "Comparez automatiquement des milliers de répartitions de votre épargne pour trouver l'équilibre parfait entre gains et tranquillité d'esprit."
          : "Système d'Aide à la Décision intégrant MOEP (programmation évolutive auto-adaptative) et NSGA-II pour la résolution du problème de Markowitz sous contraintes, avec arbitrage TOPSIS et indicateurs Hypervolume / IGD."}
      </p>
    </header>
  );
}
