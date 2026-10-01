- Id: fqseay
- Status: graduated
- Graduated-To: fqseay
- Blocks-Release: next
- Set: fqseay
- Priority: medium
- Work-Kind: bug
- Summary: run_worker_process silently ignores TaskPacket.max_output_bytes, so a worker's output bound is unenforced

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: egywai
- 2026-09-29 created (aw backlog): run_worker_process silently ignores TaskPacket.max_output_bytes, so a worker's output bound is unenforced

MEASURED 2026-09-29 while authoring the plan graduating backlog he9x6j, at lane HEAD a5b36500.

`host_runner.TaskPacket` carries a `max_output_bytes` field, and `host_runner.run_worker_process` NEVER
FORWARDS IT to `run_evidence.capture_command`, which takes a `max_output_bytes=` keyword. So the bound a
caller declares on the packet has NO EFFECT.

MEASUREMENT: a packet with `max_output_bytes=100` running `python3 -c "print('A'*50000)"` returns a
`RawWorkerResult` whose `len(stdout)` is 50001, not 100.

WHY IT IS A BUG AND NOT A CHORE: the field exists precisely to bound what a worker's output can cost
downstream (that text is redacted, classified and can reach a durable record), so an unenforced bound is a
silently broken safety control rather than a tidiness issue. It is filed SEPARATELY from he9x6j because it is
a distinct defect at a different call site: he9x6j is about the output text being ABSENT, this is about the
output BOUND being ignored. Fixing it means deciding whether the packet default (None) should stay unbounded,
which is a scope decision he9x6j does not own.
