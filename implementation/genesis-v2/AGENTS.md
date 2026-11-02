# GENESIS v2 — Codex execution instructions (implementation directory)

This directory is the **actual executable Python project**. It was imported as a byte-exact source distribution under a safe prefix; do not blindly copy it over the repository root's older G0/archival files.

## Required reading and authority

1. Root ../../AGENTS.md remains binding (no invented scientific evidence, no destructive history rewrite/automatic merge).
2. [../../research/revalidation/README.md](../../research/revalidation/README.md) is the up-to-date project execution index.
3. [../../research/revalidation/EXECUTION_PLAYBOOK_V2.md](../../research/revalidation/EXECUTION_PLAYBOOK_V2.md) contains the **mandatory 15-stage procedure** and precise commands.
4. [../../research/revalidation/START_CODEX_GOAL_V2.md](../../research/revalidation/START_CODEX_GOAL_V2.md) is the one-message Goal handoff.
5. README_GENESIS_V2.md, configs/study_v2.yaml, docs/spec/GENESIS_v2_Blueprint_Design_Only.md, docs/BLUEPRINT_TRACEABILITY.md and DELIVERY_MANIFEST.json define the implementation and science.
6. **Superseded:** earlier 2026 G0-only plans that tell you to reimplement the full platform from scratch or execute S2=80. Effective v2 is S1=130, **S2=96**, conditionally gated S3.

## Before running local GPU

- Work on a distinct Git branch/worktree on E:\GENESIS, preserve any existing user changes and historic files.
- Verify all 143 DELIVERY_MANIFEST entries, plus git commit identity. If any hash differs, fail closed.
- Run the real v2 test suite and the root repository's legacy unittest suite independently.
- Install CUDA PyTorch and venv to E: only; no C: bulk cache/output fallback. Do not alter global Windows profile, TEMP/pagefile, driver settings or unrelated local files.
- Verify native Windows RTX 4070 Ti CUDA G0 numerically before protocol freeze; **never treat GitHub Linux CPU CI or the archived 40-job micro-smoke as scientific validation**.
- Check dataset licenses, source and version hashes before download.

## Experiment invariants

- Freeze source/environment, training/data splits, solver thresholds, parameter ordering/grouping, seed manifest and analysis code before the first S1 scientific output.
- Four checkpoint fractions and three relative lambda values. Tier A/B full; C-base/C-deep exactly as precommitted. Do not select checkpoints/probes based on appealing results.
- S1 all 26×5=130 real training trajectories, including all failures. S2 all six×16=96 NEW seeds, even if S1 reports a negative/null; S3 only after U/P gates pass or explicitly S3_NO_GO.
- GGN and exact Hessian are distinct; CE GGN uses the output loss Hessian and correct valid-token normalization; empirical Fisher is not interchangeable. Precise block solves are not Adam diagonal/K-FAC. Alpha_Q and train-fitted alpha_task are distinct and validation must not refit the latter.
- Numeric invalid, ill-conditioned, near-pole, missing/failed probe, nonconverged CG and empty-gradient cases are **not zero-effect observations**. Record all failures with their denominator and hash.
- Independent statistical unit is the training seed, not checkpoint, lambda, probe or line-search row. No threshold/seed shopping or confirmation-data tuning.
- A long-running CUDA batch is managed by the local Python/SQLite process, not Codex chat. No per-seed/per-lambda/per-probe LLM calls. Bounded retries, one GPU worker and E:/thermal safeguards apply.

## Deliverables and GitHub boundaries

- Entire source, configs, tests and documentation are already on this PR branch. Do not fabricate an extra implementation just to generate commits.
- Raw data, matrices, NPZ, checkpoints, SQLite state, large logs and dataset bytes stay local to E: and hashed. **Only code corrections, tests and compact permission-safe evidence summaries** may be pushed to a new review branch.
- After full numerical/seed/statistical QA, write SCIENTIFIC_VERDICT.md, S_M_U_P_RESULTS.md, NUMERICAL_QA.md, NEGATIVE_RESULTS.md, REPRODUCTION.md, RESOURCE_ACCOUNTING.md and sanitized GITHUB_PR_SUMMARY.md, each actual result linked to raw artifact hashes.
- Submit an actual GitHub PR for new code or non-sensitive evidence; no automatic main merge, no history deletion. If no new code is needed, don't create fake commits.
- Every claimed test/experiment must have a real executed command and preserved exit/log evidence. A complete negative scientific result is valid; incomplete/blockers must be labeled INCOMPLETE_BLOCKED_EVIDENCE, never COMPLETE.

**Default next action:** Follow the runbook at Stage 0. Do not ask the owner to repeat the hardware/E-drive/Goal-mode instructions already specified here.
