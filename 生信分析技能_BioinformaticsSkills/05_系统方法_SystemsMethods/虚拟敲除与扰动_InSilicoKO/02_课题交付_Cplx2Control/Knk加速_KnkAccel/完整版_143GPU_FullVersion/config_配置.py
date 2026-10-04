"""完整版 1.4.3 GPU —— 只需要改这两个路径。

换数据集时改 DATA_DIR 与 RESULT_DIR 即可直接运行；
亚群名 / 基因名不同时，再改下方「数据集约定」段。
分析参数是课题协议（包默认），不是资源，不随机器变化。
"""
from pathlib import Path

# ============ 必改：数据集路径 + 结果存放路径 ============
DATA_DIR = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除\数据文件")
RESULT_DIR = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除\结果文件")
# ========================================================

# ---------------- 数据集约定（换数据集时看一眼） ----------------
META_FILE = "01_细胞注释_CellMeta_GSE197289.csv.gz"   # 细胞注释表（csv.gz）
COUNTS_FILE = "02_表达矩阵_Counts_GSE197289.RDS.gz"   # 基因×细胞稀疏计数（RDS）
MODEL_COL = "model"          # 分组列名
MODEL_VAL = "Control"        # 只取这一组
SUBTYPE_COL = "subtype"      # 亚群列名
CELL_ID_COL = "V1"           # 细胞 ID 列名
SUBTYPES = ("PEP", "NF1")    # 要跑的亚群
KNOCK_GENES = ("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
GENE_NAME_COL = "gene"       # 计数矩阵行名即基因名；无需另设

# ---------------- 分析协议（包默认 / 课题计划，不随机器变） ----------------
N_NET = 10                   # 每亚群建网数
N_CELLS = 500                # 每张网抽样细胞数（不足则 n-1）
MIN_LIB_SIZE = 1000          # scQC 文库大小
MIN_PCT = 0.05               # scQC 基因检出比例
MAX_MT_RATIO = 0.1           # scQC 线粒体比例
MIN_DETECTED = 25            # 基因保留：检出细胞数（或强制保留敲除基因）
N_COMP = 3                   # pcNet 主成分数
Q = 0.9                      # pcNet 分位数
SEED = 1                     # 抽样种子（只管抽样波动）
N_DECIMAL = 3                # 野生型张量四舍五入位数
FDR_CUT = 0.05               # 响应基因 FDR
KO_ALIGN_D = 2               # 流形对齐维数
ENRICH_P = 0.05              # 富集 BH p
ENRICH_Q = 0.2               # 富集 qvalue
