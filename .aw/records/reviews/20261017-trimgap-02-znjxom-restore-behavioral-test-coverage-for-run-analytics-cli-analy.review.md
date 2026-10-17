# Review findings: plan znjxom

- Subject-Id: znjxom
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5c427b50c`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean` (1 info, `IPD-Z602`). Child plan (Set `trimgap`, Order 2), test-only.

Verified in the lane (scratch copies placed in `tests/` and removed; scratch production edits reverted with `git checkout`; `git status` clean apart from the plan and this record):
- Replay of `19313eed^:tests/test_run_analytics_cli.py` at HEAD: `3 failed, 76 passed in 18.65s`, same three failures as F-01; `--durations` shows the default-launcher test 6.19s and the truncation test 3.04s.
- `_code_only` is never called (F-04 confirmed). The deleted file's only `__file__`/`ast` use is the retired-pin test.
- E-02 values reproduced: `(2, 'error: conflicting output format flags: cannot combine --agent and --json\n')`; CacheError record `outcome cannot-run`, `next aw runs analyze --rebuild`; TTY stderr carries `Analyzing run 1/3:`, `\x1b[2K` and `Analyzed 3 run(s).`.
- E-03 values reproduced with `write_run(<repo>/.aw/records/runs, <run-id>)`: raw export writes `raw/<run-1>/state.json` and `raw/<run-2>/state.json`; with `_common_base` patched to return `None`, only `raw/state.json` survives. `_common_base([])` is `None`.
- V-01 spot-checks: dropping the `FILTERABLE_FIELDS` refusal in `parse_filters` fails 2 tests; writing the report inside `_analyze_path` fails 1 test.
- Coverage gap check: `rg` over `tests/` finds no surviving test asserting `FOUR exceptions` or that `aw runs --help` names `analyze`/`export`/`submit`, and no test decoding the report's `embedded-data` payload.
- Adjusted tests: removing only the `cldbus` block passes; relaxing `row_count` to `>=` passes (`row_count 214`, 107 distinct run ids for a 107-run corpus), and truncating `_render_report_html`'s `entries` to 20 fails it.
- Bare core tier: `753 passed in 22.97s` baseline; `829 passed in 24.76s` with the deleted module core-marked (not the 31.84s / 34.61s the author measured).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Anti-regression (unique guards dropped) | `agent_workflows/cli.py:297` ("Read-only, with FOUR exceptions, named rather than counted"); `run_analytics_cli._render_report_html` (`entries = query_mod._cache_entries(repo)`); deleted tests `test_runs_description_names_every_mutating_exception`, `test_the_raw_table_is_not_truncated_to_the_terminal_page_size` | E-01(c) dropped both `intended-change` tests outright, but each fails on ONE stale assertion while its remaining assertions guard an invariant no surviving test covers: the `aw runs` help naming every mutating verb, and the full corpus reaching the report's embedded payload. Review showed the adjusted truncation test kills a 20-row truncation mutation. Dropping them leaves the read-only help claim and the report truncation unguarded. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01(d) now restores both with minimal edits (remove the `cldbus` block; `row_count` `assertEqual` to `assertGreaterEqual`). F-02 and new F-09 record the evidence; Scope, Deferred, V-01 updated. |
| PR-002 | MEDIUM | IN-SCOPE | G. Live-artifact bar | E-01 Expected outcome "reports `86 passed`"; V-01 "all 86 E-01-era tests" | A collected test count was the pass bar. | all Low | FIXED | Bar is now zero failures plus name-set equality against the `gap` names and the two adjusted names; 88 kept as context. |
| PR-003 | MEDIUM | IN-SCOPE | Evidence (claim not reproducible) / OQ-01 basis | F-08; OQ-01 resolution; review bare run `753 passed in 22.97s` | OQ-01 rested on the core tier being over budget before this plan; review measured it within budget both with and without the module core-marked. The headroom is load-dependent, so the "already over budget" framing is not a standing fact. The decision (do not core-mark) still holds on the backlog remedy alone. | all Low | FIXED | F-08 now carries both measurements; OQ-01 rationale rewritten; Concern and Deferred entries no longer claim a standing overrun. |
| PR-004 | LOW | UNDER-SCOPE | E. Testing (suite hygiene) | `conftest.pytest_terminal_summary` (`exceeded {threshold:g}s and are not listed in tests/slow_allowlist.txt`) | Restoring the truncation test (about 3.2s) would add an unlisted slow-test warning. | all Low | FIXED | E-01 Expected outcome allowlists it; `tests/slow_allowlist.txt` added to Scope-Paths. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked the honesty rule, the staged-set check, scope-fence wording, a `.coverage` cleanup note, and conditional finalize ownership. | all Low | FIXED | Gate rewritten as an execution contract matching sibling `zhoul7`. |
| PR-006 | LOW | IN-SCOPE | Precision | Concern "lost 75 `gap`-classified test names"; OQ-01/OQ-02 `Owner: none` | The trim deleted 79 names (75 `gap`); resolved questions recorded no owner. | all Low | FIXED | Concern says 79 (75 `gap`); owners set to plan author. |

`aw ipd lint --phase review-finalize --agent`: `clean` (1 info, `IPD-Z602`).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Restore the two `intended-change` tests with minimal adjustments, or drop them as the author did? | Restore with minimal adjustments | Drop (loses two unique guards); rewrite them from scratch (needless churn) | F-09 probes; `rg` shows no surviving owner; backlog `n6h5eg` remedy "updating fixtures and schemas where analytics contracts evolved" | yes |
| D-2 | Keep OQ-01 (no core-marking) after its budget premise failed to reproduce? | Keep | Core-mark the module (fits today at 24.76s, but spends a load-dependent margin) | Backlog remedy asks for restoration only; F-08 two-sided measurement | yes |
