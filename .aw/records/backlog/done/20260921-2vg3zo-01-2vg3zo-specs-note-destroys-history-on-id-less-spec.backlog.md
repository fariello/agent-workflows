- Id: 2vg3zo
- Status: done
- Blocks-Release: next
- Set: 2vg3zo
- Priority: high
- Work-Kind: bug
- Summary: aw specs note DESTROYS a spec's prior inline history record when the spec carries no - Id: field, because the sidecar append no-ops and the inline slim still runs

## Workflow history
- 2026-09-23 done (aw set): Already FIXED by executed plan vhbvwz (commit fbf85068). This item's SPECIFIC claim was the id-LESS spec path, where the sidecar append no-ops and the inline slice was said to destroy the prior record. Probed that exact case live at HEAD 22cf67d9: specs._append_history on a 2-round spec carrying NO '- Id:' bullet returned 3 rounds with both priors intact, so the id-less path preserves history like any other. Closed via the SATISFIED path; surviving family work is IPD 7jqev2 (histresid).
- 2026-09-21 created (aw backlog): Measured 2026-09-21 executing plan mzc019. specs._append_history deliberately keeps only the LATEST inline record (awhistory Order 02), on the premise that the full log lives in the .aw/records/history.jsonl sidecar. But specs._sidecar_append returns EARLY when the spec has no '- Id:' field, and 19 of 36 specs in this tree have none. So for those specs the slim runs while the sidecar append does not, and the prior record is destroyed with no copy anywhere. Reproduced on 20260802-1904-01-ipd-structure-and-linting.spec.md: 'aw specs note' removed its 2026-08-26 record and wrote nothing to the sidecar; I restored the lost line by hand from git. Note the sidecar is also gitignored, so even when it IS written the durable record is local-only. FIX SHAPE: make the slim conditional on the sidecar append having actually succeeded (fail closed: keep the inline records when the record cannot be preserved elsewhere).
