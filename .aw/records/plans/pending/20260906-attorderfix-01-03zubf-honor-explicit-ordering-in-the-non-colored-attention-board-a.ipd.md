# IPD: Honor explicit ordering in the non-colored attention board and de-flake the live-repo alias tests

- Date: 2026-09-06
- Kind: child
- Concern: CORRECTIVE PLAN for executed plan `8ldrlx` (`attorder-01`), which fixed the COLORED table path and left the NON-COLORED board path broken. `8ldrlx` recorded the defect as its own finding F-2 ("in non-colored mode, `render_board()` partitions items into attention classes, so sorting only occurs within each class section rather than globally") and then authored NO E-item for it and listed it in NEITHER `Deferred / out of scope` NOR `Under-scope`, which reads `none`. So a measured defect was found, written down, and silently dropped, and the plan was finalized to `executed/` claiming completeness.
  THIS IS THE MORE CONSEQUENTIAL HALF OF THE ORIGINAL BUG, which is why it needs its own plan rather than a footnote. Non-colored output is the PIPED / AGENT / CI path: `render_board` selects it whenever color is off (`attention.py:1741-1752`), so it is what every agent, every `| head`, every `| grep`, and every CI job sees, while the colored table `8ldrlx` fixed is only reachable at an interactive TTY. Measured through the real CLI on a fixture repo (see F-1): under `-o priority`, `--format json` correctly returns `bbb222(high), ddd444(high), aaa111(medium), ccc333(low)`, while the non-colored board prints the `high`-priority `ddd444` LAST, after two lower-priority items, because it sits in a later class section. So `aw next -o priority | head` still returns the wrong items, which is the exact user-visible failure `8ldrlx` set out to fix.
  A SECOND, INDEPENDENT DEFECT IS FIXED HERE because it blocks trustworthy validation of the first: the four `AliasEquivalenceTests` shell out with `cwd=str(REPO_ROOT)` (`tests/test_next_ordering.py:182`) and diff whole-stdout across the four command aliases, so they read the LIVE repository and compare output captured at four different instants. Any concurrent commit between the four subprocess calls changes the scan mid-test and the diff fails. Observed during review: `test_all_four_names_agree_under_details_and_long` FAILED with a 16815-character diff while other agents were committing, then passed on 7 subsequent runs. That is a false-failure generator sitting on the exact test file this plan must extend, and it is fixable outright rather than merely tolerable (F-5).
- Scope: Make the non-colored board honor an explicit `--order-by` by emitting a single globally-ordered list instead of class-partitioned sections, while preserving the class-sectioned form byte-for-byte when no explicit order is given. Then point the four `AliasEquivalenceTests` at a purpose-built temporary fixture repository instead of the live checkout, so the alias-equivalence property is tested against a static input. NO change to the resolver vocabulary, the sort engine, the colored table, the JSON shape, or the default view.
- Scope-Paths: agent_workflows/attention.py, tests/test_next_ordering.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: attorderfix
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 03zubf
- Approval: 2026-09-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-07 approved (aw set): status set to approved

- 2026-09-06 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 all FIXED; GO - PENDING HUMAN APPROVAL. Structural lint conforming at `--phase author` (exit 0, zero diagnostics) and again at `--phase review-finalize`. Pre-review snapshot SKIPPED: target already committed and unchanged at `d6caf176`. SELF-REVIEW DISCLOSED (I authored this plan in the same session), so the round was run adversarially by construction; an independent re-review before execution is still worthwhile, since a self-review is precisely what cleared `8ldrlx` with its F-2 dropped. EVERY MATERIAL CLAIM RE-VERIFIED FROM SOURCE, not trusted: `order_by` does reach `render_board` (`:1731`) and both call sites pass it (`:2179-2180`, `:2212-2213`); the non-colored branch does rebuild `by_class` and ignore it (`:1765-1768`); the multi-key tuple does sit above the class rank (`:656-660`). The defect was INDEPENDENTLY REPRODUCED through the real CLI on a fixture repo, matching F-1's evidence string exactly. F-3 and F-4 confirmed against the `8ldrlx` record and its review (the grep returns 0). PR-001 (HIGH) is the substantive finding: the plan would NOT have fully delivered its own goal, because `cmd_attention` extracts release-blockers into a trailing section UPSTREAM of the renderer (`:2162-2202`) where E-01 cannot reach, measured as a `low`-priority blocker printing last under `-o priority`; fixed by adding E-06 + V-06 on the same shared predicate. PR-002 (MEDIUM): E-02's mandated `[hidden; use --all]` notice would have invented a third behavior, since the colored flat form filters those classes SILENTLY (`:1675-1676`) while the notice is sectioned-and-non-colored only (`:1782-1785`); now requires no notice. PR-003 (LOW): recorded the two out-of-scope `render_board` test callers as a measured REGRESSION ORACLE (neither passes `order_by`) and forbade editing them to silence a failure. Deliberately NOT flagged: the scope fence correctly uses declare-then-justify rather than a stop-on-out-of-scope-edit directive (2026-09-01 ruling), and `- Readiness:` was correctly absent at authoring and is written by this review.
- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after a maintainer-requested review of another agent's claim that `8ldrlx` was "fully implemented". The delivered half is genuinely correct and I verified it rather than trusting the write-up: the colored table honors `-o priority` across class boundaries, the default (no `-o`) table order is unchanged, multi-key `-o priority,status,id6` exits 0, an invalid token exits 2, help text documents the comma syntax, and spec 8.5 determinism holds because `ctime`/`mtime` are not read in the default view (confirmed absent from default JSON item data). The bare suite is green at `5536 passed, 3 skipped, 2 xfailed`, and commit `129106db` touched exactly the four declared Scope-Paths. WHAT THE REVIEW FOUND is that `8ldrlx`'s own F-2 named the non-colored board defect and no E-item ever addressed it, while `Under-scope` says `none`; the plan-review that cleared the plan (`REVIEWED`, PR-001..PR-005, by `antigravity/gemini-2.5-pro` reviewing a plan authored in the same session) never mentions F-2 either. Both defects in this plan are REPRODUCED THROUGH THE REAL CLI on a purpose-built fixture repo rather than asserted from reading, and the de-flake approach was PROTOTYPED before being written down: a static two-item fixture yields byte-identical output across all four aliases (four identical md5 hashes) and its output provably depends only on the fixture. Also noted for the record: `8ldrlx` carries `- Readiness: go-pending-approval` with no `/plan-review` in its history that wrote it, the same unattested-readiness pattern backlog `754txs` tracks; this plan deliberately OMITS that field.
- 2026-09-06 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw next -o <key>` return the right items when its output is piped, which is how agents and CI consume it, and remove a live-repo race that produces false test failures on the file this change must extend.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the non-colored board honor an explicit order

- [ ] E-01 In `agent_workflows/attention.py`, make `render_board`'s NON-COLORED path emit ONE globally-ordered list when `order_by` is an explicit key, instead of partitioning into per-class sections. The parameter is ALREADY PLUMBED: `render_board` accepts `order_by` (`attention.py:1731`) and both `cmd_attention` call sites already pass it (`:2171-2180`, `:2204-2213`), and the colored path already forwards it to `render_table`. The non-colored path below simply ignores it and rebuilds `by_class` (`:1765-1768`), which is the whole defect. RE-LOCATE BY SYMBOL; every line number here may drift.
  THE PREDICATE MUST MATCH THE COLORED PATH EXACTLY, not be invented independently: treat an order as explicit when `order_by` is truthy AND differs from `A.ORDER_CLASS`, which is the same condition E-01 of `8ldrlx` established for `render_table` (recorded in that plan's review as D-3). Two renderers disagreeing about what "explicit" means would be a new inconsistency in place of the old one, so derive the predicate ONCE (a module-level helper both paths call) rather than writing the comparison twice.
  DO NOT REORDER HERE. `cmd_attention` has already sorted the items through `sort_items`, and the JSON path proves that ordering is correct (F-2). This item changes only how rows are GROUPED for printing; calling a sort inside a renderer is the mistake `8ldrlx` was fixing.
  - Depends on: none
  - Expected outcome: with an explicit `-o`, the non-colored board prints every item in the caller's exact sequence with no `## <class>` section headers interleaved; with no `-o`, output is byte-identical to today.
  - Execution state: pending

- [ ] E-02 Decide and record what happens to the SECTION HEADERS and the HIDDEN-CLASS RULE under an explicit order, because a global list has no sections to hang them on and two behaviors are load-bearing rather than cosmetic.
  FIRST, THE `done`/`parked` SUPPRESSION MUST SURVIVE. Today the non-colored path prints `## <cls> (N) [hidden; use --all]` and SKIPS the group's items unless `--all` (`attention.py:1783-1787`). That is a filtering rule, and losing it would make an explicit `-o` silently reveal items the default view hides, changing what `aw next -o priority` MEANS rather than just its order. Preserve the suppression by filtering those items out of the global list, honoring `show_all`.
  THE NOTICE LINE IS DELIBERATELY NOT REQUIRED IN THE FLAT FORM, and the reason is a measured asymmetry the original draft of this item got wrong (PR-002). The `[hidden; use --all]` line is a property of the SECTIONED form: it is emitted per class group and only when NOT colored (`attention.py:1782-1785`), whereas `render_table` filters the same two classes SILENTLY with no notice at all (`:1675-1676`). So under an explicit order the flat non-colored form should match the flat COLORED form it now parallels, and emit no notice. Requiring one would invent a third behavior and put a `## `-prefixed line into an output whose whole point is that it has no section headers, which would also break the `^- ` row-grep shape agents rely on being the only content lines. IF the executor judges a notice genuinely necessary, it MUST be added to BOTH flat paths identically and recorded as a deliberate change to `render_table`'s output, which is outside this plan's fence: prefer emitting none.
  SECOND, KEEP THE PER-ITEM CLASS VISIBLE. `_render_item_row` takes the class as an argument (`:1797-1806`) and the row's shape is the documented stable form `- [tree] path (status){gate}`, which agents parse. Do NOT change that shape to add a class column: it is the machine-readable contract named in `render_board`'s own docstring (`:1735-1740`). Pass each item's OWN `it.attention_class` so any class-derived rendering stays correct in a mixed list, and record in the docstring that under an explicit order the sections are absent BY DESIGN.
  - Depends on: E-01
  - Expected outcome: `done`/`parked` items remain hidden without `--all` under an explicit order, with the hidden notice still emitted; the per-item row shape is unchanged byte-for-byte; the docstring states that explicit ordering yields a flat list.
  - Execution state: pending

- [ ] E-06 FIX THE SECOND FRAGMENTATION SOURCE, WHICH IS UPSTREAM OF THE RENDERER AND WHICH E-01 CANNOT REACH (found in review, PR-001). `cmd_attention`'s non-colored branch pulls RELEASE-BLOCKERS out of the item list BEFORE calling `render_board` and appends them as a trailing `## release-blockers for <version> (<id6>)` section (`attention.py:2162-2202`). So even after E-01 emits one flat list, a release-blocking item is still extracted and printed outside the ordering entirely. MEASURED IN REVIEW on a fixture repo: with a `Blocks-Release: next` item at `low` priority, `-o priority` prints `bbb222(high), aaa111(medium), ccc333(low)`, then `## blocked`, then `## release-blockers ... eee555(low)` LAST, so the flat list E-01 produces would still be split three ways.
  UNDER AN EXPLICIT ORDER, DO NOT EXTRACT THE BLOCKERS: leave them in the single ordered list so the requested order is total. Their release-gate status is NOT lost, because `_render_item_row` already renders a per-item gate marker (the same mechanism that prints `[gate item: aaa111]` on a blocked row), which is exactly why extraction is a PRESENTATION choice rather than an information carrier.
  WITH NO EXPLICIT ORDER, KEEP THE TRAILING SECTION EXACTLY AS IT IS, including the release id6-and-version header, since that grouping is deliberate (it surfaces the planned release during ordinary use) and its bytes are part of the default view this plan must not change.
  USE THE SAME SHARED PREDICATE E-01 derives, so three call sites cannot drift apart. Note this edit is in `cmd_attention`, not `render_board`, which is why it is a separate E-item rather than a clause of E-01.
  - Depends on: E-01
  - Expected outcome: under an explicit `-o`, a release-blocking item appears in its correct ordered position with its gate marker and NO trailing `## release-blockers` section is emitted; with no `-o`, the trailing section and its header are byte-identical to today.
  - Execution state: pending

### Task group 2: de-flake the live-repo alias tests

- [ ] E-03 Point the four `AliasEquivalenceTests` at a temporary FIXTURE repository instead of the live checkout. The class's `_run` helper passes `cwd=str(REPO_ROOT)` (`tests/test_next_ordering.py:179-186`) and each test captures stdout from FOUR separate subprocesses, then asserts the four are byte-equal; a commit landing between call one and call four changes the scan and fails the diff. MEASURED: `test_all_four_names_agree_under_details_and_long` failed with a 16815-character diff during concurrent commits, then passed 7 consecutive runs (F-5).
  THE FIX IS A STATIC INPUT, NOT A RETRY OR A LOOSER ASSERTION. Build the fixture ONCE per class (`setUpClass` with a `TemporaryDirectory`, torn down in `tearDownClass`) and point `_run`'s `cwd` at it. Use the file's OWN existing fixture helpers rather than inventing a second shape: `_backlog()` (`:99-110`) already emits the real bullet form, and the `tempfile.TemporaryDirectory` + `_write` pattern is used by the scan tests (`:504-535`). PROTOTYPED BEFORE WRITING: a two-item static fixture gives four IDENTICAL md5 hashes across `next`/`attention`/`att`/`todo` under `--details --no-color`, and its output provably changes only when the fixture changes.
  THE FIXTURE MUST CONTAIN AT LEAST TWO CLASSES AND TWO PRIORITIES, because these tests are the natural place to catch a regression in E-01: a single-class fixture cannot distinguish sectioned output from a global list. Keep it MINIMAL and CLEAN otherwise (a fixture that trips `attention.missing-status` prints `VIEW INVALID` and tests the wrong thing; verified live while prototyping).
  DO NOT WEAKEN WHAT THESE TESTS PIN. Their subject is that all four aliases share one parser and therefore agree under every flag; that property is fully testable against a fixture and must remain a whole-stdout byte comparison, not a substring or length check.
  - Depends on: none
  - Expected outcome: the four alias tests read only the fixture; a concurrent commit to the live repo cannot affect them; each still asserts byte-equal stdout across all four names.
  - Execution state: pending

- [ ] E-04 Leave the two OTHER `REPO_ROOT` subprocess call sites ALONE, and say why in a comment so a later reader does not "finish the job" and delete real coverage. `tests/test_next_ordering.py:258-266` (`test_unknown_key_is_refused_by_argparse_with_the_valid_list`) and `:808-816` (`test_multi_key_with_invalid_token_is_refused_by_argparse`) also run in `REPO_ROOT`, but they assert only an argparse REFUSAL (exit 2 plus stderr content) which argparse decides BEFORE any scan, so no repository content reaches the assertion and there is nothing to race. MEASURED: `-o bogus,priority` exits 2 against the live repo, and the vocabulary list in stderr comes from the contract tuple, not from disk.
  This item is DELIBERATELY SEPARATE from E-03 so the reasoning is recorded rather than implied by an absence, and so a future sweep for `cwd=str(REPO_ROOT)` finds an explicit justification at each remaining site.
  - Depends on: E-03
  - Expected outcome: both refusal tests are unchanged and still pass; each carries a one-line comment stating it is scan-independent by construction; no third `REPO_ROOT` scanning site remains unjustified.
  - Execution state: pending

### Task group 3: prove both fixes

- [ ] E-05 Add tests pinning BOTH behaviors, at the renderer level and through the real CLI.
  (a) THE DEFECT ITSELF, which no existing test covers: build items spanning TWO attention classes whose class order CONFLICTS with the requested order (the case that makes the bug visible; a fixture where the two agree passes even when broken, which is why this must be stated explicitly). Assert the non-colored `render_board` prints the higher-priority item FIRST even though its class sorts later. The reproduction to encode, measured live via the CLI on a fixture repo: under `-o priority`, JSON gives `bbb222(high), ddd444(high), aaa111(medium), ccc333(low)` while today's board prints the `high` `ddd444` last.
  (b) THE DEFAULT IS UNCHANGED: with no `order_by`, the non-colored board still emits `## <class> (N)` sections in `A.ATTENTION_CLASS_ORDER`. Assert on the section headers, not merely on item order, since the sections ARE the default contract.
  (c) THE HIDDEN-CLASS RULE SURVIVES (E-02): a `done` or `parked` item stays absent under an explicit order without `--all`, and appears with it.
  (d) FIXTURE ISOLATION IS REAL (E-03): assert `_run`'s working directory is the fixture and not `REPO_ROOT`, so a later refactor cannot silently point it back at the live tree.
  (e) THE RELEASE-BLOCKER CASE (E-06, added in review): a `Blocks-Release` item at a priority that should place it FIRST must appear first in the flat list under `-o priority`, with no trailing `## release-blockers` section; and with no `-o` the trailing section must still appear with its `for <version> (<id6>)` header. This case needs a release record present to resolve `next`, so build one in the fixture (a `planned` release), as the review's reproduction did.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. Note that `tests/test_next_ordering.py` takes roughly 3 minutes on its own because the alias tests spawn subprocesses that each scan a tree; that is expected, and E-03 should reduce it since a small fixture scans faster than the live repo. Report the measured change rather than predicting it.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a test that FAILS on today's code and passes after E-01; the default sectioned form and the hidden-class rule both pinned; fixture isolation asserted; bare suite green with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `order_by` IS ALREADY PLUMBED to `render_board` and both `cmd_attention` call sites pass it; only the non-colored branch ignores it. So this is a small change at a known seam, not new wiring.
- THE TWO RENDER PATHS SPLIT ON COLOR, not on a flag: `render_board` returns `render_table(...)` when `term.color` is true and otherwise falls through to the sectioned form (`attention.py:1741-1752`). Colored means interactive TTY; non-colored means piped, `--no-color`, `NO_COLOR`, agent, or CI. That is why the unfixed half is the one that matters more.
- THE NON-COLORED ROW SHAPE IS A MACHINE CONTRACT, stated in `render_board`'s docstring: "the stable machine-readable `- [tree] path (status){gate}` form so agents and grep keep a fixed, parseable shape". Do not alter it.
- SORTING BELONGS TO `cmd_attention`, NOT THE RENDERERS. `sort_items` / `sort_items_with_notices` own ordering, and the multi-key tuple sits above the class rank inside the sort key (`attention.py:654-660`), so a globally correct order already reaches the renderer. The JSON path proves it.
- SPEC 8.5 FIXES THE DEFAULT, NOT EVERY VIEW: it requires "a fixed sort (class order, then normalized path, then id)" and byte-determinism with no mtimes in the default output. An explicit `-o` is a user override of the default and is spec-compatible; the `ctime`/`mtime` keys are only read when named, which I verified is still true (they do not appear in default JSON item data). Preserving the no-`-o` bytes exactly is what keeps 8.5 satisfied.
- SPEC 8.7 HAS AGENTS CONSUME `--format json`, which is already correctly ordered. That bounds the blast radius of the board defect to human-and-shell consumers, and is a reason to fix it without alarm rather than a reason to leave it.
- The file already has fixture helpers (`_backlog`, `_plan`, `_write`) and a `tempfile.TemporaryDirectory` pattern in the scan tests. Reuse them; do not invent a second fixture shape.
- Run the suite BARE: `python3 -m pytest`. The configured `addopts` already supply quiet, parallel, and the fast subset. Do not add `-n0` (measurably several times slower here) or a second `-q` (compounds to `-qq` and suppresses the `N passed` line this plan requires pasted).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | **THE DEFECT, REPRODUCED THROUGH THE REAL CLI.** On a fixture repo with four backlog items, `next -o priority --format json` returns `bbb222(high), ddd444(high), aaa111(medium), ccc333(low)`, but `next -o priority --no-color` prints `## ready (3)` with `bbb222, aaa111, ccc333` and then `## blocked (1)` with `ddd444`, placing a `high`-priority item AFTER two lower-priority ones. So `aw next -o priority \| head` returns the wrong items. | live CLI runs 2026-09-06 on a purpose-built fixture repo |
| F-2 | The sort engine is CORRECT and the bug is purely in the non-colored renderer. `sort_items(items, "priority")` returns `[('bbb222','high','blocked'), ('aaa111','low','active')]` for a deliberately conflicting pair, crossing class boundaries as intended, and the JSON path preserves it. Only `render_board`'s non-colored branch re-groups. | direct `sort_items` probe plus `--format json` comparison, 2026-09-06 |
| F-3 | **`8ldrlx` FOUND THIS AND DROPPED IT.** Its F-2 states the section-partitioning behavior verbatim and cites `attention.py:1703-1707`. No `E-*` item addresses it, `Deferred / out of scope` lists only the `:asc`/`:desc` syntax question, and `Scope check` says `Under-scope: none`, which is false. | `.aw/records/plans/executed/20260906-attorder-01-8ldrlx-...ipd.md:73`, `:88`, `:93` |
| F-4 | The plan-review that cleared `8ldrlx` never mentions F-2 either: `grep -n "F-2\|render_board\|non-color"` over the review returns NOTHING, across five findings PR-001..PR-005 and three decisions D-1..D-3. The reviewer was `antigravity/gemini-2.5-pro` reviewing a plan authored in the same session (a self-review). | `.aw/records/reviews/20260906-attorder-01-8ldrlx-...review.md`, measured grep |
| F-5 | **THE FLAKY TEST IS REAL AND ORDER/TIMING DEPENDENT.** `test_all_four_names_agree_under_details_and_long` FAILED with a 16815-character diff during a run while other agents were committing, then passed on 7 consecutive later runs (3 fixed-order, 4 randomized). Mechanism: `_run` uses `cwd=str(REPO_ROOT)` and each test compares stdout from four separate subprocesses, so a commit landing between them changes the scan mid-test. Not a regression from `8ldrlx`; a pre-existing race its new tests inherit. | `tests/test_next_ordering.py:179-186`; 8 measured runs 2026-09-06 |
| F-6 | **THE DE-FLAKE WORKS, PROTOTYPED.** A static fixture repo containing two backlog items yields four IDENTICAL md5 hashes for `--details --no-color` across `next`/`attention`/`att`/`todo`, and adding a third item changes the hash, proving the output depends on the fixture alone rather than on the live tree. | prototype 2026-09-06 in a scratch fixture repo |
| F-7 | A fixture that violates a contract rule renders `VIEW INVALID: contract violations must be resolved...` and tests the wrong code path, so the fixture must be CLEAN. Hit live while prototyping: a backlog file missing `- Status:` produced `attention.missing-status` for all four aliases. | prototype run 2026-09-06 |
| F-8 | Two other `cwd=str(REPO_ROOT)` subprocess sites are NOT racy and must not be swept up: both assert only an argparse refusal decided before any scan. Verified: `-o bogus,priority` exits 2 against the live repo. | `tests/test_next_ordering.py:258-266`, `:808-816`; live exit-code probe |
| F-9 | THE DELIVERED HALF OF `8ldrlx` IS GENUINELY CORRECT, independently re-verified, so this plan is corrective and not a revert: the colored table honors `-o priority` across classes, the no-`-o` default table order is unchanged, `-o priority,status,id6` exits 0, `-o bogus,priority` exits 2, help documents the comma syntax, `ctime`/`mtime` stay out of the default view, commit `129106db` touched exactly the four declared paths, and the bare suite is green at `5536 passed, 3 skipped, 2 xfailed`. | independent verification 2026-09-06 at HEAD `3d239cfa` |
| F-10 | `render_board`'s non-colored path carries a FILTERING rule, not only a grouping one: `done`/`parked` groups print a `[hidden; use --all]` notice and skip their items unless `show_all`. A naive flattening would silently reveal hidden items, changing what the command means. | `agent_workflows/attention.py:1783-1787` |
| F-11 | **A SECOND FRAGMENTATION SOURCE EXISTS UPSTREAM OF THE RENDERER** (found in review, PR-001). `cmd_attention`'s non-colored branch extracts `release_blockers` from the item list BEFORE calling `render_board` and appends them as a trailing `## release-blockers for <version> (<id6>)` section, so E-01 alone would still leave the order split three ways. MEASURED: a `Blocks-Release: next` item at `low` priority prints AFTER `## blocked` under `-o priority`, outside the ordering entirely. Their gate status is carried per-item by `_render_item_row` already, so extraction is presentation, not information. | `agent_workflows/attention.py:2162-2202`; fixture-repo CLI run in review |
| F-12 | **THE TWO FLAT FORMS DISAGREE ABOUT NOTICES, so requiring one would invent a third behavior** (found in review, PR-002). The `[hidden; use --all]` line is emitted per class group and ONLY when not colored (`:1782-1785`), whereas `render_table` filters `done`/`parked` SILENTLY with no notice (`:1675-1676`). The original draft of E-02 mandated the notice in the flat form, which would have made the flat non-colored output differ from the flat colored output it now parallels, and would have put a `## `-prefixed line into a form whose defining property is having no section headers. | `agent_workflows/attention.py:1675-1676` versus `:1782-1785` |
| F-13 | Two OTHER test modules call `render_board` and are deliberately out of Scope-Paths, verified safe rather than assumed: neither `tests/test_attention_compact.py` nor `tests/test_attention_priority_blocker.py` passes `order_by` (`grep -c` returns 0 for both), so both exercise the default sectioned path E-01 must leave untouched. That makes them a regression oracle for this change. | measured greps 2026-09-06 |

## Proposed changes (ordered, validatable)

1. Make the non-colored board emit one globally-ordered list under an explicit `-o`, using a predicate shared with the colored path, and reordering nothing (E-01).
2. Preserve the `done`/`parked` suppression and the stable per-item row shape in the flat form, emit no notice line, and document that sections are absent by design (E-02).
3. Stop extracting release-blockers into a trailing section under an explicit order, using the same shared predicate, leaving the default view's section byte-identical (E-06).
4. Point the four alias tests at a static two-class fixture repository built once per class (E-03).
5. Leave the two non-racy refusal tests alone, with a recorded reason at each site (E-04).
6. Pin the defect, the unchanged default, the hidden-class rule, the release-blocker case, and fixture isolation; run the bare suite (E-05).

## Deferred / out of scope (with reason)

- CHANGING THE COLORED TABLE. `8ldrlx` E-01 fixed it and I re-verified it works (F-9). Touching it here would risk the one part that shipped correctly.
- CHANGING THE SORT ENGINE, THE KEY VOCABULARY, OR THE JSON SHAPE. All three are correct (F-2); the bug is renderer-local. In particular do NOT "fix" ordering by sorting inside a renderer, which is the mistake `8ldrlx` was correcting.
- ADDING `:asc`/`:desc` PER-KEY DIRECTION MODIFIERS. Deferred by `8ldrlx` decision D-2 on KISS grounds; that ruling stands and is not revisited here.
- AMENDING `8ldrlx` IN PLACE. Forbidden by the execution contract: a plan already in `executed/` gets a corrective IPD, which is this document. Its F-2 stays as written, since the record of what was found and dropped is the useful history.
- RETROACTIVELY FIXING `8ldrlx`'s UNATTESTED `Readiness:` FIELD. That is one instance of the pattern backlog `754txs` already tracks (auto-approve trusts an unattested readiness), and editing a finalized plan's metadata to fix a process defect would itself be an in-place amendment. Recorded here; belongs to that item.
- A REPO-WIDE SWEEP FOR OTHER TESTS THAT SCAN THE LIVE TREE. This plan de-flakes the file it must extend, on evidence. A general sweep needs its own measurement pass and would widen scope well past two files.

## Scope check

- Over-scope: none. One module (two functions in it) plus one test file.
- Scope-Paths justification: `agent_workflows/attention.py` holds BOTH `render_board` (E-01, E-02) and `cmd_attention`'s release-blocker extraction (E-06), which is why one path covers both fixes; `tests/test_next_ordering.py` holds the alias tests and every new assertion (E-03, E-04, E-05). No CLI or contract change is needed because `order_by` already reaches the renderer and both `cmd_attention` call sites already pass it (verified `attention.py:2179-2180`, `:2212-2213`).
- OTHER `render_board` CALLERS ARE MEASURED SAFE, NOT ASSUMED (PR-003). `tests/test_attention_compact.py` and `tests/test_attention_priority_blocker.py` both call `render_board` and are NOT in Scope-Paths. Verified in review: neither passes `order_by` (`grep -c order_by` returns 0 for both), so both stay on the default sectioned path that E-01 leaves byte-identical. They are therefore a REGRESSION ORACLE for this change rather than a gap: if either starts failing, E-01 has altered the default view and that is a defect, not a test to update. Do NOT edit them to make a failure go away; if one fails, stop and report.
- Under-scope, stated honestly rather than left as `none`: this plan does NOT sweep other live-repo-scanning tests, does not touch the colored path, does not add a notice line to `render_table`'s silent filter (E-02), and does not revisit the deferred direction-modifier syntax. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. Baseline at authoring: `5536 passed, 3 skipped, 2 xfailed in 182.09s` at HEAD `3d239cfa`.
- Targeted: `tests/test_next_ordering.py` in full (expect roughly 3 minutes today; report the measured change after E-03).
- A LIVE CLI DEMONSTRATION on a fixture repo, before and after, showing `next -o priority --no-color` and `next -o priority --format json` agreeing on order after the fix and disagreeing before it. Renderer-level unit tests alone do not show the user-visible behavior, which is the whole point of the plan.
- A BYTE-EQUALITY CHECK that the default (no `-o`) non-colored board is unchanged: capture it before and after and diff, since spec 8.5 fixes that output.
- Repeated-run evidence for the de-flake: run `tests/test_next_ordering.py` at least 3 times, and at least once while the live repository is being modified, to show the alias tests no longer depend on it.
- `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `attention-registry-and-cross-tree-status` §8.5 requires the DEFAULT view to use "a fixed sort (class order, then normalized path, then id)" with byte-deterministic output. This plan does not change the default: E-01 gates the flat form on an explicit non-`class` `order_by`, and E-05(b) plus the byte-equality check above prove the no-flag bytes are untouched. An explicit `-o` is a user override, which the spec's ordering vocabulary already contemplates. NO spec change is required or authorized.

`render_board`'s DOCSTRING must be updated (E-02) to state that an explicit order yields a flat globally-ordered list while the default keeps class sections, because that docstring is where the two output forms are currently described and it would otherwise become wrong. Do NOT change the documented per-item row shape.

No user-facing help text needs changing: `--order-by`'s help already documents multi-key ordering and the "items lacking the selected key sort LAST; ordering never filters" rule, which the flat form honors. If the executor DOES touch user-facing prose, write no em or en dashes.

## Open questions

### OQ-01: Under an explicit order, should the non-colored board keep class section headers or emit one flat list?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONE FLAT LIST. Keeping sections is what causes the bug: sections impose class as an implicit primary sort key, so any requested order can only ever apply WITHIN a class, and no amount of intra-section sorting makes `-o priority` return the highest-priority item first (F-1). This also matches what the colored path already does after `8ldrlx` E-01, which renders one table with no class grouping, so the two paths agree rather than diverging further. The information the headers carried is not lost: each row already renders its own class context through `_render_item_row`, and the `done`/`parked` hidden notice is preserved explicitly by E-02.

### OQ-02: Should the `done`/`parked` suppression apply under an explicit order?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, it must be preserved (F-10). That rule is FILTERING, not grouping: the non-colored path prints a `[hidden; use --all]` notice and omits those items unless `show_all`. Dropping it while flattening would make `aw next -o priority` silently list items the default view hides, which changes what the command MEANS rather than merely how it is ordered, and would surprise a user who added a sort flag expecting only a reordering. `--all` continues to reveal them, so nothing becomes unreachable.

### OQ-03: Should the alias tests be de-flaked in this plan, or filed separately?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: IN THIS PLAN, decided by the maintainer when commissioning it ("Can we fix the flaky-test outright?"). It is fixable outright rather than merely suppressible, and the fix was prototyped before being written down (F-6). Two further reasons make bundling correct rather than convenient: the flaky tests live in the SAME file this plan must extend with new assertions, so a separate plan would collide on it; and E-05 must be able to trust that file's results, which a known false-failure generator undermines. The alternative of a retry decorator or a loosened assertion was rejected because it would hide the race instead of removing its cause.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the BEFORE and AFTER output of `next -o priority --no-color` and `next -o priority --format json` on a fixture repo containing items in at least two attention classes with conflicting priorities. BEFORE must show the board and the JSON DISAGREEING on order (the defect); AFTER must show them AGREEING. Paste the shared explicit-order predicate and confirm in one sentence that both render paths call the same helper rather than duplicating the comparison. Confirm no sort call was added inside a renderer.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the flat-form output showing a `done` or `parked` item ABSENT without `--all` and PRESENT with it, plus the `[hidden; use --all]` notice line. Paste one item row from before and after the change and confirm byte equality of the `- [tree] path (status){gate}` shape. Quote the updated `render_board` docstring sentence describing the two forms.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the fixture-construction code and the `_run` helper showing `cwd` pointing at the fixture, not `REPO_ROOT`. Paste the four alias tests passing. THEN paste the de-flake proof: at least 3 full runs of `tests/test_next_ordering.py`, including at least one taken WHILE the live repository is being modified (state what you changed), all green. State the fixture's class and priority spread and why a single-class fixture would have been insufficient.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste both refusal tests unchanged and passing, with the added comment at each site. Paste the measured exit code for `-o bogus,priority` (UNPIPED: `cmd >/dev/null 2>&1; echo $?`) showing 2, and state in one sentence why no repository content can reach either assertion.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste BEFORE and AFTER CLI output on a fixture repo containing a `Blocks-Release: next` item whose priority should place it FIRST, plus a `planned` release record so `next` resolves. BEFORE must show it in a trailing `## release-blockers for <version> (<id6>)` section, outside the ordering; AFTER must show it in its correct ordered position with its per-item gate marker intact and NO trailing section. THEN paste the no-`-o` output showing the trailing section and its header byte-identical to today, since that is the default view. Confirm the same shared predicate from E-01 gates this branch (name it) rather than a second independent comparison.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test that reproduces the defect, AND proof it is falsifiable: run it against the PRE-FIX renderer (stash or revert E-01 locally) and paste the FAILURE, then paste the pass after. A test that has never been observed to fail is not evidence it detects the bug. Paste the default-view byte-equality diff (empty) for the no-`-o` non-colored board. Paste the hidden-class, release-blocker (E-06), and fixture-isolation assertions passing. Paste `tests/test_attention_compact.py` and `tests/test_attention_priority_blocker.py` passing UNMODIFIED (`git diff --name-only` must not list them), since they are the regression oracle for the default view (F-13). Paste the BARE `python3 -m pytest` summary line with before/after counts against the `5536 passed, 3 skipped, 2 xfailed` baseline, and report the measured runtime change for `tests/test_next_ordering.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY `agent_workflows/attention.py` and `tests/test_next_ordering.py`. Do NOT change `attention_contract.py`, `cli.py`, the sort engine (`sort_items`, `sort_items_with_notices`, `_order_key`), the colored `render_table` path (including its silent `done`/`parked` filter, see E-02), or the JSON output shape. Do NOT alter the stable `- [tree] path (status){gate}` row form. Do NOT change the default no-`-o` output bytes, in EITHER the class sections or the trailing release-blockers section. Do NOT edit `tests/test_attention_compact.py` or `tests/test_attention_priority_blocker.py`: they are this change's regression oracle (F-13), so a failure there means E-01 broke the default view and must be reported, not silenced. Do NOT edit executed plan `8ldrlx` or its review. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook, since a rejected commit can leave another party's paths staged. THIS IS A SHARED CHECKOUT with concurrent agents: `aw runs` before starting, and never revert or commit a file you did not change.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

DO NOT REPEAT THE FAILURE THIS PLAN EXISTS TO CORRECT. `8ldrlx` recorded a real defect as a finding, wrote no E-item for it, declared `Under-scope: none`, and was finalized as complete. If you discover a further defect while executing this plan, either fix it inside the fence or write it into `Deferred / out of scope` with a reason. A finding with no E-item and no deferral entry is an incomplete plan, however green the suite is.

THE ITEM THAT MATTERS MOST IS V-05's FALSIFIABILITY PASTE. The reproduction only proves anything if the class order and the requested order CONFLICT: a fixture where `high` priority happens to sit in the earlier class passes both before and after the fix, so it would certify nothing. Show the new test FAILING against the pre-fix renderer before showing it pass. If it cannot be made to fail, the fixture is wrong; stop and report rather than recording a green result.
