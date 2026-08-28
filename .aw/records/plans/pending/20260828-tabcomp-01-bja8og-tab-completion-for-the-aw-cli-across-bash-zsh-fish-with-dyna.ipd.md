# IPD: Native shell completion script generators for Bash, Zsh, and Fish with CLI output subcommand

- Date: 2026-08-28
- Kind: child
- Concern: The `aw` CLI provides dozens of nested subcommands and flags across three executable aliases (`aw`, `agentwf`, `agent-workflows`), but has no completion generator. Users have no way to generate native completion scripts for their shells without relying on external third-party tools or manually writing shell logic.
- Scope: Implement native, zero-dependency completion script generators for Bash, Zsh, and Fish: (1) Add `agent_workflows/completion.py` with `introspect_cli_tree`, `generate_bash_completion`, `generate_zsh_completion`, and `generate_fish_completion`; (2) Add `aw completion [bash|zsh|fish]` subcommand to `agent_workflows/cli.py` to stream the generated completion script to stdout; (3) Add unit tests in `tests/test_completion.py` verifying script syntax, alias binding, and CLI execution.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py
- Item-Dependencies: none
- Status: to-review
- Set: tabcomp
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: bja8og

## Workflow history

- 2026-08-28 to-review (Antigravity): authored detailed atomic implementation plan for native shell completion generators.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Provide pure, zero-runtime-dependency completion script generators for Bash, Zsh, and Fish that introspect the `argparse` CLI action tree dynamically and emit syntax-clean completion definitions for `aw`, `agentwf`, and `agent-workflows` via `aw completion <shell>`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Parser Introspection and Shell Script Generators (`agent_workflows/completion.py`)

- [ ] E-01 Implement `introspect_cli_tree(parser)` in `agent_workflows/completion.py` that recursively extracts subcommands, positional choices, and option flags (`--flag`, `-f`) from `argparse.ArgumentParser` and `_SubParsersAction` objects into a clean dictionary tree representation.
  - Depends on: none
  - Expected outcome: `introspect_cli_tree(_build_parser())` returns a structured dictionary of commands, nested subcommands, and flags without altering the parser.
  - Execution state: pending

- [ ] E-02 Implement `generate_bash_completion()`, `generate_zsh_completion()`, and `generate_fish_completion()` in `agent_workflows/completion.py` that consume the introspected CLI tree and emit self-contained shell completion scripts binding all three entrypoints (`aw`, `agentwf`, `agent-workflows`).
  - Depends on: E-01
  - Expected outcome: Each generator returns a non-empty string containing valid, shell-specific completion declarations (`complete -F _aw_completion` for Bash, `#compdef` / `_arguments` for Zsh, `complete -c` for Fish).
  - Execution state: pending

### Task group 2: CLI Subcommand Wiring (`agent_workflows/cli.py`)

- [ ] E-03 Register the `aw completion` subcommand in `agent_workflows/cli.py` accepting an optional `shell` argument (`bash`, `zsh`, `fish`, defaulting to detecting the active shell from `os.environ.get("SHELL")`) and emitting the corresponding generated script to stdout with exit code 0.
  - Depends on: E-02
  - Expected outcome: Invocations of `aw completion bash`, `aw completion zsh`, and `aw completion fish` write their respective completion scripts to stdout and exit cleanly with code 0.
  - Execution state: pending

### Task group 3: Comprehensive Unit Tests (`tests/test_completion.py`)

- [ ] E-04 Implement unit tests in `tests/test_completion.py` testing `introspect_cli_tree`, each generator function (`generate_bash_completion`, `generate_zsh_completion`, `generate_fish_completion`), alias coverage (`aw`, `agentwf`, `agent-workflows`), and CLI stdout emission via `aw completion <shell>`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: All generator and CLI tests pass under `pytest tests/test_completion.py` with 100% assertions satisfied.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Zero Runtime Dependencies: Must not import third-party packages (e.g. `shtab`, `click`). Use only standard library `argparse`, `os`, `sys`, `pathlib`.
- Console Script Aliases: Must bind `aw`, `agentwf`, and `agent-workflows` as declared in `pyproject.toml:55-57`.
- Clean Standard Output: `aw completion <shell>` must output only the raw script to stdout so it can be evaluated directly via `source <(aw completion bash)`.

## Findings

- Introspecting the `ArgumentParser` tree at runtime ensures newly added subcommands and options in `cli.py` automatically appear in completion scripts without manual synchronization.
- Generating native Zsh `#compdef` and native Fish `complete -c` provides significantly better completions, descriptions, and performance than relying on bash-compatibility shims in non-bash shells.

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

## Required tests / validation

- `tests/test_completion.py`:
  - Test `introspect_cli_tree` extracts top-level commands (`install`, `check`, `doctor`, `runs`, `ipd`, `specs`, etc.) and their flags.
  - Test `generate_bash_completion()` output contains `_aw_completion()` function and `complete -F _aw_completion aw agentwf agent-workflows`.
  - Test `generate_zsh_completion()` output contains `#compdef aw agentwf agent-workflows`.
  - Test `generate_fish_completion()` output contains `complete -c aw` and `complete -c agentwf`.
  - Test `aw completion bash` CLI exit code is 0 and stdout starts with `# bash completion for aw`.

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

- [ ] V-01 validates E-01
  - Required evidence: Unit test asserting `introspect_cli_tree` returns all registered subcommands and options from `_build_parser()`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Unit tests proving `generate_bash_completion`, `generate_zsh_completion`, and `generate_fish_completion` return non-empty strings with required shell syntax.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: CLI test executing `aw completion bash`, `aw completion zsh`, and `aw completion fish` with exit code 0.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `pytest tests/test_completion.py` runs with all tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
