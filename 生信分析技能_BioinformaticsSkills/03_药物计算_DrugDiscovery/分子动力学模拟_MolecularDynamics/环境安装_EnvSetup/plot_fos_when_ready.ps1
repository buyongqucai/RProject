# FOS 图册：等 Origin CSV 导出完成后自动起 origin出图_plotMdOrigin.py
$proj = "E:\Origin_Data\FOS_quercetin_1A02"
$marker = Join-Path $proj "FEL_LigandProteinRmsd_kJmol.csv"
$script = "E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery\分子动力学模拟_MolecularDynamics\脚本_scripts\origin出图_plotMdOrigin.py"
$log = "E:\Origin_Data\FOS_quercetin_1A02_origin_plot.log"
$deadline = (Get-Date).AddHours(2)
while (-not (Test-Path $marker) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 20 }
if (-not (Test-Path $marker)) { "TIMEOUT waiting for $marker" | Out-File $log -Encoding utf8; exit 1 }
Start-Sleep -Seconds 30  # 让导出收尾写完剩余 CSV
"marker found $(Get-Date -Format s); start Origin plotting" | Out-File $log -Encoding utf8
python $script --data-dir $proj *>> $log
"plot exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $log
