"use client";

import { Download, TrendingUp, Shield, BarChart3 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { AllocationDonut } from "@/components/allocation-donut";
import { MetricCard } from "@/components/metric-card";
import { useAppStore } from "@/lib/store";
import { exportReport, downloadBlob } from "@/lib/api";

export function ReportSection() {
  const mode = useAppStore((s) => s.mode);
  const isSimple = mode === "simple";

  const finalByAlgo = useAppStore((s) => s.finalByAlgo);
  const assets = useAppStore((s) => s.assets);
  const correlation = useAppStore((s) => s.correlation);
  const algorithm = useAppStore((s) => s.algorithm);
  const popSize = useAppStore((s) => s.popSize);
  const nGen = useAppStore((s) => s.nGen);
  const seed = useAppStore((s) => s.seed);
  const maxRiskPct = useAppStore((s) => s.maxRiskPct);
  const wReturn = useAppStore((s) => s.wReturn);
  const riskFreeRate = useAppStore((s) => s.riskFreeRate);

  const hasResults = Object.keys(finalByAlgo).length > 0;

  if (!hasResults) {
    return (
      <Card className="glass animate-fade-in">
        <CardContent className="pt-8 pb-8 text-center text-muted-foreground space-y-2">
          <BarChart3 className="h-10 w-10 mx-auto opacity-30" />
          <p className="text-sm">
            {isSimple
              ? "Lancez d'abord une simulation dans l'onglet Simulation."
              : "Aucun résultat disponible. Exécutez une optimisation dans l'onglet Simulation."}
          </p>
        </CardContent>
      </Card>
    );
  }

  async function handleExport() {
    try {
      const results: Record<string, any> = {};
      for (const [algoName, evt] of Object.entries(finalByAlgo)) {
        results[algoName] = {
          weights: [evt.topsis.weights],
          returns_pct: [evt.topsis.return_pct],
          risks_pct: [evt.topsis.risk_pct],
          topsis: evt.topsis,
        };
      }

      const blob = await exportReport(
        {
          assets,
          correlation_matrix: correlation,
          algorithm,
          pop_size: popSize,
          n_gen: nGen,
          seed,
          max_risk_pct: maxRiskPct,
          w_return: wReturn,
          risk_free_rate: riskFreeRate,
        },
        results,
      );
      const filename = `Rapport_SID_${new Date()
        .toISOString()
        .slice(0, 16)
        .replace(/[:-]/g, "")}.xlsx`;
      downloadBlob(blob, filename);
      toast.success("Rapport Excel téléchargé");
    } catch (e: any) {
      toast.error(`Export échoué : ${e?.message ?? e}`);
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Card className="glass">
        <CardHeader>
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <CardTitle className="text-xl">
                {isSimple
                  ? "📋 Recommandation finale"
                  : "Rapport d'arbitrage TOPSIS"}
              </CardTitle>
              <CardDescription>
                {isSimple
                  ? "Voici la répartition optimale calculée pour vous."
                  : `Compromis sélectionné par TOPSIS pondéré (w_return = ${wReturn}%, r_f = ${(
                      riskFreeRate * 100
                    ).toFixed(1)}%).`}
              </CardDescription>
            </div>
            <Button onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Excel
            </Button>
          </div>
        </CardHeader>
      </Card>

      {Object.entries(finalByAlgo).map(([algoName, evt]) => {
        const sharpe =
          evt.topsis.risk_pct > 0
            ? (evt.topsis.return_pct / 100 - riskFreeRate) /
              (evt.topsis.risk_pct / 100)
            : 0;
        return (
          <Card key={algoName} className="glass">
            <CardHeader>
              <CardTitle className="text-lg">
                {isSimple
                  ? `Résultat — ${algoName}`
                  : `Algorithme : ${algoName}`}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <MetricCard
                  icon={<TrendingUp className="h-4 w-4" />}
                  label={isSimple ? "Rendement attendu" : "R_p"}
                  value={`${evt.topsis.return_pct.toFixed(2)} %`}
                  hint="par an"
                />
                <MetricCard
                  icon={<Shield className="h-4 w-4" />}
                  label={isSimple ? "Niveau de risque" : "σ_p"}
                  value={`${evt.topsis.risk_pct.toFixed(2)} %`}
                />
                {!isSimple && (
                  <MetricCard
                    icon={<BarChart3 className="h-4 w-4" />}
                    label="Ratio de Sharpe"
                    value={sharpe.toFixed(2)}
                    hint={`r_f = ${(riskFreeRate * 100).toFixed(1)}%`}
                  />
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold mb-3">
                    {isSimple ? "Répartition recommandée" : "Allocation TOPSIS"}
                  </h4>
                  <div className="space-y-1">
                    {assets
                      .map((a, i) => ({
                        name: a.name,
                        pct: (evt.topsis.weights[i] || 0) * 100,
                      }))
                      .filter((row) => row.pct > 0.1)
                      .sort((a, b) => b.pct - a.pct)
                      .map((row) => (
                        <div key={row.name} className="space-y-0.5">
                          <div className="flex justify-between text-xs">
                            <span className="font-medium">{row.name}</span>
                            <span className="font-mono text-muted-foreground">
                              {row.pct.toFixed(2)} %
                            </span>
                          </div>
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary transition-all"
                              style={{ width: `${Math.min(row.pct, 100)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-3">Vue d'ensemble</h4>
                  <AllocationDonut
                    weights={evt.topsis.weights}
                    assetNames={assets.map((a) => a.name)}
                    algorithm={algoName}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
