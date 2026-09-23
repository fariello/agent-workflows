- Id: 0b290s
- Status: open
- Blocks-Release: next
- Set: 0b290s
- Priority: medium
- Work-Kind: bug
- Summary: A parser leaf positional named 'command' silently shadows the subparsers dest and dispatch falls through to help with no error

## Workflow history
- 2026-09-22 created (aw backlog): Found while adding 'aw integration-lock' (plan vddpml E-07).

OBSERVED 2026-09-22 while adding the `integration-lock` leaf. The leaf declared a REMAINDER positional named `command`, which is the SAME dest the top-level `sub = parser.add_subparsers(dest="command")` uses. argparse silently overwrote the resolved subcommand name with the REMAINDER list, so `args.command` was `[]` instead of `"integration-lock"`, every `if args.command == ...` branch missed, and `_dispatch` fell through to `parser.print_help(); return 2`.

WHY IT IS A BUG AND NOT A GOTCHA: the failure is SILENT and its symptom is misleading. There is no argparse error, no collision warning, and no traceback; the operator sees a correct-looking top-level help page and exit 2, which reads as 'you typed the command wrong' rather than 'this leaf is structurally broken'. Diagnosing it required printing `vars(args)`. Any future leaf that adds a positional or flag whose dest is `command` (an easy, natural name for a wrapped command) reproduces it, and the leaf will appear in `--help` and in `discover_parser_leaves` while being unreachable.

THE FIX IN THIS INSTANCE was to rename the positional to `locked_command`, which is a workaround rather than prevention.

WHAT WOULD PREVENT IT: a structural test over `cli._build_parser()` asserting that no subparser declares an argument whose `dest` collides with an ANCESTOR subparsers action's `dest` (`command`, and the per-family dests such as `oc_command`, `runs_command`). That is a cheap AST/parser-object walk in the spirit of the existing `discover_parser_leaves` guards, and it turns a silent unreachable leaf into a failing test.

RELATED: the conformance matrix's `usage_error` scenario does not catch this, because a shadowed leaf still exits 2.
