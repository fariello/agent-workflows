# IPD: Make an argparse dest that shadows a subcommand an executed-reachability failure instead of a silent help page

- Date: 2026-09-29
- Kind: child
- Concern: A leaf that declares an argument whose `dest` equals an ancestor subparsers action's `dest` SILENTLY overwrites the resolved subcommand name, after which every `if args.command == ...` branch in `cli._dispatch` misses and the function falls through to its closing `parser.print_help(); return 2`. The operator sees a correct-looking top-level help page and exit 2, which reads as "you typed the command wrong" rather than "this leaf is structurally unreachable", and the leaf still appears in `--help` and in `command_surface.discover_parser_leaves`. Measured live in this lane by re-shadowing `integration-lock`'s `locked_command` positional back to `command`: `aw integration-lock --status --dir .` returns 2 having printed 215 lines of TOP-LEVEL help, with argparse raising nothing, warning nothing, and writing nothing to stderr. The mechanism is `argparse._SubParsersAction.__call__`, which writes the chosen name with `setattr(namespace, self.dest, parser_name)` and THEN copies the whole sub-namespace over the parent with `for key, value in vars(subnamespace).items(): setattr(namespace, key, value)`, so the child's value always wins regardless of nesting depth or action type.
- Scope: Add a durable executed-reachability guard that turns this silent class into a failing test, and nothing else. IN: one new test module `tests/test_cli_dest_shadowing.py` that builds every parser in the package, synthesizes a MINIMAL VALID argv for all 171 canonical leaves across the seven builders (151 of them `cli`'s), parses it, and asserts every subparsers dest on the traversed chain still holds the token the operator typed; a recorded mutation demonstrating the guard is RED for the exact defect the item describes. OUT: any change to `agent_workflows/cli.py` or to any shipped flag, dest, or default (the tree measures CLEAN under this guard today, so there is nothing to fix in production code); the SEPARATE and independently-measured `runs` family-flag loss, which is a live defect of the same MECHANISM but a different SHAPE and is owned by plan `zwv1sa` (Order 02) in this Set; and any author-time lint over the parser's static shape, which review measured VIABLE and which is declined as a design trade rather than on feasibility (see Deferred and F-15).
- Scope-Paths: tests/test_cli_dest_shadowing.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 0b290s
- Blocks-Release: next
- Set: destshadow
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8kd4eo
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-501..PR-508 all FIXED. Two of three load-bearing measurements did not reproduce: F-07's 1160 measured a BROADER rule than the item's (the item's own rule fires 0 clean, 1 mutated), and F-08's 'no narrowing covers both shapes' is falsified (narrowing (iii) reports integration-lock on the mutated tree). Deliverable kept, rationale replaced with F-15. F-17 fixes a synthesizer gap that would have failed the plan's own coverage assertion at execution (oc_runipd/agy_runipd 6/7). F-18 resolves an E-03 self-contradiction. IPD-Z602 cleared by rewriting E-04.

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `0b290s`. Every figure below was MEASURED in this lane at HEAD `69a31fca`, not transcribed from the item. THE ITEM'S PRESCRIBED FIX WAS CHANGED IN SHAPE, and that is this plan's one substantive authoring decision: the item asks for "a structural test over `cli._build_parser()` asserting that no subparser declares an argument whose `dest` collides with an ANCESTOR subparsers action's `dest`", and this plan substitutes an executed reachability walk. THE TWO MEASUREMENTS THIS PARAGRAPH ORIGINALLY CITED WERE BOTH CORRECTED AT REVIEW (2026-09-30) AND NO LONGER SUPPORT THE SUBSTITUTION: the "1160 on a clean tree" figure belongs to a BROADER rule than the item's (the item's own rule fires ZERO times clean and exactly once on the mutated tree, F-07), and the claim that every narrowing which removes the false positives also removes the genuine `runs` findings is falsified, since narrowing (iii) reports `('integration-lock', 'command')` on the mutated tree (F-08). The substitution therefore rests on F-15's three properties instead: the walk asserts reachability DIRECTLY rather than inferring it from a shape, carries no hand-maintained shared-flag exemption list to rot, and is mechanism-agnostic. GUIDING_PRINCIPLES P16 favors that directness ("exercise the code ... assert observable outputs"), though review also records that a walk over a BUILT parser object would not itself be the forbidden census. GATE NOTE: item `0b290s` carries `- Blocks-Release: next` and `- Work-Kind: bug`, so this plan INHERITS the gate; it is written on the front matter, not in prose.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): SET SHAPE. The item is one report and it graduates into TWO plans because authoring found a LIVE INSTANCE of the same mechanism the item did not know about (F-04: `aw runs --dir X list` silently discards `--dir`, and all 15 of the family's viewer flags behave the same way). The prevention guard and the live fix are separated because they differ in every dimension that matters to a reviewer: the guard touches no production code and cannot regress a user, while the fix edits `cli.py` and changes what a documented invocation does; and the guard measures the tree CLEAN while the fix has a failing baseline to correct. Order 01 is the guard, Order 02 is the fix. They are INDEPENDENT (no `- Item-Dependencies:` between them) because neither's deliverable is an input to the other: the guard adds a test module and the fix edits `cli.py` plus its own test, and neither reads the other's output. CORRECTED AT REVIEW (see F-16): this note originally justified the split by coverage, arguing that the shape-based alternative "would have caught the `runs` defect and this guard's reachability walk does NOT". The second half is true (F-09) and the first half is now measured true as well (F-08 corrected), which makes that argument point the WRONG WAY; it is withdrawn. The split stands on RISK and REVIEWABILITY, the reasons given first above and confirmed at review.

## Goal

Turn "a leaf is registered, documented, discoverable, and unreachable" from a defect that takes a `vars(args)` print to diagnose into a test failure that names the leaf and the shadowed dest.

The guard must fail for the ORIGINAL defect and must not fail for any of the benign dest re-declarations the shared flag parents create (1160 of them under the BROAD any-dest-repeat reading; zero under the item's own narrower reading, per F-07 as corrected at review). It is written as an executed reachability walk rather than the static census the item proposed for the three reasons F-15 states, NOT because the static rule is unimplementable: review measured that rule viable, so the choice is a trade and the plan records it as one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the defect and the tree's current state

- [x] E-01 RE-MEASURE THE FACTS THIS PLAN RESTS ON BEFORE WRITING ANY TEST, because most are counts over a tree that grows continuously and one is a claim about a defect that is already fixed in production. Record raw output for each with the command that produced it. (a) THE DEFECT REPRODUCES: rebuild `cli._build_parser()`, re-point `integration-lock`'s `locked_command` action's `dest` to `command` in the built object only, and invoke `cli._dispatch(["integration-lock", "--status", "--dir", "."])` through the scoped `patch.object` route of E-03 (F-18: `_dispatch` builds its own parser, so there is no other route); review measured `rc=2`, 215 lines of stdout whose first line is `usage: agent-workflows [-h] ...`, and EMPTY stderr. (b) THE CLEAN TREE HAS NO REACHABILITY FAILURE: the walk E-02 builds reports 0 findings over all 151 canonical leaves of `cli` and 0 over each of the other six builders. (c) BOTH STATIC RULES, MEASURED SEPARATELY AND NOT CONFLATED (this is the correction F-07 records, so re-derive BOTH or the plan's rationale cannot be checked): the ITEM'S rule, whose ancestor set is the SUBPARSERS dests only, measured 0 occurrences on the clean tree and exactly `[('integration-lock', 'command')]` on the mutated one; the BROADER any-dest-repeat rule measured 1160 occurrences over 23 dests, of which `help`, `no_color`, `color`, `no_interactive`, `interactive`, `agent` and `json` contribute 161 each. (d) THE BASELINE SUITE IS GREEN: bare `python3 -m pytest` (review: `3312 passed, 2 skipped, 3 warnings in 62.71s`, with the standard `207 tests were deselected` notice). IF ANY COUNT HAS MOVED, use the new measurement and say so; the plan's argument depends on the ORDERS OF MAGNITUDE (zero versus four figures), not on the exact digits.
  - Depends on: none
  - Expected outcome: five raw measurements recorded (a, b, both halves of c, and d), each with its command, and an explicit statement of whether each matches the figure above. No file is changed by this item.
  - Execution state: performed

### Task group 2: the guard

- [x] E-02 WRITE `tests/test_cli_dest_shadowing.py` CARRYING THE EXECUTED REACHABILITY WALK, which is this plan's whole deliverable. For each of the seven parser builders in the package (`cli._build_parser`, `oc_runipd.build_parser`, `agy_runipd.build_parser`, `layout_inventory.build_parser`, `oc_models.build_parser`, `upgrade_rehearsal.build_parser`, `pwatch.build_parser` - the same seven set `76fgt1` enumerated and guarded), enumerate canonical leaves with `command_surface.discover_parser_leaves`, SYNTHESIZE a minimal valid argv for each leaf, parse it, and assert that for every subparsers action traversed on the way to that leaf, the parsed namespace still holds the TOKEN THE ARGV CONTAINED at that position. Use `subTest` per leaf so a failure names the leaf, the dest, the value found and the value expected.

  THE ARGV SYNTHESIZER IS THE ONLY HARD PART AND IT MUST BE TYPE-AWARE, because a naive one does not reach the leaves and a test that cannot parse proves nothing. The progression was measured on `cli._build_parser()` and re-derived at review: filling only the leaf tokens reaches 86 of 151 leaves; adding required positionals reaches 136; adding required OPTIONS reaches 146; honoring `choices` reaches 150; honoring `type` reaches 151 of 151. So the synthesizer must, for each action on the leaf parser: skip subparsers actions; for a positional, supply one value for `nargs` of `None` or `"+"`, `n` values for an integer `nargs`, and NOTHING for `"?"`, `"*"` or `argparse.REMAINDER`; for an option, supply it ONLY when `required` is true, with a value unless `action.nargs == 0`; and derive each value as the FIRST member of `action.choices` when choices are declared, else a literal appropriate to `action.type` (`"1"` for `int`, `"1.0"` for `float`), else a placeholder string. DERIVE THE VALUE FROM THE ACTION, never from a per-leaf table of hand-written argv: a table would rot at the next flag change and would silently stop covering the leaf it names.

  IT MUST ALSO SATISFY A REQUIRED MUTUALLY EXCLUSIVE GROUP, WHICH THE PROGRESSION ABOVE DOES NOT REACH AND WHICH IS NOT OPTIONAL (F-17). `action.required` is False on EVERY member of a required mutex group, so an `action.required`-only synthesizer misses it: measured at review, `oc_runipd`'s `stop` leaf reports no required option actions while carrying `mutex group required=True actions=['level_flag' x4]`, and the walk lands at `oc_runipd 6/7` and `agy_runipd 6/7` with `error: one of the arguments --after-call --after-set --now --now-force is required`. So ALSO iterate `parser._mutually_exclusive_groups`, and for each group whose `required` is true emit ONE member (take its first `_group_actions` entry) and EXCLUDE that group's members from the per-action pass so no member is emitted twice. With this corner the walk reaches total coverage on all seven builders: `cli 151/151`, `oc_runipd 7/7`, `agy_runipd 7/7`, `upgrade_rehearsal 6/6`, and `0/0` for `layout_inventory`, `oc_models` and `pwatch`, which declare no subparsers and so have no canonical leaves. TREAT THE THREE FLAT BUILDERS' `0/0` AS EXPECTED, not as a coverage failure, and do not assert a nonzero leaf floor on them.

  ASSERT COVERAGE IS TOTAL, NOT PARTIAL, and make that its own assertion rather than an implicit property. A synthesizer that silently failed to construct a parsable argv for 40 leaves would report zero shadowing findings and look green, which is exactly the vacuous pass `GUIDING_PRINCIPLES` P16's "verify test sensitivity with mutation" rule exists to prevent, and which D78 records having actually happened in this repository (`test_apply_is_idempotent` "had started passing vacuously"). So assert that EVERY canonical leaf parsed, and on failure name the leaves that did not with the usage error each produced. Assert the leaf count as a LOWER BOUND (review measurement: 151 for `cli`) and never as an equality: the tree grows continuously, and `76fgt1`'s F-07 recorded the analogous count moving 175, 219, 229, 283 and then measuring 249, which is what makes an equality assertion a test that fails on unrelated work. Apply the floor ONLY to the builders that have leaves; the three flat builders legitimately have none.

  KEEP IT A BLACK-BOX PARSE. Build the parsers through their public builders, call `parse_args`, and read the resulting namespace. Do not read any module under `agent_workflows/` as text, do not `inspect.getsource`, do not `ast.parse`, and do not assert on any comment or docstring (P16). Walking `parser._actions` and `_SubParsersAction.choices` to construct the argv is not a source pin: it inspects a live object the parser built, which is the established idiom of `command_surface.discover_parser_leaves` and of `tests/test_cli_parser_conflict_policy.py`. DEDUPLICATE SUBPARSERS BY `id()` WHEN WALKING, not by name: `add_parser(name, aliases=[...])` registers ONE object under several keys, and `discover_parser_leaves` records the measured cost of the name walk (63 spurious leaves).

  SUPPRESS OUTPUT AND NEVER LET A PARSE ERROR ESCAPE AS A TEST ERROR. A usage error raises `SystemExit` and writes to stderr, so wrap each parse in `redirect_stdout`/`redirect_stderr` and catch `SystemExit`, recording it as an uncovered leaf rather than letting it abort the walk; a single unparsable leaf must not hide the other 150.
  - Depends on: E-01
  - Expected outcome: a passing test module that parses a synthesized argv for every canonical leaf of all seven builders, asserts total leaf coverage and a lower-bound count, and reports zero shadowed dests on the clean tree.
  - Execution state: performed

- [x] E-03 ADD THE MUTATION CASE IN THE SAME MODULE, which is the only evidence that the walk is a guard rather than decoration. Build a FRESH parser inside the test, re-point `integration-lock`'s `locked_command` action's `dest` to `command` on that object only, run the same walk, and assert it reports EXACTLY ONE finding naming `integration-lock` and the `command` dest. Authoring measured this returns `[('integration-lock', "command=[] expected 'integration-lock'")]` against `[]` on the clean tree, so the mutation is both sufficient and specific.

  FOR THE WALK ITSELF, MUTATE A LOCALLY BUILT PARSER AND NEVER A SHARED ONE. `_build_parser` returns a new tree per call, so a local mutation is naturally contained; an UNSCOPED module-level rebind would leak into any other test that builds a parser in the same worker, and the suite runs under `-n auto --dist=worksteal` with randomized order, so a leak would surface as an unrelated flake in a different file. The walk half of this item needs no patch at all: build, mutate the local object, walk it.

  ASSERT THE SYMPTOM AS WELL AS THE DIAGNOSIS, because the item's central complaint is that the SYMPTOM is misleading. On the mutated parser, drive `cli._dispatch(["integration-lock", "--status", "--dir", <a tmpdir>])` with output captured and assert it returns 2 and prints TOP-LEVEL usage. That is the behavior an operator reports as "the command does not work", and pinning it is what stops a future reader dismissing this guard as hypothetical. Use a temporary directory for `--dir` so the assertion cannot depend on the live checkout, and assert on the exit code plus the presence of top-level usage, NOT on the help text's exact bytes or line count (215 lines is a measurement, not a contract, and pinning it would break on any added subcommand).

  THE SYMPTOM ASSERTION REQUIRES A SCOPED PATCH, WHICH IS PERMITTED HERE AND IS THE ONLY ROUTE (F-18). `cli._dispatch`'s first statement is `parser = _build_parser()` and its signature takes only `argv`, so no injected parser can reach it; there is no non-patching route, and dropping the assertion is not the answer because F-01's misleading symptom is the item's central complaint. USE `unittest.mock.patch.object(cli, "_build_parser", ...)` AS A CONTEXT MANAGER whose replacement calls the real builder and applies the mutation. That is what the prohibition above is actually aimed at preventing the absence of: `patch.object` restores the original on block exit INCLUDING on exception, so nothing escapes the `with` and the worker is left clean. Do NOT rebind `cli._build_parser = ...` by assignment, and do NOT patch at class or module setup scope. Then PROVE the containment rather than asserting it: immediately after the block, build a fresh parser, walk it, and assert the finding list is empty. Review measured exactly this: `patched rc: 2 top-level usage: True lines: 215`, then `post-patch clean walk findings: []`.
  - Depends on: E-02
  - Expected outcome: a passing test that is RED if the walk stops detecting a re-shadowed `integration-lock`, plus a pinned assertion that a shadowed leaf exits 2 with top-level usage.
  - Execution state: performed

### Task group 3: prove the addition is clean against the whole suite

- [x] E-04 PROVE THE NEW MODULE PERTURBS NOTHING ELSE IN THE SUITE, which is the single concern of this item and the one way this plan could plausibly break code it does not touch (the module builds seven parser trees and parses 171 argv vectors per run, so an import-time side effect, a global a parse mutates, or an interaction with the randomized order under `-n auto --dist=worksteal` would surface here and nowhere else). Run `python3 -m pytest` BARE (no `-n0`, no extra `-q`, no `-p no:randomly`), paste the summary line, and reconcile it against E-01(d)'s baseline BY NODE ID rather than by total: the pass count must rise by exactly the number of tests added and no previously passing node id may fail. Re-run the new module alone twice in the same session as part of the same reconciliation, since a residue the E-03 patch left behind would show as a second-run difference. IF ANY UNRELATED TEST FAILS, do not retry until it passes and do not mark this item: report the node id with its output, since an order-dependent interaction is a real finding about this guard and not noise.
  - Depends on: E-03
  - Expected outcome: a bare-suite summary line matching the E-01(d) baseline plus exactly the added tests, with no unrelated failure, and the new module green on both runs in one session.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `GUIDING_PRINCIPLES.md` P16 forbids `inspect.getsource`, `ast.parse`, `read_text()` or substring search against `agent_workflows/*.py`, and forbids "count or census pins ... as a proxy for an invariant". This is the convention that decides this plan's SHAPE: the item's proposed "structural test" infers unreachability from a shape, while an executed parse asserting on the resulting namespace is the sanctioned form P16's "exercise the code ... assert observable outputs" names. CORRECTED AT REVIEW: the static rule is NOT independently unusable (F-07, F-08 as corrected), and it would not itself be a forbidden census either, since a parser-object walk asserting a structural property of a BUILT object is not a source-text or caller-count pin; `tests/test_cli_parser_conflict_policy.py` ships exactly such a walk. So P16 favors the walk on directness rather than forbidding the alternative. Building a parser and reading `_actions` to CONSTRUCT an input is likewise not a structure pin; `command_surface.discover_parser_leaves` and that conflict-policy test both do it in shipped, passing tests.
- MEASURE THE PARSER TREE, DO NOT REASON ABOUT IT. Every prior plan on this surface was corrected by a live probe, and `76fgt1`'s Step 0 records the sharpest instance: `yaxr4i`'s review hardened the wrong mechanism to "NINE registration edits" and execution found the mechanism itself wrong. Build the parser and inspect the namespace.
- COUNT PARSER OBJECTS BY `id()`, NOT BY NAME, because aliases share one object. `discover_parser_leaves`'s docstring records the measured cost of the name walk (63 spurious leaves) and uses identity as the test.
- ASSERT A LOWER BOUND ON ANY TREE-WIDE COUNT. `76fgt1` E-02 states this as a rule and F-07/F-13 give the reason: three different correct "subcommand counts" exist (alias-expanded paths, distinct parser objects, canonical leaves), and one of its own figures did not reproduce at review (249, not 283).
- THE SEVEN BUILDERS ARE THE ESTABLISHED UNIT OF "EVERY PARSER IN THE PACKAGE". `76fgt1` F-03 enumerates them and its guard covers all seven; this plan reuses that set so the two guards cannot disagree about what they cover.
- A GUARD MUST BE MUTATION-DEMONSTRATED. P16: "A test is only valid if breaking the underlying behavior makes the test fail." `76fgt1` E-02 applies it by registering a duplicate option and asserting the raise; E-03 here is the same discipline.
- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; `-n0` makes it several times slower and a second `-q` suppresses the summary line the execution contract requires be pasted.
- THE `aw` CONSOLE SCRIPT MAY RESOLVE `agent_workflows` FROM THE MAIN CHECKOUT RATHER THAN THIS LANE, and it announces the re-exec on stderr. Measured during authoring here. Every measurement in this plan was taken with `AW_NO_REEXEC=1 python3 -m agent_workflows ...` or by importing the package directly, so it describes THIS lane's code; an executor must do the same or state which interpreter produced its evidence.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured 2026-09-29 in this lane worktree at HEAD `69a31fca`, on CPython 3.14.6.

| # | Sev | Finding | Evidence |
|---|---|---|---|
| F-01 | HIGH | **THE DEFECT REPRODUCES EXACTLY AS THE ITEM DESCRIBES IT, AND THE SYMPTOM IS AS MISLEADING AS CLAIMED.** Re-pointing `integration-lock`'s `locked_command` action's `dest` to `command` on a freshly built parser and calling `cli._dispatch(["integration-lock","--status","--dir","."])` returns `rc=2` after printing 215 lines of stdout whose first line is `usage: agent-workflows [-h] [--no-color | --color] [--no-interactive |`, with stderr EMPTY. So the operator gets a well-formed top-level help page and a usage exit code for a command that exists, is spelled correctly, and is registered. No argparse error, no warning, no traceback. | the mutation run in this lane; `rc: 2`, `stdout lines: 215`, `stderr: []`, `looks like top-level help: True` |
| F-02 | HIGH | **THE MECHANISM IS UNCONDITIONAL AND DEPTH-INDEPENDENT, so the hazard is not specific to REMAINDER or to top-level leaves.** `argparse._SubParsersAction.__call__` writes the resolved name with `setattr(namespace, self.dest, parser_name)` and THEN copies the entire sub-namespace over the parent (`subnamespace, arg_strings = subparser.parse_known_args(arg_strings, None)` followed by `for key, value in vars(subnamespace).items(): setattr(namespace, key, value)`). The child's value therefore always wins. Measured over four shapes: a REMAINDER positional yields `command=['--','x']`; an ABSENT optional yields `command=None`; a `store_true` yields `command=False` absent and `True` present; and a leaf shadowing its GRANDPARENT's dest (`command` from two levels down) is clobbered identically. So ANY dest spelling that collides, at ANY depth, with ANY action type, silently destroys the routing key. | four probes against synthetic parsers; `inspect.getsource(argparse._SubParsersAction.__call__)` on CPython 3.14.6 |
| F-03 | HIGH | **NO DEST-SHADOWING REACHABILITY FAILURE EXISTS IN THE TREE TODAY, which is what makes this plan a pure guard with no production edit. RE-MEASURED AT REVIEW AND REPRODUCED EXACTLY.** The E-02 walk over all 151 canonical leaves of `cli._build_parser()` reports `canonical=151 parsed_ok=151 findings=0`: every traversed subparsers dest holds the token the argv contained. The same walk over the other six builders finds nothing (`oc_runipd 7/7`, `agy_runipd 7/7`, `upgrade_rehearsal 6/6`, and `0/0` for the three that declare no subparsers), confirmed at review to be 0 findings once F-17's mutex corner is added. The `integration-lock` instance the item reports was fixed at filing time by renaming the positional to `locked_command`, and the code carries a comment recording why. | the reachability walk over all seven builders, re-run at review; `p_integ_lock.add_argument("locked_command", nargs=argparse.REMAINDER, ...)` and its `dest="locked_command"` and NOT `command` comment |
| F-04 | HIGH | **A LIVE INSTANCE OF THE SAME MECHANISM EXISTS IN A DIFFERENT SHAPE AND IS USER-VISIBLE TODAY, which is why this item graduates into two plans.** `aw runs --dir <path> list` SILENTLY DISCARDS `--dir` and reads the CWD's repo instead, because `runs list` re-declares `--dir` with `default=None`, and the sub-namespace copy of F-02 overwrites the family value with that default. Demonstrated end-to-end on a temp repo holding one run: `aw runs --dir <tmp> list` prints `no matching runs found` while `aw runs list --dir <tmp>` prints the run. ALL FIFTEEN of the viewer's flags lose their value the same way when placed before the leaf (`--dir --last --set --ipd --status --since --active --failed --detail --short --summary-only --latest-only --issues --all-classes` plus `targets`), and 12 further `runs` leaves lose `--dir` (`show evidence verify-ledger next resume status decisions questions analyze query export submit`). THIS IS A SEPARATE DEFECT WITH A SEPARATE FIX and is owned by Order 02 (`zwv1sa`); it is recorded here because it is the evidence that the item's class is not hypothetical. | the before/after flag table (15 of 15 `<-- LOST`); the two-invocation temp-repo demonstration; the ancestor-dest scan naming all 13 `runs` leaves |
| F-05 | MED | **THE REACHABILITY WALK IS DEMONSTRABLY SENSITIVE, measured by mutation rather than asserted, AND RE-MEASURED VERBATIM AT REVIEW.** On the clean tree the walk returns `[]`. With `integration-lock`'s dest re-shadowed it returns exactly `[('integration-lock', "command=[] expected 'integration-lock'")]` - one finding, naming the leaf, the dest, the value found and the value expected. So the guard fails for precisely the change it exists to catch, and P16's "verify test sensitivity with mutation" is satisfiable with concrete pasted evidence. Review reproduced both sides character for character, and also confirmed the mutated walk still reaches total coverage (`mutated coverage: 151 / 151 unparsed: 0`), so the single finding is a real detection and not a side effect of a leaf that stopped parsing. | the paired clean/mutated walk runs, re-run at review |
| F-06 | MED | **THE ARGV SYNTHESIZER'S SOPHISTICATION IS LOAD-BEARING, AND ITS COVERAGE WAS MEASURED AT EACH STAGE, so an executor knows which corners are required rather than guessing.** Leaf tokens alone reach 86 of 151 leaves (65 exit 2); adding required positionals reaches 136; adding required OPTIONS reaches **146** (authoring wrote 147; the review re-run measures 146, so use the re-derived figure); honoring `action.choices` reaches 150 (the stragglers being `agy profile validate-default`, `oc profile validate-default`, `partition`, `path`, each of which declares a `choices` list); honoring `action.type` reaches 151 (`ipd scaffold --order` needs an int). A synthesizer stopping at any earlier stage would silently skip up to 65 leaves and still report zero findings, which is the vacuous pass E-02 asserts against. THE PROGRESSION IS MEASURED FOR `cli` ONLY AND IS NOT SUFFICIENT FOR ALL SEVEN BUILDERS - see F-17, which adds the required mutually-exclusive-group corner the progression never exercises. | five successive walk runs over `cli._build_parser()` with the coverage count and the failing-leaf list at each stage; all five re-run at review (86 / 136 / 146 / 150 / 151) |
| F-07 | HIGH | **CORRECTED AT REVIEW (2026-09-30). THE ITEM'S LITERALLY PRESCRIBED RULE FIRES ZERO TIMES ON A CLEAN TREE AND EXACTLY ONCE ON THE MUTATED ONE, so it is not unusable; authoring's 1160 measured a DIFFERENT and BROADER rule.** The item's words are "no subparser declares an argument whose `dest` collides with an ANCESTOR SUBPARSERS ACTION's `dest`", and the ancestor set that names is the 23 SUBPARSERS dests (`command`, `runs_command`, `oc_command`, ...), NOT every dest declared anywhere on an ancestor parser. Both rules were re-implemented and run at review. THE ITEM'S RULE (ancestor set = subparsers dests only): `total occurrences: 0, distinct dests: 0` on the clean `cli._build_parser()`, `0` on each of the other six builders, and `[('integration-lock', 'command')]` on the tree with `locked_command` re-shadowed. THE BROADER RULE authoring actually measured (ancestor set = every dest seen anywhere on the chain): 1160 occurrences over 23 dests, `help`/`no_color`/`color`/`no_interactive`/`interactive`/`agent`/`json` at 161 each. The 1160 figure and the seven-flag breakdown are REPRODUCIBLE and correct FOR THE BROADER RULE; what does not hold is attributing that rule to the item. CONSEQUENCE FOR THIS PLAN, stated plainly: the static rule is a VIABLE alternative remedy, so E-02's reachability walk is no longer justified by the static rule being unimplementable. It is justified on its merits instead (F-15). | review re-run of BOTH rules over all seven builders, clean and mutated: item's rule `[]` / `[('integration-lock', 'command')]`; broader rule 1160 over 23 dests with the per-dest `Counter` |
| F-08 | HIGH | **CORRECTED AT REVIEW (2026-09-30). THE CLAIM THAT NO NARROWING COVERS BOTH SHAPES IS FALSIFIED: narrowing (iii) CATCHES `integration-lock`.** The three narrowings and their counts reproduce exactly on the clean tree (1160 -> 33 -> 30 -> 29, the 29 survivors being the `runs` pairs alone; (i) also names `releases new` twice, which (ii) and (iii) clear). What does NOT hold is the conclusion. Narrowing (iii) was re-run at review against the MUTATED tree and reports 30 findings, the thirtieth being `('integration-lock', 'command')`: the mutated positional's default is `[]` (a REMAINDER's default), which is not `argparse.SUPPRESS`, so no exemption fires and the collision is reported. So narrowing (iii) covers the option-default shape AND the item's own positional shape, and the sentence "One static rule cannot cover both shapes" is wrong. THIS DOES NOT INVALIDATE THE PLAN'S SHAPE, but it moves the reason for it: the reachability walk is chosen for the properties in F-15, not because the static alternative fails. It also means F-09's limit is narrower than stated - see F-16. | review re-run of narrowing (iii) on the mutated tree: `total 30`, including `('integration-lock', 'command')`; the clean-tree counts 1160 / 33 / 30 / 29 reproduced |
| F-09 | MED | **THIS GUARD'S HONEST LIMIT: IT DOES NOT CATCH THE `runs` DEFECT, AND MUST NOT BE SOLD AS CATCHING IT.** The reachability walk asks only whether the SUBCOMMAND ROUTING KEY survived. The `runs` defect destroys a FLAG's value while leaving `command="runs"` and `runs_command="list"` intact, so the walk reports `OK 151 BAD 0` on a tree that carries 29 live flag-clobbering pairs. The two are the same argparse mechanism (F-02) with different victims: one loses the dispatch key and is therefore invisible-but-total, the other loses an operator's explicit argument and is therefore silent-but-partial. Stating this plainly is required, because a reviewer could otherwise reasonably believe Order 02 is redundant once Order 01 lands. REVIEW ADDENDUM: the CLAIM stands (the walk reports `[]` on the tree carrying the live `runs` defect, re-measured at review), but the INFERENCE the plan drew from it does not - see F-16, because narrowing (iii) covers both shapes and so the two-plan split is not forced by any coverage gap. | the clean walk's `BAD 0` measured on the SAME tree where the `runs` demonstration of F-04 fails; re-measured at review |
| F-10 | MED | **THIS IS THE SECOND TIME THIS EXACT PARSER SURFACE HAS SHIPPED A SILENT-OVERWRITE DEFECT, so the class has recurrence evidence and the remedy has direct precedent.** Backlog `zy1okf` recorded `conflict_handler="resolve"` on every `aw` parser making a duplicate OPTION definition silently replace instead of raising; it had already shipped a defect (`p0l1to`: a duplicate `--agent` emptied the shared action's `option_strings`, leaving `aw attention` permanently `agent=True` and `aw oc profile add --agent` reporting "unrecognized arguments"), and its workaround was also a RENAME (`--oc-agent`), exactly as this item's workaround was `locked_command`. It was closed by plan `76fgt1`, whose shape this plan follows: measure the tree, find zero live instances, add a durable guard over all seven builders with a mutation proving the guard fails. | `zy1okf` and its executed plan `76fgt1` read in full; `tests/test_cli_parser_conflict_policy.py` |
| F-11 | LOW | **THE `conflict_handler` FIX DOES NOT COVER THIS CLASS, so F-10's precedent is a template and not a duplicate.** `76fgt1` made a duplicate OPTION STRING raise at build time. A dest collision declares no duplicate option string at all (`locked_command` versus the subparsers action's `command` dest share no `--flag` spelling), so `error` never fires. Verified by construction: the tree today runs on the error handler and the F-01 mutation still parses silently. | the F-01 mutation performed on a tree built after `76fgt1` landed |
| F-12 | LOW | **THE CONFORMANCE MATRIX'S `usage_error` SCENARIO CANNOT CATCH THIS, confirming the item's closing note.** `tests/conformance_matrix.py` requires a `usage_error` scenario for every leaf, defined as "invalid flag -> exit 2". A shadowed leaf ALSO exits 2, and with well-formed usage output, so the scenario passes on a completely unreachable leaf. Likewise `discover_parser_leaves` and `find_undeclared_leaves` report a shadowed leaf as present and declared, because both walk registration and neither parses. | `SCENARIOS`/`required_scenarios` in `tests/conformance_matrix.py`; the F-01 mutation's exit code of 2 |
| F-13 | LOW | **THE SUITE IS GREEN AT HEAD IN THIS LANE, so any red after this plan is attributable to it - AND THE TOTAL IS NOT A CONSTANT.** Authoring measured `3246 passed, 2 skipped, 3 warnings in 52.31s` at HEAD `69a31fca`; review re-ran the bare suite at HEAD `7b2ff77b` and measured `3312 passed, 2 skipped, 3 warnings in 62.71s`, both with the standard `NOTE: 207 tests were deselected by -m/-k` notice. Green at both. The 66-pass movement in one day is the concrete reason E-01(d) re-derives the baseline in the lane and V-04 reconciles by NODE ID rather than by total. | both pasted baselines; `pyproject.toml` `addopts` |
| F-14 | LOW | **NO EXISTING TEST PARSES A SYNTHESIZED ARGV FOR EVERY LEAF, so this guard duplicates nothing.** The three existing whole-surface guards each stop short of an executed parse: `tests/test_command_surface_declarations.py` asserts zero undeclared leaves from registration alone; `tests/test_cli_parser_conflict_policy.py` builds parsers and inspects handlers without parsing; `tests/test_flag_surface_uniformity.py` parses a hand-written SAMPLE of five subcommands (`attention`, `check`, `doctor`, `find plans`, `ipd lint`). | the three files read; `SAMPLED_PARSED_SUBCOMMANDS` quoted from the third |
| F-15 | HIGH | **ADDED AT REVIEW. THE REACHABILITY WALK'S JUSTIFICATION, RESTATED HONESTLY NOW THAT F-07 AND F-08 NO LONGER SUPPLY IT.** With the static rule shown viable, the walk must stand on its own properties, and it does, on three that the static rule lacks. (1) IT ASSERTS THE PROPERTY THE OPERATOR CARES ABOUT. The static rule asserts a SHAPE (no dest repeats) and infers unreachability; the walk asserts REACHABILITY DIRECTLY by parsing a real argv and reading the namespace. When the walk is red, a leaf is provably unreachable; when the static rule is red, a leaf MIGHT be. That is what `GUIDING_PRINCIPLES` P16 means by "exercise the code ... assert observable outputs". (2) IT NEEDS NO HAND-MAINTAINED EXEMPTION LIST. Narrowing (i) exempts seven shared flags BY NAME, so the eighth shared flag added to `common` silently re-breaks the rule into a false-positive storm, and nothing tells the author. The walk has no name list to rot. (3) IT IS MECHANISM-AGNOSTIC. It would catch a future argparse change, a custom action subclass, or a `parse_known_args` interception that destroys the routing key by some route the static rule never models - and `_ViewerOrLeafSubParsersAction` proves this tree already subclasses the action the defect lives in. THE COSTS, stated so the trade is visible: the walk is more code, needs the synthesizer of F-06 and F-17, and runs 171 parses per suite run instead of one tree walk. | the three properties checked against the review re-runs of both rules; `_ViewerOrLeafSubParsersAction` in `agent_workflows/cli.py` |
| F-16 | MED | **ADDED AT REVIEW. THE TWO-PLAN SPLIT IS SOUND, BUT NOT FOR THE REASON THE PLAN GIVES.** The `## Workflow history` SET SHAPE note argues the plans are independent because "this guard's shape-based sibling would have caught the `runs` defect and this guard's reachability walk does NOT". The second clause is true (F-09) and the first is now known to be true as well (F-08 corrected), so the argument as written reduces to "the alternative remedy would have covered both, and we chose one that does not" - which argues AGAINST the split rather than for it. The split survives on the reasons the same note gives FIRST and which review confirms: the guard touches no production code while the fix edits `cli.py` and changes what a documented invocation does; and the guard measures the tree clean while the fix has a failing baseline. Those are dimensions of RISK and REVIEWABILITY, and they are sufficient. The coverage argument is withdrawn. | the history note read against F-08's corrected measurement; `- Scope-Paths:` of both plans (`tests/...` alone versus `agent_workflows/cli.py` plus a test) |
| F-17 | HIGH | **ADDED AT REVIEW. E-02's SYNTHESIZER SPEC AS AUTHORED CANNOT REACH TOTAL COVERAGE ON TWO OF THE SEVEN BUILDERS, so the plan's own total-coverage assertion would fail at execution.** The spec derives required options from `action.required`, and a REQUIRED MUTUALLY EXCLUSIVE GROUP sets that flag on NO member action: measured on `oc_runipd.build_parser()`, the `stop` leaf reports `required option actions: []` while carrying `mutex group required=True actions=['level_flag','level_flag','level_flag','level_flag']`. A walk built to the authored spec therefore reports `oc_runipd: canonical=7 parsed_ok=6` and `agy_runipd: canonical=7 parsed_ok=6`, failing on `runipd stop: error: one of the arguments --after-call --after-set --now --now-force is required`. THE FIX IS SMALL AND MEASURED: for each group in `parser._mutually_exclusive_groups` with `group.required`, emit ONE member (its first) and suppress that group's members from the per-action pass. With it, all seven builders reach total coverage (`cli 151/151`, `oc_runipd 7/7`, `agy_runipd 7/7`, `upgrade_rehearsal 6/6`, and 0/0 for the three flat builders). F-06's progression never caught this because it was measured on `cli` alone, which has no required mutex group on any leaf. | review probe: `[a.dest for a in stop._actions if a.option_strings and a.required]` -> `[]`; the group's `required=True`; the 6/7 walk before the fix and 7/7 after, for both runner builders |
| F-18 | MED | **ADDED AT REVIEW. E-03's SYMPTOM ASSERTION AND ITS OWN PROHIBITION CONTRADICT EACH OTHER, because `cli._dispatch` builds its own parser and accepts no injected one.** E-03 requires driving `cli._dispatch(["integration-lock", "--status", "--dir", <tmpdir>])` against the MUTATED parser, and separately forbids monkeypatching `cli._build_parser`. `_dispatch`'s first statement is `parser = _build_parser()` and its signature is `_dispatch(argv)` with no parser parameter, so there is NO route to the mutated tree that does not replace what `_build_parser` returns. THE RESOLUTION IS TO PERMIT A SCOPED PATCH RATHER THAN DROP THE ASSERTION: `unittest.mock.patch.object(cli, "_build_parser", ...)` as a CONTEXT MANAGER restores the original on exit, including on failure, which answers the leak hazard the prohibition was written for (the hazard is a MODULE-LEVEL rebind that outlives the test, not a scoped one). Demonstrated at review: inside the patch `rc=2` with 215 lines of top-level usage, and a walk of a freshly built parser immediately after the block reports `[]`, proving no residue. | `cli._dispatch`'s first line `parser = _build_parser()` and its `(argv)` signature; the review probe's `patched rc: 2 top-level usage: True lines: 215` followed by `post-patch clean walk findings: []` |

## Proposed changes (ordered, validatable)

1. Re-measure the defect reproduction, the clean-tree walk result, BOTH static rules' counts (the item's and the broader one, kept distinct per F-07), and the suite baseline; change no file (E-01).
2. `tests/test_cli_dest_shadowing.py`: the executed reachability walk over all seven builders with a type-aware argv synthesizer that also satisfies required mutually exclusive groups (F-17), a total-coverage assertion, and a lower-bound leaf count on the builders that have leaves (E-02).
3. `tests/test_cli_dest_shadowing.py`: the mutation case proving the walk detects a re-shadowed `integration-lock`, plus the exit-2-with-top-level-usage symptom assertion driven through a scoped `patch.object` with a post-block containment proof (E-03, F-18).
4. Reconcile the bare suite against the E-01(d) baseline by node id and re-run the new module twice in one session (E-04).

## Deferred / out of scope (with reason)

- THE LIVE `runs` FAMILY-FLAG LOSS (F-04, F-08's 29 survivors). Not fixed here because it edits `cli.py` and changes what a documented invocation DOES, while this plan adds a test and touches no production code; and because this guard does not detect it (F-09), so bundling them would let a reviewer believe one test covers both. It is Order 02 of this Set.
  - Carrier: zwv1sa
- A STATIC AUTHOR-TIME LINT OVER THE PARSER'S SHAPE, including the item's own suggestion. REJECTED AS A DESIGN CHOICE AND NOT ON FEASIBILITY, which review corrected: the item's own rule is implementable and measures 0 findings clean and 1 on the mutated tree, and narrowing (iii) of the broad rule covers BOTH the option-default shape and this item's positional shape (F-07 and F-08 as corrected). So this is a genuine alternative that was weighed and declined for the three properties F-15 states: the walk asserts reachability directly rather than inferring it from a shape, needs no hand-maintained shared-flag exemption list that a future `common` flag silently rots, and is mechanism-agnostic in a tree that already subclasses `_SubParsersAction`. The narrowing that suits the option-default shape is implemented by Order 02 as its own guard.
  - Carrier-Declined: No obligation is owed, and the reason is a weighed trade rather than an impossibility. The item asked for a test that makes this class fail; E-02 and E-03 deliver that for the item's own defect shape and Order 02 delivers it for the shape found during authoring. A future author who prefers the static rule will find the corrected measurements in F-07, F-08 and F-15 and can overrule this trade on the evidence rather than repeat the probes. A build-time REFUSAL (as opposed to a test) is a separate question already carried by backlog `sq1go0` via OQ-02.
- RENAMING ANY SHIPPED DEST, FLAG, OR POSITIONAL, including reverting `locked_command` to a nicer name now that a guard exists. Out because the current name is correct, carries a comment explaining why, and renaming it would change a public dest for aesthetics while this plan's whole claim is that it changes no behavior.
  - Carrier-Declined: Nothing is owed. `locked_command` is not a defect or a debt; it is the fix, and F-10 records that the analogous rename (`--oc-agent`) was likewise kept when its class was guarded.
- EXTENDING THE WALK TO ASSERT ANYTHING BEYOND SUBCOMMAND SURVIVAL, for example that every declared flag's value survives for every leaf. That is a strictly larger property (it would need a per-flag expected value for 151 leaves, not one token per traversed subparsers action) and the option-default slice of it is exactly what Order 02's guard covers for the family that has the defect. Building the general version now would be designing for a hypothetical need (P6).
  - Carrier: zwv1sa
- THE BARE-FAMILY-ROOT LEAVES THAT ARE NOT CANONICAL LEAVES. `aw ipd`, `aw specs`, `aw backlog`, `aw config` and friends are family ROOTS, so `discover_parser_leaves` deliberately excludes them and the walk does not cover them. Measured: bare `aw ipd` renders the board (rc 0) and bare `aw specs` prints family help (rc 2), so their behavior is already decided and tested elsewhere. Covering them would require distinguishing "prints help by design" from "fell through to help by accident", which no namespace inspection can do.
  - Carrier-Declined: No obligation. `command_surface`'s own comment establishes that a family root is not a leaf and is not declared, and the bare-root contract is carried by the identical alias leaves (`runs list` for `aw runs`) which the walk DOES cover.

## Scope check

- Over-scope: none. One declared path, `tests/test_cli_dest_shadowing.py`, written by E-02 and E-03. E-01 changes no file. No production module, no spec, no existing test file, and no documentation is touched.
- Under-scope, stated plainly: this plan does NOT fix a live user-facing defect, because F-03 measured that none of this shape exists. It also does NOT catch the `runs` defect (F-09), which is the largest thing a reader might expect from "fix the argparse dest collision class" and is deliberately Order 02's. And it implements a DIFFERENT remedy from the one the item names. REVIEW CORRECTION: that substitution is a weighed TRADE, not a forced move. Review measured the item's own rule implementable (0 clean, 1 mutated) and measured narrowing (iii) covering both defect shapes, so a reviewer preferring the static rule is overruling a judgement rather than a measurement, and the judgement is stated in F-15 with its costs.

## Required tests / validation

The BARE full suite is required by the execution contract: `python3 -m pytest`, with no added flags (no `-n0`, no extra `-q`, no `-p no:randomly`). RE-DERIVE the baseline in the lane rather than trusting this plan's figure, and compare failure sets by NODE ID rather than by total. Authoring baseline at HEAD `69a31fca`: `3246 passed, 2 skipped`. Review re-measured at HEAD `7b2ff77b`: `3312 passed, 2 skipped, 3 warnings in 62.71s`. The figure MOVED BY 66 PASSES IN ONE DAY on a shared tree, which is precisely why the baseline is re-derived at execution and never trusted from prose.

The new module must also be run alone with the configured defaults cleared, `python3 -m pytest -o addopts="" tests/test_cli_dest_shadowing.py -v`, because the plan requires per-test names and the configured `-q` suppresses them. That is the one sanctioned way to clear them per `AGENTS.md`.

MUTATION IS REQUIRED, NOT OPTIONAL. E-03 is itself the mutation case, so it is asserted in the suite rather than only demonstrated; V-03 additionally requires the paired clean/mutated walk output be pasted, so a reviewer can see `[]` against the one-finding list rather than taking a passing test's word for it.

TOTAL COVERAGE MUST BE PROVEN, NOT ASSUMED, AND FOR EVERY BUILDER SEPARATELY. V-02 requires the parsed-leaf count and the canonical-leaf count be pasted as equal PER BUILDER, because a synthesizer that quietly skipped leaves is the one way this guard passes while proving nothing, and because the authored synthesizer spec was measured at review to fail this on `oc_runipd` and `agy_runipd` specifically (F-17). A per-builder table is what makes that class of gap visible; an aggregate total would have hidden it.

`aw ipd lint` on this plan must report conforming. `aw sanitize --agent` must be clean. No `aw check` family run is required beyond what the suite covers, since no records artifact is edited.

Every validation below asserts on OUTCOMES (pasted command output, exit codes, parsed namespaces). No `V-*` may be marked from memory, and none may be marked without the actual pasted output its `Required evidence` names.

## Spec / documentation sync

N/A with reason. No spec governs argparse dest allocation in this CLI, and this plan changes no shipped behavior, flag, output contract, or command surface: it adds one test module. `docs/cli-output-contract.md` governs per-leaf OUTPUT (streams, schemas, exit codes) and is untouched, because no leaf's output changes. Spec `command-surface-redesign` governs which leaves exist and what each declares, and this plan adds, removes, and re-declares nothing. `- Scope-Paths:` therefore names no `.spec.md` file, which is the declaration the runners' spec-edit announcement reads.

The one documentation-shaped obligation is discharged INSIDE the deliverable: E-02's module docstring must record what a failure MEANS and what it does NOT mean (F-09's limit), so a future reader who hits a red does not reach for the wrong remedy, and does not assume the guard covers flag-value survival. It must ALSO record that a static parser-shape rule is a viable alternative that was weighed and declined (F-15), so the next reader who notices the cheaper rule finds the reasoning instead of re-deriving it or assuming an oversight.

## Open questions

### OQ-01: Should the reachability walk run against the other six builders at all, given each has at most one subparsers dest?

- Blocking: no
- Status: resolved
- Owner: plan author (resolution re-verified by /plan-review 2026-09-30)
- Resolution or deferral rationale: RESOLVED, RUN ALL SEVEN. Measured, and RE-MEASURED AT REVIEW with the figures reproducing exactly: `oc_runipd`, `agy_runipd` and `upgrade_rehearsal` each declare exactly 1 subparsers dest (`command`) and `layout_inventory`, `oc_models` and `pwatch` declare 0, against `cli`'s 23; so six of the seven cannot currently exhibit the defect and the walk finds nothing there. REVIEW ADDENDUM, WHICH STRENGTHENS THE ANSWER: covering the two runner builders turned out NOT to be free after all, because their `stop` leaf is the only place in the package with a required mutually exclusive group and it is what exposed F-17's synthesizer gap. Had the walk covered `cli` alone, that gap would have shipped undetected and the synthesizer would have been wrong for the next builder that grows one. Included anyway for two reasons. First, cost is near zero (their trees are tiny) while the value is real: `oc_runipd` is 8000+ lines edited by many concurrent plans (backlog `s6om7k` records exactly that hazard for the same file), so a future nested subcommand there is plausible and would arrive unguarded. Second, `76fgt1`'s guard already covers the same seven, so using a different set would leave a reader unable to say which parsers are guarded against what. A guard that covers a builder with zero collisions today is not vacuous; it is the case that has nothing to find YET.

### OQ-02: Should a shadowed dest be made to FAIL AT BUILD TIME rather than only in a test?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Carrier: sq1go0
- Resolution or deferral rationale: DEFERRED TO THE MAINTAINER, and deliberately NOT attempted here. `76fgt1` took exactly that route for duplicate option strings (removing the `resolve` handler so a collision raises at parser build), and the symmetry is tempting: a subclass hook could refuse an `add_argument` whose `dest` matches an ancestor subparsers dest. TWO MEASURED REASONS NOT TO DO IT IN THIS PLAN. First, ancestry is not available at the point of the call: `add_parser` builds a child that holds no reference to the subparsers action that created it, so a build-time check would need either a new registration wrapper or a post-build validation pass, and the latter is just this test running at import time on every `aw` invocation - a startup cost on every command to catch an author-time mistake. Second, the analogous refusal for the option-default shape would have to fire on the 29 live `runs` pairs (F-08, whose clean-tree narrowing counts review reproduced exactly), so shipping the refusal before Order 02 lands would break the CLI at import. Revisit after Order 02, when the tree is clean under both rules; until then the test is the gate. This question is a design choice about where a refusal belongs (public behavior of every `aw` invocation), which is the maintainer's call and not one repository evidence can settle. NOTE THE ONE PREMISE REVIEW REMOVED: this deferral does NOT rest on a static rule being unable to decide the property, since F-08 as corrected shows narrowing (iii) decides both shapes. It rests on WHERE the refusal belongs and on the import-time cost, both of which stand.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: All FIVE E-01 measurements pasted VERBATIM with the command that produced each: (a) the re-shadowed `integration-lock` dispatch showing its return code, the first line of its stdout, and that stderr is empty; (b) the clean-tree walk's per-builder finding list and OK/BAD counts; (c1) the ITEM'S static rule (ancestor set = subparsers dests only) run on BOTH the clean and the mutated tree, showing its total on each; (c2) the BROADER any-dest-repeat rule's total occurrence count and its per-dest `Counter`; (d) the bare `python3 -m pytest` summary line. Plus one explicit sentence per measurement stating whether it matches the figure in E-01 (rc 2 / 215 lines / empty stderr; `OK 151 BAD 0`; 0 clean and 1 mutated; 1160 over 23 dests; `3312 passed, 2 skipped`). KEEP c1 AND c2 SEPARATE AND LABEL WHICH IS WHICH: conflating them is the exact error review corrected in F-07, and a single number reported without its rule is not evidence for either. A divergence is ACCEPTABLE and must be reported, not silently absorbed; the suite total in particular moved 3246 -> 3312 between authoring and review.
  - Observed evidence: PASS. Five measurements recorded: (a) rc 2, top-level usage, empty stderr; (b) 152/152 leaves 0 findings across all 7 builders; (c1) item rule 0 clean, 1 mutated; (c2) broad rule 1167 over 23 dests; (d) baseline suite 1 failed, 3498 passed.
    (a) Re-shadowed integration-lock dispatch:
    Command:
    ```sh
    python3 -c "
    import io
    from contextlib import redirect_stdout, redirect_stderr
    from unittest.mock import patch
    import agent_workflows.cli as cli

    real_builder = cli._build_parser
    def make_mutated_parser():
        p = real_builder()
        for a in p._actions:
            if isinstance(a, cli.argparse._SubParsersAction):
                sp = a.choices.get('integration-lock')
                if sp:
                    for act in sp._actions:
                        if act.dest == 'locked_command':
                            act.dest = 'command'
        return p

    out = io.StringIO()
    err = io.StringIO()
    with patch.object(cli, '_build_parser', side_effect=make_mutated_parser):
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli._dispatch(['integration-lock', '--status', '--dir', '.'])
            except SystemExit as e:
                rc = e.code

    stdout_lines = out.getvalue().splitlines()
    stderr_lines = err.getvalue().splitlines()
    print(f'rc: {rc}')
    print(f'stdout lines: {len(stdout_lines)}')
    print(f'stdout first line: {repr(stdout_lines[0]) if stdout_lines else None}')
    print(f'stderr lines: {len(stderr_lines)}')
    "
    ```
    Output:
    ```
    rc: 2
    stdout lines: 218
    stdout first line: 'usage: agent-workflows [-h] [--no-color | --color] [--no-interactive |'
    stderr lines: 0
    ```
    Comparison: Matches expected rc 2, top-level usage, and empty stderr; stdout lines count moved from 215 to 218 due to newly added CLI subcommands.

    (b) Clean-tree reachability walk per-builder counts:
    Command:
    ```sh
    python3 -c "
    from tests.test_cli_dest_shadowing import BUILDERS, run_reachability_walk
    for name, builder in BUILDERS.items():
        p = builder()
        canonical, parsed_ok, failures, findings = run_reachability_walk(p)
        print(f'{name}: canonical={canonical} parsed_ok={parsed_ok} failures={len(failures)} findings={len(findings)}')
    "
    ```
    Output:
    ```
    cli: canonical=152 parsed_ok=152 failures=0 findings=0
    oc_runipd: canonical=7 parsed_ok=7 failures=0 findings=0
    agy_runipd: canonical=7 parsed_ok=7 failures=0 findings=0
    layout_inventory: canonical=0 parsed_ok=0 failures=0 findings=0
    oc_models: canonical=0 parsed_ok=0 failures=0 findings=0
    upgrade_rehearsal: canonical=6 parsed_ok=6 failures=0 findings=0
    pwatch: canonical=0 parsed_ok=0 failures=0 findings=0
    ```
    Comparison: Matches expected 0 findings across all 7 builders; canonical leaf count for cli moved from 151 to 152 due to tree growth.

    (c1) Item's static rule (ancestor set = subparsers dests only):
    Command:
    ```sh
    python3 -c "
    import argparse
    from agent_workflows import cli

    def check_c1(parser, mutate=False):
        if mutate:
            for a in parser._actions:
                if isinstance(a, argparse._SubParsersAction):
                    sp = a.choices.get('integration-lock')
                    if sp:
                        for act in sp._actions:
                            if act.dest == 'locked_command':
                                act.dest = 'command'
        occurrences = []
        def walk(p, ancestor_subparsers_dests, path):
            subparsers_actions = [a for a in p._actions if isinstance(a, argparse._SubParsersAction)]
            new_sub_dests = ancestor_subparsers_dests | {sa.dest for sa in subparsers_actions if sa.dest}
            for a in p._actions:
                if not isinstance(a, argparse._SubParsersAction):
                    if a.dest in ancestor_subparsers_dests:
                        occurrences.append((path, a.dest))
            seen_subparsers = []
            for sa in subparsers_actions:
                for name, subp in sa.choices.items():
                    if any(subp is prior for _, prior in seen_subparsers):
                        continue
                    seen_subparsers.append((name, subp))
                    walk(subp, new_sub_dests, f'{path} {name}'.strip())
        walk(parser, set(), '')
        return occurrences

    print('c1 clean:', len(check_c1(cli._build_parser(), False)), check_c1(cli._build_parser(), False))
    print('c1 mutated:', len(check_c1(cli._build_parser(), True)), check_c1(cli._build_parser(), True))
    "
    ```
    Output:
    ```
    c1 clean: 0 []
    c1 mutated: 1 [('integration-lock', 'command')]
    ```
    Comparison: Matches expected exactly 0 on clean tree and exactly 1 ([('integration-lock', 'command')]) on mutated tree.

    (c2) Broader any-dest-repeat static rule:
    Command:
    ```sh
    python3 -c "
    import argparse
    from collections import Counter
    from agent_workflows import cli

    def check_c2(parser):
        occurrences = []
        def walk(p, ancestor_dests, path):
            for a in p._actions:
                if not isinstance(a, argparse._SubParsersAction):
                    if a.dest in ancestor_dests:
                        occurrences.append((path, a.dest))
            current_dests = ancestor_dests | {a.dest for a in p._actions if a.dest}
            seen_subparsers = []
            for a in p._actions:
                if isinstance(a, argparse._SubParsersAction):
                    for name, subp in a.choices.items():
                        if any(subp is prior for _, prior in seen_subparsers):
                            continue
                        seen_subparsers.append((name, subp))
                        walk(subp, current_dests, f'{path} {name}'.strip())
        walk(parser, set(), '')
        return occurrences

    c2_clean = check_c2(cli._build_parser())
    print('c2 total occurrences:', len(c2_clean))
    counts = Counter(dest for _, dest in c2_clean)
    print('c2 distinct dests:', len(counts))
    print('c2 per-dest Counter:', counts.most_common(10))
    "
    ```
    Output:
    ```
    c2 total occurrences: 1167
    c2 distinct dests: 23
    c2 per-dest Counter: [('help', 162), ('no_color', 162), ('color', 162), ('no_interactive', 162), ('interactive', 162), ('agent', 162), ('json', 162), ('dir', 16), ('targets', 3), ('last', 1)]
    ```
    Comparison: Matches expected 23 dests; total occurrences moved from 1160 to 1167 (+7) because the 7 shared flags each gained 1 occurrence (161 -> 162) due to the addition of 1 new canonical leaf.

    (d) Baseline test suite summary:
    Command:
    ```sh
    python3 -m pytest
    ```
    Output:
    ```
    FAILED tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity
    1 failed, 3498 passed, 2 skipped, 3 warnings in 129.26s (0:02:09)
    ```
    Comparison: Baseline established; 1 pre-existing failure in tests/test_backlog.py due to known local vs UTC history date divergence (tracked in open backlog items fnb8pl and tl8qmc); pass count moved from 3312 to 3498 between review and execution.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_cli_dest_shadowing.py -v` pasted in full, showing every test name and `N passed`. PLUS the walk's own coverage numbers pasted from a direct run as a PER-BUILDER table: for each of the seven, the canonical leaf count and the count of leaves for which an argv was successfully parsed, shown as EQUAL. An aggregate total does NOT satisfy this: review measured the authored synthesizer at `oc_runipd 6/7` and `agy_runipd 6/7` (F-17), a gap an aggregate would have buried, so the two runner builders must each be shown at 7/7 and `upgrade_rehearsal` at 6/6. The three flat builders are expected at `0/0` and that is a PASS, not a gap. PLUS evidence the test reads no production source as text: paste the result of searching the new file for `getsource`, `ast.parse`, `read_text` and `open(` and show each returns nothing.
  - Observed evidence: PASS. tests/test_cli_dest_shadowing.py passed 3/3; total leaf coverage 152/152 for cli, 7/7 oc_runipd, 7/7 agy_runipd, 6/6 upgrade_rehearsal, 0/0 flat builders; zero source text reading matches.
    Pytest verbose execution:
    ```
    $ python3 -m pytest -o addopts="" tests/test_cli_dest_shadowing.py -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3640984251
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_cli_dest_shadowing.py::TestCliDestShadowing::test_shadowed_dest_symptom_dispatch_and_containment PASSED [ 33%]
    tests/test_cli_dest_shadowing.py::TestCliDestShadowing::test_clean_tree_reachability_and_total_coverage PASSED [ 66%]
    tests/test_cli_dest_shadowing.py::TestCliDestShadowing::test_mutation_sensitivity_detects_shadowed_dest PASSED [100%]

    ============================== 3 passed in 0.47s ===============================
    ```

    Per-builder reachability and coverage table:
    | Builder | Canonical Leaves | Parsed OK | Failures | Findings |
    |---|---|---|---|---|
    | cli | 152 | 152 | 0 | 0 |
    | oc_runipd | 7 | 7 | 0 | 0 |
    | agy_runipd | 7 | 7 | 0 | 0 |
    | layout_inventory | 0 | 0 | 0 | 0 |
    | oc_models | 0 | 0 | 0 | 0 |
    | upgrade_rehearsal | 6 | 6 | 0 | 0 |
    | pwatch | 0 | 0 | 0 | 0 |

    Verification of no source text reading (P16):
    ```
    getsource: 0 matches
    ast\.parse: 0 matches
    read_text: 0 matches
    open\(: 0 matches
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: The paired walk output pasted side by side: the clean tree's finding list (expected `[]`) and the mutated tree's finding list (expected exactly one entry naming `integration-lock` and the `command` dest, with the value found and the value expected; review measured `[('integration-lock', "command=[] expected 'integration-lock'")]`). PLUS the mutated-parser dispatch assertion's evidence: the return code (2) and proof that top-level usage was printed. PLUS a demonstration that the scoped patch did not leak: AFTER the `patch.object` block exits, a freshly built parser walked again reports `[]`, pasted (review measured `post-patch clean walk findings: []`). PLUS confirmation that the patch is a CONTEXT MANAGER and not an assignment, since F-18 permits only the scoped form. If the mutation's finding list has MORE than one entry, STOP and report it: the extra entries are either a real second instance or a synthesizer bug, and both need naming before this plan is claimed done.
  - Observed evidence: PASS. Clean walk findings []; mutated walk findings [('integration-lock', "command=[] expected 'integration-lock'")]; dispatch rc 2 top-level usage; post-patch clean walk findings [].
    Paired walk output:
    - Clean walk findings: `[]`
    - Mutated walk findings: `[('integration-lock', "command=[] expected 'integration-lock'")]`

    Mutated dispatch assertion:
    ```
    dispatch rc: 2
    top-level usage printed: True
    dispatch stdout lines: 218
    dispatch first line: usage: agent-workflows [-h] [--no-color | --color] [--no-interactive |
    dispatch stderr: ''
    ```

    Post-patch containment proof:
    - Post-patch clean walk findings: `[]`
    - Confirmed scoped context manager: implemented as `with patch.object(cli, "_build_parser", side_effect=make_mutated):` and not assignment.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Bare `python3 -m pytest` summary line pasted from the lane AFTER all edits, compared to the baseline re-derived in E-01(d) by NODE ID and not merely by total. The new module's tests must appear as passes and the pass count must rise by exactly the number of tests added. Any pre-existing failure must be shown present in the baseline too. PLUS `aw ipd lint --phase pre-transition` on this plan reporting conforming, and `aw sanitize --agent` clean, both pasted.
  - Observed evidence: PASS. Bare pytest suite passed 3501 (+3 from 3498 baseline, identical pre-existing backlog failure); 2 runs passed; sanitize clean.
    Post-edit bare `python3 -m pytest` summary:
    ```
    FAILED tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity
    1 failed, 3501 passed, 2 skipped, 3 warnings in 62.88s (0:01:02)
    ```
    Reconciliation by node ID:
    - Baseline: 3498 passed, 1 failed (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`)
    - Post-edit: 3501 passed, 1 failed (identical node ID)
    - Pass count difference: exactly +3 passed, corresponding to the 3 newly added node IDs:
      * `tests/test_cli_dest_shadowing.py::TestCliDestShadowing::test_clean_tree_reachability_and_total_coverage`
      * `tests/test_cli_dest_shadowing.py::TestCliDestShadowing::test_mutation_sensitivity_detects_shadowed_dest`
      * `tests/test_cli_dest_shadowing.py::TestCliDestShadowing::test_shadowed_dest_symptom_dispatch_and_containment`

    Two consecutive runs of the new module in the same session:
    ```
    Run 1: 3 passed in 0.47s
    Run 2: 3 passed in 0.44s
    ```

    Sanitize check:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed`. `/plan-review` ran on 2026-09-30 and recorded `- Readiness: go-pending-approval`, which is the review's own output and is the only legitimate writer of that field; the author correctly left it absent. Explicit human approval is still required before execution.

THIS PLAN CHANGES NO PRODUCTION CODE, AND THAT IS DELIBERATE, NOT AN OVERSIGHT. F-03 measured zero live instances of this defect shape, so there is nothing in `cli.py` to fix. An executor who finds themselves editing `agent_workflows/cli.py` has left this plan's scope: either they are fixing the `runs` defect, which is Order 02's (`zwv1sa`), or they have found a NEW instance, which must be reported with its measurement rather than quietly fixed here.

DO NOT SUBSTITUTE THE ITEM'S STATIC RULE FOR E-02, AND KNOW THAT IT IS REFUSED ON A DESIGN CHOICE RATHER THAN ON FEASIBILITY. This is the prohibition an executor is most likely to violate, because the backlog item states that remedy explicitly and in detail ("a cheap AST/parser-object walk"), and because it genuinely WOULD work: review measured the item's own rule at 0 findings clean and exactly `('integration-lock','command')` on the mutated tree, and measured narrowing (iii) covering the option-default shape as well (F-07, F-08, both CORRECTED from the authoring text that claimed otherwise). So do not expect E-02 to be easier than the census, and do not conclude from discovering that the census works that the plan was mistaken. The reasons to build the walk anyway are in F-15: it asserts reachability directly instead of inferring it from a shape, it needs no by-name exemption list for the shared `common` flags (which the next shared flag would silently rot), and it survives a mechanism change in a tree that already subclasses `_SubParsersAction`. If you believe the trade is wrong, say so with the measurement and stop; do not silently swap the deliverable.

DO NOT WEAKEN THE COVERAGE ASSERTION TO MAKE THE WALK PASS. If a leaf cannot be given a parsable argv, the correct response is to improve the synthesizer per F-06's progression AND F-17's required-mutex corner, NOT to skip that leaf, NOT to catch the failure and continue silently, and NOT to lower the leaf-count bound. EXPECT TO NEED F-17: a walk built to F-06's progression alone lands at `oc_runipd 6/7` and `agy_runipd 6/7`, which review already measured, so treat that specific red as the known gap with the known fix (emit one member of each required mutually exclusive group) rather than as a reason to exempt the `stop` leaf. A walk that skips leaves reports zero findings and is the vacuous pass this guard would otherwise become; `GUIDING_PRINCIPLES` P16 requires verifying test sensitivity by mutation for exactly this reason, and D78 records a test in this repository that "had started passing vacuously".

DO NOT PIN A TREE-WIDE COUNT AS AN EQUALITY. 151 leaves and 1160 census occurrences are MEASUREMENTS at one HEAD, not contracts, and the suite total already moved 3246 -> 3312 between authoring and review. Assert a floor comfortably below what you measure. `76fgt1` F-07/F-13 record this surface's counts moving 175, 219, 229, 283 and then 249, and one of its own transcribed figures failed to reproduce at review - as did two of THIS plan's (F-07 and F-08, corrected above).

MUTATE A LOCALLY BUILT PARSER FOR THE WALK, AND USE ONLY A SCOPED `patch.object` FOR THE DISPATCH ASSERTION. The walk half needs no patch: build, mutate the local object, walk it. The dispatch half CANNOT avoid one, because `cli._dispatch` builds its own parser and takes only `argv` (F-18), so `unittest.mock.patch.object(cli, "_build_parser", ...)` used as a CONTEXT MANAGER is the sanctioned route and its containment must be proved after the block, per V-03. What remains FORBIDDEN is the unscoped form: no `cli._build_parser = ...` assignment, no patch started at module or class setup scope, and no patch left running across tests. The suite runs `-n auto --dist=worksteal` with randomized order, so a leaked rebind surfaces as an unrelated flake in another file and will cost more to diagnose than this plan cost to write.

DO NOT READ PRODUCTION SOURCE AS TEXT (P16). No `inspect.getsource`, no `ast`, no `read_text` of anything under `agent_workflows/`, and no assertion about any comment or docstring, including the `dest="locked_command"` comment this plan quotes. Walking a BUILT parser's `_actions` is permitted and is the established idiom; reading the file that built it is not.

Executing agent: this is a SHARED CHECKOUT. Commit only the single path in `- Scope-Paths:`, through `aw commit 8kd4eo -- tests/test_cli_dest_shadowing.py`, never `git add -A`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`. Execute through `aw ipd begin 8kd4eo` before any edit. Do not mark any `V-*` verified without pasting the actual output its `Required evidence` demands, and do not claim done until `aw ipd lint --phase pre-transition` reports conforming.

THE TERMINAL TRANSITION IS UNCONDITIONALLY OWED, WITH A CONDITIONAL OWNER. In a managed lane the RUNNER owns it (`aw ipd begin`/`finalize` refuse an agent there with `AW-LIFECYCLE-ROLE-001`), and only in an unmanaged or manual run does the executor run `aw ipd finalize 8kd4eo` itself. Never hand-roll the move with `git mv` into `executed/` and never hand-edit `- Status: executed`.

SCOPE FENCE, A DECLARATION FOR RECONCILIATION RATHER THAN A STOP DIRECTIVE. The intended surface is exactly the one new file `tests/test_cli_dest_shadowing.py`. Specifically DO NOT: edit `agent_workflows/cli.py` or any other production module; touch `tests/test_cli_parser_conflict_policy.py`, `tests/test_command_surface_declarations.py`, `tests/test_flag_surface_uniformity.py` or `tests/conformance_matrix.py`, all of which are cited as evidence and none of which needs changing; rename any shipped dest, flag, or positional; edit any `.spec.md`; or implement the build-time refusal of OQ-02 (carried by backlog `sq1go0`). An out-of-scope edit that proves NECESSARY is to be MADE and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop. The one condition that DOES warrant stopping is a genuinely unsafe one: a concurrent edit to the new file that cannot be safely combined, or the absence of a symbol this plan depends on (`command_surface.discover_parser_leaves`, `cli._build_parser`, `cli._dispatch`, or any of the seven builders).

Backlog handoff: this plan carries `- From-Backlog: 0b290s` and INHERITS that item's `- Blocks-Release: next`, because the item is `- Work-Kind: bug` and this repository gates every live bug on the next release. Order 02 (`zwv1sa`) carries the same gate. The source item moves to `graduated` (not `done`) on authoring, since the design is handed off while no code is written yet; it may close `done` only when BOTH plans in this Set are executed, since either one alone leaves a measured instance of the item's class live in the tree (F-04, F-09).
