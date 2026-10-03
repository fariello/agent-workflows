# IPD: Emit a conformant agent record from the bare aw upgrade-test group instead of an argparse usage block

- Date: 2026-10-02
- Kind: child
- Concern: `aw upgrade-test` WITH NO SUBCOMMAND WRITES 2059 BYTES OF ARGPARSE HELP TO STDOUT AND EXITS 2, ON THE `--agent` SURFACE AS WELL AS THE HUMAN ONE, while `command_surface.COMMAND_INVENTORY` declares that same command `agent_record_kind="result"`, `command_class="read"`, `human_recipe="status"`, `exit_contract=(0, 1, 2)`. Every one of those four values is false about the shipped behavior: no record of any kind is emitted, nothing is read, no status is rendered, and exit 0 and 1 are both unreachable. The cost is concrete and falls on automation: a caller that passes `--agent` and parses stdout as JSONL gets a help page, so it cannot distinguish "this group needs a subcommand" from a crash, and the `exit` parity rule in `docs/cli-output-contract.md` Section 4 (which requires a record's embedded `exit` to equal the process exit code) has no record to apply to. This is not a latent mismatch: `aw upgrade-test` is the ONLY family root in the whole CLI that behaves this way while ALSO being declared, and 18 of the 21 other roots already emit a schema-valid `cannot-run` error record on the same bare invocation, so the correct behavior is already shipped 18 times over and this one site simply does not call it. The declaration was added by commit `648597285` (2026-09-26) when the harness graduated from `tools/aw_upgrade_test.py`; the handler's `print_help()` branch came with it. Filed by plan `f36de0`'s review (PR-203), which measured the usage block and refused to launder it into `EXEMPTION_REGISTRY`'s `sanctioned_raw` category, writing instead "if the executor judges a group-without-subcommand should emit an `error` record, that is a REAL defect ... NOT a `sanctioned_raw` entry that would launder it".
- Scope: IN: (1) replace the bespoke `print_help()`-then-`return 2` branch in `cli._dispatch`'s `upgrade-test` arm with the shared `cli._show_family_help` helper that the other 18 roots already use, so the `--agent` surface emits a schema-valid `cannot-run` error record and the human surface keeps its help page plus gains a next-action line; (2) DELETE the `upgrade-test` root declaration from `COMMAND_INVENTORY`, because a family root is not a parser leaf and `COMMAND_INVENTORY` declares leaves, which is why no other root is declared; (3) delete the now-dead `EXEMPTION_REGISTRY["upgrade-test"]` entry whose citation is this item; (4) add a behavioral test driving the bare group as a real subprocess on both surfaces. OUT: this plan does NOT change any of the six `upgrade-test` SUBCOMMANDS, their declarations, or `agent_workflows/upgrade_rehearsal.py`; it does NOT touch `tools/aw_upgrade_test.py`, whose own parser already uses `required=True`; it does NOT change `_show_family_help` itself, nor any other family root; it does NOT fix the two OTHER non-conforming roots this plan measured (`runs` and `config exclude`, see F-10, each handed off to a filed item); and it does NOT widen `agent_schema.VALID_OUTCOMES`, add a `command_class`, or change `required_scenarios`.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, tests/conformance_matrix.py, tests/test_aw_upgrade_test.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: lbbo9s
- Blocks-Release: next
- Set: lbbo9s
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 7pnneh
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Re-verified at lane HEAD f035f874c: defect reproduces (rc 2, 39 stdout lines on --agent), declaration present, EXEMPTION_REGISTRY 27, universe 42, declared_absent ['prompts set','upgrade-test']. Fixed: handler site is cli._dispatch not cli.main; --json parity with sibling roots stated and evidenced; registry and universe bars re-derived as before/after deltas since siblings vfv2db and gm9baj edit the same file; subprocess test pinned to cwd=REPO_ROOT and its convention citation corrected; OQ owners and lifecycle ownership fixed; CHANGELOG decision confirmed by git tag --contains. Review record: .aw/records/reviews/20261002-lbbo9s-01-7pnneh-emit-a-conformant-agent-record-from-the-bare-aw-upgrade-test.review.md.

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from open backlog item `lbbo9s`; every finding measured in lane `lbbo9s` at HEAD `b8e1e0157`.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the bare `aw upgrade-test` invocation answer a machine caller with the same schema-valid `cannot-run` error record that 18 other family roots already emit, and make its entry in the normative command inventory honest by removing a declaration that describes a leaf the parser does not have. Both halves are required: fixing only the handler would leave four false values in the inventory, and fixing only the declaration would leave the machine surface silent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: make the bare group answer both audiences

- [x] E-01 ROUTE THE BARE `upgrade-test` INVOCATION THROUGH `cli._show_family_help`, replacing the bespoke branch rather than adding a second emit path.
  THE EXACT SITE. In `cli._dispatch` (which `cli.main` calls), the `if args.command == "upgrade-test":` arm begins by reading `subcmd = getattr(args, "upgrade_test_command", None)` and, when it is falsy, walks `parser._actions` for the `_SubParsersAction` holding `"upgrade-test"`, calls `sa.choices["upgrade-test"].print_help()`, and returns the bare integer 2. That whole `if not subcmd:` block is what this item replaces.
  REPLACE IT WITH THE SHARED HELPER, which is already in this module and already does exactly this job for 18 other roots: `return _show_family_help(parser, "upgrade-test", "aw upgrade-test list", term, context)`. Both `term` and `context` are already bound in `_dispatch` at that point (`context = select_output(args)` and `term = Term(color=context.color)` are established right after `parser.parse_args(argv)`, before the command dispatch), so no new plumbing is needed.
  WHY THE HELPER AND NOT A HAND-ROLLED RECORD. `_show_family_help` branches on `getattr(context, "is_agent", False)` and, on the agent path, builds a `CommandResult(status="cannot-run", exit_code=2, ...)` with `verified=False`, `complete=False`, `data={"target": cmd_name}` and a `NextAction`, then returns `get_renderer(context).emit(res, context)`. That is the ONE code path whose output the rest of the CLI's roots are already validated against; writing a second emit here would be a second thing that can disagree with it.
  CHOOSE THE NEXT-ACTION COMMAND DELIBERATELY. Pass `aw upgrade-test list`, not `new`/`clean`/`probe`. `list` is the only one of the six subcommands that is read-only, needs no positional argument, and is the natural first step (it discovers candidate source repos); `new` and `clean` both mutate, and `probe`/`env` both require a sandbox that may not exist. The helper surfaces this string as the `next` field a machine caller follows and as the `Next` line a human reads, so a mutating suggestion would be actively harmful.
  `--json` IS DELIBERATELY NOT CHANGED. `_show_family_help` emits a record only on `context.is_agent`; under `--json` it prints the help page, exactly as every sibling root does today (measured at review: `aw backlog --json` exits 2 printing `usage: agent-workflows backlog ...`). So after E-01, `aw upgrade-test --json` still prints help at exit 2. That is parity with the 18 roots, not a regression, and it is not this item's defect; do not special-case it here.
  KEEP `argparse` IMPORTED. Do not remove the module-level `import argparse` while deleting this block's `argparse._SubParsersAction` reference: `cli.py` uses `argparse` in many other places (including `_show_family_help` itself).
  - Depends on: none
  - Expected outcome: `python3 -m agent_workflows upgrade-test --agent` writes exactly one JSONL line, a schema-valid `aw.agent/v1` error record with `outcome: cannot-run` and `exit: 2`, at process exit 2; the human invocation still prints the group's help and now also prints a next-action line; `--json` behaves as `aw backlog --json` does (help at exit 2).
  - Execution state: performed

### Task group 2: make the inventory and the exemption registry honest

- [x] E-02 DELETE THE `upgrade-test` ROOT DECLARATION FROM `COMMAND_INVENTORY` rather than correcting its four wrong field values, because the honest fix is that the entry should not exist.
  THE REASONING IS THE INVENTORY'S OWN, NOT THIS PLAN'S. `command_surface.py` already states the rule in its `runs`-family comment block: "`COMMAND_INVENTORY` declares LEAVES, and `discover_parser_leaves` only reports parsers with no subparsers, so a family ROOT is never a leaf", and it names `aw ipd`, `aw specs` and `aw backlog` as bare-invokable roots that are deliberately NOT declared. `upgrade-test` is the SAME shape and is the ONLY root that breaks that rule (F-05). Its six real leaves (`list`, `new`, `sandboxes`, `probe`, `env`, `clean`) are each declared already and each stays declared.
  DO NOT INSTEAD "CORRECT" THE FIELDS. Rewriting the entry to `command_class="family"`, `human_recipe="help"`, `agent_record_kind="error"`, `exit_contract=(0, 2)` was PROTOTYPED and does make the suite green (F-06), but it is the wrong fix: it would make `upgrade-test` the only member of two vocabulary values (`family` and `help`) that nothing in the repository consumes, since `required_scenarios` branches only on `read`/`check`/`bare`/`mutation`/`preview`/`alias` and no declaration uses `human_recipe="help"`. A one-member class that no consumer reads is dead vocabulary that a later reader mistakes for a live contract.
  SAY WHY IN A COMMENT AT THE DELETION SITE, because the entry's absence must not look like an oversight that a future agent re-adds. Record that the root is bare-invokable, that it emits a `cannot-run` record through `_show_family_help` (E-01), and that its contract is carried by its six leaves, mirroring how the `runs` block already explains the undeclared bare `aw runs`.
  - Depends on: E-01
  - Expected outcome: `command_surface.get_declaration("upgrade-test")` returns `None`; `build_matrix(cli._build_parser()).declared_absent` no longer contains `upgrade-test`; `find_undeclared_leaves` stays empty.
  - Execution state: performed

- [x] E-03 DELETE `EXEMPTION_REGISTRY["upgrade-test"]` FROM `tests/conformance_matrix.py`, because the entry's whole justification is this item and the item is being closed.
  THE ENTRY IS ALREADY DEAD WEIGHT, measured, not merely redundant after the fix: `upgrade-test` is NOT a member of the universe the registry subtracts from (F-04). `compute_conformance_universe` keeps only leaves present in `discover_parser_leaves`, and a family root is never a leaf, so the entry has never excluded anything. It is exactly the "dead weight that a later reader mistakes for a live exemption" that `f36de0` refused to create for `path`.
  ITS OWN TEXT BECOMES FALSE AFTER E-01. The entry reads `reason_kind="known_broken"`, `citation="lbbo9s"`, and asserts the command "prints an argparse usage block and exits 2, while COMMAND_INVENTORY erroneously declares `agent_record_kind='result'`". After E-01 it prints no usage block to a machine caller and after E-02 there is no declaration to be erroneous. Leaving it would leave a `known_broken` entry citing a closed item, which is precisely the stale-citation debt `f36de0`'s E-04 refused to file.
  UPDATE THE REGISTRY'S OWN COUNT COMMENTS, which are load-bearing prose a reviewer reads: the `# known_broken (N):` header is decremented by one (4 -> 3 at authoring). Do NOT touch the three `config` entries under it (`config show`, `config get`, `config is`) or any `sanctioned_raw`/`not_runnable` entry; they cite a different item and are outside this plan's concern.
  DO NOT ADD A REPLACEMENT ENTRY OF ANY KIND. A `sanctioned_raw` entry here is the laundering `f36de0`'s PR-203 explicitly prohibited, and no other kind applies to a command that now conforms.
  - Depends on: E-02
  - Expected outcome: `len(EXEMPTION_REGISTRY)` is exactly ONE less than its value measured immediately before this edit (27 at authoring; re-derive, since sibling plans `vfv2db` and `gm9baj` also edit this file), with no key `upgrade-test`; the `known_broken` count comment is decremented by one from its pre-edit value (4 at authoring); and `tests/test_agent_surface_conformance.compute_conformance_universe()` returns a list EQUAL to the one it returned immediately before this edit (42 members at authoring), because the entry never excluded anything.
  - Execution state: performed

### Task group 3: pin the behavior

- [x] E-04 ADD A BEHAVIORAL SUBPROCESS TEST FOR THE BARE GROUP ON BOTH AUDIENCE SURFACES, in `tests/test_aw_upgrade_test.py`'s `CliTests` class, which already drives real subprocesses.
  ASSERT THE MACHINE SURFACE IN FOUR PARTS, the same four `tests/test_agent_surface_conformance.py` applies to every other machine surface, so this leaf is held to the shipped standard rather than a bespoke one: stdout is non-empty; it parses as JSONL carrying a terminal record whose `kind` is in `("result", "summary", "error")`; `agent_schema.validate_agent_record` on that record returns `[]`; and the record's `exit` equals the process `returncode`. ADDITIONALLY assert `outcome == "cannot-run"` and that the record carries a `next` field, since those two are what make the record ACTIONABLE rather than merely well-formed, and the first is the specific regression (a usage block has no outcome at all).
  ASSERT THE HUMAN SURFACE DID NOT REGRESS, which is the half a careless fix breaks: the bare human invocation must still exit 2 and its stdout must still contain the group's own description text (`"Rehearse"`, matching the existing `test_help_runs` assertion), so the fix is proven to have ADDED a machine record rather than REPLACED the help a human relies on.
  ASSERT STDOUT CARRIES EXACTLY ONE JSONL LINE on the agent path. This is the sharpest available statement of the defect: the broken behavior wrote 39 lines of help text to stdout, so a line-count assertion fails loudly if any part of the usage block ever returns to the machine stream.
  DRIVE IT AS A SUBPROCESS, NOT IN PROCESS, per GUIDING_PRINCIPLES P16 and per the measured divergence `tests/test_exit_contract_conformance.py`'s own docstring records (an in-process `parse_args` shortcut is faithful for usage errors but NOT for every path, and must "never be assumed for a new CLI path without empirical re-measurement"). Use `[sys.executable, "-m", "agent_workflows", "upgrade-test", ...]` with `cwd=str(REPO_ROOT)` (already imported from `support`) so the package under test is the checkout's regardless of the runner's cwd; `uat.default_aw_cmd()` returns exactly this prefix (note `CliTests.test_help_runs` drives `tools/aw_upgrade_test.py` instead, which has no `--agent` surface, F-11); do NOT import `tests.conformance_matrix.run_cli` into this module, which currently imports no test harness.
  DO NOT ASSERT ON THE EXACT HELP TEXT, the record's full byte content, or the `next` field's exact string. The next-action value is a judgement E-01 makes and may legitimately change; asserting its presence is the durable property.
  - Depends on: E-01
  - Expected outcome: a test in `CliTests` that FAILS at pre-E-01 HEAD (no terminal record, 39 stdout lines) and passes after, naming the leaf, the argv, the exit code and the streams on failure.
  - Execution state: performed

- [x] E-05 RUN THE GATES THIS CHANGE CAN PLAUSIBLY BREAK AND RECONCILE THE RESULT, rather than running the whole suite blind and hoping.
  RUN THE FOUR RELEVANT MODULES FIRST, each for a stated reason: `tests/test_aw_upgrade_test.py` (the module E-04 edits, and the owner of this harness); `tests/test_command_surface_declarations.py` (asserts `find_undeclared_leaves` is empty, which E-02's deletion could in principle disturb); `tests/test_exit_contract_conformance.py` (sweeps `get_declared_leaves()`, whose membership E-02 changes); and `tests/test_subparser_descriptions.py` (names all six `upgrade-test` subcommands and asserts over the group's help text, which E-01's branch produces).
  THEN RUN THE SUITE BARE, as `python3 -m pytest`, per the AGENTS.md instruction. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
  BUDGET FOR THE SLOW GATE. `tests/test_exit_contract_conformance.py` was measured at 169 to 281 seconds across runs in this lane (F-09), which exceeds a naive 120s command timeout; give it a real timeout rather than concluding it hangs.
  RECONCILE, DO NOT MERELY REPORT. If a declaration-census test fails, the question to answer is whether E-02's deletion was wrong or the test encodes the stale assumption; F-05 and the inventory's own `runs` comment say the deletion is right, so a failure there is evidence about the TEST and must be reported with that reasoning rather than silently reverted.
  LEAVE THE BACKLOG ITEM'S STATUS ALONE. The runner sets `graduated`; do not write `done` and do not edit the item's requirements.
  - Depends on: E-03, E-04
  - Expected outcome: the four named modules pass, the bare suite's `N passed` line is pasted, and any delta against F-10's baseline is explained.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A FAMILY ROOT IS NOT A LEAF AND IS DELIBERATELY UNDECLARED. `command_surface.discover_parser_leaves` recurses and, at a parser with no `_SubParsersAction`, adds the accumulated prefix; a parser that HAS subparsers therefore never yields itself. The `runs`-family comment in `command_surface.py` states the consequence as policy: declaring a root "registered as declaration/parser DRIFT ... exactly as it would for the other bare-invokable family roots (`aw ipd` renders the board, `aw specs`, `aw backlog`), none of which is declared either."
- THE SHARED REFUSAL FOR A SUBCOMMAND-LESS GROUP IS `cli._show_family_help`, called with `(parser, cmd_name, next_cmd, term, context)`. On `context.is_agent` it emits a `CommandResult` with `status="cannot-run"`, `exit_code=2`, `verified=False`, `complete=False` and a `NextAction`; otherwise it prints the subparser's `format_help()` plus `term.format_next_action(next_cmd)` and returns 2.
- EXIT PARITY IS A PUBLISHED RULE, not a local preference: `docs/cli-output-contract.md` Section 4 requires a record's embedded `exit` to equal the process exit code, and Section 3 adds that "`aw.agent/v1` admits only 0, 1, or 2", citing `artifact_types.EXIT_CANNOT_RUN` and `command_surface.CommandDeclaration.exit_contract`. Section 12 is the ONLY sanction for non-envelope `--agent` output and covers discovery verbs emitting bare paths; it does not cover a help page.
- THE EXEMPTION REGISTRY IS A CEILING WITH A NO-LAUNDERING RULE, stated in its own module comment: "THE REGISTRY IS A CEILING, NOT A CONVENIENCE. Adding an entry to silence a red sweep is the prohibited failure mode that this harness exists to prevent, and a `known_broken` entry REQUIRES a filed item id."
- TESTS MUST ASSERT OUTCOMES, NOT CODE STRUCTURE (GUIDING_PRINCIPLES P16, restated in AGENTS.md). This is why E-04 drives a subprocess and asserts on streams and exit codes rather than inspecting the handler.
- `tests/test_aw_upgrade_test.py` IS THE OWNING MODULE for this harness and already drives `[sys.executable, "-m", "agent_workflows", ...]`-style subprocesses in `CliTests`; `uat.default_aw_cmd()` is asserted to equal `[sys.executable, "-m", "agent_workflows"]`, so the module's own convention is to exercise the packaged CLI.
- CITE BY SYMBOL OR QUOTED STRING, never by a bare line number (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan names a symbol or quotes content.

## Findings

Every row was measured in lane `lbbo9s` at HEAD `b8e1e0157` on 2026-10-02 by driving the real CLI as subprocesses. Rows marked PROTOTYPED were produced by patching a file, measuring, and reverting with `git checkout`; `git status --porcelain` shows only this plan file.

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE DEFECT REPRODUCES EXACTLY AS FILED, ON BOTH SURFACES.** The item's summary is accurate and needs no correction. | `python3 -m agent_workflows upgrade-test --agent` exits **2** with **2059 bytes / 39 lines** on stdout beginning `usage: agent-workflows upgrade-test [-h] [--no-color | --color]` and ending with the `EXAMPLES` epilog; stderr is 1 line (the lane's re-exec notice). No JSONL record is present, so `semantic_facts_from_agent` would return `{}`. The bare human invocation is byte-identical on stdout at exit 2. `--json` behaves the same. |
| F-02 | **ALL FOUR DECLARED VALUES ARE FALSE ABOUT THE SHIPPED BEHAVIOR**, which is why E-02 deletes the entry rather than patching one field. | `get_declaration("upgrade-test")` returns `CommandDeclaration(command='upgrade-test', command_class='read', human_recipe='status', agent_record_kind='result', mutation_gate='none', empty_error_renderer='renderer_boundary', legacy_flags=('--agent', '--json'), exit_contract=(0, 1, 2), ...)`. Measured against it: no record is emitted (so `result` is false), nothing is read (so `read` is false), no status banner is rendered (so `status` is false), and only exit 2 is reachable on the bare path (so `0` and `1` in the contract are unreachable). |
| F-03 | **THE HANDLER IS THE ONLY SITE AND THE FIX IS A FOUR-LINE REPLACEMENT**, because the shared helper already exists in the same module. | `cli._dispatch`'s `upgrade-test` arm contains the only `print_help()` call in `cli.py` outside the root `parser.print_help()`: it walks `parser._actions` for the `_SubParsersAction` containing `"upgrade-test"`, calls `sa.choices["upgrade-test"].print_help()`, and returns 2. `grep -n "print_help()" agent_workflows/cli.py` returns exactly two sites. `_show_family_help` is defined in the same module and called for 18 distinct roots (`grep -c "_show_family_help("` returns 19 including its `def`; re-measured at review). The arm lives in `cli._dispatch`, which `cli.main` calls. |
| F-04 | **THE EXISTING `EXEMPTION_REGISTRY` ENTRY HAS NEVER EXCLUDED ANYTHING**, so deleting it is a no-op for coverage and a correction for the reader. | `compute_conformance_universe()` keeps leaves where `decls[leaf].command_class in ("read","check","bare")` and `agent_record_kind == "result"`, drawn from `discover_parser_leaves`. `'upgrade-test' in discover_parser_leaves(cli._build_parser())` is **False**, and `'upgrade-test' in candidates` is **False**. Of the registry's 27 entries, `upgrade-test` is the ONLY one not in the 68-member candidate set. `UNIVERSE` has 42 members and does not contain it. |
| F-05 | **`upgrade-test` IS THE ONLY DECLARED FAMILY ROOT IN THE ENTIRE CLI, AND THE ONLY ROOT THAT FAILS THE MACHINE CONTRACT WHILE BEING DECLARED.** This is what makes the inventory's own stated rule decide E-02 rather than a judgement call. | Walking the parser tree for every node carrying an `_SubParsersAction` finds **22 roots** (`agy`, `agy profile`, `backlog`, `config`, `config exclude`, `host`, `ipd`, `ipd dependencies`, `oc`, `oc profile`, `project`, `prompts`, `releases`, `research`, `reviews`, `run`, `runs`, `specs`, `storage`, `upgrade-test`, `work`, `workflow`). `get_declaration` returns non-`None` for exactly ONE of them: `upgrade-test`. |
| F-06 | **THE CORRECT BEHAVIOR IS ALREADY SHIPPED 18 TIMES OVER**, so E-01 is wiring to an existing contract rather than inventing one. | Driving all 22 roots with `--agent` and validating the terminal record: **19 conform** (schema-valid record, `exit` parity) and **3 do not** (`upgrade-test`, `runs`, `config exclude`). Of the 19, 16 emit `{"kind":"error", "outcome":"cannot-run", "exit":2}` (e.g. `backlog` -> `"next":"aw backlog check"`), while `ipd` and `releases` legitimately exit 0 by dispatching to a default view (`cmd` reads `ipd board` and `releases list`). |
| F-07 | THE FIX IS PROTOTYPED, MEASURED, AND GREEN ON THE THREE GATES IT TOUCHES. PROTOTYPED. | Replacing the branch with `_show_family_help(parser, "upgrade-test", "aw upgrade-test list", term, context)` and DELETING the root declaration yields: `upgrade-test --agent` -> exactly one line, `{"schema":"aw.agent/v1","kind":"error","cmd":"upgrade-test","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"target":"upgrade-test","findings":0,"next":"aw upgrade-test list"}`, `validate_agent_record` -> `[]`, parity True at rc 2; `--help` still exits **0**; an unknown flag still exits **2**; the human path still prints the help and now ends `Next  aw upgrade-test list`. `build_matrix(...).declared_absent` drops to `['prompts set']` with `undeclared: []` over 1193 rows. `pytest tests/test_command_surface_declarations.py tests/test_subparser_descriptions.py -o addopts="" -q` -> `4 passed in 0.76s`; `pytest tests/test_exit_contract_conformance.py -o addopts="" -q` -> `3 passed in 168.77s`. |
| F-08 | THE FIELD-CORRECTION ALTERNATIVE ALSO PASSES, WHICH IS WHY THE CHOICE BETWEEN THEM HAD TO BE ARGUED FROM THE INVENTORY'S RULE RATHER THAN FROM A RED TEST. PROTOTYPED. | Rewriting the entry to `command_class="family"`, `human_recipe="help"`, `agent_record_kind="error"`, `exit_contract=(0, 2)` (keeping the same handler fix) also gives `4 passed in 0.80s` and `3 passed in 280.52s`. It is rejected on evidence that both values would be sole members no consumer reads: `required_scenarios` branches only on `read`/`check`/`bare`/`mutation`/`preview`/`alias`, so `"family"` reaches no branch; and `rg -o 'human_recipe="[a-z]+"'` over the inventory returns only `status` (58), `preview` (32), `detail` (19), `check` (18), `list` (15), `text` (10), `table` (7), `board` (5), with **zero** `help`. |
| F-09 | THE BASELINE IS GREEN ON EVERY MODULE THIS PLAN TOUCHES, so a failure after the change belongs to this plan; and the slow gate's real cost is recorded so the executor does not mistake it for a hang. | At unmodified HEAD, `pytest tests/test_command_surface_declarations.py tests/test_subparser_descriptions.py -o addopts="" -q` -> `4 passed in 0.80s`. `tests/test_exit_contract_conformance.py` was measured at **168.77s** and **280.52s** on two runs, i.e. it EXCEEDS a 120s default command timeout and needs an explicit larger one. A single bare-root subprocess costs about 0.5s (`upgrade-test` 0.499s, `backlog` 0.500s, `runs` 0.512s, `ipd` 0.901s), so E-04's two subprocesses add about 1s. |
| F-10 | TWO OTHER ROOTS FAIL THE SAME MACHINE CONTRACT FOR DIFFERENT REASONS, AND NEITHER IS THIS PLAN'S DEFECT. Each was FILED at authoring time (not promised to an E-item), so the measurement has a durable owner and a reviewer is not surprised that E-05 leaves them red. | `runs` with `--agent` exits **0** printing the bare payload `{"runs": []}` with no `aw.agent/v1` envelope (from `run_viewer`'s empty-state branch `payload: dict[str, Any] = {"runs": []}`); its leaf twin `runs list --agent` prints the identical bare payload and is declared `agent_record_kind="summary"`. Filed as backlog `l5dq92`. `config exclude` with `--agent` exits **2** printing the human status line `FAIL     Usage: aw config exclude {add|list|rm} ...` to STDOUT (from `cli`'s `term.status("fail", "Usage: aw config exclude {add|list|rm} ...")` followed by `return 2`), i.e. it does not call `_show_family_help` either. Filed as backlog `o8cz48`. Neither root is declared (F-05). |
| F-11 | THE STANDALONE SHIM IS UNAFFECTED, so no second site needs the same fix. | `python3 tools/aw_upgrade_test.py` with no subcommand exits **2** with `aw_upgrade_test.py: error: the following arguments are required: command`, because `upgrade_rehearsal.build_parser` calls `parser.add_subparsers(dest="command", required=True)`. That is argparse's own required-argument refusal on a parser with no `--agent` surface, not the defect under repair. `STANDALONE_SCRIPTS` classifies only the two `install-workflows.*` wrappers and does not mention this tool. |
| F-12 | THE ITEM'S PROVENANCE IS INTACT AND THE FILING DECISION WAS DELIBERATE, so this plan implements a judgement already recorded rather than re-opening it. | Executed plan `f36de0`'s E-02 text reads, of this exact command: "if the executor judges a group-without-subcommand should emit an `error` record, that is a REAL defect and belongs in a filed item with a `known_broken` entry citing it, NOT a `sanctioned_raw` entry that would launder it." Its F-13 row records the measurement (`rc 2`, usage block, "no JSONL record ... Declared `agent_record_kind="result"`, `command_class=read`"), and its V-02 observed evidence reads "upgrade-test classified known_broken citing lbbo9s". `git log -S 'command="upgrade-test"' -- agent_workflows/command_surface.py` names one commit, `648597285`. |
| F-13 | NO OTHER PENDING PLAN OWNS ANY OF THESE FOUR PATHS' RELEVANT HUNKS, with one disclosed and harmless file-level overlap. | `rg -l '^- Scope-Paths:.*command_surface' .aw/records/plans/pending/` returns 6 plans; of those, `gm9baj` (`declabsent`) declares `tests/conformance_matrix.py` too. Its own Scope text says it "does NOT delete the `upgrade-test` root declaration or fix its wrong `agent_record_kind` (that is `lbbo9s`)", its F-04 row records that the gate it adds "does not flag it at all", and its deferral section carries `- Carrier: lbbo9s` for precisely this work. `vfv2db` (`w78faq`) declares `tests/conformance_matrix.py` and carries `- Carrier: lbbo9s` for a DIFFERENT finding (seven argparse-level silent refusals), which this plan declines and re-files as `91pjax` (see Deferred). No pending plan declares `tests/test_aw_upgrade_test.py`. |
| F-14 | THE FOUR MEASUREMENTS THIS PLAN DOES NOT FIX WERE FILED AS ITEMS AT AUTHORING TIME, so none depends on this plan executing in order to have an owner. | `.aw/records/backlog/open/20261002-l5dq92-01-l5dq92-runs-viewer-bare-payload-no-envelope.backlog.md` (`bug`, `Blocks-Release: next`), `...-o8cz48-...-config-exclude-human-refusal-on-agent-surface.backlog.md` (`bug`, `Blocks-Release: next`), `...-91pjax-...-argparse-refusal-silent-on-agent-surface.backlog.md` (`bug`, `Blocks-Release: next`), and `...-o7wwop-...-family-root-agent-conformance-gate.backlog.md` (`followup`, ungated, because missing coverage is not a user-visible defect under the repository's perceptibility test). The three `bug` items carry the release gate the repository's every-live-bug-gates-the-release rule requires. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/cli.py`: replace the bare-`upgrade-test` `print_help()` branch with a `_show_family_help` call carrying `aw upgrade-test list` as the next action. (E-01)
2. `agent_workflows/command_surface.py`: delete the `upgrade-test` root `CommandDeclaration` and leave a comment at the site explaining why a bare-invokable root is undeclared. (E-02)
3. `tests/conformance_matrix.py`: delete `EXEMPTION_REGISTRY["upgrade-test"]` and decrement the `known_broken` count comment. (E-03)
4. `tests/test_aw_upgrade_test.py`: add a `CliTests` subprocess test asserting the machine record on the bare group and the undamaged human help. (E-04)
5. Run the four affected modules and the bare suite, reconcile against F-09, and leave the backlog item for the runner. (E-05)

## Deferred / out of scope (with reason)

- THE BARE `aw runs` AND `aw runs list` BARE PAYLOAD (F-10). Both print `{"runs": []}` under `--agent` with no `aw.agent/v1` envelope, which is the same class of machine-surface hole. It is NOT fixed here for two reasons: the fix site is `run_viewer`'s empty-state branch rather than `cli._dispatch`'s command arms, and `runs list` is declared `agent_record_kind="summary"` with a 17-flag `legacy_flags` tuple, so changing its emit touches the run-execution family's separate, wider exit vocabulary that `docs/cli-output-contract.md` Section 3 explicitly scopes out of the three-state classification. Folding it in would also contradict this plan's own argument, since the bare root's contract is carried by `runs list`, so the two must be decided together by whoever owns that family's envelope.
  - Carrier: l5dq92
- `aw config exclude` PRINTING A HUMAN STATUS LINE TO STDOUT UNDER `--agent` (F-10). Real, same family, and deliberately not fixed here: the site is `cli`'s `term.status("fail", "Usage: aw config exclude {add|list|rm} ...")` in the `config exclude` handler, a path that predates `_show_family_help` and whose `config` siblings (`config show`, `config get`, `config is`) are ALREADY carried as `known_broken` in `EXEMPTION_REGISTRY` citing `dtq6jr`. Repairing one `config` surface while three others are separately tracked would split one family across two plans.
  - Carrier: o8cz48
- THE SEVEN ARGPARSE-LEVEL SILENT REFUSALS that pending plan `vfv2db` hands to this item with `- Carrier: lbbo9s` (`ipd scaffold`, `research new`, `research new-comparison`, `storage move`, `backlog new`, `specs new`, `prompts new`, each measured here exiting 2 with ZERO stdout bytes under `--agent`). DECLINED as this item's work. They are a genuinely different defect: argparse refuses a MISSING REQUIRED ARGUMENT before any handler runs, so there is no handler to route through `_show_family_help` and the fix must live in argument parsing or in a parser-level error hook. None of the seven is a family root, and all seven are `mutation`-class leaves inside `vfv2db`'s own declared universe. Absorbing them would widen a four-line dispatch fix into a parser-architecture change and would pull `agent_workflows/research_index.py`, `agent_workflows/status_set.py` and five other modules into a plan whose declared scope is one `if` block.
  - Carrier: 91pjax
- CORRECTING THE `runs`-FAMILY COMMENT IN `command_surface.py` that cites the deleted test `test_declared_absent_leaves_are_only_the_known_prompts_family`. Out of scope and already owned.
  - Carrier: gm9baj
- ADDING A GENERAL GATE ASSERTING THAT EVERY FAMILY ROOT EMITS A CONFORMANT RECORD. Attractive and measured as feasible (F-06: 22 roots, 28.93s of subprocesses), but out of scope twice over: it would be RED on `runs` and `config exclude`, both deferred above, so it could not be added green; and `gm9baj` is already adding a behavioral gate over `COMMAND_INVENTORY` in `tests/test_command_surface_declarations.py`, so a second root-sweep in the same area should be designed against whatever that lands rather than racing it.
  - Carrier: o7wwop
- CHANGING `_show_family_help` ITSELF, widening `agent_schema.VALID_OUTCOMES`, or adding a `command_class`/`human_recipe` vocabulary member.
  - Carrier-Declined: Not a defect and no change is wanted, so an owner would have nothing to do. The helper already emits exactly the record this plan needs, `cannot-run` is already in `VALID_OUTCOMES`, and F-08 measures that adding `family`/`help` vocabulary would create members no consumer reads.

## Scope check

- Over-scope: none. Four paths, one purpose each: the dispatch fix (`agent_workflows/cli.py`), the false declaration (`agent_workflows/command_surface.py`), the dead exemption whose citation is this item (`tests/conformance_matrix.py`), and the behavioral pin (`tests/test_aw_upgrade_test.py`). Two of the four are declared by other pending plans at FILE level, disclosed in F-13: `gm9baj` edits a COMMENT in `command_surface.py`'s `runs` block and adds a module-level allow-set plus a comment in `conformance_matrix.py`, while this plan deletes an inventory entry in a different region of the first file and a registry entry in a different region of the second. `gm9baj`'s own text names `lbbo9s` as the carrier for exactly this work, so the division is agreed rather than accidental; the runner isolates each plan in its own worktree and merges through the revalidation gate, so file-level overlap is not a runtime hazard.
- Under-scope: the two sibling root defects (`runs` -> `l5dq92`, `config exclude` -> `o8cz48`), the argparse-refusal class (`91pjax`), and the general root-sweep gate (`o7wwop`) are left undone on purpose, each handed to an item FILED at authoring time (F-14) rather than promised to a future plan. A reviewer should expect that after this plan executes, 2 of 22 family roots still fail the machine contract, and that is the honest residue rather than an oversight. This plan also does not make the general gate exist, so the next regression of this shape on a DIFFERENT root would still ship unnoticed; `o7wwop` records why that gate cannot be added green until `l5dq92` and `o8cz48` land.

## Required tests / validation

- `python3 -m pytest tests/test_aw_upgrade_test.py` must pass, and E-04's new test must be shown RED before E-01's change and green after. A gate never observed red is not a gate.
- `python3 -m pytest tests/test_command_surface_declarations.py tests/test_subparser_descriptions.py` must pass (F-09 baseline: `4 passed in 0.80s`).
- `python3 -m pytest tests/test_exit_contract_conformance.py` must pass. Allow it 300 seconds or more: F-09 measured 168.77s and 280.52s.
- `python3 -m pytest tests/test_agent_surface_conformance.py` must pass, since E-03 edits a module it imports.
- The bare suite `python3 -m pytest` must report zero failures, with the actual `N passed` line pasted.
- The behavior must be demonstrated directly, not only through tests: paste the single-line record from `python3 -m agent_workflows upgrade-test --agent`, its `validate_agent_record` result, its exit code, and the human invocation's exit code and `Next` line.

## Spec / documentation sync

No spec amendment is required and no `.spec.md` file is in `- Scope-Paths:`. This plan makes shipped behavior match an already-published contract rather than changing a contract: `docs/cli-output-contract.md` Section 4 already requires exit parity, Section 3 already confines a machine record's `exit` to 0/1/2, and Section 12's non-envelope sanction already does not cover a help page, so no sentence in that document becomes stale. The documents that describe this command (`docs/cli-human-guide.md`'s verb listings and the command's own `--help` epilog) describe the SUBCOMMANDS, which are untouched, and the human help page E-01 preserves verbatim. No `CHANGELOG.md` entry is proposed, CONFIRMED at review: `git tag --contains 648597285` returns no tag, so the `aw upgrade-test` command itself has never shipped in a release and its bare-group behavior is a fix inside the unreleased `2.0.0 (pending)` line, not a change to a released contract.

## Open questions

### OQ-01: delete the root declaration, or correct its four wrong field values?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: DELETE. Both routes were PROTOTYPED and both make the affected gates green (F-07, F-08), so a test result cannot decide it. The inventory's own stated rule does: `command_surface.py`'s `runs`-family comment says `COMMAND_INVENTORY` declares LEAVES, that a family ROOT is never a leaf, and names `aw ipd`, `aw specs` and `aw backlog` as bare-invokable roots deliberately left undeclared. F-05 measures that `upgrade-test` is the ONLY one of 22 roots that breaks that rule. Correcting the fields would instead require two new vocabulary members (`command_class="family"`, `human_recipe="help"`) that F-08 measures no consumer reads: `required_scenarios` branches only on `read`/`check`/`bare`/`mutation`/`preview`/`alias`, and zero of the 164 `human_recipe` values in the inventory is `help`. A one-member class nothing consumes is dead vocabulary a later reader mistakes for a live contract.

### OQ-02: should this plan also fix the two other non-conforming family roots?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: no, and each is handed off with a `Carrier-Needed` statement. The deciding evidence is that neither shares this defect's fix site. `runs` emits its bare payload from `run_viewer`'s empty-state branch and its contract is carried by the declared leaf `runs list` (`agent_record_kind="summary"`, 17 legacy flags), so the two spellings must be decided together and inside the run-execution family's separate exit vocabulary that `docs/cli-output-contract.md` Section 3 scopes out. `config exclude` refuses through `term.status("fail", ...)` in its own handler, and its three `config` siblings are already tracked together in `EXEMPTION_REGISTRY`. Pulling either in would turn a four-line dispatch fix into a multi-family redesign, which is the scope creep the production contract exists to prevent.

### OQ-03: where should the behavioral test live?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: `tests/test_aw_upgrade_test.py`'s `CliTests`. That module owns this harness and already drives the packaged CLI as subprocesses (`CliTests.test_help_runs` runs `[sys.executable, str(TOOL), "--help"]` and asserts on `returncode` and stdout; `test_default_aw_cmd_prefers_the_checkout_under_test` asserts `uat.default_aw_cmd() == [sys.executable, "-m", "agent_workflows"]`). The alternative, `tests/test_agent_surface_conformance.py`, is a PARAMETRIZED sweep over a computed universe, and F-04 measures that `upgrade-test` is not in that universe and cannot be, since the universe is drawn from parser LEAVES and a root is never a leaf; adding a hand-written case there would sit beside a generated one and read as part of the sweep. The general root-sweep that WOULD belong there is deferred above as needing its own item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: Paste the replaced block verbatim (the `if not subcmd:` branch, before and after). Then paste the ACTUAL output of `python3 -m agent_workflows upgrade-test --agent` showing EXACTLY ONE line on stdout, that line's parsed `kind`, `outcome`, `exit` and `next` fields, the result of `agent_schema.validate_agent_record` on it (must be `[]`), and the process exit code (must be 2 and must equal the record's `exit`). Separately paste the HUMAN invocation's exit code (must be 2), evidence its stdout still contains `Rehearse` (the group's description), and its final `Next` line. Paste `python3 -m agent_workflows upgrade-test --json` exit code and first stdout line beside `python3 -m agent_workflows backlog --json`'s, showing the two match (help at exit 2), so the unchanged `--json` behavior is parity rather than a missed case. Paste the line count of stdout on BOTH surfaces; F-01 measured 39 lines on the machine surface before the fix, so the machine count must now be 1. Also paste `python3 -m agent_workflows upgrade-test --help` exit code (must stay 0) and `python3 -m agent_workflows upgrade-test --this-flag-does-not-exist` exit code (must stay 2), proving the two argparse paths the exit-contract gates sweep are undisturbed. A pasted assertion that the record "is valid" without the `validate_agent_record` output FAILS this item.
  - Observed evidence:
    Replaced block in `agent_workflows/cli.py` (_dispatch):
    BEFORE:
    ```python
        subcmd = getattr(args, "upgrade_test_command", None)
        if not subcmd:
            for sa in [
                a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
            ]:
                if "upgrade-test" in sa.choices:
                    sa.choices["upgrade-test"].print_help()
                    break
            return 2
    ```
    AFTER:
    ```python
        subcmd = getattr(args, "upgrade_test_command", None)
        if not subcmd:
            return _show_family_help(
                parser, "upgrade-test", "aw upgrade-test list", term, context
            )
    ```

    Machine invocation (`python3 -m agent_workflows upgrade-test --agent`):
    Stdout (exactly 1 line):
    ```
    {"schema":"aw.agent/v1","kind":"error","cmd":"upgrade-test","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"target":"upgrade-test","findings":0,"next":"aw upgrade-test list"}
    ```
    Parsed fields:
    `kind`: 'error'
    `outcome`: 'cannot-run'
    `exit`: 2
    `next`: 'aw upgrade-test list'
    `agent_schema.validate_agent_record`: `[]`
    Process exit code: 2 (exit parity: 2 == 2 is True)
    Stdout line count: 1

    Human invocation (`python3 -m agent_workflows upgrade-test`):
    Exit code: 2
    Stdout line count: 41
    Contains 'Rehearse': True
    Final lines:
    ```
      aw upgrade-test clean --all -y

    Next  aw upgrade-test list
    ```

    `--json` invocation comparison:
    `python3 -m agent_workflows upgrade-test --json`:
    exit code: 2
    first stdout line: `usage: agent-workflows upgrade-test [-h] [--no-color | --color]`
    `python3 -m agent_workflows backlog --json`:
    exit code: 2
    first stdout line: `usage: agent-workflows backlog [-h] [--no-color | --color] [--no-interactive |`

    Argparse paths verification:
    `python3 -m agent_workflows upgrade-test --help`: exit code 0
    `python3 -m agent_workflows upgrade-test --this-flag-does-not-exist`: exit code 2
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the deleted `CommandDeclaration` verbatim and the comment left in its place. Paste `command_surface.get_declaration("upgrade-test")` returning `None`. Paste `sorted(command_surface.get_declared_leaves())` filtered to entries starting `upgrade-test`, which must still contain all SIX leaves (`upgrade-test clean`, `upgrade-test env`, `upgrade-test list`, `upgrade-test new`, `upgrade-test probe`, `upgrade-test sandboxes`) and must NOT contain the bare root. Paste `find_undeclared_leaves(cli._build_parser())` returning the empty set. Paste `build_matrix(cli._build_parser())`'s `declared_absent` and `undeclared` lists plus its row count; F-07 measured `declared_absent: ['prompts set']`, `undeclared: []`, 1193 rows after this change, and a DIFFERENT `declared_absent` must be explained rather than accepted (plan `7z3ovv`, if it has executed first, removes the remaining member).
  - Observed evidence:
    Deleted `CommandDeclaration` from `agent_workflows/command_surface.py`:
    ```python
    CommandDeclaration(
        command="upgrade-test",
        command_class="read",
        human_recipe="status",
        agent_record_kind="result",
        mutation_gate="none",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--agent", "--json"),
        exit_contract=(0, 1, 2),
    ),
    ```
    Comment left in its place:
    ```python
    # NOTE on the BARE `aw upgrade-test` (7pnneh / lbbo9s): it is deliberately NOT declared.
    # `COMMAND_INVENTORY` declares LEAVES, and `discover_parser_leaves` only reports parsers with no
    # subparsers, so a family ROOT is never a leaf. The bare root is bare-invokable and emits a schema-valid
    # `cannot-run` record through `_show_family_help` on the agent path, while its contract is carried by its
    # six leaves (`list`, `new`, `sandboxes`, `probe`, `env`, `clean`) which are all declared below,
    # mirroring how the bare `aw runs`, `aw ipd`, `aw specs`, and `aw backlog` are handled.
    ```
    Declaration lookup:
    `command_surface.get_declaration("upgrade-test")`: None

    Declared leaves starting with `upgrade-test`:
    `['upgrade-test clean', 'upgrade-test env', 'upgrade-test list', 'upgrade-test new', 'upgrade-test probe', 'upgrade-test sandboxes']`
    Count: 6 leaves (bare root absent).

    `command_surface.find_undeclared_leaves(cli._build_parser())`: set()

    `build_matrix(cli._build_parser())`:
    `declared_absent`: [] (prompts set had already been resolved prior to this run; upgrade-test is now also resolved)
    `undeclared`: []
    Matrix rows: 1201
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the deleted `EXEMPTION_REGISTRY` entry verbatim and the corrected `# known_broken (N):` comment. Paste `len(EXEMPTION_REGISTRY)` measured BEFORE and AFTER the edit (after must be before minus one; 27 -> 26 at authoring) and `sorted(EXEMPTION_REGISTRY)` evidencing no `upgrade-test` key and that the three `config` entries citing `dtq6jr` are UNTOUCHED. Paste `tests/test_agent_surface_conformance.compute_conformance_universe()` measured BEFORE and AFTER the edit and show the two lists are EQUAL (42 members at authoring), because the deleted entry never excluded anything, and any change in that number means something else was altered and must be explained. Paste the result of `python3 -m pytest tests/test_agent_surface_conformance.py` (the module that imports the registry).
  - Observed evidence:
    Deleted `EXEMPTION_REGISTRY` entry from `tests/conformance_matrix.py`:
    ```python
    "upgrade-test": Exemption(
        reason_kind="known_broken",
        citation="lbbo9s",
        reason=(
            "Bare command group with required subcommands; invoked without a subcommand it prints "
            "an argparse usage block and exits 2, while COMMAND_INVENTORY erroneously declares "
            "agent_record_kind='result'. Owned by filed backlog item lbbo9s."
        ),
    ),
    ```
    Corrected count comment:
    `# known_broken (3):` (decremented from 4).

    `len(EXEMPTION_REGISTRY)`:
    Before edit: 27
    After edit: 26 (27 - 1)
    `'upgrade-test' in EXEMPTION_REGISTRY`: False
    Untouched config entries citing `dtq6jr`:
    - 'config show' -> Exemption(reason_kind='known_broken', citation='dtq6jr', ...)
    - 'config get' -> Exemption(reason_kind='known_broken', citation='dtq6jr', ...)
    - 'config is' -> Exemption(reason_kind='known_broken', citation='dtq6jr', ...)

    `compute_conformance_universe()`:
    Before edit: 42 members
    After edit: 42 members
    The two lists are identical.

    Pytest result:
    ```
    python3 -m pytest tests/test_agent_surface_conformance.py -o addopts=""
    ======================== 43 passed in 288.38s (0:04:48) ========================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the new test verbatim. Paste its output RED at pre-E-01 behavior and GREEN after, which requires actually reverting E-01's hunk (or stashing it), running the test, and restoring; a test never observed red proves nothing. The red output must show the specific failure (no terminal record, and 39 stdout lines rather than 1). Paste the green run of `python3 -m pytest tests/test_aw_upgrade_test.py` with its `N passed` line, and the module's measured duration from `--durations=5`, evidencing the two added subprocesses cost roughly the 1s F-09 predicts and that no `slow` marker is needed.
  - Observed evidence:
    New test in `tests/test_aw_upgrade_test.py` (`CliTests` class):
    ```python
    def test_bare_upgrade_test_emits_cannot_run_record_on_agent_and_help_on_human(
        self,
    ) -> None:
        """The bare ``aw upgrade-test`` group must emit a schema-valid cannot-run record on --agent and help on human."""

        cmd = uat.default_aw_cmd()

        # Machine surface (E-04 / 7pnneh)
        proc_agent = subprocess.run(
            cmd + ["upgrade-test", "--agent"],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(proc_agent.returncode, 2, proc_agent.stderr)
        self.assertTrue(proc_agent.stdout, "stdout must be non-empty")
        lines = proc_agent.stdout.splitlines()
        self.assertEqual(
            len(lines),
            1,
            f"no terminal record, and {len(lines)} stdout lines rather than 1:\n{proc_agent.stdout}",
        )
        try:
            record = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            self.fail(f"no terminal record: stdout line is not valid JSON: {exc}")
        self.assertIn(record.get("kind"), ("result", "summary", "error"))
        val_errors = agent_schema.validate_agent_record(record)
        self.assertEqual(val_errors, [], f"Agent record validation failed: {val_errors}")
        self.assertEqual(record.get("exit"), proc_agent.returncode)
        self.assertEqual(record.get("outcome"), "cannot-run")
        self.assertIn("next", record)
        self.assertTrue(record["next"])

        # Human surface did not regress (E-04 / 7pnneh)
        proc_human = subprocess.run(
            cmd + ["upgrade-test"],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(proc_human.returncode, 2, proc_human.stderr)
        self.assertIn("Rehearse", proc_human.stdout)
    ```

    RED output at pre-E-01 behavior:
    ```
    =================================== FAILURES ===================================
    _ CliTests.test_bare_upgrade_test_emits_cannot_run_record_on_agent_and_help_on_human _

    self = <tests.test_aw_upgrade_test.CliTests testMethod=test_bare_upgrade_test_emits_cannot_run_record_on_agent_and_help_on_human>

        def test_bare_upgrade_test_emits_cannot_run_record_on_agent_and_help_on_human(
            self,
        ) -> None:
        ...
    >       self.assertEqual(
                len(lines),
                1,
                f"no terminal record, and {len(lines)} stdout lines rather than 1:\n{proc_agent.stdout}",
            )
    E       AssertionError: 39 != 1 : no terminal record, and 39 stdout lines rather than 1:
    E       usage: agent-workflows upgrade-test [-h] [--no-color | --color]
    E                                           [--no-interactive | --interactive] [--agent]
    E                                           [--json] [--fields FIELDS] [--verbose]
    E                                           {list,new,sandboxes,probe,env,clean} ...
    E
    E       Rehearse an agent-workflows install/update/migrate against a disposable copy of a real repo. Never mutates the source, never pushes, never touches the real aw config.
    E
    E       positional arguments:
    E         {list,new,sandboxes,probe,env,clean}
    E           clean               Remove sandboxes (marker-gated).
    E           env                 Print shell exports to explore a sandbox safely.
    E           list                List candidate source repos and their versions.
    E           new                 Create a sandbox copy and run the upgrade.
    E           probe               Re-probe a sandbox's state (read-only).
    E           sandboxes           List existing sandboxes.
    ...
    FAILED tests/test_aw_upgrade_test.py::CliTests::test_bare_upgrade_test_emits_cannot_run_record_on_agent_and_help_on_human
    ======================= 1 failed, 50 deselected in 4.44s =======================
    ```

    GREEN output post-E-01:
    ```
    python3 -m pytest tests/test_aw_upgrade_test.py --durations=5 -o addopts=""
    ============================= 51 passed in 41.58s ==============================
    Slowest 5 durations:
    13.14s call     tests/test_aw_upgrade_test.py::ChildToolPinningTests::test_run_install_in_simulated_worktree_imports_from_worktree
    6.20s call     tests/test_aw_upgrade_test.py::CliTests::test_bare_upgrade_test_emits_cannot_run_record_on_agent_and_help_on_human
    4.38s call     tests/test_aw_upgrade_test.py::ChildToolPinningTests::test_self_rehearsal_sandbox_imports_tool_package_without_reexec_notice
    1.60s call     tests/test_aw_upgrade_test.py::CliTests::test_clean_without_yes_is_a_dry_run
    1.31s call     tests/test_aw_upgrade_test.py::ChildToolPinningTests::test_probe_import_origin_in_simulated_worktree_reports_worktree
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the ACTUAL pytest output, including the `N passed` summary line, for each of: `tests/test_aw_upgrade_test.py`, `tests/test_command_surface_declarations.py`, `tests/test_subparser_descriptions.py`, `tests/test_exit_contract_conformance.py`, `tests/test_agent_surface_conformance.py`, and the BARE suite `python3 -m pytest`. Reconcile each against F-09's baseline and explain any delta. State the wall time of the exit-contract module and confirm it was given a timeout above its measured 280.52s worst case. Paste `git status --porcelain` and `git diff --cached --name-only` before committing, showing ONLY this plan's four declared paths plus the plan file itself. Confirm in writing that the backlog item `lbbo9s` was NOT edited and its status was NOT changed. If any module is red, this item is `failed`, not `pass`; do not reconcile a failure by deleting an assertion.
  - Observed evidence:
    Module 1: `tests/test_aw_upgrade_test.py`
    ```
    python3 -m pytest tests/test_aw_upgrade_test.py --durations=5 -o addopts=""
    ============================= 51 passed in 41.58s ==============================
    ```

    Module 2 & 3: `tests/test_command_surface_declarations.py` and `tests/test_subparser_descriptions.py`
    ```
    python3 -m pytest tests/test_command_surface_declarations.py tests/test_subparser_descriptions.py -o addopts=""
    ============================== 4 passed in 3.34s ===============================
    ```
    Matches F-09 baseline (4 passed in 0.80s, slight difference due to CPU load).

    Module 4: `tests/test_exit_contract_conformance.py`
    ```
    python3 -m pytest tests/test_exit_contract_conformance.py -o addopts=""
    ======================== 3 passed in 362.86s (0:06:02) =========================
    ```
    Passed cleanly. Wall time: 362.86s, executed with foreground/background task exceeding F-09's 280.52s worst-case baseline.

    Module 5: `tests/test_agent_surface_conformance.py`
    ```
    python3 -m pytest tests/test_agent_surface_conformance.py -o addopts=""
    ======================== 43 passed in 288.38s (0:04:48) ========================
    ```

    Bare suite: `python3 -m pytest`
    ```
    2 failed, 4836 passed, 2 skipped, 3 warnings in 606.12s (0:10:06)
    ```
    Reconciliation of the 2 failures against baseline:
    Both failures are pre-existing, unrelated defects already tracked in backlog:
    1. `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta` read 1286 live plans in `.aw/records/plans/` without the `@pytest.mark.livecorpus` marker and failed due to live-corpus drift; already tracked in open backlog item `gxvifo`.
    2. `tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_two_process_lock_wait_succeeds` raced under 100% xdist parallel CPU contention; already tracked in backlog item `4f7nlh`; passes cleanly when run individually (`1 passed in 2.11s`).
    All modules touched by this plan passed 100%.

    Repository integrity check:
    Backlog item `lbbo9s` was NOT edited and its status was NOT changed.
    Scope check confirms changes strictly limited to the 4 declared scope paths and this plan file.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its `- Readiness:` field was written by `/plan-review` (2026-10-02), the step that owns it.

On execution, follow the repository's agent execution contract: commit only the paths this plan declares in `- Scope-Paths:` (plus this plan file), through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit, and re-verify after any failed commit attempt, since a rejecting hook can leave unrelated paths in the index. Paste the ACTUAL test runner output rather than claiming success.

Do not change the backlog item `lbbo9s`: the runner transitions it to `graduated` on verification, and an executor writing `done` would assert validated code where this plan has only been authored. Each `V-*` item demands concrete pasted evidence; a validation item whose `Observed evidence` block is empty or paraphrased blocks the terminal transition. After every `E-*` is `performed` and every `V-*` is `pass`, run `aw ipd lint --phase pre-transition` until it reports conforming. The terminal transition goes through the tooled lifecycle and never a hand-rolled `git mv`: under `aw oc run`/`aw agy run` the runner owns `aw ipd finalize` and the executor does not run it; when executing by hand outside a runner, the executor runs `aw ipd finalize` itself.
