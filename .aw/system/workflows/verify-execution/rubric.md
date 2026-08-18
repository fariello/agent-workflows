# Execution Fidelity Rubric & Failure Signature Catalog

Treat this file as the controlling instruction for RATING the fidelity of a completed execution,
using the evidence gathered by `intent-audit.md`. It is loaded by `verify-execution.md` (Step 4).
It assigns a `FIDELITY_*` level and MAPS that level onto the workflow's existing verdict
(MATCHES / DIVERGES / INCOMPLETE) and the D65 corrective-IPD status rule; it does not replace them.

## Fidelity levels

Assign exactly one, based on the aggregate of the five audit dimensions:

- `FIDELITY_EXEMPLARY` - every explicit requirement done; intent/spirit honored; validation re-run
  and genuinely green (or the only red is a pre-existing baseline this execution did not own); no
  scope violations; artifacts/conventions conform. No corrective action.
- `FIDELITY_SURFACE_ONLY` - the requirements were touched at the letter but the intent is defeated
  (a failure signature below is present: e.g. an assertion deleted, an exception swallowed, a stub
  returning the expected value). Treated as a real gap even if tests "pass".
- `FIDELITY_PARTIAL` - some required changes are missing or incomplete, but what landed is faithful.
- `FIDELITY_UNVERIFIED` - the change may be correct, but the empirical validation was not actually
  re-run / its output was not captured, so success is unproven (Dimension 3 not satisfied).
- `FIDELITY_DIVERGED` - the work differs from the plan (over-scope, a different implementation, or a
  behavior-affecting change the plan did not authorize), whether or not it is independently correct.

## Mapping to the verdict (MATCHES / DIVERGES / INCOMPLETE)

The `FIDELITY_*` level is an additional diagnostic dimension; the workflow's VERDICT is still one of
the three existing values, assigned as follows:

- `FIDELITY_EXEMPLARY` -> verdict MATCHES, readiness GO.
- `FIDELITY_DIVERGED` -> verdict DIVERGES, readiness NO-GO.
- `FIDELITY_PARTIAL` or `FIDELITY_SURFACE_ONLY` or `FIDELITY_UNVERIFIED` -> verdict INCOMPLETE,
  readiness NO-GO (a surface-only or unverified execution is a false completion; it is not GO).

This preserves the existing verdict vocabulary and its GO-only-on-genuine-green rule.

## Mapping to the corrective-IPD status (D65, unchanged)

When the verdict is DIVERGES or INCOMPLETE, emit ONE corrective IPD into `.aw/records/plans/pending/`
per `verify-execution.md`. Its born status follows the EXISTING D65 rule, judged by COMPLEXITY/risk,
not by the fidelity label:

- born `auto-approved` only when the correction is fully specified, has zero open questions,
  corrects already-reviewed work, and is LOW-COMPLEXITY/low-risk (add the
  `auto-approved by /verify-execution <date>; not human-reviewed` Approval line + a rationale in
  Workflow history);
- otherwise born `to-review`;
- `auto-approved` is set by THIS checker, never by an executor fast-tracking its own work; an
  `auto-approved` plan still must pass its stated validation before being marked `executed` (D64).

The fidelity level does not override this: a `FIDELITY_SURFACE_ONLY` finding whose fix is a small
risky change to critical logic is still born `to-review`; a `FIDELITY_PARTIAL` gap whose fix is a
large mechanical sweep can be `auto-approved`.

## Failure signature catalog (false-completion patterns)

Concrete patterns that mark `FIDELITY_SURFACE_ONLY` (or worse) even when a checkbox is ticked or a
suite is green. Quote the `path:line` when found:

- Swallowed exception: `except Exception: pass` (or `except: pass`) that hides the real failure.
- Silent fallback: a bare fallback/default that masks a missing implementation ("return None on any
  error").
- Empty or no-op mock return: a mock/stub returning the exact expected value so a test passes
  without exercising real behavior.
- Deleted or weakened assertion: an assertion removed, loosened (`assertTrue(True)`), or an expected
  value edited to match wrong output, to make a test pass.
- Stubbed-to-pass function: a function that returns the literal expected result instead of computing
  it.
- Always-true / always-false guard: a guard clause or feature flag hard-wired so the new code path
  never actually runs.
- Skipped/xfail smuggling: a failing test quietly marked skipped/expected-fail rather than fixed.
- Un-run validation reported green: a "tests pass"/"lint clean" claim with no captured real output
  (maps to `FIDELITY_UNVERIFIED`).
- Scope leak: files changed/committed outside the plan's scope fence, or a bare `git add -A` sweep.
- Hand-edited generated artifact: a file that a tool owns (generated shim, regenerated index) edited
  by hand instead of regenerated.

A catalog hit is EVIDENCE, quoted with `path:line`; it is not an accusation without the quote.
