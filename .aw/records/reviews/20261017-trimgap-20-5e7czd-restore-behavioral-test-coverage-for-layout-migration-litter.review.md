# Review findings: plan 5e7czd

- Subject-Id: 5e7czd
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 20), test-only, three declared paths, none present at HEAD.

Verified in the lane (scratch copies under `tests/zz5e_*.py`, removed afterwards; no production file edited; `git status` clean):
- `git show 19313eed^:tests/{test_layout_migration,test_awmigrename,test_storage}.py` restored to scratch paths: `71 passed in 7.69s` (49 + 9 + 13), matching F-02.
- All 7 named symbols exist: `layout_migration._grammar_facet_for`, `_apply_grammar_facet`, `is_stale_tool_litter`; `storage.load_local_attachment_record`, `get_git_commit_boundaries`, `move_companion`, `reattach_companion`. `is_stale_tool_litter` is also imported by name in `cli.py` (line 16960).
- Durations of the named tests: 0.12s, 0.07s (layout), 0.08s, 0.06s, 0.03s (storage), near 0 (awmigrename); 7 named tests ran `7 passed in 1.08s`.
- Mutation sweep by RUNTIME MONKEYPATCH (the review edits no production file; a driver replaced each function in every loaded module holding it, then ran pytest) against the NAMED core set only:
  - `is_stale_tool_litter` -> False: `1 failed, 1 passed`; -> True: `1 failed, 1 passed`.
  - `_apply_grammar_facet` -> input: `1 failed, 1 passed`.
  - `_grammar_facet_for` -> None: `2 passed` (SURVIVED). Whole `test_awmigrename.py`: `3 failed, 6 passed` (`test_records_subtypes_map_to_facets` and two integration tests). Named set plus `test_records_subtypes_map_to_facets`: `1 failed, 2 passed`, and the three together pass unmutated in 0.16s.
  - `move_companion`, `get_git_commit_boundaries`, `load_local_attachment_record`, `reattach_companion` -> None: each `1 failed, 2 passed`.
- Host has 12 CPUs (the core-budget enforcement threshold the plan cites); backlog `o58dro` exists.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Testing (Goal not met: a mutant survives the core set) | Goal "an early-return mutation of any of the 7 keys turns a routine test red"; `tests/test_awmigrename.py` (at `19313eed^`) `test_non_records_class_is_excluded` asserts only `assertIsNone`; measured `_grammar_facet_for` -> None: `2 passed` | The core set was chosen to EXECUTE every key, not to fail when one is broken. The only facet-resolution test in it expects `None`, so a mutant always returning `None` passes the routine gate. F-04's "3 failed" came from the whole file, not from the core set the Goal is about. V-02 would have exposed this at execution but given no remedy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 also marks `FacetResolutionTests.test_records_subtypes_map_to_facets` core (measured kill; near-zero cost). F-03, F-04, OQ-01, conventions, Required tests and V-02 updated from 7 to 8 tests. |
| PR-002 | MEDIUM | IN-SCOPE | Executability (stop directive; regression path) | RESTORE RULE "If a test fails at execution HEAD, STOP on it" | Same defect as in sibling plans: a stop instruction, plus a backlog filing outside Scope-Paths, with no instruction for the failing test. | all Low | FIXED | Replaced with a disposition rule: adjust the test with a cited commit, or file a gated `bug`, justify it with `--scope-reason`, mark the test `xfail(strict=True)`, and continue. |
| PR-003 | LOW | UNDER-SCOPE | Validation (mutation list incomplete) | Required tests mutation list; V-03 | `get_git_commit_boundaries` and `load_local_attachment_record` were in scope but had no required mutation, so the Goal was not checked for them. | all Low | FIXED | Both added (measured killed by the core set). |
| PR-004 | LOW | IN-SCOPE | Validation (mutation mechanics) | `cli.py:16960` `from agent_workflows.layout_migration import ... is_stale_tool_litter` | A monkeypatch of only `layout_migration.is_stale_tool_litter` leaves the CLI path calling the original, so an executor using a patch could misread a survivor. | all Low | FIXED | Required tests notes it: edit the source file, or patch both modules. |
| PR-005 | LOW | IN-SCOPE | Execution contract; live-count bars | gate paragraph; Expected outcomes "49 tests pass", "13 tests pass" | The gate lacked the honesty rule, the staged-set check, scope-fence wording and finalize ownership. The test counts were used as pass/fail bars, which a later edit to the restored file would invalidate. | all Low | FIXED | Gate rewritten. Bars now read "every restored test passes (N at review)" plus the exact named-marker set. V-02 and V-03 diffs now name their expected content. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to make the core set kill `_grammar_facet_for` -> None? | Add `test_records_subtypes_map_to_facets` to the core markers | Mark the whole `FacetResolutionTests` class; add one of the integration tests (slower, uses git subprocesses) | measured `1 failed, 2 passed` with it; 0.16s for the three | yes |
| D-2 | Handling of a restored test that fails at execution | Disposition rule (cited adjustment, or gated `bug` + `xfail(strict=True)`) | STOP; delete the test | AGENTS.md "Every live bug gates the next release"; plan-review scope-fence ruling 2026-09-01 | yes |
| D-3 | Keep the per-test marking choice (OQ-01)? | Keep | Mark files whole | `o58dro`; measured 7.69s for all 71 tests vs 1.08s for the named set | yes |
