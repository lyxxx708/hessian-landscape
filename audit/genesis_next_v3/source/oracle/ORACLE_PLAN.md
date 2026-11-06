# GENESIS NEXT v3 — addendum A1: analytic population-risk step oracle (frozen plan)

Evidence class: `POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION`. This is an addendum to the frozen v3 run (freeze_sha `0b168ec5…`). The v3 run, its code (`genesis_next_v3/`, `scripts/`, `configs/`, `tests/`) and its results are read-only. Their hashes are re-verified at every state start. No new training is done.
Qualification pilots on states `2a40c51a…` and `0c4e9be6…` (unfrozen, in `qualification/`) were used only to check numerics, the minimiser and the tolerances. The superseded first pilot used Brent as the primary minimiser.

## Population
v2 generates x = R·diag(√eig)·z with z ~ N(0, I), and y = A·x with no noise. The teacher A, the rotation R and eig are regenerated and verified bit-exactly against the frozen splits and teacher_sha.

For the product M = W_L…W_1, the exact population risk is R(M) = ‖(M−A)·R·D^½‖²_F / (2·d_out). This is the expectation of the v2/v3 half-MSE loss. Along a ray W + αE, R(α) is an exact polynomial of degree 2L.

Self-checks per state:
- trace form vs the DLN pseudo-sample path: ≤ 1e-12;
- closed-form population gradient vs autograd: ≤ 1e-10;
- pool L0 vs v3: ≤ 1e-15.

Monte-Carlo agreement: z-scores of the E8192 (native FP64) loss and gain against R at every v3 grid α. These are reported as a distribution and are not used for gating.

## Directions (identical to v3, recomputed and verified)
- **T32 directions, all 38 states:** Full, Block (best-ray) and CG8 (best-ray). Replay: the direction norm matches v3 within 1e-12 relative.
- **T512 directions, the V4 settings** (d4_orthogonal_balanced_c1 and d8_random_unbalanced_c100): Full, Block and CG8. Replay tolerance is 1e-9, because the closed-form T512 gradient replaces the AD gradient.
- **Population-Newton diagnostic:** `POP_DIAGNOSTIC` = −(G_pop + λI)⁻¹ g_pop with the same absolute λ. It is never used for selection or for any claim except a reference column.

## Step sizes compared (all on the same ray)
- α_pop: the exact continuous minimiser of R(α) on [0, 30]. It uses the derivative-polynomial roots, Newton-polished and ranked by direct evaluation, cross-checked by a scan plus bounded Brent. A Brent location disagreement over 1e-4 relative, Brent finding a lower R, or the minimiser sitting on the boundary → `NUMERIC_UNRESOLVED`.
- **Grid (deployed v3 rule, old grid [0,.01,.03,.1,.3,1,3], ties → smaller):** α*_T32, α*_T512 and α*_T4096. For T32 directions only, the v3 E8192 grid oracle is a diagnostic.
- **Continuous empirical minimisers:** α^c_T32, α^c_T512, α^c_T4096 and α^c_E8192. These separate the effect of grid quantisation from that of the batch.
- **Metrics per policy p:**
  - population gain G_p = R(0) − R(α_p), with a bound 64ε(R0 + R(α_p));
  - regret R(α_p) − R(α_pop);
  - regret / max gain;
  - log10(α_p / α_pop).

## Pre-specified statements
The unit is the training seed. Each statement is evaluated per seed on the median over its conditions, and the verdict uses the majority of seeds. The primary direction is Full; Block and CG8 are reported with the same rules. Labels are SUPPORTED_ / CONTRADICTED_WITHIN_DLN_EXPLORATION, or INCONCLUSIVE when exactly half of the seeds agree.

- **P1 — T32 overshoots the population optimum** (T32 directions). The median log10(α^c_T32 / α_pop) is > 0 in a majority of seeds. The grid version, α*_T32 > α_pop, is reported alongside.
- **P2 — T512 selection is closer to the population optimum and has lower population regret** (T32 directions). Both conditions must hold in a majority of seeds:
  - the median of |log10(α^c_T512/α_pop)| − |log10(α^c_T32/α_pop)| is < 0;
  - the median of regret(α*_T512) − regret(α*_T32) is < 0 (grid, the deployable rule).
- **P3 — same-batch selection optimism** (V4 seeds). Selecting α on the batch that produced the direction overshoots more than selecting it on independent data:
  - For T512 directions: the median log10(α^c_T512/α_pop) is > 0 and > the median log10(α^c_T32/α_pop) in a majority of seeds.
  - Companion for T32 directions: the median log10(α^c_T32/α_pop) is > the median log10(α^c_T512/α_pop).
- **P4 — the population confirms the v3 E8192 sign.** This is the agreement between sign(G at α*_T32) on the population and the v3 E8192 resolved sign (descriptive), together with the count of conditions whose population gain at α*_T32 is negative.
- **P5 — exact population attribution.** Counts of resolved population slopes s_pop = −g_popᵀd < 0 (exact FIRST_ORDER_CONFLICT) versus s_pop > 0 with G(α*_T32) < 0 (exact STEP_OVERSHOOT), compared with the v3 E8192 labels.

Descriptive companions:
- seed-cluster bootstrap CI (2000 reps, seed 20261106) of the median of seed medians of each log ratio and regret difference;
- fraction of the max gain captured by each policy.
No p-values. Test1024 is not used.

## Coverage
38 of 80 parent states (114 of 240 conditions). The 126 conditions not covered are SOURCE_NOT_READY, as in v3. Failures and timeouts are recorded in the ledger and are not replaced.
