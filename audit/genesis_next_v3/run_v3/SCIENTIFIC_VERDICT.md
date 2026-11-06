# GENESIS NEXT v3 — scientific verdict

**Evidence class:** `POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION`. This is a DLN-only, CPU FP64 re-analysis of frozen v2 checkpoints, with no new training. Passing numerical qualification is not scientific confirmation.
**Protocol lock:** `PROTOCOL_LOCK.json`, freeze_sha `0b168ec5ff55c70a012a92af301c5d4bef96dc9edb54eb6eb9faa9abb30aba94`. The plan and analysis code were frozen before the main assay ran.
**Completion state (2026-11-06):** the driver finished. All 38/38 planned states exited with `EXIT_0` (wall time 300–720 s per state). There were no failures, timeouts or `NUMERIC_UNRESOLVED` conditions, and `FAILURES.csv` = `NONE_RECORDED`.

## Coverage
| | states | conditions |
|---|---|---|
| Parent plan (NEXT v2) | 80 | 240 |
| Assayed, `QUALIFIED` | 38 | 114 (19 seeds × ckpt {1,3} × γ {1e-3,1e-2,1e-1}) |
| `SOURCE_NOT_READY` (not imputed, failed seed not replaced) | 42 | 126 |

Coverage spans 4 DLN settings (d4/d8 × orthogonal-balanced c1 / random-unbalanced c100) with 4–5 seeds each. Every sign below is resolved against its numerical bound: there were 0 indeterminate gains and 0 indeterminate slopes in any primary pool.

## Exp V — why train-selected second-order steps worsen held-out loss

**(a) Does the negative sign survive on real E8192 data?** Yes. The table gives the gain at train-only α* (T32, v2 grid). The sign of a positive gain counts as a positive result.

| direction | T32 gain>0 | E8192 gain<0 | V1024 <0 | T4096 <0 | Test1024 <0 (once) | median gain/L0 on E8192 |
|---|---|---|---|---|---|---|
| Full | 114/114 | 102/114 | 101/114 | 101/114 | 102/114 | −0.136 |
| Block | 114/114 | 106/114 | 106/114 | 106/114 | 107/114 | −0.120 |
| CG8 | 114/114 | 112/114 | 111/114 | 111/114 | 111/114 | −0.182 |

Every check agrees:
* The native-FP64 sensitivity column matches the primary FP32→FP64 policy (gain/L0 differs at the ~1e-8 level).
* The 8192-example new-data pool, the training-distribution pool T4096 and the original Test1024 agree. The effect is therefore not an artifact of the 32-example v2 validation batch.
* It is also not an artifact of a train/test distribution shift: T4096 (training data) shows the same sign.

**(b) Mechanism: step overshoot or first-order conflict?** Counts are for E8192, among resolved-negative gains at α*. Labels are non-exclusive.

| direction | STEP_OVERSHOOT | FIRST_ORDER_CONFLICT | BATCH_HETEROGENEITY | CURVATURE_OR_HIGHER_ORDER_MISMATCH |
|---|---|---|---|---|
| Full | 91/102 | 11/102 | 7 | 0 |
| Block | 95/106 | 11/106 | 5 | 0 |
| CG8 | 96/112 | 16/112 | 6 | 0 |

On V1024 the first-order conflict fraction is higher (Full 24, Block 26, CG8 33) and there is one CURVATURE label. V1024 is 8× smaller, so its slope estimate is noisier.

Supporting facts:
* **α\* is always large.** Train-only selection picks α=1 (235/342) or α=3 (107/342).
* **Small steps help on held-out data.** The oracle α on E8192 gives a resolved positive gain in 103/114 conditions (Full), at small α.
* **Validation-assisted α helps (diagnostic only, not deployable).** It turns E8192 to a positive gain in 78/114 conditions and negative in 17/114. On Test1024 the figures are 63/114 positive and 32/114 negative.

**Answer:** the dominant mechanism is **step overshoot**. The T32-trained direction is still a descent direction on held-out data in ~90% of conditions, but the T32-selected step (α≈1–3, close to the full Newton step) overshoots. A genuine first-order conflict appears in ~10–15% of conditions.

**Discriminators:**
* D1 (training-batch bias, i.e. negative held-out slope): minority only.
* D2 (overshoot): SUPPORTED_WITHIN_DLN_EXPLORATION.
* D3 (Taylor mismatch): CONTRADICTED_WITHIN_DLN_EXPLORATION, with 0–1/114 labels.
* D4 (noise): minor. Sub-batch sign mixing occurs in ≤7/114 conditions on E8192.

**(c) V4 intervention (T512 vs T32).** Fixed settings d4_orthogonal_balanced_c1 and d8_random_unbalanced_c100, 9 seeds, 54 conditions per direction. All 162 T512 solves were `QUALIFIED`, none `RESOURCE_CENSORED`. Results are on E8192:

| direction | (a) T32 dir @ α\*(T32) neg | (b) step-only neg | (c) T512 dir neg | seeds where (b) repairs majority | seeds where (c) repairs majority |
|---|---|---|---|---|---|
| Full | 49/54 | 7/54 | 24/54 | 8/9 | 4/9 |
| Block | 50/54 | 6/54 | 27/54 | 9/9 | 2/9 |
| CG8 | 54/54 | 8/54 | 31/54 | 9/9 | 2/9 |

**α=0 caveat.** Some step-only "repairs" are cases where train-only selection on T512 chose α=0, i.e. no step (Full 12/49, Block 13/50, CG8 13/54). Counting only repairs with a resolved positive gain:
* step-only: Full 30, Block 31, CG8 33;
* direction change: Full 25, Block 23, CG8 23. None of these are α=0 cases.

**Verdict on "batch-specific direction error":** `CONTRADICTED_WITHIN_DLN_EXPLORATION`. The pre-registered rule needed (c) to repair a majority of seeds while (b) did not. Instead (c) repairs the majority in only 2–4/9 seeds, and step-only rescaling repairs it in 8–9/9. Re-selecting the step on more data fixes most of the sign. Changing the direction does not reliably fix it: the T512 direction at its T512-selected α is still negative in ~half the conditions.

**Test1024 (reported once, frozen policies).** It matches E8192: Full 102/114 negative at α\*. With the validation-assisted α it is 32/114 negative.

## Exp B — does Full CG still beat an optimized exact Block-GGN at fair cost?

Cost ratio = seed-level median of cost(first CG k with F_CG ≥ F_B − 1e-4·F\*) / cost(Block Kronecker-direct). The 95% CI is a seed-cluster bootstrap with 2000 repeats (descriptive only). End-to-end cost includes the common gradient and the T32 line search.

| policy | mode | median ratio CG/Block | 95% CI | median first k |
|---|---|---|---|---|
| raw direction + train grid (no Qd) | cold | 1.02 | 0.96–1.06 | 4 |
| raw | warm 3-γ | 1.06 | 1.02–1.10 | 4 |
| best-ray (+1 charged Qd) end-to-end | cold | 1.18 | 1.11–1.19 | 8 |
| best-ray end-to-end | warm | 1.24 | 1.10–1.25 | 8 |
| best-ray, method cost only | cold | 2.16 | 1.68–2.41 | 8 |
| best-ray, method cost only | warm | 3.36 | 1.92–3.73 | 8 |

Notes on these ratios:
* **Ratios by setting:** the cold-raw ratio ranges from 0.95 (d8 random) to 1.06 (d4 random).
* **CG never reaches the Block quality** in 6/114 conditions (d8 orthogonal, raw policy). These are kept in the denominator.
* **Timing:** 227/3002 timed tasks (7.6%) were `TIMING_INCONCLUSIVE` and are excluded from ratio claims.

**Historical control (implementation effect).**
* The NEXT v2 padded AD block-CG is a median **1541×** slower than Kronecker-direct. Exact local-matvec block CG is 13× slower than direct.
* Against that old block, CG (via AD) costs a median 0.033 of the time. This reproduces the historical "CG costs 2–15% of block" result.
* **Quality ceiling:** Block attains F ≥ 0.99·F\* in only 1/114 conditions; the other 113 are `QUALITY_TARGET_UNATTAINABLE`.

**(d) Answer:** the historical CG cost advantage is **erased** by an optimized exact Block. It was an implementation artifact of the padded AD block solver. At equal quality (matching F_B), CG costs about the same as Block-direct under the raw policy (≈1.0–1.06×). Under the best-ray policy CG is 1.2× costlier end-to-end and 2–3× costlier counting method cost only.

This does not mean Block is better overall. The exact block-diagonal GGN almost never reaches 0.99·F\*, while CG reaches higher quality at larger k. The cost question is therefore conditional on quality.
* "CG beats Block at equal quality": `CONTRADICTED_WITHIN_DLN_EXPLORATION`.
* "Block can match Full quality": `CONTRADICTED_WITHIN_DLN_EXPLORATION`.

These comparisons use no oracle stop rule. The rtol stop rules are reported in `BLOCK_CG_COST.csv`. Full or exact-Block quality was never used as an online stopping signal; the "first k reaching F_B" is an offline accounting.

## Outcome labels
| statement | label |
|---|---|
| Negative held-out sign persists on E8192/T4096/Test1024 | SUPPORTED_WITHIN_DLN_EXPLORATION |
| Dominant mechanism is step overshoot (not first-order conflict) | SUPPORTED_WITHIN_DLN_EXPLORATION |
| Second-order Taylor mismatch explains the sign | CONTRADICTED_WITHIN_DLN_EXPLORATION |
| Batch-specific direction error (V4) | CONTRADICTED_WITHIN_DLN_EXPLORATION |
| CG cheaper than optimized exact Block at equal quality | CONTRADICTED_WITHIN_DLN_EXPLORATION |
| Behaviour outside DLN (Transformer, nonlinear nets) | NOT_TESTED |

## Limitations
* **DLN only.** The block solve is exact only for bias-free linear networks with MSE loss; it is not K-FAC. Nothing here transfers to nonlinear models or Transformers without new evidence.
* **Post-hoc analysis.** This is S1 exploration on 38/80 states (the 42 others are SOURCE_NOT_READY), with 4–5 seeds per setting. The bootstrap CIs are descriptive, with no p-values.
* **Timing environment.** Timings come from a shared 16-CPU workstation pinned to 2 threads. System CPU had median 34.9% (range 24–68%) across 532 contention samples, mostly from Chrome, Weixin, WSL (vmmem) and the concurrent v2 GPU worker's host process. Of the timed tasks, 7.6% were inconclusive. The ratios near 1.0 are within this noise, so "about equal" is the claim, not a winner.
* **Not implemented.** CG Krylov reuse across γ in warm mode, and preconditioned CG. Best-ray CG with scale=1 is not separately explored. The AD-operator CG and the old padded block are controls only.
* **α grid.** V4 and the α selection use the coarse v2 grid for train-only selection. Validation-assisted α is a diagnostic, never a deployable claim.
* **Not run on GPU.** No GPU, no new training and no cloud budget were used. The v2 GPU worker was not disturbed.

## Files
The tables (`VALIDATION_ALPHA_GRID.jsonl`, `DIRECTIONAL_SLOPE_AND_HVP.jsonl`, `VALIDATION_ATTRIBUTION.csv`, `V4_INTERVENTION.csv`, `BLOCK_CG_COST.csv`, `BLOCK_CG_COMPARISON.csv`, `BLOCK_REFERENCE_CHECKS.jsonl`, `NUMERIC_QUALIFICATION.csv`, `PAIRED_SEED_SUMMARY.csv`, `FAILURES.csv`, `ANALYSIS_SUMMARY.json`), the ledger and per-state results are in this directory. SHA-256 hashes are in `FILE_MANIFEST_SHA256.csv`, and reproduction steps are in `README_REPRODUCE.md`. The public-safe evidence copy is at `E:\GENESIS\evidence\genesis_next_v3`.
