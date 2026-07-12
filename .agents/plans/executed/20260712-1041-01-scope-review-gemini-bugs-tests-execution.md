# IPD: Scope-review Gemini's assess-bugs + assess-tests execution (over-scope rewrite of scan_secrets)

- Date: 2026-07-12
- Concern: scope discipline / over-scope (P6 KISS, P8 single-source). Cross-checking Gemini's
  execution of `20260712-0959-01-assess-bugs-in-scripts` + `20260712-1005-01-assess-tests` (commit
  57b2ae3) found the four targeted bugs correctly fixed, BUT the same commit performed a large
  UNREQUESTED refactor of `scan_secrets.py` (and substantial `run_checks.py` changes) far beyond what
  the reviewed-and-approved plans authorized. This IPD records the divergence and decides what to do
  about it.
- Scope: assessment/decision + (pending the OQ) either accept-and-document or trim the over-scope.
  No code is changed by THIS IPD directly (Gemini may still be editing; and the /verify-execution
  contract is emit-a-corrective-IPD, not fix-in-place).
- Status: executed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): produced by a manual /verify-execution
  cross-check (the workflow itself is proposed in 20260712-1031-01, not yet built) of commit 57b2ae3.
- 2026-07-12 executed (Antigravity/Gemini): Executed Option 3 (SPLIT). Reverted the over-scope scan_secrets refactors back to the minimal approved bug fixes, and created a new pending IPD for the line-offset refactor.

## Verify-execution verdict: DIVERGES (over-scope). NO-GO on "truly executed as approved".

The four bug fixes are CORRECT and match the reviewed plans; but the execution is not faithful to the
approved scope. Do not treat 0959-01 as cleanly executed until the over-scope is accepted or trimmed.

### What was done CORRECTLY (verified against the diff; do NOT redo)

- BUG-01 (run_checks.py): the dead `and False` term is gone, reduced to
  `"unclassified; not run" if not c.category else "declined by user"` - the BEHAVIOR-PRESERVING
  cleanup we resolved (PL-2). Correct.
- BUG-02 (normalize_plan_names.py): `fromtimestamp(min(epochs))` now wrapped in
  `try/except (ValueError, OSError, OverflowError) -> None`. Correct.
- BUG-03 (versioning.py:319): `if not isinstance(data, dict): return None` guard added before
  `.get("info")`. Correct - fixes the AttributeError the finding named.
- BUG-04 (scan_secrets.py): the unused `line_no` was not merely removed - line tracking was
  IMPLEMENTED (`line_no = text.count("\n", 0, m.start()) + start_line`), delivering the accurate
  line reporting BUG-04/PL-3 contemplated. The intent is legitimate.
- Tests added for all four (test_run_checks, test_normalize_plan_names, test_pypi_links,
  test_scan_secrets); `tests/test_scan_secrets.py` and `tests/test_run_checks.py` pass. The only 2
  suite failures are the pre-existing 0954-01 ones handled by IPD 1028-01, NOT this work.

### The divergence (the finding)

| ID | Severity | Scope | Area | Evidence | Finding | Rem. Risk | Decision |
|----|----------|-------|------|----------|---------|-----------|----------|
| VE-1 | HIGH | OVER-SCOPE | P6/P8 | commit 57b2ae3: scan_secrets.py +408/-110, new `scan_text`/`scan_working_tree`/`scan_history`/`emit`; run_checks.py +249 | The plan authorized "clean up the unused `line_no` variable" (a one-liner) and a dead-code removal. Gemini instead REWROTE scan_secrets.py into new functions and made large run_checks.py changes - a substantial refactor never proposed, reviewed, or approved, with NO DECISIONS note justifying it. Fix Bar: unrequested over-scope defaults to removal/deferral. | Medium (see OQ) | OPEN - needs maintainer decision |
| VE-2 | LOW | IN-SCOPE | provenance | DECISIONS unchanged | A behavior-affecting refactor of the secret scanner landed with no decision record and outside its own reviewed plan. | Low | Whichever option in OQ1, record it. |

Note: em-dash house rule OK (0 in both rewritten files); the code passes its tests. So the refactor
is not broken - the issue is that it is UNREVIEWED scope that bypassed the plan/review gate.

## Options (OQ1 - maintainer decision, this is the crux)

1. ACCEPT + DOCUMENT: keep the scan_secrets/run_checks refactor (it works and delivers accurate line
   reporting), but require it to be RETROACTIVELY captured: write a proper assess/IPD or a DECISIONS
   entry describing the refactor and its rationale, and confirm the new functions are reviewed for
   correctness (a real /assess or /plan-review on the refactor, not just "tests pass"). Remediation
   Risk of keeping: Medium (a large unreviewed change to a security tool stays in without a design
   review).
2. TRIM to plan: revert scan_secrets.py/run_checks.py to a MINIMAL BUG-04/BUG-01 fix (remove the
   unused var / fix the one line; keep the accurate-line-reporting only if it is small), discarding
   the unrequested refactor, so the execution matches the approved plan. Remediation Risk: Low-Medium
   (a revert of working code, but restores scope fidelity).
3. SPLIT: keep the minimal bug fixes now; extract the refactor into its OWN new IPD to be reviewed on
   its merits (it may be a good change - it just was not reviewed). Remediation Risk: Low.

## Recommendation

Lean OPTION 3 (SPLIT): the refactor may be worthwhile, but it must go through review like anything
else - shipping a +400-line rewrite of the secret scanner under a "clean up an unused variable" plan
is exactly the over-scope our Fix Bar and P6 exist to catch. Splitting keeps the legitimate bug fixes
and subjects the refactor to a real review, without discarding possibly-good work.

## Open questions

1. Which option (ACCEPT+DOCUMENT / TRIM / SPLIT) for the scan_secrets + run_checks over-scope? (Lean:
   SPLIT.)
2. Process question for the /verify-execution workflow and the multi-agent workflow generally: should
   an executor be REQUIRED to stay within the approved plan's scope (and open a new IPD for anything
   beyond it)? (Lean: yes - encode "execution must not exceed the approved plan; extra scope -> new
   IPD" as an explicit rule, probably in AGENTS.md / the plan lifecycle. This is the systemic fix.)

## Approval and execution gate

`to-review`. Next: `/plan-review`, maintainer decides OQ1/OQ2, then execute the chosen option
(accept+document, trim, or split), validate (suite green once 1028-01 also lands), commit, `git mv`
to executed/. Not auto-executed.
