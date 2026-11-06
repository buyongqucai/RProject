# 引擎选型与适用场景（SSOT）

> **唯一存放处。** 技能说明 / 交付 SOP / 接诊表只留指针。  
> **硬规则：** 一实例一引擎；多算法对照须用户另开对比任务（方法论 §5）。  
> **声称：** 一律写计算预测；禁止写成真实 KO DEG 或药效已证实。  
> 参数默认仍以 [`方法默认与信源登记_MethodDefaultsRegistry.md`](方法默认与信源登记_MethodDefaultsRegistry.md) 为准。

---

## 1. 先分清两类问题

| 问题类型 | 你有什么数据 | 本技能怎么称呼 | 典型引擎 |
|----------|--------------|----------------|----------|
| **A. 野生型-only 虚拟敲除** | 只有对照/图谱 sc(sn)RNA，没有真实扰动样本 | Virtual KO / in silico KO | scTenifoldKnk、GenKI；TF 场景可 CellOracle |
| **B. 扰动响应预测** | 已有 Perturb-seq / 药物处理 / KO–WT 配对等训练数据 | Perturbation prediction（广义扰动建模） | scGen、CPA、GEARS、CellOT |
| **C. 轻量启发式** | 已有 DEG + 先验 regulon（DoRothEA 等） | Regulon 逆转（非完整 GRN 模拟） | DoRothEA / regulon rescue |
| **D. 相关但非本技能主交付** | 轨迹/动态 GRN/基础模型 | 另技能或另开计划 | Dynamo 向量场扰动、Dictys、Geneformer/scGPT 等 |

书清类「只有公共 scRNA、无 CRISPR 屏」课题 → **优先 A**；有大规模扰动屏要外推未见组合 → **B**。

---

## 1b. 三个常见误解（先读）

### 是不是都「比较权威」？

**在各自问题类里是权威方法**（多发表于 *Nature* / *Nat Methods* / *Nat Biotechnol* / *Patterns* / *NAR*），但 **权威 ≠ 同一件事**。  
把 B 类论文里的算法写成「我们做了虚拟敲除」会审稿翻车：它们多数是 **有真实扰动数据时的响应预测**，不是 WT-only virtual KO。

### 是不是都「真的用来虚拟敲除」？

| 判定 | 引擎 | 说明 |
|------|------|------|
| **是（狭义 Virtual KO）** | scTenifoldKnk、GenKI | 输入只要 WT；在网/潜空间里「假敲」后找响应基因 |
| **是（广义 in silico 扰动，偏 TF）** | CellOracle | 在推断 GRN 上模拟 TF KO/OE；常需 ATAC/motif；不是任意基因的 Knk 式 DR 表 |
| **弱 / 启发式** | regulon 逆转 | 用先验 regulon + DEG 猜「若压这个 TF 能救回哪些 DEG」；**不是**完整虚拟敲除引擎 |
| **否（勿称虚拟敲除）** | scGen、CPA、GEARS、CellOT | 需要 **已观测的扰动/处理** 来训练或拟合；预测的是「未见扰动的表达响应」，不是「仅凭 WT 假敲基因」 |

口语上有人把整类叫「计算扰动」；本技能写报告时：**只有 A 类（及点名的 CellOracle）可称虚拟敲除/Virtual KO**；B 类必须写 **perturbation prediction / 扰动响应预测**。

### 最后出的图应不应该一样？

**不应该一样。** 一引擎一套图种与列名；禁止把 Knk 的 04 散点/DR 柱套到 GenKI/GEARS 上。

| 引擎 | 主图应长什么样（示意） | 禁止 |
|------|------------------------|------|
| scTenifoldKnk | 方法示意（建网→置零→流形）+ DR 排名散点/柱 + 富集 +（可选）STRING 子网 | 写成 KL/`hit` |
| GenKI | VGAE/KL 方法示意 + KL 排序柱 + `hit` 规则说明 + 富集 | 写成 Knk `p.adj` |
| CellOracle | GRN/信号传播示意 + 扰动前后 UMAP/向量场或目标基因表达变化 | 冒充 Knk FDR 景观 |
| regulon 逆转 | rescued 计数柱 + 所选 TF 的靶基因富集 | 当作 GRN 虚拟敲除金标 |
| GEARS / scGen / CPA / CellOT | 预测表达 vs 真值、扰动组合热图、分布对齐等 **该论文图种** | 贴 Knk 图册序 01–07 当主结果 |

Knk 主线图序见 [`出图图册_VkoFigureAtlas.md`](出图图册_VkoFigureAtlas.md)；其它引擎在实例计划里自列图序，或另开该引擎图册，**不共用 Knk 金标文件名语义**。

---

## 2. 选型口诀（接诊用）

```text
只有 WT scRNA、要预测敲某基因影响？
  ├─ 任意基因（含非 TF）→ scTenifoldKnk（默认）或 GenKI
  ├─ 明确是 master TF，且有/可做 scATAC 或 motif GRN → CellOracle
  └─ 已有疾病 DEG + 只要「干预优先级」启发式 → regulon 逆转（披露假设）

已有扰动屏 / 药物处理单细胞？
  ├─ 单扰动外推、跨条件向量算术 → scGen
  ├─ 多协变量 + 组合遗传扰动嵌入 → CPA（药化扩展 chemCPA）
  ├─ Perturb-seq 训练、预测未见单/多基因组合 → GEARS
  └─ 对照与处理为 unpaired 分布、要细胞级映射 → CellOT
```

---

## 3. 算法目录（权威来源 + 场景）

### 3.1 A 类：WT-only 虚拟敲除（本技能主战场）

| 引擎 ID | 文献 / 软件 | 输入 | 输出语义（不可混名） | 最适用场景 | 不适用 / 陷阱 | 本技能状态 |
|---------|-------------|------|----------------------|------------|----------------|------------|
| `scTenifoldKnk` | Osorio et al., *Patterns* 2022, [10.1016/j.patter.2022.100434](https://doi.org/10.1016/j.patter.2022.100434)；[GitHub](https://github.com/cailab-tamu/scTenifoldKnk) | **仅** WT counts | DR：`distance` / `p.adj` 等 | 公共图谱或对照 scRNA；敲 **任意基因**；要 FDR 式响应基因 + 下游 GO/KEGG | 不是真实 KO；GRN 质量敏感；勿与 GenKI 列名混用 | **默认主引擎**（参数见方法登记） |
| `GenKI` | Yang et al., *NAR* 2023, [10.1093/nar/gkad450](https://doi.org/10.1093/nar/gkad450)；[GitHub](https://github.com/yjgeno/GenKI) | **仅** WT AnnData + 建网 | 潜空间距离（如 KL）+ 排列 `hit` | 与 Knk 同数据场景；希望图神经网络/VGAE 叙事；可与 Knk **另开**对比任务 | 需 GPU；规则勿套用 Knk FDR | **已落地课题**（用户点名或对比时） |
| `CellOracle` | Kamimoto et al., *Nature* 2023, [10.1038/s41586-022-05688-9](https://doi.org/10.1038/s41586-022-05688-9)；[CellOracle](https://github.com/morris-lab/CellOracle) | scRNA ± **scATAC/motif** 建 GRN | TF 扰动后表达/轨迹位移（包字段） | 靶点是 **TF**；发育/命运转向；有 multiome 或可信 base-GRN | **非 TF** 勿当主引擎；无 ATAC 时 GRN 先验变弱；线性传播假设 | **用户点名启用**；实例计划自写参数 |
| regulon 逆转 | DoRothEA / decoupleR 等 + DEG | DEG + TF regulon | rescued 基因计数 / 富集 | DEG-UMAP 延展里快速排 master TF 优先级 | **非 TF**；强假设生成；≠ GRN 虚拟敲除金标 | **备选线**（样例有；非默认交付） |

> GenKI 文 Table 1 与 scTenifoldKnk 文均强调：scGen/CPA 等需真实扰动训练；**仅 WT 即可做虚拟 KO 的主流开源工具**目前主要是 Knk / GenKI（CellOracle 另需 ATAC/TF 设定）。

### 3.2 B 类：有真实扰动数据的响应预测（扩展引擎）

| 引擎 ID | 文献 / 软件 | 输入 | 输出语义 | 最适用场景 | 不适用 / 陷阱 | 本技能状态 |
|---------|-------------|------|----------|------------|----------------|------------|
| `scGen` | Lotfollahi et al., *Nat Methods* 2019, [10.1038/s41592-019-0494-8](https://doi.org/10.1038/s41592-019-0494-8) | 训练用 **对照+扰动** scRNA | 预测扰动后表达（VAE 向量算术） | 已有同扰动类型的训练细胞；跨研究/条件迁移叙事 | **不能**仅凭 WT 图谱「虚拟敲基因」当主结论 | 目录收录；**点名且有扰动数据**才开实例 |
| `CPA` | Lotfollahi et al., *Mol Syst Biol* 2023（及 chemCPA 扩展） | 扰动屏 scRNA ± 协变量；药化可用结构描述符 | 扰动/协变量嵌入与解码表达 | 组合遗传扰动、药物屏、要分解 cell-type×perturbation | 无屏数据勿用；与 Virtual KO 声称分开 | 同上 |
| `GEARS` | Roohani et al., *Nat Biotechnol* 2023, [10.1038/s41587-023-01905-6](https://doi.org/10.1038/s41587-023-01905-6)；[snap-stanford/GEARS](https://github.com/snap-stanford/GEARS) | **Perturb-seq**（多扰动、每扰动足够细胞） | 未见单/多基因组合的转录组预测 | 设计下一轮 CRISPR 组合实验；遗传互作分型 | 不支持跨细胞类型乱训；仅单基因训练时不可靠预测组合；非 bulk | 同上 |
| `CellOT` | Bunne et al., *Nat Methods* 2023, [10.1038/s41592-023-01969-x](https://doi.org/10.1038/s41592-023-01969-x) | unpaired 对照 vs 处理分布 | 细胞级最优传输映射后的响应 | 药物/细胞因子处理；要保留异质性而非只均值 | 典型不是「敲一个基因出 DR 表」；需两侧分布 | 同上 |

### 3.3 D 类：相关工具（一般不写入本技能默认 `method`）

| 名称 | 为何相关 | 本技能态度 |
|------|----------|------------|
| Dynamo 虚拟扰动 | 向量场上模拟 KO/OE，偏轨迹/速度 | 要命运动力学时另开计划；勿与 Knk DR 表混名 |
| Dictys | 动态 GRN（multiome），非 Virtual KO 专用 | 做动态网络用；不替代敲除引擎 |
| Geneformer / scGPT 等基础模型 | 可做扰动提示/迁移 | 实验性路径；须单独披露模型与提示协议 |
| SCENIC+ / Pando | 多组学 GRN 推断 | 可作 CellOracle 类上游建网，本身不是敲除统计引擎 |

---

## 4. 与书清 / DEG-UMAP 延展的关系

- 书清主线（四 GSE DEG–UMAP）**默认不含**虚拟敲除产物。  
- 延展分析若做「虚拟敲除」：无扰动屏时选 **A 类**；流水线里写的 regulon 逆转仅作启发式，报告须标明 ≠ CellOracle/Knk。  
- 用户点名 CellOracle / GEARS 等 → 按本表开**独立实例计划**，不塞进书清共享脚本默认路径。

---

## 5. 落地状态约定

| 状态 | 含义 |
|------|------|
| **默认主引擎** | 接诊未指定时填此；交付 SOP 主路径 |
| **已落地课题** | 有课题目录/脚本可复用，仍须一实例一计划 |
| **用户点名启用** | 方法登记有卡片；参数写进该次实例计划 |
| **目录收录** | 权威、可引用；本技能尚未提供统一脚本，启用前先写实例计划与环境 |

新增引擎：先在本文件加行 → 方法登记加卡片 → 方法论 §3/§7 各补一句 → 再写课题实例计划。**不要**在卡片里写「必须与某某对照」。
