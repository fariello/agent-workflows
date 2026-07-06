# 02 Execution plan (how the review runs)

- Mode: full release-review, continuous single pass (not phase-isolated).
- Subject: the agent-workflows framework itself (explicit-subject exception).
- Parallel audit lanes: NOT used. Rationale in 05-decisions.md (repo is small, familiar, and
  the reviewer authored much of it; serial is clearer and avoids coordination overhead).

## Per-section plan

1. Section 1 (done): inventory, principles, backlog, pending plans, version consistency.
2. Section 2: the four Python tools - correctness, security (subprocess use, no shell=True,
   redaction, denylist), edge cases, MEM/resource, LIVE surfaces. Bodies are prose (not code):
   check only for instructions that could cause an agent to take an unsafe action.
3. Section 3: tests - coverage of the tools, gaps, honesty of assertions.
4. Section 4: docs/specs/examples - README/ARCHITECTURE/CONTRIBUTING/index/DECISIONS accuracy vs.
   the actual framework; cold-start docs; the benchmark + a11y additions reflected everywhere.
5. Section 5: feature/usability/maintainability; per-principle adherence; cold-start verdict;
   all-eight-persona pass; TODO triage (expected empty).
6. Section 6: compatibility (Python 3.7+ claim vs. 3.14 features), packaging, CI, release
   discipline, cross-tool shim correctness.
7. Section 7: apply Fix Bar to findings.
8. Section 8: final ship review, eight-persona sign-off, pending-plans gate (expected clean),
   Go/No-Go, push plan.

## Focus areas (highest value for this repo)

- Tool correctness + safety (the only executable code).
- Doc accuracy (this repo's core value is honest docs; drift is the top risk).
- Version/consistency across manifest, shims, tools, docs.
- Python version-compat claims (3.7+ vs. actual 3.14-only syntax, e.g. `X | None`).
