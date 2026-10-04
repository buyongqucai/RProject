# 桌面存放（Cplx2 课题金标）

> **本课题桌面树的唯一说明。** 文件夹名遵守 [`样例目录与命名_SampleLayoutNaming.md`](../../../00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例目录与命名_SampleLayoutNaming.md) 的课题交付条：`数据文件/`、`代码文件/`、`结果文件/{数据文件,图片文件,报告文件}`。  
> 钩稽见 [`虚拟敲除方法论_VkoMethodology.md`](../../文档_docs/虚拟敲除方法论_VkoMethodology.md) 与 [`数据集筛选与M4规程_DatasetScreening.md`](../../文档_docs/数据集筛选与M4规程_DatasetScreening.md)。

## 两个夹，不要混

| 夹 | 路径 | 放什么 |
|----|------|--------|
| **现行虚拟敲除** | `C:\Users\10540\Desktop\琪乐无穷\虚拟敲除` | PEP、NF1，六个基因 + 对照；1.4.3 GPU/CPU、GenKI。共用 raw 也在这里 |
| **五亚群留档** | `C:\Users\10540\Desktop\琪乐无穷\五亚群留档` | 旧 Formal：cLTMR / NF1 / NP / PEP / TRPM8，只敲 Cplx2（及对照 Rplp0）、跨亚群图、试跑。**不算现行生物敲除** |

GenKI 合看图在 `_跨亚群/GenKI/图片文件/`：01 原理图按 Yang et al., *NAR* 2023（GenKI/VGAE）自绘，02/03 单细胞与检出图与 Knk 同源（同一份数据）。scTenifoldKnk 合看图里的 06 是 KO 响应对比图（节点=FDR<0.05 响应基因，边=响应关系，不是 STRING PPI）。

`_跨亚群` 还有两处汇合点：`富集汇总_EnrichSummary/`、`课题报告_ProjectReports/报告文件/`（入口 `index_报告入口.html`；论文/方法论均按算法拆开：scTenifoldKnk 与 GenKI；侧栏滚动高亮；论文报告不放入无富集空态图）。每个敲除基因统一三件套：04 散点、04 柱、05 富集图或空态图。Knk 完整版：`Knk加速_KnkAccel/完整版_143GPU_FullVersion/`（只改 DATA_DIR/RESULT_DIR）。GenKI 入口：`genki_formal.py`（VGAE 搜索/拟合有 CUDA 时用 GPU）。

`琪乐无穷` 上的网药压缩包、分子对接、连翘交付不进这两夹。优化记录在仓库 `Knk加速_KnkAccel/文档_docs`。

## 钩稽

一条引擎实例：共享 counts → 切亚群 → 建野生型 → 对该基因虚拟敲除 → **该引擎自己的**响应基因表 → **只用这张表**做 GO/KEGG。

并列的是算法/实现档。响应基因表不是 Seurat/limma 差异分析。富集放在同一亚群 × 同一算法 × 同一基因目录。

## 现行：`虚拟敲除/`

```text
虚拟敲除/
  数据文件/                 # 全课题一份 raw（五亚群留档也读这里，不复制）
  代码文件/
  结果文件/
    PEP|NF1/
      scTenifoldKnk_1.4.3_GPU|CPU|GenKI/
        _野生型/{数据文件,图片文件,报告文件}
        <基因>/{数据文件,图片文件,报告文件}
    _跨亚群/                # 现行引擎合看：1.4.3 HTML、PEP+NF1 延展图（UMAP/小提琴/检出/合看散点/Jaccard）
```

## 留档：`五亚群留档/`

```text
五亚群留档/
  结果文件/
    cLTMR|NF1|NP|PEP|TRPM8/scTenifoldKnk/{Cplx2,Rplp0,_野生型}/…
    _跨亚群/scTenifoldKnk/{数据文件,图片文件,报告文件}
    _试跑/
```

## 路径例子

| 内容 | 路径 |
|------|------|
| GSE 计数 | `虚拟敲除/数据文件/` |
| PEP 1.4.3 GPU 野生型 | `虚拟敲除/结果文件/PEP/scTenifoldKnk_1.4.3_GPU/_野生型/数据文件/` |
| PEP Cplx2 现行 DR/富集 | `虚拟敲除/结果文件/PEP/scTenifoldKnk_1.4.3_GPU/Cplx2/数据文件/` |
| 现行延展图（UMAP 等） | `虚拟敲除/结果文件/_跨亚群/scTenifoldKnk_1.4.3_GPU/图片文件/` |
| 单基因 DR 散点/柱 | `虚拟敲除/结果文件/<亚群>/scTenifoldKnk_1.4.3_GPU/<基因>/图片文件/` |
| 仓内现行 PEP/NF1 图 | `生信分析技能_BioinformaticsSkills/05_系统方法_SystemsMethods/虚拟敲除与扰动_InSilicoKO/02_课题交付_Cplx2Control/结果文件/` 下同一套 `PEP|NF1/_跨亚群/scTenifoldKnk_1.4.3_GPU/` |
| Formal cLTMR Cplx2 RDS | `五亚群留档/结果文件/cLTMR/scTenifoldKnk/Cplx2/数据文件/` |

延展图由 `Knk加速_KnkAccel/代码文件/35_现行延展出图_PlotCurrentExtent.R` 写出到**桌面** `琪乐无穷/虚拟敲除`。富集做 GO BP/CC/MF + KEGG；05 图只画通过条目（BH p&lt;0.05 且 q&lt;0.2），按本体/KEGG 分图，未通过不强行画。探索性 Top50 归档到 `_未采用_探索Top50`。响应基因不是 Seurat DEG。
