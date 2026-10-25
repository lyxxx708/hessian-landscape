# Scientific claim ledger and audit blockers

This file is deliberately conservative. It prevents earlier review prose from being mistaken for verified measurements.

| ID | Candidate statement | Current assessment | Required check |
|---|---|---|---|
| C01 | Exact H indefinite at certain orthogonal initialization checkpoints | PLAUSIBLE / REPORTED | original eigenvalue logs, loss checkpoints |
| C02 | FP32 pseudo-sparsity is caused by condition-number precision loss | PLAUSIBLE / REPORTED | same-matrix fp32/fp64/mpmath solve & forward error |
| C03 | DLN inverse block-distance spectrum exhibits 0.09–0.12 plateau at L=12 | REPORTED / UNVERIFIED | raw block energies and per-seed curves |
| C04 | Same L12 matrix has 39% offdiag mass | **CONFLICT** with C03 under common RMS metric | align run IDs; independently recompute S_RMS and mass |
| C05 | 0.012% offdiag at L6 B4 is nullspace projection | HYPOTHESIS | correct H/GGN rank, λ sweep, decomposition of diagonal λ⁻¹I term |
| C06 | Near-zero residual exact H≈GGN with gap 1.53e-4 | REPORTED | scaling and exact Hessian decomposition |
| C07 | Cut modes explain almost all offdiag signal | **METRIC NOT CAUSAL PROOF** | retained residual fraction, subspace size, matched nulls |
| C08 | H_off top (L−1) singular modes capture 44.2% energy | REPORTED | singular spectrum and holdout stability |
| C09 | Exact H+0.1I non-SPD at Rev4 initialization | REPORTED / STRONG DESIGN IMPLICATION | eigenvalue logs and residual |
| C10 | SPD matrix-decay theory fails universally for exact Hessians | **INVALID OVERGENERALIZATION** | replace with "SPD-only theorem inapplicable at this checkpoint" |
| C11 | ReLU fixed gates imply H=GGN | **MATHEMATICALLY FALSE GENERALLY** | exact cross-layer derivative counterexample |
| C12 | Branch Phase VII Path B GGN geometry has passed arbitration | NOT RUN | full experiments |
| C13 | SMPP tri/penta solver or CUDA kernel outperforms AdamW | NOT RUN | code, end-to-end timed benchmarks |
| C14 | Gauge transformation preserves raw Hessian blocks | UNSUPPORTED | reparameterization tensor transformation analysis |

## Blocking discrepancy D01 — plateau/mass bounds

If S_RMS(k)/S_RMS(0)≤0.12 for all off-diagonal layer distances k, then at L=12 OffDiagMass ≤ 13.67%. Historical report quotes 39% for the same described setting. Both numbers cannot be accepted as measurements from a single consistently normalized block-RMS partition; identify exact run/data/normalization differences.

## Blocking discrepancy D02 — spectral surgery interpretation

Norm(R_cut,off)/Norm(R,off)→1 as cut includes almost all modes is *not* itself evidence of a few dominant modes. Ratio lacks Pythagorean interpretation after masking, and can exceed 1. Need captured **retained residual** and mode fraction and pairwise cross term decomposition.

## Blocking discrepancy D03 — nullspace versus low-rank

P≫N·D_out is a loose dimensional argument; for linear input/output factorization rank(J)≤d_in d_out, possibly much tighter. The near-null subspace may be high-dimensional. Woodbury applicability requires rapid singular-value decay of the **target residual**, not only large nullity.

## Blocking discrepancy D04 — solver accuracy

Relative residual ≈1e−12 demonstrates small backward error; it does not alone establish small forward error if conditioning is extreme. Record condition estimate and high-precision references; ensure A=H+λI has no eigenvalue close to 0.

## Evidence promotion gates

- DOCUMENTARY_ONLY → RECORDED_PRIOR_PASS: obtain original code, config, raw logs/figures and unaltered archive checksum.
- RECORDED_PRIOR_PASS → FRESH_PASS: run exact code (or separately labeled reimplementation) now, capture environment and independent verification.
- THEORY_CANDIDATE → THEOREM: provide explicit assumptions and complete proof.
- Engineering claim → BENCHMARKED: identical training budgets/hardware, timed wall-clock, statistical error bars and strong baselines.

No claim in this repo is labeled fresh pass as of this archive creation.
