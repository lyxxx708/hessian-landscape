# Missing or non-uploaded artifacts

`LOCAL_EVIDENCE_REQUIRED` means the artifact exists on the author's machine but is not in this package. Hashes and sizes are in the cited manifests.

| Artifact | Status | Where recorded |
|---|---|---|
| Model checkpoints and training states (41 trained trajectories: step 0, 1/3, 2/3, final, resume) | LOCAL_EVIDENCE_REQUIRED, weights not uploaded | `02_EXECUTION/checkpoint_manifest/checkpoint_manifest.csv` (path, bytes, SHA-256, class) |
| 66 `directions.safetensors` mechanism artifacts (3,075,408 bytes) | LOCAL_EVIDENCE_REQUIRED, binary | `03_SCIENTIFIC_DATA/raw_measurement_records/shard_index.json` (`binary_artifacts_not_embedded`) |
| MNIST, CIFAR-10 prepared data and Shakespeare text | LOCAL_EVIDENCE_REQUIRED, redistribution restricted | `01_PROTOCOL/protocol_lock/protocol-lock.json` (`datasets`) |
| G0 reference arrays (`g0_*_reference.npz`, `g0_block_estimator_reference.npz`) and one-step preflight checkpoints | LOCAL_EVIDENCE_REQUIRED, binary | `02_EXECUTION/failure_records/g0_receipt.json` (hashes) |
| Per-step training logs (`logs/s1-*.jsonl`, 42 MB) | Not uploaded for size; training receipts carry totals | `09_MANIFEST/EXCLUSIONS.md` |
| Live run directory and WAL | Not copied; the committed state is the SQLite backup | `02_EXECUTION/sqlite_snapshot/` |
| S1 and S2 adjudication, tables, figures, reports, QA | NOT_PRODUCED by the pipeline yet | `06_ANALYSIS/existing_statistics/NOT_PRODUCED.md` |
| Predictor training data and evaluation | NOT_PRODUCED; only a derived feature table exists | `03_SCIENTIFIC_DATA/prediction/` |
| Null controls (as separate files) | Not separate in v2; null records are inside structure records where present | `03_SCIENTIFIC_DATA/structure/structure_records.jsonl` |
| Final audit pass for the 48 later COMPLETE rows | NOT_RUN | `04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_coverage_vs_snapshot.json` |
| FP32/FP64 gradient comparison for MLP, ResNet, Transformer | Only the one-step preflight state, inside `frozen_*.jsonl` (`precision` fields) | `05_V21_QUALIFICATION/mlp_resnet_transformer/` |
| Transformer γ=0.1 and non-V3 variants at long caps | NOT_RUN (INCOMPLETE) | `05_V21_QUALIFICATION/go_no_go/GO_NO_GO_2026-11-04.md` |
| CUDA G0 for any v2.1 candidate; FP64 VRAM; GPU cost per GGNv | NOT_RUN | same |
| Independent code review of the v2 package | Not available (the package's own review is self-review) | `07_SOURCE/executed_source/docs/CODE_REVIEW.md` |
