- Id: rb4wgj
- Status: open
- Set: rb4wgj
- Priority: medium
- Work-Kind: chore
- Summary: spec 25kzda 5.5 enumerates retry classes in a vocabulary no driver disposition uses, so every consumer must invent the mapping and two consumers can map it differently

## Workflow history
- 2026-09-22 created (aw backlog): spec 25kzda 5.5 enumerates retry classes in a vocabulary no driver disposition uses, so every consumer must invent the mapping and two consumers can map it differently

FOUND WHILE EXECUTING plan `xipfy1` (retrywire), whose E-01 was required to derive an allowlist from spec `25kzda` 5.5 'mapped onto the drivers' actual disposition vocabulary'.

WHAT IS WRONG. Section 5.5 names five retryable classes (host spawn failure; host nonzero exit without an ambiguous side effect; missing artifact or failed deterministic check; missing or stale validation evidence; verifier transport failure) and ten never-retryable ones. NONE of those fifteen names is a driver disposition. The drivers persist `executed|substantially-complete|partial|blocked|failed-safely|dependency-blocked|...`, so the mapping from spec class to driver status exists NOWHERE in the tree and each consumer must re-derive it by judgement.

THE CONSEQUENCE IS ALREADY VISIBLE, which is what makes this worth filing rather than a style note. There are now TWO consumers of the same spec section and they key on DIFFERENT things: `finalize_retry_decision` (`zzcrlo`) classifies by matching the finalize gate's FINDING TEXT, while `turn_retry_decision` (`xipfy1`) classifies by DISPOSITION. Both are defensible readings of 5.5 and neither can be checked against the spec mechanically. `xipfy1` also had to EXCLUDE `partial` on grounds that are nowhere in the spec (a sibling plan owns it, and it doubles as the verifier-downgrade status), which is exactly the kind of judgement a shared mapping would make reviewable.

A SECOND, RELATED GAP, recorded so it is not re-derived: 5.5's eleven `IPD-EXEC-*` finding codes grep to ZERO files, which the spec itself concedes, so a consumer cannot key on the codes either.

WHERE. `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` section 5.5; consumers `runner_shared.finalize_retry_decision` and `runner_shared.turn_retry_decision`/`TURN_RETRY_CLASSIFICATION`.

POSSIBLE FIXES, not prescribed: (a) AMEND the spec with an explicit class-to-disposition table, which is the durable fix and makes both consumers checkable against one contract (note this edits an `approved` spec, so it needs the declare-and-justify route); (b) declare ONE in-code mapping that both consumers read, and cite it from the spec; (c) accept the divergence and document at each site which reading it took, which is what the two sites do today and is the weakest option.

NOT A BUG: no shipped behavior is known to be wrong, and both consumers fail closed (each is a positive allowlist). It is a contract gap that makes a future divergence cheap and hard to notice.
