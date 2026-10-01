# 网络毒理学数据库可抓取登记（SSOT）

> **地位：** 网络毒理学技能的库清单与取数方式唯一正文。改「能否程序化取数」只改本文件。  
> **调研日：** 2026-09-27。站点策略会变，复用前再探一次。  
> **硬规则：** 只用公开 API、官方批量包、或浏览器人工导出。**不写**绕过验证码、伪造会话、突破频率限制的抓取器。缺数据标 `BLOCKED_EXTERNAL`，不编造化学–基因边。

## 取数档

| 档 | 含义 |
|----|------|
| **AUTO_API** | 文档化 REST/GraphQL；本机可直接请求（遵守频率） |
| **AUTO_BULK** | 官方压缩包/Figshare；脚本只读用户已下载的本地文件 |
| **KEY** | 免费注册密钥后可程序化 |
| **MANUAL** | 浏览器检索/导出；验证码或无稳定 API |
| **PREDICT** | 在线预测工具，不是策展关联库；不可当成实测毒性证据 |

## 登记表

| 库 | 网络毒理学角色 | 档 | 入口与方法 | 备注 |
|----|----------------|----|------------|------|
| **PubChem** | CID、SMILES、同义词、部分毒性测定 | AUTO_API | [PUG-REST](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest)，建议 ≤5 次/秒。例：`/rest/pug/compound/name/{name}/property/CanonicalSMILES,CID/JSON` | 化学身份枢纽；本机探测见文末 |
| **ChEMBL** | 化合物–靶点活性 | AUTO_API | [ChEMBL REST](https://www.ebi.ac.uk/chembl/api/data) | 活性≠毒性结论 |
| **Open Targets** | 靶点–疾病 | AUTO_API | GraphQL `https://api.platform.opentargets.org/api/v4/graphql` | 疾病侧可补 CTD；网药已用过同类接口 |
| **DGIdb** | 药/化合物–基因 | AUTO_API | `https://dgidb.org/api/graphql` | 治疗向互作，毒理边需另标来源 |
| **STITCH** | 化学–蛋白网络 | AUTO_BULK | [STITCH download](http://stitch.embl.de/) | 大表本地读；网页不宜当爬虫 |
| **AOP-Wiki** | 不良结局通路（MIE–KE–AO） | AUTO_BULK + 社区 API | 官网 XML；社区 REST 见 [VHP4Safety 教程](https://docs.vhp4safety.nl/en/latest/tutorials/aopwikiapi/aopwikiapi.html)（`aopwiki-api.cloud.vhp4safety.nl`） | 机制叙事层，不是剂量–反应 |
| **CompTox / DSSTox / ToxVal / ToxCast** | 危害值、体外 HTS | KEY + AUTO_BULK | [CTX API](https://www.epa.gov/comptox-tools/computational-toxicology-and-exposure-apis) 邮件申请免费 key（`ccte_api@epa.gov`）；[可下载数据包](https://www.epa.gov/comptox-tools/downloadable-computational-toxicology-data)；invitrodb 见 [ToxCast](https://www.epa.gov/comptox-tools/exploring-toxcast-data)（`tcpl`） | 公有领域数据；无 key 时用批量包 |
| **CTD** | 化学–基因、化学–疾病、化学–表型（核心） | MANUAL + AUTO_BULK（许可后） | 月度文件 `https://ctdbase.org/downloads/`（如 `CTD_chem_gene_ixns`）。非商业免费，**商业须买许可**（[2025 更新](https://pmc.ncbi.nlm.nih.gov/articles/PMC11701581/)）。`batchQuery.go` 现有人机验证，**禁止脚本打批量查询**。RENCI Automat 镜像已停 | 本地包 + `ctdR` 一类工具只读用户下载文件 |
| **gutMGene v2** | 菌群–代谢物–宿主基因 | MANUAL | 现用 [https://bio-computing.hrbmu.edu.cn/gutmgene/](https://bio-computing.hrbmu.edu.cn/gutmgene/)（Browse/Resource 导出）。旧址 `bio-annotation.cn/gutmgene` 本机 502 | 肠–器官轴网络毒理/网药交叉；策展关联≠实测组学 |
| **T3DB** | 毒素–靶点 | MANUAL | [http://www.t3db.ca/](http://www.t3db.ca/) 检索/下载页 | Wishart 库；无稳定公开写库 API 时走导出 |
| **SwissTargetPrediction** | 结构预测靶点 | MANUAL / 可达时表单 | 与网药相同：`locate→predict→result`；失败则手工 | 预测靶点必须与 CTD 策展边分开标注 |
| **SEA** | 相似性预测靶点 | MANUAL | [https://sea.bkslab.org/](https://sea.bkslab.org/) | 同上，预测层 |
| **GeneCards / OMIM / TTD 等** | 疾病或器官毒性基因 | MANUAL | 与网药疾病六库相同，英文病名/表型导出 | 不爬登录墙 |
| **DisGeNET** | 疾病–基因 | KEY | 学术申请 API/批量 | 无许可不抓 |
| **KEGG / STRING** | 通路、PPI | AUTO_API | 沿用网药：KEGG REST、STRING API | KEGG 批量图遵守其条款 |
| **ProTox / ADMETlab** | 毒性类别、ADMET 预测 | PREDICT | 网页提交 | 只作补充预测，不写入「策展互作」表 |
| **OECD QSAR Toolbox** | 法规分组/谱图 | 桌面软件 | 非网站抓取 | 本技能不封装 |

## 推荐最小可复现组合

1. **身份：** PubChem AUTO_API → SMILES/CID  
2. **策展毒理边：** CTD 本地月度包（用户浏览器下好）  
3. **预测靶点（可选）：** STP/SEA，单独一列 `evidence=predicted`  
4. **疾病/器官基因：** 网药同款手工库，或 Open Targets AUTO_API  
5. **机制：** AOP-Wiki 批量或社区 API  
6. **菌群代谢物轴（可选）：** gutMGene 手工表  
7. **对接：** 交给分子对接技能；结论写「结合提示」

## 本机连通（2026-09-27，`probe2.py`）

| 探测 | 结果 | 解读 |
|------|------|------|
| gutMGene 首页 | HTTP 200 | 站点可开；全表仍走页面导出 |
| STITCH 首页 | HTTP 200 | 下载页可开 |
| PubChem PUG-REST（aspirin CID） | HTTP 503 ServerBusy | 接口在，当次忙；稍后重试，不改档位 |
| AOP 社区 `get-all-aops` | HTTP 500 | 社区 API 不稳定；优先官网 XML 批量包 |
| ChEMBL / Open Targets | TLS 中断 | 本机当次握手失败，不否定其公开 API |

探测脚本留在 `.scratch/网络毒理学技能_NetworkToxicology/scripts/probe2.py`。失败只记连通，不降级为「库不存在」。
