# IPD: File restore backlog items for every non-guarded probed key and reconcile the 319

- Date: 2026-10-17
- Kind: child
- Concern: Backlog `lrnh5f`'s remedy has two halves: probe the 319 budget-exhausted keys, then restore behavioral test coverage where the probe shows the surviving suite does not guard a key. Orders 01 to 04 produce the verdicts; which keys need restoring, and therefore what tests to write, is unknown until they run, so the restore work cannot be specified as test-writing steps today. Without a filing step the probe results would sit in a findings doc that `aw attention` does not surface, and the restore half of `lrnh5f` would be silently dropped.
- Scope: IN: group every key whose final verdict in `## Budget probe results` or `## Probe queue` is not carrier-free, dedupe against live backlog, file one `trimgap` backlog item per module group (top 15 by key count, the rest in one residual item), and write `## Filed items` and `## Reconciliation` accounting for all 319 keys. OUT: writing any test (each filed item's own work); editing any existing backlog item, including `lrnh5f`; any code or test edit.
- Scope-Paths: .aw/records/backlog/**/*-trimgap-*.backlog.md, .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: executed:g00ljy, executed:lictgf, executed:f4pbs5, executed:pr6lo9
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 5
- Highest E allocated: 03
- Author: opencode
- Id: b83dpg

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Each of the 319 keys ends either carrier-free on evidence (`guarded`, `key-gone`) or carried by a specific live backlog item that names the key, its verdict, and the deleted test file to mine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Gaps and dedupe

- [ ] E-01 FIRST, before any filing, capture the per-rule counts of `aw check --agent` (rule and severity of every diagnostic) into the gitignored `.aw/state/trimprobe-b83dpg/check-before.jsonl`, which E-03 (d) compares against (the `z2xs98` E-01 precedent). Then, from the Set doc, collect every key with final verdict `unguarded`, `unguarded-unreached`, `unprovable` or `budget-exhausted` (from `## Budget probe results`, and for the no-probe classes from `## Probe queue`); `guarded` and `key-gone` are CARRIER-FREE and are not grouped. Group the gaps by (module, remedy shape), as `z2xs98` did, so each group has exactly one Remedy Shape. For each group, DEDUPE by searching live backlog and pending plans for each key's qualified name (`rg -l -F '<module>::<qualname>' .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/plans/pending`), IGNORING hits in this Set's own artifacts (backlog `lrnh5f` and every `*-trimprobe-*` plan), which name keys as inputs or examples rather than owning them (at review, `g00ljy` names `comms.py::validate_ack` and `ipd_schema.py::_parse_item_dependency_edge` in its Findings, Findings F-04): a key named by any other live item is `owned-confirmed` with that item's id6 and is removed from the group. `aw backlog new`'s duplicate-candidate report in E-02 is a second, advisory check. Write `## Filing plan` (columns as `b1mx2w` `## Filing plan`: Group, Module, Keys covered, Counts, Remedy Shape, Dedupe Judgement, Work-Kind, Priority, Justification, Action), ranked by gap key count descending; top 15 `filed`, the rest `rolled-up`. Remedy shape: `restore behavioral coverage` for `unguarded`/`unguarded-unreached`, `investigate probe` for `unprovable`, `probe then restore` for `budget-exhausted`.
  - Depends on: none
  - Expected outcome: every gap key is in exactly one group or is `owned-confirmed`.
  - Execution state: pending

### Task group 2: Filing

- [ ] E-02 For each `filed` group, and once for the residual, run `aw backlog new --summary "<...>" --set trimgap --priority low --work-kind chore --body "<keys covered with verdict and operator; Set doc id6 and section; deleted test files to mine: the queue's control files plus hpjj44 ## Derived properties; source 19313eed^; carried from lrnh5f via plan b83dpg>" --apply`, pasting each output. Work-Kind is `chore` and no `--blocks-release` is set because an absent or unasserted test is not a user-visible wrong behavior (the `b1mx2w` `## Filed items` precedent and `lrnh5f` itself, which carries no gate). EXCEPTION: for every probe JSON with `baseline_failing` > 0 (the JSON records only the count, `tools.mutation_probe.ProbeResult`), re-run its `selection` unmutated at `git rev-parse HEAD` with `python3 -m pytest -o addopts= -q -p no:randomly <selection>` and paste the failing node ids (or `none`); a test that fails there is a live regression: file it as its own `--work-kind bug --blocks-release next` item (never rolled up), per `AGENTS.md` "Every live bug gates the next release". Write `## Filed items` listing each id6, path, group, Work-Kind, Priority and summary.
  - Depends on: E-01
  - Expected outcome: one item per filed group plus at most one residual; paths listed.
  - Execution state: pending

### Task group 3: Reconciliation and commit

- [ ] E-03 Write `## Reconciliation`: (a) a table mapping all 319 keys by final verdict to a filed id6, an `owned-confirmed` id6, or carrier-free, summing to 319; (b) a per-partition wall-time table (`P2`, `P3`, `P4` totals from the subtotal lines); (c) for each of `g00ljy`, `lictgf`, `f4pbs5`, `pr6lo9`: `git log --format='%h %p %s' --grep='(<id6>)' --grep='lane <id6> ' HEAD`, then for each listed commit `git diff --stat <hash>^1 <hash> -- agent_workflows tests` (the `^1` form, because `git show --stat` prints nothing for a merge commit, so the `integrate(...) merge verified lane` commits would pass vacuously), showing the Set's own commits changed no code or test file (a plain `git log <Order 01 commit>^..HEAD -- agent_workflows tests` range is NOT used: other Sets merge to main in the same window, and their code commits would falsely appear, Findings F-04); (d) `aw check --agent` per-rule counts now versus `check-before.jsonl`, explaining any NEW finding that names a file this plan wrote and fixing it with the owning `aw backlog` or `aw research` verb. Run `aw research index` (backlog has no index: `aw index backlog` prints `'index' is not supported for backlog`), then commit only the doc and the new backlog items with `aw commit <this plan> -- <doc path> <each new backlog path>`.
  - Depends on: E-02
  - Expected outcome: reconciliation sums to 319; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Backlog items are created only with `aw backlog new` (`AGENTS.md` "What needs attention"); `TODO.md` is not a work surface.
- Executed `z2xs98` (Set `trimcarry` Order 06) is the precedent for grouping, the 15-item cap with a residual, `chore`/`low` defaults and the regression-as-bug exception.
- Records are declared by glob in Scope-Paths (`.aw/records/plans/README.md` "Declaring records in Scope-Paths").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Filing plan` and `## Filed items` | The prior Set filed 15 per-module `trimgap` items plus residual `q86fxm`; `lrnh5f` itself is group 1. |
| F-02 | Authoring check: each of the 319 qualified key names searched in every other `trimgap` backlog item and pending `trimgap` plan | No other item or plan names any of the 319 keys today, so dedupe is expected to find little; it is still re-run at execution because items may be filed meanwhile. |
| F-03 | `rf1xxr` totals in `b1mx2w` `## Rollup mutation totals` | Of 37 keys probed there, 30 were `guarded`, 2 `unguarded`, 1 `unprovable`: most reached keys are expected to be carrier-free, so the filed set should be far smaller than 319. |
| F-04 | Review checks at HEAD `789e1ace5` | (1) The 319 qualified key names searched in `backlog/open`, `backlog/graduated` and `plans/pending` hit only `g00ljy` (2 keys, cited as calibration examples); `lrnh5f` and the other `trimprobe` plans name none. (2) `aw find backlog storage` -> `no artifact matched selector 'storage'`: `find` matches id6, status, Set or filename, not body text, so it is not a key-level dedupe. (3) `aw index backlog` -> `WARN 'index' is not supported for backlog.` (4) Main also carries other Sets' code commits (for example `work(c8bfp9)`) interleaved with this Set's merges, so a commit range cannot prove the Set changed no code. (5) `aw check --agent` has pre-existing findings (2 errors, 2 warnings, 103 info at review), so only a before/after delta is meaningful. (6) For the precedent merge `942486446` (`integrate(aw agy run): merge verified lane rf1xxr to main`), `git show --stat` printed nothing while `git diff --stat 942486446^1 942486446` printed `3 files changed, 1227 insertions(+), 134 deletions(-)`, so a merge must be diffed against its first parent. (7) `aw backlog new ... --set trimgap --priority low --work-kind chore` previews `.aw/records/backlog/open/<date>-trimgap-01-<id6>-<slug>.backlog.md`, matching the Scope-Paths glob. |

## Proposed changes (ordered, validatable)

1. E-01 collects, dedupes and groups gaps.
2. E-02 files items.
3. E-03 reconciles and commits.

## Deferred / out of scope (with reason)

- Writing the restored tests: each filed item's own graduation and plan, as for the 15 `b1mx2w` items; the target tests are unknowable before the probes run.
  - Carrier-Declined: no work is lost; every non-carrier-free key is named by a filed or owned item in E-03 (a).

## Scope check

- Over-scope: none. New backlog items under `trimgap` and the Set doc; no existing item edited.
- Under-scope: none. E-03 (a) accounts for all 319 keys.

## Required tests / validation

- Reconciliation sums to 319; every filed path exists; `aw backlog check` and `aw check` report no new error.

## Spec / documentation sync

N/A: records only; no `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore tests inside this Set, or file restore items?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: file items. A restore plan must name the keys, the deleted file to mine and the assertions that kill each mutant (sibling plans `syzi9i`, `33f8tn`), none of which exists until Orders 02 to 04 run. This matches how `z2xs98` carried `trimcarry`'s gaps.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the line count of `check-before.jsonl` and its timestamp showing it predates the first `aw backlog new --apply`; paste per-verdict gap counts, the dedupe search outputs with each `owned-confirmed` key and id6 (or `none`) and any ignored Set-own hits, and the `## Filing plan` table.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste every `aw backlog new` output; paste `ls` of each new path; paste `aw backlog check` output; paste the `baseline_failing` re-run output for every JSON with a non-zero count (or state that none had one).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the reconciliation table with its 319 total, the per-child commit hashes and their `git diff --stat <hash>^1 <hash> -- agent_workflows tests` output (empty for each), the before/after per-rule `aw check --agent` counts with any new finding explained, the `aw commit` output and `git show --stat HEAD` listing only the doc and the new backlog items.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 to 04 are `executed`. Scope fence: `- Scope-Paths:` declares new `trimgap` backlog items and this Set's findings doc (do not edit existing items, including `lrnh5f`); do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command; never record a filing or count you did not produce. Commit only the files this plan wrote through `aw commit <plan> -- <paths>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
