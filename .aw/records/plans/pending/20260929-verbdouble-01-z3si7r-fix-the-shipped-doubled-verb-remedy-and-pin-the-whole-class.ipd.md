# IPD: Fix the shipped doubled-verb remedy and pin the whole class with a rendered-output test

- Date: 2026-09-29
- Kind: child
- Concern: `HostLabels.command` already carries the run verb, so a caller that suffixes a verb renders a command that does not exist inside an operator-facing remedy. One such site ships today.
- Scope: Fix the one live doubled-verb remedy in `runner_shared.finalize_retry_remedy`, document the verb-inclusion contract on the `HostLabels.command` field, and restore a behavioral guard that renders every host-command-carrying remedy for both hosts and refuses a first token that is not a real subcommand.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: 6if6ko
- Blocks-Release: f33nrj
- Set: verbdouble
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: z3si7r

## Workflow history

- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `6if6ko`; the audit the item asked for found one SHIPPED malformed remedy, so `Work-Kind` was raised from the item's `chore` to `bug` and the release gate added, per the item's own reclassification clause and `AGENTS.md` "Every live bug gates the next release".

## Goal

Make `runner_shared.finalize_retry_remedy` print a command an operator can actually run, and stop the whole doubled-verb class recurring by restoring a rendered-output guard that checks the token after a host command is a REAL subcommand of that host's parser rather than a second verb.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: fix the shipped defect

- [ ] E-01 In `agent_workflows/runner_shared.py`, in `finalize_retry_remedy`, change the interpolation `` `{command} run resume <run-id>` `` to `` `{command} resume <run-id>` `` (delete the stray literal `run`), leaving the rest of the sentence untouched.
  - Depends on: none
  - Expected outcome: `finalize_retry_remedy(OC_HOST_LABELS, "abc123", False)` contains `aw oc run resume <run-id>` and does not contain `run run`; the same call with `AGY_HOST_LABELS` contains `aw agy run resume <run-id>`. No other wording changes.
  - Execution state: pending

- [ ] E-02 In the same function, adjust the `None`-labels fallback literal so the fallback and the real-labels path agree on shape: it currently reads `getattr(labels, "command", None) or "aw oc"` while every sibling remedy uses `"aw oc run"`. Set it to `"aw oc run"` so the fallback renders `aw oc run resume <run-id>` by the SAME interpolation as the host path rather than by compensating for a missing verb.
  - Depends on: E-01
  - Expected outcome: `finalize_retry_remedy(None, "abc123", False)` still contains `aw oc run resume <run-id>` (the rendered string is unchanged from before this plan), but it is now produced by a fallback whose value matches `OC_HOST_LABELS.command`, so the divergence that hid F-01 is gone.
  - Execution state: pending

### Task group 2: put the contract where the next author will read it

- [ ] E-03 In `agent_workflows/runner_shared.py`, extend the `HostLabels.command` field docstring comment to state that the value INCLUDES the run verb, that a caller must therefore append a SUBCOMMAND (`resume`, `stop`, ...) or a bare selector and never a second verb, and cite the measured failure (`aw oc run run resume` is parsed as an ambiguous Set selector and exits 2).
  - Depends on: none
  - Expected outcome: the field's documentation answers the question the backlog item says the NAME fails to answer, without renaming the field (a rename would touch every consumer and is out of scope; see the deferral section).
  - Execution state: pending

### Task group 3: stop the class recurring

- [ ] E-04 In `tests/test_runner_shared.py`, add a test class that, for BOTH `OC_HOST_LABELS` and `AGY_HOST_LABELS`, calls each host-command-carrying remedy (`finalize_retry_remedy` in its retry, exhausted and lock-contention forms, `turn_retry_remedy` in both forms, `zero_work_retry_remedy` in both forms) and, for every backtick-quoted command in the returned string that starts with that host's `command`, asserts the next token is either absent, a flag (starts with `-`), a placeholder (starts with `<`), a selector-shaped token, or a member of that host's live subcommand set obtained from `build_parser()`'s `argparse._SubParsersAction.choices`. Assert additionally that no returned string contains `run run`. Include the `labels=None` fallback as its own case.
  - Depends on: E-01, E-02
  - Expected outcome: the test FAILS on the pre-E-01 code (naming `finalize_retry_remedy` and both hosts) and PASSES after. It exercises shipped functions and asserts on returned strings and live parser choices only, so it pins behavior and not code structure.
  - Execution state: pending

### Task group 4: re-verify the audit that justifies the scope

- [ ] E-05 Re-run the repository-wide render audit that F-04 rests on, at execution time rather than trusting it from authoring: enumerate every function in `agent_workflows/` that interpolates a host command into operator-facing text, render each for both hosts, and record the resulting command tokens. Do this AFTER E-01 and E-02 so the audit measures the fixed tree.
  - Depends on: E-01, E-02, E-04
  - Expected outcome: a recorded table of rendered command tokens in which no rendered command contains a doubled verb, confirming F-04's "exactly one site" claim and therefore confirming that two `Scope-Paths` entries were sufficient. If the audit finds a site this plan missed, the finding is recorded and filed rather than silently fixed, because an undeclared path would be refused by the scope gate anyway.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `HostLabels.command` INCLUDES THE VERB. `runner_shared.OC_HOST_LABELS` sets `command="aw oc run"` and `AGY_HOST_LABELS` sets `command="aw agy run"`. The field's own docstring comment describes it as "The operator-facing command prefix" and enumerates its consumers, but says NOTHING about whether the verb is included; that silence is what the backlog item identifies as the cause.
- THE MISTAKE IS ALREADY DOCUMENTED IN CODE, at the fix site the item's reporter made: `runner_shared.turn_retry_remedy` carries the comment "`labels.command` ALREADY CARRIES THE VERB (`aw oc run` / `aw agy run`), so suffixing `run` renders `aw oc run run <id6>`. MEASURED while collecting this plan's V-05 rendered evidence".
- BOTH HOSTS EXPOSE THE SAME SUBCOMMAND SET, so a guard can be written against the real parser rather than a hand-maintained list: `oc_runipd.build_parser()` and `agy_runipd.build_parser()` each yield `['audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']`. `run` is NOT among them, which is precisely why `aw oc run run resume` cannot work.
- THE SIBLING REMEDIES ARE ALREADY CORRECT, so this plan does not touch them: `runner_shared.turn_retry_remedy` and `runner_shared.zero_work_retry_remedy` both write `{command} {id6}` and `{command} resume <run-id> --retry-incomplete`, i.e. a bare selector and a real subcommand.
- A `str.startswith("aw ")` GUARD ALREADY EXISTS for the OTHER shape, and it is why the report sections are NOT defects: both `runner_shared.format_generated_next_actions_section` and `render_stream.format_generated_next_actions_summary_block` compute `host_command if host_command.startswith("aw ") else f"aw {host_command} run"`, so they accept either a bare `oc` token or a full `aw oc run` and render correctly for both.
- THE GUARD THIS PLAN RESTORES ONCE EXISTED AND WAS DELETED. `tests/test_retry_consumption.py::test_the_remedy_names_a_RUNNABLE_command_on_both_hosts` asserted exactly this class (`assertNotIn("run run", remedy)`) and was removed wholesale by commit `19313eed` "test: trim test suite from 9,136 to under 2,000 tests", which deleted the whole 729-line file. That is why the class is currently unguarded even though a test for it was written.
- TEST OUTCOMES, NOT CODE STRUCTURE. `AGENTS.md` and GUIDING_PRINCIPLES P16 forbid a test that reads production source with `inspect`/`ast`/regex or asserts a symbol census. The guard here therefore CALLS each renderer and asserts on its RETURNED STRING, and derives the legal subcommand set by introspecting the live `argparse` parser's choices (runtime behavior of the shipped CLI), never by scanning source text.

## Findings

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F-01 | `finalize_retry_remedy` ships a doubled verb for BOTH hosts | Called with `OC_HOST_LABELS`: `... or resume the run with \`aw oc run run resume <run-id>\`.` With `AGY_HOST_LABELS`: `\`aw agy run run resume <run-id>\``. The source writes `f"...resume the run with \`{command} run resume <run-id>\`"`. | An operator who types it gets exit 2. Measured: `aw oc run run resume fake-run-id` fails with `runipd: Ambiguous Set selector prefix: run matches [...]`, i.e. the runner parses the stray `run` as a SET SELECTOR and lists 32 candidate sets. This is a user-visible defect, not prevention. |
| F-02 | The defect predates the backlog item and was never the reporter's code | `git log -L 7879,7880:agent_workflows/runner_shared.py` attributes the line to commit `e11f7160` "fix(runner): send a refused finalize back to the agent and stop reporting it as success (zzcrlo)", which ADDED it. The reporter's own `turn_retry_remedy` (plan `xipfy1`) is correct. | The item's premise ("no currently shipped message is known to be malformed") is falsified by audit; the item itself says such an instance "IS a user-visible bug and should be reclassified". |
| F-03 | The `None`-labels fallback is correct, which HIDES F-01 from a careless check | `finalize_retry_remedy(None, ...)` renders `aw oc run resume <run-id>` (correct), because its fallback literal is `"aw oc"` and not `"aw oc run"`. Only the real host labels produce the doubled verb. | A test that exercised only the fallback would pass while both shipped hosts were broken. The guard must be parameterized over the REAL host labels. |
| F-04 | Exactly one site is wrong; the audit is complete and negative elsewhere | Audited every `{command}` / `{labels.command}` / `{host_labels.command}` interpolation in `agent_workflows/`. `turn_retry_remedy` and `zero_work_retry_remedy` write a bare selector or a real subcommand; `probe_refusal_remedy` and `probe_unavailable_remedy` write a bare `{labels.command}` with no suffix; `driver_actor` appends `model=`/`profile=` qualifiers, not verbs; `_compute_scope_reconciliation` writes prose ("auto-reconciled by ..."); `enforce_requested_action` writes `{labels.command} --action plan` (a flag) and `{labels.review_command}` (a separate field); the two `format_generated_next_actions_*` renderers carry the `startswith("aw ")` guard; `runner_stop`'s helpers take a plain `command: str` defaulting to `"aw oc run"` and suffix real `stop` subcommands. | The fix is a ONE-LINE change. The plan's value is mostly in F-05's guard, which is why the guard is not optional. |
| F-05 | Nothing prevents the next instance, and the item's own reasoning is confirmed | The field is named `command`; its docstring never states the verb is included; and the only surviving statement of the contract is a COMMENT inside an unrelated function (`turn_retry_remedy`). The test that guarded it was deleted (see Step 0). | Restore a guard plus document the contract ON the field, so the next author reads it where they look. |

## Proposed changes (ordered, validatable)

1. Fix F-01 by deleting the stray `run` token in `finalize_retry_remedy`, so both hosts render `aw oc run resume <run-id>` / `aw agy run resume <run-id>`.
2. State the verb-inclusion contract in `HostLabels.command`'s own field docstring, and say what a caller must therefore NOT write, citing the measured failure mode.
3. Restore a behavioral guard: render every host-command-carrying remedy for BOTH real host labels and refuse a first token after the command that is not a subcommand of that host's live parser.
4. Keep the fallback path covered too, since F-03 shows a fallback-only test would have passed on a broken shipped path.

## Deferred / out of scope (with reason)

- RENAMING the field (the item's option (a), e.g. `run_command` versus `cli_root`) is deliberately NOT done. `HostLabels` is a `NamedTuple` with 29 `.command` interpolations in `runner_shared.py` alone plus host-layer consumers, and its docstring records that `command` reaches a plan's PERMANENT finalize record; a rename is a mechanical but wide change whose risk is unrelated to the defect being fixed. E-03 takes the item's option (c) (document the contract) and E-04 takes option (b) (a guard), which together close the class at a fraction of the blast radius. If a later plan wants the rename, this plan's guard makes it safe to attempt.
- `runner_stop`'s `command: str = "aw oc run"` parameters are NOT converted to take `HostLabels`. They are correct today (they suffix real `stop` subcommands) and both hosts already pass `_detect_driver_command()`. Unifying them is a separate refactor.
- `render_stream.format_generated_next_actions_summary_block` is NOT edited. F-04 shows its `startswith("aw ")` guard makes it correct for both the bare-token and full-command shapes, and `render_stream.py` is outside `Scope-Paths`.

## Scope check

- Over-scope: none. `Scope-Paths` names exactly the two files E-01 through E-04 touch: the one production module holding the defect, the contract docstring, and the test file receiving the guard.
- Under-scope: none for the stated concern. The audit in F-04 is repository-wide and negative everywhere else, so no further production file needs editing. The field rename and the `runner_stop` unification are named in the deferral section with reasons rather than silently dropped.

## Required tests / validation

- `python3 -m pytest tests/test_runner_shared.py` for the new guard and the existing 119 tests in that file (baseline measured green before this plan: `119 passed`).
- `python3 -m pytest` (bare, per the repository's execution contract) for regression across the suite.
- A rendered-output check for both hosts and the fallback, pasted verbatim, because F-01 and F-03 are both invisible in state and only appear in rendered text; this is the same lesson `xipfy1`'s V-05 recorded.
- A negative control: the new guard must be shown FAILING against the pre-fix string, or the test proves nothing (a vacuous pass is the failure mode the guard exists to prevent).

## Spec / documentation sync

N/A for spec files: no `.spec.md` governs the wording of a remedy string, and none is declared in `Scope-Paths`. The contract being written down lands in the `HostLabels.command` field documentation (E-03), which is where every author of a new interpolation already looks, rather than in a spec no caller reads. No `AGENTS.md` change is needed: the reclassification this plan performs is authorized by the text already there ("Every live bug gates the next release" plus the backlog item's own reclassification clause).

## Open questions

### OQ-01: Should `Work-Kind` be raised from the item's `chore` to `bug`, with the release gate that implies?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED YES, from repository evidence rather than by asking. The backlog item chose `chore` explicitly because "no currently shipped message is known to be malformed", and stated the condition that would change it: "If an audit finds a shipped remedy printing a doubled verb, that instance IS a user-visible bug and should be reclassified." F-01 is that audit finding, and F-02 shows the malformed line ships from commit `e11f7160`, not from the reporter's own work. `AGENTS.md` then compels the gate: a live `bug` MUST carry `- Blocks-Release:` while it is `open`, `blocked` or `graduated`, and the single `planned` release is `f33nrj` (`.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`), which is what `next` resolves to. The plan therefore carries `- Work-Kind: bug` and `- Blocks-Release: f33nrj`. THIS GATED CARRIER UNDER AN UNGATED ITEM IS NOT A CHECK VIOLATION, verified rather than assumed: `aw check release-gates` reports `✓ CONFORMS 463 release-gates checked, errors 0 warnings 0` with this plan in the tree. `check_engine.check_release_gate_consistency`'s own docstring states the asymmetry is deliberate ("A gated CARRIER under an UNGATED item is NOT a finding, because a plan can discover during execution that it gates a release for reasons its originating item never knew") and that the direction is unreachable by construction, since its `item_gate` map is populated only for an item that HAS a gate. NOTE FOR THE EXECUTOR: reclassifying the ITEM is therefore optional rather than forced by a failing check, but it is the honest bookkeeping, since the item's own text asks for it. Do it through the setter (`aw backlog set open 6if6ko --work-kind bug --blocks-release next`), never by hand-editing the item, and note that this changes the item's CLASSIFICATION only; a plan may not rewrite the item's requirements.

### OQ-02: Is a doubled verb genuinely user-perceptible, or is this a cosmetic string defect?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED, user-perceptible, and measured rather than asserted. `AGENTS.md` sets the test as user-perceptible impact. The string is not merely ugly: running it fails. Measured `aw oc run run resume fake-run-id` exits 2 with `Ambiguous Set selector prefix: run matches [32 sets]`, so an operator following a remedy issued at the worst moment (a refused finalize, with a lane holding unlanded work) is sent to a dead end and must diagnose the tool instead of the plan. That is a defect under the perceptibility test, independent of latency.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the RENDERED output, not a state dict or a diff. Call `runner_shared.finalize_retry_remedy` with `OC_HOST_LABELS` and with `AGY_HOST_LABELS`, `retry=False`, `lock_contention=False`, and paste both full returned strings, showing `aw oc run resume <run-id>` and `aw agy run resume <run-id>` and no `run run`. Then paste an ACTUAL invocation of the fixed command shape proving it is accepted where the broken one was not: run `aw oc run resume --help` and paste its exit status, alongside a re-run of `aw oc run run resume <anything>` showing it still exits 2 (confirming the old string really was unrunnable and that the new one is not merely differently broken).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `finalize_retry_remedy(None, "abc123", False)` rendered BEFORE and AFTER the change, showing the rendered string is IDENTICAL (`aw oc run resume <run-id>`), and paste the fallback literal's new value shown to equal `OC_HOST_LABELS.command` by evaluating both and printing the comparison. If the rendered string changed at all, that is a failure of this item, not a pass: the point is that the fallback now agrees by construction instead of by compensating.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new `HostLabels.command` documentation text verbatim, and show it states three things: that the value includes the verb, what a caller may append instead, and the measured failure of appending a second verb. Then demonstrate it is reachable where an author would look, by pasting the output of a runtime introspection of the field's documentation (for example printing the `HostLabels` class docstring plus the field comment block as it appears in the module) rather than only asserting the edit was made.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: THE NEGATIVE CONTROL FIRST, because a guard that cannot fail proves nothing. Temporarily restore the stray `run` token, run the new test, and paste the FAILING output showing it names `finalize_retry_remedy` and fails for both `oc` and `agy` subTests. Then revert the temporary change, re-run, and paste the PASSING output. Then paste the full `python3 -m pytest tests/test_runner_shared.py` summary line (expect at least the baseline `119 passed` plus the new tests) and the full bare `python3 -m pytest` summary line. Finally, state explicitly that the new test reads no production SOURCE text (no `inspect.getsource`, no `ast`, no regex over a module file) and derives its legal subcommand set from the live parser's `choices`, so it complies with the no-code-pinning rule.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: this plan asserts exactly ONE site was wrong, and that claim is what keeps `Scope-Paths` to two files, so it must be re-verified against the fixed tree rather than trusted from authoring. Paste the audit's rendered output: for each host-command-carrying function, the function name, the host, and the rendered command token(s) it produced, covering at minimum `finalize_retry_remedy` (all three forms), `turn_retry_remedy`, `zero_work_retry_remedy`, `probe_refusal_remedy`, `probe_unavailable_remedy`, `driver_actor`, `enforce_requested_action`'s two refusals, `format_generated_next_actions_section`, and `runner_stop`'s `stop_footer_hint` / `stop_interrupt_hint` / `stop_verb_epilog`. Show that NO rendered command contains a doubled verb, and state explicitly whether the audit found any site beyond `finalize_retry_remedy`. A bare assertion that "the audit passed" is NOT acceptable evidence; the per-function rendered tokens are the evidence. If a missed site IS found, paste it and say whether it falls inside `Scope-Paths`; do not widen the plan to reach one that does not.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

This plan is `to-review` and requires explicit human approval before execution; no part of it may be executed on the strength of this document alone.

The executor must follow the repository execution contract: commit only the paths this plan declares, through `aw commit <plan> -- agent_workflows/runner_shared.py tests/test_runner_shared.py`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout; and paste ACTUAL runner output for every test claim rather than asserting success.

Two execution notes specific to this plan. FIRST, the E-04 negative control requires temporarily REINTRODUCING the defect; that temporary edit must be reverted before any commit, and V-04's evidence must show both the failing and the passing run so a reviewer can see the guard is not vacuous. SECOND, OQ-01 leaves one act outside these two files: reconciling backlog item `6if6ko`'s `Work-Kind` and `Blocks-Release` with this carrier via `aw backlog set`, which is a tooled status change on the item rather than an edit to its requirements. Perform it through the setter, not by hand-editing the item.

Post-gate lifecycle: after every `V-*` above is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, finalize through the tooled path (`aw ipd finalize z3si7r`) so the plan moves to `.aw/records/plans/executed/` with a real receipt. Do not hand-move the file and do not mark it executed on the strength of the execution checkmarks alone.

- Size assessment: standard
- Cohesion rationale: not required
