- Id: 1ap48y
- Status: open
- Set: workkind
- Priority: medium
- Kind: feature
- Summary: Add a uniform recognized-but-optional Work-Kind field (bug/feature/chore/... work-nature) to IPDs and specs, distinct from the structural Kind (orchestrator/child) and artifact type; enables cross-tree filtering of work by nature across backlog/plans/specs

## Workflow history
- 2026-08-28 created (aw backlog): Add a uniform recognized-but-optional Work-Kind field (bug/feature/chore/... work-nature) to IPDs and specs, distinct from the structural Kind (orchestrator/child) and artifact type; enables cross-tree filtering of work by nature across backlog/plans/specs

Problem: only BACKLOG classifies work-nature (`- Kind: bug|feature|chore|security|followup`, backlog.py:54). IPDs and specs have no work-nature field, so a bug/feature classification is lost when a backlog item graduates into a plan, and `aw attention`/queries can't filter "all bug work" across trees.

Decision: add a UNIFORM recognized-but-optional work-nature field named **`Work-Kind`** to IPDs and specs (and it already exists as `Kind` on backlog - reconcile naming). NOT named `Kind`: that token is TAKEN by two other axes - the IPD structural kind (`Kind: orchestrator|child`, ipd_schema.py:29-31) and the research doc-type kind - and `Type` is loaded by artifact type. `Work-Kind` is unambiguous ("the nature of the WORK").

Design considerations to resolve at plan time (do NOT assume):
1. VOCAB FIT PER TYPE: backlog's set (bug/feature/chore/security/followup) fits backlog well, but a SPEC is rarely a "bug" - it's more design/rfc/policy/convention. Decide whether Work-Kind uses ONE shared vocab across all three types or a per-type-appropriate set (risk: forcing one vocab creates the same drift we hit elsewhere). Likely: a shared superset with per-type sensible values.
2. DERIVE vs STORE for IPDs: an IPD that carries `From-Backlog: <id6>` could DERIVE its work-nature from the source backlog item's Kind rather than duplicating it (avoids two-places-to-update). Decide store-explicitly vs derive-from-From-Backlog vs both (explicit overrides derived).
3. Backlog reconciliation: backlog's field is `Kind`; either rename it to `Work-Kind` (migration) or accept backlog=`Kind`, IPD/spec=`Work-Kind` and map between them (inconsistent). Prefer aligning on `Work-Kind` everywhere for one cross-tree field.
4. Recognized-but-optional (like Priority/Blocks-Release/Summary/Item-Dependencies): in META_RECOGNIZED not META_REQUIRED (no mass-fail); attention reads it for filtering/labeling; aw check validates the enum.

Related cross-type-field work: Priority (xprio), Summary (ud28vy), Item-Dependencies (ipddeps) - same recognized-but-optional pattern; this should follow it. Origin: user asked whether IPD/backlog/etc. artifacts should describe the type of thing they address (bug/feature/etc.).
