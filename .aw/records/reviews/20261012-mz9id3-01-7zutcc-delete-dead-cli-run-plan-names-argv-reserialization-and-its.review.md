# Review: Delete dead cli._run_plan_names argv reserialization and its private normalizer loader

- Subject-Id: 7zutcc
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at lane HEAD `e4ea59ef8`. The plan was committed and unchanged, so the snapshot was skipped.
`aw ipd lint --phase author` reported `clean`, with one info finding (`IPD-Z602` on E-04).

All four E-01 facts reproduce:
- `_run_plan_names` matches only its `def` in `cli.py`.
- `cli._load_normalizer` is called only inside `_run_plan_names`. `ipd_lint` uses `_ce._load_normalizer()`,
  `check_engine.check_names` uses its module-local loader, and both tests use `ce._load_normalizer()`.
- `plan-names` appears in `cli.py` only in the two "awcmdsurf Order 05" comments and inside the deleted
  loader's body.
- No dynamic or mock reference to either name.

`importlib.util` is imported only locally. The block sits between the end of `_run_plans` and
`def _run_leaks_configure`, as stated. Baseline: the three normalizer tests give `46 passed`, and
`check plans names` exits 0.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Citation accuracy | `agent_workflows/check_engine.py` `_load_normalizer` docstring "mirroring cli.py:2890" | E-03/F-03 quoted the docstring only as "mirroring cli". The actual pointer is a bare offset that was already stale (the cli loader sits just above `def _run_plan_names`). E-03's grep for "mirroring cli" still matches. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and F-03 now quote the exact string. |
| PR-002 | LOW | IN-SCOPE | E. Verification completeness | `tests/test_cli.py:1299` `mock.patch.object(cli, "_install_one", ...)` pattern | E-01(4) was meant to catch mock-based references. The quoted-string alternatives already catch `patch.object(cli, "_load_normalizer")`, but attribute-style references (`cli._load_normalizer`) were not covered. E-01(3) also did not say that the normalizer-path hits inside the deleted body are expected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `cli\._run_plan_names` and `cli\._load_normalizer` alternatives to E-01(4). E-01/V-01 (3) now explain the expected hits. Added F-05 recording the review re-verification. |
| PR-003 | LOW | IN-SCOPE | G. Right-sizing (advisory `IPD-Z602`) | E-04 action text | E-04 read as several clauses. It is one concern (validate the deletion through existing behavioral surfaces). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded E-04 as one validation action. The advisory is cleared. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | The gate had no scope-fence declaration, no paste-actual-output rule, no conditional runner/executor finalize ownership, and no statement that no questions are open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is deleting `cli._load_normalizer` (beyond the backlog's literal wording) in scope? | Yes | Leave it as a second dead loader | F-02/F-05: its only caller is the deleted function. Private, unreachable code. | yes |
| D-2 | Does the CHANGELOG need an entry? | No | Add a "Removed" line | The `plan-names` verb removal is already recorded. These are private, unreachable helpers, with no user-visible change. | yes |
