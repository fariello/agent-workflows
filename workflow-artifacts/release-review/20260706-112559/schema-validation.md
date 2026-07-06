# Schema validation

NOT APPLICABLE in the data-schema sense. The repo defines no JSON/YAML/DB schemas or data
contracts for external data. The closest "contracts" are:
- index.md manifest column format (command|body|lens|description) - validated implicitly by the
  installer parsing it; Section 1 dry-run showed no drift.
- The tools' JSON output shapes (scan_secrets, run_checks, bench_env) - covered by their self-tests
  (e.g. test_json_capture_has_required_context_fields).
No SCH findings.
