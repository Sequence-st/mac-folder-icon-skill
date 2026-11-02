# One-time check on Windows. Prints the python to use on the last line as:  PY=<path>
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1
# Uses an installed python that already has Pillow + numpy, otherwise makes a small private
# environment in %USERPROFILE%\.config\mac-folder-icon\venv and installs only those two.
$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$cfg = if ($env:MFI_CONFIG_DIR) { $env:MFI_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.config\mac-folder-icon' }

function Test-Py([string]$exe, [string[]]$pre) {
  try { & $exe @pre -c "import PIL, numpy" 2>$null; return ($LASTEXITCODE -eq 0) } catch { return $false }
}
function Find-Base {
  foreach ($c in @(@('py', '-3'), @('python'), @('python3'))) {
    $cmd = Get-Command $c[0] -ErrorAction SilentlyContinue
    if (-not $cmd) { continue }
    if ($cmd.Source -like '*\WindowsApps\*') { continue }   # Microsoft Store placeholder, opens the Store
    $pre = @(); if ($c.Count -gt 1) { $pre = $c[1..($c.Count - 1)] }
    try { $real = & $cmd.Source @pre -c "import sys; print(sys.executable)" 2>$null } catch { continue }
    if ($LASTEXITCODE -eq 0 -and $real) { return $real.Trim() }
  }
  return $null
}

Write-Output ("Windows " + [Environment]::OSVersion.Version)
$base = Find-Base
if (-not $base) {
  Write-Output 'python not found. Install Python 3 from https://www.python.org/downloads/ (check "Add python.exe to PATH"), then try again.'
  exit 1
}
Write-Output ("python: " + $base)
if (Test-Py $base @()) {
  $py = $base
} else {
  $venv = Join-Path $cfg 'venv'
  $py = Join-Path $venv 'Scripts\python.exe'
  if (-not (Test-Path $py) -or -not (Test-Py $py @())) {
    Write-Output "installing Pillow + numpy into $venv (first time only, ~1 min)..."
    New-Item -ItemType Directory -Force -Path $cfg | Out-Null
    & $base -m venv $venv
    if ($LASTEXITCODE -ne 0) { Write-Output 'could not make a python environment'; exit 1 }
    & $py -m pip install -q --disable-pip-version-check pillow numpy
    if ($LASTEXITCODE -ne 0) { Write-Output 'install failed (internet?)'; exit 1 }
  }
}
& $py -c "import PIL, numpy; print('Pillow', PIL.__version__, '/ numpy', numpy.__version__)"
& $py -c "import cv2; print('OpenCV', cv2.__version__, '(optional, found)')" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Output 'OpenCV not found (optional, fine)' }
Write-Output "PY=$py"
