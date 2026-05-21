from typing import Tuple

import numpy as np

EIGENVALUE_FLOOR = 1e-10


def project_to_psd(
    cov_matrix: np.ndarray,
    floor: float = EIGENVALUE_FLOOR,
) -> Tuple[np.ndarray, float, bool]:
    eigvals, eigvecs = np.linalg.eigh(cov_matrix)
    min_eig = float(eigvals.min())
    if min_eig < floor:
        eigvals_clipped = np.maximum(eigvals, floor)
        corrected = eigvecs @ np.diag(eigvals_clipped) @ eigvecs.T
        return corrected, min_eig, True
    return cov_matrix, min_eig, False
