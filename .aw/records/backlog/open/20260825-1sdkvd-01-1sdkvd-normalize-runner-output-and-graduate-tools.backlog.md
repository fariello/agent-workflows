- Id: 1sdkvd
- Status: open
- Set: 1sdkvd
- Priority: medium
- Kind: followup
- Summary: Normalize runner interactive output into a shared renderer and graduate remaining tools (runagy, pwatch, agy sessions/view) under aw

## Workflow history
- 2026-08-25 created (aw backlog): Normalize runner interactive output into a shared renderer and graduate remaining tools (runagy, pwatch, agy sessions/view) under aw

Follow-on work deferred by the awocrunner Set (which graduated runipd to `aw oc runipd`). Non-blocking.

(a) Extract runipd's render_event / Palette / Heartbeat streaming layer (currently inline in agent_workflows/oc_runipd.py) into a shared agent_workflows rendering utility so interactive/progress output is normalized across consumers rather than duplicated per tool.

(b) Graduate the remaining source-checkout tools under the packaged host-subcommand pattern: agy_run.py -> `aw agy run` (renamed runagy), agy_sessions.py -> `aw agy sessions`, view-antigravity-jsonl.py -> `aw agy view`, pwatch.py -> `aw pwatch`.

(c) This follows the packaged-core + host-subcommand + compat-shim pattern established by the awocrunner Set (agent_workflows/oc_runipd.py + `aw oc` group + tools/ipdrunner/runipd.py shim). Non-blocking; can be split (renderer vs tool-graduation) when picked up.
