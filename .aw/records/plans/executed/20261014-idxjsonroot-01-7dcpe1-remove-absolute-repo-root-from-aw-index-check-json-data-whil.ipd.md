# IPD: Remove absolute repo_root from aw index --check --json data while preserving diagnostic path relativization

- Date: 2026-10-14
- Kind: child
- Concern: aw index <type> --check --json machine-output leak posture and diagnostic path relativization
- Scope: Add an out-of-band repo_root attribute on CommandResult so Diagnostic.to_dict, Change.to_dict, Evidence.to_dict, and HumanRenderer resolve repo_root without requiring data["repo_root"]; remove "repo_root" and non-human "human_rendered" from emit_index_check_result data while normalizing drift diagnostic locations against repo_root; pass repo_root out of band on emit_index_write_result without changing its data keys.
- Scope-Paths: agent_workflows/result_types.py, agent_workflows/renderers.py, agent_workflows/artifact_core.py, tests/test_index_check_agent_records.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- From-Backlog: aavf6a
- Blocks-Release: next
- Work-Kind: bug
- Priority: low
- Set: idxjsonroot
- Order: 1
- Highest E allocated: 04
- Author: Antigravity Agent
- Id: 7dcpe1

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 7dcpe1 verified (set idxjsonroot, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review applied revisions
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity Agent): created.

## Goal

Eliminate the raw absolute `repo_root` path (and non-human `human_rendered` drift text containing raw absolute `dangling-citation` file paths) from `aw index <type> --check --json` (`data` payload in `artifact_core.emit_index_check_result`), while preserving repo-relative diagnostic, change, and evidence path normalization in both `--json` and `--agent` modes via an out-of-band `CommandResult.repo_root` attribute. `artifact_core.emit_index_write_result` already omits `repo_root` from `data`; it only gains the out-of-band `repo_root` so its diagnostics relativize against the real root.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Out-of-band repo_root on CommandResult and index check/write emission cleanup

- [x] E-01 Add an optional out-of-band `repo_root: Optional[Union[str, Path]] = None` field as the LAST field of `result_types.CommandResult` (after `schema_version`, so no existing positional order shifts) and resolve `repo_root = self.repo_root if self.repo_root is not None else self.data.get("repo_root")` in `result_types.CommandResult.to_dict`, `result_types.CommandResult.to_agent_record`, and `renderers.HumanRenderer.render`, without serializing `repo_root` as a top-level or `data` key in `CommandResult.to_dict`.
  - Depends on: none
  - Expected outcome: `CommandResult(command="index", repo_root=root, diagnostics=[...], data={"target": "plans"})` relativizes `Diagnostic`, `Change`, and `Evidence` paths against `root` in both `to_dict()` and `to_agent_record()`, while `to_dict()["data"]` contains only `{"target": "plans"}` and no top-level `repo_root` key exists; callers that still pass `data["repo_root"]` (for example `cli.py` and `artifact_adopt.py` producers) remain backward-compatible.
  - Execution state: performed

- [x] E-02 Update `artifact_core.emit_index_check_result` to pass `target=target` and `repo_root=repo_root` on `CommandResult`, normalize each drift `Diagnostic.location` via `agent_schema.normalize_repo_path(d.location, repo_root)` (local import, as the module already imports lazily), remove `"repo_root"` from `data`, and include `"human_rendered"` in `data` only when `ctx.is_human`; update `artifact_core.emit_index_write_result` ONLY to pass `repo_root=repo_root` on `CommandResult` and normalize its `Diagnostic.location` the same way, leaving its existing `data` dict (`target`, `count`, `noun`, `json_changed`, `md_changed`, `index_dir`) unchanged.
  - Depends on: E-01
  - Expected outcome: `aw index <plans|prompts|research> --check --json` emits `data == {"target": "<type>"}` with no `"repo_root"` or `"human_rendered"` key and no absolute checkout path anywhere in the JSON document; `--check --agent` and human mode keep their existing output (human stdout byte-identical, exit codes unchanged); `aw index <type> --json` (write path) keeps every existing `data` key.
  - Execution state: performed

### Task group 2: Regression tests and changelog

- [x] E-03 Add behavior tests to `tests/test_index_check_agent_records.py` (a `unittest.TestCase` module; reuse its `IndexCheckSubprocessTests` `self.root` fixture, `_create_fixture_repo`, `VERBS`, and `tests.conformance_matrix.run_cli`, not pytest fixtures) covering (a) `CommandResult.repo_root` out-of-band relativization in-process, (b) `--check --json` `data` shape and leak-free stdout across `VERBS` for `clean`, `missing`, and `stale` fixtures, and (c) a `dangling-citation` finding in root-level `DECISIONS.md` (outside every `agent_schema.normalize_repo_path` known marker) under both `--json` and `--agent --verbose`.
  - Depends on: E-02
  - Expected outcome: the new tests pass and assert `"repo_root" not in doc["data"]`, `"human_rendered" not in doc["data"]`, `doc["data"]["target"] == verb`, that a `dangling-citation` diagnostic has `location == "DECISIONS.md:1"` on both surfaces, that the process exit code is UNCHANGED by the `info`-severity dangling finding (`0` on an otherwise clean fixture), and that neither `str(self.root)` nor `Path.home().as_posix()` appears in stdout; the existing human-mode tests in the module still pass unmodified.
  - Execution state: performed

- [x] E-04 Add one `- Fixed:` bullet under `## 2.0.0 (pending)` in `CHANGELOG.md` (with no em or en dashes), then run the targeted test modules, the full suite, and `aw sanitize --agent`.
  - Depends on: E-03
  - Expected outcome: `CHANGELOG.md` documents the fix without em/en dashes; the targeted modules pass; the full suite shows no failure that is absent at the base commit (re-derive the base result at execution time); `aw sanitize --agent` reports `"outcome":"clean"`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Normative machine-output leak contract: `docs/cli-output-contract.md` `## 4. The aw.agent/v1 JSONL Protocol and Closed Record Kinds` > `### Protocol Invariants and Anti-Greenwashing Rules`, bullet `**Path Sanitization and Leak Posture**`:
  - Path-valued envelope fields (`target`, `location`, `path`, ...) on `--agent` and `--json` MUST be repo-relative and normalized.
  - The bullet exempts `data` from DOWNSTREAM redaction only: "The `data` exemption is an exemption from downstream redaction and not a licence for a producer to put an absolute path there: a command-specific payload must itself carry repo-relative text unless an approved spec requires otherwise". No spec requires `repo_root` here.
- `result_types.CommandResult.to_dict` and `result_types.CommandResult.to_agent_record` (`agent_workflows/result_types.py`):
  - Both resolve `repo_root = self.data.get("repo_root")` and forward it to `Diagnostic.to_dict(repo_root)`, `Change.to_dict(repo_root)`, and `Evidence.to_dict(repo_root)`.
  - `CommandResult.to_dict` then emits `"data": dict(self.data)` verbatim, which `renderers.JsonRenderer.render` serializes via `json.dumps(result.to_dict(), indent=2)`.
  - `CommandResult.to_agent_record` never copies `self.data` wholesale into the record (it reads selected keys such as `target`, `applied`, `checked`, `findings`), which is why `--agent` does not leak `data["repo_root"]` or `data["human_rendered"]` while `--json` leaks both.
- Why `repo_root` must still reach `agent_schema.normalize_repo_path`:
  - `plans_index.check_drift` (`_core.Drift(f"{d.file}:{d.line}", "dangling-citation", f"PLAN-{d.id6}")`) and `research_index.check_drift` (`Drift(f"{d.file}:{d.line}", "dangling-citation", f"id6 {d.id6}")`) build locations from `artifact_core.find_dangling_citations`, whose files come from `artifact_core.iter_scan_files` as absolute `repo_root / rel` paths. `prompts_index.check_drift` emits no dangling-citation drift.
  - `artifact_core.SCAN_ROOTS` includes root-level files (`"DECISIONS.md"`, `"README.md"`, `"ARCHITECTURE.md"`) outside `.aw/`.
  - In `agent_schema.normalize_repo_path`, when `repo_root` is `None`, the fallback strips to the first path component in `known_markers = (".aw", ".agents", "agent_workflows", "tests", "docs", "plans", "records")`, else keeps the last 2 components. Measured at review: for a root-level `DECISIONS.md:1` it returns `<repo-dir-name>/DECISIONS.md:1`, and inside a lane worktree it returns `.aw/worktrees/<lane>/DECISIONS.md:1`; with `repo_root` it returns `DECISIONS.md:1`.
- `dangling-citation` severity is `info` (`check_engine.RULE_REGISTRY` entry `"dangling-citation": RuleSpec("info", ...)`), and `artifact_core.drift_exit_code` exempts only `info`, so a dangling citation alone exits `0`. Measured at review on a clean fixture plus `DECISIONS.md` citing `PLAN-zzzzzz`/`RSCH-zzzzzz`: `index plans --check --json` and `index research --check --json` both exit 0, each with one `dangling-citation` diagnostic at `DECISIONS.md:1`, `data` keys `['human_rendered', 'repo_root', 'target']`, and the fixture root present in stdout; the `--agent --verbose` runs exit 0 with no fixture root in stdout.
- `artifact_core.emit_index_write_result` already builds `data = {"target", "count", "noun", "json_changed", "md_changed", "index_dir"}` with no `repo_root`, and `tests/test_index_write_agent_records.py` (`_run_json_verb_check`) asserts `json_changed`/`md_changed` and `assertNotIn("repo_root", data)`.
- Sibling plan coordination (`7i4zba`, `.aw/records/plans/pending/20261014-indexallexit-01-7i4zba-emit-one-aggregate-aw-agent-v1-record-for-aw-index-all-acros.ipd.md`, `Status: reviewed`):
  - Its `## Deferred / out of scope` assigns single-type `data["repo_root"]`/`human_rendered` to `aavf6a` (this plan), and its gate says DO NOT WIDEN into them.
  - Its E-01 ALSO normalizes `d.location` via `agent_schema.normalize_repo_path(d.location, repo_root)` in both helpers and sets `target=target` on the check helper's `CommandResult`. Those edits are identical in effect to this plan's E-02, so whichever plan lands second finds them already present and keeps them (idempotent); the merge conflict, if any, is textual on the same lines and resolves to one copy.
- Prose convention (`AGENTS.md` execution contract): user-facing prose in `CHANGELOG.md` must contain zero em dashes or en dashes. Recent fixes use `- Fixed:` bullets directly under `## 2.0.0 (pending)` (for example `CHANGELOG.md` "Fixed: aw rename and aw group now also rewrite citations").
- Test suite (`AGENTS.md` repository development contract): run bare `python3 -m pytest`; use `-o addopts=""` only when per-test counts are needed from a narrowed run.

## Findings

| # | Location (symbol / anchor) | Observation | Impact |
|---|---|---|---|
| F-01 | `agent_workflows/artifact_core.py` (`emit_index_check_result`, `"repo_root": str(repo_root)`) | `emit_index_check_result` constructs `CommandResult` with `data={"target": target, "repo_root": str(repo_root), "human_rendered": human_rendered}` and does not set `target=target` on `CommandResult`. | Under `aw index <type> --check --json`, `JsonRenderer.render` serializes `result.to_dict()`, emitting the caller's raw absolute checkout path in `data["repo_root"]` against the `docs/cli-output-contract.md` leak-posture bullet. |
| F-02 | `agent_workflows/artifact_core.py` (`emit_index_check_result`, `"human_rendered": human_rendered`) | `human_rendered = "".join(f"{d.location}: {d.rule}: {d.detail}\n" for d in drift)` uses raw `d.location` strings and is placed in `data` unconditionally. Measured at authoring on this checkout, `index research --check --json` `data["human_rendered"]` carried several hundred lines starting with the absolute checkout path (the count is live and drifts; it is context, not a bar). | Removing only `"repo_root"` would still leak absolute paths through `data["human_rendered"]`. `human_rendered` is consumed only by `renderers.HumanRenderer.render` (`if "human_rendered" in result.data:`). |
| F-03 | `agent_workflows/artifact_core.py` (`emit_index_write_result`, `diagnostics = [Diagnostic(location=d.location, ...)]`) | The write helper's `data` already omits `repo_root`, so its diagnostics have no root to relativize against and fall back to the `normalize_repo_path` tail heuristic. | Passing `repo_root=repo_root` out of band keeps both helpers consistent and makes write-path diagnostic locations exactly repo-relative, without touching its `data` contract. |
| F-04 | `agent_workflows/result_types.py` (`CommandResult.to_dict`, `CommandResult.to_agent_record`) and `agent_workflows/renderers.py` (`HumanRenderer.render`, `Path(result.data.get("repo_root") or ".")`) | `CommandResult` has no dedicated `repo_root` field; all three read `data.get("repo_root")`. | A `repo_root` field with a `data` fallback supplies an out-of-band channel without breaking the other producers that still pass `data["repo_root"]`. |

## Proposed changes (ordered, validatable)

1. **Out-of-band `repo_root` on `CommandResult` (`agent_workflows/result_types.py`, `agent_workflows/renderers.py`), E-01**:
   - In `result_types.CommandResult`, append dataclass attribute `repo_root: Optional[Union[str, Path]] = None` after `schema_version` (the last field), so no positional construction shifts.
   - In `CommandResult.to_dict` and `CommandResult.to_agent_record`, resolve `repo_root = self.repo_root if self.repo_root is not None else self.data.get("repo_root")`. Do not add `"repo_root"` to the returned dictionary.
   - In `renderers.HumanRenderer.render`, resolve `repo_root = Path(result.repo_root if result.repo_root is not None else (result.data.get("repo_root") or "."))`.

2. **Index check/write `CommandResult` construction (`agent_workflows/artifact_core.py`), E-02**:
   - In `emit_index_check_result`:
     - Build each `Diagnostic` with `location=_schema.normalize_repo_path(d.location, repo_root)` (`from agent_workflows import agent_schema as _schema` beside the existing local imports).
     - Keep `human_rendered` construction unchanged (human stdout stays byte-identical) and populate:
       ```python
       data: Dict[str, Any] = {"target": target}
       if ctx.is_human:
           data["human_rendered"] = human_rendered
       ```
       (add `Dict` to the `typing` import or annotate inline; the module currently imports `Any, Callable, List, NamedTuple, Optional, Tuple`). Delete the now-stale `repo_root must be a str` comment.
     - Construct `CommandResult` with `target=target`, `repo_root=repo_root`, and `data=data`.
   - In `emit_index_write_result`: pass `repo_root=repo_root` on `CommandResult` and normalize `Diagnostic.location` as above. Do NOT change its `data` dict.

3. **Regression tests (`tests/test_index_check_agent_records.py`), E-03**:
   - In-process unit test (new `unittest.TestCase` method or class): `CommandResult(command="index", target="plans", repo_root=root, diagnostics=[Diagnostic(location=f"{root / 'DECISIONS.md'}:1", rule="dangling-citation", detail="PLAN-zzzzzz", severity="info")], data={"target": "plans"})` asserting `"repo_root" not in res.to_dict()`, `res.to_dict()["data"] == {"target": "plans"}`, and `location == "DECISIONS.md:1"` in both `res.to_dict()["diagnostics"][0]` and `res.to_agent_record()["diagnostics"][0]`. Use a temp directory whose path has no `known_markers` component so the assertion distinguishes real relativization from the tail heuristic (the heuristic would yield `<tmpdir-name>/DECISIONS.md:1`).
   - Subprocess test across `VERBS` x `("clean", "missing", "stale")` (`subTest`): `doc = json.loads(res.stdout)`; `"repo_root" not in doc["data"]`; `"human_rendered" not in doc["data"]`; `doc["data"]["target"] == verb`; `str(self.root) not in res.stdout`; `Path.home().as_posix() not in res.stdout`; return code equals the value the existing `test_json_*_fixture_emits_json_document` tests already assert for that mode.
   - Subprocess test for `verb in ("plans", "research")` on `_create_fixture_repo(self.root, mode="clean")` plus `self.root / "DECISIONS.md"` containing `See PLAN-zzzzzz and RSCH-zzzzzz.\n`:
     - `--check --json`: `res.returncode == 0`, `"repo_root"`/`"human_rendered"` absent from `doc["data"]`, `str(self.root) not in res.stdout`, and a diagnostic with `rule == "dangling-citation"` and `location == "DECISIONS.md:1"`.
     - `--check --agent --verbose`: `res.returncode == 0`, `str(self.root) not in res.stdout`, `agent_schema.validate_agent_record(rec) == []`, `rec["exit"] == res.returncode`, and the same `dangling-citation` diagnostic at `DECISIONS.md:1`.

4. **Changelog and verification (`CHANGELOG.md`), E-04**:
   - Add one `- Fixed:` bullet under `## 2.0.0 (pending)`: `aw index <type> --check --json` no longer puts the absolute repository path (`repo_root`) or the human report text (`human_rendered`) in `data`; diagnostic locations stay repo-relative. Zero em or en dashes.
   - Run `python3 -m pytest tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_json_surface_leak_posture.py`, the bare full suite `python3 -m pytest`, and `python3 -m agent_workflows sanitize --agent`.

## Invariant-to-test map

| Invariant | Pinned by |
|---|---|
| `--check --json` `data` carries no absolute path | E-03 subprocess `data`-shape test (all verbs x modes) |
| Diagnostic locations stay repo-relative on both machine surfaces without `data["repo_root"]` | E-03 in-process unit test; E-03 `DECISIONS.md:1` subprocess test |
| Human `--check` stdout byte-identical | existing `test_human_clean_output_per_verb`, `test_human_drifting_output_per_verb`, `test_human_stale_output_per_verb` |
| `--agent` record schema-valid, exit parity | existing `test_agent_*_fixture_emits_valid_record`; E-03 `--agent --verbose` assertions |
| Write-path `data` keys and no-leak posture unchanged | existing `tests/test_index_write_agent_records.py` (`_run_json_verb_check`, `_assert_no_leaks`, `test_refusal_research_invalid_frontmatter`) |
| Other `data["repo_root"]` producers still relativize | existing `tests/test_json_surface_leak_posture.py` and the full suite |

## Deferred / out of scope (with reason)

- Migrating other producers (`agent_workflows/cli.py`, `agent_workflows/artifact_adopt.py`) from `data["repo_root"]` to `CommandResult.repo_root`: out of scope for backlog item `aavf6a`, which scopes `aw index <type> --check --json`. The `data` fallback keeps them working unchanged.
  - Carrier-Declined: out of scope for aavf6a; data fallback keeps callers working
- Emitting one aggregate `CommandResult` for `aw index all [--check]`: owned by sibling plan `7i4zba` (backlog `hu2wka`).
  - Carrier: 7i4zba

## Scope check

- Over-scope: none.
- Under-scope: none; both leak sources in `emit_index_check_result` (`data["repo_root"]` and `data["human_rendered"]`) are removed, and out-of-band `CommandResult.repo_root` keeps `Diagnostic`, `Change`, and `Evidence` locations relativized for both index helpers.

## Required tests / validation

- Targeted: `python3 -m pytest tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_json_surface_leak_posture.py`
- Full suite: bare `python3 -m pytest`, compared against the base commit.
- Direct CLI: `python3 -m agent_workflows index plans --check --json` and `python3 -m agent_workflows index research --check --json` on the live tree (read-only) showing `data` keys `["target"]` and zero occurrences of the checkout path in stdout.
- Leak-sanitizer: `python3 -m agent_workflows sanitize --agent`

## Spec / documentation sync

- `CHANGELOG.md`: add a `- Fixed:` entry under `## 2.0.0 (pending)`.
- `docs/cli-output-contract.md`: N/A with reason. The `**Path Sanitization and Leak Posture**` bullet already forbids a producer from putting an absolute path in `data`; this plan brings `emit_index_check_result` into compliance. The new `CommandResult.repo_root` attribute is never serialized, so the Section 2 field list (which documents serialized facts) does not change.
- No `.spec.md` is touched.

## Open questions

### OQ-01: Should `human_rendered` also be omitted from `emit_index_check_result` `data` when `not ctx.is_human`?

- Blocking: no
- Status: resolved
- Owner: Antigravity Agent
- Resolution or deferral rationale: Resolved from repository evidence (`agent_workflows/artifact_core.py` symbol `emit_index_check_result`, `agent_workflows/renderers.py` symbol `HumanRenderer.render`, and sibling plan `7i4zba`). `human_rendered` is only read by `HumanRenderer.render` (`if "human_rendered" in result.data:`). When `dangling-citation` findings exist it contains raw absolute paths, so leaving it in `data` under `--json` would keep leaking. Including it only when `ctx.is_human` preserves human mode byte-for-byte while making `--check --json` free of absolute paths.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/result_types.py agent_workflows/renderers.py` showing `repo_root: Optional[Union[str, Path]] = None` as the last `CommandResult` field and the `self.repo_root if self.repo_root is not None else self.data.get("repo_root")` fallback in `CommandResult.to_dict`, `CommandResult.to_agent_record`, and `HumanRenderer.render`; PLUS pasted output of a `python3 -c` call building `CommandResult(command="index", repo_root=<tmpdir>, diagnostics=[Diagnostic(location="<tmpdir>/DECISIONS.md:1", rule="dangling-citation", detail="x", severity="info")], data={"target": "plans"})` and printing `sorted(r.to_dict())`, `r.to_dict()["data"]`, and the diagnostic `location` from both `to_dict()` and `to_agent_record()` (path: `CommandResult.to_dict` / `CommandResult.to_agent_record`, created by E-01), showing no `repo_root` key and `DECISIONS.md:1` twice.
  - Observed evidence:
```
$ git diff agent_workflows/result_types.py agent_workflows/renderers.py
diff --git a/agent_workflows/renderers.py b/agent_workflows/renderers.py
index 03cdc370e..8f2360517 100644
--- a/agent_workflows/renderers.py
+++ b/agent_workflows/renderers.py
@@ -97,7 +97,11 @@ class HumanRenderer(BaseRenderer):
             from agent_workflows import doctor as _doctor
             from pathlib import Path

-            repo_root = Path(result.data.get("repo_root") or ".")
+            repo_root = Path(
+                result.repo_root
+                if result.repo_root is not None
+                else (result.data.get("repo_root") or ".")
+            )
             groups: dict = {}
             for d in result.diagnostics:
                 drift_obj = d.to_drift() if hasattr(d, "to_drift") else d
diff --git a/agent_workflows/result_types.py b/agent_workflows/result_types.py
index 0e1c5f391..3f13b298b 100644
--- a/agent_workflows/result_types.py
+++ b/agent_workflows/result_types.py
@@ -324,6 +324,7 @@ class CommandResult:
     applied: Optional[bool] = None
     target: Optional[str] = None
     schema_version: str = _schema.SCHEMA_VERSION
+    repo_root: Optional[Union[str, Path]] = None

     @property
     def has_findings(self) -> bool:
@@ -334,7 +335,11 @@ class CommandResult:
         return self.exit_code == 2

     def to_dict(self) -> Dict[str, Any]:
-        repo_root = self.data.get("repo_root")
+        repo_root = (
+            self.repo_root
+            if self.repo_root is not None
+            else self.data.get("repo_root")
+        )
         return {
             "schema": self.schema_version,
             "command": self.command,
@@ -354,7 +359,11 @@ class CommandResult:
         self, context: Optional[OutputContext] = None
     ) -> Dict[str, Any]:
         """Convert into canonical aw.agent/v1 compact record structure (Order 03)."""
-        repo_root = self.data.get("repo_root")
+        repo_root = (
+            self.repo_root
+            if self.repo_root is not None
+            else self.data.get("repo_root")
+        )
         is_verbose = context.verbose if context is not None else False

         # Resolve outcome & enforce anti-greenwashing invariants

$ python3 -c 'import tempfile; from pathlib import Path; from agent_workflows.result_types import CommandResult, Diagnostic; td = tempfile.TemporaryDirectory(prefix="norootmarker_"); root = Path(td.name); dec = root / "DECISIONS.md"; r = CommandResult(command="index", repo_root=root, diagnostics=[Diagnostic(location=f"{dec}:1", rule="dangling-citation", detail="x", severity="info")], data={"target": "plans"}); print(sorted(r.to_dict().keys())); print(r.to_dict()["data"]); print(r.to_dict()["diagnostics"][0]["location"]); print(r.to_agent_record()["diagnostics"][0]["location"]); td.cleanup()'
['changes', 'command', 'complete', 'data', 'diagnostics', 'evidence', 'exit_code', 'next_actions', 'schema', 'status', 'summary', 'verified']
{'target': 'plans'}
DECISIONS.md:1
DECISIONS.md:1
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/artifact_core.py` showing the check helper's `data` reduced to `target` (plus `human_rendered` under `ctx.is_human`), `target=target` and `repo_root=repo_root` on both helpers' `CommandResult`, normalized `Diagnostic.location`, and the write helper's `data` dict unchanged; PLUS pasted output, from the live tree, of `python3 -c 'import json, os, subprocess; root = os.getcwd(); [print(v, (lambda p: (p.returncode, sorted(json.loads(p.stdout)["data"]), root in p.stdout))(subprocess.run(["python3", "-m", "agent_workflows", "index", v, "--check", "--json"], capture_output=True, text=True))) for v in ("plans", "prompts", "research")]'` (path: `artifact_core.emit_index_check_result` via `JsonRenderer.render`, created by E-02) showing `['target']` and `False` for every verb.
  - Observed evidence:
```
$ git diff agent_workflows/artifact_core.py
diff --git a/agent_workflows/artifact_core.py b/agent_workflows/artifact_core.py
index 53d16f6dd..e15d2dce0 100644
--- a/agent_workflows/artifact_core.py
+++ b/agent_workflows/artifact_core.py
@@ -29,7 +29,7 @@ import stat
 import subprocess
 import tempfile
 from pathlib import Path
-from typing import Any, Callable, List, NamedTuple, Optional, Tuple
+from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

 # --------------------------------------------------------------------------------------
 # Identity: the stable, greppable ``<id6>``
@@ -909,6 +909,7 @@ def emit_index_check_result(
     target: str = "",
 ) -> int:
     """Emit the typed CommandResult for an index --check invocation across agent, json, and human audiences."""
+    from agent_workflows import agent_schema as _schema
     from agent_workflows import check_engine as _ce
     from agent_workflows.renderers import get_renderer
     from agent_workflows.result_types import (
@@ -922,7 +923,7 @@ def emit_index_check_result(
     status = "conforms" if exit_code == 0 else "findings"
     diagnostics = [
         Diagnostic(
-            location=d.location,
+            location=_schema.normalize_repo_path(d.location, repo_root),
             rule=d.rule,
             detail=d.detail,
             severity=(_ce.enrich_drift(d).severity or "error"),
@@ -943,19 +944,19 @@ def emit_index_check_result(
         else f"{len(drift)} finding(s) detected across {target or 'index'}"
     )

+    data: Dict[str, Any] = {"target": target}
+    if ctx.is_human:
+        data["human_rendered"] = human_rendered

     result = CommandResult(
         command=command,
+        target=target,
         status=status,
         exit_code=exit_code,
         summary=summary,
         diagnostics=diagnostics,
-        data={
-            "target": target,
-            # repo_root must be a str, never a Path, so the --json serializer does not raise TypeError (PR-003, F-11)
-            "repo_root": str(repo_root),
-            # Preserves legacy human lines byte-exact through data["human_rendered"] (PR-002, F-10)
-            "human_rendered": human_rendered,
-        },
+        data=data,
+        repo_root=repo_root,
         verified=True,
         complete=True,
     )
@@ -979,6 +980,7 @@ def emit_index_write_result(
     refused: bool = False,
 ) -> int:
     """Emit the typed CommandResult for an index write invocation under --agent or --json."""
+    from agent_workflows import agent_schema as _schema
     from agent_workflows import check_engine as _ce
     from agent_workflows.renderers import get_renderer
     from agent_workflows.result_types import (
@@ -1018,7 +1020,7 @@ def emit_index_write_result(

     diagnostics = [
         Diagnostic(
-            location=d.location,
+            location=_schema.normalize_repo_path(d.location, repo_root),
             rule=d.rule,
             detail=d.detail,
             severity=(_ce.enrich_drift(d).severity or "error"),
@@ -1061,6 +1063,7 @@ def emit_index_write_result(
         changes=changes,
         diagnostics=diagnostics,
         data=data,
+        repo_root=repo_root,
         verified=True,
         complete=not refused,
     )

$ python3 -c 'import json, os, subprocess; root = os.getcwd(); [print(v, (lambda p: (p.returncode, sorted(json.loads(p.stdout)["data"]), root in p.stdout))(subprocess.run(["python3", "-m", "agent_workflows", "index", v, "--check", "--json"], capture_output=True, text=True))) for v in ("plans", "prompts", "research")]'
plans (0, ['target'], False)
prompts (0, ['target'], False)
research (1, ['target'], False)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted runner output of `python3 -m pytest -o addopts="" -v tests/test_index_check_agent_records.py` showing every test passing, with the new tests visibly covering the in-process out-of-band relativization, the `data`-shape and no-leak assertions across all verbs and modes, and the `DECISIONS.md:1` `dangling-citation` location on both `--json` and `--agent --verbose` with exit 0. Test names are non-binding pointers.
  - Observed evidence:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=567025868
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 12 items

tests/test_index_check_agent_records.py::CommandResultOutOfBandRelativizationTests::test_command_result_out_of_band_repo_root_relativization PASSED [  8%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_agent_stale_fixture_emits_valid_record PASSED [ 16%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_human_clean_output_per_verb PASSED [ 25%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_json_clean_fixture_emits_json_document PASSED [ 33%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_agent_missing_fixture_emits_valid_record PASSED [ 41%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_json_stale_fixture_emits_json_document PASSED [ 50%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_json_missing_fixture_emits_json_document PASSED [ 58%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_agent_clean_fixture_emits_valid_record PASSED [ 66%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_human_stale_output_per_verb PASSED [ 75%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_json_check_data_shape_and_no_leak_across_modes PASSED [ 83%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_json_and_agent_dangling_citation_in_root_decisions PASSED [ 91%]
tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_human_drifting_output_per_verb PASSED [100%]

============================= 12 passed in 16.20s ==============================
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `git diff CHANGELOG.md` showing the new `- Fixed:` bullet, plus pasted output of `grep -nP '[\x{2013}\x{2014}]' CHANGELOG.md` restricted to the added line showing no match; pasted runner output of `python3 -m pytest tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_json_surface_leak_posture.py` (all passing) and of the bare full suite `python3 -m pytest` with its summary line, any failure shown to also fail at the base commit; and pasted `python3 -m agent_workflows sanitize --agent` output with `"outcome":"clean"` and exit 0.
  - Observed evidence:
```
$ git diff CHANGELOG.md
diff --git a/CHANGELOG.md b/CHANGELOG.md
index be5b3fbac..28f1bdacb 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Fixed: aw index <type> --check --json no longer puts the absolute repository path (repo_root) or the human report text (human_rendered) in data; diagnostic locations stay repo-relative.
 - Fixed: aw rename and aw group now scan README.md files for citation rewrites while still skipping generated INDEX.md and STATUS.md manifests.
 - Fixed: aw pwatch, aw runners, and runner stream headers, statuslines, event prefixes, and run summaries now honor the color_depth pin and 16-color terminal detection, so none removes all ANSI color escapes from those surfaces and 16 uses basic 16-color ANSI codes instead of 256-color sequences.
 - Changed: the plans README and the IPD spec now recommend spelling a records entry in Scope-Paths as .aw/records/<type>/**/<filename> so it survives a status move, and the literal form remains valid.

$ sed -n '27p' CHANGELOG.md | grep -nP '[\x{2013}\x{2014}]'
(exit 1, no match)

$ python3 -m pytest tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_json_surface_leak_posture.py
40 passed in 7.60s

$ python3 -m pytest
702 passed in 25.33s

$ python3 -m agent_workflows sanitize --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5218,"findings":0,"evidence":["leak-scan"],"next":null}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it. Start with `aw ipd begin 7dcpe1`. Commit ONLY the `- Scope-Paths:`, through `aw commit 7dcpe1 -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set with `git diff --cached --name-only` before committing. Subprocess fixtures run in temp repos via `_create_fixture_repo`; the only live-tree runs are the read-only `--check` invocations in V-02.

SCOPE FENCE. Do not migrate the other `data["repo_root"]` producers, do not change `emit_index_write_result`'s `data` keys, and do not touch the `aw index all` aggregation owned by `7i4zba`. An out-of-scope edit that proves necessary is made and then justified with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. Execution requires explicit human approval (`aw ipd set approved 7dcpe1`). On completion every `E-*` is `performed`, every `V-*` is `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize 7dcpe1`. Never hand-roll the move or `git mv` the plan. This plan inherits `- Blocks-Release: next` from `aavf6a`.
