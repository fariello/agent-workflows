- Id: fv4b6s
- Status: open
- Blocks-Release: next
- Set: setdispgate
- Priority: medium
- Work-Kind: bug
- Summary: Positional aw specs set deferred writes an invalid Gate-Kind the --status spelling refuses

## Workflow history
- 2026-10-01 created (aw backlog): Filed while authoring the fcnz1r dispatch-unification Set; measured, not inferred.

MEASURED 2026-10-01 in a scratch repo at HEAD ec857565a, driving both spellings over an identical 'approved' spec fixture with a deliberately INVALID gate kind:

  aw specs set <path> --status deferred --gate-kind bogus-kind --gate-ref x
    -> rc 1, 'deferred requires a valid --gate-kind and --gate-ref', file UNCHANGED, no gate fields written
  aw specs set deferred abc123 --gate-kind bogus-kind --gate-ref x
    -> rc 0, file RELOCATED to specs/deferred/, and it now carries
         - Gate-Kind: bogus-kind
         - Gate-Ref: x

So the positional spelling writes a gate that is not in the vocabulary, producing an on-disk spec that violates the typed-gate contract AGENTS.md states ('A deferred spec MUST carry a typed gate'), while the other spelling of the same verb refuses it.

CAUSE: specs.run_set validates both halves (gk not in A.GATE_KINDS and A.validate_gate_ref(gk, gr)) plus --gate-summary safety. status_set.apply_status_change's gate handling (via _GATE_STATUS_BY_TYPE) only CLEARS and WRITES gate fields; it validates neither the kind against A.GATE_KINDS nor the ref shape.

SECOND-ORDER EFFECT WORTH NOTING: this writes a record that the checker is then expected to catch at rest, so the defect converts a fail-closed refusal into an after-the-fact finding, and the window between them is however long before anyone runs the checker.

ROOT CAUSE is the same dual dispatch fork as h4fiwa and backlog fcnz1r: 'aw specs set' routes on whether --status was PASSED. SUGGESTED FIX: validate the gate pair in the shared engine so both spellings refuse identically; the durable fix is fcnz1r's unification. Filed separately so the release gate is not silently absorbed into a chore-classified refactor.
