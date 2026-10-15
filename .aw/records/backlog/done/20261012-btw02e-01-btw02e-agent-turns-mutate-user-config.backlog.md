- Id: btw02e
- Status: done
- Graduated-To: btw02e
- Blocks-Release: next
- Set: btw02e
- Priority: high
- Work-Kind: bug
- Summary: aw oc run agent turns write the operator's real user config (an agent set color_depth none and silently decolored every command)

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD 9y27t2 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-btw02e-01-9y27t2-contain-agent-turn-writes-to-the-operator-s-user-config.ipd.md); evidence .aw/records/plans/executed/20261012-btw02e-01-9y27t2-contain-agent-turn-writes-to-the-operator-s-user-config.ipd.md
- 2026-10-12 graduated (aw set): graduated to plan 9y27t2 (to-review, lint clean)
- 2026-10-12 created (aw backlog): Filed from operator diagnosis 2026-10-12: lane cvtg9u agent left color_depth=none in ~/.config/agent-workflows/config.json

## What happened (measured, 2026-10-12)

An `aw oc run` agent turn executing in lane worktree `.aw/worktrees/cvtg9u` (while graduating backlog `cvtg9u`) ran, among other probes:

    AW_NO_REEXEC=1 python3 -m agent_workflows config set color_depth none >/dev/null

against the OPERATOR'S REAL user config. The opencode log records that command at 2026-10-12T09:06:22Z; `~/.config/agent-workflows/config.json` mtime is the same second; it then contained `"color_depth": "none"` and nothing restored it. The turn also issued `set color_depth 16` / `256` / `$pin` (apparently some under a temp `XDG_CONFIG_HOME`, since the file was not modified again). Result: lifecycle columns of `aw attention`, `aw runs` and the `aw oc run` summary tables rendered uncolored for the operator from then on, with no indication why. Diagnosed and reverted by hand (`aw config unset color_depth`).

Work-Kind `bug`: user-perceptible (the operator lost an essential UX signal on every command) and it is a containment failure, not cosmetic.

## Root cause

The runner isolates the REPO (per-item worktree) but not the USER STATE. `runner_shared.pinned_child_env` (the one child-env construction both hosts use; `oc_runipd.py` ~2915, `agy_runipd.py`) starts from `os.environ.copy()` and never overrides `XDG_CONFIG_HOME` or `AW_HOME`, so every `aw` an agent runs from a lane resolves the operator's real stores. OpenCode's `permission.external_directory=deny` does NOT cover this: it gates the agent's FILE TOOLS on paths outside the workdir, while a `bash` command that runs `aw config set` writes `~/.config` through the aw process itself.

## Who reads XDG_CONFIG_HOME (it is NOT aw-specific)

`XDG_CONFIG_HOME` is the freedesktop XDG Base Directory variable; unset means `~/.config`. It is shared by EVERY XDG-aware program in the agent's process tree, which is the central caveat below. Inside aw:
- `config.config_dir()` -> `$XDG_CONFIG_HOME/agent-workflows/` holds `config.json` (color_depth, repos.installed/search/exclude, defaults, run.on_conflict, ...), and through it `runner_profiles.store_dir()` (`runner-profiles.json`), `completion.py` (`completion-notice.json`), `leak_sanitizer` (`local-leaks-hints.json`), `model_vocab` user vocab.
- `project_context.get_default_aw_home()`: `AW_HOME`, else `$XDG_CONFIG_HOME/agent-workflows`, else `~/.aw` (home records backend / project registry).
- `oc_models.py` reads `$XDG_CONFIG_HOME/opencode/opencode.json` (model/provider config).
- `completion.py` installs fish completions under `$XDG_CONFIG_HOME/fish/`.
Outside aw, in the same agent environment: opencode itself (`~/.config/opencode`: auth keys, config, plugins), `gh` (`~/.config/gh/hosts.yml`: GitHub auth), git (`$XDG_CONFIG_HOME/git/config` is a valid global git config location), pip, npm-adjacent tools, and so on.

## How the fix should work

1. Redirect ONLY aw's own user state for an agent turn, not `XDG_CONFIG_HOME` wholesale. Add an aw-specific override, e.g. `AW_CONFIG_DIR`, honored FIRST by `config.config_dir()` (so every store above that routes through it follows automatically; keep the `except` fallbacks in `leak_sanitizer._config_dir` and `model_vocab._user_config_dir` consistent with it). In `pinned_child_env` (or the agent-turn env built from it in both hosts) set `AW_CONFIG_DIR` and `AW_HOME` to a per-run (or per-item) directory under the run's state, e.g. `<run-state>/user-config/`.
2. SEED that directory with a COPY of the operator's real `config.json` (and `runner-profiles.json`) at turn start, so reads behave identically (color pin, repo lists, profiles, on_conflict policy) and only WRITES are contained. An empty dir would silently change behavior of commands the agent runs for evidence (e.g. `aw doctor`, repo discovery).
3. At turn end, DIFF the sandbox copy against the seed. If the agent changed user config, do NOT propagate it; report it in the run summary and `aw runs` ("item X modified user config key color_depth: unset -> none; discarded"). A durable record beats silent containment, because an agent that needed the change should say so to the human.
4. The DRIVER process itself keeps the real config (it legitimately reads policy and may update `repos.installed`); only agent turns are redirected.
5. Behavioral test: drive a runner turn (fake host) whose agent command runs `aw config set color_depth none`; assert the real (temp-XDG) operator config is byte-unchanged, the run report names the discarded change, and a read (`aw config get`) inside the turn sees the seeded values.

## Caveats

- Do NOT override `XDG_CONFIG_HOME` itself for agent turns. It would also relocate opencode's own config/auth (the host runs inside that env), `gh` auth, a global git config, and model resolution in `oc_models.py`, breaking the turn in confusing ways (no credentials, wrong model, missing git identity). An aw-specific variable avoids that blast radius. If XDG is ever overridden, it must be with a seeded copy of everything those tools need, which is fragile.
- `AW_HOME` precedence: `get_default_aw_home` falls back to `$XDG_CONFIG_HOME/agent-workflows`; with `AW_CONFIG_DIR` introduced, decide (and document) whether AW_HOME's fallback follows `AW_CONFIG_DIR`, so the two never split across real and sandbox.
- This is an environment SELECTOR, not a security boundary (same honest limit as the role marker in `oc_runipd.py`): a same-user agent can unset the variable or write `~/.config` directly. It stops the observed case (an agent following normal practice running `aw config set` to test behavior). Hard enforcement needs an OS sandbox. Consider also adding to the agent prompt/contract: "never modify user config; use a temp `XDG_CONFIG_HOME`/`AW_CONFIG_DIR` for experiments".
- Test-suite parity: 30 test files already set a temp `XDG_CONFIG_HOME`; the new variable must not let an inherited `AW_CONFIG_DIR` from an outer run leak into tests (tests should clear it, like `_capable_tty` clears color env), and `pinned_child_env` must overwrite rather than inherit it so a nested driver does not reuse an outer run's sandbox (same rule already applied to `RUN_ID_ENV`).
- Both hosts: the fix must land in the shared env construction so `aw agy run` gets it too.
- `upgrade_rehearsal.sandbox_env` already does the right thing for its own use (temp `XDG_CONFIG_HOME` + `AW_HOME`); reuse its reasoning, not necessarily its XDG override.

## Provenance
- Observed: opencode log run `204e56ba`, lane `cvtg9u`, 2026-10-12T08:39Z..09:24Z.
- Related: cvtg9u (plan lv0dvv), y11p5u.
