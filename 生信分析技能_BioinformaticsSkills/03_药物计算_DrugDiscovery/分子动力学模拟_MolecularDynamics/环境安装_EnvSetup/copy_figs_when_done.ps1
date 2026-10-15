# 每套画完即拷贝 OriginFigures 到 努力学习项目/08_分子动力学/文档文件/图片文件/分子动力学图_MD/<体系>/
$log = "E:\Origin_Data\_plot_all_done.log"
$dstRoot = "E:\RProject\努力学习项目\08_分子动力学\文档文件\图片文件\分子动力学图_MD"
$systems = @("FOS_quercetin_1A02", "ADA_Adenosine_7RTG_A2", "MMP9_Tryptophan_4H3X")
$done = @{}
$deadline = (Get-Date).AddHours(8)
while ((Get-Date) -lt $deadline) {
    foreach ($sys in $systems) {
        if ($done[$sys]) { continue }
        if (Test-Path $log) {
            $hit = Select-String -Path $log -Pattern "exit=0 $sys" -Quiet
            if ($hit) {
                $src = "E:\Origin_Data\$sys\OriginFigures"
                $dst = Join-Path $dstRoot $sys
                if (Test-Path $src) {
                    New-Item -ItemType Directory -Force -Path $dst | Out-Null
                    Copy-Item -Path (Join-Path $src "*") -Destination $dst -Recurse -Force
                }
                $done[$sys] = $true
            }
        }
    }
    if ($done.Count -eq $systems.Count) { break }
    Start-Sleep -Seconds 30
}
"COPY_WATCHER done: $($done.Keys -join ', ') $(Get-Date -Format s)" | Add-Content "E:\Origin_Data\_copy_watcher.log"
