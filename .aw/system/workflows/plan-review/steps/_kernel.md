# Plan Review Kernel

Review planning documents only. Do not change code, tests, runtime
configuration, infrastructure, or production data. Editing a plan is not
executing it.

This workflow shares these sibling policies:
- `../release-review/fix-decision-policy.md`
- `../release-review/00-run-protocol.md`

If either is absent, apply these rules from memory:
- Fix findings by default.
- Defer only when the fix itself has Medium-High or High Remediation Risk on
  complexity, usability, security, or functionality.
- Severity is for reporting only.
- Effort, time, cost, and tokens never justify deferring a review finding under the Fix Bar. This rule governs fixing versus deferring findings in the plan; it does not require running redundant or full-suite test commands during review.
- Review through QA/QC, testing/regression, UI/UX, architect, software
  engineer, power user, novice, and stakeholder views.
- Apply security as a mandatory cross-cutting lens.

## Verification scope

Verify claims by reading repository files first (source code, tests, specs, and records). When static reading cannot settle a blocking factual claim, you may run a narrow, fast targeted check (for example `pytest --collect-only`, or a single test file or `-k` filter with `--no-cov`). Avoid full-suite test runs, coverage sweeps (`--cov`), benchmarks, throwaway virtual environments or `pip install`, and ad-hoc `/tmp` probe plugins unless the plan depends on an unverified runtime failure that no narrower check can settle. Never repeat a full-suite run on an unchanged tree.

---
## Memory kernel
Re-read this before each step and before the final report:
1. Review plans only.
2. Verify claims from repository evidence (prefer static reading; keep any needed check narrow and fast).
3. Fix by default. Severity never decides.
4. Resolve open questions interactively when possible.
5. Never guess a human decision.
6. Preserve valid plan content and required structure.
7. Make at most two local commits. Never push.
8. The reviewed/not-reviewed enumeration is the literal final output.
9. A gate or interactive question MUST NOT assert or imply the verdict it precedes (readiness, approval, GO); it states what was found and asks what to do. The verdict is formed only from the reviewed work's evidence.
10. Review the plan's writing against `../../technical-writing/technical-writing.md`, and preserve meaning, obligations, and recorded evidence.

---
### 0.2 Discover controlling instructions
Read the applicable repository and directory-scoped instructions, guiding
principles, contributor rules, plan lifecycle, specification obligations, plan
templates, and the target plan.

Do not assume filenames.

If instructions conflict, use the project's precedence rules. If none resolve
the conflict, record an open question. Do not silently choose.
