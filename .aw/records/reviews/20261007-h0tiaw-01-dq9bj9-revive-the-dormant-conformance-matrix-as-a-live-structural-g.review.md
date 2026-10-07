# Review findings: plan dq9bj9

- Subject-Id: dq9bj9
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `20cec6d24`. The plan was committed and byte-identical to the sealed lane input, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before review and
`--phase review-finalize --agent` was clean after revision.

Re-measured at review (no production edit):
- `build_matrix(_build_parser())`: `undeclared []`, `declared_absent []`, 1209 rows, 2.98s.
- `68sur3` and `lbbo9s` are both `done` (`.aw/records/backlog/done/`), closed through executed `gm9baj` and `7pnneh`.
- `config show --agent` rc 0 with a `result` record; `config get interactive --agent` and `config is interactive --agent` rc 2 with an `error` record and `exit: 2`.
- `tests/test_agent_surface_conformance.UNIVERSE` has 43 members and no `config` leaf (the leaves are still exempted).
- Alias pairs: `spec check`/`specs check` rc 0/0, byte-identical, 11.8s; `sanitize`/`check-local-leaks` rc 0/0, byte-identical, 36.4s.
- The recovered driver exists at `19313eed7^:tests/test_cli_conformance_matrix.py`; its `AliasEquivalenceTests` loops both pairs inside ONE test function.
- `tests/test_command_surface_declarations.py:21` imports `UNREACHABLE_COMMAND_ALLOW_SET, Exemption` from `tests.conformance_matrix` (added by `gm9baj`, commit `17801a40b`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Anti-regression / stale premise | `build_matrix(...).declared_absent == []` measured at review; `.aw/records/backlog/done/*68sur3*`, `*lbbo9s*` `Status: done`; plan E-04 "Pin the two-member set and name both id6s" | E-04 required pinning `{"prompts set", "upgrade-test"}` and citing two owners that are now closed. As written, the new test would land red, or the executor would pin members that no longer exist against closed ids. That is the same stale-citation defect E-02 removes from the registry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope, E-01, E-04, F-02, Deferred, Required tests, Proposed changes, V-04 and V-05 now pin the set re-measured at execution (expected `set()`), never pin a member whose owner is closed, and cross-reference the `gm9baj` reachability gate. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing / budget | the alias pairs measured 11.8s and 36.4s at review against the authored 2.8s and 12.2s; `conftest.py` `_DEFAULT_TEST_TIMEOUT = 90.0`; the recovered `AliasEquivalenceTests` uses one function with subTests | The measured cost is about 3x the authored cost, which puts the combined margin under 2x. A single looped test risks the hang timeout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now parametrizes one test per pair and records both measurements. OQ-02 notes that its rule is expected to fire for the `sanitize` pair. |
| PR-003 | MEDIUM | IN-SCOPE | G. Evidence currency | `tests/test_command_surface_declarations.py:21` imports `Exemption`; `tests/conformance_matrix.py` `build_matrix` comment "declared_absent is reported on MatrixReport but no longer asserted over" | The zero-importer premise is stale for `Exemption`, and E-04 makes a second in-module comment false. Neither was addressed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now notes the change and says to leave `gm9baj`'s `UNREACHABLE_COMMAND_ALLOW_SET` alone. It also requires correcting the `build_matrix` comment. |
| PR-004 | MEDIUM | IN-SCOPE | E. Probe validity | plan E-05 probe 2 "remove a declaration whose parser leaf still exists ... confirm the ... `declared_absent` assertion fails" | Removing a declaration whose leaf exists makes the leaf UNDECLARED. It does not make it declared-absent, so the probe as worded cannot exercise `declared_absent`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Probe 2's variant is now "add a throwaway declaration with no parser leaf". V-05 requires the failure to name it. |
| PR-005 | LOW | UNDER-SCOPE | C. Honest documentation | `command_surface.discover_parser_leaves` docstring "``AliasEquivalenceTests`` owns alias behavior" | Nothing tied the new alias class's name to the docstring that cites it. | all Low | FIXED | E-04 names the class `AliasEquivalenceTests` or E-06 corrects the docstring. V-06 quotes both. |
| PR-006 | LOW | UNDER-SCOPE | G. Execution contract | plan "Approval and execution gate" | The gate lacked the scope-fence declaration wording, the paste-actual-output rule, begin/finalize ownership and never-push. | all Low | FIXED | Added. OQ owners changed from `none` to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should the `declared_absent` pin be now that both members are gone? | Pin the execution-time set (expected empty), with the message naming the reachability gate | Keep the authored two-member pin; drop the assertion as redundant with `test_zero_unreachable_command_declarations` | `build_matrix` re-measured empty; the plan's own rule "do not replace it with an inequality" and GUIDING_PRINCIPLES 16 | yes |
| D-2 | How should the alias gate handle the budget? | Parametrize one case per pair and keep OQ-02's 3x rule | Mark it slow (forbidden by the plan); drop the `sanitize` pair now | Review timing of 11.8s/36.4s; `conftest.py` 90s budget | yes |
