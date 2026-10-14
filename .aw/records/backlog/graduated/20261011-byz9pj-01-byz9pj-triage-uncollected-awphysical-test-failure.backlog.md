- Id: byz9pj
- Status: graduated
- Graduated-To: byz9pj
- Set: byz9pj
- Priority: medium
- Work-Kind: followup
- Summary: Triage the failing ScenarioBindingTests case in uncollected tools/awphysical/test_awphysical_tools.py and bring it under a gate

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: 719lyq
- 2026-10-12 created (aw backlog): Triage the failing ScenarioBindingTests case in uncollected tools/awphysical/test_awphysical_tools.py and bring it under a gate

Found while graduating n8adhb (plan 5s31xp). tools/awphysical/test_awphysical_tools.py is outside testpaths=["tests"], so no gate runs it. At HEAD 8538be828, `python3 -m pytest tools/awphysical/test_awphysical_tools.py -o addopts="" -q -p no:randomly` reports `1 failed, 30 passed`: ScenarioBindingTests.test_every_binding_loads_a_real_test_method_and_names_an_assertion fails because tools/awphysical/scenario-token-bindings.json binds scenario acknowledged-remote to tests.test_acceptance_matrix.TestAcceptanceMatrixScenarios.test_19_4_companion_confirmed_private_remote, which no longer loads (likely removed by a suite trim). Note scenario-token-bindings.json addresses this module by dotted name tools.awphysical.test_awphysical_tools, so relocating it must rewrite those bindings. Fix the binding, then relocate the module into tests/ and remove its exemption from the uncollected-test-module guard that 5s31xp adds.
