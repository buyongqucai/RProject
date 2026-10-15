# 三套已完成体系串行绘图：等各自 CSV 落地 → 逐个起 Origin（不并发，避免 .opju 冲突）
$root = "E:\Origin_Data"
$script = "E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery\分子动力学模拟_MolecularDynamics\脚本_scripts\origin出图_plotMdOrigin.py"
$log = "E:\Origin_Data\_plot_all_done.log"
$systems = @("FOS_quercetin_1A02", "ADA_Adenosine_7RTG_A2", "MMP9_Tryptophan_4H3X")
foreach ($sys in $systems) {
    $proj = Join-Path $root $sys
    $marker = Join-Path $proj "FEL_LigandProteinRmsd_kJmol.csv"
    $deadline = (Get-Date).AddHours(4)
    while (-not (Test-Path $marker) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 20 }
    if (-not (Test-Path $marker)) { "TIMEOUT $sys" | Add-Content $log; continue }
    Start-Sleep -Seconds 30
    "== PLOT $sys $(Get-Date -Format s) ==" | Add-Content $log
    python $script --data-dir $proj *>> $log
    "exit=$LASTEXITCODE $sys $(Get-Date -Format s)" | Add-Content $log
}
"ALL_PLOT_DONE $(Get-Date -Format s)" | Add-Content $log
