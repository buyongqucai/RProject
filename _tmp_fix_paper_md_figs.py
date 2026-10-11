# -*- coding: utf-8 -*-
"""Fix paper report: include full MD atlas (incl 3D FEL) + missing module figs.

Root cause: prior rebuild used a hand-picked short alias set under 00/图片文件
(rmsd/com/2D-fel only), never inventoried 08/.../分子动力学图_MD/ 01–20.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from PIL import Image

ROOT = next(
    p
    for p in Path(r"E:/RProject").iterdir()
    if p.is_dir() and any(x.name.endswith("ProjectLayout.md") for x in p.iterdir())
)
OUT = ROOT / "00_全流程报告" / "结果文件" / "报告文件"
IMG00 = ROOT / "00_全流程报告" / "结果文件" / "图片文件"
DELIV = next((p for p in ROOT.iterdir() if p.is_dir() and "交付" in p.name), None)

MD_REL = Path("../../../08_分子动力学/结果文件/图片文件/分子动力学图_MD")
TOX_REL = Path("../../../02_网络毒理学_毒性分层/结果文件/图片文件/毒性分层")
MECH_REL = Path("../../../04_机制层_PPI富集/结果文件/图片文件/机制层")
IMG = Path("../图片文件")

SYSTEMS = [
    (
        "MMP9_Tryptophan_4H3X",
        "色氨酸–MMP9（4H3X）",
        {
            "bb": "0.2805147",
            "lig": "0.2325846",
            "com": "1.052",
            "ns": "100.000",
        },
    ),
    (
        "ADA_Adenosine_7RTG_A2",
        "腺苷–ADA_A2（7RTG）",
        {
            "bb": "0.2023644",
            "lig": "0.5247688",
            "com": "0.886",
            "ns": "100.000",
        },
    ),
]

# NN -> (folder_prefix_stem matching, short Chinese title, prose template)
# Files are like 17_自由能形貌3D图/17_自由能形貌3D_FreeEnergyLandscape3D.png
MD_ATLAS = [
    (1, "骨架RMSD", "骨架 RMSD", "横轴为时间（ns），纵轴为蛋白骨架 RMSD（nm）。{sys} 生产段 {ns} ns；监控骨架 RMSD 最大 {bb} nm。"),
    (2, "三线RMSD", "三线 RMSD", "同图叠蛋白、配体与复合物 RMSD：横轴时间（ns），纵轴 RMSD（nm）。{sys} 配体 RMSD 最大 {lig} nm，与骨架曲线对照看是配体晃动还是整体漂移。"),
    (3, "残基RMSF", "Cα RMSF", "横轴为残基编号，纵轴为 Cα RMSF（nm）。峰值标出柔性环/末端；核区应明显更低。{sys} 用于定位柔性，不单独证明结合。"),
    (4, "氢键数", "氢键数", "横轴时间（ns），纵轴为蛋白–配体氢键条数。波动表示接触时有时无；不能把单帧氢键写成稳定占用率。{sys}。"),
    (5, "回旋半径", "回旋半径 Rg", "横轴时间（ns），纵轴 Rg（nm）。平台表示整体紧实度未失控膨胀。{sys}。"),
    (6, "溶剂可及表面积", "SASA", "横轴时间（ns），纵轴溶剂可及表面积（nm²）。大幅持续上升才提示暴露异常。{sys}。"),
    (7, "质心距离", "质心距离 COM", "横轴时间（ns），纵轴蛋白–配体质心距离（nm）。{sys} COM 最大 {com} nm；持续拉到数纳米才属飞出。"),
    (8, "NVT温度", "NVT 温度", "平衡段质控：横轴时间，纵轴温度（K）。看恒温器是否把体系拉在设定附近，不是生物学结论。{sys}。"),
    (9, "NPT温度", "NPT 温度", "NPT 段温度–时间曲线，读法同 NVT：质控平台，不作结合结论。{sys}。"),
    (10, "NPT压力", "NPT 压力", "NPT 段压力–时间；允许噪声，关注是否发散。{sys}。"),
    (11, "NPT密度", "NPT 密度", "NPT 段密度–时间；应落到合理溶剂密度平台。{sys}。"),
    (12, "生产势能", "生产势能", "生产段势能–时间；用于排除能量发散，不读成结合自由能。{sys}。"),
    (13, "自由能形貌", "FEL 2D（RMSD×Rg）", "二维自由能形貌：横轴骨架 RMSD，纵轴 Rg，颜色为相对自由能（kJ/mol，Viridis）。低能盆地=采样更密区。{sys}。不作实验 ΔG。"),
    (14, "自由能形貌RMSDx质心", "FEL 2D（RMSD×COM）", "二维 FEL：横轴 RMSD，纵轴质心距离，颜色为相对自由能。看结合松紧的采样偏好。{sys}。"),
    (15, "自由能形貌RMSDxSASA", "FEL 2D（RMSD×SASA）", "二维 FEL：横轴 RMSD，纵轴 SASA，颜色为相对自由能。{sys}。"),
    (16, "自由能形貌配体蛋白RMSD", "FEL 2D（配体×蛋白 RMSD）", "二维 FEL：横轴配体 RMSD，纵轴蛋白 RMSD，颜色为相对自由能；区分谁在动。{sys}。"),
    (17, "自由能形貌3D", "FEL 3D（RMSD×Rg）", "三维自由能形貌曲面（与图种 13 同投影网格）：底面两轴为 RMSD 与 Rg，高度/颜色为相对自由能（显示封顶约定见 MD 出图规范）。漏斗+底板投影用于看盆地深浅，仍不是实验结合自由能。{sys}。"),
    (18, "自由能形貌3D_RMSDx质心", "FEL 3D（RMSD×COM）", "三维 FEL：投影为 RMSD×质心距离，曲面高度为相对自由能。{sys}。"),
    (19, "自由能形貌3D_RMSDxSASA", "FEL 3D（RMSD×SASA）", "三维 FEL：投影为 RMSD×SASA。{sys}。"),
    (20, "自由能形貌3D_配体蛋白RMSD", "FEL 3D（配体×蛋白 RMSD）", "三维 FEL：投影为配体 RMSD×蛋白 RMSD。{sys}。"),
]


def find_md_png(sys_id: str, nn: int, stem_key: str) -> Path:
    base = ROOT / "08_分子动力学" / "结果文件" / "图片文件" / "分子动力学图_MD" / sys_id
    # folder like 17_自由能形貌3D图
    folders = sorted(
        [
            d
            for d in base.iterdir()
            if d.is_dir() and d.name.startswith(f"{nn:02d}_")
        ]
    )
    if not folders:
        raise FileNotFoundError(f"no folder {nn} under {base}")
    # prefer folder whose name contains stem_key
    folder = next((d for d in folders if stem_key in d.name), folders[0])
    pngs = list(folder.glob("*.png"))
    if not pngs:
        raise FileNotFoundError(folder)
    # prefer name containing stem_key
    png = next((p for p in pngs if stem_key in p.name), pngs[0])
    return png


CSS = """
body{margin:0;font-family:"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.82;color:#1c241f;background:#f3efe6}
.layout{display:grid;grid-template-columns:16.5rem minmax(0,1fr);min-height:100vh}
.side{position:sticky;top:0;height:100vh;overflow:auto;background:#24362f;color:#f4efe6;padding:1rem .75rem 2rem}
.side h1{font-size:1.0rem;margin:0 0 .35rem}
.side a{display:block;color:#e7eee9;text-decoration:none;font-size:.8rem;padding:.24rem .35rem;border-radius:.35rem}
.side a:hover{background:rgba(255,255,255,.08)}
.main{max-width:72rem;padding:1.2rem 1.5rem 3rem}
h2{border-bottom:2px solid #d5e0d7;padding-bottom:.25rem;margin-top:2rem}
h3{margin:1rem 0 .35rem;color:#24362f}
h4{margin:.65rem 0 .2rem;color:#3a4a42;font-size:.95rem}
figure{margin:1rem 0;background:#fffdf8;border:1px solid #ddd4c4;border-radius:.75rem;padding:.75rem}
figure img{width:100%;height:auto;display:block;max-height:42rem;object-fit:contain}
figcaption{margin-top:.5rem;background:#f6f3ec;border-left:.25rem solid #2f5d4c;padding:.55rem .7rem}
.take{background:#eef6f1;border-left:.35rem solid #2f5d4c;padding:.75rem 1rem;border-radius:.45rem;margin:.8rem 0}
.note{background:#fff8ea;border-left:.35rem solid #8a6a3a;padding:.75rem 1rem;border-radius:.45rem;margin:.8rem 0}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.86rem;margin:.4rem 0 .9rem}
th,td{border:1px solid #ddd4c4;padding:.35rem .45rem;vertical-align:top}
th{background:#eef3ef;text-align:left}
code{font-size:.84em;background:#f0ebe1;padding:.05rem .25rem;border-radius:.25rem}
.footer{color:#5c635c;font-size:.85rem;margin-top:2rem}
@media(max-width:52rem){.layout{grid-template-columns:1fr}.side{position:relative;height:auto;max-height:42vh}}
""".strip()


def fig(src: str, cap: str) -> str:
    return (
        f"<figure><img src='{src}' alt=''/>"
        f"<figcaption>{cap}</figcaption></figure>"
    )


def shell(title: str, nav: str, body: str, footer: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>{CSS}</style></head>
<body><div class="layout">
<aside class="side"><h1>{title}</h1>{nav}</aside>
<main class="main">{body}
<p class="footer">{footer}</p>
</main></div></body></html>
"""


def md_src(sys_id: str, nn: int, stem_key: str) -> str:
    png = find_md_png(sys_id, nn, stem_key)
    rel = Path("../../../08_分子动力学/结果文件/图片文件/分子动力学图_MD") / sys_id / png.parent.name / png.name
    return rel.as_posix()


def build_md_section(fig_start: int) -> tuple[str, int]:
    parts = [
        """
<h2 id="s-md">分子动力学</h2>
<p>对接最强三对进入 MD。正式交付为色氨酸–MMP9（4H3X）与腺苷–ADA_A2（7RTG）；空口袋 ADA 对照约 42 ns 飞出、吲哚–CYP1A1 约 1 ns 飞出后取消，不附图充数。下图按 MD 冻结图册 <b>01–20</b> 完整纳入（含全部 <b>3D 自由能形貌</b>），图源链到 <code>08_分子动力学/结果文件/图片文件/分子动力学图_MD/</code>。</p>
"""
    ]
    n = fig_start
    for sys_id, sys_name, nums in SYSTEMS:
        parts.append(f"<h3 id='md-{sys_id}'>{sys_name}</h3>")
        parts.append(
            f"<p>{sys_name} 生产段完成 {nums['ns']} ns。"
            f"末段监控：骨架 RMSD 最大 {nums['bb']} nm，配体 RMSD 最大 {nums['lig']} nm，COM 最大 {nums['com']} nm。"
            f"下列图 册编号 01–20 均属该体系正式出图。</p>"
        )
        for nn, stem_key, title, tmpl in MD_ATLAS:
            prose = tmpl.format(sys=sys_name, **nums)
            parts.append(f"<p>图 {n} 为{sys_name}的{title}。{prose}</p>")
            src = md_src(sys_id, nn, stem_key)
            parts.append(fig(src, f"<b>图 {n}.</b> {sys_name} · {title}（图册 {nn:02d}）。"))
            n += 1
    parts.append(
        """
<div class="note">吲哚–CYP1A1 已 CANCELLED（配体 RMSD 最大 9.624 nm），不放入正文图册。自由能形貌（2D/3D）只描述采样偏好，禁止写成实验结合自由能或长期稳定结合。</div>
"""
    )
    return "\n".join(parts), n


def collage_md_panel() -> Path:
    """Method collage: RMSD + COM + 2D FEL + 3D FEL for both systems."""
    tiles = []
    for sys_id, _, _ in SYSTEMS:
        for nn, key in [(1, "骨架RMSD"), (7, "质心距离"), (13, "自由能形貌"), (17, "自由能形貌3D")]:
            tiles.append(find_md_png(sys_id, nn, key))
    imgs = [Image.open(p).convert("RGB") for p in tiles]
    # 2 rows × 4 cols
    w = max(im.width for im in imgs)
    h = max(im.height for im in imgs)
    imgs = [im.resize((w, h)) for im in imgs]
    canvas = Image.new("RGB", (w * 4, h * 2), (255, 255, 255))
    for i, im in enumerate(imgs):
        r, c = divmod(i, 4)
        canvas.paste(im, (c * w, r * h))
    out = IMG00 / "panel_08_MD.png"
    canvas.save(out)
    return out


def build_paper() -> str:
    nav = """
<p style="opacity:.85;font-size:.78rem;margin:.2rem 0 .8rem">含 MD 3D FEL 全图册</p>
<a href="#s-set">集合定义</a>
<a href="#s-flow">研究设计</a>
<a href="#s-c">三源共有靶点</a>
<a href="#s-tox">毒性分层</a>
<a href="#s-mech">机制层</a>
<a href="#s-met">候选代谢物</a>
<a href="#s-dock">分子对接</a>
<a href="#s-geo">GEO</a>
<a href="#s-md">分子动力学</a>
<a href="#s-disc">讨论边界</a>
<a href="#s-mm">材料与方法</a>
<p style="margin-top:1rem"><a href="方法版_全流程.html">→ 方法版</a></p>
"""
    parts = []
    n = 1
    parts.append(
        """
<h2 id="s-set">集合定义</h2>
<p>本文问复方是否可能经「菌群代谢物—宿主靶点」轴作用于溃疡性结肠炎（UC）。分析得到三源共有核心 <b>C</b>，再对高优先级代谢物–基因对做对接与分子动力学。只写候选与提示。</p>
<p><b>F</b> 为复方成分靶点并集，636 个基因。<b>D</b> 为 UC 疾病靶点，课题冻结 1517 个基因。<b>M</b> 为主分析证据优先代谢物靶点（敏感性另用 gutMGene 人类全库）。<b>I₁</b>=F∩D=291。<b>I₂</b>=M∩D。<b>C</b>=I₁∩I₂。</p>
"""
    )
    parts.append(
        f"""
<h2 id="s-flow">研究设计</h2>
<p>图 {n} 从左到右画整条计算链路。最左两块分别是复方侧形成的 I₁ 与代谢物侧形成的 I₂；二者相交得到终点集合 C。C 向右接到机制层、代谢物分层与分子对接；对接通过者进入分子动力学。GEO 与孟德尔随机化只提供外部或遗传支持，不改写 C 的定义。</p>
"""
        + fig(f"{IMG.as_posix()}/flow.png", f"<b>图 {n}.</b> 双交集研究设计。终点为 C，再接机制层、对接与 MD。")
    )
    n += 1

    parts.append(
        f"""
<h2 id="s-c">三源共有靶点</h2>
<p>图 {n} 用集合关系展示主分析证据优先面板在 H+M 设定下的规模：M=466，I₂=165，C=78；I₁ 与 I₂ 的 Jaccard=0.20634920634920634。超几何 p=1.5723546780171946×10⁻¹⁸。度加权与度分层置换（各 1000 次）p 均为 1.0。去掉度最高约 10% 枢纽后 C 仍为 61，超几何 p=1.8918841840435584×10⁻¹⁴。</p>
"""
        + fig(f"{IMG.as_posix()}/venn.png", f"<b>图 {n}.</b> 三源交集与置换摘要。主面板 H+M：C=78。")
    )
    n += 1

    parts.append(
        f"""
<p>图 {n} 把四种设定排成敏感性面板。主面板 H-only 时 C=20，H+M 时 C=78；全库 H-only 时 C=35，H+M 时 C=126（超几何 p=7.392372092671387×10⁻³⁵，Jaccard=0.30071599045346065）。主文以主面板 H+M（C=78）为准。</p>
"""
        + fig(f"{IMG.as_posix()}/sens.png", f"<b>图 {n}.</b> 敏感性面板。主面板与全库；H-only 与 H+M。")
    )
    n += 1

    # tox branch figures
    tox_files = [
        ("01_毒性线索_暴露物覆盖_ToxicExposureCoverage.png", "暴露物覆盖", "条/柱显示纳入毒性线索的暴露物覆盖规模，用于支线盘点而非主交集准入。"),
        ("02_毒性线索_暴露物靶点网络_ToxicExposureTargetNetwork.png", "暴露物–靶点网络", "节点为暴露物与靶点，边为线索连接；展示毒性支线的网络语境。"),
        ("03_毒性线索_方向证据热图_ToxicDirectionHeatmap.png", "方向证据热图", "颜色表示毒性/结局方向证据强弱；主面板 Tier A 排除既定有害物时对照此图。"),
    ]
    parts.append("<h2 id='s-tox'>毒性分层（支线）</h2>")
    parts.append(
        "<p>毒性分层是支线：提供暴露物–不良结局线索，不改写 C，也不作为对接/MD 准入。不良结局词表冻结为肠屏障损伤、肠道炎症、黏膜损伤/癌变风险。</p>"
    )
    for fname, title, prose in tox_files:
        src = (TOX_REL / fname).as_posix()
        parts.append(f"<p>图 {n} 为毒性分层·{title}。{prose}</p>")
        parts.append(fig(src, f"<b>图 {n}.</b> 毒性分层 · {title}。"))
        n += 1

    parts.append(
        f"""
<h2 id="s-mech">机制层</h2>
<p>在 78 个 C 基因上检索 STRING（combined score ≥ 0.9），得到 52 个节点、90 条边。图 {n} 是该 PPI：圆点为三源共有基因，连线为高置信互作。</p>
"""
        + fig(f"{IMG.as_posix()}/ppi.png", f"<b>图 {n}.</b> 主面板三源靶点 PPI。52 节点、90 边。")
    )
    n += 1

    parts.append(
        f"""
<p>图 {n} 是 MCC-like（Degree×局部三角）枢纽条形图：条越长枢纽性越高。最高四名为 IL1B、TNF、IL6、JUN。</p>
"""
        + fig(f"{IMG.as_posix()}/hub.png", f"<b>图 {n}.</b> MCC-like 枢纽条形图。最高 IL1B、TNF、IL6、JUN。")
    )
    n += 1

    # extra mechanism figs from module
    extra_mech = [
        ("08_PPI核心靶点网络_PpiHubNetwork.png", "PPI 核心靶点网络", "在枢纽排序之后单独画出核心靶点子网，节点标签突出 IL1B/TNF/IL6/JUN 等。"),
        ("07_机制层组合图_MechanismOverview.png", "机制层组合概览", "同页汇总 PPI/富集等机制层主结果，便于对照后文分图。"),
        ("04_PPI网络_全库敏感性_PpiSensitivityNetwork.png", "全库敏感性 PPI", "全库敏感性 C 上的 PPI，只作对照，不替换主面板 52 节点网络。"),
    ]
    for fname, title, prose in extra_mech:
        src = (MECH_REL / fname).as_posix()
        parts.append(f"<p>图 {n} 为{title}。{prose}</p>")
        parts.append(fig(src, f"<b>图 {n}.</b> {title}。"))
        n += 1

    parts.append(
        f"""
<p>以 D 映射后的 1499 个 Entrez 为背景，GO 显著 180 条。图 {n} 为 GO 富集：条长对应富集强度；主题含脂质反应、感染与炎症相关过程，不能写成复方特异机制定位。</p>
"""
        + fig(f"{IMG.as_posix()}/go.png", f"<b>图 {n}.</b> GO 富集。显著 180 条。")
    )
    n += 1

    parts.append(
        f"""
<p>图 {n} 为同一背景下的 KEGG 富集，显著 24 条。条长表示富集强度；只支持 C 落在 UC 常见宽泛通路集合。</p>
"""
        + fig(f"{IMG.as_posix()}/kegg.png", f"<b>图 {n}.</b> KEGG 富集。显著 24 条。")
    )
    n += 1

    parts.append(
        f"""
<p>图 {n} 是 G–M–C–T–P 五层网络摘要：各层为 Top 节点，层间边为策展/预测关系；完整边在 CSV。</p>
"""
        + fig(f"{IMG.as_posix()}/gctpm.png", f"<b>图 {n}.</b> 五层网络摘要。各层为 Top 节点。")
    )
    n += 1

    parts.append(
        """
<h2 id="s-met">候选干预代谢物</h2>
<p>对每个代谢物 m 计 n_C=|T_m∩C|。主面板 105 个代谢物中 Tier A（n_C≥1）72 个，其中 6 个带 gutMGene 实证 H 边。前列包括丁酸（14）、苯丙氨酸（13）、麦芽糖与麦芽三糖（各 9）、4-羟基苯乙酸（8）、肌苷（8）、色氨酸（8）、吲哚-3-乙酸（8）。72 个主面板 Tier A 的 GMMAD2 UC FDR 均 &lt;0.05，方向均为 Increase：只提示疾病中升高且与复方汇入同一靶点集合，不能推断复方使其下降。</p>
"""
    )

    parts.append(
        f"""
<h2 id="s-dock">分子对接</h2>
<p>从高优先级代谢物–基因对取 9 对正式对接，Vina，每对 3 种子，阈值 −20.9 kJ/mol。图 {n} 热图颜色为三轮均值亲和力（kJ/mol，越负越强）。最强三格：色氨酸–MMP9（4H3X）−37.26333333333333 ± 0.09504384952921963；吲哚–CYP1A1（4I8V）−29.69 ± 0.0；腺苷–ADA（3IAR）−27.56 ± 0.05567764362829951。另通过：苯丙氨酸–PPARG −26.343333333333334、精氨酸–NOS3 −26.076666666666668、色氨酸–MPO −22.366666666666664、4-羟基苯乙酸–CA2 −22.02333333333333。未通过：吲哚-3-乙酸–ACHE −19.786666666666665、丁酸–PPARG −16.46。</p>
"""
        + fig(f"{IMG.as_posix()}/dock.png", f"<b>图 {n}.</b> 对接亲和力热图。")
    )
    n += 1

    parts.append("<h2 id='s-geo'>GEO 外部一致性</h2>")
    parts.append(
        f"""
<p>图 {n} 是 GSE92415（GPL13158）火山图：横轴为 UC（n=87）相对 Healthy（n=21）的 logFC，纵轴 −log₁₀(P)。该队列同时用于后续 panel 定向，故其 AUC 有乐观偏倚。</p>
"""
        + fig(f"{IMG.as_posix()}/geo_volc1.png", f"<b>图 {n}.</b> GSE92415 火山图。UC 87 vs Healthy 21。")
    )
    n += 1
    parts.append(
        f"""
<p>图 {n} 是 GSE75214（GPL6244）火山图，坐标含义相同；活动期 UC（n=74）对正常（n=11）。主面板 C 映射 76 与 74 个基因；两队列方向一致 63 个；两队列均 FDR&lt;0.05 且方向一致 43 个。</p>
"""
        + fig(f"{IMG.as_posix()}/geo_volc2.png", f"<b>图 {n}.</b> GSE75214 火山图。活动期 UC 74 vs 正常 11。")
    )
    n += 1
    parts.append(
        f"""
<p>图 {n} 为核心基因热图：行是基因、列是样本，颜色为相对表达；疾病与对照色块可分。</p>
"""
        + fig(f"{IMG.as_posix()}/geo_heat.png", f"<b>图 {n}.</b> 核心基因热图。")
    )
    n += 1
    parts.append(
        f"""
<p>图 {n} 为 AUC 森林图：GSE92415 的 AUC=0.995（95% CI 0.987–1.000），GSE75214 的 AUC=0.993（95% CI 0.980–1.000）。这是疾病/对照分离，不是疗效。</p>
"""
        + fig(f"{IMG.as_posix()}/geo_auc.png", f"<b>图 {n}.</b> AUC 森林图。0.995 与 0.993。")
    )
    n += 1

    md_html, n = build_md_section(n)
    parts.append(md_html)

    parts.append(
        """
<h2 id="s-disc">讨论边界</h2>
<div class="take"><b>支持写到：</b>主面板 H+M 下 C=78；Tier A 72；对接 Top3 为结合候选；MMP9 与 ADA_A2 在监控内完成 100 ns，并具备完整 01–20 图册（含 3D FEL）；GEO 方向一致与高 AUC。</div>
<div class="note"><b>不支持写到：</b>疗效；复方降低代谢物；对接分=实验 Kd；FEL/MD=结合自由能；CYP 稳定；复方特异通路已定位。</div>
<h2 id="s-mm">材料与方法（短）</h2>
<p>库名、版本、原始/处理后路径、清洗原因、脚本与停机见方法版 01–08。锁定口径：D=1517；M=H∪(SEA∩STP)；STRING≥0.9；Vina 阈值 −20.9 kJ/mol；MD NS=100；SEA=ChEMBL 27。MD 出图遵循冻结图册 01–20（含 3D FEL）。</p>
"""
    )
    return shell(
        "论文版 · 努力学习全项目",
        nav,
        "\n".join(parts),
        f"论文版 · 含 MD 图册 01–20（3D FEL）· 末图号约 {n-1} · 2026-10-11",
    )


def patch_method_panel_note() -> None:
    """Refresh method HTML panel_08 caption + ensure eight-item MD mentions 3D atlas."""
    path = OUT / "方法版_全流程.html"
    t = path.read_text(encoding="utf-8")
    # update panel_08 caption if present
    t2 = re.sub(
        r"(panel_08_MD\.png'[^>]*>\s*<figcaption>)(.*?)(</figcaption>)",
        r"\1<b>方法拼图 08：</b> 每体系 RMSD、COM、FEL 2D 与 <b>FEL 3D</b>（上行 MMP9，下行 ADA_A2）。完整 01–20 细读在论文版。\3",
        t,
        count=1,
        flags=re.S,
    )
    if "FEL 3D" not in t2 or "17–20" not in t2:
        t2 = t2.replace(
            "验收：<code>报告_正式MD_100ns.md</code> 与 DONE；CYP 为 CANCELLED 书面记录。",
            "验收：<code>报告_正式MD_100ns.md</code> 与 DONE；CYP 为 CANCELLED 书面记录。"
            "论文版必须链入该体系图册 01–20（含 3D 自由能形貌 17–20），不得只贴 RMSD/COM。",
        )
    path.write_text(t2, encoding="utf-8")


def verify(html: Path) -> None:
    t = html.read_text(encoding="utf-8")
    srcs = re.findall(r"src='([^']+)'", t)
    bad = [s for s in srcs if not (html.parent / s).resolve().exists()]
    if bad:
        raise SystemExit(f"missing {len(bad)}: {bad[:8]}")
    if "自由能形貌3D" not in t and "FEL 3D" not in t:
        raise SystemExit("no 3D FEL mention")
    # count 3D img
    n3d = sum(1 for s in srcs if "3D" in s or "3d" in s)
    if n3d < 8:
        raise SystemExit(f"expected >=8 3D figs, got {n3d}")
    print(html.name, "OK figs=", len(srcs), "3d=", n3d)


def main() -> None:
    # ensure all atlas files exist before writing
    for sys_id, _, _ in SYSTEMS:
        for nn, stem_key, _, _ in MD_ATLAS:
            p = find_md_png(sys_id, nn, stem_key)
            print("ok", sys_id, nn, p.name)

    collage_md_panel()
    paper = OUT / "论文版_全流程.html"
    paper.write_text(build_paper(), encoding="utf-8")
    patch_method_panel_note()
    verify(paper)

    if DELIV:
        d_rep = DELIV / "00_全流程报告" / "结果文件" / "报告文件"
        d_img = DELIV / "00_全流程报告" / "结果文件" / "图片文件"
        d_rep.mkdir(parents=True, exist_ok=True)
        d_img.mkdir(parents=True, exist_ok=True)
        shutil.copy2(paper, d_rep / paper.name)
        shutil.copy2(OUT / "方法版_全流程.html", d_rep / "方法版_全流程.html")
        shutil.copy2(IMG00 / "panel_08_MD.png", d_img / "panel_08_MD.png")
        verify(d_rep / paper.name)
        print("synced", d_rep)


if __name__ == "__main__":
    main()
