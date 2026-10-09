# run_3htb_demo.ps1 — 3HTB 0.2ns 演示启动器（Windows 侧一键，Unicode 路径安全）
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File E:\run_3htb_demo.ps1
$ErrorActionPreference = "Continue"
$LogDir = "E:\安装日志"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$log = Join-Path $LogDir "05_3htb_demo.log"
$sh  = "/mnt/e/RProject/努力学习项目/网络毒理学_菌群代谢物双交集/准备文件/MD环境/run_3htb_demo.sh"

Write-Host "启动 3HTB 0.2ns 演示（GPU 全流程，预计 20-60 分钟）..." -ForegroundColor Cyan
& wsl.exe -d Ubuntu-24.04 -- bash $sh 2>&1 | Tee-Object -FilePath $log
Write-Host "`n日志: $log"
if (Select-String -Path $log -Pattern "DEMO PASS" -Quiet -ErrorAction SilentlyContinue) {
  Write-Host "DEMO PASS —— 环境与流程就绪，可进入课题 top3 MD" -ForegroundColor Green
} else {
  Write-Host "未见 DEMO PASS —— 把日志发回排查" -ForegroundColor Red
}
