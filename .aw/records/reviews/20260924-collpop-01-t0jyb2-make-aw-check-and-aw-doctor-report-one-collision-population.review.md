# Review: Make aw check and aw doctor report one collision population

- Subject-Id: t0jyb2
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The plan was committed and unchanged, so the pre-review snapshot was correctly skipped per Step 1.
Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0) before review,
and `--phase review-finalize` reported `clean`, exit 0, ZERO findings after the revisions.

THIS IS THE BEST-EVIDENCED PLAN IN THIS SWEEP, AND EVERY CLAIM IT MAKES REPRODUCED. I re-derived each
independently rather than trusting the table. `check_collisions(root)` returns `Counter()` and
`check_collisions(root, include_retired=True)` returns `Counter({'check.id6-identity-slot': 3})`, on
exactly the three walkthroughs named (`zpbx7o`, `y5od1h`, `4fodkt`), with the set difference containing
nothing else in either direction. F-2's second axis reproduced verbatim on a fixture built from
`tests.test_check_engine._plan_text`: two executed plans both declaring `- Id: ccc333` produce
`check all` reporting the `check.id6-collision` in `all_drift` while `doctor.probe_artifacts` reports
`all_drift` EMPTY and files the identical `(path, rule)` pair under `executed_warnings`. Both call sites
are as described (`check_engine.check_types` threading `include_retired`, `doctor.probe_artifacts`
hardcoding `include_retired=True`). F-3's staleness claim holds: the setid pass measures zero at BOTH
scopes. F-4's docstring quote is verbatim and the walkthroughs README does say a walkthrough "MUST NOT
reuse the id6 of the plan it documents". The author also correctly identified the `tests/__init__.py`
cross-module import shape, which I verified works (`from tests.test_check_engine import _plan_text`).

I ALSO SIMULATED THE FIX before reviewing it, which is what produced the two substantive findings.
Feeding `_check_identity_slots` the terminal-inclusive record list yields exactly the 3 findings and no
others, so E-03's expected outcome is right and its blast radius is bounded.

THE DOMINANT FINDING IS PR-801, AND IT IS AN ORDERING HAZARD THE PLAN PREVENTS WITHOUT SAYING SO. E-04
changes doctor's call to `include_retired=include_executed`. If that lands while the slot pass still
honors the flag, doctor's default becomes `check_collisions(root, include_retired=False)`, which I
measured returns `Counter()` - so doctor would report ZERO slot findings where it reports 3 today. That is
a regression on the exact rule this plan exists to align, in the opposite direction, and it is silent:
the parity test's equality assertions (1) and (2) would still PASS, because both surfaces would agree at
zero. Only assertion (3), which demands the identity findings be PRESENT in both default sets, catches it.
The plan's `Depends on: E-03` chain does prevent this, so this is not a defect in the plan's design; it is
a missing statement of a correctness precondition that a partial revert, a reordered execution, or a
future refactor would trip. Given the plan's own concern is two surfaces silently disagreeing, shipping a
change whose inverse ordering silently produces the mirror-image disagreement deserves to be written down.

THE SECOND MATERIAL FINDING IS PR-802, and it is about a number that will mislead the next reader. The
docstring paragraph E-03 rewrites contains a deterrent: "that is the +47-finding regression this structure
exists to prevent", alongside "measured, that ships `check.setid-collision` 39 -> 86". Both described the
PRE-D153 cross-type emission, which was removed; measured now, the setid pass returns zero even at the
wide corpus. So the paragraph warns a future maintainer off making a change with a scare-number that no
longer describes anything, and the plan as authored removed only the "FALSE POSITIVES" phrase from that
same paragraph. Leaving a stale deterrent in place next to a corrected claim is how a settled question gets
re-opened by someone who trusts the number.

PR-803 is the source of F-4, and it is worth recording because it is a contradiction between two
authorities rather than a simple error. D140's own "Applied (2026-09-20, IPD `sk7ggr`)" note says the slot
and setid passes deliberately do NOT ignore the liveness filter, "to avoid mass-flagging the legitimate
shared-setid and walkthrough-slot conventions" - calling the walkthrough slot shape LEGITIMATE. The
walkthroughs README forbids it, and backlog `mw0s1y` (open, `Blocks-Release: next`) measures all three
instances as real violations with a concrete user-visible harm: `aw find y5od1h` returns two artifacts for
one identity. The plan was right to remove the docstring claim; it should also record WHERE the claim came
from, so the contradiction is settled once in the code comment rather than rediscovered by the next person
who reads D140 and the README in the same session.

PR-804 is the one I would most want a human to see, and it is the reason I added an item rather than a
sentence. This plan deliberately does NOT fix the data (`mw0s1y` owns that), so after execution
`aw check all` reports 3 `error`-severity findings that no in-scope change can clear. A detection fix that
reds the build is a real hazard, and the plan handled it in one under-scope bullet asserting the exit
status "already exits 1 with 24 errors". Two problems: the count is an authored live-artifact number (I
measured 23 a day later, which is exactly the drift the workflow's re-derivation convention exists for),
and "already exits 1" is not the claim that matters. The claim that matters is which gates run the
collision scan at all. I measured it: the fail-closed CI steps are `aw check plans` and `aw check
releases`; a per-TYPE run does not execute the collision scan, emitting only
`check.collisions-not-checked`, whose `RuleSpec` severity is `info`; and `.pre-commit-config.yaml` declares
no `aw check all` hook. So the new errors are confined to `aw check all` and `aw doctor`, and the plan is
safe to land before `mw0s1y`. That conclusion is worth an item with re-derived evidence and a STOP
condition, because if a CI step is ever widened the answer inverts and the two plans must be sequenced.

PR-805: OQ-01 was `open` with `Owner: maintainer`, which also made it an error-severity uncarried
obligation (`evaluate_durable_carrier` reported it, and the same predicate gates `pre-transition`). It was
answerable from the repository three ways over: `sk7ggr`'s own shipped reasoning that "A terminal id6 is
permanently cited, so a collision with one is real" applies identically to the slot rule; both identity
rules are `error` in `RULE_REGISTRY`, so a doctor-local demotion contradicts the declared severity rather
than expressing a softer view; and `mw0s1y` measures the harm as a broken cross-tree handle, which is
equally broken whichever surface is asked.

PR-806 is right-sizing plus two baselines the plan asserted without measuring. It is a small plan and was
close to correctly sized; the additions are the ordering precondition (PR-801) and the CI-safety proof
(PR-804), which are genuinely separate concerns from the two code edits.

THINGS I CHECKED AND FOUND FINE, recorded so they are not re-litigated. The two existing test rows most
likely to flip under E-03 both SURVIVE: I ran the terminal-inclusive slot pass against
`RetiredAndIgnoredScopeTests`' own fixture tree and it produced zero findings, so that class's
"the full sweep, retired excluded" zero-findings row is unaffected; and
`tests/test_doctor.test_executed_dir_warns_by_default` keys on `check.name-nonconformant`, a per-type rule
E-04 explicitly does not touch. The three affected modules report `86 passed` together at HEAD, which E-06
now cites as a baseline. The release-gate handoff is correct: `lmjc8h` carries `Blocks-Release: next`, the
plan inherits it, and `aw check release-gates` reports `conforms` with zero findings.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | A. Correctness / D. Anti-regression | Measured at review: `check_collisions(root, include_retired=False)` -> `Counter()`; `include_retired=True` -> `Counter({'check.id6-identity-slot': 3})`; the parity test's equality assertions (1) and (2) are both satisfied by two surfaces agreeing at ZERO | E-04 BEFORE E-03 IS A SILENT REGRESSION IN THE MIRROR DIRECTION, and the plan never said so. Changing doctor's call to `include_retired=include_executed` while the slot pass still honors the flag makes doctor's default corpus live-only, so doctor reports ZERO slot findings where it reports 3 today - a loss of detection on the exact rule this plan exists to align. It is silent because the parity test's equality assertions still pass when both surfaces agree at zero; only assertion (3), which requires the identity findings to be PRESENT, catches it. The `Depends on: E-03` chain prevents it in a clean sequential execution, but a partial revert, a reordered execution, or a later refactor of either call site reintroduces it with no test naming the hazard. For a plan whose whole subject is two surfaces silently disagreeing, the inverse failure deserves to be recorded. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (a stated precondition plus one assertion of presence, both already measurable) | FIXED | Added F-5 with the measurement. E-03 now opens by naming the order as a CORRECTNESS PRECONDITION with the measured consequence and an instruction to stop if executing out of order; E-04's new comment block must state the same, so a future partial revert cannot silently reintroduce it. V-04 now requires ORDERING EVIDENCE: `doctor.probe_artifacts(root).all_drift` still containing the 3 slot findings after E-04, which is the only observable distinguishing a correct sequence from the regression. |
| PR-802 | MEDIUM | IN-SCOPE | F. Honest documentation | `check_collisions` docstring: "+47-finding regression this structure exists to prevent" and "ships `check.setid-collision` 39 -> 86"; measured at review: `check_collisions(root, include_retired=True)` returns `Counter({'check.id6-identity-slot': 3})` with NO setid findings at any scope; D153 / spec `2lcqno` N1 removed the cross-type emission | THE DOCSTRING'S DETERRENT NUMBER IS STALE AND WOULD SURVIVE THE PLAN'S EDIT. E-03 rewrites that paragraph but the plan named only the "FALSE POSITIVES" claim for removal. The same paragraph's "+47-finding regression" warning and its 39 -> 86 figure describe the pre-D153 cross-type emission, which no longer exists; the setid pass measures zero even at the wide corpus. The result of a partial edit is a paragraph whose corrected sentence sits beside a scare-number warning a future maintainer off the very structure this plan is establishing - which is precisely how a settled question gets re-opened by someone who trusts the number over the code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-6 with the measurement. E-03 now enumerates THREE required docstring changes rather than one, with (b) covering both stale figures and stating why a stale deterrent is worse than none. V-03 now requires the diff to show BOTH removals and says explicitly that a diff removing only the "FALSE POSITIVES" phrase does not satisfy the item. |
| PR-803 | LOW | UNDER-SCOPE | F. Honest documentation | DECISIONS.md D140 "Applied (2026-09-20, IPD `sk7ggr`)": the slot and setid passes "deliberately do NOT" ignore the filter, "to avoid mass-flagging the legitimate shared-setid and walkthrough-slot conventions"; `.aw/records/walkthroughs/README.md`: a walkthrough "MUST NOT reuse the id6 of the plan it documents"; backlog `mw0s1y` status `open`, `Blocks-Release: next`, measuring all three as violations | THE FALSE-POSITIVE CLAIM HAS A SOURCE, AND REMOVING IT FROM ONE PLACE LEAVES THE CONTRADICTION LIVE. D140's own applied-note calls the walkthrough slot shape a "legitimate ... convention", which is where the docstring's claim came from; the walkthroughs README forbids exactly that shape and `mw0s1y` treats it as a live release-blocking bug with a measured user-visible harm (`aw find y5od1h` returns two artifacts for one identity). Fixing only the docstring means the next reader who consults D140 and the README in one session rediscovers the conflict with nothing recording which governs. | C:Low; U:Low; S:Low; F:Low; Overall:Low (a recorded citation; D140 itself is deliberately NOT edited) | FIXED | Added F-7. E-03(c) now requires the docstring to record the contradiction with the README and `mw0s1y` as controlling, and to say that the D140 note's parenthetical is the source of the removed claim. The gate's scope fence explicitly excludes editing D140, since a decision record states what was decided at the time and the resolution belongs in the code comment. V-03 requires this in the diff. |
| PR-804 | MEDIUM | UNDER-SCOPE | C. Operability / E. Verification | Measured at review: `.github/workflows/tests.yml` fail-closed steps are `aw check plans` and `aw check releases`; a per-type run emits only `check.collisions-not-checked`, whose `RULE_REGISTRY` severity is `info` (against `error` for `check.id6-identity-slot`); `.pre-commit-config.yaml` declares no `aw check all` hook; `aw check all` measured 23 findings where the plan asserts 24 | THE PLAN ADDS THREE ERRORS IT CANNOT CLEAR AND PROVES THE WRONG THING ABOUT THEM. It deliberately leaves the data unfixed (`mw0s1y`), so after execution `aw check all` reports 3 `error` findings with no in-scope remedy. The plan addressed this in one under-scope bullet asserting the exit status "already exits 1 with 24 errors" - a count that is an authored live-artifact number (review measured 23 a day later) and, more importantly, not the claim that matters. What matters is WHICH GATES RUN THE COLLISION SCAN. They do not: the fail-closed CI steps are per-type and per-type runs skip the scan entirely. That makes the plan safe to land before the data fix, but it was an unstated assumption rather than a demonstrated property, and it inverts the moment any CI step is widened to `check all`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-8 and a dedicated E-05 that RE-DERIVES the CI and hook evidence at execution time (the tree is live) and STOPS if a fail-closed step now runs `check all` or `check walkthroughs`, since the two plans would then need sequencing. V-05 requires the re-derived evidence rather than the plan's prose and states that a widened step makes the item's outcome stop-and-report, not a pass. The scope-check bullet now instructs re-derivation and states the non-drifting property (the exit status is already 1, so 3 added errors change no verdict). |
| PR-805 | LOW | IN-SCOPE | A. Correctness / G. Plan executability | `evaluate_durable_carrier` at review: `1 obligation(s) name no durable carrier: OQ-01 ...`, severity `error`; `sk7ggr` E-05's shipped comment "A terminal id6 is permanently cited, so a collision with one is real"; `RULE_REGISTRY`: `check.id6-identity-slot` and `check.id6-collision` both `error`; `mw0s1y`'s measured `aw find y5od1h` harm | THE PLAN ENTERED REVIEW WITH AN ERROR-SEVERITY FINDING from an open question the repository already answers three separate ways, and the same predicate gates `aw ipd lint --phase pre-transition`, so it would have blocked execution later. Leaving it open also framed a settled consistency question as an open product decision: a doctor-local demotion of an `error`-severity rule is not a softer VIEW, it is a contradiction of the declared severity. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved OQ-01 from evidence with `Status: resolved`, `Owner: none` and a `Carrier-Declined` reason, citing all three sources and recording what a genuine soften-both-surfaces decision would actually require (a `RULE_REGISTRY` severity change affecting `aw check` too). `evaluate_durable_carrier` now returns 0 findings. Recorded as D-1. |
| PR-806 | LOW | UNDER-SCOPE | G. Plan executability (right-sizing / evidence) | Original E-05 bundled the four-module run with a fixture-adjustment policy; the plan asserted "24 errors" and named no per-module baseline; measured at review: the three pre-existing modules report `86 passed` together | TWO BASELINES WERE ASSERTED RATHER THAN MEASURED, on a plan whose entire method is measurement. The affected-modules item gave no current pass count, so a pre-existing failure would be indistinguishable from a regression it caused; and the two test rows most likely to flip under E-03 were named as risks without being checked. I checked both: `RetiredAndIgnoredScopeTests`' zero-findings row survives (its fixture trips no widened slot finding) and the doctor test keys on a per-type rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low (decomposition and measurement only) | FIXED | Split to 7 items (E-05 is the new CI-safety proof; the module run and bare suite are E-06/E-07). E-06 now carries the measured 86-passed baseline and records both row checks with their results, so a flip is new information rather than a fixture to adjust. `Highest E allocated` corrected 06 -> 07. Cohesion rationale written. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: should `aw doctor` keep a softer, historical view of identity collisions on retired records? | No. Identity rules are terminal-inclusive and never demoted on either surface, as the plan proposed. Question marked resolved. | (a) Keep doctor softer - rejected on three independent grounds: `sk7ggr`'s shipped reasoning that a terminal id6 is permanently cited applies identically to the slot rule; both rules are `error` in `RULE_REGISTRY`, so a doctor-local demotion contradicts a declared severity rather than expressing a view; and the harm `mw0s1y` measures (one id6 resolving to two artifacts) is equally broken whichever surface is asked. (b) Soften BOTH surfaces - not chosen, but recorded as the only coherent form of the softer position, and noted in the resolution as a `RULE_REGISTRY` severity change affecting `aw check` too rather than a doctor edit. (c) Leave it for the maintainer - rejected: the repository answers it, and an open question here was also an error-severity uncarried obligation blocking `pre-transition`. | `check_engine` id6-pass comment "A terminal id6 is permanently cited, so a collision with one is real"; `RULE_REGISTRY` severities measured at review; `mw0s1y`'s `aw find y5od1h` measurement | yes |
| D-2 | The docstring's false-positive claim traces to DECISIONS.md D140's applied-note calling the walkthrough slot shape "legitimate". Should this plan correct D140? | No. Record the contradiction in the `check_collisions` docstring with the README and `mw0s1y` as controlling, and leave D140 untouched. | (a) Edit the D140 note - rejected: a decision record states what was decided and what was applied AT THE TIME, and rewriting it destroys the audit trail; the note is also historically accurate about what the code then did. (b) File a new backlog item for the contradiction - not done: `mw0s1y` already owns the data and the README already states the rule, so a third artifact would add tracking without adding a decision; the docstring citation is where a reader of this code will look. (c) Say nothing and remove only the false-positive phrase - rejected: that leaves two authorities in conflict with nothing recording which governs, which is how the claim got into the docstring in the first place. | D140 "Applied (2026-09-20)" note; `.aw/records/walkthroughs/README.md`; `mw0s1y` open with `Blocks-Release: next`; AGENTS.md's prohibition on amending terminal records is the same discipline applied to a decision entry | yes |
| D-3 | The plan adds 3 unclearable `error` findings. Should it be sequenced AFTER the data fix `mw0s1y` instead? | No. Land detection first, with a measured proof that it cannot red the build, plus a STOP condition if that changes. | (a) Sequence after `mw0s1y` - rejected: it makes a detection fix wait on a data fix that needs a maintainer decision about renaming tracked records (`mw0s1y` says so explicitly), and the detection is what makes the data defect visible on both surfaces in the first place. (b) Land detection and also fix the data here - rejected: renaming records under `.aw/records/` rewrites tracked history other artifacts cite, and `mw0s1y` records that no single existing verb performs the repair and that it needs maintainer sign-off. (c) Land detection with no CI proof - rejected: that is an unmeasured assumption about whether `main` goes red, which is exactly the class of claim this plan otherwise measures. | Measured: fail-closed CI steps are `aw check plans`/`aw check releases`; per-type runs emit only the `info` marker; no `aw check all` pre-commit hook; `mw0s1y` "DO NOT RENAME THESE RECORDS WITHOUT A MAINTAINER DECISION" | yes |

## Round 1 escalation

No finding was left `OPEN` or `DEFERRED` - all six are `FIXED` - so no `- Blocking: yes` question was
owed under Step 4's escalation rule, and `evaluate_review_finding_escalation` returns zero findings. No
decision is recorded `Reversible: no`: D-1 is a code behavior settled by existing severities and undoable
by editing the plan before execution, D-2 deliberately edits nothing durable, and D-3 is a sequencing
choice reversible by landing `mw0s1y` first.

WORTH THE MAINTAINER'S ATTENTION ANYWAY. This plan carries `Blocks-Release: next` inherited from
`lmjc8h`, and approving it endorses two positions that are recorded rather than escalated: that the
walkthroughs README governs over D140's "legitimate convention" parenthetical (D-2), and that a detection
fix may land while its data fix (`mw0s1y`, also release-blocking) stays open (D-3). Both are defensible on
the measurements above, and both are the maintainer's to overturn if the release plan wants the data fixed
in the same window.
