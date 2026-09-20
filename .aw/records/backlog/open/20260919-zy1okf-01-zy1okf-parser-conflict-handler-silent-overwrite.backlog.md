- Id: zy1okf
- Status: open
- Set: zy1okf
- Priority: low
- Work-Kind: chore
- Summary: conflict_handler='resolve' on every aw parser makes a duplicate option definition silently replace instead of erroring

## Workflow history
- 2026-09-19 created (aw backlog): conflict_handler='resolve' on every aw parser makes a duplicate option definition silently replace instead of erroring

Graduated from the Deferred section of plan `yaxr4i` (ttyflags 01), where it was finding F-14 and was mitigated per-parser rather than fixed.

THE HAZARD. `_AwArgumentParser.__init__` sets `conflict_handler="resolve"` on EVERY parser in the CLI. So if a parser that already declares an option gains `parents=[...]` carrying the same option, argparse SILENTLY REPLACES one definition instead of raising. The failure is invisible: the flag still parses, but which definition (and therefore which dest, default and help) wins is not obvious from the registration site.

MEASURED STATE, 2026-09-19: no live collision exists. All 12 parser objects that lacked `--no-color` were checked and none declared `--no-color`, `--agent` or `--json`, so `yaxr4i`'s additions could not have hit it. The hazard is latent, not active, which is why this is `chore` and `low`.

WHY IT WAS NOT FIXED IN `yaxr4i`: flipping it repo-wide could surface duplicate definitions across all 229 subcommands at import time, which is unrelated to that item's flags and is its own change with its own blast radius. The mitigation used instead was a per-parser collision re-check at execution time, which protects that one change and nothing after it.

WHAT THE WORK IS: decide whether to remove the blanket `resolve`, and if so, fix whatever duplicate definitions it is currently hiding. A cheap first step is a test that builds the parser with `conflict_handler='error'` and reports every collision, so the size of the problem is known before the policy changes.
