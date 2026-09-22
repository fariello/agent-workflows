- Id: 3g5oj9
- Status: open
- Blocks-Release: next
- Set: 3g5oj9
- Priority: high
- Work-Kind: bug
- Summary: SuiteCheckResult.summary was ALWAYS empty in production: run_suite_check read tool_event['stdout_excerpt'], a key build_tool_event has never written, so every gate refusal said 'no summary line parsed' and could not name a failing test

## Workflow history
- 2026-09-20 created (aw backlog): Found and FIXED while executing daexj1 (E-01), and it is the defect F-10 predicted. oc_runipd.run_suite_check read stdout_excerpt/stderr_excerpt; run_evidence.build_tool_event writes only stdout_sha256/stderr_sha256 and lengths, and max_output_bytes truncates BEFORE hashing, so the summary regex always searched the empty string. MEASURED before the fix on a real run_suite_check: summary='' and reason='... (no summary line parsed)'. The existing test passed only because it STUBBED capture_command and fabricated the key (tests/test_novalnomerge_integration.py), which is why review never caught it. Fixed by deriving both the summary and the failing node ids at capture time and persisting only those. Can be closed as done citing daexj1.
