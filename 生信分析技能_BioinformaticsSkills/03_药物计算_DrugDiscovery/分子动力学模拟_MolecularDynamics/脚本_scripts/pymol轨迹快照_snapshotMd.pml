# PyMOL: trajectory snapshots start/mid/end for 3HTB/JZ4
reinitialize
bg_color white
cd E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/01_样例_sample/工作文件_MdWork/3HTB/10_轨迹快照_Snapshots

load 轨迹快照始干_SnapshotStartDry.pdb, start
load 轨迹快照中干_SnapshotMidDry.pdb, mid
load 轨迹快照末干_SnapshotEndDry.pdb, end

hide everything
show cartoon, polymer
show sticks, resn JZ4
color marine, polymer and start
color gray70, polymer and mid
color salmon, polymer and end
color yellow, resn JZ4
set cartoon_fancy_helices, 1
set stick_radius, 0.18
orient polymer
zoom polymer, 2

# panel montage: three states side by side
disable mid
disable end
enable start
png E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/01_样例_sample/代码文件/结果文件/25_轨迹快照图/25_轨迹快照始_SnapshotStart.png, dpi=600, ray=1, width=1600, height=1200

disable start
enable mid
png E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/01_样例_sample/代码文件/结果文件/25_轨迹快照图/25_轨迹快照中_SnapshotMid.png, dpi=600, ray=1, width=1600, height=1200

disable mid
enable end
png E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/01_样例_sample/代码文件/结果文件/25_轨迹快照图/25_轨迹快照末_SnapshotEnd.png, dpi=600, ray=1, width=1600, height=1200

# combined view all three
enable start
enable mid
enable end
# offset mid/end along X for comparison
translate [40,0,0], mid
translate [80,0,0], end
orient
zoom complete=1
png E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/01_样例_sample/代码文件/结果文件/25_轨迹快照图/25_轨迹快照拼图_TrajectorySnapshots.png, dpi=600, ray=1, width=2400, height=900
quit
