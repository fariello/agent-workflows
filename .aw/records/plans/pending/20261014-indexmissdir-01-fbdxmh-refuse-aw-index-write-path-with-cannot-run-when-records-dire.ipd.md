# IPD: Refuse aw index write path with cannot-run when records directory is missing

- Date: 2026-10-14
- Kind: child
- Concern: `aw index plans`, `aw index prompts`, `aw index research`, and `aw index all` crash on the write path (without `--check`) when the resolved records directory does not exist on disk: `scan_plans`, `scan_prompts`, and `_scan_docs` return `([], [])`, after which `json_path.write_text(new_json, encoding="utf-8")` in `plans_index.run_index`, `prompts_index.run_index`, and `research_index.run_index` raises an unhandled `FileNotFoundError` with exit `1`, a Python traceback on `stderr`, and `0` bytes on `stdout` under `--agent` and `--json`, violating `docs/cli-output-contract.md` Section 11.4.
- Scope: Add `emit_index_missing_dir_refusal` in `agent_workflows/artifact_core.py` that emits a structured `cannot-run` (`exit: 2`, `kind: "error"`, `outcome: "cannot-run"`, `applied: False`, `verified: False`, `complete: False`) result across `--agent`, `--json`, human (`stderr`), and `quiet=True` callers, naming the RESOLVED (sanitized) directory and choosing its recovery advice from `project_context.nonsurveyable_root_refusal`; guard the write branch of `plans_index.run_index`, `prompts_index.run_index`, and `research_index.run_index` when `not <dir>.is_dir()`; add subprocess and in-process behavior tests in `tests/test_index_write_agent_records.py`; and record the fix in `CHANGELOG.md`. The `aw index all` single aggregate record is NOT in scope (owned by `7i4zba`).
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/plans_index.py, agent_workflows/prompts_index.py, agent_workflows/research_index.py, tests/test_index_write_agent_records.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: o6cbp7
- Blocks-Release: next
- Set: indexmissdir
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: fbdxmh
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review applied revisions
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity): created from backlog item `o6cbp7`.

## Goal

Prevent `aw index plans`, `aw index prompts`, `aw index research`, and `aw index all` from crashing with an unhandled `FileNotFoundError` traceback when the resolved records directory does not exist on disk, refusing instead at exit code `2` (`cannot-run`) with a schema-valid `aw.agent/v1` `kind: "error"` record under `--agent`, a structured `cannot-run` `CommandResult` under `--json`, a clear diagnostic on `stderr` in human mode, recovery advice that is TRUE for the case at hand (never `aw install .` when that would create a nested project), and zero directory creation in the repo or under `HOME`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Shared missing-directory refusal helper and index write-path guards

- [ ] E-01 In `agent_workflows/artifact_core.py`, add `emit_index_missing_dir_refusal(args: Any, repo_root: Path, index_dir: Path, *, target: str) -> int` immediately after `emit_index_write_result`, implemented exactly as Proposed change 1: (a) when `getattr(args, "quiet", False)` is truthy, return `2` and emit nothing; (b) compute `rel_dir` as `index_dir.relative_to(repo_root).as_posix()` when that succeeds, else `agent_schema.normalize_repo_path(index_dir)` (so a home-backend path renders as `.aw/projects/<slug>-<hash>/records/<type>` with no absolute or home prefix); (c) compute the recovery advice from `project_context.nonsurveyable_root_refusal(f"index {target}", repo_root, explicit_dir=bool(getattr(args, "dir", None)))`: when it reports `may_proceed is False`, reuse its `summary` (path-free) and its `next_action` (which is `aw install .` only when the git root has no AW project, and `None` for an explicit `--dir` inside a project); when it reports `may_proceed is True` (a real project root whose records tree is incomplete), use `next_actions=[NextAction("aw install .", "restore the missing records directories")]`; (d) in human mode write `f"error: aw index {target}: records directory {rel_dir} does not exist; nothing was written.\n"` followed by the refusal's `human_message` (non-root case) or `"Run 'aw install .' at the project root to restore it.\n"` (root case) to `ctx.stderr`, and return `2`; (e) in machine modes build the `CommandResult` of Proposed change 1 (`status="cannot-run"`, `exit_code=2`, `applied=False`, `verified=False`, `complete=False`, one `Diagnostic(rule="records-dir-missing", severity="error")` at `rel_dir`, `data={"target": target, "index_dir": rel_dir}`), and if `isinstance(getattr(args, "_index_result_sink", None), list)` append it and return `2`, else return `get_renderer(ctx).emit(result, ctx)`. Do NOT edit `aggregate_index_results` (owned by `7i4zba`; see Deferred).
  - Depends on: none
  - Expected outcome: `artifact_core.emit_index_missing_dir_refusal` returns `2` in all four audiences, writes nothing to `stdout` in human and `quiet=True` modes, and every emitted machine record passes `agent_schema.validate_agent_record` with no absolute or home-directory path in any field.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/plans_index.py` (`run_index`), `agent_workflows/prompts_index.py` (`run_index`), and `agent_workflows/research_index.py` (`run_index`), insert a missing-directory guard immediately after the `if getattr(args, "check", False):` block and before the `scan_plans` / `scan_prompts` / `_scan_docs` call: `if not plans_dir.is_dir(): return _core.emit_index_missing_dir_refusal(args, repo_root, plans_dir, target="plans")`, and the analogues with `prompts_dir` / `target="prompts"` and `research_root` / `target="research"`. Do NOT touch the `--check` branch, `_dirs`, `_roots`, or `prompts.prompts_root`, and add no `mkdir`.
  - Depends on: E-01
  - Expected outcome: `aw index <plans|prompts|research>` (without `--check`) on a missing resolved directory returns exit `2` through `emit_index_missing_dir_refusal` before any `write_text`; `--check` on the same tree keeps today's output (`outcome: "conforms"`, exit `0`, `check.stale-index-missing` info findings, measured at review).
  - Execution state: pending

### Task group 2: Subprocess and in-process behavior tests and changelog

- [ ] E-03 In `tests/test_index_write_agent_records.py`, add behavioral tests. Every subprocess test runs `run_cli(..., env_overrides=...)` with `HOME` set to a temp dir and `AW_HOME`, `XDG_CONFIG_HOME`, and `AW_CONFIG_DIR` removed from the child env (build the env with `tests.conformance_matrix._pinned_env` or pop them explicitly; `run_cli` otherwise inherits the parent's values), on a fresh `git init` temp repo, never the live tree. Cover: (a) BARE GIT REPO (no `.aw/`), for each verb in `VERBS`, `aw index <verb> --agent` exits `2`, `stderr` contains no `Traceback`, `stdout` is exactly one line that passes `agent_schema.validate_agent_record(rec) == []` with `kind == "error"`, `cmd == "index"`, `target == <verb>`, `outcome == "cannot-run"`, `exit == 2`, `verified is False`, `complete is False`, `applied is False`, `next == "aw install ."`, one `records-dir-missing` diagnostic, and no line containing the temp `HOME` or repo absolute path; and afterwards no new directory exists under the repo (outside `.git`) or under `HOME`; (b) PARTIAL TREE (the `o6cbp7` reproduction): only `.aw/records/plans/` created, then `aw index all --agent` exits `2` with no `Traceback` on `stderr`, every `stdout` line passes `validate_agent_record`, and the LAST line has `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`; assert only these properties so the test holds both before and after `7i4zba` lands (before it the stream is per-type lines; after it one aggregate line); (c) `--json` for each verb on a bare git repo: exit `2`, `json.loads(stdout)` succeeds with `status == "cannot-run"` and `exit_code == 2`, and `data["index_dir"]` is a relative path; human mode for each verb: exit `2`, `stdout == ""`, `stderr` names the records directory and `aw install`; (d) EXPLICIT `--dir` INSIDE A PROJECT: install a fixture project with `aw install . -y --no-interactive` (isolated `HOME`), create `sub/`, run `aw index plans --dir sub --agent` from the project root: exit `2`, no `Traceback`, `outcome == "cannot-run"`, and `next` is NOT `"aw install ."` (the refusal must not advise creating a nested project), and no `sub/.aw` is created; (e) in-process `quiet=True`: call each module's `run_index(argparse.Namespace(dir=<bare git repo>, check=False, agent=False, json=False, limit=None, quiet=True))` with `contextlib.redirect_stdout`/`redirect_stderr` and with `HOME`/`AW_HOME` patched to the temp dir, asserting the return value `2` and empty captured `stdout` and `stderr`.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_index_write_agent_records.py` passes with the new tests pinning (a) through (e) and every pre-existing test unchanged and green.
  - Execution state: pending

- [ ] E-04 Add ONE `- Fixed:` bullet to `CHANGELOG.md` under the current pending release heading (`## 2.0.0 (pending) ...`, beside the other `- Fixed:` bullets; the file has no `## [Unreleased]` or `### Fixed` section) stating that `aw index plans|prompts|research|all` now refuse with exit code `2` (`cannot-run`) and a structured record when the records directory does not exist, instead of crashing with a `FileNotFoundError` traceback; write it with no em or en dashes. Then run the verification commands named in V-04.
  - Depends on: E-03
  - Expected outcome: `CHANGELOG.md` carries the bullet with zero em/en dashes; the bare `python3 -m pytest` shows no failure that does not also fail on the base commit; `python3 -m agent_workflows check all --agent` shows no new rule id and no increased per-rule count versus the base commit (the live corpus already exits `1` at base, so exit `0` is NOT the bar).
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Fatal failure and `cannot-run` contract (`docs/cli-output-contract.md` Section 11.4 "Error States and No-Silent-Failure Rule")**: "Handlers MUST NEVER catch and swallow unexpected exceptions or return exit code `0` on fatal failure." A command that cannot run maps to exit `2`, `kind: "error"`, `outcome: "cannot-run"`, `verified: false`, `complete: false`, and a `next` recovery command. `CommandResult.to_agent_record` (`agent_workflows/result_types.py`, the `if is_error:` branch) forces `kind`, `verified`, and `complete` for any `exit_code == 2`, and keeps `outcome == "cannot-run"` only when `status == "cannot-run"`.
- **Write verbs fail loudly and locally; they do not climb or silently create (`lmyeas` OQ-01, `rlhmt9` F-05)**: `.aw/records/plans/executed/20260930-ci9kx2-02-lmyeas-decide-and-implement-explicit-dir-resolution-semantics-for-a.ipd.md` decides an explicit `--dir` never climbs, and `.aw/records/plans/executed/20261002-dirsilent-04-rlhmt9-split-the-shared-read-write-helpers-and-convert-the-remainin.ipd.md` F-05 records that a write verb should fail "AT A PATH THE OPERATOR CAN READ" and that nothing should enter the real records tree. A traceback is a loud failure but not a structured one; this plan keeps the loud-and-local property and adds the structure.
- **Existing refusal primitive (`project_context.nonsurveyable_root_refusal`, from `dirsilent` Order 01)**: returns `may_proceed`, a human message, a PATH-FREE machine `summary`, and a `next_action` that is `aw install .` only when the git root holds no AW project (`git_root_for_message`), and `None` for an explicit `--dir` inside a project. Used by `attention.run`, `specs`, `backlog`, `releases`, and `release_readiness`. Reusing it is what makes the recovery advice correct (PR-001).
- **`aw install` creates all three records directories**: measured at review, a non-interactive `aw install . -y --no-interactive` on a fresh git repo creates `.aw/records/{plans,prompts,research}`, after which `aw index all --agent` exits `0`. Re-running it after deleting one directory restores it (measured with `prompts`). So `aw install .` is the right advice at a project root or in a bare git repo.
- **`aw install .` is the WRONG advice inside a project (measured at review)**: running `aw install . -y --no-interactive` in `<project>/sub` exits `0` and creates a NESTED project (`sub/.aw`, `sub/.agents`, `sub/AGENTS.md`, `sub/.opencode`, ...). This is why the original fixed `next: "aw install ."` was a defect (PR-001).
- **Home-backend fallback (`plans_index._dirs`, `research_index._roots`)**: both resolve via `record_producers.resolve_record_path`, which in a repo with no `.aw/config/project.json` (or for a `--dir <subdir>`) returns `<aw_home>/projects/<slug>-<hash>/records/<type>`, and fall back to `<repo>/.aw/records/<type>` only when THAT exists. `prompts_index._dirs` uses `prompts.prompts_root`, which is always in-repo. Measured: in a bare git repo, `plans` and `research` resolve under `$HOME/.aw/projects/`, `prompts` under the repo. A `mkdir(parents=True)` would therefore pollute `$HOME/.aw/projects/` and permanently shadow a later in-repo tree; the refusal must create nothing.
- **Path sanitizing**: `agent_schema.normalize_repo_path` strips an absolute path to a relative tail (measured: `<HOME>/.aw/projects/x-abc123/records/plans` -> `.aw/projects/x-abc123/records/plans`), and `Diagnostic.to_dict` / `CommandResult.to_dict` redact home paths in `detail`, `fix`, and `summary`. `data` is an unredacted passthrough under `--json` (`docs/cli-output-contract.md` Section 6), so `data["index_dir"]` must be computed relative before it is stored.
- **Legacy write-sink static check (`record_producers.discover_legacy_write_sinks`)**: no new line in the four scoped modules may combine `.agents/` with a write marker. This plan adds no write at all.
- **Internal `quiet=True` callers of `run_index`**: thirteen in-package call sites (`artifact_adopt.py`, `artifact_rename.py` x4, `ipd_lifecycle._refresh_plans_index_fail_loud`, `plans_refs.py`, `research_cmd.py` x2, `research_refs.py`, `status_set.py` x2) pass `quiet=True`; every one runs after mutating an artifact inside the directory being indexed, so the directory exists and the new guard is unreachable for them. `ipd_lifecycle._refresh_plans_index_fail_loud` ignores the return value and then runs `check_drift`, so a `2` there would still surface as a fail-loud `RuntimeError`, never as silent success.
- **Suite invocation**: run the suite bare as `python3 -m pytest`; use `-o addopts=""` for a narrowed verbose run (`AGENTS.md`, repository development contract).

## Findings

| ID | Severity | Location | Finding |
| :--- | :--- | :--- | :--- |
| F-01 | high | `agent_workflows/prompts_index.py` (`run_index`), `agent_workflows/research_index.py` (`run_index`), `agent_workflows/plans_index.py` (`run_index`) | On the write branch all three `run_index` functions scan (returning `([], [])` for a missing directory) and then call `json_path.write_text(...)`, which raises `FileNotFoundError`. Re-measured at review at HEAD `182cb1818` on a fresh `git init` repo with isolated `HOME`: all of `index plans|prompts|research|all --agent` exit `1` with a traceback; `plans` and `research` name `$HOME/.aw/projects/<slug>-<hash>/records/<type>/INDEX.json`, `prompts` names `<repo>/.aw/records/prompts/INDEX.json`. |
| F-02 | high | `agent_workflows/cli.py` (`_run_noun_verb`) | `aw index all` loops `for t in types:`; with only `.aw/records/plans/` present (the `o6cbp7` scenario), measured at review: `plans` emits an `ok` record, then `prompts` crashes with a traceback, rc `1`. |
| F-03 | medium | `agent_workflows/plans_index.py` (`_dirs`), `agent_workflows/research_index.py` (`_roots`), `agent_workflows/artifact_core.py` (`emit_index_write_result`) | The resolved directory may sit under `<aw_home>/projects/...`. `emit_index_write_result` falls back to `index_dir.as_posix()` (absolute) when `relative_to` fails, which would leak through `data["index_dir"]` under `--json`. The refusal must normalize the path before storing it, and must name the directory it actually checked rather than a canonical one it did not. |
| F-04 | medium | `agent_workflows/project_context.py` (`nonsurveyable_root_refusal`) | The correct recovery advice depends on where the repo root sits: a bare git repo or an incomplete project root wants `aw install .`; an explicit `--dir` inside a project wants the project root, and `aw install .` there creates a nested project (measured at review). The existing primitive already makes this distinction. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/artifact_core.py` (`emit_index_missing_dir_refusal`)**, immediately after `emit_index_write_result`:
   ```python
   def emit_index_missing_dir_refusal(
       args: Any,
       repo_root: Path,
       index_dir: Path,
       *,
       target: str,
   ) -> int:
       """Refuse an index WRITE with exit 2 (cannot-run) when the resolved records dir is absent.

       Creates nothing: a mkdir here would write under $HOME/.aw/projects/ for a home-backend
       resolution and permanently shadow a later in-repo tree (plan fbdxmh). Recovery advice
       comes from project_context.nonsurveyable_root_refusal, so an explicit --dir inside a
       project is never told to run 'aw install .' (which would nest a new project there).
       """
       if getattr(args, "quiet", False):
           return 2
       from agent_workflows import agent_schema as _schema
       from agent_workflows.project_context import nonsurveyable_root_refusal
       from agent_workflows.renderers import get_renderer
       from agent_workflows.result_types import (
           CommandResult,
           Diagnostic,
           NextAction,
           select_output,
       )

       ctx = select_output(args)
       try:
           rel_dir = index_dir.relative_to(repo_root).as_posix()
       except ValueError:
           rel_dir = _schema.normalize_repo_path(index_dir)

       refusal = nonsurveyable_root_refusal(
           f"index {target}", repo_root, explicit_dir=bool(getattr(args, "dir", None))
       )
       if refusal.may_proceed:
           reason = "the project's records tree is incomplete"
           next_actions = [
               NextAction(command="aw install .", description="restore the missing records directories")
           ]
           human_tail = "Run 'aw install .' at the project root to restore it.\n"
       else:
           reason = refusal.summary or "no AW project root at this directory"
           next_actions = [
               NextAction(command=n.command, description=n.description)
               for n in refusal.next_actions
           ]
           human_tail = (refusal.human_message or "") + "\n"

       if ctx.is_human:
           ctx.stderr.write(
               f"error: aw index {target}: records directory {rel_dir} does not exist; "
               "nothing was written.\n"
           )
           ctx.stderr.write(human_tail)
           return 2

       result = CommandResult(
           command="index",
           target=target,
           status="cannot-run",
           exit_code=2,
           summary=f"refusing to write {target} index: records directory {rel_dir} does not exist ({reason})",
           applied=False,
           diagnostics=[
               Diagnostic(
                   location=rel_dir,
                   rule="records-dir-missing",
                   detail=f"records directory {rel_dir} does not exist; nothing was written",
                   severity="error",
                   fix=next_actions[0].command if next_actions else None,
               )
           ],
           next_actions=next_actions,
           data={"target": target, "index_dir": rel_dir},
           verified=False,
           complete=False,
       )
       sink = getattr(args, "_index_result_sink", None)
       if isinstance(sink, list):
           sink.append(result)
           return result.exit_code
       return get_renderer(ctx).emit(result, ctx)
   ```
   Notes for the executor: `ctx.stderr` is the human diagnostic stream (`docs/cli-output-contract.md` Section 7); the human message from `nonsurveyable_root_refusal` names absolute paths and is human-only by that primitive's documented contract ("only the human message names paths"); the machine `summary` is path-free apart from the normalized `rel_dir`.

2. **`run_index` guards** in `agent_workflows/plans_index.py`, `agent_workflows/prompts_index.py`, and `agent_workflows/research_index.py`, immediately after the `if getattr(args, "check", False):` block and before the scan:
   ```python
   if not plans_dir.is_dir():
       return _core.emit_index_missing_dir_refusal(args, repo_root, plans_dir, target="plans")
   ```
   with `prompts_dir` / `target="prompts"` and `research_root` / `target="research"` respectively.

3. **`tests/test_index_write_agent_records.py`**: the cases in E-03 (a) through (e).

4. **`CHANGELOG.md`**: one `- Fixed:` bullet under `## 2.0.0 (pending)`, per E-04.

### Invariant-to-test map

| Invariant | Pinned by |
| :--- | :--- |
| Missing dir on write exits `2`, no traceback, schema-valid `cannot-run` record | E-03 (a), (c) |
| Nothing is created in the repo or under `HOME` | E-03 (a), (d) |
| No absolute or home path in any machine field, including `--json` `data` | E-03 (a), (c) |
| `aw index all` on a partial tree no longer crashes; terminal record is `cannot-run` | E-03 (b) |
| Recovery advice never tells an in-project `--dir` to `aw install .` | E-03 (d) |
| `quiet=True` callers get `2` and no output | E-03 (e) |
| `--check` behavior unchanged | pre-existing `tests/test_index_check_agent_records.py` and `tests/test_nv_backend_args_climb.py`, run in V-04 |
| Existing write-path behavior unchanged when the dir exists | pre-existing tests in `tests/test_index_write_agent_records.py`, run in V-03 |

## Deferred / out of scope (with reason)

- **Single aggregate `aw.agent/v1` and `--json` record for `aw index all` (`hu2wka` / `7i4zba`)**: owned by sibling plan `7i4zba` (status `reviewed`). This plan does NOT edit `aggregate_index_results` or `cli._run_noun_verb`: an executor-side conditional edit of a function that may not exist yet makes the scope depend on run order. Instead `emit_index_missing_dir_refusal` honors `_index_result_sink`, so the refusal reaches the aggregate when `7i4zba` is present. One interaction is recorded for `7i4zba`'s executor: its `check=False` branch computes `status = "findings" if exit_code == 1 else "ok"`, so an aggregate with `exit_code == 2` will render `outcome: "error"` rather than `"cannot-run"` (verified at review: `CommandResult(status="ok", exit_code=2).to_agent_record()` gives `kind: "error"`, `outcome: "error"`, `verified: false`, `complete: false`). That is contract-legal under Section 11.4 (`"cannot-run"` or `"error"`), so it is not a defect of either plan, and E-03 (b) asserts only properties that hold in both orders.
  - Carrier: 7i4zba
- **Creating the directory and writing an empty index**: decided against in OQ-01. No carrier needed: a settled decision.
  - Carrier-Declined: decided against in OQ-01 as settled decision

## Scope check

- Over-scope: none. (The original E-01(e) conditional edit of `aggregate_index_results` was removed at review, PR-005.)
- Under-scope: none after review (PR-001 recovery advice, PR-004 environment isolation, PR-006 nested-dir test added).

## Required tests / validation

- New behavior tests in `tests/test_index_write_agent_records.py` per E-03 (a) through (e).
- Pre-existing `tests/test_index_write_agent_records.py`, `tests/test_index_check_agent_records.py`, and `tests/test_nv_backend_args_climb.py` stay green.
- Full suite (bare `python3 -m pytest`) and `python3 -m agent_workflows check all --agent`, each compared against the base commit.

## Spec / documentation sync

- N/A with reason: `docs/cli-output-contract.md` Section 11.4 already specifies exit `2` (`cannot-run`) with a `kind: "error"` record and a `next` recovery command for a command that cannot run. No spec governs `aw index`'s missing-directory behavior, so no `.spec.md` is touched. Only `CHANGELOG.md` gets an entry.

## Open questions

### OQ-01: When the target records directory does not exist on an `aw index <plans|prompts|research>` write invocation, should `run_index` create the directory (`mkdir`) and write an empty index, or refuse with exit code `2` (`cannot-run`)?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence in favor of **refusing with exit code `2` (`cannot-run`)**: (1) `aw install` already creates all three records directories (measured at review on a fresh git repo, and it restores a deleted one), so a missing directory means an uninitialized repo, an explicit `--dir` that is not the project root, or a damaged tree; (2) in a repo without `.aw/config/project.json`, or for `--dir <subdir>`, `plans_index._dirs` and `research_index._roots` resolve under `$HOME/.aw/projects/<slug>-<hash>/records/<type>` (measured at review), so a `mkdir` would pollute `$HOME/.aw/projects/` and permanently shadow any in-repo tree created later, because the repo-local fallback is gated on the home path not existing; and (3) refusing matches `docs/cli-output-contract.md` Section 11.4 and Set `dirsilent` (`lmyeas` OQ-01, `rlhmt9` F-05). Review amendment (PR-001): the recovery `next` is derived from `project_context.nonsurveyable_root_refusal` rather than fixed to `aw install .`, because `aw install .` inside a project subdirectory creates a nested project (measured at review).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/artifact_core.py` showing `emit_index_missing_dir_refusal` with the `quiet` early return, the relative/normalized `rel_dir`, the `nonsurveyable_root_refusal` call and both advice branches, the human `ctx.stderr` write, the `CommandResult` fields named in E-01(e), and the `_index_result_sink` branch; PLUS pasted output of a `python3 -c` call that invokes `emit_index_missing_dir_refusal` with `argparse.Namespace(agent=True, dir=None)` and a `repo_root` that is a bare `git init` temp dir and `index_dir` under a temp `HOME` (`<home>/.aw/projects/x-abc123/records/plans`), with `stdout` captured, showing the return value `2`, the emitted line, `agent_schema.validate_agent_record(json.loads(line)) == []`, `next == "aw install ."`, and that the line contains neither the temp `HOME` nor the repo absolute path. (Reachable: the call drives E-01's function directly.)
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/plans_index.py agent_workflows/prompts_index.py agent_workflows/research_index.py` showing the guard placed after the `--check` block and before the scan in all three `run_index` functions, with no `mkdir` added; PLUS pasted stdout, stderr, and return code of `python3 -m agent_workflows index prompts --agent` and `python3 -m agent_workflows index prompts --check --agent` run in a fresh `git init` temp repo with isolated `HOME` and `AW_HOME`/`XDG_CONFIG_HOME`/`AW_CONFIG_DIR` unset, showing rc `2` with a `cannot-run` line and no traceback for the write, and rc `0` with `outcome: "conforms"` for `--check`. (Reachable: the dispatch path is `cli._run_noun_verb` -> `prompts_index.run_index`, guarded by E-02.)
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_index_write_agent_records.py` showing every test passing, with the new tests visibly covering E-03 (a) bare-repo `--agent` per verb with no-creation check, (b) partial-tree `aw index all --agent`, (c) `--json` and human per verb, (d) explicit `--dir` inside a project with `next != "aw install ."` and no `sub/.aw`, and (e) `quiet=True` per module. Test names are non-binding pointers; the evidence is the behaviors pinned.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff CHANGELOG.md` showing the one new `- Fixed:` bullet under `## 2.0.0 (pending)`, plus `grep -nP '[\x{2013}\x{2014}]'` over the added line returning nothing; pasted output of `python3 -m pytest -o addopts="" tests/test_index_check_agent_records.py tests/test_nv_backend_args_climb.py` passing; pasted summary line of the bare `python3 -m pytest`, with any failure shown to fail identically on the base commit; and the per-rule error/warning counts of `python3 -m agent_workflows check all --agent --verbose` on the base commit and after the change, showing no new rule id and no increased count.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it. Start with `aw ipd begin fbdxmh`. Commit ONLY the `- Scope-Paths:`, through `aw commit fbdxmh -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set with `git diff --cached --name-only` before committing. Every fixture run uses a temp repo with isolated `HOME` and with `AW_HOME`, `XDG_CONFIG_HOME`, and `AW_CONFIG_DIR` unset, never the live tree, because `aw index` writes index files and the home backend writes under `HOME`.

DO NOT WIDEN. Do not change `--check` behavior, `_dirs` / `_roots` / `prompts.prompts_root` resolution, `cli._run_noun_verb`, `aggregate_index_results` (owned by `7i4zba`), or `project_context.nonsurveyable_root_refusal`, and add no `mkdir`. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. Execution requires explicit human approval (`aw ipd set approved fbdxmh`). On completion every `V-*` carries pasted evidence and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize fbdxmh`. Never hand-roll the move or `git mv` the plan. This plan inherits `- Blocks-Release: next` from `o6cbp7`.
