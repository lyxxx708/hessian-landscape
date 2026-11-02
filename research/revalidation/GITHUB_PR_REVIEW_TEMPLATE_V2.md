# GENESIS v2 — template for the FINAL Codex GitHub review PR

> This is an empty *future evidence template*, NOT a report of completed GPU experiments. Codex must fill each section with real file/commit/receipt references, leave failures visible and never mark a box without a command/log proof.

## Identity & authorization

- Repository / base PR / head execution branch:
- Source Git SHA and original source-manifest SHA:
- Frozen protocol SHA, data-split SHA, seed-manifest SHA, Python/PyTorch/CUDA/driver:
- Reviewer/independent numerical verification mechanism:
- Local GPU: RTX 4070 Ti 12GB / native Windows / E:-first artifact root:
- Public-release data licence and sensitive-file scan result:
- Paid cloud/API used? **Must be NO**:
- Raw matrices/datasets/checkpoints/SQLite/personal paths included in public PR? **Must be NO**:
- Automatic main merge requested? **Must be NO**:

## Executed acceptance gates (not inherited from Linux CPU CI)

| Gate | Planned | Actually executed | PASS/FAIL/NOT_RUN | Receipt path + SHA |
| --- | ---: | ---: | --- | --- |
| Exact shipped manifest | 143 indexed blobs | | | |
| CPU package tests | 80 historical passed, 1 CUDA skip | | | |
| Legacy repository regressions | all existing tests | | | |
| Native Windows CUDA doctor | one RTX 4070 Ti | | | |
| G0 numerical qualification | MSE+CE GGN, HVP, dense vs CG/sketch, fixed buffers | | | |
| Frozen source/seed/protocol | all immutable | | | |
| S1 real training | 130 | | | |
| S2 new-seed confirmation | 96 | | | |
| S3 conditional trial | PASS only if U/P gate passes; otherwise S3_NO_GO | | | |
| Independent raw-data recomputation | representative all-family samples | | | |
| Report + figure SHA manifest | final after generation | | | |

## Full scientific evidence inventory

- S1: 26 settings ×5 independent seed clusters; total COMPLETE / NUMERIC_INVALID / EXECUTION_FAILED / missing. Not 26×5×4 checkpoints×3 λ independent n.
- S2: 6 anchors ×16 NEW independent seeds; total COMPLETE / NUMERIC_INVALID / EXECUTION_FAILED / missing; leakage inspection and source hash.
- Per-model family, width/depth, loss/task and dataset version: all predeclared full data counts and invalid causes.
- Curvature object and normalization: squared loss and CE logit output-Hessian GGN vs exact H (NOT empirical Fisher).
- Full-vs-precise-layerwise direction: true linear residuals, absolute and relative λ, oracle alpha_Q, separate CE-Hessian-weighted train alpha_task, validation E_val with train scale, task utility eta/Delta and nonlinear line-search.
- Structure S: every layer-distance RMS bin, raw and interaction-corrected R, full probe uncertainty, near-pole and gauge/spectral/null controls, depth scaling and grouping dependence.
- Mechanism M: exact-H residual, nullspace/gauge contrasts, matched spectral random and ordering nulls, near-pole qualification, proposed causal interpretation limits.
- Prediction/Optimization P: independent S2 AUC/MAE and baselines, true S3 optimizer cost/time-to-target if gated; no free Full GN baseline.

## Scientific conclusions (fill all four, including negatives)

| Claim | Qualified evidence status | Independent N / uncertainty | Strongest competing explanation | Disconfirming/null cases | Raw evidence pointer + SHA |
| --- | --- | --- | --- | --- | --- |
| S: Structure | | | | | |
| M: Mechanism | | | | | |
| U: Task utility | | | | | |
| P: Prediction/online optimizer | | | | | |

Overall: COMPLETE_POSITIVE / COMPLETE_MIXED / COMPLETE_NEGATIVE / INCOMPLETE_BLOCKED_EVIDENCE. Explicitly justify outcome against the frozen thresholds and ineligible fractions. A failed optimizer gate is NOT an invitation to cherry-pick new seeds.

## Reviewer checks before merge consideration

- [ ] All new source files and imported manifest hashes pass; git diff --check clean.
- [ ] Real Windows CUDA G0 actually executed with device/driver/VRAM proof.
- [ ] Both new v2 and original repository software tests executed; failing/skipped named.
- [ ] No unreviewed alteration of after-freeze scientific config/analysis/seeds; versioned replacements documented.
- [ ] 130/96 sample inventory complete or all exceptions explicitly documented; no missingness-suppression.
- [ ] Source/data/checkpoint hashes and independent verifier receipts trace every result.
- [ ] Confidence intervals use seed clusters rather than pseudoreplicate λ/checkpoint/probes.
- [ ] All numerical invalid, negative and adverse results included without “approved PASS” from historical reports.
- [ ] Source/IP/data licence, secret/privacy and public release review passed.
- [ ] Large raw artifacts remain private on E: and are not uploaded to a public GitHub repository.
- [ ] Existing historical research files unchanged; main not auto-merged.

## Honest limits

Original 2025 Phase IV/V matrices/checkpoints are missing, and their incompatible report values are not new experimental targets. A 2026 synthetic P0 platform is a correctness control, not a universal physical law. CPU CI alone and passing software tests cannot certify a scientific discovery or actual training speedup.
