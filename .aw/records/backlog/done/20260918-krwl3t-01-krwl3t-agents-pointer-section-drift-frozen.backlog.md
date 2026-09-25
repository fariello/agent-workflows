- Id: krwl3t
- Status: done
- Graduated-To: sectfreeze
- Blocks-Release: next
- Set: krwl3t
- Priority: high
- Work-Kind: bug
- Summary: AGENTS.md#aw:pointer is drift-frozen: its recorded hash no longer matches the on-disk body, so _apply_section_consent treats it as user drift and every install discards the regenerated section, meaning no future generator change to the managed block reaches this repo's AGENTS.md

## Workflow history
- 2026-09-25 set (aw backlog): closed by aw oc run: IPD b4bvas executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260924-sectfreeze-01-b4bvas-stop-managed-agents-md-sections-freezing-after-a-tracked-edi.ipd.md); evidence .aw/records/plans/executed/20260924-sectfreeze-01-b4bvas-stop-managed-agents-md-sections-freezing-after-a-tracked-edi.ipd.md
- 2026-09-25 graduated (aw set): graduated into sectfreeze plan b4bvas (to-review)
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): Found by IPD diof9n (E-05), which had to write the same sentence twice (generator plus a declared direct AGENTS.md edit) to work around it. Fixing it means either re-recording the section hash or changing _apply_section_consent consent semantics, and the second alters installer behavior for every managed repository, so it was deliberately NOT fixed in diof9n. Evidence: recorded vs on-disk hash comparison and an in-process _apply_section_consent probe showing the merge chooses the on-disk body and drops the new text.
