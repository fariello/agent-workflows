# 05 Decisions, assumptions, scope choices

## Scope
- D-S1: THIS repo is the subject (explicit-subject exception, 00-run-protocol.md:30). All of
  `.agents/workflows/`, the installer, tools, tests, shims, and root docs are in scope as
  ordinary project code. Confirmed by the user. `workflow-artifacts/` remains out of scope.

## Parallel audit lanes
- D-S2: NOT used. The repo is small (182 files), familiar, and the reviewer authored much of
  it; serial review is clearer and avoids lane-coordination overhead with no quality loss here.

## Assumptions / notes
- D-S3: Self-review caveat recorded in 00-run-metadata.md. Not an independent audit.
- D-S4: The 4 Python tools are the only executable code; workflow bodies are instruction PROSE.
  Prose is reviewed for accuracy/safety-of-instruction (Section 4), not unit-tested (per
  CONTRIBUTING: "prose is reviewed by /assess prose, not unit-tested"). This matches the
  project's stated testing philosophy; not a coverage gap.
- D-S5: Python 3.7+ claim - the tools use `X | None` annotations but all under
  `from __future__ import annotations` (stringized, safe on 3.7). No runtime 3.8+/3.9+/3.10+
  feature found (no walrus [the `[:=]` hit is a regex char class], no match, no f-string `=`,
  no runtime dict-merge, no removeprefix, no runtime subscripted builtins, no shell=True).
  The claim is plausibly accurate but is ASSERTED, not tested against a real 3.7 interpreter
  (only 3.14 available here). Recorded as a low-severity honesty note, not a blocker.
- D-S6: Downstream 27 repos are on 20260704-03; source is -05 (benchmark + a11y not rolled out).
  This is a deliberate, user-gated state ("Don't roll out yet"), NOT a defect.
