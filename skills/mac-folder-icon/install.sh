#!/bin/bash
# Installs this skill for both Codex and Claude Code.
#   bash install.sh
# - copies the skill to  ~/.agents/skills/mac-folder-icon   (Codex reads this folder)
# - links it into        ~/.claude/skills/mac-folder-icon   (Claude Code reads this folder)
# - runs the one-time check (Pillow + numpy)
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
NAME="mac-folder-icon"
DEST="$HOME/.agents/skills/$NAME"
[ "$(uname)" = "Darwin" ] || { echo "macOS only."; exit 1; }

if [ "$SRC" != "$DEST" ]; then
  mkdir -p "$HOME/.agents/skills"
  rm -rf "${DEST:?}.tmp"
  cp -R "$SRC" "$DEST.tmp"
  rm -rf "$DEST.tmp/.git" "$DEST.tmp/__pycache__" "$DEST.tmp/scripts/__pycache__"
  rm -rf "${DEST:?}"
  mv "$DEST.tmp" "$DEST"
fi
echo "Codex: $DEST"

if [ -d "$HOME/.claude" ]; then
  mkdir -p "$HOME/.claude/skills"
  CL="$HOME/.claude/skills/$NAME"
  if [ -L "$CL" ] || [ ! -e "$CL" ]; then
    ln -sfn "../../.agents/skills/$NAME" "$CL"
  else
    rm -rf "${CL:?}"; cp -R "$DEST" "$CL"      # an old real folder was there: replace with the new copy
  fi
  echo "Claude Code: $CL"
fi

bash "$DEST/scripts/setup.sh"
echo "done. Say: \"우리 고양이 사진으로 폴더 아이콘 만들어줘\""
