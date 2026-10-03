- Id: e6zeta
- Status: open
- Set: 4xtpvg
- Priority: low
- Work-Kind: followup
- Summary: Decide whether to keep the unarmed permission-bound mechanism documented or delete it, given its trigger has never had a caller and the deadlock class was closed by denial instead

## Workflow history
- 2026-10-01 created (aw backlog): Filed while authoring plan 0b7fic (from backlog 4xtpvg) as the durable carrier for that plan's OQ-01. THIS IS A MAINTAINER DECISION, NOT A DEFECT, and it is filed because the plan deliberately refuses to make it: the two readings are both defensible and the plan is written so either answer stays cheap. It must NOT be closed by an agent picking a side.

THE SUBJECT: lane_containment.PERMISSION_TIMEOUT (ships 0.0), TurnBoundWatch.note_permission_request, BOUND_PERMISSION, and the _permission_pending_since half of TurnBoundWatch._expired.

THE CASE FOR KEEPING, which plan 0b7fic implements: TurnBoundWatch already gets the resettable semantics right (progress disarms the permission bound, nothing resets MAX_TURN_TIMEOUT), the runtime cost at 0.0 is zero, that plan's E-05 makes it tested rather than merely present, and a host whose stdout stream DOES carry a permission event could arm it with no redesign.

THE CASE FOR DELETING: GUIDING_PRINCIPLES P6 refuses a mechanism kept for a hypothetical need. The trigger has never had a production caller since commit 8a491d4c1 introduced it (2026-09-05), and research 7so8uz measured that the SAME commit landed the R4.1 deny posture that closed the deadlock class by denial, with driver-turn permission asks going 1,102 before it to 0 across the 640 driver turns since 2026-09-13. So the mechanism is a solution to a problem the product solved another way.

WHY DELETION IS THE LARGER CHANGE, which is why 0b7fic did not simply pick it: spec 7ckptx A10b requires the constants EXIST and be named PERMISSION_TIMEOUT and MAX_TURN_TIMEOUT (not ..._DEADLINE), and R4.4(a) specifies the permission bound's own default, so deleting them needs a spec amendment of its own plus its own review. 0b7fic's amendment only narrows two requirements' PROSPECTS (recording that A10c option (i) is unsatisfiable on stdout); deleting the mechanism would change what the contract REQUIRES to exist.

IF THE ANSWER IS DELETE, the right shape is a follow-on plan amending A10b and R4.4(a) together with the code removal, and 0b7fic makes that plan's job SMALLER rather than larger, since by then the state to be deleted is documented and pinned by tests. IF THE ANSWER IS KEEP, 0b7fic already does everything needed and this item closes done with that plan as its evidence.

NOT A RELEASE BLOCKER: Work-Kind followup, nothing is broken either way, and the status quo is safe (a bound at 0.0 cannot fire).
