- Id: xw4rb7
- Status: open
- Blocks-Release: next
- Set: bporphan
- Priority: medium
- Work-Kind: bug
- Summary: _add_output_mode_flags is owned by no pending rununify plan after child 03's re-scope dropped group H

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): _add_output_mode_flags is owned by no pending rununify plan after child 03's re-scope dropped group H

Measured at 4a1bb873 by plan s16omw (rununify Order 10, E-01/E-04).

WHAT IS WRONG. `_add_output_mode_flags` is defined in BOTH runners (agent_workflows/oc_runipd.py:9128, agent_workflows/agy_runipd.py:5532) and is one of only two still-double-defined names in `build_parser`'s closure. No pending plan owns lifting it:

* child 04 (`tx6q0h`) lifts `_detect_driver_command` and EXPLICITLY assigns `_add_output_mode_flags` to child 03;
* child 03 (`i3d6ml`) was re-scoped at its 2026-09-16 review from 48 symbols to 9 (groups A and B), and group H, which holds `_add_output_mode_flags`, was dropped.

So the Set's 100%-de-duplication objective currently has a hole exactly one symbol wide, and it is a symbol that registers three operator-visible option strings (`--quiet`, `--raw`, `-v`/`--verbose`) on two subparsers per host.

WHY IT IS NOT MERELY A MOVE. The two bodies genuinely DIFFER (asserted by tests/test_rununify_build_parser.py::test_the_two_output_mode_helper_bodies_genuinely_differ), so a lift needs a body decision. It also carries a deliberate asymmetry: `verbosity_default` is 0 on `start` and None on `resume`, so an omitted `-v` on resume does not reset a frozen tier.

WHAT ALREADY EXISTS TO HELP. The asymmetry is now characterized behaviorally on BOTH hosts by tests/test_rununify_build_parser_characterization.py::test_resume_leaves_verbosity_absent_so_a_frozen_tier_survives_on_both_hosts, and the fork is pinned STILL-forked in tests/test_rununify_build_parser.py::TheTwoRemainingForksAreStillForked, which will fail deliberately when the lift lands.

RECOMMENDED OWNER: child 03 (`i3d6ml`), by re-adding group H, since it already owns the lift mechanism and the named-table test pattern. Failing that, a new precursor child.
