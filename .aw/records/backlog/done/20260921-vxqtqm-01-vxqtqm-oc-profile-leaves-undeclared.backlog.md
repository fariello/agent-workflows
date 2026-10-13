- Id: vxqtqm
- Status: done
- Graduated-To: vxqtqm
- Set: vxqtqm
- Priority: low
- Work-Kind: chore
- Summary: Five oc profile parser leaves are undeclared in the command inventory

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD 4mv9ul executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261011-vxqtqm-01-4mv9ul-verify-the-five-aw-oc-profile-leaves-stay-declared-and-the-w.ipd.md); evidence .aw/records/plans/executed/20261011-vxqtqm-01-4mv9ul-verify-the-five-aw-oc-profile-leaves-stay-declared-and-the-w.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005641Z-2321995: 4mv9ul
- 2026-09-21 created (aw backlog): Found while executing plan qhy3i3 (rdyrecheck-01), which had to add a declaration for its own new verb. tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves requires ZERO undeclared leaves across _build_parser(), and fails at HEAD 5421fc10 with: 'AssertionError: 5 != 0 : Found undeclared parser leaves: {oc profile show, oc profile list, oc profile default, oc profile remove, oc profile add}'. Note the BARE suite passes, so this is only visible when the module is run alone, which means the conformance guarantee the test exists to provide is not actually being enforced in the default run. Each leaf needs its own command_class / human_recipe / mutation_gate / exit_contract judgement, so this was deliberately left out of qhy3i3's scope (recorded as its decision D4) rather than swept in.
