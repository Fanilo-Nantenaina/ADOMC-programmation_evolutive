"use client";

import { useState } from "react";
import { Play, Square, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";

import { ParetoStreamChart } from "@/components/pareto-stream-chart";
import { PlaybackControl } from "@/components/playback-control";
import { useAppStore } from "@/lib/store";
import { streamSimulation } from "@/lib/api";
import type { AlgorithmChoice } from "@/lib/types";

export function SimulateSection() {
  const mode = useAppStore((s) => s.mode);
  const isSimple = mode === "simple";

  const algorithm = useAppStore((s) => s.algorithm);
  const setAlgorithm = useAppStore((s) => s.setAlgorithm);
  const popSize = useAppStore((s) => s.popSize);
  const setPopSize = useAppStore((s) => s.setPopSize);
  const nGen = useAppStore((s) => s.nGen);
  const setNGen = useAppStore((s) => s.setNGen);
  const seed = useAppStore((s) => s.seed);
  const setSeed = useAppStore((s) => s.setSeed);
  const wReturn = useAppStore((s) => s.wReturn);
  const setWReturn = useAppStore((s) => s.setWReturn);
  const maxRiskPct = useAppStore((s) => s.maxRiskPct);
  const setMaxRiskPct = useAppStore((s) => s.setMaxRiskPct);
  const riskFreeRate = useAppStore((s) => s.riskFreeRate);
  const setRiskFreeRate = useAppStore((s) => s.setRiskFreeRate);

  const assets = useAppStore((s) => s.assets);
  const correlation = useAppStore((s) => s.correlation);
  const isSimulating = useAppStore((s) => s.isSimulating);
  const setSimulating = useAppStore((s) => s.setSimulating);
  const setSimulationError = useAppStore((s) => s.setSimulationError);
  const pushEvent = useAppStore((s) => s.pushEvent);
  const resetSimulation = useAppStore((s) => s.resetSimulation);
  const currentGen = useAppStore((s) => s.currentGen);
  const totalGen = useAppStore((s) => s.totalGen);
  const setAbortController = useAppStore((s) => s.setAbortController);
  const abortController = useAppStore((s) => s.abortController);

  const [riskLimitEnabled, setRiskLimitEnabled] = useState(false);

  const progress = totalGen > 0 ? (currentGen / totalGen) * 100 : 0;

  async function handleLaunch() {
    resetSimulation();
    setSimulating(true);

    const ctrl = new AbortController();
    setAbortController(ctrl);

    try {
      await streamSimulation(
        {
          assets,
          correlation_matrix: correlation,
          algorithm,
          pop_size: popSize,
          n_gen: nGen,
          seed,
          max_risk_pct: riskLimitEnabled ? maxRiskPct : null,
          w_return: wReturn,
          risk_free_rate: riskFreeRate,
        },
        {
          onStart: (meta) => {
            toast.info(
              `Lancement — ${meta.algorithms.join(" + ")} sur ${meta.n_gen} générations`,
            );
          },
          onEvent: (e) => pushEvent(e),
          onEnd: () => {
            setSimulating(false);
            setAbortController(null);
            toast.success("Optimisation terminée");
          },
          onError: (msg) => {
            setSimulationError(msg);
            setSimulating(false);
            setAbortController(null);
            toast.error(`Erreur : ${msg}`);
          },
        },
        ctrl.signal,
      );
    } catch (e: unknown) {
      if (e instanceof Error && e.name !== "AbortError") {
        setSimulationError(e.message);
        setSimulating(false);
        setAbortController(null);
        toast.error(`Erreur : ${e.message}`);
      } else if (!(e instanceof Error)) {
        const msg = String(e);
        setSimulationError(msg);
        setSimulating(false);
        setAbortController(null);
        toast.error(`Erreur : ${msg}`);
      }
    }
  }

  function handleCancel() {
    if (abortController) {
      abortController.abort();
      setSimulating(false);
      setAbortController(null);
      toast.warning("Simulation interrompue");
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-xl">
            {isSimple
              ? "🚀 Lancer la recherche"
              : "Configuration de l'optimisation"}
          </CardTitle>
          <CardDescription>
            {isSimple
              ? "Réglez les paramètres et cliquez sur Lancer. L'IA évoluera génération par génération sous vos yeux."
              : "Streaming SSE génération-par-génération. Le front s'actualise en flux continu."}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-sm">
                {isSimple ? "Méthode d'IA" : "Algorithme"}
              </Label>
              <Select
                value={algorithm}
                onValueChange={(v: string) =>
                  setAlgorithm(v as AlgorithmChoice)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="moep">
                    {isSimple ? "Méthode adaptative (MOEP)" : "MOEP"}
                  </SelectItem>
                  <SelectItem value="nsga2">
                    {isSimple ? "Méthode classique (NSGA-II)" : "NSGA-II"}
                  </SelectItem>
                  <SelectItem value="both">
                    {isSimple
                      ? "Comparer les deux"
                      : "MOEP + NSGA-II (comparaison)"}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <SliderField
              label={isSimple ? "Taille de population" : "Population (μ)"}
              value={popSize}
              onChange={setPopSize}
              min={20}
              max={150}
              step={10}
            />

            <SliderField
              label={isSimple ? "Itérations" : "Générations (T)"}
              value={nGen}
              onChange={setNGen}
              min={10}
              max={100}
              step={5}
            />

            <div className="space-y-1.5">
              <div className="flex justify-between text-sm">
                <Label>Seed (reproductibilité)</Label>
                <span className="font-mono text-muted-foreground">{seed}</span>
              </div>
              <input
                type="number"
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm"
                value={seed}
                onChange={(e) => setSeed(parseInt(e.target.value || "0", 10))}
                min={0}
                max={99999}
              />
            </div>
          </div>

          <div className="space-y-4">
            <SliderField
              label={isSimple ? "Priorité au gain (%)" : "w_return (%)"}
              value={wReturn}
              onChange={setWReturn}
              min={10}
              max={90}
              step={5}
              suffix=" %"
            />

            {!isSimple && (
              <SliderField
                label="Taux sans risque r_f"
                value={Math.round(riskFreeRate * 1000) / 10}
                onChange={(v) => setRiskFreeRate(v / 100)}
                min={0}
                max={10}
                step={0.1}
                suffix=" %"
              />
            )}

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm" htmlFor="risk-limit">
                  {isSimple ? "Limite de sécurité" : "Contrainte σ_max"}
                </Label>
                <Switch
                  id="risk-limit"
                  checked={riskLimitEnabled}
                  onCheckedChange={(v) => {
                    setRiskLimitEnabled(v);
                    if (!v) setMaxRiskPct(null);
                    else setMaxRiskPct(maxRiskPct ?? 0.25);
                  }}
                />
              </div>
              {riskLimitEnabled && (
                <SliderField
                  label={isSimple ? "Risque max accepté" : "σ_max"}
                  value={Math.round((maxRiskPct ?? 0.25) * 100)}
                  onChange={(v) => setMaxRiskPct(v / 100)}
                  min={5}
                  max={60}
                  step={5}
                  suffix=" %"
                />
              )}
            </div>

            <div className="flex gap-2 pt-2">
              {!isSimulating ? (
                <Button onClick={handleLaunch} className="flex-1">
                  <Play className="h-4 w-4 mr-2" />
                  {isSimple ? "Lancer la recherche" : "Lancer l'optimisation"}
                </Button>
              ) : (
                <Button
                  onClick={handleCancel}
                  variant="destructive"
                  className="flex-1"
                >
                  <Square className="h-4 w-4 mr-2" />
                  Annuler
                </Button>
              )}
            </div>

            {isSimulating && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    {isSimple
                      ? `Étape ${currentGen}/${totalGen}`
                      : `Génération ${currentGen}/${totalGen}`}
                  </span>
                  <span>{Math.round(progress)} %</span>
                </div>
                <Progress value={progress} className="h-1.5" />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="glass">
        <CardContent className="pt-6">
          <ParetoStreamChart />
          <PlaybackControl />
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
