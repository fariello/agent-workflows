# IPD: Dynamic contextual artifact resolver and argcomplete soft-import for aw tab-completion

- Date: 2026-08-28
- Kind: child
- Concern: Static completion can suggest subcommands and flags, but cannot complete dynamic repository artifacts such as Set IDs (e.g. `tabcomp`, `xprio`, `reslife`), plan IDs (`id6`), spec IDs, backlog IDs, run IDs, or status keywords based on the current repository state.
- Scope: Implement dynamic contextual artifact completion and argcomplete ecosystem support: (1) Add `complete_query(words, cword, repo_root)` and artifact completers to `agent_workflows/completion.py`; (2) Wire hidden `aw __complete` subparser in `agent_workflows/cli.py` to handle shell query callbacks; (3) Add `# PYTHON_ARGCOMPLETE_OK` header and soft-imported `argcomplete.autocomplete(parser)` with custom completers in `agent_workflows/cli.py`; (4) Add comprehensive unit tests in `tests/test_completion.py`.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py
- Item-Dependencies: executed:bja8og
- Status: to-review
- Set: tabcomp
- Order: 2
- Highest E allocated: 04
- Author: Antigravity
- Id: 4f1j25

## Workflow history

- 2026-08-28 to-review (Antigravity): authored detailed atomic implementation plan for dynamic artifact resolution and argcomplete integration.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Enable high-speed (<50ms) dynamic completion of active Set IDs, plan IDs, spec IDs, backlog IDs, run IDs, and status keywords via `aw __complete`, and enable automatic global Python argcomplete support without adding any mandatory runtime dependencies.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Dynamic Artifact Query Engine (`agent_workflows/completion.py`)

- [ ] E-01 Implement `complete_query(words: list[str], cword: int, repo_root: Optional[Path] = None) -> list[str]` in `agent_workflows/completion.py` that parses the input token stream and returns matching completion candidates: (a) subcommands and flags if in command position; (b) Set IDs and run IDs if completing `aw run` or `aw runs`; (c) plan, spec, or backlog `id6` hashes if completing entity commands (`aw ipd`, `aw specs`, `aw backlog`, `aw find`); (d) status enum tokens if completing status arguments.
  - Depends on: none
  - Expected outcome: `complete_query` returns precise, prefix-matching strings evaluated against the active repository state using `agent_workflows.selectors` and `agent_workflows.artifact_core` in under 50ms.
  - Execution state: pending

### Task group 2: CLI Query Hook and argcomplete Integration (`agent_workflows/cli.py`)

- [ ] E-02 Register the hidden `__complete` subcommand in `agent_workflows/cli.py` that accepts command tokens and cursor index, invokes `complete_query`, and prints matching candidate lines to stdout.
  - Depends on: E-01
  - Expected outcome: Invocations of `aw __complete -- <tokens>` output newline-delimited completion strings suitable for shell hook consumption.
  - Execution state: pending

- [ ] E-03 Add `# PYTHON_ARGCOMPLETE_OK` header to `agent_workflows/cli.py` and implement a soft-imported `argcomplete.autocomplete(parser)` hook with custom completer callables attached to artifact and Set arguments.
  - Depends on: E-01, E-02
  - Expected outcome: If `argcomplete` is installed in the Python environment, it handles autocompletion seamlessly; if absent, the import is caught with zero errors and normal execution proceeds.
  - Execution state: pending

### Task group 3: Testing and Validation (`tests/test_completion.py`)

- [ ] E-04 Implement unit tests in `tests/test_completion.py` testing `complete_query` for subcommands, flags, Set IDs, plan IDs, run IDs, status keywords, `aw __complete` CLI invocation, and `argcomplete` soft-import resilience when missing or present.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: All dynamic query and argcomplete test cases pass with 100% assertions satisfied under `pytest tests/test_completion.py`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Fast Latency (<50ms): Tab-completion queries run interactively on keypress. Queries must avoid heavy disk sweeps and reuse cached indices (`plans_index`, `selectors`) whenever possible.
- Artifact Authorities: Re-use `agent_workflows.selectors.resolve_selectors` and `agent_workflows.artifact_core` for entity ID lookups rather than reimplementing ad-hoc filesystem scans.
- Zero Hard Dependency on argcomplete: Must use `try: import argcomplete ... except ImportError: pass` to strictly adhere to zero runtime dependency policy (D44/D46).

## Findings

- Wiring the shell generator from Child 01 (`bja8og`) to query `aw __complete` for positionals provides real-time contextual completion directly from git/repo state without complex shell scripting.
- Python `argcomplete` uses `PYTHON_ARGCOMPLETE_OK` in the first 1024 bytes of the script to identify completion-capable executables.

## Proposed changes (ordered, validatable)

1. `agent_workflows/completion.py`: Implement `complete_query` and helper completer functions.
2. `agent_workflows/cli.py`: Register `__complete` command, add `# PYTHON_ARGCOMPLETE_OK`, and wire soft `argcomplete` hook.
3. `tests/test_completion.py`: Add unit tests for dynamic query resolution across all artifact types and argcomplete compatibility.

## Deferred / out of scope (with reason)

- Shell completion script generation: Delivered in Child 01 (`tabcomp-01`).
- Drop-in filesystem installation and install wizard integration: Handled in Child 03 (`tabcomp-03`).

## Scope check

- Over-scope: none.
- Under-scope: none (covers dynamic artifact queries, CLI hook, argcomplete integration, and comprehensive test suite).

## Required tests / validation

- `tests/test_completion.py`:
  - Test `complete_query(["aw", "r"], 1)` returns `["run", "runs", "research"]`.
  - Test `complete_query(["aw", "run", "t"], 2)` in a repo containing set `tabcomp` returns `["tabcomp"]`.
  - Test `complete_query(["aw", "ipd", "lint", "b"], 3)` returns `["bja8og"]`.
  - Test `complete_query(["aw", "ipd", "set", "a"], 3)` returns `["approved", "auto-approved"]`.
  - Test `aw __complete` CLI output matches `complete_query`.
  - Test `cli.py` execution succeeds without error when `argcomplete` is uninstalled.

## Spec / documentation sync

- Inline documentation for `__complete` and `complete_query`.

## Open questions

### OQ-01: How does __complete distinguish between flags and positionals?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: If the current word starts with `-`, `complete_query` returns matching option flags for the current subparser context; otherwise it delegates to the active positional completer for that subcommand position.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests demonstrating `complete_query` returns expected candidate lists for subcommands, Set IDs, plan IDs, and status enums across test repos.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: CLI test executing `aw __complete -- aw ru` emitting matching subcommands to stdout.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Code inspection proving `# PYTHON_ARGCOMPLETE_OK` is on line 1 or 2, and unit test proving `cli.py` imports cleanly with and without `argcomplete`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `pytest tests/test_completion.py` runs with all dynamic query tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
