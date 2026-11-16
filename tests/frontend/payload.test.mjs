import assert from "node:assert/strict";
import test from "node:test";

import {
  asHistoryList,
  buildPayload,
  formatRequestError,
  historyKey,
  normalizeHistoryEntry,
  readJson,
  requireArrayField,
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

test("formatRequestError renders FastAPI 422 detail arrays as readable text", () => {
  const message = formatRequestError(
    { status: 422 },
    {
      detail: [
        { loc: ["body", "titles", 0], msg: "Input should be a valid string" },
        { loc: ["body", "skills"], msg: "Too many skills" },
        "plain detail",
      ],
    },
  );
  assert.equal(
    message,
    "titles.0: Input should be a valid string; skills: Too many skills; plain detail",
  );
  assert.doesNotMatch(message, /\[object Object\]/);
});

test("formatRequestError tolerates odd payload shapes", () => {
  assert.equal(formatRequestError({ status: 422 }, { detail: [] }), "Request failed (422).");
  assert.equal(
    formatRequestError({ status: 400 }, { detail: { message: "Nested message" } }),
    "Nested message",
  );
  assert.equal(formatRequestError(null, null), formatRequestError({ status: 0 }, {}));
  assert.match(formatRequestError({ status: 422 }, "not an object"), /422/);
});

test("readJson returns parsed JSON and null for invalid bodies", async () => {
  assert.deepEqual(await readJson({ json: async () => ({ ok: true }) }), { ok: true });
  assert.equal(
    await readJson({
      json: async () => {
        throw new SyntaxError("Unexpected token <");
      },
    }),
    null,
  );
});

test("requireArrayField returns arrays and rejects malformed payloads", () => {
  const presets = [{ id: "data" }];
  assert.equal(requireArrayField({ presets }, "presets", "preset list"), presets);
  assert.throws(
    () => requireArrayField({ presets: "nope" }, "presets", "preset list"),
    /missing preset list/,
  );
  assert.throws(
    () => requireArrayField(null, "presets", "preset list"),
    /Unexpected response from the server/,
  );
});

test("asHistoryList only accepts arrays", () => {
  assert.deepEqual(asHistoryList([{ id: 1 }]), [{ id: 1 }]);
  assert.deepEqual(asHistoryList("[]"), []);
  assert.deepEqual(asHistoryList(null), []);
  assert.deepEqual(asHistoryList({ length: 1 }), []);
});

test("history entries round-trip through the payload contract", () => {
  const data = new FormData();
  data.set("titles", "Data Engineer, Analytics Engineer");
  data.set("location", "Tunis");
  data.set("skills", "SQL, dbt");
  data.set("exclude_terms", "intern");
  data.set("company", "Stripe");
  data.set("company_domains", "stripe.com");
  data.set("experience", "mid level");
  data.set("time_filter", "30d");
  data.set("preset_id", "data");
  data.set("keyword_mode", "or");
  data.set("title_mode", "or");
  data.set("remote", "on");

  const payload = buildPayload(data, ["greenhouse", "lever"]);
  const entry = normalizeHistoryEntry(payload);

  assert.deepEqual(Object.keys(entry).sort(), Object.keys(payload).sort());
  for (const field of [
    "titles",
    "location",
    "skills",
    "exclude_terms",
    "company",
    "company_domains",
    "remote",
    "experience",
    "time_filter",
    "preset_id",
    "keyword_mode",
    "title_mode",
    "ats_platforms",
  ]) {
    assert.deepEqual(entry[field], payload[field], field);
  }
  assert.equal(historyKey(payload), historyKey(entry));
});

test("normalizeHistoryEntry trims list items and drops non-strings", () => {
  const entry = normalizeHistoryEntry({
    titles: ["  Engineer  ", "", 42, "Engineer"],
    skills: [" Python ", null],
  });
  assert.deepEqual(entry.titles, ["Engineer", "Engineer"]);
  assert.deepEqual(entry.skills, ["Python"]);
});
