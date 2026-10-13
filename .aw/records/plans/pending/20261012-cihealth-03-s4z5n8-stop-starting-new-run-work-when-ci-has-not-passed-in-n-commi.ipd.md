# IPD: Stop starting new run work when CI has not passed in N commits, with an override

- Date: 2026-10-12
- Kind: child
- Concern: Showing CI's state (Order 02) makes a red CI visible, but runs keep adding commits on top of it. The maintainer asked for a hard stop that can be overridden: when CI has not passed in more than N main commits, a run must not start new work unless told to, and the reason for overriding must be kept.
- Scope: (1) At run start, after Order 02's checkup step, read the saved checkup record (never GitHub). If it says CI's last pass is more than N first-parent commits behind main (N = `ci_checkup_interval_commits`, the same setting), refuse to start before any agent turn, with a message naming the last passing commit, the count, and the two ways forward. (2) `--allow-red-ci "<why>"` on `aw oc run` and `aw agy run` overrides it; the reason is required and is recorded in the run's events and summary. (3) Always allowed with no flag: a run whose every selected item belongs to a Set listed in the project setting `ci_red_exempt_sets` (default empty; this repository sets `["cihealth"]`), so the stop cannot block its own fix. Any other CI repair uses `--allow-red-ci`, which the refusal names. (4) UNKNOWN CI state (no `gh`, no network, no record) never stops a run; it warns. (5) Interval `0` disables the stop.
- Scope-Paths: .aw/config/project.json, agent_workflows/config.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_red_ci_stop.py, CHANGELOG.md, README.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:n7xlhm, executed:ezyb4a
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 5st6e5
- Blocks-Release: next
- Set: cihealth
- Order: 3
- Highest E allocated: 05
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: s4z5n8

## Workflow history
- 2026-10-13 reviewed (aw set): plan-review done
- 2026-10-12 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored during /plan-review of Set gradfix from the maintainer's 2026-10-12 ruling ("hard stop that can be overridden").
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

No run piles new work on a CI that has been red for more than N commits unless a person decided it should and said why, while the plans that repair CI always run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the stop

- [ ] E-01 Add the decision as one shared predicate in `runner_shared` (both hosts call it): inputs are the saved checkup record (Order 02's reader), the setting, the selected queue, and the override reason; output is ALLOW, ALLOW-WITH-WARNING (unknown state, or overridden, with the text to print), or REFUSE (with the message). REFUSE only when the record is PRESENT, says CI's last pass is more than N commits behind the branch, no override is given, and not every selected item's `- Set:` is in `ci_red_exempt_sets`. Keep the predicate PURE: the caller passes the commits-since-last-pass count, re-counted against the CURRENT tip of Order 02's `ci_checkup_branch` (`git rev-list --count --first-parent <last-pass>..<branch>`) when the record is older than the tip, so a stale record is not read as fresher than it is; a count that cannot be computed (last-pass commit not in local history) is UNKNOWN, which warns. Read `ci_red_exempt_sets` through the project-config loader beside Order 02's settings (a list of Set ids, default `[]`, malformed values warn and fall back, as `config.release_gate_work_kinds` does), and set it to `["cihealth"]` in this repository's `.aw/config/project.json`.
  - Depends on: none
  - Expected outcome: a pure function returning the right verdict for each combination, and the setting loader.
  - Execution state: pending

- [ ] E-02 Wire it into both runners. Add `enforce_red_ci_gate` to `runner_shared` and call it from `runner_shared.initialize_run_core` (the shared path both hosts use), after Order 02's checkup step and after the run directory exists, BEFORE the `--prepare-only` early return and before any agent turn or session, sited exactly as `enforce_spec_edit_ack_gate` is (spec `25kzda` 2.5c), so a prepared queue cannot later be resumed past the gate. On REFUSE: record a durable refusal (refusal code `red-ci`, an event in `events.jsonl`, state persisted) so it is readable in `aw runs`, raise `DriverError` with the message, exit nonzero, and emit an `aw.agent/v1` refusal record under `--agent`; spawn no session and touch no repository file. On an override, record a `red-ci-override` event with the reason and the CI state, and show the reason in the run summary.
  - Depends on: E-01
  - Expected outcome: a refused run (including under `--prepare-only`) starts no session and its refusal is readable afterwards; an overridden run starts and its summary names the reason.
  - Execution state: pending

- [ ] E-05 Add the flag. Register `--allow-red-ci` as a `runner_shared.RunPolicyFlag` row (`kind="str"`, so argparse requires a value; refuse an empty or whitespace-only value; `owner="runner_shared.enforce_red_ci_gate"`; `resume_rule=RESUME_REFUSE`, because `resume` does not call `initialize_run_core` and consent accepted there would gate nothing, the reasoning recorded on the `--ack-spec-edits` row), so both `aw oc run` and `aw agy run` get it from the one table. Its help text says it waives only this gate. `--full-auto` does not imply it.
  - Depends on: E-02
  - Expected outcome: both hosts parse the flag; an empty value and a value on `resume` are refused.
  - Execution state: pending

### Task group 2: prove and document

- [ ] E-03 Add `tests/test_red_ci_stop.py`, driving the real runner entry points with a scripted host and a pre-written checkup record, asserting on exit codes, output, events and spawned-agent counts, never on source text. Cases: (a) red beyond N: refused, no agent spawned, message names the last passing commit, durable refusal event present; (a2) the same under `--prepare-only`: refused; (b) same with `--allow-red-ci "fixing X"`: runs, reason in events and summary; (c) empty reason refused by the parser, and `--allow-red-ci` on resume refused; (d) every selected item in a Set listed in `ci_red_exempt_sets`: runs with no flag, and a mixed queue (one exempt, one not) is refused; (e) unknown state and missing record: runs with a warning; (f) interval 0: runs silently; (g) red but within N: runs; (g2) a record older than the branch tip whose re-count crosses N: refused; (h) both hosts behave the same for (a) and (b); (i) `--full-auto` alone does not override.
  - Depends on: E-02, E-05
  - Expected outcome: the new module passes.
  - Execution state: pending

- [ ] E-04 Amend spec `25kzda`: add `[--allow-red-ci <justification>]` to the Section 2.1 grammar and a bullet for it beside `--ack-spec-edits` (every registered `RunPolicyFlag` row must be declared in 2.1 in the same change, per the comments on the `--allow-uncovered-orchestrator-work` and `--allow-concurrent-driver` rows); add it to 2.1's "`--full-auto` ... does not imply" list; and add a section `2.5f Red-CI gate` after 2.5e stating the trigger, the exemption setting, UNKNOWN never refusing, the durable refusal, and the `--prepare-only` siting; add README and CHANGELOG lines (no em or en dashes). Run the bare suite and paste its summary line.
  - Depends on: E-03
  - Expected outcome: the spec diff, doc lines, and a green bare suite.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- Attested overrides require a non-empty reason and are recorded (precedent: `--allow-uncovered-orchestrator-work '<why>'`).
- Run policy flags are rows of `runner_shared.RUN_POLICY_FLAGS` (`RunPolicyFlag`), registered on both hosts from the one table; `kind="str"` rows take a justification; `resume_rule` says what resume does with them.
- Run-start gates live in `runner_shared.initialize_run_core`; `enforce_spec_edit_ack_gate` is the precedent for a deterministic gate sited before the `--prepare-only` return with a durable refusal (`tests/test_spec_edit_ack_gate.py` shows the test shape).
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Runs have no CI awareness. | No caller of `gh` in `agent_workflows/` (Order 02 F-01). |
| F-02 | An attested-override precedent exists. | `aw oc run --allow-uncovered-orchestrator-work '<why>'` requires and records a justification (AGENTS.md, orchestrator coverage gate). |
| F-03 | Shipping this before CI is green would stop every run. | CI red at review (Order 01 F-01); hence `Item-Dependencies: executed:ezyb4a`. |
| F-04 | `resume` never calls `initialize_run_core`, so an init-only gate's flag on resume gates nothing. | Comment on the `--ack-spec-edits` `RunPolicyFlag` row (`resume_rule=RESUME_REFUSE`); spec `25kzda` 2.5c "Deterministic and operates under `--prepare-only`". |
| F-05 | Every registered run flag must be declared in spec 2.1. | Comments on the `--allow-uncovered-orchestrator-work` and `--allow-concurrent-driver` rows; spec 2.1 grammar lists `--ack-spec-edits`. |

## Proposed changes (ordered, validatable)

1. Shared predicate and exemption setting (E-01). 2. Gate wiring (E-02). 3. Flag (E-05). 4. Tests (E-03). 5. Spec and docs (E-04).

## Deferred / out of scope (with reason)

- Stopping hand commits or pushes: those do not go through a run; the checkup line in `aw attention` / `aw doctor` covers them.
  - Carrier-Declined: a git hook would be local, skippable, and slow every commit, which the maintainer ruled out.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `tests/test_red_ci_stop.py` (new).
- `tests/test_spec_edit_ack_gate.py` (existing neighbour at the same call site; must stay green).
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

Spec `25kzda` amended (E-04: 2.1 grammar and flag bullet, the `--full-auto` non-implication list, new 2.5f), listed in Scope-Paths. WHY: it describes what a run checks before starting and declares every run flag, and this adds a refusal and a flag that every reviewer of the runner must know. README and CHANGELOG lines.

## Open questions

### OQ-02: How are CI-repair plans recognised for the exemption?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: By a project setting `ci_red_exempt_sets` (list of Set ids, default empty), set to `["cihealth"]` here. A hard-coded `cihealth` literal would be meaningless in other repositories that install this toolkit and would stop exempting anything once a later repair lives in another Set; a new front-matter field would be a schema change for one gate. `--allow-red-ci` covers every other repair. Reversible.

### OQ-01: Should UNKNOWN CI state stop a run?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Being offline or lacking `gh` must not stop work; it warns, and `aw attention` shows "CI status unknown". Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the predicate's verdict for each E-03 case, pasted as a table, and the `ci_red_exempt_sets` value under missing, valid and malformed config.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a refused run, a refused `--prepare-only` run, and an overridden run (human and `--agent`), produced by the run-start path E-02 creates, plus the refusal as shown by `aw runs` afterwards.
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

- [ ] V-05 validates E-05
  - Required evidence: pasted `aw oc run --help` and `aw agy run --help` excerpts showing the flag, and pasted refusals for an empty value and for the flag on resume.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval, and only after Orders 01 (`ezyb4a`) and 02 (`n7xlhm`) are executed. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit s4z5n8 -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize s4z5n8` only after `aw ipd lint --phase pre-transition` conforms.
