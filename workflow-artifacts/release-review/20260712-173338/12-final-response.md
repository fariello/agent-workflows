# Release Review - agent-workflows (RUN 20260712-173338)

Subject: the framework itself (explicit-subject exception, D43 precedent). Parallel read-only audit
(4 lanes) + serial synthesis/implementation. Nothing pushed.

## Completed actions

| ID | What was done | Files | Commit | Validation |
|----|---------------|-------|--------|------------|
| A1 | rc-aware version comparator: `_OURS_RE`+`Parsed.rc`+`_sort_key` handle `rcN`; `next_version_ok` guards unparseable published; 3 regression tests. Fixes a real crash (rc versions raised `ValueError` / reported `unknown`) that this session's `parse_describe` rc work had introduced a mismatch for. | versioning.py, test_versioning.py, test_pypi_links.py | 7f7d5c6 | 215 passed; rc compare/status/next_version_ok verified by repro |
| A2 | Fixed 8 `Term(<bool>)` misuse sites to `Term(color=False if no_color else None)`; stream is never a bool. Removes the long-standing pyright errors AND a latent `--no-color` crash. | engine.py | 7f7d5c6 | 215 passed; `Term(color=False).stream` not bool; `line()` no crash |
| A3 | ARCHITECTURE: shim count 16 -> 18; added `plan-review-long/` + `verify-execution/` to the workflow tree. | ARCHITECTURE.md | 7f7d5c6 | grep confirms 18 shims + both dirs |
| A4 | README: corrected core-workflow prose count and added `release-review-plan`/`plan-review-long`/`verify-execution` to the enumeration (16 rows). | README.md | 7f7d5c6 | prose matches the 16-row table |
| A5 | CI: install `build` in the unittest job so the packaging ship-vs-dev gate runs instead of self-skipping (it was running in no CI job). | .github/workflows/tests.yml | 7f7d5c6 | step added before self-tests |
| A6 | pyproject: added `Issues` + `Changelog` project.urls for the PyPI sidebar. | pyproject.toml | 7f7d5c6 | twine check PASSED |
| A7 | pyproject: dropped the deprecated `License :: OSI Approved` classifier (SPDX `license` expression retained; PEP 639). | pyproject.toml | 7f7d5c6 | twine check PASSED; wheel builds |

## Identified but not addressed

| ID | What was not done | Remediation Risk + axis | Reason | Recommended next step |
|----|-------------------|------------------------|--------|----------------------|
| A8 | Normalize ~18 older `executed/` plans from uppercase `Status: EXECUTED (...)` to lowercase `executed` (D52 vocab). | Low; functionality N/A | DEFER on P4: `executed/` plans are append-only history; rewriting closed records to fix cosmetics violates the honest-history principle. New plans already use the lowercase vocab. | Leave as-is (P4). Optionally a one-line note in D52. |
| A9 | Add a symlink-cycle guard to `discovery._scan_children` (recursive scan follows symlinks, no visited-set/depth cap). | Low; functionality | Real but low: the scanned roots are the user's own configured, non-adversarial paths; a cycle is an unusual local misconfig. Out of scope for this release. | Small follow-up IPD. |
| A10 | Rename the one `.agents/docs/roadmaps/` file to include the `-NN-` segment; add a roadmaps bucket README. | Low; usability | The roadmaps bucket's policy was explicitly deferred by the maintainer to a post-release discussion; the file is untracked. | Post-release roadmaps discussion. |
| CI-2 | Add a lint/type-check job to CI. | Low; maintainability | Non-blocking maintainability improvement; no correctness impact. | Follow-up CI PR. |

## Summary of changes
Seven Low-risk fixes across correctness (rc comparator), a latent UX crash (Term), doc accuracy
(shim/workflow counts), CI (packaging gate actually runs), and PyPI-publish polish (urls, classifier).
The rc-comparator fix is the highest value: it closes a self-inconsistency this session created
(`parse_describe` emitted rc versions the comparator could not consume) that would have crashed a
future rc release-review gate.

## Fix Bar summary
10 findings, all Low remediation risk. Fixed 7 (fix-by-default); deferred 3 with stated axes (P4
history; non-adversarial/out-of-scope; maintainer-deferred bucket) + 1 CI follow-up. No finding
silently dropped.

## Validations run (actual)
- `python -m pytest -q` -> **215 passed** (pre-fix 212; +3 rc regression tests).
- `tests/test_packaging.py` -> 5 passed (ship-vs-dev gate; wheel content verified).
- `python -m build --wheel` + `twine check` -> **PASSED** (metadata valid after the classifier/url changes).
- `aw plan-names` -> 0 to rename. em/en-dash sweep -> 0 across changed files.

## CI assessment
Packaging gate now executes in CI (A5). secret-scan sound. No auto-publish workflow (correct). Lint
job deferred (CI-2).

## Schema validation
N/A (no data schemas/migrations). The version string is the one structured contract; rc parsing/
ordering now correct and tested.

## Deprecated-code
None. Root `prompts/`+`docs/specs/` already consolidated into `.agents/docs/` earlier this session.

## Final bug/security/memory audit
Subprocess shell=False with `--` guards; no injection/traversal; config key-allowlist; no secrets.
Installer no-clobber + backup + fail-safe marker-merge + stage-not-commit. Short-lived CLI; no leaks.
Post-fix: rc no longer crashes; Term never gets a bool stream. Clean.

## TODO / pending-plans reconciliation
No TODO/backlog files, no code TODO/FIXME, no pending plans, no staged prompts. One untracked
roadmap-for-consideration doc (deferred bucket, A10). No in-scope pending work -> no pending-plans
block on GO.

## Guiding-principles adherence
Adherent across all 10; notably P4 HELD (declined to rewrite executed-plan history) and P8 improved
(reduced doc<->reality and emit<->consume drift). No violation introduced.

## Eight-persona sign-off
QA, testing, UI/UX, architect, engineer, power-user, novice, stakeholder: all sign off. Each
surfaced at least one finding (recorded in persona-review.md); all High/Medium items fixed.

## Self-documenting / cold-start
Adequate across intent/philosophy/architecture/decisions; improved by the ARCHITECTURE + README count
fixes and (this session) RELEASING.md + the docs bucket standard.

## Documentation / artifact updates
ARCHITECTURE, README, pyproject, CI updated. Run artifacts under
workflow-artifacts/release-review/20260712-173338/.

## Remaining risks
Low. The deferred items (A8-A10, CI-2) are cosmetic/maintainability/out-of-scope. One release nuance:
a real `v1.1.0` publish must be built from a CLEAN checkout of the `v1.1.0` tag (the current tree
resolves to `1.1.1.devN`).

## Push/no-push decision
21 commits ahead of origin (unpushed), plus a pending run-artifacts commit. No push performed;
awaiting the rung choice below.

## Restart recommendation
No restart needed. Fixes were bounded and validated; no late architectural discovery. Convergence
reached.

## Section 9 readiness
Ready for a rung choice. A candidate (rung B) or full release (rung C) must be cut from a clean
`v1.1.0` tag checkout. PyPI publish remains a separate credentialed step.

## RELEASE REVIEW DECISION
Recommendation: **GO** (CONDITIONAL on the release-build nuance below, not on any unfixed finding).
