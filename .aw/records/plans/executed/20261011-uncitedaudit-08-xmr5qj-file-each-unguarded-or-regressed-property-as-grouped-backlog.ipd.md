# IPD: File each unguarded or regressed property as grouped backlog items

- Date: 2026-10-11
- Kind: child
- Concern: An audit that ends in a findings doc leaves its gaps invisible to `aw attention`, which reads backlog, plans and specs but not research prose (`AGENTS.md` "What needs attention": "Do NOT keep committed backlog only in prose"). Orders 05 to 07 produce `unguarded` properties, `regression` replay failures, and a `triaged-not-mutated` tail; each needs a tracked carrier or the audit retires the question without answering it, the exact failure plan `oyh28b` warned of ("a census that runs clean and files nothing ... would retire the question").
- Scope: IN: file one backlog item per ROOT-CAUSE GROUP (same production module plus same remedy shape: restore a behavioral test, or fix a regression) with `aw backlog new`, naming every property `P-NN` and deleted test it covers; file ONE rollup item enumerating every remaining outcome that needs a carrier (E-03 (d) defines the set) if non-empty; cap at 10 grouped items plus the rollup (remaining groups go into the rollup by name); justify each `- Work-Kind:` (`chore` for an absent test by default; `bug` with `- Blocks-Release: next` when Order 06 recorded `regression` with user-visible wrong behavior, per the repository's gating rule); record every filed id6 and a final reconciliation in the findings doc; dedupe against live items before filing. Also verify, as the Set's whole-Set checks, that every inventory file has a verdict and every non-`guarded` outcome has a carrier, and that the Set's own commits changed no code or test file outside the four tool files, their tests and `tools/README.md`. OUT: writing replacement tests or fixing regressions (each filed item's own work); changing backlog `e486tz`'s status.
- Scope-Paths: .aw/records/backlog/, .aw/records/research/
- Item-Dependencies: executed:rq3q7v
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 8
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xmr5qj

## Workflow history
- 2026-10-15 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: xmr5qj verified (set uncitedaudit, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Reviewed at HEAD 9f8eb0db7. Check (e) attributes by commit subject (range diff already caught 6 other-Set files); carrier-needed/free sets made explicit over upstream verdicts incl. stale-at-trim; dedupe by grep plus advisory detector (aw find is not text search); --priority added; aw check compared against a captured baseline; exact-file commit; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-08-xmr5qj-file-each-unguarded-or-regressed-property-as-grouped-backlog.review.md.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Turn every non-guarded audit outcome into a tracked, grouped backlog carrier and prove, by reconciliation, that no uncited file and no outcome was dropped.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Dedupe and file

- [x] E-01 First capture, outside the repo, the per-rule counts of `aw check --agent` (it exits 1 on 137 pre-existing findings at review HEAD `9f8eb0db7`) so E-04 compares against them. Group every `unguarded` property (Order 07) and every `regression` replay failure (Order 06 `## Replay failures`) by (production module, remedy shape). For each group, search live items for the module and the deleted test basenames with `grep -rlnwF -e <module stem> -e <deleted test basename> .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending`, and run the item's `aw backlog new ...` WITHOUT `--apply` to read its duplicate-candidate report. `aw find backlog <name>` is not a text search: its selector matches id6, status, Set and filename (at review `aw find backlog lost_guard_census` gave `no artifact matched`). OPEN any hit and record whether it actually covers the group (`owned-confirmed` / `owned-rejected`). Write a `## Filing plan` section listing each group, its dedupe judgement, its intended work-kind and priority with a one-sentence justification (a `bug` cites the user-perceptible effect and its measurement, per `AGENTS.md` "INEFFICIENCY A USER CAN NOTICE IS A DEFECT"), and whether it is filed or rolled up.
  - Depends on: none
  - Expected outcome: every unguarded and regression outcome appears in exactly one group with a dedupe judgement.
  - Execution state: performed

- [x] E-02 File each non-owned group, top 10 by (regressions first, then exclusive line count), with `aw backlog new --summary "<...>" --priority <low|medium|high> --work-kind <chore|bug> [--blocks-release next] --body "<properties P-NN, deleted tests, mutation verdicts, findings doc id6>" --apply` (`--priority` is required; `next` resolves to the single `planned` release, `f33nrj` 2.0.0 at review), pasting each output; then, if any group is beyond the cap or any outcome in E-03 (d)'s carrier-needed set is not covered by a grouped or `owned-confirmed` item, file ONE `chore` rollup item enumerating them by verdict, with `P-NN` or file path (for a long list, the counts per verdict plus the findings doc id6 and section name that lists them). Record each filed id6 and path in the findings doc's `## Filed items` section.
  - Depends on: E-01
  - Expected outcome: at most 10 grouped items plus at most one rollup, each with pasted creation output; every `bug` carries `- Blocks-Release: next`.
  - Execution state: performed

### Task group 2: Whole-Set reconciliation

- [x] E-03 Write a `## Reconciliation` section in the findings doc: (a) inventory file count equals the sum of `## Verdict totals` (Order 05); (b) the set of `pass-exclusive` keys in `## Candidates for Order 06` equals the set of keys in `## Derived properties`, and every `fail-investigate` file has a `## Replay failures` row (Order 06); (c) every `behavioral` property is in `## Mutation results` or `triaged-not-mutated` (Order 07); (d) every outcome in the CARRIER-NEEDED set names a carrier id6 from E-02 or an `owned-confirmed` live item. Carrier-free: `guarded`, `pin-retired`, `subject-retired`, `no-product-reach`, `intended-change`, `stale-at-trim`, and `recreated` with every deleted test name present at HEAD. Carrier-needed: everything else, i.e. `unguarded`, `regression`, `unprovable`, `import-only`, `property-unidentifiable`, `triaged-not-mutated` (including the `pass-shared` files Order 06 lists there), `replay-env-limited`, `api-moved`, and `recreated` with missing names; (e) the Set's own commits touched only the eight files Orders 01 to 04 declared (`tools/lost_guard_census.py`, `tests/test_lost_guard_census.py`, `tools/deleted_test_replay.py`, `tests/test_deleted_test_replay.py`, `tools/mutation_probe.py`, `tests/test_mutation_probe.py`, `tools/replay_coverage_diff.py`, `tests/test_replay_coverage_diff.py`) plus `tools/README.md`: `git log --name-only --format= -E --grep '^[a-z-]+(\(| )(k93w2g|1ub8ex|nzzu8n|g55j1e|sk2rbf|8d0qsg|anzu8q|rq3q7v|xmr5qj)\b' -- agent_workflows tests tools | sort -u`. Attribute by commit subject, NOT by a `<base>..HEAD` range diff: other Sets commit code concurrently on `main` (at review, `git diff --name-only 27ba5283c^..HEAD -- agent_workflows tests tools` already listed `agent_workflows/cli.py` from `work(pua92o)` and 4 other files, none of this Set's), so a range diff would fail on work unrelated to this Set. Also paste the command's subject list (`--format=%h %s` instead of `--format=`) so a reader can see which commits it attributed.
  - Depends on: E-02
  - Expected outcome: all five reconciliation checks pass with pasted numbers, or each failure is named with its fix applied in this pass.
  - Execution state: performed

- [x] E-04 Run `aw research index` (it regenerates the GITIGNORED index, `.aw/.gitignore:50-51`, which is not committed), `aw backlog check` and `aw check --agent`, then commit via `aw commit <this plan> -- <each new backlog item path> <findings doc path>`, naming EXACT files rather than the directories (a directory argument would include any co-worker's untracked backlog file), after confirming `git diff --cached --name-only` lists only those files.
  - Depends on: E-03
  - Expected outcome: `aw backlog check` exits 0; `aw check --agent` per-rule counts differ from E-01's capture only by diagnostics that name none of the new files (any that do are fixed in this pass); one path-scoped commit containing only the new items and the doc.
  - Execution state: performed


## Project conventions discovered (Step 0)

- Committed backlog lives in `records/backlog/`, created with `aw backlog new`, never in prose (`AGENTS.md` "What needs attention").
- Group by root cause, not one item per citation (`oyh28b` E-07: "DO NOT FILE 43 SEPARATE ITEMS. Group by ROOT CAUSE").
- Work-kind is a judgement recorded with evidence: an absent test is `chore` by default; user-perceptible wrong behavior is `bug` and must carry `- Blocks-Release:` while live (`AGENTS.md` "Every live bug gates the next release").
- Retired code pins are never filed for restoration (P16; `oyh28b` "TWO REFUSALS ARE ABSOLUTE").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Research prose is invisible to `aw attention`. | `AGENTS.md` "What needs attention": the view maps backlog, plans and specs; "Do NOT keep committed backlog only in prose". |
| F-02 | The predecessor audit capped filing at eight plus a rollup to keep the queue readable. | `oyh28b` E-07 "file at most EIGHT items in this pass ... and ONE further item that enumerates the remaining groups". |
| F-03 | Basename dedupe both over- and under-matches, so owned claims must be opened. | `oyh28b` F-20 and E-07 "OPEN the named item and confirm it actually covers this citation". |
| F-04 | A range diff from the Set's first commit includes other Sets' concurrent code commits. | Review at `9f8eb0db7`: `git diff --name-only 27ba5283c^..HEAD -- agent_workflows tests tools` listed 6 files (`agent_workflows/cli.py`, `ipd_lifecycle.py`, `runner_shared.py`, `status_set.py`, `tests/test_lifecycle_lane_nudge.py`, `tests/test_nv_backend_args_climb.py`), all from `work(pua92o)` and `work(m47znv)`. Work commits are subject-tagged `work(<id6>)`. |
| F-05 | `aw find backlog` selects by id6/status/Set/filename, not body text; `aw backlog new` requires `--priority` and has an advisory duplicate detector. | Review: `aw find backlog lost_guard_census` -> `no artifact matched`; `aw backlog new --summary x --work-kind chore` -> `--priority required`; the dry run prints `no duplicate candidates detected. ADVISORY ONLY`. |
| F-06 | `aw check` and `aw research index --check` already fail at review HEAD on pre-existing findings; the research index is gitignored. | `aw check --agent` at `9f8eb0db7`: `findings 137` (exit 1); `aw backlog check` exit 0; `.aw/.gitignore:50-51`; `8d0qsg` F-07. |
| F-07 | `next` resolves to exactly one planned release. | `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`: `- Status: planned`, `- Version: 2.0.0`. |

## Proposed changes (ordered, validatable)

1. Group and dedupe (E-01).
2. File grouped items and the rollup (E-02).
3. Whole-Set reconciliation (E-03).
4. Checks and commit (E-04).

## Deferred / out of scope (with reason)

- Writing replacement behavioral tests and fixing regressions: each filed item is its own unit of work and graduates separately.
  - Carrier-Declined: The obligation travels with the items E-02 files; a single carrier for all of them would duplicate those items.
- Closing backlog `e486tz`: the runner sets it `graduated` when this Set is authored; it closes `done` through the normal backlog close after the Set executes.
  - Carrier-Declined: Lifecycle step owned by the runner and `aw backlog set`, not by this plan.

## Scope check

- Over-scope: none.
- Under-scope: none known. Upstream verdicts added at review (`stale-at-trim` by `anzu8q`; `replay-env-limited`/`api-moved` by `8d0qsg`) are now classified in E-03 (d).

## Required tests / validation

- `aw backlog check` exits 0 after filing; `aw check --agent` adds no diagnostic naming a new file.
- Reconciliation checks (a) to (e) pass with pasted numbers.
- The commit contains only the new backlog items and the findings doc.

## Spec / documentation sync

N/A: backlog and research records only.

## Open questions

### OQ-01: Should a `regression` be filed `bug` automatically?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Per the repository's user-perceptible-impact test, `bug` requires that the changed behavior is visible to a user; E-01 records that judgement with its evidence per group. A regression in an internal helper with no user-visible effect is `chore`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `## Filing plan` table, with every `owned-*` judgement naming the item id6 opened and one sentence on what it covers; the pasted `grep` command and its output for each group; and a pasted count showing the number of grouped outcomes equals the number of `unguarded` rows in `## Mutation results` plus `regression` rows in `## Replay failures`.
  - Observed evidence:
    `## Filing plan` table from hpjj44:
    ```markdown
    | Group | Production Module | Production Key | Property ID | Exclusive Lines | Remedy Shape | Dedupe Judgement | Work-Kind | Priority | Justification | Action |
    |---|---|---|---|---:|---|---|---|---|---|---|
    | 1 | `agent_workflows/cli.py` | `agent_workflows/cli.py::_run_migrate_layout` | `PROP-01` | 277 | Restore behavioral test coverage | `non-owned` | `chore` | `low` | An absent test is chore by default since no user-perceptible wrong behavior or regression was observed; restoring behavioral test coverage is preventive maintenance. | `filed` |
    ```
    Ownership evaluations for search hits:
    - `6kczjg` (`.aw/records/backlog/done/20260923-6kczjg-01-6kczjg-decide-default-leftovers-disposition.backlog.md`): `owned-rejected` (decides interactive/non-interactive default leftover disposition for install; does not restore behavioral tests for `_run_migrate_layout`).
    - `719lyq` (`.aw/records/plans/pending/20261014-byz9pj-01-719lyq-repair-scenario-token-bindings-relocate-test-awphysical-tool.ipd.md`): `owned-rejected` (relocates `tools/awphysical/test_awphysical_tools.py` into `tests/` and rebinds scenario tokens; does not cover `agent_workflows/cli.py::_run_migrate_layout`).
    - Generic word matches on `cli` (`83ns86`, `7dcpe1`, `pirm70`, `whri6h`, `jmogmv`, `61lsze`, `ksmdcd`, `7i4zba`, `xvv7n4`, `swpf3q`, `fbdxmh`, `9380pe`, `3jg79f`): all `owned-rejected` (unrelated CLI leaves or flags, none touching layout migration or `_run_migrate_layout`).
    - Advisory duplicate detector check:
      `aw backlog new --summary "Restore behavioral test coverage for _run_migrate_layout" --priority low --work-kind chore`
      Output: `no duplicate candidates detected. ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.`
    Dedupe grep command:
    ```sh
    grep -rlnwF -e "cli" -e "test_awmigrename" -e "test_layout_migration" .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending
    ```
    Output:
    ```text
    .aw/records/backlog/graduated/20261011-indexmissdir-01-o6cbp7-index-write-missing-dir-traceback.backlog.md
    .aw/records/backlog/graduated/20261012-aws1tg-01-aws1tg-fields-flag-unhonored-on-agent-leaves.backlog.md
    .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md
    .aw/records/backlog/graduated/20261001-x31lcm-01-x31lcm-pwatch-sigterm-exits-zero.backlog.md
    .aw/records/backlog/graduated/20261012-idxjsonroot-01-aavf6a-index-check-json-absolute-repo-root.backlog.md
    .aw/records/backlog/graduated/20261011-indexallexit-01-hu2wka-index-all-record-exit-parity.backlog.md
    .aw/records/backlog/graduated/20261012-sbh1o1-01-g3ropl-source-anchors-agent-crash.backlog.md
    .aw/records/backlog/graduated/20260929-fcnz1r-01-fcnz1r-unify-backlog-set-dispatch-paths.backlog.md
    .aw/records/plans/pending/20261014-uypgvi-01-kmmoca-consume-the-release-readiness-report-in-release-review-secti.ipd.md
    .aw/records/plans/pending/20261014-mlm0b5-01-xocbpc-document-staged-rename-filtering-in-commit-backlog-transitio.ipd.md
    .aw/records/plans/pending/20261014-runledger-05-g5s94t-add-ledger-leaves-to-live-safe-leaves-once-aw-run-init-lands.ipd.md
    .aw/records/plans/pending/20261014-n2fx9i-01-e97wtz-restore-behavioral-coverage-of-the-run-cli-emit-error-machin.ipd.md
    .aw/records/plans/pending/20261014-t8icgt-01-of6kpx-refuse-renaming-or-regrouping-an-in-flight-plan-holding-a-be.ipd.md
    .aw/records/plans/pending/20261011-x31lcm-01-ww744p-make-aw-pwatch-return-143-on-sigterm-while-keeping-exit-0-on.ipd.md
    .aw/records/plans/pending/20261014-5tj8g4-01-i44j8w-stop-project-root-climb-at-temp-roots-so-stray-tmp-aw-or-tmp.ipd.md
    .aw/records/plans/pending/20261014-aws1tg-01-83ns86-honor-the-shared-fields-projection-under-agent-across-the-ni.ipd.md
    .aw/records/plans/pending/20261014-idxjsonroot-01-7dcpe1-remove-absolute-repo-root-from-aw-index-check-json-data-whil.ipd.md
    .aw/records/plans/pending/20261014-cleancfg-02-irjoga-route-clean-target-system-and-records-to-aw-home-and-leave-z.ipd.md
    .aw/records/plans/pending/20261014-s4pys7-01-1vwjdl-contain-incidental-agent-turn-writes-to-aw-home-while-preser.ipd.md
    .aw/records/plans/pending/20261014-jfdk7p-01-pirm70-honor-the-shared-json-flag-across-the-five-non-json-leaves-a.ipd.md
    .aw/records/plans/pending/20261014-sbh1o1-05-f0kolj-verify-and-close-the-source-anchors-agent-crash-fix-and-add.ipd.md
    .aw/records/plans/pending/20261014-promptidxword-01-whri6h-report-up-to-date-and-partial-update-outcomes-in-aw-index-pr.ipd.md
    .aw/records/plans/pending/20261014-jt7ns3-01-jmogmv-wire-corrupt-run-state-exit-4-in-driver-runs-and-align-spec.ipd.md
    .aw/records/plans/pending/20261012-wc5c5e-01-z28jah-classify-the-two-load-sensitive-suite-nodes-and-close-the-re.ipd.md
    .aw/records/plans/pending/20261014-nrcvpg-01-ybf6za-restore-behavioral-coverage-that-reviews-is-a-type-noun-with.ipd.md
    .aw/records/plans/pending/20261014-byz9pj-01-719lyq-repair-scenario-token-bindings-relocate-test-awphysical-tool.ipd.md
    .aw/records/plans/pending/20261014-cleancfg-03-on0keo-preserve-project-json-policy-keys-cutover-dates-and-local-js.ipd.md
    .aw/records/plans/pending/20261014-runledger-06-3a3hh9-classify-and-render-ledger-only-run-directories-in-aw-runs-v.ipd.md
    .aw/records/plans/pending/20261014-nj13xp-01-ivq0nr-pass-dir-in-test-finalize-sendback-e2e-scaffold-and-bound-fi.ipd.md
    .aw/records/plans/pending/20261014-rd6ei9-01-61lsze-adopt-the-shared-repo-relative-posix-renderer-across-the-rem.ipd.md
    .aw/records/plans/pending/20261014-4y614a-01-ksmdcd-honor-the-shared-fields-flag-in-parser-usage-refusals-under.ipd.md
    .aw/records/plans/pending/20261014-indexallexit-01-7i4zba-emit-one-aggregate-aw-agent-v1-record-for-aw-index-all-acros.ipd.md
    .aw/records/plans/pending/20261011-uncitedaudit-08-xmr5qj-file-each-unguarded-or-regressed-property-as-grouped-backlog.ipd.md
    .aw/records/plans/pending/20261014-mmpjti-01-xvv7n4-emit-aw-agent-v1-cannot-run-records-on-remaining-handler-usa.ipd.md
    .aw/records/plans/pending/20261014-c4q9e8-01-swpf3q-surface-discarded-agent-user-config-changes-per-run-in-aw-ru.ipd.md
    .aw/records/plans/pending/20261014-pex4pv-01-i2ty4u-filter-staged-rename-sources-in-commit-spec-transition-outpu.ipd.md
    .aw/records/plans/pending/20261014-indexmissdir-01-fbdxmh-refuse-aw-index-write-path-with-cannot-run-when-records-dire.ipd.md
    .aw/records/plans/pending/20261014-runledger-07-o34rb3-persist-workflow-beside-ledger-on-aw-run-init-and-verify-wor.ipd.md
    .aw/records/plans/pending/20261014-uu4rfe-01-9380pe-make-the-aw-runners-table-dashboard-return-143-on-sigterm-wh.ipd.md
    .aw/records/plans/pending/20261014-runledger-05-um0twl-write-requirement-set-on-aw-run-init-and-add-aw-run-verify-f.ipd.md
    .aw/records/plans/pending/20261014-3vz4wj-01-yfo6z6-restore-behavioral-coverage-of-aw-commit-routing-through-the.ipd.md
    .aw/records/plans/pending/20261014-selquiet-03-uhp38x-make-aw-show-refuse-a-zero-match-selector-with-exit-2-and-dr.ipd.md
    .aw/records/plans/pending/20261014-4d3ynu-01-3jg79f-aw-runs-non-empty-agent-stream-and-refusals-emit-aw-agent-v1.ipd.md
    .aw/records/plans/pending/20261012-runledger-03-v47z9u-add-aw-run-init-the-one-writer-of-a-conformant-ledger-header.ipd.md
    ```
    Count check: 1 grouped outcome = 1 unguarded row (`PROP-01`) + 0 regression rows.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `aw backlog new ... --apply` output for every filed item and the rollup; for one `bug` item, `grep -n 'Blocks-Release' <its path>` showing `- Blocks-Release: next` (or a statement that no group was filed `bug`); and the pasted `## Filed items` section.
  - Observed evidence:
    Group 1 (`5slmvq`):
    ```text
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/xmr5qj_attempt2/.aw/records/backlog/open/20261014-5slmvq-01-5slmvq-restore-behavioral-test-coverage-for-run-migrate-l.backlog.md
    ```
    Rollup item (`9qvfie`):
    ```text
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/xmr5qj_attempt2/.aw/records/backlog/open/20261014-9qvfie-01-9qvfie-rollup-of-uncited-trim-deleted-test-audit-carrier-.backlog.md
    ```
    *(Note: Slug normalized to drop trailing hyphen via `aw rename backlog 9qvfie --slug rollup-uncited-trim-audit-carrier-outcomes --apply`)*.
    Bug status: No group was filed as `bug`; both `5slmvq` and `9qvfie` were filed as `chore` (absent test / audit tail without user-perceptible regression). Neither carries `- Blocks-Release: next`.
    `## Filed items` section from hpjj44:
    ```markdown
    | Item Id | File Path | Scope | Work-Kind | Priority | Summary |
    |---|---|---|---|---|---|
    | `5slmvq` | `.aw/records/backlog/open/20261014-5slmvq-01-5slmvq-restore-behavioral-test-coverage-for-run-migrate-l.backlog.md` | Group 1 | `chore` | `low` | Restore behavioral test coverage for _run_migrate_layout |
    | `9qvfie` | `.aw/records/backlog/open/20261014-9qvfie-01-9qvfie-rollup-uncited-trim-audit-carrier-outcomes.backlog.md` | Rollup | `chore` | `low` | Rollup of uncited trim-deleted test audit carrier-needed outcomes |
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `## Reconciliation` section with the numbers for (a) to (d), including for (d) a per-verdict table of outcome count and carrier id6; and for (e) the pasted subject-attributed `git log` output (both the `%h %s` list and the sorted file list) whose file list is a subset of the nine declared files.
  - Observed evidence:
    `## Reconciliation` section from hpjj44:
    - (a) Inventory: 208 files holding 3573 removed funcs == Verdict totals: 208 files (4 recreated + 2 subject-retired + 0 api-moved + 1 replay-env-limited + 80 fail-investigate + 95 pass-exclusive + 17 pass-shared + 9 no-product-reach) holding 3573 removed funcs (PASS).
    - (b) 749 pass-exclusive candidate keys in Candidates for Order 06 == 749 keys in Derived properties (`cand_keys == dp_keys` is True). All 80 fail-investigate files have rows in Replay failures (203 nodeids) (PASS).
    - (c) 741 behavioral properties in Derived properties: 2 in Mutation results (`PROP-01`, `PROP-02`) + 739 in Triaged not mutated (38 budget-exhausted + 701 cost-cap). Missing: 0 (PASS).
    - (d) All 771 carrier-needed outcomes covered:
      | Outcome Verdict / Category | Outcomes Count | Carrier Id | Carrier File Path |
      |---|---:|---|---|
      | `unguarded` (`PROP-01`) | 1 | `5slmvq` | `.aw/records/backlog/open/20261014-5slmvq-01-5slmvq-restore-behavioral-test-coverage-for-run-migrate-l.backlog.md` |
      | `unprovable` (`PROP-02`) | 1 | `9qvfie` | `.aw/records/backlog/open/20261014-9qvfie-01-9qvfie-rollup-uncited-trim-audit-carrier-outcomes.backlog.md` |
      | `triaged-not-mutated` (keys) | 747 | `9qvfie` | `.aw/records/backlog/open/20261014-9qvfie-01-9qvfie-rollup-uncited-trim-audit-carrier-outcomes.backlog.md` |
      | `triaged-not-mutated` (`pass-shared` files) | 17 | `9qvfie` | `.aw/records/backlog/open/20261014-9qvfie-01-9qvfie-rollup-uncited-trim-audit-carrier-outcomes.backlog.md` |
      | `replay-env-limited` | 1 | `9qvfie` | `.aw/records/backlog/open/20261014-9qvfie-01-9qvfie-rollup-uncited-trim-audit-carrier-outcomes.backlog.md` |
      | `recreated` (missing test names) | 4 | `9qvfie` | `.aw/records/backlog/open/20261014-9qvfie-01-9qvfie-rollup-uncited-trim-audit-carrier-outcomes.backlog.md` |
      | **Total Carrier-Needed Outcomes** | **771** | | Every outcome named by a carrier (PASS) |
    - (e) Subject-attributed `git log` output:
      Command: `git log --name-only --format= -E --grep '^[a-z-]+(\(| )(k93w2g|1ub8ex|nzzu8n|g55j1e|sk2rbf|8d0qsg|anzu8q|rq3q7v|xmr5qj)\b' -- agent_workflows tests tools | sort -u`
      Output:
      ```text
      tests/test_replay_coverage_diff.py
      tools/README.md
      tools/replay_coverage_diff.py
      ```
      Subjects (`--format="%h %s"`):
      `07248f203 work(sk2rbf): Add a coverage differential that finds production lines only the replayed deleted tests reach`
      Broad word-boundary match capturing all 4 child tool commits:
      Command: `git log --name-only --format= -E --grep '\b(k93w2g|1ub8ex|nzzu8n|g55j1e|sk2rbf|8d0qsg|anzu8q|rq3q7v|xmr5qj)\b' -- agent_workflows tests tools | sort -u`
      Output:
      ```text
      tests/test_deleted_test_replay.py
      tests/test_lost_guard_census.py
      tests/test_mutation_probe.py
      tests/test_replay_coverage_diff.py
      tools/README.md
      tools/deleted_test_replay.py
      tools/lost_guard_census.py
      tools/mutation_probe.py
      tools/replay_coverage_diff.py
      ```
      Subjects:
      `013fd3a58 integrate(aw agy run): merge verified lane sk2rbf to main`
      `07248f203 work(sk2rbf): Add a coverage differential that finds production lines only the replayed deleted tests reach`
      `c24d211e8 integrate(aw agy run): merge verified lane nzzu8n to main`
      `71b3a94a4 Add deleted-test replay harness and tests (uncitedaudit nzzu8n)`
      `44dba9fc4 integrate(aw agy run): merge verified lane g55j1e to main`
      `7ce48464e uncitedaudit (Order 3, g55j1e): add worktree-isolated mutation probe`
      `3abc2ec97 integrate(aw agy run): merge verified lane 1ub8ex to main`
      `8be9fce0d chore(census): add uncited deleted file inventory (1ub8ex)`
      All 9 touched files are within declared instrument set; 0 production files modified (PASS).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `aw backlog check` output and exit code; pasted per-rule count comparison of `aw check --agent` against E-01's capture, with any new diagnostic shown; the pasted `git diff --cached --name-only` before commit; the `aw commit` output and `git show --stat HEAD` listing only the new backlog items and the findings doc.
  - Observed evidence:
    `aw backlog check`:
    ```text
    aw backlog check: all backlog items conform. 1026 backlog items checked.
    ```
    Exit code: 0
    `aw check --agent` per-rule count comparison:
    - Pre-execution baseline: 161 total findings (check.gate-ref-discharged: 3, check.graduated-to-dangling: 3, check.graduation-incomplete: 3, check.ipd-carrier-finished-unverified: 2, check.ipd-carrier-ungated: 2, check.ipd-lint-diagnostic: 3, check.ipd-uncarried-obligation: 25, check.lifecycle-transition-unvalidated: 70, check.plan-spec-link-missing: 4, check.scope-path-target-stale: 1, check.source-test-citation-dangling: 43, check.spec-criteria-uncovered: 1, check.system-layout-missing: 1).
    - Post-filing check: 160 total findings.
    - Diagnostics naming new files (`5slmvq`, `9qvfie`, `hpjj44`): `[]` (zero new diagnostics).
    `git diff --cached --name-only` before commit:
    ```text
    (empty)
    ```
    `aw commit` output:
    ```text
    aw commit: committed 3 path(s): ed8c89cc21a00d7e97b823f0315fa095ecfdb838
    ```
    `git show --stat HEAD`:
    ```text
    commit ed8c89cc21a00d7e97b823f0315fa095ecfdb838 (HEAD -> aw/lane/xmr5qj_attempt2)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Wed Oct 14 23:16:48 2026 -0400

        work(xmr5qj): File each unguarded or regressed property as grouped backlog items

        AW-Run: run-20261015T011924Z-3874138
        AW-Item: xmr5qj
        AW-Runner: aw agy run

     ...oral-test-coverage-for-run-migrate-l.backlog.md |  18 +++
     ...-uncited-trim-audit-carrier-outcomes.backlog.md |  26 +++
     ...daudit-01-hpjj44-uncited-trim-audit.findings.md | 176 +++++++++++++++++++++
     3 files changed, 220 insertions(+)
    ```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: no code or test edits; commit only the new backlog item files and the findings doc, named exactly, through `aw commit <plan> -- <paths>` (the research index is gitignored); never `git add -A`, never push. Do not change backlog `e486tz`'s status. Scope fence: `- Scope-Paths:` declares `.aw/records/backlog/` and `.aw/records/research/`; an edit outside them is justified at finalize, not avoided by stopping. Paste the ACTUAL output of every command whose numbers enter the doc or a V-item. Prerequisite: the findings doc carries `## Verdict totals`, `## Derived properties`, `## Replay failures` and `## Mutation results` (Orders 05 to 07); if any is absent, stop and report. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
