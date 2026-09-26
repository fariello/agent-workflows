# IPD: Prune aged workflow-artifacts run dirs with a dry-run-by-default archive route

- Date: 2026-09-24
- Kind: child
- Concern: Nothing reclaims `.aw/workflow-artifacts/<workflow>/<run-id>/`. The tree is gitignored (`.aw/.gitignore` pattern `/workflow-artifacts/`, confirmed with `git check-ignore -v`), so growth is invisible. Re-measured in the main checkout: 972K, 20 run dirs across 10 workflows. Two things make a naive prune unsafe. FIRST, readers exist: `run_cli._run_decisions` and `run_cli._run_questions` (`aw runs decisions|questions`) resolve `set_records.run_artifacts_dir(repo_root, workflow, run_id)` and exit 2 when the projection is gone, and `set_records.promote_local_checkpoints` reads the same dir on recovery to promote unflushed decisions/questions into a tracked walkthrough "so a crash never loses a recorded decision". The release-review protocol also says a run "may read prior `.aw/workflow-artifacts/release-review/<RUN_ID>/` records as input". SECOND, mtime is not a trustworthy age: every run dir in the main checkout has mtime 2026-08-16 (the day `engine.migrate_root_workflow_artifacts` moved the tree), while the run ids themselves date from 20260703 to 20260818. An mtime-based age would call all 20 runs the same age.
- Scope: IN: a pure planner plus a thin CLI route, `aw archive workflow-artifacts`, that previews by default and deletes only under `--apply`; retention is "keep the newest N runs per workflow AND anything younger than D days" (a run is deleted only when it is BOTH outside the newest N AND older than D); age comes from the run id's leading `YYYYMMDD` and falls back to the newest mtime inside the dir; a run is ALWAYS kept when it carries unresolved questions in EITHER projection shape (the `open-questions.md` marker OR an `assess`-style `decisions.md`, which is the only shape present in the measured tree), when it looks like an unfinished `release-review` run, when it is an `assess` run whose `ipd-link.md` records that no IPD was written, or when pinned with `--keep <run-id>`; the tree's README and non-directory entries are never touched; tests on a temp tree. OUT: un-ignoring the tree; moving runs anywhere (this reclaims disk, it does not shelve); any automatic or install-time prune; making `aw archive all` include this tree.
- Scope-Paths: agent_workflows/workflow_artifacts_prune.py, agent_workflows/cli.py, agent_workflows/command_surface.py, .aw/system/workflows/templates/workflow-artifacts-README.md, tests/test_workflow_artifacts_prune.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- Set: wfprune
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: muza7y
- From-Backlog: zzsaq2

## Workflow history
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: muza7y verified (set wfprune, attempt 1).
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (aw set): plan-review complete: PR-701..PR-708 all fixed. BLOCKER PR-701: the only reader-safety rule could not fire on any run in the plan's own measured tree (E-02 keys on open-questions.md; the measured population is assess runs that write none). Added E-03/E-04 for the assess and unfinished-release-review shapes, E-07 to name every keep; 10 items, 10:10 E/V bijection; OQ-01/OQ-02 resolved from evidence. Findings and 4 decisions in .aw/records/reviews/20260924-wfprune-01-muza7y-...review.md

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701..PR-708, all FIXED. Verified every author claim (the misroute reproduces verbatim; `normalize_type` raises; `--keep` is already `action="append"`; `args.age` defaults to `None` so a route-local 30d default is clean; the keep rule deletes exactly one run on the measured tree; depth-2 plus `is_symlink` skipping behaves as designed). THE DOMINANT FINDING: E-02's reader-safety rule keys ONLY on `open-questions.md`, but that file does not exist in the measured population - `write_local_projections` always writes all three projections together, whereas the `assess` workflow hand-authors a `decisions.md` that holds "any open questions for the user" IN PROSE with NO `open-questions.md` at all, which is exactly the 10-decisions-zero-questions asymmetry the plan's own F-5 measured. So the safety rule cannot fire on the only runs that actually exist. Added E-03 (assess-shape questions), E-04 (unfinished `release-review` and no-IPD `assess` runs, both of which the workflows call authoritative or sole-durable output), and E-09 (exit contract plus conformance). Split the overloaded E-06 into E-08/E-09. Corrected F-5, resolved OQ-01 and OQ-02 from evidence with carriers, clearing an error-severity `check.ipd-uncarried-obligation`.
- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog zzsaq2; re-measured the tree size and run count, the readers of the per-run dir, and found every run dir's mtime flattened to the 2026-08-16 migration date.

## Goal

Give the operator a safe, previewable way to reclaim `.aw/workflow-artifacts/` that can never delete a run a reader still needs, modelled on the existing dry-run-by-default `aw archive plans` sweep (`plans_archive.run_archive`: preview lists moves then prints "preview only; re-run with --apply to move").

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: planner

- [x] E-01 Add `agent_workflows/workflow_artifacts_prune.py` with a PURE planner `plan_prune(artifacts_root, *, keep_last, older_than_days, keep_ids=(), today=None) -> PrunePlan` returning, per run dir, a decision (`keep` or `delete`) and a reason (`newest-N`, `younger-than-D`, `open-questions`, `pinned`, `aged`). Root is `repo_root / set_records.RUN_ARTIFACTS_SUBDIR` (reuse the constant, do not re-spell the path). Only directories at exactly depth 2 (`<workflow>/<run-id>`) are candidates; files at depth 1 (the README) and symlinked dirs are skipped and never followed. Run age = leading `YYYYMMDD` of the run id when it parses as a date, else the newest mtime of any file under the dir (`os.walk(followlinks=False)`). Order within a workflow by that age, newest first, run id as tie-break. A run is `delete` only if it is outside the newest `keep_last` AND older than `older_than_days`.
  - Depends on: none
  - Expected outcome: importable module; calling it on a temp tree performs zero filesystem writes.
  - Execution state: performed

- [x] E-02 Add the FIRST reader-safety rule to the planner, for the `set_records` projection shape: a run dir whose `set_records.OPEN_QUESTIONS_FILE` exists and does NOT contain the renderer's empty marker `_No unresolved questions._` (the same string `run_cli._run_questions` keys on) is `keep` with reason `open-questions`, regardless of age or N. Also `keep` any run id listed in `keep_ids` (reason `pinned`). NOTE THE REACH, measured at review and the reason E-03 exists: `set_records.write_local_projections` writes `decisions.md`, `open-questions.md` and `deferred-work.md` TOGETHER in one call (verified: a call with zero records produced all three, with `open-questions.md` containing the empty marker), so this rule fires only on runs produced by THAT writer. It cannot fire on any run in the measured tree, because F-5 found 10 `decisions.md` and ZERO `open-questions.md`, which is only possible for a different producer.
  - Depends on: E-01
  - Expected outcome: an aged run with unresolved questions in the `set_records` shape is never planned for deletion, so `aw runs questions` and `set_records.promote_local_checkpoints` still find it.
  - Execution state: performed

- [x] E-03 Add the SECOND reader-safety rule, for the `assess` projection shape, which is the only shape present in the measured tree. The `assess` workflow hand-authors `decisions.md` and its own spec for that file says it holds "Key decisions and assumptions, ... and any open questions for the user" - in PROSE, with no `open-questions.md` written at all (confirmed at review against `.aw/system/workflows/assess/assess.md`'s artifact table, and consistent with F-5's 10-and-zero measurement). So a run dir that has `decisions.md` but NO `open-questions.md` is NOT covered by E-02 and must be handled here: treat such a run as `keep` with reason `unreviewed-decisions` unless it ALSO carries positive evidence of completion. Choose the discriminator from what the workflow actually writes rather than inventing one - `assess` writes `ipd-link.md` naming the IPD it produced, so a run with a resolvable `ipd-link.md` whose IPD path exists has handed its durable output off and is prunable, while one without it has not. Do NOT attempt prose parsing of `decisions.md` for question-like text: it is unbounded natural language and a false negative here deletes a record.
  - Depends on: E-02
  - Expected outcome: an aged `assess` run carrying `decisions.md` and no `open-questions.md` is kept unless its `ipd-link.md` resolves to an existing IPD; no rule depends on parsing prose.
  - Execution state: performed

- [x] E-04 Add the THIRD reader-safety rule, for runs whose own workflow calls the dir authoritative or sole output. TWO cases, both read out of the shipped workflow text at review. (a) UNFINISHED `release-review`: `00-run-protocol.md` states "`.aw/workflow-artifacts/release-review/<RUN_ID>/` is the authoritative run record" and, for the fresh-context mode, "the authoritative state", so an in-progress or ABORTED-PRE-FLIGHT run is live resumable state, not scratch. Keep a `release-review` run (reason `unfinished-run`) unless it carries positive completion evidence; derive the test from the required-artifact list (for example `08-checkpoints.md` present AND `00-run-metadata.md` recording a terminal status), and state in a comment which artifact you keyed on and why. (b) NO-IPD `assess`: the workflow calls the run record one of "two durable outputs", and for a run that proposed no IPD it documents a closing report reading "Created: none." - in that case the run record is the ONLY output that run produced, so deleting it destroys the sole record of the assessment. Keep a run whose `ipd-link.md` is absent or records that no IPD was created (reason `sole-durable-output`). This overlaps E-03 deliberately: E-03 decides on the QUESTIONS hazard, this decides on the SOLE-OUTPUT hazard, and a run can trip either.
  - Depends on: E-03
  - Expected outcome: an unfinished or aborted `release-review` run and a no-IPD `assess` run are never planned for deletion, whatever their age.
  - Execution state: performed

- [x] E-05 Add `apply_prune(plan) -> list[Path]` that `shutil.rmtree`s only the `delete` entries, and before each removal re-checks that the path is a real directory (not a symlink) resolving inside the artifacts root; a path failing that check is skipped and reported, never deleted. The `is_symlink` half of that check is LOAD-BEARING and not belt-and-braces: measured at review, `Path.is_dir()` returns True for a symlink pointing at a directory, so an `is_dir`-only test would follow the link and `rmtree` the target outside the root. Use `shutil.rmtree(..., ignore_errors=False)` and let a failure be reported rather than swallowed, so a partial delete is visible.
  - Depends on: E-01
  - Expected outcome: deletion is confined to planned depth-2 real directories under the root; a symlinked entry is skipped and reported.
  - Execution state: performed

### Task group 2: CLI surface

- [x] E-06 Route `aw archive workflow-artifacts` in `cli._run_archive`: check the literal token `workflow-artifacts` BEFORE `artifact_types.normalize_type` (it is not an artifact type; `normalize_type("workflow-artifacts")` raises today - verified at review: `ValueError: unknown artifact type 'workflow-artifacts'` - which is why it currently falls through to research and prints "no research doc or set matches 'workflow-artifacts'"). Add `--keep-last N` (default 5) to `p_archive`; reuse the existing `--age` and `--keep`, `--apply` and `--dir`. Two measured details to get right. FIRST, `args.age` defaults to `None`, not to a number (verified by parsing `archive workflow-artifacts`), so pass the route-local default explicitly as `duration.parse_age_duration(args.age, default_days=30)`; do NOT rely on the parser's own `default_days=14.0`. SECOND, `--keep` is ALREADY `action="append"`, so pinning several run ids works unchanged - but its help text reads "In a sweep, send this `<id6>` to reference instead of archive", which describes the research-specific MOVE and is wrong for this route; widen that help string to cover both meanings rather than leaving a flag whose documentation contradicts its behavior here. `aw archive all` stays research plus plans only. Add `--keep-last` to the `archive` `CommandDeclaration.legacy_flags` in `command_surface.py`; `mutation_gate="dry_run_default"` already fits and `discover_parser_leaves` reports `archive` as a single leaf, so no new declaration is needed (both verified at review). Do not call `_offer_archive_commit`: the tree is untracked, so there is nothing to commit.
  - Depends on: E-04, E-05
  - Expected outcome: preview is the default and writes nothing; `--apply` deletes exactly the previewed set; `--keep` accepts repetition and its help text is true for both routes.
  - Execution state: performed

- [x] E-07 Make the route's OUTPUT say what it is doing, since this is the one `archive` route that DELETES rather than moves. Preview prints one line per run as `would delete <workflow>/<run-id> (<age>d, <reason>)`, then the kept count, the total bytes reclaimable, and the closing `preview only; re-run with --apply to delete`. Under `--apply` it prints `deleted ...` lines. A run KEPT for a reader-safety reason (`open-questions`, `unreviewed-decisions`, `unfinished-run`, `sole-durable-output`, `pinned`) must be named in the preview with its reason rather than folded into a bare count, because a silently-kept run is indistinguishable from a bug and the operator cannot otherwise tell the guard worked. A missing tree is an empty result, exit 0.
  - Depends on: E-06
  - Expected outcome: the preview names every deletion candidate with its age and reason AND every reader-safety keep with its reason, and closes with the `--apply` hint; a missing tree prints an empty result and exits 0.
  - Execution state: performed

- [x] E-08 Document the retention verb in `.aw/system/workflows/templates/workflow-artifacts-README.md` under a short "Reclaiming space" section: the command, the keep rule, that runs with unresolved questions or unfinished state are always kept, and that deletion is permanent because the tree is untracked. Reconcile it with what that README ALREADY says rather than appending a contradiction: it currently states "treat its contents as disposable working material" and "Nothing here survives a fresh clone", which is true for scratch but is precisely the sentence that makes deleting a no-IPD `assess` run look safe (E-04). Add the qualification that a run whose workflow calls its record a durable output is the exception, and that the prune verb keeps those. No em or en dashes (user-facing prose).
  - Depends on: E-07
  - Expected outcome: the README names `aw archive workflow-artifacts` and `--apply`, and its disposability sentence carries the durable-output exception.
  - Execution state: performed

### Task group 3: tests and suite

- [x] E-09 Add `tests/test_workflow_artifacts_prune.py` building a temp tree and asserting the planner and deleter. The tree: `assess-bugs` with 7 dated runs, `release-review` with 2, one undated run id, a README FILE at depth 1, a symlinked run dir whose target holds a sentinel file, one aged run with an unresolved `open-questions.md`, one aged `assess` run with a prose `decisions.md` and NO `open-questions.md` (the E-03 case, which is the shape the measured tree actually contains), one aged `assess` run whose `ipd-link.md` records no IPD (the E-04(b) case), and one `release-review` run missing its completion artifact (the E-04(a) case). Assert: newest N kept per workflow; young runs kept even beyond N; each of the four reader-safety keeps fires with its own reason; `--keep` pins; undated run falls back to mtime; README file and symlink target both untouched (check the sentinel file still exists); `--apply` removes exactly the previewed set. Include at least one FAIL-WITHOUT-FIX demonstration per reader-safety rule, since a keep rule that never fires is indistinguishable from a passing test.
  - Depends on: E-08
  - Expected outcome: planner and deleter tests pass, and each reader-safety rule is shown failing when its rule is disabled.
  - Execution state: performed

- [x] E-10 Add the CLI-surface tests and run the bare suite. Through `cli.main(["archive","workflow-artifacts","--dir",tmp])`: preview leaves the tree byte-identical (compare a `find | sort` digest before and after); `--apply` removes exactly the previewed set; a missing tree exits 0; `archive all` does not touch the tree; `--keep` given twice pins both runs. Also assert the route's exit codes stay inside the `archive` declaration's `exit_contract` of `(0, 2)` (verified at review) - in particular that a skipped-because-unsafe path does NOT introduce a bare exit 1, since the declaration does not permit it and the conformance matrix reads that contract. Then run the bare suite `python3 -m pytest`.
  - Depends on: E-09
  - Expected outcome: CLI tests pass, the route's exits stay within `(0, 2)`, and the bare suite is green.
  - Execution state: performed

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
| F-5 | No open-questions projection exists today in the main checkout | `find ... -name open-questions.md` returned 0; 10 `decisions.md` exist (assess runs) |
| F-5a | CORRECTED AT REVIEW: F-5's durability inference does NOT cover the measured population, and its asymmetry proves a SECOND producer. `set_records.write_local_projections` writes `decisions.md`, `open-questions.md` and `deferred-work.md` in ONE call, so its runs can never show 10-and-zero; the `assess` workflow hand-authors `decisions.md` alone. The `revgate c621h9` durability argument (cited by backlog `zzsaq2`) is about the `set_records` DECISION REGISTER, whose durable copy is the tracked review artifact. It says nothing about an `assess` run record | Verified at review: `write_local_projections(td, wf, rid, [])` produced all three files, `open-questions.md` holding `_No unresolved questions._`; `.aw/system/workflows/assess/assess.md` artifact table lists `report.md`, `findings.csv`, `decisions.md`, `evidence.md`, `ipd-link.md` and no `open-questions.md`; backlog `zzsaq2` scopes its durability claim to "set_records.py:143-158 writes the autonomous-decisions register" |
| F-5b | An `assess` `decisions.md` HOLDS the open questions, in prose | `.aw/system/workflows/assess/assess.md`: `decisions.md` contains "Key decisions and assumptions, ... and any open questions for the user". So the E-02 marker test cannot see them, and prose parsing is not a safe substitute (E-03) |
| F-5c | Two run shapes call the run dir DURABLE or AUTHORITATIVE, so "disposable scratch" is not uniformly true | `release-review/00-run-protocol.md`: "`.aw/workflow-artifacts/release-review/<RUN_ID>/` is the authoritative run record" and "the authoritative state" for fresh-context phases; `03-findings-register.csv` / `04-action-register.csv` are labelled "Durable register". `assess.md`: "It **does** write two durable outputs: the IPD ... and a run record", and for a run proposing no IPD the closing report reads "Created: none.", making the run record that run's ONLY output (E-04) |
| F-6 | The token currently misroutes | `aw archive workflow-artifacts` prints "no research doc or set matches 'workflow-artifacts'" and exits 0. RE-VERIFIED at review, verbatim, exit 0; `normalize_type("workflow-artifacts")` raises `ValueError: unknown artifact type` |
| F-7 | Flag and contract facts the route depends on, all measured at review | `args.age` defaults to `None` (so the route must pass `default_days=30` itself; the parser's own default is `14.0`); `--keep` is already `action="append"` but its help text describes the research-specific "send to reference" MOVE; the `archive` declaration is `command_class="mutation"`, `mutation_gate="dry_run_default"`, `legacy_flags=("--keep", "--apply")`, `exit_contract=(0, 2)`; `discover_parser_leaves` reports `archive` as ONE leaf and `find_undeclared_leaves` does not list it, so a positional value adds no leaf |
| F-8 | `Path.is_dir()` is True for a symlink to a directory, so E-05's `is_symlink` check is load-bearing | Verified at review on a temp tree: a symlinked run dir reported `is_dir=True is_symlink=True`; depth-1 `README.md` and the symlink were both correctly skippable, and an `is_dir`-only test would have followed the link out of the root |

## Proposed changes (ordered, validatable)

1. Pure planner with the keep rule and id-date age (E-01).
2. Reader-safety rule for the `set_records` projection shape and pins (E-02).
3. Reader-safety rule for the `assess` shape, which is the only one in the measured tree (E-03).
4. Reader-safety rule for unfinished `release-review` and no-IPD `assess` runs (E-04).
5. Confined deleter, with the load-bearing symlink check (E-05).
6. `aw archive workflow-artifacts` route and `--keep-last` flag, preview by default (E-06).
7. Output that names every deletion AND every reader-safety keep with its reason (E-07).
8. README note reconciled with the existing disposability sentence (E-08).
9. Planner and deleter tests with a fail-without-fix per safety rule (E-09).
10. CLI tests, exit-contract assertion, and the bare suite (E-10).

## Deferred / out of scope (with reason)

- Automatic prune on install, update, or run completion: a silent delete of machine-local history should stay an explicit operator act until the manual verb has been used.
  - Carrier-Declined: no demand measured; 972K does not justify automation.
- A separate top-level `aw prune` verb: `archive` already carries the preview/`--apply`/`--age` contract and its declaration; a new top-level leaf would need its own declaration, completion and conformance rows for one tree.
  - Carrier-Declined: revisit only if OQ-01 resolves toward a new verb.

## Scope check

- Over-scope: none.
- Under-scope (added at review): the plan's single reader-safety rule (E-02) could not fire on ANY run in its own measured tree, because that rule keys on `open-questions.md` and the measured population has none (F-5a, F-5b); E-03 and E-04 cover the shapes that actually exist, including two the shipped workflows call authoritative or sole-durable output (F-5c). E-07's requirement to NAME each reader-safety keep is also new: a silently-kept run is indistinguishable from a guard that never ran. Separately, `docs/artifact-lifecycles.md` lists `aw archive research` examples but covers record trees only; this untracked tree is documented in its own README instead (E-08).

## Required tests / validation

Temp-tree unit tests for the planner and deleter, including a fixture for EACH of the four reader-safety shapes and a fail-without-fix demonstration per rule (a keep rule that never fires is indistinguishable from a passing test); CLI tests through `cli.main` for preview byte-identity, `--apply` set equality, a missing tree, `archive all` isolation, repeated `--keep`, and the `(0, 2)` exit contract; and the bare suite.

## Spec / documentation sync

- No `.spec.md` is amended: no spec governs `.aw/workflow-artifacts/` retention, and the `archive` command's declaration shape is unchanged apart from one legacy flag.
- `.aw/system/workflows/templates/workflow-artifacts-README.md` gains the retention note (E-05).

## Open questions

### OQ-01: Should deletion live under `aw archive` or a new verb?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved at review in favour of `aw archive workflow-artifacts`, on measured evidence rather than preference. The `archive` declaration ALREADY carries the exact contract this route needs (`command_class="mutation"`, `mutation_gate="dry_run_default"`, `legacy_flags=("--keep", "--apply")`, `exit_contract=(0, 2)`), and `discover_parser_leaves` reports `archive` as a single leaf with `find_undeclared_leaves` not listing it, so a positional value adds no leaf, no new declaration, no completion row and no conformance row. A dedicated verb would need all four for one untracked tree. The residual cost is real and is mitigated rather than dismissed: `archive` MOVES records elsewhere while this route DELETES, so E-07 requires the word "delete" in every preview and apply line and in the closing hint, and E-08 requires the README to say the deletion is permanent.
- Carrier-Declined: Resolved from the shipped declaration and parser-leaf measurements, so nothing is outstanding; the Deferred row for a separate `aw prune` verb records the alternative and its trigger.

### OQ-02: Default retention values

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `--keep-last 5` and `--age 30d`. Re-derived at review against the measured `assess-documentation` workflow (6 runs, all aged): with those defaults exactly ONE run is planned for deletion, the oldest at index 5, because every other run is inside the newest-5 window even though all six are older than 30 days. That is the AND rule working as intended, and it confirms the author's claim that the defaults are conservative on the real tree. Both remain flags, so a maintainer who wants a different window passes one; the default is chosen to under-delete rather than to reclaim maximally, which is correct for a permanent delete on an untracked tree.
- Carrier-Declined: Re-derived at review and fixed in E-06; a later change to either default is a new decision about a flag default, not a deferred obligation from this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_workflow_artifacts_prune.py -k "keep_last or younger or undated or depth" -v` showing those tests PASSED, including the undated-run mtime fallback test and the test that a run with id `20260703-...` but mtime today is treated as aged. Also paste a direct demonstration that the planner wrote nothing: a `find <tmp> | sort | sha256sum` identical before and after a `plan_prune` call.
  - Observed evidence: PASS; see the pasted evidence below.
    ```
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_dated_run_with_today_mtime_is_aged_undated_check PASSED [ 20%]
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_depth_and_non_dir_skipped PASSED [ 40%]
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_undated_run_mtime_fallback PASSED [ 60%]
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_keep_last_and_retention PASSED [ 80%]
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_younger_than_days_kept PASSED [100%]

    ======================= 5 passed, 18 deselected in 0.17s =======================
    ```
    Demonstration that `plan_prune` performs zero filesystem writes:
    ```
    Before: 423c66dce46d28a415a09a31d4ee0726716be3ce27485fe56e83b334ab15b99b  -
    After:  423c66dce46d28a415a09a31d4ee0726716be3ce27485fe56e83b334ab15b99b  -
    Identical before and after plan_prune!
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the passing run of the `open-questions` and pin tests; AND paste the same open-questions test FAILING (`1 failed`) with the E-02 rule temporarily commented out, then restored. Also paste the output of a `set_records.write_local_projections(tmp, wf, rid, [])` call listing the three files it created, which is the measurement establishing that this rule's reach is limited to that writer and therefore why E-03 exists.
  - Observed evidence: PASS; see the pasted evidence below.
    Passing test:
    ```
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_open_questions PASSED [ 50%]
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_pinned PASSED [100%]

    ======================= 2 passed, 21 deselected in 0.18s =======================
    ```
    Failing demonstration with E-02 rule disabled:
    ```
    FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_open_questions - AssertionError: 'delete' != 'keep'
    ======================= 1 failed, 22 deselected in 0.18s =======================
    ```
    Output of `set_records.write_local_projections`:
    ```
    Created files: ['decisions.md', 'deferred-work.md', 'open-questions.md']
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the passing test for the `assess`-shape run (a `decisions.md` with prose questions and NO `open-questions.md`) showing it is KEPT with reason `unreviewed-decisions`, and the paired test showing a run WITH a resolvable `ipd-link.md` is prunable. Then paste the same keep test FAILING with the E-03 rule disabled, restored afterwards. This is the plan's most important single piece of evidence: review measured that without this rule NO run in the real tree is protected, because the only shape present there is the one E-02 cannot see.
  - Observed evidence: PASS; see the pasted evidence below.
    Passing tests:
    ```
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_assess_unreviewed_decisions PASSED [ 50%]
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_assess_with_resolvable_ipd_link_is_prunable PASSED [100%]

    ======================= 2 passed, 21 deselected in 0.20s =======================
    ```
    Failing demonstration with E-03 rule disabled:
    ```
    FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_assess_unreviewed_decisions - AssertionError: 'delete' != 'keep'
    ======================= 1 failed, 22 deselected in 0.17s =======================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste passing tests for BOTH cases with their distinct reasons - an in-progress/aborted `release-review` run kept as `unfinished-run`, and a no-IPD `assess` run kept as `sole-durable-output` - plus each FAILING with its rule disabled. State in the evidence which completion artifact you keyed the `release-review` test on and quote the protocol sentence that justifies it, since review found the protocol calls that directory "the authoritative run record" and the choice of discriminator is the whole safety of this item.
  - Observed evidence: PASS; see the pasted evidence below.
    Passing tests:
    ```
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_assess_no_ipd_sole_durable_output PASSED [ 50%]
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_release_review_unfinished PASSED [100%]

    ======================= 2 passed, 21 deselected in 0.17s =======================
    ```
    Failing demonstrations with rules disabled:
    1. `unfinished-run` rule disabled:
    ```
    FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_release_review_unfinished - AssertionError: 'delete' != 'keep'
    ======================= 1 failed, 22 deselected in 0.18s =======================
    ```
    2. `sole-durable-output` rule disabled:
    ```
    FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_assess_no_ipd_sole_durable_output - AssertionError: 'delete' != 'keep'
    ======================= 1 failed, 22 deselected in 0.18s =======================
    ```
    Release-review completion artifact choice: keyed on `12-final-response.md`.
    Protocol justification from `.aw/system/workflows/release-review/00-run-protocol.md`:
    - Line 305: "Write the response to `.aw/workflow-artifacts/release-review/<RUN_ID>/12-final-response.md` (the authoritative run record, gitignored so local context does not leak)."
    - Line 489: "Section 8 writes the final response into the run record (`12-final-response.md`)."
    Without `12-final-response.md`, the run is in-progress or aborted pre-flight and constitutes resumable working state, protected as `unfinished-run`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the passing symlink-confinement test showing the symlink TARGET directory and its sentinel file still exist after `apply_prune`, and the depth-1 README file still present. Additionally paste a run of the same test with the `is_symlink` half of the check removed, showing it FAILS (the sentinel gone or the target removed), since review measured `is_dir()` to be True for a symlinked directory and that is the only thing distinguishing a safe deleter from one that escapes the root.
  - Observed evidence: PASS; see the pasted evidence below.
    Passing test:
    ```
    tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_symlink_confinement_sentinel_safe PASSED [100%]

    ======================= 1 passed, 22 deselected in 0.17s =======================
    ```
    Failing demonstration with `p.is_symlink()` check disabled in `apply_prune`:
    ```
    FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_symlink_confinement_sentinel_safe - AssertionError: False is not true
    ======================= 1 failed, 22 deselected in 0.19s =======================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m agent_workflows archive workflow-artifacts --dir <tmp>` showing the route is reached (no "no research doc or set matches" line). Paste `rg -n '"--keep-last"' agent_workflows/command_surface.py` showing the flag declared in `legacy_flags`. Paste a test asserting the effective age default is 30 days when `--age` is absent (review measured `args.age is None`, so a route that forgot `default_days=30` would silently use 14). Paste the widened `--keep` help text.
  - Observed evidence: PASS; see the pasted evidence below.
    Route reached:
    ```
    $ python3 -m agent_workflows archive workflow-artifacts --dir <tmp>
    ✓ CLEAN  no workflow artifacts to prune
    ```
    Command surface declaration:
    ```
    $ rg -n '"--keep-last"' agent_workflows/command_surface.py
    544:        legacy_flags=("--keep", "--apply", "--keep-last"),
    ```
    Effective age default test passing:
    ```
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_default_age_is_30_days PASSED [100%]

    ======================= 1 passed, 22 deselected in 0.35s =======================
    ```
    Widened `--keep` help text from `aw archive --help`:
    ```
      --keep KEEP           In a sweep, send this <id6> to reference instead of
                            archive, or pin a run id against pruning.
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste a preview against a tree containing at least one deletion candidate AND at least one reader-safety keep, showing a `would delete <workflow>/<run-id> (<age>d, <reason>)` line for the candidate, a NAMED line with its reason for the keep, the kept count, the reclaimable bytes, and the closing `preview only; re-run with --apply to delete`. Separately paste the missing-tree invocation showing an empty result and exit 0 (echo the exit code).
  - Observed evidence: PASS; see the pasted evidence below.
    Preview against tree:
    ```
    $ aw archive workflow-artifacts --dir <tmp> --keep-last 0
    would delete custom-wf/20260701-01 (87d, aged)
    keep custom-wf/20260702-02 (open-questions)
    kept: 1 run(s)
    reclaimable: 5 bytes
    preview only; re-run with --apply to delete
    RC: 0
    ```
    Missing-tree invocation:
    ```
    $ aw archive workflow-artifacts --dir <empty-tmp>
    ✓ CLEAN  no workflow artifacts to prune
    EXIT: 0
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste `rg -n "aw archive workflow-artifacts|--apply" .aw/system/workflows/templates/workflow-artifacts-README.md` with at least one hit each, and `rg -n "[\u2013\u2014]" .aw/system/workflows/templates/workflow-artifacts-README.md` returning no hits. Also quote the sentence you added qualifying the existing "treat its contents as disposable working material" claim, so the reconciliation E-08 requires is visible rather than assumed.
  - Observed evidence: PASS; see the pasted evidence below.
    ```
    $ rg -n "aw archive workflow-artifacts|--apply" .aw/system/workflows/templates/workflow-artifacts-README.md
    32:aw archive workflow-artifacts
    38:aw archive workflow-artifacts --apply
    ```
    Dash check (zero hits):
    ```
    $ rg -n "[\u2013\u2014]" .aw/system/workflows/templates/workflow-artifacts-README.md
    (exit code 1, zero matches)
    ```
    Qualification sentence:
    "Because this tree is untracked, treat its contents as disposable working material, with the exception of runs whose workflow calls their record a durable output (such as an assess run where no IPD was created, or an in-progress release-review run). Nothing here survives a fresh clone."
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the planner/deleter test run summary (`N passed`) and, in one place, the four fail-without-fix results from V-02/V-03/V-04/V-05 listed together, so a reviewer can see every reader-safety rule was independently shown to fire. A rule with no failing demonstration does not count as validated.
  - Observed evidence: PASS; see the pasted evidence below.
    Planner and deleter test suite summary:
    ```
    ======================= 14 passed, 9 deselected in 0.21s =======================
    ```
    Four fail-without-fix demonstrations:
    1. V-02 (`open-questions` disabled): `FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_open_questions - AssertionError: 'delete' != 'keep'`
    2. V-03 (`unreviewed-decisions` disabled): `FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_assess_unreviewed_decisions - AssertionError: 'delete' != 'keep'`
    3. V-04a (`unfinished-run` disabled): `FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_release_review_unfinished - AssertionError: 'delete' != 'keep'`
       V-04b (`sole-durable-output` disabled): `FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_reader_safety_assess_no_ipd_sole_durable_output - AssertionError: 'delete' != 'keep'`
    4. V-05 (`is_symlink` check disabled in deleter): `FAILED tests/test_workflow_artifacts_prune.py::TestWorkflowArtifactsPrune::test_symlink_confinement_sentinel_safe - AssertionError: False is not true`
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste the CLI test results including the before/after `find <tmp>/.aw/workflow-artifacts | sort | sha256sum` identical across a preview, the `--apply` output whose `deleted` lines match the preview's `would delete` lines exactly, the missing-tree exit 0, the `archive all` isolation assertion, the repeated-`--keep` assertion, and the exit-code assertion showing the route stays within `(0, 2)`. Then paste the final summary line of the bare `python3 -m pytest` showing 0 failed (bare per AGENTS.md: no `-n0`, no extra `-q`, no `-p no:randomly`).
  - Observed evidence: PASS; see the pasted evidence below.
    CLI test suite:
    ```
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_preview_byte_identity PASSED [ 11%]
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_preview_output_format PASSED [ 22%]
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_exit_contract PASSED [ 33%]
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_apply_matches_preview PASSED [ 44%]
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_archive_all_does_not_touch_workflow_artifacts PASSED [ 55%]
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_command_surface_declaration PASSED [ 66%]
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_repeated_keep_pins_both PASSED [ 77%]
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_missing_tree_exits_zero PASSED [ 88%]
    tests/test_workflow_artifacts_prune.py::TestCliSurface::test_cli_default_age_is_30_days PASSED [100%]

    ======================= 9 passed, 14 deselected in 0.83s =======================
    ```
    Bare `python3 -m pytest` full suite run:
    ```
    2280 passed, 1 skipped, 3 warnings in 41.86s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Ten items, one concern: a safe, previewable reclaim verb for `.aw/workflow-artifacts/`. The count grew from six at review because the plan had ONE reader-safety rule that review measured could not fire on any run in the plan's own measured tree, so the safety surface needed three rules rather than one (E-02/E-03/E-04), and because the original E-06 bundled the whole test suite plus the bare run into one item while the original E-04 bundled routing with output formatting. No item introduces a second concern.

WHAT A HUMAN IS APPROVING. A new `aw archive` route that PERMANENTLY DELETES directories from an untracked tree. Three things deserve attention despite the small measured payoff (972K, and exactly one run deleted under the default window). FIRST, this is the only `archive` route that deletes rather than moves, and the tree is gitignored, so a wrong deletion is unrecoverable - there is no `superseded/` to fish it back out of. SECOND, the safety of the whole feature rests on the reader-safety rules in E-02 through E-04, and review measured that the originally-planned single rule protected NOTHING in the real tree; if those rules are wrong, the failure mode is silent destruction of an assessment record whose workflow calls it a durable output. THIRD, the 30-day/keep-5 defaults are deliberately conservative (OQ-02): they under-delete, which is the right bias here.

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface: `agent_workflows/workflow_artifacts_prune.py` is a NEW module holding the pure planner, the four reader-safety rules and `apply_prune`; `agent_workflows/cli.py` gains the `workflow-artifacts` branch in `_run_archive` placed BEFORE `normalize_type`, the `--keep-last` argument on `p_archive`, the widened `--keep` help text, and the route's output; `agent_workflows/command_surface.py` gains `--keep-last` in the `archive` declaration's `legacy_flags` and nothing else; the README template gains one "Reclaiming space" section plus the disposability qualification; `tests/test_workflow_artifacts_prune.py` is new. EXPLICITLY NOT IN SCOPE: `set_records.py` (the projection writers are read, never changed); `run_cli.py`; `plans_archive.py` or `research_archive.py`; the `archive` declaration's `mutation_gate`, `command_class` or `exit_contract`; `aw archive all`'s type list; the `.aw/.gitignore` entry; and any automatic or install-time prune. An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on the four fail-without-fix demonstrations (V-02, V-03, V-04, V-05), because each requires temporarily DISABLING a safety rule to prove it fires and then restoring it - and a keep rule that never fires passes every test that does not try to break it. V-05's symlink case is the one where a faked result has the worst consequence, since that check is what keeps `rmtree` inside the root.

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: the `assess` workflow no longer writes `ipd-link.md`, or `release-review` no longer writes the completion artifact E-04 keys on, since both discriminators would then be unavailable and the safety rules would need redesigning rather than reimplementing; or `set_records.write_local_projections` has changed such that the three projections are no longer written together, which would invalidate the reach argument in E-02.

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit muza7y -- <Scope-Paths>`, never push. NEVER run `--apply` against the real `.aw/workflow-artifacts/` tree as part of executing this plan: every test uses a temp tree, and the one permitted live invocation is a PREVIEW. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-10 carry pasted evidence. Backlog `zzsaq2` is already `graduated` and carries no `- Blocks-Release:`, so no gate handoff is owed.
