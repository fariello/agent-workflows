# IPD: Delete parse_frontmatter and move the history grammar into artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader (`artifact_meta`). Part 11 of the round-3 split of `k6jd6l` (Order 43, research `nj8zdp` guidance). After Orders 288 and 289, `research_contract.parse_frontmatter` has no caller and is deleted here. This part also copies the three workflow-history grammars `artifact_meta`'s legacy loader borrows from `attention_contract` (`history_block` with its `HistoryBlock` result, `newest_history_record`, `last_history_at`) into `artifact_meta`, and gives text-only readers one public `artifact_meta` entry point, so Orders 291 and 292 can move the readers. Measured at `f83159217`: `artifact_meta.load_legacy_artifact` calls `_att.newest_history_record` once and `_att.last_history_at` twice.
- Scope: Part of `k6jd6l` E-10: delete `research_contract.parse_frontmatter`; copy the history grammar into `artifact_meta` with a public text entry point; retarget the loader and the migration. EXCLUDES the readers (Orders 291, 292), deleting the `attention_contract` originals (Order 292), and `attention_contract.HISTORY_RECORD_RE`, which Order 248 (`tdhav3`) deletes after `k6jd6l` (`artifact_meta` gets its own private copy of the record pattern).
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/artifact_meta.py, agent_workflows/migrations/m0001_convert.py, tests/test_artifact_meta_legacy.py, .aw/records/plans/pending/20261109-metastore-290-bxupy8-delete-parse-frontmatter-and-move-the-history-grammar-into-a.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:5lgpix, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 290
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: bxupy8
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved

> Written to .aw/system/workflows/technical-writing/technical-writing.md. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

## Workflow history
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006; review record .aw/records/reviews/20261109-metastore-290-bxupy8-delete-parse-frontmatter-and-move-the-history-grammar-into-a.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from k6jd6l (round 3, research nj8zdp guidance).

## Goal

`research_contract` defines no `parse_frontmatter`, and `artifact_meta` owns a private history grammar that its loader uses and that a text-only caller reaches through one public function.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Carried from `k6jd6l` E-10: "`attention_contract.history_block`, `last_history_at`, `newest_history_record` ... The migration (`dcerjg` E-09, `m0001_convert`) computes `last_history_day` with `newest_history_record`: it must call the moved private function inside `artifact_meta` (or a public `artifact_meta` wrapper), and `tests/test_m0001_conversion.py` and `tests/test_m0001_roundtrip.py` must pass unchanged." Ensure `.aw/state/9o83cr/` exists (`mkdir -p .aw/state/9o83cr/`). Save the before-list of `tests/test_artifact_meta_legacy.py` (and `tests/test_m0001_conversion.py` and `tests/test_m0001_roundtrip.py` if present) to `.aw/state/9o83cr/E-10d-before.txt`.

PIN RULE (carried from `9o83cr`): before an edit that deletes or retargets, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > <before-file>`); after it, run the same command into the matching after-file. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: one step per item

- [ ] E-01 Before the first edit, ensure `.aw/state/9o83cr/` exists (`mkdir -p .aw/state/9o83cr/`) and save the baseline test PIN list to `.aw/state/9o83cr/E-10d-before.txt`. Delete `research_contract.parse_frontmatter`.
  - Depends on: none
  - Expected outcome: no module defines or calls it.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/artifact_meta.py`, add private copies, unchanged in behavior, of `attention_contract.history_block` (with its `HistoryBlock` result type and a private copy of the record pattern), `attention_contract.newest_history_record` and `attention_contract.last_history_at`, and change `artifact_meta.load_legacy_artifact` to call them.
  - Depends on: E-01
  - Expected outcome: `artifact_meta` calls no `_att` history function.
  - Execution state: pending

- [ ] E-03 Add one public `artifact_meta` function for a caller that holds only TEXT and needs the history records (for example `artifact_meta.history_records(text) -> HistoryBlock`), documented as the single history grammar; a caller with an id6 uses `artifact_meta.history` or `read` instead.
  - Depends on: E-02
  - Expected outcome: the public function exists and returns the same block as the original for the same text.
  - Execution state: pending

- [ ] E-04 If `agent_workflows/migrations/m0001_convert.py` exists, change its `newest_history_record` call to the `artifact_meta` function; save the after-list; commit through `aw commit bxupy8 -- <paths>`.
  - Depends on: E-03
  - Expected outcome: the migration calls `artifact_meta`; the migration tests pass unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `attention_contract.HISTORY_RECORD_RE` is imported by `plan_readiness`, `record_history`, `ipd_lifecycle` and `review_sequence`; Order 248 (`tdhav3`) E-02 deletes it, so this family leaves it in place.
- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `history(id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`), and the legacy loader (`load_legacy_artifact`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `f83159217` with `rg -n "_att\." agent_workflows/artifact_meta.py`: the loader calls `newest_history_record` (1) and `last_history_at` (2). `agent_workflows/migrations/` did not exist at that commit; Order 18 (`ghhzb6`) creates `m0001_convert.py`.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["E-01: Delete research_contract.parse_frontmatter"] --> E02["E-02: Copy history grammar to artifact_meta"]
    E02 --> E03["E-03: Add public history_records entry point"]
    E03 --> E04["E-04: Retarget migration (if present) & commit"]
```

1. Delete `parse_frontmatter` (E-01).
2. Copy the history grammar (E-02).
3. Add the public text entry point (E-03).
4. Retarget the migration and commit (E-04).

## Deferred / out of scope (with reason)

- The history readers.
  - Carrier: ay6sxp
- `attention_contract.HISTORY_RECORD_RE`.
  - Carrier: tdhav3

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 4 work Scope-Paths.

## Required tests / validation

`tests/test_artifact_meta_legacy.py`, `tests/test_m0001_conversion.py`, `tests/test_m0001_roundtrip.py` (PIN lists).

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Open questions

### OQ-01: Does a public `history_records(text)` break the 'read through `read`, `history`, `read_text` or `read_at`' rule of `k6jd6l` E-10?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No: E-10 already allows a public `artifact_meta` wrapper for the migration, and several readers (`plan_readiness.newest_verdict`, `status_set.same_status_message_is_duplicate`) hold staged text with no id6, so they need a text entry point; it keeps the one grammar inside `artifact_meta`. Recommendation strength: medium. RESOLVED 2026-11-11 by the user via /askme: public now, private later (the function is public in artifact_meta so every caller uses the one copy; the cutover may make it private once no outside caller remains). No reason was given.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "parse_frontmatter\b" agent_workflows tools tests` listing only the private `artifact_meta` copy from Order 288 (and comments, each quoted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "_att\.(history_block|newest_history_record|last_history_at)" agent_workflows/artifact_meta.py` printing nothing and `rg -n "def _(history_block|newest_history_record|last_history_at)\b" agent_workflows/artifact_meta.py` with three hits.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new test in `tests/test_artifact_meta_legacy.py` that compares `artifact_meta.history_records(text)` with `attention_contract.history_block(text)` on the fixture texts, and its PASSED line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n "newest_history_record|attention_contract" agent_workflows/migrations/m0001_convert.py` (no `attention_contract` hit, or 'file absent' with `ls agent_workflows/migrations/`), `diff .aw/state/9o83cr/E-10d-before.txt .aw/state/9o83cr/E-10d-after.txt` with no FAILED or ERROR line, and `git show --stat` of the `aw commit bxupy8` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first where an item deletes or retargets. Stop safely if prerequisite metastore symbols from `59aiyh`, `5lgpix`, `ffceq0`, or `t4gl15` are absent.

Safety rule: uncommitted changes and untracked files you did not create are not yours; never revert, stage, commit, discard, reformat, or "clean up" another party's work.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: paste the ACTUAL output; never claim a result you did not run.

Commits: only through `aw commit bxupy8 -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize bxupy8` (never a hand git mv), after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When aw oc run or aw agy run executes the plan, the runner performs the finalize; a hand executor runs aw ipd finalize bxupy8 itself.
