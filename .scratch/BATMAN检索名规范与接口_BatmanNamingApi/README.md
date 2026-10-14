# 父议题：BATMAN 检索名规范与接口 SOP

**标签:** 待Agent处理（用户已拍板：只允许拉丁名/英文名检索；本次只要水蛭数据）
**来源:** 2026-10-14 清风项目取数会话（BATMAN 2.0 `SHUI ZHI` 同音混条事件）

## 背景

BATMAN 2.0 以拼音 `shui zhi` 检索被归并到「水栀子 Gardenia jasminoides var. grandiflora」，
45 成分中 12 个栀子属专属、仅 4 个水蛭专属（Hirudin 系/Heparin 系）。
`hirudo / hirudo nipponica / whitmania pigra / leech / 水蛭` 均 NO MATCH（status 500）。

## 决策（用户确认，2026-10-14）

1. **检索名规范**：非 TCMSP 库只允许**拉丁名或英文名**检索，禁用拼音；无匹配记覆盖缺口，不得回退近音条目。
2. 本次交付只要**水蛭数据**（混杂条目人工截取水蛭专属成分）。

## 子单

- [x] `issues/01-网药技能补BATMAN2SOP与拉丁名规范.md`
