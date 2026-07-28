#!/usr/bin/env python3
"""Generate bilingual Markdown catalogs for built-in executable calculators."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import html
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from clinical_calculators import load_registry  # noqa: E402


CATEGORY_TRANSLATIONS = {
    "急诊与重症医学": "Emergency & Critical Care Medicine",
    "心血管医学": "Cardiovascular Medicine",
    "呼吸与睡眠医学": "Respiratory & Sleep Medicine",
    "消化、肝胆与营养": "Gastroenterology, Hepatobiliary Medicine & Nutrition",
    "肾脏与泌尿生殖": "Nephrology & Urogenital Medicine",
    "内分泌、代谢与电解质": "Endocrinology, Metabolism & Electrolytes",
    "感染病学": "Infectious Diseases",
    "儿科学": "Pediatrics",
    "妇产科学": "Obstetrics & Gynecology",
    "神经、精神与老年医学": "Neurology, Psychiatry & Geriatric Medicine",
    "血液、肿瘤与免疫/过敏": "Hematology, Oncology & Immunology/Allergy",
    "创伤、中毒与职业损伤": "Trauma, Toxicology & Occupational Injury",
    "临床药理、诊断统计与通用工具": "Clinical Pharmacology, Diagnostic Statistics & General Tools",
    "眼科": "Ophthalmology",
    "耳鼻喉、头颈与听力言语": "Otolaryngology, Head & Neck, Hearing & Speech",
    "皮肤科": "Dermatology",
    "风湿免疫": "Rheumatology & Immunology",
    "麻醉、疼痛与围术期医学": "Anesthesia, Pain & Perioperative Medicine",
    "骨科、运动医学与康复": "Orthopedics, Sports Medicine & Rehabilitation",
    "肿瘤学、放疗与姑息医学": "Oncology, Radiation Oncology & Palliative Medicine",
    "移植医学": "Transplant Medicine",
    "护理、安全与功能评估": "Nursing, Safety & Functional Assessment",
    "口腔、牙周与颌面医学": "Oral, Periodontal & Maxillofacial Medicine",
    "放射影像与核医学": "Radiology & Nuclear Medicine",
    "儿科亚专科与新生儿": "Pediatric Subspecialties & Neonatology",
    "妇产高危与生殖医学": "High-Risk Obstetrics & Reproductive Medicine",
    "心衰、心电与血管医学": "Heart Failure, Electrocardiology & Vascular Medicine",
    "消化内镜、IBD与胰胆疾病": "GI Endoscopy, IBD & Pancreatobiliary Disease",
    "肝衰竭、门脉高压与脂肪肝": "Liver Failure, Portal Hypertension & Fatty Liver Disease",
    "肾脏AKI、透析充分性与结石": "Nephrology: AKI, Dialysis Adequacy & Stones",
    "感染、HIV/TB与抗菌药管理": "Infectious Diseases, HIV/TB & Antimicrobial Stewardship",
    "急诊毒理、环境与高压氧医学": "Emergency Toxicology, Environmental & Hyperbaric Medicine",
    "内分泌、糖尿病足与骨代谢": "Endocrinology, Diabetic Foot & Bone Metabolism",
    "神经肌病、癫痫、多发性硬化与睡眠": "Neuromuscular Disease, Epilepsy, Multiple Sclerosis & Sleep",
    "妇科肿瘤、生殖内分泌与盆底": "Gynecologic Oncology, Reproductive Endocrinology & Pelvic Floor",
    "男科、泌尿肿瘤与下尿路功能": "Andrology, Urologic Oncology & Lower Urinary Tract Function",
    "血栓、止血、输血与血液专病": "Thrombosis, Hemostasis, Transfusion & Hematologic Disorders",
    "临床营养、肥胖与代谢手术": "Clinical Nutrition, Obesity & Metabolic Surgery",
    "遗传、罕见病与公共卫生筛查": "Genetics, Rare Diseases & Public Health Screening",
    "急诊、院前与灾难医学": "Emergency, Prehospital & Disaster Medicine",
    "外科、围术期与质量评估": "Surgery, Perioperative Care & Quality Assessment",
    "呼吸、睡眠与肺血管医学": "Respiratory, Sleep & Pulmonary Vascular Medicine",
    "消化、肝胆、内镜与营养": "Gastroenterology, Hepatobiliary Medicine, Endoscopy & Nutrition",
    "肾脏、泌尿与男科": "Nephrology, Urology & Andrology",
    "感染、抗菌药与旅行医学": "Infection, Antimicrobials & Travel Medicine",
    "妇产、儿科与新生儿": "Obstetrics, Pediatrics & Neonatology",
    "神经、精神、老年与行为医学": "Neurology, Psychiatry, Geriatrics & Behavioral Medicine",
    "肿瘤、放疗与姑息": "Oncology, Radiation Oncology & Palliative Care",
    "血液、免疫、风湿与皮肤": "Hematology, Immunology, Rheumatology & Dermatology",
    "影像、实验室、遗传与公共卫生": "Imaging, Laboratory Medicine, Genetics & Public Health",
    "重症、麻醉、疼痛与姑息": "Critical Care, Anesthesia, Pain & Palliative Care",
    "骨科、运动医学与康复扩展": "Orthopedics, Sports Medicine & Extended Rehabilitation",
    "眼耳鼻喉、口腔与头颈扩展": "Ophthalmology, ENT, Oral & Head and Neck Extensions",
    "公共卫生、职业医学与生活方式": "Public Health, Occupational Medicine & Lifestyle",
    "临床药理、药物剂量与TDM扩展": "Clinical Pharmacology, Drug Dosing & Extended TDM",
    "公共卫生、预防医学与筛查扩展": "Public Health, Preventive Medicine & Extended Screening",
}


def cell(value: str) -> str:
    return html.escape(value.strip()).replace("|", "&#124;").replace("\n", "<br>")


def source_link(name: str, url: str) -> str:
    return f'<a href="{html.escape(url, quote=True)}">{cell(name)}</a>'


def render_catalog(language: str) -> str:
    registry = load_registry(include_custom=False)
    grouped: dict[str, list[object]] = defaultdict(list)
    for skill in registry.skills:
        grouped[skill.metadata.category].append(skill)

    categories = list(grouped)
    missing_translations = set(categories) - set(CATEGORY_TRANSLATIONS)
    extra_translations = set(CATEGORY_TRANSLATIONS) - set(categories)
    if missing_translations or extra_translations:
        raise ValueError(
            "category translation map is out of sync: "
            f"missing={sorted(missing_translations)}, extra={sorted(extra_translations)}"
        )

    levels = Counter(skill.implementation_level for skill in registry.skills)
    if language == "zh":
        lines = [
            '<p align="center">',
            '  <strong>简体中文</strong> · <a href="./CALCULATORS_EN.md">English</a>',
            "</p>",
            "",
            "# 已支持的计算器",
            "",
            f"本目录列出当前 **{len(registry.skills)}** 个内置可执行计算器，覆盖 **{len(registry.unique_names())}** 个唯一中文名称，并按注册表中的专业类别分组。",
            "",
            "> 来源列展示仓库当前记录的来源名称与链接。来源可追溯不等于已经通过独立临床审核；使用时仍需核对版本、适用人群、授权状态和最新指南。",
            "",
            "## 实现类型",
            "",
            "| 类型 | 数量 | 含义 |",
            "| --- | ---: | --- |",
            f"| 完整 | {levels['complete']} | 可以从声明的原始输入完成计算 |",
            f"| 中间步骤 | {levels['partial']} | 需要预评分组件或上游结果，但本地步骤可执行 |",
            "",
            "## 专业类别",
            "",
            "| 类别 | 数量 |",
            "| --- | ---: |",
        ]
    else:
        lines = [
            '<p align="center">',
            '  <a href="./CALCULATORS.md">简体中文</a> · <strong>English</strong>',
            "</p>",
            "",
            "# Supported Calculators",
            "",
            f"This catalog lists all **{len(registry.skills)}** built-in executable calculators, covering **{len(registry.unique_names())}** unique calculator names and grouped by their registry specialty.",
            "",
            "> The source column shows the source name and link currently recorded by the repository. A traceable source does not mean independent clinical approval; always verify the version, intended population, content rights, and current guidance.",
            "",
            "## Implementation types",
            "",
            "| Type | Count | Meaning |",
            "| --- | ---: | --- |",
            f"| Complete | {levels['complete']} | Calculates from the declared original inputs |",
            f"| Intermediate | {levels['partial']} | Requires pre-scored components or upstream results, but the local step is executable |",
            "",
            "## Specialties",
            "",
            "| Specialty | Count |",
            "| --- | ---: |",
        ]

    for index, category in enumerate(categories, 1):
        label = category if language == "zh" else CATEGORY_TRANSLATIONS[category]
        lines.append(f'| <a href="#category-{index:02d}">{cell(label)}</a> | {len(grouped[category])} |')

    for index, category in enumerate(categories, 1):
        label = category if language == "zh" else CATEGORY_TRANSLATIONS[category]
        lines.extend(["", f'<a id="category-{index:02d}"></a>', f"## {cell(label)}（{len(grouped[category])}）" if language == "zh" else f"## {cell(label)} ({len(grouped[category])})", ""])
        if language == "zh":
            lines.extend([
                "| ID | 计算器 | 英文名称 | 实现 | 来源 |",
                "| --- | --- | --- | --- | --- |",
            ])
        else:
            lines.extend([
                "| ID | Calculator | Implementation | Source |",
                "| --- | --- | --- | --- |",
            ])
        for skill in grouped[category]:
            metadata = skill.metadata
            level = (
                "完整" if skill.implementation_level == "complete" else "中间步骤"
            ) if language == "zh" else (
                "Complete" if skill.implementation_level == "complete" else "Intermediate"
            )
            if language == "zh":
                lines.append(
                    f"| {cell(metadata.id)} | {cell(metadata.name_cn)} | {cell(metadata.name_en)} | "
                    f"{level} | {source_link(metadata.source, metadata.source_url)} |"
                )
            else:
                lines.append(
                    f"| {cell(metadata.id)} | {cell(metadata.name_en)} | {level} | "
                    f"{source_link(metadata.source, metadata.source_url)} |"
                )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if checked-in catalogs are stale")
    args = parser.parse_args()
    outputs = {
        ROOT / "CALCULATORS.md": render_catalog("zh"),
        ROOT / "CALCULATORS_EN.md": render_catalog("en"),
    }
    stale = []
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path.name)
        else:
            path.write_text(content, encoding="utf-8")
    if stale:
        print(f"stale generated catalogs: {', '.join(stale)}", file=sys.stderr)
        return 1
    if not args.check:
        print("generated CALCULATORS.md and CALCULATORS_EN.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
