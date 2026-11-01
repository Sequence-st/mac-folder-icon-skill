#!/usr/bin/env python3
"""Remember which image generator this user picked, so the skill asks only once.

    python3 route.py get                         -> prints the saved choice as JSON, or "none"
    python3 route.py set <route> [--tool NAME] [--model NAME]
    python3 route.py clear

<route> is one of: codex | mcp | flow | manual
Saved in ~/.config/mac-folder-icon/route.json (or $MFI_CONFIG_DIR/route.json).
"""
import argparse
import json
import os
import time

CFG = os.environ.get("MFI_CONFIG_DIR") or os.path.expanduser("~/.config/mac-folder-icon")
PATH = os.path.join(CFG, "route.json")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("get")
    sub.add_parser("clear")
    s = sub.add_parser("set")
    s.add_argument("route", choices=["codex", "mcp", "flow", "manual"])
    s.add_argument("--tool", help="MCP tool name, e.g. the image tool of the chosen server")
    s.add_argument("--model", help="model name/id used on that route")
    a = ap.parse_args()
    if a.cmd == "get":
        print(open(PATH).read().strip() if os.path.exists(PATH) else "none")
    elif a.cmd == "clear":
        if os.path.exists(PATH):
            os.remove(PATH)
        print("cleared")
    else:
        os.makedirs(CFG, exist_ok=True)
        d = {"route": a.route, "tool": a.tool, "model": a.model, "saved": time.strftime("%Y-%m-%d %H:%M")}
        json.dump(d, open(PATH, "w"), ensure_ascii=False)
        print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
