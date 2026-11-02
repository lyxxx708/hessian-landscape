# Codex 执行入口：使用已有可执行源码，不重新发明实验框架

在 E 盘读取本包 `README_GENESIS_V2.md`、原始蓝图、`configs/study_v2.yaml`、`docs/BLUEPRINT_TRACEABILITY.md` 与 `docs/IMPLEMENTATION_LEDGER.md`。

**你的任务是安装、验证、运行和审阅这套已实现的源码，不是只写新计划，也不是绕过它另建一个只有 toy demo 的项目。**

1. 保护现有仓库/未提交修改，使用独立 E 盘目录。需要增量并入时，使用 `scripts/install_genesis_v2_overlay.py` dry-run/apply；任何同名冲突先比较再处理，不覆盖旧证据。
2. 运行 `scripts/genesis_bootstrap.ps1`。先处理环境/软件测试失败，保留完整日志；不以改松科学阈值让测试变绿。
3. 进入 `scripts/genesis_launch.ps1 -AcceptPublicDataLicenses`。它已有 doctor→data→G0→freeze→S1→adjudication→S2→S3 gate→independent verify→report 完整实现。最多一个本地 GPU worker。无付费云/API。
4. 失败时读 `status.json`、`resource_status.json`、失败日志与具体收据。普通运行不调用模型。源码在 freeze 后不得静默改动；确需改错则记录原因、完成回归测试、重新 G0，并为受影响科学试验创建新协议/输出目录。
5. S2 即使 S1 无效应也运行。S3 只有 U/P 门禁通过才跑完整在线实验；否则自动执行轻量负对照并记录 `S3_NO_GO`。不得为“得出正结果”换 seeds、模型、目标或阈值。
6. 验证至少这些项目：E 盘所有大文件；checkpoint/hash 可复查；真实 effective batch 与 CE token 分母；Frozen GGN 不是 empirical Fisher；准确层块求解；报告的独立 n；全部负结果与不可测状态；调用 `verify --independent --all` 从原始数据重算。
7. 本地 CPU/GPU耗时、实际有效种子、尚未完成/失败项均真实报告。源码包中的 CPU 烟测数据不可混进 S1/S2。本地 CUDA 未验证时不宣称完整科研验收。
8. 如接入原仓库，另外运行原有 `tests/` 回归套件。只有审阅 source/data rights、通过全部软件回归后，才提交增量代码和紧凑非敏感摘要到新的 review 分支；不自动合并 main，不上传大体积原始数据。

GPU 时长预算无上限不等于无限磁盘或无限显存。E 盘不足/异常温度/数值未资格时应暂停或显式保留失败，不回退 C 盘。主流程不依赖 Codex 对话保持在线。
