# DATA_SOURCE — 胰腺癌新辅助 vs 直接手术 Meta Pilot

- **data_provenance:** REAL（已发表 RCT 摘要/全文报告的 HR；非编造）
- **analysis_kind:** medical_srma_pilot
- **scope:** L1 Pilot — **不是**完整系统评价；未做全库检索、双人筛选、GRADE、PRISMA 四阶段计数
- **PICO（暂定，待用户终稿）:**
  - P: Resectable ± Borderline resectable PDAC（作者原文定义）
  - I: Neoadjuvant chemotherapy ± chemoradiotherapy pathway
  - C: Upfront / immediate surgery (± adjuvant)
  - O_primary_pilot: **Overall survival (OS) HR**（三研究终点一致，便于验证工具链）
  - O_secondary_pilot: DFS / RFS（定义不完全一致，合并仅作示意）
- **embedded:** 2026-09-03

## 纳入研究（Pilot 手动精选）

| study_id | 文献 | DOI / PMID | 人群 | 干预 | n_I | n_C |
|----------|------|------------|------|------|-----|-----|
| PREOPANC_2022 | Versteijne et al. JCO 2022 | 10.1200/JCO.21.02233 / PMID 34694891 | Resectable + BRPC | Gemcitabine CRT → surgery → adjuvant Gem | 119 | 127 |
| Prep02_JSAP05 | Unno et al. Ann Surg 2025 (phase II/III) | EuropePMC MED40235447 / UMIN000009634 | Resectable PDAC | Gemcitabine + S-1 → surgery → adjuvant S-1 | 182 | 182 |
| ESPAC5_2023 | Ghaneh et al. Lancet Gastroenterol Hepatol 2023 | 10.1016/S2468-1253(22)00348-X / PMID 36521500 | BRPC only | Combined neoadjuvant arms (GemCap / FOLFIRINOX / CRT) vs immediate surgery | 55* | 31* |

\*ESPAC5 FAS：随机 90 人，排除 4 人后 FAS；干预组为三个新辅助臂合并（20+20+17−排除）≈55，对照组 ≈31。具体以原文 FAS 为准；Pilot 用合并臂 HR（原文报告）。

## 效应量来源（可核对）

| study_id | outcome | HR (neoadjuvant vs surgery) | 95% CI | 备注 |
|----------|---------|------------------------------|--------|------|
| PREOPANC_2022 | OS | 0.73 | 0.56–0.96 | ITT；中位随访 59 mo |
| PREOPANC_2022 | DFS | 0.69 | 0.53–0.91 | 长期结果报告 |
| Prep02_JSAP05 | OS | 0.73 | 0.56–0.95 | ITT |
| Prep02_JSAP05 | RFS | 0.77 | 0.61–0.98 | 文中称 relapse-free survival |
| ESPAC5_2023 | OS | 0.29 | 0.14–0.60 | 新辅助合并 vs 直接手术；次要终点；随访短 |
| ESPAC5_2023 | DFS | 0.53 | 0.28–0.98 | 从手术起算的 1-year DFS |

## 禁止误读

- Pilot 合并效应 **不可**写成「新辅助优于直接手术」的发表级结论。
- ESPAC5 为可行性/II 期、BRPC 为主、随访短，对 OS 合并贡献权重异常大时须在敏感性分析中讨论。
- Prep-02 主要为 resectable、方案含 S-1（东亚常用），与欧美 CRT 方案异质。
