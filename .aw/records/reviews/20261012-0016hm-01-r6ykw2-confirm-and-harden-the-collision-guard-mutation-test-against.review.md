# Review findings: plan r6ykw2

- Subject-Id: r6ykw2
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `6bac33183`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize --agent` both reported `clean`. `- Kind: child`.

Re-measured: the file runs `12 passed` at HEAD. `git diff bbf408eed HEAD --stat` on the test file shows `6 insertions(+)`, the `163874fcc` (psgyzw) `host_capabilities` hunk, which confirms F-3. Ten callers use `_drive_execute_turn`. The proposed guard was applied to SCRATCH copies only (`tests/_zz_r6ykw2_probe*_test.py`, deleted afterwards; `git status` clean): `12 passed` as written, and `7 failed, 5 passed` with the descriptor capability `False`, every failure being the named AssertionError and none a `KeyError`.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (negative control feasibility) | Review run: removing `host_capabilities` from the helper state, two drives -> `fail-gate True None` both times (reached verify; live probe did not refuse here) | E-02/V-02's negative control (remove `host_capabilities`) depends on the live host probe and, measured here, does not trigger the early return at all, so V-02's demanded AssertionError could not be produced. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The control now sets the descriptor's `supports_fresh_verifier_session` to `False`, which refused deterministically on both hosts (F-5). Updated E-02, V-02 and Required tests. |
| PR-002 | MEDIUM | IN-SCOPE | A (diagnostic correctness) | `runner_shared.record_refusal(it, ...)` -> `{'refusal': {...}}`; `item["worktree_error"]` is set on the item in `execute_item_core` | E-02 quoted `item.get("refusals")` (no such key) and listed `worktree_error` among ATTEMPT keys, so the diagnostic would print `None` for the very refusal it exists to name. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names `item["refusal"]` (singular) and `item["worktree_error"]`, with the attempt keys listed separately. |
| PR-003 | LOW | IN-SCOPE | E (guard robustness) | E-02 "assert `"verification_status" in item`" | A bare `assert` is stripped under `python -O`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires an explicit `raise AssertionError(...)` with a fixed message prefix. |
| PR-004 | LOW | IN-SCOPE | G (execution contract) | Gate paragraph; OQ-01 `Owner: maintainer` on an author deferral; E-01 hard-coded `12 passed` | The gate lacked the scope-fence declaration and the conditional finalize ownership. OQ-01 was labeled maintainer-owned. The test count was presented as the bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate, set the owner to `plan author`, and made E-01's bar "every test passes" with the count as context. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should the negative control induce a pre-verify early return? | Flip the frozen descriptor capability to `False`. | Remove `host_capabilities` (environment-dependent, measured not to refuse); monkeypatch `preflight_host_capabilities` (more invasive). | Review runs recorded in plan F-5. | yes |
