# Review findings: plan y9m1ya

- Subject-Id: y9m1ya
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `383ebc1ee`. The plan was committed and byte-identical to the lane
input, so there was no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean` before review, and
`--phase review-finalize`: `clean` after revision. Not an orchestrator.

Premise re-verified in-process: `ACTION_CLASSES == ('read_only',)`, its `required == ()`,
`RUNNER_ACTION_TO_CONTRACT_ACTION == {}`, and `runner_action_contract_class` returns `None` for execute, review
and plan. `supports_fresh_verifier_session` is True for opencode, antigravity and scripted. `bqtgmo` is executed and
`ensure_frozen_host_capabilities` reads `state["host_capabilities"]`, which `initialize_run_core` writes. A
`darwin` descriptor reports False. Spec `25kzda` 5.2 rows "Plan/spec review or IPD authoring ... fresh verifier" and "IPD or contract
prompt mutation | All review capabilities plus ..." both exist. `aw opencode run --help` and `aw antigravity
run --help` exit 0.

DEMONSTRATION (the load-bearing measurement of this review): bare `python3 -m pytest` at base gave `6625 passed,
2 skipped, 3 warnings in 518.86s`. The same suite run with a pytest plugin that only adds an `execute` row requiring
`supports_fresh_verifier_session` and maps `execute` onto it gave `26 failed, 6599 passed, 2 skipped`. Wrapping
`preflight_host_capabilities` recorded zero refusals in the failing tests. Pre-seeding a frozen descriptor for
states lacking one made the 22 non-pin failures pass (`22 passed in 13.98s`, 27 states seeded).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric D/E (anti-regression) | `runner_shared.ensure_frozen_host_capabilities` (self-heal "measures once on demand"); `host_sandbox_profile` turn-argv capture `_oc.run_opencode(...)` / `_agy.run_agy_turn(...)`; failing tests e.g. `tests/test_oc_runipd.py::SelfFinalizeWiringTests::test_begin_precedes_run_opencode_on_success` (`['run', 'run'] != ['begin', 'run']`) | Activating the mapping makes 22 dispatch tests in six files outside Scope-Paths fail. Their hand-built states carry no frozen descriptor, so the self-healing probe runs the test's mocked launcher. The plan's "suite at or above baseline" demand was therefore unsatisfiable within its declared scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-08/V-08 seeds a frozen descriptor in the affected tests (mirroring production `initialize_run_core`), with the set re-derived at execution. Six test files were added to Scope-Paths, and the resumed-run self-heal residual is recorded. Added F-16. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (precision) | `execute_item_core` host-capability block `preflight_host_capabilities(contract_action, ...)`; `format_host_capability_finding(... action=action ...)` | The message interpolates the CONTRACT class value, not the runner action name, while E-02 left the value unspecified. Any value other than `"execute"` breaks E-05(d). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 fixes the value to `"execute"` and pastes the rendered message measured at review. Added F-17. |
| PR-003 | MEDIUM | UNDER-SCOPE | Rubric E (pins) | `tests/test_host_capability_extension.py` `DenyPushRemovedTests.test_supports_deny_push_and_unenforced_action_verdicts_removed`, `CheckerTests.test_an_unknown_action_raises_rather_than_defaulting`, `FailClosedPreflightTests.test_an_unknown_action_still_raises` | E-06 named only the requirement-map pins. Three more break, and two of them use `"execute"` as the example of an UNKNOWN action. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 re-points the DenyPush pins and retargets the unknown-action tests to a still-unknown name, preserving the `UnknownActionError` property. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (live-artifact baseline) | F-15 "3 failed, 4624 passed"; E-07(e) "fails the same way on the Set's base commit" | The authoring baseline is stale: the suite is now fully green, so E-07(e) demanded a failure that may no longer exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07(e) and F-15 now require re-derivation, with any new failure attributed to this plan. |
| PR-005 | LOW | UNDER-SCOPE | Rubric G (execution contract) | Original "Approval and execution gate" | The gate lacked the scope-fence-as-declaration wording and the conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE paragraph (justify with `--scope-reason`, keeping only the unsafe-condition stops) and conditional finalize ownership. |
| PR-006 | LOW | IN-SCOPE | Rubric G (consistency) | Proposed changes list (6 items for 7 E-items); "all six `V-*` items" | The plan's own counts drifted from its checklist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Proposed changes now list E-07 and E-08, and the gate says eight V-items. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Fix the 22 broken dispatch tests in the tests or in `ensure_frozen_host_capabilities`? | In the tests (seed a frozen descriptor) | Change self-healing to not probe; stub `ensure_frozen_host_capabilities` globally | Production `initialize_run_core` always writes `state["host_capabilities"]`; self-healing is `bqtgmo`'s executed design; demonstrated `22 passed` with seeding | yes |
| D-2 | What value should the new action class carry? | `"execute"` | `"mutate"` (deleted by `01reg8`), `"ipd_mutation"` | Message renders the contract class; E-05(d) requires "action `execute`" | yes |
