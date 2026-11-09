# IPD: Delete the specs record text readers

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader (`artifact_meta`). Part 18 of the round-3 split of `k6jd6l` (Order 43, research `nj8zdp` guidance): delete the seven `specs` line readers `specs._read_status`, `_read_gate`, `_read_blocks_release`, `_read_priority`, `_read_work_kind`, `_read_scope` and `_read_summary`. Measured at `f83159217`: 13 internal calls in `specs` (mostly `specs.validate_spec`), `attention._spec_record` (4), `check_engine.check_decision_ref_dangling` and `check_engine._iter_live_gate_carriers` (3), `tests/test_specs_status_dirs.py` (1).
- Scope: The `specs` part of `k6jd6l` E-18 (subset 2). `check_engine._read_blocks_release` (a different function, used by `runner_shared` and `tools/gate_drop_audit.py`) is owned by Order 45 (`e8420v`), as `k6jd6l` E-18 already said. EXCLUDES `backlog.parse_item` (Orders 298, 299) and `attention`'s inline literals (Order 248).
- Scope-Paths: agent_workflows/specs.py, agent_workflows/attention.py, agent_workflows/check_engine.py, tests/test_specs_status_dirs.py, .aw/records/plans/pending/20261109-metastore-297-um2kvx-delete-the-specs-record-text-readers.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:hrbbhy, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 297
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: um2kvx

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from k6jd6l (round 3, research nj8zdp guidance).

## Goal

`specs` defines none of the seven readers, and `aw check all --all --agent`'s rule multiset matches the Order 280 baseline.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Carried from `k6jd6l` E-18: "Delete `specs._read_status`, `_read_gate`, `_read_blocks_release`, `_read_priority`, `_read_work_kind`, `_read_scope` and `_read_summary` ...; their remaining callers use `artifact_meta.read`, `read_text` or `read_at`." Save the before-list of `tests/test_specs_status_dirs.py`, `tests/test_attention.py` and `tests/test_check_engine.py` to `.aw/state/9o83cr/E-18a-before.txt`.

PIN RULE (carried from `9o83cr`): before an edit that deletes or retargets, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > <before-file>`); after it, run the same command into the matching after-file. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: callers first, then delete

- [ ] E-01 In `specs.validate_spec` and the other internal callers, read status, gate, Blocks-Release, Priority, Work-Kind, Scope and Summary from one `artifact_meta.read_text(text, record_type="specs")` call; keep `specs._find_status_index` only for the WRITE path that needs a line index.
  - Depends on: none
  - Expected outcome: no internal call to a `specs._read_*` reader remains.
  - Execution state: pending

- [ ] E-02 In `attention._spec_record`, replace the four `specs_mod._read_*` calls with `artifact_meta.read_text` fields.
  - Depends on: E-01
  - Expected outcome: `attention` calls no `specs_mod._read_*`.
  - Execution state: pending

- [ ] E-03 In `check_engine.check_decision_ref_dangling` and `check_engine._iter_live_gate_carriers`, replace the three `_specs._read_gate`/`_specs._read_status` calls with `artifact_meta.read_text` fields.
  - Depends on: E-02
  - Expected outcome: `check_engine` calls no `_specs._read_*`.
  - Execution state: pending

- [ ] E-04 Delete the seven `specs._read_*` readers; retarget `tests/test_specs_status_dirs.py`; save the after-list; compare `aw check all --all --agent`'s rule multiset with `.aw/state/k6jd6l/before/`; commit through `aw commit um2kvx -- <paths>`.
  - Depends on: E-03
  - Expected outcome: the readers are gone; the check multiset is unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `specs._read_status` used `SPEC_STATUS_RE`, which Order 292 moved; this plan deletes the function itself.
- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `history(id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`), and the legacy loader (`load_legacy_artifact`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `f83159217` with `rg -n "_read_(status|gate|blocks_release|priority|work_kind|scope|summary)\(" agent_workflows tests`: see the Concern.

## Proposed changes (ordered, validatable)

1. Retarget the internal callers (E-01).
2. Retarget `attention` (E-02).
3. Retarget `check_engine` (E-03).
4. Delete the readers and commit (E-04).

## Deferred / out of scope (with reason)

- `check_engine._read_blocks_release`.
  - Carrier: e8420v
- `backlog.parse_item`.
  - Carrier: po3o1c

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 4 work Scope-Paths.

## Required tests / validation

The three PIN modules and the `aw check all --all --agent` rule multiset.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Open questions

### OQ-01: Order 45 (`e8420v`) also edits `check_engine`; is a unit handled twice?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No: Order 45 deletes `check_engine._read_blocks_release` and the `check_engine` regex literals; this plan changes only the three `_specs._read_*` calls. Order 45 depends on `k6jd6l`, so it runs later. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "_read_(status|gate|blocks_release|priority|work_kind|scope|summary)\(" agent_workflows/specs.py` listing only the seven definitions.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "specs_mod\._read_" agent_workflows/attention.py` printing nothing and the before/after per-test lines of `tests/test_attention.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "_specs\._read_" agent_workflows/check_engine.py` printing nothing and the before/after per-test lines of `tests/test_check_engine.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the empty output of `rg -n "specs\._read_|_specs\._read_|def _read_(status|gate|blocks_release|priority|work_kind|scope|summary)\b" agent_workflows/specs.py agent_workflows/attention.py agent_workflows/check_engine.py`, `diff .aw/state/9o83cr/E-18a-before.txt .aw/state/9o83cr/E-18a-after.txt` with no FAILED or ERROR line, the rule-multiset `diff` (empty), and `git show --stat` of the `aw commit um2kvx` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first where an item deletes or retargets. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit um2kvx -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
