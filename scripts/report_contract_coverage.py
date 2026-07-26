#!/usr/bin/env python3
"""Write and print built-in input-contract coverage metrics."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from clinical_calculators.contract_coverage import calculate_contract_coverage  # noqa: E402


REPORT_PATH = ROOT / "reports" / "contract_coverage.json"


def main() -> int:
    coverage = calculate_contract_coverage()
    rendered = json.dumps(coverage, ensure_ascii=False, indent=2) + "\n"
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
