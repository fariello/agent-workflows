# IPD: Report the examined count on the human specs check surface so a validated-nothing verdict is visible

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `uwerb5` names TWO surfaces on which `aw specs check` hides how many specs it examined: the `--agent` record omitting `checked` at zero, and the human branch printing no count at any value. THE `--agent` HALF IS ALREADY FIXED and must not be re-implemented: commit `0a10a7b1` (plan `kifrou`, set `specsread`, closing backlog `an3vqw`) replaced the falsy `or` in `result_types.CommandResult.to_agent_record` with an explicit `"checked" in self.data` presence test, and `tests/test_agent_checked_count.py` pins `checked == 0` on an empty tree. Measured in this lane 2026-09-29: `aw specs check --agent` emits `"checked":38` here and that test file passes 3/3. THE HUMAN HALF IS LIVE AT HEAD. `specs.run_check`'s human branch hand-writes two `sys.stdout.write` calls and bypasses `HumanRenderer` entirely, so the `summary` string it already computes (`f"{len(paths)} specs checked"`) is unreachable and the operator sees only `aw specs check: all specs conform.` with no number. Measured in this lane: that exact line, exit 0, while `--agent` on the same tree reported 38. This is the same validated-nothing failure `an3vqw` was filed for, surviving on the surface a HUMAN uses: a conform verdict over zero specs is indistinguishable from a conform verdict over 38, and `specs check` declares `human_recipe="check"` in `command_surface.py` while not rendering a check at all.
- Scope: IN: make `specs.run_check`'s human branch report the examined count, matching the count wording the same function already computes for the agent/JSON branch and the `Evidence` receipt convention `aw check <type>` demonstrates; a behavioral test asserting the count is visible in human output at zero AND at nonzero; one CHANGELOG line. OUT: the `--agent` branch and `result_types.to_agent_record` (already fixed by `kifrou`, F-1); the identical missing-count gap in `backlog check`, `attention --check`, `research check-refs` and `sanitize` (filed separately, see Deferred); `_spec_files`'s retired-filter scope (the 38-vs-20 difference from `check_engine._iter_type_files` is that filter working as designed, F-6); and any change to which specs are examined, to exit codes, or to the drift rules.
- Scope-Paths: agent_workflows/specs.py, tests/test_agent_checked_count.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: uwerb5
- Blocks-Release: next
- Set: uwerb5
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 121j2r

## Workflow history

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `uwerb5`. The item names two halves and ONE IS ALREADY DONE: verified at HEAD by reading `result_types.to_agent_record`'s presence test, by running `tests/test_agent_checked_count.py` (3 passed), and by measuring `aw specs check --agent` in this lane. The plan therefore carries only the HUMAN half, which was re-measured live and is still broken, and it records the already-fixed half as a finding so a reviewer can see the substitution rather than discover it. The item's release gate is inherited.

## Goal

Make `aw specs check`'s human output state how many specs it examined, so an operator can tell a
clean verdict over 38 specs from a clean verdict over zero.

The user-facing property: running `aw specs check` in a repository with no specs prints a count of
`0` rather than an unqualified `all specs conform.`, and running it here prints the same count the
`--agent` and `--json` surfaces already report for the same tree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: put the count on the human surface

- [ ] E-01 In `specs.run_check`, make the human branch report the examined count on BOTH paths (drift and no-drift). The count is already computed as `len(paths)` and already worded in the `summary` expression above the agent branch (`f"{len(paths)} specs checked"` / `f"{len(drift)} finding(s) detected across {len(paths)} specs"`); reuse that SAME wording rather than inventing a second phrasing, so the human and machine surfaces cannot drift apart in wording or in value. Hoist the `summary` computation so both branches read one expression, rather than duplicating the f-strings into the human branch. Keep the existing per-drift `{location}: {rule}: {detail}` lines, the existing remediation sentence, and the existing exit code (`core.drift_exit_code(drift)`) exactly as they are: this item is about a missing fact, not about restyling the output. DECIDE AND STATE in Findings which of the two shapes you implemented, a minimal in-place count line or a full `HumanRenderer` adoption, and why; OQ-01 records the tradeoff and either answer is executable, but the choice must be justified in the plan rather than left implicit in the diff.
  - Depends on: none
  - Expected outcome: `aw specs check` in a zero-spec repository prints a line containing `0` and the word `checked`, and in this repository prints the same count `--agent` reports for the same tree (38 at authoring). The drift path also carries the count. Exit codes are unchanged at 0 and 1, and no existing drift line or remediation sentence is removed.
  - Execution state: pending

- [ ] E-02 Verify and record in Findings that the human count and the `--agent` `checked` value are computed from the SAME expression and cannot disagree. Run all three surfaces (`aw specs check`, `--agent`, `--json`) against one unchanged tree and compare the three numbers. If E-01 left two independent expressions that happen to agree today, fix that rather than recording the agreement: the defect class this item belongs to is a surface reporting a different fact than its sibling, so an accidental agreement is not the property wanted. Do NOT change `_spec_files` or any filter to make the numbers match; if they disagree for a reason OTHER than E-01's implementation, stop and record it as a finding, because that would be a distinct defect from this one (see F-6 for the one known legitimate difference, which is `check_engine._iter_type_files`'s retired filter and is NOT in scope).
  - Depends on: E-01
  - Expected outcome: one pasted three-way comparison over a single tree showing the same integer on all three surfaces, plus a written statement that the human count reads the same computed value as the agent record rather than a parallel recomputation.
  - Execution state: pending

### Task group 2: pin it so it cannot silently regress

- [ ] E-03 Add behavioral tests to `tests/test_agent_checked_count.py` covering the HUMAN surface at zero and at nonzero, mirroring the two `--agent` cases that file already contains for `specs check`. Drive the real CLI through the file's existing `_run_cli_with_fallback` helper (which already supports the `AW_UNFIXED_TREE` before/after comparison this repository uses) in a real temporary repository built by `tests.support.init_repo`, and assert on the actual stdout text: at zero specs the output must contain the count `0`, and in the nonzero control it must contain the count matching the number of specs created. Pass `--no-color` so the assertion is not defeated by ANSI styling. Assert on the OBSERVABLE stdout of a subprocess, never by reading `specs.py` source with `inspect`/`ast`/regex and never by asserting a symbol census (AGENTS.md test contract, GUIDING_PRINCIPLES P16). Put them in this file rather than a new module because it is already the named regression suite for exactly this defect (its docstring names IPD `kifrou`) and keeping both halves of `uwerb5` in one place is what makes the pair discoverable.
  - Depends on: E-01
  - Expected outcome: at least two new tests, each FAILING against pre-E-01 code (the human output contains no digit at all) and passing after, asserting the count is present in human stdout at zero and at nonzero.
  - Execution state: pending

- [ ] E-04 Add ONE `- Fixed:` line to `CHANGELOG.md` under the pending-version heading describing the user-visible change: `aw specs check` now reports how many specs it examined, so a clean result over zero specs is distinguishable from a clean result over many. Write it in the user-facing register with NO em or en dashes (AGENTS.md). Then establish the suite baseline comparison: run `python3 -m pytest` BARE (no added flags) and record the summary line plus the full FAILED set, and compare against a baseline captured BEFORE this plan's first source edit. The pre-edit half must be captured FIRST even though this item is ordered last, because a baseline taken afterwards cannot separate a failure this plan caused from one it inherited; this repository has known pre-existing failures, so "the suite is green" is NOT the expected result and must not be asserted.
  - Depends on: E-03
  - Expected outcome: one CHANGELOG line in user-facing prose with no em or en dash, and two pasted bare-suite summary lines with their FAILED sets plus an explicit statement of whether the two sets are identical.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The count wording convention is `"<N> <plural-noun> checked"` on the clean path and `"<M> finding(s) detected across <N> <plural-noun>"` on the dirty path. `specs.run_check`, `backlog.run_check`, `aw check`'s handler and `attention`'s `--check` branch all build that same shape, and `specs.run_check` ALREADY builds it; the human branch simply never prints it. So E-01 is a plumbing fix, not a new message design.
- The canonical carrier of a human count is `HumanRenderer`, which puts it in the outcome banner and again in an `Evidence` grid. `docs/cli-human-guide.md` documents that layout (`X FINDINGS  2 findings across 41 checked`, then `Evidence` / `checked: 41`) and `aw check specs` demonstrates it live, measured in this lane as `✓ CONFORMS  20 specs checked` plus an `Evidence` line `checked  20`.
- `docs/cli-output-contract.md` Section 2 states the governing rule this defect violates: "Both renderers expose identical facts (counts, paths, evidence, exit code) with zero domain drift". Section 11.1 separately requires that an empty result carry "the zero count" rather than a bare clean line. These are the contract citations that make this a defect and not a styling preference.
- `command_surface.py` declares `specs check` with `human_recipe="check"` (and `spec check` the same), but NO test enforces that declaration: `rg human_recipe tests/` returns nothing. So the declaration is documentation today, which is why this defect survived a declared recipe and why E-03 must assert on real output rather than trusting the declaration.
- `tests/conformance_matrix.py` lists `specs check` and `spec check` in `LIVE_SAFE_LEAVES` and exercises them across audience scenarios, but by explicit design gates on "schema / ANSI / exit-code invariants (not on exact finding COUNTS)", and its `semantic_facts_from_human` returns `None` unless the output starts with an `AW <command>` title banner. Two consequences for E-01: the existing matrix cannot catch this defect (hence E-03), and if E-01 adopts the full `HumanRenderer` the command STARTS emitting that banner, which makes the matrix begin extracting an outcome family for it where it previously fell back to exit-code parity. That is a behavior change in a shared test surface and must be checked, not assumed harmless.
- Nothing pins the current human string: `rg "all specs conform"` finds the literal only in `specs.py` itself plus prose inside review records and executed plans (which are historical evidence and must not be edited). No test, workflow, or doc asserts it, so the line is safe to change.
- Test-authoring contract (AGENTS.md, GUIDING_PRINCIPLES P16): assert observable outcomes, never read production source with `inspect`/`ast`/regex, never pin caller counts or symbol censuses. E-03 stays on the right side by asserting subprocess stdout.
- Run the suite BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q` (which suppresses the summary line this plan must paste), or `-p no:randomly`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Where | Finding |
|---|---|---|
| F-1 | `result_types.CommandResult.to_agent_record` | THE ITEM'S `--agent` HALF IS ALREADY FIXED and this plan deliberately does not redo it. The falsy expression the item quotes is gone; HEAD reads `self.data["checked"] if "checked" in self.data else self.data.get("total_checked")` guarded by `if checked_count is not None`, so zero survives. Fixed by commit `0a10a7b1` ("specsread(kifrou): emit a zero checked count in the agent record instead of dropping it"), which closed backlog `an3vqw`. |
| F-2 | `tests/test_agent_checked_count.py` | The `--agent` half is ALSO already pinned: `test_specs_check_agent_emits_checked_zero_on_empty_tree` asserts `"checked" in rec` and `rec["checked"] == 0`, with a nonzero control asserting `1`. Measured in this lane: `3 passed in 1.30s`. This is the file E-03 extends, so both halves of `uwerb5` end up in one suite. |
| F-3 | `specs.run_check` human branch | THE LIVE DEFECT AND THIS PLAN'S REASON TO EXIST. The branch hand-writes `sys.stdout.write` and never constructs a renderer, so the `summary` value computed a few lines above (`f"{len(paths)} specs checked"`) is dead on this path. Measured in this lane 2026-09-29: `aw specs check` printed exactly `aw specs check: all specs conform.` and nothing else, exit 0, while `aw specs check --agent` on the same tree printed `"checked":38`. |
| F-4 | `docs/cli-output-contract.md` Sections 2 and 11.1 | The governing contract is explicit, which is what makes this a defect rather than a preference: Section 2 requires both renderers to "expose identical facts (counts, paths, evidence, exit code) with zero domain drift", and Section 11.1 requires an empty result to carry "the zero count". The human branch satisfies neither. |
| F-5 | `command_surface.py` `specs check` / `spec check` | Both declare `human_recipe="check"`, yet the command emits no check render at all. The declaration is unenforced (`rg human_recipe tests/` is empty), so it documents an intent the code does not honor. Recorded because it means a reviewer cannot treat the declaration as evidence the surface is correct. |
| F-6 | `specs._spec_files` vs `check_engine._iter_type_files` | A KNOWN AND LEGITIMATE COUNT DIFFERENCE, named so nobody "fixes" it under this plan. Measured in this lane: `_spec_files` returns 38, `_iter_type_files(..., "specs")` returns 20, and `_iter_type_files(..., include_retired=True)` returns 38, so the gap is the retired filter working as designed. This is why `aw specs check` says 38 while `aw check specs` says 20. E-02 compares the THREE surfaces of one command, not these two different commands. |
| F-7 | `backlog.run_check`, `attention` `--check`, `research_refs`, `leak_sanitizer` | THE SAME DEFECT SHAPE EXISTS IN FOUR SIBLINGS, each hand-writing `sys.stdout.write` instead of using `HumanRenderer` and each printing no count (`aw backlog check: all backlog items conform.`, `aw attention --check: the view is valid.`, and so on). Deliberately OUT of scope here to keep a bug fix from becoming a five-command refactor; filed as its own item instead (see Deferred). Named so a reviewer knows the narrow scope is a choice, not an oversight. |
| F-8 | `tests/conformance_matrix.py` | Cannot catch this defect by design: it gates on "schema / ANSI / exit-code invariants (not on exact finding COUNTS)". It is also the reason E-01's shape matters beyond style: `semantic_facts_from_human` only extracts an outcome family when stdout opens with an `AW <command>` title line, so a full `HumanRenderer` adoption would newly satisfy that precondition for `specs check` and change which comparison path the matrix takes for this leaf. |
| F-9 | two review records (`1bdxcp` PR-208, `wfjsp4` PR-003) | This defect was FOUND BY REVIEW and consciously deferred twice, each time because a Set's own acceptance criterion turned out to be unobservable on the surface it named; both reviews redirected their criteria to `--json` as a workaround and required the gap be filed rather than fixed in passing. `uwerb5` is that filing, so this plan is closing a loop those reviews opened, not discovering something new. |

## Proposed changes (ordered, validatable)

1. E-01: report the examined count in `specs.run_check`'s human branch on both the drift and no-drift paths, reusing the `summary` expression the function already computes for the machine surfaces.
2. E-02: prove the human count and the `--agent` `checked` value come from one expression and agree on one tree across all three surfaces.
3. E-03: add human-surface regression tests at zero and nonzero to `tests/test_agent_checked_count.py`, shown failing before the change.
4. E-04: one user-facing CHANGELOG line, plus a before/after bare-suite FAILED-set comparison.

## Deferred / out of scope (with reason)

- The `--agent` half of backlog `uwerb5` (the `checked`-at-zero omission). Already implemented and already pinned by tests at HEAD (F-1, F-2); re-implementing it would be a no-op at best and a regression at worst.
  - Carrier-Evidence: .aw/records/plans/executed/20260926-specsread-01-kifrou-emit-a-zero-checked-count-in-the-agent-record-instead-of-dro.ipd.md
- The identical missing-count gap in `backlog check`, `attention --check`, `research check-refs` and `sanitize` (F-7). Fixing five commands at once would turn a release-gating bug fix into a cross-command renderer migration, with five surfaces of regression risk and a much larger review. The narrow fix here also establishes the pattern the sweep would follow.
  - Carrier-Declined: NOT YET A FILED OBLIGATION, and deliberately not filed by this authoring turn, because the right scope for the sweep depends on the shape E-01 actually lands (OQ-01). If E-01 takes the minimal in-place form, a sweep is four small independent edits; if it adopts `HumanRenderer`, the sweep is a renderer migration touching `attention` and `doctor`-adjacent output whose blast radius needs its own measurement. Filing an item now would fix a scope before the information that decides it exists. The executor of this plan MUST file it with `aw backlog new` once E-01's shape is known, and V-01 requires the filed item id6 be pasted, so the obligation is enforced by this plan's own validation rather than left to memory.
- `_spec_files`'s retired-filter scope and the 38-vs-20 difference against `aw check specs` (F-6). Measured and understood as the filter working as designed, not a defect, and changing which specs are examined is a behavior change this item does not ask for.
  - Carrier-Declined: NOTHING IS OUTSTANDING. This entry exists to record a measurement that a reader might otherwise mistake for a bug, and the measurement is complete: the two functions differ only by `include_retired`, and with it set they return the same 38. There is no residual work for a future carrier, and filing an item saying "these two counts legitimately differ" would create an obligation nobody can close.
- Enforcing `command_surface.py`'s `human_recipe` declarations with a test (F-5). A real gap, but it is a test-infrastructure project spanning every declared command, not part of fixing one command's output.
  - Carrier-Declined: OUT OF THIS ITEM'S SUBJECT AND NOT SILENTLY DROPPED. The observation is recorded as F-5 so a reviewer can weigh it, but a declaration-conformance harness is a cross-cutting piece of test infrastructure whose value and shape are independent of `specs check`; bundling it would widen a bug fix into a framework change and would delay a release-gating fix behind it. This plan needs no such harness: E-03 pins the actual behavior directly, which is the stronger guarantee for this command regardless of whether the declaration is ever enforced.
- Closing backlog `uwerb5` as `done`. The authoring contract forbids it, and the runner sets `graduated` on verifying this turn.
  - Carrier: uwerb5

## Scope check

- Over-scope: `tests/test_agent_checked_count.py` and `CHANGELOG.md` are in `Scope-Paths` although the item names neither. The test file is required by the execution contract (a bug fix needs a regression guard) and is the file already dedicated to this exact defect (F-2); the CHANGELOG line is required by repository convention for a user-visible output change.
- Under-scope: the item's `--agent` half is NOT implemented, because it is already in the tree and pinned by passing tests (F-1, F-2). The four sibling commands with the same defect are NOT fixed (F-7). Both omissions are recorded here and in Deferred so a reviewer can overrule the narrowing rather than discover it, and OQ-02 asks directly whether the sweep should be pulled in.

## Required tests / validation

- `python3 -m pytest tests/test_agent_checked_count.py` run BARE for the focused surface. Paste the summary line and the new tests' names.
- Each new test must be shown FAILING against pre-change code (stash the `specs.py` change and re-run) so it is proven to bite. The expected pre-change failure is that human stdout contains no count at all.
- A measured three-surface comparison on one unchanged tree (`aw specs check`, `--agent`, `--json`) showing the same integer, pasted verbatim.
- A measured zero-spec case: in a throwaway repository with an empty `.aw/records/specs/`, paste the actual human stdout showing the count `0` and exit 0. This is the exact case the item exists for, so an unmeasured claim here does not satisfy the plan.
- Exit-code parity: paste `aw specs check` exit status on a conforming tree (expect 0) and on a tree with one nonconforming spec (expect 1), confirming E-01 changed neither.
- `python3 -m pytest` bare for the whole suite, with a before/after comparison of the FAILED set so a pre-existing failure is not miscounted as a regression. Include the conformance-matrix tests in that comparison and explicitly state whether `specs check`'s rows changed, per F-8.
- `aw ipd lint --phase pre-transition` on this plan must report conforming before any terminal transition.

## Spec / documentation sync

No `.spec.md` file governs this behavior, so NO spec path is declared in `- Scope-Paths:` and no spec is
amended. Verified by searching the specs tree: the two specs mentioning `aw.agent/v1`
(`command-surface-redesign`, `pip-distribution-and-multi-repo-setup`) describe the agent envelope and
neither states how a human check render reports its examined count, and no spec mentions `HumanRenderer`.

The governing statements are in `docs/`, and both ALREADY REQUIRE the behavior this plan implements, so
they need no edit: `docs/cli-output-contract.md` Section 2 ("Both renderers expose identical facts
(counts, paths, evidence, exit code) with zero domain drift") and Section 11.1 (an empty result must
carry "the zero count"), plus `docs/cli-human-guide.md`'s documented count layout. This plan brings the
code into line with documentation that is already correct rather than changing the contract, which is why
no doc edit is in scope. The only documentation this plan writes is the user-facing `CHANGELOG.md` line
in E-04. If the executor finds any doc sentence that describes the CURRENT countless human output as
correct, that sentence must be corrected and the file added to `- Scope-Paths:` with a `--scope-reason`.

## Open questions

### OQ-01: minimal in-place count line, or full `HumanRenderer` adoption?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NOT blocking; the plan is executable either way and E-01 requires the executor to choose and JUSTIFY, so no decision is silently made. The minimal form adds the already-computed `summary` to the two `sys.stdout.write` paths: smallest diff, no change to the output's overall shape, and no new interaction with the conformance matrix. The full form routes the branch through `HumanRenderer` like `aw check specs` does, which additionally delivers the title banner and the `Evidence` grid that `docs/cli-human-guide.md` documents and that `human_recipe="check"` declares (F-5), at the cost of changing every line of this command's output and of newly satisfying `semantic_facts_from_human`'s `AW ` precondition (F-8), which changes which comparison path the shared matrix takes for this leaf. The author's recommendation is the MINIMAL form for this release-gating fix, because it closes the measured defect with the least regression surface, and to let the sweep in F-7 carry the renderer migration for all five commands together. A reviewer wanting the documented layout now should say so explicitly, since that answer also enlarges the evidence V-01 must show.
- Carrier-Declined: DECIDED BY THE ACT OF REVIEWING AND BY E-01, leaving nothing to carry. Both answers close the same defect and E-01 obliges the executor to record which shape was implemented and why, so whichever is chosen is documented in this plan's own Findings and validated by V-01. There is no residue: the unchosen alternative is not deferred work but a rejected styling, and the broader renderer question it gestures at is already tracked as the F-7 sweep obligation that V-01 requires be filed. An item saying "decide how one command formats its count" could never be closed on evidence independent of this plan.

### OQ-02: should the four sibling commands be fixed in this plan instead of separately?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NOT blocking; the narrow scope is chosen and defensible. `backlog check`, `attention --check`, `research check-refs` and `sanitize` all hand-write their human output and all print no count (F-7), so a reader could reasonably ask for one sweep. Against that: only `specs check` is named by this release-gating item, a five-command change multiplies the regression surface and the review burden, and the right sweep shape depends on OQ-01's outcome. The author recommends keeping this plan to one command and filing the sweep, which E-01's outcome then informs; V-01 requires the filed item's id6 be pasted, so the sweep cannot be quietly forgotten. A reviewer who prefers one change should redirect before approval, since that widens `- Scope-Paths:` to four more modules.
- Carrier-Declined: NOT AN OUTSTANDING OBLIGATION FROM THIS PLAN, because the work it describes is already enforced as one: the Deferred entry for F-7 obliges the executor to file the sweep with `aw backlog new` and V-01 refuses without the resulting id6. So the follow-up work has a real carrier by the time this plan finishes, and this question is only about WHO does it and WHEN, which the reviewer settles before execution. Filing a second item to track the question itself would duplicate the item the plan already guarantees gets filed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of the `specs.run_check` human-branch change. Paste the ACTUAL stdout of `aw specs check --no-color` from THREE trees: this repository (count must match the `--agent` `checked` value on the same tree), a repository with an empty `.aw/records/specs/` (the output must contain `0`), and a tree with at least one nonconforming spec (the count must appear alongside the drift lines, and the pre-existing `{location}: {rule}: {detail}` lines and remediation sentence must still be present). Paste the exit status for the clean and dirty cases showing 0 and 1 unchanged. STATE which shape from OQ-01 was implemented and why, in one or two sentences. Paste the id6 returned by the `aw backlog new` call that files the F-7 sweep; an unfiled sweep does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the three-way comparison (`aw specs check`, `aw specs check --agent`, `aw specs check --json`) over one unchanged tree, with the three integers visible and identical. Then show the count is ONE fact and not two agreeing facts: quote the single expression both branches read, or if two expressions remain, paste the change that unified them. A claim of agreement without the shared expression shown does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste each new test's name and source, and the BARE `python3 -m pytest tests/test_agent_checked_count.py` summary line showing them passing together with the three pre-existing tests. Then paste proof they BITE: stash the `specs.py` change, re-run, and paste the FAILURE output showing the human stdout carried no count. Confirm in writing that the tests drive a real CLI subprocess in a temporary repository and assert on stdout text, reading no production source via `inspect`/`ast`/regex and pinning no symbol census (P16).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the added CHANGELOG line and confirm it sits under the pending-version heading, is written in the user-facing register, and contains no em or en dash. Paste the BARE `python3 -m pytest` summary line from BEFORE the first source edit and from after all edits, with the FAILED set for each, and state explicitly whether the two sets are identical; any new failure must be fixed or explained with evidence, never waved through as flakiness without naming the test and re-running it. State explicitly whether any `tests/conformance_matrix.py`-derived test changed status for `specs check` (F-8). Confirm no flag was added to the bare invocation (no `-n0`, no extra `-q`, no `-p no:randomly`).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; it is `to-review` and carries no `- Readiness:`
field, which is `/plan-review`'s output to write and not the author's.

Execution contract. Commit ONLY the paths in `- Scope-Paths:` through `aw commit 121j2r -- <paths>`; never
`git add -A`, never `-a`, never `--no-verify`, never push. Paste actual runner output for every test claim; a
summary line reconstructed from memory is not evidence, and the zero-spec measurement in particular must be
observed rather than asserted, since an unobservable criterion is the exact failure mode that produced this
item (F-9). Other agents may be working in this checkout: commit only paths you changed, and verify the
staged set before committing.

Scope fence. If a needed edit falls outside `- Scope-Paths:`, MAKE the edit and then justify it via
`--scope-reason`/`--scope-ack`; this is a declaration requirement, not a stop order. Stop and report only for
the genuinely unsafe cases: a conflicting concurrent change to `specs.py` you cannot safely combine, or a
required change to `result_types.to_agent_record` (which would mean F-1's premise is wrong and the
already-fixed half regressed, a different plan's subject).

Post-gate lifecycle. Do not move this plan to `.aw/records/plans/executed/` or mark it `executed` until
`aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted evidence. In a
runner lane the runner owns finalize; a hand executor uses `aw ipd finalize`. Backlog `uwerb5` carries
`- Blocks-Release: next` and this plan inherits it, so the gate travels here through `- From-Backlog:`; the
item reaches `done` only once this plan is `executed`, and the executor should close it citing this plan as
evidence, noting `kifrou` as the carrier of the `--agent` half (F-1).
