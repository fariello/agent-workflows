- Id: wdazvp
- Status: open
- Blocks-Release: next
- Set: wdazvp
- Priority: medium
- Work-Kind: bug
- Summary: aw find --agent prints bare paths and ignores --fields and --limit because its agent branch returns before building a record

## Workflow history
- 2026-09-29 created (aw backlog): Carrier filed while authoring plan 75ic2f (backlog rcjorx).

MEASURED 2026-09-29 at HEAD `3f7997b2` while authoring plan `75ic2f` from backlog item `rcjorx`.

`aw find`'s agent path has a branch, taken when `getattr(args, "paths", False) or (ctx.is_agent and all_paths)`, that prints bare repo-relative paths one per line and RETURNS before constructing any `CommandResult`. Its code comment states the intent deliberately: stdout is byte-identical to `--paths` so scripts can consume it line by line, and no warning line may enter that stream. TWO TOKEN-CONTROL FLAGS ARE CONSEQUENTLY INERT ON IT.

`--limit` IS ACCEPTED, REACHES THE CONTEXT, AND IS IGNORED. Measured:

    $ aw find plans --agent --limit 20 | wc -l
    985

The flag is not unwired: `aw find` declares `--limit` (via the shared noun-verb loop) and `select_output` puts it on the context (probed: `ctx.limit == 20`). Only `renderers.AgentRenderer.render_stream` honors `ctx.limit`, and `find` does not use it, so all 985 rows print. The guide advertises this exact command: `docs/cli-human-guide.md` reads `| Bounded output with a continuation hint | aw find plans --agent --limit 20 |`, so a reader is told they get a bounded answer with a continuation hint and receives neither, and no `summary` record carrying `total`/`emitted`/`omitted` is emitted at all.

`--fields` IS TODAY REFUSED AND WILL BECOME SILENTLY INERT. That flag reaches only four `aw runs` leaves, which is the separate defect `rcjorx` records; `aw find plans --agent --fields findings` currently exits 2. Plan `75ic2f` moves the flag onto the shared output-mode parents, and measured under that patch the command then prints 985 bare paths and projects nothing, turning a loud usage error into a silent no-op. `75ic2f` therefore deliberately does NOT point the guide's example at this command, and filed this item instead.

NOTE THE BRANCH IS CONDITIONAL, WHICH IS WHAT MAKES IT CONFUSING. The record-emitting path IS reached when the query matches nothing or a selector is given, so `aw find plans rcjorx --agent --fields findings` projects correctly under that patch while the same command without a selector does not. A caller cannot tell from the flag which behavior they will get.

WHY IT IS A BUG AND NOT A CHORE: a documented command produces output that contradicts what the guide says it produces, and for `--fields` the future state is worse than an error because nothing signals the flag was dropped. Per AGENTS.md a live bug gates the next release, hence `Blocks-Release: next`.

THE FIX IS A CONTRACT DECISION, NOT A ONE-LINER, which is why this is filed rather than folded into `75ic2f`. Deciding it means deciding what `aw find --agent` should emit at all: honoring `--limit`/`--fields` means emitting `item` plus `summary` records instead of bare paths, which changes a machine surface every existing consumer parses line by line, and the branch's comment records the byte-identical-to-`--paths` property as deliberate. Candidate directions: (a) emit a real record stream under `--agent` and keep bare paths for `--paths` only, which is the honest fix and a breaking change to that surface; (b) keep bare paths and REFUSE `--limit`/`--fields` there with exit 2, so the flags never silently lie; (c) keep bare paths and honor `--limit` by truncating the path list, which is cheap but still emits no continuation hint and so only half-fixes the guide's claim. Related: `rcjorx` (which command accepts `--fields`) and `qm04zi` (the same reach defect on `--verbose`).
