# Review: Give spec 25kzda 5.5's retry classes one declared mapping onto the drivers' disposition vocabulary

- Subject-Id: 4gx141
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims re-measured at HEAD `dac742b5` by importing the shipped module and driving the real
predicates, not transcribed. The target plan was committed and unchanged with a clean tree, so the
pre-review snapshot was correctly skipped per Step 1. Structural preflight `aw ipd lint --phase
author` reported `conforming` before review and `--phase review-finalize` reported `conforming`
after the revisions.

EVERY ONE OF THE PLAN'S ELEVEN FINDINGS REPRODUCES, SEVERAL CHARACTER FOR CHARACTER. F-01: the
fifteen spec class names intersected against the 29 `TURN_RETRY_CLASSIFICATION` rows is EMPTY. F-02,
the plan's centerpiece: `turn_failure_is_retryable({}, "failed")` returns `(False, "disposition
'failed' is not retryable: spec 5.5 ... generic undiagnosed turn failure, retryable")`, a single
sentence asserting both halves, exactly as quoted. F-03: `git log -S` confirms commit `6b94a4d9`
added the `failed` row and touched `TURN_RETRYABLE_DISPOSITIONS` zero times. F-04: `grep -rn
"TURN_RETRY\|turn_failure_is_retryable\|turn_retry_decision" tests/` returns 0 matches suite-wide,
and `tests/test_retry_consumption.py` was deleted by `19313eed`. F-05: `already-landed` is the sole
member of the three vocabularies with no table row, and the predicate returns the fail-closed "has
no entry" refusal for it. F-06: no queue-item producer writes bare `failed`, and
`reconcile_disposition`'s thirteen return sites never yield it. F-11: `canonical_terminal_status
("failed-safely")` is `"fail-gate"` and `failed-safely` is absent from `TERMINAL_STATES_CANONICAL`.
The defect is real, the diagnosis is correct, and the derive-plus-declare remedy is the right shape.

THE DOMINANT FINDING IS THAT A PLAN THIS ONE TREATS AS PENDING HAS ALREADY EXECUTED, and the plan is
consequently wrong about live code in the place it most needs to be right. `qo9khm` is `executed`:
authored at 03:24, this plan warns E-04 against prose-pinning lest the amendment "be stale the day
that plan executes"; `qo9khm`'s implementation landed at 05:00 and it finalized at 05:09, 1h45m
later. So the stale description is THIS PLAN'S. At review HEAD `finalize_refusal_is_retryable` keys
PRIMARILY on shipped lint codes via `retryable_finalize_finding_codes()`, with
`RETRYABLE_FINALIZE_FINDING_TEXTS` retained only as a deliberate fallback for findings carrying no
code and for the `C_CHECKPOINT` catch-all excluded on purpose. Had E-04 been executed as written it
would have written a spec amendment describing a mechanism replaced seven hours earlier, in the
very paragraph whose purpose is to be the durable reference. Seven places carried the stale premise
and all seven are corrected. The two-surfaces finding itself is untouched and remains the plan's
reason to exist.

THREE TEST-AND-ORDERING DEFECTS THAT WOULD EACH HAVE COST AN EXECUTION PASS. E-06's property (b)
says "every member of the vocabularies has a row", which is right, but an executor writing it as set
equality or symmetric difference gets a RED test at HEAD for an unrelated reason: the table carries
`merge-unchecked` and `unknown_outcome`, which are in neither vocabulary and are correctly there.
The invariant is one-directional containment and the plan never said so (PR-202). E-07's second half
instructs a repair to a comment that does not exist: the deleted test file is cited exactly ONCE in
the package, in the sentence E-07's first half already fixes, and `TURN_RETRY_COUNT_KEY`'s comment
cites no test at all, so an executor would have wasted a pass or invented an edit (PR-204). And
E-01 alone FLIPS BEHAVIOR, since the derived set is `{failed, failed-safely}` against the shipped
`{failed-safely}`; the plan names this risk in its gate but declares `E-02 Depends on: E-01`, which
reads as license to land the derivation first (PR-205).

TWO SMALLER CORRECTIONS OF FACT. The suite baseline is stale twice over: authoring recorded `3312
passed`, review measures `1 failed, 3401 passed`, and the one failure is a pre-existing UTC
date-rollover flake in `tests/test_backlog.py` that asserts a hardcoded `2026-09-30` while the
setter stamps the now-current `2026-10-01`. It touches no declared path, but V-06 compared against
a figure that no longer exists, so a real regression could have hidden behind the mismatch
(PR-203). And E-02's reachability case, while sound, omitted whether `failed` is canonical or
legacy: it IS canonical and is NOT an alias, so option (b) cannot be defended as retiring a legacy
spelling (PR-206, F-16).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | C. Architecture; G. Plan executability | `aw find all qo9khm` -> `executed`; `git log`: plan authored `aae72e5b 03:24:17`, `qo9khm` impl `b311fdfc 05:00:02` ("key on lint codes"), finalize `1e4b8a34 05:09:09`; `runner_shared.finalize_refusal_is_retryable` Arm 1 reads `retryable_codes = retryable_finalize_finding_codes()` | The plan calls `qo9khm` a "pending approved plan" that "is re-keying" the finalize classifier, and instructs E-04 to hedge the spec amendment so it survives that landing. It landed 1h45m after authoring. As written, E-04 would amend an approved spec to describe a prose-matching mechanism that was replaced seven hours earlier, in the paragraph whose whole purpose is durable reference. Seven sites carried the premise: Concern, Scope, Goal, E-04, E-05, F-08, Deferred, Spec-sync, Under-scope, V-05 and the gate. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added F-12 with the commits and timings. Corrected all affected sites: E-04 now requires the surface described as code-keyed-with-prose-fallback, cited by SYMBOL not by quoting either list, and requires re-reading the function at execution HEAD; E-05 records `qo9khm` as already executed and drops it from the compositions; F-08 reduced to one live composition and corrected (`cpi6p3` is now `approved`, not `reviewed`); Deferred re-grounded from collision-avoidance to out-of-subject; Under-scope now explains why the two surfaces legitimately differ rather than citing a pending fix; the gate re-written. |
| PR-202 | MEDIUM | UNDER-SCOPE | E. Testing | Driven: `(KNOWN_ITEM_STATUSES \| oc TERMINAL_STATES \| agy TERMINAL_STATES) - table` -> `{'already-landed'}`; `table - KNOWN_ITEM_STATUSES` -> `{'merge-unchecked', 'unknown_outcome'}` | E-06 property (b) states the coverage invariant without saying it is ONE-DIRECTIONAL. The table carries two rows in neither vocabulary, correctly, so an equality or symmetric-difference assertion is RED at HEAD for a reason this plan is not fixing. An executor would either write a failing test or "fix" the two extra rows, which is out of scope and wrong. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-13. E-06 now mandates `vocabularies - table == set()` and never equality, names both extra rows, explains why they are correct, and requires the asymmetry stated in the test's own docstring so a later reader does not tighten it. V-06 requires proof the test is green while both extra rows persist. |
| PR-203 | MEDIUM | IN-SCOPE | E. Testing; Step 1 evidence accuracy | Review-measured bare suite: `1 failed, 3401 passed, 2 skipped`; plan claims `3312 passed, 2 skipped`; the failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, asserting `- 2026-09-30` against a stamped `2026-10-01` | The declared baseline is stale and the suite is no longer green, so V-06's "at least as green" comparison is against a figure that does not exist. A real regression could hide behind the mismatch, and an executor could also waste a pass trying to fix an unrelated date flake. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Required-tests now instructs re-establishing the baseline in the executor's own lane and pasting it, records BOTH expired figures, identifies the flake by name with its cause and the fact that it touches no declared path, and forbids fixing it here. V-06 requires the baseline paste and that a still-red flake be shown present in the baseline too. |
| PR-204 | MEDIUM | OVER-SCOPE | G. Plan executability | `grep -n test_retry_consumption agent_workflows/*.py` -> exactly one line, `runner_shared.py:8052`; `TURN_RETRY_COUNT_KEY`'s comment names no test file | E-07's second half instructs the executor to repair a sibling comment citing the deleted test as the guard for `TURN_RETRY_COUNT_KEY`. No such citation exists. Following the instruction means either wasting a pass searching or inventing an edit to a comment that is not defective. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14. E-07 rewritten to describe ONE comment carrying TWO defects in one sentence (deleted file plus two files that exist but lack the coverage), to forbid hunting for the second comment with the measurement showing why, and to require the repaired coverage claim be stated one-directionally per PR-202. V-07 requires the single-citation measurement pasted. Scope check records this as a removed would-be over-scope edit. |
| PR-205 | MEDIUM | IN-SCOPE | A. Correctness | Driven: derived set `{failed, failed-safely}` vs shipped `{failed-safely}`, delta exactly `{failed}`; plan declares `E-02 Depends on: E-01` | E-01 alone is a behavior change: the moment the comprehension lands, `failed` becomes retryable. The plan names the risk in its gate but constrains no commit ORDER, and the dependency direction reads as license to land E-01 first, which would ship an unintended retry flip in an intermediate commit. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | Added F-17. E-01 now requires E-02 in the same pass or E-02's row first, states that the item split is for decision hygiene rather than a licence to land separately, and its Expected outcome forbids any committed state carrying the derivation without the resolved row. |
| PR-206 | LOW | IN-SCOPE | Step 1 evidence accuracy | Driven: `"failed" in TERMINAL_STATES_CANONICAL` -> `True`; `"failed" in TERMINAL_STATUS_ALIASES` -> `False`; `canonical_terminal_status("failed")` -> `"failed"` | E-02's reachability measurement establishes no producer but not whether the token is canonical or legacy. It is CANONICAL and not an alias, so option (b) may not be justified as retiring a legacy spelling, and a resumed run reading an older persisted `failed` stays `failed`. The plan's conclusion is probably right; its justification was incomplete. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16. E-02 gained the canonical-versus-legacy measurement, a requirement to state which justification the evidence supports, the correction that `layout_migration.py`'s five `tx_data["status"] = "failed"` hits are a different object rather than producers, and the resumed-run case as a legitimate route to option (a). V-02 requires all of it pasted. |
| PR-207 | LOW | IN-SCOPE | Step 1 evidence accuracy; G. Plan executability | `grep -rn "verifier transport"` -> three tracked prose matches (spec, research `ig9bai`, backlog `rb4wgj`), not one; `agent_workflows/specs.py` module docstring "NEVER stages, commits, or pushes git" | Two small inaccuracies: F-10 claims the phrase matches "exactly one line, in the spec itself", which overstates a true finding; and E-05 prescribes `aw specs note` without stating it does not stage or commit, so an executor could omit the spec path from `aw commit` and fail the declared finalize reconciliation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 restated with the three matches and the operative fact sharpened to "no CODE consumer". E-05 states `aw specs note` stages nothing and the spec must reach the plan's own `aw commit`; V-05 requires proof it did. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | `qo9khm` has executed. Does that invalidate the plan, require a REPLAN, or require corrections? | Corrections only. The plan's thesis, defect and remedy are untouched; one consumer's MECHANISM description was wrong. | REPLAN, rejected: the two-surfaces finding, the `failed` contradiction, the missing row and the dead citation are all independent of how the finalize surface classifies, and all four reproduce. Leaving it, rejected outright: E-04 writes into an approved spec, so a wrong mechanism description there is the most durable possible place for it. | `aw find all qo9khm` -> `executed`; `finalize_refusal_is_retryable` read in full at review HEAD showing code-keyed Arm 1 with prose fallback; F-01..F-06 all re-driven and reproducing. | yes |
| D-2 | Should E-06 property (b) assert containment or set equality? | One-directional containment, `vocabularies - table == set()`. | Set equality, rejected: measured RED at HEAD because `merge-unchecked` and `unknown_outcome` are table rows in neither vocabulary. Removing those two rows to make equality hold, rejected as out of scope and wrong: a classified-but-unlisted disposition is harmless, an unclassified one is the hole E-03 closes. | Driven set arithmetic in both directions; the shipped comment's own words claim coverage ("a status added elsewhere without a verdict here FAILS A TEST"), not a bijection. | yes |
| D-3 | E-07's second target does not exist. Delete the instruction, or leave it for the executor to discover? | Delete it and record the measurement that retired it. | Leaving it, rejected: it costs a pass at best and an invented edit to a non-defective comment at worst. Silently dropping it without the measurement, rejected because a later reader would re-add it on the same reasoning the author used. | `grep -n test_retry_consumption agent_workflows/*.py` -> one line; `TURN_RETRY_COUNT_KEY`'s comment read in full, citing no file. | yes |
| D-4 | Does the E-01/E-02 ordering hazard need a blocking question, or an in-plan constraint? | An in-plan constraint on commit order; not blocking. | Raising it `Blocking: yes`, rejected: it is not a question for the human, it is a sequencing requirement the plan can simply state, and `IPD-Q501` would then hold the plan for something the author can fix by wording. Leaving it to the gate's prose risk note, rejected because the dependency declaration pointed the other way. | Driven: delta is exactly `{failed}`; the plan's own gate already identifies the risk, so only the constraint was missing. | yes |
| D-5 | Is the pre-existing suite failure this plan's to fix? | No. Identify it as pre-existing, require it reproduced at the baseline, forbid fixing it here. | Fixing the date flake in this plan, rejected: it touches no declared path and would widen `- Scope-Paths:` for an unrelated defect. Ignoring the baseline staleness, rejected because V-06's comparison would then be against a nonexistent figure and could mask a regression. | `tests/test_backlog.py` failure output showing `- 2026-09-30` vs `+ 2026-10-01`; `date -u` confirming the UTC rollover; the test's path is not in this plan's `- Scope-Paths:`. | yes |
| D-6 | OQ-02 leaves the `failed` verdict to the executor and is `open`. Is that acceptable, or must the reviewer decide it? | Acceptable as authored, with the measurement strengthened. | Resolving it myself to option (b), rejected: it is a HOW question whose answer turns on a reachability measurement that must be re-taken at execution HEAD, and this plan's own figures have already expired twice; the workflow permits converting such a question into a bounded item whose outcome names the demonstration, which E-02 already is. Making it blocking, rejected: either option yields one consistent source of truth, which is the plan's objective. | plan-review 3.1 "Resolving HOW questions"; E-02 names both options, the evidence each requires, and a recorded decision; V-02 refuses the item without it; `- Owner: executor of E-02` is a real owner. | yes |

No `Reversible: no` decisions were made, so no escalation was required under the
irreversible-decision rule. No finding was left `OPEN` or `DEFERRED` at or above the `HIGH` gate
threshold, so no `- Blocking: yes` escalation question was added to the plan.
