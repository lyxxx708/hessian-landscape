# GENESIS v2 可执行源码交付验收

**交付日：2026-11-02。结论：可执行源码、软件验证和 CPU 小规模闭环已完成；本机 Windows/CUDA 全科研验证尚未执行。**

## 已实际验证

| 项目 | 实测结果 |
|---|---|
| 全包 pytest | **80 passed，1 skipped，0 failed** |
| 唯一跳过项 | 实际 CUDA 设备测试；当前环境没有 GPU，未伪装执行 |
| 四模型端到端 CPU 工程流程 | **40 COMPLETE**：8 条微型训练、32 条曲率/效用测量 |
| 研究阶段控制 | S1、S2、冻结/解封、S3 NO-GO 负对照、审计和报告均真正执行 |
| 独立算法重算 | **8/8**（4 模型族 × 2 阶段），错误列表为空 |
| 生成结果 | **8 张图、9 类表、完整 Markdown/HTML 报告与 SHA 清单** |
| 安装包 | wheel 构建成功；脱离源码目录导入和 CLI help 成功 |
| 来源一致性 | 源码、配置、数据/快照、软件 ABI 与 protocol-lock 绑定 |
| 失效防护 | E盘/C盘回退、损坏checkpoint、冻结后修改、旧G0、旧QA、并发/恢复、科学样本单位等故障测试 |

当前 Python 3.13.5；PyTorch 2.10.0+cpu；NumPy 2.3.5；SciPy 1.17.0。pytest 显示 18 条上游 `torch.jit.script` 弃用警告，没有隐藏这些警告。

## 真实证据定位

源码包中 `validation/48_release_tests.txt` 是最终完整软件测试；`49_release_cpu_pipeline.log` 是最终源码版本端到端运行；`51_release_independent_verification.txt` 是另一次实际独立重算；`52_release_report_rebuild.txt` 是重新生成报告。早期 `*_red.txt` 是开发中实际观察到的失败测试，后续修复后已转绿，不应当作当前失败状态。

完整 CPU 证据包包含生成数据、8 条小型训练 checkpoint、全部测量、SQLite 台账、环境/协议锁、原始探针与报告，可据此独立核对原始数值；完整协议恢复仍须匹配冻结的源码/环境，迁移机器需新的验收。它只属于工程 smoke，不属于 130+96 条真实研究数据。

- 核对的远程基线：PR #11 / `26315f006c3fc60edbe8bb726df3c894a9f40c05`。
- 本地实现提交：`564b8640b20d328eca799aa3decd41d707ab4ab5`（不是已推送到 GitHub 的提交）。
- 本次源文件清单 SHA：`6ea8ae068e284e2ea1d1c6257e0e1479fc4c3bb00111e5fb8d5aa185cd007d65`。
- 最终 smoke protocol SHA：`4979f5ffe81d0b17083a79df5d0f62e235d62ba0430d5913e49b1bfd29110f13`。
- 原始蓝图 SHA：`6bb8578a984c9210504d448b2014a02d85b8740b26859ab906d808a3dbef5970`。

## 尚未发生，因此不声称已通过

原生 Windows PowerShell、4070 Ti CUDA 数值/显存/驱动资格、真实公开数据下载和 226 次完整训练、满足 U/P 后的真实 S3 比较、旧仓库完整回归、GitHub Actions。本次未修改远程仓库、未控制用户电脑、没有付费云/API 任务。

审计使用不同数值算法代码路径；代码 review 是作者自审，没有第二位专家或独立 agent 的批准。当前可以进入本机软件与 G0 验收，不能据此宣布新 Hessian 定理、论文贡献或优化器提速。

## 本机使用

解压源码至 `E:\GENESIS\worktrees\genesis-v2`，阅读 `README_GENESIS_V2.md`。先运行 `scripts\genesis_bootstrap.ps1`；通过后使用 `scripts\genesis_launch.ps1 -AcceptPublicDataLicenses`。需要并入已有仓库时用安全 additive overlay，冲突必须停下，不覆盖历史档案。启动/暂停/恢复均不依赖 Codex 持续推理。
