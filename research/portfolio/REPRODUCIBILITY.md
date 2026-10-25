# Evidence-preserving restore and verification contract

This repository's cross-project index and copied texts are **not** an executable full-scale research release. Restore the separately reported original archive before claiming exact reproduction.

## Order of operations

1. Acquire the original **2026-10-26 WorkBuddy archive** together with its matching detached ZIP SHA256, `MANIFEST.csv`, `MANIFEST.sha256` and `PACKAGE_VERIFICATION.json`.
2. Hash the untouched ZIP and compare to the detached checksum; reject mismatch or missing manifest binding. Check that all ZIP entry paths are safe against path traversal before extracting.
3. Hash each extracted archive file against its recorded SHA256 and byte size; produce a machine-readable difference log. Do not silently normalize text or regenerate figures to match.
4. Separate historical science-v4 initial terminal outcomes from science-v5/v6/v7/v8/v9 follow-up audits and engineering qualifications.
5. Rebind source/environment hashes to the current runtime. The report warns of two Python base-runtime anchor mismatches in the v3r15 GENESIS qualification.
6. Read `project/PROJECT_CHARTER.md`, `project/RESEARCH_PROTOCOL.md`, `science_v4/PLAN.json`, `METHODS_ADDENDUM.md` and original terminal JSON **before** executing any program.
7. Review security/rights of all assets before committing to this **public** repository. Large private raw data should remain in a controlled object store with content hashes and a resolvable manifest.
8. Only after raw provenance is reconciled should independent scientific validators run; publish exact commands, environment locks, seeds, hashes, software versions and **failures**.

## Data model for later imports

Each row should contain:
```csv
source_id,relative_path,byte_size,sha256,source_run_id,protocol_version,artifact_role,access_class,ingest_state,validation_state
```

Recommended `ingest_state`: `MISSING`, `POINTER_ONLY`, `COPIED_UNVERIFIED`, `HASH_VERIFIED`.
Recommended `validation_state`: `NOT_RUN`, `CALCULATION_VERIFIED`, `QUALIFICATION_FAILED`, `SCIENTIFIC_ACCEPTED`, `SCIENTIFIC_REJECTED`.

Never map `CALCULATION_VERIFIED` to `SCIENTIFIC_ACCEPTED`.

## Statistical rules

- Seed cluster—not multiple overlapping windows, probes, horizons, or sibling depth instances—is the unit of independent replication unless independently justified.
- Undefined relative improvements (including zero denominators) remain missing/undefined, not zero or success.
- All registered mandatory null panels must qualify before null-hypothesis rejection or false-positive rates can be asserted.
- Keep pre-registration, subsequent amendments, held-out status and post hoc exploratory analysis separate.
- A finite exact counterexample refutes only a precisely stated universal proposition; a finite negative search does not prove general nonexistence.

The reports and historical engineering scripts may explain how to repeat analyses; the present commit **does not run them**.
