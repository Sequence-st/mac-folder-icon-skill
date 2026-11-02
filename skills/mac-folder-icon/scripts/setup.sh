#!/bin/bash
# One-time check. Prints the python to use on the last line as:  PY=<path>
#   bash setup.sh
# Uses the system python3 if it already has Pillow + numpy, otherwise makes a small private
# environment in ~/.config/mac-folder-icon/venv and installs only those two.
set -uo pipefail
CFG="${MFI_CONFIG_DIR:-$HOME/.config/mac-folder-icon}"
HERE="$(cd "$(dirname "$0")" && pwd)"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$HERE/setup.ps1" 2>/dev/null || echo "$HERE/setup.ps1")" ;;
esac
[ "$(uname)" = "Darwin" ] || { echo "This skill works on macOS or Windows only."; exit 1; }
command -v osascript >/dev/null || { echo "osascript missing (macOS built-in tool)."; exit 1; }
if ! command -v python3 >/dev/null; then
  echo "python3 not found. Run:  xcode-select --install   then try again."; exit 1
fi
echo "macOS $(sw_vers -productVersion), $(python3 --version 2>&1)"
if python3 -c "import PIL, numpy" 2>/dev/null; then
  PY="$(command -v python3)"
else
  VENV="$CFG/venv"
  if [ ! -x "$VENV/bin/python" ] || ! "$VENV/bin/python" -c "import PIL, numpy" 2>/dev/null; then
    echo "installing Pillow + numpy into $VENV (first time only, ~1 min)..."
    mkdir -p "$CFG"
    python3 -m venv "$VENV" || { echo "could not make a python environment"; exit 1; }
    "$VENV/bin/python" -m pip install -q --disable-pip-version-check pillow numpy || { echo "install failed (internet?)"; exit 1; }
  fi
  PY="$VENV/bin/python"
fi
"$PY" -c "import PIL, numpy; print('Pillow', PIL.__version__, '/ numpy', numpy.__version__)"
"$PY" -c "import cv2; print('OpenCV', cv2.__version__, '(optional, found)')" 2>/dev/null || echo "OpenCV not found (optional, fine)"
echo "PY=$PY"
