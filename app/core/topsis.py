from typing import List, Literal, Sequence

import numpy as np
from sklearn.preprocessing import MinMaxScaler

EPSILON_NUM = 1e-8

Direction = Literal["max", "min"]


def weighted_topsis(
    returns_pct: np.ndarray,
    risks_pct: np.ndarray,
    w_return: float,
    w_risk: float,
) -> int:

    F = np.column_stack([returns_pct, risks_pct])
    return topsis_nd(
        criteria_matrix=F,
        weights=np.array([w_return, w_risk]),
        directions=["max", "min"],
    )


def topsis_nd(
    criteria_matrix: np.ndarray,
    weights: np.ndarray,
    directions: Sequence[Direction],
) -> int:

    n_sol, n_crit = criteria_matrix.shape
    if len(weights) != n_crit or len(directions) != n_crit:
        raise ValueError(
            f"Length mismatch : criteria={n_crit}, weights={len(weights)}, "
            f"directions={len(directions)}"
        )

    if all(np.std(criteria_matrix[:, j]) < EPSILON_NUM for j in range(n_crit)):
        return 0

    scaler = MinMaxScaler()
    nF = scaler.fit_transform(criteria_matrix)

    w = np.asarray(weights, dtype=float)
    w = w / max(w.sum(), EPSILON_NUM)

    ideal_pos = np.zeros(n_crit)
    ideal_neg = np.zeros(n_crit)
    for j in range(n_crit):
        if directions[j] == "max":
            ideal_pos[j] = nF[:, j].max()
            ideal_neg[j] = nF[:, j].min()
        else:
            ideal_pos[j] = nF[:, j].min()
            ideal_neg[j] = nF[:, j].max()

    d_pos = np.sqrt(np.sum(w * (nF - ideal_pos) ** 2, axis=1))
    d_neg = np.sqrt(np.sum(w * (nF - ideal_neg) ** 2, axis=1))
    closeness = d_neg / (d_pos + d_neg + EPSILON_NUM)
    return int(np.argmax(closeness))


def compute_criteria_matrix(
    weights_matrix: np.ndarray,
    returns_pct: np.ndarray,
    risks_pct: np.ndarray,
    risk_free_rate: float,
) -> np.ndarray:

    n_sol = weights_matrix.shape[0]

    ret_prop = returns_pct / 100.0
    risk_prop = risks_pct / 100.0
    sharpe = np.zeros(n_sol)
    valid = risk_prop > 0
    sharpe[valid] = (ret_prop[valid] - risk_free_rate) / (
        risk_prop[valid] + EPSILON_NUM
    )

    hhi = np.sum(weights_matrix**2, axis=1)

    max_weight = np.max(weights_matrix, axis=1)

    return np.column_stack([returns_pct, risks_pct, sharpe, hhi, max_weight])


DEFAULT_DIRECTIONS: List[Direction] = ["max", "min", "max", "min", "min"]
