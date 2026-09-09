# Review: decide the unit a model attaches to, child btot17 (Set actmodel)

- Subject-Id: btot17
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `7e633c74`. Structural preflight `aw ipd lint --phase author --agent` returned
`"outcome":"clean","findings":0` before any semantic work, and `--phase review-finalize` conforms clean
after the revisions.

DISCLOSURE: authored by the same agent/model in an adjacent session, so this is effectively a
self-review. The cost is concentrated in PR-901 and PR-908 and is the same failure in two sizes: the
plan INHERITED sibling measurements instead of re-deriving them, while asserting in its own prose that
it had "re-verified at HEAD by symbol rather than by remembered line". Both the stale line number and
the stale plan status came from `m7gvuz`'s round-2 findings table, quoted forward as current.

THE VERDICT AND READINESS CHANGED MID-REVIEW BECAUSE THE MAINTAINER RULED WHILE IT WAS RUNNING, and the
sequence is recorded because it explains the record. Round 1 concluded `REVIEWED - OPEN QUESTIONS` /
`no-go`, correctly: all nine findings were fixed, but OQ-01 was `- Blocking: yes` and owned by the
maintainer, which the readiness vocabulary treats as a genuine not-ready condition. Between that
conclusion and this record being committed, the maintainer committed `93703697` ("plan(actmodel,
actorparen): record maintainer OQ rulings"), which RESOLVED OQ-01 and opened a new non-blocking OQ-05.
No blocking question remains, so the honest verdict is `APPROVE WITH REVISIONS APPLIED` and the
readiness is `go-pending-approval`. See D-4 and D-5.

THE RULING CONVERTED THIS FROM A DECISION PLAN INTO A BUILD PLAN, and it did so by rejecting the
premise this plan was built on rather than by picking one of its options. The maintainer's words:
"It is NOT about just getting a cheap model. It's about getting the best model for the job. Writing
prose? Sonnet 5. Writing code? Opus 5. ..." That reframes the whole item from COST CONTROL to FITNESS
FOR TASK, and three consequences follow that I had to apply across the plan: the unit is a validated
ROLE (the maintainer's categories are kinds of work, not step names), the "decide and defer" outcome is
STRUCK (a cost bound cannot justify deferring a quality fix that benefits every run), and E-02's
extensibility count stops being the discriminator. Notably the ruling ALSO independently reached the
`verify_with` EXTEND disposition that PR-905 had forced the plan to confront, which is corroboration
that the finding was pointed at the right question.

THE PROBLEM IS REAL AND THE PLAN'S SHAPE IS RIGHT. A decision plan is the correct response to a
"decided-but-unscoped design question", the four questions are the right four, the E/V structure is
sound, the deferral outcome is honestly presented as a legitimate completion rather than a failure, and
the fence against building before the unit is chosen is exactly right. Everything wrong here is
FACTUAL: the plan describes a world that had already changed.

WHAT ROUND 1 CHANGED. Nine findings, ALL FIXED in place, one BLOCKER. No E-item was added or removed:
the five were the right decomposition, and every repair re-aimed an existing item at the state that
actually exists. OQ-01 was RE-FRAMED rather than resolved, because its original framing rested on the
false premise and its replacement is still not agent-resolvable.

THE BLOCKER IS THAT THE PLAN'S CENTRAL PREMISE WAS FALSE WHEN IT WAS WRITTEN, AND THE PLAN ITSELF SAID
WHAT TO DO ABOUT IT. `kgpptv` is `executed`, not "approved and unexecuted", and its `verify_with` field
has shipped: a per-role model preference with the chain `explicit --verify-with > profile's own
verify_with > defaults.verify_with > ABSENT`, a deliberate `SCHEMA_VERSION` 1 -> 2 bump recorded as
DECISION 06-kgpptv-D2, and a load-time refusal of a dangling reference. The plan's E-01 had already
written the contingency in as many words: if `kgpptv` has executed, the question "changes from 'should a
general mechanism subsume it' to 'should a general mechanism absorb a shipped special case', which is a
harder and different design problem", and the executor should "report rather than proceeding on the
authored assumption". So the plan was correct about the risk and wrong about the fact, and an executor
following it would have spent E-01 discovering that its own premise was void.

WHY THE ERROR SURVIVED AUTHORING IS WORTH RECORDING, because it is reusable. The motivating measurement
is `grep role agent_workflows/runner_profiles.py` -> zero, which is TRUE at HEAD. But the shipped
mechanism does not use the word `role`; it is called `verify_with`. A term search cannot establish the
absence of a capability, and here it produced a confident zero for a feature sitting three lines away in
`ALLOWED_PROFILE_KEYS`.

TWO FURTHER FINDINGS CHANGE RECOMMENDATIONS RATHER THAN FACTS. OQ-03 recommended "warn and fall back,
never fail the run" for an unprovidable model, which directly contradicts `_validate_verify_reference`'s
load-time refusal, and the code gives a reason the plan never engages: a silent fallback means the
operator "would believe an independent model verified the work when the same model did". That splits
cleanly into a configuration error (refuse, cheap, knowable at load) and a runtime unavailability (warn,
because refusing wastes a queue for no safety gain), and the plan now says both. And E-05 would have
added a new field beside a shipped public key with no instruction about it, so it now demands an
explicit extend/supersede/layer disposition, citing the module's own argument that two switches for one
behavior is the defect to avoid.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | BLOCKER | IN-SCOPE | Evidence accuracy; G. executability | `.aw/records/plans/executed/20260905-runprofile-06-kgpptv-...ipd.md:12` `- Status: executed`; `ALLOWED_PROFILE_KEYS` contains `verify_with`; the plan's own E-01 contingency clause | **The plan's central premise was false at authoring time, and the plan itself specified the remedy it did not apply.** `kgpptv` is EXECUTED and `verify_with` has SHIPPED: a per-role model preference with a documented precedence chain, a deliberate `SCHEMA_VERSION` 1 -> 2 bump (DECISION 06-kgpptv-D2), and a load-time refusal of a dangling reference. The plan asserts `- Status: approved`, unexecuted, in the Concern, the conventions, F-3, F-4 and OQ-01, and builds OQ-01's blocking rationale on "the answer determines whether that plan should be executed as-is, re-scoped, or retired". E-01 had already written the contingency: if `kgpptv` has executed, the design problem "changes from 'should a general mechanism subsume it' to 'should a general mechanism absorb a shipped special case'" and the executor must report rather than proceed. An executor would have spent E-01 discovering the plan's premise was void | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Concern rewritten around the shipped mechanism; E-01 re-aimed from re-measuring a gap to DOCUMENTING the shipped baseline (chain, reference-not-string, version bump, dangling refusal) plus what is genuinely still absent; OQ-01 re-framed to the harder question with an explicit extend/supersede/layer choice; F-3 rewritten as BLOCKER; conventions, Deferred, doc-sync and the gate all corrected; `Finding: PR-901` added to OQ-01 |
| PR-902 | HIGH | IN-SCOPE | Evidence accuracy; D. invariants | `grep -c role agent_workflows/runner_profiles.py` -> 0, beside `verify_with` in `ALLOWED_PROFILE_KEYS` | **The measurement that motivated the whole item is a vocabulary artifact.** Zero `role` occurrences is true and misleading: the shipped mechanism spells the concept `verify_with`. So the Concern's "no action can choose a cheaper model" is false as written; one role can, by name. A term search cannot establish the absence of a capability, and this one returned a confident zero for a feature three lines from the grep target | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-4 states the artifact explicitly; the Concern now distinguishes the vocabulary gap from the capability gap; the conventions' lead bullet rewritten from "THERE IS NO ROLE CONCEPT" to name the distinction |
| PR-903 | HIGH | IN-SCOPE | Evidence accuracy; C. architecture | `grep -c "runner_profiles\|resolve_launch_profile\|launch_profile" agent_workflows/agy_runipd.py` -> 0; `tm2cz8` `- Status: executed` | **The plan inverts a premise: it claims the oc-only limitation is now FALSE, and it is TRUE.** `tm2cz8` executed and `RUNNER_REGISTRY` does carry an `agy` row, but the agy driver reads no profiles at all, so a profile naming `runner: agy` resolves and no agy run consumes it. The plan's conclusion that "any per-action design must be cross-host from the outset" is therefore derived from a fact that is not true. Whether to build cross-host first is a real question; it is not settled this way | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 rewritten with the measurement; the Concern states the registry-row-is-not-an-integration distinction; the Deferred entry corrected from "missing provenance record" to "no integration exists" |
| PR-904 | HIGH | IN-SCOPE | A. correctness; B. integrity | `runner_profiles._validate_verify_reference` docstring | **OQ-03's resolution contradicts shipped behavior and never engages the code's stated reason.** The plan recommends "warn and fall back; do not fail the run" for an unprovidable model, but a dangling `verify_with` is REFUSED at load time because a silent fallback means the operator "would believe an independent model verified the work when the same model did. That is worse than a dangling default, because the failure is invisible in the result rather than visible in the bill." A new mechanism recommending laxity beside a shipped one that fails closed needs a reason, and the plan offers none because it did not know | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | OQ-03 split into (A) unresolvable reference -> REFUSE at load, quoting the code's reason, and (B) resolved profile whose model the host cannot provide at launch -> warn and fall back, with the configuration-error versus runtime-unavailability distinction stated; E-03 rewritten to demand both cases; required-tests now demands a test per case with opposite outcomes; F-6 added |
| PR-905 | HIGH | UNDER-SCOPE | C. architecture; G. executability | `ALLOWED_PROFILE_KEYS`; the module docstring's two-switches-for-one-behavior argument | **E-05 would have added a preference field beside a shipped public key with no instruction about it.** Under either building outcome the plan says to add a role enum or an action map to the same schema that already carries `verify_with`, without saying whether the new field extends, supersedes, or sits beside it. Silently layering is the outcome the module's own docstring argues against, and it would leave an operator with two fields and no stated precedence between them | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-05 now requires an explicit EXTEND / SUPERSEDE / LAYER disposition with its reason, and a schema-version decision citing DECISION 06-kgpptv-D2 rather than re-deriving it; a new Deferred entry forbids actually removing or renaming `verify_with` in this plan; F-13 records that `verify_with`'s reference design resists the open-action-key option; V-05 demands the disposition and the compatibility tests |
| PR-906 | MEDIUM | IN-SCOPE | Evidence accuracy | `m7gvuz` `- Status: approved`, `8tgg6g` `- Status: reviewed`, both unexecuted; `m7gvuz` OQ-01 | The plan calls question 4 "the one question with a concrete substrate", but the verdict store and its answering-model field do not exist: both owning plans are unexecuted and the field is a design intent in `m7gvuz`'s OQ-01. The recommendation is a forward commitment on a store yet to be built, which is fine to make and wrong to describe as grounded in existing data | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 states the substrate is planned rather than present with both statuses; OQ-04 carries the correction; F-9 added; V-04 requires the status evidence plus a search for the store |
| PR-907 | MEDIUM | IN-SCOPE | Evidence accuracy | `m7gvuz` OQ-01..OQ-03, all `- Blocking: no` / `- Status: resolved` | The plan twice describes `m7gvuz` as carrying "its own blocking questions", which would make the motivating consumer doubly remote. All three of its open questions are resolved and non-blocking; it is approved and simply not yet run. The error understates how close the motivating case is to becoming real | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and the conventions corrected to "approved and unexecuted, questions resolved"; F-10 added; V-02 requires the prospective-not-blocked phrasing |
| PR-908 | MEDIUM | IN-SCOPE | Evidence accuracy | `grep -n "def resolve_launch_profile"` -> `oc_runipd.py:2613` | **The plan's own citation was stale at authoring while it claimed to have re-verified by symbol.** It cites `:2702` (inherited from `m7gvuz`'s round 2) in the Concern, the conventions and F-1/F-2, and builds F-2 into a lecture about line drift. The function is at `:2613`. The plan preaches the discipline it did not follow, which is the same inheritance failure as PR-901 in miniature | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every citation corrected to `:2613`; F-2 rewritten to name the plan's own lapse rather than the item's; the execution contract now cites this plan's error as the demonstration and adds a standing instruction to treat every sibling-status claim in the document as dated |
| PR-909 | LOW | IN-SCOPE | E. testing | bare `python3 -m pytest` at HEAD `7e633c74` -> `1 failed, 5866 passed, 3 skipped, 2 xfailed` | The stated baseline `1 failed, 5648 passed` is wrong by 218 passes, and the failing test is `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (untracked `opencode-recovery/` files), not identified in the plan. An executor judging on the delta would see unexplained drift | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required-tests carries the measured baseline with the failing test named and its unrelated cause; instruction to re-baseline in the executor's own tree; F-16 added |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's premise is void because `kgpptv` shipped. Re-aim it in place, or mark REPLAN and require a fresh plan? | Re-aim in place: the SHAPE (a decision plan, four questions, evidence-then-ruling, deferral as a legitimate outcome) is correct and only the facts were wrong | REPLAN (rejected: the E/V structure, the fence, and three of four questions survive intact, so a rewrite would reproduce them); leave the premise and let E-01 discover it (rejected: the plan's own E-01 says to report and re-scope, so leaving it would knowingly hand an executor a void premise) | The plan's E-01 already specified the re-scope for exactly this condition, so applying it is executing the plan's own instruction rather than substituting reviewer judgement; findings repairable with bounded edits do not meet the REPLAN bar | yes |
| D-2 | OQ-01's original framing (does a general mechanism subsume a pending `kgpptv`) is void. Resolve it, or re-frame and keep it blocking? | Re-frame and keep `Blocking: yes`, owned by the maintainer | Resolve it myself now that one role is served (rejected: choosing the unit still commits the repository to a schema shape and to a shipped public key's fate, which is not a reviewer's call); drop it as moot (rejected: the underlying question is not moot, it got harder) | The item reserved question 1 deliberately; the new question additionally disposes of `verify_with`, a public key in a versioned on-disk schema, which is a compatibility commitment a maintainer must make | yes |
| D-3 | OQ-03 recommended warn-and-fall-back, which shipped code contradicts. Overturn the recommendation, or split the question? | Split: refuse an unresolvable reference (matching shipped behavior), warn and fall back on an unprovidable-model-at-launch | Overturn wholesale to always-refuse (rejected: refusing mid-run wastes a queue for no safety gain, and the item's cost reasoning is sound for that case); keep warn-and-fall-back for both (rejected: it would make a new mechanism laxer than the shipped one beside it, defeating the integrity check's stated purpose) | `_validate_verify_reference`'s docstring gives the integrity reason for the load-time refusal; the two cases differ in whether the fault is knowable and fixable before the run starts | yes |
| D-4 | Should readiness be `no-go` or `go-pending-approval` given all findings are fixed? | `no-go` AT ROUND 1, superseded by D-5 once the maintainer ruled | `go-pending-approval` (rejected AT THE TIME: the workflow reserves it for a plan with NO open questions, and OQ-01 was then deliberately `Blocking: yes`) | The readiness vocabulary makes an open blocking question a genuine not-ready condition; recording `go-pending-approval` while a plan awaited a ruling would misreport it, and the auto-approve predicate reads this field | yes |
| D-5 | The maintainer resolved OQ-01 in commit `93703697` while this review was running, and their commit also swept in my in-progress plan edits. Re-review from scratch, keep `no-go`, or reconcile and update? | Reconcile: keep the nine findings, apply the ruling through the plan (E-02 re-aimed off the struck cost framing, E-05 reduced to the chosen EXTEND path, four residual deferral references corrected, gate rewritten), and update verdict/readiness to `APPROVE WITH REVISIONS APPLIED` / `go-pending-approval` | Keep `no-go` (rejected: it would be FALSE, since no blocking question remains, and the field is machine-read by the auto-approve predicate, so a stale `no-go` would suppress a plan the maintainer just cleared); re-review from scratch (rejected: the findings and their repairs remain valid and the ruling corroborates PR-905 rather than contradicting anything) | OQ-01 now reads `- Blocking: no` / `- Status: resolved` with the ruling recorded inline; the surviving OQ-05 is `- Blocking: no` by the maintainer's explicit "pairing recorded as the next step" choice; `aw ipd lint --phase review-finalize` conforms after the reconciliation | yes |
| D-6 | The maintainer's commit left the plan mixing my review's decision-plan framing with their build ruling (E-02 still turning on an extensibility count, E-05 still offering three dispositions and a struck deferral, four deferral references, a gate announcing a blocking question). Leave the contradictions for the executor, or resolve them? | Resolve them in favor of the ruling, and say in the plan that where the two disagree the ruling wins | Leave them (rejected: an executor meeting E-05's "the ruling must name one" after the ruling already named EXTEND would either re-decide a settled question or stall); revert the maintainer's merge and re-apply cleanly (rejected: never revert a co-worker's committed work) | The ruling is the later and higher authority, is recorded inline in OQ-01, and explicitly strikes the deferral outcome and the cost framing; leaving both readings in one document is the ambiguity plan-review exists to remove | yes |
