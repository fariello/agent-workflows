- Id: cnn7au
- Status: graduated
- Graduated-To: relnextres
- Blocks-Release: next
- Set: cnn7au
- Priority: medium
- Work-Kind: bug
- Summary: Shipping the single planned release without creating its successor makes all 608 Blocks-Release: next records dangle, which a fail-closed release-gates CI step turns into a red main

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: x4vf9p
- 2026-09-26 created (aw backlog): Found in /plan-review of plan 3cs7qg (finding F-8/PR-002). releases.resolve_release maps the literal 'next' only when EXACTLY ONE release record carries Status: planned ('return planned[0] if len(planned) == 1 else None'), and check.blocks-release-dangling is a member of the release-gate family. MEASURED on a copy of .aw/records with the project config: baseline 0 findings; mark the single planned release f33nrj 'shipped' and the family reports 608 check.blocks-release-dangling; add a SECOND planned record and it is 608 again (next becomes ambiguous); ship the old record AND create its successor in the same change and it returns to 0. 608 records carry Blocks-Release: next (331 backlog, 269 plans, 8 specs). WHY IT MATTERS NOW: plan 3cs7qg E-07 flips the aw check release-gates step in .github/workflows/tests.yml from advisory to FAIL-CLOSED, so after it lands this state fails the tests workflow on main rather than emitting warnings, and it fires exactly at release time when the tree is least able to absorb it. No shipped code path writes Status: shipped (grep finds no writer), so the transition is a human act. THE FIX NEEDS A MAINTAINER DECISION and was deliberately NOT folded into 3cs7qg: either (a) make the release cycle obligated to ship-and-create-the-successor in one change (cheap, documentation plus possibly a release verb, but it leaves the trap for anyone who forgets), or (b) change how 'next' resolves so a tree with zero planned records does not mass-dangle (touches every Blocks-Release reader and risks weakening a real check). Plan 3cs7qg names this item in the CI step comment so a future reader meets the caveat where the gate lives.
