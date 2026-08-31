- Id: rxya25
- Status: open
- Set: rxya25
- Priority: high
- Work-Kind: feature
- Summary: configurable per-transition policy for how far automation may advance an artifact through the lifecycle

## Workflow history
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
