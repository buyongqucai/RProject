# MD-compat shim → global E:\alert_kit\send_alert.ps1
param(
  [Parameter(Mandatory = $true)][string]$Subject,
  [Parameter(Mandatory = $true)][string]$BodyFile,
  [string]$AuthFile = "",
  [string]$Account = "1054034696@qq.com"
)
$ErrorActionPreference = "Stop"
$splat = @{
  Subject  = $Subject
  BodyFile = $BodyFile
  From     = $Account
  To       = $Account
}
if (-not [string]::IsNullOrWhiteSpace($AuthFile)) {
  $splat.AuthFile = $AuthFile
}
& "E:\alert_kit\send_alert.ps1" @splat
