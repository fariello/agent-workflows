- Id: jb0sc1
- Status: open
- Set: livecorpusguard
- Priority: low
- Work-Kind: chore
- Summary: Six live-corpus tests carry no livecorpus marker, so a third party's artifact can still red a lane's suite

## Workflow history
- 2026-09-20 created (aw backlog): Carried forward from plan h3bjue E-04: the livecorpus marker added in 7b9f3ae2 supplies the discriminator a class-wide guard previously lacked; six unmarked live-corpus call sites measured 2026-09-20.

CARRIED FORWARD from plan `h3bjue` (`gatepin` Order 01) E-04, which repaired ONE instance of this
class and was scoped to RECORD a decision about the class rather than build a guard. That plan's
finding is that a guard is now TRACTABLE where it previously was not, and this item is the capture.

THE CLASS, stated as the symptom. A test that asserts a property over the LIVE `.aw/records/` tree
can be turned red by any agent authoring a normal artifact. Because a runner lane merges its work
only when the full suite passes, one such red blocks integration for EVERY concurrent lane, including
lanes whose work is unrelated and correct. Measured 2026-09-19: three `reaskscore` plans wrote
"clearing ... its `no-go`", `newest_verdict` matched the token inside that clearing clause, and run
`run-20260919T194413Z-2056285` spent 2h 10m and $55.02 integrating NOTHING, with three lanes
preserved unmerged and eight items cascaded to `dependency-blocked`.

FOUR KNOWN INSTANCES, three of them now addressed:
  1. `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`.
     Asserted that NO pending plan carries a negative verdict, which is FALSE BY CONSTRUCTION
     whenever the gate works, since a legitimately REJECTed plan awaiting replan is a correct
     occupant of `pending/`. REPLACED by plan `h3bjue` with a named-id6 test plus a falsifiable
     whole-corpus property.
  2. `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`.
     Asserted `{"kgpptv": "reviewed"}` against the live corpus and was red for days. DELIBERATELY
     rewritten to `test_runprofile_is_not_refused_for_unauthored_rows` in commit `31169afd`, whose
     docstring reasons that the old form "pinned a transient repository state rather than the
     behavior this test is named for".
  3. `tests/test_run_viewer.py`'s dependence on the GITIGNORED `.aw/records/runs/` tree. Fixed by
     plan `xbwq8n`; its missing regression guard is tracked separately as `rcmbnb`.
  4. STILL LIVE AND UNMARKED, measured 2026-09-20 by sweeping every `tests/test_*.py` for a
     `glob`/`rglob`/`iterdir` over the live records tree. Six call sites in four modules read the
     live plan corpus and carry NO `livecorpus` marker:
       - `tests/test_plan_readiness.py:350` `test_every_pending_plan_yields_a_real_history_record`
       - `tests/test_ipd_lint.py:730` `test_every_readiness_carrying_plan_in_the_tree_is_attested`
       - `tests/test_ipd_lint.py:1084` `test_real_executed_plan_at_post_transition`
       - `tests/test_ipd_schema.py:2978` `test_executed_conforming_corpus_low_overfire_rate`
       - `tests/test_cli_find.py:447` `test_a_setid_query_excludes_prefix_sharing_foreign_sets`
       - `tests/test_cli_find.py:474` `test_an_id6_query_returns_the_declaring_artifact_not_its_citers`
     Each is a legitimate, valuable check. The concern is not that they read the corpus; it is that
     nothing records that they CAN be reddened by a third party's artifact, so the next lane to meet
     one spends review prose re-establishing that the red is nobody's fault. That cost is documented
     repeatedly in the review tree (for example `29wvmj:142` calls the pattern a "CORPUS TRAP").

WHY A GUARD IS NOW TRACTABLE WHERE IT WAS NOT. Plan `h3bjue` was authored before the `livecorpus`
marker existed and concluded (its OQ-02) that a blunt "test reads live repo state" detector would
forbid the DELIBERATE and valuable cases along with the bad, since this very coupling is the stated
reason its class exists ("a fixture-only suite can pass while the gate misjudges reality"). Commit
`7b9f3ae2` then added the `livecorpus` marker and `pyproject.toml` deselects it by default. That
supplies the discriminator the earlier analysis lacked: the guard no longer has to judge whether a
live-corpus read is GOOD, only whether it is DECLARED. Suggested shape, offered as an option and not
a decision: assert that every test function containing a `glob`/`rglob`/`iterdir` over
`.aw/records/` is either marked `livecorpus` or listed in an explicit, justified allowlist.

THE HONEST LIMITATION TO WEIGH FIRST, because it is why this is filed rather than built. `utwr6y`
E-03 established that the obvious implementation, a grep over test source, is unsound for its own
case because "it would pass while an implicit `dir='.'` still reached the live tree". The same
objection applies in weaker form here: a source-level check catches the syntactic shape and misses a
read reached through a helper. An AST-level or import-time check is stronger. Whoever picks this up
should decide that first, since a guard that is easy to evade will be trusted further than it holds.

WHY LOW PRIORITY: nothing is broken today. The measured suite is green and the two most expensive
instances are repaired. This is prevention against a recurrence whose cost is well documented but
whose trigger is another party's ordinary work.
