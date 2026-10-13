import os
import shutil
src_root = r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO"
dst = r"E:\RProject\生信分析技能_BioinformaticsSkills\05_系统方法_SystemsMethods\虚拟敲除与扰动_InSilicoKO\02_课题交付_Cplx2Control"
for sub in ("代码文件", "结果文件/图片文件", "结果文件/数据文件", "结果文件/报告文件"):
    os.makedirs(os.path.join(dst, sub.replace("/", os.sep)), exist_ok=True)

code_src = os.path.join(src_root, "代码文件")
for n in os.listdir(code_src):
    if n.endswith(".R"):
        shutil.copy2(os.path.join(code_src, n), os.path.join(dst, "代码文件", n))

fig_src = os.path.join(src_root, "结果文件", "图片文件")
for n in os.listdir(fig_src):
    if not n.endswith(".png"):
        continue
    if n.startswith("06_"):
        continue
    shutil.copy2(os.path.join(fig_src, n), os.path.join(dst, "结果文件", "图片文件", n))

keep_csv = (
    "03_检出率_对照五亚群_Cplx2DetectionControl.csv",
    "04_扰动基因_五亚群_Cplx2DrAll.csv",
    "08_GSEA_突触条目_SynapseGsea.csv",
    "08_边权与距离_EdgeWeightDistance.csv",
)
tab_src = os.path.join(src_root, "结果文件", "数据文件")
for n in keep_csv:
    p = os.path.join(tab_src, n)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(dst, "结果文件", "数据文件", n))

shutil.copy2(
    os.path.join(src_root, "结果文件", "报告文件", "虚拟敲除说明_Report.html"),
    os.path.join(dst, "结果文件", "报告文件", "虚拟敲除说明_Report.html"),
)
print("copied")
