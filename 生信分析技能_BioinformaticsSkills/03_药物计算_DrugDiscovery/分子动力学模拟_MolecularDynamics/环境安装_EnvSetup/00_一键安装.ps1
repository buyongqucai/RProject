# 00_一键安装.ps1 — 本地 MD 环境一键安装（WSL→UV环境→GPU GROMACS→烟测）
# 用法（管理员 PowerShell，或右键“使用 PowerShell 运行”）：
#   powershell -ExecutionPolicy Bypass -File 00_一键安装.ps1
# 特性：自提权 / 允许重启（已获授权）/ 每步幂等可续跑（重复执行自动跳过已完成步骤）
#      全程日志 → 本目录\安装日志\（出问题把日志发回即可）
# 已规避坑：PS5.1 的 wsl -l 输出 UTF-16 乱码（做 null 剥离）；不使用 \$HOME（PS 会展开成 Windows 路径，统一用 ~/）
$ErrorActionPreference = "Continue"
$Kit    = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Kit "安装日志"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Boot02 = "/mnt/e/RProject/努力学习项目/网络毒理学_菌群代谢物双交集/准备文件/MD环境/02_环境内引导_bootstrap_md_env.sh"
$Boot03 = "/mnt/e/RProject/努力学习项目/网络毒理学_菌群代谢物双交集/准备文件/MD环境/03_构建GPU版GROMACS.sh"
$Smoke  = "/mnt/e/RProject/努力学习项目/网络毒理学_菌群代谢物双交集/准备文件/MD环境/04_烟测_3HTB.sh"

function Head($t) { Write-Host "`n===== $t =====" -ForegroundColor Cyan }
function Get-Distros {
  # wsl -l -q 在 Windows PowerShell 5.1 下是 UTF-16 → 剥离 NUL 再比对
  @(& wsl.exe -l -q 2>$null | ForEach-Object { "$_".Replace([char]0, '').Trim() } | Where-Object { $_ })
}

# ---- 0) 自提权 ----
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
  ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Write-Host "需要管理员权限，正在请求提权（UAC 点“是”）..." -ForegroundColor Yellow
  Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy","Bypass","-File","`"$PSCommandPath`""
  exit
}

# ---- 1) WSL2 + Ubuntu-24.04 → E:\WSL ----
# 注意：docker-desktop 也是 WSL 发行版，不能当 MD 环境；必须有 Ubuntu-24.04
Head "[1/5] WSL2 + Ubuntu-24.04（→ E:\WSL）"
$distros = Get-Distros
$nonDocker = @($distros | Where-Object { $_ -notmatch '^(docker-desktop|docker-desktop-data)$' })
Write-Host "  已检测到发行版: $($distros -join ', ')"
if ($distros -notcontains "Ubuntu-24.04") {
  New-Item -ItemType Directory -Force -Path "E:\WSL" | Out-Null
  Write-Host "  未找到 Ubuntu-24.04（忽略 docker-desktop），开始安装 → E:\WSL\Ubuntu ..." -ForegroundColor Yellow
  & wsl.exe --install -d Ubuntu-24.04 --location "E:\WSL\Ubuntu" 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "01_wsl_install.log")
  Write-Host "`nWSL 安装命令已执行。日志: 安装日志\01_wsl_install.log" -ForegroundColor Yellow
  Write-Host "若提示需要重启：**允许重启**（已获授权）。重启后重新运行本脚本即可自动续跑。" -ForegroundColor Yellow
  $r = Read-Host "现在就重启吗? (y=立即重启 / n=稍后手动重启)"
  if ($r -eq 'y') { Restart-Computer }
  exit 0
}
$Distro = "Ubuntu-24.04"
if ($nonDocker.Count -gt 0 -and $nonDocker[0] -ne $Distro) {
  Write-Host "  另有非 Docker 发行版: $($nonDocker -join ', ')；MD 固定使用 $Distro" -ForegroundColor DarkGray
}

# ---- 2) 首启 / OOBE ----
Head "[2/5] 发行版首启检查（$Distro）"
$ok = & wsl.exe -d $Distro -- echo OOBE_OK 2>&1 | Out-String
if ($ok -notmatch "OOBE_OK") {
  Write-Host "首次启动出现初始化（若提示 Enter new UNIX username）：" -ForegroundColor Yellow
  Write-Host "  → 用户名/密码必须**纯 ASCII**（避免 GBK 坑；密码输入不显示属正常）" -ForegroundColor Yellow
  Read-Host "完成后按回车继续"
  $ok = & wsl.exe -d $Distro -- echo OOBE_OK 2>&1 | Out-String
  if ($ok -notmatch "OOBE_OK") { Write-Host "仍无法执行命令，把窗口输出发回排查。" -ForegroundColor Red; exit 1 }
}
Write-Host "  发行版可正常执行命令 OK"

# ---- 3) UV 环境（02，幂等） ----
Head "[3/5] UV 环境引导（acpype + gmx_MMPBSA + impi-rt + AmberTools）"
& wsl.exe -d $Distro -- bash -c "test -x ~/md-venv/bin/acpype && command -v antechamber >/dev/null" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
  Write-Host "  已安装，跳过 OK"
} else {
  Write-Host "  执行 02（apt 处会要求输入 WSL 用户的 sudo 密码；约 5-15 分钟）..."
  & wsl.exe -d $Distro -- bash -c "bash '$Boot02'" 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "02_bootstrap.log")
  if ($LASTEXITCODE -ne 0) { Write-Host "02 失败 → 检查 安装日志\02_bootstrap.log 并发回" -ForegroundColor Red; exit 1 }
  Write-Host "  02 完成 OK"
}

# ---- 4) GPU GROMACS（03，幂等；脚本内部也有已构建跳过） ----
Head "[4/5] GPU 版 GROMACS 构建（20-60 分钟）"
& wsl.exe -d $Distro -- bash -c "test -x ~/gromacs-gpu/bin/gmx" 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
  Write-Host "  已构建，跳过 OK"
} else {
  Write-Host "  执行 03（首次会要求 sudo 密码安装 CUDA nvcc；请保持窗口开启）..."
  & wsl.exe -d $Distro -- bash -c "bash '$Boot03'" 2>&1 |
    Tee-Object -FilePath (Join-Path $LogDir "03_gpu_gromacs.log")
  if ($LASTEXITCODE -ne 0) { Write-Host "03 失败 → 检查 安装日志\03_gpu_gromacs.log 并发回" -ForegroundColor Red; exit 1 }
  Write-Host "  03 完成 OK"
}

# ---- 5) 烟测（04） ----
Head "[5/5] 一键烟测 3HTB（NS=0.02，含 GPU 判定）"
& wsl.exe -d $Distro -- bash -c "bash '$Smoke'" 2>&1 |
  Tee-Object -FilePath (Join-Path $LogDir "04_smoke.log")
$smokeLog = Join-Path $LogDir "04_smoke.log"
$smokeOk = Select-String -Path $smokeLog -Pattern "SMOKE PASS" -Quiet -ErrorAction SilentlyContinue
$gpuOk   = Select-String -Path $smokeLog -Pattern "CUDA acceleration" -Quiet -ErrorAction SilentlyContinue

Head "结果汇总"
Write-Host ("  烟测链路: " + $(if($smokeOk){"PASS OK"}else{"未通过 X → 把 安装日志\04_smoke.log 发回"}))
Write-Host ("  GPU 加速: " + $(if($gpuOk){"CUDA acceleration 检出 OK"}else{"未检出（CPU 构建/驱动）→ 把 03、04 日志发回"}))
Write-Host "`n后续：按 SOP §10 回写运行环境登记。日志目录: $LogDir"
