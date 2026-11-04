# Project context

## Lineage

- GENESIS v2 was implemented by an earlier agent (Codex) as an installable package, `genesis_gpu`, from a design blueprint. Its package is PR #14 in this repository (a Draft, not merged). The executed commit is `12c240e1a22445b6fd6a50dfbe8552815de1fb71`, plus seven uncommitted local edits (below).
- A second agent (Claude Code) took the run over on 2026-11-03 without modifying the frozen protocol, seeds, thresholds or checkpoints, resumed the worker after a console-window outage, and did the diagnostics in `04_` and `05_`.
- An earlier 2025 project in this repository is not part of this study and is not restored here.

## Frozen protocol

- `protocol_sha` `b580695c152f85ac5ab79b3d070e5f660c28118d2cbe4a4c45c2c057b8a0c5c3`, in `01_PROTOCOL/protocol_lock/protocol-lock.json` (config, seed hash, G0 hash, dataset manifest hash, runtime ABI, 62-file source manifest).
- 62 of 62 source files in the lock match the working tree at snapshot time (`01_PROTOCOL/source_identity/source_manifest_vs_worktree.json`).
- No Python file in the executed tree was modified after the worker process started (checked by modification time).
- Config: `01_PROTOCOL/frozen_config/study_v2.yaml`. All 226 planned runs: `01_PROTOCOL/study_matrix/study_matrix_runs.jsonl`; seeds: `01_PROTOCOL/seed_manifest/seed-manifest.json`.

## Executed source versus GitHub

The executed tree is `07_SOURCE/executed_source/`. The seven uncommitted edits (`07_SOURCE/local_changes/v2_frozen_uncommitted.diff`, SHA-256 `436f90fb…158de`) are Windows and configuration fixes: `configs/study_v2.yaml`, `genesis_gpu/training/checkpoint.py`, `DELIVERY_MANIFEST.json` and four test files. PR #14's remote head therefore differs from what ran. The frozen lock was taken with these edits in place (the lock's manifest matches the working tree).

## Roles of other directories

- `04_NUMERICAL_AUDIT/`: read-only FP32 versus FP64 audit of v2 results, plus earlier diagnostics.
- `05_V21_QUALIFICATION/`: offline solver candidates for a possible v2.1. v2.1 is a separate version. It has no scientific results and is not mixed with v2 data.
- The v2 pipeline order is S1, S1 adjudication, S2, S2 adjudication, then conditional S3. Diagnostics do not gate it.

## Data

- DLN: synthetic teacher data generated at run time from the seed (thread-count dependent; see `04_NUMERICAL_AUDIT/reproducibility/`).
- MNIST, CIFAR-10: owner-licensed local copies. Shakespeare (Project Gutenberg eBook 2270): owner-authorised local research use; text training has not started.
- No raw dataset is in this package.
