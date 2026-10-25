# τ_int Anti-Slowing → Regime Mixing / NAO: claim evolution

**This document covers a separate research line from GENESIS/Hessian.** “NAO Genesis Takeover” means authority migration rather than Project GENESIS replication.

## Stage 1: measurement failure in early `lossspike` experiments

The initial 138-run learning-rate / batch-size experiment returned τ_int near 0.52 and interpreted it as a white-noise limit. A subsequent audit in the conversation source reported that the Sokal implementation clipped negative autocorrelations and floored τ at 0.5, while minibatch-resampled loss differences had MA(1)-like negative lag-one structure, training data had extensive unmasked EOS padding, and the scan failed to bracket a divergence boundary. Treat the early 0.52 claim as a measurement artifact, not a negative physics discovery. Original code/raw traces were not independently rerun in this GitHub archive.

## Stage 2: near-boundary anti-slowing and July 6 memo

After revision, the July Scientific Memo reports ~800 runs/~200 GPU h and correlation-time drops as SGD learning rate approaches instability. The memo gives a 16M reference near 80→25 and argues for an apparent one-layer width transition between n_embd=128 and 256; W256 gives τ(η=0.50)=15.8 while W512 gives 3.2. These are **historically reported numerical observations**. They are not sufficient to infer a stationary intrinsic width threshold, Hessian causality, or an optimizer-universal phase transition. See [verbatim parsed-text memo](sources/anti-slowing/2026-07-06_ANTI_SLOWING_SCIENTIFIC_MEMO.md).

## Stage 3: SUPER V4 stationarity audit and pseudo-IAT pivot

The later theory-handoff source says 83 of 85 analyzable trajectories show >2× early/late autocorrelation-time differences. In matched late-window comparisons, the historical W224/W256 separation ceases to be stable. Common nonstationary regimes affect full-trajectory ACF, PSD, spike/noise diagnostics and apparent mediators. The prior mechanism was demoted to **superseded hypothesis**. The global estimate should be called **pseudo-IAT** when no stationarity justification is provided; use local IAT only inside diagnostic-qualified segments.

## Stage 4: regime-mixing / signed-Sokal theory program

The Aug 17 reconstructed NAO takeover report lists:

- Adaptive signed-Sokal first-crossing stochastic criticality, with random O(√T) prefactors at first-order contact, and branch-splitting candidates such as T^1/2 vs T^3/4 at higher order.
- A T^−1/2 local critical layer under specified assumptions; a universal realized threshold-jitter law requires cross-parameter coupling.
- R5 causal stress test: hold optimizer trajectory/local IAT fixed, alter zero-gradient observable regime timing, and obtain global Sokal values from roughly 3 to >600.
- R6 72 MLP+SGD trajectories, run-level Spearman **0.803** for held-out reconstruction.
- R7 96 Digits classification trajectories, run-level Spearman **0.98195**.

These are reported by the historic scientific handoff. R5–R7 were designated **LEGACY_SEEN** for subsequent V2; they are *not* untouched V2 confirmation.

As of the Aug 17 report, the sealed ResNet-18/CIFAR-10 science gate G1 was **NOT RUN**, and ViT-Tiny/CIFAR-100 and DistilBERT/AG News confirmation were **UNTOUCHED**. Nothing in this repository verifies later deployment/experimental success. See the [NAO takeover source transcript](sources/nao/2026-08-17_NAO_GENESIS_TAKEOVER_REPORT.md).

## Stage 5: distinct Oct 2026 WorkBuddy pilot

The Oct 26 four-line report conducts a new synthetic 8-D finite-response Anti test and a new NAO local predictor/surrogate study. They fail or do not qualify their predetermined scientific gates. This should not be merged into the previously reported GPT-2 τ curve or earlier R5–R7 proof program as if one were the replicate of the other.

## Claims and non-claims

- **Documented phenomenon:** Global training-trajectory autocorrelation estimates vary with learning rate, model and regime composition.
- **Supported research direction:** Adaptive estimator behavior under nonstationary regime mixing and reconstructed pseudo-thresholds, conditional on formal assumptions.
- **Not established:** n_embd=256 universal physical threshold; Hessian top mode as causal mediator; global τ necessarily measures a single stationary relaxation timescale; universal cross-estimator Sokal critical exponents; cross-family confirmation completed.
- **No validated GENESIS ↔ Anti mechanism bridge:** inverse-Hessian nonlocality and observable-time estimator behavior remain scientifically distinct.

The [claim register](../catalog/CLAIM_REGISTER_20261026.csv) tags the strongest time-dependent revisions.
