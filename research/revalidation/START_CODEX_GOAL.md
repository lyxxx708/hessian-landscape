# Start the RTX 4070 Ti local Codex Goal

Use Codex on the Windows PC that physically contains the RTX 4070 Ti. This ChatGPT session has updated GitHub PR #11 but **has not started anything on that PC**.

1. Open the existing hessian-landscape repository in Codex Desktop or Codex CLI. No manual replacement of an existing working tree is required: the Goal instructs Codex to create a new, isolated worktree from PR #11.
2. Confirm the local Codex build supports Goals; official documentation lists /goal in Codex 0.128.0 and later. If the installed app lacks /goal, paste the same text as an ordinary instruction and allow Codex to implement the persistent local Python runner.
3. Paste the following one-line Goal and give Codex local workspace/terminal access. Authorize local CUDA runtime and public dataset downloads; cloud spend, secrets and protected files remain excluded.

    /goal 在这台 Windows 本机的 RTX 4070 Ti 12GB 上完成 GENESIS 全量新实验而不是再写计划。安全 fetch lyxxx708/hessian-landscape 的 PR #11 到独立 worktree，阅读根目录 AGENTS.md、research/revalidation/CODEX_LOCAL_4070TI_GOAL.md、LOCAL_4070TI_FULL_V1.json、PRIMARY_ENDPOINTS_AND_FREEZE_RULES.md 与新验证协议；先实现并验证 CUDA/GGN/Hessian/矩阵自由求解及可恢复批处理系统，冻结科学协议，再由本地 Python 独立进程完整执行 G0、S1 全部 26×5=130 训练、S2 至少 5×16=80 个全新种子的确认实验，即使 S1 结果为负也完成 S2；仅在 U 门禁通过时开展 S3 优化器实验，否则按规则 STOP。GPU 运行时长不设上限，单卡显存须受控；严格少用 Codex token、禁止逐 seed/λ 调模型，实验靠脚本自动调度、断点续跑、GPU 数值校验和独立 QA。保存全部负结果、原始数据和 SHA256、本地运行日志；输出 SCIENTIFIC_VERDICT.md 及完整复现实验报告。不得将 2025 缺失数据当证据，不调用付费云/API，不公开原始敏感文件，不自动合并 main。只在真实硬阻塞时停止并输出 INCOMPLETE_BLOCKED_EVIDENCE；完成条件是有证据的完整研究结果，不要求正结论。

4. Codex should create its own dedicated local process for the actual many-hour/many-day GPU batch after G0 and freeze. Leaving the Codex chat is not itself a CUDA scheduler; the OS process must write artifacts independently.
5. Ensure Windows stays awake while the GPU job is running. The Goal forbids silent global power-setting changes; adjust the sleep policy yourself if necessary. Codex must implement a safe resume command for interruption/reboot.

**Expected implementation CLI (Codex must implement this; these commands are not yet available on PR #11):**

    python -m genesis_gpu.cli doctor --config research/revalidation/LOCAL_4070TI_FULL_V1.json
    python -m genesis_gpu.cli g0 --config research/revalidation/LOCAL_4070TI_FULL_V1.json
    python -m genesis_gpu.cli freeze --config research/revalidation/LOCAL_4070TI_FULL_V1.json
    python -m genesis_gpu.cli run-all --config research/revalidation/LOCAL_4070TI_FULL_V1.json --resume
    python -m genesis_gpu.cli status --json
    python -m genesis_gpu.cli verify --all
    python -m genesis_gpu.cli report

These commands are a **deliverable contract**, not a claim that runnable code currently exists. The background launcher, restart/stop controls and exact scientific adapters must be implemented and tested by local Codex.

**Evidence-gated endpoint:** G0 valid, S1/ S2 required records completed or explicitly invalid, QA recomputed from raw measurements, evidence-linked S/M/U verdict; S3 measured if warranted or correctly stopped. The experimental result may legitimately be negative. Do not keep the Goal running forever in search of a positive effect.

**Canonical full instructions:** [CODEX_LOCAL_4070TI_GOAL.md](CODEX_LOCAL_4070TI_GOAL.md), [LOCAL_4070TI_FULL_V1.json](LOCAL_4070TI_FULL_V1.json), [primary endpoints / freeze rules](PRIMARY_ENDPOINTS_AND_FREEZE_RULES.md) and [fresh validation protocol](2026-11-02_FRESH_VALIDATION_PROTOCOL_V1.md).
