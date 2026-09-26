# IPD: Make every From-Backlog reader agree on the absent sentinels and flip the release-gates CI step to fail-closed

- Date: 2026-09-26
- Kind: child
- Concern: Three readers of `- From-Backlog:` disagree about the literal values `-`, `none` and `unresolved`. `runner_shared._read_from_backlog` treats `{"-", "none", "unresolved"}` as ABSENT; `releases.check_from_backlog` (via `releases._ITEM_FROM_BACKLOG_RE`) reports each of them as `check.from-backlog-dangling`; `check_engine._META_FROM_BACKLOG_RE` (read by `find_from_backlog_plans`, `find_from_backlog_specs`, `_from_backlog_carrier_index`, the graduation index and the orphaned-blocker warning) indexes the literal as if it were an id6. The data finding that made this visible (an executed plan's `From-Backlog: none`) was removed by `dc1e791c`, and `aw check release-gates --agent` reports 0 findings at HEAD, but the code disagreement is live and the next hand-written sentinel re-reds the family. Separately, the CI `aw check release-gates` step is still advisory with a comment citing findings that no longer exist.
- Scope: IN: one schema constant naming the absent sentinels; all three readers consult it; outcome tests; flip the CI step to fail-closed and replace its stale comment. OUT: multi-valued `From-Backlog` (backlog 6os96s, which needs a single-vs-multi decision first); the setter `releases.set_from_backlog_line`.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/releases.py, agent_workflows/check_engine.py, agent_workflows/runner_shared.py, tests/test_check_engine_release_gate.py, .github/workflows/tests.yml
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 7dcw6z
- Blocks-Release: next
- Set: frombacklog
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3cs7qg

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 7dcw6z: one sentinel set shared by all three From-Backlog readers, outcome tests, and the release-gates CI step flipped to fail-closed (0 findings at HEAD 61ef21d8).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every surface that reads `- From-Backlog:` gives the same answer for `-`, `none` and `unresolved` (absent, no finding, no carrier), and the release-gate family becomes a fail-closed CI gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one sentinel set, three readers

- [ ] E-01 In `agent_workflows/ipd_schema.py`, directly below `META_FROM_BACKLOG`, add `FROM_BACKLOG_ABSENT_SENTINELS: frozenset = frozenset({"-", "none", "unresolved"})` with a comment: these literal values mean "no source item" and every reader treats them as if the field were absent; comparison is case-insensitive after stripping surrounding quotes. Add a helper `from_backlog_is_absent(value: str | None) -> bool` beside it (True for None, empty, or a sentinel), so readers share the comparison as well as the set.
  - Depends on: none
  - Expected outcome: one importable definition.
  - Execution state: pending

- [ ] E-02 Make the three readers use it. (a) `releases.check_from_backlog`: skip the match when `ipd_schema.from_backlog_is_absent(m.group(1))`. (b) `runner_shared._read_from_backlog`: replace the inline `raw in {"-", "none", "unresolved"}` with the helper. (c) `check_engine`: add a module-private `_from_backlog_value(text) -> str | None` that runs `_META_FROM_BACKLOG_RE.search` and returns None for an absent sentinel, and route every single-value call site through it (`find_from_backlog_plans`, `find_from_backlog_specs`, `_from_backlog_carrier_index`, and the plan-gate index in the orphaned-live-blocker check); in the graduation reverse index that uses `_META_FROM_BACKLOG_RE.finditer`, filter sentinel values out of `sources`. Do not change either regex's shape (that is 6os96s's decision).
  - Depends on: E-01
  - Expected outcome: a sentinel produces no dangling finding, no carrier entry, and no graduation edge on any surface.
  - Execution state: pending

- [ ] E-03 Add outcome tests to `tests/test_check_engine_release_gate.py`, reusing `_create_minimal_repo`: for each of `-`, `none`, `unresolved` (subTest), a plan with `- From-Backlog: <value>` yields 0 `check.from-backlog-dangling` from `check_engine.check_release_gates(repo)`, and `check_engine.find_from_backlog_artifacts(repo, <value>)` returns empty; `runner_shared._read_from_backlog(<plan text>)` returns None. One case with a real-shaped but unknown id6 (`zz9zz9`) yields exactly 1 `check.from-backlog-dangling`. Outcomes only; no test reads source text or pins the constant's spelling.
  - Depends on: E-02
  - Expected outcome: 4 cases pass; the three sentinel cases fail against the pre-change `releases.check_from_backlog`.
  - Execution state: pending

### Task group 2: fail-closed CI gate

- [ ] E-04 In `.github/workflows/tests.yml`, first run `python -m agent_workflows check release-gates --agent` at the branch head and confirm `"findings":0` and exit 0 (measured at HEAD `61ef21d8`: `outcome":"conforms","exit":0,...,"findings":0`). Then change the step named `aw check release-gates (release-gate family; ADVISORY until baseline findings cleared)` to `aw check release-gates (release-gate family; fail closed)` with `run: python -m agent_workflows check release-gates --agent` (drop the `|| echo "::warning::..."` fallback), and replace the six-line comment above it (which cites `7l1ggb` and an executed plan's `From-Backlog: none`, neither of which is a finding any more) with one line: it joined the fail-closed set once the family reported zero findings (plan 3cs7qg). If the check reports ANY finding at the branch head, do not flip; see the stop condition.
  - Depends on: E-02
  - Expected outcome: the step fails the job on any release-gate finding.
  - Execution state: pending

- [ ] E-05 Run the bare suite `python3 -m pytest`.
  - Depends on: E-03, E-04
  - Expected outcome: green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_schema.META_FROM_BACKLOG` is the field-name authority (runner_shared cites it, zhr6mc E-01); the sentinel set belongs beside it.
- `ipd_authoring` scaffolds `- Item-Dependencies: unresolved` and `- Work-Kind/Priority: unresolved`; `unresolved` is the toolkit's general "not yet decided" sentinel, which is why it belongs in the set.
- Tests assert OUTCOMES only (maintainer rule): no source-text or constant-spelling pins.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `releases.check_from_backlog` | Flags `-`, `none`, `unresolved` as dangling. | `m and m.group(1) not in known` with `_ITEM_FROM_BACKLOG_RE = re.compile(r"(?m)^- From-Backlog:\s*(\S+)\s*$")` |
| F-2 | MED | `runner_shared._read_from_backlog` | Treats the same three as absent: the runner and the checker disagree. | `if not raw or raw in {"-", "none", "unresolved"}: return None` |
| F-3 | LOW | `check_engine._META_FROM_BACKLOG_RE` consumers | A third reader with no sentinel handling at all; it would index `none` as a carrier key. | `_META_FROM_BACKLOG_RE = _re.compile(r"(?m)^- From-Backlog:[ \t]*(\S+)[ \t]*$")` used by `find_from_backlog_plans` etc. |
| F-4 | INFO | tree | 0 tracked records carry a sentinel today; the family is clean. | `grep -rn "^- From-Backlog: \(none\|-\|unresolved\)\s*$" .aw/records` -> 0; `aw check release-gates --agent` -> `findings":0`, exit 0 |
| F-5 | LOW | `.github/workflows/tests.yml` release-gates step | Still advisory, and its comment cites two findings that no longer exist. | comment names `7l1ggb` and "executed plan mjx7ne with From-Backlog: none" |
| F-6 | INFO | backlog 6os96s | Multi-valued `From-Backlog: a, b` is invisible to both anchored regexes. Same code, but NOT small: it first needs a single-valued-vs-multi-valued decision, and the only corpus instance (`nmlx47`) is now in `superseded/`. Not folded in. | 6os96s body; `.aw/records/plans/superseded/20260917-hostdedup-02-nmlx47-...ipd.md` `- From-Backlog: dstnso, 8hx3g3` |

## Proposed changes (ordered, validatable)

1. E-01: sentinel constant and helper.
2. E-02: all readers use it.
3. E-03: outcome tests.
4. E-04: fail-closed CI step.
5. E-05: bare suite.

## Deferred / out of scope (with reason)

- Multi-valued `From-Backlog` (F-6): needs a maintainer decision on the field's cardinality before either regex changes, and this plan must not diverge the two regexes.
  - Carrier: 6os96s

## Scope check

- Over-scope: none. The CI flip is in the backlog item's own resolution path (plan 2vw35i F-8 named this sentinel verdict as the blocker for the flip).
- Under-scope: none for the declared concern.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_check_engine_release_gate.py -v`.
- `python -m agent_workflows check release-gates --agent` before and after.
- Bare `python3 -m pytest`.
- Test rule: outcomes only.

## Spec / documentation sync

N/A: no `.spec.md` defines the From-Backlog sentinel values; AGENTS.md describes the field and the dangling rule without listing sentinels, and this change makes all readers match the runner's already-shipped behavior.

## Open questions

### OQ-01: Should `unresolved` count as absent, or as a finding (an undecided field on a plan)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Absent, matching the runner's shipped `_read_from_backlog`. `From-Backlog` is optional, so an undecided value carries no handoff claim; readiness of undecided fields is policed elsewhere (the approval floor refuses `unresolved` Priority/Work-Kind), not by the dangling-link rule.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff; paste `python3 -c 'from agent_workflows import ipd_schema as s; print([s.from_backlog_is_absent(v) for v in (None, "", "-", "none", "NONE", "\"none\"", "unresolved", "abc123")])'` showing `[True, True, True, True, True, True, True, False]`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the three readers; paste `grep -n '"none"' agent_workflows/releases.py agent_workflows/runner_shared.py agent_workflows/check_engine.py` showing no remaining inline sentinel set.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_check_engine_release_gate.py -v` showing the new cases passed; revert only the `releases.check_from_backlog` hunk IN THE WORKTREE and paste the three sentinel cases FAILING with a `check.from-backlog-dangling` finding (not an import error) while the unknown-id6 case still passes; restore.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python -m agent_workflows check release-gates --agent; echo exit=$?` at the branch head showing `findings":0` and `exit=0`; paste the `tests.yml` diff showing the `|| echo` fallback and the stale comment removed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed; name any failure as pre-existing (with evidence at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. A behavior alignment: `aw check` stops flagging the three sentinel values the runner already ignores, and the release-gate family becomes a fail-closed CI step. The CI flip is the consequential half: after it, any `check.live-bug-ungated`, `check.from-backlog-dangling`, `check.blocks-release-dangling` or similar finding fails the tests workflow on `main`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if `aw check release-gates --agent` reports any finding at the branch head when E-04 runs, do NOT flip the step and do NOT edit another party's artifact to clear it; complete E-01..E-03, leave the step advisory with an updated comment naming the actual finding, and report.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `7dcw6z` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`. Backlog 6os96s stays open.
