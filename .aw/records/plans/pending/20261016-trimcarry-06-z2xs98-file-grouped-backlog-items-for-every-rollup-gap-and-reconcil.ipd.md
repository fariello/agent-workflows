# IPD: File grouped backlog items for every rollup gap and reconcile the 770 outcomes

- Date: 2026-10-16
- Kind: child
- Concern: Orders 01 to 05 measure and settle the 770 carrier-needed outcomes rolled into backlog `9qvfie` (1 `unprovable` + 764 `triaged-not-mutated` + 1 `replay-env-limited` + 4 `recreated` files with missing names), but a measurement in a findings doc is invisible to `aw attention` (`AGENTS.md` "What needs attention": "Do NOT keep committed backlog only in prose"). Every outcome the Set leaves unguarded needs a tracked carrier, and the Set needs one place that proves no outcome was dropped.
- Scope: IN: group every remaining gap (`unguarded`, `unguarded-unreached`, `unprovable`, `budget-exhausted` keys; `exclusive-now` pass-shared files; `gap` and `regression` recreated names; any suspected regression Order 02 recorded) by (production module, remedy shape); dedupe each group against live items; file one backlog item per group with `aw backlog new` (cap 15 groups, the rest in ONE residual rollup item naming them); write `## Filing plan`, `## Filed items` and `## Reconciliation` in the Set's findings doc; run the whole-Set checks. OUT: writing replacement tests or fixing regressions (each filed item's own work); changing backlog `9qvfie`'s status (the runner sets `graduated`; closing it `done` follows from this Set executing).
- Scope-Paths: .aw/records/backlog/, .aw/records/research/*-trimcarry-01-*.findings.md
- Item-Dependencies: executed:24h56i, executed:x9z0ve, executed:8dyt88, executed:we3kkb, executed:rf1xxr
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 9qvfie
- Set: trimcarry
- Order: 6
- Highest E allocated: 04
- Author: opencode
- Id: z2xs98

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set trimcarry graduating backlog 9qvfie.

## Goal

Leave every one of the 770 rollup outcomes either closed by evidence in this Set or carried by a specific, live backlog item, and prove it with a reconciliation that sums to 770.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Group and dedupe

- [ ] E-01 Capture the per-rule counts of `aw check --agent` into the gitignored `.aw/state/trimcarry-z2xs98/check-before.jsonl` (E-04 compares against it). Collect the gaps from the Set doc: keys with final verdict `unguarded`, `unguarded-unreached`, `unprovable` or `budget-exhausted` (`## Rollup mutation results`); files `exclusive-now` (`## Pass-shared re-diff`); names `gap` or `regression` (`## Recreated missing names`); plus any suspected regression recorded in Order 02's (`x9z0ve`) V-02. Group by (production module stem, remedy shape: `restore behavioral coverage` or `fix regression`). For each group, search live work with `grep -rlnwF -e <module stem> -e <deleted test basename> .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending`, run the group's `aw backlog new ...` WITHOUT `--apply` to read its duplicate-candidate report, open every hit, and record `owned-confirmed` / `owned-rejected` (`aw find backlog` is not a text search: `xmr5qj` F-05). Write `## Filing plan`: one row per group with module, keys or names covered, counts, remedy shape, dedupe judgement, Work-Kind and Priority with a one-sentence justification, and `filed` / `owned` / `rolled-up`.
  - Depends on: none
  - Expected outcome: every gap is in exactly one group; every group has a dedupe judgement.
  - Execution state: pending

### Task group 2: File

- [ ] E-02 File each non-owned group, regressions first then by covered exclusive lines, up to 15, with `aw backlog new --summary "<...>" --set trimgap --priority <low|medium|high> --work-kind <chore|bug> [--blocks-release next] --body "<keys or test names covered, reach class and verdict, Set doc id6 and section, deleted test files to mine>" --apply`, pasting each output. Work-Kind: `chore` for an absent test (no user-visible wrong behavior observed, the `xmr5qj` precedent); `bug` with `--blocks-release next` for a `regression`, because a live bug must carry the gate (`AGENTS.md` "Every live bug gates the next release"; `next` resolves to the single `planned` release, `f33nrj` 2.0.0 at authoring). If more than 15 groups remain, file ONE residual `chore` item listing the remaining groups by module with counts and the Set doc section that enumerates them. Record each filed id6 and path in `## Filed items`.
  - Depends on: E-01
  - Expected outcome: one item per filed group (at most 15) plus at most one residual item; every `regression` item carries `- Blocks-Release: next`.
  - Execution state: pending

### Task group 3: Reconcile

- [ ] E-03 Write `## Reconciliation` with (a) the 770-outcome table: one row per backlog `9qvfie` outcome class with its count and where it ended: `PROP-02` (1) -> Order 01 (`24h56i`) verdict; `tests/test_run_evidence_completion.py` (1) -> restored by Order 02 (`x9z0ve`); 747 keys -> per-verdict counts from `## Rollup mutation totals`, each non-carrier-free count mapped to a filed id6, an `owned-confirmed` id6, or carrier-free (`pin-retired`, `key-gone`, `guarded`); 17 pass-shared files -> `shared-confirmed` (declined with the partition reason, flagged `Human review requested` in the row) or a filed id6; 4 recreated files -> per-class name counts from `## Recreated missing names`, each `gap`/`regression` count mapped to an id6. The table total MUST equal 770 (1 + 764 + 1 + 4). (b) A check that every id6 named resolves: `aw find backlog <id6>` for each. (c) The Set's own code and test footprint: `git log --name-only --format= -E --grep '(24h56i|x9z0ve|8dyt88|we3kkb|rf1xxr|z2xs98)' -- agent_workflows tests tools | sort -u` lists only `tests/test_benchmark_runners_reports.py` and `tests/test_run_evidence_completion.py`.
  - Depends on: E-02
  - Expected outcome: reconciliation total 770; every id6 resolves; footprint is exactly the two restored modules.
  - Execution state: pending

- [ ] E-04 Run `aw check --agent`, compare its per-rule counts with `check-before.jsonl`, and explain any NEW finding that names a file this plan wrote (fix it with the owning `aw backlog` or `aw research` verb). Run `aw research index`, then commit exactly the files this plan wrote: `aw commit <this plan> -- <each filed backlog path> <Set doc path>`.
  - Depends on: E-03
  - Expected outcome: no new `aw check` finding on this plan's files; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Committed backlog is created with `aw backlog new` (requires `--priority`; `--work-kind` or its alias `--kind`; `--set`, `--body`, `--blocks-release`), never hand-written; `--set trimgap` clusters the filed items (authoring dry run: would write `.aw/records/backlog/open/20261016-trimgap-01-<id6>-<slug>.backlog.md`).
- Grouping, dedupe method, the 10-plus-rollup cap pattern and the `chore` default for an absent test follow executed plan `xmr5qj` (E-01, E-02); the cap is 15 here because the population is larger (747 keys across about 100 modules at authoring).
- A live `bug` must carry `- Blocks-Release:`; the only `planned` release record is `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md`.
- The research index is gitignored, so only the doc and the backlog files are committed.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F1 | The rollup holds 770 outcomes: 1 + 764 + 1 + 4. | Backlog `9qvfie` body; `hpjj44` `## Reconciliation` (d) carrier table rows assigned to `9qvfie`. |
| F2 | The 747 keys span about 100 production modules; the largest are `run_analytics_telemetry.py` (47), `migration_complex.py` (40), `compat_migration.py` (36), `migration_inventory.py` (31), `run_analytics_taxonomy.py` (29). | Authoring count over `hpjj44` `## Triaged not mutated`. |
| F3 | The earlier filing found no regression and filed `chore`. | `hpjj44` `## Filed items`: "No group was filed as `bug` because `PROP-01` represents an absent behavioral test without observed regression". |

## Proposed changes (ordered, validatable)

1. Group and dedupe (E-01).
2. File groups and at most one residual item (E-02).
3. 770-outcome reconciliation and footprint check (E-03).
4. `aw check` comparison, index, commit (E-04).

## Deferred / out of scope (with reason)

- Writing replacement tests or fixing regressions: each filed item's own work.
  - Carrier-Declined: deliberate non-goal; each gap is carried by the item E-02 files for it.
- Setting backlog `9qvfie` to `done`: done follows from the Set's carriers executing, and the close-legitimacy rule applies at that time.
  - Carrier-Declined: outside this plan's authority per the production contract for `9qvfie`.

## Scope check

- Over-scope: none.
- Under-scope: none; E-03 accounts for all 770 outcomes.

## Required tests / validation

No tests are authored. Validity: the reconciliation totals 770 (V-03), every named id6 resolves (V-03), and `aw check` shows no new finding on this plan's files (V-04).

## Spec / documentation sync

N/A: backlog and research records only.

## Open questions

### OQ-01: Should a `shared-confirmed` pass-shared file be filed anyway?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. It reaches no line a surviving test does not reach, which is the partition `hpjj44` used; filing it would carry a gap that the measurement says is not there. The row is flagged for human review so the maintainer can overrule it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `## Filing plan` table; pasted output of a `python3 -c` check that every gap from the three source sections appears in exactly one group; for each group, the pasted grep hit list and the dry-run duplicate report line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of every `aw backlog new ... --apply`; pasted `## Filed items` table; for every `bug` item, pasted `grep -n 'Blocks-Release' <path>` showing `next`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `## Reconciliation` table with the total shown as 770; pasted `aw find backlog <id6>` output for every id6 named; pasted footprint command output listing only the two restored test modules.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted before/after per-rule counts of `aw check --agent` with any new finding explained; pasted `aw commit` output and `git show --stat HEAD` listing exactly the filed backlog files and the Set doc.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 to 05 are `executed`. Scope fence: `- Scope-Paths:` declares `.aw/records/backlog/` (new items only; do not edit existing items, including `9qvfie`) and the Set's findings doc; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command; never record a filing or a count you did not produce. Commit only the files this plan wrote through `aw commit <plan> -- <paths>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
