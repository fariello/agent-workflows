- Id: s4jctz
- Status: graduated
- Graduated-To: s4jctz
- Set: s4jctz
- Priority: low
- Work-Kind: chore
- Summary: two noqa F401 re-exports in the host runners are justified only by a deleted test file

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: sznlsf
- 2026-09-28 note (aw backlog): Maintainer ruling: We do not test to make sure code does not change or pin imports. The deleted test will not be restored. Evaluate re-exports on whether functional callers use them, not based on dead code-pinning tests.
- 2026-09-28 created (aw backlog): two noqa F401 re-exports in the host runners are justified only by a deleted test file

Found while authoring plan t0ovw6 (backlog xw4rb7), measured at HEAD 98e3ea9a.

WHAT IS WRONG. Both host runners carry an identical line:

    from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - a DELIBERATE re-export; tests/test_runner_refork_guard.py requires it

(in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`). `tests/test_runner_refork_guard.py` was DELETED in 19313eed. So each re-export's ONLY stated justification is a test that does not exist, and the `# noqa` suppresses the linter that would otherwise flag the now-unexplained import.

WHY THIS IS NOT SIMPLY 'DELETE THEM'. A re-export is a surface: something may import `oc_runipd._read_id` even though the underscore says it should not, and the deleted test is not evidence of what else does. Plan t0ovw6 deliberately declines to remove them for exactly this reason (it corrects the COMMENTS and keeps the imports), because removing a re-export on the strength of a deleted test's absence is an unmeasured change.

THE WORK. Measure what actually reads `_read_id` from either host module (and whether anything outside the repo plausibly could, given the modules are not in `__init__`'s re-export set and `runner_shared` declares no `__all__`). Then either delete both lines with the `# noqa` or re-justify them against something real. Note that plan t0ovw6 will already have replaced the stale citation with a note recording the deletion, so the comment will no longer be FALSE by the time this item is worked; what remains is that the import is unjustified.

FILED chore AND low: nothing is user-visible and nothing is broken; this is a dead justification on two lines.
