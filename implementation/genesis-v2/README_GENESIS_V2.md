# GENESIS v2：可执行本地科研平台

本源码包实施 `docs/spec/GENESIS_v2_Blueprint_Design_Only.md`。这是可安装的 Python 包、CLI、Windows 启动器、数值核、四类模型、训练/确认/审计流水线；不是再交给 Codex 从零实现的需求清单。

**验收边界：**本次构建环境是 Linux / PyTorch 2.10.0+cpu。软件测试和四模型端到端 CPU 小规模流程已实际执行；Windows 原生启动、RTX 4070 Ti CUDA G0、真实公共数据训练以及完整 130+96 条轨迹尚未在你的电脑执行。`validation/` 记录真实测试输出，不用 CPU 绿灯冒充 GPU 或科学验证。正式运行必须通过本机 CUDA/E 盘门禁。

## 1. 交付与旧仓库关系

核对的旧基线是 `lyxxx708/hessian-landscape` PR #11、commit `26315f006c3fc60edbe8bb726df3c894a9f40c05`。本次未向远程 GitHub 写入，未改动 `main`、旧报告、PR #11 或你的 Windows 磁盘。当前容器不能克隆该仓库，因此这里是**隔离的增量源码包**，不声称已运行旧仓库的回归测试。

可直接把整个包解压至 `E:\GENESIS\worktrees\genesis-v2` 独立使用。需要并入已有仓库时，先让 Codex 在 E 盘建立新分支/worktree，再运行安全覆盖工具：

```powershell
py -3.11 scripts\install_genesis_v2_overlay.py --target E:\GENESIS\worktrees\hessian-landscape-revalidation
py -3.11 scripts\install_genesis_v2_overlay.py --target E:\GENESIS\worktrees\hessian-landscape-revalidation --apply
```

第一条只预览；第二条只添加新文件或接受字节相同的文件，遇到冲突立即拒绝，不覆盖现有 `README.md`、`AGENTS.md` 或历史证据。已有 `pyproject.toml` 冲突需要 Codex 显式整合，不得强行覆盖。并入后额外执行旧仓库 `python -m unittest discover -s tests -v`，本包测试不能替代它。

## 2. Windows 开箱入口

先在 E 盘打开 PowerShell，进入本源码根目录。脚本仅修改当前进程及子进程环境，不修改 Windows 全局设置。需要系统已有 Python 3.11/3.12、NVIDIA 驱动；不会自动安装驱动或触碰 C 盘现有文件。

```powershell
# 环境、CUDA wheel、依赖、软件测试、设备/存储 doctor
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\genesis_bootstrap.ps1

# 审阅数据来源后，运行有门禁的完整流水线；独立于 Codex 对话
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\genesis_launch.ps1 -AcceptPublicDataLicenses

# 查看、合作式停止、恢复
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\genesis_status.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\genesis_stop.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\genesis_resume.ps1
```

`-ExecutionPolicy Bypass` 只作用于这一 PowerShell 进程，不持久修改系统执行策略。首次使用可加 `-Foreground` 直接查看输出。暂停/停止不会 `taskkill`、不会杀死其他 Python 程序。断电/kill 后重启须再次使用 `genesis_resume.ps1`；不会擅自安装开机任务或改变休眠政策。

安装器默认采用官方已核对的 **torch 2.10.0 + torchvision 0.25.0 / CUDA 12.8** wheel（这是实现基线，不宣称最新版本）。需由本机初始化确认驱动兼容，失败即阻止正式运行；不静默安装 CPU wheel。全部 venv、包缓存、数据、临时文件和结果都在 `E:\GENESIS`。若 E 盘不存在/空间不足或目录经 junction 指向 C 盘，拒绝运行。

## 3. 可执行 CLI

```powershell
. .\scripts\genesis_env.ps1
$Py = 'E:\GENESIS\venvs\hessian-landscape-v2\Scripts\python.exe'
& $Py -m genesis_gpu --config configs\study_v2.yaml doctor
& $Py -m genesis_gpu --config configs\study_v2.yaml prepare-data --accept-licenses
& $Py -m genesis_gpu --config configs\study_v2.yaml g0 --all --save-reference
& $Py -m genesis_gpu --config configs\study_v2.yaml freeze
& $Py -m genesis_gpu --config configs\study_v2.yaml plan --stage s1 --dry-run
& $Py -m genesis_gpu --config configs\study_v2.yaml run --stage s1 --resume
& $Py -m genesis_gpu --config configs\study_v2.yaml adjudicate --stage s1
& $Py -m genesis_gpu --config configs\study_v2.yaml run --stage s2 --resume
& $Py -m genesis_gpu --config configs\study_v2.yaml adjudicate --stage s2
& $Py -m genesis_gpu --config configs\study_v2.yaml run --stage s3
& $Py -m genesis_gpu --config configs\study_v2.yaml verify --independent --all
& $Py -m genesis_gpu --config configs\study_v2.yaml report --format md,html
```

`pipeline` 实际串联上述命令；已提交的工作不重算，未通过数值门禁不伪造成科学通过。`run --stage s2` 必须匹配 S1 的已落盘裁决和队列哈希。G0 后冻结源码、配置、数据清单、种子和软件运行 ABI；改变 PyTorch/配置/源码需新的 G0 与新研究目录，不能偷换已冻结分析。

主分析配置集中在单个 `study_v2.yaml` 中，避免两个分析文件互相覆盖。CLI 不会悄悄忽略 `freeze --analysis`：它会要求把分析字段正式写入配置再冻结。

## 4. 研究范围与真正实现的功能

- **226 条固定训练轨迹：**S1 26×5=130，S2 六个锚点×16=96；S2 包含 4 层和 8 层 Transformer。初始、1/3、2/3、终点四个 checkpoint；B 层全部状态、三档阻尼、coarse/fine 双参数分组。C-base/C-deep 在结果产生前由设计确定。
- **四类真实训练适配：**固定 teacher DLN、MNIST MLP、CIFAR-10 GroupNorm ResNet8/20、字符 Tiny Transformer。真实数据缺失时明确失败，不替换为合成数据。`smoke` 是完全分离、显式标注的工程验证配置。
- **数值核：**冻结参数/buffer/batch；MSE 和 CE 的真实 GGN，忽略 token 正确归一化；HVP、独立 reverse-autograd dense/差分参考、逻辑 tied 参数、可选双空间 Woodbury、小规模精确矩阵与矩阵自由 CG/PCG。
- **精确比较：**Full GN 与精确 restricted Block-GGN；实际 true residual、十倍容差稳定性；alpha_Q 与 loss-curvature alpha_task 分开，验证集沿用训练 alpha_task；固定少步与成本匹配 CG 均保存，真实 loss line-search 计入成本。
- **结构/机制：**原始 GGN、阻尼逆、稳定的 `R−λ⁻¹I` 修正；逐探针标量记录、Monte Carlo 区间与求解误差分开；自适应 pilot 和独立最终探针；层序 null、匹配随机子空间、Gauge 重缩放、有限 λ 横向项、H/G 差和近极点诊断。
- **统计/P：**独立训练 seed 是重采样单位，不把 checkpoint/λ 当成新样本；partial-conjunction/Holm；S1 训练的透明 ridge 预测器及廉价基线、S2 一次确认。不可测的效应是 `NUMERIC_UNRESOLVED`，不是零。
- **在线 S3：**实际 AdamW、Gradient Smoothing 参考重实现、 sampled-model-Fisher K-FAC 参考实现、精确层块 GN、同成本 CG、选择性 Krylov；独立调参种子、相等调参时间预算、成对测试种子、sample 和 wall-time 双预算。每个方法的真实成本入账。K-FAC 的 factor damping 和 unsupported 参数 AdamW fallback 均显式报告，绝不冒充精确 Block-GGN。
- **执行/证据：**SQLite WAL 状态机、跨研究目录单 GPU 锁、PID 创建时间识别、原子 checkpoint/resume、safetensors/JSON（不反序列化 pickle）、SHA 链、停止/恢复、资源保护、独立代码路径数值重算、CSV/可选 Parquet、图与 Markdown/HTML 报告。

没有依赖 LLM 的逐实验调度，没有付费 API/云资源调用，也没有自动公开 checkpoint 或合并 main 的代码。

## 5. 独立 CPU 验证方式

CPU 模式只验证工程与数学，不能给 full 配置授权：

```bash
python -m pip install -e '.[test]'
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python -m pytest -q
python scripts/run_cpu_smoke.py --root /absolute/path/to/new/smoke-run
```

Windows 也可以显式 `--config configs\smoke_v2.yaml --root E:\GENESIS\runs\cpu-smoke` 运行测试；该配置永远输出 `ENGINEERING_SMOKE_ONLY`，不会报告真实科学确认。实际源码包附带测试日志、端到端收据和验证索引。

## 6. 结果在哪里

正式默认 `E:\GENESIS\runs\genesis_full_v2`：

- `protocol-lock.json`、`env-lock.json`、`seed-manifest.json`、`run_status.sqlite`。
- `checkpoints/` 中四个固定 checkpoint 与受控双槽 resume（保留 hash，不无限增长）。
- `measurements/` 中 g/G/H 同一快照下的原始结果、probe seeds/能量/求解记录。
- `tables/`：全部状态、资格失败、全部距离 bins、GGN/逆/校正能量、逐探针、null、claim ledger。
- `reports/`：`SCIENTIFIC_VERDICT.md`、`S_M_U_P_RESULTS.md`、`NUMERICAL_QA.md`、`NEGATIVE_RESULTS.md`、`STATISTICAL_ANALYSIS.md`、`REPRODUCTION.md`、`RESOURCE_ACCOUNTING.md`、`FIGURE_INDEX.md` 和独立核验收据。
- `manifest_sha256.txt` 对生成报告/图表给出可复算清单。

## 7. 不夸大的边界

原始 2025 结果不被恢复或升级。本次的软件编写不等于已在 4070 Ti 上通过 G0，更不等于已经完成 226 次真实训练。源码的数值审计用不同算法路径；最终代码审查为作者自审，不是独立专家背书。

当前固定 S2 锚点的深度在 S1 已出现，因而只支持**新 seed 确认**，不能称“未见深度外推”。程序明确报告 `NOT_TESTED`；要研究新深度必须在首次科学冻结前另立版本，不能事后改当前确认集。

高阶可选加速（Hutch++、多源编码、Krylov 跨右端项复用、批量 probes、原生 fused kernels）没有伪装成已认证默认；使用经过独立对照的保守块支持探针。自动采样额外 S1 正/负设置属于可选扩展，默认只运行冻结的六个确认锚点。

正式科研发布之前还需本机 native Windows/CUDA 资格、完整真实数据试验与另外一位评审的复核。工程完备、统计效应和论文新颖性是三种不同的结论。
