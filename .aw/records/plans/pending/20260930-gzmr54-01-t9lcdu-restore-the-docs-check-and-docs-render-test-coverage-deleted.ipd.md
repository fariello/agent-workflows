# IPD: Restore the docs_check and docs_render test coverage deleted from tests/test_docs.py

- Date: 2026-09-30
- Kind: child
- Concern: TWO SHIPPED MODULES HAVE NO TEST CALLER AT ALL, AND ONE OF THEM IS ALREADY BROKEN IN A WAY NOTHING REPORTS. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_docs.py` whole, 472 lines and 28 test functions. Plan `fzueyy` restored only the run-scratch guard arm into `tests/test_run_scratch_path_guard.py` (verified: `ShippedRunScratchPathTests`, `ShippedRunScratchGuardFalsifiabilityTests` and `_bare_run_scratch_refs` are all present there), leaving the rest unrestored. MEASURED AT AUTHORING HEAD `2e2ecce12`: `rg -l 'docs_check|docs_render' tests/` returns NOTHING, so `agent_workflows/docs_check.py` (181 lines) and `agent_workflows/docs_render.py` (173 lines) ship with zero test callers. I DID NOT STOP AT THE COVERAGE ARGUMENT, because a coverage gap is only a hypothesis until it hides something. I recovered the deleted file into gitignored run scratch, re-anchored `REPO_ROOT`, and ran it: `1 failed, 27 passed`. The single failure is a LIVE DEFECT the deletion masked: `docs_check.check_aw_commands` reports an `aw-command` finding in `docs/skill-selection.md` saying `'aw router' is not a known subcommand`, against the plain-prose heading `## The aw router skill` (line 27 at authoring), which commit `a2394b00` ("feat(agyinstall): install unified aw router skill", 2026-09-26) added TWO DAYS AFTER the tests were deleted. So the checker has a false-positive bug that no suite can see, and the module's own docstring is what makes it a bug rather than a judgement call: it promises to check "every `aw <subcommand>` referenced in a FENCED COMMAND BLOCK", while `check_doc` applies `_AW_CMD_RE` to the raw text line by line with no notion of a code span at all.
- Scope: Restore behavioral test coverage for `agent_workflows/docs_check.py` and `agent_workflows/docs_render.py` as two per-module test files, and fix the prose-versus-code-span false positive in `check_aw_commands` that the restored coverage exposes. Out of scope: the `RunAnalyticsPrivacyDocTests` and `LifecycleLegendAndDocsDriftGuardTests` classes from the same deleted file (they test neither module and are deferred with reason below), any new `aw` subcommand, any wiring of these modules into `aw check` or a hook, and any edit to a document other than the single heading named in E-04.
- Scope-Paths: tests/test_docs_check.py, tests/test_docs_render.py, agent_workflows/docs_check.py, docs/skill-selection.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: gzmr54
- Set: gzmr54
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: t9lcdu
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-301..PR-308, all FIXED, none OPEN or DEFERRED. THIS IS AN UNUSUALLY WELL EVIDENCED PLAN AND ITS CENTRAL CLAIM REPRODUCED EXACTLY, INDEPENDENTLY, AT REVIEW HEAD `ba383298b`: recovering `19313eed^:tests/test_docs.py` into gitignored scratch with `REPO_ROOT` re-anchored gives `1 failed, 27 passed in 0.42s`, failing on precisely `DocFinding(doc='skill-selection.md', line=27, check='aw-command', message="'aw router' is not a known subcommand")`, and the same defect is directly observable without the recovered file (`check_docs_dir(Path("docs"))` returns that one finding today). F-01 (472 lines, 28 test functions), F-02 (zero test callers, 181 and 173 lines), F-03 (the `fzueyy` restoration present), F-05 (`'router' in known_subcommands()` False over 68 real subcommands; the docstring promises "referenced in a fenced command block" while `check_aw_commands` iterates raw lines with no code-span notion), F-06 (`19313eed` IS an ancestor of `a2394b00`), F-08 (both deferred classes green: `8 passed`), F-09 (all 18 required docs present and linked) and the inert-gate claim (`doc_findings` matches only `release_readiness.py`) ALL verified. F-07 was re-verified in BOTH halves without editing one tracked file, which also demonstrates the method the plan should use: an out-of-module restricted scan returned 0 findings across `docs/` while still flagging `` `aw florb` `` and staying silent on the prose heading, and applying only the heading fix to a gitignored COPY of `docs/` with the checker unchanged took `check_docs_dir` from 1 finding to 0. THE HIGHEST FINDING (PR-301, HIGH) IS THAT F-10 HAS INVERTED SINCE AUTHORING AND WOULD NOW TEACH AN EXECUTOR TO WAVE THROUGH A RED NODE: the plan says the suite is NOT green at the base and instructs "EXPECT ONE PRE-EXISTING FAILURE ... confirm it fails", but the bare suite is now FULLY GREEN at `3867 passed, 2 skipped` and `test_release_exempt_setter_roundtrip_and_parity` PASSES in isolation (`1 passed in 0.21s`), because it was a UTC-midnight date-rollover flake rather than a standing failure (backlog `fnb8pl` remains `open`, so the latent defect is real and correctly out of scope). The bar is now green-before and green-after, with an explicit re-run-the-node-alone test before accepting any red as pre-existing. PR-302 (HIGH) found the Required-tests section naming 3604 collected as "the baseline to compare against" while E-07 correctly said to measure at the execution base; the two contradicted each other and the figure is spent (re-measured 4077 collected, 664 commits later), so every count is now self-relative with a Step 0 convention bullet recording the live-versus-stable rule. PR-304 (MEDIUM) found a signature mismatch that would have cost a guaranteed round trip: `check_doc` takes a **`Path`**, not text, and review hit the `TypeError` directly, so all five current signatures are now recorded in E-01 and V-04's independence probe is routed through a gitignored docs copy (the only way to drive altered content through a Path-taking checker). PR-303 (MEDIUM) hardened the three negative controls for this SHARED CHECKOUT: each temporary source edit must be held for a NARROWED run only, and any probe needing altered doc CONTENT must use a gitignored copy rather than editing `docs/`, which is how review verified F-07 and F-09 with zero tracked-file edits. PR-305 (MEDIUM) supplied the accounting a restoration plan most needs and the plan lacked: the deleted file held TEN classes, not the "six" its prose implies, and all ten have a disposition (two already restored by `fzueyy`, five restored here, one subsumed with the subsumption MEASURED by deleting `docs/recovery.md` from a scratch copy and watching findings go 1 -> 6, two deferred to live carrier `spvm3v`). PR-306 (LOW) records that the recovered falsifiability arm injects `["run", "ipd"]` rather than calling `known_subcommands()`, which is what keeps it a unit test, since the live set has 68 entries that change whenever a subcommand lands. PR-307 added the missing scope fence (verified no sibling plan declares any of the four paths) and PR-308 corrected the terminal-transition verb from `aw ipd set` to `aw ipd finalize` with conditional runner-versus-executor ownership. All four cited carriers resolve to live items (`spvm3v`, `tj9dq9`, `fnb8pl` open; `gzmr54` graduated). OQ-01 verified sound and left resolved, its feasibility claim re-demonstrated rather than taken on trust. OQ-02 remains OPEN, `Blocking: no`, correctly a maintainer scope call and correctly carried by `spvm3v`; per the 2026-09-10 ruling a non-blocking question does not gate readiness. Three decisions recorded in the typed review record, all `Reversible: yes`. Structural preflight `conforming` at `author` and at `review-finalize`.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `gzmr54` in a non-interactive authoring turn. Measurement at HEAD `2e2ecce12` ran the deleted file out of gitignored scratch and found `1 failed, 27 passed`, so the plan's subject grew from pure restoration to restoration plus the one live checker defect the deletion masked (F-04, F-05). Two of the six classes the item names are deferred with reason rather than silently dropped (F-08).
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give `docs_check` and `docs_render` real test callers again, so a regression in either is reported by the suite instead of shipping unnoticed, and fix the `check_aw_commands` false positive that restoring the coverage immediately surfaces. The restored tests must drive the modules and assert on their outputs, never read their source.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the docs_check coverage and fix what it exposes

- [x] E-01 Create `tests/test_docs_check.py` covering the per-check FALSIFIABILITY arms of `docs_check`, recovered from `git show 19313eed^:tests/test_docs.py` (the `DocCheckFalsifiabilityTests` class) and re-verified against the CURRENT signatures of `docs_check.check_no_unicode_dashes`, `check_internal_links`, `check_aw_commands`, `check_doc` and `check_docs_dir` rather than pasted blind. THE FIVE SIGNATURES ARE RECORDED AT REVIEW SO THIS COSTS NO ROUND TRIP (F-11): `check_no_unicode_dashes(text, doc="")`, `check_internal_links(text, doc_path)` (text AND a `Path`), `check_aw_commands(text, known_subcommands, doc="")` (the known set is a REQUIRED argument, not defaulted), `check_doc(doc_path, subcommands=None)` (takes a **`Path`** and reads the file itself, so passing text raises `TypeError`), and `check_docs_dir(docs_dir, subcommands=None)`. INJECT THE KNOWN SET IN THESE PER-CHECK ARMS rather than calling `known_subcommands()`, exactly as the deleted arm did with `["run", "ipd"]`: the live set has 68 entries derived from the CLI parser and changes whenever a subcommand lands, so injecting pins the behavior under test and leaves the live set as E-02's subject (F-13). Each check must be proven to FIRE on a positive input and to STAY SILENT on a negative one, since a check that cannot fail proves nothing: an em dash (U+2014) and an en dash (U+2013) each produce a `no-unicode-dashes` finding while an ASCII hyphen produces none; a relative link to a missing file produces an `internal-link` finding while a link to a file that exists, an `http://` link, a bare `#anchor` and a `mailto:` link each produce none; and an unknown subcommand produces an `aw-command` finding while a known one produces none. Assert on the `DocFinding` fields (`doc`, `line`, `check`) and on its `__str__` rendering, not merely on truthiness, so a finding attributed to the wrong line or check is caught. Build inputs with `tmp_path`, never by writing into the real `docs/` tree.
  - Depends on: none
  - Expected outcome: The file exists and passes against unmodified source. `python3 -m pytest tests/test_docs_check.py -o addopts=""` reports every collected test passing, and `rg -c 'docs_check' tests/test_docs_check.py` is non-zero where `rg -l 'docs_check' tests/` returned nothing before.
  - Execution state: performed

- [x] E-02 Add to `tests/test_docs_check.py` the whole-tree arm restored from the deleted `DocCheckTests.test_no_findings_across_docs`: `check_docs_dir(REPO_ROOT / "docs")` must return an EMPTY finding list, with the failure message rendering every finding so a reader sees the whole set at once rather than rediscovering it one red test per document. Also cover `check_docs_dir`'s ignore behavior (it consults `artifact_core.get_ignored_dirs` / `is_ignored_path`) by asserting that a doc placed under an ignored directory inside a `tmp_path` docs tree contributes no finding, which is live behavior the deleted file never exercised. This item is expected to FAIL until E-04 lands; that failure is the point, and it must be observed before the fix rather than after.
  - Depends on: E-01
  - Expected outcome: Run before E-03/E-04 are performed, the whole-tree arm fails with one finding whose `doc` is `skill-selection.md`, whose `check` is `aw-command`, and whose message is `'aw router' is not a known subcommand`, attributed to the line carrying the heading `## The aw router skill` (the offset was 27 at authoring and may shift, so match the heading text and not the number). This reproduces the measurement this plan was authored from. The ignore arm passes immediately.
  - Execution state: performed

- [x] E-03 Fix `docs_check.check_aw_commands` so it honors the contract its own module docstring states, scanning `aw <subcommand>` references inside FENCED BLOCKS and INLINE CODE SPANS only, and ignoring plain prose. The defect is that `check_doc` applies `_AW_CMD_RE` to raw lines, so the prose heading `## The aw router skill` is read as a command invocation. Keep the function's signature and return type, and keep the `aw-command` check name and the `line` attribution correct relative to the ORIGINAL document (a fenced-block or span scan must not renumber lines). PRESERVE FALSIFIABILITY: the recovered input `run \`aw florb\` please` must still produce a finding, because it is inside a code span; that exact string is asserted in E-01, so a fix that silenced it would be caught. I VERIFIED THIS APPROACH RATHER THAN ASSUMING IT: a span-and-fence-restricted scan over the live `docs/` tree yields 0 findings while still flagging the `aw florb` input, so no OTHER document depends on the prose-scanning behavior and the fix is not trading this false positive for a new blind spot.
  - Depends on: E-02
  - Expected outcome: `check_aw_commands` returns no finding for a prose line naming `aw router` and still returns one for `` run `aw florb` please ``. The module docstring and the checker agree where they previously did not.
  - Execution state: performed

- [x] E-04 Correct the one document the checker legitimately flags, rewriting the `docs/skill-selection.md` heading `## The aw router skill` to put the command in a code span (`## The \`aw\` router skill`). THIS IS A SEPARATE ITEM FROM E-03 ON PURPOSE: E-03 removes the false positive class, while this item makes the document say what it means, so each can be reverted independently if review wants only one. I confirmed this is the ONLY document needing it: with the heading in a code span and the checker UNCHANGED, `check_docs_dir(Path("docs"))` returns 0 findings, which also proves the two fixes are independent rather than one masking the other. Change the heading only; do not edit the surrounding prose, and do not touch any other document.
  - Depends on: E-03
  - Expected outcome: `docs/skill-selection.md` carries the code-span heading, `git diff --stat docs/skill-selection.md` shows a one-line change, and the E-02 whole-tree arm now passes.
  - Execution state: performed

### Task group 2: restore the docs_render coverage

- [x] E-05 Create `tests/test_docs_render.py` covering `docs_render.render_support_table` and `render_benchmark_thresholds_table`, restored from the deleted `SupportTableRendersFromRegistryTests` and `BenchmarkThresholdTableTests` and re-verified against current signatures. The property under test is EVIDENCE GATING, which is what makes these renderers worth having: built against an EMPTY `host_capability_registry.HostCapabilityRegistry`, no row of the rendered support table may claim `supported`, and the provenance line must be present. Strengthen the restored arm with its missing POSITIVE control, which the deleted version lacked: promote one capability in the registry and assert that cell, and ONLY that cell, renders as supported. For the threshold table, assert the provenance line and the non-negotiable invariants (0 critical escapes, 1.0 evidence validity) are rendered for each risk class in `benchmark_thresholds.ThresholdPolicy`, iterating the policy rather than hard-coding a row count.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_docs_render.py -o addopts=""` reports every collected test passing, including the new positive control, and `rg -c 'docs_render' tests/test_docs_render.py` is non-zero where `rg -l 'docs_render' tests/` returned nothing before.
  - Execution state: performed

- [x] E-06 Add to `tests/test_docs_render.py` the `render_model_profile_table` arms restored from the deleted `ModelProfileTableTests`: the model ID stays a column DISTINCT from the profile and the reasoning config; the header records benchmark date, task corpus, host and version, and measurement uncertainty; unmeasured combinations are listed as pending rather than asserted; the caption carries the "not a universal quality claim" disclaimer; and a profile carrying an unknown key is REJECTED with `workflow_profile.ProfileError`, which is the arm proving a semantic override cannot be smuggled through a transport profile. Assert the rendered row ORDER follows the input sequence, and that an empty `pending_combinations` renders no pending section at all, neither of which the deleted version covered.
  - Depends on: E-05
  - Expected outcome: Every arm passes, including the `ProfileError` rejection and the empty-pending case.
  - Execution state: performed

### Task group 3: prove the whole tree still holds

- [x] E-07 Run the full suite BARE as `python3 -m pytest` with no added flags and confirm no regression, measuring the collected total against a baseline taken AT THE EXECUTION BASE rather than trusting any number recorded in this plan (other lanes land tests between authoring and execution, so a hard-coded number would misreport a clean run as a regression). Review re-measured the authoring figures as spent for exactly that reason: 3604 collected became **4077**, and the bare run is now **green at `3867 passed, 2 skipped`** where authoring saw one failure (F-10, PR-301, PR-302). The total must rise, since this plan only adds tests. Pay specific attention to any test that reads the `docs/` tree, since E-04 edits a shipped document: `tests/test_run_scratch_path_guard.py`, `tests/test_record_producers.py` and `tests/test_precommit_verbatim_exclusions.py` all reference docs paths (measured at review: 3, 31 and 10 `docs/` references respectively) and are the likeliest places an unexpected coupling surfaces. ONE REASSURANCE MEASURED AT REVIEW so the executor knows what to expect rather than fearing the edit: NO test in the tree references `skill-selection.md` at all (`rg -ln skill-selection tests/` returns nothing), so E-04's heading change has no known test coupling.
  - Depends on: E-06
  - Expected outcome: The bare suite passes GREEN with a collected total exceeding the executor's own execution-base baseline by exactly the number of tests added, and no previously passing test fails. If the `test_release_exempt_setter_roundtrip_and_parity` node is red at your base, do NOT accept it as the known flake on this plan's word: re-run that node alone, and only treat it as pre-existing if it fails in isolation at the base too (F-10).
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `AGENTS.md` forbids reading production source with `inspect`, `ast`, regex or substring search, forbids caller counts and symbol censuses, and requires restored coverage to CALL the code and assert on real outputs (GUIDING_PRINCIPLES P16). Every item above drives a function and asserts its return value, and the one structural-sounding claim in this plan (that the docstring and the checker disagree) is validated by CALLING `check_aw_commands`, not by reading it.
- PER-MODULE TEST FILES ARE THE CONVENTION, which is why this plan does not recreate the omnibus `tests/test_docs.py`. The tree carries `tests/test_host_capability_registry.py`, `test_host_capability_extension.py`, `test_host_capability_wiring.py` and `test_run_analytics.py` beside `test_run_analytics_cli.py` and `test_run_analytics_statistics.py`. The deleted file bundled six unrelated subjects, which is exactly why restoring it whole would re-create a file no one can place.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so validation uses `python3 -m pytest` with no added flags; `-o addopts=""` appears above ONLY for the narrowed per-file runs where per-test counts are needed, which is the documented exception.
- THE PRIOR RESTORATION IS THE PRECEDENT. `fzueyy` (executed, `wfartgrowth-01`) restored TWO classes of this same deleted file plus a helper into a NEW narrowly named file, `tests/test_run_scratch_path_guard.py`, rather than reviving `tests/test_docs.py`. This plan follows that shape. (Verified at review: `fzueyy` is `executed`, and `ShippedRunScratchPathTests`, `ShippedRunScratchGuardFalsifiabilityTests` and `_bare_run_scratch_refs` are all present in that file.)
- A COUNT OVER THE LIVE TREE IS RE-DERIVED, NOT MATCHED, which decides how every count in this plan must be consumed (repository plan-review convention, "Live-artifact success criteria vs. stable code facts"). A suite total and a collected total are LIVE populations that other lanes move, so an exact-match bar fails on correct work; the authoring figure belongs in the prose as context. ADDED AT REVIEW, because the authored Required-tests section named 3604 as "the baseline to compare against" while E-07 correctly said to measure at the execution base, and review re-measured 4077 (PR-302).
- MEASURE ALTERED DOC CONTENT IN A GITIGNORED COPY, NEVER BY EDITING `docs/` (ADDED AT REVIEW, PR-303). `check_doc` takes a `Path` and reads the file itself (F-11), so a probe over changed content needs a real file; copying `docs/` into gitignored scratch gives one without touching the tracked tree, and review used exactly that to verify both halves of F-07 and the deletion arm of F-09.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `tests/test_docs.py` was deleted whole: 472 lines, 28 test functions. | `git show 19313eed -- tests/test_docs.py` shows `deleted file mode`; `git show 19313eed^:tests/test_docs.py \| rg -c '    def test_'` reports 28. |
| F-02 | Both target modules ship with zero test callers at authoring HEAD `2e2ecce12`. | `rg -l 'docs_check\|docs_render' tests/` returns nothing. `agent_workflows/docs_check.py` is 181 lines, `docs_render.py` is 173. |
| F-03 | The item's premise holds and the prior restoration is partial, not absent. `fzueyy` restored only the run-scratch arm. | `ShippedRunScratchPathTests`, `ShippedRunScratchGuardFalsifiabilityTests` and `_bare_run_scratch_refs` are all present in `tests/test_run_scratch_path_guard.py`; the other classes are in no file. |
| F-04 | THE GAP HIDES A LIVE DEFECT, not just absent coverage. Running the recovered file out of gitignored scratch gives `1 failed, 27 passed`; the failure is an `aw-command` finding reading `'aw router' is not a known subcommand`, attributed to `docs/skill-selection.md`'s heading `## The aw router skill` (line 27 at authoring). **REPRODUCED EXACTLY AT REVIEW, INDEPENDENTLY AND BY THE SAME METHOD**, which is the single most important confirmation in this review: recovering `19313eed^:tests/test_docs.py` into a gitignored scratch dir with `REPO_ROOT` re-anchored gives `1 failed, 27 passed in 0.42s`, failing at `DocCheckTests::test_no_findings_across_docs` on precisely `DocFinding(doc='skill-selection.md', line=27, check='aw-command', message="'aw router' is not a known subcommand")`. The live defect is also directly observable without the recovered file at all: `docs_check.check_docs_dir(Path("docs"))` returns exactly that one finding today, still at line 27. | Recovered to gitignored scratch, `REPO_ROOT` re-anchored, run with `-o addopts=""`. Review: the same recovery run (`1 failed, 27 passed`) plus a direct `check_docs_dir(Path("docs"))` call printing `doc='skill-selection.md' line=27 check='aw-command'`; scratch removed and `git status --short` empty afterwards. |
| F-05 | That finding is a FALSE POSITIVE caused by the checker scanning prose. The flagged text is the plain Markdown heading `## The aw router skill`; `router` is genuinely not a subcommand (`'router' in docs_check.known_subcommands()` is `False`, over 68 real subcommands, so the fallback list is not in play), but a heading is not a command invocation. The module docstring promises to check references "in a fenced command block", which `check_doc` does not implement. | `docs/skill-selection.md` line 27; `docs_check.check_doc` passes raw text to `check_aw_commands`. |
| F-06 | The defect is NEWER than the deletion, so it was never a pre-existing failure the trim knowingly dropped. The heading arrived in `a2394b00` (2026-09-26); `19313eed` is its ancestor (2026-09-24). | `git log -S'The aw router skill' -- docs/skill-selection.md`; `git merge-base --is-ancestor 19313eed a2394b00` succeeds. |
| F-07 | BOTH fixes are independently sufficient and neither hides a second problem. Restricting the scan to fenced blocks and inline code spans yields 0 findings over the live `docs/` tree while still flagging `` run `aw florb` please ``; separately, code-spanning the heading with the checker unchanged also yields 0 findings. **BOTH HALVES RE-VERIFIED AT REVIEW WITHOUT EDITING ONE TRACKED FILE**, which both confirms the finding and demonstrates the method E-03/V-04 should use: a restricted scan implemented OUTSIDE the module (fence toggle plus `` ` ``-span extraction, reusing `docs_check._AW_CMD_RE`) returned 0 findings across every `docs/**/*.md` while still flagging `florb` and staying silent on the prose heading; and applying ONLY the heading fix to a gitignored COPY of `docs/` with the checker UNCHANGED took `check_docs_dir` from 1 finding to 0. So the two fixes really are independent, and neither masks the other. | Authored: two scratch probes against `docs/`, each reverted. Review: an out-of-module restricted scan printing `restricted scan findings over live docs/: 0`, `falsifiability input still flagged? [('x', 1, 'aw-command', 'florb')]`, `prose heading now silent? []`; plus a scratch-copy probe printing `BEFORE ... 1` then `AFTER heading fix (checker UNCHANGED) ... 0`. `git status --short` empty throughout. |
| F-08 | Two of the six classes the backlog item names belong to neither target module, so restoring them here would widen scope past the item's own stated subject. `RunAnalyticsPrivacyDocTests` tests `run_analytics_export`'s `DETECTOR_BLIND_SPOTS`/`DETECTOR_COVERED_CLASSES` against `docs/run-analytics.md`; `LifecycleLegendAndDocsDriftGuardTests` tests `cli._build_parser()` help against `lifecycle_style.STAGE_ORDER`. Both PASS today, so nothing is currently broken by deferring them, and partial coverage already exists for the latter (`tests/test_term.py` asserts `format_lifecycle_legend` covers `STAGE_ORDER`, though NO test asserts the legend reaches `--help` output). | Scratch run: both classes green. `rg -n 'LIFECYCLE LEGEND' tests/` returns nothing; `rg -n 'DETECTOR_BLIND_SPOTS' tests/` returns nothing. |
| F-10 | **THE "EXPECT ONE FAILURE" INSTRUCTION IS NOW WRONG AND MUST NOT BE FOLLOWED (CORRECTED AT REVIEW, PR-301).** At authoring the bare suite was red at `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, because `backlog.py` stamps history from the LOCAL clock (`datetime.date.today()`) while `status_set.py` uses UTC, so the two `aw backlog set` spellings recorded `2026-09-30` and `2026-10-01` for one transition. RE-MEASURED AT REVIEW HEAD `ba383298b`: the bare suite is **FULLY GREEN** at `3867 passed, 2 skipped, 3 warnings in 72.89s`, and the named node passes in isolation (`1 passed in 0.21s`). It was a DATE-ROLLOVER flake, not a standing failure: the two clocks only disagree when a run straddles UTC midnight. Backlog `fnb8pl` is still `open`, so the latent defect is real and correctly out of scope, but the EXECUTOR BAR IS A GREEN BASELINE. The authored instruction ("must expect this failure at the base") would teach an executor to wave through a red node, which is the dangerous direction: if that node is red at execution it is either the same flake (prove it by re-running the node alone) or something new that must be investigated. | Authored: clean detached worktree at HEAD `2e2ecce12`, `1 failed, 3394 passed, 2 skipped`. Review: bare `python3 -m pytest` -> `3867 passed, 2 skipped, 3 warnings`; narrowed node -> `1 passed in 0.21s`; `aw find backlog fnb8pl` -> `open`. |
| F-09 | The `DocsExistTests` class is subsumed rather than dropped: its required-doc list is enforced transitively, because every document it names is linked from `docs/README.md` and `check_internal_links` fails a dead relative link. A deleted required doc therefore fails E-02's whole-tree arm. VERIFIED AT REVIEW AND THE SUBSUMPTION IS GENUINELY PROVEN RATHER THAN ARGUED: all 18 required paths exist and all 17 non-index ones are linked from `docs/README.md`, and a scratch probe DELETING `docs/recovery.md` from a gitignored copy of the tree took `check_docs_dir` from 1 finding to 6, three of them `internal-link` findings naming the missing target in `README.md` (twice) and `troubleshooting.md`. So the property really does stay red-on-deletion without the hand-maintained list. | Probe over `docs/README.md` links: all 18 required paths resolve and all are linked from the index; three non-required docs (`branch-protection.md`, `runner-profiles.md`, `wtiso-state-taxonomy.md`) are unlinked, which is why a blanket orphan check is NOT added here. Review: deletion probe on a gitignored copy printing `baseline findings: 1` then `after deleting docs/recovery.md, findings: 6`, no tracked file touched. |
| F-11 | **ADDED AT REVIEW (PR-304). `check_doc` TAKES A `Path`, NOT TEXT, AND THE PLAN'S OWN V-ITEMS ASSUME OTHERWISE IN ONE PLACE.** E-01 rightly says to re-verify against CURRENT signatures rather than pasting blind, and the signatures are: `check_no_unicode_dashes(text, doc="")`, `check_internal_links(text, doc_path)` (text AND a Path), `check_aw_commands(text, known_subcommands, doc="")` (an explicit subcommand sequence, NOT defaulted), `check_doc(doc_path, subcommands=None)` (a PATH, reading the file itself), and `check_docs_dir(docs_dir, subcommands=None)`. Review hit the mismatch directly: calling `check_doc(text, known, name)` raises `TypeError: check_doc() takes from 1 to 2 positional arguments but 3 were given`. So any probe that wants to check ALTERED CONTENT must write a file (a gitignored scratch copy) rather than passing a string, which is exactly what V-04's independence probe needs. Stating the five signatures here removes a guaranteed round trip. | Each signature read from `agent_workflows/docs_check.py`; the `TypeError` reproduced at review by passing text to `check_doc`. |
| F-12 | **ADDED AT REVIEW (PR-305). THE DELETED FILE HELD TEN CLASSES, NOT SIX, AND THE PLAN'S DISPOSITION COVERS ALL OF THEM, so the accounting is sound but was never stated.** The ten are `DocsExistTests`, `DocCheckTests`, `DocCheckFalsifiabilityTests`, `SupportTableRendersFromRegistryTests`, `ModelProfileTableTests`, `ShippedRunScratchPathTests`, `ShippedRunScratchGuardFalsifiabilityTests`, `BenchmarkThresholdTableTests`, `RunAnalyticsPrivacyDocTests`, `LifecycleLegendAndDocsDriftGuardTests`. TWO are already restored by `fzueyy` (the run-scratch pair, measured present in `tests/test_run_scratch_path_guard.py`), FIVE are restored by this plan (`DocCheckTests` and `DocCheckFalsifiabilityTests` via E-01/E-02; `SupportTableRendersFromRegistryTests`, `BenchmarkThresholdTableTests` and `ModelProfileTableTests` via E-05/E-06), ONE is subsumed (`DocsExistTests`, F-09), and TWO are deferred with a carrier (F-08). That is 10 of 10 with no silent drop, which is the claim a reviewer most needs and which the plan's "six classes the item names" phrasing obscures. | `git show 19313eed^:tests/test_docs.py \| rg -n '^class '` listing all ten; per-class presence check over `tests/` showing exactly the run-scratch pair present and eight absent. |
| F-13 | **ADDED AT REVIEW (PR-306). THE RECOVERED FALSIFIABILITY ARM PASSES AN EXPLICIT TWO-ELEMENT SUBCOMMAND LIST, WHICH IS WHAT MAKES IT A UNIT TEST RATHER THAN A TREE-COUPLED ONE, AND E-01 SHOULD PRESERVE THAT.** The deleted `test_detects_unknown_command` reads `dc.check_aw_commands("run \`aw florb\` please", ["run", "ipd"], "x.md")`, injecting the known set rather than calling `known_subcommands()`. That matters for stability: `known_subcommands()` returns 68 entries derived from the live CLI parser, so an arm built on it changes meaning whenever a subcommand is added, while the injected list pins the behavior under test. E-01's restored arms should inject the known set for the per-check arms and reserve `known_subcommands()` for E-02's whole-tree arm, where the live set IS the subject. | The deleted class body read in full; `len(docs_check.known_subcommands())` -> 68 and `'router' in ...` -> False at review. |

## Proposed changes (ordered, validatable)

1. `tests/test_docs_check.py` (new): per-check falsifiability arms with positive and negative controls, `DocFinding` field assertions, the whole-tree `check_docs_dir(docs/)` zero-findings arm, and an ignored-directory arm (E-01, E-02).
2. `agent_workflows/docs_check.py`: restrict `check_aw_commands` scanning to fenced blocks and inline code spans, preserving signature, return type, check name and original line attribution (E-03).
3. `docs/skill-selection.md`: one heading, `## The aw router skill` to `## The \`aw\` router skill` (E-04).
4. `tests/test_docs_render.py` (new): support-table evidence gating with a new positive control, threshold-table invariants iterated from the policy, and the model-profile arms including the `ProfileError` rejection, row order and the empty-pending case (E-05, E-06).

## Deferred / out of scope (with reason)

- `RunAnalyticsPrivacyDocTests` and `LifecycleLegendAndDocsDriftGuardTests` are NOT restored here (F-08). They exercise `run_analytics_export` and `cli`/`lifecycle_style`, not the two modules this item is about, and both pass today, so deferring them leaves nothing newly broken. They are real coverage gaps and should be filed as their own backlog items against their own modules (plausibly `tests/test_run_analytics.py` and a legend arm beside `tests/test_term.py`). NOTE THE ONE SHARP EDGE a reviewer should weigh: no test currently asserts the lifecycle legend reaches `aw --help` output at all, only that `Term.format_lifecycle_legend` covers `STAGE_ORDER`, so that gap is live while deferred.
  - Carrier: spvm3v
- `DocsExistTests` is not restored as a standalone class, because its property is already enforced transitively through the index links (F-09). A reviewer who disagrees can ask for the explicit list; the reason it is omitted is that a hand-maintained required-doc list is a second place to update whenever a doc is legitimately retired, and the link check needs no maintenance.
  - Carrier-Declined: Nothing outlives this plan to carry. The property is ENFORCED, not deferred: every one of the 18 documents the deleted class listed is linked from `docs/README.md`, and E-02's whole-tree arm fails on a dead relative link (F-09, measured), so deleting a required doc still turns the suite red. Only the hand-maintained list is dropped, and a list is not an obligation.
- Wiring `check_docs_dir` into `aw check`, a pre-commit hook, or `release_readiness.gate_docs_checks` is out of scope. `gate_docs_checks` takes a `doc_findings` sequence and NOTHING in the repository computes one (`rg -n 'doc_findings'` matches only `release_readiness.py` itself), so the gate is inert; that is a real finding but it is a wiring decision, not test restoration.
  - Carrier: tj9dq9
- The pre-existing suite failure F-10 (`test_release_exempt_setter_roundtrip_and_parity`, a local-versus-UTC history date skew between `backlog.py` and `status_set.py`) is NOT fixed here. It touches neither target module and neither declared source path, and fixing it would mean editing `agent_workflows/backlog.py` outside this plan's scope.
  - Carrier: fnb8pl

## Scope check

- Over-scope: none. The two new test files and the two source/doc edits are each required by a numbered item, and the checker fix is confined to the one function whose contract the restored test disproves. Verified at review that no sibling pending or approved plan declares any of the four paths.
- Under-scope: Deliberate, and named above. Two deleted classes stay unrestored (F-08), `gate_docs_checks` stays inert, and no new `aw` subcommand is introduced for `router`. A reviewer who wants any of these in scope should say so before approval, since each would change the declared `- Scope-Paths:`.
- FULL ACCOUNTING OF THE DELETED FILE, ADDED AT REVIEW (F-12) because a restoration plan's most important property is that nothing was silently dropped. The deleted `tests/test_docs.py` held TEN classes, and all ten have a stated disposition: TWO already restored by `fzueyy` (`ShippedRunScratchPathTests`, `ShippedRunScratchGuardFalsifiabilityTests`), FIVE restored here (`DocCheckTests` and `DocCheckFalsifiabilityTests` by E-01/E-02; `SupportTableRendersFromRegistryTests`, `BenchmarkThresholdTableTests` and `ModelProfileTableTests` by E-05/E-06), ONE subsumed by the link check with the subsumption measured (`DocsExistTests`, F-09), and TWO deferred to a live carrier (`RunAnalyticsPrivacyDocTests`, `LifecycleLegendAndDocsDriftGuardTests`, carrier `spvm3v`, F-08). Ten of ten, no silent drop. The plan's own prose called it "six classes the item names", which undercounts and obscures this; the accounting is what a reviewer should check.

## Required tests / validation

Narrowed runs with `-o addopts=""` for per-test counts on the two new files, then the FULL suite run BARE (`python3 -m pytest`) with its actual output pasted.

CAPTURE YOUR OWN BASELINE; DO NOT USE A NUMBER FROM THIS PLAN (CORRECTED AT REVIEW, PR-302). The authored baseline of 3604 collected at HEAD `2e2ecce12` is SPENT: re-measured at review HEAD `ba383298b`, `python3 -m pytest --collect-only -q -o addopts=""` reports **4077 tests collected** and the bare run reports **`3867 passed, 2 skipped`**, after 664 intervening commits. E-07 already says to measure at the execution base rather than trusting 3604, and this makes the two statements agree instead of contradicting each other. Every count comparison in this plan is therefore SELF-RELATIVE: measure before any edit, measure after, and require the delta to equal the number of tests you added. The bar is a GREEN before-baseline and a GREEN after-baseline (F-10, corrected).

E-02's arm must be observed FAILING before E-03 and E-04 are performed and PASSING after, since a fix validated only after the fact does not demonstrate it addressed the measured defect. E-03's falsifiability must be shown by a negative control: a temporary edit that would reintroduce prose scanning must make the restored test fail, and must be reverted in the same pass with the revert proven by `git diff --stat`.

METHOD RULE FOR EVERY NEGATIVE CONTROL AND EVERY DOCS-TREE PROBE (ADDED AT REVIEW, PR-303). Three V-items require a TEMPORARY edit to a tracked file (V-01 neuters a checker, V-03 reverts the scan restriction, V-04 reverts the checker fix). This is a SHARED CHECKOUT, so each such edit must be held for the shortest possible window: run only the NARROWED node while the edit is live (`-o addopts=""` on the single file), never the full suite, then restore and paste `git status --short` empty. Where a probe only needs to observe `check_docs_dir`'s behavior on altered CONTENT, do not edit `docs/` at all: copy the tree into a gitignored scratch directory and point the checker at the copy. Review used exactly that method to verify F-07 and F-09 without touching one tracked file, so it is known to work here.

## Spec / documentation sync

No `.spec.md` file is amended, so none appears in `- Scope-Paths:`. The behavior changed in E-03 is governed by `docs_check`'s own module docstring rather than by a spec, and the change brings the code INTO line with that docstring rather than altering a documented contract; if the docstring needs its wording tightened to name inline code spans beside fenced blocks, that edit belongs to E-03's file and is covered by the declared path. `docs/skill-selection.md` is edited by E-04 and is declared. No user-facing document gains or loses a claim, so `CHANGELOG.md` is not touched by this plan.

## Open questions

### OQ-01: Should `check_aw_commands` ignore prose entirely, or should prose be held to the same standard with a documented exemption?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, so it does not need the maintainer. The module docstring already states the intended scope ("every `aw <subcommand>` referenced in a fenced command block"), so honoring it is a fix rather than a judgement call, and the measurement in F-07 shows the restricted scan yields 0 findings over the live tree while still catching the falsifiability input. Not blocking: were the maintainer to prefer the opposite resolution (keep prose in scope and exempt `router`), only E-03 changes and the restored tests in E-01 still stand.

### OQ-02: Should the two deferred classes be restored in this Set rather than deferred?

- Blocking: no
- Status: open
- Owner: human
- Carrier: spvm3v
- Resolution or deferral rationale: A SCOPE JUDGEMENT THAT IS THE MAINTAINER'S, which is why it is not resolved here. The repository can tell us the classes pass today (F-08) but not whether coverage for `run_analytics_export` and the `--help` legend belongs to this item or to its own. Not blocking: this plan is executable and complete as scoped either way, and the answer only decides whether follow-on work is filed. The work itself is carried by backlog `spvm3v` either way, so a 'no' answer here does not drop it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the output of `python3 -m pytest tests/test_docs_check.py -o addopts="" -q` showing every collected test passing with a count, plus the output of `rg -c 'docs_check' tests/test_docs_check.py`. Then paste a NEGATIVE CONTROL proving the arms can fail: temporarily neuter `check_no_unicode_dashes` to return `[]`, paste the resulting failure, revert it, and paste `git diff --stat` showing a clean tree.
  - Observed evidence:
    Passing test run on tests/test_docs_check.py:
    ```
    $ python3 -m pytest tests/test_docs_check.py -o addopts="" -q
    ..........                                                               [100%]
    10 passed in 0.50s
    ```
    Occurrences of docs_check in tests/test_docs_check.py:
    ```
    $ rg -c 'docs_check' tests/test_docs_check.py
    3
    ```
    Negative control (temporarily neutered check_no_unicode_dashes to return []):
    ```
    $ python3 -m pytest tests/test_docs_check.py -o addopts="" -q
    ..F.....FF                                                               [100%]
    =================================== FAILURES ===================================
    _______________ DocCheckFalsifiabilityTests.test_detects_en_dash _______________
    self = <tests.test_docs_check.DocCheckFalsifiabilityTests testMethod=test_detects_en_dash>
        def test_detects_en_dash(self):
            findings = dc.check_no_unicode_dashes("a \u2013 b", "x.md")
    >       self.assertEqual(len(findings), 1)
    E       AssertionError: 0 != 1
    tests/test_docs_check.py:32: AssertionError
    _______________ DocCheckFalsifiabilityTests.test_detects_em_dash _______________
    self = <tests.test_docs_check.DocCheckFalsifiabilityTests testMethod=test_detects_em_dash>
        def test_detects_em_dash(self):
            findings = dc.check_no_unicode_dashes("a \u2014 b", "x.md")
    >       self.assertEqual(len(findings), 1)
    E       AssertionError: 0 != 1
    tests/test_docs_check.py:20: AssertionError
    _________ DocCheckFalsifiabilityTests.test_check_doc_drives_all_checks _________
    self = <tests.test_docs_check.DocCheckFalsifiabilityTests testMethod=test_check_doc_drives_all_checks>
        def test_check_doc_drives_all_checks(self):
    ...
    >           self.assertEqual(len(findings), 3)
    E           AssertionError: 2 != 3
    tests/test_docs_check.py:120: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_docs_check.py::DocCheckFalsifiabilityTests::test_detects_en_dash
    FAILED tests/test_docs_check.py::DocCheckFalsifiabilityTests::test_detects_em_dash
    FAILED tests/test_docs_check.py::DocCheckFalsifiabilityTests::test_check_doc_drives_all_checks
    3 failed, 7 passed in 0.29s
    ```
    Reverted and clean:
    ```
    $ git checkout agent_workflows/docs_check.py && git diff --stat
    Updated 1 path from the index
    $ git diff --stat
    (clean)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the whole-tree arm FAILING before E-03/E-04, with the message naming `skill-selection.md` and `'aw router' is not a known subcommand` verbatim, and separately paste it PASSING after. Paste the ignored-directory arm passing. The before-and-after pair is the required shape; a single passing run does not satisfy this item.
  - Observed evidence:
    Before E-03/E-04 (whole-tree arm failing with expected finding):
    ```
    $ python3 -m pytest tests/test_docs_check.py -o addopts="" -q
    ..........F.                                                             [100%]
    =================================== FAILURES ===================================
    __________________ DocCheckTests.test_no_findings_across_docs __________________
    self = <tests.test_docs_check.DocCheckTests testMethod=test_no_findings_across_docs>
        def test_no_findings_across_docs(self):
            findings = dc.check_docs_dir(DOCS_DIR)
    >       self.assertEqual(findings, [], "\n".join(str(f) for f in findings))
    E       AssertionError: Lists differ: [DocFinding(doc='skill-selection.md', line[69 chars]nd")] != []
    E       First list contains 1 additional elements.
    E       First extra element 0:
    E       DocFinding(doc='skill-selection.md', line=27, check='aw-command', message="'aw router' is not a known subcommand")
    E       + []
    E       - [DocFinding(doc='skill-selection.md',
    E       -             line=27,
    E       -             check='aw-command',
    E       -             message="'aw router' is not a known subcommand")] : skill-selection.md:27: [aw-command] 'aw router' is not a known subcommand
    tests/test_docs_check.py:138: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_docs_check.py::DocCheckTests::test_no_findings_across_docs
    1 failed, 11 passed in 1.07s
    ```
    After E-03/E-04 (whole-tree arm and ignored-directory arm passing):
    ```
    $ python3 -m pytest tests/test_docs_check.py -o addopts="" -q
    ...............                                                          [100%]
    15 passed in 2.71s
    ```
    Ignored directory arm passing: `DocCheckTests.test_check_docs_dir_respects_ignored_directories` passed without findings.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste a Python one-liner result showing `check_aw_commands` returns `[]` for the prose line `## The aw router skill` and returns a non-empty list for `` run `aw florb` please ``, with the finding's `check` field shown as `aw-command`. Paste `git diff agent_workflows/docs_check.py` so the reviewer sees the scan restriction and can confirm line attribution is computed against the original document. Paste a NEGATIVE CONTROL: revert the restriction temporarily, show the E-01 prose arm failing, restore it, and show `git diff --stat` clean.
  - Observed evidence:
    Python one-liner result:
    ```
    $ python3 -c "from agent_workflows.docs_check import check_aw_commands; print('prose:', check_aw_commands('## The aw router skill', ['run', 'ipd'], 'x.md')); print('inline:', [(f.check, f.message) for f in check_aw_commands('run \`aw florb\` please', ['run', 'ipd'], 'x.md')])"
    prose: []
    inline: [('aw-command', "'aw florb' is not a known subcommand")]
    ```
    git diff agent_workflows/docs_check.py (confirming line attribution uses original line index i):
    ```diff
    @@ -9,7 +9,7 @@ Deterministic, read-only checks over the Markdown documentation set:
       * :func:`check_internal_links`    - a relative Markdown link ``[text](path)`` must resolve to
         a file that exists (a broken link fails).
       * :func:`check_aw_commands`       - every ``aw <subcommand>`` referenced in a fenced command
    -    block must be a known top-level subcommand (a typo fails).
    +    block or inline code span must be a known top-level subcommand (a typo fails).
       * :func:`check_doc`               - run all checks over one doc, returning findings.
       * :func:`check_docs_dir`          - run all checks over a docs directory.

    @@ -27,8 +27,10 @@ EN_DASH = "\u2013"

     # Markdown inline link: [text](target)
     _LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    -# An `aw <sub>` reference (in prose or fenced blocks).
    +# An `aw <sub>` reference (in inline code spans or fenced blocks).
     _AW_CMD_RE = re.compile(r"\baw\s+([a-z][a-z0-9-]*)\b")
    +# Markdown inline code span: `code` or ``code``
    +_CODE_SPAN_RE = re.compile(r"(`+)(.*?)\1")


     @dataclass
    @@ -92,21 +94,50 @@ def check_internal_links(text: str, doc_path: Path) -> List[DocFinding]:
     def check_aw_commands(
         text: str, known_subcommands: Sequence[str], doc: str = ""
     ) -> List[DocFinding]:
    -    """Fail on an ``aw <subcommand>`` reference that is not a known top-level subcommand."""
    +    """Fail on an ``aw <subcommand>`` reference in code that is not a known top-level subcommand.
    +
    +    Scans fenced command blocks and inline code spans only, ignoring plain prose.
    +    """
         known = set(known_subcommands)
         findings: List[DocFinding] = []
    +    in_fence = False
    +    fence_char: Optional[str] = None
         for i, line in enumerate(text.splitlines(), 1):
    -        for m in _AW_CMD_RE.finditer(line):
    -            sub = m.group(1)
    -            if sub not in known:
    -                findings.append(
    -                    DocFinding(
    -                        doc,
    -                        i,
    -                        "aw-command",
    -                        f"'aw {sub}' is not a known subcommand",
    +            stripped = line.strip()
    +            if not in_fence:
    +                if stripped.startswith(("```", "~~~")):
    +                    in_fence = True
    +                    fence_char = stripped[:3]
    +                    continue
    +                for span_m in _CODE_SPAN_RE.finditer(line):
    +                    code_text = span_m.group(2)
    +                    for m in _AW_CMD_RE.finditer(code_text):
    +                        sub = m.group(1)
    +                        if sub not in known:
    +                            findings.append(
    +                                DocFinding(
    +                                    doc,
    +                                    i,
    +                                    "aw-command",
    +                                    f"'aw {sub}' is not a known subcommand",
    +                                )
    +                            )
    +            else:
    +                if stripped.startswith(("```", "~~~")) and stripped[:3] == fence_char:
    +                    in_fence = False
    +                    fence_char = None
    +                    continue
    +                for m in _AW_CMD_RE.finditer(line):
    +                    sub = m.group(1)
    +                    if sub not in known:
    +                        findings.append(
    +                            DocFinding(
    +                                doc,
    +                                i,
    +                                "aw-command",
    +                                f"'aw {sub}' is not a known subcommand",
    +                            )
    +                        )
         return findings
    ```
    Negative control (reverted restriction temporarily):
    ```
    $ python3 -m pytest tests/test_docs_check.py -k "test_ignores_plain_prose_command_reference" -o addopts="" -q
    F                                                                        [100%]
    =================================== FAILURES ===================================
    ____ DocCheckFalsifiabilityTests.test_ignores_plain_prose_command_reference ____
    self = <tests.test_docs_check.DocCheckFalsifiabilityTests testMethod=test_ignores_plain_prose_command_reference>
        def test_ignores_plain_prose_command_reference(self):
            findings = dc.check_aw_commands(
                "## The aw router skill", ["run", "ipd"], "x.md"
            )
    >       self.assertEqual(findings, [])
    E       AssertionError: Lists differ: [DocFinding(doc='x.md', line=1, check='aw-[54 chars]nd")] != []
    E       First list contains 1 additional elements.
    E       First extra element 0:
    E       DocFinding(doc='x.md', line=1, check='aw-command', message="'aw router' is not a known subcommand")
    tests/test_docs_check.py:108: AssertionError
    FAILED tests/test_docs_check.py::DocCheckFalsifiabilityTests::test_ignores_plain_prose_command_reference
    1 failed, 14 deselected in 0.14s
    ```
    Restored fix, verified git status clean.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste `git diff docs/skill-selection.md` showing exactly one changed line, and paste the output of a `check_docs_dir(Path("docs"))` call returning an empty list. Also prove THE TWO FIXES ARE INDEPENDENT rather than one masking the other (F-07), and prefer the method review used, which needs no revert at all: copy `docs/` into a gitignored scratch directory, apply ONLY the heading change there, and run `check_docs_dir` against the copy with the checker UNCHANGED, showing it goes from 1 finding to 0. Review did exactly this and recorded `BEFORE heading fix ... 1` then `AFTER heading fix (checker UNCHANGED) ... 0`, touching no tracked file. If you instead revert the E-03 fix in place, hold the revert for the narrowed probe only, restore it immediately, and paste `git status --short` empty afterwards. NOTE THE SIGNATURE CONSTRAINT (F-11): `check_doc` takes a `Path` and reads the file itself, so an in-memory string substitution cannot drive this probe; a file must exist, which is why the scratch copy is the clean route.
  - Observed evidence:
    git diff docs/skill-selection.md (one-line change):
    ```diff
    diff --git a/docs/skill-selection.md b/docs/skill-selection.md
    index 8086f1a72..4961eb5bb 100644
    --- a/docs/skill-selection.md
    +++ b/docs/skill-selection.md
    @@ -24,7 +24,7 @@ clauses, references a missing resource, exceeds the entry-point byte budget, or
     the canonical digest. `check_authority_not_inlined` fails a router that copied the canonical
     body into its own prose.

    -## The aw router skill
    +## The `aw` router skill

     In addition to per-workflow skills, the compiler generates a unified router skill package at `.agents/skills/aw/SKILL.md` (via `agent_workflows/host_adapters.build_aw_router_skill_package`).
    ```
    check_docs_dir(Path("docs")) call output:
    ```
    $ python3 -c "from pathlib import Path; from agent_workflows import docs_check as dc; print('check_docs_dir:', dc.check_docs_dir(Path('docs')))"
    check_docs_dir: []
    ```
    Independence probe (copying docs/ to scratch directory with checker UNCHANGED):
    ```
    BEFORE heading fix (checker UNCHANGED): 1 finding(s): [DocFinding(doc='skill-selection.md', line=27, check='aw-command', message="'aw router' is not a known subcommand")]
    AFTER heading fix (checker UNCHANGED): 0 finding(s): []
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste `python3 -m pytest tests/test_docs_render.py -o addopts="" -q` with a passing count and `rg -c 'docs_render' tests/test_docs_render.py`. Paste the test body or output demonstrating the POSITIVE control specifically: with one capability promoted in the registry, that cell renders supported and the others do not. An empty-registry-only run does not satisfy this item, because it cannot distinguish evidence gating from a renderer that never emits `supported` at all.
  - Observed evidence:
    Passing test run on tests/test_docs_render.py:
    ```
    $ python3 -m pytest tests/test_docs_render.py -o addopts="" -q
    .........                                                                [100%]
    9 passed in 1.23s
    ```
    Occurrences of docs_render in tests/test_docs_render.py:
    ```
    $ rg -c 'docs_render' tests/test_docs_render.py
    3
    ```
    Positive control test run and rendered row:
    ```
    $ python3 -m pytest tests/test_docs_render.py -k "test_promoted_capability_renders_supported_positive_control" -o addopts="" -q
    .                                                                        [100%]
    1 passed, 8 deselected in 1.30s
    ```
    Output from positive control:
    ```
    Supported row: | opencode | 1.0.0 | skill | router | supported |
    ```
    All other capability cells render as 'unverified'.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste the passing run covering the model-profile arms, including the `workflow_profile.ProfileError` rejection of an unknown profile key, the rendered-row order assertion, and the empty-`pending_combinations` case rendering no pending section. Paste the rendered table text for one row so the reviewer can see the model ID and reasoning config are separate columns rather than taking the assertion's word for it.
  - Observed evidence:
    Passing run covering ModelProfileTableTests:
    ```
    $ python3 -m pytest tests/test_docs_render.py -k "ModelProfileTableTests" -o addopts="" -q
    .....                                                                    [100%]
    5 passed, 4 deselected in 1.27s
    ```
    Rendered table text for one row demonstrating distinct Model ID and Reasoning config columns:
    ```
    | Model ID | Profile | Reasoning config | Output format | Notes |
    |---|---|---|---|---|
    | (operator-selected) | default | medium | (host default) | baseline |
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Paste the FULL bare `python3 -m pytest` output including the final `N passed` summary line, with no added flags. Paste the execution-base baseline total you measured BEFORE the change and the new total, and state the delta explicitly rather than only asserting green; the delta must equal the number of tests this plan added, and both runs must be YOUR OWN (do not compare against 3604 or 4077 or any other figure written here; both are dated measurements, not bars). THE BAR IS GREEN BEFORE AND GREEN AFTER (CORRECTED AT REVIEW, PR-301): review measured the suite fully green at `3867 passed, 2 skipped`, and the `test_release_exempt_setter_roundtrip_and_parity` node the authored plan told you to expect RED now PASSES in isolation, because it was a UTC-midnight date-rollover flake rather than a standing failure. So do NOT pre-accept any red node. If that node is red at your base, re-run it alone: a failure in isolation at the base with the same local-versus-UTC date diff is the known flake (backlog `fnb8pl`, still `open`) and must be reported as pre-existing and left unfixed; anything else is new and must be investigated, not waved through. Do NOT report the run green by excluding any node. Paste `git diff --cached --name-only` before the commit showing ONLY the four declared `- Scope-Paths:` entries, and paste `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
    Execution-base baseline measured BEFORE changes:
    - Collected: 6718 tests collected in 20.47s
    - Passed: 6458 passed, 2 skipped, 3 warnings in 323.01s (258 deselected by default options)

    Full bare `python3 -m pytest` output AFTER changes:
    ```
    ...................................................................      [100%]
    =============================== warnings summary ===============================
    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_the_lock_is_reacquirable_after_the_holder_exits
    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_second_holder_is_genuinely_EXCLUDED_and_the_holder_is_NAMED
    tests/test_concurrent_driver_guard.py::RealTwoProcessContentionTests::test_a_KILLED_holder_does_not_strand_the_lock
      DeprecationWarning: This process is multi-threaded, use of fork() may lead to deadlocks in the child.
        self.pid = os.fork()

    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    NOTE: 258 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    6482 passed, 2 skipped, 3 warnings in 693.80s (0:11:33)
    ```

    Post-change collected total:
    - Collected: 6742 tests collected in 18.31s
    - Delta collected: 6742 - 6718 = +24 tests
    - Delta passed: 6482 - 6458 = +24 passed
    - Added tests breakdown:
      - tests/test_docs_check.py: 15 tests
      - tests/test_docs_render.py: 9 tests
      - Total added: 24 tests. Delta matches exactly.

    git diff --cached --name-only before commit:
    ```
    agent_workflows/docs_check.py
    docs/skill-selection.md
    tests/test_docs_check.py
    tests/test_docs_render.py
    ```

    aw ipd lint --phase pre-transition report: conforming
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; it writes no `- Readiness:` field, since that is `/plan-review`'s output and never an author's to assert.

EXECUTION CONTRACT. Commit only the four declared `- Scope-Paths:` and only through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`; do not push; do not create a tag or release. The full suite must be run BARE (`python3 -m pytest`) and its actual output pasted, never summarized or claimed. V-01, V-03 and V-04 each require a TEMPORARY source edit as a negative control: every one must be reverted in the same pass and the revert proven with `git diff --stat`, because leaving a neutered check in the tree would ship the very blind spot this plan exists to close. HOLD EVERY SUCH EDIT FOR THE NARROWED RUN ONLY (ADDED AT REVIEW, PR-303): run the single affected file with `-o addopts=""` while the edit is live, never the full suite, because this is a shared checkout and a restore after a multi-minute run discards whatever a co-worker wrote in the interval. Where a probe only needs ALTERED CONTENT rather than altered code, use a gitignored copy of `docs/` instead of editing the tracked tree; review verified F-07 and F-09 that way with zero tracked-file edits. ORDER MATTERS AND IS NOT OPTIONAL: E-02 must be observed failing BEFORE E-03 and E-04 are performed, so do not fix the checker first and reconstruct the failure afterwards.

SCOPE FENCE (ADDED AT REVIEW, PR-307). The declared `- Scope-Paths:` are `tests/test_docs_check.py`, `tests/test_docs_render.py`, `agent_workflows/docs_check.py` and `docs/skill-selection.md`. That is a DECLARATION so finalize can reconcile what was edited against what was declared, not a stop condition: if the work genuinely requires a path outside it, make the edit and JUSTIFY it at finalize with `--scope-reason`, and acknowledge any declared-but-unmodified path with `--scope-ack`. Do not stop and report over a scope question. DO stop and report for a genuinely unsafe condition: an unresolvable concurrent edit to `agent_workflows/docs_check.py` or `docs/skill-selection.md`, or a prerequisite symbol that is absent. Verified at review that no sibling pending or approved plan declares any of the four paths, so none is contested today.

POST-GATE LIFECYCLE MOVE. The finalize obligation is unconditional: this plan does not reach `.aw/records/plans/executed/` until every `V-*` carries pasted evidence with a non-pending `Result` and `aw ipd lint --phase pre-transition` reports conforming. OWNERSHIP IS CONDITIONAL (CORRECTED AT REVIEW, PR-308): when executed under `aw oc run` or `aw agy run`, the RUNNER performs the finalize and the lifecycle move, so do not invoke it yourself; when executed by hand outside a runner, the executor performs it via `aw ipd finalize`. Never hand-edit the status line and never hand-move the file. The authored instruction named `aw ipd set` for the terminal transition; `aw ipd finalize` is the verb that owns it, because it also runs the scope reconciliation the fence above depends on. This plan is the graduation carrier for backlog item `gzmr54`; whether that item closes `done` or stays open for the two deferred classes (OQ-02) is the maintainer's call, and this plan does not close it.
