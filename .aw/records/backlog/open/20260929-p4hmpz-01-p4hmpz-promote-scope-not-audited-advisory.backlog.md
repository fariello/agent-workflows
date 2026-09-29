- Id: p4hmpz
- Status: open
- Set: p4hmpz
- Priority: low
- Work-Kind: followup
- Summary: Decide whether the scope-not-audited advisory from plan iqtt8d should be promoted from info to a gating severity, on a measured residual rate

## Workflow history
- 2026-09-29 created (aw backlog): Filed as the durable carrier for OQ-01 of plan iqtt8d (Set fkmjoy).

CARRIER for OQ-01 of plan `iqtt8d` (Set `fkmjoy`, from backlog `fkmjoy`).

THE QUESTION. Plan `iqtt8d` adds a `check_engine` advisory that names an in-flight execution whose declared scope could NOT be audited (its lane holds work but no lane candidate's HEAD descends from the receipt's frozen `base_head`). It ships at `info` severity, which by `artifact_core.drift_exit_code` cannot fail a gate. Should it ever become `warning` or `error`?

WHY IT WAS NOT DECIDED IN THAT PLAN. Two reasons, and the first is the substantive one. FIRST, the datum does not exist yet: that plan's main change is RESOLVING the lane an execution actually ran in, which is expected to eliminate the dominant cause (an attempt-scoped lane, `aw/lane/<id6>_attemptN`, that the advisory was never looking at). The residual population the advisory then reports is unknown in both size and legitimacy, and a severity decision without it would be a guess. SECOND, promotion partially reverses a maintainer ruling: the offered variant that printed a 'scope not checked, not lane-isolated' line for the NO-LANE case was DECLINED under `wmnmei` OQ-01 'in favor of the plain silent form', and that reasoning is recorded in `check_engine._plan_execution_tree`'s docstring.

WHAT WOULD MAKE IT DECIDABLE. Observe the advisory in production for a period and record, per firing, whether the named execution turned out to have had real out-of-scope drift that finalize later caught. A run of firings that correlate with real drift argues for promotion; firings on ordinary in-flight lane states argue for leaving it at `info`.

THE RISK OF PROMOTING BLIND, stated because it is the reason for the gate. The advisory fires on a state a legitimate execution can be in (a lane honestly cut from a different commit than the receipt froze, which `allocate_worktree`'s docstring describes as correct behavior), so at a gating severity it would fail commits on lane states nobody did anything wrong to reach. This rule is also explicitly LOCAL best-effort feedback and not an authority boundary (`hooks/precommit_scope_gate.py`); the authoritative boundary is finalize's scope reconciliation plus CI.

OWNER: maintainer. This is a risk-appetite call, not a technical one.

PRECONDITION: plan `iqtt8d` must be executed first, since the advisory does not exist until it lands.
