# Project GENESIS — Hessian Landscape

Research archive for the **curvature structure / damped inverse Hessian / long-range plateau** line of Project GENESIS.

**Fresh evidence reset (draft, 2026-11-02):** The original 2025 matrices and checkpoints are unavailable; old numeric plateau heights are not scientific targets. New hypotheses require fresh, independently auditable training checkpoints. See [large-scale revalidation draft](research/revalidation/2026-11-02_FRESH_VALIDATION_PROTOCOL_V1.md) and [G0 numerical core](scripts/fresh_revalidation_g0.py). **No large-scale experiment has been executed under this protocol.**

## Current integration snapshot (2026-11-02)

PRs #4, #6, #7, #8 and #9 have been reviewed and merged. The **2026 WorkBuddy source payload is available as a [public GitHub Release](https://github.com/lyxxx708/hessian-landscape/releases/tag/archive-20261026)** (63 chunks), and **new synthetic P0 Hessian/GGN and gauge reimplementations** plus scientific investment protocols now exist in the Git tree. The **original 2025 Phase IV/V DLN source matrices/checkpoints are still unrecovered**; no universal plateau, optimizer acceleration, or scientific replication claim has been promoted. [Current evidence and PR integration QA](research/2026-11-02_PR_INTEGRATION_QA.md) · [Current research status](RESEARCH_STATUS.md).

The 2026-10-26 state below is maintained as a dated historical record, not the latest availability inventory.

## Current state (2026-10-26)

**Archive assembled from user-provided reports and conversation context.** No original experiment scripts, full logs, raw eigenvectors, or plot binaries were located in the accessible project files, Library, Drive search, or the initially empty destination repository. Therefore **this archive is a documentary research package, NOT a reproduced experimental release.**

Three scientifically distinct objects must never be conflated: exact parameter Hessian H; generalized Gauss–Newton GGN = JᵀJ for squared loss with consistent scaling; and the damped inverse resolvent R(λ)=(H+λI)⁻¹ (or (GGN+λI)⁻¹). An indefinite Hessian cannot be interpreted as a Gaussian precision matrix, but its inverse is still mathematically defined whenever the shifted matrix is nonsingular.

**Next milestone:** Phase VII / Path B — audit a PSD GGN baseline and compare Chain / Global / Mixed geometry under fair nulls, with full rank, conditioning, and holdout tests.

## Navigation

- [Project status and evidence grades](docs/SCIENTIFIC_STATE.md)
- [Phase I–V chronology and reported measurements](docs/PHASES_I_V.md)
- [Long-range plateau deep investigation (Phase V/V-B)](docs/LONG_PLATEAU_V_VB.md)
- [Matrix decay and Rev4 arbitration](docs/MATRIX_DECAY_VI_REV4.md)
- [Mathematical definitions and exact caveats](docs/THEORY_NOTE.md)
- [Scientific claim ledger / critical audit discrepancies](docs/CLAIMS_AND_AUDIT.md)
- [Research directions and Phase VII execution contract](docs/NEXT_EXPERIMENTS.md)
- [Theory and numerical/engineering task registry](docs/PROMPT_TASK_REGISTRY.md)
- [SMPP optimizer engineering status](docs/SMPP_ENGINEERING.md)
- [Literature landscape](docs/LITERATURE_MAP.md)
- [Artifact inventory and missing originals](archive/ASSET_MANIFEST.md)
- [Transcribed numbers (NOT source data)](archive/REPORTED_MEASUREMENTS.csv)
- [Newly authored reference metric implementation](scripts/reference_block_metrics.py)
- [2026-10-26 value assessment, gauge-structure findings and research program (ASSESSMENT)](research/assessment/2026-10-26_VALUE_ASSESSMENT_AND_RESEARCH_PROGRAM.md)
- [DLN gauge-structure reimplementation and cross-platform logs (NEW_REIMPLEMENTATION)](reimplementation/dln_gauge/README.md)

## Provenance and caution

- Figures and reported numeric claims come from user-supplied textual reports, **not** checked original experiment logs.
- PASS / FAIL / APPROVED FAIL labels inside historical reports are **historical team judgments**. They do not imply fresh independent validation.
- Do not cite this repository as proof of reproduced scientific results until original inputs, environment, execution records, plots, and checkpoints are attached and independently checked.
- For completeness, see archive/ASSET_MANIFEST.md. A missing source file is never silently recreated and labeled original.

## Proposed scientific thesis (candidate, not theorem)

Damped inverse curvature of a deep linear parameterization may contain non-decaying layer-separated energy arising from shared spectral/nullspace structure. Whether this is a universal or even reproducible quantitative mechanism depends on the matrix object, rank, damping, normalization and parameterization; it remains under active audit.

## Repository policy

New reference code is labeled **REIMPLEMENTATION**; source experimental code retains original file names and checksums when supplied. No unverified raw logs or screenshots are synthesized. Public repository: review all future uploads for private data before publishing.

## Research status and archive index

See [RESEARCH_STATUS.md](RESEARCH_STATUS.md) for the current evidence boundaries and the [integrated documentary archive](research/README.md). The WorkBuddy report has one canonical copy at [EXPERIMENT_REPORT.md](research/workbuddy/2026-10-26/EXPERIMENT_REPORT.md); its committed Git blob is verified, while the inaccessible original data package is not independently verified or present here.

## Research investment decision (2026-10-26)

- [GENESIS: evidence-graded research value, nontrivial hypotheses, ICML/NeurIPS/ICLR positioning, and falsifiable experiment protocol](research/genesis/README.md) — analytical decision documents only; they do not upgrade the status of historical measurements or synthetic P0 results.
