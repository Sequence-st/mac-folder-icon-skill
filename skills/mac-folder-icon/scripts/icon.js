// Mac folder icon helper (JavaScript for Automation, runs with the built-in osascript)
//
//   osascript -l JavaScript icon.js set <icon.png> <folder> [folder...]   put the picture on folders
//   osascript -l JavaScript icon.js remove <folder> [folder...]           back to the normal blue folder
//   osascript -l JavaScript icon.js has <folder>                          prints yes / no
//   osascript -l JavaScript icon.js readback <folder> <out.png> [size]   saves what macOS now shows for the folder
//
// Do NOT call Finder's "update" command after setting an icon: it can drop the new icon again.
// Finder redraws by itself in about 2-3 seconds. If an old icon stays, close and reopen the window.
ObjC.import('AppKit');
ObjC.import('Foundation');

const fm = $.NSFileManager.defaultManager;
const ws = $.NSWorkspace.sharedWorkspace;

function hasIcon(p) { return fm.fileExistsAtPath(p + '/Icon\r'); }
function isDir(p) { const d = Ref(); return fm.fileExistsAtPathIsDirectory(p, d) && d[0]; }

function setIcon(png, p) {
  if (!isDir(p)) return 'FAIL not a folder: ' + p;
  const img = $.NSImage.alloc.initWithContentsOfFile(png);
  if (img.isNil()) return 'FAIL cannot read picture: ' + png;
  for (let t = 0; t < 3; t++) {          // now and then the icon drops right after setting -> check and retry
    ws.setIconForFileOptions(img, p, 0);
    delay(0.15);
    if (hasIcon(p)) { try { ws.noteFileSystemChanged(p); } catch (e) {} return 'ok ' + p; }
    delay(0.3);
  }
  return 'FAIL ' + p;
}

function removeIcon(p) {
  ws.setIconForFileOptions($(), p, 0);
  return (hasIcon(p) ? 'FAIL ' : 'removed ') + p;
}

function readback(p, out, size) {
  const S = size || 512;
  const img = ws.iconForFile(p);
  img.setSize($.NSMakeSize(S, S));
  const rep = $.NSBitmapImageRep.alloc.initWithBitmapDataPlanesPixelsWidePixelsHighBitsPerSampleSamplesPerPixelHasAlphaIsPlanarColorSpaceNameBytesPerRowBitsPerPixel(
    null, S, S, 8, 4, true, false, $.NSDeviceRGBColorSpace, 0, 0);
  $.NSGraphicsContext.saveGraphicsState;
  $.NSGraphicsContext.setCurrentContext($.NSGraphicsContext.graphicsContextWithBitmapImageRep(rep));
  img.drawInRectFromRectOperationFraction($.NSMakeRect(0, 0, S, S), $.NSZeroRect, $.NSCompositingOperationCopy, 1.0);
  $.NSGraphicsContext.restoreGraphicsState;
  const data = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $());
  return data.writeToFileAtomically(out, true) ? 'saved ' + out : 'FAIL ' + out;
}

function run(argv) {
  const mode = argv[0];
  if (mode === 'set') return argv.slice(2).map(p => setIcon(argv[1], p)).join('\n');
  if (mode === 'remove') return argv.slice(1).map(removeIcon).join('\n');
  if (mode === 'has') return hasIcon(argv[1]) ? 'yes' : 'no';
  if (mode === 'readback') return readback(argv[1], argv[2], parseInt(argv[3] || '512', 10));
  return 'usage: icon.js set <png> <folder...> | remove <folder...> | has <folder> | readback <folder> <out.png> [size]';
}
