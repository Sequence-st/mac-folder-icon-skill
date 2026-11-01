// New-folder auto icon (run by a LaunchAgent whenever the watched folder changes)
//
//   osascript -l JavaScript auto_apply.js <config_dir> run       put the icon on folders it has never seen
//   osascript -l JavaScript auto_apply.js <config_dir> init      only remember the folders that exist now
//
// <config_dir>/auto.json = {"icon": "<png>", "watch": ["<folder>", ...]}
// <config_dir>/seen.json = folders already handled (by inode, so renaming does not re-trigger)
// - A folder that already has its own icon is left alone.
// - A fresh "untitled folder" is handled after you finish typing its name (waits up to 20 s);
//   setting the icon while the name is still being typed makes Finder flash back to blue.
ObjC.import('AppKit');
ObjC.import('Foundation');

const fm = $.NSFileManager.defaultManager;
const ws = $.NSWorkspace.sharedWorkspace;

function readJSON(p, dflt) {
  const s = $.NSString.stringWithContentsOfFileEncodingError(p, 4, null);
  try { return JSON.parse(s.js); } catch (e) { return dflt; }
}
function writeJSON(p, o) { $(JSON.stringify(o)).writeToFileAtomicallyEncodingError(p, true, 4, null); }
function stamp() { return new Date().toString().slice(4, 24); }
function inode(p) { const a = fm.attributesOfItemAtPathError(p, null); return a.isNil() ? null : ObjC.unwrap(a.objectForKey('NSFileSystemFileNumber')); }
function hasIcon(p) { return fm.fileExistsAtPath(p + '/Icon\r'); }

function folders(dir) {
  const names = fm.contentsOfDirectoryAtPathError(dir, null);
  if (names.isNil()) return null;
  const out = [];
  for (let i = 0; i < names.count; i++) {
    const n = names.objectAtIndex(i).js;
    if (n.startsWith('.')) continue;
    const p = dir + '/' + n;
    const d = Ref();
    if (fm.fileExistsAtPathIsDirectory(p, d) && d[0] && !ws.isFilePackageAtPath(p)) out.push(p);
  }
  return out;
}

// Finder writes new folder names in decomposed Unicode (NFD) -> normalise before matching
const UNTITLED = /^(무제 폴더|untitled folder|名称未設定フォルダ|neuer ordner|nouveau dossier|nueva carpeta)( \d+)?$/i;
function isUntitled(p) { return UNTITLED.test(p.split('/').pop().normalize('NFC')); }

function setIcon(icon, p) {
  const img = $.NSImage.alloc.initWithContentsOfFile(icon);
  if (img.isNil()) return false;
  for (let t = 0; t < 3; t++) {
    ws.setIconForFileOptions(img, p, 0);
    delay(0.15);
    if (hasIcon(p)) { try { ws.noteFileSystemChanged(p); } catch (e) {} return true; }
    delay(0.3);
  }
  return false;
}

function waitNamed(dir, ino) {
  for (let k = 0; k < 80; k++) {
    for (const p of (folders(dir) || [])) if (inode(p) === ino && !isUntitled(p)) return p;
    delay(0.25);
  }
  for (const p of (folders(dir) || [])) if (inode(p) === ino) return p;  // never renamed: use as is
  return null;
}

function run(argv) {
  const cfgDir = argv[0];
  const mode = argv[1] || 'run';
  const cfg = readJSON(cfgDir + '/auto.json', null);
  if (!cfg) return stamp() + ' no auto.json in ' + cfgDir;
  const statePath = cfgDir + '/seen.json';
  const s = readJSON(statePath, { seen: [] });
  const log = [];
  for (const dir of cfg.watch) {
    const list = folders(dir);
    if (list === null) { log.push('cannot read ' + dir + ' (allow the access request?)'); continue; }
    for (const p of list) {
      const i = inode(p);
      if (i === null || s.seen.includes(i)) continue;
      s.seen.push(i);
      if (mode === 'init') continue;
      if (hasIcon(p)) { log.push('skip (has own icon) ' + p); continue; }
      let q = p;
      if (isUntitled(p)) { q = waitNamed(dir, i); if (!q) continue; delay(0.15); }
      log.push((setIcon(cfg.icon, q) ? 'ok ' : 'FAIL ') + q);
    }
  }
  writeJSON(statePath, s);
  if (mode === 'init') return stamp() + ' init: remembered ' + s.seen.length + ' folders';
  return log.length ? stamp() + ' ' + log.join(' | ') : '';
}
