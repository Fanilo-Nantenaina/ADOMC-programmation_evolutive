"use client";

import { Sparkles, GitBranch, Target, Calculator } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAppStore } from "@/lib/store";

export function TheorySection() {
  const mode = useAppStore((s) => s.mode);
  return mode === "simple" ? <SimpleTheory /> : <ExpertTheory />;
}

function SimpleTheory() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="glass">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">
                La frontière du choix parfait
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed text-muted-foreground space-y-3">
            <p>
              Imaginez des milliers de répartitions possibles de votre argent,
              chacune représentée par un point sur un graphique{" "}
              <strong>rendement vs risque</strong>.
            </p>
            <p>
              La plupart sont mauvaises. Mais certaines forment une{" "}
              <strong>courbe parfaite</strong> où il devient impossible de
              gagner plus sans accepter plus de risque.
            </p>
            <div className="rounded-lg border-l-2 border-primary bg-primary/5 p-3 text-foreground">
              C&apos;est cette courbe que notre IA recherche : les choix où plus
              rien ne se sacrifie inutilement.
            </div>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              <CardTitle className="text-lg">L&apos;arbitre neutre</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed text-muted-foreground space-y-3">
            <p>
              Une fois la courbe trouvée, comment choisir LE point qui vous
              convient ?
            </p>
            <p>
              Un système compare chaque point à deux références : le{" "}
              <strong>paradis financier</strong> (max gain, zéro risque) et
              l&apos;<strong>enfer financier</strong> (zéro gain, max risque).
            </p>
            <div className="rounded-lg border-l-2 border-primary bg-primary/5 p-3 text-foreground">
              Le meilleur est celui qui est le plus proche du paradis et le plus
              loin de l&apos;enfer, selon vos préférences.
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="glass">
        <CardHeader>
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">
              L&apos;intelligence évolutive
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="text-sm leading-relaxed text-muted-foreground space-y-2">
          <p>
            L&apos;IA fonctionne comme la sélection naturelle : elle crée une
            population de portefeuilles, garde les meilleurs, les fait muter
            légèrement, et recommence. Au fil des générations, la population se
            rapproche automatiquement de la courbe parfaite.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function ExpertTheory() {
  return (
    <div className="space-y-6 animate-fade-in">
      <Card className="glass">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-primary" />
            <CardTitle>Modèle de Markowitz</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="text-sm space-y-3 leading-relaxed">
          <p className="text-muted-foreground">Problème bi-objectif :</p>
          <pre className="font-mono text-xs p-3 rounded-md bg-muted/40 overflow-x-auto">
            {`max R_p = w^T · μ
min σ_p = √(w^T · Σ · w)
s.c.  Σ w_i = 1,  w_i ≥ 0`}
          </pre>
          <ul className="text-xs space-y-1 text-muted-foreground">
            <li>• μ ∈ ℝⁿ : vecteur des rendements espérés</li>
            <li>• Σ ∈ ℝⁿˣⁿ : matrice de covariance (PSD)</li>
            <li>• w ∈ Δⁿ⁻¹ : vecteur d&apos;allocation simplexe</li>
            <li>• Contrainte optionnelle : σ_p ≤ σ_max</li>
          </ul>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="glass">
          <CardHeader>
            <CardTitle className="text-base">MOEP (Fogel-style)</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-2">
            <p>
              <strong>Distinctions structurelles vs NSGA-II :</strong>
            </p>
            <ul className="space-y-1.5">
              <li>
                • <strong>Pas de croisement</strong> — chaque parent → 1 enfant
                par mutation seule (marqueur EP définitoire).
              </li>
              <li>
                • <strong>σ auto-adaptatif</strong> log-normal (Schwefel) :
                <pre className="mt-1 font-mono text-[10px] p-2 rounded bg-muted/40">
                  {`σ'(k) = σ(k) · exp(τ' · N(0,1) + τ · N_k(0,1))
τ' = 1/√(2n),  τ = 1/√(2√n)`}
                </pre>
              </li>
              <li>
                • <strong>Tournoi (μ+λ) q-stochastique</strong> sur dominance
                Pareto avec crowding pour départage.
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card className="glass">
          <CardHeader>
            <CardTitle className="text-base">TOPSIS pondéré</CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground space-y-2">
            <pre className="font-mono text-[10px] p-2 rounded bg-muted/40">
              {`C_i* = d_i^- / (d_i^+ + d_i^-)
d_i^± = √(Σ_j w_j · (n_ij - n_j^±)²)`}
            </pre>
            <p>
              Sélectionne la solution maximisant la proximité relative à
              l&apos;idéal positif après normalisation min-max (Hwang & Yoon,
              1981).
            </p>
            <p>
              Variante : pondération embarquée dans la distance L2 plutôt que
              dans la matrice normalisée.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="glass">
        <CardHeader>
          <CardTitle className="text-base">Indicateurs de qualité</CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-muted-foreground space-y-2 grid md:grid-cols-2 gap-4">
          <div>
            <p className="font-semibold text-foreground">Hypervolume (HV)</p>
            <p>
              Volume dominé par le front avec point de référence invariant
              (rendement nul, volatilité max individuelle). Comparable entre
              runs. Plus grand = mieux.
            </p>
          </div>
          <div>
            <p className="font-semibold text-foreground">IGD</p>
            <p>
              Distance moyenne au front de référence approché (union
              non-dominée). Relatif : l&apos;algo qui contribue le plus à
              l&apos;union aura un IGD biaisé à la baisse. Plus petit = mieux.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
