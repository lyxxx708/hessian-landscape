# Source-copy provenance

| Candidate | Source | Import result |
|---|---|---|
| PR #2/#3 copies of `EXPERIMENT_REPORT.md` | Duplicate report transcription blobs | **EXCLUDED_DUPLICATE**. The integrated branch keeps PR #4's canonical report at `../workbuddy/2026-10-26/EXPERIMENT_REPORT.md`; its committed Git blob is verified as `9d6ce23fd3fdb04c2fef3c105b722a363ec13ab4`. This does not independently verify an inaccessible original file or raw-data package. |
| `REGIME_MIXING_THEORY_HANDOFF.md` | Library metadata pointer to historical theory handoff | **NOT_IMPORTED** / **POINTER_ONLY_UNTRANSFERABLE**. Authorized readable-text and raw-byte materialization were unavailable; no handoff text or placeholder is included. |

This is an incomplete archival package. The canonical experiment report refers to `figures/` links and `project/` source paths; none of these local files were uploaded here. No fabricated historical source was substituted.

Commit Git blob SHA values can validate committed copies, but must not be misrepresented as original local SHA256 checksums.
