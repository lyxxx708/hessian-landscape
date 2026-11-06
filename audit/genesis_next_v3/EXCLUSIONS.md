# Exclusions

Not included in this package:

* v2 checkpoints, model weights and training receipts (`E:\GENESIS\runs\genesis_full_v2`). The package references them only by SHA-256: `model_sha`, `checkpoint_integrity_sha` and `training_receipt_sha256` in `run_v3/results/*.json`.
* v2 datasets and data arrays. Evaluation pools are regenerated in memory from the verified teacher; only their hashes and indices are recorded.
* The executed v2 source snapshot and the NEXT v2 package. They are pinned by per-file hashes in `run_v3/PROTOCOL_LOCK.json` and `results/*.json → inputs`.
* v2 S2 material, which was never read.

Included as recorded, without modification: the CPU-contention receipts in `run_v3/results/*.json → expB_timing_meta.contention`. These list the names of other busy processes on the workstation during timing (for example browser, chat and WSL processes).
