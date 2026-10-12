# IPD: File each unguarded or regressed property as grouped backlog items

- Date: 2026-10-11
- Kind: child
- Concern: An audit that ends in a findings doc leaves its gaps invisible to `aw attention`, which reads backlog, plans and specs but not research prose (`AGENTS.md` "What needs attention": "Do NOT keep committed backlog only in prose"). Orders 05 to 07 produce `unguarded` properties, `regression` replay failures, and a `triaged-not-mutated` tail; each needs a tracked carrier or the audit retires the question without answering it, the exact failure plan `oyh28b` warned of ("a census that runs clean and files nothing ... would retire the question").
- Scope: IN: file one backlog item per ROOT-CAUSE GROUP (same production module plus same remedy shape: restore a behavioral test, or fix a regression) with `aw backlog new`, naming every property `P-NN` and deleted test it covers; file ONE rollup item enumerating every remaining outcome that needs a carrier (E-03 (d) defines the set) if non-empty; cap at 10 grouped items plus the rollup (remaining groups go into the rollup by name); justify each `- Work-Kind:` (`chore` for an absent test by default; `bug` with `- Blocks-Release: next` when Order 06 recorded `regression` with user-visible wrong behavior, per the repository's gating rule); record every filed id6 and a final reconciliation in the findings doc; dedupe against live items before filing. Also verify, as the Set's whole-Set checks, that every inventory file has a verdict and every non-`guarded` outcome has a carrier, and that the Set's own commits changed no code or test file outside the four tool files, their tests and `tools/README.md`. OUT: writing replacement tests or fixing regressions (each filed item's own work); changing backlog `e486tz`'s status.
- Scope-Paths: .aw/records/backlog/, .aw/records/research/
- Item-Dependencies: executed:rq3q7v
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 8
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xmr5qj
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Reviewed at HEAD 9f8eb0db7. Check (e) attributes by commit subject (range diff already caught 6 other-Set files); carrier-needed/free sets made explicit over upstream verdicts incl. stale-at-trim; dedupe by grep plus advisory detector (aw find is not text search); --priority added; aw check compared against a captured baseline; exact-file commit; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-08-xmr5qj-file-each-unguarded-or-regressed-property-as-grouped-backlog.review.md.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Turn every non-guarded audit outcome into a tracked, grouped backlog carrier and prove, by reconciliation, that no uncited file and no outcome was dropped.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Dedupe and file

- [ ] E-01 First capture, outside the repo, the per-rule counts of `aw check --agent` (it exits 1 on 137 pre-existing findings at review HEAD `9f8eb0db7`) so E-04 compares against them. Group every `unguarded` property (Order 07) and every `regression` replay failure (Order 06 `## Replay failures`) by (production module, remedy shape). For each group, search live items for the module and the deleted test basenames with `grep -rlnwF -e <module stem> -e <deleted test basename> .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending`, and run the item's `aw backlog new ...` WITHOUT `--apply` to read its duplicate-candidate report. `aw find backlog <name>` is not a text search: its selector matches id6, status, Set and filename (at review `aw find backlog lost_guard_census` gave `no artifact matched`). OPEN any hit and record whether it actually covers the group (`owned-confirmed` / `owned-rejected`). Write a `## Filing plan` section listing each group, its dedupe judgement, its intended work-kind and priority with a one-sentence justification (a `bug` cites the user-perceptible effect and its measurement, per `AGENTS.md` "INEFFICIENCY A USER CAN NOTICE IS A DEFECT"), and whether it is filed or rolled up.
  - Depends on: none
  - Expected outcome: every unguarded and regression outcome appears in exactly one group with a dedupe judgement.
  - Execution state: pending

- [ ] E-02 File each non-owned group, top 10 by (regressions first, then exclusive line count), with `aw backlog new --summary "<...>" --priority <low|medium|high> --work-kind <chore|bug> [--blocks-release next] --body "<properties P-NN, deleted tests, mutation verdicts, findings doc id6>" --apply` (`--priority` is required; `next` resolves to the single `planned` release, `f33nrj` 2.0.0 at review), pasting each output; then, if any group is beyond the cap or any outcome in E-03 (d)'s carrier-needed set is not covered by a grouped or `owned-confirmed` item, file ONE `chore` rollup item enumerating them by verdict, with `P-NN` or file path (for a long list, the counts per verdict plus the findings doc id6 and section name that lists them). Record each filed id6 and path in the findings doc's `## Filed items` section.
  - Depends on: E-01
  - Expected outcome: at most 10 grouped items plus at most one rollup, each with pasted creation output; every `bug` carries `- Blocks-Release: next`.
  - Execution state: pending

### Task group 2: Whole-Set reconciliation

- [ ] E-03 Write a `## Reconciliation` section in the findings doc: (a) inventory file count equals the sum of `## Verdict totals` (Order 05); (b) the set of `pass-exclusive` keys in `## Candidates for Order 06` equals the set of keys in `## Derived properties`, and every `fail-investigate` file has a `## Replay failures` row (Order 06); (c) every `behavioral` property is in `## Mutation results` or `triaged-not-mutated` (Order 07); (d) every outcome in the CARRIER-NEEDED set names a carrier id6 from E-02 or an `owned-confirmed` live item. Carrier-free: `guarded`, `pin-retired`, `subject-retired`, `no-product-reach`, `intended-change`, `stale-at-trim`, and `recreated` with every deleted test name present at HEAD. Carrier-needed: everything else, i.e. `unguarded`, `regression`, `unprovable`, `import-only`, `property-unidentifiable`, `triaged-not-mutated` (including the `pass-shared` files Order 06 lists there), `replay-env-limited`, `api-moved`, and `recreated` with missing names; (e) the Set's own commits touched only the eight files Orders 01 to 04 declared (`tools/lost_guard_census.py`, `tests/test_lost_guard_census.py`, `tools/deleted_test_replay.py`, `tests/test_deleted_test_replay.py`, `tools/mutation_probe.py`, `tests/test_mutation_probe.py`, `tools/replay_coverage_diff.py`, `tests/test_replay_coverage_diff.py`) plus `tools/README.md`: `git log --name-only --format= -E --grep '^[a-z-]+(\(| )(k93w2g|1ub8ex|nzzu8n|g55j1e|sk2rbf|8d0qsg|anzu8q|rq3q7v|xmr5qj)\b' -- agent_workflows tests tools | sort -u`. Attribute by commit subject, NOT by a `<base>..HEAD` range diff: other Sets commit code concurrently on `main` (at review, `git diff --name-only 27ba5283c^..HEAD -- agent_workflows tests tools` already listed `agent_workflows/cli.py` from `work(pua92o)` and 4 other files, none of this Set's), so a range diff would fail on work unrelated to this Set. Also paste the command's subject list (`--format=%h %s` instead of `--format=`) so a reader can see which commits it attributed.
  - Depends on: E-02
  - Expected outcome: all five reconciliation checks pass with pasted numbers, or each failure is named with its fix applied in this pass.
  - Execution state: pending

- [ ] E-04 Run `aw research index` (it regenerates the GITIGNORED index, `.aw/.gitignore:50-51`, which is not committed), `aw backlog check` and `aw check --agent`, then commit via `aw commit <this plan> -- <each new backlog item path> <findings doc path>`, naming EXACT files rather than the directories (a directory argument would include any co-worker's untracked backlog file), after confirming `git diff --cached --name-only` lists only those files.
  - Depends on: E-03
  - Expected outcome: `aw backlog check` exits 0; `aw check --agent` per-rule counts differ from E-01's capture only by diagnostics that name none of the new files (any that do are fixed in this pass); one path-scoped commit containing only the new items and the doc.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: pasted `## Filing plan` table, with every `owned-*` judgement naming the item id6 opened and one sentence on what it covers; the pasted `grep` command and its output for each group; and a pasted count showing the number of grouped outcomes equals the number of `unguarded` rows in `## Mutation results` plus `regression` rows in `## Replay failures`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw backlog new ... --apply` output for every filed item and the rollup; for one `bug` item, `grep -n 'Blocks-Release' <its path>` showing `- Blocks-Release: next` (or a statement that no group was filed `bug`); and the pasted `## Filed items` section.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `## Reconciliation` section with the numbers for (a) to (d), including for (d) a per-verdict table of outcome count and carrier id6; and for (e) the pasted subject-attributed `git log` output (both the `%h %s` list and the sorted file list) whose file list is a subset of the nine declared files.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `aw backlog check` output and exit code; pasted per-rule count comparison of `aw check --agent` against E-01's capture, with any new diagnostic shown; the pasted `git diff --cached --name-only` before commit; the `aw commit` output and `git show --stat HEAD` listing only the new backlog items and the findings doc.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT: no code or test edits; commit only the new backlog item files and the findings doc, named exactly, through `aw commit <plan> -- <paths>` (the research index is gitignored); never `git add -A`, never push. Do not change backlog `e486tz`'s status. Scope fence: `- Scope-Paths:` declares `.aw/records/backlog/` and `.aw/records/research/`; an edit outside them is justified at finalize, not avoided by stopping. Paste the ACTUAL output of every command whose numbers enter the doc or a V-item. Prerequisite: the findings doc carries `## Verdict totals`, `## Derived properties`, `## Replay failures` and `## Mutation results` (Orders 05 to 07); if any is absent, stop and report. Under a runner, the runner finalizes; by hand, use `aw ipd finalize`.
