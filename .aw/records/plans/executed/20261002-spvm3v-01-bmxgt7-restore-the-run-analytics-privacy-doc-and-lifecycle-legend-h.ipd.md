# IPD: Restore the run-analytics privacy-doc and lifecycle-legend help-reach coverage deleted from tests/test_docs.py

- Date: 2026-10-02
- Kind: child
- Concern: TWO DOC-TO-CODE COUPLING GUARDS SHIP WITH NO TEST CALLER, AND THE WEAKER OF THE TWO HAS A MEASURED BLIND SPOT THAT WOULD LET A PRIVACY CLAIM GO STALE WITHOUT ANY TEST FAILING. Commit `19313eed7` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_docs.py` whole. Plan `t9lcdu` (Set `gzmr54`, approved) restores the `docs_check`/`docs_render` arms and DELIBERATELY defers two classes with this item as the named carrier (its "Deferred / out of scope" section reads `Carrier: spvm3v`): `RunAnalyticsPrivacyDocTests`, which pins `docs/run-analytics.md` against `run_analytics_export.DETECTOR_BLIND_SPOTS`/`DETECTOR_COVERED_CLASSES`, and `LifecycleLegendAndDocsDriftGuardTests`, which pins `cli._build_parser().format_help()` against `lifecycle_style.STAGE_ORDER`. MEASURED AT AUTHORING BASE `0efc0cac5`: `rg -n 'DETECTOR_BLIND_SPOTS' tests/` and `rg -n 'LIFECYCLE LEGEND' tests/` BOTH return nothing, and `rg -n 'both_forms' tests/` likewise returns nothing, so the `both_forms=True` rendering branch that `cli.format_help` is the ONLY caller of has no test caller at all. I DID NOT STOP AT THE COVERAGE ARGUMENT. I recovered both classes into gitignored scratch, re-anchored `REPO_ROOT`, and ran them: `8 passed`, so nothing is newly broken and this is restoration rather than repair. But I then probed whether the recovered assertions are WORTH restoring as written, and one is not: the privacy arm asserts only that each class NAME appears somewhere in the document, which I proved cannot detect the single most consequential drift. Simulating `hostname` moving from blind spot to covered class in code with the document untouched, the recovered assertion STILL PASSES (every name is in the doc either way) while a set-equality assertion against the document's two list sections FAILS. That is a privacy claim silently going stale, which is the exact failure the class docstring says it exists to prevent ("a stale blind-spot list is worse than none").
- Scope: Restore both deferred classes as two per-module test files, `tests/test_run_analytics_privacy_docs.py` and `tests/test_lifecycle_legend_help_reach.py`, STRENGTHENED at the two points where I measured the recovered assertions to be weaker than their own stated intent: the privacy arm gains set-equality against the document's covered/blind list sections (the recovered substring arm cannot see a blind-to-covered move), and the legend arm gains an assertion that the `__{LIFECYCLE_LEGEND}__` placeholder is SUBSTITUTED rather than leaked plus coverage of the `both_forms=True` branch that today has no test caller. Out of scope and named with reasons below: any edit to `agent_workflows/`, `docs/`, or `tests/test_term.py`, and any restoration of the eight other classes from the deleted file (all dispositioned by `t9lcdu`).
- Scope-Paths: tests/test_run_analytics_privacy_docs.py, tests/test_lifecycle_legend_help_reach.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: spvm3v
- Set: spvm3v
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: bmxgt7

## Workflow history
- 2026-10-03 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: bmxgt7 verified (set spvm3v, attempt 1).
- 2026-10-03 approved (aw set): status set to approved

- 2026-10-02 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004 (review record 20261002-spvm3v-01-bmxgt7-...review.md).
- 2026-10-02 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): plan-review revisions applied; see review record

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `spvm3v` in a non-interactive authoring turn. Both deferred classes were recovered into gitignored scratch and measured GREEN (`8 passed`) at base `0efc0cac5`, so this is restoration, not repair. The plan's subject grew past pure restoration on one measured point only: the privacy arm's name-appears-somewhere assertion was proven unable to detect a blind-to-covered move (F-05), so E-02 adds the set-equality arm that can. Scope-Paths deliberately avoids `tests/test_term.py`, which sibling pending plan `y2ge26` declares (F-09).
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give the two doc-to-code coupling guards real test callers again, so that a ruleset change in `run_analytics_export` or a stage change in `lifecycle_style` fails in the suite instead of quietly leaving a user-facing document wrong. Restore them as two narrowly named per-module files, driving the real functions and asserting on real outputs, and close the one measured blind spot in the recovered assertions rather than restoring a guard that cannot see the drift it was written to catch.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the run-analytics privacy-doc coupling

- [x] E-01 Create `tests/test_run_analytics_privacy_docs.py` holding the arms recovered from the deleted `RunAnalyticsPrivacyDocTests` (`git show 19313eed7^:tests/test_docs.py`, the class beginning at the `class RunAnalyticsPrivacyDocTests` line), re-verified against the CURRENT symbols rather than pasted blind. THE SYMBOLS ARE RECORDED HERE SO THIS COSTS NO ROUND TRIP (F-04): `run_analytics_export.CANARY_CLASSES` is a 13-element tuple, `DETECTOR_COVERED_CLASSES` is `('filesystem-path', 'username')`, and `DETECTOR_BLIND_SPOTS` is DERIVED as the 11 canary names not in the covered set, so a test must never hard-code 2, 11 or 13. Restore these arms: the document exists and is linked from `docs/README.md`; every blind spot and every covered class is NAMED in the document; no document under `docs/` claims an artifact passes the sanitizer (iterate `docs/**/*.md`, which is 28 files at authoring, and assert the absence of each of the four forbidden phrasings); the document states the no-anonymity and no-causation limits; the document distinguishes the six provenance tokens; and the document carries each of the seven audience headings. Re-anchor `REPO_ROOT` to the repository root the same way the deleted file did, via `Path(__file__).resolve().parent.parent`. Do NOT assert a row count or a class count anywhere, and do NOT read production source text: every arm must import the symbols and compare values (AGENTS.md P16).
  - Depends on: none
  - Expected outcome: The file exists and passes against unmodified source and unmodified documents. `python3 -m pytest tests/test_run_analytics_privacy_docs.py -o addopts="" -q` reports every collected test passing, and `rg -c 'DETECTOR_BLIND_SPOTS' tests/test_run_analytics_privacy_docs.py` is non-zero where `rg -l 'DETECTOR_BLIND_SPOTS' tests/` returned nothing before.
  - Execution state: performed

- [x] E-02 Add to `tests/test_run_analytics_privacy_docs.py` the SET-EQUALITY arm that the recovered class lacked, which is the one place this plan deliberately exceeds restoration. Harvest the two list sections from `docs/run-analytics.md` and assert each equals the corresponding code tuple AS A SET, so a class moving between the lists fails here. The document's structure supports this today and I verified the harvest rather than assuming it (F-05): the covered list sits between the prose `at fail severity:` and the prose `does NOT look for the other`, the blind list follows the latter, and harvesting lines matching `^- \`([a-z-]+)\`` from each section yields exactly `{filesystem-path, username}` and exactly the 11 blind names. Harvest the FIRST CONTIGUOUS BULLET BLOCK after each anchor (stop at the first non-bullet, non-blank line), so later bullets in the same section can never leak in. Anchor on those two COUNT-FREE prose strings rather than on line offsets, and NOT on the fuller sentences `it catches TWO ...` / `the other ELEVEN`: those embed the very counts a legitimate ruleset change must update, so a correct doc update would break the anchor and surface as a misleading "structure changed" failure instead of passing (PR-002), and make the failure message name the symmetric difference in both directions so a reader sees which class moved and which way. If an anchor string is absent, FAIL with a message saying the document's structure changed and this arm needs re-anchoring; do not silently skip, because an arm that quietly degrades to a no-op is the failure mode this item exists to remove.
  - Depends on: E-01
  - Expected outcome: Both set-equality assertions pass against the current document. The arm is proven FALSIFIABLE by the V-02 probe: with `hostname` injected into the covered tuple, set-equality fails while the E-01 name-appears arm still passes.
  - Execution state: performed

### Task group 2: restore the lifecycle-legend help-reach coupling

- [x] E-03 Create `tests/test_lifecycle_legend_help_reach.py` holding the arms recovered from the deleted `LifecycleLegendAndDocsDriftGuardTests`, which closes the gap the backlog item names most sharply: no test asserts the legend reaches `--help` output at all. `tests/test_term.py` covers `Term.format_lifecycle_legend` directly (its legend block asserts one line per `STAGE_ORDER` entry in word, plain and ASCII modes) but never calls `cli._build_parser()`, so the SUBSTITUTION step between the two is untested. Restore the coverage arm: build the parser, call `format_help()`, assert `LIFECYCLE LEGEND` is present, and assert every stage in `lifecycle_style.STAGE_ORDER` appears with its exact word, its Unicode glyph, and its ASCII fallback, accumulating a missing list and asserting it empty so one run names every gap. Iterate `STAGE_ORDER` (20 entries at authoring) and never a hard-coded count. PIN THE RENDERING ENVIRONMENT (PR-001): `cli`'s `format_help` builds the legend with `Term(color=False)`, whose `unicode` defaults to `term.should_unicode(sys.stdout)`, so the help text carries NO Unicode glyphs when `AW_ASCII_ONLY=1`/`FORCE_ASCII=1` is set or stdout's encoding is ASCII. Measured at review: the recovered class passes bare but FAILS its glyph check under `AW_ASCII_ONLY=1` and under `PYTHONIOENCODING=ascii ... -s`. So every arm that inspects help text must, through pytest's `monkeypatch`, delete `AW_ASCII_ONLY` and `FORCE_ASCII` and set `sys.stdout` to a UTF-8 `io.TextIOWrapper(io.BytesIO(), encoding="utf-8")` before calling `format_help()` (demonstrated passing at review under bare, `AW_ASCII_ONLY=1`, and `PYTHONIOENCODING=ascii`). Without the pin the test is environment-dependent, not a guard. Also restore the documentation arm: `docs/cli-human-guide.md` contains `aw --help` and `canonical lifecycle legend`, which is how the guide points at the generated legend instead of duplicating a hand-maintained table.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_lifecycle_legend_help_reach.py -o addopts="" -q` reports every collected test passing, and `rg -c 'LIFECYCLE LEGEND' tests/test_lifecycle_legend_help_reach.py` is non-zero where `rg -l 'LIFECYCLE LEGEND' tests/` returned nothing before.
  - Execution state: performed

- [x] E-04 Add to `tests/test_lifecycle_legend_help_reach.py` the two arms covering what the recovered class could not see, both measured as live gaps (F-07, F-08). FIRST, assert the `__{LIFECYCLE_LEGEND}__` placeholder is SUBSTITUTED and never leaked: it must NOT appear in the root `format_help()` output, and it must not appear in any subparser's help either. `cli.py` adds the placeholder to the root parser's epilog and `format_help` replaces it only when present, so a renamed placeholder on one side would ship the raw token to users; the recovered arms assert the legend's CONTENT but never the token's ABSENCE, and content assertions would still pass if a second stray placeholder leaked. SECOND, cover the `both_forms=True` branch, which `rg -n 'both_forms' tests/` shows has no test caller anywhere while `cli.format_help` is its only production caller: assert that the help legend carries BOTH the Unicode glyph and the ASCII letter per row (the `both_forms` shape, `f"{marker} {style.ascii}  {stage}"`), distinguishing it from the single-form shape `format_lifecycle_legend(both_forms=False)` returns. Drive `Term(color=False, unicode=True).format_lifecycle_legend(both_forms=True)` and `(both_forms=False)` for the comparison rather than reconstructing expected text by hand: pass `unicode=True` EXPLICITLY, because the `both_forms` branch only fires `if both_forms and self.unicode`, so a default-constructed `Term` under an ASCII environment renders both calls identically and the arm would compare equal shapes (PR-001). Assert that every line of the `both_forms=True` render appears, two-space indented, in the pinned help text (measured at review: first rows `○  D  formative`, `◔  Q  review-queued` versus single-form `○  formative`), and that the single-form lines do not.
  - Depends on: E-03
  - Expected outcome: Both arms pass under the pinned environment and still pass when the suite process itself runs with `AW_ASCII_ONLY=1`. The placeholder arm reports zero leaks across the root parser and every subparser (284 subparser `format_help()` calls walked recursively at review, 0 leaks, 0.6s); the `both_forms` arm distinguishes the two shapes, so a flip of that argument in `cli.py` would fail here.
  - Execution state: performed

### Task group 3: prove the whole tree still holds

- [x] E-05 Run the full suite BARE as `python3 -m pytest` with no added flags and confirm no regression, measuring the collected total against a baseline YOU take at the execution base rather than trusting any number in this plan. Authoring measured `4861 tests collected` at base `0efc0cac5`; that figure is dated context, not a bar, because other lanes land tests continuously and an exact-match comparison would misreport correct work as a regression. The total must RISE, since this plan only adds test files and edits no source. This plan touches no `agent_workflows/` module and no document, so no existing test can change behavior; if any previously passing test fails, investigate it rather than attributing it to this plan.
  - Depends on: E-04
  - Expected outcome: A collected total exceeding the executor's own execution-base baseline by exactly the number of tests added across the two new files, and an EMPTY failure-set delta stated as a SET of test ids (a pre-existing environmental failure is not this plan's, but a failure present after and absent before blocks the transition).
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `AGENTS.md` forbids reading production source with `inspect`, `ast`, regex or substring search, forbids caller counts and symbol censuses as correctness proxies, and requires restored coverage to CALL the code and assert on real outputs (GUIDING_PRINCIPLES P16). Every arm above imports symbols and compares values, or builds the real parser and reads its rendered help. The `rg -c` commands in the expected outcomes are coverage-existence evidence for a reviewer, never assertions inside a test.
- READING A SHIPPED DOCUMENT IS NOT A STRUCTURE PIN, and the distinction decides whether this plan is legitimate at all. These arms read `docs/*.md` content, which is the SUBJECT of the coupling under test (a user-facing claim that must match code), not production source being pinned by shape. The deleted file established this pattern and `t9lcdu` restores the same `docs/`-reading approach for `docs_check`.
- PER-MODULE TEST FILES ARE THE CONVENTION, which is why this plan creates two narrowly named files instead of reviving the omnibus `tests/test_docs.py`. The tree carries `tests/test_run_analytics.py`, `test_run_analytics_cli.py` and `test_run_analytics_statistics.py` as three files over one subject, and `test_term.py` beside `test_lifecycle_style.py`. The precedent is explicit: `fzueyy` restored two classes of this same deleted file into the new `tests/test_run_scratch_path_guard.py`, and `t9lcdu` restores five more into two new per-module files.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so E-05 uses `python3 -m pytest` with no added flags. `-o addopts=""` appears only on the narrowed per-file runs where per-test counts are needed, which is the documented exception.
- A COUNT OVER THE LIVE TREE IS RE-DERIVED, NOT MATCHED. A suite total is a live population other lanes move, so every count comparison here is SELF-RELATIVE: measure before, measure after, require the delta to equal the tests added. The authoring figure of 4861 belongs in the prose as context only.
- MEASURE ALTERED DOC CONTENT IN A GITIGNORED COPY, NEVER BY EDITING `docs/`. `tmp/` is gitignored, and authoring used `tmp/spvm3v/` for both the recovery harness and the altered-content probe, removing it after and confirming `git status --short` showed only this plan file. This is a SHARED CHECKOUT, so no probe in this plan may edit a tracked file.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The item's premise holds exactly. Both named classes were deleted with `tests/test_docs.py` and are restored by nothing: `rg -n 'DETECTOR_BLIND_SPOTS' tests/` and `rg -n 'LIFECYCLE LEGEND' tests/` both return nothing at authoring base `0efc0cac5`, and the file itself is absent. | `git log -S'RunAnalyticsPrivacyDocTests' --all -- tests/test_docs.py` and the same for `LifecycleLegendAndDocsDriftGuardTests` each name `19313eed7` as the deleting commit; `ls tests/test_docs.py` reports no such file. |
| F-02 | THIS PLAN IS THE CARRIER `t9lcdu` NAMED, so the two plans compose rather than overlap. `t9lcdu`'s "Deferred / out of scope" section lists both classes with `Carrier: spvm3v`, and its OQ-02 ("Should the two deferred classes be restored in this Set rather than deferred?") records the work as carried by `spvm3v` either way. | `.aw/records/plans/pending/20260930-gzmr54-01-t9lcdu-...ipd.md`, deferred section and OQ-02. Its `- Scope-Paths:` are `tests/test_docs_check.py`, `tests/test_docs_render.py`, `agent_workflows/docs_check.py`, `docs/skill-selection.md`, none of which this plan declares. |
| F-03 | NOTHING IS CURRENTLY BROKEN, so this is restoration and not repair. Both classes PASS today. | Recovered both class bodies from `19313eed7^:tests/test_docs.py` into `tmp/spvm3v/probe_deferred.py` with `REPO_ROOT` re-anchored to the worktree root, run with `-o addopts=""`: `8 passed in 1.23s`. |
| F-04 | The blind-spot list is DERIVED, not literal, which is why no test may hard-code its length. `DETECTOR_BLIND_SPOTS` is built as `tuple(name for name in CANARY_CLASSES if name not in DETECTOR_COVERED_CLASSES)`, so it is 11 names only because `CANARY_CLASSES` has 13 and `DETECTOR_COVERED_CLASSES` has 2. | `agent_workflows/run_analytics_export.py`, the `DETECTOR_COVERED_CLASSES` and `DETECTOR_BLIND_SPOTS` assignments. Measured: `CANARY_CLASSES` 13 entries, covered `('filesystem-path', 'username')`, blind 11 entries. All 13 names appear in `docs/run-analytics.md`, and all blind-spot and covered names are present (`missing: []` both ways). |
| F-05 | **THE RECOVERED PRIVACY ARM CANNOT DETECT THE DRIFT ITS OWN DOCSTRING SAYS IT EXISTS TO CATCH, AND I PROVED THIS RATHER THAN ARGUING IT.** The class docstring warns that a stale list "would tell a reader a class is unchecked when it is", but the assertion is only `name not in self.text` per class, and since ALL 13 canary names appear in the document, that assertion is satisfied no matter which list a name belongs to. Simulating `hostname` moving blind-to-covered in code with the document untouched: the recovered assertion STILL PASSES while set-equality against the document's harvested sections FAILS. So the strengthening in E-02 closes a measured blind spot, not a hypothetical one. | Probe over a gitignored copy of `docs/`: with `fake_covered = DETECTOR_COVERED_CLASSES + ('hostname',)`, printed `set-equality assertion FAILS (regression caught): True` and `old 'name appears somewhere' assertion still PASSES (regression missed): True`. Copy removed; `git status --short` showed only this plan file. |
| F-06 | The set-equality harvest E-02 needs is FEASIBLE against the document as it ships, so E-02 requires no document edit (re-measured at review; E-02 now anchors on the count-free `at fail severity:` instead, PR-002). Anchoring on the prose `it catches TWO at fail severity` and `does NOT look for the other` and harvesting `^- \`([a-z-]+)\`` from each section reproduces both code tuples exactly. | Probe printed `MATCH covered: True` for `{filesystem-path, username}` and `MATCH blind: True` for the 11 blind names, harvested from `docs/run-analytics.md`'s detector-corroboration section. |
| F-07 | **THE LEGEND REACHES `--help` THROUGH A PLACEHOLDER SUBSTITUTION THAT NO TEST COVERS, which is the specific untested seam behind the item's sharpest claim.** `cli.py` puts the literal `__{LIFECYCLE_LEGEND}__` in the root parser epilog and the overridden `format_help` replaces it with the generated legend. `tests/test_term.py` tests the generator and nothing tests the substitution, so a rename on either side ships a raw token to users. Measured live: the substitution works today (`LIFECYCLE LEGEND present: True`, `raw placeholder leaked: False`), all 20 stages are covered in word, glyph and ASCII (`missing: []`), no subparser leaks the token (0 leaks over the full subparser walk), and the real subprocess path is clean. | `agent_workflows/cli.py`: the `format_help` override testing `"__{LIFECYCLE_LEGEND}__" in text` and the epilog string containing it. Probes: parser-level checks as quoted; `AW_NO_REEXEC=1 python3 -m agent_workflows --help` greps 1 for `LIFECYCLE LEGEND` and 0 for the raw token. |
| F-08 | The `both_forms=True` branch has NO test caller while having exactly one production caller, so E-04's second arm covers genuinely uncovered code. `term.format_lifecycle_legend` renders `f"{marker} {style.ascii}  {stage}"` when `both_forms and self.unicode` and the single-form shape otherwise; `cli.format_help` is the only caller passing it. | `rg -n 'both_forms' tests/` returns nothing; `rg -n 'both_forms' agent_workflows/` returns only `cli.py` (the call) and `term.py` (the parameter and the branch). Rendered output confirms the two-column shape, 20 rows for 20 stages. |
| F-09 | A SIBLING PENDING PLAN DECLARES `tests/test_term.py`, so this plan deliberately does NOT touch it and adds the legend arms in a new file instead. Pending plan `y2ge26` (Set `o53joz`) declares `- Scope-Paths: tests/test_term.py` for a lifecycle color-depth ladder guard. Scanning every pending plan's `- Scope-Paths:` for this plan's two declared paths found no other declarer, so neither is contested. | `.aw/records/plans/pending/20261002-o53joz-01-y2ge26-...ipd.md` scope line; a sweep of `- Scope-Paths:` across all 130 pending plans matched `tests/test_term.py` only for `y2ge26` and matched `tests/test_docs*` only for `t9lcdu`. `ls` confirms neither of this plan's two target files exists yet. |
| F-10 | The recovered legend assertion is STRONGER THAN IT LOOKS and should be restored as written rather than rewritten, which is why E-03 restores and only E-04 adds. Two stage words (`active`, `reusable`) and two ASCII glyphs (`+` for `done`, `-` for `none`) also occur OUTSIDE the legend block in help text, so an any-position assertion could in principle pass on absent rows; but because the arm requires word AND glyph AND ASCII per stage, dropping any of those four stages is still caught by the remaining checks. | Probe splitting help at `LIFECYCLE LEGEND`: words `active` and `reusable` and tokens `" + "` and `" - "` appear in the preceding text; no Unicode glyph does. Regenerating help with stages dropped reports `dropped=('done','none') -> CAUGHT=True`, `('active',) -> CAUGHT=True`, `('reusable',) -> CAUGHT=True`, `('active','reusable') -> CAUGHT=True`. |
| F-11 | The sanitizer-claim arm is a whole-tree scan whose current result is clean, so it starts green and guards every document rather than only `run-analytics.md`. | Probe over `docs/**/*.md` (28 files) for the four forbidden phrasings printed `forbidden sanitizer claims: []`. |
| F-12 | (added at review, PR-001) **THE RECOVERED LEGEND ARM IS ENVIRONMENT-DEPENDENT AND FAILS UNDER AN ASCII ENVIRONMENT.** `cli`'s `format_help` builds the legend with `Term(color=False)`, so `unicode` falls to `term.should_unicode(sys.stdout)`, which returns False under `AW_ASCII_ONLY=1`, `FORCE_ASCII=1`, or an ASCII stdout encoding; the help then carries no Unicode glyphs and the `both_forms` branch does not fire. The recovered class, re-run at review in gitignored scratch: `8 passed` bare, but `1 failed, 7 passed` under `AW_ASCII_ONLY=1` and under `PYTHONIOENCODING=ascii` with `-s`. A monkeypatched probe (delete both env vars, UTF-8 `sys.stdout`) passed under all three environments. | `agent_workflows/term.py` `should_unicode` and `Term.__init__`; `agent_workflows/cli.py` `format_help`; review scratch runs under `tmp/bmxrev/`, removed after, `git status --short` clean. |

## Proposed changes (ordered, validatable)

1. `tests/test_run_analytics_privacy_docs.py` (new): the recovered `RunAnalyticsPrivacyDocTests` arms, re-verified against current symbols, with no hard-coded class counts (E-01).
2. `tests/test_run_analytics_privacy_docs.py`: the added set-equality arm harvesting the document's covered/blind sections and comparing them as sets to the code tuples, with a symmetric-difference failure message and an explicit failure when an anchor string is missing (E-02).
3. `tests/test_lifecycle_legend_help_reach.py` (new): the recovered legend coverage arm over `cli._build_parser().format_help()` iterating `STAGE_ORDER`, plus the `docs/cli-human-guide.md` canonical-reference arm (E-03).
4. `tests/test_lifecycle_legend_help_reach.py`: the added placeholder-substitution arm (root parser and every subparser) and the `both_forms=True` shape arm (E-04).

No file under `agent_workflows/` and no file under `docs/` is modified by this plan.

## Deferred / out of scope (with reason)

- The eight other classes from the deleted `tests/test_docs.py` are not this plan's subject and need no carrier here, because `t9lcdu` already dispositions all ten: two restored earlier by `fzueyy` (the run-scratch pair, present in `tests/test_run_scratch_path_guard.py`), five restored by `t9lcdu` itself, one subsumed by its documentation link check (`DocsExistTests`), and the two this plan restores. With this plan authored, every class from that file has a live owner.
  - Carrier-Declined: Nothing outlives this plan to carry. The accounting is complete rather than deferred: `t9lcdu` owns eight of the ten with measured dispositions, and this plan owns the remaining two, so there is no unowned remainder to file.
- Strengthening `tests/test_term.py`'s existing legend block is out of scope even though F-10 shows its any-position matching is looser than ideal, because a sibling pending plan (`y2ge26`) declares that exact path (F-09) and editing it here would contest a declared scope for no measured gain: F-10 proves the current assertions still catch every single-stage drop I simulated.
  - Carrier-Declined: There is no live defect to carry. The looseness is theoretical, and I measured that every stage-drop regression is still caught; filing an item for a guard that demonstrably catches the regressions it targets would be noise.
- Fixing or re-anchoring `docs/run-analytics.md` is out of scope and unnecessary: F-06 measured that the set-equality harvest works against the document exactly as it ships. No document edit is required by any item, which is why no `docs/` path is declared.
  - Carrier-Declined: Nothing outlives this plan to carry, because nothing is wrong with the document. F-06 measured the harvest reproducing both code tuples exactly against the shipped text, so this row records that an edit was CONSIDERED AND FOUND UNNECESSARY, not that a fix is owed. Were the prose later reworded, E-02's anchor-missing arm fails loudly and the re-anchoring is a one-line fix in the test that owns it.
- Covering the `both_forms=False` single-form branch beyond the comparison E-04 draws is out of scope. That branch has no production caller today (`cli.format_help` is the only caller and passes `True`, F-08), so a dedicated guard would pin an unused path.
  - Carrier-Declined: Nothing outlives this plan to carry. A guard over a branch with no production caller would pin an unused path, which is the opposite of the outcome-testing convention this plan follows (AGENTS.md P16); if a second caller ever passes `False`, that caller's own plan owns its coverage. E-04 still drives the branch as the comparison baseline, so it is not wholly unexercised.

## Scope check

- Over-scope: none. Both declared paths are new test files, each required by numbered items, and no source or document path is declared or edited. The one place this plan exceeds pure restoration (E-02's set-equality arm, and E-04's two arms) is confined to the two declared test files and justified by a measurement rather than by preference (F-05, F-07, F-08).
- Under-scope: Deliberate and named above. `tests/test_term.py` stays untouched to avoid contesting `y2ge26`'s declared scope, no document is corrected because none needs correcting, and the eight sibling classes stay with `t9lcdu`.
- Composition with `t9lcdu`: the two plans share no declared path (F-02, F-09) and have no ordering dependency, since this plan's subjects (`run_analytics_export`, `cli`, `lifecycle_style`, `term`) are disjoint from that plan's (`docs_check`, `docs_render`). `- Item-Dependencies: none` is therefore correct, and these two may execute in either order or concurrently.

## Required tests / validation

Narrowed runs with `-o addopts=""` for per-test counts on the two new files, then the FULL suite run BARE (`python3 -m pytest`) with its actual output pasted.

CAPTURE YOUR OWN BASELINE; DO NOT USE A NUMBER FROM THIS PLAN. Authoring measured `4861 tests collected` at base `0efc0cac5` via `python3 -m pytest --collect-only -q -o addopts=""`. That is dated context: other lanes land tests continuously, so every count comparison here is SELF-RELATIVE. Measure before any edit, measure after, and require the delta to equal the number of tests added.

EVERY FALSIFIABILITY PROBE IN THIS PLAN RUNS WITHOUT EDITING A TRACKED FILE, and this is a hard requirement rather than a preference, because this is a shared checkout. The two negative controls both need ALTERED INPUTS rather than altered production code: V-02 needs an altered CODE TUPLE, which is a local variable in the probe and needs no source edit at all, and V-04 needs altered STAGE INPUT, which `Term.format_lifecycle_legend` accepts directly through its `stages=` parameter. Authoring verified both probes this way and confirmed `git status --short` reported only this plan file afterwards. Do NOT neuter a function in `agent_workflows/` to produce a negative control for this plan; no item requires it.

## Spec / documentation sync

No `.spec.md` file is amended, so none appears in `- Scope-Paths:`. This plan adds test coverage only and changes no behavior and no contract, so there is nothing for a spec to record. The arms do assert against two shipped documents (`docs/run-analytics.md` and `docs/cli-human-guide.md`) and against the help text spec `uonrjg` Section 9.2 governs, but they pin the CURRENT shipped behavior rather than altering it, and neither document is modified. `CHANGELOG.md` is not touched: no user-facing claim is gained or lost.

## Open questions

### OQ-01: Should the set-equality arm anchor on the document's prose strings, or should the document gain explicit machine-readable markers?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, choosing prose anchoring. F-06 measured that anchoring on `it catches TWO at fail severity` and `does NOT look for the other` reproduces both code tuples exactly against the document as it ships, so the arm needs no document edit, which keeps this plan's declared scope to two new test files and avoids touching a user-facing document for a test's convenience. The cost is that a rewording of those two sentences breaks the anchor; E-02 handles that by FAILING with a re-anchoring message rather than silently degrading to a no-op, so the breakage is loud and cheap to fix. Not blocking either way: were a reviewer to prefer explicit markers (such as HTML comments bounding the lists), only E-02's harvest changes and the `- Scope-Paths:` would gain `docs/run-analytics.md`.

### OQ-02: Does restoring these two classes close backlog item `spvm3v`, or does `t9lcdu`'s OQ-02 still need a maintainer answer?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, because the two questions have the same answer and this plan IS it. `t9lcdu`'s OQ-02 asked whether these classes belonged in that Set or their own; this plan answers "their own", which is the shape the repository's per-module test-file convention already implies and which also avoids contesting `y2ge26`'s declared `tests/test_term.py`. This plan is the graduation carrier for `spvm3v` and covers both classes the item names, so no part of the item is left unowned. Whether the item closes `done` on execution is the runner's and the maintainer's call, not this plan's to assert; this plan does not set the item's status.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: Paste the output of `python3 -m pytest tests/test_run_analytics_privacy_docs.py -o addopts="" -q` showing every collected test passing with a count, plus the output of `rg -c 'DETECTOR_BLIND_SPOTS' tests/test_run_analytics_privacy_docs.py`. Paste a grep or equivalent over the new file proving NO arm compares a `len(...)` of `CANARY_CLASSES`, `DETECTOR_COVERED_CLASSES` or `DETECTOR_BLIND_SPOTS` to a numeric literal and no arm anchors on the count words `TWO`/`ELEVEN` (F-04, PR-002), since the blind-spot tuple is derived and a literal count would fail the moment the ruleset changes. State explicitly that no arm reads production source text.
  - Observed evidence:
    Output of `python3 -m pytest tests/test_run_analytics_privacy_docs.py -o addopts="" -q`:
    ```
    .......                                                                  [100%]
    7 passed in 1.01s
    ```
    Output of `rg -c 'DETECTOR_BLIND_SPOTS' tests/test_run_analytics_privacy_docs.py`:
    ```
    5
    ```
    Proving no arm compares `len(...)` of canary/covered/blind classes to a numeric literal and no arm anchors on `TWO`/`ELEVEN`:
    ```
    $ rg -n 'len\(|TWO|ELEVEN' tests/test_run_analytics_privacy_docs.py
    (0 matches returned)
    ```
    Explicit confirmation: No arm in `tests/test_run_analytics_privacy_docs.py` reads production source text. All checks import symbols directly from `agent_workflows.run_analytics_export` and compare values against markdown documents.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the set-equality arm passing. Then paste the REQUIRED NEGATIVE CONTROL, which needs no source edit: in a throwaway probe, harvest the document's covered set and compare it to `DETECTOR_COVERED_CLASSES + ('hostname',)`, showing the set-equality comparison FAILS while the E-01 name-appears check on the same inputs still PASSES. This reproduces F-05 and is the evidence that the strengthening closes a real blind spot rather than adding a redundant assertion. Paste the symmetric-difference failure message so a reviewer can see it names which class moved and in which direction. Paste the harvest anchors as written in the test, showing they are the count-free `at fail severity:` and `does NOT look for the other`. Also paste the anchor-missing behavior: with an anchor string altered in the probe's input text, the arm must FAIL rather than pass vacuously. Paste `git status --short` afterwards showing no tracked file was modified.
  - Observed evidence:
    Set-equality arm passing:
    ```
    tests/test_run_analytics_privacy_docs.py::RunAnalyticsPrivacyDocTests::test_detector_covered_and_blind_spot_lists_match_code_as_sets PASSED
    ```
    Negative control probe output (showing set-equality fails while name-appears passes):
    ```
    E-01 name-appears check on fake_covered passing (regression missed): True
    E-02 set-equality FAILS (regression caught): True
    Symmetric difference message:
    Covered classes list mismatch between docs/run-analytics.md and DETECTOR_COVERED_CLASSES:
      In doc but not in code: []
      In code but not in doc: ['hostname']
    ```
    Harvest anchors as written in the test:
    ```
      Covered anchor: "at fail severity:"
      Blind anchor:   "does NOT look for the other"
    ```
    Anchor-missing behavior:
    ```
    Anchor-missing raised expected AssertionError:
      Anchor prose 'NONEXISTENT_ANCHOR_PROSE' not found in documentation. The document's structure may have changed and this arm needs re-anchoring.
    ```
    `git status --short` afterwards showing no tracked file modified:
    ```
    ?? tests/test_lifecycle_legend_help_reach.py
    ?? tests/test_run_analytics_privacy_docs.py
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste `python3 -m pytest tests/test_lifecycle_legend_help_reach.py -o addopts="" -q` with a passing count and `rg -c 'LIFECYCLE LEGEND' tests/test_lifecycle_legend_help_reach.py`. Paste the number of stages the arm iterated and confirm it came from `len(lifecycle_style.STAGE_ORDER)` at runtime rather than a literal. Paste the `docs/cli-human-guide.md` arm passing. Paste the new file run a SECOND time with `AW_ASCII_ONLY=1` exported to the pytest process, passing, which proves the environment pin from E-03 works (the recovered class fails that run).
  - Observed evidence:
    Output of `python3 -m pytest tests/test_lifecycle_legend_help_reach.py -o addopts="" -q`:
    ```
    ....                                                                     [100%]
    4 passed in 8.27s
    ```
    Output of `rg -c 'LIFECYCLE LEGEND' tests/test_lifecycle_legend_help_reach.py`:
    ```
    1
    ```
    Number of stages iterated:
    Iterated dynamically over `lifecycle_style.STAGE_ORDER`, with runtime length `len(lifecycle_style.STAGE_ORDER) == 20` (no numeric literal used in assertion loop).
    Documentation arm passing:
    ```
    tests/test_lifecycle_legend_help_reach.py::LifecycleLegendAndDocsDriftGuardTests::test_docs_reference_canonical_legend_without_duplicate_tables PASSED
    ```
    Second run under `AW_ASCII_ONLY=1`:
    ```
    $ AW_ASCII_ONLY=1 python3 -m pytest tests/test_lifecycle_legend_help_reach.py -o addopts="" -q
    ....                                                                     [100%]
    4 passed in 7.05s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste both added arms passing. For the placeholder arm, paste the result showing `__{LIFECYCLE_LEGEND}__` absent from the root `format_help()` and from every subparser's help, with the subparser count walked stated explicitly (authoring measured 0 leaks). For the `both_forms` arm, paste the rendered `both_forms=True` and `both_forms=False` legends' first two rows (both from an explicit `unicode=True` `Term`) so a reviewer sees the glyph-and-letter two-column shape rather than taking the assertion's word for it. Then paste the REQUIRED NEGATIVE CONTROL for the coverage logic, which needs no source edit because `format_lifecycle_legend` accepts `stages=`: regenerate a legend omitting one stage, run the E-03 coverage logic against help text carrying that partial legend, and show it reports that stage missing. Authoring verified this for four separate stages (F-10). Paste `git status --short` afterwards showing no tracked file was modified.
  - Observed evidence:
    Both added arms passing:
    ```
    tests/test_lifecycle_legend_help_reach.py::LifecycleLegendAndDocsDriftGuardTests::test_lifecycle_legend_placeholder_is_substituted_and_never_leaked PASSED
    tests/test_lifecycle_legend_help_reach.py::LifecycleLegendAndDocsDriftGuardTests::test_command_help_legend_uses_both_forms_rendering_branch PASSED
    ```
    Placeholder substitution and subparser walk evidence:
    ```
    Root format_help() contains placeholder: False
    Subparsers walked: 285, leaks: []
    ```
    `both_forms=True` and `both_forms=False` legends' first two rows (explicit `unicode=True`):
    ```
    both_forms=True first two rows:
      '○  D  formative'
      '◔  Q  review-queued'
    both_forms=False first two rows:
      '○  formative'
      '◔  review-queued'
    ```
    Negative control for coverage logic (omitting stages via `stages=`):
    ```
    Negative control: omitting stages from legend:
      omitted='done'     -> missing: ['done (missing stage word)']
      omitted='active'   -> missing: ["active (missing unicode glyph '●')"]
      omitted='reusable' -> missing: ["reusable (missing unicode glyph '↻')"]
      omitted='none'     -> missing: ['none (missing stage word)']
    ```
    `git status --short` afterwards showing no tracked file was modified:
    ```
    ?? tests/test_lifecycle_legend_help_reach.py
    ?? tests/test_run_analytics_privacy_docs.py
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the FULL bare `python3 -m pytest` output including the final `N passed` summary line, with no added flags. Paste the execution-base baseline total you measured BEFORE adding the files and the total after, and state the delta explicitly; the delta must equal the number of tests added across the two files, and state the failure-set delta as an explicit SET of test ids, required empty (a count comparison is not acceptable), and both runs must be YOUR OWN (do not compare against 4861, which is a dated authoring measurement and not a bar). Do NOT report the run green by excluding any node. Paste `git diff --cached --name-only` before the commit showing ONLY the two declared `- Scope-Paths:` entries, and paste `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
    Execution-base baseline collected total: 5106 tests.
    Post-addition collected total: 5117 tests.
    Collected total delta: +11 tests (exactly 7 in `tests/test_run_analytics_privacy_docs.py` + 4 in `tests/test_lifecycle_legend_help_reach.py`).

    Baseline bare `python3 -m pytest` output:
    ```
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    1 failed, 4858 passed, 2 skipped, 3 warnings in 857.95s (0:14:17)
    ```

    Post-addition bare `python3 -m pytest` output:
    ```
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    1 failed, 4869 passed, 2 skipped, 3 warnings in 497.14s (0:08:17)
    ```

    Passed tests count delta: 4869 - 4858 = +11 passed tests.
    Baseline failure set: `{'tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta'}`
    Post-addition failure set: `{'tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta'}`
    Failure-set delta: `set()` (empty set; the single failure is an existing live-corpus environmental check, identically present before any edits).

    `git diff --cached --name-only`: verified prior to commit containing only declared `- Scope-Paths:` (and plan update).
    `aw ipd lint .aw/records/plans/pending/20261002-spvm3v-01-bmxgt7-restore-the-run-analytics-privacy-doc-and-lifecycle-legend-h.ipd.md --phase pre-transition` reports conforming.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; it writes no `- Readiness:` field, since that is `/plan-review`'s output and never an author's to assert.

EXECUTION CONTRACT. Commit only the two declared `- Scope-Paths:` and only through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`; do not push; do not create a tag or release. The full suite must be run BARE (`python3 -m pytest`) and its actual output pasted, never summarized or claimed. NO ITEM IN THIS PLAN REQUIRES A TEMPORARY EDIT TO A TRACKED FILE, which is a deliberate property rather than an accident: both negative controls (V-02, V-04) drive altered INPUTS through parameters the functions already accept (`DETECTOR_COVERED_CLASSES` copied into a local, and `format_lifecycle_legend(stages=...)`), so a neutered checker is never needed. If you find yourself about to edit `agent_workflows/` or `docs/` to produce evidence, stop: the probe is wrong, not the plan.

SCOPE FENCE. The declared `- Scope-Paths:` are `tests/test_run_analytics_privacy_docs.py` and `tests/test_lifecycle_legend_help_reach.py`. That is a DECLARATION so finalize can reconcile what was edited against what was declared, not a stop condition: if the work genuinely requires a path outside it, make the edit and JUSTIFY it at finalize with `--scope-reason`, and acknowledge any declared-but-unmodified path with `--scope-ack`. Do not stop and report over a scope question. DO stop and report for a genuinely unsafe condition: a prerequisite symbol absent from `run_analytics_export`, `cli`, `term` or `lifecycle_style`, or an unresolvable concurrent edit to either declared file. Verified at authoring that no sibling pending plan declares either path, and that `tests/test_term.py` is deliberately avoided because `y2ge26` declares it (F-09).

POST-GATE LIFECYCLE MOVE. The finalize obligation is unconditional: this plan does not reach `.aw/records/plans/executed/` until every `V-*` carries pasted evidence with a non-pending `Result` and `aw ipd lint --phase pre-transition` reports conforming. OWNERSHIP IS CONDITIONAL: when executed under `aw oc run` or `aw agy run`, the RUNNER performs the finalize and the lifecycle move, so do not invoke it yourself; when executed by hand outside a runner, the executor performs it via `aw ipd finalize`. Never hand-edit the status line and never hand-move the file. This plan is the graduation carrier for backlog item `spvm3v` and covers both classes that item names; it does not set the item's status.
