# v2 设计—源码—测试—本地验收对应表

规范：原样保留的 `docs/spec/GENESIS_v2_Blueprint_Design_Only.md`。批准 v2 后采用 130 个发现训练、96 个确认训练，不沿用 v1 的 80 条确认数。这里区分“源码已实现”“本环境实际验证”“必须在用户硬件完成的验收”；不以空目录或 TODO 代替能力。

| 蓝图条目 | 可执行实现 | 本次证据 / 本地门禁 |
|---|---|---|
| §0 旧证据隔离、不追求正结果 | `study/design.py`, `study/adjudication.py`, `reporting/report.py` | smoke 与 full 强类型隔离；生产 GPU 未运行 |
| §3 科学/执行/审计分层 | `contracts`, `curvature`, `runtime`, `audit`, `reporting` 包 | tests_v2 全套；无逐 seed LLM 依赖 |
| §4 参数顺序/共享权重/冻结状态 | `curvature/params.py`, `operators.py`, `contracts.py` | tied embedding、buffer、输入深复制、分组覆盖测试 |
| §5.1 MSE GGN | `LossSpec`, `FrozenOperator.raw_ggn` | FP64 独立 reverse-autograd dense 对照 |
| §5.2 CE GGN 与有效 token 分母 | 同上及 `audit/independent_reference.py` | ignore token、microbatch 分母、softmax 平移零模测试 |
| §5.2 加权任务响应 | `science/utility.py` | alpha_Q、alpha_task 分离；E_val 不重拟合测试 |
| §5.3 Exact Hessian | `FrozenOperator.hvp`, `dense_mechanism`, `lanczos` | 小矩阵 HVP/中心差分；不定 Hessian 不当成 SPD CG |
| §5.4 Full/Block/dual 求解 | `solvers/cg.py`, `curvature/dual_solve.py` | true residual、精确 restricted block、Woodbury 对照；未收敛状态显式 |
| §5.4 预条件 | Hutchinson diagonal PCG | 只加速迭代，不改变 oracle；独立残差测试 |
| §6 原始 G / inverse / corrected inverse | `sketches/block_probe.py`, `science/structure.py` | 小 dense 矩阵对照，稳定 `-GR/λ` 校正，逐距离误差界 |
| §6 自适应探针/区间 | disjoint pilot/final + source bootstrap | 固定 8 次独立 MC 校准；区间是近似，不能当保证95%覆盖 |
| §7 A/B/C 计算密度 | `diagnostic_tier`, `runtime/scheduler.py` | A 全训练；B 所有状态×阻尼×双分组；C-base/C-deep 事前固定 |
| §8 真实四类训练 | `models/`, `datasets/registry.py`, `training/trainer.py` | 4 族 CPU 合成工程跑通；公开真实数据与 CUDA 全规模待本机 |
| §8 130/96 与种子隔离 | `study/design.py`, `seed-manifest` | 两阶段数量及无重叠测试；S2 强制先 S1 裁决 |
| §9 机制/null | `science/controls.py`, `mechanism.py` | 同谱/等秩随机子空间、层序置换、Gauge 的函数/曲率敏感性、H/G/nullspace |
| §10 U 统计 | `study/statistics.py` | 每 seed 中后期3 checkpoint 中位数；两档 damping partial conjunction；Holm |
| §10 P 预测 | `science/predictor.py` | S1-only group-CV ridge，冻结 JSON；S2 AUROC/MAE/Spearman，独立 cluster bootstrap |
| §8/10 S3 | `training/optimizers.py`, `benchmark.py` | 真实更新逐方法单元测试；完整真实 S3 尚未发生，门禁不满足只跑小负对照 |
| §10 预算公平 | measured calibration, paired samples/wall budgets | 调参/训练/matvec成本入账；按全部基线且保守时间区间比较，不只对 AdamW |
| §11 E盘/缓存 | `env/storage_guard.py`, `scripts/genesis_env.ps1` | C盘回退/目录逃逸/不存在驱动 fail-closed 测试；native Windows 待验证 |
| §11 设备资源 | `runtime/resources.py`, `audit/g0.py` | 跨研究单GPU锁、热暂停、磁盘预留；真实显存/热/驱动收据待本机 |
| §11 持久化/恢复 | SQLite WAL, checkpoint safetensors+JSON | 逐位复现恢复、重复提交、活PID/死PID、SHA损坏注入 |
| §12 CLI | `cli.py` 与六个 PowerShell 入口 | CLI help/dryrun/完整CPU pipeline 已测；Windows入口静态检查 |
| §12 原始表/报告 | `reporting/report.py` | CSV主表；有pyarrow时同时Parquet，无pyarrow不假造文件；MD/HTML/PNG实际生成 |
| §13 独立算法核验 | `audit/verify.py`, `independent_reference.py` | 与主 jvp 实现不同的 differentiation/direct solve/SciPy 算法；并非第二位人类评审 |
| §13 证据级门禁 | source/config/data/runtime ABI+QA ledger hashes | 旧 G0失败后撤销绿灯、QA台账变化拒绝完成、报告二次生成hash测试 |
| §13 CI | `.github/workflows/genesis-v2-cpu.yml` | 提供Linux/Windows CPU工作流，但本次未提交GitHub/未运行远程CI |
| §14 D6/D7/D8 | 已编码 `pipeline` 执行路径 | 本次仅本环境小规模工程闭环，不宣称用户226次真实训练已执行 |

## 有意采用的明确裁决

1. **默认保守估计器优先。**蓝图的多源编码/Hutch++/跨右端复用/定制 CUDA kernel 均为可选加速；未通过独立偏差/方差/速度验收，不自动启用或假冒实现。已有 dense/dual、PCG、microbatch、缓存谱尺度；正式 G0 决定其是否适合本机。
2. **单一分析配置。**全部分析字段位于 `study_v2.yaml` 并哈希冻结。单独 `freeze --analysis` 不会被悄悄忽略，而是显式拒绝未合并的第二份配置。
3. **确认集新seed，不虚称新depth。**当前六个 S2 锚点均复用发现集架构深度，研究输出明确把未见深度外推标记 NOT_TESTED。不可从有限深度图宣称无限深度定理。
4. **原始训练语义明确。**S1 使用蓝图的原基线训练（DLN Adam、MLP/文本AdamW、ResNet SGD）；S3 的方法比较使用相同AdamW参考语义及相同原始目标/数据顺序。分析数据loss不包含解耦weight decay，记录在每个快照。
5. **K-FAC是参考重实现。**sampled-model-Fisher（不是 empirical Fisher），EMA、factored damping，非仿射参数显式AdamW fallback；不能称精确 layerwise-GGN或宣称复现某篇论文性能。Gradient Smoothing按已核对主文Eq.(2)作用于基础优化器更新，而不是偷换为原始梯度平滑。
6. **当前完成状态。**可执行源码、数学/恢复/审计测试和CPU闭环交付；原生Windows/CUDA、真实数据/226训练/统计发现是后续本机执行事实，不能写成已通过。不存在必须调用远端LLM才能完成日常运行的环节。
