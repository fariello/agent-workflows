- Id: uhbi1o
- Status: done
- Set: uhbi1o
- Priority: medium
- Work-Kind: chore
- Summary: is_pure_delegation hard-codes runner_shared as the delegation target, so a sanctioned wrapper onto any other module is misread as a fork

## What is wrong

TWO SEPARATE GAPS IN THE SAME SEAM, both measured 2026-09-19 while executing plan `z8ddk0`, which
converted `runner_shared.should_color` into a sanctioned delegation onto `term`.

FIRST, the predicate is target-specific. `tests/test_rununify_run_queue.py:250` `is_pure_delegation`
ends with:

```python
return (
    isinstance(fn, ast.Attribute)
    and isinstance(fn.value, ast.Name)
    and fn.value.id == "runner_shared"
)
```

So it recognizes the sanctioned wrapper shape ONLY when the callee is `runner_shared.X`. A wrapper
delegating to any other owning module (`term`, `render_stream`, `run_selection_policy`) is reported
as NOT a delegation, i.e. as a re-fork, even though it holds no logic. Measured against the shipped
delegation `z8ddk0` introduced: `is_pure_delegation(node)` returned `False` for a body whose only
statement is `return term.should_color(stream)`. Plan `z8ddk0` E-07 could therefore not reuse the
predicate as its review intended and had to reimplement the notion locally, which is exactly the
"second notion of sanctioned delegation" the repo warns against.

SECOND, the shape it accepts is unreachable in `runner_shared` for a NEW dependency. A one-statement
`return term.should_color(stream)` requires `term` to be bound, and
`tests/test_orchestrator_probe_cache.py::TheRowWalkIsSharedWithTheRetirementGate::test_no_new_module_level_first_party_import_in_runner_shared`
REFUSES a module-level first-party import there (allowing only `render_stream` and
`runner_profiles`, because an import in that file changes the graph for both host drivers). The only
legal spelling is therefore a function-local import plus a return - TWO statements - which every
`len(body) != 1` delegation predicate rejects. So the two shipped guards, taken together, admit no
legal way to express a new sanctioned delegation in `runner_shared`.

## Evidence

```
$ python3 -c "... is_pure_delegation(should_color node) ..."
non-docstring statements: 1
unparsed: return _term.should_color(stream)
is_pure_delegation (runner_shared.X form): False
```

```
$ python3 -m pytest tests/test_orchestrator_probe_cache.py -k module_level_first_party -o addopts=""
AssertionError: Items in the first set but not the second:
'agent_workflows.term' : runner_shared gained a module-level first-party import: ['agent_workflows.term']
```

## Suggested fix

Widen `is_pure_delegation` to accept any module attribute as the callee (what makes a wrapper safe is
that it carries no logic, not which module it forwards to), and subtract a function-local `import`
from the statement count the same way a docstring is already subtracted. Then have `z8ddk0`'s locally
reimplemented predicate in `tests/test_term.py::OneOriginatingDefinitionTests._is_pure_delegation`
import the shared one instead, so there is one notion again. Keep the refusal narrow: only imports
and docstrings subtract, so a body with a conditional or an environment read is still a fork.

## Where

- `tests/test_rununify_run_queue.py:250` (`is_pure_delegation`), and the near-copies at
  `tests/test_rununify_execute_item.py:104` and `tests/test_rununify_initialize_run.py:337`
- `tests/test_orchestrator_probe_cache.py` (`test_no_new_module_level_first_party_import_in_runner_shared`)
- `tests/test_term.py::OneOriginatingDefinitionTests._is_pure_delegation` (the local reimplementation
  to retire once the shared predicate is widened)

## Provenance

Found while executing plan `z8ddk0`. Worked AROUND there rather than fixed: those test files are
outside that plan's declared `Scope-Paths` except the two it already owned, and re-baselining a
shipped anti-re-fork guard is precisely what that plan's scope fence forbids doing to make a test
green.

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: moot: is_pure_delegation removed with its test file in 19313eed
- 2026-09-19 created (aw backlog): is_pure_delegation hard-codes runner_shared as the delegation target, so a sanctioned wrapper onto any other module is misread as a fork
