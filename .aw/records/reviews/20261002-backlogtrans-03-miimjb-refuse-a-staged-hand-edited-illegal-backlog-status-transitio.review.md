# Review findings: plan miimjb

- Subject-Id: miimjb
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `fe2ee961c` in an isolated review lane. Plan committed and byte-identical to the sealed lane
input, so no pre-review snapshot. `aw ipd lint` clean before and after (one info-level `IPD-Z602` on E-05, see D-2).

Re-verified:
- `cc2m29` is in `.aw/records/plans/executed/`. `attention_contract.BACKLOG_TRANSITIONS` =
  `open -> {blocked, done, graduated, parked}`, `graduated -> {blocked, done, parked, open}`,
  `blocked -> {done, graduated, parked, open}`, `parked -> {blocked, open}`, `done -> {graduated, open}`;
  `backlog_transition_allowed` returns `new in BACKLOG_TRANSITIONS.get(old, frozenset())` (fail-closed).
- Premise: throwaway repo under `.aw/state/`, committed `done` item, thorough hand edit to parked/blocked/open/
  graduated staged as `R088`/`R087`/`R089`/`R086`; `check_commit_invariants` -> `[]` for all four.
  `check_commit_invariants` composes `check_status_untooled`, `check_release_gate_consistency`, `check_scope_drift`.
- Reused symbols resolve: `check_engine._git_capture`, `_blob_text`, `_status_meta`, `_read_item_id`,
  `_staged_backlog_done_items`, `check_status_untooled` call sites in the full sweep and `doctor.py`;
  `doctor._extract_record_id6` and the `"status-untooled" in rule` branch.
- Fence test files named in Required tests all exist; `test_check_commit_invariants_composition` exists.
- `.aw/records/backlog/README.md` has `## Legal status transitions` naming `BACKLOG_TRANSITIONS`.
- `aw check`: `check.ipd-uncarried-obligation` (error) on this plan before revision; none after.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | MEDIUM | IN-SCOPE | G. Traceability | `aw check` `check.ipd-uncarried-obligation`: "`Carrier-Evidence: .aw/records/plans/pending/20261001-backlogtrans-01-cc2m29-...` does not resolve" | Three Carrier-Evidence lines pointed at `pending/` for `cc2m29`, which has since executed; an error-severity repository finding. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Repointed all three to `executed/`; finding cleared. |
| PR-302 | LOW | IN-SCOPE | G. Open questions | `BACKLOG_TRANSITIONS['done'] == {graduated, open}` | OQ-01 was open conditional on whether the table refuses `done -> graduated`; the shipped table permits it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved from the shipped table; F-15/F-16 added; E-01 dependency wording and E-05 edge derivation updated. |
| PR-303 | LOW | IN-SCOPE | D. Invariant | `attention_contract.backlog_transition_allowed` fail-closed on unknown source | E-05(k) did not say why the out-of-vocabulary skip is load-bearing: consulting the fail-closed table first would refuse an unknown status, double-refusing `backlog.status-invalid`'s case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(k) now states the ordering requirement. |
| PR-304 | LOW | UNDER-SCOPE | G. Scope-Paths ownership | Scope-Paths `tests/test_check_engine_release_gate.py`; F-13 (fixture has no HEAD so the new rule emits nothing) | The declared composition-test strengthening lived only in Required tests, no E-item owned it, and an `assertIn` against the existing no-HEAD fixture could never fire. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now owns it, requiring a fixture case that actually yields the new finding. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Resolve OQ-01 or leave it to the maintainer? | Resolve from the shipped table | Leave open (rejected: its premise is conditional on a table that now exists and permits the edge) | `attention_contract.BACKLOG_TRANSITIONS`; executed `cc2m29` | yes |
| D-2 | Split E-05 per the info-level IPD-Z602 heuristic? | Keep one E-item | Split into separate refused/not-refused modules (rejected: one module, one rule under test, one V-item; splitting adds coordination without reducing risk) | E-05 text; V-05 | yes |
