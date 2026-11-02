"""Independent REIMPLEMENTATION: exact Jacobian / GGN / Hessian for bias-free deep linear nets.
Loss L = 1/(2 c) ||W_L...W_1 X - Y||_F^2, c = N*d_out. Params flattened row-major per layer."""
import numpy as np

def prod(Ws, lo, hi, n_left):
    """W_hi ... W_lo (1-indexed, inclusive); identity of size n_left if empty."""
    M = np.eye(n_left)
    for k in range(lo, hi + 1):
        M = Ws[k - 1] @ M
    return M

def shapes(din, widths, dout):
    dims = [din] + list(widths) + [dout]
    return [(dims[i + 1], dims[i]) for i in range(len(dims) - 1)]

def unflat(theta, shp):
    out, i = [], 0
    for (a, b) in shp:
        out.append(theta[i:i + a * b].reshape(a, b)); i += a * b
    return out

def flat(Ws):
    return np.concatenate([W.ravel() for W in Ws])

def lr(Ws, l):
    """A_l = W_L..W_{l+1}, B_l = W_{l-1}..W_1 (l 1-indexed)."""
    L = len(Ws)
    A = prod(Ws, l + 1, L, Ws[l - 1].shape[0])
    B = prod(Ws, 1, l - 1, Ws[0].shape[1])
    return A, B

def loss_grad(theta, shp, X, Y):
    Ws = unflat(theta, shp); L = len(Ws)
    c = X.shape[1] * Y.shape[0]
    M = prod(Ws, 1, L, X.shape[0])
    E = M @ X - Y
    G = E @ X.T / c
    grads = []
    for l in range(1, L + 1):
        A, B = lr(Ws, l)
        grads.append(A.T @ G @ B.T)
    return 0.5 * np.sum(E * E) / c, flat(grads)

def jac_M(Ws):
    """Jacobian of vec(M) (row-major) wrt theta: d_out*d_in x P."""
    L = len(Ws); cols = []
    for l in range(1, L + 1):
        A, B = lr(Ws, l)
        # dM = A dW B ; vec_r(A dW B) = (A kron B^T) vec_r(dW)
        cols.append(np.kron(A, B.T))
    return np.hstack(cols)

def ggn(Ws, X, dout):
    c = X.shape[1] * dout
    JM = jac_M(Ws)
    # residual jac: vec_r(dM X) = (I kron X^T) vec_r(dM)
    S = X @ X.T  # din x din
    K = np.kron(np.eye(dout), S)  # metric on vec_r(dM)
    return JM.T @ K @ JM / c, JM

def hessian(Ws, X, Y):
    L = len(Ws); dout = Y.shape[0]
    c = X.shape[1] * dout
    H, JM = ggn(Ws, X, dout)
    M = prod(Ws, 1, L, X.shape[0])
    G = (M @ X - Y) @ X.T / c
    off = np.cumsum([0] + [W.size for W in Ws])
    for m in range(1, L + 1):
        for l in range(1, m):
            Am, _ = lr(Ws, m); _, Bl = lr(Ws, l)
            C = prod(Ws, l + 1, m - 1, Ws[l - 1].shape[0])  # W_{m-1}..W_{l+1}
            K = Bl @ G.T @ Am  # e x a
            # block[(a,b),(c,e)] = C[b,c] * K[e,a]
            blk = np.einsum('bc,ea->abce', C, K)
            am, bm = Ws[m - 1].shape; al, bl = Ws[l - 1].shape
            blk = blk.reshape(am * bm, al * bl)
            H[off[m - 1]:off[m], off[l - 1]:off[l]] += blk
            H[off[l - 1]:off[l], off[m - 1]:off[m]] += blk.T
    return H

def block_metrics(R, sizes):
    """Same definitions as scripts/reference_block_metrics.py plus pairwise C_ij and profile."""
    L = len(sizes); st = np.cumsum([0] + list(sizes))
    N = np.array([[np.linalg.norm(R[st[i]:st[i+1], st[j]:st[j+1]]) for j in range(L)] for i in range(L)])
    E = N ** 2
    Ek = np.array([sum(E[i, j] for i in range(L) for j in range(L) if abs(i - j) == k) for k in range(L)])
    nk = np.array([L if k == 0 else 2 * (L - k) for k in range(L)])
    rms = np.sqrt(Ek / nk)
    d = np.sqrt(np.diag(N))
    Cij = N / np.outer(d, d)
    return dict(norms=N, rms_ratio=rms / rms[0], mass=Ek / Ek.sum(), offdiag=1 - Ek[0] / Ek.sum(), C=Cij)

def gauge_basis(Ws):
    """Tangent vectors of the GL(h)^ (L-1) gauge orbit: dW_l = X_l W_l - W_l X_{l-1}."""
    L = len(Ws); shp = [W.shape for W in Ws]
    vecs = []
    for g in range(1, L):  # hidden layer g between W_g and W_{g+1}
        h = Ws[g - 1].shape[0]
        for a in range(h):
            for b in range(h):
                Xg = np.zeros((h, h)); Xg[a, b] = 1
                dW = [np.zeros(s) for s in shp]
                dW[g - 1] = Xg @ Ws[g - 1]
                dW[g] = -Ws[g] @ Xg
                vecs.append(flat(dW))
    return np.array(vecs).T

def proj(V, tol=1e-10):
    U, s, _ = np.linalg.svd(V, full_matrices=False)
    r = int(np.sum(s > tol * s[0]))
    U = U[:, :r]
    return U @ U.T, r

def orth_init(shp, scale, rng):
    Ws = []
    for (a, b) in shp:
        Q, _ = np.linalg.qr(rng.standard_normal((max(a, b), max(a, b))))
        Ws.append(scale * Q[:a, :b])
    return Ws
