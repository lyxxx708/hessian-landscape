# GENESIS fresh large-scale revalidation — protocol v1

**Date:** 2026-11-02. **Status: DRAFT_NOT_FROZEN / NOT_EXECUTED.**

**RTX 4070 Ti local execution override (same day, still not executed):** The operational finite grid, 4 checkpoint fractions, 26 S1 settings × 5 training seeds and five mandatory S2 anchors × 16 new seeds are defined by [LOCAL_4070TI_FULL_V1.json](LOCAL_4070TI_FULL_V1.json), [primary endpoints and freeze rules](PRIMARY_ENDPOINTS_AND_FREEZE_RULES.md) and [Codex local Goal](CODEX_LOCAL_4070TI_GOAL.md). Earlier illustrative sizes or stage counts lower in this document are superseded for the local full-run contract. No scientific run results have been viewed when authoring this override.
 This protocol makes no claim of experimental validation or authorization to spend compute, use private datasets, or expose sealed holdouts.

## 0. Retire the old evidence; preserve its provenance

The original 2025 Phase IV/V matrices, checkpoints, run IDs and full logs are unavailable. The reported 0.09–0.12 layer-RMS plateau and 39% offdiagonal energy are mutually incompatible for one L=12 equal-block inverse under the same metric. **Treat all historical plateau values as RETIRED_AS_EVIDENCE, not the new study target.** Do not delete or rewrite the original archive. No further historic-file recovery is required for this prospective study.

The 2026 three-seed orthogonal-DLN P0 results are **new synthetic analytic controls only**, not confirmation of a law in naturally trained nonlinear networks.

This plan complements, but does not relabel as completed, the earlier [task-coupling protocol](../genesis/2026-10-26_EXPERIMENT_PROTOCOL_AND_GO_NOGO.md) and [G0–G4 utility contract](../strategy/2026-10-26/EXPERIMENT_CONTRACT.md).

## 1. Three independent questions

**S — Structure:** On real training trajectories, under what architecture/scale/damping conditions do distant layer blocks of the damped inverse GGN or exact Hessian decay, remain near-flat, or behave otherwise? Distinguish (i) flatness *within* finite L from (ii) a nonzero magnitude as L grows. A flat tail proportional to 1/L is NOT a nonvanishing asymptotic plateau.

**M — Mechanism:** Separate shared Jacobian Gram, rank deficiency and nullspace projectors, gauge/parameter-scale effects, exact-H residual curvature, and spectral-pole amplification. A masked-eigenvector norm change alone is not a causal explanation.

**U — Task value:** At the SAME loss, batch, checkpoint, gradient and damping, can full damped GGN provide material quadratic-update benefit beyond a *best-scaled* precise layerwise-GGN direction? Could a cheap predictor estimate the benefit? Only then test real optimizer wall-clock performance. S may be worth publishing as a sharply conditional theory/negative result even if U is NO-GO; S alone cannot justify an optimizer.

## 2. Fixed numerical contract

For loss-specific GGN, define G = J_f^T H_out J_f (PSD), Q = G + λI (SPD for λ>0), D = blockdiag(G) + λI, g = grad(loss). For squared loss with recorded 1/(2M) reduction, G=J^T J/M. For cross-entropy, include the output-loss Hessian; **do not confuse GGN with empirical Fisher**. Record regularization separately.

For structure, each layer block R_ij of R=Q^-1 has squared Frobenius energy e_ij=||R_ij||_F^2. Save all distance-bin energies E_k=sum_{|i-j|=k} e_ij, non-diagonal energy fraction and normalized block RMS. For unequal-sized blocks, use per-element RMS sqrt(E_k / sum_{|i-j|=k} n_i n_j); retain the original equal-block metric only for equal sizes. Declare parameter grouping, biases, norm and skip ownership.

For utility, p* = -Q^-1 g and pB = -D^-1 g; α* = -g^T pB/(pB^T Q pB), F* = -g^T p*/2 and FB = (g^T pB)^2/(2 pB^T Q pB). The primary quadratic-model regret is Δ=1−FB/F*. Record separately E_task (best-scaled training-output Jacobian response error) and E_val (validation output-response error using the TRAIN-fitted scale). Alpha* is an **offline oracle scalar**, not a free online learning rate. Flag g≈0, denominator≈0, failed CG or ill-conditioning as INELIGIBLE; never assign Δ=0.

For the exact Hessian H, do NOT assume H+λI SPD or H=GGN for fixed ReLU gates. Exact-H inverse phenomena are the separate mechanism lane, and SPD update comparisons require independently justified safe positive damping. Report forward accuracy when feasible, not just small backward residual.

## 3. Staged experiment matrix

| Stage | Setting and statistical unit | What qualifies as evidence |
|---|---|---|
| G0: correctness + time/VRAM preflight | Independent fresh DLN L=4/8/12, tiny MLP; numerical finite differences, independent autodiff, dense vs matrix-free GN, exact inverse vs Rademacher block sketch; dry-run seeds excluded from science | Correct objects and normalization; residual, spectrum, block-energy identities, data/metadata hash all pass. STOP on a mismatch |
| S1: exploratory discovery | DLN L=4/8/16, balanced/unbalanced and widths 16/32; MLP 3/6/12 layers width 128; small ResNet/CIFAR-10; Tiny Transformer on a licensed small text corpus. **5 independent training seeds per frozen setting**; checkpoints at fixed fractions 0/0.5/1 of budget; γ=λ/max(||G||_2,s0) in {1e-3,1e-2,1e-1} | Full all-seed/all-λ curves, S mechanism controls, U regret distribution, failures and runtime. Checkpoints and λ within seed are correlated repeats, not more independent n |
| S2: locked confirmation | At least one vision and one text model family plus separate DLN depth extrapolation; model choices follow a PRE-FROZEN selection rule; **16 new independent seeds per selected condition (local full-run override; earlier draft proposed 8)** | Pre-registered null comparisons, seed-cluster confidence intervals, negative cases and uncertainty. One confirmatory pass only |
| S3: optimizer qualification (conditional) | Only after task-value and predictive gates pass. Precise layerwise GN, full GN offline oracle (small only), budget-matched CG, AdamW, SOAP/K-FAC as applicable, and Gradient Smoothing | Matched tuning/data/token/compute budgets; actual wall-clock time-to-target and fixed-budget quality including every curvature/matvec cost |

The above is the **target envelope, NOT completed runs**. Freeze seed schedule, dataset splits, layer-group definitions, optimization budgets and model sizes BEFORE any S1 scientific results. First benchmark a 12GB-class device or available cloud GPU in G0, publish projected GPU-hours and maximum memory per setting, and modify infeasible sizes only **before** S1; never quietly drop a slow/negative model after seeing results. S2 seed lists and private data remain sealed until pre-registration and access approval.

## 4. Matrix-free scaling method

Use verified JVP/VJP and the loss-output Hessian to calculate GGN-vector products. PyTorch torch.func.jvp/vjp are candidate primitives, but unsupported forward-mode operators need tested fallbacks. Validate dense full-GN and block-GN solves first. For large SPD Q, use matrix-free CG with explicit convergence residuals and condition diagnostics, and a comparably accurate layerwise solver — not an Adam diagonal step mislabeled precise layerwise GN.

To estimate inverse layer-block Frobenius energies without materializing P×P, for each source block j draw zero-mean Rademacher probes z supported only on block j; solve Qx=z; E[||x_i||²] = ||(Q^-1)_ij||_F². Log probe counts, random seeds, Monte Carlo uncertainty and solver errors. Compare against exact dense block energies in G0, and distinguish sampling uncertainty from variation between independent training seeds. For large exact-H, use validated HVP/Lanczos on an appropriately qualified subset; a Lanczos extremal estimate alone is not a proof of SPD.

## 5. Controls and falsification

- Balanced orthogonal DLN and rank-one toy: expected flat finite-distance shape and possible ~1/L decay. These are **negative novelty controls**.
- Actual fixed-target training trajectory versus artificial zero-residual target replacement (the latter is not training dynamics).
- Fixed H/G and g with λ sweep; gradient and matrix must remain from the same loss checkpoint. Monitor min|eig(H)+λ| and conditioning, so pole effects cannot be sold as new physics.
- Layer-distance null: joint row/column block permutation preserves spectrum but randomizes architectural order. For U, simultaneously permuting matrix and gradient is a coordinate relabeling and cannot demonstrate altered value.
- Rank-matched spectral/random-subspace nulls, multiple widths, anisotropic input covariance, balanced vs unbalanced layers, gauge-preserving rescalings and comparable parameter counts.
- For depth laws, compare a constant-height candidate with 1/L, 1/sqrt(L), exponential and power-law alternatives **on new depths**. Do not assert a nonzero L→infinity limit from finite-depth flattening.
- Predeclare negative-result reporting, missing/invalid record handling, Monte Carlo error, model-family/seed-cluster bootstrap units and multiple-test interpretation.

## 6. Go / No-Go decisions

**S GO:** an independently validated, conditional effect beyond matched nulls persists on unseen training seeds, at more than a single orthogonal-DLN setting and under specified damping/parameterization choices. **S FAIL:** flatness or energy disappears after geometry-null, normalization, or conditioning controls; stop claiming a general long-range plateau. A conditional negative or no-universality result is acceptable.

**U GO:** the task-value and predictive thresholds in the pre-existing G1/G2 contract hold on natural checkpoints and independent seed groups; a cheap predictor beats λ/scale, gradient norm, block energy, condition proxies and same-cost short CG. If Δ is uniformly tiny (around <0.01), or only appears at unstable poles, stop optimizer engineering regardless of S.

**S3 GO:** real optimizer benefit under preregistered compute-adjusted wall-clock and quality criteria, with strong baselines and failures published. A high off-diagonal norm, a toy eta value, or CI PASS are insufficient.

## 7. Immutable evidence ledger

Every run must save: protocol + git/source/config hashes; model checkpoint and data-split hashes; seed cluster; stage; architecture; parameter block order/sizes; exact loss and reduction; regularization; absolute/relative damping; matrix type and dtype; solver precision/residual/conditioning; probe counts and uncertainty; all distance energies, η, Δ, E_task/E_val, ineligible reasons; runtime/peak VRAM; manifest SHA-256. Keep unsuccessful and invalid runs.

Evidence labels: DESIGN_ONLY → G0_VALIDATED → EXPLORATORY_EXECUTED → HOLDOUT_FROZEN → CONFIRMATORY_PASS / CONFIRMATORY_FAIL / NUMERIC_INVALID. **Nothing in this PR is a new S1/S2/S3 result.** Do not push private data, credentials or unapproved holdouts to the public repository.

**Execution order:** validate math and the inverse-block sketch; run a resource preflight; freeze protocol and seed allocation; execute exploratory runs; independent review; execute sealed confirmation once; only then consider new optimizer engineering.