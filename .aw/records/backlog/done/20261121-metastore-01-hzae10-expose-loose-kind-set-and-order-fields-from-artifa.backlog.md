- Id: hzae10
- Status: done
- Set: metastore
- Work-Kind: chore
- Priority: low
- Summary: Expose loose Kind, Set, and Order fields from artifact_meta.read_text for D-4 callers
- Short-Description: Expose loose Kind, Set, and Order fields from artifact_meta.read_text for D-4 callers

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 done (aw set): Moot after metastore cutover: post-cutover records store Kind/Set/Order in JSONL logs rather than inline bullets.
- 2026-11-22 created (aw backlog): Expose loose Kind, Set, and Order fields from artifact_meta.read_text for D-4 callers

During IPD k86yq7 execution, artifact_meta.read_text parsed loose leading whitespace bullets (loose_bullets) for Id, Status, Blocks-Release, and six reference keys, but omitted Kind (plan_role), Set, and Order. runner_shared.parse_plan_file worked around this by normalizing loose bullet prefixes before calling artifact_meta.read_text to preserve D-4 tolerance without widening scope into artifact_meta.read_text. Expose those loose fields directly in artifact_meta.read_text so callers need no pre-normalization helper.
