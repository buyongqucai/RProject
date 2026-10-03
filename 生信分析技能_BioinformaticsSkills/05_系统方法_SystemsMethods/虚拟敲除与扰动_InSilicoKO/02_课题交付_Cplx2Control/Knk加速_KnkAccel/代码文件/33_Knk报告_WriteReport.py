"""Two HTML reports for the current scTenifoldKnk 1.4.3 GPU run."""

from pathlib import Path

ROOT = Path(r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件")
REPORT = ROOT / "报告_1.4.3"
SUBTYPES = ("PEP", "NF1")
TARGETS = ("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")
CONTROLS = {"PEP": "Ret", "NF1": "Rdx"}

CSS = """<style>
body{font-family:Georgia,serif;max-width:920px;margin:36px auto;line-height:1.7;color:#222;padding:0 18px}
h1{font-size:24px;line-height:1.35} h2{font-size:20px;margin-top:32px}
table{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0 20px}
th,td{border-bottom:1px solid #ccc;text-align:left;padding:6px 8px}
p{margin:10px 0 12px}
</style>"""


def responsive_count(subtype: str, gene: str) -> tuple[int, str]:
    folder = ROOT / subtype / "scTenifoldKnk" / gene
    if (folder / "说明_无出边.txt").exists():
        return 0, "无出边"
    path = folder / "响应基因_Responsive.csv"
    if not path.exists():
        return 0, "无表"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()[1:] if line.strip()]
    return len(lines), "FDR<0.05"


def table_rows() -> str:
    rows = []
    for subtype in SUBTYPES:
        genes = list(TARGETS) + [CONTROLS[subtype]]
        for gene in genes:
            count, note = responsive_count(subtype, gene)
            role = "对照" if gene == CONTROLS[subtype] else "靶基因"
            rows.append(f"<tr><td>{subtype}</td><td>{gene}</td><td>{role}</td><td>{count}</td><td>{note}</td></tr>")
    return "\n".join(rows)


def write(name: str, title: str, body: str) -> None:
    REPORT.mkdir(parents=True, exist_ok=True)
    html = (
        f"<!DOCTYPE html><html lang='zh'><head><meta charset='utf-8'><title>{title}</title>{CSS}</head>"
        f"<body><h1>{title}</h1>{body}</body></html>"
    )
    (REPORT / name).write_text(html, encoding="utf-8")
    print(REPORT / name)


def main() -> None:
    rows = table_rows()
    methods = f"""
<h2>1. 这份报告在回答什么</h2>
<p>在 GSE197289 小鼠 Control 的 PEP 和 NF1 里，用 scTenifoldKnk 1.4.3 逐个虚拟敲除 Mitf、Bace2、Cplx2、Ppp1r26、Slc28a3、Sh3d21，并各加一个与 Cplx2 绝对相关最低的对照基因。这是计算预测，不是慢性三叉神经痛模型，也不是湿实验敲除的差异基因。</p>
<h2>2. 方法</h2>
<p>细胞取 <code>model == Control</code>。不设 8000 基因上限。质控用官网 <code>scQC</code>：文库大于 1000、线粒体比例低于 0.1、检出比例高于 5%。六个靶基因只要检出细胞数大于 0 就加回矩阵。每个亚群只建一次野生型网：10 张网、每张 500 个细胞、3 个主成分、分位数 0.9、张量秩 3、种子 1。建网和张量在 GPU 上完成，公式是 1.4.3 的 Gram 加 secular，张量是稀疏 CP。敲除是把该基因的出边置 0，再做 2 维流形对齐和卡方检验，Benjamini-Hochberg 校正。富集预定为 GO 与 KEGG，图用网药的气泡、柱状和棒棒糖。通过线是校正 P 小于 0.05、q 小于 0.2。</p>
<p>质控后 PEP 是 9477 个基因、677 个细胞，对照基因是 Ret。NF1 是 7607 个基因、1084 个细胞，对照基因是 Rdx。CPU 上的仓库 pcNet 已用 12 个核并行写在 <code>scTenifoldKnk_CPU/_野生型</code>，这一份报告的扰动表来自 GPU 野生型网。</p>
<h2>3. 结果</h2>
<table><tr><th>亚群</th><th>基因</th><th>角色</th><th>其他响应基因</th><th>说明</th></tr>
{rows}
</table>
<p>PEP 的 Mitf、Ppp1r26、Sh3d21 在收到 3 位小数的野生型网里出边全是 0。把已经是 0 的一行再置 0，网络不变。此时检验仍报出 167 个基因，三份名单完全相同，是全零距离上的数值噪声。这三份名单和它们的 GO 气泡已移到各基因目录的 <code>_未采用_无出边</code>，不进入结论。</p>
<p>PEP 里有出边的 Bace2、Cplx2、Slc28a3 和对照 Ret，其他基因的 FDR 都没有低于 0.05。NF1 的七次敲除各自都只有 Actg1 和 Ywhag 通过 FDR。这两个基因在每一次敲除里都出现，包括对照 Rdx，所以不能写成某一个靶基因特异的响应。GO 没有条目通过校正。KEGG 表只有表头，没有通路通过校正，因此没有可绘制的网药富集图。</p>
<h2>4. 不能写出的结论</h2>
<p>不能把这份名单写成三叉神经痛机制已经证实。不能把无出边基因的 167 个噪声基因写成通路。不能把 NF1 上每次都出现的 Actg1 和 Ywhag 写成 Cplx2 或其余靶基因的特异下游。</p>
"""
    paper = f"""
<h2>摘要</h2>
<p>目的：在正常小鼠三叉神经节的 PEP 与 NF1 中，预测六个候选基因被虚拟敲除后的响应基因。方法：GSE197289 Control，scTenifoldKnk 1.4.3，GPU 建网与稀疏张量，参数用官网默认，不设 8000 基因上限。每个亚群另敲一个低相关对照。结果：PEP 中有出边的敲除没有其他 FDR 低于 0.05 的基因；三个无出边基因的显著名单是数值噪声，已弃用。NF1 中七次敲除共同得到 Actg1 和 Ywhag，对照 Rdx 也得到这两个基因。结论：这些是正常三叉神经节上的计算预测，当前没有可以单独归给某一个靶基因的通路。</p>
<h2>1. 引言</h2>
<p>亚群按 CGRP 与 NF200 对应的作者注释留在 PEP 和 NF1。数据是偏头痛图谱中的 Naive/Control，不是 IoN-CCI，也不是慢性三叉神经痛。</p>
<h2>2. 方法</h2>
<p>一次只敲一个基因。野生型网不随基因重算。富集只在 FDR 低于 0.05 的其他基因上做。没有出边的基因不进入富集。</p>
<h2>3. 结果</h2>
<table><tr><th>亚群</th><th>基因</th><th>角色</th><th>其他响应基因</th><th>说明</th></tr>
{rows}
</table>
<p>网药样式的 GO 气泡只在被弃用的无出边名单上生成过，没有放进本报告。有效敲除没有通过校正的 GO 或 KEGG 条目。</p>
<h2>4. 讨论</h2>
<p>对照与靶基因在 NF1 上给出同一对基因，说明这张网对“去掉一行”的响应不特异。PEP 上高检出的 Cplx2 也没有带出其他显著基因。阴性结果保留。单核样本不能写成每只鼠的独立重复。</p>
"""
    write("Knk_报告_原理方法与数据分析.html", "scTenifoldKnk 1.4.3 的原理、方法与数据分析", methods)
    write("Knk_报告_论文式阐述.html", "正常小鼠三叉神经节 PEP 与 NF1 中六个候选基因的 scTenifoldKnk 虚拟敲除", paper)


if __name__ == "__main__":
    main()
