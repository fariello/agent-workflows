# IPD: File restore backlog items for every non-guarded probed key and reconcile the 319

- Date: 2026-10-17
- Kind: child
- Concern: Backlog `lrnh5f`'s remedy has two halves: probe the 319 budget-exhausted keys, then restore behavioral test coverage where the probe shows the surviving suite does not guard a key. Orders 01 to 04 produce the verdicts; which keys need restoring, and therefore what tests to write, is unknown until they run, so the restore work cannot be specified as test-writing steps today. Without a filing step the probe results would sit in a findings doc that `aw attention` does not surface, and the restore half of `lrnh5f` would be silently dropped.
- Scope: IN: group every key whose final verdict in `## Budget probe results` or `## Probe queue` is not carrier-free, dedupe against live backlog, file one `trimgap` backlog item per module group (top 15 by key count, the rest in one residual item), and write `## Filed items` and `## Reconciliation` accounting for all 319 keys. OUT: writing any test (each filed item's own work); editing any existing backlog item, including `lrnh5f`; any code or test edit.
- Scope-Paths: .aw/records/backlog/**/*-trimgap-*.backlog.md, .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: executed:g00ljy, executed:lictgf, executed:f4pbs5, executed:pr6lo9
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 5
- Highest E allocated: 03
- Author: opencode
- Id: b83dpg

## Workflow history

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Each of the 319 keys ends either carrier-free on evidence (`guarded`, `key-gone`) or carried by a specific live backlog item that names the key, its verdict, and the deleted test file to mine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Gaps and dedupe

- [ ] E-01 From the Set doc, collect every key with final verdict `unguarded`, `unguarded-unreached`, `unprovable` or `budget-exhausted` (from `## Budget probe results`, and for the no-probe classes from `## Probe queue`); `guarded` and `key-gone` are CARRIER-FREE and are not grouped. Group the gaps by module. For each group, DEDUPE by searching live backlog and pending plans for each key's qualified name (`rg -l -F '<module>::<qualname>' .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/plans/pending`, and `aw find backlog <module stem>`): a key already named by a live item is `owned-confirmed` with that item's id6 and is removed from the group. Write `## Filing plan` (columns as `b1mx2w` `## Filing plan`: Group, Module, Keys covered, Counts, Remedy Shape, Dedupe Judgement, Work-Kind, Priority, Justification, Action), ranked by gap key count descending; top 15 `filed`, the rest `rolled-up`. Remedy shape: `restore behavioral coverage` for `unguarded`/`unguarded-unreached`, `investigate probe` for `unprovable`, `probe then restore` for `budget-exhausted`.
  - Depends on: none
  - Expected outcome: every gap key is in exactly one group or is `owned-confirmed`.
  - Execution state: pending

### Task group 2: Filing

- [ ] E-02 For each `filed` group, and once for the residual, run `aw backlog new --summary "<...>" --set trimgap --priority low --work-kind chore --body "<keys covered with verdict and operator; Set doc id6 and section; deleted test files to mine: the queue's control files plus hpjj44 ## Derived properties; source 19313eed^; carried from lrnh5f via plan b83dpg>" --apply`, pasting each output. Work-Kind is `chore` and no `--blocks-release` is set because an absent or unasserted test is not a user-visible wrong behavior (the `b1mx2w` `## Filed items` precedent and `lrnh5f` itself, which carries no gate). EXCEPTION: if any probe JSON shows the survivor's BASELINE run failing (`baseline_failing` > 0) on a test that also fails at `git rev-parse HEAD` in the bare suite, that is a live regression: file it as its own `--work-kind bug --blocks-release next` item (never rolled up), per `AGENTS.md` "Every live bug gates the next release". Write `## Filed items` listing each id6, path, group, Work-Kind, Priority and summary.
  - Depends on: E-01
  - Expected outcome: one item per filed group plus at most one residual; paths listed.
  - Execution state: pending

### Task group 3: Reconciliation and commit

- [ ] E-03 Write `## Reconciliation`: (a) a table mapping all 319 keys by final verdict to a filed id6, an `owned-confirmed` id6, or carrier-free, summing to 319; (b) a per-partition wall-time table (`P2`, `P3`, `P4` totals from the subtotal lines); (c) `git log --stat <Order 01 commit>^..HEAD -- agent_workflows tests` showing the Set changed no code or test file; (d) `aw check --agent` rule counts before E-02 and after, showing no new error. Run `aw research index` and `aw index backlog`, then commit only the doc and the new backlog items with `aw commit <this plan> -- <doc path> <each new backlog path>`.
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
  - Required evidence: paste per-verdict gap counts, the dedupe search outputs with each `owned-confirmed` key and id6 (or `none`), and the `## Filing plan` table.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste every `aw backlog new` output; paste `ls` of each new path; paste `aw backlog check` output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the reconciliation table with its 319 total, the `git log --stat` output, the before/after `aw check --agent` counts, the `aw commit` output and `git show --stat HEAD` listing only the doc and the new backlog items.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 to 04 are `executed`. Scope fence: `- Scope-Paths:` declares new `trimgap` backlog items and this Set's findings doc (do not edit existing items, including `lrnh5f`); do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command; never record a filing or count you did not produce. Commit only the files this plan wrote through `aw commit <plan> -- <paths>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
