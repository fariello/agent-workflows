- Id: a88210
- Status: done
- Blocks-Release: next
- Set: promptid6
- Priority: medium
- Work-Kind: bug
- Summary: aw rename <type> --to-id6 injects a '- Id:' bullet under the H1 of any artifact with no Status/Date bullet, which for walkthroughs and roadmaps puts metadata in the body

## Workflow history
- 2026-09-25 done (aw set): fixed in ed10d555: --to-id6 converts dated legacy names and never writes an Id into a document body; tests TestToId6DatedLegacyNames (fail when either fix is reverted); suite 1865 passed, 1 skipped
- 2026-09-23 created (aw backlog): aw rename <type> --to-id6 injects a '- Id:' bullet under the H1 of any artifact with no Status/Date bullet, which for walkthroughs and roadmaps puts metadata in the body

FOUND WHILE EXECUTING IPD ubac5n (promptid6), which repaired exactly this defect for PROMPTS only.

WHAT IS WRONG: artifact_rename._update_frontmatter_metadata injects a '- Id: <id6>' bullet anchored after '- Status:', else after '- Date:', else AFTER THE FIRST '# ' HEADING. That third anchor is a silent fallback, not a validated placement: for an artifact type that carries NO front-matter bullets it drops a metadata line into the document BODY.

WHERE: agent_workflows/artifact_rename.py:_update_frontmatter_metadata (the insert_at fallback loop).

MEASURED 2026-09-23 in this repository: at least 10 tracked walkthroughs and 1 roadmap have no '- Status:' or '- Date:' bullet in their first 6 lines, so 'aw rename walkthroughs <legacy> --to-id6' (the flag is GENERIC on the shared rename verb, not per type) would place '- Id:' directly under their H1. Examples: .aw/records/walkthroughs/20260823-highpbacklog0822-execution-decisions.walkthrough.md, .aw/records/roadmaps/20260712-1426-agent-workflows-bounded-iteration-skills-roadmap-for-consideration.roadmap.md.

WHY ubac5n DID NOT FIX IT: for prompts the consequence is a violation of approved spec 20260808-1958-01-prompt-purity-lint (visible text in a pasteable prompt), so ubac5n E-04 routed prompts to their own metadata comment and DELIBERATELY did not widen the change ('DO NOT WIDEN THIS INTO THE OTHER TYPES'). For walkthroughs/roadmaps there is no purity spec, so the harm is cosmetic-to-moderate (a stray bullet in prose) rather than a contract breach, which is why this is filed rather than folded in.

WORK-KIND bug ON THE USER-PERCEPTIBLE TEST: a user running a documented, shipped verb gets a visible edit to their document body that they did not ask for and that no check reports. It is not an inefficiency question.

SUGGESTED FIX: make the H1 fallback EXPLICIT per type rather than universal. Either (a) refuse to inject when no front-matter bullet region exists, reporting that the id6 lives in the filename only (the honest outcome ubac5n adopted for a comment-less prompt), or (b) give each bulletless type a declared metadata home. Do NOT simply move the anchor: a plan or spec legitimately needs the bullet, and ubac5n's tests pin that behavior as byte-unchanged.
