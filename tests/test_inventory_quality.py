import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "clinical_calculator_inventory_full.csv"
EXCLUDED = ROOT / "clinical_calculator_inventory_excluded_pending_sources.csv"
METHODOLOGY = ROOT / "clinical_calculator_source_methodology.md"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


class InventoryQualityTest(unittest.TestCase):
    def test_effective_inventory_has_complete_core_calculator_information(self):
        rows = read_rows(FULL)
        required_fields = [
            "专业类别",
            "疾病/场景",
            "中文名称",
            "英文名称",
            "输入",
            "输出",
            "量表/方程",
            "评分解读",
            "用途",
            "来源类型",
            "来源/指南",
            "来源链接",
            "获取渠道",
            "真实性层级",
            "常用程度",
            "覆盖说明",
            "临床使用说明",
            "条目来源",
        ]

        self.assertEqual(len(rows), 1138)
        self.assertEqual(len({row["中文名称"] for row in rows}), 982)
        for row in rows:
            for field in required_fields:
                self.assertTrue(row[field].strip(), f"{row['id']} missing {field}")
            self.assertTrue(row["来源链接"].startswith("http"), row["id"])
            self.assertFalse(row["真实性层级"].startswith("D："), row["id"])

    def test_pending_inventory_keeps_only_items_that_need_more_work(self):
        rows = read_rows(EXCLUDED)

        self.assertEqual(len(rows), 36)
        self.assertTrue(all(row["中文名称"].strip() for row in rows))
        self.assertTrue(all(row["剔除原因"].strip() for row in rows))
        self.assertTrue(
            all(
                row["剔除原因"]
                in {
                    "来源层级为候选或待审核，未达到可靠来源要求",
                    "核心信息描述过于空泛，需补充具体条目/方程/解读",
                }
                for row in rows
            )
        )

    def test_public_files_do_not_expose_retired_input_artifacts(self):
        terms = [
            "Ex" + "cel",
            "ex" + "cel",
            "calculator" + "_processed",
            "." + "xlsx",
            "原" + "始表",
            "原" + "表",
            "线" + "索",
            "原" + "专业类别",
            "来源" + "文件",
            "用户" + "提供",
            "早期" + "输入",
        ]
        for path in [FULL, EXCLUDED, METHODOLOGY]:
            text = path.read_text(encoding="utf-8-sig")
            for term in terms:
                self.assertNotIn(term, text, path.name)


if __name__ == "__main__":
    unittest.main()
