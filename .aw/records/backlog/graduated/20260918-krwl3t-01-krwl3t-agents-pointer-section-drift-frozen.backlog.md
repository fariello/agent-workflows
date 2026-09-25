- Id: krwl3t
- Status: graduated
- Graduated-To: sectfreeze
- Blocks-Release: next
- Set: krwl3t
- Priority: high
- Work-Kind: bug
- Summary: AGENTS.md#aw:pointer is drift-frozen: its recorded hash no longer matches the on-disk body, so _apply_section_consent treats it as user drift and every install discards the regenerated section, meaning no future generator change to the managed block reaches this repo's AGENTS.md

## Detail

The recorded hash for `AGENTS.md#aw:pointer` in `.aw/system/managed-sections.json` is
`a9deb5a1d76e603e6c016d5ea0c2f676010bd4910297ffa16aa5b52647897fc4`; the on-disk pointer body hashes
to `935b3f1578dfce0c02123a789194bea9f309ca3d93821bac82d50ff21872dc4e`. Because a recorded hash EXISTS
and does NOT match, `engine._apply_section_consent` classifies the section as user drift and preserves
the on-disk body, discarding the regenerated one. Measured with an in-process probe driving that exact
predicate against a temp copy of the real `AGENTS.md` plus the real manifest: the generator's desired
body contained the new text, the merge chose the on-disk body, and the written body did not.

Consequence beyond the finding that surfaced it: NO future managed-block change ever reaches this
repository's `AGENTS.md`, for any generator edit, not just the one that found it.

Fixing it means either re-recording the section hash (which rewrites installer consent state to force
a delivery, the very clobber the consent model exists to prevent) or changing
`_apply_section_consent`'s semantics (which alters installer behavior for every managed repository).
Both need their own decision, which is why IPD `diof9n` deliberately did not fix it and instead wrote
the same sentence twice: once in the generator (the every-repo reach half) and once as a declared
direct edit to this repository's `AGENTS.md`.

## Workflow history
- 2026-09-25 graduated (aw set): graduated into sectfreeze plan b4bvas (to-review)
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): Found by IPD diof9n (E-05), which had to write the same sentence twice (generator plus a declared direct AGENTS.md edit) to work around it. Fixing it means either re-recording the section hash or changing _apply_section_consent consent semantics, and the second alters installer behavior for every managed repository, so it was deliberately NOT fixed in diof9n. Evidence: recorded vs on-disk hash comparison and an in-process _apply_section_consent probe showing the merge chooses the on-disk body and drops the new text.
