# GENESIS 科学价值、非平凡性与主会论文路线：研究投资决策报告

> **版本：v1.0 / 2026-10-26（Asia/Singapore）**  
> **性质：独立科学评估 + 有条件的研究规划；不是既有论文、不是主会录用承诺。**  
> **对象：Project GENESIS 的 Hessian / GGN / damped-inverse curvature 主线。不将 NAO 的同名 Genesis 迁移项目混为一谈。**  
> **证据边界：2025 年历史 Phase IV/V 的原始矩阵和 checkpoint 尚未恢复；2026-10-26 P0 是独立合成重实现；引用的公开论文以本文末尾的一手来源为准。**

## 0. 执行结论：明确 Go / No-Go

**GO（有条件，限期）：**投入 **6–8 周**，验证一个收窄后的科学问题——**跨层曲率的矩阵非局部性，究竟在什么条件下转化为不可被逐层近似与标量步长吸收的优化价值？能否廉价预测这种价值并据此分配曲率计算？**

**NO-GO（立即停止作为论文中心）：**
1. 将“12 层 DLN 的逆 Hessian 存在 ~0.09 的长程平台”称为普遍新定律；
2. 将旧报告中的“0.09–0.12 平台 + 39% 非对角能量”作为一个已复现实验；
3. 未建立全局曲率边际价值之前开发 SMPP tri/penta CUDA 内核；
4. 用多个派生指标/图形代替独立验证，或用报告数量替代有效样本量；
5. 在未取得真实训练收益前，把“能近似 Full GN”当成优化器贡献。

**主会定位：**ICML、NeurIPS、ICLR 是 **conditional stretch target（达到科学门槛后争取）**，不是现有成果的合理基线预期。当前没有达到主会审稿所需的独立贡献与真实训练证据。不能给出有校准意义的录用概率。

**投资边界：**先投入小规模 CPU / 单卡探索与一个研究者的有限时间；通过四项科学门禁后才释放真实网络训练资源。若第 3–4 周没有强于简单对照的留出预测信号，应停止当前主线，不以“还需更多算力”延长项目。

## 1. 核心科研对象：必须先定义再叙事

对于均方损失 \(\mathcal L(\theta)=\frac1{2M}\|r(\theta)\|_2^2\)，设 \(J=\partial r/\partial\theta\)，则：

\[
H=\nabla_\theta^2\mathcal L
=\underbrace{\frac1M J^\top J}_{G\ (\mathrm{GGN})}
+\underbrace{\frac1M\sum_a r_a\nabla_\theta^2r_a}_{S\ (\mathrm{residual\ curvature})}.
\]

注意：对一般输出损失，GGN 是 \(J^\top H_{\mathrm{loss,out}}J\)，**不**简单等同 \(J^\top J/M\)；经验 Fisher、期望 Fisher 和 GGN 不能无条件混用 [R10]。

定义 \(Q_G=G+\lambda I\succ0\)（\(\lambda>0\)）与 \(Q_H=H+\lambda I\)。后者可能不定，即使可逆也不能用于所有依赖正定性的优化保证。本文关于“最优二次模型下降率”的主定理、效用函数及预测评价 **仅用于 SPD 的 \(Q\)**；不定 \(Q_H\) 是独立的机制支线，必须用合理的 trust-region / 正定化后再谈优化。

给定按层分块的 \(Q\)，定义 \(D=\operatorname{blockdiag}(Q)\succ0\)、\(E=Q-D\)，以及：
- **几何非局部性**：\(M_{\rm off}(Q)=\|E\|_F^2/\|Q\|_F^2\)；若统计对象是 \(Q^{-1}\)，必须另写 \(M_{\rm off}(Q^{-1})\)，二者不可交换；
- **层距离谱**：\(S(k)^2=\sum_{|i-j|=k}\|[Q^{-1}]_{ij}\|_F^2/n_k\)，\(C(k)=S(k)/S(0)\)；
- **梯度条件化效用**：见第 4 节的 \(\eta\) 和 \(\Delta\)。这才直接度量在指定二次模型下“逐层近似损失了多少完整解的价值”。

## 2. 证据账本：哪些是事实、哪些只是历史报告

### 2.1 可靠性分级

- **THEOREM / ALGEBRA**：在列明假设下可直接推导的恒等式/不等式。数学正确不代表首次发现。
- **FRESH_SYNTHETIC**：可从新代码、种子、配置和输出复算的 P0 合成观测；不能升级历史实验。
- **DOCUMENTARY_ONLY**：从 2025 年阶段报告摘录但缺少原始数组/checkpoint/run_id 的数值。
- **PILOT_QUALIFICATION_FAILED**：2026 年残差学生模型深层端点不满足所需的驻点或局部极小值资格。
- **HYPOTHESIS_NOT_TESTED**：机制解释、跨架构通用性、SMPP 收敛加速和参数规范不变性。

### 2.2 具体已知事实

| ID | 观察或陈述 | 当前级别 | 对科研决策的意义 |
| --- | --- | --- | --- |
| E01 | 历史 L12 报告 \(C(k)\approx0.09\text{–}0.12\) 且非对角能量约 39% | DOCUMENTARY / 相同指标下冲突 | 不得作为证明平台的一个一致观测 |
| E02 | 若 L12 所有非对角距离组 \(C(k)\le0.12\)，能量必须 \(\le13.674\%\) | ALGEBRA | 指标或 run_id 修复是历史重建门槛 |
| E03 | P0 新建 L12×d10、N32、λ=1e−3、三个种子零残差实验：\(C(k\ge1)\approx0.09050\text{–}0.09057\) 且平台平坦 | FRESH_SYNTHETIC | 存在不用特殊相变即可出现的全距平台 |
| E04 | 上述零残差逆 H 非对角质量约 8.265%–8.277%，而非 39% | FRESH_SYNTHETIC | 与分块能量恒等式一致 |
| E05 | P0 同权重但**不同目标函数**的初始非零残差精确 H：597–606 个负特征值，阻尼逆 H 非对角质量约 85.4%–89.6% | FRESH_SYNTHETIC | 非局部响应强烈依赖残差谱与条件数；不能称训练相变 |
| E06 | 固定 H 的阻尼扫描显示逆 H 非对角能量会随 λ 及谱极点邻近度大幅变化 | FRESH_SYNTHETIC | 不控制 resolvent 极点就不能解释结构 |
| E07 | 2026 WorkBuddy GENESIS v4 深度 8 的历史有效极小值：0/6 | DOCUMENTARY / 资格失败 | 不能用于确认性跨深度“极小值平台”结论 |
| E08 | 新 P0 同种子正交 DLN 的 GGN 块间能量高，但 Full/Layerwise GN 的**事后最优缩放局部模型下降率**接近 | FRESH_SYNTHETIC / 探索 | 指向需要研究“效用”而非只看矩阵范数 |
| E09 | 2025 Phase IV/V 原始矩阵、checkpoint、完整日志不在已检索的归档范围 | RECOVERY_BLOCKED | 不能认证旧平台真实高度 |
| E10 | SMPP tri/penta 及 CUDA 实际性能提升 | NOT IMPLEMENTED / NOT TESTED | 不可作为项目已形成的算法结果 |

第 E08 的进一步独立核算见 [PILOT_DIRECTIONAL_VALUE.csv](PILOT_DIRECTIONAL_VALUE.csv) 及本目录以外的 [scripts/strategy_directional_utility.py](../../../scripts/strategy_directional_utility.py)：L12、宽度 10、N32、同样正交 0.95 初始化、恒等目标、λ=0.001，在 3 个种子上 GGN 的非对角 Frobenius 能量质量均为 91.667%；在同一个阻尼 GGN 二次模型中，Full GN 与 block-diagonal GN 更新方向余弦依次约 0.999780、0.998957、0.999586；**沿 block-diagonal 方向事后优化标量步长后**的效用 \(\eta\) 依次为 **0.999737、0.999503、0.999610**。这里的 D 包含每层 \(G_{ii}+\lambda I\)，并不是 AdamW/ SOAP 更新。

**解释限制：**正交 DLN 的等尺度对称性很强，3 个 seed 不是跨架构泛化，最优标量 \(\alpha^*\) 使用当前真实 \(Q\)，属于 **oracle**；该值不是在线可免费获得的学习率，也不是实际训练收敛曲线。零残差处 \(g\approx0\)，效用指标数学上失去稳定意义，故本次 E08 只使用初始非零残差条件。

### 2.3 原始平台的硬冲突

对于等尺寸的 L 个层块，\(n_0=L,n_k=2(L-k)\)，有

\[
M_{\rm off}(R)=\frac{\sum_{k=1}^{L-1}n_k C(k)^2}{L+\sum_{k=1}^{L-1}n_k C(k)^2}.
\]

如果 L=12 且所有 \(C(k)\in[0.09,0.12]\)，则 \(M_{\rm off}\in[8.18\%,13.674\%]\)。历史 39% 不可能与其在**同一矩阵、同一分块定义、同一 run_id**下同时成立。若 39% 为真，则某距离组 \(C(k)\ge0.2411\)；若除 k=1 外都不超过 0.12，必须 \(C(1)\ge0.5261\)。这是**条件性代数界**，绝不是“测到历史高度 0.241”的新结果。

恢复原始 Phase IV/V checkpoint 仍值得作为档案科学诚信工作，但本项目是否值得做新课题，不需要等待它才能判断。

## 3. 创新性预审：哪些“发现”目前不能卖

### 3.1 低秩与平台都可以来自平凡代数

DLN 的有效端到端矩阵 \(M_\theta=W_L\cdots W_1\in\mathbb R^{d_{\rm out}\times d_{\rm in}}\)，故 \( {\rm rank}(J)\le d_{\rm out}d_{\rm in}\)。P0 的 10×10 宽度对应上界 100，早期 8×8 对应上界 64。对于 \(G=J^\top J/M\)：

\[
(G+\lambda I)^{-1}=\lambda^{-1}I-\lambda^{-1}J^\top (JJ^\top+M\lambda I)^{-1}J.
\]

全球低秩修正是一条 **Woodbury 恒等式**；不能作为原创性。等尺度正交权重下，层 Jacobian 块之间存在正交坐标关联，足以让各距离的 Frobenius 块范数一致。标量 rank-one 基准的归一化平台约 \(1/(L-1)\)，随深度衰减。可见有限 L 的平坦性不等于非零渐近平台，更不等于物理相变。

### 3.2 精确 Hessian 的强远层响应可能是普通的谱极点

令 \(R_H(\lambda)=(H+\lambda I)^{-1}\)，则其特征模态放大 \((\mu_i+\lambda)^{-1}\)。当 \(-\lambda\) 接近负特征值时，任何基于逆矩阵的分块能量都可能骤增。\(H+\lambda I\) 不定并不必然不可逆，但不能被当作 PSD covariance/precision，更不能套用要求 SPD 的相关定理。必须匹配谱间隙 \(\min_i|\mu_i+\lambda|\)、条件数及前后向误差再讨论“新机制”。

### 3.3 参数规范（Gauge）不能当作免检的几何不变量

即使两组分层权重实现相同函数，非正交重参数化下的参数 Hessian 分块 Frobenius 范数与 \(\lambda I\) 阻尼通常不保持不变。若主张“架构固有层距规律”，须展示变换协变/函数空间可比较量或声明参数坐标依赖；不能仅比较未变换的原始矩阵。

### 3.4 层间交互或局部近似的实用价值已有强先行研究

- ICLR 2026 Full GN 研究在最高 150M 参数 Transformer 上展示：精确 layerwise GN（忽略跨层信息）**接近** Full GN 的迭代效果；这已占据“跨层信息可以大幅简化”的经验观察 [R01]。
- ICML 2026 Gradient Smoothing 直接对任意基础优化器的层更新做低成本深度耦合 [R02]。
- ICML 2026 对称性驱动曲率近似，已将权重空间对称性用于可存储、可求逆近似 [R03]。
- ICML 2026 DASH 已在块优化器求逆实现和吞吐上形成强工程基线 [R04]。
- 2026 的 Layerwise LQR 提出了在全球层间最优控制目标下学习结构化逆预条件器 [R05，arXiv 预印本，非已核实主会录用]。
- 2026 的 DAG Hessian 研究已经将层间曲率、GN 项和残差曲率区分并估计 [R06，arXiv 预印本]。
- Hessian 秩（NeurIPS 2021）、DLN 二阶驻点（JMLR 2024）、GN 条件数（NeurIPS 2024）已有直接理论积累 [R07–R09]。

因此：**“有跨层块”“有平台”“低秩近似”“逐层 GN 很强”“跨层平滑能提升优化”“块求解更快”单独都不是足够的新意。** 参照 [PRIOR_ART_AND_NOVELTY.md](PRIOR_ART_AND_NOVELTY.md) 判断实际差异，而不使用“首次”类措辞。

## 4. 首选研究命题 A：优化有效性是一个梯度条件化问题

**科学问题 A：** 对给定 \(Q\succ0,D=\operatorname{blockdiag}(Q)\succ0,g\neq0\)，跨层耦合 \(E=Q-D\) 的 Frobenius 能量、层间距离谱、谱条件数，与“逐层预条件方向需要怎样的跨层修正”究竟是什么关系？能否用 1–数次 \(Qv\) 和廉价 \(D^{-1}v\) 运算，预测完整二阶更新的边际价值？

### 4.1 应采用的正确、可审计目标：ray-oracle relative value

完整模型二次目标 \(\phi(p)=g^\top p+\frac12p^\top Qp\)，Full GN 的最优更新 \(p_*=-Q^{-1}g\)。逐层方向 \(p_D=-D^{-1}g\)。先赋予逐层方法一个**很强的公平对照**：允许在该方向上选择最优标量 \(\alpha_*\)，而不是固定糟糕的学习率。

\[
\alpha_*=-\frac{g^\top p_D}{p_D^\top Qp_D}>0,\qquad
\eta=\frac{\phi(0)-\phi(\alpha_*p_D)}{\phi(0)-\phi(p_*)}\in(0,1].
\]

定义主要效用损失（directional regret）：\(\Delta=1-\eta\)。\(\Delta=0\) 表示：完整二阶更新在**本地正定二次模型**上，相比这条可最优缩放的逐层方向没有进一步收益；并不意味着实际神经网络训练可以免费获得 \(\alpha_*\)。

令 \(u=D^{-1/2}g\)，\(B=D^{-1/2}QD^{-1/2}=I+K\succ0\)，则

\[
\boxed{\eta=\frac{(u^\top u)^2}{(u^\top Bu)(u^\top B^{-1}u)}}.
\]

这一公式属于标准逆 Rayleigh 商/预条件梯度几何，**在本文中仅作为新实证问题的测量定义，而非新定理**。恰有 \(Bu=\mu u\) 时 \(\eta=1\)，跨层矩阵范数可以很大而方向增益完全不变。

### 4.2 一个决定性的 2×2 反例（解析，不是创新声明）

同一 SPD 矩阵、同一对角近似：

\[
Q=\begin{bmatrix}1&\rho\\\rho&1\end{bmatrix},\quad D=I,\quad0<\rho<1.
\]

其跨层 Frobenius 能量质量始终 \(M_{\rm off}(Q)=\rho^2/(1+\rho^2)\)。但：
- 梯度 \(g=(1,1)\) 是特征向量，\(\eta=1\)；
- 梯度 \(g=(1,0)\) 非特征向量，\(\eta=1-\rho^2\)。

例如 \(\rho=0.9\)：**相同 44.751% 跨层能量；效用分别为 100% 与 19%。** 这严格证明“仅靠矩阵跨层能量无法决定当前梯度的逐层更新价值”。数学例子简单、可证，但并不声称别人未曾使用。

### 4.3 可计算指标，而不是重复估计完整逆

定义 \(p_D=-D^{-1}g\)；用一次 \(Qp_D\) 计算 \(\alpha_*\)。令优化后的一阶残差 \(r_D=g+\alpha_*Qp_D\)，构造

\[
\boxed{\rho_D=\sqrt{\frac{r_D^\top D^{-1}r_D}{g^\top D^{-1}g}}}.
\]

实现上不必显式计算 \(D^{-1/2}\)：需要分块解或现有预条件器的逆作用，和一次额外的 \(Qv\)（GGN-vector product；不同基础优化器成本必须实测）。如果 \(B\) 的条件数为 \(\kappa(B)\)，有标准 Rayleigh 商界

\[
\boxed{\kappa(B)^{-1}\rho_D^2\le \Delta\le \kappa(B)\rho_D^2},
\]

可将上界截断至 1。**这是条件性界，不是普遍紧界**：当 \(\kappa(B)\) 很大时可能毫无信息；准确/廉价获得 \(\kappa(B)\) 上界也非免费。

研究价值来自：廉价 \(\rho_D\) 或其更稳健替代，在真实 checkpoint 上能否**优于所有矩阵范数、阻尼、谱条件数、随机探针等基线，预测 \(\Delta\) 与实际更新收益**。如果只能事后借助 Full GN 才能判断，那不是实用方法。

### 4.4 命题的可证伪性

- H-A1：在冻结的 checkpoint 上，梯度条件化指标预测 \(\Delta\) 的留出效果优于 \(M_{\rm off}\)、层距谱、阻尼、梯度范数、条件数及廉价随机诊断；
- H-A2：在相似“几何跨层能量”但梯度方向不同的匹配对照中，\(\Delta\) 的差异显著，且代理指标能够识别；
- H-A3：不依赖 oracle 的真实在线自适应校正，相比最强调参的逐层算法、固定局部耦合及 Gradient Smoothing，带来**同等算力预算下**的净收益；
- H-A4：预测行为不只存在于等尺度正交 DLN，也能迁移至实际训练的 ReLU/ResNet/Transformer。

A1/A2 是科学机制门槛，A3 是算法论文门槛，A4 是主会通用性门槛。任一条件均可能失败，不应以“未达到统计显著性”自动解释为算力不够。

## 5. 第二候选命题 B：残差曲率是否导致超出谱极点的非局部重组

现有合成实验中，固定初始权重但改变训练目标，从 zero residual 的 PSD H=GGN 到 nonzero residual 的不定 H，阻尼逆非对角能量由约 8.3% 到 85–90%。**因为目标函数不同，这不是训练动态，也不是反映真实学习中的相变**。

命题 B 的关键不在于差异有多大，而在于差异中有多少**不是**以下已知因素所解释：残差幅度、\(-\lambda\) 特征值邻近、谱条件数、负特征向量几何、范数归一化、Gauge 以及正定性恢复方式。

必须用**同一个训练目标**沿真实 checkpoint 轨迹观察，分别比较 H、GGN 和 S；固定 \(\min_i|\mu_i+\lambda|\) / 条件数分层，做特征值匹配但特征向量受控的对照。若改用安全的 \(Q_H=H+\lambda I\succ0\)，还应记录为安全阻尼增加带来的尺度变化。

**B 的 No-Go：**一旦按照谱极点间隙、规范变换及随机对照匹配后，剩余跨层响应没有稳健、可预测的量；或结果仅在病态低精度求逆时出现，就停止“新非局部机制”叙事。B 不得直接给 A 的正定优化结论背书。

## 6. 其余方向的明确取舍

| 方向 | 投资决策 | 原因 |
| --- | --- | --- |
| 普通 DLN 层距平台/深度尺度律 | **NO-GO 为主线** | 低秩与正交对称已提供低门槛解释；历史数据冲突 |
| 相似谱模态剪除“解释平台” | **仅保留为严谨消融** | 原历史指标非因果解释，可能受遮罩后交叉项抵消 |
| Chain/Global/Mixed 距离几何拟合 | **暂停独立主线** | 历史链模型甚至弱于置换负对照；先证明任务价值 |
| Gauge 不变的 Hessian 空间 | **理论控制** | 参数坐标是重要问题，但已存在直接相关先行理论 [R03] |
| SMPP tri/penta + fused CUDA | **冻结工程** | 目前无预测性收益证据，且 DASH/LLQR/GS 竞争强 |
| Gradient-conditioned value | **A：主力** | 可定义相同度量的 oracle，方向性反例，能通向算法判断 |
| Exact-H residual geometry | **B：旁路探索** | P0 异常强，但极易由谱极点解释 |
| 恢复历史文件 | **独立完整性任务** | 为旧 claim 提供审计，不自动产生科研新颖性 |

## 7. 优先实验组合：先寻找强反例和失败域，再寻求正面结果

详见同目录 [EXPERIMENT_CONTRACT.md](EXPERIMENT_CONTRACT.md)。关键顺序：

**G0（已有/新补数学控制）**：解析 2×2 相同 Q 不同梯度、标量秩一、等尺度正交 DLN、同谱随机旋转、Gauge 缩放、不定近极点。输出真实/代理 \(\Delta\)、CG 解残差、全部负例。

**G1（值不值得做）**：在小型 DLN、非线性 MLP、小 ResNet 等合格训练轨迹上固定 Q=GGN+λI，按种子/阶段/阻尼保存 \(M_{\rm off}(Q)\)、\(M_{\rm off}(Q^{-1})\)（仅小规模）、\(\rho_D\)、\(\Delta\)、梯度方向和 Full/Layerwise GN 效用。保证输入目标不切换为零残差伪“训练”。若真实梯度下所有 \(\Delta\) 几乎都等于零或代理被简单条件数基线打败，则**不必开发新优化器**。

**G2（预先登记的 out-of-distribution 预测）**：预先冻结指标定义、阈值、模型划分与统计口径；按 **seed cluster / architecture family** 而非 checkpoint 行随机分割。优先检验**同等能量、不同梯度**的近邻匹配对；强制同时报告预测失败的条件。

**G3（轻量算法）**：在 Layerwise GN / SOAP / Muon / AdamW 的公平参考下，对比固定跨层平滑、可学习定向校正与自适应触发。必须对照只调学习率或简单 global scalar 的收益，并把评估代理消耗的 \(Qv\)、CPU/GPU 内存和实际 wall-clock 算入。

**G4（跨架构实际训练）**：至少一个视觉架构与一个 Transformer 设置，使用完整多种子训练轨迹；核心指标是相同资源政策下的 time-to-target accuracy/loss，而不是单步余弦或“比默认 AdamW 少迭代”。

**G5（理论/主会阶段）**：在实验揭示的稳定非平凡区域上提出可检验的非渐近误差或复杂度结论，以及失败边界；至少独立于经典 Kantorovich/Schur/Woodbury 代数恒等式本身。需要在同一理论假设下解释方法优于固定平滑/逐层 oracle 的机制。

## 8. 强对照与统计约束

1. **Baseline ladder**：Full GN（小规模离线 oracle，非公平在线算力基线）；Layerwise GN + exact ray oracle；Layerwise GN +同等级在线调参；AdamW、SOAP、K-FAC/Shampoo、Muon（架构适用时）；Gradient Smoothing；LLQR（取得可复现实现时）。如果竞争方法复现不可用，须公开标注，不得视其劣于新方法。
2. **无共享信息泄漏**：代理选择、超参数和阈值不得在测试种子/测试架构上调优；梯度、曲率由当前训练 batch 计算，验证损失不用于在线选择超参。
3. **独立单位**：不同 checkpoint/阻尼/探针共享训练种子，不增加独立 n。模型家族转移应单独汇报，不能把同种子多个观测当高 n 显著性。
4. **性能**：配对随机种子、相同数据顺序、相同梯度累计/批大小/学习率搜索预算；算法本身的额外计算纳入 wall-clock、显存、吞吐、能耗（有可靠数据时）。
5. **病态数值**：优先 SPD GGN；全部 Full GN oracle 附解残差、Krylov 停止准则及 \(\lambda\)；\(Q_H\) 不定时必须严格另组。
6. **Gauge 与层分块**：比较前明确定义层块/embedding/normalization/bias 的映射和组权重；跨架构归一化既报告块 RMS，又报告元素数校正的能量。
7. **避免 oracle 混淆**：\(\alpha_*\)、Full GN、Full \(Q^{-1}\) 只能作为离线真值与可计算上界，不可把其免费使用记在方法名下。

## 9. 资源和阶段门禁：6–8 周、非无限延长

| 阶段 | 时间上限 | 可交付科学证据 | Go 条件 | No-Go 条件 |
| --- | --- | --- | --- | --- |
| 0. 基准与来源核验 | 第 1 周 | 解析反例、三个合成 seed 复核；GGN 乘积和 oracle 数值精度 | \(\Delta,\rho_D\) 算术和对照闭环 | 值定义、求解残差或数据来源无法一致 |
| 1. 真实梯度效用分布 | 第 2–3 周 | 固定训练目标的多阶段快照及高/低 \(\Delta\) 区域 | 在不刻意选高 \(\Delta\) 的情况下存在有意义的差异 | 各真实阶段效用损失几乎为零且无可用分层结构 |
| 2. 留出预测 | 第 4 周 | 冻结模型/seed 划分下的 AUC、Spearman、误差校准与不确定性 | 代理指标可重复胜过最佳廉价对照；见实验契约 | 优势只出现在训练集、lambda 泄漏或病态数值 |
| 3. 在线方法原型 | 第 5–6 周 | 自适应 vs 固定耦合 vs 仅调学习率，GPU profile | 校正净收益为正，且无需离线 oracle | 额外算力超过收益；标量 LR 完全解释改善 |
| 4. 主会决定 | 第 7–8 周 | 跨任务/架构配对多种子，独立消融 | 明确、可复现、计算预算公平的机制+算法改进 | 单 toy 效果、无泛化、竞争基线不足 |

**建议的预注册研发阈值（人为项目管理阈值，不是顶会录用条件）**：
- 有足够非平凡样本时，以 **\(\Delta>0.05\)** 定义正类，在冻结的留出组别上 **AUC≥0.75**、相对最佳廉价基线 **ΔAUC≥0.10**；必须报告按 seed 聚类的区间，且不能以重采样 checkpoint 伪造独立性。
- 算法阶段以 **≥10% 的配对中位 time-to-target 改善**作为高优先级继续标准，且 95% 聚类区间应支持正向改善；额外优化器计算开销优先控制 **≤10%**。如果无法以可接受资源测到这一差异，不应声称通过。
- 如果正类过少，分类 AUC 不定义；改成报告 \(\Delta\) 分布与构造域转移，**不得填 0 或强行报告显著性**。这时优先考察为何现实梯度天然集中在低 regret 子空间。

**资源建议而非分配声明**：阶段 0–2 以单机 CPU、小规模单卡为主，避免密集完整 Hessian 分解；阶段 3–4 才申请受控 GPU 预算，且每项运行都附 config hash、commit、seed、checkpoint、optimizer setting、耗时与峰值内存。当前没有授权我调度外部服务器，以上是执行契约，不是宣称这些未来实验已运行。

## 10. 候选论文定位与过会门槛

### 10.1 不能作为主会中心贡献的版本
- “Deep linear inverse Hessian has a plateau”：新颖性弱，已知代数对照太强、历史原件缺失；
- “A banded/low-rank optimizer for DLN”：缺少真实规模及强基线，K-FAC/Shampoo/DASH/LLQR/GS 均有相关先行；
- “The Hessian is indefinite while GGN is PSD”：众所周知且不构成新贡献；
- “Gradients often lie near an eigenvector and scaled layerwise matches full GN”：若没有**可低成本预测且可利用的新规律**，只是已知谱几何的特例。

### 10.2 有条件的理论/算法主会版本

**暂拟题目：** *When Does Cross-Layer Curvature Matter? Gradient-Conditioned Utility and Selective Global Preconditioning*。

三条实质性贡献应分别满足：
1. **机制**：新的跨架构经验规律/失败域，解释高矩阵非局部性为何不等于高更新价值，且超越已经发表的 Full GN vs Layerwise GN 观察；
2. **技术**：以廉价在线算子预测并选择性补偿全球曲率价值，提供非空洞的误差/代价保证，不能只重述 Kantorovich inequality；
3. **结果**：与 AdamW / SOAP / Gradient Smoothing / 合适的二阶强基线公平比较，展示 time-to-target 或训练效率的稳定收益与失败条件。

**Venue 选择：**偏严谨理论+机制预测可瞄准 ICML/NeurIPS；若形成扎实神经优化算法及多架构训练证据则 ICLR/ICML/NeurIPS 均可考虑。会议名称本身不是研究质量指标；任何投稿时间应以会议届时官方 CFP 为准，不在本报告中虚构 2027 截稿日。

### 10.3 决策概率与主观评分

这里的分数是研究顾问评分，**不是校准录用概率**：

| 维度 | 当前评分（0–10） | 含义 |
| --- | ---: | --- |
| 核心问题重要性 | 8 | 二阶预条件成本与效用具有明显普适意义 |
| 既有“平台发现”的原创性证据 | 2 | 简单对称/低秩基准可以解释主要外观 |
| 当前作为主会投稿的成熟度 | 1 | 无新的完整算法和强实验 |
| 转向 A 后的可探索潜力 | 7 | 有明确 oracle、低成本代理与强反例，但竞争激烈 |
| 在 6–8 周内形成主会级结果的可保证性 | **没有保证** | 不提供虚构概率 |

## 11. 风险登记与必要的失败报告

- **RISK-1：全是已知恒等式。** 用“新计算方法或新预测规律 + 新任务证据”证明贡献，不堆术语。
- **RISK-2：代理指标与 \(\Delta\) 因共享 \(Qv\) 而构成部分计算循环。** 报告每次 matvec 与 block solve 成本，并和同成本的 CG、谱估计、固定更新比较。
- **RISK-3：P0 正交 DLN 的特殊对称性。** 必须测试非正交、不同层尺度、norm 层、Residual skip、真实 Batch 波动。
- **RISK-4：工作跨方向漂移。** Anti-Slowing/NAO/Regime Mixing 的历史证据不是本 Hessian 假设的独立确认，不纳入本主线有效 n。
- **RISK-5：正类分布不足。** 不能只从工程上制造大 regret 的合成训练场景而宣称实际网络常见；构造反例可证明诊断敏感，但不能替代自然分布。
- **RISK-6：真实 loss 不符合 SPD 二次近似。** 需要正则化步长、backtracking / trust region 与 finite-step 实际损失改善对照。
- **RISK-7：论文先行工作刷新。** 2026 年还有持续发布的预印本；临投稿时需重新检索，不能据这次文献表宣称不存在先行工作。

## 12. 最终执行裁决

1. **继续有限投入：YES。** A 线为唯一主线；B 只保留 ~10–20% 探索资源；历史修复属独立档案任务。
2. **现在启动 SMPP 大规模训练/CUDA：NO。** 等待 A 的预测与真实收益门禁。
3. **保留 ICML / NeurIPS / ICLR 主会作为目标：YES，附严格条件。** 不把当前 0.09 平台写成已完成创新；不对录用概率做无根据估计。
4. **如果 4 周内没有有效预测增益：立即 STOP/PIVOT。** 允许发表严谨否定性技术报告，不以重复试验“追结果”。
5. **如果方法优于最强廉价对照且能提高真实 wall-clock：推进至论文开发。** 开发出的具体定理与算法必须相对 2026 先行文献另行审核新颖性。

**简明结论：GENESIS 值得投入的是“何时跨层曲率真正有用”的可预测科学规律及其计算价值，而不是旧平台图像本身。当前项目只具备高风险探索资格，尚不具备主会成果承诺资格。**

## 13. 参考文献与可追溯证据

- [R01] Abreu, Vyas, Kakade, Morwani. *The Potential of Second-Order Optimization for LLMs: A Study with Full Gauss-Newton*. ICLR 2026 **主会**. https://proceedings.iclr.cc/paper_files/paper/2026/hash/c8e9a2beb84ab1a616edb89581c4b32a-Abstract-Conference.html
- [R02] Meng, Sugolov, Papyan. *Gradient Smoothing: Coupling Layer-wise Updates for Improved Optimization*. ICML 2026 **主会**. https://proceedings.mlr.press/v306/meng26j.html
- [R03] Artemev et al. *Exploiting weight-space symmetries for approximating curvature*. ICML 2026 **主会**. https://proceedings.mlr.press/v306/artemev26a.html
- [R04] Modoranu et al. *DASH: Faster Shampoo via Batched Block Preconditioning and Efficient Inverse-Root Solvers*. ICML 2026 **主会**. https://proceedings.mlr.press/v306/modoranu26a.html
- [R05] Dufort-Labbé et al. *Layerwise LQR for Geometry-Aware Optimization of Deep Networks*. arXiv:2605.04230 **预印本**. https://arxiv.org/abs/2605.04230
- [R06] Bolshim, Kugaevskikh. *Inter-Layer Hessian Analysis of Neural Networks with DAG Architectures*. arXiv:2604.11639 **预印本**. https://arxiv.org/abs/2604.11639
- [R07] Singh, Bachmann, Hofmann. *Analytic Insights into Structure and Rank of Neural Network Hessian Maps*. NeurIPS 2021. https://proceedings.neurips.cc/paper/2021/hash/c900ced7451da79502d29aa37ebb7b60-Abstract.html
- [R08] Achour, Malgouyres, Gerchinovitz. *The Loss Landscape of Deep Linear Neural Networks: a Second-order Analysis*. JMLR 2024. https://jmlr.org/beta/papers/v25/23-0493.html
- [R09] Zhao, Singh, Lucchi. *Theoretical Characterisation of the Gauss Newton Conditioning in Neural Networks*. NeurIPS 2024. https://proceedings.neurips.cc/paper_files/paper/2024/hash/d067d16e3e5fe8fa8a3e62909907659a-Abstract-Conference.html
- [R10] Kunstner, Hennig, Balles. *Limitations of the empirical Fisher approximation for natural gradient descent*. NeurIPS 2019. https://papers.nips.cc/paper_files/paper/2019/hash/46a558d97954d0692411c861cf78ef79-Abstract.html
- [R11] Martens, Grosse. *Optimizing Neural Networks with Kronecker-factored Approximate Curvature*. ICML 2015. https://proceedings.mlr.press/v37/martens15.html
- [R12] Vyas et al. *SOAP: Improving and Stabilizing Shampoo using Adam for Language Modeling*. ICLR 2025. https://proceedings.iclr.cc/paper_files/paper/2025/hash/e988664070e9591f93fdcf605f7dc623-Abstract-Conference.html
- [I01] [主仓库科学现状](../../../docs/SCIENTIFIC_STATE.md)、[指标审计](../../../docs/CLAIMS_AND_AUDIT.md)、[原计划](../../../docs/NEXT_EXPERIMENTS.md)。
- [I02] [P0 独立实验与核验 PR #6](https://github.com/lyxxx708/hessian-landscape/pull/6)、[P0 首次原始恢复状态](https://github.com/lyxxx708/hessian-landscape/blob/experiments/p0-dln-audit-20261026/docs/P0_HISTORICAL_RECOVERY_STATUS_20261026.md)。
- [I03] [2026 WorkBuddy GENESIS 资格失败证据](../../../research/portfolio/SCIENCE_STATUS_20261026.md)。

**审计声明：**本报告新增的“投资建议/项目决策/实验计划”不是科学执行结果；此次新增 pilot 是单独标识的合成诊断。未改写 2025 历史报告、原始实验状态或其他研究线的结论。
