# Cplx2 — scTenifoldKnk 实例计划

> **引擎：** 仅 `scTenifoldKnk`。  
> **方法论：** [`虚拟敲除方法论_VkoMethodology.md`](../../文档_docs/虚拟敲除方法论_VkoMethodology.md)  
> **本计划不包含：** 与 GenKI 或其它算法的对照、共识、组合验证。  
> **约束：** 不中断已启动的 Formal 跑批，除非用户明确要求停止。Formal 运行期间不提高本引擎的 worker 数。GenKI 的 CPU 上限写在 GenKI 实例计划，不从本计划分走正在用的核。

## 问题

在小鼠 TG、GSE197289 **Control** 感觉神经元亚群（cLTMR、NF1、NP、PEP、TRPM8）中，用 scTenifoldKnk 虚拟敲除 **`Cplx2`**，得到各亚群 DR/扰动基因，并做突触囊泡循环、SNARE、递质释放方向的富集，用于功能讨论。结果是计算预测，不是湿实验 KO DEG。

## 数据

- 登录号：GSE197289；路径：桌面 `琪乐无穷/CPLX2虚拟敲除_Cplx2VirtualKO/数据文件`  
- 细胞：`model == Control` 且上述亚群  
- 基因：检出 ≥25 细胞；超过 8000 则按平均表达 soft_cap，**强制保留 Cplx2**（作者 Issue #33：不单用 HVG）

## 引擎与参数

| 项 | 值 | 来源 |
|----|----|------|
| 包 | `scTenifoldKnk` 1.1 / `scTenifoldNet` 1.4 | 本机已装 |
| `qc_minLibSize` | 1000 | CRAN 默认 |
| `nc_nNet` / `nc_nCells` / `td_K` | 10 / min(500, n−1) / 3 | CRAN 默认 |
| 文献 | Osorio et al., *Patterns* 2022, DOI 10.1016/j.patter.2022.100434 | H |

Pilot（nNet=3、nCells=200、基因约 1000）只作试跑，**不能**当作正式结果。

## 阶段

1. **正式跑（进行中）**  
   `代码文件/13_正式参数虚拟敲除_RunFormalDefaults.R`  
   亚群串行；`makeNetworks` 补丁使 10 张网并行（因 Rcpp `pcNet` 忽略 `nCores`）。  
   完成标志：五亚群 `*_Cplx2_formal.rds` + `*_Cplx2Dr_Formal.csv` + `STATUS_Formal.txt`。
2. **出图与富集**  
   Formal 完成后跑 `14_正式后出图分析_PostFormalPipeline.R`（enrichR、GSEA、PDF+STRING 网络等）。  
   入网规则：FDR < 0.05；边用 STRING；见方法登记「画法与筛选」。
3. **本引擎优化（正式结果之后或并行隔离目录）**  
   - P0：固化当前并行启动说明。  
   - P1：加速 `pcNet`（OpenMP 或 leave-one-out 等价），与 `pcNetCoreRcpp` 对齐后再考虑替换。测试条目、通过线和现行范围见 [`../Knk加速_KnkAccel/文档_docs/测试规程_TestProtocol.md`](../Knk加速_KnkAccel/文档_docs/测试规程_TestProtocol.md)。  
   - P2：GPU/CUDA 仅作试验；未对齐不得称为官方 Knk 结果。  
   产物目录与 Formal 分开（如 `Knk加速_KnkAccel/`）。

## 验收

- 五亚群 Formal checkpoint 齐全  
- DR 总表、FDR 表、图与 `STATUS_Formal.txt`  
- 报告声明：computational prediction；参数为包默认而非 pilot

## 声称

使用 **scTenifoldKnk** 的 distance / Z / `p.adj`。禁止把其它算法的排序表标成 Knk DR。

## 本计划不包含

GenKI、CellOracle 或任意跨算法验证。若以后需要，按方法论 §5 **另开**对比任务。
