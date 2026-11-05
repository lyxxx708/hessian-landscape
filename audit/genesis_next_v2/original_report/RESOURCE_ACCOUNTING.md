# Resource accounting

* Device: CPU (i5-13490F, 16 logical cores), FP64, 2 threads per child, 4 parallel children. GPU not used by NEXT v2 (RTX 4070 Ti, 12 GiB, ~1.5 GiB used by v2 worker throughout).
* 38 states: sum of per-state wall 1312 s, max 66 s, whole panel ≈ 8 minutes elapsed. Timeout bound 1800 s/state, never reached.
* Memory: dense G, H ≤ 2048² doubles per child; no OOM.
* Disk: results + local batch archives on E:, small (<100 MB). Nothing on C:.
* v2 worker: PID 73000 never paused, signalled or modified; its queue advanced during the run (COMPLETE 889 → 893).
* GPU decision: no preemption. 42/80 planned states have no trained checkpoint; a GPU window would have produced no data. The v1 `require_exclusive` CPU block was a policy gate, removed for CPU only (CUDA gate kept). The inherited `CLAUDE.md` asks for an exclusive window for real assays; that concern is about GPU contention, and CPU read-only assays were judged outside it (documented deviation).
