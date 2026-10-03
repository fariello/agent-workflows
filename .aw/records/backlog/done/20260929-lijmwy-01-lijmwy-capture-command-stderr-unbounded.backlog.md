- Id: lijmwy
- Status: done
- Graduated-To: lijmwy
- Blocks-Release: next
- Set: lijmwy
- Priority: low
- Work-Kind: bug
- Summary: capture_command truncates stdout but never stderr, so max_output_bytes bounds only half the captured output

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD 75gxkj executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-lijmwy-01-75gxkj-bound-stderr-against-max-output-bytes-with-a-per-stream-cap.ipd.md); evidence .aw/records/plans/executed/20261001-lijmwy-01-75gxkj-bound-stderr-against-max-output-bytes-with-a-per-stream-cap.ipd.md
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: 75gxkj
- 2026-09-29 created (aw backlog): capture_command truncates stdout but never stderr, so max_output_bytes bounds only half the captured output

MEASURED 2026-09-29 while authoring the plan graduating backlog he9x6j, at lane HEAD a5b36500.

`run_evidence.capture_command` applies its `max_output_bytes` cap to `stdout_raw` ONLY. `stderr_raw` is
never truncated and never contributes to the `truncated` flag.

MEASUREMENT: with `max_output_bytes=10` against a command writing 100 bytes to each stream, the resulting
tool_event reads `stdout_len: 10` (truncated) and `stderr_len: 101` (not truncated), with `truncated: True`
describing only the stdout half.

WHY IT IS A BUG: a caller passing `max_output_bytes` is declaring a bound on what this capture may cost, and
a stream that ignores the bound defeats it. `runner_shared.run_suite_check` passes `max_output_bytes=512_000`
and then reads BOTH streams (it parses the summary from stdout falling back to stderr, and scans both for
failure lines), so an unbounded stderr is reachable from the shipped integration gate, not only in theory.
The `truncated` flag is also then a half-truth, which matters because it is a persisted ledger field.

WHY IT IS low PRIORITY AND SEPARATE FROM he9x6j: no user-visible wrong answer has been measured from it (the
gate's parse succeeds either way), so it is a latent bound violation rather than an active defect; and
deciding the right shape (one shared budget across both streams, or a per-stream cap) is a design choice
he9x6j does not own.
