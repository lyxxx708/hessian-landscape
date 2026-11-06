"""Complete loss-vs-alpha replay on fixed pools, with sign resolution from two independent rounding paths.

For pool P (n examples, N = n*d_out) and direction d (per-layer E_l):
  dL(a)   = L_P(theta + a d) - L_P(theta)          (measured; FP64)
  s_P     = -g_P^T d                               (slope of the GAIN at a=0; >0 means descent on P)
  c_P     = d^T H_P d   (full Hessian along d),    c_P^GGN = ||J_P d||^2 / N
  pred1(a)= a s_P,   pred2(a) = a s_P - a^2 c_P / 2  (predicted gain)
Sign resolution: each dL is computed by (i) residual form sum((2R+delta)delta)/2N with layer-sequential forward,
(ii) the same with a product-first forward (different rounding), (iii) naive L(a)-L(0). bound = 2*max pairwise
discrepancy + 16 eps sum|terms|. |dL| <= bound -> NUMERICALLY_INDETERMINATE (never forced to a sign).
"""
from __future__ import annotations
import math
import torch
from torch.func import jvp

ALPHA_GRID = [0.0, 1e-5, 1e-4, 1e-3, 3e-3, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0]
OLD_GRID = [0.0, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0]
EPS = torch.finfo(torch.float64).eps
SAFETY = 2.0


def _fwd_seq(W, X):
    h = X
    for w in W:
        h = h @ w.T
    return h


def _fwd_prod(W, X):
    M = W[0]
    for w in W[1:]:
        M = w @ M
    return X @ M.T


def sign_of(value, bound):
    if value > bound:
        return 1
    if value < -bound:
        return -1
    return 0


class PoolEval:
    """All quantities for one direction on one pool, with optional contiguous groups."""

    def __init__(self, W, X, Y, groups=None):
        self.W, self.X, self.Y = W, X, Y
        self.groups = groups or []
        self.dout = Y.shape[1]
        self.F0s = _fwd_seq(W, X)
        self.F0p = _fwd_prod(W, X)
        self.R0 = self.F0s - Y
        self.R0p = self.F0p - Y
        self.sample_sq = self.R0.square().sum(1)
        self.L0 = float(self.sample_sq.sum() / (2 * self.R0.numel()))

    def _ranges(self):
        return [(0, len(self.X))] + list(self.groups)

    def base_losses(self):
        return [float(self.sample_sq[a:b].sum() / (2 * (b - a) * self.dout)) for a, b in self._ranges()]

    def curve(self, E, alphas):
        """Returns per range (whole pool first, then groups): dL, bound for each alpha."""
        out = []
        ranges = self._ranges()
        for a in alphas:
            Wa = [w + a * e for w, e in zip(self.W, E)]
            Fs = _fwd_seq(Wa, self.X)
            Fp = _fwd_prod(Wa, self.X)
            ds = Fs - self.F0s
            dp = Fp - self.F0p
            t1 = ((2 * self.R0 + ds) * ds).sum(1)
            t2 = ((2 * self.R0p + dp) * dp).sum(1)
            sq = (Fs - self.Y).square().sum(1)
            mag = ((2 * self.R0 + ds).abs() * ds.abs()).sum(1)
            row = []
            for lo, hi in ranges:
                den = 2 * (hi - lo) * self.dout
                v1 = float(t1[lo:hi].sum()) / den
                v2 = float(t2[lo:hi].sum()) / den
                v3 = (float(sq[lo:hi].sum()) - float(self.sample_sq[lo:hi].sum())) / den
                vf = math.fsum(t1[lo:hi].tolist()) / den
                disc = max(abs(v1 - v2), abs(v1 - v3), abs(v1 - vf))
                bound = SAFETY * disc + 16 * EPS * float(mag[lo:hi].sum()) / den
                if a == 0.0:
                    v1, bound, v3 = 0.0, 0.0, 0.0
                row.append((v1, bound, v3))
            out.append(row)
        return out  # [alpha][range] -> (dL, bound)

    def slope_curv(self, E, g_pool=None):
        """Gain slope s=-g^T d and directional curvatures, for the whole pool and each group."""
        dF = jvp(lambda a: _fwd_seq([w + a * e for w, e in zip(self.W, E)], self.X),
                 (torch.zeros((), dtype=self.X.dtype),), (torch.ones((), dtype=self.X.dtype),))[1]
        ddF = jvp(lambda b: jvp(lambda a: _fwd_seq([w + a * e for w, e in zip(self.W, E)], self.X),
                                (b,), (torch.ones((), dtype=self.X.dtype),))[1],
                  (torch.zeros((), dtype=self.X.dtype),), (torch.ones((), dtype=self.X.dtype),))[1]
        rows = []
        for i, (lo, hi) in enumerate(self._ranges()):
            N = (hi - lo) * self.dout
            R = self.R0[lo:hi]
            s_jvp = -float((R * dF[lo:hi]).sum()) / N
            s_alt = None
            if i == 0 and g_pool is not None:
                s_alt = -float(sum((gl * el).sum() for gl, el in zip(g_pool, E)))
            mag = float((R * dF[lo:hi]).abs().sum()) / N
            disc = abs(s_jvp - s_alt) if s_alt is not None else 0.0
            ggn = float(dF[lo:hi].square().sum()) / N
            cH = ggn + float((R * ddF[lo:hi]).sum()) / N
            rows.append({'slope': s_jvp, 'slope_gradient_formula': s_alt,
                         'slope_bound': SAFETY * disc + 16 * EPS * mag, 'curv_H': cH, 'curv_GGN': ggn})
        return rows


def pool_gradient(W, X, Y):
    """Closed-form DLN gradient of the pool loss (per-layer matrices)."""
    hs = [X]
    for w in W[:-1]:
        hs.append(hs[-1] @ w.T)
    F = hs[-1] @ W[-1].T
    R = F - Y
    N = R.numel()
    P = torch.eye(W[-1].shape[0], dtype=X.dtype)
    out = [None] * len(W)
    for l in range(len(W) - 1, -1, -1):
        out[l] = P.T @ R.T @ hs[l] / N
        P = P @ W[l]
    return out


def evaluate_direction(W, E, pools, groups, alphas=ALPHA_GRID):
    """pools: name -> (X, Y); groups: name -> list of (lo, hi) on that pool. Returns JSON-ready dict."""
    res = {}
    for name, (X, Y) in pools.items():
        gr = groups.get(name, [])
        pe = PoolEval(W, X, Y, gr)
        cur = pe.curve(E, alphas)
        sc = pe.slope_curv(E, pool_gradient(W, X, Y))
        base = pe.base_losses()
        entry = {'n': len(X), 'L0': base[0], 'groups_L0': base[1:],
                 'dL': [c[0][0] for c in cur], 'bound': [c[0][1] for c in cur],
                 'loss_naive': [base[0] + c[0][2] for c in cur],
                 'sign_gain': [sign_of(-c[0][0], c[0][1]) for c in cur],
                 **{k: sc[0][k] for k in sc[0]}}
        if gr:
            entry['groups'] = [{'dL': [c[j + 1][0] for c in cur], 'bound': [c[j + 1][1] for c in cur],
                                'slope': sc[j + 1]['slope'], 'slope_bound': sc[j + 1]['slope_bound'],
                                'curv_H': sc[j + 1]['curv_H']} for j in range(len(gr))]
        res[name] = entry
    return res


def select_alpha(loss_by_alpha, alphas, allowed):
    """v2 rule: minimise the measured loss over the allowed grid; ties -> smaller alpha."""
    cand = [(loss_by_alpha[alphas.index(a)], a) for a in allowed]
    return min(cand)[1]
