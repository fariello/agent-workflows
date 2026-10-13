# IPD: Stop starting new run work when CI has not passed in N commits, with an override

- Date: 2026-10-12
- Kind: child
- Concern: Showing CI's state (Order 02) makes a red CI visible, but runs keep adding commits on top of it. The maintainer asked for a hard stop that can be overridden: when CI has not passed in more than N main commits, a run must not start new work unless told to, and the reason for overriding must be kept.
- Scope: (1) At run start, after Order 02's checkup step, read the saved checkup record (never GitHub). If it says CI's last pass is more than N first-parent commits behind main (N = `ci_checkup_interval_commits`, the same setting), refuse to start before any agent turn, with a message naming the last passing commit, the count, and the two ways forward. (2) `--allow-red-ci "<why>"` on `aw oc run` and `aw agy run` overrides it; the reason is required and is recorded in the run's events and summary. (3) Always allowed with no flag: a run whose every selected item belongs to Set `cihealth`, so the stop cannot block its own fix. (4) UNKNOWN CI state (no `gh`, no network, no record) never stops a run; it warns. (5) Interval `0` disables the stop.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_red_ci_stop.py, CHANGELOG.md, README.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:n7xlhm, executed:ezyb4a
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 5st6e5
- Blocks-Release: next
- Set: cihealth
- Order: 3
- Highest E allocated: 04
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: s4z5n8

## Workflow history
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored during /plan-review of Set gradfix from the maintainer's 2026-10-12 ruling ("hard stop that can be overridden").
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

No run piles new work on a CI that has been red for more than N commits unless a person decided it should and said why, while the plans that repair CI always run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the stop

- [ ] E-01 Add the decision as one shared predicate in `runner_shared` (both hosts call it): inputs are the saved checkup record (Order 02's reader), the setting, the selected queue, and the override reason; output is ALLOW, ALLOW-WITH-WARNING (unknown state, or overridden, with the text to print), or REFUSE (with the message). REFUSE only when the record is PRESENT, says CI's last pass is more than N commits behind main as of the record, and no override is given and not every selected item has `- Set: cihealth`. Re-count commits since the last pass against current main when the record is older than main, so a stale record is not read as fresher than it is.
  - Depends on: none
  - Expected outcome: a pure function returning the right verdict for each combination.
  - Execution state: pending

- [ ] E-02 Wire it into both runners and add the flag. Call E-01 after the checkup step and before the first agent turn; on REFUSE, exit nonzero with the message and an `aw.agent/v1` refusal record under `--agent`, having changed nothing. Add `--allow-red-ci WHY` to `aw oc run` and `aw agy run` (and their `resume`), refusing an empty reason, and record `red-ci-override` with the reason and the CI state in events and the run summary. `--full-auto` does not imply it.
  - Depends on: E-01
  - Expected outcome: a refused run starts no session; an overridden run starts and its summary names the reason.
  - Execution state: pending

### Task group 2: prove and document

- [ ] E-03 Add `tests/test_red_ci_stop.py`, driving the real runner entry points with a scripted host and a pre-written checkup record, asserting on exit codes, output, events and spawned-agent counts, never on source text. Cases: (a) red beyond N: refused, no agent spawned, message names the last passing commit; (b) same with `--allow-red-ci "fixing X"`: runs, reason in events and summary; (c) empty reason refused by the parser; (d) every selected item in Set `cihealth`: runs with no flag; (e) unknown state and missing record: runs with a warning; (f) interval 0: runs silently; (g) red but within N: runs; (h) both hosts behave the same for (a) and (b).
  - Depends on: E-02
  - Expected outcome: the new module passes.
  - Execution state: pending

- [ ] E-04 Amend spec `25kzda` where it lists what a run checks before its first turn, adding the red-CI stop, its override, and the CI-repair exemption; add README and CHANGELOG lines (no em or en dashes). Run the bare suite and paste its summary line.
  - Depends on: E-03
  - Expected outcome: the spec diff, doc lines, and a green bare suite.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- Attested overrides require a non-empty reason and are recorded (precedent: `--allow-uncovered-orchestrator-work '<why>'`).
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Runs have no CI awareness. | No caller of `gh` in `agent_workflows/` (Order 02 F-01). |
| F-02 | An attested-override precedent exists. | `aw oc run --allow-uncovered-orchestrator-work '<why>'` requires and records a justification (AGENTS.md, orchestrator coverage gate). |
| F-03 | Shipping this before CI is green would stop every run. | CI red at review (Order 01 F-01); hence `Item-Dependencies: executed:ezyb4a`. |

## Proposed changes (ordered, validatable)

1. Shared predicate (E-01). 2. Wiring and flag (E-02). 3. Tests (E-03). 4. Spec and docs (E-04).

## Deferred / out of scope (with reason)

- Stopping hand commits or pushes: those do not go through a run; the checkup line in `aw attention` / `aw doctor` covers them.
  - Carrier-Declined: a git hook would be local, skippable, and slow every commit, which the maintainer ruled out.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `tests/test_red_ci_stop.py` (new).
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

Spec `25kzda` amended (E-04), listed in Scope-Paths. WHY: it describes what a run checks before starting, and this adds a refusal that every reviewer of the runner must know. README and CHANGELOG lines.

## Open questions

### OQ-01: Should UNKNOWN CI state stop a run?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Being offline or lacking `gh` must not stop work; it warns, and `aw attention` shows "CI status unknown". Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the predicate's verdict for each E-03 case, pasted as a table.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a refused run and an overridden run (human and `--agent`), produced by the run-start path E-02 creates.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new module passing, with each case named.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the spec diff, the doc lines, and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval, and only after Orders 01 (`ezyb4a`) and 02 (`n7xlhm`) are executed. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit s4z5n8 -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize s4z5n8` only after `aw ipd lint --phase pre-transition` conforms.
