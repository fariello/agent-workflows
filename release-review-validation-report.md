# Release Review Zip Validation Report

## Verdict

The original zip did not fully meet the agreed objectives. I corrected the package and re-ran validation checks. Some validation checks still failed and are listed below.

## Important finding

The archive I examined at the start of this validation did not include the most recent requested OpenCode wrappers, controlled parallel audit lane support, schema-validation artifacts, final bug/security audit artifacts, or section-summary artifacts. I added those missing pieces and regenerated the zip.

## Files in corrected zip

- `.opencode/commands/release-review-plan.md`
- `.opencode/commands/release-review.md`
- `release-review/00-run-protocol.md`
- `release-review/01-current-state.md`
- `release-review/02-quality-security-edge-cases.md`
- `release-review/03-tests-regression.md`
- `release-review/04-docs-specs-examples.md`
- `release-review/05-feature-usability-maintainability.md`
- `release-review/06-compatibility-packaging-release.md`
- `release-review/07-implementation.md`
- `release-review/08-final-ship-review.md`
- `release-review/MANIFEST.md`
- `release-review/README.md`
- `release-review/templates/action-register.csv`
- `release-review/templates/audit-lane-report.md`
- `release-review/templates/execution-plan.md`
- `release-review/templates/final-bug-security-audit.md`
- `release-review/templates/final-response.md`
- `release-review/templates/finding-register.csv`
- `release-review/templates/implementation-plan.md`
- `release-review/templates/schema-validation.md`
- `release-review/templates/section-summary.md`

## Validation checks

- **PASS**: required file exists: release-review/MANIFEST.md
- **PASS**: required file exists: release-review/README.md
- **PASS**: required file exists: release-review/00-run-protocol.md
- **PASS**: required file exists: release-review/01-current-state.md
- **PASS**: required file exists: release-review/02-quality-security-edge-cases.md
- **PASS**: required file exists: release-review/03-tests-regression.md
- **PASS**: required file exists: release-review/04-docs-specs-examples.md
- **PASS**: required file exists: release-review/05-feature-usability-maintainability.md
- **PASS**: required file exists: release-review/06-compatibility-packaging-release.md
- **PASS**: required file exists: release-review/07-implementation.md
- **PASS**: required file exists: release-review/08-final-ship-review.md
- **PASS**: required file exists: release-review/templates/action-register.csv
- **PASS**: required file exists: release-review/templates/audit-lane-report.md
- **PASS**: required file exists: release-review/templates/execution-plan.md
- **PASS**: required file exists: release-review/templates/final-bug-security-audit.md
- **PASS**: required file exists: release-review/templates/final-response.md
- **PASS**: required file exists: release-review/templates/finding-register.csv
- **PASS**: required file exists: release-review/templates/implementation-plan.md
- **PASS**: required file exists: release-review/templates/schema-validation.md
- **PASS**: required file exists: release-review/templates/section-summary.md
- **PASS**: required file exists: .opencode/commands/release-review.md
- **PASS**: required file exists: .opencode/commands/release-review-plan.md
- **FAIL**: required phrase present: release-review/README.md remains the controlling instruction
- **PASS**: required phrase present: controlled parallel read-only audit lanes
- **PASS**: required phrase present: Section 7 implementation remains serial
- **PASS**: required phrase present: Section 8 final review remains serial
- **PASS**: required phrase present: schema-validation.md
- **PASS**: required phrase present: final-bug-security-audit.md
- **PASS**: required phrase present: SCH
- **PASS**: required phrase present: Do not commit `repository-review/` artifacts
- **PASS**: required phrase present: do not push unless explicitly permitted
- **PASS**: required phrase present: TodoWrite
- **PASS**: OpenCode command wrapper structure: .opencode/commands/release-review.md
- **PASS**: OpenCode command wrapper structure: .opencode/commands/release-review-plan.md
- **PASS**: CSV header valid: release-review/templates/finding-register.csv - id,section,type,severity,title,status,affected_area,evidence,impact,recommended_action,public_behavior_change,artifact_updates,source_files,validation,next_step
- **PASS**: CSV header valid: release-review/templates/action-register.csv - id,source_ids,section,status,description,files_changed,commit,validation,reason_not_done,next_step
- **PASS**: no em dash characters in Markdown/CSV files
- **PASS**: no ambiguous runbook README/protocol reference
- **PASS**: section 1 has standing constraints
- **PASS**: section 1 has exit criteria
- **PASS**: section 2 has standing constraints
- **PASS**: section 2 has exit criteria
- **PASS**: section 3 has standing constraints
- **PASS**: section 3 has exit criteria
- **PASS**: section 4 has standing constraints
- **PASS**: section 4 has exit criteria
- **PASS**: section 5 has standing constraints
- **PASS**: section 5 has exit criteria
- **PASS**: section 6 has standing constraints
- **PASS**: section 6 has exit criteria
- **PASS**: section 7 has standing constraints
- **PASS**: section 7 has exit criteria
- **PASS**: section 8 has standing constraints
- **PASS**: section 8 has exit criteria
- **FAIL**: section 1 exact summary path present
- **FAIL**: section 2 exact summary path present
- **FAIL**: section 3 exact summary path present
- **FAIL**: section 4 exact summary path present
- **FAIL**: section 5 exact summary path present
- **FAIL**: section 6 exact summary path present
- **FAIL**: section 7 exact summary path present
- **PASS**: section 8 exact summary path present
- **PASS**: zip contains required file: release-review/MANIFEST.md
- **PASS**: zip contains required file: release-review/README.md
- **PASS**: zip contains required file: release-review/00-run-protocol.md
- **PASS**: zip contains required file: release-review/01-current-state.md
- **PASS**: zip contains required file: release-review/02-quality-security-edge-cases.md
- **PASS**: zip contains required file: release-review/03-tests-regression.md
- **PASS**: zip contains required file: release-review/04-docs-specs-examples.md
- **PASS**: zip contains required file: release-review/05-feature-usability-maintainability.md
- **PASS**: zip contains required file: release-review/06-compatibility-packaging-release.md
- **PASS**: zip contains required file: release-review/07-implementation.md
- **PASS**: zip contains required file: release-review/08-final-ship-review.md
- **PASS**: zip contains required file: release-review/templates/action-register.csv
- **PASS**: zip contains required file: release-review/templates/audit-lane-report.md
- **PASS**: zip contains required file: release-review/templates/execution-plan.md
- **PASS**: zip contains required file: release-review/templates/final-bug-security-audit.md
- **PASS**: zip contains required file: release-review/templates/final-response.md
- **PASS**: zip contains required file: release-review/templates/finding-register.csv
- **PASS**: zip contains required file: release-review/templates/implementation-plan.md
- **PASS**: zip contains required file: release-review/templates/schema-validation.md
- **PASS**: zip contains required file: release-review/templates/section-summary.md
- **PASS**: zip contains required file: .opencode/commands/release-review.md
- **PASS**: zip contains required file: .opencode/commands/release-review-plan.md

## OpenCode compatibility basis

- OpenCode supports custom Markdown command files under `.opencode/commands/` with frontmatter fields such as `description` and `agent`.
- OpenCode supports built-in primary agents and subagents, including a full-tool `build` primary agent, a restricted `plan` primary agent, and read-only `explore`/`scout` subagents. The runbook uses command wrappers only as entry points and keeps the runbook as the source of truth.

## Recommendation

Do not use this package until the failed checks are addressed.
