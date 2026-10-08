- Id: h4fiwa
- Status: done
- Graduated-To: setdispgate
- Blocks-Release: next
- Set: setdispgate
- Priority: high
- Work-Kind: bug
- Summary: Positional aw specs set implemented bypasses the --evidence citation gate the --status spelling enforces

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD wdyz5n executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-setdispgate-01-wdyz5n-run-the-shared-evidence-predicate-on-the-positional-aw-specs.ipd.md); evidence .aw/records/plans/executed/20261002-setdispgate-01-wdyz5n-run-the-shared-evidence-predicate-on-the-positional-aw-specs.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: wdyz5n
- 2026-10-01 created (aw backlog): Filed while authoring the fcnz1r dispatch-unification Set; measured, not inferred.

MEASURED 2026-10-01 in a scratch repo at HEAD ec857565a, driving both spellings over an identical 'implementing' spec fixture:

  aw specs set <path> --status implemented  -> rc 1, 'requires a resolvable --evidence citation', file UNCHANGED in implementing/
  aw specs set implemented abc123           -> rc 0, file RELOCATED to specs/implemented/

So the gate is reachable only through one of the two spellings of one verb, and the OTHER spelling is the shorter, more idiomatic one an agent is likelier to type.

WHY THIS IS A GATE BYPASS AND NOT A COSMETIC GAP. AGENTS.md states an agent 'may NOT set implemented (needs cited evidence)', and specs.run_set enforces exactly that via auth.get('evidence') + _evidence_resolvable. status_set.validate_transition_allowed has NO evidence branch at all (no reference to auth evidence anywhere in the function), so the positional spelling lets an agent assert a spec is implemented with no cited executed IPD. That is a forged attestation of the same class the Readiness and by-human rules exist to prevent.

ROOT CAUSE is the dual dispatch fork in cli.main (backlog item fcnz1r): 'aw specs set' routes on whether --status was PASSED, absent to status_set.run_set_command and present to specs.run_set. This is the SAME class fcnz1r documents three prior instances of (43p53n, gatefollows, mawwlc/47ttnv).

SUGGESTED FIX: consume the one shared evidence predicate from status_set.validate_transition_allowed, exactly as 47ttnv did for the release-gate close predicate and as specs.run_set's own comments describe doing for the ->reviewed attestation and the approval gate ('a gate installed in only one of them is bypassed by choosing the other spelling'). The durable fix is fcnz1r's unification; this item is the release-gated defect that unification would close, filed separately so the gate is not silently absorbed.
