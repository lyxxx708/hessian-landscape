# Scientific status — evidence cut 2026-10-26

**Primary source:** [2026-10-26 WorkBuddy full-stage report](sources/EXPERIMENT_REPORT_20261026.md), §§3–13, S01–S19. This file transcribes source-reported data; original ZIP, CSVs, executable and raw run directories are not currently in this repository. It is not an independent re-execution.

## A. Original WorkBuddy science-v4 producer outcomes

| Track | Original run status | CPU sec | Wall sec | Interpretation |
|---|---|---:|---:|---|
| GENESIS | `PILOT_EXECUTION_FAILED` | 218.875 | 224.032 | Original rough finite-difference check failed; later exact derivative audit does not retroactively mark original as passed |
| NAO V3 | `PILOT_COMPUTATION_VERIFIED` | 347.28125 | 353.047 | Numeric computation checked; **mechanism and predictive success not established** |
| Anti-Slowing | `PILOT_EXECUTION_FAILED` | 240.609375 | 247.859 | Exit 124 / memory-budget failure; later streaming-hash audit not a new qualifying producer |
| signed-Sokal | `PILOT_COMPUTATION_VERIFIED` | 21.203125 | 22.25 | Computation verification, **not a theorem or novelty certificate** |

Original four child jobs totaled 827.96875 CPU seconds, with controller CPU accounted separately. These *original statuses must not be overwritten by subsequent recovery checks*.

## B. Track-specific results

### GENESIS — `STOP_CURRENT_PLATFORM_PROMOTION_REVISE_MINIMUM_FEASIBILITY`

New v4 residual students (depths 2/4/8, six shared-seed clusters) could not provide reliable trained minima across depths:

| Depth | N | Gradient-qualified | Clearly negative curvature | Historical `valid_minima` |
|---|---:|---:|---:|---:|
| 2 | 6 | 6 | 3 | 3 |
| 4 | 6 | 2 | 5 | 1 |
| 8 | 6 | 1 | 6 | 0 |

Deep endpoints are not fit for a cross-depth intrinsic plateau test. Subsequent exact-Hessian/Jacobian recomputation passed in existing 18 models / 90 directions, **but does not repair stationarity, local-minimum qualification or build the missing valid null envelope**.

The alternative GENESIS v3r15 increases objective-call budget in a proposed 36-fit comparison. It has **10/10 deterministic qualification checks**, **0 new scientific fits**, mismatched hashes for two base Python runtime anchors, and missing present-version authorization/approval/resource-binding. It is **not a launched confirmatory experiment**.

### NAO V3 — `STOP_CURRENT_MECHANISM_PROMOTION`

New 18-trajectory synthetic study (six seed clusters × SGD/SGDM/Adam; seven prediction windows per trajectory) yielded median forecast gain over strongest baseline:

| Optimizer | Median forecast gain |
|---|---:|
| SGD | -3.5276% |
| SGDM | -10.3886% |
| Adam | -40.0843% |

Only one Adam seed cleared the +20% descriptive threshold; four SGD intervention-based relative gains were **undefined**, not zero, because the best baseline error was zero.

The mandatory multiscale null/surrogate family qualified **0/25,074 proposals** and **0/126 complete windows**. This is **failure of the null-generation qualification procedure**, not rejection of a null hypothesis or evidence of a novel mechanism.

### Anti-Slowing — `REVISE_SCIENTIFIC_PIPELINE_BEFORE_ANY_CALIBRATION`

A new eight-dimensional nonlinear response benchmark used six independent seed clusters for the registered main effect; **0/6 met both** predeclared gain and localization thresholds. All six localization contrasts were negative. Per-family calibration saw zero false promotions in six seeds, but the unconditional one-sided 95% upper bound is approximately **0.393**, far above 0.05. The Q2 generating-family panel qualified **0/6** seed clusters, precluding claimed error-control validation. Q4H history-aware engineering repairs passed deterministic checks but no new full end-to-end scientific calibration was run.

### signed-Sokal — `STOP_CURRENT_CLAIM` (for the pre-registered finite family)

- An explicit two-state boundary counterexample targets a **strong, specifically formulated** universal first-crossing claim; this does not refute an unseen, more qualified theorem.
- A new symmetric three-state family (27 chains × three c constants = 81 exact cases) yielded **0** examples with ≥2 exact boundary lags, **0** re-entry, and **0** non-crossing cases; independent arithmetic readback agreed 81/81.
- This excludes witnesses **only within the registered finite family**. It neither proves a universal absence nor establishes a new theorem.

## C. Old research ≠ new confirmation

Older GENESIS ReLU sparse-phase and DLN plateau observations, historical signed-Sokal R1–R7 claims, Anti-Slowing summer data and NAO ResNet G1 results remain archived **historical claims at their original scope**. None is automatically upgraded by these October 2026 four-track engineering or pilot checks.

## D. Resource and archive honesty

The source report states 1,984 original project files / 2,139,736,566 bytes had been packaged in a separate existing archive with MANIFEST.csv and SHA256 verification. **That payload is not present here.** Exact local archive hashes have not been independently verified in this repository.

No original scientific pipeline was restarted as part of this GitHub organization.  
No new research authorization, calibration, theorem certification or statistical approval is implied.
