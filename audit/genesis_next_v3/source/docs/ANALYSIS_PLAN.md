# GENESIS NEXT v3 — frozen analysis plan

Binding design: `docs/design_input/EXPERIMENT_PROTOCOL.md` (sha256 `4905e909…3bfc1`). This plan fixes every
selection rule, threshold, label and table *before* the main assay. Qualification pilots (gate 2 states, the smoke
run) are excluded from inference. Evidence class: `POSTHOC_S1_EXPLORATORY_NOT_CONFIRMATION`.

## Panel and units
* Parent denominator: 80 states / 240 conditions (NEXT v2 plan). Assayed: the 38 NEXT v2 NUMERIC_VALID DLN states
  (19 seeds × checkpoints {1,3}) × γ ∈ {0.001, 0.01, 0.1} = 114 conditions. The other 42 states (126 conditions) stay
  `SOURCE_NOT_READY`; the failed seed is not replaced; nothing is imputed.
* Independent unit: the training seed. Checkpoint and γ are paired within seed. V8×128, E8×1024 and T512 32-subsets are
  within-seed resamples, never independent units.
* Absolute λ = γ·max(frozen v2 spectral scale, 1e-8), read from NEXT v2 and checked against the scale.

## Exp V
Pools per seed (one hashed schedule, shared by checkpoints/γ/methods): T32 (v2 batch, replacement sampling), T512
(512 distinct train indices excluding T32), T4096, V1024 = V8×128, E8192 = E8×1024 (new data from the verified teacher,
namespace `GENESIS_NEXT_V3_E8x1024_EVAL_POOL`), Test1024 (original), plus V32_v2 (v2's own validation batch, continuity).
Primary input policy FP32-rounded→FP64; native-FP64 V1024/E8192/Test1024 as a sensitivity column.

Directions on T32: Full (dense FP64 solve), Block (exact Kronecker-direct, best-ray scaled), CG8 (8-step CG, best-ray).
Full α grid `[0,1e-5,1e-4,1e-3,3e-3,.01,.03,.1,.3,1,3]` on every pool, no pruning.

* **Train-only α (deployable):** argmin of measured T32 loss over the original v2 grid `[0,.01,.03,.1,.3,1,3]`, ties →
  smaller α (v2 rule). Called α*.
* **Validation-assisted α (diagnostic only):** argmin over the v2 grid of the mean dL on V-half A (V groups 0–3);
  reported on V-half B (groups 4–7), E8192 and Test1024.
* **Oracle α (upper bound only):** argmin over the full grid of V1024 (and separately E8192) loss.
* **Sign resolution:** every dL has a bound = 2×(max discrepancy among residual-form / product-first-forward /
  naive-difference / fsum paths) + 16 ε Σ|terms|. |gain| ≤ bound ⇒ `NUMERICALLY_INDETERMINATE` (counted separately,
  never as positive or negative). Slope bound analogous (JVP form vs closed-form gradient).

### Labels (non-exclusive) — for each (condition, direction, primary pool P ∈ {V1024, E8192}) whose gain at α* is resolved negative
* `FIRST_ORDER_CONFLICT`: slope s_P = −g_Pᵀd resolved < 0.
* `STEP_OVERSHOOT`: s_P resolved > 0 and some grid α with 0 < α < α* has resolved positive gain on P.
* `CURVATURE_OR_HIGHER_ORDER_MISMATCH`: second-order prediction q_P(α*) = α*s_P − ½α*² dᵀH_P d is > 0 (predicts
  improvement) while the measured gain is resolved negative.
* `BATCH_HETEROGENEITY`: the 8 sub-batches of P (V8×128 or E8×1024) at α* contain both resolved-positive and
  resolved-negative gains.
* `INCONCLUSIVE`: none of the above.
Continuous companions: relative 2nd-order mismatch |G(α*)−q(α*)|/max(|G|,|q|), loss-normalised gain gain/L0_P.

### Pre-specified discriminator statements (evaluated per setting, seed-level)
D1 training-batch bias: T32 gain > 0 but T512/T4096/V1024/E8192 slope < 0. D2 overshoot: positive held-out slope,
negative gain at α*, smaller α better. D3 Taylor mismatch: label CURVATURE… frequency. D4 noise: V8/E8 sign mixing with
weak pooled agreement.

## V4 intervention (fixed: settings d4_orthogonal_balanced_c1 and d8_random_unbalanced_c100; all ready seeds; ckpt {1,3}; all γ)
Same absolute λ. New T512 Full (dense on explicit-Jacobian G, checked against the v2 matrix-free FP64 operator CG — Q0)
and exact Block (Kronecker, checked vs dense) directions; CG8 secondary. Comparisons on common held-out E8192 (V1024
secondary), all with train-only selection:
(a) T32 dir @ α*(T32) [original]; (b) T32 dir @ α*(T512) [step-only rescaling]; (c) T512 dir @ α*(T512) [direction change].
Statement "batch-specific direction error" is SUPPORTED_WITHIN_DLN_EXPLORATION if, at the seed level, (c) repairs the
E8192 sign (resolved non-negative or positive) in a majority of seeds where (a) is negative **and** (b) does not; otherwise
CONTRADICTED / INCONCLUSIVE accordingly. A "repair" that comes from train-only selection choosing α=0 (no step) is
counted and reported separately (`*_alpha_zero_among_a_neg`), as is repair with a resolved *positive* gain. Cost cap per state 900 s; exceeding it → `RESOURCE_CENSORED` (kept in denominator).
Gradient variance: 8 disjoint 32-example subsets of T512 (not seeds).

## Exp B
Methods: exact Block Kronecker-direct (primary), Block Kronecker local-CG (control), old padded Block-CG (implementation
control), Full CG k ∈ {1,2,4,8,16,32,64} with explicit DLN GGNv (primary CG) and with the v2 AD operator (control),
residual stop rules rtol ∈ {1e-1,1e-2,1e-3} (non-oracle). Modes: cold single-γ and warm three-γ.
Policies: (a) raw direction + train-only grid (no Qd), (b) best-ray (+1 charged Qd via explicit cached GGNv).
End-to-end = method + common gradient + line search (6 T32 losses; equal for all).
Timing: 2 threads, fresh process per state, 1 warm-up + 7 randomized-order repeats, each sample ≥ 20 ms by inner repetition.
CV > 10% → `TIMING_INCONCLUSIVE` (excluded from ratio claims, counted).
Comparisons: (1) quality frontier (end-to-end time vs F/F*, both policies); (2) offline oracle: first k with
F_CG ≥ F_B − 1e-4 F* vs Block-direct cost (+Qd if best-ray); (3) F ≥ 0.99 F*: Block rows with F_B < 0.99 F* →
`QUALITY_TARGET_UNATTAINABLE`. Question (d) answered by the seed-level median of cost(CG reaching F_B)/cost(Block-direct).

## Statistics
Seed-level medians per setting and pooled; 95% seed-cluster bootstrap (2000 reps, seed 20261106) for medians of seed
means — descriptive only. No p-values. Outcomes: SUPPORTED_WITHIN_DLN_EXPLORATION / CONTRADICTED_WITHIN_DLN_EXPLORATION /
INCONCLUSIVE / NOT_TESTED.

## Test1024
Computed inside the main run but analysed only after this plan and all code are frozen; reported once for frozen
policies (α*, validation-assisted α). Never used to choose anything.
