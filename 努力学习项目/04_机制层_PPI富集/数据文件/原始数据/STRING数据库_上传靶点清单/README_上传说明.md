# STRING 上传靶点清单

本目录为 **送入 STRING 的原始输入**（Homo sapiens，combined score ≥ 0.900）。

| 文件 | 用途 |
|------|------|
| `Main_STRING上传靶点_geneList.txt` | 主面板 C（H+M）基因，一行一个，可直接粘贴/上传 |
| `Full_STRING上传靶点_geneList.txt` | 全库敏感性 C 基因列表 |
| 同名 `.csv` | 带表头 `gene`，便于脚本读取 |

基因来源：`上游模块_03三源结果/C_*_H_plus_M.csv`。

## 结果数据（勿放本目录）

STRING 导出边与后续分析在：

`数据文件/结果数据/机制层/`

含 `STRING_*_score900.tsv`、边表、MCC、MCODE、GO/KEGG、五层网等。
