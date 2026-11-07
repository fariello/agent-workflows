# IPD: Supersede spec 2vev8j and re-home backlog ms06pi's release gate to 4sd62s

- Date: 2026-11-02
- Kind: child
- Concern: Approved spec `4sd62s` SUPERSEDES approved spec `2vev8j` (4sd62s "Relation to prior work"; OQ-4, maintainer ruling 2026-10-24, SR-102), but the records still say otherwise. Measured 2026-11-02: `2vev8j` sits in `.aw/records/specs/approved/` with `- Status: approved`, `- From-Backlog: ms06pi` and `- Blocks-Release: next`, so `aw releases show next` lists BOTH `2vev8j` and `4sd62s` as live blockers of release 2.0.0 (`f33nrj`); `4sd62s` carries no `- From-Backlog:`, so backlog `ms06pi` (`graduated`, `Blocks-Release: next`) hands its gate only to a spec that will never be implemented; and `rg -l 2vev8j agent_workflows tests` returns 16 files (8 modules, 8 tests) whose comments, docstrings and one user-facing recovery string cite the superseded spec as the authority. Spec section 7 requires this to be fixed by the first plan of phase A, "so that the records are consistent before any code changes".
- Scope: Records and citation hygiene only. Transition `2vev8j` to `superseded` with a history message citing `4sd62s`, and clear its `- From-Backlog:` so it stops counting as an unshippable carrier of `ms06pi`; add `- From-Backlog: ms06pi` to `4sd62s` with the tooled setter; record the handoff on `ms06pi`; re-point every `2vev8j` citation in `agent_workflows/` and `tests/` to the `4sd62s` section that now holds the rule. EXCLUDES any behavior change, any code other than comments, docstrings and one recovery-hint string, and `CHANGELOG.md` (released history).
- Scope-Paths: .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md, .aw/records/specs/superseded/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md, .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md, agent_workflows/artifact_core.py, agent_workflows/attention.py, agent_workflows/backlog.py, agent_workflows/check_engine.py, agent_workflows/ipd_authoring.py, agent_workflows/record_history.py, agent_workflows/specs.py, agent_workflows/status_set.py, tests/test_backlog.py, tests/test_backlog_history_dedup_parity.py, tests/test_history_date_clock.py, tests/test_history_date_clock_parity.py, tests/test_history_date_clock_residual.py, tests/test_history_date_clock_sidecar.py, tests/test_history_label_parity.py, tests/test_scaffold_history_clock.py, .aw/records/plans/pending/20261102-metastore-01-7ehv8l-supersede-spec-2vev8j-and-re-home-backlog-ms06pi-s-release-g.ipd.md
- Item-Dependencies: none
- Status: executed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7ehv8l
- Readiness: go-pending-approval
- Review-Depth: standard

## Workflow history
- 2026-11-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 7ehv8l verified (set metastore, attempt 1).
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 FIXED; review record .aw/records/reviews/20261102-metastore-01-7ehv8l-supersede-spec-2vev8j-and-re-home-backlog-ms06pi-s-release-g.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the records agree with the maintainer's ruling that `4sd62s` replaces `2vev8j`: one live metadata spec, one carrier of `ms06pi`'s release gate, and code comments that cite the spec that now owns each rule.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [x] E-01 Record the baseline before any change: save `aw check --agent` to `.aw/state/7ehv8l/check-before.jsonl` (gitignored and inside the workspace; a runner lane may refuse writes outside it, measured at review), and save the output of `aw releases show next`, `aw specs check`, `rg -l 2vev8j agent_workflows tests` and `python3 -c "from pathlib import Path; from agent_workflows import check_engine as c; print(c.find_from_backlog_artifacts(Path('.').resolve(), 'ms06pi'))"`.
  - Depends on: none
  - Expected outcome: the release blocker list names `2vev8j` and `4sd62s`; the carrier list names only `2vev8j`; the `rg` file list is saved and is the set of files E-05 and E-06 must change (16 files, 8 modules and 8 tests, at authoring; re-derive it here and use the list this step prints, not the authoring count).
  - Execution state: performed

### Task group 2: records

- [x] E-02 Supersede `2vev8j` through the tooled setter and clear its backlog link in the same call: `aw specs set superseded 2vev8j --from-backlog - --message "Superseded by spec 4sd62s (4sd62s OQ-4, maintainer ruling 2026-10-24, SR-102). Surviving rules folded into 4sd62s 4.2, 4.2a, 4.2b, 4.5. Release-gate handoff of backlog ms06pi moved to 4sd62s (plan 7ehv8l)." --no-commit`. Leave its `- Blocks-Release: next` line unchanged (a superseded spec is not a live blocker: measured on a scratch copy, `aw releases show next` stops listing it after the transition, and rewriting the line would alter what the record says it gated).
  - Depends on: E-01
  - Expected outcome: the file moves to `.aw/records/specs/superseded/`, carries `- Status: superseded`, no `- From-Backlog:` line, and a new history line naming `4sd62s`.
  - Execution state: performed

- [x] E-03 Link `4sd62s` to the backlog item with the tooled setter: `aw specs set approved 4sd62s --from-backlog ms06pi --message "Inherits the release-gate handoff of backlog ms06pi from superseded spec 2vev8j (4sd62s OQ-4; plan 7ehv8l). Status unchanged." --no-commit`. Status stays `approved`; the call is a same-status write whose only field change is `- From-Backlog: ms06pi` (measured on a scratch copy). Its existing `- Blocks-Release: next` already matches `ms06pi`, so `check.from-backlog-gate-mismatch` has nothing to report.
  - Depends on: E-02
  - Expected outcome: the `4sd62s` front matter gains exactly one line, `- From-Backlog: ms06pi`, and one history line; no other byte of the spec changes.
  - Execution state: performed

- [x] E-04 Record the handoff on the backlog item without changing its status: `aw backlog set graduated ms06pi --message "Release-gate handoff moved from superseded spec 2vev8j to spec 4sd62s, which now carries - From-Backlog: ms06pi and the same - Blocks-Release: next (4sd62s OQ-4; plan 7ehv8l). Still graduated, not done: no code is written." --no-commit`.
  - Depends on: E-03
  - Expected outcome: `ms06pi` stays in `graduated/` with `- Status: graduated` and `- Blocks-Release: next`; one new history line names `4sd62s`.
  - Execution state: performed

### Task group 3: citations

- [x] E-05 Re-point the `2vev8j` citations in the modules from the E-01 list (8 modules at authoring), comment and docstring text only plus one recovery hint, using this mapping (each 4sd62s section quoted from the spec): `2vev8j` 4.4 UTC writer rule -> `4sd62s` 4.2b; `2vev8j` 4.3 per-artifact seq -> `4sd62s` 4.2; `2vev8j` C5 (no event before the durable write) -> `4sd62s` C6; `2vev8j` E1 (shared JSONL append conflicts) -> `4sd62s` P3 (which cites that measured evidence) and C3 and 4.7 (per-artifact logs so different artifacts never share a file); keep the sentence a citation of where the measurement is recorded, not a claim that `4sd62s` made it. Files: `artifact_core.py` (the `utc_history_date` banner and docstring), `attention.py`, `backlog.py` (two sidecar-order comments), `check_engine.py` (the `check.lifecycle-transition-unvalidated` rule comment and docstring, its `recovery=` hint which becomes "wait for spec 4sd62s 4.2 per-artifact seq", and the namespace-gate comment, a historical measurement, which becomes "spec 6m4kow and the artifact-metadata-storage spec since superseded by 4sd62s"), `ipd_authoring.py`, `record_history.py`, `specs.py`, `status_set.py`.
  - Depends on: E-01
  - Expected outcome: `rg -n 2vev8j agent_workflows` prints nothing; `git diff --stat agent_workflows` shows only the modules from the E-01 list; every changed line is a comment, a docstring, or the one `recovery=` string.
  - Execution state: performed

- [x] E-06 Re-point the `2vev8j` citations in the test files from the E-01 list (8 files at authoring; module docstrings and inline comments only; no assertion reads the spec id, measured with `rg -n 2vev8j tests`): `test_backlog.py`, `test_backlog_history_dedup_parity.py`, `test_history_date_clock.py`, `test_history_date_clock_parity.py`, `test_history_date_clock_residual.py`, `test_history_date_clock_sidecar.py`, `test_history_label_parity.py`, `test_scaffold_history_clock.py`, using the E-05 mapping (the "One timezone for every writer" rule is `4sd62s` 4.2b "One clock for each stored value").
  - Depends on: E-01
  - Expected outcome: `rg -l 2vev8j agent_workflows tests` prints nothing; no test logic changes.
  - Execution state: performed

### Task group 4: verification and commit

- [x] E-07 Verify and commit: rerun the E-01 commands and diff the `(location, rule)` pairs of `aw check --agent` against `.aw/state/7ehv8l/check-before.jsonl`; run `python3 -m pytest -o addopts="" -n auto tests/test_backlog.py tests/test_backlog_history_dedup_parity.py tests/test_history_date_clock.py tests/test_history_date_clock_parity.py tests/test_history_date_clock_residual.py tests/test_history_date_clock_sidecar.py tests/test_history_label_parity.py tests/test_scaffold_history_clock.py tests/test_check_engine_release_gate.py tests/test_release_gate_one_way_mismatch.py`, the bare core gate `python3 -m pytest`, `aw check release-gates` and `aw sanitize --agent`; commit through `aw commit 7ehv8l -- <every Scope-Paths path that changed>`. Never push.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: both pytest runs pass; `aw check` shows no new error or warning (the only path change is `2vev8j`'s pre-existing `check.spec-criteria-uncovered` advisory moving with the file; any other difference is named and traced to a cause, such as a date-derived rule crossing midnight); `aw releases show next` lists `ms06pi` and `4sd62s` and not `2vev8j`; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Spec status is owned by `aw specs set` (AGENTS.md "What needs attention"); `attention_contract.SPEC_TRANSITIONS["approved"]` contains `superseded`, so `approved -> superseded` is a legal edge and needs no override. The setter relocates the file to `superseded/` (`.aw/records/specs/README.md`, "Location agrees with status").
- `aw specs set` accepts `--from-backlog <id6|->` on any call, including a same-status call (`aw specs set --help`); measured on a scratch copy, `aw specs set approved 4sd62s --from-backlog ms06pi` writes `- From-Backlog: ms06pi` and reports status `unchanged`.
- The close-legitimacy predicate is `check_engine.evaluate_blocking_close`. Its HANDOFF route requires at least one same-gate carrier AND that EVERY carrier from `check_engine.find_from_backlog_artifacts` is finished per `check_engine._carrier_is_executed` (a spec counts only at `implemented`). A superseded spec never reaches `implemented`, so a `2vev8j` that kept `- From-Backlog: ms06pi` would block `ms06pi` from closing through HANDOFF forever (measured below, F-04).
- Setters append to the gitignored sidecar `.aw/records/history.jsonl` (`record_history.append`); that file is never committed.
- Commits go through `aw commit <id6> -- <paths>` (AGENTS.md execution contract); setters here run with `--no-commit` so the plan's single commit holds every change.

## Findings

| Id | Evidence (measured 2026-11-02 at `0cbfcc706`) | Finding |
|---|---|---|
| F-01 | `rg -l 2vev8j agent_workflows tests` lists 16 files; `rg -c` gives 18 lines in 8 modules and 14 lines in 8 tests | Matches the spec's OQ-4 count of 16 files. |
| F-02 | `aw releases show next` lists `ms06pi`, `2vev8j` and `4sd62s` | `2vev8j` is still counted as a live blocker of 2.0.0. |
| F-03 | `find_from_backlog_artifacts(repo, 'ms06pi')` returns only the `2vev8j` spec | The gate is handed to the superseded spec only. |
| F-04 | Scratch copy, `2vev8j` superseded with its `From-Backlog` kept and `4sd62s` linked: `evaluate_blocking_close(..., 'done')` refuses and names BOTH carriers as not shipped | Clearing `2vev8j`'s `From-Backlog` is required, not cosmetic. After clearing it, the verdict names only `4sd62s`, which is correct until `4sd62s` is implemented. |
| F-05 | Scratch copy after the E-02 to E-04 steps (re-measured at review 2026-11-06 on a scratch clone of `bfdcb514f`: same result, `aw check` severity counts unchanged at 14 error, 1 warning, 55 info): `aw releases show next` lists `ms06pi` and `4sd62s`; `aw check release-gates` reports 0 errors; `aw check` adds no finding for `2vev8j`, `ms06pi` or `4sd62s` once the metastore plans are present | The record change is safe for every release-gate rule. |
| F-06 | `rg -n "per-artifact seq" tests` returns nothing | No test asserts the `check_engine` recovery hint text, so re-pointing it changes no test. |
| F-07 | `CHANGELOG.md` cites `2vev8j` twice (lines for the lifecycle-unvalidated rule and the UTC unification) | Those are entries describing work as it shipped; see Deferred. |

## Proposed changes (ordered, validatable)

1. E-01 baseline.
2. Records: supersede `2vev8j` and clear its link; link `4sd62s`; note the handoff on `ms06pi`.
3. Citations: modules, then tests.
4. Verify, gates, commit.

## Deferred / out of scope (with reason)

- `CHANGELOG.md` citations of `2vev8j`: changelog entries describe what shipped and what it cited at the time; rewriting them would misstate history.
  - Carrier-Declined: released-history text is not re-pointed; the superseded spec stays findable through `4sd62s` "Relation to prior work".
- Citations of `2vev8j` inside other records (82 record files, including executed plans and implemented spec `wy9aru`): AGENTS.md forbids changing what executed records say, and the spec's OQ-4 scope is the code and test files only.
  - Carrier-Declined: record history is immutable by repository rule; the cutover citation rewrite (5.2 step 3) covers only the 34 renamed legacy filenames, not this id.
- Recording `- Graduated-To: metastore` on `ms06pi`: not required for the gate handoff, which `From-Backlog` on the carrier establishes.
  - Carrier-Declined: optional navigation field; the handoff link is the carrier's `- From-Backlog:`.

## Scope check

- Over-scope: none.
- Under-scope: none. Spec OQ-4 asks for three things (supersede with a reference, re-point the 16 files, move the `ms06pi` handoff) and lists `2vev8j` in Scope-Paths; all are covered, with both the old and new path of `2vev8j` declared because the setter moves the file.

## Required tests / validation

- Acceptance criteria: this plan OWNS no `4sd62s` AC and CONTRIBUTES to none; it implements OQ-4 and the section 7 sentence "The first plan of phase A also SUPERSEDES `2vev8j`".
- Release-gate behavior: `aw releases show next` before and after; `evaluate_blocking_close` carrier list before and after; `aw check release-gates`.
- No behavior change: the named history-clock and release-gate test modules plus the bare core gate pass.

## Spec / documentation sync

Amends two spec records through tooled setters only, both declared in Scope-Paths: `2vev8j` moves to `superseded/` and loses `- From-Backlog:`; `4sd62s` gains `- From-Backlog: ms06pi`. Why: OQ-4 of `4sd62s` requires the supersession and the handoff, and the handoff is what lets `ms06pi` close legitimately once `4sd62s` is implemented. No spec body text changes.

## Open questions

### OQ-01: Does a same-status `aw specs set approved 4sd62s` read as a second approval?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The setter writes a history line whose token is `approved` with the explicit message "Status unchanged", carries no `--by-human` attestation, and leaves the existing 2026-11-02 human approval line intact. The alternative, `aw specs note`, cannot write `--from-backlog` (its help lists no such option), and a hand edit of the field would bypass the tooled-write rule. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the baseline `aw releases show next` rows for `ms06pi`, `2vev8j` and `4sd62s`; the printed `find_from_backlog_artifacts` list (one `2vev8j` path); the full `rg -l 2vev8j agent_workflows tests` output as re-derived at execution; and `ls .aw/state/7ehv8l/check-before.jsonl`.
  - Observed evidence:
    `aw releases show next` baseline rows:
    ```
    ms06pi  backlog  graduated     high      .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md
    ...
    2vev8j  specs    approved      -         .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    4sd62s  specs    approved      -         .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md
    ```

    `find_from_backlog_artifacts` output:
    ```
    [(PosixPath('.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md'), 'next')]
    ```

    `rg -l 2vev8j agent_workflows tests`:
    ```
    agent_workflows/backlog.py
    agent_workflows/status_set.py
    agent_workflows/specs.py
    agent_workflows/attention.py
    agent_workflows/record_history.py
    agent_workflows/check_engine.py
    agent_workflows/artifact_core.py
    agent_workflows/ipd_authoring.py
    tests/test_history_date_clock.py
    tests/test_backlog.py
    tests/test_history_date_clock_parity.py
    tests/test_history_label_parity.py
    tests/test_backlog_history_dedup_parity.py
    tests/test_history_date_clock_sidecar.py
    tests/test_scaffold_history_clock.py
    tests/test_history_date_clock_residual.py
    ```

    `ls .aw/state/7ehv8l/check-before.jsonl`:
    ```
    .aw/state/7ehv8l/check-before.jsonl
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git status --short` showing the rename `specs/approved/...2vev8j... -> specs/superseded/...2vev8j...`, and `git diff -M` of that file showing `- Status: approved` -> `- Status: superseded`, the removed `- From-Backlog: ms06pi` line, the unchanged `- Blocks-Release: next` line, and the new history line containing `4sd62s`.
  - Observed evidence:
    `git status --short`:
    ```
    D  .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    AM .aw/records/specs/superseded/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    ```

    `git diff -M HEAD`:
    ```diff
    diff --git a/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md b/.aw/records/specs/superseded/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    similarity index 98%
    rename from .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    rename to .aw/records/specs/superseded/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    index b08d8d84f..d7c12dba2 100644
    --- a/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    +++ b/.aw/records/specs/superseded/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    @@ -1,11 +1,10 @@
     # Spec: Artifact metadata storage: per-artifact history journals and explicit event ordering

     - Date: 2026-09-08
    -- Status: approved
    +- Status: superseded
     - Id: 2vev8j
     - Author: aw specs new
     - Scope: Where aw-owned artifact metadata lives: front matter stays inline; unbounded workflow history moves to git-tracked per-artifact JSONL keyed by id6, ordered by an explicit per-artifact seq
    -- From-Backlog: ms06pi
     - Blocks-Release: next
     - Canonical: true

    @@ -336,6 +335,7 @@ Both are real and neither is a storage decision. They must NOT be absorbed silen


     ## Workflow history
    +- 2026-11-07 superseded (aw set): Superseded by spec 4sd62s (4sd62s OQ-4, maintainer ruling 2026-10-24, SR-102). Surviving rules folded into 4sd62s 4.2, 4.2a, 4.2b, 4.5. Release-gate handoff of backlog ms06pi moved to 4sd62s (plan 7ehv8l).

     - 2026-10-13 note (aw specs): amend Section 4.4: bind date readers to the clock of their stored operand (IPD hinpcf, backlog 6ly144)
     - 2026-10-08 approved (aw specs, --by-human): amend Section 7 write-order bullet (IPD ulepef E-05)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff` of the `4sd62s` spec showing exactly two added lines (`- From-Backlog: ms06pi` in the front matter and one history line containing `ms06pi`) and no removed line; paste `aw specs check` output reporting all specs conform.
  - Observed evidence:
    `git diff .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md b/.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md
    index 5de0f92a0..daafd981c 100644
    --- a/.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md
    +++ b/.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md
    @@ -2,6 +2,7 @@

     - Date: 2026-09-25
     - Status: approved
    +- From-Backlog: ms06pi
     - Blocks-Release: next
     - Id: 4sd62s
     - Author: aw specs new
    @@ -2332,6 +2333,7 @@ for concurrency.
     | `tg80ht` spec-to-plan bridge | open (backlog) | Connects approved specs to runner dispatch and to IPD Set authoring. It automates the graduation of this spec into the implementing IPD Set and does not change the metadata schema. |

     ## Workflow history
    +- 2026-11-07 approved (aw set): Inherits the release-gate handoff of backlog ms06pi from superseded spec 2vev8j (4sd62s OQ-4; plan 7ehv8l). Status unchanged.

     - 2026-11-05 note (aw specs): Amended 2026-11-02 on maintainer decision (plan cxxmyv OQ-01, via /askme): event key overrides (list of setter override flags) added to 4.2; aw specs set --date refused once metadata_schema is 2. Spec stays approved; the change is an additive event key decided by the maintainer.
     - 2026-11-02 note (aw specs): Editorial fix after approval: removed a fragment ('the run') left in section 7 step 1 by the 2026-11-01 split; no requirement changed.
    ```

    `aw specs check`:
    ```
    aw specs check: all specs conform. 49 specs checked.
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff` of the `ms06pi` backlog file showing one added history line naming `4sd62s` and no change to `- Status: graduated` or `- Blocks-Release: next`; paste the post-change `find_from_backlog_artifacts(..., 'ms06pi')` output listing exactly the `4sd62s` path.
  - Observed evidence:
    `git diff .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md`:
    ```diff
    diff --git a/.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md b/.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md
    index 6b1c0ffb4..ee114f394 100644
    --- a/.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md
    +++ b/.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md
    @@ -65,6 +65,7 @@ DO NOT resolve this by reordering the plan histories. That satisfies a parser wh
     convention the executed corpus follows, and `tk1gqo` already considered and rejected it.

     ## Workflow history
    +- 2026-11-07 same-status (aw set): Release-gate handoff moved from superseded spec 2vev8j to spec 4sd62s, which now carries - From-Backlog: ms06pi and the same - Blocks-Release: next (4sd62s OQ-4; plan 7ehv8l). Still graduated, not done: no code is written.
     - 2026-09-08 graduated (aw set): GRADUATED to spec 2vev8j (.aw/records/specs/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md), which carries - From-Backlog: ms06pi and inherits this item's - Blocks-Release: next, so the release gate is provably handed off rather than dropped. GRADUATED, NOT DONE: the design is settled and handed off; no code is written. THE GATE IS ANSWERED. Research prompt 27rjro is consumed: five reports adopted 2026-09-08 and reconciled in 6mye7n. Four independent models reached the SAME design without conferring (front matter stays INLINE; unbounded ## Workflow history moves to git-tracked, append-only, PER-ARTIFACT JSONL keyed by the immutable id6; ordering by an explicit per-artifact seq, never by parsing dates; SQLite only as a gitignored disposable cache), and all four independently reject the single global file, tracked SQLite, moving front matter out, and bulk-reordering the corpus. WHERE THE REPORTS SPLIT, THE SPEC ADJUDICATES RATHER THAN PICKING A SIDE. On the inline residue (spec 4.5): keep exactly ONE line AND make IPD-S405 read the history API, because pavnai's justification is wrong on its own terms (executed -> superseded breaks 'the latest entry is always executed', which is precisely xn6f6u's eviction argument) while xn6f6u's conclusion assumes IPD-S405 is immovable when the rule must be rewritten anyway. On the journal path (spec 4.2): key on the IMMUTABLE id6, deciding AGAINST 2o895n's basename-derived sidecar, on a property of this repo that report could not observe (artifacts are renamed and moved constantly). THREE CLAIMS RE-MEASURED AT HEAD 57143149 RATHER THAN INHERITED, all superseding this item's own figures: the corpus is 591 plans / 15,639,697 chars, not the 483 / 10,823,121 recorded here, so the token case is STRONGER not weaker and every percentage must be re-derived at implementation; the heading is referenced by 18 modules, not the 19 this item and all four reports state; and record_history.py's own docstring claim that append-only files 'rarely conflict' is EMPIRICALLY FALSE (two branches appending one line each to the same JSONL conflict on merge), which matters doubly because aw oc run isolates every execute item in its own worktree, making the global file a conflict magnet on the normal execution path. TWO DEFECTS FOUND WHILE ANSWERING THIS, both recorded in the spec as OUT OF SCOPE so they are not absorbed silently: attention_contract.py:32-33 defines last_history_at as the LAST record in file order while the plan writers PREPEND, so the attention view reads the OLDEST record and calls it newest (a live bug, caught by takpys alone); and the specs/backlog writers append their sidecar event BEFORE validation and BEFORE the dry-run/apply decision, so a PREVIEW or a REFUSED transition can leave a phantom event. FIRST ACTION FOR THE IMPLEMENTER, ahead of any code: export and preserve .aw/records/history.jsonl. 176 of its 177 records are specs/backlog history that exists ONLY on this machine, because that inline history was already slimmed to one line while the sidecar is gitignored, so a fresh clone has NEITHER copy. This is the most damaging CURRENT defect and it is unrecoverable local state. THE SPEC IS AT to-review, NOT approved, and that is deliberate: aw specs set refused approved because the anti-self-approval floor requires a review record naming 2vev8j, and none exists. Design is handed off; IMPLEMENTATION IS NOT YET LICENSED. The spec's OQ-1 is BLOCKING and needs a human: whether backward lifecycle edges (approved -> reviewed) are legal is a policy call the event store exposes but cannot answer.
    ```

    `find_from_backlog_artifacts` post-change output:
    ```
    [(PosixPath('.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md'), 'next')]
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `rg -n 2vev8j agent_workflows` (empty output and exit code 1), `git diff --stat -- agent_workflows` listing exactly the modules from the V-01 list, `git diff -U0 -- agent_workflows | rg '^[-+][^-+]'` showing every changed line is a comment, a docstring line, or the `recovery=` string, and the `git diff` hunk of the `check_engine.py` `recovery=` string.
  - Observed evidence:
    `rg -n 2vev8j agent_workflows`:
    ```
    (exit code 1, empty output)
    ```

    `git diff --stat -- agent_workflows` (from commit `1aaa67d2664e9e63a3264e99c6f582fda92a68c1`):
    ```
     agent_workflows/artifact_core.py  |  4 ++--
     agent_workflows/attention.py      |  2 +-
     agent_workflows/backlog.py        |  4 ++--
     agent_workflows/check_engine.py   | 10 +++++-----
     agent_workflows/ipd_authoring.py  |  6 +++---
     agent_workflows/record_history.py |  9 +++++----
     agent_workflows/specs.py          |  6 +++---
     agent_workflows/status_set.py     |  2 +-
     8 files changed, 22 insertions(+), 21 deletions(-)
    ```

    `git diff -U0 HEAD~1 HEAD -- agent_workflows | rg '^[-+][^-+]'`:
    ```
    -# Workflow history UTC date helper (spec 2vev8j Section 4.4; IPD 5ivkdh E-01)
    +# Workflow history UTC date helper (spec 4sd62s Section 4.2b; IPD 5ivkdh E-01)
    -    Authority: Spec ``2vev8j`` Section 4.4 ("One timezone for every writer") requires all history
    +    Authority: Spec ``4sd62s`` Section 4.2b ("One clock for each stored value") requires all history
    -    else '' (recent). Reads the UTC clock per spec 2vev8j Section 4.4 so verdicts are invariant under reader timezone."""
    +    else '' (recent). Reads the UTC clock per spec 4sd62s Section 4.2b so verdicts are invariant under reader timezone."""
    -    # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
    +    # Spec `4sd62s` C6 first clause: the sidecar may never precede the durable write it describes,
    -    # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
    +    # Spec `4sd62s` C6 first clause: the sidecar may never precede the durable write it describes,
    -    # Event-derived lifecycle transition coverage companion (IPD 5xq2ng E-01, spec 2vev8j Section 4.4).
    -    # The lifecycle gate's inputs are DATE-DERIVED, and the UTC history-date ruling (spec 2vev8j 4.4)
    +    # Event-derived lifecycle transition coverage companion (IPD 5xq2ng E-01, spec 4sd62s Section 4.2b).
    +    # The lifecycle gate's inputs are DATE-DERIVED, and the UTC history-date ruling (spec 4sd62s 4.2b)
    -    observable when date variation is collapsed by UTC history-date unification (spec 2vev8j 4.4).
    +    observable when date variation is collapsed by UTC history-date unification (spec 4sd62s 4.2b).
    -                        "spec 2vev8j 4.3 per-artifact seq"
    +                        "spec 4sd62s 4.2 per-artifact seq"
    -        # (spec 6m4kow and 2vev8j are the ONLY reported specs at HEAD without this gate, both namespace
    +        # (spec 6m4kow and the artifact-metadata-storage spec since superseded by 4sd62s are the ONLY reported specs at HEAD without this gate, both namespace
    -    to ``when`` if omitted. The history date is recorded in UTC per spec ``2vev8j`` Section 4.4
    -    ("One timezone for every writer"), whereas the ``- Date:`` metadata field (and the artifact's
    +    to ``when`` if omitted. The history date is recorded in UTC per spec ``4sd62s`` Section 4.2b
    +    ("One clock for each stored value"), whereas the ``- Date:`` metadata field (and the artifact's
    -    # History records record UTC per spec 2vev8j Section 4.4 (reusing artifact_core.utc_history_date,
    +    # History records record UTC per spec 4sd62s Section 4.2b (reusing artifact_core.utc_history_date,
    -concurrent-append git merges rarely conflict was measured false in spec 2vev8j E1 (two branches
    -each appending one line to the same JSONL produce an ordinary content conflict, making a shared
    -file a conflict magnet under the isolated worktrees aw oc run uses by default), and the claim is
    +concurrent-append git merges rarely conflict was measured false in spec 4sd62s P3 (which cites that
    +measured evidence) and C3 and 4.7 (per-artifact logs so different artifacts never share a file; two
    +branches each appending one line to the same JSONL produce an ordinary content conflict, making a
    +shared file a conflict magnet under the isolated worktrees aw oc run uses by default), and the claim is
    -    merges were measured to conflict (spec 2vev8j E1), though moot as this sidecar is gitignored."""
    +    merges were measured to conflict (spec 4sd62s P3, C3, 4.7), though moot as this sidecar is gitignored."""
    -    Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
    +    Spec `4sd62s` C6 first clause: the sidecar may never precede the durable write it describes,
    -        # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
    +        # Spec `4sd62s` C6 first clause: the sidecar may never precede the durable write it describes,
    -        # Spec 2vev8j Section 4.4: Every writer records UTC for history records.
    +        # Spec 4sd62s Section 4.2b: Every writer records UTC for history records.
    -    # The write happens AFTER the durable write succeeds (spec 2vev8j C5).
    +    # The write happens AFTER the durable write succeeds (spec 4sd62s C6).
    ```

    `git diff` hunk of `check_engine.py` `recovery=` string:
    ```diff
    @@ -3959,5 +3959,5 @@ def check_lifecycle_transition_coverage(
                         recovery=(
                             "order history entries across distinct dates or wait for "
    -                        "spec 2vev8j 4.3 per-artifact seq"
    +                        "spec 4sd62s 4.2 per-artifact seq"
                         ),
                     )
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `rg -l 2vev8j agent_workflows tests` (empty output, exit code 1) and `git diff --stat -- tests` listing exactly the test files from the V-01 list, plus `git diff -U0 -- tests | rg '^[-+][^-+]'` showing every changed line is a comment or docstring line.
  - Observed evidence:
    `rg -l 2vev8j agent_workflows tests`:
    ```
    (exit code 1, empty output)
    ```

    `git diff --stat HEAD~1 HEAD -- tests`:
    ```
     tests/test_backlog.py                      | 2 +-
     tests/test_backlog_history_dedup_parity.py | 4 ++--
     tests/test_history_date_clock.py           | 8 ++++----
     tests/test_history_date_clock_parity.py    | 4 ++--
     tests/test_history_date_clock_residual.py  | 2 +-
     tests/test_history_date_clock_sidecar.py   | 2 +-
     tests/test_history_label_parity.py         | 4 ++--
     tests/test_scaffold_history_clock.py       | 2 +-
     8 files changed, 14 insertions(+), 14 deletions(-)
    ```

    `git diff -U0 HEAD~1 HEAD -- tests | rg '^[-+][^-+]'`:
    ```
    -            # (History dates now both use UTC per spec 2vev8j 4.4 and are compared literally).
    +            # (History dates now both use UTC per spec 4sd62s 4.2b and are compared literally).
    -per spec 2vev8j 4.4) while normalizing:
    +per spec 4sd62s 4.2b) while normalizing:
    -    (Date clock differences are eliminated by unifying writers onto UTC per spec 2vev8j 4.4; dates are compared literally).
    +    (Date clock differences are eliminated by unifying writers onto UTC per spec 4sd62s 4.2b; dates are compared literally).
    -Spec 2vev8j Section 4.4 ("One timezone for every writer") requires:
    +Spec 4sd62s Section 4.2b ("One clock for each stored value") requires:
    -                # Check created history record date is UTC per 2vev8j 4.4
    +                # Check created history record date is UTC per 4sd62s 4.2b
    -                # Check created history record date is UTC per 2vev8j 4.4
    +                # Check created history record date is UTC per 4sd62s 4.2b
    -                # Check created history record date is UTC per 2vev8j 4.4
    +                # Check created history record date is UTC per 4sd62s 4.2b
    -Enforces spec 2vev8j Section 4.4 ("One timezone for every writer"):
    +Enforces spec 4sd62s Section 4.2b ("One clock for each stored value"):
    -                # Check created history record date is UTC per 2vev8j 4.4
    +                # Check created history record date is UTC per 4sd62s 4.2b
    -Spec 2vev8j Section 4.4 ("One timezone for every writer") requires:
    +Spec 4sd62s Section 4.2b ("One clock for each stored value") requires:
    -Spec 2vev8j Section 4.4 ("One timezone for every writer"):
    +Spec 4sd62s Section 4.2b ("One clock for each stored value"):
    -per spec 2vev8j 4.4) while normalizing the actor and passing an explicit --message
    +per spec 4sd62s 4.2b) while normalizing the actor and passing an explicit --message
    -    (Date skew fnb8pl is fixed by routing all writers to UTC per spec 2vev8j 4.4; dates are compared literally).
    +    (Date skew fnb8pl is fixed by routing all writers to UTC per spec 4sd62s 4.2b; dates are compared literally).
    -UTC clock per spec `2vev8j` Section 4.4, while leaving human-facing timestamp names
    +UTC clock per spec `4sd62s` Section 4.2b, while leaving human-facing timestamp names
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the summary lines of the named pytest run and of the bare `python3 -m pytest`; the post-change `aw releases show next` rows (`ms06pi` and `4sd62s` present, `2vev8j` absent); the `aw check release-gates` summary line (0 errors); a before/after diff of `(location, rule)` pairs from the two `aw check --agent` captures showing only the `2vev8j` advisory path move (or each other difference with its named cause); the `aw sanitize --agent` result record; and the `aw commit` output listing the committed paths.
  - Observed evidence:
    Named pytest run summary:
    ```
    ======================= 137 passed, 2 skipped in 13.61s ========================
    ```

    Bare core pytest run summary:
    ```
    1860 passed, 11 warnings in 33.21s
    ```

    Post-change `aw releases show next` rows:
    ```
    ms06pi  backlog  graduated     high      .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md
    ...
    4sd62s  specs    approved      -         .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md
    ```
    (`ms06pi` and `4sd62s` present, `2vev8j` absent).

    `aw check release-gates` summary line:
    ```
    ✓ CONFORMS  81 release-gates checked
    errors  0   warnings  0   info  0
    ```

    Before/after diff of `(location, rule)` pairs from `check-before.jsonl` vs `check-after.jsonl`:
    ```
    Removed (in before but not after):
      ('.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md', 'check.spec-criteria-uncovered')
    Added (in after but not before):
      ('.aw/records/specs/superseded/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md', 'check.spec-criteria-uncovered')
    Summary:
      before total diagnostics: 60
      after total diagnostics: 60
      before severity: {'error': 13, 'warning': 2, 'info': 45}
      after severity: {'error': 13, 'warning': 2, 'info': 45}
    ```

    `aw sanitize --agent` result record:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6254,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    `aw commit` output:
    ```
    aw commit: committed 20 path(s): 1aaa67d2664e9e63a3264e99c6f582fda92a68c1
    ```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). All open questions are resolved. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified in the finalize scope reconciliation (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Run every setter with `--no-commit`, then commit only through `aw commit 7ehv8l -- <paths>` (name both the old and new `2vev8j` paths; the setter stages the rename itself, and `aw commit` was measured at review to commit it); never `git add -A`, a bare `git add`, or `git commit -a`, and never push. Paste the ACTUAL command and test output into each `V-*`; never claim a result you did not run. Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 7ehv8l` itself.
