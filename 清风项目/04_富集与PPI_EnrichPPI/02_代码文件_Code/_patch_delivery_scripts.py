# -*- coding: utf-8 -*-
"""从努力学习项目移植 32/28/26 三脚本到清风项目（07/08/09），只改路径与项目文案，不动结构/样式。"""
from __future__ import annotations

from pathlib import Path

SRC = Path(r"E:/RProject/努力学习项目/网络药理学/代码文件")
DST = Path(r"E:/RProject/清风项目/04_富集与PPI_EnrichPPI/02_代码文件_Code")

R32 = (SRC / "32_export_cytoscape_network_analysis.py").read_text(encoding="utf-8")
R28 = (SRC / "28_collect_report_stats.py").read_text(encoding="utf-8")
R26 = (SRC / "26_build_html_report.py").read_text(encoding="utf-8")


def rep(t: str, old: str, new: str, tag: str) -> str:
    if old not in t:
        raise SystemExit(f"MISSING anchor: {tag}")
    return t.replace(old, new)


# ================= 07 网络分析报告（§J） =================
t = R32
t = rep(t, 'ROOT = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件")',
        'ROOT = Path(r"E:/RProject/清风项目/交付文件")', "32 ROOT")
t = rep(t, "    write_rg_note(df)\n",
        "    # 清风项目 9 味药均有靶点（水蛭=已知靶点路径），无 §K 空靶点药味 -> 不写无靶点说明\n", "32 rg-note call")
t = rep(t, '<div class="stat"><div class="k">肉桂 RG · Degree</div><div class="v">{rg_deg if rg_deg is not None else "—"}</div></div>',
        '<div class="stat"><div class="k">最大 Degree</div><div class="v">{int(df["Degree"].max())}</div></div>', "32 rg stat")
t = rep(t, "<strong>肉桂（RG）：</strong>Degree = 0 源于上游数据缺口（TCMSP 有效成分为空等），不是「无药理作用」。详见 <code>肉桂_无靶点说明.txt</code>。",
        "<strong>空靶点药味：</strong>本方 9 味药均有靶点支持（水蛭为 BATMAN-TCM 已知靶点），无 §K 数据缺口药味（无 Degree=0 药味）。", "32 rg note block")
(DST / "07_网络分析报告_exportNetworkAnalysis.py").write_text(t, encoding="utf-8")
print("OK 07")

# ================= 08 交付统计（§H _stats.json） =================
t = R28
t = rep(t, 'ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")',
        'ROOT = Path(r"E:/RProject/清风项目")', "28 ROOT")
t = rep(t, '"n_herbs_nominal": 12,', '"n_herbs_nominal": 9,', "28 herbs")
(DST / "08_交付统计_collectReportStats.py").write_text(t, encoding="utf-8")
print("OK 08")

# ================= 09 交付 HTML 报告（§H） =================
t = R26
t = rep(t, 'ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")',
        'ROOT = Path(r"E:/RProject/清风项目")', "26 ROOT")
t = rep(t, 'STATS_PY = ROOT / "代码文件" / "28_collect_report_stats.py"',
        'STATS_PY = ROOT / "04_富集与PPI_EnrichPPI" / "02_代码文件_Code" / "08_交付统计_collectReportStats.py"', "26 stats_py")
t = rep(t, "<title>溃疡性结肠炎 · 网络药理学交付报告</title>",
        "<title>特发性肺纤维化（水蛭宣痹化纤汤）· 网络药理学交付报告</title>", "26 title")
t = rep(t, "<h1>溃疡性结肠炎 · 网络药理学交付报告</h1>",
        "<h1>特发性肺纤维化（水蛭宣痹化纤汤）· 网络药理学交付报告</h1>", "26 h1")
t = rep(t, "以 12 味药（肉桂靶点为 0）筛选有效成分与疾病靶点交集",
        "以 9 味药（水蛭为 BATMAN-TCM 已知靶点）筛选有效成分与疾病靶点交集", "26 hero")

old_biomap = t[t.find("bio_map = {"):t.find("}", t.find("bio_map = {")) + 1]
new_biomap = '''bio_map = {
        "hsa04657": "IL-17 轴促 Th17/中性粒细胞炎症，参与肺纤维化模型中的成纤维细胞活化；对照 IPF 文献解读。",
        "hsa04668": "TNF 信号是肺纤维化炎症微环境的核心轴之一。",
        "hsa04620": "TLR 通路参与肺固有免疫与损伤修复应答。",
        "hsa04066": "HIF-1 与缺氧微环境、肺血管重塑相关。",
        "hsa04151": "PI3K-Akt 调控细胞存活、增殖与纤维化相关信号。",
        "hsa05417": "富集常因共享炎症/脂质代谢基因；解读时对照 IPF 文献，勿直接等同动脉粥样硬化。",
        "hsa05418": "血流剪切应力通路富集常由炎症/内皮基因共享驱动；与 IPF 肺血管重塑文献对照解读。",
        "hsa04933": "AGE-RAGE 常因炎症基因重叠出现；宜作交叉通路提示。",
        "hsa05161": "病毒感染通路多反映 NF-κB/凋亡等共享模块，非指肝炎病因。",
        "hsa05167": "同上，感染类通路多为共享信号模块富集。",
        "hsa05205": "肿瘤相关通路常因增殖/基质基因重叠；作旁证而非肿瘤结论。",
        "hsa05215": "肿瘤通路富集多因增殖/凋亡基因共享；对照 IPF 上皮-间质转化文献解读。",
        "hsa05160": "感染类通路多为 NF-κB/干扰素共享模块；勿作病因结论。",
        "hsa05207": "化学致癌-受体激活通路常因核受体/激酶基因重叠；作旁证。",
        "hsa05163": "巨细胞病毒通路多反映炎症/趋化共享模块。",
    }'''
t = rep(t, old_biomap, new_biomap, "26 biomap")
t = rep(t, 'note = bio_map.get(pid, "结合 geneID 与 UC 文献判断是否为共享炎症模块或疾病特异轴。")',
        'note = bio_map.get(pid, "结合 geneID 与 IPF 文献判断是否为共享炎症/纤维化模块或疾病特异轴。")', "26 fallback note")
t = rep(t, '香附/淫羊藿/黄连等交集靶点多，提示其在方剂抗炎轴中贡献更大；',
        '川芎/黄芪/甘草等交集靶点多，提示其在方剂抗纤维化与抗炎轴中贡献更大；', "26 herb sentence")
t = rep(t, '肉桂靶点为 0，流量图中通常不可见，写作时需注明数据缺口而非「无作用」。',
        '本方 9 味药均有靶点支持（水蛭为已知靶点路径），无空靶点药味。', "26 rg sentence 2")
t = rep(t, '肉桂当前靶点为 0，讨论时注明数据来源限制。',
        '水蛭为 BATMAN-TCM 已知靶点路径获取，其余 8 味走 TCMSP 瀑布。', "26 rg sentence 3")
t = rep(t, '<strong>药病交集 291</strong>',
        '<strong>药病交集 {esc(s.get(\'n_overlap\'))}</strong>', "26 291")
t = rep(t, "全量 GeneCards 噪声大（弱相关基因极多），不过滤会稀释富集与 PPI，反而不严谨。</li>",
        "全量 GeneCards 噪声大（弱相关基因极多），不过滤会稀释富集与 PPI，反而不严谨。</li>"
        "<li><strong>验证脚注：</strong>GeneCards 原始导出 9787 行剔除非基因条目 COPD（1 条）计 9786；"
        "CTD 直接证据 23 条剔除小鼠基因 CCL12（无对应人类基因）计 22；两处剔除不影响主并集。</li>", "26 footnote")
(DST / "09_交付HTML报告_buildHtmlReport.py").write_text(t, encoding="utf-8")
print("OK 09")
print("ALL PATCHED")
