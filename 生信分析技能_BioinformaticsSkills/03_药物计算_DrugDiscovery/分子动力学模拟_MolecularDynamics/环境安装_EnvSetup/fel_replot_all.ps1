# Re-render 8 FEL figures per system (ASCII-only source; resolve plot script at runtime)
$plot = (Get-ChildItem "E:\RProject" -Recurse -Filter "origin*plotMdOrigin.py" | Select-Object -First 1).FullName
$stems = "FreeEnergyLandscape,FreeEnergyLandscape3D,FreeEnergyRmsdCom,FreeEnergyRmsdCom3D,FreeEnergyRmsdSasa,FreeEnergyRmsdSasa3D,FreeEnergyLigandProteinRmsd,FreeEnergyLigandProteinRmsd3D"
$log = "E:\Origin_Data\_fel_replot.log"
foreach ($sys in @("FOS_quercetin_1A02", "ADA_Adenosine_7RTG_A2", "MMP9_Tryptophan_4H3X")) {
    "== FEL REPLOT $sys $(Get-Date -Format s) ==" | Add-Content $log
    python $plot --data-dir "E:\Origin_Data\$sys" --only $stems *>> $log
    "exit=$LASTEXITCODE $sys" | Add-Content $log
}
python E:\md_kit\reorganize_md_figs_layout.py *>> $log
"LAYOUT exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $log
