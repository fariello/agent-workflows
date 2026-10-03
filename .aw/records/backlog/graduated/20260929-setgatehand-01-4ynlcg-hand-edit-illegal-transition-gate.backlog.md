- Id: 4ynlcg
- Status: graduated
- Graduated-To: setgatehand
- Set: setgatehand
- Priority: medium
- Work-Kind: chore
- Summary: Extend the untooled-transition pre-commit gate to catch a hand-edited illegal plan lifecycle transition

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: tliqz6
- 2026-09-29 created (aw backlog): Extend the untooled-transition pre-commit gate to catch a hand-edited illegal plan lifecycle transition

Split out of plan nvsz19 (Set ipdsetback), which closes the SETTER path only. nvsz19 makes aw set / aw ipd set refuse an illegal backwards plan transition by delegating to ipd_lifecycle.validate_transition. That covers the tooled path, which is what an agent and a human actually use, but it cannot see a hand edit: rewriting '- Status:' in an editor and git-mv-ing the file bypasses the setter entirely.

WHAT ALREADY EXISTS: the shipped ipd-status-untooled-gate pre-commit hook detects a status changed WITHOUT a tooled transition, and check_engine.check_lifecycle_transitions validates recorded histories with the same predicate nvsz19 wires into the setter. So both halves exist; what is missing is a commit-time gate that refuses a STAGED illegal transition specifically, the way backlog-blocking-close-gate does for the backlog close case.

HONEST LIMIT TO STATE IN THE PLAN: git hooks are local, not cloned by default, and skippable with --no-verify, so the portable authority is the aw check rule family plus CI, never the local hook alone. That is the same limit AGENTS.md already records for backlog-blocking-close-gate.

SCOPE NOTE: check_engine.check_lifecycle_transitions is deliberately advisory AND pending-scoped (it skips any plan outside pending/). Measured 2026-09-29: 24 TERMINAL records (19 executed/, 5 superseded/) carry illegal recorded edges and are explicitly grandfathered by that scoping, so any gate must stay commit-scoped rather than whole-tree or it will re-litigate them.
