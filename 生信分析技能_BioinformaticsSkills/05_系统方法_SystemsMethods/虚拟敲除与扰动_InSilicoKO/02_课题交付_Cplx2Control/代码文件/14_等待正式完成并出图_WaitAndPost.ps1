$ErrorActionPreference = "Stop"
$desktop = [Environment]::GetFolderPath("Desktop")
$rep = Join-Path $desktop "琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件\报告文件"
$tab = Join-Path $desktop "琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件\数据文件"
$obj = Join-Path $tab "敲除对象_KoObjects_Formal"
$code = Split-Path -Parent $MyInvocation.MyCommand.Path
$rscript = "E:\R-4.6.0\bin\Rscript.exe"
$pipe = Join-Path $code "14_正式后出图分析_PostFormalPipeline.R"
$log = Join-Path $rep "14_WaitAndPost.log"
$stdout = Join-Path $rep "14_PostFormal_stdout.txt"
$stderr = Join-Path $rep "14_PostFormal_stderr.txt"
$subtypes = @("cLTMR","NF1","NP","PEP","TRPM8")

New-Item -ItemType Directory -Force -Path $rep | Out-Null
function Write-Log([string]$msg) {
  $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
  [System.IO.File]::AppendAllText($log, $line + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
  Write-Host $line
}

function Test-FormalReady {
  $status = Join-Path $rep "STATUS_Formal.txt"
  if ((Test-Path -LiteralPath $status) -and ((Get-Content -LiteralPath $status -Raw -ErrorAction SilentlyContinue) -match "FORMAL_COMPLETE")) {
    return $true
  }
  $n = 0
  foreach ($s in $subtypes) {
    $rds = Join-Path $obj ("{0}_Cplx2_formal.rds" -f $s)
    $csv = Join-Path $tab ("04_扰动基因_{0}_Cplx2Dr_Formal.csv" -f $s)
    if ((Test-Path -LiteralPath $rds) -and (Test-Path -LiteralPath $csv) -and ((Get-Item -LiteralPath $rds).Length -gt 1000)) { $n++ }
  }
  return ($n -eq 5)
}

$post = Join-Path $rep "STATUS_PostFormal.txt"
if ((Test-Path -LiteralPath $post) -and ((Get-Content -LiteralPath $post -Raw) -match "POST_FORMAL_COMPLETE")) {
  Write-Log "PostFormal already complete; exit."
  exit 0
}

Write-Log ("Waiting for Formal KO... rep=" + $rep)
Write-Log ("pipe exists=" + (Test-Path -LiteralPath $pipe))
$last = -1
while (-not (Test-FormalReady)) {
  $n = 0
  foreach ($s in $subtypes) {
    $rds = Join-Path $obj ("{0}_Cplx2_formal.rds" -f $s)
    $csv = Join-Path $tab ("04_扰动基因_{0}_Cplx2Dr_Formal.csv" -f $s)
    if ((Test-Path -LiteralPath $rds) -and (Test-Path -LiteralPath $csv) -and ((Get-Item -LiteralPath $rds).Length -gt 1000)) { $n++ }
  }
  if ($n -ne $last) {
    Write-Log ("Formal progress: {0}/5 checkpoints" -f $n)
    $last = $n
  }
  Start-Sleep -Seconds 120
}

Write-Log "Formal ready. Launching PostFormal pipeline..."
[System.IO.File]::WriteAllText($stdout, "", [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($stderr, "", [System.Text.UTF8Encoding]::new($false))
$p = Start-Process -FilePath $rscript `
  -ArgumentList @("--vanilla", $pipe) `
  -WorkingDirectory $code `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr `
  -PassThru -Wait -WindowStyle Hidden
Write-Log ("PostFormal exit code={0}" -f $p.ExitCode)
if ($p.ExitCode -ne 0) {
  Write-Log "FAILED — see 14_PostFormal_stderr.txt"
  exit $p.ExitCode
}
Write-Log "POST_FORMAL_DONE"
exit 0