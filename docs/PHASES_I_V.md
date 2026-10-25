# Phase I–V DLN numerical-forensics chronology

**This is a reconstructed historical report, not a source execution log.**

## Phase I — minimum reproducible experiment and solver audit

- DLN L=3, d=10, orthogonal initialization; H constructed with autograd, damping λ=1e-3.
- Float32 versus float64 and sweep λ=1e-2…1e-8.
- Compared inverse, LU solve, Cholesky, ordinary CG. Reported min eig(H) about −5.82e2 in one experiment; a negative eigenvalue invalidates **SPD-only** Cholesky/CG on H+1e-3I, but LU and symmetric-indefinite LDLᵀ/MINRES remain relevant.
- Hutchinson probe sweep 1–128 with multiple seeds; reported element-level S(1)/S(0) from around 1.0 (K=1) toward 0.75 (K=128); estimator and confidence interval not preserved.
- Earlier element-level diagonal-distance metrics were criticized: flatten order is not a scientifically privileged layer distance.
- Numeric reference: fp32 residual approx 8.7e-4, fp64 approx 1e-12 (not same as 12 orders of magnitude).

## Phase II — spectral and mode localization

- Small batch B=4 and λ scan 1…1e-8; reported min eig(H) about −149.03, maximum condition estimate 2.52e10, and fp32 divergence at λ roughly 1.84e-5.
- Reported IPR for low-eigenvalue vectors 0.0181 versus Gaussian 0.0099, but degeneracy-basis dependence and statistical null distribution remain open.
- Rank/mode surgery reported S(1)/S(0) 0.57 → 0.45 after removal of 50 modes; off-diagonal energy 0.9768 → 0.9640. This does **not** establish full-spectrum irreducible coupling without decomposition definitions and controlled spectral subspaces.

## Phase III — H versus GGN and batch

- Exact Hessian reported symmetric to around 1e-16 and indefinite at some checkpoints.
- GGN reported PSD/near singular; for squared loss GGN is JᵀJ with a loss-scaling factor.
- B=32 versus B=4 on L=3: element-distance metric around 0.57 versus 0.18. Small-batch phenomena depend on damping, rank and the matrix object; "inverse is pseudoinverse" is not correct when λ>0 and H+λI is invertible.

## Phase IV — depth and layer-block metric correction

- L∈{3,6,12}, d=10, B=32, λ=1e-3, fp64 CPU LU.
- Switch from element distance to layer-block Frobenius RMS and grouped energy mass.
- L=12 report: normalized block-distance curve around 0.09–0.12 for k=1…11, rather than decaying; earlier report stated off-diagonal mass 51.6%, tail 38.1%.
- Early "Solve Residual" entries had seconds mixed with residual values, later corrected.
- L=6 B=4 off-diagonal reported 2.7%, variable in later versions.

## Phase V — stability checks and final account from previous conversation

- Three seeds claimed for L=3,6,12 (no mean±std table available).
- Relative residual r=||AX−I||_F/||I||_F reported:
  - L3: 5.99e-14, time 0.009 s.
  - L6: 1.84e-12, time 0.013 s.
  - L12: 4.99e-12, time 0.040 s.
- L12 B=32, λ=1e-3 reported k=1≈0.09; k=2…11≈0.09–0.12; **also** offdiag mass≈39%, k≥4 mass≈8.8%.
- L6 B=32 reported H rank≈595/600, offdiag mass≈39%; L6 B=4 reported H rank≈360/600, offdiag mass≈0.012%, with declining λ associated with decreasing offdiag mass.

## Critical reconciliation

Reported plateau amplitudes 0.09–0.12 and total offdiag energy 39% are not obviously compatible if calculated from **the same L=12 matrix** using an unweighted homogeneous-block RMS normalized by diagonal-block RMS. If all off-diagonal RMS bins were ≤0.12×S_block(0), offdiag mass cannot exceed 13.67% at L=12. Different runs, normalizations, asymmetric sampling, or definitions may explain this; do NOT promote both numbers simultaneously as verified.

The rank claims refer to exact H only if the loss-residual second term is included. For an 8×8 DLN function, Jacobian rank cannot exceed 64 as a function of parameters despite N×8 data residual entries, because all predictions factor through the 64-dimensional effective matrix.

## Terminology retained only historically

Terms "physical truth", "phase transition", "superdetermined", "rank projection" and "precision exhaustion" are qualitative historical labels; they require precise mathematical definitions before use as theorem claims.
