- Id: qyaime
- Status: graduated
- Blocks-Release: next
- Set: wtextperm
- Priority: high
- Work-Kind: bug
- Summary: Worktree-isolated aw oc run hangs forever on opencode's external_directory permission prompt (agent cwd is the lane worktree but the driver forces main-repo run-dir access; --auto non-interactive has no answerer)

## Workflow history
- 2026-08-29 graduated (aw set): status set to graduated
- 2026-08-28 basis (manual): Basis: research x03wgn (20260828-wtiso-00). Facet of the driver-owned-control-plane architecture; to be implemented via the orchestrated wtiso Set, not standalone. Near-term fix: Layer-1 (internal-only lane prompt paths) + Layer-6 (permission-event timeout/watchdog). (Hand-added: aw backlog set --message is a no-op when status is unchanged; see tooling gap.)
- 2026-08-28 created (aw backlog): Worktree-isolated aw oc run deadlocks on the external_directory permission prompt: the driver launches opencode with --dir <worktree> but its prompt forces the agent to read/write the run-dir (outcome JSON, decisions, report, runbook) under the MAIN repo (outside the lane), which trips opencode's external_directory gate; under --auto non-interactive nobody can answer, so the turn hangs forever

OBSERVED (definitive, from opencode.log): jolfpj lane, cwd inside .aw/worktrees/jolfpj. Healthy agent loop for many steps, then a line: 'message=asking ... permission=external_directory patterns=["<repo-root>/*"]' - a permission PROMPT for a main-repo path. No answer possible (--auto, non-interactive). Turn blocked in ep_poll on the permission-response socket, zero events for 6+ min. (hound MCP was a RED HERRING: it was killed ~3 min AFTER the freeze; the 'MCP connection closed server=hound' line is that manual kill, not the cause.)

MECHANISM: emus4n worktree isolation runs opencode with --dir <worktree> (oc_runipd.py:1640, agent_dir=work_dir at :1624), cwd inside .aw/worktrees/<id6>. But build_prompt (:1225+) REQUIRES the agent to use main-repo paths: Required JSON outcome .aw/records/runs/<run>/outcomes/NN-<id6>.json, decisions-and-questions.md, execution-report.md, and the runbook --file - ALL under state['repo'], OUTSIDE the worktree. First access -> opencode external_directory permission gate -> 'asking' -> infinite wait under --auto non-interactive.

WHY IT'S NEW: distinct from xmqv5l (stale receipt at finalize) and from any hound MCP issue. This is a direct consequence of adding worktree isolation (emus4n): before isolation cwd WAS the main repo, so run-dir access never crossed a boundary.

DESIGN PRINCIPLE (corrected): the isolated worktree is a FULL checkout of the whole repo; the agent should do EVERYTHING inside its own worktree and NEVER touch the real/main repo. So the fix is NOT to grant the agent access to the main repo (that defeats isolation) - it is to stop the driver from pointing the agent at main-repo paths. Keep the agent wholly in-lane.

FIX (primary: 1; plus backstop 2):
1) KEEP RUN ARTIFACTS IN-LANE. The driver's prompt (build_prompt, oc_runipd.py:1225+) currently hands the agent absolute main-repo paths for the outcome JSON, decisions register, and report (all under state['repo']/.aw/records/runs/<run>/). For an isolated turn these MUST be paths INSIDE the agent's own worktree (relative to cwd, e.g. .aw/records/runs/<run>/... resolved within .aw/worktrees/<id6>, or a lane-local scratch dir), so the agent writes only inside its tree and never crosses the external_directory boundary. The driver, which owns both trees, HARVESTS those artifacts from the worktree during lane integration/teardown (it already reads the branch diff there). The runbook --file is read-only context: attach it by value/copy into the lane rather than referencing a main-repo path. Net: no main-repo path ever appears in an isolated agent's instructions. Apply to BOTH oc_runipd.py and agy_runipd.py.
2) DEFENSIVE BACKSTOP (regardless of 1): a non-interactive --auto turn must NEVER wait forever on a permission prompt. Enforce a per-turn no-event watchdog/timeout that kills + records failed-safely, and/or configure opencode so an unanswerable prompt in a non-interactive run auto-denies rather than blocks. Overlaps kjzlgw (graceful-quit) but the no-answerer-hang guard belongs independently - it prevents this ENTIRE CLASS of silent infinite hangs, not just this instance.

OPEN COMPLEXITIES (to resolve when this is graduated to an IPD - do NOT hand-wave):
- Run-dir ownership across lanes: run state (manifest.json, state.json, driver.lock, the ledger) is single and lives in the MAIN repo; only per-child artifacts should be lane-local. Define precisely which files are lane-local (agent-written: outcome/decisions/report) vs driver-owned-main (ledger/manifest/lock), and how the harvest reconciles them without the agent ever writing driver-owned state.
- Harvest timing vs the merge gate: artifacts must be collected from the lane BEFORE teardown_worktree, and must NOT themselves become part of the merged-to-main diff unless intended (they may be gitignored run material, not product code) - clarify interaction with execute_merge_and_revalidate_gate and .gitignore.
- Path identity: a path like '.aw/records/runs/<run>/...' means different absolute locations in the lane vs main; ensure the agent's relative writes land where the driver later looks, and that a resumed/recovered run can still find them.
- The runbook and OTHER read-only main-repo references (completed prerequisite artifacts, current orchestrator) the prompt tells the agent to read: these are also main-repo paths. Copying everything into the lane is heavy; decide read-only-context strategy (copy vs a narrowly-scoped read grant vs relying on the full checkout already containing them at HEAD).

REPRO: aw oc run <set> with isolation on (default), where the agent is instructed to read/write the main-repo run-dir; the turn hangs at the first external_directory access with no TTY to approve.

TEST: (a) a worktree-isolated non-interactive turn is launched with NO main-repo path in its instructions and completes without any external_directory prompt; the driver harvests the outcome/decisions/report from the lane. (b) a simulated unanswerable permission prompt in a non-interactive turn is bounded by the watchdog (killed + recorded failed-safely), never an infinite wait.
