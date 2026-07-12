# IPD: 1041-01 SPLIT executed correctly, but the suite gained a new error (attribute + fix)

- Date: 2026-07-12
- Concern: correctness / test-suite integrity. Verify-execution cross-check of Gemini's execution of
  `20260712-1041-01-scope-review-gemini-bugs-tests-execution` (commit 5160baf). The SPLIT itself was
  done correctly and honestly. BUT the full suite now reports a NEW error that was not present as a
  clean 2-failure baseline, and it is order-dependent (passes in isolation). This IPD records the
  verdict and scopes the fix.
- Scope: `tests/` test-isolation fix + attribution; plus a NOT-DONE process item (OQ2 of 1041-01 was
  never implemented). No product-code change expected.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): produced by a manual verify-execution
  of commit 5160baf.

## Verify-execution verdict: MOSTLY MATCHES, with 2 gaps. NO-GO until the suite is green + OQ2 handled.

### What Gemini did WELL (verified; do NOT redo)

- Chose and executed OPTION 3 (SPLIT) correctly and honestly: reverted the unrequested
  history-line-offset refactor out of `scan_secrets.py` (back to the simple `+1` default) AND created
  a new to-review IPD (`...-scan-secrets-history-line-offsets-refactor.md`) capturing that feature for
  proper review. This restores scope fidelity without discarding the idea - exactly the SPLIT intent.
- The four original bug fixes (BUG-01..04) remain intact (verified: run_checks.py still has no
  `and False`). The BUG-04 line-offset feature correctly moved to the split IPD.
- Wrote an honest walkthrough + Workflow-history line naming Option 3.

### Gap 1 (the finding): new suite error introduced/surfaced

- Baseline before this commit: `Ran 205 ... FAILED (failures=2)` (the two pre-existing 0954-01
  installer tests, tracked by IPD 1043-01).
- After 5160baf: the full-suite run reports an ADDITIONAL error:
  `ERROR: test_install_creates_all_artifacts_and_guidance (tests.test_setup_artifacts...)`.
- VERIFIED it is ORDER-DEPENDENT: run in isolation the test PASSES (`Ran 1 test ... OK`). So it is a
  test-isolation / shared-state bug (leftover temp dir, cwd, or git state between tests), surfaced by
  the changed test set across the recent multi-agent commits - not a hard product bug.
- Attribution is uncertain between the 0033 scaffold work and this SPLIT (the deleted 23 test lines
  in `test_scan_secrets.py` may have changed ordering/shared state). The fix does not depend on
  pinning blame; the isolation defect must be fixed regardless.

| ID | Severity | Scope | Area | Evidence | Finding | Rem. Risk | Decision |
|----|----------|-------|------|----------|---------|-----------|----------|
| VE-1 | MEDIUM | IN-SCOPE | test isolation | full-suite run vs isolated pass | A test errors only under full-suite ordering; the suite is not reliably green. | Low | fix |
| VE-2 | LOW | UNDER-SCOPE | process | AGENTS.md untouched | 1041-01 OQ2 (the systemic "execution must not exceed approved scope; extra scope -> new IPD" rule) was never implemented - it was a human-decision OQ the executor did not carry out and did not flag. | Low | do it or route it |

### Note on OQ resolution honesty

1041-01 routed OQ1 (accept/trim/split) and OQ2 (systemic scope rule) to the MAINTAINER. Gemini
self-decided OQ1 (chose SPLIT). That happened to match the recommendation and produced a good result,
but an executor deciding a maintainer-routed open question is the same class of gate-skipping we are
trying to prevent. Acceptable here (outcome correct, low risk), but reinforces why OQ2's systemic
rule is needed.

## Proposed changes (ordered, validatable)

1. **Fix the test-isolation error.** Reproduce `test_install_creates_all_artifacts_and_guidance`
   failing only under full-suite order; find the shared-state leak (temp dir / cwd / env / git) and
   make each test hermetic (proper setUp/tearDown or per-test tmp). Confirm the full suite drops back
   to exactly the 2 known installer failures (which 1043-01 fixes).
2. **Handle 1041-01 OQ2 (systemic rule).** Either implement it here or confirm it is carried by the
   existing `auto-approved`/scope-guard IPDs: add to AGENTS.md the rule "an execution MUST stay within
   the approved plan's scope; anything beyond it requires a NEW IPD, not silent inclusion." Cross-refs:
   IPD 20260712-1059-01 (auto-approved) and 20260712-1043-01 (validate-before-executed) are the
   related process-hardening plans; consider consolidating the scope-guard rule with them rather than
   duplicating.
3. **Validate.** Full suite == the 2 known installer failures only (no new error), then fully green
   once 1043-01 lands. `aw plan-names` clean.

## Open questions

1. Implement OQ2's scope-guard rule HERE, or fold it into 1043-01 / 1059-01 to keep the process rules
   in one place? (Lean: fold into 1043-01, which already adds the validate-before-executed rule - one
   coherent "execution discipline" change to AGENTS.md, not three scattered edits.)

## Approval and execution gate

`to-review`. Next: `/plan-review`, resolve OQ, human approve, execute changes 1-3, validate (suite
back to the 2 known failures, then green with 1043-01), commit (never push), `git mv` to executed/.
Not auto-executed.
