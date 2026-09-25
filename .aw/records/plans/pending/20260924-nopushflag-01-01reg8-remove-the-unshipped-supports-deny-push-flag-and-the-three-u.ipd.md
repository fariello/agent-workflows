# IPD: Remove the unshipped supports_deny_push flag and the three unenforced action verdicts

- Date: 2026-09-24
- Kind: child
- Concern: `aw host capabilities` prints `REFUSED  review`, `REFUSED  mutate` and `REFUSED  contractless_prompt`, each `missing: supports_commit_gateway, supports_deny_push`, on every host. NOTHING CONSUMES THOSE VERDICTS: the runners never call `host_sandbox_profile.preflight_host_capabilities` (`run_selection_policy` records "zero occurrences of `preflight_host_capabilities` in all three files", and re-measured here: the only non-test callers of `check_action_capabilities` are `host_cmd._action_rows`), so the output advertises a push-denial refusal that protects nothing while `aw oc run` reviews and mutates freely. The maintainer ruled on 4h7tt0 OQ-02 (2026-09-10, recorded in backlog `aagh7v`): REMOVE `supports_deny_push` AND the `review`/`mutate`/`contractless_prompt` requirement entries that reference it. The flag was never shipped (added `30108f78` 2026-09-04; newest tag `v1.3.0-rc.1`), so removal has no external consumer.
- Scope: IN: delete the `supports_deny_push` field, `CAP_DENY_PUSH`, its `_DECLARED_UNENFORCED` and `_RUNNER_SAFETY_PROBES` entries and `__all__` export; delete the `ACTION_REVIEW`/`ACTION_MUTATE`/`ACTION_CONTRACTLESS_PROMPT` constants and their `ACTION_CAPABILITY_REQUIREMENTS` entries so `ACTION_CLASSES` is `(ACTION_READ_ONLY,)`; correct every docstring, help string and comment that describes the removed flag or the "four action classes"; re-point the tests; amend spec `25kzda` where it describes the flag as preserved. OUT: `supports_commit_gateway` (kept; see OQ-01), the preflight machinery itself (`check_action_capabilities`, `preflight_host_capabilities`, `RUN-HOST-CAPABILITY`, all kept and still tested), and spec 5.2's host-requirement prose ("deny push-capable network routes"), which states a requirement on a host, not the Python field.
- Scope-Paths: agent_workflows/host_sandbox_profile.py, agent_workflows/host_cmd.py, agent_workflows/cli.py, agent_workflows/run_evidence.py, tests/test_host_capability_extension.py, tests/test_host_sandbox_profile.py, .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- Set: nopushflag
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 01reg8
- From-Backlog: aagh7v

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog aagh7v; re-measured every `supports_deny_push`/`CAP_DENY_PUSH` reference at HEAD `cfc7f5c1`, confirmed `check_action_capabilities` has no consumer beyond `host_cmd`, and captured the current `aw host capabilities opencode` output (3 pairs refused).

## Goal

Stop `aw host capabilities` from printing a push-denial protection that nothing enforces, by removing the unshipped `supports_deny_push` flag and the three action-class verdicts that exist only to display it, while keeping the preflight machinery and its two-sided tests intact.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and a test that fails first

- [ ] E-01 Capture the BEFORE state: `python3 -m agent_workflows host capabilities opencode` and `rg -n "supports_deny_push|CAP_DENY_PUSH|ACTION_REVIEW|ACTION_MUTATE|ACTION_CONTRACTLESS_PROMPT" agent_workflows tests`.
  - Depends on: none
  - Expected outcome: output shows `NO   supports_deny_push (runner-safety)`, three `REFUSED` action lines and `1 host(s) reported; 3 (host, action) pair(s) refused`; the grep inventory matches the Findings table.
  - Execution state: pending
- [ ] E-02 Add `DenyPushRemovedTests` to `tests/test_host_capability_extension.py` asserting: `"supports_deny_push" not in {f.name for f in dataclasses.fields(HostSandboxCapabilities)}`; `not hasattr(hsp, "CAP_DENY_PUSH")`; `hsp.ACTION_CLASSES == (hsp.ACTION_READ_ONLY,)`; `check_action_capabilities("review", ...)` raises `UnknownActionError`; and `host_cmd.run_capabilities` output for `opencode` contains no `REFUSED` line and no `deny_push`. Run it BEFORE E-03/E-04.
  - Depends on: E-01
  - Expected outcome: the new class FAILS against the unmodified module (at least the field, `CAP_DENY_PUSH` and `ACTION_CLASSES` assertions).
  - Execution state: pending

### Task group 2: remove the flag and the verdicts

- [ ] E-03 In `agent_workflows/host_sandbox_profile.py` delete the `supports_deny_push: bool = False` field, `CAP_DENY_PUSH = "supports_deny_push"`, its members of `RUNNER_SAFETY_CAPABILITIES`, `_DECLARED_UNENFORCED` and `_RUNNER_SAFETY_PROBES`, and `"CAP_DENY_PUSH"` from `__all__`; reword "three runner-safety" to "two" in the module docstring, the field comment, `probe_runner_safety_capabilities` and `detect_host_capabilities` docstrings, and the `_DECLARED_UNENFORCED` rationale comment. Do NOT add any presence-based probe on the way out (module docstring "Inspection MEASURABLY LIES" paragraph).
  - Depends on: E-02
  - Expected outcome: `rg -n "deny_push|DENY_PUSH" agent_workflows/host_sandbox_profile.py` returns nothing; `HostSandboxCapabilities` has 12 fields.
  - Execution state: pending
- [ ] E-04 In the same module delete `ACTION_REVIEW`, `ACTION_MUTATE`, `ACTION_CONTRACTLESS_PROMPT` (constants, `__all__` entries, and their three `ACTION_CAPABILITY_REQUIREMENTS` entries), set `ACTION_CLASSES = (ACTION_READ_ONLY,)`, and rewrite the "The FOUR action classes spec 25kzda 5.2 defines" comment to say only read-only is represented, and why (the other three were verdicts nothing consumed; maintainer ruling 4h7tt0 OQ-02). Leave `check_action_capabilities`, `preflight_host_capabilities`, `UnknownActionError` and `RUN_HOST_CAPABILITY` unchanged.
  - Depends on: E-03
  - Expected outcome: `python3 -c "from agent_workflows import host_sandbox_profile as h; print(h.ACTION_CLASSES, list(h.ACTION_CAPABILITY_REQUIREMENTS))"` prints `('read_only',) ['read_only']`.
  - Execution state: pending
- [ ] E-05 Correct the prose that describes the removed flag or the four classes: `host_cmd` module docstring ("two capabilities that are DECLARED AND NEVER PROBED ... every action requiring them is refused"); `cli.py` help strings for `host probe` ("(commit gateway, push denial) are declared but never probed") and `host capabilities` ("each of the four action classes"), and the `SAFETY & DEFAULTS` epilog ("Two runner-safety capabilities (commit gateway, push denial)"); and the `run_evidence` comment beside the retired `RUN-NO-PUSH` row that says the capability is "deliberately LEFT IN PLACE", which becomes a note that it was removed by this plan.
  - Depends on: E-04
  - Expected outcome: `rg -n "push denial|four action classes|LEFT IN PLACE" agent_workflows/cli.py agent_workflows/host_cmd.py agent_workflows/run_evidence.py` returns nothing.
  - Execution state: pending

### Task group 3: tests and spec

- [ ] E-06 Re-point existing tests. `tests/test_host_sandbox_profile.py`: drop `"supports_deny_push"` from `CONTRACT_FIELDS`. `tests/test_host_capability_extension.py`: drop the `CAP_DENY_PUSH` and three action imports; drop `CAP_DENY_PUSH` from the tuples in `test_new_contract_fields_and_defaults`, `test_the_two_unenforced_capabilities_are_declared_and_not_probed` (rename to `..._the_unenforced_capability_is_declared...`) and the `deny-push` row of `PRESENCE_VS_OBSERVATION`; switch `test_the_seam_is_restored_even_when_the_body_raises` to `CAP_COMMIT_GATEWAY`; reduce `test_requirement_map_structure_and_coverage` to `{ACTION_READ_ONLY}` / `len(ACTION_CLASSES) == 1`; `test_the_json_payload...` expects 1 action; `test_capabilities_shows_both_an_allowed_and_a_refused_action` becomes an ALLOWED-only assertion (the REFUSED absence is E-02's). Preserve the TWO-SIDED preflight coverage (`CheckerTests`, `FailClosedPreflightTests`, `test_a_real_host_today_refuses...`) by adding a test-local context manager that inserts a synthetic `ActionRequirement(action="_gated_for_test", required=(CAP_COMMIT_GATEWAY, CAP_FRESH_VERIFIER_SESSION), ...)` into `ACTION_CAPABILITY_REQUIREMENTS` and removes it in `finally`; those tests use that action instead of `ACTION_REVIEW`/`ACTION_MUTATE`.
  - Depends on: E-05
  - Expected outcome: `python3 -m pytest tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py tests/test_hostdedup_third_host.py -o addopts=""` all pass, including E-02's class, and the REFUSES/PROCEEDS pair still both run.
  - Execution state: pending
- [ ] E-07 Amend spec `25kzda`: the build-order paragraph ("carries 13 fields including the three runner-safety ones") becomes 12 fields and two runner-safety ones; the 4.2 retirement paragraph sentence "Section 5.2's `supports_deny_push` capability is DELIBERATELY PRESERVED" and the 5.2 paragraph "THE PUSH-DENIAL ENTRY BELOW ... SURVIVED THE RETIREMENT" are rewritten to record that the flag and the three verdicts were removed by plan `01reg8` (maintainer ruling 4h7tt0 OQ-02) because nothing consumed them, while the host REQUIREMENT line "deny push-capable network routes and withhold remote credentials" stays; the section 7 "MEASURED:" sentence drops `supports_deny_push`. Record it with `python3 -m agent_workflows specs note <spec path> --message "AMENDED 2026-09-24 (plan 01reg8, backlog aagh7v): ..."` (or the repo's current `aw specs note` form).
  - Depends on: E-06
  - Expected outcome: `rg -n "supports_deny_push" <spec>` returns only lines that describe the removal; the spec's `## Workflow history` gains one AMENDED line.
  - Execution state: pending

### Task group 4: after state and the suite

- [ ] E-08 Capture the AFTER state: `python3 -m agent_workflows host capabilities opencode` and a residual grep `rg -n "supports_deny_push|CAP_DENY_PUSH|ACTION_REVIEW\b|ACTION_MUTATE\b|ACTION_CONTRACTLESS_PROMPT" agent_workflows tests`.
  - Depends on: E-07
  - Expected outcome: no `supports_deny_push` row, only `ALLOWED  read_only`, and `1 host(s) reported; 0 (host, action) pair(s) refused`; the grep's only hits are `run_selection_policy`'s unrelated `ACTION_REVIEW` (its own lifecycle vocabulary, `pol.ACTION_REVIEW`) and E-02's negative assertions.
  - Execution state: pending
- [ ] E-09 Run the bare suite: `python3 -m pytest`.
  - Depends on: E-08
  - Expected outcome: no new failures relative to a baseline taken the same way at the start of execution.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Presence-based inference is forbidden (`host_sandbox_profile` module docstring, "WHY THE PROBE EXECUTES INSTEAD OF INSPECTING"); backlog `aagh7v` repeats it for this removal. Nothing here adds a probe.
- `tests/test_host_sandbox_profile.CONTRACT_FIELDS` (not dataclass introspection) drives the default-False and snapshot tests, so the field must be removed there too or the suite fails on a missing attribute.
- `tests/test_run_no_push_boundary.py`, which 4h7tt0 added to pin `CAP_DENY_PUSH`'s shape, no longer exists (deleted by the suite trim `19313eed`), so it is not in scope.
- `run_selection_policy.ACTION_REVIEW` is a DIFFERENT symbol (the lifecycle action vocabulary) and must not be touched.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `cfc7f5c1`.

| # | Site | Reference |
| --- | --- | --- |
| F-1 | `host_sandbox_profile` | field `supports_deny_push`, `CAP_DENY_PUSH`, `__all__`, `RUNNER_SAFETY_CAPABILITIES`, `_DECLARED_UNENFORCED`, `_RUNNER_SAFETY_PROBES`, and `CAP_DENY_PUSH` in the `review`/`mutate`/`contractless_prompt` requirement entries |
| F-2 | `host_cmd`, `cli.py` | prose only: "two capabilities that are DECLARED AND NEVER PROBED", "(commit gateway, push denial)", "four action classes" |
| F-3 | `run_evidence` | comment beside the retired `RUN-NO-PUSH` row: "that capability is deliberately LEFT IN PLACE" |
| F-4 | tests | `tests/test_host_sandbox_profile.CONTRACT_FIELDS`; `tests/test_host_capability_extension.py` imports plus nine uses of `CAP_DENY_PUSH` and the three action constants (the backlog's line numbers have drifted; re-measured by symbol above) |
| F-5 | spec `25kzda` | "carries 13 fields including the three runner-safety ones", "DELIBERATELY PRESERVED", "SURVIVED THE RETIREMENT", section 7 "MEASURED:" sentence; the packet example `"required_host_capabilities": [..., "deny_push"]` and the 5.2 host requirement list are spec vocabulary, not the flag |
| F-6 | consumers | `check_action_capabilities` is called outside its module only by `host_cmd._action_rows`; `preflight_host_capabilities` only by tests. No `docs/` page or `CHANGELOG.md` entry mentions the flag |

Current output (`aw host capabilities opencode`, trimmed): `NO   supports_deny_push (runner-safety)`, `REFUSED  review  missing: supports_commit_gateway, supports_deny_push` (same for `mutate`, `contractless_prompt`), `1 host(s) reported; 3 (host, action) pair(s) refused`.

## Proposed changes (ordered, validatable)

1. Failing regression test first (E-02).
2. Remove the flag (E-03), then the three requirement entries and constants (E-04), then the prose that describes them (E-05).
3. Re-point tests, keeping two-sided preflight coverage via a synthetic test-local action (E-06).
4. Amend spec `25kzda` so it no longer says the flag is preserved (E-07).
5. After-output, residual grep, bare suite (E-08, E-09).

## Deferred / out of scope (with reason)

- Removing `supports_commit_gateway`, which after this plan gates no action and is equally unenforced.
  - Carrier-Declined: the maintainer's ruling covers only `supports_deny_push`; see OQ-01, where the default is to keep it.
- Wiring `preflight_host_capabilities` into the runners.
  - Carrier-Declined: not requested; with only `read_only` represented it would refuse nothing, and real enforcement belongs to the OS-sandbox line of work, not to this cleanup.
- Editing spec `25kzda`'s packet example and 5.2 host-requirement list that name push denial.
  - Carrier-Declined: they describe what a HOST must prove, which stays true; only the Python flag is removed.

## Scope check

- Over-scope: none. The prose edits in `cli.py`/`host_cmd`/`run_evidence` only correct text that would otherwise describe removed code.
- Under-scope: none known; E-08's residual grep is the check.

## Required tests / validation

- E-02's `DenyPushRemovedTests` fails before and passes after.
- Targeted run of the three host test files passes, with the synthetic-action REFUSES/PROCEEDS pair still present.
- Before/after `aw host capabilities opencode` output pasted.
- Bare `python3 -m pytest` summary line pasted.

## Spec / documentation sync

Spec `25kzda` (`.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) is amended by E-07 and is listed in `- Scope-Paths:`. WHY: three of its paragraphs state that `supports_deny_push` is "DELIBERATELY PRESERVED" and that its refusal "SURVIVED THE RETIREMENT"; after this plan those sentences would describe code that no longer exists, and the 1106 paragraph itself names backlog `aagh7v` as the pending removal. No user-facing docs mention the flag (F-6).

## Open questions

### OQ-01: Should `supports_commit_gateway` be removed too, now that it gates no action?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: KEEP it. The 2026-09-10 ruling names only `supports_deny_push`, and the commit-gateway capability still has a probe note and a presence-vs-observation test row that document a real anti-inference rule. It will display `NO` but refuse nothing. If the maintainer wants it removed, that is a separate follow-up with the same shape as this plan.

### OQ-02: Remove the three requirement entries, or only drop `CAP_DENY_PUSH` from them?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Remove the entries. 4h7tt0 OQ-02's recorded answer lists "deletion of the `review`/`mutate`/`contractless_prompt` requirement entries that reference it", and dropping only the flag would leave the same three unconsumed `REFUSED` lines printed on `commit_gateway` alone, which is the exact misleading output the ruling targets.

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
  - Required evidence: paste the targeted run `python3 -m pytest tests/test_host_capability_extension.py tests/test_host_sandbox_profile.py tests/test_hostdedup_third_host.py -o addopts=""` summary with 0 failed, and `-k "REFUSES or PROCEEDS"` output showing both tests collected and passed.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `rg -n "supports_deny_push|DELIBERATELY PRESERVED|SURVIVED THE RETIREMENT" <spec>` showing only removal-describing lines, the new AMENDED workflow-history line, and `python3 -m agent_workflows specs check <spec>` (or `aw check`) passing.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste the full AFTER `python3 -m agent_workflows host capabilities opencode` output next to V-01's: no `supports_deny_push` row, only `ALLOWED  read_only`, final line `1 host(s) reported; 0 (host, action) pair(s) refused`; and the residual grep with every hit explained.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste the bare `python3 -m pytest` summary line, with the baseline summary line, and name any failure present in both.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `- Status: approved`. Commit only the Scope-Paths files through `aw commit 01reg8 -- <paths>`; never push. This is a removal of dead code at the maintainer's explicit direction; it is NOT licence to infer push prevention from any helper, hook or flag. After every V-* item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `executed/` via the lifecycle transition and set backlog `aagh7v` accordingly.
