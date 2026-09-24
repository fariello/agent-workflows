- Id: yvp951
- Status: done
- Blocks-Release: next
- Set: yvp951
- Priority: high
- Work-Kind: bug
- Summary: aw specs set destroys a LEGACY spec's prior workflow-history records: it keeps only the latest inline record on the premise that the full log lives in the history.jsonl sidecar, but that sidecar write is a no-op for a spec with no Id bullet, so the truncation deletes the only tracked copy

## Detail

`specs._append_history` deliberately rebuilds the `## Workflow history` section as `["", record]`,
dropping every prior inline record. The stated premise (`awhistory` Order 02) is that the full
chronological log lives in the `.aw/records/history.jsonl` sidecar. That premise fails for LEGACY
specs on two counts at once:

1. The sidecar helper extracts the id6 with `_SPEC_ID_RE` and RETURNS EARLY when the spec carries no
   `- Id:` bullet. Legacy `YYYYMMDD-HHMM-NN-<slug>.spec.md` specs have none, so nothing is ever
   written to the sidecar for them. Its own docstring acknowledges this ("specs ... only join the
   sidecar once they gain an id6").
2. `.aw/.gitignore` line 11 ignores `records/history.jsonl`, so the sidecar is not a tracked record
   even for specs that do reach it.

So for a legacy spec the truncation deletes the only TRACKED copy of its history, with no warning.

Measured in IPD `diof9n` (E-03): repointing the gates of
`20260725-0957-01-external-delivery-and-skills.spec.md` and
`20260726-1239-01-clean-delta-and-tracking-modes.spec.md` with `aw specs set` silently dropped each
spec's `2026-08-08 migrated (aw specs)` record. Both were restored by hand in that plan, so no
history is currently lost; the DEFECT remains and affects every legacy spec any `aw specs set`
touches.

Candidate fixes (needs a decision): preserve prior inline records for a spec with no id6; or mint an
id6 and write the sidecar before truncating; or stop truncating for specs entirely. Note also that
the sidecar being gitignored makes "the full log lives in the sidecar" a weak premise even for
id6-bearing artifacts.

## Workflow history
- 2026-09-23 done (aw set): Already FIXED by executed plan vhbvwz (setterguard Order 02, commit fbf85068), which reversed the slimming in specs._append_history and backlog._reattach_history so both PREPEND and PRESERVE prior rounds. Verified live at HEAD 22cf67d9 by probing specs._append_history on a 3-round fixture: 4 rounds out, all 3 priors intact. The maintainer's 2026-09-10 ruling (vhbvwz OQ-01) made inline history the DURABLE home for specs and backlog items, matching plans, so this item's fix-option (a) (re-track the gitignored sidecar) is settled against. Closed via the SATISFIED path. What SURVIVED this family is tracked by IPD 7jqev2 (histresid): the migration slimmer, the oldest-first legacy reader, and the missing specs dedup.
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): Found by IPD diof9n (E-03): repointing two legacy deferred specs' gates via aw specs set silently dropped each spec's 2026-08-08 'migrated' record; diof9n restored both by hand. Evidence: specs.py _append_history rebuilds the section as [blank, record]; the sidecar helper returns early when _SPEC_ID_RE finds no - Id:; .aw/.gitignore line 11 ignores records/history.jsonl. Affects every legacy spec that any aw specs set touches.
