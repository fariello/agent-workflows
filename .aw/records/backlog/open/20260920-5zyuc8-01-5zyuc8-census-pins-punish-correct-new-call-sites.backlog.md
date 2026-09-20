- Id: 5zyuc8
- Status: open
- Set: 5zyuc8
- Priority: medium
- Work-Kind: chore
- Summary: Five pinned tests assert launcher/closure CENSUS counts, so adding a correctly-wired call site reads as a regression

## Workflow history
- 2026-09-20 created (aw backlog): Found while wiring the standalone audit verb (plan mp289j).

OBSERVED 2026-09-20. Adding ONE correctly-wired caller of `oc_runipd.run_opencode` (the standalone audit verb, which passes `use_verifier_launch=True` and names its telemetry phase, i.e. does everything the guards ask for) turned NINE tests red across five files. None had found a defect; each had pinned a COUNT as a proxy for an invariant:

- `tests/test_oc_runipd.py::VerifierTurnArgvRoutingTests::test_one_argv_builder_serves_both_call_sites` - wanted ONE BUILDER, asserted TWO CALLERS.
- `tests/test_oc_runipd.py::OcTelemetryWiringTests` and `tests/test_runner_telemetry_integration.py::HostWiringTests` - wanted EVERY LAUNCH INSTRUMENTED AND ITS PHASE STATED, asserted exactly two callers and exactly one phase declaration.
- `tests/test_defect_report.py::HostResumeSpellingTests::test_neither_host_gained_a_third_launcher_call_site` - its own docstring gives the reason as "a third could inherit the wrong profile", and then rejects a third caller that explicitly declares its profile.
- `tests/test_rununify_main.py::TheClosureClassification` (five tests) - `main`'s closure size, the double-defined count, and agy's closure size, all as literals, including one in a METHOD NAME (`test_the_closure_is_still_28_names`) which had already gone stale once.

ALL NINE WERE RESTATED AS INVARIANTS in plan `mp289j` rather than merely re-numbered: one builder (definition count) instead of one caller count; exactly one call site may take the default execute phase and every other must declare validate; exactly one call site may omit the launch-role keyword; and the closure counts now read from the single table that documents them. The tables that genuinely ARE censuses (the flag partition, the subparser set) were updated with the measurement and the reason, which is what they ask for.

THE GENERAL DEFECT, and why this is worth a carrier rather than just a commit: a count-shaped pin is a tax on correct changes and a false signal about incorrect ones. It fires on a well-wired addition (nine times here) and it does NOT fire on the actual hazard, since a badly-wired third caller and a well-wired one produce the same number. The repository has already recorded this shape twice in prose: `cli.py`'s `aw runs` help text says its exception count "KEEPS GOING STALE, WHICH IS WHY THE NAMES LEAD", and AGENTS.md records a fraction that "rotted three times" before being restated as a property.

SUGGESTED WORK: sweep the suite for count-shaped assertions over CODE STRUCTURE (callers, symbol occurrences, closure sizes) and restate each as the invariant it stands for, keeping literal counts only where the number is itself the contract (an operator-visible flag surface, a declared subparser set). A lint or a review checklist item would stop new ones being written.

EVIDENCE: the nine failures and their rewrites are in plan `mp289j`'s diff; each rewritten test carries a comment naming the invariant it now asserts and why the count was a proxy.
