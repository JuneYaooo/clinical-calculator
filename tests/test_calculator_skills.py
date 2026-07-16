import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CalculatorSkillsTest(unittest.TestCase):
    def test_registry_loads_every_effective_calculator_as_a_skill(self):
        from clinical_calculators.registry import load_registry

        with (ROOT / "clinical_calculator_inventory_full.csv").open(encoding="utf-8-sig", newline="") as f:
            source_rows = list(csv.DictReader(f))

        registry = load_registry(ROOT / "clinical_calculator_inventory_full.csv")

        self.assertEqual(len(registry) + len(registry.aliases), len(source_rows))
        effective_names = {
            row["中文名称"] for row in source_rows if row["id"] not in registry.aliases
        }
        self.assertEqual(len(registry.unique_names()), len(effective_names))
        for skill in registry.skills:
            check = skill.self_check()
            self.assertTrue(check.ok, f"{skill.metadata.id}: {check.errors}")

    def test_registry_exposes_inventory_and_implementation_summary(self):
        from clinical_calculators.registry import load_registry

        registry = load_registry(ROOT / "clinical_calculator_inventory_full.csv")
        summary = registry.summary()

        self.assertEqual(summary["total_rows"], 1054)
        self.assertEqual(summary["inventory_rows"], 1138)
        self.assertEqual(summary["merged_alias_rows"], 84)
        self.assertEqual(summary["unique_chinese_names"], 981)
        self.assertEqual(summary["implemented_rows"], 643)
        self.assertEqual(summary["implemented_unique_names"], 570)
        self.assertEqual(summary["metadata_only_rows"], 411)
        self.assertEqual(
            summary["catalog_layers"],
            {
                "executable": 643,
                "source_candidate": 110,
                "guidance_knowledge": 206,
                "controlled_content": 95,
            },
        )
        for implemented_name in (
            "SOFA评分",
            "HEART胸痛评分",
            "Glasgow-Blatchford上消化道出血评分",
            "HOMA-IR胰岛素抵抗指数",
            "RCRI围手术期心脏风险指数",
            "肺容积multicalc",
            "PaO2 / FIO2 比值（MODS计算）",
            "Barthel日常生活活动指数",
            "儿童维持液量的计算",
            "卡铂Calvert剂量",
            "碳酸氢钠补碱估算",
            "Mentzer指数",
            "代谢综合征判定",
            "MELD 3.0评分",
            "预产期与孕周计算",
            "视力LogMAR换算",
            "特应性皮炎SCORAD评分",
            "ABI踝肱指数",
            "Mayo溃疡性结肠炎评分",
            "皮肤软组织感染坏死性筋膜炎风险",
            "IMPROVE住院VTE风险评分",
            "Charlson合并症指数",
            "Khorana肿瘤相关VTE风险",
            "PRAM儿童哮喘严重度",
            "Atlanta急性胰腺炎严重度分类",
            "龋失补指数",
            "克罗恩病活动指数（CDAI）",
            "CLL-IPI慢淋预后指数",
            "NEXUS胸部影像规则",
            "AKIN急性肾损伤分期",
            "骨质疏松T值解释",
            "Maddrey以外酒精性肝炎感染风险辅助",
            "眼外伤评分",
            "强直性脊柱炎疾病活动评分",
            "RECIST 1.1实体瘤疗效评价",
            "姑息预后评分",
            "简化内镜克罗恩评分",
            "估计胎儿体重Hadlock公式",
            "H2FPEF心衰保留射血分数评分",
            "结核感染TST解释",
            "DECAF COPD急性加重死亡风险",
            "营养风险指数",
            "Berg平衡量表",
            "DAPSA银屑病关节炎活动度",
            "功能性步行分级",
            "CKD-EPI肌酐-胱抑素C联合方程",
            "Rotterdam CT评分",
            "LEMON困难气道评估",
            "House-Brackmann面神经分级",
            "APACHE II评分",
            "EuroSCORE评分心脏手术风险评估（附加版）",
            "SAPS II简化急性生理评分",
            "鼻窦炎生活质量评分",
            "RIETE肺栓塞出血风险",
            "扩展残疾状态量表",
            "IOTA简单规则",
            "AUDIT酒精使用障碍识别测试",
            "HFA-PEFF诊断评分",
            "Rutherford慢性肢体缺血分级",
            "腹膜透析Kt/V",
            "Penn State危重症能量公式",
            "主动脉瓣狭窄严重度",
            "哮喘控制测试",
            "BCLC肝癌分期",
            "锂中毒EXTRIP透析建议",
            "DASH停抗凝后VTE复发风险",
            "重症疟疾WHO标准",
            "WHO登革热警示征象",
            "DN4神经病理性疼痛问卷",
            "MI溶栓治疗颅内出血风险",
            "PTCA死亡率预测",
            "不稳定型心绞痛结局预测",
            "非Q波心肌梗死预测",
            "疾病预防控制中心女孩体重身高百分位数（77-121cm高）",
            "女孩（2 - 20岁）的体质量指数百分比",
        ):
            self.assertIn(implemented_name, summary["implemented_names"])

    def test_implemented_calculators_are_discovered_from_subdirectories(self):
        from clinical_calculators.registry import load_registry

        registry = load_registry(ROOT / "clinical_calculator_inventory_full.csv")

        self.assertTrue(registry.implemented())
        for skill in registry.implemented():
            self.assertTrue(
                skill.implementation_module.startswith("clinical_calculators.calculators."),
                skill.metadata.name_cn,
            )

    def test_registry_search_finds_calculators_by_name_category_and_scenario(self):
        from clinical_calculators.registry import load_registry

        registry = load_registry(ROOT / "clinical_calculator_inventory_full.csv")

        chinese_matches = registry.search("体质指数")
        self.assertTrue(chinese_matches)
        self.assertEqual(chinese_matches[0].metadata.name_cn, "体质指数（凯特勒指数）")

        english_matches = registry.search("Glasgow")
        self.assertTrue(english_matches)
        self.assertEqual(english_matches[0].metadata.name_en, "Glasgow Coma Scale")

        cardiovascular = registry.by_category("心血管医学")
        self.assertTrue(cardiovascular)
        self.assertTrue(all(skill.metadata.category == "心血管医学" for skill in cardiovascular))

        self.assertEqual(len(registry.by_catalog_layer("executable")), 643)
        self.assertEqual(len(registry.by_catalog_layer("source_candidate")), 110)
        self.assertTrue(
            all(
                skill.catalog_layer == "guidance_knowledge"
                for skill in registry.search_layer("筛查", "guidance_knowledge", limit=None)
            )
        )

    def test_merged_alias_ids_resolve_to_one_canonical_skill(self):
        from clinical_calculators.registry import load_registry

        registry = load_registry(ROOT / "clinical_calculator_inventory_full.csv")

        self.assertEqual(registry.alias_target("CALC-0064"), "CALC-0039")
        self.assertIs(registry.get("CALC-0064"), registry.get("CALC-0039"))
        self.assertNotIn("CALC-0064", {skill.metadata.id for skill in registry.skills})
        self.assertEqual(registry.alias_target("CALC-0185"), "CALC-0187")
        self.assertEqual(registry.alias_target("CALC-0186"), "CALC-0187")
        self.assertEqual(registry.alias_target("CALC-0559"), "CALC-0111")
        self.assertIs(registry.get("CALC-0185"), registry.get("CALC-0187"))
        self.assertIs(registry.get("CALC-0559"), registry.get("CALC-0111"))

    def test_registry_entries_are_runnable_without_claiming_unimplemented_formulas(self):
        from clinical_calculators.registry import load_registry

        registry = load_registry(ROOT / "clinical_calculator_inventory_full.csv")

        for skill in registry.skills:
            result = skill.run({})
            self.assertIn(result.status, {"implemented", "missing_inputs", "needs_formula_implementation"})
            self.assertTrue(result.message)
            self.assertEqual(result.calculator_id, skill.metadata.id)

    def test_representative_formula_calculators_compute_expected_values(self):
        from clinical_calculators.registry import load_registry

        registry = load_registry(ROOT / "clinical_calculator_inventory_full.csv")

        bmi = registry.get("体质指数（凯特勒指数）").run({"weight_kg": 70, "height_cm": 175})
        self.assertEqual(bmi.status, "implemented")
        self.assertAlmostEqual(bmi.value, 22.86, places=2)
        self.assertEqual(bmi.unit, "kg/m^2")

        anion_gap = registry.get("阴离子间隙").run({"sodium": 140, "chloride": 104, "bicarbonate": 24})
        self.assertEqual(anion_gap.status, "implemented")
        self.assertAlmostEqual(anion_gap.value, 12.0, places=2)
        self.assertEqual(anion_gap.unit, "mEq/L")

        corrected_na = registry.get("高血糖时低钠的处理").run({"measured_sodium": 130, "glucose_mg_dl": 500})
        self.assertEqual(corrected_na.status, "implemented")
        self.assertAlmostEqual(corrected_na.value, 136.4, places=2)
        self.assertEqual(corrected_na.unit, "mEq/L")

        qt = registry.get("QT间期校正 (EKG)").run({"qt_seconds": 0.40, "heart_rate": 60})
        self.assertEqual(qt.status, "implemented")
        self.assertAlmostEqual(qt.value, 0.40, places=2)
        self.assertEqual(qt.unit, "seconds")

        pediatric_fev1 = registry.get("CALC-0068").run({"age_years": 10, "height_m": 1.3})
        self.assertEqual(pediatric_fev1.status, "implemented")
        self.assertAlmostEqual(pediatric_fev1.value, 1.6643, places=4)
        self.assertEqual(pediatric_fev1.unit, "L")

        carboplatin = registry.get("CALC-1079").run({"target_auc_mg_ml_min": 5, "gfr_ml_min": 80})
        self.assertEqual(carboplatin.status, "implemented")
        self.assertEqual(carboplatin.value, 525)
        self.assertEqual(carboplatin.unit, "mg")

        metabolic_syndrome = registry.get("CALC-0204").run(
            {
                "sex": "female",
                "waist_circumference_cm": 90,
                "triglycerides_mg_dl": 140,
                "hdl_mg_dl": 45,
                "systolic_bp": 132,
                "diastolic_bp": 80,
                "fasting_glucose_mg_dl": 101,
            }
        )
        self.assertEqual(metabolic_syndrome.status, "implemented")
        self.assertTrue(metabolic_syndrome.value["metabolic_syndrome"])
        self.assertEqual(metabolic_syndrome.value["criteria_met"], 4)

        meld3 = registry.get("CALC-0120").run(
            {
                "bilirubin_mg_dl": 3,
                "inr": 2,
                "creatinine_mg_dl": 1.5,
                "sodium_mEq_l": 130,
                "albumin_g_dl": 3.0,
                "sex": "female",
            }
        )
        self.assertEqual(meld3.status, "implemented")
        self.assertAlmostEqual(meld3.value, 27.6056, places=4)

        due_date = registry.get("CALC-0266").run({"lmp_date": "2026-01-01", "as_of_date": "2026-03-12"})
        self.assertEqual(due_date.status, "implemented")
        self.assertEqual(due_date.value["estimated_due_date"], "2026-10-08")

        abi = registry.get("CALC-0533").run(
            {
                "left_dorsalis_pedis_sbp": 92,
                "left_posterior_tibial_sbp": 100,
                "right_brachial_sbp": 130,
                "left_brachial_sbp": 120,
            }
        )
        self.assertEqual(abi.status, "implemented")
        self.assertEqual(abi.value, 0.7692)


if __name__ == "__main__":
    unittest.main()
