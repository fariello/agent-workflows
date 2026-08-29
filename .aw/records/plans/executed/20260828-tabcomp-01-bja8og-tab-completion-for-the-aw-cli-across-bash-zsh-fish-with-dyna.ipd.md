# IPD: Native shell completion script generators for Bash, Zsh, and Fish with CLI output subcommand

- Date: 2026-08-28
- Kind: child
- Concern: The `aw` CLI provides dozens of nested subcommands and flags across three executable aliases (`aw`, `agentwf`, `agent-workflows`), but has no completion generator. Users have no way to generate native completion scripts for their shells without relying on external third-party tools or manually writing shell logic. This child delivers only the STATIC generation of subcommand/flag completion scripts and the `aw completion <shell>` output command; dynamic repository-artifact completion (Set/plan/spec/run IDs, status enums) is child 02 (`tabcomp-02`) and drop-in installation is child 03 (`tabcomp-03`).
- Scope: Implement native, zero-runtime-dependency (stdlib-only) STATIC completion script generators for Bash, Zsh, and Fish: (1) Add `agent_workflows/completion.py` with `introspect_cli_tree`, `generate_bash_completion`, `generate_zsh_completion`, and `generate_fish_completion`; (2) Add `aw completion <shell>` subcommand to `agent_workflows/cli.py` to stream the generated completion script to stdout, structured so child 03 can later add `install`/`uninstall` subcommands WITHOUT reshaping the parser (see E-03); (3) Add unit tests in `tests/test_completion.py` verifying alias binding, shell-syntax validity, CLI execution, and correct filtering of non-user commands.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py
- Item-Dependencies: none
- Status: executed
- Set: tabcomp
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: bja8og

## Workflow history
- 2026-08-29 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Finalize bja8og (tabcomp-01 shell completion): implemented+verified this run (3d2461b/0b216c9); lifecycle move stranded by the pre-isolation race. Scope committed. [Scope reconciliation - in-scope-unmodified agent_workflows/cli.py: already-committed; in-scope-unmodified agent_workflows/completion.py: already-committed; in-scope-unmodified tests/test_completion.py: already-committed]
- 2026-08-28 approved (aw set): status set to approved

- 2026-08-28 reviewed (OpenCode/its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Added command-visibility filter policy (E-01), shell-escaping discipline for special chars in help text (E-02), forward-compatible `completion` parser shape to unblock child 03's install/uninstall (E-03), and shell-own-parser syntax-validity + escaping tests (E-04); scoped the concern to STATIC generation; strengthened V-items to demand concrete evidence.
- 2026-08-28 to-review (Antigravity): authored detailed atomic implementation plan for native shell completion generators.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Provide pure, zero-runtime-dependency completion script generators for Bash, Zsh, and Fish that introspect the `argparse` CLI action tree dynamically and emit syntax-clean completion definitions for `aw`, `agentwf`, and `agent-workflows` via `aw completion <shell>`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Parser Introspection and Shell Script Generators (`agent_workflows/completion.py`)

- [x] E-01 Implement `introspect_cli_tree(parser)` in `agent_workflows/completion.py` that recursively extracts subcommands, positional choices, and option flags (`--flag`, `-f`) from `argparse.ArgumentParser` and `_SubParsersAction` objects into a clean dictionary tree representation. Model the recursion on the existing `_apply_descriptions` walker (`agent_workflows/cli.py:432-442`), which already traverses `_SubParsersAction.choices`. Apply one explicit command-visibility policy so completion surfaces only real user commands. The single filter EXCLUDES both the internal gate commands (the `*-gate` family: `ipd-executed-gate`, `ipd-status-untooled-gate`, `backlog-blocking-close-gate`, `ipd-dependency-statement-gate`, `precommit-scope-gate`, `prepush-authorization-gate`) and every subparser whose help is `argparse.SUPPRESS` or that has no `_choices_actions` help entry (the hidden aliases `att`, `spec`, `sanitize`, `antigravity`, `opencode`). Add a code comment recording that the pre-argparse forwarding pseudo-commands `oc`/`opencode`, `agy`/`antigravity`, and `pwatch` (intercepted in `_dispatch` at `agent_workflows/cli.py:7474-7511` before parsing) have no argparse subtree, so their nested commands are not statically completable and are out of scope for this child.
  - Depends on: none
  - Expected outcome: `introspect_cli_tree(_build_parser())` returns a structured dictionary of user-facing commands, nested subcommands, and flags without altering the parser, and the internal gate commands and hidden aliases enumerated above are absent from the tree.
  - Done note: Implemented `introspect_cli_tree(parser)` in `agent_workflows/completion.py` (recurses `_SubParsersAction.choices`, modeled on `_apply_descriptions`). The visibility policy lives in `_visible_subcommands`: include a name only if it has a `_choices_actions` help entry (EXCLUDES the 5 argparse aliases att/spec/sanitize/antigravity/opencode, which share the parent parser and carry no separate help entry), skip `help is argparse.SUPPRESS`, and skip any name ending `-gate` (the 6 internal gate hooks). Added the required code comment noting the oc/opencode/agy/antigravity/pwatch forwarding pseudo-commands are intercepted pre-parse and have no argparse subtree (out of scope). Verified: the tree has install/check/doctor/runs/ipd/specs/completion, excludes all `*-gate`, and excludes all 5 hidden aliases; the parser is not mutated.
  - Execution state: performed

- [x] E-02 Implement `generate_bash_completion()`, `generate_zsh_completion()`, and `generate_fish_completion()` in `agent_workflows/completion.py` that consume the introspected CLI tree and emit self-contained shell completion scripts binding all three entrypoints (`aw`, `agentwf`, `agent-workflows`). Every emitted token that originates from the parser (command names, flag strings, and any help/description text used for Zsh/Fish descriptions) MUST be shell-escaped for its target shell before interpolation, because argparse help text in this CLI contains shell-special characters (verified: backticks and `$` appear in flag help, e.g. the `--scope-reason`/`--scope-ack`/`--path` help strings and the `-- <cmd>` positionals). Use a per-shell quoting helper (e.g. `shlex.quote` for POSIX single-word tokens, and explicit escaping of `` ` ``, `$`, `\`, `"`, and `'` where descriptions are embedded) so no emitted script can be broken or command-injected by help text.
  - Depends on: E-01
  - Expected outcome: Each generator returns a non-empty string containing valid, shell-specific completion declarations (`complete -F _aw_completion` for Bash, `#compdef` / `_arguments` for Zsh, `complete -c` for Fish), and a generated script embedding a flag whose help contains a backtick or `$` remains syntactically valid (no unescaped metacharacters).
  - Done note: Implemented `generate_bash_completion`/`generate_zsh_completion`/`generate_fish_completion` over the introspected tree, each binding `aw agentwf agent-workflows`. Bash: a `_aw_completion` function + `complete -F _aw_completion aw agentwf agent-workflows`, every word `shlex.quote`d and the whole compgen word list single-quoted. Zsh: `#compdef aw agentwf agent-workflows` + `_arguments`/`_values`, descriptions run through `_zsh_desc` (escapes `\`/`'`/backtick/`$`/`:`/`[`/`]`). Fish: `complete -c <entry>` with `__fish_use_subcommand`/`__fish_seen_subcommand_from`, tokens/descriptions Fish-escaped (`_fish_word`/`_fish_desc`). Per-shell quoting helpers keep help text (which contains backticks + `$`, e.g. `--scope-ack`) from breaking/injecting the script. Verified: `bash -n` passes on the real generated script AND on a synthetic hostile tree whose help contains `` `rm -rf $HOME` `` + quotes + backslash.
  - Execution state: performed

### Task group 2: CLI Subcommand Wiring (`agent_workflows/cli.py`)

- [x] E-03 Register the `aw completion` subcommand in `agent_workflows/cli.py` accepting an optional `shell` argument (`bash`, `zsh`, `fish`, defaulting to detecting the active shell from `os.environ.get("SHELL")`, falling back to `bash` when unset/unparseable per OQ-01) and emitting the corresponding generated script to stdout with exit code 0, then wire dispatch in `_dispatch` (`agent_workflows/cli.py:7464+`) alongside the other `args.command == ...` branches. PARSER SHAPE (forward-compatibility requirement, blocks child 03): `shell` MUST NOT be a bare positional with `choices={bash,zsh,fish}`, because child 03 (`tabcomp-03` E-02) later adds `aw completion install` and `aw completion uninstall`, which would collide with a positional-shell design. Instead register `completion` with its OWN sub-action layer: a default/output behavior when a bare shell name is given, structured so `install`/`uninstall` sub-actions can be added without reshaping the parser (e.g. a `completion` subparser whose first positional accepts the shell names AND is extensible to the `install`/`uninstall` verbs, or an equivalent shape child 03 can extend additively). Document the chosen shape in a code comment referencing `tabcomp-03` so the next executor does not undo it.
  - Depends on: E-02
  - Expected outcome: Invocations of `aw completion bash`, `aw completion zsh`, and `aw completion fish` write their respective completion scripts to stdout and exit cleanly with code 0; `aw completion` with no argument emits the `$SHELL`-detected (or bash-fallback) script; and the parser shape leaves room for child 03 to add `install`/`uninstall` without a redesign.
  - Done note: Registered the `completion` subparser in `_build_parser` with a FREE-FORM optional positional `target` (metavar `bash|zsh|fish`, `nargs="?"`, NO `choices=`) plus a load-bearing code comment referencing tabcomp-03 so `install`/`uninstall` can be added additively without reshaping the parser. Wired `if args.command == "completion": return _run_completion(args)` in `_dispatch` (alongside the other `args.command` branches). `_run_completion` resolves `target` (or `_detect_shell()` -> $SHELL basename in {bash,zsh,fish} else bash) and streams `completion.generate(shell)` to stdout (exit 0; clean stdout so `source <(aw completion bash)` works); an unknown target -> stderr error + exit 2. Also added the `completion` `_DESCRIPTIONS` entry (in-scope cli.py). Verified live: `aw completion bash|zsh|fish` exit 0 with correct headers; bare `aw completion` with SHELL unset -> bash script; SHELL=/usr/bin/zsh -> zsh script; `parser.parse_args(["completion","install"])` yields `target=="install"` (no choices rejection) proving child-03 extensibility.
  - Execution state: performed

### Task group 3: Comprehensive Unit Tests (`tests/test_completion.py`)

- [x] E-04 Implement unit tests in `tests/test_completion.py` (stdlib `unittest.TestCase`, invoking `cli.main([...])` under `redirect_stdout` per the existing `tests/test_cli_help_and_errors.py` convention) testing: `introspect_cli_tree` (asserts top-level user commands like `install`/`check`/`doctor`/`runs`/`ipd`/`specs` are present AND the internal gate commands and hidden aliases from E-01 are ABSENT); each generator function (`generate_bash_completion`, `generate_zsh_completion`, `generate_fish_completion`) for required syntax and alias coverage (`aw`, `agentwf`, `agent-workflows`); a shell-syntax validity check for each generated script using the shell's own parser (`bash -n`, `zsh -n`, `fish --no-execute`), skipped gracefully via `unittest.skipUnless(shutil.which(<shell>))` when the shell is not installed; the escaping guarantee from E-02 (a generated script remains syntactically valid despite help text containing a backtick/`$`); and CLI stdout emission and exit code 0 via `aw completion bash|zsh|fish`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: All generator and CLI tests pass under `pytest tests/test_completion.py` with 100% assertions satisfied; where `bash`/`zsh`/`fish` are installed on the runner, the shell-syntax checks pass (and are skipped, not failed, where absent).
  - Done note: Implemented `tests/test_completion.py` (stdlib unittest, `cli.main([...])` under `redirect_stdout` per the test_cli_help_and_errors convention): IntrospectTreeTests (user commands present; `*-gate` + hidden aliases absent; nested recursion; no parser mutation), GeneratorSyntaxTests (required syntax + alias coverage for all three; `bash -n`/`zsh -n`/`fish --no-execute` guarded by `skipUnless(shutil.which(...))`; the backtick/`$` escaping guarantee), CompletionCliTests (bash/zsh/fish exit 0 + headers; SHELL-unset bash fallback; zsh detection; `_detect_shell` fallback; the child-03 parser-shape extensibility). Result: `16 passed, 2 skipped` (the 2 skips are the zsh/fish `-n` checks - those shells are absent on this runner, gracefully skipped not failed).
  - Execution state: performed

## Project conventions discovered (Step 0)

- Zero Runtime Dependencies: Must not import third-party packages (e.g. `shtab`, `click`). Use only standard library `argparse`, `os`, `sys`, `pathlib`.
- Console Script Aliases: Must bind `aw`, `agentwf`, and `agent-workflows` as declared in `pyproject.toml:55-57`.
- Clean Standard Output: `aw completion <shell>` must output only the raw script to stdout so it can be evaluated directly via `source <(aw completion bash)`.

## Findings

- Introspecting the `ArgumentParser` tree at runtime ensures newly added subcommands and options in `cli.py` automatically appear in completion scripts without manual synchronization. The CLI exposes 136 (sub)parsers; a naive dump would include internal `*-gate` commands and hidden aliases, so E-01 applies an explicit visibility filter. The existing `_apply_descriptions` walker (`cli.py:432-442`) is the reusable recursion pattern.
- Generating native Zsh `#compdef` and native Fish `complete -c` provides significantly better completions, descriptions, and performance than relying on bash-compatibility shims in non-bash shells. Because Zsh/Fish embed help text as descriptions, and this CLI's help text contains shell-special characters (`` ` ``, `$`), the generators MUST escape emitted tokens (E-02).
- FORWARD-COMPATIBILITY WITH CHILD 03: the `aw completion` parser must be shaped so `tabcomp-03` (`jolfpj`) can add `install`/`uninstall` sub-actions without reshaping it; a bare `choices={bash,zsh,fish}` positional would collide. Captured as an explicit E-03 requirement to avoid rework in the dependent child.
- D46 is dependency MINIMIZATION, not a hard prohibition (DECISIONS.md, and `pyproject.toml:26-28`); this child needs no new dependency (stdlib `argparse`/`shlex`/`os`/`shutil` suffice), so "zero runtime dependency" is satisfied by construction here.

## Proposed changes (ordered, validatable)

1. `agent_workflows/completion.py`: Create module with `introspect_cli_tree`, `generate_bash_completion`, `generate_zsh_completion`, `generate_fish_completion`.
2. `agent_workflows/cli.py`: Add `completion` subparser and command handler.
3. `tests/test_completion.py`: Add unit tests for introspection, script generation, and CLI output.

## Deferred / out of scope (with reason)

- Dynamic repository artifact queries (e.g. completing Set IDs and plan IDs): Handled in Child 02 (`tabcomp-02`).
- Drop-in filesystem installation and install wizard integration: Handled in Child 03 (`tabcomp-03`).

## Scope check

- Over-scope: none.
- Under-scope: none (provides complete static script generation and CLI output for Bash, Zsh, and Fish).
- Right-sizing (reviewer, plan-review): `aw ipd lint` raises the ADVISORY density flag (`IPD-Z602`) on E-02/E-03/E-04. Each was re-evaluated against the "one concern / one focused pass / one test-surface" test and judged correctly sized: E-02 is one concern (three cohesive sibling generators over the same introspected tree plus a shared escaping helper; the "because argparse help contains special chars" clause is a rationale, not a separate deliverable); E-03 is one deliverable (registering a command and wiring its dispatch are inseparable, and the forward-compatible parser shape is a design constraint on that same deliverable); E-04 is the single per-child test file (one test-surface mapped 1:1 to V-04, matching the convention of siblings 02/03). The advisory fires on rationale/example clauses, not genuine multi-deliverable bundling, and does not affect conformance (lint exit 0).

## Required tests / validation

- `tests/test_completion.py`:
  - Test `introspect_cli_tree` extracts top-level commands (`install`, `check`, `doctor`, `runs`, `ipd`, `specs`, etc.) and their flags, AND asserts the internal gate commands (`*-gate`) and hidden aliases (`att`, `spec`, `sanitize`, `antigravity`, `opencode`) are excluded from the tree.
  - Test `generate_bash_completion()` output contains `_aw_completion()` function and `complete -F _aw_completion aw agentwf agent-workflows`.
  - Test `generate_zsh_completion()` output contains `#compdef aw agentwf agent-workflows`.
  - Test `generate_fish_completion()` output contains `complete -c aw` and `complete -c agentwf`.
  - Test each generated script parses under its shell's own syntax checker (`bash -n` / `zsh -n` / `fish --no-execute`), skipped when the shell is not installed.
  - Test the escaping guarantee: a generated script whose embedded help text contains a backtick or `$` still passes the shell syntax check (no unescaped metacharacter breaks or injects the script).
  - Test `aw completion bash` CLI exit code is 0 and stdout starts with `# bash completion for aw`.
  - Test `aw completion` with no argument and `SHELL` unset emits the bash script (OQ-01 fallback).

## Spec / documentation sync

- Help text for `aw completion` subcommand.

## Open questions

### OQ-01: Should shell detection fallback to bash if $SHELL is unset?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Yes. If no shell argument is given and `SHELL` is empty or unparseable, default to `bash` as the standard POSIX baseline.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Unit test asserting `introspect_cli_tree` returns the registered USER subcommands and options from `_build_parser()` AND excludes the internal gate commands and hidden aliases enumerated in E-01. Paste the passing test output.
  - Observed evidence: `python3 -m pytest tests/test_completion.py -o addopts="" -v` -> `16 passed, 2 skipped`. IntrospectTreeTests all PASSED: `test_user_commands_present` (install/check/doctor/runs/ipd/specs/completion present), `test_gate_commands_excluded` (all six `*-gate` names absent + no name ends `-gate`), `test_hidden_aliases_excluded` (att/spec/sanitize/antigravity/opencode absent), `test_nested_subcommands_captured` (ipd exposes nested subs), `test_does_not_mutate_parser` (parser `_actions` unchanged). Live cross-check: `introspect_cli_tree(cli._build_parser())` top-level has install/check/doctor/ipd/specs, excludes gates, excludes the 5 aliases.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Unit tests proving `generate_bash_completion`, `generate_zsh_completion`, and `generate_fish_completion` return non-empty strings with required shell syntax, PLUS the shell-own-parser validity checks (`bash -n`/`zsh -n`/`fish --no-execute`) passing where the shell is installed (and the escaping test passing). Paste the test output, noting which shell checks ran vs. were skipped for absence.
  - Observed evidence: From the same `16 passed, 2 skipped -v` run. GeneratorSyntaxTests PASSED: `test_bash_required_syntax_and_aliases` (`_aw_completion()` + `complete -F _aw_completion aw agentwf agent-workflows`), `test_zsh_required_syntax_and_aliases` (`#compdef aw agentwf agent-workflows`), `test_fish_required_syntax_and_aliases` (`complete -c aw` + `complete -c agentwf` + `complete -c agent-workflows`), `test_bash_parses_under_bash_n` PASSED (bash IS installed), `test_escaping_guarantee_backtick_and_dollar` PASSED (a hostile tree with `` `rm -rf $HOME` `` help still passes `bash -n`; `_zsh_desc` leaves no unescaped backtick/`$`). SKIPPED (shell absent on runner, not failed): `test_zsh_parses_under_zsh_n` (SKIPPED: zsh not installed), `test_fish_parses_under_fish_no_execute` (SKIPPED: fish not installed). Live: `bash -n <(aw completion bash)` -> OK.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: CLI test executing `aw completion bash`, `aw completion zsh`, and `aw completion fish` with exit code 0, plus a test that `aw completion` with `SHELL` unset emits the bash script, plus confirmation (code inspection or a child-03-forward test) that the `completion` parser shape admits future `install`/`uninstall` sub-actions without redesign. Paste the test output.
  - Observed evidence: From the same run. CompletionCliTests PASSED: `test_cli_bash_exit0_and_header` (rc 0, stdout starts `# bash completion for aw`), `test_cli_zsh_and_fish_exit0` (zsh -> `#compdef`, fish -> `complete -c aw`, both rc 0), `test_bare_completion_shell_unset_falls_back_to_bash` (SHELL popped -> bash script, OQ-01), `test_bare_completion_detects_zsh_from_shell_env` (SHELL=/usr/bin/zsh -> `#compdef`), `test_detect_shell_fallback` (tcsh -> bash; fish -> fish), `test_parser_shape_allows_child03_extension` (`parser.parse_args(["completion","install"])` -> `target=="install"`, i.e. NOT constrained by `choices=`, so tabcomp-03 install/uninstall parse without redesign). Live: `aw completion bash|zsh|fish` all exit 0 with correct headers.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `pytest tests/test_completion.py` runs with all tests passing.
  - Observed evidence: `python3 -m pytest tests/test_completion.py -o addopts=""` -> `16 passed, 2 skipped in 0.73s` (all assertions satisfied; the 2 skips are the zsh/fish shell-syntax checks, skipped-not-failed because those shells are absent on this runner). ruff `--select E4,E7,E9,F` on completion.py/cli.py/test_completion.py -> `All checks passed!`; ruff-format clean. NOTE (run DECISION 12-bja8og-D1): the pre-existing-red CLI-conformance guards `test_cli.py::...fuller_description` and `test_cli_conformance_matrix.py::...` remain red on 33 UNRELATED undeclared leaves (oc/agy/pwatch/*-gate/commit/finish/test/work begin/research set-outcome/spec new/...) that predate this turn (proven via `git show ccda13f`); `completion` now carries a `_DESCRIPTIONS` entry, and declaring it in the out-of-scope `tests/conformance_matrix.py` is left as a noted housekeeping follow-up (not in this plan's Scope-Paths).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
