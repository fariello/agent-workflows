- Id: qm04zi
- Status: graduated
- Graduated-To: qm04zi
- Blocks-Release: next
- Set: qm04zi
- Priority: medium
- Work-Kind: bug
- Summary: docs advertise --verbose as a general agent-mode token-control flag but only upgrade-test new accepts it, so the documented usage exits 2

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053024Z-3198670: c4btis
- 2026-09-29 created (aw backlog): Carrier filed while authoring plan 75ic2f (backlog rcjorx): the same reach defect rcjorx records for --fields, on its documented sibling --verbose.

MEASURED 2026-09-29 at HEAD `3f7997b2` while authoring plan `75ic2f` from backlog item `rcjorx`.

THIS IS THE SAME DEFECT `rcjorx` RECORDS, ON ITS DOCUMENTED SIBLING FLAG. `docs/cli-agent-protocol.md` (`## Token control`) introduces its bullets with "Two escape hatches tune the token cost" and lists `--fields <a,b,c>` and then `- --verbose: include full nested diagnostics, change details, and evidence dictionaries.` `docs/cli-output-contract.md` (`## 6. Token Control and Escape Hatches`) lists `--verbose` alongside `--fields` and `--limit` the same way. Neither states any restriction on which commands accept it.

THE ACTUAL SURFACE IS ONE COMMAND, AND IT IS NOT THE ONE THE DOCS DESCRIBE. Walking the built parser and deduplicating leaves by object identity: 151 unique leaves, 139 carrying `--agent`, and exactly 1 carrying `--verbose`, namely `aw upgrade-test new`, where it controls installer output rather than agent-record verbosity. Measured:

    $ aw check plans --agent --verbose
    agent-workflows: error: unrecognized arguments: --verbose
    (exit 2)

THE FLAG HAS A REAL CONSUMER, SO DECLARING IT WOULD WORK. This is worth stating because it is the opposite of what a reader might assume from the flag being absent. `result_types.select_output` already reads it (`verbose_val = bool(getattr(args, "verbose", False))`) and puts it on the context, and `CommandResult.to_agent_record` branches on `context.verbose` in three places: it emits full `changes` dictionaries instead of a count or truncated list, full `evidence` dictionaries instead of `sanitize_evidence_item` output, and full `diagnostics` dictionaries instead of the `{location, rule}` pairs. So the behavior the two documents promise is implemented and simply unreachable from any command a reader would use it on.

WHY IT IS A BUG AND NOT A CHORE: a documented invocation exits 2 with `unrecognized arguments`, naming a flag the reader just read in the official protocol reference, and an agent following that reference to widen its diagnostics receives a usage error it cannot distinguish from its own malformed request. That is the same user-perceptible failure `rcjorx` cites. Per AGENTS.md a live bug gates the next release, hence `Blocks-Release: next`.

SUGGESTED FIX: declare `--verbose` on the shared output-mode parents (`common` and `common_upgrade` in `cli._build_parser`), exactly as plan `75ic2f` does for `--fields`. TWO CONSTRAINTS THAT PLAN MEASURED AND THIS ONE INHERITS. FIRST, `aw upgrade-test new` ALREADY DECLARES `--verbose`, and `_AwArgumentParser` deliberately keeps argparse's default `conflict_handler="error"`, so that leaf declaration must be DELETED or the parser raises `ArgumentError: conflicting option string: --verbose` at build time and every `aw` invocation dies on import. That is not a mechanical deletion here: the existing flag means installer verbosity on that command, so folding it into the shared agent-mode flag either changes that command's behavior or needs a distinct name for the installer sense. SECOND, adding a shared long option can destroy working prefix abbreviations; `75ic2f` measured 14 such breakages from adding `--fields` and turns abbreviation off to handle them, so this item should be sequenced AFTER `75ic2f` and re-measure rather than assume the collision set is unchanged. Related: `rcjorx`, plan `75ic2f`, and `wdazvp` (a third token-control flag inert on `aw find --agent`).
