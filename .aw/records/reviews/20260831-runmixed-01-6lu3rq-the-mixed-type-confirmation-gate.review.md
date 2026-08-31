# Review: The mixed-type confirmation gate and the runner-facing selector policy over the shipped resolver

- Plan-Id: 6lu3rq
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `381dbd5c1c313c16b4a833ed5c3541939872ee42`, working tree clean, target plan
committed and unchanged (pre-review snapshot correctly skipped per the workflow's Step 1). Structural
preflight `aw ipd lint --phase author` reports `conforming`.

This plan is unusually well grounded, and the verification bore that out rather than merely agreeing with
it. Every material claim I could test was TRUE:

- The gate really is wholly unbuilt: `RUN-MIXED-TYPES`, `--allow-mixed` and `allow_mixed` return ZERO hits
  across `agent_workflows/` and `tests/`.
- The refusal string in E-04 is character-for-character identical to spec `25kzda` 2.5's exact refusal
  block (`spec:215`), including the `No work started.` clause and the recovery command. I diffed them.
- `selectors.py` really is the authoritative resolver, `UNIQUE_KINDS` is at `:46`, and `_PRECEDENCE`
  really does begin `MATCH_PATH, MATCH_ID6, ...`, matching what the plan says spec 2.3 step 3 requires.
- The `run mixed` exact-phrase rule, the `y`/empty rejection, the unattended `--allow-mixed` rule, and the
  narrowing rule that `--allow-mixed` acknowledges type mixing ONLY are all present verbatim in spec 2.5
  (`spec:206-209`), so F5 and F6 are accurate and the plan is not paraphrasing.
- Both sibling collisions it claims are resolved really are: `lanetruth-03` (`8guhs0`) and `bkclose-01`
  (`zhr6mc`) are both in `executed/`.
- Its Scope-Paths collide with NO other pending plan and with NO approved plan, so it can land
  independently. I checked this by intersecting scope paths across all pending plans.

ONE DEFECT was found, by reading the spec section the plan implements rather than the plan's account of
it. The plan implements three of spec 2.5's four bullets and is silent on the fourth.

1. PR-001, MEDIUM. Spec 2.5's fourth bullet requires the confirmed type counts, action preview, user
   response or flag, and queue digest to be RECORDED IN THE RUN LEDGER. The plan never mentions the
   ledger; `grep -in ledger` over the plan returns nothing. This is a genuine under-scope against the
   spec section the plan names as its contract, and it matters because the ledger record is the audit
   trail proving what the operator acknowledged.

FIXED in place with a bounded edit. The plan's architecture is sound and needed no replan: it deliberately
does not touch the runners, and the ledger write belongs to the caller that owns a live run, so the honest
fix is to make the predicate RETURN the recordable facts and state the deferral explicitly, rather than to
widen scope into `run_ledger_store.py`.

The plan's deliberate under-scope (the gate is not consulted by any live run until a follow-up wires it) is
stated plainly three times, including in the Approval gate's honesty rule. That is correct practice, not a
defect, and it is what dissolves the `rununify` sequencing conflict rather than answering it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | A. Correctness / F. Spec conformance | spec `25kzda` 2.5 bullet 4 (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:210`); `grep -in 'ledger' <plan>` returns ZERO | The plan implements THREE of spec 2.5's four bullets and is silent on the fourth, which requires that "the confirmed type counts, action preview, user response or flag, and queue digest are recorded in the run ledger". Nothing in E-01..E-05, the Deferred section, or the Scope check mentions the ledger at all, so the omission reads as an oversight rather than a decision. This is the audit trail proving WHAT the operator acknowledged; without it a `--allow-mixed` run leaves no durable record of the counts that were acknowledged, which is precisely the accountability the gate exists to create. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (the fix is a return-value requirement plus an explicit deferral, not new machinery) | FIXED | E-03 now requires the predicate to RETURN the four recordable facts (counts, preview, response-or-flag, queue digest) as structured data so a caller can record them, and V-03 requires that structure to be pasted. The ledger WRITE is added to Deferred with its reason (it belongs to the caller owning a live run; `run_ledger_store.py` is outside Scope-Paths and this plan deliberately touches no runner), and the Spec sync section now records that 2.5 bullet 4 is only partially discharged. Added as F7. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Spec 2.5 bullet 4 requires the acknowledgement facts to be recorded in the run ledger. Should this plan write that record, or is returning the facts enough? | RETURN the four facts as structured data from the E-03 predicate; DEFER the ledger write to the caller that owns a live run. | (a) Widen Scope-Paths to include `run_ledger_store.py` and write the record here. Rejected: the write needs a live run's context, and taking on a runner-adjacent edit destroys the property that makes this plan runnable now (it touches neither runner, which is what dissolves the `rununify` conflict rather than answering it). (b) Leave the bullet unmentioned. Rejected: that is the defect PR-001 found; silence reads as oversight and loses the audit trail. | spec `25kzda` 2.5 bullet 4 (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:210`); the plan's own Deferred section and the `hostcap-01` (`mjx7ne`) precedent it cites for deferring runner wiring | yes |
| D-2 | Is "nothing consults this gate when the plan completes" an acceptable under-scope, or a defect? | ACCEPTABLE, and correctly disclosed. Not raised as a finding. | Requiring the runner wiring in this plan. Rejected: that reintroduces the exact `rununify` scope conflict that made the predecessor `kaygwo` unexecutable twice, and the gate's vocabulary plus its verbatim message are what any wiring needs first. | The plan states the consequence plainly in three places (Scope check, Deferred, and the Approval gate's honesty rule, which forbids describing the plan as making runs safer) | yes |
