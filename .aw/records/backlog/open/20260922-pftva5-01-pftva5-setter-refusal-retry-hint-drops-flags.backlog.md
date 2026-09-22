- Id: pftva5
- Status: open
- Blocks-Release: next
- Set: pftva5
- Priority: medium
- Work-Kind: bug
- Summary: Correct the aw set confirmation refusal's retry hint: it drops the caller's flags and rewrites the verb

## Workflow history
- 2026-09-22 created (aw backlog): Correct the aw set confirmation refusal's retry hint: it drops the caller's flags and rewrites the verb

FOUND BY: executing IPD 4bc1nd (Set setterguard), which recorded this as finding F-11 and deferred it with a required carrier.

WHAT IS WRONG. The confirmation refusal in `status_set.run_set_command` builds its suggested retry command as `f"aw set {' '.join(raw_args)} --yes"` (agent_workflows/status_set.py:1819). `raw_args` holds only the status and the selectors, so the printed hint DROPS every other flag the caller passed AND rewrites the invoked verb as the untyped `aw set`.

MEASURED 2026-09-22 in a scratch repo, on the code as of this filing:

    $ aw ipd set reviewed aaaa03 --actor 'me model=x' -m 'retire note' --no-commit --dir .
    Next  aw set reviewed aaaa03 --yes (Apply status changes)

So `--actor`, `-m` and `--no-commit` are silently lost, and `ipd set` became `set`. A caller who copy-pastes the hint performs a DIFFERENT transition from the one they asked for: without `--actor` the history line is attributed to the generic `aw set` rather than the agent, and without `--no-commit` the setter may self-commit when the caller asked it not to.

WHY IT MATTERS MORE NOW. IPD 4bc1nd extended that refusal to every FLAGLESS caller (previously only `--agent`/`--json` callers could reach it), so this hint went from rarely seen to seen by every unconfirmed setter invocation. 4bc1nd deliberately did not fix it: constructing a faithful retry string means reconstructing the invoked verb and every declared flag from the parsed namespace, which is a general CLI-echo capability with its own correctness surface (which flags are safe to echo, which could carry secrets, how the five routing spellings map back to their verb). Printing a command that does something OTHER than what the caller asked is worse than printing an under-specified one, so it wants its own reviewed change.

INTERIM MITIGATION ALREADY IN PLACE: the refusal lists the full change set, so a caller can see the blast radius even when the suggested command is incomplete.

SUGGESTED FIX. Echo the invoked verb and the caller's declared flags from the parsed namespace rather than from `raw_args`, or alternatively print no command at all and describe the needed flag in prose. Decide explicitly which flags are echo-safe.
