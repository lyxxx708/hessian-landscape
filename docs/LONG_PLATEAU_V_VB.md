# Long-Range Plateau Paradox — Phase V/V-B Rev3.4

**Historical experiment date:** 2025-12-17. **Original report status:** Success (Data & Narrative Aligned). **Current evidence grade:** DOCUMENTARY_ONLY.

## Main hypotheses

- H1: near-null modes amplified by (H+λI)⁻¹ contribute to a long-range, non-decaying layer-distance floor.
- H2: regularization and parameter constraints can change the near-zero spectrum and reported coupling.
- H3: a block-local operator plus a global low-rank correction provides a useful approximate preconditioner.

## Experimental configuration reported

- Bias-free DLN, input=8, output=8, hidden width=12; depth 8 or 12.
- Depth 8 parameter count P = (12×8) + 6(12×12) + (8×12) = 1056.
- 50 observations with 8 outputs, 400 residual coordinates; for a deep **linear** network fθ(x)=Mx, rank(J) is at most 64. Consequently nullity(J)≥992, stronger than only P−400=656.
- Orthogonal initialization ×0.95, float64, iso/aniso data, standard MSE, weight decay α=0.001, hard Frobenius layer norm projection; SGD 2000 epochs, lr=.01.
- λ∈{1e-2,1e-4,1e-6,1e-8}. V-B fast protocol: depth 8, iso, standard/weight_decay, λ={1e-4,1e-8}.

## Exact and GGN audit

With loss 0.5/(N D_out) ∑r², use r_scaled=r/√(N D_out), GGN=J_scaledᵀJ_scaled, and exact H = GGN + ∑ r_scaled,a ∇²r_scaled,a. Exact weight decay α||θ||² adds 2αI.

Reported standard, λ=1e-8 case:
- final MSE≈5.30e-7;
- grad_norm≈5.20e-4;
- min eig(H)≈−8.97e-4;
- relative ||H−GGN||_F/||H||_F≈1.53e-4;
- low-rank capture of off-block H residual at rank L−1: norm ratio 0.665 (energy fraction 0.442 when using leading SVD singular values).

**No raw matrices or scripts were supplied; these remain reported values.**

## Rank-one scalar-chain exact baseline

At balanced unit weights and zero residual: H=ggᵀ, g=(1,…,1), ||g||²=L.
With m=λ+β>0:

R=(mI+ggᵀ)⁻¹ = m⁻¹I − [m(m+L)]⁻¹ggᵀ.

R_ii=(m+L−1)/[m(m+L)], R_ij=−1/[m(m+L)], i≠j.
Thus |R_ij|/R_ii=1/(m+L−1), and λ→0, β=0 gives 1/(L−1).

This is an **existence example**, not proof of generic non-decay or a macroscopic nonzero thermodynamic limit: normalized plateau tends to zero as L increases.

## Eigen-surgery

Reported threshold τ∈logspace(1e-12,1e-2,40), selecting |μ_i|<τ; eliminate selected spectral contributions from R and observe changes in off-diagonal block signal.

Historical metric: E_cut=||Mask_off(R_cut)||_F / ||Mask_off(R)||_F, reported tending toward 1 with many cut modes.

**Critical:** E_cut is a *norm-of-contribution ratio*, not a fraction of positive energy explained. Its numerator may exceed the original norm due to cancellation; reaching 1 by removing nearly all eigenmodes is tautological. Scientifically useful metrics must report the number and proportion of cut modes, the true retained residual ||Mask_off(R−R_cut)||/||Mask_off(R)|| and offdiag spectral cross terms, with controls matched to rank and eigenvalue weights.

## Gauge tests

Historic code reportedly enforced difference <1e-10 under "gauge scramble." Clarify what was compared: the network function/loss is invariant under appropriate invertible layer transformations; coordinate Hessian entries and their Frobenius block norms are **not generally gauge-invariant** under non-orthogonal reparameterizations. Compare tensor-transform predictions or invariant outputs, not uncorrected Hessian arrays.

## Low-rank correction

H_res=H−blockdiag(H); top-(L−1) SVD fraction ||R_r||_F/||H_res||_F≈0.665, square≈0.442. This is modest partial compressibility, **not** proof that an optimizer has better convergence. Proposed comparison: blockdiag, banded, banded+rank-r (with invertibility/SPD checks).

## Reproducibility needed

- Original training loss normalization, checkpoint weights, exact and GGN matrix hashes.
- rank(J;tol) and singular values; near-zero eigenspace overlap; λ near a negative-pole check.
- Multi-seed error bands; λ and N sweeps.
- Tail fits and H/GGN comparisons with a single unchanging block metric.
