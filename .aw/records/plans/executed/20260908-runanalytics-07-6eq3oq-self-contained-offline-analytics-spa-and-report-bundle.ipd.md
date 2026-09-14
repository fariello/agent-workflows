# IPD: Self-contained offline analytics SPA and report bundle

- Date: 2026-09-08
- Kind: child
- Concern: Present the complete analytical result in one discoverable, portable, accessible, offline report without weakening privacy or statistical context.
- Scope: Build deterministic bundle publication, a self-contained interactive SPA, chart and table views, accessibility, security, size handling, and snapshot retention.
- Scope-Paths: agent_workflows/run_analytics_report.py, agent_workflows/run_analytics_spa.py, agent_workflows/run_analytics_assets/**, tests/test_run_analytics_report.py, tests/test_run_analytics_spa.py, pyproject.toml, .gitignore
- Item-Dependencies: executed:aflsz3
- Status: executed
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 7
- Highest E allocated: 08
- Author: Codex
- Id: 6eq3oq

## Workflow history
- 2026-09-14 executed (aw oc run): aw oc run self-finalize: 6eq3oq verified (set runanalytics, attempt 1). [Scope reconciliation - out-of-scope tests/test_packaging.py: changed by the plan's approved execution (auto-reconciled by aw oc run); in-scope-unmodified .gitignore: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified pyproject.toml: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-08 approved (aw set): status set to approved

- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-083..PR-092, ALL TEN FIXED, no open findings. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE ROOT FINDING IS A CONTRACT BREAK WITH THIS PLAN'S OWN DEPENDENCY (PR-083, F-1): E-02 demands "one interactive chart and exact table for each of the 16 required" analyses, but Order 06 (`aflsz3`) was reviewed the same day and now REFUSES five of those sixteen outright, returning `cannot-determine` because the corpus measures n=3 to 6 for three of them, 1.1 percent model-identity coverage for the model comparison, and zero telemetry runs for resource saturation; five more are reshaped or qualified, leaving only SIX of sixteen chartable as authored. An executor following this plan literally would fabricate five charts from refusals, which destroys the exact property the Set exists to protect. E-04 now renders a REFUSAL PANEL as a first-class view. SECOND, THE PACKAGING CLAIM IS FALSE AS WRITTEN AND WAS MEASURED (PR-084, F-2): the plan says browser assets "must be included by wheel/sdist packaging", but hatchling honors `.gitignore`, and a probe wheel built here SILENTLY DROPPED a gitignored asset with no error; `pyproject.toml` also declares NO wheel include for a new asset directory and the sdist `include` list is explicit and would omit it, while `tests/test_packaging.py` asserts only that forbidden content is ABSENT and would pass with every asset missing. THIRD, THE ATOMICITY DESIGN IS IMPOSSIBLE AS SPECIFIED (PR-085, F-3): `os.replace` on a non-empty target directory raises `OSError` errno 39, measured, so a MULTI-FILE bundle cannot be swapped atomically the way a single file can; the working pattern is publish-to-new-dir plus an atomic symlink flip, also measured, but CI runs `windows-latest` where symlinks need privilege. FOURTH, THE SPA'S DATA VOLUME WAS NEVER SIZED AND IT DECIDES THE ARCHITECTURE (PR-086, F-4): per-step facts are 29766 rows, 3.24 MB minified, 0.93 MB as base64 gzip, and 29766 SVG nodes is past where browsers degrade; measured columnar layout cuts it to 0.71 MB. FIFTH, THE INJECTION FIXTURES UNDERSTATE A HAZARD THAT IS ALREADY REAL (PR-087, F-5): 152 of 216 real outcome files contain HTML-tag-looking substrings (`<id6>` 32 times, `<path>`, `<plan>`), 6 carry FAIL-severity `home-path`/`handle` leaks in free text, and this package contains ZERO uses of `html.escape` anywhere. ALSO FIXED: the plan never said which browser-free test tooling is available, and bs4/lxml/playwright are present in the maintainer venv but ABSENT from `[project.optional-dependencies].test`, so a test importing them passes locally and fails in CI (PR-088, F-6); the three E-items were mechanically sized and the Set orchestrator's OWN blocking OQ-01 names this plan's E-02 as "the whole SPA" and the single densest item in the Set (PR-089, F-7, split to EIGHT); the gate carried no execution contract, the seventh sibling in a row (PR-090, F-8); Order 01 reserves `analytics/` and forbids lane writes via `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS`, which this plan must consume rather than re-derive (PR-091, F-9); and 20 escaped backticks rendered as literal backslashes (PR-092, F-10).

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): specified the on-disk bundle, interactive views, accessibility, offline/security constraints, and publication guarantees.

## Goal

Generate the latest report directly at `<resolved-runs-root>/analytics/index.html`, with companion machine-readable and narrative artifacts in that directory and optional immutable snapshots beneath `analytics/snapshots/`. Opening the HTML from disk must provide useful charts, raw normalized data, quality context, and findings without a server or network.

RESOLVE THAT PATH THROUGH ORDER 01'S RESOLVER, NEVER BY COMPOSING THE LITERAL. Order 01 (`xbwq8n`) exists to remove the `.aw/records/runs` literal from its six live sites and to expose `analytics/`, `analytics/cache/`, `analytics/snapshots/`, `analytics/exports/` plus a `path_is_within_analytics` predicate. Composing the path here would re-create the seventh site.

RENDER WHAT ORDER 06 ACTUALLY PRODUCES, WHICH INCLUDES REFUSALS. Order 06 (`aflsz3`) refuses five of the sixteen required analyses on measured grounds and reshapes five more (F-1). This report's job is therefore NOT twenty charts; it is however many charts the data supports plus an honest, prominent account of what could not be computed and why. A chart fabricated from a `cannot-determine` verdict is the single worst outcome this Set can produce.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RIGHT-SIZING NOTE. Authored with THREE E-items, as were all ten children of this Set. The orchestrator `5lxvl3`'s own OPEN blocking question OQ-01 names THIS plan's E-02 as the clearest case in the entire Set: "Order 07 E-02 is one item for the ENTIRE SPA (linked filters, metric/phase toggles, charts, tables, findings, pricing, quality, and raw-data exploration)". Six siblings were already split for the identical reason (`bzz5e6` 3->6, `lhccjf` 3->8, `5f2h8i` 3->7, `8hald1` 3->8, `aflsz3` 3->9). Split into EIGHT items across four groups (publication / data contract / views / hardening).

### Task group 1: Publication

- [x] E-01 Implement the bundle's DIRECTORY publication using a scheme that is actually atomic, since the authored one is not.
  MEASURED: `os.replace` REFUSES a non-empty target directory with `OSError` errno 39 ("Directory not empty"), so the single-file atomic-rename pattern this repository uses in 60 places (`artifact_core.atomic_write:118` is the canonical helper) DOES NOT generalize to a multi-file bundle. The plan's "a failure leaves the previous latest bundle intact" is therefore unimplementable as stated.
  MEASURED ALTERNATIVE: publish into a fresh versioned directory, then flip a `latest` SYMLINK with `os.symlink` to a temp name followed by `os.replace`, which succeeds and is observably atomic. THE CATCH IS WINDOWS: CI runs `windows-latest` (`.github/workflows/tests.yml:24`), where creating a symlink requires Developer Mode or elevation, and this package's only `os.symlink` call (`layout_migration.py:486`) is in a preserve-symlink branch, not a create-a-link-as-policy path. So choose and IMPLEMENT a documented fallback: on a platform where the symlink attempt raises, publish to the versioned directory and then replace the flat files one at a time in a documented order with the manifest LAST, so a reader that finds a manifest can trust the files it names. Record the choice; do not leave it to the executor to discover mid-run.
  - Depends on: none
  - Expected outcome: publication is transactional in a way that is TESTED by fault injection (kill between file writes) and never leaves a half-written bundle a reader can mistake for complete; the manifest is written last and is the completeness signal; the Windows no-symlink path is implemented and tested, not merely mentioned.
  - Execution state: performed

- [x] E-02 Make the browser assets actually ship, and prove it, because the authored claim is measurably false.
  MEASURED AT REVIEW WITH A PROBE BUILD: hatchling HONORS `.gitignore`. A probe package with `pkg/assets/{index.html,app.css,ignored.html}` and `.gitignore` naming `ignored.html` produced a wheel containing the first two and SILENTLY OMITTING the third, with no warning and exit 0. Three consequences the plan did not account for. FIRST, `[tool.hatch.build.targets.wheel]` declares only `packages = ["agent_workflows"]` plus one `force-include` for `.aw/system`, so a new `agent_workflows/run_analytics_assets/` directory ships ONLY if it is inside the package directory AND not gitignored. SECOND, `[tool.hatch.build.targets.sdist].include` is an EXPLICIT allowlist (`/agent_workflows`, `/.aw/system`, `/hatch_build.py`, `/pyproject.toml`, `/README.md`, `/LICENSE`, `/NOTICE`), so an asset outside `/agent_workflows` is absent from the sdist. THIRD, and worst, `tests/test_packaging.py` asserts what must NOT be present (`FORBIDDEN_TOP`, `FORBIDDEN_AGENTS_SUBSTRINGS`) plus a handful of named modules, so it would pass with every browser asset missing. Verified: `python3 -m pytest tests/test_packaging.py` reports `7 passed`, and none of the seven would notice.
  `.gitignore` is in `Scope-Paths` for exactly one reason: the repo-wide `*.untracked*` and build-artifact patterns must not accidentally match an asset filename. Do not weaken any existing pattern; the `*.untracked.*` block carries a DO-NOT-NARROW warning.
  - Depends on: E-01
  - Expected outcome: assets live inside `agent_workflows/` and are proven present in BOTH the wheel and the sdist by a POSITIVE assertion added to the packaging test (name each asset), plus a test that an asset matching a gitignore pattern is detected rather than silently dropped; `pyproject.toml` updated only if the measured build requires it, with the reason recorded.

  - Execution state: performed

### Task group 2: The embedded data contract

- [x] E-03 Choose and implement the embedded data layout against the MEASURED volume, because it decides the whole architecture.
  MEASURED FROM THE REAL CORPUS, and the plan sized none of this. Per-step facts (the grain Order 05 requires so medians and quantiles can be computed without reparsing) are 29766 rows. As minified JSON that is 3.24 MB; gzipped 0.70 MB (4.7x); as the base64 text a single HTML file must actually embed, 0.93 MB. A COLUMNAR layout (one array per field rather than one object per row) measures 2.11 MB raw, 0.53 MB gzipped, 0.71 MB base64, a 24 percent saving on the embedded size and a larger one on parse time. Per-ATTEMPT aggregates alone are 39 KB, which is comfortable but forecloses every distribution and quantile the Set exists to provide.
  THE RENDERING CONSEQUENCE IS SHARPER THAN THE SIZE. 29766 points as individual SVG `<circle>` nodes is roughly 1.34 MB of markup and 29766 DOM nodes, which is past where browsers degrade; as SVG path data it is roughly 0.36 MB and one node. Canvas avoids both but is not accessible and cannot be asserted structurally, which collides directly with E-06 and E-07. So the decision is: aggregate/bin for the plotted series, keep the per-step rows available for the raw view via pagination, and use SVG paths rather than per-point nodes. Decide it HERE with the measurement, not at render time.
  - Depends on: E-02
  - Expected outcome: ONE documented embedded data contract with the layout choice and its measured basis; a size budget with a test asserting the produced `index.html` stays under it for the corpus-scale fixture; plotted series are pre-binned or path-rendered so DOM node count stays bounded regardless of row count; the raw view pages rather than materializing every row.
  - Execution state: performed

- [x] E-04 Render Order 06's REFUSALS as a first-class view, not as missing charts.
  THIS IS THE MOST IMPORTANT CORRECTION IN THIS REVIEW. E-02 as authored demands "one interactive chart and exact table for each of the 16 required and at least four corpus-supported analyses from Order 06". Order 06 as reviewed the same day REFUSES five of those sixteen: analysis 5 (failed-merge waste, measured n=3 to 6), 8 (merge/conflict recurrence, n=3), 10 (test retry loops, n=6), 12's model arm (1.1 percent identity coverage), and 15 (resource saturation, zero of 135 runs carry `telemetry/`). Five more are reshaped or partially refused: 1 (instruction-read TIME is 0.014 percent of elapsed and was reshaped into a token measure), 3 and 11 (retry arms under-powered), 4 (merge subcategories at n=3), 13 (verifier phase derivable only from a filename). SO ONLY SIX OF SIXTEEN ARE CHARTABLE EXACTLY AS THIS PLAN ASSUMES. An executor honoring the authored wording literally would invent five charts out of refusals, which is precisely the "impressive charts are not evidence" failure Order 06's gate forbids.
  - Depends on: E-03
  - Expected outcome: a refusal is rendered with equal prominence to a chart, naming the analysis, the reason, and the observed sample size or coverage; the report NEVER renders a chart for a `cannot-determine` verdict; a test asserts that feeding a refusal produces the refusal view and NOT an empty or zero-valued chart; the overview states how many of the required analyses were computed versus refused.
  - Execution state: performed

### Task group 3: The interactive views

- [x] E-05 Implement the linked filter, metric and phase controls over one shared data contract.
  Users can switch time, cost, and input/output/cache/total tokens; aggregate, review, execute, verifier and recovery phases; and filter by model, runner, date, set, IPD, outcome, attempt and node pseudonym. Charts and exact tables update from the SAME data so a table can never disagree with the chart above it.
  TWO MEASURED CONSTRAINTS ON THE FILTER SET. The `model` filter will be empty or near-empty for historical data (identity resolves for 2 of 179 attempts), so it must render an honest empty state rather than an apparently-working control over one value. The `verifier` phase exists in 57 session logs but at ZERO attempt records, so the phase control's verifier option is populated from a derived signal and must be labeled derived.
  - Depends on: E-04
  - Expected outcome: one embedded data contract feeds every view; a control whose underlying dimension is empty or single-valued renders a documented empty/degenerate state rather than a dead control; the verifier phase is labeled derived; a test proves a chart and its exact table are computed from the same rows.
  - Execution state: performed

- [x] E-06 Implement the overview, pricing, quality, findings and raw-data views with their uncertainty context.
  The overview carries corpus coverage, totals, distributions, incomplete/missing data, cache behavior, runner and PRICE-ERA composition, and ranked findings. Pricing shows recorded price/cost distinctly from estimated, with source, version, effective dates and unknown-price states; note Order 06 measured two exact price eras and no `cache_write` rate, so the pricing view has a real two-era composition to show rather than a placeholder. The interpretation panel describes overlap, missingness, sample size, uncertainty, association versus causation, and the current filter population.
  THE OVERLAP AND UNATTRIBUTED FIGURES ARE THE HEADLINE, NOT A FOOTNOTE. Order 06 measured tool activity at 3.8 percent of run wall time, so 96.2 percent is unattributed. A time view that shows only classified activity shows 4 percent of the truth while looking complete. Publish unattributed time by default in every time view.
  - Depends on: E-05
  - Expected outcome: every required panel present; recorded and estimated cost visually distinct and never merged; the two price eras shown as a composition; unattributed time shown by default on every time view; the interpretation panel reflects the CURRENT filter population rather than the whole corpus.
  - Execution state: performed

### Task group 4: Hardening

- [x] E-07 Enforce offline behavior and injection safety, with the escaping proven rather than assumed.
  THE HAZARD IS ALREADY IN THE REAL DATA, MEASURED. 152 of 216 real outcome files contain `<`, `>` or `&` in free text, and HTML-tag-looking substrings are common: `<id6>` appears 32 times, plus `<id>`, `<run-id>`, `<path>`, `<plan>`, `<summary>`, `<repo>`, `<selector>` and `<agent/model>`. Separately, 6 of those 216 files carry FAIL-severity leaks (`home-path` and `handle`) in `partial_work_location` or `summary`, containing real absolute worktree paths. AND THIS PACKAGE CONTAINS ZERO USES OF `html.escape`: a repo-wide search finds only `re.escape`. So there is no existing escaping helper to reuse and no precedent to copy, which makes this greenfield and worth its own item.
  Note the interaction with Order 02: its projector is an allowlist that "passes an explicit allowlist and refuses unknown keys", so free-text fields SHOULD never reach a fact. Do not rely on that alone. The projector protects the CACHE; this item protects the RENDER, and a report may legitimately show a finding string that Order 06 generated. Escape at the render boundary regardless of what upstream promises.
  - Depends on: E-06
  - Expected outcome: a single documented escaping boundary every string crosses before entering HTML, SVG, or a JS string literal (three different contexts with three different escapes); a static scan proving no `http:`, `https:`, external script/link/font/image, dynamic import, `fetch`, `XHR` or WebSocket appears in the output; injection fixtures built from the REAL measured shapes (`</script>`, `<id6>`, a formula-leading cell, Unicode controls, a bidi override) plus `aw sanitize --agent` run over the produced bundle with a CONTROL run proving the same invocation flags a raw absolute path.
  - Execution state: performed

- [x] E-08 Implement accessibility and the large-dataset fallback with tooling that EXISTS IN CI.
  THE TEST-TOOLING QUESTION IS DECISIVE AND THE PLAN NEVER ASKED IT. Measured: `bs4` 4.15.0, `lxml` and `playwright` are all importable in this maintainer venv, and NONE of them is in `[project.optional-dependencies].test`, which is exactly `["pytest>=8", "pytest-xdist>=3", "pytest-randomly>=3", "PyYAML>=6"]`; CI installs `-e ".[test]"` (`.github/workflows/tests.yml:70`). So a test importing bs4 or driving playwright PASSES on the maintainer's box and FAILS or silently skips in CI, and no test in the suite imports any of them today. The repository already treats this as a reproducibility defect in `pyproject.toml`'s own comment on `pytest-randomly` ("an undeclared dep that alters results is a reproducibility hole, not a convenience").
  MEASURED RESOLUTION: stdlib `html.parser` is sufficient for the structural half. A probe confirmed it extracts `aria-pressed`, `role`, `aria-labelledby`, `scope` and `<caption>` from a representative document, so every DOM-CONTRACT assertion this item needs is reachable with zero new dependencies. What stdlib CANNOT check is computed focus order, contrast ratio, real JS execution, and whether a control's state updates after a click. Those are the honest boundary: assert the structure deterministically, and state plainly in the docs that behavioral a11y was not machine-verified rather than implying it was.
  - Depends on: E-07
  - Expected outcome: keyboard navigability, visible focus, labels, color-independent series encoding, a reduced-motion rule, screen-reader summaries and real data tables, all asserted via stdlib `html.parser` with NO new test dependency; the checks that stdlib cannot perform are named as unverified rather than claimed; size thresholds produce a documented, tested fallback at the measured corpus scale and above.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The run tree is ignored and disposable. Latest reports belong directly in `analytics/` for discoverability; caches, snapshots, and exports occupy named subdirectories. RESOLVE THE PATH THROUGH ORDER 01'S RESOLVER: `xbwq8n` E-01 exposes `analytics/`, `analytics/cache/`, `analytics/snapshots/`, `analytics/exports/` and `path_is_within_analytics`, and exists to remove the `.aw/records/runs` literal from six sites. Composing it here creates the seventh.
- ORDER 01 ALSO MAKES THE ANALYTICS TREE WORKER-FORBIDDEN AND THAT MUST BE PRESERVED. `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` (`worktree_lease.py:876`) already contains `.aw/records/runs/`, so analytics is produced by the human or coordinator invoking the analyzer, never inside a worker lane turn. Do not weaken that predicate to make the report writable from a lane.
- Package code lives under `agent_workflows/`; browser assets stored there must be included by wheel/sdist packaging and rendered into one HTML file. CORRECTED AND MEASURED AT REVIEW: this does not happen by default. Hatchling HONORS `.gitignore` (probe-verified: a gitignored asset was silently dropped from the wheel with exit 0), the sdist `include` list is an explicit allowlist that omits anything outside `/agent_workflows`, and `tests/test_packaging.py` only asserts ABSENCE of forbidden content, so it would pass with every asset missing (`7 passed`, verified). A POSITIVE per-asset assertion is required.
- ATOMIC MULTI-FILE PUBLICATION IS NOT `os.replace`. Measured: `os.replace` on a non-empty target directory raises `OSError` errno 39. The package's 60 atomic writes (canonically `artifact_core.atomic_write:118`) are all SINGLE-FILE temp-then-rename. A `latest` symlink flipped by `os.symlink` plus `os.replace` IS atomic (measured), but CI includes `windows-latest` where symlink creation needs privilege, so a fallback must be implemented rather than assumed.
- The prompt requires one chart per analytical question with button-like multi-select controls. Controls must remain understandable without color and expose their state to assistive technology. NOTE THE CEILING: Order 06 refuses five of the sixteen required analyses and reshapes five more, so "one chart per question" yields SIX charts as specified plus refusal panels, not twenty (F-1).
- Companion JSON/JSONL/Markdown are safe normalized outputs, not original run logs.
- Source run directories remain untouched; report publication writes only under the reserved analytics namespace.
- NO BROWSER-ASSET PRECEDENT EXISTS IN THIS REPOSITORY. A tracked-file search finds zero `.html`, `.js`, `.css` or `.svg` files, and no accessibility helper exists in the package. This work is greenfield, which is why the a11y and escaping items are separated rather than bundled.
- THE TEST TOOLING AVAILABLE IN CI IS NARROWER THAN ON A DEVELOPER BOX. `bs4`, `lxml` and `playwright` import here but are NOT in the declared `test` extra (`pyproject.toml:85`), and CI installs exactly that extra. Stdlib `html.parser` is sufficient for structural DOM assertions (probe-verified for `aria-*`, `role`, `scope`, `<caption>`), so no new dependency is needed.
- THE INJECTION HAZARD IS LIVE, NOT HYPOTHETICAL. 152 of 216 real outcome files contain `<`, `>` or `&` in free text, with `<id6>` alone appearing 32 times; 6 carry FAIL-severity `home-path`/`handle` findings in `partial_work_location` or `summary`. The package contains ZERO uses of `html.escape`.

## Findings

The page must include:

- An overview with corpus coverage, totals, distributions, incomplete/missing data, cache behavior, runner/model/price-era composition, and ranked findings. It must ALSO state how many required analyses were computed versus refused, since five of sixteen are refused (F-1).
- One interactive chart and exact table for each required and corpus-supported analysis THAT ORDER 06 ACTUALLY COMPUTES, and a prominent REFUSAL PANEL for each it does not. Measured against Order 06 as reviewed: 6 of 16 chartable as authored, 5 reshaped or partially refused, 5 refused outright. Never render a chart for a `cannot-determine` verdict.
- Visible model/provider/variant, recorded price/cost, effective estimated price/cost, price source/version/effective dates, and unknown-price states. Note the model dimension is near-empty for historical data (2 of 179 attempts) and must show an honest empty state.
- A raw normalized data view with schema descriptions, pagination or virtualization, download links to safe companion files, and no prompt/conversation/source content. Pagination is not optional at the measured scale: 29766 per-step rows.
- An interpretation panel describing overlap, missingness, sample size, uncertainty, association versus causation, and the current filter population. Unattributed time (96.2 percent measured) is a default element, not a footnote.
- Stable deep-linkable or exportable filter state when feasible without compromising single-file/offline behavior.

### Findings (review, measured 2026-09-08 at HEAD `2b9632fb`)

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | plan E-02 versus Order 06 (`aflsz3`) as reviewed | **THE PLAN DEMANDS CHARTS FOR FIVE ANALYSES ITS OWN DEPENDENCY REFUSES TO COMPUTE.** E-02 requires "one interactive chart and exact table for each of the 16 required" analyses. Order 06, reviewed the same day, returns `cannot-determine` for analysis 5 (n=3 to 6), 8 (n=3), 10 (n=6), 12's model arm (1.1 percent identity coverage) and 15 (zero of 135 runs carry telemetry), and reshapes or partially refuses 1, 3, 4, 11 and 13. Only 6 of 16 are chartable as authored. An executor following the literal wording fabricates five charts from refusals, which is exactly the failure Order 06's gate forbids | cross-read both plans; counted the feasibility verdicts Order 06 now carries per analysis |
| F-2 | HIGH | `pyproject.toml:120-144`; `tests/test_packaging.py`; probe wheel build | **THE ASSET-PACKAGING CLAIM IS FALSE AND NOTHING WOULD CATCH IT.** Measured with a probe package: hatchling HONORS `.gitignore` and silently omitted a gitignored asset from the wheel with exit 0 and no warning. The wheel target declares only `packages = ["agent_workflows"]` plus one `.aw/system` force-include; the sdist `include` is an explicit allowlist omitting anything outside `/agent_workflows`; and `tests/test_packaging.py` asserts only that FORBIDDEN content is absent, so it passes with every browser asset missing (`7 passed`, verified) | probe wheel built and inspected with and without a `.gitignore` entry; pyproject read; packaging test run |
| F-3 | HIGH | plan E-01's atomicity requirement | **`os.replace` CANNOT SWAP A MULTI-FILE BUNDLE, SO "a failure leaves the previous latest bundle intact" IS UNIMPLEMENTABLE AS WRITTEN.** Measured: `os.replace` onto a non-empty target directory raises `OSError` errno 39. All 60 atomic writes in this package are single-file temp-then-rename (`artifact_core.atomic_write:118`). A `latest` symlink flipped via `os.symlink` + `os.replace` IS atomic (measured), but CI runs `windows-latest` where symlink creation needs privilege and the package's only `os.symlink` use is a preserve-existing branch | both operations executed in a scratch directory; CI matrix and `layout_migration.py:486` read |
| F-4 | HIGH | plan E-02's single-file SPA; embedded data volume | **THE DATA VOLUME WAS NEVER SIZED AND IT DETERMINES THE ARCHITECTURE.** Measured over the real corpus: 29766 per-step fact rows are 3.24 MB minified JSON, 0.70 MB gzipped, 0.93 MB as the base64 text a single HTML file must embed; a columnar layout measures 0.71 MB base64, a 24 percent saving. Worse, 29766 points as individual SVG nodes is ~1.34 MB of markup and 29766 DOM nodes, past where browsers degrade, while SVG path data is ~0.36 MB and one node. Canvas fixes rendering but is inaccessible and structurally untestable, colliding with the a11y requirement | serialized real fact rows in both layouts and measured raw/gzip/base64; computed SVG markup and node counts |
| F-5 | HIGH | plan E-03's injection fixtures; package-wide escaping | **THE INJECTION HAZARD IS ALREADY IN THE REAL DATA AND THERE IS NO ESCAPING HELPER TO REUSE.** 152 of 216 real outcome files contain `<`, `>` or `&` in free text, with HTML-tag-looking substrings common (`<id6>` 32 times, plus `<path>`, `<plan>`, `<repo>`, `<selector>`); 6 carry FAIL-severity `home-path`/`handle` findings in `partial_work_location` or `summary` containing real absolute worktree paths. A repo-wide search finds ZERO uses of `html.escape`, only `re.escape`. HTML, SVG and JS-string are three contexts needing three different escapes | scanned all 216 outcome files for markup shapes; ran `leak_sanitizer.scan_text` over their free-text fields; grepped the package for escaping helpers |
| F-6 | MEDIUM | plan E-03's "automated browser-free checks"; `pyproject.toml:85` | **THE PLAN NEVER NAMED ITS TEST TOOLING, AND THE OBVIOUS CHOICES ARE UNDECLARED.** `bs4` 4.15.0, `lxml` and `playwright` all import in this venv; NONE is in the `test` extra, which is exactly pytest/xdist/randomly/PyYAML, and CI installs that extra. So a test using them passes locally and fails in CI, the reproducibility hole `pyproject.toml` already calls out for `pytest-randomly`. Measured resolution: stdlib `html.parser` extracts `aria-pressed`, `role`, `aria-labelledby`, `scope` and `<caption>`, so structural assertions need no new dependency | imported each library; read the declared extra and the CI install step; probed `html.parser` against a representative document |
| F-7 | MEDIUM | plan E-01..E-03; orchestrator `5lxvl3` OQ-01 | **MECHANICALLY SIZED, AND THE SET'S OWN BLOCKING QUESTION CALLS THIS PLAN'S E-02 THE CLEAREST CASE IN THE SET:** "Order 07 E-02 is one item for the ENTIRE SPA (linked filters, metric/phase toggles, charts, tables, findings, pricing, quality, and raw-data exploration)". E-03 likewise bundled accessibility, offline behavior, injection safety, large-dataset behavior and deterministic rendering, which are five unrelated test surfaces. Seventh sibling with this finding | orchestrator plan read; item content counted against the workflow's split diagnostics |
| F-8 | MEDIUM | plan gate as authored | The gate carried two sentences and NO execution contract: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle move, no re-measure warning, no stop conditions. Seventh consecutive sibling with the same omission, so it is a property of the authoring pipeline | plan read; six sibling review records read |
| F-9 | MEDIUM | plan Goal and conventions versus Order 01 (`xbwq8n`) | The plan writes the output path as prose without naming Order 01's resolver, risking a seventh construction of the literal Order 01 exists to remove from six sites, and mis-siting the report for any non-`repository` `records_backend`. It also never records that `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` already makes the tree worker-forbidden, which a lane-based executor might try to weaken | Order 01's plan read; `worktree_lease.py:876` confirmed |
| F-10 | LOW | plan source (20 escaped backticks); suite baseline | Twenty escaped backtick pairs rendered as literal backslashes, after Order 01's six, 02's four, 03's ten, 04's eighteen, 05's sixteen and 06's four, so it is a pipeline artifact. Also no baseline was recorded despite requiring a bare suite run: measured `2 failed, 5655 passed, 3 skipped, 2 xfailed`, both failures pinned to the live mutable plan corpus and pre-existing | `grep -o` count before the fix; bare suite run at review |

## Proposed changes (ordered, validatable)

1. E-01 publishes the bundle transactionally with a scheme that is actually atomic, plus a tested Windows fallback; E-02 makes the assets ship and asserts their presence positively.
2. E-03 fixes the embedded data layout and the DOM-node budget against the measured 29766-row scale.
3. E-04 renders Order 06's five refusals as a first-class view, never as a fabricated chart.
4. E-05 wires the linked controls over one data contract with honest empty states; E-06 adds the overview, pricing, quality, findings and raw views with unattributed time shown by default.
5. E-07 establishes the three-context escaping boundary and the offline scan; E-08 asserts accessibility with stdlib tooling only and names what it cannot verify.

## Deferred / out of scope (with reason)

- A hosted dashboard, web server, database, CDN, or runtime JavaScript dependency is excluded.
- Direct source-run browsing is excluded because it would expose sensitive data.
- CLI command registration is Order 08 (`mm5p3v`), whose `Scope-Paths` cover `cli.py` and `run_analytics_cli.py`. Verified against its front matter.
- Network submission and export tiers are Order 09 (`ixis0c`).
- The run-root resolver and the reserved `analytics/` namespace are Order 01 (`xbwq8n`); the privacy projector and cache are Order 02 (`bzz5e6`); the taxonomy, pricing, statistics and findings this report renders are Order 06 (`aflsz3`). This plan CONSUMES all of them and reimplements none.
- Pixel-perfect branding is secondary to correctness and accessibility.
- BEHAVIORAL accessibility verification (real focus order, contrast ratios, JS-driven state updates after a click) is OUT OF SCOPE for automated testing here, because the tooling that could do it is not a declared dependency (F-6). It must be documented as unverified rather than implied verified.
- IMPROVING the analyses Order 06 refuses is not this plan's work. Rendering the refusal honestly is.

## Scope check

- Over-scope: no ingestion, cache parsing, statistics, runner changes, CLI dispatch, or transport. Specifically, and each for a measured reason: do NOT compose the `.aw/records/runs` literal (Order 01 owns the resolver and the literal already exists at six sites); do NOT weaken `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` to make the report writable from a lane; do NOT add a runtime OR test dependency (`pyproject.toml:50` declares one runtime dep and `:85` four test deps, and stdlib `html.parser` is measured sufficient); do NOT narrow any existing `.gitignore` pattern, especially the `*.untracked.*` block that carries an explicit do-not-narrow warning; do NOT write into any source run directory; do NOT compute or re-derive a statistic Order 06 owns; and do NOT edit a spec, since none is declared in `Scope-Paths`.
- `pyproject.toml` and `.gitignore` ARE in `Scope-Paths`, deliberately and narrowly: the measured packaging defect (F-2) may require a wheel/sdist include, and an asset filename must be proven not to match an ignore pattern. Any edit to either file must be minimal and justified.
- An out-of-scope edit is not forbidden outright, it must be JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.
- Under-scope: includes all report files, the computable views, filters/toggles, accessibility, security, offline use, transactional publication, snapshots, and large-data behavior. The refusal view (E-04), the measured data-layout decision (E-03), the positive packaging assertion (E-02), the workable atomicity scheme (E-01), the three-context escaping boundary (E-07) and the stdlib-only test tooling (E-08) were all under-scope before review.

## Required tests / validation

Baseline, measured bare at HEAD `2b9632fb`: `2 failed, 5655 passed, 3 skipped, 2 xfailed in 95.72s`. Both failures (`tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` and `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`) are pinned to the live mutable plan corpus and are PRE-EXISTING. Re-measure in the executing worktree and compare failing NODE IDS; the criterion is an empty delta against your own baseline, never a total.

FIXTURES ARE AUTHORITATIVE; THE LIVE CORPUS IS A READ-ONLY SMOKE CHECK. Do not pin a test to `.aw/records/runs/`: it is gitignored, mutable, grows with every run, and its outcome files carry absolute paths the leak detector flags at `fail` (measured, 6 of 216). The two current suite failures are themselves live-corpus couplings. Build a corpus-SCALE synthetic fixture (roughly 30000 fact rows, matching the measured 29766) so the size and DOM-budget tests are exercised rather than asserted.

- Golden bundle manifest and deterministic render tests (byte-identical output for identical input, so a diff means a real change).
- Static scan proving no `http:`, `https:`, external script/link/font/image loads, dynamic module imports, or runtime fetch/XHR/WebSocket.
- Injection fixtures built from the REAL measured shapes: `</script>`, a literal `<id6>` (32 real occurrences), `<path>`, a formula-leading cell (`=`, `+`, `-`, `@`), Unicode controls, a bidi override, and a hostile identifier. Assert per CONTEXT: HTML text, an attribute value, SVG text, and a JS string literal are four different escapes and a single helper used everywhere is a defect.
- `aw sanitize --agent` over the produced bundle reporting clean, PLUS a control run proving the same invocation flags a raw absolute path, since a clean report and a detector that was not looking are indistinguishable.
- DOM-contract tests via stdlib `html.parser` ONLY (no bs4, lxml or playwright, none of which is a declared test dep) for every chart/table/control, ARIA state, keyboard-reachable element, visible focus class, text alternative, reduced-motion rule, and the absence of color-only distinction. State explicitly which a11y properties are NOT machine-verified.
- Refusal-rendering tests: each of Order 06's five refused analyses produces a refusal panel naming the reason and the observed n, and NOT an empty or zero-valued chart. A test that a `cannot-determine` input cannot produce a chart element at all.
- Size and node-budget tests at the measured scale: the produced `index.html` stays under a declared budget for a ~30000-row fixture, and the plotted DOM node count stays bounded (path-rendered or pre-binned) rather than scaling with row count.
- Fault injection for publication: interrupt between file writes and assert a reader never sees a half-written bundle; assert the manifest is written LAST; assert the Windows no-symlink fallback path is exercised (simulate `os.symlink` raising).
- Positive packaging assertions: NAME each browser asset and assert its presence in BOTH the wheel and the sdist, plus a test proving a gitignore-matched asset is DETECTED rather than silently dropped (the measured hatchling behavior). Extend `tests/test_packaging.py` rather than writing a parallel one.
- Small, empty, one-run, missing-price, partial, mixed-runner, mixed-price-era, and corpus-scale renders.
- Companion-file schema checks and latest/snapshot replacement and retention tests; retention prunes only tool-owned snapshots.
- No test may reach the network, spawn a browser, spend real time, or parse the live corpus as its assertion source.
- Bare `python3 -m pytest` and `git diff --check`. Run the suite BARE; do not add `-n0`, a second `-q`, or `-p no:randomly`, since `pyproject.toml` `addopts` already supplies the intended flags.

## Spec / documentation sync

Order 10 (`9xycbh`) documents the output tree, open workflow, report/data schemas, browser support, size thresholds, snapshot retention, and privacy caveats. Asset packaging changes are verified there.

THIS PLAN DECLARES NO SPEC FILE IN `Scope-Paths` AND MUST EDIT NONE. Approved spec `kw5y2s` governs the emitted layout; if execution concludes the layout contract must change, that is a STOP-and-raise, not a unilateral edit.

THE DOCUMENTATION MUST CARRY TWO HONEST LIMITS, and both were absent before review. FIRST, WHICH ANALYSES ARE REFUSED AND WHY: five of the sixteen required analyses cannot be computed from this corpus, so a document listing twenty views without saying five are refusals invites the reader to assume all twenty are measured. SECOND, WHAT ACCESSIBILITY WAS NOT VERIFIED: structural ARIA and table semantics are machine-checked, while focus order, contrast ratio and post-click state are not, because the tooling is not a declared dependency. Claiming "accessible" without that boundary is the kind of unearned claim this repository's honesty rules exist to prevent. RE-MEASURE every figure here at execution; the corpus grows with every run.

## Open questions

"No open questions" was not accurate: the plan required four decisions it specified nowhere. All four are answerable from repository evidence or from measurement rather than by asking, so each is recorded resolved with its basis. Every reviewed sibling in this Set carried the same inaccurate claim.

### OQ-01: What does the report render for an analysis Order 06 refuses to compute?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as a FIRST-CLASS REFUSAL PANEL with equal prominence to a chart, naming the analysis, the reason and the observed sample size or coverage. The plan demanded a chart for each of sixteen required analyses; Order 06, reviewed the same day, refuses five outright and reshapes five more, leaving six chartable as authored. REJECTED: rendering an empty chart, because an empty axis reads as "we measured zero" rather than "we could not measure", which is a stronger and falser claim than silence. Omitting the analysis entirely, rejected because its absence is indistinguishable from an oversight and a reader cannot tell the report is complete. Rendering the chart from whatever few points exist, rejected outright because n=3 rendered as a trend is precisely the fabrication Order 06's gate forbids and this Set exists to avoid.

### OQ-02: How is a MULTI-FILE bundle published atomically, given `os.replace` cannot swap a directory?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASUREMENT as publish-to-versioned-directory plus an atomic `latest` symlink flip, WITH an implemented and tested Windows fallback that writes the flat files in a documented order with the manifest LAST. Measured: `os.replace` onto a non-empty directory raises `OSError` errno 39, so the single-file pattern used in all 60 of this package's atomic writes does not generalize; a symlink created to a temp name and then `os.replace`d IS atomic. REJECTED: writing files in place and hoping, because a reader opening `index.html` mid-write sees a truncated document with no way to detect it. A lock, rejected because `platform_lock`'s docstring records that exactly one caller may block and a blocking analytics publisher would hang a driver; and a reader has no lock anyway. Requiring symlink support unconditionally, rejected because CI runs `windows-latest` where symlink creation needs privilege, so it would make the suite fail on a supported platform.

### OQ-03: What test tooling verifies the DOM, and is it available in CI?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW as STDLIB `html.parser` ONLY, with the unverifiable properties named rather than claimed. Measured: `bs4` 4.15.0, `lxml` and `playwright` all import in the maintainer venv, and none is in `[project.optional-dependencies].test` (exactly pytest, pytest-xdist, pytest-randomly, PyYAML), which is what CI installs; no test in the suite imports any of them. A probe confirmed `html.parser` extracts `aria-pressed`, `role`, `aria-labelledby`, `scope` and `<caption>`, covering every structural assertion needed. REJECTED: adding bs4 or lxml to the test extra, because `pyproject.toml` keeps the dependency surface deliberately minimal and stdlib is measured sufficient for the structural half. Adding playwright, rejected more strongly: it downloads browser binaries, needs network, and would make an offline-first report's own test suite require the network. Using the libraries WITHOUT declaring them, rejected because that is exactly the reproducibility hole `pyproject.toml`'s `pytest-randomly` comment documents, where the maintainer and CI run different suites.

### OQ-04: What embedded data layout and grain does the single HTML file carry?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW BY MEASUREMENT as a COLUMNAR layout of per-step facts with pre-binned or path-rendered plotted series and a paginated raw view. Measured over the real corpus: 29766 per-step rows are 3.24 MB row-wise minified (0.93 MB base64-gzip) versus 2.11 MB columnar (0.71 MB base64-gzip), a 24 percent saving on embedded size and more on parse time; and 29766 individual SVG nodes is ~1.34 MB of markup past the point browsers degrade, while path data is ~0.36 MB in one node. REJECTED: per-attempt aggregates only (39 KB, comfortable) because it forecloses every distribution, median and quantile the Set exists to provide, and Order 05 stores per-step facts precisely so they need not be reparsed. Canvas rendering, rejected because it is not accessible and cannot be asserted structurally, which would defeat E-08 and leave the a11y claim unverifiable. An external data file beside the HTML, rejected because the deliverable is explicitly a single self-contained file openable from disk.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the fault-injection test output showing an interruption between file writes leaves NO readable half-bundle, and that the manifest is written LAST and is the completeness signal. Paste the `os.replace`-on-a-directory failure re-measured in the executing worktree (`OSError` errno 39 at review) as the reason the scheme is what it is. Paste the Windows fallback exercised by simulating `os.symlink` raising, showing publication still completes correctly.
  - Observed evidence: RE-MEASURED IN THIS WORKTREE at HEAD `96d13413`, not cited from review. Test output from
    `python3 -m pytest tests/test_run_analytics_report.py -o addopts="" -q -s -k "Measured or fallback or INTERRUPTION"`:

    ```
    MEASURED fault injection: wrote ['analysis.json'] then interrupted; no manifest present, bundle correctly unreadable
    .MEASURED: symlink flip via os.symlink + os.replace succeeded and is atomic
    .MEASURED: os.replace onto a non-empty directory -> OSError errno=39 (Directory not empty)
    .MEASURED fallback engaged: symlink publication unavailable: PermissionError: [Errno 1] symbolic link privilege not held
    4 passed, 20 deselected in 0.35s
    ```

    SO, POINT BY POINT. (1) `os.replace` onto a non-empty directory REFUSES with errno 39, which is
    why the single-file pattern used in this package's ~60 atomic writes does not generalize and why
    the plan's original scheme was unimplementable. (2) The symlink flip IS atomic, confirmed. (3) The
    Windows fallback is EXERCISED by making `os.symlink` raise `PermissionError`, exactly as it does
    without privilege, and publication still COMPLETED correctly flat with the manifest present and
    `verify_bundle` returning no problems. (4) FAULT INJECTION interrupted publication after the first
    file: no manifest was present, `read_manifest` REFUSED the directory as incomplete, and
    `verify_bundle` reported problems, so no reader can mistake the result for a finished bundle. The
    manifest is ordered LAST by `PUBLICATION_ORDER` (asserted by `test_manifest_is_ordered_last`) on
    BOTH paths, and each file is fsync'd before it, so everything the manifest names is durable when
    it appears. A republish removes the OLD manifest FIRST, so an interruption can never leave a stale
    manifest describing new files (`test_an_interrupted_republish_never_leaves_a_STALE_manifest`).
    Full module: `24 passed`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the POSITIVE packaging assertions naming each browser asset and showing it present in BOTH the wheel and the sdist listing. Paste the test proving a gitignore-matched asset is DETECTED rather than silently dropped, with the measured hatchling behavior stated (a probe wheel omitted a gitignored asset at exit 0). Paste the full `tests/test_packaging.py` run. If `pyproject.toml` was edited, paste the diff and the measured reason.
  - Observed evidence: FULL `tests/test_packaging.py` RUN, which was `7 passed` before this plan and is now `13 passed`
    (`python3 -m pytest tests/test_packaging.py -o addopts="" -q -s`):

    ```
    ......MEASURED: hatchling honored .gitignore and omitted pkg/assets/ignored.css from the wheel at exit 0 with no warning
    .....wheel runtime deps (allowlisted): ['Requires-Dist: filelock>=3']
    ..
    13 passed in 6.89s
    ```

    THE POSITIVE ASSERTIONS, naming each asset in BOTH artifacts. `test_wheel_ships_every_browser_asset_BY_NAME`
    and `test_sdist_ships_every_browser_asset_BY_NAME` assert `agent_workflows/run_analytics_assets/app.css`
    and `.../app.js` by name; a separate sdist BUILD is required because the sdist `include` is an
    explicit allowlist and is a different mechanism from the wheel's. Verified present in the real wheel:

    ```
    REAL wheel: assets present -> ['agent_workflows/run_analytics_assets/app.css', 'agent_workflows/run_analytics_assets/app.js']
    assertion on real wheel, missing list: [] -> PASSES
    ```

    AND THE CONTROL, because a passing assertion and an assertion that cannot fail are
    indistinguishable. Removing `app.css` from the namelist the assertion reads:

    ```
    CONTROL with app.css removed, missing list: ['agent_workflows/run_analytics_assets/app.css'] -> correctly FAILS
    CONTROL CONFIRMED: the positive assertion detects a silently dropped asset
    ```

    THE MEASURED HATCHLING BEHAVIOR, REPRODUCED rather than cited: a probe package with a gitignored
    asset built at EXIT 0 and SILENTLY OMITTED it (see the `MEASURED:` line in the run above). That is
    the whole reason absence-only testing was insufficient: the pre-existing seven tests would have
    passed with every asset missing. `test_a_gitignored_asset_would_be_DETECTED_rather_than_silently_dropped`
    now reproduces it in-suite, and `test_no_asset_filename_matches_a_gitignore_pattern` plus
    `test_the_assets_are_TRACKED_by_git_which_is_what_makes_them_ship` (via `git check-ignore`) assert
    the real assets are not matched.

    `pyproject.toml` WAS NOT EDITED, deliberately, and the reason is measured rather than assumed: the
    wheel target already declares `packages = ["agent_workflows"]` so a directory INSIDE the package
    ships automatically, and the sdist allowlist already contains `/agent_workflows`. A probe build
    confirms both assets ship with no config change. Adding config that changes nothing would imply a
    constraint that does not exist. `.gitignore` was likewise NOT touched, so no existing pattern was
    narrowed. Recorded as DECISION 04-6eq3oq-D6. `test_declared_assets_match_the_module` keeps the
    packaging list from falling behind `run_analytics_spa.REQUIRED_ASSETS`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the measured embedded size for the corpus-scale fixture in BOTH layouts, re-measured (row-wise 0.93 MB versus columnar 0.71 MB base64-gzip over 29766 rows at review), and the chosen layout with its budget test passing. Paste the plotted DOM node count for the corpus-scale fixture proving it is bounded and does NOT scale with row count. Paste the raw view paginating rather than materializing all rows.
  - Observed evidence: RE-MEASURED ON THE CORPUS-SCALE FIXTURE (29766 rows, matching the measured per-step count), from
    `python3 -m pytest tests/test_run_analytics_spa.py -o addopts="" -q -s -k "SizeBudget or Bounded or Columnar"`:

    ```
    MEASURED at 29766 rows: index.html is 405179 bytes (0.39 MiB) against a 8 MiB budget
    MEASURED at 29766 source rows: bin_count=240, plotted DOM nodes in document=1 (budget 600)
    MEASURED at 2000 rows: row-wise 330740 bytes, columnar 151013 bytes (54.3% smaller)
    ```

    THE LAYOUT COMPARISON came out STRONGER than the review-time figure and is reported as measured
    rather than as predicted: columnar is 54.3 percent smaller than row-wise on this fixture against
    the 24 percent measured at review. The direction is what the decision rested on and it holds. The
    chosen layout is columnar per-step, recorded in `EMBEDDED_DATA_CONTRACT` together with its basis
    and an explicit `basis_provenance` marking the review figures NOT CURRENT.

    THE DOM NODE COUNT IS BOUNDED AND DOES NOT SCALE WITH ROWS: 29766 source observations render as
    `bin_count=240` and **1** plotted DOM node, against a declared budget of 600, because a series
    becomes ONE `<path>` rather than one node per point (the measured 29766-node defect).
    `test_above_scale_the_plotted_nodes_stay_bounded` repeats the check at TWICE corpus scale
    (59532 rows) and still yields one path node.

    THE SIZE BUDGET PASSES WITH ROOM: 0.39 MiB against the declared 8 MiB ceiling.

    THE RAW VIEW PAGINATES rather than materializing rows:
    `test_the_raw_view_PAGINATES_rather_than_materializing_every_row` asserts the served `<tbody
    id="raw-body">` contains NO `<tr>` at all at 1000 rows, so rows are added per page client-side,
    100 at a time. Determinism holds too: `test_the_whole_document_is_byte_identical_for_identical_input`
    passes, which required `gzip` `mtime=0` and a fixed level (DECISION 04-6eq3oq-D3).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the rendered refusal panel for each of Order 06's five refused analyses (5, 8, 10, 12's model arm, 15), each naming the reason and the observed n or coverage. Paste the test proving a `cannot-determine` input produces NO chart element, with the assertion shown failing against a version that renders an empty chart. Paste the overview line stating computed-versus-refused counts.
  - Observed evidence: ALL FIVE of Order 06's refused analyses render as first-class refusal panels naming the verdict
    and the observed n. `python3 -m pytest tests/test_run_analytics_spa.py -o addopts="" -q -k RefusalRendering`
    reports `7 passed, 102 deselected`. Two of the five rendered panels, verbatim from the produced document:

    ```html
    <article class="panel refusal" role="group" aria-label="Refused analysis: Failed merge waste and retry cost"><h3>Failed merge waste and retry cost</h3><p><span class="verdict">cannot-determine</span> &mdash; observed n=3.</p><p>observed n=3 is below the declared minimum n=12</p></article>
    <article class="panel refusal" role="group" aria-label="Refused analysis: Merge conflict share and recurrence"><h3>Merge conflict share and recurrence</h3><p><span class="verdict">cannot-determine</span> &mdash; observed n=3.</p><p>observed n=3 is below the declared minimum n=12</p></article>
    ```

    Feeding the five (analysis 5 at n=3, 8 at n=3, 10 at n=6, 12's model arm REFUSED at n=2, and 15 at
    n=0) yields `charts: 0 refusals: 5`, and the overview states the split:
    `<strong>0</strong> of <strong>16</strong> required analyses were computed;`.

    A `cannot-determine` INPUT PRODUCES NO CHART ELEMENT AT ALL, which is the assertion that would fail
    against a version rendering an empty chart. `test_a_cannot_determine_result_produces_NO_chart_element`
    parses the document with stdlib `html.parser` and asserts `<figure>`, `<svg>` and `<path>` are ALL
    absent, so there is no empty axis for a reader to misread as a measurement of zero. The guarantee is
    STRUCTURAL rather than a remembered check: `build_view_model` routes on `AnalysisResult.renderable`,
    so a refusal has no code path into `charts`, and `chart_from_result` RAISES `SpaError` on a
    non-computed verdict ("a chart may not be produced for it"). The symmetric refusal is also tested:
    `refusal_from_result` rejects a COMPUTED result, since presenting a computable analysis as refused
    understates the evidence. Caveats travel with the panel.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a chart and its exact table computed from the SAME rows, with a test proving they cannot disagree. Paste the model filter rendering an honest empty/degenerate state at the measured 1.1 percent identity coverage, and the verifier phase option labeled DERIVED. Paste every metric and phase toggle exercised.
  - Observed evidence: `python3 -m pytest tests/test_run_analytics_spa.py -o addopts="" -q -k "LinkedControl or HonestEmptyState"`
    reports `10 passed, 99 deselected`.

    CHART AND TABLE CANNOT DISAGREE, and it is structural rather than promised: both project from ONE
    `row_indices` tuple on the `ChartView`, asserted by
    `test_a_chart_and_its_table_are_computed_from_the_SAME_rows` (indices equal `range(len(rows))` and
    the payload's `row_count` matches) and `test_the_table_rows_are_the_charted_results_own_values`
    (the exact table is the charted result's own `values`: `{'n_sessions': 345, 'share': 0.9862}`).
    There is no second computation that could drift.

    EVERY METRIC AND PHASE TOGGLE IS EXERCISED. All six metrics (time, cost, input/output/cache/total
    tokens) and all five phases (aggregate, review, execute, verifier, recovery) are asserted present
    with `aria-pressed` state, and `test_exactly_one_button_per_group_starts_pressed` asserts exactly
    one pressed per group.

    THE MODEL CONTROL RENDERS AN HONEST DEGENERATE STATE at the measured coverage. At 2 resolved of 179
    attempts the dimension classifies `degenerate` (not `populated`), coverage computes to 1.1 percent,
    and the rendered control is `disabled` AND `aria-disabled="true"` AND `aria-describedby` a note
    reading `degenerate: only one distinct value is present ... Coverage: 1.1%`. It is DISABLED rather
    than HIDDEN, because a hidden control is indistinguishable from an oversight (DECISION
    04-6eq3oq-D7); a single-valued control that looks operable is the worse failure, since it appears
    to filter while describing a fraction of the corpus. An EMPTY dimension is a separate state from a
    DEGENERATE one, since the two mislead differently.

    THE VERIFIER PHASE IS LABELED DERIVED: the option carries `(derived)` and points via
    `aria-describedby` at a note stating it is derived from a log filename rather than recorded, with
    the measured 57 verifier logs against 0 attempts carrying a verify cost.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste each required panel rendered (overview, pricing, quality, findings, raw, interpretation). Paste recorded and estimated cost shown DISTINCTLY and never merged, with the two measured price eras as a composition. Paste a time view showing unattributed time BY DEFAULT with the measured 96.2 percent share. Paste the interpretation panel changing with the filter population rather than describing the whole corpus.
  - Observed evidence: `python3 -m pytest tests/test_run_analytics_spa.py -o addopts="" -q -k RequiredPanel` reports
    `12 passed, 97 deselected`.

    EVERY REQUIRED PANEL IS PRESENT, asserted by id: overview, controls, time-accounting, charts,
    refusals, pricing, quality, findings, interpretation, raw, a11y.

    RECORDED AND ESTIMATED COST ARE NEVER MERGED. They render in distinct `class="recorded"` and
    `class="estimated"` spans whose CSS appends "(recorded)"/"(estimated)" as generated content, so the
    distinction survives even without color, and the panel states it in words. An unknown price is
    reported as REFUSED rather than defaulted ("Steps with no resolvable price: <strong>23</strong> ...
    <strong>refused</strong> rather than priced at a default"), and a population with no era says so
    instead of showing a placeholder.

    BOTH MEASURED PRICE ERAS RENDER AS A COMPOSITION, with era id, effective-from, effective-to
    (`open-ended` for the current one), source, source version and spend share (28.0% / 72.0% in the
    fixture) as a real table.

    UNATTRIBUTED TIME IS SHOWN BY DEFAULT, not as a footnote: "Unattributed time is shown
    <strong>by default</strong> ... classified tool activity accounted for <strong>3.8%</strong> of run
    wall time, leaving <strong>96.2%</strong> unattributed (review-time snapshot)", with a two-row
    attribution table. The figure is LABELED as a review-time snapshot rather than presented as current
    (see DECISION 04-6eq3oq-D4: the live corpus is absent from this lane).

    THE QUALITY PANEL KEEPS THREE SEPARATE COUNTS (missing / unavailable / not applicable) plus a parse
    error count, never one "incomplete" flag, preserving the compatibility-versus-defect distinction.

    THE INTERPRETATION PANEL REFLECTS THE CURRENT POPULATION rather than the corpus, and CHANGES with
    it: `test_the_interpretation_panel_changes_with_the_population` asserts "(2 rows as loaded)" versus
    "(40 rows as loaded)". It carries association-not-causation, overlap, missingness, sample size (with
    the live refused-of-required count) and uncertainty. Findings render with uncertainty, competing
    explanations, caveats and the cheapest discriminating test; a `cannot-determine` finding renders in
    the refusal style rather than as an ordinary one.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the static offline scan showing zero `http:`/`https:`/external asset/dynamic import/fetch/XHR/WebSocket occurrences. Paste each injection fixture rendered INERT, per context (HTML text, attribute, SVG text, JS string literal), using the REAL measured shapes including a literal `<id6>` and a formula-leading cell. Paste `aw sanitize --agent` over the produced bundle reporting clean AND a control run proving the same invocation flags a raw absolute path. State the measurement that motivated this item (152 of 216 real outcome files carry markup characters; 6 carry FAIL-severity leaks; zero uses of `html.escape` existed).
  - Observed evidence: `python3 -m pytest tests/test_run_analytics_spa.py -o addopts="" -q -k "Offline or Injection or ControlCharacter or ThreeContext or LeakSanitizer"`
    reports `23 passed, 86 deselected`.

    THE OFFLINE SCAN IS CLEAN AND ITS CONTROL PROVES IT IS LOOKING. `scan_for_network_references` over
    the produced document returns `[]`. The CONTROL (`test_the_scanner_CONTROL_flags_a_planted_reference`)
    plants `<script src=`, `fetch(`, `https:`, `WebSocket`, `@import` and `import(` and asserts each is
    caught, so a clean result is evidence rather than an absence of looking. `render_document` ITSELF
    scans before returning and RAISES `SpaError` on a violation, so an offline break cannot ship from
    this module. Note the design consequence recorded as DECISION 04-6eq3oq-D1: inline SVG carries NO
    `xmlns`, because the namespace URI would itself be an `http:` occurrence; HTML5 namespaces inline
    SVG by parser rule, so no scan exception was needed. Asserted by
    `test_inline_svg_carries_NO_xmlns_so_the_scan_needs_no_exception`.

    FIVE CONTEXTS, FIVE ESCAPES, EACH ASSERTED SEPARATELY. HTML text, HTML attribute (both quote forms,
    which text escaping deliberately does not do), SVG text, JS string literal (where `</script` is
    broken and `\u2028`/`\u2029` escaped, which no HTML escape does), and a fifth the plan did not
    anticipate: the JSON island. THE JSON ISLAND WAS A REAL DEFECT THIS SUITE CAUGHT: escaping it with
    the JS-string escape produced `\"` sequences that reach the client as literal backslash-quote in
    `textContent`, so `JSON.parse` would have failed on EVERY page load. The correct escape uses
    `\uXXXX` for `<`, `>`, `&`, which `JSON.parse` decodes back losslessly while no `<` survives to
    terminate the element. `test_the_rendered_view_model_island_is_parseable_JSON` parses the real
    island and round-trips a hostile analysis name.

    INJECTION FIXTURES ARE THE REAL MEASURED SHAPES, not invented ones: `</script><script>`, a literal
    `<id6>` (32 real occurrences at review), `<path>`, `<plan>`, `<repo>`, `<selector>`,
    `<agent/model>`, formula-leading cells (`=1+1+cmd|' /C calc'!A0`, `+SUM(A1)`, `-2+3`, `@import`), a
    bidi override, a NUL, and quote/attribute breakouts. Each is asserted inert in each context, and
    end-to-end through a finding, a refusal and a table cell: no `<img`, no live `<id6>`, exactly the
    three script elements this module emits, and the text still PRESENT escaped so real content is not
    silently dropped. THE CONTRACT IS INERTNESS, NOT ABSENCE, and the test says so.

    A BIDI OVERRIDE IS REPLACED, NOT ESCAPED (DECISION 04-6eq3oq-D2), because a numeric character
    reference decodes to the same active code point and would still reorder text. Every escape routes
    through `sanitize_control_characters` first, which maps `Cc`/`Cf`/`Cs`/`Co` to U+FFFD while
    preserving tab/newline/return. U+FFFD rather than deletion keeps the tampering visible.

    `aw sanitize` OVER THE PRODUCED BUNDLE IS CLEAN, WITH A CONTROL. Using the same
    `leak_sanitizer.build_ruleset` the CLI uses:

    ```
    === SANITIZE OVER THE PRODUCED BUNDLE ===
    findings: 0
    CLEAN

    === CONTROL: the same ruleset over a planted raw absolute path ===
    findings: 2
      control/planted.html:1	home-path	fail
      control/planted.html:1	handle	fail
    CONTROL CONFIRMED: the same invocation flags a raw absolute path
    ```

    THE MEASUREMENTS THAT MOTIVATED THIS ITEM, stated as review-time snapshots since the live corpus is
    absent from this lane: 152 of 216 real outcome files carried markup characters, 6 carried
    FAIL-severity `home-path`/`handle` leaks, and the package contained ZERO uses of `html.escape`
    before this module (only `re.escape`). A permanent test also records the honest boundary that
    ESCAPING IS NOT REDACTION: a real absolute path passing through a finding is made inert but NOT
    removed, and it is the sanitizer's job to detect it, which the test confirms it does.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the stdlib-`html.parser` DOM-contract assertions for ARIA state, keyboard-reachable elements, focus visibility, text alternatives, the reduced-motion rule, real data tables, and the absence of color-only encoding. Paste proof NO test imports bs4, lxml or playwright (a grep is acceptable) and that the declared test extra is unchanged. NAME the a11y properties that are NOT machine-verified (focus order, contrast, post-click state) rather than implying coverage. Paste the size-threshold fallback exercised at and above the measured corpus scale.
  - Observed evidence: `python3 -m pytest tests/test_run_analytics_spa.py -o addopts="" -q -k "Accessibility or NoNewTestDependency or LargeDataset or PackagedAsset"`
    reports `33 passed, 76 deselected`.

    STRUCTURAL DOM CONTRACT, ASSERTED WITH STDLIB `html.parser` ONLY: a declared document language;
    every `<section>` labeled by a real heading id; every toggle exposing `aria-pressed` (or
    `aria-disabled`); a disabled control disabled for BOTH the DOM and assistive technology; every
    chart carrying `role="img"` plus `aria-labelledby` and a `<title>` text alternative; every table
    carrying a `<caption>` and every `<th>` a `col`/`row` `scope`; real `<table>`/`<thead>`/`<tbody>`
    rather than layout divs; a `:focus-visible` outline; a `prefers-reduced-motion` block with
    `animation: none`; series distinguished by `stroke-dasharray` (four patterns) so the encoding
    survives monochrome; a pressed toggle marked with generated content as well as color; a skip link
    ordered before the content; and `<figure>`/`<figcaption>` grouping each chart with its exact table.

    NO NEW TEST DEPENDENCY, ASSERTED RATHER THAN TRUSTED. `test_no_analytics_report_test_imports_bs4_lxml_or_playwright`
    greps both new test modules for `bs4`, `beautifulsoup`, `lxml`, `playwright` and `selenium` imports
    and finds none; `test_the_declared_test_extra_is_UNCHANGED` asserts the extra is still exactly
    `["pytest>=8", "pytest-xdist>=3", "pytest-randomly>=3", "PyYAML>=6"]`; and
    `test_the_spa_module_imports_only_stdlib` allowlists the module's imports. That test EARNED ITS
    KEEP during execution by failing when `pathlib` was added, which is the mechanism working.

    WHAT IS NOT MACHINE-VERIFIED IS NAMED, NOT IMPLIED, and is published IN the report (the `a11y`
    panel) rather than only in a doc: computed keyboard focus ORDER (structural tab-ability is asserted,
    the resulting order is not), color CONTRAST RATIO against WCAG thresholds, post-interaction state
    (no JS is executed by the suite, so a control's state after a click is asserted only as authored
    markup), and screen-reader ANNOUNCEMENT text. `test_the_UNVERIFIED_properties_are_published_in_the_document`
    asserts each string appears in the output, so the boundary cannot be quietly dropped.

    THE LARGE-DATASET FALLBACK IS EXERCISED AT AND ABOVE CORPUS SCALE: bins stay bounded at 59532 rows
    (twice measured scale) and the series is still ONE path node; the client carries a documented
    fallback for a browser without `DecompressionStream`, pointing at the companion file; and the client
    renderer assigns via `textContent` only, never `innerHTML`, so escaping holds client-side too.
    A second real defect was caught here: a literal backslash-n in the emitted script had commented out
    the row renderer, and `test_no_emitted_script_line_carries_a_LITERAL_backslash_n` plus
    `test_every_comment_line_in_the_emitted_script_is_only_a_comment` are the permanent guards.

    BARE SUITE AND DIFF CHECK FROM THIS WORKTREE, as this V item is also required to carry:

    ```
    17 failed, 6740 passed, 3 skipped, 2 xfailed in 230.31s (0:03:50)
    ```

    Compared by FAILING NODE IDS against the baseline I measured MYSELF in this worktree BEFORE any
    edit (`17 failed, 6601 passed, 3 skipped, 2 xfailed`), the delta is EMPTY:

    ```
    === DELTA (baseline vs post) ===
    EMPTY DELTA: identical failing node IDs
    baseline count: 17, post count: 17
    ```

    All 17 are pre-existing and environmental, not code defects: each is the worker-role lifecycle
    refusal `AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role
    process must not run them`, which fires because this turn runs as a worker lane. They sit in
    `test_oc_runipd.py`, `test_agy_runipd_cli.py`, `test_ipd_lifecycle_cli.py`,
    `test_novalnomerge_integration.py` and `test_worker_role_refusal.py`, none of which this plan
    touches. Passing count rose 6601 -> 6740, the 139 tests added here. `git diff --check` reports
    CLEAN. The suite was run BARE, with no `-n0`, no second `-q` and no `-p no:randomly`.
  - Result: pass

Additionally, and NOT as a separate V-item because it validates no single E-item: V-08 must also carry bare `python3 -m pytest` and `git diff --check` from the executing worktree, against the baseline the executor measured itself, comparing failing NODE IDS and never totals.

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: bundle publication and the single-file application share one schema and atomic artifact boundary. NOTE THE SCOPE OF THAT ARGUMENT: it justifies ONE PLAN, not one ITEM. Publication and the application do share a contract, which is why they belong together; that does not make the transactional publish, the asset packaging, the data layout, the refusal view, the controls, the panels, the escaping boundary and the accessibility checks one deliverable, which is why the eight items exist (F-7, and the Set orchestrator's own OQ-01 calling this plan's E-02 the clearest case in the Set).

EXECUTION CONTRACT. This plan requires explicit human approval (`aw ipd set approved 6eq3oq --by-human --message ...`), and its `Item-Dependencies` refuse dispatch until `aflsz3` (Order 06) is `executed`. That dependency is load-bearing rather than bookkeeping, and this review makes it sharper: Order 06 decides WHICH analyses exist and which are refused, and this report renders exactly that. Order 08 (`mm5p3v`) depends on this plan and Order 10 (`9xycbh`) covers it end to end, so the bundle layout and the companion schemas are CONTRACTS, not internal details.

- Commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since a rejected hook can leave paths in the index you never staged. Other agents and humans work concurrently in this checkout.
- NEVER COMMIT ANY PART OF THE LIVE RUN CORPUS OR A PRODUCED BUNDLE. The analytics tree is gitignored by design (`.aw/.gitignore` `records/runs/`), and 6 of 216 real outcome files carry absolute paths that `aw sanitize` flags at `fail`. Run `aw sanitize --agent` before treating any output as shareable.
- THE HONESTY RULE, which outranks every convenience: when you report that tests passed, PASTE THE ACTUAL RUNNER OUTPUT. Never fill an `Observed evidence:` field from memory or from a matching execution checkmark. If a validation cannot be performed, say so plainly and leave it `pending`. This applies with special force to the ACCESSIBILITY claim: assert only what stdlib tooling proved, and name the rest unverified.
- RE-MEASURE EVERY NUMBER IN THIS PLAN. Every figure (29766 fact rows, 3.24 MB / 0.93 MB / 0.71 MB, 152 of 216 outcome files, 6 fail-severity leaks, the 5-of-16 refusal count, `7 passed` on the packaging test) is a review-time snapshot of a tree that grows with every run. Re-derive them; do not cite them as current.
- RE-LOCATE EVERY CITED SYMBOL BY NAME, not by line number.
- Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

Do not omit uncertainty or data-quality context to simplify a visualization. FIVE STOP CONDITIONS. If you find yourself rendering a chart for an analysis Order 06 returned `cannot-determine` for, STOP: the refusal is the finding, and five of the sixteen required analyses are refusals. If the packaging test passes but you have not added a POSITIVE per-asset assertion, STOP: the existing test passes with every asset missing, measured. If you reach for bs4, lxml or playwright, STOP: none is a declared test dependency and stdlib `html.parser` is measured sufficient. If you find yourself composing the `.aw/records/runs` literal or weakening `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS`, STOP: Order 01 owns both. And if a test needs the live corpus to pass, STOP and build a fixture, because the two current suite failures are precisely that mistake made earlier.
