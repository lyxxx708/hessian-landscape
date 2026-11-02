# Maintainer integration QA — 2026-11-02

**Decision scope:** archive a supplied, newly authored DLN/gauge reimplementation and the original contributor's report **without** endorsing its stronger scientific conclusions. The original 23 supplied source/log files and the original report remain unchanged in this review. This is an additive maintainer note.

## What was inspected

- `reimplementation/dln_gauge/dln.py`, `expA.py`–`expE.py`, the three regression tests and the committed independent rerun logs.
- `2026-10-26_INDEPENDENT_IMPORT_REVIEW.md` and its SR-1 through SR-6 limitations.
- GitHub Actions reported success on the PR's previous head `636d750022e4ba9c2271c485369c09ad13f5b382`. This maintainer inspection was **source-level**: it did not independently re-execute the five experiments or re-download historic GENESIS assets.

## Mandatory interpretation gates

1. For finite positive damping, `(GGN+lambda I)^-1` has both a null-projector term and a nonzero horizontal component. Equating it to `lambda^-1 P_null` is valid only as a qualified leading small-damping limit, not an exact finite-lambda identity.
2. The pure GGN null-projector annihilates data-gradient signals, but that alone does **not** prove the entire cross-layer correction or SMPP optimization direction useless; compare the same gradient at the same checkpoint against the best-scaled layerwise direction.
3. Reported negative exact-H eigenmodes are not proven to be entirely attributable to gauge structure. Raw sign tests for near-zero eigenvalues are numerically unstable unless a tolerance and a near-zero bucket are defined.
4. The claimed damping regimes must state spectral separation and pole restrictions; at large damping `lambda(H+lambda I)^-1 -> I` for a fixed matrix, not to a fixed non-identity gauge projector.
5. The proposed pseudo-Goldstone `F_S` fraction and large dense eigensolve budget are **unqualified proposals**, not verified results.

## Reproduction boundaries

- Core tests use NumPy and are part of the repository unit-test suite.
- `expB.py`–`expE.py` additionally import **SciPy**, which is not in the top-level NumPy-only `requirements.txt`. For an optional experiment environment, install both NumPy and SciPy in an isolated environment (for example `python -m pip install numpy scipy`) and record exact package versions and BLAS threading in the output. This is not a fully pinned reproducibility lock.
- No original 2025 Phase IV/V checkpoint, full original matrix, historical logs, held-out trial, or nonlinear-network validation was recovered by this PR.
- Some supplied logs contain local Windows paths. Their presence does not imply a credential scan proves every secret absent; review public-data suitability before wider sharing.

**Merge meaning:** accepted as *archival original-source material with independent scientific caveats*, NOT SCIENTIFIC_ACCEPTED or a verified theoretical proof. Any future claim promotion requires separate, versioned experiments and independent validation.
