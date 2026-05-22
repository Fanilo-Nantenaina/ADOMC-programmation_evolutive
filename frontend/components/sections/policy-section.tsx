"use client";


import { useEffect } from "react";
import {
  Brain,
  Play,
  Square,
  Sparkles,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Progress } from "@/components/ui/progress";

import { AllocationDonut } from "@/components/allocation-donut";
import { MetricCard } from "@/components/metric-card";
import { NeatTrainingChart } from "@/components/neat-training-chart";
import { useAppStore } from "@/lib/store";
import {
  fetchNeatStatus,
  runNeatInference,
  streamNeatTraining,
} from "@/lib/api";

export function PolicySection() {
  const mode = useAppStore((s) => s.mode);
  const isSimple = mode === "simple";

  const assets = useAppStore((s) => s.assets);
  const correlation = useAppStore((s) => s.correlation);
  const wReturn = useAppStore((s) => s.wReturn);
  const riskFreeRate = useAppStore((s) => s.riskFreeRate);
  const seed = useAppStore((s) => s.seed);
  const frameDelayMs = useAppStore((s) => s.frameDelayMs);

  const nGen = useAppStore((s) => s.neatNGenerations);
  const setNGen = useAppStore((s) => s.setNeatNGenerations);
  const nScenarios = useAppStore((s) => s.neatNScenarios);
  const setNScenarios = useAppStore((s) => s.setNeatNScenarios);
  const perturb = useAppStore((s) => s.neatPerturbStrength);
  const setPerturb = useAppStore((s) => s.setNeatPerturbStrength);

  const history = useAppStore((s) => s.neatTrainingHistory);
  const isTraining = useAppStore((s) => s.isTrainingPolicy);
  const setTraining = useAppStore((s) => s.setTrainingPolicy);
  const policyError = useAppStore((s) => s.policyError);
  const setPolicyError = useAppStore((s) => s.setPolicyError);
  const ctrl = useAppStore((s) => s.policyAbortController);
  const setCtrl = useAppStore((s) => s.setPolicyAbortController);
  const hasPolicy = useAppStore((s) => s.hasPolicy);
  const setHasPolicy = useAppStore((s) => s.setHasPolicy);
  const pushEvent = useAppStore((s) => s.pushNeatEvent);
  const resetTraining = useAppStore((s) => s.resetTraining);

  const inference = useAppStore((s) => s.latestInference);
  const setInference = useAppStore((s) => s.setLatestInference);

  useEffect(() => {
    let mounted = true;
    fetchNeatStatus()
      .then((s) => {
        if (mounted) setHasPolicy(s.has_policy);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [setHasPolicy]);

  const currentGen = history.length > 0 ? history[history.length - 1].gen : 0;
  const progress = nGen > 0 ? (currentGen / nGen) * 100 : 0;
  const bestFitness =
    history.length > 0 ? Math.max(...history.map((h) => h.f_max)) : null;

  async function handleTrain() {
    resetTraining();
    setTraining(true);
    setPolicyError(null);

    const abortCtrl = new AbortController();
    setCtrl(abortCtrl);

    try {
      await streamNeatTraining(
        {
          assets,
          correlation_matrix: correlation,
          n_generations: nGen,
          n_scenarios: nScenarios,
          perturb_strength: perturb,
          w_return: wReturn,
          risk_free_rate: riskFreeRate,
          seed,
          frame_delay_ms: frameDelayMs,
        },
        {
          onStart: (meta) =>
            toast.info(
              `Entraînement lancé — ${meta.n_gen} générations, ${meta.n_scenarios} scénarios`,
            ),
          onEvent: (e) => pushEvent(e),
          onEnd: (payload) => {
            setTraining(false);
            setCtrl(null);
            setHasPolicy(true);
            toast.success(
              `Entraînement terminé — fitness finale ${
                payload.final_fitness?.toFixed(3) ?? "N/A"
              }`,
            );
          },
          onError: (msg) => {
            setPolicyError(msg);
            setTraining(false);
            setCtrl(null);
            toast.error(`Erreur : ${msg}`);
          },
        },
        abortCtrl.signal,
      );
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== "AbortError") {
        setPolicyError(e.message);
        setTraining(false);
        setCtrl(null);
        toast.error(`Erreur : ${e.message}`);
      }
    }
  }

  function handleCancel() {
    if (ctrl) {
      ctrl.abort();
      setTraining(false);
      setCtrl(null);
      toast.warning("Entraînement interrompu");
    }
  }

  async function handleInfer() {
    try {
      const result = await runNeatInference(
        assets,
        correlation,
        wReturn,
        riskFreeRate,
      );
      setInference(result);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(msg);
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {}
      <Card className="glass">
        <CardHeader>
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                <CardTitle className="text-xl">
                  {isSimple
                    ? "Entraîner le conseiller IA"
                    : "Entraînement NEAT"}
                </CardTitle>
              </div>
              <CardDescription className="mt-1.5">
                {isSimple
                  ? "L'IA apprend des principes d'allocation en s'entraînant sur des scénarios de marché variés. Une fois formée, elle s'adapte à de nouvelles situations sans recalcul."
                  : "NeuroEvolution of Augmenting Topologies. Évolution d'un réseau de neurones qui mappe (μ, σ, corrélation, profil) → allocation softmax. Multi-scénarios pour forcer la généralisation."}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid md:grid-cols-3 gap-5">
            <SliderField
              label={isSimple ? "Étapes d'apprentissage" : "Générations NEAT"}
              value={nGen}
              onChange={setNGen}
              min={10}
              max={100}
              step={5}
            />
            <SliderField
              label={isSimple ? "Scénarios de test" : "n_scénarios"}
              value={nScenarios}
              onChange={setNScenarios}
              min={1}
              max={16}
              step={1}
            />
            <SliderField
              label={isSimple ? "Diversité des scénarios" : "Perturbation σ"}
              value={Math.round(perturb * 100)}
              onChange={(v) => setPerturb(v / 100)}
              min={5}
              max={40}
              step={5}
              suffix=" %"
            />
          </div>

          <div className="flex flex-wrap gap-2 items-center">
            {!isTraining ? (
              <Button onClick={handleTrain}>
                <Play className="h-4 w-4 mr-2" />
                {isSimple ? "Entraîner" : "Lancer l'entraînement"}
              </Button>
            ) : (
              <Button onClick={handleCancel} variant="destructive">
                <Square className="h-4 w-4 mr-2" />
                Annuler
              </Button>
            )}

            {hasPolicy && !isTraining && (
              <div className="text-xs flex items-center gap-1.5 text-primary">
                <Sparkles className="h-3.5 w-3.5" />
                Une politique entraînée est disponible
              </div>
            )}
          </div>

          {isTraining && (
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  {isSimple ? "Étape" : "Génération"} {currentGen}/{nGen}
                </span>
                <span>{Math.round(progress)} %</span>
              </div>
              <Progress value={progress} className="h-1.5" />
            </div>
          )}

          {policyError && (
            <div className="flex items-start gap-2 p-3 rounded-md border border-destructive/30 bg-destructive/5 text-xs">
              <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
              <span className="text-destructive">{policyError}</span>
            </div>
          )}

          {history.length > 0 && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <MetricCard
                  label={isSimple ? "Meilleur score" : "f_max final"}
                  value={bestFitness?.toFixed(3) ?? "—"}
                />
                <MetricCard
                  label={isSimple ? "Génération" : "Gen courante"}
                  value={`${currentGen} / ${nGen}`}
                />
                <MetricCard
                  label={isSimple ? "Espèces" : "Spéciation"}
                  value={String(history[history.length - 1]?.n_species ?? 0)}
                />
              </div>
              <NeatTrainingChart />
            </div>
          )}
        </CardContent>
      </Card>

      {}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-lg">
            {isSimple
              ? "Demander une recommandation"
              : "Inférence — état actuel du marché"}
          </CardTitle>
          <CardDescription>
            {isSimple
              ? "L'IA entraînée analyse vos placements et propose une allocation. Modifiez vos placements dans l'étape 1 pour voir comment l'IA s'adapte."
              : "Forward pass du génome champion sur le vecteur d'entrée encodé (μ, σ, corr_moy, mask, profil, r_f) → softmax sur les n_assets actifs."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={handleInfer} disabled={!hasPolicy} variant="default">
            <Sparkles className="h-4 w-4 mr-2" />
            {hasPolicy
              ? isSimple
                ? "Obtenir l'allocation"
                : "Lancer l'inférence"
              : "Entraînez d'abord une politique"}
          </Button>

          {inference && (
            <div className="space-y-4 pt-2">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                <MetricCard
                  label="Rendement attendu"
                  value={`${inference.expected_return_pct.toFixed(2)} %`}
                />
                <MetricCard
                  label="Risque (σ_p)"
                  value={`${inference.risk_pct.toFixed(2)} %`}
                />
                <MetricCard
                  label="Sharpe"
                  value={inference.sharpe.toFixed(3)}
                />
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold mb-3">
                    {isSimple ? "Recommandation de l'IA" : "Allocation prédite"}
                  </h4>
                  <div className="space-y-1">
                    {assets
                      .map((a, i) => ({
                        name: a.name,
                        pct: (inference.weights[i] ?? 0) * 100,
                      }))
                      .filter((row) => row.pct > 0.1)
                      .sort((a, b) => b.pct - a.pct)
                      .map((row) => (
                        <div key={row.name} className="space-y-0.5">
                          <div className="flex justify-between text-xs">
                            <span className="font-medium truncate pr-2">
                              {row.name}
                            </span>
                            <span className="font-mono text-muted-foreground shrink-0">
                              {row.pct.toFixed(2)} %
                            </span>
                          </div>
                          <div className="h-1.5 bg-foreground/10 rounded-full overflow-hidden">
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
                  <h4 className="text-sm font-semibold mb-3">
                    Vue d&apos;ensemble
                  </h4>
                  <AllocationDonut
                    weights={inference.weights}
                    assetNames={assets.map((a) => a.name)}
                    algorithm="NEAT"
                  />
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

interface SliderFieldProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
  suffix?: string;
}

function SliderField({
  label,
  value,
  onChange,
  min,
  max,
  step,
  suffix,
}: SliderFieldProps) {
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
