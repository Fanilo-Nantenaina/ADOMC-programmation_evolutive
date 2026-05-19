"""
Couche métier : problème d'optimisation, algorithmes évolutionnaires,
fonctions utilitaires mathématiques. Aucune dépendance Streamlit.
"""

import numpy as np
from sklearn.preprocessing import MinMaxScaler

from pymoo.algorithms.base.genetic import GeneticAlgorithm
from pymoo.core.population import Population
from pymoo.core.problem import Problem
from pymoo.core.survival import Survival
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.survival.rank_and_crowding.metrics import calc_crowding_distance
from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.util.display.multi import MultiObjectiveOutput
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from config import EPSILON_NUM, EIGENVALUE_FLOOR


def weighted_topsis(returns_pct, risks_pct, w_return, w_risk):
    """
    TOPSIS pondéré bi-objectif.

    Paramètres
    ----------
    returns_pct : (n,) rendements en %, À MAXIMISER
    risks_pct   : (n,) risques en %, À MINIMISER
    w_return, w_risk : poids du décideur en [0, 1]

    Retourne
    -------
    int : index du meilleur compromis selon la proximité relative à l'idéal positif.

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


class PortfolioProblem(Problem):
    """
    Problème bi-objectif de Markowitz :
    - f1 = -E[R_p] (rendement espéré, à maximiser → on minimise son opposé)
    - f2 =  σ_p    (volatilité, à minimiser)

    Variables X ∈ [0,1]^n normalisées en interne en w = X / sum(X) pour
    respecter ∑w_i = 1, w_i ≥ 0. Encodage redondant mais permettant l'usage
    direct des opérateurs évolutionnaires en boîte ∈ [0,1]^n.
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

    Pour chaque individu :
    - q adversaires aléatoires sont tirés ;
    - une victoire est comptée si l'individu domine au sens de Pareto, ou si
      égalité de rang avec meilleure distance de crowding ;
    - les μ avec le plus de victoires survivent.

    Opération entièrement vectorisée (numpy broadcasting).
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
    Multi-Objective Evolutionary Programming (Fogel-style authentique).

    Distinctions structurelles vs NSGA-II :
    - Pas de croisement (n_offsprings = pop_size, chaque parent → 1 enfant)
    - Mutation gaussienne avec auto-adaptation log-normale de σ (Schwefel)
    - Sélection (μ+λ) par tournoi stochastique sur dominance de Pareto

    Utilise `self.random_state` (pymoo Generator) pour la pleine reproductibilité.
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
