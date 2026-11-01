#!/bin/bash
# Turn off the automatic new-folder icon. Folders that already got the icon keep it
# (put them back with: osascript -l JavaScript ../icon.js remove <folder>).
#   bash uninstall_auto.sh            stop it, keep settings
#   bash uninstall_auto.sh --purge    stop it and delete its settings too
set -uo pipefail
CFG="${MFI_CONFIG_DIR:-$HOME/.config/mac-folder-icon}/auto"
USER_ID="$(id -un | tr -c 'A-Za-z0-9.\n-' '-')"
LABEL="${MFI_LABEL:-com.${USER_ID}.mac-folder-icon}"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null && echo "stopped $LABEL" || echo "$LABEL was not running"
rm -f "$PLIST"
if [ "${1:-}" = "--purge" ]; then rm -rf "$CFG"; echo "settings removed: $CFG"; fi
echo "off"
