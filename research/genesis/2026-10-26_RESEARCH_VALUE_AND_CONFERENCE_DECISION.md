# Project GENESIS：研究价值、非平凡机制与主会投稿可行性裁决

> **文档性质**：独立研究判断 / 科学问题重构 / Go–No-Go 决策备忘录（非新实验报告、非同行评审结论）  
> **证据截点**：2026-10-26（Asia/Singapore）  
> **基线**：仓库 main commit [41de815](https://github.com/lyxxx708/hessian-landscape/commit/41de8154c0bd8517749f829c1265c565cd7b1a90)；另审阅未合并、draft 的 [PR #6](https://github.com/lyxxx708/hessian-landscape/pull/6)，head [90516c7](https://github.com/lyxxx708/hessian-landscape/commit/90516c7fcfd6001ea08450579c5ed2abec329403)。  
> **范围约束**：只讨论 GENESIS 的深度线性网络（DLN）、精确 Hessian、广义 Gauss–Newton（GGN）、阻尼逆曲率与结构化近似；Anti-Slowing、NAO、signed-Sokal 是独立研究线，不能合并为本项目证据。  
> **审阅原则**：数学恒等式 ≠ 新定理；合成基准 ≠ 历史复现；数值现象 ≠ 机制；矩阵误差 ≠ 实际优化损失；科学潜力 ≠ 主会录用概率。

## 执行摘要：给出明确决定

**决策：CONDITIONAL GO / LIMITED INVESTMENT。保留 GENESIS，但暂停将“长程平台存在”和“局部 + 全局低秩预条件器”当作核心论文贡献；只允许围绕两个可证伪的科学问题开展一轮明确止损的研究。**

1. **现有成绩不够 ICML / NeurIPS / ICLR 主会级别。** 12 层 DLN 在特殊合成设置的约 0.09 平台已经有直接解析说明；GGN 阻尼逆的对角加低秩形式是 Woodbury 恒等式；此前 39% 与平台高度的组合存在共同口径下的严格矛盾。现无新的跨架构、任务相关、具有预测能力的结论。
2. **最值得投入的方向 A（P0）**：证明何时忽略跨层曲率只等价于重设步长，何时产生**无法由任何正标量步长补偿的任务相关更新误差**；寻找可计算的预测量，而非继续堆块范数热图。
3. **第二方向 B（P0/P1）**：定量研究精确 Hessian 的残差二阶项在什么条件下使 GGN 近似失效，并区分谱极点放大、非正定与真实的任务相关方向变化。
4. **方向 C（P2）**：仅在 A/B 得到新且可迁移的现象或边界之后，研究结构感知的低成本校正；**当前不批准优先投入 SMPP CUDA/大规模优化器工程。**
5. **科研投稿定位**：可以把主会作为通过验证关口后的目标，**不能把“当前研究继续扩大样本就自然具备主会竞争力”作为预算理由**。如果关键效应在校准后消失，停止主会导向投入，归档负结果。

**拟定中心问题**：

> 跨层曲率近似造成的误差，什么时候只是可补偿的优化时间尺度改变，什么时候实质改变任务空间中的更新方向与收敛条件？哪些网络、数据与谱条件决定二者的边界？

这个问题有明确反面结论、有已有理论可比较，也允许最终不产生新优化器。

---

## 1. 科学证据分级及不可逾越的来源边界

| 级别 | 可以说什么 | 不可以说什么 |
|---|---|---|
| **A / ANALYTIC** | 在列明假设下推导的精确等式、上界或构造性例子 | 将已知恒等式宣称为首次发现，或推广到未覆盖的网络 |
| **B / FRESH-SYNTHETIC** | 已执行且报告了配置、种子、数值检验的**新实现合成实验** | 称为找回原始 2025 实验；称为训练轨迹证据 |
| **C / DOCUMENTARY** | 旧报告中的数值、阶段结论和待审阅假设 | 冒充现可复现结论，或擅自提升证据等级 |
| **D / HYPOTHESIS** | 拟研究的机制、需要验证的统计量和决策门槛 | 写作中变为已证实的发现、定理和创新 |

**实际来源**：

- main 分支：[科学状态](../../docs/SCIENTIFIC_STATE.md)、[历史断言审计](../../docs/CLAIMS_AND_AUDIT.md)、[DLN 平台](../../docs/LONG_PLATEAU_V_VB.md)、[Phase VI 仲裁](../../docs/MATRIX_DECAY_VI_REV4.md)。
- 独立 P0 **未合并**：[PR #6](https://github.com/lyxxx708/hessian-landscape/pull/6)、[新实现报告](https://github.com/lyxxx708/hessian-landscape/blob/experiments/p0-dln-audit-20261026/docs/P0_REPORT_20261026.md)、[历史恢复判定](https://github.com/lyxxx708/hessian-landscape/blob/experiments/p0-dln-audit-20261026/docs/P0_HISTORICAL_RECOVERY_STATUS_20261026.md)。
- 2026 WorkBuddy 深层端点资格：[科研状态](../portfolio/SCIENCE_STATUS_20261026.md)。不同架构的 2026 checkpoint **不能**作为 2025 L12 DLN 的原始证据。
- 本报告的新数学整理标为 **A**，各项项目性判断标为**分析判断**；**本报告未训练新网络、未重新跑 PR #6 数值、未恢复旧 checkpoint**。

## 2. 对已有结果逐项裁决：什么成立，什么有意思，什么不够新

| 候选发现 / 结果 | 目前真实证据 | 非平凡程度及科研价值 | 裁决 |
|---|---|---|---|
| 12 层 DLN 的归一化非零层距平台约 0.09 | **B**：P0 新合成实验在等比例缩放正交权重、零残差时约 0.090502–0.090571，所有非零 k 几乎严格平坦 | 有效的数值基准；这些条件下可用公共 Jacobian Gram + Woodbury **解析推出严格平坦** | **KEEP AS CONTROL；不能作为主会主贡献** |
| 旧 Phase IV/V 声称平台 0.09–0.12 且非对角能量 39% | **C / CONFLICT**：原始矩阵、checkpoint、run_id 未恢复 | 同一 12 等块矩阵/同一 RMS 指标下不相容；若 c≤0.12，总非对角平方能量≤13.674% | **BLOCKED；不要在论文中并列引用为事实** |
| DLN-GGN 的全局低秩逆响应 | **A**：GGN=JᵀJ/M，阻尼逆 Woodbury；DLN 的函数 Jacobian 秩受输入×输出维度限制 | 理论上清楚、工程上有用，但核心代数已知 | **BASELINE；不能单独作为创新** |
| 非零残差下精确 H 的负曲率和强远层逆响应 | **B**：P0 新合成非零残差条件下 597–606 个负特征值，约 85.43–89.61% 的逆非对角能量 | 确实是值得解释的对照，但 H 在多个阻尼下非 SPD，靠近谱极点可放大响应；不是训练轨迹 | **FOLLOW UP WITH DAMPING / TASK TEST；不能称为相变** |
| 相同非零残差 H 阻尼扫描强烈改变逆非对角占比 | **B**：例如 λ=0.001:86.62%，λ=1.1:18.11%，λ=2:1.80% | 强烈提醒阻尼条件的重要性；但 λ→∞ 时一切有限矩阵的阻尼逆都趋于标量对角 | **真实机制控制，但不是“发现通用非局部性”** |
| 精确 H 与 GGN 很接近但出现负特征值 | **C**：旧 Phase V-B 报告相对 Frobenius 差约 1.53e−4，缺少原件 | 是可形成重要条件数/任务效应研究的问题，旧数字当前未核验 | **候选，不是已证实的主结论** |
| H 的离块部分可用 L−1 模态捕捉 | **C**：原报告 0.665 为 Frobenius **范数**比例，平方能量约 0.442 | 中等压缩性，尚不足支持有效新预条件器 | **不作为创新主张** |
| Phase VI 链式几何模型 | **C**：0.5408 的候选拟合距离比负对照 0.496 更差 | 针对**该模型、该指标**是负结果；不证明所有非局部几何不存在 | **停止使用该拟合结果宣传链式规律** |
| 2026 残差学生深层训练端点资格 | **C**：深度 8 的 6/6 端点存在明显负曲率，0 个历史有效极小值 | 不能以此做“随深度变化的局部极小值”推断 | **深层极小值比较仍然 blocked** |
| 小非对角 Frobenius 质量与大算子误差并存 | **A**：下面给出严格的秩一构造 | **诊断层面的非平凡现象**，但仍是可解析的通用线性代数，不等于优化意义 | **高价值的新研究入口，不是现成论文贡献** |

### 同口径矛盾的不可回避公式

给 L 个等尺寸块、距离 k 的有序对数为 n₀=L、nₖ=2(L−k)，定义

$$
C(k)=\frac{\sqrt{\sum_{|i-j|=k}\|R_{ij}\|_F^2/n_k}}
{\sqrt{\sum_i\|R_{ii}\|_F^2/L}}.
$$

若所有 k≥1 满足 C(k)≤c，则

$$
M_{\mathrm{off}}=
\frac{\sum_{k\ge1}n_k C(k)^2}
{L+\sum_{k\ge1}n_k C(k)^2}
\le\frac{(L-1)c^2}{1+(L-1)c^2}.
$$

L=12、c=0.12 导致上界 13.674%；原始 39% 与该口径**不能同时成立**。这一结论只约束同矩阵、同块划分、同指标，不说明旧数字究竟哪一项错。缺少历史原件时应维持 **UNRESOLVED**。

## 3. 数学基础：为什么“全局耦合”不自动构成新发现

对同一数据和平方损失：

$$
\mathcal L(\theta)=\frac{1}{2M}\|r(\theta)\|^2,\qquad
g=\frac1M J^\top r,
$$

$$
H=G+S,\quad G=\frac1M J^\top J,\quad
S=\frac1M\sum_a r_a\nabla_\theta^2 r_a.
$$

精确 Hessian 可不定；G 半正定；对于 λ>0，A_G=G+λI 总是 SPD；对于 A_H=H+λI 必须**逐次检查**其谱与正定性。A_H 不定时可存在逆，但不能把它直接当作 SPD 预条件器或 Gaussian covariance。

### 3.1 Woodbury 的精确低秩基准

$$
(G+\lambda I)^{-1}
=\lambda^{-1}I-\lambda^{-1}J^\top
(JJ^\top+M\lambda I)^{-1}J.
$$

全局修正秩不超过 rank(J)。对不含非线性、输入输出维度为 d_in、d_out 的 DLN，有 rank(J)≤d_in d_out，不随层数增加；例如 8×8 有 rank≤64。这是**解析基准**，不是新发现。

又因为对同一损失的未正则化梯度 g=Jᵀr/M，有

$$
P_{\ker J}g=0,
$$

所以逆矩阵在零空间方向的巨大范数**不必然参与该损失的梯度更新**。报告高维零空间的“能量占比”不能替代对实际 g 的计算。使用 weight decay、momentum 等时，应分别说明加入了哪些额外向量。

### 3.2 重要解析反例：非对角能量很小，但相对算子误差趋近于 1

设 L≥2，G=11ᵀ、λ>0，并令 R=(G+λI)⁻¹，D_R=diag(R)。Sherman–Morrison 给出

$$
R=\lambda^{-1}I-
\frac{11^\top}{\lambda(\lambda+L)},\qquad
c=\frac{|R_{ij}|}{R_{ii}}=\frac{1}{L-1+\lambda}.
$$

则距离平台严格平坦，但 c~1/L，且

$$
M_{\mathrm{off}}=
\frac{(L-1)c^2}{1+(L-1)c^2}\sim\frac1L.
$$

另一方面，注意 R−D_R=−(11ᵀ−I)/[λ(λ+L)]，因此

$$
\boxed{
\frac{\|R-D_R\|_2}{\|R\|_2}
=\frac{L-1}{L+\lambda}\longrightarrow1.
}
$$

λ=10⁻³ 时，L=12 对应非对角平方能量约 8.332%、相对算子误差约 91.659%；L=100 约为 1.00% 和 99.00%。

**关键限制**：这里删除的是**逆矩阵 R 的非对角项**；实际 block-diagonal 曲率预条件器通常是 (blockdiag(G)+λI)⁻¹，它与 diag(R) 并不相等。另外，秩一模型对任务梯度 g∈span(1) 的更新常只差一个正标量，最优步长可以补偿。因此**大算子误差仍不足以宣称训练恶化**。

> 本构造的科研作用不是单独构成新理论，而是证明“平台低 / offdiag mass 低 → 可放心忽略跨层作用”的研究判断并不成立；随后的关键缺口是**任务相关性**。

## 4. 最优先问题 RQ-A：何时跨层耦合真正影响任务更新？

**投资优先级：最高。主会论文可行性的第一决策关口。**

对同一 checkpoint、同一梯度、同一 GGN、同一 λ：

$$
A=G+\lambda I,\quad
D=\operatorname{blockdiag}(G)+\lambda I,\quad E=A-D.
$$

$$
d_*=-A^{-1}g,\qquad d_0=-D^{-1}g.
$$

在函数空间衡量任务误差，定义

$$
u=J_{\mathrm{train}}d_*,\quad
v=J_{\mathrm{train}}d_0,\quad
\boxed{
E_{\mathrm{task}}=
\min_{\alpha\ge0}
\frac{\|u-\alpha v\|_2}
{\|u\|_2}
}.
$$

分母接近零时指标记为**未定义并标记资格失败**，绝不能设为零。α 为唯一的全局标量步长补偿；若 v≠0，则 α*=max{0,〈u,v〉/‖v‖²}。另外独立评估验证数据 J_val d，但不能用验证集选择 α 后再报告同一验证误差。若更关注长期训练，还必须报告真实目标函数的一步线搜索与完整轨迹；仅靠 Jd 不够。

**必须区分的三种错配**：

1. **矩阵差异**：‖A⁻¹−D⁻¹‖，可能被零空间主导。
2. **方向差异**：‖d_*−αd₀‖，可能包含对当前损失函数无影响的参数方向。
3. **任务差异**：‖J(d_*−αd₀)‖，以及真实损失改进、最优步长、收敛时间，最接近要解释的机器学习效应。

### 4.1 可作为理论起点的严格谱分解

令

$$
K=D^{-1/2}ED^{-1/2},\qquad b=D^{-1/2}g.
$$

则

$$
D^{1/2}(-d_*)=(I+K)^{-1}b,\qquad
D^{1/2}(-d_0)=b.
$$

因为 A、D 均 SPD，I+K SPD。设 K 的本征值 κ_i>−1、本征向量 u_i，b_i=〈u_i,b〉。在 D 白化参数范数下，有精确恒等式：

$$
\boxed{
\varepsilon_D^2=
\frac{\sum_i[\kappa_i/(1+\kappa_i)]^2b_i^2}
{\sum_i[1/(1+\kappa_i)]^2b_i^2}.
}
$$

若 ρ=‖K‖₂<1，粗上界为 ‖(I+K)⁻¹−I‖₂≤ρ/(1−ρ)，预条件谱的条件数满足 κ(I+K)≤(1+ρ)/(1−ρ)。当 ρ≥1 时**不能套用此上界**；但这也不自动表示失败。

**一个更精确的“何时只改步长”诊断**：令 f_i=(1+κ_i)⁻¹、w_i=b_i²/‖b‖²（b≠0，∑w_i=1），则对白化方向做最优非负标量匹配可得

$
\boxed{
\min_{\alpha\ge0}
\frac{\|(I+K)^{-1}b-\alpha b\|_2^2}
{\|(I+K)^{-1}b\|_2^2}
=
\frac{\mathrm{Var}_w(f)}{\mathbb E_w[f^2]}.
}
$

由于 f_i>0，最佳 α 为正；右边恰为 0 当且仅当梯度激活的谱方向具有相同的 κ_i。这揭示了研究焦点应当是**梯度加权的预条件谱离散性**，而不是单独的非对角范数。但白化参数差异仍可能被 J 投影抹去，因此最终必须测 E_task。该式为基本谱分解推论、并非新定理。

**真正值得研究的是**：网络何时使危险 κ_i 方向与实际梯度的 b_i 权重重合，从而在白化参数空间乃至任务空间产生错误；以及该谱/梯度耦合量是否比纯块范数、纯条件数具有更好的跨深度预测能力。

注意：上述谱恒等式是标准矩阵分析推论，不是未来论文可直接声称的新定理。潜在创新必须来自**神经网络的结构性边界、可计算代理指标、泛化性或由此改善的算法**。

### 4.2 RQ-A 的明确假设、反假设和成功条件

- **H-A1（候选）**：在有限宽、非各向同性输入、训练中间阶段或不平衡层参数化时，E_task 在校准最优标量后仍显著非零；并可跨 checkpoint/种子观察。
- **H-A0（强零假设）**：任务相关差异主要可由标量步长和有效阻尼变化解释，或只在近奇异数值区出现。
- **H-A2（更强目标）**：基于白化耦合谱、梯度对齐、层尺度和数据协方差的受限模型，能在**留出种子与结构**上预测 E_task/一步改进，显著优于条件数或 ‖offdiag(G)‖ 单变量基线。

**先证实 E_task，后考虑训练加速。** 如果不能排除 H-A0，不应进入新优化器项目。

## 5. 第二优先问题 RQ-B：什么时候精确 Hessian 与 GGN 的差异在任务层面变得重要？

**投资优先级：高，但技术风险高于 A。**

写 A_G=G+λI，H=G+S，对 λ>0 定义

$$
B=A_G^{-1/2}SA_G^{-1/2},\quad
\delta_\lambda=\|B\|_2.
$$

有精确恒等式

$$
(H+\lambda I)^{-1}
=A_G^{-1/2}(I+B)^{-1}A_G^{-1/2}.
$$

若 δ_λ<1，则 H+λI SPD，且

$$
\|(I+B)^{-1}-I\|_2\le \frac{\delta_\lambda}{1-\delta_\lambda}.
$$

因此 ‖S‖_F/‖H‖_F 很小**不能单独**约束逆误差：S 如落在小 G+λI 曲率方向，白化后可变大。这个相对扰动理论同样是已知解析工具。

**值得追的未知量**：残差曲率与 Jacobian 小奇异方向、层间参数尺度和真实梯度的对齐如何随训练而变化？能否给出“GGN 实际上够用 / 不够用”的网络条件，而不是仅用逆矩阵热图猜测？

实验必须在**固定目标、同一训练轨迹、同一 checkpoint、同一 g** 下比较 H 和 G；使用人工替换 teacher-target 使残差归零的 P0 对照仅用于机制隔离，不是训练中的“零残差→非零残差相变”。对于 H 非正定的 checkpoint，分成明确的两种问题：

- 研究**不定 Hessian 的数学 resolvent**：报告最小极点距离 min_i|μ_i(H)+λ|、谱条件数与求解误差；不声称它是 SPD 预条件器。
- 研究**正定优化方向**：只在 λ>−λ_min(H) 且留有谱安全裕量时比较 SPD 更新；或者明确采用 trust-region / negative-curvature-aware 方法，不与普通 SPD-GGN 混比。

**决定性失败条件**：一旦在固定损失、谱安全阻尼、步长校准、零空间与任务投影后，所有差异都消失，则应判定 RQ-B 对主会导向暂无价值；不能通过减小 λ 靠近极点重新制造一个“机制”。

## 6. 第三方向 RQ-C：参数化与深度尺度律——必要的混杂控制，不宜单独包装论文

DLN 有保持函数不变的变换 W_{i+1}W_i=(W_{i+1}A⁻¹)(AW_i)。其参数 Hessian、分块 Frobenius 范数及固定欧氏阻尼 λI **通常不在任意非正交重参数化下不变**。在非线性坐标变换下，离驻点还有梯度乘坐标映射二阶导数的额外项；不能直接用粗糙的 H→TᵀHT 公式解释所有场景。

需要将三个不同目标分开：

1. **坐标内的结构研究**：说明指标本来依赖参数化，并规范比较。
2. **正确变换下的结构研究**：比较对应度量、阻尼和函数响应，检验可转移陈述。
3. **函数空间的优化研究**：明确比较输出响应及其对 reparameterization 的条件不变性，而不是假设 Jd 指标自动不变。

应检验零残差平衡 DLN 的 c~1/L、非对角质量~1/L 是否只出现在高度对称情形；在不同数据谱、异方差、宽度、缩放、残差与 λ/‖G‖ 配比下给出尺度域。**必须先明确固定哪一种尺度（函数尺度、曲率尺度、阻尼尺度）**，否则“随 L 变化”混合了模型增益与矩阵谱位置。

本方向属于保证主研究可靠性的必要支撑；若没有真正非平凡的、坐标处理完备的极限定理，不建议单独做为主会故事。

## 7. 第四方向 RQ-D：结构化预条件器与 SMPP——只在条件满足后启动

此前“块局部 + 低秩全局修正”已经与 Woodbury、K-FAC、Two-Level K-FAC、M-FAC 等思路直接相邻。只提出这种分解本身，不具有足够原创性。

若 A/B 通过关口，可考虑：

$$
P_{\rm proposed}=D^{-1}+\mathcal U\mathcal C\mathcal U^\top
$$

或以 SPD 的曲率端低秩修正构造 P=(D+UC Uᵀ)⁻¹，并明确 SPD 保证、正则化与计算复杂度。两种形式**不是同一算法**。

潜在原创点只能是**方向如何选择、为什么任务相关、何时无需校正，以及以更低代价取得相同效果**。方向选择必须与前文预测理论挂钩，不能只选大奇异值模态并宣称“捕获信息”。对比至少包括精确阻尼 GGN、小模型全 H，blockdiag-GGN、block-band、低秩/随机粗空间、两层预条件类方法以及合适的 K-FAC/Shampoo/M-FAC 基线；对于 Fisher/GGN 定义不同的方法必须在文中标注对象差异。

**不批准当前优先做的事**：CUDA fused kernel、大模型全 Hessian、没有机制结果的全新优化器品牌。无方向效用证据，就没有投入这些工程成本的科研依据。

## 8. 与强先行工作的原创性边界

| 先行工作 | 已占据的成果空间 | 本项目必须跨过的门槛 |
|---|---|---|
| Singh, Bachmann, Hofmann, NeurIPS 2021, *Analytic Insights into Structure and Rank of Neural Network Hessian Maps* | DLN Hessian rank、架构相关的秩亏损 | 不以“DLN 零空间很多”为主贡献 |
| Zhao, Singh, Lucchi, NeurIPS 2024, *Theoretical Characterisation of the Gauss-Newton Conditioning in Neural Networks* | DLN 任意深宽 GN 条件数理论及残差架构影响 | 新结果需超越普通 GN 条件数 |
| Karakida & Osawa, NeurIPS 2020, *Understanding Approximate Fisher Information for Fast Convergence of Natural Gradient Descent in Wide Neural Networks* | 特定无限宽条件下，层块近似 Fisher 可以保留与精确自然梯度相同的函数空间训练动力学 | 必须给出明确**失效条件**或不同前提，不能声称“忽略跨层必然不行” |
| Martens & Grosse, ICML 2015, *Optimizing Neural Networks with Kronecker-factored Approximate Curvature* | K-FAC 的 Kronecker 结构化曲率优化 | 不能把结构化曲率近似当作全新思路 |
| Tselepidis, Kohler, Orvieto, arXiv 2020, *Two-Level K-FAC Preconditioning for Deep Learning* | 块预条件 + 全局 coarse-space 校正 | 不能把“局部 + 全局”单独声明为新算法 |
| Frantar, Kurtic, Alistarh, NeurIPS 2021, *M-FAC* | 矩阵自由二阶信息与低秩逆向量乘 | 必须证明任务结构选择或成本收益优于通用低秩 IHVP |
| Dinh et al., ICML 2017, *Sharp Minima Can Generalize For Deep Nets* | 参数化对曲率和 sharpness 测量的影响 | Gauge 敏感性是必要对照而非自动的原创贡献 |
| Demko, Moss, Smith, 1984, *Decay rates for inverses of band matrices* | 满足带状性/谱条件时矩阵逆元素的衰减估计 | 不得声称一张 DLN 图像推翻经典逆衰减定理 |
| Bolshim & Kugaevskikh, arXiv 2604.11639 (2026), *Inter-Layer Hessian Analysis of Neural Networks with DAG Architectures* | DAG 层间参数 Hessian 分解、共振/几何耦合指标 | 与之明确区分：本项目重点应是**阻尼逆及任务相关近似误差**，而非重复 H_ij 结构热图 |

**文献结论**：高度相关研究已经覆盖秩、谱、参数化、层间 Hessian 和结构化二阶优化。GENESIS 的真正机会是构建一个**有预测力的“近似何时够好”边界**，而不是“又观察到全局结构”。

## 9. 主会级别的诚实判断与可升级门槛

### 当前裁决

- **当前是否已经有主会级论文主结果？否。**
- **这个科学主题是否在 ICML/NeurIPS/ICLR 主会可能成立？是。** 但尚不等于本项目已经具备录用竞争力。
- **是否应预定 NeurIPS/ICML/ICLR 主会为有把握的产出？否。** 对任何具体录用概率没有数据支持，不应给出似是而非的百分比。
- **是否需要为了主会硬上大模型？否。** 强定理及重要的有限宽失效机制可以在小模型取得竞争力；反之，大量训练曲线也不能替代新发现。

### 主会场景下的贡献类型匹配（并非各会录用概率）

| 目标 | 合理的潜在论文形态 | 目前的短板 |
|---|---|---|
| **ICML 主会** | 明确的优化近似失效/有效理论、与机器学习问题直接相关的定量误差边界，或有成本优势的预条件方法 | 当前只有已知解析基准与待证机制，没有超越先行理论的新命题 |
| **NeurIPS 主会** | 深层曲率的可预测机制、严密反例/定理或跨任务实验证实的计算方法 | 缺少可复现的任务相关主效应、留出验证和强基线对比 |
| **ICLR 主会** | 有深度网络建模意义的结构-训练动力学机制，非线性/残差架构上的清晰因果与充分消融 | 目前重度依赖特殊 DLN 与矩阵统计，尚未建立神经网络行为意义 |

以上是**科研选题匹配度判断**而非投稿政策保证；同一高质量成果也可能适合多个会议。所有会场目前均判定 **NOT READY**，不编造录用概率或确保录用的承诺。

### 两条可进入主会审阅的路线（非录用保证）

**Theory-first**：给出一项非平凡的网络结构定理——例如在明确的宽度/深度/数据谱/残差/阻尼条件下，块近似的函数空间误差或收敛因子的上下界；构造不能用步长缩放消除的反例；解释已有近似理论适用和失效的边界。单纯改写 Woodbury/Neumann 等式不算。

**Mechanism-first / optimization**：在小型 DLN 找到可预测信号；在不同初始化及非线性网络留出设置重现；强基线和同预算调参无法消除；提出从诊断量自然导出的低成本修正，并在**实际时间/内存/计算预算**上获益。

若 A/B 只得到“矩阵外观不同，但更新、收敛与任务响应同等有效”，则应停止主会方法论文预期；可以尝试发表严谨的边界/负结果理论，但也不能提前假定它足够新。

## 10. 研究资源与投资优先级

| 排名 | 科学问题 | 潜在学术价值 | 当前证据强度 | 建议投入 |
|---|---|---|---|---|
| **1** | RQ-A：步长可补偿性 vs 任务相关跨层误差 | 高，连接已有无限宽近似理论的有限宽失效边界 | 理论诊断成立，**实际网络效应尚未确认** | **优先 60%** |
| **2** | RQ-B：残差曲率与 GGN 任务误差 | 中高，可能提供定量近似有效域 | 数值对照已见、机制未隔离 | **优先 30%** |
| **3** | RQ-C：规范/深度/阻尼敏感性与数值基准 | 是有效科研的基础，但单独新颖性一般 | 解析基准较清楚 | **必需支持 10%** |
| **4** | RQ-D：SMPP/新预条件器 | 通过 A/B 后潜力高，当前过早 | 未实现/未 benchmark | **当前 0%，过关后重新拨款** |

百分比是**有限探索阶段的人力/注意力建议**，不是对发表概率的估计，也不是有事实依据的精确收益模型。预算优先投向科学解释，不是 GPU 采购或算法工程。

---

## 11. 三个必须完成的投资关口

### Gate 0 — 科学对象和可执行资格

必须先有同一目标函数、同一模型 checkpoint、同一 g 和同一 λ 下的 H/G、D、更新向量；明确独立样本单位、模型/优化器定义；数值验证和同一 run_id 的对象清单。旧 Phase V 原件找不到时可以**使用全新严格标注的 P0 研究线**，但不可偷换为历史复现。

**NO-GO**：梯度/HVP/求解不一致；把不定 H 当 SPD；归一化不自洽；所有样本均只能靠接近谱极点看到效应。

### Gate 1 — 可补偿性测试（决定是否真正值得继续）

在预先锁定的 DLN 合成任务、正则化尺度、训练轨迹以及留出的深度/数据谱条件下，要求：

1. 全曲率与块近似使用相同实际梯度和可比较的谱安全阻尼。
2. 先给予块近似公平的**最优非负步长/固定调参预算**，再算 E_task、实际一步目标变化和轨迹。
3. 有非玩具结构条件，体现稳定的任务方向差异，且强基线无法解释。
4. 使用独立种子簇/数据实例估计不确定性，而不是把每个 checkpoint 当独立样本。

**若只看到非对角块能量、算子误差或近极点放大，仍应 FAIL。** RQ-A 至少须看到针对梯度的任务误差、并且未被简单校准完全抹去，才值得继续。

### Gate 2 — 预测 / 新知识（决定是否升主会导向）

候选谱对齐统计量必须在留出种子、深度、数据谱上预测 E_task 或实际效果，优于只用 κ(A)、‖G_off‖_F、梯度范数等简单基线；或者形成明确非平凡定理并覆盖现有理论未处理的假设域。

**若只有事后解释而没有可迁移预测或新边界，暂不升级。**

### Gate 3 — 算法/推广（可选）

若已有新机制，测试非线性 MLP/小 ResNet；若提出新预条件器，计算其**额外开销后**的收敛收益。真实训练成本控制无优势则降级为理论分析，不应再投资实现复杂 CUDA。

具体实验表、指标、资格和确认性设计见同目录 [可执行预注册协议](2026-10-26_EXPERIMENT_PROTOCOL_AND_GO_NOGO.md)。

## 12. 明确的风险、反证与作者应如何对待

- **零空间范数谬误**：GGN 的 g∈range(Jᵀ)；不能从 R 大块/大能量直接推到训练会使用该方向。
- **阻尼极点谬误**：不定 H 的逆在谱极点附近显著放大是一般矩阵现象，必须做固定矩阵 λ 扫描和 SPD 安全对照。
- **投影自动不变谬误**：Jd 仍依赖 d 的生成算法及固定欧氏 λ 的参数尺度；函数响应也不能脱离度量变换来声称完全规范不变。
- **比较对象混淆**：diag(R) 不是 (diag(G)+λI)⁻¹；经验 Fisher 不等于真实 Fisher，也不总等于 GGN。
- **拟合好看谬误**：Chain/Global/Mixed 应留出 seed、深度、数据分布，做同复杂度 null；带状结构不从前向层链自动推出。
- **无效统计显著性**：共享 seed 的多 checkpoint 属于簇内相关；测试大量 λ 后挑最大差异属于选择偏差。
- **工程先行谬误**：没有确定重要的方向效应，就没有计算理由为 SMPP 投入大量内核实现。

## 13. 报告与实验可交付物要求

研究实验启动后应形成**同一可信证据链**：明确 hypothesis_id、run_id、seed cluster、model/loss/dataset hash、parameter ordering、checkpoint step、λ 及其归一化、matrix_object、rank(J)、谱与正定资格、数值残差与 forward-error 检查、任务相关指标、null、留出分组、调参预算、成本指标。公布图时由保存的原始数组重算。

**不能将本报告误当作新的科学运行结果。** 本文的数值仅来自现存 PR、历史档案或标明的解析例子。新的原始矩阵、真实训练和证据升级均需要以后实际执行并逐项审计。

## 14. 结论：哪些结果会改变投资决策？

**不会**改变本判断的事情：多画几张相似平台图、在更深的特殊正交 DLN 再发现同样的 c、将 Woodbury 低秩形式重新命名、为没有验证的预条件器加速 CUDA、围绕历史矛盾数值做进一步猜测。

**会**改变判断的事情：发现可信的有限宽/训练中任务空间方向误差，能预先解释何时块近似的调步长技巧失效；得到新且严格的边界或可迁移预测，在 DLN→非线性网络中保持明确适用域；必要时把这一机制变成比强基线更高效的修正方法。

**最终投资决定：有限探索继续；主会预期不予提前认证；用 Gate 1 / Gate 2 的科学结果决定是否升级。**

---

## 参考文献（优先原始页面）

1. Singh, Bachmann & Hofmann (2021). [Analytic Insights into Structure and Rank of Neural Network Hessian Maps, NeurIPS](https://papers.nips.cc/paper/2021/hash/c900ced7451da79502d29aa37ebb7b60-Abstract.html).
2. Zhao, Singh & Lucchi (2024). [Theoretical Characterisation of the Gauss Newton Conditioning in Neural Networks, NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/d067d16e3e5fe8fa8a3e62909907659a-Abstract-Conference.html).
3. Karakida & Osawa (2020). [Understanding Approximate Fisher Information for Fast Convergence of Natural Gradient Descent in Wide Neural Networks, NeurIPS](https://papers.neurips.cc/paper_files/paper/2020/hash/7b41bfa5085806dfa24b8c9de0ce567f-Abstract.html).
4. Martens & Grosse (2015). [Optimizing Neural Networks with Kronecker-factored Approximate Curvature, ICML](https://proceedings.mlr.press/v37/martens15.html).
5. Tselepidis, Kohler & Orvieto (2020). [Two-Level K-FAC Preconditioning for Deep Learning, arXiv:2011.00573](https://arxiv.org/abs/2011.00573).
6. Frantar, Kurtic & Alistarh (2021). [M-FAC: Efficient Matrix-Free Approximations of Second-Order Information, NeurIPS](https://proceedings.neurips.cc/paper/2021/hash/7cfd5df443b4eb0d69886a583b33de4c-Abstract.html).
7. Dinh, Pascanu, Bengio & Bengio (2017). [Sharp Minima Can Generalize For Deep Nets, ICML](https://proceedings.mlr.press/v70/dinh17b.html).
8. Demko, Moss & Smith (1984). [Decay rates for inverses of band matrices, Mathematics of Computation](https://doi.org/10.1090/S0025-5718-1984-0758197-9).
9. Bolshim & Kugaevskikh (2026). [Inter-Layer Hessian Analysis of Neural Networks with DAG Architectures, arXiv:2604.11639](https://arxiv.org/abs/2604.11639). **截至本报告列作 arXiv 预印本，不假定已经主会录用。**

**引用边界**：文献方向用于定义先行工作空间，而非宣称已穷尽所有相关论文；正式投稿前仍需按新近发表工作继续更新完整 Related Work。
