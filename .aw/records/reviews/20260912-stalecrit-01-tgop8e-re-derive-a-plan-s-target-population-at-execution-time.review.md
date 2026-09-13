# Review: re-derive a plan's target population at execution time instead of trusting an authored id list, child tgop8e (Set stalecrit)

- Subject-Id: tgop8e
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `3dd2047d`. Structural preflight `aw ipd lint --phase author --agent` CONFORMED (clean,
exit 0, 0 findings) before semantic review, and `--phase review-finalize` CONFORMED again after every
revision, so nothing here is structural. Suite measured BARE: `5971 passed, 3 skipped, 2 xfailed in
61.44s`. `aw sanitize --agent` clean (0 findings). No pre-review snapshot was needed: the target plan was
already committed and unmodified (`git status --porcelain` on it returned empty).

DISCLOSURE: this plan was authored hours earlier by the same model family in this repository, so treat it
as a near-self-review worth less than an independent one. Its value rests on what was EXECUTED rather
than re-read. Six things were driven rather than recalled, and four of them contradicted the plan.

THE PLAN'S THESIS IS CORRECT AND ITS CENTRAL PREMISE IS BACKWARDS. The thesis (a criterion naming a
population measured at authoring can be satisfied by doing nothing) is real, and the five plans E-07
names do all return zero today: `subject_gating_blocks` returns `()` for `4h7tt0`, `kbqpkn`, `5lxvl3`,
`y9vpvv` and `daexj1`, confirming F-1 exactly. But the plan reasons from there to "an executor finds
nothing to fix", and that does not hold. Re-derived across ALL 65 plans carrying a `- Finding:`
escalation, the predicate returns NON-EMPTY for four plans: `ki6tom` PR-201, `32ij2j` PR-016 and PR-017,
`xtklpd` PR-023, `yku4ga` PR-701. Reading each escalated question: `ki6tom` PR-201 and `yku4ga` PR-701
sit behind questions that are `- Status: resolved`, so they ARE the stale-bookkeeping defect E-07 exists
to close, live at review time; the other three sit behind questions still genuinely `open` and must not
be touched. So E-07 has real work, its authored list misses all of it, and E-02 was about to record
"zero is legitimately a pass, as it is today" as a decision resting on a falsified premise. That is
PR-002, the finding that most changes what an executor does.

THE MECHANICAL FACT THE PLAN NEEDED AND DID NOT HAVE. An `Expected outcome` line is OUTSIDE the frozen
requirement digest. `ipd_lifecycle._requirements_from_plan` freezes `Scope-Paths`, each E-leaf's `.text`
and each V-leaf's `.text`, and `ipd_lint.parse` puts an indented `- Key: value` sub-field in
`Leaf.fields` while `.text` is the action line alone. Measured: rewriting `qhy3i3` E-07's `Expected
outcome` left `frozen_region_digest` byte-identical (`d5380e65acf1a485` before and after), while editing
its action text DID change it. A V-leaf's frozen `.text` is likewise only its header (`V-07 validates
E-07`), so the `Required evidence:` sub-field where every real bar lives is outside the digest too. This
cuts both ways and both matter: the repair is provably safe against a frozen receipt, AND no gate reads
a criterion, which is what DECIDES E-03's open question about where to site the convention. `plan-review.md`
is now primary because review is the only enforcement surface that can exist; siting the rule in the
`ipd-spec` doc would put an unenforceable obligation in the document `aw ipd lint` implements.

TWO WHOLE SECTIONS BELONGED TO ANOTHER SET, AND THIS IS A RECURRENCE. `## Project conventions discovered
(Step 0)` and `## Deferred / out of scope` were BYTE-IDENTICAL to `wfartifacts` child `gzhd7t` (verified
by diffing the extracted sections): run-scratch relocation, D92, `.aw/.gitignore` anchoring,
`_ensure_aw_gitignore`, `install_into_repo`, `tools/untrack-workflow-artifacts.py`, backlog `2812t3`,
and a Set-wide "do not delete a user's committed run records" clause that also sat in this plan's GATE.
None of it describes this plan. The identical defect on the identical two sections from the identical
source Set was found and fixed on `4y95tp` (its PR-003) days earlier, so this is a copy habit rather
than a slip, recorded as F-8. Both sections were replaced with what review measured, and the gate's
inherited clause was replaced with a real scope fence.

THE AUTHORED COUNTS DID NOT REPRODUCE, THOUGH THE BOUND SURVIVED. The plan says "56 `Expected outcome`
lines across `pending/` carry a hardcoded count" and derives "the 52 criteria that count stable CODE
facts" from it, twice in metadata and twice in prose. Re-measured: `pending/` holds 690 such lines, 169
carrying a digit and 224 a spelled number, so the raw figure understates by roughly fourfold and the 52
never existed as a measurement. The BOUND does hold, which is why this is MEDIUM and not a REPLAN: of
the 17 criteria that count a plan/child/item population, most are an orchestrator counting its OWN
declared children (`cczotj` "all five children", `5lxvl3` "all ten children"), which is a fixed authored
fact rather than a drifting live one. That third class is the interesting one and the plan did not name
it, so V-03 now demands the convention be demonstrated on THREE cases rather than two.

A SECOND LIVE-ARTIFACT CRITERION EXISTS AND HAS ALREADY DRIFTED, which is the plan's own thesis proven
on an artifact it claims to exclude. `vhbvwz` E-02's criterion is "the 273 currently-mismatching plans
report correctly with zero files rewritten". Re-measured with the production readers
(`attention._history_section_lines`, `attention_contract.HISTORY_RECORD_RE`, `last_history_at`): it is
now 300 of 601 multi-record plans, not 273. Not swept in (another Set's approved plan) but recorded as
F-7 and as a named exclusion, so the claim "only `qhy3i3` counts live artifacts" is no longer stated as
true.

WHAT REVIEW SUPPLIED, stated plainly: the re-derived population that inverts the plan's framing and
gives E-07 real work; the digest measurement that both de-risks the repair and decides E-03's site; the
attestation guardrail for editing an APPROVED plan (`qhy3i3` carries a human `- Approval:` line, and its
`Status`/`Approval`/`Readiness` are other roles' outputs); a zero-is-a-pass rule that survives contact
with a broken query (report the DENOMINATOR, so a zero is corroborated); the two imported sections
replaced; the corrected counts; the third exemption class; and an `- Status: open` question whose own
body said it was resolved.

WHAT THE PLAN GOT RIGHT AND WAS PRESERVED: the diagnosis, the instruction/criterion asymmetry (E-07's
method is population-independent and only its bar is wrong), the refusal to delete the measured ids
rather than demote them to context, the refusal to add a dependency edge on `qhy3i3`, the refusal to
attempt a lint rule, and the insistence that E-06's empty board is not by itself evidence. All survive
unchanged.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | OVER-SCOPE | G. executability; evidence accuracy | `diff` of both extracted sections against `gzhd7t` returning nothing; `4y95tp`'s PR-003 | **Two whole sections and one gate clause were copied verbatim from an unrelated Set.** `## Project conventions discovered (Step 0)` and `## Deferred / out of scope` are byte-identical to `wfartifacts` child `gzhd7t` (run scratch, D92, `.aw/.gitignore` anchoring, `_ensure_aw_gitignore`, `install_into_repo`, backlog `2812t3`), and the gate carried that Set's "do not delete a user's committed run records" prohibition. Nothing in any of it touches this plan. An executor would either act on a defect that is not present or distrust the plan. The SAME defect on the SAME two sections from the SAME source was fixed on `4y95tp` days earlier, so it is a recurrence. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Conventions replaced with what review measured (the frozen-digest facts, the V-leaf text fact, `qhy3i3`'s approved status and absent receipt, the `subject_gating_blocks` signature). Deferred replaced with this plan's real exclusions. The gate's inherited clause replaced with a declared scope fence plus an attestation guardrail. Recurrence recorded as F-8. |
| PR-002 | HIGH | IN-SCOPE | A. Correctness; E. verification | re-derivation over all 65 plans carrying a `- Finding:` escalation; each escalated question's `- Status:` read | **The plan's central premise is inverted, and E-02 was about to record a decision resting on it.** The Concern reasons that because the five named plans return zero, "an executor finds nothing to fix". Measured: `subject_gating_blocks` is NON-EMPTY for four plans (`ki6tom` PR-201, `32ij2j` PR-016/PR-017, `xtklpd` PR-023, `yku4ga` PR-701). Two of them (`ki6tom` PR-201, `yku4ga` PR-701) sit behind RESOLVED questions and are therefore exactly E-07's live target; three sit behind still-`open` questions and must not be touched. So E-07 has real work its authored list misses entirely, and E-02's instruction to record "zero is legitimately a pass (as it is today)" would have written a falsified premise into an approved plan as a decision. | C:Low; U:Medium; S:Low; F:Medium-High; Overall:Medium | FIXED | Concern gains the re-derived measurement with the resolved/open split. E-01 must carry it into E-07's context as CONTEXT bearing the same re-derive instruction. E-02 rewritten: the zero rule is now "zero passes only when the DENOMINATOR is also reported", so a zero is corroborated by a non-zero examined-count and a broken query cannot masquerade as a clean repo; its expected outcome forbids resting on the falsified premise. V-02 fails the item if the recorded reason asserts it. |
| PR-003 | HIGH | UNDER-SCOPE | B. authorization of an attestation; D. anti-regression | `qhy3i3` `- Status: approved` with `- Approval: 2026-09-13`; `.aw/state/ipd-lifecycle/` holds 24 receipts, none for `qhy3i3`; `frozen_region_digest` measured before/after | **The plan edits an APPROVED plan carrying a human approval attestation and said nothing about the limits.** `AGENTS.md` forbids an agent writing another role's attestation field, and `Status`/`Approval`/`Readiness` are outputs of the human and of `/plan-review`. Nothing in the plan told the executor to leave them alone, to leave E-item action text alone, or to record the edit in the edited plan's history. Measured mitigation that makes this bounded rather than dangerous: an `Expected outcome` line is outside the frozen requirement digest (`d5380e65acf1a485` unchanged across the repair; changing the action text DID move it), and `qhy3i3` has no begin receipt at all, so no frozen contract can go stale. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-01 now requires a history record on `qhy3i3` attributing the change to `tgop8e` and forbids touching `Status`/`Approval`/`Readiness`. The gate carries a DO NOT ALTER ANOTHER ROLE'S ATTESTATION clause. V-01 demands the digest EQUAL before and after (a changed digest is a failed validation) and a `git diff` proving the three fields byte-unchanged. The digest and receipt facts are recorded in the conventions so a later reader does not re-derive them. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence accuracy | re-count over all 690 `Expected outcome` lines in `pending/` | **Both headline counts are wrong, and one was never a measurement.** The plan states "56 `Expected outcome` lines carry a hardcoded count" and derives "the 52 criteria that count stable CODE facts", the latter appearing in `- Scope:` as an exclusion. Measured: 690 such lines exist, 169 with a digit and 224 with a spelled number, so 56 understates roughly fourfold and 52 is not a figure any query produces. The BOUND survives (17 count a plan/child/item population; only `qhy3i3` and `vhbvwz` count live artifacts), which is why this is MEDIUM: the argument holds, the arithmetic did not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected in the Concern, `- Scope:`, F-6 and the Scope check. Every exclusion now names the CLASS (code facts, or an orchestrator's own declared children) rather than a count, so it cannot go stale the way the numbers did, which is this plan's own convention applied to itself. |
| PR-005 | MEDIUM | UNDER-SCOPE | C. architecture; F. KISS | `_requirements_from_plan` measurement; `ipd-spec` `- Status: implemented` | **E-03 deferred its only real design decision to the executor.** It offered two homes for the convention and said "choose ONE", leaving the highest-leverage choice in the plan unmade. It is decidable from evidence the plan already half-had: because an `Expected outcome` line is outside the frozen digest, NO gate reads it, so review is the only enforcement surface that can exist; siting the rule in the `ipd-spec` doc would assert an obligation `aw ipd lint` neither checks nor can check, and that spec is `Status: implemented`, making the edit a heavier amendment for less reach. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Decided in the plan: `plan-review.md` rubric section G is primary (beside the sibling requirement that validation items demand concrete evidence), with a one-sentence pointer in the `ipd-spec` doc. E-03, the spec-sync section and V-03 all state the choice and the mechanical reason. Recorded as D-1. |
| PR-006 | LOW | IN-SCOPE | G. executability; honest status | OQ-01's own body versus its `- Status:` field | **OQ-01 was `- Status: open` while its body says "Resolved from what the two plans actually do rather than asked" and reaches a firm answer.** The field contradicted the text, so `aw attention` would count a decided question as outstanding work on a plan whose whole subject is criteria that misreport reality. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `- Status: resolved` with a note recording why the authored value was wrong. Kept `- Blocking: no`; the answer and the no-dependency-edge reasoning are unchanged. |
| PR-007 | LOW | IN-SCOPE | Scope fence precision | `ipd_lifecycle._scope_match('.aw/records/specs/<file>', '.aw/records/specs/')` -> True | **The declared `- Scope-Paths:` entry `.aw/records/specs/` is a directory, so the fence permits editing any spec while E-03 needs exactly one.** Narrowing it would edit a `Scope-Paths` entry and move the frozen requirement digest, so the fix is a stated instruction rather than a metadata change. Separately, `runner_shared.declared_spec_paths` recognizes a spec only by the `.spec.md` facet, so a directory entry yields NO declared spec paths and the runner's pre-run spec-edit announcement will not name this amendment. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check records the width and why it is left as-is. The gate and the spec-sync section tell the executor to touch only the `ipd-spec` doc and to justify anything else with `--scope-reason` at finalize. V-03 requires the executor to state plainly that a spec was amended, since the announcement will not. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-03 left the convention's home open between the `ipd-spec` doc and `plan-review.md`. Which, and decide it or escalate? | `plan-review.md` rubric section G primary, one-sentence pointer in the `ipd-spec` doc. Decided at review rather than escalated. | (a) `ipd-spec` primary, rejected on the measurement: an `Expected outcome` line is outside `_requirements_from_plan`'s frozen digest, so no gate reads it, and siting the rule in the document `aw ipd lint` implements would assert an obligation the linter cannot check; that spec is also `Status: implemented`, a heavier amendment for less reach. (b) Both, rejected as the duplication the reporting-contract parity test exists to catch. (c) Leave the choice to the executor as authored, rejected because it is the plan's highest-leverage decision and is answerable from repository evidence, so asking an executor to guess it would strand the one thing E-03 delivers. | `frozen_region_digest` unchanged (`d5380e65acf1a485`) across an `Expected outcome` rewrite and changed across an action-text edit; `_requirements_from_plan` freezing only scope + E/V `.text`; `ipd-spec` `- Status: implemented`; `plan-review.md` rubric G already carrying the concrete-evidence sibling requirement | yes |
| D-2 | The re-derived population is non-empty (4 plans, 2 behind resolved questions), contradicting the plan's premise. Rewrite the plan's reasoning, or escalate to the maintainer? | REWRITE in place, and give E-07 the measured population as CONTEXT. | (a) Escalate as a blocking question, rejected: nothing here needs a human judgement, the predicate is shipped and its output is unambiguous, and blocking would strand a release-gated plan on a measurement anyone can re-run. (b) Leave the premise and only soften E-02's zero rule, rejected because the Concern's own argument would still read "an executor finds nothing to fix", which is false and is exactly the vacuous-criterion failure the plan exists to end. (c) Add the four plans as the new bar, rejected as repeating the original defect with a fresher list; they are recorded as context carrying a re-derive instruction. | `subject_gating_blocks` over all 65 plans carrying a `- Finding:` escalation; each escalated question's `- Status:` read (`ki6tom` OQ-02 resolved, `yku4ga` OQ-01 resolved, `32ij2j` OQ-04/OQ-05 open, `xtklpd` OQ-04 open) | yes |
| D-3 | `vhbvwz`'s live-artifact count has already drifted 273 -> 300. Sweep it into this plan, or exclude it? | EXCLUDE and NAME it (F-7 plus an explicit exclusion bullet). | (a) Sweep it in, rejected: `vhbvwz` is an approved plan in another Set, editing it here widens this plan's blast radius to a second Set's contract and its `Scope-Paths` does not cover it. (b) Say nothing, rejected because the plan asserts "only `qhy3i3` counts live artifacts" and that claim is false; leaving it would be the same evidence-accuracy defect this review is fixing elsewhere in the same plan. | re-measurement with `attention._history_section_lines` + `HISTORY_RECORD_RE` + `last_history_at`: 300 mismatching of 601 multi-record plans | yes |
| D-4 | Is editing an APPROVED plan's criteria legitimate at all, or must it be escalated? | LEGITIMATE, with guardrails, no escalation. | (a) Escalate for human permission, rejected on two measured grounds: the change is provably outside the frozen requirement digest, and `qhy3i3` has no begin receipt to invalidate, so nothing another party depends on moves; the maintainer also instructed this plan be filed for exactly this repair. (b) Supersede `qhy3i3` and re-author it, rejected as grossly disproportionate to fixing two criterion sentences in a plan that is otherwise correct and already approved. Guardrails added instead: no attestation field touched, no action text touched, digest equality proven, edit recorded in that plan's history. | `frozen_region_digest` equality measurement; absence of `.aw/state/ipd-lifecycle/qhy3i3.receipt.json` among 24 receipts; `AGENTS.md`'s never-write-another-role's-attestation rule | yes |

### Deferred and open

None. Every finding was FIXED in place; none deferred, none REPLAN, no question left open (OQ-01 was
resolved from evidence and its status corrected).
