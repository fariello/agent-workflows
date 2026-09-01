- Id: mzy2so
- Status: open
- Blocks-Release: next
- Set: l2depgate
- Priority: high
- Work-Kind: bug
- Summary: make test-all fails a level-2 wind-down test: an item with an UNMET dependency is started during a level-2 stop, blocking zpbx7o's whole-Set verification

## Workflow history
- 2026-09-01 created (aw backlog): Found performing zpbx7o's whole-Set verification (checklist item 3), whose V-01 requires pasted make test-all output. Pre-existing (reproduced at 5e5da9a0, before this session's commits) and invisible to a bare pytest because the test is slow-marked. Falsified the obvious 'stale legacy dependency field' explanation by rewriting the fixture to the canonical field: it still fails. Carries a next-place-to-look pointer at oc_runipd.py:5837 as a hypothesis, not a diagnosis.

`make test-all` fails `tests/test_runner_stop_levels12.py::Level2Tests::
test_level_2_leaves_another_sets_runnable_item_queued_when_this_set_is_blocked`. Found while performing
`zpbx7o`'s whole-Set verification (checklist item 3), whose V-01 REQUIRES pasted `make test-all` output
"since a bare `pytest -q` deselects the `slow` tests this Set depends on". The plan's own gate says a
failing criterion blocks the Set, so `zpbx7o` was left in `pending/` rather than finalized.

WHY THIS IS NOT VISIBLE IN NORMAL RUNS: the test is `slow`-marked, so the default
`addopts` (`-m 'not slow'`) deselects it. A bare `python3 -m pytest` reports `3996 passed` GREEN at the
same commit. Only `make test-all` (`-m ''`) surfaces it.

PRE-EXISTING, NOT A REGRESSION FROM THE 2026-09-01 SESSION. Verified in a throwaway clone at `5e5da9a0`
(before `cdef9c90`, `9c643cf8`, `b2b2bf6c`, `362b3dd1`, `18142312`, `739450ee`): the same test fails
there, among 20 failures at that commit vs 5 now. So it predates this session's work.

WHAT THE TEST ASSERTS. Queue: set `sca` = [`ca0001`, `ca0002`], set `scb` = [`cb0001`]. `ca0002` is
given an unmet dependency, then a level-2 (after-set) stop is requested after `ca0001`. Expectation:
only `ca0001` ran; `ca0002` and `cb0001` both stay `queued`; exit 0.

WHAT ACTUALLY HAPPENS. `run.ran()` contains `ca0002` as well, i.e. the item with the UNMET dependency
WAS STARTED during the level-2 wind-down. The reaped-state dump shows its plan file moved
(`D .aw/records/plans/pending/20260829-sca-02-ca0002-plan.ipd.md` plus an untracked
`.aw/records/plans/executed/`), which is a real execution, not a bookkeeping artifact. The level-2
machinery itself behaves correctly and says so: `stop requested: level 2 (after-set); boundary = next
set, finishing set sca` and `deliberate stop (level 2, after-set): 1 item(s) left queued, not started:
cb0001`. All four invariants pass (R1 children_reaped, R2 lock_released, R3 ledger_coherent, R4
tree_observed). So the defect is DEPENDENCY GATING DURING A WIND-DOWN, not the stop protocol.

A HYPOTHESIS I TESTED AND FALSIFIED, recorded so it is not retried. The test's own inline comment says
the driver reads a legacy `- Dependencies:`/`- Depends-on:` field via `oc_runipd._DEPS_RE`, "NOT the
plan-schema `- Item-Dependencies:` field". That comment is now WRONG: `8guhs0` (lanetruth-03)
deliberately DELETED `_DEPS_RE` (see the explicit note at `agent_workflows/oc_runipd.py:161-168`,
"there is deliberately NO dependency regex here"), making `- Item-Dependencies:` canonical. The test
still writes the legacy field, and it landed 26 seconds AFTER `8guhs0` (test `dc6b0a80` at
2026-08-30 03:32:59, `8guhs0` at 03:32:33), so "stale fixture" was a plausible read.
BUT: rewriting the fixture to use the canonical `- Item-Dependencies: executed:zzzz99` and re-running
STILL FAILS identically. So the fixture spelling is a genuine wart worth fixing, and it is NOT the
cause. The canonical path is otherwise well covered:
`tests/test_runner_item_dependencies.py` passes 55/55.

WHERE TO LOOK NEXT (not concluded). `oc_runipd.py:5837-5841`: when `wind_down is not None` the loop
records the deliberate stop and `break`s BEFORE the `for item in queued:` block at `:5842` that assigns
`status = "dependency-blocked"` and populates `unsatisfied_dependencies`. So during a wind-down the
dependency-blocked marking may be skipped, which would explain a blocked item being treated as
startable. That ordering is the first thing to test; it is a hypothesis, not a diagnosis.

FOUR OTHER `make test-all` FAILURES at the same commit, all also pre-existing at `5e5da9a0` and all
CLI-surface declaration checks rather than runner behavior, listed so nobody assumes they are related:
`test_command_surface_declarations.py::test_zero_undeclared_parser_leaves`,
`test_cli.py::test_every_subparser_has_fuller_description`,
`test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves`, and
`test_cli_conformance_matrix.py::test_every_declared_leaf_gets_a_full_scenario_row_set`. These four are
plausibly owned by the `awcmdsurf`/`0soncw` command-surface work; that attribution is unverified.

CONSEQUENCE FOR THE RELEASE: `zpbx7o` is a 2.0.0 release blocker and cannot honestly finalize while its
required `make test-all` evidence is red. Spec `c4gd2h` therefore also stays `implementing`.
