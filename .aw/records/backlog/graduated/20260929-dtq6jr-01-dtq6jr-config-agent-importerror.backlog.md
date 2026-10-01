- Id: dtq6jr
- Status: graduated
- Graduated-To: dtq6jr
- Blocks-Release: next
- Set: dtq6jr
- Priority: high
- Work-Kind: bug
- Summary: every aw config verb except the exclude subgroup (seven of them) crashes with an unhandled ImportError when passed --agent, so the whole config family has no machine-readable surface

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053053Z-3200037: kfbom1
- 2026-09-29 note (author): corrected the count from five to SEVEN before first commit. The initial summary and body named five verbs, derived from the first batch driven; enumerating every `format_agent_json` import in `cli.py` by enclosing function and then driving each verb showed `config remove` and `config is` crash too, and that `_run_config_show` holds two such imports. Only `config exclude` is unaffected.
- 2026-09-29 created (aw backlog): aw config show/get/set/add/unset crash with an unhandled ImportError when passed --agent, so the whole config family has no machine-readable surface

MEASURED 2026-09-29 at HEAD `1ea7928f` while authoring plan `ypnk56` (graduating backlog `g0bdgg`).

WHAT IS WRONG: SEVEN `aw config` verbs, which is every verb in the family except the `config exclude`
subgroup, CRASH with an unhandled `ImportError` the moment `--agent` is passed, so the
machine-readable surface of the whole family is dead. Each handler does
`from agent_workflows.term import format_agent_json` inside its `--agent` branch, and
`agent_workflows/term.py` defines NO such symbol. The exception is not caught, so the process dies
with a traceback instead of emitting an `aw.agent/v1` record or returning a documented exit code.

THE SEVEN CALL SITES, all in `agent_workflows/cli.py`, each an `--agent` branch: `_run_config_show`
(which holds TWO such imports, one per output path), `_run_config_get`, `_run_config_set`,
`_run_config_unset`, `_run_config_add`, `_run_config_remove`, and `_run_config_is`. That is eight
import statements across seven functions. Only the `config exclude` subgroup
(`_run_config_exclude`) takes a different route and is unaffected; `config exclude list --agent`
was driven and exits 0.

EVIDENCE (driven in-process with `XDG_CONFIG_HOME` pointed at a throwaway dir, so no real config was touched):

    config show --agent                          -> CRASH ImportError
    config get repos.search --agent              -> CRASH ImportError
    config set defaults.backup false --agent     -> CRASH ImportError
    config unset defaults.backup --agent         -> CRASH ImportError
    config add /tmp/x to repos.exclude --agent   -> CRASH ImportError
    config remove /tmp/x from repos.exclude --agent -> CRASH ImportError
    config is /tmp/x in repos.exclude --agent    -> CRASH ImportError
    config exclude list --agent                  -> exit=0 (unaffected, different route)

Every crash is the same message: `cannot import name 'format_agent_json' from 'agent_workflows.term'`.

Traceback tail for the `unset` case:

    File ".../agent_workflows/cli.py", line 9354, in _run_config_unset
        from agent_workflows.term import format_agent_json
    ImportError: cannot import name 'format_agent_json' from 'agent_workflows.term'

WHY IT SURVIVED: the corresponding `--json` branches DO work (they call `json.dumps` directly), and
NO test in `tests/` drives any `config` verb with `--agent`, so the dead branch is entirely uncovered.

WHY THIS IS A BUG AND NOT A CHORE: the failure is user-perceptible and total, not a slow path. An
agent following the documented protocol (`docs/cli-agent-protocol.md`) and passing `--agent` gets a
traceback and a nonzero exit with no parseable record at all, so the command cannot be consumed
machine-readably. Per the repository release-gate policy every live bug carries `- Blocks-Release:`.

LIKELY FIX (unverified, for the eventual plan to confirm): route these branches through whatever
emitter the rest of the CLI actually uses for `aw.agent/v1` output (`agent_workflows/agent_schema.py`
holds `render_jsonl_record` / `validate_agent_record`; other families emit via their own helper, for
example `upgrade_rehearsal._emit_agent`), rather than a symbol that does not exist. Any fix MUST come
with tests driving ALL SEVEN verbs with `--agent`, asserting a valid record plus the declared exit
code, since the absence of such tests is what let this ship. Also check the `command_surface`
declarations for the `config` family, which list `--agent` as an accepted flag.

NOT IN SCOPE OF `g0bdgg`: that item is about argparse `description=` text on eight subparsers and its
plan `ypnk56` deliberately touches no handler. This was found incidentally while measuring
`config unset` behavior to author an accurate description, and is filed separately rather than folded in.
