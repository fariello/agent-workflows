# IPD: Delete the runner_shared metadata parsers and regex literals

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 and 4.3 require deleting every metadata parser and `^-` metadata regex outside `artifact_meta`. `agent_workflows/runner_shared.py` has `runner_shared._front_matter_bullets` (re-exported by `oc_runipd` and `agy_runipd`) and 16 `^-` literals, one of which rewrites a plan's `- Status:` line (a WRITE). This is part 4 of the round-3 split of `e8420v` (Order 45), carrying `e8420v` E-19 verbatim.
- Scope: delete `_front_matter_bullets` and its two re-exports, the named and inline `^-` literals, and route the `run_review_sequence` status rewrite through `artifact_meta.append`; update `tests/test_runner_shared.py`. EXCLUDES the two `record_oq_answer` literals (open-question rows, body prose, N3).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, .aw/records/plans/pending/20261109-metastore-242-k6nukd-delete-the-runner-shared-metadata-parsers-and-regex-literals.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:786w7r, executed:7uq6xg, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:k6jd6l, executed:t4gl15
- Status: reviewed
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 242
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: k6nukd

> Written to .aw/system/workflows/technical-writing/technical-writing.md. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

## Workflow history

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED; review record .aw/records/reviews/20261109-metastore-242-k6nukd-delete-the-runner-shared-metadata-parsers-and-regex-literals.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from e8420v (round 3, research nj8zdp guidance).

## Goal

After this plan, `rg -n "_front_matter_bullets" agent_workflows tests` prints nothing, the `^-` literal search over `runner_shared` prints only the two `record_oq_answer` rows, and `tests/test_runner_shared.py` passes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`e8420v` E-19 ("Delete `runner_shared._front_matter_bullets` and its re-exports in `oc_runipd`/`agy_runipd`, and every `^-` metadata regex literal in `runner_shared`. Sites at the split (16 literals): the named `_SET_RE`, `_ORDER_RE`, `_KIND_RE`, `_HISTORY_BULLET_RE` (defined twice), `_FRONT_MATTER_BULLET_RE`; inline literals in `declared_spec_paths`, `enforce_no_active_runner_conflict`, `run_review_sequence` (the `- Status:` rewrite to `to-review`, a WRITE that must go through `artifact_meta.append`), `reconcile_disposition`, `execute_item_core`, `perform_coordinator_proposal_file` (three). ... Update `tests/test_runner_shared.py`.") is split across E-01 to E-05 here. The search is `LIT` from `786w7r`.

PIN RULE (carried from `9o83cr`): before E-01, ensure directory `.aw/state/k6nukd/` exists (`mkdir -p .aw/state/k6nukd/`) and save `tests/test_runner_shared.py`'s per-test outcome list to `.aw/state/k6nukd/before.txt` (command as in `9o83cr`); after E-04, the same into `after.txt`. A retargeted test keeps every input case.

### Task group 1: runner parsers and literals

- [ ] E-01 Capture the baseline PIN list (`mkdir -p .aw/state/k6nukd/` and save `.aw/state/k6nukd/before.txt`); then delete `runner_shared._front_matter_bullets` and its four call sites (in the three-way front-matter merge and the bullet-key lookup), reading each key through `artifact_meta.read_text`; delete its re-exports in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: none
  - Expected outcome: `rg -n "_front_matter_bullets" agent_workflows` prints nothing.
  - Execution state: pending

- [ ] E-02 Delete the named patterns `runner_shared._SET_RE`, `_ORDER_RE`, `_KIND_RE`, both `_HISTORY_BULLET_RE` definitions and `_FRONT_MATTER_BULLET_RE`, each use reading through `artifact_meta.read_text` or `history`.
  - Depends on: E-01
  - Expected outcome: `rg -n "\b(_SET_RE|_ORDER_RE|_KIND_RE|_HISTORY_BULLET_RE|_FRONT_MATTER_BULLET_RE)\b" agent_workflows/runner_shared.py` prints nothing.
  - Execution state: pending

- [ ] E-03 In `runner_shared.run_review_sequence`, replace the `re.sub` that rewrites `- Status:` to `to-review` with an `artifact_meta.append` `set` event of `status`.
  - Depends on: E-02
  - Expected outcome: `run_review_sequence` contains no `^-` literal.
  - Execution state: pending

- [ ] E-04 Delete the inline literals in `runner_shared.declared_spec_paths`, `enforce_no_active_runner_conflict`, `reconcile_disposition`, `execute_item_core` and the three in `perform_coordinator_proposal_file`.
  - Depends on: E-03
  - Expected outcome: the `LIT` search over `agent_workflows/runner_shared.py` prints only the two `record_oq_answer` rows.
  - Execution state: pending

- [ ] E-05 Update `tests/test_runner_shared.py` where a case names a deleted symbol (keeping `CrossHostReadIdReExportTests` unchanged), save `after.txt`, run the module, and commit through `aw commit k6nukd -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-04
  - Expected outcome: the module passes; the mapping accounts for every case.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.run_review_sequence` rewrites a plan's `- Status:` line with `re.sub`; that is a WRITE and moves to `artifact_meta.append` (a `set` event of `status`), not to a reader (carried from `e8420v`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`: `rg -n "_front_matter_bullets" agent_workflows` prints the definition and 4 calls in `runner_shared.py`. At `ac76110f4` (`e8420v`): 16 literals, 14 delete sites, 2 `body prose`.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["1. Delete _front_matter_bullets & re-exports (E-01)<br/>Capture PIN baseline, remove parser and re-exports"]
    E02["2. Delete named regex patterns (E-02)<br/>Remove _SET_RE, _ORDER_RE, _KIND_RE, _HISTORY_BULLET_RE, _FRONT_MATTER_BULLET_RE"]
    E03["3. Retarget status rewrite (E-03)<br/>Replace re.sub with artifact_meta.append set event"]
    E04["4. Delete inline literals (E-04)<br/>Remove inline ^- literals across runner functions"]
    E05["5. Update tests & commit (E-05)<br/>Verify PIN after-list, run test_runner_shared, aw commit"]

    E01 --> E02
    E02 --> E03
    E03 --> E04
    E04 --> E05
```

1. Delete the parser and re-exports (E-01): Capture baseline PIN test outcomes to `.aw/state/k6nukd/before.txt`, delete `runner_shared._front_matter_bullets` and its four call sites, reading keys via `artifact_meta.read_text`, and delete its re-exports in `oc_runipd.py` and `agy_runipd.py`.
2. Delete named regex patterns (E-02): Remove `_SET_RE`, `_ORDER_RE`, `_KIND_RE`, both `_HISTORY_BULLET_RE` definitions, and `_FRONT_MATTER_BULLET_RE`, retargeting their call sites to `artifact_meta.read_text` or `history`.
3. Retarget status rewrite (E-03): In `runner_shared.run_review_sequence`, replace the `re.sub` regex rewrite of `- Status:` with an `artifact_meta.append` `set` event for `status`.
4. Delete inline literals (E-04): Remove inline `^-` metadata regex literals in `declared_spec_paths`, `enforce_no_active_runner_conflict`, `reconcile_disposition`, `execute_item_core`, and `perform_coordinator_proposal_file`, keeping only body prose rows in `record_oq_answer`.
5. Update tests and commit (E-05): Update `tests/test_runner_shared.py` to account for deleted symbols, verify after-list PIN outcomes against before-list, run pytest, and commit via `aw commit k6nukd`.

## Deferred / out of scope (with reason)

- `status_set` and `releases`: Order 243.
  - Carrier: e8420v

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 4 work Scope-Paths.

## Required tests / validation

`tests/test_runner_shared.py` (PIN lists), then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3.

## Open questions

### OQ-01: Do the `oc_runipd`/`agy_runipd` `_read_id` re-exports change here?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `_read_id` is rebound by `k6jd6l` E-11; this plan removes only the `_front_matter_bullets` re-exports. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "_front_matter_bullets" agent_workflows` printing nothing, and the `git diff` hunks of `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the E-02 `rg` command printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` hunk of `runner_shared.run_review_sequence` showing the `artifact_meta.append` call replacing the `re.sub`, and `python3 -m pytest -o addopts="" -v tests/test_runner_shared.py -k review_sequence` with every case PASSED. Code path: `runner_shared.run_review_sequence` (E-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `LIT` search over `agent_workflows/runner_shared.py` showing only the two `record_oq_answer` rows.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `diff .aw/state/k6nukd/before.txt .aw/state/k6nukd/after.txt` with each removed name mapped, `python3 -m pytest -o addopts="" -v tests/test_runner_shared.py -k CrossHostReadIdReExport` PASSED, and `git show --stat` of the `aw commit k6nukd` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed (Order 239 first: it also edits `runner_shared`). Safety stop: if prerequisite metastore reader symbols from `1ajqaa`, `59aiyh`, `786w7r`, `7uq6xg`, `dcerjg`, `ffceq0`, `g5hpbb`, `k6jd6l`, or `t4gl15` are absent, stop and report rather than proceeding. Shared-checkout safety: this plan edits only its Scope-Paths; do not stage, edit, or commit any other file.

Pin-first. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit k6nukd -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize k6nukd` itself.
