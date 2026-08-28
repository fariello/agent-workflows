# IPD: Integrate tab completion into aw install wizard and cli setup with drop-in directory auto-discovery

- Date: 2026-08-28
- Kind: child
- Concern: The core tab-completion generation engine and subcommand (`aw completion <shell>`) exist in child 01 (`bja8og`), but `aw install`, `aw setup`, and the interactive install wizard do not offer or automate shell completion configuration for users. Developers must manually look up shell-specific autoload directories or copy snippets by hand.
- Scope: Integrate drop-in shell completion into the installer workflows: (1) Add `aw completion install [--shell <shell>] [--dir <path>] [--rc]` and `aw completion uninstall` to manage drop-in completion scripts in standard XDG auto-discovery directories (`~/.local/share/bash-completion/completions/aw`, `~/.local/share/zsh/site-functions/_aw`, `~/.config/fish/completions/aw.fish`) with symlinks for `agentwf` and `agent-workflows`, leaving user RC files untouched by default; (2) Add an optional completion prompt / step in the interactive install wizard (`agent_workflows/install_wizard.py`) detecting current shell via `$SHELL` and offering 1-click drop-in completion file installation; (3) Add `--completion [auto|bash|zsh|fish|none]` flag to `aw install` / `aw setup` (defaulting to `none` in non-interactive/`--yes` mode); (4) Add post-install completion status and guidance in the `aw install` output summary when completion is not yet configured; (5) Add full unit tests in `tests/test_install_wizard.py` and `tests/test_completion.py`.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/install_wizard.py, agent_workflows/cli.py, tests/test_completion.py, tests/test_install_wizard.py, README.md
- Item-Dependencies: executed:bja8og
- Status: to-review
- Set: tabcomp
- Order: 2
- Highest E allocated: 06
- Author: Antigravity
- Id: 4f1j25

## Workflow history

- 2026-08-28 to-review (Antigravity): authored detailed implementation plan for install wizard and cli setup integration using drop-in directory auto-discovery.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Seamlessly integrate tab-completion configuration into the `aw install` and `aw setup` workflows and the interactive installation wizard, writing self-contained completion scripts directly to standard shell auto-discovery directories without polluting or modifying user configuration files.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Drop-In Directory Auto-Discovery Manager (`agent_workflows/completion.py`)

- [ ] E-01 Implement `install_shell_completion(shell=None, target_dir=None, use_rc=False, dry_run=False)` and `uninstall_shell_completion(shell=None, target_dir=None, use_rc=False, dry_run=False)` in `agent_workflows/completion.py`. By default, install writes self-contained completion scripts into standard user auto-discovery directories (`~/.local/share/bash-completion/completions/aw`, `~/.local/share/zsh/site-functions/_aw`, `~/.config/fish/completions/aw.fish`) and creates symlinks for `agentwf` and `agent-workflows`, leaving user RC files untouched.
  - Depends on: none
  - Expected outcome: `install_shell_completion` creates the parent directory if needed and writes the script and alias symlinks cleanly; `uninstall_shell_completion` removes the files and symlinks.
  - Execution state: pending

- [ ] E-02 Wire `aw completion install` and `aw completion uninstall` subcommands in `agent_workflows/cli.py` supporting `--shell`, `--dir`, `--rc`, and `--dry-run` options.
  - Depends on: E-01
  - Expected outcome: `aw completion install` detects shell via `$SHELL`, writes drop-in completion files to the user auto-discovery path with clear feedback, and supports uninstall.
  - Execution state: pending

### Task group 2: Wizard and Installer Integration (`agent_workflows/install_wizard.py`, `agent_workflows/cli.py`)

- [ ] E-03 Add a shell completion configuration step to the interactive install wizard in `agent_workflows/install_wizard.py` that checks if completion files exist in the user autoload path, prompts the user to install drop-in tab-completion for their detected shell, and applies it upon confirmation without touching user config files.
  - Depends on: E-01
  - Expected outcome: Interactive wizard displays a clean prompt to install drop-in shell completion, previewing the target directory before writing.
  - Execution state: pending

- [ ] E-04 Add `--completion [auto|bash|zsh|fish|none]` flag to `aw install` / `aw setup` in `agent_workflows/cli.py`, defaulting to `none` in non-interactive/`--yes` mode and installing drop-in completion files when specified.
  - Depends on: E-01, E-02
  - Expected outcome: Users can run `aw install --completion auto` or `aw install --completion bash` during setup to configure drop-in completion in one command.
  - Execution state: pending

- [ ] E-05 Add a completion status hint to the post-installation summary emitted by `aw install` and `aw setup`, alerting the user if drop-in tab-completion is not installed and showing the 1-line command to enable it (`aw completion install`).
  - Depends on: E-02, E-04
  - Expected outcome: Post-install summary includes `Tip: Enable tab-completion with 'aw completion install'`.
  - Execution state: pending

### Task group 3: Testing and documentation (`tests/test_install_wizard.py`, `tests/test_completion.py`, `README.md`)

- [ ] E-06 Add unit tests in `tests/test_completion.py` and `tests/test_install_wizard.py` validating drop-in file writing, symlink creation, uninstallation, shell auto-detection from `$SHELL`, wizard interactive prompts, `--completion` CLI flag, and doc updates.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: All tests pass with full assertion coverage under `pytest`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Zero Configuration File Pollution: Writing to standard auto-discovery directories (`~/.local/share/bash-completion/completions/` and `~/.config/fish/completions/`) avoids touching `~/.bashrc` or `~/.zshrc`, preventing merge conflicts, duplicate entries, or unwanted edits to user dotfiles.
- Non-destructive Defaults: In automated batch or non-interactive installs (`-y` / `--yes`), modifications to user completion directories default to opt-in (`none`) unless explicitly requested via `--completion <shell>` or `--completion auto`.
- Shell Detection: Detect shell reliably by consulting `os.environ.get("SHELL")`, falling back safely to `bash`.

## Findings

- Modern Bash, Zsh, and Fish all have designated user-level autoload directories that require no root privileges and no `.bashrc` modification.
- Drop-in files paired with alias symlinks for `agentwf` and `agent-workflows` deliver an instant zero-maintenance user experience.

## Proposed changes (ordered, validatable)

1. `agent_workflows/completion.py`: Implement `install_shell_completion` and `uninstall_shell_completion` targeting standard XDG auto-discovery paths.
2. `agent_workflows/cli.py`: Add `aw completion install|uninstall` commands, `--completion` flag on `install`/`setup`, and post-install hint.
3. `agent_workflows/install_wizard.py`: Add drop-in shell completion step in interactive wizard.
4. `tests/test_completion.py` & `tests/test_install_wizard.py`: Unit tests for file writing, symlinks, uninstallation, wizard, and CLI flags.
5. `README.md`: Update documentation with `aw completion install` usage.

## Deferred / out of scope (with reason)

- System-wide completion installation (e.g. writing to `/etc/bash_completion.d` requiring sudo): Deferred (user-level configuration `~/.local/share/bash-completion/completions/` is standard, non-privileged, and portable).

## Scope check

- Over-scope: none.
- Under-scope: none (covers CLI installer commands, drop-in directories, wizard prompts, CLI flags, post-install hints, and test coverage).

## Required tests / validation

- Test `install_shell_completion` writes drop-in completion file and alias symlinks to standard directories.
- Test `uninstall_shell_completion` cleanly removes drop-in completion file and alias symlinks.
- Test `aw completion install --dry-run` previews file writes without creating files.
- Test wizard prompt handles accept, reject, and pre-existing installation states.
- Test `aw install --completion bash` activates drop-in completion during repo install.

## Spec / documentation sync

- Update `README.md` to reference `aw completion install`.

## Open questions

### OQ-01: How are entrypoint aliases handled in auto-discovery directories?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: In `~/.local/share/bash-completion/completions/`, the primary file `aw` is written, and relative symlinks `agentwf -> aw` and `agent-workflows -> aw` are created so the shell activates the completion function regardless of which binary name is typed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests demonstrate `install_shell_completion` and `uninstall_shell_completion` write and remove drop-in completion files and symlinks accurately.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw completion install` and `aw completion uninstall` execute successfully via CLI invocations.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Install wizard renders drop-in completion prompt when running interactively and respects user acceptance/rejection.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `aw install --completion <shell>` configures drop-in shell completion alongside target repo installation.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Post-install summary includes completion installation tip when completion is not yet configured.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `pytest tests/test_completion.py tests/test_install_wizard.py` runs with all tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
