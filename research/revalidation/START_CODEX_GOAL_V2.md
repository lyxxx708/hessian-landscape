# Paste this exact Goal into local Codex — GENESIS v2 runnable source

**Source:** [implementation/genesis-v2](../../implementation/genesis-v2/README_GENESIS_V2.md).  
**Step-by-step runbook:** [EXECUTION_PLAYBOOK_V2.md](EXECUTION_PLAYBOOK_V2.md).  
**State:** GitHub source and software CPU validation only; the user's Windows RTX 4070 Ti G0 and 226 real model training trajectories have NOT yet run.

Open Codex Desktop/CLI on the Windows PC with RTX 4070 Ti and authenticated GitHub access. If Goal mode is available, start the following as a Goal. Otherwise provide the same instruction as a normal Codex long-running task; the research worker itself must run as a separate OS process independent of Codex.

## Primary Goal instruction (copy as one message)

> /goal
>
> 你现在负责把已经实现并提交到 GitHub 的 GENESIS v2 科研平台，在我本地 Windows + RTX 4070 Ti 12GB 上，从环境资格一直运行到独立科学验证与 GitHub 审查交付。**不要重新从零设计或仅写计划；源码已经在 lyxxx708/hessian-landscape 的 research/fresh-curvature-revalidation-v1-20261102 分支、implementation/genesis-v2/ 目录。**
>
> **立即阅读**仓库根 AGENTS.md、本目录 EXECUTION_PLAYBOOK_V2.md、implementation/genesis-v2/README_GENESIS_V2.md、CODEX_EXECUTE_V2.md、configs/study_v2.yaml、docs/spec/GENESIS_v2_Blueprint_Design_Only.md 和 DELIVERY_MANIFEST.json。以上最新 v2 代码与手册优先于 PR #11 旧的 G0-only / S2=80 草稿。严格执行手册的 Stage 0—14，每个阶段保存真实原始证据与门禁收据，不得跳过。
>
> **工程安全：**先保护当前本地 Git 工作区；在 E:\GENESIS\worktrees 新建隔离 worktree/分支。Python 环境、源码、大数据、临时文件、各类缓存、checkpoint、日志、SQLite、结果全部尽量存 E:\GENESIS；E 盘不足时停机报告，不得无声改写 C 盘；禁止移动/删除我现有文件或改全局 Windows 设置。只允许本地 4070 Ti GPU 长时工作，不限 GPU 计算时长但必须遵守 12GB/温度、单 GPU worker、预注册有限实验网格；不得调用付费云/API 或接触无授权 holdout。
>
> **实施流程：**先核对全部源码 SHA256、部署 Windows 环境、跑 v2 全部软件测试及原仓库旧回归、公开数据许可证检查，再在真实 RTX 4070 Ti 上完成 G0 数值/显存/任务资格。任何 G0 或求解精度失败必须定位修复并重新 G0，不能降低科学阈值。首次真正 S1 结果出现前锁定源码、数据、参数分组、分析代码、随机种子和主要终点。
>
> **大实验：**按照 v2 冻结的 26 settings×5 seeds 全部执行 S1=130 条真实训练，每条固定 4 checkpoint 与 3 λ 诊断；A/B 全覆盖，C-base/C-deep 按事先锁定的计算密度，保存全部负结果和数值 invalid。S1 科学信号无论是否为正，都必须执行 S2 的 6 anchors×16 全新 seeds=96 条独立确认（包括 8 层 Transformer）。必须严格区分 Hessian/GGN、正确 CE loss Hessian、精确 block-GGN、任务效用、Gauge/null、统计独立性和误差区间。S3 仅在 U/P 的冻结门禁通过时做真实成本公平的优化器对照，否则真实记录 S3_NO_GO。
>
> **少用模型、多用 GPU：**实验靠独立且可恢复的 Python 进程执行；零逐 seed、逐 λ、逐 probe 的 LLM 调用；Codex 只用于不可避免的代码修复和独立审查。失败必须按真实类型和 hash 收据归档；不要为了得到正结论换 seeds、任务、损失、阈值、checkpoint 或有效样本。
>
> **最后验收与 GitHub 交付：**真实运行独立算法复核与报告生成，输出 SCIENTIFIC_VERDICT.md、S_M_U_P_RESULTS.md、NUMERICAL_QA.md、NEGATIVE_RESULTS.md、REPRODUCTION.md、RESOURCE_ACCOUNTING.md、GITHUB_PR_SUMMARY.md，报告 130/96 有效/无效数目、独立 n、S/M/U/P 分轨正负裁决、来源/数据/源码 SHA、实际 GPU 时间/显存、全部异常。最终把必要的源码修复、测试与脱敏紧凑科研报告提交到新的 GitHub 审阅分支和 PR；绝不将私有原始 checkpoint、数据包或密钥上传公开仓库，也不得自动合并 main。
>
> **继续条件：**按照 Stage 0—14 自主推进，不为普通步骤反复询问。遇到缺真实 CUDA、缺公共数据使用权、严重数值不一致、E 盘空间不足等无法安全解决的硬障碍，要留下 INCOMPLETE_BLOCKED_EVIDENCE、准确状态与安全恢复命令；绝不能假装完成或仅交付一个 demo。允许最后得到科学负结果，只要完整执行、复核和如实报告。

## Two critical distinctions

1. **Goal-mode is not a GPU scheduler.** Codex must use the already shipped separate Windows launcher and SQLite-backed experiment worker so the GPU process continues without a live model conversation. Do not promise perpetual Codex cognition or bypass its usage limits.
2. **GitHub delivery means a review PR, not a main merge.** The full source is already in GitHub; only later fixes and genuinely completed non-sensitive results need an additional PR. The 2025 archived claims are NOT primary evidence.

## Current approved scope

- User PC: native Windows, RTX 4070 Ti 12 GiB; E: worktrees/venvs/cache/results first, no C: fallback.
- S1: 130 real training runs across DLN, MLP, ResNet and Tiny Transformer, 4 checkpoints and 3 lambda choices.
- S2: **96** new confirmatory runs on six locked anchors, even when S1 is null.
- G0: genuine CUDA acceptance required; Linux CPU CI and original three-seed toy do not count.
- S3: conditional, with actual wall-clock and strong baselines.
- All results and failures must be independently auditable from saved E: artifacts; GitHub publication limited to source and safe summaries.
