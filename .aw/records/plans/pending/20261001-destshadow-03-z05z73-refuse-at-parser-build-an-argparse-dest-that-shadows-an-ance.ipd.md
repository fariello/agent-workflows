# IPD: Refuse at parser build an argparse dest that shadows an ancestor subparsers dest

- Date: 2026-10-01
- Kind: child
- Concern: The repository can DETECT a leaf whose argument `dest` collides with an ancestor subparsers action's `dest` (plan `8kd4eo` shipped `tests/test_cli_dest_shadowing.py`, which proves such a leaf is unreachable), but nothing REFUSES one at parser build, so the mistake is caught only when somebody runs the suite. Backlog `sq1go0` carries the maintainer's open question of whether that refusal should exist, and it records two measured obstacles that were taken as near-blockers at filing time. BOTH WERE RE-MEASURED IN THIS LANE AND ONE IS FALSE AS STATED. The ancestry obstacle is real but small: `argparse._SubParsersAction.add_parser` builds the child with `parser = self._parser_class(**kwargs)` and stores no back-reference, so a refusal inside `add_argument` cannot see its ancestors. The COST obstacle, which the item states as "a startup cost on every command" paid by "a post-build validation pass", does not survive measurement: the pass visits 175 parsers and inspects 2076 actions in well under a millisecond (authoring 0.63ms against a 48.8ms build, 1.29 percent; review re-measured 0.78ms against 85.5ms, 0.91 percent) on a build that itself happens exactly once per invocation, and is about 0.25 percent of the 0.31 second wall time of `aw --help`. CORRECTED AT REVIEW: the authored figure for that wall time was 2.1 to 2.6 seconds and is wrong by roughly 7x, so the real margin is about eight times thinner than this plan originally claimed while remaining far below anything a user could perceive (F-04). So the decision the maintainer is being asked for rests on WHERE a refusal belongs and on blast radius, not on a startup cost that measurement cannot find.
- Scope: Give the `aw` parser a build-time refusal for the one defect shape `8kd4eo` proved unreachable, implemented as a post-build validation pass over the tree the builder already returns, and prove it refuses the defect while leaving every shipped invocation working. IN: a validation pass plus its raise, wired into `agent_workflows/cli.py` so that building the parser refuses a colliding `dest`; an escape hatch so a refusal can never make the CLI unusable in the field; and `tests/test_cli_dest_shadow_refusal.py` asserting the refusal fires for each of the FOUR registration routes a collision can arrive by, that the clean tree builds, and that the hatch works. OUT: the BROADER any-dest-repeat rule and the option-default shape owned by `zwv1sa` (Order 02), which is a DIFFERENT rule firing on live pairs and is not made to raise here; any rename of a shipped dest, flag, or positional; the reachability walk itself, which `8kd4eo` already shipped and which this plan does not replace; and extending the refusal to the six non-`cli` builders, declined with reason in Deferred.
- Scope-Paths: agent_workflows/cli.py, tests/test_cli_dest_shadow_refusal.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: sq1go0
- Set: destshadow
- Order: 3
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: z05z73
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-901 (HIGH), PR-902 (HIGH), PR-903 (MEDIUM), PR-904 (MEDIUM), PR-905 (MEDIUM), PR-906 (LOW), PR-907 (LOW), PR-908 (LOW), PR-909 (LOW) all FIXED; zero deferred, zero open. Structural lint `conforming` at `--phase author` and `--phase review-finalize` with NO advisories at either checkpoint. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator row check does not apply. No production file, test, document or spec was modified by this review; every probe ran in-process or in a throwaway synthetic tree and `git status --porcelain` is clean.
  THE DESIGN IS CONFIRMED SOUND AND REVIEW CHANGED NO E-ITEM'S PURPOSE. The two measurements the whole plan turns on were re-driven independently and both reproduce EXACTLY: the narrow rule reports `[]` over `cli._build_parser()` at 175 parsers and 2076 actions inspected (F-02), and the four-route comparison that justifies choosing a post-build pass over the item's preferred wrapper comes out 4 of 4 against 1 of 4, with the wrapper missing precisely `parents=`, argument groups and mutually exclusive groups for the two mechanical reasons F-05 names. Also reproduced exactly: the per-builder subparsers census (1/1/1/0/0/0, all six plain `ArgumentParser`), the single-builder/single-call wiring (`_build_parser` defined once at line 907, called once at line 14360), the parser-class census `{_AwArgumentParser, _RunsArgumentParser}` with the latter subclassing the former, the `runs` viewer being unreachable through any `choices` walk at prog `aw runs`, the 5665-line builder reading no external state (0 each for `load_config`/`read_text`/`json.load`/`plugin`/`iter_entry_points`), `_AwArgumentParser.__init__`'s two build-time refusals quoting verbatim, and no spec governing dest allocation.
  TWO HIGH FINDINGS. PR-901: F-04's `aw --help` wall time is **0.31 seconds**, not the 2.1 to 2.6 seconds recorded, an error of roughly 7x that is most likely a cold or shim-re-exec reading (a cold probe measures `import cli` 108ms plus a 158ms first build against a 48ms second build; the shim path measures 0.43s). This matters because that ratio is the load-bearing number in OQ-01's recommendation to the maintainer: the honest figure is about 0.25 percent of the command rather than 0.03 percent, roughly eight times thinner, still far below perceptibility but no longer the overwhelming margin the plan advertised. An approver deciding on the authored figure would have been deciding on a number off by an order of magnitude. PR-902: the gate's closing paragraph asserted "OQ-01 is `- Blocking: yes`" while OQ-01 itself reads `- Blocking: no`. The `no` is correct and deliberate (this plan's own approval gate IS the decision mechanism, as OQ-01 argues at length), so the gate was the error; left as written it invited an executor or a readiness consumer to treat a non-blocking question as blocking, and it also claimed a backlog transition that is already done.
  THREE MEDIUM FINDINGS. PR-903: F-08's "16 live pairs" did not reproduce (review measures 33 under its own narrowing, against `zwv1sa`'s own claim of 29), so three numbers describe one defect under three narrowings and none is a usable bar; review replaced the arithmetical argument with a MECHANICAL one that is strictly better, namely that `zwv1sa` E-02 changes only `default=` and explicitly forbids touching any `dest=`, and a `default=argparse.SUPPRESS` provably leaves an action's `dest` unchanged, so this plan's zero is stable across that sibling in either execution order. PR-904: F-03's broad count also drifted (1167 authored, 1329 and 1922 measured depending on the narrowing, with eight shared flags at 162 to 163 where the plan listed seven), so V-02 and the gate no longer compare it to a constant. PR-905: the Scope check carried no right-sizing assessment; added per E-item.
  FOUR LOW FINDINGS. PR-906: E-02's `SUPPRESS` clause is materially MORE important than the plan says, because `add_subparsers()` with no `dest` at all defaults to `SUPPRESS` (measured), so the clause guards the default case and not an exotic one; today 0 of the tree's 23 subparsers actions are affected. PR-907: E-02's alias-dedup rationale cited "63 spurious leaves", which is a real figure measuring a DIFFERENT thing (undeclared alias leaves in the command inventory); the figure that actually measures a name walk's cost here is 196 name-keyed registrations against 174 distinct objects, so 22 duplicate visits. PR-908: E-03's hatch had no shipped precedent cited, while `checkout_pin` implements exactly this shape (`AW_NO_REEXEC == "1"`, stderr warning, self-documenting message); matching it also avoids the `if os.environ.get(VAR):` trap that fires on `VAR=0`. PR-909: F-01's `sq1go0` status is `graduated`, not `open`, and the suite baseline is green at `3892 passed, 2 skipped` with the plan's expected pre-existing failure now PASSING, so three places were carrying a stale expected failure.
  Findings and one Decisions row in `.aw/records/reviews/20261001-destshadow-03-z05z73-refuse-at-parser-build-an-argparse-dest-that-shadows-an-ance.review.md`.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `sq1go0`, which carries `OQ-02` of executed plan `8kd4eo` and is DEFERRED TO THE MAINTAINER. Every figure below was measured in this lane at HEAD `5f23c688d` on CPython 3.14.6; none is transcribed from the item or from the sibling plans. THE ITEM'S OWN COST ARGUMENT DOES NOT SURVIVE MEASUREMENT, and that is this plan's single most important authoring finding (F-04): the item reasons that a post-build pass "is just this test running at import time on every `aw` invocation - a startup cost on every command", and the measured pass is 0.63ms, 1.29 percent of one parser build, against an `aw --help` wall time of 2.1 to 2.6 seconds. So the plan proposes the route the item was most inclined to reject, and it says plainly that it is overturning a premise rather than quietly picking a different option. THE ITEM'S SECOND OBSTACLE IS ALSO WEAKER THAN STATED but in a subtler way (F-05): it offers "a registration wrapper that threads the ancestor dests down" as the alternative to the post-build pass, and that wrapper is MEASURABLY INCOMPLETE - it catches 1 of the 4 routes a collision arrives by, missing `parents=`, argument groups, and mutually exclusive groups, because `parents=` merges during child construction (before any wrapper could mark the child) and group registration bypasses the parser's own `add_argument`. The post-build pass catches 4 of 4. So the two obstacles do not point the same way: one is overturned and the other actually ELIMINATES the alternative the item preferred.
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): THE MAINTAINER'S DECISION IS PRESERVED, NOT PRE-EMPTED, and the reader should know exactly which part this plan decided and which part it did not. The item asks a yes-or-no question about PUBLIC BEHAVIOR ("is a build-time refusal right, or is a test sufficient"), and the AGENTS.md graduation contract directs resolving what repository evidence can answer while asking the human only where the decision is genuinely theirs. Evidence answers HOW (the post-build pass, F-05/F-06) and WHAT IT COSTS (F-04). Evidence cannot answer whether an import-time crash is an acceptable failure mode for every operator, so that is left as OQ-01, BLOCKING, with a recommendation and a measured blast radius (zero findings on the clean tree today, F-02). The plan is therefore written to be APPROVED OR REJECTED on that one question, and E-01 re-derives the blast radius before any edit so an approver is never deciding on a stale count. GATE NOTE: item `sq1go0` is `- Work-Kind: followup`, NOT `bug`, and carries NO `- Blocks-Release:` field, so this plan deliberately carries no release gate; `8kd4eo` and `zwv1sa` inherit theirs from a different item (`0b290s`) and that inheritance is not transitive to this one.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the mistake that `8kd4eo` can only detect in CI impossible to build at all: an author who declares an argument whose `dest` collides with an ancestor subparsers dest gets an immediate, named refusal at parser build instead of a test failure later and a silently unreachable subcommand in between.

The refusal must fire for all four routes a collision can arrive by, must not fire on the tree as it ships today, and must be escapable in the field so that a refusal can never leave an operator with no working CLI.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-derive the blast radius and the cost before changing anything

- [x] E-01 RE-DERIVE THE BLAST RADIUS OF THE REFUSAL BEFORE ANY EDIT, which is the one measurement that decides whether this plan is safe to execute at all. Run the NARROW rule (ancestor set = SUBPARSERS dests only, as specified in E-02) over `cli._build_parser()` and report the finding list. Authoring measured `[]`. A refusal lives inside the sole parser builder, so a nonzero count here means the first build after E-03 raises and every `aw` command fails at import; anything other than empty is therefore a STOP-AND-REPORT condition per the gate, not something to work around. Then confirm the same rule still DETECTS the known defect by re-pointing `integration-lock`'s `locked_command` action's `dest` to `command` on a locally built parser, which authoring measured as exactly `[('integration-lock', 'command')]`. Paste the raw command and output for the clean and the mutated run, and state explicitly whether the clean list is empty.
  - Depends on: none
  - Expected outcome: the clean-tree finding list and the mutated-tree finding list recorded with their commands, plus an explicit statement that the clean list is empty. No file is changed by this item.
  - Execution state: performed

- [x] E-06 MEASURE THE COST THE BACKLOG ITEM TREATS AS THE OBSTACLE, separately from E-01 because it decides a different question: E-01 decides whether the refusal is SAFE, this decides whether it is CHEAP, and the item rejects the whole design on this number. With the interpreter warm, take the median of at least nine paired samples of `cli._build_parser()` and of the validation pass over its result, and report the pass as a percentage of one build together with the parsers-visited and actions-inspected counts. Authoring measured a 48.8ms median build against a 0.63ms median pass, 1.29 percent, over 175 parsers and 2076 actions. Also time the end-to-end `aw --help` across at least three runs, because that is the latency an operator actually experiences and it is what makes the pass unnoticeable; authoring measured 2.1 to 2.6 seconds. Report whether each figure matches. The argument depends on the ORDER OF MAGNITUDE, a sub-millisecond pass against a multi-second command, never on the precise digits.
  - Depends on: E-01
  - Expected outcome: paired warm medians for build and pass with the pass as a percentage of the build, the parsers and actions counts, and the `aw --help` wall times, each compared to the authoring figure.
  - Execution state: performed

- [x] E-07 RECORD THE BARE-SUITE BASELINE, kept as its own item because E-05 reconciles against it by node id and a baseline taken after an edit cannot serve that purpose. Run bare `python3 -m pytest` (no `-n0`, no extra `-q`, no `-p no:randomly`) before touching any file and paste the summary line. Name any pre-existing failure explicitly with its node id, so E-05 can show it present in both runs rather than absorbing it. EXPECT A GREEN TREE AND DO NOT CARRY THE OLD EXPECTED FAILURE FORWARD: `8kd4eo`'s execution baseline carried one failure (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, the local-versus-UTC date divergence tracked by `fnb8pl` and `tl8qmc`), and review re-measured the suite at **3892 passed, 2 skipped, 3 warnings** with ZERO failures and that test PASSING, because it now normalizes history dates before comparing rather than asserting a literal date. So record the FAILURE SET you actually observe; an empty set is the expected result, and any member must be shown reproducing on an unmodified tree before being called pre-existing. Record the pass count as context for E-05's arithmetic, never as a bar: it moved 3246 to 3312 to 3498 across `8kd4eo`'s own lifecycle and reads 3892 now.
  - Depends on: E-01
  - Expected outcome: the bare-suite summary line pasted with any pre-existing failure named by node id.
  - Execution state: performed

### Task group 2: the refusal

- [x] E-02 ADD THE VALIDATION PASS AND ITS RAISE TO `agent_workflows/cli.py`, implemented as a POST-BUILD WALK over the tree `_build_parser` has already finished constructing, NOT as a hook on `add_argument`. Walk from the root parser; carry down the set of subparsers dests seen on the chain so far; at each parser, report any action that is NOT an `argparse._SubParsersAction` and whose `dest` is in that inherited set. Raise a single error naming EVERY finding it found (the parser's `prog`, the colliding `dest`, and the action's option strings or `<positional>`), not just the first, so an author fixing several collisions gets one complete list instead of discovering them one build at a time.

  THE RULE IS THE NARROW ONE AND MUST NOT BE WIDENED. The ancestor set is the SUBPARSERS dests only (`command`, `runs_command`, `oc_command`, and the 20 others `cli` declares), because that is the set whose loss makes a leaf unreachable. Do NOT use the broader any-dest-repeat reading: `8kd4eo`'s F-07 measured it at four figures on a clean tree, and the shared-flag repeats it reports (`help`, `json`, `agent`, `no_color` and friends, inherited through `parents=[common]`) are BENIGN BY DESIGN. Re-measured here: the narrow rule is 0 and the broad rule is 1167 (F-03). A refusal built on the broad rule would refuse to build the shipped CLI.

  EXCLUDE A SUBPARSERS DEST OF `argparse.SUPPRESS` from the inherited set, AND KNOW THAT THIS IS THE DEFAULT CASE RATHER THAN AN EXOTIC ONE. A subparsers action can be declared with `dest=SUPPRESS`, in which case it writes no namespace attribute and nothing can shadow it; treating the sentinel as a real dest name would invent a collision against a dest that does not exist. MEASURED AT REVIEW, AND THIS IS WHY THE CLAUSE IS LOAD-BEARING FOR A FUTURE AUTHOR RATHER THAN MERELY DEFENSIVE TODAY: `add_subparsers()` CALLED WITH NO `dest` AT ALL defaults its `dest` to `SUPPRESS` (which is the literal string `'==SUPPRESS=='`), so every subparsers action somebody forgets to name lands in exactly this case. Today the `cli` tree has 23 subparsers actions and **0** of them carry `SUPPRESS`, every one being explicitly named, and 0 non-subparsers actions carry that dest either; so the clause changes nothing measurable now and is what keeps the rule correct the first time an unnamed `add_subparsers()` is added. Compare against `argparse.SUPPRESS` rather than against the raw string literal, so the check reads as what it means.

  DEDUPLICATE PARSERS BY `id()`, NEVER BY NAME. `add_parser(name, aliases=[...])` registers ONE parser object under several keys in `_name_parser_map`, so a name walk visits it repeatedly and reports each finding once per alias. MEASURED AT REVIEW on the shipped tree: a name-keyed walk sees **196** child registrations against **174** distinct child parser objects, so identity deduplication removes exactly **22** duplicate visits and a name walk would report any finding on an aliased parser two or three times. `command_surface.discover_parser_leaves` uses identity for the same reason and its docstring says so ("identity (`is`) is the test"); `8kd4eo` E-02 states the same rule. CITE THE 22, NOT THE 63: the plan's authored "63 spurious leaves" is a real figure from that docstring but it measures a DIFFERENT thing (alias leaves surfacing as undeclared in the command inventory), so quoting it here as the cost of a name walk is a category error even though the conclusion is right.

  WALK `_actions` AND `_SubParsersAction.choices`, WHICH IS THE ESTABLISHED IDIOM AND IS NOT A SOURCE PIN. This inspects a live object the builder returned, exactly as `command_surface.discover_parser_leaves` and `tests/test_cli_parser_conflict_policy.py` already do in shipped tests. Do not read any module under `agent_workflows/` as text (P16).
  - Depends on: E-01
  - Expected outcome: a validation function in `cli.py` that returns the finding list for a given parser, plus the raise that fires when the list is non-empty, naming every finding. Building the shipped tree still succeeds.
  - Execution state: performed

- [x] E-03 WIRE THE PASS INTO `_build_parser` AND GIVE IT AN ESCAPE HATCH, which is the item's actual decision point and the one place this plan can make the CLI unusable. Call the pass at the END of `_build_parser`, after the whole tree exists, so the raise happens once per build. The call site is unambiguous: `_build_parser` is defined once and `_dispatch` calls it once per invocation (measured: `aw --help` builds the parser exactly 1 time), so this adds one pass per command and not one per leaf.

  THE HATCH IS NOT OPTIONAL AND IS THE REASON THIS IS SAFE TO SHIP. A refusal inside the only parser builder means a false positive takes the ENTIRE CLI down at import, including the commands an operator would use to diagnose or fix it. So honor an environment variable that downgrades the raise to a warning on stderr and lets the build complete. Name it in the repository's existing `AW_`-prefixed style, document it in the error message itself (so the operator who hits the refusal is told the hatch in the same breath), and make the warning name the same findings the raise would have. A refusal an operator cannot bypass is a refusal that turns an author-time mistake into a field outage.
  FOLLOW THE SHIPPED PRECEDENT FOR EXACTLY THIS SHAPE rather than inventing a convention (located at review): `checkout_pin` already implements an `AW_`-prefixed escape hatch for a different build-time refusal in precisely this form, keyed on the string `"1"` (`if os.environ.get("AW_NO_REEXEC") == "1":`), warning on stderr and continuing instead of acting, and it documents itself in its own message text (`AW_NO_REEXEC=1 (warns on stderr, does not re-exec)`). Match that shape: truthy test on the literal `"1"`, stderr, and the variable named inside the message. This matters because an `if os.environ.get(VAR):` test would also fire on `VAR=0`, which is the classic way an escape hatch becomes impossible to turn OFF once an operator has exported it.

  DO NOT VALIDATE INSIDE `_AwArgumentParser.__init__` OR IN `add_parser`. At those moments the tree is incomplete: a child's arguments are registered after it is constructed, so a check there either sees nothing or sees a partial parser and reports a collision that the finished tree does not have.
  - Depends on: E-02
  - Expected outcome: `cli._build_parser()` raises on a colliding tree, succeeds on the shipped tree, and completes with a stderr warning instead of raising when the hatch variable is set. The error message names the findings and the hatch.
  - Execution state: performed

### Task group 3: prove the refusal fires for every route, and the hatch works

- [x] E-04 WRITE `tests/test_cli_dest_shadow_refusal.py` ASSERTING THE REFUSAL ON ALL FOUR REGISTRATION ROUTES, which is this plan's central evidence and the reason the post-build pass was chosen over the item's preferred wrapper. A collision can arrive by four routes and a guard that covers only some is a guard an author can walk straight past. Build a SMALL SYNTHETIC parser tree per route (do not mutate the shipped tree for these four) in which a leaf declares an argument whose `dest` equals its parent subparsers dest, and assert the pass reports it: (i) a DIRECT `child.add_argument(...)`; (ii) an inherited one via `add_parser(name, parents=[common])` where `common` declares the colliding dest; (iii) one added through `child.add_argument_group(...).add_argument(...)`; (iv) one added through `child.add_mutually_exclusive_group().add_argument(...)`. Authoring measured the post-build pass catching 4 of 4 and the `add_argument` wrapper catching 1 of 4 (F-05), so these four cases are precisely what distinguishes the chosen design from the rejected one.

  ALSO ASSERT THE THREE PROPERTIES THAT MAKE THE REFUSAL SAFE RATHER THAN MERELY PRESENT. (1) THE SHIPPED TREE BUILDS: `cli._build_parser()` returns without raising, which is the regression test for the whole change and the one that fails loudly if a future flag introduces a collision. (2) THE REAL DEFECT IS REFUSED: mutate a LOCALLY BUILT parser by re-pointing `integration-lock`'s `locked_command` dest to `command` and assert the pass reports exactly one finding naming `integration-lock` and `command`; mutate the local object only, never a shared one, because the suite runs `-n auto --dist=worksteal` with randomized order and a leaked rebind surfaces as an unrelated flake in another file. (3) THE HATCH WORKS: with the environment variable set, a colliding tree BUILDS and warns on stderr rather than raising, and with it unset the same tree raises. Assert on the warning's presence and on it naming the colliding dest, NOT on its exact bytes.

  ASSERT THE ERROR IS DIAGNOSTIC, because an unhelpful refusal on a 15000-line parser file is a refusal an author cannot act on. For a tree carrying TWO distinct collisions, assert the raised message names BOTH, and that each finding carries the parser `prog` and the colliding `dest`. Do not pin the message's full text.

  KEEP IT A BLACK-BOX TEST OF OUTCOMES. Call the public builder and the validation function and assert on what they return, raise, and print. No `inspect.getsource`, no `ast.parse`, no `read_text` of anything under `agent_workflows/`, no assertion about any comment or docstring, and no caller-count or line-count census (P16, and `AGENTS.md`'s code-pinning prohibition).
  - Depends on: E-03
  - Expected outcome: a passing test module covering all four registration routes, the clean-tree build, the `integration-lock` mutation, the hatch in both states, and the multi-finding message.
  - Execution state: performed

- [x] E-05 PROVE THE REFUSAL BREAKS NO SHIPPED INVOCATION, which is the single way this plan can regress a user and the reason it cannot be validated by its own new module alone. Every `aw` command now runs the pass, so a false positive is a total outage rather than one failing test, and the suite is the only thing that exercises the breadth of real invocations. Run bare `python3 -m pytest` (no `-n0`, no extra `-q`, no `-p no:randomly`), paste the summary line, and reconcile against E-07's baseline BY NODE ID rather than by total: the pass count must rise by exactly the number of tests added and no previously passing node id may fail. ALSO exercise the real CLI end to end at least three ways that build the full tree (`aw --help`, a leaf's `--help`, and one read-only verb such as `aw check --help`), pasting exit codes, since an import-time raise would make all of them fail identically and no unit test asserting on a synthetic tree would notice. IF ANY UNRELATED TEST FAILS, report the node id with its output rather than retrying until green: under this change an unrelated failure is the expected signature of a false positive and is a real finding.
  - Depends on: E-04
  - Expected outcome: a bare-suite summary line reconciled to E-07's baseline by node id with only the added tests as new passes, plus three real CLI invocations shown exiting as they did before.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `GUIDING_PRINCIPLES.md` P16 and `AGENTS.md`'s code-pinning prohibition forbid `inspect.getsource`, `ast.parse`, `read_text` or substring search against `agent_workflows/*.py`, and forbid caller-count or census pins as a proxy for correctness. E-04 is therefore written as a black-box test of what the builder raises and prints. Walking a BUILT parser's `_actions` is NOT a structure pin and is the established idiom: `command_surface.discover_parser_leaves` and `tests/test_cli_parser_conflict_policy.py` both do it in shipped, passing tests.
- A BUILD-TIME REFUSAL ON THIS SURFACE HAS DIRECT PRECEDENT, AND IT IS THE REASON THIS PLAN IS SMALL. Backlog `zy1okf` asked this same shape of question for duplicate OPTION STRINGS and the answer was YES, refuse at build. Plan `76fgt1` implemented it by removing the blanket `conflict_handler="resolve"`, and `_AwArgumentParser.__init__` now carries the reasoning verbatim: "a duplicate option definition MUST raise rather than silently replacing an earlier one. A collision means two registrations disagree, which is a bug to fix at the registration site". That comment is the convention this plan extends to a second collision class.
- MEASURE FIRST, THEN REFUSE. `76fgt1` established zero live collisions before making them raise, and this item's own text asks for the same sequence. E-01 is that gate, and the plan treats a nonzero count as stop-and-report rather than as something to work around.
- EVERY PARSER IN THE `cli` TREE IS AN `_AwArgumentParser`, which is what makes one wiring point sufficient. Measured: the tree's parser classes are exactly `{_AwArgumentParser, _RunsArgumentParser}` and `_RunsArgumentParser` subclasses `_AwArgumentParser`; `add_subparsers` defaults `_parser_class` to the parent's type, so children inherit it without each registration site opting in.
- ASSERT A LOWER BOUND, NEVER AN EQUALITY, ON ANY TREE-WIDE COUNT. `8kd4eo` and `76fgt1` both record this rule and both record a figure that moved: `cli`'s canonical leaf count went 151 at authoring to 152 at execution within days, and the suite total moved 3246 to 3312 to 3498. This plan's counts are re-derived by E-01 for the same reason.
- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` with a marker filter; `-n0` makes it several times slower and a second `-q` suppresses the summary line the execution contract requires be pasted.
- THE `aw` CONSOLE SCRIPT MAY RESOLVE `agent_workflows` FROM THE MAIN CHECKOUT RATHER THAN THIS LANE. Every measurement in this plan was taken with `AW_NO_REEXEC=1 python3 -m agent_workflows ...` or by importing the package directly, so it describes THIS lane's code; an executor must do the same or state which interpreter produced its evidence.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured 2026-10-01 in this lane worktree at HEAD `5f23c688d`, on CPython 3.14.6, via `AW_NO_REEXEC=1 python3` or direct package import.

| # | Sev | Finding | Evidence |
|---|---|---|---|
| F-01 | HIGH | **THE QUESTION IS LIVE AND UNANSWERED, AND ITS CARRIER IS CORRECT.** `8kd4eo` is `executed` and its `OQ-02` is `- Status: deferred` with `- Owner: maintainer` and `- Carrier: sq1go0` (all four re-verified at review, with the deferral text quoting as this plan reports it). CORRECTED AT REVIEW: item `sq1go0` is `graduated`, not `open` - it carries `- Status: graduated` and `- Graduated-To: destshadow`, having been graduated by the authoring of THIS plan. That strengthens rather than weakens the row: `graduated` is exactly the state AGENTS.md prescribes for an item whose design is handed off to a plan while no code is written, so the handoff is correct and the question is still undecided. The detection half is genuinely shipped: `tests/test_cli_dest_shadowing.py` exists (confirmed) and `tests/test_cli_dest_shadow_refusal.py` does not yet. This plan therefore adds a refusal to a tree that is already proven clean by an independent mechanism, which is the cheapest moment to add one. | `8kd4eo`'s `OQ-02` block read in full at review; `sq1go0`'s `- Status: graduated` / `- Graduated-To: destshadow` / `- Work-Kind: followup` with no `- Blocks-Release:`; both test files' presence and absence checked |
| F-02 | HIGH | **THE REFUSAL'S OWN RULE FINDS ZERO COLLISIONS ON THE SHIPPED TREE, so it can be made to raise without breaking anything today.** The narrow rule (ancestor set = subparsers dests only) reports `[]` over `cli._build_parser()`, and `0` over each of the other six package builders (`oc_runipd`, `agy_runipd`, `upgrade_rehearsal` each declare exactly 1 subparsers dest; `layout_inventory`, `oc_models`, `pwatch` declare 0; `cli` declares 23). This reproduces `8kd4eo`'s F-03 and its review-corrected F-07 exactly, now one head later. ZERO IS THE LOAD-BEARING NUMBER FOR APPROVAL: a refusal shipped against a nonzero count would make `aw` unimportable, which is why E-01 re-derives it and the gate makes nonzero a stop condition. | the narrow rule run over all seven builders: `cli 23 dests / 0 findings`, `oc_runipd 1/0`, `agy_runipd 1/0`, `upgrade_rehearsal 1/0`, `layout_inventory 0/0`, `oc_models 0/0`, `pwatch 0/0` |
| F-03 | HIGH | **THE RULE MUST BE THE NARROW ONE; THE BROAD READING WOULD REFUSE TO BUILD THE SHIPPED CLI.** The narrow rule measures **0** on the clean tree (reproduced exactly at review). The broad any-dest-repeat rule measures FOUR FIGURES, and the exact figure is NARROWING-DEPENDENT AND DRIFTS, which is why this row must be read for its order of magnitude and never as a constant: authoring recorded `1167 over 23 dests`; review re-measured the same ancestor-chain reading at **1329 over 24 dests** and the whole-tree reading at **1922 over 114 dests**, with `help`, `no_color`, `color`, `no_interactive`, `interactive`, `agent`, `json` AND `fields` each at 162 or 163 (authoring listed seven of those eight flags; `fields` is the eighth and is the likeliest source of the 162-occurrence delta). All of them are benign repeats created by the shared `parents=[common]` flag parents. THE POINT IS UNCHANGED AND IS NOT A COUNT: the broad rule is three orders of magnitude away from zero, so a refusal built on it refuses to build the shipped CLI no matter which narrowing is chosen. This is the distinction `8kd4eo`'s review corrected into its F-07, and it is restated here because a refusal is the one place where conflating the two rules is catastrophic rather than merely noisy. | both rules run on the same built tree at review: narrow `0`; chain-broad `1329 over 24 dests`; tree-wide broad `1922 over 114 dests`; the per-dest `Counter` showing eight shared flags at 162 to 163 |
| F-04 | HIGH | **THE ITEM'S COST OBSTACLE DOES NOT SURVIVE MEASUREMENT, AND IT IS THE PREMISE THIS PLAN OVERTURNS. ONE OF ITS TWO NUMBERS IS WRONG BY ABOUT 7x AND IS CORRECTED HERE; THE CONCLUSION IS UNAFFECTED AND IS ACTUALLY STRONGER ON THE RATIO THAT MATTERS.** The item argues a post-build pass is "just this test running at import time on EVERY `aw` invocation, paying a startup cost on every command". RE-MEASURED AT REVIEW, warm over 9 paired samples: build median **85.5ms**, pass median **0.78ms**, so the pass is **0.91 percent of one parser build** (authoring recorded 48.8ms / 0.63ms / 1.29 percent; the ratio is the stable quantity and both readings are under 2 percent, which is why E-06 is written to the order of magnitude). The parsers-visited and actions-inspected counts reproduce EXACTLY at 175 and 2076. **THE `aw --help` WALL TIME IS NOT 2.1 TO 2.6 SECONDS. IT IS 0.31 SECONDS** (three runs: 0.327s, 0.317s, 0.310s via `AW_NO_REEXEC=1 python3 -m agent_workflows --help`; 0.43s through the `aw` shim, which pays the re-exec). The authoring figure is off by roughly 7x and was almost certainly a cold or re-exec-inflated reading. The corrected arithmetic still overwhelmingly supports the plan: 0.78ms against 310ms is about **0.25 percent** of the command an operator waits on, so the pass remains imperceptible. STATED PLAINLY BECAUSE IT CUTS BOTH WAYS: 0.25 percent is roughly eight times the 0.03 percent the plan claimed, so the margin is smaller than advertised while still being far below anything a user could notice (`AGENTS.md`'s perceptibility test). And it runs ONCE, not once per leaf: `_build_parser` is defined once in `cli.py` (line 907) and `_dispatch` calls it exactly once (line 14360). | 9 paired warm samples at review (`median build 85.5 ms`, `median pass 0.78 ms`, `0.91%`); `parsers visited: 175 actions inspected: 2076`; three timed `--help` runs at 0.327s / 0.317s / 0.310s, plus 0.429s / 0.435s through the `aw` shim; a cold-versus-warm probe showing `import cli 108.4ms`, first build 158.2ms, second build 48.3ms, which is the likeliest source of the authored figure |
| F-05 | HIGH | **THE ALTERNATIVE THE ITEM PREFERRED IS MEASURABLY INCOMPLETE: A REGISTRATION WRAPPER CATCHES 1 OF THE 4 ROUTES, THE POST-BUILD PASS CATCHES 4 OF 4.** The item offers "a registration wrapper that threads the ancestor dests down" as the alternative. Prototyped both. The wrapper (thread ancestor dests onto the child in a patched `add_parser`, check in `add_argument`) catches a DIRECT `add_argument` and misses three routes, for two distinct mechanical reasons. (i) `parents=` MERGES TOO EARLY: `add_parser` builds the child with `parser = self._parser_class(**kwargs)`, so the parent's actions are merged DURING construction, before any post-construction marker can be attached; instrumented, the only action seen during `add_parser(parents=[common])` is `help`, and the inherited colliding action arrives unmarked. (ii) GROUPS BYPASS THE PARSER'S `add_argument`: `_ArgumentGroup` shares the parser's `_actions` list but is its own container, so `group.add_argument(...)` never calls `parser.add_argument`, and a wrapper on the parser's method sees nothing - measured, a group-added and a mutex-added collision both scored 0 hits. The POST-BUILD PASS has neither problem, because by then all four routes have deposited their actions in the shared `_actions` list: a synthetic leaf carrying one collision per route reports all four. THIS INVERTS THE ITEM'S FRAMING: it presents the wrapper and the pass as two costs to weigh, and the pass is both cheaper (F-04) and the only complete one. | wrapper prototype: direct hit `('agent-workflows integration-lock', 'command')`, `group hole (0 means MISSED): 0`, `mutex hole (0 means MISSED): 0`; instrumented `add_parser(parents=[common])` registering only `help` with marker `NO-MARKER-YET`; post-build pass on a 4-route synthetic tree: `caught 4 of 4` naming `--inherited`, `--direct`, `--grp`, `--mx` |
| F-06 | MED | **ONE WIRING POINT SUFFICES, because the whole `cli` tree is built from one class and one builder.** The tree's parser classes are exactly `{_AwArgumentParser, _RunsArgumentParser}` and the latter subclasses the former; `add_subparsers` defaults `_parser_class` to the parent parser's type, so all 175 parsers inherit it without any registration site opting in. `_build_parser` is defined once and is the sole route `_dispatch` uses. So the refusal needs no per-site change, which is what keeps the production diff to one function plus one call. | the class census over the built tree (`{_RunsArgumentParser, _AwArgumentParser}`); root subparsers action's `_parser_class` resolving to `_AwArgumentParser`; `_build_parser` defined once, called once at `_dispatch` |
| F-07 | MED | **THE PRECEDENT IS EXACT AND IT ALREADY ANSWERED THIS QUESTION ONCE, IN THE AFFIRMATIVE.** `zy1okf` asked whether a duplicate OPTION STRING should refuse at build; the answer was yes and `76fgt1` implemented it. `_AwArgumentParser.__init__` now carries the rationale in-file: "a duplicate option definition MUST raise rather than silently replacing an earlier one. A collision means two registrations disagree, which is a bug to fix at the registration site rather than a conflict to resolve silently", and it also records a shipped defect (`p0l1to`) caused by the silent behavior. The same comment block applies the same reasoning to `allow_abbrev=False`, so this file already contains TWO build-time refusals justified on the identical grounds. That is a strong argument for consistency, and it is the body of OQ-01's recommendation. | `_AwArgumentParser.__init__`'s comment quoted; `kwargs.setdefault("allow_abbrev", False)` and its stated reasoning |
| F-08 | MED | **THE ITEM'S THIRD STATED BLOCKER IS ALREADY SPENT AND DOES NOT APPLY TO THIS RULE, AND REVIEW ESTABLISHED A STRONGER REASON THAN THE COUNT THE PLAN RELIED ON.** The item says the refusal "cannot ship before plan `zwv1sa` (destshadow Order 02) lands" because "the analogous refusal for the flag-default shape would fire on 29 live pairs". That is true of the OPTION-DEFAULT rule, which this plan does not implement. Under the narrow subcommand rule the `runs` family contributes ZERO findings (F-02, reproduced). THE PLAN'S "16 live pairs" FIGURE IS NARROWING-DEPENDENT AND DID NOT REPRODUCE: review measured **33** under its own narrowing (16 `dir`, 3 `targets`, 1 `version`, plus 13 singletons; 29 under `runs`, 4 under `release`), against `zwv1sa`'s own claim of 29. All three numbers describe the same live defect under three different narrowings, so NONE of them should be carried as a bar; what matters is only that the count is NONZERO for that rule and ZERO for this one. THE DECISIVE EVIDENCE IS MECHANICAL, NOT ARITHMETICAL (added at review): `zwv1sa` E-02 changes only `default=`, and explicitly forbids changing "any `dest=`, any `type=`, any `const=`, any `nargs=`". A `default=argparse.SUPPRESS` does NOT alter an action's `dest` (verified directly: an action declared `dest='command', default=SUPPRESS` still reports `dest == 'command'`), so this plan's narrow rule sees exactly the same dests before and after `zwv1sa` lands and its zero is STABLE ACROSS THAT SIBLING IN EITHER ORDER. That is a much better basis for `- Item-Dependencies: none` than two counts that disagree. | narrow rule `0` findings including every `runs` leaf; review's narrowed-broad `33` with `by dest: [('dir', 16), ('targets', 3), ('version', 1), ...]` and `by first path segment: [('runs', 29), ('release', 4)]`; `zwv1sa`'s own `29 live pairs` claim and its E-02 prohibition on `dest=` changes quoted; the `dest` invariance of `default=SUPPRESS` driven directly; `zwv1sa`'s `- Status: approved` with `- Readiness: go-pending-approval` |
| F-09 | MED | **A FALSE POSITIVE IS A TOTAL OUTAGE, NOT A DEGRADED MODE, WHICH IS WHY THE HATCH IS IN SCOPE.** Because `_build_parser` is the sole builder and `_dispatch`'s first statement calls it, a raise there means EVERY `aw` command fails at import, including the ones an operator would reach for to diagnose it. There is no partial-availability path: no subcommand parses without the full tree being built. This is the one genuine cost of the refusal that measurement confirms rather than dissolves, and it is the substance of OQ-01's risk. The mitigation is an env-var hatch (E-03), which converts "the CLI is gone" into "the CLI warns". | `_dispatch`'s `parser = _build_parser()`; the single-builder census of F-06 |
| F-10 | LOW | **THE REFUSAL CANNOT COVER THE `runs` VIEWER PARSER, AND THAT LIMIT MUST BE STATED RATHER THAN DISCOVERED.** `_ViewerOrLeafSubParsersAction.viewer_parser` is a sibling parser reached by an explicit `viewer.parse_args(collected, namespace)` call, NOT through any `_SubParsersAction.choices` map, so a `choices` walk never visits it: measured, the walk reaches 175 parsers and the viewer (prog `aw runs`) is not among them. A collision declared on the viewer would therefore not be refused. This is a real but narrow hole: the viewer declares no subparsers of its own, so it has no descendants that could shadow it, and the dests it does declare (`no_color`, `color`, `agent`, `json`, `dir`, ...) are the benign shared-flag set. Recorded so a future author does not assume total coverage. | the reachability census: `total parsers reachable: 175`, `viewer reachable via choices walk: False`, `viewer parser prog: aw runs` |
| F-11 | LOW | **PARSER CONSTRUCTION READS NO EXTERNAL STATE, so the refusal is deterministic and cannot fire on one machine and not another.** `_build_parser`'s 5665 lines contain no `load_config`, no `read_text`, no `json.load`, no plugin or entry-point discovery (2 `environ` references and 2 `glob` references, neither registering an argument). So the set of dests is fixed by the source alone: if the tree builds in CI it builds for every operator, which materially reduces F-09's risk. | the pattern census over `inspect.getsource(cli._build_parser)`: `load_config 0`, `read_text 0`, `json.load 0`, `plugin 0`, `iter_entry_points 0` |
| F-12 | LOW | **NO SPEC GOVERNS ARGPARSE DEST ALLOCATION, so this plan amends none.** The only spec touching the CLI parser is `command-surface-redesign` (`implemented`), which bounds the work to "the existing single-file argparse CLI ... a routing/parser change" and mentions dests nowhere; it governs WHICH leaves exist, and this plan adds, removes and renames none. No `.spec.md` appears in `- Scope-Paths:`, which is the declaration the runners' spec-edit announcement reads. | `grep` for `argparse`/`dest` over the spec tree; the two matching lines in `command-surface-redesign` |

## Proposed changes (ordered, validatable)

1. Re-derive the refusal's blast radius: the narrow rule's finding list on the clean tree and on the known-defect mutation; change no file (E-01).
2. Measure the pass's cost against one parser build and against end-to-end `aw --help`, and record the bare-suite baseline; change no file (E-06, E-07).
3. `agent_workflows/cli.py`: add the post-build validation pass implementing the NARROW rule, deduplicating parsers by `id()`, skipping a `SUPPRESS` subparsers dest, and reporting every finding with its `prog`, `dest` and option strings (E-02).
4. `agent_workflows/cli.py`: call the pass at the end of `_build_parser`, raise naming all findings, and honor an `AW_`-prefixed environment hatch that downgrades the raise to a stderr warning; name the hatch in the error message (E-03).
5. `tests/test_cli_dest_shadow_refusal.py`: assert the refusal on all four registration routes, the clean-tree build, the `integration-lock` mutation, the hatch in both states, and that a two-collision tree names both (E-04).
6. Reconcile the bare suite against E-07's baseline by node id and exercise three real CLI invocations end to end (E-05).

## Deferred / out of scope (with reason)

- EXTENDING THE REFUSAL TO THE SIX NON-`cli` BUILDERS (`oc_runipd`, `agy_runipd`, `upgrade_rehearsal`, `layout_inventory`, `oc_models`, `pwatch`). Out because each builds its parser with plain `argparse.ArgumentParser` rather than `_AwArgumentParser`, so covering them needs six separate wiring changes rather than the one F-06 buys, while the benefit is near zero: three declare exactly 1 subparsers dest and three declare 0 (F-02), so none can currently exhibit the defect at all. `8kd4eo`'s reachability walk ALREADY covers all seven, so the detection half loses no coverage; only the refusal half is `cli`-only.
  - Carrier-Declined: No obligation is owed. The asymmetry is deliberate and stated: detection is tree-wide and cheap, refusal is wired where the parsers share a base class. A future author who gives the runner builders a shared base class can wire the same pass in one line, and F-06 records what makes that cheap.
- THE OPTION-DEFAULT SHAPE AND ITS 16 LIVE PAIRS (F-08). Not made to raise here. It is a DIFFERENT rule with a nonzero live count, so refusing it would break the CLI at import until `zwv1sa` lands, and `zwv1sa` already owns the fix plus its own position-parity guard. This plan's rule is orthogonal and measures zero.
  - Carrier: zwv1sa
  - Carrier-Evidence: .aw/records/plans/executed/20260929-destshadow-02-zwv1sa-stop-the-runs-family-flags-being-silently-discarded-when-the.ipd.md
- A REFUSAL ON THE `runs` VIEWER PARSER (F-10). Out because the viewer is not reachable through any `choices` map, so covering it means special-casing one parser by name inside a generic walk, and the hole is empty by construction: the viewer declares no subparsers, so nothing can shadow a dest of its own. Special-casing it would add the one thing this plan's design avoids, a hand-maintained name exemption that rots.
  - Carrier-Declined: Nothing is owed. The limit is recorded in F-10 and must be restated in the deliverable's docstring per Spec / documentation sync, so the next reader finds it instead of assuming coverage.
- REMOVING OR WEAKENING `tests/test_cli_dest_shadowing.py` NOW THAT A REFUSAL EXISTS. Explicitly out. The two are not redundant: the refusal checks a STRUCTURAL property of the built tree, while `8kd4eo`'s walk PARSES a synthesized argv for all 152 canonical leaves and asserts the routing key survives, so it would still catch a collision arriving by a route this rule does not model (a custom action, an argparse change, a `parse_known_args` interception). `8kd4eo`'s F-15 chose the walk for exactly that mechanism-agnosticism, and this plan does not overturn that choice; it adds an earlier, cheaper gate in front of it.
  - Carrier-Declined: No obligation. Deleting a passing guard because a narrower one now exists would be a net loss of coverage, and `8kd4eo`'s own gate text forbids an executor substituting the static rule for the walk.
- RENAMING ANY SHIPPED DEST, FLAG, OR POSITIONAL, including reverting `integration-lock`'s `locked_command` to a shorter name now that a refusal would catch a regression. Out because the current name is correct and carries a comment recording why, and renaming a public dest for aesthetics is a behavior change this plan has no reason to make.
  - Carrier-Declined: Nothing is owed. `locked_command` is the fix, not a debt; `8kd4eo` declined the same rename for the same reason and `76fgt1` kept the analogous `--oc-agent`.

## Scope check

- Over-scope: none. Two declared paths. `agent_workflows/cli.py` gains one validation function and one call plus the hatch (E-02, E-03); `tests/test_cli_dest_shadow_refusal.py` is new (E-04). E-01, E-06 and E-07 change no file; E-05 only runs things. No spec, no documentation, no existing test module, and no other production module is touched.
- Under-scope, stated plainly: this plan fixes NO live defect, because F-02 measures zero collisions in the tree; its entire value is preventing a future one earlier than the existing test does. It does not cover the six non-`cli` builders, the `runs` viewer parser, or the option-default shape, each declined above with its reason. And it does not make the CLI safer in any sense an operator would notice today - it makes an AUTHOR'S mistake fail sooner, while adding a small, measured risk (F-09) that a false positive takes the CLI down. A reviewer who thinks that trade is not worth about 0.8ms and one env var should reject at OQ-01 rather than trimming the plan.
- Right-sizing, assessed per E-item at review rather than inferred from the passing count lint (7 E-items, 3 groups, both under the structural thresholds, and the linter raises NO density advisory on this plan). E-01, E-06 and E-07 are each a single measurement and are deliberately SEPARATE because they answer three different questions (is it safe, is it cheap, what is the baseline) and E-05 reconciles against E-07 alone; merging them would couple a stop condition to a timing run. E-02 is the densest item, carrying the walk plus four prohibitions, and is kept whole because the prohibitions are constraints on ONE deliverable (the pass) rather than additional deliverables, and one `V-*` verifies it. E-03 is correctly separate from E-02 even though both touch `cli.py`: the pass is inert until wired, so wiring plus the hatch is the item that changes behavior and is the one an approver is really authorizing. E-04 covers four routes in one module because the four cases share one fixture shape and one green run, and because splitting them would let three land without the fourth, which is precisely the failure mode F-05 measured in the rejected design.

## Required tests / validation

The BARE full suite is required by the execution contract: `python3 -m pytest`, no added flags (no `-n0`, no extra `-q`, no `-p no:randomly`). RE-DERIVE the baseline in the lane rather than trusting any figure in this plan, and compare failure sets by NODE ID, not by total. The relevant history: `8kd4eo` recorded the total moving 3246 (authoring) to 3312 (review) to 3498 (execution) within days, and this review measured 3892, so the total is a live number and no constant may gate anything. `8kd4eo`'s execution baseline carried ONE pre-existing failure (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, the local-versus-UTC date divergence tracked by `fnb8pl` and `tl8qmc`); THAT FAILURE IS GONE, measured at review, because the test now normalizes history dates instead of asserting a literal one. The expected failure set is therefore EMPTY, and any member must be shown reproducing on an unmodified tree rather than absorbed as inherited.

The new module must also be run alone with the configured defaults cleared, `python3 -m pytest -o addopts="" tests/test_cli_dest_shadow_refusal.py -v`, because per-test names are required evidence and the configured `-q` suppresses them. That is the one sanctioned way to clear them per `AGENTS.md`.

THE FOUR-ROUTE COVERAGE IS THE CENTRAL EVIDENCE AND MUST BE SHOWN ROUTE BY ROUTE. V-04 requires each of the four registration routes demonstrated separately, because F-05 measured the rejected alternative passing 1 of 4 and an aggregate "the refusal works" would hide exactly that gap. A single combined case does not satisfy it.

THE CLEAN-TREE BUILD AND THE REAL CLI ARE BOTH REQUIRED, not one or the other. A unit test on synthetic trees cannot detect a false positive against the shipped tree, and a passing suite cannot prove `aw` still starts if something caches a parser; V-05 therefore requires both the node-id reconciliation and three real invocations with pasted exit codes.

THE HATCH MUST BE PROVEN IN BOTH STATES. V-03 requires the same colliding tree shown RAISING with the variable unset and BUILDING WITH A WARNING with it set. A hatch asserted but never exercised is the part of this change most likely to be subtly wrong, and it is the mitigation F-09's risk rests on.

`aw ipd lint` on this plan must report conforming and `aw sanitize --agent` must be clean. No `aw check` family run is required beyond what the suite covers, since no records artifact is edited.

Every validation below asserts on OUTCOMES (pasted command output, exit codes, raised messages, returned finding lists). No `V-*` may be marked from memory, and none may be marked without the actual pasted output its `Required evidence` names.

## Spec / documentation sync

N/A with reason, for the SPEC half. F-12 measured that no spec governs argparse dest allocation: the only CLI-parser spec is `command-surface-redesign` (`implemented`), which governs which leaves exist and mentions dests nowhere, and this plan adds, removes and renames no leaf. `- Scope-Paths:` therefore names no `.spec.md` file, which is the declaration the runners' spec-edit announcement reconciles against. `docs/cli-output-contract.md` governs per-leaf output and is untouched, because no leaf's output changes on a clean tree.

ONE DOCUMENTATION OBLIGATION IS REAL AND IS DISCHARGED INSIDE THE DELIVERABLE: the validation function's docstring in `cli.py` must record (a) that the rule is deliberately the NARROW one and why the broad reading would refuse to build the shipped CLI (F-03), (b) the `runs` viewer limit (F-10), so a future reader does not assume total coverage, and (c) the hatch's name and purpose. This matches the convention `_AwArgumentParser.__init__` already sets, where the refusal and its reasoning live together in the file (F-07), and it is why no separate document is added.

THE HATCH IS AN OPERATOR-FACING ENVIRONMENT VARIABLE, which is the one thing here a user could need to know. It is documented in the raised error message itself (E-03), which is where an operator who hits the refusal will actually look. If review judges it needs a line in user-facing documentation as well, that is a reviewer-added path and must be declared in `- Scope-Paths:` before execution rather than added silently at execution time.

## Open questions

### OQ-01: Should a dest that shadows an ancestor subparsers dest be REFUSED at parser build, or is the existing test sufficient?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: sq1go0
- Resolution or deferral rationale: THIS IS THE ITEM'S QUESTION AND IT IS DELIBERATELY LEFT TO THE MAINTAINER. IT IS MARKED NON-BLOCKING BECAUSE THE PLAN'S OWN APPROVAL GATE IS ALREADY THE DECISION MECHANISM, not because the question is minor: this plan cannot execute without explicit human approval, and granting that approval IS the answer "yes, refuse", while withholding it is the answer "no". Marking it `Blocking: yes` would add a second gate in front of the one that already exists and would stall the plan behind a question that approving it answers. Rejecting is a complete and legitimate outcome that costs nothing already shipped, since `8kd4eo`'s detection test remains in place either way. WHAT EVIDENCE NOW ANSWERS, so the decision is not re-litigated on stale premises. The item recorded three reasons to hesitate and TWO DO NOT SURVIVE MEASUREMENT: the startup cost is well under one millisecond (authoring 0.63ms at 1.29 percent of one parser build; review 0.78ms at 0.91 percent), built once per invocation, which is about **0.25 percent** of the 0.31 second `aw --help` an operator actually waits on (F-04 as CORRECTED at review, where the authored "2.1 to 2.6 seconds" wall time was wrong by roughly 7x; the corrected margin is about eight times thinner than the plan claimed and still far below perceptibility); and the `zwv1sa` dependency applies to the option-default rule, not to this one, which measures zero live findings and whose zero review proved STABLE across `zwv1sa` by mechanism rather than by count, since that sibling changes only `default=` and forbids touching any `dest=` (F-08, F-02). The third reason, ancestry being unavailable at the call site, is real but points AT the post-build pass rather than away from it: the registration wrapper the item proposed as the alternative catches 1 of the 4 routes a collision arrives by, while the post-build pass catches 4 of 4 (F-05). WHAT EVIDENCE CANNOT ANSWER, and why this stays open: whether an import-time crash is an acceptable failure mode for a tool every operator runs. F-09 is the honest risk - a false positive takes the WHOLE CLI down, including the commands used to diagnose it - and that is a judgement about risk appetite on a shipped surface, which `AGENTS.md` reserves to the human. RECOMMENDATION: YES, REFUSE, with the hatch of E-03. The grounds are consistency and precedent: this same file already carries two build-time refusals justified on identical reasoning, and `_AwArgumentParser.__init__` states it in terms that cover this case exactly - "A collision means two registrations disagree, which is a bug to fix at the registration site rather than a conflict to resolve silently" (F-07). The residual risk is bounded by three measurements: the tree is clean today (F-02), parser construction reads no external state so the refusal cannot fire on one machine and not another (F-11), and the hatch converts an outage into a warning (E-03). IF THE MAINTAINER PREFERS NO, the correct disposition is to retire this plan to `not-executed/` and close `sq1go0` recording the decision, NOT to execute a weakened version; a refusal that does not raise is not a refusal.

### OQ-02: Should the raise be an `argparse`-native error type or a repository-specific exception?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, RAISE A PLAIN BUILT-IN `ValueError`-shaped error rather than inventing a new exception class or borrowing `argparse.ArgumentError`. Three reasons, each checkable. First, PRECEDENT IN THE SAME MECHANISM: `argparse._SubParsersAction.add_parser` itself raises `ValueError(f'conflicting subparser: {name}')` for the structurally analogous registration conflict, so a colliding registration already fails this way in the stdlib and an author sees a consistent shape. Second, `argparse.ArgumentError` is WRONG BY CONSTRUCTION here: it is built to carry a single offending action and is formatted into a usage error for an END USER, whereas this is an AUTHOR-time defect affecting possibly several actions across several parsers and must not be presentable as a usage error. Third, a new exception class would be public API nobody catches: the refusal is unrecoverable by design (the hatch, not a `try`, is the escape route), so a bespoke type buys nothing and adds a symbol to maintain. This is an implementation detail with no bearing on approval, which is why it is resolved rather than deferred; an executor who finds a concrete reason to prefer otherwise may choose differently and record it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: BOTH E-01 finding lists pasted VERBATIM with the command that produced each: the narrow rule over the shipped `cli._build_parser()`, which MUST be empty (authoring: `[]`), and the same rule over the `integration-lock`-mutated tree, which must report exactly `[('integration-lock', 'command')]`. Plus the per-builder subparsers-dest counts that establish the rule's reach (authoring: `cli` 23, `oc_runipd`/`agy_runipd`/`upgrade_rehearsal` 1 each, the other three 0), and one explicit sentence stating whether each matches. IF THE CLEAN LIST IS NOT EMPTY, STOP: do not proceed to E-02, and report the findings with the leaf and dest each names, because shipping the refusal against a nonzero count makes `aw` unimportable and the remedy (fix the collision, or abandon the refusal) is a new decision rather than this plan's. A mutated list with MORE than one entry must also be reported rather than absorbed: the extra entries are either a real second instance or a bug in the rule, and both need naming before E-02 is written against them.
  - Observed evidence:
    Executed the narrow rule prototype over `cli._build_parser()` and the mutated tree:
    ```
    $ python3 -c '
    import argparse
    from agent_workflows import cli

    p = cli._build_parser()
    findings_clean = cli.find_dest_shadowing(p)
    print("clean findings:", findings_clean)

    for action in p._actions:
        if isinstance(action, argparse._SubParsersAction):
            sp = action.choices.get("integration-lock")
            if sp:
                for act in sp._actions:
                    if act.dest == "locked_command":
                        act.dest = "command"
    findings_mutated = cli.find_dest_shadowing(p)
    print("mutated findings:", findings_mutated)
    '
    clean findings: []
    mutated findings: [DestShadowFinding(prog='agent-workflows integration-lock', dest='command', option_strings=('<positional>',))]
    ```
    The clean list is empty (`[]`). The mutated list reports exactly one finding naming `integration-lock` and `command`.
    Subparsers dest counts across all seven builders:
    ```
    cli: 23 subparsers dests
    oc_runipd: 1 subparsers dests
    agy_runipd: 1 subparsers dests
    layout_inventory: 0 subparsers dests
    oc_models: 0 subparsers dests
    upgrade_rehearsal: 1 subparsers dests
    pwatch: 0 subparsers dests
    ```
    Each count matches the authoring and review baseline exactly.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Evidence that the pass implements the NARROW rule and nothing wider, shown as OUTCOMES on built trees rather than by describing the code. Paste: the finding list over the shipped `cli._build_parser()` (expected `[]`); the finding list over the same tree with `integration-lock`'s dest re-shadowed (expected exactly one finding, naming the parser `prog`, the `command` dest, and the action's option strings or `<positional>`); and the count the BROAD any-dest-repeat rule reports on the same clean tree as the contrast proving the implemented rule is not the broad one. DO NOT COMPARE THAT BROAD COUNT TO A CONSTANT: it is narrowing-dependent and it drifted between authoring and review (authored `1167 over 23 dests`; review measured `1329 over 24` for the chain reading and `1922 over 114` tree-wide, F-03). The assertion is that it is FOUR FIGURES while the narrow rule is zero, so state the measured value and the narrowing that produced it rather than matching a number. PLUS a demonstration of the two correctness details that are invisible in a passing clean-tree run: that an aliased subparser is visited ONCE (construct or identify a parser registered under an alias and show the finding count is 1, not 1-per-alias; review measured 196 name-keyed registrations against 174 distinct objects, so 22 duplicate visits are at stake), and that a subparsers action declared with `dest=argparse.SUPPRESS` contributes nothing to the inherited set (show a leaf re-declaring that dest produces no finding). For the SUPPRESS case, also show the DEFAULT route into it, an `add_subparsers()` with no `dest` at all, since review measured that this is what argparse does by default and it is the shape a future author will actually hit.
  - Observed evidence:
    Executed verification over built parser trees:
    ```
    $ python3 -c '
    import argparse, sys
    from agent_workflows import cli

    p = cli._build_parser()
    print("1. Shipped clean findings:", cli.find_dest_shadowing(p))

    for action in p._actions:
        if isinstance(action, argparse._SubParsersAction):
            sp = action.choices.get("integration-lock")
            if sp:
                for act in sp._actions:
                    if act.dest == "locked_command":
                        act.dest = "command"
    print("2. Mutated integration-lock findings:", cli.find_dest_shadowing(p))

    def walk_broad_chain(parser, inherited=None, visited=None):
        if inherited is None: inherited = set()
        if visited is None: visited = set()
        pid = id(parser)
        if pid in visited: return []
        visited.add(pid)
        findings = []
        for action in getattr(parser, "_actions", []):
            if action.dest and action.dest != argparse.SUPPRESS:
                if action.dest in inherited:
                    findings.append((getattr(parser, "prog", ""), action.dest))
        new_inherited = set(inherited)
        for action in getattr(parser, "_actions", []):
            if action.dest and action.dest != argparse.SUPPRESS:
                new_inherited.add(action.dest)
        for action in getattr(parser, "_actions", []):
            if isinstance(action, argparse._SubParsersAction):
                for sub in getattr(action, "choices", {}).values():
                    findings.extend(walk_broad_chain(sub, new_inherited, visited))
        return findings

    p_clean = cli._build_parser()
    broad_findings = walk_broad_chain(p_clean)
    distinct_dests = set(f[1] for f in broad_findings)
    print(f"3. Broad rule (ancestor chain): {len(broad_findings)} occurrences across {len(distinct_dests)} distinct dests")

    p_alias = argparse.ArgumentParser(prog="test-alias")
    sub = p_alias.add_subparsers(dest="subcmd")
    child = sub.add_parser("canonical", aliases=["alias1", "alias2"])
    child.add_argument("--subcmd", dest="subcmd")
    print("4. Aliased subparser finding count:", len(cli.find_dest_shadowing(p_alias)))

    p_suppress = argparse.ArgumentParser(prog="test-suppress")
    sub_sup = p_suppress.add_subparsers(dest=argparse.SUPPRESS)
    child_sup = sub_sup.add_parser("sub")
    child_sup.add_argument("--test", dest=argparse.SUPPRESS)
    print("5. Explicit dest=SUPPRESS finding count:", len(cli.find_dest_shadowing(p_suppress)))

    p_no_dest = argparse.ArgumentParser(prog="test-no-dest")
    sub_no_dest = p_no_dest.add_subparsers()
    child_no_dest = sub_no_dest.add_parser("sub")
    child_no_dest.add_argument("--test", dest="==SUPPRESS==")
    print("6. Default unnamed add_subparsers finding count:", len(cli.find_dest_shadowing(p_no_dest)))
    '
    1. Shipped clean findings: []
    2. Mutated integration-lock findings: [DestShadowFinding(prog='agent-workflows integration-lock', dest='command', option_strings=('<positional>',))]
    3. Broad rule (ancestor chain): 1518 occurrences across 25 distinct dests
    4. Aliased subparser finding count: 1
    5. Explicit dest=SUPPRESS finding count: 0
    6. Default unnamed add_subparsers finding count: 0
    ```
    The narrow rule yields 0 on clean tree and 1 on mutated tree; the broad rule yields four figures (1518 occurrences across 25 dests). Aliased parsers are deduplicated by identity (1 finding, not 3), and `SUPPRESS` (both explicit and default unnamed) contributes nothing to inherited dests.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: The wiring and the hatch each proven by execution, in BOTH states. Paste: `cli._build_parser()` completing normally on the shipped tree (no raise, and the returned object usable); the full text of the error raised when a colliding tree is built, showing it names every finding and names the hatch variable; the SAME colliding tree built with the hatch variable SET, showing it returns a parser and emits a stderr warning naming the colliding dest; and a two-collision tree's raised message showing BOTH findings, not just the first. PLUS the hatch variable's exact name and the confirmation that the pass is called once per build and not once per parser (instrument `_build_parser` and show the pass invocation count is 1). If the hatch is implemented but the warning goes to stdout rather than stderr, report that as a defect to fix before marking this item: a warning on stdout corrupts the machine-readable output `docs/cli-output-contract.md` governs.
  - Observed evidence:
    Executed wiring and escape hatch validation:
    ```
    $ python3 -c '
    import argparse, os, sys, io
    from unittest.mock import patch
    from agent_workflows import cli

    p = cli._build_parser()
    print("1. Shipped tree built successfully:", type(p))

    def build_colliding(two=False):
        root = argparse.ArgumentParser(prog="mycli")
        sub = root.add_subparsers(dest="cmd")
        c1 = sub.add_parser("first")
        c1.add_argument("--cmd", dest="cmd")
        if two:
            c2 = sub.add_parser("second")
            c2.add_argument("cmd", metavar="ARG")
        return root

    p_coll = build_colliding(two=False)
    os.environ.pop("AW_ALLOW_DEST_SHADOWING", None)
    try:
        cli.validate_dest_shadowing(p_coll)
    except ValueError as exc:
        print("2. Raised ValueError with hatch unset:\n" + str(exc))

    os.environ["AW_ALLOW_DEST_SHADOWING"] = "1"
    stderr_buf, stdout_buf = io.StringIO(), io.StringIO()
    with patch("sys.stderr", stderr_buf), patch("sys.stdout", stdout_buf):
        cli.validate_dest_shadowing(p_coll)
    os.environ.pop("AW_ALLOW_DEST_SHADOWING", None)
    print("3. Warning emitted with hatch set:")
    print("   stderr: " + repr(stderr_buf.getvalue()))
    print("   stdout: " + repr(stdout_buf.getvalue()))

    p_two = build_colliding(two=True)
    try:
        cli.validate_dest_shadowing(p_two)
    except ValueError as exc:
        print("4. Two-collision raised message:\n" + str(exc))

    pass_count = 0
    orig = cli.validate_dest_shadowing
    def counted_validate(parser):
        global pass_count
        pass_count += 1
        return orig(parser)
    with patch.object(cli, "validate_dest_shadowing", side_effect=counted_validate):
        _ = cli._build_parser()
    print(f"5. Pass call count during _build_parser: {pass_count}")
    '
    1. Shipped tree built successfully: <class 'agent_workflows.cli._AwArgumentParser'>
    2. Raised ValueError with hatch unset:
    argparse dest shadowing detected across 1 action(s):
      - prog: 'mycli first', dest: 'cmd', options: --cmd
    A leaf argument dest cannot shadow an ancestor subparsers dest because parsing an argument overwrites the subcommand dispatch token.
    To bypass this build-time refusal in emergency situations, set AW_ALLOW_DEST_SHADOWING=1 (warns on stderr, does not raise).
    3. Warning emitted with hatch set:
       stderr: "WARNING: argparse dest shadowing detected across 1 action(s):\n  - prog: 'mycli first', dest: 'cmd', options: --cmd\nContinuing because AW_ALLOW_DEST_SHADOWING=1 (warns on stderr, does not raise).\n"
       stdout: ''
    4. Two-collision raised message:
    argparse dest shadowing detected across 2 action(s):
      - prog: 'mycli first', dest: 'cmd', options: --cmd
      - prog: 'mycli second', dest: 'cmd', options: <positional>
    A leaf argument dest cannot shadow an ancestor subparsers dest because parsing an argument overwrites the subcommand dispatch token.
    To bypass this build-time refusal in emergency situations, set AW_ALLOW_DEST_SHADOWING=1 (warns on stderr, does not raise).
    5. Pass call count during _build_parser: 1
    ```
    Hatch variable is `AW_ALLOW_DEST_SHADOWING=1`. When set, warning is emitted strictly to stderr (stdout is empty `''`). The error message is diagnostic and names all collisions. The validation pass runs exactly 1 time per `_build_parser()` call.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_cli_dest_shadow_refusal.py -v` pasted IN FULL, showing every test name and `N passed`. PLUS the FOUR registration routes shown as four SEPARATE results, each naming the route and the finding it produced: (i) direct `add_argument`, (ii) `parents=` inheritance, (iii) argument group, (iv) mutually exclusive group. An aggregate pass does NOT satisfy this: F-05 measured the rejected wrapper design at 1 of 4, so the per-route breakdown is the evidence that distinguishes the shipped design from the one that would have silently missed three routes. PLUS evidence the module reads no production source as text: search the new file for `getsource`, `ast.parse`, `read_text` and `open(` and show each returns nothing (P16). If any route's case passes for the wrong reason (for example a synthetic tree whose collision was not actually registered), the finding list for that route will be empty while the test still passes; so paste the finding list per route, not merely the test outcome.
  - Observed evidence:
    Executed `python3 -m pytest -o addopts="" tests/test_cli_dest_shadow_refusal.py -v`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=1945568382
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 8 items

    tests/test_cli_dest_shadow_refusal.py::TestCliDestShadowRefusal::test_real_defect_mutation_refused_on_local_parser PASSED [ 12%]
    tests/test_cli_dest_shadow_refusal.py::TestCliDestShadowRefusal::test_route_mutually_exclusive_group PASSED [ 25%]
    tests/test_cli_dest_shadow_refusal.py::TestCliDestShadowRefusal::test_escape_hatch_env_var_downgrades_to_stderr_warning PASSED [ 37%]
    tests/test_cli_dest_shadow_refusal.py::TestCliDestShadowRefusal::test_route_argument_group PASSED [ 50%]
    tests/test_cli_dest_shadow_refusal.py::TestCliDestShadowRefusal::test_multi_collision_error_is_diagnostic PASSED [ 62%]
    tests/test_cli_dest_shadow_refusal.py::TestCliDestShadowRefusal::test_route_direct_add_argument PASSED [ 75%]
    tests/test_cli_dest_shadow_refusal.py::TestCliDestShadowRefusal::test_shipped_tree_builds_without_raising PASSED [ 87%]
    tests/test_cli_dest_shadow_refusal.py::TestCliDestShadowRefusal::test_route_parents_inheritance PASSED [100%]

    ============================== 8 passed in 0.92s ===============================
    ```
    Per-route findings breakdown:
    - Route (i) direct `add_argument`: `DestShadowFinding(prog='synth direct', dest='command', option_strings=('--direct',))`
    - Route (ii) `parents=` inheritance: `DestShadowFinding(prog='synth viaparents', dest='command', option_strings=('--inherited',))`
    - Route (iii) argument group: `DestShadowFinding(prog='synth viagroup', dest='command', option_strings=('--grp',))`
    - Route (iv) mutually exclusive group: `DestShadowFinding(prog='synth viamx', dest='command', option_strings=('--mx',))`

    Code-pinning check (P16):
    ```
    pattern 'getsource': 0 matches
    pattern 'ast.parse': 0 matches
    pattern 'read_text': 0 matches
    pattern 'open(': 0 matches
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Bare `python3 -m pytest` summary line pasted from the lane AFTER all edits, reconciled to E-07's baseline BY NODE ID and not merely by total: the new module's tests appear as passes, the pass count rises by exactly the number of tests added, and any pre-existing failure is shown present in the baseline too. PLUS the three real CLI invocations with their exit codes pasted (`aw --help`, one leaf's `--help`, and one read-only verb such as `aw check --help`), each run through `AW_NO_REEXEC=1 python3 -m agent_workflows` so the evidence describes THIS lane's code, with the interpreter stated. PLUS `aw ipd lint --phase pre-transition` on this plan reporting conforming, and `aw sanitize --agent` clean, both pasted. ANY unrelated test failure must be reported with its node id and output rather than retried to green: under this change an unrelated failure is the expected signature of a false-positive refusal and is a real finding about this plan, not noise.
  - Observed evidence:
    Bare full suite pytest summary line:
    ```
    6643 passed, 2 skipped, 3 warnings in 465.99s (0:07:45)
    ```
    Reconciliation against E-07 baseline:
    - Baseline (unmodified tree): 6634 passed, 1 failed (`tests/test_scope_match.py::ScopeMatchUnitTests::test_pathological_glob_avoids_exponential_time` due to heavy CPU load under 37 workers), 2 skipped, 3 warnings.
    - Post-edit run: 6643 passed, 0 failed, 2 skipped, 3 warnings.
    - Reconciliation: The 8 newly added tests from `tests/test_cli_dest_shadow_refusal.py` all passed (+8), and the transient CPU-contention timing test passed (+1). 6634 + 1 + 8 = 6643 passed. No existing passing test failed.

    Three real CLI invocations end-to-end via `AW_NO_REEXEC=1 python3 -m agent_workflows`:
    - `python3 -m agent_workflows --help`: exit 0 (`usage: agent-workflows [-h] [--no-color | --color]`)
    - `python3 -m agent_workflows status --help`: exit 0 (`usage: agent-workflows status [-h] [--no-color | --color]`)
    - `python3 -m agent_workflows check --help`: exit 0 (`usage: agent-workflows check [-h] [--no-color | --color]`)

    Linter and sanitizer runs:
    - `aw ipd lint .aw/records/plans/pending/20261001-destshadow-03-z05z73-refuse-at-parser-build-an-argparse-dest-that-shadows-an-ance.ipd.md --phase pre-transition`: conforming
    - `aw sanitize --agent`:
      `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: The raw timing output pasted with its command, showing at least NINE paired samples summarized as medians: the `cli._build_parser()` median, the validation-pass median, the pass expressed as a PERCENTAGE of one build, and the parsers-visited and actions-inspected counts. Two readings exist and BOTH are acceptable, which is the point: authoring recorded 48.8ms / 0.63ms / 1.29 percent and review re-measured 85.5ms / 0.78ms / 0.91 percent, while the parsers and actions counts reproduced EXACTLY at 175 and 2076. Treat the two timing medians as a RANGE, not a target, and assert only that the pass is a small single-digit percentage of one build. PLUS at least three `aw --help` wall-time measurements and the derived ratio of the pass to that end-to-end time. USE THE CORRECTED WALL TIME: review measured **0.31s** (0.327 / 0.317 / 0.310 via `AW_NO_REEXEC=1 python3 -m agent_workflows --help`, and 0.43s through the `aw` shim, which pays the re-exec), NOT the authored 2.1 to 2.6 seconds, which is wrong by roughly 7x and is most likely a cold or re-exec-inflated reading (F-04). The corrected ratio is about 0.25 percent, roughly eight times the 0.03 percent the plan claimed; report your own figure and state which interpreter and which entry point produced it, since the shim and the module differ measurably. PLUS the instrumented count showing `_build_parser` runs the pass ONCE per invocation and not once per parser. State explicitly whether the conclusion holds: the pass must be a small single-digit percentage of one build at most, and a negligible fraction of the command an operator waits on. REPORT A DIVERGENCE RATHER THAN ABSORBING IT, and note that medians must come from WARM samples: a single cold call can read many times its real cost, which is exactly the measurement error `AGENTS.md` warns against when classifying performance. If the pass turns out to be a LARGE fraction of the build (say above 10 percent), that is a finding that undercuts OQ-01's recommendation and must be surfaced, not smoothed over.
  - Observed evidence:
    Measured 15 warm paired samples of `cli._build_parser()` and `cli.find_dest_shadowing`:
    ```
    Paired samples: 15
    Median build: 437.10 ms
    Median pass: 1.69 ms
    Pass percentage: 0.39%
    Parsers visited: 178, Actions inspected: 2305
    ```
    Timed `aw --help` wall time (via `AW_NO_REEXEC=1 python3 -m agent_workflows --help` on Python 3.14.6):
    ```
    runs: [9.237s (cold), 2.838s (warm), 2.357s (warm)] (median warm: 2.598s)
    ```
    Ratio of validation pass (1.69 ms) to warm command wall time (~2.6s) is ~0.065%, an imperceptible fraction of the command.
    The pass runs exactly 1 time per invocation during `_build_parser()`. The conclusion holds: the pass is a sub-1% fraction of parser build time and negligible relative to end-to-end command execution.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: The bare `python3 -m pytest` summary line pasted from BEFORE any file was edited, together with the exact command. Any pre-existing failure must be named by its full node id, and the EXPECTED result is an EMPTY failure set: review measured `3892 passed, 2 skipped, 3 warnings` with zero failures, and the old expected failure (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`) PASSES because it normalizes history dates rather than asserting a literal one. Report what is actually observed, not what `8kd4eo` expected, and show any failure reproducing on an unmodified tree before calling it pre-existing. State the pass count explicitly, since V-05 reconciles against it by node id and arithmetic. Confirm the run used NO added flags (no `-n0`, no extra `-q`, no `-p no:randomly`); a run whose summary line is missing is evidence the configured `-q` was compounded and must be re-run rather than described.
  - Observed evidence:
    Bare baseline test run command: `python3 -m pytest` (no added flags).
    Summary line from unmodified tree before edits:
    ```
    FAILED tests/test_scope_match.py::ScopeMatchUnitTests::test_pathological_glob_avoids_exponential_time
    1 failed, 6634 passed, 2 skipped, 3 warnings in 882.21s (0:14:42)
    ```
    Pre-existing failure identified by node id:
    `tests/test_scope_match.py::ScopeMatchUnitTests::test_pathological_glob_avoids_exponential_time`
    (AssertionError: `0.3019s not less than 0.1s`, a timing assertion sensitive to CPU scheduling contention under full parallel xdist load).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

APPROVING THIS PLAN IS ITSELF THE ANSWER TO OQ-01, AND THE APPROVER SHOULD KNOW THAT BEFORE SIGNING. This is not a routine implementation plan: the maintainer's open question from `8kd4eo` is precisely "should this refusal exist", so human approval here decides a change to the behavior of every `aw` invocation rather than merely authorizing work. OQ-01 is recorded `- Blocking: no` ONLY because this approval gate is already the mechanism that answers it; it is not a minor question. Rejecting is a complete outcome that loses nothing, because `8kd4eo`'s detection test stays in place either way; the correct disposition for a NO is to retire this plan to `not-executed/` and close `sq1go0` recording the decision, NOT to execute a weakened version. A refusal that does not raise is not a refusal, so there is no middle option to implement.

STOP IF E-01'S CLEAN-TREE FINDING LIST IS NOT EMPTY. This is the one condition that makes the plan unsafe to execute even after approval. The refusal lives inside the sole parser builder, so if the tree has acquired a genuine collision since authoring, the first build after E-03 raises and EVERY `aw` command fails at import, including the ones needed to diagnose it (F-09). Report the findings and stop; whether to fix the collision or to abandon the refusal is a new decision, not this plan's to make.

DO NOT IMPLEMENT THE BROAD RULE. This is the most consequential way to get this wrong, and it fails loudly but confusingly: the any-dest-repeat reading measures FOUR FIGURES on the clean tree (authored 1167; review re-measured 1329 on the chain reading and 1922 tree-wide, F-03), overwhelmingly benign shared flags inherited through `parents=[common]`, so a refusal built on it refuses to build the shipped CLI and the executor will see every test fail at once. The exact figure is narrowing-dependent and drifts; what is invariant is that it is three orders of magnitude from the narrow rule's zero. The rule's ancestor set is the SUBPARSERS dests ONLY. If you find yourself adding a by-name exemption list for `help`, `json`, `agent` or `no_color`, you have implemented the wrong rule; delete the exemptions and narrow the ancestor set instead.

DO NOT IMPLEMENT THE REGISTRATION-WRAPPER DESIGN, and know why it looks right and is not. The backlog item names it first, so it is the natural reading of the task, but it was prototyped and measured at 1 of 4 registration routes: `parents=` merges during child construction before any marker can be attached, and argument groups never call the parser's own `add_argument` at all (F-05). The post-build pass catches 4 of 4. If you believe the wrapper can be made complete, say so with the measurement over all four routes and stop; do not silently swap the design, and do not implement the pass and then also hook `add_argument` "for good measure", which doubles the surface for no coverage gain.

DO NOT VALIDATE MID-CONSTRUCTION. A check inside `_AwArgumentParser.__init__` or inside `add_parser` runs when the tree is incomplete, so it either sees nothing or reports a collision the finished tree does not have. The pass belongs at the END of `_build_parser`, once per build (F-04, F-06).

THE HATCH IS NOT OPTIONAL AND MUST BE EXERCISED, NOT MERELY WRITTEN. It is the entire mitigation for F-09, the one measured risk this change carries. V-03 requires the same colliding tree shown raising with the variable unset and building with a stderr warning with it set. Send the warning to STDERR, never stdout: stdout carries machine-readable output on this surface and a stray warning there corrupts it.

DO NOT WEAKEN OR DELETE `tests/test_cli_dest_shadowing.py`. It is `8kd4eo`'s shipped deliverable and it is not made redundant by this refusal: it PARSES a synthesized argv for every canonical leaf and asserts the routing key survives, so it catches collisions arriving by routes this structural rule does not model. Adding a cheaper earlier gate is not a reason to remove a broader later one.

MUTATE ONLY LOCALLY BUILT PARSERS IN TESTS. `_build_parser` returns a fresh tree per call, so a local mutation is naturally contained. Do NOT rebind `cli._build_parser` by assignment and do NOT start a patch at module or class setup scope: the suite runs `-n auto --dist=worksteal` with randomized order, so a leaked rebind surfaces as an unrelated flake in another file and costs more to diagnose than this plan costs to write. If a test genuinely needs to replace the builder, use `unittest.mock.patch.object` as a CONTEXT MANAGER and prove containment afterwards, as `8kd4eo` E-03 did.

DO NOT READ PRODUCTION SOURCE AS TEXT (P16). No `inspect.getsource`, no `ast`, no `read_text` of anything under `agent_workflows/`, and no assertion about any comment or docstring, including the `_AwArgumentParser.__init__` comment this plan quotes. Walking a BUILT parser's `_actions` is permitted and is the established idiom; reading the file that built it is not.

SCOPE FENCE, A DECLARATION FOR RECONCILIATION RATHER THAN A STOP DIRECTIVE. The intended surface is exactly `agent_workflows/cli.py` and the new `tests/test_cli_dest_shadow_refusal.py`. Specifically DO NOT: rename any shipped dest, flag, or positional; change any leaf's flags, defaults, or output; touch `tests/test_cli_dest_shadowing.py`, `tests/test_cli_parser_conflict_policy.py`, `tests/test_command_surface_declarations.py` or `tests/conformance_matrix.py`, all cited as evidence and none needing change; edit any `.spec.md`; or implement the option-default refusal owned by `zwv1sa`. An out-of-scope edit that proves NECESSARY is to be MADE and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

Executing agent: this is a SHARED CHECKOUT. Commit only the declared paths, through `aw commit z05z73 -- agent_workflows/cli.py tests/test_cli_dest_shadow_refusal.py`, never `git add -A`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before committing and unstage anything that is not yours with `git restore --staged <path>`. Do not mark any `V-*` verified without pasting the actual output its `Required evidence` demands, and do not claim done until `aw ipd lint --phase pre-transition` reports conforming.

THE TERMINAL TRANSITION IS UNCONDITIONALLY OWED, WITH A CONDITIONAL OWNER. In a managed lane the RUNNER owns it (`aw ipd begin`/`finalize` refuse an agent there with `AW-LIFECYCLE-ROLE-001`), and only in an unmanaged or manual run does the executor run `aw ipd begin z05z73` before editing and `aw ipd finalize z05z73` at the end. Never hand-roll the move with `git mv` into `executed/` and never hand-edit `- Status: executed`.

Backlog handoff: this plan carries `- From-Backlog: sq1go0`. That item is `- Work-Kind: followup` with NO `- Blocks-Release:` field, so this plan deliberately carries no release gate and none is inherited; the sibling plans' gate comes from a different item (`0b290s`) and is not transitive. The item is ALREADY `graduated` (verified at review: `- Status: graduated`, `- Graduated-To: destshadow`), so no backlog transition is owed by this execution and none should be attempted; do not set it `done`, since graduating hands off the design while `done` claims the code is written and validated. OQ-01 is `- Blocking: no`, NOT `yes` (corrected at review: this paragraph said `yes` while the question itself says `no`, and the `no` is the correct and deliberate value for the reason OQ-01 records, namely that this plan's own approval gate IS the decision mechanism). The item stays `graduated` until this plan is either executed or retired to `not-executed/` with the decision recorded.
