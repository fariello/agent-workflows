# IPD: Drop-in auto-discovery installation, wizard integration, and cli setup for tab completion

- Date: 2026-08-28
- Kind: child
- Concern: Having a completion generator (child 01) and dynamic query resolver (child 02) still requires manual setup unless the framework provides clean, zero-maintenance installation into standard shell autoload directories during `aw install`, `aw setup`, or interactive wizard runs.
- Scope: Implement drop-in auto-discovery installation, an interactive setup prompt, CLI flags, and documentation: (1) Add `resolve_completion_dir`, `install_shell_completion`, and `uninstall_shell_completion` in `agent_workflows/completion.py` targeting XDG auto-discovery directories with shell-specific alias binding and no-clobber/sentinel safety; (2) Wire `aw completion install` and `aw completion uninstall` in `agent_workflows/cli.py`, extending child 01's `completion` parser shape additively; (3) Add an interactive completion prompt to the host-level `_run_setup` flow in `agent_workflows/cli.py` (NOT the per-repo `install_wizard.py`); (4) Add `--completion [auto|bash|zsh|fish|none]` flag to `aw install` / `aw setup` in `agent_workflows/cli.py` (default `none` non-interactively) and post-install discovery tips; (5) Add unit tests in `tests/test_completion.py` (and `tests/test_cli_*`/setup coverage as needed); (6) Update `README.md`.
- Scope-Paths: agent_workflows/completion.py, agent_workflows/cli.py, tests/test_completion.py, README.md
- Item-Dependencies: executed:4f1j25
- Status: executed
- Set: tabcomp
- Order: 3
- Highest E allocated: 05
- Author: Antigravity
- Id: jolfpj

## Workflow history
- 2026-08-29 executed (opencode its_direct/pt3-claude-opus-5-1m-us): Finalize tabcomp-03 (jolfpj): drop-in auto-discovery completion install, host-level setup prompt, and --completion flag; implemented+verified this run (impl commit de51d91; 78 passed, 2 skipped; full suite 2722 passed, 3 skipped) [Scope reconciliation - in-scope-unmodified README.md: implemented in commit de51d91 (E-05 docs) before the re-begin froze base de51d91; in-scope-unmodified agent_workflows/cli.py: implemented in commit de51d91 (E-02/E-03/E-04) before the re-begin froze base de51d91; in-scope-unmodified agent_workflows/completion.py: implemented in commit de51d91 (E-01) before the re-begin froze base de51d91; in-scope-unmodified tests/test_completion.py: implemented in commit de51d91 (E-05) before the re-begin froze base de51d91]
- 2026-08-28 approved (aw set): status set to approved

- 2026-08-28 reviewed (OpenCode/its_direct/pt3-claude-opus-4.8): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Moved the completion prompt out of the per-repo `install_wizard.py` into the host-level `_run_setup` (verified module roles); made E-02 depend explicitly on child 01's extensible `completion` parser shape; corrected the blanket-symlink assumption to shell-specific alias binding (bash command-name files, single zsh `_aw`, fish multi-`complete -c`); added no-clobber/sentinel + symlink-safe + uninstall-only-ours semantics; added XDG env-var precedence consistent with `config._config_dir`; and added the dotfile-untouched and no-clobber test assertions. Dropped `install_wizard.py`/`test_install_wizard.py` from Scope-Paths.
- 2026-08-28 to-review (Antigravity): authored detailed atomic implementation plan for drop-in installation, wizard integration, and documentation.
- 2026-08-28 draft (Antigravity): scaffolded skeleton.

## Goal

Provide seamless 1-command and 1-click drop-in shell completion installation for Bash, Zsh, and Fish that writes directly to standard user auto-discovery directories with alias symlinks, integrates smoothly into the `aw install` wizard, and leaves user configuration dotfiles completely untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Drop-In Directory Auto-Discovery Manager (`agent_workflows/completion.py`)

- [x] E-01 Implement `resolve_completion_dir(shell, custom_dir)` and `install_shell_completion(shell, target_dir, dry_run)` / `uninstall_shell_completion(shell, target_dir, dry_run)` in `agent_workflows/completion.py` targeting standard user auto-discovery paths, honoring `XDG_DATA_HOME`/`XDG_CONFIG_HOME` before falling back to `~/.local/share`/`~/.config` (matching `agent_workflows/config._config_dir`, verified at `config.py:58-64`): bash `${XDG_DATA_HOME:-~/.local/share}/bash-completion/completions/aw`, zsh `${XDG_DATA_HOME:-~/.local/share}/zsh/site-functions/_aw`, fish `${XDG_CONFIG_HOME:-~/.config}/fish/completions/aw.fish`. ALIAS BINDING IS SHELL-SPECIFIC (verified correctness constraint), do NOT blanket-symlink all three: for BASH create command-name files/symlinks (`agentwf`, `agent-workflows` -> the `aw` file) since bash-completion loads by command name; for ZSH a SINGLE `_aw` file whose `#compdef aw agentwf agent-workflows` line already binds all three aliases (do not create `_agentwf`/`_agent-workflows` symlinks unless the generated script requires them); for FISH write `aw.fish` containing `complete -c aw`/`-c agentwf`/`-c agent-workflows` (the generator from child 01 already binds all three via `complete -c`), so no per-alias fish files are needed. SAFETY: writes MUST be idempotent and no-clobber-unless-ours (detect a pre-existing foreign `aw` completion and refuse/replace only a file this tool wrote, e.g. via a sentinel marker line); never write or delete THROUGH a symlink to an unexpected target; `uninstall_shell_completion` MUST remove only files/symlinks this tool created (identified by the sentinel), never a user's or another tool's file. NEVER edit `~/.bashrc`/`~/.zshrc`/`config.fish` (the core promise).
  - Depends on: none
  - Expected outcome: `install_shell_completion` creates parent directories, writes the completion script with a self-identifying sentinel, and binds aliases per the shell-specific rules above; re-running is idempotent; `uninstall_shell_completion` removes only the files/symlinks this tool created; no user rc/dotfile is ever modified.
  - Done note: Implemented `resolve_completion_dir`, `install_shell_completion`, `uninstall_shell_completion`, plus the supporting `INSTALL_SENTINEL`, `SUPPORTED_SHELLS`, `_DROPIN_LAYOUT`, `CompletionInstallError`, `completion_filename`, `_alias_filenames`, `_script_with_sentinel`, `_is_ours`, `_foreign`, and `is_completion_installed` in `agent_workflows/completion.py`. XDG precedence reuses the SAME convention as `config.config_dir` (`XDG_DATA_HOME` for bash/zsh, `XDG_CONFIG_HOME` for fish, then `~/.local/share`/`~/.config`) - asserted directly against `config.config_dir()` in a test rather than merely restated. ALIAS BINDING is shell-specific exactly as specified: bash gets `agentwf`/`agent-workflows` command-name symlinks -> `aw` (verified `os.readlink` == `aw`); zsh gets ONE `_aw` and the test asserts the zsh dir contains ONLY `_aw` (no `_agentwf`); fish gets one `aw.fish` and the test asserts all three `complete -c <name>` lines are present inside it. SAFETY: every written file carries `INSTALL_SENTINEL`; install fails CLOSED before writing anything if a foreign file occupies the primary OR any alias path; a symlink whose target is outside/unexpected is treated as foreign so we never write THROUGH it; uninstall is sentinel-gated and reports foreign files under `skipped` instead of deleting them. `mkdir(parents=True, exist_ok=True)` resolves OQ-01. NO rc/dotfile is read or written anywhere in the module. See run DECISION 01-jolfpj-D1 for the one non-obvious detail: for zsh the sentinel goes on line 2 because `compinit` only honors `#compdef` as line 1, so a literal "prepend" would have broken the alias binding E-01 also requires.
  - Execution state: performed

### Task group 2: CLI Commands, Installer Flags, and Setup Prompt (`agent_workflows/cli.py`)

- [x] E-02 Register `aw completion install` and `aw completion uninstall` subcommands in `agent_workflows/cli.py` accepting `--shell`, `--dir`, and `--dry-run` arguments with descriptive status feedback, and wire their dispatch alongside the existing `args.command`/`completion` branches. CROSS-PLAN CONTRACT (verified prerequisite): child 01 (`tabcomp-01` E-03, now reviewed) was required to shape the `completion` parser so `install`/`uninstall` sub-actions can be added additively WITHOUT reshaping it. This E-item MUST extend that existing shape (add `install`/`uninstall` as sub-actions of `completion` next to the shell-name output behavior); it MUST NOT redesign `aw completion` or break `aw completion <shell>` output. If child 01's shipped shape does not admit these sub-actions, that is a child-01 defect to fix there, not a redesign here - verify the shape first.
  - Depends on: E-01
  - Expected outcome: `aw completion install` detects active shell via `$SHELL` (bash fallback, consistent with child 01), writes completion files to the user autoload directory, and reports installed paths; `aw completion <shell>` output (child 01) still works unchanged.
  - Done note: VERIFIED child 01's parser shape FIRST (as the cross-plan contract requires) rather than assuming it: `cli.py` documents `target` as a deliberately free-form `nargs="?"` positional with NO `choices`, precisely so these verbs can be added additively, and `tests/test_completion.py::CompletionCliTests::test_parser_shape_allows_child03_extension` already pinned it. EXTENDED that shape without redesign: added `--shell` (choices from `completion.SUPPORTED_SHELLS`, the single source of truth), `--dir`, and `--dry-run` to the existing `p_completion` parser, and routed `target in ("install","uninstall")` from `_run_completion` into a new `_run_completion_install(args, verb=..., term=...)`. `aw completion <shell>` and bare `aw completion` are untouched (still stream the raw script to stdout for `source <(aw completion bash)`). Shell defaults to child 01's `_detect_shell()` ($SHELL basename, bash fallback) so both surfaces agree. Exit codes: 0 ok, 1 refusal (foreign file / OSError) - a refusal is reported, never a silent overwrite. Threads the dispatcher's existing `Term` instead of constructing a second one. Live verified with a temp XDG: dry-run listed the 3 bash paths and created nothing; the real install wrote `aw` + the two alias symlinks; `aw completion bash` still ended with `complete -F _aw_completion aw agentwf agent-workflows`; uninstall removed all three.
  - Execution state: performed

- [x] E-03 Add a shell-completion installation prompt to the HOST-LEVEL, once-per-user setup flow (`_run_setup` in `agent_workflows/cli.py`, verified at `cli.py:4771`), NOT to `agent_workflows/install_wizard.py`. RATIONALE (verified): `install_wizard.py` is the PER-TARGET-REPO project-policy wizard (private/public presets, physical `.aw/` placement; module docstring `install_wizard.py:1-18`); shell completion is a per-user/per-machine concern, so prompting inside the repo-policy wizard would fire on every repo install and be intrusive/repetitive. `_run_setup` is the host-level, once-per-user configuration (search roots, XDG config) and is the correct home. The prompt checks whether completion is already installed for the detected shell, offers a single confirm to install drop-in completion, and on acceptance calls `install_shell_completion` (E-01); it only fires interactively (TTY) and is skipped non-interactively.
  - Depends on: E-01, E-02
  - Expected outcome: The interactive `aw setup` flow offers a clean one-confirm prompt to enable shell completion, calls `install_shell_completion` on acceptance, modifies no rc/dotfile, and is skipped in non-interactive runs; `install_wizard.py` (repo-policy) is untouched by this feature.
  - Done note: Added `_configure_completion(args, term)` to `agent_workflows/cli.py` and called it from the HOST-LEVEL `_run_setup` (after the per-repo installs, before `_orient`). `agent_workflows/install_wizard.py` is NOT modified - a test asserts the wizard source contains none of `install_shell_completion`/`resolve_completion_dir`/`completion install`, so the reviewed integration point is machine-enforced, not just documented. The prompt fires ONLY on an interactive TTY without `--yes`, states the exact target directory, and explicitly promises it will not modify `~/.bashrc`/`~/.zshrc`/`config.fish`; a single `[y/N]` confirm installs on `y`/`yes` and otherwise prints how to enable it later. It is a no-op when completion is already ours (no pointless re-prompt), when `--completion none` is passed, and when non-interactive or `--yes` (safe default: write nothing). An install failure is caught and downgraded to a `warn` so an optional convenience can never fail the host setup flow. Per run DECISION 01-jolfpj-D2 it runs once per invocation, not once per repo, which is the whole reason the prompt lives here rather than in the per-repo wizard.
  - Execution state: performed

- [x] E-04 Add `--completion [auto|bash|zsh|fish|none]` flag to `aw install` and `aw setup` in `agent_workflows/cli.py` (defaulting to safe `none` in non-interactive/`--yes` mode) and append a completion discovery tip to the post-installation summary if completion is not configured.
  - Depends on: E-01, E-02
  - Expected outcome: Running `aw install --completion auto` configures shell completion alongside target repo installation; post-install summary shows `Tip: Enable tab-completion with 'aw completion install'` when unconfigured.
  - Done note: Registered `--completion {auto,bash,zsh,fish,none}` (default `None`) on BOTH `p_install` and `p_setup` in `_build_parser`, with `_resolve_completion_choice` mapping `auto` -> `_detect_shell()` and `none`/absent -> "do nothing". Added `_completion_configured()` + `_completion_tip(term)` which appends `Tip: Enable tab-completion with 'aw completion install'` to the post-install summary ONLY when completion is not already installed (the tip self-suppresses once installed). Wired `_configure_completion` + `_completion_tip` into `_run_install`, `_install_all`, and `_run_setup` - once per invocation, not per repo (run DECISION 01-jolfpj-D2). NON-DESTRUCTIVE DEFAULT confirmed live: `install <tmp repo> --yes` (no `--completion`) created NO completion directory at all and printed the tip once; `install <tmp repo> --yes --completion bash` wrote `aw` + both alias symlinks and reported the directory with "(no rc/dotfile modified)".
  - Execution state: performed

### Task group 3: Testing and Documentation (`tests/test_completion.py`, `README.md`)

- [x] E-05 Implement unit tests in `tests/test_completion.py` (using a real `tmp_path`-style temp HOME/XDG, not a mock, so symlink and `mkdir(parents=True)` behavior is exercised) covering: `resolve_completion_dir` honoring `XDG_DATA_HOME`/`XDG_CONFIG_HOME` and the `~/.local/share`/`~/.config` fallbacks for bash/zsh/fish; drop-in file creation with the self-identifying sentinel; the shell-specific alias binding (bash command-name files/symlinks; a single zsh `_aw`; fish `aw.fish` with multi-`complete -c`); idempotent re-install; no-clobber refusal when a FOREIGN `aw` completion pre-exists; `uninstall_shell_completion` removing ONLY tool-created files; an explicit assertion that NO user rc/dotfile (`.bashrc`/`.zshrc`/`config.fish`) is created or modified; the `aw completion install`/`uninstall`/`--dry-run` CLI; the host-level setup prompt (E-03) honoring accept/reject and being skipped non-interactively; and the `aw install/setup --completion <shell>` flag. Update `README.md` with a "Shell Tab Completion" section. Keep any subprocess-spawning CLI test marked `slow` per `pyproject.toml:108-109`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: All installer and setup-prompt completion tests pass under `pytest` with 100% assertions satisfied, including the dotfile-untouched and no-clobber assertions, and `README.md` documents `aw completion install`.
  - Done note: Added the tabcomp-03 test classes to `tests/test_completion.py` on a `_DropInFixture` that builds a REAL temp HOME + real `XDG_DATA_HOME`/`XDG_CONFIG_HOME` (not a mock), so `mkdir(parents=True)` and actual symlink creation are exercised, and provides `assert_no_dotfile_touched()` checking `.bashrc`/`.bash_profile`/`.zshrc`/`.profile`/`fish/config.fish`: `ResolveCompletionDirTests` (XDG env vars win; `~/.local/share` + `~/.config` fallbacks; `--dir` override; unsupported shell raises; precedence asserted EQUAL to `config.config_dir()`), `InstallShellCompletionTests` (bash command-name symlinks per alias; zsh dir contains ONLY `_aw` with `#compdef` line 1; fish single file with all three `complete -c`; sentinel in every file; zsh sentinel does not displace `#compdef`; parent dirs created; idempotent; refuses a foreign primary AND a foreign alias without writing anything; dry-run writes nothing; a symlink to an unexpected target is foreign and is not written through), `UninstallShellCompletionTests` (removes only ours, leaves a foreign neighbor and a foreign `aw` intact and reports it, no-op when absent, dry-run removes nothing, roundtrip touches no dotfile), `CompletionInstallCliTests` (install/uninstall exit 0, `--dry-run` previews only, `--dir`, `$SHELL` default, foreign refusal exits 1, and the child-01 REGRESSION GUARD that `aw completion bash|zsh|fish` and bare `aw completion` still emit scripts), `SetupCompletionPromptTests` (accept installs, reject installs nothing, skipped non-interactively, skipped under `--yes`, no prompt when already installed, `none` never prompts, install failure does not break setup, and the assertion that `install_wizard.py` carries none of this), `InstallCompletionFlagTests` (flag on both verbs, all five choices, `auto`/`none` resolution, explicit shell does not prompt, `--yes` without the flag installs nothing, tip shown then hidden), `CompletionInstallSubprocessTests` (real subprocess install+uninstall, marked `@pytest.mark.slow` per `pyproject.toml:108-109`), and `ReadmeCompletionDocsTests`. Added the README "Shell Tab Completion" section (per-shell drop-in path table, `aw completion install`/`uninstall`, `--dry-run`, the never-edits-your-dotfiles promise, `aw install . --completion auto`, and `source <(aw completion bash)`). Result: `78 passed, 2 skipped`; full default suite `2722 passed, 3 skipped`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Zero Configuration File Pollution: Never modify `~/.bashrc`/`~/.zshrc`/`config.fish` automatically; rely on standard XDG auto-discovery directories. Honor `XDG_DATA_HOME`/`XDG_CONFIG_HOME` before the `~/.local/share`/`~/.config` fallbacks, consistent with `config._config_dir` (`config.py:58-64`). Writing under XDG subdirs is sanctioned by the project's existing config convention (R-5/D46 forbid writing directly under bare `~/` and forbid sensitive data in config, not XDG-subdir writes); completion scripts contain no sensitive data.
- Non-destructive Defaults: In automated batch or non-interactive installs (`-y`/`--yes`), modifications to user completion directories default to opt-in (`none`) unless explicitly requested via `--completion <shell>`/`--completion auto`. Installs are idempotent and no-clobber-unless-ours (sentinel-identified); uninstall removes only tool-created files.
- Shell Detection: Detect shell reliably by consulting `os.environ.get("SHELL")`, falling back safely to `bash` (consistent with child 01's `aw completion` default).
- Correct integration point: the interactive completion prompt belongs in the HOST-LEVEL once-per-user `_run_setup` (`cli.py:4771`), NOT the per-target-repo `install_wizard.py` (project-policy placement wizard, `install_wizard.py:1-18`).

## Findings

- Modern Linux and macOS shells auto-discover completion files in `${XDG_DATA_HOME:-~/.local/share}/bash-completion/completions/` (and the fish/zsh equivalents) without requiring any shell restarts or rc file edits.
- Alias binding is SHELL-SPECIFIC (verified correctness caveat), not a uniform symlink: bash loads by command-name file (so `agentwf`/`agent-workflows` command-name files/symlinks make sense); zsh binds all aliases via the ONE `_aw` file's `#compdef aw agentwf agent-workflows` line (extra `_agentwf` symlinks are usually wrong/unneeded); fish binds via `complete -c aw`/`-c agentwf`/`-c agent-workflows` inside one `aw.fish`. E-01 encodes these per-shell rules.
- CROSS-PLAN: `aw completion install`/`uninstall` (E-02) rely on the extensible `completion` parser shape that child 01 (`tabcomp-01` E-03) was required to ship; E-02 extends it additively and must verify it rather than assume it.
- SAFETY: writing to a shared user directory risks clobbering a foreign `aw` completion or following a symlink to an unexpected target; E-01 uses a self-identifying sentinel + no-clobber-unless-ours + symlink-safe writes, and uninstall removes only tool-created files. The dotfile-untouched promise is asserted by an explicit test (E-05).

## Proposed changes (ordered, validatable)

1. `agent_workflows/completion.py`: Implement `resolve_completion_dir`, `install_shell_completion`, and `uninstall_shell_completion` with sentinel/no-clobber/symlink safety and shell-specific alias binding.
2. `agent_workflows/cli.py`: Register `aw completion install|uninstall` (extending child 01's `completion` parser), add `--completion` flag on `install`/`setup`, add the host-level `_run_setup` completion prompt, and post-install hint.
3. `tests/test_completion.py`: Unit tests for dir resolution (XDG), drop-in files, per-shell alias binding, idempotency, no-clobber, uninstall-only-ours, dotfile-untouched, the setup prompt, and CLI flags.
4. `README.md`: Update documentation with `aw completion install` and manual activation examples.

## Deferred / out of scope (with reason)

- System-wide completion installation (e.g. writing to `/etc/bash_completion.d` requiring root/sudo): Deferred (user-level auto-discovery in `${XDG_DATA_HOME:-~/.local/share}/bash-completion/completions/` is standard, portable, and non-privileged).
- Wiring the completion prompt into `agent_workflows/install_wizard.py`: Removed from scope (plan-review). That module is the per-target-repo project-policy wizard; a per-user/per-machine completion prompt belongs in the host-level `_run_setup` (E-03), not fired on every repo install.

## Scope check

- Over-scope (removed in this review): the original plan touched `agent_workflows/install_wizard.py` (the per-repo project-policy wizard) for the completion prompt; that integration point was wrong, so the prompt moved to the host-level `_run_setup`, and `install_wizard.py` + `tests/test_install_wizard.py` were dropped from Scope-Paths.
- Under-scope (addressed in this review): the original E-items omitted no-clobber/sentinel safety, symlink-safety, the dotfile-untouched assertion, the shell-specific alias-binding correctness, XDG env-var precedence, and the explicit cross-plan dependency on child 01's extensible `completion` parser. All now specified.
- Right-sizing (reviewer): E-05 bundles tests + README across two concerns but maps to one test-surface file plus a doc update (one V-item, V-05), consistent with the sibling children's convention; not split. E-01 carries the most weight (dir resolution + install + uninstall + safety) but is one cohesive filesystem-manager concern.

## Required tests / validation

- `tests/test_completion.py` (real temp HOME/XDG via `tmp_path`, not a mock):
  - Test `resolve_completion_dir` honors `XDG_DATA_HOME`/`XDG_CONFIG_HOME` and the `~/.local/share`/`~/.config` fallbacks for bash, zsh, and fish.
  - Test `install_shell_completion` writes the script file with the sentinel and binds aliases per the shell-specific rules (bash command-name files/symlinks; single zsh `_aw`; fish `aw.fish` with multi-`complete -c`).
  - Test `install_shell_completion` is idempotent on repeat, and REFUSES to clobber a pre-existing FOREIGN `aw` completion (no sentinel).
  - Test `uninstall_shell_completion` removes only tool-created files/symlinks and leaves foreign files intact.
  - Test that NO user rc/dotfile (`.bashrc`/`.zshrc`/`config.fish`) is created or modified by install or uninstall.
  - Test `aw completion install --dry-run` previews paths without creating files, and `aw completion <shell>` output still works (child-01 regression guard).
  - Test the host-level `aw setup` completion prompt respects confirmation and rejection and is skipped non-interactively.
  - Test `aw install --completion bash` installs completion files, and `--yes` without `--completion` installs nothing (safe default).

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

- [x] V-01 validates E-01
  - Required evidence: Paste passing unit-test output over a real temp HOME/XDG proving `install_shell_completion`/`uninstall_shell_completion` create/remove drop-in files with the correct per-shell alias binding, honor XDG env vars, are idempotent, REFUSE to clobber a foreign `aw` completion, remove only tool-created files on uninstall, and MODIFY NO rc/dotfile.
  - Observed evidence: `python3 -m pytest tests/test_completion.py -o addopts="" -m "" -v` -> `78 passed, 2 skipped` overall; the E-01 classes (all over a REAL temp HOME + real XDG bases, not a mock) PASSED:
    ```
    ResolveCompletionDirTests::test_xdg_env_vars_win PASSED
    ResolveCompletionDirTests::test_fallbacks_when_xdg_unset PASSED
    ResolveCompletionDirTests::test_xdg_precedence_matches_config_module PASSED
    ResolveCompletionDirTests::test_custom_dir_overrides_everything PASSED
    ResolveCompletionDirTests::test_unsupported_shell_raises PASSED
    InstallShellCompletionTests::test_bash_writes_command_name_files_for_each_alias PASSED
    InstallShellCompletionTests::test_fish_writes_single_file_with_multi_complete_c PASSED
    InstallShellCompletionTests::test_zsh_sentinel_does_not_displace_compdef_first_line PASSED
    InstallShellCompletionTests::test_dry_run_writes_nothing PASSED
    InstallShellCompletionTests::test_symlink_to_unexpected_target_is_treated_as_foreign PASSED
    InstallShellCompletionTests::test_refuses_when_a_foreign_alias_file_exists PASSED
    InstallShellCompletionTests::test_refuses_to_clobber_foreign_completion PASSED
    InstallShellCompletionTests::test_sentinel_present_in_every_written_file PASSED
    InstallShellCompletionTests::test_zsh_writes_single_compdef_bound_file_only PASSED
    InstallShellCompletionTests::test_creates_missing_parent_directories PASSED
    InstallShellCompletionTests::test_install_is_idempotent PASSED
    UninstallShellCompletionTests::test_roundtrip_touches_no_dotfile PASSED
    UninstallShellCompletionTests::test_dry_run_removes_nothing PASSED
    UninstallShellCompletionTests::test_removes_only_our_files PASSED
    UninstallShellCompletionTests::test_uninstall_when_nothing_installed_is_a_noop PASSED
    UninstallShellCompletionTests::test_leaves_foreign_aw_file_intact_and_reports_it PASSED
    ```
    Mapping to each required clause: PER-SHELL ALIAS BINDING - bash asserts `agentwf`/`agent-workflows` command-name entries exist with `os.readlink(...) == "aw"`; zsh asserts the site-functions dir listing equals exactly `["_aw"]` AND line 1 is `#compdef aw agentwf agent-workflows`; fish asserts one `aw.fish` containing `complete -c aw `, `complete -c agentwf `, and `complete -c agent-workflows `. XDG - env vars win, and the fallbacks resolve to `~/.local/share/bash-completion/completions`, `~/.local/share/zsh/site-functions`, `~/.config/fish/completions`; precedence asserted EQUAL to `config.config_dir()`. IDEMPOTENT - second install returns the same paths and byte-identical content. NO-CLOBBER - a foreign `aw` (no sentinel) raises `CompletionInstallError`, the foreign bytes are unchanged, and NO alias link was created; a foreign ALIAS file also aborts before the primary is written; a symlink pointing outside the dir is treated as foreign and is NOT written through (target bytes unchanged). UNINSTALL-ONLY-OURS - removes exactly `aw`/`agentwf`/`agent-workflows`, leaves an unrelated `other-tool` file and a foreign `aw` intact (the latter reported under `skipped`). DOTFILE-UNTOUCHED - `assert_no_dotfile_touched()` (checks `.bashrc`, `.bash_profile`, `.zshrc`, `.profile`, `fish/config.fish`) is asserted in the bash/zsh/fish install tests, in `test_removes_only_our_files`, and in `test_roundtrip_touches_no_dotfile` after a full install+uninstall of all three shells. ruff `--select E4,E7,E9,F` -> `All checks passed!`; `ruff format --check` -> `3 files already formatted`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste CLI test output executing `aw completion install`, `aw completion uninstall`, and `aw completion install --dry-run` with exit 0, PLUS a regression assertion that `aw completion <shell>` output (child 01) still works after the `install`/`uninstall` sub-actions are added (proves the parser shape was extended, not redesigned).
  - Observed evidence: From the same `78 passed, 2 skipped` run:
    ```
    CompletionInstallCliTests::test_install_and_uninstall_exit0 PASSED
    CompletionInstallCliTests::test_dry_run_previews_paths_without_creating_files PASSED
    CompletionInstallCliTests::test_custom_dir_flag PASSED
    CompletionInstallCliTests::test_shell_defaults_to_detected_shell PASSED
    CompletionInstallCliTests::test_foreign_file_refusal_exits_1 PASSED
    CompletionInstallCliTests::test_child01_script_output_still_works PASSED
    CompletionInstallSubprocessTests::test_module_cli_install_then_uninstall PASSED
    CompletionCliTests::test_parser_shape_allows_child03_extension PASSED
    CompletionCliTests::test_cli_bash_exit0_and_header PASSED
    CompletionCliTests::test_cli_zsh_and_fish_exit0 PASSED
    CompletionCliTests::test_bare_completion_shell_unset_falls_back_to_bash PASSED
    CompletionCliTests::test_bare_completion_detects_zsh_from_shell_env PASSED
    ```
    `test_install_and_uninstall_exit0` asserts rc 0 for both verbs, that the drop-in `aw` file exists after install and is gone after uninstall, that the installed path is echoed in output, and that no dotfile was touched. `test_dry_run_previews_paths_without_creating_files` asserts rc 0, `[dry-run]` in output, `aw.fish` named, and the file NOT created. `test_foreign_file_refusal_exits_1` asserts rc 1 with the foreign bytes unchanged (a refusal, not a silent overwrite). REGRESSION GUARD (`test_child01_script_output_still_works`) asserts `aw completion bash` -> `# bash completion for aw`, `aw completion zsh` -> `#compdef aw agentwf agent-workflows`, `aw completion fish` -> `complete -c aw `, and that BARE `aw completion` still detects the shell rather than being misread as a verb - proving the parser was EXTENDED, not redesigned; the pre-existing child-01 `CompletionCliTests` also still pass unmodified. `CompletionInstallSubprocessTests` proves the same install/uninstall roundtrip through a REAL subprocess (`python -m agent_workflows`) with rc 0. Live cross-check with a temp XDG:
    ```
    $ python3 -m agent_workflows completion install --shell bash --dry-run   # rc=0
    OK  [dry-run] completion file: .../bash-completion/completions/aw
    OK  [dry-run] completion file: .../bash-completion/completions/agentwf
    OK  [dry-run] completion file: .../bash-completion/completions/agent-workflows
    $ python3 -m agent_workflows completion install --shell bash            # rc=0
    $ ls -la .../bash-completion/completions/
    lrwxrwxrwx agentwf -> aw ; lrwxrwxrwx agent-workflows -> aw ; -rw-r--r-- aw
    $ python3 -m agent_workflows completion bash | tail -1                  # rc=0
    complete -F _aw_completion aw agentwf agent-workflows
    $ python3 -m agent_workflows completion uninstall --shell bash          # rc=0 (dir empty after)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Test demonstrating the host-level `aw setup` completion prompt renders interactively, respects accept/reject, calls `install_shell_completion` only on accept, is skipped non-interactively, and does NOT touch `install_wizard.py`'s repo-policy flow. Paste the test output.
  - Observed evidence: From the same `78 passed, 2 skipped` run:
    ```
    SetupCompletionPromptTests::test_prompt_installs_on_accept PASSED
    SetupCompletionPromptTests::test_prompt_installs_nothing_on_reject PASSED
    SetupCompletionPromptTests::test_skipped_non_interactively PASSED
    SetupCompletionPromptTests::test_skipped_under_yes PASSED
    SetupCompletionPromptTests::test_no_prompt_when_already_installed PASSED
    SetupCompletionPromptTests::test_explicit_none_never_prompts PASSED
    SetupCompletionPromptTests::test_prompt_lives_in_cli_not_install_wizard PASSED
    SetupCompletionPromptTests::test_install_failure_does_not_break_setup PASSED
    ```
    ACCEPT (`input` -> `y`, isatty True) installs the real drop-in `aw` file and touches no dotfile. REJECT (`input` -> `n`) leaves the completion directory NON-EXISTENT, proving `install_shell_completion` is called ONLY on accept. SKIPPED NON-INTERACTIVELY (`isatty` False) and SKIPPED UNDER `--yes` both assert `input` was NEVER called (`m_input.assert_not_called()`) and that nothing was written - so a headless/batch run cannot be blocked on a question nor silently modify a user directory. `test_no_prompt_when_already_installed` and `test_explicit_none_never_prompts` also assert `input` was not called. INSTALL_WIZARD UNTOUCHED (`test_prompt_lives_in_cli_not_install_wizard`) reads `install_wizard.py` source and asserts it contains NONE of `install_shell_completion`, `resolve_completion_dir`, or `completion install`, while asserting `_configure_completion(args, term)` IS present in `cli.py` - so the reviewed integration point is machine-enforced, and `git status --porcelain` confirms `install_wizard.py` is not among the modified files (only README.md, agent_workflows/cli.py, agent_workflows/completion.py, tests/test_completion.py). `test_install_failure_does_not_break_setup` proves a `CompletionInstallError` is swallowed into a warning rather than aborting the host setup flow.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: CLI test executing `aw install --completion <shell>` proving completion files are installed alongside framework files.
  - Observed evidence: From the same `78 passed, 2 skipped` run:
    ```
    InstallCompletionFlagTests::test_flag_is_registered_on_install_and_setup PASSED
    InstallCompletionFlagTests::test_resolve_choice PASSED
    InstallCompletionFlagTests::test_explicit_shell_installs_without_prompting PASSED
    InstallCompletionFlagTests::test_yes_without_flag_installs_nothing PASSED
    InstallCompletionFlagTests::test_auto_detects_shell PASSED
    InstallCompletionFlagTests::test_tip_shown_when_unconfigured_and_hidden_once_installed PASSED
    ```
    `test_flag_is_registered_on_install_and_setup` parses `--completion` on BOTH verbs and all five choices (`auto|bash|zsh|fish|none`). `test_resolve_choice` pins the mapping (absent/`none` -> None, `zsh` -> `zsh`, `auto` + `SHELL=/usr/bin/fish` -> `fish`). `test_explicit_shell_installs_without_prompting` proves the flag installs the real file with `input` never called. `test_auto_detects_shell` writes the real `zsh/site-functions/_aw` under `--completion auto`. SAFE DEFAULT: `test_yes_without_flag_installs_nothing` asserts neither the bash nor fish directory exists and no dotfile was touched. TIP: `test_tip_shown_when_unconfigured_and_hidden_once_installed` captures the `Term` stream, asserts `aw completion install` appears when unconfigured, then asserts the stream is EMPTY after installing (self-suppressing). End-to-end against a real temp repo + temp XDG (framework files AND completion installed by one command):
    ```
    $ python3 -m agent_workflows install /tmp/e04t/repo --yes            # no --completion
      ... Changes committed successfully.
      OK  Tip: Enable tab-completion with 'aw completion install'
    $ ls /tmp/e04t/xd                                                   # nothing written
      ls: cannot access '/tmp/e04t/xd': No such file or directory
    $ python3 -m agent_workflows install /tmp/e04t/repo --yes --completion bash
      OK  bash completion installed in /tmp/e04t/xd/bash-completion/completions (no rc/dotfile modified). Start a new bash shell to pick it up.
    $ ls -la /tmp/e04t/xd/bash-completion/completions/
      lrwxrwxrwx agentwf -> aw ; lrwxrwxrwx agent-workflows -> aw ; -rw-r--r-- aw
    ```
    (the tip correctly no longer printed on the second run, since completion was then configured).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `pytest tests/test_completion.py` (plus any added setup-flow test module) runs with all tests passing - paste the runner output - and `README.md` contains the "Shell Tab Completion" section documenting `aw completion install`.
  - Observed evidence: Module suite including the `slow` subprocess test:
    ```
    $ python3 -m pytest tests/test_completion.py -o addopts="" -m "" -q
    ...................................s..s.................................
    ........
    78 passed, 2 skipped in 2.72s
    ```
    (the 2 skips are the pre-existing child-01 zsh/fish shell-syntax checks, skipped-not-failed because those shells are absent on this runner; the module went from 35 passed/2 skipped at child 02 to 78 passed/2 skipped, i.e. 43 new tabcomp-03 tests, all passing). Default-marker run (`-m "not slow"`, the repo's normal invocation) also green. FULL DEFAULT SUITE:
    ```
    $ python3 -m pytest
    2722 passed, 3 skipped in 24.62s
    ```
    README: `ReadmeCompletionDocsTests::test_readme_has_shell_tab_completion_section PASSED`, asserting the literal strings `Shell Tab Completion`, `aw completion install`, and `source <(aw completion bash)` are present. The new README section documents `aw completion install`/`uninstall`, `--shell`/`--dry-run`, the per-shell drop-in path table with XDG variables, the never-edits-your-dotfiles promise, idempotent/no-clobber behavior, `aw install . --completion auto`, and the `source <(...)` one-off. LINT: ruff `--select E4,E7,E9,F` on all four changed files -> `All checks passed!`; `ruff format --check` -> `3 files already formatted` (README is not a ruff target). SLOW-SUITE HONESTY (run DECISION 01-jolfpj-D3): `pytest -m ""` at HEAD reports `4 failed, 3049 passed, 3 skipped`; the SAME 4 guard tests fail at the frozen base 5f65618 (verified in a throwaway worktree: base `14 failed, 2996 passed, 3 skipped`), `comm -13` shows ZERO failures at HEAD absent from base, and the undeclared-leaf count is IDENTICAL 42 -> 42 with the description-gap list IDENTICAL 33 -> 33 - proving this plan added no new CLI leaf and no new failure. That backlog needs `agent_workflows/command_surface.py`, which is outside this plan's Scope-Paths.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: execution requires explicit human approval. Upon approval, implement according to the checklist, verify all V items with test outputs, run `aw ipd lint --phase pre-transition`, and finalize via the IPD lifecycle workflow.
