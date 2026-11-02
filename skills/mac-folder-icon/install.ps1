# Installs this skill on Windows for both Codex and Claude Code.
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
# - copies the skill to  %USERPROFILE%\.agents\skills\mac-folder-icon   (Codex reads this folder)
# - links it into        %USERPROFILE%\.claude\skills\mac-folder-icon   (Claude Code reads this folder; a folder
#                        junction, needs no admin rights)
# - runs the one-time check (Pillow + numpy)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
$name = 'mac-folder-icon'
$agents = Join-Path $env:USERPROFILE '.agents\skills'
$dest = Join-Path $agents $name

if ((Resolve-Path $src).Path -ne $dest) {
  New-Item -ItemType Directory -Force -Path $agents | Out-Null
  $tmp = "$dest.tmp"
  if (Test-Path $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }
  Copy-Item -LiteralPath $src -Destination $tmp -Recurse
  foreach ($junk in @('.git', '__pycache__', 'scripts\__pycache__')) {
    $j = Join-Path $tmp $junk; if (Test-Path $j) { Remove-Item -LiteralPath $j -Recurse -Force }
  }
  if (Test-Path $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
  Rename-Item -LiteralPath $tmp -NewName $name
}
Write-Output "Codex: $dest"

$claude = Join-Path $env:USERPROFILE '.claude'
if (Test-Path $claude) {
  $cs = Join-Path $claude 'skills'
  New-Item -ItemType Directory -Force -Path $cs | Out-Null
  $cl = Join-Path $cs $name
  if (Test-Path $cl) {
    $it = Get-Item -LiteralPath $cl -Force
    if ($it.LinkType) { $it.Delete() } else { Remove-Item -LiteralPath $cl -Recurse -Force }
  }
  New-Item -ItemType Junction -Path $cl -Target $dest | Out-Null
  Write-Output "Claude Code: $cl"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $dest 'scripts\setup.ps1')
Write-Output 'done. Say: "우리 고양이 사진으로 폴더 아이콘 만들어줘"'
