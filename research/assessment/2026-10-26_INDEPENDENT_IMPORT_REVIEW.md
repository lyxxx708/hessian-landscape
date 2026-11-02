# Claude DLN gauge reimplementation: import provenance & independent scientific review

**Date:** 2026-10-26 (Asia/Singapore)  
**Class:** INDEPENDENT_IMPORT_AUDIT / REVIEW_ONLY — not a substitute for the source report and not a theorem certification.  
**Contributor manuscript:** [2026-10-26_VALUE_ASSESSMENT_AND_RESEARCH_PROGRAM.md](2026-10-26_VALUE_ASSESSMENT_AND_RESEARCH_PROGRAM.md) (Claude Opus 5.5; preserve its original wording).  
**Code:** [reimplementation/dln_gauge/](../../reimplementation/dln_gauge/README.md).  
**Comparison:** independently authored [GENESIS research value decision PR #7](https://github.com/lyxxx708/hessian-landscape/pull/7). The two analyses are distinct; neither supersedes the other.

## 1. Source custody and byte-level checks

Two user-supplied inputs were examined *as received*:

| Source | SHA-256 | Disposition |
|---|---|---|
| `2026-10-26_VALUE_ASSESSMENT_AND_RESEARCH_PROGRAM.md` | `943e72dd392c4faadb2167d60f1e6b982b9181c6a1f6971f43dd99fc82571c0f` | Standalone report **byte-identical** to report embedded inside patch. One canonical report committed. |
| `0001-gauge-value-assessment.patch` | `c6c76f8f5004c3067301c8cf1666990765f4a4126428018040d4ecd2e5569ccc` | Applied as a **25-path patch** (23 additions, 2 README insertion-only updates). Patch itself not duplicated as a second 85-KB source document; its content is represented by the committed Git diff. |

Every one of the 23 added-file Git blobs was created using the attached patch's original bytes, then checked against the **exact 40-character blob SHA computed before transfer**. Both README resulting Git blob hashes matched the patch's expected hashes (`6abcb23` and `f9a23d8`). The source report, code and original Linux/Windows logs have not been rewritten.

This import intentionally **does not** recover historical 2025 GENESIS Phase IV/V sources; `NEW_REIMPLEMENTATION` does not mean `HISTORICAL_REPRODUCTION`. The supplied Windows local-run note contains local Windows account paths; no credential-shaped values or executable network/remote-write operations were found by a limited textual scan. Since the repository is public, the owner should still review disclosed local paths before merging.

## 2. Checks actually executed in the import environment

- **Environment used for independent replay:** Python **3.13.5**, NumPy **2.3.5**, SciPy **1.17.0**, OpenBLAS and OpenMP threads constrained to 2.
- **Three new tests:** `OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m unittest discover -s tests -p 'test_dln_gauge_reimplementation.py' -v` → **3/3 PASS**.
- **Five new experiment scripts:** `expA.py`, `expB.py`, `expC.py`, `expD.py`, `expE.py` each executed to completion with **exit status 0 and empty stderr** in this environment. Their exact outputs are retained separately under [independent rerun logs](../../reimplementation/dln_gauge/logs/independent_python3.13_numpy2.3.5_scipy1.17.0/).
- **Reproduction nuance:** these replays generally support the supplied *new synthetic* qualitative trends, but are **not byte-identical** to the supplied Python 3.13.17 / NumPy 2.5.3 / SciPy 1.18.1 logs:
  - `expA`: the gauge projection norm differs in its tiny ~1e-14 residuals; the displayed plateau and mass agree.
  - `expB`: at orthogonal seed 1, exact-H, λ=1e−8, k=1 ratio from supplied log **0.8270**, our replay **0.8247**; this is a numerically delicate point, not an independent reproduction of precisely identical values.
  - `expC`: raw `w<0` negative-eigenvalue counts differ by several eigenvalues across environments (e.g. 504 vs 503); the script counts arbitrarily small negative roundoff values as negative. **Do not use these exact counts as robust scientific integers** without a fixed spectral tolerance and a near-zero bucket.
  - `expD`: the approximately 96 exact/near-zero structural modes and qualitative λ regions remain visible; several small numerical values differ.
  - `expE`: gradient projection ratios show small environment-dependent changes; reported 50-point influence-rank Spearman remains +1.000.

**Not checked:** full original GENESIS pipeline, source Windows environment, older source tests across all Python versions, actual raw 2025 matrices/checkpoints, generalization to nonlinear neural networks, and publication/novelty certification. The source's third-party literature claims were not independently verified line by line in this import.

## 3. Mandatory scientific limitations before interpreting the source's strong conclusions

### SR-1 — Finite-λ GGN inverse is *not exactly* λ⁻¹ times the gauge projector

For positive semidefinite G with orthogonal null projector P₀:

```math
(G+\lambda I)^{-1}
=\lambda^{-1}P_0
 +\sum_{\mu_i>0}(\mu_i+\lambda)^{-1}v_iv_i^\top.
```

The second, horizontal term is nonzero for finite λ. Only in the limit λ→0 at **fixed G with separated nonzero eigenvalues** does λ(G+λI)⁻¹→P₀. Equality `null(G) = gauge tangent` also requires a full-rank regularity hypothesis; the supplied weight-decay/rank-63 example itself has a one-dimensional extra null direction. Therefore the executive wording "the GGN platform equals λ⁻¹ times the gauge projector independently of data/loss" needs scope restrictions. The **projection-limit formula** is a valid important baseline; universal finite-λ equality is not established.

### SR-2 — Invisibility of the *GGN null projector* does **not** justify abolishing all global curvature correction

For the data-gradient g=Jᵀr/M, `P₀g=0`; since P₀ and G commute, the pure λ⁻¹P₀ contribution vanishes from GGN-gradient bilinear quantities. This is rigorous **for that exact null term**. However:
- The horizontal correction in the same full inverse can carry material cross-layer coupling when applied to g.
- Block-diagonalizing *curvature before inversion* differs from deleting the non-diagonal blocks of the *already inverted* matrix.
- The exact H with residual term S can mix horizontal and gauge tangent directions. The source's own `expE` reports `‖P₀(H+λI)⁻¹g‖/‖(H+λI)⁻¹g‖≈1` at several λ settings.
- A straight parameter-space step tangent to a gauge orbit is not the same as integrating an exact function-preserving gauge path over a finite step.

Thus it is justified to deprioritize a **gauge-platform-only** explanation, but **not** mathematically justified to declare that the entire SMPP research direction or every task-relevant cross-layer correction has zero value. Compare [PR #7 task-related update tests](https://github.com/lyxxx708/hessian-landscape/pull/7) before a final cancellation decision.

### SR-3 — Hessian negative curvature ≠ automatically "entirely from gauge"

The gauge orbit identity `ξᵀHξ = −gᵀγ″(0)` for a symmetry curve γ(t) is exact; it does not prove all negative eigenvectors are inside the gauge tangent, nor that all off-gauge restrictions are PSD. The supplied `expA` finds **95.9–96.4%**, not 100%, of negative eigenvector energy inside the gauge tangent. Accordingly phrases such as "completely due to gauge orbital curvature" are **theory candidates** with unproven additional hypotheses, not established theorems.

### SR-4 — The "three regimes" require multiple spectral scales

The statement `λ≫μ_max` alone cannot imply `λR→P₀`: as λ→∞ for any fixed finite H, **λ(H+λI)⁻¹→I**, not P₀. An *intermediate* projector-like window requires an additional separation from the nonzero horizontal eigenvalues, and the sign and location of negative-H poles must be checked. The small-λ exact-H limit (away from poles and for fixed finite H) approaches the **exact H null projector**, not automatically the full GGN gauge projector. These qualifications must accompany P6 and any Phase VII "outcome predicted a priori" claim.

### SR-5 — Q1 pseudo-Goldstone mechanism and proposed experiment still lack a unique operational test

The candidate approximate-symmetry subspace need not be invariant under G or H. A projected Rayleigh quotient distribution is not automatically a decomposition of resolvent sensitivities, and influence-function derivatives are signed bilinear forms with cross terms. A scalar "`F_S` explained fraction" is therefore not well defined until one specifies a projector, cross-term allocation, norm or signed objective, and denominator treatment. Spectrally matched random-subspace controls are necessary but do not repair an undefined estimand.

Also, the proposed M1 has about **20,000 parameters**. One dense FP64 20k×20k matrix occupies approximately **3.2 GB** before eigensolver workspace; full eigendecomposition is cubic-time. The claimed ~10 min per CPU configuration should be treated as **unbenchmarked** without a matrix-free or dual formulation. The `O(P)` cost claim for analytic gauge projection likewise depends on the basis, rank and chosen projector solver.

### SR-6 — Statistical and publication claims are proposals or judgments, not measured facts

- Spearman +1.000 over one 50-point influence ranking is a **local diagnostic**, not a general robustness result.
- The reported "<5%" main-conference acceptance probability is **the author's subjective prediction**, without an empirical calibration; should not be cited as a frequency estimate.
- PR-1…PR-5 and the Q1 kill-test criteria are **pre-registered proposals**, not pre-registered confirmatory experiments executed on held-out data.
- Source's "GAUGE accounts for 100%" language requires constant loss/gradient/regularization definitions and meaningful scale tolerance before extrapolation.

## 4. Recommended decision for the maintainer

**Import recommendation: RETAIN AS ORIGINAL SOURCE + LABEL ANALYTICAL DISAGREEMENTS.** The source is valuable as a runnable fresh reimplementation with a strong analytical viewpoint. Preservation is warranted; endorsement of all conclusions is not.

**Merge gate:** review SR-1 through SR-5 and the existing [PR #7](https://github.com/lyxxx708/hessian-landscape/pull/7), decide how the two research hypotheses relate, and request reproducible dependencies (SciPy is needed for expB–E but absent from main `requirements.txt`). Existing notebooks/figures/old matrices are not restored by this PR.

**Publication gate:** do not mark main-conference readiness or historical confirmation based on these reports alone. Any future authoritative status update belongs in a separate, explicitly dated evidence ledger; historical reports remain unchanged.
