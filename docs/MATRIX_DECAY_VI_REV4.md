# Matrix-decay theory arbitration — Phase VI Rev3/Rev4

**Historical stage date:** 2025-12-17. **Stage verdict in team report:** Audit Passed / Arbitration FAILED (APPROVED FAIL). **Next planned:** Phase VII / GGN.

## Background: Rev3 negative control defeated positive chain

At λ=0.1, BDS fit distance:
- candidate tridiagonal Kronecker chain: 0.5408;
- block-permuted negative control: 0.4960;
- negative/positive distance ratio≈0.917 (<1).
A candidate model being worse than a negative control is evidence **against this fitted geometry**, not proof that DLN lacks all structured coupling.

## Rev4 corrections

1. **Correct inverse mapping**: fit the curvature-side small matrix A through the BDS of A⁻¹; don't set A offdiagonal directly from inverse plateau value.
2. **Dimensions**: uniform parameter block dimension d²=100 in L=12,d=10 setup, hence Kronecker factor B should be 100×100 if that ansatz is used.
3. **Analytical factor cancellation**: if R=A⁻¹⊗B⁻¹ with identical factor across all block pairs, the Frobenius normalized block-distance ratios cancel ||B⁻¹||_F; one can fit A (12×12).
4. **Fair controls**: test permutation on original curvature/graph when applicable and a spectrum-preserving orthogonal null, with care to apply the same nuisance parameter fitting to all null datasets.
5. **Candidate geometric models**:
   - Chain A=I−αT;
   - Global A=I+ρ(J−I);
   - Mixed A=I−αT+ρ(J−I).
   Optimize fit with L-BFGS-B, compare plateau, drop, flatness, pair-count weighted distance-vector MSE.

## Exact-Hessian SPD gate result

Reported ground truth initialization: x=I_d, target I_d; L=12, d=10, full exact H with λ=0.1. Q=H+0.1I reportedly had min eigenvalues around −9.09…−9.54 on tested seeds. Consequently Q is indefinite. This correctly **fails a chosen SPD precision/covariance or Cholesky-specific modeling gate**.

This does **not** establish that R=Q⁻¹ cannot exist or that every matrix inverse-decay theorem fails: invertibility depends on distance of −λ from spec(H); exponential decay bounds also require assumptions on underlying banded matrix/graph and resolvent spectral gap. An indefinite but nonsingular operator may admit bounds of a different class.

The pipeline produced no accepted ground-truth BDS and null distribution after the gate, with NaN Z scores. Those are **absence of eligible test data**, not statistical support for any geometric model.

## Useful analytical result and limits

For normalized block norms, Kronecker cancellation is exact **under exact separable ansatz and identical B factor**. It does not by itself validate separability of real Hessian/GGN blocks. When per-layer parameter block sizes differ, one common Kronecker factor is not possible without further modeling.

## Phase VII experimental contract

Use Q_G=GGN+λI, λ>0, proving SPD algebraically. First verify actual block structure/distance on GGN, then fit candidate Chain/Global/Mixed geometry. Use seeded train/test split across matrices/seeds for model selection, matched null refitting, confidence intervals, out-of-sample scores, and rank/condition reporting. Always retain exact H as a **separate** descriptive indefinite resolvent control.
