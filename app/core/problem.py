from typing import Optional

import numpy as np
from pymoo.core.problem import Problem

EPSILON_NUM = 1e-8


def decode_weights(
    X: np.ndarray,
    cardinality_max: Optional[int] = None,
) -> np.ndarray:

    n = X.shape[1]

    if cardinality_max is not None and cardinality_max < n:
        K = int(cardinality_max)
        top_k_idx = np.argpartition(X, -K, axis=1)[:, -K:]
        mask = np.zeros_like(X)
        np.put_along_axis(mask, top_k_idx, 1.0, axis=1)
        X_masked = X * mask
    else:
        X_masked = X

    sums = np.maximum(X_masked.sum(axis=1, keepdims=True), EPSILON_NUM)
    return X_masked / sums


class PortfolioProblem(Problem):

    def __init__(
        self,
        mu_vec: np.ndarray,
        cov_mat: np.ndarray,
        max_risk: Optional[float] = None,
        cardinality_max: Optional[int] = None,
    ):
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
        self.cardinality_max = cardinality_max

    def _evaluate(self, X, out, *args, **kwargs):
        weights = decode_weights(X, cardinality_max=self.cardinality_max)
        returns = weights @ self.mu_vec
        risks = np.sqrt(np.diag(weights @ self.cov_mat @ weights.T))
        out["F"] = np.column_stack([-returns, risks])
        if self.max_risk is not None:
            out["G"] = risks - self.max_risk
