# IPD: Refuse a new marker-located unbounded section slice in tests at author time

- Date: 2026-10-01
- Kind: child
- Concern: SET `secbound` FIXES THE MEASURED SITES AND STOPS NO NEW ONE, AND THE CLASS HAS ALREADY COME BACK ONCE BY EXACTLY THIS ROUTE. Backlog `1pgrii`'s own history records the originating guard being "Bounded in place while executing `skn8uk` with a control test; this item records the class of defect for the other guards written the same way", which is the class returning after a point fix. Order 01 (`78rxzc`) shipped `support.section`/`final_section`/`section_lines` and Order 02 (`tr8ugt`) converts the measured sites, but NOTHING refuses the next one. The defect is a test that locates a section by a marker and then reads to end of input, so it asserts over text it was never written to judge, and it is invisible at authoring because it is GREEN when written: `tests/test_research_index.py::test_n_honored` passes today only because `## Most recent` happens to be the last section `research_index.build_index_md` emits, and `tests/test_project_layout.py::test_e06` satisfies 3 of its 5 required topics from text after D130 the moment `### D131.` is renamed. NOTHING MECHANICAL NOTICES THIS TODAY: `aw check`'s rule families all scan `.aw/records` (no rule in `check_engine` constructs a `tests` path), the three local pre-commit hooks cover leaks and plan lifecycle only, and `pyproject.toml` declares no `[tool.ruff]` section, so there is no configured lint surface to extend. Measured at authoring HEAD `46cd2f8a5` with the detector this plan specifies: 8 marker-located unbounded tail slices survive in `tests/` plus 5 heading-separator `split(MARKER)[1]` tails, and the gap is not hypothetical because 3 of those sites sit in files Order 02 never converts.
- Scope: Add ONE guard test that walks the suite's test modules with `ast` and refuses a NEW marker-located unbounded section slice, carrying a typed per-site exemption comment for the sites where the unboundedness IS the assertion, and point `CONTRIBUTING.md` at the rule so an author meets it while authoring. The guard detects TWO spellings of the same defect, each measured live: a SLICE whose lower bound comes from a marker search (`x[x.index(M):]`, or `start = x.find(M)` then `x[start:]`), and a `split(HEADING, ...)[1]` whose separator is a markdown heading. It EXCLUDES its own detection of field-delimiter splits (`":"`, `"."`, `"="`, `"---"`), which the backlog item explicitly lists as sites that must not be flagged. It EXCLUDES complementary text reconstruction (`t[:i] + block + t[i:]`), which is a rewrite and not a section read. EXCLUDES converting any site: every conversion is Order 02 (`tr8ugt`), which MUST land first or this guard is red on arrival. EXCLUDES every production module; this plan touches one new test file and one documentation bullet.
- Scope-Paths: tests/test_no_unbounded_section_reads.py, CONTRIBUTING.md
- Item-Dependencies: executed:tr8ugt, executed:76ic0k
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: ap839o
- Set: secbound
- Order: 3
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: jj5ju1

## Workflow history

- 2026-10-01 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `ap839o`, the deferred residue of Set `secbound`. The item's stated blocker was a DESIGN problem ("`x[start:]` is indistinguishable from a legitimate tail slice without knowing `start` came from a marker search"), and this plan resolves it from repository evidence rather than deferring it again: the binding IS tractable within a single function body, which is where every live instance sits, and the authoring census drove the detector over all 218 discovery-set files to prove it. Three findings changed the plan's shape against the backlog item's own expectations and are recorded in Findings so a reviewer can contest them: the item described ONE arm (the unbounded slice) but the `split(HEADING)[1]` tail is the same defect and is live in 5 places (F-03); the item's "sites that must NOT be flagged" list is incomplete, because Order 01's OWN control test deliberately uses the raw slice as a contrast and would be red on arrival (F-04); and a text-reconstruction shape exists that no prose anticipated (F-05). OQ-01 and OQ-02 are resolved from measurement; OQ-03 is a genuine design choice left open and non-blocking.
- 2026-10-01 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Make the next author who writes a test that reads a section to end of input get a refusal that names
the bounded helper and says what to call instead, at the moment they run the suite, rather than when
an unrelated change later widens the read and the assertion starts lying.

The guard must be honest about what it cannot see. It is not a proof that no unbounded read exists;
it closes the two entry routes that every measured instance in this repository actually used.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the detector

- [ ] E-01 WRITE `tests/test_no_unbounded_section_reads.py` WITH THE SLICE-ARM DETECTOR, WHICH RESOLVES THE BACKLOG ITEM'S STATED DESIGN PROBLEM RATHER THAN RESTATING IT. The item says `x[start:]` is indistinguishable from a legitimate tail slice "without knowing `start` came from a marker search", and that detection "needs the binding tracked from the search to the subscript, which the authoring census did within a single function but not across functions". RESOLVED AT AUTHORING: the single-function scope is SUFFICIENT, measured, because all 8 live slice-arm instances bind and consume within one function body. The cross-function case has ZERO instances, so building for it is the hypothetical-need generality `GUIDING_PRINCIPLES.md` P6 directs against. Implement TWO arms over each `ast.FunctionDef`/`ast.AsyncFunctionDef`. ARM A (INLINE) flags an `ast.Subscript` with an `ast.Slice` whose `upper is None` and whose `lower` subtree CONTAINS a call to `.find`/`.rfind`/`.index`/`.rindex`, which catches `out[out.index("## Sets"):]` (4 live instances). ARM B (BOUND) flags the same slice shape whose `lower` names a variable ASSIGNED in that function from a marker-search call, which catches `start = prompt.find(M)` then `prompt[start:]` (4 live instances). Both arms require `upper is None`, because a slice with any upper bound is bounded and must not be flagged. Model the whole file on `tests/test_carrier_scan_single_item_contract.py`, this repository's established shape for an AST guard shipped as a test: a `NamedTuple` violation record with a `render()` method, a module docstring stating SCOPE and KNOWN HOLE, and positive and negative fixtures over source STRINGS so the detector is proven to fire and proven not to over-fire. IMPLEMENT THE DETECTOR AS A PURE FUNCTION over `(relative_path, source_text)` returning violations, with the tree walk calling it, because E-03's exemption audit must re-scan a file with exemptions IGNORED and a detector that consults exemptions internally cannot answer that question (`tests/test_carrier_scan_single_item_contract.py` already ships this seam as `scan_source_for_contract_violations` beside its package walk; reuse the shape rather than inventing a second one). DISCOVERY SET, narrowed for the reason `76ic0k` establishes: walk `tests/test_*.py` plus the named shared helpers `tests/support.py` and `tests/conformance_matrix.py`, and EXCLUDE `tests/fixtures/` and `tests/benchmark_fixtures/`, which are synthetic sample code standing in for a user's repository rather than this suite's assertions. Measured at authoring: that set is 218 files and 5,444 function bodies. The failure message must be actionable, not merely a refusal: name the file, the line, the unparsed slice expression, which arm fired, and the remedy (`support.section` for a bounded read, `support.final_section` to declare a terminal one, or the exemption comment E-03 defines when the unboundedness is the assertion).
  - Depends on: none
  - Expected outcome: `tests/test_no_unbounded_section_reads.py` exists carrying the two-arm slice detector behind a pure `(path, source)` entry point; run against the post-Order-02 tree it reports zero unexempted violations; its positive fixtures prove both arms fire; its negative fixtures prove a bounded slice (`x[a:b]`), a bare tail slice with no marker search (`lines[1:]`), and a search-derived UPPER bound (`x[:x.index(M)]`) are all silent.
  - Execution state: pending

- [ ] E-02 ADD THE `split(HEADING, ...)[1]` ARM, WHICH IS THE SAME DEFECT THE BACKLOG ITEM DID NOT NAME AS A TAIL. The item's `## Suggested work` describes only the slice shape, and its "sites that must NOT be flagged" section discusses `split` only to EXCLUDE the 9 field-delimiter cases. But `text.split("## Workflow history", 1)[1]` reads to end of input exactly as `text[start:]` does, and the item's own Concern paragraph cites two of its live instances as the class's provable defects (`tests/test_backlog.py` counting 4 history bullets where it asserts 2, `tests/test_research_index.py` counting 3 where it asserts 2). So detect it: an `ast.Subscript` with a CONSTANT INTEGER index of 1 or greater over a `.split(...)`/`.rsplit(...)` call whose FIRST argument is a string literal that is a MARKDOWN HEADING, defined as the literal with leading newlines stripped beginning with `#`. THE HEADING TEST IS WHAT KEEPS THE ITEM'S EXCLUSION PROMISE, and it is measured rather than assumed: a census of all 53 `split`-subscript sites in the discovery set found 12 heading separators and 41 non-heading ones, and every non-heading separator is a field delimiter whose failure mode is an immediate `IndexError` rather than a widened assertion (`":"` 8, `": "` 6, `"="` 3, `"---"` 2, `"."` 1, plus whitespace and non-literal forms). The full separator census is in Findings so a reviewer can check there is no borderline case; there is none, because no field delimiter in the suite begins with `#`. DO NOT FLAG INDEX `[0]`, which is the HEAD shape: its failure mode is a whole-text fallback rather than an unbounded tail, Order 02's E-06 converts those 7 sites by a different remedy, and flagging them here would duplicate that plan's concern in a guard whose message names the wrong fix.
  - Depends on: E-01
  - Expected outcome: the split arm is live behind the same pure detector entry point; run against the post-Order-02 tree it reports zero unexempted violations; positive fixtures prove a heading-separator `[1]` and `[2]` fire; negative fixtures prove `split(":")[1]`, `split(". ")[1]`, a non-literal separator, and a heading separator at `[0]` are all silent.
  - Execution state: pending

### Task group 2: the sites where unboundedness is the point

- [ ] E-03 DEFINE A TYPED, PER-SITE, SELF-CLEANING EXEMPTION COMMENT, BECAUSE THREE LEGITIMATE SITES WOULD OTHERWISE MAKE THIS GUARD RED ON ARRIVAL. Use a LINE comment read with `tokenize`, spelled `# aw-unbounded-ok: <reason>`, matching the repository's established `# aw<topic>` pragma family (`# awcmdsurf`, `# awpypi:`, `# awstateignore` and a dozen more are live) rather than inventing a new shape, and requiring a NON-EMPTY reason so an exemption is a visible claim a reviewer can contest rather than a free suppression. A PER-SITE comment is deliberate and not a file allowlist: a file-level allowlist would exempt every future site in that file too, which is exactly how the class returns. THE EXEMPTION MUST BE SELF-CLEANING: assert that every exemption comment in the discovery set sits on a line the detector WOULD otherwise flag, calling the pure detector with exemptions ignored, so a comment left behind after its site is converted fails LOUDLY instead of sitting as permanent dead permission. The three sites needing one, each verified at authoring: (a) `tests/test_defect_report.py::test_prompt_integration_and_format`'s `prompt[start:]`, which compares the tail EQUAL to `reporting_contract.contract_text()` with the failure message "text was added AFTER the reporting contract", so the unboundedness IS the assertion, and which the backlog item names and Order 02's E-07 leaves a comment at; (b) and (c) the TWO slices in `tests/test_support_section.py::test_final_section_against_real_plans_render_status_index` (`out[out.index("## Sets"):]` and `appended[appended.index("## Sets"):]`), which are Order 01's OWN control test proving a raw slice ABSORBS an appended section where `final_section` refuses. THE BACKLOG ITEM'S "SITES THAT MUST NOT BE FLAGGED" LIST DOES NOT MENTION (b) OR (c), because Order 01 was authored after that list was written; report that gap rather than silently widening the list.
  - Depends on: E-01, E-02
  - Expected outcome: the exemption is parsed with `tokenize`, requires a non-empty reason, and is proven to work end-to-end (add it to one site, paste the flagged count dropping by exactly one, with the reason captured); the self-cleaning check is shown to FAIL when an exemption comment is placed on a line the detector would not flag, then reverted; all three legitimate sites carry one with its reason, and the suite is green.
  - Execution state: pending

- [ ] E-04 SUPPRESS COMPLEMENTARY TEXT RECONSTRUCTION STRUCTURALLY, NOT BY EXEMPTION, BECAUSE IT IS NOT A SECTION READ AT ALL. Measured at authoring and anticipated by no prose in the backlog item: `tests/test_ipd_authoring.py::_add_unassigned` does `idx = t.index(marker) + len(marker)` then `self.path.write_text(t[:idx] + block + t[idx:])`. ARM B flags that tail slice, and it is a FALSE POSITIVE of a different kind from the E-03 three: it makes no assertion over the tail at all, it splices text to build a fixture, and `t[idx:]` is not a section whose extent could be wrong because the head and tail are rejoined losslessly. Suppress it by STRUCTURE: a tail slice is not a violation when it appears as an operand of a string concatenation whose operands also include the COMPLEMENTARY HEAD slice over the same subject expression with the same index expression (compare by `ast.unparse` of the subject and of the index, so `t[:idx] + block + t[idx:]` is recognized while `t[:i] + other[j:]` is not). Prefer this over an E-03 exemption for a stated reason: an exemption asserts that a site holds a SANCTIONED unbounded read whose need may later expire, whereas a rejoined split is not an unbounded read in the first place, and E-03's self-cleaning rule would then demand forever that the site still be flaggable. Flatten nested `ast.Add` chains so the three-operand form is seen; a two-operand `t[:idx] + t[idx:]` must also be recognized.
  - Depends on: E-01
  - Expected outcome: the reconstruction suppression is structural; `tests/test_ipd_authoring.py:279` is shown suppressed by it and NOT by an exemption comment (verified by confirming that file carries no `# aw-unbounded-ok:` comment); a positive fixture proves a tail slice NOT in a complementary concatenation still fires; a negative fixture proves `t[:i] + block + t[i:]` is silent and that a mismatched rejoin (`t[:i] + u[j:]`) is still flagged.
  - Execution state: pending

### Task group 3: reach the author before they write it

- [ ] E-05 ADD ONE POINTER BULLET TO `CONTRIBUTING.md` UNDER `## Authoring conventions`, AND RESTATE NOTHING. That section's established pattern is delegation: it already reads "Keep each policy or rule in exactly one canonical place and link to it, rather than duplicating it (P8)", and its neighbouring bullets cite `GUIDING_PRINCIPLES.md` P2 and P14 and the `AGENTS.md` managed block by reference rather than quoting them. So the bullet states the rule (a test that locates a section by a marker must establish where the section ends), names `tests/support.py`'s `section`/`final_section`/`section_lines` as the canonical mechanism, and names the guard test so an author who trips it knows where the rule lives. Do NOT restate the helpers' signatures or refusal semantics, which belong in their docstrings, and do NOT touch `## Self-tests (run before pushing tool changes)`, which governs how to RUN the suite rather than how to author a test. NOTE the user-facing-prose dash rule applies to `CONTRIBUTING.md`: write no em or en dashes in the bullet.
  - Depends on: E-01, E-02
  - Expected outcome: one new bullet quoted from `CONTRIBUTING.md`'s `## Authoring conventions`, naming the three helpers and the guard test at the path E-01 actually created (verified by `ls`, so the file does not cite a test that does not exist, per P2); a `git diff` confirming no other section changed; no em or en dash in the added text.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/test_carrier_scan_single_item_contract.py` is the repository's established shape for an AST guard shipped as a test, and this plan copies it deliberately: a `NamedTuple` violation record with `render()`, a module docstring with explicit SCOPE and KNOWN HOLE sections, fixtures over source strings, and a pure `(source, filename)` detector beside the tree walk. `GUIDING_PRINCIPLES.md` P16 permits a test to read files "where the text or file itself is the artifact under test", which is this guard's footing, the same as `tests/test_artifact_adopt.py`'s scan of `Path(__file__)`.
- `tests/support.py` exposes `section`, `final_section`, `section_lines` and `SectionBoundError` (an `AssertionError` subclass, so a refusal reports as a FAILURE rather than an ERROR). `section` is line-anchored by default with an `anchored=False` escape; the docstring records that tracked `.md` files where an unanchored `.find` diverges from a line-anchored match numbered 122 of 3,077 at that plan's execution.
- `tests/support.py` is imported both as `from tests import support` and as `from tests.support import <name>`; both spellings are live, so follow whichever a file already uses.
- The repository has an established `# aw<topic>` line-pragma family for machine-read annotations (`# awcmdsurf` 8 sites, `# awpypi:` 7, `# awoptimize` 4, `# awdoctorfix` 4, and a dozen singletons), so E-03's `# aw-unbounded-ok:` follows a convention rather than introducing one. `# noqa:` (84 sites) and `# pragma:` (76) are the third-party spellings and are not reused here.
- `aw check`'s rule families scan `.aw/records`; no rule constructs a path under `tests/`. The three local pre-commit hooks (`local-leaks`, `ipd-executed-transition-gate`, `ipd-status-untooled-gate`) each record in their own comment that they are local-only and skippable, with `aw check` as the deterministic backstop. `pyproject.toml` declares no `[tool.ruff]` section. So the suite is the only surface that reaches every author, which is the same conclusion `76ic0k` reached and recorded for the same reason.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

### F-01: the detection surface, measured at authoring HEAD `46cd2f8a5`

Driving the detector this plan specifies over the 218-file discovery set (5,444 function bodies):

```
SLICE ARM: FLAGGED=8  RECONSTRUCTION_SUPPRESSED=1
  tests/test_defect_report.py:113              [B-bound]  'prompt[start:]'
  tests/test_oc_runipd.py:7096                 [B-bound]  'lines[start + 1:]'
  tests/test_oc_runipd.py:7234                 [A-inline] 'out_mixed[out_mixed.index(pol.SUMMARY_HEADER):]'
  tests/test_plan_review_feasibility_rule.py:93 [B-bound] 'content[start_idx:]'
  tests/test_plans_board.py:183                [A-inline] "out[out.index('## Sets'):]"
  tests/test_project_layout.py:478             [B-bound]  'content[d130_start:]'
  tests/test_support_section.py:164            [A-inline] "out[out.index('## Sets'):]"
  tests/test_support_section.py:165            [A-inline] "appended[appended.index('## Sets'):]"
  (suppressed) tests/test_ipd_authoring.py:279 [B-bound]  't[idx:]'
```

The two arms are both load-bearing: 4 instances are inline and 4 are bound, so dropping either arm
halves the detector. Both arms resolve WITHIN a single function body, which is what makes the
backlog item's stated design problem tractable; see F-02.

### F-02: the backlog item's stated blocker is resolved by measurement, not by deferral

The item deferred this work partly because "the detector needs a design neither plan did
(`x[start:]` is indistinguishable from a legitimate tail slice without knowing `start` came from a
marker search, and an authoring AST census found the shape reachable but not trivially so)". That is
the right problem. The resolution is that the binding is tractable at the scope where every instance
actually lives: all 8 slice-arm instances in F-01 bind the index and consume it inside ONE function
body, so a per-function symbol table suffices and no interprocedural dataflow is needed. The
cross-function case has zero instances today, so the guard does not build for it and E-01 records
that as a stated bound rather than implying completeness. This is the same trade-off
`tests/test_carrier_scan_single_item_contract.py` records as its own KNOWN HOLE (a loop variable
rebound to a temporary evades it) for the same reason, from the file this plan takes as its model.

### F-03: the `split(HEADING)[1]` tail is the same defect and the item does not name it as one

The item's `## Suggested work` describes only the slice shape, and mentions `split` only to exclude
the 9 field-delimiter sites. But its own Concern paragraph names two `split(HEADING)[1]` sites as
the class's provable defects. Censusing all 53 `split`-subscript sites in the discovery set:

```
12 heading separators  (5 at index [1+], 7 at index [0])
41 non-heading separators, every one a field delimiter:
   '<whitespace/no-arg>' 10, ':' 8, ': ' 6, '=' 3, '\n\n' 2, '---' 2, 'abc123' 2,
   'also in ' 2, '\n' 1, '-' 1, '.' 1, '/' 1, 'approved' 1, 'deferred' 1

The 5 heading-separator TAILS:
  tests/test_backlog.py:140                  '## Workflow history'
  tests/test_backlog.py:602                  '## Workflow history'
  tests/test_orchestrator_retirement.py:5346 '## Detailed Implementation Checklist (TODO)'
  tests/test_research_index.py:129           '## Most recent'
  tests/test_support_section.py:230          '## Workflow history'
```

The heading test is therefore clean with no borderline case: no field delimiter in the suite begins
with `#`, so the arm keeps the item's exclusion promise by construction rather than by allowlist.
Index `[0]` is deliberately not flagged (E-02 states why).

### F-04: Order 01's own control test would make this guard red on arrival, and the item's exclusion list does not say so

`tests/test_support_section.py::test_final_section_against_real_plans_render_status_index` ends with

```python
# Contrast: unbounded slice absorbs the new section and grows
unbounded_orig = out[out.index("## Sets") :]
unbounded_appended = appended[appended.index("## Sets") :]
self.assertGreater(len(unbounded_appended), len(unbounded_orig))
```

Those two slices are the DEMONSTRATION that `final_section` is worth having, so they must survive.
The backlog item's "Sites that must NOT be flagged" section lists only
`tests/test_defect_report.py`'s `prompt[start:]` and the 9 field-delimiter splits, because Order 01
was authored after that list was written. This is reported rather than quietly folded in, because the
item's list being incomplete is itself the finding: a guard built only to the item's stated exclusions
would have turned the suite red against the very control test the Set shipped. The same file also
carries a `split("## Workflow history", 1)[1]` tail at line 230 whose comment reads "The buggy
unbounded slice reads across sections to EOF", which is the split arm's equivalent of the same thing
and needs the same treatment.

### F-05: a text-reconstruction false positive no prose anticipated

`tests/test_ipd_authoring.py::_add_unassigned` splices a fixture with
`t[:idx] + block + t[idx:]`. Arm B flags the tail, and it is a false positive of a different kind
from F-04's: it asserts nothing over the tail, and the head and tail are rejoined losslessly, so
there is no section whose extent could be wrong. E-04 suppresses it structurally rather than by
exemption, and records why that distinction matters.

### Why a test, and not an `aw check` rule or a pre-commit hook

This is the same question `76ic0k` settled for the sibling guard, and the reasoning transfers
without change, so it is cited rather than re-derived. `aw check` RUNS AGAINST MANAGED TARGET
REPOSITORIES (`--dir DIR  Repo root`), so a rule refusing a slice shape in `tests/` would impose
this repository's testing conventions on a codebase that never adopted them, and no existing rule
reads a file under `tests/` at all. `aw check` also has no advisory tier available here, because
`artifact_core.drift_exit_code` exempts only `info`, so a `warning` fails the gate exactly as an
`error` does. A pre-commit hook was rejected for the reason the three existing local hooks state
about themselves in their own comments: local, not cloned by default, skippable with `--no-verify`.
The suite is what CI runs and what `make test` runs.

### Why the dependencies are load-bearing in both directions

`- Item-Dependencies: executed:tr8ugt, executed:76ic0k`.

On `tr8ugt` (Order 02): run before it, this guard is RED ON ARRIVAL against the 5 sites that plan
converts (`tests/test_oc_runipd.py` 7096 and 7234, `tests/test_plan_review_feasibility_rule.py`,
`tests/test_plans_board.py`, `tests/test_project_layout.py`), plus the 4 split-arm sites its E-01,
E-02 and E-08 convert. The only remedies available inside this plan's scope would be exempting the
very sites the Set exists to fix, or converting them here, outside this plan's declared scope.

On `76ic0k` (structpin Order 02): the backlog item asks for this sequencing explicitly, and the
reason is shape convergence rather than redness. `76ic0k` writes
`tests/test_no_code_structure_pins.py`, an AST guard over the same discovery set, and it is the file
whose narrowing decisions (exclude `tests/fixtures/` and `tests/benchmark_fixtures/`, include
`tests/support.py` and `tests/conformance_matrix.py` by name) this plan adopts verbatim. Two guards
walking `tests/` should share a shape rather than race. NOTE a real interaction to verify at
execution rather than assume: `76ic0k`'s guard flags `ast.parse`/`ast.walk` in test files and
excludes only ITS OWN path structurally, so THIS plan's new guard file is a second legitimate AST
analyzer that its detector will see. Resolve it through `76ic0k`'s own E-02 allowlist mechanism,
which exists for exactly this case and whose self-cleaning rule this file satisfies permanently (an
AST guard always contains an `ast` walk). OQ-02 records the alternative and why it was not chosen.

## Proposed changes (ordered, validatable)

1. E-01 writes the guard file with the two-arm slice detector behind a pure `(path, source)` entry point, with fixtures proving it fires and does not over-fire.
2. E-02 adds the heading-separator `split(...)[1]` arm behind the same entry point.
3. E-04 adds the structural reconstruction suppression (depends only on E-01, independent of E-02).
4. E-03 defines the typed self-cleaning exemption comment and applies it to the three legitimate sites, which requires both detector arms to be live so the exemption audit covers both.
5. E-05 adds the single `CONTRIBUTING.md` pointer bullet.

E-01 and E-03 are coupled by a shared design constraint rather than only by order: E-03's audit
requires the detector to be callable with exemptions ignored, so E-01 must land that seam. The
constraint is stated in both items so neither can be executed in a way that strands the other.

## Deferred / out of scope (with reason)

- CONVERTING ANY SITE is Order 02 (`tr8ugt`). This plan must not touch one; if it did, the guard and the conversions would land in one unreviewable change.
  - Carrier: tr8ugt
  - Carrier-Evidence: .aw/records/plans/pending/20260929-secbound-02-tr8ugt-convert-the-measured-unbounded-section-sites-onto-the-bounde.ipd.md
- FLAGGING THE `split(HEADING)[0]` HEAD SHAPE, whose fallback is the whole text rather than an unbounded tail. It is a real defect class, but its remedy differs (an explicit marker-presence assertion, not a bounded read), Order 02's E-06 converts its 7 live sites, and a guard whose message named the wrong fix would be worse than none.
  - Carrier: tr8ugt
  - Carrier-Evidence: .aw/records/plans/pending/20260929-secbound-02-tr8ugt-convert-the-measured-unbounded-section-sites-onto-the-bounde.ipd.md
- INTERPROCEDURAL BINDING TRACKING (a marker index computed in one function and sliced in another).
  - Carrier-Declined: A PERMANENT DESIGN BOUND with a measured basis, not deferred work. All 8 live slice-arm instances bind and consume within one function body, so the cross-function case has ZERO instances and building for it is the hypothetical-need generality P6 directs against. This is the same trade-off `tests/test_carrier_scan_single_item_contract.py` records as its own KNOWN HOLE. If a first instance ever appears, the correct response is to EXTEND the detector, and E-01 requires the bound be stated in the docstring so a future maintainer knows the choice was deliberate. A carrier would misrepresent a settled decision as pending work.
- DETECTING AN UNBOUNDED READ THAT OBTAINS ITS START OFFSET WITHOUT A MARKER SEARCH (a regex `match.end()`, an `enumerate`/`startswith` walk, a `partition` tail, or a hand-computed constant).
  - Carrier-Declined: A STATED BOUND rather than an obligation. The guard closes the two routes every measured instance used; `GUIDING_PRINCIPLES.md` P16 and `/plan-review` remain the standing cover for the residue, exactly as they do for `76ic0k`'s acknowledged holes. Order 02's E-05(a) converts the one live `enumerate`/`break` walk, so the shape has no live instance for a guard to protect, and a carrier promising general detection would commit to a mechanism whose false-positive rate on legitimate tail slices has not been shown acceptable.

## Scope check

- Over-scope: none. Two paths, one new test file and one documentation bullet. No production module and no existing test is touched.
- Under-scope: the guard closes two entry routes, not all of them. A regex-derived offset, a `partition()` tail, an `enumerate`/`startswith` walk, a marker index passed between functions, and a slice whose index is rebound through a temporary all evade it, which E-01 requires the docstring to say out loud. It also says nothing about whether a BOUNDED read's marker is the RIGHT one, which no syntactic check can decide. A third accepted gap: fixture modules under `tests/fixtures/` and `tests/benchmark_fixtures/` are outside the walk, so a site parked in a fixture is invisible; the exclusion matches `76ic0k`'s and those files are synthetic sample code rather than this suite's assertions.

## Required tests / validation

The guard is itself the test, so validation is mostly about proving it is NOT VACUOUS, which is the
specific failure mode of a guard that passes by finding nothing. FOUR distinct vacuity modes are in
play and each has its own demonstration, because they fail independently: either DETECTOR ARM could
match nothing (V-01 and V-02 each require a probe), the EXEMPTION could suppress more than its line
(V-03 requires the flagged count to drop by exactly one), and the EXEMPTION AUDIT could be
structurally unable to see a flagged call (V-03 requires a fabricated stale comment to fail). A green
run proves none of the four.

Run the suite BARE, as `python3 -m pytest`: `pyproject.toml` `addopts` already supplies
`-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so do not add `-n0` (several times
slower here) or a second `-q` (which compounds into `-qq` and suppresses the `N passed` line this
plan requires pasted).

The suite baseline measured at authoring HEAD `46cd2f8a5` was `3559 passed, 2 skipped` with 208
deselected. Re-derive it at execution: two Orders land first and Order 02 is expected to RAISE the
count, so the authoring number is not the baseline this plan will see. THE INVARIANT IS PARITY
AGAINST YOUR OWN PRE-CHANGE MEASUREMENT taken on the post-dependency tree, never against a number
written here; this plan adds test functions and removes none, so the only acceptable delta is the
count of tests the guard file itself contributes, and any other movement is someone else's change and
must be named rather than absorbed.

## Spec / documentation sync

No `.spec.md` amendment is owed, and no spec path appears in `Scope-Paths`. No spec describes the
suite's section-reading mechanisms; the helpers are documented in their own docstrings in
`tests/support.py` and the governing principle is `GUIDING_PRINCIPLES.md` P16, which this plan cites
and deliberately does not edit. The only documentation change is the one `CONTRIBUTING.md` pointer
bullet in E-05, which is a reference and not a restatement, per P8 and per that section's own stated
convention.

## Open questions

### OQ-01: Should the guard flag the `split(HEADING)[0]` head shape as well as the `[1+]` tail?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as NO. The two shapes fail differently and need different remedies: a `[1+]` tail reads to end of input and the fix is a bounded or declared-terminal read, whereas a `[0]` head falls back to the WHOLE TEXT when the marker is absent and the fix is an explicit marker-presence assertion (Order 02's E-06 records that it deliberately did not build a fourth `head_before()` helper for its 3 callers, so there is no bounded-head entry point for this guard to name). Flagging `[0]` here would emit a message pointing at `support.section`, which is not the remedy, and would duplicate a concern Order 02 already carries for all 7 live sites. Measured: 7 `[0]` heading sites exist, every one inside a file Order 02 declares in `Scope-Paths`. If the head shape needs an author-time guard after Order 02 lands, that is a separate detector with a separate message and should be filed as such. Owner recorded as `plan author` because this is the author's judgement from evidence, not a maintainer answer; no maintainer was asked.

### OQ-02: How should this guard file and `76ic0k`'s guard avoid flagging each other?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED as: THIS plan changes nothing, and the interaction is handled by `76ic0k`'s existing allowlist. The interaction is one-directional and asymmetric, which is what makes it cheap. `76ic0k`'s guard flags `ast.parse`/`ast.walk` in test files; this plan's guard file necessarily calls both, so `76ic0k` will flag it. The reverse does not happen: `76ic0k`'s guard contains no marker-located unbounded slice, so this plan's detector is silent on it (verified at authoring by running this detector over the discovery set, which reported zero hits in any guard file other than the three F-04/F-03 sites in `tests/test_support_section.py`). `76ic0k` E-02 ships a `(path, reason)` allowlist for exactly the case of a file whose subject requires the flagged mechanism, and its self-cleaning rule is satisfied permanently here because an AST guard always contains an `ast` walk. So the remedy is one allowlist entry in `76ic0k`'s file. THE ALTERNATIVE WAS CONSIDERED AND REJECTED: widening `76ic0k`'s structural self-exclusion from `Path(__file__)` to a set of guard paths would make the exclusion a de facto unjustified allowlist with no stated reason per entry, which is the thing that plan's E-02 exists to prevent. NOTE this is a cross-plan edit this plan does not declare: `tests/test_no_code_structure_pins.py` is NOT in this plan's `Scope-Paths`, deliberately, because adding the entry is an edit to a file `76ic0k` owns. The executor must therefore EXPECT `76ic0k`'s guard to fire once this file lands and must REPORT it with the recommended one-line entry rather than making the edit, unless a human directs otherwise. Flagged here because an executor who discovers this mid-run and silently edits another plan's file would breach the scope gate.

### OQ-03: Should the exemption comment be enforced to name a reason of some minimum substance?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as NO, require only a NON-EMPTY reason, because this repository has ALREADY DECIDED the identical question in the identical shape and the precedent is explicit. `check_engine.evaluate_carrier_obligation` accepts a `- Carrier-Declined:` escape on exactly one condition, a non-empty reason, and its docstring states why it goes no further: "The reason's MERIT is the reviewer's job, exactly as `open_question_error` says of an OQ rationale; requiring a human-judged reason here would be a semantic claim this module cannot make." That is this question verbatim, with `# aw-unbounded-ok:` in place of `- Carrier-Declined:`, so adopting a different answer here would make two sibling mechanisms disagree about the same trade-off for no stated reason. The reasoning transfers exactly: a length floor or a required citation is a PROXY for substance that an author satisfies with filler, so it buys the appearance of rigor while adding a number with no principled basis, and the real control in both cases is the reviewer who reads every new exemption. This was initially filed open with the maintainer as owner; it is resolved instead because the repository can answer it, which is the standard this plan is held to, and because an OQ left open with no durable carrier would itself be an outstanding obligation that vanishes when this plan reaches `executed` (`check.ipd-uncarried-obligation`, an `error`-severity rule, fires on exactly that). Owner recorded as `plan author` because this is the author's judgement from cited evidence, not a maintainer answer; no maintainer was asked. IF A THIN REASON IS LATER OBSERVED IN PRACTICE, the correct response is to raise it as a finding against that exemption in review, not to add a length rule.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a pasted run of `python3 -m pytest tests/test_no_unbounded_section_reads.py` on the post-dependency tree showing it passes, WITH the tree scan re-run and its full output pasted rather than assumed (Order 02 converts 9 of the sites this detector finds; if any site it declared converted still fires, that is a finding to report against Order 02, not a line to exempt). NON-VACUITY FOR EACH ARM SEPARATELY, demonstrated and not asserted: temporarily add a probe file under `tests/` containing one Arm A slice (`x[x.index("## H"):]`) and one Arm B slice (`i = x.find("## H")` then `x[i:]`), paste the resulting FAILURE showing the message names the file, the line, the unparsed expression, which arm fired, and the remedy; delete the probe; paste the pass. Paste the discovery set's size (218 files and 5,444 function bodies at authoring) and confirm `tests/fixtures/` and `tests/benchmark_fixtures/` are excluded and the repo-root `conftest.py` is outside the walk. Plus the negative fixture results proving silence on a bounded slice `x[a:b]`, a bare tail `lines[1:]` with no marker search, and a search-derived UPPER bound `x[:x.index(M)]`. Finally, quote the module docstring showing the KNOWN HOLE section states the interprocedural bound and the non-marker-offset bound.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the split arm shown NON-VACUOUS by probe, the same way as V-01: a temporary file containing `t.split("## Workflow history", 1)[1]`, the pasted FAILURE, the deletion, the pass. The EXCLUSION PROMISE verified by re-running the separator census at execution and pasting it: report the total `split`-subscript site count, how many separators are headings, and how many are field delimiters (authoring: 53 total, 12 heading, 41 field). If any NEW field delimiter now begins with `#`, say so and state how the arm treats it, because the heading test's soundness is exactly the claim that none does. Plus negative fixture results proving silence on `split(":")[1]`, `split(". ")[1]`, a non-literal separator, and a heading separator at index `[0]`; and a positive fixture proving index `[2]` fires as well as `[1]`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: every `# aw-unbounded-ok:` comment this plan adds quoted with its file, line and reason, and confirmation that there are exactly three (the `tests/test_defect_report.py` tail and the two `tests/test_support_section.py` control slices) or an explanation of any difference found at execution. The exemption shown to work with the flagged count dropping by EXACTLY ONE when applied to one site, pasted before and after, which is what proves it is per-site rather than per-file. The empty-reason rule demonstrated: a `# aw-unbounded-ok:` with no reason must FAIL; paste it, then revert. The audit's SELF-CLEANING property demonstrated: place an exemption comment on a line the detector would not flag, paste the FAILURE naming that line as a stale exemption, remove it, paste the pass. The audit shown NON-VACUOUS: paste evidence that it calls the detector with exemptions IGNORED and therefore still sees the three exempted sites, rather than returning the empty list the exemption filter would guarantee.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `tests/test_ipd_authoring.py`'s `_add_unassigned` shown suppressed, with a pasted scan confirming it is absent from the violation list AND a search of that file confirming it carries no `# aw-unbounded-ok:` comment, which together prove the suppression is structural and not an exemption. A positive fixture proving a tail slice NOT in a complementary concatenation still fires. Negative fixtures proving silence on the three-operand `t[:i] + block + t[i:]` and the two-operand `t[:i] + t[i:]`. A positive fixture proving a MISMATCHED rejoin (`t[:i] + u[j:]`, different subject and different index) is still flagged, which is what stops the suppression becoming a blanket escape for any slice that appears beside a `+`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the added `CONTRIBUTING.md` bullet quoted; `git diff` for the file pasted, showing only that one bullet changed and that `## Self-tests (run before pushing tool changes)` is untouched; a confirmation that the added text contains no em or en dash; a confirmation that the guard-test path the bullet names exists (paste the `ls`); and a confirmation that `GUIDING_PRINCIPLES.md` was NOT modified by this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

DO NOT EXECUTE BEFORE BOTH DEPENDENCIES REACH `executed`. This plan declares
`- Item-Dependencies: executed:tr8ugt, executed:76ic0k` and both edges are load-bearing, not
cosmetic. Run before `tr8ugt` and this guard is RED ON ARRIVAL against the 9 sites that plan
converts, and the only remedies inside this plan's scope would be exempting the very sites the Set
exists to fix or converting them here, out of scope. Run before `76ic0k` and the two guards'
discovery-set narrowing decisions are being invented twice instead of once, which is the collision
the backlog item asked to avoid. The runner re-checks dependencies at dispatch and will mark this
item `dependency-blocked` rather than run it; an agent executing the Set by hand must honor the same
order.

EXPECT `76ic0k`'S GUARD TO FIRE ON THIS NEW FILE, AND DO NOT SILENTLY FIX IT. This file is a
legitimate AST analyzer, so it necessarily calls `ast.parse` and `ast.walk`, which
`tests/test_no_code_structure_pins.py` flags in any test file but its own. The remedy is one entry in
that guard's `(path, reason)` allowlist, which exists for this case. That file is deliberately NOT in
this plan's `Scope-Paths` because it belongs to another plan, so REPORT the firing with the
recommended entry and let a human decide, rather than editing it. See OQ-02.

EXECUTE ONLY WHAT THIS PLAN DECLARES. The two `Scope-Paths` entries are the whole authorized surface;
this is a DECLARATION so the finalize scope gate can reconcile what was actually edited against what
was declared, and an out-of-scope edit is made and then JUSTIFIED with `--scope-reason` rather than
avoided by halting. THE ONE EXCEPTION IS A GENUINELY UNSAFE CONDITION, and it is live here: if the
guard fires on a site this plan did not predict, STOP and report it rather than proceeding, because
every remedy available inside this plan's scope is wrong. Adding an exemption comment to make the
suite green is the exact failure mode E-03 exists to prevent (it institutionalizes the unbounded read
while appearing to complete the plan), and converting the offending site is outside `Scope-Paths` and
belongs to Order 02 or a new carrier. Report which site fired, with its arm and line, and let a human
decide.

DO NOT WEAKEN THE GUARD TO MAKE IT PASS. A guard that passes because it detects nothing is worse than
no guard, since it advertises a protection that does not exist. V-01, V-02, V-03 and V-04 therefore
each require a DEMONSTRATED failure and revert, not an assertion that the guard would fail.

HONESTY. Paste actual runner output; never claim a test run you did not perform. Where an authoring
baseline is quoted (the 8 slice sites, the 53 `split`-subscript sites of which 12 are headings, the
218-file and 5,444-function discovery set, the `3559 passed, 2 skipped` suite), re-measure at
execution and report the new number if it differs rather than restating the authoring figure.

COMMIT DISCIPLINE. Commit through `aw commit <plan> -- <paths>`, path-scoped to the two files this
plan names, never `git add -A`/bare/`-a`, and never push. Other agents may be working in this
checkout: verify the staged set with `git diff --cached --name-only` before committing and unstage
anything that is not yours with `git restore --staged <path>`.

LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item must
carry pasted evidence before this plan moves to `.aw/records/plans/executed/`. Use the tooled
transition; do not hand-edit `- Status:`. Reaching `executed/` via `aw ipd finalize` is
UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER owns
that transition, so do not invoke `aw ipd finalize` yourself in a runner-driven execution; a HAND
execution invokes it. Never hand-roll a `git mv` to `executed/`. Backlog item `ap839o` is this plan's
sole carrier, so it may close `done` once this plan is genuinely executed.
