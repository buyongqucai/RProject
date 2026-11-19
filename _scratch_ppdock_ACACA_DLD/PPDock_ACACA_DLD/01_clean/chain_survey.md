# chain_survey — ACACA × DLD

## ST — ACACA / 6G2D

- title / method / resolution: Citrate-induced ACC-Cit filament；EM **5.4 Å**
- biological assembly: 纤维
- literature: ACC 纤维；对接取全长原体而非整纤维（PMID 相关 Nature 2018 ACC 结构）
- chain table: B/F≈625–634 片段；C/D≈2121 完整样原体；无 HET
- chosen chains: **C**
- chain_source: `entity_longest`
- discarded: B、F（片段）；D（另一原体，控体积）
- volume: 全原子 clean ≈1.29 MB → ZDOCK 用 CA（`model_note`）

## PT — DLD / 6I4Q

- title / method / resolution: human DLD；X-ray **1.75 Å**
- biological assembly: obligate homodimer A+B
- literature: 二聚体功能相关；各亚基 FAD
- chosen chains: **A,B** + FAD
- chain_source: `auth_asym_partner`
- discarded HET: BTB、SO4、HOH
- volume: clean ≈0.55 MB（可全原子）

## ST/PT assignment

- ST = ACACA chain C（更大/固定）；PT = DLD A+B（移动）
- proceed
