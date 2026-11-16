import assert from "node:assert/strict";
import test from "node:test";

import {
  buildPayload,
  formatRequestError,
  historyKey,
  normalizeHistoryEntry,
  splitCommaList,
} from "../../static/js/form-payload.js";

test("splitCommaList trims, drops blanks, and dedupes case-insensitively", () => {
  assert.deepEqual(splitCommaList(" Python, python ,, AWS "), ["Python", "AWS"]);
  assert.deepEqual(splitCommaList(""), []);
  assert.deepEqual(splitCommaList(undefined), []);
});

test("buildPayload converts form fields to the API contract", () => {
  const data = new FormData();
  data.set("titles", "Software Engineer, Backend Developer");
  data.set("skills", "Python, python, AWS");
  data.set("location", " London ");
  data.set("keyword_mode", "or");
  data.set("title_mode", "and");
  data.set("remote", "on");
  data.set("ats_platforms_raw", "ignored");

  const payload = buildPayload(data, null);

  assert.equal(payload.location, "London");
  assert.deepEqual(payload.titles, ["Software Engineer", "Backend Developer"]);
  assert.deepEqual(payload.skills, ["Python", "AWS"]);
  assert.equal(payload.keyword_mode, "or");
  assert.equal(payload.title_mode, "and");
  assert.equal(payload.remote, true);
  assert.equal(payload.ats_platforms, null);
  assert.deepEqual(Object.keys(payload).sort(), [
    "ats_platforms",
    "company",
    "company_domains",
    "exclude_terms",
    "experience",
    "keyword_mode",
    "location",
    "preset_id",
    "remote",
    "skills",
    "time_filter",
    "title_mode",
    "titles",
  ]);
});

test("buildPayload keeps an explicit ATS subset", () => {
  const data = new FormData();
  data.set("titles", "Engineer");
  assert.deepEqual(buildPayload(data, ["lever", "ashby"]).ats_platforms, [
    "lever",
    "ashby",
  ]);
});

test("historyKey ignores volatile fields and matches equivalent configs", () => {
  const config = { titles: ["Engineer"], location: "Tunis", skills: ["Python"] };
  assert.equal(
    historyKey({ ...config, id: 1, ranAt: "2026-01-01T00:00:00.000Z" }),
    historyKey({ ...config, id: 2, ranAt: "2026-02-01T00:00:00.000Z" }),
  );
  assert.notEqual(historyKey(config), historyKey({ ...config, location: "Berlin" }));
});

test("normalizeHistoryEntry fills defaults for legacy entries", () => {
  const entry = normalizeHistoryEntry({ title: "Old Role", ats_platforms: [] });
  assert.deepEqual(entry.titles, ["Old Role"]);
  assert.deepEqual(entry.skills, []);
  assert.equal(entry.keyword_mode, "and");
  assert.equal(entry.title_mode, "or");
  assert.deepEqual(entry.ats_platforms, []);
  assert.equal(normalizeHistoryEntry(null).ats_platforms, null);
});

test("formatRequestError prefers API detail and explains server failures", () => {
  assert.equal(
    formatRequestError({ status: 400 }, { detail: "At least one job title is required" }),
    "At least one job title is required",
  );
  assert.match(formatRequestError({ status: 500 }, {}), /server/i);
  assert.match(formatRequestError({ status: 404 }, {}), /404/);
  assert.match(
    formatRequestError({ status: 0 }, {}),
    /reach the server|connection/i,
  );
});
