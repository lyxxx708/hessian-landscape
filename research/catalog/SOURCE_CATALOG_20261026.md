# Source catalog and receipt boundaries — 2026-10-26

## What this PR contains

| File in this repository | Source document as encountered | Type | Completeness | Evidence standing |
| --- | --- | --- | --- | --- |
| `research/history/sources/anti-slowing/2026-07-06_ANTI_SLOWING_SCIENTIFIC_MEMO.md` | Library markdown `941827e2-75c9-48d4-9719-bb99730ad047.md`, headed *τ_int(η) Anti-Slowing Project — Scientific Memo*, 2026-07-06 | `PARSED_TEXT_TRANSCRIPTION` | 136/136 logical lines read | Older claims; superseded where inconsistent with Aug audit |
| `research/history/sources/nao/2026-08-17_NAO_GENESIS_TAKEOVER_REPORT.md` | Library file `Pasted markdown(20260817-162201).md` | `PARSED_TEXT_TRANSCRIPTION` | 430/430 logical lines read | Historic authority reconstruction, not proof that source code was rerun here |
| `research/workbuddy/2026-10-26/EXPERIMENT_REPORT.md` | Canonical report copy retained from PR #4 | `CANONICAL_COMMITTED_REPORT` | 463 logical lines; committed Git blob `9d6ce23fd3fdb04c2fef3c105b722a363ec13ab4` verified | Secondary report of archived results, NOT actual raw experimental outputs; original source file and raw package not independently verified here |
| `research/history/PROGRAM_MAP_AND_AUTHORITY_20261026.md` and related docs | Reviewed summary derived from above and existing repository notes | `NEW_SYNTHESIS` | Complete as authored | Explanatory only |
| `research/catalog/CLAIM_REGISTER_20261026.csv` | Author-compiled scope/status of documented claims | `NEW_INDEX` | Complete as authored | Not a measured data table |

The Anti-Slowing and NAO transcriptions are created from **parsed file text**, *not raw original bytes*. Original newline encoding and bytes may differ. The report's Git blob identity authenticates **what is committed to GitHub**, not its inaccessible historical original. No original-file SHA256 has been independently verified in this task.

The historical source docs retain their internal labels and conclusions as written, including material later disproved or superseded. Read this catalog and the program map first. Images referenced in WorkBuddy Markdown, such as `figures/*.svg`, have **not** been acquired and will be missing when rendered; links to `project/records/...` in the body denote entries of a separate, not-uploaded archive.

## Original WorkBuddy package is NOT deposited here

The Oct report describes an archive with **1,984 project files totalling 2,139,736,566 bytes**, a `MANIFEST.csv`, `MANIFEST.sha256`, a verified ZIP and an external package SHA/receipt. **Neither this ZIP nor its member bytes, independent manifest, figures or table originals was present in the connected files read for this commit.** Consequently GitHub has only the report and indices, not a full reproducible dataset. Do not calculate an apparent SHA256 from the report text and attach it to the absent ZIP.

No original GENESIS `phase_v_log.json`, `results_phase_v*.pkl`, `genesis_rev4_final.pkl`, original figures, or executable training scripts were recovered for this PR. The pre-existing [GENESIS asset manifest](../../archive/ASSET_MANIFEST.md) remains operative.

## Receipt checklist for a later full archive

See [bulk-import checklist](BULK_ARCHIVE_IMPORT_CHECKLIST.md). A complete raw receipt must include the actual archive, file-level SHA256 manifest, outer package hash, generator/version and OS provenance, terminal Job outcomes, and a proof that named sources were not edited or recompressed without tracking. Binary files should remain unexecuted until audited.

## Public disclosure boundary

This repository is **public**. No passwords, authentication records, private Bridge database, personal identifying metadata, protected test sets or private holdout data were intentionally copied. Before importing the external archive, inspect each file for sensitive content and rights/redistribution restrictions. A report stating exclusions is not a substitute for scanning actual bytes.
