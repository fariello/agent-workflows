# IPD: Tab completion for the aw CLI across Bash, Zsh, and Fish with dynamic artifact query and argcomplete soft-import

- Date: 2026-08-28
- Kind: child
- Concern: The `aw` CLI (and its aliases `agentwf` and `agent-workflows`) provides dozens of subcommands, arguments, and options, but offers no shell tab-completion. Users currently have to remember or re-type complex subcommand paths, flag names, and 6-character artifact handles (`id6`), Set IDs, run IDs, and status keywords manually.
- Scope: Implement native shell completion for `aw` across Bash, Zsh, and Fish with zero required dependencies: (1) Add `agent_workflows/completion.py` with pure shell completion generators for Bash, Zsh, and Fish and a fast dynamic query resolver; (2) Add `aw completion <bash|zsh|fish>` subcommand in `agent_workflows/cli.py` and wire a hidden `__complete` CLI query hook; (3) Add `# PYTHON_ARGCOMPLETE_OK` and a soft-imported `argcomplete.autocomplete(parser)` hook with custom completers for artifact IDs, Set IDs, run IDs, and status keywords; (4) Add tests in `tests/test_completion.py` and document setup instructions.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py, README.md
- Item-Dependencies: none
- Status: to-review
- Set: tabcomp
- Order: 1
- Highest E allocated: 06
- Author: Antigravity
- Id: bja8og

## Workflow history

- 2026-08-28 to-review (Antigravity): authored detailed implementation plan covering native bash/zsh/fish completion, dynamic artifact query, and argcomplete integration.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Provide comprehensive, high-performance tab-completion for `aw` across Bash, Zsh, and Fish that works with zero external runtime dependencies via `aw completion <shell>`, supports dynamic contextual completion of repository artifacts (Set IDs, plan IDs, spec IDs, backlog IDs, run IDs, and status tokens), and enables automatic ecosystem integration for users running `argcomplete`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Native completion generators and dynamic query engine (`agent_workflows/completion.py`)

- [ ] E-01 Implement `agent_workflows/completion.py` with standalone shell completion script generators for Bash (using `complete -F`), Zsh (using `#compdef` and `_arguments`), and Fish (using `complete -c`). Ensure generated scripts complete all three entrypoint aliases (`aw`, `agentwf`, `agent-workflows`) and function with zero external runtime dependencies.
  - Depends on: none
  - Expected outcome: `generate_bash_completion()`, `generate_zsh_completion()`, and `generate_fish_completion()` return valid, syntax-clean shell completion scripts.
  - Execution state: pending

- [ ] E-02 Implement the dynamic completion resolver (`complete_query` and helper completers) in `agent_workflows/completion.py` that queries active subcommands, flags, and repository artifacts (Set IDs, plan IDs, spec IDs, backlog IDs, run IDs, and valid status enums) using `agent_workflows.selectors` and `agent_workflows.artifact_core`.
  - Depends on: E-01
  - Expected outcome: Given a token prefix and context (e.g. `aw find <prefix>`, `aw run <prefix>`, `aw ipd set <status> <prefix>`), `complete_query` returns matching strings and short descriptions in milliseconds.
  - Execution state: pending

### Task group 2: CLI integration and soft-import hook (`agent_workflows/cli.py`)

- [ ] E-03 Add `aw completion [bash|zsh|fish]` subcommand to `agent_workflows/cli.py` to output the corresponding shell script, plus a hidden `aw __complete ...` dispatch command used by shell hooks for dynamic context-aware completions.
  - Depends on: E-01, E-02
  - Expected outcome: Running `aw completion bash` outputs the bash completion script to stdout; running `aw __complete <args>` outputs tab-delimited completion candidates.
  - Execution state: pending

- [ ] E-04 Add `# PYTHON_ARGCOMPLETE_OK` header and soft-imported `argcomplete` hook in `agent_workflows/cli.py` before argument parsing, wiring custom completers for artifact IDs, Set IDs, run IDs, and status keywords when `argcomplete` is installed.
  - Depends on: E-02, E-03
  - Expected outcome: `argcomplete.autocomplete(parser)` is invoked safely if `argcomplete` is present in the environment; no-op if missing (no crash, zero runtime dependency requirement preserved).
  - Execution state: pending

### Task group 3: Testing and documentation (`tests/test_completion.py`, `README.md`)

- [ ] E-05 Implement comprehensive unit tests in `tests/test_completion.py` validating bash/zsh/fish script generation, static subcommand/flag completion trees, dynamic artifact completion (plans, specs, backlog, runs, status enums), and `argcomplete` soft-import resilience.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: All completion test cases pass with 100% assertion verification under `pytest`.
  - Execution state: pending

- [ ] E-06 Update documentation (`README.md` and CLI help text) with user instructions for activating tab-completion in `~/.bashrc`, `~/.zshrc`, and `~/.config/fish/config.fish` (e.g. `source <(aw completion bash)`).
  - Depends on: E-03
  - Expected outcome: Clear, copy-pasteable instructions are present in documentation for all supported shells.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Zero runtime dependencies: The package maintains `dependencies = []` in `pyproject.toml` (DECISIONS D44/D46/D138). Native completion scripts and dynamic query helpers must rely strictly on standard library Python and native shell facilities.
- Multi-alias support: The package registers three console scripts (`aw`, `agentwf`, `agent-workflows`) in `pyproject.toml`. Completion must attach to all three command names.
- Artifact lookup authority: Plan, spec, research, and backlog resolution is unified under `agent_workflows.selectors.resolve_selectors` and `agent_workflows.artifact_core`. Dynamic completers must reuse these authorities to avoid duplicate file discovery code.
- Fast execution: CLI completion queries must execute in <50ms to ensure a responsive terminal experience during interactive tab key presses.

## Findings

- Pure static completion scripts (subcommands and option flags) can be generated directly by inspecting the `argparse.ArgumentParser` action tree at build or runtime.
- Dynamic completion (e.g. suggesting Set IDs like `tabcomp`, `xprio`, `reslife` or plan IDs like `bja8og`) requires evaluating the current repository state on demand when the user presses `<TAB>`.
- Hybrid approach (native `aw completion` generator + fast hidden `__complete` fallback + soft `argcomplete` hook) provides the ideal developer experience without forcing any dependencies on minimal installs.

## Proposed changes (ordered, validatable)

1. `agent_workflows/completion.py`: Create module with `generate_bash_completion()`, `generate_zsh_completion()`, `generate_fish_completion()`, and `complete_query()`.
2. `agent_workflows/cli.py`: Register `completion` subcommand, `__complete` hidden command, and `# PYTHON_ARGCOMPLETE_OK` soft-import.
3. `tests/test_completion.py`: Test suite verifying script generation, dynamic completions across artifact types, and parser argument compatibility.
4. `README.md`: Add Shell Tab Completion section with setup examples for Bash, Zsh, and Fish.

## Deferred / out of scope (with reason)

- PowerShell / Windows cmd completion: Deferred (Linux/macOS POSIX shells Bash/Zsh/Fish cover the primary user base; PowerShell can be added in a follow-up plan if requested).
- External completion frameworks (e.g. shtab / click / typer): Out of scope (would introduce external runtime dependencies contrary to D44/D46).

## Scope check

- Over-scope: none.
- Under-scope: none (provides complete native script generation, dynamic artifact queries, and argcomplete compatibility across Bash, Zsh, and Fish).

## Required tests / validation

- `tests/test_completion.py`:
  - Test `aw completion bash` produces valid bash syntax containing `complete -F _aw_completion aw agentwf agent-workflows`.
  - Test `aw completion zsh` produces valid zsh compdef syntax for `aw`, `agentwf`, `agent-workflows`.
  - Test `aw completion fish` produces valid fish completion directives.
  - Test `__complete` returns all top-level subcommands when given `aw ""` or `aw <prefix>`.
  - Test `__complete` returns valid Set IDs when completing `aw run <prefix>`.
  - Test `__complete` returns valid plan `id6` handles when completing `aw ipd <subcommand> <prefix>`.
  - Test soft-import of `argcomplete` does not raise errors when `argcomplete` is not installed.
  - Test execution time of `__complete` query is under 50ms.

## Spec / documentation sync

- Update `README.md` with tab completion setup instructions.
- Update `pyproject.toml` keywords or descriptions if applicable.

## Open questions

### OQ-01: Should completion script generation be static or dynamically introspect the ArgumentParser tree?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Dynamic introspection of the `ArgumentParser` tree inside `agent_workflows/completion.py` ensures that adding new subcommands or flags in `cli.py` automatically updates completion without maintaining manual shell script templates.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Script generation functions return valid syntax for bash, zsh, and fish covering `aw`, `agentwf`, and `agent-workflows`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Dynamic query engine returns matching subcommands, flags, Set IDs, plan `id6` hashes, and status tokens accurately.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `aw completion bash|zsh|fish` emits non-empty script output to stdout, and `aw __complete` outputs tab-delimited suggestions.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Header `# PYTHON_ARGCOMPLETE_OK` exists in `cli.py`, and `argcomplete` soft-import handles both missing and present module states without error.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `pytest tests/test_completion.py` runs with all tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `README.md` contains clear tab-completion configuration snippets for Bash, Zsh, and Fish.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
