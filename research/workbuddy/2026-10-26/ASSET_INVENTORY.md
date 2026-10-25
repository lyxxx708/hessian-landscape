# WorkBuddy source inventory and migration gaps

## Confirmed uploaded

| Asset | Location | State |
| --- | --- | --- |
| Canonical report copy from PR #4 | `EXPERIMENT_REPORT.md` | **Committed Git blob verified**, 38,095 bytes; original source file not independently checked in this task |
| Four-line research status index | `SCIENTIFIC_STATE.md` | New derivative summary, not raw evidence |
| Source citation map (S01–S19) | `SOURCE_INDEX.tsv` | Derived from report references only |
| Migration guidance | `TRANSFER_RUNBOOK.md` | Instructions, not an executed transfer |

## Described in report but NOT locally available to uploader

- Original project files: **1,984**, total **2,139,736,566 bytes**, across workspaces including `science_v4`, `science_v5` … `science_v9`, `records/science_v4` … `records/science_v9`, bridge/runner/docs/artifacts and research design source directories.
- Full package ZIP filename and its actual byte size: **unknown here**.
- `MANIFEST.csv` with SHA-256 per original file, and `MANIFEST.sha256` binding it: **not uploaded here**.
- `PACKAGE_VERIFICATION.json` and package-outer SHA-256: **not uploaded here**.
- Underlying `PLAN.json`, `BATCH_RESULT.json`, `FINAL_ASSESSMENT_20261022.json`, D0–D7 controls, Sokal `PLAN.json`, GENESIS v3r15 `PROTOCOL.md`, original code/arrays: **not uploaded here**.
- Existing GENESIS-only documentary archive in repository `docs/`, `archive/`, `scripts/`, `tests/`: **preserved, not replaced**.

## Explicitly excluded by source report

Frozen D008/D009, `data` root, confirmatory/holdout subtrees, accounts/credentials, Bridge private state, Git objects/databases, virtual environments and dependency caches. Do **not** traverse or include those paths from a manifest without authorization and a privacy review.

## Completion condition

A full-fidelity archive claim requires all of:

1. Authorized local operator has identified the original ZIP / source bytes and manifest.
2. Every selected source file appears exactly once in a manifest with path, byte size, and SHA-256.
3. Exclusions and public repository privacy checks are complete.
4. Package or chunks are actually uploaded in a downloadable, durable store, with explicit links.
5. A separate download-and-hash verification against the source manifest succeeds.
6. The finalized repository commit and any release/LFS objects are linked from a verifiable index.

**As of this commit, only the report and newly authored reference documents meet the upload condition.**
