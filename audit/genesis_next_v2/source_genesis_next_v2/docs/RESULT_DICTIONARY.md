# 输出字段与阅读方法

## 来源分层

`e0/`：旧快照的再统计，未重做神经网络计算。
`results/`：本轮 S1 checkpoint 重算。`freeze_sha` 不等于旧 `protocol_sha`。
`local_inputs/`：精确参考 batch，保留原 FP32 数学值后升精度；私有工件，不得公开。

## 核心字段

- `delta`：Full 相对于 best-ray Block 的局部二次型收益损失比，不是训练加速率。
- `F_star` / `absolute_block_gain_gap`：绝对局部收益与损失；避免把接近零的分母造成的漂亮比例当重大收益。
- `first_tested_cg_budget_ge99`：固定网格中首次达到 99%参考收益的预算，不是精确最小迭代数。
- `matched_matvec_budget`：本轮 block solve 实际 GGNv + 一次 Qb，不等同于原 v2 的 matched-budget。
- `solve_wall_vs_block`：固定执行顺序下的诊断比值，非随机化 speedup trial。
- `train_gain/validation_gain`：同一固定步长网格；训练集选择，验证集只评价。
- `null_energy_fraction`：数值 near-null 部分的 Frobenius 平方份额；阈值必须随同报告。
- `gradient_null_fraction`：梯度投影份额，和矩阵能量不同。
- `negative_certified_count`：只表示“低于本次选择的数值阈值”，不是区间算术证明；须同时看 `negative_mass_fraction/threshold/ambiguous_count`。
- `gradient_relative_vector_error`：同设备、相同量化输入的 FP32 对 FP64。
- `input_quantization_control`：原生 FP64 输入与量化后输入的数学问题差异，不能混成求解器误差。
- `reference_class`：小模型使用稠密 reverse-autograd；大模型 alternate-operator CG 仍共享模型/损失实现与本包 CG 算法，不能宣称完全独立数学证明。

## 状态

- `QUALIFIED`：仅该条件通过本次程序的参考检查；不是科学成功。
- `EXECUTED`：状态执行结束；需要看 `qualified_condition_n`，不能只看顶层状态。
- `NUMERIC_UNRESOLVED`：没有资格用于主数值结论，不填零。
- `ZERO_GRADIENT_UNASSESSED`：比值测量不适用，不是“没有跨层收益”的证据。
- `TIMEOUT_INCONCLUSIVE`：资源上限截断；不等于算法不可收敛。
- `SOURCE_TRAINING_NOT_READY_NO_REPLACEMENT`：计划保留，未生成数据，不换案例。
- `WAITING_FAMILY_QUALIFICATION`：该族未完成真实设备资格，不调用 CPU 小样本替代。

## 汇总

`seed_summary.csv` 每 setting×gamma 一行；同 seed checkpoint 1/3 先聚合。少于4个合格 seed 时区间为空。不同 setting 不混成一个“全网络总体”的独立样本。S1 事后探索性结果不能通过换文件名变成确认性结果。
