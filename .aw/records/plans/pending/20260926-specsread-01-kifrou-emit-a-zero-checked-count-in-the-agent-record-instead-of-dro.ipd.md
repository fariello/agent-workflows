# IPD: Emit a zero checked count in the agent record instead of dropping it

- Date: 2026-09-26
- Kind: child
- Concern: `result_types.CommandResult.to_agent_record` builds the count as `self.data.get("checked") or self.data.get("total_checked")`, so a count of `0` is falsy and the `aw.agent/v1` record OMITS `checked` entirely. That is the dangerous case: a checker that examined zero artifacts and reports `clean` is indistinguishable, in `--agent` output, from a genuinely clean tree, and a test asserting the count via `--agent` passes vacuously.
- Scope: IN: the one expression in `to_agent_record` (use `data["checked"]` when the key is present, else fall back to `total_checked`); outcome tests for `aw specs check --agent` and `aw backlog check --agent` on empty trees. OUT: adding `checked` to commands that do not put it in `data` today; the human renderer; the `--json` renderer (already emits `data.checked` verbatim); `aw check <target>` (its `data` carries no `checked` key, only an `inventory` evidence value, so it is unaffected and unchanged).
- Scope-Paths: agent_workflows/result_types.py, tests/test_agent_checked_count.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: an3vqw
- Blocks-Release: next
- Set: specsread
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: kifrou
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 PR-002 PR-003 fixed in place
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog an3vqw: Emit checked:0 in --agent records instead of dropping it.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A command that reports a checked count reports it in `--agent` output at every value including `0`, so "examined nothing" is visible to an agent consumer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Reproduce, audit, fix

- [ ] E-01 Reproduce at HEAD: in a temp dir with `git init` and empty `.aw/records/specs/` and `.aw/records/backlog/open/`, run `aw specs check --agent` and `aw backlog check --agent` and confirm neither record has a `checked` key. Audit emitters and consumers: `git grep -n '"checked"' agent_workflows/` and `git grep -n '"checked" not in\|checked.*not in\|assertNotIn("checked"' tests/` to confirm which commands put `checked` in `data` and that no test relies on its omission.
  - Depends on: none
  - Expected outcome: both records lack `checked` (measured at authoring). Emitters putting `checked` into `CommandResult.data`: `specs.run_check` (`data={"checked": len(paths), ...}`) and `backlog.run_check` (`data={"checked": items_count, ...}`) only; no `data` anywhere sets `total_checked`. No test asserts the key's absence.
  - Execution state: pending
- [ ] E-02 In `result_types.CommandResult.to_agent_record`, replace `checked_count = self.data.get("checked") or self.data.get("total_checked")` with a presence test: `checked_count = self.data["checked"] if "checked" in self.data else self.data.get("total_checked")`. Keep the existing `if checked_count is not None` / `int(...)` guard unchanged, so a command that omits the key still emits none (no behavior change for commands with no count).
  - Depends on: E-01
  - Expected outcome: a present `0` is emitted as `"checked":0`; an absent key still emits nothing.
  - Execution state: pending

### Task group 2: Outcome tests

- [ ] E-03 Add `tests/test_agent_checked_count.py` with two outcome tests that run the real CLI (`tests.support.run_cli`) in a temp git repo with empty specs and backlog trees (`.aw/records/specs/` and `.aw/records/backlog/open/` created, `git init` run): `aw specs check --agent` emits a result record with `"checked": 0`; `aw backlog check --agent` emits a result record with `"checked": 0`. Parse the JSONL line, assert `schema == "aw.agent/v1"` and BOTH `"checked" in rec` and `rec["checked"] == 0` -- assert the key's PRESENCE separately from its value, because `rec.get("checked") == 0` is not a valid substitute (a `.get` default of `None` fails the comparison but an author writing `rec.get("checked", 0)` would re-create the exact vacuous pass this plan exists to remove). Add one non-zero control in the same file asserting `checked == 1`, so the test is not satisfied by a hard-coded 0.
  - Depends on: E-02
  - Expected outcome: all three pass after E-02; the two zero-case tests FAIL at HEAD (key absent).
  - Execution state: pending
  - Control-fixture argv, MEASURED at review so the executor spends no round trip on a usage error: `aw specs new --title <t> --slug <s> --apply` writes one spec and `aw specs check --agent` then reports `"checked":1`. For backlog, `aw backlog new` REFUSES without `--priority` (`--priority required: decide the item's priority ... and work kind`) and without `--apply` it only PREVIEWS and writes nothing, so the count stays 0 and the control would pass vacuously; the working form is `aw backlog new --summary <s> --work-kind chore --priority low --apply`, after which `aw backlog check --agent` reports `"checked":1`. A hand-written minimal fixture file is equally acceptable if it conforms (a non-conforming fixture turns the control's `outcome` to `findings`, which is a different assertion, so prefer the verbs).
- [ ] E-04 Run the bare suite `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: suite green with no failure attributable to the new `checked` key. Baseline measured at review on this tree, bare run: `2458 passed, 2 skipped`. Re-derive the baseline at execution time rather than treating that number as the bar (the suite is a live population); the property to hold is "no test fails that passed before this change".
  - What this step does and does not prove (corrected at review, PR-001): its value is the ABSENCE of a consumer relying on the omitted key (F-5), not a positive assertion of the new field, which is E-03's job alone. There is no live CLI-conformance gate behind it: `tests/conformance_matrix.py` lists `specs check` / `backlog check` in `LIVE_SAFE_LEAVES`, but the harness is INERT (F-7) -- both of its consumer modules were deleted in commit `19313eed`, nothing imports it, and pytest collects zero tests from it. The bare suite is therefore the whole regression surface for this change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `--agent` records are `aw.agent/v1`, additive-fields-only within v1 (`docs/cli-output-contract.md`); emitting a key that was previously omitted at one value is additive and needs no schema bump.
- `--json` already emits `data.checked` verbatim, which is why `tests/test_specs_recursive_read.py` routes its count assertions through `--json` (backlog an3vqw).
- Tests invoke the CLI via `tests.support.run_cli` (pinned to this tree by `PYTHONPATH`).
- Commits via `aw commit kifrou -- <paths>`; suite run bare.

## Findings

| # | Evidence (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | `result_types.CommandResult.to_agent_record`, "checked_count = self.data.get(\"checked\") or self.data.get(\"total_checked\")" (~:403) | Confirmed. |
| F-2 | `specs.run_check` `data={"checked": len(paths), "violations": len(drift)}` (~:585); `backlog.run_check` `data={"checked": items_count, ...}` (~:1455) | Confirmed emitters. |
| F-3 | `cli.py` `{"checked": total_checked}` (~:11569) | CORRECTION TO THE BRIEF: this is an `Evidence(key="inventory", value=...)` value, not `CommandResult.data`; `aw check`'s `data` has no `checked` key. It never reaches the line being fixed, so `aw check specs --agent` emits no `checked` at any count (measured: no key on an empty tree) and is unchanged by this plan. |
| F-4 | measured on an empty temp repo | `aw specs check --agent` -> `{...,"outcome":"clean","exit":0,...,"findings":0,...}` with no `checked`; `aw backlog check --agent` likewise. In this repo `aw specs check --agent` emits `"checked":38`. |
| F-5 | `git grep '"checked" not in' tests/` | No test relies on the omission. The only `checked` assertions in tests (`tests/test_specs_recursive_read.py`) read `--json` `data.checked`, unaffected. |
| F-6 | `git grep -n 'total_checked' agent_workflows/` | `total_checked` exists only as a local variable in `cli.py`; no `data` sets that key. The fallback is dead but harmless and is kept (removing it is out of scope and changes nothing observable). |
| F-7 | ADDED at review (PR-001). `tests/conformance_matrix.py:6` names its consumers; `git log --diff-filter=D --all` -> both deleted in `19313eed`; no importer; `pytest --collect-only tests/conformance_matrix.py` -> `no tests collected` | **THE CONFORMANCE HARNESS E-04 CITED IS INERT.** `specs check` and `backlog check` ARE listed in its `LIVE_SAFE_LEAVES`, but the module is dead data, so no live output-contract gate covers this change. The bare suite is the whole regression surface, and it proves only that nothing depended on the omitted key. |
| F-8 | ADDED at review (PR-003). `tests/support.py:270-283`, `run_cli` docstring "pinned to THIS tree via `PYTHONPATH`" and the `merged_env["PYTHONPATH"] = f"{root_str}..."` prepend | **`run_cli` PINS THE CLI TO THIS TREE, SO A NAIVE BEFORE-FIX RUN LIES.** Setting `PYTHONPATH` to an older tree does NOT change which package a `run_cli` test resolves; it still exercises the fixed code and passes. V-03 carries the caveat and the two acceptable alternatives. |
| F-9 | ADDED at review (PR-002). Measured: `aw backlog new --summary X --work-kind chore` refuses (`--priority required`); without `--apply` it previews and writes nothing; `--priority low --apply` writes and yields `"checked":1`. `aw specs new --title X --slug x --apply` yields `"checked":1` | **THE NON-ZERO CONTROL CAN PASS VACUOUSLY.** Omitting `--apply` leaves the tree empty, so a control asserting a count would measure zero. E-03 now carries the exact working argv for both fixtures. |
| F-10 | ADDED at review. Driving the real `to_agent_record()` across `{"checked":0}`, `{"checked":1}`, `{}`, `{"checked":None}`, `{"total_checked":0}` | The proposed expression is CORRECT at every value: `0` becomes `"checked":0`, an absent key still emits nothing, and an explicit `None` still emits nothing (the `is not None` guard). No command that omits a count changes behavior. |

## Proposed changes (ordered, validatable)

1. E-01 reproduce and audit.
2. E-02 one-expression fix.
3. E-03 outcome tests (zero on both commands, non-zero control).
4. E-04 full suite.

## Deferred / out of scope (with reason)

- Making `aw check <target> --agent` report a checked count (F-3): a new field on a different command, not the reported defect. File separately if wanted.
  - Carrier-Declined: not a defect; no user has asked for a checked count on aw check, and nothing reads one.
- The same falsy-`or` shape elsewhere in `to_agent_record`: audited, `grep -n "self.data.get([^)]*) or" agent_workflows/result_types.py` returns only this line.
  - Carrier-Declined: audited; no other occurrence exists, so nothing is outstanding.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

The maintainer's standing rule is to test OUTCOMES only: the tests run the real CLI and assert the emitted record, never the source expression. Three tests in one new file: two zero-count cases (the bug) and one non-zero control (proves the value is real, not a constant). Each zero-count test fails at HEAD, which V-03 must demonstrate.

REVIEW CORRECTION (PR-001): the bare suite is the ONLY regression surface here. `tests/conformance_matrix.py` lists `specs check` / `backlog check` among its live-safe leaves and would have been the natural output-contract gate, but it is INERT (F-7), so E-03's three tests are the only thing that will ever assert this field's presence. That raises the bar on them: the zero-case tests must assert the KEY'S PRESENCE separately from its value (F-9's reasoning), and the non-zero control must be shown to actually write a fixture rather than preview one.

## Spec / documentation sync

No `.spec.md` amended. `docs/cli-output-contract.md` shows `"checked":17` in an example and does not state that a zero count is omitted, so emitting `0` brings behavior in line with the documented shape; no doc edit needed.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the two `--agent` lines from the empty temp repo at HEAD (no `checked` key) and the two `git grep` outputs (emitters list; empty absence-reliance grep).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/result_types.py` (one expression changed) and the same two `--agent` lines re-run after the fix, each now containing `"checked":0`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_agent_checked_count.py` passing (3 passed), AND the same file's output run against UNFIXED code, showing the two zero-count tests FAIL (on the key's absence) and the control PASSES. A control that also fails means the test is broken rather than the bug being demonstrated, so report instead of proceeding.
  - How to get the before-fix run WITHOUT touching your own edit (method corrected at review, PR-003; the previous copy-the-file-aside-and-restore dance risked losing the fix if anything failed between the two steps, which is the one irreversible outcome in this plan): create a throwaway worktree pinned at the pre-change commit and run the NEW test file against it, e.g. `git worktree add --detach .aw/tmp/kifrou-head <pre-change-commit>`, then `PYTHONPATH=.aw/tmp/kifrou-head python3 -m pytest -o addopts="" tests/test_agent_checked_count.py` (the test file itself stays in your tree; only the imported package is the old one). Remove it with `git worktree remove --force .aw/tmp/kifrou-head` when done. `.aw/tmp/` is gitignored, so nothing is committed. Verified at review that such a worktree does carry HEAD's unfixed `checked_count = self.data.get("checked") or ...` line. `git stash` remains FORBIDDEN here (shared checkout; it moves a co-worker's unstaged work).
  - CAVEAT, so a clean before-fix run is not misread: `tests.support.run_cli` PREPENDS its own `REPO_ROOT` to `PYTHONPATH`, so a test using that helper resolves the CLI from THIS tree regardless of the variable above and would show the FIXED behavior. For the before-fix run, invoke the old tree's package explicitly (e.g. run the subprocess with `cwd` in the temp repo and `PYTHONPATH` set to the throwaway worktree, bypassing `run_cli`), or run the before-fix check as a direct two-command reproduction (the V-01 commands executed against the old worktree's package) and paste that instead. Either is acceptable; what is NOT acceptable is pasting a "failure" you did not actually observe, or a pass you obtained from the fixed tree while labelling it before-fix.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (`N passed`, no failures). Compare against the review baseline `2458 passed, 2 skipped` (measured on this tree at HEAD `457bad3c`) and expect it to RISE by the three tests E-03 adds; the bar is that no test which passed before now fails, NOT that the number matches, since the suite is a live population.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a one-expression change to the shared `--agent` record builder. Blast radius audited (F-2, F-3, F-6) and RE-DERIVED at review: only `specs check` and `backlog check` feed a `checked` key, and the only visible change is that they now emit `"checked":0` where they emitted nothing. Additive under `aw.agent/v1` (`docs/cli-output-contract.md:214`). Confirmed at review by driving the real `to_agent_record()` across the value space (F-10): a command that supplies no count is byte-identical before and after, and an explicit `None` still emits nothing. The one class of consumer this repository cannot survey is an EXTERNAL agent or CI script reading `--agent`; such a consumer begins seeing a `checked:0` it never saw, which is precisely what the additive-field clause licenses, and it is the honest residual risk of this change.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/result_types.py` (the one expression) and the new test file. Do not expand scope casually; a genuinely required out-of-fence edit is made and JUSTIFIED at finalize with `--scope-reason`. Genuine stop condition: E-01's audit finds a consumer that relies on the key's absence (then report before changing the contract).

HONESTY RULE (hard MUST): paste the ACTUAL runner output; V-03's before-fix failure must be real.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit kifrou -- <paths>`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, transition with `aw ipd finalize kifrou --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). This plan inherits `- Blocks-Release: next` from backlog `an3vqw`; then set that item `done` with `--evidence` citing the executed plan.
