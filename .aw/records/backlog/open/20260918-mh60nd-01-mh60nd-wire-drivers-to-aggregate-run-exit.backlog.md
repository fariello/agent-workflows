- Id: mh60nd
- Status: open
- Set: mh60nd
- Priority: medium
- Work-Kind: followup
- Summary: Wire the drivers to run_evidence.aggregate_run_exit so a needs_input run returns spec 25kzda 5.6's exit 3 instead of 1

## Workflow history
- 2026-09-18 created (aw backlog): Wire the drivers to run_evidence.aggregate_run_exit so a needs_input run returns spec 25kzda 5.6's exit 3 instead of 1

Found while executing plan `zz5yxq` (runnoop Order 01), whose OQ-02 records this as a discoverable follow-on outside its fence.

THE GAP, measured. `run_evidence` already agrees with the approved spec: `_CLASSIFICATION_EXITS` maps `needs_input: 3`, `_CLASSIFICATION_PRIORITY` makes 3 outrank a plain item failure (1), and `aggregate_run_exit` already raises the candidate from `any(result.item.needs_input ...)`. The ONLY thing missing is that NEITHER DRIVER CALLS IT: measured zero call sites for `aggregate_run_exit` in `oc_runipd` or `agy_runipd` (the sole mention is a comment).

CONSEQUENCE. `zz5yxq` fixed the measured silent-0 (an approval-blocked queue now exits 1 instead of 0), but 1 means "an item failed", not "a human gate needs input", so a caller cannot distinguish an approval-blocked run from a genuinely failed one by exit code alone. The durable per-item fact IS now on the queue entry (`needs_input: true`, byte-equal to `run_gates.GATE_STATUS_NEEDS_INPUT`), so the input the aggregator needs already exists in run state.

WHY IT WAS NOT DONE IN zz5yxq. Wiring the drivers to the aggregator changes EVERY run's exit classification, not just this case, which is far beyond a `reviewed`-item fix and deserves its own plan and its own review.

WHERE. `agent_workflows/run_evidence.py` (`aggregate_run_exit`, `AggregatedItem`, `_CLASSIFICATION_EXITS`), and the exit-code sites in `agent_workflows/oc_runipd.py` / `agent_workflows/agy_runipd.py` that currently call `runner_stop.deliberate_stop_exit_code` via `runner_shared.exit_code_statuses`. Do NOT edit `_CLASSIFICATION_EXITS`; it already matches the spec.
