# GENESIS revalidation — current execution entrypoint (2026-11-02)

## PRIMARY: executable v2, not old draft

**Open PR #11, branch research/fresh-curvature-revalidation-v1-20261102.**

- **[Runnable complete source](../../implementation/genesis-v2/README_GENESIS_V2.md)** — isolated Python project, four model families, numerical core, GPU/Windows scripts, tests and archived CPU verification logs. Original source ZIP SHA-256: 71936c89c451e3c096a0b80d96876a73d312e01c08cd18f4dcdbb040920a5832.
- **[Codex Goal copy-paste](START_CODEX_GOAL_V2.md)** — assign the full local run without per-seed LLM calls.
- **[Full 15-stage runbook](EXECUTION_PLAYBOOK_V2.md)** — exact environment, dataset, G0, freeze, S1, S2, S3, QA, GitHub PR commands and failure handling.
- **[GitHub source-delivery receipt](GITHUB_DELIVERY_RECEIPT_V2.md)** — imported file counts, hashes, software-validation scope and remaining CUDA gates.
- **[v2 blueprint](../../implementation/genesis-v2/docs/spec/GENESIS_v2_Blueprint_Design_Only.md)** — scientific definitions and algorithm design.
- **[Full v2 YAML](../../implementation/genesis-v2/configs/study_v2.yaml)** — actual config parsed by implemented CLI.

## Effective finite experiment scope

- Full training S1: **130 real trajectories** (26 settings × 5 independent training seeds).
- Independent S2: **96 new trajectories** (six anchors ×16 new seeds), **mandatory even if S1 is null**. Transformer L8 is a separate S structure anchor.
- Four frozen checkpoint fractions, three relative damping values, A/B/C-base/C-deep diagnostic tiers. The scientific questions S (structure), M (mechanism), U (task update utility), P (predictor/real optimization) receive **independent** verdicts.
- S3 new optimizer trials start only after U and P pass frozen eligibility, validation and cost gates. Otherwise record explicit S3_NO_GO.
- One local RTX 4070 Ti 12 GiB GPU; E:\GENESIS for worktree, venv, datasets, caches, scratch and experiment artifacts. **No C: bulk fallback**, no paid cloud or API, no private data upload, no automatic merge to main.
- Original 2025 checkpoints and matrices remain unavailable; never use old numeric plateau claims as prospective evidence.

## Status boundary

**Delivered to GitHub:** complete runnable v2 Python source, source-level Git manifest, CPU engineering test history, source integrity CI and the detailed Codex execution contract.

**Not yet executed by this GitHub delivery:** native Windows RTX 4070 Ti CUDA G0, real external-data download/licence execution, the 130+96 full training trajectories, true S3 performance and independent scientific publication-grade review.

Prior documents [START_CODEX_GOAL.md](START_CODEX_GOAL.md), [CODEX_LOCAL_4070TI_GOAL.md](CODEX_LOCAL_4070TI_GOAL.md) and [DRAFT_EXECUTION_CONFIG.json](DRAFT_EXECUTION_CONFIG.json) describe the **older G0-only design phase**. They remain for provenance but should not be executed instead of the v2 code and instructions. Do not remove or silently rewrite these historical contracts.

**Codex handoff:** Start with START_CODEX_GOAL_V2.md and execute EXECUTION_PLAYBOOK_V2.md from Stage 0 through Stage 14. All real runs and raw outputs must remain on the owner's E: drive. GitHub receives code/fixes and only non-sensitive, evidence-linked summaries for review.
