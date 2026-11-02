# 实验脚本运行报告

运行时间：2026-10-26 03:19–03:22 (GMT+8)
环境：Python 3.13.14 + numpy 2.5.4 + scipy 1.18.1

## 运行结论

| 脚本 | 退出码 | 耗时 | stderr | 状态 |
|---|---|---|---|---|
| dln.py | 0 | <1s | 空 | OK（库文件，无输出） |
| expA.py | 0 | 28–29s | 空 | OK |
| expB.py | 0 | 26s | 空 | OK |
| expC.py | 0 | 39s | 空 | OK |

四个文件全部成功执行，无异常、无警告。日志见同目录 `expA.log.txt` / `expB.log.txt` / `expC.log.txt`。

## 依赖说明

`dln.py` 是共享库（Jacobian / GGN / Hessian / gauge 基的独立实现），被 expA/B/C 以 `from dln import *` 引用，因此三个 exp 脚本**必须在"实验"目录下运行**才能 import 成功。

原环境缺 scipy（expB、expC 依赖 `scipy.optimize`），已装入隔离 venv `C:\Users\lyxxx\.workbuddy\binaries\python\envs\default`。

## 各脚本要点

### expA — 深度线性网络的 GGN 与精确 Hessian 谱

L=12, d=10, N=32，P=1200 参数，3 个 seed。

- **零空间 = gauge 空间精确成立**：`||P_null − P_gauge|| ≈ 7.5e-14`，三个 seed 一致。rank(GGN)=100 = d_out·d_in，gauge 维 1100 = P−100。
- **gauge 投影的块结构符合解析预测**：非对角块范数恒为 0.8333 = d/L，对角块 9.1667 = d(1−1/L)，min=max 说明完全均匀。
- **GGN 伪逆在 gauge 空间内是标量**：λ 很小时 rms ratio 所有 k 恒等于 1/(L−1)=0.0909，offdiag mass → 1/L=0.0833，即纯投影算子行为。
- **精确 Hessian 与 GGN 差很大**：`||H−GGN||/||H|| ≈ 0.78–0.80`，H 有 ~600 个负特征值（min eig ≈ −1.7 至 −2.6）。
- **负曲率集中在 gauge 方向**：负特征向量能量落在 gauge 切空间的比率为 0.959–0.964，而非 gauge 方向的 H 部分接近半正定。这是本组实验最强的结论。

### expB — 收敛点处的谱分析

din=dout=8, h=12, L=8, N=50，P=1056，4 组配置（orth/orth/gauss/orth+weight decay）。

- orth 初始化两组收敛到 loss ~1e-16，`|grad|~1e-8`，rank J_M=64，`||P0−Pg||~1e-13`。
- 收敛点处 H 与 GGN 几乎重合：`||H−GGN||/||H|| ~ 7e-9`（expA 里是 0.78，因为 expA 用的是随机初始化点，不在临界点）。
- **关键分歧**：λ=1e-8 时 GGN 逆仍逼近 P0（误差 2e-8），但**精确 H 逆已明显偏离**。Levenberg–Marquardt 的 `λR ≈ P0` 只在用 GGN 时成立；用精确 Hessian 时，λ=1e-8 给出的近似偏差达 O(0.2–3.7)，完全失效。原因是收敛点处 H 有极小负特征值（~−1e-8），与 λ 同量级，`μ+λ` 抵消导致逆爆炸。
- H_off（块外部分）低秩性很强：rank L−1=7 就能捕获 65–80% 范数，rank 64 达 95–98%。

### expC — 沿训练轨迹扫 loss 水平的负曲率

4 seed × 2 个目标 loss（1e-3, 5.3e-7）。

- 每个 loss 水平下都稳定出现 ~500 个负特征值，且**负特征向量几乎完全落在 gauge 切空间内**（比值 0.999–1.000）——与 expA 的 0.96 同向且更干净。
- loss 越低，`||H−GGN||/||H||` 越小（1e-3 时 1.4e-2 至 2.8e-2，5.3e-7 时 3.2e-4 至 7.6e-4），H→GGN 的收敛随训练推进而加强。
- λ=1e-8 时 rms ratio 在低 loss 下塌到 0.004–0.04，印证 expB 的结论：**精确 H 加微小 λ 不能复现伪逆投影**，因为 `min|μ+λ|` 恰在 1e-8 量级。

## 一致性检查

三个脚本的结论互相印证：

1. gauge 零空间结构在随机点（expA）和收敛点（expB/C）都成立，expA 的 `||P0−Pg||~1e-14` 与 expB 的 `~1e-13` 同量级。
2. 负曲率被限制在 gauge 方向这一结论，在 expA（0.96）与 expC（1.00）一致。
3. H 与 GGN 的差异随距离临界点而增大：收敛点 ~1e-9，中等 loss ~1e-2，随机点 ~0.8。三者构成单调序列，无矛盾。

## 复现方式

```bash
cd "C:\Users\lyxxx\Downloads\实验"
"C:\Users\lyxxx\.workbuddy\binaries\python\envs\default\Scripts\python.exe" -u expA.py
"C:\Users\lyxxx\.workbuddy\binaries\python\envs\default\Scripts\python.exe" -u expB.py
"C:\Users\lyxxx\.workbuddy\binaries\python\envs\default\Scripts\python.exe" -u expC.py
```

注意：Windows 下直接用 `>` 重定向会把 UTF-8 输出按 GBK 解码，λ/μ 等符号变乱码。需先设 `$env:PYTHONIOENCODING='utf-8'` 与 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`。