- Id: lz16f3
- Status: open
- Set: lz16f3
- Priority: low
- Work-Kind: followup
- Summary: An installed completion script goes stale silently for any user who never re-runs aw install or aw setup

## Workflow history
- 2026-09-21 created (aw backlog): An installed completion script goes stale silently for any user who never re-runs aw install or aw setup

FOUND while executing plan 4y95tp (compargs 01), whose E-06 closed the reportability half of this and
deliberately left this half open.

WHAT NOW WORKS. `aw completion install` writes a drop-in script once, and NOTHING in the install or
upgrade path ever regenerates it, so a framework upgrade that adds or renames a command leaves the user
completing a vocabulary that no longer exists. Before 4y95tp that was UNREPORTABLE: `_completion_tip`
composed `is_completion_installed`, a PRESENCE check, so a stale file took the same silent branch as a
current one. 4y95tp added `completion.installed_completion_state` (absent/current/stale, by byte
comparison against a fresh generation) and a warning naming `aw completion install`.

WHAT REMAINS, and it is a genuine coverage gap rather than a defect in that fix: the warning fires only
from `_completion_tip`, which is called from exactly three host-level sites - single-repo `aw install`,
batch `aw install`, and `aw setup`. A user who upgrades the package (pip/pipx) and never runs either
verb again is never told, and their completion silently drifts for as long as they keep using the tool.
That is arguably the MOST common upgrade path for someone who installed once and now just uses `aw`.

THIS IS RECORDED IN THE PLAN AS AN ACCEPTED COST, not discovered afterwards: its Scope check states
"E-06 warns an installed user that their script is stale, but the warning fires only when they next run
`aw install` or `aw setup`. A user who never re-runs either keeps a stale vocabulary indefinitely."
Filing it so the gap has a durable carrier rather than living only inside an executed plan.

CONSTRAINT ANY FIX INHERITS: the maintainer ruled WARN-ONLY on 2026-09-12 (OQ-01) - `aw install` must
never rewrite the user's completion file, because a user-scoped write requires consent. So the fix is
about WHERE the check runs, never about repairing the file silently.

OPTIONS, none costed: check on some other frequently-run command (cost: a per-user filesystem read on a
hot path, and the <50ms-style budgets this repo cares about); check at most once per day via a stamp
(cost: a new state artifact, which E-06 deliberately avoided); or have the generated script itself
detect a version skew (cost: it is static and self-contained by contract, and a runtime callback is
explicitly excluded).

LOW PRIORITY and NOT release-gating: a stale script still completes every command whose name did not
change, so the failure mode is a missing completion rather than a wrong one. The actively MISLEADING
behavior - suggesting tokens that cannot be valid - is what 4y95tp fixed.
