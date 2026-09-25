- Id: ykfgpd
- Status: graduated
- Graduated-To: smallfix
- Set: recunify
- Priority: low
- Work-Kind: followup
- Summary: Collapse discover_plans' now-vestigial parse_plan_file injection, since one shared parser makes the seam pointless

## Workflow history
- 2026-09-25 graduated (aw set): graduated into smallfix (plan 0i4fkt); verified live at 8e74dcac
- 2026-09-17 created (aw backlog): Found while executing rununify 06 (sy7uwh). discover_plans still takes parse_plan_file as a keyword-only injected dependency, and each host keeps a one-line wrapper that binds it. The ORIGINAL reason for that injection was that the two hosts built DIFFERENT PlanRecord types, so a shared discover_plans could not construct one type without handing the other host a shape its code never expects. sy7uwh unified both the record and the parser, so both wrappers now inject the SAME object and the parameter carries no information. It was deliberately NOT removed there: the signature is fingerprint-pinned in tests/fixtures/runner_shared_premove_fingerprints.json, enumerated in tests/test_runner_shared.py::INJECTED, and covered by the maintainer's wrapper ruling whose whole point is to leave call sites untouched, so collapsing it means updating that fixture and the INJECTED table and belongs in its own plan rather than as a side effect. Concrete work: drop the parameter, delete both wrappers, move discover_plans from INJECTED into the clean-fingerprint set (which changes the pinned clean-move count of 23), and add it to tests/test_runner_refork_guard.py's REFORK_TABLE, which currently excludes it as a wrapped symbol.
