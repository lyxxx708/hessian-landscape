# Delegation registry — GPT/Gemini tickets

These are consolidated assignments from historical task prompts; they are specifications, **not execution results**.

## Theory line (T-series)

- T01-A: define layer blocks, S_RMS(k), S_mass(k), effective bandwidth with bootstrap confidence intervals and null controls.
- T01-B: linear residual toy; derive exact parameter Hessian and block-distance prediction; explicitly attempt to falsify the "skip implies pentadiagonal precision" shortcut.
- T01-C: map computational DAG versus parameter-curvature dependency graph and infer only justified sparsity bounds.
- T01-D: design block tri/penta solver with definiteness gating, complexity and test tensors.
- T02-A: prove moral-graph upper bound for linear-Gaussian variable precision, including parameter cancellation/genericity caveats.
- T02-B: distinguish activations and weights; show marginalizing activations can introduce parameter fill-in; construct 5–10-layer counterexamples.
- T02-C: define an order parameter and test whether crossover vs true nonanalytic phase transition.
- T02-D: DenseNet/Transformer low-rank+bande structure predictions with matched-size controls.

## Numerical forensics (N-series)

- N00: minimal reproducible DLN experiment with seed/device/dtype/data/loss/λ/probe options, plots and logs.
- N01-A: matched fp32/fp64 λ scan with backward and forward error, cond and null-run baseline.
- N01-B: small toy mpmath high-precision reference, numerical rank and raw npz output.
- N01-C: LU/inverse/LDLᵀ/MINRES/CG applicability, stopping criteria and matched residual.
- N01-D: Hutchinson samples K with estimator written down, observed CI, bias/variance.
- N02-A: λ-dependent spectrum including nearest pole min|μ+λ|, not just most negative μ.
- N02-B: layer-wise eigenspace localization under degenerate-subspace invariant metrics.
- N02-C: eigen-surgery plus residual retained norm, matched-rank and equal-weight null.
- N03-A: symmetry, definite/indefinite, exact vs GGN and scaling audit.
- N03-B: batch/data/noise/rank/λ phase chart, separate pseudoinverse from shifted inverse.

## Engineering (E-series)

E00; E01-A/B/C/D; E02-A/B as detailed in SMPP_ENGINEERING.md.

## Worker-prompt contract

Every worker must provide:
1. exact code/derivation plus explicit matrix-object definition;
2. input provenance and configuration hash;
3. negative controls and stated falsification criterion;
4. raw machine-readable numerical evidence (or label "not run");
5. uncertainty and conditioning audit;
6. no fabricated plots, logs or PASS judgments;
7. handoff note with unresolved blockers.

## Quality gate

A written narrative that claims execution without code, execution logs, input hashes and full numerical table is DOCUMENTARY_ONLY, regardless of its prose quality or previously assigned PASS label.
