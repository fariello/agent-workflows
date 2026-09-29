# IPD: Pin the name-versus-metadata Set agreement the trimmed suite left unguarded and correct the surviving fixture mismatches

- Date: 2026-09-28
- Kind: child
- Concern: Backlog `0f809c` asks for a broader sweep of fixture trees for the latent "declared `- Set:` contradicts the filename's setid segment" inconsistency `3i6rso` found in four `check_engine` rows. Measured, the sweep finds 36 such fixtures across 14 test modules, and separately the ONE test module that guarded the rule reporting this shape (`tests/test_name_identity_report.py`, 585 lines) was DELETED by a suite-trim commit, leaving `check_engine.check_name_identity`'s `drift` branch with zero coverage: disabling that branch outright leaves the entire suite green.
- Scope: Restore behavioral coverage for the `drift` bucket (a modern id6-clustered filename whose declared `- Set:`/`- Id:` disagrees with its name) as fixture-driven rows in `tests/test_check_engine.py`, and correct the incidental name-vs-metadata mismatch in the four fixtures where it is genuinely accidental AND the fixture's own module asserts nothing about setid resolution. Does NOT change `check_engine` behavior, does NOT touch the deliberate legacy-trap fixtures, and does NOT mass-rewrite all 36 hits.
- Scope-Paths: tests/test_check_engine.py, tests/test_find_filters.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 0f809c
- Set: findtier
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: y43g6q

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `0f809c`. Step 0 measurement re-aimed the plan: the item asks for a fixture sweep, and the sweep's real finding is that the RULE guarding this shape lost all of its coverage to a suite trim, which is a more valuable gap than the cosmetic mismatches the item anticipated.
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Close backlog `0f809c` on evidence rather than on a cosmetic sweep. The item's literal ask (find other fixture trees carrying a declared `- Set:` that contradicts their own filename) is answered with a measured census: 36 fixtures across 14 modules. But the census's important finding is a COVERAGE hole, not a tidiness problem: the rule that reports this exact shape, `check_engine.check_name_identity`'s `drift` bucket, has no test left anywhere, because the 585-line module that covered it was deleted in a suite trim. This plan restores that coverage as fixture rows in the surviving table, and corrects only the mismatches that are provably incidental.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the lost coverage (the census's real finding)

- [ ] E-01 Add a `drift`-bucket row to `tests.test_check_engine.CollisionTests.COLLISIONS` whose fixture is a MODERN id6-clustered plan filename whose declared `- Set:` disagrees with its own filename setid segment, and expect `check.identity-absent-from-name` to be reported for it. Use the module's existing `_plan_text(id6, setid=...)` helper with a filename whose setid segment differs from the `setid=` argument (the exact shape the backlog item describes: a plan named `...-demo-01-aaa111-p.ipd.md` declaring `- Set: topic`). The row's `why` must state that this row is what `tests/test_name_identity_report.py` used to hold before commit `19313eed` deleted it, that the `drift` bucket is the ONLY one of the rule's four buckets with no live member on this tree (so a fixture is the only possible coverage), and that disabling the branch was measured to leave the whole suite green.
  RE-DRIVE THE EXPECTED-RULES TUPLE RATHER THAN COPYING ONE FROM THIS PLAN. The runner compares the FULL sweep's finding set exactly (`test_one_pass_reports_exactly_the_collisions_present` asserts both `check_collisions` and `check_types(root, ["all"])`), so the tuple must include every incidental finding the fixture trips. Measured at authoring on an isolated tree, `check_name_identity(repo, include_retired=True)` on exactly this shape returns one `check.identity-absent-from-name` whose detail begins `[drift] declared \`Set: topic\` is absent from an otherwise MODERN id6-clustered filename`; the full-sweep set on a table fixture will differ from that isolated measurement, so measure it in place.
  - Depends on: none
  - Expected outcome: `COLLISIONS` carries a row asserting the `drift` bucket; `test_one_pass_reports_exactly_the_collisions_present` passes with it.
  - Execution state: pending

- [ ] E-02 Prove the new row is not vacuous by MUTATION rather than by assertion: with E-01's row in place, confirm that neutering the `drift` branch in `check_engine._identity_finding` (the `elif modern:` arm that sets `bucket = "drift"`) makes the new row FAIL, then restore the module byte-for-byte. Record the failing node id and the restored-clean `git status --porcelain` for that module as the evidence.
  THE MUTATION MUST BE MADE IN MEMORY OR IN A THROWAWAY COPY, NOT BY EDITING THE TRACKED MODULE IN THIS SHARED CHECKOUT. `agent_workflows/check_engine.py` is deliberately OUTSIDE this plan's `- Scope-Paths:`, other pending plans declare it, and a write-then-revert can race a co-worker while a failed revert leaves the repository's rule mutated with the suite still green. Prefer monkeypatching the predicate inside the test process, or copying the tree to a temp directory; if no in-memory route works, state that plainly rather than editing the tracked file.
  - Depends on: E-01
  - Expected outcome: the mutant kills the new row (a named failing node id), and `git status --porcelain agent_workflows/check_engine.py` is empty afterwards.
  - Execution state: pending

### Task group 2: correct only the provably incidental mismatches

- [ ] E-03 Correct the four `tests/test_find_filters.py` fixture filenames whose setid segment contradicts their own declared `- Set:`, so each fixture carries only the property its test asserts. These are the clearest incidental members of the census: `20260927-spc001-01-spc001-one.spec.md` declares `- Set: setalpha`, `spc002` declares `setbeta`, `spc003` declares `setalpha`, and `20260927-rel001-01-rel001-release.release.md` declares `- Set: setrel`, i.e. each repeats its own id6 in the setid slot instead of its Set. Rename each to carry its declared setid, leaving every assertion and every declared `- Set:` value unchanged.
  THIS MODULE IS THE RIGHT ONE TO CORRECT AND THE REASON IS MEASURABLE. Its own sibling fixtures in the SAME `setUp` already do it correctly (the backlog fixtures are named `20260927-setgamma-01-bkl001-item-one.backlog.md`, i.e. setid-in-the-setid-slot), so the four are an internal inconsistency rather than a convention. And the tests resolve their Sets from METADATA, so the rename is behavior-preserving: verified at authoring by making exactly this rename and running the module, which reported `11 passed`.
  - Depends on: none
  - Expected outcome: `tests/test_find_filters.py` passes unchanged in assertions; no fixture in it declares a `- Set:` contradicting its own filename.
  - Execution state: pending

- [ ] E-04 Record the census in the new row's `why` (or a short comment beside it) so the next reader does not re-derive it: 36 fixtures across 14 modules currently declare a `- Set:` contradicting their own filename, the large majority are harmless because their module asserts nothing about setid resolution, and this plan deliberately corrects only `test_find_filters.py`'s four. Name the two classes that must NOT be "fixed": the deliberate legacy-name traps, and the orchestrator fixtures whose setid differs by construction.
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
| F-8 | Three suite failures exist at HEAD and are unrelated to this plan. | On an unmodified tree, `python3 -m pytest -o addopts="" -p no:xdist` reported `3 failed, 3360 passed`, all three in installer deep-cleanup / subparser-description tests. The bare configured run (`python3 -m pytest`) reports `3158 passed, 2 skipped`, because those three are among the 205 deselected. | The executor must use the bare run as its baseline and must not attribute these to its own work. |

## Proposed changes (ordered, validatable)

1. Add a `drift`-bucket row to `CollisionTests.COLLISIONS` (E-01), re-driving its expected-rules tuple in place.
2. Prove the row kills a mutant of the `drift` branch, without editing the tracked module (E-02).
3. Rename the four `test_find_filters.py` fixtures to carry their declared setid (E-03).
4. Record the census and the two do-not-touch classes beside the new row (E-04).

## Deferred / out of scope (with reason)

- THE OTHER 32 CENSUS MEMBERS ARE DELIBERATELY NOT RENAMED. None of their modules resolves a Set through `check_engine` or the selector rules (measured: zero references per module), so renaming them changes no assertion and no outcome; it is churn across 13 files in a shared checkout. If a future plan makes one of those modules resolve a Set, that plan should correct its own fixtures then.
- NO CHANGE TO `agent_workflows/check_engine.py`. The rule behaves correctly; only its coverage was lost. The module is outside `- Scope-Paths:` on purpose, and E-02 is explicitly forbidden from editing it.
- NO NEW CHECK RULE, and specifically no rule asserting that a FIXTURE's name matches its metadata. The existing `check.identity-absent-from-name` already covers tracked records, and test fixtures are written to temp directories that no sweep reaches.
- NO ATTEMPT TO RESTORE THE DELETED 585-LINE MODULE WHOLESALE. Most of it covered buckets that either have live members or were pinned structurally, and the trim commits that removed it were deliberate policy (AGENTS.md forbids code-pinning tests). Only the behavioral `drift` coverage is restored, as a row in the surviving table.

## Scope check

- Over-scope: none. Both files in `- Scope-Paths:` receive changes (`tests/test_check_engine.py` for E-01/E-02/E-04, `tests/test_find_filters.py` for E-03).
- Under-scope: the 32 census members in 13 other modules are named and deliberately deferred above, with the measured reason (their modules resolve no Set). `agent_workflows/check_engine.py` is read and mutation-tested but must end byte-unchanged, so it is correctly absent.

## Required tests / validation

- The BARE configured suite (`python3 -m pytest`), before and after, with the `N passed` summary pasted and the failure-set delta stated BY NODE ID against the executor's own measured baseline. Do not add flags: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Authoring baseline was `3158 passed, 2 skipped`; re-measure rather than asserting that figure.
- The four `check_engine` test modules and `tests/test_find_filters.py` run directly, with output pasted.
- THE MUTATION RESULT, which is the only evidence that distinguishes a real test from a decorative one: the new row must FAIL when the `drift` branch is neutered, and the named failing node id must be pasted. A row that passes both with and without the branch has added nothing.
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
- Owner: none
- Resolution or deferral rationale: IN THE EXISTING TABLE, resolved from repository evidence. The deleted module was removed by two deliberate trim commits (`19313eed`, `80db6750`) whose stated purpose was cutting the suite from 9,136 tests to under 2,000 and deleting 366 structure-pinning tests; re-creating a dedicated 585-line module would walk directly back into the policy that removed it. `CollisionTests.COLLISIONS` is the right home on its own terms: it already carries a `check.identity-absent-from-name` expectation (the legacy row), its docstring states that the rules "are produced by a SINGLE pass of `check_collisions` over every supported type, which is why they belong in one table", and the `drift` row is one more row in a table built for exactly this. If a reviewer prefers a dedicated module, that is a style call with no correctness consequence, and only E-01/E-04's placement changes.

### OQ-02: Should this plan correct all 36 census members?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, AND THE TEST IS WHETHER THE MODULE RESOLVES A SET. Measured per module, none of the 14 calls `check_name_identity`, `check_collisions` or `check_types`, so in 13 of them the mismatch cannot affect any assertion and a rename is pure churn across a shared checkout. `test_find_filters.py` is corrected anyway because it is INTERNALLY inconsistent (F-5): its own backlog fixtures put the setid in the setid slot while its specs and release repeat their id6, so the four are a local slip against the module's own convention. Two further classes are affirmatively left alone because their mismatch is load-bearing or generated (F-6). Note the honest limit: since nothing evaluates those 32, this plan cannot claim they are harmless in some future refactor; it claims only that correcting them today changes no outcome, and E-04 leaves the census behind so the judgement can be revisited with the number in hand.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new row as committed AND the passing output of `test_one_pass_reports_exactly_the_collisions_present`. Paste the row's expected-rules tuple together with the measurement that produced it (the full-sweep finding set for that fixture), and state explicitly that it was re-driven in place rather than copied from this plan. Paste the actual finding detail showing it carries the `[drift]` bucket prefix, since a row that passes on a `legacy` or `artifact` finding would assert the wrong bucket and leave the gap open.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the FAILING node id and the assertion output with the `drift` branch neutered, then the passing run after restoration, then `git status --porcelain agent_workflows/check_engine.py` showing EMPTY output. State which mechanism was used (in-memory monkeypatch or a throwaway tree copy) and confirm the tracked module was never written. If the tracked module had to be edited, say so explicitly and name the window during which it was mutated; do not present a clean final `git status` as proof it never happened.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff --stat tests/test_find_filters.py`, the four old and new filenames side by side, and the module's passing output. Confirm by inspection that NO declared `- Set:` value and NO assertion changed, i.e. the diff touches filenames only. Then paste a re-run of the census probe (or an equivalent targeted check) showing those four filenames are no longer members, so the correction is measured rather than assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the census text as it appears in the test file, and confirm it names BOTH do-not-touch classes with their reasons (the legacy HHMM trap row and the `_make_orchestrator_doc` formula). Paste the legacy row's expected-rules tuple UNCHANGED as proof E-04 documented that row without altering it. Also paste the BARE `python3 -m pytest` summary before and after with the failure-set delta stated by node id against your own baseline, and note that the three installer/subparser failures visible under `-o addopts=""` are pre-existing (F-8) and not this plan's.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS SMALL AND ITS VALUE IS CONCENTRATED IN E-01/E-02, not in the renames. A reviewer who wants to cut scope should keep the mutation-proven `drift` row and drop E-03, not the reverse: the row closes a real coverage hole in a shipped `check_engine` rule, while the renames are tidiness in a module that resolves Sets from metadata anyway.

IT CARRIES NO `Blocks-Release`, because backlog `0f809c` carries none. The item is `Work-Kind: chore` at `Priority: low` and the maintainer did not gate it; stated so a reader does not assume a gate was dropped. Note that the coverage hole F-1 documents would arguably justify filing a separate `bug`, since a silently unguarded branch is a live defect risk, but this plan does NOT reclassify the item on its own authority: that is a maintainer call, and raising it is the honest action rather than quietly promoting it.

EXECUTION CONTRACT. Commit only the two files in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, and never push. `agent_workflows/check_engine.py` MUST end byte-unchanged: E-02 mutation-tests it and is forbidden from writing it in this shared checkout. Do NOT rename the other 32 census members. Do NOT touch the `20260101-1357-01-assess-bugs.ipd.md` legacy row's filename or its expected set; it reports `check.identity-absent-from-name` twice ON PURPOSE. Do NOT change `_make_orchestrator_doc`'s `- Set: set{id6}` formula. Do NOT re-create `tests/test_name_identity_report.py` wholesale (OQ-01). Do NOT assert against any COUNT recorded in this plan: the suite total and `aw check`'s finding count drift as other agents land work, so measure your own and state it. Run the suite BARE (`python3 -m pytest`); do not pass `-n0`, an extra `-q`, or `-p no:randomly`. Re-locate every symbol by NAME rather than by any line number, and re-read the other pending plans touching `tests/test_check_engine.py` before starting (`tl2b2r` declares it) since a concurrent edit to the same table must not be overwritten. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the mutation's failing node id and the empty `git status` for `check_engine.py`.
