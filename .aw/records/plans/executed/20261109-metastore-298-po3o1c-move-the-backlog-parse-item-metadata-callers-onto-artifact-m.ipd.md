# IPD: Move the backlog parse_item metadata callers onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader (`artifact_meta`). Part 19 of the round-3 split of `k6jd6l` (Order 43, research `nj8zdp` guidance). `backlog.parse_item` returns a `BacklogItem` with metadata fields and body sections; `k6jd6l` E-18 removes its metadata part. This part moves the callers that read METADATA from it onto `artifact_meta`. Measured at `f83159217` (`k6jd6l` F-25 live list): `attention._backlog_record` (1), `set_records.promote_question_to_backlog` and `set_records.close_on_answer` (2), `tools/gate_drop_audit.census` (1), and the `backlog` internal callers `find_duplicate_candidates`, `validate_item`, `existing_backlog_ids`, `blocks_release_of_item`, `find_item`, `run_new`, `run_note` and `run_check` (8).
- Scope: The caller half of `k6jd6l` E-18's `backlog.parse_item` work. Callers in `check_engine`, `runner_shared`, `status_set` and `production_checks` are in phase-B Scope-Paths (`ffceq0`, `t4gl15`) and expected moved; a live one in Order 280's F-25 is retargeted here with `--scope-reason`. EXCLUDES changing `parse_item` itself (Order 299).
- Scope-Paths: agent_workflows/attention.py, agent_workflows/set_records.py, tools/gate_drop_audit.py, agent_workflows/backlog.py, tests/test_gate_drop_audit.py, .aw/records/plans/pending/20261109-metastore-298-po3o1c-move-the-backlog-parse-item-metadata-callers-onto-artifact-m.ipd.md
- Scope-Exceeded: .aw/records/backlog/open/20261124-metastore-01-5t533v-artifact-meta-bullet-reader-strips-edge-whitespace.backlog.md (defect-report carrier the driver requires for a finding made while executing po3o1c artifact_meta.read_text strips edge FF/VT/FS-US/NEL that parse_item kept, hiding them from is_safe_descriptive a new...); agent_workflows/runner_shared.py (k6jd6l F-25 plan 6bxlzb assigns the live runner_shared.perform_coordinator_proposal_file parse_item caller to this plan the plan's Scope says a live F-25 caller is retargeted here with --scope-reason)
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15, executed:um2kvx
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 298
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: po3o1c

> Written to .aw/system/workflows/technical-writing/technical-writing.md. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

## Workflow history
- 2026-11-24 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5.5-1m-us variant=high profile=opus): aw oc run self-finalize: po3o1c verified (set metastore, attempt 2). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261124-metastore-01-5t533v-artifact-meta-bullet-reader-strips-edge-whitespace.backlog.md: defect-report carrier the driver requires for a finding made while executing po3o1c (artifact_meta.read_text strips edge FF/VT/FS-US/NEL that parse_item kept, hiding them from is_safe_descriptive); a new record, edits no existing file; out-of-scope agent_workflows/runner_shared.py: k6jd6l F-25 (plan 6bxlzb) assigns the live runner_shared.perform_coordinator_proposal_file parse_item caller to this plan; the plan's Scope says a live F-25 caller is retargeted here with --scope-reason; in-scope-unmodified agent_workflows/attention.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_gate_drop_audit.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED; review record .aw/records/reviews/20261109-metastore-298-po3o1c-move-the-backlog-parse-item-metadata-callers-onto-artifact-m.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from k6jd6l (round 3, research nj8zdp guidance).

## Goal

Every caller that reads a metadata field of a backlog item reads it from `artifact_meta`; only body-section uses of `backlog.parse_item` remain.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Carried from `k6jd6l` E-18: "the metadata part of `backlog.parse_item`; their remaining callers use `artifact_meta.read`, `read_text` or `read_at` ... Retarget `tools/gate_drop_audit.py`'s `backlog.parse_item` call to `artifact_meta.read`/`read_at`, keeping `tests/test_gate_drop_audit.py` green." Ensure directory `.aw/state/9o83cr/` exists (`mkdir -p .aw/state/9o83cr/`), and save the before-list of `tests/test_attention.py`, `tests/test_gate_drop_audit.py`, `tests/test_backlog.py` and `tests/test_backlog_duplicate_guard.py` to `.aw/state/9o83cr/E-18b-before.txt`.

PIN RULE (carried from `9o83cr`): before an edit that deletes or retargets, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > <before-file>`); after it, run the same command into the matching after-file. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: one module per item

- [x] E-01 Capture the baseline PIN list (`mkdir -p .aw/state/9o83cr/` and save `.aw/state/9o83cr/E-18b-before.txt`); then in `attention._backlog_record`, read the item's metadata through `artifact_meta.read_text(text, record_type="backlog")` instead of `backlog_mod.parse_item`.
  - Depends on: none
  - Expected outcome: `attention` calls no `parse_item`.
  - Execution state: performed

- [x] E-02 In `set_records.promote_question_to_backlog` and `set_records.close_on_answer`, read the item id and metadata through `artifact_meta`; keep `parse_item` only where the body sections are re-rendered.
  - Depends on: E-01
  - Expected outcome: `set_records` reads no metadata field from `parse_item`.
  - Execution state: performed

- [x] E-03 In `tools/gate_drop_audit.census`, replace `backlog.parse_item` with `artifact_meta.read`/`read_at`.
  - Depends on: E-02
  - Expected outcome: `tools/gate_drop_audit.py` calls no `parse_item`; its test passes.
  - Execution state: performed

- [x] E-04 In the eight `backlog` internal callers (`backlog.find_duplicate_candidates`, `validate_item`, `existing_backlog_ids`, `blocks_release_of_item`, `find_item`, `run_new`, `run_note`, `run_check`), read metadata fields through `artifact_meta.read_text`; keep `parse_item` only for body sections; save the after-list; commit through `aw commit po3o1c -- <paths>`.
  - Depends on: E-03
  - Expected outcome: no `backlog` caller reads a metadata field from `parse_item`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `backlog.parse_item` body parsing (N3) may stay; its metadata fields come from `artifact_meta`.
- `backlog.validate_item` also uses the `attention_contract` gate regexes (`A.GATE_KIND_RE` and siblings); Order 248 (`tdhav3`) owns those.
- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `history(id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`), and the legacy loader (`load_legacy_artifact`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `f83159217` with `rg -n "parse_item\(" agent_workflows tools tests`: see the Concern. Other production callers at that commit: `check_engine` 3, `runner_shared` 9, `status_set` 5, `production_checks` 2 (phase B).

Execution (2026-11-24, starting HEAD `7821d7423`): no production caller used `parse_item` for body sections (it parses only the leading bullet block). Every caller was therefore retargeted, through a new `backlog.item_from_text` adapter that fills the `BacklogItem` fields from `artifact_meta.read_text(text, record_type="backlog").fields`, keeping the single-token rule the old `\S+` patterns enforced. After this plan, `parse_item` has no production caller, only tests, which is the input Order 299 (`vw88h0`) needs to choose deleting it.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["1. Retarget attention (E-01)<br/>Capture PIN baseline, read metadata via artifact_meta.read_text"]
    E02["2. Retarget set_records (E-02)<br/>Read id and metadata via artifact_meta, keep body re-rendering"]
    E03["3. Retarget gate_drop_audit (E-03)<br/>Replace parse_item with artifact_meta.read/read_at"]
    E04["4. Retarget backlog internals & commit (E-04)<br/>Read metadata via artifact_meta, verify PIN after-list, aw commit"]

    E01 --> E02
    E02 --> E03
    E03 --> E04
```

1. Retarget `attention` (E-01): Capture baseline PIN test outcomes to `.aw/state/9o83cr/E-18b-before.txt`, then update `attention._backlog_record` to read backlog metadata through `artifact_meta.read_text(text, record_type="backlog")`.
2. Retarget `set_records` (E-02): Update `set_records.promote_question_to_backlog` and `set_records.close_on_answer` to read item IDs and metadata through `artifact_meta`, preserving `parse_item` only where body sections are re-rendered.
3. Retarget `gate_drop_audit` (E-03): In `tools/gate_drop_audit.census`, replace `backlog.parse_item` with `artifact_meta.read`/`read_at` while keeping `tests/test_gate_drop_audit.py` passing.
4. Retarget the `backlog` internals and commit (E-04): Update internal callers in `backlog.py` (`find_duplicate_candidates`, `validate_item`, `existing_backlog_ids`, `blocks_release_of_item`, `find_item`, `run_new`, `run_note`, `run_check`) to read metadata via `artifact_meta.read_text`, verify after-list PIN outcomes match before-list, and commit via `aw commit po3o1c`.

## Deferred / out of scope (with reason)

- Removing the metadata part of `parse_item`.
  - Carrier: vw88h0

## Scope check

- Over-scope: none.
- Under-scope: If Order 280's F-25 lists a live caller outside these files, retarget it here with `--scope-reason`. Size: 4 E-items, 5 work Scope-Paths.

## Required tests / validation

The four PIN modules above.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Open questions

### OQ-01: Does `backlog.parse_item` disappear entirely?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Carried from `k6jd6l` OQ-02: no; `9o83cr` E-11 deletes only "the metadata part of `backlog.parse_item`". Body sections are Markdown prose that N3 keeps, so a body-only parser may survive; Order 299 decides by whether any caller still needs body sections. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `rg -n "parse_item\(" agent_workflows/attention.py` printing nothing and the before/after per-test lines of `tests/test_attention.py`.
  - Observed evidence: `rg -n "parse_item\(" agent_workflows/attention.py` printed nothing (`attention_rc=1`). `attention._backlog_record` already read every field through `artifact_meta.read_text(text, record_type="backlog")` at starting HEAD `7821d7423`, and no edit was needed (decision 12-po3o1c-D1). Baseline saved to `.aw/state/9o83cr/E-18b-before.txt` before any edit. `tests/test_attention.py` lines: 76 PASSED before and 76 PASSED after; the before/after lists are identical (the full `diff` under V-04 printed nothing).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `rg -n "parse_item\(" agent_workflows/set_records.py` with each remaining hit labelled body-only.
  - Observed evidence: `rg -n "parse_item\(" agent_workflows/set_records.py` printed nothing (`sr_rc=1`), so no hit remains to label. `set_records.promote_question_to_backlog` reads the id through `_backlog.item_from_text(...).id`, and `set_records.close_on_answer` reads the status and id through `_backlog.item_from_text(text)`. Both read through the new `backlog.item_from_text` adapter, which builds a `BacklogItem` from `artifact_meta.read_text(text, record_type="backlog").fields`. Neither function re-renders body sections from `parse_item`. Covered by `tests/test_backlog.py` and `tests/test_history_block_bounding.py` (part of the 312 passed in the narrowed run).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `rg -n "parse_item" tools/gate_drop_audit.py` printing nothing and the before/after per-test lines of `tests/test_gate_drop_audit.py`.
  - Observed evidence: `rg -n "parse_item" tools/gate_drop_audit.py` printed nothing (`gda_rc=1`). `census` now reads `artifact_meta.read_text(item_text, record_type="backlog").fields.get("work_kind")`. `tests/test_gate_drop_audit.py`: 10 PASSED before and 10 PASSED after, with the same names:

    ```
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_custom_message_flag_spelling_close_dated
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_gated_done_item_executed_carrier_handoff_not_reported
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_gated_done_item_no_carrier_reported
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_gated_done_item_superseded_carrier_reported_carrier_not_executed
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_graduated_then_done_dated_by_done_line
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_persisted_close_evidence_not_reported
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_pre_boundary_close_partitioned_pre_predicate
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_read_only_property_preserves_bytes_and_mtime
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_undated_item_partitioned_undated
    PASSED tests/test_gate_drop_audit.py::TestGateDropAudit::test_ungated_done_item_not_reported
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `rg -n "parse_item\(" agent_workflows/backlog.py` with each hit labelled body-only (or the definition), `diff .aw/state/9o83cr/E-18b-before.txt .aw/state/9o83cr/E-18b-after.txt` with no FAILED or ERROR line, and `git show --stat` of the `aw commit po3o1c` commit.
  - Observed evidence: `rg -n "parse_item\(" agent_workflows/backlog.py` prints only the definition:

    ```
    342:def parse_item(text: str) -> BacklogItem:
    ```

  The eight callers (`find_duplicate_candidates`, `validate_item`, `existing_backlog_ids`, `blocks_release_of_item`, `find_item`, `run_new`, `run_note`, `run_check`) call `item_from_text`. Across the whole repository, `rg -n "parse_item\(" agent_workflows tools` prints only that definition: the two `runner_shared.perform_coordinator_proposal_file` references that k6jd6l F-25 (plan `6bxlzb`) assigned here were also moved, to `_meta_reader.read_text(..., record_type="backlog").id6`, with a `--scope-reason`. `diff .aw/state/9o83cr/E-18b-before.txt .aw/state/9o83cr/E-18b-after.txt` printed nothing (`diff_rc=0`). Both lists hold 142 lines and `grep -cE "^(FAILED|ERROR)"` counts 0 in the after-list (76 attention, 47 backlog, 9 duplicate guard, 10 gate_drop_audit). Parity probe (starting-HEAD `parse_item` against `item_from_text` on all 12 fields): `1293 inputs 7 diffs`. The input set is 1277 corpus items, the tests' `*.backlog.md` files and 16 fixtures (CRLF, FF, NEL, U+2028, bare CR, multi-word values, legacy and dual Kind, duplicate Status, gate, fence, title, trailing whitespace, tab). All 7 diffs fall in two synthetic fixtures, and `validate_item` differs on those same 2 of 1293 inputs (decisions D2 and D3). Core suite `aw suite`: `2889 passed, 1 skipped, 11 warnings in 107.23s`. `git show --stat HEAD` of the `aw commit po3o1c` commit:

    ```
    commit d941c41258caa7fca43c0829c10fd76bbdd9ecb5
        metastore 298 (po3o1c): move the backlog parse_item metadata callers onto artifact_meta (backlog.item_from_text adapter; set_records, gate_drop_audit, runner_shared proposal filing retargeted)
     agent_workflows/backlog.py       | 56 ++++++++++++++++++++++++++++++++++------
     agent_workflows/runner_shared.py |  8 +++---
     agent_workflows/set_records.py   |  6 ++---
     tools/gate_drop_audit.py         | 10 ++++---
     4 files changed, 63 insertions(+), 17 deletions(-)
    ```

  Attempt 2 re-verification (2026-11-24, lane `aw/lane/po3o1c_attempt2`, base `f31580e26`, which adds an `artifact_meta.py` perf commit after attempt 1's base). The attempt-1 code diff was applied unchanged. The PIN baseline was re-captured on the UNMODIFIED base (`.aw/state/9o83cr/E-18b-before.txt`: 142 lines, all `PASSED`), the diff was applied, and the after-list re-captured: `diff ... E-18b-before.txt ... E-18b-after.txt` printed nothing (`diff_rc=0`), 142 lines, `grep -cE "^(FAILED|ERROR)"` printed `0`, per module 76 attention, 10 gate_drop_audit, 47 backlog, 9 duplicate guard. `rg -n "parse_item\(" agent_workflows tools` printed only `agent_workflows/backlog.py:342:def parse_item(text: str) -> BacklogItem:`. Corpus parity probe (`parse_item` against `item_from_text` on the 12 fields, every `*.backlog.md` under `.aw/records/backlog` and `tests`): `1276 inputs 0 differing`. `aw suite`: `2889 passed, 1 skipped, 11 warnings in 98.42s (0:01:38)`. `git show --stat 8fa20ac0a` (this attempt's `aw commit po3o1c` commit):

    ```
    commit 8fa20ac0abd41c907c697ea9b7228a28240672cd
        metastore 298 (po3o1c): move the backlog parse_item metadata callers onto artifact_meta (backlog.item_from_text adapter; set_records, gate_drop_audit, runner_shared proposal filing retargeted; brought forward from lane aw/lane/po3o1c d941c4125)
     agent_workflows/backlog.py       | 56 ++++++++++++++++++++++++++++++++++------
     agent_workflows/runner_shared.py |  8 +++---
     agent_workflows/set_records.py   |  6 ++---
     tools/gate_drop_audit.py         | 10 ++++---
     4 files changed, 63 insertions(+), 17 deletions(-)
    ```

  Scope reasons recorded with `aw commit po3o1c --scope-reason`: `agent_workflows/runner_shared.py` (k6jd6l F-25 live caller, as the plan's Scope directs) and `.aw/records/backlog/open/20261124-metastore-01-5t533v-artifact-meta-bullet-reader-strips-edge-whitespace.backlog.md` (the defect-report carrier for finding 5t533v, committed as `4524dc046`).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Safety stop: if prerequisite metastore reader symbols from `t4gl15`, `ffceq0`, or `1ajqaa` are absent, stop and report rather than proceeding. Shared-checkout safety: this plan edits only its Scope-Paths; do not stage, edit, or commit any other file.

Pin-first where an item deletes or retargets. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit po3o1c -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize po3o1c` itself.
