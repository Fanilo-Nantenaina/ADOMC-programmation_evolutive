"""
SID — Optimisation Évolutive & Arbitrage de Portefeuille
=========================================================

Système d'Aide à la Décision multi-objectif pour la sélection de portefeuille
au sens de Markowitz, résolu par deux algorithmes évolutionnaires :

- MOEP : Multi-Objective Evolutionary Programming (Fogel-style, implémentation
         authentique : mutation gaussienne auto-adaptative log-normale,
         pas de croisement, sélection (μ+λ) par tournoi q-stochastique).
- NSGA-II : référence pymoo (croisement SBX + mutation polynomiale + tri
         non-dominé déterministe).

Arbitrage final par TOPSIS pondéré. Indicateurs de qualité du front :
Hypervolume + IGD (front de référence approché par l'union non-dominée).
"""

import io
import time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.preprocessing import MinMaxScaler

from pymoo.algorithms.base.genetic import GeneticAlgorithm
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.population import Population
from pymoo.core.problem import Problem
from pymoo.core.survival import Survival
from pymoo.indicators.hv import Hypervolume
from pymoo.indicators.igd import IGD
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.survival.rank_and_crowding.metrics import calc_crowding_distance
from pymoo.optimize import minimize
from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.util.display.multi import MultiObjectiveOutput
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

DEFAULT_ASSET_NAMES = [
    "NVDA",
    "AAPL",
    "MSFT",
    "GOOGL",
    "Obligations",
    "Or",
    "BTC",
    "Immobilier",
    "Pétrole",
    "EUR/USD",
    "LVMH",
    "ASML",
]
DEFAULT_RETURNS_PCT = [
    35.0,
    22.0,
    18.0,
    15.0,
    4.0,
    8.0,
    55.0,
    10.0,
    14.0,
    3.0,
    16.0,
    24.0,
]
DEFAULT_VOLATILITIES_PCT = [
    42.0,
    25.0,
    22.0,
    24.0,
    6.0,
    15.0,
    75.0,
    12.0,
    30.0,
    5.0,
    20.0,
    28.0,
]

CORR_SAFE_HAVEN_DEFAULT = -0.10
CORR_EQUITY_DEFAULT = 0.55

EPSILON_NUM = 1e-8
EIGENVALUE_FLOOR = 1e-10

COLOR_MOEP = "#1f77b4"
COLOR_NSGA = "#2ca02c"
COLOR_MOEP_BEST = "#d62728"
COLOR_NSGA_BEST = "#ff7f0e"
COLOR_CONSTRAINT = "crimson"


st.set_page_config(page_title="SID - Optimisation Évolutive", layout="wide")
st.title("🧠 SID : Optimisation Évolutive & Arbitrage de Portefeuille")

st.sidebar.markdown("---")
simple_mode = st.sidebar.toggle(
    "🔰 Activer le mode vulgarisation (Termes simples)", value=False
)
st.sidebar.markdown("---")

if simple_mode:
    st.markdown("""
    ### 👩‍💼 Bienvenue dans votre conseiller financier intelligent
    Cette application vous aide à trouver la **meilleure répartition possible de votre argent** entre plusieurs placements. 
    Elle compare automatiquement des milliers de combinaisons pour trouver l'équilibre parfait entre le gain et la sécurité.
    """)
else:
    st.markdown("""
    Ce Système d'Aide à la Décision (SID) intègre une couche d'auto-explication mathématique et algorithmique. 
    Modifiez les paramètres financiers ou algorithmiques à la volée pour observer l'adaptation des fronts de Pareto et l'arbitrage multicritère (ADOMC).
    """)

tab_config, tab_theory, tab_exec, tab_analysis = st.tabs(
    [
        "🛠️ 1. Paramètres des Placements",
        "📐 2. Explications des Modèles",
        "🚀 3. Simulation en Temps Réel",
        "🧠 4. Choix Final & Rapport",
    ]
)


def weighted_topsis(returns_pct, risks_pct, w_return, w_risk):
    """
    TOPSIS pondéré bi-objectif.

    Paramètres
    ----------
    returns_pct : (n,) rendements en %, À MAXIMISER
    risks_pct   : (n,) risques en %,  À MINIMISER
    w_return, w_risk : poids du décideur en [0, 1]

    Retourne
    -------
    int : index du meilleur compromis.

    Variante : pondération à l'intérieur de la distance euclidienne (norme L2
    pondérée), équivalente à la formulation de Hwang & Yoon (1981) après
    normalisation min-max.
    """
    F = np.column_stack([returns_pct, risks_pct])
    if np.std(F[:, 0]) < EPSILON_NUM and np.std(F[:, 1]) < EPSILON_NUM:
        return 0

    scaler = MinMaxScaler()
    nF = scaler.fit_transform(F)
    w = np.array([w_return, w_risk])

    ideal_pos = np.array([nF[:, 0].max(), nF[:, 1].min()])
    ideal_neg = np.array([nF[:, 0].min(), nF[:, 1].max()])

    d_pos = np.sqrt(np.sum(w * (nF - ideal_pos) ** 2, axis=1))
    d_neg = np.sqrt(np.sum(w * (nF - ideal_neg) ** 2, axis=1))
    closeness = d_neg / (d_pos + d_neg + EPSILON_NUM)
    return int(np.argmax(closeness))


def project_to_psd(cov_matrix, floor=EIGENVALUE_FLOOR):
    """
    Projette une matrice symétrique sur le cône PSD par clipping spectral.

    Retourne (matrice_corrigée, min_eigenvalue_avant_correction, correction_appliquée).
    """
    eigvals, eigvecs = np.linalg.eigh(cov_matrix)
    min_eig = float(eigvals.min())
    if min_eig < floor:
        eigvals_clipped = np.maximum(eigvals, floor)
        return eigvecs @ np.diag(eigvals_clipped) @ eigvecs.T, min_eig, True
    return cov_matrix, min_eig, False


with tab_config:
    if simple_mode:
        st.header("1. Vos options de placements")
        st.markdown(
            "Indiquez ici la liste des placements que vous souhaitez analyser, ce qu'ils peuvent vous rapporter au mieux, et leur niveau de danger (risque)."
        )
    else:
        st.header("Définition des Actifs et Scénarios Marché")
        st.markdown(
            "Ajustez les rendements attendus, volatilités et corrélations. L'ensemble de la machinerie s'adaptera instantanément."
        )

    col_n1, _ = st.columns([1, 3])
    with col_n1:
        n_assets_ui = st.number_input(
            (
                "Nombre de placements à analyser"
                if simple_mode
                else "Nombre d'actifs à optimiser"
            ),
            min_value=3,
            max_value=12,
            value=6,
            step=1,
        )

    st.subheader(
        "📈 Gains espérés et Niveaux de risque"
        if simple_mode
        else "📈 Rendements espérés (μ) et Volatilités individuelles (σ)"
    )

    default_data = {
        "Nom du Placement" if simple_mode else "Actif": DEFAULT_ASSET_NAMES[
            :n_assets_ui
        ],
        (
            "Gain annuel estimé (%)" if simple_mode else "Rendement Espéré (%)"
        ): DEFAULT_RETURNS_PCT[:n_assets_ui],
        (
            "Danger / Volatilité (%)" if simple_mode else "Volatilité / Risque (%)"
        ): DEFAULT_VOLATILITIES_PCT[:n_assets_ui],
    }
    df_assets = pd.DataFrame(default_data)
    edited_assets = st.data_editor(
        df_assets, key="assets_editor", hide_index=True, use_container_width=True
    )

    ui_mu = edited_assets.iloc[:, 1].to_numpy() / 100
    ui_vol = edited_assets.iloc[:, 2].to_numpy() / 100
    assets_list = edited_assets.iloc[:, 0].tolist()

    if len(set(assets_list)) != len(assets_list):
        st.error(
            "⚠️ Vous avez des noms de placements en double. Renommez-les pour pouvoir continuer."
        )
        st.stop()

    st.subheader(
        "🔗 Liens de dépendance entre les placements"
        if simple_mode
        else "🔗 Matrice de Corrélation entre Actifs (R)"
    )
    st.info(
        "💡 Éviter de mettre tous ses œufs dans le même panier : Si deux placements ont un lien négatif (proche de -1), l'un montera quand l'autre baisse, ce qui protège votre capital total !"
        if simple_mode
        else "💡 Conseil académique : Une corrélation proche de -1 indique des actifs qui se compensent, réduisant drastiquement le risque global du portefeuille (Effet de Diversification de Markowitz)."
    )

    base_corr = np.eye(n_assets_ui)
    is_safe_haven = np.array([("Obligations" in a) or ("Or" in a) for a in assets_list])
    for i in range(n_assets_ui):
        for j in range(i + 1, n_assets_ui):
            base_corr[i, j] = base_corr[j, i] = (
                CORR_SAFE_HAVEN_DEFAULT
                if (is_safe_haven[i] or is_safe_haven[j])
                else CORR_EQUITY_DEFAULT
            )

    df_corr = pd.DataFrame(base_corr, columns=assets_list, index=assets_list)
    edited_corr = st.data_editor(df_corr, key="corr_editor", use_container_width=True)

    raw_corr = edited_corr.to_numpy()
    ui_corr = (raw_corr + raw_corr.T) / 2
    np.fill_diagonal(ui_corr, 1.0)
    ui_cov_raw = np.diag(ui_vol) @ ui_corr @ np.diag(ui_vol)

    ui_cov_matrix, min_eig_observed, was_corrected = project_to_psd(ui_cov_raw)
    if was_corrected:
        if simple_mode:
            st.warning(
                f"⚠️ Les liens entre vos placements étaient mathématiquement incohérents "
                f"(valeur propre minimale = {min_eig_observed:.2e}). Une correction "
                f"automatique a été appliquée pour rendre les calculs possibles. Vérifiez "
                f"que vos corrélations sont réalistes."
            )
        else:
            st.warning(
                f"⚠️ **Projection PSD appliquée :** la matrice de corrélation saisie n'était "
                f"pas semi-définie positive (λ_min = {min_eig_observed:.2e}). Les valeurs "
                f"propres négatives ont été clippées à {EIGENVALUE_FLOOR}. La matrice "
                f"utilisée pour l'optimisation diffère légèrement de la matrice saisie."
            )


with tab_theory:
    if simple_mode:
        st.header("Comprendre la logique en termes simples")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("1. La Frontière du Choix Parfait (Front de Pareto)")
            st.markdown("""
            Imaginez que vous jetez des milliers de fléchettes au hasard sur un graphique représentant le Gain et le Risque. 
            La plupart des lancers sont mauvais. Mais certains lancers forment une ligne parfaite tout en haut à gauche : **c'est la ligne des choix parfaits**.
            Sur cette ligne, il est impossible de gagner plus sans accepter d'avoir plus peur. Notre intelligence artificielle calcule précisément cette ligne.
            """)
        with col_t2:
            st.subheader("2. Le Tri Sélectif (TOPSIS)")
            st.markdown("""
            Une fois la ligne des choix parfaits dessinée, comment choisir le meilleur emplacement ? 
            La méthode **TOPSIS** agit comme un arbitre neutre. Elle cherche la solution qui est **la plus proche possible du Paradis financier** (gagner le maximum avec zéro risque) et **la plus éloignée possible de l'Enfer financier** (perdre tout sans rien gagner).
            """)
    else:
        st.header("Fondations Mathématiques et Architecture du SID")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("1. Modèle de Sélection de Portefeuille de Markowitz")
            st.latex(
                r"R_p = \mathbf{w}^T \boldsymbol{\mu} \quad \text{et} \quad "
                r"\sigma_p = \sqrt{\mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}}"
            )
            st.markdown(
                r"On cherche à maximiser $R_p$ et minimiser $\sigma_p$ sous contraintes vectorielles."
            )
        with col_t2:
            st.subheader("2. Arbitrage Multicritère TOPSIS")
            st.latex(r"C_i^* = \frac{d_i^-}{d_i^+ + d_i^-}")
            st.markdown(
                "Sélection par maximisation de la proximité relative à l'idéal positif."
            )
        st.markdown("---")
        st.subheader("3. Programmation Évolutive Multi-Objectif (MOEP)")
        st.markdown(r"""
        Implémentation Fogel-style **distincte structurellement de NSGA-II** :
        - **Pas de croisement** (caractéristique définitoire de l'EP) ; reproduction asexuée uniquement.
        - **Mutation gaussienne auto-adaptative** : chaque individu porte son propre vecteur $\boldsymbol{\sigma}$ qui mute lui-même selon la règle log-normale de Schwefel.
        - **Sélection $(\mu + \lambda)$ par tournoi stochastique** : chaque candidat affronte $q$ adversaires aléatoires ; ceux qui accumulent le plus de victoires (par dominance de Pareto, départage par distance de crowding) survivent.
        """)
        st.latex(
            r"\sigma_i'(k) = \sigma_i(k) \cdot \exp\bigl(\tau' \cdot \mathcal{N}(0,1) "
            r"+ \tau \cdot \mathcal{N}_k(0,1)\bigr)"
        )
        st.latex(
            r"\tau' = \frac{1}{\sqrt{2n}}, \quad \tau = \frac{1}{\sqrt{2\sqrt{n}}}"
        )


class PortfolioProblem(Problem):
    """
    Problème bi-objectif de Markowitz :
    - f1 = -E[R_p] (rendement espéré, à maximiser → on minimise son opposé)
    - f2 =  σ_p   (volatilité, à minimiser)

    Les variables X ∈ [0,1]^n sont normalisées en interne en w = X / sum(X)
    pour respecter la contrainte d'investissement total (∑w_i = 1, w_i ≥ 0).
    Cet encodage présente une redondance (plusieurs X mappent au même w) mais
    permet l'usage direct des opérateurs évolutionnaires en boîte ∈ [0,1]^n.
    """

    def __init__(self, mu_vec, cov_mat, max_risk=None):
        super().__init__(
            n_var=len(mu_vec),
            n_obj=2,
            n_ieq_constr=1 if max_risk is not None else 0,
            xl=0.0,
            xu=1.0,
        )
        self.mu_vec = mu_vec
        self.cov_mat = cov_mat
        self.max_risk = max_risk

    def _evaluate(self, X, out, *args, **kwargs):
        weights = X / np.maximum(np.sum(X, axis=1, keepdims=True), EPSILON_NUM)
        returns = weights @ self.mu_vec
        risks = np.sqrt(np.diag(weights @ self.cov_mat @ weights.T))
        out["F"] = np.column_stack([-returns, risks])
        if self.max_risk is not None:
            out["G"] = risks - self.max_risk


class EPTournamentSurvival(Survival):
    """
    Survie (μ+λ) par tournoi stochastique à q adversaires.

    Pour chaque individu de la pool combinée :
    - tirage de q adversaires aléatoires distincts
    - une victoire est comptée si l'individu domine l'adversaire au sens de
      Pareto, ou s'ils sont de même rang mais l'individu a une meilleure
      distance de crowding (départage par diversité)
    - les μ individus avec le plus de victoires survivent

    Cette opération est entièrement vectorisée (O(n) au lieu de O(n²) Python).
    """

    def __init__(self, q_tournament=10):
        super().__init__(filter_infeasible=True)
        self.q_tournament = q_tournament

    def _do(self, problem, pop, n_survive=None, random_state=None, **kwargs):
        n = len(pop)
        if n <= n_survive:
            return pop

        if random_state is None:
            random_state = np.random.default_rng()

        F = pop.get("F")
        fronts = NonDominatedSorting().do(F)
        rank = np.zeros(n, dtype=int)
        crowding = np.zeros(n)
        for k, front in enumerate(fronts):
            rank[front] = k
            crowding[front] = calc_crowding_distance(F[front])

        q = min(self.q_tournament, n - 1)
        opps_idx = random_state.integers(0, n, size=(n, q))

        rank_self = rank[:, None]
        rank_opp = rank[opps_idx]
        crowd_self = crowding[:, None]
        crowd_opp = crowding[opps_idx]

        wins = (
            (rank_self < rank_opp)
            | ((rank_self == rank_opp) & (crowd_self > crowd_opp))
        ).sum(axis=1)

        survivors = np.argsort(-wins, kind="stable")[:n_survive]
        return pop[survivors]


class MOEP(GeneticAlgorithm):
    """
    Multi-Objective Evolutionary Programming.

    Distinctions structurelles vs NSGA-II :
    - Pas de croisement (n_offsprings = pop_size, chaque parent → 1 enfant)
    - Mutation gaussienne avec auto-adaptation log-normale de σ (Schwefel)
    - Sélection (μ+λ) par tournoi stochastique sur dominance de Pareto

    Utilise `self.random_state` (pymoo Generator) pour la pleine
    reproductibilité avec le `seed` passé à minimize().
    """

    def __init__(self, pop_size=80, q_tournament=10, sigma_init=0.15, **kwargs):
        super().__init__(
            pop_size=pop_size,
            n_offsprings=pop_size,
            sampling=FloatRandomSampling(),
            survival=EPTournamentSurvival(q_tournament=q_tournament),
            output=MultiObjectiveOutput(),
            advance_after_initial_infill=True,
            **kwargs,
        )
        self.q_tournament = q_tournament
        self.sigma_init = sigma_init
        self.tau_prime = None
        self.tau = None
        self.sigma_max = None
        self.termination = DefaultMultiObjectiveTermination()

    def _setup(self, problem, **kwargs):
        super()._setup(problem, **kwargs)
        n = problem.n_var
        self.tau_prime = 1.0 / np.sqrt(2.0 * n)
        self.tau = 1.0 / np.sqrt(2.0 * np.sqrt(n))
        box_size = float(np.max(problem.xu - problem.xl))
        self.sigma_max = 0.3 * box_size

    def _initialize_infill(self):
        rng = self.random_state
        X = rng.uniform(
            self.problem.xl,
            self.problem.xu,
            size=(self.pop_size, self.problem.n_var),
        )
        pop = Population.new("X", X)
        sigma = np.full((self.pop_size, self.problem.n_var), self.sigma_init)
        pop.set("sigma", sigma)
        return pop

    def _infill(self):
        rng = self.random_state
        parents_X = self.pop.get("X")
        parents_sigma = self.pop.get("sigma")
        n_off, n_var = parents_X.shape

        r_global = rng.standard_normal((n_off, 1))
        r_local = rng.standard_normal((n_off, n_var))
        off_sigma = parents_sigma * np.exp(
            self.tau_prime * r_global + self.tau * r_local
        )
        off_sigma = np.clip(off_sigma, 1e-5, self.sigma_max)

        off_X = parents_X + off_sigma * rng.standard_normal(parents_X.shape)
        off_X = np.clip(off_X, self.problem.xl, self.problem.xu)

        off = Population.new("X", off_X)
        off.set("sigma", off_sigma)
        return off


st.sidebar.header(
    "⚙️ Configuration Technique" if not simple_mode else "⚙️ Réglages de la Simulation"
)
algo_choice = st.sidebar.selectbox(
    "Algorithme Évolutif" if not simple_mode else "Moteur d'intelligence artificielle",
    ["MOEP (Programmation Évolutive)", "NSGA-II", "Les deux (Comparaison simultanée)"],
)
pop_size = st.sidebar.slider(
    "Taille du groupe de recherche" if simple_mode else "Taille de la population (N)",
    40,
    150,
    80,
)
n_gen = st.sidebar.slider(
    (
        "Nombre de tentatives d'amélioration"
        if simple_mode
        else "Nombre de générations (T)"
    ),
    20,
    100,
    50,
)
seed_val = st.sidebar.number_input(
    "Graine aléatoire" if simple_mode else "Seed (reproductibilité)",
    min_value=0,
    max_value=99999,
    value=42,
    step=1,
)
anim_fps = st.sidebar.slider(
    "Vitesse de l'animation (images/s)" if simple_mode else "FPS de l'animation",
    1,
    30,
    12,
)

st.sidebar.header("🛡️ Protection / Sécurité")
apply_risk_limit = st.sidebar.checkbox(
    "Interdire les portefeuilles trop dangereux"
    if simple_mode
    else "Activer une contrainte de Volatilité maximale"
)
max_risk_val = (
    st.sidebar.slider("Niveau de risque maximum accepté (%)", 5, 60, 25) / 100
    if apply_risk_limit
    else None
)

st.sidebar.header(
    "🎯 Votre Profil d'investisseur" if simple_mode else "🎯 Profil du Décideur (ADOMC)"
)
w_return = st.sidebar.slider(
    "Importance accordée au gain (%)" if simple_mode else "Priorité Rendement (%)",
    10,
    90,
    60,
)
w_risk = 100 - w_return

if not simple_mode:
    risk_free_rate = (
        st.sidebar.slider(
            "Taux sans risque pour Sharpe (% annuel)",
            0.0,
            10.0,
            2.0,
            0.1,
        )
        / 100
    )
else:
    risk_free_rate = 0.02

if "results_data" not in st.session_state:
    st.session_state.results_data = None
if "final_fig" not in st.session_state:
    st.session_state.final_fig = None


def build_animated_figure(
    raw_results, n_gen, ui_mu, ui_vol, w_return, w_risk, max_risk_val, simple_mode, fps
):
    """
    Construit UNE figure Plotly avec des frames d'animation natives.

    Avantages vs N appels à plotly_chart :
    - 1 seul rendu côté Python
    - Animation native côté navigateur (slider, play/pause)
    - L'utilisateur peut scruber dans le temps après la fin du calcul
    """
    x_max = max(ui_vol) * 110
    y_max = max(ui_mu) * 110
    frame_duration_ms = max(33, int(1000 / fps))

    def traces_for_step(step):
        """Construit la liste de traces à afficher pour une génération."""
        traces = []
        for name, res in raw_results.items():
            if not res.history or step >= len(res.history):
                continue
            pop = res.history[step].pop
            F = pop.get("F")
            returns = -F[:, 0] * 100
            risks = F[:, 1] * 100

            best_idx = weighted_topsis(returns, risks, w_return / 100, w_risk / 100)

            color = COLOR_MOEP if name == "MOEP" else COLOR_NSGA
            color_best = COLOR_MOEP_BEST if name == "MOEP" else COLOR_NSGA_BEST

            traces.append(
                go.Scatter(
                    x=risks,
                    y=returns,
                    mode="markers",
                    marker=dict(color=color, opacity=0.6, size=8),
                    name="Portefeuille testé" if simple_mode else f"Front ({name})",
                    showlegend=True,
                )
            )
            traces.append(
                go.Scatter(
                    x=[risks[best_idx]],
                    y=[returns[best_idx]],
                    mode="markers",
                    marker=dict(
                        color=color_best,
                        size=16,
                        symbol="star",
                        line=dict(color="white", width=1),
                    ),
                    name=(
                        "Meilleur choix trouvé"
                        if simple_mode
                        else f"Compromis TOPSIS ({name})"
                    ),
                    showlegend=True,
                )
            )
        return traces

    frames = [
        go.Frame(data=traces_for_step(step), name=str(step + 1))
        for step in range(n_gen)
    ]

    fig = go.Figure(data=traces_for_step(0), frames=frames)

    if max_risk_val is not None:
        fig.add_vline(
            x=max_risk_val * 100,
            line_dash="dash",
            line_color=COLOR_CONSTRAINT,
            annotation_text=(
                "Limite de sécurité" if simple_mode else "Contrainte Risque"
            ),
        )

    fig.update_layout(
        title=(
            "L'IA cherche la meilleure répartition"
            if simple_mode
            else "Dynamique Temporelle des Fronts de Compromis"
        ),
        xaxis_title=(
            "Niveau de risque global (%)"
            if simple_mode
            else "Risque Global (Volatilité %) — MIN"
        ),
        yaxis_title=(
            "Rendement espéré (%)" if simple_mode else "Rendement Espéré (%) — MAX"
        ),
        xaxis=dict(range=[0, x_max]),
        yaxis=dict(range=[0, y_max]),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=80),
        showlegend=True,
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0,
                y=-0.15,
                xanchor="left",
                yanchor="top",
                showactive=False,
                pad=dict(r=10, t=10),
                buttons=[
                    dict(
                        label="▶ Lecture",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=frame_duration_ms, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                active=0,
                currentvalue=dict(
                    prefix=("Étape " if simple_mode else "Génération ") + ": ",
                    visible=True,
                    xanchor="right",
                ),
                x=0.1,
                y=-0.15,
                len=0.85,
                xanchor="left",
                yanchor="top",
                pad=dict(t=10),
                steps=[
                    dict(
                        method="animate",
                        label=str(step + 1),
                        args=[
                            [str(step + 1)],
                            dict(
                                frame=dict(duration=0, redraw=True),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    )
                    for step in range(n_gen)
                ],
            )
        ],
    )
    return fig


with tab_exec:
    st.header(
        "Lancement de la recherche automatique"
        if simple_mode
        else "Suivi Temps Réel de la Convergence Collective"
    )
    st.caption(
        "Utilisez le bouton ▶ Lecture sous le graphique pour visualiser l'évolution génération par génération, "
        "ou faites glisser le curseur pour naviguer manuellement."
    )

    plot_placeholder = st.empty()
    if st.session_state.final_fig is not None:
        plot_placeholder.plotly_chart(
            st.session_state.final_fig, use_container_width=True
        )

    if st.button(
        (
            "🚀 Lancer les calculs"
            if simple_mode
            else "🚀 Déclencher l'Optimisation Stochastique"
        ),
        type="primary",
    ):
        problem = PortfolioProblem(
            mu_vec=ui_mu, cov_mat=ui_cov_matrix, max_risk=max_risk_val
        )

        progress_bar = st.progress(0)
        status_text = st.empty()

        algorithms = {}
        if algo_choice in [
            "MOEP (Programmation Évolutive)",
            "Les deux (Comparaison simultanée)",
        ]:
            algorithms["MOEP"] = MOEP(pop_size=pop_size)
        if algo_choice in ["NSGA-II", "Les deux (Comparaison simultanée)"]:
            algorithms["NSGA-II"] = NSGA2(pop_size=pop_size)

        raw_results = {}
        n_algos = len(algorithms)
        for i, (name, algo) in enumerate(algorithms.items()):
            status_text.text(
                f"Optimisation en cours ({name})..."
                if simple_mode
                else f"Évolution stochastique des fronts ({name})..."
            )
            res = minimize(
                problem,
                algo,
                ("n_gen", n_gen),
                seed=int(seed_val),
                verbose=False,
                save_history=True,
            )
            raw_results[name] = res
            progress_bar.progress((i + 1) / n_algos)
            time.sleep(0.05)

        status_text.text("Construction de l'animation interactive...")
        fig = build_animated_figure(
            raw_results,
            n_gen,
            ui_mu,
            ui_vol,
            w_return,
            w_risk,
            max_risk_val,
            simple_mode,
            anim_fps,
        )

        plot_placeholder.plotly_chart(fig, use_container_width=True)
        status_text.empty()
        progress_bar.empty()
        st.success(
            "🎉 Calculs terminés ! Utilisez ▶ Lecture pour voir l'évolution, ou allez sur le dernier onglet pour le rapport."
        )

        st.session_state.final_fig = fig
        st.session_state.results_data = {
            "raw_results": raw_results,
            "assets_list": assets_list,
            "ui_mu": ui_mu,
            "ui_vol": ui_vol,
            "seed": int(seed_val),
            "risk_free_rate": risk_free_rate,
        }


with tab_analysis:
    st.header("📋 Recommandation finale et Synthèse")

    if st.session_state.results_data is None:
        st.warning(
            "⚠️ Veuillez d'abord cliquer sur le bouton de l'onglet précédent pour lancer les simulations."
        )
    else:
        data_store = st.session_state.results_data
        rf = data_store.get("risk_free_rate", 0.0)

        has_feasible = any(
            res.X is not None for res in data_store["raw_results"].values()
        )

        if has_feasible and not simple_mode:
            st.subheader("📊 Indicateurs de qualité des fronts de Pareto")

            all_F = [
                np.atleast_2d(res.F)
                for res in data_store["raw_results"].values()
                if res.F is not None
            ]
            if len(all_F) >= 1:
                union_F = np.vstack(all_F)
                ref_fronts = NonDominatedSorting().do(union_F)
                ref_F = union_F[ref_fronts[0]]

                ref_point = np.array([0.0, float(max(data_store["ui_vol"]))])
                hv_indicator = Hypervolume(ref_point=ref_point)
                igd_indicator = IGD(ref_F)

                cols = st.columns(len(data_store["raw_results"]))
                for col, (name, res) in zip(cols, data_store["raw_results"].items()):
                    if res.F is not None:
                        hv_val = hv_indicator(res.F)
                        igd_val = igd_indicator(res.F)
                        with col:
                            st.markdown(f"**{name}**")
                            st.metric("Hypervolume (↑ mieux)", f"{hv_val:.4f}")
                            st.metric("IGD (↓ mieux)", f"{igd_val:.4f}")
                            st.caption(f"Front non-dominé : {len(res.F)} solutions")
                st.caption(
                    "HV : volume dominé par le front, calculé avec un point de référence "
                    "invariant (rendement nul, volatilité maximale individuelle) — comparable "
                    "entre runs. IGD : distance moyenne du front trouvé au front de référence "
                    "approché (union non-dominée), donc relatif (l'algo qui contribue le plus "
                    "à l'union aura un IGD biaisé à la baisse)."
                )
                st.markdown("---")

        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:

            df_configuration = pd.DataFrame(
                {
                    "Paramètre Décisionnel": [
                        "Date de Simulation",
                        "Seed",
                        "Priorité Rendement",
                        "Priorité Risque",
                        "Taux sans risque",
                        "Statut Calcul",
                    ],
                    "Valeur Spécifiée": [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        data_store.get("seed", "N/A"),
                        f"{w_return} %",
                        f"{w_risk} %",
                        f"{rf*100:.2f} %",
                        "Validé" if has_feasible else "Contraintes saturées",
                    ],
                }
            )
            df_configuration.to_excel(
                writer, sheet_name="Configuration_Générale", index=False
            )

            if not has_feasible:
                st.error(
                    "❌ **Alerte Contraintes Métier :** L'algorithme n'a trouvé aucune solution respectant vos critères."
                )
                st.info(
                    "💡 Augmentez le seuil de risque maximum accepté dans la barre latérale ou désactivez la contrainte, puis relancez."
                )
            else:
                for name, res in data_store["raw_results"].items():
                    if res.X is None:
                        continue

                    st.subheader(f"💼 La recette de répartition conseillée ({name})")

                    final_X = np.atleast_2d(res.X)
                    final_F = np.atleast_2d(res.F)
                    weights = final_X / np.maximum(
                        np.sum(final_X, axis=1, keepdims=True), EPSILON_NUM
                    )

                    returns_pct = -final_F[:, 0] * 100
                    risks_pct = final_F[:, 1] * 100

                    best_idx = weighted_topsis(
                        returns_pct, risks_pct, w_return / 100, w_risk / 100
                    )
                    best_weights = weights[best_idx]
                    final_return = float(returns_pct[best_idx])
                    final_risk = float(risks_pct[best_idx])

                    sharpe_ratio = (
                        (final_return / 100 - rf) / (final_risk / 100)
                        if final_risk > 0
                        else 0.0
                    )

                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric(
                        (
                            "Rendement attendu"
                            if simple_mode
                            else "Rendement Arbitré (R_p)"
                        ),
                        f"{final_return:.2f} % / an",
                    )
                    col_m2.metric(
                        (
                            "Niveau de risque"
                            if simple_mode
                            else "Volatilité Arbitrée (σ_p)"
                        ),
                        f"{final_risk:.2f} %",
                    )
                    if not simple_mode:
                        col_m3.metric(
                            f"Ratio de Sharpe (r_f = {rf*100:.1f}%)",
                            f"{sharpe_ratio:.2f}",
                        )

                    summary_df = pd.DataFrame(
                        {
                            "Placement" if simple_mode else "Actif": data_store[
                                "assets_list"
                            ],
                            (
                                "Pourcentage à y investir (%)"
                                if simple_mode
                                else "Allocation Capital (%)"
                            ): np.round(best_weights * 100, 2),
                        }
                    )
                    summary_df = summary_df.sort_values(
                        by=summary_df.columns[1], ascending=False
                    )
                    summary_df_filtered = summary_df[summary_df.iloc[:, 1] > 0.1]

                    if summary_df_filtered.empty:
                        summary_df_filtered = summary_df.head(3)
                        st.caption(
                            "Aucune allocation > 0.1% détectée ; affichage des 3 plus fortes."
                        )

                    st.dataframe(
                        summary_df_filtered, use_container_width=True, hide_index=True
                    )

                    fig_front = go.Figure()
                    color = COLOR_MOEP if name == "MOEP" else COLOR_NSGA
                    color_best = COLOR_MOEP_BEST if name == "MOEP" else COLOR_NSGA_BEST

                    order = np.argsort(risks_pct)
                    fig_front.add_trace(
                        go.Scatter(
                            x=risks_pct[order],
                            y=returns_pct[order],
                            mode="lines+markers",
                            line=dict(color=color, width=2),
                            marker=dict(color=color, size=8),
                            name="Front de Pareto",
                        )
                    )
                    fig_front.add_trace(
                        go.Scatter(
                            x=[final_risk],
                            y=[final_return],
                            mode="markers",
                            marker=dict(
                                color=color_best,
                                size=18,
                                symbol="star",
                                line=dict(color="white", width=2),
                            ),
                            name="Compromis TOPSIS retenu",
                        )
                    )
                    if max_risk_val is not None:
                        fig_front.add_vline(
                            x=max_risk_val * 100,
                            line_dash="dash",
                            line_color=COLOR_CONSTRAINT,
                            annotation_text="Contrainte",
                        )
                    fig_front.update_layout(
                        title=f"Front de Pareto final — {name}",
                        xaxis_title="Risque (%)",
                        yaxis_title="Rendement (%)",
                        template="plotly_white",
                        height=400,
                        margin=dict(l=40, r=40, t=50, b=40),
                    )
                    st.plotly_chart(fig_front, use_container_width=True)

                    df_pareto_all = pd.DataFrame(
                        weights, columns=data_store["assets_list"]
                    )
                    df_pareto_all["Rendement_%"] = returns_pct
                    df_pareto_all["Risque_%"] = risks_pct
                    df_pareto_all.to_excel(
                        writer, sheet_name=f"Pareto_{name}", index=False
                    )

                    summary_df.to_excel(
                        writer, sheet_name=f"Allocation_{name}", index=False
                    )

                    st.markdown("#### 🎙️ L'explication de notre conseiller virtuel")
                    highest_asset = summary_df_filtered.iloc[0, 0]
                    highest_val = summary_df_filtered.iloc[0, 1]
                    max_possible = float(max(data_store["ui_mu"]) * 100)

                    if simple_mode:
                        explanation = f"""
                        Pour satisfaire vos choix, notre système a créé un mélange stratégique. 
                        La majeure partie de votre argent (**{highest_val:.2f}%**) est placée sur **{highest_asset}** car c'est le moteur principal de vos gains.
                        
                        **Pourquoi vous ne gagnez pas plus ?** Le placement le plus rentable de votre liste propose au maximum **{max_possible:.2f}%**. Il est donc impossible de dépasser ce chiffre. De plus, l'IA a volontairement choisi de ne pas tout mettre dessus afin de vous protéger des baisses brutales grâce aux autres placements.
                        """
                    else:
                        explanation = f"""
                        L'optimisation bi-objectif montre une convergence robuste. La solution retenue par arbitrage **TOPSIS** se positionne à un rendement de **{final_return:.2f}%** pour une volatilité de **{final_risk:.2f}%**, dégageant un **Ratio de Sharpe de {sharpe_ratio:.2f}** (taux sans risque = {rf*100:.1f}%).
                        
                        **Analyse de la Borne Supérieure :** Le rendement maximum accessible par l'écosystème avec vos paramètres actuels est limité à **{max_possible:.2f}%** (portefeuille saturé à 100% sur l'actif à espérance maximale). L'algorithme dégage un compromis optimal en deçà de cette frontière afin de minimiser les facteurs de risques de la matrice de covariance.
                        """
                    st.info(explanation)
                    st.markdown("---")

        st.download_button(
            label="📥 Télécharger le Rapport d'Arbitrage (Excel)",
            data=excel_buffer.getvalue(),
            file_name=f"Rapport_SID_Portefeuille_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
