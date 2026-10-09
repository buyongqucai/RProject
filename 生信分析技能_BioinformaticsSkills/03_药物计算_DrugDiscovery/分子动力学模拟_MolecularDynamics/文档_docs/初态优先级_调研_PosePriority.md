# 初态优先级调研（共晶 vs 对接）

> 日期：2026-10-09。回答：合格共晶是否优先于对接姿态做 MD 初态；对接是否只用来判断「有没有模拟潜力」。  
> 执行口径见 SOP §9.0.1。本页只记出处，不把未覆盖的句子写成已定规则。

## 已由文献/官方材料支持的

1. **目标配体自己的实验复合物坐标，是该配体 MD 的标准起点。**  
   GROMACS 蛋白–配体教程从晶体复合物 PDB 3HTB 取 JZ4 坐标建体系，不从对接姿态建体系。平衡阶段对蛋白重原子做位置限制，用来放松溶剂，晶体复合物同样如此。  
   出处：Justin A. Lemkul, Protein–Ligand Complex, <http://www.mdtutorials.com/gmx/complex/01_pdb2gmx.html>；GROMACS 官方入门教程对位置限制的说明，<https://tutorials.gromacs.org/docs/md-intro-tutorial.html>。

2. **已有结构数据时，不要用对接最高分替代实验位姿。**  
   自对接（配体放回自己的晶体）时，最高分也不总是 RMSD ≤ 2 Å 的实验朝向。交叉对接（放进别的配体的晶体）更差。作者建议用打分，并加上类似物的结构标准，而不是只取最高分。  
   出处：Ramírez D., Caballero J. *Molecules* 2018, 23, 1038. <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6102569/>。

3. **无参照的交叉对接，顶部分姿态经常对不上晶体；用已有共晶配体引导后明显提高。**  
   Cleves 与 Jain 综述：交叉对接成功率常见约 20–30%。他们用截日前已知的共晶配体引导搜索和排序，在 10 个靶点、949 个配体上，最高分姿态族正确率超过 60%，前两族约 75%。  
   出处：Cleves A.E., Jain A.N. *J. Comput.-Aided Mol. Des.* 2015, 29, 485–509. <https://europepmc.org/article/pmc/4464052>。  
   同文转述的更早交叉对接：Sutherland 等全交叉对接约 18–24%；Verdonk 等在 Astex 多样集上，仅因蛋白构象从共晶换成非共晶，成功率约从 80% 降到 61%。

4. **没有目标配体晶体时，用对接姿态做 MD 是文献和论坛里的常规做法，不是被禁止的。**  
   Guterres 与 Im 用 AutoDock Vina 姿态做高通量 MD，在 DUD-E 子集上把 ROC AUC 从 0.68 提到 0.83，用来区分活性与诱饵，不是用来证明姿态等于晶体。  
   出处：Guterres H., Im W. *J. Chem. Inf. Model.* 2020, 60, 2189–2198. <https://pmc.ncbi.nlm.nih.gov/articles/PMC7534544/>。  
   对接与 MD 的关系综述把对接作为提出结合模式、MD 作为后续采样，而不是「对接只做资格筛选、不做初态」。  
   出处：Salmaso V., Moro S. *Front. Pharmacol.* 2018, 9, 923. <https://pmc.ncbi.nlm.nih.gov/articles/PMC6113859/>。  
   GROMACS 论坛里，Lemkul 对「Vina 对接复合物怎么做 MD」的回复是指向上述晶体教程的搭建步骤；另一帖在配体根本不在活性位点时要求先改成合理复合物再模拟。论坛接受对接复合物作为输入，条件是坐标确实在位点里。  
   出处：<https://gromacs.bioexcel.eu/t/how-to-run-md-simulation-of-a-docked-protein-ligand-complex-using-autodock-vina-using-gromacs/3027>；<https://gromacs.bioexcel.eu/t/what-is-wrong-with-my-complex/551>。

## 文献明确不支持的

1. **「以后一律共晶，没有共晶就不做 MD。」**  
   新配体多数没有自己的晶体。上面第 4 条把对接初态 MD 当作正式计算，不是临时凑合。

2. **「对接分用来判断有没有模拟潜力。」**  
   最高分经常不是实验朝向（Ramírez & Caballero 2018）。约 30 ns 的轨迹稳定也不能区分对接姿态对不对：错误姿态也可以在动力学上很稳；MD 精修没有把姿态显著拉近实验，约半数相对实验的 RMSD 反而变大；从错误姿态出发也没有采样到实验结构。从实验姿态出发的对照轨迹里，多数配体留在实验结构附近。  
   出处：Bhakat S., Åberg E., Söderhjelm P. *J. Comput.-Aided Mol. Des.* 2018（在线 2017-10-20），DOI 10.1007/s10822-017-0074-x，<https://link.springer.com/article/10.1007/s10822-017-0074-x>。  
   平衡 MD 可以滤掉一部分诱饵姿态，但滤不干净：五次平行里「任一次稳定就算稳定」时，约 95% 的正确姿态保留，诱饵只排除约 25–44%。  
   出处：*J. Chem. Inf. Model.* 2017, 57, 2514，「Exploring the Stability of Ligand Binding Modes to Proteins by Molecular Dynamics Simulations: A Cross-docking Study」。<https://pubs.acs.org/jcisd8/article/57/10/2514/849207/Exploring-the-Stability-of-Ligand-Binding-Modes-to>。

3. **「近缘共晶只要把原子换上就可以，完全不要对接。」**  
   被测过的做法是用已知共晶配体**引导**对接和排序（Cleves & Jain），不是原子替换后跳过一切搜索。骨架极近时叠合是化学上的保守操作，但这次调研没有找到官方文档把它写成唯一标准。

## 因此 SOP 只敲定这三句

- 有目标配体的合格实验复合物 → MD 用这份坐标，不用对接最高分替换。  
- 没有这份复合物、但有同口袋近缘共晶 → 用近缘姿态作参照（引导对接或极近骨架叠合），不用空口袋盲对接。  
- 两样都没有 → 可以用对接姿态做 MD，结论写成对接初态。对接分和短轨迹「还在口袋」都不单独作为「值得开长轨迹 / 姿态正确」的证据。
