# Review: Make the unreachable-binding perturbation test select a measured-unreachable predicate

- Subject-Id: 3tmt98
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at HEAD `11505c84b`; `aw ipd lint --phase author` clean before and after revision.

Claims re-measured: test currently hardcodes `worktree_lease.LeaseTable.held_by` and
`host_sandbox_profile.preflight_host_capabilities` (`tests/test_run_finding_reachability.py:141-197`,
`test_unreachable_binding_refusal_fires_under_perturbation`). Prover verdicts at HEAD: `LeaseTable.claim`
reachable, `held_by`/`owner_of`/`allocate_session`/`assert_worker_scope` unreachable, `release`/`snapshot`
reachable, preflight reachable. The `claim` local exists in `verifier_corroboration.match_claims_to_observed`
(`verifier_corroboration.py:630-660`); `rg '\.claim\('` finds only the stale docstring
(`run_evidence.py:1913`). `RUN-BASELINE-OWNERSHIP` verdicts: claim reachable, assert_worker_scope unreachable,
dirty_within reachable (F-05 holds: still bound via `dirty_within`, but the plan's parenthetical calling
`assert_worker_scope` reachable is wrong; it does not change the outcome). `validate_finding_table()` is
`ok=True`. E-03 negative control demonstrated: `git show 8c460a9a1^:tests/...` written to `/tmp`, run with
`-k perturbation` -> `1 failed, 4 deselected`; current file `5 passed`. `_validate_finding_row` refuses only
when no verdict equals `REACHABLE` (`run_evidence.py:2034-2042`), so `unresolved` candidates also satisfy the
refusal but must not be chosen as "reachable".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing (regression) | plan Required tests, V-04 | Bare-suite regression was demanded only inside V-04 (a docstring item) with no E-item and no recorded base failing set; E/V bijection hid it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 records the bare-suite base FAILED set; new E-05/V-05 compare node-id sets; V-04 reduced to the docstring diff. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing (determinism) | `vars(worktree_lease)` pool measured: dunders, namedtuple `_replace`/`__new__` report `unresolved`, `LeaseTable.__init__` reachable via generic name | E-02's candidate pool was unspecified beyond `vars()`, admitting dunders, private helpers and generated methods whose verdicts depend on generic names, re-introducing the coupling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now restricts to public `types.FunctionType` members whose `__module__` is the module; measured pool still yields both verdicts. |
| PR-003 | LOW | IN-SCOPE | G. Live-artifact bar | V-02 "`5 passed`", E-01 "5 passed" | Collected test count used as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to "every collected test passed; count is context". |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | plan gate | Gate lacked conditional runner/executor finalize ownership and `aw ipd begin`; stated "moves through lifecycle tooling" only. `self.fail` wording is wrong for a module-level helper. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added POST-GATE LIFECYCLE paragraph, Blocks-Release handoff note; helper raises `AssertionError`. |
| PR-006 | LOW | IN-SCOPE | Evidence accuracy | `predicate_verdicts_for('RUN-BASELINE-OWNERSHIP')` | Scope and F-05 called `assert_worker_scope` reachable; it is unreachable. Conclusion unchanged (`dirty_within` reachable). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected Scope OUT clause and F-05. |
| PR-005 | LOW | IN-SCOPE | D. Anti-regression | `run_evidence.py:1911-1914` | Replacement docstring could re-state a census fact as permanent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 requires the example be dated as a measurement. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which members may enter the selection pool? | Public plain functions defined in the module (incl. class methods) | All `vars()` callables; a hand-listed set | Measured verdict listing of `worktree_lease` at HEAD; `run_evidence.py:1940-1950` name-keyed resolution | yes |
| D-2 | Is the E-03 negative control reachable? | Yes, as written | Synthetic fixture | Demonstrated: `/tmp` copy `1 failed, 4 deselected` | yes |
