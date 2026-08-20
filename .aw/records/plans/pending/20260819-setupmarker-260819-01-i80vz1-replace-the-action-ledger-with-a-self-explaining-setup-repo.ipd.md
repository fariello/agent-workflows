# IPD: replace the action ledger with a self-explaining setup-repo-needed marker and kill write-on-read

- Date: 2026-08-19
- Concern: The `ActionManager` operational-action ledger (`.aw/state/actions/*`) exists to hold ONE hardcoded reminder (the post-install `setup-repo` recommendation), yet it is a full generalized lifecycle system nobody will remember exists. Worse, `ActionManager.__init__` eagerly `mkdir`s `.aw/state/actions/*` + `.aw/state/history`, and a READ-ONLY path (`attention.scan` -> `aw status`/`aw attention`, attention.py:175) constructs one PER SCANNED REPO, so `aw status` silently stamped an empty `.aw/state/` into ~26 configured repos (verified + reproduced). Root cause: write-on-read + an over-built subsystem for a single derivable reminder.
- Scope: DELETE the action ledger (the `agent_workflows/actions.py` ActionManager + its attention source + the complete/dismiss/reopen/history verbs) and REPLACE the setup reminder with a single self-explaining, gitignored, per-repo marker `repo/.aw/setup-repo-needed.md`: `aw install` writes it, `aw setup` removes it, the user may delete it to dismiss, and `aw attention`/`aw doctor` DERIVE "setup pending" from its presence (read-only, never create). KEEP the install-history audit log (`state/install.json` + `state/history/installs.jsonl`) - that is a genuine append-only artifact with no on-disk-derivable equivalent. Then clean up the ~26 already-stamped `.aw/state/` litter dirs. This REVERSES previously-shipped code (the action ledger, spec 20260809-2211-01) by maintainer decision, because the ledger is over-built for its single use and caused a write-on-read defect.
- Kind: child
- Status: reviewed
- Set: setupmarker-260819
- Order: 1
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: i80vz1

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - delete the action ledger (write-on-read + over-built for one reminder), replace with a self-explaining gitignored repo/.aw/setup-repo-needed.md marker, keep install-history, clean up the stamped litter.
- 2026-08-19 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (E-04 rewrite-not-extend setup_needed, which currently reads the ledger being deleted), PR-002 (concurrency caution added to the gate - a sibling instance is reviewing another Set), PR-003 (E-06 delete-vs-adapt ledger tests clarified). All anchors verified against code (engine .aw/.gitignore writer 3770/4392; install create_action cli.py:2129-2130; attention action-scan 171-210; _ACTIONS_MAP attention_contract:238/267; verbs cli.py:4040-4079/5026-5032; DurableStateClass.ACTIONS record_producers:108/151; setup_needed attention.py:506). Structural preflight conforming (author + review-finalize). Readiness: GO - PENDING HUMAN APPROVAL.

## Goal

Kill the write-on-read bug at its root by deleting the action ledger, and satisfy its one real purpose (persist + surface the "run setup here" reminder) with a self-explaining, gitignored, per-repo marker file that install writes and setup/deletion clears, while attention/doctor DERIVE the pending state read-only.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: the marker

- [ ] E-01 In `agent_workflows/engine.py`, add `SETUP_MARKER_PATH = ".aw/setup-repo-needed.md"` + `_SETUP_MARKER_TEMPLATE`, a self-EXPLAINING body (a reader who opens it understands it fully): title "agent-workflows: setup not yet run in this repo"; states it is a REMINDER not configuration; that `aw` was installed but `aw setup` has not run here; WHAT TO DO (run `aw setup`, OR delete this file to dismiss); that running `aw setup` removes it automatically; that it is per-machine + gitignored (never committed) + safe to delete. Add helpers `write_setup_marker(repo_root)` (write the file + ensure `.aw/.gitignore` ignores `setup-repo-needed.md`) and `remove_setup_marker(repo_root)` (unlink if present). Reuse the awgitignore `.aw/.gitignore` writer pattern (add a `setup-repo-needed.md` line alongside `records/*/untracked/`).
  - Depends on: none
  - Expected outcome: `write_setup_marker` creates a self-explaining `.aw/setup-repo-needed.md` + a `.aw/.gitignore` line for it; `remove_setup_marker` removes it; both idempotent.
  - Execution state: pending

- [ ] E-02 Wire the marker into the lifecycle. In `_run_install` (cli.py, where it currently seeds the setup-repo action ~cli.py:2129), REPLACE the `ActionManager.create_action("setup-repo")` call with `engine.write_setup_marker(repo_root)`. In the setup path (`aw setup` / `_run_setup`), call `engine.remove_setup_marker(repo_root)` on success. KEEP the `record_install_history(...)` call (install audit log stays).
  - Depends on: E-01
  - Expected outcome: `aw install` drops `.aw/setup-repo-needed.md`; `aw setup` removes it; install history still recorded.
  - Execution state: pending

### Task group 2: delete the ledger (kill write-on-read)

- [ ] E-03 Remove the action-ledger attention source (the write-on-read culprit): delete the `ActionManager` scan block in `attention.py` (~171-215, the "External AW operational actions scan") and its `actions` tree handling; remove the `actions` entry from `attention_contract.py` (`_ACTIONS_MAP` + the `CLASS_MAPS["actions"]` + any tracked-tree/`class_of("actions",...)`). Attention no longer reads or creates `.aw/state/actions/`.
  - Depends on: none
  - Expected outcome: `attention.scan` on a fresh dir creates NO `.aw/` (reproduce the old bug scenario -> now clean); no `actions` tree in the attention contract.
  - Execution state: pending

- [ ] E-04 REWRITE the "setup pending" signal to derive from the marker (PR-001): the existing `attention.setup_needed` (attention.py:506, added by awdoctorfix-02) currently keys off the ACTION LEDGER (an open `setup-repo` action) - which E-03 deletes - so it will BREAK unless rewritten. Change `setup_needed(repo_root)` to return True iff `repo/.aw/setup-repo-needed.md` exists (read-only presence check; never create). Verify every consumer of `setup_needed` still resolves: the `aw attention` human-board notice (awdoctorfix-02) and the `aw doctor` setup surfacing (awdoctorfix-03) - `setup_needed` lives ONLY in attention.py, so doctor imports/derives from it; confirm doctor's call still works after the rewrite. Never create the marker from any read path.
  - Depends on: E-01,E-03
  - Expected outcome: `setup_needed` returns True iff the marker file exists; with the marker present, `aw attention`/`aw doctor` note setup is pending; with it absent, they are silent; neither writes anything; no consumer of `setup_needed` references the deleted ledger.
  - Execution state: pending

- [ ] E-05 Delete the action-ledger CLI surface + module. Remove the `complete`/`dismiss`/`reopen`/`history` (action) verbs (parsers cli.py:1274-1289 + dispatch cli.py:5026-5033 + `_run_complete`/`_run_dismiss`/`_run_reopen`/`_run_action_history`); `todo` already routes to attention (awcmdsurf-04) so leave it. Delete `agent_workflows/actions.py`'s ActionManager/ActionDocument/create_action/transition_action/list_actions + the `state/actions` mkdir; KEEP `record_install_history` + `_redact_details` (move them to a small `agent_workflows/install_history.py` if that leaves actions.py empty, else keep a slimmed actions.py holding only install-history). Update `record_producers.py` `DurableStateClass.ACTIONS` (drop the actions class; keep TRANSACTIONS + install state) and any `_record_scaffold_dirs`/scaffold that materializes `state/actions/`.
  - Depends on: E-02,E-03,E-04
  - Expected outcome: no `complete`/`dismiss`/`reopen`/action-`history` verbs; no `state/actions/` scaffolded on install; install-history preserved; `aw --help` clean; `python3 -c "import agent_workflows.cli"` works.
  - Execution state: pending

### Task group 3: tests + cleanup

- [ ] E-06 Update/replace tests: `tests/test_actions.py` - DELETE the ledger-specific tests (ActionManager/ActionDocument/create_action/transition/list are gone); KEEP or move the `record_install_history`/`_redact_details` tests to match wherever E-05 leaves install-history. `tests/test_attention.py`/`test_attention_stem.py`/`test_acceptance_matrix.py` - drop the actions-tree expectations (the `actions` tree/`aw-state/actions` logical paths no longer appear). `tests/__init__.py` - remove any actions seeding. Add `tests/test_setup_marker.py`: `write_setup_marker` creates a self-explaining gitignored marker; `remove_setup_marker` clears it; `setup_needed` derives from the marker (True iff present); `attention.scan` on a fresh dir creates NO `.aw/` (write-on-read regression guard); the install->marker + setup->removal cycle (via the engine helpers or the verbs). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04,E-05
  - Expected outcome: suite green; a direct regression test proves no write-on-read; marker lifecycle covered.
  - Execution state: pending

- [ ] E-07 Clean up the already-stamped litter (now STICKY, since no writer re-creates it): remove the empty `.aw/state/` (actions-only) scaffolding from the configured repos where `.aw/` is empty scaffolding + untracked (the ~26 identified). Enumerate from config, verify each `.aw/` has NO files and is git-untracked, remove only those, never touch agent-workflows itself or any repo with real `.aw/` content. Paste the removed list + a final `aw status` proving no phantom split-brain remains and re-running `aw status` does NOT re-stamp (the bug is fixed).
  - Depends on: E-05
  - Expected outcome: the ~26 stamped `.aw/state/` dirs are gone and STAY gone after `aw status`; no repo with real content touched.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The ledger is over-built for one hardcoded `setup-repo` reminder (only `create_action("setup-repo")` at cli.py:2129 ever creates one; no generic create verb). Maintainer decision: delete it.
- Write-on-read root cause: `ActionManager.__init__` eager mkdir (actions.py:130-131) reached by `attention.scan` (attention.py:175) per scanned repo; reproduced stamping `.aw/state/` into a fresh dir.
- `repo/.aw/` is framework-owned (awgitignore-01); `.aw/.gitignore` already exists as a framework deliverable and can carry a `setup-repo-needed.md` line. This keeps the marker per-repo (NOT records-backend-redirected) and per-machine (gitignored) - the two properties the reminder needs.
- Install-history (`state/install.json` + `state/history/installs.jsonl`, record_install_history) is a genuine append-only audit with no derivable equivalent - KEEP.
- `todo` already routes to `attention` (awcmdsurf-04); only complete/dismiss/reopen/history are action-ledger-only.
- "setup pending" is derivable (marker presence) - prefer derived surfacing over a stored ledger (the artifact-vs-derive rule); the marker persists only the visible reminder + the dismissal (delete = dismiss).

## Findings

The action ledger fails three tests we agreed on: (1) it stores state that should be derived/visible-on-disk, and (2) it is a subsystem neither maintainer nor agent will remember, which already produced a silent write-on-read defect mutating ~26 repos. Replacing it with a self-explaining `repo/.aw/setup-repo-needed.md` marker + derivation is simpler, discoverable, backend-independent, and removes the bug at the root.

- (3) THE DECISIVE ARCHITECTURAL REASON (recorded so we do not relitigate it later): the BACKLOG tier is ALREADY the general "per-project operational task with a lifecycle" machinery. The action ledger is therefore a REDUNDANT DUPLICATE PATH (violates P8 single-source-of-truth + rubric C "use existing canonical mechanisms, avoid duplicate paths"). This redundancy holds INDEPENDENT of whether an item is git-tracked or machine-local: "tracked-ness" is a PLACEMENT property of a records class (resolved via the backend + gitignore the framework owns), NOT an intrinsic capability that only the ledger provides. The original spec (20260809-2211-01 problem 4) justified the ledger as "a native source for AW actions stored OUTSIDE the tracked tree," but that rationale predates the backend/placement system and the consolidation on backlog + attention as the general surfaces; in today's architecture "store it outside the tracked tree" is a backlog placement choice, not a reason for a second class. So: keeping the ledger would mean maintaining TWO general operational-task systems whose only claimed difference (storage location) is a config knob backlog can already vary. The one reminder that actually exists (`setup-repo`) is not general at all - it is a single, purpose-built, derivable install reminder, best served by the `.aw/setup-repo-needed.md` marker, not by a general ledger. If a SECOND distinct operational reminder kind ever appears, it belongs in BACKLOG (with whatever placement it needs), never in a revived ledger.

- PR-001 (MEDIUM, IN-SCOPE, /plan-review): E-04 originally said "extend" `setup_needed`, but the existing `setup_needed` (attention.py:506) keys off the ACTION LEDGER that E-03 deletes, so it would BREAK. Rewrote E-04 to REWRITE `setup_needed` to derive from the marker + verify the `aw doctor` consumer (setup_needed lives only in attention.py). Remediation risk Low. Decision: FIXED.
- PR-002 (MEDIUM, IN-SCOPE, /plan-review): the plan mutates shared modules + deletes a subsystem while a concurrent agent instance is reviewing another Set; the gate lacked a concurrency caution. Added a CONCURRENCY note to the execution gate (do not execute while another instance edits these files; re-stage on hook-restore). Decision: FIXED.
- PR-003 (LOW, IN-SCOPE, /plan-review): E-06 was ambiguous about adapting vs deleting ledger tests. Clarified: DELETE ledger-specific tests, KEEP/move install-history tests. Decision: FIXED.

## Proposed changes (ordered, validatable)

1. Marker template + write/remove helpers + gitignore line.
2. Wire into install (write) + setup (remove); keep install-history.
3. Remove the action attention source + contract entry (kills write-on-read).
4. Derive "setup pending" in attention/doctor from the marker.
5. Delete the action CLI verbs + ActionManager module (keep install-history).
6. Tests incl. a write-on-read regression guard.
7. Sticky cleanup of the stamped litter.

## Deferred / out of scope (with reason)

- A general operational-action system for FUTURE reminder kinds: deliberately NOT kept (maintainer + agent agreed we would not remember it; add a purpose-built marker if a second kind ever appears).
- The install-history audit log: kept as-is (genuine artifact), only relocated if actions.py would otherwise be empty.

## Scope check

- Over-scope: none - all edits serve deleting the ledger + the marker replacement + the cleanup.
- Under-scope: does not add new reminder kinds (none exist).

## Required tests / validation

`tests/test_setup_marker.py` (marker lifecycle + write-on-read regression) + updated actions/attention/acceptance tests; full serial suite green; `aw status` cleanup proof (no re-stamp).

## Spec / documentation sync

Update spec `20260809-2211-01` (the layout/state/action-ledger spec): record that the per-project operational-action LEDGER is superseded by a derived "setup pending" signal + a `repo/.aw/setup-repo-needed.md` marker (nothing shipped since pre-.aw/, so supersede, not migrate); install-history state is retained. Note the reversal in the spec history.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The design (delete ledger + marker + derive + keep install-history + cleanup) was settled interactively with the maintainer; no open decision. If a SECOND reminder kind ever arises it is a future purpose-built marker, explicitly out of scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `write_setup_marker` on a tmp repo creates `.aw/setup-repo-needed.md` whose body explains itself (reminder-not-config, run `aw setup` or delete to dismiss, gitignored, safe to delete) and a `.aw/.gitignore` line ignoring it; `remove_setup_marker` clears it; both idempotent.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `aw install` on a tmp repo drops `.aw/setup-repo-needed.md`; `aw setup` removes it; `state/history/installs.jsonl` still gets the install event.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `attention.scan(Path(tmpdir))` on a fresh dir creates NO `.aw/` (the exact old repro now clean); no `actions` key in `attention_contract.CLASS_MAPS`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: with the marker present `aw attention`/`aw doctor` note "setup pending"; absent -> silent; neither writes anything (fresh-dir scan stays empty).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `aw complete`/`aw dismiss`/`aw reopen` are gone (invalid choice); `aw install` scaffolds no `state/actions/`; `record_install_history` still importable + works; `python3 -c "import agent_workflows.cli"` OK.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest tests/test_setup_marker.py tests/test_actions.py tests/test_attention.py -p no:xdist -q` green; full serial suite tail pasted; the write-on-read regression test is present + passing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the removed-litter list pasted; the config-driven enumeration (walk the configured repos, `-maxdepth 2 -type d -name .aw`) shows only agent-workflows + any real installs; `aw status` run TWICE shows no phantom split-brain and no re-stamp between runs.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 7 E items, but they are one indivisible change - deleting the action ledger safely REQUIRES the marker replacement (E-01/02), the read-path derivation (E-03/04), the CLI/module removal (E-05), tests (E-06), and the now-sticky cleanup (E-07) to land together; splitting would leave the write-on-read bug half-fixed or the reminder unsurfaced between Orders.

Execution contract: commit only files changed by this plan, path-scoped, never push. The E-07 cleanup DELETES untracked empty `.aw/state/` dirs from OTHER configured repos - it MUST enumerate + verify (no files, git-untracked) each before removing, never touch agent-workflows or any repo with real `.aw/` content, and paste the exact removed list. Run the full serial suite and paste the actual runner output as V evidence.

CONCURRENCY (PR-002): this plan mutates shared modules (`attention.py`, `attention_contract.py`, `cli.py`, `record_producers.py`, `actions.py`) and deletes a subsystem. Do NOT execute it while another agent instance is concurrently editing or reviewing those files (e.g. an in-flight `/plan-review` of another Set). The executor MUST confirm the working tree is quiet (no other instance mid-write) before starting, to avoid the stash/restore commit races observed this session; if a commit is restored by the pre-commit hook, re-stage and re-commit rather than proceeding on a half-committed state.

On completion, lint --phase pre-transition while approved, then flip to executed + executed history line + git mv + post-transition lint. Do not mark executed until every V item is verified with concrete evidence.
