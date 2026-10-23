# Review findings: plan avg8qv

- Subject-Id: avg8qv
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `623eb73cb`. The plan was committed and byte-identical to
the sealed lane input, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent`:
`clean` (one info, `IPD-Z602`); after revisions `--phase review-finalize --agent`: `clean` (same
info). Not an orchestrator.

Verified at review:
- `runner_shared.execute_item_core` calls `reconcile_disposition(repo, item, run_dir, exit_code,
  plan_repo=Path(work_dir) if work_dir else None)`; `reconcile_disposition` reads `plan_repo or repo`.
- `ipd_schema.read_readiness` normalizes to `READINESS_VALUES` or `None` and never raises.
- `queue_artifact_path` raises `DriverError` for an unresolvable entry; reading can raise `OSError`
  or `UnicodeDecodeError`.
- `run_analytics_attempts._label` maps `None`/`""` to `(not recorded)`; `view_experiment` docstring
  carries the quoted sentence; `ATTEMPT_FACTS_SCHEMA_VERSION = 2`; no `readiness` or
  `review_readiness` exists in `agent_workflows/`.
- Probe (stdin script, nothing written) driving `oc_runipd.execute_item` with the
  `tests/test_rereview_reviewed_plan.py` harness and `run_opencode` patched:
  `readiness go-pending-approval rereview False -> ('reviewed', 'reviewed')`;
  `readiness None rereview False -> ('reviewed', 'reviewed')`;
  `readiness None rereview True -> ('fail-gate', 'fail-gate')`.
- `aw check --json`: 0 errors, 2 warnings (`check.system-layout-missing`,
  `check.identity-absent-from-name` on spec `k3yx72`), so the check exits 1 before this plan runs.
- `aw research new ... --set revcost --slug runs-analyze-review-cost-report` dry run previews
  `.aw/records/research/20261023-revcost-01-<id6>-runs-analyze-review-cost-report.findings.md`,
  matched by the Scope-Paths glob (`ipd_lifecycle._scope_match` returned True for it and for both
  prompt locations).
- `.aw/.gitignore` ignores `records/research/INDEX.json` and `INDEX.md`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing | agent_workflows/runner_shared.py:38966 `reconcile_disposition` `if item.get("rereview"):` refusal `rereview-no-fresh-review`; tests/test_rereview_reviewed_plan.py:477 | E-02 told the executor to copy a RE-REVIEW test's pattern, yet case two (no Readiness line, expect `reviewed`) fails by design on a re-review item: the probe ended `fail-gate`. Following the plan literally produces an unsatisfiable test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires a fresh review item without `rereview`, a `to-review` plan with no Readiness, and cites the measured outcomes; F-08 added; V-02 demands the asserting lines. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness | agent_workflows/run_analytics_attempts.py:287 `_label`; plan E-01/E-03 | E-01 stores `None` for "review wrote no Readiness", but E-03 folded it into `""`, so it would read `(not recorded)` exactly like an older run that never recorded the key. Q8 could not tell a Readiness-less review from missing data. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 maps value / `absent` (key present, `None`) / `""` (key missing); E-04, E-05, E-06 and V-03/V-05/V-06 carry the distinction. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Testing | plan E-05, V-05; tests/test_run_analytics_review_cost.py:396 `query.run_query("attempts", ... group_by=..., metric=...)` | E-05 used non-existent `run_query` keyword names (`group_by=["readiness"], metrics=["cost"]`; the signature is `group_by: str or Sequence`, `metric: str`), did not test the new filter or the schema listing, and V-05's `-k` filter could hide regressions in the other tests of the file. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 uses real keywords, adds filter (c), header-and-row key (d), schema (e), keeps the 14-run shape; V-05 runs the whole file and quotes asserting lines. |
| PR-004 | MEDIUM | IN-SCOPE | G. Executability | agent_workflows/cli.py:1091 `_add_commit_flags` ("non-interactively it is a NO-OP"); plan E-09/E-10 | E-09's `aw prompts set ... --yes` commits nothing unattended, and E-10's commit instruction did not say the prompt MOVE (deleted `pending/` path plus added `executed/` path) must be committed, risking a half-recorded move. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09 passes `--no-commit` explicitly; E-10 names both sides of the move; V-09/V-10 demand both. |
| PR-005 | MEDIUM | IN-SCOPE | E. Verification | `aw check --json` at `623eb73cb`: 2 warnings, exit 1 | E-10's "all three pass" could not be met: `aw check` already exits 1 on two pre-existing warnings unrelated to this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-10/V-10 define pass as no error and no new warning against a baseline re-derived at execution; F-10 records the measurement. |
| PR-006 | MEDIUM | IN-SCOPE | G. Executability | plan E-08/E-10 depends-on; `.aw/.gitignore` `records/research/INDEX.json` | E-08 needed the test summary line that only E-10 produces while E-10 does not run until after E-08 and E-09 (circular), and V-08 demanded `aw research index --check`, which already fails on repo-wide drift and an untracked index. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 runs the named-file pytest itself; E-10 re-runs it and now depends on E-08; V-08 demands `aw research index` output plus `aw research find --id`. |
| PR-007 | LOW | UNDER-SCOPE | C. Traceability | `aw research set-outcome --help` ("the provenance link that lets a later reader tell research that changed a decision") | The findings document was never linked to the plan that consumed it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 runs `aw research set-outcome <id6> --to adopted --consumed-by avg8qv --apply`; V-08 checks `consumed-by`. |
| PR-008 | LOW | IN-SCOPE | E. Testing | plan E-10 command `-q` with `addopts=""`; AGENTS.md "Do NOT pass another `-q`" | The named-file command's `-q` risked hiding the summary line the plan asks to paste; E-01 did not state the turns that never reach the new line (spawn failure, interrupt, stop), nor that the read uses the same tree as `reconcile_disposition` and a local `ipd_schema` import like the module's other call sites; V-06's dash grep did not say how to restrict to added lines. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `-q` removed; E-01 states tree, import, exceptions (`UnicodeDecodeError` added) and unreached paths; V-06 gives the exact command. |
| PR-009 | LOW | IN-SCOPE | Spec / docs sync | `aw check` `check.plan-spec-link-missing` on this plan; E-06 docs table row "Experiment comparison" already exists at docs/run-analytics.md:174 | E-06 added a second, overlapping experiment row instead of amending the existing one, and the spec-sync section did not explain the advisory `From-Spec` nudge or the prompt-path prose citations left by the move. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 amends the existing row; spec-sync explains why no `From-Spec` and no runner-spec amendment; E-09 notes the two prose citations and why they stay. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should a review with no valid Readiness appear in the analysis? | A distinct `absent` label, separate from `(not recorded)` | Fold into `(not recorded)` (original plan); use `none` | `run_analytics_attempts._label` maps empty to `(not recorded)`; prompt okj4bg Section 3 Q8 asks for the outcome "if the run records it", which a Readiness-less review does record | yes |
| D-2 | Should `aw check` exit 0 be the E-10 bar? | No; no error and no new warning against a re-derived baseline | Require exit 0 (unsatisfiable); drop the check | Measured `aw check --json` at `623eb73cb`: 2 pre-existing warnings | yes |
| D-3 | Should the prompt move commit itself? | `--no-commit`; E-10's single path-scoped commit carries it | `--commit` (a second commit outside `aw commit avg8qv`) | `cli._add_commit_flags` docstring; AGENTS.md execution contract (`aw commit <plan> -- <paths>`) | yes |
| D-4 | Update the prose citations of the old prompt path in backlog i2i81x and spec k3yx72? | Leave them; out of the fence and the id6 still resolves | Edit both (scope expansion into a reviewed spec) | `grep -rln prompts/pending/20261018-revsteps-02-okj4bg` returned only those two | yes |
| D-5 | Add `- From-Spec: k3yx72`? | No | Add it to silence the info advisory | Plan graduated from backlog `i2i81x` (`- From-Backlog:`); k3yx72 cites the work only as a prerequisite (Section 13.2) | yes |
