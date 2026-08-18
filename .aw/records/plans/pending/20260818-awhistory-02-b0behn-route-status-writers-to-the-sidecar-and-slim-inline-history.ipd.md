# IPD: route status writers to the sidecar and slim inline history

- Date: 2026-08-18
- Kind: child
- Concern: awhistory Order 02 (spec 20260818-1525-02; RELEASE BLOCKER; requirement R2; acceptance AC1). Route the EXISTING status-transition writers so that, in ADDITION to their current inline-history append, they ALSO append one record to the ONE GLOBAL sidecar `.aw/records/history.jsonl` (the Order 01 module), and slim the inline `## Workflow history` block down to the LATEST ONE record line (spec Section 3 + OQ-2). The writers touched are `agent_workflows/specs.py` (`_append_history` specs.py:224, `run_set` specs.py:330, `run_note` specs.py:550) and `agent_workflows/backlog.py` (the history append in `_reattach_history` backlog.py:413). CRITICAL: `aw attention`'s `last_history_at` derivation reads the inline `## Workflow history` record DATE (attention_contract.py:434, grammar attention_contract.py:431), so this Order KEEPS the latest-one inline record line (it must NOT remove the `## Workflow history` section) or that derivation breaks (spec R6 / AC4).
- Scope: EDIT two existing modules + ONE new test file. IN: (1) route `specs.py`'s three writers to ALSO call `record_history.append(...)` and slim the inline block to the latest one line; (2) route `backlog.py`'s history append likewise; (3) `tests/test_history_routing.py` proving a routed write appends exactly one sidecar record AND that a slimmed file still yields the correct `attention` `last_history_at`. OUT: the store/append/read writer (Order 01, consumed here), the legacy inline-history migration + the read verb (Order 03), the `- Managed-by:` directive + templates (spec R5), any manifest/index/attention derivation CHANGE (spec R6 leaves those reading inline state unchanged - this Order keeps the inline latest-one line precisely so `attention` is untouched).
- Status: to-review
- Set: awhistory
- Order: 2
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: b0behn

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from spec 20260818-1525-02.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).

## Goal

Route every existing status-transition writer (`aw specs set`, `aw specs note`, the shared
`_append_history`, and `aw backlog set`) so each ALSO appends one record to the global sidecar
`.aw/records/history.jsonl` (Order 01 `record_history.append`), and slim each file's inline
`## Workflow history` block to the LATEST ONE record line (spec OQ-2). Keeping exactly one inline record
line preserves `aw attention`'s `last_history_at` derivation (attention_contract.py:434), so `attention`,
`specs check`, and `backlog check` keep passing unchanged (spec R6, AC4) while NEW writes stop growing the
inline body (AC1).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Do EXACTLY the steps below, in order. This Order EDITS `agent_workflows/specs.py` and
`agent_workflows/backlog.py`, and ADDS `tests/test_history_routing.py`. Do NOT touch any other module,
index, or validator. Use 4-space indentation. After each code step, run the matching V-item command and
paste its output.

DEPENDENCY CONTRACT (from Order 01 `agent_workflows/record_history.py`, spec Section 3) - this Order assumes
these already exist and CALLS them; do NOT re-implement them:
- `append(repo_root, *, id6, tree, workflow, actor, message, date=None) -> None` appends one JSON line `{id6,date,tree,workflow,actor,message}` (creating file/parent dir if absent; ValueError on a bad id6).
- `history_path(repo_root) -> Path` returns `repo_root / ".aw/records/history.jsonl"`.
If an Order-01 symbol name differs at execution time, adapt the CALL SITE (not the contract) and note it in the V evidence.

### Task group 1: route the specs writers + slim inline

- [ ] E-01 In `agent_workflows/specs.py`, (a) add two small helpers near the existing readers (after `_history_lines`, which ends at specs.py:132), then (b) route the sidecar append + inline slim through the shared `_append_history` (specs.py:224) so all three specs writers (`run_set` specs.py:330, `run_note` specs.py:550, and `run_set`'s migrate sibling) benefit. Do it as follows:
  - (a) Add a module-level id6 reader and a repo-root deriver (mirrors `_evidence_resolvable`'s walk-up, specs.py:565):
  ```python
  import re as _re

  _ID_RE = _re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")


  def _read_id6(text: str):
      m = _ID_RE.search(text)
      return m.group(1) if m else None


  def _repo_root_for(path: Path) -> Path:
      """Walk up from a record file to the repo root (a dir holding `.aw`/`.agents`/`.git`)."""
      for parent in path.resolve().parents:
          if (parent / ".aw").is_dir() or (parent / ".agents").is_dir() or (parent / ".git").exists():
              return parent
      return Path(".")
  ```
  - (b) Slim the inline block in `_append_history` (specs.py:224) to the LATEST ONE record line. Change `_append_history` so that, after inserting the new record, it KEEPS ONLY the last matching `HISTORY_RECORD_RE` line inside the `## Workflow history` section (dropping older record lines but preserving the heading and any non-record prose). Import the grammar `from agent_workflows.attention_contract import HISTORY_RECORD_RE` and, after the existing insert logic builds `out`, post-process the section to keep only the last record line. Add this slim pass at the end of `_append_history` just before `return out`:
  ```python
      # spec 20260818-1525-02 OQ-2: keep ONLY the latest inline record line (the full log is in the sidecar).
      slimmed: List[str] = []
      in_hist = False
      records_in_section = [
          ln for ln in out
          if HISTORY_RECORD_RE.match(ln)
      ]
      # find the section span to keep only its LAST record
      last_record = None
      seen = False
      for ln in out:
          if ln.strip() == "## Workflow history":
              in_hist = True
              # compute the last record line within this section
              j = out.index(ln) + 1
              last_record = None
              while j < len(out) and not out[j].startswith("## "):
                  if HISTORY_RECORD_RE.match(out[j]):
                      last_record = out[j]
                  j += 1
              slimmed.append(ln)
              continue
          if in_hist:
              if ln.startswith("## "):
                  in_hist = False
                  slimmed.append(ln)
                  continue
              if HISTORY_RECORD_RE.match(ln):
                  if ln == last_record and not seen:
                      slimmed.append(ln)
                      seen = True
                  continue
              slimmed.append(ln)
              continue
          slimmed.append(ln)
      return slimmed
  ```
  - Depends on: none
  - Expected outcome: after this edit, `_append_history(lines, "- 2026-01-02 reviewed (x): y")` on a `lines` list whose `## Workflow history` already had older records returns a list whose `## Workflow history` section contains EXACTLY ONE record line (the newest, `2026-01-02`), heading + non-record prose preserved; `python3 -c "import agent_workflows.specs"` exits 0.
  - Execution state: pending
- [ ] E-02 Route the sidecar append into the two specs entry points that append a transition record. In `run_set` (specs.py:330), immediately BEFORE the `out = _append_history(out, f"- {date} {new} {actor}: ...")` call (specs.py:405), append to the sidecar. Use the id6 + repo-root helpers from E-01 and the Order 01 writer. Insert directly above the `_append_history` call at specs.py:405:
  ```python
      id6 = _read_id6(text)
      if id6:
          from agent_workflows import record_history as _rh
          _rh.append(
              _repo_root_for(path),
              id6=id6,
              tree="specs",
              workflow="specs",
              actor="aw specs --by-human" if getattr(args, "by_human", False) else "aw specs",
              message=str(msg),
              date=date,
          )
  ```
  Do the SAME in `run_note` (specs.py:550): immediately BEFORE its `out = _append_history(lines, f"- {date} note (aw specs): {args.message}")` (specs.py:559), read `id6 = _read_id6(text)` and, if present, `record_history.append(_repo_root_for(path), id6=id6, tree="specs", workflow="specs", actor="aw specs note", message=str(args.message), date=date)`. (The `_append_history` slim from E-01 then trims the inline block to the latest one on both paths.)
  - Depends on: E-01
  - Expected outcome: `aw specs set --status to-review --message "x" <spec>` (or `note`) appends exactly ONE line to `.aw/records/history.jsonl` with `{id6:<spec id6>, tree:"specs", workflow:"specs", ...}` AND leaves the spec's inline `## Workflow history` with exactly one record line; `aw specs check <spec>` still conforms.
  - Execution state: pending

### Task group 2: route the backlog writer

- [ ] E-03 In `agent_workflows/backlog.py`, route the backlog transition into the sidecar and slim the inline block. `_reattach_history` (backlog.py:410-439) rebuilds the inline history block (it currently re-emits ALL prior records + the new one at backlog.py:435). (a) Change `_reattach_history` so `hist_block` keeps ONLY the new record (the latest one): replace `hist_block = "\n".join(old_hist + [new_record]) if old_hist else new_record` (backlog.py:435) with `hist_block = new_record` (drop the re-emitted `old_hist`; the full log now lives in the sidecar). (b) In `run_set` (backlog.py:338), AFTER `rendered = _reattach_history(...)` (backlog.py:375-377) and using the already-parsed `item` (which carries `item.id`, the id6, from `parse_item`, backlog.py:356), append the sidecar record. Insert directly after the `_reattach_history(...)` call:
  ```python
      if getattr(item, "id", None):
          from agent_workflows import record_history as _rh
          from datetime import date as _date
          _rh.append(
              repo_root,
              id6=item.id,
              tree="backlog",
              workflow="backlog",
              actor="aw backlog",
              message=(getattr(args, "message", "") or f"status -> {new_status}"),
              date=_date.today().strftime("%Y%m%d"),
          )
  ```
  - Depends on: none
  - Expected outcome: `aw backlog set --status ready <item>` appends exactly ONE line to `.aw/records/history.jsonl` with `{id6:<item id>, tree:"backlog", workflow:"backlog", ...}` AND the moved item's inline `## Workflow history` block contains exactly ONE record line (the new transition); `aw backlog check` still conforms.
  - Execution state: pending

### Task group 3: tests + attention-preservation proof

- [ ] E-04 Create `tests/test_history_routing.py` with a `unittest.TestCase` subclass `HistoryRoutingTests` that builds tmp-repo fixtures (in `setUp` via `tempfile.TemporaryDirectory`, `self.root = Path(...)`) and proves BOTH the routing and the attention-preservation invariant. Write EXACTLY these test methods:
  - `test_specs_set_routes_and_slims`: create a conformant spec under `.aw/records/specs/` carrying `- Id: aaa111`, a `- Status: draft`, and a `## Workflow history` block with TWO record lines. Call `specs.run_set` with an `argparse.Namespace(path=<spec>, status="to-review", message="advance", by_human=False, date="20260102", ...)` (fill the gate/evidence attrs it reads with `None`). Assert it returns 0; assert `record_history.read_for(self.root, "aaa111")` has exactly ONE new `tree=="specs"` record with `message=="advance"`; assert the spec's inline `## Workflow history` block now has exactly ONE `HISTORY_RECORD_RE`-matching line.
  - `test_backlog_set_routes_and_slims`: create a backlog item carrying `- Id: bbb222` with a 2-record inline history. Call `backlog.run_set` with `argparse.Namespace(dir=str(self.root), path=<item rel path>, status="ready", message="pick up", apply=True, gate_kind=None, gate_ref=None)`. Assert it returns 0; assert `record_history.read_for(self.root, "bbb222")` has exactly ONE `tree=="backlog"` record; assert the moved item's inline history has exactly ONE record line.
  - `test_slimmed_file_last_history_at_preserved`: take the spec file AFTER `test_specs_set_routes_and_slims`-style slimming (build it inline: a `## Workflow history` with exactly one record line dated `2026-01-02`), parse its history lines with the same walk `attention` uses (`## Workflow history` -> next `## `), and assert `attention_contract.last_history_at(<those lines>) == "2026-01-02"` (i.e. the slim-to-latest-one keeps the derivation intact; spec R6/AC4).
  Then run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: all three test methods pass; full serial suite green (no regressions - notably `aw attention`/`specs check`/`backlog check` still pass because the latest-one inline line is preserved).
  - Execution state: pending

## Project conventions discovered (Step 0)

- History-record grammar: `attention_contract.HISTORY_RECORD_RE = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) .+$")` (attention_contract.py:431); `last_history_at` (attention_contract.py:434) returns the date of the LAST matching record in file order. KEEPING the latest-one inline record line (not removing the section) is what preserves this derivation - this Order MUST NOT delete `## Workflow history`.
- specs writers: `_append_history` (specs.py:224) is the shared inline appender used by `run_set` (specs.py:330, record at specs.py:405), the migrate sibling (specs.py:534), and `run_note` (specs.py:550, record at specs.py:559). Slimming inside `_append_history` covers all three inline paths in one place; the sidecar append is added at the two transition entry points (`run_set`, `run_note`).
- backlog writer: `_reattach_history` (backlog.py:410) currently re-emits ALL prior records + the new one (backlog.py:435); `run_set` (backlog.py:338) has `repo_root` (backlog.py:341) and the parsed `item` with `item.id` the id6 (backlog.py:356). Slim = keep only `new_record`; sidecar append uses `item.id`/`repo_root`.
- Sidecar shape (spec Section 3): ONE GLOBAL append-only JSONL `.aw/records/history.jsonl`, line `{id6,date,tree,workflow,actor,message}`, `tree` in {plans,specs,research,backlog,...}. Owned by the Order 01 `record_history` module; this Order CALLS `append`/`history_path`.
- id6 line is universal: `^- Id:\s*([0-9a-z]{6})\s*$`. specs.py has no id6 reader today, so E-01 adds `_read_id6`; backlog's `item.id` is already parsed.
- repo-root deriver: walk up to a dir holding `.aw`/`.agents`/`.git` (mirrors `_evidence_resolvable`, specs.py:565). backlog already has `resolve_verb_repo_root` (backlog.py:341) so it needs no new deriver.

## Findings

| # | Finding | Consequence |
|---|---------|-------------|
| F1 | `aw attention`'s `last_history_at` reads the inline record DATE (attention_contract.py:434). | This Order KEEPS the latest-one inline line (does not remove the section) so the derivation is byte-for-byte preserved (spec R6/AC4); E-04's `test_slimmed_file_last_history_at_preserved` pins this. |
| F2 | `_append_history` (specs.py:224) is the single shared inline appender for all three specs paths. | Slim ONCE inside `_append_history`; add the sidecar append only at the two transition entry points (`run_set`, `run_note`). |
| F3 | backlog `_reattach_history` re-emits all prior records (backlog.py:435). | Change it to keep only `new_record` (latest-one); the full log is now the sidecar. |
| F4 | specs.py has no id6 reader; backlog already parses `item.id`. | E-01 adds `_read_id6` + `_repo_root_for` to specs.py; backlog reuses `item.id` + `repo_root`. |
| F5 | The Order 01 sidecar writer must exist. | E-02/E-03 CALL `record_history.append`; if a symbol name differs, adapt the call site (not the contract) and note it in V evidence. |

## Proposed changes (ordered, validatable)

1. `specs.py`: add `_read_id6` + `_repo_root_for`, and slim `_append_history` to the latest-one inline line (E-01). 2. `specs.py`: append to the sidecar in `run_set` + `run_note` before the inline append (E-02). 3. `backlog.py`: slim `_reattach_history` to `new_record` + append to the sidecar in `run_set` (E-03). 4. `tests/test_history_routing.py` (routes+slims for specs + backlog, and the `last_history_at`-preserved proof) + full serial suite (E-04).

## Deferred / out of scope (with reason)

- The sidecar store + `append`/`read_for`/`read_all`/`history_path` writer: awhistory Order 01 (this Order consumes it).
- The one-time idempotent migration of legacy inline `## Workflow history` blocks into the sidecar + the `aw` read verb: awhistory Order 03 (this Order routes NEW writes only; it does not backfill history that predates it).
- The `- Managed-by: aw ...` front-matter directive + template/generator changes: spec R5, separate work.
- Any change to `aw attention`/`specs check`/`backlog check`/index derivations: spec R6 leaves those reading inline Status/Set/Id/Order unchanged - this Order deliberately keeps the latest-one inline line so none of them change.

## Scope check

- Over-scope: none - two module edits (`specs.py`, `backlog.py`) + one test file; no index/validator/attention/template change.
- Under-scope: none - the three specs paths (`run_set`, `run_note`, shared `_append_history` slim) and the backlog path are all routed + slimmed, and the attention-preservation invariant (the risk this Order carries) is explicitly proven by `test_slimmed_file_last_history_at_preserved`.

## Required tests / validation

`tests/test_history_routing.py` (E-04, three named methods: specs_set_routes_and_slims, backlog_set_routes_and_slims, slimmed_file_last_history_at_preserved) + the full serial suite (`python3 -m pytest -p no:xdist`). Each V-item pins one E with pasted evidence; the full suite must show `aw attention`/`specs check`/`backlog check` still pass (spec R6/AC4) because the latest-one inline line is preserved.

## Spec / documentation sync

No `AGENTS.md`/README grammar change here (the `- Managed-by:` directive + user-facing docs are spec R5, separate work). No spec transition in this Order: awhistory is a multi-Order Set and the orchestrator (Order 00) advances spec `20260818-1525-02` (draft -> implemented) only on Set completion, after the terminal Order (03) lands.

## Open questions

### OQ-01: slim to the latest-one line, or keep the latest N?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: latest-ONE line, per spec OQ-2 (maintainer decision 2026-08-18): the file keeps the current state's provenance (one line) and the full chronological log lives only in `.aw/records/history.jsonl`. One line is also the minimum that keeps `attention`'s `last_history_at` derivation intact (attention_contract.py:434), so it is both the spec-chosen tail and the derivation-preserving floor. Keeping N>1 would leak more of the narrative back into the cached body for no derivation benefit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import agent_workflows.specs; print('ok')"` printing `ok`, AND a snippet calling `specs._append_history(<lines with a 2-record ## Workflow history>, "- 2026-01-02 reviewed (x): y")` showing the returned list's `## Workflow history` section holds EXACTLY ONE record line (the `2026-01-02` one) with heading + non-record prose preserved.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a snippet building a tmp repo + a conformant spec (`- Id: aaa111`), calling `specs.run_set(Namespace(status="to-review", message="advance", date="20260102", ...))`, then showing (a) `record_history.read_for(root,"aaa111")` gained exactly ONE `tree=="specs"`/`message=="advance"` record and (b) the spec's inline `## Workflow history` has exactly one record line; AND `aw specs check <spec>` printing conformance.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a snippet building a tmp repo + a backlog item (`- Id: bbb222`), calling `backlog.run_set(Namespace(dir=root, path=<item>, status="ready", message="pick up", apply=True, ...))`, then showing `record_history.read_for(root,"bbb222")` gained exactly ONE `tree=="backlog"` record AND the moved item's inline history has exactly one record line; AND `aw backlog check` printing conformance.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `pytest tests/test_history_routing.py -p no:xdist -q` (3 passed) AND the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing no regressions. The `test_slimmed_file_last_history_at_preserved` result MUST show `attention_contract.last_history_at(<slimmed lines>) == "2026-01-02"`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the three touched
files path-scoped (`git commit -- agent_workflows/specs.py agent_workflows/backlog.py tests/test_history_routing.py`;
never `git add -A`), and NEVER pushes. This is a RELEASE BLOCKER (spec 20260818-1525-02, OQ-3) and Order 02
of the awhistory Set: it depends on Order 01 (the `record_history` store/writer) and is depended on by
Order 03 (which backfills the LEGACY inline history + adds the read verb). The plan moves to
`.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is
`pass`; on Set completion the orchestrator (awhistory Order 00) advances spec `20260818-1525-02`.
