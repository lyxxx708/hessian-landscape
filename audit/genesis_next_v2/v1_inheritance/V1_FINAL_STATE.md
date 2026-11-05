# GENESIS NEXT v1: final state

Status: **ARCHIVED_HANDOFF**. Written 2026-11-05 23:15 (UTC+8). No NEXT v1 development or experiment follows this document.

## What NEXT v1 is

An exploratory, S1-only follow-up to GENESIS v2 (`evidence_class` `EXPLORATORY_S1_FOLLOWUP_NOT_ORIGINAL_V2`). It asks where the chain "complex curvature structure → complex update → expensive solve" holds or fails, using a 80-state / 240-condition plan over 8 settings × seeds 0–4 × checkpoints 1 and 3 × three dampings, in FP64, coarse grouping. It is not a registered confirmation study and reads no S2 data.

## What exists (all copied here; originals untouched)

| Item | Where | Notes |
|---|---|---|
| Delivery package (source, config, docs, 31-test evidence, launcher) | `package/` | 42 files; `verify-package` reported `PACKAGE_HASHES_PASS` on 2026-11-05 |
| `FOLLOWUP_LOCK.json` | `run_output/` | freeze SHA `cc9d8cc8284b795481836321f112ee12260f064fc9670cef36b57202206b77d0`, created 2026-11-05 15:05 UTC, device `cuda:0`; inputs: audit bundle manifest `25a76f34…c3e`, protocol lock `f9f48682…1263` |
| `PLANNED_STATES.json` | `run_output/` | 80 states, 240 conditions, "no replacement" policy |
| E0 reanalysis | `run_output/e0/1793891140351875600/` | CSV/JSON/Markdown reanalysis of the audit snapshot; 40 independent-seed pairs, 40 positive damping differences; labelled exploratory |
| Live-state checks of 2026-11-05 | `checks/` | read-only; see below |

**Never produced:** any Q0 result, any E1–E4 measurement, `results/`, `invocations/`, `logs/`, `analysis/`. No NEXT v1 process exists; no `ACTIVE.lock`.

## Why it never ran on real checkpoints

The last blocking gate is in the package's own code (`genesis_next/safety.py`, `cli.py`):

1. `require_exclusive()` refuses to start any assay, **CPU or CUDA**, while a process with `-m genesis_gpu` exists. The v2 worker (PID 73000, parent 73948, started 2026-11-03 21:45:44) is alive and working, so every `Qualify` or `Run` call stops here. The package states it will not stop the worker.
2. For CUDA it also refuses if `nvidia-smi --query-compute-apps` lists anything. On this machine it lists 22 PIDs (Windows WDDM exposes many processes with no memory figure, including the v2 worker), so this check would fail even with v2 stopped unless those listings are empty.
3. Independently of 1 and 2, only DLN has trained v2 checkpoints. Of the 80 planned states, 38 have a COMPLETE training receipt; 42 do not (MLP 10, ResNet 10, Transformer 20, and 2 DLN states of the setting whose seed 0 failed). The runner marks those `SOURCE_TRAINING_NOT_READY_NO_REPLACEMENT`. Because Q0 for MLP, ResNet and Transformer needs seed 1, checkpoint 3 of an untrained setting, those three families cannot qualify and the whole panel for them waits (`WAITING_FAMILY_QUALIFICATION`).

## Q0 and the adapter

- **Q0** is the first real-checkpoint state per family (seed index 1, checkpoint 3). It was never run. DLN Q0 (`41c00898702c…`, setting `dln_d4_w16_orthogonal_balanced_c1`) has its training receipt COMPLETE and is the only Q0 that could run today.
- **Adapter contract:** the adapter (`genesis_next/assay.py`) was written from a remote reading of the v2 interfaces in a Linux CPU environment. Its only execution was a synthetic-torch test (`evidence/ACCEPTANCE.md`). It has **never run against a real checkpoint, the real data, or CUDA**, so it has neither passed nor failed a real-world contract check. `ACCEPTANCE.md` itself says READY_FOR_LOCAL_PREFLIGHT, not accepted.

## Live state of v2 at the check (read-only)

- Worker PID 73000 alive; it is in the GPU process list; the running measurement job's heartbeat was 1 s old; GPU samples 16–34% utilization, ~1.5 GiB used.
- Queue progressing: measure COMPLETE 836 (658 at the 2026-11-04 20:11 audit snapshot), NUMERIC_UNRESOLVED 408, BLOCKED 24, PENDING 1,851, RUNNING 1; training COMPLETE 52, FAILED 1, PENDING 77. Last finished measurement 16 minutes before the check (long DLN d16 jobs).
- `worker.json`, `control.json` and `study-state.json` are 2 days old because they are written at launch; they are not a liveness signal. The queue heartbeat is.

## Technical barriers versus chosen policy

Reasons below are drawn from the code and measurements. The author of this document did not take part in earlier NEXT v1 sessions, so the history of why the work waited is not known, only what blocked it today.

| Item | Kind |
|---|---|
| 42 of 80 states have no trained checkpoint | Technical, real. Needs v2 to train MLP/ResNet/Transformer first (those jobs sit far down the queue) |
| Adapter untested on real data | Technical, real, but cheap to resolve: DLN Q0 is small |
| WDDM listing of GPU processes cannot prove exclusivity | Technical limitation of the check, not of the hardware |
| `require_exclusive` rejects CPU runs while v2 is alive | Policy built into the package (conservative; GPU is not needed for CPU runs) |
| GPU compute-app list must be empty | Policy; with WDDM it may never be empty |
| No pause of v2 | Owner policy so far (keep v2 running, no second GPU worker); a cooperative pause is available through v2's own `genesis_stop.ps1` |
| GPU capacity | Not a barrier: v2 uses about 1.5 GiB of 12 GiB; DLN states are small (FP32 peak about 72 MB). Contention would slow v2 slightly; the package does not allow it |
| Timeouts | Per-state limit 3,600 s in the lock. Offline Transformer FP64 on CPU needed over 5 h at γ=0.001, so Transformer on GPU is unmeasured |

## What v2 (the next project) should inherit

- Its first-order finding is a gate design question: exclusivity should be decided by one authoritative resource owner (the v2 device lock / queue), not by scanning process names and the WDDM list.
- Run Q0 on DLN first, because it is the only family with trained checkpoints.
- Keep the audit bundle (`E:\GENESIS\handoff\audit_snapshot_20261104_201035`, manifest SHA `25a76f34…`) as the immutable input. E0 is already reproducible from it.
- Treat the E0 result as exploratory: the 40 paired seeds come from the S1 stage and the audited rows carry the known false-valid caveats.
- Carry forward v2 rules: no S2 read, no replacement seeds, hash gates not to be bypassed, timeout means INCONCLUSIVE.
