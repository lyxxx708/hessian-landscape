# GENESIS NEXT v2 — independent audit package

Exploratory, S1-only, DLN-only, CPU FP64 follow-up to GENESIS v2 (`POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION`). It is **not** a confirmation study and says nothing about MLP/ResNet/Transformer (no trained S1 checkpoints existed).

* What was measured: 38 of 80 planned states (4 DLN settings, 19 independent training seeds, checkpoints 1 and 3) × 3 dampings = **114 of 240 conditions**. The other 42 states / 126 conditions are `SOURCE_NOT_READY` and stay in the denominator (`derived/state_denominator_80.csv`).
* The 114 conditions are correlated measurements of 19 seeds — never treat them as 114 independent samples.
* Start: `CLAIM_LEDGER.jsonl` (8 claims, each with value, evidence files, method source) → `EVIDENCE_INDEX.jsonl` (one row per planned condition, with raw file and SHA) → `results/per_state/<state_id>.json` (raw per-state record: every comparator, CG receipts, geometry at 3 tolerances, Hessian diagnostics, gauge, E4 attribution).
* Recompute without trusting any summary: `python audit_tools/recompute_from_raw.py .` (numpy only) — see `VERIFY_INSTRUCTIONS.md`.
* Original reports are unmodified copies in `original_report/` (`SCIENTIFIC_VERDICT.md`, `FINAL_HANDOFF.md`, …). Packaging added only: indexes, `derived/`, `audit_tools/`, `environment/`, `tests/test_run_at_audit.log`.
* Source identity: `source_genesis_next_v2/` is the executed code (hashes in `FILE_MANIFEST_SHA256.csv`; freeze `0c881869d1eb17bb034a7fde8f0868ed7780b324a07b9b90ebe65d0a5c6305bf`; code digest in `results/FOLLOWUP_LOCK.json`). An earlier freeze `178898216f22…` (aborted by an infrastructure bug before any science) is in `superseded_freeze1/`; `dev_pilots_not_in_tables/` holds two development pilots of a single state that are not in any table.
* v1 → v2 changes and known defects: `NEXT_V2_PROTOCOL_LOCK.json` (`fixes_vs_v1_each_with_regression_test`), `v1_inheritance/`, `source_genesis_next_v2/tests/test_v2.py`.
* Relation to other PRs: original GENESIS v2 audit is PR #15 (head `629032110fa51affc7f4e96cdb75f0c40070a9fe`). The v2 worker, source, database and checkpoints were read-only inputs and are not part of this package.
* Known limitations: null-energy fraction is partly mechanical (∝ nullity/γ); single frozen batch per state; wall-clock timings are single-run on a shared CPU (4 parallel children plus the v2 worker); dense problems ≤2048 parameters; one setting has 4 seeds (v2 seed 0 failed); validation gains are ~1e-7 and mostly negative.
