# IPD: Close the R6.1 porcelain fork and refresh spec 7ckptx's two stale coverage claims

- Date: 2026-09-29
- Kind: child
- Concern: The two substantive obstacles standing between spec `7ckptx` and an honest `implemented` claim: one live R6.1 violation (`runner_shared.dirty_tree_overlap` re-forks the single porcelain parser) and two acceptance-criterion texts (A12b, A15) that assert facts no longer true at HEAD.
- Scope: Re-point `runner_shared.dirty_tree_overlap` at the one porcelain parser, add the behavioral test that the existing re-export test structurally cannot catch, and correct A12b's stale coverage sentence. Explicitly NOT the spec status transition, which is Order 02's subject.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_shared.py, .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: eozq91
- Set: specfin7ck
- Order: 1
- Highest E allocated: 05
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: e9ekuj

## Workflow history

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

- [ ] E-01 RE-MEASURE FINDING F1 AT EXECUTION HEAD BEFORE CHANGING ANYTHING, and abandon the fix if it has already been closed. Read `runner_shared.dirty_tree_overlap` and confirm it still decodes the porcelain format itself rather than delegating: the tells are the two-column strip (`entry = line[3:] if len(line) > 3 else line.strip()`) and the rename split on `" -> "`. Confirm `lane_containment.parse_porcelain_entries` still claims sole ownership ("THE ONE PORCELAIN PARSER (spec R6.1)") and that `parse_porcelain_paths` is its path-only projection. Record which surfaces reach the forked copy: both `oc_runipd` and `agy_runipd` re-export the `runner_shared` function rather than defining their own, so the fork is reached by every driver.
  - Depends on: none
  - Expected outcome: the two function bodies pasted side by side with the duplicated format knowledge identified line by line, plus an explicit statement that the fork IS or IS NOT still present. If absent, E-02/E-03 are recorded not-needed with the commit that closed it cited, and this plan continues at E-04.
  - Execution state: pending

- [ ] E-02 REPOINT `dirty_tree_overlap` AT THE ONE PARSER, changing no behavior. Replace the inline decode with a call to `lane_containment.parse_porcelain_paths`, using the deferred-import form already used elsewhere in this module (`runner_shared.teardown_lane_if_classified` imports `lane_containment` inside the function body) so no import cycle is introduced. Preserve the function's contract exactly: it still runs `git status --short --untracked-files=all`, still intersects with the incoming set, still returns a sorted list, and still treats BOTH endpoints of a rename as dirty. Keep the docstring's merge-result-diff reasoning and its finding F-7 pointer intact, and replace only the paragraph that documents the format it no longer decodes, noting where the format now lives.
  - Depends on: E-01
  - Expected outcome: the new body pasted, showing the delegation and no remaining format knowledge, with the behavioral contract paragraphs preserved.
  - Execution state: pending

- [ ] E-03 ADD THE TEST THE EXISTING ONE STRUCTURALLY CANNOT FAIL, because a fix with no new test would leave the next fork equally invisible. `4fodkt` recorded WHY the fork went unnoticed: the driver-level tests assert only the OVERLAP RESULT (`tests/test_oc_runipd.py::test_dirty_tree_overlap_helper_reports_only_overlap` and its `agy` twin), and `tests/test_runner_shared.py` treats `dirty_tree_overlap` as a plain re-export, so every existing assertion passes whether the parser is shared or forked. Add a test that fails on a fork and passes on delegation, WITHOUT reading source text (AGENTS.md forbids `inspect`/`ast`/regex pins on production source): monkeypatch `lane_containment.parse_porcelain_entries` to record its calls, drive `dirty_tree_overlap` against a real repository with a dirty tracked file, and assert the shared parser was actually invoked. Include a rename case, since that is the clause the two copies could most plausibly drift on.
  - Depends on: E-02
  - Expected outcome: the new test pasted, plus a demonstration that it FAILS against the pre-E-02 body (stash or temporarily restore the inline parser) and PASSES after, so its discriminating power is shown rather than asserted.
  - Execution state: pending

### Task group 2: correct the criterion text that is false at HEAD

- [ ] E-04 CORRECT A12b'S STALE COVERAGE SENTENCE, and change nothing else about the criterion. A12b currently asserts that parts (i) and (ii) and the in-place-edit check of part (iii) "currently have no shipped test since commit `19313eed` deleted `tests/test_lane_input_manifest.py`". Verify the present state first: confirm the file exists, count its tests, and identify which of them cover parts (i), (ii), and the in-place-edit half of (iii) BY NAME (at authoring these include `test_an_accidental_in_place_write_fails`, `test_part_iii_a_change_is_a_new_revision_not_an_edit`, and `test_a_restored_write_bit_is_detected`). Then rewrite ONLY that sentence to name the tests that now cover each part, and cite the restoring commit (`654a3adb`, restorecov `dmxc5h`). Do NOT weaken, retarget, or renumber the criterion, and do NOT touch its requirement citation. Append the amendment to the spec's `## Workflow history` using `aw specs note` rather than hand-editing that section.
  - Depends on: none
  - Expected outcome: the before/after text of A12b's coverage sentence, the test names mapped to parts (i)/(ii)/(iii), and the `aw specs note` invocation with its output.
  - Execution state: pending

- [ ] E-05 RUN THE SUITE AND THE SANITIZER, and record the baseline this plan is judged against. Run the suite BARE as `python3 -m pytest` (the repository's `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; do NOT add `-n0`, a second `-q`, or `-p no:randomly`). Also run `python3 -m pytest tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_lane_input_manifest.py` narrowed, since those are the four surfaces this plan touches or cites. Run `aw sanitize --agent`.
  - Depends on: E-03, E-04
  - Expected outcome: the bare suite's own summary line pasted verbatim, the narrowed run's summary pasted, and the sanitizer's exit status, with any new failure attributed to this plan or shown pre-existing at the base commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A containment rule consumed by more than one surface must live in ONE predicate (spec `7ckptx` R6.1), and the spec states that "forking the rule is non-conforming even when the copies agree at the time of writing". That last clause is why E-02 is warranted even though the two parsers currently agree.
- `lane_containment.parse_porcelain_entries` declares itself the sole owner of the porcelain format and records that both drivers' `dirty_tree_overlap` were previously de-forked into it; `parse_porcelain_paths` is documented as "A PROJECTION" that "holds no format knowledge of its own". The inline copy in `runner_shared.dirty_tree_overlap` is therefore a REGRESSION of an already-completed de-forking, not an omission.
- `runner_shared` reaches `lane_containment` by deferred in-function import (`runner_shared.teardown_lane_if_classified`), which is the established way to avoid a module-level cycle; E-02 follows it rather than adding a top-level import.
- Tests must assert observable behavior, never code structure: AGENTS.md forbids reading production source with `inspect`, `ast`, regex, or substring search, and forbids symbol censuses as correctness proxies. E-03 is shaped as a call-observation test for exactly this reason.
- Spec status and history are owned by `aw specs`; the specs README states plainly "Do NOT hand-edit the status or history". E-04 edits only criterion BODY text and records the amendment with `aw specs note`.
- A plan that amends a spec must declare the `.spec.md` file in `- Scope-Paths:` (AGENTS.md), which this plan does, because both runners announce and then reconcile declared spec edits.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence | Consequence |
|---|---|---|---|
| F-1 | `runner_shared.dirty_tree_overlap` re-forks the single porcelain parser, violating R6.1 | The function decodes the format itself (`entry = line[3:] ...`, `" -> "` split) while `lane_containment.parse_porcelain_entries` claims to be "THE ONE PORCELAIN PARSER (spec R6.1)" | A live R6.1 violation against a release-blocking spec; E-02 closes it |
| F-2 | F-1 was found by `4fodkt` and never filed anywhere | Searched `.aw/records/backlog/` and `.aw/records/plans/pending/` for `dirty_tree_overlap` and for `R6.1`: no item names it | The only record was a sentence inside an executed plan, which no status view reads; this plan is the filing |
| F-3 | Existing tests cannot fail on the fork | The two driver tests assert only the overlap RESULT; `tests/test_runner_shared.py` lists `dirty_tree_overlap` among plain re-exports | A fix alone would not prevent recurrence, so E-03 adds a test that discriminates |
| F-4 | A12b's coverage sentence is false at HEAD | It says `tests/test_lane_input_manifest.py` was deleted by `19313eed`; the file exists with 17 tests, restored by `654a3adb` (2026-09-26) | A criterion asserting a false fact cannot support an `implemented` claim; E-04 corrects it |
| F-5 | A12b and A15 were both amended AFTER `4fodkt` verified them | Spec history records amendments on 2026-09-18 (R5.5/A15) and 2026-09-25 (R5.1a/A12b); `4fodkt` verified on 2026-09-17 at HEAD `e299a9a5` | The two criteria as they read today were never demonstrated; re-demonstration is Order 02's E-scope, not this plan's |
| F-6 | The backlog item's requirement count is off by one, and its conclusion still holds | The spec defines 43 distinct requirement ids, not 42; a `R[0-9]+\.[0-9]+` pattern misses the letter-suffixed `R3.3a`, `R4.1a`, `R5.1a`, `R5.6a`. All 43 are cited by executed `lanectn` plans | Recorded so a reviewer is not misled by the item's arithmetic; no action needed |
| F-7 | `aw attention` currently reports `valid: false` repository-wide | `aw attention --format json` at authoring | Not caused by and not addressed by this plan; noted so its output is not read as clean during execution |

## Proposed changes (ordered, validatable)

1. Re-measure F-1 at execution HEAD and stop if already closed (E-01).
2. Delegate `runner_shared.dirty_tree_overlap` to `lane_containment.parse_porcelain_paths`, preserving its contract and its merge-result-diff docstring reasoning (E-02).
3. Add a behavioral test that fails on a forked parser and passes on delegation, including a rename case, and demonstrate it fails before the fix (E-03).
4. Correct A12b's stale coverage sentence to name the tests that now cover parts (i)/(ii)/(iii), citing the restoring commit, and record the amendment with `aw specs note` (E-04).
5. Run the bare suite, the narrowed surfaces, and the sanitizer, attributing any failure (E-05).

## Deferred / out of scope (with reason)

- THE SPEC STATUS TRANSITION. Order 02 owns it. Splitting it out keeps a code fix and a lifecycle claim from sharing one validation item.
  - Carrier: uuh71v
- RE-DEMONSTRATING A15 AND THE AMENDED A12b (F-5). That is re-verification of criterion behavior, which is Order 02's subject; this plan only makes A12b's text true.
  - Carrier: uuh71v
- BACKLOG `nvymif` (the R5.5 teardown gate refusing every interrupted lane) and the R2.5 question it raises. It is filed, `open`, and explicitly needs its own plan; it is a spec R2.5 design question, not a conformance defect this plan can close.
  - Carrier: nvymif
- FINDING F2 from `4fodkt` (the R1.2 clause detector misses one plausible rewording, LOW). The composite check still fails, so A1 passes; it is a robustness improvement with no live violation and no bearing on the transition.
  - Carrier-Declined: No future work is owed, and filing an item would overstate a measured non-defect. `4fodkt` recorded F2 at LOW severity precisely because the COMPOSITE check still fails on the rewording it found, so criterion A1 passes on its own terms and no requirement is violated at HEAD. What F2 describes is a detector that could be more thorough, not one that returns a wrong answer, and AGENTS.md's own test for filing a `bug` is user-perceptible impact, which an unreached branch of a passing check does not have. Recorded here rather than silently dropped so a reviewer does not read the omission as a claim that `4fodkt` found nothing beyond F1. Order 02's E-05 reports it to the maintainer as a standing counter-consideration, which is the correct destination for a measurement that needs a judgement rather than a fix.
- THE `aw attention` `valid: false` CONDITION (F-7). Pre-existing, repository-wide, and unrelated to this spec.
  - Carrier-Declined: Nothing is owed BY THIS PLAN and no item is filed, because this plan has not measured the cause and filing an unmeasured hunch is exactly what AGENTS.md forbids ("an unmeasured hunch that something feels slow is not a bug and should not be filed as one", the same standard applied to any unexamined condition). The condition is recorded ONLY so that an executor reading `aw attention` output during this Set does not mistake a pre-existing repository-wide invalidity for damage this Set caused, and so that a reviewer knows the attention view was consulted with its caveat understood. Diagnosing it requires resolving violations across trees this plan does not touch and would need its own measurement pass to file honestly.

## Scope check

- Over-scope: none. The three declared paths are the forked function, its test surface, and the one criterion text that is false.
- Under-scope: A15's re-demonstration and the amended A12b's re-demonstration are not performed here (see Deferred); Order 02 performs them, and this plan's Order-01 position guarantees it runs first.

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

- [ ] V-01 validates E-01
  - Required evidence: both function bodies pasted, with the duplicated format knowledge identified clause by clause (the two-column strip and the rename split), and an explicit IS or IS NOT verdict on the fork. A verdict asserted without both bodies pasted does NOT satisfy this item. If the verdict is IS NOT, the commit that closed it must be cited and V-02/V-03 recorded not-needed rather than passed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the post-change body of `dirty_tree_overlap` pasted, showing (a) the delegation to `lane_containment.parse_porcelain_paths`, (b) NO remaining format decoding, (c) the deferred in-function import form, and (d) the preserved contract (the same `git status` invocation, the intersection, the sorted return). Plus the three existing result tests passing, pasted, which is what proves behavior did not change. A paste showing delegation but no passing result tests does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new test pasted, plus BOTH runs: its FAILURE output against the pre-E-02 inline body and its PASS output after. The failure run is the load-bearing half, because a test that passes either way is exactly the gap F-3 records; a pass-only paste does NOT satisfy this item. The rename case must appear in the pasted test. Confirm the test reads no production source text (no `inspect`, `ast`, or regex over source), per the AGENTS.md prohibition.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: A12b's coverage sentence quoted BEFORE and AFTER; the `tests/test_lane_input_manifest.py` test names mapped to parts (i), (ii), and the in-place-edit half of (iii), with those tests shown passing; the restoring commit cited; and the `aw specs note` command with its output. Also paste the spec's `- Status:` line before and after, proving it is UNCHANGED, since this plan has no authority over it. Any edit to A12b's id, its `(R5.1a)` citation, or its substantive obligations is a FAILURE of this item, not a pass.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the bare `python3 -m pytest` summary line pasted VERBATIM (the `N passed` line; if it is absent, the run was misinvoked with extra `-q` and must be rerun), the narrowed four-file run's summary, and `aw sanitize --agent`'s exit status. Every failure must be attributed either to this plan or shown pre-existing at the base commit by running it there. A claim of green without the pasted summary line does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (5 E-items in 2 task groups, under the 18-leaf / 5-group thresholds). The two groups are one code-conformance concern and one text-correctness concern against the same spec, sharing a single validation run.

EXECUTION CONTRACT. STOP IF E-01 SAYS THE FORK IS GONE: record it, skip E-02/E-03 as not-needed with the
closing commit cited, and continue at E-04 rather than manufacturing a change. DO NOT TRANSITION THE SPEC;
its `- Status:` must read `approved` before and after this plan, and V-04 requires proving that. Amend ONLY
A12b's coverage sentence: this plan has no mandate to reword any other criterion, and A15's re-demonstration
belongs to Order 02. TESTS ASSERT BEHAVIOR, NOT SOURCE TEXT: E-03 must not read production source with
`inspect`, `ast`, or regex, per AGENTS.md. Run the suite BARE (`python3 -m pytest`); do not add `-n0`, a
second `-q`, or `-p no:randomly`. Commit through `aw commit <plan> -- <paths>`, never `git add -A`, never
`--no-verify`, and never push. This is a SHARED CHECKOUT: run `git diff --cached --name-only` before every
commit and `git restore --staged <path>` anything not yours. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`; do not claim done until `aw ipd lint --phase
pre-transition` conforms and every `V-*` above carries real observed evidence.
