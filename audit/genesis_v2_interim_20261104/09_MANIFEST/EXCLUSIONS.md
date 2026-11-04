# Exclusions and redactions

The E: drive snapshot is complete except for the items below. The GitHub copy is the E: snapshot minus the section "Not on GitHub". Nothing was removed to hide a negative result: failed, blocked and unresolved jobs, the false-valid rows, the wrong residual report and the timeouts are all included.

## Not in the package at all (stay on the author's E: drive)

| Item | Why | Identification |
|---|---|---|
| Model checkpoints, training states, resume files (`checkpoints/**` except receipts) | Size and policy: no model weights are published | `02_EXECUTION/checkpoint_manifest/checkpoint_manifest.csv`: path, bytes, SHA-256, class (830 files, 9.0 MB) |
| MNIST, CIFAR-10 prepared data; Gutenberg text (Shakespeare First Folio, eBook 2270) | Third-party data; owner authorised local use only, no redistribution | dataset hashes in `01_PROTOCOL/protocol_lock/protocol-lock.json` |
| 66 `directions.safetensors` | Binary tensors from the mechanism tier | path, bytes, SHA-256 in `03_SCIENTIFIC_DATA/raw_measurement_records/shard_index.json` |
| G0 reference arrays `g0_*_reference.npz` and `audit/preflight_checkpoints/` (63 MB) | Binary | `audit/g0_receipt.json` (copied) lists them |
| Live `run_status.sqlite`, `-wal`, `-shm` | Direct copying of an active database is unsafe; the SQLite backup replaces it | `02_EXECUTION/sqlite_snapshot/` |
| `worker.json`, `heartbeat.json`, `control.json`, `resource_status.json`, `status.json` | Live control state with a lock token; not evidence | PID and times are quoted in `CURRENT_STATE.md` |
| Python bytecode (`__pycache__`) | Not source | none |

## In the E: snapshot but not on GitHub

| Item | Why | Identification |
|---|---|---|
| `02_EXECUTION/training_logs/` (50 files, 42 MB) | Per-step training loss logs; size. The 41 training receipts carry totals. | `09_MANIFEST/FILE_MANIFEST_SHA256.csv` lists each file with `on_github=no` |

## Redactions (content changed in the snapshot copy)

Three files had the local Windows account name in absolute paths (`C:\Users\<name>\...`). The name was replaced with `<user>` in the snapshot copy. Originals are unchanged in `E:\GENESIS\evidence\`. Original and redacted SHA-256 are in `09_MANIFEST/REDACTIONS.json`.

- `06_ANALYSIS/existing_reports/stage1-review/genesis-deps-install.log`
- `06_ANALYSIS/existing_reports/stage1-review/v2-tests.txt`
- `06_ANALYSIS/existing_reports/stage3-image-import/source_sha256_pre.json`

The git author name from the public repository history appears in `07_SOURCE/git_metadata/log15.txt` and was left as it is already public. Paths on `E:\GENESIS\...` are kept because receipts and the protocol lock hash them.

## Scan performed

Before packaging: text search of every non-SQLite file for API keys and tokens (`ghp_`, `gho_`, `github_pat`, `sk-`, `AKIA`), private-key headers, passwords, secrets, email addresses and `C:\Users`. Only the three redacted files matched private-path patterns; matches for "token" are language-model tokens (vocabulary, token budgets). The SQLite snapshot contains no account name. A second scan runs on the GitHub tree before push (see `VERIFY_INSTRUCTIONS.md`).
