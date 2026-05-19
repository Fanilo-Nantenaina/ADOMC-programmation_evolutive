import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pymoo.core.problem import Problem
from pymoo.core.algorithm import Algorithm
from pymoo.core.population import Population
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.operators.crossover import NoCrossover
from pymoo.operators.survival import RankAndCrowdingSurvival
from pymoo.optimize import minimize
from pymoo.indicators.hv import HV
import time
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler

np.random.seed(42)
n_assets = 10
assets = [f"Actif_{i+1}" for i in range(n_assets)]

mu = np.random.uniform(0.05, 0.25, n_assets)
cov = np.random.uniform(0.01, 0.08, (n_assets, n_assets))
cov = (cov + cov.T) / 2
np.fill_diagonal(cov, np.random.uniform(0.02, 0.15, n_assets))


class PortfolioProblem(Problem):
    def __init__(self):
        super().__init__(n_var=n_assets, n_obj=2, n_ieq_constr=1, xl=0.0, xu=1.0)
        self.mu = mu
        self.cov = cov

    def _evaluate(self, X, out, *args, **kwargs):
        weights = X / np.sum(X, axis=1, keepdims=True)
        returns = weights @ self.mu
        risks = np.sqrt(np.diag(weights @ self.cov @ weights.T))

        out["F"] = np.column_stack([-returns, risks])
        out["G"] = np.abs(np.sum(X, axis=1) - 1)


problem = PortfolioProblem()


class MOEP_Portfolio(Algorithm):
    def __init__(
        self, pop_size=120, n_offsprings=None, sigma_init=0.12, tau=0.08, **kwargs
    ):
        super().__init__(**kwargs)
        self.pop_size = pop_size
        self.n_offsprings = n_offsprings or pop_size
        self.sigma_init = sigma_init
        self.tau = tau
        self.tau_prime = tau / np.sqrt(2 * n_assets)

        self.sampling = FloatRandomSampling()
        self.crossover = NoCrossover()
        self.survival = RankAndCrowdingSurvival()

    def _initialize_infill(self):
        pop = self.sampling.do(problem, self.pop_size)
        self.sigma = np.full((self.pop_size, n_assets), self.sigma_init)
        return pop

    def _infill(self):
        indices = np.random.permutation(len(self.pop))[: self.n_offsprings]
        parents = self.pop[indices]
        parent_sigma = self.sigma[indices]

        rand1 = np.random.normal(0, 1, (len(parents), 1))
        rand2 = np.random.normal(0, 1, (len(parents), n_assets))

        sigma_new = parent_sigma * np.exp(self.tau_prime * rand1 + self.tau * rand2)
        sigma_new = np.maximum(sigma_new, 1e-5)

        offspring = parents + sigma_new * np.random.normal(0, 1, parents.shape)
        offspring = np.clip(offspring, 0, 1)

        self.offspring_sigma = sigma_new
        return Population.new("X", offspring)

    def _advance(self, infills=None, **kwargs):
        if infills is not None:
            self.pop = Population.merge(self.pop, infills)
            self.sigma = np.vstack((self.sigma, self.offspring_sigma))

        self.pop = self.survival.do(problem, self.pop, n_survive=self.pop_size)
        self.sigma = self.sigma[: self.pop_size]


def run_multiple_experiments(n_runs=10, n_gen=150, pop_size=120):
    results = []
    hv = HV(ref_point=np.array([0, 1.5]))

    for r in range(n_runs):
        start = time.time()
        algo = MOEP_Portfolio(pop_size=pop_size, seed=42 + r)
        res = minimize(problem, algo, ("n_gen", n_gen), seed=42 + r, verbose=False)
        duration = time.time() - start

        weights_norm = res.X / np.sum(res.X, axis=1, keepdims=True)
        returns = -res.F[:, 0]
        risks = res.F[:, 1]

        results.append(
            {
                "run": r,
                "hv": hv(res.F),
                "returns": returns,
                "risks": risks,
                "weights": weights_norm,
                "time": duration,
                "n_solutions": len(res.F),
            }
        )
        print(f"Run {r+1}/{n_runs} terminé - HV: {hv(res.F):.4f}")

    return results


def topsis_with_profile(front_returns, front_risks, weights_matrix, profile="modéré"):
    F = np.column_stack([front_returns, front_risks])

    profiles = {
        "conservateur": np.array([0.3, 0.7]),
        "modéré": np.array([0.5, 0.5]),
        "agressif": np.array([0.7, 0.3]),
    }
    w_obj = profiles.get(profile, profiles["modéré"])

    scaler = MinMaxScaler()
    nF = scaler.fit_transform(F)

    ideal_pos = np.array([nF[:, 0].max(), nF[:, 1].min()])
    ideal_neg = np.array([nF[:, 0].min(), nF[:, 1].max()])

    dist_pos = np.sqrt(np.sum(w_obj * (nF - ideal_pos) ** 2, axis=1))
    dist_neg = np.sqrt(np.sum(w_obj * (nF - ideal_neg) ** 2, axis=1))

    scores = dist_neg / (dist_pos + dist_neg + 1e-8)
    best_idx = np.argmax(scores)

    allocation = pd.DataFrame(
        {"Actif": assets, "Poids (%)": np.round(weights_matrix[best_idx] * 100, 2)}
    ).sort_values("Poids (%)", ascending=False)

    return best_idx, allocation, scores[best_idx]


if __name__ == "__main__":
    print("=== Optimisation de Portefeuille avec MOEP ===\n")
    experiments = run_multiple_experiments(n_runs=8, n_gen=120, pop_size=100)

    best_run = max(experiments, key=lambda x: x["hv"])
    returns = best_run["returns"]
    risks = best_run["risks"]
    weights_matrix = best_run["weights"]

    print(f"\nMeilleur HV : {best_run['hv']:.4f}")

    for profile in ["conservateur", "modéré", "agressif"]:
        idx, alloc, score = topsis_with_profile(returns, risks, weights_matrix, profile)
        print(f"\n--- Profil {profile.upper()} (score TOPSIS: {score:.4f}) ---")
        print(alloc.head(6))
