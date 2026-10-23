# Review findings: plan di5puw

- Subject-Id: di5puw
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (MEDIUM, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `16d8abbb8`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 26), test-marker-only, two declared paths.

Verified at the lane HEAD:
- F-01: `bf5057b69` subject "remove classic report.html (run_analytics_spa + assets), keep its HTML-safety helpers as run_analytics_html", author date 2026-10-17 18:16:22; `f3afece9` (18:14:47) is its ancestor; `agent_workflows/run_analytics_spa.py` absent and untracked; `git grep` for the four defs exits 1.
- F-02: `run_analytics_html.scan_for_network_references` defined; `run_dashboard` calls `spa.scan_for_network_references(doc)`. `-m core --collect-only` over the two files collects only `FixtureCorpusTests::test_the_corpus_carries_all_four_generations_including_both_legacy_ones` of 51. Probe `--op raise ... -m core` over the two files: `verdict: survived`, `mutant_failing: 0`.
- F-03: probe `--op return-none` over the two named test ids: `verdict: killed`, `baseline_failing: 0`, newly failing both. Both tests call the scanner and assert on its returned list (behavioral).
- `tests/test_run_analytics_e2e.py` imports `pytest` and uses method-level `@pytest.mark.core`; `tests/test_run_dashboard.py` does not import `pytest` (E-03's conditional import applies).
- Bare `python3 -m pytest` before any change: `1675 passed, 11 warnings in 34.68s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Executability (validation would fail on correct work) | `tools/mutation_probe.py:231` `run_probe` docstring "against committed HEAD"; `:292` `git worktree add --detach ... HEAD` | E-04 ran the probe right after the uncommitted decorator edits, but the probe checks out committed HEAD, so it would report `survived` (measured: `raise` under `-m core` survives at HEAD) and V-04 could never pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now commits the two edits through `aw commit di5puw -- <paths>` first; V-04 demands `head:` equal to that commit. Added F-04. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (unsatisfiable or artifact-of-organization bars) | bare run at review `1675 passed, 11 warnings in 34.68s`; `conftest.py` budget block "Core tier wall time: ... exceeded budget of"; old E-04 "`mutant_failing: 2` naming the two tests" | "No budget breach" is already false before this change on this host, and `mutant_failing: 2` is a test-count bar (any other core test reaching the scanner changes it). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Bar is now `baseline_failing: 0`, `verdict: killed`, `newly_failing` naming at least one marked test; a wall-time overrun is reported, not treated as plan failure; the two tests' measured cost (0.31s) recorded in F-04. |
| PR-003 | LOW | IN-SCOPE | Evidence (command noise) | `grep -rnE ... agent_workflows/` at review printed "binary file matches" for `__pycache__/*.pyc` | E-01 demanded the `grep -r` print nothing; stale untracked bytecode makes it print. | all Low | FIXED | E-01 uses `git grep ... -- agent_workflows/` (exit 1, no output, measured). |
| PR-004 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | Gate lacked the paste-actual-output rule, the scope-fence declaration wording, the staged-set check, and conditional finalize ownership; it implied a hand move to `executed/`. Also no note on the mutating ruff hook (`.pre-commit-config.yaml` `ruff --fix`; `ruff check` already reports I001/RUF100 fixables in `tests/test_run_analytics_e2e.py`). | all Low | FIXED | Gate rewritten as a full execution contract; E-02 notes hook churn is recorded, not hand-edited. Required-tests diff check now covers `<base>..HEAD` and the worktree. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should V-04 treat the core-tier wall-time budget, already exceeded before this change on this host? | Report an overrun, do not fail the plan on it; bar the two marked tests' own cost | Keep "no budget breach" (unsatisfiable); drop the budget mention entirely (hides cost) | bare run `34.68s` at `16d8abbb8`; `conftest.py` budget enforcement block; sibling `btubm6` same rule | yes |
| D-2 | Is commit-before-probe acceptable given the probe reads HEAD? | Yes: commit through `aw commit` then probe | Use `--extra-test` (reads `COMMIT^:PATH`, wrong for an uncommitted file); hand-edit production (forbidden by the plan) | `tools/mutation_probe.py` `run_probe`; sibling `a5drqh` E-04 precedent | yes |
