# 设计依据与边界

访问/核查日期：2026-11-05。下面是来源；新实验的参数选择和继续/停止规则是本次提出的设计，不是来源已经证明的结论。

## 项目一手材料

固定 commit：`629032110fa51affc7f4e96cdb75f0c40070a9fe`。

- PR #15： https://github.com/lyxxx708/hessian-landscape/pull/15
- 原执行源码 `runtime/measurement.py`： https://github.com/lyxxx708/hessian-landscape/blob/629032110fa51affc7f4e96cdb75f0c40070a9fe/audit/genesis_v2_interim_20261104/07_SOURCE/executed_source/genesis_gpu/runtime/measurement.py
- 原 GGN/梯度算子： https://github.com/lyxxx708/hessian-landscape/blob/629032110fa51affc7f4e96cdb75f0c40070a9fe/audit/genesis_v2_interim_20261104/07_SOURCE/executed_source/genesis_gpu/curvature/operators.py
- 独立参考路径： https://github.com/lyxxx708/hessian-landscape/blob/629032110fa51affc7f4e96cdb75f0c40070a9fe/audit/genesis_v2_interim_20261104/07_SOURCE/executed_source/genesis_gpu/audit/independent_reference.py
- 数据 dtype、thread dependence： https://github.com/lyxxx708/hessian-landscape/blob/629032110fa51affc7f4e96cdb75f0c40070a9fe/audit/genesis_v2_interim_20261104/07_SOURCE/executed_source/genesis_gpu/datasets/registry.py
- 原任务 ID/阶段计划： https://github.com/lyxxx708/hessian-landscape/blob/629032110fa51affc7f4e96cdb75f0c40070a9fe/audit/genesis_v2_interim_20261104/07_SOURCE/executed_source/genesis_gpu/runtime/scheduler.py
- 已有审计结果：同审计目录 `04_NUMERICAL_AUDIT/fp32_vs_fp64/`。这些是旧 agent 的记录，本包 E0 从行级材料重新统计，不把旧文字解释当最终真相。

## 外部一手参考（不是新颖性全面检索）

1. Alberto Bernacchia, Máté Lengyel, Guillaume Hennequin. *Exact natural gradient in deep linear networks and its application to the nonlinear case*. NeurIPS 2018.
   https://proceedings.neurips.cc/paper_files/paper/2018/hash/7f018eb7b301a66658931cb8a93fd6e8-Abstract.html
   用途：防止将 DLN 上复杂曲率与简单更新的联系当成全新概念。这里只核查摘要及论文身份，不声称完成系统性 novelty review。
2. PyTorch official documentation: *Numerical accuracy*.
   https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html
   用途：浮点精度、算子顺序、设备差异和 ill-conditioning 的限制。实现适配用户原 PyTorch 2.10 环境，不按 main 文档自动升级环境。
3. Barrett et al. *Templates for the Solution of Linear Systems*, 2nd edition, Netlib/SIAM.
   https://www.netlib.org/templates/templates.html
   用途：迭代法、真实残差、停止准则。交付 CG 为独立简化实现，经本包测试，不把模板文档当本实验的数值资格证书。

## 不能由这些材料推出

- 没有证明跨所有非线性架构的普适定律。
- 没有证明新方法 wall-clock 加速。
- 没有证明 FP64 在 RTX 4070 Ti 上一定划算。
- 没有证明所有已记录 false-valid 都仅来自 FP32 运算；输入量化和设备效应需拆开。
