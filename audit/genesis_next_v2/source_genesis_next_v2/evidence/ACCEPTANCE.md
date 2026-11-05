# 交付验收记录

状态：**READY_FOR_LOCAL_PREFLIGHT**。不是 GPU 科学验收通过，也不是 GENESIS 假设成立。

## 已在本次会话实际执行

- 31 项自动测试通过，使用 `python -m unittest discover -s tests -v`。
- 数值测试：best-ray Block utility、零梯度、错误参考、near-null 能量平方、带尺度的负谱判定、协变坐标对照、CG 残差及预算。
- 输入/隔离测试：路径越界/输入输出重叠拒绝、JSON 非有限数拒绝、seed 字符串精度保留、完整 checkpoint 聚合、重复行拒绝、S2 拒绝、hash 异常阻断。
- 工作流测试：按真实导出 schema 构造的合成审计包，Inspect→Plan→Freeze→Reproduce→幂等 Freeze；80 状态计划及所有保护输入前后哈希不变。
- 小型 Torch 端到端适配器测试：使用合成网络和模拟的 upstream 模块接口，跑完三 γ、稠密参考、CG/Block 比较、gauge 与精度对照；不是用户真实 checkpoint。
- 回归测试：CPU 收据不能给 CUDA 放行；CUDA 资格必须有显存实测；内部子进程不能绕过受控 parent 直接启动。
- 独立合成数学演示：`examples/SYNTHETIC_DEMO.json`，明确非科研数据。

测试日志包含先失败后实现/修复的记录，最终结果见 `FINAL_TESTS.log`。早期 RED 日志中的失败是开发回归证据，不是最新测试状态。

## 尚未执行，必须本机完成

- Windows PowerShell 5.1/Windows 原生启动器的实际运行。
- 用户 E: 盘 398 文件审计快照的整包实际读取（当前容器无该本地目录）。
- 用户真实训练 checkpoint 与 prepared dataset 的完整重算。
- RTX 4070 Ti 的 CUDA FP64 时间、显存、算子兼容性及单步 loss 实验。
- 原 v2 worker 的实时身份、当前 stage、S2 是否已开始。旧聊天或快照不能代替此检查。

当前环境：Linux、Python 3.13.5、PyTorch 2.10.0+cpu、NumPy 2.3.5；本包代码目标 Python 3.11+，未使用 3.13-only 语法。用户环境的依赖不会被自动升级。

## 源码核查边界

通过 GitHub 连接器读取了固定提交中的 measurement/operator/independent_reference/dataset/scheduler/design 接口，并据此实现适配器。未把远端读取伪装成本机科学重算。

输出包附完整 SHA-256 manifest，解压后可用 verify-package 自检。没有模型权重、原始语料、凭证、安装器或持久化任务。
