- Id: suugsf
- Status: graduated
- Set: coauthor
- Priority: high
- Work-Kind: bug
- Summary: installed agent contract never warns that other agents or humans share the checkout, so agents sweep others' uncommitted work into their own commits

## Workflow history
- 2026-08-29 graduated (aw set): Graduated to plan a5ni7v (review-ready).
- 2026-08-29 created (aw backlog): installed agent contract never warns that other agents/humans share the checkout; agents sweep others' uncommitted work into their commits (observed: Gemini under agy committed another session's run_viewer.py edits)

Observed 2026-08-29 in this repo. Gemini (running under `aw agy run`) committed `bd3fed1`
"feat(run_viewer): add pid liveness, runtime, and multi-line run header", which SWEPT another
session's uncommitted `agent_workflows/run_viewer.py` and `agent_workflows/cli.py` edits into it. The
commit message is a single subject line with no body and makes NO mention of the swept work (no
`abandoned?` projection, no `driver_holder_state`, no `repair_run`, no reference to plan `ssk6nf`).
The other session then had to declare `already-committed` to its own finalize scope gate, because its
declared in-scope files showed as unmodified: the provenance was only recoverable from the OTHER
commit's body. Same session also observed: an uncommitted `functools` import break in
`artifact_core.py` that broke every `aw` command for another agent mid-run.

CORRECTION (maintainer, 2026-08-29): this was NOT a runner turn. It was a LIVE / interactive `agy`
session. Verified: no run ledger under `.aw/records/runs/*/state.json` references `bd3fed1`, so no
driver managed that commit.

That correction makes the defect WORSE, not milder, and relocates the primary gap. The
`## Concurrent Work` warning at `agy_runipd.py:1573-1579` (and its `oc` twin) is injected into the
DRIVER PROMPT only, so it never reached this session at all. And per `host_adapters.py:83` the
`antigravity` host's pointer file is `AGENTS.md` - the interactive agent's ONLY standing instruction
source is exactly the block proven silent on concurrency below. So for every non-runner session
(interactive agy, an ad-hoc Claude/Gemini/Codex session, a human's own agent) the concurrency rule
DOES NOT EXIST anywhere it can be read.

GAP 1 (PRIMARY: the installed contract is silent, and it is the only thing an interactive agent
reads). The `AGENTS.md` block written at install time by
`engine.py:1137` ("### Agent execution contract") says "commit ONLY files you changed, path-scoped...
never `git add -A`/bare/`-a`" but NEVER states that other agents or humans may be working in the same
checkout. Verified by scanning that block: `concurrent`, `other agent`, `another agent`,
`shared checkout`, `unrelated`, `sweep`, `git status`, and `staged` are ALL absent. An agent reading
only `AGENTS.md` - which is EVERY non-runner session, including interactive `agy` (the actual observed
case) and any ad-hoc Claude/Gemini/Codex session - is never told the checkout is shared. The
`## Concurrent Work` warning exists ONLY in the driver prompt, so it does not reach them. Corollary
for the fix: putting the warning in the driver prompts alone would NOT have prevented the observed
incident; it must live in the installed `AGENTS.md` block.

GAP 2 (no VERIFICATION step anywhere). Neither the installed contract nor the driver prompt tells the
agent how to CHECK what it is about to commit. This gap is host-independent: it applies to runner and
interactive sessions alike. Verified: `git status`, `git diff --cached`, and
`verify` appear nowhere in the `## Concurrent Work` block. "Stage only your files" is unactionable
advice unless the agent is told to enumerate the staged set and compare it against the files it
actually edited. The fix should require inspecting `git diff --cached --name-only` before committing
and refusing any path the agent did not itself modify.

Minor, same area: the delivered prompt text at `agy_runipd.py:1577` uses a CURLY apostrophe
("another agent's"), inconsistent with the repo's plain-ASCII posture for delivered artifacts.

Scope note: this must land in the INSTALLED artifacts (the `engine.py` AGENTS block, so every managed
repo gets it on install/update) and not only in this repo's own `AGENTS.md`, or it fixes one repo and
no adopters.
