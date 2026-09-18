- Id: xtrwdb
- Status: open
- Blocks-Release: next
- Set: xtrwdb
- Priority: low
- Work-Kind: bug
- Summary: tools/untrack-workflow-artifacts.py still untracks the RETIRED repo-root path in place and writes a root ignore rule for it

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): tools/untrack-workflow-artifacts.py still untracks the RETIRED repo-root path in place and writes a root ignore rule for it

Found while executing wfartifacts Order 05 (y4pptx).

WHAT IS WRONG: `tools/untrack-workflow-artifacts.py` hard-codes `ARTIFACTS = "workflow-artifacts"`, the REPO-ROOT path that Order 07 (spec 20260817-2124-01) retired and that the wfartifacts Set has now migrated away from. The tool untracks that path IN PLACE and writes an ignore rule for it into the user's ROOT .gitignore. After this Set, run scratch lives at `.aw/workflow-artifacts/` and is ignored by the framework-owned `.aw/.gitignore`, so the tool now advertises and reinforces a layout that no longer exists.

WHY IT IS ONLY A LOW-PRIORITY GAP, stated honestly rather than inflated: the tool has NO caller in `agent_workflows/` (verified: grep for untrack_workflow_artifacts returns nothing), so nothing runs it automatically and it cannot regress an install. It is a hand-run convenience script. Order 05's plan explicitly DEFERRED changing its in-place behavior ('it stays available for a user who wants only to untrack; changing it is a separate concern'), so this item carries that deferral rather than contradicting it.

WHAT A FIX WOULD DECIDE: whether the tool should (a) be retargeted to the new path, (b) be taught to delegate to `engine.migrate_root_workflow_artifacts` now that a real migration exists, or (c) be retired with a pointer to `aw install`, which now performs the migration. Option (b) or (c) is likely right, since a user reaching for this tool today most likely wants the migration the installer now does.

WHERE: tools/untrack-workflow-artifacts.py (ARTIFACTS constant and the root-.gitignore write).
