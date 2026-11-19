# chain_survey — ACOX1 × DLD

## ST — ACOX1 / 7Q84
- title / method / resolution: Crystal structure of human peroxisomal acyl-CoA oxidase 1A, apo-form; X-ray 2.00 Å
- biological assembly: homodimer (chains A+B)
- literature: ACOX1 过氧化物酶体 β-氧化限速酶，功能二聚；HPA/STRING **无** ACOX1–DLD 直接实验互作强证据 → 本对接为课题假设粗模
- chain table:
  | chain | n_res | note | HET |
  |-------|-------|------|-----|
  | A | 626 | isoform 2 | CSO, EDO, GOL, PEG, PGE, HOH |
  | B | 623 | isoform 2 | 同上 |
- chosen chains: **A+B**
- chain_source: `auth_asym_partner`（同源二聚生物学组装）
- discarded chains + why: 无其它蛋白链；HET 去溶剂/结晶试剂（CSO 修饰 Cys 对接时省略）
- volume estimate (MB): clean ~0.76 MB

## PT — DLD / 6I4Q
- title / method / resolution: Human dihydrolipoamide dehydrogenase; X-ray 1.75 Å
- biological assembly: obligate homodimer A+B
- literature: 线粒体 E3；功能二聚含 FAD
- chain table:
  | chain | n_res | note | HET |
  |-------|-------|------|-----|
  | A | 472 | +FAD | BTB, SO4, HOH |
  | B | 481 | +FAD | 同上 |
- chosen chains: **A+B** + keep FAD
- chain_source: `auth_asym_partner`
- discarded HET: BTB, SO4, HOH
- volume estimate (MB): clean ~0.55 MB

## ST/PT assignment
- ST = ACOX1（更大，~1249 res 二聚）; PT = DLD（~953 res 二聚）
- rationale: 体积更大侧作受体（HDOCK receptor）

## Decision
- proceed（假设性 PPI；STATUS 标明无强文献界面）
