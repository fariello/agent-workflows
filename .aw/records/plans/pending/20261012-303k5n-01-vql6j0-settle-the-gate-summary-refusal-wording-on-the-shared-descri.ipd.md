# IPD: Settle the gate-summary refusal wording on the shared descriptive vocabulary and retire its last inline copy

- Date: 2026-10-12
- Kind: child
- Concern: Backlog `303k5n` asks whether the `--gate-summary` refusal should adopt the shared Section 8.8 descriptive-refusal vocabulary. Re-verification at HEAD `76204c8f4` shows the CLI half of that decision was already made and shipped by plan `m94eht`, but the old one-sentence wording survives in `attention_contract.validate_gate_flags`, and the non-regression test still carries a comment describing the retired wording, so the decision is not yet recorded or finished.
- Scope: Route the `summary` arm of `attention_contract.validate_gate_flags` through `attention_contract.refuse_unsafe_descriptive` so every `--gate-summary` refusal in the code base speaks one vocabulary; correct the stale comment in `tests/test_specs_releases_descriptive_safety.py::test_non_regression_already_validated_run_set_flags_preserved`; add behavioral tests for the validator's summary arm; record the decision in the CHANGELOG.
- Scope-Paths: agent_workflows/attention_contract.py, tests/test_specs_releases_descriptive_safety.py, tests/test_gate_summary_refusal_vocabulary.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 303k5n
- Set: 303k5n
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: vql6j0
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed. Re-verified at ba0fb6975: F-01..F-06 reproduce; validate_gate_flags returns the old wording for newline, BEL, 301 and 400 chars and None at 300; refuse_unsafe_descriptive gives the three specific messages; the five related test files pass (1051 passed).
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog 303k5n after re-verifying the premise against HEAD 76204c8f4; premise found drifted (inline refusal already removed by m94eht), plan scoped to the residue.

## Goal

Finish and record the `303k5n` decision: one Section 8.8 refusal vocabulary for `--gate-summary` everywhere (option (a)), by retiring the last copy of the old `must be a bounded single control-char-free line` wording from `attention_contract.validate_gate_flags`, and make the non-regression test say what it actually pins.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-verify, then unify the validator's summary arm

- [ ] E-01 Re-verify the premise before editing: confirm `specs.run_set` contains no inline `--gate-summary` refusal (it is a thin adapter to `status_set.run_set_command`), confirm `attention_contract.validate_gate_flags` still returns `f"{verb}: --gate-summary must be a bounded single control-char-free line"` for an unsafe summary, and run `python3 -m pytest -o addopts="" -q tests/test_specs_releases_descriptive_safety.py -k non_regression_already` to confirm the selected test passes and pins `aw set: --gate-summary must not contain embedded newlines` at rc 2. If any of these differ from the Findings table, stop and record the drift instead of editing.
  - Depends on: none
  - Expected outcome: pasted grep/pytest output matching Findings F-01..F-04, or a recorded drift note and a halt.
  - Execution state: pending

- [ ] E-02 In `attention_contract.validate_gate_flags`, replace the summary arm (`if summary is not None and not is_safe_descriptive(summary): return f"{verb}: --gate-summary must be a bounded single control-char-free line"`) with a delegation to `refuse_unsafe_descriptive(verb, "--gate-summary", summary)` (default `bound_length=True`, `prose=False`), returning its message when non-None. Leave the kind/ref arms and their messages untouched. Update the docstring to say the summary arm uses the shared Section 8.8 vocabulary.
  - Depends on: E-01
  - Expected outcome: `validate_gate_flags("aw set","date","2026-10-02","a\nb")` returns `aw set: --gate-summary must not contain embedded newlines`; a 400-char summary returns `aw set: --gate-summary exceeds maximum length of 300 characters (400 > 300)`; a control-char summary returns `aw set: --gate-summary must not contain control characters`; a safe summary still returns None; `git grep -n 'bounded single control-char-free' -- agent_workflows` returns nothing (use `git grep`, not `grep -r`, which also matches stale `__pycache__/*.pyc` bytes).
  - Execution state: pending

### Task group 2: Tests and record

- [ ] E-03 Add `tests/test_gate_summary_refusal_vocabulary.py` that CALLS `attention_contract.validate_gate_flags` and asserts the three refusal messages and the None result from E-02 (newline, control char, 301 chars refused; exactly 300 chars and a plain value accepted), and asserts each refusal equals `attention_contract.refuse_unsafe_descriptive("aw set", "--gate-summary", value)` for the same input. In `tests/test_specs_releases_descriptive_safety.py::test_non_regression_already_validated_run_set_flags_preserved`, replace the stale comment `# --gate-summary must be bounded single control-char-free line (exit 2)` with one stating the test pins the shared Section 8.8 wording (`must not contain embedded newlines`, rc 2) by design per backlog `303k5n`; do not change any assertion in that test.
  - Depends on: E-02
  - Expected outcome: new test file passes; the edited test's assertions are byte-identical to before (diff shows only the comment line changed).
  - Execution state: pending

- [ ] E-04 Add one CHANGELOG `Unreleased` entry: `- Changed: the library-level gate validator (attention_contract.validate_gate_flags) now reports an unsafe --gate-summary with the same specific reason the CLI already uses (embedded newline, control character, or over-length with the actual length), so one wording is used everywhere.` (no em or en dashes). Place it in the topmost pending release section (`## 2.0.0 (pending)`, beside the other `- Changed:` lines); the file has no `Unreleased` heading. Then run the targeted files from `## Required tests / validation`, and the full suite bare (`python3 -m pytest`) at the execution base AND after the change, comparing failures BY NAME: the bare suite is not green on this tree for unrelated reasons (a sibling plan measured `39 failed` at `2600a93e3`), so "zero failures" is not the bar.
  - Depends on: E-03
  - Expected outcome: CHANGELOG line present; targeted files all pass; the post-change bare suite has no failing test absent from the base-commit failure list (any newly red node is re-run alone at the base before being called pre-existing).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Section 8.8 output-safety refusals are produced by ONE helper, `attention_contract.refuse_unsafe_descriptive`, hoisted there by executed plan `685iq8`; per-module `_refuse_unsafe_descriptive` wrappers in `specs.py`, `backlog.py`, `status_set.py`, `research_cmd.py` delegate to it.
- `aw specs set` (both spellings) is a thin adapter: `specs.run_set` delegates to `status_set.run_set_command` (executed plan `m94eht`, Set `setdisp`, Order 04).
- `status_set.run_set_command` refuses unsafe descriptive flags in its pre-flight loop (the `for _val, _flag, _bound in [...]` block commented `IPD 4gwgo3 E-02, E-03`) with `_refuse_unsafe_descriptive("aw set", _flag, _val, ...)` and rc 2, BEFORE `validate_transition_allowed` calls `_ac.validate_gate_flags("aw set", gk, gr, gs)`.
- Tests must exercise behavior (call functions / drive the CLI), never read source (AGENTS.md, GUIDING_PRINCIPLES P16). Suite is run bare: `python3 -m pytest`.
- User-facing prose (CHANGELOG) carries no em or en dashes.

## Findings

| ID | Finding | Evidence (measured 2026-10-12, HEAD `76204c8f4`) |
|---|---|---|
| F-01 | The inline `--gate-summary` refusal in `specs.run_set` that the backlog item describes NO LONGER EXISTS. `specs.run_set` is a thin adapter to `status_set.run_set_command`. | `specs.run_set` docstring: "Thin adapter delegating to status_set.run_set_command with scoped_type=\"specs\" (Set setdisp Order 04, IPD m94eht ...)". |
| F-02 | Option (a) was already SHIPPED for the CLI by `m94eht`, as a recorded, CHANGELOG-named message change, and the pinning tests were updated in that change. | `m94eht` refusal table row: "Unsafe `--gate-summary` \| rc 1, `aw specs set: --gate-summary must be a bounded single control-char-free line` \| rc 2, `aw set: --gate-summary must not contain embedded newlines` ... \| changed". CHANGELOG: "descriptive flag violations (`--message`, `--blocks-release`, `--from-backlog`, `--gate-summary`) ... on this spelling now exit 2 with the `aw set:` message prefix." |
| F-03 | Measured CLI behavior, both spellings, already uses the shared vocabulary. | Driving `cli.main(["specs","set",...,"--gate-summary",V,...])` on a fixture spec: newline -> `(2, 'aw set: --gate-summary must not contain embedded newlines')`; 400 chars -> `(2, 'aw set: --gate-summary exceeds maximum length of 300 characters (400 > 300)')`; BEL char -> `(2, 'aw set: --gate-summary must not contain control characters')`; identical for `--status` and positional spellings. |
| F-04 | The non-regression test passes and pins the NEW wording, but its comment still describes the retired wording. | `python3 -m pytest tests/test_specs_releases_descriptive_safety.py -k non_regression_already` -> `1 passed`. Comment: `# --gate-summary must be bounded single control-char-free line (exit 2)`; assertion: `"aw set: --gate-summary must not contain embedded newlines"`, `rc_gs == 2`. |
| F-05 | The ONLY remaining code copy of the old wording is the summary arm of `attention_contract.validate_gate_flags`. It is unreachable from the CLI for an unsafe summary (the pre-flight refuses first) but is the answer any direct library caller gets. | Grep for `bounded single control-char-free` under `agent_workflows/` returns only `attention_contract.py` (`validate_gate_flags`). Direct call returns `aw set: --gate-summary must be a bounded single control-char-free line` for newline, control-char, and 400-char inputs alike. Its only production caller is `status_set.validate_transition_allowed`. |
| F-06 | No test asserts the `validate_gate_flags` summary message, so changing it breaks nothing pinned. | Grep for `bounded single` / `validate_gate_flags` under `tests/` finds only the stale comment in F-04. |

## Proposed changes (ordered, validatable)

1. E-01: re-verify F-01..F-05 (halt on drift).
2. E-02: `validate_gate_flags` summary arm delegates to `refuse_unsafe_descriptive`.
3. E-03: new behavioral test file; stale comment corrected, assertions unchanged.
4. E-04: CHANGELOG line; full suite green.

## Deferred / out of scope (with reason)

- The kind/ref messages of `validate_gate_flags` (`requires --gate-kind and --gate-ref`, `--gate-kind must be one of ...`, `--gate-ref is invalid for kind ...`): they are typed-gate validity refusals, not Section 8.8 descriptive refusals, and are pinned by `tests/test_gate_pair_validation_parity.py`; out of the backlog item's scope.
- `check`-time drift messages (`specs.validate_spec`'s "Gate-Summary is over-length or has control chars/newlines", `backlog.validate_item`'s "Gate-Summary not a single bounded control-char-free line"): these are stable named-rule diagnostics (`attention.unsafe-field`, `backlog.gate-descriptive-unsafe`) for already-written records, not CLI refusals of a flag, and the backlog item does not cover them.
- Removing the per-module `_refuse_unsafe_descriptive` wrappers: retained by `685iq8` deliberately for existing call sites.

## Scope check

- Over-scope: none. Every edit is either the last copy of the wording the item names, the test the item names, a test proving the change, or the CHANGELOG record of a message change.
- Under-scope: none. The item's two obligations are (1) decide and (2) settle the non-regression test; F-02 shows the decision was made, E-02 finishes it in code, E-03 settles the test.

## Required tests / validation

- `python3 -m pytest tests/test_gate_summary_refusal_vocabulary.py tests/test_specs_releases_descriptive_safety.py tests/test_gate_pair_validation_parity.py tests/test_specs_set_gate_parity.py tests/test_status_set_descriptive_safety.py tests/test_descriptive_refusal_hoist.py` passes.
- Full suite run bare: `python3 -m pytest`.
- `git grep -n 'bounded single control-char-free' -- agent_workflows` returns nothing.
- Full-suite failures compared by name against a base-commit baseline (E-04).

## Spec / documentation sync

- No spec edit. Spec `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` Section 8.8 / F10 requires that unsafe descriptive values be refused but does not prescribe refusal wording, so the contract is unchanged.
- CHANGELOG: one `Changed` line (E-04), because a library-level refusal message changes.

## Open questions

### OQ-01: Option (a) adopt the shared vocabulary, or option (b) keep a distinct --gate-summary wording?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved from repository evidence as option (a). The backlog item framed this as a maintainer call between changing a shipped message and preserving it; that trade was already taken and recorded by executed plan `m94eht`, whose refusal table marks the `--gate-summary` row `changed`, whose CHANGELOG entry names `--gate-summary` among the changed refusals, and which updated `tests/test_specs_releases_descriptive_safety.py` to pin the shared wording (F-02, F-04). Every user-facing CLI path now emits the shared wording (F-03). Choosing (b) now would mean reverting a shipped, documented change, which is outside this item. This plan only removes the unreachable-from-CLI residue (F-05) so the decision is complete in code. If the maintainer nevertheless wants (b), the plan should be rejected at review rather than executed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of the grep for `def run_set` body in `agent_workflows/specs.py` showing the `status_set.run_set_command` delegation, a pasted direct `python3 -c` call of `attention_contract.validate_gate_flags` showing the old wording, and the pasted pytest summary for `-k non_regression_already` showing the selected test passed and none failed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -c` output calling `attention_contract.validate_gate_flags("aw set","date","2026-10-02",v)` for newline, BEL, 400-char, and `ok` inputs, showing the three specific messages and `None`; pasted `git grep -n 'bounded single control-char-free' -- agent_workflows` returning no matches; pasted `git diff agent_workflows/attention_contract.py` confined to `validate_gate_flags`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output for `tests/test_gate_summary_refusal_vocabulary.py` showing all tests passed; pasted `git diff tests/test_specs_releases_descriptive_safety.py` showing only the comment line changed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff CHANGELOG.md` showing the one `Changed` line with no em or en dash; pasted summary line of the targeted-files run (zero failed); pasted base-commit and post-change bare `python3 -m pytest` summary lines and failure lists, with a by-name diff showing no new failure (any difference re-run alone at the base, output pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). OQ-01 is resolved and non-blocking.

EXECUTION CONTRACT. Scope fence: the four `- Scope-Paths:` files; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a reason to stop. E-01's drift halt is a prerequisite check, not a scope stop. Commit only the Scope-Paths files through `aw commit vql6j0 -- <paths>` (never `git add -A`/`-a`, `--no-verify`, or `git stash` in the shared checkout), verify the staged set first, and never push. You MUST paste the actual runner output for every test claim; never report a run that was not performed.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`. Under `aw oc run`/`aw agy run` the runner owns begin/finalize, so do not finalize yourself; by hand, use `aw ipd begin` and `aw ipd finalize`, never a hand `git mv` to `executed/`.
