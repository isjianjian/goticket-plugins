#!/usr/bin/env python3
"""Print or set the canvas plugin version in every client manifest.

    python3 scripts/version.py          # list versions, fail if they differ
    python3 scripts/version.py 0.2.1    # set all of them

Clients only pick up an update when the version changes, so bump it on
every change to skills/, .mcp.json or a manifest.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGINS = [
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".codebuddy-plugin/plugin.json",
    ".kimi-plugin/plugin.json",
    "gemini-extension.json",
]
MARKETPLACES = [
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/marketplace.json",
    ".codebuddy-plugin/marketplace.json",
]


def entries():
    for name in PLUGINS:
        path = ROOT / name
        data = json.loads(path.read_text(encoding="utf-8"))
        yield path, data, [data]
    for name in MARKETPLACES:
        path = ROOT / name
        data = json.loads(path.read_text(encoding="utf-8"))
        yield path, data, [p for p in data["plugins"] if p["name"] == "canvas"]


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    seen = set()
    for path, data, items in entries():
        for item in items:
            if target:
                item["version"] = target
            seen.add(item.get("version"))
            print(f"{item.get('version')}  {path.relative_to(ROOT)}")
        if target:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if len(seen) != 1:
        sys.exit("versions differ")


if __name__ == "__main__":
    main()
