"""New independent REIMPLEMENTATION of layer-block distance metrics.

Not historical Project GENESIS experiment code. Requires numpy.
Usage: import summarize_blocks; pass R and per-layer parameter sizes.
No experiments are executed or data reproduced by importing this module.
"""
from __future__ import annotations
import numpy as np


def summarize_blocks(matrix, block_sizes):
    """Return RMS, distance-bin mass, offdiag mass, and two consistency audits.

    RMS(k) = sqrt(sum_{|i-j|=k} ||R_ij||_F^2 / count_k)
    mass(k) = sum_{|i-j|=k} ||R_ij||_F^2 / ||R||_F^2

    If blocks have unequal sizes, these are *block* RMS values, not
    per-parameter element RMS; cross-architecture comparisons need care.
    """
    a = np.asarray(matrix)
    dims = [int(x) for x in block_sizes]
    if a.ndim != 2 or a.shape[0] != a.shape[1]:
        raise ValueError("matrix must be square")
    if len(dims) == 0 or min(dims) <= 0 or sum(dims) != a.shape[0]:
        raise ValueError("invalid block sizes")
    if not np.isfinite(a).all():
        raise ValueError("non-finite matrix")
    L = len(dims)
    starts = np.cumsum([0] + dims)
    energy = np.zeros((L, L), dtype=float)
    norm = np.zeros((L, L), dtype=float)
    for i in range(L):
        for j in range(L):
            block = a[starts[i]:starts[i+1], starts[j]:starts[j+1]]
            v = float(np.linalg.norm(block, ord="fro"))
            norm[i, j] = v
            energy[i, j] = v * v
    sums = np.array(
        [sum(energy[i, j] for i in range(L) for j in range(L)
             if abs(i-j) == k) for k in range(L)],
        dtype=float
    )
    counts = np.array([L if k == 0 else 2*(L-k) for k in range(L)])
    rms = np.sqrt(sums / counts)
    total = float(sums.sum())
    if total == 0:
        raise ValueError("zero matrix has undefined relative mass")
    mass = sums / total
    normalized = rms / rms[0] if rms[0] > 0 else np.full_like(rms, np.nan)
    return {
        "block_norms": norm,
        "energy_per_pair": energy,
        "counts": counts,
        "rms_by_distance": rms,
        "normalized_rms": normalized,
        "mass_by_distance": mass,
        "offdiag_mass": float(1 - mass[0]),
        "energy_consistency_error": float(abs(total - np.linalg.norm(a, "fro")**2)),
        "symmetry_error": float(np.linalg.norm(a - a.T, "fro")
                                / max(np.linalg.norm(a, "fro"), 1e-300)),
    }


def uniform_offdiag_upper_bound(layers: int, c: float) -> float:
    """Mass upper bound when max normalized RMS(k) <= c for all k>=1."""
    if layers < 1 or c < 0:
        raise ValueError("invalid L or c")
    z = (layers - 1) * c * c
    return float(z / (1 + z))


def relative_inverse_residual(a, x) -> float:
    """||A X-I||_F / ||I||_F; small backward error ≠ small forward error."""
    a, x = np.asarray(a), np.asarray(x)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or a.shape != x.shape:
        raise ValueError("invalid matrix shapes")
    n = a.shape[0]
    return float(np.linalg.norm(a @ x - np.eye(n), "fro") / np.sqrt(n))


if __name__ == "__main__":
    print("Reference metric utilities; no original experimental results included.")
