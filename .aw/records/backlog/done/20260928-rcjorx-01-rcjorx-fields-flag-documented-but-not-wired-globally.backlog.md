- Id: rcjorx
- Status: done
- Graduated-To: rcjorx
- Blocks-Release: next
- Set: rcjorx
- Priority: medium
- Work-Kind: bug
- Summary: Docs advertise --fields as a general agent-mode flag but only four runs subcommands accept it, so the documented example exits 2

## Workflow history
- 2026-10-01 set (aw backlog): closed by aw oc run: IPD 75ic2f executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260929-rcjorx-01-75ic2f-wire-fields-onto-the-shared-output-mode-parents-so-every-age.ipd.md); evidence .aw/records/plans/executed/20260929-rcjorx-01-75ic2f-wire-fields-onto-the-shared-output-mode-parents-so-every-age.ipd.md
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: 75ic2f
- 2026-09-28 created (aw backlog): Filed while authoring plan gygujf (from backlog 3f4ayi): the human guide's --fields example exits 2 with unrecognized arguments, and only the four runs subcommands wire the flag.

MEASURED 2026-09-28 at HEAD `71aee0d3` while authoring plan `gygujf` from backlog item `3f4ayi`.

THREE USER-FACING DOCUMENTS DESCRIBE `--fields` AS A GENERAL AGENT-MODE FLAG, AND IT IS NOT ONE. `docs/cli-human-guide.md` gives it as a worked example in its how-do-I table:

    | Only the fields you care about (agent) | `aw find plans --agent --fields findings` |

That command does not run. Measured:

    $ aw find plans --agent --fields findings
    agent-workflows: error: unrecognized arguments: --fields
    (exit 2)

`docs/cli-agent-protocol.md` (`## Token control`) and `docs/cli-output-contract.md` (`## 6. Token Control and Escape Hatches`) both describe `--fields <list>` alongside `--limit` and `--verbose` with no statement that it is available on only a few commands, which reads as a protocol-wide escape hatch.

THE ACTUAL SURFACE IS FOUR COMMANDS. `grep` for `"--fields"` across the package returns exactly four `add_argument` calls, all in the `runs` subparsers: `aw runs analyze`, `aw runs query`, `aw runs export`, `aw runs submit`. Every other command, including the `aw find plans` the guide names and the `aw status` and `aw check` a reader would try next, rejects the flag with exit 2. By contrast `--agent` and `--json` are on the SHARED output-mode group and so reach every leaf, which is exactly why a reader assumes `--fields` does too.

WHY IT IS A BUG AND NOT A CHORE. A documented command that exits 2 with `unrecognized arguments` is user-perceptible by construction: the advertised invocation fails outright, and the failure names a flag the reader just read in the official guide. An agent following the guide to reduce token cost gets a usage error it cannot distinguish from its own malformed request, which is the same confusion `3f4ayi` cites as its reason for being a bug. Per AGENTS.md a live bug gates the next release, hence `Blocks-Release: next`.

TWO CANDIDATE FIXES, and choosing between them is a real decision rather than a detail:

(a) MOVE `--fields` TO THE SHARED OUTPUT-MODE GROUP so it reaches every command, making all three documents true as written. This matches how `--agent`, `--json` and `--limit` are already plumbed, and `result_types.select_output` ALREADY reads `fields` generically off `args` (it accepts either a comma string or a sequence), so the plumbing largely exists. This is the fix that matches what the docs promise and what a reader expects.

(b) CORRECT THE THREE DOCUMENTS to say `--fields` is available on the `runs` family only, and replace the guide's example with one that runs. Smaller, but it narrows a documented capability rather than delivering it, and it leaves the asymmetry with `--limit` unexplained.

(a) is preferred on the evidence above; it should be decided by whoever picks this up, since it changes a CLI surface on every command.

RELATED BUT DISTINCT: `3f4ayi` (bug, gated) and its plan `gygujf` concern whether a projection produces a VALID record, i.e. the correctness of `agent_schema.filter_record_fields` once the flag IS accepted. This item concerns WHICH COMMANDS accept the flag at all. Fixing either leaves the other live, and note the interaction: fix (a) here would widen the blast radius of `3f4ayi`'s latent crash from four commands to all of them, so `gygujf` should land first.

NOT FIXED IN `gygujf`: that plan's Scope-Paths cover `agent_schema.py`, its new test, and the `--fields` bullets in the two protocol documents. It does not touch `cli.py` (a CLI surface change) and does not touch `docs/cli-human-guide.md`. Filed so the defect has a carrier rather than living in that plan's prose.
