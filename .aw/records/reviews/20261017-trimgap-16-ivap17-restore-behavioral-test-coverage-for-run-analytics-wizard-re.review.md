# Review findings: plan ivap17

- Subject-Id: ivap17
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `cfc742aef`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 16), test-only.

Verified in the lane (scratch restores of the six files and scratch production mutations, all removed or reverted; `git diff agent_workflows/` empty; `git status` clean apart from the plan and this record):
- None of the six Scope-Paths files exists at HEAD; all eight files named exist at `19313eed^`; every test the plan deletes or marks exists there with the stated class.
- Scratch restore applying E-01..E-05 literally: test counts 19, 23, 20, 14, 28, 21; explicit-path `125 passed in 2.71s`; `-m core` `79 passed, 46 deselected`.
- Per-function coverage JSON under `-m core`: all 22 keys have nonzero covered lines.
- Early-return sweep under `-m core` over all 22 keys: 20 killed; `prune_snapshots -> []` and `publish_snapshot -> None` SURVIVED (`79 passed`). Marking `SnapshotRetentionTests.test_snapshots_are_pruned_to_the_keep_count` and `test_a_snapshot_manifest_records_immutability` killed both.
- Bare `python3 -m pytest` with the scratch files present and six report tests marked: `834 passed in 26.61s`.
- E-04 literal result: `FIXTURE_TREE = Path(__file__)` remains (the E-04 `rg` would hit it) and `ruff check --select F` reports `import subprocess` unused.
- `aw sanitize --agent` reported `checked: 5835, findings: 0` both with and without the untracked scratch files, so it does not scan untracked files; `leak_sanitizer.scan_text` over each restored file returned no finding.
- Process note: an edit script aborted on a mismatched anchor before writing, after which `aw ipd set reviewed` was run on the unedited plan. The edits were then reapplied in full before this commit; the committed plan carries all revisions.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D. Coverage on the routine gate | `run_analytics_report.prune_snapshots`, `run_analytics_report.publish_snapshot`; review `-m core` sweep `79 passed` | The Goal says an early-return mutation of any key turns a ROUTINE test red. Under the four-test report marking, two keys' mutations survive. F-06 claimed every key was killed, apparently from a sweep run without `-m core`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 marks six tests. F-06 is corrected and F-07 added. Every mutation in Required tests and the V items now runs under `-m core`, and a `publish_snapshot` mutation was added. |
| PR-002 | MEDIUM | IN-SCOPE | Validation (check cannot pass) / lint | E-04 `rg -n "__file__\|...\|check-ignore"`; `FIXTURE_TREE = Path(__file__)`; `import subprocess` | The E-04 deletions leave `FIXTURE_TREE` and `import subprocess` unused, and the docstring mentions `check-ignore`. So the `rg` check can never return nothing, and the ruff pre-commit hook rejects or rewrites the file. | all Low | FIXED | E-04 deletes both definitions. The RESTORE RULE now requires removing anything left unused. The `rg` pattern is narrowed, and `ruff check --select F` is added to E-04, V-04 and Required tests. |
| PR-003 | MEDIUM | IN-SCOPE | Validation (evidence the command cannot produce) | E-05/V-05 `aw sanitize --agent` on an untracked file; Required tests Reach `--cov-report=term-missing` | `aw sanitize` scans tracked files only (measured), so before staging it proves nothing about the new files. `term-missing` reports lines, not functions, and writes an untracked `.coverage`. | all Low | FIXED | Sanitize now runs after staging, with `leak_sanitizer.scan_text` used before that. Reach uses the coverage JSON per-function report under `.aw/state/`. |
| PR-004 | MEDIUM | IN-SCOPE | Executability (stop directive) | RESTORE RULE "STOP on that test" | This is the same defect as the sibling plans: STOP plus an out-of-scope `bug` filing with no way to justify it. | all Low | FIXED | Replaced with the Set's disposition rule (cite and adjust, or gated `bug` + `xfail(strict=True)` + `--scope-reason`, then continue). |
| PR-005 | LOW | IN-SCOPE | Executability / live-artifact bar | E-01..E-05 Expected outcomes and V-items ("19", "23", "34", "28", "21", "79"); `pytestmark` placement | Collected test counts were used as the bar. The placement rule did not deal with the parenthesized multi-line imports in these files. | all Low | FIXED | The bar is now all-pass plus exact core selection, with counts kept as context. The rule now says to insert after the last complete import statement. |
| PR-006 | LOW | IN-SCOPE | Execution contract | gate paragraph | The gate had no honesty rule, no staged-set check, no scope-fence wording, and no conditional finalize ownership. | all Low | FIXED | Gate rewritten as an execution contract. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to make the two surviving report keys guarded on the routine gate? | Core-mark two existing restored tests (0.12s) | Add new tests; mark the whole report module (more budget) | Review mutation kills; bare run 26.61s of 30s | yes |
| D-2 | Keep the docstring prose that mentions `git check-ignore`? | Keep it, and narrow the `rg` to the quoted command form | Rewrite the restored docstring | RESTORE RULE "keep every other test body unchanged" | yes |
