# Verification

1. Integrity: for every row of `FILE_MANIFEST_SHA256.csv` (path, bytes, sha256) recompute SHA-256 of the file; all must match (the manifest does not list itself).
2. Recompute claims from raw only: `python audit_tools/recompute_from_raw.py <package_dir>`. Expected at packaging:
   * C1 recomputed qualified 114 / 114 (thresholds read from `results/FOLLOWUP_LOCK.json`: operator/gradient cross-check 1e-6, full direction 1e-5, dense delta 1e-5)
   * C2 δ = 1 − F_block/F* mismatches 0; CG reaches Block gain in 114/114; matching-budget wall ratio median 0.044, max 0.153; median grid k 8
   * C3 null-energy fraction min 0.811, median 0.956; gradient null fraction max 1.1e-3; effective gain directions median 13.5
   * C4 v2 valid rows 76, median |error| 2.1e-7, 2 rows >1e-3; 38 v2-unresolved conditions FP64-valid
   * C5 negative validation gain: Block 93/114, full 91/114, over 19 independent seeds
   * C8 executed 38/80 states, 114/240 conditions
3. Cross-check tables: `results/SCIENTIFIC_RESULTS.csv`, `CG_COST_COMPARISON.csv` etc. are derived from `results/per_state/*.json` by `source_genesis_next_v2/analysis/make_deliverables.py`.
4. Re-execute a state (needs the v2 run root and checkpoints, not included): see `original_report/REPRODUCIBILITY.md`; environment in `environment/`.
5. Independence: group by `(setting_id, seed)`; 19 seeds. Do not treat conditions as independent.
