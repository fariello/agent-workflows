# Assessment - documentation (whole project)

Verdict: **adequate, needs work** for documentation honesty
IPD written: `.agents/plans/pending/20260711-1738-01-assess-documentation.md`

Run before a planned `/release-review`. Focus: does every forward-facing doc describe what the
software actually does today (P2), especially after D44-D50. No blocker-level false claims found;
drift is concentrated in tool-inventory counts, two shipped-but-unadvertised features, one
self-contradicting example, a Python-floor mismatch, and two self-conformance (dogfooding) gaps.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| D-1 | High | Low | novice | README:9 "two small Python helpers" - front-page undercount; 5 tools + package exist. |
| D-2 | Medium | Low | software-engineer | `normalize_plan_names.py` absent from README/ARCHITECTURE/CONTRIBUTING inventories. |
| D-3 | Medium | Low | stakeholder | This repo's `.agents/plans/` missing `superseded/`+`not-executed/` and the Category-1 READMEs (never re-ran its own install; violates its own D47/D49). |
| D-4 | Medium | Low | stakeholder | `index.md` stamp hard-codes `1.0.0` while HEAD is `v1.0.0-40` (the exact stale-value state D44/D50 warn against). |
| D-5 | Medium | Low | software-engineer | `assess.md:124-126` still shows the old `YYYY-MM-DD-assess-<concern>.md` IPD-name example, contradicting its own Step 0 + D48. |
| D-6 | Medium | Low | novice | `pyproject requires-python >=3.8` vs README "3.9+"; CI provisions only 3.9/3.13. |
| D-7 | Medium | Low | software-engineer | CONTRIBUTING self-tests list only 3 of 5+ tools; omits the full `tests/` suite. |
| D-8 | Low-Med | Low | novice | D49 self-documenting `.agents/` tree feature not mentioned in README/ARCHITECTURE. |
| D-9 | Low | Low | novice | README:98 "thirteen core" prose vs the 14-row core table (advise counted both ways). |
| D-10 | Low | Low | software-engineer | `scaffold.md` still shows `python3 install-workflows.py` rather than `aw`. |

## Proposed plan (summary)

1. Dogfood first: re-run `python3 -m agent_workflows install .` (creates the missing plan dirs +
   Category-1 READMEs) and refresh the version stamp (entangled with the release/bump decision).
2-9. Doc edits: fix the README front-page tool phrasing (count-free); add the normalizer to the
   inventories; fix the assess.md IPD-name example; reconcile the Python floor; refresh the
   CONTRIBUTING self-tests list; mention the directory-README feature; reconcile the core-workflow
   count; update scaffold examples.
10. DECISIONS D51.

All fixes Low Remediation Risk (doc edits + re-running the framework's own idempotent tooling).

## Deferred (with reason)

- The version bump / `v1.0.1` release itself: a RELEASE action, not a doc fix; Step 1's stamp
  refresh is entangled with it (Open Question 1). Sequencing choice, not a Remediation-Risk
  deferral; `/release-review` (running next) will handle release readiness.

## Out-of-concern note (routed onward, not in this IPD)

Pre-existing type issues in `agent_workflows/engine.py` surfaced during the read (a `Term(bool)`
call where a stream is expected, ~lines 734/935/1326/1454/1531/1613/2282, and a `None` default for a
`list[str]` param ~1607). These are CODE quality, not documentation, so they are out of scope for
this assessment. Flagged here so they reach the upcoming `/release-review` rather than being lost.

Next step: review the IPD (optionally run plan-review on it) and approve before execution. This
workflow does not execute the plan.
