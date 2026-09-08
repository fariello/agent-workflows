- Id: rxya25
- Status: graduated
- Set: rxya25
- Priority: high
- Work-Kind: feature
- Summary: configurable per-transition policy for how far automation may advance an artifact through the lifecycle

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan u06zo2 (Set lcpolicy, .aw/records/plans/pending/20260908-lcpolicy-01-u06zo2-...ipd.md), which carries From-Backlog: rxya25. This item carries no Blocks-Release, so the plan inherits none. Status graduated (design handed off), NOT done. THE PLAN PRODUCES A SPEC, NOT CODE, and that shape is deliberate: this item is a MAINTAINER REQUIREMENT carrying FIVE unanswered design questions, and one of them (what is the default) this item itself notes 'would immediately break --full-auto unless it ships with a permissive default for the transitions it already performs'. A plan that implemented a policy engine would have to answer all five by fiat, which is precisely the hardcoding this item exists to end, so it would add a sixth hardcoded opinion beside the five it is meant to consolidate. aw specs new exists and mints a conforming spec, so spec-first is a tooled route. NOTHING IN THIS ITEM IS OBSOLETE and nothing covers it: grepping the specs tree and every pending plan for a lifecycle-automation policy or a per-transition permission model returns nothing. THE FIRST CONSUMER HAS SINCE LANDED, WHICH SHARPENS THIS ITEM RATHER THAN CLOSING IT: 97df1z (fullauto-01) is now EXECUTED, so the --full-auto path that decides 'may I advance this reviewed plan to ready-to-execute without a human?' is SHIPPED and is answering that question by hardcoding today. This item's premise that 97df1z 'is the FIRST CONSUMER of a policy that does not exist' is therefore now a LIVE condition rather than an anticipated one, and it converts the default question from theoretical to breaking: the plan's BLOCKING open question OQ-01 asks the maintainer to choose, and recommends fail-closed WITH an explicit grandfather list naming exactly the transitions --full-auto performs today, because that is the only option that is both fail-closed (matching this repository's posture everywhere else) and non-breaking, and the grandfather list doubles as the inventory the plan produces anyway. ALL THE REUSABLE MATERIAL THIS ITEM CITES VERIFIES at HEAD a2e0438a: the honest-attestation precedent is real AND ENFORCED (auto-approved is a sibling ready-to-execute tier at ipd_schema.py:267, READY_TO_EXECUTE = frozenset(('approved','auto-approved')), documented at :265-266 as 'an automated clear, NOT human approval', and :396-402 enforces that only approved carries the human Approval field, so auto-approved cannot masquerade as human sign-off); the shared-predicate pattern is real (check_engine.evaluate_blocking_close at :1951, which backs the backlog setter, the aw check rules and the opt-in pre-commit hook so they provably cannot diverge); and the config home exists (.aw/config/project.json plus a resolved user config path). ONE ADDITIONAL PRECEDENT FOUND THAT THIS ITEM DOES NOT NAME, and it matters because it means a per-transition authority model already exists to extend rather than duplicate: attention_contract.TRANSITION_AUTHORITY, introduced by the IMPLEMENTED spec 20260815-0151-01-honest-human-approval-attestation.spec.md, which is also the closest prior art in shape (it reframed a human-only TTY gate into an honest non-TTY attestation, the same move this policy needs for automated advances). The plan requires the spec to extend BOTH auto-approved and TRANSITION_AUTHORITY by name, and to forbid any policy-permitted automated advance from being indistinguishable from a human's, which is this item's own question 4 answered in the affirmative and is the property that makes the audit trail trustworthy. The plan takes the spec to to-review and NOT to approved, because the five answers are proposals until the maintainer attests them with --by-human, and it requires the spec to state that it authorizes no code change so a later executor cannot read it as licence to build. Implementation is explicitly a follow-on Set graduated FROM the approved spec, and the migration sequencing (all verbs at once, or the --full-auto path first) is itself left to the spec rather than presumed.
- 2026-08-31 created (aw backlog): configurable per-transition policy for how far automation may advance an artifact through the lifecycle

MAINTAINER REQUIREMENT recorded 2026-08-31 while resolving `97df1z` (fullauto-01) OQ-02. Filed separately because it spans every lifecycle verb and is far larger than the plan that surfaced it.

## What is wanted

A CONFIGURABLE, ARGUMENT-OVERRIDABLE policy deciding how far automation may advance an artifact along the WHOLE pipeline:

    backlog -> backlog-review -> graduate to IPD -> to-review -> reviewed -> approved -> executed

The configuration decides, PER TRANSITION, what conditions still permit moving forward. It is not a single on/off switch and not `--full-auto` generalized: each hop has its own risk profile, so each needs its own predicate.

The maintainer's worked example: is it acceptable to advance an artifact carrying an unanswered OPEN QUESTION that the "try harder before refusing" rule (DECISIONS D148) could not resolve into a strong recommendation? Today that is hardcoded per verb, differently in each, rather than being one policy a maintainer can set and an argument can override.

Other conditions that plausibly belong in the same policy, rather than being scattered:
  - unresolved BLOCKING vs non-blocking open questions (the pre-execution gate already distinguishes these; the policy should say which may be advanced past and by whom)
  - an unfixed review finding at or above the gate threshold (`review_findings_gate.block_at`, currently enforced by `check.review-finding-unescalated`)
  - a stale `aw ipd begin` receipt
  - out-of-scope changed paths needing `--scope-reason`
  - a `Blocks-Release` gate on the artifact
  - whether an automated actor may write a terminal state at all

## Why it matters now

`97df1z` is the FIRST CONSUMER of a policy that does not exist. Its `--full-auto` path decides "may I advance this reviewed plan to ready-to-execute without a human?" and, absent a policy, answers by hardcoding. That plan's OQ-02 was resolved to make the ATTESTATION honest (use the shipped `auto-approved` tier, which `ipd_schema.py:248` documents as "an automated clear, NOT human", rather than falsely asserting `--by-human`), but the QUESTION OF HOW FAR AUTOMATION MAY GO was deliberately left to this item.

Expect more consumers: the runner already makes similar per-transition judgements in `driver_begin`, `aw ipd finalize`, the backlog close gate (`evaluate_blocking_close`), and the spec status setter. Each currently encodes its own answer.

## Design notes and existing material to reuse

- There IS already a precedent for the honest-attestation half: `auto-approved` as a sibling of `approved` in `ipd_schema.READY_TO_EXECUTE` (`:250`), with `:337` enforcing that it carries no human `Approval:` field, and `.aw/records/plans/README.md` recording D65's rule that it is "set only by an automated checker, never by an executor fast-tracking its own work". A policy engine should EXTEND this vocabulary, not fork it.
- There is already a shared-predicate pattern worth copying: `check_engine.evaluate_blocking_close` backs the backlog setter, the `aw check` rules, AND the opt-in pre-commit hook, so they provably cannot diverge. A lifecycle policy should be ONE predicate consulted by every verb for the same reason.
- Config already has a home (`.aw/config/project.json`, schema_version 2) and a documented local/project split, so the policy has somewhere to live without new machinery.

## Open questions for whoever specs this

- Is the policy per-TRANSITION, per-ARTIFACT-TYPE, or both? A backlog item graduating is not the same risk as a plan finalizing.
- Does an argument override LOOSEN only, or may it also TIGHTEN? Loosen-only is safer to reason about; tighten-also is more useful in CI.
- What is the default? Fail-closed (advance nothing without explicit permission) matches this repo's posture elsewhere, but would immediately break `--full-auto` unless it ships with a permissive default for the transitions it already performs.
- Must an automated advance always be DISTINGUISHABLE in the record afterwards? The `auto-approved` precedent says yes, and that property is what makes the audit trail trustworthy.
- Does the policy govern only FORWARD transitions, or also retirement (`superseded`/`not-executed`) and reversal (`approved -> to-review`)?
