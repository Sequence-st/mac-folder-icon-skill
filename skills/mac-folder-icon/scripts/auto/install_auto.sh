#!/bin/bash
# Turn on "new folders get my icon automatically".
#   bash install_auto.sh <icon_512.png> [folder_to_watch]      (default folder: ~/Desktop)
# Existing folders are only remembered, never changed. Turn off with uninstall_auto.sh.
set -euo pipefail
ICON="${1:?usage: install_auto.sh <icon.png> [folder_to_watch]}"
WATCH="${2:-$HOME/Desktop}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CFG="${MFI_CONFIG_DIR:-$HOME/.config/mac-folder-icon}/auto"
USER_ID="$(id -un | tr -c 'A-Za-z0-9.\n-' '-')"
LABEL="${MFI_LABEL:-com.${USER_ID}.mac-folder-icon}"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

[ -f "$ICON" ] || { echo "picture not found: $ICON"; exit 1; }
[ -d "$WATCH" ] || { echo "folder not found: $WATCH"; exit 1; }
WATCH="$(cd "$WATCH" && pwd)"
mkdir -p "$CFG" "$HOME/Library/LaunchAgents"
cp "$HERE/auto_apply.js" "$CFG/auto_apply.js"
cp "$ICON" "$CFG/icon.png"
/usr/bin/python3 - "$CFG" "$WATCH" <<'PY'
import json, sys
cfg, watch = sys.argv[1], sys.argv[2]
json.dump({"icon": cfg + "/icon.png", "watch": [watch]}, open(cfg + "/auto.json", "w"), ensure_ascii=False)
PY
rm -f "$CFG/seen.json"
echo "remembering the folders that are already there (they stay as they are)..."
/usr/bin/osascript -l JavaScript "$CFG/auto_apply.js" "$CFG" init

xml() { printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$(xml "$LABEL")</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/osascript</string><string>-l</string><string>JavaScript</string>
    <string>$(xml "$CFG/auto_apply.js")</string><string>$(xml "$CFG")</string><string>run</string>
  </array>
  <key>WatchPaths</key><array><string>$(xml "$WATCH")</string></array>
  <key>ThrottleInterval</key><integer>3</integer>
  <key>StandardOutPath</key><string>$(xml "$CFG/auto.log")</string>
  <key>StandardErrorPath</key><string>$(xml "$CFG/auto.log")</string>
</dict>
</plist>
EOF
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "on: new folders in $WATCH get the icon ($LABEL)"
echo "If macOS asks \"osascript wants to access files in your Desktop folder\", click Allow."
