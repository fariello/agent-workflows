# IPD: rename backlog's Kind field to Work-Kind and migrate the existing items

- Date: 2026-08-29
- Kind: child
- Concern: Backlog records work nature in a field named `- Kind:`, but that token is already used for two unrelated things elsewhere (an IPD's structural kind, and research's document type), so the field cannot keep this name once plans and specs gain the same concept. The maintainer chose one consistent name. Renaming it touches 88 tracked items in a checkout other agents are committing to, and `backlog.py` also parses a DISTINCT `- Gate-Kind:` field that a careless substring rename would silently corrupt.
- Scope: Rename the on-disk work-nature field from `- Kind:` to `- Work-Kind:` in `backlog.py`, migrate the 88 existing backlog items behind a dual-read window so the tree never stops parsing, and update any documentation naming the old spelling. Excludes adding the field to plans or specs (child 02 owns that), excludes renaming the in-code vocabulary symbol, and excludes any change to `Gate-Kind`.
- Scope-Paths: agent_workflows/backlog.py, .aw/records/backlog, tests/test_backlog_work_kind_rename.py
- Item-Dependencies: none
- Status: to-review
- Set: wkindname
- Order: 1
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 9trlc3
- Blocks-Release: next
- From-Backlog: 1ap48y

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): split out of the approved plan `a6cej0` (now superseded) at the maintainer's direction, carrying its rename task group. The rename itself is the maintainer's decision, made against my recommendation to defer it; their reasoning was that two names for one concept is worse design, and they accepted the larger migration. Measurement done for that decision and carried here: `backlog.py` is the sole consumer, 88 items carry the field, and `Gate-Kind` is a live collision hazard on 2 items.

## Goal

Get backlog onto the field name the whole repo will use, without the tree ever failing to parse and without touching the unrelated gate field that shares the word.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: accept both spellings, then move

- [ ] E-01 Add a DUAL-READ window to `backlog.py` before anything is rewritten: accept `- Work-Kind:` and `- Kind:` on read, preferring the new spelling when both somehow appear. Anchor on the full-line field pattern, never on the bare token `Kind`, because the same module parses a distinct `- Gate-Kind:` field. This lands FIRST so that at no point during the migration does a partially converted tree fail to parse; a plan that rewrites files before dual-read exists has created a window where `aw backlog check` is broken.
  - Depends on: none
  - Expected outcome: an item with the old spelling parses; an item with the new spelling parses; a tree containing BOTH parses and `aw backlog check` is clean; `- Gate-Kind:` still parses unchanged.
  - Execution state: pending

- [ ] E-02 Make `backlog.py` WRITE the new spelling: update the item renderer and the creation path so a newly created item carries `- Work-Kind:`, and update the module's own documented field list. Keep the in-code vocabulary symbol name as it is; only the on-disk field name changes. Decide and RECORD whether the `--kind` CLI flag gains a `--work-kind` spelling with `--kind` retained as an accepted alias; the house pattern for a renamed surface is to accept both rather than break a caller, so prefer the alias unless you find a reason not to.
  - Depends on: E-01
  - Expected outcome: a newly created item carries `- Work-Kind:`; the validator accepts it; the module's documented field list matches what it writes; the CLI flag decision is recorded and both spellings work if the alias was chosen.
  - Execution state: pending

### Task group 2: migrate the corpus, prove nothing else moved

- [ ] E-03 Rewrite the field in the 88 existing items, using a script anchored on the full-line pattern from E-01. Re-verify the `- Gate-Kind:` count is still exactly 2 afterwards and that one such item still parses, because that is the specific corruption this rename can cause and the only way to know it did not happen is to check. Do NOT reformat, reorder, or otherwise touch any other line in these files: they are tracked records and several are being read by concurrent sessions.
  - Depends on: E-02
  - Expected outcome: 88 items carry `- Work-Kind:` and 0 carry `- Kind:`; the `Gate-Kind` count is still 2 and such an item parses; `git diff` shows exactly one changed line per migrated item and no other edits.
  - Execution state: pending

- [ ] E-04 Add `tests/test_backlog_work_kind_rename.py` covering: an item with the NEW spelling parses and validates; an item with the OLD spelling still parses through the dual-read window; a tree containing both spellings passes `aw backlog check`; a newly created item is written with the new spelling; an out-of-vocabulary value is still rejected; and the `Gate-Kind` guard, namely that an item carrying `- Gate-Kind:` parses with its gate intact and that field is never rewritten. Build every case on a throwaway tree rather than the live records, because the live backlog is being modified by other sessions while this runs.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the module passes; the dual-read case fails against an implementation that only accepts the new spelling; the `Gate-Kind` case fails against a substring-based rename.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `backlog.py` is the ONLY module that reads this field. Every `.kind` access outside it belongs to a different concept (a gate kind, an artifact type, a research document kind, or an unrelated change record), so the rename does not ripple into other modules.
- The module parses `- Gate-Kind:` through a shared matcher alongside its own fields, which is precisely why a substring rename is unsafe here rather than merely inelegant.
- The vocabulary is a frozen set of five members and is validated on both read and creation, so the tests already have a rejection path to extend.
- The backlog tree is live shared state: other sessions create and transition items continuously, and three items appeared in it during the graduation sweep that produced this plan. The migration must therefore be a single quick pass, re-counted immediately, not a long interactive edit.
- The superseded `a6cej0` holds the full evidence for the maintainer's decision to rename; cite it rather than re-deriving the argument.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `backlog.py` | The corruption hazard that shapes this whole plan: the module parses a DISTINCT `- Gate-Kind:` field, carried by 2 items, so any rename anchored on the token `Kind` rather than the full-line field pattern produces `Gate-Work-Kind` and silently breaks the gate contract. Every E-item here anchors on the full line, and E-03 and E-04 verify the count afterwards. | `grep -rl '^- Gate-Kind:' .aw/records/backlog/` = 2 |
| F2 | HIGH | `.aw/records/backlog/` | The migration size: 88 tracked items carry the field. The CODE change is one module, so the risk here is file-count and concurrency, not complexity. | `grep -rl '^- Kind:' .aw/records/backlog/` = 88 |
| F3 | MED | `backlog.py` | The rename is CONTAINED because no other module reads the field. This is what makes the plan small in code terms and is worth stating so a reviewer does not go looking for downstream consumers. | the only work-nature reads are inside `backlog.py`; other `.kind` hits are gate, artifact-type, research-kind, or change-record uses |
| F4 | MED | ordering | Dual-read MUST precede the rewrite. Without it, the instant the first item is converted the tree contains a spelling the parser rejects, so `aw backlog check` fails until the last item lands, and any concurrent session reading the backlog sees a broken tree in between. | the parser validates the field on read and rejects an out-of-vocabulary or missing value |

## Proposed changes (ordered, validatable)

1. Accept both spellings on read, anchored on the full-line pattern (E-01).
2. Write the new spelling, and decide the CLI flag alias (E-02).
3. Rewrite the 88 items and re-verify `Gate-Kind` is untouched (E-03).
4. Prove dual-read, creation, rejection, and the `Gate-Kind` guard (E-04).

## Deferred / out of scope (with reason)

- Adding `Work-Kind` to plans and specs is child 02 (`ng2blv`), which declares `executed:9trlc3`. This plan must not touch the schema, the spec contract, or the check engine.
- Renaming the in-code vocabulary SYMBOL. Only the on-disk field name is in question; renaming the symbol would churn child 02's imports for no gain.
- Removing the dual-read window. It stays after the migration as cheap insurance, since an old-spelling item can still arrive from a long-lived branch or a stash. Retiring it is a later cleanup, not this plan's business.
- Any change to `Gate-Kind` itself.

## Scope check

- Over-scope: none. `backlog.py` carries the reader, writer, and validator; the records tree is the corpus being migrated; the test file is new.
- Under-scope, DECLARED: documentation outside these paths may name the old field spelling. Grep the docs tree; if a hit lies outside `Scope-Paths`, STOP and report rather than editing it, and record which files need a follow-up. The orchestrator assigns doc updates to this child, so if the only hits are inside `backlog.py`'s own docstring the obligation is already met.
- The backlog records tree is shared live state. Migrate in one pass, and if another session has an item staged or dirty, do NOT sweep it into your commit; verify the staged set before committing rather than trusting the path scope.

## Required tests / validation

- `tests/test_backlog_work_kind_rename.py` must pass with every case in E-04, built on throwaway trees rather than the live records.
- Falsifiability is specific: the dual-read case must FAIL against an implementation accepting only the new spelling, and the `Gate-Kind` case must FAIL against a substring-based rename. Paste both failures.
- `aw backlog check` must be clean at THREE points, and all three must be pasted: before the migration, DURING it with a tree containing both spellings, and after. The middle one is the whole justification for E-01.
- The existing backlog tests must pass unchanged. Locate them by name first; if one asserts the old field spelling as correct, it is a characterization test of the pre-rename contract and updating it is legitimate, but it must be called out in the record rather than quietly edited, and it must be added to `Scope-Paths` first.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""` (or `make test` / `make test-all`). Do NOT add `-n auto` or a second `-q`.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite during the sweep that authored this at `df731f1`: `2880 passed, 3 skipped, 4 xfailed`. Take your own readings with their HEAD.
- Post-migration counts must be pasted: 88 items with the new spelling, 0 with the old, `Gate-Kind` still 2.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- Update `backlog.py`'s own documented field list as part of E-02, since it enumerates the field by name.
- Grep the docs tree for the old field spelling and fix any hit that falls inside `Scope-Paths`; report anything outside it rather than reaching for it.
- Record in the terminal history that the dual-read window is deliberately RETAINED after the migration, so a later reader does not mistake it for dead code and remove it without thought.

## Open questions

### OQ-01: Keep `--kind` as a CLI alias, or replace it outright?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP IT AS AN ALIAS, add `--work-kind` as the preferred spelling. The house pattern for a renamed surface is to accept the old form rather than break a caller, and the cost here is one line of argument parsing. Breaking `--kind` would fail any script, habit, or agent instruction that uses it, for no benefit beyond tidiness, and the field's on-disk name (the thing that actually needed to be consistent) is already fixed by this plan. E-02 records the decision; if the executor finds the alias genuinely awkward to wire, that is a finding to report rather than a licence to break the flag.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the dual-read implementation showing it anchors on the full-line field pattern and not the bare token. Paste an old-spelling item and a new-spelling item both parsing. Paste `aw backlog check` clean against a tree deliberately containing BOTH spellings, which is the state the migration passes through. Paste an item carrying `- Gate-Kind:` parsing with its gate values intact.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a newly created item showing `- Work-Kind:` on disk. Paste the validator accepting it and rejecting an out-of-vocabulary value. Paste the module's documented field list matching what it now writes. State the OQ-01 flag decision and paste both `--kind` and `--work-kind` working if the alias was kept.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the counts after migration: items carrying `- Work-Kind:` = 88, items carrying `- Kind:` = 0, items carrying `- Gate-Kind:` = 2. Paste `aw backlog check` clean. Paste a `git diff` excerpt for two or three migrated items showing exactly ONE changed line each and no incidental reformatting. Paste `git diff --cached --name-only` before your commit proving no other session's file was swept in.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the full test module passing. Paste FALSIFIABILITY as actual failures: the dual-read case failing when only the new spelling is accepted, and the `Gate-Kind` case failing under a substring-based rename. Confirm every case used a throwaway tree, not the live records.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 4 E-leaves across 2 task groups, well under the thresholds. One concern throughout: move backlog's field to its new name safely. Right-sizing per leaf: E-01 dual-read, E-02 write side, E-03 the corpus rewrite, E-04 the tests.

Open questions: ALL RESOLVED. OQ-01 keeps `--kind` as an alias. The decision to rename at all is the maintainer's, recorded in the superseded `a6cej0`; this plan implements it and does not relitigate it.

Scope fence: touch ONLY `agent_workflows/backlog.py`, the backlog records tree, and the new test file. Do NOT touch the IPD schema, the spec contract, the check engine, or the CLI beyond backlog's own flag (child 02 owns those). Do NOT modify `Gate-Kind` handling. Do NOT rename the in-code vocabulary symbol. If it seems to need more, STOP and report.

CONCURRENCY RULE, not optional: the backlog tree is live shared state and other sessions create and transition items continuously; three new items appeared in it while this plan was being written. Do the migration in ONE pass and re-count immediately. If an item is dirty or staged by someone else, leave it and report it rather than migrating it under them. Before every commit run `git diff --cached --name-only` and unstage anything that is not yours; at least one concurrent session had unrelated files STAGED while this plan was authored, so a path-scoped commit alone is not sufficient protection.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run, and never reuse this plan's recorded baseline as if freshly measured.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
