# Technical mathematical notes — what is known versus hypothesized

## Matrix objects

With squared loss L(θ)=1/(2M)||r(θ)||²:
- J=∂r/∂θ.
- H=∇²L=(1/M)JᵀJ+(1/M)∑_a r_a∇²r_a.
- GGN=(1/M)JᵀJ is PSD.
- For λ>0, GGN+λI is SPD; exact H+λI may remain indefinite.
- R_H(λ)=(H+λI)⁻¹ exists iff −λ∉spec(H). The inverse, if indefinite, is not an SPD Gaussian covariance/precision object.

**The ReLU subtlety:** A fixed ReLU gate pattern is locally linear in input, NOT in *all layer weight parameters jointly*. Cross-layer products still have second derivatives. Thus exact Hessian≠GGN generally even when every ReLU gate is locally fixed; equality holds for zero residual or other special conditions.

## Layer-block metrics

Given R partitioned into layer parameter blocks B_ij and layer distance k=|i−j|:

n_k=#{(i,j):|i−j|=k}, E_k=∑_{|i−j|=k}||B_ij||_F².
S_RMS(k)=√(E_k/n_k).
S_mass(k)=E_k/∑_j E_j.
Offdiag=1−S_mass(0).
Normalized S_RMS(k)/S_RMS(0) is meaningful for uniformly sized blocks. Nonuniform block sizes require explicit element-count normalization for cross-architecture comparison.

Block-pair geometric normalization:
C_ij=||B_ij||_F/√(||B_ii||_F||B_jj||_F) where denominators are nonzero. For indefinite R, C_ij may exceed 1. For a positive-semidefinite block matrix R with nonzero PSD diagonal blocks, this Frobenius-normalized pairwise quantity is at most 1 (the PSD block factorization implies ||B_ij||_F²≤||B_ii||_F||B_jj||_F). For indefinite R it need not be bounded by 1.

## Consistency identity

For L equal-size blocks and bound S_RMS(k)/S_RMS(0)≤c for k≥1:
E_off≤L(L−1)c² S_RMS(0)²,
E_diag=L S_RMS(0)², hence
Offdiag ≤ (L−1)c²/[1+(L−1)c²].

For L=12,c=0.12, Offdiag≤0.1367. This strongly conflicts with a simultaneously reported offdiag≈0.39 under the same matrix/metric. Must reconcile source runs before citing these figures together.

## Rank caveat for DLN

For input/output dimension d_in,d_out, fθ(x)=Mθ x, where Mθ is a d_out×d_in effective linear matrix. Therefore rank of Jacobian of all observed outputs with respect to θ ≤ d_in d_out, regardless of number of observations. For 8×8 DLN: rank(J)≤64, so nullity(J)≥1056−64=992 for P=1056.

At zero residual exact Hessian=GGN and shares this rank upper bound. Away from zero residual the functional Hessian term can give full or much higher rank; one cannot infer rank(H)≤rank(J).

## Rank-one Sherman–Morrison example

For H=11ᵀ with dimension L, m=λ+β>0, R=(H+mI)⁻¹:
- R_ij=−1/[m(m+L)] for i≠j;
- R_ii=(m+L−1)/[m(m+L)];
- ratio |R_ij|/R_ii=1/(m+L−1).

Every pair has the same offdiagonal magnitude, but the normalized platform decays ~1/L. This example cannot establish finite asymptotic plateau height without scale definition.

## Matrix decay theory boundaries

Inverse of banded uniformly well-conditioned SPD matrices can exhibit off-band exponential decay, with bounds depending on bandwidth, spectrum, condition number and distance. Deep parameter Hessians are not assumed banded; their computation graph being a chain does **not** imply Hessian or inverse is block tridiagonal.

Graph moralization corresponds to Gaussian variable precision patterns when a **specified linear-Gaussian factorization** is available. Weight parameter Hessian patterns do not automatically equal activation-graph moralization patterns.

An SPD gate is appropriate when using Gaussian precision or SPD-only factorization, but its failure is not a global refutation of resolvent decay.

## Woodbury direction

If Q=B+UCUᵀ, B invertible, C invertible:
Q⁻¹=B⁻¹−B⁻¹U(C⁻¹+UᵀB⁻¹U)⁻¹UᵀB⁻¹.

Use B as a verified well-conditioned block/banded approximation; global low-rank residual must be measured, not assumed. Negative eigenvalues require suitable indefinite solver/regularization. Evaluate actual preconditioned residuals and end-task training, not cosine similarity alone.
