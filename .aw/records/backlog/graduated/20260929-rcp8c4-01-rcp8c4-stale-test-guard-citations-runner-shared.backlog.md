- Id: rcp8c4
- Status: graduated
- Graduated-To: rcp8c4
- Set: rcp8c4
- Priority: low
- Work-Kind: chore
- Summary: runner_shared.py cites the deleted tests/test_run_flag_surface.py as its guard in seven comments

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053053Z-3200037: 8wpjeq
- 2026-09-29 created (aw backlog): runner_shared.py cites the deleted tests/test_run_flag_surface.py as its guard in seven comments

Seven comments in `agent_workflows/runner_shared.py` name `tests/test_run_flag_surface.py` as the mechanism that guards spec `25kzda` 2.1's flag surface, and that file does not exist. Measured at HEAD `09f68a5b`: `:117` ("What replaces the fingerprint as its guard is tests/test_run_flag_surface.py"), `:1079`, `:14374` ("because tests/test_run_flag_surface.py reads the spec FILE in BOTH directions and a row here that 2.1 does not declare fails the suite"), `:14574`, `:14595`, `:14620`, and `:27858`. `ls tests/test_run_flag_surface.py` fails and `git log --diff-filter=D` attributes the deletion to `19313eed` ("trim test suite from 9,136 to under 2,000 tests"). The spec's own 2026-09-21 history note at `:1618` repeats the same claim.

WHY THIS MATTERS AND WHY IT IS NOT A BUG. No computed behavior is wrong and no operator sees any of it. The cost is paid by an EDITOR: each comment tells whoever is about to add a run policy flag that a bidirectional spec-versus-table test will catch a mismatch, so a real divergence between `RUN_POLICY_FLAGS` and the spec's grammar stanza now ships silently while the code claims otherwise. That is a false guard claim, which is worse than no claim, but it fails the repository's perceptibility test: no user waits on a wrong answer, so `chore` and no release gate.

THE FIX IS ALREADY DECIDED BY A MAINTAINER RULING ON THE SIBLING ITEM, so this is a text correction and NOT an open design question. Item `pn7rw3` (the same defect class in `tests/test_runner_shared.py`, filed 2026-09-28) carries the ruling verbatim in its own history: "Code-pinning guards (refork tables/module ownership pins) were deleted in the suite trim and will not be restored. Stale comments should simply remove references to them without seeking to restore code pins." So DO NOT restore `tests/test_run_flag_surface.py` or author a replacement bidirectional test. CORRECT the seven comments to stop naming a guard that does not exist, and state plainly that the bidirectional spec-versus-table check was removed by `19313eed` and was not replaced, so the next author adding a run policy flag knows the spec stanza and `RUN_POLICY_FLAGS` are kept in step BY HAND.

ONE CAVEAT THE RULING DOES NOT COVER, and it is why this is not purely mechanical. The deleted `test_run_flag_surface.py` was not only a code pin: per the comments it read the SPEC FILE and compared it against `RUN_POLICY_FLAGS` in both directions, which is an artifact-consistency test of exactly the shape `AGENTS.md` P16 permits (compare the surviving `test_spec_25kzda_contains_no_follow_generated_token`, which reads the same spec). The ruling's subject was code-pinning guards, so whether a spec-to-table consistency test may be reinstated is arguably outside it. Treat that as a question to ASK if a future author wants the guard back; it does not block correcting the comments, which is wrong today under either answer.

DO NOT EDIT the spec's `:1618` history note as part of this. That line is a dated `aw specs note` record of what was true on 2026-09-21, and rewriting a history record falsifies it. If the stale claim inside it needs flagging, append a new note rather than editing the old one.

SURFACED BY /plan-review of plan `cpi6p3` (finding PR-011 / plan finding F-15). That plan needed F-6, "the test that guarded 2.1's grammar stanza no longer exists", to justify editing the 2.1 bullet cheaply; re-verifying F-6 turned up the seven surviving comments that still assert the opposite. `cpi6p3` deliberately leaves them alone (they are stale-guard claims, not spec-section citations) and names this item as their carrier. Adjacent but distinct: `sbh1o1`/`mt54wr` covers spec quoted-string and line-anchor rot, `ajomj3`/`2wmwf7` covers dangling spec PATH citations. This is a dangling TEST path plus a false guarantee, so neither claims it.
