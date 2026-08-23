<!-- Durable turn-2 skeptical audit prompt for general prompt/file execution. Fed by tools/agy_run.py. Version-controlled on purpose. -->
Perform a skeptical verification of the task you just completed in this session:

1. Inspect git diff: verify all changes made in this turn. Confirm every file touched is in-scope and intentional.
2. Verify completeness: check that every element of the initial prompt/brief was completely fulfilled without missing edge cases or skipped steps.
3. Verify test coverage: run relevant tests and the full test suite using EXACTLY the canonical command `make test` (this is `pytest -n auto`, ~40s; do NOT use a serial `unittest discover` full-suite run). Paste the actual `make test` output.
4. Correct any gaps or defects discovered during this inspection immediately before producing your final report. Write target-repo files via `run_command` ONLY; never call `write_to_file` on a target-repo path (it is sandboxed to the brain dir and will be rejected).

Report back with:
- Summary of verified changes
- Actual test execution output
- Corrections made during audit (if any)
- Final status
