# GENESIS v2.0 — RTX 4070 Ti 本地全量科研平台技术蓝图

**日期：2026-11-02｜状态：DESIGN ONLY / NOT IMPLEMENTED / NOT EXECUTED / NOT FROZEN**  
**基准代码仓库：** `lyxxx708/hessian-landscape`，Draft PR #11。**本文件不修改 PR、仓库或本地设备。**  
**最终目标：**在单张 NVIDIA RTX 4070 Ti 12GB、本地 E 盘优先、Codex Token 节约的条件下，实现完整、可恢复、可独立复核的深度网络 Hessian/GGN 结构、机制与优化效用研究系统。

## 0. 范围、边界与版本管理

- **证据重置：**2025 年缺失的 Hessian 原始矩阵和 checkpoint 不再纳入核心科研证据。旧报告永久保留，但数字不作为新实验目标。2026 年小规模合成实验仅作数学/数值对照。
- **先设计，后实施：**当前交付的是系统规格、数学对象、接口和验收合同。这里的类、文件名、CLI 和计算量均为**拟实现**，不是声称已编写或运行。
- **不追求正结果：**结构现象不存在、机制属于平凡规范/低秩解释、跨层优化无收益，都属于合格的科研结论。
- **自主计算权限：**未来 Codex 可使用本机 GPU 无限时长运行**有限的冻结实验网格**；不得自动调用付费云 GPU、付费 API、私有未授权数据，不得将原始实验资产公开，也不得合并 `main`。
- **资源路径：**Git/worktree、虚拟环境、数据、缓存、临时文件、checkpoint、结果必须尽量位于 `E:\GENESIS`；C 盘只允许不可避免的系统级写入，E 盘不足时停止，禁止无声回退。

## 1. 研究命题：S / M / U / P 四个独立终点

**S — Structure:** 自然训练轨迹中的层间逆曲率是否在非正交 DLN、非线性 MLP、ResNet 和 Transformer 上存在可重复的远距结构？必须区分“固定有限深度的平坦尾部”和“深度增大后仍具有非零高度”。后者不能凭有限几个深度外推为定理。

**M — Mechanism:** 将观测结构拆解为 Jacobian 共享 Gram、秩亏、GGN 零空间、Gauge 规范/非正交重参数化、深度/宽度/尺度效应、残差 Hessian 项与阻尼谱极点。只接受与匹配 null 对照比较后的可复现机制证据。

**U — Utility:** 在同一损失、batch、参数 checkpoint、梯度和阻尼下，比较 Full GGN 与精确 Block-GGN，在允许最佳标量步长校正之后还存在多大优化价值？**不能将逆曲率非对角能量直接等同于优化收益。**

**P — Prediction / Optimization:** 是否能用便宜的 matvec、梯度条件化统计量预报 U 的显著性，并在实际训练中以总体 wall-clock / fixed-budget 指标超过学习率、短 CG、精确层块解及已有优化器基线？P 仅在 U 有真实可确认信号后启动算法研究。

2026 年先行研究已经指出精确逐层 GN 在部分 Transformer 实验中接近 Full GN，因此“必须知道什么情况下 Full 跨层信息不可替代”是优先研究对象，而不是仅发布耦合热图。相关：ICLR 2026 *The Potential of Second-Order Optimization for LLMs*；ICML 2026 *Gradient Smoothing*。

## 2. 旧方案与 v2 设计变更

| 问题 | 现有 PR #11 方案 | v2 设计规则 |
| --- | --- | --- |
| 计算膨胀 | 26×5 + 5×16 条训练，4 checkpoint ×3 λ，按全部层源 16 probes 可能需数十万次逆问题 | 保留全训练和主 U 测量；把高昂的 S/M 结构估计分为预注册的 C-base 与 C-deep；计算密度由 G0 性能实测选择，不由观测结果选择 |
| S2 文本层距不足 | 4 层 Transformer 仅适合 U 的短层距辅助确认 | 除 4 层 U 锚点外，增加 8 层 Transformer S 结构锚点：**S2 改为拟定 6×16=96 新独立训练**，冻结前确认 |
| CE 度量错配 | 任务误差可能使用裸 logit Jacobian 范数 | 主任务响应同时报告带输出损失 Hessian 权重的 **loss-curvature metric**；裸 logit 响应仅作次要诊断 |
| 训练/诊断混同 | G0 NumPy 算子、CI 通过容易误写为科学完成 | 工程 PASS、数值资格、探索发现、确认结果、真实优化收益单独状态；GitHub CI 只做代码门禁 |
| 物理不变量混同 | 距离分组强烈依赖参数化与 grouping | 冻结 coarse / fine 双分组，披露权重重缩放、GroupNorm、共享 embedding 和 skip 结构；不把原始 Hessian 块范数称为天然架构不变量 |

## 3. 系统分层和目录（全部拟实现）

```text
E:\GENESIS\
  worktrees\hessian-landscape-revalidation\
    genesis_gpu\
      cli.py                      # doctor / freeze / run / status / resume / verify / report
      contracts\{models,params,loss,run,artifacts}.py
      env\{gpu_probe,storage_guard,reproducibility}.py
      models\{dln,mlp,resnet_gn,tiny_transformer}.py
      datasets\{registry,manifest,split,loaders}.py
      training\{trainer,checkpoint,recording}.py
      curvature\{ggn_operator,hessian_operator,dense_oracle,dual_solve}.py
      solvers\{cg,block_cg,precondition,diagnostics}.py
      sketches\{block_probe,variance,adaptive_probes}.py
      science\{structure,mechanism,utility,controls,predictor}.py
      study\{design,freeze,seed_split,analysis_plan,statistics}.py
      runtime\{scheduler,worker,resources,atomic_io,resume,watchdog}.py
      audit\{independent_reference,artifact_verify,leakage_checks,claim_ledger}.py
      reporting\{tables,figures,verdict}.py
    configs\{models,training,curvature,study,freeze_rules}.yaml
    tests\{unit,numerical,adversarial,system,regression}\
    scripts\{prepare_E,launch,status,resume,stop}.ps1
  venvs\hessian-landscape\
  datasets\...
  cache\...
  tmp\...
  runs\genesis_full_v2\
    config-locks\ datasets\ checkpoints\ measurements\ probes\ tables\
    logs\ audit\ reports\ figures\ manifests\
```

**三类执行平面：**①科学核（完全无副作用的参数/损失/算子/指标）；②本地执行核（GPU 调度、资源、checkpoint、重试、E 盘 I/O）；③审计核（独立参考算法、预注册统计、原始数据再计算、证据等级及报告）。审计核不得直接调用科学核的同一个 summary 函数“再次确认自己”。

**职责边界：**Trainer 只产出 checkpoint 和训练轨迹；CurvatureEngine 只读冻结 checkpoint；Statistics 只读已落盘 measurement；Report 只读经过审计的表。任何参数随机变更必须有 seed/hash，任何运行副作用必须能恢复/追踪。

## 4. 严格对象与 API 设计

所有输入都先解析成版本化不可变结构，字段至少包括：

- `ModelSpec(model_id, family, depth, widths, normalization, tie_weights, param_group_schema_sha)`；
- `DataSpec(source_uri, license, archive_sha256, split_sha256, transform_sha256, reduction, curvature_batch_sha256)`；
- `ParamSpec(ordered_names, shapes, offsets, groups, tied_alias_map, buffers_sha256)`：训练 checkpoint、GGN operator、Block 计算必须共用**同一维展开顺序**；
- `SnapshotSpec(run_id, seed_cluster, checkpoint_step, checkpoint_sha256, model_sha256, state_buffer_sha256, batch_sha256, loss_spec_sha, precision)`；
- `CurvatureSpec(kind=GGN|HESSIAN, damping_absolute, damping_relative, operator_version, numerical_dtype, symmetry_test)`；
- `SolveResult(direction, converged, true_residual, effective_condition, iterations, wall_time, peak_vram, numerical_status)`；
- `ProbeResult(E_ij_mean, E_ij_se, bin_energy, source_block, probe_seeds, solve_error_bounds, num_probes, status)`；
- `EvidenceRecord(claim_id, estimand, independent_seed_n, artifact_path, sha256, uncertainty, null_comparison, evidence_grade)`。

**抽象接口**：

```python
class CurvatureOperator(Protocol):
    def matvec(self, v) -> Tensor: ...        # (G + λI)v
    def raw_ggn(self, v) -> Tensor: ...       # Gv
    def block_matvec(self, block_id, u): ... # (G_ii + λI)u
    def gradient(self) -> Tensor: ...        # same loss/batch/checkpoint
    def diagnostics(self) -> OperatorReceipt: ...

class ExperimentRunner(Protocol):
    def plan(self) -> FrozenManifest: ...
    def run(self, work_item) -> ArtifactReceipt: ...
    def resume(self) -> StateReceipt: ...
    def verify(self, run_id) -> AuditReceipt: ...
```

**不变量（强制测试）**：同一 `SnapshotSpec` 上的 `g,G,H,J` loss reduction、参数 flatten 顺序、model buffers 和随机 mask 恒定；任一项变化即拒绝比较而不是补算后混接。`Q` SPD 与 `H+λI` 是否 SPD 必须分别记录。参数共享严格使用同一逻辑自由度，不能双重计数。

## 5. 数值算法（不可简化成“用 autograd 算 Hessian”）

### 5.1 Square-loss GGN

对 \(\ell=\|r(\theta)\|_2^2/(2M)\)，\(J=\partial r/\partial\theta\)：

\[G=J^\top J/M,\qquad Qv=J^\top(Jv)/M+\lambda v.\]

`matvec(v)`：冻结参数和 buffer，`torch.func.jvp` 得到 `Jv`，再经 `torch.func.vjp` 得到 `J^T(Jv)/M`。**用严格的 FP64 小型 dense J^T J 和有限差分基准检验完全一致**，再允许 GPU FP32 大型应用。若 JVP 不支持某个算子，使用经过数值测试的 reverse-over-reverse fallback，并明确记录性能/误差。

### 5.2 Cross-entropy GGN

对 N 个监督 logit 向量 \(z_n\)，\(p_n=\operatorname{softmax}(z_n)\)：

\[Gv=\frac1N J_z^\top\left[\bigoplus_n (\operatorname{diag}(p_n)-p_np_n^\top)\right]J_zv.\]

在每个样本/有效 token 上令 `u=Jz(v)`，施加 `H_out(u)=p*(u - sum(p*u))`，再做 `vjp`，按**有效样本/非忽略 token 数**一致归一化。必须与实际 loss 的 `reduction/ignore_index/class weights/label smoothing` 严格一致；首版冻结为无 class weight/label smoothing 的 CE，再将扩展作为单独验证适配器。**GGN 不是 empirical Fisher。**

对于分类、语言模型的任务响应，主指标采用 \(\|H_{\ell,\mathrm{out}}^{1/2}J_z\Delta\theta\|\) 诱导的半范数（用二次型 `u^T H_out u` 计算，不必显式平方根）；裸 logit 范数保留为敏感性分析。这样避免将 softmax 平移零模误判为任务误差。

### 5.3 Exact Hessian

小模型对同一损失计算 \(H v=\mathrm{JVP}_{\theta}(\nabla_\theta\ell,v)\)，并与 FP64 dense autograd Hessian、中心差分逐方向交叉验证。平方损失检验 \(H=G+S\)，其中 \(S\) 为残差二阶项。固定 ReLU mask 不意味着参数 Hessian=GGN。大模型只允许 HVP+谨慎的随机谱诊断，不显式构造完整 H。对不定矩阵不把 CG 作为无条件可用求解器；若需要 MINRES，必须独立验证且将近极点状态标记不合格，不将非 SPD inverse 当作高斯精度矩阵。

### 5.4 线性求解（核心吞吐瓶颈）

- `Full solve`: \(p_*=-Q^{-1}g\)，SPD 情况用经验证的 PCG；可选参数维/双空间（小 output/batch 时 Woodbury）；统一对返回方向重算 true residual。
- `Block solve`: \(p_B\) 的第 i 块是 \(-(G_{ii}+\lambda I)^{-1}g_i\)。block_matvec 必须把 v 只注入 i 块并取出 i 块，使用精确到约定残差的 restricted-CG；**不能用 Adam 对角或简单 K-FAC 近似冒充 precise layerwise GN**。
- `Preconditioning`: 对角 Hutchinson/层块近似仅用于加速迭代，不改变 Full/Block oracle 的定义；预条件器和精确迭代残差独立保存。
- `G0 precision`: 参考小矩阵 FP64 `1e-9` true residual 目标；大模型 FP32 初始 `1e-5`，同时要求 δ/关键 c(k) 在更紧容差下稳定，否则 NUMERIC_UNRESOLVED。前向可信度不由小 residual 单独证明。
- `Performance`: 逐个基准比较前向 AD 与二阶反向 fallback、预条件 CG 与未预条件 CG、参数空间与双空间、batched probes；用 G0 的**运行成本（非科学结果）**确定适配器后冻结。严禁在 S1 数据出炉后因为结果方向选择求解精度。

正式部署前要验证 `torch.func.functional_call` 对参数、buffers、tied weights、随机 dropout 的处理。PyTorch 官方文档说明 `torch.func` 存在部分算子兼容限制，且 forward-mode AD 可能对算子不支持；绝不能假定所有模型“一次封装即可”。

## 6. 逆曲率几何与可扩展随机估计

对 \(R=(G+\lambda I)^{-1}\)，分块 \(R_{ij}\)，每个源层 j 抽 Rademacher \(z_j\in\{\pm1\}^{n_j}\)，其余层为零。求解 \(x=Rz\)，则

\[\mathbb E\|x_i\|_2^2=\|R_{ij}\|_F^2.\]

**核心产物**：\(E_{ij}=\|R_{ij}\|_F^2\) 的估计、probe 方差、solver 残差和精度区间；\(E_k=\sum_{|i-j|=k}E_{ij}\)；\(c(k)=\sqrt{E_k/\sum_{|i-j|=k}n_in_j}\) 除以 k=0 的相同 per-element RMS；非对角 mass；所有 k 都报告。

**数值风险**：源层探针对角受 \(\lambda^{-1}I\) 项支配；同时报告原始 R 和 \(C=R-\lambda^{-1}I\) 的“交互修正”结构。若小 λ 相减出现灾难性消减，优先用已验证的双空间公式/校正算子而不是粗暴相减。RMS、mass 是非线性比例，其随机估计即使 E_ij 无偏，也未必无偏；必须报告比值偏差和置信区间。

**Adaptive probes:** 16→32→64→128→256，每批独立 probe 种子，记录逐 probe 的标量能量而不是保存全部 GB 级求解向量；达到预先定义的数值精度就停止，否则保留 `UNCERTAIN`。针对所有重要分块层距，给出 MC 不确定度和 solver error 的分离估计，不能把 0.0001 的噪声负值裁成 0 后宣称衰减。

**可选的优化器/估计器**：多源块编码探针、全局成对探针估计器、Hutch++/low-rank 修正、复用 CG Krylov 空间、block probe batching。它们可以缩减求解次数，但其每个 E_ij 必须先在 G0 对真实 dense inverse 做无偏性/偏差/方差及总耗时对照；验证失败就退回块支持 Rademacher。严禁把同一求解轨迹上的相关 probe 当成独立训练 seed。

## 7. 计算密度管理：A/B/C 三层计划

**A：训练状态台账，全面覆盖。**每个种子固定训练 checkpoint 0、1/3、2/3、1，记录 loss、gradient、train/validation 指标、参数规范、谱尺度、状态哈希、显存和 wall-clock。训练轨迹全部采集，禁止仅挑出拟合尾部明显的状态。

**B：主要 U 全覆盖。**为所有数值合格状态及三档预注册相对阻尼计算 Full-GGN、精确层块-GGN、最佳 ray scalar、δ、E_task、E_val、少步等成本 CG 及真实 line-search。极端条件数/不收敛明确标注，不要用便宜对角解代替精确比较。此层可有 CPU/GPU 求解精度适配，但不能有数据驱动的抽样偏差。

**C-base：预注册结构档。**S1 在每条轨迹的 checkpoint 0 和终点，γ=1e−2，估计完整层块/层距 profile（主要 S 候选限 L≥8；短 L 仍记录总跨层 mass）。S2 在同样两状态同时使用 γ=1e−2 和 1e−1，以保证阻尼稳健性。选择规则在首次 S1 科学结果前固定。

**C-deep：机制档。**在每个架构的预先选定/哈希选定 seed，以及全部 S2 结构锚点，扩展到最多 256 probe、跨 λ、spectrum/gauge/nullspace controls、exact H 小模型子集。可以按 G0 预先测出的 MC/solver 性能升级精度，不得按高平台高度挑样本。

**数量提示：**旧方案若对每个状态、每档 λ、每个源层做 16 probe，按模型名近似视为层块数，S1/S2 合计可能超过 40 万次 SPD 线性求解。v2 C-base 降低主结构估计密度到若干预先指定的状态，但严格保留全部种子、全部 B 层任务测量以及 S2 两档阻尼结构确认。真实 CG 迭代数、Gv 时间和显存只能在 G0 得到，不可事先声称一个小时数。

## 8. 模型、任务、训练与冻结矩阵

### S1 发现集（26 个 setting × 5 新独立 seed = 130 次训练）

| 架构 | Setting 定义 | 固定训练任务 / 约定预算（仅为冻结前默认） |
| --- | --- | --- |
| DLN 16w | 4/8/16 深度 × 平衡/非平衡 × 协方差条件数 1/100，共 12 setting | 由 seed 生成的固定 teacher，Adam，4000 steps，batch 256 |
| DLN 32w | 4/8/16 深度 × 平衡初始 × 条件数 1，共 3 | 同一目标家族、独立新 seeds，4000 steps |
| MLP | 3/6/12 深度 × ReLU/tanh，共 6 | MNIST，宽 128，AdamW，20 epochs |
| ResNet | GroupNorm ResNet8/20，共 2 | CIFAR-10，SGD momentum，80 epochs；无 BatchNorm 运行状态混淆 |
| Transformer | 2/4/8 层，d_model=192，6 heads，共 3 | 经过许可核查的小型字符级语言模型；固定有效 token、上下文 128、默认每 seed 50M 训练 token |

以上为**候选冻结值**，不可宣称已运行；G0 资源/数值预检后冻结 train batch、effective batch、token/epoch、LR schedule、数据增强、dropout、层分组。因 12GB 显存所需的微批大小可在 G0 预先定义，同时保持 effective batch/更新次数与目标函数不变。类别/序列任务的 curvature batch 也必须有明确版本与大小，不能每次调用随机取不同样本。

### S2 确认集（v2 拟修改为 6 锚点 ×16 新 seed = 96 次训练）

1. 非平衡 DLN L8，非各向同性输入；
2. 非平衡 DLN L16，非各向同性输入；
3. ReLU MLP L6（主要 U/M 对照）；
4. GroupNorm ResNet20（视觉 S/U）；
5. Transformer L4（文本 U）；
6. **新增 Transformer L8（文本 S 的长层距确认）**。

每个锚点固定 16 个与 S1 绝不重叠的新训练 seed。S2 始终执行，即使 S1 没有任何显著正结果；如发现集有可信正/负对照，可按**提前冻结的选择规则**另加两个设置各 16 种子，但不可在观察结果后任意更改规则。用独立 seed-cluster 而不是 checkpoint/λ 行进行不确定性估计。

### S3 条件性优化器试验

仅 U/P 均通过前述科学门禁时进入跨视觉/文本的在线优化器试验，和 AdamW、精确 layerwise GN、同成本短 CG、适用的 SOAP/K-FAC、Gradient Smoothing 比较，包含等量超参搜索、同样 token/sample 数据顺序、总 wall-clock、固定预算性能、峰值显存和失败率。Full GN 在可计算的小网络仅作离线 oracle，不能当作“无需计算成本”的在线优化器。未过门禁时只执行已冻结的轻量负对照，记录合法 `S3_NO_GO`。

## 9. 机制、强对照与主要科学反例

- **DLN 代数对照：**零残差、正交平衡和 rank-one toy 可以得到平坦距离谱，且高度可能随 1/L 衰减；不得把这当作新的无限深度平台规律。
- **真实训练：**固定 teacher/目标，沿同一轨迹保存 checkpoint；禁止将零残差替换目标当作“训练产生相变”。
- **固定矩阵 λ 扫描：**在同一 H/G/g 上只改变阻尼，记录极点距离、条件数、正定状态。
- **Gauge 重参数化：**变换前后输出函数相同，记录参数 Hessian、λI 和层块范数如何变；如果变化很大，声明坐标依赖而非纯架构固有规律。
- **随机几何 null：**共同置换矩阵的层块行列、谱匹配随机子空间、梯度方向旋转、等秩随机模式和宽度/参数量对照。共同置换矩阵与梯度的效用值通常坐标不变，不能当作“层距影响训练”的证据。
- **S 测度边界：**层数少于 8 的网络主要贡献 U/M；远距结构候选依赖 L≥8，组内 per-element RMS 和 grouping 锁定，包含全部极端尾 bin。
- **M 因果审计：**nullspace-projector 对 GGN 数据梯度的贡献可能为零，但有限 λ 的横向模态不可删除；不允许将一部分负曲率与 Gauge 的重叠称为“全部负特征值来自 Gauge”。
- **模型族外推：**同一数据集不同 seed 不等于独立数据集；报告条件性家族结论，不夸大为普遍定理。

## 10. 主终点、统计计划与科学门禁

对同一 SPD \(Q=G+\lambda I\)、\(D=\operatorname{blockdiag}(Q)\)，\(p_*=-Q^{-1}g\)，\(p_B=-D^{-1}g\)；令

\[\alpha_Q^*=-\frac{g^\top p_B}{p_B^\top Qp_B},\quad
F_*=-\tfrac12g^\top p_*,\quad F_B=\frac{(g^\top p_B)^2}{2p_B^\top Qp_B},\quad \Delta=1-F_B/F_*.\]

**两个 alpha 不要混淆：**上述 \(\alpha_Q^*\) 最大化二次模型下降；训练输出响应误差的最佳 \(\alpha_{\rm task}^*\) 则要在训练 batch 上用 W 加权投影另行拟合，**E_val 必须沿用训练得到的 \(\alpha_{\rm task}^*\)**，不能在验证集重新调。令 \(u=Jp_*,v=Jp_B\)，则 \(\alpha_{\rm task}^*=\max(0,u^T Wv/(v^TWv))\)，\(E_{\rm task}=\sqrt{(u-\alpha_{\rm task}v)^TW(u-\alpha_{\rm task}v)/(u^TWu)}\)；MSE 取合适的单位权重，CE 取正确的输出损失 Hessian。全部分母接近零时按预冻结规则标记 NOT_ELIGIBLE。

**拟议内部继续阈值（冻结前可修订，执行中不得修订）：**

- **S：**真实非平衡/非线性条件下、有限深度远距尾部可测且对预定义 matched null 显示超出误差的差异；再独立评价幅度是否随 L 衰减。主要筛选基准可用 tail CV≤0.15、幅度≥0.02，并要求数值/MC 误差显著低于信号。单个 L 的 flatness 不是 S-depth PASS。
- **U：**在至少两个预先指定非平凡条件（至少一个非线性）里，seed-cluster median Δ≥0.05、95% cluster bootstrap 下限>0.01、至少两档固定 λ 满足且无数值病态。必须保留不合格比例和多重检验控制；上述是项目管理门槛，不是领域公认阈值。
- **P：**预测正类 Δ>0.05，在独立 seed holdout 上 AUROC≥0.75，且比最强预注册廉价基线高≥0.10；如正类过少无法定义 AUROC，则只按预先锁定的连续指标（如 Spearman/MAE）判断，不事后变换阈值。
- **S3：**预先锁定实际 time-to-target 至少 10% 的中位改进和配对 seed 区间支持改善，报告全部 curvature/matvec/调参成本；对理论或观察性论文，不能用没有实际 S3 的结果宣称优化器提速。

每个 setting 的 checkpoint/λ 多次测量属同一 seed cluster；主要置信区间按 seed 层重抽样（例如 2000 次），确认集事先登记的多重检验使用 Holm 或已确定的层级检验；同时公开全部主、次指标、负结果、模型族差异和缺测机制。`NUMERIC_UNRESOLVED` 不是负结构结论。

## 11. RTX 4070 Ti 12GB 与 E 盘资源工程

**GPU:** 仅一个 active CUDA job；CPU 可提前加载数据/解析日志。显存目标 9.5 GiB（是预警目标，不是绝对硬件物理限制）；测量 `torch.cuda.max_memory_allocated`, `max_memory_reserved` 和设备总体 VRAM，占用分项与其他进程区分。保持负载内存稳定，超标按 G0 冻结的 microbatch/activation checkpointing 回退，不以减模型/换任务掩盖科学不合格。对 GGN 默认禁用混合精度，至少 FP32；小模型 FP64 参考可在 CPU 上实现，避免消费者卡 FP64 慢导致误判。

**持久化:** 以 `E:\GENESIS\runs\genesis_full_v2` 为结果根目录，所有 Python venv、pip/uv/HF/torch/CUDA/Triton/Numba caches 和临时文件指向 E 盘。由进程级环境脚本设置，不修改全局 Windows 目录、Pagefile、用户 Profile。任何 worker/reboot 恢复都须重新设置；E: 不存在/不足时 `STORAGE_BLOCKED`，不得回退 C:。

**磁盘：**启动 G0 记录 C/E 总量/剩余；通过试运行实测每个架构每 checkpoint 平均和极值字节，估算 S1/S2/S3 占用。保留固定空闲安全裕量（拟定 max(30 GiB, 下一阶段预计写入量 20%)，按 E 盘真实容量冻结）。原始 checkpoint 可保留必要可重算版本+完整哈希；不要每次将完整 probe 解向量落盘，每 probe 保存 source block、seed、E_ij、CG 真残差、耗时、数值失败与重算依据，预注册抽样子集保存完整向量用于独立核验。

**调度:** 主进程 SQLite WAL / 原子 JSONL 单写者，work item 用 `(protocol_sha,setting,seed,ckpt,lambda,diagnostic)` 确定性 ID；状态 `PENDING→CLAIMED→RUNNING→COMPLETE/NUMERIC_UNRESOLVED/FAILED/INTERRUPTED`；单 GPU worker、带心跳和 Windows PID 识别，暂停/继续只影响当前任务。单个 run 的输出先写临时目录，校验 SHA 后同卷 atomic rename；中断重启先核查证据再恢复。所有执行在独立 Windows 进程中，不依赖 Codex 对话持续在线。

**少 token：**Codex 只在工程设计/复杂失败修复/科研独立审计时介入；每 seed、每 λ、每 probe、每普通 OOM retry 的 LLM 调用均为 0。调度、运行、画图、统计、报告模板全部由确定性 Python 实现；Codex 默认读取 2 KB 状态摘要而不是百万行日志。允许最多两个明确分工的子 Agent 进行代码模块审计，不允许每个实验实例创建 Agent。

## 12. CLI 合同、状态机和结果格式（均未实现）

```text
genesis doctor --device cuda:0 --storage E:\GENESIS
genesis prepare-data --config configs/study_v2.yaml
genesis g0 --all --save-reference
genesis freeze --config configs/study_v2.yaml --analysis configs/analysis_v2.yaml
genesis plan --stage s1 --dry-run
genesis run --stage s1 --resume
genesis status --json
genesis run --stage s2 --unlock-only-after-s1-adjudication
genesis adjudicate --stage s1,s2
genesis run --stage s3 --only-if-gate-pass
genesis verify --independent --all
genesis report --format md,html
```

**研究系统状态：** `DESIGN_ONLY`, `ENV_READY`, `G0_NUMERIC_VALID`, `PROTOCOL_FROZEN`, `S1_EXECUTED`, `S1_ADJUDICATED`, `S2_UNLOCKED`, `S2_EXECUTED`, `S2_ADJUDICATED`, `S3_DONE|S3_NO_GO`, `QA_PASSED`, `COMPLETE_POSITIVE|COMPLETE_MIXED|COMPLETE_NEGATIVE|INCOMPLETE_BLOCKED_EVIDENCE`。不能因 `pytest PASS` 将 `S1_EXECUTED` 自动升级为科研结论。

**必要机器可读输出：** `env-lock.json`, `protocol-lock.json`, `study-matrix.csv`, `seed-manifest.json`, `checkpoints.csv`, `numerical_eligibility.csv`, `all_block_energies.parquet`, `probe_results.parquet`, `utility_all_states.parquet`, `null_results.parquet`, `run_status.sqlite`, `manifest_sha256.txt`, `claim_ledger.csv`。文件名及 schema 仅为设计建议，但每条科学主张必须能经 `claim_id → estimator definition → run IDs → checkpoint/data/config/source SHA → raw arrays → independent verifier` 闭环追踪。

**完整报告：** `SCIENTIFIC_VERDICT.md`, `S_M_U_P_RESULTS.md`, `NUMERICAL_QA.md`, `NEGATIVE_RESULTS.md`, `STATISTICAL_ANALYSIS.md`, `REPRODUCTION.md`, `RESOURCE_ACCOUNTING.md`, `FIGURE_INDEX.md`, `INDEPENDENT_VERIFIER_RECEIPT.json`；至少包括每个架构/深度的失败率、完整 λ 曲线、原始与校正后的层距谱、Task Utility、Strong Null 对照和独立 S2 结论，图表可由原始 CSV/Parquet 一键再生。

## 13. 独立 QA 和对抗测试（必须先于大实验）

**数学正确性**：2×2 SPD 同矩阵不同梯度 η=1 vs η=0.19、rank-one 解析平台、GGN PSD/阻尼 SPD、反例 exact-H 非 SPD、导数差分/JVP/VJP/HVP、有限 λ 反例、非等尺寸分组公式、CE softmax shift 零空间；全部必须与独立小 dense 实现一致。

**数值正确性**：同一 model checkpoint 和 batch 下 dense GGN 对照 matrix-free，精确 D_i 反演对照 block-CG，真 residual vs 估计 residual，精度收紧稳定性，病态谱与近极点失效状态，逆块 probe 预期/方差/负对照及不同 seed 的 MC 区间覆盖率。

**系统健壮性**：随机 kill GPU worker、Windows 进程终止/重启、E 盘断开/空间不足、数据集 sha 不匹配、单个 checkpoint 损坏、缓存指向 C 盘、并发重复提交、stdout/日志写入失败、模型/组数更改、训练/确认 seed 泄漏；所有注入必须有预期错误码且不得污染已有 `COMPLETE` 记录。

**独立科研 QA**：在独立脚本路径从 checkpoint 重建 g 和 Gv、与主曲率模块比较，抽取已存 probe seed 重算 block energy、逐 claim 对应统计与原始 run_id，复核 CI 按真实 seed cluster、对所有失效记录不删除不挑样本。主作者的 report writer 和 QA 不能共用唯一的核心聚合函数作为“独立验证”。

**回归/CI**：GitHub CPU CI 执行纯 NumPy/dense 小规模测试与 schema、文档链接及安全扫描；真实 CUDA G0 需在 RTX 4070 Ti 上运行并保存设备收据，不能用 GitHub 的 CPU CI 绿灯替代本地 GPU 数值验收。

## 14. Codex 未来实施里程碑与产物验收

| 里程碑 | Codex 应交付（未来） | 验收条件 |
| --- | --- | --- |
| D0 规格冻结候选 | 所有 schema/config/模型分组/阈值/seed 规划，review & risk register | 所有主张有定义；无旧数值结果作目标；S2 隔离 |
| D1 底座 | E 盘环境 bootstrap、设备监控、CLI、日志、状态机、checkpoint、资源保护 | 对抗 E/C、进程中断恢复与 SHA 故障测试通过 |
| D2 数值核心 | loss-specific GGN/HVP、dense/dual/CG、准确 block solve、层块 sketch | MSE+CE cross-check，数值边界、全套小基准 PASS |
| D3 模型训练 | DLN/MLP/GN-ResNet/Tiny Transformer，公共数据/许可/可重现训练 | 每族 GPU preflight 可复现；不同 seed/固定目标一贯 |
| D4 科学与统计 | S/M/U/P、nulls、bootstrap、holdout、raw-data-independent verifier | 预注册度量与独立 QA，数值单位/显著性测试 PASS |
| D5 G0 资源冻结 | 四族端到端真实 GPU 干跑、性能/容量估计、协议哈希锁 | 能估算运行成本而不看 S1 结果；冻结不可变 |
| D6 S1 执行 | 130 轨迹及分层测量、自动恢复、失败台账 | 预设所有 setting 有完整或明确 invalid 证据，独立 QA |
| D7 S2 确认 | 拟定 96 新独立种子训练及其预定义测量 | 没有 S1/S2 seed 泄漏，不事后改阈值；明确正/负/不确定 |
| D8 S3 / 论文级报告 | 满足门禁才跑真实优化器；最终独立报告和可审查 PR | 结构/机制/任务/算法四轨分别裁决，原始数据可逐 claim 再生 |

**不得只“搭好框架”就认为用户要求已实现。**最后完成时要提供真实的 `--status` 运行总表、GPU 时长、有效种子数、完整矩阵/曲线汇总、科学负结果、独立审计收据和 Git SHA。若硬件/数据权利/GGN 真实性无法解决，则诚实输出 `INCOMPLETE_BLOCKED_EVIDENCE`，记录已完成与尚缺部分。

## 15. 冻结前最关键的设计决策

1. **S2 从 80 扩到 96**：建议单独增加 Transformer L8 的文本结构锚点；正式锁定前明确是否同意。若仍维持 80，则应降低“文本上 S-long-range 结构已确认”的声称范围。
2. **C 层测量密度**：采用所有 eligible seed 的固定始末 checkpoint、指定阻尼的 C-base；加锁定随机/分层的 C-deep 子集，避免全部状态全阻尼每层 16+ probes 的爆炸成本。必须通过 G0 耗时/方差预检，并事前冻结计算精度与升级规则。
3. **真实优化收益的算力公平**：精确 full/layerwise 是科学 oracle，不等于部署成本；各在线基线对比必须算 matvec/预条件和超参搜索时间。
4. **软件版本与数据许可证**：以本机 CUDA/PyTorch 稳定兼容版本、模型代码与许可完整锁定，不提前假定能用某一版本的 torch.func 组合。
5. **零与负结果同样完成**：不允许无限试随机种子、无限迭代调模型直到出现“足够好”的平台。

## 16. 官方实现与研究参考（设计阶段核对）

- PyTorch `torch.func` API： https://docs.pytorch.org/docs/stable/func.api
- PyTorch `functional_call`： https://docs.pytorch.org/docs/stable/generated/torch.func.functional_call.html
- PyTorch CUDA Memory： https://docs.pytorch.org/docs/stable/notes/cuda.html
- PyTorch Windows CUDA install： https://pytorch.org/get-started/locally/
- ICLR 2026, *The Potential of Second-Order Optimization for LLMs*： https://proceedings.iclr.cc/paper_files/paper/2026/hash/c8e9a2beb84ab1a616edb89581c4b32a-Abstract-Conference.html
- ICML 2026, *Gradient Smoothing*： https://proceedings.mlr.press/v306/meng26j.html

---

**最终说明：**本蓝图只设计，不运行、不向 GitHub 写入、不修改 Windows 的 C/E 盘。下一步只有在用户批准方案后，才把它变为真实代码及可执行 Codex Goal。
