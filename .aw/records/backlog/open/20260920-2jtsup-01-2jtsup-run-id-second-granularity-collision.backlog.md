- Id: 2jtsup
- Status: open
- Blocks-Release: next
- Set: 2jtsup
- Priority: medium
- Work-Kind: bug
- Summary: new_run_id can collide: two runs started within one second from one process share a run directory

## Workflow history
- 2026-09-20 created (aw backlog): Found while wiring the standalone audit verb (plan mp289j).

MEASURED 2026-09-20 at HEAD 4b8f22b5: `runner_shared.new_run_id()` returns `run-<UTC seconds>-<pid>`, so two calls from ONE process inside ONE second return the IDENTICAL id. Verified directly: `{new_run_id(), new_run_id()}` has length 1.

WHY IT MATTERS. A run directory is the container for state.json, events.jsonl, outcomes/, prompts/ and sessions/. Two runs sharing one id share all of that, so the second silently overwrites the first's state and outcomes. For the LONG-LIVED queued runs this helper was written for the window is narrow (a human rarely starts two runs in the same second, and the pid differs across shells), which is presumably why it has never been hit. It is NOT narrow for a short, on-demand, repeatable verb: `aw oc run audit <id6>` run twice in quick succession from one shell is an entirely ordinary thing to do, and it collided on the first attempt in testing.

WORKED AROUND LOCALLY, NOT FIXED. Plan `mp289j` needed the append guarantee for its verdict destination, so `oc_runipd._fresh_audit_run_dir` suffixes the base id (`-2`, `-3` ...) until `mkdir(exist_ok=False)` succeeds, which is atomic against a concurrent audit. That guards the audit verb ONLY. Every other caller of `new_run_id` still takes the raw value.

THE REAL FIX is in the shared helper, and it was deliberately not made there because changing `new_run_id`'s format alters run ids repository-wide (including how they sort, how they are parsed by the analytics reader, and what operators have in their shell history) for a hazard only one verb had measured. Candidates: sub-second precision in the stamp, a short random suffix, or lifting the `mkdir(exist_ok=False)` loop into the helper so every caller inherits it. The third is the smallest behavioral change: the id format is unchanged for the common case and only a genuine collision produces a suffixed name.

EVIDENCE: `agent_workflows/runner_shared.py` `new_run_id`; `agent_workflows/oc_runipd.py` `_fresh_audit_run_dir`; `tests/test_standalone_verify.py::TheVerdictDestination::test_two_invocations_cannot_collide_so_a_second_opinion_cannot_erase_the_first`.
