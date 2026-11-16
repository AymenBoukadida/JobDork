import { KEYS, storageGet, storageSet } from "./js/storage.js";
import {
  asHistoryList,
  buildPayload,
  formatRequestError,
  historyKey,
  normalizeHistoryEntry,
  readJson,
  requireArrayField,
} from "./js/form-payload.js";
import { showToast } from "./js/toast.js";

const form = document.getElementById("dork-form");
const resultsPanel = document.getElementById("results-panel");
const emptyState = document.getElementById("empty-state");
const resultsEl = document.getElementById("results");
const resultsMeta = document.getElementById("results-meta");
const resultsWarnings = document.getElementById("results-warnings");
const resultsStatus = document.getElementById("results-status");
const copyStatus = document.getElementById("copy-status");
const copyAllBtn = document.getElementById("copy-all");
const categoryNav = document.getElementById("category-nav");
const atsContainer = document.getElementById("ats-platforms");
const atsCount = document.getElementById("ats-count");
const cvUploadPanel = document.getElementById("cv-upload-panel");
const cvFileInput = document.getElementById("cv-file");
const cvChooseBtn = document.getElementById("cv-choose");
const cvParseBtn = document.getElementById("cv-parse-btn");
const cvStatus = document.getElementById("cv-status");
const dropZone = document.getElementById("drop-zone");
const fileNameEl = document.getElementById("file-name");
const modeTabs = document.querySelectorAll(".input-mode-tabs .tab");
const submitBtn = document.getElementById("submit-btn");
const btnSpinner = submitBtn.querySelector(".btn-spinner");
const resultsError = document.getElementById("results-error");
const historyToggle = document.getElementById("history-toggle");
const historyPanel = document.getElementById("history-panel");
const historyList = document.getElementById("history-list");
const historyEmpty = document.getElementById("history-empty");
const historyClear = document.getElementById("history-clear");
const titleError = document.getElementById("title-error");
const presetGrid = document.getElementById("preset-grid");
const presetIdInput = document.getElementById("preset-id");
const presetClearBtn = document.getElementById("preset-clear");
const presetStatus = document.getElementById("preset-status");
const timeFilterSelect = document.getElementById("time-filter");
const timeFilterStatus = document.getElementById("time-filter-status");
const atsStatus = document.getElementById("ats-status");
const advancedDetails = document.getElementById("advanced-details");

let lastDorkResults = null;
let allDorksFlat = [];
let domainPresets = [];
let isLoading = false;

copyAllBtn.disabled = true;

async function init() {
  bindEvents();
  await Promise.allSettled([loadPresets(), loadTimeFilters(), loadAtsPlatforms()]);
  renderHistory();
}

function normalizePresets(raw) {
  return raw
    .filter((preset) => preset && typeof preset.id === "string")
    .map((preset) => ({
      id: preset.id,
      name: typeof preset.name === "string" ? preset.name : preset.id,
      icon: typeof preset.icon === "string" ? preset.icon : "",
      description:
        typeof preset.description === "string" ? preset.description : "",
      titles: Array.isArray(preset.titles)
        ? preset.titles.filter((title) => typeof title === "string")
        : [],
      skills: Array.isArray(preset.skills)
        ? preset.skills.filter((skill) => typeof skill === "string")
        : [],
      exclude_terms: Array.isArray(preset.exclude_terms)
        ? preset.exclude_terms.filter((term) => typeof term === "string")
        : [],
    }));
}

function renderPresets() {
  presetGrid.innerHTML = domainPresets
    .map((p) => {
      const domId = `preset-desc-${String(p.id).replace(/[^a-zA-Z0-9_-]/g, "-")}`;
      return `
    <div class="preset-item" role="listitem">
      <button type="button" class="preset-card" data-preset-id="${escapeHtml(p.id)}" title="${escapeHtml(p.description)}" aria-describedby="${domId}">
        <span class="preset-icon" aria-hidden="true">${escapeHtml(p.icon)}</span>
        <span class="preset-name">${escapeHtml(p.name)}</span>
      </button>
      <span class="sr-only" id="${domId}">${escapeHtml(p.description)}</span>
    </div>`;
    })
    .join("");
  presetGrid.querySelectorAll(".preset-card").forEach((btn) => {
    btn.addEventListener("click", () => applyPreset(btn.dataset.presetId));
  });
  setStatus(presetStatus, "");
}

function bootstrappedPresets() {
  const node = document.getElementById("preset-bootstrap");
  if (!node) return null;
  try {
    const parsed = JSON.parse(node.textContent || "null");
    return Array.isArray(parsed) ? normalizePresets(parsed) : null;
  } catch {
    return null;
  }
}

async function loadPresets() {
  const bootstrapped = bootstrappedPresets();
  if (bootstrapped) {
    domainPresets = bootstrapped;
    renderPresets();
    return;
  }
  try {
    const res = await fetch("/api/presets");
    const data = await readJson(res);
    if (!res.ok) throw new Error(formatRequestError(res, data));
    domainPresets = normalizePresets(
      requireArrayField(data, "presets", "preset list")
    );
    renderPresets();
  } catch (err) {
    domainPresets = [];
    presetGrid.innerHTML = "";
    setStatus(presetStatus, `Presets unavailable. ${err.message}`);
  }
}

async function loadTimeFilters() {
  try {
    const res = await fetch("/api/time-filters");
    const data = await readJson(res);
    if (!res.ok) throw new Error(formatRequestError(res, data));
    const filters = requireArrayField(data, "filters", "time filter list");
    for (const f of filters) {
      if (!f || typeof f.id !== "string" || typeof f.label !== "string") continue;
      const opt = document.createElement("option");
      opt.value = f.id;
      opt.textContent = f.label;
      timeFilterSelect.appendChild(opt);
    }
    setStatus(timeFilterStatus, "");
  } catch (err) {
    setStatus(timeFilterStatus, `Time filters unavailable. ${err.message}`);
  }
}

function applyPreset(presetId) {
  const preset = domainPresets.find((p) => p.id === presetId);
  if (!preset) return;

  form.titles.value = preset.titles.join(", ");
  form.skills.value = preset.skills.join(", ");
  if (preset.skills.length > 1) {
    const orMode = form.querySelector('input[name="keyword_mode"][value="or"]');
    if (orMode) orMode.checked = true;
  }
  if (preset.exclude_terms?.length) {
    form.exclude_terms.value = preset.exclude_terms.join(", ");
    advancedDetails.open = true;
  }
  presetIdInput.value = presetId;
  clearTitleError();

  presetGrid.querySelectorAll(".preset-card").forEach((el) => {
    el.classList.toggle("active", el.dataset.presetId === presetId);
  });
  if (presetClearBtn) presetClearBtn.hidden = false;

  showToast(`${preset.name} preset applied. Edit fields as needed.`);
  form.titles.focus();
}

function clearPresetSelection() {
  presetIdInput.value = "";
  presetGrid.querySelectorAll(".preset-card").forEach((el) => el.classList.remove("active"));
  if (presetClearBtn) presetClearBtn.hidden = true;
}

function bindEvents() {
  document.getElementById("ats-select-all")?.addEventListener("click", () => setAllAts(true));
  document.getElementById("ats-select-none")?.addEventListener("click", () => setAllAts(false));

  modeTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      modeTabs.forEach((t) => {
        t.classList.remove("active");
        t.setAttribute("aria-pressed", "false");
      });
      tab.classList.add("active");
      tab.setAttribute("aria-pressed", "true");
      cvUploadPanel.hidden = tab.dataset.mode !== "cv";
    });
  });

  cvChooseBtn.addEventListener("click", () => cvFileInput.click());
  cvParseBtn.addEventListener("click", parseCv);
  cvFileInput.addEventListener("change", onFileSelected);
  setupDropZone();

  atsContainer.addEventListener("change", updateAtsCount);

  form.addEventListener("submit", onSubmit);
  copyAllBtn.addEventListener("click", copyAllQueries);

  historyToggle.addEventListener("click", toggleHistory);
  historyClear.addEventListener("click", clearHistory);
  presetClearBtn?.addEventListener("click", () => {
    clearPresetSelection();
    showToast("Preset cleared");
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !historyPanel.hidden) {
      historyPanel.hidden = true;
      historyToggle.setAttribute("aria-expanded", "false");
      historyToggle.focus();
    }
  });

  form.addEventListener("input", (e) => {
    if (e.target.name === "titles") {
      clearPresetSelection();
      if (e.target.value.trim()) clearTitleError();
    }
  });
}

function setupDropZone() {
  ["dragenter", "dragover"].forEach((ev) => {
    dropZone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropZone.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((ev) => {
    dropZone.addEventListener(ev, (e) => {
      e.preventDefault();
      dropZone.classList.remove("drag-over");
    });
  });
  dropZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer?.files?.[0];
    if (file) setCvFile(file);
  });
}

function onFileSelected() {
  const file = cvFileInput.files?.[0];
  if (file) setCvFile(file);
}

function setCvFile(file) {
  const dt = new DataTransfer();
  dt.items.add(file);
  cvFileInput.files = dt.files;
  fileNameEl.textContent = file.name;
  cvParseBtn.disabled = false;
}

async function loadAtsPlatforms() {
  try {
    const res = await fetch("/api/ats-platforms");
    const data = await readJson(res);
    if (!res.ok) throw new Error(formatRequestError(res, data));
    const platforms = requireArrayField(data, "platforms", "ATS platform list").filter(
      (platform) =>
        platform &&
        typeof platform.id === "string" &&
        typeof platform.name === "string"
    );
    atsContainer.innerHTML = platforms
      .map(
        (p) => `
    <label class="ats-option">
      <input type="checkbox" name="ats" value="${escapeHtml(p.id)}" checked />
      <span>${escapeHtml(p.name)}</span>
    </label>`
      )
      .join("");
    setStatus(atsStatus, "");
    updateAtsCount();
  } catch (err) {
    atsContainer.innerHTML = "";
    if (atsCount) atsCount.textContent = "Unavailable";
    setStatus(atsStatus, `ATS platforms unavailable. ${err.message}`);
  }
}

function updateAtsCount() {
  const checked = atsContainer.querySelectorAll('input[name="ats"]:checked').length;
  const total = atsContainer.querySelectorAll('input[name="ats"]').length;
  if (atsCount) {
    atsCount.textContent = checked === total ? `${total} selected` : `${checked} of ${total}`;
  }
}

function getFormPayload() {
  return buildPayload(new FormData(form), getSelectedAtsIds());
}

function getSelectedAtsIds() {
  const boxes = atsContainer.querySelectorAll('input[name="ats"]:checked');
  const allBoxes = atsContainer.querySelectorAll('input[name="ats"]');
  if (boxes.length === allBoxes.length) return null;
  return Array.from(boxes).map((el) => el.value);
}

function setAllAts(checked) {
  atsContainer.querySelectorAll('input[name="ats"]').forEach((el) => {
    el.checked = checked;
  });
  updateAtsCount();
}

function validateForm(payload) {
  if (!payload.titles?.length) {
    showFieldError(titleError, "At least one job title is required.");
    form.titles.setAttribute("aria-invalid", "true");
    form.titles.focus();
    return false;
  }
  clearTitleError();
  return true;
}

function clearTitleError() {
  form.titles.removeAttribute("aria-invalid");
  hideFieldError(titleError);
}

function showFieldError(el, msg) {
  el.hidden = false;
  el.textContent = msg;
}

function hideFieldError(el) {
  el.hidden = true;
  el.textContent = "";
}

async function onSubmit(e) {
  e.preventDefault();
  if (isLoading) return;
  const payload = getFormPayload();
  if (!validateForm(payload)) return;

  const generated = await generateDorks(payload);
  if (generated) saveHistoryEntry(payload);
}

async function generateDorks(payload) {
  setLoading(true);
  clearResultsUi();

  try {
    let res;
    try {
      res = await fetch("/api/dorks", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      });
    } catch {
      throw new Error(formatRequestError({ status: 0 }, {}));
    }
    const data = await readJson(res);
    if (!res.ok) throw new Error(formatRequestError(res, data));
    if (!data || typeof data !== "object" || !Array.isArray(data.categories)) {
      throw new Error("Unexpected response from the server. Try again.");
    }

    lastDorkResults = data;
    renderDorkResults(data);
    showResultsPanel();
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    resultsPanel.scrollIntoView({
      behavior: reduceMotion ? "auto" : "smooth",
      block: "start",
    });
    return true;
  } catch (err) {
    showResultsPanel();
    resultsError.hidden = false;
    resultsError.textContent = err?.message || "Could not generate dorks. Try again.";
    return false;
  } finally {
    setLoading(false);
  }
}

function renderDorkResults(data) {
  const categories = data.categories.filter((cat) => cat && Array.isArray(cat.dorks));
  allDorksFlat = categories.flatMap((cat) => cat.dorks);
  const total = Number.isFinite(data.total) ? data.total : allDorksFlat.length;
  const warnings = Array.isArray(data.warnings) ? data.warnings : [];
  const params = data.params && typeof data.params === "object" ? data.params : {};
  const titles = Array.isArray(params.titles) ? params.titles : [];

  const titlesLabel =
    titles.length > 1 ? titles.join(", ") : params.title || titles[0] || "";
  resultsMeta.textContent = `${total} queries for ${titlesLabel}${
    params.location ? ` · ${params.location}` : ""
  }${params.time_filter ? ` · ${params.time_filter}` : ""}`;

  if (warnings.length) {
    resultsWarnings.hidden = false;
    resultsWarnings.textContent = warnings.join(" ");
  }

  categoryNav.hidden = false;
  categoryNav.innerHTML = categories
    .map(
      (cat) =>
        `<a href="#cat-${escapeHtml(cat.id)}"><span aria-hidden="true">${escapeHtml(cat.icon)}</span> ${escapeHtml(cat.label)}</a>`
    )
    .join("");

  let idx = 0;
  resultsEl.innerHTML = categories
    .map(
      (cat) => `
    <section class="category" id="cat-${escapeHtml(cat.id)}" aria-labelledby="cat-title-${escapeHtml(cat.id)}">
      <h3 class="category-title" id="cat-title-${escapeHtml(cat.id)}">
        <span aria-hidden="true">${escapeHtml(cat.icon)}</span> ${escapeHtml(cat.label)}
        <span class="category-count">${cat.dorks.length}</span>
      </h3>
      ${cat.dorks.map((d) => dorkCard(d, idx++)).join("")}
    </section>`
    )
    .join("");

  copyAllBtn.disabled = false;
  resultsStatus.textContent = `${total} queries generated.${
    warnings.length ? ` ${warnings.join(" ")}` : ""
  }`;

  resultsEl.querySelectorAll("[data-dork-index]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const query = allDorksFlat[Number(btn.dataset.dorkIndex)]?.query;
      if (!query) return;
      if (await copyText(query, btn)) {
        copyStatus.textContent = "Query copied to clipboard.";
      }
    });
  });
}

function dorkCard(dork, index) {
  const warn = dork.query_warning
    ? `<p class="dork-warn">${escapeHtml(dork.query_warning)}</p>`
    : "";
  const label = escapeHtml(dork.label);
  return `
    <article class="dork-card">
      <div class="dork-label">${label}</div>
      <p class="dork-desc">${escapeHtml(dork.description)}</p>
      ${warn}
      <div class="dork-query">${escapeHtml(dork.query)}</div>
      <div class="dork-actions">
        <button type="button" class="btn-icon" data-dork-index="${index}" aria-label="Copy ${label} query">Copy</button>
        <a href="${escapeHtml(dork.google_url)}" target="_blank" rel="noopener noreferrer" class="btn-icon open-google" aria-label="Open ${label} in Google">Open in Google</a>
      </div>
    </article>`;
}

function saveHistoryEntry(config) {
  const history = asHistoryList(storageGet(KEYS.history, []));
  const key = historyKey(config);
  const entry = {
    ...normalizeHistoryEntry(config),
    id: Date.now(),
    ranAt: new Date().toISOString(),
  };
  const next = [entry, ...history.filter((h) => historyKey(h) !== key)].slice(0, 20);
  if (!storageSet(KEYS.history, next)) {
    showToast("Could not save past searches because browser storage is unavailable.", { type: "error" });
  }
  renderHistory();
}

function renderHistory() {
  const history = asHistoryList(storageGet(KEYS.history, [])).filter(
    (entry) => entry && typeof entry === "object"
  );
  historyEmpty.hidden = history.length > 0;
  historyList.innerHTML = history
    .map(
      (h) => `
    <li class="history-item">
      <button type="button" class="history-run" data-id="${h.id}">
        <strong>${escapeHtml(displayTitles(h))}</strong>
        <span>${escapeHtml(h.location || "Any location")} · ${formatDate(h.ranAt)}</span>
      </button>
    </li>`
    )
    .join("");

  historyList.querySelectorAll(".history-run").forEach((btn) => {
    btn.addEventListener("click", () => {
      const entry = history.find((h) => h.id === Number(btn.dataset.id));
      if (entry) applyConfigToForm(entry);
      historyPanel.hidden = true;
      historyToggle.setAttribute("aria-expanded", "false");
      showToast("Form restored from history");
    });
  });
}

function displayTitles(config) {
  const titles = Array.isArray(config?.titles)
    ? config.titles.filter((title) => typeof title === "string" && title)
    : [];
  if (titles.length) return titles.join(", ");
  return typeof config?.title === "string" && config.title ? config.title : "Untitled";
}

function applyConfigToForm(config) {
  const entry = normalizeHistoryEntry(config);
  clearTitleError();
  form.titles.value = entry.titles.join(", ");
  form.location.value = entry.location;
  form.skills.value = entry.skills.join(", ");
  form.exclude_terms.value = entry.exclude_terms.join(", ");
  form.company.value = entry.company;
  form.company_domains.value = entry.company_domains.join(", ");
  form.experience.value = entry.experience;
  form.remote.checked = entry.remote;
  const hasTimeOption = Array.from(form.time_filter.options).some(
    (option) => option.value === entry.time_filter
  );
  form.time_filter.value = hasTimeOption ? entry.time_filter : "";
  presetIdInput.value = entry.preset_id;
  presetGrid.querySelectorAll(".preset-card").forEach((el) => {
    el.classList.toggle("active", el.dataset.presetId === entry.preset_id);
  });
  if (presetClearBtn) presetClearBtn.hidden = !entry.preset_id;

  const km = form.querySelector(`input[name="keyword_mode"][value="${entry.keyword_mode}"]`);
  if (km) km.checked = true;
  const tm = form.querySelector(`input[name="title_mode"][value="${entry.title_mode}"]`);
  if (tm) tm.checked = true;

  if (entry.ats_platforms === null) {
    setAllAts(true);
  } else {
    atsContainer.querySelectorAll('input[name="ats"]').forEach((el) => {
      el.checked = entry.ats_platforms.includes(el.value);
    });
    updateAtsCount();
  }

  advancedDetails.open = Boolean(
    entry.exclude_terms.length || entry.company || entry.company_domains.length || entry.remote
  );
}

function clearHistory() {
  if (!storageSet(KEYS.history, [])) {
    showToast("Could not clear history.", { type: "error" });
    return;
  }
  renderHistory();
  showToast("History cleared");
}

function toggleHistory() {
  const open = historyPanel.hidden;
  historyPanel.hidden = !open;
  historyToggle.setAttribute("aria-expanded", String(open));
}

async function parseCv() {
  const file = cvFileInput.files?.[0];
  if (!file) {
    cvStatus.hidden = false;
    cvStatus.className = "field-msg error-msg";
    cvStatus.textContent = "Choose a CV file first.";
    return;
  }

  cvParseBtn.disabled = true;
  cvStatus.hidden = false;
  cvStatus.className = "field-msg loading-msg";
  cvStatus.textContent = "Parsing CV…";

  const body = new FormData();
  body.append("cv", file);

  try {
    const res = await fetch("/api/cv/parse", { method: "POST", body });
    const data = await readJson(res);
    if (!res.ok) throw new Error(formatRequestError(res, data));
    if (!data || typeof data !== "object") {
      throw new Error("Unexpected response from the server. Try again.");
    }

    applyCvToForm(data);
    const skillCount = Array.isArray(data.skills) ? data.skills.length : 0;
    cvStatus.className = "field-msg success-msg";
    cvStatus.textContent = data.title
      ? `Filled form from CV (${skillCount} skills). Review and generate dorks.`
      : "Extracted text. Please set a job title manually.";
    modeTabs.forEach((t) => {
      t.classList.remove("active");
      t.setAttribute("aria-pressed", "false");
    });
    const manual = document.querySelector('.input-mode-tabs .tab[data-mode="manual"]');
    manual?.classList.add("active");
    manual?.setAttribute("aria-pressed", "true");
    cvUploadPanel.hidden = true;
    form.titles.focus();
  } catch (err) {
    cvStatus.className = "field-msg error-msg";
    cvStatus.textContent = err.message;
  } finally {
    cvParseBtn.disabled = !cvFileInput.files?.[0];
  }
}

function applyCvToForm(data) {
  if (data.title) form.titles.value = data.title;
  clearPresetSelection();
  if (data.location) form.location.value = data.location;
  if (Array.isArray(data.skills) && data.skills.length) {
    form.skills.value = data.skills.join(", ");
  }
  if (data.experience) form.experience.value = data.experience;
  if (data.suggested_remote) {
    form.remote.checked = true;
    advancedDetails.open = true;
  }
  if (form.titles.value.trim()) clearTitleError();
}

function clearResultsUi() {
  lastDorkResults = null;
  allDorksFlat = [];
  resultsEl.innerHTML = "";
  resultsMeta.textContent = "";
  resultsWarnings.hidden = true;
  resultsWarnings.textContent = "";
  resultsError.hidden = true;
  resultsError.textContent = "";
  resultsStatus.textContent = "";
  copyStatus.textContent = "";
  copyAllBtn.disabled = true;
  categoryNav.hidden = true;
  categoryNav.innerHTML = "";
}

function showResultsPanel() {
  emptyState.hidden = true;
  resultsPanel.hidden = false;
}

function setLoading(loading) {
  isLoading = loading;
  form.classList.toggle("loading", loading);
  form.setAttribute("aria-busy", String(loading));
  submitBtn.disabled = loading;
  btnSpinner.hidden = !loading;
  const label = submitBtn.querySelector(".btn-label");
  if (label) label.textContent = loading ? "Generating…" : "Generate dorks";
}

function setStatus(el, message, type = "error") {
  if (!el) return;
  el.hidden = !message;
  el.textContent = message;
  el.className = message ? `field-msg ${type}-msg` : "field-msg";
}

async function copyAllQueries() {
  if (!lastDorkResults || !Array.isArray(lastDorkResults.categories)) return;
  const queries = lastDorkResults.categories.flatMap((category) =>
    Array.isArray(category.dorks) ? category.dorks.map((dork) => dork.query) : []
  );
  if (!queries.length) return;
  if (await copyText(queries.join("\n\n"), copyAllBtn)) {
    copyStatus.textContent = `${queries.length} queries copied to clipboard.`;
    showToast(`Copied ${queries.length} queries`);
  }
}

const HTML_ESCAPES = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

function escapeHtml(text) {
  return String(text ?? "").replace(/[&<>"']/g, (ch) => HTML_ESCAPES[ch]);
}

async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    if (btn) {
      if (btn.querySelector("svg")) {
        btn.classList.add("copied");
        setTimeout(() => btn.classList.remove("copied"), 1500);
      } else {
        const orig = btn.textContent;
        btn.textContent = "Copied!";
        btn.classList.add("copied");
        setTimeout(() => {
          btn.textContent = orig;
          btn.classList.remove("copied");
        }, 1500);
      }
    }
    return true;
  } catch {
    showToast("Could not copy to clipboard", { type: "error" });
    return false;
  }
}

function formatDate(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "Unknown time";
  return date.toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
}

init();
