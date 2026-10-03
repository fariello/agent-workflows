- Id: in7pfz
- Status: graduated
- Graduated-To: in7pfz
- Set: in7pfz
- Priority: low
- Work-Kind: chore
- Summary: Neither aw backlog check nor aw specs check detects a duplicated single-valued metadata field, so a duplicated - Blocks-Release: or - From-Backlog: on a backlog item or spec is invisible while the same duplicate on a plan is reported as IPD-M102

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: 1znlxy
- 2026-09-30 created (aw backlog): Neither aw backlog check nor aw specs check detects a duplicated single-valued metadata field, so a duplicated - Blocks-Release: or - From-Backlog: on a backlog item or spec is invisible while the same duplicate on a plan is reported as IPD-M102

MEASURED 2026-09-30 at HEAD `d7328e8e` while authoring plan `izh17y` from backlog item `71wqol`.

THE GAP. A duplicated single-valued metadata bullet is DETECTED on a plan and INVISIBLE on a backlog item and on a spec.

On a PLAN, `ipd_schema.parse_metadata_block` counts field occurrences and emits `duplicate field` on the second, which `ipd_lint.check_metadata` routes to `IPD-M102`. Measured on a plan carrying two `- From-Backlog:` lines:

        $ aw ipd lint <plan>
        ! IPD-M102: From-Backlog: duplicate field

On a BACKLOG ITEM and a SPEC there is no equivalent. `backlog.parse_item` iterates lines and keeps the FIRST match per field (`if m and getattr(item, attr) is None`), so a second occurrence is silently discarded and never counted; `specs.validate_spec` likewise reads each field with a single `.search()`. Measured on files carrying two `- Blocks-Release:` / `- From-Backlog:` lines respectively:

        $ aw backlog check
        aw backlog check: all backlog items conform.
        $ aw specs check
        aw specs check: all specs conform.

`aw check all` reported the duplicate nowhere either.

WHY `chore` AND NOT `bug`, stated so the classification can be disputed on its reasoning. Plan `izh17y` closes the only TOOLED producer of this state: it repairs `releases._BLOCKS_RELEASE_LINE_RE` and `releases._FROM_BACKLOG_LINE_RE`, whose `\\S+` value group is what let a writer duplicate a field it meant to replace. Once that lands, no `aw` command can create the duplicate, so the only remaining producer is a HAND EDIT. No user-perceptible impact is measured (per AGENTS.md's perceptibility test), and nothing in the corpus carries the condition today: `rg -c '^- (From-Backlog|Blocks-Release|From-Spec|Graduated-To):[ \\t]*$' .aw/records/` returns nothing and `aw check plans` reports no `IPD-M102`. So this is a detection gap worth closing, not a live defect.

SCOPE IF TAKEN UP. Add a duplicate-field finding to `backlog.validate_item` and `specs.validate_spec`, needing its own severity decision and its own corpus measurement. It is deliberately NOT part of `izh17y`, whose `- Scope-Paths:` covers neither validator and whose concern is the writer that creates the condition rather than a detector for it (recorded as that plan's OQ-02).

HONEST LIMIT. A detector here would catch a hand edit only, which is exactly why it is low priority. The reader patterns are also unaffected: `releases._ITEM_BLOCKS_RELEASE_RE` and `releases._ITEM_FROM_BACKLOG_RE` keep their strict `\\S+` shape deliberately (see `izh17y` F-05), so a duplicated field still READS as its real value rather than as absent.

RELATED. Plan `izh17y` (writer repair plus `--from-backlog` setter refusal) measured this gap, declined it as out of scope, and carries this id6 in its `## Deferred` rows.
