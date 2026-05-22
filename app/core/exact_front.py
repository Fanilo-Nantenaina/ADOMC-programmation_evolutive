from typing import List, Optional

import numpy as np
from scipy.optimize import minimize


def _solve_min_risk_for_target_return(
    mu: np.ndarray,
    cov: np.ndarray,
    target_return: float,
    max_weight: Optional[float] = None,
) -> Optional[np.ndarray]:

    n = len(mu)

    def objective(w: np.ndarray) -> float:
        return float(w @ cov @ w)

    def objective_grad(w: np.ndarray) -> np.ndarray:
        return 2.0 * cov @ w

    constraints = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        {"type": "ineq", "fun": lambda w: float(w @ mu - target_return)},
    ]
    upper = max_weight if max_weight is not None else 1.0
    bounds = [(0.0, upper)] * n

    x0 = np.ones(n) / n

    res = minimize(
        objective,
        x0,
        jac=objective_grad,
        constraints=constraints,
        bounds=bounds,
        method="SLSQP",
        options={"ftol": 1e-9, "maxiter": 300},
    )
    if not res.success:
        return None
    return res.x


def compute_exact_front(
    mu: np.ndarray,
    cov: np.ndarray,
    n_points: int = 30,
) -> List[dict]:

    n = len(mu)
    mu_min = float(mu.min())
    mu_max = float(mu.max())

    if mu_max - mu_min < 1e-10:
        w = np.ones(n) / n
        ret = float(w @ mu)
        risk = float(np.sqrt(w @ cov @ w))
        return [
            {
                "return_pct": ret * 100,
                "risk_pct": risk * 100,
                "weights": w.tolist(),
            }
        ]

    epsilons = np.linspace(mu_min, mu_max, n_points)
    front: List[dict] = []
    seen_keys = set()

    for eps in epsilons:
        w = _solve_min_risk_for_target_return(mu, cov, eps)
        if w is None:
            continue
        ret = float(w @ mu)
        risk = float(np.sqrt(w @ cov @ w))

        key = (round(ret, 6), round(risk, 6))
        if key in seen_keys:
            continue
        seen_keys.add(key)

        front.append(
            {
                "return_pct": ret * 100,
                "risk_pct": risk * 100,
                "weights": [float(x) for x in w.tolist()],
            }
        )

    front.sort(key=lambda p: p["return_pct"])
    return front
