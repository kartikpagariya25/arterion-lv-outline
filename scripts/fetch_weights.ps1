# Downloads trained ONNX weights from the latest GitHub Release into backend/app/lv_outline/weights/
$ErrorActionPreference = "Stop"
$repo = "kartikpagariya25/arterion-lv-outline"
$dest = Join-Path $PSScriptRoot "..\backend\app\lv_outline\weights"
New-Item -ItemType Directory -Force $dest | Out-Null
foreach ($f in "lv_model.onnx") {
  Write-Host "Downloading $f ..."
  Invoke-WebRequest "https://github.com/$repo/releases/latest/download/$f" -OutFile (Join-Path $dest $f)
}
Write-Host "Done."
