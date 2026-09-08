- Id: dk16dx
- Status: graduated
- Blocks-Release: next
- Set: specvis
- Priority: high
- Work-Kind: feature
- Summary: IPDs may amend specs: make a run's declared spec edits visible at run START and END, and cover both hosts

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan st5klo (to-review), which carries From-Backlog: dk16dx and inherits Blocks-Release: next.
- 2026-09-07 created (aw backlog): IPDs may amend specs: make a run's declared spec edits visible at run START and END, and cover both hosts

MAINTAINER RULING 2026-09-07, recorded verbatim in substance: an IPD MAY modify a spec. Specs are
meant to EVOLVE as we learn and get new information, so a plan amending one is legitimate and is not
a contract violation to be prevented. What must be guaranteed is VISIBILITY: whenever a runner run
will modify a spec file, that fact is raised CLEARLY to the operator so it is never a surprise, and
it is raised at the START and at the END of the run.

THE DOCTRINE IS ALREADY WRITTEN DOWN; THE MECHANISM IS HALF-BUILT. `AGENTS.md:82` ("A PLAN MAY AMEND
A SPEC, AND MUST DECLARE IT") states both obligations: declare every `.spec.md` in `- Scope-Paths:`,
and say why in the plan's spec-sync section. It also asserts, as present-tense fact, that "`aw oc
run` / `aw agy run` announce declared spec edits BEFORE the run starts". That claim is currently
TRUE OF ONE HOST AND FALSE OF THE OTHER.

MEASURED GAPS, at HEAD `aeb71ca2`:
  1. AGY NEVER ANNOUNCES. `agy_runipd.py:162` re-exports `spec_impacts_for_queue` from
     `runner_shared` and there is NO OTHER REFERENCE to it in the file, and no reference at all to
     `format_spec_impact_announcement`. The import is dead. `oc_runipd.py:4100-4108` is the only
     caller. So the AGENTS.md sentence overstates the shipped behavior for `aw agy run`, which is
     the more dangerous direction: an operator who has read AGENTS.md believes the announcement is
     universal.
  2. NEITHER HOST ANNOUNCES AT THE END. The only call site sits in the run-order announcement path,
     which runs BEFORE dispatch. Nothing re-states which specs were actually touched when the run
     finishes, so the operator's single chance to notice is the top of a scrollback that a long run
     will have buried. The maintainer explicitly asked for both ends.
  3. THE START ANNOUNCEMENT IS BEST-EFFORT AND SILENT ON FAILURE. `oc_runipd.py:4107-4109` wraps the
     call in `except Exception: pass` ("Advisory only: never let a missing announcement stop a run").
     Not letting it abort a run is right; swallowing it WITHOUT A TRACE is not, because the failure
     mode is indistinguishable from "this run amends no spec". It should still not block, but it must
     say that it could not compute the impact.

WHY THIS IS `Blocks-Release: next`. Two plans in flight are gated on maintainer answers that this
visibility contract is the precondition for: `51vw4y` (OQ-04, resolved 2026-09-07 to amend spec
25kzda 2.1 and then register the two ladder flags) and `03ie04` (OQ-04, resolved to amend 2.9 first).
Both now legitimately carry spec amendments, so the release should not ship with the announcement
covering one host and one end of the run.

WHAT DONE LOOKS LIKE: both hosts announce declared spec edits at run start AND at run end, from ONE
shared implementation (not a second copy in agy: see `cnwy8g` on the 40-symbol import coupling); the
end-of-run report names the specs ACTUALLY modified, reconciled against what was declared, since the
finalize scope gate already computes that reconciliation; a computation failure is reported rather
than silently swallowed; and `AGENTS.md:82`'s present-tense claim is either made true or corrected.
Verify the agy path by running it, not by reading the import.
