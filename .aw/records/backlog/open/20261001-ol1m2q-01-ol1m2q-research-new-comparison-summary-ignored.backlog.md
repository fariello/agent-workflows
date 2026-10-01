- Id: ol1m2q
- Status: open
- Blocks-Release: next
- Set: ol1m2q
- Priority: low
- Work-Kind: bug
- Summary: aw research new-comparison silently ignores --summary: plan_new_comparison passes a fixed per-file string to _mk so the user value is never written, and the flag is documented as a one-line human summary

## Workflow history
- 2026-10-01 created (aw backlog): aw research new-comparison silently ignores --summary: plan_new_comparison passes a fixed per-file string to _mk so the user value is never written, and the flag is documented as a one-line human summary

FILED WHILE AUTHORING plan `deftzy` (Set `7w6zsl`), which GUARDS this parameter without making it live.

MEASURED 2026-10-01 in a lane at HEAD `9e813570a`.

`aw research new-comparison` accepts `--summary`, documented as `One-line human summary`, and `research_cmd.plan_new_comparison` accepts it as a keyword. But its inner `_mk(order_n, kind, model, sm)` is called with a FIXED string for every planned document, and `build_frontmatter` receives `sm or summary`, so the user's value is reached only when the fixed string is empty, which it never is. Driven with `--summary $'legit\nstatus: active'` on a three-file comparison set: the planned files carried `summary: Originating prompt for the comparison set.`, `summary: gpt56 report.` and `summary: Synthesis of the model reports.`, and the user value appeared nowhere. Exit 0, no warning, no note.

WHY THIS IS A BUG RATHER THAN A DESIGN. The flag is advertised, accepted, and silently discarded, so a user who passes it reasonably believes the records carry their summary and gets three generic placeholders instead. The alternative reading, that the per-file strings are deliberate and the flag is vestigial, is contradicted by the code itself: `sm or summary` exists specifically to fall back to the user value, so the intent was clearly for it to matter.

`Priority: low` AND `Work-Kind: bug` ARE BOTH DELIBERATE. It is a `bug` because it is user-perceptible: the flag does nothing a user can see it doing. It is `low` because the damage is a generic summary on three freshly-created scaffold documents the author is about to edit anyway, not lost or corrupted data.

WHAT THE FIX MUST DECIDE, since it is not a one-liner: whether a user `--summary` REPLACES the per-file string on every document (which loses the useful `gpt56 report.` / `Synthesis of the model reports.` distinctions that tell a reader which file is which), PREFIXES or SUFFIXES it, or applies only to the `00` prompt. The last is probably closest to the flag's intent, since the prompt is the set's subject document, but it is a choice a human should make rather than an executor.

`deftzy` DELIBERATELY DOES NOT FIX THIS and that is recorded in its own Deferred section. It adds the descriptive-safety guard to the parameter because the parameter is accepted and consumed as `sm or summary`, so a future edit that makes it live would otherwise reopen the injection vector; making it live AND guarding it in one change would be two user-visible behavior changes in one commit. So when this item is implemented, the guard is already in place and no new validation is owed.
