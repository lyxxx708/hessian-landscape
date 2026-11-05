# Reproducibility

* Source: `E:\GENESIS\worktrees\genesis-next-v2` (copy of NEXT v1 package + listed fixes; `PACKAGE_MANIFEST.json` regenerated, `verify-package` PASS 46 files). Tests: `python -B -m unittest discover -s tests` → 35 OK before freeze.
* Inputs (read-only): audit bundle `E:\GENESIS\handoff\audit_snapshot_20261104_201035` (manifest SHA in lock), executed v2 source (hash-verified), v2 protocol lock `f9f48682…`, v2 S1 checkpoints under `E:\GENESIS\runs\genesis_full_v2\checkpoints`. v2 PR commit `629032110fa51affc7f4e96cdb75f0c40070a9fe`.
* Lock: `FOLLOWUP_LOCK.json` (freeze_sha `0c881869d1eb17bb034a7fde8f0868ed7780b324a07b9b90ebe65d0a5c6305bf`) + `NEXT_V2_PROTOCOL_LOCK.json` (decisions and analysis plan written before measurement). First freeze `178898216f22…` was superseded after an infrastructure bug (child ownership check) before any science; archived in `_superseded_freeze1/`.
* Environment: venv `E:\GENESIS\venvs\hessian-landscape-v2`, torch 2.10.0+cu128, CPU FP64, `OMP_NUM_THREADS=2` (required: synthetic DLN data hash depends on it).
* Re-run: `$env:OMP_NUM_THREADS=2; $env:PYTHONPATH=<worktree>; python -B -m genesis_next drive --out E:\GENESIS\runs\genesis_next_v2 --device cpu --workers 4 --approve-compute` (committed results are never overwritten; only new source-ready states run). Tables: `python analysis\make_deliverables.py`.
* Each result JSON carries model/seed/checkpoint/provenance, training receipt SHA, source batch identity, v2 recorded values read-only, and per-condition reference class. Local batch archives (`local_inputs/*.npz`) are private; do not upload.
* Two dev pilots (`_dev_pilot*`, same state, earlier code) are development runs, not part of any table.
