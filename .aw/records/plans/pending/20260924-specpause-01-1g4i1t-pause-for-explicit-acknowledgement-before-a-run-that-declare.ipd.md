# IPD: Pause for explicit acknowledgement before a run that declares spec edits

- Date: 2026-09-24
- Kind: child
- Concern: A run whose queue declares a `.spec.md` edit in `- Scope-Paths:` only ANNOUNCES it (plan `st5klo`, report-only by design), so an unattended run rewrites a contract every other plan is reviewed against with nobody consenting.
- Scope: Add a shared, host-neutral spec-edit acknowledgement gate: prompt y/N on a TTY listing the declared specs; unattended runs proceed only with `--ack-spec-edits <justification>` and otherwise refuse before any agent turn, recording the refusal durably with the same carrier the orchestrator coverage gate uses. Amend spec `25kzda` 2.1 and add 2.5c.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_spec_edit_ack_gate.py, .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- Set: specpause
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1g4i1t
- From-Backlog: 10qxm7

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 10qxm7; re-measured that `announce_run_order` still only prints the spec-impact lines (catching every exception) and that `enforce_orchestrator_probe_gate` records its refusal via `render_stream.record_refusal` + `save_state` + an `events.jsonl` event, sited in `initialize_run_core` after the run directory exists.

## Goal

Turn the declared-spec-edit announcement from information into consent: a run whose queue declares a spec edit must either get a human "y" on a TTY or carry an explicit, justified `--ack-spec-edits` flag, and otherwise refuse before spawning anything, with the refusal readable afterwards in `aw runs`. Both hosts get it from one shared seam.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: contract first

- [ ] E-01 Amend spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`): add `[--ack-spec-edits <justification>]` to the Section 2.1 grammar block after `[--allow-concurrent-driver <justification>]`, add a 2.1 bullet describing it (takes a justification string, recorded in the run ledger, waives no other gate), and add a new `### 2.5c Spec-edit acknowledgement gate` section after 2.5b stating: the trigger (any queued item whose `- Scope-Paths:` names a `.spec.md`, computed by `runner_shared.spec_impacts_for_queue`), TTY behavior (y/N prompt listing each id6 and spec path; only `y`/`yes` proceeds; an unanswered prompt refuses), unattended behavior (refuse unless the flag is present), the durable refusal record, that it runs under `--prepare-only` too (deterministic, spends nothing), and that a queue with no declared spec edit is unaffected.
  - Depends on: none
  - Expected outcome: `grep -n "ack-spec-edits\|2.5c Spec-edit acknowledgement gate"` on the spec shows the grammar line, the 2.1 bullet and the 2.5c heading.
  - Execution state: pending

### Task group 2: tests before code

- [ ] E-02 Create `tests/test_spec_edit_ack_gate.py` (unittest style, like `tests/test_concurrent_driver_guard.py`), building a temp repo with one queued plan whose `- Scope-Paths:` names `x.spec.md` and a run dir. Cases: (a) `test_unattended_without_flag_REFUSES_and_records_it`: `interactive=False`, no acknowledgement -> `decision.proceed is False`, `render_stream.refusal_of_item(item).code == "spec-edit-unacknowledged"`, `state.json` on disk carries the refusal, `events.jsonl` has a `spec-edit-ack-gate` event with `"proceed": false`; (b) `test_unattended_WITH_flag_proceeds_and_records_the_justification`: `acknowledgement="reviewed the 2.5c amendment"` -> proceed, `state["options"]["ack_spec_edits"]` equals the string, event `"override": "flag"`; (c) `test_tty_prompt_lists_specs_and_y_proceeds`: `interactive=True`, stub `prompt` captures its question and returns `"y"` -> proceed, question contains the plan id6 and `x.spec.md`, recorded as `"interactive confirmation: y"`; (d) `test_tty_prompt_default_is_NO`: stub returns `""`, then `None` -> refuse; (e) `test_no_declared_spec_edit_never_prompts`: queue without a spec -> proceed, stub prompt never called, no refusal; (f) `test_flag_on_both_hosts`: for `oc_runipd` and `agy_runipd`, `build_parser().parse_args(["start","sel","--ack-spec-edits"])` raises `SystemExit`, and with a value `freeze_run_policy_flags(args)["ack_spec_edits"]` returns it; (g) `test_gate_is_wired_once_before_announcement`: `inspect.getsource(runner_shared.initialize_run_core)` contains exactly one `enforce_spec_edit_ack_gate(` call and it precedes every `announce_run_order_fn(` call.
  - Depends on: none
  - Expected outcome: the file exists and, before E-03..E-05, every case fails (AttributeError on `enforce_spec_edit_ack_gate` / unknown flag).
  - Execution state: pending

### Task group 3: the gate

- [ ] E-03 Register a `RunPolicyFlag(flag="--ack-spec-edits", dest="ack_spec_edits", kind="str", implemented=True, owner="runner_shared.enforce_spec_edit_ack_gate", resume_rule=RESUME_REFUSE, help=...)` row in `runner_shared.RUN_POLICY_FLAGS` directly after the `--allow-concurrent-driver` row, with a comment citing this plan and spec 2.5c. `kind="str"` for the reason the `--allow-uncovered-orchestrator-work` row states: the record must say WHY, not only that somebody passed it (also the `gjadwm` reflexive-override concern).
  - Depends on: E-01
  - Expected outcome: `RUN_POLICY_FLAGS_BY_FLAG["--ack-spec-edits"].kind == "str"`; both hosts' parsers accept it through `register_run_policy_flags` with no per-host edit.
  - Execution state: pending
- [ ] E-04 Add `runner_shared.SPEC_EDIT_ACK_REFUSAL_CODE = "spec-edit-unacknowledged"`, a `SpecEditAckDecision(NamedTuple)` (`proceed`, `impacts`, `refusal`, `acknowledgement`, `message`) and `enforce_spec_edit_ack_gate(run_dir, state, *, repo, interactive, write_report_fn, acknowledgement=None, prompt=None) -> SpecEditAckDecision`, modeled on `enforce_orchestrator_probe_gate`: compute impacts with `spec_impacts_for_queue(repo, queue_with_plan_paths(repo, state["queue"]))`; empty -> proceed and emit `spec-edit-ack-gate` `{"proceed": true, "declared": []}`; non-empty with a stripped justification -> store `state["options"]["ack_spec_edits"]`, `save_state`, emit `"override": "flag"`, print one stderr line naming the specs; else if `interactive` -> ask via `prompt or prompt_for_gate_phrase` a question listing each `id6: spec` pair ending `Proceed? [y/N]: `, and on `y`/`yes` (case-insensitive) record `"interactive confirmation: y"`; otherwise `render_stream.record_refusal(item, code=SPEC_EDIT_ACK_REFUSAL_CODE, reason=..., remedy=...)` on every declaring item, `save_state`, emit `{"proceed": false, "declared": [...], "reason", "remedy"}`, return `proceed=False`. The remedy names both exits: rerun on a TTY and answer y, or pass `--ack-spec-edits '<why>'`. An exception computing impacts is NOT swallowed here (unlike the advisory announcement): it refuses with the exception text, because a consent gate that cannot see the specs must fail closed.
  - Depends on: E-03
  - Expected outcome: cases (a)-(e) of E-02 pass.
  - Execution state: pending
- [ ] E-05 Wire the gate into `runner_shared.initialize_run_core` once, immediately after `write_report_fn(run_dir, state)` and BEFORE the `--prepare-only` early return, so it runs under `--prepare-only` too (deterministic, no model call, and it closes the prepare-then-resume path, since the gate only lives in initialization). Pass `interactive=is_interactive_run(args)` and `acknowledgement=getattr(args, "ack_spec_edits", None)`; on `not decision.proceed` raise `DriverError(decision.message)`. Both `oc_runipd` and `agy_runipd` reach it through `initialize_run_core`, so no host file changes.
  - Depends on: E-04
  - Expected outcome: case (g) passes; `grep -n "enforce_spec_edit_ack_gate(" agent_workflows/runner_shared.py` shows the definition and exactly one call site.
  - Execution state: pending
- [ ] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Policy flags live ONLY in `runner_shared.RUN_POLICY_FLAGS` and are registered on both hosts by `register_run_policy_flags`; spec `25kzda` 2.1 is amended in the same change as a new row (the table's own comments).
- Gates that must be readable in `aw runs` are sited after the run directory exists and record via `render_stream.record_refusal` + `save_state` + an `events.jsonl` event (`enforce_orchestrator_probe_gate`, "orchestrator-probe-gate").
- Prompts go through `runner_shared.prompt_for_gate_phrase` (never blocks, no TTY means no prompt, unanswered returns `None`) and `is_interactive_run` (`--unattended`/`--full-auto` win over a TTY).
- Commit through `aw commit <plan> -- <paths>`; tests run bare.

## Findings

- `runner_shared.announce_run_order` computes `spec_impacts_for_queue(... queue_with_plan_paths(...))` and prints `format_spec_impact_announcement`, wrapped in `except Exception` that only prints `format_spec_impact_failure`: it "changes what the operator is TOLD, never what a run is ALLOWED to do". Nothing refuses.
- `enforce_orchestrator_probe_gate` is the reusable mechanism: `record_refusal(item, code=PROBE_REFUSAL_CODE, ...)`, `save_state(Path(run_dir), state, write_report=write_report_fn)`, `append_jsonl(run_dir / "events.jsonl", {"event": "orchestrator-probe-gate", ...})`, override stored in `state["options"]`, interactive consent recorded as an override. Its single call site is in `initialize_run_core`, after `--prepare-only` returns.
- Both hosts call `runner_shared.initialize_run_core` (`oc_runipd` and `agy_runipd` `initialize_run`), so one call site covers both.
- `tests/test_run_flag_surface.py` (spec/table bidirectional check) no longer exists in this tree (removed by commit `19313eed`, the suite trim), so nothing mechanically enforces the spec 2.1 row; E-01 amends the spec by hand and E-02 (f) checks the row.

## Proposed changes (ordered, validatable)

1. Spec 2.1 grammar/bullet + new 2.5c (E-01).
2. Red tests (E-02).
3. Flag row (E-03), gate function (E-04), single wiring (E-05).
4. Full suite (E-06).

## Deferred / out of scope (with reason)

- Rewording the AGENTS.md managed-block paragraph "A PLAN MAY AMEND A SPEC" (installed from `engine.py`) to mention the pause. Its current claims (announce before, report at end) stay true.
  - Carrier-Declined: the claims stay accurate and a managed-block edit touches every installed repo; reconsider once OQ-02 confirms the default.
- Re-gating on `resume` for a run started before this ships: such runs predate the gate and the flag is frozen (`RESUME_REFUSE`).
  - Carrier-Declined: a transitional edge only; new runs are gated at initialization, including under `--prepare-only`.

## Scope check

- Over-scope: none. No host-file edits; one shared function, one flag row, one spec section.
- Under-scope: `aw runs` rendering needs no change because it already renders `record_refusal` records (the orchestrator gate relies on this).

## Required tests / validation

`tests/test_spec_edit_ack_gate.py` cases (a)-(g), shown red before E-03..E-05 and green after, plus the bare suite.

## Spec / documentation sync

Amends spec `25kzda` (`.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`), declared in `- Scope-Paths:`. Why: this changes what a run is ALLOWED to do (a new refusal and a new policy flag), and 2.1 is the closed flag list both hosts are reviewed against; a flag the spec does not declare would be undocumented contract.

## Open questions

### OQ-01: Must a run that declares a spec edit pause for acknowledgement, and what is the unattended answer?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Resolution or deferral rationale: YES. TTY: a y/N prompt listing each declaring id6 and spec path, default No. Unattended (`--unattended`/`--full-auto` or no TTY): refuse before any agent turn unless `--ack-spec-edits <justification>` is present, with the refusal recorded durably. Reasons: (1) a spec is the contract other plans are reviewed against, and the backlog records that the report-only announcement lets an unattended run rewrite one "with nobody consenting"; (2) the declaration is known from `- Scope-Paths:` before anything is spawned, so the gate is deterministic and costs no model call; (3) the mechanism and wording already exist and were accepted for the orchestrator coverage gate (`enforce_orchestrator_probe_gate`), so reuse adds no new surface shape; (4) requiring a justification string rather than a boolean answers the `gjadwm` reflexive-override concern the same way `--allow-uncovered-orchestrator-work` and `--allow-concurrent-driver` do; (5) a y/N prompt (not a typed phrase) is enough because the operator is shown exactly which specs change, and the risk is visibility, not silent data loss.

### OQ-02: Maintainer, confirm the default (pause on TTY, refuse unattended without `--ack-spec-edits`).

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default if unanswered: ship as OQ-01 resolves. Alternatives the maintainer may prefer: a typed phrase instead of y/N, a bare boolean flag, or a repository-policy key to pre-acknowledge a named spec. Any of these is a small follow-up on the same function.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "ack-spec-edits\|2.5c Spec-edit acknowledgement gate" .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` showing the grammar line, the 2.1 bullet and the 2.5c heading, plus `git diff --stat` for the spec file.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_spec_edit_ack_gate.py` output run BEFORE E-03..E-05, showing every case FAILING (AttributeError for `enforce_spec_edit_ack_gate` or unrecognized `--ack-spec-edits`), and the same command after E-05 showing `7 passed` (or the actual count with 0 failed).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -c "from agent_workflows import runner_shared as r; x=r.RUN_POLICY_FLAGS_BY_FLAG['--ack-spec-edits']; print(x.kind, x.implemented, x.owner, x.resume_rule)"` printing `str True runner_shared.enforce_spec_edit_ack_gate refuse`, and `python3 -m agent_workflows oc run --help` plus `python3 -m agent_workflows agy run --help` output lines containing `--ack-spec-edits`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the passing lines for cases (a) unattended-refuses, (b) flag-proceeds, (c) TTY-y-proceeds, (d) TTY-default-No, (e) no-spec-never-prompts from `python3 -m pytest -o addopts="" -v tests/test_spec_edit_ack_gate.py`, and the `events.jsonl` line written by case (a) (print it from the test tmp dir or via a probe under `/tmp/opencode/`) containing `"event": "spec-edit-ack-gate"` and `"proceed": false`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `grep -n "enforce_spec_edit_ack_gate(" agent_workflows/runner_shared.py` showing one definition and one call inside `initialize_run_core`, the passing line for case (g), and an end-to-end probe in a scratch repo: `aw oc run <selector> --unattended --prepare-only` on a plan declaring a spec exits nonzero with the `spec-edit-unacknowledged` remedy text, and the same command with `--ack-spec-edits 'probe'` succeeds.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit <this plan> -- <paths>`; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
