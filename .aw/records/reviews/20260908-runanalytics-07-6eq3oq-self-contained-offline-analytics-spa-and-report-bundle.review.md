# Review: self-contained offline analytics SPA and report bundle (child 6eq3oq, Set runanalytics)

- Subject-Id: 6eq3oq
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `2b9632fb`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic review
(exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the eight-item split and the rewritten
V-item bijection.

METHOD. Four of the five HIGH findings here came from RUNNING something rather than reading: a probe wheel built
with hatchling to test the asset claim, `os.replace` and `os.symlink` executed against real directories to test
the atomicity claim, the actual corpus serialized in two layouts to size the embedded payload, and all 216
outcome files scanned for markup and leaks. The fifth came from reading this plan against its own dependency,
which was reviewed the same day. That last one matters most, and it is the kind of defect only cross-reading
finds.

WHAT THE PLAN GETS RIGHT, and it is not a small list. The single-file offline deliverable is the correct product
decision for a privacy-sensitive local report: no server, no CDN, no network, openable from disk, and therefore
nothing to secure and nothing to leak in transit. Requiring an exact TABLE beside every chart is exactly the
discipline that lets a reader check a visualization instead of trusting it. Requiring an interpretation panel that
names overlap, missingness, sample size and association-versus-causation is unusual and right. And the closing
sentence, that uncertainty must not be dropped to simplify a visualization, is the correct instinct; the problem
is that the checklist above it demanded twenty charts the data cannot support, which is the same instinct
contradicted.

THE ROOT FINDING IS A CONTRACT BREAK WITH ITS OWN DEPENDENCY, AND IT WOULD HAVE PRODUCED FABRICATED CHARTS. E-02
demands "one interactive chart and exact table for each of the 16 required and at least four corpus-supported
analyses from Order 06". Order 06 (`aflsz3`), reviewed the same day and hardened on measured grounds, now REFUSES
five of those sixteen: analysis 5 (failed-merge waste) at n=3 to 6, 8 (merge/conflict recurrence) at n=3, 10 (test
retry loops) at n=6, 12's model arm at 1.1 percent model-identity coverage, and 15 (resource saturation) with zero
of 135 runs carrying a `telemetry/` directory. Five more are reshaped or partially refused, including the flagship
analysis 1, whose read-TIME measure is 0.014 percent of elapsed time and was converted into a token measure. So
only SIX of sixteen are chartable as this plan assumes. An executor following the literal wording would render
five charts from `cannot-determine` verdicts, which is precisely the "impressive charts are not evidence" failure
Order 06's gate exists to forbid, committed by the plan whose job is to display Order 06's output faithfully. E-04
now makes the refusal a first-class view with equal prominence to a chart.

THE PACKAGING CLAIM IS FALSE, AND NOTHING IN THE SUITE WOULD HAVE CAUGHT IT. The conventions assert browser assets
"must be included by wheel/sdist packaging". Measured with a throwaway package: hatchling HONORS `.gitignore`, and
a probe wheel silently omitted a gitignored asset at exit 0 with no warning. Three compounding facts follow.
`[tool.hatch.build.targets.wheel]` declares only `packages = ["agent_workflows"]` plus a single `.aw/system`
force-include. The sdist `include` is an explicit allowlist of seven paths, so anything outside `/agent_workflows`
is absent. And `tests/test_packaging.py` asserts only that FORBIDDEN content is absent plus a handful of named
modules, so it passes with every browser asset missing; verified by running it (`7 passed`). A plan whose product
is a rendered HTML file, shipping a wheel with no HTML in it, would pass its own packaging test. E-02 now requires
a POSITIVE per-asset assertion in both artifacts plus a test for the gitignore-drop behavior.

THE ATOMICITY REQUIREMENT IS UNIMPLEMENTABLE AS WRITTEN. E-01 requires that "a failure leaves the previous latest
bundle intact", which is the right property. But `os.replace` onto a non-empty target directory raises `OSError`
errno 39, measured, so the single-file temp-then-rename pattern this package uses in all 60 of its atomic writes
(canonically `artifact_core.atomic_write:118`) does not generalize to a multi-file bundle. The working scheme is
publish-to-versioned-directory plus an atomic `latest` symlink flip, also measured to work. The catch the plan
could not have known without checking the CI matrix: `windows-latest` is in it, symlink creation there needs
privilege, and this package's only `os.symlink` call is a preserve-existing branch rather than a create-as-policy
path. So the fallback has to be designed and tested, not discovered mid-run, and the manifest-written-last rule is
what makes a partial bundle detectable.

THE DATA VOLUME WAS NEVER SIZED, AND IT DECIDES THE ARCHITECTURE RATHER THAN BEING A DETAIL. Measured over the real
corpus: 29766 per-step fact rows are 3.24 MB as minified JSON, 0.70 MB gzipped, and 0.93 MB as the base64 text a
single HTML file must actually embed; a columnar layout measures 0.71 MB, a 24 percent saving. The sharper number
is the rendering one: 29766 points as individual SVG nodes is roughly 1.34 MB of markup and 29766 DOM nodes, past
where browsers degrade, while the same series as SVG path data is roughly 0.36 MB in one node. Canvas solves the
rendering and destroys the accessibility, which this plan also requires and which cannot be asserted structurally
against a canvas. Per-attempt aggregates alone would be a comfortable 39 KB but forfeit every distribution and
quantile the Set exists to provide. The decision therefore belongs in the plan with its measurement, which is what
E-03 now does.

THE INJECTION HAZARD IS ALREADY IN THE DATA, AND THERE IS NO ESCAPING HELPER TO REUSE. 152 of 216 real outcome
files contain `<`, `>` or `&` in free text, and HTML-tag-looking substrings are routine: `<id6>` 32 times, plus
`<id>`, `<run-id>`, `<path>`, `<plan>`, `<summary>`, `<repo>`, `<selector>`, `<agent/model>`. Separately, 6 of those
files carry FAIL-severity `home-path` and `handle` findings in `partial_work_location` or `summary`, containing real
absolute worktree paths. And a repo-wide search finds ZERO uses of `html.escape`; only `re.escape` appears. So the
escaping boundary is greenfield, and it is not one boundary but four: HTML text, attribute value, SVG text and JS
string literal each need a different escape, and a single shared helper applied everywhere is itself the defect.
Order 02's allowlist projector should keep free text out of the CACHE, but a report may legitimately display a
finding string Order 06 generated, so the render boundary must escape regardless of upstream promises.

ONE FINDING THAT WOULD HAVE SPLIT THE MAINTAINER'S BOX FROM CI. E-03 asked for "automated browser-free checks" and
never named the tooling. Measured: `bs4` 4.15.0, `lxml` and `playwright` all import in this venv, and NONE is in
`[project.optional-dependencies].test`, which is exactly pytest, pytest-xdist, pytest-randomly and PyYAML; CI
installs precisely that extra. No test in the suite imports any of the three today. So a DOM test written the
obvious way passes locally and fails in CI, which is the identical reproducibility hole `pyproject.toml`'s own
comment documents for `pytest-randomly` ("an undeclared dep that alters results is a reproducibility hole, not a
convenience"). A probe settled it cheaply: stdlib `html.parser` extracts `aria-pressed`, `role`, `aria-labelledby`,
`scope` and `<caption>`, covering every structural assertion this plan needs. What it cannot do is computed focus
order, contrast ratio and post-click state, and the honest move is to name those unverified rather than let
"accessible" stand as an unearned claim.

ON SIZING, WHICH THE SET ALREADY KNEW. Three E-items, and the orchestrator `5lxvl3` carries an OPEN blocking
question naming THIS plan's E-02 as the clearest case in the entire Set: "one item for the ENTIRE SPA (linked
filters, metric/phase toggles, charts, tables, findings, pricing, quality, and raw-data exploration)". E-03 was
comparable, bundling accessibility, offline behavior, injection safety, large-dataset behavior and deterministic
rendering across five unrelated test surfaces. This is the seventh sibling split for the same reason (`bzz5e6`
3->6, `lhccjf` 3->8, `5f2h8i` 3->7, `8hald1` 3->8, `aflsz3` 3->9) and the seventh consecutive gate with no
execution contract. Both patterns live in the authoring pipeline, not in any one plan.

WHY APPROVE WITH REVISIONS RATHER THAN OPEN QUESTIONS. Nothing needed a human. The refusal-rendering question was
settled by reading the dependency's own reviewed text, the atomicity and packaging questions by executing the
operations, the tooling question by importing the libraries and reading the declared extra, and the data-layout
question by serializing the real corpus. All four are recorded as decisions with rejected alternatives. No BLOCKER
and no unfixed HIGH remains. The Set's sizing question (`5lxvl3` OQ-01) stays OPEN and blocking on the
ORCHESTRATOR, which is correct: this review applied the remedy that question recommends for this child, and the
maintainer's answer still governs Orders 09 and 10.

ONE NOTE FOR THE MAINTAINER, since it spans plans rather than belonging to this one. Two of this Set's remaining
unreviewed children (09 and 10) are the ones `5lxvl3` OQ-01 also names as over-dense, and Order 10 owns the
documentation that must carry both honest limits this review added (which analyses are refused, and what
accessibility was not verified). If Order 10 is reviewed without that context it will document twenty working
views and a verified-accessible report, neither of which is true.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-083 | HIGH | IN-SCOPE | D. domain invariants; A. correctness (cross-plan contract) | cross-read this plan against `aflsz3` as reviewed the same day; counted its per-analysis feasibility verdicts | **THE PLAN DEMANDS CHARTS FOR FIVE ANALYSES ITS OWN DEPENDENCY REFUSES TO COMPUTE.** Order 06 returns `cannot-determine` for analyses 5 (n=3..6), 8 (n=3), 10 (n=6), 12's model arm (1.1 percent identity coverage) and 15 (zero telemetry runs), and reshapes or partially refuses 1, 3, 4, 11, 13. Only 6 of 16 are chartable as authored. An executor following the literal wording fabricates five charts from refusals, committing exactly the failure Order 06's gate forbids, in the plan whose job is to display Order 06 faithfully | C:Low; U:Medium; S:Low; F:High; Overall:Medium | FIXED | New E-04 renders a refusal as a FIRST-CLASS view with equal prominence, naming reason and observed n; V-04 requires all five refusal panels pasted plus a test that `cannot-determine` produces NO chart element, shown failing against an empty-chart version; the Goal and Findings list state the 6/5/5 split; OQ-01/D-1 rejects empty charts, omission, and rendering from n=3 |
| PR-084 | HIGH | IN-SCOPE | C. operability; E. testing (a test that cannot fail) | probe wheel built with and without a `.gitignore` entry; `pyproject.toml:120-144` read; `tests/test_packaging.py` read and run (`7 passed`) | **THE ASSET-PACKAGING CLAIM IS FALSE AND NOTHING WOULD CATCH IT.** Hatchling HONORS `.gitignore`: a probe wheel silently omitted a gitignored asset at exit 0 with no warning. The wheel target declares only `packages` plus one `.aw/system` force-include; the sdist `include` is an explicit seven-path allowlist; and the packaging test asserts only ABSENCE of forbidden content, so it passes with every browser asset missing. A plan whose product is an HTML file could ship a wheel containing no HTML and pass | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-02 requires POSITIVE per-asset assertions in BOTH wheel and sdist plus a test for the gitignore-drop behavior, extending the existing packaging test rather than forking one; `pyproject.toml` and `.gitignore` added to `Scope-Paths` narrowly with the reason stated; V-02 requires the asset listings pasted; a stop condition forbids relying on the existing test |
| PR-085 | HIGH | IN-SCOPE | A. correctness and data integrity (atomicity) | executed `os.replace` onto a non-empty directory (`OSError` errno 39) and an `os.symlink`+`os.replace` flip (succeeded) in a scratch tree; CI matrix and `layout_migration.py:486` read | **`os.replace` CANNOT SWAP A MULTI-FILE BUNDLE, SO THE STATED ATOMICITY PROPERTY IS UNIMPLEMENTABLE AS WRITTEN.** All 60 atomic writes in this package are single-file temp-then-rename (`artifact_core.atomic_write:118`) and do not generalize. The working scheme is versioned-dir plus an atomic `latest` symlink flip, but CI runs `windows-latest` where symlink creation needs privilege and the package's only `os.symlink` use is a preserve-existing branch | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-01 requires the versioned-dir plus symlink-flip scheme WITH an implemented and tested Windows fallback writing the manifest LAST as the completeness signal; V-01 requires the errno-39 measurement re-run, fault injection between writes, and the fallback exercised by making `os.symlink` raise; OQ-02/D-2 rejects in-place writes and a lock (citing `platform_lock`'s one-blocking-caller rule) |
| PR-086 | HIGH | UNDER-SCOPE | C. architecture; F. UX at scale | serialized real fact rows row-wise and columnar, measuring raw/gzip/base64; computed SVG markup size and DOM node counts | **THE EMBEDDED DATA VOLUME WAS NEVER SIZED AND IT DETERMINES THE ARCHITECTURE.** 29766 per-step rows are 3.24 MB minified / 0.93 MB base64-gzip row-wise versus 0.71 MB columnar (24 percent saving). Worse, 29766 individual SVG nodes is ~1.34 MB of markup past browser degradation, while path data is ~0.36 MB in one node; canvas fixes rendering but is inaccessible and structurally untestable, colliding with the plan's own a11y requirement; per-attempt aggregates (39 KB) forfeit every quantile the Set exists to provide | C:Medium; U:Medium; S:Low; F:High; Overall:Medium | FIXED | New E-03 fixes ONE documented data contract (columnar, per-step, pre-binned or path-rendered series, paginated raw view) with the measurements as its basis; a size budget test and a bounded-DOM-node test at corpus scale; V-03 requires both layouts re-measured and the node count proven not to scale with rows; OQ-04/D-4 records the rejected alternatives |
| PR-087 | HIGH | UNDER-SCOPE | B. security (injection); E. testing | scanned all 216 outcome files for markup shapes; ran `leak_sanitizer.scan_text` over their free-text fields; grepped the package for `html.escape` | **THE INJECTION HAZARD IS ALREADY IN THE REAL DATA AND THERE IS NO ESCAPING HELPER TO REUSE.** 152 of 216 outcome files contain `<`, `>` or `&` in free text, with `<id6>` appearing 32 times plus `<path>`, `<plan>`, `<repo>`, `<selector>`; 6 carry FAIL-severity `home-path`/`handle` findings in `partial_work_location` or `summary` holding real absolute paths. ZERO uses of `html.escape` exist in the package. HTML text, attribute, SVG text and JS string are four contexts needing four escapes, so one shared helper is itself the defect | C:Low; U:Low; S:High; F:Medium; Overall:Medium | FIXED | New E-07 establishes a documented per-CONTEXT escaping boundary; the required tests name the real measured shapes (`</script>`, literal `<id6>`, formula-leading cell, Unicode controls, bidi override) asserted per context; `aw sanitize --agent` over the bundle WITH a control run; a convention records that Order 02's projector protects the CACHE while this protects the RENDER, so upstream promises are not relied on |
| PR-088 | MEDIUM | UNDER-SCOPE | E. testing (reproducibility) | imported bs4 (4.15.0), lxml and playwright successfully; read `pyproject.toml:85` and `.github/workflows/tests.yml:70`; probed stdlib `html.parser` | **THE PLAN NEVER NAMED ITS TEST TOOLING AND THE OBVIOUS CHOICES ARE UNDECLARED.** All three libraries import in the maintainer venv; none is in the `test` extra, which is what CI installs; no suite test imports any of them. A DOM test written the obvious way passes locally and fails in CI, the exact reproducibility hole `pyproject.toml` documents for `pytest-randomly`. Stdlib `html.parser` was measured sufficient for `aria-*`, `role`, `scope` and `<caption>` | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-08 requires stdlib `html.parser` ONLY with no new test dependency, and requires the properties stdlib CANNOT verify (focus order, contrast, post-click state) be NAMED unverified rather than implied; V-08 requires a grep proving no test imports the three and that the extra is unchanged; a stop condition forbids reaching for them; OQ-03/D-3 rejects declaring bs4/lxml, adding playwright (network + browser binaries in an offline-first product's suite), and using them undeclared |
| PR-089 | MEDIUM | UNDER-SCOPE | G. right-sizing and conceptual density | orchestrator `5lxvl3` OQ-01 read (names this plan's E-02 explicitly); item content counted; lint conforming both before and after | **MECHANICALLY SIZED, AND THE SET'S OWN BLOCKING QUESTION CALLS THIS PLAN'S E-02 THE CLEAREST CASE IN THE SET:** "one item for the ENTIRE SPA (linked filters, metric/phase toggles, charts, tables, findings, pricing, quality, and raw-data exploration)". E-03 similarly bundled accessibility, offline behavior, injection safety, large-dataset behavior and deterministic rendering across five unrelated test surfaces. Seventh sibling with this finding | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split into EIGHT items across four groups (publication / data contract / views / hardening); `Highest E allocated` 03 -> 08; V-01..V-08 rewritten to bijection; a right-sizing note quotes the orchestrator's own text; cohesion rationale restated to say it justifies one PLAN, not one ITEM |
| PR-090 | MEDIUM | UNDER-SCOPE | G. executability | plan gate as authored (two sentences); six sibling review records | **THE GATE CARRIED NO EXECUTION CONTRACT**: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle move, no re-measure warning, no stop conditions. Seventh consecutive sibling with the same omission | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Full contract added: approval requirement, the load-bearing `aflsz3` dependency restated as deciding WHICH analyses exist, the two consuming Orders; a fence naming eight measured prohibitions with the narrow `pyproject.toml`/`.gitignore` exception justified; path-scoped commit with re-verify-after-failed-hook; the honesty rule extended explicitly to the accessibility claim; re-measure-every-number; and FIVE stop conditions |
| PR-091 | MEDIUM | IN-SCOPE | C. architecture (duplicate paths) | Order 01 (`xbwq8n`) plan read; `worktree_lease.py:876` confirmed | The plan writes the output path as prose without naming Order 01's resolver, risking a SEVENTH construction of the `.aw/records/runs` literal Order 01 exists to remove from six sites, and mis-siting the report for any non-`repository` `records_backend`. It also never recorded that `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` already makes the analytics tree worker-forbidden, which a lane-based executor might try to weaken | C:Low; U:Low; S:Medium; F:Medium; Overall:Low | FIXED | The Goal requires resolution THROUGH Order 01's resolver and names the four reserved subpaths and the containment predicate; a convention records the worker-forbidden predicate as preserve-only; the fence and a stop condition forbid both composing the literal and weakening the predicate |
| PR-092 | LOW | IN-SCOPE | Presentation; Evidence accuracy | `grep -o` count before the fix (20); bare suite run at review | Twenty escaped backtick pairs rendered as literal backslashes, after Order 01's six, 02's four, 03's ten, 04's eighteen, 05's sixteen and 06's four, so it is a pipeline artifact rather than a slip. Also no baseline was recorded despite requiring a bare suite run, so an executor meeting two pre-existing failures could not distinguish them from its own | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All 20 backticks unescaped and verified zero remaining, with zero smart quotes or dashes; baseline recorded (`2 failed, 5655 passed, 3 skipped, 2 xfailed in 95.72s`) with both node ids named and attributed pre-existing, plus compare-node-ids-not-totals and a corpus-SCALE synthetic fixture requirement so the size tests are exercised rather than asserted |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | What does the report render for an analysis Order 06 refuses to compute? | A FIRST-CLASS refusal panel with equal prominence to a chart, naming the analysis, the reason, and the observed n or coverage | An empty chart, rejected because an empty axis reads as "we measured zero" rather than "we could not measure", which is a stronger and falser claim than silence. Omitting the analysis, rejected because its absence is indistinguishable from an oversight and a reader cannot tell the report is complete. Rendering from the few points that exist, rejected outright because n=3 drawn as a trend is the fabrication Order 06's gate forbids | Order 06 as reviewed refuses analyses 5, 8, 10, 12's model arm and 15, and reshapes 1, 3, 4, 11, 13, leaving 6 of 16 chartable | yes |
| D-2 | How is a multi-file bundle published atomically, given `os.replace` cannot swap a directory? | Publish to a versioned directory, then flip a `latest` symlink atomically; on a platform where symlink creation raises, write the flat files in a documented order with the MANIFEST LAST as the completeness signal | Writing files in place, rejected because a reader opening `index.html` mid-write sees a truncated document with no way to detect it. A lock, rejected because `platform_lock` records that exactly one caller may block and a blocking publisher would hang a driver, and a reader holds no lock anyway. Requiring symlinks unconditionally, rejected because CI runs `windows-latest` where creation needs privilege, so the suite would fail on a supported platform | `os.replace` onto a non-empty dir raises `OSError` errno 39 (executed); `os.symlink`+`os.replace` flip succeeds (executed); CI matrix at `.github/workflows/tests.yml:24`; the package's 60 single-file atomic writes | yes |
| D-3 | What test tooling verifies the DOM, and is it available in CI? | Stdlib `html.parser` ONLY, with the properties it cannot check named as unverified | Declaring bs4 or lxml in the test extra, rejected because the dependency surface is deliberately minimal and stdlib is measured sufficient for every structural assertion needed. Adding playwright, rejected more strongly because it downloads browser binaries and needs network, so an offline-first report's own suite would require the network. Using any of them UNDECLARED, rejected because that is the reproducibility hole `pyproject.toml`'s `pytest-randomly` comment documents, where maintainer and CI run different suites | bs4 4.15.0, lxml and playwright all import locally; none is in `pyproject.toml:85`; CI installs `-e ".[test]"`; `html.parser` probe extracted `aria-pressed`, `role`, `aria-labelledby`, `scope`, `<caption>` | yes |
| D-4 | What embedded data layout and grain does the single HTML file carry? | Columnar per-step facts, with plotted series pre-binned or path-rendered and the raw view paginated | Row-wise objects, rejected on measurement: 0.93 MB versus 0.71 MB base64-gzip, and slower to parse. Per-attempt aggregates only (39 KB), rejected because it forecloses every distribution, median and quantile the Set exists to provide, and Order 05 stores per-step facts precisely so they need not be reparsed. Canvas rendering, rejected because it is inaccessible and structurally untestable, defeating E-08 and leaving the a11y claim unverifiable. An external data file, rejected because the deliverable is explicitly one self-contained file | 29766 real rows measured in both layouts (3.24/0.70/0.93 MB versus 2.11/0.53/0.71 MB); 29766 SVG nodes ~1.34 MB of markup versus ~0.36 MB as path data | yes |
| D-5 | Does this plan get to edit `pyproject.toml` and `.gitignore`, which its authored `Scope-Paths` omitted? | YES, narrowly and with justification, so both are added to `Scope-Paths` | Leaving them out, rejected because the measured packaging defect may genuinely require a wheel or sdist include, and an undeclared edit would trip the finalize scope gate mid-run, which is the situation the declare-then-reconcile mechanism exists to avoid. Declaring them broadly, rejected because `.gitignore` carries an explicit do-not-narrow warning on the `*.untracked.*` block and a wide licence invites exactly that damage | probe wheel showing hatchling honors `.gitignore` and the sdist include-list omitting non-`/agent_workflows` paths; `aw ipd finalize`'s `--scope-reason`/`--scope-ack` mechanics; the `.gitignore` do-not-narrow block | yes |
