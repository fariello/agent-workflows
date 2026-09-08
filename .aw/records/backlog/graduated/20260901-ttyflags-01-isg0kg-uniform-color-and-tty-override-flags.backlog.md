- Id: isg0kg
- Status: graduated
- Set: ttyflags
- Priority: high
- Work-Kind: feature
- Summary: Every aw command should accept a uniform trio of presentation overrides: --no-color (exists on 59/60 top-level but missing from 9 nested host-driver subcommands), --color (force 256-color ANSI, no env var needed), and --tty (behave as if attached to an interactive TTY)

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to plan yaxr4i (Set ttyflags, .aw/records/plans/pending/20260908-ttyflags-01-yaxr4i-...ipd.md), which carries From-Backlog: isg0kg. This item carries no Blocks-Release, so the plan inherits none. Status graduated (design handed off), NOT done. NOTHING IN THIS ITEM IS OBSOLETE and nothing covers it; no pending or approved plan and no spec touches --color, --tty or the common parent's flag set. RE-MEASURED 2026-09-08 at HEAD a2e0438a by walking the built parser tree exactly as this item did, and THE GAP HAS GROWN AND IS ACTIVELY REGROWING: the item reports --no-color missing on 18 of 175 nested subcommands; I measure 25 of 219 missing, and the list has changed shape as well as size. It now includes 'run as', 'run ipd', 'oc review', 'agy review', 'opencode review' and 'antigravity review', which did not exist when this item was written, alongside the 9-doubled host-driver set it named. So every nested subcommand added since has ALSO missed parents=[common]. That is why the plan's durable deliverable is the PARSER-WALK TEST (E-04) rather than the flag additions: a per-command spot check demonstrably did not catch this, and without a test the gap will regrow again. --color and --tty remain at 0 of 219, as filed. THE DOC-VERSUS-CODE DIVERGENCE THIS ITEM FOUND IS CONFIRMED LIVE, and it is the reason the plan deliberately does NOT specify --tty: measured by execution, non-TTY stdout gives mode=OutputMode.HUMAN color=False and TTY stdout gives mode=OutputMode.HUMAN color=True, so piping yields monochrome HUMAN text and never JSONL, while docs/cli-output-contract.md:18 publishes 'non-TTY stdout (pipe/redirect) => agent' and :161 calls it a maintainer decision adopted 'immediately upon release', with the same claim repeated in select_output's docstring at result_types.py:75. I confirmed the code has NO such branch at all: result_types.py contains exactly TWO isatty mentions and both are inside that docstring, the only real TTY consultation being should_color(out_stream) for COLOR at :159. This item is right that it must be settled first, and the plan carries it as a BLOCKING open question with a recommendation (correct the docs, since the documented behavior has never shipped so nothing depends on it, whereas implementing it would change what every piped aw invocation emits and break any existing consumer that parses prose). WHAT IS GRADUATED: GAP 1 (the 25 missing --no-color), GAP 2 (--color as a mutually exclusive twin on common, threaded through the existing engine with an override parameter on should_color so no os.environ mutation leaks into subprocesses), the written precedence table, the parser-walk test, and the doc-versus-code resolution. WHAT IS DEFERRED, with reasons recorded in the plan: --tty ITSELF and any change to interactive prompting. This item presents three options (presentation-only, both axes, or two separate flags) and asks the maintainer to rule, AND requires the divergence settled first because implementing the documented rule would make --tty flip AUDIENCE MODE as a side effect. The plan's E-06 writes the two-axis constraint into the published contract instead, including the requirement that any future --tty route the interactivity axis through ONE resolver rather than a flag check at each site; I re-counted that axis as 49 isatty references package-wide (this item said 44), 18 in cli.py alone. The 16-versus-256-color capability tier is recorded as explicitly not smuggled in, per this item's instruction: --color sets the one existing self.color boolean that already gates both palettes.
- 2026-09-01 created (aw backlog): Every aw command should accept a uniform trio of presentation overrides: --no-color (exists on 59/60 top-level but missing from 9 nested host-driver subcommands), --color (force 256-color ANSI, no env var needed), and --tty (behave as if attached to an interactive TTY)

REQUESTED by the maintainer 2026-09-01: all `aw` tools should have `--no-color`, `--color` (forces
256-color ANSI formatting), and `--tty` (forces it to behave as if attached to an interactive TTY). The
maintainer noted `--no-color` probably already exists; MEASURED BELOW, it mostly does, and the other two
do not exist at all.

STATE OF PLAY, measured at HEAD `30556c52` by walking the built parser tree, not by reading docs:

| Flag | Top-level subcommands | Nested subcommands | Env equivalent |
| --- | --- | --- | --- |
| `--no-color` | 59 of 60 (only the hidden `__complete` lacks it, correctly) | MISSING on 18 of 175 | `NO_COLOR` |
| `--color` | 0 | 0 | `FORCE_COLOR` (env only) |
| `--tty` | 0 | 0 | none at all |

`--no-color` is declared ONCE on the shared `common` parent parser (`cli.py:586-590`) and inherited via
`parents=[common]`, which is why coverage is nearly total and why the fix for the gap is mechanical.

GAP 1: THE 18 NESTED SUBCOMMANDS THAT DO NOT INHERIT `common`. These are 9 real commands, doubled
because each host group is registered twice under an alias (`agy`/`antigravity`, `oc`/`opencode`):
`agy exec`, `agy run`, `agy runagy`, `agy runipd`, `agy sessions`, `agy view`,
`agy view-antigravity-jsonl`, `oc run`, `oc runipd`. So `aw oc run --no-color` is a usage error TODAY
while `aw attention --no-color` works. That inconsistency is the concrete bug inside this feature
request, and it hits exactly the long-running driver commands whose output a user is most likely to want
to pipe or capture.

GAP 2: `--color` HAS NO FLAG FORM, ONLY AN ENV VAR. `term.should_color()` (`term.py:74-98`) already
implements the wanted semantics: `NO_COLOR` off unless `FORCE_COLOR` overrides (`:84-88`), then
`TERM=dumb`/unset off (`:90-92`), then `isatty()` (`:94-98`). So forcing color on is possible today ONLY
as `FORCE_COLOR=1 aw ...`. A `--color` flag is the missing surface over an already-correct engine.
NOTE the maintainer specified 256-COLOR: the 256-palette path is `Term.color256` (`term.py:254-264`) with
`STATUS_COLOR_256` (`term.py:101+`), and it is gated by the SAME single `self.color` boolean as the
16-color `colorize` (`:244-252`). So `--color` does not need a new capability tier; it needs to set that
one boolean. If a distinct "16-color vs 256-color" capability level is ever wanted, that is a SEPARATE
question and should not be smuggled in here.

GAP 3: `--tty` HAS NO EQUIVALENT AT ALL, AND WOULD SPAN TWO INDEPENDENT AXES. This is the substantive
design problem in the item, so it is stated precisely. TTY-ness currently controls two unrelated things
through two different streams:

  (a) PRESENTATION, keyed on STDOUT: `should_color(stdout)` (`term.py:94-98`) and
      `select_output` color resolution (`result_types.py:157-160`).
  (b) INTERACTIVITY (whether to PROMPT), keyed on STDIN: 15 separate `sys.stdin.isatty()` call sites in
      `cli.py` alone (`:3841` `_confirm`, `:3931` `_confirm_install`, `:3982`, `:4032`, `:4302`, `:4610`,
      `:4714`, `:4856`, `:4954`, `:5592`/`:5594` setup wizard, `:6484`, `:8325`, `:8491`, `:8984`), plus
      `git_commit_helper._is_interactive` (`:282-294`), `install_wizard`, `specs.py`, `status_set.py`,
      `ipd_lifecycle.py`, `pwatch.py`, `render_stream.py`, `oc_runipd.py`, `agy_runipd.py`
      (44 `isatty` references across the package).

The existing contract deliberately keeps these apart. `select_output`s own docstring (`:76`) says
"`stdin.isatty()` controls interactive prompting, NOT audience/mode", and
`docs/cli-output-contract.md:28` repeats it. THEREFORE `--tty` MUST NOT be one undifferentiated boolean
unless that separation is explicitly retired. DECIDE, and this is the main open question:

  OPTION A: `--tty` means presentation only (pretend stdout is a TTY). Cheap, safe, fully covered by the
    two seams in (a). But it does NOT do what the maintainer literally asked ("behave as if it were
    attached to an interactive TTY"), because prompting would still be declined.
  OPTION B: `--tty` means both, i.e. it also makes prompts fire when stdin is a pipe. This is what was
    asked for, and it is DANGEROUS in exactly one direction worth naming: `_confirm` (`:3841-3846`)
    currently DECLINES and warns when non-interactive, which is a deliberate fail-safe ("Non-interactive
    without --yes: refuse to change things silently"). Under `--tty` it would instead call `input()` on a
    pipe, get EOF, and return False anyway (`:3849-3850`), so the practical effect is a WORSE message
    rather than a hang, unless stdin actually carries answers.
  OPTION C: two flags, `--tty` (presentation) and `--interactive` (prompting), each with a `--no-` twin.
    Most honest, most flags.

RECOMMENDED SHAPE, not decided: implement `--color`/`--no-color` as a mutually exclusive pair on the
`common` parent, implement `--tty` as OPTION A plus a SEPARATE `--interactive`/`--no-interactive` pair
(OPTION C), because conflating the two axes would silently weaken the non-interactive fail-safe that 15
call sites currently rely on. The maintainer should rule.

A DOCUMENTATION/BEHAVIOR DIVERGENCE FOUND WHILE MEASURING (worth fixing under this item, since `--tty`
would otherwise inherit the confusion): the PUBLISHED contract says non-TTY stdout auto-selects AGENT
mode, and calls it a hard cutover. `docs/cli-output-contract.md:18` ("non-TTY stdout (pipe/redirect) =>
agent"), `:24-27`, and `:159-161` ("Per maintainer decision OQ-01, non-TTY stdout adopts `aw.agent/v1`
JSONL immediately upon release"), and the same claim sits in `select_output`s docstring at
`result_types.py:75`. THE CODE DOES NOT DO THIS. `select_output` (`:107-171`) never calls
`stdout.isatty()` for mode selection at all; it only uses it for COLOR at `:160`. Verified by execution:

    non-TTY stdout -> mode: OutputMode.HUMAN color: False
    TTY stdout    -> mode: OutputMode.HUMAN color: True

So piping `aw` today yields monochrome HUMAN text, not JSONL. Either the docs or the code is wrong, and
that must be settled BEFORE `--tty` is specified, because if the documented rule were implemented then
`--tty` would flip audience mode as a side effect (pretending to be a TTY would switch JSONL back to
human prose), which is a much bigger behavior change than a styling override.

IMPLEMENTATION NOTES (cheap parts first):
1. Add the missing `parents=[common]` to the 9 nested driver subparsers. Purely mechanical; closes GAP 1
   and makes `--no-color` universal.
2. Add `--color` to `common` as the mutually exclusive twin of `--no-color`; thread it into the
   `Term(color=...)` construction (`cli.py:8772` already does the `no_color` half) and into
   `select_output`s color resolution (`result_types.py:157-160`). `should_color` needs a parameter or an
   explicit override argument so a flag can beat env detection without setting `os.environ`.
3. `--tty` per the ruled option. If prompting is included, the 15 `sys.stdin.isatty()` sites should NOT
   each grow a flag check: introduce ONE resolver (e.g. `term.is_interactive(args)`) and route them
   through it, exactly as `git_commit_helper._is_interactive` (`:282-294`) already allows an explicit
   override. Otherwise the override will be applied inconsistently and the fail-safe will hold in some
   paths and not others.
4. Precedence must be written down in `docs/cli-output-contract.md` (which already owns this contract at
   `:18-34`) and enforced by tests: flag beats env beats detection. `--no-color` with `--color` is a
   usage error (exit 2), not a silent winner.

WHY HIGH PRIORITY (maintainer-set): these flags are the difference between `aw` output being usable in a
capture, a log, a CI job, or a demo recording, and the current state is inconsistent per-command, which
is worse than uniformly absent because it cannot be scripted around. GAP 1 in particular is a plain
inconsistency bug hiding inside a feature request.

RELATED: `.aw/records/plans/executed/` awcliux Set (the 256-color status work that added
`STATUS_COLOR_256` and `Term.color256`) is the origin of the 256-color path this item exposes.
`docs/cli-output-contract.md` is the published contract that must be updated with any change here, and
`docs/cli-agent-protocol.md` covers the machine surface. The precedence table belongs in the existing
`tests/test_term.py` (140 lines, which ALREADY exercises `should_color` against fake TTY/pipe streams at
`:46`, `:52`, `:56`, `:60`, `:65`, i.e. the NO_COLOR/FORCE_COLOR/isatty matrix, so a flag override slots
straight into that harness) and `tests/test_output_contract.py` (119 lines, which owns the
`select_output` mode/color contract). Also present: `tests/test_term_components.py`,
`tests/test_term_severity.py`. A parser-walk test asserting the trio is present on EVERY non-hidden
subcommand (nested included) would have caught GAP 1 and should be added, since a per-command spot check
demonstrably did not.
