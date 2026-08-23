"use strict";

const state = {
  recommendation: null,
  calculation: null,
  selected: new Set(),
  auditLog: [],
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const unitLabels = {
  points: "分",
  years: "岁",
  "beats/min": "次/分",
  "breaths/min": "次/分",
};
const auditEventLabels = {
  case_received: "收到脱敏病例",
  values_extracted: "识别病例数据",
  case_intents_detected: "识别评估方向",
  catalog_searched: "检索计算器目录",
  selection_confirmed: "确认使用量表",
  calculator_executed: "完成计算",
  result_bundle_created: "生成复核记录",
};

function element(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(options)) {
    if (value === undefined || value === null) continue;
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "htmlFor") node.htmlFor = value;
    else if (key.startsWith("data")) node.dataset[key.slice(4).toLowerCase()] = value;
    else if (key in node) node[key] = value;
    else node.setAttribute(key, value);
  }
  for (const child of Array.isArray(children) ? children : [children]) {
    if (child != null) node.append(child);
  }
  return node;
}

function setError(target, message) {
  target.textContent = message || "";
  target.hidden = !message;
}

function setLoading(loading) {
  $("#recommend-button").disabled = loading;
  $("#recommend-button span").textContent = loading ? "正在分析病例与目录…" : "分析病例并生成建议";
  if (loading) $("#empty-state").hidden = true;
  $("#loading-state").hidden = !loading;
  if (loading) $$(".stage").forEach((stage) => { stage.hidden = true; });
}

function showStage(name) {
  document.body.dataset.stage = name;
  document.body.classList.remove("show-case");
  $("#empty-state").hidden = true;
  $("#loading-state").hidden = true;
  $$(".stage").forEach((stage) => { stage.hidden = stage.id !== `${name}-stage`; });
  const order = ["recommendations", "inputs", "results"];
  const index = order.indexOf(name);
  $$(".progress-item").forEach((item, itemIndex) => {
    item.classList.toggle("is-active", itemIndex === index);
    item.classList.toggle("is-complete", itemIndex < index);
    item.disabled = itemIndex > index || (itemIndex === 1 && !state.selected.size) || (itemIndex === 2 && !state.calculation);
  });
}

function statusBadge(text, kind = "") {
  return element("span", { className: `status-label ${kind}`, text });
}

function sourceLink(candidate) {
  const link = element("a", {
    href: candidate.evidence.source_url,
    target: "_blank",
    rel: "noreferrer",
    text: candidate.evidence.source || candidate.evidence.source_url,
  });
  return link;
}

function renderCandidates(payload) {
  state.selected.clear();
  const list = $("#candidate-list");
  list.replaceChildren();
  $("#candidate-count").textContent = `${payload.candidates.length} 项`;
  $("#recommendation-summary").textContent = payload.status === "ok"
    ? payload.mode === "case_driven"
      ? "系统根据病例线索发现以下评估机会；请结合诊断、人群、版本与来源确认。"
      : `按“${payload.query}”并结合病例线索匹配；请结合人群、版本与来源确认。`
    : "没有从病例中识别出可靠评估方向。可以补充诊断、主要问题，或直接填写评估目标。";

  const existingIntents = $("#intent-strip");
  if (existingIntents) existingIntents.remove();
  if (payload.detected_intents.length) {
    const strip = element("div", { id: "intent-strip", className: "intent-strip" });
    for (const intent of payload.detected_intents) {
      strip.append(element("span", { className: "intent-item", text: intent.label }));
    }
    $("#privacy-warning").before(strip);
  }

  const warning = $("#privacy-warning");
  if (payload.privacy_warnings.length) {
    warning.textContent = `输入中发现 ${payload.privacy_warnings.join("、")}。请返回左侧移除直接身份信息后再继续。`;
    warning.hidden = false;
  } else {
    warning.hidden = true;
  }

  for (const candidate of payload.candidates) {
    const checkbox = element("input", {
      className: "check-control",
      type: "checkbox",
      value: candidate.id,
      ariaLabel: `选择 ${candidate.name_cn}`,
    });
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) state.selected.add(candidate.id);
      else state.selected.delete(candidate.id);
      updateSelectionSummary();
    });

    const knownCount = candidate.inputs.length - candidate.missing_inputs.length;
    const meta = element("div", { className: "candidate-meta" }, [
      statusBadge(candidate.category),
      statusBadge(
        candidate.missing_inputs.length
          ? `已识别 ${knownCount} 项，还需确认 ${candidate.missing_inputs.length} 项`
          : `所需 ${candidate.inputs.length} 项数据已识别`,
        candidate.missing_inputs.length ? "warn" : "good",
      ),
      statusBadge(
        candidate.evidence.source_specific ? "来源可直接核对" : "来源需进一步回溯",
        candidate.evidence.source_specific ? "good" : "warn",
      ),
    ]);

    const main = element("div", {}, [
      element("h3", { className: "candidate-title", text: candidate.name_cn }),
      element("p", { className: "candidate-subtitle", text: candidate.name_en }),
      element("p", { className: "candidate-reason", text: candidate.recommendation_reasons.join("；") }),
      meta,
    ]);

    const evidence = element("div", { className: "evidence-grid" }, [
      element("div", {}, [
        element("h4", { text: "计算依据" }),
        element("p", { text: candidate.formula || "目录未记录具体公式文本" }),
      ]),
      element("div", {}, [
        element("h4", { text: "来源与使用提醒" }),
        element("p", {}, [
          sourceLink(candidate),
          document.createTextNode(`\n${candidate.evidence.tier || "证据层级未记录"}`),
          document.createTextNode(candidate.evidence.version ? `\n版本：${candidate.evidence.version}` : "\n版本：未记录"),
          document.createTextNode(candidate.review.gaps.length ? `\n使用前请注意：${candidate.review.gaps.join("；")}` : "\n来源信息已通过自动检查"),
          document.createTextNode(`\n目录编号：${candidate.id}`),
        ]),
      ]),
    ]);
    const details = element("details", { className: "candidate-details" }, [
      element("summary", { text: "查看计算依据和来源" }),
      evidence,
    ]);
    list.append(element("article", { className: "candidate" }, [
      checkbox,
      main,
      details,
    ]));
  }
  updateSelectionSummary();
}

function updateSelectionSummary() {
  const count = state.selected.size;
  $("#selection-summary").textContent = count ? `已选择 ${count} 个计算器` : "尚未选择";
  $("#continue-button").disabled = count === 0 || Boolean(state.recommendation?.privacy_warnings.length);
}

function fieldControl(candidate, spec) {
  const id = `${candidate.id}--${spec.name}`;
  const wrapper = element("div", { className: "field" });
  const label = element("label", { htmlFor: id }, [
    element("span", { text: spec.label }),
    spec.unit ? element("small", { text: unitLabels[spec.unit] || spec.unit }) : null,
  ]);
  let control;
  if (spec.ui_type === "boolean") {
    control = element("select", { id, name: id, required: true }, [
      element("option", { value: "", text: "待确认" }),
      element("option", { value: "true", text: "是" }),
      element("option", { value: "false", text: "否" }),
    ]);
    if (spec.available && typeof spec.value === "boolean") control.value = String(spec.value);
    const boolean = element("div", { className: "boolean-field" }, [label, control]);
    wrapper.append(boolean);
  } else if (spec.ui_type === "choice") {
    control = element("select", { id, name: id, required: true }, [element("option", { value: "", text: "请选择" })]);
    for (const choice of spec.choices) {
      control.append(element("option", {
        value: choice,
        text: spec.choice_labels?.[choice] || choice.replaceAll("_", " "),
      }));
    }
    if (spec.available) control.value = String(spec.value);
    wrapper.append(label, control);
  } else {
    const type = spec.ui_type === "number" ? "number" : "text";
    control = element("input", {
      id,
      name: id,
      type,
      required: true,
      step: type === "number" ? "any" : undefined,
      value: spec.available ? String(spec.value) : "",
    });
    if (spec.minimum != null) control.min = spec.minimum;
    if (spec.maximum != null) control.max = spec.maximum;
    wrapper.append(label, control);
  }
  control.dataset.calculator = candidate.id;
  control.dataset.input = spec.name;
  control.dataset.type = spec.ui_type;
  wrapper.classList.toggle("is-prefilled", Boolean(spec.available));
  if (spec.available) wrapper.append(element("p", { className: "field-note", text: "已从病例中识别，请核对" }));
  else wrapper.append(element("p", { className: "field-note needs-confirmation", text: "病例中未明确，请补充" }));
  return wrapper;
}

function renderInputGroups() {
  const container = $("#input-groups");
  container.replaceChildren();
  const candidates = state.recommendation.candidates.filter((candidate) => state.selected.has(candidate.id));
  for (const candidate of candidates) {
    const grid = element("div", { className: "input-grid" });
    for (const spec of candidate.inputs) grid.append(fieldControl(candidate, spec));
    container.append(element("section", { className: "input-group" }, [
      element("div", { className: "input-group-heading" }, [
        element("h3", { text: candidate.name_cn }),
        element("span", { text: `需确认 ${candidate.inputs.length} 项` }),
      ]),
      grid,
    ]));
  }
  updateCompleteness();
  $$("#input-groups input, #input-groups select").forEach((control) => control.addEventListener("input", updateCompleteness));
}

function updateCompleteness() {
  const controls = $$("#input-groups input, #input-groups select");
  const complete = controls.filter((control) => control.value !== "").length;
  $("#completeness-summary").textContent = `已确认 ${complete}/${controls.length} 项`;
}

function collectInputs() {
  const calculatorInputs = {};
  for (const id of state.selected) calculatorInputs[id] = {};
  for (const control of $$("#input-groups input, #input-groups select")) {
    if (!control.value) throw new Error(`请确认“${control.closest(".field").querySelector("label span").textContent}”`);
    let value = control.value;
    if (control.dataset.type === "number") value = Number(value);
    else if (control.dataset.type === "boolean") value = value === "true";
    else if (control.dataset.type === "any") {
      try { value = JSON.parse(value); } catch (_) { /* keep explicit text */ }
    }
    calculatorInputs[control.dataset.calculator][control.dataset.input] = value;
  }
  return calculatorInputs;
}

function reviewItem(input) {
  return element("div", { className: "review-item" }, [
    element("dt", { text: input.label }),
    element("dd", { text: input.display_value }),
  ]);
}

function resultStatusClass(status) {
  if (["implemented", "partial"].includes(status)) return "good";
  if (status === "missing_inputs") return "warn";
  return "danger";
}

function renderResults(payload) {
  const list = $("#result-list");
  list.replaceChildren();
  for (const run of payload.runs) {
    const displayValue = run.value == null ? "—" : String(run.value);
    const displayUnit = unitLabels[run.unit] || run.unit || "";
    const source = element("a", { href: run.source.url, target: "_blank", rel: "noreferrer", text: run.source.name || "查看来源" });
    const inputs = element("dl", { className: "review-grid" });
    for (const input of run.input_display) inputs.append(reviewItem(input));

    const calculationPath = element("ol", { className: "calculation-path" }, [
      element("li", {}, [
        element("strong", { text: "核对输入" }),
        element("span", { text: `已确认 ${run.input_display.length} 项必要数据` }),
      ]),
      element("li", {}, [
        element("strong", { text: "应用计算规则" }),
        element("span", { text: "按当前目录记录的公式或评分规则执行" }),
      ]),
      element("li", {}, [
        element("strong", { text: "生成结果" }),
        element("span", { text: `${displayValue}${displayUnit ? ` ${displayUnit}` : ""}` }),
      ]),
    ]);

    const evidenceDetails = element("details", { className: "result-details" }, [
      element("summary", { text: "查看计算依据、参考解释与来源" }),
      element("div", { className: "result-details-body" }, [
        element("section", {}, [
          element("h4", { text: "公式或评分规则" }),
          element("p", { className: "formula-text", text: run.formula || "未记录" }),
        ]),
        element("section", {}, [
          element("h4", { text: "目录中的参考解释" }),
          element("p", { className: "formula-text", text: run.reference_interpretation || "未记录" }),
        ]),
        element("section", {}, [
          element("h4", { text: "来源" }),
          element("p", {}, [
            source,
            document.createTextNode(run.source.version ? ` · ${run.source.version}` : " · 版本未记录"),
          ]),
        ]),
      ]),
    ]);

    const reviewNotice = element("div", {
      className: `review-notice ${run.review.ok ? "is-ok" : "is-warning"}`,
    }, [
      element("strong", { text: run.review.label }),
      element("span", {
        text: run.review.ok
          ? "仍需结合适用人群、现行指南和临床判断。"
          : run.review.gaps.join("；"),
      }),
    ]);

    list.append(element("article", { className: "result-card" }, [
      element("header", { className: "result-header" }, [
        element("div", {}, [
          statusBadge(run.status_label, resultStatusClass(run.status)),
          element("h3", { text: run.name_cn }),
          element("p", { text: run.name_en }),
        ]),
        element("div", { className: "result-value", text: displayValue }, [
          element("small", { text: displayUnit }),
        ]),
      ]),
      element("div", { className: "result-body" }, [
        element("section", { className: "clinical-conclusion" }, [
          element("span", { text: "结果解释" }),
          element("p", { text: run.clinical_explanation }),
        ]),
        reviewNotice,
        element("div", { className: "result-columns" }, [
          element("section", { className: "result-section" }, [
            element("h4", { text: "本次已确认数据" }),
            inputs,
          ]),
          element("section", { className: "result-section" }, [
            element("h4", { text: "计算过程" }),
            calculationPath,
          ]),
        ]),
        evidenceDetails,
      ]),
    ]));
  }
  state.auditLog = [...state.recommendation.audit_log, ...payload.audit_log];
  const audit = $("#audit-log");
  audit.replaceChildren();
  for (const item of state.auditLog) {
    audit.append(element("li", {}, [
      element("time", { text: new Date(item.at).toLocaleTimeString("zh-CN", { hour12: false }) }),
      element("strong", { text: auditEventLabels[item.event] || item.event }),
      element("span", { text: item.detail }),
    ]));
  }
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "请求失败");
  return data;
}

$("#case-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setError($("#form-error"), "");
  setLoading(true);
  try {
    state.recommendation = await postJson("/api/recommend", {
      query: $("#query").value,
      case_text: $("#case-text").value,
      limit: 6,
    });
    state.calculation = null;
    renderCandidates(state.recommendation);
    showStage("recommendations");
  } catch (error) {
    $("#empty-state").hidden = false;
    setError($("#form-error"), error.message);
  } finally {
    setLoading(false);
  }
});

$("#fill-example").addEventListener("click", () => {
  $("#query").value = "房颤卒中风险";
  $("#case-text").value = [
    "74岁男性，非瓣膜性房颤。",
    "hypertension=true",
    "diabetes=false",
    "congestive_heart_failure=false",
    "stroke_tia_thromboembolism=true",
    "vascular_disease=false",
  ].join("\n");
});

$("#continue-button").addEventListener("click", () => {
  renderInputGroups();
  showStage("inputs");
});
$("#back-to-recommendations").addEventListener("click", () => showStage("recommendations"));
$("#back-to-inputs").addEventListener("click", () => showStage("inputs"));
$("#edit-case").addEventListener("click", () => {
  document.body.classList.add("show-case");
  $(".case-panel").scrollIntoView({ behavior: "smooth", block: "start" });
});

$("#input-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  setError($("#input-error"), "");
  const button = $("#calculate-button");
  button.disabled = true;
  try {
    const calculatorInputs = collectInputs();
    state.calculation = await postJson("/api/calculate", {
      session_id: state.recommendation.session_id,
      calculator_inputs: calculatorInputs,
    });
    renderResults(state.calculation);
    showStage("results");
  } catch (error) {
    setError($("#input-error"), error.message);
  } finally {
    button.disabled = false;
  }
});

$("#download-log").addEventListener("click", () => {
  const payload = {
    exported_at: new Date().toISOString(),
    session_id: state.recommendation.session_id,
    query: state.recommendation.query,
    extracted_values: state.recommendation.extracted_values,
    calculation: state.calculation,
    audit_log: state.auditLog,
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
  const link = element("a", { href: url, download: `clinical-calculation-${payload.session_id.slice(0, 8)}.json` });
  link.click();
  URL.revokeObjectURL(url);
});

$$('.progress-item').forEach((item) => item.addEventListener('click', () => {
  if (!item.disabled) showStage(item.dataset.stage);
}));
