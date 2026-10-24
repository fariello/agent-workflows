- Id: dthgoi
- Status: open
- Blocks-Release: next
- Set: tabcomp
- Priority: high
- Work-Kind: bug
- Summary: aw completion install: verify shell loader prerequisites and guide activation

## Workflow history
- 2026-10-24 open (aw set): status set to open
- 2026-10-23 created (aw backlog): aw completion install: verify shell loader prerequisites and guide activation

### Problem Statement

Plan `tabcomp-03` (`jolfpj`, commit `de51d91`) implemented drop-in shell completion via `aw completion install` (`agent_workflows/cli.py:8761-8820` and `agent_workflows/completion.py:718-845`). The design prioritized zero dotfile pollution, installing completion scripts into standard XDG auto-discovery paths:
- Bash: `${XDG_DATA_HOME:-~/.local/share}/bash-completion/completions/aw` (with symlinks for aliases `agentwf` and `agent-workflows`)
- Zsh: `${XDG_DATA_HOME:-~/.local/share}/zsh/site-functions/_aw`
- Fish: `${XDG_CONFIG_HOME:-~/.config}/fish/completions/aw.fish`

The implementation relied on the assumption in plan `jolfpj` (Findings, line 77):
> "Modern Linux and macOS shells auto-discover completion files in `${XDG_DATA_HOME:-~/.local/share}/bash-completion/completions/` (and the fish/zsh equivalents) without requiring any shell restarts or rc file edits."

In practice, this assumption is false for many environments:
1. **Bash:** Bash itself has no built-in knowledge of `~/.local/share/bash-completion/completions/`. That directory is only scanned dynamically if the system `bash-completion` package (`/usr/share/bash-completion/bash_completion` or `/etc/bash_completion`) has been sourced by the user's rc files, defining `_completion_loader`. In minimal or custom configurations (for example `linux-config` or server environments), system `bash-completion` is not sourced. In this state, `aw completion install` reports success and prints `Next start a new bash shell (or run exec bash) to pick it up`, but restarting the shell never activates completion.
2. **Zsh:** `${XDG_DATA_HOME:-~/.local/share}/zsh/site-functions` is not included in `$fpath` by default on many standard distributions or user setups. If the directory is absent from `$fpath` before `compinit` runs, Zsh will never discover `_aw`.

The result is a misleading user experience where the installer claims success and tells the user to restart their shell, but completion remains completely non-functional.

### Proposed Solution and Scope

1. **Loader Prerequisite Detection (`agent_workflows/completion.py`):**
   - Implement environment/prerequisite checks for each supported shell:
     - For Bash: detect whether `_completion_loader` is available in the current environment or whether `/usr/share/bash-completion/bash_completion` is sourced in the user's rc hierarchy. Check whether the system `bash-completion` package is installed on the host.
     - For Zsh: detect whether `${XDG_DATA_HOME:-~/.local/share}/zsh/site-functions` is present in `$fpath`.
     - For Fish: verify that the user's fish configuration includes default completion discovery paths.

2. **Diagnostic and Guided Reporting (`agent_workflows/cli.py`):**
   - When `aw completion install` runs and detects that the shell's auto-discovery framework is inactive or missing:
     - Do not print the generic "start a new shell to pick it up" message.
     - Emit a clear warning explaining that the shell is not configured to load completions from the drop-in directory.
     - Print the exact, copy-pasteable line required to enable the loader:
       - Bash: `[ -f /usr/share/bash-completion/bash_completion ] && . /usr/share/bash-completion/bash_completion`
       - Zsh: `fpath=(~/.local/share/zsh/site-functions $fpath)`
     - Provide the direct fallback sourcing line for immediate or standalone use:
       - `source ~/.local/share/bash-completion/completions/aw` (or `source <(aw completion bash)`)

3. **Opt-In Dotfile Helper (Optional / Explicit):**
   - Provide an explicit flag (such as `--enable-loader` or `--rc`) or, in interactive mode, an explicit confirmation prompt offering to append the loader line to the user's `~/.bashrc` / `~/.zshrc`.
   - Preserve the existing safety guarantee as the default: never modify rc files without explicit user consent.

4. **Health Check Integration (`aw doctor`):**
   - Extend `aw doctor` to verify whether installed shell completion drop-ins are actually active and loadable in the current user session, surfacing a warning if drop-ins exist but the shell loader is absent.

5. **Test Coverage (`tests/test_completion.py`):**
   - Add unit tests verifying loader prerequisite detection under both active and inactive states.
   - Assert diagnostic messages when prerequisites are unmet.
   - Verify non-interactive batch behavior remains safe.
