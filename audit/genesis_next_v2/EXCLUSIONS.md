# Exclusions (what is not in this package, and why)

| Item | Reason |
|---|---|
| `local_inputs/*.npz` (exact FP32 analysis batches, 38 files, 464 KB, in `E:\GENESIS\runs\genesis_next_v2\local_inputs`) | Marked private by the NEXT v1/v2 design ("never publish"); derived from v2 data bundles. Their SHA-256 and the batch/operator identities are in each per-state JSON (`local_batch_archive.sha256`, `source_batch_identity`). Batches are regenerable from the v2 checkpoints + data via `rebuild_snapshot`. |
| v2 checkpoints / model weights, MNIST/CIFAR/Gutenberg data | Not to be uploaded; only SHAs are listed (`derived/checkpoint_and_data_sha_manifest.csv`). |
| `partials/*.json` (3.1 MB) | Incremental duplicates of the committed `results/per_state` records (written after each condition); the final records contain the same condition data. |
| v2 run database, worker files, audit snapshot bundle | Original GENESIS v2 evidence; read-only inputs; already in PR #15 / local audit snapshot `E:\GENESIS\handoff\audit_snapshot_20261104_201035`. |
| `__pycache__`, venv, `.tmp` files | Not evidence. |
| Credentials, tokens, SSH keys, personal files | None collected; a keyword scan found only the benign `budget_kind: tokens` strings in the lock. |
No failed, timed-out or unfavorable records were removed: there were no failed or unresolved NEXT v2 conditions, and the 126 SOURCE_NOT_READY conditions are listed in `EVIDENCE_INDEX.jsonl` and `results/EXPERIMENT_INVENTORY.csv`.
