- Id: go8ztx
- Status: open
- Blocks-Release: next
- Set: newgatevocab
- Priority: medium
- Work-Kind: bug
- Summary: aw backlog new --status blocked writes an out-of-vocabulary Gate-Kind that every set verb refuses

## Workflow history
- 2026-10-02 created (aw backlog): aw backlog new --status blocked writes an out-of-vocabulary Gate-Kind that every set verb refuses

MEASURED 2026-10-02 at HEAD 45bd52b2f in a scratch repo, while authoring plan ju3rhs from backlog fv4b6s:

  aw backlog new --summary ... --status blocked --gate-kind bogus-kind --gate-ref x --apply
    -> rc 0, wrote backlog/blocked/<...>.backlog.md carrying
         - Gate-Kind: bogus-kind
         - Gate-Ref: x
  aw backlog check on that result
    -> rc 1, backlog.gate-kind-invalid: Gate-Kind not in ['artifact', 'date', 'decision', 'external', 'issue', 'todo']

So the CREATE verb writes a gate outside the closed vocabulary that the at-rest checker immediately reports, producing a record that violates the typed-gate contract from the moment it is born. As with fv4b6s, this converts a fail-closed refusal into an after-the-fact finding, and the window between them is however long before anyone runs the checker.

CAUSE: backlog.run_new validates only presence ('if status == "blocked" and (not item.gate_kind or not item.gate_ref)'). It never consults attention_contract.GATE_KINDS and never calls validate_gate_ref, even though backlog.validate_item (the at-rest validator in the same module) checks both, and even though the sibling release-exemption pair in the same verb IS fully validated at the point of typing by backlog.validate_release_exempt_flags.

RELATIONSHIP TO fv4b6s: the same vocabulary hole on the SET verbs is filed as fv4b6s and fixed by plan ju3rhs, which adds ONE shared gate-pair validator to attention_contract and wires it into status_set.validate_transition_allowed and backlog.run_set. This item is the CREATE verb, deliberately excluded from that plan (its F-08 and OQ-02) so a release-gated fix with a measured two-test blast radius was not widened into one whose radius was unmeasured.

SUGGESTED FIX: consume the same shared validator ju3rhs adds, at the same point backlog.run_new already validates --release-exempt-kind/--release-exempt-ref. That makes it a one-line change once ju3rhs lands, which is why this is sequencing rather than a design question. Confirm whether aw specs new / aw ipd scaffold need the same treatment: measured, neither declares --gate-kind or --gate-ref at all, so neither can reach this hole today.
