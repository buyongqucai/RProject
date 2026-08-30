# 三库数据下载（TCMSP 药物 / RCSB+PubChem 对接 / KEGG 通路）

> 标签：待Agent处理 → 进行中
> 创建：2026-08-31｜负责人：Agent
> 关联技能：网络药理学（成分靶点 SOP）、分子对接（DockingPipelineSOP）、bio-structure-animation（KEGG GIF）

## 需求拆解（用户原话 2026-08-31）

1. **TCMSP**：补齐《中国药典》常用中药（准备文件已有 ~200 味），格式对齐
   `TCMSP{药}参数表格.xlsx`（13 列含 Save 空列）+ `TCMSP{药}有效成分靶点表格.xlsx`（无表头，成分→靶点）。
   兜底链：TCMSP 无 → HERB（成分+SMILES）→ SwissTargetPrediction（Probability>0）→ 分子太多走 PharmGKB →
   HERB 也无 → BATMAN（仅 known，不要预测）。
2. **分子对接库**：`D:\数据库\分子对接数据库\test\` 下 big/big_clean/big_clean_h/small/small_clean/small_clean_h；
   蛋白表 112 条（PDB ID + 少量 UniProt→AlphaFold）、化合物表 224 个 PubChem CID；总量 ≤40GB。
3. **KEGG**：映射表 183 条中 95 条「待绘制」；另扩展常见/前沿通路；官方 PNG → `KEGG通路图`，
   动画 GIF → `KEGG动画图`；已绘制不重绘。

## 技术验证记录（2026-08-31 凌晨）

- TCMSP-e 无需登录：`tcmsp.php` 取 token → `tcmspsearch.php?qs=herb_all_name&q={拼音}&token=` →
  `tcmspsearch.php?qr={拉丁名}&qsr=herb_en_name&token=`（成分 JSON 内嵌 kendoGrid）→
  `molecule.php?qn={molecule_ID}`（靶点 JSON + ADME 全字段）。
- 模板列映射：FASA- 列实际 = **tpsa** 字段；HL = halflife；Save = 空。
- 筛选：OB≥30 且 DL≥0.18（羌活 185 → 15，与参考表行数一致 ✓）。
- 全草药清单：`browse.php?qc=herbs`（kendoGrid JSON，~499 味 = 2015 药典集）。
- 本机工具：Python 3.13 + openpyxl + requests ✓；Open Babel 3.1.1（E:\OpenBabel-3.1.1）✓。
- KEGG GIF 管线：`E:\绘图\人体生物结构动画\SKILL.md`（GenerateImage 完整提示词 + PIL 合成，
  禁止截断提示词；001–088 为画风金标）。

## 进度（2026-08-31 全部完成）

- [x] TCMSP 试点：羌活 185→15 成分、109 靶点对，与参考表逐项一致（数值差 ≤0.01 系版本漂移）
- [x] TCMSP 全量：browse 502 味 − 已有 171 = **331 味补缺，331/331 OK**（`_tcmsp_scrape_log.csv`）
- [x] 兜底链：TCMSP 宇宙（2015 药典 502 味）已全覆盖，无缺味；2020 药典新增味如需再启动 HERB→STP
- [x] 对接库：111 蛋白（101 RCSB + 9 AlphaFold v6 + 9CMK 走 CIF）+ 224 化合物全量；
  修补 18 盐型→母体 CID、苯甲酸平面放行、硅氧烷 SKIP_unsupported、2 个无 3D 者（邻苯二甲酸母体 / SMILES+gen3d）；
  终盘 big 112 / big_clean 111 / big_clean_h 111 / small 225 / small_clean 224 / small_clean_h 223，**0.56 GiB ≪ 40GB**
- [x] KEGG PNG：95 张「待绘制」官方图早已齐（skip=95）；新增 30 条扩展通路 PNG 已下载
- [x] KEGG 扩展：184–213（癌症总览/铁死亡/溶酶体/Notch/Hedgehog/昼夜节律/产热/突触系/PD/ALS/HD/心肌病等 30 条），
  官方名经 rest.kegg.jp 校验，映射表+manifest+kegg_zh_names 已同步
- [x] KEGG GIF：95 条旧 GIF 实体已存在（状态未登记）→ 翻牌已绘制；新增 30 条 GenerateImage 全提示词底图 + 合成 + QA 通过；
  **映射表 213/213 全部已绘制**

标签：已完成
