# Research status

## Latest project/software status — 2026-11-02

**DELIVERED SOURCE, SCIENTIFIC EXECUTION NOT YET ESTABLISHED.** PR #11's branch now contains [all 144 files of the executable v2 distribution](implementation/genesis-v2/README_GENESIS_V2.md) under an isolated directory, with a [15-stage runbook](research/revalidation/EXECUTION_PLAYBOOK_V2.md) and [local Codex Goal](research/revalidation/START_CODEX_GOAL_V2.md). Existing archival material is unchanged.

**Software evidence:** original Linux CPU engineering run 80 passed, one real-CUDA test skipped; GitHub CI rechecks source hashes and CPU tests separately. **Hardware/scientific evidence still missing:** user's native Windows RTX 4070 Ti G0, public data staging, S1=130 real training trajectories, S2=96 fresh trajectories, conditional S3, and independent scientific acceptance.

The older design/G0-only notes below are retained unchanged as dated historical snapshots. Neither source delivery nor a green CPU CI promotes a historical Hessian claim.

---

## Proposed epistemic reset — 2026-11-02 (draft, not executed)

**User decision:** Original 2025 Phase IV/V raw Hessian matrices and checkpoints are unavailable, and early reported plateau numbers are too unreliable to use as present scientific evidence. **Retire those numerical claims as a basis for new findings** (retain the immutable historical archive); stop treating archival recovery as a prerequisite for prospective research.

A [fresh large-scale revalidation protocol](research/revalidation/2026-11-02_FRESH_VALIDATION_PROTOCOL_V1.md) is now drafted with separate structure / mechanism / task-utility hypotheses and numerical G0 checks. **Status is DRAFT_NOT_FROZEN / NOT_EXECUTED**, not replication, confirmation, or authorization of GPU spending. A new empirical result must come from new code, real training checkpoints and held-out independent seed clusters.

---

## Current addendum — 2026-11-02 (Asia/Singapore)

**Integration complete for active new PRs:** #4, #6, #7, #8, and #9 are merged into `main` after source-level QA and successful branch CI. [Read the complete dated PR and science audit](research/2026-11-02_PR_INTEGRATION_QA.md).

- **Raw 2026 WorkBuddy package:** now publicly accessible as a [63-chunk GitHub Release](https://github.com/lyxxx708/hessian-landscape/releases/tag/archive-20261026), 2,089,046,079 compressed bytes. This review independently confirmed Release asset count and size, not complete re-download hashes; the author's separate full-archive verification is recorded under `archive/workbuddy-fourline-2026-10-26/`. It is *not* a validated replication of its scientific claims.
- **Fresh P0 synthetic research:** PR #6's new 12-layer DLN Hessian/GGN runner, tests and reports are committed. Its three-seed zero-residual plateau and nonzero-residual damping results are a newly authored synthetic baseline, **not** a replay of historical 2025 Phase IV/V.
- **Research decisions and gauge sources:** PRs #7/#8 provide decision-led protocols and a small synthetic directional-utility diagnostic; PR #9 preserves Claude's gauge reimplementation alongside independent scientific caveats. No new optimizer speedup or G1–G4 confirmatory result has been established.
- **Historical 2025 blocker remains:** original Phase IV/V Hessian matrices, run IDs and checkpoints not recovered; 0.09–0.12 RMS ratio and 39% off-diagonal energy cannot both hold under a single consistent 12-layer equal-block metric.
- **Legacy PRs #2/#3:** preserved as open drafts for provenance, superseded by merged #5; do not merge redundant old directory layouts.

**Historical record below:** the 2026-10-26 snapshot is retained unchanged. Its statement that the raw package was absent describes the Git tree and the search performed *at that time*; it does not supersede the later public Release identified above.

---

**Snapshot:** 2026-10-26 (Asia/Singapore)
**Overall state:** **DOCUMENTARY ARCHIVE INTEGRATED; SCIENTIFIC REPLICATION NOT ESTABLISHED**

## What is archived

- The merged GENESIS archive, including its mathematics, reference script, tests, and historical documents, is retained from `main`.
- The #2 project-lineage map, Claim Ledger, source registry, and reproducibility guidance are included under [`research/portfolio/`](research/portfolio/README.md).
- The #3 Anti-Slowing and NAO historical texts, source catalog, authority/history summaries, and claim register are retained under [`research/history/`](research/history/ANTI_SLOWING_AND_NAO_HISTORY_20261026.md) and [`research/catalog/`](research/catalog/SOURCE_CATALOG_20261026.md).
- The single canonical WorkBuddy report copy from #4 is [`EXPERIMENT_REPORT.md`](research/workbuddy/2026-10-26/EXPERIMENT_REPORT.md). Its committed Git blob was verified as `9d6ce23fd3fdb04c2fef3c105b722a363ec13ab4`. This verifies the committed blob only; it is not an independent verification of the inaccessible original report file or the source archive.

## Evidence and reproduction state

- The archived narrative and measurements are **documentary claims**. No new scientific experiment or independent scientific reproduction was performed for this integration.
- The reported original package of 1,984 files / 2,139,736,566 bytes, its ZIP, manifests, raw data, original code, logs, and referenced figures are **not present** in this repository.
- Regime Mixing handoff: **`NOT_IMPORTED` / `POINTER_ONLY_UNTRANSFERABLE`**. No readable source text or authorized raw-byte materialization was available.
- Existing Python unit tests cover the committed reference helper only: **4 tests passed locally** in an isolated Python 3.10 environment with `numpy 2.2.6`. A passing unit test does not validate the historical scientific claims.
- Historical negative results, failed qualifications, and unrun work retain their reported status. See [`research/portfolio/SCIENCE_STATUS_20261026.md`](research/portfolio/SCIENCE_STATUS_20261026.md).

## Public-repository risk boundary

This repository is public. This integration does not upload the 2.14 GB source package or raw experiment data. The report and source indexes include references to external records; reviewers should confirm public-release rights and access expectations before merging. No claim is made that all inaccessible original assets or third-party materials were independently audited.
