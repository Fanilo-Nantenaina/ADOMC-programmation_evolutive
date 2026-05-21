"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { useAppStore } from "@/lib/store";
import { validateCorrelation } from "@/lib/api";

export function ConfigSection() {
  const mode = useAppStore((s) => s.mode);
  const isSimple = mode === "simple";
  const assets = useAppStore((s) => s.assets);
  const setNumAssets = useAppStore((s) => s.setNumAssets);
  const updateAsset = useAppStore((s) => s.updateAsset);
  const correlation = useAppStore((s) => s.correlation);
  const updateCorrelationCell = useAppStore((s) => s.updateCorrelationCell);

  const [psdWarning, setPsdWarning] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(async () => {
      try {
        const result = await validateCorrelation(
          assets.map((a) => a.name),
          assets.map((a) => a.volatility_pct / 100),
          correlation,
        );
        if (!cancelled) {
          setPsdWarning(result.was_corrected ? result.message : null);
        }
      } catch {
        if (!cancelled) setPsdWarning(null);
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [assets, correlation]);

  return (
    <div className="space-y-6 animate-fade-in">
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl">
            {isSimple ? "📊 Vos placements" : "Définition des actifs"}
          </CardTitle>
          <CardDescription>
            {isSimple
              ? "Indiquez les placements à analyser : leur gain attendu et leur niveau de risque."
              : "Rendements espérés μ_i et volatilités individuelles σ_i. La covariance Σ est calculée à la volée."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3 max-w-xs">
            <Label className="text-sm font-medium whitespace-nowrap">
              {isSimple ? "Nombre de placements" : "n_assets"}
            </Label>
            <Input
              type="number"
              min={2}
              max={12}
              value={assets.length}
              onChange={(e) => setNumAssets(parseInt(e.target.value || "2"))}
              className="w-20"
            />
          </div>

          <div className="overflow-x-auto rounded-lg border border-border/60">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr>
                  <th className="text-left px-4 py-2 font-semibold">
                    {isSimple ? "Placement" : "Actif"}
                  </th>
                  <th className="text-left px-4 py-2 font-semibold">
                    {isSimple ? "Gain estimé (%)" : "μ (%)"}
                  </th>
                  <th className="text-left px-4 py-2 font-semibold">
                    {isSimple ? "Volatilité (%)" : "σ (%)"}
                  </th>
                </tr>
              </thead>
              <tbody>
                {assets.map((a, i) => (
                  <tr
                    key={i}
                    className="border-t border-border/40 hover:bg-muted/20"
                  >
                    <td className="px-4 py-2">
                      <Input
                        value={a.name}
                        onChange={(e) =>
                          updateAsset(i, { name: e.target.value })
                        }
                        className="h-8"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <Input
                        type="number"
                        step="0.5"
                        value={a.expected_return_pct}
                        onChange={(e) =>
                          updateAsset(i, {
                            expected_return_pct: parseFloat(
                              e.target.value || "0",
                            ),
                          })
                        }
                        className="h-8 w-24"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <Input
                        type="number"
                        step="0.5"
                        min="0.1"
                        value={a.volatility_pct}
                        onChange={(e) =>
                          updateAsset(i, {
                            volatility_pct: parseFloat(e.target.value || "0.1"),
                          })
                        }
                        className="h-8 w-24"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl">
            {isSimple
              ? "🔗 Liens entre les placements"
              : "Matrice de corrélation (R)"}
          </CardTitle>
          <CardDescription>
            {isSimple
              ? "Une corrélation négative entre deux placements signifie qu'ils évoluent en sens opposés — c'est un excellent bouclier."
              : "Une corrélation proche de −1 indique des actifs qui se compensent (effet de diversification de Markowitz). Symétrie et diagonale unitaire sont forcées."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-lg border border-border/60">
            <table className="w-full text-xs">
              <thead className="bg-muted/40">
                <tr>
                  <th className="px-2 py-1 text-left"></th>
                  {assets.map((a, j) => (
                    <th key={j} className="px-2 py-1 text-left font-mono">
                      {a.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {assets.map((a, i) => (
                  <tr key={i} className="border-t border-border/40">
                    <td className="px-2 py-1 font-mono font-semibold bg-muted/40">
                      {a.name}
                    </td>
                    {assets.map((_, j) => (
                      <td key={j} className="px-1 py-1">
                        {i === j ? (
                          <span className="text-muted-foreground font-mono px-2">
                            1.00
                          </span>
                        ) : (
                          <Input
                            type="number"
                            step="0.05"
                            min="-1"
                            max="1"
                            value={correlation[i]?.[j] ?? 0}
                            onChange={(e) =>
                              updateCorrelationCell(
                                i,
                                j,
                                parseFloat(e.target.value || "0"),
                              )
                            }
                            className="h-7 w-16 text-xs font-mono"
                          />
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {psdWarning && (
            <div className="mt-4 flex items-start gap-3 p-3 rounded-lg border border-destructive/30 bg-destructive/5 text-sm">
              <AlertTriangle className="h-4 w-4 text-destructive mt-0.5 shrink-0" />
              <div>
                <p className="font-semibold text-destructive">
                  {isSimple
                    ? "Vos corrélations sont incohérentes"
                    : "Projection PSD requise"}
                </p>
                <p className="text-muted-foreground mt-1">{psdWarning}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export function SliderField({
  label,
  value,
  onChange,
  min,
  max,
  step,
  suffix,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
  suffix?: string;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <Label>{label}</Label>
        <span className="font-mono text-muted-foreground">
          {value}
          {suffix}
        </span>
      </div>
      <Slider
        value={[value]}
        onValueChange={(v) => onChange(v[0])}
        min={min}
        max={max}
        step={step}
      />
    </div>
  );
}
