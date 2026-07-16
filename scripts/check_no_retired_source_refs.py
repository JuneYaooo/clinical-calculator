#!/usr/bin/env python3
"""Fail if public project files contain retired-source references."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN = [
    "Ex" + "cel",
    "ex" + "cel",
    "calculator" + "_processed",
    "." + "xl" + "sx",
    "\u539f\u59cb\u8868",
    "\u539f\u8868",
    "\u7ebf\u7d22",
    "\u539f\u4e13\u4e1a\u7c7b\u522b",
    "\u6765\u6e90\u6587\u4ef6",
    "\u7528\u6237\u63d0\u4f9b",
    "\u65e9\u671f\u8f93\u5165",
]

SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
}

SKIP_SUFFIXES = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
}


def iter_files() -> list[Path]:
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        for filename in filenames:
            path = Path(current_root) / filename
            if path.suffix.lower() in SKIP_SUFFIXES:
                continue
            files.append(path)
    return files


def main() -> int:
    matches: list[str] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(term in line for term in FORBIDDEN):
                matches.append(f"{relative}:{line_number}")

    if matches:
        print("retired source reference scan failed")
        for match in matches[:100]:
            print(match)
        if len(matches) > 100:
            print(f"... {len(matches) - 100} more")
        return 1

    print("retired source reference scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
