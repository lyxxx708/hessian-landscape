# GENESIS NEXT v2 — Scientific verdict

Evidence class: `POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION`. Freeze `0c881869d1eb…`. All numbers come from `SCIENTIFIC_RESULTS.csv`, `CG_COST_COMPARISON.csv`, `SEED_SUMMARY.csv`, `STRUCTURE_MECHANISM_RESULTS.jsonl` (FP64, CPU, frozen S1 checkpoints, v2 batch lifted to FP64). Statistics are descriptive; the independent unit is the training seed (4–5 seeds per setting); no p-values, no confirmation claim.

## Coverage (denominator stays 240 conditions)
| status | conditions |
|---|---|
| NUMERIC_VALID (FP64 dense + alternate-operator + autograd cross-checks passed) | 114 (all 38 DLN states × 3 γ) |
| SOURCE_NOT_READY (no COMPLETE v2 S1 training receipt) | 126 (MLP 30, ResNet 30, Transformer 60 conditions, plus 6 DLN conditions of the setting whose v2 seed 0 failed) |
| NUMERIC_UNRESOLVED / FAILED / TIMEOUT | 0 / 0 / 0 |
Only the DLN family was evaluable. Nothing about MLP, ResNet or Transformer was measured. G0/initial states were not substituted.

## H1 — structure–action decoupling: SUPPORTED_WITHIN_TESTED_SCOPE (DLN only)
* The damped inverse's Frobenius energy sits overwhelmingly in the GGN near-null space (per-condition range 0.81–0.999; nullity 768–1805 of 1024–2048 parameters), yet the gradient's projection on that space is ≈0 (median ≈0, max 1.1e-3). Most of the inverse's matrix norm is therefore irrelevant to the actual update.
* Caveat (important): a large null-energy fraction is partly mechanical — each null direction contributes 1/γ² — so this alone is not a discovery. The informative part is the second statement: the update lives in a small gradient-weighted subspace (effective gain directions median 13.5, range 2.9–45; n99 median 98, range 15–165 out of ≥1024 parameters).
* The cross-layer share of the *full* inverse (0.3%–20%) does not predict Block's loss: within each γ the Spearman association between inverse off-diagonal fraction and δ is negative (γ=0.001: −0.76, γ=0.01: −0.48, γ=0.1: −0.24; n=38 per γ, seeds/checkpoints correlated), while the pooled association is positive (+0.30) — a pooling artifact driven by γ. Descriptive only.
* δ (relative Block loss of quadratic gain): 0.022–0.29 setting medians; decreases monotonically with γ in every setting (e.g. d4 balanced 0.125 → 0.093 → 0.022).

## H2 — non-cheaply-replaceable cross-layer value: CONTRADICTED_WITHIN_TESTED_SCOPE (DLN only)
* 0/114 conditions where CG failed to reach the Block gain within 64 steps. Median first grid CG budget reaching Block's quadratic gain: 2–16 matvecs; at that budget CG's solve wall time is 0.02–0.10 of Block's (max over conditions 0.15).
* Full-convergence CG (rtol 1e-8) used 18–214 matvecs (median 69) and 0.19–0.83 of Block's wall (matvec-matched CG, budget = Block matvecs+1, *enforced*; wall-clock is reported separately and not claimed equivalent).
* Block therefore buys nothing CG does not deliver sooner and cheaper here; the cross-layer part of the exact solution (δ up to 0.38) is cheaply recoverable.
* **Nonlinear architectures: NOT_YET_TESTED.** The question "is there a stable cross-layer benefit in nonlinear networks that CG cannot cheaply obtain" is open. Do not extrapolate from DLN.

## Real one-step loss vs quadratic reference (kept separate)
Train-selected line search: train gains exist but are ~1e-7 (loss near floor). Validation gain is negative in 81% of Block steps and 80% of full-solve steps (median ≈ 0): the quadratic reference F is not a predictor of generalization of a single step on one batch at these checkpoints. `block_gain_above_roundoff` is recorded per row.

## E3 gauge control — mathematical covariance confirmed (no new discovery)
36/36 PASS: covariant damping reproduces direction/δ to 7e-16, forward drift ≤6e-16. Fixed Euclidean damping changes δ by median 0.010, up to 0.106 after function-preserving rescaling of layers 0/1 (scales 0.5, 2, 10). This is known covariance; the quantitative damping-dependence for these networks is the only content.

## E4 numerical error attribution (114 conditions with dense references)
* Input quantization of δ (native FP64 vs FP32-rounded batch): median 2e-8, max 6.3e-3.
* FP32 arithmetic on the same rounded inputs: median 1.1e-7, max 2.0e-2.
* v2's recorded δ vs FP64 reference (76 NUMERIC_VALID rows): median |err| 2e-7; 2 rows exceed 1e-3 (max 0.027), both `dln_d8_w16_orthogonal_balanced_c1`; there arithmetic error dominates and input quantization has the opposite sign, so neither is "the" cause.
* All 38 v2 NUMERIC_UNRESOLVED conditions are FP64-valid here (δ 0.079–0.381). The solver is a FP32 limitation, not absent signal.
* Reference checks: max over 114 conditions: operator cross-check 2.5e-16, gradient cross-check 2.1e-10, full-direction error 4.3e-8, dense-vs-CG δ difference 2.3e-10, true CG residual 1.0e-8.

## Limits
DLN only (depth 4/8, width 16, widths 32/depth 16 not in this frame); small dense problems (1024/2048 params); synthetic data; seed 0 of one setting is unavailable (v2 failure) → 4 seeds; S1 data already seen in v2 and NEXT v1 E0; single batch; no CIs claimed below 4 seeds.
