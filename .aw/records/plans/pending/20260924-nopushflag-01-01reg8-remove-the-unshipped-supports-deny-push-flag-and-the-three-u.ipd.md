# IPD: Remove the unshipped supports_deny_push flag and the three unenforced action verdicts

- Date: 2026-09-24
- Kind: child
- Concern: `aw host capabilities` prints `REFUSED  review`, `REFUSED  mutate` and `REFUSED  contractless_prompt`, each `missing: supports_commit_gateway, supports_deny_push`, on every host. NOTHING CONSUMES THOSE VERDICTS: the runners never call `host_sandbox_profile.preflight_host_capabilities` (`run_selection_policy` records "zero occurrences of `preflight_host_capabilities` in all three files", and re-measured here: the only non-test callers of `check_action_capabilities` are `host_cmd._action_rows`), so the output advertises a push-denial refusal that protects nothing while `aw oc run` reviews and mutates freely. The maintainer ruled on 4h7tt0 OQ-02 (2026-09-10, recorded in backlog `aagh7v`): REMOVE `supports_deny_push` AND the `review`/`mutate`/`contractless_prompt` requirement entries that reference it. The flag was never shipped (added `30108f78` 2026-09-04; newest tag `v1.3.0-rc.1`), so removal has no external consumer.
- Scope: IN: delete the `supports_deny_push` field, `CAP_DENY_PUSH`, its `RUNNER_SAFETY_CAPABILITIES`, `_DECLARED_UNENFORCED` and `_RUNNER_SAFETY_PROBES` entries and `__all__` export; delete the `ACTION_REVIEW`/`ACTION_MUTATE`/`ACTION_CONTRACTLESS_PROMPT` constants and their `ACTION_CAPABILITY_REQUIREMENTS` entries so `ACTION_CLASSES` is `(ACTION_READ_ONLY,)`; correct every docstring, help string and comment that describes the removed flag or the "four action classes"; re-point the tests, PRESERVING the two-sided preflight coverage via a synthetic test-local action; amend spec `25kzda` where it describes the flag as preserved. OUT: `supports_commit_gateway` (kept; see OQ-01), the preflight machinery itself (`check_action_capabilities`, `preflight_host_capabilities`, `UnknownActionError`, `RUN_HOST_CAPABILITY`, all kept and still tested), spec 5.2's host-requirement prose ("deny push-capable network routes") and its packet example's `"deny_push"` string, both of which state a requirement on a HOST rather than naming the Python field, and `run_evidence.RUN_FINDING_CODES`' `RUN-HOST-CAPABILITY` row, whose `BOUND` binding is unchanged because its three named predicates all survive.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, agent_workflows/host_cmd.py, agent_workflows/cli.py, agent_workflows/run_evidence.py, tests/test_host_capability_extension.py, tests/test_host_sandbox_profile.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- Set: nopushflag
- Order: 1
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 01reg8
- From-Backlog: aagh7v

## Workflow history
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): Reviewed via /plan-review; 8 findings (PR-601..PR-608), all FIXED. Corrected the Scope-Paths spec path (named a nonexistent file), added the missing dataclasses import to E-02, added the synthetic-gated-action seam that keeps the preflight REFUSES/PROCEEDS pair non-vacuous after the only remaining action class requires nothing, corrected three 'every action requiring them is refused' claims that the removal falsifies, split E-06 into three items over AST-measured method lists, declined three adjacent scope temptations with carriers, and rewrote the gate with an approval statement, scope fence, honesty rule and conditional transition. Raised OQ-03 (spec table keeps four rows while the code drops to one).

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog aagh7v; re-measured every `supports_deny_push`/`CAP_DENY_PUSH` reference at HEAD `cfc7f5c1`, confirmed `check_action_capabilities` has no consumer beyond `host_cmd`, and captured the current `aw host capabilities opencode` output (3 pairs refused).

## Goal

Stop `aw host capabilities` from printing a push-denial protection that nothing enforces, by removing the unshipped `supports_deny_push` flag and the three action-class verdicts that exist only to display it, while keeping the preflight machinery and its two-sided tests GENUINELY intact — meaning the REFUSES half still refuses something, which after this change requires a synthetic gated action rather than any surviving production one (F-7).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and a test that fails first

- [ ] E-01 Capture the BEFORE state: `python3 -m agent_workflows host capabilities opencode`, and the per-file reference inventory `rg -c "supports_deny_push|CAP_DENY_PUSH|ACTION_REVIEW\b|ACTION_MUTATE\b|ACTION_CONTRACTLESS_PROMPT" agent_workflows tests`. Use `-c` (per-file counts) rather than `-n`: the unanchored pattern matches `run_selection_policy`'s and `runner_shared`'s own unrelated review vocabulary, so a per-file count is the readable BEFORE/AFTER comparison and F-6's explained-hit list is what makes it auditable.
  - Depends on: none
  - Expected outcome: output shows `NO   supports_deny_push (runner-safety)`, three `REFUSED` action lines and `1 host(s) reported; 3 (host, action) pair(s) refused`. RE-DERIVE the counts at execution time rather than asserting the authoring numbers: the Findings table's F-4 records 26 matching lines in `tests/test_host_capability_extension.py` and 25 in `agent_workflows/host_sandbox_profile.py` as CONTEXT measured at authoring, and the bar is that every file with a hit is either a target of E-03..E-06 or appears in F-6's explained list.
  - Execution state: pending
- [ ] E-02 Add `DenyPushRemovedTests` to `tests/test_host_capability_extension.py` asserting: `"supports_deny_push" not in {f.name for f in dataclasses.fields(HostSandboxCapabilities)}`; `not hasattr(hsp, "CAP_DENY_PUSH")`; `hsp.CAP_DENY_PUSH` is absent from `hsp.__all__`; `hsp.ACTION_CLASSES == (hsp.ACTION_READ_ONLY,)`; `set(hsp.ACTION_CAPABILITY_REQUIREMENTS) == {hsp.ACTION_READ_ONLY}`; `check_action_capabilities("review", ...)` and `("mutate", ...)` and `("contractless_prompt", ...)` each raise `UnknownActionError`; and `host_cmd.run_capabilities` output for `opencode` contains no `REFUSED` line and no `deny_push`. ADD `import dataclasses` to the test module: it currently imports only `argparse`, `io`, `json`, `unittest` and `contextlib` names, so `dataclasses.fields` would raise `NameError` rather than failing the assertion it is meant to prove. Run it BEFORE E-03/E-04.
  - Depends on: E-01
  - Expected outcome: the new class FAILS against the unmodified module (at least the field, `CAP_DENY_PUSH`, `ACTION_CLASSES` and `UnknownActionError` assertions), and fails on an ASSERTION rather than on a collection or import error.
  - Execution state: pending

### Task group 2: remove the flag and the verdicts

- [ ] E-03 In `agent_workflows/host_sandbox_profile.py` delete the `supports_deny_push: bool = False` field, `CAP_DENY_PUSH = "supports_deny_push"`, its members of `RUNNER_SAFETY_CAPABILITIES`, `_DECLARED_UNENFORCED` and `_RUNNER_SAFETY_PROBES`, and `"CAP_DENY_PUSH"` from `__all__`; reword "three runner-safety" to "two" in the module docstring ("Three fields and a preflight close that"), the field comment ("Two of the three name host ENFORCEMENT"), the `RUNNER_SAFETY_CAPABILITIES` comment ("The three runner-safety capability names"), `probe_runner_safety_capabilities`' docstring ("Decide the three runner-safety capabilities"), `detect_host_capabilities`' docstring ("The three RUNNER-SAFETY capabilities ... Two of the three are declared and never probed"), and the `_DECLARED_UNENFORCED` rationale comment ("WHY THESE TWO ARE DECLARED AND NOT PROBED", which becomes one). KEEP that rationale comment's substance for `commit_gateway`, including its measured justification and its explicit prohibition on inferring support from `git_commit_helper.offer_commit`: the anti-inference rule is what OQ-01 keeps the capability FOR, and reducing it to a bare sentence discards the only durable record of why. Do NOT add any presence-based probe on the way out (module docstring "WHY THE PROBE EXECUTES INSTEAD OF INSPECTING").
  - Depends on: E-02
  - Expected outcome: `rg -n "deny_push|DENY_PUSH" agent_workflows/host_sandbox_profile.py` returns nothing; `HostSandboxCapabilities` has 12 fields; `RUNNER_SAFETY_CAPABILITIES == ('supports_commit_gateway', 'supports_fresh_verifier_session')`.
  - Execution state: pending
- [ ] E-04 In the same module delete `ACTION_REVIEW`, `ACTION_MUTATE`, `ACTION_CONTRACTLESS_PROMPT` (constants, `__all__` entries, and their three `ACTION_CAPABILITY_REQUIREMENTS` entries), set `ACTION_CLASSES = (ACTION_READ_ONLY,)`, and rewrite the "The FOUR action classes spec 25kzda 5.2 defines" comment to say only read-only is represented, and why (the other three were verdicts nothing consumed; maintainer ruling 4h7tt0 OQ-02). Also correct the module docstring's "compares one of spec 25kzda 5.2's FOUR action classes" and `UnknownActionError`'s docstring "An action class outside the spec's four was named", both of which would otherwise name a count the module no longer carries. STATE IN THE REWRITTEN COMMENT that spec 25kzda 5.2's action TABLE still declares four rows and is deliberately not narrowed (it describes what a host must prove, and E-07 amends only the sentences that claim the Python flag is preserved), so a later reader does not "restore parity" by re-adding the three constants. Leave `check_action_capabilities`, `preflight_host_capabilities`, `UnknownActionError` (the class itself) and `RUN_HOST_CAPABILITY` unchanged, and leave every `UNREPRESENTED_SPEC_CAPABILITIES` key in place: four of the seven (`argv_capture`, `timeout_cancel`, `hook_preserving_commit`, `isolated_worktree`) are referenced ONLY by the three entries being deleted, and the dict is the honest record of what the contract cannot represent rather than a per-action index, so pruning it would delete spec-derived gaps this plan was not asked to withdraw.
  - Depends on: E-03
  - Expected outcome: `python3 -c "from agent_workflows import host_sandbox_profile as h; print(h.ACTION_CLASSES, list(h.ACTION_CAPABILITY_REQUIREMENTS), len(h.UNREPRESENTED_SPEC_CAPABILITIES))"` prints `('read_only',) ['read_only'] 7`.
  - Execution state: pending
- [ ] E-05 Correct the prose that describes the removed flag or the four classes: `host_cmd` module docstring ("the contract records two capabilities that are DECLARED AND NEVER PROBED ... every action requiring them is refused" — note the SECOND clause becomes FALSE once `read_only` is the only action, because no remaining action requires `commit_gateway`, so it must be rewritten to say the capability reads not-supported and NO action gates on it today, not merely renumbered); `cli.py` help strings for `host probe` ("(commit gateway, push denial) are declared but never probed ... any action requiring them is refused", same two corrections) and `host capabilities` ("each of the four action classes"), and the `SAFETY & DEFAULTS` epilog ("Two runner-safety capabilities (commit gateway, push denial) are declared but never probed ... actions requiring them are refused: fail-closed"); and the `run_evidence` comment beside the retired `RUN-NO-PUSH` row that says the capability is "deliberately LEFT IN PLACE", which becomes a note that plan `01reg8` removed it on the same maintainer ruling. PRESERVE that comment's closing prohibition ("DO NOT REINTRODUCE THE CODE BOUND TO A PRESENCE CHECK"), which outlives the flag and is the reason the row was retired rather than rebound; update only its stale `host_sandbox_profile.py:88-95` line reference to a symbol citation.
  - Depends on: E-04
  - Expected outcome: `rg -n "push denial|four action classes|LEFT IN PLACE" agent_workflows/cli.py agent_workflows/host_cmd.py agent_workflows/run_evidence.py` returns nothing, AND no remaining sentence in those three files claims an action is refused for want of a runner-safety capability. (`host_sandbox_profile.py` is deliberately absent from that grep: its own "commit gateway and push denial" phrase lives in the `contractless_prompt` `spec_basis` string E-04 deletes outright.)
  - Execution state: pending

### Task group 3: tests and spec

- [ ] E-06 BUILD THE SYNTHETIC-ACTION SEAM FIRST, before deleting any action reference, because it is what keeps the two-sided preflight coverage alive. Add to `tests/test_host_capability_extension.py` a module-level context manager (mirroring the shipped `forced_runner_safety_verdicts` save/restore style, and the file's existing `@contextmanager` import) that inserts `ActionRequirement(action="_gated_for_test", required=(CAP_COMMIT_GATEWAY, CAP_FRESH_VERIFIER_SESSION), unrepresented=("path_policy",), spec_basis=<why this synthetic action exists>)` into `ACTION_CAPABILITY_REQUIREMENTS` and removes it in `finally`. WHY A SYNTHETIC ACTION AND NOT A NARROWED ASSERTION: after E-04 the ONLY remaining action requires nothing, so `check_action_capabilities` can never return `satisfied=False` and `preflight_host_capabilities` can never refuse; re-pointing `CheckerTests` / `FailClosedPreflightTests` at `ACTION_READ_ONLY` would leave the REFUSES half of every pair VACUOUSLY PASSING, which is the fail-open direction this module's own docstring exists to refuse. The seam must restore the dict on exception (the same process-global leak reason `forced_runner_safety_verdicts` documents) and MUST NOT be left registered, or E-02's `set(ACTION_CAPABILITY_REQUIREMENTS) == {ACTION_READ_ONLY}` assertion becomes order-dependent under the suite's random ordering.
  - Depends on: E-05
  - Expected outcome: with the seam added and NOTHING else changed, `python3 -m pytest tests/test_host_capability_extension.py -o addopts=""` still passes; a scratch check shows `check_action_capabilities("_gated_for_test", HostSandboxCapabilities(platform="linux"))` REFUSES naming both capabilities, the same call with both True PROCEEDS, and `ACTION_CAPABILITY_REQUIREMENTS` is back to its original keys after the block exits.
  - Execution state: pending
- [ ] E-07 Re-point the action-class tests onto the seam, so the REFUSES/PROCEEDS pair survives. In `tests/test_host_capability_extension.py` drop the `ACTION_REVIEW`/`ACTION_MUTATE`/`ACTION_CONTRACTLESS_PROMPT` imports and switch every use to `"_gated_for_test"` inside the E-06 context manager. The 12 affected methods, measured by AST at review: `RequirementMapTests.test_requirement_map_structure_and_coverage` (reduce to `{ACTION_READ_ONLY}` and `len(ACTION_CLASSES) == 1`, and DROP its `review.unrepresented` assertion, whose subject E-04 deletes); `CheckerTests.test_it_names_multiple_missing_capabilities_in_one_verdict` (now names TWO, `(CAP_COMMIT_GATEWAY, CAP_FRESH_VERIFIER_SESSION)`), `test_the_verdict_carries_the_evidence_for_each_missing_capability`, `test_the_checker_runs_no_probe`, and `test_a_fully_capable_host_passes_every_action` (keep it iterating `ACTION_CLASSES`, which is now one entry, and ALSO assert the seam action passes, or the positive half degenerates to a requirement-free action that cannot fail); `FailClosedPreflightTests.test_the_message_carries_the_recovery_command`, `test_it_REFUSES_when_a_required_capability_is_unsupported`, `test_it_PROCEEDS_when_the_same_action_is_satisfied`, `test_the_refusal_starts_no_session_and_mutates_nothing`, `test_the_refusal_is_ITEM_LOCAL_and_does_not_abort_the_run`, `test_an_independent_item_still_passes_after_another_is_refused` (its independent-item half already uses `ACTION_READ_ONLY` and stays), and `test_a_real_host_today_refuses_the_mutating_actions` (rename, and assert the missing set is `{CAP_COMMIT_GATEWAY}` since `fresh_verifier_session` probes True on a real host). `test_the_message_carries_the_recovery_command` asserts the literal `required by mjx7ne action review`, so its expected string changes with the action name. Leave `test_an_unknown_action_raises_rather_than_defaulting` / `test_an_unknown_action_still_raises` alone: both pass `"execute"`, which is still unknown.
  - Depends on: E-06
  - Expected outcome: `python3 -m pytest tests/test_host_capability_extension.py -o addopts=""` passes with the REFUSES and PROCEEDS tests both COLLECTED and both PASSING, and no test asserts a refusal that the requirement map can no longer produce.
  - Execution state: pending
- [ ] E-08 Re-point the capability-name tests. `tests/test_host_sandbox_profile.py`: drop `"supports_deny_push"` from `CONTRACT_FIELDS`. `tests/test_host_capability_extension.py`: drop the `CAP_DENY_PUSH` import; drop it from the tuple in `test_new_contract_fields_and_defaults`; rename `test_the_two_unenforced_capabilities_are_declared_and_not_probed` to `..._the_unenforced_capability_is_declared_and_not_probed` and reduce its loop to `CAP_COMMIT_GATEWAY`; delete the `deny-push` row of `PRESENCE_VS_OBSERVATION` (its witness is the SAME helper as the `commit-gateway` row, so the table keeps its anti-inference claim and loses only the duplicate); switch `MockSeamTests.test_the_seam_is_restored_even_when_the_body_raises` to `CAP_COMMIT_GATEWAY`; `test_the_json_payload_carries_the_full_contract_and_action_verdicts` expects 1 action class and 1 host action; `test_capabilities_shows_both_an_allowed_and_a_refused_action` is renamed and reduced to the ALLOWED assertion (the REFUSED absence is E-02's, so the two do not both own it). `tests/test_hostdedup_third_host.py` needs NO edit (verified at review: it references neither the flag nor any action constant).
  - Depends on: E-07
  - Expected outcome: `python3 -m pytest tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py tests/test_hostdedup_third_host.py -o addopts=""` all pass, including E-02's `DenyPushRemovedTests`, and `rg -n "CAP_DENY_PUSH|deny_push" tests/` returns only E-02's negative assertions.
  - Execution state: pending
- [ ] E-09 Amend spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`). Three sentences are rewritten and one host-requirement line is deliberately kept. (a) The build-order paragraph "carries 13 fields including the three runner-safety ones (`supports_commit_gateway`, `supports_deny_push`, `supports_fresh_verifier_session`)" becomes 12 fields and two runner-safety ones, and its stale `host_sandbox_profile.py:107-111` citation becomes a symbol citation. (b) The 4.2 retirement sentence "Section 5.2's `supports_deny_push` capability is DELIBERATELY PRESERVED for that reason, so the fail-closed refusal outlives the reporting code" is rewritten to record that the flag and the three verdicts were REMOVED by plan `01reg8` on the maintainer ruling of 4h7tt0 OQ-02 because nothing consumed the refusal; keep the surrounding "THE PROMISE IS WITHDRAWN, NOT THE PROTECTION" analysis, which is still the reason 4.2's row went. (c) The 5.2 paragraph "THE PUSH-DENIAL ENTRY BELOW IS A REQUIREMENT ON A HOST, AND IT SURVIVED THE RETIREMENT ..." keeps its FIRST claim (the entry is a requirement on a host, and it stays) and loses only the clause that rests on the flag ("That answer FAILS CLOSED - `supports_deny_push` is declared False and never probed, so an action requiring it is REFUSED - which is why the requirement is kept"), replaced by the honest post-removal reason: the requirement asks what a host can enforce, no host can, and the list records the gap so a future probed capability has somewhere to land; its closing sentence naming backlog `aagh7v` as pending work becomes a record that `01reg8` did it. (d) The section 7 "MEASURED:" sentence drops `supports_deny_push` and keeps the commit-gateway half, which backlog `b7tlsh` still owns. DO NOT TOUCH the 5.2 host-requirement bullet "deny push-capable network routes and withhold remote credentials", the 5.2 action TABLE's four rows, or the packet example's `"deny_push"` string: all three state what a HOST must prove, which is unchanged, and backlog `oq05nc` is the live carrier for ever building it. Record the amendment with `python3 -m agent_workflows specs note <spec path> --message "AMENDED 2026-09-24 (plan 01reg8, backlog aagh7v): ..."`.
  - Depends on: E-08
  - Expected outcome: `rg -n "supports_deny_push" <spec>` returns only lines that describe the removal; the 5.2 host-requirement bullet and the four-row action table are unchanged; the spec's `## Workflow history` gains one AMENDED line.
  - Execution state: pending

### Task group 4: after state and the suite

- [ ] E-10 Capture the AFTER state: `python3 -m agent_workflows host capabilities opencode` and the residual per-file inventory `rg -c "supports_deny_push|CAP_DENY_PUSH|ACTION_REVIEW\b|ACTION_MUTATE\b|ACTION_CONTRACTLESS_PROMPT" agent_workflows tests`.
  - Depends on: E-09
  - Expected outcome: no `supports_deny_push` row, only `ALLOWED  read_only`, and `1 host(s) reported; 0 (host, action) pair(s) refused`. Every remaining file in the inventory is accounted for by F-6's explained list — `run_selection_policy.py` and `tests/test_run_selection_policy.py` (`pol.ACTION_REVIEW`, the lifecycle vocabulary), `runner_shared.py` plus `oc_runipd.py`/`agy_runipd.py` (`INTEGRATION_ACTION_REVIEW`, matched because the pattern is a substring), and `tests/test_host_capability_extension.py` (E-02's negative assertions) — with NO hit in `agent_workflows/host_sandbox_profile.py`, `host_cmd.py`, `cli.py`, `run_evidence.py` or `tests/test_host_sandbox_profile.py`. Name each surviving file and why, rather than asserting a count.
  - Execution state: pending
- [ ] E-11 Run the bare suite: `python3 -m pytest`.
  - Depends on: E-10
  - Expected outcome: no new failures relative to a baseline taken the same way at the start of execution.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Presence-based inference is forbidden (`host_sandbox_profile` module docstring, "WHY THE PROBE EXECUTES INSTEAD OF INSPECTING"); backlog `aagh7v` repeats it for this removal. Nothing here adds a probe.
- `tests/test_host_sandbox_profile.CONTRACT_FIELDS` (not dataclass introspection) drives the default-False and snapshot tests, so the field must be removed there too or the suite fails on a missing attribute.
- `tests/test_run_no_push_boundary.py`, which 4h7tt0 added to pin `CAP_DENY_PUSH`'s shape, no longer exists (deleted by the suite trim `19313eed`), so it is not in scope.
- `run_selection_policy.ACTION_REVIEW` is a DIFFERENT symbol (the lifecycle action vocabulary) and must not be touched. `runner_shared.INTEGRATION_ACTION_REVIEW` (used by `oc_runipd` and `agy_runipd`) is a THIRD, also unrelated, and is matched by the inventory pattern only as a substring.
- A ONE-SIDED CAPABILITY TEST IS A FAIL-OPEN TEST, and this module says so about itself: `_probe_fresh_verifier_session`'s docstring requires both a finalizing and a REFUSED half because "accepting only the positive half would report True for a contract that never refuses", and `test_it_PROCEEDS_when_the_same_action_is_satisfied` carries "a one-sided demonstration proves nothing". That is why E-06 builds a synthetic gated action rather than re-pointing the refusal tests at the requirement-free `read_only`.
- The suite runs with `-p randomly` (via `pyproject.toml` `addopts`), so a test that mutates the process-global `ACTION_CAPABILITY_REQUIREMENTS` MUST restore it, exactly as `forced_runner_safety_verdicts` restores `_FORCED_RUNNER_SAFETY`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `cfc7f5c1`; re-measured and corrected at review (HEAD `4e91bb1b`), where noted.

| # | Site | Reference |
| --- | --- | --- |
| F-1 | `host_sandbox_profile` | field `supports_deny_push`, `CAP_DENY_PUSH`, `__all__`, `RUNNER_SAFETY_CAPABILITIES`, `_DECLARED_UNENFORCED`, `_RUNNER_SAFETY_PROBES`, and `CAP_DENY_PUSH` in the `review`/`mutate`/`contractless_prompt` requirement entries. Also the COUNT PROSE in six places: the module docstring's "Three fields and a preflight close that" and "spec 25kzda 5.2's FOUR action classes", the field comment's "Two of the three name host ENFORCEMENT", the `RUNNER_SAFETY_CAPABILITIES` comment, `probe_runner_safety_capabilities`' and `detect_host_capabilities`' docstrings, and `UnknownActionError`'s "outside the spec's four" |
| F-2 | `host_cmd`, `cli.py` | prose only: "two capabilities that are DECLARED AND NEVER PROBED", "(commit gateway, push denial)", "four action classes". CORRECTED AT REVIEW: each of those three sites ALSO asserts that "every action requiring them is refused", a clause that becomes FALSE once `read_only` is the only action (nothing then requires `commit_gateway`), so E-05 must rewrite the claim rather than renumber it |
| F-3 | `run_evidence` | comment beside the retired `RUN-NO-PUSH` row: "that capability is deliberately LEFT IN PLACE". The same comment's closing "DO NOT REINTRODUCE THE CODE BOUND TO A PRESENCE CHECK" prohibition is KEPT (only its stale line reference is corrected). The `RUN-HOST-CAPABILITY` row itself is untouched: its `binding=BOUND` rests on `preflight_host_capabilities`, `format_host_capability_finding` and `check_action_capabilities`, all three of which survive |
| F-4 | tests | `tests/test_host_sandbox_profile.CONTRACT_FIELDS` (1 line). `tests/test_host_capability_extension.py`: 26 matching lines across the imports, one class-level table and 16 test methods, enumerated BY SYMBOL in E-07 and E-08 (AST-measured at review; the authoring note of "nine uses" undercounted, which is why the two items name every method). `tests/test_hostdedup_third_host.py` needs NO edit: verified at review to reference neither the flag nor any action constant, though it does call `host_cmd._describe_host("scripted")` and so exercises the reduced action list |
| F-5 | spec `25kzda` | The spec's real path is `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (CORRECTED AT REVIEW; the authored `- Scope-Paths:` and this section both named `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, which does not exist). Sentences to amend: "carries 13 fields including the three runner-safety ones", "DELIBERATELY PRESERVED", "SURVIVED THE RETIREMENT", section 7's "MEASURED:" sentence. NOT amended: the packet example `"required_host_capabilities": [..., "deny_push"]`, the 5.2 host-requirement bullet, and 5.2's four-row action table, all of which state what a HOST must prove |
| F-6 | consumers | `check_action_capabilities` is called outside its module only by `host_cmd._action_rows`; `preflight_host_capabilities` only by tests. No `docs/` page or `CHANGELOG.md` entry mentions the flag (re-verified at review: `rg "deny_push\|deny push\|four action classes" docs/ CHANGELOG.md README.md` is empty). Files that survive the E-10 inventory for UNRELATED reasons: `run_selection_policy.py` and `tests/test_run_selection_policy.py` (`pol.ACTION_REVIEW`, the lifecycle vocabulary), and `runner_shared.py`, `oc_runipd.py`, `agy_runipd.py` (`INTEGRATION_ACTION_REVIEW`, a substring match) |
| F-7 | vacuity risk | ADDED AT REVIEW. After E-04 the only action requires nothing, so `check_action_capabilities` cannot return unsatisfied and `preflight_host_capabilities` cannot refuse. Every REFUSES-side test would therefore pass vacuously if re-pointed at `ACTION_READ_ONLY`. E-06's synthetic `_gated_for_test` action is what keeps the pair two-sided; verified at review by driving it (REFUSES naming both capabilities; PROCEEDS when both are True; `ACTION_CAPABILITY_REQUIREMENTS` restored after the block) |

Current output (`aw host capabilities opencode`, trimmed): `NO   supports_deny_push (runner-safety)`, `REFUSED  review  missing: supports_commit_gateway, supports_deny_push` (same for `mutate`, `contractless_prompt`), `1 host(s) reported; 3 (host, action) pair(s) refused`.

## Proposed changes (ordered, validatable)

1. Baseline, then the failing regression test (E-01, E-02).
2. Remove the flag (E-03), then the three requirement entries and constants (E-04), then the prose that describes them (E-05).
3. Build the synthetic-action seam BEFORE re-pointing anything (E-06), so the REFUSES half of every preflight pair keeps a requirement it can actually fail; then re-point the action tests onto it (E-07); then re-point the capability-name tests (E-08).
4. Amend spec `25kzda` so it no longer says the flag is preserved, keeping the host requirement it still asserts (E-09).
5. After-output with every surviving inventory hit explained, then the bare suite (E-10, E-11).

## Deferred / out of scope (with reason)

- Removing `supports_commit_gateway`, which after this plan gates no action and is equally unenforced.
  - Carrier-Declined: the maintainer's ruling covers only `supports_deny_push`; see OQ-01, where the default is to keep it.
- Wiring `preflight_host_capabilities` into the runners.
  - Carrier-Declined: not requested; with only `read_only` represented it would refuse nothing, and real enforcement belongs to the OS-sandbox line of work, not to this cleanup.
- Editing spec `25kzda`'s packet example, its 5.2 host-requirement bullet, and 5.2's four-row action table, all of which name push denial.
  - Carrier-Declined: they describe what a HOST must prove, which stays true; only the Python flag is removed. Backlog `oq05nc` is the live carrier for ever building a real OS-level push-denial boundary, and it explicitly anticipates this plan landing first ("if `aagh7v` lands first, building this means reintroducing the field as a probed capability"), so narrowing the spec's requirement list would delete that work's landing site.
- Pruning `UNREPRESENTED_SPEC_CAPABILITIES`, four of whose seven keys become referenced by no requirement entry.
  - Carrier-Declined: the dict is the honest record of what the contract cannot represent (its own comment: "a requirement that is never listed is a requirement that can never fail"), not a per-action index. Deleting spec-derived gaps because the only action citing them went away would withdraw requirements this plan was not asked to withdraw.
- Reconciling `run_evidence.RUN_FINDING_CODES`' `RUN-HOST-CAPABILITY` row or its `BOUND` binding.
  - Carrier-Declined: verified at review that its three named predicates (`preflight_host_capabilities`, `format_host_capability_finding`, `check_action_capabilities`) all survive this plan, so the binding is still honest. Only the neighbouring retired-`RUN-NO-PUSH` comment needs the correction E-05 makes.

## Scope check

- Over-scope: none. The prose edits in `cli.py`/`host_cmd`/`run_evidence` only correct text that would otherwise describe removed code, and three adjacent temptations (pruning `UNREPRESENTED_SPEC_CAPABILITIES`, narrowing spec 5.2's host-requirement list, touching the `RUN-HOST-CAPABILITY` row) are named and declined above.
- Under-scope: the authored plan under-specified three things, each now an item or a named constraint — the vacuity created by leaving only a requirement-free action (F-7, E-06), the `every action requiring them is refused` clause that becomes false (F-2, E-05), and the missing `import dataclasses` in the test module (E-02). E-10's inventory, with every surviving file explained, is the residual check.

## Required tests / validation

- E-02's `DenyPushRemovedTests` fails before (on an assertion, not an import error) and passes after.
- Targeted run of `tests/test_host_capability_extension.py`, `tests/test_host_sandbox_profile.py` and `tests/test_hostdedup_third_host.py` passes, with the synthetic-action REFUSES and PROCEEDS tests BOTH collected and BOTH passing, and the REFUSES side naming the capabilities it observed missing so the assertion is demonstrably non-vacuous.
- The synthetic-action seam is proven to restore `ACTION_CAPABILITY_REQUIREMENTS` after both a normal exit and a raising body.
- `python3 -m agent_workflows specs check <spec>` passes after the amendment, and the spec's 5.2 host-requirement bullet plus its four-row action table are shown unchanged.
- Before/after `aw host capabilities opencode` output pasted.
- Bare `python3 -m pytest` summary line pasted, against a baseline taken the same way.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`) is amended by E-09 and is listed in `- Scope-Paths:`. WHY: three of its paragraphs state that `supports_deny_push` is "DELIBERATELY PRESERVED" and that its refusal "SURVIVED THE RETIREMENT"; after this plan those sentences would describe code that no longer exists, and the 5.2 paragraph itself names backlog `aagh7v` as the pending removal, so leaving it would have the spec still pointing at work this plan performed. The amendment is deliberately NARROW: it corrects only the sentences whose truth depends on the Python flag existing, and leaves every sentence stating what a HOST must prove, because those remain true and are `oq05nc`'s landing site. No user-facing docs mention the flag (F-6). Both runners announce declared spec edits before a run and reconcile them at finalize, so the corrected `- Scope-Paths:` entry is what makes this amendment visible; the path as authored resolved to no file, which would have left a real spec edit undeclared.

## Open questions

### OQ-01: Should `supports_commit_gateway` be removed too, now that it gates no action?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: b7tlsh
- Resolution or deferral rationale: Default: KEEP it. The 2026-09-10 ruling names only `supports_deny_push`, and the commit-gateway capability still has a probe note and a presence-vs-observation test row that document a real anti-inference rule. ADDED AT REVIEW, because it sharpens the consequence the maintainer is accepting: after this plan `supports_commit_gateway` is required by NO action at all (the only surviving class, `read_only`, requires nothing), so it becomes a capability that is declared, never probed, and gates nothing — a strictly weaker position than the one it holds today. It also acquires a SECOND reason to exist beyond the anti-inference note: it is what E-06's synthetic test action requires, so it is the only remaining capability by which the preflight's refusal path can be exercised at all. Backlog `b7tlsh` is the live carrier for the separate question of whether the spec should claim commit-gateway enforcement at all. If the maintainer wants the field removed, that is a follow-up with the same shape as this plan, and it would need to answer how the preflight keeps two-sided coverage afterwards.

### OQ-02: Remove the three requirement entries, or only drop `CAP_DENY_PUSH` from them?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Remove the entries. 4h7tt0 OQ-02's recorded answer lists "deletion of the `review`/`mutate`/`contractless_prompt` requirement entries that reference it", and dropping only the flag would leave the same three unconsumed `REFUSED` lines printed on `commit_gateway` alone, which is the exact misleading output the ruling targets.

### OQ-03: The code's action vocabulary drops to one class while spec 5.2's table keeps four. Is that divergence acceptable, or should the spec table be narrowed too?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: This question is answered, either way, INSIDE this plan's own diff and leaves no work behind it. Under the default (accept the divergence) E-04's replacement comment RECORDS it permanently in the code, so the fact survives this plan reaching `executed` without needing a carrier to revisit; under the alternative (narrow the spec table) the edit happens in E-09 of this same plan. There is therefore no outstanding obligation for a backlog item or a successor plan to own. The adjacent obligations that DO outlive this plan already have their own live carriers and are not duplicated here: `oq05nc` owns building a real push-denial boundary (and explicitly anticipates this removal landing first), and `b7tlsh` owns whether the spec should claim commit-gateway enforcement at all.
- Resolution or deferral rationale: RAISED AT REVIEW. Default: ACCEPT the divergence and record it in the spec rather than narrowing the table. The two artifacts answer different questions — the spec table states what a HOST must prove for each kind of work, which is unchanged by deleting a Python constant, while `ACTION_CAPABILITY_REQUIREMENTS` states what THIS contract can currently check, which is now only the requirement-free read-only case. The module's existing comment argues the opposite direction ("Deliberately the spec's four, not a convenient two: an `execute`/`review` pair would have silently renamed the policy and made this layer's vocabulary disagree with the packet field the spec specifies"), so this plan is knowingly creating the disagreement that comment was written to prevent; E-04 therefore replaces it with a comment saying so explicitly, which is why the divergence is recorded rather than silent. Narrowing the spec table instead would withdraw host requirements the maintainer has not asked to withdraw and would collide with backlog `oq05nc`. Non-blocking because either answer leaves the removal itself correct; only the spec's shape differs.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full BEFORE `python3 -m agent_workflows host capabilities opencode` output showing `NO   supports_deny_push (runner-safety)`, three `REFUSED` lines and `3 (host, action) pair(s) refused`, plus the grep inventory.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_host_capability_extension.py -o addopts="" -k DenyPushRemoved` run against the UNMODIFIED module, showing it FAILED (non-zero failed count and at least one of the field / `CAP_DENY_PUSH` / `ACTION_CLASSES` assertion messages).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "deny_push|DENY_PUSH" agent_workflows/host_sandbox_profile.py` (empty) and `python3 -c "import dataclasses; from agent_workflows import host_sandbox_profile as h; print(len(dataclasses.fields(h.HostSandboxCapabilities)), h.RUNNER_SAFETY_CAPABILITIES)"` printing `12 ('supports_commit_gateway', 'supports_fresh_verifier_session')`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the E-04 one-liner printing `('read_only',) ['read_only']`, and `git diff agent_workflows/host_sandbox_profile.py` showing `check_action_capabilities` and `preflight_host_capabilities` bodies unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the E-05 `rg` (empty) and `python3 -m agent_workflows host capabilities --help` showing the rewritten description.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the scratch driving of the synthetic action showing BOTH sides — `check_action_capabilities("_gated_for_test", HostSandboxCapabilities(platform="linux"))` returning `satisfied=False` with `missing=('supports_commit_gateway', 'supports_fresh_verifier_session')`, the same call with both fields True returning `satisfied=True`, and `preflight_host_capabilities` on the incapable descriptor returning `ok=False` with `finding_code='RUN-HOST-CAPABILITY'` — plus proof the seam RESTORES the dict (print `list(ACTION_CAPABILITY_REQUIREMENTS)` after the block and after a body that RAISES, both showing the original keys). Also paste `python3 -m pytest tests/test_host_capability_extension.py -o addopts=""` passing with only the seam added.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_host_capability_extension.py -o addopts=""` with 0 failed, AND `-k "REFUSES or PROCEEDS"` output showing BOTH tests collected and passed (a one-sided pair is the failure this item exists to prevent), AND `rg -n "ACTION_REVIEW|ACTION_MUTATE|ACTION_CONTRACTLESS_PROMPT" tests/test_host_capability_extension.py` returning only E-02's negative assertions. State explicitly that the REFUSES test's assertion is non-vacuous by naming the capabilities it observed missing.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py tests/test_hostdedup_third_host.py -o addopts=""` summary with 0 failed, `rg -n "CAP_DENY_PUSH|deny_push" tests/` showing only E-02's negative assertions, and the `PRESENCE_VS_OBSERVATION` row count before and after (4 -> 3) with the surviving `commit-gateway` row quoted to show the anti-inference claim is intact.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste `rg -n "supports_deny_push|DELIBERATELY PRESERVED|SURVIVED THE RETIREMENT" <spec>` showing only removal-describing lines; `rg -n "deny push-capable network routes" <spec>` showing the host-requirement bullet STILL PRESENT and unchanged; the `git diff` of the spec confirming the four-row 5.2 action table and the packet example's `"deny_push"` string were not touched; the new AMENDED workflow-history line; and `python3 -m agent_workflows specs check <spec>` passing.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste the full AFTER `python3 -m agent_workflows host capabilities opencode` output next to V-01's: no `supports_deny_push` row, only `ALLOWED  read_only`, final line `1 host(s) reported; 0 (host, action) pair(s) refused`; and the residual per-file inventory with EVERY surviving file named and explained against F-6's list, plus the explicit statement that the five target files have zero hits.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: paste the bare `python3 -m pytest` summary line, with the baseline summary line, and name any failure present in both.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (remove the unshipped flag and the verdicts that only displayed it). E-06 and E-07 are separate items rather than one because building the synthetic seam and re-pointing twelve methods onto it have different failure modes: the seam fails by leaking a process-global, the re-point fails by leaving a refusal test vacuous. E-07 and E-08 are separate because the action-class edits and the capability-name edits touch disjoint tests and are verified by different evidence.

WHAT A HUMAN IS APPROVING. Deleting a shipped-but-unreleased public symbol set (`supports_deny_push`, `CAP_DENY_PUSH`, three `ACTION_*` constants and their requirement entries) on the maintainer's recorded ruling of 4h7tt0 OQ-02, and AMENDING AN APPROVED SPEC (`25kzda`) so three of its sentences stop claiming the flag is preserved. Two judgements are genuinely the maintainer's to overrule. FIRST, OQ-01: `supports_commit_gateway` survives and after this plan gates NOTHING, so `aw host capabilities` will print one `NO` row that refuses no action; the alternative is removing it too, which the ruling did not authorize. SECOND, the spec amendment leaves 5.2's host-requirement bullet and four-row action table intact while the Python contract drops to a single action class, so spec and code deliberately disagree in COUNT; that is the honest reading (the spec states what a host must prove, the code states what this contract can check) but a maintainer may prefer the spec narrowed in the same change.

SCOPE FENCE (a declaration, so the runner can reconcile afterwards; not an instruction to stop over a scope question). Within the declared paths the intended surface is: `host_sandbox_profile.py` — the field, `CAP_DENY_PUSH`, its three collection memberships, the `__all__` entries, the three action constants and their `ACTION_CAPABILITY_REQUIREMENTS` entries, `ACTION_CLASSES`, and the count prose enumerated in F-1; `host_cmd.py` and `cli.py` — docstring and help-string prose only, no behavior; `run_evidence.py` — one comment beside the retired `RUN-NO-PUSH` row, and NOT the `RUN-HOST-CAPABILITY` row or any binding; `tests/test_host_capability_extension.py` — the new `DenyPushRemovedTests`, the new seam, and the methods E-07/E-08 enumerate; `tests/test_host_sandbox_profile.py` — one `CONTRACT_FIELDS` entry; the spec — the four sentences E-09 names. DELIBERATELY NOT IN SCOPE, mirroring Deferred: `supports_commit_gateway`, `UNREPRESENTED_SPEC_CAPABILITIES`, the preflight machinery's bodies, spec 5.2's host-requirement bullet / action table / packet example, and `tests/test_hostdedup_third_host.py` (declared nowhere and expected to need no edit). An out-of-scope edit that proves necessary should be MADE and then justified with `--scope-reason` at finalize, not abandoned.

HONESTY RULE (hard MUST). Paste the ACTUAL command output for every `V-*` item. Do not claim a test passed without its runner output, and do not record the REFUSES/PROCEEDS pair as covered without output showing BOTH collected and BOTH passing: the whole point of E-06 is that after E-04 a re-pointed refusal test can pass while asserting nothing.

STOP CONDITIONS (genuinely unsafe, distinct from a scope question). Stop and report if: the synthetic-action seam cannot be made to restore `ACTION_CAPABILITY_REQUIREMENTS` on an exception, since a leaked global would corrupt later tests under random ordering; `python3 -m agent_workflows specs check` refuses the amended spec for a reason the amendment cannot satisfy; or a symbol this plan expects to delete is already absent or has been changed under you by concurrent work.

This is a removal of dead code at the maintainer's explicit direction; it is NOT licence to infer push prevention from any helper, hook or flag, and the `run_evidence` comment's prohibition on rebinding a retired code to a presence check survives the flag it discusses.

Execute only after `- Status: approved`. Commit only the Scope-Paths files through `aw commit 01reg8 -- <paths>`; never push. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, the lifecycle transition to `executed/` is performed by the RUNNER when one is driving this plan, and by the executor via `aw ipd finalize` only when no runner owns the transition; do not hand-roll a `git mv`. Then set backlog `aagh7v` accordingly (it carries no `- Blocks-Release:`, so no release gate is owed and none may be invented).
