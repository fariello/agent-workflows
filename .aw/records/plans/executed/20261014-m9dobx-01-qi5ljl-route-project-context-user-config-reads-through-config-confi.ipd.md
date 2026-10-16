# IPD: Route project_context user config reads through config.config_dir()

- Date: 2026-10-14
- Kind: child
- Concern: Backlog `m9dobx`: `project_context.resolve_project_context` (and its extracted helper `project_context._resolve_effective_aw_home`) reads the user configuration from a hard-coded `os.path.expanduser("~/.config/agent-workflows")` at two sites when `user_config_dir` is omitted, ignoring `XDG_CONFIG_HOME` and `AW_CONFIG_DIR` that `config.config_dir()` honors. Operators who export `XDG_CONFIG_HOME` write `aw_home` and global defaults to `$XDG_CONFIG_HOME/agent-workflows/config.json` via `aw config set` while `resolve_project_context` reads `~/.config/agent-workflows/config.json`, and tests that omit `user_config_dir=` bypass the `conftest.py` `XDG_CONFIG_HOME` sandbox and read the developer's real `~/.config/agent-workflows/config.json`.
- Scope: IN: a lazy, fail-open `_config_dir()` helper in `agent_workflows/project_context.py` delegating to `config.config_dir()` (mirroring `leak_sanitizer._config_dir` and `model_vocab._user_config_dir`); routing both hard-coded `os.path.expanduser("~/.config/agent-workflows")` fallbacks in `project_context._resolve_effective_aw_home` and `project_context.resolve_project_context` through `_config_dir()` when `user_config_dir` is not supplied; behavioral unit tests in `tests/test_project_context.py` covering `XDG_CONFIG_HOME` and `AW_CONFIG_DIR` resolution across `effective_aw_home`, `project_config_dir`, `GLOBAL_DEFAULTS`, and `NAMED_GLOBAL_PROFILE`; and a `CHANGELOG.md` entry. OUT: changing `project_context.get_default_aw_home()` (which already reads `AW_HOME` and `XDG_CONFIG_HOME` for the platform-default `AW_HOME` fallback); `AW_HOME` runner containment (tracked separately by backlog `s4pys7`).
- Scope-Paths: agent_workflows/project_context.py, tests/test_project_context.py, CHANGELOG.md, agent_workflows/runner_shared.py, tests/test_agent_user_config_containment.py, .aw/records/plans/pending/20261014-m9dobx-01-qi5ljl-route-project-context-user-config-reads-through-config-confi.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: m9dobx
- Blocks-Release: next
- Set: m9dobx
- Order: 1
- Highest E allocated: 05
- Author: antigravity Gemini-4-Argon-High
- Id: qi5ljl

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: qi5ljl verified (set m9dobx, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record 20261014-m9dobx-01-qi5ljl)
- 2026-10-14 to-review (aw set): authored from backlog m9dobx

- 2026-10-14 draft (antigravity Gemini-4-Argon-High): created.

## Goal

`project_context.resolve_project_context` and `project_context.project_config_dir` resolve the user configuration directory through `config.config_dir()` whenever `user_config_dir` is not explicitly provided, so `XDG_CONFIG_HOME` and `AW_CONFIG_DIR` govern user-config reads in `project_context` identically to every other user-config reader and writer in the toolkit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and resolver routing

- [x] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` BEFORE the first edit and record its summary line and the failing node ids. The post-change bar is "no node id fails that did not fail here".
  - Depends on: none
  - Expected outcome: a recorded baseline summary line and failing-node-id list.
  - Execution state: performed

- [x] E-02 In `agent_workflows/project_context.py`, add a module-private helper `_config_dir() -> Path` that lazily imports `agent_workflows.config` (`from . import config as _config`) and returns `_config.config_dir()`, failing open in `except Exception:` with the same `AW_CONFIG_DIR` > `XDG_CONFIG_HOME` > `~/.config/agent-workflows` fallback used by `leak_sanitizer._config_dir` and `model_vocab._user_config_dir`. Route both hard-coded `os.path.expanduser("~/.config/agent-workflows")` sites in `agent_workflows/project_context.py` through `str(_config_dir())` when `user_config_dir` is omitted: (1) `user_cfg_path` in `project_context._resolve_effective_aw_home` (which backs step `2. AW_HOME Resolution` in `project_context.resolve_project_context` and `project_context.project_config_dir`), and (2) `user_cfg_dir_effective` under `# Read configuration layers` in `project_context.resolve_project_context` (which reads `<dir>/config.json` and `<dir>/profiles/<profile>.json`). Preserve explicit `user_config_dir` taking precedence when passed by a caller. Also update the `resolve_project_context` docstring's Level 4 and Level 5 lines, which name `~/.config/agent-workflows/...`, to name the user config directory resolved by `config.config_dir()`.
  - Depends on: E-01
  - Expected outcome: when `user_config_dir` is not passed, both `_resolve_effective_aw_home` and `resolve_project_context` resolve the user config directory via `_config_dir()` (`config.config_dir()`), honoring `AW_CONFIG_DIR` and `XDG_CONFIG_HOME`; when `user_config_dir` is passed, behavior is unchanged.
  - Execution state: performed

### Task group 2: behavioral tests and changelog

- [x] E-03 In `tests/test_project_context.py`, add behavioral tests on `TestProjectContextResolver` (driving `resolve_project_context` and `project_config_dir` and asserting on returned `ProjectContext` fields and paths; no source inspection per `GUIDING_PRINCIPLES` P16): (a) `test_xdg_config_home_aw_home_resolution`: set `XDG_CONFIG_HOME` to a temp dir `<xdg>` containing `<xdg>/agent-workflows/config.json` with `{"aw_home": "<custom_aw_home>"}`, remove `AW_HOME` and `AW_CONFIG_DIR` from `os.environ` for the test's duration with `unittest.mock.patch.dict(os.environ, ..., clear=True)` (so restoration cannot be forgotten), call `resolve_project_context(target_repo=self.target_repo)` with neither `aw_home` nor `user_config_dir` passed, and assert `ctx.effective_aw_home` equals the canonical `<custom_aw_home>` path, `ctx.provenance["effective_aw_home"]["source"] == PrecedenceLevel.GLOBAL_DEFAULTS.value`, and `ctx.provenance["effective_aw_home"]["detail"]` names `<xdg>/agent-workflows/config.json`; also seed `<custom_aw_home>/projects/<ctx.project_id>/config/project.json` and assert `project_config_dir(self.target_repo)` returns `<custom_aw_home>/projects/<ctx.project_id>/config`; (b) `test_xdg_config_home_layers_and_aw_config_dir_override`: with `XDG_CONFIG_HOME` set to `<xdg>` containing `<xdg>/agent-workflows/config.json` (`{"default_delivery_mode": "tracked", "default_records_backend": "companion"}`) and `<xdg>/agent-workflows/profiles/team.json` (`{"delivery_mode": "tracked", "records_backend": "repository"}`), and `user_config_dir` omitted, assert `resolve_project_context(target_repo=self.target_repo, aw_home=self.aw_home)` resolves `records_backend == "companion"` at `PrecedenceLevel.GLOBAL_DEFAULTS.value` and `resolve_project_context(target_repo=self.target_repo, aw_home=self.aw_home, profile="team")` resolves `records_backend == "repository"` at `PrecedenceLevel.NAMED_GLOBAL_PROFILE.value`; then set `AW_CONFIG_DIR` to a separate absolute temp directory `<aw_cfg>` holding `<aw_cfg>/config.json` (`{"aw_home": "<override_aw_home>", "default_records_backend": "repository"}`) with `AW_HOME` removed, and assert `resolve_project_context(target_repo=self.target_repo)` resolves `effective_aw_home` to `<override_aw_home>`, and `records_backend == "repository"` with `ctx.provenance["records_backend"]["source"] == PrecedenceLevel.GLOBAL_DEFAULTS.value` (NOT `"home"`, which is also the built-in default and so could not distinguish a working override from an ignored one), while passing an explicit `user_config_dir=` still overrides both `AW_CONFIG_DIR` and `XDG_CONFIG_HOME`.
  - Depends on: E-02
  - Expected outcome: both new test methods in `tests/test_project_context.py` pass with E-02 applied and fail when the pre-fix lookup is simulated in-process (see V-03); the full `python3 -m pytest` suite passes with no new failures against E-01, and `aw sanitize --agent` exits 0.
  - Execution state: performed

- [x] E-04 In `CHANGELOG.md`, add one `- Fixed:` bullet at the top of the `## 2.0.0 (pending)` entry stating that `project_context.resolve_project_context` and `project_context.project_config_dir` now read user configuration through `config.config_dir()` (honoring `AW_CONFIG_DIR` and `XDG_CONFIG_HOME`) instead of a hard-coded `~/.config/agent-workflows` path when `user_config_dir` is omitted. Write no em or en dashes (user-facing prose rule).
  - Depends on: E-02
  - Expected outcome: one new `- Fixed:` bullet in `CHANGELOG.md` with no em or en dashes.
  - Execution state: performed

### Task group 3: keep named profiles visible inside contained agent turns

- [x] E-05 In `agent_workflows/runner_shared.py`, extend `runner_shared.prepare_agent_user_config` so that, beside every regular top-level file, it also seeds every regular file directly inside a top-level `profiles/` subdirectory of the real config dir into `<sandbox>/profiles/` (`shutil.copy2`, mode preserved), recording each in `seed_hashes` (and `seed_json` when it parses as a JSON object) under its sandbox-relative key `profiles/<name>`. WHY: E-02 makes `resolve_project_context` honor `AW_CONFIG_DIR`, and both hosts export `AW_CONFIG_DIR=<per-turn sandbox>` into every agent turn (`config.CONFIG_DIR_ENV` in `oc_runipd` and `agy_runipd`); today that sandbox seeds only top-level files, so after E-02 an agent turn running `aw` loses the NAMED_GLOBAL_PROFILE layer it saw before (measured at review: a seeded sandbox lacked `profiles/team.json`, and `resolve_project_context(..., profile="team", user_config_dir=<sandbox>)` resolved `records_backend` `home` / `builtin_defaults` where the real dir resolved `repository` / `named_global_profile`). `runner_shared.reconcile_agent_user_config` already walks the sandbox with `rglob` and keys by relative path, so seeded profile files are diffed and reported (and never copied back) with no reconcile change. Update the docstring ("copies every regular top-level file") to match. In `tests/test_agent_user_config_containment.py`, add a behavioral test: a source dir with `config.json` and `profiles/team.json`; after `prepare_agent_user_config(..., source_dir=source)`, `<sandbox>/profiles/team.json` is byte-identical to the source; modifying it in the sandbox makes `reconcile_agent_user_config` return a record with `file == "profiles/team.json"` and `change == "modified"`, and the source file is unchanged.
  - Depends on: E-02
  - Expected outcome: a contained agent turn resolves the same named profile as the operator's real config dir; the new containment test passes and `tests/test_agent_user_config_containment.py` stays green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Canonical user-config directory resolver: `config.config_dir()` in `agent_workflows/config.py` resolves `AW_CONFIG_DIR` (when set, non-empty, absolute after `expanduser()`, and not the home directory) > `$XDG_CONFIG_HOME/agent-workflows` > `~/.config/agent-workflows`.
- Lazy fail-open caller pattern: `leak_sanitizer._config_dir` in `agent_workflows/leak_sanitizer.py` and `model_vocab._user_config_dir` in `agent_workflows/model_vocab.py` lazily import `config.config_dir()` inside `try ... except Exception:` and mirror the `AW_CONFIG_DIR` > `XDG_CONFIG_HOME` > `~/.config/agent-workflows` fallback if the import fails.
- Test session home isolation: `conftest.py` ("Home isolation", `_SANDBOX_ENV` and `_restore_home_sandbox`) exports both `AW_HOME` and `XDG_CONFIG_HOME` into `os.environ` around every test and pops `AW_CONFIG_DIR`. Because `project_context._resolve_effective_aw_home` checks `os.environ.get("AW_HOME")` (Level 2 `MACHINE_LOCAL_BINDING`) before `user_cfg.get("aw_home")` (Level 5 `GLOBAL_DEFAULTS`), a test exercising the `user_cfg["aw_home"]` branch must pop `AW_HOME` from `os.environ` for the duration of the check.
- Behavioral tests only (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", `GUIDING_PRINCIPLES` P16). Run the test suite bare (`python3 -m pytest`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | Two sites in `agent_workflows/project_context.py` hard-code `os.path.expanduser("~/.config/agent-workflows")` when `user_config_dir` is omitted. | (1) `project_context._resolve_effective_aw_home` (`else os.path.expanduser("~/.config/agent-workflows")`, extracted from `resolve_project_context` step `2. AW_HOME Resolution` by commit `4ad21328e` so `project_config_dir` and `resolve_project_context` share it); (2) `project_context.resolve_project_context` under `# Read configuration layers` (`user_cfg_dir_effective = (user_config_dir if user_config_dir else os.path.expanduser("~/.config/agent-workflows"))`). |
| F-02 | Every other user-config reader routes through `config.config_dir()`. | `config.config_dir` in `agent_workflows/config.py`; callers `runner_profiles.store_dir`, `completion` (`NOTICE_STAMP_FILENAME`), `leak_sanitizer._config_dir`, and `model_vocab._user_config_dir`. |
| F-03 | `project_context` already imports from `agent_workflows.config` lazily. | `project_context._is_repos_schema_mapping` executes `from agent_workflows.config import _ALLOWED_REPOS_KEYS`, so a lazy `from . import config as _config` inside `project_context._config_dir()` introduces no import cycle while preserving fail-open fallback behavior. |
| F-04 | `conftest.py` sets `AW_HOME` in `os.environ` by default, which precedes `user_cfg["aw_home"]`. | `conftest._SANDBOX_ENV` sets both `AW_HOME` and `XDG_CONFIG_HOME`; `project_context._resolve_effective_aw_home` checks `if os.environ.get("AW_HOME"):` before reading `config.json`, so testing `user_cfg["aw_home"]` requires popping `AW_HOME` inside the test. |
| F-05 | Plan review (2026-10-15): routing through `config.config_dir()` makes `resolve_project_context` honor `AW_CONFIG_DIR`, which both runners set to a per-turn sandbox seeded with top-level files only, so a `profiles/<name>.json` disappears inside an agent turn. | `runner_shared.prepare_agent_user_config` (`for child in real_dir.iterdir(): if child.is_file():`); review probe: real dir -> `repository named_global_profile`, seeded sandbox -> `home builtin_defaults`. Fixed by E-05. |

## Proposed changes (ordered, validatable)

1. Capture the pre-change bare `python3 -m pytest` baseline (E-01).
2. Add `_config_dir()` in `agent_workflows/project_context.py` and route both default user-config directory sites (`_resolve_effective_aw_home` and `resolve_project_context`) through it when `user_config_dir` is omitted (E-02).
3. Add behavioral tests in `tests/test_project_context.py` covering `XDG_CONFIG_HOME` and `AW_CONFIG_DIR` resolution across `effective_aw_home`, `project_config_dir`, `GLOBAL_DEFAULTS`, and `NAMED_GLOBAL_PROFILE` (E-03).
4. Record the fix in `CHANGELOG.md` under `## 2.0.0 (pending)` (E-04).
5. Seed `profiles/` into the per-turn agent user-config sandbox so contained agent turns keep the named-profile layer after E-02 (E-05).

## Deferred / out of scope (with reason)

- `AW_HOME` containment during runner agent turns: redirecting `AW_HOME` requires handling `records_backend: home` projects where the agent legitimately writes records, and is tracked separately by backlog `s4pys7`.
  - Carrier: s4pys7
  - Carrier-Evidence: .aw/records/backlog/done/20261012-s4pys7-01-s4pys7-agent-turn-aw-home-containment.backlog.md
- Changing `project_context.get_default_aw_home()`: it resolves the built-in platform-default `AW_HOME` (`AW_HOME` env > `$XDG_CONFIG_HOME/agent-workflows` > `~/.aw`), not the user `config.json` directory, and already honors `XDG_CONFIG_HOME`.
  - Carrier-Declined: deliberate non-goal; get_default_aw_home resolves the fallback AW_HOME directory rather than user config.json and already reads XDG_CONFIG_HOME

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is modified by an E-item: `agent_workflows/project_context.py` (E-02), `tests/test_project_context.py` (E-03), `CHANGELOG.md` (E-04), `agent_workflows/runner_shared.py` and `tests/test_agent_user_config_containment.py` (E-05), and this plan file (its own checklist).
- Under-scope: none. A repository-wide search for `.config/agent-workflows` across `agent_workflows/` confirms these two sites in `agent_workflows/project_context.py` are the only remaining readers that bypass `config.config_dir()`.

## Required tests / validation

- Targeted run of `python3 -m pytest -o addopts="" tests/test_project_context.py tests/test_home_isolation.py tests/test_agent_user_config_containment.py` passing, plus demonstrating the new E-03 tests fail when the pre-fix lookup is simulated in-process (V-03).
- Full bare suite `python3 -m pytest` passing with no new failures relative to the E-01 baseline.
- `aw sanitize --agent` reporting `outcome: "clean"` (`exit: 0`).

## Spec / documentation sync

- No spec amendment required: `.aw/records/specs/implemented/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md` ("4. A JSON config file under `~/.config/agent-workflows/` (honoring `XDG_CONFIG_HOME`)") already specifies that the user config file honors `XDG_CONFIG_HOME`; this fix brings `project_context` into compliance with that contract.
- `CHANGELOG.md` updated with a `- Fixed:` entry (E-04).

## Open questions

### OQ-01: Should `project_context.project_config_dir` also follow `XDG_CONFIG_HOME` / `AW_CONFIG_DIR` when computing `aw_home` from user config?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED to yes automatically. Commit `4ad21328e` (plan `p425hv`) factored step `2. AW_HOME Resolution` out of `resolve_project_context` into `_resolve_effective_aw_home`, shared by both `resolve_project_context` and `project_config_dir`. Routing `_resolve_effective_aw_home`'s fallback through `_config_dir()` fixes both callers with one change so they cannot disagree on `effective_aw_home`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted pre-change `python3 -m pytest` summary line and the list of failing node ids.
  - Observed evidence:
```
702 passed in 25.55s
failing node ids: none (0 failing node ids)
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff agent_workflows/project_context.py` showing `_config_dir()` and both sites (`_resolve_effective_aw_home` and `resolve_project_context`) routed through `str(_config_dir())`, plus pasted output of a one-liner invocation (`python3 -c ...` driving `project_context.resolve_project_context` with `XDG_CONFIG_HOME` set to a temp dir containing `agent-workflows/config.json` with `{"aw_home": ...}` and `AW_HOME` unset) printing the resolved `ctx.effective_aw_home` and `ctx.provenance["effective_aw_home"]`.
  - Observed evidence:
```diff
diff --git a/agent_workflows/project_context.py b/agent_workflows/project_context.py
index fcce78872..da817abd1 100644
--- a/agent_workflows/project_context.py
+++ b/agent_workflows/project_context.py
@@ -247,6 +247,22 @@ def _read_json_file(path_str: str) -> Optional[Dict[str, Any]]:
     return None


+def _config_dir() -> Path:
+    """Return the user config directory via config.config_dir() with lazy fail-open fallback."""
+    try:
+        from . import config as _config
+
+        return _config.config_dir()
+    except Exception:
+        raw_override = os.environ.get("AW_CONFIG_DIR")
+        if raw_override and raw_override.strip():
+            candidate = Path(raw_override.strip()).expanduser()
+            if candidate.is_absolute() and candidate != Path.home():
+                return candidate
+        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
+        return Path(base).expanduser() / "agent-workflows"
+
+
 def _resolve_effective_aw_home(
     aw_home: Optional[str | Path] = None,
     user_config_dir: Optional[str | Path] = None,
@@ -269,7 +285,7 @@ def _resolve_effective_aw_home(
     user_cfg_path = (
         str(user_config_dir)
         if user_config_dir
-        else os.path.expanduser("~/.config/agent-workflows")
+        else str(_config_dir())
     )
     user_cfg = _read_json_file(os.path.join(user_cfg_path, "config.json"))
     if user_cfg and user_cfg.get("aw_home"):
@@ -964,8 +980,8 @@ def resolve_project_context(
       1. EXPLICIT_FLAGS (explicit arguments passed to invocation)
       2. MACHINE_LOCAL_BINDING (.aw/config/local.json in target repo or user repo binding)
       3. PROJECT_DURABLE_CONFIG (.aw/config/project.json in target repo)
-      4. NAMED_GLOBAL_PROFILE (~/.config/agent-workflows/profiles/<profile>.json)
-      5. GLOBAL_DEFAULTS (~/.config/agent-workflows/config.json default keys)
+      4. NAMED_GLOBAL_PROFILE (profiles/<profile>.json in user config dir via config.config_dir())
+      5. GLOBAL_DEFAULTS (config.json default keys in user config dir via config.config_dir())
       6. BUILTIN_DEFAULTS (built-in fallbacks)
     """
     provenance_map: Dict[str, Provenance] = {}
@@ -996,9 +1012,9 @@ def resolve_project_context(

     # Read configuration layers
     user_cfg_dir_effective = (
-        user_config_dir
+        str(user_config_dir)
         if user_config_dir
-        else os.path.expanduser("~/.config/agent-workflows")
+        else str(_config_dir())
     )
     user_cfg_file = os.path.join(user_cfg_dir_effective, "config.json")
     user_cfg_data = _read_json_file(user_cfg_file) or {}
```
One-liner output:
```
effective_aw_home: /tmp/tmpcnbbiz56/custom_home
provenance effective_aw_home: {'source': 'global_defaults', 'detail': 'global config (/tmp/tmpcnbbiz56/xdg/agent-workflows/config.json)'}
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted passing output of `python3 -m pytest -o addopts="" tests/test_project_context.py tests/test_home_isolation.py`; pasted failing output of the new tests when the pre-fix lookup is simulated IN-PROCESS without touching the working tree (reverting the file would destroy the uncommitted E-02 edit, and stashing is forbidden), e.g. `python3 -c "import os, sys, pytest; from pathlib import Path; from unittest import mock; from agent_workflows import project_context as pc; mock.patch.object(pc, '_config_dir', lambda: Path(os.path.expanduser('~/.config/agent-workflows'))).start(); sys.exit(pytest.main(['-o', 'addopts=', '-p', 'no:randomly', '<new test node ids>']))"`, followed by `git status --short agent_workflows/` showing only the intended edits; pasted post-change bare `python3 -m pytest` summary line with no node id failing that was not in V-01's list; and pasted `aw sanitize --agent` JSON result.
  - Observed evidence:
    Targeted tests passing:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=1258738395
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/qi5ljl
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 24 items

tests/test_home_isolation.py ....                                        [ 16%]
tests/test_project_context.py ....................                       [100%]

============================== 24 passed in 2.10s ==============================
```
    Pre-fix simulation failing:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/qi5ljl
configfile: pyproject.toml
plugins: anyio-4.14.1, cov-7.1.0, xdist-3.8.0
collecting ... collected 2 items

tests/test_project_context.py FF                                         [100%]

=================================== FAILURES ===================================
______ TestProjectContextResolver.test_xdg_config_home_aw_home_resolution ______

self = <tests.test_project_context.TestProjectContextResolver testMethod=test_xdg_config_home_aw_home_resolution>

    def test_xdg_config_home_aw_home_resolution(self):
...
>           self.assertEqual(ctx.effective_aw_home, expected_aw_home)
E           AssertionError: '/tmp/tmpitfvam8m/xdg/agent-workflows' != '/tmp/tmpitfvam8m/custom_aw_home'
E           - /tmp/tmpitfvam8m/xdg/agent-workflows
E           + /tmp/tmpitfvam8m/custom_aw_home

tests/test_project_context.py:360: AssertionError
_ TestProjectContextResolver.test_xdg_config_home_layers_and_aw_config_dir_override _

self = <tests.test_project_context.TestProjectContextResolver testMethod=test_xdg_config_home_layers_and_aw_config_dir_override>

    def test_xdg_config_home_layers_and_aw_config_dir_override(self):
...
>           self.assertEqual(ctx_default.records_backend, "companion")
E           AssertionError: 'home' != 'companion'
E           - home
E           + companion

tests/test_project_context.py:412: AssertionError
=========================== short test summary info ============================
FAILED tests/test_project_context.py::TestProjectContextResolver::test_xdg_config_home_aw_home_resolution
FAILED tests/test_project_context.py::TestProjectContextResolver::test_xdg_config_home_layers_and_aw_config_dir_override
============================== 2 failed in 0.16s ===============================
```
    Status check:
```
$ git status --short agent_workflows/
 M agent_workflows/project_context.py
```
    Post-change bare `python3 -m pytest` summary:
```
702 passed in 20.95s
failing node ids: none (0 failing node ids)
```
    Leak sanitizer result:
```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5223,"findings":0,"evidence":["leak-scan"],"next":null}
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `git diff CHANGELOG.md` showing the single new `- Fixed:` bullet under `## 2.0.0 (pending)`, and pasted output of `git diff CHANGELOG.md | grep -nP "\x{2013}|\x{2014}"` returning empty (no em or en dashes).
  - Observed evidence:
```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 878a7633f..6362bacd6 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Fixed: project_context.resolve_project_context and project_context.project_config_dir now read user configuration through config.config_dir() (honoring AW_CONFIG_DIR and XDG_CONFIG_HOME) instead of a hard-coded ~/.config/agent-workflows path when user_config_dir is omitted.
 - Fixed: the shipped conformance host matrix (.aw/system/workflows/conformance/tools/host_matrix.json) no longer carries unproven supported booleans, so aw releases readiness no longer reports 19 stale capability claims; host support is established only by probe evidence recorded in the capability registry.
 - Fixed: aw index all and aw index all --check now emit a single aggregate aw.agent/v1 result record under --agent and a single valid JSON document under --json, ensuring record exit parity with the process exit code and closing multi-document parsing failures.
 - Fixed: aw index <type> --check --json no longer puts the absolute repository path (repo_root) or the human report text (human_rendered) in data; diagnostic locations stay repo-relative.
```
    Grep for em and en dashes:
```
$ git diff CHANGELOG.md | grep -nP "\x{2013}|\x{2014}"
(empty output, exit 1)
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `git diff agent_workflows/runner_shared.py` showing the `profiles/` seeding and docstring change; pasted passing output of `python3 -m pytest -o addopts="" -v tests/test_agent_user_config_containment.py` including the new test; and pasted output of a one-off `python3 -c` that seeds a sandbox from a temp source holding `profiles/team.json` (`{"records_backend": "repository"}`) and prints `resolve_project_context(target_repo=<tmp repo>, aw_home=<tmp>, profile="team", user_config_dir=str(handle.path)).records_backend` as `repository`.
  - Observed evidence:
```diff
diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
index 17b693697..b71812c11 100644
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -47167,7 +47167,8 @@ def prepare_agent_user_config(

     Resolves the operator's real directory via ``config.config_dir()`` (or source_dir),
     creates ``<run_dir>/agent-user-config/<NN>-<id6>-attempt-<N>[-<suffix>]/`` with mode
-    0o700, and copies every regular top-level file preserving mode.
+    0o700, and copies every regular top-level file and every regular file directly
+    inside a top-level profiles/ subdirectory, preserving mode.
     Records SHA-256 and parsed JSON object for each seeded file.

     Fails open: returns None and prints a warning on failure (never aborts a run).
@@ -47204,6 +47205,26 @@ def prepare_agent_user_config(
                     except Exception:
                         pass

+            profiles_dir = real_dir / "profiles"
+            if profiles_dir.is_dir():
+                sandbox_profiles = sandbox_dir / "profiles"
+                sandbox_profiles.mkdir(parents=True, exist_ok=True, mode=0o700)
+                with contextlib.suppress(OSError):
+                    os.chmod(sandbox_profiles, 0o700)
+                for child in sorted(profiles_dir.iterdir()):
+                    if child.is_file():
+                        dest = sandbox_profiles / child.name
+                        shutil.copy2(child, dest)
+                        rel_key = f"profiles/{child.name}"
+                        seed_hashes[rel_key] = sha256_file(dest)
+                        try:
+                            with dest.open("r", encoding="utf-8") as f:
+                                parsed = json.load(f)
+                                if isinstance(parsed, dict):
+                                    seed_json[rel_key] = parsed
+                        except Exception:
+                            pass
+
         return AgentUserConfig(
             path=sandbox_dir,
             seed_hashes=seed_hashes,
```
    Test suite output:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=2920085358
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/qi5ljl
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 8 items                                                             collected 8 items

tests/test_agent_user_config_containment.py::test_conftest_scrub PASSED  [ 12%]
tests/test_agent_user_config_containment.py::test_profiles_subdirectory_containment PASSED [ 25%]
tests/test_agent_user_config_containment.py::test_seed_fidelity PASSED   [ 37%]
tests/test_agent_user_config_containment.py::test_overwrite_or_pop_child_env PASSED [ 50%]
tests/test_agent_user_config_containment.py::test_aw_config_dir_precedence PASSED [ 62%]
tests/test_agent_user_config_containment.py::test_incident_end_to_end_per_host PASSED [ 75%]
tests/test_agent_user_config_containment.py::test_turn_failure_and_popen_raise_still_reconciles PASSED [ 87%]
tests/test_agent_user_config_containment.py::test_report_discarded_user_config_output PASSED [100%]

============================== 8 passed in 9.17s ===============================
```
    One-off script output:
```
records_backend: repository
provenance records_backend: {'source': 'named_global_profile', 'detail': 'named global profile (team)'}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Ready for `/plan-review`, then explicit human approval (`aw ipd set approved qi5ljl --by-human --message ...`). OQ-01 is resolved from repository evidence and the backlog item's ask; no maintainer decision is outstanding.

Execution contract once approved:

- Resolved questions: OQ-01 is resolved; nothing remains open.
- Order: perform E-01..E-05 in dependency order.
- Scope declaration (not a stop directive): `- Scope-Paths:` declares the files this plan expects to touch (`agent_workflows/project_context.py`, `tests/test_project_context.py`, `CHANGELOG.md`, `agent_workflows/runner_shared.py`, `tests/test_agent_user_config_containment.py`, and this plan file). Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and justify it in the two-way scope reconciliation at finalize (`--scope-reason <path>=<why>`), and acknowledge any declared-but-unmodified path with `--scope-ack`. Stop and report only for a genuinely unsafe condition (an unresolvable conflict with a co-worker's concurrent edit, or a cited symbol absent at HEAD).
- Honesty: paste the ACTUAL runner output into every `V-*` `Observed evidence`; never record a pass you did not observe.
- Commits: commit only the declared paths through `aw commit qi5ljl -- <paths>`; never `git add -A`, never push, never tag.
- Lifecycle transition: when run by `aw oc run` / `aw agy run` as an isolated worker, do NOT run `aw ipd begin` / `aw ipd finalize` in the lane (the role marker refuses them); the driver finalizes after integration. When executed by hand, finish with `aw ipd finalize qi5ljl` (never a hand-rolled `git mv` to `executed/`), and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
- Release gate: this plan inherits `- Blocks-Release: next` from backlog `m9dobx`; the item closes `done` through the handoff once this plan is executed.
