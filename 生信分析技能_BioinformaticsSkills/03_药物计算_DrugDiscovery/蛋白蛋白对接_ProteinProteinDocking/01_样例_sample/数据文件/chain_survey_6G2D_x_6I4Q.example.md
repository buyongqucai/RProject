# chain_survey 示例 — ACACA × DLD（姿态金标未入库；provenance BLOCKED）

## ST — ACACA / 6G2D

- title / method / resolution: Citrate-induced ACC-Cit filament；EM 5.4 Å
- biological assembly: 纤维（多原体）
- literature: ACC 纤维组装；伙伴对接取全长原体而非整纤维
- chain table:

| chain | n_res | note | HET |
|-------|-------|------|-----|
| B | 625 | 片段 | - |
| C | 2121 | 完整样原体 | - |
| D | 2121 | 完整样原体 | - |
| F | 634 | 片段 | - |

- chosen chains: **C**
- chain_source: `entity_longest`
- discarded: B/F 片段；D 另一原体（控体积）
- volume estimate: 全原子单链大；ZDOCK 常需 CA → model_note

## PT — DLD / 6I4Q

- title / method / resolution: human DLD；X-ray 1.75 Å
- biological assembly: obligate homodimer A+B
- literature: 二聚体功能相关；各亚基 FAD
- chain table:

| chain | n_res | note | HET |
|-------|-------|------|-----|
| A | 472 | 单体 | FAD, BTB, SO4, HOH |
| B | 481 | 单体 | FAD, BTB, SO4, HOH |

- chosen chains: **A,B** + keep FAD
- chain_source: `auth_asym_partner`
- discarded HET: BTB, SO4, HOH

## ST/PT assignment

- ST = ACACA chain C；PT = DLD A+B
- proceed
