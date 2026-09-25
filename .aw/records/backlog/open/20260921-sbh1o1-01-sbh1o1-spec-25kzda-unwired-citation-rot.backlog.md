- Id: sbh1o1
- Status: open
- Set: sbh1o1
- Priority: low
- Work-Kind: chore
- Summary: The spec 25kzda 'built but UNWIRED' string cited by several plans no longer exists, so those citations resolve to nothing

## Workflow history
- 2026-09-21 created (aw backlog): Found by the i1hlgx execution turn while re-verifying its premise.

MEASURED 2026-09-21.

WHAT IS WRONG. Multiple artifacts cite spec `25kzda` at `:29` as reading 'the ledger is built but UNWIRED', including plan `i1hlgx` (its Concern, Step 0, F-2 and E-01) and backlog `zrzfkw`. That string is GONE: `grep -n -i 'unwired|built but'` over `.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` returns nothing. The spec's preamble was rewritten on 2026-09-20 by plan `wenmg4`.

THE UNDERLYING FACT SURVIVES, which is why this is low and a chore rather than a bug: the same file now says at `:59-62` that the hash-chained run ledger's trailers are 'STILL NET-NEW and to be built ... NOTHING PASSES THEM: zero of 3764 commits across all refs carry an AW-Run trailer', naming plan `wao266` as the owner of the wiring. So no plan's premise was false; only the quoted string and the line number were.

WHY FILE IT ANYWAY. An executor instructed to re-verify a premise by grepping for a quoted string gets ZERO hits and must then decide whether the premise died or the citation rotted. That decision is exactly the kind a tired agent gets wrong, in the direction of a spurious STOP. The spec itself anticipates this: its preamble says every dated paragraph is a point-in-time snapshot that MUST be re-measured, and notes all three of its snapshots have been measured stale at least once, with NOTHING enforcing their accuracy.

A SECOND, SMALLER INSTANCE of the same rot, found in the same pass: `i1hlgx` and `zrzfkw` both state that `oc_runipd.py` says 'ledger' exactly 13 times (a count illustrating the two-substrate naming trap). It now says it 9 times. The trap is unchanged; the number moved.

WHERE. The citations live in `.aw/records/plans/pending/20260908-ledgerhonest-01-i1hlgx-...ipd.md` (whose V-01 evidence now records the correction), `.aw/records/backlog/graduated/20260906-verifygap-01-zrzfkw-...backlog.md`, and any sibling that quotes the same line.

POSSIBLE FIX. Prefer citing the spec's stable SECTION and its claim over a line number plus a quoted sentence, since the spec's own convention is that its dated paragraphs decay. A checker that resolves quoted spec strings in artifacts would catch this class mechanically, but that is a larger piece of work than this item needs.
