import { KEYS, storageGet, storageSet } from "./js/storage.js";
import { showToast } from "./js/toast.js";

const form = document.getElementById("dork-form");
const resultsPanel = document.getElementById("results-panel");
const emptyState = document.getElementById("empty-state");
const resultsEl = document.getElementById("results");
const resultsMeta = document.getElementById("results-meta");
const resultsWarnings = document.getElementById("results-warnings");
const copyAllBtn = document.getElementById("copy-all");
const categoryNav = document.getElementById("category-nav");
const atsContainer = document.getElementById("ats-platforms");
const atsCount = document.getElementById("ats-count");
const cvUploadPanel = document.getElementById("cv-upload-panel");
const cvFileInput = document.getElementById("cv-file");
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
const timeFilterSelect = document.getElementById("time-filter");

let lastDorkResults = null;
let allDorksFlat = [];
let domainPresets = [];

init();

function init() {
  loadAtsPlatforms();
  loadPresets();
  loadTimeFilters();
  renderHistory();
  bindEvents();
}

async function loadPresets() {
  const res = await fetch("/api/presets");
  if (!res.ok) return;
  const data = await res.json();
  domainPresets = data.presets || [];
  presetGrid.innerHTML = domainPresets
    .map(
      (p) => `
    <button type="button" class="preset-card" data-preset-id="${escapeHtml(p.id)}" title="${escapeHtml(p.description)}">
      <span class="preset-icon">${p.icon}</span>
      <span class="preset-name">${escapeHtml(p.name)}</span>
    </button>`
    )
    .join("");
  presetGrid.querySelectorAll(".preset-card").forEach((btn) => {
    btn.addEventListener("click", () => applyPreset(btn.dataset.presetId));
  });
}

async function loadTimeFilters() {
  const res = await fetch("/api/time-filters");
  if (!res.ok) return;
  const data = await res.json();
  for (const f of data.filters || []) {
    const opt = document.createElement("option");
    opt.value = f.id;
    opt.textContent = f.label;
    timeFilterSelect.appendChild(opt);
  }
}

function applyPreset(presetId) {
  const preset = domainPresets.find((p) => p.id === presetId);
  if (!preset) return;

  form.titles.value = preset.titles.join(", ");
  form.skills.value = preset.skills.join(", ");
  if (preset.exclude_terms?.length) {
    form.exclude_terms.value = preset.exclude_terms.join(", ");
    document.getElementById("advanced-details").open = true;
  }
  presetIdInput.value = presetId;

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
        t.setAttribute("aria-selected", "false");
      });
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");
      cvUploadPanel.hidden = tab.dataset.mode !== "cv";
    });
  });

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
    }
  });

  form.addEventListener("input", (e) => {
    if (e.target.name === "titles") clearPresetSelection();
  });

  form.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && !e.shiftKey) {
      if (e.target.type === "button" || e.target.type === "file") return;
      e.preventDefault();
      form.requestSubmit();
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
  const res = await fetch("/api/ats-platforms");
  if (!res.ok) return;
  const data = await res.json();
  atsContainer.innerHTML = (data.platforms || [])
    .map(
      (p) => `
    <label class="ats-option">
      <input type="checkbox" name="ats" value="${escapeHtml(p.id)}" checked />
      <span>${escapeHtml(p.name)}</span>
    </label>`
    )
    .join("");
  updateAtsCount();
}

function updateAtsCount() {
  const checked = atsContainer.querySelectorAll('input[name="ats"]:checked').length;
  const total = atsContainer.querySelectorAll('input[name="ats"]').length;
  if (atsCount) {
    atsCount.textContent = checked === total ? `${total} selected` : `${checked} of ${total}`;
  }
}

function getFormPayload() {
  const data = new FormData(form);
  const titlesRaw = data.get("titles")?.toString().trim() || "";
  const skillsRaw = data.get("skills")?.toString().trim() || "";
  const excludeRaw = data.get("exclude_terms")?.toString().trim() || "";
  const domainsRaw = data.get("company_domains")?.toString().trim() || "";
  const titles = titlesRaw ? titlesRaw.split(",").map((s) => s.trim()).filter(Boolean) : [];
  return {
    titles,
    location: data.get("location")?.toString().trim() || "",
    skills: skillsRaw ? skillsRaw.split(",").map((s) => s.trim()).filter(Boolean) : [],
    exclude_terms: excludeRaw ? excludeRaw.split(",").map((s) => s.trim()).filter(Boolean) : [],
    company: data.get("company")?.toString().trim() || "",
    company_domains: domainsRaw ? domainsRaw.split(",").map((s) => s.trim()).filter(Boolean) : [],
    remote: data.get("remote") === "on",
    experience: data.get("experience")?.toString() || "",
    company: data.get("company")?.toString().trim() || "",
    keyword_mode: data.get("keyword_mode")?.toString() || "and",
    title_mode: data.get("title_mode")?.toString() || "or",
    time_filter: data.get("time_filter")?.toString() || "",
    preset_id: data.get("preset_id")?.toString() || "",
    ats_platforms: getSelectedAtsIds(),
  };
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
    form.titles.focus();
    return false;
  }
  hideFieldError(titleError);
  return true;
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
  const payload = getFormPayload();
  if (!validateForm(payload)) return;

  saveHistoryEntry(payload);
  await generateDorks(payload);
}

async function generateDorks(payload) {
  setLoading(true);
  clearResultsUi();

  try {
    const res = await fetch("/api/dorks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to generate dorks");

    lastDorkResults = data;
    renderDorkResults(data);
    showResultsPanel();
    resultsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    showResultsPanel();
    resultsError.hidden = false;
    resultsError.textContent = err.message;
  } finally {
    setLoading(false);
  }
}

function renderDorkResults(data) {
  allDorksFlat = data.categories.flatMap((c) => c.dorks);

  const titlesLabel =
    data.params.titles?.length > 1
      ? data.params.titles.join(", ")
      : data.params.title || data.params.titles?.[0] || "";
  resultsMeta.textContent = `${data.total} queries for ${titlesLabel}${
    data.params.location ? ` · ${data.params.location}` : ""
  }${data.params.time_filter ? ` · ${data.params.time_filter}` : ""}`;

  if (data.warnings?.length) {
    resultsWarnings.hidden = false;
    resultsWarnings.textContent = data.warnings.join(" ");
  }

  categoryNav.hidden = false;
  categoryNav.innerHTML = data.categories
    .map((cat) => `<a href="#cat-${cat.id}">${cat.icon} ${escapeHtml(cat.label)}</a>`)
    .join("");

  let idx = 0;
  resultsEl.innerHTML = data.categories
    .map(
      (cat) => `
    <section class="category" id="cat-${cat.id}">
      <h3 class="category-title">
        ${cat.icon} ${escapeHtml(cat.label)}
        <span class="category-count">${cat.dorks.length}</span>
      </h3>
      ${cat.dorks.map((d) => dorkCard(d, idx++)).join("")}
    </section>`
    )
    .join("");

  resultsEl.querySelectorAll("[data-dork-index]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = allDorksFlat[Number(btn.dataset.dorkIndex)]?.query;
      if (query) copyText(query, btn);
    });
  });
}

function dorkCard(dork, index) {
  const warn = dork.query_warning
    ? `<p class="dork-warn" role="status">${escapeHtml(dork.query_warning)}</p>`
    : "";
  return `
    <article class="dork-card">
      <div class="dork-label">${escapeHtml(dork.label)}</div>
      <p class="dork-desc">${escapeHtml(dork.description)}</p>
      ${warn}
      <div class="dork-query">${escapeHtml(dork.query)}</div>
      <div class="dork-actions">
        <button type="button" class="btn-icon" data-dork-index="${index}">Copy</button>
        <a href="${dork.google_url}" target="_blank" rel="noopener noreferrer" class="btn-icon open-google">Open in Google</a>
      </div>
    </article>`;
}

function saveHistoryEntry(config) {
  const history = storageGet(KEYS.history, []) || [];
  const entry = { ...config, id: Date.now(), ranAt: new Date().toISOString() };
  const next = [entry, ...history.filter((h) => JSON.stringify(h) !== JSON.stringify(config))].slice(0, 20);
  if (!storageSet(KEYS.history, next)) {
    showToast("Could not save past searches because browser storage is unavailable.", { type: "error" });
  }
  renderHistory();
}

function renderHistory() {
  const history = storageGet(KEYS.history, []) || [];
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
  if (config.titles?.length) return config.titles.join(", ");
  return config.title || "Untitled";
}

function applyConfigToForm(config) {
  form.titles.value = (config.titles || (config.title ? [config.title] : [])).join(", ");
  form.location.value = config.location || "";
  form.skills.value = (config.skills || []).join(", ");
  form.exclude_terms.value = (config.exclude_terms || []).join(", ");
  form.company.value = config.company || "";
  form.company_domains.value = (config.company_domains || []).join(", ");
  form.experience.value = config.experience || "";
  form.remote.checked = !!config.remote;
  form.time_filter.value = config.time_filter || "";
  presetIdInput.value = config.preset_id || "";
  presetGrid.querySelectorAll(".preset-card").forEach((el) => {
    el.classList.toggle("active", el.dataset.presetId === config.preset_id);
  });
  if (presetClearBtn) presetClearBtn.hidden = !config.preset_id;

  const km = form.querySelector(`input[name="keyword_mode"][value="${config.keyword_mode || "and"}"]`);
  if (km) km.checked = true;
  const tm = form.querySelector(`input[name="title_mode"][value="${config.title_mode || "or"}"]`);
  if (tm) tm.checked = true;

  if (config.ats_platforms === null) {
    setAllAts(true);
  } else if (Array.isArray(config.ats_platforms)) {
    atsContainer.querySelectorAll('input[name="ats"]').forEach((el) => {
      el.checked = config.ats_platforms.includes(el.value);
    });
    updateAtsCount();
  }

  if (config.exclude_terms?.length || config.company || config.company_domains?.length || config.remote) {
    document.getElementById("advanced-details").open = true;
  }
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
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to parse CV");

    applyCvToForm(data);
    cvStatus.className = "field-msg success-msg";
    cvStatus.textContent = data.title
      ? `Filled form from CV (${data.skills?.length || 0} skills). Review and generate dorks.`
      : "Extracted text. Please set a job title manually.";
    modeTabs.forEach((t) => {
      t.classList.remove("active");
      t.setAttribute("aria-selected", "false");
    });
    const manual = document.querySelector('.input-mode-tabs .tab[data-mode="manual"]');
    manual?.classList.add("active");
    manual?.setAttribute("aria-selected", "true");
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
  if (data.skills?.length) form.skills.value = data.skills.join(", ");
  if (data.experience) form.experience.value = data.experience;
  if (data.suggested_remote) {
    form.remote.checked = true;
    document.getElementById("advanced-details").open = true;
  }
}

function clearResultsUi() {
  resultsEl.innerHTML = "";
  resultsMeta.textContent = "";
  resultsWarnings.hidden = true;
  resultsError.hidden = true;
  categoryNav.hidden = true;
  categoryNav.innerHTML = "";
}

function showResultsPanel() {
  emptyState.hidden = true;
  resultsPanel.hidden = false;
}

function setLoading(loading) {
  form.classList.toggle("loading", loading);
  submitBtn.disabled = loading;
  btnSpinner.hidden = !loading;
}

async function copyAllQueries() {
  if (!lastDorkResults) return;
  const all = lastDorkResults.categories.flatMap((c) => c.dorks.map((d) => d.query)).join("\n\n");
  await copyText(all, copyAllBtn);
  showToast(`Copied ${lastDorkResults.total} queries`);
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
        return;
      }
      const orig = btn.textContent;
      btn.textContent = "Copied!";
      btn.classList.add("copied");
      setTimeout(() => {
        btn.textContent = orig;
        btn.classList.remove("copied");
      }, 1500);
    }
  } catch {
    showToast("Could not copy to clipboard", { type: "error" });
  }
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
  } catch {
    return iso;
  }
}
