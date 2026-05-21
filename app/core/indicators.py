from typing import Dict

import numpy as np
from pymoo.indicators.hv import Hypervolume
from pymoo.indicators.igd import IGD
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting


def compute_indicators(
    F_per_algo: Dict[str, np.ndarray], vol_max: float
) -> Dict[str, dict]:
    if not F_per_algo:
        return {}

    union_F = np.vstack(list(F_per_algo.values()))
    ref_fronts = NonDominatedSorting().do(union_F)
    ref_F = union_F[ref_fronts[0]]

    ref_point = np.array([0.0, vol_max])
    hv = Hypervolume(ref_point=ref_point)
    igd = IGD(ref_F)

    return {
        name: {"hv": float(hv(F)), "igd": float(igd(F))}
        for name, F in F_per_algo.items()
    }
