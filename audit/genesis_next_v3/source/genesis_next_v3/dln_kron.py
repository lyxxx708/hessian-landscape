"""Exact curvature algebra for a bias-free deep linear network with half-MSE mean loss.

Model: h_0 = X (B x d_in), h_{l+1} = h_l W_l^T, output F = h_L. Loss = ||F - Y||^2 / (2N), N = B * d_out.
For layer l let P_l = W_{L-1} ... W_{l+1} (d_out x out_l, identity for the last layer). Then
    dF[E_l]       = h_l E_l^T P_l^T
    grad_l        = P_l^T R^T h_l / N,            R = F - Y
    G_ll[E]       = S_l E T_l,  S_l = P_l^T P_l,  T_l = h_l^T h_l / N
which is EXACT only for this linear MSE model (not a K-FAC approximation). Nothing here calls the v2
FrozenOperator, so it is an independent implementation path that the tests compare against it.
"""
from __future__ import annotations
import math
import torch


class DLN:
    def __init__(self, weights, X, Y):
        self.W = [w.detach() for w in weights]
        self.X, self.Y = X.detach(), Y.detach()
        self.L = len(self.W)
        self.shapes = [tuple(w.shape) for w in self.W]
        self.sizes = [w.numel() for w in self.W]
        self.offsets = [0]
        for s in self.sizes:
            self.offsets.append(self.offsets[-1] + s)
        self.n = self.offsets[-1]
        self.N = X.shape[0] * self.W[-1].shape[0]
        self.cache = None
        self.factors = None

    # ---------- layout ----------
    def split(self, v):
        return [v[a:b].view(s) for a, b, s in zip(self.offsets[:-1], self.offsets[1:], self.shapes)]

    def theta(self):
        return torch.cat([w.reshape(-1) for w in self.W])

    # ---------- forward / loss ----------
    @staticmethod
    def forward_weights(W, X):
        h = X
        for w in W:
            h = h @ w.T
        return h

    def loss_at(self, v=None, X=None, Y=None):
        W = self.W if v is None else self.split(v)
        X = self.X if X is None else X
        Y = self.Y if Y is None else Y
        F = self.forward_weights(W, X)
        return float((F - Y).square().sum() / (2 * F.numel()))

    # ---------- caches (method-exclusive cost, charged to whoever uses them) ----------
    def build_cache(self):
        hs = [self.X]
        for w in self.W[:-1]:
            hs.append(hs[-1] @ w.T)
        F = hs[-1] @ self.W[-1].T
        dout = self.W[-1].shape[0]
        Ps = [None] * self.L
        Ps[-1] = torch.eye(dout, dtype=self.X.dtype, device=self.X.device)
        for l in range(self.L - 2, -1, -1):
            Ps[l] = Ps[l + 1] @ self.W[l + 1]
        self.cache = {'h': hs, 'P': Ps, 'F': F}
        return self.cache

    def gradient(self):
        c = self.cache or self.build_cache()
        R = c['F'] - self.Y
        return torch.cat([(c['P'][l].T @ R.T @ c['h'][l] / self.N).reshape(-1) for l in range(self.L)])

    def ggn_vec(self, v):
        c = self.cache or self.build_cache()
        E = self.split(v)
        dF = sum(c['h'][l] @ E[l].T @ c['P'][l].T for l in range(self.L))
        return torch.cat([(c['P'][l].T @ dF.T @ c['h'][l] / self.N).reshape(-1) for l in range(self.L)])

    def output_jvp(self, v):
        c = self.cache or self.build_cache()
        E = self.split(v)
        return sum(c['h'][l] @ E[l].T @ c['P'][l].T for l in range(self.L))

    # ---------- exact block Kronecker solver ----------
    def build_factors(self):
        c = self.cache or self.build_cache()
        out = []
        for l in range(self.L):
            S = c['P'][l].T @ c['P'][l]
            T = c['h'][l].T @ c['h'][l] / self.N
            s, U = torch.linalg.eigh((S + S.T) / 2)
            t, V = torch.linalg.eigh((T + T.T) / 2)
            out.append({'S': S, 'T': T, 's': s, 'U': U, 't': t, 'V': V})
        self.factors = out
        return out

    def block_direct(self, g, lam):
        """-(G_ll + lam I)^{-1} g_l for every layer, via the two eigensystems."""
        f = self.factors or self.build_factors()
        parts = []
        for l, gl in enumerate(self.split(g)):
            U, V, s, t = f[l]['U'], f[l]['V'], f[l]['s'], f[l]['t']
            C = (U.T @ gl @ V) / (s[:, None] * t[None, :] + lam)
            parts.append((-(U @ C @ V.T)).reshape(-1))
        return torch.cat(parts)

    def block_local_matvec(self, l, E, lam):
        f = self.factors or self.build_factors()
        return f[l]['S'] @ E @ f[l]['T'] + lam * E

    def block_local_cg(self, g, lam, rtol=1e-12, max_iter=2000):
        """Control: same exact block system solved by CG with block-local Kronecker matvecs (no padded AD)."""
        f = self.factors
        if f is None:
            c = self.cache or self.build_cache()
            f = [{'S': c['P'][l].T @ c['P'][l], 'T': c['h'][l].T @ c['h'][l] / self.N} for l in range(self.L)]
        parts, iters = [], []
        for l, gl in enumerate(self.split(g)):
            S, T = f[l]['S'], f[l]['T']
            A = lambda E: S @ E @ T + lam * E
            x, k = cg_matrix(A, -gl, rtol=rtol, max_iter=max_iter)
            parts.append(x.reshape(-1))
            iters.append(k)
        return torch.cat(parts), iters


def cg_matrix(A, b, rtol, max_iter):
    x = torch.zeros_like(b)
    r = b.clone()
    p = r.clone()
    rr = float((r * r).sum())
    bn = math.sqrt(rr)
    k = 0
    while k < max_iter and math.sqrt(rr) > rtol * bn and bn > 0:
        Ap = A(p)
        curv = float((p * Ap).sum())
        if curv <= 0:
            break
        a = rr / curv
        x = x + a * p
        r = r - a * Ap
        rr2 = float((r * r).sum())
        p = r + (rr2 / rr) * p
        rr = rr2
        k += 1
    return x, k


def cg_lean(Q, b, k, rtol=0.0):
    """Unpreconditioned CG from x0=0 with exactly <=k matvecs and no extra true-residual matvec.
    Stops early only if the recurrence residual <= rtol*||b|| (rtol fixed ex ante; never an oracle)."""
    x = torch.zeros_like(b)
    r = b.clone()
    p = r.clone()
    rr = float(r @ r)
    bn = math.sqrt(rr)
    used = 0
    status = 'ITERATION_LIMIT'
    while used < k:
        if bn == 0 or math.sqrt(rr) <= rtol * bn:
            status = 'RECURRENCE_TOLERANCE'
            break
        Ap = Q(p)
        used += 1
        curv = float(p @ Ap)
        if not math.isfinite(curv) or curv <= 0:
            status = 'NONPOSITIVE_CURVATURE'
            break
        a = rr / curv
        x = x + a * p
        r = r - a * Ap
        rr2 = float(r @ r)
        p = r + (rr2 / rr) * p
        rr = rr2
    return x, {'matvecs': used, 'status': status, 'recurrence_relative_residual': math.sqrt(rr) / bn if bn else 0.0}


def quad_gain(g, d, Qd):
    return float(-(g @ d) - 0.5 * (d @ Qd))


def best_ray(g, d, Qd):
    dq = float(d @ Qd)
    dg = float(g @ d)
    a = -dg / dq if dq > 0 and dg < 0 else 0.0
    return a, (dg * dg / (2 * dq) if a > 0 else 0.0)
