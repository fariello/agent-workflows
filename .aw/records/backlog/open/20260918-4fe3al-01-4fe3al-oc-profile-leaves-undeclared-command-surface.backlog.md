- Id: 4fe3al
- Status: open
- Blocks-Release: next
- Set: 4fe3al
- Priority: medium
- Work-Kind: bug
- Summary: the five 'aw oc profile *' parser leaves are undeclared in command_surface, failing test_zero_undeclared_parser_leaves outside the default -m 'not slow' subset

## Workflow history
- 2026-09-18 created (aw backlog): the five 'aw oc profile *' parser leaves are undeclared in command_surface, failing test_zero_undeclared_parser_leaves outside the default -m 'not slow' subset

Found while executing plan `di08i9` (Set `nobugship`). That plan's scope check told the executor to
settle whether `agent_workflows/command_surface.py` needed touching, so this test was run
deliberately; the failure is PRE-EXISTING and unrelated to that plan, which changed no parser flag.

MEASURED, at HEAD `af5fa26e`:

```text
$ python3 -m pytest tests/test_command_surface_declarations.py -o addopts="" -p no:randomly
FAILED tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
E  AssertionError: 5 != 0 : Found undeclared parser leaves:
   {'oc profile add', 'oc profile remove', 'oc profile default', 'oc profile show', 'oc profile list'}
======================== 1 failed, 13 passed in 20.77s =========================
```

NOT CAUSED BY THE PLAN UNDER EXECUTION, proven by stashing that plan's two source edits
(`agent_workflows/backlog.py`, `agent_workflows/status_set.py`) and re-running: the failure is
IDENTICAL (`1 failed, 13 passed`), so it reproduces on unmodified HEAD.

WHY IT WAS NOT ALREADY CAUGHT, which is the more interesting half: the whole file carries
`pytestmark = pytest.mark.slow`, and `pyproject.toml` `addopts` supplies `-m "not slow"`, so a BARE
`python3 -m pytest` (the run the contributor rules mandate, and which passed `8096 passed` for that
plan) never executes it. The conformance harness that is supposed to guarantee "0 undeclared leaves
across `_build_parser()`" is therefore red in a lane nobody routinely runs.

WHY `bug` RATHER THAN `chore`: a failing conformance test is a broken contract, not untidiness, and
the declaration it guards is what the agent-surface machinery reads. The five leaves being
undeclared means `aw oc profile *` has no declared command class, output recipe, or exit contract, so
its agent-mode behavior is unspecified by the surface that is meant to specify every leaf.

SUGGESTED FIX. Add the five `oc profile` leaves to `CommandDeclaration`s in
`agent_workflows/command_surface.py` (mirroring a neighbouring `oc` family entry for
`command_class`/`human_recipe`/`agent_record_kind`/`mutation_gate`/`exit_contract`), then re-run the
file. Worth also asking whether this harness belongs in the `slow` bucket at all, given that its whole
value is catching a drift that a bare run cannot see.
