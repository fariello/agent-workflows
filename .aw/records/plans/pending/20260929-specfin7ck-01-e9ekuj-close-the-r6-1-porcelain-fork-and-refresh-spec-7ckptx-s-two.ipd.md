# IPD: Close the R6.1 porcelain fork and correct spec 7ckptx's one false coverage sentence

- Date: 2026-09-29
- Kind: child
- Concern: Two substantive obstacles standing between spec `7ckptx` and an honest `implemented` claim: one live R6.1 violation (`runner_shared.dirty_tree_overlap` re-forks the single porcelain parser) and ONE acceptance-criterion sentence (A12b's coverage clause) that asserts a fact false at HEAD. A15 is separately stale in the weaker sense that it was amended after its only demonstration, which is a re-verification obligation and is Order 02's, not a text correction this plan can make.
- Scope: Re-point `runner_shared.dirty_tree_overlap` at the one porcelain parser, add the behavioral test that the existing re-export test structurally cannot catch, and correct A12b's stale coverage sentence. Explicitly NOT the spec status transition, which is Order 02's subject.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_shared.py, .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: eozq91
- Set: specfin7ck
- Order: 1
- Highest E allocated: 05
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: e9ekuj
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED, none deferred or open. HIGH PR-001: the conditional-abandon path told the executor to record E-02/E-03 and V-02/V-03 'not-needed', which is not a legal state in either closed vocabulary (probed: IPD-S401/IPD-S402, author disposition conforming -> error), so a fork already closed would have stranded the plan; rewritten onto E-02 'blocked' with a required Execution note, V-02 'blocked', and E-03 STILL PERFORMED because the test gap F-3 measures is independent of who closed the fork, with the honest IPD-S404 consequence stated (a blocked E-item cannot be finalized, so stop and report for retirement or re-scope). PR-003: F-6's arithmetic was backwards; the spec DEFINES 42 requirement ids and MENTIONS 43, the extra being R3.3b which is never defined at HEAD and survives only in WITHDRAWN A7c, so the backlog item's 42 was right and this plan's 43 was the error, and Order 02 must re-derive rather than adopt either figure. F-1, F-3 and F-4 all reproduce at HEAD 17387e25, and two things the plan asserted are now demonstrated: the forked decode and parse_porcelain_paths agree on all 12 probed porcelain inputs (so E-02 is a pure conformance change), and E-03's spy over parse_porcelain_entries records 0 calls at HEAD but 1 through the projection (so the new test genuinely discriminates). Bare suite 3246 passed, 2 skipped.

- 2026-09-29 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `eozq91`, whose premise is that spec `7ckptx` is finished and needs only a human transition. MEASURED AT AUTHORING AND THE PREMISE IS PARTLY FALSE, which is why this plan exists ahead of any transition. THREE MEASUREMENTS, each reproducible at HEAD `90bb593b`. (1) The item's requirement-coverage claim HOLDS but its count is wrong: it says "all 42 of the spec R<n>.<n> requirement ids", and the spec actually defines 43 distinct ids (the letter-suffixed `R3.3a`, `R4.1a`, `R5.1a`, `R5.6a` and siblings are missed by a `R[0-9]+\.[0-9]+` pattern that does not allow a trailing letter). Every one of the 43 IS cited by an executed `lanectn` plan, so the conclusion survives the arithmetic. (2) FINDING F1, which plan `4fodkt` reported and NOBODY FILED, is still live: `runner_shared.dirty_tree_overlap` decodes the porcelain format inline (`entry = line[3:]`, the `" -> "` split) while `lane_containment.parse_porcelain_entries` documents itself as "THE ONE PORCELAIN PARSER (spec R6.1)". That is the fork R6.1 calls non-conforming, and it is unfiled in every backlog directory (searched for `dirty_tree_overlap` and for `R6.1`). (3) TWO ACCEPTANCE CRITERIA WENT STALE AFTER `4fodkt` VERIFIED THEM, which `aw attention` cannot see because it reads status and not criterion text: the spec was amended twice (2026-09-18 R5.5/A15, 2026-09-25 R5.1a/A12b) after the 2026-09-17 verification at HEAD `e299a9a5`, so A12b and A15 as they read today were never demonstrated. A12b is additionally stale ON ITS FACE: it says parts (i)/(ii) "currently have no shipped test since commit `19313eed` deleted `tests/test_lane_input_manifest.py`", and that file exists at HEAD with 17 tests, restored by `654a3adb` (restorecov `dmxc5h`) on 2026-09-26. WHY THE WORK IS SPLIT FROM THE TRANSITION: F1 is a code change against a release-blocking spec and must be reviewed as one, while the transition is an evidence-and-authority act; bundling them would make one V-item cover both a code fix and a lifecycle claim.
- 2026-09-29 draft (opencode model=its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Remove the two things that make an `implemented` claim on spec `7ckptx` dishonest today: close the live R6.1
parser fork that plan `4fodkt` found and nobody filed, and correct the one acceptance-criterion text whose
stated facts are false at HEAD.

This plan deliberately does NOT transition the spec. It makes the transition Order 02 recommends TRUE
rather than merely asserted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the R6.1 fork, and prove the test gap that hid it

- [x] E-01 RE-MEASURE FINDING F1 AT EXECUTION HEAD BEFORE CHANGING ANYTHING, and abandon the fix if it has already been closed. Read `runner_shared.dirty_tree_overlap` and confirm it still decodes the porcelain format itself rather than delegating: the tells are the two-column strip (`entry = line[3:] if len(line) > 3 else line.strip()`) and the rename split on `" -> "`. Confirm `lane_containment.parse_porcelain_entries` still claims sole ownership ("THE ONE PORCELAIN PARSER (spec R6.1)") and that `parse_porcelain_paths` is its path-only projection. Record which surfaces reach the forked copy: both `oc_runipd` and `agy_runipd` re-export the `runner_shared` function rather than defining their own, so the fork is reached by every driver.
  - Depends on: none
  - Expected outcome: the two function bodies pasted side by side with the duplicated format knowledge identified line by line, plus an explicit statement that the fork IS or IS NOT still present. IF IT IS ALREADY GONE, follow the legal states named in the Approval and execution gate below (E-02 `blocked` with an `Execution note:` citing the closing commit; E-03 still performed, because the test gap F-3 records is independent of who closed the fork) and do NOT invent a state: `not-needed` is not a legal execution state.
  - Execution state: performed

- [x] E-02 REPOINT `dirty_tree_overlap` AT THE ONE PARSER, changing no behavior. Replace the inline decode with a call to `lane_containment.parse_porcelain_paths`, using the deferred-import form already used elsewhere in this module (`runner_shared.teardown_lane_if_classified` imports `lane_containment` inside the function body) so no import cycle is introduced. Preserve the function's contract exactly: it still runs `git status --short --untracked-files=all`, still intersects with the incoming set, still returns a sorted list, and still treats BOTH endpoints of a rename as dirty. Keep the docstring's merge-result-diff reasoning and its finding F-7 pointer intact, and replace only the paragraph that documents the format it no longer decodes, noting where the format now lives.
  - Depends on: E-01
  - Expected outcome: the new body pasted, showing the delegation and no remaining format knowledge, with the behavioral contract paragraphs preserved.
  - Execution state: performed

- [x] E-03 ADD THE TEST THE EXISTING ONE STRUCTURALLY CANNOT FAIL, because a fix with no new test would leave the next fork equally invisible. `4fodkt` recorded WHY the fork went unnoticed: the driver-level tests assert only the OVERLAP RESULT (`tests/test_oc_runipd.py::test_dirty_tree_overlap_helper_reports_only_overlap` and its `agy` twin), and `tests/test_runner_shared.py` treats `dirty_tree_overlap` as a plain re-export, so every existing assertion passes whether the parser is shared or forked. Add a test that fails on a fork and passes on delegation, WITHOUT reading source text (AGENTS.md forbids `inspect`/`ast`/regex pins on production source): monkeypatch `lane_containment.parse_porcelain_entries` to record its calls, drive `dirty_tree_overlap` against a real repository with a dirty tracked file, and assert the shared parser was actually invoked. Include a rename case, since that is the clause the two copies could most plausibly drift on. PATCH `parse_porcelain_entries` AND NOT `parse_porcelain_paths`, which is load-bearing and was demonstrated at review: the projection calls the decoder by module-global name, so patching the decoder is observed through the projection E-02 delegates to, whereas patching the projection would be bypassed if a later refactor called the decoder directly. Demonstrated in a scratch probe at review: with a spy bound over `parse_porcelain_entries`, `dirty_tree_overlap(repo, ["a.txt"])` on a dirty tracked file returned `['a.txt']` and the spy recorded `0` calls (the fork, so the test FAILS today), while `parse_porcelain_paths(" M a.txt\nR  orig.txt -> dest.txt\n")` returned `['a.txt', 'dest.txt', 'orig.txt']` with the spy recording `1` call (so the patch point is reached through the projection). RESTORE THE SPY IN A `finally` or with `monkeypatch`, since `lane_containment` is imported process-wide and a leaked spy would corrupt unrelated tests under `-n auto`.
  - Depends on: E-02
  - Expected outcome: the new test pasted, plus a demonstration that it FAILS against the pre-E-02 body (stash or temporarily restore the inline parser) and PASSES after, so its discriminating power is shown rather than asserted.
  - Execution state: performed

### Task group 2: correct the criterion text that is false at HEAD

- [x] E-04 CORRECT A12b'S STALE COVERAGE SENTENCE, and change nothing else about the criterion. A12b currently asserts that parts (i) and (ii) and the in-place-edit check of part (iii) "currently have no shipped test since commit `19313eed` deleted `tests/test_lane_input_manifest.py`". Verify the present state first: confirm the file exists, count its tests, and identify which of them cover parts (i), (ii), and the in-place-edit half of (iii) BY NAME (at authoring these include `test_an_accidental_in_place_write_fails`, `test_part_iii_a_change_is_a_new_revision_not_an_edit`, and `test_a_restored_write_bit_is_detected`). Then rewrite ONLY that sentence to name the tests that now cover each part, and cite the restoring commit (`654a3adb`, restorecov `dmxc5h`). CLAIM NO MORE THAN THE TESTS PROVE, which is the trap here: A12b parts (i)/(ii) ask for the manifest's and each input's MODE to be pasted in the artifact, whereas the restored tests prove the BEHAVIOR that mode buys (`test_an_accidental_in_place_write_fails` asserts the write raises `PermissionError`; `test_a_restored_write_bit_is_detected` asserts `verify_lane_input_seal` refuses an unsealed input) and assert no mode string. Those are the right tests by GUIDING_PRINCIPLES P16, so the corrected sentence must say the parts are now covered BEHAVIORALLY and name what each test asserts, NOT that the modes are pasted. Do NOT weaken, retarget, or renumber the criterion, and do NOT touch its requirement citation. Append the amendment to the spec's `## Workflow history` using `aw specs note` rather than hand-editing that section.
  - Depends on: none
  - Expected outcome: the before/after text of A12b's coverage sentence, the test names mapped to parts (i)/(ii)/(iii), and the `aw specs note` invocation with its output.
  - Execution state: performed

- [x] E-05 RUN THE SUITE AND THE SANITIZER, and record the baseline this plan is judged against. Run the suite BARE as `python3 -m pytest` (the repository's `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; do NOT add `-n0`, a second `-q`, or `-p no:randomly`). Also run `python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_lane_input_manifest.py` narrowed, since those are the four surfaces this plan touches or cites. Run `aw sanitize --agent`.
  - Depends on: E-03, E-04
  - Expected outcome: the bare suite's own summary line pasted verbatim, the narrowed run's summary pasted, and the sanitizer's exit status, with any new failure attributed to this plan or shown pre-existing at the base commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A containment rule consumed by more than one surface must live in ONE predicate (spec `7ckptx` R6.1), and the spec states that "forking the rule is non-conforming even when the copies agree at the time of writing". That last clause is why E-02 is warranted even though the two parsers currently agree.
- `lane_containment.parse_porcelain_entries` declares itself the sole owner of the porcelain format and records that both drivers' `dirty_tree_overlap` were previously de-forked into it; `parse_porcelain_paths` is documented as "A PROJECTION" that "holds no format knowledge of its own". The inline copy in `runner_shared.dirty_tree_overlap` is therefore a REGRESSION of an already-completed de-forking, not an omission.
- `runner_shared` reaches `lane_containment` by deferred in-function import (`runner_shared.teardown_lane_if_classified`), which is the established way to avoid a module-level cycle; E-02 follows it rather than adding a top-level import.
- Tests must assert observable behavior, never code structure: AGENTS.md forbids reading production source with `inspect`, `ast`, regex, or substring search, and forbids symbol censuses as correctness proxies. E-03 is shaped as a call-observation test for exactly this reason.
- Spec status and history are owned by `aw specs`; the specs README states plainly "Do NOT hand-edit the status or history". E-04 edits only criterion BODY text and records the amendment with `aw specs note`.
- A plan that amends a spec must declare the `.spec.md` file in `- Scope-Paths:` (AGENTS.md), which this plan does, because both runners announce and then reconcile declared spec edits.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE STATE VOCABULARIES ARE CLOSED and there is no "skipped" state. Execution states are `pending`/`performed`/`blocked`/`failed` (`ipd_schema.EXEC_STATES`) and validation results are `pending`/`pass`/`blocked`/`failed` (`ipd_schema.VALIDATION_RESULTS`), per spec `ipd-structure-and-linting` Sections 5.2/5.3. Demonstrated at review by inserting each into a scratch copy of this plan: `Execution state: not-needed` produced `IPD-S401 E-02: unknown execution state 'not-needed'` and `Result: not-needed` produced `IPD-S402 V-02: unknown validation result 'not-needed'`, each turning the `author` disposition from `conforming` to `error`. `blocked` additionally REQUIRES an `Execution note:`, and it is not finalizable: `aw ipd lint --phase pre-transition` emits `IPD-S404` for any `E-*` that is not `performed` and any `V-*` that is not `pass`, and `ipd_lifecycle` fails closed on a non-conforming pre-transition gate. The conditional-abandon branch is written against these facts rather than against an invented state.

## Findings

| Id | Finding | Evidence | Consequence |
|---|---|---|---|
| F-1 | `runner_shared.dirty_tree_overlap` re-forks the single porcelain parser, violating R6.1 | The function decodes the format itself (`entry = line[3:] ...`, `" -> "` split) while `lane_containment.parse_porcelain_entries` claims to be "THE ONE PORCELAIN PARSER (spec R6.1)" | A live R6.1 violation against a release-blocking spec; E-02 closes it |
| F-2 | F-1 was found by `4fodkt` and never filed anywhere | Searched `.aw/records/backlog/` and `.aw/records/plans/pending/` for `dirty_tree_overlap` and for `R6.1`: no item names it | The only record was a sentence inside an executed plan, which no status view reads; this plan is the filing |
| F-3 | Existing tests cannot fail on the fork | The two driver tests assert only the overlap RESULT; `tests/test_runner_shared.py` lists `dirty_tree_overlap` among plain re-exports | A fix alone would not prevent recurrence, so E-03 adds a test that discriminates |
| F-4 | A12b's coverage sentence is false at HEAD | It says `tests/test_lane_input_manifest.py` was deleted by `19313eed`; the file exists with 17 tests, restored by `654a3adb` (2026-09-26) | A criterion asserting a false fact cannot support an `implemented` claim; E-04 corrects it |
| F-5 | A12b and A15 were both amended AFTER `4fodkt` verified them | Spec history records amendments on 2026-09-18 (R5.5/A15) and 2026-09-25 (R5.1a/A12b); `4fodkt` verified on 2026-09-17 at HEAD `e299a9a5` | The two criteria as they read today were never demonstrated; re-demonstration is Order 02's E-scope, not this plan's |
| F-6 | The backlog item's count of 42 is RIGHT for defined requirements, and this plan's authoring claim of 43 conflated DEFINED with MENTIONED | Re-measured at review: the spec DEFINES 42 ids (unique line-start `R<n>.<n>[a-z] ` matches) and MENTIONS 43; the extra id is `R3.3b`, which is never defined at HEAD and survives only inside withdrawn criterion A7c and R3.3a's supersession prose. A letter-blind `R[0-9]+\.[0-9]+` pattern yields 32, not 42, so it cannot be what produced the item's 42 either | The item's arithmetic needed no correction. Every one of the 42 defined ids IS cited by an executed `lanectn` plan (re-verified at review), so the coverage conclusion holds on both counts. Order 02's E-01 must re-derive this itself and must NOT adopt either number |
| F-7 | `aw attention` currently reports `valid: false` repository-wide | `aw attention --format json` re-run at review: exactly two violations, both lane-hygiene (`attention.lane-superseded` for lane `3brgb6`, `attention.lane-stranded` for lane `om3rzi`), neither touching a spec, plan, or backlog record | Not caused by and not addressed by this plan; noted with its measured cause so its output is not read as clean during execution and is not mistaken for damage this Set caused |
| F-8 | A15 is stale in a WEAKER sense than A12b, and conflating them overstated this plan's scope | A12b asserts a checkable fact that is FALSE at HEAD (the deleted test file exists), so its TEXT is wrong; A15's text is correct and merely UNDEMONSTRATED since the 2026-09-18 amendment inverted its gitignored clause | Title, Concern, and Deferred reworded at review: this plan corrects ONE sentence and A15 stays wholly with Order 02, where it is a re-verification obligation rather than a text edit |

## Proposed changes (ordered, validatable)

1. Re-measure F-1 at execution HEAD; if already closed, record E-02 `blocked` with the closing commit and still perform E-03 (E-01, and see the execution gate for why the plan then cannot finalize).
2. Delegate `runner_shared.dirty_tree_overlap` to `lane_containment.parse_porcelain_paths`, preserving its contract and its merge-result-diff docstring reasoning (E-02).
3. Add a behavioral test that fails on a forked parser and passes on delegation, including a rename case, and demonstrate it fails before the fix (E-03).
4. Correct A12b's stale coverage sentence to name the tests that now cover parts (i)/(ii)/(iii) BEHAVIORALLY (not by mode string), citing the restoring commit, and record the amendment with `aw specs note` (E-04).
5. Run the bare suite, the narrowed surfaces, and the sanitizer, attributing any failure (E-05).

## Deferred / out of scope (with reason)

- THE SPEC STATUS TRANSITION. Order 02 owns it. Splitting it out keeps a code fix and a lifecycle claim from sharing one validation item.
  - Carrier: uuh71v
- RE-DEMONSTRATING A15 AND THE AMENDED A12b (F-5). That is re-verification of criterion behavior, which is Order 02's subject; this plan only makes A12b's text true. A15 IS NOT TOUCHED AT ALL here, not even textually (F-8): its text is correct and merely undemonstrated, so there is nothing for this plan to correct.
  - Carrier: uuh71v
- CORRECTING THE BACKLOG ITEM'S OWN SUMMARY, which says "all 42 of its requirements" (F-6). That count turns out to be RIGHT, so nothing is owed.
  - Carrier-Declined: No future work is owed because there is no defect. Re-measured at review, the spec DEFINES 42 requirement ids and the item's 42 is correct; this plan's authoring claim of 43 was the error, and it is corrected in F-6 rather than propagated. Recorded here because the authoring history line still states 43 and a reader comparing it against F-6 would otherwise wonder which was acted on: the answer is that F-6's re-measurement supersedes the history line, and Order 02's E-01 is instructed to re-derive the count from the spec rather than adopt either figure.
- BACKLOG `nvymif` (the R5.5 teardown gate refusing every interrupted lane) and the R2.5 question it raises. It is filed, `open`, and explicitly needs its own plan; it is a spec R2.5 design question, not a conformance defect this plan can close.
  - Carrier: nvymif
- FINDING F2 from `4fodkt` (the R1.2 clause detector misses one plausible rewording, LOW). The composite check still fails, so A1 passes; it is a robustness improvement with no live violation and no bearing on the transition.
  - Carrier-Declined: No future work is owed, and filing an item would overstate a measured non-defect. `4fodkt` recorded F2 at LOW severity precisely because the COMPOSITE check still fails on the rewording it found, so criterion A1 passes on its own terms and no requirement is violated at HEAD. What F2 describes is a detector that could be more thorough, not one that returns a wrong answer, and AGENTS.md's own test for filing a `bug` is user-perceptible impact, which an unreached branch of a passing check does not have. Recorded here rather than silently dropped so a reviewer does not read the omission as a claim that `4fodkt` found nothing beyond F1. Order 02's E-05 reports it to the maintainer as a standing counter-consideration, which is the correct destination for a measurement that needs a judgement rather than a fix.
- THE `aw attention` `valid: false` CONDITION (F-7). Pre-existing, repository-wide, and unrelated to this spec.
  - Carrier-Declined: Nothing is owed BY THIS PLAN and no item is filed, because this plan has not measured the cause and filing an unmeasured hunch is exactly what AGENTS.md forbids ("an unmeasured hunch that something feels slow is not a bug and should not be filed as one", the same standard applied to any unexamined condition). The condition is recorded ONLY so that an executor reading `aw attention` output during this Set does not mistake a pre-existing repository-wide invalidity for damage this Set caused, and so that a reviewer knows the attention view was consulted with its caveat understood. Diagnosing it requires resolving violations across trees this plan does not touch and would need its own measurement pass to file honestly.

## Scope check

- Over-scope: none. The three declared paths are the forked function, its test surface, and the one criterion text that is false.
- Under-scope: A15's re-demonstration and the amended A12b's re-demonstration are not performed here (see Deferred); Order 02 performs them, and this plan's Order-01 position guarantees it runs first. A15 receives no edit of any kind here (F-8).

## Required tests / validation

- A new test in `tests/test_runner_shared.py` that observes `lane_containment.parse_porcelain_entries` being called by `dirty_tree_overlap`, covering a plain dirty path and a rename, shown FAILING against the pre-fix body.
- The three existing `dirty_tree_overlap` result tests (`tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, and the `runner_shared` re-export identity test) must remain green, proving the delegation changed no behavior.
- `tests/test_lane_input_manifest.py` green, since E-04's corrected sentence cites it by test name.
- The bare suite (`python3 -m pytest`) and `aw sanitize --agent`.

## Spec / documentation sync

`.aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md` is declared in `- Scope-Paths:` and IS amended by E-04.

WHY A SPEC EDIT IS WARRANTED: A12b asserts a concrete, checkable fact about the test suite, and that fact is
false at HEAD. Leaving it would make the criterion unfalsifiable in the wrong direction, since a reader
checking it would find the cited deletion reversed and could not tell whether the criterion or the tree was
wrong. The edit NARROWS nothing: it names the tests that satisfy the parts the sentence said were uncovered,
which is a strictly stronger claim than the one it replaces. The requirement citation `(R5.1a)`, the
criterion's id, and its substantive obligations are untouched, so no other plan's review basis moves.

## Open questions

### OQ-01: Should A15's amended text be re-demonstrated by this plan rather than Order 02?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved from the Set's own division of labor rather than preference. This plan's concern is making false things true (a live R6.1 violation, a false coverage sentence); re-demonstrating criterion behavior is verification, which is what Order 02 exists to do and where the evidence belongs alongside the transition recommendation it supports. Folding it in here would put criterion evidence in a plan whose V-items are about a code fix, and would leave Order 02 recommending a transition on evidence gathered by a different plan.

### OQ-02: Does correcting A12b require the maintainer, since the spec is `approved`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved from AGENTS.md, which states that "specs are living contracts, not immutable history" and that a plan changing behavior a spec describes SHOULD carry the amendment in the same change, provided the spec file is declared in `- Scope-Paths:` (it is). The precedent is in this spec's own history: `xzroy8` and `d7qoxv` both amended it while `approved`. The guard that does bind is the one on STATUS, which `aw specs` owns and which this plan does not touch.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: both function bodies pasted, with the duplicated format knowledge identified clause by clause (the two-column strip and the rename split), and an explicit IS or IS NOT verdict on the fork. A verdict asserted without both bodies pasted does NOT satisfy this item. If the verdict is IS NOT, the commit that closed it must be cited; V-02 then records `blocked` with its `Observed evidence` naming that commit (`not-needed` is not a legal validation result, and `pass` would assert a delegation this plan did not make), while V-03 is still required to `pass` because E-03 is still performed.
  - Observed evidence: Both function bodies compared; duplicated format knowledge identified; fork confirmed present at execution HEAD:
    Function body 1 (`runner_shared.dirty_tree_overlap` in `agent_workflows/runner_shared.py` at HEAD `c9d1de82ac`):
    ```python
    def dirty_tree_overlap(repo: Path, changed_files: Sequence[str]) -> list[str]:
        incoming = {p for p in changed_files if p.strip()}
        if not incoming:
            return []
        _rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])
        dirty: set[str] = set()
        for line in out.splitlines():
            if not line.strip():
                continue
            # Strip the two status columns and the following space: entries are `XY path` (min 3 chars).
            entry = line[3:] if len(line) > 3 else line.strip()
            # A rename/copy renders as `orig -> dest`; treat both endpoints as dirty.
            if " -> " in entry:
                orig, dest = entry.split(" -> ", 1)
                dirty.add(orig.strip())
                dirty.add(dest.strip())
            else:
                dirty.add(entry.strip())
        return sorted(incoming & dirty)
    ```

    Function body 2 (`lane_containment.parse_porcelain_entries` in `agent_workflows/lane_containment.py`):
    ```python
    def parse_porcelain_entries(porcelain: str) -> list[tuple[str, str]]:
        entries: list[tuple[str, str]] = []
        for line in porcelain.splitlines():
            if not line.strip():
                continue
            # Strip the two status columns and the following space: entries are `XY path` (min 3 chars).
            status = line[:2] if len(line) > 3 else ""
            entry = line[3:] if len(line) > 3 else line.strip()
            endpoints = (
                [part.strip() for part in entry.split(" -> ", 1)]
                if " -> " in entry
                else [entry.strip()]
            )
            for path in endpoints:
                if path:
                    entries.append((status, path))
        return entries
    ```

    Duplicated format knowledge identified clause by clause:
    - Clause 1 (two-column strip): `entry = line[3:] if len(line) > 3 else line.strip()` in `runner_shared.dirty_tree_overlap` duplicates identical logic in `lane_containment.parse_porcelain_entries`.
    - Clause 2 (rename split): `if " -> " in entry: orig, dest = entry.split(" -> ", 1)` in `runner_shared.dirty_tree_overlap` duplicates `" -> " in entry` / `entry.split(" -> ", 1)` in `lane_containment.parse_porcelain_entries`.

    Driver surfaces reaching the forked copy:
    - `agent_workflows/oc_runipd.py:625`: re-exports `dirty_tree_overlap as dirty_tree_overlap` from `runner_shared`.
    - `agent_workflows/agy_runipd.py:327`: re-exports `dirty_tree_overlap as dirty_tree_overlap` from `runner_shared`.

    Explicit verdict: The fork IS still present at execution HEAD.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the post-change body of `dirty_tree_overlap` pasted, showing (a) the delegation to `lane_containment.parse_porcelain_paths`, (b) NO remaining format decoding, (c) the deferred in-function import form, and (d) the preserved contract (the same `git status` invocation, the intersection, the sorted return). Plus the three existing result tests passing, pasted, which is what proves behavior did not change. A paste showing delegation but no passing result tests does NOT satisfy this item.
  - Observed evidence: Post-change body delegates to lane_containment.parse_porcelain_paths; 3 existing test suites pass:
    Post-change body of `dirty_tree_overlap` in `agent_workflows/runner_shared.py`:
    ```python
    def dirty_tree_overlap(repo: Path, changed_files: Sequence[str]) -> list[str]:
        """driverfin-03 (7kbtkw) E-01: report the MAIN tree's un-owned dirty paths that overlap an
        INCOMING CHANGE.

        Inspect ``git status --short`` in the MAIN repo (working tree + index) and return the sorted set
        of paths that are BOTH dirty in main AND part of the incoming change. A non-empty result means the
        integration base is contaminated with un-owned edits to the very paths we are about to integrate,
        so integrating over it could clobber or half-finish; the caller REFUSES rather than integrating.

        ``changed_files`` IS THE SET THE MERGE WOULD WRITE, NOT THE LANE'S OWN DIFF (mergedirty-01
        `fujm0y` E-02). The caller passes :func:`merge_write_set`'s result - the merge result tree diffed
        against HEAD - and falls back to the lane's `changed_files` only when that is UNKNOWN. This
        parameter therefore means "the incoming change as it will land", and the docstring said
        ``changed_files`` for a reason that no longer holds: passing the lane's diff was the DEFECT. A
        non-fast-forward merge also writes paths the lane never touched (commits that landed on main
        since the lane base, and renames of lane-touched files), and those were outside the check.
        REPRODUCED (git 2.43.0): the lane changed only `a.txt`, main renamed `a.txt` to `renamed.txt` and
        was dirty there, `dirty_tree_overlap(repo, ["a.txt"])` returned `[]` (guard says clear), and
        `git merge --no-ff` then failed on `renamed.txt`.

        WHY THE INPUT IS THE MERGE-RESULT DIFF AND NOT A MERGE-BASE-TO-BOTH-TIPS UNION: the union
        REFUSES a merge that succeeds safely, so it would trade a missed refusal for a wrong one. The
        counterexample is measured and lives in :func:`merge_write_set`'s docstring (finding F-7). Read it
        before changing the input set, because the union reads as the more thorough choice and is not.

        The porcelain format is decoded by :func:`lane_containment.parse_porcelain_paths` (the single
        parser prescribed by spec `7ckptx` R6.1, which treats both the origin and destination of a
        rename as dirty).
        """
        incoming = {p for p in changed_files if p.strip()}
        if not incoming:
            return []
        from agent_workflows import lane_containment

        _rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])
        dirty = lane_containment.parse_porcelain_paths(out)
        return sorted(incoming & dirty)
    ```
    Confirmation of properties:
    - (a) Delegates to `lane_containment.parse_porcelain_paths(out)`
    - (b) No format decoding logic remaining in `runner_shared.py`
    - (c) Deferred in-function import `from agent_workflows import lane_containment` avoids module cycle
    - (d) Preserved contract: same `_run_git(repo, ["status", "--short", "--untracked-files=all"])`, `incoming & dirty` set intersection, and `sorted(...)` list return.

    Three existing result tests passing (pasted verbatim):
    1. `tests/test_oc_runipd.py`:
       `2 passed in 6.97s`
    2. `tests/test_agy_runipd_cli.py`:
       `1 passed in 9.77s`
    3. `tests/test_runner_shared.py` (`test_a_rename_still_makes_BOTH_endpoints_count_as_dirty`):
       `1 passed in 9.79s`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the new test pasted, plus BOTH runs: its FAILURE output against the pre-E-02 inline body and its PASS output after. The failure run is the load-bearing half, because a test that passes either way is exactly the gap F-3 records; a pass-only paste does NOT satisfy this item. The rename case must appear in the pasted test. Confirm the test reads no production source text (no `inspect`, `ast`, or regex over source), per the AGENTS.md prohibition.
  - Observed evidence: Discriminating test test_dirty_tree_overlap_delegates_to_single_porcelain_parser added and demonstrated failing pre-fix and passing post-fix:
    Pasted new test `test_dirty_tree_overlap_delegates_to_single_porcelain_parser` in `tests/test_runner_shared.py`:
    ```python
    def test_dirty_tree_overlap_delegates_to_single_porcelain_parser(self):
        """specfin7ck-01 (e9ekuj) E-03: prove dirty_tree_overlap delegates to lane_containment's parser.

        F-1/F-3: Existing tests assert only the overlap result, passing whether the porcelain format
        is decoded by the shared parser or forked inline. This test spies on
        `lane_containment.parse_porcelain_entries` to prove that the single parser prescribed by
        spec 7ckptx R6.1 is actually invoked, covering both a plain dirty file and a rename.
        """
        import tempfile
        from agent_workflows import lane_containment

        original_parser = lane_containment.parse_porcelain_entries
        calls: list[str] = []

        def spy_parser(porcelain: str):
            calls.append(porcelain)
            return original_parser(porcelain)

        try:
            lane_containment.parse_porcelain_entries = spy_parser
            for runner in BOTH:
                with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                    repo = self._repo(pathlib.Path(tmp))
                    (repo / "a.txt").write_text("a\n", encoding="utf-8")
                    self._git(repo, "add", "a.txt")
                    self._git(repo, "commit", "-qm", "add a")

                    # Case 1: plain dirty tracked file
                    (repo / "a.txt").write_text("modified\n", encoding="utf-8")
                    calls.clear()
                    overlap = _MODULES[runner].dirty_tree_overlap
                    res = overlap(repo, ["a.txt"])
                    self.assertEqual(res, ["a.txt"])
                    self.assertGreaterEqual(
                        len(calls),
                        1,
                        "dirty_tree_overlap must delegate to the shared porcelain parser",
                    )

                    # Case 2: rename case
                    self._git(repo, "checkout", "-f", "main")
                    self._git(repo, "mv", "a.txt", "b.txt")
                    calls.clear()
                    res_orig = overlap(repo, ["a.txt"])
                    self.assertEqual(res_orig, ["a.txt"])
                    self.assertGreaterEqual(
                        len(calls),
                        1,
                        "rename origin check must delegate to the shared porcelain parser",
                    )
                    calls.clear()
                    res_dest = overlap(repo, ["b.txt"])
                    self.assertEqual(res_dest, ["b.txt"])
                    self.assertGreaterEqual(
                        len(calls),
                        1,
                        "rename dest check must delegate to the shared porcelain parser",
                    )
        finally:
            lane_containment.parse_porcelain_entries = original_parser
    ```

    Both runs:
    Run 1: FAILURE against pre-E-02 inline body:
    ```
    F                                                                        [100%]
    =================================== FAILURES ===================================
    _ LaneIntegrationBehaviorTests.test_dirty_tree_overlap_delegates_to_single_porcelain_parser _
    [gw11] linux -- Python 3.14.6 <venv>/bin/python3
    ...
        overlap = _MODULES[runner].dirty_tree_overlap
        res = overlap(repo, ["a.txt"])
        self.assertEqual(res, ["a.txt"])
    >   self.assertGreaterEqual(
            len(calls),
            1,
            "dirty_tree_overlap must delegate to the shared porcelain parser",
        )
    E   AssertionError: 0 not greater than or equal to 1 : dirty_tree_overlap must delegate to the shared porcelain parser

    tests/test_runner_shared.py:710: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_runner_shared.py::LaneIntegrationBehaviorTests::test_dirty_tree_overlap_delegates_to_single_porcelain_parser
    1 failed in 7.71s
    ```

    Run 2: PASS after E-02 delegation:
    ```
    .                                                                        [100%]
    1 passed in 8.49s
    ```

    Rename case check: Case 2 explicitly tests `mv a.txt b.txt` and asserts delegation for both `a.txt` (origin) and `b.txt` (destination).
    Source inspection check: The test contains no `inspect`, `ast`, or regex/substring analysis over production source; it asserts strictly on runtime delegation behavior via a spy on the public function.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: A12b's coverage sentence quoted BEFORE and AFTER; the `tests/test_lane_input_manifest.py` test names mapped to parts (i), (ii), and the in-place-edit half of (iii), with those tests shown passing; the restoring commit cited; and the `aw specs note` command with its output. The AFTER text must describe the coverage as BEHAVIORAL and must not claim the tests paste a mode, since they assert `PermissionError` and a `verify_lane_input_seal` refusal rather than a mode string; a corrected sentence that overclaims is a FAILURE of this item, because it would replace one false sentence with another. Also paste the spec's `- Status:` line before and after, proving it is UNCHANGED, since this plan has no authority over it. Any edit to A12b's id, its `(R5.1a)` citation, or its substantive obligations is a FAILURE of this item, not a pass.
  - Observed evidence: A12b coverage sentence updated to cite restored behavioral tests; spec note recorded; status unchanged:
    A12b coverage sentence BEFORE:
    "Parts (i) and (ii) and the in-place edit check of part (iii) currently have no shipped test since commit `19313eed` deleted `tests/test_lane_input_manifest.py`, leaving only the out-of-position dispatch scoping of part (iii) covered in `tests/test_lane_input_revision_scope.py`."

    A12b coverage sentence AFTER:
    "Parts (i) and (ii) and the in-place edit check of part (iii) are covered behaviorally in `tests/test_lane_input_manifest.py` (restored by commit `654a3adb`, restorecov `dmxc5h`): `test_an_accidental_in_place_write_fails` asserts an in-place write to the manifest or an input raises `PermissionError`, `test_a_restored_write_bit_is_detected` asserts `verify_lane_input_seal` detects a restored write bit, and `test_part_iii_a_change_is_a_new_revision_not_an_edit` asserts an input change produces a new revision leaving prior revision bytes untouched, alongside `tests/test_lane_input_revision_scope.py` covering the out-of-position dispatch scoping of part (iii)."

    Test mapping to criterion parts and pass evidence:
    - Parts (i) and (ii): `test_an_accidental_in_place_write_fails` (raises `PermissionError`) and `test_a_restored_write_bit_is_detected` (`verify_lane_input_seal` detects restored write bit).
    - Part (iii) in-place edit check: `test_part_iii_a_change_is_a_new_revision_not_an_edit` (produces new revision, prior revision bytes untouched).
    - Part (iii) out-of-position dispatch: `tests/test_lane_input_revision_scope.py` (`test_out_of_position_turn_attachment_resolves_own_revision`).
    Restoring commit: `654a3adb` (restorecov `dmxc5h`).
    Test suite runs:
    - `python3 -m pytest tests/test_lane_input_manifest.py`: `17 passed in 9.36s`
    - `python3 -m pytest tests/test_lane_input_revision_scope.py`: `4 passed in 8.93s`

    `aw specs note` invocation and output:
    ```
    $ aw specs note .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md --message "AMENDED 2026-10-01 (specfin7ck-01 e9ekuj): A12b coverage sentence corrected to cite behavioral test coverage restored by 654a3adb (dmxc5h) in tests/test_lane_input_manifest.py" --date 2026-10-01
    aw specs note: appended a history record to .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
    ```

    Spec `- Status:` line BEFORE:
    `- Status: approved`
    Spec `- Status:` line AFTER:
    `- Status: approved`
    Status is UNCHANGED. A12b's identifier, `(R5.1a)` citation, and substantive obligations are untouched.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the bare `python3 -m pytest` summary line pasted VERBATIM (the `N passed` line; if it is absent, the run was misinvoked with extra `-q` and must be rerun), the narrowed four-file run's summary, and `aw sanitize --agent`'s exit status. Every failure must be attributed either to this plan or shown pre-existing at the base commit by running it there. A claim of green without the pasted summary line does NOT satisfy this item.
  - Observed evidence: Bare suite, narrowed suite, and sanitizer verified clean:
    Bare `python3 -m pytest` summary line (verbatim):
    `3742 passed, 2 skipped, 3 warnings in 121.52s (0:02:01)`

    Narrowed four-file run (`python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_lane_input_manifest.py`) summary line:
    `385 passed in 32.62s`

    `aw sanitize --agent` exit status:
    `0` (output: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (5 E-items in 2 task groups, under the 18-leaf / 5-group thresholds). The two groups are one code-conformance concern and one text-correctness concern against the same spec, sharing a single validation run.

EXECUTION CONTRACT. IF E-01 FINDS THE FORK ALREADY CLOSED, do NOT manufacture a change: set E-02's
`Execution state: blocked` with an `Execution note:` citing the commit that closed it, and record V-02
`blocked` with that commit as its `Observed evidence`. STILL PERFORM E-03: the test gap F-3 records is that
no existing assertion can fail on a fork, which is true whoever closed it, so the regression test is owed
either way and E-03's "demonstrate it fails against the pre-fix body" is then done by temporarily
re-introducing the inline parser rather than by stashing. USE ONLY THE LEGAL STATES: execution states are
`pending`/`performed`/`blocked`/`failed` and validation results are `pending`/`pass`/`blocked`/`failed`
(spec `ipd-structure-and-linting` Sections 5.2/5.3); `not-needed` is not one and `aw ipd lint` reports
`IPD-S401`/`IPD-S402` on it. NOTE THE CONSEQUENCE HONESTLY: `aw ipd lint --phase pre-transition` requires
every `E-*` `performed` and every `V-*` `pass` (`IPD-S404`), so a `blocked` E-02 CANNOT be finalized by
`aw ipd finalize`. On that path STOP after E-05 and report to the maintainer that the plan's premise expired
and it should be retired to `.aw/records/plans/not-executed/` (or re-scoped to E-03/E-04 alone), rather than
forcing a transition the gate refuses. DO NOT TRANSITION THE SPEC;
its `- Status:` must read `approved` before and after this plan, and V-04 requires proving that. Amend ONLY
A12b's coverage sentence: this plan has no mandate to reword any other criterion, and A15's re-demonstration
belongs to Order 02. TESTS ASSERT BEHAVIOR, NOT SOURCE TEXT: E-03 must not read production source with
`inspect`, `ast`, or regex, per AGENTS.md. Run the suite BARE (`python3 -m pytest`); do not add `-n0`, a
second `-q`, or `-p no:randomly`. Commit through `aw commit <plan> -- <paths>`, never `git add -A`, never
`--no-verify`, and never push. This is a SHARED CHECKOUT: run `git diff --cached --name-only` before every
commit and `git restore --staged <path>` anything not yours. POST-GATE LIFECYCLE: reaching
`.aw/records/plans/executed/` via `aw ipd finalize` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL:
under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do not invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it. Never hand-roll a `git mv` to
`executed/`. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every `V-*` above
carries real observed evidence. Backlog `eozq91` is already `graduated` and MUST NOT be closed `done` here:
its gate is carried by Order 02, which is the plan that hands the spec to the maintainer.
