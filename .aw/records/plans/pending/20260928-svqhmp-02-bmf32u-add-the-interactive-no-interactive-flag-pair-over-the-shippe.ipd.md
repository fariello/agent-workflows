# IPD: Add the --interactive/--no-interactive flag pair over the shipped resolver

- Date: 2026-09-28
- Kind: child
- Concern: An operator can control the PRESENTATION axis from the command line (`--color`/`--no-color`, shipped by `yaxr4i`) but has no equivalent control of the INTERACTIVITY axis. The only ways to say "do not prompt" today are `AW_NONINTERACTIVE`/`CI`, which are ENVIRONMENT variables and therefore INHERITED by every nested `aw` invocation this package spawns, and per-command `--yes`, which is hand-registered 23 times across 22 distinct parser objects and means "approve the mutation" rather than "there is nobody here to ask". There is no way to say "there IS somebody here" either, which matters because the suite's own `tests/__init__.py` reopens stdin on `/dev/null`, and four `cli.py` sites carry an `isinstance(sys.stdin, io.StringIO)` hack precisely because forcing interactivity has no supported spelling. Measured at HEAD `3ef0c74e`: `--interactive`, `--no-interactive`, `--non-interactive`, `--tty` and `--no-tty` are declared on ZERO of 283 subcommands.
- Scope: Add the interactivity flag pair as the operator surface over the resolver Order 1 ships, in ONE place, and prove it reaches every command including the leaves whose argv is forwarded verbatim. IN: the mutually exclusive flag pair on the shared parent, its pre-parse consumption for the forwarded leaves, publication into the resolver's process-wide override, the entry-point restore that stops it leaking across in-process invocations, the parser-walk uniformity guard, and the published contract. OUT: the interactivity resolver itself and any reconciliation of the divergent predicates, which are Order 1's whole job; and any change to what a prompt ASKS or to `--yes` semantics.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/term.py, docs/cli-output-contract.md, tests/test_flag_surface_uniformity.py, tests/test_interactivity_resolver.py, tests/test_term.py
- Item-Dependencies: executed:da9n1s
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: svqhmp
- Set: svqhmp
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: bmf32u

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `svqhmp` alongside Order 1 (`da9n1s`). GATE NOTE: item `svqhmp` carries NO `- Blocks-Release:`, so this plan inherits none.
  THIS PLAN IS GATED ON ORDER 1 AND THE GATE IS THE ITEM'S OWN REQUIREMENT, not sequencing preference. The item requires the flag be "routed through ONE resolver that every call site already consults" and says a per-site check across ~57 sites "is explicitly the wrong shape and is how the two axes drift apart". A flag added before the resolver exists would be silently inert at whichever of the 22 `cli.py` sites was missed, which is the exact per-command inconsistency `yaxr4i` existed to remove. Hence `- Item-Dependencies: executed:da9n1s`.
  THE MECHANISM IS ALREADY PROVEN IN THIS REPOSITORY AND MUST NOT BE RE-DERIVED, WHICH IS WHY THIS PLAN IS SMALL. `yaxr4i` discovered at EXECUTION that its own stated mechanism was wrong: declaring a flag on the shared parent makes the parser WALK see it while leaving the command BROKEN, because 28 forwarded leaves have their argv intercepted in `cli._dispatch` and handed to another program's parser BEFORE `parse_args` runs. Its recorded measurement was that `aw oc run --no-color status` still exited 2 with `runipd: error: unrecognized arguments: --no-color`. The fix that worked is CONSUMPTION in `_dispatch` (`_consume_presentation_flags`) plus a process-wide publish. E-02 copies that shape deliberately; an executor who reaches for `parents=[...]` alone will reproduce a solved bug.
  THE NAME QUESTION THE ITEM RESERVES FOR A MAINTAINER IS ALREADY ANSWERED IN A NORMATIVE PUBLISHED DOCUMENT, and that is worth stating plainly because it changes what this plan asks of a human. The item's closing line asks "whether `--tty` should exist as a name at all, given that two separate flags are the safe construction". `docs/cli-output-contract.md` section 9.1 answers both halves already: "No `--tty` flag exists, deliberately", plus requirement 1, "Two axes, never one flag ... an `--interactive/--no-interactive` pair". That text shipped in commit `67c15b2f` as executed plan `yaxr4i` E-06, human-approved 2026-09-13. So OQ-01 was authored BLOCKING, then RESOLVED from that evidence rather than sent back to the maintainer, because re-asking a question the repository answers normatively spends a round trip on a settled decision. The maintainer may still overrule at approval, at a cost of one flag string; OQ-01 records the full evidence so that is a one-line call.
  ONE GUARD THIS PLAN NEEDS NO LONGER EXISTS. `yaxr4i` called `tests/test_flag_surface_uniformity.py` "the durable deliverable" because the color flag gap had regrown four measurements running (18 of 175, then 25 of 219, then 25 of 219, then 29 of 229). Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) DELETED that file, and approved spec `uonrjg` still cites it by name. E-04 restores the walk covering BOTH axes; see OQ-02 for the file-placement question and F-05 for the dangling spec citation, which this plan does not fix.

## Goal

Give an operator one supported way to say "there is nobody here to answer" or "there is", per invocation rather than per environment, working identically on every command including the long-running driver commands. The payoff is that an unattended run can be declared unattended without exporting a variable its children inherit, and a scripted invocation stops depending on which command it happens to be calling.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the flag surface

- [ ] E-01 Declare the flag pair ONCE, as a mutually exclusive group on the shared `add_help=False` parent parser inside `cli._build_parser`, so every subcommand inherits it by construction. USE THE NAMES OQ-01 RULES, namely `--interactive` and `--no-interactive` with no `--tty` spelling; that is what `docs/cli-output-contract.md` section 9.1 already publishes, so this item is mechanical. Put it on the parent that the FORWARDED leaves also inherit (the one carrying `--color`/`--no-color`) rather than the one adding `--agent`/`--json`: the existing comment there records exactly why the two parents differ in reach, namely that `aw` can honor a flag it CONSUMES itself but must not advertise a mode it never renders. Interactivity is a flag `aw` consumes itself, so it belongs with the presentation pair.
  MUTUAL EXCLUSION MUST BE STRUCTURAL, VIA argparse's OWN GROUP, not hand-checked, and passing both must be a usage error with exit 2 rather than a silent winner. `yaxr4i` OQ-02 settled this for the color pair with the reasoning to reuse: a last-flag-wins rule makes a scripted invocation's behavior depend on argument ORDER. That plan also VERIFIED that a group declared on an `add_help=False` parent propagates through `parents=[...]` and through the parent-of-parent chain used here, so the mechanism needs no re-derivation.
  RE-CHECK FOR A NAME COLLISION AT EXECUTION rather than trusting this plan. `_AwArgumentParser` sets `conflict_handler="resolve"` on EVERY parser, so adding a flag a target parser already declares SILENTLY REPLACES the definition instead of erroring; `yaxr4i` recorded that hazard as its F-14 and it is still live. MEASURED at HEAD `3ef0c74e`: all five candidate spellings are declared on ZERO of 283 subcommands, so no collision exists today.
  - Depends on: none
  - Expected outcome: the pair is declared once on the shared parent and appears in `--help` for a parsed subcommand; passing both exits 2 with argparse's own usage error; the collision re-check is recorded.
  - Execution state: pending

- [ ] E-02 CONSUME the pair in `cli._dispatch` BEFORE every verbatim-forwarding interception, mirroring `_consume_presentation_flags`, because declaration alone provably does not work for the forwarded leaves. This is the load-bearing half and the reason this plan is not one item: 28 of 283 subcommands are host-driver leaves (`oc`/`opencode`/`agy`/`antigravity` run, review, integrate, sessions, view, exec, plus `run as` and `run ipd`) whose argv `_dispatch` hands to another program's parser before the top-level `parse_args` ever runs.
  REUSE THE EXISTING FUNCTION'S PROVEN SEMANTICS RATHER THAN INVENTING SECOND ONES, and prefer extending it over writing a twin: tokens after a bare `--` are LEFT ALONE (`--` means the rest is data, and `aw oc run -- as` is the documented way to pass a literal selector); `--flag=1` spellings are NOT recognized because `store_true` makes argparse reject them and the two surfaces must not disagree; and both-flags-seen is signalled so `_dispatch` can render the SAME exit-2 refusal the argparse group gives, since the group never runs on a forwarded path.
  CHECK FOR A DOWNSTREAM COLLISION BEFORE CONSUMING, because stripping a token the host driver owns would STEAL a downstream option. The existing comment records exactly this trap for `--agent`, which on `oc run start` is an OpenCode AGENT NAME rather than a machine-output flag, and is therefore deliberately NOT consumed. MEASURED at HEAD `3ef0c74e`: neither `oc_runipd` nor `agy_runipd` declares any `--interactive`-family flag (`agy` declares `--no-dangerously-skip-permissions`, a different concept). Re-verify at execution.
  - Depends on: E-01
  - Expected outcome: the flags work on a forwarded leaf (no `unrecognized arguments`), tokens after `--` survive untouched, an unrelated flag is never consumed, both-flags exits 2 on the forwarded path with the same message as the parsed path, and the no-downstream-collision check is recorded.
  - Execution state: pending

- [ ] E-03 PUBLISH the parsed decision into the resolver's process-wide override and RESTORE it in `cli.main`'s `finally`, which is a correctness requirement rather than tidiness. Set it UNCONDITIONALLY, including to `None`, so an invocation passing no flag RESETS a previous in-process invocation's value instead of inheriting it; the color path documents this and the test suite is exactly the long-lived process that needs it.
  THE LEAK THIS PREVENTS WAS MEASURED, ON THE COLOR FLAG, AND IT PRESENTED AS A MOVING-TARGET FLAKE. `cli.main`'s docstring records that `cli.main(["--no-color", "check", "--help"])` raises `SystemExit` from inside argparse part-way through `_dispatch`, leaving the override set for the remainder of the process, so `should_color` answered False for every later caller; under `pytest-xdist` whichever detection test was scheduled next failed, and four runs in six passed by luck. Restore the value the call INHERITED rather than `None`, because a caller that legitimately set an override around a block of work must still see it after a nested `aw` invocation returns.
  AN INTERACTIVITY LEAK IS WORSE THAN A COLOR LEAK, which is why this is its own item: a stuck `--no-interactive` silently converts every later prompt in that process into a refusal, and a stuck `--interactive` converts an unattended path into one that may block. Both are failures the environment-variable route cannot produce, so this item is the price of not using an environment variable.
  - Depends on: E-02
  - Expected outcome: the flag reaches every call site through the resolver with no per-site check; a flagless invocation resets the override; an early-exit path (`--help`, a usage error, a raising verb) does not leave it set, proven by asserting the value after each.
  - Execution state: pending

### Task group 2: guard it and publish it

- [ ] E-04 RESTORE THE PARSER-WALK UNIFORMITY GUARD, covering BOTH axes, and assert the two flag CATEGORIES separately. Deleted by commit `19313eed`; recover the prior implementation from git history rather than reinventing it, since it was written against this exact parser tree and its walk is known to reproduce the real counts. Its shape: recurse `parser._actions`, descend every `argparse._SubParsersAction.choices`, and test membership via `any(flag in (a.option_strings or []) for a in sub._actions)`.
  KEEP ITS TWO CLOSED NAMED SETS, both load-bearing and neither a predicate. `EXEMPT_SUBCOMMANDS` held only `__complete`, the hidden completion verb; `FORWARDED_SUBCOMMANDS` held the leaves that ACCEPT the flags but must not DECLARE them, and `yaxr4i` recorded why a single exemption list was wrong for them. A predicate like "skip anything hidden" silently absorbs the next command, which is the regrowth the guard exists to stop.
  ASSERT A LOWER BOUND ON THE SUBCOMMAND COUNT, NOT AN EQUALITY, and here is the evidence that matters: the gap regrew at every single measurement (18 of 175, 25 of 219, 25 of 219, 29 of 229 at `yaxr4i`'s execution), and the tree is 283 today. An equality assertion on a growing tree is a test that fails on unrelated work.
  MUTATION-CHECK THE GUARD: add a fake flagless subcommand outside both sets, show the test FAILS and NAMES it, revert. A guard that cannot fail proves nothing.
  - Depends on: E-03
  - Expected outcome: one walk asserting both axes on every non-hidden subcommand with the two closed named sets intact, a lower-bound count, and the mutation demonstrated and reverted.
  - Execution state: pending

- [ ] E-05 PROVE THE TWO AXES STAY SEPARATE, which is the item's central safety requirement and the reason the backlog item exists rather than a single `--tty` boolean being added. The item's words: a single undifferentiated boolean "would silently re-enable prompting while the operator was only asking about color, weakening a real fail-safe". Assert the independence as a 2x2 MATRIX over both flag pairs, not as prose: `--color` must not change the interactivity answer, `--no-color` must not, `--interactive` must not change `should_color`'s answer, and `--no-interactive` must not.
  ASSERT THE FAIL-SAFE DIRECTLY, NOT BY IMPLICATION. With `--no-interactive` on a real TTY, `cli._confirm` without `assume_yes` must still DECLINE and warn naming `--yes`, and the four hardened sites must still refuse. This is the property the whole Set exists to protect and it deserves its own assertion rather than being inferred from the resolver's unit tests.
  - Depends on: E-04
  - Expected outcome: a passing 2x2 independence matrix over both flag pairs, plus a direct assertion that `--no-interactive` on a TTY preserves the decline-and-warn fail-safe at `_confirm` and refusal at the hardened sites.
  - Execution state: pending

- [ ] E-06 PUBLISH the flag in `docs/cli-output-contract.md`, beside section 1.1's color precedence table and the interactivity rungs Order 1 adds, with a precedence ladder in the same flag-beats-env-beats-detection shape: flag > `AW_NONINTERACTIVE`/`CI` > stdin and output-stream detection. State that the pair is mutually exclusive and that passing both is exit 2.
  UPDATE SECTION 9.1 FROM CONSTRAINT TO FULFILMENT. It currently reads as a constraint on UNWRITTEN work ("No `--tty` flag exists, deliberately", then "If both are wanted, they are separate flags ... an `--interactive/--no-interactive` pair"). Once this plan ships, that pair EXISTS, so leaving the section in the future tense would republish a stale constraint as normative. PRESERVE the two-axis prohibition and the `--tty` ruling themselves: what changes is that the recommendation became the implementation, not the analysis. Record that the pair now ships, and keep the statement that no `--tty` spelling exists, since this plan adds none.
  - Depends on: E-05
  - Expected outcome: the published contract documents the pair, its precedence ladder and its exit-2 mutual exclusion; section 9.1 reads as fulfilled rather than pending, while keeping its two-axis prohibition and its no-`--tty` ruling intact.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE COLOR PAIR IS THE TEMPLATE AT EVERY LEVEL and copying it is the point: a mutually exclusive group on an `add_help=False` parent, pre-parse consumption in `_dispatch` for the forwarded leaves, one reader of the flag pair off the namespace (`term.color_override`), a process-wide override consulted by the resolver, and an entry-point `finally` restore.
- THE TWO NESTED PARENTS HAVE DIFFERENT REACH ON PURPOSE. `presentation` carries the styling pair and is inherited by every subcommand INCLUDING the forwarded leaves, because `aw` consumes those tokens itself; `common` adds `--agent`/`--json` and is deliberately withheld from the forwarded leaves. The comment records that a downstream `--agent` on `oc run start` is an OpenCode agent NAME, so declaring it would advertise a flag whose meaning differs from the one applied.
- DECLARATION WITHOUT CONSUMPTION IS A MEASURED FALSE GREEN. `yaxr4i` recorded that `parents=[common]` on `oc run` made the parser walk report the flag present while `aw oc run --no-color status` still exited 2. Its own review had hardened the wrong mechanism to "NINE registration edits"; execution found the mechanism itself wrong. That is the single most important convention here.
- BOTH-FLAGS REFUSAL NEEDS TWO IMPLEMENTATIONS FOR ONE BEHAVIOR, because the argparse group never runs on a forwarded path. The color pair renders a message deliberately matching argparse's own wording so the two surfaces read identically.
- `--yes` IS NOT AN INTERACTIVITY FLAG and must not be conflated with one: it is hand-registered 23 times on 22 distinct parser objects with no shared helper, and `cli.py` records elsewhere that `--yes` is "a broad preauthorization for expected mutations", explicitly NOT consent. So `--no-interactive` and `--yes` are orthogonal: the first says nobody is here, the second pre-answers.
- THE SUITE NEUTRALIZES STDIN GLOBALLY (`tests/__init__.py` reopens it on `/dev/null`, with a win32 `_NotATty` wrapper), recording a measured 40+ minute real-terminal hang. A test asserting the INTERACTIVE branch must therefore force it, which is precisely what this flag and the resolver's override make clean.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | NO NAME COLLIDES, so the ruled spelling is mechanically available: walking the built parser tree finds `--interactive`, `--no-interactive`, `--non-interactive`, `--tty` and `--no-tty` on ZERO of 283 subcommands. | parser-tree walk at HEAD `3ef0c74e` |
| F-02 | TWO OF THOSE SPELLINGS DO APPEAR IN THE PACKAGE, but only inside command lines built for THIRD-PARTY hosts: `host_capability_registry` appends `--non-interactive` to a host command template and `benchmark_runners` passes `--no-interactive` to `kiro-cli`. Neither is an `aw` flag, but a reviewer grepping the tree will hit them, and reusing `--non-interactive` as `aw`'s own spelling would read as the same concept as the host one. | `rg -n` for each spelling at HEAD `3ef0c74e` |
| F-03 | THE FORWARDED-LEAF PROBLEM IS REAL AND SIZED: 28 of 283 subcommands accept the color flags WITHOUT declaring them, because `_dispatch` intercepts their argv first; `__complete` is the only legitimately flagless one. So E-02 is not defensive, it is the majority of the work for exactly those commands. | parser-tree walk: `--no-color` missing on 29 of 283; `cli._dispatch`'s interception blocks and `_consume_presentation_flags` |
| F-04 | NO DOWNSTREAM HOST DRIVER DECLARES AN `--interactive`-FAMILY FLAG, so consuming the pair steals no downstream option: neither `oc_runipd` nor `agy_runipd` declares one (`agy` has `--no-dangerously-skip-permissions`, a permissions concept, not an interactivity flag). | `rg -n 'add_argument\(\s*"--[a-z-]*interactive'` over the package at HEAD `3ef0c74e` |
| F-05 | THE GUARD THIS PLAN NEEDS WAS DELETED AND AN APPROVED SPEC STILL CITES IT. Commit `19313eed` removed `tests/test_flag_surface_uniformity.py` (460 lines) plus `tests/test_output_contract.py` and `tests/test_output_mode.py`; spec `uonrjg` still names `tests/test_flag_surface_uniformity.py` as a pin for the published precedence chain. E-04 restores the walk; the dangling spec citation is NOT fixed here (see Spec sync). | `git show 19313eed --stat`; `git cat-file -e main:tests/test_flag_surface_uniformity.py` fails; `rg -n test_flag_surface_uniformity .aw/records/specs/approved/` |
| F-06 | THE DELETED GUARD'S IMPLEMENTATION IS RECOVERABLE AND ALREADY HAD THE RIGHT SHAPE: `git show 19313eed^:tests/test_flag_surface_uniformity.py` contains `EXEMPT_SUBCOMMANDS`, `FORWARDED_SUBCOMMANDS`, a deep-tree walk test, a both-flags-exit-2 test on parsed AND forwarded paths, a `--` passthrough test, and an unlisted-flagless-subcommand mutation test. Restoring beats reinventing. | `git show 19313eed^:tests/test_flag_surface_uniformity.py` |
| F-07 | THE PROCESS-WIDE OVERRIDE LEAK IS A KNOWN, MEASURED TRAP WITH A KNOWN FIX, so E-03 is copying a solution rather than guessing: `cli.main` documents that a `SystemExit` from `--help` left the color override set for the rest of the process, failing whichever detection test xdist scheduled next, with four runs in six passing by luck. | `cli.main` docstring |
| F-08 | THE ENV-VAR ROUTE IS GENUINELY UNAVAILABLE, which is why a flag is the right answer rather than a convenience: `should_color`'s comment records that this package spawns nested `aw` invocations (both IPD runners, `aw ipd finalize`, the commit helper) so an environment variable is INHERITED. An inherited `AW_INTERACTIVE` would tell a child it may prompt when its stdout is a pipe, the exact wedge the hardened fences exist to prevent. | `term.should_color`'s `_COLOR_OVERRIDE` rationale comment |
| F-09 | `--yes` CANNOT SERVE AS THE INTERACTIVITY FLAG, so this is not duplicate surface: it is hand-registered 23 times across 22 parser objects with no shared helper, and `cli.py` records it as "a broad preauthorization for expected mutations", explicitly not consent. A missing `--yes` also does not mean "nobody is here". | `rg -c '"--yes"' agent_workflows/cli.py`; the `runs export`/`submit` consent comment in `cli.py` |

## Proposed changes (ordered, validatable)

1. Declare the mutually exclusive pair once on the shared parent that the forwarded leaves also inherit (E-01).
2. Consume it pre-parse in `_dispatch`, with `--` passthrough and a matching exit-2 refusal on the forwarded path (E-02).
3. Publish it into the resolver's process-wide override and restore it in `cli.main`'s `finally` (E-03).
4. Restore the parser-walk uniformity guard covering both axes, with both closed named sets and a lower-bound count (E-04).
5. Prove axis independence as a 2x2 matrix and assert the decline-and-warn fail-safe directly (E-05).
6. Publish the flag and its precedence ladder in the output contract, and move section 9.1 from constraint to fulfilment (E-06).

## Deferred / out of scope (with reason)

- THE RESOLVER ITSELF AND THE RECONCILIATION OF THE FIVE DIVERGENT PREDICATES. Order 1 (`da9n1s`) owns it and this plan is gated on it executing. CARRIER: `da9n1s`.
  - Carrier: da9n1s
- FIXING SPEC `uonrjg`'S DANGLING CITATION of the deleted `tests/test_flag_surface_uniformity.py` (F-05). E-04 restores a file at that path, which may incidentally make the citation resolve again, but whether the spec's assertion is still SATISFIED depends on OQ-02's placement decision and on what the restored file asserts. A spec amendment changes the contract every other plan is reviewed against and must be declared in `- Scope-Paths:` up front, not added at execution; the defect was created by the suite trim (`19313eed`) and is not this item's work. CARRIER: none filed; RAISED FOR THE REVIEWER as a records defect needing its own backlog item, because it will outlive this Set if nobody files it.
  - Carrier-Declined: a records defect in an approved spec created by an unrelated suite trim; naming it in this plan's scope would amend a contract this item does not own, so it is surfaced for the reviewer to file separately
- RESTORING `tests/test_output_contract.py` AND `tests/test_output_mode.py`, also deleted by `19313eed`. They own the `select_output` mode/color truth table, which this Set does not touch: the interactivity axis never reaches `select_output`. NO CARRIER NEEDED from this item; it is the suite trim's residue, not this Set's obligation.
  - Carrier-Declined: unrelated to the interactivity axis; residue of the suite trim rather than an obligation of this item
- ANY CHANGE TO `--yes` SEMANTICS OR TO THE 23 HAND-REGISTERED `--yes` DECLARATIONS. `--yes` is orthogonal (F-09) and consolidating it onto a shared helper is a separate mechanical item. NO CARRIER NEEDED: this is a decision not to widen scope, and the flags do not conflict.
  - Carrier-Declined: a decision not to widen scope onto an orthogonal flag; nothing outstanding is created
- ANY CHANGE TO WHAT A PROMPT ASKS, to its default answer, or to which sites prompt at all. This plan adds a way to OVERRIDE the answer, not new prompting behavior. NO CARRIER NEEDED.
  - Carrier-Declined: adding an override is not a change to prompt content or placement; nothing outstanding is created

## Scope check

- Over-scope: `tests/test_term.py` is in `Scope-Paths` although this plan adds no color logic. It is required: E-05's independence matrix asserts that the interactivity flags do NOT move `should_color`'s answer, and that file owns the `should_color` matrix and the `CliNeverLeaksTheColorOverrideTests` harness E-03's restore test mirrors.
- Under-scope: the flag controls only whether a prompt MAY happen, not what it asks or how it defaults. That is deliberate: the item asks for an override routed through one resolver, not a redesign of the prompts.

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, pasting the ACTUAL summary line. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`. Establish the baseline on a CLEAN tree BEFORE editing and judge on the DELTA OF FAILING NODE IDS; prove any surviving failure pre-existing by reproducing it with this work stashed.
- `python3 -m pytest tests/test_flag_surface_uniformity.py tests/test_interactivity_resolver.py tests/test_term.py tests/test_cli.py` for the focused surface.
- THE PARSER WALK re-run before and after, pasting the subcommand total and the per-flag gap counts each time.
- REAL INVOCATIONS ON THE FORWARDED LEAVES, exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`), covering at least `aw oc run`, `aw agy run`, `aw run as` and `aw run ipd` with each flag, plus a parsed command for contrast. An exit 2 from the DRIVER's own argument handling is acceptable and must be distinguished from an `unrecognized arguments` flag error by pasting the message.
- MEASUREMENT DISCIPLINE, since it changes how to reproduce this: the `aw` console script may resolve `agent_workflows` from the MAIN checkout rather than the lane, so run every invocation with `PYTHONPATH=<lane>` (or via `python3 -m agent_workflows`) and say which was used. `yaxr4i` recorded this exact trap; without it the flag appears broken because the OLD code is running.
- THE OVERRIDE-LEAK ASSERTION over early-exit paths, mirroring `tests/test_term.py`'s existing `CliNeverLeaksTheColorOverrideTests` table: after `--help`, after a usage error, and after a raising verb, the process-wide interactivity override must equal the inherited value.
- `python3 -m agent_workflows check` must not gain a diagnostic.
- `aw sanitize --agent` clean, since this plan's evidence pastes absolute lane paths in `PYTHONPATH`.

## Spec / documentation sync

`docs/cli-output-contract.md` is the PUBLISHED contract for both TTY axes and is declared in `Scope-Paths` deliberately: E-06 adds the interactivity flag's precedence ladder beside section 1.1's color table and moves section 9.1 from a constraint on unwritten work to a record of what shipped, since its "If both are wanted, they are separate flags" framing becomes stale the moment this plan lands. The section's `--tty` ruling and two-axis prohibition are PRESERVED, not rewritten: this plan implements that recommendation rather than revisiting it.

NO `.spec.md` FILE IS EDITED, AND THAT IS A JUDGEMENT THE REVIEWER SHOULD CHECK RATHER THAN AN OMISSION. Approved spec `uonrjg` governs the COLOR precedence chain and cites `tests/test_flag_surface_uniformity.py` as one of its pins; that citation dangles today because `19313eed` deleted the file (F-05). E-04 restores a file at that path, so the citation may resolve again as a side effect, but this plan does NOT claim to satisfy `uonrjg`'s assertion and does not amend it: the spec's subject is the color axis, the defect was created by an unrelated suite trim, and a spec edit changes the contract every other plan is reviewed against. IF THE REVIEWER JUDGES THE AMENDMENT IN SCOPE, `.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md` must enter `- Scope-Paths:` BEFORE approval, because both runners announce declared spec edits before a run starts and reconcile them at finalize; adding it at execution time would trip that gate.

## Open questions

### OQ-01: What are the flag names, and should `--tty` exist as a spelling at all?

- Blocking: no
- Status: resolved
- Owner: executor
- Finding: F-01, F-02
- Resolution or deferral rationale: RESOLVED FROM PUBLISHED REPOSITORY EVIDENCE, having first been authored as a blocking maintainer question. The backlog item asks for "a maintainer ruling on whether `--tty` should exist as a name at all", and the ANSWER IS ALREADY PUBLISHED AND ALREADY HUMAN-APPROVED, which is why this does not need asking again. `docs/cli-output-contract.md` section 9.1 is a NORMATIVE document and it states both halves: "No `--tty` flag exists, deliberately", and requirement 1, "Two axes, never one flag. If both are wanted, they are separate flags (for example `--color/--no-color`, which already exist, and an `--interactive/--no-interactive` pair)." That text shipped in commit `67c15b2f` as executed plan `yaxr4i` E-06, which carries `- Status: executed` and was human-approved on 2026-09-13. So the RULING IS: `--interactive`/`--no-interactive`, and NO `--tty` spelling.
  THE SUPPORTING EVIDENCE, since the doc gives the choice but not all of the reasoning: (a) no spelling collides, so all were mechanically available and the choice was genuinely free (F-01); (b) `--non-interactive` is already used in this package for THIRD-PARTY host command lines (`host_capability_registry`, `benchmark_runners`), so reusing it as `aw`'s own flag invites a reader to conflate the two (F-02); and (c) `--tty` names a MECHANISM (a device) while the pair names INTENTIONS, and a name spanning two axes is exactly the conflation section 9.1 exists to prevent.
  WHAT IS NOT DECIDED HERE, stated so the reviewer can see the boundary: whether `--tty` should later exist as an ALIAS for one axis alone. Section 9.1 forbids only the undifferentiated BOOLEAN, so an alias is not foreclosed by the analysis; it is simply not proposed, and the status quo the doc publishes is that no such flag exists. Adding one is a separate proposal needing its own decision.
  A MAINTAINER MAY STILL OVERRULE THIS AT APPROVAL, and the cost of doing so is one line: E-01 says to use the name this question rules, so a different ruling changes the flag string and nothing structural. It is recorded as non-blocking rather than blocking because the repository genuinely answers it in a normative published contract, and holding the plan to re-ask a settled question would spend a maintainer round trip on a decision already made and documented.

### OQ-02: Should the restored uniformity guard live at the old path, or somewhere that names both axes?

- Blocking: no
- Status: open
- Owner: executor
- Finding: F-05, F-06
- Resolution or deferral rationale: RESOLVABLE AT EXECUTION and recorded so the choice is deliberate. The old path `tests/test_flag_surface_uniformity.py` is cited BY NAME in approved spec `uonrjg`, which is a strong argument for restoring it there: a citation that resolves is worth more than a tidier name, and this plan does not amend specs (see Spec sync). The RECOMMENDED approach is therefore to restore the old path and widen its contents to both axes, rather than creating a new file and leaving the spec's citation dangling. Not blocking because either placement satisfies the plan's property; the reason to record it is that a new path would silently leave a second records defect behind.
- Carrier-Declined: DISCHARGED BY THIS PLAN'S OWN EXECUTION, since E-04 must write the guard SOMEWHERE and V-04 requires the committed file be evidenced, so the placement is necessarily decided in-tree before this plan could reach `executed`. NOTE THE DISTINCT OBLIGATION THAT IS **NOT** DECLINED HERE: spec `uonrjg`'s dangling citation of the deleted file (F-05) is a separate records defect, and the Deferred section surfaces it for the reviewer to file rather than pretending this question carries it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the committed declaration showing ONE mutually exclusive group on the shared parent, and name which parent and why. Paste `aw <a parsed command> --help` showing both flags rendered. Paste the UNPIPED exit code and message for passing both on a parsed command (expect 2, argparse's own group wording). Paste the collision re-check proving no target parser already declared either spelling, given `conflict_handler="resolve"` would otherwise silently replace a definition.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste at least four real FORWARDED-leaf invocations with each flag (`aw oc run`, `aw agy run`, `aw run as`, `aw run ipd`), exit codes measured UNPIPED, and show NONE emits `unrecognized arguments`; where the exit is 2, paste the message proving it is the driver's own argument handling rather than a flag error. Paste the BEFORE measurement showing the same invocation failing with `unrecognized arguments` prior to the change. Paste a `--` passthrough case proving a flag-shaped token after `--` survives into the forwarded argv, an unrelated-flag case proving nothing else is consumed, and the both-flags case on a forwarded leaf exiting 2 with the SAME message as the parsed path. State which interpreter/`PYTHONPATH` was used.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a test showing the flag reaching a call site that never sees the parsed namespace, proving the process-wide publish works rather than a per-site check. Paste the early-exit table: for `--help`, a usage error, and a raising verb, the override equals the inherited value after `cli.main` returns or raises. Paste the flagless-invocation case showing the override RESET to the inherited value rather than retaining a previous invocation's. Paste the committed `finally` block.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the walk's output BEFORE and AFTER, with the subcommand total and per-flag gap counts each time, and confirm the only unexplained gap is empty. Paste both closed named sets as committed and confirm each is a frozen collection, not a predicate. Paste the count assertion showing it is a LOWER BOUND. Then paste the MUTATION: the injected flagless subcommand, the FAILING output naming it, and the revert restoring green.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the 2x2 independence matrix as executed: `--color` and `--no-color` each shown NOT to change the interactivity answer, and `--interactive` and `--no-interactive` each shown NOT to change `should_color`'s answer. Paste the fail-safe assertion: with `--no-interactive` and a forced-TTY stdin, `cli._confirm` without `assume_yes` returns False AND emits the warn naming `--yes`, and each of the four hardened sites refuses. Paste the converse too (`--interactive` with a non-TTY stdin) and state plainly which sites then prompt, since that is the direction that can wedge.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the committed diff region of `docs/cli-output-contract.md` showing the interactivity precedence ladder and the exit-2 mutual exclusion. Quote section 9.1 as committed, showing the two-axis prohibition and the no-`--tty` ruling PRESERVED, and confirm no text still describes the `--interactive`/`--no-interactive` pair as unwritten or merely recommended. Confirm by grep that the section's stale counts are gone.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. An operator gains a per-invocation way to say "nobody is here to answer" or "somebody is", working identically on all 283 subcommands including the 28 forwarded driver leaves, replacing an inherited environment variable with a flag that cannot leak into a child process. Nothing about what a prompt asks, when it appears, or what `--yes` means changes. The Set's safety property is asserted directly rather than assumed: the two axes are proven independent, and `--no-interactive` on a real TTY still leaves `cli._confirm` declining with its warn naming `--yes`. Graduates backlog `svqhmp` (with Order 1) and inherits NO release gate, because the item carries none.

THE FLAG NAMES ARE NOT GUESSED AND ARE NOT ASKED AGAIN. `--interactive`/`--no-interactive` with NO `--tty` spelling is what `docs/cli-output-contract.md` section 9.1 already publishes as normative, shipped by executed plan `yaxr4i` and human-approved 2026-09-13, so OQ-01 is `resolved` from that evidence rather than held open for a round trip on a settled question (the full reasoning is in OQ-01, and overruling it costs one flag string). THIS PLAN STILL CANNOT RUN FIRST: `- Item-Dependencies: executed:da9n1s` gates it, because the resolver must exist and every call site must already consult it, or the flag is silently inert wherever it was missed.

Execute only after explicit human approval (`Status: approved`) and after `da9n1s` is executed. Per the repository execution contract: commit only the paths named in `- Scope-Paths:` through `aw commit`, never `git add -A`; never push; paste ACTUAL test output rather than claiming success; and leave the terminal lifecycle transition to the runner, which owns begin/finalize for a managed lane. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries pasted evidence.
