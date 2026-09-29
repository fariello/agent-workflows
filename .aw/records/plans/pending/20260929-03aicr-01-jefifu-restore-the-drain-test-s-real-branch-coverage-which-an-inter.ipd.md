# IPD: Restore the drain test's real branch coverage, which an interim fix silently routed to the unparseable-token path

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `03aicr` reports `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` FAILING on a clean tree because it hardcoded `"dependencies": ["executed:5o1jye"]` against the LIVE checkout and plan `5o1jye` had since executed. THE REPORTED RED IS ALREADY GONE, and it was closed by an UNCARRIED interim commit that introduced a DIFFERENT, quieter defect. Commit `f1b5b9ff` ("test(deps): use synthetic dependency for unsatisfied reason reporting test") swapped the token to `executed:drnprereq`. That string is NOT A LEGAL id6: `runner_shared.ID6_RE` is `^[a-z0-9]{6}$` and `drnprereq` is nine characters, so `runner_shared.parse_dependency_token` returns `None` and `dependency_status_detailed` takes its FAIL-CLOSED `_block(dep, f"{dep}: unparseable dependency token")` branch, `continue`ing BEFORE `edge_satisfied` is ever called. Measured: `edge_satisfied` is invoked ZERO times, and the reason is `'executed:drnprereq: unparseable dependency token'`, not a dependency-resolution reason. So the assertion still passes, and it now passes over the WRONG BRANCH: the test's own docstring and the module docstring's case (c) both claim it pins "drain-shaped ... items render mapped reasons" derived via `dependency_status_detailed`'s resolution path, while what it actually exercises is a malformed-token guard.
- Scope: Make that one test exercise the branch it claims, by pointing its drain dependency at a LEGAL id6 resolved against a SYNTHESIZED repository root under the `tmp_path` the test already receives, so the verdict depends on nothing in the live checkout. Prove the restored coverage with a mutation check that the current form cannot fail. Also drop the now-vestigial `Path(__file__).resolve().parents[1]` live-root reference from that one test. Does NOT touch `agent_workflows/runner_shared.py`, `agent_workflows/render_stream.py`, or `agent_workflows/run_selection_policy.py`: no production behavior is wrong here (`dependency_status_detailed` is CORRECT in every measurement below), and the two adjacent PRODUCTION defects are separately carried by `8mohre` and `csjq81`. Does NOT audit the other tests that reference the live root, and does NOT author the standing convention that governs this class, which plan `kmzude` owns.
- Scope-Paths: tests/test_dependency_block_reporting.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 03aicr
- Blocks-Release: next
- Set: 03aicr
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: jefifu

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `03aicr`. THE ITEM'S HEADLINE SYMPTOM NO LONGER REPRODUCES and the plan says so in F1 rather than asserting a red suite it did not observe: a bare `python3 -m pytest` at lane HEAD `a70cdb6a` reports `3246 passed, 2 skipped`. The item is NOT thereby satisfied, because the interim commit that closed it (`f1b5b9ff`, no plan and no backlog carrier) chose a replacement token that is not a legal id6 and so routed the test to `dependency_status_detailed`'s unparseable-token guard, measured with `edge_satisfied` called zero times (F2). That is the SAME class of defect the item filed, a test whose green does not mean what its docstring says, arriving by a different route, so this plan finishes the item's own SUGGESTED FIX ("point the dependency token at a synthesized artifact under a `tmp_path` repo root") rather than inventing new scope. The item's second suggested option (an id6 that cannot resolve at all) is REJECTED with a measurement in F4, and the rejection is the one authored judgement here.

## Goal

Make `test_drain_and_cascade_mapped_reasons_rendered_once` assert what it says it asserts: that a
drain-shaped item's reason, AS PRODUCED BY `dependency_status_detailed`'s dependency-resolution path,
is rendered exactly once by `render_run_summary_table`. Today it reaches that renderer through a
malformed-token guard instead, so the resolution path it names is untested by it and the test cannot
fail if that path breaks.

Close backlog `03aicr` honestly: its reported red is gone, but the property it wanted protected (a
verdict that does not depend on the live checkout, and a green that means what the docstring claims)
is not yet held.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the current green is over the wrong branch, then move it

- [ ] E-01 REPRODUCE THE THREE MEASUREMENTS THIS PLAN RESTS ON, at execution HEAD, before editing anything, because every one of them is a claim about behavior that could have changed since authoring and the whole plan collapses if any is false. (a) THE ITEM'S REPORTED RED IS GONE: run a bare `python3 -m pytest` and paste the summary line; the authoring baseline is `3246 passed, 2 skipped` at lane HEAD `a70cdb6a`, and the item's `1 failed, 3034 passed, 2 skipped` at `71aee0d3` must NOT reproduce. If it DOES reproduce, STOP and report: the interim commit is not in your tree and this plan's premise is wrong. (b) THE CURRENT TOKEN IS UNPARSEABLE: show `runner_shared.parse_dependency_token("executed:drnprereq")` returning `None`, and show `runner_shared.ID6_RE.pattern` so the nine-versus-six character cause is visible rather than asserted. (c) `edge_satisfied` IS NEVER REACHED: monkeypatch or wrap `runner_shared.edge_satisfied` with a counting spy, call `dependency_status_detailed` on the test's own drain item verbatim, and paste both the call count (baseline `0`) and the returned reason map (baseline `{'executed:drnprereq': 'executed:drnprereq: unparseable dependency token'}`). Do the spying in a throwaway script or an inline `python3 -c`, NOT by adding a test; delete nothing from `tests/` and add nothing to it in this item.
  - Depends on: none
  - Expected outcome: three pasted measurements. (a) a bare-suite summary line with no failure, contradicting the item's report and confirming F1. (b) `None` from `parse_dependency_token`, with `^[a-z0-9]{6}$` shown. (c) an `edge_satisfied` call count of `0` beside the `unparseable dependency token` reason, which is the finding that makes this plan necessary at all.
  - Execution state: pending

- [ ] E-02 POINT THE DRAIN DEPENDENCY AT A LEGAL id6 RESOLVED AGAINST A SYNTHESIZED REPOSITORY ROOT UNDER `tmp_path`, which is the fix backlog `03aicr` itself suggests first and which the test is already equipped for (it takes `tmp_path` and uses it for nothing today). Three coupled edits, all inside `test_drain_and_cascade_mapped_reasons_rendered_once`. FIRST, build the synthetic root: write one plan file under `tmp_path` at `.aw/records/plans/pending/` whose name and `- Id:` carry a SIX-character id6, with a non-`executed` `- Status:`, so the `executed:` edge is legitimately unmet for a REASON THAT IS ABOUT DEPENDENCY RESOLUTION. The worked shape, measured to produce the intended branch, is a file named `20260919-s-01-<id6>-dep.ipd.md` containing `# IPD: dep\n\n- Id: <id6>\n- Status: approved\n`; `tests/test_finalize_sendback.py` already uses exactly this idiom (its `pending / "20260919-s-01-yaxr4i-dep.ipd.md"` write), so follow that precedent rather than inventing a fixture shape. SECOND, set `state_drain["repo"]` to that `tmp_path` root instead of the live checkout, which is what severs the coupling the backlog item filed. THIRD, set the drain item's `"dependencies"` to `["executed:<that id6>"]`. CHOOSE AN id6 THAT IS NOT A REAL PLAN'S, so a future collision cannot resurrect the original bug in reverse; the synthesized root makes a collision harmless, but a distinctive value keeps the intent legible. DO NOT reuse `aaa111`, which the same file already uses for the cascade half of this test and for three other tests, because the drain and cascade halves assert DIFFERENT reason texts and sharing the token invites a copy-paste error that makes one half assert the other's string. DO NOT weaken any assertion: `assert not sat`, the single-diagnostic-line assertion, the `(blocked)` absence, and the `un_reasons[...] in drain_diags[0]` containment all stay, and the last one keeps reading the reason out of the map rather than hardcoding prose, which is what keeps this test from pinning `edge_satisfied`'s exact wording (wording that `csjq81` may legitimately change).
  - Depends on: E-01
  - Expected outcome: the drain half of the test resolves a legal `executed:<id6>` edge against a `tmp_path` root, and the reason now comes from the RESOLUTION path. Authoring baseline for the new reason, to reproduce or correct: `executed:<id6>: external target <id6> is 'approved' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)`. The test passes, and `git diff` shows no assertion removed or relaxed.
  - Execution state: pending

- [ ] E-03 REMOVE THE NOW-VESTIGIAL LIVE-ROOT REFERENCE FROM THIS TEST AND FIX THE DOCSTRING CLAIM IT FALSIFIED, because leaving either in place preserves the coupling this plan exists to remove. The line `repo_root = Path(__file__).resolve().parents[1]` exists ONLY to feed `state_drain["repo"]`, which E-02 repoints, so after E-02 it is either unused or (worse) still silently pointing part of the test at the live tree. Delete it and confirm by `grep` that `parents[` no longer appears in the file. If `Path` becomes unused, drop the import; if it is still used (the cascade half and other tests take `tmp_path: Path` annotations, so it very likely is), KEEP it and say so in V-03 rather than deleting an import the type annotations need. SEPARATELY, the module docstring's case (c) reads "drain-shaped and post-E-01 cascade items render mapped reasons exactly once" and the function docstring repeats it; that claim was FALSE for the drain half under the interim token (E-01(c) measures why). It becomes TRUE under E-02, so do NOT rewrite the claim, but DO make the drain half's mechanism explicit in the test body so the next reader cannot repeat `f1b5b9ff`'s mistake: state in a short comment that the dependency must be a LEGAL SIX-CHARACTER id6 resolved against a synthesized root, and that a malformed token silently diverts to the unparseable-token guard and asserts nothing about resolution. Keep it to a sentence or two; this is a landmine marker, not an essay, and P16's concern is the test's behavior rather than its prose.
  - Depends on: E-02
  - Expected outcome: no `parents[` in `tests/test_dependency_block_reporting.py`; a short comment in the drain half naming the legal-id6 requirement and the guard it would otherwise hit; the `Path` import's fate stated with its reason; the file's other five tests byte-unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE TOKEN GRAMMAR IS SHARED AND STRICT, AND THAT IS WHY `drnprereq` FAILS. `runner_shared.parse_dependency_token` delegates to `ipd_schema.parse_item_dependencies` and, on failure, accepts only a BARE id6 matching `runner_shared.ID6_RE` (`^[a-z0-9]{6}$`). Its docstring is explicit that "nothing is parsed here". So a token's legality is not a local judgement a test can fudge; a nine-character stem is simply not an edge.
- THE UNPARSEABLE BRANCH IS DELIBERATELY FAIL-CLOSED, so it is not a bug that it swallowed the token. `dependency_status_detailed`'s own comment says "an unparseable token is never 'no dependency'. Preflight refuses such a run before any session starts; this is the belt-and-braces path for a hand-edited state.json". The defect is that a test meaning to exercise resolution landed on the belt-and-braces path, not that the path exists.
- `dependency_status_detailed` IS CORRECT IN EVERY MEASUREMENT HERE, which is why `- Scope-Paths:` names no production file. The backlog item already concluded this for the original failure ("`dependency_status_detailed` is CORRECT here and the TEST is wrong"), and it holds for the interim state too: returning `unparseable dependency token` for `executed:drnprereq` is exactly what the function documents.
- THE SYNTHESIZED-ROOT IDIOM ALREADY EXISTS IN THIS TEST TREE, so E-02 copies a precedent rather than inventing a fixture. `tests/test_finalize_sendback.py` writes `20260919-s-01-yaxr4i-dep.ipd.md` containing `- Id: yaxr4i` and `- Status: approved` into a temporary `pending/` and then asserts `["executed:yaxr4i"]` is unsatisfied. That is the same shape E-02 needs, including the detail that a four-line file is enough for `resolve_plan_path` plus `read_front_matter_status`.
- RESOLUTION READS THE DIRECTORY AND THE FIELD, NOT THE QUEUE, which is what makes a `tmp_path` root sufficient. `edge_satisfied`'s `executed:` branch calls `resolve_plan_path(repo, "", edge.id6)` then `plan_bucket`, and its comment records the maintainer ruling of 2026-09-19 that `by_id` is "DELIBERATELY UNREAD" so there is "ONE authority: the plan's directory on disk". A synthesized root therefore fully determines the verdict.
- THE RENDERER CONTRACT THIS TEST GUARDS IS SEPARATE FROM THE REASON'S WORDING. The surviving assertion `un_reasons["executed:<id6>"] in drain_diags[0]` reads the expected text out of the producer's own map, so it pins "rendered once, containing the mapped reason" without pinning prose. That matters because `csjq81` proposes changing exactly that prose (the token is printed twice), and a test hardcoding the string would block it.
- THE NEIGHBOURING CASCADE HALF NEEDS NO `repo` AT ALL, which is worth noting so an executor does not "helpfully" repoint it too. `cascade_dependency_blocked` walks in-queue statuses and never touches disk, and `state_cascade` in this test carries no `repo` key today. Its `aaa111` token is a legal id6 and its reason (`target aaa111 is reviewed`) is composed by the cascade function itself.
- THE SUITE IS RUN BARE AND IS GREEN AT AUTHORING. `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; a bare `python3 -m pytest` at lane HEAD reports `3246 passed, 2 skipped` plus the deselect notice. The item's `3034 passed` count is from an older HEAD, so V-01 must gate on NO NEW failures rather than on an absolute count.
- THE STANDING CONVENTION FOR THIS CLASS OF TEST IS BEING DECIDED ELSEWHERE AND THIS PLAN CONFORMS TO ITS ANSWER IN ADVANCE. Backlog `5mc38x` (now `graduated`) asked whether a test that genuinely depends on the live checkout should skip loudly or synthesize; plan `kmzude` (`- Status: reviewed`, Set `testlocality`) answers "synthesize first" and records that a runtime skip reason is printed ZERO times under this repository's configured `addopts`. E-02 takes the synthesize route, which is that rule's FIRST option, so no dependency edge between the plans is needed.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | backlog `03aicr`; lane HEAD `a70cdb6a` | **THE ITEM'S HEADLINE SYMPTOM DOES NOT REPRODUCE, AND SAYING SO IS PART OF THE JOB.** The item reports `1 failed, 3034 passed, 2 skipped` at HEAD `71aee0d3` with `test_drain_and_cascade_mapped_reasons_rendered_once` red. At lane HEAD the bare suite is GREEN. The item is nonetheless not satisfied, for F2's reason, so this plan neither closes it as a non-issue nor restates a red it did not see. | measured 2026-09-29: bare `python3 -m pytest` -> `3246 passed, 2 skipped, 3 warnings in 53.71s` plus `NOTE: 207 tests were deselected`; `python3 -m pytest tests/test_dependency_block_reporting.py` -> `8 passed`; `git merge-base --is-ancestor f1b5b9ff HEAD` succeeds, with 406 commits since |
| F2 | HIGH | `f1b5b9ff`; `runner_shared.parse_dependency_token`; `runner_shared.ID6_RE` | **THE INTERIM FIX TRADED A LOUD WRONG ANSWER FOR A QUIET ONE: THE TEST NOW PASSES OVER A BRANCH ITS DOCSTRING DOES NOT NAME.** `f1b5b9ff` replaced `executed:5o1jye` with `executed:drnprereq`. `drnprereq` is NINE characters and `ID6_RE` is `^[a-z0-9]{6}$`, so `parse_dependency_token` returns `None`, `dependency_status_detailed` takes `_block(dep, f"{dep}: unparseable dependency token")` and `continue`s, and `edge_satisfied` is NEVER CALLED. The test's `assert not sat` is therefore satisfied by a malformed-input guard, while the module docstring's case (c) claims it pins reasons "derived via `dependency_status_detailed`" for a drain-shaped item. | measured: `parse_dependency_token('executed:drnprereq')` -> `None`, while `'executed:drn999'` -> `ItemDependency(kind='executed', target_type='ipd', status=None, id6='drn999')`; `dependency_status_detailed` -> `(False, ['executed:drnprereq'], {'executed:drnprereq': 'executed:drnprereq: unparseable dependency token'})`; a counting spy over `runner_shared.edge_satisfied` records **0** calls |
| F3 | HIGH | `tests/test_dependency_block_reporting.py` drain half | **THE TEST IS INSENSITIVE TO THE CODE IT CLAIMS TO COVER, WHICH IS THE P16 MUTATION CRITERION FAILING OUTRIGHT.** Replacing `edge_satisfied` wholesale with `lambda ...: (False, "")` (a total destruction of every reason string it composes) leaves the drain half's verdict and reason map BYTE-IDENTICAL, because control flow never reaches it. `GUIDING_PRINCIPLES.md` P16 states the rule this violates: "A test is only valid if breaking the underlying behavior makes the test fail." | measured with `edge_satisfied` monkeypatched to `lambda edge,item,state,by_id: (False, "")`: `dependency_status_detailed` still returns `(False, ['executed:drnprereq'], {'executed:drnprereq': 'executed:drnprereq: unparseable dependency token'})`. This is the exact measurement V-02 must show FLIPPING after E-02 |
| F4 | MEDIUM | backlog `03aicr` suggested fix; `runner_shared.edge_satisfied` | **THE ITEM'S SECOND SUGGESTED OPTION IS THE ONE THAT WENT WRONG, SO THIS PLAN TAKES ITS FIRST AND SAYS WHY.** The item offers either "a synthesized artifact under a `tmp_path` repo root" OR "an id6 that cannot resolve at all so the unmet branch is reached by construction". The second is what `f1b5b9ff` reached for, and it is a trap in two ways. A MALFORMED stem short-circuits before resolution (F2). Even a WELL-FORMED unresolvable id6 reaches only `resolve_plan_path`'s `DriverError` arm, whose reason is a resolver diagnostic, not a dependency verdict, and whose text embeds a configured-path fragment. Only a RESOLVABLE non-executed target exercises the bucket-and-status comparison the drain case is about. | measured against the LIVE root, so both arms are visible: `executed:zzz999` (legal id6, no such plan) -> `"executed:zzz999: Cannot locate IPD zzz999; configured path was "`; a synthesized `tmp_path` root containing `20260919-s-01-drn999-dep.ipd.md` with `- Status: approved` -> `"executed:drn999: external target drn999 is 'approved' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)"`. The second is the drain case's real reason |
| F5 | MEDIUM | `f1b5b9ff` commit metadata | **THE INTERIM FIX WAS UNCARRIED, WHICH IS WHY IT WAS NEVER REVIEWED AND WHY THE ITEM STAYED `open`.** The commit message is a bare `test(deps): use synthetic dependency for unsatisfied reason reporting test` with no plan id6, no `From-Backlog`, and no reference to `03aicr`. Nothing linked the edit to the item it addressed, so the item's own suggested-fix text was never checked against what shipped. Recorded as CONTEXT for why F2 escaped, NOT as an accusation and NOT as scope: this plan does not audit other uncarried commits. | `git show f1b5b9ff --format='%B' --no-patch` -> the single subject line quoted, empty body; `git log --format=... --all -- .aw/records/backlog/open/20260928-03aicr*.md` shows no entry after the item's creation |
| F6 | LOW | `tests/test_dependency_block_reporting.py`; `tests/test_finalize_sendback.py`; `tests/test_run_selection_policy.py` | THE REAL-id6 HABIT IS WIDER THAN THIS ONE TEST, AND THIS PLAN DELIBERATELY DOES NOT SWEEP IT. `test_finalize_sendback.py` uses `yaxr4i` and `test_run_selection_policy.py` uses `zz5yxq`, both real executed plans. NEITHER IS A LIVE-STATE BUG: both SYNTHESIZE their own root or never resolve at all, so their verdicts do not move when a plan executes. Recorded so a reviewer knows the pattern was checked and found harmless elsewhere, and so an executor does not widen scope into a rename sweep whose measured yield here is zero. | `tests/test_finalize_sendback.py` writes its own `pending/20260919-s-01-yaxr4i-dep.ipd.md` under a temporary root before asserting; `tests/test_run_selection_policy.py` passes `unsatisfied_dependencies`/`unsatisfied_dependency_reasons` as literals to renderers and never calls `dependency_status_detailed` |
| F7 | LOW | the tests referencing `parents[1]` | ONLY THIS TEST'S LIVE-ROOT REFERENCE IS A DEPENDENCY-VERDICT COUPLING. Four test files derive the repository root from `Path(__file__)`: this one, `tests/test_lifecycle_style.py`, `tests/test_precommit_verbatim_exclusions.py`, and `tests/test_run_viewer.py`. The latter three assert over repository FILES by design (style, hook exclusions, viewer corpus), which is a different and legitimate use. This one fed a dependency-resolution verdict, which is why E-03 removes only it. | `grep -n 'parents\[1\]' tests/*.py` returns those four sites; only `test_dependency_block_reporting.py`'s feeds `state["repo"]` |
| F8 | LOW | scope and gate | THE `bug` WORK-KIND AND THE `next` GATE ARE INHERITED AND REMAIN CORRECT, THOUGH THE PERCEPTIBLE HARM HAS CHANGED SHAPE. The item's argument was a red suite on a clean tree, which is no longer true (F1). What remains is a test that cannot fail when the code it names breaks (F3), so a future regression in `dependency_status_detailed`'s resolution path would ship with a green suite. That is a defect in the gate the execution contract depends on, which is the same reasoning the item used, and `AGENTS.md` requires a live `bug` to carry the gate. | the item's `- Work-Kind: bug` and `- Blocks-Release: next`, inherited by `aw ipd scaffold --from-backlog 03aicr`; F3's mutation measurement is the surviving harm |

## Proposed changes (ordered, validatable)

1. Reproduce the green suite, the unparseable token, and the zero `edge_satisfied` calls, establishing that the item's red is gone and that the interim fix moved the test off the branch it documents (E-01).
2. Repoint the drain half at a legal id6 resolved against a synthesized `tmp_path` root carrying one non-`executed` plan file, so the unmet verdict comes from dependency resolution and depends on nothing in the live checkout (E-02).
3. Delete the vestigial live-root line and mark the landmine in a comment, so the coupling cannot return by the same route (E-03).

REVIEW NOTE ON WHAT THIS PLAN IS NOT. It changes no production code and fixes no user-visible output.
Both of the adjacent PRODUCTION defects found in the same review are already carried and deliberately
left alone: `8mohre` (`derive_item_disposition` labelling an in-queue unmet dependency `external`) and
`csjq81` (the reason line printing its token twice). Reaching into `run_selection_policy.py` or
`render_stream.py` from here would take work those items own, and would put a behavior change inside a
plan whose whole justification is that the test guarding that behavior does not currently work.

## Deferred / out of scope (with reason)

- FIXING THE TWO ADJACENT PRODUCTION DEFECTS (`8mohre`, `csjq81`). Out of scope by carrier, not by judgement: both are filed, both are about the reason/disposition TEXT rather than about this test, and `csjq81` explicitly notes its fix touches four surfaces including a durable events format. Doing either here would break this plan's own fence.
  - Carrier: 8mohre
  - Carrier: csjq81
- AUDITING EVERY TEST THAT NAMES A REAL PLAN id6 OR DERIVES THE LIVE ROOT. F6 and F7 measured the two candidate populations and found the other sites harmless: the real-id6 uses either synthesize their own root or never resolve, and the other three `parents[1]` uses assert over repository files by design. A sweep's measured yield beyond this one test is zero, so this is a scope fence rather than deferred work.
  - Carrier-Declined: the audit was PERFORMED (F6, F7) and found nothing to fix, so filing a carrier would assert outstanding work that measurement says does not exist.
- AUTHORING THE STANDING CONVENTION FOR A TEST WHOSE PROPERTY DEPENDS ON THE CHECKOUT. Owned by plan `kmzude` (Set `testlocality`, from backlog `5mc38x`), which is already `reviewed` and which answers "synthesize first". E-02 conforms to that answer, so this plan consumes the rule rather than writing it, and no `Item-Dependencies:` edge is needed because conforming requires nothing of `kmzude` to have landed.
  - Carrier-Declined: the work exists and is already carried by `kmzude`; a second carrier would duplicate it.
- INVESTIGATING WHY AN UNCARRIED TEST EDIT REACHED `main` (F5). A real process question, but it is about commit provenance across the repository rather than about this test, it would need its own measurement over many commits, and bundling it here would make a one-file test fix into a process audit. Needs its own backlog item if the maintainer wants one.
  - Carrier-Declined: recorded as context for how F2 escaped review, and deliberately NOT turned into an obligation this plan is not asking for.

## Scope check

- Over-scope: TWO RISKS NAMED. FIRST, an executor may notice that the new reason string exposes `csjq81`'s double-token defect (the rendered line will contain the token twice) and try to fix it; that is `csjq81`'s work and the surviving assertion is deliberately written as a containment check so it passes either way. SECOND, an executor may repoint the CASCADE half's state at `tmp_path` too, for symmetry; do not, because `cascade_dependency_blocked` never reads `repo`, so adding the key would imply a dependency that does not exist.
- Under-scope: this plan restores ONE test's sensitivity and adds no new test. It does not add coverage for `resolve_plan_path`'s `DriverError` arm (F4's other branch), which remains untested by this module; that is a genuine gap, it is not a regression, and inventing coverage for it here would exceed an item about live-state coupling. Stated so a reviewer weighs a known limit rather than discovering it.

## Required tests / validation

1. `python3 -m pytest` BARE, before and after, both summary lines pasted. Run it bare: `addopts` already supplies the quiet, parallel, fast-subset flags, and a second `-q` compounds to `-qq` and suppresses the `N passed` line this contract requires. Gate on NO NEW failures rather than on an absolute count, because the item's `3034 passed` is from an older HEAD and a managed worker lane can fail lifecycle tests by design.
2. `python3 -m pytest tests/test_dependency_block_reporting.py -v` after the change, showing all eight tests by name and passing, so the drain test is visibly present rather than inferred from a total.
3. THE MUTATION CHECK, which is the decisive evidence and the one this plan cannot be reported done without: with `runner_shared.edge_satisfied` replaced by a reason-destroying stub, `test_drain_and_cascade_mapped_reasons_rendered_once` must FAIL after E-02, and must be shown PASSING under the same mutation BEFORE it. A test green under both is asserting nothing about resolution (`GUIDING_PRINCIPLES.md` P16, "Verify test sensitivity with mutation"; precedent `DECISIONS.md` D78, which fixed a test that "had started passing vacuously" by restoring the real code path rather than relaxing the assertion).
4. THE LIVE-STATE INDEPENDENCE PROOF, which is the property backlog `03aicr` actually asked for: show the drain half's verdict is unchanged when the live checkout's plan corpus is irrelevant to it, by pasting the test passing AND by `grep`ping the file for `parents[` and for any real plan id6 in the drain half and showing neither remains.
5. `aw ipd lint --phase pre-transition` conforming, pasted.
6. `aw sanitize --agent` clean, pasted (the new code writes a `tmp_path`-derived path into a test, so the check is not pro forma).
7. `git diff` for `tests/test_dependency_block_reporting.py` reviewed and pasted, shown to remove no assertion and to leave the file's other five tests unchanged.

## Spec / documentation sync

No spec change is owed, and that is measured rather than assumed: `- Scope-Paths:` declares one test
file and no `.spec.md`, and this plan changes no behavior any spec describes. The runtime dependency
semantics the test exercises are specified in `25kzda` section 2.9 (the wait/release rules
`edge_satisfied` implements), and this plan makes the test conform to that spec's behavior rather than
proposing any amendment to it.

No user-facing documentation changes: the edit is confined to a test's own body and comments.

## Open questions

### OQ-01: Should the drain half assert the reason's exact text rather than containment, now that the reason is a stable resolution string?

- Blocking: no
- Status: resolved
- Owner: plan author (opencode/its_direct-pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT AUTHORING, KEEP CONTAINMENT, and recorded here rather than left silent because it is the one place this plan declines to strengthen an assertion and a reviewer should be able to dispute that. THE TEMPTATION: after E-02 the reason is deterministic (`external target <id6> is 'approved' (directory 'pending'), needs one of ['executed'] ...`), so an exact-equality assertion would be possible and would look stronger. THE REASON NOT TO: that string is exactly what backlog `csjq81` proposes to change. `csjq81` measures that every reason `dependency_status_detailed` produces is prefixed with its own token and that the renderers then compose `<token> (<reason>)`, printing the token twice, and its stated fix direction is to alter that composition. A test pinning the prose would fail on a correct fix and would have to be edited in the same change, which is the code-pinning-by-another-name that `GUIDING_PRINCIPLES.md` P16 forbids ("Do not assert that specific text ... remains unchanged"). The CONTAINMENT form already in the test, `un_reasons["executed:<id6>"] in drain_diags[0]`, reads the expected text out of the producer's own map, so it pins the PROPERTY the module docstring claims (the mapped reason is rendered, exactly once, with no `(blocked)` fallback) while staying agnostic to the wording. That is the assertion this test is for, and F3's mutation check is what proves it has teeth. A separate, narrow test pinning the resolution wording would be legitimate future work, but it belongs with whoever changes that wording, which is `csjq81`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all three measurements pasted at execution HEAD, each labelled with the exact command run, and each COMPARED to the authoring baseline rather than merely stated. (a) the bare-suite summary line, which must show NO failure of `test_drain_and_cascade_mapped_reasons_rendered_once`; if it DOES fail, this item's correct outcome is to STOP and report that the plan's premise is wrong, and that is a conforming result for V-01 while E-02 and E-03 must then not proceed unchanged. (b) `parse_dependency_token("executed:drnprereq")` -> `None`, WITH `ID6_RE.pattern` shown beside it, since the finding is the length mismatch and not merely a `None`. (c) the `edge_satisfied` call count, which MUST be pasted as an actual number from an actual spy (baseline `0`); a claim that the function "is not reached" does NOT satisfy this item, because a zero is precisely what a reader cannot verify from prose. Paste the reason map alongside it. Confirm no file under `tests/` was added or modified by this item (`git status --porcelain`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: FOUR things, each closing a way this could be reported satisfied while the coverage was still absent. FIRST, the new reason string pasted from an actual run, shown to be a RESOLUTION reason (naming the target's status and directory) and NOT `unparseable dependency token` and NOT `Cannot locate IPD`; those three arms are distinguishable by text and the whole point of E-02 is landing on the first. SECOND, THE MUTATION CHECK, which is this plan's decisive evidence: with `runner_shared.edge_satisfied` stubbed to destroy its reasons, show the test FAILING after the change, and show it PASSING under the same mutation before the change (F3 records the before-measurement to reproduce). BOTH directions are required; an after-only failure does not establish that anything improved. THIRD, the test passing normally, with the assertion set shown UNCHANGED by diff: `assert not sat`, the single-diagnostic assertion, the `(blocked)` absence, and the containment check must all still be present and unweakened, and the containment check must still read from `un_reasons` rather than a hardcoded string (an exact-prose assertion FAILS this item per OQ-01). FOURTH, the synthesized root shown to be under `tmp_path`, by quoting the lines that build it, so a reviewer can see the live checkout is no longer consulted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `grep -n 'parents\[' tests/test_dependency_block_reporting.py` returning NOTHING, pasted (an empty result must be shown as a pasted command with its exit status, not asserted). PLUS the fate of the `Path` import stated with its reason: if kept, name the surviving use; if removed, show the file still imports what its annotations need and the suite still passes. PLUS the new comment quoted, checked to name BOTH the legal-six-character-id6 requirement AND the unparseable-token guard it prevents, since a comment that says only "use a real id6" does not tell the next reader what goes wrong. PLUS a diff confirming the file's other five tests are byte-unchanged, and a `grep` showing no real plan id6 remains in the drain half. PLUS the bare-suite summary line after all three items, compared to V-01(a)'s, with NO NEW failures. PLUS `aw ipd lint --phase pre-transition` conforming and `aw sanitize --agent` clean, both pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (3 E-items in 1 task group, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is resolved and non-blocking: keep the containment assertion and do not
convert it to exact-text equality. SCOPE FENCE: `- Scope-Paths:` declares
`tests/test_dependency_block_reporting.py` and nothing else; an out-of-scope edit must be genuinely
required and then justified to `aw ipd finalize` with a `--scope-reason` per path. THE FIVE THINGS THIS
PLAN MUST NOT DO, each a short path to a change that reads as progress and is not. FIRST, do NOT edit
`agent_workflows/runner_shared.py`, `agent_workflows/render_stream.py`, or
`agent_workflows/run_selection_policy.py`: every measurement here says the production code is CORRECT,
and the two adjacent production defects are carried by `8mohre` and `csjq81`. SECOND, do NOT "fix" this
by flipping or deleting an assertion: the backlog item forbids it explicitly ("Do NOT 'fix' it by
flipping the assertion to match today's state, which would re-arm the same bomb pointed the other way,
and do not weaken it to a tautology"), and a test that asserts less is the defect this plan is closing,
not the remedy. THIRD, do NOT choose a token that cannot resolve (whether malformed like `drnprereq` or
merely absent like `zzz999`): F4 measures that both land on branches other than the drain case's, and
the malformed one is what `f1b5b9ff` already got wrong. FOURTH, do NOT repoint the cascade half's state
at `tmp_path` or add a `repo` key to it; `cascade_dependency_blocked` never reads it. FIFTH, do NOT
widen into the audits F6 and F7 already performed, and do not rename id6s in other test files. THE
HARD-MUST HONESTY RULE: paste the ACTUAL command output for every `V-*`. V-01(c) requires a pasted
spy COUNT, not a claim that a function is unreached; V-02 requires the mutation check in BOTH
directions, since an after-only failure cannot show the coverage was restored rather than always
present; and if any measurement contradicts this plan's authoring baseline, revise the plan's reasoning
and say so rather than restating the baseline. Commit path-scoped through `aw commit <plan> -- <paths>`;
never `git add -A`; never push. Before every commit run `git diff --cached --name-only` and unstage
anything not yours. LIFECYCLE TRANSITION: reaching `.aw/records/plans/executed/` via `aw ipd finalize`
is unconditionally owed, but its OWNER is conditional: under `aw oc run` / `aw agy run` the RUNNER owns
that transition, so do not invoke `aw ipd finalize` yourself in a runner-driven execution; a HAND
execution invokes it. Never hand-roll a `git mv` to `executed/`. Do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.

BEFORE IMPLEMENTING, re-run E-01's three reproductions. If the bare suite is RED on this test, or
`parse_dependency_token("executed:drnprereq")` no longer returns `None`, or the `edge_satisfied` spy
records a nonzero count, STOP and report rather than editing against a tree that has changed. All three
were measured on 2026-09-29 at lane HEAD `a70cdb6a`: `3246 passed, 2 skipped`; `None` against
`^[a-z0-9]{6}$`; and `0` calls beside the `unparseable dependency token` reason.
