# Research archive and governance map

This index separates the existing GENESIS research archive from the integrated cross-project materials. The repository's top-level [research status](../RESEARCH_STATUS.md) is the current status summary; [AGENTS.md](../AGENTS.md) defines contribution and evidence-handling rules.

## Directory responsibilities

| Directory | Contents | Authority |
| --- | --- | --- |
| [`portfolio/`](portfolio/README.md) | Cross-project relationships, claim ledger, source registry, status, missing-source register, and reproducibility contract | Current documentary status index; not raw evidence |
| [`history/`](history/ANTI_SLOWING_AND_NAO_HISTORY_20261026.md) | Historical source transcriptions and clearly labeled explanatory histories | Transcriptions preserve the text as received; syntheses do not overwrite them |
| [`catalog/`](catalog/SOURCE_CATALOG_20261026.md) | File/source mapping, claim register, and bulk-receipt checklist | Provenance and custody tracking; not experimental evidence |
| [`assessment/`](assessment/2026-10-26_VALUE_ASSESSMENT_AND_RESEARCH_PROGRAM.md) | Dated value assessment, analytic baseline (gauge projector), pre-registered predictions, next research program | ASSESSMENT backed by NEW_REIMPLEMENTATION; does not alter historical records |
| [`workbuddy/2026-10-26/`](workbuddy/2026-10-26/README.md) | The single canonical WorkBuddy report copy and its inventory, source index, state note, and transfer runbook | Committed report blob verified; original package and raw assets absent |
| [`../docs/`](../docs/SCIENTIFIC_STATE.md) and [`../archive/`](../archive/ASSET_MANIFEST.md) | Existing GENESIS science notes, mathematics, asset inventory, and measurements | Retained from the merged #1 archive |

## Evidence and custody rules

- A source transcription, status summary, calculation, qualification, adjudication, and independent reproduction are distinct evidence classes. The report and its derived indexes do not establish independent reproduction.
- The WorkBuddy report exists at one canonical path: [`EXPERIMENT_REPORT.md`](workbuddy/2026-10-26/EXPERIMENT_REPORT.md). Other documents link to it; they do not carry another report copy.
- The reported 1,984-file / 2,139,736,566-byte source package, raw records, source code, and figures are not present. No source hash or package verification is inferred from the report's Git blob hash.
- Regime Mixing handoff remains `NOT_IMPORTED` / `POINTER_ONLY_UNTRANSFERABLE`.
- Keep source texts intact. Record corrections or changed interpretations in a dated status or audit document with provenance, without rewriting historical conclusions.
- Do not promote failed, unrun, or documentary-only work to a verified scientific result. Do not upload raw data to this public repository without explicit authorization and completed privacy, rights, credential, and holdout review.
