# GENESIS：先行研究与新颖性红线（2026-10-26）

**原则：**以正式会议/期刊官网与 arXiv 一手记录核对标题和状态；2026 年文献表不是穷尽性的系统综述。**主会**与**arXiv 预印本**严格区分，投稿前需要重新检索。

## 直接竞争工作

| ID | 已核对论文/状态 | 已覆盖的贡献 | GENESIS 不可重复包装 | 尚有可能成立的差异 |
| --- | --- | --- | --- | --- |
| R01 | [The Potential of Second-Order Optimization for LLMs: A Study with Full Gauss-Newton](https://proceedings.iclr.cc/paper_files/paper/2026/hash/c8e9a2beb84ab1a616edb89581c4b32a-Abstract-Conference.html), **ICLR 2026 主会** | full GN 与精确 layerwise GN，150M 规模的 Transformer，后者接近前者 | “忽略跨层的信息仍然很强”不是首次发现 | 预测 **何时必须保留**，在线选择性补偿的收益 |
| R02 | [Gradient Smoothing: Coupling Layer-wise Updates for Improved Optimization](https://proceedings.mlr.press/v306/meng26j.html), **ICML 2026 主会** | 任意基础优化器的层更新低成本耦合，跨多任务评测 | “跨层平滑可以提升优化”不新 | 与固定平滑等成本比较的动态 value-based gate |
| R03 | [Exploiting weight-space symmetries for approximating curvature](https://proceedings.mlr.press/v306/artemev26a.html), **ICML 2026 主会** | 基于权重空间对称构造并反演结构化曲率近似 | 使用 Gauge / symmetry 近似曲率不够新 | 非协变的指标何时失效及跨参数化效用评价 |
| R04 | [DASH: Faster Shampoo via Batched Block Preconditioning and Efficient Inverse-Root Solvers](https://proceedings.mlr.press/v306/modoranu26a.html), **ICML 2026 主会** | GPU 块批处理及高效矩阵逆根实现 | tri/penta GPU 内核本身不够有新意 | 有理论可检验的选择性跨层效用及端到端 wall-clock |
| R05 | [Layerwise LQR for Geometry-Aware Optimization of Deep Networks](https://arxiv.org/abs/2605.04230), **2026 arXiv 预印本** | 全局几何控制目标导出结构化逆预条件，ResNet/Transformer 评测 | 从 global objective 构造 layerwise inverse 已相关 | 在线、低成本预测 value of cross-layer information |
| R06 | [Inter-Layer Hessian Analysis of Neural Networks with DAG Architectures](https://arxiv.org/abs/2604.11639), **2026 arXiv 预印本** | DAG 网络 Hessian 层块、GN 与残差曲率及相关指标 | 直接层间 Hessian 耦合和 GN-Gap 已有先行 | 控制谱极点后的 inverse resolvent 与优化效用关系 |

## 基础理论与优化器

| ID | 一手来源 | 直接制约 |
| --- | --- | --- |
| R07 | [NeurIPS 2021 Hessian Maps](https://proceedings.neurips.cc/paper/2021/hash/c900ced7451da79502d29aa37ebb7b60-Abstract.html) | DLN Hessian 秩/结构冗余已有理论，rank(J) 与 rank(H) 不可混用 |
| R08 | [JMLR 2024 DLN Second-order Analysis](https://jmlr.org/beta/papers/v25/23-0493.html) | 极小值与非严格鞍点已有精细分类 |
| R09 | [NeurIPS 2024 Gauss–Newton Conditioning](https://proceedings.neurips.cc/paper_files/paper/2024/hash/d067d16e3e5fe8fa8a3e62909907659a-Abstract-Conference.html) | 网络深度、宽度、skip 与 GN 条件数的联系已有研究 |
| R10 | [NeurIPS 2019 Empirical Fisher Caveats](https://papers.nips.cc/paper_files/paper/2019/hash/46a558d97954d0692411c861cf78ef79-Abstract.html) | 经验 Fisher 不可无条件替换 GGN |
| R11 | [ICML 2015 K-FAC](https://proceedings.mlr.press/v37/martens15.html) | 已有强的可反演分块近似与自然梯度优化器 |
| R12 | [ICLR 2025 SOAP](https://proceedings.iclr.cc/paper_files/paper/2025/hash/e988664070e9591f93fdcf605f7dc623-Abstract-Conference.html) | 现代预条件强基线，不能只与默认 AdamW 比 |

## 新颖性否定测试（必须逐项回答）

1. 新公式是否只是 Woodbury、Schur complement、Rayleigh quotient 或 Kantorovich/standard residual bounds 的改写？若是，公式仅作测量基线。
2. “跨层信息可能不重要”是否已经由 ICLR 2026 Full GN 观察覆盖？若是，需要给出 **何时重要**的可预测新条件。
3. 是否只是在 Gradient Smoothing 或 LLQR 结构中换一个门控超参？必须证明同成本在线收益和新的可泛化解释。
4. 是否在训练轨迹的真实模型、held-out architecture 上得出结论，而非只在等尺度正交 DLN 上？
5. 是否比较同成本少步 CG 与经过同预算 LR 搜索的逐层 GN？
6. 是否提出并验证失败条件、没有人为制造 pseudo-independent checkpoint 的统计显著性？
7. 机制/方法是否能在不调用 full GN oracle 的生产条件下工作？

**肯定不能据以独立投稿主会的观察：**平台存在、GN 低秩、H 不定、层间矩阵非零、层间平滑可能改善优化、GPU 块求逆提速。**可能的新缺口：**对跨层曲率边际效用的廉价预测 + 新失败定律 + 实际动态校正净收益，但截至本报告仍属探索假说。
