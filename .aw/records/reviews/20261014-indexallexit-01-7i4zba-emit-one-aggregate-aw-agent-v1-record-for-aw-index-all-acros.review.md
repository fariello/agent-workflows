# Review findings: plan 7i4zba

- Subject-Id: 7i4zba
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `de5c53233` in an isolated review lane. The plan was committed and unchanged (`5b91dc5a3`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` was clean after revisions (two `IPD-C801` info hits on `README.md:1`, which is an expected output value in E-03 and not a citation).

Re-verified by running the CLI against temp fixtures built with `tests.test_index_check_agent_records._create_fixture_repo`:
- `index all --check --agent` on a fixture with only `plans/INDEX.md` stale: rc 1, three lines with exits 1, 0, 0; the last line reads `conforms`. F-02 is reproduced.
- `index all --json` on a missing-index fixture: `json.loads` raises `Extra data`. F-03 is reproduced.
- Mixed write (`_write(..., status="bogus-status")` under `.agents/docs/research`): rc 1, three lines with exits 0, 0, 1. F-01 is reproduced. Editing the `_create_fixture_repo` research file to a bogus status did NOT refuse (rc 0, research index written).
- Unflagged `index all` stdout is byte-identical to the concatenated three single-type runs.
- `README.md` citing `RSCH-zzzzzz`: single-type `index research --check --agent` gives location `README.md:1` only via `data["repo_root"]`. Without the root, `normalize_repo_path` returns `<tmpdir>/README.md:1`. F-04 is confirmed.
- A hand-built aggregate `CommandResult(target="all", ...)` passes `agent_schema.validate_agent_record`, and `to_dict()` round-trips through `json`.
- `python3 -m agent_workflows check all --agent` on the live tree exits 1 at base (40 errors).
- `CHANGELOG.md` has no `[Unreleased]` or `### Fixed`. Fixes use `- Fixed:` bullets under `## 2.0.0 (pending)`.
- `command_surface` declares `agent_record_kind="result"` for `index`; `vfqjc0` is executed; `aw index` has no `--quiet`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Verification (unsatisfiable demand) | `python3 -m agent_workflows check all --agent` at `de5c53233`: exit 1, 40 errors (`check.lifecycle-transition-unvalidated` etc.) | E-05/V-05 required `check all` to exit 0 and the full suite to have "zero errors". The live corpus already fails, so a correct execution could not pass V-05. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 now require a base-commit comparison (no new rule id or increased count; no new suite failure), and the baseline is re-derived at execution time. |
| PR-002 | MEDIUM | IN-SCOPE | G. Executability (stale target) | `CHANGELOG.md` heading `## 2.0.0 (pending)`; no `## [Unreleased]`/`### Fixed` | E-05, the proposed changes, and V-05 named a section that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Retargeted to one `- Fixed:` bullet under the pending release heading, matching recent entries. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness (exit parity) | `plans_index.run_index` / `prompts_index.run_index` / `research_index.run_index` `not getattr(args, "quiet", False)` guard | A machine-mode backend that returns without reaching the sink would leave the aggregate `exit` below the process `rc`. This is unreachable today because `aw index` has no `--quiet`, but nothing prevents it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `aggregate_index_results` takes `rc`; `exit_code = max([rc, *per-type])`. Added F-05. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Testing (fixture feasibility) | `tests/test_index_write_agent_records.test_refusal_research_invalid_frontmatter`; review probe | E-04(c) did not say how to build the mixed-outcome fixture, and the obvious route (editing the fixture's research file) does not trigger the refusal. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04(c) names the measured fixture recipe and adds assertions for 4 changes and that the research index is not written. E-03(b) names the partial-stale recipe. |
| PR-005 | MEDIUM | UNDER-SCOPE | D. Anti-regression (invariant map) | E-01 normalization; `research_index.check_drift` `f"{d.file}:{d.line}"` | F-04 normalization had no test; human invariance had no oracle; the plan had no invariant-to-test map. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-03(d) (`README.md:1` location, no root leak), a concatenated-single-type oracle for E-03(c)/E-04(d), schema validation per line, and an invariant-to-test map. |
| PR-006 | MEDIUM | UNDER-SCOPE | G. Verification checklist strength | V-01, V-02 | V-01/V-02 demanded only diffs, which cannot show that the aggregate behaves correctly. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 adds a direct `aggregate_index_results` call with schema validation. V-02 adds a fixture CLI run whose path is `cli._run_noun_verb`. V-03/V-04 demand `-o addopts="" -v` output and the pinned behaviors, with test names as pointers only. |
| PR-007 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status, the paste-output honesty rule, `aw ipd begin`, path-scoped `aw commit`/never-push, a scope fence, and runner-conditional finalize. It also told the executor to always run `aw ipd finalize`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate with all of those elements, with finalize conditional on runner versus hand execution. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Replace the `check all` exit-0 bar with what? | Base-commit comparison of per-rule counts, plus no new suite failure | Keep exit 0 (unsatisfiable); drop the check entirely (loses regression signal) | live `check all --agent` exit 1 at `de5c53233` | yes |
| D-2 | Prefix aggregated diagnostic locations with the type's dir so three `INDEX.json` locations are distinct? | No; carry per-type locations unchanged | Rewrite locations to `.aw/records/<type>/INDEX.json` (changes a value consumers of single-type output already see, and the backends own those strings) | Owning type is in each diagnostic's `detail`/`fix` (`run 'aw index plans'`) and in `data["by_type"]`; probe output | yes |
| D-3 | Guard the unreachable no-sink return path? | Pass `rc` into the aggregator | Leave it (latent parity hole); force the sink in every backend return (touches three out-of-scope modules) | `run_index` `quiet` guards; `aw index --help` has no `--quiet` | yes |
