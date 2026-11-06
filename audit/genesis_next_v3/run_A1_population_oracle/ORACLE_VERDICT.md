# GENESIS NEXT v3 — addendum A1: analytic population step oracle — verdict

**Evidence class:** `POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION`, DLN only, CPU FP64, no new training.
**Lock:** `ORACLE_LOCK.json`, freeze_sha `1a0b67701f7374f110156ca345fd405f569a8b49c85c2eb9ad8694d6c0e035f8`. It was frozen after the unit tests (`qualification/TESTS.log`, 6/6 OK) and the two pilots, and before the main run. The plan is in `source/oracle/ORACLE_PLAN.md`.
**v3 base:** freeze_sha `0b168ec5…`. It is read-only and its code hashes are re-verified at every state.
**Completion (2026-11-06):** 38/38 states exited with `EXIT_0`. 36 states are QUALIFIED. 598 of 618 direction rows are QUALIFIED; 20 rows in 2 states are `NUMERIC_UNRESOLVED`.

## What the oracle is
The v2 DLN data are y = A·x with x ~ N(0, R·diag(eig)·Rᵀ) and no noise. A, R and eig are regenerated and verified bit-exactly against teacher_sha and all three frozen splits.

The population risk of any weight set is exact: R(W) = ‖(W_L…W_1 − A)·R·D^½‖² / (2·d_out). Along every update ray it is an exact polynomial of degree 2L. α_pop is its exact continuous minimiser on [0, 30], taken from the roots of the derivative polynomial and cross-checked with Brent.

Numerical receipts per state:
- trace form vs the DLN pseudo-sample path: ≤ 1.7e-13 (qualified states);
- closed-form population gradient vs autograd: ≤ 1e-10;
- pool L0 vs v3: ≤ 1e-15;
- recomputed directions vs v3 norms: 0.0 for T32 directions and ≤ 4e-16 for T512 directions.

**Monte-Carlo validation.** The analytic R was compared with the native-FP64 E8192 loss at all 10 non-zero grid α (6180 comparisons):
- median |z| 0.66 for the loss and 0.81 for the gain;
- 0 comparisons with |z| > 3.

The z-values within a state are correlated. Even so, the analytic risk is the expectation that E8192 estimates.

**Unresolved rows.** Two d8_orthogonal checkpoint-3 states (`251adb3c…` and `d3ed4ec6…`) are near interpolation, with R0 = 1.5e-9 and 3.3e-13. In 18 rows (plus 2 diagnostic rows) the frozen minimiser cross-check failed at the 1e-22 absolute level. In `d3ed4ec6…` the gradient check also failed (2e-9 > 1e-10). These rows stay `NUMERIC_UNRESOLVED`, are not imputed, and are excluded from the statements below.

## Results: T32 directions, Full primary
n = 109 qualified conditions. α values are medians across conditions.

| step policy | median α | α > α_pop | population gain < 0 / > 0 | median share of the attainable gain captured |
|---|---|---|---|---|
| **α_pop (exact)** | **0.110** | — | 0 / 109 except slope < 0 | 1 |
| α*_T32, grid (deployed v2/v3 rule) | 1.0 | 94.5% | **99 / 10** | −106 (regret = 107× the attainable gain) |
| α^c_T32, continuous | 1.54 | 97.2% | 100 / 9 | −167 |
| α*_T512, grid | 0.10 | 34.9% | 14 / 67 (28 chose α=0) | 0.71 |
| α^c_T512, continuous | 0.111 | 40.4% | 14 / 68 | 0.78 |
| α*_T4096, grid | 0.10 | 44.0% | 12 / 93 | 0.89 |
| α^c_E8192, continuous | 0.132 | 69.7% | 16 / 82 | 0.97 |

* **T32 overshoots.** The T32-selected step is a median **10^1.15 ≈ 14×** the population-optimal step (continuous; grid: 10^1.05 ≈ 11×). In 99/109 conditions it increases the true population risk.
* **T512 selection is close to the population optimum.** The continuous T512 step has median log10(α/α_pop) = +0.002, and the grid T512 step captures a median 71% of the attainable population gain.
* **Block and CG8 behave the same way.**
  - Block: α_pop 0.096, T32 grid ≈ 10^1.08 above α_pop, population-negative in 104/108.
  - CG8: α_pop 0.065, T32 grid ≈ 10^1.26 above α_pop, population-negative in 109/109.
* **P4.** The population sign at α*_T32 agrees with the v3 E8192 resolved sign in **100%** of conditions for all three directions. The v3 held-out finding is a real population effect, not finite-sample noise.
* **P5, exact attribution (Full).** The population slope is negative (exact first-order conflict) in 11/109 conditions. Of the conditions with a negative population gain, 88 are exact step overshoot (positive slope). The population slope sign agrees with the v3 E8192 slope sign in 91% of conditions.

## Results: V4 T512 directions
9 seeds, 54 conditions per direction.

| Full, T512 direction | median α | α > α_pop | population gain < 0 / > 0 | gain captured |
|---|---|---|---|---|
| α_pop | 1.04 | — | — | 1 |
| α^c_T512, same batch as the direction | 2.32 | 90.7% | 30 / 24 | −0.05 |
| α*_T512, grid, same batch | 3.0 | 81.5% | 24 / 30 | 0.54 |
| α^c_T32, independent batch | 1.56 | 57.4% | 11 / 30 | 0.64 |
| α*_T4096, grid | 1.0 | 37.0% | 5 / 49 | 0.87 |

* **Same-batch optimism.** Selecting α on the batch that produced the direction overshoots the population optimum by about 10^0.31 ≈ 2× (median), even at T512. An independent batch overshoots less.
* **The T512 direction itself is better.** At its own optimal population step, the T512 Full direction attains a median **7.1×** the maximum population gain of the T32 Full direction, and is better in 83% of conditions. Block: 5.8×, 85%. CG8: 8.6×, 76%.

## Pre-specified statements
Each statement is evaluated per seed on the median over its conditions; the label is decided by the majority of seeds.

| statement | Full | Block | CG8 |
|---|---|---|---|
| P1: T32 step > α_pop | SUPPORTED (19/19 seeds; median log10 1.14, CI 0.99–1.20) | SUPPORTED (19/19) | SUPPORTED (18/18) |
| P2: T512 selection closer to α_pop **and** lower population regret (grid) | SUPPORTED (19/19) | SUPPORTED (18/18) | SUPPORTED (16/17) |
| P3: same-batch selection overshoots and overshoots more than independent selection (T512 directions) | SUPPORTED (8/9) | SUPPORTED (7/9) | SUPPORTED (6/9) |

All labels are `…_WITHIN_DLN_EXPLORATION`. Bootstrap CIs are in `ORACLE_SUMMARY.json`.

## Interpretation and correction to the v3 V4 reading
1. The v3 held-out degradation is a true population-risk increase. Its main cause is a T32-selected step that is about 10–14× too large. More data in the selection step (T512/T4096) moves α to within a factor of ~1 of α_pop.
2. The v3 V4 conclusion that "a direction change does not repair the sign" needs a qualification. With the exact population risk, the T512 direction is a substantially better direction (about 7× the attainable gain). It looked no better in v3 because its step was chosen on its own batch (T512), and same-batch selection overshoots. The v3 statement "batch-specific direction error: CONTRADICTED" therefore applies only to the deployed rule (same-batch α selection). It does not apply to the intrinsic quality of the directions. Both a step-selection bias and a direction-quality difference are present. The step bias dominates for T32.
3. The population-Newton diagnostic direction is the exact population GGN step with the same λ. Its median α_pop is 3.99, so with T32-calibrated damping the population-optimal step along it is large. This direction is a reference only and supports no claim.

## Limitations
* The results cover the noise-free linear-Gaussian teacher only, where the population is analytically available. Nothing transfers to nonlinear models or Transformers.
* 36 of 80 parent states are qualified here: 42 are SOURCE_NOT_READY and 2 are NUMERIC_UNRESOLVED near interpolation. Each setting has 4–5 seeds, and the CIs are descriptive.
* α_pop is the population optimum along fixed directions. It is not the optimum over directions.
* Grid policies inherit the coarse v2 grid. Continuous policies remove that quantisation, but they are analysis tools, not deployable rules.
* P3 rests on only 9 seeds (the two V4 settings).
