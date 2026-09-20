- Id: he9x6j
- Status: open
- Blocks-Release: next
- Set: he9x6j
- Priority: high
- Work-Kind: bug
- Summary: tool_event carried no output text, so every consumer's stdout read silently yielded empty string

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing plan h5pyqa. FIXED IN THAT PLAN for the two live readers; filed so the wider class is visible.

## What is wrong

`run_evidence.build_tool_event` records `stdout_sha256`/`stdout_len` and NO output text, by design: a
`tool_event` is a ledger record. But two consumers read the text off it under keys nobody writes:

  * `oc_runipd.run_suite_check` read `tool_event["stdout_excerpt"]`
  * `host_runner.run_raw_worker` reads `tool_event["stdout"]` and `["stderr"]`

Both silently yielded `""`. MEASURED 2026-09-20 by calling `capture_command` directly: `sorted(tool_event)`
contained neither key. The visible consequence was that the integration gate's `SuiteCheckResult.summary`
was ALWAYS empty, so every suite-failure refusal reason read `no summary line parsed` instead of naming the
counts, on every run since `novalnomerge-01` shipped.

WHY NO TEST CAUGHT IT: every test of `run_suite_check` mocks `capture_command` and fabricates a
`stdout_excerpt` key that production never produced, so the mocks were testing a contract that did not exist.

## What was already fixed, and what is left

Plan `h5pyqa` made `capture_command` attach the text to the mapping it RETURNS (all four key spellings, so
both existing readers work), leaving `build_tool_event`'s persisted record shape untouched. That repairs both
live reads and is verified end to end.

LEFT FOR THIS ITEM, which is why it stays open:

1. The MOCK-SHAPE HAZARD is unaddressed. Tests may still fabricate keys production does not emit, which is
   how this hid for so long. A contract test asserting the real `capture_command` emits exactly the keys its
   consumers read would prevent the next instance.
2. The two spellings (`stdout` vs `stdout_excerpt`) were both supplied rather than unified, deliberately:
   picking one would have left the other consumer broken. Converging them is a separate cleanup.
3. Whether the text belongs in the PERSISTED ledger record (not just the returned mapping) is an open
   design question with a real cost: unbounded command output in durable records. Not decided here.
