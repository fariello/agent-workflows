# Assessment - documentation (agent-workflows)

- Run ID: 20260704-193843
- Date: 2026-07-04
- Concern: documentation (whole repository)
- IPD: `.agents/plans/pending/2026-07-04-assess-documentation.md`

Verdict: **needs work** for documentation.

The user-facing on-ramp (README, `index.md`) is accurate and current - it was maintained
during the D31-D37 builds. The internals doc (`ARCHITECTURE.md`) is materially stale: it
predates the seven-IPD roadmap, still teaches the removed per-concern command model, and
omits nine of the fifteen workflows. Because a maintainer is directed to ARCHITECTURE for
the design (CONTRIBUTING points there), this is a High-impact accuracy gap. All fixes are
Low Remediation Risk (docs only, no behavior change).

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| D-01 | High | Low | software-engineer | ARCHITECTURE describes the pre-D31 model (`/assess-performance`, `/assess-security` as separate commands sharing the harness). |
| D-02 | High | Low | novice | ARCHITECTURE's by-tool examples use `/assess-security`, which no longer exists. |
| D-03 | High | Low | software-engineer | ARCHITECTURE omits nine workflows (verify, advise, assess-all, spec, incident, release-notes, migrate, list-workflows, getting-started). |
| D-04 | High | Low | software-engineer | ARCHITECTURE file tree omits the new dirs, `VERSION`, `tests/`, and `run_checks.py`. |
| D-05 | Medium | Low | software-engineer | No mention of versioning (D32) or self-tests (D36). |
| D-06 | Medium | Low | operator | `run_checks.py` missing from the tools description. |

(Full set incl. Low findings in `findings.csv`.)

## Proposed plan (summary)

1. Rewrite ARCHITECTURE's assess section to the single `/assess <concern>` model; replace
   all `/assess-<concern>` command examples (D-01, D-02).
2. Add concise ARCHITECTURE sections for the nine missing workflows (D-03).
3. Update the ARCHITECTURE file tree to the current layout + VERSION + tests/ + tools (D-04).
4. Add versioning + self-tests subsections; add `run_checks.py` to the tools (D-05, D-06).
5. Generalize the CONTRIBUTING doc-sync step to cover advise personas (D-07).
6. Remove the stray `:Zone.Identifier` file (D-08).
7. Point users to the change history (README -> DECISIONS, or a new CHANGELOG) (D-09).

## Deferred (with reason)

None - all findings are Low Remediation Risk and proposed for action.

Next step: review the IPD (optionally run plan-review on it) and approve before execution.
This workflow does not execute the plan.
