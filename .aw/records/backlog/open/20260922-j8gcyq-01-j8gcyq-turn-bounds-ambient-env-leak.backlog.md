- Id: j8gcyq
- Status: open
- Blocks-Release: next
- Set: j8gcyq
- Priority: medium
- Work-Kind: bug
- Summary: tests/test_turn_bounds.py isolation-scope test reads the ambient environment and fails inside an agent lane turn

## Workflow history
- 2026-09-22 created (aw backlog): Filed from IPD vdabn5 execution. Reproduced at HEAD 49848926: the node fails in a lane worktree solely because the executing agent's own turn exports OPENCODE_CONFIG_CONTENT.

MEASURED AT HEAD `49848926` in an isolated lane worktree (`aw/lane/vdabn5`), while executing IPD `vdabn5`, which touches neither this test nor anything it covers.

`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` FAILS on a bare `python3 -m pytest`:

```text
>       assert policy_key not in main_env, (
            "a non-isolated turn must get NO denial policy; it works in the main checkout "
            "where external-directory denial would refuse its ordinary work (R4.1)"
        )
E       AssertionError: a non-isolated turn must get NO denial policy; ...
E       assert 'OPENCODE_CONFIG_CONTENT' not in {'AGENT': '1', 'AW_PIN_KEEP_ROOT': ..., 'CLAUDE_CODE_SSE_PORT': '12820', ...}
tests/test_turn_bounds.py:310: AssertionError
```

THE CAUSE IS AMBIENT-ENVIRONMENT COUPLING, not a defect in the behavior under test. The assertion checks that a NON-isolated turn's computed environment carries no `OPENCODE_CONFIG_CONTENT` denial policy. The environment it inspects inherits from the process running pytest. An OpenCode agent turn EXPORTS `OPENCODE_CONFIG_CONTENT`, so whenever the suite is run BY an agent (which is how every lane executes), the variable is already present and the assertion fails regardless of the code's correctness.

PROOF IT IS THE AMBIENT VARIABLE AND NOTHING ELSE:

```text
$ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest \
    tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
1 passed in 4.69s
```

WHY THIS IS FILED AS `bug` AND GATES THE RELEASE. It is user-perceptible in the way that matters most for this toolkit: every agent-run suite in a lane reports `1 failed`, so the contract's own instruction to compare failing NODE IDS against a baseline is degraded, and each executing agent must independently re-derive that this failure is environmental and not its own. That cost was paid twice in this run alone (once at baseline, once post-fix). It also risks the WORSE outcome the contract warns about: an agent 'reconciling' a mismatch it does not understand by modifying state it does not own.

SUGGESTED FIX (not implemented here; out of `vdabn5`'s scope): make the test hermetic rather than ambient. Build the non-isolated environment from an explicit base mapping, or `monkeypatch.delenv('OPENCODE_CONFIG_CONTENT', raising=False)` before computing it, so the assertion tests what the code PUTS IN the environment rather than what the developer's or agent's shell happened to export. The isolated half of the same test is already unambiguous because it asserts presence.
