param(
  [string]$Target = ".",
  [switch]$WhatIf
)

$danger = @(".\", ".", "..\", "..", "C:\", "D:\", "$env:USERPROFILE", "$env:OneDrive")
if ($danger -contains $Target) { throw "Refusing to clean dangerous target: $Target" }

Write-Host "Cleaning: $Target"
Get-ChildItem -LiteralPath $Target -Force | Remove-Item -Recurse -Force -WhatIf:$WhatIf
Write-Host "Done."