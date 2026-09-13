# Review findings: spec w15vzb

- Subject-Id: w15vzb
- Subject-Type: spec
- Reviewed-At: 2026-09-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9697856e`. Structural preflight `aw specs check` CONFORMED (exit 0) before and after
revision. No pre-review snapshot needed: the spec was committed and unmodified.

THE DECISION RECORD IS EXEMPLARY AND THE SPEC WAS NOT REVIEWABLE AS A SPEC. Its reasoning is the best of
the four reviewed today: the maintainer's fitness-for-task reframing is preserved verbatim and its two
consequences traced, Section 3 corrects its own motivating measurement (a `grep role` returning zero was
TRUE and MISLEADING, because the shipped mechanism spells the concept `verify_with`), Section 4.4 splits
one recommendation into two cases with opposite answers and says why, and Section 4.6 declines a version
bump with a stated asymmetry rather than by oversight. It also corrects two of its own source plan's
claims. None of that needed changing.

WHAT IT LACKED WAS ANY ACCEPTANCE CRITERION AT ALL. Nine requirements, zero criteria, so nothing stated
what evidence would satisfy or REFUSE a claim of completion. That is the single largest gap found in any
of the four specs, and it matters most here precisely because Section 9 asserts R-1 to R-5, R-9 and R-6
case A are implemented: an implementation claim with no criterion is unrefusable. Twelve criteria were
added with a full coverage map, and three of them (A-8, A-9, A-10) are explicitly the OUTSTANDING set,
each naming what it waits on.

TWO PROPERTIES THE SPEC ARGUES FOR AND NOTHING WAS CHECKING. The design's core promise is 'EXTEND, do not
supersede': the role map is a new BOTTOM tier, so it can add an answer where there was none and can never
change one an existing document already produced. Section 4.3 says every prior configuration resolves
byte-identically and that this is 'asserted rather than assumed' - but no criterion asserted it, so the
claim rested on the reader's trust. A-5 now demands it. Likewise the provenance value is `role-map`
DISTINCT from `defaults` for a stated operator-debugging reason, with nothing requiring it; A-6 does.

I VERIFIED EVERY IMPLEMENTATION CLAIM RATHER THAN TRUSTING SECTION 9. `ROLE_NAMES` is exactly the six
named roles; `SCHEMA_VERSION` is 2 with both versions supported; `PROVENANCE_ROLE_MAP` is `role-map`;
`roles` is top-level and `ALLOWED_PROFILE_KEYS` was NOT widened (which was one of the placement
decision's stated reasons); and `tests/test_runner_profiles.py` passes at `131 passed in 2.42s` with named
cases for the vocabulary, the dangling reference, the mutator cases, the tier ordering, the
unchanged-bytes property and the no-bump decision. The inertness claim also holds: `runner_profiles`,
`resolve_launch_profile` and `launch_profile` each grep to ZERO in `agy_runipd.py`.

ONE NAMING COLLISION WILL CONFUSE THE NEXT READER AND IS A DEFECT IN NEITHER PLACE. `host_adapters.py`
independently defines a closed set of things it calls ROLES (`ROLE_ROUTER`, `ROLE_ISOLATED_EXECUTOR`,
`ROLE_NONINTERACTIVE_RUNTIME`, `ROLE_PERMISSION_GATE`) with its own `resolve_role_target` resolver. Those
are HOST CAPABILITIES; this spec's are KINDS OF WORK. The vocabularies are disjoint and must never be
unified or cross-validated, and a plan wiring a consumer will meet both.

R-9 WAS CONDITIONAL ON A QUESTION THE SPEC NEVER STATED. It requires a pairing to stay inexpressible
'until OQ-05 is decided', and OQ-05 lives only in plan `btot17`, so a reader of the spec alone could not
see what R-9 waits on, who owns it, or what would close it. The spec had no open-questions section at
all. One was added carrying the question properly, and it is `Blocking: no` for a real reason: R-9 ships a
typed refusal, so the pair cannot become quietly expressible while the question waits.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-201 | HIGH | UNDER-SCOPE | C. acceptance criteria cover the requirements | the spec as authored: nine `R-*` requirements in Section 7, and no acceptance-criteria section anywhere | **THE SPEC HAD NO ACCEPTANCE CRITERIA WHATSOEVER, so no requirement had a refusable completion test.** This is worse than a coverage gap because Section 9 CLAIMS six requirements plus one case are implemented: with no criteria, that claim cannot be refused, and the three outstanding requirements have nothing describing what finishing them would look like. For a design record whose whole purpose is that the next action finds an ANSWER here, an unrefusable implementation claim is the failure mode. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | New Section 9 adds twelve criteria, each naming the requirements it covers, with a full coverage map. A-8, A-9 and A-10 are marked OUTSTANDING and each names its dependency (the consumer, the verdict store, the consumable-`roles` plan). A-12 was added for the Section 6 inertness boundary, so a populated role map cannot be mistaken for working routing. |
| SR-202 | HIGH | IN-SCOPE | B. requirements are testable; D. the load-bearing promise | Section 4.3's claim that every prior configuration 'resolves byte-identically, which is asserted rather than assumed'; no criterion asserting it as authored | **THE DESIGN'S CENTRAL SAFETY PROPERTY HAD NO CRITERION, despite the spec saying it is asserted.** 'EXTEND, do not supersede' means the role map is consulted ONLY where the shipped chain already fell through to ABSENT. If that property breaks, an existing operator's configuration silently resolves to a different model, which is precisely the invisible-in-the-result-rather-than-visible-in-the-bill failure the spec elsewhere refuses to accept. Nothing in the spec required proving it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A-4 requires the role map to speak last at every tier, and A-5 requires a pre-existing document's resolution AND serialized bytes to be equal before and after. A-6 covers the distinct `role-map` provenance, which was the other stated-but-unchecked property. |
| SR-203 | MEDIUM | UNDER-SCOPE | E. open questions are dispositioned | R-9's text ('until OQ-05 is decided'); OQ-05 exists only in plan `btot17`; the spec had no open-questions section | **A REQUIREMENT IS CONDITIONAL ON AN OPEN QUESTION THE SPEC DOES NOT CONTAIN.** R-9 defers to `btot17`'s OQ-05, so a reader of the spec alone cannot see what R-9 waits on, who owns it, or what would close it, and `aw attention` counted zero open questions for a spec with a live one. The spec is explicitly the durable record for this design, so a question governing one of its requirements must be visible in it rather than in a plan that will move to `executed/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New Section 8 carries OQ-01 with the maintainer as owner, the 2026-09-08 ruling that decided the DEFERRAL, the three points that would close the DESIGN (all named in Section 6), and why it is non-blocking (R-9's typed refusal keeps the pair inexpressible while it waits). Section renumbering applied so the heading is one the attention counter recognizes, verified by measurement rather than assumed. |
| SR-204 | MEDIUM | IN-SCOPE | F. honest limits; G. it can be planned from | `host_adapters.ROLE_ROUTER`/`ROLE_ISOLATED_EXECUTOR`/`ROLE_NONINTERACTIVE_RUNTIME`/`ROLE_PERMISSION_GATE` with `resolve_role_target`, versus this spec's `ROLE_NAMES` | **TWO DISJOINT CLOSED VOCABULARIES IN THIS PACKAGE ARE BOTH CALLED ROLES, AND THE SPEC MENTIONS ONLY ITS OWN.** One is host capabilities (what a host can do), the other kinds of work (what a model is good at). A plan wiring a consumer will meet both, and the plausible-but-wrong move is to unify or cross-validate them. Not a defect in either place; a collision a reader must be warned about. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in Section 10 as a naming hazard, naming both vocabularies, stating they are disjoint, forbidding unification or cross-validation, and requiring a consumer plan to say which it means at every call site. |
| SR-205 | LOW | IN-SCOPE | A. measured claims are verified | verified at review: `ROLE_NAMES` exactly six; `SCHEMA_VERSION` 2 with `SUPPORTED_SCHEMA_VERSIONS` {1,2}; `PROVENANCE_ROLE_MAP == 'role-map'`; `ALLOWED_PROFILE_KEYS` unwidened; `131 passed in 2.42s`; zero `runner_profiles`/`resolve_launch_profile`/`launch_profile` hits in `agy_runipd.py` | **SECTION 9's IMPLEMENTATION CLAIM WAS UNVERIFIED IN THE RECORD, and a spec asserting its own implementation should carry the evidence.** Every claim CHECKS OUT, including the OC-only reach and the deliberate non-widening of the profile key set. But as authored the reader had only the assertion, and this spec exists so the next action finds an answer rather than re-deriving it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Section 10 gains the verification with the measured values, the named test cases, and the pasted suite result, so the implementation claim is evidenced rather than asserted. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-201 | The spec has no acceptance criteria. Author them, or record the gap and leave the spec as a decision record? | AUTHOR THEM, twelve, with a coverage map and an explicit outstanding set. | (a) Leave it as a pure decision record, rejected: the spec carries nine numbered MUSTs and a claim that seven are implemented, so it is a requirements document whether or not it is called one, and the rubric's coverage rule applies. (b) Author criteria only for the outstanding three, rejected: that leaves the IMPLEMENTED claim unrefusable, which is the more dangerous half. (c) Ask the maintainer whether criteria are wanted, rejected: the spec contract answers it, since every MUST needs a covering criterion. | the spec's own R-1..R-9 numbering and Section 9's implementation claim; the spec rubric's requirement that every MUST map to at least one criterion | yes |
| D-202 | R-9 depends on plan `btot17`'s OQ-05. Restate it in the spec, or point at the plan? | RESTATE IT AS THE SPEC'S OWN OQ-01, with owner, ruling, closing conditions and blocking judgement. | (a) Point at the plan, rejected: `btot17` is executed and its plan file will read as history, while this spec is the durable record by its own Section 1; a live question governing a spec requirement must be visible in the spec. (b) Mark it blocking to force a decision, rejected as false: R-9 ships a typed refusal, so nothing can become quietly expressible while it waits, and marking it blocking would stall a spec on a capability nobody has asked for. (c) Drop R-9's conditionality, rejected: it is the guard keeping an undecided shape inexpressible. | R-9's own text; `btot17` OQ-05 with the 2026-09-08 ruling 'role to model mapping now, pairing recorded as the next step'; the object-value refusal citing the question by name | yes |
| D-203 | Adding an open-questions section required renumbering three later sections. Renumber, or use a non-numbered heading? | RENUMBER (7a became 8, and the two following shifted), after MEASURING that the attention counter recognizes the heading. | (a) Keep `## 7a. Open questions`, rejected on measurement: `attention._OQ_SECTION_RE` does NOT match a `7a.` prefix, so the question would have been invisible to `aw attention` and the OQ count would have stayed zero, defeating the point of recording it. (b) Use a bare `## Open questions` out of numeric order, rejected as inconsistent with the spec's own numbered structure. Verified after renumbering that the count reads 1 unresolved. | `attention._OQ_SECTION_RE` matching `## 8. Open questions` and rejecting `## 7a. Open questions`; `count_question_stats` returning (1, 0) after the change | yes |

### Deferred and open

Five findings, all FIXED; none deferred, none REPLAN. ONE OPEN QUESTION REMAINS BY DESIGN: the spec's new
OQ-01 (the producing-plus-validating pair), which is `Blocking: no`, owned by the maintainer, and whose
deferral was already ruled on. It does not block approval: R-9's typed refusal keeps the capability
inexpressible while it waits.

### Honest limits of this review

- IT DID NOT EXERCISE THE ROLE MAP END TO END, because there is no consumer to exercise (Section 6). The
  implementation claims were verified at the module and test level only.
- THE THREE OUTSTANDING CRITERIA (A-8, A-9, A-10) ARE UNSATISFIABLE TODAY and are marked as such. A-9 in
  particular depends on a verdict store that does not exist, which the spec itself corrects its source
  plan about.
- I DID NOT JUDGE WHETHER THE SIX ROLES ARE THE RIGHT SIX. They are the maintainer's own categories taken
  verbatim, which is a decision recorded rather than a question open.
