# v2 FP32 numeric qualification audit: protocol

Written 2026-11-04, before any audit result was computed. Owner priority P0.

## Question

Do v2 results labelled NUMERIC_VALID, computed in FP32 with the frozen solver, agree with an independent FP64 computation on the same frozen checkpoint, batch, group schema and damping?

## Rules

- Read-only for `runs/genesis_full_v2`: the SQLite queue is opened `mode=ro`; checkpoints and receipts are only read. Output goes only to `evidence/v2_numeric_audit/`.
- CPU only and 3 threads, so no GPU worker is started and the GPU is not touched.
- v2 labels and receipts are never changed. Audit classes are a separate disclosure layer.
- Scope is every `COMPLETE` measurement with a NUMERIC_VALID utility, both schemas, all γ. There is no sampling and no screening by gradient norm, because gradient norm alone may not predict error. Rows finished later are added by rerunning, keyed by job id.
- NUMERIC_UNRESOLVED rows are out of scope: they claim no value, and FP64 values must not fill them.

## Comparison for each job

1. **Reference:** frozen `evaluate_utility` from the frozen source tree, with `analysis_dtype=float64`, `preconditioner_probes=0`, and the receipt's recorded `lambda_absolute`. Other solver settings stay frozen.
2. **Independent check of the reference:** dense FP64 solve, where parameters ≤ `dense_limit` (2048). This has no CG in it.
3. **Recorded v2 values:** `delta`, `E_task`, `E_val`, `cheap_rho`, `F_star`, `gradient_norm`, `task_status` from the receipt.
4. **Gradient, per state:** on the same CPU, ||g32−g64||/||g64||, cosine, and FP32 vs FP64 norm, plus recorded GPU norm vs FP64 norm. A CPU FP32 gradient is a proxy for the GPU one, because rounding can differ, and is labelled so.

Group-level checks: agreement by setting, checkpoint and γ, with the audit recomputing the same comparison at `checkpoint_index` level.

## Classes (fixed now, from frozen protocol values)

Let D = max(|Δδ|, |ΔE_task|, |ΔE_val|) between recorded v2 and the FP64 reference.

| Class | Condition | Meaning |
|---|---|---|
| `AGREE` | D ≤ 0.005 | Within the protocol's own `delta_stability` |
| `DIVERGENT` | 0.005 < D ≤ 0.01 | Exceeds numeric tolerance |
| `MATERIAL` | D > 0.01 | Exceeds `delta_lower`, large enough to affect a scientific threshold |
| `STATUS_CHANGE` | `status` or `task_status` differs from the reference | Any D |
| `UNAUDITABLE` | The reference is not NUMERIC_VALID, or disagrees with dense by > 0.005 | The audit cannot judge this row |

Secondary, descriptive only: relative differences, gradient error, and whether `delta_stability` or gradient norm would have predicted the error. Any predictor found here is reported as exploratory and does not reclassify any row.

An `AGREE` row is "consistent with FP64 on this state", not a high-precision validation of the study's result.

## Limits

- CPU FP64 vs GPU FP32 also compares devices. A difference could arise from either, and the row is still disclosed.
- Only DLN results exist today. The audit says nothing about families not yet measured.
- This audit does not revisit the frozen analysis plan. How flagged rows are treated in S1/S2 inference is reported as sensitivity analysis, with the primary v2 result unchanged.
