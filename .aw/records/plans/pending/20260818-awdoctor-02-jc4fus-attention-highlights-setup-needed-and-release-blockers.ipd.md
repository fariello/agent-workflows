# IPD: attention highlights setup-needed and release-blockers

- Date: 2026-08-18
- Kind: child
- Concern: awdoctor Order 02 (TODO items 1 + release-blocker surfacing). The attention board today shows the per-tree classes but says nothing about two cross-cutting facts a human needs at a glance: (a) whether `aw setup` / the `/setup-repo` workflow still needs running in this repo (item 1), and (b) which artifacts are RELEASE BLOCKERS (carry the awrelease Set's `Blocks-Release:` field and are not yet done). Add two top-of-board notices to `aw attention`: a setup-needed notice (shown UNLESS setup has been run or the setup-repo action was dismissed) and a dedicated release-blocker section (populated by scanning items for `Blocks-Release: next|<release-id6>`). This Set CONSUMES the awrelease `Blocks-Release` field; if that field/class is absent it degrades gracefully to no section.
- Scope: ONE edited module `agent_workflows/attention.py` (add notice builders + call them from the top of `render_board` attention.py:436-517, above the class loop; add a release-blocker collector consumed by `run`/`render_board`) + ONE new test file `tests/test_attention_notices.py`. IN: a `setup_needed(repo_root)` predicate reading configured-state (`config.is_configured` per cli.py:4037) and the `setup-repo` action's status (via `actions.ActionManager`, the ledger seeded at cli.py:2029-2034); a `release_blockers(items_or_repo)` collector reading a `Blocks-Release:` bullet; and two top-of-board notice renders. OUT: any change to `scan`'s per-tree records, to `render_json`'s existing keys (attention.py:362), to the compacted class rendering from Order 01, to `attention_contract.py`, or to the awrelease field DEFINITION (that is the awrelease Set's job - this Order only READS it).
- Status: approved
- Approval: 2026-08-18, human ("Approve ALL 21 IPDs now ... Execute everything one at a time using Gemini ... then do it yourself.") after /plan-review (rigorous, opencode Opus 4.8; APPROVE / APPROVE WITH REVISIONS APPLIED).
- Set: awdoctor
- Order: 2
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: jc4fus

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO items 1,33,36,37 (Set awdoctor).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against config.py, actions.py:ActionManager, and cli.py:2029/4037; notice gating and graceful degrade of release-blockers sound; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Give the attention board two cross-cutting highlights at the top: a setup-needed notice (shown until
setup is run or the setup-repo action is dismissed) and a release-blocker section listing artifacts
that carry the awrelease `Blocks-Release:` field and are not done. Both are additive human-board
notices; the JSON key set and the Order-01 compacted class rendering are unchanged, and the
release-blocker path degrades to nothing when the awrelease field is absent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Do EXACTLY the steps below, in order. Edit ONLY `agent_workflows/attention.py`
(add the two predicates/collectors + wire two notices into the TOP of `render_board`) and create ONLY
`tests/test_attention_notices.py`. Do NOT alter the per-tree scan records, the existing JSON keys, or
the Order-01 compacted class rendering. Use 4-space indentation. After each code step, run the matching
V-item command and paste its output. This Order DEPENDS ON the awrelease Set landing the `Blocks-Release`
field; write the release path to degrade gracefully (no field -> no section) so it is safe before then.

### Task group 1: setup-needed notice

- [ ] E-01 Add a `setup_needed(repo_root: Path) -> bool` predicate to `attention.py` (above `render_board`, near attention.py:434) and render a top-of-board notice when it is true. The predicate returns True when the repo is NOT yet configured AND the seeded `setup-repo` action has not been dismissed/completed:
  ```python
  def setup_needed(repo_root: "Path") -> bool:
      """True iff setup still needs running: repo not configured AND the seeded 'setup-repo'
      action (cli install seeds it, cli.py:2029) is still 'open'. Dismissed/completed/absent
      -> False (the human ran-or-dismissed it). Any read failure -> False (never nag on error)."""
      try:
          from agent_workflows import config
          if config.is_configured():
              return False
      except Exception:
          return False
      try:
          from agent_workflows.actions import ActionManager
          mgr = ActionManager(target_repo=str(repo_root))
          # The setup-repo action lives in the STATE actions ledger under open/ when unresolved.
          open_dir = mgr.actions_dir / "open"
          if not open_dir.is_dir():
              return False
          return any(p.name.startswith("setup-repo") for p in open_dir.glob("setup-repo*.md"))
      except Exception:
          return False
  ```
  Then at the TOP of `render_board` (immediately after the `drift` block ends, before the `by_class` loop at attention.py:462), accept a new keyword-only param `setup_notice: bool = False` and, when true, prepend:
  ```python
  if setup_notice:
      lines.append("NOTE: setup not complete - run `aw setup` then the `/setup-repo` workflow.")
      lines.append("")
  ```
  In `run` (attention.py:525) compute `setup_notice = (fmt != "json") and not check and attention.setup_needed(repo_root)` and pass it to `render_board` (attention.py:579). The notice is HUMAN-board only: never in `--check`, never in JSON.
  - Depends on: none
  - Expected outcome: on an unconfigured repo with an open `setup-repo` action, the human board starts with the `NOTE: setup not complete ...` line; on a configured repo (or after the action is dismissed) the notice is absent; `--format json` and `--check` never show it.
  - Execution state: pending

### Task group 2: release-blocker section

- [ ] E-02 Add a `Blocks-Release:` reader + a release-blocker section. The awrelease Set defines a `- Blocks-Release: next|<release-id6>` bullet on any artifact that must ship before a release; this Order CONSUMES it. Add a collector to `attention.py` (near attention.py:434):
  ```python
  _BLOCKS_RELEASE_RE = re.compile(r"(?m)^- Blocks-Release:\s*(next|[0-9a-z]{6})\s*$")

  def release_blockers(repo_root: "Path", items: "List[Item]") -> "List[Tuple[str, str]]":
      """Return (path, target) for each scanned item whose file carries a `Blocks-Release:`
      bullet AND is not in the DONE class. Degrades to [] when the field is absent everywhere
      (awrelease not yet landed). Reads each item's file once; any read failure skips that item."""
      out: List[Tuple[str, str]] = []
      for it in items:
          if it.attention_class == A.DONE:
              continue
          try:
              text = (repo_root / it.path).read_text(encoding="utf-8")
          except OSError:
              continue
          m = _BLOCKS_RELEASE_RE.search(text)
          if m:
              out.append((it.path, m.group(1)))
      return sorted(out)
  ```
  (Add `import re` and `Tuple` to the imports if not already present - `Tuple` is already imported at attention.py:21; add `re`.) Then in `render_board` accept a keyword-only param `blockers: "Optional[List[Tuple[str, str]]]" = None` and, when it is a non-empty list, render a dedicated section at the top (after the setup notice, before the class loop):
  ```python
  if blockers:
      lines.append(f"## release-blockers ({len(blockers)})")
      for path, target in blockers:
          lines.append(f"- {path} (blocks {target})")
      lines.append("")
  ```
  In `run` compute `blockers = attention.release_blockers(repo_root, items) if (fmt != "json" and not check) else None` and pass it in. When the awrelease field is absent everywhere, `release_blockers` returns `[]`, `blockers` is falsy, and NO section renders (graceful degrade).
  - Depends on: E-01
  - Expected outcome: with an item carrying `- Blocks-Release: next` that is not done, the human board shows a `## release-blockers (1)` section listing it; with no such field anywhere, no section appears; JSON/`--check` never show it.
  - Execution state: pending

### Task group 3: tests

- [ ] E-03 Create `tests/test_attention_notices.py` with a `unittest.TestCase` subclass `AttentionNoticesTests`. Build a tmp repo fixture with `tempfile.TemporaryDirectory` and write EXACTLY these methods:
  - `test_setup_notice_shown_when_unconfigured_and_open`: monkeypatch/arrange so `config.is_configured()` is False and an open `setup-repo` action exists (or patch `attention.setup_needed` to return True), render the board with `setup_notice=True`, assert the output starts with the `NOTE: setup not complete` line.
  - `test_setup_notice_absent_when_configured`: with `setup_notice=False` (configured, or action dismissed), assert the `NOTE: setup not complete` line is absent.
  - `test_setup_notice_never_in_json`: assert `attention.render_json(items, [])` contains no `setup not complete` text and no new top-level key beyond the existing `{schema_version,mapping_version,valid,items,violations}`.
  - `test_release_blocker_section`: build one non-done Item whose file carries `- Blocks-Release: next`, compute `release_blockers(root, items)`, render with that `blockers` list, assert the board contains `## release-blockers (1)` and lists the item with `(blocks next)`.
  - `test_release_blocker_absent_degrades`: with NO `Blocks-Release:` field on any item, assert `release_blockers(root, items) == []` and the rendered board contains NO `release-blockers` section (graceful degrade proving the awrelease dependency is optional).
  Then run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02
  - Expected outcome: all five methods pass; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Bare `aw` uses `config.is_configured()` (cli.py:4037) to decide setup-vs-status; the same predicate answers "is setup needed?".
- The install path SEEDS a `setup-repo` action in the STATE actions ledger via `ActionManager.create_action(action_id="setup-repo", ...)` (cli.py:2029-2034); `attention.scan` already reads that ledger's `open/completed/dismissed/superseded` dirs (attention.py:166-201), so the setup-repo action's status is discoverable from `mgr.actions_dir`.
- The attention board separates human vs machine output by `fmt`/`check` in `run` (attention.py:558-580); notices belong on the HUMAN path only, so JSON/`--check` stability is preserved by gating on `fmt != "json" and not check`.
- `A.DONE` is the terminal attention class (attention_contract.py); a release blocker that is done no longer blocks, so `release_blockers` skips `A.DONE`.
- `Tuple` is already imported (attention.py:21); `re` may need adding.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Configured-state + the seeded setup-repo action are both already available. | The setup-needed notice composes existing signals; no new state store. |
| F2 | Notices live only on the human path (`fmt != "json" and not check`). | JSON + `--check` stay byte-stable; machines are unaffected. |
| F3 | The `Blocks-Release` field is OWNED by the awrelease Set, not this one. | This Order READS it and degrades to no section when absent, so it is safe to land before awrelease. |

## Proposed changes (ordered, validatable)

1. `setup_needed` predicate + top-of-board setup notice wired through `run`/`render_board` (E-01). 2. `Blocks-Release` reader + `release_blockers` collector + release-blocker section, degrading gracefully (E-02). 3. `tests/test_attention_notices.py` + full suite (E-03).

## Deferred / out of scope (with reason)

- DEFINING the `Blocks-Release` field grammar and the release-id6 lifecycle: OWNED by the awrelease Set - this Order only consumes the field.
- The aggregated `aw doctor` verb: awdoctor Order 03.
- Any change to per-tree scan records, existing JSON keys, or the Order-01 class rendering: explicitly OUT.

## Scope check

- Over-scope: none - one edited module (additive notices) + one new test file.
- Under-scope: none - both notices are implemented, gated to the human path, and the release path is proven to degrade when the awrelease field is absent (E-03 `test_release_blocker_absent_degrades`).

## Required tests / validation

`tests/test_attention_notices.py` (E-03, five named methods) + the full serial suite. Each V-item pins one E; V-03 proves JSON/`--check` stability AND the graceful-degrade of the release path.

## Spec / documentation sync

No spec transition here. No AGENTS.md change: the notices are a human-facing readout and the machine contract (JSON/`--agent`) is unchanged. The awrelease field is documented by the awrelease Set, not here.

## Open questions

### OQ-01: this Order consumes the awrelease `Blocks-Release` field - can it land before awrelease?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: YES - Cross-references note the dependency on the awrelease Set for the `Blocks-Release` field/class. E-02's `release_blockers` degrades to `[]` (no section) when the field is absent everywhere, and E-03 `test_release_blocker_absent_degrades` proves it. So this Order is SAFE to land before awrelease; when awrelease lands the section auto-populates with no further change. The dependency is documented, not blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a render (with `setup_notice=True`) showing the board begins with the `NOTE: setup not complete` line, and a second render with `setup_notice=False` showing it absent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `release_blockers(root, items)` returning one `(path, "next")` for an item carrying `Blocks-Release: next`, and the rendered board showing the `## release-blockers (1)` section; plus the empty-field case returning `[]` and NO section.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_attention_notices.py -p no:xdist -q` (5 passed) AND the tail of the full serial suite (`python3 -m pytest -p no:xdist`) showing no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the edited
`agent_workflows/attention.py` and the new `tests/test_attention_notices.py` path-scoped (never
`git add -A`), never pushes, and the plan moves to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every V-item is `pass`. Order 02 of awdoctor;
depends on Order 01's compacted board and on the awrelease Set for the `Blocks-Release` field (consumed,
degrading gracefully when absent).
