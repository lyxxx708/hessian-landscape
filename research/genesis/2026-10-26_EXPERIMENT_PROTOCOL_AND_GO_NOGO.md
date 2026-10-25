# GENESIS 可执行研究协议：任务相关逆曲率、Hessian–GGN 差异与 Go/No-Go 门槛

> **状态：PROPOSED / NOT EXECUTED。** 该文件是建议采用的研究预注册草案，不代表已经获得资源许可、执行了任何训练、锁定了外部 confirmatory 数据或完成了科学复现。  
> **配套决策报告**：[研究价值与主会裁决](2026-10-26_RESEARCH_VALUE_AND_CONFERENCE_DECISION.md)  
> **已存在的基础工程**：[P0 draft PR #6](https://github.com/lyxxx708/hessian-landscape/pull/6)。其新 12 层 DLN 合成实验证实了某些解析控制，并非原始 2025 复现。  
> **授权原则**：新训练需单独确认运行资源、代码版本与数据授权。不能擅自使用封存 holdout、confirmatory 或未获许可的私有资源。

## 0. 核心裁决问题、严格定义及输出

**主要科学问题 RQ-A**：在公平的阻尼、步长、曲率对象条件下，忽略层间 GGN 耦合是否产生真实、稳定、可预测、不可由一个标量步长消除的任务更新误差？

**次要问题 RQ-B**：同一训练 checkpoint 的残差二阶项 S 在什么谱与任务对齐条件下使精确 Hessian 相较于 GGN 的更新产生实质区别？此区别能否在 SPD 安全阻尼下维持？

**第三问题 RQ-C**：在归一化后的深度、宽度、输入协方差、层间尺度及规范变换中，上述效应何时消失？现有宽网络 Fisher 近似理论的适用条件是否构成完整解释？

**算法问题 RQ-D**：若存在重要且可预测的误差，能否用低复杂度校正提供超出已有方法的实际速度收益？

在 RQ-A/RQ-B 未通过前不启动 RQ-D 的大规模工程。**主要输出不是热图，而是一组同一梯度下的更新、预测和实际优化验证**。

## 1. 数学对象与唯一指标合同

对每个固定训练状态，使用**同一个损失函数、同一个样本批次、同一个参数顺序和梯度**：

$$
\mathcal L(\theta)=\frac1{2M}\|r(\theta)\|_2^2,\quad
J=\frac{\partial r}{\partial\theta},\quad
g=\frac1M J^\top r,\quad
G=\frac1M J^\top J,\quad
H=G+S.
$$

$$
A_\lambda=G+\lambda I,\quad
D_\lambda=\mathrm{blockdiag}(G)+\lambda I,\quad
d_*=-A_\lambda^{-1}g,\quad
d_B=-D_\lambda^{-1}g.
$$

**指标类型固定**：

| 名称 | 精确定义 | 用途及限制 |
|---|---|---|
| Block-RMS(k) | 以有序层对平均的 ‖(A⁻¹)_{ij}‖_F² 的平方根 | 只描述几何；等块才能直接按历史归一化 |
| OffdiagMass | ‖Mask_off(A⁻¹)‖_F²/‖A⁻¹‖_F² | 不是训练性能，不能自动解释梯度 |
| RelativeSolverResidual | ‖A d+g‖₂/(‖A‖₂‖d‖₂+‖g‖₂) | 衡量后向数值一致性，不保证前向误差 |
| E_param | min_{a≥0}‖d_*−a d_B‖₂/‖d_*‖₂ | 参数方向差异；会受 nullspace/gauge 影响 |
| **E_task（主指标）** | min_{a≥0}‖J_train d_*−a J_train d_B‖₂/‖J_train d_*‖₂ | 排除单一学习率缩放后的训练输出响应失配 |
| E_val | 使用训练得到的 a*，计算 ‖J_val d_*−a*J_val d_B‖₂/‖J_val d_*‖₂ | 留出输入的一阶响应差异；不得重新拟合 a* |
| E_D | ‖D^{1/2}(d_*−d_B)‖₂/‖D^{1/2}d_*‖₂ | 易于谱分析的白化参数误差，不等于 E_task |
| **E_D,scale** | min_{a≥0}‖D^{1/2}(d_*−a d_B)‖₂/‖D^{1/2}d_*‖₂ | 白化空间去步长误差 |
| OneStepGain | L(θ)−L(θ+t d)；t 由相同预算的预指定 line-search 选择 | 实际非线性目标变化；单步不能证明长期优化 |
| ComputeAdjustedTime | 到同等训练损失阈值的 wall-clock，含曲率求解/刷新 | 仅在研究 RQ-D 时作为主要工程指标 |

**未定义处理**：若 ‖J_train d_*‖₂≤预先固定的数值资格阈值，E_task 不作为 0 或 1，须标记 NOT_ELIGIBLE 并统计比例。预设相对资格阈值可采用 1e−10×max(1,‖J_train‖₂‖d_*‖₂)；改变阈值须保存审计记录。

注意 A=G+λI 对 λ>0 为 SPD，而精确 H+λI 可能不定；不能把二者混成一个分析矩阵。若模型有 weight decay，必须把其对 g/H 的贡献以独立字段记录，不能假定数据残差梯度公式仍覆盖整个正则化目标。

## 2. 关键解析对照：什么情况下只改变步长？

令

$$
K=D_\lambda^{-1/2}(A_\lambda-D_\lambda)D_\lambda^{-1/2},\quad
b=D_\lambda^{-1/2}g,\quad
z=(I+K)^{-1}b.
$$

设 K=U diag(κ_i)Uᵀ，κ_i>−1，b_i=(Uᵀb)_i，w_i=b_i²/‖b‖²（b≠0），f_i=1/(1+κ_i)>0。

则**去标量尺度的白化误差**满足精确恒等式：

$$
\boxed{
E_{D,\mathrm{scale}}^2
=1-\frac{(\sum_i w_i f_i)^2}{\sum_i w_i f_i^2}
=\frac{\operatorname{Var}_{w}(f)}
{\operatorname{E}_{w}(f^2)}.
}
$$

推导：白化后的两个方向分别为 z_i=f_i b_i 与 b_i；最优缩放 a*=〈z,b〉/‖b‖²=Σw_i f_i>0。这个量**等于零当且仅当** b 的非零投影仅落在 f 相同（即 κ 相同）的谱子空间中。若多个不同 κ 的模态被任务梯度同时激活，白化参数更新才存在不可由标量恢复的方向差异。

**本式不是新理论贡献**，是本研究的诊断控制；重要的是验证在神经网络中，它与任务空间 E_task、训练效果有怎样的具体对应关系。它可能很大而 J 投影后的 E_task 很小，因此**不得用其替代主要指标**。

**必须区分**：
- diag[(G+λI)⁻¹] 与 (diag G+λI)⁻¹ 是不同的近似。
- 在 rank-one G=11ᵀ 例子中，相对算子误差可以很大；但本例的真实平方损失梯度落在 span(1)，去标量方向误差可以为 0。它是阴性对照，不是优化提升结果。
- 对平方损失数据梯度 g∈range(Jᵀ)；GGN 的零空间放大不是自动的任务效应。

## 3. 研究假设、可证伪的反结论

### Primary hypothesis H1

存在可预先刻画的训练条件（有限宽度、层尺度不平衡、非各向同性输入、非零残差或训练中间状态），使 E_task 高于纯数值误差、并且在合理阻尼和步长校准后**稳定存在**。

**反结论 H1-0**：在相同损失/梯度与光谱安全条件下，所有可观察差异主要由全局标量步长补偿、极点接近或不合理数值容差消除。

### Predictive hypothesis H2

白化谱的梯度加权离散程度、层相关性与数据谱构成的有限复杂度预测器，可在完全留出 seed family/depth/covariance condition 上预测 E_task，并优于仅用 κ(A)、‖G_off‖_F、OffdiagMass、‖g‖ 的简单基线。

**反结论 H2-0**：候选指标在留出设置上不增加预测力；所谓相关性只存在于拟合数据中。

### Hessian-gap hypothesis H3

某些训练状态下，即便 ‖S‖_F/‖H‖_F 小，任务相关的精确 H 与 GGN 更新也可能不同，并能由 δ_λ=‖(G+λI)⁻¹/² S (G+λI)⁻¹/²‖₂ 或更细的梯度对齐解释。

**反结论 H3-0**：所有差异只出现于 H+λI 不定、距离负特征值极点过近或者目标函数被换掉的控制设置；SPD 安全区中无新解释需求。

### Engineering hypothesis H4（仅 H1/H2 通过后）

基于被证实为重要的结构选择小数量全局模式，可以在可比较实际时间/存储预算下优于块近似和强二阶基线，而不是仅用更大的计算成本取得更好的 oracle step。

## 4. 模型/数据与对照矩阵：先便宜后昂贵

### Panel A — 必备解析与导数正确性

| 任务 | 必测对象 | 预期（正确性，而非新科研） |
|---|---|---|
| 标量 L=2,4,12,100 DLN | 精确 rank-one R；BlockRMS；offdiag；opnorm | 复核 c=1/(L−1+λ) 与 opnorm ratio=(L−1)/(L+λ) |
| 12 层 10×10 正交 DLN | P0 新实现 1200 参数、λ 固定 | 验证严格平坦和 8.27% offdiag；不可称旧实验复现 |
| 小型非零残差 DLN | autograd exact H，解析 J、S、HVP | H−G−S 残差数值为 0；权重和目标定义固定 |
| 秩受限随机 J | Woodbury direct inverse / solve | 正阻尼下 residual 与 64/100 类秩界一致 |
| 两参数非退化小例子 | 全曲率与块对角同 g | 有意构造 E_task>0，对照 rank-one 的步长可补偿情形 |

任何一个测试失败，**暂停后面的科学拟合**。Panel A 属于 correctness suite，不进入主会贡献清单。

### Panel B — RQ-A 探索性因子设计（仅供预算与代码设计；需锁定后执行）

- **网络**：无偏 DLN；深度 L∈{4,8,12}、等宽 d=8 为第一批；可增设 d∈{4,16} 做宽度验证。优先参数规模 P≤1200，以便显式 G 的可靠 FP64 oracle。
- **教师与输入**：教师映射固定于每个 seed cluster；X 行采样具有规范化相同迹的协方差，其条件数分为 {1,10,100}；训练/验证输入不共享 RNG。必要时区分 noise-free 可实现任务与指定噪声水平，但绝不能在对照组间暗换目标函数。
- **参数状态**：每次训练的相同、固定损失中收集初始 / 中期 / 后期 checkpoint；具体步数在探索前冻结。并记录 loss、‖g‖、rank(J)、层尺度、残差量。**训练轨迹状态无需谎称已是局部极小值**。
- **种子单位**：6 个探索 seed clusters，每簇固定数据谱采样、teacher、初始化、训练器；同簇多个 checkpoint/λ 属于重复测量，不得在统计中视作独立样本。
- **阻尼**：λ=η·s_G，η∈{10⁻³,10⁻²,10⁻¹,1}，s_G=max(λ_max(G),10⁻¹²)。同时记录绝对 λ、λ_min(A) 与 cond₂(A)，且不允许事后选一档画“最佳平台”。与 PR6 的绝对阻尼对照时需额外注明口径差异。
- **主比较**：full-GGN、blockdiag-GGN、block-tridiagonal-GGN（先检查 SPD/用明确修正）、rank-matched 随机修正、需要时 band+lowrank。第一批不把 AdamW/K-FAC 与精确 GGN oracle 直接当同类型曲率矩阵比较。
- **主输出**：E_task 与 E_val、E_D,scale、最优标量 a*、真实 loss line-search、一致的曲率 solve 精度；测量相应便宜预测变量。

探索性任务规模约 6 seeds × 3 depths × 3 input regimes × 3 checkpoints = **162 个固定状态**，每状态 4 档 λ 产生 **648 个同状态 update 比较**。这是预设设计数量，**不是已执行次数**。如果计算成本过高，预先减少因子并记录，不许在看过结果后隐性挑样本。

### Panel C — 留出确认（只在 Panel B 有实际信号后启用）

- **独立于 Panel B 的生成种子和 teacher/data**，建议 12 个 seed clusters。
- 锁定两个结构设置（一个预期有效，一个预期无效）、两个深度/数据谱切片、两个阻尼，不再微调模型假设或筛出失败样本。
- 保存所有合格和不合格状态，报告资格覆盖率；任何资格排除必须有预先批准的规则。
- 主要分析以独立 seed cluster 聚合；对多重 hypothesis / 多 λ 的检验采用预设层级检验或校正，置信区间通过 cluster bootstrap 并明确 resample 单元。
- 留出阶段若失败，应报告失败；不应将其转为另一个探索集并继续声称“确认”。

### Panel D — RQ-B 的精确 H 对照

- 取 Panel B 中按**预设规则**选定的代表性 checkpoint（例如按 seed/depth/regime 全覆盖的有限子集；不能只挑 E_task 最大的）。
- 在同一 checkpoint/批次/g/λ 下构造 H、G、S 和各自的更新；对 H 的 shift 保留原始不定矩阵描述，**只在 λ>−λ_min(H) 且有记录的安全裕量下比较 SPD 预条件更新**。
- 记录 ‖S‖_F/‖H‖_F、δ_λ、极点距离 min|μ_i(H)+λ|、cond₂(H+λI)、Jd 和实际 loss line-search。
- 同时做“固定 H 的 λ 扫描”与“固定目标训练轨迹的 checkpoint 扫描”，明确二者不同，禁止把前者解释成训练相变。
- 量化计算前向误差：数值条件适中时 FP64 直接解与独立 solver 一致；极端条件数时应抽样用高精度或可靠的高精度参考，不得仅凭很小 residual 宣称可靠。

### Panel E — 推广（只有前面过关）

小型 MLP（ReLU/tanh）、宽度与深度控制、残差结构；先在 P 可显式算 H/G 的设置验证同一诊断，再用 HVP/GGN-vector + Lanczos/CG 扩展。ReLU 即使门控模式不变，跨层参数依然非线性，不能假设 exact H=GGN。设计里单独记录训练状态和门控改变。

不在证据不足时直上完整 Transformer Hessian：例如 P=600,000 的 FP64 dense H 约 2.88 TB，尚未包含分解工作空间。需要矩阵自由路线和经过小矩阵 benchmark 的诊断近似。

## 5. 关键负对照（防止伪发现）

| 控制 | 实验方法 | 排除什么 | 禁忌 |
|---|---|---|---|
| 平衡正交零残差 DLN | 共 Gram 层块、Woodbury | 平台只是平衡性造成 | 由于 g=0，不可拿它检测任务梯度更新 |
| 秩一标量网络 | exact rank-one 闭式 | Offdiag/算子量大但更新可能只差步长 | 不能误称新反例理论 |
| 非各向同性 vs 各向同性 | 保持输入总能量与教师尺度 | 全局非局部性是否只是数据谱 | 不可同时改变输出目标和模型增益 |
| 同谱旋转 Jacobian 基准 | J→JQ、g 随同一残差正确变换；保持 JJᵀ | 层分组几何是否超出低秩数据矩阵 | Q 旋转通常不是网络真实规范变换；仅是诊断 null |
| 规范保持的层缩放 | 仅改变分解而保持函数/训练输入目标一致 | 参数坐标依赖 | 固定 Euclidean λI 不自动随变换协变 |
| fixed-matrix λ sweep | 完全不改变 H/G、g、目标 | 谱极点与强阻尼的作用 | 不能说是随训练动态转变 |
| 模态 rank-matched | 真实子空间 vs 同 rank/谱权重随机控制 | “切掉很多模态自然改变范数” | Mask_off 后的模态范数不具可加性能量解释 |
| 曲率模型 fitting null | refit Chain/Global/Mixed 及谱保持几何 null | 事后拟合平台 | 对任意块做独立置换可能破坏 PSD，不能直接作为优化器输入 |

尤其需要防止**坐标重标号无效 null**：同时把矩阵和梯度做同一正交置换，许多标量更新指标本来会严格不变；不能因此得到架构相关结论。几何 null 只是基准，不代表一个物理可实现的神经网络。

## 6. 预测模型比较与禁止事项

**最低对照**：仅 λ/‖G‖；cond₂(A)；‖offdiag(G)‖_F；OffdiagMass(A⁻¹)；梯度范数；层尺度方差；联合线性/岭回归。新模型使用白化 κ_i 谱权与梯度投影权 w_i，优先低复杂度、解析可解释形式。

- 主要标签应为 E_task 和经步长公平校准的一步训练增益，而不是 E_D,scale 自身。
- 如果候选预测器直接输入全部 J、G、g，再输出由这些对象完全决定的 E_task，属于**重算指标**而非新的廉价预测能力；必须报告额外计算开销。
- 训练集选择代理特征和阈值，留出种子/深度/谱设置只做一次预设评估。
- 报告留出 R²（可为负）、Spearman、置信区间、相对便宜基线的净改进。相关性没有实际任务增益，不能自动成为优化器贡献。
- 若比较不同深度，联合模型要明确哪些变量按 P、L、‖G‖、rank(J) 做无量纲归一化。

## 7. 投入门槛：建议的预注册项目管理阈值（不是自然定律）

这些数字是**建议的内部门槛**，需要在 Panel B 正式开始之前由研究组签署和冻结；并非当前经验结果，也不等价于统计显著性。研究者不得根据已看过的数据反向改变阈值。

| Gate | 建议 pass 规则 | fail 动作 |
|---|---|---|
| **G0：正确性** | 导数交叉验证通过；GGN SPD；同一矩阵每个 inverse residual 及 block-energy identity 与 FP64 容差相符；标注极点距离 | 暂停论文实验，先修数值实现 |
| **G1：任务信号** | 在至少两个预指定非平凡 setting 上，校正单标量后的 E_task 中位数≥0.10，cluster-bootstrap 下限>0.05；并提供实际 line-search/训练趋势、强 null 对照 | 暂停 SMPP；把矩阵现象归入基准 |
| **G2：可预测性** | 留出预测 R²>0 且优于最强廉价基线，或形成具有新前提/结论的严格理论界；不应仅仅对已有谱恒等式改写符号 | 不再以主会机制发现为目标 |
| **G3：算法** | 在至少两个真正独立任务族中，同等最终质量下 compute-adjusted time 中位数有实质改善，例如预注册 >20%，且稳定性、峰值内存与调参预算公开 | 不继续扩大 CUDA 工程；必要时转为理论成果 |

**对 G1 的提醒**：上述 0.10/0.05 是研究资源止损线，并不表示 0.09 没有科学意义；对于严格理论的构造性结果，不应套用经验效应大小门槛。统计 bootstrap 需保留真正独立簇数；12 个 holdout seed 的区间仍可能很宽。G2 的 R²>0 本身也不表示可投稿，须结合新颖性、基线与问题重要性。

**不允许的结论**：通过 G1 就叫“证明优化器加速”；通过 G2 就叫“主会稳录”；通过 G3 就叫“所有深度网络都会有跨层耦合收益”。

## 8. 可复现实验记录 schema（必需字段）

建议每个固定状态生成一个 JSON config 与数值包，并另存所有 checkpoint/谱/分块数据。

~~~yaml
schema: genesis_task_coupling_v1
status: NOT_RUN                # NEVER infer from filename
evidence_class: FRESH_SYNTHETIC
run_id: null
hypothesis_id: H1
repository_commit: null
script_sha256: null
config_sha256: null
environment_lock_sha256: null
checkpoint_sha256: null
dataset_sha256: null
seed_cluster: null
train_seed: null
teacher_seed: null
data_seed: null
split: discovery              # discovery / locked_confirmatory
architecture:
  family: DLN
  depth: null
  layer_shapes: []
  block_order: []
loss:
  reduction: half_mean_squared_error
  M: null
  weight_decay: 0.0
checkpoint:
  step: null
  train_loss: null
  val_loss: null
  gradient_norm: null
curvature:
  matrix_object: GGN         # EXACT_H / GGN
  dtype: float64
  rank_J: null
  smallest_eigenvalue: null
  largest_eigenvalue: null
  damping_lambda: null
  damping_ratio_to_spectrum: null
  condition_number: null
  nearest_pole_distance: null
  shifted_SPD: null
  inverse_residual: null
controls:
  null_family: null
  gauge_transform: null
  scalar_step_optimization_set: train
outputs:
  E_param: null
  E_task: null
  E_val: null
  E_D_scale: null
  one_step_gain_full: null
  one_step_gain_block: null
  wall_clock_seconds: null
  max_peak_memory_bytes: null
eligibility:
  gradient: null
  numerical: null
  solver: null
  scientific: null
artifacts:
  raw_matrix_hash: null
  block_norms_hash: null
  spectrum_hash: null
  metrics_csv_hash: null
~~~

**拒绝**：未说明参数块次序的 12×12 图片、只标“通过”却没有原始校验、不同运行拼出的平台和能量、只提供图不提供数值数组、没有失败资格/负结果的结果汇总。

## 9. 提议的代码组织（分支而非直接污染 main）

~~~text
research/genesis/
    2026-10-26_RESEARCH_VALUE_AND_CONFERENCE_DECISION.md
    2026-10-26_EXPERIMENT_PROTOCOL_AND_GO_NOGO.md
    README.md
scripts/             # only after scientific coding task approved
    task_coupling_metrics.py
    dln_task_coupling_pilot.py
    exact_hessian_ggn_check.py
tests/
    test_task_coupling_metrics.py
results/             # ignored / artifact storage, NOT automatically public
    discovery/
    confirmatory/    # no unapproved access or execution
~~~

可复用 PR #6 现有计算正确性基础，但它**尚未合并 main**。若需要直接复用相关脚本，应先决定是将 PR #6 作为科学代码依赖合并、还是在新的实验分支上显式合并其确认的 commit；不能在文档中假装脚本已存在于 main。

## 10. 科学设计审计清单（开始投入的先决条件）

- [ ] 冻结具体主/次假设，以及 E_task、E_val、line-search、簇定义和资格失败处理。
- [ ] 冻结 source commit、模型 shape、参数块次序、训练目标/数据生成与权重正则化口径。
- [ ] 完成解析 toy、J/H/GGN 数值一致性、Woodbury 与块范数能量恒等式测试。
- [ ] 确认资源与授权；不自动调用旧封存数据、外部 holdout 或任何私有对象。
- [ ] 阻尼量纲、固定矩阵 λ sweep、谱极点、同一对象求解误差的记录已实现。
- [ ] blockdiag(G)⁻¹ 与 diag(G⁻¹) 的差别在代码和表格上明确。
- [ ] 已建立强负对照，不因不合预期删掉或挑掉失败样本。
- [ ] Pilot 结果分析与 holdout 筛选过程在实验前固定，确认性种子尚未接触。
- [ ] 预注册 G0/G1/G2/G3 的资源止损决策，实际结果分别保留 PASS/FAIL/NOT_RUN。

### 最终指令

**先做数值正确性和 RQ-A 任务相关效应，后做 RQ-B 残差曲率机制；仅当两项出现超过已知理论/强基线的新结论时，才扩大网络并讨论 SMPP。任何一步结果为负，都必须保留原始证据，停止升级而非重写假设。**
