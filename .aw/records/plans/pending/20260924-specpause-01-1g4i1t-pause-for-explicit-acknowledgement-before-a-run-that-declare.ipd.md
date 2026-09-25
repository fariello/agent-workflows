# IPD: Pause for explicit acknowledgement before a run that declares spec edits

- Date: 2026-09-24
- Kind: child
- Concern: A run whose queue declares a `.spec.md` edit in `- Scope-Paths:` only ANNOUNCES it (plan `st5klo`, report-only by design), so an unattended run rewrites a contract every other plan is reviewed against with nobody consenting.
- Scope: Add a shared, host-neutral spec-edit acknowledgement gate: prompt y/N on a TTY listing the declared specs; unattended runs proceed only with `--ack-spec-edits <justification>` and otherwise refuse before any agent turn, recording the refusal durably with the same carrier the orchestrator coverage gate uses. Amend spec `25kzda` 2.1 and add 2.5c.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_spec_edit_ack_gate.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- Set: specpause
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1g4i1t
- From-Backlog: 10qxm7

## Workflow history
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): Reviewed via /plan-review; 7 findings (PR-901..PR-907), all FIXED. Corrected a - Scope-Paths: spec path that resolved to no file (would have announced a phantom spec edit while E-01 amended the real spec undeclared). Closed a FAIL-OPEN the plan's exception-handling sentence did not cover: neither spec_impacts_for_queue (except OSError: continue) nor queue_with_plan_paths (documented drop) raises on an unreadable declaring plan, so the gate would have proceeded silently on an empty impact list; E-04 now refuses on that accounting and new case (h) pins it. Recorded why RESUME_REFUSE diverges from both str precedents (which use none-default) and corrected the Deferred text that inverted its meaning. Justified the --prepare-only placement inverting the model gate's (it closes the prepare-then-resume bypass, since resume never calls initialize_run_core). Warned that case (g)'s source-counting assertion traps E-05's own comment. Rewrote the gate; gave OQ-02 a declined carrier.

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 10qxm7; re-measured that `announce_run_order` still only prints the spec-impact lines (catching every exception) and that `enforce_orchestrator_probe_gate` records its refusal via `render_stream.record_refusal` + `save_state` + an `events.jsonl` event, sited in `initialize_run_core` after the run directory exists.

## Goal

Turn the declared-spec-edit announcement from information into consent: a run whose queue declares a spec edit must either get a human "y" on a TTY or carry an explicit, justified `--ack-spec-edits` flag, and otherwise refuse before spawning anything, with the refusal readable afterwards in `aw runs`. Both hosts get it from one shared seam.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: contract first

- [ ] E-01 Amend spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`; CORRECTED AT REVIEW, the authored plan named `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, which does not exist): add `[--ack-spec-edits <justification>]` to the Section 2.1 grammar block after `[--allow-concurrent-driver <justification>]`, add a 2.1 bullet describing it (takes a justification string, recorded in the run ledger, waives no other gate), and add a new `### 2.5c Spec-edit acknowledgement gate` section after 2.5b stating: the trigger (any queued item whose `- Scope-Paths:` names a `.spec.md`, computed by `runner_shared.spec_impacts_for_queue`), TTY behavior (y/N prompt listing each id6 and spec path; only `y`/`yes` proceeds; an unanswered prompt refuses), unattended behavior (refuse unless the flag is present), the durable refusal record, that it runs under `--prepare-only` too (deterministic, spends nothing), and that a queue with no declared spec edit is unaffected.
  - Depends on: none
  - Expected outcome: `grep -n "ack-spec-edits\|2.5c Spec-edit acknowledgement gate"` on the spec shows the grammar line, the 2.1 bullet and the 2.5c heading.
  - Execution state: pending

### Task group 2: tests before code

- [ ] E-02 Create `tests/test_spec_edit_ack_gate.py` (unittest style, like `tests/test_concurrent_driver_guard.py`), building a temp repo with one queued plan whose `- Scope-Paths:` names `x.spec.md` and a run dir. Cases: (a) `test_unattended_without_flag_REFUSES_and_records_it`: `interactive=False`, no acknowledgement -> `decision.proceed is False`, `render_stream.refusal_of_item(item).code == "spec-edit-unacknowledged"`, `state.json` on disk carries the refusal, `events.jsonl` has a `spec-edit-ack-gate` event with `"proceed": false`; (b) `test_unattended_WITH_flag_proceeds_and_records_the_justification`: `acknowledgement="reviewed the 2.5c amendment"` -> proceed, `state["options"]["ack_spec_edits"]` equals the string, event `"override": "flag"`; (c) `test_tty_prompt_lists_specs_and_y_proceeds`: `interactive=True`, stub `prompt` captures its question and returns `"y"` -> proceed, question contains the plan id6 and `x.spec.md`, recorded as `"interactive confirmation: y"`; (d) `test_tty_prompt_default_is_NO`: stub returns `""`, then `None` -> refuse; (e) `test_no_declared_spec_edit_never_prompts`: queue without a spec -> proceed, stub prompt never called, no refusal; (f) `test_flag_on_both_hosts`: for `oc_runipd` and `agy_runipd`, `build_parser().parse_args(["start","sel","--ack-spec-edits"])` raises `SystemExit`, and with a value `freeze_run_policy_flags(args)["ack_spec_edits"]` returns it; (g) `test_gate_is_wired_once_before_announcement`: `inspect.getsource(runner_shared.initialize_run_core)` contains exactly one `enforce_spec_edit_ack_gate(` call and it precedes every `announce_run_order_fn(` call — verified at review that `initialize_run_core` contains TWO `announce_run_order_fn(` calls (one in the `--prepare-only` branch, one on the normal path), so "precedes every" is the correct form and a first-occurrence test would be weaker than it looks; (h) `test_an_unreadable_declaring_plan_REFUSES_rather_than_proceeding`: queue one item whose `- Scope-Paths:` names a spec and then make its plan file unreadable or absent, and assert the decision REFUSES naming that item, because both shared helpers skip such a plan silently (`spec_impacts_for_queue`'s `except OSError: continue`, `queue_with_plan_paths`' documented drop) and an empty impact list must not be read as "no spec edit declared".

  WARNING FOR CASE (g), inherited from the model gate and easy to trip: because (g) COUNTS occurrences of the literal string `enforce_spec_edit_ack_gate(` in the function's source, E-05's explanatory comment must NOT write the symbol in its call form, or the test fails on a COMMENT rather than on a second call site. The shipped orchestrator gate records exactly this hazard and avoids it (its comment names the three pre-queue gates in prose rather than spelling them, and mentions its own symbol only WITHOUT the paren; verified at review that `initialize_run_core`'s source contains the bare name but the paren form exactly once). NOTE the test that comment cites, `tests/test_run_flag_surface.py::test_the_mixed_type_call_site_was_not_duplicated`, was DELETED by the suite trim `19313eed`, so the constraint currently binds nothing — case (g) RE-CREATES it for this gate, which is why the hazard becomes live again with this plan.
  - Depends on: none
  - Expected outcome: the file exists and, before E-03..E-05, every case fails (AttributeError on `enforce_spec_edit_ack_gate` / unknown flag), failing on those causes rather than on a collection error.
  - Execution state: pending

### Task group 3: the gate

- [ ] E-03 Register a `RunPolicyFlag(flag="--ack-spec-edits", dest="ack_spec_edits", kind="str", implemented=True, owner="runner_shared.enforce_spec_edit_ack_gate", resume_rule=RESUME_REFUSE, help=...)` row in `runner_shared.RUN_POLICY_FLAGS` directly after the `--allow-concurrent-driver` row, with a comment citing this plan and spec 2.5c. `kind="str"` for the reason the `--allow-uncovered-orchestrator-work` row states: the record must say WHY, not only that somebody passed it (also the `gjadwm` reflexive-override concern).

  JUSTIFY `RESUME_REFUSE` IN THE ROW'S COMMENT, because it DIVERGES from both existing `kind="str"` rows and the divergence is deliberate rather than inherited. Measured at review: `--allow-concurrent-driver` and `--allow-uncovered-orchestrator-work` both carry `resume_rule="none-default"` (the dataclass default), so copying the neighbouring row's shape would give the opposite behavior from what this item specifies. `RESUME_REFUSE` means `refuse_frozen_flags_on_resume` RAISES when the flag is passed on a resume, and it is the right choice here for a reason the other two do not share: this gate lives ONLY in `initialize_run_core`, and `resume` does not call that function (verified: each host's `resume` branch loads state and applies policy flags directly, reaching no gate), so a `--ack-spec-edits` accepted on resume would record consent that GATED NOTHING — the run it belongs to already passed or failed the gate at initialization. Refusing loudly is therefore honest where accepting-and-freezing would be theatre. State that in the comment so the next reader does not "restore consistency" with the sibling rows.
  - Depends on: E-01
  - Expected outcome: `RUN_POLICY_FLAGS_BY_FLAG["--ack-spec-edits"].kind == "str"` and `.resume_rule == RESUME_REFUSE`; both hosts' parsers accept it through `register_run_policy_flags` with no per-host edit; a bare `--ack-spec-edits` with no value exits 2 (argparse "expected one argument", the behavior verified at review on the `--allow-concurrent-driver` precedent).
  - Execution state: pending
- [ ] E-04 Add `runner_shared.SPEC_EDIT_ACK_REFUSAL_CODE = "spec-edit-unacknowledged"`, a `SpecEditAckDecision(NamedTuple)` (`proceed`, `impacts`, `refusal`, `acknowledgement`, `message`) and `enforce_spec_edit_ack_gate(run_dir, state, *, repo, interactive, write_report_fn, acknowledgement=None, prompt=None) -> SpecEditAckDecision`, modeled on `enforce_orchestrator_probe_gate`: compute impacts with `spec_impacts_for_queue(repo, queue_with_plan_paths(repo, state["queue"]))`; empty -> proceed and emit `spec-edit-ack-gate` `{"proceed": true, "declared": []}`; non-empty with a stripped justification -> store `state["options"]["ack_spec_edits"]`, `save_state`, emit `"override": "flag"`, print one stderr line naming the specs; else if `interactive` -> ask via `prompt or prompt_for_gate_phrase` a question listing each `id6: spec` pair ending `Proceed? [y/N]: `, and on `y`/`yes` (case-insensitive) record `"interactive confirmation: y"`; otherwise `render_stream.record_refusal(item, code=SPEC_EDIT_ACK_REFUSAL_CODE, reason=..., remedy=...)` on every declaring item, `save_state`, emit `{"proceed": false, "declared": [...], "reason", "remedy"}`, return `proceed=False`. The remedy names both exits: rerun on a TTY and answer y, or pass `--ack-spec-edits '<why>'`.

  CLOSE THE UNREADABLE-PLAN FAIL-OPEN, which is the real hazard and is NOT an exception. The authored item said only that "an exception computing impacts is NOT swallowed here", but neither helper RAISES on the case that matters: `spec_impacts_for_queue` does `except OSError: continue` and its docstring justifies the skip because "this is an advisory surface, and refusing to start a run because an announcement could not be built would be a worse failure" — a justification that is TRUE for the announcement and FALSE for a consent gate; and `queue_with_plan_paths` DROPS an item whose plan it cannot locate, saying so in its own docstring ("An item whose plan cannot be located is DROPPED, which matches the helper's own posture"). So a queued plan that declares a spec edit but whose file is unreadable or unlocatable yields EMPTY impacts and this gate PROCEEDS SILENTLY, which is precisely the consent bypass the plan exists to prevent, reachable without any exception being raised. Therefore: do NOT rely on the shared helpers' emptiness as evidence of no spec edit. Compare the queue length against what the two helpers actually resolved, and when any queued item was dropped or unread, REFUSE with a distinct reason naming those items, rather than treating an unverifiable queue as a clean one. Do this WITHOUT changing either shared helper (their advisory posture is correct for `announce_run_order`, whose `except Exception` is deliberate and documented); the fail-closed decision belongs to this gate's caller-side accounting. An exception computing impacts likewise refuses with the exception text.
  - Depends on: E-03
  - Expected outcome: cases (a)-(e) and (h) of E-02 pass; a queued item whose plan file is unreadable produces a REFUSAL naming it, never a silent proceed.
  - Execution state: pending
- [ ] E-05 Wire the gate into `runner_shared.initialize_run_core` once, immediately after `write_report_fn(run_dir, state)` and BEFORE the `--prepare-only` early return. Pass `interactive=is_interactive_run(args)` and `acknowledgement=getattr(args, "ack_spec_edits", None)`; on `not decision.proceed` raise `DriverError(decision.message)`. Both `oc_runipd` and `agy_runipd` reach it through `initialize_run_core`, so no host file changes.

  THE PREPARE-ONLY SITING IS THE OPPOSITE OF THE MODEL GATE'S AND THAT IS CORRECT; say so in the comment, because a reader comparing the two will otherwise read it as a mistake. The orchestrator coverage gate sits AFTER the `--prepare-only` early return and ANNOUNCES a deliberate skip, for a reason stated at its call site: it SPENDS A MODEL CALL, and `--prepare-only`'s contract is to "create and display the durable queue WITHOUT launching OpenCode". This gate spends NO model call and launches nothing, so that reason does not transfer, and a y/N prompt is not a launch. Placing it BEFORE the return is also load-bearing rather than tidy: verified at review that neither host's `resume` path calls `initialize_run_core`, so a gate sited after the return would leave `--prepare-only` ungated, and the operator could then `resume` that prepared queue and execute the spec edits having consented to nothing. That is the bypass this placement closes, and it is the ONE hole a gate living only in initialization would otherwise have.
  - Depends on: E-04
  - Expected outcome: case (g) passes; `grep -n "enforce_spec_edit_ack_gate(" agent_workflows/runner_shared.py` shows the definition and exactly one call site, and the new explanatory comment does NOT contain the symbol in its `(`-suffixed form (see E-02's case-(g) warning).
  - Execution state: pending
- [ ] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Policy flags live ONLY in `runner_shared.RUN_POLICY_FLAGS` and are registered on both hosts by `register_run_policy_flags`; spec `25kzda` 2.1 is amended in the same change as a new row (the table's own comments).
- Gates that must be readable in `aw runs` are sited after the run directory exists and record via `render_stream.record_refusal` + `save_state` + an `events.jsonl` event (`enforce_orchestrator_probe_gate`, "orchestrator-probe-gate").
- Prompts go through `runner_shared.prompt_for_gate_phrase` (never blocks, no TTY means no prompt, unanswered returns `None`) and `is_interactive_run` (`--unattended`/`--full-auto` win over a TTY). Its docstring records a MEASURED 1h49m wedge from a blocking `input()`, which is why an unanswered prompt must fall through to the automatic decision rather than wait.
- `resume` DOES NOT re-run initialization. Each host's `resume` branch calls `refuse_frozen_flags_on_resume`, loads state, and applies policy flags; it never calls `initialize_run_core`. So a gate living only in initialization is bypassed by `--prepare-only` followed by `resume` unless the gate sits BEFORE the `--prepare-only` early return.
- A `RESUME_REFUSE` row is REFUSED on resume (`refuse_frozen_flags_on_resume` raises) and is skipped by `apply_run_policy_flags_on_resume`; it is not "frozen and applied". Both existing `kind="str"` rows use `"none-default"` instead, so choosing `RESUME_REFUSE` is a divergence that must carry its reason.
- The two shared spec-impact helpers are ADVISORY BY DESIGN and skip what they cannot read (`spec_impacts_for_queue`'s `except OSError: continue`; `queue_with_plan_paths`' documented drop of an unlocatable plan). A consent gate must not treat their empty result as proof of no spec edit.
- Commit through `aw commit <plan> -- <paths>`; tests run bare.

## Findings

- `runner_shared.announce_run_order` computes `spec_impacts_for_queue(... queue_with_plan_paths(...))` and prints `format_spec_impact_announcement`, wrapped in `except Exception` that only prints `format_spec_impact_failure`: it "changes what the operator is TOLD, never what a run is ALLOWED to do". Nothing refuses.
- `enforce_orchestrator_probe_gate` is the reusable mechanism: `record_refusal(item, code=PROBE_REFUSAL_CODE, ...)`, `save_state(Path(run_dir), state, write_report=write_report_fn)`, `append_jsonl(run_dir / "events.jsonl", {"event": "orchestrator-probe-gate", ...})`, override stored in `state["options"]`, interactive consent recorded as an override. Its single call site is in `initialize_run_core`, after `--prepare-only` returns.
- Both hosts call `runner_shared.initialize_run_core` (`oc_runipd` and `agy_runipd` `initialize_run`), so one call site covers both.
- `tests/test_run_flag_surface.py` (spec/table bidirectional check) no longer exists in this tree (removed by commit `19313eed`, the suite trim; confirmed at review that the commit deletes a 4863-line file of that name), so nothing mechanically enforces the spec 2.1 row; E-01 amends the spec by hand and E-02 (f) checks the row. A SECOND CONSEQUENCE, added at review: the orchestrator gate's call-site comment still cites that deleted test as the reason it avoids writing its own symbol in `(`-suffixed form, so that constraint currently binds nothing — and E-02's case (g) RE-CREATES it for the new gate, which makes the comment hazard live again (see the warning added to E-02).
- ADDED AT REVIEW, the fail-open that the plan's exception-handling sentence did not cover: NEITHER shared helper raises on the case that matters. `spec_impacts_for_queue` contains `except OSError: continue` and justifies it in its docstring on the grounds that "this is an advisory surface" — true of `announce_run_order`, false of a consent gate — and `queue_with_plan_paths` documents that "an item whose plan cannot be located is DROPPED". So a queued plan declaring a spec edit whose file is unreadable produces an EMPTY impact list and the gate would proceed silently, with no exception raised anywhere. E-04 now refuses on that accounting and E-02 case (h) pins it.
- ADDED AT REVIEW, the `resume_rule` divergence: both existing `kind="str"` rows (`--allow-concurrent-driver`, `--allow-uncovered-orchestrator-work`) carry `resume_rule="none-default"`, not `RESUME_REFUSE`, so this row's specified value is a deliberate divergence and needs its reason recorded. The reason is sound: `refuse_frozen_flags_on_resume` RAISES for a `RESUME_REFUSE` row, and since each host's `resume` branch never calls `initialize_run_core` (verified), consent passed on resume would gate nothing.
- ADDED AT REVIEW, why the `--prepare-only` placement inverts the model gate's: the orchestrator gate sits AFTER the early return and announces a skip because it SPENDS A MODEL CALL against a flag contracted to launch nothing. This gate spends none, and placing it BEFORE the return is what closes the prepare-then-resume bypass, since a prepared queue can be executed by `resume`, which reaches no gate.

## Proposed changes (ordered, validatable)

1. Spec 2.1 grammar/bullet + new 2.5c (E-01).
2. Red tests (E-02).
3. Flag row (E-03), gate function (E-04), single wiring (E-05).
4. Full suite (E-06).

## Deferred / out of scope (with reason)

- Rewording the AGENTS.md managed-block paragraph "A PLAN MAY AMEND A SPEC" (installed from `engine.py`) to mention the pause. Its current claims (announce before, report at end) stay true.
  - Carrier-Declined: the claims stay accurate and a managed-block edit touches every installed repo; reconsider once OQ-02 confirms the default.
- Re-gating on `resume` for a run started before this ships: such runs predate the gate, and `RESUME_REFUSE` makes passing the flag on a resume RAISE rather than silently freeze consent that gated nothing.
  - Carrier-Declined: a transitional edge only; new runs are gated at initialization, including under `--prepare-only`, which is what closes the prepare-then-resume path. CLARIFIED AT REVIEW: the authored wording said "the flag is frozen (`RESUME_REFUSE`)", which inverts what that value does — a `RESUME_REFUSE` row is REFUSED on resume (`refuse_frozen_flags_on_resume` raises), while `apply_run_policy_flags_on_resume` skips it precisely so it can never be frozen there. The conclusion is unchanged and in fact better supported: since `resume` never reaches `initialize_run_core`, there is nothing on that path for a re-gate to protect.
- Changing `spec_impacts_for_queue` or `queue_with_plan_paths` to raise on an unreadable plan instead of skipping it.
  - Carrier-Declined: ADDED AT REVIEW. Their skip-and-continue posture is CORRECT for their existing caller, `announce_run_order`, which is advisory by design and catches everything so "a broken announcement must never stop a run from starting". Making them raise would convert an advisory surface into a run-stopper for every caller, which is a behavior change to shipped code outside this plan's fence. The fail-closed decision belongs to this gate's own accounting (E-04), which is where it now lives.

## Scope check

- Over-scope: none. No host-file edits; one shared function, one flag row, one spec section, and no change to either shared impact helper.
- Under-scope: `aw runs` rendering needs no change because it already renders `record_refusal` records (the orchestrator gate relies on this).
- Under-scope as authored, now fixed: the declared spec path resolved to no file; the gate would have PROCEEDED silently when a declaring plan was unreadable, because neither shared helper raises on that path; `RESUME_REFUSE` diverged from both `str` precedents with no recorded reason and was described with its meaning inverted; the `--prepare-only` placement inverted the model gate's without saying why; and E-02 case (g)'s source-counting assertion sets a trap for E-05's own explanatory comment.

## Required tests / validation

`tests/test_spec_edit_ack_gate.py` cases (a)-(g), shown red before E-03..E-05 and green after, plus the bare suite.

## Spec / documentation sync

Amends spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`), declared in `- Scope-Paths:`. Why: this changes what a run is ALLOWED to do (a new refusal and a new policy flag), and 2.1 is the closed flag list both hosts are reviewed against; a flag the spec does not declare would be undocumented contract. THE DECLARED PATH WAS CORRECTED AT REVIEW: it named `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, which resolves to no file, and that is not cosmetic. `runner_shared.declared_spec_paths` matches on the `.spec.md` facet, so the wrong value WOULD have been announced as a declared spec edit while pointing at nothing, and E-01 would then have amended the real spec UNDECLARED — the exact undeclared-spec-edit case both runners' end-of-run report exists to catch, and the case whose finalize reconciliation would demand a `--scope-reason` for the real path and a `--scope-ack` for the phantom one. Verified after the correction that both the path and Sections 2.1 / 2.5b exist, so 2.5c has a real anchor to follow.

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
- Carrier-Declined: The question asks the maintainer to CONFIRM a default this plan already ships, and every alternative it names is a change to the one function this plan creates, so the obligation does not outlive the plan: if the default stands, nothing is owed; if the maintainer prefers another shape, that is a new plan against a shipped `enforce_spec_edit_ack_gate` and would be filed then with the maintainer's actual answer in hand. Filing a carrier now would track a decision that may never need making, and would name no work anyone can start. The consequence of no answer is explicit and recorded in the rationale below, which is what keeps this honest rather than silent.
- Resolution or deferral rationale: Default if unanswered: ship as OQ-01 resolves. Alternatives the maintainer may prefer: a typed phrase instead of y/N, a bare boolean flag, or a repository-policy key to pre-acknowledge a named spec. Any of these is a small follow-up on the same function. STATED AT REVIEW so the default is chosen with its cost visible: shipping this makes every future UNATTENDED run whose queue declares a spec edit FAIL unless `--ack-spec-edits` is passed, including under `--prepare-only`. That is the intended behavior, but it is a change to existing operator habit rather than a purely additive one, and it is the part a maintainer is most likely to want to shape. Nothing about the plan is blocked on the answer, because the default IS the resolution of OQ-01 and it is fully specified.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "ack-spec-edits\|2.5c Spec-edit acknowledgement gate" .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the grammar line, the 2.1 bullet and the 2.5c heading, plus `git diff --stat` for the spec file. ALSO paste `python3 -c "from pathlib import Path; from agent_workflows import runner_shared as r; print([(s, Path(s).exists()) for s in r.declared_spec_paths(Path('<this plan>').read_text())])"` showing the declared spec path RESOLVES to `True`, which is the check that the declaration and the edit name the same file.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_spec_edit_ack_gate.py` output run BEFORE E-03..E-05, showing every case FAILING on an `AttributeError` for `enforce_spec_edit_ack_gate` or an unrecognized `--ack-spec-edits` (state which, per case, and confirm no case fails on a collection or import error instead), and the same command after E-05 showing 0 failed with the actual collected count (8 cases, (a) through (h), after review added (h)).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -c "from agent_workflows import runner_shared as r; x=r.RUN_POLICY_FLAGS_BY_FLAG['--ack-spec-edits']; print(x.kind, x.implemented, x.owner, x.resume_rule)"` printing `str True runner_shared.enforce_spec_edit_ack_gate refuse`, and `python3 -m agent_workflows oc run --help` plus `python3 -m agent_workflows agy run --help` output lines containing `--ack-spec-edits`. ALSO paste the same one-liner for `--allow-concurrent-driver` and `--allow-uncovered-orchestrator-work`, showing both print `none-default`, so the DIVERGENCE this row makes is visible in the evidence rather than only asserted, and confirm the row's comment states why (the gate lives only in `initialize_run_core`, which `resume` does not call).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the passing lines for cases (a) unattended-refuses, (b) flag-proceeds, (c) TTY-y-proceeds, (d) TTY-default-No, (e) no-spec-never-prompts, and (h) unreadable-declaring-plan-REFUSES from `python3 -m pytest -o addopts="" -v tests/test_spec_edit_ack_gate.py`, and the `events.jsonl` line written by case (a) containing `"event": "spec-edit-ack-gate"` and `"proceed": false`. Print the event line from the test's own temp directory (or from a scratch repo inside this workspace); do not assume a path outside the workspace is writable. CASE (h) IS THE ONE THAT MUST NOT BE SKIPPED: it is the only evidence that an empty impact list caused by an unreadable plan refuses instead of proceeding, and both shared helpers reach that state without raising, so no other case covers it.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `grep -n "enforce_spec_edit_ack_gate(" agent_workflows/runner_shared.py` showing one definition and one call inside `initialize_run_core`, and `python3 -c "import inspect; from agent_workflows import runner_shared as r; s=inspect.getsource(r.initialize_run_core); print(s.count('enforce_spec_edit_ack_gate('), s.count('announce_run_order_fn('))"` printing `1 2` (two announce calls exist; the gate must precede both). Paste the passing line for case (g). Then an end-to-end probe in a scratch repo INSIDE this workspace: `aw oc run <selector> --unattended --prepare-only` on a plan declaring a spec exits nonzero with the `spec-edit-unacknowledged` remedy text, and the same command with `--ack-spec-edits 'probe'` succeeds. The `--prepare-only` half of that probe is the point: it is the evidence that the prepare-then-resume bypass is closed, since `resume` reaches no gate.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (turn the declared-spec-edit announcement into consent). E-03, E-04 and E-05 are separate items because each fails differently: a flag row fails by diverging from its siblings' resume semantics, the gate function fails by proceeding on an unverifiable queue, and the wiring fails by siting the gate where `--prepare-only` escapes it.

WHAT A HUMAN IS APPROVING. A NEW REFUSAL PATH in the shared initialization both runners use, which means every future unattended run whose queue declares a `.spec.md` edit will FAIL unless someone passes `--ack-spec-edits '<why>'`. That is the intent, and it is worth stating plainly because it changes existing operator habits: a queue that runs clean today can start refusing tomorrow purely because one of its plans declares a spec edit. Three further points. FIRST, this plan AMENDS AN APPROVED SPEC (`25kzda` 2.1 plus a new 2.5c), which is the contract every other plan is reviewed against. SECOND, the gate runs under `--prepare-only`, deliberately unlike the orchestrator coverage gate, because that is the only placement that closes the prepare-then-resume bypass; an operator who uses `--prepare-only` to inspect a queue will now be prompted or refused there. THIRD, OQ-02 is genuinely the maintainer's: the y/N shape, the justification-string flag, and the absence of a repository-policy pre-acknowledgement key are all defaults this plan ships if unanswered.

SCOPE FENCE (a declaration, so the runner can reconcile afterwards; not an instruction to stop over a scope question). Within the declared paths the intended surface is: `runner_shared.py` the new `SPEC_EDIT_ACK_REFUSAL_CODE`, `SpecEditAckDecision`, `enforce_spec_edit_ack_gate`, ONE `RUN_POLICY_FLAGS` row, and ONE call site plus its comment in `initialize_run_core`; `tests/test_spec_edit_ack_gate.py` NEW; the spec's 2.1 grammar block, one 2.1 bullet, and a new 2.5c section after 2.5b. DELIBERATELY NOT IN SCOPE: any edit to `spec_impacts_for_queue`, `queue_with_plan_paths`, or `announce_run_order` (their advisory posture is correct for their existing caller); any host file (`oc_runipd.py`, `agy_runipd.py`), since both reach the gate through the shared seam; the AGENTS.md managed block; a repository-policy pre-acknowledgement key; and re-gating on `resume`. An out-of-scope edit that proves necessary should be MADE and then justified with `--scope-reason` at finalize.

HONESTY RULE (hard MUST). Paste the ACTUAL command output for every `V-*` item. Three specific temptations to refuse: do not report case (h) as covered by any other case, since it is the only evidence that an unreadable declaring plan refuses rather than proceeds and no exception is raised on that path; do not record V-05 without the `--prepare-only` half of the probe, which is the only evidence the prepare-then-resume bypass is closed; and do not report a green `tests/test_spec_edit_ack_gate.py` as proof the gate is wired, since case (g) is a source-text assertion that a passing E-04 alone would satisfy.

STOP CONDITIONS (genuinely unsafe, distinct from a scope question). Stop and report if: satisfying E-02 case (g) appears to require editing or weakening that test rather than rewording E-05's comment (that is the comment hazard, and the fix is always the comment); the spec's Section 2.5b or the 2.1 grammar block has been restructured under you so 2.5c has no coherent anchor; or `initialize_run_core`'s `--prepare-only` early return has moved such that the "after `write_report_fn`, before the return" window no longer exists.

Execute only after explicit human approval (`- Status: approved`). Commit only the Scope-Paths files through `aw commit 1g4i1t -- <paths>`; never push. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, the lifecycle transition to `executed/` is performed by the RUNNER when one is driving this plan, and by the executor via `aw ipd finalize` only when no runner owns the transition; do not hand-roll a `git mv`. Backlog `10qxm7` carries no `- Blocks-Release:`, so no release gate is owed and none may be invented.
