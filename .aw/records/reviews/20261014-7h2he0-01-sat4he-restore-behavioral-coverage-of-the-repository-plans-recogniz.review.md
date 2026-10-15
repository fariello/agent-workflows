# Review findings: plan sat4he

- Subject-Id: sat4he
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`d24ba6308`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review; `--phase review-finalize` conforms after the revisions, and `--phase pre-transition` no longer reports `check.ipd-uncarried-obligation`.

Claims verified:

- `agent_workflows/plans.py` defines `PRE_TERMINAL` (with `auto-approved`), `RECOGNIZED`, `DIR_TERMINAL`, `LEGACY_MAP`, `LEGACY_GROUP`, `DISPOSITION_DIRS` (`pending, executed, superseded, not-executed, reusable, done`), `normalize_status` and `read_status`; the module docstring carries the cited "no live guard currently asserts this drift check directly" parenthetical.
- `normalize_status('AUTO-APPROVED') == 'auto-approved'`, `normalize_status('aproved') == 'legacy/unknown'`, `normalize_status('DONE') == 'executed'`; `read_status` returns `None` with no status line.
- `tests/test_plan_status.py` does not exist; `19313eed7^:tests/test_plan_status.py` holds the cited tests. `support.SOURCE_PLANS` resolves the repo plans tree; `livecorpus` is registered and deselected by `addopts`.
- Prototype of the planned checker on the live tree (recursive): 1537 plan files examined, 0 unrecognized, 0 mismatched, so the live tests pass on landing.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | G. Lifecycle gate | `aw ipd lint --phase pre-transition`: `check.ipd-uncarried-obligation: 3 obligation(s) name no durable carrier` | No Deferred row carried a carrier field, so the plan could not pass its own pre-transition gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to each row. |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Invariant coverage | `agent_workflows/plans_archive.py` module docstring "moving cold plans into monthly `YYYYMM/` shards INSIDE each terminal dir"; E-01 "each `*.md` file" (deleted test used flat `d.glob("*.md")`) | A flat glob silently exempts every sharded terminal plan from the guard once `aw plans archive` runs, the exact population the terminal/directory rule exists for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now scans recursively with `rglob`, mismatch keys on the top-level dir, and a sharded-mismatch synthetic case was added. |
| PR-003 | LOW | IN-SCOPE | E. Non-vacuity | E-02 "at least one plan file was examined" vs `status_drift` returning only two lists | The checker's signature could not express the examined-count assertion E-02 demands. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `status_drift` now returns `(examined, unrecognized, mismatched)`. A file already counted as unrecognized is not repeated as mismatched. A synthetic test asserts the count. |
| PR-004 | LOW | IN-SCOPE | E. Test robustness | E-01 "`support.declare_execution_role(self)` ... if the existing plan-tree tests do so"; V-01 `grep "plans\.py"` | A conditional instruction left a choice to the executor, although the checker is read-only. The `grep` pattern would also match a legitimate docstring mention. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Role declaration is now explicitly not used. The pattern is narrowed to actual source-reading forms. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; Scope-Paths; OQ-01/OQ-02 `Owner: none` | The gate lacked the scope fence, `aw ipd begin`, conditional finalize ownership, never-tag, and a red-live-test stop. The plan file was missing from Scope-Paths, and the owners were placeholders. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract and the plan path. Owners set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Scan shards recursively or keep the deleted test's flat glob? | Recursive `rglob` | Flat glob (exempts sharded plans) | `agent_workflows/plans_archive.py` docstring; manifest scan is recursive per the same docstring | yes |
| D-2 | Carry the deferred rows as backlog items or decline them? | `Carrier-Declined` with reason | File new backlog items | Backlog `7h2he0` names only S-19 | yes |
| D-3 | Accept OQ-01 (`livecorpus`) and OQ-02 (recreate path)? | Yes, as authored | Default-suite live test; new module name | `pyproject.toml` `livecorpus` marker text; `DECISIONS.md` cites the path | yes |
