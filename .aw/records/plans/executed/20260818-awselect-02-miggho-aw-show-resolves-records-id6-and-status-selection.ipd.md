# IPD: aw show resolves records id6 and status selection

- Date: 2026-08-18
- Kind: child
- Concern: awselect Order 02 (TODO items 16, 18). Today `aw show pp6y76` FAILS with "Action 'pp6y76' not found" because `_run_show` (cli.py:3514) only searches the operational action ledger (`ActionManager.find_action_file`, actions.py:136), which knows nothing about the RECORDS id6 namespace (plans/specs/research/backlog/...). Fix `aw show` to FIRST resolve the token as a records artifact using the Order-01 selector resolver, printing the matching record file(s), and only fall back to the action ledger if no records artifact matches. Also clarify the confusing "Action ID or ID@generation" help text.
- Scope: `agent_workflows/cli.py` `_run_show` + the `show` parser help ONLY, plus a test. IN: make `_run_show` try `selectors.resolve_selectors` across the record types before the action-ledger lookup; update the `show` positional help; a test proving `aw show <id6>` finds a records artifact and the action-ledger path still works. OUT: the selector module itself (Order 01, already built); the cross-cutting verbs (awcmdsurf); any change to ActionManager.
- Status: executed
- Set: awselect
- Order: 2
- Highest E allocated: 04
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: miggho

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade detail from investigation (_run_show cli.py:3514; show parser cli.py:1246-1251; resolve_verb_repo_root cli.py:2813; selectors.resolve_selectors from awselect Order 01).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE. Records-first _run_show (via selectors) with action-ledger fallback; verified _run_show:3514, ActionManager.find_action_file:136, resolve_verb_repo_root; uses an inline record-types tuple (no cross-Set artifact_types dependency). No findings.
- 2026-08-18 executed (opencode Opus 4.8): E-01..E-04 performed, V-01..V-04 pass; code committed; aw show pp6y76 resolves the records artifact live; full serial suite 1038 passed 1 skipped.

## Goal

Make `aw show <token>` resolve a RECORDS artifact (by id6, setid, filename fragment, or status) via the
Order-01 selector module and print it, falling back to the action ledger only when no records artifact
matches - so `aw show pp6y76` prints the plan/spec/etc. with that id6 instead of erroring. Fix the
misleading help text.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Order 01 (`agent_workflows/selectors.py` with `resolve_selectors`) MUST already be
executed and present. Edit ONLY `agent_workflows/cli.py` and add ONE test file. Do NOT change
`actions.py`. Preserve the existing action-ledger behavior as a fallback.

### Task group 1: teach _run_show to resolve records first

- [x] E-01 In `agent_workflows/cli.py`, replace the body of `_run_show` (currently cli.py:3514-3525) so it FIRST tries the records selector, THEN falls back to the action ledger. Use this exact new body (keep the function name + signature `def _run_show(args, term)`):
  ```python
  def _run_show(args: argparse.Namespace, term: Term) -> int:
      from agent_workflows import selectors
      from agent_workflows.project_context import resolve_verb_repo_root

      ref = args.action_ref
      # 1. Try to resolve the token as a RECORDS artifact (id6 | setid | filename | status),
      #    searching each record type; print every match.
      repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
      record_types = ("plans", "specs", "research", "backlog", "prompts", "walkthroughs", "roadmaps")
      hits = []
      for rt in record_types:
          hits.extend(selectors.resolve_selectors(repo_root, rt, [ref]))
      # de-dup preserving order
      seen = set()
      unique = [p for p in hits if not (str(p) in seen or seen.add(str(p)))]
      if unique:
          for p in unique:
              term.heading(str(p))
              print(p.read_text(encoding="utf-8"))
          return 0
      # 2. Fallback: the operational action ledger (unchanged behavior).
      from agent_workflows.actions import ActionManager, ActionError
      try:
          mgr = ActionManager()
          _status, path = mgr.find_action_file(ref)
          print(path.read_text(encoding="utf-8"))
          return 0
      except ActionError as exc:
          term.status("fail", f"No records artifact or action matched '{ref}'.")
          return 1
  ```
  - Depends on: none
  - Expected outcome: `aw show <a records id6>` prints that record's file; `aw show <an action id>` still prints the action doc; an unknown ref prints the combined "No records artifact or action matched" failure and returns 1.
  - Execution state: performed
- [x] E-02 Add a `--dir` option to the `show` parser so the records lookup can be pointed at a specific repo (mirroring other verbs). In `_build_parser`, at the `show` parser (cli.py:1246-1251), after the `action_ref` positional add: `p_show.add_argument("--dir", default=None, help="Repo root to search for a records artifact (default: current directory).")`.
  - Depends on: none
  - Expected outcome: `aw show <id6> --dir <path>` searches that repo's records.
  - Execution state: performed

### Task group 2: fix the help text (item 16)

- [x] E-03 Update the `show` help strings to reflect the new dual behavior. Change the parser `help=` (cli.py:1249) from `"Inspect an action document by ID or ID@generation."` to `"Inspect a record or action by id6, set id, filename, or status (records first, then the action ledger)."` and change the `action_ref` positional help (cli.py:1251) from `"Action ID or ID@generation."` to `"A selector: an id6 (e.g. pp6y76), a set id, a filename fragment, a status, or an action id[@generation]."`. Also update `_DESCRIPTIONS["show"]` (cli.py:240-243) to the same effect (one or two clear sentences for a layperson AND an agent).
  - Depends on: none
  - Expected outcome: `aw show --help` describes resolving a record OR an action by the listed selector forms; no mention of only "action document".
  - Execution state: performed

### Task group 3: test

- [x] E-04 Add `tests/test_show_records.py` with a `unittest.TestCase` `ShowRecordsTests` that, in a tmp repo fixture, writes a plan `.aw/records/plans/pending/20260101-demo-01-pp6y76-example.ipd.md` containing `- Id: pp6y76` and a body marker line `MARKER_SHOW_BODY`, then invokes the CLI in-process (build args via the parser or call `_run_show` with a small args stub carrying `action_ref="pp6y76"` and `dir=<repo>`) and asserts: (a) return code 0 and the printed output contains `MARKER_SHOW_BODY` (records path works); (b) `action_ref="nonexistent-xyz"`, `dir=<repo>` returns 1 (no match). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: both assertions pass; full serial suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `_run_show` (cli.py:3514) currently delegates ONLY to `ActionManager.find_action_file` (actions.py:136), which globs `<STATE>/actions/{open,...}/<id>-v*.md` - the STATE ledger, NOT the RECORDS id6 namespace. That is exactly why `aw show pp6y76` fails today.
- The Order-01 module `agent_workflows/selectors.py` provides `resolve_selectors(repo_root, record_type, tokens) -> List[Path]`; this Order consumes it.
- Repo-root helper: `project_context.resolve_verb_repo_root(explicit_dir)` (used at cli.py:2813/2821).
- Do NOT depend on `artifact_types.py` (that is created by the awcmdsurf Set, a different Set); use the small inline `record_types` tuple in E-01 instead so this Order is self-contained.
- Keep the action-ledger fallback so `aw show <action-id>` and `<action-id>@generation` still work.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | show is hard-wired to the action ledger. | The fix is a records-first lookup with the ledger as fallback; no ActionManager change. |
| F2 | The Order-01 resolver already resolves all selector forms. | show gains id6/setid/filename/status resolution for free by calling it. |
| F3 | artifact_types.py is owned by another Set. | Use an inline record-types tuple here to stay self-contained (no cross-Set dependency). |

## Proposed changes (ordered, validatable)

1. Records-first `_run_show` body with ledger fallback (E-01). 2. `--dir` on show (E-02). 3. Help-text fix (E-03). 4. `tests/test_show_records.py` + full suite (E-04).

## Deferred / out of scope (with reason)

- The selector module: Order 01 (already built). Cross-cutting verbs: awcmdsurf.
- Any change to ActionManager / the action ledger: OUT (kept as the fallback).

## Scope check

- Over-scope: none - only `_run_show` + the show parser help + a test.
- Under-scope: none - records-first resolution (all selector forms via Order 01) + ledger fallback + help fix are covered.

## Required tests / validation

`tests/test_show_records.py` (E-04) + the full serial suite. Each V-item pins one E.

## Spec / documentation sync

Help text updated (E-03). No AGENTS.md change. No spec transition here (orchestrator advances the spec).

## Open questions

### OQ-01: if a token matches MULTIPLE records (e.g. a status), print all or refuse?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: PRINT ALL matches (each under a `term.heading(path)` banner), per E-01. `show` is a read; printing every match of a status/setid selector is the useful behavior. An id6 normally matches one file, so the common case prints one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste an `aw show <records id6>` run printing the record body (return 0), and an unknown-ref run returning 1 with the combined failure message.
  - Observed evidence: aw show pp6y76 prints the records artifact (awretrofit orchestrator) rc=0; an unknown ref rc=1 with the combined message (test_show_records + live smoke).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `aw show <id6> --dir <repo>` resolving against that repo.
  - Observed evidence: aw show <id6> --dir <repo> resolves against that repo (test uses dir=<tmp repo>).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `aw show --help` showing the new help + positional description (no "action document"-only wording).
  - Observed evidence: aw show --help shows 'record or action ... selector ... --dir'; no action-document-only wording (verified).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `pytest tests/test_show_records.py -p no:xdist -q` (passing) + the full serial suite tail (no regressions).
  - Observed evidence: pytest tests/test_show_records.py -> 2 passed; full serial suite 1038 passed, 1 skipped.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the changed
`cli.py` + the new test file path-scoped (never `git add -A`), never pushes, and the plan moves to
`.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V is
`pass`. Order 02 of awselect; depends on Order 01 (the selector module).
