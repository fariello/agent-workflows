- Id: un6ppd
- Status: open
- Set: un6ppd
- Priority: medium
- Work-Kind: chore
- Summary: assert_valid_agent_record raises unguarded from the machine renderer, so any out-of-range exit crashes the CLI with a traceback

## Workflow history
- 2026-09-20 created (aw backlog): assert_valid_agent_record raises unguarded from the machine renderer, so any out-of-range exit crashes the CLI with a traceback

FOUND while executing IPD quqyc4 (its finding F-9); quqyc4 fixed the one VALUE it knew about and deliberately left the CLASS, which this item carries.

THE CLASS: `result_types.CommandResult.to_agent_record` calls `agent_schema.assert_valid_agent_record`, which RAISES `ValueError`, and `renderers.AgentRenderer.render` does not catch it. So any verb that returns a `CommandResult` whose `exit_code` (or any other field) is outside the validator's permitted set does not degrade to a diagnostic: it crashes the CLI with a Python traceback and exit 1, i.e. with a code that MEANS 'domain findings'. That was measured on `aw attention --agent` and `aw ipd board --agent` outside a project before quqyc4.

WHAT quqyc4 DID AND DID NOT DO: it widened the permitted `exit` set to admit 3 for cannot-run, which removes the only known trigger, and it added a validator/documentation agreement test. It did NOT guard the raise. So the next verb to invent an exit value, or to construct a record that trips any other validator rule in production, reproduces the same traceback.

THE TENSION TO RESOLVE, which is why this is a decision and not just a try/except: the raise is deliberately strict because the validator is the anti-greenwashing gate, and silently downgrading an invalid record would let a nonconforming record ship. A reasonable shape is to catch in the renderer and emit a CONFORMING `kind: error`/`outcome: cannot-run`/`exit: 2` record that reports the validation failure itself, so the failure is machine-visible instead of a traceback, and to keep raising under a test/strict mode so the suite still fails loudly. That needs a maintainer's view on which surface must stay fail-loud.
