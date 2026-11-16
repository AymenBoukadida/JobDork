# JobScout Dorks Refinement Design

## Intent

Make JobScout Dorks feel like a polished, dependable job-search workspace while preserving its current purpose: turning a small set of job preferences into useful Google queries for boards, ATS platforms, company career pages, remote listings, and niche sources.

The refinement covers both sides of the product:

- **Logic quality:** normalize input consistently, remove duplicate frontend behavior, make state transitions predictable, and keep query-generation behavior protected by tests.
- **Product polish:** improve hierarchy, scanning, feedback, accessibility, responsive behavior, and visual consistency without adding a frontend framework or a backend service.

## Goals

- Keep the existing FastAPI and vanilla JavaScript architecture.
- Make the primary search flow understandable without documentation.
- Make generated results easier to scan, copy, and open.
- Improve empty, loading, validation, and error states.
- Strengthen input normalization and API validation at the existing boundaries.
- Remove obvious duplication and improve frontend structure without speculative abstractions.
- Preserve existing features: presets, CV parsing, history, ATS selection, remote search, query warnings, and privacy behavior.
- Add or update focused tests for changed logic.

## Non-goals

- No scraping of Google or job sites.
- No authentication, database, accounts, or cloud deployment.
- No new frontend framework or dependency unless the existing implementation proves insufficient.
- No large feature expansion such as saved accounts, notifications, ranking, or a full results database.
- No removal of existing search categories or supported ATS platforms.

## Anti-goals

- Do not turn the form into a dense enterprise dashboard.
- Do not hide important controls behind unexplained interactions.
- Do not use visual polish to conceal weak validation or unclear query behavior.
- Do not introduce animation that slows down search or harms reduced-motion users.

## Current findings

- The app already has a coherent dark visual foundation and a responsive two-column layout.
- The frontend is concentrated in `static/app.js`; it is serviceable but mixes API loading, form state, rendering, history, CV parsing, and clipboard behavior.
- `getFormPayload()` currently assigns `company` twice.
- Backend normalization is split between Pydantic request validation and `SearchParams`; the existing behavior should be preserved while making accepted values more explicit and testable.
- Existing Python tests cover query construction and CV parsing well, but there is no focused coverage for frontend-facing payload semantics or API validation edge cases.

## Approaches considered

### A. Minimal patch

Fix the duplicate field, tighten a few validations, and adjust a small set of styles. This is safest and fastest, but it would not deliver the requested overall polish or meaningfully improve the interaction model.

### B. Full rewrite or framework migration

Move the UI to a frontend framework and redesign the app around new components. This could improve long-term structure, but it introduces build tooling, dependencies, and migration risk that the current product does not need.

### C. Focused refinement on the existing stack — selected

Keep FastAPI and vanilla JavaScript, but establish clearer boundaries inside the current files, improve the form and results experience, and add tests around the logic that changes. This gives the largest user-visible improvement per line changed and avoids a migration that is unrelated to the product goal.

## Design direction

Use a calm, high-contrast productivity-tool aesthetic:

- Keep the dark theme, but reduce competing glow/shadow effects and rely more on clear surfaces, borders, and spacing.
- Use a restrained teal/cyan action color with a warm accent only for high-attention actions or warnings.
- Keep typography technical and readable, with strong result labels and comfortable body text.
- Treat the search form as the primary task surface and results as a focused workspace.
- Prefer explicit SVG icons with accessible labels over emoji-based visual controls.
- Use short transitions, visible focus states, and a reduced-motion fallback.

## Proposed changes

### Logic and maintainability

- Centralize frontend form payload construction and remove duplicate fields.
- Make API loading failures visible instead of silently leaving empty controls.
- Improve request error handling for non-JSON and network failures.
- Preserve history compatibility while making restored form state deterministic.
- Normalize and validate relevant backend enum-like inputs (`keyword_mode`, `title_mode`, experience/time filters, and ATS selections) at the request boundary without changing valid existing requests.
- Add focused tests for invalid modes, empty/duplicate values, protected query suffixes, and API responses where appropriate.

### UI and interaction

- Make the first step more obvious with a stronger title field and concise helper copy.
- Improve preset cards, segmented controls, advanced filters, ATS selection, and CV upload feedback.
- Make loading state communicate that query generation is in progress and prevent duplicate submits.
- Improve results metadata, category navigation, query readability, and copy/open actions.
- Add clearer empty, warning, failure, and success states.
- Improve responsive behavior at approximately 375px, 768px, 1024px, and desktop widths.
- Ensure keyboard focus, touch target size, status announcements, and reduced-motion behavior are reliable.

## Files likely to change

- `static/index.html`
- `static/style.css`
- `static/app.js`
- `app/main.py`
- `app/dork_engine.py` or related validation helpers only where needed
- Existing `tests/` files plus focused new tests if the current suite cannot express the behavior cleanly
- `README.md` only if the user-facing workflow or run instructions change

## Success criteria

- Existing test suite passes unchanged except for intentional additions.
- Invalid user input receives a clear, local error and does not send a malformed request.
- API failures leave the user with an actionable message and a usable form.
- A generated result set is easier to scan and operate on keyboard and touch.
- Existing features continue to work: presets, CV parsing, history, ATS selection, copy all, individual copy, and Google links.
- The page remains usable without horizontal scrolling on a 375px viewport.
- No new runtime dependency is required.
