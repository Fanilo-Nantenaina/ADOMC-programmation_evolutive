from typing import Dict, Optional

import numpy as np
from pymoo.indicators.hv import Hypervolume
from pymoo.indicators.igd import IGD
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting


def compute_indicators(
    F_per_algo: Dict[str, np.ndarray],
    vol_max: float,
    reference_front: Optional[np.ndarray] = None,
) -> Dict[str, dict]:

    if not F_per_algo:
        return {}

    if reference_front is not None and len(reference_front) > 0:
        ref_F = reference_front
        ref_kind = "exact"
    else:
        union_F = np.vstack(list(F_per_algo.values()))
        ref_fronts = NonDominatedSorting().do(union_F)
        ref_F = union_F[ref_fronts[0]]
        ref_kind = "union"

    ref_point = np.array([0.0, vol_max])
    hv = Hypervolume(ref_point=ref_point)
    igd = IGD(ref_F)

    results: Dict[str, dict] = {}
    for name, F in F_per_algo.items():
        results[name] = {
            "hv": float(hv(F)),
            "igd": float(igd(F)),
            "igd_reference_kind": ref_kind,
            "spacing": compute_spacing(F),
            "spread": compute_spread(F),
            "n_solutions": int(len(F)),
        }
    return results


def compute_spacing(F: np.ndarray) -> float:

    n = len(F)
    if n < 2:
        return 0.0

    d_min = np.zeros(n)
    for i in range(n):
        diffs = np.abs(F - F[i]).sum(axis=1)
        diffs[i] = np.inf
        d_min[i] = diffs.min()

    d_mean = d_min.mean()
    return float(np.sqrt(np.mean((d_min - d_mean) ** 2)))


def compute_spread(F: np.ndarray) -> float:

    n = len(F)
    if n < 2:
        return 0.0

    idx_min_obj1 = int(np.argmin(F[:, 0]))
    idx_min_obj2 = int(np.argmin(F[:, 1]))
    return float(np.linalg.norm(F[idx_min_obj1] - F[idx_min_obj2]))


def hv_for_stagnation(F: np.ndarray, vol_max: float) -> float:
    """Lightweight HV computation for stagnation detection during streaming."""
    if len(F) == 0:
        return 0.0
    ref_point = np.array([0.0, vol_max])
    return float(Hypervolume(ref_point=ref_point)(F))
