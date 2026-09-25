# IPD: Prune aged workflow-artifacts run dirs with a dry-run-by-default archive route

- Date: 2026-09-24
- Kind: child
- Concern: Nothing reclaims `.aw/workflow-artifacts/<workflow>/<run-id>/`. The tree is gitignored (`.aw/.gitignore` pattern `/workflow-artifacts/`, confirmed with `git check-ignore -v`), so growth is invisible. Re-measured in the main checkout: 972K, 20 run dirs across 10 workflows. Two things make a naive prune unsafe. FIRST, readers exist: `run_cli._run_decisions` and `run_cli._run_questions` (`aw runs decisions|questions`) resolve `set_records.run_artifacts_dir(repo_root, workflow, run_id)` and exit 2 when the projection is gone, and `set_records.promote_local_checkpoints` reads the same dir on recovery to promote unflushed decisions/questions into a tracked walkthrough "so a crash never loses a recorded decision". The release-review protocol also says a run "may read prior `.aw/workflow-artifacts/release-review/<RUN_ID>/` records as input". SECOND, mtime is not a trustworthy age: every run dir in the main checkout has mtime 2026-08-16 (the day `engine.migrate_root_workflow_artifacts` moved the tree), while the run ids themselves date from 20260703 to 20260818. An mtime-based age would call all 20 runs the same age.
- Scope: IN: a pure planner plus a thin CLI route, `aw archive workflow-artifacts`, that previews by default and deletes only under `--apply`; retention is "keep the newest N runs per workflow AND anything younger than D days" (a run is deleted only when it is BOTH outside the newest N AND older than D); age comes from the run id's leading `YYYYMMDD` and falls back to the newest mtime inside the dir; a run with unresolved open questions and any `--keep <run-id>` is always kept; the tree's README and non-directory entries are never touched; tests on a temp tree. OUT: un-ignoring the tree; moving runs anywhere (this reclaims disk, it does not shelve); any automatic or install-time prune; making `aw archive all` include this tree.
- Scope-Paths: agent_workflows/workflow_artifacts_prune.py, agent_workflows/cli.py, agent_workflows/command_surface.py, .aw/system/workflows/templates/workflow-artifacts-README.md, tests/test_workflow_artifacts_prune.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- Set: wfprune
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: muza7y
- From-Backlog: zzsaq2

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog zzsaq2; re-measured the tree size and run count, the readers of the per-run dir, and found every run dir's mtime flattened to the 2026-08-16 migration date.

## Goal

Give the operator a safe, previewable way to reclaim `.aw/workflow-artifacts/` that can never delete a run a reader still needs, modelled on the existing dry-run-by-default `aw archive plans` sweep (`plans_archive.run_archive`: preview lists moves then prints "preview only; re-run with --apply to move").

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: planner

- [ ] E-01 Add `agent_workflows/workflow_artifacts_prune.py` with a PURE planner `plan_prune(artifacts_root, *, keep_last, older_than_days, keep_ids=(), today=None) -> PrunePlan` returning, per run dir, a decision (`keep` or `delete`) and a reason (`newest-N`, `younger-than-D`, `open-questions`, `pinned`, `aged`). Root is `repo_root / set_records.RUN_ARTIFACTS_SUBDIR` (reuse the constant, do not re-spell the path). Only directories at exactly depth 2 (`<workflow>/<run-id>`) are candidates; files at depth 1 (the README) and symlinked dirs are skipped and never followed. Run age = leading `YYYYMMDD` of the run id when it parses as a date, else the newest mtime of any file under the dir (`os.walk(followlinks=False)`). Order within a workflow by that age, newest first, run id as tie-break. A run is `delete` only if it is outside the newest `keep_last` AND older than `older_than_days`.
  - Depends on: none
  - Expected outcome: importable module; calling it on a temp tree performs zero filesystem writes.
  - Execution state: pending

- [ ] E-02 Add the reader-safety rule to the planner: a run dir whose `set_records.OPEN_QUESTIONS_FILE` exists and does NOT contain the renderer's empty marker `_No unresolved questions._` (the same string `run_cli._run_questions` keys on) is `keep` with reason `open-questions`, regardless of age or N. Also `keep` any run id listed in `keep_ids` (reason `pinned`).
  - Depends on: E-01
  - Expected outcome: an aged run with unresolved questions is never planned for deletion, so `aw runs questions` and `set_records.promote_local_checkpoints` still find it.
  - Execution state: pending

- [ ] E-03 Add `apply_prune(plan) -> list[Path]` that `shutil.rmtree`s only the `delete` entries, and before each removal re-checks that the path is a real directory (not a symlink) resolving inside the artifacts root; a path failing that check is skipped and reported, never deleted.
  - Depends on: E-01
  - Expected outcome: deletion is confined to planned depth-2 run dirs under the root.
  - Execution state: pending

### Task group 2: CLI surface

- [ ] E-04 Route `aw archive workflow-artifacts` in `cli._run_archive`: check the literal token `workflow-artifacts` BEFORE `artifact_types.normalize_type` (it is not an artifact type; `normalize_type("workflow-artifacts")` raises today, which is why it currently falls through to research and prints "no research doc or set matches 'workflow-artifacts'"). Add `--keep-last N` (default 5) to `p_archive`; reuse the existing `--age` (parsed with `duration.parse_age_duration`, default 30 days for this route only), `--keep` (pin run ids), `--apply` and `--dir`. Preview prints one line per run as `would delete <workflow>/<run-id> (<age>d, <reason>)` plus the kept count and total bytes reclaimable, then "preview only; re-run with --apply to delete". With `--apply` it prints `deleted ...` lines. A missing tree is an empty result (exit 0). `aw archive all` stays research plus plans only. Add `--keep-last` to the `archive` `CommandDeclaration.legacy_flags` in `command_surface.py`; `mutation_gate="dry_run_default"` already fits. Do not call `_offer_archive_commit`: the tree is untracked, so there is nothing to commit.
  - Depends on: E-02, E-03
  - Expected outcome: preview is the default and writes nothing; `--apply` deletes exactly the previewed set.
  - Execution state: pending

- [ ] E-05 Document the retention verb in `.aw/system/workflows/templates/workflow-artifacts-README.md` under a short "Reclaiming space" section: the command, the keep rule, that runs with unresolved questions are always kept, and that deletion is permanent because the tree is untracked. No em or en dashes (user-facing prose).
  - Depends on: E-04
  - Expected outcome: the README names `aw archive workflow-artifacts` and `--apply`.
  - Execution state: pending

### Task group 3: tests and suite

- [ ] E-06 Add `tests/test_workflow_artifacts_prune.py` building a temp tree (workflows `assess-bugs` with 7 dated runs, `release-review` with 2, one undated run id, a README file at depth 1, a symlinked run dir, and one aged run with an unresolved `open-questions.md`) and asserting: newest N kept per workflow; young runs kept even beyond N; the open-questions run kept; `--keep` pins; undated run falls back to mtime; README and symlink target untouched; preview (via `cli.main(["archive","workflow-artifacts","--dir",tmp])`) leaves the tree byte-identical; `--apply` removes exactly the previewed set; missing tree exits 0; `archive all` does not touch the tree. Then run the bare suite `python3 -m pytest`.
  - Depends on: E-05
  - Expected outcome: new tests pass; bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Dry-run default with `--apply` is the house pattern for sweeps: `plans_archive.run_archive` and `research_archive.run_archive`, declared as `mutation_gate="dry_run_default"` on the `archive` `CommandDeclaration`.
- Age strings are parsed centrally by `duration.parse_age_duration` (h/d/w/m/y).
- The run dir path is owned by `set_records.run_artifacts_dir` and `set_records.RUN_ARTIFACTS_SUBDIR`; do not hard-code it.
- Every parser leaf needs a `CommandDeclaration` (`tests/conformance_matrix.build_matrix` reports undeclared leaves); this plan adds no new leaf, only a positional value and one flag on `archive`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Growth confirmed, still modest | main checkout: `du -sh` 972K; 20 depth-2 dirs; 10 workflows |
| F-2 | mtime is flattened by the migration | every run dir `%TY-%Tm-%Td` = 2026-08-16; run ids range 20260703 to 20260818 (`overnight-exec/20260818`) |
| F-3 | Readers of an OLD run dir | `run_cli._run_decisions`, `run_cli._run_questions` (exit 2 "no ... projection found"), `set_records.promote_local_checkpoints`; release-review "may read prior ... records as input" |
| F-4 | `aw reviews decisions` is NOT a reader | its help: "read from the review record's Decisions section" (tracked `.aw/records/reviews/`); no `workflow-artifacts` reference in `reviews.py` |
| F-5 | No open-questions projection exists today in the main checkout | `find ... -name open-questions.md` returned 0; 10 `decisions.md` exist (assess runs). Decisions are a projection whose durable copy lives in tracked records (backlog zzsaq2, revgate `c621h9`), so deleting an aged `decisions.md` loses no durable record |
| F-6 | The token currently misroutes | `aw archive workflow-artifacts` prints "no research doc or set matches 'workflow-artifacts'" and exits 0 |

## Proposed changes (ordered, validatable)

1. Pure planner with the keep rule and id-date age (E-01).
2. Reader-safety rule for unresolved questions and pins (E-02).
3. Confined deleter (E-03).
4. `aw archive workflow-artifacts` route and `--keep-last` flag, preview by default (E-04).
5. README note (E-05).
6. Temp-tree tests plus bare suite (E-06).

## Deferred / out of scope (with reason)

- Automatic prune on install, update, or run completion: a silent delete of machine-local history should stay an explicit operator act until the manual verb has been used.
  - Carrier-Declined: no demand measured; 972K does not justify automation.
- A separate top-level `aw prune` verb: `archive` already carries the preview/`--apply`/`--age` contract and its declaration; a new top-level leaf would need its own declaration, completion and conformance rows for one tree.
  - Carrier-Declined: revisit only if OQ-01 resolves toward a new verb.

## Scope check

- Over-scope: none.
- Under-scope: `docs/artifact-lifecycles.md` lists `aw archive research` examples but covers record trees only; this untracked tree is documented in its own README instead (E-05).

## Required tests / validation

Temp-tree unit tests for the planner and deleter, CLI tests through `cli.main` for preview and `--apply`, one FAIL-without-fix demonstration, and the bare suite.

## Spec / documentation sync

- No `.spec.md` is amended: no spec governs `.aw/workflow-artifacts/` retention, and the `archive` command's declaration shape is unchanged apart from one legacy flag.
- `.aw/system/workflows/templates/workflow-artifacts-README.md` gains the retention note (E-05).

## Open questions

### OQ-01: Should deletion live under `aw archive` or a new verb?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default is `aw archive workflow-artifacts`, because it reuses the existing dry-run-by-default contract, `--age` parsing and declaration. The cost is that `archive` moves records elsewhere while this route deletes; the preview and apply lines say "delete" explicitly so the difference is visible. Proceed with the default unless the maintainer prefers a dedicated verb.

### OQ-02: Default retention values

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default `--keep-last 5` and `--age 30d`. On the measured tree that deletes only `assess-documentation`'s oldest run (6 runs, all aged), which is conservative. Both are flags, so the defaults are easy to change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_workflow_artifacts_prune.py -k "keep_last or younger or undated or depth" -v` showing those tests PASSED, including the undated-run mtime fallback test and the test that a run with id `20260703-...` but mtime today is treated as aged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the passing run of the open-questions and pin tests; AND paste the same open-questions test FAILING (`1 failed`) with the E-02 rule temporarily commented out, then restored.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the passing symlink-confinement test showing the symlink target dir still exists after `apply_prune`, and the README file still present.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: in a probe copy of a temp tree, paste `python3 -m agent_workflows archive workflow-artifacts --dir <tmp>` output ending "preview only; re-run with --apply to delete" plus a `find <tmp>/.aw/workflow-artifacts | sort | sha256sum` identical before and after; then the `--apply` output with `deleted` lines matching the preview lines exactly. Also paste `rg -n '"--keep-last"' agent_workflows/command_surface.py` showing the flag declared.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n "aw archive workflow-artifacts|--apply" .aw/system/workflows/templates/workflow-artifacts-README.md` with at least one hit each, and `rg -n "[\u2013\u2014]" .aw/system/workflows/templates/workflow-artifacts-README.md` returning no hits.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new test file's run summary (`N passed`) and the bare `python3 -m pytest` final summary line showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <plan> -- <Scope-Paths>`, never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
