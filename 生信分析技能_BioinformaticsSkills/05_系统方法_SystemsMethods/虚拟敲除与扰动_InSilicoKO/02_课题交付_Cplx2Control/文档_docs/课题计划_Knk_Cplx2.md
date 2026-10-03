# Cplx2 — scTenifoldKnk 实例计划

> **引擎：** 仅 `scTenifoldKnk`。  
> **方法论：** [`虚拟敲除方法论_VkoMethodology.md`](../../文档_docs/虚拟敲除方法论_VkoMethodology.md)  
> **本计划不包含：** 与 GenKI 或其它算法的对照、共识、组合验证。  
> **约束：** 不中断已启动的 Formal 跑批，除非用户明确要求停止。Formal 运行期间不提高本引擎的 worker 数。GenKI 的 CPU 上限写在 GenKI 实例计划，不从本计划分走正在用的核。

## 问题

数据集、亚群和敲除基因只写在 [`数据集筛选与M4规程_DatasetScreening.md`](../../文档_docs/数据集筛选与M4规程_DatasetScreening.md) 的「两台机器共用的选择」。本文件只写 scTenifoldKnk 怎么跑。

下一轮生物敲除：GSE197289 小鼠 Control，只跑 **PEP** 和 **NF1**，六个基因逐个敲（Mitf、Bace2、Cplx2、Ppp1r26、Slc28a3、Sh3d21）。某个基因检出为 0 才跳过。富集在扰动基因出来之后做，不预先指定突触囊泡、SNARE 或递质释放。结果是计算预测。

已经在跑的五亚群 Formal（cLTMR、NF1、NP、PEP、TRPM8，只敲 Cplx2）和 cLTMR 加速对照，不改输出路径，不在本计划里下令停止。那些结果按旧选择留档，不当作现行生物敲除。

## 数据

- 登录号、亚群、敲除基因：见上面的共用选择  
- 路径：桌面 `琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO/数据文件`  
- 细胞：`model == Control`，且只取 PEP、NF1  
- 基因过滤：检出 ≥25 细胞；超过 8000 则按平均表达 soft_cap，**六个靶基因只要有检出就强制保留**（作者 Issue #33：不单用 HVG）  
- 新结果目录：`结果文件/PEP/scTenifoldKnk/<基因>/` 与 `结果文件/NF1/scTenifoldKnk/<基因>/`

## 引擎与参数

| 项 | 值 | 来源 |
|----|----|------|
| 包 | `scTenifoldKnk` 1.1 / `scTenifoldNet` 1.4 | 本机已装 |
| `qc_minLibSize` | 1000 | CRAN 默认 |
| `nc_nNet` / `nc_nCells` / `td_K` | 10 / min(500, n−1) / 3 | CRAN 默认 |
| 文献 | Osorio et al., *Patterns* 2022, DOI 10.1016/j.patter.2022.100434 | H |

Pilot（nNet=3、nCells=200、基因约 1000）只作试跑，**不能**当作正式结果。

## 阶段

1. **旧 Formal（留档，不是现行选择）**  
   `代码文件/13_正式参数虚拟敲除_RunFormalDefaults.R` 里仍是五亚群、只敲 Cplx2。正在跑就让它跑完。不要把它的完成标志当成六个基因已经做完。
2. **现行生物敲除**  
   PEP 与 NF1，六个基因逐个敲，参数仍用上表的包默认。一个亚群一张野生型网，换基因只改 `gKO`。对照基因按共用选择的相关规则重算。  
   完成标志：两个亚群、六个靶基因各自有 DR 表，外加对照基因的 DR 表。
3. **出图与富集**  
   扰动基因出来之后再富集。GO 生物学过程与 KEGG，BH，p = 0.05，q = 0.2。不把突触囊泡或 SNARE 写进筛选条件。STRING 只在检索到真实边时画。
4. **本引擎优化（正式结果之后或并行隔离目录）**  
   - P0：固化当前并行启动说明。  
   - P1：加速 `pcNet`（OpenMP 或 leave-one-out 等价），与 `pcNetCoreRcpp` 对齐后再考虑替换。测试条目、通过线和现行范围见 [`../Knk加速_KnkAccel/文档_docs/测试规程_TestProtocol.md`](../Knk加速_KnkAccel/文档_docs/测试规程_TestProtocol.md)。  
   - P2：GPU/CUDA 仅作试验；未对齐不得称为官方 Knk 结果。  
   产物目录与 Formal 分开（如 `Knk加速_KnkAccel/`）。

## 验收

- 旧五亚群 Formal 若已完成，只作留档  
- 现行跑次：PEP、NF1 × 六个靶基因 + 各 1 个对照基因的 DR 表  
- 报告声明：computational prediction；参数为包默认而非 pilot；数据不是慢性三叉神经痛模型

## 声称

使用 **scTenifoldKnk** 的 distance / Z / `p.adj`。禁止把其它算法的排序表标成 Knk DR。

## 本计划不包含

GenKI、CellOracle 或任意跨算法验证。若以后需要，按方法论 §5 **另开**对比任务。
