# Review findings: spec r07vma

- Subject-Id: r07vma
- Subject-Type: spec
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f4bbcb17`. Structural preflight `aw specs check` CONFORMED (exit 0) before semantic
review and again after every revision. Pre-review snapshot committed as `f4bbcb17` because the spec was
untracked. `aw ipd lint` was never invoked against the spec (prohibition (c)); no `- Readiness:` field was
added (prohibition (a)); the status transition and history were written only by `aw specs set` / `aw specs
note` (prohibition (b)).

DISCLOSURE: THE SAME AGENT AND MODEL AUTHORED THIS SPEC EARLIER IN THE SAME SESSION. So rather than
re-reading my own prose for plausibility, I verified every material claim against the shipped source and
then went looking for the governing spec the draft had NOT cited. That is what produced SR-001, and it is
the finding that most changes the spec.

THE DESIGN IS SOUND AND ITS CENTRAL CLAIM IS TRUE. Every measurement in the draft reproduced exactly:
`evaluate_set_retirement` contains zero references to `E-`, `V-`, `items`, `checklist`, `execution state`,
`lint` or `checkpoint` (verified by source inspection, function begins `runner_shared.py` line 7114);
`rh5tt6` was retired by commit `8b4e1570` whose message states "Its own `E-*`/`V-*` items were NOT
performed" while its E-02 still reads `Execution state: pending` and its V-02 `Observed evidence:` is
blank; the 2026-09-06 `Readiness` incident is recorded in `AGENTS.md` as stated, `ipd_lint.C_READINESS_
UNATTESTED` is `IPD-M107`, and `aw ipd scaffold` emits zero `- Readiness:` lines; `resolve_retry_budget
(None)` returns 2 and backlog `dh3us4` exists for the unimplemented middle tier;
`check_engine.evaluate_blocking_close` is genuinely one predicate consumed from five modules.

BUT THE DRAFT PROPOSED TO RETIRE A CONTROL THAT AN APPROVED SPEC FORBIDS REPLACING, AND DID NOT CITE
THAT SPEC. `25kzda` Section 2.5b (`- Status: approved`) states the coverage check "is SEMANTIC and is
therefore a MODEL question, not a pattern match", that the dangerous case is stated in PROSE and "matches
no checklist syntax, so a syntactic rule catches only the tidy mistake and misses the harmful one", and
then prohibits the substitution outright: "A syntactic rule MUST NOT be added in its place". The draft's
R9 and its acceptance criterion 7 required exactly that substitution.

THE PROHIBITION'S PREDICTION WAS TESTED RATHER THAN ACCEPTED ON AUTHORITY, and it held. Two candidate
deterministic signals were measured against live plans. A child-reference signal (does the E-item name a
child id6?) PASSES `rh5tt6` E-02, the actual production failure, because it name-drops sixteen children
while being pure parent-only work. A confession-phrase signal (`no child owns|covers|can`) catches
`s0gnha` and `wfjsp4` but MISSES `5e4sb6`, `tb63qv` and `a5wdne`: 2 of 5 on a sample the spec already had
in hand. So the parser's recall on the harmful case is demonstrably partial, and the draft would have
narrowed real coverage while claiming to harden it, deleting 476 lines of shipped code across seven
functions and 1265 lines of tests merged the same day.

THE REPAIR PRESERVES THE DRAFT'S ACTUAL CONTRIBUTION. A deterministic parser is cheap, it is repairable
at review where a violation can be FIXED rather than merely reported, and it has no availability failure
mode. Those are real gains the probe does not provide. So the spec now ADDS the parser beside the probe
with a narrower question, orders them parser-then-probe, and states in its own honest-limits section that
a clean parser result is not evidence an orchestrator carries no uncovered work.

ONE COUNT MOVED WITHIN HOURS, which is itself evidence for the re-derive discipline: the pending
`Kind: orchestrator` population was ten at authoring and is ELEVEN at review (`7ewc74` left by being
finalized earlier in this same session; `2xz59a` and `s0gnha` arrived). The SHAPE the spec depends on (a
majority carry at least one parent-only item) survived.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-001 | BLOCKER | IN-SCOPE | D (decisions), F (honest limits) | `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:305-312`; draft R9 and criterion 7 | The spec proposed RETIRING the semantic coverage probe and replacing it with a syntactic parser. Approved spec `25kzda` 2.5b states the check is semantic and that "A syntactic rule MUST NOT be added in its place", with the measured reason that the harmful violation is stated in prose and matches no syntax. The draft did not cite 2.5b at all. Measured at review: a child-reference signal passes `rh5tt6` E-02 (the production failure) and a confession-phrase signal catches 2 of 5 sampled violators, so the substitution would have reduced coverage. It would also have deleted 476 lines of code and 1265 lines of tests merged the same day. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | R9 rewritten: the parser is ADDITIVE, the probe is RETAINED, the two questions are stated separately and ordered parser-then-probe. Section 1 reframed from "wrong shape" to "what the existing control does not reach". Section 3 records the correction and the measurements. Criterion 7 INVERTED to pin that the probe still runs. `- Constrained-by:` added naming 2.5b. |
| SR-002 | HIGH | UNDER-SCOPE | F (honest limits) | draft Sections 5-6 | The spec had no honest-limits statement, which rubric F makes a BLOCKER-class omission for a spec claiming more than it delivers. It implied a conforming parse meant no uncovered work, which is false by construction for the prose case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New Section 3a with five numbered limits: a clean parse is not evidence of coverage; recall is unquantified; review repair is self-assessed; concealment is not prevented; and the spec does not establish that a parser is sufficient. |
| SR-003 | HIGH | IN-SCOPE | A (measured claims current) | draft cost 3 ("ten pending, seven parent-only") | The count was stale within hours of authoring: the population is now eleven, with one departure and two arrivals. A spec whose cost statement reads as an invariant invites an implementer to treat it as a fixture. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cost 3 re-measured inline, names the departure and both arrivals, states the SHAPE that must survive re-measurement, and requires the implementer to re-derive and report the denominator. |
| SR-004 | MEDIUM | UNDER-SCOPE | C (criteria cover requirements) | draft criteria 1-8 | No criterion covered the coexistence of the two controls, their distinguishability to an operator, or their ordering, so an implementer could satisfy every criterion while silently collapsing them into one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion 7 inverted (probe still runs, prose case still refused, probe tests pass unedited); criterion 8 added (the two refusals are distinguishable, naming different rule ids); criterion 9 added (parser-then-probe ordering, a parser refusal spends zero model calls). |
| SR-005 | MEDIUM | IN-SCOPE | E (open questions dispositioned) | draft OQ-03 | OQ-03 was left `open` with a "PROPOSED DIRECTION", but the repository already answers it: `77tr3o`'s Scope states a hand-run Set still executes its orchestrator's items, and nothing in the schema marks a Set as hand-run-only. Rubric E requires a question the repository answers to be resolved and cited, not left open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-03 resolved as APPLY UNIFORMLY, citing `77tr3o`'s Scope and the absence of any execution-route marker, with the accepted cost stated and a named revisit condition. Recorded as decision SR-D1. |
| SR-006 | LOW | IN-SCOPE | B (requirements testable) | draft `- Scope:` line | The scope line claimed the whole coverage question rather than the authoring-conformance subset, overlapping the probe's territory and making the spec's boundary unreadable from its front matter alone. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope narrowed to AUTHORING CONFORMANCE and marked ADDITIVE to the existing probe; `- Parent:` corrected from "REPLACES R-12" to "ADDS beside R-12, leaves R-1..R-12 intact". |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| SR-D1 | OQ-03: does the conformance rule apply to an orchestrator a runner will never queue, given that a hand-run Set legitimately executes its parent's items? | APPLY THE RULE UNIFORMLY, with the accepted cost stated and a named revisit condition. | (a) Exempt hand-run-only Sets, rejected: the exemption is not expressible, because nothing in the plan schema marks a Set as hand-run-only and the execution route is chosen at run time rather than at authoring time, so the rule would have to guess; guessing permissively reintroduces the silent loss `rh5tt6` measured. (b) Ask the maintainer, rejected: the repository answers it, since `77tr3o`'s Scope states the hand-run path still executes those items and no marker exists to condition on. (c) Apply only at the run-time consumer, rejected: it would leave review unable to repair the violation, which is the one capability this spec adds. | `77tr3o` Scope ("does NOT change the agent-driven path (a human or agent running a Set by hand still executes the orchestrator's own `E-*`/`V-*` items)"); absence of any execution-route field in the plan schema; `rh5tt6` commit `8b4e1570` | yes - a durable execution-route marker would make a conditional rule expressible and the trade re-takeable; the spec records that revisit condition |
| SR-D2 | SR-001: should the semantic coverage probe be retired and replaced by the deterministic parser, as the draft proposed? | RETAIN the probe; the parser is ADDITIVE, ordered parser-then-probe, answering a narrower question. | (a) Retire the probe as the draft proposed, rejected: `25kzda` 2.5b (approved) states "A syntactic rule MUST NOT be added in its place" with the measured reason that the harmful violation is prose, and two candidate signals measured at review both missed real violations (a child-reference test passes `rh5tt6` E-02; a confession-phrase test catches 2 of 5 sampled). It would also delete 476 lines of code and 1265 lines of tests merged the same day. (b) Keep the probe but make the parser authoritative when both run, rejected as the same substitution with extra steps. (c) Abandon the parser entirely and keep only the probe, rejected: the parser contributes repairability at review and has no availability failure mode, which the probe does not provide. | `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:305-312`; measured recall of both candidate signals; `inspect.getsourcelines` over the seven probe functions | yes - if measurement later shows the parser's recall on real violations is negligible, dropping the parser and keeping only the probe is a reasonable response; Section 3a limit 5 records that |

### Verdict

`APPROVE WITH REVISIONS APPLIED`. Six findings, all FIXED in place, none deferred, none left open, no
REPLAN. The spec's central claim (an orchestrator cannot hold agent-performed work, because retirement is
programmatic and skips the E/V checkpoint) is verified and unchanged. What changed is the mechanism's
RELATIONSHIP to the existing control: additive rather than substitutive, which is what `25kzda` 2.5b
requires and what the measurements support.

READY FOR THE HUMAN APPROVAL GATE. No gating finding remains, so this record arms no refusal on approval.
Two open questions remain by design (OQ-01 on instruction/code drift, OQ-02 on prose versus a typed
checklist), both explicitly non-blocking and both carrying a proposed direction rather than a silent
default; neither is required to author the implementing plan.
