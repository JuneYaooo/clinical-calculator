"""Case-oriented orchestration for calculator recommendation and execution.

The workbench deliberately keeps case data in memory. It routes against the local
evidence catalog and never treats missing facts as negative findings.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import re
from typing import Any, Mapping
from uuid import uuid4

from .registry import CalculatorRegistry, load_registry
from .release import CLINICALLY_RELEASED_IDS


MAX_CASE_TEXT_LENGTH = 20_000
MAX_SELECTED_CALCULATORS = 10

_GENERIC_SOURCE_URLS = {
    "https://www.mdcalc.com/",
    "https://qxmd.com/calculate/",
    "https://www.merckmanuals.com/professional/pages-with-widgets/clinical-calculators",
}

_INPUT_LABELS = {
    "age": "年龄",
    "age_years": "年龄",
    "sex": "生理性别",
    "height_cm": "身高",
    "weight_kg": "体重",
    "bmi": "BMI",
    "respiratory_rate": "呼吸频率",
    "systolic_bp": "收缩压",
    "diastolic_bp": "舒张压",
    "heart_rate": "心率",
    "temperature_c": "体温",
    "oxygen_saturation_percent": "血氧饱和度",
    "serum_creatinine_mg_dl": "血清肌酐",
    "serum_creatinine_umol_l": "血清肌酐",
    "altered_mentation": "意识状态改变",
    "confusion": "意识模糊",
    "hypertension": "高血压",
    "diabetes": "糖尿病",
    "congestive_heart_failure": "充血性心力衰竭 / 左室功能障碍",
    "stroke_tia_thromboembolism": "卒中、TIA 或血栓栓塞史",
    "vascular_disease": "血管疾病史",
    "bleeding_history": "出血史",
    "antiplatelet_therapy": "抗血小板治疗",
    "hemoglobin_g_dl": "血红蛋白",
    "egfr_ml_min_1_73m2": "估算肾小球滤过率",
    "urea_mmol_l": "尿素",
}

_CHOICE_LABELS = {
    "female": "女性",
    "male": "男性",
    "yes": "是",
    "no": "否",
    "low": "低",
    "medium": "中",
    "high": "高",
}

_UNIT_LABELS = {
    "points": "分",
    "years": "岁",
    "beats/min": "次/分",
    "breaths/min": "次/分",
}

_REVIEW_GAP_LABELS = {
    "missing source version/year": "来源版本或年份未记录",
    "source URL is a generic calculator-library landing page": "当前链接为计算器平台入口，需回溯具体原始来源",
    "interpretation defers thresholds to an external source": "结果阈值仍需结合外部来源核对",
    "custom extension requires independent clinical review": "自定义计算器尚需独立临床审核",
}

_INTERPRETATION_LABELS = {
    "high stroke risk support by CHA2DS2-VASc score; anticoagulation decision depends on current guidelines, patient context, and bleeding risk assessment": (
        "提示卒中风险较高；抗凝决策仍需结合现行指南、患者具体情况及出血风险综合判断。"
    ),
    "low bleeding risk by ORBIT AF bleeding risk score": "ORBIT 评分提示低出血风险。",
    "medium bleeding risk by ORBIT AF bleeding risk score": "ORBIT 评分提示中等出血风险。",
    "high bleeding risk by ORBIT AF bleeding risk score": "ORBIT 评分提示高出血风险。",
    "higher risk; prompt sepsis evaluation is indicated": "提示较高风险，应尽快完成脓毒症相关临床评估。",
    "lower qSOFA risk; continue clinical assessment": "qSOFA 风险较低，但仍需继续结合临床情况评估。",
    "low risk by CURB-65": "CURB-65 提示低风险。",
    "moderate risk by CURB-65": "CURB-65 提示中等风险。",
    "severe/high risk by CURB-65": "CURB-65 提示重症或高风险。",
    "underweight by standard adult BMI categories": "按成人 BMI 分类属于体重过低。",
    "normal adult BMI range": "处于成人 BMI 正常范围。",
    "overweight adult BMI range": "按成人 BMI 分类属于超重。",
    "obesity adult BMI range": "按成人 BMI 分类属于肥胖。",
}

_BOOLEAN_UI_FIELDS = {
    "altered_mentation",
    "antiplatelet_therapy",
    "bleeding_history",
    "confusion",
    "hypertension",
    "diabetes",
    "congestive_heart_failure",
    "stroke_tia_thromboembolism",
    "vascular_disease",
}

# Conservative routing cues. These identify assessment opportunities rather than
# diagnoses; each route remains visible to the user and requires confirmation.
_CASE_INTENT_RULES = (
    {
        "id": "atrial_fibrillation_stroke",
        "label": "房颤相关卒中风险",
        "pattern": re.compile(r"(?:房颤|心房颤动|atrial fibrillation|\bAF\b)", re.I),
        "queries": ("CHA2DS2-VASc 房颤卒中风险",),
        "reason": "病例提到房颤，可核对卒中风险评估工具",
    },
    {
        "id": "atrial_fibrillation_bleeding",
        "label": "房颤抗凝相关出血风险",
        "pattern": re.compile(r"(?:房颤|心房颤动|atrial fibrillation|\bAF\b).*(?:抗凝|出血|卒中|stroke)|(?:抗凝|出血).*(?:房颤|心房颤动)", re.I | re.S),
        "queries": ("HAS-BLED ORBIT 房颤出血风险",),
        "reason": "病例涉及房颤风险评估，可同时核对出血风险工具",
    },
    {
        "id": "pneumonia_severity",
        "label": "肺炎严重度",
        "pattern": re.compile(r"(?:肺炎|community.acquired pneumonia|\bCAP\b)", re.I),
        "queries": ("CURB-65 肺炎严重度",),
        "reason": "病例提到肺炎，可核对肺炎严重度评估工具",
    },
    {
        "id": "sepsis_deterioration",
        "label": "感染相关病情恶化风险",
        "pattern": re.compile(
            r"(?:脓毒|感染性休克|sepsis|感染|肺炎).*(?:低血压|意识|呼吸频率|器官功能|血压\s*\d{2,3}\s*/\s*\d{2,3})"
            r"|(?:低血压|意识改变|血压\s*\d{2,3}\s*/\s*\d{2,3}).*(?:感染|发热|肺炎)",
            re.I | re.S,
        ),
        "queries": ("qSOFA 脓毒症",),
        "reason": "病例同时出现感染线索和病情恶化线索，可核对快速器官功能风险工具",
    },
    {
        "id": "renal_function",
        "label": "肾功能估算",
        "pattern": re.compile(r"(?:肾功能|肌酐|creatinine|\beGFR\b|肌酐清除率|慢性肾病|\bCKD\b)", re.I),
        "queries": ("肾功能 eGFR", "肌酐清除率"),
        "reason": "病例提到肾功能或肌酐，可核对肾功能估算工具",
    },
    {
        "id": "body_size",
        "label": "体型相关指标",
        "pattern": re.compile(r"(?:肥胖|超重|消瘦|营养|体质指数|\bBMI\b)", re.I),
        "queries": ("成人 体质指数",),
        "reason": "病例涉及体型或营养问题，可核对体型相关计算工具",
    },
    {
        "id": "venous_thromboembolism",
        "label": "静脉血栓栓塞风险",
        "pattern": re.compile(r"(?:深静脉血栓|静脉血栓|肺栓塞|\bDVT\b|\bVTE\b|pulmonary embolism)", re.I),
        "queries": ("静脉血栓 风险", "肺栓塞 概率"),
        "reason": "病例提到静脉血栓或肺栓塞，可核对相应概率与风险工具",
    },
)

_PRIVACY_PATTERNS = (
    ("疑似中国大陆身份证号", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("疑似手机号码", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("疑似电子邮箱", re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")),
    (
        "疑似直接身份字段",
        re.compile(r"(?:姓名|身份证|住院号|门诊号|病历号|手机号|联系电话)\s*[:：]", re.I),
    ),
)

_NARRATIVE_FIELDS = {
    "age_years": (
        re.compile(r"(?:年龄\s*[:：]?\s*)?(\d{1,3}(?:\.\d+)?)\s*岁"),
        float,
    ),
    "weight_kg": (
        re.compile(r"(?:体重\s*[:：]?\s*)?(\d{1,3}(?:\.\d+)?)\s*kg\b", re.I),
        float,
    ),
    "height_cm": (
        re.compile(r"(?:身高\s*[:：]?\s*)?(\d{2,3}(?:\.\d+)?)\s*cm\b", re.I),
        float,
    ),
    "respiratory_rate": (
        re.compile(r"(?:呼吸频率|呼吸|RR)\s*[:：]?\s*(\d{1,3}(?:\.\d+)?)\s*(?:次\s*/?\s*分|/min)?", re.I),
        float,
    ),
    "systolic_bp": (
        re.compile(r"(?:收缩压|SBP)\s*[:：]?\s*(\d{2,3}(?:\.\d+)?)", re.I),
        float,
    ),
    "diastolic_bp": (
        re.compile(r"(?:舒张压|DBP)\s*[:：]?\s*(\d{2,3}(?:\.\d+)?)", re.I),
        float,
    ),
    "heart_rate": (
        re.compile(r"(?:心率|HR)\s*[:：]?\s*(\d{1,3}(?:\.\d+)?)", re.I),
        float,
    ),
    "temperature_c": (
        re.compile(r"(?:体温|T)\s*[:：]?\s*(\d{2}(?:\.\d+)?)\s*(?:°?C|℃)?", re.I),
        float,
    ),
}

_EXPLICIT_BOOLEAN_FIELDS = {
    "hypertension": (
        re.compile(r"(?:有|合并|患有|既往有|诊断为)高血压|高血压[（(]?\+", re.I),
        re.compile(r"(?:无|否认|未诊断)高血压|高血压[（(]?-", re.I),
    ),
    "diabetes": (
        re.compile(r"(?:有|合并|患有|既往有|诊断为)糖尿病|糖尿病[（(]?\+", re.I),
        re.compile(r"(?:无|否认|未诊断)糖尿病|糖尿病[（(]?-", re.I),
    ),
    "congestive_heart_failure": (
        re.compile(r"(?:有|合并|患有|既往有)心(?:力)?衰竭|左室功能障碍", re.I),
        re.compile(r"(?:无|否认)心(?:力)?衰竭|无左室功能障碍", re.I),
    ),
    "stroke_tia_thromboembolism": (
        re.compile(r"(?:有|既往|病史).*?(?:脑卒中|卒中|TIA|血栓栓塞)|既往(?:脑卒中|卒中|TIA)", re.I),
        re.compile(r"(?:无|否认)(?:脑卒中|卒中|TIA|血栓栓塞)(?:史|病史)?", re.I),
    ),
    "vascular_disease": (
        re.compile(r"(?:有|既往|合并).*?(?:心肌梗死|外周血管疾病|主动脉粥样硬化)", re.I),
        re.compile(r"(?:无|否认)(?:心肌梗死|外周血管疾病|主动脉粥样硬化)(?:史|病史)?", re.I),
    ),
    "altered_mentation": (
        re.compile(r"(?:意识改变|意识障碍|意识模糊|神志不清)", re.I),
        re.compile(r"(?:意识清楚|神志清楚|无意识改变)", re.I),
    ),
    "confusion": (
        re.compile(r"(?:意识模糊|意识障碍|神志不清)", re.I),
        re.compile(r"(?:意识清楚|神志清楚|无意识模糊)", re.I),
    ),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _event(event: str, detail: str) -> dict[str, str]:
    return {"at": _utc_now(), "event": event, "detail": detail}


def _coerce_scalar(value: str) -> Any:
    value = value.strip()
    lowered = value.casefold()
    if lowered in {"true", "yes", "是", "有", "阳性"}:
        return True
    if lowered in {"false", "no", "否", "无", "阴性"}:
        return False
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def detect_privacy_risks(text: str) -> list[str]:
    """Return warnings for obvious direct identifiers without retaining matches."""

    return [label for label, pattern in _PRIVACY_PATTERNS if pattern.search(text)]


def detect_case_intents(text: str) -> list[dict[str, Any]]:
    """Identify explainable calculator-search intents from case narrative."""

    return [
        {
            "id": rule["id"],
            "label": rule["label"],
            "queries": list(rule["queries"]),
            "reason": rule["reason"],
        }
        for rule in _CASE_INTENT_RULES
        if rule["pattern"].search(text)
    ]


def extract_case_values(text: str) -> dict[str, Any]:
    """Extract only explicit, conservative values from de-identified case text."""

    values: dict[str, Any] = {}
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            values.update(
                (str(key), value)
                for key, value in payload.items()
                if isinstance(value, (str, int, float, bool, list)) or value is None
            )

    assignment = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*[:=]\s*(.+?)\s*$")
    for line in text.splitlines():
        match = assignment.match(line)
        if match:
            values[match.group(1)] = _coerce_scalar(match.group(2))

    for name, (pattern, converter) in _NARRATIVE_FIELDS.items():
        if name in values:
            continue
        match = pattern.search(text)
        if match:
            values[name] = converter(match.group(1))

    paired_bp = re.search(
        r"(?:血压|BP)\s*[:：]?\s*(\d{2,3}(?:\.\d+)?)\s*/\s*(\d{2,3}(?:\.\d+)?)\s*(?:mmHg)?",
        text,
        re.I,
    )
    if paired_bp:
        values.setdefault("systolic_bp", float(paired_bp.group(1)))
        values.setdefault("diastolic_bp", float(paired_bp.group(2)))

    for name, (positive, negative) in _EXPLICIT_BOOLEAN_FIELDS.items():
        if name in values:
            continue
        if negative.search(text):
            values[name] = False
        elif positive.search(text):
            values[name] = True

    if "sex" not in values:
        if re.search(r"(?:性别\s*[:：]?\s*)?(?:男性|男患|男，|男,)", text):
            values["sex"] = "male"
        elif re.search(r"(?:性别\s*[:：]?\s*)?(?:女性|女患|女，|女,)", text):
            values["sex"] = "female"
    return values


def _metadata_input_labels(raw_inputs: str, expected_count: int) -> tuple[str, ...]:
    parts = tuple(
        part.strip(" ,，、")
        for part in re.split(r"[;；\n]+", raw_inputs)
        if part.strip(" ,，、")
    )
    if len(parts) != expected_count or any(len(part) > 40 for part in parts):
        return ()
    return parts


def _input_label(spec: Any, metadata_label: str = "") -> str:
    return (
        spec.item_text
        or spec.description
        or _INPUT_LABELS.get(spec.name)
        or metadata_label
        or spec.name.replace("_", " ")
    )


def _choice_label(value: Any) -> str:
    text = str(value).strip()
    return _CHOICE_LABELS.get(text.casefold(), text.replace("_", " "))


def _display_value(value: Any, unit: str = "") -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if value is None:
        return "未提供"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    rendered = _choice_label(value)
    unit_label = _UNIT_LABELS.get(unit, unit)
    return f"{rendered} {unit_label}".strip()


def _localized_review_gaps(errors: tuple[str, ...]) -> list[str]:
    return [_REVIEW_GAP_LABELS.get(error, error) for error in errors]


def _result_explanation(interpretation: str, metadata_interpretation: str, value: Any) -> str:
    localized = _INTERPRETATION_LABELS.get(interpretation.strip())
    if localized:
        return localized
    if re.search(r"[\u3400-\u9fff]", interpretation):
        return interpretation.strip()
    if isinstance(value, (int, float)):
        numeric = f"{float(value):g}"
        for line in metadata_interpretation.splitlines():
            candidate = line.strip()
            if re.match(rf"^{re.escape(numeric)}\s*(?:分值|分|[:：])", candidate):
                return candidate.replace("\t", " ")
    if metadata_interpretation and "具体单位、正常范围" not in metadata_interpretation:
        first_line = metadata_interpretation.splitlines()[0].strip()
        if first_line:
            return first_line
    return "计算已完成；结果需结合适用人群、当前指南和患者具体情况解释。"


def _input_payload(
    spec: Any,
    extracted: Mapping[str, Any],
    metadata_label: str = "",
) -> dict[str, Any]:
    payload = asdict(spec)
    payload["ui_type"] = (
        "boolean"
        if spec.value_type == "boolean" or spec.name in _BOOLEAN_UI_FIELDS
        else spec.value_type
    )
    payload["label"] = _input_label(spec, metadata_label)
    payload["choice_labels"] = {
        choice: _choice_label(choice) for choice in spec.choices
    }
    payload["available"] = spec.name in extracted
    if payload["available"]:
        payload["value"] = extracted[spec.name]
    return payload


def _candidate_payload(
    result: Any,
    extracted: Mapping[str, Any],
    rank: int,
    *,
    reasons: tuple[str, ...] = (),
    route_queries: tuple[str, ...] = (),
) -> dict[str, Any]:
    skill = result.skill
    metadata = skill.metadata
    review = skill.medical_review_check()
    metadata_labels = _metadata_input_labels(metadata.inputs, len(skill.input_schema))
    inputs = [
        _input_payload(
            spec,
            extracted,
            metadata_labels[index] if metadata_labels else "",
        )
        for index, spec in enumerate(skill.input_schema)
    ]
    return {
        "rank": rank,
        "id": metadata.id,
        "name_cn": metadata.name_cn,
        "name_en": metadata.name_en,
        "category": metadata.category,
        "scenario": metadata.scenario,
        "purpose": metadata.purpose,
        "implementation_level": skill.implementation_level,
        "match": result.match.as_dict(),
        "recommendation_reasons": list(reasons),
        "route_queries": list(route_queries),
        "inputs": inputs,
        "missing_inputs": [item["name"] for item in inputs if not item["available"]],
        "formula": metadata.formula,
        "interpretation": metadata.interpretation,
        "clinical_note": metadata.clinical_note,
        "evidence": {
            "source": metadata.source,
            "source_type": metadata.source_type,
            "source_url": metadata.source_url,
            "version": metadata.version,
            "tier": metadata.evidence_tier,
            "source_specific": metadata.source_url not in _GENERIC_SOURCE_URLS,
        },
        "review": {
            "ok": review.ok,
            "gaps": _localized_review_gaps(review.errors),
            "clinically_released": metadata.id in CLINICALLY_RELEASED_IDS,
        },
    }


def recommend_for_case(
    query: str,
    case_text: str = "",
    *,
    supplied_values: Mapping[str, Any] | None = None,
    limit: int = 6,
    registry: CalculatorRegistry | None = None,
) -> dict[str, Any]:
    """Recommend executable calculators and report all unconfirmed inputs."""

    query = query.strip()
    case_text = case_text.strip()
    if not query and not case_text:
        raise ValueError("请填写评估目标或脱敏病例")
    if len(case_text) > MAX_CASE_TEXT_LENGTH:
        raise ValueError(f"病例文本不能超过 {MAX_CASE_TEXT_LENGTH} 个字符")
    try:
        limit = max(1, min(int(limit), 12))
    except (TypeError, ValueError) as exc:
        raise ValueError("候选数量必须是整数") from exc
    registry = registry or load_registry()
    extracted = extract_case_values(case_text)
    if supplied_values is not None and not isinstance(supplied_values, Mapping):
        raise ValueError("结构化病例值必须是对象")
    extracted.update(supplied_values or {})
    intents = detect_case_intents(case_text)
    search_routes: list[tuple[str, str]] = []
    if query:
        search_routes.append((query, "使用者指定的评估目标"))
    for intent in intents:
        search_routes.extend((route_query, intent["reason"]) for route_query in intent["queries"])

    combined: dict[str, dict[str, Any]] = {}
    suggestions: list[str] = []
    per_route_limit = max(4, min(limit, 8))
    route_results: list[list[str]] = []
    for route_index, (route_query, reason) in enumerate(search_routes):
        response = registry.search_runnable_detailed(route_query, limit=per_route_limit)
        suggestions.extend(response.suggestions)
        route_ids: list[str] = []
        best_coverage = response.results[0].match.coverage if response.results else 0
        route_matches = [
            result
            for result in response.results
            if result.match.coverage >= max(0.2, best_coverage * 0.45)
        ][:2]
        for route_rank, result in enumerate(route_matches):
            calculator_id = result.skill.metadata.id
            route_ids.append(calculator_id)
            current = combined.get(calculator_id)
            if current is None:
                combined[calculator_id] = {
                    "result": result,
                    "best_score": result.match.score,
                    "reasons": [reason],
                    "queries": [route_query],
                    "first_route": route_index,
                    "first_rank": route_rank,
                }
            else:
                if result.match.score > current["best_score"]:
                    current["result"] = result
                    current["best_score"] = result.match.score
                if reason not in current["reasons"]:
                    current["reasons"].append(reason)
                if route_query not in current["queries"]:
                    current["queries"].append(route_query)
        route_results.append(route_ids)

    # Interleave routes so every detected clinical direction gets a representative
    # before secondary results from one broad search dominate the list.
    ranked_ids: list[str] = []
    for route_rank in range(per_route_limit):
        for route_ids in route_results:
            if route_rank < len(route_ids) and route_ids[route_rank] not in ranked_ids:
                ranked_ids.append(route_ids[route_rank])
    ranked = [combined[calculator_id] for calculator_id in ranked_ids[:limit]]
    status = "ok" if ranked else "no_match"
    mode = "guided" if query else "case_driven"
    display_query = query or "病例自动发现"
    session_id = uuid4().hex
    events = [
        _event("case_received", "病例数据仅在当前进程内存中处理，不写入文件"),
        _event("values_extracted", f"从明确陈述中识别 {len(extracted)} 个结构化字段"),
        _event(
            "case_intents_detected",
            f"识别 {len(intents)} 个可解释的评估方向",
        ),
        _event(
            "catalog_searched",
            f"通过 {len(search_routes)} 条检索路径查询本地目录，合并为 {len(ranked)} 个候选",
        ),
    ]
    return {
        "session_id": session_id,
        "status": status,
        "mode": mode,
        "query": display_query,
        "scope": "local_evidence_catalog",
        "detected_intents": intents,
        "privacy_warnings": detect_privacy_risks(case_text),
        "extracted_values": extracted,
        "candidates": [
            _candidate_payload(
                item["result"],
                extracted,
                rank,
                reasons=tuple(item["reasons"]),
                route_queries=tuple(item["queries"]),
            )
            for rank, item in enumerate(ranked, start=1)
        ],
        "suggestions": list(dict.fromkeys(suggestions))[:5],
        "audit_log": events,
    }


def calculate_selected(
    calculator_inputs: Mapping[str, Mapping[str, Any]],
    *,
    session_id: str = "",
    registry: CalculatorRegistry | None = None,
) -> dict[str, Any]:
    """Run explicitly selected calculators with reproducible input snapshots."""

    if not calculator_inputs:
        raise ValueError("至少选择一个计算器")
    if len(calculator_inputs) > MAX_SELECTED_CALCULATORS:
        raise ValueError(f"一次最多运行 {MAX_SELECTED_CALCULATORS} 个计算器")
    registry = registry or load_registry()
    events = [_event("selection_confirmed", f"使用者确认 {len(calculator_inputs)} 个计算器")]
    runs: list[dict[str, Any]] = []

    for calculator_id, provided in calculator_inputs.items():
        if not isinstance(provided, Mapping):
            raise ValueError(f"{calculator_id} 的输入必须是对象")
        try:
            skill = registry.get(calculator_id)
        except KeyError as exc:
            raise ValueError(f"未知计算器 ID: {calculator_id}") from exc
        expected_names = {spec.name for spec in skill.input_schema}
        snapshot = {name: provided[name] for name in expected_names if name in provided}
        missing = [name for name in skill.required_inputs if name not in snapshot]
        trace = [
            {"step": 1, "kind": "input", "detail": "冻结本次输入快照", "data": snapshot},
            {
                "step": 2,
                "kind": "validation",
                "detail": "检查必填项、类型、范围和可选值",
                "data": {"missing": missing},
            },
            {
                "step": 3,
                "kind": "formula",
                "detail": skill.metadata.formula,
                "data": None,
            },
        ]
        result = skill.run(snapshot)
        trace.append(
            {
                "step": 4,
                "kind": "result",
                "detail": result.message,
                "data": {"value": result.value, "unit": result.unit},
            }
        )
        review = skill.medical_review_check()
        metadata_labels = _metadata_input_labels(
            skill.metadata.inputs, len(skill.input_schema)
        )
        input_display = [
            {
                "name": spec.name,
                "label": _input_label(
                    spec,
                    metadata_labels[index] if metadata_labels else "",
                ),
                "value": snapshot.get(spec.name),
                "display_value": _display_value(
                    snapshot.get(spec.name), spec.unit
                ),
                "unit": spec.unit,
            }
            for index, spec in enumerate(skill.input_schema)
            if spec.name in snapshot
        ]
        status_label = {
            "implemented": "计算完成",
            "partial": "已完成中间计算",
            "missing_inputs": "需要补充数据",
            "invalid_inputs": "输入需要核对",
        }.get(result.status, result.status)
        review_gaps = _localized_review_gaps(review.errors)
        runs.append(
            {
                "calculator_id": calculator_id,
                "name_cn": skill.metadata.name_cn,
                "name_en": skill.metadata.name_en,
                "status": result.status,
                "message": result.message,
                "value": result.value,
                "unit": result.unit,
                "interpretation": result.interpretation,
                "clinical_explanation": _result_explanation(
                    result.interpretation,
                    skill.metadata.interpretation,
                    result.value,
                ),
                "reference_interpretation": skill.metadata.interpretation,
                "status_label": status_label,
                "required_inputs": list(result.required_inputs),
                "input_snapshot": snapshot,
                "input_display": input_display,
                "formula": skill.metadata.formula,
                "source": {
                    "name": skill.metadata.source,
                    "url": skill.metadata.source_url,
                    "version": skill.metadata.version,
                },
                "review": {
                    "ok": review.ok,
                    "gaps": review_gaps,
                    "clinically_released": (
                        skill.metadata.id in CLINICALLY_RELEASED_IDS
                    ),
                    "label": (
                        "来源信息已通过自动检查"
                        if review.ok
                        else "使用前需核对来源与版本"
                    ),
                },
                "trace": trace,
            }
        )
        events.append(_event("calculator_executed", f"{calculator_id}: {result.status}"))

    events.append(_event("result_bundle_created", "生成可复核结果、输入快照与计算轨迹"))
    return {
        "session_id": session_id or uuid4().hex,
        "status": "completed" if all(run["status"] in {"implemented", "partial"} for run in runs) else "needs_input",
        "runs": runs,
        "audit_log": events,
    }
