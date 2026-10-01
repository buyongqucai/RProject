# Cplx2 — GenKI 实例计划

> **引擎：** 仅 `GenKI`。  
> **方法论：** [`虚拟敲除方法论_VkoMethodology.md`](../../../文档_docs/虚拟敲除方法论_VkoMethodology.md)  
> **本计划不包含：** 与 scTenifoldKnk 的对照、共识或「谁更优」裁定。  
> **约束：** 独立目录与进程；不停止正在进行的 Knk Formal，也不改它的输出路径。  
> **桌面副本：** `C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\GenKI_GenKI\课题计划_GenKI_Cplx2.md` 与本文件同一内容。改规则时先改本文件，再复制到桌面。

## 问题

小鼠 TG、GSE197289 Control、亚群 cLTMR / NF1 / NP / PEP / TRPM8，虚拟敲除 `Cplx2`。GenKI 给出各亚群的响应基因，再做突触囊泡 / SNARE / 递质释放方向的通路分析，用来判断后续研究哪条通路。计算预测，不是湿实验 KO 差异基因。

## 数据

- 与 Knk 共用的 counts 与细胞注释仍在桌面 `琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\数据文件`。本次不复制、不搬家。见同目录 [`数据位置说明_DataPointer.md`](数据位置说明_DataPointer.md)。  
- 基因：各亚群 **top 3000 HVG**（Seurat `vst`，与 NAR 2023 一致）。名单里没有 `Cplx2` 时强制补入，并在 STATUS 里写明。不用 Knk 的 8000 soft_cap，也不把全部基因送进模型。

## 参数变动（只按论文）

出处：Yang et al., *Nucleic Acids Research* 2023，DOI 10.1093/nar/gkad450，「Hyperparameters, metrics and implementation」。一个量变不变，只看它在原文里是搜索项还是固定流程。

计算顺序：top 3000 HVG → PC 回归全连接网 → 边阈值得到布尔图 → 在这张图上做 100 次随机搜索 → 用搜到的参数训练 → 再用固定的排列规则做敲除推断。挑选标准是验证集链接预测的 AUROC 和 AP。边划分：75% 训练、5% 验证、20% 测试。最多 100 轮，验证 AP 见顶回落即停。

搜索项（只通过搜索变，不在搜索之外手调）：

| 项 | 搜索范围 | 原文结果 | 本课题 |
|----|----------|----------|--------|
| `beta` | log10 从 -5 到 -1，再乘 1–9 | 四个数据集都是 `1e-4` | 放进同一轮搜索；验证集选中别的值就用选中值 |
| 学习率 | log10 从 -4 到 -1，再乘 1–9 | 随数据集变（`7e-4` 或 `5e-3`） | 各亚群在自己的图上搜，可以不同于 `7e-4` |
| `weight decay` | log10 从 -7 到 -3，再乘 1–9 | 四个数据集都是 `9e-4` | 与 `beta` 相同 |

边阈值默认是绝对权重最高的 **15%**。原文允许按生物学场景修改。阈值不是搜索的输出。阈值一改，布尔图就变，上面三项必须在新图上按同一范围重搜。首轮不改这个 15%。

不随搜索、也不随阈值改动：

- 细胞顺序打乱 **1000** 次。软件 README 示例里的 100 次不作为标准。  
- 响应基因：KL 进入 **top 5%**，且在超过 **95%** 的重复中出现。  
- Adam、Xavier 初始化、二维二元高斯潜变量、KO 得分用 KL。  
- 种子沿用软件示例 `8096`，写入 STATUS。种子不是搜索项。

每亚群 STATUS 记录：所用阈值，搜到的 `beta`、学习率、`weight decay`，以及验证 AUROC/AP。

输出列名用 GenKI 的 rank / KL，不写成 Knk 的 `distance` / `p.adj`。通路分析只用本引擎的响应基因。

## 资源划分

本机 24 个逻辑核。Formal（scTenifoldKnk）已在跑，约 10 个建网进程，本次不改它的并行度。

- 留给 Windows 日常操作：至少 **4** 个逻辑核。GenKI 不得把线程设满 24。  
- Formal 仍在跑时：**不启动** GenKI 的 PC 回归、Ray Tune 或多进程 DataLoader。VGAE 以后若必须与 Formal 重叠，CPU 线程上限为 **2**（`OMP` / `MKL` / `OpenBLAS` / PyTorch），Ray 同时只跑 **1** 个 trial，训练放在 GPU（RTX 4080 SUPER）。  
- Formal 结束后：GenKI 的 CPU 上限为 **16**（24 减去留给 Windows 的 4，再留 4 给系统与出图）。Ray 同时 trial 不超过 **2**。  
- 执行入口：[`../代码文件/00_资源上限_CpuCap.py`](../代码文件/00_资源上限_CpuCap.py)。训练脚本必须先调用它，再加载 NumPy / PyTorch。

## 目录

- 技能：本文件所在的 `GenKI_GenKI/`（文档与以后的 Python）。  
- 桌面：`琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\GenKI_GenKI\`（文献、课题计划副本、以后的结果）。  
- 不把 Knk 的脚本、结果、`虚拟敲除方法学.pdf` 移进新目录。

## 阶段

1. 目录、开放获取论文、本计划。这一步不跑模型。  
2. 独立环境：`GenKI` + `scanpy` / `anndata`，复用已有 CUDA Torch。Formal 仍在跑时只做安装，不跑建网。  
3. 导出 1 个亚群（先 cLTMR）做烟测。调用 CPU 上限后再建网、搜索、训练。  
4. 对其余亚群重复。每亚群自己的图单独搜索。  
5. 用本引擎响应基因做焦点通路富集。  
6. `STATUS_GenKI.txt`：阈值、搜索结果、验证 AUROC/AP、种子、过滤、亚群、耗时、显存、实际线程数。

## 验收

- 五亚群响应基因表（KL top 5% 且 >95% 的 1000 次打乱）  
- 可复现命令、种子、软件版本、每亚群的搜索结果  
- 图与表在 GenKI 目录，标明 `GenKI`

## 声称

方法写 **GenKI / VGAE 虚拟敲除**（Yang et al. 2023）。禁止写成 scTenifoldKnk，禁止在本计划内宣称「优于 Knk」。

## 本计划不包含

与 Knk 或其它算法的重叠表、通路共识、主辅裁定。需要时按方法论另开对比任务。
