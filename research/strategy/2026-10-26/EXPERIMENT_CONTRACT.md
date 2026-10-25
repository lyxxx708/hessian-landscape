# GENESIS 预研究实验合同：G0–G4 科学门禁

> Protocol v1.0，2026-10-26。**以下为拟定、尚未执行的后续实验**。实验设计与实际结果须分开存档；探索结果不得事后改称预注册确认性检验。

## A. 操作性定义与主指标

### A1. 统一矩阵对象、损失与参数分组

在真实训练轨迹的固定 checkpoint \(\theta_{s,t}\) 上计算 \(g=\nabla_\theta\ell_B\)。曲率和梯度必须来自同一模型、同一损失归一化与同一 batch。禁止将 P0 的零残差目标切换包装成训练前后变化。

平方损失下 \(G=J^\top J/M\)；在交叉熵等其他输出损失下，按正确的 generalized Gauss–Newton 定义 \(G=J_f^\top H_{\ell,\mathrm{out}}J_f\)，同时记录 loss reduction；不要把 empirical Fisher 与 GGN 默认视为同一矩阵。

固定层块划分和权重、bias、norm 参数归属，记录真实每组参数个数。定义 \(Q=G+\lambda I\succ0\)、\(D=\operatorname{blockdiag}(Q)\succ0\)，\(g\ne0\)，以及 \(p_D=-D^{-1}g\)、\(p_*=-Q^{-1}g\)。

**主要目标：**

\[
F_*=\tfrac12 g^\top Q^{-1}g,\quad
F_D=\frac{(g^\top p_D)^2}{2p_D^\top Qp_D},\quad
\eta=F_D/F_*,\quad\Delta=1-\eta.
\]

它度量的是**当前 SPD 二次模型中** Full GN 相比最优缩放逐层 GN 方向的边际收益，不是实际训练的收敛速度。若 \(g\) 近似为零，或解与输入非有限，标记 INVALID，不设为零收益。

### A2. 代理和竞争预测器

\[
\alpha_*=-\frac{g^\top p_D}{p_D^\top Qp_D},\
r_D=g+\alpha_*Qp_D,\
\rho_D=\sqrt{\frac{r_D^\top D^{-1}r_D}{g^\top D^{-1}g}}.
\]

主代理至少需要一次 \(Qp_D\)（即一次 GGN-vector product）与一次额外的分块逆作用。若该成本已接近数步 CG，必须与**相同成本**的 CG 部分求解比较，不能称为免费估计。

对照指标：离线 \(M_{\rm off}(G)\)、小模型的逆曲率分块谱、阻尼 \(\lambda/\|G\|_2\)、梯度范数、block cond、廉价随机谱估计、\(\|K u\|\)、仅调全局学习率、固定梯度平滑。大型模型的 Frobenius 全矩阵 norm 若无法廉价获得，其精确值仅作离线解释基线；在线用同预算采样估计并报告误差。

### A3. 数值有效性检查

- GGN 近似 PSD，λ>0；精度、参数布局、求解器残差及条件估计必须报告。
- Full GN oracle：小模型 dense solve；大模型可采用通过误差验证的矩阵自由 CG。建议小尺度 FP64 目标相对线性残差 \(10^{-8}\) 或更小；达不到则该记录不作精确标签。
- 每一个无效的 checkpoint、负曲率误用、CG 未收敛、原始数值异常必须保留失败状态与诊断。
- exact Hessian 若不定，不得将其放进本 SPD 效用指标；分入支线 B。

## B. G0 — 确定性反例与数值契约

### G0.1 基本 sanity cases

1. \(Q=\begin{bmatrix}1&0.9\\0.9&1\end{bmatrix},D=I\)，\(g=(1,1)\) 与 \(g=(1,0)\)，验证同一非对角能量 0.44751381215，但效用 1.0 vs 0.19；
2. \(\rho_D\) 在 Q 的特征梯度方向应为零（\(10^{-10}\) 数值误差内）；
3. 对小型 DLN 比较 Woodbury 逆作用与 dense Cholesky，以及 GGN/H 的自动微分有限差分；
4. 对梯度等范数旋转、谱保持随机旋转、参数层置换、规范重缩放做受控消融；
5. 记录 exact λ 与矩阵谱尺度，防止 damping 比较被参数化混淆。

**G0 PASS 仅证明代码/对象定义正确，不是新理论。**

### G0.2 当前已执行的一组有限合成诊断

脚本见 [strategy_directional_utility.py](../../../scripts/strategy_directional_utility.py)、数值见 [PILOT_DIRECTIONAL_VALUE.csv](PILOT_DIRECTIONAL_VALUE.csv)。三个种子非零残差正交 DLN 记录的 \(\eta\) 为 0.999737 / 0.999503 / 0.999610；这只是探索线索，不是训练中广泛成立的结论，也未引入实际随机优化。

## C. G1 — 找到自然训练中真实存在的 regret 变化

**首要判定**：不人为制造高 regret 的情况下，实际训练状态是否呈现可建模的 \(\Delta\) 异质性？

| 架构组 | 初期选择 | 必须控制 |
| --- | --- | --- |
| LIN | DLN L=3/6/12、不同宽度；正交与非正交初始化 | 解析 rank、权重尺度、Gauge |
| MLP | 3–6 层 ReLU/LeakyReLU 小模型，受控分类任务 | activation gates、GN loss Hessian |
| RES | 小 ResNet / CIFAR-10 | normalization 状态、skip、层块定义 |
| TRF | Tiny Transformer / 有限语言建模 | attention 组大小、embedding、计算预算 |

探索阶段建议每模型 **至少五个独立训练 seed**，每 seed 冻结初期/中期/后期三个 checkpoint。阻尼取 \(\lambda=\gamma\max(\widehat{\|G\|_2},s_0)\)，\(\gamma\in\{10^{-3},10^{-2},10^{-1}\}\)，数值下界 \(s_0\) 必须预先指定并记录。不同 checkpoint 和 λ 是相关重复测量，不增加独立 seed 数。

每行保存模型版本、完整配置哈希、seed、train checkpoint、梯度、curvature batch、loss、rank / 线性残差、绝对 λ、相对 γ、\(\Delta,\rho_D\)、替代预测器、成本及无效原因。

**早期退出情形：**若在自然训练数据下 \(\Delta\) 几乎恒定低于 0.01，则可能值得研究“逐层 GN 为什么普遍足够”的解释，但**不具备自适应跨层优化器的明显增益空间**。若高 \(\Delta\) 只出现在病态求解、人工损坏或无收敛训练，也不能据此继续工程路线。

## D. G2 — 严格的留出预测与竞争解释排除

### D1. 数据/统计拆分

- 预先记录 train / validation / test 的**种子簇**以及用于 OOD 的模型家族，不按 checkpoint 行拆分。
- 同一 seed 的不同阶段、阻尼及 probes 只能放在同一组；不把高频监控读数当作独立证据。
- 预先冻结阈值和主要评价方向，避免根据结果改变正例定义。
- 如果不同架构独立种子过少，只报告 exploratory within-family，不宣称跨架构泛化。

### D2. 必须实现的对照

1. 固定 Q、相同范数、变换 g 的方向，建立同矩阵高/低 \(\Delta\) 样本；
2. 由同谱不同特征向量的 Q 对照，分离谱值与梯度谱投影；
3. 层块打乱、层序置换、匹配 λ/条件数/规模的负对照；
4. 与 block Frobenius norm、近邻/远邻质量、CG 少步残差、简单 LR 调节的同成本比较；
5. 保留所有失败的种子和预先登记的强 null panel。

### D3. 预测成绩与统计

连续 \(\Delta\) 采用留出 Spearman、MAE、分桶校准、配对排序误差；二分类以 \(\Delta>0.05\) 定义正类，报告 ROC-AUC 和 PR-AUC。正例太少时 ROC-AUC **不定义**，不能用 0 替代或调阈值直到出现正结果。

统计不确定性按 seed cluster 重采样，说明独立 seed 和家族数；多指标和多 λ 的探索性检验明确标注 post-hoc。研发继续阈值建议：正类足够时 AUC≥0.75，且相对**最佳廉价基线** ΔAUC≥0.10，seed-level 区间方向支持改善；或者连续指标具有同等可靠的可解释优势。**阈值是项目管理选择，不是顶会评审标准或已有通过结果。**

**G2 NO-GO：**改善只来自特定同类训练集、λ 泄漏、算法不稳定、重采样相关 checkpoint、或被最佳廉价基线解释；在第 4 周直接停止主力优化器工程。

## E. G3 — 仅通过预测门槛后进行选择性校正

候选方法：默认计算 layerwise preconditioned step；当廉价代理预测 \(\Delta\) 较高时，额外实施少量（r=1/2/4/8）的 Krylov 或低秩定向校正，低值直接保留 base step。不能在线调用 Full GN oracle 或已知 \(\eta\)。

**对比必须包括：**
- 充分调参的原始 base optimizer；
- 相同预算的学习率/weight-decay 搜索和 global scalar 步长对照；
- 固定周期校正、随机触发、基于条件数触发、基于矩阵能量触发；
- ICML 2026 Gradient Smoothing（适用架构）、等额 matvec 的 CG、SOAP、AdamW、其他可复现的结构化方法；
- Full GN oracle 仅用于小模型诊断，绝不当作免费 online baseline。

真实指标为 wall-clock time-to-target loss/accuracy、validation / downstream 性能、吞吐、峰值显存、平均每步额外计算、最差情况损失。**不能将最优 ray-oracle 的局部 99.97% 直接转换成训练提速率。**

建议 G3 继续标准：多 seed 配对中位 time-to-target 至少提升约 10%，区间支持正向，额外优化器开销优先控制约 10% 内；如收益完全可由学习率调整解释，STOP。

## F. G4 — 论文级检验

至少视觉网络 + Transformer 两类，分别多个独立种子（条件许可优先 8–10），同硬件、相同 token/样本预算、相同 warmup、数据顺序、learning-rate 搜索与 optimizer reset 策略。报告 time-to-target 和 target-at-fixed-budget 两类实际结果；公开至少一个失败的架构与原因。若没有足够计算预算或强基线，可投稿目标应相应降低，不能将缺失基线视为方法优胜。

### 竞争基线与再现成本

参考 [PRIOR_ART_AND_NOVELTY.md](PRIOR_ART_AND_NOVELTY.md)：ICLR 2026 Full GN vs layerwise、ICML 2026 Gradient Smoothing、ICML 2026 DASH、2026 Layerwise LQR arXiv、K-FAC、SOAP。若无法复现其中某方法，明确标注 unavailable；不能暗示已比较而未比较。

## G. 并行 B 线：精确 H 残差曲率（最多约 10–20% 探索资源）

在同一个目标函数下观察真实 checkpoint 序列。对于 \(H=G+S\)，匹配或控制 \(\min_i|\mu_i+\lambda|\)、正定门槛、条件数、谱保持 null、参数 Gauge、模型尺度及 solver forward error。仅当去除普通谱极点解释后仍保留稳定的远层结构或优化预测，才考虑建立新机制理论。否则两周后 B 线 STOP。

## H. 输出产物、证据状态、资源节奏

每个运行必须生成：config/environment、源码 commit hash、data/weights/checkpoint hash、run_id、seed group、所有 solver traces、指标及估计开销、failure/invalid 原因、机器可读 CSV/JSON、MANIFEST_SHA256。原始 checkpoint 若包含私有内容不得未经授权推送公开 GitHub；陌生 pickle 不直接反序列化。

推荐状态：DESIGNED → SANITY_PASS → EXPLORATORY_RUN → FROZEN_EVALUATION → INDEPENDENT_REPLICATION → SCIENTIFIC_ACCEPTED / SCIENTIFIC_REJECTED。方案与自动测试成功不等于科学验证成功。

| 时间 | 科学门禁 | 理想交付 |
| --- | --- | --- |
| W1 | G0 | 数学与数值契约、反例、合成 P0 重算 |
| W2–W3 | G1 | 真实训练 \(\Delta\) 分布、困难条件 |
| W4 | G2 | seed/architecture 留出预测、强 null；**强制继续/停止** |
| W5–W6 | G3 | 低成本在线原型、公平 wall-clock |
| W7–W8 | G4 | 跨架构/强基线重复验证、可投稿性判定 |

**此表是实验设计与建议资源节奏，不代表已获得外部服务器资源或启动未来实验。**若第 4 周无强信号，停止。对后续修改需要日期化版本与理由，禁止事后改写失败实验为 PASS。
