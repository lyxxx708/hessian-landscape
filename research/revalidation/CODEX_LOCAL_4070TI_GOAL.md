# Codex Local Goal — GENESIS complete revalidation on RTX 4070 Ti

**Owner:** user · 2026-11-02 · **Status:** NOT_STARTED_LOCALLY.
**Hardware:** local Windows RTX 4070 Ti, 12 GiB VRAM. User authorizes UNLIMITED LOCAL GPU RUN TIME; not unlimited VRAM, electricity-free hardware, Codex tokens, paid cloud services or external data access.

## Objective

Autonomously IMPLEMENT and RUN the complete prospective GENESIS Hessian/GGN study on the owner's local GPU: G0 correctness, S1 natural-training discovery, S2 independent confirmation **even when S1 finds a null**, and S3 real optimizer trial **only if task-utility gates pass**. Finish with preserved evidence, negative findings, independent numerical QA and a final scientific verdict. The unavailable 2025 raw matrix/checkpoint is NOT an experimental input or fitting target. The 2026 synthetic P0 is a correctness control only.

This is a run-to-evidence objective, not a request to produce another plan, tiny demo, CI badge, slide deck or speculative paper. A rigorously completed negative result is as good as a positive result. Never claim full completion without raw executed results.

## Sources and scope

- Read root AGENTS.md. Read this file, research/revalidation/2026-11-02_FRESH_VALIDATION_PROTOCOL_V1.md and research/revalidation/LOCAL_4070TI_FULL_V1.json. The 2026-10-26 protocols are historical scientific context, not permission to reuse old invalid claims.
- Work on an isolated branch/worktree based on draft PR #11, preserving any existing local changes. Never overwrite historical archives, force-push main, delete research branches or auto-merge a PR.
- Local CUDA GPU time is explicitly approved without a time cap; finite preregistered experimental grid and bounded individual solver retries still apply. NO paid cloud GPU, paid API calls, remote LLM inference within experiments, private sealed dataset, third-party credentials or automatic public raw data uploads. License-verified public datasets may be downloaded.
- Do not waste tokens trying to recover the unavailable 2025 DLN matrix. It cannot validate the new research. Do not make a synthetic run match the reported 0.09–0.12 curve.

## Token minimization: code once, GPU many times

- No model queries per training seed, checkpoint, damping value, estimator probe or ordinary runtime status. LLM CALLS PER SEED = ZERO. Do not use an Agent to watch the GPU. Codex should implement deterministic Python batch orchestration and let a separate local process run all hours/days of computation.
- Use Codex for architecture, implementation, mathematical debugging and final audit; at most two tightly scoped subagents may independently implement/review code if this improves test quality. No subagent chains per experiment. Read compact error summary JSON rather than dumping thousands of log lines into context.
- After G0 passes, freeze experiment/seed/analysis/holdout definitions and hand off to one resumable GPU worker. All routine runs, measurements, retries, figures, reports and final data manifests are code-driven. Repairs after freeze require a new version/hash, explicit reason, and rerun of affected conditions, not silent patching.
- Periodic status output is one compact JSON record: runs completed / planned / invalid, numerical qualification, current task, CUDA peak memory and resource faults. Full logs and exact failures stay on local disk.

## Phase A — preflight and implementation

1. Inspect exact local git state, CUDA/nvidia-smi, 12 GiB VRAM, Windows/Python/CUDA/PyTorch, RAM/disk free space, source/data availability. Install a compatible stable CUDA-enabled PyTorch wheel using the official selector; do NOT hardcode an unverified wheel URL. Prefer an isolated Python 3.11/3.12 venv and freeze actual packages and driver in env-lock.
2. Do not fallback silently to CPU. Use only one GPU job at once and target peak device usage <=9.5 GiB to leave Windows desktop headroom. Adjust **microbatch only while preserving effective batch, normalization, sample/token budget and training state**. If not valid, record a resource failure. Keep GPU temperature/power monitored; pause safely for persistent >=85C; never bypass hardware protections or silently alter OS-wide power settings.
3. Implement tested model/data adapters: fixed-target DLN, MLP/MNIST, GroupNorm ResNet8/20-CIFAR10, and character Tiny Transformer on a legally distributable public-domain/clearly licensed corpus. Pre-freeze corpus/version/hash and split; no later dataset switching based on outcome.
4. Implement loss-specific GGN-vector products: mean squared residual G = J^T J/M; cross-entropy G = J_logits^T H_CE_logits J_logits using correct reduction. NO empirical-Fisher substitution. Verify JVP/VJP, exact-H HVP, adjoints, symmetry, PSD and fixed-vs-moving stochastic model state on tiny models, and independently compare against FP64 dense reference/finite differences. Frozen checkpoint and batch must remain unchanged during all CG matvecs.
5. Implement accurate full SPD CG and **precise layer-restricted CG** for D = blockdiag(G)+lambda I; log true residual, conditioning and nonconvergence. A diagonal Adam/SGD preconditioner must never be called precise layerwise GN. Avoid autograd-graph accumulation across the many matvecs.
6. Implement inverse block energy estimates without dense H: block-supported independent Rademacher probes z, solve (G+lambda I)x=z, estimate E_ij = average ||x_i||_2^2. This estimates squared Frobenius energy. Log all individual probe energies, solver bias, Monte Carlo uncertainty and size-adjusted block RMS; validate on exact small matrices. Distinguish unbiased energies from biased ratios and document limits.
7. Implement same-checkpoint task-value assay: full p* vs block pB with optimal scalar alpha chosen OFFLINE; report eta, Delta=1-eta, E_task, E_val with fixed train-fitted scalar, actual line-search, numerical qualification. No zero-gradient forced Delta=0. Exact-H indefinite analyses belong in a separate mechanism lane with pole/shift checks.
8. Implement deterministic experiment driver and independent verifier: doctor, g0, freeze, run-all, status, resume, verify, report. Write idempotent run IDs, SHA256 checkpoint/config/data hashes, atomic JSONL/SQLite progress, fixed seed splits, restart logic, resource monitoring, CSV/NPZ/parquet arrays, figures and all failure states. Windows PowerShell start/status/stop/resume wrappers must launch a local process independent of the Codex interface. Stop only this experiment's process.
9. Execute G0 with seeds **excluded from S1/S2 inference**. Verify dense/CG, true GGN for MSE+CE, exact-H reference, inverse-block sketch and error bars, equal-block consistency algebra, end-to-end toy checkpoint reproduction, GPU memory/time on every model family. Freeze a protocol lock and complete deterministic selection logic BEFORE viewing S1 science data. If G0 fails, repair and retest instead of declaring success.

## Phase B — execute S1 completely

Run ALL **26 planned settings, 5 independently seeded training trajectories each** = **130 fresh training jobs**, as exactly specified in LOCAL_4070TI_FULL_V1.json:
- DLN 15 conditions: depths 4/8/16 with balance and covariance sweeps, plus a width sensitivity panel.
- MLP 6 conditions: depths 3/6/12 × ReLU/tanh on MNIST.
- GroupNorm ResNet 2 conditions: ResNet8/20 on CIFAR-10.
- Tiny Transformer 3 conditions: depths 2/4/8 on licensed character-level next-token prediction.

Save checkpoints at fractions 0, 1/3, 2/3, 1 of the same fixed training task. Analyze 3 relative damping settings per state (nominal 520 checkpoints ×3 = 1,560 measurements, before ineligibility). Fully record S structural distance profiles, M controls (nullspace, layer scaling/gauge, fixed-matrix lambda sweeps, matched permutations/spectra) and U gradient-conditioned value. Use adaptive 16→32→64→128→256 probes per source block; a failed uncertainty criterion is NUMERIC_UNRESOLVED, not zero signal. Save all seeds/configs, including negative or expensive ones.

GPU compute time is unbounded by the user, but experiments remain **finite and deterministic**. Predeclared per-job training steps/tokens, adaptive numerical tolerance escalation and finite retry policy still apply. Do not endlessly tune after inspecting S1 results. If required settings cannot fit memory after documented fallback, preserve INVALID and report incomplete coverage, not an unapproved smaller replacement.

## Phase C — execute S2 regardless of discovery's sign

Run the **unconditional confirmatory anchors**, all with eight NEW independent training seed clusters: DLN depth 8 &16 unbalanced anisotropic, MLP depth 6 ReLU, ResNet20 GroupNorm/CIFAR10, and four-layer Tiny Transformer. This is a minimum of **40 new training runs**, whether S1 discovered an effect or a null. When the locked S1 selection rule requests one discovery-positive and one discovery-negative condition, add up to 8 new runs each, excluding duplicate anchors.

No tuning on S2. Do not look at S2 data before the seed/config/analysis freeze and committed S1 selection. Report confidence intervals by *training-seed cluster*, not checkpoint/lambda rows. Separate estimator Monte Carlo error from seed-to-seed variability; run independent raw metric recomputation. Lack of a platform or optimizer utility is a valid S2 result; do not make unsupported universal impossibility claims.

## Phase D — S3 conditional real optimizer study

Apply locked S and U Go/No-Go decisions after S2. If the gradient-conditioned full-GN advantage is negligible or fully explained by a scalar step/cheap predictor, **STOP a new optimizer** even if the structural pattern exists; execute only predeclared minimal negative-control training. If U passes pre-fixed effect AND predictor gates, complete paired-seed real training (at least vision and text) comparing tuned AdamW, precise layerwise GN, same-cost short CG, applicable SOAP/K-FAC and Gradient Smoothing; include small-only offline full-GN oracle. Measure actual compute-adjusted wall-clock time-to-target, fixed-budget quality, variance, memory and all extra matvec/tuning costs. No speedup claims from block-energy heatmaps or oracle eta alone.

## Deliverables, QA and true stopping rules

Use local ignored artifact storage (default local_artifacts/genesis_full_20261102) with manifest.jsonl, atomic status.json, env + protocol locks, all seed/checkpoint/config hashes, raw numerical arrays, estimator probes, solver traces and every failure/invalid case.

Produce **reports/SCIENTIFIC_VERDICT.md** with distinct S / M / U verdicts, effect sizes, counts, confidence intervals, negative results, and path+SHA for every material claim, plus S_M_U_RESULTS.md, NUMERICAL_QA.md, NEGATIVE_RESULTS.md, REPRODUCTION.md, RESOURCE_ACCOUNTING.md and figures. A separate verifier independently recomputes a sample of raw metrics/plots and proves no holdout leakage or invalid claim promotion. Final state is COMPLETE_POSITIVE / COMPLETE_NEGATIVE / COMPLETE_MIXED only with full S1/S2 required coverage and audit. Ineligible runs must remain counted and cannot support a positive claim.

Store large datasets/checkpoints/arrays locally; commit only runnable code, configs, tests and compact non-sensitive reports to a feature branch. Review rights/credentials before any public push. Do NOT auto-merge main.

If CUDA absent, safe hardware conditions impossible, public dataset rights unsatisfied, G0 numerical validity irreparable, or essential settings cannot run on this 12 GiB device, stop with INCOMPLETE_BLOCKED_EVIDENCE and complete diagnostic artifacts. Do not fabricate completion or substitute toy demos. Otherwise autonomously implement, run, check, correct, and resume without unnecessary user questions.

**Use more GPU; use far fewer model tokens. Success = new reproducible scientific evidence, including negative evidence.**
