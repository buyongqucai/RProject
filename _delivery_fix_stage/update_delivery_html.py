from bs4 import BeautifulSoup
from pathlib import Path
import json
root=Path(r'E:\RProject\_delivery_fix_stage\交付文件')
html_path=root/'图注与解读说明.html'
soup=BeautifulSoup(html_path.read_text(encoding='utf-8'),'html.parser')

def card(href, img, title, stat, meaning, how, bio):
    return f'''
<article class="card">
  <div class="card-media"><a class="thumb" href="{href}" target="_blank" rel="noopener"><img src="{img}" alt="{title}" loading="lazy" /></a></div>
  <div class="card-body">
    <h3>{title}</h3>
    <p class="statline">{stat}</p>
    <p><span class="tag">含义</span>{meaning}</p>
    <p><span class="tag how">怎么看</span>{how}</p>
    <p><span class="tag bio">生物学意义</span>{bio}</p>
    <p class="links"><a href="{href}" target="_blank">PNG</a> · <a href="{href[:-4]}.svg" target="_blank">SVG</a></p>
  </div>
</article>'''

kegg_card=card('图片/富集分析/KEGG富集气泡图_Top30.png','图片/富集分析/KEGG富集气泡图_Top30.png','KEGG 富集气泡图（Top30）','完整显著通路表 n=183 · 展示 Top30','KEGG 通路富集气泡图','通路名已换行；点大小=基因数，颜色=-log10(Padj)，坐标与边距完整显示。','优先关注 IL-17、TNF、TLR、PI3K-Akt 等与 UC/炎症相关通路；其余感染/肿瘤通路视为共享炎症模块。')
old_kegg=soup.find('a',href='图片/富集分析/KEGG棒棒糖图.png')
if old_kegg:
    old_article=old_kegg.find_parent('article')
    old_article.insert_before(BeautifulSoup(kegg_card,'html.parser'))

ppi_card=card('图片/PPI/Top20_PPI核心网络.png','图片/PPI/Top20_PPI核心网络.png','Top20 PPI 核心网络','Top20 hubs · 99 条诱导子网络边','Degree 最高的 20 个蛋白及相互作用','3 环同心布局；节点大小和颜色=Degree，所有标签完整显示。','用于论文主图讨论 TNF/IL6/STAT3/AKT1/NFKB1 等核心炎症枢纽。')
old_ppi=soup.find('a',href='图片/PPI/PPI渐变图.png')
if old_ppi:
    old_article=old_ppi.find_parent('article')
    old_article.insert_before(BeautifulSoup(ppi_card,'html.parser'))

html_path.write_text(str(soup),encoding='utf-8')

md=root/'报告'/'图注与解读说明.md'
text=md.read_text(encoding='utf-8')
text=text.replace('## 4. 网络与 PPI', '''## 4. 网络与 PPI

### Top20 PPI 核心网络（修正版）
Top20 PPI 核心网络使用 Degree 最高的 20 个蛋白构建诱导子网络，采用 3 环同心布局，节点大小与颜色映射 Degree，全部标签完整显示。文件：`图片/PPI/Top20_PPI核心网络.png/svg`。''')
text=text.replace('## 3. 富集分析', '''## 3. 富集分析

### KEGG 富集气泡图 Top30（修正版）
修正版 KEGG 气泡图展示显著通路 Top30，长通路名换行，扩大画布和坐标边距，避免标签/点被裁切。完整结果见 `数据/富集分析/KEGG.csv`（183 条）。文件：`图片/富集分析/KEGG富集气泡图_Top30.png/svg`。''')
md.write_text(text,encoding='utf-8')

stats_path=root/'报告'/'_stats.json'
stats=json.loads(stats_path.read_text(encoding='utf-8'))
stats.update({'n_kegg_top30_display':30,'n_ppi_top20_nodes':20,'n_ppi_top20_edges':99,'figure_fix':'KEGG Top30 complete labels; PPI concentric degree; Top20 hub network'})
stats_path.write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
print('updated_html_md_stats')

