- Id: yzwfql
- Status: open
- Set: yzwfql
- Priority: low
- Work-Kind: chore
- Summary: Two brittle tests snapshot whole allowlists instead of asserting their claim, so any new config key or term palette fails unrelated tests

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing plan pow5sj (spec uonrjg R9.3a.4). Adding the legitimate color_depth config key and the spec-mandated STAGE_COLOR_16 palette each failed a test in an unrelated module, because both tests pinned an entire set rather than the property they exist to demonstrate. (1) tests/test_run_analytics_wizard.py::test_the_xdg_user_config_would_have_dropped_the_setting asserted config._ALLOWED_TOP_KEYS == {aw_home, config_version, defaults, repos}; its actual claim is that an UNREGISTERED key is silently dropped by normalize(), which needs no snapshot of the allowlist. (2) tests/test_term_components.py::PaletteSingleSourceTests::test_no_parallel_palette_defined asserted the list of term dicts matching COLOR equals exactly [STATUS_COLOR_256]; its actual claim is that no RIVAL table answers the same question, and a second RUNG of the documented 256/16/none ladder is not a rival. Both were narrowed in place to assert the claim (pow5sj D-02, D-03), so nothing is outstanding for this instance. Filed because the PATTERN is the defect and likely recurs: a test that snapshots a whole allowlist converts every legitimate extension into a failure in a module that has no stake in it, which costs a later executor a diagnosis and tempts an unjustified assertion edit. Worth a sweep for other whole-set snapshots (grep for assertEqual on sorted()/set() of a module-level allowlist) and, if the pattern is common, a short convention note.
