# Non-interactive MD installer (auto-reboot; ignore docker-desktop).
$ErrorActionPreference = "Continue"
$Kit = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = "E:\安装日志"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Boot02 = "/mnt/e/RProject/努力学习项目/网络毒理学_菌群代谢物双交集/准备文件/MD环境/02_环境内引导_bootstrap_md_env.sh"
$Boot03 = "/mnt/e/RProject/努力学习项目/网络毒理学_菌群代谢物双交集/准备文件/MD环境/03_构建GPU版GROMACS.sh"
$Smoke  = "/mnt/e/RProject/努力学习项目/网络毒理学_菌群代谢物双交集/准备文件/MD环境/04_烟测_3HTB.sh"
$summary = Join-Path $LogDir "00_summary.txt"

function Head($t) {
  $line = "`n===== $t ====="
  Write-Host $line -ForegroundColor Cyan
  Add-Content -Path $summary -Value $line
}
function Log($t) {
  Write-Host $t
  Add-Content -Path $summary -Value $t
}
function Get-Distros {
  @(& wsl.exe -l -q 2>$null | ForEach-Object { "$_".Replace([char]0, '').Trim() } | Where-Object { $_ })
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
  ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Log "Need admin; relaunching elevated..."
  Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File","`"$PSCommandPath`""
  exit
}

Head "[1/5] WSL2 + Ubuntu-24.04 -> E:\WSL"
$distros = Get-Distros
Log ("Detected: " + ($distros -join ", "))
if ($distros -notcontains "Ubuntu-24.04") {
  New-Item -ItemType Directory -Force -Path "E:\WSL" | Out-Null
  & wsl.exe --install -d Ubuntu-24.04 --location "E:\WSL\Ubuntu" 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "01_wsl_install.log")
  Log "Ubuntu install invoked. Auto-reboot in 15s. Re-run this script after reboot."
  Start-Sleep -Seconds 15
  Restart-Computer -Force
  exit 0
}
$Distro = "Ubuntu-24.04"

Head "[2/5] Distro OOBE check ($Distro)"
$ok = & wsl.exe -d $Distro -- echo OOBE_OK 2>&1 | Out-String
if ($ok -notmatch "OOBE_OK") {
  Log "OOBE not ready. Opening interactive shell for username/password (ASCII only)."
  Start-Process wsl -ArgumentList "-d",$Distro -Wait
  $ok = & wsl.exe -d $Distro -- echo OOBE_OK 2>&1 | Out-String
  if ($ok -notmatch "OOBE_OK") { Log "FAIL OOBE"; exit 1 }
}
Log "OOBE OK"

Head "[3/5] UV bootstrap (02)"
& wsl.exe -d $Distro -- bash -c "test -x ~/md-venv/bin/acpype && command -v antechamber >/dev/null" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
  Log "02 already installed; skip"
} else {
  & wsl.exe -d $Distro -- bash -c "bash '$Boot02'" 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "02_bootstrap.log")
  if ($LASTEXITCODE -ne 0) { Log "FAIL 02"; exit 1 }
  Log "02 OK"
}

Head "[4/5] GPU GROMACS (03)"
& wsl.exe -d $Distro -- bash -c "test -x ~/gromacs-gpu/bin/gmx" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
  Log "03 already built; skip"
} else {
  & wsl.exe -d $Distro -- bash -c "bash '$Boot03'" 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "03_gpu_gromacs.log")
  if ($LASTEXITCODE -ne 0) { Log "FAIL 03"; exit 1 }
  Log "03 OK"
}

Head "[5/5] Smoke 3HTB (04)"
& wsl.exe -d $Distro -- bash -c "bash '$Smoke'" 2>&1 |
  Tee-Object -FilePath (Join-Path $LogDir "04_smoke.log")
$smokeLog = Join-Path $LogDir "04_smoke.log"
$smokeOk = Select-String -Path $smokeLog -Pattern "SMOKE PASS" -Quiet -ErrorAction SilentlyContinue
$gpuOk   = Select-String -Path $smokeLog -Pattern "CUDA acceleration" -Quiet -ErrorAction SilentlyContinue
Head "SUMMARY"
Log ("smoke=" + $(if($smokeOk){"PASS"}else{"FAIL"}))
Log ("gpu_cuda=" + $(if($gpuOk){"YES"}else{"NO"}))
Log ("logdir=$LogDir")
