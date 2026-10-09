# 01_安装WSL与检查.ps1 — WSL2 + Ubuntu-24.04（虚拟盘落 E 盘，按 SOP §9.8）
# 用法：powershell -ExecutionPolicy Bypass -File 01_安装WSL与检查.ps1
# 说明：wsl --install 通常需要管理员权限与一次重启；装完请完成 Ubuntu 首次初始化（用户名纯 ASCII）。

Write-Host "== 第0步：检测已安装的 WSL 发行版 ==" -ForegroundColor Cyan
$distros = wsl -l -q 2>$null
if ($distros) {
    Write-Host "已存在发行版：" -ForegroundColor Green
    wsl -l -v
    Write-Host "→ 无需重复安装，直接执行 02_环境内引导_bootstrap_md_env.sh" -ForegroundColor Green
    exit 0
}

Write-Host "== 第1步：启用 WSL2 并安装 Ubuntu-24.04 到 E:\WSL\Ubuntu ==" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "E:\WSL" | Out-Null
wsl --install -d Ubuntu-24.04 --location E:\WSL\Ubuntu

Write-Host ""
Write-Host "若提示需要重启：请重启后重新打开 PowerShell，" -ForegroundColor Yellow
Write-Host "完成 Ubuntu 首次初始化（用户名请用纯 ASCII），再执行第2步引导脚本。" -ForegroundColor Yellow
