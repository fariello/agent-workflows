# IPD: Make the stranded-lane report tell the truth: content-landed exclusion, one row per lane, no phantom worktree, live remedy

- Date: 2026-09-17
- Kind: child
- Concern: `aw attention` prints 19 STRANDED rows and `--check` fails closed, while NOT ONE of the 12 reported lanes holds work that needs recovering (triaged per lane 2026-09-18, evidence in backlog `kvf5xo`/`q96tpi`/`46fb5i`/`fci7yn`). FOUR DEFECTS IN THE REPORTING, all in the same ~60 lines, produce that. (1) THE LANDING TEST ANSWERS THE WRONG QUESTION, and this is a SPEC VIOLATION rather than a gap: spec `attention-registry-and-cross-tree-status` F3a already makes it NORMATIVE that "a lane whose work HAS reached the integration target MUST NOT fail it either", but the only landing test is `runner_shared.lane_work_has_landed` (runner_shared.py:1077-1107), a single `git merge-base --is-ancestor`, which sees ANCESTRY and is therefore blind to work that reached the target by RE-EXECUTION. Six of the twelve reported lanes are abandoned first attempts whose plan was re-executed on a SECOND lane: `03ie04`, `fn2l1u`, `mm5p3v`, `nna8yz`, `r2i1b1`, `ybkmzp`, each finalized on `main` by a commit its own dead lane is not an ancestor of (`bc9b3f43`, `e0c139ea`, `a912d5a9`, `14d5429a`, `84c5adcd`, `68930180`), each with the shipped symbol named in `kvf5xo`. (2) ONE LANE IS REPORTED ONCE PER RUN, because the dedup key includes `run_id` (runner_shared.py:1281-1285), so `7p9n2v`/`qcqhj7`/`rchpms` print 3 rows each and `58ha43` 2, turning 12 lanes into 19 violations. (3) EVERY ROW NAMES A WORKTREE THAT DOES NOT EXIST: all 19 print `.aw/worktrees/<id>` and zero of the 12 directories are on disk, because `lane_worktree_display` RECONSTRUCTS that string from the recorded absolute path to satisfy F8a's no-absolute-path rule (runner_shared.py:1345-1350) and nothing existence-checks it. (4) THE REMEDY NAMES A SHIPPED VERB AS MISSING: `attention.lane_remedy_hint` gates on `hasattr(oc_runipd, "cmd_integrate")` (attention.py:1312), a symbol that has NEVER existed (the real entry point is `handle_integrate_command`), so the stale "no `aw integrate` verb exists yet" prints unconditionally even though `aw oc integrate` shipped in executed plan `rl67b0` and is in `aw oc --help`; that steers an operator to a manual merge which SKIPS the merge-and-revalidate gate the verb routes through. NET: a gate permanently red on zero real losses, which is the alarm-fatigue outcome F3a's own "a check that fails on correct behavior is a check operators bypass" warns against, and which buries any FUTURE genuine strand.
- Scope: Fix the four reporting defects and amend F3a to match. Add a CONTENT-landed reading beside the ancestry one and consult both, so a re-executed lane is LANDED and silent; collapse the reported set to one row per lane branch while KEEPING the existing within-run collapse; existence-check the worktree before rendering it and omit it when absent; repair the dead `cmd_integrate` sentinel to probe a symbol that exists. AMENDS spec F3a to state the content-landed reading and the one-row-per-lane rule, declared in `Scope-Paths`. Does NOT change `describe_lane` (its body is pinned byte-for-byte against `tests/fixtures/runner_shared_premove_fingerprints.json` captured at HEAD `1ecc5891`, and `classify_lane_integration`'s docstring at runner_shared.py:1124-1130 records that editing it breaks a pure-move proof for an unrelated reason); does NOT change what `commits_ahead` MEANS, since `LANE_STALE`/`LANE_FOREIGN` adoption reads it; does NOT extend `SCAN_ROOTS` to `.aw/worktrees` or `.aw/records/runs`, which F3a forbids; does NOT delete, merge, prune or reclaim ANY lane, branch or worktree, so `aw attention` stays READ-ONLY per F3a and spec G3; and does NOT decide the DISPOSITION of the 12 currently-reported lanes, which is plan `ut0vzr`'s (`qliia1`).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/attention.py, tests/test_runner_shared.py, tests/test_attention.py, .aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, .aw/records/plans/pending/20260917-stranrep-01-0ta5vg-make-the-stranded-lane-report-tell-the-truth-content-landed.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: stranrep
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 0ta5vg
- From-Backlog: kvf5xo
- Blocks-Release: next

## Workflow history

- 2026-09-17 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-17 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog kvf5xo (with q96tpi, 46fb5i, fci7yn), all four measured at HEAD d188eaad; spec F3a amendment declared; maintainer chose one cohesive plan over a Set.

## Goal

Make `aw attention --check` silent when every lane's work is accounted for, and loud exactly once per lane when a lane genuinely holds unintegrated work. This restores the gate's credibility BEFORE plan `ut0vzr` triages the current 12 lanes, so that triage is measured against a report that does not lie.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the landing question answer what F3a actually asks

- [ ] E-01 Add a CONTENT-landed reading to `agent_workflows/runner_shared.py` as a NEW helper beside `lane_work_has_landed` (do NOT edit `describe_lane`, per the fingerprint pin cited in Scope). Decide whether every commit the lane adds beyond its merge-base is already represented on the target using `git cherry <target> <branch>`, which compares PATCH IDS and therefore sees a cherry-pick or a rebase: a result whose every line begins `-` means landed, any `+` line means at least one commit is genuinely absent. Return the SAME three-valued `True`/`False`/`None` contract `lane_work_has_landed` documents (runner_shared.py:1088-1092), mapping git failure and unresolvable refs to `None` so an unanswerable question stays UNKNOWN and never reads as either answer.
  - Depends on: none
  - Expected outcome: a helper returning True for a branch whose commits are all present on the target by patch id, False when at least one is absent, None when either ref does not resolve or git errors.
  - Execution state: pending

- [ ] E-02 Consult BOTH readings in `classify_lane_integration` (runner_shared.py:1110-1191) so `LANE_STRANDED` is reached only when the work is absent by ancestry AND by content. Preserve the documented decision ORDER exactly (LIVE first, then EMPTY, then the landing question) and leave `LANE_ATTENTION_STATES` (runner_shared.py:1068) unchanged, so this NARROWS what is reported without inventing a reportable state. Record which reading settled it on the returned record (`landed_by`, values `ancestor`/`content`/None) for debuggability. PRESERVE THE FAIL-CLOSED DIRECTION: if the ancestry reading says False and the content reading returns `None`, the lane is NOT silently landed; it stays reportable, because a false LANDED hides real loss and is strictly worse than the false STRANDED this plan is removing.
  - Depends on: E-01
  - Expected outcome: a cherry-picked lane classifies `LANDED` with `landed_by == "content"`; a genuinely unmerged lane still classifies `STRANDED`; an unanswerable lane stays reportable.
  - Execution state: pending

- [ ] E-03 Measure the six re-execution lanes against the new reading and record the per-lane result IN THIS PLAN before relying on it. For each of `03ie04`, `fn2l1u`, `mm5p3v`, `nna8yz`, `r2i1b1`, `ybkmzp`, run the content reading against the integration target and report the verdict and resulting `lane_state`. THIS IS A MEASUREMENT, NOT A TARGET: `03ie04` is the known risk, because its fix is present on `main` with the same rationale but was REIMPLEMENTED rather than cherry-picked (8% line overlap, measured), so patch-id equality may legitimately fail for it. Any lane the reading does not resolve is REPORTED, not reclassified, and its continued presence in the report is the CORRECT outcome, not a failure of this plan.
  - Depends on: E-02
  - Expected outcome: a six-row table giving, per lane, the content verdict and resulting `lane_state`, plus the honest count of how many the reading resolves and which remain reported.
  - Execution state: pending

### Task group 2: one lane, one row, and a row that is true

- [ ] E-04 Collapse the reported set to one row per lane branch in `runner_shared.stranded_lane_records`. The current key is `(run_id, branch, worktree)` (runner_shared.py:1281-1285) and its docstring justifies it as "one lane named by both an attempt and the item-level `preserved_*` fields yields one record", which is CORRECT for the within-run duplicate it was written for; it is the `run_id` component that is wrong ACROSS runs. KEEP the within-run collapse, then add a per-BRANCH collapse of the reported set, retaining the most informative record (prefer one carrying an `integration_signal`, then the highest `commits_ahead`) and carrying the run count plus the newest `run_id` so no evidence is dropped from the row. Update the docstring's dedup sentence, which will otherwise describe behavior that no longer exists.
  - Depends on: none
  - Expected outcome: at most one record per lane branch, each naming how many runs touched it and the newest run id.
  - Execution state: pending

- [ ] E-05 Existence-check the worktree before it is rendered. `lane_worktree_display` (runner_shared.py:1324-1353) returns a reconstructed `.aw/worktrees/<name>` from the recorded absolute path in its except branch (runner_shared.py:1345-1350), so all 19 rows assert a directory that is gone. Return None when the path does not exist, so the caller OMITS the segment (attention.py:1277-1279 already omits on None). PRESERVE F8a IN THE SAME DIRECTION: never return an absolute path, and prefer omission over leaking; omitting an absent worktree strictly REDUCES what is printed and so cannot introduce a leak. Do NOT satisfy this by walking `.aw/worktrees/`: F3a forbids a filesystem-derived VERDICT, and this checks only whether ONE already-derived display field should be rendered.
  - Depends on: none
  - Expected outcome: an absent worktree is omitted from the row; an existing one still renders repository-relative; no surface ever renders an absolute path.
  - Execution state: pending

- [ ] E-06 Repair the dead sentinel in `attention.lane_remedy_hint` (attention.py:1297-1320). It probes `hasattr(oc_runipd, "cmd_integrate")` (attention.py:1312); no such symbol exists (the integrate entry point is `handle_integrate_command`, and `cli.py:3929` forwards `aw oc integrate` as REMAINDER args rather than binding a `cmd_*` function), so the conditional froze in its pre-`rl67b0` state. Probe a symbol that exists, keep the function's own documented rule intact ("Do not print a verb that does not exist"), and name the concrete command using the record's `id6` where available. Add a test that FAILS if the probed symbol disappears, since a bare `hasattr` against a name nothing else references is unobservable when it rots; that unobservability is the actual defect, not the wrong string.
  - Depends on: none
  - Expected outcome: `lane_remedy_hint` returns the `aw oc integrate` remedy in this repository, still degrades to the manual hint where the verb is genuinely absent, and a test pins the probed name.
  - Execution state: pending

### Task group 3: bring the contract with the code

- [ ] E-07 Amend spec `attention-registry-and-cross-tree-status` F3a (spec line 231-234) for the two rules this plan establishes, since F3a is what every future reader of this surface is reviewed against. FIRST, the landing exclusion is satisfied by CONTENT reaching the target, not only by ancestry: F3a already REQUIRES the exclusion, and it is its "requires a reachability test against the target" wording that licensed the ancestor-only reading now producing six false strands. SECOND, one lane is at most one row. Append the history record with `aw specs note` naming plan `0ta5vg` as the cause. Do NOT weaken F3a's fail-closed posture, its run-record-not-filesystem rule, or F8a. NO `schema_version` BUMP IS EXPECTED: `render_json` puts only `{branch, rule, detail}` per lane into `stranded_lanes` (attention.py:1382-1386), so `landed_by` stays internal; if implementation surfaces it anyway, F8 obliges the bump and `SCHEMA_VERSION` (attention.py:41, currently 4) must be incremented with its comment block extended.
  - Depends on: E-02, E-04
  - Expected outcome: F3a states both rules, carries a history note citing this plan, and no other normative clause changes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE READER BY CONSTRUCTION: `runner_shared.stranded_lane_records` feeds both the end-of-run summary and the attention view, and its docstring states why ("two derivations of 'is this work lost' would drift and only one of them would be wrong at a time"). Both fixes belong there, not in either consumer.
- FINGERPRINT PINS FORBID CASUAL EDITS: `describe_lane` is held byte-for-byte against `tests/fixtures/runner_shared_premove_fingerprints.json` (HEAD `1ecc5891`). `lane_work_has_landed` exists as a separate helper precisely so the landing question could be added without touching it (runner_shared.py:1124-1130). New readings go in NEW helpers. Relatedly, `plan_bucket` documents itself in COMMENTS because a docstring is part of the AST and breaks that guard.
- THE TARGET IS `HEAD`, NOT `main`: `LANE_INTEGRATION_TARGET_FALLBACK = "HEAD"` (runner_shared.py:1074) and `attention.stranded_lane_drift` passes no target (attention.py:1259), so it takes that fallback. Tests must control HEAD rather than assume `main` exists.
- TESTS MUST NOT READ THE REAL REPO: backlog `no0j8g` records four `aw attention` tests that passed `dir=None` and so read the developer's own repository, making their exit codes depend on live state. New tests build temporary git repos.
- `aw attention` CANNOT BE MEASURED FROM INSIDE A LANE: `stranded_lane_drift` returns `[]` when it finds no run records (attention.py:1141-1145) and `.aw/records/runs/` is gitignored hence absent in a linked worktree, so an in-lane check reports a FALSE clean. This was established by `ut0vzr`'s review (PR-006); every acceptance check below names a non-lane tree.
- READ-ONLY IS A CONTRACT: F3a's closing clause and spec G3/8.1. Nothing here merges, deletes or reclaims.

## Findings

| # | Finding | Evidence (measured 2026-09-18, HEAD `d188eaad`, primary non-lane checkout) | Consequence |
|---|---|---|---|
| F-1 | 19 rows cover 12 lanes | `rows: 19 distinct: 12`; repeats `{58ha43: 2, 7p9n2v: 3, qcqhj7: 3, rchpms: 3}` | Count overstated 58%; `run_id` in the dedup key (runner_shared.py:1281-1285) |
| F-2 | 6 lanes are re-executed first attempts whose work IS on `main` | Finalize commits `bc9b3f43`/`e0c139ea`/`a912d5a9`/`14d5429a`/`84c5adcd`/`68930180`, none having the dead lane as ancestor; shipped symbols `oc_runipd.edge_satisfied` (comment cites "depreview 03ie04 E-01, OQ-01"), `attention_contract.actor_refusal:618`, `aw runs analyze --help`, `lane_containment.LANE_INPUT_SUBDIR`, `render_stream.Refusal`, `runner_shared.resolve_verification_decision` | Ancestry-only reading reports re-executed work as lost forever |
| F-3 | F3a ALREADY forbids this | Spec line 233: "a lane whose work HAS reached the integration target MUST NOT fail it either" | A spec VIOLATION, not a gap; raises severity and obliges the amendment |
| F-4 | All 19 rows name an absent worktree | `rows naming a worktree: 19, nonexistent: 19`; `.aw/worktrees/` held only `3v7wo6`, `fujm0y`, `perf-opt` and a review-sweep lane, none reported | Remediation points at a dead end and implies a recoverable tree |
| F-5 | The remedy's capability probe can never be True | `hasattr(oc_runipd,"cmd_integrate") = False`; `handle_integrate_command` present; `aw oc integrate` in `aw oc --help`; `rl67b0` is `executed` | Steers the operator to a manual merge that SKIPS the merge-and-revalidate gate |
| F-6 | Text similarity is NOT a sound landing test | Added-line presence 8-18% for lanes whose work is demonstrably on `main`; `03ie04` scored 8% yet its fix is present and cites the plan by id | E-01 must use patch ids; recorded so the discarded approach is not retried |
| F-7 | `65cuw0` delegates its new reclaim reading to the SAME broken predicate | Its E-01 computes `merged_into_target` by "DELEGATING to the existing `runner_shared.lane_work_has_landed`", mapping `None` to not-merged | Fixing E-01/E-02 here makes `65cuw0` reclaim strictly MORE. Its failure direction is safe (under-reclaims, never force-deletes), so this is not a blocking dependency, but the two must not diverge |
| F-8 | The payload does not carry per-lane state today | `render_json`'s `stranded_lanes` entries are `{branch, rule, detail}` only (attention.py:1382-1386); `SCHEMA_VERSION = 4` (attention.py:41) | `landed_by` can stay internal, so no `schema_version` bump is expected; E-07 states the condition under which it would be |

## Proposed changes (ordered, validatable)

1. New content-landed helper, patch-id based, three-valued (E-01).
2. `classify_lane_integration` consults both readings, records `landed_by`, keeps fail-closed on unanswerable (E-02).
3. Measure the six re-execution lanes and record per-lane results (E-03).
4. Per-branch collapse of the reported set, retaining run count and newest run id; docstring corrected (E-04).
5. Existence-check the worktree; omit when absent, never absolutize (E-05).
6. Repair the sentinel and pin the probed name with a test (E-06).
7. Amend F3a for both rules; bump `schema_version` only if `landed_by` surfaces (E-07).

## Deferred / out of scope (with reason)

- DISPOSITION OF THE 12 REPORTED LANES: plan `ut0vzr` (`laneorph-02`, from `qliia1`) owns it. This plan deliberately lands FIRST so that triage measures against a report that does not lie. Note for whoever sequences them: `ut0vzr`'s blocking OQ-04 asserts that deleting a branch converts a `lane-stranded` row into an equally-failing `lane-unknown` row; that is refuted by measurement (a deleted branch has no `commits_ahead`, so `holds_work` is False and EMPTY is reached BEFORE the landing question at runner_shared.py:1166-1171). Verified twice: already-deleted `tx6q0h` produces NO row (12 reported, not 13), and in a throwaway repo `STRANDED` becomes `EMPTY` after `git branch -D`. Recorded here as evidence for that plan's OQ, not resolved by this one.
- LANE TEARDOWN / WORKTREE RECLAMATION (4.7G): backlog `a58s04` and plan `65cuw0` own it. That is a WRITE against real worktrees, where this plan is read-only. F-7 records the shared predicate.
- THE DRIVER'S DESTRUCTIVE MERGE-ABORT (`csmtjp`): a real high-priority defect in `integrate_lane_branch`, but a different surface (the runner's merge path, not the reporting view) and independently filed.
- PRUNING RUN RECORDS that name long-gone lanes: the record is deliberately authoritative and historical (F3a), so rewriting it is out of scope; E-04/E-05 fix the RENDERING instead.
- A PROVABLE-REIMPLEMENTATION TEST: if `git cherry` cannot resolve a reimplemented lane (likely for `03ie04`), the honest outcome is that the lane stays reported for a human. Building a semantic-equivalence detector is out of scope and probably not tractable.

## Scope check

- Over-scope: none. Every E-item is one of the four measured defects or the spec amendment they oblige.
- Under-scope: this plan does not retire any lane, does not reclaim any worktree, and does not resolve `ut0vzr`'s OQ-04 (it supplies evidence only). After it lands, `aw attention` will still report any lane whose content reading is unresolvable, which is the intended fail-closed behavior and not a residual defect.

## Required tests / validation

Run the suite BARE as `python3 -m pytest` (the repo's `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; do NOT add `-n0`, a second `-q`, or `-p no:randomly`) and paste the actual `N passed` summary line, compared against a pre-change baseline captured at the same HEAD. New tests go in `tests/test_runner_shared.py` (content reading, classification, dedup) and `tests/test_attention.py` (row rendering, remedy hint). Every test constructs its own temporary git repository and passes an explicit `dir`, per the hazard backlog `no0j8g` records for exactly these tests; because the target defaults to `HEAD` (runner_shared.py:1074), a test must control HEAD explicitly. Any acceptance measurement of `aw attention` itself must be taken in a NON-LANE tree, since an in-lane run finds no run records and reports a false clean (attention.py:1141-1145).

## Spec / documentation sync

AMENDS `.aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` (F3a), declared in `Scope-Paths` so both runners announce the spec edit before the run and reconcile it at finalize. WHY THE AMENDMENT IS OBLIGATORY, not optional: F3a currently says the landing exclusion "requires a reachability test against the target", and that wording is what licensed the ancestor-only reading producing six false strands. Fixing the code alone would leave the next implementer correctly following prose that reproduces the defect. The amendment is NARROWING and additive: nothing that previously failed the gate stops failing except the case F3a already said must not fail, and the fail-closed posture, the run-record-not-filesystem rule and F8a are untouched. The spec is `implemented`; this plan returns it to accuracy rather than extending its surface. `schema_version` is expected to stay 4 (see F-8); E-07 names the condition that would change that.

## Open questions

### OQ-01: Should a content-landed lane be silent, or a distinct non-failing state?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SILENT. `LANE_ATTENTION_STATES` (runner_shared.py:1068) exists to separate reportable from correct states, and its comment states that `LANDED`, `EMPTY` and `LIVE` "are correct behavior and are deliberately silent". A content-landed lane IS landed, so it takes the existing `LANDED` path and adds no reportable state. `landed_by` preserves the distinction for debugging without spending a row on it.

### OQ-02: Does `git cherry` resolve all six re-execution lanes?

- Blocking: no
- Status: open
- Owner: executing agent
- Resolution or deferral rationale: DELIBERATELY UNRESOLVED; E-03 answers it by measurement. Patch-id equality cannot see a REIMPLEMENTATION, and `03ie04` is the known such case (its fix is on `main` citing the plan by id, at 8% line overlap). The plan does not depend on the answer: a lane the reading resolves becomes silent, a lane it does not stays reported for a human. Stated because the failure mode to avoid is an executor treating "all six resolve" as the target and loosening the predicate until they do; a false LANDED hides real loss and is worse than the false STRANDED being fixed.

### OQ-03: Should the row say "no worktree remains" rather than omitting the field?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: E-05 implements OMISSION, which is the minimum correct fix and matches the existing None-means-omit contract at attention.py:1277-1279. But "no worktree remains" is genuinely useful information, since it tells the reader recovery is a branch merge and not a tree inspection. Deferred to the maintainer as a presentation choice; omission is not blocked on it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the helper's source pasted, plus pytest output for three cases built in a TEMPORARY git repo: True where the lane's commits were cherry-picked onto the target, False where one commit is genuinely absent, None for an unresolvable ref. Paste the actual test output, not a description.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `classify_lane_integration` output pasted for THREE constructed lanes: cherry-picked (expect `LANDED`, `landed_by == "content"`), genuinely unmerged (expect `STRANDED`), and one whose content reading returns None while ancestry says False (expect STILL REPORTABLE, proving the fail-closed direction). Show `lane_state` and `needs_attention` for each.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the six-row table with the content verdict and resulting `lane_state` per lane, plus the honest count resolved. Name any lane still reported and confirm that is the intended outcome rather than a defect.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `aw att --format json` re-run in a NON-LANE tree, with row count and distinct-lane count pasted, showing at most one row per branch and the previously-tripled `7p9n2v`/`qcqhj7`/`rchpms` and doubled `58ha43` appearing once each. Show the retained record still carries the run count. Plus a unit test proving a single run naming one lane by both an attempt and `preserved_*` still yields ONE record (the within-run collapse must survive).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: a row (or unit test) for a lane whose worktree is absent, pasted, showing NO `worktree` segment; and one whose worktree exists, showing the repo-relative path still rendered. Confirm by inspection that no surface emits an absolute path.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -c "from agent_workflows import attention; print(attention.lane_remedy_hint())"` output pasted showing the `aw oc integrate` remedy; plus pytest output for the fallback case (symbol patched away) AND for the new test that fails if the probed name disappears.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the F3a diff pasted, plus the appended spec history record naming this plan. Confirm the fail-closed posture, the run-record-not-filesystem rule and F8a are unchanged. State explicitly whether `landed_by` reached the `--json` payload and therefore whether `SCHEMA_VERSION` was bumped from 4.
  - Observed evidence:
  - Result: pending

WHOLE-PLAN EVIDENCE, required in addition to the per-item evidence above and recorded at V-04 (whose surface is the report itself): bare `python3 -m pytest` output with the actual `N passed` summary line pasted, against a pre-change baseline at the same HEAD; and the `aw attention --check` exit code taken in a NON-LANE tree, which must be 0 if no lane genuinely holds unintegrated work, or must fail naming ONLY lanes whose landing is genuinely unresolvable.

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The four defects are ONE cohesive change (the same ~60 lines across two modules) authored as one plan at the maintainer's explicit direction, having considered a two-child Set and rejected it as lifecycle overhead for that blast radius.

The executing agent must: commit ONLY files it changed, path-scoped (`git commit -m msg -- <path>`), never `git add -A` or `-a`, and never push; verify the staged set with `git diff --cached --name-only` before EVERY commit and RE-VERIFY after any failed hook, because this is a SHARED checkout with other agents active (backlog `csmtjp` records a concurrent merge being destroyed here, and during this plan's authoring HEAD moved four times and three files belonging to a co-worker appeared and were committed by them); paste ACTUAL runner output rather than claiming success.

NOTHING IN THIS PLAN IS DESTRUCTIVE: it merges no lane, deletes no branch, and removes no worktree. If an E-item appears to require one of those, STOP: the item has been misread, and the disposition of a lane belongs to `ut0vzr`. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry pasted evidence before the plan moves to `.aw/records/plans/executed/`.
