# IPD: Drop-in auto-discovery installation, wizard integration, and cli setup for tab completion

- Date: 2026-08-28
- Kind: child
- Concern: Having a completion generator (child 01) and dynamic query resolver (child 02) still requires manual setup unless the framework provides clean, zero-maintenance installation into standard shell autoload directories during `aw install`, `aw setup`, or interactive wizard runs.
- Scope: Implement drop-in auto-discovery installation, interactive wizard prompts, CLI flags, and documentation: (1) Add `install_shell_completion` and `uninstall_shell_completion` in `agent_workflows/completion.py` targeting standard XDG auto-discovery directories (`~/.local/share/bash-completion/completions/aw`, `~/.local/share/zsh/site-functions/_aw`, `~/.config/fish/completions/aw.fish`) with alias symlinks; (2) Wire `aw completion install` and `aw completion uninstall` in `agent_workflows/cli.py`; (3) Add an interactive prompt step to `agent_workflows/install_wizard.py`; (4) Add `--completion [auto|bash|zsh|fish|none]` flag to `aw install` / `aw setup` in `agent_workflows/cli.py` and post-install discovery tips; (5) Add unit tests in `tests/test_completion.py` and `tests/test_install_wizard.py`; (6) Update `README.md`.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/install_wizard.py, agent_workflows/cli.py, tests/test_completion.py, tests/test_install_wizard.py, README.md
- Item-Dependencies: executed:4f1j25
- Status: to-review
- Set: tabcomp
- Order: 3
- Highest E allocated: 05
- Author: Antigravity
- Id: jolfpj

## Workflow history

- 2026-08-28 to-review (Antigravity): authored detailed atomic implementation plan for drop-in installation, wizard integration, and documentation.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Provide seamless 1-command and 1-click drop-in shell completion installation for Bash, Zsh, and Fish that writes directly to standard user auto-discovery directories with alias symlinks, integrates smoothly into the `aw install` wizard, and leaves user configuration dotfiles completely untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Drop-In Directory Auto-Discovery Manager (`agent_workflows/completion.py`)

- [ ] E-01 Implement `resolve_completion_dir(shell, custom_dir)` and `install_shell_completion(shell, target_dir, dry_run)` / `uninstall_shell_completion(shell, target_dir, dry_run)` in `agent_workflows/completion.py` targeting standard user auto-discovery paths (`~/.local/share/bash-completion/completions/aw`, `~/.local/share/zsh/site-functions/_aw`, `~/.config/fish/completions/aw.fish`) and creating alias symlinks for `agentwf` and `agent-workflows`.
  - Depends on: none
  - Expected outcome: `install_shell_completion` creates parent directories, writes the completion script, and links aliases cleanly; `uninstall_shell_completion` cleanly removes the files and symlinks.
  - Execution state: pending

### Task group 2: CLI Commands, Installer Flags, and Wizard Prompt (`agent_workflows/cli.py`, `agent_workflows/install_wizard.py`)

- [ ] E-02 Register `aw completion install` and `aw completion uninstall` subcommands in `agent_workflows/cli.py` accepting `--shell`, `--dir`, and `--dry-run` arguments with descriptive status feedback.
  - Depends on: E-01
  - Expected outcome: `aw completion install` detects active shell via `$SHELL`, writes completion files to the user autoload directory, and reports installed paths.
  - Execution state: pending

- [ ] E-03 Add a shell completion installation prompt step in `agent_workflows/install_wizard.py` that checks if completion is installed, prompts interactive users to install drop-in tab-completion for their detected shell, and writes the files upon confirmation.
  - Depends on: E-01, E-02
  - Expected outcome: The interactive wizard offers a clean 1-click prompt to enable shell completion without modifying any configuration dotfiles.
  - Execution state: pending

- [ ] E-04 Add `--completion [auto|bash|zsh|fish|none]` flag to `aw install` and `aw setup` in `agent_workflows/cli.py` (defaulting to safe `none` in non-interactive/`--yes` mode) and append a completion discovery tip to the post-installation summary if completion is not configured.
  - Depends on: E-01, E-02
  - Expected outcome: Running `aw install --completion auto` configures shell completion alongside target repo installation; post-install summary shows `Tip: Enable tab-completion with 'aw completion install'` when unconfigured.
  - Execution state: pending

### Task group 3: Testing and Documentation (`tests/test_completion.py`, `tests/test_install_wizard.py`, `README.md`)

- [ ] E-05 Implement unit tests in `tests/test_completion.py` and `tests/test_install_wizard.py` covering directory resolution, drop-in file creation, symlink creation, uninstallation, wizard prompt acceptance/rejection, `--completion` installer flag, and update `README.md` with usage instructions.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: All installer and wizard completion tests pass under `pytest` with 100% assertions satisfied, and `README.md` documents `aw completion install`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Zero Configuration File Pollution: Never modify `~/.bashrc` or `~/.zshrc` automatically; rely on standard XDG auto-discovery directories (`~/.local/share/bash-completion/completions/` for Bash, `~/.config/fish/completions/` for Fish).
- Non-destructive Defaults: In automated batch or non-interactive installs (`-y` / `--yes`), modifications to user completion directories default to opt-in (`none`) unless explicitly requested via `--completion <shell>` or `--completion auto`.
- Shell Detection: Detect shell reliably by consulting `os.environ.get("SHELL")`, falling back safely to `bash`.

## Findings

- Modern Linux and macOS shells auto-discover completion files in `~/.local/share/bash-completion/completions/` without requiring any shell restarts or rc file edits.
- Creating symlinks `agentwf -> aw` and `agent-workflows -> aw` ensures that completions trigger regardless of which CLI alias the developer executes.

## Proposed changes (ordered, validatable)

1. `agent_workflows/completion.py`: Implement `resolve_completion_dir`, `install_shell_completion`, and `uninstall_shell_completion`.
2. `agent_workflows/cli.py`: Register `aw completion install|uninstall`, add `--completion` flag on `install`/`setup`, and post-install hint.
3. `agent_workflows/install_wizard.py`: Add shell completion step in interactive wizard.
4. `tests/test_completion.py` & `tests/test_install_wizard.py`: Unit tests for drop-in files, symlinks, uninstallation, wizard prompt, and CLI flags.
5. `README.md`: Update documentation with `aw completion install` and manual activation examples.

## Deferred / out of scope (with reason)

- System-wide completion installation (e.g. writing to `/etc/bash_completion.d` requiring root/sudo): Deferred (user-level auto-discovery in `~/.local/share/bash-completion/completions/` is standard, portable, and non-privileged).

## Scope check

- Over-scope: none.
- Under-scope: none (covers drop-in installation, symlink management, wizard prompt, installer flag, post-install tips, unit tests, and documentation).

## Required tests / validation

- `tests/test_completion.py` & `tests/test_install_wizard.py`:
  - Test `resolve_completion_dir` returns correct user paths for bash, zsh, and fish.
  - Test `install_shell_completion` writes script file and creates alias symlinks in a mock directory.
  - Test `install_shell_completion` is idempotent when run repeatedly.
  - Test `uninstall_shell_completion` removes script and symlinks cleanly.
  - Test `aw completion install --dry-run` previews paths without creating files.
  - Test wizard prompt respects user confirmation and rejection.
  - Test `aw install --completion bash` installs completion files during repo installation.

## Spec / documentation sync

- `README.md`: Add "Shell Tab Completion" section with `aw completion install` and `source <(aw completion bash)` instructions.

## Open questions

### OQ-01: How should missing parent directories be handled during installation?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: `install_shell_completion` invokes `target_dir.mkdir(parents=True, exist_ok=True)` so missing user auto-discovery directories are created automatically with user-only permissions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests proving `install_shell_completion` and `uninstall_shell_completion` create and remove drop-in completion files and alias symlinks.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: CLI test executing `aw completion install` and `aw completion uninstall` with exit code 0.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Wizard test demonstrating completion prompt renders in interactive mode and respects user response.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: CLI test executing `aw install --completion <shell>` proving completion files are installed alongside framework files.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `pytest tests/test_completion.py tests/test_install_wizard.py` runs with all tests passing, and `README.md` contains tab-completion documentation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
