# Review findings: plan t5txjk

- Subject-Id: t5txjk
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `1aaa74e4` in a lane worktree. Structural preflight `aw ipd lint --phase author`
reported `conforming` with ZERO findings. After the revision edits, `--phase review-finalize` reports
`error` with exactly ONE diagnostic, `IPD-Q501` (OQ-01 is a BLOCKING question still open), which is the
INTENDED fail-closed consequence of PR-002's deliberate escalation and not a structural defect; every
other structural check passes and the `E-*`/`V-*` bijection is complete at 5/5. No pre-review snapshot
was owed: the plan was committed and unmodified (`git status --short` empty) and the lane-input copy
under `.aw/state/lane-inputs/rev-24/` is byte-identical (`diff -q` reports IDENTICAL). Bare suite at
review HEAD: `3246 passed, 2 skipped, 3 warnings in 46.12s`. NO PRODUCTION FILE, TEST, OR DOC WAS
MODIFIED by this review; every measurement was a read, an in-process run over a synthetic `TestCase`, or
a `pytest` run over a temporary probe file in a `TemporaryDirectory`.

ALL SEVEN AUTHORED FINDINGS REPRODUCE, and the plan's central claim reproduces empirically. F-01: I had
already reproduced this independently while reviewing the sibling plan `vtup6x`, and it reproduces again
here (corrupting `MERGE_DECISIONS[0]`'s expected exit code to `99` yields `FAILED (failures=1)` with the
aggregate naming the corrupted case, while an `addSubTest` driver prints PASS for all seven rows). F-02:
an AST walk over `tests/*.py` returns exactly four append-without-in-context-assert `subTest` blocks,
all in `tests/test_executed_transition_gate_e2e.py`, in exactly the four methods E-01 names; I measure
266 total `subTest` blocks against the plan's 242-plus-4, a counting-method difference that leaves the
operative claim exact. F-04 reproduces UNDER `unittest`, precisely as worded, including its "one failure
per failing row plus one for the aggregate" (3 failures for 2 wrong rows) and the aggregate message
still being present. F-05: `pytest_subtests` raises `ModuleNotFoundError` and the extras are as quoted.
F-06's row census reproduces exactly: 15 + 4 + 7 + 4 + 3 = 33. F-07: `test_executed_transition_gate.py`
contains neither table. The `0i4fkt` precedent exists. The three new files do not yet exist and `docs/`
does.

THE PLAN IS WELL MEASURED AND ITS CENTRAL FIX IS STILL WRONG, which is the whole substance of this
review. F-04 measured the fix under `unittest`, where every subtest failure is recorded and the trailing
aggregate assertion still runs. This repository runs `pytest`, without `pytest-subtests` (which the
plan's own F-05 establishes), and pytest behaves differently: an in-context failure aborts the test at
the FIRST failing row, so the aggregate assertion is never reached and the maintainer's diagnostic prose
and the complete wrong-row list both vanish. The plan's fence names that prose as "the channel a normal
`pytest` run reports through" and forbids touching it; the authored E-01 would have deleted it while its
`Expected outcome` asserted the opposite. This is a case where the plan's evidence was correct, its
inference from that evidence was wrong, and the error is invisible on an unmodified tree because every
row passes.

I did not stop at the finding: I searched for a mechanism satisfying both constraints and demonstrated
one, so the plan is repaired in place rather than replanned. An opt-in switch read INSIDE the test method
gives truthful per-row verdicts in the driver's mode and a byte-identical default run. I also measured
that the obvious variants do NOT work (a class-attribute read is invisible to a subprocess driver; an
aggregate assertion moved into its own trailing `subTest` block still does not surface), so the
prescription is specific rather than a hopeful sketch.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness; D. Anti-regression (the prescribed fix deletes the diagnostic it must preserve) | plan E-01 as authored; plan fence constraint FIRST; `tests/test_executed_transition_gate_e2e.py` trailing `self.assertEqual(wrong, [], ...)` in each of the four methods | **THE PRESCRIBED FIX DESTROYS THE DIAGNOSTIC CHANNEL THE PLAN'S OWN FENCE REQUIRES IT TO PRESERVE.** Measured at review through REAL `python3 -m pytest` on a probe reproducing the house shape (three rows, two wrong): with TODAY's append-only code the aggregate marker IS present and BOTH wrong rows are listed; with an UNCONDITIONAL in-context `self.fail`, the aggregate marker is ABSENT, only the FIRST failing row appears (`ROWFAIL_b` count 2, `ROWFAIL_c` count 0), and the trailing aggregate assertion is NEVER REACHED. The fence says those messages "carry the maintainer's diagnostic reasoning" and "are the channel a normal `pytest` run reports through"; E-01's own `Expected outcome` claimed the aggregate "still fails with the same aggregate message naming the same rows". F-04 is not false, it measured `unittest` (reproduced at review: 3 failures, aggregate present); pytest without `pytest-subtests` differs, and pytest is what this repository runs, which F-05 already establishes. The error is invisible on an unmodified tree because every row passes. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | A mechanism satisfying BOTH properties was found and DEMONSTRATED at review: an opt-in strict switch read INSIDE the method body, default off (switch off -> aggregate present and both rows listed; switch on -> `a PASS`, `b FAIL`, `c FAIL` with every row executed and the enclosing test failing). E-01 rewritten around it with the measurement inline and the two non-working variants named (class-attribute read, aggregate-in-its-own-subTest). E-02 extended to assert BOTH modes. E-03 made to own turning the switch on. E-05 added to prove the default path unchanged, with V-05. Gate gains this as constraint ZERO and a second silent-failure paragraph. Added F-08. |
| PR-002 | HIGH | IN-SCOPE | G. Executability; release-gate contract | plan OQ-01 `- Blocking: no`; `AGENTS.md` "Every live bug gates the next release"; measured `release_gate_work_kinds` absent from `.aw/config/project.json` | **OQ-01 IS A RELEASE-GATE QUESTION AND THEREFORE BLOCKING, so `- Blocking: no` was wrong.** The plan correctly declines to invent a gate and correctly routes the classification to the maintainer; the error is the label. The repository's contract is that a LIVE artifact whose `- Work-Kind:` is in the gating set (default `bug`, confirmed by the absent config key) MUST carry `- Blocks-Release:`. So the answer decides a FRONT-MATTER FIELD on this very plan, and executing under the wrong answer ships a release-gating defect with no gate recorded, which is precisely the silent gap that contract exists to prevent. That is not a classification nicety an executor may proceed past. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | OPEN | ESCALATED, not merely left open: OQ-01 set to `- Blocking: yes` with `- Finding: PR-002`, so `aw ipd lint` now reports `IPD-Q501` at EVERY checkpoint and the plan cannot reach `approved` or be dispatched until a human answers. The rationale records what is being decided in one line and adds review's own measurement (F-10) without settling it. Gate paragraph rewritten; readiness is `no-go` for this one reason, with the re-check route named. Added F-09. |
| PR-003 | HIGH | UNDER-SCOPE | E. Testing (the regression had no owning item) | plan E-02/V-01 as authored | **NOTHING OWNED PROVING THE DEFAULT RUN UNCHANGED**, which after PR-001 is the plan's most important regression surface. V-01 asked only for the driver-path before/after, and E-02 as authored pinned only the strict property, so an implementation that broke the default run would have passed every item in the plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-05/V-05 owning the DEFAULT-path corrupted-row before/after (does the aggregate prose appear; which wrong rows are listed) plus the same-lane bare-suite delta. E-02 now also asserts the switch-OFF behaviour, so the regression is pinned by a test and not only by a one-time paste. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing (a V-item that could pass while the regression shipped) | plan V-01 as authored | V-01's AFTER half demanded the corrupted row report FAIL and "the enclosing aggregate assertion still failing with its original diagnostic prose naming the same row", which F-08 measured is UNOBTAINABLE in strict mode: pytest never reaches that assertion. So V-01 as authored was internally contradictory, and the likely resolutions are both bad (weaken the demand, or paste `unittest` output and call it the pytest result). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now demands the strict-mode half AND the switch-OFF half explicitly, states that an AFTER showing only the strict listing FAILS the item, and requires pasting the switch and showing it is read inside the method body rather than as an import-time class attribute. |
| PR-005 | MEDIUM | IN-SCOPE | C. Architecture / F. Honest documentation (undisclosed public surface) | `pyproject.toml` `packages = ["agent_workflows"]` | **E-03 ADDS A MODULE TO THE SHIPPED WHEEL and the plan does not say so.** `agent_workflows/subtest_rows.py` is published, not test-only. That is defensible for importable executor tooling, but an approver should see it stated, and it strengthens rather than weakens the decision not to add a CLI verb. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-11 and stated in the approver paragraph, tied to the existing CLI-verb deferral. |
| PR-006 | LOW | IN-SCOPE | F. Honest documentation (a dated number with no stated baseline) | plan Required-tests bullet 3 | The plan correctly forbids comparing against any number written in it, then recorded `3246 passed, 2 skipped` nowhere and gave the executor no honest framing for the comparison. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 records the review-measured `3246 passed, 2 skipped` at HEAD `1aaa74e4` explicitly labelled DATED CONTEXT, not the bar, and requires a same-lane baseline judged as a delta of failing node ids. |
| PR-007 | LOW | IN-SCOPE | Step 1 evidence (a count that does not reproduce) | plan F-02 ("the other 242 subTest blocks across 46 files"); measured 266 total by AST walk | F-02's subsidiary count does not reproduce (I measure 266 total, so 262 others). The finding's OPERATIVE claim reproduces exactly and is what bounds the work: 4 affected blocks, all in one file, in the four named methods. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Left the number and recorded both measurements here, for the same reason applied in the sibling review: the sibling plan's own new rule says a live-population count belongs in prose as CONTEXT and must never be the bar, no item depends on it, and swapping one unexplained number for another is not an improvement. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001: the prescribed in-context failure deletes the aggregate diagnostic under real pytest. Replan, weaken the fence, or find a mechanism satisfying both? | FIND AND PRESCRIBE A MECHANISM: an opt-in strict switch read inside the test method, default off. Demonstrated at review before prescribing. | (a) REPLAN; rejected because a working mechanism exists and was demonstrated, so bounded edits suffice and a replan would discard sound work (F-01 through F-07 all reproduce). (b) Weaken the fence to permit losing the aggregate diagnostic; rejected because that prose is the maintainer's diagnostic reasoning and the only channel an ordinary run reports through, and deleting it to improve an ad-hoc driver trades a shared surface for a private one. (c) Add `pytest-subtests`; rejected on the plan's own F-05 (it cannot surface a row that raises nothing) and because it would add a dependency the plan deliberately declines. (d) Aggregate assertion moved into its own trailing `subTest` block; MEASURED at review and it still does not surface, so it does not solve the problem. | Measured at review HEAD `1aaa74e4`: real `pytest` on a probe, switch off -> aggregate marker present and both wrong rows listed; switch on -> `addSubTest` records `a PASS`, `b FAIL`, `c FAIL` with all rows executed and the enclosing test failing. Also measured: a class-attribute read of the switch is invisible to a subprocess-spawning driver, so the read must be in the method body. | yes |
| D-2 | PR-002: should the reviewer answer OQ-01's `bug`-versus-`followup` classification, or escalate it? | ESCALATE. Set `- Blocking: yes` with `- Finding: PR-002` and leave the answer to the maintainer. | Answering it myself as `followup` (the perceptibility test leans that way, F-10); rejected because the repository reserves release-gating and risk-appetite calls to the human, and because the answer writes a `- Blocks-Release:` field, which is exactly the kind of attestation a reviewer must not mint. Leaving it `- Blocking: no` as authored; rejected because the answer decides a front-matter field on this plan, so execution under the wrong answer ships an ungated release-gating defect. | `AGENTS.md`'s release-gate contract plus the measured default gating set (`release_gate_work_kinds` absent from `.aw/config/project.json`). The escalation is the documented mechanism: `IPD-Q501` now fires at every checkpoint, verified by running the linter after the edit. | yes |
| D-3 | F-02's subsidiary count (242 across 46 files) does not reproduce; I measure 262 of 266 (PR-007). Correct it or leave it? | Leave the number and record both measurements here. | Rewriting it to my measurement; rejected for the reason the sibling plan `vtup6x` itself establishes and this review already applied to its F-07: a live-population count belongs in prose as context and must never become a bar, no E-item or V-item depends on it, and substituting one unexplained number for another does not improve it. | The operative claim (4 blocks, 1 file, 4 named methods) reproduces exactly by AST walk. Consistency with D-3 of the sibling review, same measurement, same disposition. | yes |

### Verdict and readiness

Verdict: `REVIEWED - OPEN QUESTIONS`. Readiness: `NO-GO` (`- Readiness: no-go`), for EXACTLY ONE reason:
the unresolved BLOCKING question OQ-01. Six of the seven findings are FIXED in place, including the
BLOCKER, which was repaired with a demonstrated alternative rather than deferred. PR-002 is OPEN and
correctly escalated into the plan as a `- Blocking: yes` question carrying `- Finding: PR-002`, so
`check.review-finding-unescalated` is satisfied and `aw ipd lint` reports `IPD-Q501` at every checkpoint
until a human answers.

WHAT THE MAINTAINER MUST DO, in one line: answer whether a test harness that reports a FAILING row as
PASS is a `bug` (which obliges `- Blocks-Release:` on this plan while it is live) or a `followup` (no
gate). Review's own measurement (F-10) leans `followup` by the repository's stated USER-PERCEPTIBLE
IMPACT test, since no shipped command changes and the four tests do still fail on a wrong row through
their aggregate assertion; the argument for `bug` is that the corrupted artifact is EVIDENCE, which that
test was not written for. That weighing is the maintainer's, not the reviewer's.

ONCE ANSWERED, this plan needs no fresh review: set the field the answer implies, resolve OQ-01, and run
`aw ipd recheck-readiness t5txjk` to reach `GO - PENDING HUMAN APPROVAL`. The `no-go` recorded here is a
MOMENT, not a judgement on the plan's quality, which is high.
