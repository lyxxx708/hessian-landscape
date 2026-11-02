"""G0 numerical references for prospective GENESIS curvature revalidation.

NumPy-only small-matrix oracle and unbiased block-energy probes.
NOT the large-scale GPU study; no 2025 historical data is read.
"""
from __future__ import annotations
from collections.abc import Callable, Sequence
import numpy as np


def groups(sizes: Sequence[int]) -> list[slice]:
    if not sizes or any(int(n) != n or n <= 0 for n in sizes):
        raise ValueError("positive integer block sizes required")
    starts = np.cumsum([0, *sizes])
    return [slice(int(starts[i]), int(starts[i + 1])) for i in range(len(sizes))]


def cg_spd(apply: Callable[[np.ndarray], np.ndarray], rhs: np.ndarray,
           tol: float = 1e-10, max_iter: int | None = None):
    """Return x, relative TRUE residual, converged, iterations. SPD-only CG."""
    b = np.asarray(rhs, dtype=np.float64)
    if b.ndim != 1 or not b.size or not np.isfinite(b).all() or not 0 < tol < 1:
        raise ValueError("invalid CG input")
    n = b.size
    limit = max_iter if max_iter is not None else 10 * n
    if limit < 1:
        raise ValueError("positive iteration budget required")
    x = np.zeros(n)
    r = b.copy()
    p = r.copy()
    rr = float(r @ r)
    nb = float(np.linalg.norm(b))
    if nb == 0:
        return x, 0., True, 0
    for iteration in range(1, limit + 1):
        q = np.asarray(apply(p), dtype=np.float64)
        if q.shape != b.shape or not np.isfinite(q).all():
            raise ValueError("invalid matvec")
        pq = float(p @ q)
        if pq <= 0:
            raise ValueError("operator is not SPD on this CG direction")
        alpha = rr / pq
        x += alpha * p
        r -= alpha * q
        rr_new = float(r @ r)
        if np.sqrt(rr_new) / nb <= tol:
            err = float(np.linalg.norm(np.asarray(apply(x)) - b) / nb)
            return x, err, err <= tol, iteration
        p = r + (rr_new / rr) * p
        rr = rr_new
    err = float(np.linalg.norm(np.asarray(apply(x)) - b) / nb)
    return x, err, False, limit


def dense_utility(undamped_ggn: np.ndarray, gradient: np.ndarray,
                  sizes: Sequence[int], damping: float,
                  train_jacobian: np.ndarray | None = None) -> dict:
    """Small dense GGN oracle vs best-scaled precise block-GGN direction.

    The caller must use one fixed loss, batch, checkpoint and parameter order.
    Quadratic utility is not real training speed. g near zero is INELIGIBLE.
    """
    G = np.asarray(undamped_ggn, dtype=np.float64)
    g = np.asarray(gradient, dtype=np.float64)
    if G.ndim != 2 or G.shape[0] != G.shape[1] or G.shape[0] == 0:
        raise ValueError("GGN must be square and nonempty")
    n = len(G)
    slices = groups(sizes)
    if sum(sizes) != n or g.shape != (n,) or not np.isfinite(G).all() or not np.isfinite(g).all():
        raise ValueError("dimensions or finite-value check failed")
    if not np.isfinite(damping) or damping <= 0:
        raise ValueError("positive damping required")
    if np.linalg.norm(G - G.T) > 1e-9 * max(1., np.linalg.norm(G)):
        raise ValueError("GGN is not symmetric")
    G = (G + G.T) / 2
    evals = np.linalg.eigvalsh(G)
    if evals[0] < -1e-9 * max(1., evals[-1]):
        raise ValueError("GGN is not PSD: exact-H/indefinite object not allowed")
    Q = G + damping * np.eye(n)
    if np.linalg.eigvalsh(Q)[0] <= 0:
        raise ValueError("damped GGN is not SPD")
    if np.linalg.norm(g) <= 1e-12:
        return {"status": "INELIGIBLE_ZERO_GRADIENT", "delta": None, "eta": None}
    full = -np.linalg.solve(Q, g)
    block = np.empty_like(g)
    for s in slices:
        block[s] = -np.linalg.solve(Q[s,s], g[s])
    qbb = float(block @ Q @ block)
    fg = float(-g @ full)
    if qbb <= 0 or fg <= 0:
        raise ValueError("invalid quadratic gain")
    alpha = -float(g @ block) / qbb
    eta = (float(g @ block) ** 2 / qbb) / fg
    if eta > 1 + 1e-10 or eta < -1e-10:
        raise ValueError("utility outside [0,1]: invalid numeric computation")
    out = {"status": "G0_DENSE_REFERENCE_ONLY", "eta": float(min(eta,1.)),
           "delta": float(max(0.,1.-eta)), "oracle_alpha": float(alpha),
           "relative_full_residual": float(np.linalg.norm(Q @ full + g)/np.linalg.norm(g)),
           "relative_block_residual": float(np.linalg.norm(np.concatenate(
               [Q[s,s] @ block[s] + g[s] for s in slices]))/np.linalg.norm(g))}
    if train_jacobian is not None:
        J = np.asarray(train_jacobian, dtype=np.float64)
        if J.ndim != 2 or J.shape[1] != n or not np.isfinite(J).all():
            raise ValueError("invalid train Jacobian")
        a,b = J @ full, J @ block
        denom = float(b @ b)
        if np.linalg.norm(a) <= 1e-12 or denom <= 1e-24:
            out["E_task"] = None
        else:
            scale = max(0., float(a @ b)/denom)
            out["E_task"] = float(np.linalg.norm(a - scale*b)/np.linalg.norm(a))
    return out


def sketch_inverse_blocks(solve: Callable[[np.ndarray], np.ndarray],
                          sizes: Sequence[int], probes_per_source: int,
                          seed: int = 0) -> dict:
    """Estimate ||R_ij||_F^2 by Rademacher probes on input block j.

    E_z ||(R z)_i||^2 = ||R_ij||_F^2 for an exact linear solve.
    Approximate solves add solver bias; estimates require error controls.
    Energy ratios can be biased even when each energy estimate is unbiased.
    """
    slices = groups(sizes)
    if probes_per_source < 2:
        raise ValueError("at least two probes required to estimate uncertainty")
    P = sum(sizes)
    L = len(slices)
    rng = np.random.default_rng(seed)
    raw = np.empty((L, probes_per_source, L), dtype=np.float64)
    for j, sj in enumerate(slices):
        for k in range(probes_per_source):
            z = np.zeros(P)
            z[sj] = rng.choice([-1., 1.], size=sj.stop-sj.start)
            x = np.asarray(solve(z), dtype=np.float64)
            if x.shape != (P,) or not np.isfinite(x).all():
                raise ValueError("invalid inverse solve result")
            raw[j,k,:] = [float(x[si] @ x[si]) for si in slices]
    energy = raw.mean(axis=1).T
    stderr = raw.std(axis=1, ddof=1).T / np.sqrt(probes_per_source)
    total = float(energy.sum())
    if total <= 0:
        raise ValueError("zero energy in inverse sketch")
    dist_rms = []
    for k in range(L):
        pairs = [(i,j) for i in range(L) for j in range(L) if abs(i-j)==k]
        count_entries = sum(sizes[i]*sizes[j] for i,j in pairs)
        dist_rms.append(np.sqrt(float(sum(energy[i,j] for i,j in pairs))/count_entries))
    return {"energy_by_target_source": energy.tolist(),
            "energy_standard_error": stderr.tolist(),
            "normalized_element_rms_by_distance": (np.array(dist_rms)/dist_rms[0]).tolist(),
            "offdiag_mass_estimate": float((total - np.trace(energy))/total),
            "probes_per_source": int(probes_per_source),
            "probe_seed": int(seed),
            "status": "G0_NUMERICAL_SKETCH_NOT_SCIENTIFIC_REPLICATION"}
