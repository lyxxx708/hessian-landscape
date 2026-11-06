# GENESIS NEXT v3 — Validation Reversal & Fair Block-GGN Benchmark

**Status:** DESIGN-ONLY, NOT FROZEN, NOT EXECUTED. **Evidence:** post-hoc, S1 exploratory. 2026-11-06.

## 0. Why two experiments, not one narrative

PR #16 (commit `4c02cd6e465403825fbe3059f6266094a91df555`) records 38 completed DLN checkpoints (19 independent training seeds) × 3 gamma = 114 qualified conditions. Among these, `Block` one-step validation gain is negative in 93/114 and `Full` in 91/114, despite positive gains on the original 32-example curvature/training batch. Fixed-grid CG matches Block on all 114 conditions and reaches at least 99.9% of the Full quadratic gain in all 114. These are repeated measures, not 114 independent trials. The old Block-CG calls a full zero-padded GGN matvec for every layer, and its wall cost is not a fair bound on optimized Block-GGN cost.

**Exp V — cause of negative validation gain:** Separate (i) mini-batch gradient conflict / sampling noise, (ii) train-selected step overshoot, (iii) failure of local curvature predictions. Causes can coexist.

**Exp B — fair Block-GGN economics:** Compare mathematically identical exact Block directions implemented by old padded matvecs versus efficient DLN Kronecker direct solve; then compare both to Full CG under honest cold/warm/end-to-end costs. Do not use weakened Block approximations to manufacture CG advantage.

Non-goals: do not change original GENESIS v2/S1/S2, reread S2, train new models in this first phase, claim new independent scientific confirmation, or publish restricted checkpoints/datasets.

## 1. Frozen parent panel and provenance

Primary panel: the **same 38 trained DLN checkpoint states** that have `NUMERIC_VALID` NEXT v2 results; gamma = {0.001, 0.01, 0.1}. Preserve the *80-state/240-condition parent denominator*, including the 42 currently `SOURCE_NOT_READY` states. Never replace the failed seed or untrained non-DLN states. The 38 states are 19 independent seeds with checkpoint indices {1,3}. Setting/seed/checkpoint/gamma, model SHA, data SHA, original S1 protocol SHA, frozen spectral scale and absolute damping, source SHA, input rounding policy, v3 code/config hashes must accompany every result.

Every direction and analysis objective is built with **the exact same FP32-valued v2 curvature batch lifted to FP64**, as in NEXT v2. Control for native FP64 synthetic inputs separately; never silently change the mathematical problem. Preserve OMP, MKL, OpenBLAS and Torch thread settings recorded by the original run and verify synthetic dataset fingerprint before use.

Use original synthetic DLN data source: full train split 4096, validation split 1024, original test split 1024. These share the training seed's teacher/generative distribution but are disjoint draws. Never select a scientific claim using a new experimental seed after seeing its test result.

## 2. Exp V — high-power validation of the observed sign reversal

### V1. Fixed deterministic evaluation pools

For each training seed, build and hash **one** identity-preserving evaluation schedule and reuse it across checkpoint, gamma and method:

- **T32:** the original v2 curvature/train batch, count 32 (same replacement sampling as v2).
- **T512-excluding-T32:** choose 512 distinct train-split indices, deterministically, excluding the indices of the original T32 batch. This is a *training-split control*, not generalization data.
- **T4096:** the full train split, including T32 (read-only).
- **V8×128:** a deterministic seeded permutation of the original 1024 validation examples, partitioned into 8 disjoint groups of 128. Also report **V1024**, their complete mean. Do not count V1024 as an independent ninth batch.
- **E8×1024:** a newly generated, independent 8192-example synthetic evaluation pool from the same verified fixed teacher/input covariance, using a new deterministic namespace per seed. Partition into eight disjoint batches of 1024. Check the teacher/covariance identities and hash all generated data. It is new *data*, NOT a new training seed or confirmatory trajectory.
- **Test1024:** the original untouched test split; used **once after** the V experiment implementation, alpha policies and analysis logic are fixed, only for reporting generalization of frozen policies. It is not used for tuning or selecting conditions.

The primary result uses V1024 and E8192; V8×128 quantifies between-mini-batch variation. Use FP32-valued data lifted to FP64 for the primary matching comparison; native FP64 generation is a separate precision sensitivity column.

### V2. Directions and complete alpha grid

For all 38 states and 3 gamma, calculate three fixed directions on T32 only:

- `Full`: the independent FP64 full-GGN reference direction, \(d_F=-(G+\lambda I)^{-1}g\).
- `Block`: exact layer Block-GGN direction with the original **quadratic best-ray scaling** and numerically validated against NEXT v2.
- `CG8`: fixed 8-step unpreconditioned Full-GGN CG direction, with best-ray scaling charged consistently; no oracle per-case k choice.

Evaluate ALL directions (no validation-based pruning) on each pool and **all** alpha grid values:

`[0, 1e-5, 1e-4, 1e-3, 3e-3, .01, .03, .1, .3, 1, 3]`.

This includes all 7 original train-selected grid points plus 4 near-zero diagnostic points. Record actual \(L_B(\theta+\alpha d)\), \(L_B(\theta)\), \(\Delta L\), and gain \(-\Delta L\) at each alpha. Reproduce NEXT v2's original T32-selected alpha and gain from the frozen old grid first (pilot tolerance fixed before full run). Do not use validation/test grid to choose a deployable alpha.

Diagnostic **oracle** alpha minimizing V1024 loss may be reported, but it is not a valid online baseline. To evaluate a validation-selected alpha, choose it using predeclared V-half and evaluate it on the other V-half or Test1024. Distinguish train selection, validation-assisted selection and oracle upper bound in every table.

### V3. Mechanism diagnostics and mutually nonexclusive labels

For each direction, compute train/validation/extra-pool gradients at \(\alpha=0\), and the projected descent score:

\[
 s_B(d)=-g_B^\top d.
\]

If `s_B<0`, infinitesimal movement in the direction *increases* that population/sample loss: first-order train/held-out gradient conflict. If `s_B>0` but the T32-selected finite-alpha update has negative gain, the likely mechanism is **step overshoot** or higher-order deviation. Compute validation directional Hessian \(d^\top H_{V}d\) (and original train GGN quadratic \(d^\top G_{T32}d\)); compare measured small-alpha gains against first- and second-order predictions. A demonstrable prediction mismatch beyond measured FP64 numeric error is a **local-model failure**; do not use the word causal for correlations alone.

Attribution tags: `FIRST_ORDER_CONFLICT`, `STEP_OVERSHOOT`, `CURVATURE_OR_HIGHER_ORDER_MISMATCH`, `BATCH_HETEROGENEITY`, `INCONCLUSIVE`; more than one can apply. Set numeric sign resolution from repeat FP64 evaluation and summation-order controls before classifying; values within the error bound are `NUMERICALLY_INDETERMINATE`, never arbitrarily positive/negative. Report absolute gain and loss-normalized gain together.

Pre-specified discriminators:

- T32 gains positive, but T512/T4096/V1024/E8192 negative **already at infinitesimal alpha** → training-batch optimization bias/direction conflict.
- V1024/E8192 have positive initial directional slope, but T32-selected alpha yields negative gain and a smaller alpha improves → overshoot/step selection.
- Early curves deviate materially from both held-out first/second-order predictions → nonlinear/Taylor mismatch.
- V8×128 signs vary and V1024/E8192 agree weakly → evaluation noise/heterogeneity; test via independent seed-level replication.

Use conditional labels, not one automatic winner.

### V4. Fixed intervention: recompute the direction with a larger training batch

Reading a larger validation batch alone cannot establish that the **T32 gradient/direction estimate** caused the reversal. Add a pre-declared nested mechanistic intervention on two representative original settings: `dln_d4_w16_orthogonal_balanced_c1` and `dln_d8_w16_random_unbalanced_c100`, **all actually ready seeds**, checkpoints {1,3}, all three gamma (currently 9 original seeds × 2 × 3 = 54 state–gamma comparisons). Do not cherry-pick seeds or conditions based on their existing delta or validation gain.

Hold checkpoint, parameterization, **absolute lambda**, loss definition and held-out V1024/E8192 pools fixed. Compute a **new** independent T512 direction on 512 training-split examples excluded from the original T32 curvature examples, via FP64 Full GGN and exact optimized Block GGN (CG8 may be a secondary comparator). Evaluate the complete frozen alpha grid and train-only alpha selection under the same rules as T32, separately reporting the chosen alpha for each training batch. Also measure gradient variance on eight disjoint T32-sized training subsets (do not confuse these gradients with eight independent training seeds). If the reestimated T512 direction changes the held-out directional derivative/gain while T32→T512 step-only rescaling cannot, this supports **batch-specific direction error** rather than pure overshoot. Note that changing the gradient/curvature batch also changes the local quadratic optimization problem; compare directions on a **common held-out loss**, not raw F* values from different batches. If matrix-free FP64 T512 Q0 exceeds the pre-frozen cost cap, record resource censoring and keep V1–V3 results intact.

## 3. Exp B — optimized exact Block-GGN versus Full CG

### B1. Three Block baselines (one exact target)

- **Old-Block-CG**: unchanged legacy block solver with full-length padded `raw_ggn` per layer. Validity check and historical timing context **only**; never the sole primary Block runtime comparator.
- **Fast-Block-Kron-Direct (primary)**: exploit the **exact** block Kronecker form for the **linear, bias-free DLN + MSE** case. For layer \(\ell\), with row-stacked layer inputs \(X_\ell\) (B×input width), downstream product \(D_\ell\) (output width×layer output width), and loss denominator \(N=B\cdot d_{out}\),

\[
 G_{\ell\ell}[\Delta W] = (D_\ell^\top D_\ell)\;\Delta W\; (X_\ell^\top X_\ell)/N.
\]

Set \(S=D_\ell^\top D_\ell\), \(T=X_\ell^\top X_\ell/N\). Eigen-decompose \(S=U\,\mathrm{diag}(s)\,U^\top\), \(T=V\,\mathrm{diag}(t)\,V^\top\). Solve \(S\Delta W T+\lambda\Delta W=-g_\ell\) exactly as

\[
 \Delta W=-U\left[(U^\top g_\ell V)\oslash(s_i t_j+\lambda)\right]V^\top.
\]

Cache X/D and eigensystems across the **three frozen gammas for one checkpoint**. Include factor formation and eigensystem cost in the clock; the fact this formula is exact is *specific to linear MSE networks*. Do not call generic K-FAC exact on nonlinear networks.

- **Fast-Block-Kron-CG (control)**: implement block-local matvec \(S\Delta W T+\lambda\Delta W\) without full-length padded AD/GGN; compare to direct solve to isolate factorization overhead.

Keep two online Block policies separate: (a) **raw Block-direct direction + train-only fixed-grid line search**, which does not require an extra full \(Qd\), and (b) **best-ray Block-direct direction**, for direct comparison with the original \(\delta\) estimand; this second policy must pay for any necessary full \(Qd\). Match CG with the same scalar/line-search policy when claiming online cost advantage.

**Numerical acceptance:** verify every new Block direction against independent dense FP64 \((G_{\ell\ell}+\lambda I)^{-1}g_\ell\), and old Block direction, before timing. Require relative direction error ≤1e−7 (or explicit `NUMERIC_UNRESOLVED`, never loosen based on outcomes). The best-ray gain \(F_B\) must agree within a numeric tolerance chosen before timing, with absolute fallback when \(F_*\) is very small. Verify GGN operator equality on predeclared random vectors.

### B2. CG baselines and workload/clock fairness

CG: unpreconditioned Full GGN, fixed k∈{1,2,4,8,16,32,64}, plus residual-based stopping fixed ex ante. Keep a high-precision Full reference **out of the online cost** only as an *evaluation oracle*, never let methods exploit it.

Report two distinct execution regimes:

**Cold-start, one gamma:** common frozen checkpoint and T32 inputs ready; count every method-exclusive forward/backward, Block-factor construction, eigensolve, all GGNv, damping/application and best-ray scalar calculation. Common gradient cost is reported separately and added equally when reporting end-to-end step cost. Each method gets the same candidate step grid and pays for training-only line search in end-to-end accounting. Validation/test diagnostic curves are **not** online costs.

**Warm/reuse:** compute all three frozen gammas from one checkpoint; Block caches X/D and decompositions; Full CG may also reuse its operator/compiled graph or any allowed common work. Report total per-checkpoint cost across gamma, not an artificially free Block cache or free Full GGN materialization.

**Timing design:** dedicated/sequential CPU timing, 2 threads per run, 1 warm-up + 7 randomized paired repeats per state; fresh processes when required to prevent cache contamination. Log CPU affinity, thread settings, CPU/process time and wall time, competitor background load, peak RAM and computed GGNv/local factor operations. GPU timing is optional and **only if** existing v2 worker is safely released; no preemption required for the DLN CPU panel. If timing instability (coefficient of variation >10% within a method/condition), report cost `TIMING_INCONCLUSIVE` instead of claiming acceleration.

**Two noninterchangeable comparisons:**

1. *Quadratic quality frontier*: horizontal actual end-to-end time, vertical \(F(d)/F_*\), with Block and CG each receiving the same train-only step evaluation policy.
2. *Cost to reach the exact Block quality* \(F_B\): compare CG's first measured k satisfying \(F_{CG}\ge F_B-10^{-4}F_*\) with optimized Block direct total cost (including one \(Qd_B\) for best-ray scaling if used). This is an **offline oracle diagnostic**: online CG cannot know \(F_B\) to stop. Also report all fixed-k CG methods and their practical nonoracle stop rules.

For \(F_{CG}\ge 0.99F_*\), record CG cost, but label Block as `QUALITY_TARGET_UNATTAINABLE` whenever its exact best-ray \(F_B<0.99F_*\). Never call those rows a direct cost win by default. Disclose if the efficient Block implementation reverses earlier runtime ranking.

### B3. Relation to nonlinear models

Do not transfer the exact DLN formula blindly to MLP/ResNet/Transformer. A future, separately frozen nonlinear extension may include K-FAC as a **Kronecker approximation** (Martens & Grosse, ICML 2015), plus a separately validated exact block-JVP/VJP oracle if resources allow. No S2 reads; no new claim that S1 extension is confirmation.

## 4. Primary analyses / estimands and statistical unit

Unit of independence = **original training seed**, with checkpoint 1/3 and the three gamma values paired within seed. Within each setting, report seed-level median absolute and relative validation gains, fraction of negative large-pool gains, directional-slope sign, overshoot prevalence, median Full/Block/CG quality, cold/warm costs and time ratios. Report V8×128 and E8×1024 variation *conditional on that seed* separately; these samples are not new independent training trajectories. Stratify by DLN depth (4/8), conditioning (1/100) and initialization. No p-values masquerading as preregistered confirmation; 95% seed-cluster bootstrap descriptive with n=4 or 5 per setting and explicit limits.

**Primary questions judged from E8192:** (a) does the 91/114 Full validation-negative sign persist in large independent data? (b) what fraction is first-order conflict vs finite-step overshoot? (c) in the fixed T512 intervention, does changing the actual direction repair the reversal when mere step rescaling does not? (d) does optimized exact Block reverse or erase CG's historical 2–15% solve-time ratio at comparable quality?

For future confirmation of any candidate **new** claim: independently train fresh, non-overlapping seeds under a *new versioned protocol*, freeze hypotheses/selection/costs before starting; do not repurpose the old S2 to confirm these post-hoc claims.

## 5. Execution contract, failure handling, deliverables

- Isolated new E: worktree, output root and protocol lock; old v2 and NEXT v2 remain read-only. No automatic GPU pause and no new training in this phase. Pin and verify all SHA inputs before any result.
- Gates in order: source/provenance replay → T32 original-alpha compatibility checks on predeclared balanced and ill-conditioned states → Kronecker exactness/independent reference tests → freeze new protocol → Exp V + Exp B on all input-ready DLN states → seed-level analysis → independent review. Freeze must precede *new* scientific assay measurements (qualification pilots explicitly excluded from inference).
- Per-condition states: `QUALIFIED`, `NUMERIC_UNRESOLVED`, `SOURCE_NOT_READY`, `TIMEOUT_INCONCLUSIVE`, `FAILED`. Do not replace seeds or impute unavailable samples.
- If full E8192 evaluation is too expensive, record pre-specified staged coverage (e.g. E2048, E4096, E8192) as resource censored, not selectively stop because of a scientific effect.
- Store `RUN_PLAN.json`, `PROTOCOL_LOCK.json`, `STATE_CONDITION_INDEX.csv`, `VALIDATION_ALPHA_GRID.jsonl`, `DIRECTIONAL_SLOPE_AND_HVP.jsonl`, `VALIDATION_ATTRIBUTION.csv`, `BLOCK_REFERENCE_CHECKS.jsonl`, `BLOCK_CG_COST.csv`, `PAIRED_SEED_SUMMARY.csv`, `NUMERIC_QUALIFICATION.csv`, `FAILURES.csv`, `SCIENTIFIC_VERDICT.md`, `README_REPRODUCE.md` and SHA-256 manifest. Keep private arrays/checkpoints/local batch archives on E:; public upload only after secret/rights scan.
- Scientific outcomes only: `SUPPORTED_WITHIN_DLN_EXPLORATION`, `CONTRADICTED_WITHIN_DLN_EXPLORATION`, `INCONCLUSIVE`, `NOT_TESTED`. This is not a full optimizer speedup paper without multiple training steps and independent nonlinear confirmation.

## 6. Existing sources and code grounding

- PR #16 https://github.com/lyxxx708/hessian-landscape/pull/16 ; NEXT v2 `source_genesis_next_v2/genesis_next/assay.py` and `solvers.py` show train-only alpha selection and old block loop.
- PR #15 https://github.com/lyxxx708/hessian-landscape/pull/15 ; source `genesis_gpu/curvature/operators.py` uses full padded `raw_ggn` for each block, and `genesis_gpu/datasets/registry.py` produces 4096/1024/1024 DLN splits under the same teacher.
- Kronecker approximations for **general neural network Fisher** are not exact: J. Martens & R. Grosse, *Optimizing Neural Networks with Kronecker-factored Approximate Curvature*, ICML 2015, https://proceedings.mlr.press/v37/martens15.html .
