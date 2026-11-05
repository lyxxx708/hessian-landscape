# GENESIS NEXT v1: unfinished work and recovery

Nothing below was started. This file only records what remains and how to resume it. The `ARCHIVED_HANDOFF` status means no one should continue it inside NEXT v1; a new NEXT project may adopt it.

## Unexecuted tasks

| Task | Status | Blocker |
|---|---|---|
| Q0 for DLN (state `41c00898702c…`) | NOT_RUN | v2 worker active; GPU process list not empty |
| Q0 for MLP, ResNet, Transformer | NOT_RUN | no trained v2 checkpoint (setting training PENDING in v2) |
| E1 (Full / Block / short CG / counted-budget CG) on 80 states, 240 conditions | NOT_RUN | needs Q0 pass per family; 38 of 80 states have a trained checkpoint |
| E2 (near-null decomposition, spectral directions, H−G) | NOT_RUN | embedded in E1 |
| E3 (DLN fixed/covariant damping gauge control) | NOT_RUN | sparse DLN subset; needs Q0 |
| E4 (input quantization, arithmetic precision, reference error) | NOT_RUN | embedded in E1 |
| Summarize | NOT_RUN | no results to summarize |

2 DLN states of `dln_d4_w16_orthogonal_balanced_c1` can never run without replacement: v2 seed 0 failed (`Resume provenance mismatch`) and the package forbids replacing seeds.

## Resuming (shortest path to first real results)

All of this needs the owner's decision to pause v2; nothing here is automatic.

1. Cooperatively stop v2: run v2's own `scripts\genesis_stop.ps1`, then confirm both PIDs (73948 launcher, 73000 worker) have exited and the GPU compute list shows no GENESIS process. Do not kill by force.
2. From `E:\GENESIS\delivery\GENESIS_NEXT_v1\GENESIS_NEXT_v1` (or `package\` here, same bytes): `.\START.ps1 -Mode Qualify -Device cuda:0 -MaxStates 1 -ApproveCompute`. This runs DLN Q0 only. Read `results\<state>.json`: every one of the three conditions must be `QUALIFIED` and within the 9.5 GiB memory target for DLN to enter the panel.
3. `.\START.ps1 -Mode Run -Device cuda:0 -MaxStates 4 -ApproveCompute`, repeated until the 38 DLN states are done (about 10 invocations).
4. `.\START.ps1 -Mode Summarize`.
5. Resume v2 with its own `scripts\genesis_resume.ps1`; the environment must come from `genesis_env.ps1` (OMP_NUM_THREADS=2) or DLN resume fails.

Caveat: the `nvidia-smi` listing check may still refuse CUDA after v2 is stopped (WDDM lists unrelated processes). Do not edit the package gate; that changes its hash and invalidates `FOLLOWUP_LOCK.json`. A new project should replace the gate by design.

## Not possible until v2 advances

MLP, ResNet and Transformer panels (40 states) need v2 to finish training their S1 seeds. At the observed pace this is far off (training COMPLETE 52 of 130 on 2026-11-05).

## Open risks

- The adapter has never touched a real checkpoint; the first Q0 is also its first real test.
- Transformer FP64 on GPU is unmeasured; the 3,600 s per-state limit may be too short (CPU needed over 5 h for one condition).
- E0 inputs include the 3 false-valid DLN measurements (flagged MATERIAL); they are retained.
