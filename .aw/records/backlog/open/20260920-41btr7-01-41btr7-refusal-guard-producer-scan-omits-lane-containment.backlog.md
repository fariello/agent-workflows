- Id: 41btr7
- Status: open
- Set: 41btr7
- Priority: medium
- Work-Kind: chore
- Summary: The diagnostics-block AST producer guard omits lane_containment, so reading a genuinely-written preserved_* field trips a false positive

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing plan ys1dor. tests/test_refusal_surfacing.py::TestNoFieldNameMismatch::test_every_field_the_diagnostics_block_reads_is_one_a_runner_writes builds its written-field set by AST over oc_runipd, agy_runipd and runner_shared ONLY. But item['preserved_branch'] (and every other preserved_* field) is written by lane_containment.record_preserved_lane_state at lane_containment.py:3497. So a renderer that legitimately reads preserved_branch inside the guarded diagnostics block fails the guard on a field a producer DOES write. This is the same false-positive class the guard's own docstring records for runner_shared in 2026-09-14, when 51vw4y moved the integration-refusal write into the shared library. ys1dor worked around it by lifting its read into a named function outside the guarded block and carrying an equivalent guard (with lane_containment in the scan) in tests/test_run_summary_table.py, so coverage was moved rather than lost; the underlying guard is still incomplete and will mislead the next author who reads a preserved_* field in that block. FIX: add lane_containment to the module tuple in _fields_written_by_the_runners.
