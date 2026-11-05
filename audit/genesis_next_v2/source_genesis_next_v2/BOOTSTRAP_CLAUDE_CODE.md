# Bootstrap — GENESIS NEXT v1 独立补充实验执行者

从交付包当前位置接手。先读 START_HERE.md、docs/EXPERIMENT_PLAN.md、docs/CONFIRMATION_EXTENSION.md 和 evidence/ACCEPTANCE.md。

你的目标是运行已交付的具体实验，不是重新讨论架构、重写 harness、重新搭建 Scientist Agent 或扩大科学网格。

## 当前已知依据

依据的是 commit `629032110fa51affc7f4e96cdb75f0c40070a9fe`、2026-11-04 20:11 的固定审计快照。它不是实时状态。旧 v2 的当前 worker/阶段只能在本机检查，不能沿用聊天中的 PID、完成数或“GPU 正在跑”的旧说法。

## 第一轮必须执行的实际动作

1. 用既有 Python：`E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe`。
2. 运行包校验与 Test，再 Inspect。不得重装 torch/CUDA 或新建无必要环境。
3. 运行 Reproduce，形成 E0 科学复算表；运行 Plan，核对 80 状态/240 条件、S1-only、没有 seed 替换。
4. 核验原运行协议和本包 source adapter 接口。冻结本包 Follow-up lock；不执行原 v2 freeze/report/adjudicate。
5. 真实实验只在明确独占的计算窗口执行。已有 v2 仍运行时，保持它不动，先完成 E0/计划；本包不会偷偷再开 GPU worker。不得擅自终止旧运行、注册服务或计划任务。需要计算窗口时，说明哪一个 Q0 状态需要窗口，不新开一轮泛化诊断工程。
6. 有窗口后先 Qualify，一次一个状态；记录真实 GPU 成本/显存。某族未就绪或不合格，不换预注册设置、不用 G0 初始状态冒充训练后状态。
7. 资格通过的族再 Run，每次至多四个状态；完成后 Summarize。原 v2 和本轮结果不得混合。

## 不可违反的科学边界

- 本轮是看过 S1 后设计的探索研究，不是重新预注册后就自动变成独立确认。
- 不读取原 S2 的科学结果来调整求解器、阈值、样本或叙事；原 S2 保持自己的 frozen endpoints。
- 程序主参考是原 v2 FP32 输入的精确 FP64 升格。原生 FP64 输入仅为量化对照。不要擅自合并二者。
- Hessian 负值须同时报告谱尺度/质量/容差，不用数量讲“严重鞍点”。
- gauge 实验必须包含协变阻尼负对照；固定 λI 不变时观察到差异不等于函数性质变化。
- 相同 matvec 不等于相同 wall time；本轮局部收益不等于长程优化加速。
- 每个独立 seed 是一个统计单位。缺失、失败、超时保留，不补零、不换 seed。
- E0 的原 matched-CG 和 E1 的新预算定义不同，分开命名。

## 异常与版本

若发现软件缺陷，在新的副本/版本修复，先添加回归测试。已冻结 FOLLOWUP_LOCK 对应的源码不就地修改。任何真实结果保持原样。测试通过不能替代科学资格。

只允许写新输出目录和本包的单独开发副本。不修改旧 worktree、datasets、run_status.sqlite、protocol-lock 或任何训练 checkpoint。

## 交付

每轮只汇报：实际执行的状态、数值资格、独立 seed 覆盖、主要效应/成本、真实阻塞。停止重复工程叙事。

本轮阶段结束后输出现有 analysis CSV/JSON/Markdown、逐条件证据索引和明确边界；先本地保存。不自动公开上传 `local_inputs/`、原始数据或权重；GitHub 发布需要单独的审计导出，不能直接 add 整个运行目录。

不新增优化器、训练 seed 或大型实验。若新机制值得确认，遵循 CONFIRMATION_EXTENSION.md 提交独立后续设计，不挪用原 S2 充当新指标调参集。
