# 菌群臂真实队列验证报告（HMP2/IBDMDB，2026-10-08）

**方法**：对 IBDMDB/HMP2 宏基因组队列（UC=459、nonIBD=429、CD=750）预登记的 15 个物种/分类单元做 UC vs nonIBD 比较（中位数、检出率、Mann-Whitney U 双侧、BH-FDR），效应量为 rank-biserial r（r<0=UC 耗竭）。

**核心结果**：
- 显著耗竭（FDR<0.05）：*Ruminococcus bromii*（r=-0.264，FDR=1.5×10⁻¹⁴；检出率 21.1% vs 49.0%）；*Bilophila wadsworthia*（r=-0.167，FDR=2.1×10⁻⁶）。
- 显著富集（FDR<0.05）：Enterobacteriaceae 科合计（r=+0.134，FDR=1.7×10⁻³）、*Escherichia coli*（r=+0.107）、*Ruminococcus gnavus*（r=+0.102）、*Butyricicoccus pullicaecorum*（FDR=6.8×10⁻⁴，但丰度极低，检出率 3.9% vs 0.2%）、*Anaerostipes* unclassified（FDR=5.8×10⁻³）。
- 方向一致但未过 FDR：*F. prausnitzii*（r=-0.040，p=0.30）、*E. rectale*（r=-0.081，名义 p=0.036，FDR=0.064）、*C. comes*、*R. intestinalis* 均不显著。*Anaerobutyricum* 属 not_detected（该表以 *E. hallii* 计，无差异）。
- Guild（丁酸产生菌样本级求和）：UC vs nonIBD 中位数 0.150 vs 0.137，p=0.34 不显著（r=+0.037）；CD vs nonIBD 0.098 vs 0.137，p=3.3×10⁻⁷ 显著耗竭。

**与丁酸轴假设的关系**：核心丁酸菌在 UC 中方向一致（轻度耗竭）但未达显著，guild 阴性；显著信号集中于抗性淀粉上游菌 *R. bromii* 耗竭与肠杆菌科富集，CD 中 guild 显著耗竭——该轴在本队列的异常更清晰地见于 CD，对 UC 为弱支持。

**局限**：① 横断面、单队列，仅能描述组间差异，不能推断因果或外推人群；② 相对丰度具组成性，物种间升降互为消长，且同一受试者多时间点样本按独立处理、未建模重复测量。
