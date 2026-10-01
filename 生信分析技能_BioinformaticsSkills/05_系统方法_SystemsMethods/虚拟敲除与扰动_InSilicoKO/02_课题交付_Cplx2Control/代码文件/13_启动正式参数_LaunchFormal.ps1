# Launch formal KO: sequential subtypes, ~20 cores via parallel nNet (patched).
$ErrorActionPreference = "Stop"
$env:OMP_NUM_THREADS = "2"
$env:OPENBLAS_NUM_THREADS = "2"
$env:MKL_NUM_THREADS = "2"
$env:VECLIB_MAXIMUM_THREADS = "2"
$env:R_PARALLELLY_AVAILABLECORES = "24"
$env:FORMAL_N_WORKERS = "20"
Remove-Item Env:FORCE_RERUN -ErrorAction SilentlyContinue

$script = Join-Path $PSScriptRoot "13_正式参数虚拟敲除_RunFormalDefaults.R"
$rscript = "E:\R-4.6.0\bin\Rscript.exe"
$desktop = [Environment]::GetFolderPath("Desktop")
$logDir = Join-Path $desktop "琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件\报告文件"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stdout = Join-Path $logDir "正式参数_stdout.txt"
$stderr = Join-Path $logDir "正式参数_stderr.txt"
"" | Set-Content -Path $stdout -Encoding utf8
"" | Set-Content -Path $stderr -Encoding utf8

Write-Host "Starting formal KO MAXCPU: sequential subtypes, parallel nNet workers<=20"
Write-Host "stdout: $stdout"
Write-Host "stderr: $stderr"

$p = Start-Process -FilePath $rscript `
  -ArgumentList @("--vanilla", $script) `
  -WorkingDirectory $PSScriptRoot `
  -RedirectStandardOutput $stdout `
  -RedirectStandardError $stderr `
  -PassThru -WindowStyle Hidden

try { $p.PriorityClass = "High" } catch { Write-Host "Priority High not set: $($_.Exception.Message)" }

Write-Host "PID=$($p.Id)"
$p.Id | Out-File -Encoding utf8 (Join-Path $logDir "正式参数_PID.txt")
