# Verifying this package

## 1. File integrity

`FILE_MANIFEST_SHA256.csv` has `path,bytes,sha256,on_github` for every file except itself and `SNAPSHOT_METADATA.json`. From the package root:

```bash
python - <<'EOF'
import csv,hashlib,os
bad=0
for r in csv.DictReader(open('09_MANIFEST/FILE_MANIFEST_SHA256.csv',encoding='utf-8')):
    if r['on_github']!='yes' and not os.path.exists(r['path']):continue
    h=hashlib.sha256(open(r['path'],'rb').read()).hexdigest()
    if h!=r['sha256']:print('MISMATCH',r['path']);bad+=1
print('mismatches',bad)
EOF
```

The manifest's own hash and counts are in `SNAPSHOT_METADATA.json`.

## 2. Raw measurement shards

`03_SCIENTIFIC_DATA/raw_measurement_records/shard_index.json` lists every shard with SHA-256, record count and first/last job id. Each line of `receipts_*.jsonl` carries `receipt_path` and `receipt_sha256`: the SHA-256 of the original `result.json` on the author's drive. Shard lines re-serialize the receipt compactly, so they are not byte-identical to the original `result.json`; that hash can only be rechecked on the author's machine. The shard files themselves are checked by step 1, and every original receipt was verified against its recorded hash before export (`02_EXECUTION/job_inventory/receipt_verification.json`).

## 3. Queue

Open `02_EXECUTION/sqlite_snapshot/run_status_snapshot.sqlite` read-only (`sqlite3 file:...?mode=ro`). `job_inventory.jsonl` was exported from it by `06_ANALYSIS/analysis_scripts/export_inventory.py`. State counts must equal the table in `00_README/CURRENT_STATE.md`.

## 4. Source identity

`01_PROTOCOL/protocol_lock/protocol-lock.json` → `source.files[]` lists SHA-256 for 62 source files. Each must equal the SHA-256 of the same path under `07_SOURCE/executed_source/`. `01_PROTOCOL/source_identity/source_manifest_vs_worktree.json` records that check at snapshot time (62 of 62).

## 5. Regenerating derived files

With a Python environment holding the project's requirements (numpy, torch, safetensors) and the original run directory:

- `export_inventory.py <snapshot_dir> <run_root>`, then `export_science.py <snapshot_dir> <run_root> <frozen_source_dir>`, then `derive_summaries.py <snapshot_dir>`, then `build_ledger.py <snapshot_dir>`.
- Numerical audit: `04_NUMERICAL_AUDIT/fp32_vs_fp64/audit_fp32.py` needs checkpoints and the data (local only); run with `OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2` (see `ADDENDUM_01_thread_pinning.md`). Without them, recompute class counts from `audit_rows.jsonl`.

## 6. GitHub copy

The GitHub tree is the snapshot minus rows marked `on_github=no`. After cloning, step 1 must report zero mismatches for rows with `on_github=yes`.
