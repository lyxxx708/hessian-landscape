# WorkBuddy four-line pilot: 2026-10-26 evidence snapshot

**Source:** Parsed text of the contemporaneous 463-line `EXPERIMENT_REPORT.md`, transcribed under `archive/source-transcripts/`. All figures and [S01–S19] referenced therein are **not present in this pull request**. This document records report claims, not new independent numerical validation.

## First-batch immutable execution status

| Line | Original terminal state | CPU seconds | Peak MiB | Original output bytes |
| --- | --- | ---: | ---: | ---: |
| GENESIS | PILOT_EXECUTION_FAILED | 218.875 | 1,065.16 | 11,527,484 |
| NAO V3 | PILOT_COMPUTATION_VERIFIED | 347.28125 | 2,462.91 | 186,917,218 |
| Anti-Slowing | PILOT_EXECUTION_FAILED | 240.609375 | 5,365.87 | 1,899,933,723 |
| signed-Sokal | PILOT_COMPUTATION_VERIFIED | 21.203125 | 1,132.57 | 13,536,017 |

Child Job CPU total **827.96875 seconds** (parent controller separate **26.859375 seconds**). Producer failure remains historical fact even when later recomputation or stream-hash audits pass.

## GENESIS: deep-layer endpoint eligibility blocks inference

The new test is a **residual teacher/student synthetic model**, not the earlier unqualified original DLN plateau experiment. Student input 4, output 2, width 4, depths 2/4/8, six matched seeds per depth. The original pilot optimizer cap was 5,000 objective calls and stationarity threshold 1e-6.

| Depth | Seeds | Gradient-qualified | Significant negative curvature | Legacy valid_minima |
| --- | ---: | ---: | ---: | ---: |
| 2 | 6 | 6 | 3 | 3 |
| 4 | 6 | 2 | 5 | 1 |
| 8 | 6 | 1 | 6 | 0 |

The original producer's coarse finite-difference check failed; an exact directional second-derivative audit later examined 18 models/90 directions and recorded RAW_RECOMPUTATION_PASS. **That does not repair absent second-order qualified deep minima or enable a cross-depth plateau conclusion.** N1 finite chain, N2 199 isospectral-Haar samples, N3 predetermined low-rank models, N4 distinct GGN/ridge operators were proposed; the full eligible null envelope has not been established.

Current disposition: **STOP_CURRENT_PLATFORM_PROMOTION_REVISE_MINIMUM_FEASIBILITY**.

The v3r15 feasibility candidate proposes matched 5,000 vs 20,000 objective-call caps for 36 fits / 18 paired initializations. Deterministic qualification **10/10 PASS** with `scientific_runs=0`, `training_data_generated=false`; the **36-fit scientific pilot has not run**. Runtime binding reported 28/30 matches with two Python runtime-anchor hash mismatches, and authorization/review/resource gates remain unclosed.

## NAO V3: prediction and surrogate failure

Eighteen trajectories (SGD/SGDM/Adam; six seed clusters each), 126 nested origin records; independent unit is seed rather than origin.

| Optimizer | Median candidate gain over best baseline | Seeds exceeding 20% |
| --- | ---: | ---: |
| SGD | −3.5276% | 0/6 |
| SGDM | −10.3886% | 0/6 |
| Adam | −40.0843% | 1/6 |

The required multiscale surrogate/null family did not satisfy scientific eligibility. Optimizer-state ablations and one favorable Adam seed are not evidence of a reliable across-seed mechanism. Current claims must remain **negative/inconclusive**, not “optimizer-memory time-scale discovery”.

## Anti-Slowing: original producer failed and thresholds were not met

Six nonlinear seeds, seven q values, 84 primary cases. Predeclared main effect D>0.20 and localization L>0.10 jointly required; **0/6** achieved both. All six localization contrasts were negative. Calibration: Q1 and Q4 had 6/6 eligible seeds, Q2 had **0/6** eligible full panels. Even with zero observed false promotion in n=6, the one-sided 95% Clopper–Pearson upper bound is **0.39303777**, nowhere near 5%.

The producer exceeded its memory budget during whole-file hashing and terminated with code 124. Later streaming recomputation verified existing cases at lower peak memory but did not erase that original failure or provide pre-crash sealed provenance.

Current disposition: **REVISE_SCIENTIFIC_PIPELINE_BEFORE_ANY_CALIBRATION**. Historical 2026 July GPT-2 Anti-Slowing observations are **not** this new 8-D synthetic test.

## Signed-Sokal: scoped exact counterexample and negative finite grid

The two-state boundary calculation at p=3/10, φ=−2/5, c=5 reports f(1)=0, f(2)=−3/5, f(3)=26/25; a sample first-crossing mixture was argued under stated conditions. This addresses a particular overstrong consistency formulation, not any unseen theorem.

The newly predeclared reversible three-state finite grid used 27 matrices × 3 constants = **81 exact cases**: target cases with two exact boundary lags **0**, reentry cases **0**, never-crossing cases **0**, independent per-case readback **81/81**. Disposition **STOP_CURRENT_CLAIM**, scoped to this finite family only.

## Whole-program caveats

- Recorded aggregate is **1,984 files / 2,139,736,566 bytes** in a separate source archive, not uploaded here.
- Resource budget accounting in the report totals 1,064.71875 CPU seconds (sub-job + parent accounting); GPU usage recorded as zero.
- The 2026-10-26 author explicitly states no original core claim has been independently established as a generalizable confirmatory result.
- Engineering fixture PASS, deterministic gate PASS, computation verification, producer terminal success, and scientific result acceptance **must not be conflated**.

Read the [full text-transcribed report](../archive/source-transcripts/2026-10-26_WORKBUDDY_EXPERIMENT_REPORT.md) before interpreting these summaries.
