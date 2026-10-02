- Id: 94op6l
- Status: open
- Blocks-Release: next
- Set: runclileak
- Priority: medium
- Work-Kind: security
- Summary: run_cli human-mode output is not redacted though its docstring claims both surfaces are, leaking a token that the --agent surface masks

## Workflow history
- 2026-10-02 created (aw backlog): found while graduating h9kgjp (run_cli docstring vs module contradictions)

`run_cli`'s module docstring Contract block claims "Redacts sensitive values in both human and machine outputs". MEASURED FALSE on the human surface: redaction lives ONLY in `run_cli._emit_machine`, which calls `_redact_output` before printing, while `_emit_error`'s human branch prints `f"error: {message}"` with no redaction, and no other `print(` in the module routes through `_redact_output`.

REPRODUCED TWICE against the real handlers at HEAD. (1) A missing target whose path embeds a token: `aw runs show` human mode printed `error: ledger file not found for target '<dir>/ghp_BBBB...'` LEAKING the token verbatim, while the same call with `--agent` emitted `"...target '<dir>/[REDACTED]'"`. (2) Secret in ledger CONTENT: a `tool_event` whose `argv` carried `Bearer ghp_CCCC...`, read back with `aw runs evidence`: human mode LEAKED the token, `--agent` masked it. So the two surfaces disagree, and the one a human reads (and pastes into a terminal, a bug report, or an agent transcript) is the UNREDACTED one.

WHY security AND NOT chore: the claim is a stated safety property that a reader relies on, and the failure direction is disclosure of a credential rather than cosmetic drift. The redaction pattern `_redact_output` already recognizes `ghp_`/`Bearer` tokens and `KEY`/`TOKEN`/`SECRET`/`PASSWORD`/`AUTH`/`CRED` keys, so the capability exists and is simply not wired into the human path.

FOUND BY the h9kgjp graduation, which fixes only the EXIT-CODE half of the same docstring's Contract block. NOT FIXED THERE because this is a behavior change to a security property with its own test surface, while h9kgjp is a docstring-only correction; folding a code change into it would turn a zero-risk documentation fix into a security change needing its own review. The h9kgjp plan must therefore NOT silently delete this docstring bullet to make the docstring 'true', and it is instructed not to.
