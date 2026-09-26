# IPD: Emit a zero checked count in the agent record instead of dropping it

- Date: 2026-09-26
- Kind: child
- Concern: `result_types.CommandResult.to_agent_record` builds the count as `self.data.get("checked") or self.data.get("total_checked")`, so a count of `0` is falsy and the `aw.agent/v1` record OMITS `checked` entirely. That is the dangerous case: a checker that examined zero artifacts and reports `clean` is indistinguishable, in `--agent` output, from a genuinely clean tree, and a test asserting the count via `--agent` passes vacuously.
- Scope: IN: the one expression in `to_agent_record` (use `data["checked"]` when the key is present, else fall back to `total_checked`); outcome tests for `aw specs check --agent` and `aw backlog check --agent` on empty trees. OUT: adding `checked` to commands that do not put it in `data` today; the human renderer; the `--json` renderer (already emits `data.checked` verbatim); `aw check <target>` (its `data` carries no `checked` key, only an `inventory` evidence value, so it is unaffected and unchanged).
- Scope-Paths: agent_workflows/result_types.py, tests/test_agent_checked_count.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: an3vqw
- Blocks-Release: next
- Set: specsread
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: kifrou

## Workflow history
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

- [ ] E-03 Add `tests/test_agent_checked_count.py` with two outcome tests that run the real CLI (`tests.support.run_cli`) in a temp git repo with empty specs and backlog trees: `aw specs check --agent` emits a result record with `"checked": 0`; `aw backlog check --agent` emits a result record with `"checked": 0`. Parse the JSONL line, assert `schema == "aw.agent/v1"` and `rec["checked"] == 0` (key present AND zero). Add one non-zero control in the same file (one spec or backlog item written through `aw specs new ... --apply` or `aw backlog new ...`, or a minimal fixture) asserting `checked == 1`, so the test is not satisfied by a hard-coded 0.
  - Depends on: E-02
  - Expected outcome: all three pass after E-02; the two zero-case tests FAIL at HEAD (key absent).
  - Execution state: pending
- [ ] E-04 Run the bare suite `python3 -m pytest`, including the CLI conformance tests that execute `specs check` / `backlog check` live (`tests/conformance_matrix.py` `LIVE_SAFE_LEAVES`), and confirm nothing depended on the omitted key.
  - Depends on: E-03
  - Expected outcome: suite green.
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
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_agent_checked_count.py` passing (3 passed), AND its output with E-02 temporarily reverted in a scratch working copy (`git stash push agent_workflows/result_types.py` is NOT allowed in a shared checkout; instead copy the file aside, restore HEAD's line, run, then restore your edit) showing the two zero-count tests FAIL and the control passes.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (`N passed`, no failures).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a one-expression change to the shared `--agent` record builder. Blast radius audited (F-2, F-3, F-6): only `specs check` and `backlog check` feed a `checked` key, and the only visible change is that they now emit `"checked":0` where they emitted nothing. Additive under `aw.agent/v1`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/result_types.py` (the one expression) and the new test file. Do not expand scope casually; a genuinely required out-of-fence edit is made and JUSTIFIED at finalize with `--scope-reason`. Genuine stop condition: E-01's audit finds a consumer that relies on the key's absence (then report before changing the contract).

HONESTY RULE (hard MUST): paste the ACTUAL runner output; V-03's before-fix failure must be real.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit kifrou -- <paths>`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, transition with `aw ipd finalize kifrou --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). This plan inherits `- Blocks-Release: next` from backlog `an3vqw`; then set that item `done` with `--evidence` citing the executed plan.
