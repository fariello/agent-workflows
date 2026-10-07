# IPD: Ask before applying the rest of a status batch when some plans are refused, or skip them with --skip-refused

- Date: 2026-10-07
- Kind: child
- Concern: `aw set <status> <many selectors>` is all-or-nothing: if any one record is refused by any pre-flight gate (illegal transition, blocking open question, unready orchestrator, backward move without `--message`, release-gate close legitimacy, graduation handoff), nothing is written and the command exits 1. Measured 2026-10-07: `aw set approved $(aw att ... -id) -y` over 57 reviewed plans wrote nothing because one orchestrator (`itamry`) was unready. The maintainer then has to find the refused plan, remove it from the list and re-run, for every batch.
- Scope: Change `status_set.run_set_command`'s pre-flight so each gate records a per-record refusal instead of returning, then: when some records are refused and others pass, on an interactive terminal show the refused records with their reasons and ask whether to apply the rest; with `--skip-refused`, apply the rest without asking; non-interactive without `--skip-refused`, keep today's all-or-nothing refusal. Always exit 1 when anything was refused. Declare `--skip-refused` on every setter spelling that routes through `run_set_command`. EXCLUDES changing what any gate decides, the message styling owned by `juu1rj`, and refusals that are about the whole command (unknown selector, cross-type ambiguity, missing `--message` for the whole batch is per-record and IS included).
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/cli.py, tests/test_status_set_partial_batch.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: setbatch
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: f42oxd

## Workflow history
- 2026-10-07 to-review (aw set): authored review-ready at the maintainer's request 2026-10-07

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

One refused plan no longer blocks a whole batch: a human is shown what was refused and asked whether to apply the rest, and a script can say `--skip-refused` to do so without asking.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: collect refusals per record

- [ ] E-01 In `status_set.run_set_command`, convert each per-record pre-flight gate (the `validate_transition_allowed` loop, the backlog close-legitimacy check, the graduation handoff check, the terminal-reopen refusal, the backward-move `--message` refusal, and the orchestrator readiness gate) from "render and return" to "append `(record, gate, reason, remedy)` to one refusal list". Whole-command refusals (unknown or ambiguous selector, cross-type fan-out, scoped-type mismatch, the `executed` delegation to finalize) keep returning immediately. Keep gate ORDER and each gate's decision unchanged. For the orchestrator gate, compute `status_overrides` from the records that PASSED the earlier gates, so a child refused earlier is not counted as becoming ready.
  - Depends on: none
  - Expected outcome: with no refusals, behavior and output are byte-identical to today; with refusals, every refused record and its reason are in the list and nothing has been written yet.
  - Execution state: pending

### Task group 2: decide what to do

- [ ] E-02 After pre-flight, when the refusal list is non-empty: if every record is refused, refuse as today. Otherwise list each refused record (id6, gate, reason, remedy) and then: with `--skip-refused`, drop them and continue; else if `term.is_interactive()` (respecting `--no-interactive`, `AW_NONINTERACTIVE` and `CI`), ask "Apply the remaining N and skip these M? [y/N]" and continue on yes; otherwise refuse as today with a hint naming `--skip-refused`. `-y`/`--yes` does NOT imply `--skip-refused`: it confirms writes, not skipping refusals.
  - Depends on: E-01
  - Expected outcome: the three branches behave as stated in a scratch repo; default answer is No.
  - Execution state: pending

- [ ] E-03 When records were skipped, exit 1 after applying the rest, and make the summary and the `--agent`/`--json` result list both the applied and the skipped records (with reasons), so a script can tell partial success from full success.
  - Depends on: E-02
  - Expected outcome: exit 1, the human summary names applied and skipped counts, the agent record has `outcome: findings` with both lists.
  - Execution state: pending

- [ ] E-04 Add `--skip-refused` to every parser that routes to `run_set_command` (`aw set`, `aw ipd set`, `aw spec(s) set`, `aw backlog set` positional), with help text "Apply the records that pass and skip refused ones (each is listed); exit 1 if any were skipped." Add a `CHANGELOG.md` entry.
  - Depends on: E-02
  - Expected outcome: `--help` on each spelling shows the flag.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_status_set_partial_batch.py` driving the real CLI in a scratch repo with one refused orchestrator and two ready plans: non-interactive refuses and writes nothing (today's behavior); `--skip-refused` applies two, skips one, exit 1, both lists in `--agent` output; simulated interactive yes applies, no writes nothing; all refused refuses; no refusals unchanged; `--yes` alone does not skip. Plus one case per converted gate showing it lands in the refusal list. No source introspection.
  - Depends on: E-03, E-04
  - Expected outcome: the module passes and existing `tests/test_status_set.py` still passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The interactivity decision has one definition, `term.is_interactive` (plan `da9n1s`); do not use a bare `isatty`.
- A gate added to one setter spelling and not another is bypassed by choosing the other (`status_set` comments on `--allow-open-questions`); the flag goes on every spelling.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Every per-record gate returns before any write. | `status_set.run_set_command`: "Refusing before making changes" at the transition, close-legitimacy, backward-move and orchestrator gates; the close-legitimacy comment names "the all-or-nothing batch contract". |
| F-02 | One unready orchestrator blocked 57 approvals. | Session 2026-10-07, `itamry`. |
| F-03 | Maintainer ruling 2026-10-07: ask interactively unless `--skip-refused` is given. | Session 2026-10-07. |

## Proposed changes (ordered, validatable)

1. Collect refusals per record (E-01).
2. Ask, skip, or refuse (E-02).
3. Exit code and reporting (E-03).
4. Flag on every spelling, changelog (E-04).
5. Tests (E-05).

## Deferred / out of scope (with reason)

- Clearer refusal wording and styling.
  - Carrier: juu1rj

## Scope check

- Over-scope: none. `status_set.py` E-01 to E-03; `cli.py` and `CHANGELOG.md` E-04; the test module E-05.
- Under-scope: `aw backlog set --status` and `aw specs set --status` route to forked setters (`backlog.run_set`, `specs.run_set`) that take one record; they have no batch to split.

## Required tests / validation

- `python3 -m pytest tests/test_status_set_partial_batch.py tests/test_status_set.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

N/A: no spec states the all-or-nothing batch contract; it lives in `status_set` comments, which E-01 updates. `CHANGELOG.md` records the new flag.

## Open questions

### OQ-01: Should the orchestrator gate count children refused earlier in the same batch?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: No. E-01 builds `status_overrides` only from records that passed, so an orchestrator is never approved on the strength of a child that was skipped.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a no-refusal run's output diffed against the pre-change output (empty diff), and the refusal list for a mixed batch.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the three branches' transcripts (skip flag, interactive yes and no, non-interactive refusal with the hint).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the exit code, the human summary and the `--agent` record for a partial batch.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `--help` excerpts for each spelling and the `CHANGELOG.md` diff.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing module runs with per-test counts and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Commit only the Scope-Paths through `aw commit <plan> -- <paths>`; never push. Paste actual runner output into each V-item.
