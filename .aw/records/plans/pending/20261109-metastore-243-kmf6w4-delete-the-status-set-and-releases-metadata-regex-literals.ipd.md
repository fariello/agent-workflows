# IPD: Delete the status_set and releases metadata regex literals

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 and 4.3 require deleting every `^-` metadata regex outside `artifact_meta`. `agent_workflows/status_set.py` has 10 and `agent_workflows/releases.py` has 6 (after `k6jd6l` moves the `releases` line writers). This is part 5 of the round-3 split of `e8420v` (Order 45), carrying `e8420v` E-20 minus its `tools/gate_drop_audit.py` retarget (moved to Order 239 for `_status_meta`; `backlog.parse_item` is owned by `k6jd6l` E-18).
- Scope: delete the 16 literals, each of their uses reading through `artifact_meta.read`, `read_text` or `read_at`; update `tests/test_status_set.py` and `tests/test_releases.py` only where a test names a deleted pattern. EXCLUDES every other module.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/releases.py, tests/test_status_set.py, tests/test_releases.py, .aw/records/plans/pending/20261109-metastore-243-kmf6w4-delete-the-status-set-and-releases-metadata-regex-literals.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:786w7r, executed:7uq6xg, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:k6jd6l, executed:t4gl15
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 243
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: kmf6w4
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved
- Scope-Exceeded: agent_workflows/attention.py (attention._resolve_release_version read the deleted releases._VERSION_RE inside try/except, so deleting it would have silently dropped the release version; retargeted onto releases.parse_release, backlog yb6z41 item 1)

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004.
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from e8420v (round 3, research nj8zdp guidance).

## Goal

After this plan, the `^-` literal search over `status_set` and `releases` prints nothing (or only `body prose` rows), and the setters and release records behave unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`e8420v` E-20 ("Delete `status_set._STATUS_RE` and its `finditer` loop and `releases._STATUS_RE`, and every other `^-` metadata regex literal in `status_set` and `releases`. Sites at the split: `status_set` (10) `_ID_RE`, `_STATUS_RE`, `_SET_RE`, `_GATE_KIND_RE`, `_GATE_REF_RE`, `_GATE_SUMMARY_RE`, the three inline searches in `_format_status_transition_line` and the `finditer` loop in `plan_priority_work_kind_problems`; `releases` (6) `_ID_RE`, `_STATUS_RE`, `_VERSION_RE`, `_SUMMARY_RE`, `_ITEM_FROM_BACKLOG_RE`, `_ITEM_GRADUATED_TO_RE` ... Update `tests/test_status_set.py` and `tests/test_releases.py` only where a test names a deleted pattern.") is split across E-01 to E-04 here. The search is `LIT` from `786w7r`.

PIN RULE (carried from `9o83cr`): before E-01, save the per-test outcome list of `tests/test_status_set.py` and `tests/test_releases.py` to `.aw/state/kmf6w4/before.txt` (ensure `.aw/state/kmf6w4/` exists via `mkdir -p .aw/state/kmf6w4/`); after E-03, the same into `after.txt`.

### Task group 1: two modules

- [x] E-01 Before the first edit, ensure `.aw/state/kmf6w4/` exists (`mkdir -p .aw/state/kmf6w4/`) and save baseline test PIN list to `.aw/state/kmf6w4/before.txt`. In `agent_workflows/status_set.py`, delete the named patterns `status_set._ID_RE`, `_STATUS_RE` (and its `finditer` loop in `status_set.plan_priority_work_kind_problems`), `_SET_RE`, `_GATE_KIND_RE`, `_GATE_REF_RE`, `_GATE_SUMMARY_RE`.
  - Depends on: none
  - Expected outcome: `rg -n "\b(_ID_RE|_STATUS_RE|_SET_RE|_GATE_KIND_RE|_GATE_REF_RE|_GATE_SUMMARY_RE)\b" agent_workflows/status_set.py` prints nothing.
  - Execution state: performed

- [x] E-02 In `status_set._format_status_transition_line`, delete the three inline `^-` searches.
  - Depends on: E-01
  - Expected outcome: the `LIT` search over `agent_workflows/status_set.py` prints nothing.
  - Execution state: performed

- [x] E-03 In `agent_workflows/releases.py`, delete `releases._ID_RE`, `_STATUS_RE`, `_VERSION_RE`, `_SUMMARY_RE`, `_ITEM_FROM_BACKLOG_RE`, `_ITEM_GRADUATED_TO_RE`.
  - Depends on: none
  - Expected outcome: the `LIT` search over `agent_workflows/releases.py` prints nothing.
  - Execution state: performed

- [x] E-04 Update `tests/test_status_set.py` and `tests/test_releases.py` only where a case names a deleted pattern, save `after.txt`, run both modules, and commit through `aw commit kmf6w4 -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-02, E-03
  - Expected outcome: both modules pass; the mapping accounts for every case.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Every typed setter goes through `status_set.run_set_command`; release records are read by `releases` and resolved for `Blocks-Release: next`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured at `ac76110f4` (`e8420v` F-26): `status_set` 10 literals with their internal uses, `releases` 6. `786w7r` F-26 re-derives them.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["E-01: Save Baseline PIN & Delete<br/>status_set Named Regex Patterns"] --> E02["E-02: Delete status_set Inline Searches"]
    E03["E-03: Delete releases Regex Patterns"] --> E04["E-04: Update Tests, Save PIN after.txt<br/>Run Gate & Commit"]
    E02 --> E04
```

1. `status_set` named patterns (E-01) and inline literals (E-02).
2. `releases` (E-03).
3. Tests and commit (E-04).

## Deferred / out of scope (with reason)

- `tools/gate_drop_audit.py` `_status_meta` retarget: Order 239.
  - Carrier: e8420v
- `tools/gate_drop_audit.py` `backlog.parse_item` retarget.
  - Carrier: k6jd6l
  - Carrier-Evidence: .aw/records/plans/executed/20261108-metastore-43-k6jd6l-fold-the-value-writers-into-artifact-meta-delete-the-writer.ipd.md

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 4 work Scope-Paths.

## Required tests / validation

`tests/test_status_set.py`, `tests/test_releases.py` (PIN lists), then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3.

## Open questions

### OQ-01: Are the `releases` line-writer patterns in scope?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No: "the `releases` line-writer patterns go with the writers in Order 43" (carried from `e8420v` E-20). Recommendation strength: strong.

## Execution notes (kmf6w4, 2026-11-24)

- E-01/E-02: `status_set` already carried none of the named patterns or inline literals at the starting HEAD `9497ecc4d`; `3c8da4e40` (r81uvz) moved its metadata reads onto `artifact_meta`, as `786w7r` F-26 recorded ("`status_set` is `already gone` for Order 243 E-01/E-02"). No `status_set.py` edit was needed; the declared path is acknowledged unmodified.
- E-03: the six `releases` patterns are gone. Id/Status/Version/Summary are read by the new `releases._read_release_fields` through `artifact_meta.read_text`; `parse_graduated_to` and `check_from_backlog` read `graduated_to`/`from_backlog` through `artifact_meta.read_text`.
- Out-of-scope edit: `attention._resolve_release_version` read `releases._VERSION_RE` inside `try/except Exception`; it now reads `releases.parse_release(...).version` (backlog `yb6z41` item 1). Recorded in `- Scope-Exceeded:`.
- E-04: no test in `tests/test_status_set.py` or `tests/test_releases.py` names a deleted pattern, so neither test file changed; both declared paths are acknowledged unmodified.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the E-01 `rg` command printing nothing, and the `git diff` hunk of `status_set.plan_priority_work_kind_problems`.
  - Observed evidence:
    $ rg -n "\b(_ID_RE|_STATUS_RE|_SET_RE|_GATE_KIND_RE|_GATE_REF_RE|_GATE_SUMMARY_RE)\b" agent_workflows/status_set.py; echo "e01 rc=$?"
    e01 rc=1
  No `git diff` hunk of `status_set.plan_priority_work_kind_problems` exists: `git diff 9497ecc4d -- agent_workflows/status_set.py` is empty because the patterns and the `finditer` loop were already removed by `3c8da4e40` (r81uvz) before this plan ran (`786w7r` F-26 note: "`status_set` is `already gone` for Order 243 E-01/E-02"). `git log -S"_GATE_SUMMARY_RE" -- agent_workflows/status_set.py` names `3c8da4e40` as the removing commit.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `LIT` search over `agent_workflows/status_set.py` printing nothing, and the `git diff` hunk of `status_set._format_status_transition_line`.
  - Observed evidence:
    $ LIT='re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?["'"'"'](\(\?m\))?\^-'
    $ rg -n "$LIT" agent_workflows/status_set.py; echo "status_set rc=$?"
    status_set rc=1
  No `git diff` hunk of `status_set._format_status_transition_line`: the three inline searches were already absent at `9497ecc4d` (same cause as V-01); the function is unchanged by this plan.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `LIT` search over `agent_workflows/releases.py` printing nothing, and `aw attention --format json` release-blocker section unchanged against `786w7r` F-30 (hash equal or the difference traced).
  - Observed evidence:
    $ rg -n "$LIT" agent_workflows/releases.py; echo "releases rc=$?"
    releases rc=1
    $ rg -n "releases\._(ID|STATUS|VERSION|SUMMARY|ITEM_FROM_BACKLOG|ITEM_GRADUATED_TO)_RE|\b_(ITEM_FROM_BACKLOG|ITEM_GRADUATED_TO)_RE\b" agent_workflows tools tests; echo "callers rc=$?"
    callers rc=1
    $ sha256sum .aw/state/kmf6w4/attention-*.json   # `python3 -m agent_workflows attention --format json`, before and after the edit
    0d81bc32f44f150737d2277b0fcec6a6b8709dff9b83cee9398a3a35d1b3999c  .aw/state/kmf6w4/attention-after.json
    0d81bc32f44f150737d2277b0fcec6a6b8709dff9b83cee9398a3a35d1b3999c  .aw/state/kmf6w4/attention-before.json
  The whole attention JSON (including every `blocks_release` value, 1574 items carry one) is byte-identical before and after, so the release-blocker section is unchanged. It differs from `786w7r` F-30 (`9f31b694...`) because F-30 was taken at `56e9d649f`; later runs changed records, and the before/after pair here is the like-for-like comparison on this tree. Behavior probe: `attention._resolve_release_version(root, 'next')` and `(root, 'f33nrj')` both return `2.0.0`; `releases.describe_planned_release` returns `('f33nrj', '2.0.0')`; `validate_release` on `- Status: Weird` still reports `release.status-invalid` with `'Weird'`. `aw check all --agent` rule multiset differs only by one `check.scope-drift` on this plan (the recorded `attention.py` scope exceedance).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/kmf6w4/before.txt .aw/state/kmf6w4/after.txt` with each change mapped, the summary line of `python3 -m pytest -o addopts="" tests/test_status_set.py tests/test_releases.py` passing, and `git show --stat` of the `aw commit kmf6w4` commit listing only Scope-Paths files.
  - Observed evidence:
    $ diff .aw/state/kmf6w4/before.txt .aw/state/kmf6w4/after.txt; echo diff rc=$?
    diff rc=0
  132 PASSED before and after; no test changed, so there is nothing to map.
    $ python3 -m pytest -o addopts="" tests/test_status_set.py tests/test_releases.py
    ============================= 132 passed in 32.03s =============================
    $ aw suite
    2894 passed, 1 skipped, 11 warnings in 137.79s (0:02:17)   (exit 0)
  Neighbouring modules: 348 passed (`test_attention`, `test_check_engine`, release-gate, From-Backlog and Graduated-To test files). `git show --stat` of the `aw commit kmf6w4` commit is recorded in the execution report (the commit is made after this evidence is written).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed (Order 239 first: it also edits `status_set`). Pin-first. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Safety stop: if prerequisite metastore symbols from `59aiyh`, `786w7r`, `7uq6xg`, `ffceq0`, `k6jd6l`, or `t4gl15` are absent upon starting, stop and report rather than creating conflicting implementations. Honesty rule: paste the ACTUAL summary lines. Commits: only through `aw commit kmf6w4 -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through finalize; when `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize kmf6w4` itself; never a hand `git mv` to `executed/`.
