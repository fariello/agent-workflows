# Review findings: plan 38pxaz

- Subject-Id: 38pxaz
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-301 (HIGH, fixed), PR-302 (HIGH, fixed), PR-303 (HIGH, fixed), PR-304 (MEDIUM, fixed), PR-305 (MEDIUM, fixed), PR-306 (MEDIUM, fixed), PR-307 (MEDIUM, fixed), PR-308 (LOW, fixed), PR-309 (LOW, fixed), PR-310 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `d4235e0b`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `clean` with zero findings after revision. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

THIS IS A STRONG PLAN AND ITS CENTRAL JUDGEMENT IS CORRECT. I re-drove every measurement rather than
reading it, because the plan authorizes deleting shipped code and amending an approved spec, and every
one holds:

- The AST caller census reproduces EXACTLY. Walking every `.py` in the tree outside the module (and
  outside `.aw/`) for an `Import` or `ImportFrom` naming `wtiso_gate` returns precisely one result,
  `from agent_workflows.wtiso_gate import AW_MISSING_INPUT` at `lane_containment.py:62`. One import,
  against a module of 443 lines and nine public predicates.
- The raise check reproduces. Calling all nine with placeholder arguments: `check_lifecycle_role`,
  `check_hook_bypass`, `check_protected_refs`, `classify_retention` and `check_receipt` raise
  `NotImplementedError` naming a retired owner; `check_scope` returns `[]`, `format_missing_input`
  returns a token, `parse_missing_input` returns `None`, and `check_permission_deadline` raises
  `TypeError` on string placeholders (a probe artifact, not a defect, and the same trap I hit reviewing
  sibling `bec7ee`).
- Both cited test files are absent, `git log --diff-filter=D` names `19313eed` alone, and
  `git show --stat` lists them at 731 and 704 deleted lines.
- The spec's three sites quote VERBATIM, R6.1's text quotes verbatim, P15's and P6's text quote
  verbatim, and the 2026-09-28 maintainer ruling on backlog `gia5i7` quotes verbatim.
- `MISSING_INPUT_TOKEN_FORM` renders `AW_MISSING_INPUT:<repo-relative-path>:<why it is required>`
  composed from the single imported constant, exactly as F-9 claims, and `_token_prefix` reads the
  prefix back out of it, so the prompt/parser single-definition property is real and load-bearing.
- `aw specs check` reports all 38 specs conforming today, so the spec is clean before the amendment.
- The sibling dependency is sound: `bec7ee` is `reviewed` with `Readiness: go-pending-approval`, the
  Order-0 orchestrator names all three children, and `executed:bec7ee` correctly sequences the audit
  record ahead of the deletion it justifies.

FOUR CORRECTIONS MATTER, and three of them are undercounts rather than errors of judgement, which is the
characteristic failure mode of a plan whose measurements were taken by sampling rather than enumeration.

PR-301, THE CITATION COUNT IS SIX AND HALF OF THEM SURVIVE E-03. The plan says three. Measured, there are
six, and the distribution is what makes the undercount material rather than cosmetic: TWO sit in the
MODULE DOCSTRING and ONE in `check_scope`'s docstring, all three of which survive E-03 under any
keep-the-file branch. So the plan's claim that "most will disappear with the deleted docstrings" is false
for exactly half, and E-04 is doing substantive work rather than catching a remainder. One of the six is
also inside the RUNTIME `_unimplemented` MESSAGE STRING in `check_hook_bypass`, i.e. executable code, not
a docstring, so an executor sweeping docstrings would miss it even while deleting the right things. I
mapped all six to their enclosing scope by AST rather than by eye, because that is the only way to know
which survive which branch.

PR-302, E-03'S ERROR-CODE LIST IS WRONG TWICE. It says "the four stable error codes" and then names FIVE;
and it omits `AW_GATE_SCOPE` and `AW_PERMISSION_DEADLINE` entirely, though a repo-wide grep shows them as
unreferenced outside the module as the five it does name. The module defines EIGHT codes plus an
`ERROR_CODES` tuple enumerating all eight. An executor following the list literally would delete five,
re-home one, and leave two orphans in a file the plan intends to delete, with the tuple referencing them.
I replaced the list with a RULE over all eight and required the disposition re-derived from the module,
because a hand-list is what failed here and copying a corrected hand-list would fail the same way next
time.

PR-303, A16 HAS THREE CLAUSES AND THE PLAN ADDRESSED ONE. This is the finding with the longest reach,
because it is the one `aw specs check` cannot catch. A16 reads "Each implemented shared predicate has unit
tests; each unimplemented one still raises naming its owner; and a predicate implemented but not chartered
for wiring has no product caller." The plan quotes and amends only clause 2. But clause 1 is EQUALLY
falsified by deleting the file: the four implemented bodies cease to exist while A16 keeps asserting they
have unit tests, and those tests went with the same 2026-09-24 trim, so the criterion would end up
asserting tests for predicates that are gone. The plan would have shipped a spec amendment that left the
spec wrong in a different place than it found it.

PR-304 is the related trap I checked because PR-303 made me read Section 4's preamble: the spec asserts
programmatic traceability ("every requirement below is cited by at least one criterion, with TWO deliberate
exceptions", naming R3.3a-1 and R4.1b). A16 is the ONLY criterion citing R6.2, so an amendment that deleted
A16 rather than amending it in place would create a third, undocumented exception and falsify the preamble.
E-05 now forbids the deletion and requires the `(R6.1, R6.2, R6.3)` citation list kept intact.

PR-305 is a second spec-side omission in the same area. R6.3 (the implement-versus-wire split) is cited by
A16's third clause, and `check_scope` is the ONE predicate in the tree that demonstrates it; its own
docstring says exactly that. Deleting it removes R6.3's only instance. Losing an example is not a licence to
narrow the rule, but a later reader finding R6.3 with no instance may read it as dead, so E-05 now requires
R6.3 left untouched WITH the loss of its example stated rather than silently absorbed.

PR-306 fixes a missing machine-readable field rather than a missing intent: `aw check` reported
`check.plan-spec-link-missing` on this plan, remedy `aw ipd set 38pxaz --from-spec 7ckptx`. The plan already
declares the spec in `- Scope-Paths:` and argues the amendment at length in its spec-sync section, so the
intent was never in doubt; what was missing is the field that makes the spec handoff readable by tooling.
Setting it cleared the finding. Worth recording that adding `- Readiness:` before writing the history record
made `aw ipd lint` refuse with `IPD-M107` ("a REVIEW OUTPUT but no review verdict appears in
`## Workflow history`"), which is the attestation gate working exactly as AGENTS.md describes, caught on my
own edit rather than on the author's.

PR-307 RESOLVES BOTH OPEN QUESTIONS, which is this review's own obligation because both carried
`- Owner: reviewer` and were addressed to me. OQ-01 (delete the file, or keep it holding the constant)
resolves to DELETE, on measurement: after E-02 the import count is ZERO, the seven other error codes have no
external reference, and two of the four implemented bodies are one-line delegations INTO `lane_containment`,
so keeping them preserves a prose-level dependency cycle whose only purpose was a caller surface that never
arrived. I answered the counter-argument rather than dismissing it: `check_scope`'s rule is not lost, because
its own docstring records that `ipd_lifecycle._scope_match` owns the grammar and `finalize_precheck` already
enforces scope today, so the predicate wraps a live rule rather than being it; and `check_permission_deadline`'s
own docstring says "the enforcing bound today is `MAX_TURN_TIMEOUT` alone", so it enforces nothing. OQ-02
resolves to the NO-SUBJECT framing, and I rejected narrowing R6.2 on a specific hazard rather than on
verbosity: narrowing would write an anti-malice carve-out into a requirement about fail-loud DISCIPLINE,
conflating two orthogonal rules, so a later author wanting a legitimate non-malice stub would find R6.2
narrowed by a reason irrelevant to their case and would naturally read fail-loud as optional, which is the
permissive default R6.2 exists to forbid.

PR-308 and PR-309 are small. F-10 claims `docs/wtiso-state-taxonomy.md` "cites the module"; measured,
`grep -c 'wtiso_gate'` on that file returns 0, so the doc shares a name prefix and nothing more. The
correction STRENGTHENS the out-of-scope call (the doc holds no reference this deletion could dangle) rather
than weakening it, which is why I corrected it rather than leaving a harmless overstatement. PR-310 updates
the stale baseline and adds the one validation surface the suite is blind to: under any keep-the-file branch,
the surviving module and `check_scope` docstrings are prose no test exercises, so E-04's work on them is
invisible to `pytest` and must be shown by pasting the surviving text.

NOTHING ELSE WAS FOUND WRONG, and several things are notably well done. The plan's refusal to restore either
deleted test file is correct twice over and correctly argued (one was an AST caller census, which P16 forbids
and the maintainer has ruled against restoring; the other proved a premise for a gate this Set deletes on
principle). The "ONE WAY TO GET THIS PLAN WRONG" paragraph is exactly the right warning and names the real
hazard (duplicate the constant and the prompt/parser can drift, which is the fork R6.1 forbids). E-02's
move-not-copy discipline is the correct reading of R6.1, and F-8's observation that this plan HONORS R6.1
rather than weakening it is right. Treating E-01 as a hard gate with an explicit stop is correct for a
deletion. The prohibition on any test asserting a symbol was deleted is correct and unusually well stated
("would itself become the next stale citation"). The five `Carrier-Declined` reasonings are substantive, and
the one for re-implementing deleted predicates is the strongest: filing a carrier would assert the repository
intends to build what its own guiding principle forbids. `Work-Kind: chore` with no release gate is correct
and measurement-backed, since every deleted symbol is unreachable from any shipped path.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | UNDER-SCOPE | Rubric D (invariants), G (executability) | `grep -rn 'test_containment_predicates\|test_wtiso_adversarial' agent_workflows/` returning six lines (26, 33, 138, 260, 270, 289), mapped by AST to MODULE docstring (26, 33), `check_scope` (138), `check_hook_bypass` (260 docstring, 270 runtime string), `check_protected_refs` (289) | THE CITATION COUNT IS SIX, NOT THREE, AND HALF SURVIVE E-03. Three citations sit in prose the keep-the-file branch preserves (two module docstring, one `check_scope`), so "most will disappear with the deleted docstrings" is false for exactly half and E-04 is substantive rather than a remainder sweep. One of the six is inside a RUNTIME `_unimplemented` message string, i.e. code, which a docstring-only sweep misses. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Fact 3 rewritten with the six and the three-and-three split; E-04 rewritten around which vanish and which must be struck by hand, naming the runtime-string instance; V-04 requires the struck count reconciled against six. New F-3b. |
| PR-302 | HIGH | IN-SCOPE | Rubric A (correctness), G | module top-level assigns (eight codes plus `ERROR_CODES` over all eight); repo-wide grep for the seven non-`AW_MISSING_INPUT` codes returning nothing outside the module | E-03'S ERROR-CODE LIST IS WRONG TWICE: it says "four" while naming five, and omits `AW_GATE_SCOPE` and `AW_PERMISSION_DEADLINE` entirely though both are equally unreferenced. A literal executor would leave two orphan codes, still enumerated by `ERROR_CODES`, in a file the plan intends to delete. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now resolves the surface BY RULE over all eight codes and requires the disposition re-derived from the module rather than copied from the item; V-03 requires an eight-way table and fails a five-code answer. New F-3c. |
| PR-303 | HIGH | UNDER-SCOPE | Rubric A, spec sync | A16 verbatim: "Each implemented shared predicate has unit tests; each unimplemented one still raises naming its owner; and a predicate implemented but not chartered for wiring has no product caller. (R6.1, R6.2, R6.3)" | A16 HAS THREE CLAUSES AND THE PLAN ADDRESSED ONE. Clause 1 is equally falsified by deleting the file: the four implemented bodies cease to exist while A16 keeps asserting they have unit tests, and those tests went with the same trim. The amendment as scoped would leave the spec wrong in a new place, and `aw specs check` cannot catch it because it validates structure rather than claims. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now quotes A16 in full, amends all three clauses, and requires each labelled no-subject or still live; V-05 fails an amendment addressing only clause 2. New F-7b. |
| PR-304 | MEDIUM | IN-SCOPE | Rubric A, spec sync | Section 4 preamble ("every requirement below is cited by at least one criterion, with TWO deliberate exceptions", naming R3.3a-1 and R4.1b); `grep -n 'R6\.2'` returning exactly two hits, the requirement and A16 | A CARELESS A16 EDIT WOULD BREAK THE SPEC'S OWN TRACEABILITY PROPERTY. A16 is the ONLY criterion citing R6.2, so deleting it rather than amending in place would create a third, undocumented exception and falsify the preamble that claims there are exactly two. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 forbids deleting A16, requires its `(R6.1, R6.2, R6.3)` citation list intact, and requires `aw specs check` pasted; V-05 enforces both. New F-7d. |
| PR-305 | MEDIUM | UNDER-SCOPE | Rubric A, spec sync | `check_scope`'s docstring: "BODY IMPLEMENTED, CALLERS DELIBERATELY ABSENT - the spec R6.3 split, and the one predicate here that demonstrates it"; A16's trailing R6.3 citation | DELETING `check_scope` REMOVES R6.3'S ONLY DEMONSTRATION, and the plan never says so. R6.3 remains correct, but a later reader finding a rule with no instance may read it as dead, and the amendment is where that should be stated rather than left to inference. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires R6.3 left UNTOUCHED with the loss of its example stated explicitly and not used as an argument to narrow it; V-05 requires R6.3 shown unchanged in the diff. New F-7c. |
| PR-306 | MEDIUM | IN-SCOPE | Project rule (`check.plan-spec-link-missing`) | `aw check` naming the rule, this plan, and the fix `aw ipd set 38pxaz --from-spec 7ckptx`; `rule_spec` severity `info` | THE PLAN AMENDS A SPEC WITHOUT THE MACHINE-READABLE LINK. The spec is correctly declared in `- Scope-Paths:` and the amendment is argued at length, so this is a missing field rather than a missing intent, but the field is what makes the handoff readable by tooling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- From-Spec: 7ckptx` added; `aw check` re-run reports no finding on this plan. V-05 requires that evidence. New F-7e. Noted: adding `- Readiness:` before the history record made the lint refuse with `IPD-M107`, the attestation gate working as designed. |
| PR-307 | MEDIUM | IN-SCOPE | Step 3 (open questions) | both OQs carrying `- Owner: reviewer` and `- Status: open` | BOTH OPEN QUESTIONS WERE ADDRESSED TO THE REVIEWER AND LEFT UNANSWERED, which would have sent the executor into a deletion with a live design choice to make mid-item (OQ-01 decides whether the file survives, which changes what E-04 must strike by hand). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | OQ-01 resolved to DELETE the file on measurement (zero importers after E-02, zero external code references, two bodies being delegation cycles), with the counter-argument answered rather than dismissed. OQ-02 resolved to the no-subject framing, rejecting narrowing on the hazard that it conflates fail-loud discipline with anti-malice scope. Both recorded with reasoning; E-03 and V-03 now reference OQ-01's resolution. |
| PR-308 | LOW | IN-SCOPE | Step 1 evidence | `grep -c 'wtiso_gate' docs/wtiso-state-taxonomy.md` returns `0` | F-10 CLAIMS THE DOC CITES THE MODULE; IT DOES NOT. The doc shares a name prefix and nothing more. The correction strengthens the out-of-scope call rather than weakening it, since the doc holds no reference this deletion could dangle. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 corrected with the measurement and the stronger out-of-scope reason stated. |
| PR-309 | LOW | IN-SCOPE | Rubric G (live-artifact criteria) | bare `python3 -m pytest` at review HEAD: `3512 passed, 2 skipped, 3 warnings in 135.66s`, `208 deselected` | THE REQUIRED-TESTS SECTION DEMANDED A BASELINE WITHOUT GIVING ONE, so an executor had no figure to sanity-check against and no warning that the count drifts daily. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The review baseline is recorded as CONTEXT with an explicit instruction to re-derive in the executing worktree and to judge on the property rather than the number. |
| PR-310 | LOW | UNDER-SCOPE | Rubric E (testing) | the module docstring and `check_scope`'s docstring, neither exercised by any test | HALF OF E-04'S WORK IS INVISIBLE TO THE SUITE. Under any keep-the-file branch the surviving docstrings are prose no test touches, so `pytest` cannot show whether a false enforcement claim remains. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a required module-docstring cross-check to Required tests, requiring the surviving prose pasted so a reviewer can see no sentence still claims a test enforces anything. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: delete `wtiso_gate.py` entirely, or keep it holding only `AW_MISSING_INPUT`? | DELETE the file. | (a) Keep it holding the constant: rejected, that is the arrangement E-02 exists to end, and it leaves the reverse dependency the plan identifies as the hazard. (b) Keep `check_scope` and `check_permission_deadline` as real logic a future wiring might want: rejected on their own docstrings, since `_scope_match`/`finalize_precheck` already own and enforce the scope rule so the predicate wraps a live rule rather than being it, and `check_permission_deadline` records that "the enforcing bound today is `MAX_TURN_TIMEOUT` alone", so it enforces nothing; git history plus a re-proposal on merit is the recovery route its sibling's docstring already prescribes. | The AST census (one import, removed by E-02); the repo-wide grep showing the seven other codes unreferenced; `format_missing_input`/`parse_missing_input` measured as one-line delegations INTO `lane_containment`; GUIDING_PRINCIPLES P6 on hypothetical need; both owning phases RETIRED 2026-09-02 with no successor. | yes |
| D-2 | OQ-02: narrow R6.2 and A16 to exclude anti-malice predicates, or record them as having no subject? | NO-SUBJECT framing (as E-05 already specified), with the P15 reasoning in the amendment. | Narrowing R6.2: rejected on a specific hazard rather than on verbosity. It would write an anti-malice carve-out into a requirement about FAIL-LOUD DISCIPLINE, conflating two orthogonal rules; a later author wanting a legitimate non-malice stub would find R6.2 narrowed for a reason irrelevant to their case and would naturally read fail-loud as optional, which is the permissive default R6.2 exists to forbid. | R6.2's own text (a declared-not-implemented predicate must not return a permissive default); P15 as a rule about which predicates are worth declaring rather than how they must behave; the plan's own measurement that it found no fault in the discipline. | yes |
| D-3 | E-03's error-code list is wrong twice. Correct the list, or replace it with a rule? | REPLACE it with a rule over all eight codes, requiring re-derivation from the module. | Correcting the list in place: rejected, a hand-list is precisely what failed here (it miscounted AND omitted two members), so shipping a corrected hand-list invites the same failure the next time the module changes. | The module's eight top-level code assigns plus `ERROR_CODES`; the repo-wide grep establishing `AW_MISSING_INPUT` as the only externally referenced one. | yes |
| D-4 | A16's clause 1 is also falsified. Amend A16, delete it, or leave clause 1? | AMEND A16 IN PLACE, all three clauses, citation list intact. | (a) Delete A16: rejected, it is the only criterion citing R6.2, so deleting it would create a third undocumented exception to the spec's stated traceability property. (b) Amend only clause 2 as authored: rejected, that leaves the spec asserting unit tests for predicates that no longer exist, which is a new wrong claim introduced by the fix. | A16 verbatim with its three clauses and `(R6.1, R6.2, R6.3)` citation; Section 4's two-exceptions preamble; `grep -n 'R6\.2'` showing A16 as its sole citing criterion. | yes |
| D-5 | Should this review add `- From-Spec: 7ckptx`, given the plan already declares the spec in `Scope-Paths` and argues the amendment? | YES, set the field. | Leaving it and noting the finding: rejected, the rule's whole purpose is to make the spec handoff machine-readable, the remedy is a single front-matter field, and `aw check` names this plan explicitly with the exact fix command, so leaving it would preserve a reported finding for no benefit. | `aw check` reporting `check.plan-spec-link-missing` with the fix `aw ipd set 38pxaz --from-spec 7ckptx`; AGENTS.md on the `From-Spec` field as the machine-readable spec-to-plan link. | yes |

No `Reversible: no` decision was taken in this round. Both open questions are now `resolved` and neither is
`Blocking: yes`; every finding is `FIXED`, so no escalation into the plan as a blocking question was required.
