# IPD: migrate inline history into the sidecar and history read verb

- Date: 2026-08-18
- Kind: child
- Concern: awhistory Order 03 (spec 20260818-1525-02; RELEASE BLOCKER; requirements R3, R4; acceptance AC2, AC3). Two closely-related pieces close the sidecar story: (a) a one-time, IDEMPOTENT migration that folds EVERY existing inline `## Workflow history` block across all record trees into the ONE GLOBAL `.aw/records/history.jsonl` (Order 01 store), preserving each record's date/actor/message, then slims each file's inline history down to the latest ONE line (spec Section 3 + OQ-2); and (b) a READ verb that prints a record's full chronological history from the sidecar by id6. Both consume the Order 01 module (`agent_workflows/record_history.py`) and assume Order 02 has already routed NEW writes to the sidecar; this Order handles the LEGACY backfill + the reader.
- Scope: EDIT two existing modules + ONE test file. IN: (1) a `migrate_inline_history(repo_root, apply=False) -> int` function ADDED to `agent_workflows/record_history.py` (the Order 01 module) that walks every record tree EXCEPT `plans` (plans/IPDs are DELIBERATELY excluded - see the critical guard below), parses each file's inline `## Workflow history` records (grammar per `attention_contract.HISTORY_RECORD_RE`, attention_contract.py:431), appends each as a sidecar record (id6 from the file's `- Id:`, tree from its path) via the Order 01 writer, skips any record already present (idempotent, keyed on id6+date+message), then slims the inline block to its latest one line; (2) a `record-history <id6>` CLI verb ADDED to `agent_workflows/cli.py` (a parser + dispatch + a `_run_record_history` handler) that prints `read_for(repo_root, id6)` chronologically; (3) `tests/test_record_history_migrate.py`. OUT: the store/append/read_for writer (Order 01), routing NEW writes (Order 02), the `- Managed-by:` directive + templates (spec R5, separate work), any manifest/index/attention change (spec R6 leaves those reading inline state unchanged); and CRITICALLY the `plans` tree - IPDs are NEVER folded/slimmed because `ipd_lint` IPD-S405 (ipd_lint.py:666) requires the inline `executed` history entry at post-transition, so slimming plan history would break every executed plan's lint (a silent invariant violation across the whole plans tree). Plans keep their full inline history; the IPD lifecycle owns it.
- Status: reviewed
- Set: awhistory
- Order: 3
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: cizkf4

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from spec 20260818-1525-02; idempotent inline->sidecar migration + aw history read verb.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. PR-003 (BLOCKER): `migrate_inline_history` walked `_RECORD_TREES` INCLUDING `plans` and slimmed each file's inline history to latest-one - which would DELETE the `executed` `## Workflow history` entry that ipd_lint IPD-S405 (ipd_lint.py:666) requires on all ~184 executed plans, silently breaking the whole plans tree's post-transition lint (irreversible content loss). Fixed: removed `plans` from `_RECORD_TREES` with a critical guard comment; plans keep full inline history (the IPD lifecycle owns it). Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.

## Goal

Backfill the legacy inline history into the global sidecar without loss and idempotently, then slim each
file's inline `## Workflow history` to the single latest line (the current-state provenance the spec keeps
inline, OQ-2), and give humans/agents a read path (`aw record-history <id6>`) that prints a record's full
chronological log from `.aw/records/history.jsonl`. After this Order the sidecar is the source of truth for
history and the cached file body no longer carries the unbounded narrative (spec G2, AC3).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Do EXACTLY the steps below, in order. This Order EDITS `agent_workflows/record_history.py`
(created by Order 01) and `agent_workflows/cli.py`, and ADDS `tests/test_record_history_migrate.py`. Do NOT
touch any other module, index, or validator. Use 4-space indentation. After each code step, run the matching
V-item command and paste its output.

DEPENDENCY CONTRACT (from Order 01 `agent_workflows/record_history.py`, spec Section 3) - this Order assumes
these already exist and calls them; do NOT re-implement them:
- `SIDECAR_RELPATH = ".aw/records/history.jsonl"` and `sidecar_path(repo_root: Path) -> Path` returning `repo_root / SIDECAR_RELPATH`.
- `append(repo_root: Path, *, id6: str, date: str, tree: str, workflow: str, actor: str, message: str) -> None` appends one JSON object line `{id6,date,tree,workflow,actor,message}` (creating the file/parent dir if absent).
- `read_for(repo_root: Path, id6: str) -> List[dict]` returns every record dict for that id6 in file (chronological append) order.
- `read_all(repo_root: Path) -> List[dict]` returns every record dict in the sidecar (used by the idempotency key set).
If any Order-01 symbol name differs at execution time, adapt the CALL SITES (not the contract) and note it in the V evidence; the SHAPE above is what this Order depends on.

### Task group 1: migration - preview (no writes)

- [ ] E-01 Add helper parsers + a PREVIEW-only `migrate_inline_history` to `agent_workflows/record_history.py`. Insert the following block at the END of the module (after the Order 01 definitions). It (a) walks the record trees, (b) parses each file's inline `## Workflow history` records via the exact grammar, (c) reports what it WOULD fold, and writes NOTHING when `apply=False`.
  ```python
  # --------------------------------------------------------------------------------------
  # awhistory Order 03: one-time idempotent inline->sidecar migration + slim (spec R4, AC3)
  # --------------------------------------------------------------------------------------

  import re as _re
  from typing import Dict as _Dict, List as _List, Tuple as _Tuple

  from agent_workflows.attention_contract import HISTORY_RECORD_RE as _HISTORY_RECORD_RE

  # id6 line + the record trees to walk (first path segment under .aw/records/ is the sidecar `tree`).
  _ID_LINE_RE = _re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
  _HIST_HEADING = "## Workflow history"
  # CRITICAL: `plans` is DELIBERATELY EXCLUDED. IPDs keep their FULL inline `## Workflow history`
  # because `ipd_lint` IPD-S405 (ipd_lint.py:666) REQUIRES an inline `executed` entry at
  # post-transition; folding+slimming plan history would delete that entry across every executed
  # plan and break the whole plans tree's lint. The IPD lifecycle owns plan history; the sidecar
  # covers the other record types only.
  _RECORD_TREES = (
      "specs", "research", "backlog", "prompts", "walkthroughs", "roadmaps", "releases",
  )
  # Parse "workflow" + "actor" out of the free tail when it matches "<workflow> (<actor>): <message>";
  # otherwise the whole tail is the message and workflow/actor are "" (grammar only pins the date).
  _TAIL_RE = _re.compile(r"^(?P<workflow>\S+)\s*\((?P<actor>[^)]*)\):\s*(?P<message>.*)$")


  def _record_id6(text: str):
      m = _ID_LINE_RE.search(text)
      return m.group(1) if m else None


  def _tree_from_path(repo_root: Path, path: Path):
      """First path segment under .aw/records/ (the sidecar `tree`), or None if outside it."""
      try:
          rel = path.resolve().relative_to((repo_root / ".aw" / "records").resolve())
      except ValueError:
          return None
      parts = rel.parts
      return parts[0] if parts else None


  def _inline_history_records(text: str) -> _List[str]:
      """Return the raw '- YYYY-MM-DD ...' record lines inside the file's ## Workflow history block."""
      out: _List[str] = []
      in_hist = False
      for line in text.split("\n"):
          if line.strip() == _HIST_HEADING:
              in_hist = True
              continue
          if in_hist:
              if line.startswith("## "):
                  break
              if _HISTORY_RECORD_RE.match(line):
                  out.append(line)
      return out


  def _parse_record_line(line: str) -> _Tuple[str, str, str, str]:
      """(date, workflow, actor, message) from one record line. date is guaranteed by the caller."""
      m = _HISTORY_RECORD_RE.match(line)
      date = m.group("date")
      tail = line[len("- " + date):].strip()
      tm = _TAIL_RE.match(tail)
      if tm:
          return date, tm.group("workflow"), tm.group("actor"), tm.group("message").strip()
      return date, "", "", tail


  def _iter_record_files(repo_root: Path):
      """Yield every record .md file across the known trees (skips index/readme sentinels)."""
      base = repo_root / ".aw" / "records"
      for tree in _RECORD_TREES:
          d = base / tree
          if not d.is_dir():
              continue
          for p in sorted(d.rglob("*.md")):
              if p.name in ("README.md", "INDEX.md", "STATUS.md"):
                  continue
              yield tree, p


  def migrate_inline_history(repo_root: Path, apply: bool = False) -> int:
      """Fold every inline ## Workflow history record across the record trees into the global sidecar
      (idempotent, keyed on id6+date+message), then slim each file's inline block to its latest ONE
      record. apply=False (default) previews and writes nothing; returns the count of records that
      WOULD be (apply=False) or WERE (apply=True) newly folded into the sidecar."""

      repo_root = Path(repo_root)
      existing = {
          (r.get("id6"), r.get("date"), r.get("message"))
          for r in read_all(repo_root)
      }
      folded = 0
      for tree, path in _iter_record_files(repo_root):
          try:
              text = path.read_text(encoding="utf-8")
          except OSError:
              continue
          id6 = _record_id6(text)
          if not id6:
              continue
          records = _inline_history_records(text)
          if not records:
              continue
          for line in records:
              date, workflow, actor, message = _parse_record_line(line)
              key = (id6, date, message)
              if key in existing:
                  continue
              if apply:
                  append(
                      repo_root,
                      id6=id6,
                      date=date,
                      tree=tree,
                      workflow=workflow,
                      actor=actor,
                      message=message,
                  )
              existing.add(key)
              folded += 1
          if apply:
              _slim_inline_history(path, text, records)
      return folded
  ```
  - Depends on: none
  - Expected outcome: `python3 -c "import agent_workflows.record_history"` exits 0; calling `migrate_inline_history(repo_root)` (apply defaulting False) walks the trees and returns an int without writing to `.aw/records/history.jsonl` or modifying any file. (Cross-Order: this consumes Order 01's `record_history.append`/`read_for`/`read_all` and assumes Order 02 already routed NEW writes; if an Order-01 symbol name differs, adapt the call site per the DEPENDENCY CONTRACT above.)
  - Execution state: pending
- [ ] E-02 Add the `_slim_inline_history` helper (the WRITE side of `--apply`) directly ABOVE `migrate_inline_history` in `agent_workflows/record_history.py`. It rewrites the file's `## Workflow history` block to contain ONLY the LAST record line (latest in file order, per OQ-2), leaving the rest of the file byte-identical. It is a no-op when the block already has <=1 record.
  ```python
  def _slim_inline_history(path: Path, text: str, records: _List[str]) -> None:
      """Rewrite path's ## Workflow history block to keep ONLY the latest (last-in-order) record line.
      No-op if <=1 record. Preserves everything outside the block (spec OQ-2: keep the latest one)."""
      if len(records) <= 1:
          return
      keep = records[-1]
      lines = text.split("\n")
      out: _List[str] = []
      in_hist = False
      wrote_keep = False
      for line in lines:
          if line.strip() == _HIST_HEADING:
              in_hist = True
              out.append(line)
              continue
          if in_hist:
              if line.startswith("## "):
                  in_hist = False
                  out.append(line)
                  continue
              if _HISTORY_RECORD_RE.match(line):
                  if not wrote_keep:
                      out.append(keep)
                      wrote_keep = True
                  # drop every other record line
                  continue
              out.append(line)  # preserve blank lines / non-record prose in the block
              continue
          out.append(line)
      path.write_text("\n".join(out), encoding="utf-8")
  ```
  - Depends on: E-01
  - Expected outcome: with `apply=True`, a file whose inline history had N>1 records ends with exactly ONE record line (the last) in its `## Workflow history` block, and the sidecar has gained the folded records; re-reading `read_for(repo_root, id6)` returns all N records for that id6.
  - Execution state: pending

### Task group 2: read verb (CLI)

- [ ] E-03 Add the `record-history` subparser to `agent_workflows/cli.py`. Insert it immediately AFTER the existing `p_history` block (the ACTION history parser at cli.py:1268-1273; the name `history` is already taken for action documents, so this record-history verb gets its own name). Use this exact block:
  ```python
      p_record_history = sub.add_parser(
          "record-history",
          parents=[common],
          help="Print a record's full chronological workflow history from the global sidecar (by id6).",
      )
      p_record_history.add_argument("id6", help="The 6-char record id (from a file's `- Id:`).")
      p_record_history.add_argument(
          "--dir", default=None, help="Repo root (default: current directory)."
      )
  ```
  - Depends on: none
  - Expected outcome: `aw record-history --help` prints the new verb's help; `aw --help` lists `record-history`. (Parser wiring is independent of E-01/E-02; the handler that consumes it lands in E-04.)
  - Execution state: pending
- [ ] E-04 Add the `_run_record_history` handler + its dispatch. (a) Add the handler function immediately AFTER `_run_action_history` (which ends at cli.py:3579):
  ```python
  def _run_record_history(args: argparse.Namespace, term: Term) -> int:
      import os
      from pathlib import Path
      from agent_workflows import record_history as rh

      repo_root = Path(getattr(args, "dir", None) or os.getcwd())
      id6 = args.id6
      records = rh.read_for(repo_root, id6)
      if not records:
          term.status("warn", f"No sidecar history for id6 {id6}.")
          return 0
      term.heading(f"History for {id6}")
      for r in records:
          date = r.get("date", "")
          workflow = r.get("workflow", "")
          actor = r.get("actor", "")
          tree = r.get("tree", "")
          message = r.get("message", "")
          who = f" ({actor})" if actor else ""
          wf = f" {workflow}" if workflow else ""
          term.line(f"- {date} [{tree}]{wf}{who}: {message}")
      return 0
  ```
  (b) Add the dispatch branch immediately AFTER the existing `history` branch (cli.py:4098-4099, `if args.command == "history": return _run_action_history(args, term)`):
  ```python
      if args.command == "record-history":
          return _run_record_history(args, term)
  ```
  - Depends on: E-03
  - Expected outcome: `aw record-history <id6> --dir <repo>` prints one `- <date> [<tree>] <workflow> (<actor>): <message>` line per sidecar record for that id6, in chronological order; an unknown id6 prints a `warn` and exits 0. (Cross-Order: consumes Order 01's `record_history.read_for`.)
  - Execution state: pending

### Task group 3: idempotency + tests

- [ ] E-05 Create `tests/test_record_history_migrate.py` with a `unittest.TestCase` subclass `MigrateInlineHistoryTests` that builds a tmp repo fixture (in `setUp`, via `tempfile.TemporaryDirectory`: create `.aw/records/plans/pending/` and write ONE plan file `P` carrying `- Id: aaa111` and a `## Workflow history` block with TWO record lines - `- 2026-01-01 draft (alice): created.` and `- 2026-01-02 reviewed (bob): looked over.`). Write EXACTLY these test methods, then run the migration idempotency + read-verb paths:
  - `test_preview_writes_nothing`: `migrate_inline_history(root)` (apply False) returns `2`; assert `.aw/records/history.jsonl` does NOT exist (or is empty) AND `P` is byte-identical to before (both records still inline).
  - `test_apply_folds_and_slims`: `migrate_inline_history(root, apply=True)` returns `2`; `read_for(root,"aaa111")` returns 2 records with the right dates/actors/messages; `P`'s inline `## Workflow history` block now has exactly ONE record line (the 2026-01-02 one).
  - `test_idempotent_rerun`: after one `apply=True`, a SECOND `migrate_inline_history(root, apply=True)` returns `0` and `read_for(root,"aaa111")` still returns exactly 2 records (no duplicates; key = id6+date+message).
  - `test_read_verb`: build `args = argparse.Namespace(dir=root, id6="aaa111", no_color=True)`, call `_dispatch`-equivalent handler `cli._run_record_history(args, cli.Term(color=False))` after an `apply=True`; assert it returns 0 (capture stdout to confirm both dates appear). If Order 01's `read_for` is unavailable in isolation, this method may `assertEqual(len(rh.read_for(root,"aaa111")), 2)` as the equivalent evidence.
  Then run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: all four test methods pass; full serial suite green (no regressions - this Order adds one test file and appends to two modules). (Cross-Order: requires the Order 01 `record_history` module present so `append`/`read_for`/`read_all` resolve.)
  - Execution state: pending

## Project conventions discovered (Step 0)

- History-record grammar: `attention_contract.HISTORY_RECORD_RE = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) .+$")` (attention_contract.py:431) - the DATE is the only pinned field; everything after is a free single line. `last_history_at` (attention_contract.py:434) takes the LAST matching record's date. This Order parses `<workflow> (<actor>): <message>` out of that free tail best-effort; when the tail does not match, the whole tail is the message.
- Inline-block walk pattern (start at `## Workflow history`, stop at the next `## `): mirrored from `specs._history_lines` (specs.py:109) and `attention._history_section_lines` (attention.py:81).
- Sidecar shape (spec Section 3): ONE GLOBAL append-only JSONL `.aw/records/history.jsonl`, each line `{id6, date, tree, workflow, actor, message}`, keyed by id6, `tree` in {plans,specs,research,backlog,prompts,walkthroughs,roadmaps,releases,...}. Owned by the Order 01 `record_history` module.
- `tree` derivation: the FIRST path segment under `.aw/records/` (e.g. `.aw/records/plans/pending/x.ipd.md` -> `plans`). The `.aw/records/` layout is flat for the doc-family types (Order 07 retrofit, record_producers.py:123-133), so the first segment IS the tree.
- id6 front-matter line is universal: `^- Id:\s*([0-9a-z]{6})\s*$` (mirrors plans_index / selectors readers).
- CLI: `history` is already a verb (action-document lifecycle, `_run_action_history`, cli.py:3567, dispatch cli.py:4098) - so the record-history read verb takes a DISTINCT name (`record-history`) to avoid collision. Handlers follow `def _run_<verb>(args, term) -> int` returning an exit code; repo root is `getattr(args, "dir", None) or os.getcwd()` (mirrors `specs check --dir`).

## Findings

| # | Finding | Consequence |
|---|---------|-------------|
| F1 | The `history` CLI verb already exists for ACTION documents (cli.py:1268, 4098). | The sidecar read verb must NOT reuse `history`; use `record-history` (distinct name, own parser + dispatch + handler). |
| F2 | The record-history grammar pins only the date; the `<workflow> (<actor>): <message>` shape is a convention, not enforced. | Parse the tail best-effort with `_TAIL_RE`; on no match, fold the whole tail as `message` with empty workflow/actor - lossless. |
| F3 | Idempotency must survive re-runs AND partial prior state (Order 02 may already have appended some records). | Key on `(id6, date, message)` computed from `read_all` BEFORE folding; skip any record already present. This makes re-run add zero (AC3). |
| F4 | OQ-2 keeps the LATEST ONE inline line, not zero. | `_slim_inline_history` keeps `records[-1]` (last in file order) and drops the rest; no-op if <=1. |
| F5 | This Order depends on the Order 01 module existing. | The E-items ADD to `record_history.py` and CALL `append`/`read_for`/`read_all`; if a symbol name differs, adapt the call site (not the contract) and note it in V evidence. |

## Proposed changes (ordered, validatable)

1. Preview-only `migrate_inline_history` + parsers/tree-derivation added to `record_history.py` (E-01). 2. `_slim_inline_history` write helper + wire `apply=True` (E-02). 3. `record-history` subparser in `cli.py` (E-03). 4. `_run_record_history` handler + dispatch branch (E-04). 5. `tests/test_record_history_migrate.py` (preview/apply/idempotent/read) + full serial suite (E-05).

## Deferred / out of scope (with reason)

- The sidecar store + `append`/`read_for`/`read_all` writer: awhistory Order 01 (this Order consumes it).
- Routing NEW status-transition writers to the sidecar + slimming on write: awhistory Order 02 (this Order backfills the LEGACY inline blocks only).
- The `- Managed-by: aw ...` front-matter directive + template/generator changes: spec R5, separate work (not required for migration or read).
- Any manifest/index/attention/validator change: spec R6 leaves those reading inline Status/Set/Id/Order unchanged; history moving does not touch them.

## Scope check

- Over-scope: none - two module edits (`record_history.py` append; `cli.py` verb) + one test file; no index/validator/template change.
- Under-scope: none - migration preview + apply + idempotency guard + the read verb + tests are all present; the four spec pieces this Order owns (R3 read verb, R4 migration, AC2 read, AC3 idempotent no-loss) are each covered by an E and a V.

## Required tests / validation

`tests/test_record_history_migrate.py` (E-05, four named methods: preview-no-write, apply-fold+slim, idempotent-rerun, read-verb) + the full serial suite (`python3 -m pytest -p no:xdist`). Each V-item pins one E with pasted evidence.

## Spec / documentation sync

No `AGENTS.md`/README grammar change here (the `- Managed-by:` directive + user-facing docs are spec R5, separate work). No spec transition in this Order: awhistory is a multi-Order Set and the orchestrator (Order 00) advances spec `20260818-1525-02` (draft -> implemented) only on Set completion, after this terminal Order lands. This Order does add the `record-history` verb, which the orchestrator's doc-sync step will surface when the Set closes.

## Open questions

### OQ-01: should the read verb be `aw record-history <id6>` or `aw show <id6> --history`?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: `aw record-history <id6>` (a distinct verb). The `history` name is already taken by the action-document lifecycle verb (cli.py:1268/4098), and `aw show` currently resolves ACTION refs (cli.py:3514), not record id6 - overloading it with a `--history` flag would conflate two id namespaces. A dedicated `record-history` verb is unambiguous and additive; a future awselect/awcmdsurf Set can add a record-oriented `aw show <id6> --history` alias once the shared selector resolver (awselect) lands, without changing this migration.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import agent_workflows.record_history; print('ok')"` printing `ok`, AND a snippet building a tmp repo with one plan carrying a 2-record inline history, calling `migrate_inline_history(root)` (apply False), showing it returns `2` and that `.aw/records/history.jsonl` was NOT created (or is empty) and the plan file is unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a snippet calling `migrate_inline_history(root, apply=True)` on the 2-record fixture, then showing (a) `read_for(root, id6)` returns 2 records and (b) the plan file's `## Workflow history` block now contains exactly ONE record line (the last-dated one), with the rest of the file preserved.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `aw record-history --help` (shows the id6 positional + `--dir`) and confirm `record-history` appears in `aw --help`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the output of `aw record-history aaa111 --dir <tmp-repo>` after an `apply=True` migration, showing one `- <date> [<tree>] <workflow> (<actor>): <message>` line per record in chronological order; AND the unknown-id6 case printing a `warn` and exiting 0.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `pytest tests/test_record_history_migrate.py -p no:xdist -q` (4 passed) AND the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing no regressions. The `test_idempotent_rerun` result MUST show a second `apply=True` returning `0` and `read_for` still returning exactly 2 records.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the three touched
files path-scoped (`git commit -- agent_workflows/record_history.py agent_workflows/cli.py tests/test_record_history_migrate.py`;
never `git add -A`), and NEVER pushes. This is a RELEASE BLOCKER (spec 20260818-1525-02, OQ-3) and the
TERMINAL Order of the awhistory Set: it depends on Order 01 (the `record_history` store/writer) and Order 02
(NEW writes routed + slim-on-write). The plan moves to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every V-item is `pass`; on Set completion the orchestrator
(awhistory Order 00) advances spec `20260818-1525-02` (draft -> implemented) with cited evidence.
