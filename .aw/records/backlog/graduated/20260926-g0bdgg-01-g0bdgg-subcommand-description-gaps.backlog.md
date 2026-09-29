- Id: g0bdgg
- Status: graduated
- Graduated-To: g0bdgg
- Blocks-Release: next
- Set: g0bdgg
- Priority: medium
- Work-Kind: bug
- Summary: SubcommandDescriptionTests fails on eight subparser description gaps

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: ypnk56
- 2026-09-26 note (aw backlog): CI step 'Run slow-marked tests' (tests.yml, plan 4petcj) is advisory because of this item's slow-test failure; when the last of the owning items (57dwkc, 3ypquf, 4vfkl1, g0bdgg) closes, remove its continue-on-error so the slow set fails closed.
- 2026-09-26 created (aw backlog): SubcommandDescriptionTests fails on eight subparser description gaps

MEASURED 2026-09-26 while executing plan 4petcj.

WHAT IS WRONG: `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description` fails on eight subparser description gaps:
- config unset: description not longer than help (71 <= 88)
- conf unset: description not longer than help (71 <= 88)
- upgrade-test list: empty description
- upgrade-test new: empty description
- upgrade-test sandboxes: empty description
- upgrade-test probe: empty description
- upgrade-test env: empty description
- upgrade-test clean: empty description

EVIDENCE:
`python3 -m pytest tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description -o addopts=""`
AssertionError: Lists differ: ['config unset: description not longer than help (71 <= 88)', 'conf unset: description not longer than help (71 <= 88)', 'upgrade-test list: empty description', 'upgrade-test new: empty description', 'upgrade-test sandboxes: empty description', 'upgrade-test probe: empty description', 'upgrade-test env: empty description', 'upgrade-test clean: empty description'] != []
