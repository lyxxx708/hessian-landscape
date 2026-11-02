# GENESIS v2 — 4070 Ti complete experiment and GitHub delivery runbook

**Authority:** [runnable source](../../implementation/genesis-v2/README_GENESIS_V2.md), [v2 blueprint](../../implementation/genesis-v2/docs/spec/GENESIS_v2_Blueprint_Design_Only.md), [frozen candidate configuration](../../implementation/genesis-v2/configs/study_v2.yaml), [source manifest](../../implementation/genesis-v2/DELIVERY_MANIFEST.json).  
**Current status:** source imported; earlier Linux CPU tests reported 80 passed and one real-CUDA skipped. User Windows CUDA numerical G0 and the actual complete scientific experiment have **NOT** run.  
**Scientific scope:** S1=26 conditions ×5 independent training seeds=130; S2=6 locked anchors ×16 NEW independent seeds=96. S2 must run even if S1 is negative. This v2 implementation supersedes the older PR #11 draft's 80-confirmation-run layout.  
**Permissions:** unlimited local 4070 Ti running time for this finite design, legally permitted public dataset downloads after rights check. NO paid cloud GPU/API, private holdouts, public raw dataset/checkpoint upload, deletion of historical records, or automatic merging to main.

## Stage 0 — Prepare isolated Git worktree on E:, prove code identity

0.1. Read repository root AGENTS.md, this runbook, the source README, CODEX_EXECUTE_V2.md, configs/study_v2.yaml, docs/BLUEPRINT_TRACEABILITY.md, docs/CODE_REVIEW.md, and docs/RELEASE_VERIFICATION.md.
0.2. In the existing local hessian-landscape repository, check git status and remote before any fetch. Protect all uncommitted work. No reset, clean, forced checkout or forced push. Create a separate worktree on E:; if the chosen branch/path already exists, choose a new non-conflicting branch, not an overwrite.

~~~powershell
git status --short --branch
git remote -v
git fetch origin research/fresh-curvature-revalidation-v1-20261102
git worktree add -b codex/genesis-v2-execution E:\GENESIS\worktrees\hessian-landscape-v2 origin/research/fresh-curvature-revalidation-v1-20261102
cd E:\GENESIS\worktrees\hessian-landscape-v2\implementation\genesis-v2
git rev-parse HEAD
~~~

0.3. Before installing dependencies, verify 143 indexed source files against the shipped SHA-256 manifest; the 144th file is the manifest itself and is protected by the Git commit.

~~~powershell
$M = Get-Content .\DELIVERY_MANIFEST.json -Raw | ConvertFrom-Json
foreach ($F in $M.files) {
    $P = Join-Path (Get-Location) ($F.path -replace '/', '\')
    if (-not (Test-Path -LiteralPath $P -PathType Leaf)) { throw "Missing $($F.path)" }
    if ((Get-Item -LiteralPath $P).Length -ne [int64]$F.bytes) { throw "Size mismatch $($F.path)" }
    $H = (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($H -ne $F.sha256) { throw "SHA256 mismatch $($F.path)" }
}
Write-Host "SOURCE_MANIFEST_VERIFIED: $($M.files.Count) files"
~~~

If the manifest check fails, STOP rather than changing the hash list.

## Stage 1 — E:-first storage, Windows/NVIDIA safety and environment

1.1. Check E: and C: available storage, RAM, GPU process list, driver, actual 4070 Ti name and nvidia-smi VRAM. There must be no other active GENESIS GPU worker.
1.2. Worktree, virtualenv, public data, package/model/HF/Torch/CUDA caches, TEMP/TMP, checkpoint, NPZ/Parquet/SQLite, probe traces, logs, figures and reports must live under E:\GENESIS. C: only unavoidable Windows/driver/installed app files. No junctions or E: overflow to C:, no system-wide registry/Windows changes.
1.3. The E: source code must be inside an E: worktree; the bundled bootstrap refuses a C: source location. Verify the machine has the Python 3.11 launcher and a CUDA driver compatible with the implementation's pinned torch/torchvision CUDA baseline. If not, capture an ENV_BLOCKED receipt and fix reproducibly; no silent CPU-wheel fallback.
1.4. Use 9.5 GiB peak VRAM operational target and 30 GiB initial E: reserve, monitor thermal policy. These are G0-to-be-validated resource constraints, not measured capacity guarantees.

~~~powershell
nvidia-smi
py -3.11 --version
Get-PSDrive -PSProvider FileSystem
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_bootstrap.ps1 -Root E:\GENESIS
~~~

1.5. Bootstrap installs E:\GENESIS\venvs\hessian-landscape-v2, performs package/software checks and a CUDA device doctor. Its pinned package baseline is an implementation choice; do not substitute an unrelated torch version without a new environment lock and G0 rerun.

## Stage 2 — Independent software QA plus legacy-repository regression

2.1. Activate only the process-local E: environment and rerun the v2 test suite; record full stdout/stderr, skipped CUDA count and source git SHA. The prior CPU environment had 80 passed, one skipped, and this is NOT local Windows qualification.
2.2. Also run the earlier repository's original unit tests from the repository root. Do not confuse passing v2 tests with passing the old project suite.
2.3. Check source compilation and git diff; do not loosen numeric acceptance in order to turn failures green.

~~~powershell
. .\scripts\genesis_env.ps1
$Py = 'E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe'
& $Py -m pytest tests_v2 -q
& $Py -m compileall -q genesis_gpu tests_v2
cd ..\..
& $Py -m unittest discover -s tests -v
cd implementation\genesis-v2
~~~

If legacy tests fail, record the failing names and establish root cause separately; never silently state integrated regression is green.

## Stage 3 — Pre-run science matrix and public data rights

3.1. Review the exact dataset sources and licences before downloading: synthetic fixed-teacher DLN, MNIST, CIFAR-10, and a precisely versioned/licensed public-domain Shakespeare character corpus. Never replace real-model datasets with synthetic smoke data for S1/S2.
3.2. Inspect full config: 26 S1 settings, six S2 fixed anchors including **Transformer depth 8**, 5/16 seed split, four checkpoints at 0/1/3/2/3/end of training, three relative dampings 0.001/0.01/0.1, coarse/fine parameter grouping, finite optimizer budget, and C-base/C-deep rules.
3.3. Obtain the driver-generated deterministic dry-run plan before freezing anything. Its training run counts must be 130 and 96, and seed manifests must not overlap. Do not reveal or tune against S2 data during discovery.

~~~powershell
& $Py -m genesis_gpu --config configs\study_v2.yaml plan --stage s1 --dry-run
& $Py -m genesis_gpu --config configs\study_v2.yaml plan --stage s2 --dry-run
~~~

3.4. After reading public-data licence/provenance, permit the configured public downloads, then store exact hashes and split metadata. If a URL/hash/licence is unclear, pause and record DATA_BLOCKED instead of changing data after seeing outcomes.

~~~powershell
& $Py -m genesis_gpu --config configs\study_v2.yaml prepare-data --accept-licenses
~~~

## Stage 4 — Real RTX 4070 Ti G0 numerical and memory qualification

4.1. Run device/storage doctor then *actual CUDA* G0, not just CPU tests or a GitHub Actions badge.

~~~powershell
& $Py -m genesis_gpu --config configs\study_v2.yaml doctor
& $Py -m genesis_gpu --config configs\study_v2.yaml g0 --all --save-reference
~~~

4.2. Confirm same frozen checkpoint, batch, loss normalization, weights/buffers and parameter ordering for G, H, gradient and vector products. For MSE use correctly scaled J-transpose-J; for Cross-Entropy use logit output Hessian, NOT empirical Fisher. Verify valid-token denominator and CE softmax translation null mode.
4.3. Independently compare finite differences/FP64 dense Hessian/GGN with JVP/VJP/HVP, symmetric/PSD GGN, SPD damped GGN, precise full CG and restricted block-CG. Record true residual, condition, tolerance tightening, rank/nullspace controls and failure categories; no fake zero results.
4.4. Compare small exact inverse Frobenius layer blocks to Rademacher random probes; separate Monte Carlo uncertainty from solver bias. Validate loss-curvature weighted E_task/E_val and non-linear loss line search.
4.5. On genuine GPU measure peak allocated/reserved VRAM, GPU total occupancy, Gv time, CG iterations, checkpoint bytes/disk forecast and temperature. If 12GB limits prevent a fixed setting, apply only approved microbatch changes preserving effective batch and objective; otherwise NUMERIC_UNRESOLVED/RESOURCE_BLOCKED.
4.6. **Hard G0 gate:** no S1 or protocol freeze until full software and real local numeric qualification pass. If repairs alter code/config, rerun full tests and new G0; retain original failed receipts.

## Stage 5 — Freeze before viewing scientific S1 outcomes

5.1. Freeze source git commit, Python/PyTorch/CUDA driver, dataset versions/licences, model specs and tied parameters, all tensor flatten/group mappings, RNG/optimizer state, checkpoint fractions, damping scale, solver tolerance, probe methods, null controls, analysis code and Go/No-Go thresholds.
5.2. Predeclare S1 130 and S2 96 distinct training seed clusters. S2 is mandatory even if S1 is entirely negative. Multiple checkpoint, lambda and probe rows inside one seed are correlated, never added to independent N.
5.3. **A tier:** every trajectory has training metadata/checkpoints and cheap spectra. **B tier:** every eligible checkpoint × damping has full-vs-precise-layerwise task utility. **C-base:** fixed initial/terminal structure profiles; **C-deep:** preselected source seeds with extended probes, gauge/nullspace and matched nulls. G0 resource performance, never signal height, determines C costs.
5.4. Record statistical estimands, eligibility, minimum scientific effect, uncertainty/cluster bootstrap and multiple-test policy before discovery. The output protocol-lock.json and seed-manifest.json must be immutable; revisions after results require new version/protocol and independent reruns.

~~~powershell
& $Py -m genesis_gpu --config configs\study_v2.yaml freeze
& $Py -m genesis_gpu --config configs\study_v2.yaml plan --stage s1 --dry-run
~~~

## Stage 6 — Launch one autonomous, resumable local GPU process

6.1. Preferred: the shipped launcher creates a detached local Python process independent of the Codex chat. Use it after G0 and freeze; no separate per-seed Agent or LLM calls. Confirm there is no existing active process before starting.
6.2. The launcher performs/continues G0→freeze→S1→S1 adjudication→S2→S2 adjudication→S3 gate→independent verification→reports.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_launch.ps1 -Root E:\GENESIS -RunRoot E:\GENESIS\runs\genesis_full_v2
~~~

For an INITIAL launch before explicit data preparation/freeze, the licence-acknowledgment switch is permitted only AFTER reviewing public data rights:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_launch.ps1 -AcceptPublicDataLicenses
~~~

Do not run two workers on one GPU. Use -Foreground only to diagnose a local failure and preserve the resulting logs.

## Stage 7 — S1: all 130 real training trajectories

7.1. Execute the 26 model settings ×5 independently sampled training seeds: DLN depth 4/8/16 balanced/unbalanced and covariance variations plus width32, MLP 3/6/12×ReLU/tanh on MNIST, GN-ResNet8/20 on CIFAR-10, and Tiny Transformer 2/4/8 on the frozen text corpus.
7.2. Save all checkpoint weights/optimizer/RNG states at initial, 1/3, 2/3 and final positions. No changing a teacher/target mid-trajectory or substituting an artificially zero residual dataset.
7.3. B tier: compare full damped GGN and *accurate* blockdiag(GGN)+damping solves at SAME checkpoint/loss/batch/g, best quadratic-ray scalar alpha_Q, train-fitted CE-Hessian-weighted alpha_task, E_task/E_val, quadratic regret Delta, actual non-linear loss line-search and same-cost short CG. Exact parameter and output-response weights must be locked.
7.4. C tier: all requested layer-distance bin energies (raw G, damped inverse, stable correction), per-element unequal-block RMS, full seed/probe variance and solver residual, matched-order/spectral/Gauge controls. Finite-depth flat tails cannot be promoted as a universal non-decaying L→infinity plateau.
7.5. Every invalid gradient, failure, thermal/OOM escalation and unresolved CG must be preserved as a separately qualified record and included in coverage denominators. Never hide negative cases, retune thresholds or add seeds until a positive effect is found.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_status.ps1
~~~

7.6. Review compact status counts, not thousands of lines of logs in Codex; no LLM calls per seed, λ or probe. A row is scientifically usable only if its numerical qualifications pass.

## Stage 8 — S1 adjudication, S2 unlock and independence

8.1. The preregistered adjudicator operates on completed or explicitly invalid rows, with seed-cluster resampling (not checkpoint pseudoreplication). Grade S-structure, M-mechanism, U-task and P-predictive value separately. An S-positive U-negative result is legitimate.
8.2. Do NOT retune or alter source/config after reading S1 and before confirmation. Lock S2 selection and verify all 96 seeds are fresh and unseen.
8.3. The pipeline performs adjudication automatically; explicit replay only when recovering a completed stage:

~~~powershell
& $Py -m genesis_gpu --config configs\study_v2.yaml adjudicate --stage s1
& $Py -m genesis_gpu --config configs\study_v2.yaml plan --stage s2 --dry-run
~~~

S2 is **not optional** merely because S1 found nothing interesting.

## Stage 9 — S2: mandatory 96 fresh training trajectories

9.1. Six fixed anchors, each with 16 new independent training seeds: DLN L8 and L16 nonorthogonal/anisotropic, ReLU MLP L6, GroupNorm ResNet20, Transformer L4 (text U) and **Transformer L8 (text long-distance structure)**.
9.2. Use exactly the original frozen task and λ scheme, preserve numerical eligibility and independent raw probe uncertainty. Include all negative and invalid seeds.
9.3. Report seed-level confidence/cluster bootstrap and preregistered multiple-test correction. Do not count 16 seeds ×4 checkpoints ×3 λ as independent N=192.
9.4. If the structure/utility fails, report a no-support result limited to the tested architecture/depth/data/damping; do not transform an S2 failure into new discovery training.

~~~powershell
& $Py -m genesis_gpu --config configs\study_v2.yaml run --stage s2 --resume
& $Py -m genesis_gpu --config configs\study_v2.yaml adjudicate --stage s2
~~~

These commands are for explicitly controlled recovery; the normal detached pipeline already calls them.

## Stage 10 — Conditional S3, strong baselines and time-to-target

10.1. Only if U and P pass frozen significance/effect/cost gates, run paired-seed real optimizer comparisons with tuned AdamW, precise layerwise GN, equal-cost short CG, K-FAC as an explicit approximation, Gradient Smoothing reference implementation, and selective Krylov. Account for hyperparameter search and actual Gv cost.
10.2. Full GN on small models is an offline oracle; it is not a free online baseline. Evaluate wall-clock time-to-target, fixed sample/token budget performance, peak GPU memory, failure/variance and learning-rate-only controls.
10.3. If U/P fail, perform the predeclared minimal negative optimizer sanity check and mark S3_NO_GO, not “unimplemented” or fabricated speedup.

~~~powershell
& $Py -m genesis_gpu --config configs\study_v2.yaml run --stage s3 --only-if-gate-pass
~~~

## Stage 11 — Stop, resume and fail-closed recovery

Use the cooperative stop and resume scripts; never taskkill unrelated Python/Codex processes, never silent C: fallback, never automatically erase evidence. After interruption, compare on-disk source/config/env/protocol hash before launching resumed work.

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_stop.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_resume.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_status.ps1
~~~

Separate fault labels: ENV_BLOCKED, STORAGE_BLOCKED, CUDA/OOM, DATA_LICENSE_BLOCKED, G0_FAILED, NUMERIC_UNRESOLVED, MISSING_CHECKPOINT, INTERRUPTED, INVALID_SEED, S3_NO_GO. For a code fix after freeze, create a new versioned run and repeat affected qualifications, not overwrite old evidence. Do not claim scientific completion while an essential panel is silently missing.

## Stage 12 — Independent numerical QA and report generation

12.1. After S2 and any warranted S3, rerun independent numerical checks against saved checkpoint/batch/probe seed via separate algorithm paths; verify numerical residuals, hashes, parameter shared weights, true GGN MSE/CE normalization, CE loss-curvature E_task/E_val, seed non-overlap, all distance bins and negative cases.
12.2. Check every published claim has a raw artifact path, SHA256, independent training-seed count, CI/uncertainty, major null and invalid-rate. Engineering smoke must never be mixed with S1/S2 scientific data.
12.3. Regenerate figures/tables from audited raw data, then recheck the final report/figure manifest. Use exactly these shipped CLI entrypoints:

~~~powershell
& $Py -m genesis_gpu --config configs\study_v2.yaml verify --independent --all
& $Py -m genesis_gpu --config configs\study_v2.yaml report --format md,html
& $Py -m genesis_gpu --config configs\study_v2.yaml status --json
~~~

12.4. Expected local E:\GENESIS\runs\genesis_full_v2 output: protocol/environment/seed locks, run_status.sqlite, all source/data/checkpoint/probe hashes, failed and ineligible rows, full S/M/U/P tables, figures, NUMERICAL_QA, NEGATIVE_RESULTS, REPRODUCTION, RESOURCE_ACCOUNTING and SCIENTIFIC_VERDICT.md.
12.5. Permitted scientific verdicts: COMPLETE_POSITIVE, COMPLETE_MIXED, COMPLETE_NEGATIVE or INCOMPLETE_BLOCKED_EVIDENCE. A complete negative study is a valid finish; an unrun study is NOT.

## Stage 13 — Reviewable GitHub delivery of real code and evidence

13.1. User authorizes delivery of source, fixes, tests, guides and compact **redacted** results to GitHub. Never push raw checkpoint/NPZ/Parquet/SQLite, protected datasets, secrets, private paths or large scientific traces.
13.2. Before push: run source manifest check, full regression tests (new and old), CUDA G0, raw-data independent audit, git diff check and credential/licence/publication scan. Compare to frozen source hash. Preserve historical failures; no false claim promotion.
13.3. In E: worktree prepare a distinct Codex execution branch. Use a GitHub review PR targeting the PR #11 feature branch unless the maintainer separately authorizes main. No automatic merge. Attach a compact evidence index with actual runtime counts, invalid rates, GPU-hours/VRAM, final S/M/U/P verdict and SHA.
13.4. When a tested source change exists and the GitHub CLI is authenticated:

~~~powershell
git status --short --branch
git diff --check
git add implementation/genesis-v2 research/revalidation
git commit -m "feat(genesis): audited Windows CUDA qualification and scientific outputs"
git push -u origin codex/genesis-v2-execution
gh pr create --base research/fresh-curvature-revalidation-v1-20261102 --head codex/genesis-v2-execution --title "GENESIS v2 GPU research qualification and results" --body-file E:\GENESIS\runs\genesis_full_v2\reports\GITHUB_PR_SUMMARY.md
~~~

Do not invent an empty commit if no change was needed. A PR creation requires actual tool/CLI success; otherwise save the PR body and report the blocker.

## Stage 14 — Final acceptance, hard-stop and scientific claim grades

Mark the Goal COMPLETE only when ALL hold:
- Native Windows CUDA 4070 Ti G0 passed with numerical/device receipts, and E: storage check passed without C: bulk overflow.
- Full local v2 and legacy regression suite passed or every unrelated failure was expressly adjudicated; actual source/config/seed lock is preserved.
- **130 S1 +96 S2** planned training rows have real completed or explicitly invalid evidence; all scientific claims use only numerically qualified rows and independent seed-cluster statistics.
- The standalone independent verifier actually ran against raw artifacts, all significant claims have source/hashes and uncertainty, and both positive and negative evidence are preserved.
- S3 was executed if task/predictor gate passed, or explicitly stopped by S3_NO_GO; no claims of optimizer acceleration from heatmaps.
- GitHub has only reviewed/source/redacted summaries and a readable PR, not private raw evidence; main untouched.

Any hard blocker must produce INCOMPLETE_BLOCKED_EVIDENCE with the exact failed gate, artifact pointers and a safe resume procedure. Do NOT fabricate completion, select attractive seeds, switch research objectives after results or expand the finite grid indefinitely.

## Quick commands

| Task | Actual entrypoint from implementation/genesis-v2 |
| --- | --- |
| Bootstrap | powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_bootstrap.ps1 |
| Full launch | powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_launch.ps1 -AcceptPublicDataLicenses |
| Status | powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_status.ps1 |
| Cooperative stop | powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_stop.ps1 |
| Resume | powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\genesis_resume.ps1 |
| Verify | $Py -m genesis_gpu --config configs\study_v2.yaml verify --independent --all |
| Report | $Py -m genesis_gpu --config configs\study_v2.yaml report --format md,html |

**Precedence note:** Old PR #11 text saying “build the whole harness from scratch”, S2=80, or G0-only code describes earlier proposals and is superseded by the source and v2 runbook here. Keep those historical records as provenance, not as live execution instructions.
