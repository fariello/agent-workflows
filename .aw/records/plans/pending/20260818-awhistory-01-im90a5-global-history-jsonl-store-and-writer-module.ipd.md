# IPD: global history jsonl store and writer module

- Date: 2026-08-18
- Kind: child
- Concern: awhistory Order 01 (spec 20260818-1525-02; RELEASE BLOCKER; requirements R1; acceptance AC1/AC2 substrate). Build ONE self-contained store-and-writer module for the ONE GLOBAL append-only history sidecar `.aw/records/history.jsonl` (spec Section 3), keyed by id6, where each line is a JSON object `{id6, date, tree, workflow, actor, message}`. This is a PURE PRIMITIVE with no CLI wiring and no edits to existing writers: Order 02 (route status writers + slim inline) and Order 03 (migrate + read verb) consume it. Building the store/append/read as its own module with its own tests keeps this Order small, unambiguous, and independently green.
- Scope: ONE new module `agent_workflows/record_history.py` + ONE new test file `tests/test_record_history.py`. IN: `history_path(repo_root)->Path` (the `.aw/records/history.jsonl` location), `append(repo_root, *, id6, tree, workflow, actor, message, date=None)` (one JSON line, parent-dir create, utf-8 append, default date = today YYYYMMDD, ValueError on a bad id6 via `artifact_core.ID6_RE`), `read_for(repo_root, id6)->List[dict]` (file order, `[]` when missing, skip malformed JSON lines), `read_all(repo_root)->List[dict]`, and the `MANAGED_BY_DIRECTIVE` string constant (spec G4). OUT: any change to `cli.py`, `specs.py`, `backlog.py`, `attention_contract.py`, any existing writer, any template/generator, the migration, or the read verb (all Order 02 / Order 03 / spec R5). This Order adds a NEW file and a NEW test file ONLY.
- Status: to-review
- Set: awhistory
- Order: 1
- Highest E allocated: 06
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: im90a5

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from spec 20260818-1525-02.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Pure new module (record_history.py) + tests; verified artifact_core.ID6_RE, the global-sidecar path, and append/read_for shape; no interaction with existing code; no findings.

## Goal

Add a new pure module `agent_workflows/record_history.py` that owns the ONE GLOBAL append-only history
sidecar `.aw/records/history.jsonl` (spec Section 3): a `history_path` locator, an `append` writer that
emits one `{id6, date, tree, workflow, actor, message}` JSON line (validating id6 against
`artifact_core.ID6_RE`), and `read_for`/`read_all` readers that tolerate a missing file and skip malformed
lines. It touches nothing else, so it is safe and independently testable; Order 02 routes the existing
status writers into it and Order 03 backfills legacy inline history + adds the read verb.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Do EXACTLY the steps below, in order. Create only the two files named in Scope
(`agent_workflows/record_history.py`, `tests/test_record_history.py`). Do NOT edit `cli.py`, `specs.py`,
`backlog.py`, or any other existing module. After each code step, run the matching V-item command and paste
its output. Use 4-space indentation and `from __future__ import annotations` at the top of the module.

### Task group 1: create the module skeleton + the sidecar locator

- [ ] E-01 Create the new file `agent_workflows/record_history.py` with this exact header, imports, module constants, and locator, and nothing else yet:
  ```python
  """Global append-only workflow-history sidecar (spec 20260818-1525-02, Section 3).

  ONE file per repo: `.aw/records/history.jsonl`, keyed by id6. Each line is a JSON object
  `{id6, date, tree, workflow, actor, message}`. Append-only, so line order is irrelevant and
  concurrent-append git merges rarely conflict. Pure (no CLI, no argparse). Consumed by the
  status writers (Order 02) and the migration + read verb (Order 03)."""

  from __future__ import annotations

  import json
  from datetime import date as _date
  from pathlib import Path
  from typing import List, Optional

  from agent_workflows import artifact_core as _core

  SIDECAR_RELPATH = ".aw/records/history.jsonl"

  # Front-matter directive the managed record files carry (spec G4); Order 03 / templates write it.
  MANAGED_BY_DIRECTIVE = (
      "- Managed-by: aw (status + history are managed by the aw CLI; do not hand-edit them)"
  )


  def history_path(repo_root) -> Path:
      """The ONE GLOBAL history sidecar path for a repo root: `.aw/records/history.jsonl`."""
      return Path(repo_root) / SIDECAR_RELPATH
  ```
  - Depends on: none
  - Expected outcome: the file imports cleanly (`python3 -c "import agent_workflows.record_history"` exits 0), `record_history.MANAGED_BY_DIRECTIVE` equals the exact spec-G4 string, and `history_path("/tmp/x")` returns `Path("/tmp/x/.aw/records/history.jsonl")`.
  - Execution state: pending

### Task group 2: the append writer

- [ ] E-02 Add the `append` writer directly below `history_path`. It validates the id6 against `artifact_core.ID6_RE` (raising `ValueError` on a bad token), defaults `date` to today as `YYYYMMDD`, creates the parent directory if absent, and appends exactly ONE utf-8 JSON line `{id6, date, tree, workflow, actor, message}` (fixed key order) followed by `\n`. Use this exact block:
  ```python
  def append(
      repo_root,
      *,
      id6: str,
      tree: str,
      workflow: str,
      actor: str,
      message: str,
      date: Optional[str] = None,
  ) -> None:
      """Append ONE history record line to the global sidecar (creating file + parent dir if absent).

      `id6` MUST match `artifact_core.ID6_RE` (else ValueError). `date` defaults to today as YYYYMMDD.
      The line is a single JSON object `{id6, date, tree, workflow, actor, message}` + a trailing newline;
      append-only, so line order is irrelevant."""
      if not _core.ID6_RE.match(id6 or ""):
          raise ValueError(f"record_history.append: {id6!r} is not a valid id6")
      if date is None:
          date = _date.today().strftime("%Y%m%d")
      record = {
          "id6": id6,
          "date": date,
          "tree": tree,
          "workflow": workflow,
          "actor": actor,
          "message": message,
      }
      path = history_path(repo_root)
      path.parent.mkdir(parents=True, exist_ok=True)
      with path.open("a", encoding="utf-8") as fh:
          fh.write(json.dumps(record, ensure_ascii=False) + "\n")
  ```
  - Depends on: E-01
  - Expected outcome: `append(root, id6="aaa111", tree="plans", workflow="ipd", actor="alice", message="created")` creates `.aw/records/history.jsonl` (parent dirs auto-created) containing one JSON line whose parsed object equals `{"id6":"aaa111","date":<today YYYYMMDD>,"tree":"plans","workflow":"ipd","actor":"alice","message":"created"}`; `append(root, id6="BAD", ...)` raises `ValueError`.
  - Execution state: pending

### Task group 3: the readers

- [ ] E-03 Add the `read_for` reader directly below `append`. It returns every record dict for one id6 in file (append) order, returns `[]` when the file is missing, and SKIPS any line that fails `json.loads` (a `json.JSONDecodeError`). Use this exact block:
  ```python
  def read_for(repo_root, id6: str) -> List[dict]:
      """Every history record for `id6`, in file (chronological append) order. `[]` if the sidecar is
      missing. Malformed (non-JSON) lines are skipped, never raised."""
      path = history_path(repo_root)
      if not path.is_file():
          return []
      out: List[dict] = []
      for line in path.read_text(encoding="utf-8").splitlines():
          line = line.strip()
          if not line:
              continue
          try:
              rec = json.loads(line)
          except json.JSONDecodeError:
              continue
          if isinstance(rec, dict) and rec.get("id6") == id6:
              out.append(rec)
      return out
  ```
  - Depends on: E-01,E-02
  - Expected outcome: after two `append`s for `aaa111` and one for `bbb222`, `read_for(root,"aaa111")` returns the two `aaa111` records in append order and `read_for(root,"missing")==[]`; `read_for(root,"aaa111")` on a repo with no sidecar returns `[]`; a hand-inserted non-JSON line is skipped without raising.
  - Execution state: pending
- [ ] E-04 Add the `read_all` reader directly below `read_for`. It returns EVERY record dict in the sidecar (all id6s) in file order, `[]` when missing, skipping malformed lines. Order 03's idempotency key set consumes it. Use this exact block:
  ```python
  def read_all(repo_root) -> List[dict]:
      """Every history record in the sidecar (all id6s), in file order. `[]` if missing; malformed lines
      skipped. Used by the Order 03 migration's idempotency key set."""
      path = history_path(repo_root)
      if not path.is_file():
          return []
      out: List[dict] = []
      for line in path.read_text(encoding="utf-8").splitlines():
          line = line.strip()
          if not line:
              continue
          try:
              rec = json.loads(line)
          except json.JSONDecodeError:
              continue
          if isinstance(rec, dict):
              out.append(rec)
      return out
  ```
  - Depends on: E-01,E-02
  - Expected outcome: after appending records for `aaa111` (x2) and `bbb222` (x1), `read_all(root)` returns all three dicts in file order; `read_all(root)==[]` when the sidecar is missing.
  - Execution state: pending

### Task group 4: tests

- [ ] E-05 Create `tests/test_record_history.py` with a `unittest.TestCase` subclass `RecordHistoryTests` that builds a tmp repo fixture (in `setUp` via `tempfile.TemporaryDirectory`, storing `self.root = Path(self._tmp.name)`; no files pre-created - `append` creates the sidecar). Import the module as `from agent_workflows import record_history as rh`. Write EXACTLY these five test methods with these assertions:
  - `test_append_and_read`: call `rh.append(self.root, id6="aaa111", tree="plans", workflow="ipd", actor="alice", message="created")` then `rh.append(self.root, id6="aaa111", tree="plans", workflow="ipd", actor="bob", message="reviewed")` and `rh.append(self.root, id6="bbb222", tree="specs", workflow="specs", actor="carol", message="drafted")`. Assert `rh.history_path(self.root).is_file()`; assert `len(rh.read_for(self.root, "aaa111")) == 2` and the two messages are `["created","reviewed"]` in that order; assert `len(rh.read_all(self.root)) == 3`.
  - `test_missing_file_returns_empty`: on a fresh `self.root` (no append yet), assert `rh.read_for(self.root, "aaa111") == []` and `rh.read_all(self.root) == []`.
  - `test_malformed_line_skipped`: `rh.append(self.root, id6="aaa111", tree="plans", workflow="ipd", actor="alice", message="ok")`; then append a raw non-JSON line by opening `rh.history_path(self.root)` in append mode and writing `"this is not json\n"`; assert `len(rh.read_all(self.root)) == 1` and `len(rh.read_for(self.root, "aaa111")) == 1` (the bad line skipped, no exception).
  - `test_bad_id6_raises`: assert `self.assertRaises(ValueError, rh.append, self.root, id6="BAD", tree="plans", workflow="ipd", actor="a", message="m")` (bad id6, uppercase/short); also assert it raises for `id6=""`.
  - `test_date_defaults_today`: call `rh.append(self.root, id6="aaa111", tree="plans", workflow="ipd", actor="a", message="m")` WITHOUT a `date=`; read it back and assert its `date` equals `datetime.date.today().strftime("%Y%m%d")`; then call again WITH `date="20200101"` and assert that record's `date == "20200101"`.
  Then run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: all five test methods pass; full serial suite green (this Order only ADDS files).
  - Execution state: pending
- [ ] E-06 Confirm the module is importable in isolation and carries no accidental side effects (no argparse, no top-level writes, no dependency on `cli.py`). Run `python3 -c "import agent_workflows.record_history as rh; assert not hasattr(rh, 'argparse'); print('ok')"` and confirm it prints `ok`. This pins the PRIMITIVE property (Order 02/03 import it without pulling in the CLI).
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: the isolation import prints `ok` (no argparse symbol, no CLI import, no write on import).
  - Execution state: pending

## Project conventions discovered (Step 0)

- id6 primitive: `artifact_core.ID6_RE = re.compile(r"\A[0-9a-z]{6}\Z")` (artifact_core.py:39); `is_valid_id6` (:45). `append` validates with `ID6_RE.match` and raises `ValueError` on a bad token.
- Sidecar shape (spec Section 3): ONE GLOBAL append-only JSONL `.aw/records/history.jsonl`, each line `{id6, date, tree, workflow, actor, message}`, keyed by id6, `tree` in {plans,specs,research,backlog,prompts,walkthroughs,roadmaps,releases,...}. Append-only: line order is irrelevant, concurrent-append merges rarely conflict.
- Date convention: this module writes `date` as `YYYYMMDD` (compact) via `datetime.date.today().strftime("%Y%m%d")` when a caller omits `date=`. (The inline `## Workflow history` grammar uses `YYYY-MM-DD`, attention_contract.py:431; Order 03 parses that and passes an explicit `date` string when folding.)
- `- Managed-by:` directive (spec G4): kept as the module constant `MANAGED_BY_DIRECTIVE` here so Order 03 / the templates reuse one canonical string; this Order only defines it, it does NOT write it into any record file.
- This module is a PRIMITIVE: no argparse, no writes on import, no dependency on `cli.py`/`specs.py`/`backlog.py`. Keep it importable in isolation (E-06 pins this).

## Findings

| # | Finding | Consequence |
|---|---------|-------------|
| F1 | id6 primitive already exists (`artifact_core.ID6_RE`). | `append` reuses it for validation; the module invents no new id grammar. |
| F2 | Append-only JSONL (spec Section 3) neutralizes the write-hotspot + merge-conflict concern. | `append` opens the file in `"a"` mode and writes one JSON line; readers tolerate line order + missing file. |
| F3 | Pure module, new file only. | Zero risk to existing behavior; the full suite must stay green with only additions (E-05/E-06). |
| F4 | Malformed lines must not crash consumers. | `read_for`/`read_all` skip a `json.JSONDecodeError` line rather than raising (F2 tolerance). |

## Proposed changes (ordered, validatable)

1. New `record_history.py` header/imports + `SIDECAR_RELPATH`/`MANAGED_BY_DIRECTIVE`/`history_path` (E-01). 2. `append` writer with id6 validation + default date + parent-dir create (E-02). 3. `read_for` reader (E-03). 4. `read_all` reader (E-04). 5. `tests/test_record_history.py` with the five named methods + full suite (E-05). 6. isolation/PRIMITIVE-property check (E-06).

## Deferred / out of scope (with reason)

- Routing the existing status writers (`specs set`/`specs note`/`_append_history`, `backlog` set) into `append` + slimming inline history: awhistory Order 02.
- The one-time idempotent migration of legacy inline `## Workflow history` into the sidecar + the `aw` read verb: awhistory Order 03.
- Writing the `- Managed-by:` directive into record templates + a generator so new files carry it: spec R5, separate work (this Order only defines the constant).
- Any manifest/index/attention/validator change: spec R6 leaves those reading inline Status/Set/Id/Order unchanged.

## Scope check

- Over-scope: none - one new module + its test; no edit to any existing module, no CLI wiring.
- Under-scope: none for the PRIMITIVE - the locator, the append writer (id6 validation + default date + parent-dir create + utf-8 append), both readers (missing-file + malformed-line tolerance), and the `MANAGED_BY_DIRECTIVE` constant are all present and each pinned by a V-item.

## Required tests / validation

`tests/test_record_history.py` (E-05, five named methods: append_and_read, missing_file_returns_empty, malformed_line_skipped, bad_id6_raises, date_defaults_today) + the isolation check (E-06) + the full serial suite (`python3 -m pytest -p no:xdist`). Each V-item pins one E with pasted evidence.

## Spec / documentation sync

No `AGENTS.md`/README grammar change here (the `- Managed-by:` directive + user-facing docs are spec R5, separate work). No spec transition in this Order: awhistory is a multi-Order Set and the orchestrator (Order 00) advances spec `20260818-1525-02` (draft -> implemented) only on Set completion, after the terminal Order (03) lands.

## Open questions

### OQ-01: should `date` be stored compact (YYYYMMDD) or with dashes (YYYY-MM-DD)?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: compact `YYYYMMDD` is the DEFAULT this module writes (matching the artifact-naming grammar's date facet), but `append` accepts ANY `date=` string opaquely, so Order 03 can pass the `YYYY-MM-DD` value it parses from an inline `## Workflow history` record verbatim. The sidecar therefore preserves whatever date form the caller supplies; the readers do not reformat. This keeps the store lossless and defers any display normalization to the read verb (Order 03).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import agent_workflows.record_history as rh; print(rh.MANAGED_BY_DIRECTIVE); print(rh.history_path('/tmp/x'))"` showing the exact `- Managed-by: aw (status + history are managed by the aw CLI; do not hand-edit them)` string AND `/tmp/x/.aw/records/history.jsonl`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a Python snippet building a tmp repo, calling `append(root, id6="aaa111", tree="plans", workflow="ipd", actor="alice", message="created")`, then showing `.aw/records/history.jsonl` exists and `json.loads(open(...).readline())` equals `{"id6":"aaa111","date":<today YYYYMMDD>,"tree":"plans","workflow":"ipd","actor":"alice","message":"created"}`; AND `append(root, id6="BAD", ...)` raising `ValueError`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a snippet doing two appends for `aaa111` and one for `bbb222`, showing `read_for(root,"aaa111")` returns the two `aaa111` records in append order, `read_for(root,"missing")==[]`, and (after appending a hand-written non-JSON line) `read_for` still returns exactly the JSON records without raising.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `read_all(root)` after three appends returning all three dicts in file order, and `read_all(root)==[]` on a repo with no sidecar.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `pytest tests/test_record_history.py -p no:xdist -q` (5 passed) AND the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing no regressions.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -c "import agent_workflows.record_history as rh; assert not hasattr(rh, 'argparse'); print('ok')"` printing `ok`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: six E-items but one cohesive unit - a single new module (`record_history.py`) plus its single test file. E-01..E-04 are the four small members of one API surface (locator, writer, two readers) that must ship together to be useful, E-05 tests them, and E-06 pins the PRIMITIVE property Orders 02/03 rely on. Splitting further would strand a half-built API; the Order stays one module + one test.

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the two new files
path-scoped (`git commit -- agent_workflows/record_history.py tests/test_record_history.py`; never
`git add -A`), and NEVER pushes. This is a RELEASE BLOCKER (spec 20260818-1525-02, OQ-3) and Order 01 of
the awhistory Set; Order 02 (route writers + slim inline) and Order 03 (migrate + read verb) depend on this
module. The plan moves to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition`
conforms and every V-item is `pass`.
