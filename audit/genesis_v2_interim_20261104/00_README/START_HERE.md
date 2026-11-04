# GENESIS v2 interim audit snapshot: start here

Snapshot time: 2026-11-04 20:11 (UTC+8). This is an evidence hand-off for an independent audit, not a result report. The packager draws no scientific conclusion. The experiment was **still running** and had finished only part of Stage S1.

## What GENESIS studies

GENESIS v2 asks four separate questions about the layer-wise structure of inverse curvature in neural networks, using the damped Gauss-Newton matrix `Q = G + λI` on trained checkpoints:

| Line | Question (from `07_SOURCE/executed_source/docs/spec/GENESIS_v2_Blueprint_Design_Only.md`, section 1) |
|---|---|
| S, structure | Do natural training trajectories show a reproducible long-range layer structure in inverse curvature? |
| M, mechanism | Which mechanisms (Jacobian Gram, null space, gauge, depth, width, damping poles) explain it, against matched nulls? |
| U, utility | How much optimization value does full GGN keep over exact block-GGN after the best scalar step? Primary quantity `δ = 1 − F_B/F_*` (blueprint section 10). |
| P, prediction | Can cheap statistics predict U, and does that help in real training? P starts only after U shows a confirmable signal. |

Design: Stage S1, exploratory, 26 settings × 5 training seeds = 130 trajectories. Stage S2, confirmation, 6 anchors × 16 seeds = 96. Stage S3 is conditional. Each trajectory has 4 checkpoints, 3 relative dampings (0.001, 0.01, 0.1) and 2 parameter-grouping schemas (coarse, fine), giving 24 measurement jobs per trajectory. **The independent unit is the training seed**: checkpoints, dampings and schemas are repeated measures within a seed cluster.

## Where the run stood

Details in `00_README/CURRENT_STATE.md`. In short: S1 was running on one GPU worker; 41 of 130 trajectories were trained (all DLN), 980 measurements had terminal results, and **no adjudication, statistic, figure or report had been produced**. Hypotheses S, M, U and P are therefore NOT_YET_TESTED.

## What was found so far (observations about measurement quality, not hypothesis results)

1. **γ=0.001 solver failure.** 161 of 164 coarse measurements at the smallest damping ended `NUMERIC_UNRESOLVED` (`ORACLE_SOLVE_FAILED`). Diagnosis and the offline repair candidates are in `05_V21_QUALIFICATION/`.
2. **False-valid measurements.** An offline FP64 audit of 610 rows found 6 rows (3 distinct measurements, all one trajectory) labelled `NUMERIC_VALID` whose δ, E_task or E_val are off by more than 0.01, without any v2 check firing. `04_NUMERICAL_AUDIT/`.
3. **Data reproducibility.** Synthetic DLN data depend on the thread count; this very likely caused the one failed training job and 24 blocked jobs.
4. **Redundant work.** For DLN and MLP, coarse and fine are the same partition; 1,260 of 3,120 S1 jobs repeat a partition. Formal statistics filter to coarse.
5. **A reporting error of mine** (relative residual) was corrected; both versions are kept.

## What cannot be claimed

- Any S, M, U or P conclusion, for any family.
- Results for MLP, ResNet or Transformer in v2: they have no trained v2 trajectories or measurements yet.
- That `NUMERIC_VALID` labels are high-precision validated. Only 610 of 658 COMPLETE rows were audited, on DLN, with FP64 computed on CPU while v2 used GPU FP32.
- That structure metrics, mechanism records or predictor features were independently verified. They were not.
- That v2.1 solver variants are production-qualified: CPU only, no real CUDA G0, no trained non-DLN states.

## Where each claim's evidence is

`08_AUDIT_LEDGER/CLAIM_LEDGER.jsonl` (20 claims, each with file paths), `EVIDENCE_INDEX.jsonl` (every file with SHA-256), `OPEN_QUESTIONS.md`, `KNOWN_LIMITATIONS.md`, `MISSING_ARTIFACTS.md`.

## Recomputing statistics

- Job states: `02_EXECUTION/job_inventory/job_inventory.csv`; the SQLite snapshot (`02_EXECUTION/sqlite_snapshot/`) is the source of truth.
- Raw measurements: `03_SCIENTIFIC_DATA/raw_measurement_records/` (full receipts and probe artifacts, one JSON per line, ≤ 8.4 MB shards, `shard_index.json` lists SHA-256 and record ranges). Flat tables are derived from them by `06_ANALYSIS/analysis_scripts/export_science.py`.
- Formal analysis code: `07_SOURCE/executed_source/genesis_gpu/study/statistics.py` and `science/predictor.py`; these filter to `schema == 'coarse'`.
- Exact commands to check hashes: `09_MANIFEST/VERIFY_INSTRUCTIONS.md`.

## Only checkable on the author's machine (`LOCAL_EVIDENCE_REQUIRED`)

Model checkpoints and training states (hash-indexed in `02_EXECUTION/checkpoint_manifest/`), the MNIST/CIFAR/Shakespeare datasets (hashes in `01_PROTOCOL/protocol_lock/protocol-lock.json`), 66 `directions.safetensors` mechanism artifacts, the G0 reference arrays, per-step training logs, and the live run directory. See `09_MANIFEST/EXCLUSIONS.md`.
