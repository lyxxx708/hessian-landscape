# P0 independent DLN audit — 2026-10-26

**Evidence class: NEW INDEPENDENT REIMPLEMENTATION. Not a replay of historical GENESIS Phase IV/V.** No historical code/checkpoint/full raw matrices have been recovered. Original claims remain DOCUMENTARY_ONLY and the 0.09–0.12 / 39% common-metric discrepancy remains unresolved.

## Protocol

A 12-layer bias-free width-10 deep linear network (1200 real parameters), QR orthogonal initialization times 0.95; N=32 Gaussian samples; deterministic seeds 20261026, 20261027, 20261028. At identical weights per seed, compare (a) identity target (nonzero residual, initial) and (b) target equal to current predictions (synthetic zero-residual condition). This is **not a training trajectory**. Loss is 0.5*mean(residual**2); explicit exact H, GGN=J^T J/(N*d), functional second-order residual S, damping lambda=1e-3, FP64 eigenbased inverse. Layer-pair RMS and energy use 100x100 blocks, both upper and lower off-diagonal triangles, 12 distance bins.

## Commands

    python -m pip install -r requirements.txt
    OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m unittest discover -v
    OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m scripts.p0_repro --all --out results/p0_fresh
    # For full matrices (large outputs; review before public release):
    OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m scripts.p0_repro --all --save-full --out results/p0_fresh_raw

Each run emits summary JSON, layer-distance CSV, 12x12 block norms for inverse/H/GGN and eigenvalue spectrum CSV. Per-file SHA-256 values are in JSON. The optional PyTorch unit test checks analytic H against independent autodiff at small scale (skips if torch is absent). A separate full-size numerical gradient finite-difference test and two independently authored implementations were additionally executed in the companion local experiment archive.

## Recorded independent results

| seed | condition | rank(J) | negative eig(H) | eigmin(H) | cond(H+lambda I) | offdiag mass of inverse |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 20261026 | initial | 100 | 597 | -0.992895 | 13074.9 | 86.6215% |
| 20261026 | zero_residual | 100 | 0 | ~0 | 867.50 | 8.2767% |
| 20261027 | initial | 100 | 602 | -0.920865 | 267616.8 | 85.4339% |
| 20261027 | zero_residual | 100 | 0 | ~0 | 764.44 | 8.2650% |
| 20261028 | initial | 100 | 606 | -0.899163 | 56459.5 | 89.6133% |
| 20261028 | zero_residual | 100 | 0 | ~0 | 753.40 | 8.2703% |

Zero-residual cases exhibit exactly flat k>=1 Frobenius layer-distance ratios to ~1e-15, at 0.090502–0.090571. Same-size scaled orthogonal layers have Jacobian blocks J_i=J_0 O_i with orthogonal parameter-space O_i. The Woodbury identity gives identical off-diagonal block Frobenius norms for all distances. This is a known algebraic alternative to an asserted novel phase transition.

For L=12 equal-sized blocks with max offdiagonal distance-bin RMS ratio <=0.12, the exact consistency bound forces offdiag energy mass <=13.6740%; a same-run value 39% would be contradictory. Historical original source files are still needed to determine whether different runs or metrics were combined.

**Gates:** no historical claim promotion, no causal or generalization conclusion, no optimizer-performance claim. This establishes an internally checked synthetic P0 baseline. Next: recover original source/checkpoints to audit their same-run metrics, sweep damping lambda and held-out seeds, and test nonorthogonal/gauge controls.

## Files

- scripts/p0_repro.py: independent full Hessian, GGN, spectra and block metrics runner.
- tests/test_p0_repro.py: rank, PSD, energy consistency and optional torch autograd cross-check.
- archive/P0_NEW_RUNS_20261026.csv: numerical outcomes and gates from the separately executed, larger independent baseline.
