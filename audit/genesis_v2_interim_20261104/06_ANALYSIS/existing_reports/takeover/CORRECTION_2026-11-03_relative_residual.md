# Correction: relative residual misreported (original retained)
Original statements (kept unmodified in FINDINGS_2026-11-03.md F4 and in the status message of 2026-11-03):
 "ckpts 1-3 median rel true residual 0.46-0.66" and quantiles up to 9.2e3.
Error: `true_residual` in a solve receipt is already relative; the analysis divided it by ||g|| again.
Corrected values (full_solve, gamma=0.001, 224 records at time of recomputation, relative to ||b||):
 ckpt 0 median 3.74e-04 (range 7.67e-05..6.38e-04)
 ckpt 1 median 3.68e-03 (6.05e-04..1.20e-02)
 ckpt 2 median 2.92e-03 (5.78e-05..7.91e-03)
 ckpt 3 median 2.65e-03 (1.24e-04..9.11e-03)
Conclusions unaffected: every record still exceeds rtol=1e-5, and the failure attribution came from separate solver comparisons computed correctly as absolute_residual/||g||. Not affected: "rel" values in cgdiag.py output.
## Field definitions (genesis_gpu/contracts.py SolveResult, genesis_gpu/solvers/cg.py)
 true_residual     = ||Qx-b||_2 / ||b||_2, recomputed with the operator; dimensionless; compared to rtol.
 absolute_residual = ||Qx-b||_2; units of b (loss per parameter unit for gradient RHS).
 residual_history  = recursive ||r_k||_2 / ||b||_2; an estimate, not a true residual, reset at refreshes.
 Denominator b: -g for full solves; -g restricted to the block for block solves (block norm, not ||g||); Rademacher z for structural probe solves; the block-residual for rho solves.
 Q = GGN + lambda*I, lambda = gamma * power-iteration scale (absolute, not relative).
