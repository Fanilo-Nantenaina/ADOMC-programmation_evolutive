import numpy as np
from pymoo.core.problem import Problem

EPSILON_NUM = 1e-8


class PortfolioProblem(Problem):

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
