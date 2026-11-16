# JobScout Dorks Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve JobScout Dorks' logic quality, reliability, accessibility, responsive behavior, and overall visual polish while preserving the existing FastAPI + vanilla JavaScript product and search behavior.

**Architecture:** Keep the existing backend modules and static frontend. Tighten request normalization in `app/main.py` and `app/dork_engine.py`, protect behavior with focused Python tests, then refine the existing `static/index.html`, `static/app.js`, and `static/style.css` without introducing a frontend framework or runtime dependency.

**Tech Stack:** Python, FastAPI, Pydantic, pytest, semantic HTML, CSS, ES modules, browser `fetch`/Storage/Clipboard APIs.

**Spec:** `docs/superpowers/specs/2026-11-16-jobscout-refinement-design.md`

## Global Constraints

- Keep FastAPI and vanilla JavaScript; do not migrate frameworks.
- Do not add a runtime dependency.
- Preserve presets, CV parsing, history, ATS selection, remote search, query warnings, copy actions, and Google links.
- Do not scrape Google or job sites.
- Keep important controls visible and keyboard accessible.
- Respect reduced motion and avoid horizontal scrolling at 375px.
- Preserve existing valid query-generation behavior unless a test demonstrates a bug.

## Review Focus

- **Malformed enum values:** invalid `keyword_mode`, `title_mode`, experience, time filter, or ATS ids should fail clearly or normalize consistently; cover in backend tests.
- **Duplicate/blank input:** repeated titles, skills, domains, and empty comma-separated values should not create duplicate query terms; cover with `SearchParams` tests.
- **Network/API failures:** failed metadata requests and non-JSON API errors should produce actionable UI feedback instead of a silent empty control; cover with browser-level manual verification and small pure helper tests where possible.
- **Long/protected queries:** trimming must preserve site filters and exclusions; retain and extend query-builder tests.
- **Small screens and keyboard use:** the form, results actions, tabs, dialogs/panels, and category links must remain usable at 375px with visible focus; verify with a local browser pass.

---

### Task 1: Lock down backend normalization and request validation

**Files:**
- Modify: `app/main.py:60-99, 140-161`
- Modify: `app/dork_engine.py:64-137`
- Test: `tests/test_dork_engine.py`
- Test: `tests/test_query_builder.py`

**Interfaces:**
- Consumes: existing `DorkRequest`, `SearchParams`, `generate_dorks`, and `resolve_ats_platforms` interfaces.
- Produces: the same public `/api/dorks` response shape, with deterministic validation for supported values and normalized list inputs.

- [ ] **Step 1: Add failing tests for request and parameter edge cases**

Add tests that establish:

- duplicate/blank titles and skills are removed case-insensitively while preserving order;
- invalid `keyword_mode` and `title_mode` resolve to their documented defaults (or produce the chosen clear validation error, consistently at the request boundary);
- unsupported time-filter values do not create an invalid Google clause;
- an unknown ATS id raises the existing `ValueError` with the existing error wording;
- an empty title remains rejected unless a valid preset supplies titles.

- [ ] **Step 2: Run the focused tests and verify the new cases fail or expose the current behavior**

Run: `pytest tests/test_dork_engine.py tests/test_query_builder.py -q`

Expected: existing tests pass; at least the newly added assertions fail before implementation if they describe behavior not currently guaranteed.

- [ ] **Step 3: Implement the smallest normalization/validation change**

Keep `SearchParams` as the canonical normalization layer. Use one normalization path for list values, preserve first-seen order, keep the current six-title/five-domain limits, and validate only values that the query engine actually supports. Do not change generated categories or query templates.

- [ ] **Step 4: Run the focused tests and the complete Python suite**

Run: `pytest tests/test_dork_engine.py tests/test_query_builder.py -q` then `pytest -q`

Expected: PASS with no regressions.

- [ ] **Step 5: Commit the backend logic work**

```bash
git add app/main.py app/dork_engine.py tests/test_dork_engine.py tests/test_query_builder.py
git commit -m "fix: normalize search parameters consistently"
```

### Task 2: Make frontend state and API handling deterministic

**Files:**
- Modify: `static/app.js:1-307, 369-515`
- Modify: `static/js/storage.js` only if a compatibility-safe helper is needed
- Test: `tests/test_frontend_contracts.py` if pure payload/serialization helpers are extracted; otherwise manual browser verification documented in the task result

**Interfaces:**
- Consumes: existing DOM ids, `/api/presets`, `/api/time-filters`, `/api/ats-platforms`, `/api/dorks`, and `/api/cv/parse` endpoints.
- Produces: stable form payload construction, visible metadata-load failures, actionable request errors, and compatible history restoration.

- [ ] **Step 1: Add or extract pure frontend helpers for testable state rules**

Keep browser-only wiring in `app.js`, but isolate small pure helpers where useful for:

- splitting comma-separated values;
- converting `FormData` to the API payload;
- formatting API/network errors;
- restoring defaults when a saved history entry omits newer fields.

Do not introduce a general state-management abstraction.

- [ ] **Step 2: Remove the duplicate `company` payload property and test the payload contract**

Ensure `company` appears once, `remote` is a boolean, omitted ATS selection remains `null`, and blank comma-separated fields become empty arrays.

- [ ] **Step 3: Improve asynchronous loading and submit error paths**

Update metadata loaders to show a compact status/error in the relevant section rather than silently returning. Make `generateDorks()` handle failed JSON parsing and network failures with a user-facing message. Keep the form usable after errors and prevent duplicate submits while loading.

- [ ] **Step 4: Improve history and CV state restoration**

Restore title mode, keyword mode, filters, ATS selection, and advanced-section state deterministically. Keep old history entries readable. Ensure CV parsing returns the user to the manual form with focus on the title field and preserves the existing review-before-submit behavior.

- [ ] **Step 5: Run the complete Python suite and manually verify frontend flows**

Run: `pytest -q`

Manual browser checks against `uvicorn app.main:app --reload`:

- initial metadata loads populate presets, time filters, and ATS options;
- disabling an API endpoint or simulating a failed request shows a visible error;
- title-only generation, preset generation, history restore, CV parse, copy, and failed generation all leave the UI in a usable state.

- [ ] **Step 6: Commit the frontend logic work**

```bash
git add static/app.js static/js/storage.js tests/test_frontend_contracts.py
git commit -m "refactor: make search form state predictable"
```

### Task 3: Refine semantic markup and interaction feedback

**Files:**
- Modify: `static/index.html:16-255`
- Modify: `static/app.js` render functions and event wiring

**Interfaces:**
- Consumes: existing DOM ids and event handlers from Tasks 1-2.
- Produces: semantic, accessible controls with stable labels, status regions, and result actions.

- [ ] **Step 1: Update markup for clearer hierarchy and status messaging**

Keep existing ids and form names stable. Improve headings, field descriptions, `aria-describedby`, tab semantics, result live-region behavior, and explicit labels for icon/action controls. Replace emoji-only category decoration with accessible SVG or text treatment while preserving category meaning.

- [ ] **Step 2: Improve result card semantics and actions**

Render result categories as sections with meaningful headings, make the query visually distinct and selectable, give copy/open controls accessible names, and expose warning text to assistive technology without making the whole result region overly chatty.

- [ ] **Step 3: Add keyboard and focus behavior where the current flow needs it**

Ensure preset cards, tabs, category links, history actions, ATS controls, and copy actions have visible focus and predictable keyboard behavior. Move focus to the results heading after successful generation only if it does not disrupt the form workflow; otherwise use a polite status announcement.

- [ ] **Step 4: Manually verify semantic interaction behavior**

Use keyboard-only navigation to complete a search, restore history, open advanced filters, select ATS options, copy a query, and jump to a category. Verify the page remains understandable with browser accessibility inspection.

### Task 4: Apply the visual and responsive polish pass

**Files:**
- Modify: `static/style.css`
- Modify: `static/index.html` only for class hooks required by the design

**Interfaces:**
- Consumes: the stable markup and state classes from Tasks 2-3.
- Produces: a restrained productivity-tool visual system that is readable, responsive, and consistent across form, results, feedback, and footer states.

- [ ] **Step 1: Consolidate visual tokens and reduce competing effects**

Keep the dark theme but simplify gradients/shadows, define semantic surface/text/action/warning tokens, and maintain contrast for primary and secondary text. Use the existing font approach unless a local asset or current dependency makes a change clearly safer.

- [ ] **Step 2: Polish primary form surfaces**

Improve the hero, preset cards, segmented controls, advanced disclosure, ATS grid, CV drop zone, buttons, inputs, and validation messages. Keep touch targets at least approximately 44px where practical and retain visible focus rings.

- [ ] **Step 3: Polish results scanning**

Improve category navigation, result headers, metadata, query blocks, warning states, copy/open actions, and empty/error/loading states. Make long queries readable without breaking the layout.

- [ ] **Step 4: Add responsive and reduced-motion behavior**

Verify layouts at 375px, 768px, 1024px, and desktop widths. Remove horizontal overflow, keep sticky behavior from obscuring content, and add `prefers-reduced-motion` rules for pulse/transition effects.

- [ ] **Step 5: Run a browser polish pass and correct regressions**

Run the app locally and check:

- no console errors;
- no horizontal scrolling at 375px;
- focus is visible;
- primary/secondary text is readable;
- loading, warning, error, and success states remain visually distinct;
- existing copy/open/history/CV interactions still work.

- [ ] **Step 6: Commit the UI polish work**

```bash
git add static/index.html static/style.css static/app.js
git commit -m "style: polish job search workspace"
```

### Task 5: Final verification and documentation update

**Files:**
- Modify: `README.md` only if behavior or run instructions changed
- Test: all existing `tests/`

**Interfaces:**
- Consumes: completed backend and frontend changes from Tasks 1-4.
- Produces: verified working tree and documentation that matches the refined behavior.

- [ ] **Step 1: Run the full automated suite**

Run: `pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Run a local smoke test**

Start: `uvicorn app.main:app --reload`

Verify `/`, `/privacy`, `/api/health`, `/api/presets`, `/api/time-filters`, `/api/ats-platforms`, `/api/dorks`, and `/api/cv/parse` respond as expected for valid and invalid requests.

- [ ] **Step 3: Inspect the final diff and repository status**

Run: `git diff --check` and `git status --short`

Expected: no whitespace errors, no generated cache files added, and only intended files changed.

- [ ] **Step 4: Update README only for actual user-facing changes**

Document changed interaction or validation behavior briefly; do not add a speculative feature guide.

- [ ] **Step 5: Commit final documentation/verification changes if needed**

```bash
git add README.md
git commit -m "docs: clarify refined search workflow"
```
