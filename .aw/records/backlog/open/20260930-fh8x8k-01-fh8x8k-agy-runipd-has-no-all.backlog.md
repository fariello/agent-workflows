- Id: fh8x8k
- Status: open
- Set: fh8x8k
- Priority: low
- Work-Kind: chore
- Summary: agy_runipd has no __all__, so its deliberate re-exports can only be justified by noqa comments

## Workflow history
- 2026-09-30 created (aw backlog): agy_runipd has no __all__, so its deliberate re-exports can only be justified by noqa comments

Found while authoring plan h0zk2g (backlog s4jctz), measured at HEAD 27a80985.

WHAT IS ASYMMETRIC. `agent_workflows/oc_runipd.py` declares an `__all__` (22 entries, five of them underscore-prefixed: `_ANSI_CODES`, `_ANSI_RESET`, `_ANSI_STRIP_RE`, `_one_line`, `_strip_ansi`). `agent_workflows/agy_runipd.py` declares NONE (`hasattr(agy_runipd, '__all__')` is False).

WHY IT MATTERS. A module with an `__all__` can justify a deliberate re-export MECHANICALLY: listing the name makes ruff treat it as an intentional export, and `F401` goes quiet with no comment to rot. Measured both ways on ruff 0.16.3 and on the hook-pinned v0.4.4 (`.pre-commit-config.yaml`): adding `"_read_id"` to `oc_runipd.__all__` and deleting its `# noqa: F401` gives `All checks passed!` on both, with the default suite at `3387 passed, 2 skipped`. `agy_runipd` has no such route, so its re-exports must rely on a `# noqa` plus prose. That prose is exactly what decayed to produce backlog s4jctz: a suppression justified by `tests/test_runner_refork_guard.py`, deleted in 19313eed. Plan h0zk2g leaves `agy_runipd` on a re-justified `# noqa` for this reason, and records the residual asymmetry as its OQ-02.

WHY THIS IS NOT SIMPLY 'ADD AN __all__'. Introducing a module-wide export list to a 4172-line runner changes what `from agy_runipd import *` yields and what other tooling treats as that module's public surface. It also invites the question of WHICH of its many names belong in it, which is a design call across the whole module rather than a lint fix. `runner_shared` likewise declares no `__all__`, so the convention is not uniform in this area and a decision here should say what the rule is.

NOTE a related shim asymmetry worth deciding at the same time: `tools/ipdrunner/runagy.py` re-exports by looping `for _k, _v in vars(agy_runipd).items()` (capturing PRIVATE names), while `tools/ipdrunner/runipd.py` assigns five names explicitly. That divergence is why `agy_runipd._read_id` has a live consumer and `oc_runipd._read_id` has none.

FILED chore AND low: nothing is broken and no behavior differs; this is a consistency and maintainability question about how deliberate re-exports are justified.
