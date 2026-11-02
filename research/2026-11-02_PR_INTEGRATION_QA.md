# PR integration & scientific QA — 2026-11-02

**Repository:** `lyxxx708/hessian-landscape`. **Scope:** GitHub-connected PR/source/doc review and GitHub Actions verification. **Important:** this maintainer session did NOT independently rerun the large numerical experiments or re-download the entire 2.09 GB raw archive.

## PR disposition (reviewed 2026-11-02)

| PR | Disposition | Decision boundary |
| --- | --- | --- |
| #1 | Previously merged | Historical Phase I–VII documentary research baseline |
| #2 | Draft/open, **superseded by #5** | Do not merge old structure; original Regime Mixing handoff is `NOT_IMPORTED`, not backed up |
| #3 | Draft/open, **superseded by #5** | Historical Anti-Slowing/NAO source transcriptions already integrated into governed tree |
| #4 | **Merged**, merge `e52231de` | Release archive provenance and verifier; NOT science replication |
| #5 | Previously merged | Canonical portfolio/history/catalog/workbuddy layout |
| #6 | **Merged**, merge `faf4e972` | NEW independent synthetic 12-layer DLN baseline, not original 2025 replay |
| #7 | **Merged**, merge `48f0aad1` | Research decision/protocol; fixed GGN PSD vs damped SPD gate and Codex review thread |
| #8 | **Merged**, merge `993119d9` | Synthetic directional-utility diagnostic and conditional investment contract |
| #9 | **Merged**, merge `153d4949` | Original Claude gauge source/logs with independent caveats, not theory certification |

PR #2 was converted to draft and both #2/#3 received source-preserving supersession comments. Their historical branches were **not deleted or closed**.

## Evidence classes and checked findings

**#4: Archive existence & integrity boundary.** Public GitHub Release [archive-20261026](https://github.com/lyxxx708/hessian-landscape/releases/tag/archive-20261026) exposes 63 uploaded assets with API-reported sizes totaling 2,089,046,079 bytes. The archive author recorded a complete re-download, outer SHA-256 `290b84297c0ef2263ba40270f112358e1322a49bbcd17bffd749bd80757ebf1f`, and 2,024/2,024 member checks. This QA checked metadata and verifier source, **not** the complete archive byte sequence. The report blob at `archive/workbuddy-fourline-2026-10-26/EXPERIMENT_REPORT.md` duplicates the canonical report at `research/workbuddy/2026-10-26/EXPERIMENT_REPORT.md` exactly (Git blob `9d6ce23fd3fdb04c2fef3c105b722a363ec13ab4`); treat the latter as canonical.

**#6: 12-layer DLN synthetic P0.** Reported six new runs (3 seeds × initial/zero residual) use (L=12,d=10,N=32,\lambda=10^{-3}). At zero residual, (H=GGN), `rank(J)=100`, and every nonzero-distance normalized inverse block-RMS bin is approximately 0.09050–0.09057, with 8.265%–8.277% off-diagonal energy. At the separate nonzero-residual loss, the exact Hessian has 597–606 materially negative modes and inverse off-diagonal energy of 85.4%–89.6%. At fixed nonzero-residual curvature, changing damping from 0.001 to 2.0 reduces off-diagonal inverse energy from 86.62% to 1.80%. These conditions are different target losses, **not** a time-ordered training phase transition. P0 script, tests, CSVs and damping sweeps were source-reviewed; prior branch CI passed. No new full-scale rerun in this QA.

**Historical contradiction remains unresolved.** For 12 equal layer blocks, if all (C(k)=RMS(k)/RMS(0)\le0.12), then `OffDiagMass <= 11*(.12)^2/(1+11*(.12)^2) = 0.1367403`. The historical pair `0.09–0.12` and `39% offdiag` cannot describe one matrix under one such metric. The **original 2025** Phase IV/V raw matrix, run IDs and checkpoint are still not recovered, even though the **2026 four-line WorkBuddy** archive exists.

**#8: gradient-conditioned value.** At three synthetic orthogonal DLN initialization seeds, reported GGN cross-layer Frobenius energy mass is 91.667% while best scalar-ray-corrected layerwise quadratic utility `eta=0.999737/0.999503/0.999610`. This is a strong counterexample to interpreting block energy as optimizer utility. The `alpha*` used is a **post-hoc oracle** in one local SPD quadratic model; no online algorithm, actual training speedup, independent-seed generalization or main-conference novelty is demonstrated. The implementation/formula and synthetic CSV were source-reviewed.

**#9: gauge reimplementation.** Original report/code/logs are preserved, with independent 2026-10-26 and 2026-11-02 audit notes. Their previously reported 3/3 new regression tests and 5/5 experiment script exits are not 2025 scientific reproduction. Material limits remain: finite-λ inverse contains non-null modes, negative exact-H curvature is not wholly proven gauge-induced, near-zero eigenvalue counts require tolerance, damping regimes require correct spectral windows, and `F_S` needs a defined estimand. Experiments B–E need SciPy beyond the root NumPy requirements.

## Validated versus unvalidated

- **Observed here:** GitHub PR metadata, source file contents, GitHub CI success for integration heads and main through the #4 merge, Release asset metadata, mathematical consistency review and conservative source QA comments.
- **Reported from previous executed experiments:** new P0 numerical values, directional-utility pilot, Claude script reruns, and downloaded archive SHA-256 checks.
- **Not established:** original 2025 Phase V numerical replication, universal/non-decaying depth-law theorem, gauge-only complete mechanism, real-train optimizer speedup, G1–G4 confirmatory validation, or peer-reviewed novelty.

## Next scientific Go/No-Go

First audit *task-relevant* performance at fixed gradient/checkpoint: for (Q=GGN+\lambda I\succ0) and (D=blockdiag(Q)), compare full (p_*=-Q^{-1}g) to best-scaled layerwise (p_D=-D^{-1}g); distinguish `offdiag energy`, `directional regret`, cost and genuine training utility. The #7 and #8 experiment contracts are **proposals and resource gates**, not already-run proof. Preserve all failed cases and split held-out evaluation at the independent seed/architecture level. No optimizer/CUDA build-out on the basis of curvature heatmaps alone.

**Repository authority:** dated integration notes supplement, and do not erase, historical reports. Any scientific promotion requires original/reimplementation code, exact configs and checkpoint/run IDs, full numerical error and conditioning checks, and independent executed verification.
