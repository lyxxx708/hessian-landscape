# Project GENESIS — Hessian Landscape

Research archive for the **curvature structure / damped inverse Hessian / long-range plateau** line of Project GENESIS.

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

## Provenance and caution

- Figures and reported numeric claims come from user-supplied textual reports, **not** checked original experiment logs.
- PASS / FAIL / APPROVED FAIL labels inside historical reports are **historical team judgments**. They do not imply fresh independent validation.
- Do not cite this repository as proof of reproduced scientific results until original inputs, environment, execution records, plots, and checkpoints are attached and independently checked.
- For completeness, see archive/ASSET_MANIFEST.md. A missing source file is never silently recreated and labeled original.

## Proposed scientific thesis (candidate, not theorem)

Damped inverse curvature of a deep linear parameterization may contain non-decaying layer-separated energy arising from shared spectral/nullspace structure. Whether this is a universal or even reproducible quantitative mechanism depends on the matrix object, rank, damping, normalization and parameterization; it remains under active audit.

## Repository policy

New reference code is labeled **REIMPLEMENTATION**; source experimental code retains original file names and checksums when supplied. No unverified raw logs or screenshots are synthesized. Public repository: review all future uploads for private data before publishing.
