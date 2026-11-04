# Current state at snapshot (2026-11-04 20:11, UTC+8)

Source: SQLite online backup of the live queue (`02_EXECUTION/sqlite_snapshot/`, taken with `Connection.backup` from a read-only connection; integrity check `ok`). Latest job update inside it: 20:11:03.

## Process

One GPU worker, PID 73000 (parent launcher PID 73948), started 2026-11-03 21:45:44, stage state `S1_RUNNING`, control `run`, protocol SHA as above. Checked read-only before the backup; the worker was not touched by this packaging.

## Queue (all stage S1; no S2 jobs exist yet)

| Kind | State | Count |
|---|---|---|
| train | COMPLETE | 41 |
| train | FAILED | 1 |
| train | PENDING | 88 |
| measure | COMPLETE | 658 |
| measure | NUMERIC_UNRESOLVED | 322 |
| measure | BLOCKED | 24 |
| measure | RUNNING | 1 |
| measure | PENDING | 2,115 |

Total 3,250 jobs (130 training + 3,120 measurement). Anything finished after 20:11 is not in this evidence version.

## Independent seed coverage (training seeds, per setting)

`06_ANALYSIS/existing_statistics/seed_coverage_by_setting.csv`. Seven DLN settings have all 5 seeds trained; `dln_d4_w16_orthogonal_balanced_c1` has 4 (one FAILED, 24 dependents BLOCKED); `dln_d16_w16_orthogonal_balanced_c1` has 2. No MLP, ResNet or Transformer trajectory has been trained.

## Results available

- 980 measurement receipts (658 COMPLETE, 322 NUMERIC_UNRESOLVED), all verified against their recorded SHA-256 (`02_EXECUTION/job_inventory/receipt_verification.json`: 1,021 of 1,021 receipts OK, including 41 training receipts).
- Coarse and fine rows are both present; for DLN they are identical in δ.
- 66 mechanism-direction tensors and 226 probe artifacts exist (probe artifacts are embedded; tensors are local only).

## Not produced

S1 adjudication, S2, S3, predictor fit, tables, figures, reports, `NUMERICAL_QA`, the independent verification receipt. See `06_ANALYSIS/existing_statistics/NOT_PRODUCED.md`.

## Not covered by the numerical audit

48 COMPLETE rows finished after the audit pass (`04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_coverage_vs_snapshot.json`). The audit was not rerun for this packaging.
