import csv
import unittest
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "clinical_calculator_inventory_full.csv"
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

        self.assertEqual(len(rows), 727)
        self.assertEqual(len({row["中文名称"] for row in rows}), 571)
        for row in rows:
            for field in required_fields:
                self.assertTrue(row[field].strip(), f"{row['id']} missing {field}")
            self.assertTrue(row["来源链接"].startswith("http"), row["id"])
            self.assertFalse(row["真实性层级"].startswith("D："), row["id"])

    def test_inventory_contains_only_executable_calculators_and_aliases(self):
        from clinical_calculators.registry import load_registry

        rows = read_rows(FULL)
        registry = load_registry(include_custom=False)
        retained_ids = {skill.metadata.id for skill in registry.skills} | set(registry.aliases)

        self.assertEqual({row["id"] for row in rows}, retained_ids)
        self.assertTrue(all(skill.implemented for skill in registry.skills))

    def test_registry_rejects_inventory_rows_without_local_implementation(self):
        from clinical_calculators.registry import load_registry

        rows = read_rows(FULL)
        unsupported = {
            **rows[0],
            "id": "NOT-IN-REGISTRY",
            "中文名称": "未注册测试计算器",
            "英文名称": "Unregistered Test Calculator",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=unsupported)
                writer.writeheader()
                writer.writerow(unsupported)

            with self.assertRaisesRegex(ValueError, "without local implementation"):
                load_registry(path, include_custom=False)

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
        for path in [FULL, METHODOLOGY]:
            text = path.read_text(encoding="utf-8-sig")
            for term in terms:
                self.assertNotIn(term, text, path.name)


if __name__ == "__main__":
    unittest.main()
