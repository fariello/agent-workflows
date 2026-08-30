- Id: lavkg7
- Status: done
- Set: awretrofit
- Priority: high
- Work-Kind: chore
- Summary: RELEASE BLOCKER: clean up .aw/records/ taxonomy (run-artifacts home, dup prompts, flatten docs/) before release

## Workflow history
- 2026-08-17 done (opencode Opus 4.8): spec 20260817-2124-01 implemented via Order 07 (executed IPD u7xtni); release gate cleared.
- 2026-08-17 created (aw backlog): RELEASE BLOCKER: clean up .aw/records/ taxonomy (run-artifacts home, dup prompts, flatten docs/) before release

Pre-release taxonomy cleanup; MUST block the release (see spec 20260817-2124-01). Three problems: (A) workflow run-artifacts (assess-*/verify/verify-execution/release-review/advise-*) at the .aw/records/ root instead of one obvious runs home; (B) duplicate prompts name (.aw/records/prompts staging vs .aw/records/docs/prompts library); (C) flatten .aw/records/docs/{research,specs,walkthroughs,roadmaps} to .aw/records/. PRE-RELEASE framing: only legacy->final migration needed, NO intermediate .aw/records/docs->final hop. Gated on the spec being approved+implemented. Surfaced by release-review run 20260817-153418; maintainer designated it a release blocker.
