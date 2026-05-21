import numpy as np
from sklearn.preprocessing import MinMaxScaler

EPSILON_NUM = 1e-8


def weighted_topsis(
    returns_pct: np.ndarray,
    risks_pct: np.ndarray,
    w_return: float,
    w_risk: float,
) -> int:
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
