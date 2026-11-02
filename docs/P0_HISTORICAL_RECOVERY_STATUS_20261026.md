# GENESIS P0 historical Phase IV/V recovery status — 2026-10-26

**Evidence verdict: ORIGINAL_2025_DLNV_MATRIX_AND_CHECKPOINT_NOT_RECOVERED.**
This is a scope-limited result of an actual multi-source file-name and manifest search, not proof that the files were deleted or never existed. **Do not change C03/C04 historical claim grades.**

## Sources checked

1. All seven branches and the initial (2026-10-25) Git history of `lyxxx708/hessian-landscape`: 2025 original 12-layer DLN code, raw matrices and checkpoints absent.
2. WorkBuddy 2026-10-26 release and archive branch `archive/workbuddy-fourline-20261026`; indexed the 2,024-content-member `archive/workbuddy-fourline-2026-10-26/FILE_MANIFEST.csv`. No `results_phase_v.pkl`, `results_phase_v_b.pkl`, `phase_v_log.json`, `dln_rebuttal.py`, `genesis_rev4_final.pkl`, or `dln_*` file. The index DOES identify 2026 GENESIS v4 `project/records/science_v4/.../genesis/bundle/model_checkpoint.json` (87,675 bytes, SHA-256 `57fb4bd2096a420fb37705039b658956309d0a2c59da06c0c6a507e24ff39120`), but that is a **different** 2/4/8-layer residual-model experiment; it cannot verify the historical L=12,width=10,batch=32 DLN curve.
3. Connected Library, Google Drive and mail searches, using exact original filenames/terms: no original Phase IV/V binary matrices, source scripts or checkpoint located. Connected sources do not cover every historical desktop or legacy chat.
4. The known WorkBuddy original ZIP was reported and source-side hashed on a Windows workstation, but that package's indexed scope is from **2026** experiments. Its existence does not restore the 2025 matrix.

## Strict common-metric algebraic audit

For L identical-sized blocks, let
`n_0=L`, `n_k=2(L-k)` for `k>=1`,
`S(k)=sqrt(sum_{|i-j|=k} ||R_ij||_F^2/n_k)`,
`C(k)=S(k)/S(0)`, and
`M_off=(sum_{k>=1} n_k C(k)^2)/(L+sum_{k>=1} n_k C(k)^2)`.

For **the same matrix and same metric**, if all `C(k)` (k=1..11) lie in `[0.09,0.12]`:
- `0.08181066936 <= M_off <= 0.13674033149` (8.18%–13.67%).
- The historical statement `M_off=0.39` is **mathematically incompatible** with this interval.
- To have `M_off=0.39`, at least one distance-bin ratio must be `>=0.24108547377`.
- Even if `C(k<=11, k>=2)<=0.12` while `C(1)` is free, `C(1)>=0.52605440211` is required. Archived Phase V text reports `C(1)~0.09`, which does not rescue compatibility.

No raw historical run identifier, energy table or checkpoint has been recovered, so **which report number/normalization is wrong remains unknown**. It is incorrect to label the historical true plateau height either 0.09–0.12 or 0.241; the latter is a *necessary bound under the 39% claim*, not a measured historical value.

## Independent test control, NOT historical reproduction

The NEW synthetic P0 12-layer DLN at zero residual gives precisely flat `C(k>=1)~0.0905` and `M_off~0.0827`, under the same binning definition. This shows that such a low-height plateau is algebraically realizable without proving the 2025 experiment. See `docs/P0_EXPERIMENT_20261026.md`.

## Ready-to-use future audit

- `python -m scripts.strict_plateau_audit --claims-only` reproduces the bound and the contradiction.
- `python -m scripts.strict_plateau_audit --npz /verified/original.npz --key R` audits a recovered inverse matrix, defaulting to 12 equal blocks of 100 parameters.
- `python -m scripts.strict_plateau_audit --block-norms-csv /verified/original_block_norms.csv` audits an original **12x12 block-norm CSV** without needing the full inverse.
- The script uses `np.load(..., allow_pickle=False)`; never deserialize `.pkl` or `.pt` from unknown origins just to inspect its contents.
- For a checkpoint alone: require the exact architecture, dataset, loss reduction, target, checkpoint state, parameter ordering, damping and dtype, then reconstruct exact H/GGN with independently verified derivatives before calling it a recovery.

**Promotion gate:** at least one original, hash-verified run with shared `run_id`, checkpoint + configuration + `R` or full block norms; recompute **all 12** distance RMS bins, per-bin squared energy mass, total offdiag, conditioning, exact-H vs GGN and solver residual. If incompatible, supersede reported values rather than blending different runs.

## Source references

- [Original archive manifest](https://github.com/lyxxx708/hessian-landscape/blob/archive/workbuddy-fourline-20261026/archive/workbuddy-fourline-2026-10-26/FILE_MANIFEST.csv)
- [Original archive Release](https://github.com/lyxxx708/hessian-landscape/releases/tag/archive-20261026)
- [Historic Phase I-V reconstructions](https://github.com/lyxxx708/hessian-landscape/blob/main/docs/PHASES_I_V.md)
- [Claim ledger](https://github.com/lyxxx708/hessian-landscape/blob/main/docs/CLAIMS_AND_AUDIT.md)

**Never represent the separate 2026 model_checkpoint.json as the 2025 Phase V L12 matrix.**
