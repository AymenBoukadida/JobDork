function text(data, name) {
  return data.get(name)?.toString().trim() || "";
}

function mode(value, fallback) {
  const normalized = String(value ?? "").toLowerCase();
  return normalized === "and" || normalized === "or" ? normalized : fallback;
}

function list(value) {
  return Array.isArray(value)
    ? value
        .filter((item) => typeof item === "string" && item.trim())
        .map((item) => item.trim())
    : [];
}

function stringValue(value) {
  return typeof value === "string" ? value.trim() : "";
}

export function asHistoryList(value) {
  return Array.isArray(value) ? value : [];
}

export async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export function requireArrayField(data, field, label) {
  const value = data && typeof data === "object" ? data[field] : null;
  if (!Array.isArray(value)) {
    throw new Error(`Unexpected response from the server (missing ${label}).`);
  }
  return value;
}

export function splitCommaList(value) {
  const seen = new Set();
  const terms = [];
  for (const part of String(value ?? "").split(",")) {
    const term = part.trim();
    const key = term.toLowerCase();
    if (term && !seen.has(key)) {
      seen.add(key);
      terms.push(term);
    }
  }
  return terms;
}

export function buildPayload(data, selectedAts) {
  return {
    titles: splitCommaList(data.get("titles")),
    location: text(data, "location"),
    skills: splitCommaList(data.get("skills")),
    exclude_terms: splitCommaList(data.get("exclude_terms")),
    company: text(data, "company"),
    company_domains: splitCommaList(data.get("company_domains")),
    remote: data.get("remote") === "on",
    experience: text(data, "experience"),
    keyword_mode: mode(data.get("keyword_mode"), "and"),
    title_mode: mode(data.get("title_mode"), "or"),
    time_filter: text(data, "time_filter"),
    preset_id: text(data, "preset_id"),
    ats_platforms: selectedAts,
  };
}

export function normalizeHistoryEntry(entry) {
  const source = entry && typeof entry === "object" ? entry : {};
  const titles = list(source.titles);
  const legacyTitle = stringValue(source.title);
  if (!titles.length && legacyTitle) titles.push(legacyTitle);
  return {
    titles,
    location: stringValue(source.location),
    skills: list(source.skills),
    exclude_terms: list(source.exclude_terms),
    company: stringValue(source.company),
    company_domains: list(source.company_domains),
    remote: Boolean(source.remote),
    experience: stringValue(source.experience),
    time_filter: stringValue(source.time_filter),
    preset_id: stringValue(source.preset_id),
    keyword_mode: source.keyword_mode === "or" ? "or" : "and",
    title_mode: source.title_mode === "and" ? "and" : "or",
    ats_platforms: Array.isArray(source.ats_platforms) ? source.ats_platforms : null,
  };
}

export function historyKey(config) {
  return JSON.stringify(normalizeHistoryEntry(config));
}

function detailMessage(detail) {
  if (typeof detail === "string") return detail.trim();
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item.trim();
        if (!item || typeof item !== "object") return "";
        const field = Array.isArray(item.loc)
          ? item.loc.filter((part) => part !== "body").join(".")
          : "";
        const message = typeof item.msg === "string" ? item.msg.trim() : "";
        if (field && message) return `${field}: ${message}`;
        return message;
      })
      .filter(Boolean)
      .join("; ");
  }
  if (detail && typeof detail === "object" && typeof detail.message === "string") {
    return detail.message.trim();
  }
  return "";
}

export function formatRequestError(response, body) {
  const status = Number(response?.status) || 0;
  const detail = detailMessage(body?.detail);
  if (status === 0) {
    return "Could not reach the server. Check your connection and try again.";
  }
  if (detail) return detail;
  if (status >= 500) {
    return "The server hit a problem while generating dorks. Try again in a moment.";
  }
  return `Request failed (${status}).`;
}
