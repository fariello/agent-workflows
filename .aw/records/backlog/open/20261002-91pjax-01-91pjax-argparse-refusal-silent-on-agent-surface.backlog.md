- Id: 91pjax
- Status: open
- Blocks-Release: next
- Set: 91pjax
- Priority: low
- Work-Kind: bug
- Summary: seven mutation leaves exit 2 with empty stdout under --agent when argparse refuses a missing required positional

## Workflow history
- 2026-10-02 created (aw backlog): seven mutation leaves exit 2 with empty stdout under --agent when argparse refuses a missing required positional

Measured in lane lbbo9s at HEAD b8e1e0157 while authoring plan 7pnneh (from backlog lbbo9s).

THE DEFECT. Seven mutation-class leaves, driven with `--agent` and no positional argument, exit 2 having written ZERO bytes to stdout: `ipd scaffold`, `research new`, `research new-comparison`, `storage move`, `backlog new`, `specs new`, `prompts new`. Each writes its argparse error to stderr and nothing at all to the machine stream, so a caller parsing stdout gets an empty string and cannot distinguish a refusal from a crash, a hang, or a successful no-op. `tests/test_agent_surface_conformance.py` asserts non-empty stdout as its FIRST property for exactly this reason.

WHY THIS IS A SEPARATE DEFECT FROM THE FAMILY-ROOT CASE, which is the reason this item exists at all. Pending plan `vfv2db` (backlog `w78faq`) E-06 nominated backlog `lbbo9s` as this finding carrier, on the ground that it is "a real machine-surface hole of the same family as upgrade-test". Plan `7pnneh`, authored from `lbbo9s`, DECLINED that handoff with reasons measured at the same HEAD: (1) argparse refuses a MISSING REQUIRED ARGUMENT before any handler runs, so there is no handler to route through `cli._show_family_help` and the fix must live in argument parsing or in a parser-level error hook, whereas `upgrade-test` fix was a four-line dispatch replacement inside an existing handler; (2) none of the seven is a family ROOT, while `lbbo9s` whole concern is the subcommand-less group case; (3) all seven are `mutation`-class leaves inside `vfv2db` own declared universe, and `vfv2db` already owns 48 further `arg_fixture_needed` leaves in the same area. Absorbing them into a dispatch fix would have pulled seven unrelated modules into a plan whose declared scope was one `if` block.

SO `vfv2db` E-06 SHOULD BE RE-POINTED at this item id instead of at `lbbo9s`. That is the concrete follow-up action, and it is why this item was filed at authoring time rather than promised: a carrier that only exists if some plan executes is the obligation loss the repository carrier rules exist to prevent.

WHAT TO DECIDE. The fix is architectural rather than per-verb: whether `_AwArgumentParser` overrides `error()` (and/or `exit()`) to emit an `aw.agent/v1` `error` record with `outcome: cannot-run` and `exit: 2` when the active output mode is agent/json, and if so how the output mode is known at parse time (it is currently resolved AFTER `parse_args` via `select_output(args)`, which is the crux: an argparse error fires BEFORE that call, so the mode must be sniffed from raw argv or the parse restructured). A naive per-verb fix in seven handlers would NOT work, because the handlers never run.

SCOPE BOUNDARY: this item is about the argparse-level refusal path, which is CLI-wide and affects every leaf with a required positional, not only these seven. The seven are the measured instances in the mutation sweep; a complete fix should be gated by a behavioral sweep over every leaf with a required positional rather than by a hand list.
