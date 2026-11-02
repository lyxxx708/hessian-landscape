# DLN gauge-structure reimplementation (NEW_REIMPLEMENTATION)

**Evidence class:** `NEW_REIMPLEMENTATION`. Newly written independent code, not original Project GENESIS experiment code. It does not reproduce the original Phase I–VI runs; those inputs remain missing (see `archive/ASSET_MANIFEST.md`).

Analysis and interpretation: [`research/assessment/2026-10-26_VALUE_ASSESSMENT_AND_RESEARCH_PROGRAM.md`](../../research/assessment/2026-10-26_VALUE_ASSESSMENT_AND_RESEARCH_PROGRAM.md).

## Files

| File | Purpose | Runtime (Linux, 2 cores) |
|---|---|---|
| `dln.py` | Analytic gradient, function-space Jacobian, GGN, exact Hessian (with functional term), GL gauge tangent basis, block metrics. numpy only. | — |
| `expA.py` | L=12, d=10, N=32, orthogonal init: null(GGN) = gauge space, closed-form plateau 1/(L−1), exact-H indefiniteness | ~6 s |
| `expB.py` | Phase V-B-like setup (8→12×7→8, depth 8, N=50) trained with L-BFGS: λR vs P₀, exact H vs GGN, gauge-fixed inverse, low-rank capture | ~7 s |
| `expC.py` | Early-stopped at loss ≈ 1e-3 / 5.3e-7: negative curvature lies in the gauge space; λ=1e-8 collapse | ~7 s |
| `expD.py` | 96 exact zero modes of H ("dead-to-dead"); λ sweep across the three regimes | ~6 s |
| `expE.py` | Gauge plateau is invisible to Newton steps and influence scores | ~1.5 s |

Run from this directory: `python expA.py` (expB–E also need scipy). Do not run with `python -I`, because the scripts import `dln` from the same directory.

Validation: gradient and Hessian match central finite differences to 3.8e-10 / 2.2e-10 relative error; J_M · (gauge vector) ≈ 9e-16.

## Logs

- `logs/linux_numpy2.5.3/`: Python 3.13.17, numpy 2.5.3, scipy 1.18.1 (cloud workspace, 2026-10-26). `*.time` files are shell `time` output.
- `logs/windows_numpy2.5.4/`: Python 3.13.14, numpy 2.5.4, scipy 1.18.1, run locally by the project owner. Includes the user-supplied run summary `RUN_REPORT_user_supplied.md`. Two interpretations in that summary are corrected in §3 R5 of the assessment ("pseudo-inverse" should read "damped inverse"; the expC collapse is regime III, not a μ+λ pole).

## Cross-platform note

GGN-derived numbers agree digit-for-digit across the two platforms. For `expB` orth seed 1, both platforms reach the same endpoint (loss 1.18e-16), yet the exact-H λ=1e-8 row differs (0.827 vs 0.8225). This is evidence of regime-II ill-conditioning.

For the gauss and weight-decay runs, the L-BFGS endpoints themselves differ across platforms, so those rows mix endpoint drift with ill-conditioning and are not clean evidence.
