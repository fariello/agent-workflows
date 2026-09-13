# Review findings: spec 6m4kow

- Subject-Id: 6m4kow
- Subject-Type: spec
- Reviewed-At: 2026-09-13
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `9697856e`. Structural preflight `aw specs check` CONFORMED (exit 0) before and after
revision. No pre-review snapshot needed: the spec was committed and unmodified.

THIS REVIEW IS ITSELF THE SPEC'S ACCEPTANCE TEST, which is worth stating plainly because it is unusual
and because it is the strongest evidence available. Spec `6m4kow` R-06 requires that a spec-review
capability exist producing a findings table, a verdict, a conforming record and a legal transition. This
review ran that capability, against this spec, and this record is its output. A-01 is satisfied by the
artifact you are reading.

THE SPEC HAS SHIPPED AND READS AS THOUGH IT HAD NOT, WHICH IS THE CENTRAL DEFECT. It sat at `to-review`
for nine days while three plans graduated from it and executed, so its Section 1 still says 'none of it
is implementable today' and its requirements are all future tense. Measured requirement by requirement:
15 of 16 are IMPLEMENTED (the artifact-neutral record with a closed subject-type vocabulary, type-directed
dangling resolution, 186 records all carrying the subject pair and none carrying `- Plan-Id:`, the
`spec-review/` package, the three prohibitions, the attested transition enforced by exactly ONE predicate
consulted from three call sites, structural grandfathering, and a single `def needs_review` in the whole
package). A reader taking the spec at face value would re-derive finished work.

THE EXCEPTION IS R-15, AND ITS GAP IS PRECISE. Cross-type discovery WORKS when called
(`sweep_review_candidates_for_type(repo, "spec")` returns exactly the four specs now at `to-review`) and
is unreachable by any operator, because `--type` greps to ZERO in both host runners. The function's own
docstring says so and refuses to overclaim. That is the one honest hole, and it was carrying the release
gate.

NO ACCEPTANCE CRITERION CITED A SINGLE REQUIREMENT, in a spec whose requirements carry stable ids
expressly so criteria and plans can cite them (its own Section 2 preamble says this). Mapping them
revealed three MUSTs with no criterion at all: R-05 (the filename grammar), R-10 (the workflow-shape
decision) and R-15 (cross-type discovery, the one unfinished requirement, uncovered). An uncovered MUST
in a release-gating spec is how an unbuilt requirement ships unnoticed, and here it nearly did.

THE RELEASE GATE MOVED, ON THE MAINTAINER'S EXPLICIT RULING. Asked whether R-15's unreachable half should
still gate 2.0.0, the maintainer answered that a gate belongs on a PLAN and not on a spec, that plans are
preferred to backlog items, that selection ships now with the execution half filed as its OWN release
blocker, and that HOW execution is implemented needs DISCUSSION captured loudly. Two plans were therefore
authored review-ready and this spec's field cleared: `ui8b9b` (selection) and `mng63x` (execution,
design-first, whose blocking question is the design itself). The blocker count is unchanged.

THREE MEASURED CLAIMS THAT WOULD HAVE MISLED AN IMPLEMENTER, all corrected: the record population is
quoted as 34 in a requirement and a criterion when it grows with every review (186 today, and 36 when the
implementing plan was reviewed, so it was already stale then); `aw find specs --status` is called broken
at authoring and IS STILL BROKEN, root-caused here to a branch that never consults its status filter and
affecting seven record types, tracked by no backlog item; and the grandfathered population is quoted as
20 when the invariant must hold for whatever the population is.

WHAT THE SPEC GOT RIGHT AND KEEPS: the structural argument (specs authorize plans, and their transition
was the unattested one), the refusal to make a volume case, D-01's single-record reasoning, D-04's
insistence that a meaningless `reviewed` is worse than an inconvenient gate, and Section 6's honesty that
attestation proves a review happened and never that it was competent.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| SR-101 | HIGH | IN-SCOPE | C. acceptance criteria cover the requirements | the spec's own Section 2 preamble ('Each requirement has a stable ID so a graduating plan can trace to it'); zero `R-` references inside Section 3 as authored | **NOT ONE ACCEPTANCE CRITERION CITED A REQUIREMENT, AND THREE MUSTS WERE UNCOVERED.** The spec gives every requirement a stable id for traceability and then never uses them in its criteria. Mapping them exposed R-05, R-10 and R-15 with no criterion at all. R-15 is the ONE requirement that is not fully built, so the uncovered set and the unfinished set intersect exactly where it is most dangerous: a release-gating spec could have been read as satisfied while its only outstanding requirement had nothing checking it. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | Every criterion now names the requirements it covers; A-09 (R-15), A-10 (R-05) and A-11 (R-10) added; an explicit 16-requirement coverage map closes the section so an uncovered MUST is visible rather than inferred. A-09 additionally requires the operator-reachability limit to be stated plainly rather than implied. |
| SR-102 | HIGH | IN-SCOPE | A. the spec describes the current state | `review_findings.SUBJECT_TYPES == ('ipd','spec')`; 186 records all carrying the subject pair, 0 carrying `- Plan-Id:`; `TRANSITION_AUTHORITY['->reviewed']` carrying `review_record: True`; exactly one `def needs_review`; `eyh1fu`/`5slbpi`/`wpomxa` all `- Status: executed` | **THE SPEC SAYS 'NONE OF IT IS IMPLEMENTABLE TODAY' WHILE 15 OF ITS 16 REQUIREMENTS HAVE SHIPPED.** Three plans graduated and executed during the nine days it waited at `to-review`, and nothing in the spec records that. Every requirement is future tense. A reader would re-derive finished work, and a reviewer could re-authorize it as pending, which for a release-gating spec means the release gate says something false about what remains. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | New Section 0 carries a per-requirement status table with the evidence for each row, names the three delivering plans, and states which requirement is NOT done and why. Section 1's diagnosis moved to the past tense and marked as preserved reasoning rather than a live measurement. |
| SR-103 | HIGH | UNDER-SCOPE | F. honest limits; the release gate's meaning | `grep -c '\"--type\"'` -> 0 in both `oc_runipd.py` and `agy_runipd.py`; `sweep_review_candidates_for_type(repo,'spec')` -> the four `to-review` specs; `uyeko5` excluding the flag by name | **R-15 IS BUILT AND UNREACHABLE, AND THE SPEC CARRIED A RELEASE GATE WITHOUT SAYING WHICH HALF WAS OUTSTANDING.** The sweep resolves real specs at the function boundary; no operator invocation can supply a type, so `aw oc run reviews --type spec` is an unrecognized-argument error. The spec's `- Blocks-Release: next` therefore gated 2.0.0 on something no reader of the spec could identify, and nothing tracked the remainder. | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium | FIXED | Escalated to the maintainer, who ruled: selection ships now, the execution half is filed as its OWN release blocker, and a gate belongs on a plan rather than a spec. Two review-ready plans authored (`ui8b9b` selection, `mng63x` execution, both `aw ipd lint` conforming and both carrying `- Blocks-Release: next` plus `- From-Spec: 6m4kow`); this spec's gate cleared through the setter. Section 0 carries the carrier table; Section 6 gains two honest limits. Recorded as D-101. |
| SR-104 | MEDIUM | IN-SCOPE | A. measured claims are current | R-04/A-03 say 34; `iter_review_files` returns 186 today; the implementing plan's own review measured 36 and recorded three conflicting figures | **A MOVING COUNT IS ASSERTED AS A FIXED ONE IN BOTH A REQUIREMENT AND A CRITERION.** Every plan-review adds a record, so 'the 34 existing review records' was already false when the implementing plan was reviewed (that review found 36 and flagged the same defect). A migration validated against a literal either fails for an unrelated reason or passes because someone edited the number. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | R-04 and A-03 now require the population to be DERIVED from `iter_review_files` at execution and validated as size-independent invariants (every record carries both fields, none retains the old one, the type value is in the closed vocabulary), with the three historical figures named so the discrepancy is not rediscovered. |
| SR-105 | MEDIUM | IN-SCOPE | F. honest limits are current and actionable | `aw find specs --status to-review`, `--status implemented`, and `--status bogusvalue` each return all 32 specs at exit 0; `cli._find_type_records`'s 'All other types' branch never reads `explicit_flags.status` | **A KNOWN BROKEN DEPENDENCY IS RECORDED AS 'BROKEN AT AUTHORING' WITH NO ROOT CAUSE AND NO OWNER, AND IT IS STILL BROKEN.** The filter silently ignores its argument, including for an invalid value. Root-caused here: the branch serving specs never consults the status filter, unlike the `plans` and `research` branches which each call a `query(...)` helper, so SEVEN record types are affected. The executed plan deliberately avoided it, and no backlog item tracks it, so the honest limit as written would age into folklore. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The limit rewritten with the re-measurement (including the invalid-value case, which shows the filter is ignored rather than merely wrong), the root cause, the seven-type blast radius, the executed plan's deliberate avoidance, and the fact that nothing tracks it. Recorded as an untracked gap rather than presented as handled. |
| SR-106 | MEDIUM | IN-SCOPE | D. decisions are recorded with rationale | Section 5 titled 'The one decision left to the graduating plan'; the ruling recorded in `.aw/system/workflows/spec-review/README.md` and dated 2026-09-04 | **A DECISION THE MAINTAINER MADE NINE DAYS AGO IS STILL PRESENTED AS OPEN.** R-10 defers the workflow-shape choice and Section 5 frames it as pending. It was ruled on the day the spec was authored (a separate `spec-review/` package, with the rejected option's measured cost and the accepted cost both recorded elsewhere). A spec that presents a settled decision as open invites re-litigation, which is exactly what the ruling's own record exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | R-10 carries the ruling and points at where its evidence and accepted cost live. Section 5 retitled 'SINCE DECIDED' and reframed as the reasoning the ruling weighed. New A-11 requires the decision to be recorded durably, so R-10 is covered rather than merely satisfied. |
| SR-107 | LOW | IN-SCOPE | A. measured claims; F. grandfathering | R-13 names 15 `implemented` + 5 `approved`; measured now 15 `implemented`, 7 `approved`, 1 `implementing` | **A GRANDFATHERING REQUIREMENT IS PINNED TO A POPULATION COUNT it must not depend on.** R-13 and Section 6 name 20 specs. Grandfathering must hold for whatever the population is, and stating it as a count both dates the requirement and obscures that the mechanism is structural (the authority table is consulted only at transition time) rather than a cutover list. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | R-13 rewritten to bind 'any spec already past `to-review` without a review record', with the structural mechanism stated and the counts demoted to dated context. The Section 6 limit rewritten the same way. |
| SR-108 | LOW | IN-SCOPE | A. sizing claim is current | re-measured: 6 plans and 4 specs at `to-review` (was 1 plan, 2 draft specs, 0 `to-review` specs) | **THE SIZING NOTE IS STALE IN THE DIRECTION THAT STRENGTHENS THE SPEC, which is worth correcting precisely because it is flattering.** The population is no longer near-empty, and this spec is now itself a member of the set it exists to make reviewable. Left uncorrected, a reader checking the claim finds it false and may distrust the surrounding argument, which is sound. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The note keeps its original measurement and gains the re-measurement, restating that the structural argument still carries the decision and that the volume argument remains the weaker one. |
| SR-109 | LOW | UNDER-SCOPE | F. honest limits | `review_findings.subject_gating_blocks` treating a parse diagnostic as BLOCKING; `plan_readiness.approval_refusals` keyed on the artifact's `- Id:`, which specs carry | **THE SPEC DOES NOT WARN THAT FILING A REVIEW RECORD ARMS A NO-OVERRIDE REFUSAL ON THE SPEC'S OWN APPROVAL.** An unfixed finding at or above the threshold, or a record that merely fails to PARSE, refuses `aw specs set approved` with no override by design. That is intended fail-closed behavior and it means a careless reviewer can block a maintainer's spec with a parse error rather than a finding. The implementing plan's review found this and called it the behavior an approver must know; the spec never absorbed it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to Section 6 as an honest limit: the attestation is only as strong as the record, and a malformed record refuses approval with a parse code rather than a finding. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-101 | R-15's operator surface is unreachable and this spec carried the release gate. Keep the gate, drop it, or move it? | ESCALATED TO THE MAINTAINER rather than decided. Their ruling: selection ships now, the execution half is filed as its OWN release blocker, and the gate belongs on a PLAN not a spec. Two plans authored; the spec's field cleared. | (a) Decide it myself by clearing the gate, rejected: retiring a release blocker is exactly the irreversible, human-owned call an agent must not make on its own authority. (b) Decide it myself by keeping the gate, rejected for the same reason in the other direction, and it would have added an unbounded blocker (registering `--type` means teaching a runner to dispatch a non-plan artifact). (c) Leave it unresolved and note it, rejected because the spec would keep gating the release on an unidentified remainder. | the maintainer's answers of 2026-09-13, verbatim: 'Keep the gate; R-15 must be operator-reachable before 2.0.0' with 'The gate should NOT be in the spec, it should be in an IPD or backlog and the gate should be released from the spec once that has been filed. I prefer plans to backlogs', then 'Selection now, and file the execution half as its own release blocker too' with 'HOW execution is implemented is something that needs discussion. Capture that fact loudly' | no |
| D-102 | Is a spec whose work has shipped still worth reviewing and approving, or should it be retired as historical? | REVIEW AND APPROVE IT. Add a status section rather than retiring. | (a) Retire as superseded by its own executed plans, rejected: a spec is the CONTRACT those plans were built against and two new plans cite it as `From-Spec`, so retiring it would strand four plans' provenance. (b) Leave it future-tense and approve anyway, rejected: approving prose that says the work is not implementable would make the approval assert something false. (c) Ask the maintainer, rejected: the repository answers it, since the specs README makes `implemented` the terminal state for shipped work and this spec is not there yet precisely because R-15 is outstanding. | `eyh1fu`/`5slbpi`/`wpomxa` carrying `- From-Spec: 6m4kow`; the new `ui8b9b`/`mng63x` doing the same; the spec status lifecycle in `.aw/records/specs/README.md` | yes |
| D-103 | The three uncovered MUSTs could be closed by adding criteria or by deleting the requirements as already-satisfied. Which? | ADD CRITERIA (A-09, A-10, A-11), and for R-15 make the criterion demand that the reachability LIMIT be stated. | (a) Delete R-05 and R-10 as satisfied, rejected: R-05 is a NEGATIVE requirement (the grammar must not change) and deleting it removes the guard against a future change, while R-10's value is the recorded decision. (b) Add a criterion for R-15 that simply asserts the sweep works, rejected as the overclaim this review is fixing: a criterion satisfied only at the function boundary must say so or a green result reads as a shipped feature. | `build_review_name` still delegating to the naming authority with the review facet; the R-10 ruling's record; the measured zero `--type` registrations | yes |

### Deferred and open

None. Nine findings, all FIXED; none deferred, none REPLAN, no question left open. The one decision that
was genuinely the maintainer's (D-101) was escalated and answered rather than resolved from evidence.

### Artifacts this review produced

- `.aw/records/plans/pending/20260913-specsweep-01-ui8b9b-...ipd.md` - R-15's selection half; carries
  `- Blocks-Release: next` and `- From-Spec: 6m4kow`; `aw ipd lint --phase author` conforming.
- `.aw/records/plans/pending/20260913-specdispatch-01-mng63x-...ipd.md` - R-15's execution half;
  DESIGN-FIRST by the maintainer's instruction, `- Scope-Paths:` deliberately TBD, its own OQ-01 being the
  design; carries `- Blocks-Release: next`, `- From-Spec: 6m4kow`, and `- Item-Dependencies: executed:ui8b9b`.

### Honest limits of this review

- IT IS A NEAR-SELF-REVIEW OF THE CAPABILITY IT USED. This spec specifies the spec-review workflow, and
  this review ran that workflow. That makes A-01 unusually well evidenced and makes any judgement about
  the workflow's own quality weaker than an independent one would be.
- I DID NOT VALIDATE THE THREE EXECUTED PLANS' WORK BEYOND THE SPEC'S CLAIMS. Section 0's table cites what
  I measured; it is not a `verify-execution` pass.
- NEITHER NEW PLAN IS EXECUTED, so R-15 remains outstanding. The gate moved; it was not satisfied.
