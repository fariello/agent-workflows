- Id: l23v3j
- Status: done
- Blocks-Release: next
- Set: l23v3j
- Priority: high
- Work-Kind: bug
- Summary: aw specs note destroys every prior inline Workflow history record and the sidecar it defers to does not hold them

## Confirmed sibling: `aw specs set` has the identical defect

CONFIRMED by measurement rather than left as a suspicion. `aw specs set` destroys inline history
EXACTLY as `aw specs note` does, because both route through the same `_append_history` helper.
Measured in a throwaway fixture: a spec with three inline records, after
`aw specs set <path> --status to-review --message advance`, retained ZERO of them (3 in, 0
preserved), leaving only the new transition record.

Call sites sharing the helper are `specs.py:642` and `specs.py:852` (the `set` paths) and
`specs.py:878` (the `note` path), so a single fix at `_append_history` covers all three.

THIS WIDENS THE BLAST RADIUS MATERIALLY: every spec status transition in this repository, including
the human-attested approval path, silently deletes the spec's prior amendment provenance. No status
transition was performed on any real spec while measuring; the fixture was a throwaway and has been
removed.

## Workflow history
- 2026-09-23 done (aw set): Already FIXED by executed plan vhbvwz (setterguard Order 02, commit fbf85068), which reversed the slimming in specs._append_history and backlog._reattach_history so both PREPEND and PRESERVE prior rounds. Verified live at HEAD 22cf67d9 by probing specs._append_history on a 3-round fixture: 4 rounds out, all 3 priors intact. The maintainer's 2026-09-10 ruling (vhbvwz OQ-01) made inline history the DURABLE home for specs and backlog items, matching plans, so this item's fix-option (a) (re-track the gitignored sidecar) is settled against. Closed via the SATISFIED path. What SURVIVED this family is tracked by IPD 7jqev2 (histresid): the migration slimmer, the oldest-first legacy reader, and the missing specs dedup.
- 2026-09-20 created (aw backlog): Found while executing plan wenmg4, which is REQUIRED by its own execution contract to record its spec correction via 'aw specs note' rather than by hand. MEASURED, and reproduced minimally in a throwaway fixture: a spec carrying three inline history records had ZERO of them left after one 'aw specs note' call (3 in, 0 preserved, and the command reported success as 'appended a history record'). On the real target, spec 25kzda, the call silently deleted FOUR pre-existing records (2026-09-19 m7gvuz, two 2026-09-14, 2026-09-13), each a substantive multi-sentence amendment record. I restored all four verbatim by hand from 'git show HEAD:<path>' and verified the restoration byte-for-byte, so no history was lost in the committed result; but the loss is silent, and an agent who did not diff the history region would have committed the deletion without noticing, because the command prints 'appended'. CAUSE, at specs.py:342-359 '_append_history': the comment says 'awhistory Order 02: the inline Workflow history section keeps only the LATEST record; the full chronological log lives in the global .aw/records/history.jsonl sidecar', and the code does exactly that, replacing the whole section body with 'new_section = ["", record]'. So the truncation is DELIBERATE. THE DEFECT IS THAT ITS PREMISE DOES NOT HOLD IN THIS REPOSITORY: .aw/records/history.jsonl is UNTRACKED ('git cat-file -e HEAD:.aw/records/history.jsonl' -> exists on disk but not in HEAD) and it contained exactly ONE record afterwards, mine. It never held the four it was supposed to be the durable home of. So the design trades tracked, reviewable, committed history for an untracked local file that does not have the data, which is not a relocation, it is a deletion. THREE THINGS MAKE THIS WORSE THAN AN ORDINARY BUG. First, the destroyed content is exactly the provenance the repository's own contracts treat as load-bearing: every spec amendment's reasoning. Second, AGENTS.md and this plan both INSTRUCT agents to prefer 'aw specs note' over hand-appending, so following the documented path is what triggers the loss. Third, it is silent and the success message actively misleads. NOTE the same file's 'aw specs set' path may share '_append_history' and therefore the same behavior; that was not measured here and should be checked. RECOMMENDED FIX DIRECTION, for a maintainer to rule on rather than for this report to decide: either preserve the inline records (append rather than replace) or make the sidecar genuinely durable and tracked AND migrate the existing inline records into it before truncating any, with the truncation refusing while the sidecar cannot be written. Gated on the next release because it silently destroys tracked provenance on a documented happy path.
