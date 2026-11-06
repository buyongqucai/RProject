# 脚本入口 — 蛋白蛋白对接

| 脚本 | 作用 |
|------|------|
| `summarize_pdb_chains.py` | 只读：每链残基数 / HET / 体积，供 `chain_survey` |
| `clean_pp_structures.py` | 按 `het_policy` 清理；写 `clean_report.json` |
| `pymol_pp_dock_viz_standard.py` | ST/PT/CJ/QJ → big/surface/detail `.pse`+PNG |
| `prepare_detail_square.py` | 用户 detail 截图 → 去白边 → 居中切正方形 |
| `combine_pp_result.py` | big + detail → `result_N.png`（分子对接拼图引擎） |

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

# 手调 detail-1.pse 后由用户截图（可多角度）→ 落盘到 图片/
python prepare_detail_square.py 用户截图_detail2.jpg -o .../1/图片/detail-2.png --also-jpeg
python combine_pp_result.py --img-dir .../1/图片 --index 2
```

定稿指针：[`对接与交付基线_PPDockBaseline.md`](../文档_docs/对接与交付基线_PPDockBaseline.md)；几何细节复用分子对接 SOP §7.3/§7.4。
