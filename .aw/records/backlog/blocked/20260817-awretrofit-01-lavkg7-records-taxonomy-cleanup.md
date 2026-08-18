- Id: lavkg7
- Status: blocked
- Set: awretrofit
- Priority: high
- Kind: chore
- Summary: RELEASE BLOCKER: clean up .aw/records/ taxonomy (run-artifacts home, dup prompts, flatten docs/) before release
- Gate-Kind: artifact
- Gate-Ref: .aw/records/docs/specs/20260817-2124-01-records-taxonomy-cleanup.spec.md

## Workflow history
- 2026-08-17 created (aw backlog): RELEASE BLOCKER: clean up .aw/records/ taxonomy (run-artifacts home, dup prompts, flatten docs/) before release

Pre-release taxonomy cleanup; MUST block the release (see spec 20260817-2124-01). Three problems: (A) workflow run-artifacts (assess-*/verify/verify-execution/release-review/advise-*) at the .aw/records/ root instead of one obvious runs home; (B) duplicate prompts name (.aw/records/prompts staging vs .aw/records/docs/prompts library); (C) flatten .aw/records/docs/{research,specs,walkthroughs,roadmaps} to .aw/records/. PRE-RELEASE framing: only legacy->final migration needed, NO intermediate .aw/records/docs->final hop. Gated on the spec being approved+implemented. Surfaced by release-review run 20260817-153418; maintainer designated it a release blocker.
