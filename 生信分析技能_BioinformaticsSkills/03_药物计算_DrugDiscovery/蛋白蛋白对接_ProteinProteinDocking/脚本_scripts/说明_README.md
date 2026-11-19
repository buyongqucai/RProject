# 脚本入口 — 蛋白蛋白对接

| 脚本 | 作用 |
|------|------|
| `summarize_pdb_chains.py` | 只读：每链残基数 / HET / 体积，供 `chain_survey` |
| `clean_pp_structures.py` | 按 `het_policy` 清理；写 `clean_report.json` |
| `pymol_pp_dock_viz_standard.py` | ST/PT/CJ/QJ → big/surface/detail `.pse`+PNG |
| `prepare_detail_square.py` | **已定稿**：用户截图 → 对接颜色定界 → 正方形 → 拉到 6000² |
| `combine_pp_result.py` | 薄封装；优先直接跑 `E:\PythonProject\分子对接\2.分子对接结果图组合.py` |

## 推荐顺序

```text
python summarize_pdb_chains.py 00_raw/*.pdb
# 填写 01_clean/chain_survey.md → 登记 chain_source
python clean_pp_structures.py 00_raw/ST.pdb 01_clean/ST_clean.pdb --chains C --het-policy keep_cofactor
python clean_pp_structures.py 00_raw/PT.pdb 01_clean/PT_clean.pdb --chains A,B --het-policy keep_cofactor
# 上传 HDOCK（默认）→ 取回 model_N.pdb → 拆 ST_*.pdb / PT_*.pdb
# 写入桌面：{ST}_{PT}_蛋白蛋白对接_序号文件夹/N/

E:\pymol\python.exe pymol_pp_dock_viz_standard.py \
  --st .../1/ST_*.pdb --pt .../1/PT_*.pdb --out-dir .../1 --tag 1

# 手调并截图 → 原图放入 图片/detail-N_用户原图.png → 切方 → 拼图
python prepare_detail_square.py .../1/图片/detail-1_用户原图.png -o .../1/图片/detail-1.png
python E:\PythonProject\分子对接\2.分子对接结果图组合.py --dir=.../1/图片 1

# 仅有 .pse、未截图时才用对接完整钩子：
python ..\分子对接与虚拟筛选_MolecularDocking\脚本_scripts\export_detail_png_from_pse.py --root .../1
```

定稿：[`对接与交付基线_PPDockBaseline.md`](../文档_docs/对接与交付基线_PPDockBaseline.md)。
