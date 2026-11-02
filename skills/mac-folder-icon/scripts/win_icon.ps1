# Windows folder icon helper (built-in PowerShell 5.1 or 7)
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File win_icon.ps1 set <icon.ico> <folder> [folder...]
#   powershell -NoProfile -ExecutionPolicy Bypass -File win_icon.ps1 remove <folder> [folder...]
#   powershell -NoProfile -ExecutionPolicy Bypass -File win_icon.ps1 has <folder>                 -> yes / no
#   powershell -NoProfile -ExecutionPolicy Bypass -File win_icon.ps1 readback <folder> <out.png> [size]
#
# How it works: copies the .ico into the folder as a hidden "folder-icon.ico" and points the folder's
# desktop.ini at it (the normal Windows way, same as Properties > Customize > Change Icon).
# An existing desktop.ini (Documents, Desktop, OneDrive folders have one) is kept: only the icon line is
# added, and "remove" puts back exactly what was there before.
# Use the .ico made by make_icon.py (PNG is not accepted here).

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

$TAG = '; mac-folder-icon'
$ICONNAME = 'folder-icon.ico'   # PowerShell names ignore case: keep this apart from any $ico variable

Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @"
using System; using System.Runtime.InteropServices; using System.Drawing; using System.Drawing.Imaging;
[ComImport, Guid("bcc18b79-ba16-442f-80c4-8a59c30c463b"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface IMfiImageFactory { [PreserveSig] int GetImage(MfiSize size, int flags, out IntPtr phbm); }
[StructLayout(LayoutKind.Sequential)] public struct MfiSize { public int cx; public int cy; }
[StructLayout(LayoutKind.Sequential)] public struct MfiBm { public int t; public int w; public int h; public int wb; public short pl; public short bp; public IntPtr bits; }
public static class MfiShell {
  [DllImport("shell32.dll", CharSet=CharSet.Unicode)] public static extern void SHChangeNotify(int e, uint f, string a, IntPtr b);
  [DllImport("shell32.dll", CharSet=CharSet.Unicode, PreserveSig=false)]
  static extern void SHCreateItemFromParsingName(string p, IntPtr bc, [MarshalAs(UnmanagedType.LPStruct)] Guid riid, [MarshalAs(UnmanagedType.Interface)] out IMfiImageFactory f);
  [DllImport("gdi32.dll")] static extern int GetObject(IntPtr h, int c, ref MfiBm bm);
  [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr h);
  public static void Refresh(string path) {
    SHChangeNotify(0x00002000, 0x0005, path, IntPtr.Zero);   // SHCNE_UPDATEITEM, SHCNF_PATHW
    SHChangeNotify(0x00001000, 0x0005, path, IntPtr.Zero);   // SHCNE_UPDATEDIR
    SHChangeNotify(0x08000000, 0x0000, null, IntPtr.Zero);   // SHCNE_ASSOCCHANGED
  }
  public static string Readback(string path, int size, string outp) {
    IMfiImageFactory f;
    SHCreateItemFromParsingName(path, IntPtr.Zero, new Guid("bcc18b79-ba16-442f-80c4-8a59c30c463b"), out f);
    IntPtr hbm; int hr = f.GetImage(new MfiSize{cx=size, cy=size}, 0x4, out hbm);   // SIIGBF_ICONONLY
    if (hr != 0) return "FAIL readback hr=" + hr;
    MfiBm bm = new MfiBm(); GetObject(hbm, Marshal.SizeOf(typeof(MfiBm)), ref bm);
    var b = new Bitmap(bm.w, Math.Abs(bm.h), bm.wb, PixelFormat.Format32bppPArgb, bm.bits);
    var c = new Bitmap(b); if (bm.h > 0) c.RotateFlip(RotateFlipType.RotateNoneFlipY);
    c.Save(outp, ImageFormat.Png); DeleteObject(hbm);
    return "saved " + outp;
  }
}
"@

function Get-Dir([string]$p) {
  $full = [IO.Path]::GetFullPath($p)
  if (-not [IO.Directory]::Exists($full)) { throw "not a folder: $p" }
  return $full.TrimEnd('\')
}

function Clear-Attr([string]$f) { if ([IO.File]::Exists($f)) { [IO.File]::SetAttributes($f, [IO.FileAttributes]::Normal) } }

function Read-Ini([string]$f) {
  if (-not [IO.File]::Exists($f)) { return @() }
  return @([IO.File]::ReadAllLines($f))   # detects UTF-16/UTF-8 BOM, otherwise system code page
}

function Write-Ini([string]$f, [string[]]$lines) {
  Clear-Attr $f
  [IO.File]::WriteAllLines($f, $lines, [Text.Encoding]::Unicode)
  [IO.File]::SetAttributes($f, [IO.FileAttributes]::Hidden -bor [IO.FileAttributes]::System)
}

function Set-Icon([string]$icoPath, [string]$folder) {
  $d = Get-Dir $folder
  $ini = Join-Path $d 'desktop.ini'
  $dst = Join-Path $d $ICONNAME
  Clear-Attr $dst
  Copy-Item -LiteralPath $icoPath -Destination $dst -Force
  [IO.File]::SetAttributes($dst, [IO.FileAttributes]::Hidden)

  $lines = Read-Ini $ini
  $created = ($lines.Count -eq 0)
  $already = [bool]($lines | Where-Object { $_ -like "$TAG*" })
  $out = New-Object System.Collections.Generic.List[string]
  $inShell = $false; $hasShell = $false
  foreach ($l in $lines) {
    $t = $l.Trim()
    if ($t -match '^\[.*\]$') { $inShell = ($t -ieq '[.ShellClassInfo]'); if ($inShell) { $hasShell = $true } }
    if ($inShell -and -not $already -and $t -match '^(IconResource|IconFile|IconIndex)\s*=') {
      $out.Add("$TAG old: $t"); continue                      # remember the old icon line for "remove"
    }
    if ($inShell -and $t -match '^IconResource\s*=') { continue } # our own line from an earlier run
    $out.Add($l)
  }
  if (-not $hasShell) { $out.Insert(0, '[.ShellClassInfo]') }
  $i = 0; while ($out[$i].Trim() -ine '[.ShellClassInfo]') { $i++ }
  $out.Insert($i + 1, "IconResource=$ICONNAME,0")
  if (-not $already) {
    $out.Add("$TAG made-ini: $created")
    $ro = (([IO.File]::GetAttributes($d) -band [IO.FileAttributes]::ReadOnly) -ne 0)
    $out.Add("$TAG had-readonly: $ro")
  }
  Write-Ini $ini $out.ToArray()
  # Windows reads desktop.ini only from folders marked read-only or system
  [IO.File]::SetAttributes($d, [IO.File]::GetAttributes($d) -bor [IO.FileAttributes]::ReadOnly)
  [MfiShell]::Refresh($d)
  if ((Has-Icon $d) -eq 'yes') { return "ok $d" } else { return "FAIL $d" }
}

function Remove-Icon([string]$folder) {
  $d = Get-Dir $folder
  $ini = Join-Path $d 'desktop.ini'
  $lines = Read-Ini $ini
  if (-not ($lines | Where-Object { $_ -like "$TAG*" })) { return "nothing to remove (not set by this skill): $d" }
  $made = [bool]($lines | Where-Object { $_ -like "$TAG made-ini: True" })
  $hadRo = [bool]($lines | Where-Object { $_ -like "$TAG had-readonly: True" })
  $out = New-Object System.Collections.Generic.List[string]
  foreach ($l in $lines) {
    $t = $l.Trim()
    if ($t -like "$TAG old: *") { $out.Add($t.Substring(("$TAG old: ").Length)); continue }
    if ($t -like "$TAG*") { continue }
    if ($t -ieq "IconResource=$ICONNAME,0") { continue }
    $out.Add($l)
  }
  $rest = @($out | Where-Object { $_.Trim() -ne '' -and $_.Trim() -ine '[.ShellClassInfo]' })
  if ($made -and $rest.Count -eq 0) { Clear-Attr $ini; Remove-Item -LiteralPath $ini -Force }
  else { Write-Ini $ini $out.ToArray() }
  $dst = Join-Path $d $ICONNAME
  if ([IO.File]::Exists($dst)) { Clear-Attr $dst; Remove-Item -LiteralPath $dst -Force }
  if (-not $hadRo) { [IO.File]::SetAttributes($d, [IO.File]::GetAttributes($d) -band (-bnot [IO.FileAttributes]::ReadOnly)) }
  [MfiShell]::Refresh($d)
  return "removed $d"
}

function Has-Icon([string]$folder) {
  $d = Get-Dir $folder
  $ini = Join-Path $d 'desktop.ini'
  $ok = [IO.File]::Exists((Join-Path $d $ICONNAME)) -and [bool]((Read-Ini $ini) | Where-Object { $_.Trim() -ieq "IconResource=$ICONNAME,0" })
  if ($ok) { 'yes' } else { 'no' }
}

if ($args.Count -lt 2) { Write-Output 'usage: win_icon.ps1 set <icon.ico> <folder>... | remove <folder>... | has <folder> | readback <folder> <out.png> [size]'; exit 1 }
$cmd = $args[0]
$fail = 0
switch ($cmd) {
  'set' {
    $ico = [IO.Path]::GetFullPath($args[1])
    if (-not $ico.ToLower().EndsWith('.ico') -or -not [IO.File]::Exists($ico)) { Write-Output "FAIL need the .ico file from make_icon.py: $($args[1])"; exit 1 }
    foreach ($f in $args[2..($args.Count - 1)]) { try { $r = Set-Icon $ico $f } catch { $r = "FAIL $f : $($_.Exception.Message)" }; if ($r -like 'FAIL*') { $fail++ }; Write-Output $r }
  }
  'remove' { foreach ($f in $args[1..($args.Count - 1)]) { try { Write-Output (Remove-Icon $f) } catch { $fail++; Write-Output "FAIL $f : $($_.Exception.Message)" } } }
  'has' { try { Write-Output (Has-Icon $args[1]) } catch { Write-Output "FAIL $($_.Exception.Message)"; $fail++ } }
  'readback' {
    $size = 256; if ($args.Count -ge 4) { $size = [int]$args[3] }
    try { Write-Output ([MfiShell]::Readback((Get-Dir $args[1]), $size, [IO.Path]::GetFullPath($args[2]))) } catch { Write-Output "FAIL $($_.Exception.Message)"; $fail++ }
  }
  default { Write-Output "unknown command: $cmd"; exit 1 }
}
if ($fail -gt 0) { exit 1 }
