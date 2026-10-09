# 完整版 1.4.3 GPU（scTenifoldKnk 1.4.3 公式，GPU/CPU 自适应）

从原始 counts 到每个敲除基因的扰动表与 GO/KEGG 富集，一条命令跑完。
**换数据集只改 `config_配置.py` 顶部的 `DATA_DIR`（数据集路径）和 `RESULT_DIR`（结果存放路径）。**

```powershell
E:\Python3.13.14\python.exe run_all_一键运行.py
```

## 流程与资源

| 步骤 | 文件 | 做什么 | 资源怎么来 |
|------|------|--------|-----------|
| 0 | `probe_资源探测.py` | 探测 CPU/内存/GPU，测 GPU 并发收益 | 运行时探测，不写死核数/显存 |
| 1 | `step1_export_qc.R` | 亚群导出、scQC、CPM、抽样、检出率、低相关对照 | R 线程数 = 探测值 |
| 2 | `step2_gpu_build.py` | 10 张 1.4.3 网 + 稀疏 CP 张量（rank 3，nDecimal=3） | GPU 并发数 = 实测吞吐探测；无 GPU 自动转 CPU 多进程 |
| 3 | `step3_ko_enrich.R` | 逐基因敲除 → 流形对齐 → dRegulation → GO/KEGG | R 线程数 = 探测值 |

产物树（与桌面课题一致）：

```text
<RESULT_DIR>/<亚群>/scTenifoldKnk_1.4.3_GPU/
  _野生型/{数据文件,报告文件}        # cpm.bin、genes.txt、抽样下标、张量、计时
  <基因>/{数据文件,报告文件}          # 扰动_Dr.csv、响应基因、富集_GO/KEGG.csv、说明
```

## 可重复运行

每步带跳过逻辑：导出（cpm.bin+genes.txt+timings.csv 在）、建网（每张 .csr 在）、张量（gpu_wt_rounded.bin 在）、敲除（扰动_Dr.csv 在）都会跳过。删掉对应文件才会重算。

## 环境

- Python 3.13 + numpy/scipy/torch（有 CUDA 用 GPU，没有自动 CPU）；`knk_accel/` 已内置
- R 4.x + `scTenifoldNet`、`scTenifoldKnk`、`clusterProfiler`、`org.Mm.eg.db`
- Rscript / CUDA 路径自动探测；也可用环境变量 `KNK_RSCRIPT`、`KNK_CUDA_BIN` 指定

## 分析协议（写在 config，不随机器变）

10 张网 × 每张抽 min(500, n-1) 细胞（seed=1，`sample.int` 不放回→有放回按 scTenifoldNet 协议有放回）、
scQC 文库 1000 / 检出 5% / 线粒体 0.1、pcNet nComp=3 q=0.9、CP rank 3、
四舍五入 3 位、流形对齐 d=2、响应基因 FDR<0.05（剔除被敲基因）、富集 BH p=0.05 q=0.2。
注：抽样下标用 base `sample.int(set.seed(1))`；与旧脚本 `30_导出现行亚群` 的 furrr 抽样路径不同，
同一数据集重算得到的细胞组合可能不同（统计协议相同）。

## 声称

虚拟敲除是计算预测，不是湿实验 KO 差异基因。富集条目来自本次敲除的响应基因表，不预先指定通路。
