import numpy as np
from pymoo.algorithms.base.genetic import GeneticAlgorithm
from pymoo.core.population import Population
from pymoo.core.survival import Survival
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.survival.rank_and_crowding.metrics import calc_crowding_distance
from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.util.display.multi import MultiObjectiveOutput
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting


class EPTournamentSurvival(Survival):

    def __init__(self, q_tournament: int = 10):
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
    """Multi-Objective Evolutionary Programming algorithm."""

    def __init__(
        self,
        pop_size: int = 80,
        q_tournament: int = 10,
        sigma_init: float = 0.15,
        **kwargs
    ):
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
