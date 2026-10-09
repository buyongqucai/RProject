"""婷婷痤疮 — 完整版 1.4.3 GPU（人源 NFKB1）。

对齐琪乐无穷完整版；换路径只改 DATA_DIR / RESULT_DIR。
物种与敲除基因与 Cplx2 小鼠课题不同，勿混用。
"""
from pathlib import Path

# ============ 必改：数据集路径 + 结果存放路径 ============
DATA_DIR = Path(r"C:\Users\10540\Desktop\tingting_nfk1_data_ascii")
RESULT_DIR = Path(r"C:\Users\10540\Desktop\tingting_nfk1_results_ascii")
# ========================================================

# ---------------- 数据集约定（GSE175817 作者髓系注释导出后） ----------------
META_FILE = "meta.csv.gz"
COUNTS_FILE = "counts.rds.gz"
MODEL_COL = "stim"                 # 皮损分组列（作者对象导出后的列名）
MODEL_VAL = "Lesional"             # 第一轮：皮损侧；若作者写 Stim/lesional 则改此处
SUBTYPE_COL = "celltype"
CELL_ID_COL = "cell_id"
# 第一轮先跑 TREM2 巨噬细胞找通路；名称须与作者 celltype 字符串完全一致
# 已跑：TREM2 macrophage、M2-like macrophage（皮损 × AHR）
SUBTYPES = ("TREM2 macrophage", "M2-like macrophage")

KNOCK_GENES = ("NFKB1",)
PRIMARY_GENE = "NFKB1"               # 低相关对照相对此基因计算
GENE_NAME_COL = "gene"

# 富集物种（人）
ORG_DB = "org.Hs.eg.db"
KEGG_ORGANISM = "hsa"

# ---------------- 分析协议（包默认 / 课题计划，不随机器变） ----------------
N_NET = 10
N_CELLS = 500
MIN_LIB_SIZE = 1000
MIN_PCT = 0.05
MAX_MT_RATIO = 0.1
MIN_DETECTED = 25
N_COMP = 3
Q = 0.9
SEED = 1
N_DECIMAL = 3
FDR_CUT = 0.05
KO_ALIGN_D = 2
ENRICH_P = 0.05
ENRICH_Q = 0.2
