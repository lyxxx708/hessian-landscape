"""Analytic population-risk oracle for the v2 synthetic DLN task (GENESIS NEXT v3 addendum A1).

v2 generates x = R diag(sqrt(eig)) z, z ~ N(0, I), and y = A x with no noise (registry._synthetic). For a bias-free DLN
with product M = W_L ... W_1 and the half-MSE mean loss, the population risk is therefore exact:
    R(M) = E||M x - A x||^2 / (2 d_out) = ||(M - A) R diag(sqrt(eig))||_F^2 / (2 d_out).
Along a ray W_l + a E_l the product M(a) = sum_k a^k C_k is a degree-L matrix polynomial, so R(a) is a degree-2L
scalar polynomial. Equivalently R = d_in * L_DLN(W; X_eff, Y_eff) with the d_in pseudo-samples X_eff = (R D^1/2)^T,
Y_eff = X_eff A^T, which gives an independent second evaluation path through the v3 DLN class.

The same polynomial machinery gives the exact continuous minimiser of any finite-pool empirical loss along the ray.
"""
from __future__ import annotations
import math
import numpy as np
import torch
from scipy.optimize import minimize_scalar

EPS = float(np.finfo(np.float64).eps)
ALPHA_HI = 30.0          # search interval [0, ALPHA_HI]; v2 grid maximum is 3
SCAN_POINTS = 4001       # log-spaced scan of the polynomial before direct-evaluation refinement
CURVE_ALPHAS = [0.0] + np.logspace(-6, math.log10(ALPHA_HI), 241).tolist()   # stored full curves


def product(W):
    M = W[0]
    for w in W[1:]:
        M = w @ M
    return M


def matrix_poly(W, E):
    """Coefficients C_0..C_L with prod_l (W_l + a E_l) = sum_k a^k C_k (later layers multiply on the left)."""
    C = [W[0].clone(), E[0].clone()]
    for w, e in zip(W[1:], E[1:]):
        new = [torch.zeros(w.shape[0], C[0].shape[1], dtype=w.dtype) for _ in range(len(C) + 1)]
        for k, c in enumerate(C):
            new[k] += w @ c
            new[k + 1] += e @ c
        C = new
    return C


class Population:
    """Exact population risk of the v2 synthetic DLN task for one training seed."""

    def __init__(self, eig, rotation, teacher):
        self.A = teacher
        self.B = rotation * eig.sqrt()[None, :]        # R diag(sqrt eig): Sigma = B B^T
        self.dout, self.din = teacher.shape
        self.X_eff = self.B.T.contiguous()             # d_in pseudo-samples
        self.Y_eff = self.X_eff @ teacher.T

    def risk(self, W):
        D = (product(W) - self.A) @ self.B
        return float(D.square().sum() / (2 * self.dout))

    def risk_via_dln(self, W):
        F = self.X_eff
        for w in W:
            F = F @ w.T
        return float((F - self.Y_eff).square().sum() / (2 * self.dout))

    def poly(self, W, E):
        """Ascending coefficients r_0..r_2L of R(a)."""
        C = matrix_poly(W, E)
        D = [(c - (self.A if k == 0 else 0)) @ self.B for k, c in enumerate(C)]
        return _gram_poly(D, 2 * self.dout)

    def gradient(self, W):
        """Closed-form population gradient (per layer), for the analytic slope cross-check."""
        hs = [self.X_eff]
        for w in W[:-1]:
            hs.append(hs[-1] @ w.T)
        Rr = hs[-1] @ W[-1].T - self.Y_eff
        P = torch.eye(self.dout, dtype=self.A.dtype)
        out = [None] * len(W)
        for l in range(len(W) - 1, -1, -1):
            out[l] = P.T @ Rr.T @ hs[l] / self.dout
            P = P @ W[l]
        return out


class Pool:
    """Finite-pool empirical loss L = ||X M^T - Y||^2 / (2 n d_out), as an exact polynomial along a ray."""

    def __init__(self, X, Y):
        self.X, self.Y = X, Y
        self.N = Y.numel()

    def risk(self, W):
        return float((self.X @ product(W).T - self.Y).square().sum() / (2 * self.N))

    def poly(self, W, E):
        C = matrix_poly(W, E)
        D = [self.X @ c.T - (self.Y if k == 0 else 0) for k, c in enumerate(C)]
        return _gram_poly(D, 2 * self.N)

    def per_sample(self, W):
        return (self.X @ product(W).T - self.Y).square().sum(1) / (2 * self.Y.shape[1])


def _gram_poly(D, den):
    K = len(D)
    G = np.array([[float((D[j] * D[k]).sum()) for k in range(K)] for j in range(K)])
    r = np.zeros(2 * K - 1)
    for j in range(K):
        for k in range(K):
            r[j + k] += G[j, k]
    return r / den


def ray(W, E, a):
    return [w + a * e for w, e in zip(W, E)]


def minimize_on_ray(obj, W, E, hi=ALPHA_HI):
    """Exact continuous minimiser of obj.risk(W + a E) over a in [0, hi].

    Primary: real roots of the exact derivative polynomial in (0, hi], Newton-polished, local minima ranked by
    direct evaluation (a minimum is located far more precisely by R'(a)=0 than by comparing flat values of R).
    Cross-check: log scan of the polynomial + bounded Brent on direct evaluation. Returns a JSON-ready record."""
    r = obj.poly(W, E)
    p = np.polynomial.Polynomial(r)
    dp, d2p = p.deriv(), p.deriv(2)
    f = lambda a: obj.risk(ray(W, E, a))
    R0 = f(0.0)
    roots = []
    for z in dp.roots():
        if abs(z.imag) > 1e-6 * max(1.0, abs(z)) or not (0 < z.real <= hi * 1.01):
            continue
        x = float(z.real)
        for _ in range(8):
            h = d2p(x)
            if h == 0:
                break
            x = x - dp(x) / h
        if 0 < x <= hi:
            roots.append(x)
    local_min = [z for z in roots if d2p(z) > 0]
    cands = [(R0, 0.0)] + [(f(z), z) for z in local_min] + [(f(hi), hi)]
    R_opt, a_opt = min(cands, key=lambda t: (t[0], t[1]))
    grid = np.concatenate([[0.0], np.logspace(-10, math.log10(hi), SCAN_POINTS)])
    i = int(np.argmin(p(grid)))
    if i == 0:
        best_root = 0.0
    else:
        lo, up = grid[i - 1], grid[min(i + 1, len(grid) - 1)]
        res = minimize_scalar(f, bounds=(lo, up), method='bounded', options={'xatol': 1e-14 * max(up, 1e-300), 'maxiter': 500})
        best_root = float(res.x)
    # direct vs polynomial evaluation (precision receipt)
    chk = [0.0, 1e-3, 0.1, 1.0, 3.0, a_opt]
    poly_err = max(abs(p(a) - f(a)) for a in chk)
    scale = max(abs(f(a)) for a in chk)
    sign_changes = int(np.sum(np.diff(np.sign(dp(grid[1:]))) != 0))
    return {'alpha_opt': a_opt, 'R0': R0, 'R_opt': R_opt, 'max_gain': R0 - R_opt,
            'alpha_opt_brent_crosscheck': best_root,
            'alpha_brent_rel_disagreement': abs(best_root - a_opt) / max(a_opt, 1e-300) if a_opt > 0 else abs(best_root),
            'R_brent_minus_R_opt': f(best_root) - R_opt,
            'n_local_minima': len(local_min), 'derivative_sign_changes': sign_changes,
            'at_upper_boundary': bool(a_opt >= hi * (1 - 1e-9)),
            'poly_vs_direct_max_abs': poly_err, 'poly_vs_direct_rel': poly_err / max(scale, 1e-300),
            'slope_at_0': float(-r[1]) if len(r) > 1 else 0.0, 'curvature_at_0': float(2 * r[2]) if len(r) > 2 else 0.0,
            'coefficients': r.tolist()}


def gain_bound(R0, Ra):
    """Rounding bound for a population gain R0 - R(a) from exact closed-form evaluation (generous)."""
    return 64 * EPS * (abs(R0) + abs(Ra))


def mc_agreement(pop, pool, W, E, alphas):
    """z-scores of the E8192 Monte-Carlo loss and gain against the analytic population values."""
    l0 = pool.per_sample(W)
    R0 = pop.risk(W)
    out = []
    n = len(l0)
    for a in alphas:
        Wa = ray(W, E, a)
        la = pool.per_sample(Wa)
        Ra = pop.risk(Wa)
        se_L = float(la.std(unbiased=True) / math.sqrt(n))
        d = la - l0
        se_d = float(d.std(unbiased=True) / math.sqrt(n)) if a > 0 else 0.0
        out.append({'alpha': a, 'R': Ra, 'L_mc': float(la.mean()), 'z_loss': (float(la.mean()) - Ra) / se_L,
                    'dR': Ra - R0, 'dL_mc': float(d.mean()),
                    'z_gain': (float(d.mean()) - (Ra - R0)) / se_d if se_d > 0 else 0.0})
    return out
