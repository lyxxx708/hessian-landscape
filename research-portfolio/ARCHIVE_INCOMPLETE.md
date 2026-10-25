# Missing originals and unresolved archive-boundary

## What is actually preserved in this GitHub branch

- Existing **GENESIS** project documentary archive, historical phase narratives, recorded numerical claims and **newly authored** reference code (pre-existing in the destination repository).
- User-supplied 2026-10-26 cross-track research report copied as text.
- Historical Regime Mixing theory handoff copied as extracted text.
- New lineage, claim ledger, source registry and reproduction/import instructions.

## What is not preserved here

The 2026-10-26 report states that a separate WorkBuddy archive had been assembled containing **1,984 files totaling 2,139,736,566 bytes**, plus a manifest, checksums and verification output. **This GitHub branch does not include that ZIP or its full contents.** The report alone does not give a downloadable path or transfer capability to the actual 2.14 GB payload.

The following remain **SOURCE_MISSING_FROM_REPO**:
- Original GENESIS Phase V/V-B arrays (`results_phase_v.pkl`, `results_phase_v_b.pkl`), plots and source scripts; Phase VI Rev4 raw and Python auditing implementation where not explicitly committed.
- WorkBuddy `project/records/science_v4/` raw results, 2.1 GB original output; control ledgers, calibration and job records as files.
- 2026-10 WorkBuddy `MANIFEST.csv`, `MANIFEST.sha256`, ZIP-level checksum, `PACKAGE_VERIFICATION.json`, and all individual archive content hashes.
- Original NAO G1 sealed returns, signed-Sokal complete proof bundle, Anti-Slowing canonical SUPER V4 trajectories and estimator source.
- All figures referenced in the source report via `figures/*.svg` and most linked local tables.

## Import priority

**P0:** original ZIP + detached SHA256 + package verification JSON + MANIFEST.csv; independently compare SHA256 before expansion.  
**P1:** research protocols, environment locks, original producer terminal outputs, negative/error paths and rechecks, preserving source directory structure.  
**P2:** raw arrays, time series, model checkpoints, spectral data, plots and fitting/replay scripts; consider external object store or Git LFS depending on repository quotas.  
**P3:** modernized analysis notebooks/scripts, only in separately labeled `reimplementation/` paths.

## Integrity rules

1. Do not invent missing originals or give a generated replacement their historical names.
2. Never turn a failed producer into PASS on the basis of later reanalysis.
3. Reconcile file-level `path,size,sha256,source_run,protocol_version,artifact_role` before moving binary datasets.
4. Obtain explicit public-release clearance for account data, task transcripts, internal endpoints, research credentials, datasets with third-party restrictions and identifiable records.
5. Do not run the archived launchers automatically. Restore and independently qualify the environment first.
6. This file is a **gap register**, not a statement that sources have been deleted from the user's local WorkBuddy drive.
