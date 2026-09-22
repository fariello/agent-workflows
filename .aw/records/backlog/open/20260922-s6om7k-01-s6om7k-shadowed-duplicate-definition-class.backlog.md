- Id: s6om7k
- Status: open
- Set: s6om7k
- Priority: low
- Work-Kind: chore
- Summary: oc_runipd carried a duplicate locked_run definition that shadowed its own wrapper

## Workflow history
- 2026-09-22 created (aw backlog): oc_runipd carried a duplicate locked_run definition that shadowed its own wrapper

Found and FIXED while executing plan li44r9 (hostdedup Order 01). Filed for the CLASS, since the
instance is closed.

WHAT HAPPENED. While lifting `locked_run`, the wrapper was written near the original `run_lock` block
and a SECOND `locked_run` definition was left further down the same module. Python's last-definition-wins
meant the wrapper was UNREACHABLE: the module exported the stale private copy, so the symbol read as
lifted in a diff and behaved as forked at runtime. Every structural assertion that merely checks 'a
wrapper exists' would have passed.

WHAT CAUGHT IT: the new guard `tests/test_hostdedup_identical_lift.py` asserts ONE definition per host
per lifted symbol, not merely that a wrapper exists. That assertion (`test_no_host_defines_a_lifted_symbol_twice`)
was written for exactly this hazard and found it on its first run.

THE CLASS, which is why this is filed rather than just fixed. `oc_runipd.py` and `agy_runipd.py` are
8000+ and 4000+ lines and are edited by many concurrent plans, so a duplicate top-level definition is
easy to introduce and invisible to review: a diff shows an added wrapper and nothing shows the stale
twin. Nothing in the suite checks the GENERAL property for either runner; the new guard checks it only
for the sixteen symbols li44r9 lifted.

SUGGESTED FIX: a cheap repo-wide assertion that no module in `agent_workflows/` defines the same
top-level symbol twice. That is a few lines of AST over `ast.Module.body`, catches this class
everywhere rather than per tranche, and would have caught this instance without the tranche-specific
guard existing.
