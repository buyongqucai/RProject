# chain_survey — DLD × SCD

## ST — DLD / 6I4Q
- title / method / resolution: Human DLD; X-ray 1.75 Å
- biological assembly: obligate homodimer A+B
- literature: 线粒体 E3；功能二聚 + FAD
- chain table:
  | chain | n_res | note | HET |
  |-------|-------|------|-----|
  | A | 472 | +FAD | BTB, SO4, HOH |
  | B | 481 | +FAD | 同上 |
- chosen chains: **A+B** + keep FAD
- chain_source: `auth_asym_partner`
- discarded HET: BTB, SO4, HOH
- volume estimate (MB): clean ~0.55 MB

## PT — SCD / 4ZYO
- title / method / resolution: Human integral membrane stearoyl-CoA desaturase with substrate; X-ray 3.25 Å
- biological assembly: monomer fragment（UNP 45–359）
- literature: ER 膜 SCD1；STRING 邻域为脂代谢酶，**无** DLD–SCD 直接强互作证据 → 假设性对接；膜蛋白局限写 STATUS
- chain table:
  | chain | n_res | note | HET |
  |-------|-------|------|-----|
  | A | 298 | fragment + Zn | ST9, LMT, HOH, ZN |
- chosen chains: **A**；keep ZN；drop ST9（底物）/ LMT（去污剂）/ HOH
- chain_source: `entity_longest`（仅一条功能片段链）
- volume estimate (MB): clean ~0.19 MB

## ST/PT assignment
- ST = DLD（更大）; PT = SCD（较小膜蛋白片段）
- rationale: 更大侧固定；膜蛋白作配体

## Decision
- proceed（假设性；3.25 Å + 膜片段须在 STATUS 标明局限）
