# IPD: Comprehensive shell tab completion for aw across Bash, Zsh, and Fish with dynamic query and drop in installer integration

- Date: 2026-08-28
- Kind: orchestrator
- Concern: The `aw` CLI (and its console aliases `agentwf` and `agent-workflows`) provides dozens of subcommands, flags, and arguments, but offers no shell tab-completion. Developers must manually look up or re-type complex command paths, 6-character artifact handles (`id6`), Set IDs, run IDs, and status enums.
- Scope: Deliver clean, production-grade tab-completion for `aw` across Bash, Zsh, and Fish with zero external runtime dependencies: (1) Child 01 (`bja8og`): Core completion generation engine for Bash/Zsh/Fish and `aw completion <shell>` CLI command; (2) Child 02 (`4f1j25`): Dynamic contextual artifact query resolver (`aw __complete`) and soft-imported `argcomplete` hook; (3) Child 03 (`jolfpj`): Drop-in auto-discovery file installation (`aw completion install/uninstall`), alias symlinks, interactive install wizard prompt, `aw install --completion` flag, and documentation.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, agent_workflows/install_wizard.py, tests/test_completion.py, tests/test_install_wizard.py, README.md
- Item-Dependencies: none
- Status: to-review
- Set: tabcomp
- Order: 0
- Highest E allocated: 01
- Author: Antigravity
- Id: e6h1p3

## Workflow history

- 2026-08-28 to-review (Antigravity): refined orchestrator plan into 3 atomic, right-sized child plans with explicit verification boundaries.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Provide seamless, high-performance tab-completion for `aw` across Bash, Zsh, and Fish that requires zero external runtime dependencies, dynamically completes repository artifacts (Set IDs, plan IDs, spec IDs, backlog IDs, run IDs, status enums) in <50ms, installs cleanly into standard drop-in directories without polluting user dotfiles, and integrates smoothly into the `aw install` wizard.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors no direct feature code; children 01, 02, and 03 carry the deliverables. Its only execution step is whole-Set verification.

### Task group 1: Whole-Set Verification

- [ ] E-01 After children 01, 02, and 03 execute, run end-to-end set verification covering shell completion script generation, dynamic artifact completion queries, drop-in installer operations, and full test suite validation.
  - Depends on: none
  - Expected outcome: End-to-end tab completion functions cleanly across all supported shells with full test suite passing.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
| :--- | :--- | :--- | :--- |
| 01 | `bja8og` | Native completion generators (Bash, Zsh, Fish) and `aw completion <shell>` CLI output | none |
| 02 | `4f1j25` | Dynamic contextual artifact query resolver (`aw __complete`) and `argcomplete` soft-import | `executed:bja8og` |
| 03 | `jolfpj` | Drop-in auto-discovery installer (`aw completion install/uninstall`), alias symlinks, wizard prompt, `aw install --completion` flag, and documentation | `executed:4f1j25` |

## Completion criteria (the whole Set is done only when)

- `aw completion bash`, `aw completion zsh`, and `aw completion fish` output clean, syntax-valid completion scripts binding `aw`, `agentwf`, and `agent-workflows`.
- `aw __complete` dynamically returns matching repository artifacts (Set IDs, plan IDs, spec IDs, backlog IDs, run IDs, and status tokens) contextually in <50ms.
- `aw completion install` places completion files in standard user auto-discovery directories (`~/.local/share/bash-completion/completions/aw`, `~/.local/share/zsh/site-functions/_aw`, `~/.config/fish/completions/aw.fish`) with alias symlinks, leaving user RC files untouched.
- Interactive install wizard and `aw install --completion` support 1-step completion setup.
- Soft-import of `argcomplete` works automatically when installed, with zero required runtime dependencies when absent.
- Full test suite green under `pytest`.

## Cross-IPD validation

- Single source of truth: Dynamic completers in Child 02 reuse `agent_workflows.selectors` and `agent_workflows.artifact_core`.
- Clean separation: Child 01 delivers static generators; Child 02 delivers runtime dynamic query resolution; Child 03 delivers filesystem and installer integration.

## Cross-set dependencies

- No functional dependency on other in-flight sets. Disjoint files from `driverfin`, `rstodo`, `xprio`, and `runnernorm`.

## Deferred / out of scope (with reason)

- Windows cmd / PowerShell completion: Deferred (POSIX shells Bash, Zsh, and Fish cover the primary user base; PowerShell can be added in a future plan if requested).
- External completion dependencies (e.g. shtab / click / typer): Out of scope to preserve zero-dependency design (D44/D46).

## Scope check

- Over-scope: none.
- Under-scope: none (covers generation, dynamic artifact lookup, ecosystem hooks, drop-in installation, wizard integration, and complete test suites across 3 atomic children).

## Required tests / validation

- Unit tests in `tests/test_completion.py` validating script generation for bash/zsh/fish, static subcommand trees, dynamic artifact completion, and argcomplete soft-import.
- Unit tests in `tests/test_install_wizard.py` validating drop-in file writing, symlink creation, uninstallation, and wizard prompt handling.
- Full test suite green (`pytest`).

## Spec / documentation sync

- `README.md` updated with Shell Tab Completion setup and usage instructions.

## Open questions

### OQ-01: Should drop-in directory auto-discovery be the primary installation strategy?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Yes. Standard auto-discovery directories (`~/.local/share/bash-completion/completions/` and `~/.config/fish/completions/`) allow the shell to load completions dynamically on demand without polluting or editing user dotfiles (`~/.bashrc` / `~/.zshrc`).

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: After children 01, 02, and 03 execute, paste: (a) test output from `pytest tests/test_completion.py tests/test_install_wizard.py -v` showing all tests passing; (b) output of `aw completion bash` showing valid completion functions for `aw`, `agentwf`, `agent-workflows`; (c) output of `aw completion install --dry-run` showing drop-in target paths; (d) full test suite runner output showing green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
