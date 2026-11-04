# Questions for the independent auditor

These are the questions the packager could not close, framed so that each can be checked from files in this snapshot.

1. **Is the false-valid finding sound?** `04_NUMERICAL_AUDIT/fp32_vs_fp64/` uses thresholds fixed before results. Re-run `audit_fp32.py` (needs the local run directory) or recompute from `audit_rows.jsonl`: do the 6 MATERIAL rows follow from the stated classes? Is a CPU FP64 reference an adequate comparator for GPU FP32?
2. **Does the false-valid trajectory matter for S1 inference?** Rows enter the predictor as targets with checkpoint ≠ 0 (`predictor.py:32`) and U aggregates checkpoints 1–3 (`statistics.py:29`). The packager did not analyse this.
3. **Is NUMERIC_UNRESOLVED handled as the protocol says?** At γ=0.001 nearly all coarse measurements are unresolved (`03_SCIENTIFIC_DATA/numerical_eligibility/`). Does the frozen analysis still reach its pass conditions with one of three dampings missing? Does "at least two fixed λ levels" in the U gate still hold?
4. **Is the per-seed unit respected?** Check `statistics.py` bootstrap and the partial-conjunction logic against the claim that seeds, not checkpoints or dampings, are resampled. S1 `U PASS` was previously found impossible with n=5 (minimum sign-test p = 0.03125, partial conjunction minimum 0.0625); verify from `statistics.py` and note that the S1 verdict is hard-coded `CONFIRMATION_PENDING`.
5. **Do receipts match the executed code?** Compare `protocol-lock.json` source hashes with `07_SOURCE/executed_source/`, and the seven local edits in `07_SOURCE/local_changes/`.
6. **Is the failed training run a thread-dependence artifact?** See `04_NUMERICAL_AUDIT/reproducibility/ADDENDUM_01_thread_pinning.md` and `registry.py` `_synthetic`. Do other DLN trajectories depend on the thread count at train time, and would that affect reproducibility of the published seeds?
7. **Is the matched-cost CG baseline informative?** In offline tests it saturates after 9–14 matvecs with gain equal to F*; if so, "U over matched CG" has little room. See `05_V21_QUALIFICATION/mlp_resnet_transformer/`.
8. **Was the v2.1 qualification adequate for its decision?** CPU only, one preflight state per non-DLN family, DLN seeds 1 and 3. What additional evidence would the decision need?
9. **Structure and mechanism records.** They were not independently verified. Which of them can be recomputed from `raw_measurement_records/` without checkpoints?
10. **Anything in the diagnostic history that contradicts the ledger?** For example the earlier relative-residual error (kept in `04_NUMERICAL_AUDIT/residual_corrections/`).
