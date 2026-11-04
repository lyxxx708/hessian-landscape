# Known limitations

## Snapshot
- One moment (20:11, 2026-11-04). The run continued afterwards; later results are not part of this evidence version.
- S1 only, DLN only, partially complete. No adjudication of any kind.

## Numerical audit
- FP64 reference ran on CPU; v2 ran on GPU FP32. Device effects and precision effects are not separated.
- FP32 gradient comparison used CPU FP32 as a proxy for the GPU gradient.
- Audit covers 610 of 658 COMPLETE rows; 48 later rows are unaudited. The audit used the frozen utility function with `preconditioner_probes=0` and FP64, plus a dense solve where parameters ≤ 2048.
- Audit compares δ, E_task, E_val, cheap_rho, F*, status and gradient only. Not compared: structure profiles, mechanism records, short/matched-CG gains as predictor features.
- Class thresholds (0.005, 0.01) come from protocol values, chosen before results; they are not a statistical test.
- The 6 MATERIAL rows are one trajectory. The audit cannot estimate an error rate.

## v2.1 qualification
- CPU harness, not the production pipeline. Timings are CPU, with other jobs competing, and are not GPU predictions.
- DLN: 6 settings, seeds 1 and 3, checkpoints 0, 1 and 3, γ-wise results in `dln_variant_summary.csv`. MLP, ResNet, Transformer: one frozen one-step preflight state each (checkpoint from the G0 gate), not trained S1 states.
- A reduced-budget development MLP state (`family_mlp_d6_relu.jsonl`) and smoke runs are included as engineering data, not evidence for the decision.
- First Transformer attempt: every variant hit the 1800 s cap (INCONCLUSIVE). The later long run (V3 only) finished at γ=0.01 and 0.001. γ=0.1 and other variants were not run at long caps.
- The experimental v2.1 source plumbing is uncommitted and intended to be reverted before any v2.1 freeze.

## Provenance and reporting
- An earlier diagnostic report (`FINDINGS_2026-11-03.md`) contains a wrong relative-residual calculation; it is kept unchanged beside its correction.
- The audit scripts and ledger were written by an AI agent from the files in this snapshot; the ledger's numbers are computed by `build_ledger.py`, but the wording of claims and limitations was composed by the agent and should be checked.
- Absolute paths of the author's E: drive appear in receipts and logs. `C:\Users\<name>` paths were redacted; see `EXCLUSIONS.md`.

## Source
- The executed tree differs from PR #14's remote head by seven uncommitted local edits.
- Tests included are the tests of the package; they were not rerun for this snapshot.
