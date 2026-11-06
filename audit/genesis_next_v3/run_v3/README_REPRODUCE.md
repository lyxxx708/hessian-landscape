# GENESIS NEXT v3 — reproduction

**Evidence class:** `POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION`. The study is DLN-only, runs on CPU in FP64, and uses no new training.

## Inputs (read-only, hash-verified at every state start)
* Executed v2 source: `E:\GENESIS\handoff\audit_snapshot_20261104_201035\07_SOURCE\executed_source`. Per-file hashes are in `PROTOCOL_LOCK.json → inputs.v2_source_files_sha256`.
* v2 run (checkpoints, training receipts, protocol lock `f9f48682…`): `E:\GENESIS\runs\genesis_full_v2`.
* NEXT v2 package `E:\GENESIS\worktrees\genesis-next-v2`. Its 13 files are verified against the NEXT v2 FOLLOWUP_LOCK. NEXT v2 results come from `E:\GENESIS\runs\genesis_next_v2\results`; their hashes are in `RUN_PLAN.json`.
* Design: `docs/design_input/` (from `GENESIS_NEXT_v3_design.zip`, sha256 `100a03c9…588c`; SHA256SUMS verified).

## Environment
* venv `E:\GENESIS\venvs\hessian-landscape-v2` (Python 3.11.14, torch 2.10.0+cu128, numpy 2.4.6), CPU only.
* `OMP/MKL/OPENBLAS_NUM_THREADS=2` and torch threads 2. The package sets these itself. The synthetic DLN data hash depends on the thread count, and every state re-verifies the dataset fingerprint against its training receipt.

## Steps (source: `E:\GENESIS\worktrees\genesis-next-v3`)
```
$py = 'E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe'; $env:PYTHONUTF8 = 1
& $py -B scripts\pilot_reproduce.py E:\GENESIS\runs\genesis_next_v3\qualification      # gate 2
& $py -B -m unittest tests.test_v3 > E:\GENESIS\runs\genesis_next_v3\qualification\TESTS.log 2>&1   # gate 3
& $py -B scripts\freeze.py E:\GENESIS\runs\genesis_next_v3                               # gate 4 (refuses to overwrite)
& $py -B scripts\drive.py E:\GENESIS\runs\genesis_next_v3                                # main: 38 states, fresh process each
& $py -B scripts\analyze.py E:\GENESIS\runs\genesis_next_v3                              # tables
& $py -B scripts\manifest.py E:\GENESIS\runs\genesis_next_v3 E:\GENESIS\evidence\genesis_next_v3
```
`run_state.py` refuses to run if any frozen code file has changed since `PROTOCOL_LOCK.json`. `drive.py` never re-runs a state whose result already exists, and it appends every exit, failure or timeout to `EXECUTION_LEDGER.jsonl`.

## What is deterministic and what is not
Directions, α grids, slopes, curvatures, labels and V4 results are deterministic given the inputs and the thread settings. Wall-clock timings are not: they depend on machine load. Contention samples are recorded with every repeat in `results/<state>.json → expB_timing_meta.contention`.

## Private material
The run writes no data arrays to disk; pools are regenerated in memory. Checkpoints and datasets stay in the v2 run. Do not publish `E:\GENESIS\runs\genesis_full_v2` contents.
