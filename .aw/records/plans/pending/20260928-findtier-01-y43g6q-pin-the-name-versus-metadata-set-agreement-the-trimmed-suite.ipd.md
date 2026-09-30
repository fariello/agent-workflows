# IPD: Pin the name-versus-metadata Set agreement the trimmed suite left unguarded and correct the surviving fixture mismatches

- Date: 2026-09-28
- Kind: child
- Concern: Backlog `0f809c` asks for a broader sweep of fixture trees for the latent "declared `- Set:` contradicts the filename's setid segment" inconsistency `3i6rso` found in four `check_engine` rows. Measured, the sweep finds 36 such fixtures across 14 test modules, and separately the ONE test module that guarded the rule reporting this shape (`tests/test_name_identity_report.py`, 585 lines) was DELETED by a suite-trim commit, leaving `check_engine.check_name_identity`'s `drift` branch with zero coverage: disabling that branch outright leaves the entire suite green.
- Scope: Restore behavioral coverage for the `drift` bucket (a modern id6-clustered filename whose declared `- Set:`/`- Id:` disagrees with its name) as fixture-driven rows in `tests/test_check_engine.py`, and correct the incidental name-vs-metadata mismatch in the four fixtures where it is genuinely accidental AND the fixture's own module asserts nothing about setid resolution. Does NOT change `check_engine` behavior, does NOT touch the deliberate legacy-trap fixtures, and does NOT mass-rewrite all 36 hits.
- Scope-Paths: tests/test_check_engine.py, tests/test_find_filters.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 0f809c
- Set: findtier
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: y43g6q
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED; five findings PR-801..PR-805 fixed, two BLOCKER (the chosen table cannot assert the drift bucket, and the surviving rule-id-only assertion survives the plan's own mutant); review record written; readiness go-pending-approval

- 2026-09-29 /plan-review findings (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801, PR-802 (both BLOCKER), PR-803, PR-804, PR-805 all FIXED. Reviewed at HEAD `bf3cf2d7`. The DIAGNOSIS was confirmed independently: with the `elif modern:` arm made unreachable in memory, a bare suite run reported `3246 passed, 2 skipped`, identical to the clean baseline, so the `drift` branch really is unguarded. The REMEDY could not have worked. `check.identity-absent-from-name` comes from `check_name_identity` on the types sweep, while `CollisionTests.COLLISIONS` matches its detail columns only against `check_collisions` output (measured 0 findings there against 1 from the types sweep), so a row in that table cannot assert the `[drift]` bucket; and because the mutant leaves the rule id intact and only flips the bucket prefix, the surviving rule-id-only assertion passes BOTH mutated and clean, making E-01 and E-02 jointly unsatisfiable and the coverage decorative. Both candidate shapes were run: detail-asserting passes clean and fails mutated, rule-id-only passes both. E-01 rewritten to a focused test driving `check_name_identity` directly per `SetidLengthTests`' precedent; E-02 given the working in-memory rebind and a kill criterion; OQ-01 re-resolved (its "style call with no correctness consequence" was falsified); F-9, F-10, F-11 added; F-7/F-8's drifted counts refreshed. No code file was modified by this review: `check_engine.py` never written, `test_find_filters.py` restored byte-for-byte after verifying F-4. Three Decisions recorded, all reversible. `aw ipd lint --phase review-finalize` conforms.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `0f809c`. Step 0 measurement re-aimed the plan: the item asks for a fixture sweep, and the sweep's real finding is that the RULE guarding this shape lost all of its coverage to a suite trim, which is a more valuable gap than the cosmetic mismatches the item anticipated.
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Close backlog `0f809c` on evidence rather than on a cosmetic sweep. The item's literal ask (find other fixture trees carrying a declared `- Set:` that contradicts their own filename) is answered with a measured census: 36 fixtures across 14 modules. But the census's important finding is a COVERAGE hole, not a tidiness problem: the rule that reports this exact shape, `check_engine.check_name_identity`'s `drift` bucket, has no test left anywhere, because the 585-line module that covered it was deleted in a suite trim. This plan restores that coverage as fixture rows in the surviving table, and corrects only the mismatches that are provably incidental.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the lost coverage (the census's real finding)

- [ ] E-01 Add behavioral coverage for the `drift` bucket to `tests/test_check_engine.py` as a SMALL FOCUSED TEST that drives `check_engine.check_name_identity` DIRECTLY and asserts the `[drift]` bucket marker in the finding's detail. Build the fixture with the module's existing `_plan_text(id6, setid=...)` helper under a filename whose setid segment differs from the `setid=` argument (the exact shape the backlog item describes: a plan named `20260927-demo-01-aaa111-p.ipd.md` declaring `- Set: topic`). Assert three things: the rule set is exactly `[check.identity-absent-from-name]`, the detail CONTAINS `[drift]`, and the detail names the declared value (`Set: topic`). Document beside it that this is what `tests/test_name_identity_report.py` held before commit `19313eed` deleted it, that the `drift` bucket is the ONLY one of the rule's four buckets with no live member on this tree (so a fixture is the only possible coverage), and that disabling the branch was measured to leave the whole suite green.

  DO NOT PUT THIS IN `CollisionTests.COLLISIONS`. An earlier draft of this item did, and REVIEW MEASURED THAT IT CANNOT WORK; this is the load-bearing correction in this plan (see F-9, F-10). Two facts make that table the wrong home, and the second one is fatal:
  - THE RULE IS NOT IN THE COLLISIONS PASS AT ALL. Measured on the exact fixture shape above: `check_collisions(root)` returns ZERO findings, while `check_types(root, ["all"])` returns the one `check.identity-absent-from-name`. The rule comes from `check_name_identity`, which rides the types sweep.
  - THE TABLE'S DETAIL COLUMNS ONLY SEE THE COLLISIONS PASS. In `test_one_pass_reports_exactly_the_collisions_present` the haystack is built as `" | ".join(... for d in drift)` where `drift = ce.check_collisions(root)`, so the `required_detail_substrings` and `forbidden_substrings` columns are matched ONLY against collisions output. A `[drift]` needle can therefore NEVER match there, leaving the row able to assert the RULE ID alone.
  - AND A RULE-ID-ONLY ASSERTION IS VACUOUS, which is why this matters rather than being a placement quibble. Measured: under the E-02 mutation the SAME rule id is still reported (only the bucket prefix flips `[drift]` -> `[legacy]`), so a rule-id-only row passes IDENTICALLY with and without the branch and E-02's mutant would NOT kill it. Review ran both shapes: the detail-asserting test passes clean and FAILS mutated; the rule-id-only row passes BOTH.

  FOLLOW `SetidLengthTests`' PRECEDENT, which is the in-module pattern for a non-collisions rule: it drives its own rule function directly (`ce.check_setid_length(root)`) over a small tree and asserts outcomes. This is NOT the dedicated 585-line module OQ-01 rightly refuses to recreate; it is a few assertions in the surviving module.
  - Depends on: none
  - Expected outcome: `tests/test_check_engine.py` carries a test that calls `check_name_identity` on the drift fixture and asserts the `[drift]` marker; it passes, and (per E-02) fails under the mutation. Measured at review on this exact fixture: `check_name_identity(root, include_retired=True)` returns exactly one `check.identity-absent-from-name` whose detail begins `[drift] declared \`Set: topic\` is absent from an otherwise MODERN id6-clustered filename`.
  - Execution state: pending

- [ ] E-02 Prove the new test is not vacuous by MUTATION rather than by assertion: with E-01's test in place, confirm that neutering the `drift` branch in `check_engine._identity_finding` (the `elif modern:` arm that sets `bucket = "drift"`) makes the new test FAIL, then confirm the tracked module is byte-unchanged. Record the failing node id and the clean `git status --porcelain` for that module as the evidence.

  A WORKING IN-MEMORY MECHANISM IS ALREADY KNOWN, SO DO NOT EDIT THE TRACKED MODULE. `agent_workflows/check_engine.py` is deliberately OUTSIDE this plan's `- Scope-Paths:`, other pending plans declare it, and a write-then-revert can race a co-worker while a failed revert leaves the repository's rule mutated with the suite still green. Review performed this mutation successfully by rebinding the function and forcing the `modern` argument False, which makes the `elif modern:` arm unreachable and routes the finding into the `legacy` bucket:

      orig = ce._identity_finding
      ce._identity_finding = lambda rt, p, f, v, ir, m, s: orig(rt, p, f, v, ir, False, s)

  Use `mock.patch.object` or a pytest plugin. If no in-memory route works, state that plainly rather than editing the tracked file.

  THE MUTANT MUST KILL THE TEST ON THE BUCKET, NOT ON THE RULE ID, and this is the check that makes E-02 meaningful. Measured at review: under this mutation `check_name_identity` STILL returns exactly one `check.identity-absent-from-name`, so a test asserting only the rule id survives the mutant. Only the `[drift]` detail assertion dies (the detail becomes `[legacy] declared \`Set: topic\` is absent from this pre-id6-grammar filename ...`). So if the mutant does NOT kill E-01's test, the defect is in E-01's assertions, not in the mutation: fix the assertion rather than concluding the branch is covered.
  - Depends on: E-01
  - Expected outcome: the mutant kills the new test (a named failing node id whose failure names the missing `[drift]` marker), and `git status --porcelain agent_workflows/check_engine.py` is empty afterwards.
  - Execution state: pending

### Task group 2: correct only the provably incidental mismatches

- [ ] E-03 Correct the four `tests/test_find_filters.py` fixture filenames whose setid segment contradicts their own declared `- Set:`, so each fixture carries only the property its test asserts. These are the clearest incidental members of the census: `20260927-spc001-01-spc001-one.spec.md` declares `- Set: setalpha`, `spc002` declares `setbeta`, `spc003` declares `setalpha`, and `20260927-rel001-01-rel001-release.release.md` declares `- Set: setrel`, i.e. each repeats its own id6 in the setid slot instead of its Set. Rename each to carry its declared setid, leaving every assertion and every declared `- Set:` value unchanged.
  THIS MODULE IS THE RIGHT ONE TO CORRECT AND THE REASON IS MEASURABLE. Its own sibling fixtures in the SAME `setUp` already do it correctly (the backlog fixtures are named `20260927-setgamma-01-bkl001-item-one.backlog.md`, i.e. setid-in-the-setid-slot), so the four are an internal inconsistency rather than a convention. And the tests resolve their Sets from METADATA, so the rename is behavior-preserving: verified at authoring by making exactly this rename and running the module, which reported `11 passed`.
  - Depends on: none
  - Expected outcome: `tests/test_find_filters.py` passes unchanged in assertions; no fixture in it declares a `- Set:` contradicting its own filename.
  - Execution state: pending

- [ ] E-04 Record the census in a short comment beside the new test so the next reader does not re-derive it: 36 fixtures across 14 modules currently declare a `- Set:` contradicting their own filename, the large majority are harmless because their module asserts nothing about setid resolution, and this plan deliberately corrects only `test_find_filters.py`'s four. Name the two classes that must NOT be "fixed": the deliberate legacy-name traps, and the orchestrator fixtures whose setid differs by construction.
  NAME THE DELIBERATE CASES EXPLICITLY, because a future sweep will otherwise break them. `tests/test_check_engine.py`'s `20260101-1357-01-assess-bugs.ipd.md` row is a legacy `YYYYMMDD-HHMM-NN-<slug>` name whose HHMM occupies the setid segment ON PURPOSE (its `why` already explains the mass-flagging trap, and its expected set already contains `check.identity-absent-from-name` twice). `tests/test_orchestrator_shape_composed.py`'s `_make_orchestrator_doc` emits `- Set: set{id6}` while its files are named `20260924-setgod-00-god001-good.ipd.md`, so the mismatch is generated by the helper's own formula and is incidental to a shape-gate test that never resolves a Set.
  - Depends on: E-01
  - Expected outcome: the census and both do-not-touch classes are recorded in the test file, so a later sweep has the reasoning rather than only the count.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The rule that reports this shape is `check_engine.check_name_identity`, registered as `check.identity-absent-from-name` at `warning` severity against invariant `I-09`. It classifies each finding into one of FOUR buckets in `check_engine._identity_finding`: `non-identifier`, `artifact`, `drift` (the `elif modern:` arm), and `legacy`. The backlog item's shape is precisely the `drift` bucket.
- THE `drift` BUCKET HAS NO COVERAGE ANYWHERE. `rg -l "identity-absent|name_identity"` over `tests/` matches exactly ONE file, `tests/test_check_engine.py`, and every one of its three matches is the legacy-trap row plus its constant definition; none asserts `drift`. The dedicated module `tests/test_name_identity_report.py` that `3i6rso` wrote to cover all four buckets was DELETED (585 lines) by commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests".
- THE ONLY LIVE MEMBER CLASS IS GONE TOO, so a fixture is the sole possible coverage. `aw check all --agent` on this tree reports `findings: 2` (`check.name-nonconformant` on one backlog item, `check.system-layout-missing`), and ZERO `check.identity-absent-from-name`. `3i6rso`'s own V-01 recorded the `drift` bucket as empty on the live tree at its execution too, so it was always fixture-only.
- `CollisionTests.COLLISIONS` rows are 6-tuples `(case, files, exact_expected_rules, required_detail_substrings, forbidden_substrings, why)`, and `test_one_pass_reports_exactly_the_collisions_present` asserts the FULL sweep (`check_collisions` AND `check_types(root, ["all"])`), so a row's expected tuple must list incidental findings as well: a synthetic spec adds `attention.history-missing`, and a placeholder-free `draft` plan adds `check.ipd-draft-ready-to-review`.
- The module's fixture builders are `_plan_text(id6, setid="demo", desc=None, status="approved")`, `_spec_text(...)` and `_walk_text(id6=None)`, with tree roots `PLANS = ".aw/records/plans/pending"`, `SPECS = ".aw/records/specs"` and `WALK = ".aw/records/walkthroughs"`. `_plan_text` takes `setid` independently of the filename, which is exactly why a row can express the drift shape.
- `tests/support.py` holds the shared plan-fixture builder `ready_plan_text(..., set_name="demo", ...)` used across modules; it also takes the setid independently of any filename, so the mismatch class is reachable from the shared helper and not only from private ones.
- THE CENSUS, measured rather than estimated: a `pytest_sessionfinish` probe that intercepted every artifact-named file written during a full serial run recorded 36 distinct fixtures whose filename setid segment disagrees with their declared `- Set:`, across 14 modules (`test_status_set.py` 8, `test_ipd_lint.py` 4, `test_history_order.py` 5, `test_find_filters.py` 4, `test_orchestrator_shape_composed.py` 3, `test_run_selection_policy.py` 2, `test_runner_active_conflict.py` 2, `test_backlog_handoff_close.py` 2, and one each in `test_check_engine.py`, `test_hostdedup_third_host.py`, `test_carrier_reverse_lookup.py`, `test_graduation_forward_links.py`).
- MOST OF THE 36 ARE HARMLESS, AND THE TEST IS WHETHER THE MODULE RESOLVES A SET. None of the 14 modules calls `check_name_identity`, `check_collisions` or `check_types` (grepped per file, all zero), so none of these fixtures is currently evaluated against the name-vs-metadata rule. That is why this plan corrects one module rather than 14: a rename in a module that never resolves a Set is churn.
- `tests/fixtures/` contains NO artifact-named `.ipd.md`/`.spec.md`/`.backlog.md` files at all (`git ls-files tests/fixtures/` shows goldens, JSON and `conforming-orchestrator.md`), so the census is entirely about fixtures constructed at runtime, and there is no static fixture tree to sweep.

## Findings

| Id | Finding | Evidence | Consequence |
|---|---|---|---|
| F-1 | The rule's `drift` branch is fully unguarded: neutering it leaves the ENTIRE suite green. | Replaced `elif modern:` with `elif modern and False:` in `check_engine._identity_finding`; the four `check_engine` modules reported `85 passed` and a full `python3 -m pytest` reported `3158 passed, 2 skipped`. Module restored and re-verified clean. | This, not the cosmetic mismatch, is the defect worth closing. A future refactor can delete the branch silently. |
| F-2 | The coverage was not missing by design; it was deleted by a suite trim. | `git log --all -- tests/test_name_identity_report.py` shows it ADDED by `46fd3754` (findtier `3i6rso`) and DELETED by `19313eed` (`585 deletions`). | Restoring a small fixture-driven row is a repair of an accidental loss, not new scope. |
| F-3 | The census is 36 fixtures over 14 modules, and it was measured, not estimated. | A write-intercepting pytest plugin run over a full serial suite emitted 36 distinct `(filename, declared_set, filename_setid)` records. | The item's "worth a broader sweep" is answered with a number a reviewer can dispute. |
| F-4 | Correcting the four `test_find_filters.py` fixtures is behavior-preserving. | Applied exactly the four renames and ran the module: `11 passed`. Reverted. | E-03 is safe and its evidence already exists. |
| F-5 | `test_find_filters.py` is internally inconsistent, which is what makes its four incidental rather than conventional. | In one `setUp`, specs/release repeat their id6 in the setid slot (`20260927-spc001-01-spc001-one.spec.md` declaring `- Set: setalpha`) while backlog fixtures do it correctly (`20260927-setgamma-01-bkl001-item-one.backlog.md`). | The fix direction is unambiguous: follow the module's own correct sibling. |
| F-6 | At least two classes of mismatch are DELIBERATE and must not be swept. | `tests/test_check_engine.py`'s `20260101-1357-01-assess-bugs.ipd.md` legacy row exists to hold the mass-flagging line and expects `check.identity-absent-from-name` twice; `test_orchestrator_shape_composed._make_orchestrator_doc` emits `- Set: set{id6}` by formula. | A blind 36-file sweep would break the legacy trap. E-04 records this. |
| F-7 | The live tree has no member of this population, so fixtures are the only coverage route. | `aw check all --agent` reports `findings: 2`, neither being `check.identity-absent-from-name`. | Confirms a live-corpus assertion would be vacuous. |
| F-8 | Three suite failures exist at HEAD and are unrelated to this plan. | On an unmodified tree, `python3 -m pytest -o addopts="" -p no:xdist` reported `3 failed, 3360 passed`, all three in installer deep-cleanup / subparser-description tests. The bare configured run (`python3 -m pytest`) reports `3158 passed, 2 skipped`, because those three are among the 205 deselected. RE-VERIFIED at review: the same three fail by node id (`test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw`, `test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, `test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory`), and the bare run is green at `3246 passed, 2 skipped` (the total drifted from 3158, exactly as this plan warns). | The executor must use the bare run as its baseline and must not attribute these to its own work. |
| F-9 | **REVIEW FINDING: `check.identity-absent-from-name` IS NOT PRODUCED BY THE COLLISIONS PASS, so `CollisionTests.COLLISIONS`' detail columns can never see it.** The table runner builds its needle haystack from `drift = ce.check_collisions(root)` and matches `required_detail_substrings`/`forbidden_substrings` against THAT only, while it compares the expected RULE set against `ce.check_types(root, ["all"])`. Measured on the exact drift fixture E-01 prescribes: `check_collisions` returns 0 findings and `check_types(["all"])` returns the 1 `check.identity-absent-from-name`. So a row in that table cannot assert the `[drift]` bucket marker at all; it can only assert the rule id. | Review probe printing both passes over the fixture (`check_collisions findings: 0`; `check_types(['all']) findings: 1 check.identity-absent-from-name [drift] ...`) and confirming `'[drift]' in coll_haystack` is False; read of the runner's `haystack = " | ".join(... for d in drift)` line. |
| F-10 | **REVIEW FINDING: A RULE-ID-ONLY ASSERTION IS MUTATION-INSENSITIVE, so E-01-in-the-table and E-02 were JOINTLY UNSATISFIABLE.** Under E-02's own mutation the rule STILL fires with the SAME id; only the bucket prefix in the detail flips from `[drift]` to `[legacy]`. So the table row E-01 originally specified would have passed identically with and without the `drift` branch, E-02's mutant would have failed to kill it, and the plan would have closed its coverage hole with a test that proves nothing. Review ran both candidate shapes: the detail-asserting test PASSES clean and FAILS mutated (mutation-sensitive); the rule-id-only shape PASSES BOTH (vacuous). This is why E-01 was moved out of the table and now asserts the `[drift]` marker directly. | Review probe running both shapes under `ce._identity_finding` rebound to force `modern=False`: detail-asserting -> `unmutated: PASS` / `mutated: FAIL -> no [drift] bucket in: [legacy] declared ...`; rule-id-only -> `unmutated: PASS (rules=['check.identity-absent-from-name'])` / `mutated: PASS (rules=['check.identity-absent-from-name'])`. |
| F-11 | **REVIEW CONFIRMATION: F-1's central claim reproduces exactly, and the mutation is genuinely observable.** With `_identity_finding` rebound in memory to make the `elif modern:` arm unreachable, a BARE `python3 -m pytest` reported `3246 passed, 2 skipped`, identical to the unmutated baseline, so the branch is confirmed unguarded on the current tree. The mutation is not a silent no-op: on a synthetic fixture the unmutated rule emits `[drift] ...` and the mutated one emits `[legacy] ...`, both as a single `check.identity-absent-from-name` at `warning`. | Two bare suite runs (baseline and with a `pytest_configure` plugin rebinding `_identity_finding`), both `3246 passed, 2 skipped`; probe printing the unmutated and mutated detail for the same fixture. The tracked module was never written: `git status --porcelain` empty throughout. |

## Proposed changes (ordered, validatable)

1. Add a focused `drift`-bucket test to `tests/test_check_engine.py` that drives `check_name_identity` directly and asserts the `[drift]` marker in the detail (E-01, per F-9 and F-10, which measure that the COLLISIONS table cannot express this assertion).
2. Prove the test kills a mutant of the `drift` branch, without editing the tracked module (E-02).
3. Rename the four `test_find_filters.py` fixtures to carry their declared setid (E-03).
4. Record the census and the two do-not-touch classes beside the new test (E-04).

## Deferred / out of scope (with reason)

- THE OTHER 32 CENSUS MEMBERS ARE DELIBERATELY NOT RENAMED. None of their modules resolves a Set through `check_engine` or the selector rules (measured: zero references per module), so renaming them changes no assertion and no outcome; it is churn across 13 files in a shared checkout. If a future plan makes one of those modules resolve a Set, that plan should correct its own fixtures then.
- NO CHANGE TO `agent_workflows/check_engine.py`. The rule behaves correctly; only its coverage was lost. The module is outside `- Scope-Paths:` on purpose, and E-02 is explicitly forbidden from editing it.
- NO NEW CHECK RULE, and specifically no rule asserting that a FIXTURE's name matches its metadata. The existing `check.identity-absent-from-name` already covers tracked records, and test fixtures are written to temp directories that no sweep reaches.
- NO ATTEMPT TO RESTORE THE DELETED 585-LINE MODULE WHOLESALE. Most of it covered buckets that either have live members or were pinned structurally, and the trim commits that removed it were deliberate policy (AGENTS.md forbids code-pinning tests). Only the behavioral `drift` coverage is restored, as a small focused test in the surviving module (NOT as a row in `CollisionTests.COLLISIONS`, which F-9 measures cannot express the bucket assertion).
- THE OTHER THREE BUCKETS (`non-identifier`, `artifact`, `legacy`) GAIN NO NEW COVERAGE HERE. The `legacy` bucket is exercised incidentally by the existing table row, and review did not measure whether `non-identifier` and `artifact` have live members or tests; this plan's subject is the ONE bucket F-1 proves is unguarded. Recorded so nobody reads it as a claim that all four buckets are now covered.

## Scope check

- Over-scope: none. Both files in `- Scope-Paths:` receive changes (`tests/test_check_engine.py` for E-01/E-02/E-04, `tests/test_find_filters.py` for E-03). Note that after the review correction E-01 adds a NEW focused test rather than a row in the existing `COLLISIONS` table, which touches the same file and does not widen the fence; it also REDUCES the risk of colliding with the concurrent plan `tl2b2r` that declares this module, since a new test is additive where a table row edits shared data.
- Under-scope: the 32 census members in 13 other modules are named and deliberately deferred above, with the measured reason (their modules resolve no Set). `agent_workflows/check_engine.py` is read and mutation-tested but must end byte-unchanged, so it is correctly absent.

## Required tests / validation

- The BARE configured suite (`python3 -m pytest`), before and after, with the `N passed` summary pasted and the failure-set delta stated BY NODE ID against the executor's own measured baseline. Do not add flags: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Authoring baseline was `3158 passed, 2 skipped` and review measured `3246 passed, 2 skipped` at `bf3cf2d7`; re-measure rather than asserting either figure.
- The four `check_engine` test modules and `tests/test_find_filters.py` run directly, with output pasted.
- THE MUTATION RESULT, which is the only evidence that distinguishes a real test from a decorative one: the new test must FAIL when the `drift` branch is neutered, and the named failing node id must be pasted, AND the failure must name the missing `[drift]` marker rather than a rule-set mismatch. A test that passes both with and without the branch has added nothing; review measured that a rule-id-only assertion is exactly such a test (F-10).
- `git status --porcelain agent_workflows/check_engine.py` empty after E-02, proving the mutation left no residue in this shared checkout.
- `aw ipd lint --phase pre-transition` conforming, and `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change is expected. This plan restores coverage for behavior an approved rule already implements and does not alter the rule, its severity, or its registration, so no contract moves.

The census and the two do-not-touch classes ARE documentation and must land in the test file itself (E-04) rather than only in this plan: a plan in `executed/` is not where the next person sweeping fixtures will look, and the failure mode being prevented is precisely a well-intentioned blind sweep that breaks the legacy trap.

If the executor finds that the deleted `tests/test_name_identity_report.py` is being restored wholesale by another pending plan, that supersedes E-01's approach and should be reported rather than duplicated.

## Open questions

### OQ-01: Should the restored coverage live in `CollisionTests.COLLISIONS` or in a new dedicated module?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us (re-resolved at review)
- Resolution or deferral rationale: NEITHER, AND THE ORIGINAL ANSWER WAS FALSIFIED ON MECHANISM AT REVIEW. The original resolution said "IN THE EXISTING TABLE" and reasoned from the table's docstring. That reasoning was wrong about which pass produces the rule, and the error was load-bearing rather than stylistic: `CollisionTests.COLLISIONS`' detail columns are matched ONLY against `check_collisions` output, and `check.identity-absent-from-name` comes from `check_name_identity` on the TYPES sweep, so the table literally cannot assert the `[drift]` bucket (F-9). A row there could assert the rule id alone, which is mutation-INSENSITIVE because the mutant still emits the same rule id under a different bucket (F-10), so E-01 and E-02 could not both have been satisfied. The correct answer is the THIRD option neither branch of the question offered: a SMALL FOCUSED TEST IN THE SAME SURVIVING MODULE that drives `check_name_identity` directly and asserts the `[drift]` marker, following `SetidLengthTests`' established precedent for a non-collisions rule. This keeps the original resolution's valid half intact, namely that re-creating the deleted 585-line module would walk back into the policy of trim commits `19313eed` and `80db6750`; a handful of assertions is not that module. The legacy row's presence in the table is still correct and E-04 still documents it without altering it. Verified at review by running both candidate shapes and measuring which one the mutant kills.

### OQ-02: Should this plan correct all 36 census members?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, AND THE TEST IS WHETHER THE MODULE RESOLVES A SET. Measured per module, none of the 14 calls `check_name_identity`, `check_collisions` or `check_types`, so in 13 of them the mismatch cannot affect any assertion and a rename is pure churn across a shared checkout. `test_find_filters.py` is corrected anyway because it is INTERNALLY inconsistent (F-5): its own backlog fixtures put the setid in the setid slot while its specs and release repeat their id6, so the four are a local slip against the module's own convention. Two further classes are affirmatively left alone because their mismatch is load-bearing or generated (F-6). Note the honest limit: since nothing evaluates those 32, this plan cannot claim they are harmless in some future refactor; it claims only that correcting them today changes no outcome, and E-04 leaves the census behind so the judgement can be revisited with the number in hand.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) paste the new test's SOURCE as committed and its PASSING node id and output. (b) QUOTE the assertion that checks the detail contains `[drift]`, and paste the ACTUAL finding detail observed, showing the `[drift]` bucket prefix and the declared `Set: topic`. A test that passes on a `legacy` or `artifact` finding asserts the wrong bucket and leaves the gap open. (c) CONFIRM the test drives `check_name_identity` (or the full types sweep) DIRECTLY and is NOT a row in `CollisionTests.COLLISIONS`; a row there FAILS V-01, because F-9 measures that the table's detail columns see only `check_collisions` output, where this rule never appears, so the bucket could not be asserted and F-10 measures the surviving rule-id-only assertion to be mutation-insensitive. (d) CONFIRM the test asserts the rule set is exactly `[check.identity-absent-from-name]` so an unexpected extra finding is not silently tolerated.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: (a) paste the FAILING node id and the assertion output with the `drift` branch neutered, then the passing run unmutated, then `git status --porcelain agent_workflows/check_engine.py` showing EMPTY output. (b) STATE which mechanism was used (in-memory rebind / `mock.patch.object` / pytest plugin / throwaway tree copy) and confirm the tracked module was never written. If the tracked module had to be edited, say so explicitly and name the window during which it was mutated; do not present a clean final `git status` as proof it never happened. (c) CONFIRM THE MUTANT DIED ON THE BUCKET, NOT ON THE RULE ID, by pasting the failure message and showing it names the missing `[drift]` marker. This is the load-bearing half: review measured that under this mutation the rule STILL reports the same id, so a failure that instead reads "expected rule set X, got Y" means the mutation changed something else and the proof does not hold. (d) If the mutant does NOT kill the test, do NOT record V-02 as verified and do NOT conclude the branch is covered: fix E-01's assertions, because F-10 measures that exactly this shape of test survives the mutant.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff --stat tests/test_find_filters.py`, the four old and new filenames side by side, and the module's passing output. Confirm by inspection that NO declared `- Set:` value and NO assertion changed, i.e. the diff touches filenames only. Then paste a re-run of the census probe (or an equivalent targeted check) showing those four filenames are no longer members, so the correction is measured rather than assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the census text as it appears in the test file, and confirm it names BOTH do-not-touch classes with their reasons (the legacy HHMM trap row and the `_make_orchestrator_doc` formula). Paste the legacy row's expected-rules tuple UNCHANGED as proof E-04 documented that row without altering it. Also paste the BARE `python3 -m pytest` summary before and after with the failure-set delta stated by node id against YOUR OWN measured baseline, and note that the three installer/subparser failures visible under `-o addopts=""` are pre-existing (F-8) and not this plan's. DO NOT transcribe any total from this plan: authoring recorded `3158 passed` and review measured `3246 passed, 2 skipped` on a clean tree at `bf3cf2d7`, which is exactly the drift the execution contract warns about. The three pre-existing failures are named by node id in F-8; confirm you observe that same set and no other.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS SMALL AND ITS VALUE IS CONCENTRATED IN E-01/E-02, not in the renames. A reviewer who wants to cut scope should keep the mutation-proven `drift` test and drop E-03, not the reverse: the test closes a real coverage hole in a shipped `check_engine` rule, while the renames are tidiness in a module that resolves Sets from metadata anyway.

WHAT REVIEW CHANGED, because it alters what is being approved. The plan's DIAGNOSIS was confirmed independently: with the `drift` arm made unreachable in memory, a bare suite run reported the same `3246 passed, 2 skipped` as the clean baseline, so the branch really is unguarded (F-11). But the plan's chosen REMEDY could not have worked. E-01 originally put the coverage in `CollisionTests.COLLISIONS`, and that table's detail columns are matched only against `check_collisions` output, where this rule never appears (F-9), so the row could assert the rule id alone; under E-02's own mutation the rule still reports that same id and only the bucket prefix changes, so the row would have passed both mutated and clean and E-02 could never have killed it (F-10). The plan would have closed a coverage hole with a test that proved nothing, and reported success. E-01 now adds a focused test that drives `check_name_identity` directly and asserts the `[drift]` marker, which review ran in both arms: it passes clean and fails mutated. OQ-01's "in the existing table" answer is re-resolved accordingly.

IT CARRIES NO `Blocks-Release`, because backlog `0f809c` carries none. The item is `Work-Kind: chore` at `Priority: low` and the maintainer did not gate it; stated so a reader does not assume a gate was dropped. Note that the coverage hole F-1 documents would arguably justify filing a separate `bug`, since a silently unguarded branch is a live defect risk, but this plan does NOT reclassify the item on its own authority: that is a maintainer call, and raising it is the honest action rather than quietly promoting it.

EXECUTION CONTRACT. Commit only the two files in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, and never push. `agent_workflows/check_engine.py` MUST end byte-unchanged: E-02 mutation-tests it and is forbidden from writing it in this shared checkout. Do NOT rename the other 32 census members. Do NOT touch the `20260101-1357-01-assess-bugs.ipd.md` legacy row's filename or its expected set; it reports `check.identity-absent-from-name` twice ON PURPOSE. Do NOT change `_make_orchestrator_doc`'s `- Set: set{id6}` formula. Do NOT re-create `tests/test_name_identity_report.py` wholesale (OQ-01). Do NOT assert against any COUNT recorded in this plan: the suite total and `aw check`'s finding count drift as other agents land work, so measure your own and state it. Run the suite BARE (`python3 -m pytest`); do not pass `-n0`, an extra `-q`, or `-p no:randomly`. Re-locate every symbol by NAME rather than by any line number, and re-read the other pending plans touching `tests/test_check_engine.py` before starting (`tl2b2r` declares it) since a concurrent edit to the same table must not be overwritten. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the mutation's failing node id and the empty `git status` for `check_engine.py`.
