# IPD: Integrate tab completion into aw install wizard and cli setup with idempotent shell rc management

- Date: 2026-08-28
- Kind: child
- Concern: The core tab-completion generation engine and subcommand (`aw completion <shell>`) exist in child 01 (`bja8og`), but `aw install`, `aw setup`, and the interactive install wizard do not offer or automate shell completion configuration for users. Developers must manually look up shell-specific rc syntax and copy snippets by hand.
- Scope: Integrate tab-completion configuration into the installer workflows: (1) Add `aw completion install [--shell <shell>] [--target-rc <path>]` and `aw completion uninstall` to manage idempotent delimited blocks (`# agent-workflows completion:BEGIN ... # agent-workflows completion:END`) in `~/.bashrc`, `~/.zshrc`, or `~/.config/fish/completions/aw.fish`; (2) Add an optional completion prompt / step in the interactive install wizard (`agent_workflows/install_wizard.py`) detecting current shell via `$SHELL` and offering 1-click shell completion installation; (3) Add `--completion [auto|bash|zsh|fish|none]` flag to `aw install` / `aw setup` (defaulting to `none` in non-interactive/`--yes` mode); (4) Add post-install completion status and guidance in the `aw install` output summary when completion is not yet configured; (5) Add full unit tests in `tests/test_install_wizard.py` and `tests/test_completion.py`.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/install_wizard.py, agent_workflows/cli.py, tests/test_completion.py, tests/test_install_wizard.py, README.md
- Item-Dependencies: executed:bja8og
- Status: to-review
- Set: tabcomp
- Order: 2
- Highest E allocated: 06
- Author: Antigravity
- Id: 4f1j25

## Workflow history

- 2026-08-28 to-review (Antigravity): authored detailed implementation plan for install wizard and cli setup integration.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Seamlessly integrate tab-completion configuration into the `aw install` and `aw setup` workflows and the interactive installation wizard, allowing users to enable shell completions automatically and idempotently without manual copy-pasting.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Shell RC Manager and Automated Install/Uninstall (`agent_workflows/completion.py`)

- [ ] E-01 Implement `install_shell_completion(shell=None, target_rc=None, dry_run=False)` and `uninstall_shell_completion(shell=None, target_rc=None, dry_run=False)` in `agent_workflows/completion.py` with atomic, idempotent marker-delimited block management (`# agent-workflows completion:BEGIN` to `# agent-workflows completion:END`), auto-detecting user shell from `$SHELL` and selecting canonical RC files (`~/.bashrc`, `~/.zshrc`, `~/.config/fish/completions/aw.fish`).
  - Depends on: none
  - Expected outcome: Calling `install_shell_completion` cleanly writes or updates the delimited block without duplicating entries, and `uninstall_shell_completion` strips the block without modifying surrounding user config.
  - Execution state: pending

- [ ] E-02 Wire `aw completion install` and `aw completion uninstall` subcommands in `agent_workflows/cli.py` supporting `--shell`, `--rc-file`, and `--dry-run` options.
  - Depends on: E-01
  - Expected outcome: `aw completion install` detects shell and installs the hook with clear terminal feedback; `aw completion uninstall` removes it cleanly.
  - Execution state: pending

### Task group 2: Wizard and Installer Integration (`agent_workflows/install_wizard.py`, `agent_workflows/cli.py`)

- [ ] E-03 Add a shell completion configuration step to the interactive install wizard in `agent_workflows/install_wizard.py` that checks if completion is already active, prompts the user to enable tab-completion for their detected shell, and applies it upon confirmation.
  - Depends on: E-01
  - Expected outcome: Interactive wizard displays a clean prompt to install shell completion, previewing the target RC path before applying.
  - Execution state: pending

- [ ] E-04 Add `--completion [auto|bash|zsh|fish|none]` flag to `aw install` / `aw setup` in `agent_workflows/cli.py`, defaulting to `none` in non-interactive/`--yes` mode and executing shell completion configuration when specified.
  - Depends on: E-01, E-02
  - Expected outcome: Users can run `aw install --completion auto` or `aw install --completion bash` during setup to configure completion in one command.
  - Execution state: pending

- [ ] E-05 Add a completion status hint to the post-installation summary emitted by `aw install` and `aw setup`, alerting the user if tab-completion is not installed and showing the 1-line command to enable it.
  - Depends on: E-02, E-04
  - Expected outcome: Post-install summary includes `Tip: Enable tab-completion with 'aw completion install'`.
  - Execution state: pending

### Task group 3: Testing and documentation (`tests/test_install_wizard.py`, `tests/test_completion.py`, `README.md`)

- [ ] E-06 Add unit tests in `tests/test_completion.py` and `tests/test_install_wizard.py` validating RC block injection, idempotency, uninstallation, shell auto-detection from `$SHELL`, wizard interactive prompts, `--completion` CLI flag, and doc updates.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: All tests pass with full assertion coverage under `pytest`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Idempotency & Safety: Any automated modification to user configuration files (`~/.bashrc`, `~/.zshrc`) must be enclosed in distinct begin/end comment markers (`# agent-workflows completion:BEGIN` / `# agent-workflows completion:END`) so repeated runs never duplicate lines, and uninstall leaves no residue.
- Non-destructive Defaults: In automated batch or non-interactive installs (`-y` / `--yes`), modifications to user shell RC files must default to opt-in (`none`) unless explicitly requested via `--completion <shell>` or `--completion auto`.
- Shell Detection: Detect shell reliably by consulting `os.environ.get("SHELL")`, falling back safely to `bash`.

## Findings

- Fish uses file-based completion autoloading (`~/.config/fish/completions/aw.fish`), whereas Bash and Zsh typically use loader lines in `~/.bashrc` and `~/.zshrc`.
- Providing both a direct CLI command (`aw completion install`) and an optional wizard prompt gives both interactive and automated installation workflows full coverage.

## Proposed changes (ordered, validatable)

1. `agent_workflows/completion.py`: Implement `install_shell_completion` and `uninstall_shell_completion` with delimited block handling.
2. `agent_workflows/cli.py`: Add `aw completion install|uninstall` commands, `--completion` flag on `install`/`setup`, and post-install hint.
3. `agent_workflows/install_wizard.py`: Add shell completion step in interactive wizard.
4. `tests/test_completion.py` & `tests/test_install_wizard.py`: Unit tests for installation, idempotency, uninstallation, wizard, and CLI flags.
5. `README.md`: Update documentation with `aw completion install` usage.

## Deferred / out of scope (with reason)

- System-wide completion installation (e.g. writing to `/etc/bash_completion.d` requiring sudo): Deferred (user-level configuration `~/.bashrc` / `~/.zshrc` / `~/.config/fish` is standard, non-privileged, and portable).

## Scope check

- Over-scope: none.
- Under-scope: none (covers CLI installer commands, wizard prompts, CLI flags, post-install hints, and test coverage).

## Required tests / validation

- Test `install_shell_completion` writes delimited block to target RC file.
- Test `install_shell_completion` is idempotent (repeated calls update existing block without duplicating).
- Test `uninstall_shell_completion` cleanly removes delimited block and leaves surrounding user config untouched.
- Test `aw completion install --dry-run` previews changes without writing.
- Test wizard prompt handles accept, reject, and pre-existing installation states.
- Test `aw install --completion bash` activates shell completion during repo install.

## Spec / documentation sync

- Update `README.md` to reference `aw completion install`.

## Open questions

### OQ-01: How should Fish shell completion be handled compared to Bash/Zsh?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Fish natively loads completions from `~/.config/fish/completions/<name>.fish`. For Fish, `install_shell_completion` writes directly to `~/.config/fish/completions/aw.fish`, whereas for Bash and Zsh it writes the loader block into `~/.bashrc` and `~/.zshrc`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit tests demonstrate `install_shell_completion` and `uninstall_shell_completion` manage delimited blocks accurately and idempotently.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw completion install` and `aw completion uninstall` execute successfully via CLI invocations.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Install wizard renders completion prompt when running interactively and respects user acceptance/rejection.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `aw install --completion <shell>` configures shell completion alongside target repo installation.
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
