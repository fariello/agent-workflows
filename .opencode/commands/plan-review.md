---
description: Review and improve a proposed implementation plan before any code is written
agent: build
---

Read and execute @release-review/plan-review.md.

Treat that file as the controlling instruction. Review the proposed plan(s) the user
points you at (or, if unspecified, the project's pending-plan location discovered per
that file's Step 0) and then revise the plan(s) in place to be materially safer.

Apply the Fix Bar (`release-review/fix-decision-policy.md`): fix findings by default;
defer only when the Remediation Risk of the fix is Medium-High or higher (naming the
axis), never for effort/time. Review through the eight personas. Discover and conform
to the project's own guiding principles, contributor contract, plan format, stack, and
domain invariants rather than assuming any. Edit planning documents only - never
application code, tests, or config. Produce the table-first report defined in
`plan-review.md`, and do not mark the plan as executed.
