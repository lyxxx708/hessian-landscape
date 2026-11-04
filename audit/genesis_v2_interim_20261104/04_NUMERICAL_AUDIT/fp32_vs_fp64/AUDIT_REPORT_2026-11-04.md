# v2 FP32 numeric audit: interim report

Date: 2026-11-04. Protocol and script are hash-verified (`protocol_and_script.sha256`), with `ADDENDUM_01_thread_pinning.md`. Raw rows: `audit_rows.jsonl`. Interim because v2 is still running: this covers every COMPLETE measurement at the time of the last pass, all of it DLN.

## Result

**610 rows: 604 `AGREE`, 6 `MATERIAL`; no `DIVERGENT`, `STATUS_CHANGE` or `UNAUDITABLE`.**

Coarse and fine schemas gave identical v2 δ in all 305 pairs, so these are **305 distinct measurements: 302 AGREE, 3 MATERIAL**, over 151 states and 8 settings.

The FP64 reference agreed with the CG-free dense solve to at most 9e-7 in the 594 rows of the first pass, and no row of the final 610 was `UNAUDITABLE` (threshold 0.005).

| Absolute difference, v2 vs FP64 | Median | p99 | Max |
|---|---|---|---|
| δ | 1.6e-7 | 1.6e-3 | 3.3e-2 |
| E_task | 3.5e-7 | 3.0e-3 | 3.2e-2 |
| E_val | 4.2e-7 | 1.6e-3 | 4.4e-2 |
| cheap_rho | 3.0e-7 | 1.6e-3 | 3.6e-2 |
| F* | 3.8e-11 | 3.4e-7 | 7.0e-7 |

## The MATERIAL measurements

All three are from one trajectory: `dln_d8_w16_orthogonal_balanced_c1`, seed 3. Each is NUMERIC_VALID in v2 and passed `delta_stability`.

| Checkpoint | γ | δ v2 / FP64 | E_task v2 / FP64 | E_val v2 / FP64 | Recorded stability |
|---|---|---|---|---|---|
| 3 | 0.1 | 0.1794 / 0.1461 | 0.3778 / 0.3504 | 0.4381 / 0.3940 | 2.1e-7 |
| 2 | 0.1 | 0.1499 / 0.1288 | 0.3624 / 0.3308 | 0.3888 / 0.3697 | 3.9e-9 |
| 3 | 0.01 | 0.2402 / 0.2307 | 0.4126 / 0.4024 | 0.4601 / 0.4338 | 3.1e-6 |

The errors are larger than the protocol's `delta_stability` tolerance (0.005) and `delta_lower` (0.01), yet recorded stability was at most 3.1e-6. **`delta_stability` cannot detect this error**: it measures solver agreement, and both solves share the same wrong gradient.

At these states, FP32 and FP64 gradients differ far more than the norm suggests (FP32 on CPU as a proxy):

| Checkpoint | \|g\| FP64 | \|g\| recorded (GPU) | Relative vector error | Cosine |
|---|---|---|---|---|
| 3 | 2.65e-7 | 3.15e-7 | 41% | 0.928 |
| 2 | 2.99e-7 | 3.17e-7 | 40% | 0.934 |

## Scientific impact so far

- **No threshold crossing at measurement level:** no audited δ changes side of `delta_lower` (0.01) or `delta_median` (0.05), and no `task_status` changes.
- **Setting-level inference not assessed.** S1 is unfinished, so its effect on setting statistics needs a sensitivity analysis once S1 adjudication exists.
- **Scope.** Only DLN has been measured. MLP, ResNet and Transformer have no v2 measurements to audit, so this says nothing about them.

## Exploratory, does not reclassify anything

Small |g| is related to the risk but does not decide it:
- Same trajectory, checkpoint 2, γ=0.01, |g| 3.0e-7: AGREE (D=3.0e-3), while γ=0.1 on the same state is MATERIAL.
- Seed 2, checkpoint 3, |g| 7.4e-6, gradient vector error 1%: AGREE (D≤6.8e-4).

Gradient vector error tracked δ error better than norm: states with errors of about 40% show δ differences of 2e-2 to 3e-2, 1% or less shows 6e-5 or less. There are only two states in the high group, so this is a lead and not a validated screen.

## Other findings

1. **Coarse and fine are numerically identical on DLN, and this is by design of the code.** All 305 pairs match. See "Owner review" below: formal statistics do not double count them.
2. **Corrections to my earlier statements.** I said the FP32 gradient on this state was "off by about 10%". The norm differs by 19% (recorded GPU) and the vector by 41% (CPU proxy). I also quoted FP32 δ 0.1772, which was a CPU FP32 recomputation; v2's recorded value is 0.1794. The CPU and GPU FP32 values differing by 0.002 shows these results are also sensitive to device.
3. **Device limit.** The FP64 side ran on CPU and v2 on GPU, as the protocol notes. The dense check and matching on CPU make the FP64 values reliable; the split of the error between FP32 and device is not established.

## Owner review (2026-11-04), checked against frozen source

**Schema redundancy, confirmed.**
- `group_for` in `models/dln.py:27` and `models/mlp.py:22` ignores `schema`, so coarse and fine are the same partition for those families.
- `study/statistics.py:29,71` and `science/predictor.py:32` filter to coarse, so U, S and P do not double count them.
- `expand_design` gives 105 DLN and MLP S1 runs, so 1,260 of 3,120 S1 measurement jobs (40.4%) repeat a partition. Only MLP's real runs are still to come.
- v2 keeps these jobs. v2.1 should drop them, under its own protocol lock. ResNet and Transformer `group_for` were not reviewed here beyond seeing they are separate implementations.

**S1 predictor risk, confirmed as a separate exposure from U.**
- `predictor.py:32` includes every NUMERIC_VALID coarse row with checkpoint ≠ 0, so all 3 MATERIAL rows enter as training targets.
- `features()` (`predictor.py:18-25`) uses the recorded gradient: `log10(g)`, short-CG and matched-CG gain divided by g², plus `cheap_rho`. The recorded norm on these states is about 6% to 19% above FP64, and gain/g² is squared in that error, so inputs are affected as well as targets.
- U uses checkpoints 1, 2, 3 (`statistics.py:29`), so one seed's aggregate for this setting can move. Not crossing a measurement threshold does not show the conclusion is unchanged.
- The 3 rows share one seed: they are one failure, not three independent ones. 3/305 understates how concentrated the problem is and is not an independent error rate.

**Audit limits to carry forward.** Only δ, E_task, E_val, cheap_rho, F*, status and gradient are compared. Structure metrics and the other predictor features (short and matched gain ratios, `layer_scale_cv`, off-diagonal proxy) have not been independently checked.

**Sensitivity analysis, run independently and only in this directory; it does not gate anything.** Owner correction, 2026-11-04: an earlier version of this section said it must finish before formal S1 adjudication. That was wrong. The frozen pipeline runs S1, S1 adjudication, S2, S2 adjudication automatically and must not wait for it.

Once S1 data is complete, compare U and P across three inputs: original data, these rows excluded, FP64 values substituted. It needs the FP64 predictor features, which `audit_rows.jsonl` does not store, so the flagged rows need a recomputation at that point. Results can raise or lower confidence in conclusions, but cannot change the frozen formal result, the S1 predictor or the S2 confirmation rules. S2 seeds are not reselected from audit results.

**Final reporting is three separate parts:** (1) scientific conclusions under the original v2 protocol; (2) systematic error and sensitivity from the independent FP32 audit; (3) v2.1 repair effect, cost and unfinished validation.

## Disclosure text for the final report

> An independent read-only FP64 audit of v2 results found that NUMERIC_VALID does not guarantee numerical accuracy at very small gradient. In the audited DLN set, 302 of 305 distinct measurements agreed within 0.005; 3, all from one near-converged trajectory, differed by up to 0.033 in δ and 0.044 in E_val without triggering any v2 check. Results are not validated to high precision beyond this audit, and families not yet audited carry no such assurance. Original labels and receipts are unchanged.

The counts must be updated from a final audit pass before use.
