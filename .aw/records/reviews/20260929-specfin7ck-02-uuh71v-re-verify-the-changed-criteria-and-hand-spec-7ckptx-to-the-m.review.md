# Review findings: plan uuh71v

- Subject-Id: uuh71v
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `f25eb2fa` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent` conforms after.
`IPD-S407` does not apply: the plan's own first `- Kind:` bullet reads `child`. No pre-review snapshot was
owed: `git status --porcelain` was empty at review start.

NO PRODUCTION FILE AND NO SPEC WAS MODIFIED BY THIS REVIEW. Every measurement was a read, a library call, or
a read-only verb (`aw find`, `aw check`, `aw attention`, `aw specs check`, `git diff`, `python3 -m pytest`).
NO `aw spec set` was run, so spec `7ckptx` still reads `approved` at its original path, exactly as it did
before this review. The only writes were to this plan and this record.

THIS PLAN IS UNUSUALLY GOOD AT THE THING THAT MATTERS MOST HERE: it refuses to inherit its own backlog item's
false premise, and it is RIGHT to. I verified the correction mechanically rather than taking its word:

- **F-2, the plan's central correction.** `TRANSITION_AUTHORITY["->implemented"]` is
  `{'who': 'executor', 'by_human': False, 'human_token': False, 'evidence': True}`, while the
  `by_human`/`human_token` gate sits on `->approved`
  (`{'who': 'human', 'by_human': True, 'human_token': True, 'evidence': False}`). So the item's claim that an
  agent is MECHANICALLY barred from `implemented` is false, and the plan's reading (a POLICY floor in
  AGENTS.md above a permissive mechanism) is correct. Honoring the policy while naming the distinction is the
  honest treatment.
- **F-5.** `SPEC_TRANSITIONS['approved']` = `{implementing, reviewed, superseded, parked, deferred}`, with
  `implemented` absent; `SPEC_TRANSITIONS['implementing']` contains `implemented`. The two-step really is
  forced by the table.
- **F-1.** `_SPEC_MAP`: approved -> `ready`, implementing -> `active`, implemented -> `done`. `aw attention`
  emits `native_status= approved  attention_class= ready` for this spec, the exact misreport claimed.
- **F-4 and E-01's counts, measured to the id.** Section 4 holds 36 distinct `A*` ids, 5 WITHDRAWN
  (A7b, A7b-1, A7b-2, A7b-3, A7c), 31 LIVE. The spec defines 43 distinct `R*` ids including the
  letter-suffixed ones, so E-01's correction of backlog `eozq91`'s "42" is right. (Worth noting for the
  executor: a regex that misses the `-N` suffixed ids yields 33, not 36; the plan's number is the correct one.)
- **F-3, the staleness that justifies the whole plan.** The spec history contains both amendments verbatim:
  2026-09-18 ("R5.5's refusal on unknown ignored files is removed ... A15 updated accordingly") and
  2026-09-25 (`xzroy8`, R5.1a). `4fodkt` verified at `e299a9a5`, which predates both.
- **The diff mechanics E-02 depends on.** `git diff e299a9a5 HEAD` over BOTH spec paths works and reports
  `35 insertions, 11 deletions`; commit `2fa65732` is the move, as the plan says.
- **F-6, F-7 and the standing facts.** All 8 `lanectn` plans read `Status: executed` in
  `.aw/records/plans/executed/`; `nvymif` is `open`; `i4y84y`, `vqv9im` and `eozq91` are `graduated`;
  `aw specs check` reports "all specs conform"; OQ-03 is `Status: deferred` with
  `Owner: the implementing plan`; the suite is green at `3312 passed, 2 skipped, 3 warnings`.
- **The Step 0 path-declaration reasoning.** `check.scope-path-target-stale` is a real registered rule that
  fires elsewhere in this repo and does NOT fire against this plan, so declaring only the CURRENT spec path
  is the correct choice.
- **`aw spec set` spelling.** The verb exists with `--graduated-to` and `--evidence`, as E-06 spells it.

I found nothing wrong with the plan's scoping, its stopping point, or its three original open questions. All
three findings below ADD to the packet rather than faulting the approach.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | MEDIUM | UNDER-SCOPE | G (executability: assumptions and ownership); F (UX: decision-readiness) | the spec's front matter `- Blocks-Release: next`; `aw find releases` -> single `planned` record `f33nrj` (2.0.0); `grep -c Blocks-Release` on the plan -> 1, that one being adjacent item `i4y84y`; backlog `eozq91` carries no gate; `aw check release-gates` exits 0 | **THE SPEC THIS PLAN TRANSITIONS IS ITSELF A RELEASE BLOCKER, AND THE PLAN NEVER SAYS SO.** It discusses release gates only for adjacent item `i4y84y` (F-6) and nowhere records that `7ckptx` carries `- Blocks-Release: next`, resolving to the `planned` 2.0.0 release. This is the single most decision-relevant fact in a packet whose entire purpose is to let a maintainer decide `-> implemented`: it converts the question from bookkeeping into "does 2.0.0 ship?". A packet that omits it asks a maintainer to close a release gate without telling them one exists, which is precisely the one-sidedness the plan's own OQ-03 and V-05 exist to prevent. NOT a metadata defect: AGENTS.md's inheritance rule keys on the BACKLOG item's gate and `eozq91` has none, and nothing is mechanically violated. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-8; E-05 must confirm the gate at HEAD and resolve it to its release record; E-06 must state it prominently in the packet; V-05 and V-06 require it as evidence; the gate carries the instruction; OQ-04 records why no `- Blocks-Release:` field was added to the plan. |
| PR-402 | MEDIUM | IN-SCOPE | E (verification method); G (executability) | `git diff e299a9a5 HEAD -- '.agents/specs/*7ckptx*' '.aw/records/specs/*7ckptx*'`; `grep '^[+-]- A'` over it returns ONLY the A15 pair; the A12b hunk shows `- ...NEW REVISION. Also` replaced by `+ ...NEW REVISION, and, for a shared lane, that each turn's attachment resolves to its own revision when turns are dispatched out of position order.` | **THE PLAN'S DELTA OF EXACTLY TWO IS CORRECT, BUT THE OBVIOUS WAY TO COMPUTE IT YIELDS ONE.** A15's criterion line changes directly; A12b's amendment lands on CONTINUATION lines while its `- A12b.` label sits on an unchanged leading line. So an executor following E-02's instruction to "enumerate every criterion whose text changed" by grepping the diff for changed criterion labels finds A15 alone, concludes the delta is one, and silently carries A12b forward as unchanged, skipping E-04 entirely. The plan's whole defense of a targeted re-verification (OQ-02: the delta is falsifiable because diff-computed) depends on the enumeration being done correctly. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-10; E-02 now requires hunk-level attribution and names the trap with the measured evidence; V-02 states that a delta reporting only A15 is a FAILURE of the item rather than a smaller delta; the gate repeats it. |
| PR-403 | LOW | IN-SCOPE | C (use canonical mechanisms); D (repository consistency) | `aw check --agent` diagnostics report `check.plan-spec-link-missing` for this plan and for Order 01; `check_engine` registers the rule at `"info"`; AGENTS.md: "let the advisory `check.plan-spec-link-missing` rule nudge when a pending plan cites a spec without carrying the link" | A LIVE (if advisory) CHECK FINDING STOOD AGAINST THIS PLAN: it cites spec `7ckptx` throughout while carrying no `- From-Spec:` field. Severity is `info` so it gates nothing, but a plan whose entire subject is one spec's lifecycle is the clearest possible case for carrying the machine-readable link, and leaving it unset in a plan handed to a maintainer as an evidence packet is avoidable noise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set via the tooled verb `aw ipd set to-review uuh71v --from-spec 7ckptx` and verified cleared in a re-run of `aw check`. Order 01's identical finding was deliberately NOT touched (it owns its own front matter). Recorded as F-9. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Does the spec's own `- Blocks-Release: next` change what this plan may DO, or only what its packet must SAY? | Only what the packet must say: disclose the gate, transition as planned | (a) HOLD the plan until the release question is settled, REJECTED because `approved -> implementing` asserts work is in progress, which is true regardless of any release decision, and leaving the spec `approved` preserves the exact `attention_class: ready` misreport the source item filed; the transition strictly improves the record. (b) INHERIT the gate onto this plan's front matter, REJECTED because AGENTS.md keys that obligation on the BACKLOG item's gate and `eozq91` carries none, so writing one would assert a gate no source conferred, and `aw check release-gates` exits 0 | The field's meaning (the spec must be done before 2.0.0 ships) makes the `-> implemented` judgement a release judgement, so disclosure is what the gate demands; measured `- Blocks-Release: next` on the spec, `f33nrj` as the single `planned` release, and no gate on `eozq91` | yes |
| D-2 | Is the plan's claim of a two-criterion delta actually correct, or did it over-report? | Correct: A12b and A15 both changed. The risk is the reverse, an executor UNDER-reporting to one | (a) Treat the plan as over-reporting and narrow the delta to A15, REJECTED after reading the hunks: A12b's text demonstrably changed, gaining the out-of-position dispatch clause E-04 exists to demonstrate. (b) Leave E-02's method as written, REJECTED because the natural label-grep implementation silently drops A12b, which would skip E-04 and carry an undemonstrated amended criterion into the packet | Read every hunk of `git diff e299a9a5 HEAD` over both paths; A12b's replacement text is visible while its label is not on any changed line, and `grep '^[+-]- A'` returns the A15 pair alone | yes |
| D-3 | Are the plan's three original open questions (OQ-01 policy floor, OQ-02 targeted re-verification, OQ-03 recommend-against-if-unverified) correctly resolved? | Yes, all three left exactly as authored | (a) Reopen OQ-01 to let the plan set `implemented`, REJECTED: AGENTS.md withholds it and `APPROVAL_FLOOR` (verified present) records that the evidence check tests "presence + format + resolvability, NOT semantic verification", so passing the gate would prove nothing about satisfaction. (b) Reopen OQ-02 to demand all 31 criteria be re-run, REJECTED: the live/withdrawn split is identical at both HEADs (verified 36/5/31), the delta is diff-computed, and V-06 forces every carried-forward criterion to be LABELED as the weaker claim, which is the disclosure that makes the limit safe | Verified `APPROVAL_FLOOR`'s wording, the identical criterion split, and that `4fodkt` set the same stopping-point precedent ("NO TRANSITION performed on spec 7ckptx") | yes |
| D-4 | Should the advisory `check.plan-spec-link-missing` on Order 01 (`e9ekuj`) be fixed here too? | No. Fix only this plan's field and leave Order 01's to Order 01 | (a) Fix both, REJECTED: Order 01 is a separate `reviewed` plan under a different review, its front matter is not this plan's `Scope-Paths`, and editing a sibling's metadata during this plan's review would sweep another artifact's provenance into this commit. (b) Fix neither, REJECTED: the finding is live against the plan under review and the remedy is one tooled command that AGENTS.md itself names | `aw check --agent` reports the rule for both plans; the rule is `info`; the remedy `aw ipd set ... --from-spec` is the documented one and was verified to clear the finding for this plan only | yes |

No `Reversible: no` decision was taken, so no escalation is owed. No finding was left `OPEN` or `DEFERRED`,
so no `- Blocking: yes` escalation is owed either.
