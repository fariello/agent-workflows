- Id: 5x195l
- Status: open
- Blocks-Release: next
- Set: 5x195l
- Priority: medium
- Work-Kind: bug
- Summary: aw ipd --agent crashes with a schema ValueError in a non-project directory (exit_code=3 is unemittable)

## Workflow history
- 2026-09-21 created (aw backlog): aw ipd --agent crashes with a schema ValueError in a non-project directory (exit_code=3 is unemittable)

MEASURED 2026-09-21 on a clean HEAD (found while executing IPD rkn8ya, attcor-01).

REPRODUCTION. From any directory that is NOT an AW project:

    cd $(mktemp -d) && aw ipd --agent

raises, rather than emitting a diagnostic:

    ValueError: Invalid aw.agent/v1 record: Field 'exit' must be an integer in (0, 1, 2), got '3'; Error record must carry exit=2, got exit=3

THE CAUSE is a contract conflict, not a typo. `cli.py:8127` builds a `CommandResult(status="cannot-run", exit_code=3)` for the no-project case and DOES pass it to `get_renderer(ctx).emit(...)`. But `aw.agent/v1` admits only exit 0/1/2 (`agent_schema.validate_agent_record`, the `exit not in (0, 1, 2)` rule) and additionally requires an error-class record to carry `exit=2`. So the record can never serialize, and the renderer raises before writing a byte. `docs/cli-output-contract.md` Section 3 classifies exactly this condition ("Cannot-Run ... preventing domain inspection") as exit 2, and its exit-parity rule requires the embedded `exit` to equal the process exit code.

WHY IT WAS NOT FIXED IN rkn8ya. That plan fixed the SAME defect in `aw attention` (its E-12) by emitting `exit_code=2` on the machine surfaces while leaving the HUMAN surface at its long-standing exit 3. `cli.py` is outside that plan's declared Scope-Paths, so the sibling was reported rather than changed. See decision 12-rkn8ya-D1 in that run's decisions register.

SUGGESTED FIX: mirror the attention resolution at `cli.py:8127` (machine surfaces emit `exit_code=2` with `outcome: cannot-run`; the human stderr path keeps exit 3), and additionally sanitize the machine `summary`, because `project_context.no_project_message` interpolates `Path.cwd()` and would write a machine-local ABSOLUTE path into the payload.

AUDIT NOTE: `grep -n "exit_code=3" agent_workflows/*.py` finds exactly two sites, `attention.py` (fixed by rkn8ya) and this one. A broader question worth deciding separately is whether the no-project condition should surface as exit 2 everywhere, retiring 3 entirely, since 3 is outside the published three-state classification.
