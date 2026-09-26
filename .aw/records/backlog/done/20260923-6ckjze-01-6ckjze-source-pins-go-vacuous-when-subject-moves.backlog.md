- Id: 6ckjze
- Status: done
- Set: 6ckjze
- Priority: medium
- Work-Kind: chore
- Summary: a source-reading guard whose subject moves into runner_shared can go VACUOUS rather than red, and only two of the nine guards this lift touched said so out loud

## Workflow history
- 2026-09-26 done (aw set): Retired NOT-DOING (maintainer ruling 2026-09-26, graduation of batch incl. xelvyi): no tests that pin source text or code structure. 6ckjze proposed ADDING found-it anchors to source-reading guards; the ruling instead deletes source-reading tests (keeping behavioral tests only where behavior matters), which xelvyi's plan carries, so this item's premise no longer applies.
- 2026-09-23 created (aw backlog): Observed across hostdedup Order 02 (nmlx47) E-03/E-04/E-05/E-06, which re-based nine guard files. Filed as a concern about the guard-writing convention, not about any one file.

OBSERVED 2026-09-23 while unifying twelve runner symbols, which moved the SUBJECT of nine existing source-reading guards.

THE FAILURE MODE. A guard of the shape `assertIn(\"select.select\", source_of(host_body))` or `assertIn(\"suite_check\", <ast of each driver>)` answers a question about WHERE code is, not about what it does. When the code legitimately MOVES to `runner_shared`, such a guard has three possible fates, and only one is safe:

  * RED, naming the move. Fine: the executor re-bases it.
  * VACUOUS-AND-GREEN. The scan finds nothing and the assertion is trivially satisfied, so a real property silently stops being checked. This is the dangerous one.
  * VACUOUS-AND-RED-ON-PURPOSE, because the guard explicitly asserts it found something.

MEASURED THIS PASS: two guards took the third path and said so in their failure message.
`tests/test_run_flag_surface.py`'s `full_auto` fallback walk ends with 'if reads == 0: ... so this guard is VACUOUS on this host', and `tests/test_suite_adjudication.py` asserted `self.assertTrue(calls, ...must build the runner)`. BOTH went red for the right reason and told the executor exactly what had happened. That is the convention worth generalizing.

OTHERS WERE CAUGHT ONLY BECAUSE A SECOND, STRONGER ASSERTION EXISTED. `tests/test_resumedupe.py`'s prompt-content pin read `module_source(OC)` and would have found its symbols absent; it failed on `StopIteration` from a `next(...)` rather than on a stated property, which is a fine accident but not a designed one. `tests/test_lane_allocation_idempotent.py`'s bounded-wait pin failed on a substring that had moved.

THE CONCERN, stated as the rule it implies: ANY guard that reads source to prove a property should assert that it FOUND the thing it is reading about, in the same test, with a message naming the vacuous case. Without that, a lift can quietly disarm it.

THE WORK. Two parts, and the first is cheap. (1) Survey the source-reading guards over `oc_runipd`/`agy_runipd`/`runner_shared` for ones with no found-something assertion, and add one each; the population is finite and the pattern is mechanical. (2) Decide whether this belongs in the repository's test-writing conventions as a stated rule, since the same trap applies to any future extraction, not only to the runner pair. Related and already recorded: several of these files carry their own 'REPLACES A SOURCE-TEXT PIN' notes explaining why a behavioral assertion beat a textual one, so the preference for driven tests is established; what is missing is the fallback rule for the cases where a source read is genuinely the only option.
