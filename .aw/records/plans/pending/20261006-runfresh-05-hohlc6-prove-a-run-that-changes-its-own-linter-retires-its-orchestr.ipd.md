# IPD: Prove a run that changes its own linter retires its orchestrator

- Date: 2026-10-06
- Kind: child
- Concern: Orders 02 to 04 each prove their own piece. The failure the Set exists to fix only shows across them: a child of a run changes the linter's rules, and a later step of the same run (the orchestrator retirement) is judged by the driver's outdated copy. Only a test that reproduces that shape, through the real driver as its own process, shows the restart closes it and that the failure returns without it. This is the Set's final cross-child measurement, assigned here by orchestrator `67lvds`.
- Scope: IN: one integration test module that builds a fixture repository under `tempfile` containing a COPY of the `agent_workflows` package (so the test can change it without touching the real tree), a Set of one orchestrator and one child, and a scripted host turn for the child that edits the fixture's `ipd_schema.py` to recognize a new metadata field and writes that field into the orchestrator plan, then drives `python -m agent_workflows <oc|agy> run <setid>` as a SUBPROCESS from the fixture with `PYTHONPATH` pointing at the copy, for both hosts. Asserts with the restart enabled: one `driver-restarted` event, the orchestrator retired to `executed/` with no refusal. Asserts with `AW_NO_DRIVER_RESTART=1`: the retirement is refused, the item ends `fail-depend`, and the refusal names `IPD-M103` and the new field (Order 04). Then the bare suite. OUT: any production code change; any real model call.
- Scope-Paths: tests/test_runfresh_end_to_end.py
- Item-Dependencies: executed:re15ol, executed:vvqr34
- Status: to-review
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 5
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: hohlc6

## Workflow history

- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 05 of Set `runfresh`, the final child, owning orchestrator `67lvds` completion criteria 1 and 6 and the final suite run.

## Goal

Reproduce the 2026-10-06 failure in a fixture and show that the restart makes the retirement succeed, and that disabling it brings the failure back with its findings recorded.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the fixture

- [ ] E-01 Build the fixture in `tests/test_runfresh_end_to_end.py`: a temporary git repository with the toolkit package copied in (`shutil.copytree` of the real `agent_workflows`, excluding `__pycache__`), an `aw install` seeded with `--records-backend repository`, an approved Set with one orchestrator and one child, and a scripted host turn for the child (using the existing fake-host injection the runner tests use, passed to the subprocess by environment) that (a) adds a new recognized field name to the fixture's `ipd_schema.META_RECOGNIZED`, (b) writes `- <Field>: x` into the orchestrator plan, and (c) completes the child normally. The fixture must make the child's lane integrate to the fixture's `main` so the driver's checkout sees the change.
  - Depends on: none
  - Expected outcome: before any run, linting the orchestrator with the fixture's ORIGINAL package reports `IPD-M103 <Field>: unknown field` after step (b), and with the EDITED package reports it conforming, reproducing the 2026-10-06 shape.
  - Execution state: pending

### Task group 2: both directions on both hosts

- [ ] E-02 Run the Set through the real driver as a subprocess, once per host. With the restart enabled, assert: exactly one `driver-restarted` event naming the child as the preceding item; a fresh `tool-identity-verified` event after it; the orchestrator file under `executed/` with `- Status: executed`; the run summary showing one restart; and the child's status, attempts and the frozen options identical to their values before the restart (compare the `state.json` snapshot saved by the restart with the final one, ignoring the restart fields). With `AW_NO_DRIVER_RESTART=1`, assert: no `driver-restarted` event; the orchestrator item ends `fail-depend` with reason `finalize-refused`; its recorded refusal contains `IPD-M103` and the field name.
  - Depends on: E-01
  - Expected outcome: all assertions hold on both hosts.
  - Execution state: pending

### Task group 3: the whole suite

- [ ] E-03 Prove the test can fail by making Order 03's decision always `none` (in a scratch copy of the fixture's package, not the real tree) and pasting the restart-enabled case failing with the orchestrator refused. Then run the bare suite and reconcile it against a baseline measured on a clean tree at this child's HEAD. If the test takes longer than the repository's slow threshold, mark it `slow` and say so, with its measured runtime.
  - Depends on: E-02
  - Expected outcome: the mutation fails the enabled case; the bare suite shows no new failing node id.
  - Execution state: pending

## Project conventions discovered (Step 0)

- IN-PROCESS RUNNER TESTS CANNOT TEST A RESTART, because `os.execv` replaces the test process. This test therefore drives the driver as a subprocess, which is how `tests/test_lane_import_root.py` and `tests/test_cli_checkout_reexec.py` already test process-identity behavior.
- SEED FIXTURES WITH `--records-backend repository`, or a non-interactive install may put records under `$HOME` and make the assertions vacuous.
- REAL MODEL CALLS ARE FORBIDDEN IN TESTS (`runner_shared._assert_probe_spawn_is_permitted`); the orchestrator coverage probe is satisfied by a coverage record pre-written into the fixture orchestrator.
- RUN THE SUITE BARE.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The production failure is reproducible offline: linting the retired `1f4faf` bytes with the package exported from `3f4763b56` gives three `IPD-M103` errors; with current code, `conforming`. A fixture that adds one field reproduces the same mechanism at small scale. | the reproduction recorded in `0bjke0` F-02 |
| F-02 | The fake-host injection used by runner tests is in-process; a subprocess needs it passed by environment or a fixture-local fake host binary on `PATH`. Choose the fixture-local binary if the in-process seam cannot cross the process boundary, and record which. | `tests/test_backlog_production.py` `_patch_host_agent` |

## Proposed changes (ordered, validatable)

1. Fixture reproducing the 2026-10-06 shape with a copied package (E-01).
2. Both directions on both hosts through the real driver as a subprocess (E-02).
3. Mutation proof and the bare suite (E-03).

## Deferred / out of scope (with reason)

- A LIVE RUN AGAINST A REAL MODEL. Not reproducible and costs money.
  - Carrier-Declined: tests must not spend tokens

## Scope check

- Over-scope: none. One test file.
- Under-scope: none.

## Required tests / validation

- Baseline bare `python3 -m pytest` on a clean tree at this child's HEAD.
- `python3 -m pytest -o addopts="" tests/test_runfresh_end_to_end.py -q` pasted, with runtime.
- The mutation run pasted.
- Bare `python3 -m pytest` after, `N passed` line pasted, reconciled.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec or document edited. This plan measures spec `25kzda` 5.3b and 4.1 as amended by Order 01.

## Open questions

### OQ-01: Copy the whole package into the fixture, or only the files the test changes?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: the whole package. The driver must import its entire toolkit from the fixture so that the fingerprint, the restart and the post-restart import all refer to the same tree; a partial copy would mix the real tree's modules with the fixture's and test nothing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the fixture's two pre-run lint results (original package: `IPD-M103 <Field>: unknown field`; edited package: conforming) and state which fake-host mechanism was used and why.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each host, paste from the enabled run the `driver-restarted` event, the following `tool-identity-verified` event, the orchestrator's executed path and status, and the state comparison result; and from the disabled run the orchestrator item's status, reason and recorded refusal containing `IPD-M103` and the field.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the mutation run failing the enabled case and the restored run passing; the test file's runtime and whether it was marked `slow`; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the declared path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only the declared path through `aw commit <plan> -- <path>`; never push. Paste actual output. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
