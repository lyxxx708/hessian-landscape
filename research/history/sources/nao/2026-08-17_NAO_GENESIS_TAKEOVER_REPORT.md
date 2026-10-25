# NAO — Genesis Takeover Reconstruction Report

```
PROJECT_ID = NAO
PROJECT_NAME = Nonstationary Autocorrelation in Optimization

PROJECT_STATE = GENESIS_MIGRATION_PENDING
GENESIS_RECONSTRUCTION = COMPLETE
TAKEOVER_COMMIT = NOT YET PERFORMED
STRATEGIC_STATE = NOT YET CREATED
CONTROL_LEDGER = NOT YET CREATED
GPU_EXECUTION = REGISTERED / NOT STARTED
```

本轮只完成了 Genesis reconstruction、authority audit 和拟迁移状态重建；**没有运行任何新科学实验，也没有修改任何 threshold / estimator / grid / seed / Gate**。

## 0. Migration pack 验证结论

Migration pack 可以作为 Genesis takeover 的可靠输入。

- 上传 ZIP SHA256：
  `3ad4aaa9796b376bc9d84b1ecb09cd78ef3573fcd94236e200bcf800733072d3`
  与给定值**完全一致**。
- ZIP：34 个对象 = 4 个目录项 + 30 个文件。
- `AUTHORITY_MANIFEST_SHA256.txt` 对除自身外的 29 个文件逐项校验，**29/29 PASS**。
- canonical execution bundle：
  `111675521acbc0af4f75bc2f4f11fdb7f779ecb4a741b3a8632cc5baffaec719`
  与 migration state / manifest 一致。
- migration pack 的 A42 与 supervisor bundle 内部的 `MASTER_EXECUTION_LOCK.json` **逐字节相同**：
  `c9a088e924ae5db67dcb88090d3baa13c220a9a516af45eb92a52a86f1f6409a`
- A42 锁定的 **22 个科学执行文件全部存在，22/22 SHA256 匹配**。
- 包内不存在 `G1_RETURN_*.zip`。
- supervisor 的真实 `results/` 中没有 ResNet 科学 trajectory 或 G1 scientific decision；只有 deployment preflight 信息。工程 synthetic/test summaries 与 scientific evidence 可明确区分。

因此没有证据支持“ResNet 已经偷偷跑过”或“新家庭结果已被查看”。

---

# 1. Authoritative scientific state

Genesis reconstruction 后，当前科学状态应迁移为：

```
CORE R2/R3 THEORY                    PASS / FROZEN
ACTUAL FIRST-CROSSING LOCALIZATION   PASS
IID GAUSSIAN TRANSFER                PASS
R4 SHORT-MEMORY EXTENSION            PASS WITH SM-BARRIER ONLY
ADAPTIVE FIRST-CROSSING NORMAL FORM  PASS
R5 CAUSAL FALSIFICATION              PASS / LEGACY_SEEN
R6 NATURAL RECONSTRUCTION            PASS / LEGACY_SEEN
R7 INDEPENDENT TASK REPLICATION      PASS / LEGACY_SEEN
MULTI-ESTIMATOR R5 BREADTH           PASS / DEVELOPMENT EVIDENCE

V2.1 FINITE-REPLICATE AUDIT          PASS / FROZEN
AUDIT VALIDITY PROPOSITION           PASS UNDER STATED REPLICATE ASSUMPTIONS
A4 AUXILIARY ESTIMATORS              CORRECTED / FROZEN
A5 RESAMPLING SEMANTICS              CORRECTED / FROZEN

RESNET-18/CIFAR-10 PROTOCOL          FROZEN
RESNET EXECUTION PIPELINE            ENGINEERING PASS
RESNET SCIENTIFIC G1                 NOT RUN

VIT-TINY/CIFAR-100                   FROZEN / UNTOUCHED
DISTILBERT/AG NEWS                   FROZEN / UNTOUCHED

TOP-VENUE EMPIRICAL CLOSURE          OPEN
```

所以用户给出的预期 frozen state 已经从“提示”升级为**经 authority reconstruction 验证后的结论**：

[
\boxed{\text{V2.4.2 EXECUTION READY / WAITING FOR SEALED RESNET G1 DATA}}
]

历史主线也已重建清楚：

[
\text{failed stationary width interpretation}
\rightarrow
\text{nonstationarity salvage}
\rightarrow
\text{signed-Sokal first-crossing theory}
\rightarrow
R5/R6/R7
\rightarrow
\text{proof hardening}
\rightarrow
\text{P8 manuscript candidate}
\rightarrow
\text{narrowness/scale critique}
\rightarrow
\text{V2 normal form + audit + cross-family program}
\rightarrow
\text{V2.4.2 sealed execution frontier}.
]

---

# 2. Authority precedence

Genesis 中应固化以下 precedence，而不是按聊天时间排序：

| 优先级Authority |                                                       |
| ------------ | ----------------------------------------------------- |
| **A0**       | `REGIME_MIXING_V2_STAGE_MIGRATION_MASTER.md`          |
| **A1**       | `NEXT_THREAD_STARTUP_PROMPT.md`                       |
| **A2**       | `AUTHORITY_MANIFEST_SHA256.txt`，负责 integrity，而非独立科学结论 |
| **B0**       | A42 master execution lock + 它实际绑定的科学文件                |
| **B1**       | A40 V2.4 status                                       |
| **B2**       | A1–A5 amendments，即 A30–A35                            |
| **B3**       | A20 V2 top-venue master                               |
| **B4**       | A21–A25 Gate / normal-form / audit-validity authority |
| **C**        | A10–A13 proof-hardening authority                     |
| **D**        | L1/L2/L0 pre-V2 provenance                            |
| **E**        | L10/L11 manuscript provenance only                    |

这里有几条必须进入 Genesis 的明确 supersession：

**A1 finite-replicate correction** supersedes G0 中原始 naive LOO mean-covariance reconstruction。当前 predictor 是 cross-replicate covariance + `n/(n+1)` residual correction。

**A2/A2B** supersedes A20 早期 validation split：R7 已经看过，因此是 `LEGACY_SEEN`；真正 untouched holdouts 是 ViT/CIFAR-100 和 DistilBERT/AG News。

**A3** supersedes较弱的 provenance chain；科学执行现在必须通过 A42 的 cryptographic binding。

**A4** supersedes旧 Geyer/Bartlett implementation。尤其旧的
((\rho\_1+\rho\_2),(\rho\_3+\rho\_4),\ldots)
Geyer pairing 已死亡。

**A5** supersedes G0 中“95% bootstrap CI”的语义。3000 次计算本身没变，但只能叫 **descriptive resampling stability bands**。

因此较早文件中的冲突内容不能因为仍被 A42 打包而重新取得 authority；**amendments 是对 frozen base protocol 的有序 patch stack**。

---

# 3. Surviving claims

Genesis 中可以保留的主要科学 claims 是：

1. **Signed-Sokal adaptive first crossing 的 estimator-specific stochastic criticality。** 一阶接触有随机非退化 (\sqrt T) prefactor；高阶接触可出现
   [
   T^{1/2}\quad\text{vs.}\quad T^{1-1/(2r)}
   ]
   的随机 branch splitting，(r=2) 时为 (T^{1/2}) vs. (T^{3/4})。
2. **临界层为 (T^{-1/2})**，并支持 pointwise branch-probability crossover。实际 random threshold-location law 只有在增加 cross-parameter coupling 后才能声称。
3. **first crossing 已经是真正的 first-hit theorem**，不是只找到一个候选 asymptotic root。
4. Gaussian short-memory extension 存活，但只能在 **signed-Sokal pre-crossing / partial-sum barrier** 下成立。
5. adaptive first-crossing normal form 是 V2 的理论泛化层；signed-Sokal 是主要 concrete instantiation。
6. R5 构成强 causal falsification：优化 trajectory/local dynamics 不变时，仅改变 zero-gradient observable regime geometry，可以使 global memory diagnostic 巨变。
7. R6/R7 支持自然 training trajectory 的 quantitative reconstruction，但属于 **legacy seen evidence**，不能作为 V2 blind validation。
8. R5 multi-estimator replay 支持：
   [
   \boxed{\text{regime-mixing distortion is empirically not Sokal-only}}
   ]
   但 **critical exponents 仍然只能归属于已证明的 signed-Sokal case**。
9. V2.1 audit 可以作为 replicate-aware **reconstruction/falsification procedure**。在 independent/exchangeable replicate assumptions 下，有限 replicate bias 修正有理论支持。

---

# 4. Superseded / dead claims

以下内容应在 Genesis 中明确标为 `SUPERSEDED`、`DEAD` 或 `QUARANTINED`，不能重新浮回论文主张：

- 历史 W224/W256 SUPER V4 的 stationary width / intrinsic anti-slowing 机制解释；
- “generic nonstationarity contaminates ACF”作为项目 novelty；
- deterministic R1
  [
  \bar W\_T\asymp T^{r/(r+1)}
  ]
  被当作 actual random estimator law；
- unrestricted Gaussian short-memory universality；
- 强负 AR(1) 仍遵循同一 mesoscopic law 的旧表述；
- 不加 cross-coordinate coupling 就声称 universal realized random threshold jitter；
- 当前 R2B 推出 proportional/supercritical Gaussian theorem；
- R7 是 V2 untouched confirmatory holdout；
- naive finite-replicate LOO covariance decomposition；
- pre-A4 Geyer IPS/IMS identity；
- pre-A4 Bartlett covariance convention；
- 3000 endpoint resampling ranges 是 nominal 95% CI；
- Geyer / batch means / spectral LRV / PSD 共享 signed-Sokal critical exponents；
- V2 已经完成 CNN / ViT / NLP transfer validation；
- FakeData / synthetic engineering fixtures 是科学 evidence；
- `update_norm` 已经收集或 preregistered 为现有 primary evidence；
- P8 是当前 final top-venue manuscript。

历史 SUPER V4 目前仍是 **motivation/provenance only**，不是 scientific blocker。

---

# 5. Frozen experimental gates

这里需要区分 **ResNet G1 development Gate** 和后面的 **confirmatory family Gate**，二者不是完全一样。

### ResNet G1

Frozen family：

```
ResNet-18 / CIFAR-10
10 conditions × 5 seeds = 50 canonical runs
SGD+momentum + AdamW
4096 logged updates
fixed held-out probe loss
```

一个 condition 只有五个 canonical seeds 全部完成才 analyzable；不允许 replacement seed。Family 必须：

```
analyzable conditions >= 8/10
SGD analyzable       >= 4/5
AdamW analyzable     >= 4/5

run Spearman         >= 0.70
condition Spearman   >= 0.80
median |log2 error|  <= 1 bit
error reduction      >= 50%
local qualification  >= 80%
```

同时 frozen causal replay 必须满足：

- signed-Sokal：至少一个 preregistered intervention regime global change ≥10×，local ≤10% change；
- Geyer / batch means / spectral LRV / low-frequency PSD 中至少另外 **2 个 diagnostic families**：global ≥2×，local ≤10%。

实际 A42-bound analyzer 明确：

```
G1_resnet_pass =
    reconstruction_pass
    AND estimator_breadth_replay_pass
```

**natural-discrepancy ≥20% 不是 ResNet G1 pass 的附加条件。**

### ViT / NLP confirmatory Gate

在上述 reconstruction + breadth requirements 之外，还必须满足：

[
\text{natural discrepancy rate}\ge 20%,
]

其中 retained non-cap runs 同时要求：

[
\texttt{contam\_ratio0}\ge0.25
]

和

[
W\_{\rm obs}/W\_{\rm localonly}\ge2.
]

其他冻结常数包括：

```
signed-Sokal c                  = 5
cap                             = floor(T/2)
local windows                   = 8
local covariance cutoff         = floor(L/8)

contamination threshold         = 0.25
global/local W threshold        = 2.0
local-IAT variation threshold   = 2.5
reconstruction error threshold  = 1 bit

resampling draws                = 3000
resampling RNG seed             = 20260817
```

3000 draws 继续执行，但仅产生 **stability bands**，不能改变 point-estimate PASS/FAIL。

访问顺序也是冻结的：

[
\boxed{
\text{ResNet G1 PASS}
\rightarrow
\text{ViT unlock}
\rightarrow
\text{NLP remains untouched}
}
]

若查看 ViT 后修改 audit/threshold/estimator/success rule，则 ViT 自动降为 development；NLP 成为唯一 remaining untouched holdout。

---

# 6. Current blocker

当前不存在理论、协议或设计 blocker。

唯一 legitimate scientific blocker 是：

[
\boxed{
\text{REAL RESNET-18/CIFAR-10 50-RUN G1 HAS NOT BEEN EXECUTED}
}
]

也就是说，当前 frontier 不是“继续想设计”，而是：

[
\boxed{
\text{A42 lock}
\rightarrow
50\text{ real runs}
\rightarrow
\text{seal}
\rightarrow
\text{one-shot frozen analysis}
\rightarrow
\text{G1 adjudication}.
}
]

GPU requirement 现在只登记为：

```
EXECUTION_REQUIREMENT = REAL CUDA ENVIRONMENT
CANONICAL_OBJECT = execution/V242_SINGLE_GPU_SUPERVISOR_BUNDLE.zip
EXPECTED_RETURN = G1_RETURN_*.zip
GENESIS_EXECUTION_AUTHORIZATION = NOT ISSUED
```

本轮没有启动它。

---

# 7. Proposed Project OS initial state

我建议 Genesis takeover commit 时初始化为下面的逻辑状态，但**现在还没有把它写成最终 Strategic State / Control Ledger**：

```
PROJECT_ID = NAO

SCIENTIFIC_PHASE =
    V2_EMPIRICAL_CLOSURE_PRE_G1

SCIENTIFIC_CORE =
    FROZEN

THEORY_FRONTIER =
    CLOSED_PENDING_EMPIRICAL_EVIDENCE

METHOD_STATE =
    V2.1 + A4
    A5_REPORTING_SEMANTICS_ACTIVE

DEVELOPMENT_FAMILY =
    RESNET18_CIFAR10
    FROZEN / NOT RUN

CONFIRMATORY_FAMILY_1 =
    VIT_TINY_CIFAR100
    FROZEN / UNTOUCHED

CONFIRMATORY_FAMILY_2 =
    DISTILBERT_AGNEWS
    FROZEN / UNTOUCHED

CURRENT_BLOCKER =
    SEALED_REAL_RESNET_G1_DATA_ABSENT

NEXT_SCIENTIFIC_TRANSITION =
    G1_RETURN_VERIFIED_AND_ADJUDICATED

EXPERIMENT_DESIGN_MUTABILITY =
    LOCKED

GPU_EXECUTION =
    REGISTERED_BUT_NOT_STARTED

MANUSCRIPT_STATE =
    PRE_V2_BASELINE_EXISTS
    CURRENT_TOP_VENUE_CLOSURE_OPEN
```

此外，应把两个原始项目风险保留为战略背景，而不是重新打开科学设计：

```
PERCEIVED_NARROWNESS = V2 REMEDIATION PROGRAM ACTIVE
EMPIRICAL_SCALE      = V2 REMEDIATION PROGRAM ACTIVE
```

它们的解决机制已经被冻结为 normal form + audit + CNN/ViT/NLP cross-family program；**不能再用这两个风险作为继续添加 estimator/grid/threshold 的理由。**

---

# 8. 是否具备建立 NAO Drive control plane 的条件

**结论：YES。**

从 Genesis governance 的角度，现在已经具备建立 Drive control plane 的必要条件：

- migration root object 已 cryptographically verified；
- authority hierarchy 已恢复；
- supersession chain 已恢复；
- scientific claims / dead claims 已区分；
- frozen experiment protocol 已确定；
- canonical deployment object 已验证；
- current scientific frontier 唯一；
- 当前不存在未 adjudicate 的新-family scientific data；
- 因而不会在建立 control plane 时发生“到底哪个版本才是 authority”的歧义。

但应保持一个边界：

> **现在具备建立条件，不等于本轮已经完成 Genesis migration。**

在真正创建 NAO Drive control plane、写入 initial Strategic State / Control Ledger 并建立 authority/artifact/data/execution namespaces 之前，项目状态仍应保持：

```
PROJECT_STATE = GENESIS_MIGRATION_PENDING
```

因此本次 takeover 的精确收束状态是：

[
\boxed{
\textbf{GENESIS RECONSTRUCTION PASS}
;|;
\textbf{AUTHORITY CHAIN VERIFIED}
;|;
\textbf{READY FOR DRIVE CONTROL-PLANE ESTABLISHMENT}
;|;
\textbf{NO SCIENTIFIC EXECUTION STARTED}
}
]

下一治理动作可以直接进入 **NAO Drive control-plane establishment / Genesis takeover commit**；不需要再进行一次科学探索或协议设计。