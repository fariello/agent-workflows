# Review findings: plan ellenm

- Subject-Id: ellenm
- Subject-Type: ipd
- Reviewed-At: 2026-10-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `cb23fb012`. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize --agent` was clean after revisions (one IPD-C801 advisory raised by a review edit was fixed).

Re-verified:
- The Set measurement command over `git ls-files 'agent_workflows/*.py' 'tools/*.py'` prints `UNRETIRED 88`: 41 `runner_shared.py`, 19 across the six Order 02 files, 27 across the 17 Order 03 files, 1 `tools/lost_guard_census.py` (`print_classifier` `mixed_example = "tests/test_dependency_verb.py"`).
- `python3 tools/lost_guard_census.py --dedupe` still reports shipped-source `Unowned: 44`.
- `aw find backlog test_lane_permission_posture` -> `no artifact matched selector`; `aw find` matches id6/status/Set/filename only.
- `aw backlog new` without `--apply` prints an advisory duplicate report; it flagged `mv18lz [graduated]` for an `InRunExecutedDependencyTests` summary.
- Live owners: `mv18lz` graduated (plan `df486j`), `yf1p8y` graduated (plan `z2ugxc`), `2ohbkj` open.
- `aw check --agent` exits 1 with 178 pre-existing findings and runs for minutes; `aw check backlog --agent` reports 3 (2 `check.name-nonconformant`, 1 `check.collisions-not-checked`) in about 5s.
- `9rthek` S-14 (`tests/test_lane_permission_posture.py`) is a known RETIRE-UNGUARDED candidate with no live owner.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Evidence / E. dedupe mechanism | E-03; `aw find backlog test_lane_permission_posture` -> `no artifact matched` | E-03's dedupe used `aw find backlog <basename>`, which is not a text search, so every group would read unowned and duplicate `mv18lz`/`yf1p8y`/`2ohbkj` could be filed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 dedupes with `rg -lwF` over live backlog and pending plans plus the dry-run duplicate report, with an owned-confirmed/rejected judgement; F-03 records the evidence; the Set's own plans and `iosmvn` never count as owners. |
| PR-002 | MEDIUM | IN-SCOPE | E. Evidence feasibility | E-03 "`aw check` reports no new errors" | Whole-repo `aw check` exits 1 on 178 pre-existing findings and takes minutes; "no new errors" had no baseline. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 captures `aw check backlog --agent` before and after; V-03 demands both. |
| PR-003 | MEDIUM | UNDER-SCOPE | G. Completeness | E-01 "any other line is ... reported" | An extra surviving line (child missed it, or a citation added later) was only reported, not carried, so it could be abandoned, which is the backlog item's exact failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 routes extra lines into a `RESIDUAL` group that E-02 lists and E-03 carries. |
| PR-004 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | E-01 "`UNRETIRED 1`"; E-02 "sum to the children's E-01 measurements" | The bar was a fixed count, and the reconciliation was ambiguous (a sum compared with what). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 bar is the property "only the census fixture survives"; E-02 compares each child's table to that child's own E-01 count and appends a grouped table with a Carrier column. |
| PR-005 | LOW | IN-SCOPE | G. Execution detail | E-03 `--set <short-setid>` | An unspecified setid invited ad-hoc or long setids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Setid defaults to the item's id6 (singleton, as `2ohbkj`); `bug` only with a cited user-perceptible defect. |
| PR-006 | LOW | UNDER-SCOPE | G. Execution contract | Approval and execution gate; OQ-01 `Owner: none` | The gate lacked the OQ status line, scope-fence wording, the MUST-paste rule, staged-set verification, conditional runner/manual finalize ownership, and the no-`git mv` rule; OQ-01 had no owner; closing `iosmvn` was unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to match siblings; owner `plan author`; deferral notes the runner's `process_backlog_close` path owns closing `iosmvn`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which `aw check` scope is the bar? | `aw check backlog --agent` before/after | Whole-repo `aw check` (178 pre-existing, slow) | Measured at `cb23fb012`; only backlog files are written | yes |
| D-2 | Setid for filed items? | Default singleton (item's own id6) | A shared new setid for all carriers | `2ohbkj` precedent; OQ-01 per-file grouping | yes |
| D-3 | What happens to an unexpected survivor? | Carry it as `RESIDUAL` and file a carrier | Edit source here (out of scope for a records-only plan); report only (abandons it) | Backlog `iosmvn` purpose "no dangling test citations are silently abandoned" | yes |
