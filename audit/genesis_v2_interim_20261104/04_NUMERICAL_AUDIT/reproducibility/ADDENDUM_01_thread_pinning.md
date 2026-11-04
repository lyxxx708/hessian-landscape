# Addendum 1 to AUDIT_PROTOCOL.md

Written 2026-11-04 after a 3-row smoke test and before the full audit. The classes and thresholds are unchanged.

**Change:** the audit runs with `OMP_NUM_THREADS=2`, `OPENBLAS_NUM_THREADS=2` and `--threads 2`, not 3 threads.

**Why:** `rebuild_snapshot` refused every DLN state at 3 threads with `Checkpoint/data SHA mismatch`. The synthetic DLN data's fingerprint depends on the thread count.

| Threads | Seed 0 fingerprint | Seed 1 fingerprint |
|---|---|---|
| 2 (OMP set by `genesis_env.ps1`) | a66f6d75b0d8 | a42eed57c235 (matches v2 receipt) |
| 3 | c3c1c8f713ed | be4606a46732 |
| 4 | a66f6d75b0d8 | a42eed57c235 |
| 8 | 446e30bd8810 | 4a3d7dd2f8b4 |
| OMP unset, torch default 10 | 5158cbd2df21 | 9ade01710a5f |

Setting: `dln_d4_w16_orthogonal_balanced_c1`. The integrity check was not bypassed: at 2 threads it passes.

**Consequence for the isolated run:** `s1-dln_d4_w16_orthogonal_balanced_c1-s00-44e78b87532803bf` has `data_sha` 5158cbd2df21 in all its checkpoints and resume metadata. That is the value for OMP unset. A relaunch with OMP=2 computes a66f6d75b0d8, and `Resume provenance mismatch` follows. So the mismatched key is `data_sha`, and the likely cause is the thread environment changing between launches. Earlier records called this root key unrecoverable; this replaces that statement. Nothing in the run or queue was changed, and the run stays isolated.
