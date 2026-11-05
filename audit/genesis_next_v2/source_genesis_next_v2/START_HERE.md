# GENESIS NEXT v1 — 开封即用交付包

**目标：**检验“曲率矩阵结构复杂 → 梯度更新复杂 → 实际求解昂贵”这条推断在哪一步成立或失效。不是先造新优化器。

**交付内容：实验方案 + 可运行程序 + 固定配置 + Windows 启动器 + 自动测试 + Claude Code 接管指令。**

## 先读这三点

1. **原 v2 完全不改。** 数据、checkpoint、队列、S1 predictor、S2 规则均不覆盖。本包输出到 `E:\GENESIS\runs\genesis_next_v1`。
2. **默认只检查。** 双击 `START_HERE.cmd` 或运行 `START.ps1 -Mode Inspect` 不会启动 GPU、不暂停旧进程、不下载或上传任何内容。
3. **S1 新分析不是确认研究。** 80 个 checkpoint 状态来自 40 条旧 S1 轨迹；原 S2 只按原协议独立确认。不要把测试通过、CG 收敛或“生成报告”当作科学发现。

## 放在哪里

解压整个 `GENESIS_NEXT_v1` 文件夹，例如：

```text
E:\GENESIS\delivery\GENESIS_NEXT_v1\
```

不要解压到 frozen worktree 或原 `genesis_full_v2` 运行目录内。

已配置的默认位置：

```text
Python   E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe
审计包   E:\GENESIS\handoff\audit_snapshot_20261104_201035
旧运行   E:\GENESIS\runs\genesis_full_v2
新输出   E:\GENESIS\runs\genesis_next_v1
```

路径不同，使用 `-Bundle`、`-RunRoot`、`-OutputRoot`、`-Py` 参数显式传入；不需要改源码或在 C 盘安装环境。

## 第一阶段：现在即可执行，不使用 GPU

在本文件所在目录打开 PowerShell：

```powershell
Set-Location 'E:\GENESIS\delivery\GENESIS_NEXT_v1'
.\START.ps1 -Mode Test
.\START.ps1 -Mode Inspect
.\START.ps1 -Mode Reproduce
.\START.ps1 -Mode Plan
```

若系统策略阻止 `.ps1`，只对本次进程使用：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\START.ps1 -Mode Inspect
```

`Reproduce` 会校验审计包 SHA 并输出 E0 的 CSV、JSON、Markdown，位于新输出目录 `e0/<独立编号>/`。它不会重跑 FP32/FP64 审计或构造神经网络算子。

## 第二阶段：冻结本轮新方案

```powershell
.\START.ps1 -Mode Freeze
```

写入 `FOLLOWUP_LOCK.json`，固定本包源码、配置、环境、旧源协议和 80 状态选择。可以重复调用同一冻结命令；若身份发生变化则拒绝覆盖，必须使用新的输出根目录。

此命令不等于原 v2 的 `freeze`，不会写原运行目录。

## 第三阶段：独占计算窗口内运行

**先用既有流程确认 v2 worker 已安全退出。** 本包不会代替你停掉它；运行中则明确拒绝。Windows GPU 进程检查并非完整安全隔离，因此仍须由本地执行者确认资源所有权。

```powershell
# 每个 family 固定一个 S1 seed/checkpoint；只先做一个。
.\START.ps1 -Mode Qualify -Device cuda:0 -MaxStates 1 -ApproveCompute

# 资格通过的 family 才会进入正式面板；每次最多四个状态。
.\START.ps1 -Mode Run -Device cuda:0 -MaxStates 4 -ApproveCompute

.\START.ps1 -Mode Summarize
```

重复 Qualify/Run 只处理尚未产生结果的计划状态。原训练尚未完成的状态保留缺口；不替换 seed、不读取 S2、不自动重试已失败的数值条件。超时是 `INCONCLUSIVE`，不是零收益。各族 Q0 的结果属于同一探索面板，不重复增加样本量。

CPU 实验必须先用 `Freeze -Device cpu -OutputRoot <新的CPU输出根>` 单独冻结，再用相同输出根执行 `-Device cpu -ApproveCompute`；CPU 收据不能给 CUDA 放行。CPU 实验同样受相同超时限制。**不要为了绕过 GPU 占用，把 Transformer 自动转到 CPU 跑一整天。**

## 产物在哪里

```text
E:\GENESIS\runs\genesis_next_v1\
  FOLLOWUP_LOCK.json          新协议身份
  PLANNED_STATES.json         80 状态计划（Plan 生成）
  e0\                        对已有快照的复算
  results\                   每状态不可覆盖的测量收据
  local_inputs\              精确分析 batch，含受限数据，不得公开上传
  logs\                      本包子进程日志
  invocations\               本轮做了什么、什么还未就绪
  analysis\                  汇总与有效样本覆盖
```

## 实验范围

| 模块 | 做什么 | 是否新增训练 |
|---|---|---|
| E0 | 复算原始快照与误差分母 | 否 |
| Q0 | 每族实际 S1 checkpoint 的 FP64/CUDA 资格与成本 | 否 |
| E1 | Full/Block/短 CG/计数预算 CG 的局部收益与成本 | 否 |
| E2 | 小模型的 near-null 分解、谱收益方向和 H−G | 否，嵌入 E1 |
| E3 | DLN 固定/协变阻尼的 gauge 对照 | 否，稀疏子集 |
| E4 | 输入量化、算术精度、参考实现误差分开 | 否，嵌入 E1 |

详细方案：`docs/EXPERIMENT_PLAN.md`。Claude Code 接管：`BOOTSTRAP_CLAUDE_CODE.md`。

## 已验证与未验证

本包制作环境为 Linux / Python / PyTorch CPU；自动测试包含数值恒等式、错误路径、文件哈希、S2 排除、CLI 流程和小型 Torch 接口演示。结果见 `evidence/ACCEPTANCE.md` 与测试日志。

**未在此环境执行：你的真实 E: 文件访问、真实 4070 Ti CUDA G0、Windows PowerShell 端到端、原始神经网络 checkpoint 重算。** 程序已按固定提交的真实接口实现；这些必须在本机验收。包内 Demo 全部明确标记合成测试，绝不冒充 GENESIS 科研结果。

## 遇到 BLOCKED

先读具体原因。源哈希不符、旧 worker 仍活跃、数据指纹不一致、checkpoint 未就绪都不是应该删除门禁的问题。禁止改 metadata/hash、删除 checkpoint、自动换数据、重装 CUDA、关闭 TLS 或强推 Git。

`ACTIVE.lock` 是本包进程锁。异常断电后若遗留，先核对其中 PID 与进程创建身份，确认所有本包子进程退出后再移走到本包 `logs/` 保存；不要删除原 v2 的任何锁。

完整交付哈希：`PACKAGE_MANIFEST.json`；直接校验：`python -B -m genesis_next verify-package`。
