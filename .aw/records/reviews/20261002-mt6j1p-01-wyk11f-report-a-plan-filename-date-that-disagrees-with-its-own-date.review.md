# Review findings: plan wyk11f

- Subject-Id: wyk11f
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `dc53b1918` (corpus measured at `9ccffaca3`, plans tree unchanged between them except
the wdyz5n review). The plan was committed and byte-identical to the lane input, so no pre-review snapshot
was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize`
was clean after revision.

Re-verified:
- Corpus scan via `check_engine._iter_type_files` + `artifact_naming.parse_clustered` + `_CARRIER_DATE_RE`:
  default walk `files 149 clustered 149 nodate 0 DIS 0`; `include_retired=True` walk
  `files 1313 clustered 1309 nodate 1 DIS 0`. F-03's zero holds; its population is the `--all` walk.
- Baseline exit codes: `aw check plans` rc 1, `aw check plans --all` rc 1 (pre-existing findings).
- `check_content` plans branch carries `check_ipd_dependencies`, `check_plan_priority`, `check_plan_work_kind`,
  `check_plan_priority_required` in `try/except`; `check_plan_work_kind` signature and `enrich_drift` shape match.
- `artifact_naming.parse_clustered` (closed facet) and `parse_uniform_permissive` exist as described.
- `_DEFAULT_RULESPEC = RuleSpec("error", ...)`; `check.lifecycle-placement-conflict` empty-invariant comment present.
- `carrier_severity_for_plan` docstring quote and `junk_names`/SUBSUMES comment verified in `check_engine`.
  The "NO CUTOVER IS CONSULTED, DELIBERATELY" block is in `config.py:2237`, not `check_engine`.
- `plans_refs._preserved_date` reads the filename first, as F-06 states.
- Spec `agents-artifact-organization` 4.2 quote verified; 4.3 says regroup "renames the chosen files to share the set's date".
- `docs/cli-output-contract.md` 3.1 quotes and the `check.scope-drift` example verified.
- Backlog `mt6j1p` is `graduated`, no `Blocks-Release`; `tf4jz5` carrier plan `j7dsci` exists in pending.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Testing / G. Executability | `agent_workflows/check_engine.py:1119` `_iter_type_files` `if not include_retired and is_retired(...)`; `cli.py:13223` `include_retired = bool(getattr(args, "all", False))` | E-04/V-04 treated "zero over 1198" as what `aw check plans` measures, but the default walk sees only 149 live plans; the full corpus is reached only with `--all`. The evidence would silently describe a different population. | all Low | FIXED | E-04/V-04/validation now run default and `--all`, label each population, and require equal exit codes (rc 1 baseline). E-02 must pass `include_retired` through. |
| PR-002 | MEDIUM | UNDER-SCOPE | E. Testing | E-01 rows; V-01 "paste the count of plans the engine examined" | No test proved the wiring into `check_content` (only a diff), no test pinned the no-date skip or retired reach, and the examined-count demand had no producing mechanism. | all Low | FIXED | E-01 adds no-date, retired-reach, entry-point rows and a non-vacuity control via `check_plan_work_kind`; V-01/V-02 updated. |
| PR-003 | MEDIUM | IN-SCOPE | Spec sync | `.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md:115` Section 4.3 | Spec sync reasoned only from 4.2; 4.3 states regroup renames files "to share the set's date", which an executor could read as the plan's stop condition. | all Low | FIXED | Spec sync explains 4.3 is intent not implemented (F-06), rule is `info`, and does not trigger the stop; no amendment. |
| PR-004 | LOW | IN-SCOPE | Evidence | `agent_workflows/config.py:2237` "NO CUTOVER IS CONSULTED, DELIBERATELY" | F-11 attributed the block to `check_engine`. | all Low | FIXED | Attribution corrected to `config.py` in both places. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | Spec / documentation sync last paragraph "stop, add the file" | A stop directive for a scope widening contradicts the plan's own scope fence and the 2026-09-01 ruling. | all Low | FIXED | Reworded to make the edit and justify with `--scope-reason`. |
| PR-006 | LOW | IN-SCOPE | C. Duplicate path | `check_engine._plan_date_compact`, `_CARRIER_DATE_RE` | E-02 did not name which body-date parser to use, inviting a third date regex. | all Low | FIXED | E-02 requires `_plan_date_compact`; signature mirrors `check_plan_work_kind`. Typo "plains" fixed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the rule reach retired plans by default rather than only under `--all`? | No; follow the neighbour convention (`--all` only) | Force `include_retired=True` for this rule | `check_plan_work_kind` and siblings pass the flags through; retired plans are not where a new disagreement enters | yes |
| D-2 | Does spec 4.3's "share the set's date" require an amendment? | No | Amend 4.3 in this plan | F-06 measured regroup preserves dates; rule is `info`; finding would be true anyway | yes |
