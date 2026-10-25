# Next stage: decision-led research plan

## P0 — Repair the decisive measurement contradiction (must precede new theory)

**Goal:** Same L=12, d=10, B=32, λ=1e-3 run; release original R blocks and exact definitions.
**Outputs:** block norm matrix, S_RMS(k), S_mass(k), all 12 bins, offdiag mass, cross-consistency test, Hessian spectrum/condition and solve residual.
**Acceptance:** energy identity and L-dependent bounds match to numerical tolerance. If no match, original reported 0.09–0.12 and 39% pair is superseded with corrected values.

## P1 — Phase VII / GGN-geometry arbitration

**Input:** GGN=JᵀJ/M on a frozen checkpoint, scaled consistently with exact H; λ>0.
**Models:** Chain, Global, Mixed, fitted on training seeds; nuisance parameters matched across each null.
**Controls:** label/block order permutations, matched spectral orthogonal null, shuffled layer geometry; seed-split holdout.
**Metrics:** SPD eigenvalue check, rank(J), λ-spectrum, BDS fit with confidence intervals, null p-values, cross-seed held-out MSE.
**Pass:** mixed model significantly beats both chain/global and null on unseen seeds across λ values, with conditions reported.
**Fail/pivot:** indistinguishable from null; seek other structure (block-band+low-rank).

## P2 — Nullspace mechanism disambiguation

1. Exact J rank (strong 8×8 function rank bound ≤64), nullspace projection P0 and dimension.
2. Decompose for GGN: R=(G+λI)⁻¹=λ⁻¹P0+∑_{μ>0}(μ+λ)⁻¹v_iv_iᵀ.
3. Compare off-diagonal baseline of P0 with retained non-null modes; assess cross-term cancellations.
4. Gauge-specific analytic tangent vectors and overlap with nullspace; compare expected dimensionality and projection to P0.
5. Report explained *retained residual* versus cut rank with random-subspace and equal-spectral-weight controls.

**Pass:** a small, stable, independently validated subspace (specified r/P) explains >90% of tail mass on heldout samples without metric tautology. Otherwise describe a high-rank projector mechanism.

## P3 — Predictive scale law

Sweep L,d,n,λ and conditioning; normalize function scale and damping by spectral norms. Fit out-of-sample candidate laws (1/L, 1/√L, constant, rank-fraction) against a rank-one toy baseline. Report uncertainty, extrapolation and failure domains. A normalized finite-L plateau need not remain nonzero as L→∞.

## P4 — Nonlinear and dynamics testing

ReLU/LeakyReLU with frozen gates versus changing gates; exact H vs GGN; monitor residual second derivative. Track checkpoints, rank, condition, mask density, block spectrum. Do not assume fixed gates imply H=GGN. Test whether apparent change is continuous crossover before calling a phase transition.

## P5 — Architecture modulation

Plain/ResNet + optional normalization at matched parameter count; attention later. Separate intrinsic architecture effect from width, scale, gauge and batch effects. Compare layer-block offdiag mass and distance spectrum against controls.

## P6 — Optimizer test

Implement reference block-band plus low-rank preconditioning, benchmark linear solve residual, direction cosine, training speed/accuracy and memory. Only after numerical benefit, pursue GPU fused operators.

## Release gates

All public results require:
- source code and run config hash;
- exact checkpoint, seed and batch;
- exact matrix object and dtype;
- residual plus conditioning estimate;
- table/plot recomputation from saved raw block norms/eigenpairs;
- provenance: original file vs newly authored reimplementation;
- independent review with explicit pass/fail reason.
