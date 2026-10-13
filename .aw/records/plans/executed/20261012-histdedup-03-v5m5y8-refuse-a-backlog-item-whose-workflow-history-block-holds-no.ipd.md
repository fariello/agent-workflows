# IPD: Refuse a backlog item whose Workflow history block holds no record

- Date: 2026-10-12
- Kind: child
- Concern: Nothing in the tree refuses a backlog item whose `## Workflow history` block holds no record. Backlog `wkpcop` measured a suppressed same-status write leaving the heading with no record under it while `backlog.validate_item` returned no drift, and re-measured in this lane at HEAD `5ebf5364d`: after `aw backlog set <item> --status open --message "metadata only"` over an item whose only history-shaped line is indented, `backlog.validate_item(path, text)` returned `[]`. The item names a validation rule for this as "a cheap independent backstop". It is independent of the reader reconciliation in sibling `kgv213`: that plan removes the one measured route to the state, this plan makes any route to it visible.
- Scope: IN: (a) a new `backlog.validate_item` drift rule `backlog.history-empty` raised when the item's `## Workflow history` heading is ABSENT or its block holds no column-zero record, reading the block through `attention_contract.history_block` (added by `kgv213`) so the check and the writer agree on what a record is; (b) document the rule in the backlog README's validation section and in the `aw backlog check` help text; (c) behavioral tests; (d) repair the two existing `tests/test_check_engine.py` backlog fixtures that carry no history and would otherwise start failing (F-04); (e) a CHANGELOG entry. OUT: the same rule for specs or plans (specs carry their own `aw specs check` and plans are fenced by `ipd_lint`; neither was measured empty); a fixer or migration (no tracked item violates the rule, F-02); refusing at write time in `status_set` (the writer fix is `kgv213`'s).
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/cli.py, tests/test_backlog_history_empty_rule.py, tests/test_check_engine.py, .aw/records/backlog/README.md, CHANGELOG.md
- Scope-Exceeded: tests/test_generic_color_depth.py (E-05 re-derivation repaired fixture lacking history block); tests/test_validator_nonsurveyable_dir.py (E-05 re-derivation repaired fixture lacking history block)
- Item-Dependencies: executed:kgv213
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: wkpcop
- Set: histdedup
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: v5m5y8

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: v5m5y8 verified (set histdedup, attempt 1). [Scope reconciliation - out-of-scope tests/test_generic_color_depth.py: E-05 re-derivation repaired fixture lacking history block; out-of-scope tests/test_validator_nonsurveyable_dir.py: E-05 re-derivation repaired fixture lacking history block]
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Record: .aw/records/reviews/20261012-histdedup-03-v5m5y8-refuse-a-backlog-item-whose-workflow-history-block-holds-no.review.md Round 1

- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `wkpcop` as the item's suggested independent backstop. Live-corpus violation count measured as 0 of 967 tracked backlog items at HEAD `5ebf5364d`, so the rule refuses nothing that exists today. Blocking status: none.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make an empty or missing `## Workflow history` block on a backlog item a validation error, so a writer defect that strips an item's provenance is caught by `aw backlog check` / `aw check` instead of passing silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rule

- [x] E-01 `agent_workflows/backlog.py` (`validate_item`): before `return drift`, append `core.Drift(rel, "backlog.history-empty", <detail>)` when `A.history_block(text).records` is empty. The detail must distinguish "no `## Workflow history` heading" (test the heading with the same `(?m)^## Workflow history[ \t]*$` anchor `history_block` uses, so the two cannot disagree on whether a heading exists) from "heading present but no column-zero `- YYYY-MM-DD ...` record in the block", and name the remedy (restore the records from git history; an indented line is not a record). Do NOT add a `RULE_REGISTRY` entry: an unregistered rule resolves to `check_engine._DEFAULT_RULESPEC` (severity `error`), which is the intended fail-closed severity and matches every sibling `backlog.*` shape rule except the three registered in `RULE_REGISTRY`. Prerequisite check FIRST: `kgv213` must be in `.aw/records/plans/executed/` AND `attention_contract.history_block` must exist (at review HEAD `1134a92b6`, `kgv213` was `reviewed` in `pending/` and `history_block` was absent). If either fails, mark this item `blocked`, paste the check, and edit nothing.
  - Depends on: none
  - Expected outcome: `validate_item` reports `backlog.history-empty` on both empty shapes, with distinct detail text, and nothing new on a conformant item. Accepted consequence, intended: every `validate_item` consumer (`aw backlog check`, `aw check` record type `backlog`, `set_records.promote`, the `runner_shared` run-structure preflight) now refuses such an item.
  - Execution state: performed

### Task group 2: tests and docs

- [x] E-02 `tests/test_backlog_history_empty_rule.py` (new): behavioral tests (P16) calling `backlog.validate_item` and the CLI. Cases: (a) a conformant item yields no `backlog.history-empty`; (b) heading with only an indented history-shaped line yields it with the "no column-zero record" detail; (c) heading with only blank lines then prose yields it; (d) no heading yields it with the "no heading" detail (assert the two details differ); (e) an item written by the real writer (`cli.main(["backlog","new",...,"--dir",<root>])`) yields no `backlog.history-empty`, fencing the Step 0 claim that every writer emits a record; (f) `cli.main(["backlog","check","--dir",<root>])` over a temp repo (laid out under `.aw/records/backlog/open/` as `tests/test_status_set.py` does, so `nonsurveyable_root_refusal` permits it) holding case (b) exits nonzero and names the rule in its output, and over a repo of conformant items exits 0; (g) `check_engine` record type `backlog` (drive `aw check backlog` via `cli.main` on the same temp repo) reports the rule for case (b).
  - Depends on: E-01
  - Expected outcome: the new module passes, and each case asserts on returned drift, exit codes or captured output only (no source inspection).
  - Execution state: performed

- [x] E-03 `.aw/records/backlog/README.md`: extend the `aw backlog check [--agent]` bullet's parenthesized rule list with `at least one column-zero history record [backlog.history-empty]`, matching the existing `[backlog.<rule>]` style.
  - Depends on: E-01
  - Expected outcome: README names the rule; no em or en dashes.
  - Execution state: performed

- [x] E-04 `CHANGELOG.md`: one entry under the top pending section for the new rule.
  - Depends on: E-01
  - Expected outcome: one new line, no em or en dashes.
  - Execution state: performed

- [x] E-05 `tests/test_check_engine.py`: give the backlog fixtures that carry no history a conformant `## Workflow history` block with one column-zero record (`\n## Workflow history\n\n- 2026-01-01 created (aw backlog): fixture\n`), so they keep testing what they were written to test (F-04): `LifecyclePlacementTests._BKLG_OPEN` and `_BKLG_DONE` (the row (e) expected rule set stays exactly `['check.id6-collision', 'check.lifecycle-placement-conflict']`), and the two backlog rows (`bkl111` open, `bkl222` done) in the `RetiredAndIgnoredScopeTests` artifact table (its "zero findings on a healthy tree" claim stays exactly zero). Do NOT add `backlog.history-empty` to any expected set and do NOT weaken an assertion. Then re-derive at execution whether any OTHER test fixture newly fails under the rule (the bare suite in V-05 answers this); repair each such fixture the same way and list it in V-05, or, if a failure is not a fixture lacking history, stop and report it.
  - Depends on: E-01
  - Expected outcome: both named tests pass with their original expected sets unchanged.
  - Execution state: performed

- [x] E-06 `agent_workflows/cli.py`: the `aw backlog check` parser description (the string listing "valid enums, status-mirrors-directory, gate present-and-valid iff blocked, unique id6, nonempty summary") gains "at least one Workflow history record", so `--help` names the new refusal.
  - Depends on: E-01
  - Expected outcome: `aw backlog check --help` mentions the history requirement.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `backlog.validate_item` is a fail-closed shape checker with no repo root (comment "f7igdu design constraint" in it); rules are `core.Drift(rel, "backlog.<rule>", detail)`. It is consumed by `aw backlog check`, `check_engine` (record_type `backlog`), `set_records.promote` (validates BEFORE writing) and `runner_shared`.
- `check_engine` skips `README.md`, `INDEX.md`, `STATUS.md` (`_SKIP_NAMES`), so the backlog README (which has a heading and no record) is not validated as an item.
- Every backlog writer (`backlog.run_new`/`_render_item`, `status_set.apply_status_change` via `_prepend_workflow_history_entry`) emits at least one column-zero record, so a conformant write cannot trip the rule.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | `validate_item` accepts an item with no history record. | In-lane probe at `5ebf5364d`: after the indented-fixture `aw backlog set`, `backlog.validate_item(p, p.read_text())` -> `[]`. |
| F-02 | No tracked backlog item would be refused. | Probe over all 967 tracked `*.backlog.md`: every file has the heading, and only `.aw/records/backlog/README.md` (not an item) has a block with no column-zero record. Re-measured at review over the wider `_iter_items` population, see F-05. `README.md` is excluded from validation by both `backlog._iter_items` (`f.name != "README.md"`) and `check_engine._SKIP_NAMES`. |
| F-03 | `set_records.promote` validates its rendered item before writing, and `_render_item` mints a `created` record, so the new rule does not affect promotion. | `set_records.promote`: `drift = _backlog.validate_item(dest, rendered)` before `atomic_write`; `backlog._render_item` appends `- {today} created (aw backlog): {msg}` under `## Workflow history`. |
| F-04 | Existing test fixtures without a history block WOULD break. The original plan assumed only new tests were affected. | Review probe at HEAD `1134a92b6`: the bare suite run with `validate_item` monkeypatched to add the rule (equivalent column-zero record test) gave `2 failed, 7279 passed, 2 skipped`; the failures are `tests/test_check_engine.py::LifecyclePlacementTests::test_six_row_regression_table` (row (e): got an extra `backlog.history-empty`, fixtures `_BKLG_OPEN`/`_BKLG_DONE`) and `tests/test_check_engine.py::RetiredAndIgnoredScopeTests::test_is_retired_and_the_default_scope_agree_about_every_artifact` (expected `[]`, got `{'backlog.history-empty': 1}`, from the active `bkl111` row). Both pass unpatched. E-05 repairs the fixtures. |
| F-05 | The live tracked corpus has one backlog file outside the `*.backlog.md` glob F-02 used. | `git ls-files .aw/records/backlog` lists `done/20260817-awphysical-01-xd78mr-e06-scenario-token-test-bindings.md`; `_iter_items` globs `*.md`, so it IS validated. Review probe over all 977 tracked `.md` files under the backlog tree: only `README.md` lacks a column-zero record, so the corrected population still has zero violators. |

## Proposed changes (ordered, validatable)

1. E-01 adds the rule.
2. E-05 repairs the existing fixtures the rule would otherwise break.
3. E-02 fences it; E-03, E-04 and E-06 document it.

## Deferred / out of scope (with reason)

- Specs and plans: not measured empty, and each has its own validator (`aw specs check`, `ipd_lint`); extending is a separate decision.
  - Carrier-Declined: neither tree was measured with an empty history block and each has its own validator
- Write-time refusal: the writer-side fix is `kgv213`; this plan is the read-side backstop the item asked for.
  - Carrier: kgv213
  - Carrier-Evidence: .aw/records/plans/executed/20261012-histdedup-02-kgv213-bound-the-workflow-history-block-by-one-shared-rule.ipd.md
- Fixer/migration: F-02 shows nothing to fix.
  - Carrier-Declined: F-02 measures zero violating tracked items

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_backlog_history_empty_rule.py tests/test_backlog.py tests/test_history_block_bounding.py tests/test_check_engine.py`, actual output pasted.
- The WHOLE BARE SUITE, `python3 -m pytest`, summary pasted, no new failure against the base.
- `aw backlog check` and `aw check` on the live corpus, output pasted, showing zero `backlog.history-empty` findings (re-derived at execution; F-02/F-05 measured zero at authoring and review).

Invariants: (I-1) a conformant item yields no new drift (E-02 (a), (e)); (I-2) both empty shapes are refused with distinguishable detail (E-02 (b)-(d)); (I-3) existing check_engine fixtures keep their exact expected rule sets (E-05, `tests/test_check_engine.py`); (I-4) the live corpus stays clean (V-01).

## Spec / documentation sync

`.aw/records/backlog/README.md` gains the rule (E-03) and the `aw backlog check` help text names it (E-06). No spec governs backlog validation rules.

## Open questions

### OQ-01: Should a missing heading be refused, or only an empty block?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Both. F-02 shows every tracked item has the heading and every writer emits one, so refusing its absence costs nothing today and catches the same provenance loss.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: PASTE the prerequisite check (`ls .aw/records/plans/executed/ | grep kgv213` and `python3 -c "from agent_workflows import attention_contract as A; print(A.history_block)"`). PASTE the `git diff` of `validate_item`. PASTE `aw backlog check` and `aw check backlog` output on the live repository showing no `backlog.history-empty` finding, and direct `validate_item` calls on the F-01 fixture AND on a no-heading fixture showing the rule with its two distinct detail texts. Runtime path: `backlog.run_check` -> `validate_item`; `check_engine` record type `backlog` -> `_backlog.validate_item`.
  - Observed evidence:
    1. Prerequisite check:
    ```sh
    $ ls .aw/records/plans/executed/ | grep kgv213 && python3 -c "from agent_workflows import attention_contract as A; print(A.history_block)"
    20261012-histdedup-02-kgv213-bound-the-workflow-history-block-by-one-shared-rule.ipd.md
    <function history_block at 0x79708d257950>
    ```

    2. git diff of validate_item:
    ```diff
    diff --git a/agent_workflows/backlog.py b/agent_workflows/backlog.py
    index bd665dacd..8b8ed1c8c 100644
    --- a/agent_workflows/backlog.py
    +++ b/agent_workflows/backlog.py
    @@ -121,6 +121,7 @@ _RELEASE_EXEMPT_REF_RE = re.compile(
         r"^- Release-Exempt-Ref:[ \t]*(?P<value>.+?)[ \t]*$"
     )
     _CLOSE_EVIDENCE_RE = re.compile(r"^- Close-Evidence:[ \t]*(?P<value>.+?)[ \t]*$")
    +_WORKFLOW_HISTORY_HEADING_RE = re.compile(r"(?m)^## Workflow history[ \t]*$")
     _TOP_KEY_RE = re.compile(r"^- ([A-Za-z0-9_-]+):(?:\s*(.*))?$")
     _TEMPLATE_OWNED_KEYS = frozenset(
         (
    @@ -609,6 +610,20 @@ def validate_item(path: Path, text: str) -> List[core.Drift]:
                 )
             )

    +    hist_block = A.history_block(text)
    +    if not hist_block.records:
    +        if not _WORKFLOW_HISTORY_HEADING_RE.search(text):
    +            detail = (
    +                "no ## Workflow history heading; restore the records from git history "
    +                "(an indented line is not a record)"
    +            )
    +        else:
    +            detail = (
    +                "heading present but no column-zero '- YYYY-MM-DD ...' record in the block; "
    +                "restore the records from git history (an indented line is not a record)"
    +            )
    +        drift.append(core.Drift(rel, "backlog.history-empty", detail))
    +
         return drift
    ```

    3. aw backlog check and aw check backlog output on live repository:
    ```
    $ python3 -m agent_workflows.cli backlog check && python3 -m agent_workflows.cli check backlog
    aw backlog check: all backlog items conform. 992 backlog items checked.
    AW check  backlog                                                        1861 ms
    ✓ CONFORMS  76 backlog checked

    Findings:
      Issue: cross-tree collisions NOT checked by a per-type run [INFO]
      - <collisions>
        1. <collisions> [INFO]
        Fix: aw check all


    Evidence
      checked  76
      errors  0   warnings  0   info  1

    Next  aw backlog check
    Agent output: --agent
    ```

    4. Direct validate_item calls on F-01 fixture and no-heading fixture:
    ```
    F-01 fixture:
      rule: backlog.history-empty
      detail: heading present but no column-zero '- YYYY-MM-DD ...' record in the block; restore the records from git history (an indented line is not a record)

    No heading fixture:
      rule: backlog.history-empty
      detail: no ## Workflow history heading; restore the records from git history (an indented line is not a record)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the pytest output of the new module passing, and name, per E-02 case (a)-(g), the assertion that pins it (behaviour plus mechanism; a test function name is a pointer only, not the bar).
  - Observed evidence:
    Pytest runner output:
    ```
    $ python3 -m pytest -o addopts="" -q tests/test_backlog_history_empty_rule.py
    .......                                                                  [100%]
    7 passed in 0.82s
    ```

    Assertion pinning per case:
    - Case (a): `assert history_rules == []` where `history_rules = [d.rule for d in drift if d.rule == "backlog.history-empty"]` validating that a conformant item yields zero history drift.
    - Case (b): `assert len(history_drifts) == 1 and "no column-zero" in history_drifts[0].detail and "restore the records from git history (an indented line is not a record)" in history_drifts[0].detail` on an item whose heading only contains an indented line.
    - Case (c): `assert len(history_drifts) == 1 and "no column-zero" in history_drifts[0].detail` on an item whose heading contains blank lines then prose without a record bullet.
    - Case (d): `assert len(d_drifts) == 1 and "no ## Workflow history heading" in d_drifts[0].detail and d_drifts[0].detail != b_drifts[0].detail` asserting distinct detail messages between absent heading and empty records block.
    - Case (e): `assert code == 0` for `cli.main(["backlog", "new", ..., "--apply"])` and `assert history_rules == []` for `backlog.validate_item(item_file, item_file.read_text())`, proving the production writer emits conformant history.
    - Case (f): `assert code != 0 and ("backlog.history-empty" in out or "backlog.history-empty" in err)` for `cli.main(["backlog", "check", "--dir", ...])` on case (b), and `assert code_ok == 0` on conformant items.
    - Case (g): `assert code != 0 and ("backlog.history-empty" in out or "backlog.history-empty" in err)` for `cli.main(["check", "backlog", "--dir", ...])` on case (b).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE `git diff .aw/records/backlog/README.md`.
  - Observed evidence:
    ```diff
    diff --git a/.aw/records/backlog/README.md b/.aw/records/backlog/README.md
    index aee26c1a5..3a4b57e37 100644
    --- a/.aw/records/backlog/README.md
    +++ b/.aw/records/backlog/README.md
    @@ -113,7 +113,8 @@ Portability limit: `DECISIONS.md` is this repository's own local log and is NOT
       same-status `set` is a transition call doing an annotation's job, and history is what suffers.
     - `aw backlog check [--agent]` validate the tree fail-closed (valid enums, status-mirrors-directory,
       gate present-and-valid iff blocked, unique id6, nonempty summary, no repeated metadata bullets [backlog.metadata-bullet-repeated],
    -  Gate-Summary present only when blocked [backlog.gate-summary-unexpected], safe bounded Gate-Summary [backlog.gate-descriptive-unsafe]).
    +  Gate-Summary present only when blocked [backlog.gate-summary-unexpected], safe bounded Gate-Summary [backlog.gate-descriptive-unsafe],
    +  at least one column-zero history record [backlog.history-empty]).

     History is recorded INLINE in the item's `## Workflow history`, newest record first, and prior records
     are kept. That inline block is the durable copy, because it is the one that is committed and therefore
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE `git diff CHANGELOG.md`.
  - Observed evidence:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 760a7cf59..32bc0d790 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Added: `backlog.validate_item` and `aw backlog check` now report rule `backlog.history-empty` when a backlog item lacks a `## Workflow history` heading or its block contains no column-zero records.
     - Fixed: runs with verification on no longer start a background test-suite baseline they never read.
     - Fixed: attention, check and readiness readers now share the history bounding rule, so a quoted indented history line can no longer attest a review.
     - Fixed: a mismatch between the runner's own agent_workflows package and the one a nested aw call would load now fails only the affected item (with a tool-identity-mismatch refusal) instead of stopping the whole aw oc run or aw agy run; other independent items keep running.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE `git diff tests/test_check_engine.py` showing only fixture text gained a history block and no expected rule set or assertion changed. PASTE `python3 -m pytest -o addopts="" -q tests/test_check_engine.py` passing. PASTE the bare-suite `python3 -m pytest` summary line, and list every other fixture repaired under E-05's re-derivation (or state none).
  - Observed evidence:
    1. git diff tests/test_check_engine.py:
    ```diff
    diff --git a/tests/test_check_engine.py b/tests/test_check_engine.py
    index fddf22c6a..32bb5c202 100644
    --- a/tests/test_check_engine.py
    +++ b/tests/test_check_engine.py
    @@ -805,6 +805,8 @@ class LifecyclePlacementTests(unittest.TestCase):
             "- Priority: high\n"
             "- Work-Kind: feature\n"
             "- Summary: Open\n\n"
    +        "## Workflow history\n\n"
    +        "- 2026-01-01 created (aw backlog): fixture\n\n"
             "## Detail\n\nx\n"
         )

    @@ -815,6 +817,8 @@ class LifecyclePlacementTests(unittest.TestCase):
             "- Priority: high\n"
             "- Work-Kind: feature\n"
             "- Summary: Done\n\n"
    +        "## Workflow history\n\n"
    +        "- 2026-01-01 created (aw backlog): fixture\n\n"
             "## Detail\n\nx\n"
         )

    @@ -1603,7 +1607,7 @@ class RetiredAndIgnoredScopeTests(unittest.TestCase):
             (
                 "a backlog item in open/",
                 ".aw/records/backlog/open/20260101-bkl111-01-bkl111-open.backlog.md",
    -            "- Id: bkl111\n- Status: open\n- Set: bkl111\n- Priority: high\n- Work-Kind: feature\n- Summary: Open\n\n## Detail\n\nx\n",
    +            "- Id: bkl111\n- Status: open\n- Set: bkl111\n- Priority: high\n- Work-Kind: feature\n- Summary: Open\n\n## Workflow history\n\n- 2026-01-01 created (aw backlog): fixture\n\n## Detail\n\nx\n",
                 False,
                 "the active case for the third tree shape, whose disposition directories are STATUS "
                 "names. `open/` must not be mistaken for a retirement segment",
    @@ -1611,7 +1615,7 @@ class RetiredAndIgnoredScopeTests(unittest.TestCase):
             (
                 "a backlog item in done/",
                 ".aw/records/backlog/done/20260101-bkl222-01-bkl222-done.backlog.md",
    -            "- Id: bkl222\n- Status: done\n- Set: bkl222\n- Priority: high\n- Work-Kind: feature\n- Summary: Done\n\n## Detail\n\nx\n",
    +            "- Id: bkl222\n- Status: done\n- Set: bkl222\n- Priority: high\n- Work-Kind: feature\n- Summary: Done\n\n## Workflow history\n\n- 2026-01-01 created (aw backlog): fixture\n\n## Detail\n\nx\n",
                 True,
                 "THE OVERLAP ROW: `done` is BOTH a directory segment and a status, so this path is "
                 "retired by either mechanism. Kept because it is the shape most likely to be "
    ```

    2. test_check_engine.py passing:
    ```
    $ python3 -m pytest -o addopts="" -q tests/test_check_engine.py
    ..................................................                       [100%]
    50 passed in 8.62s
    ```

    3. Bare-suite python3 -m pytest summary line:
    ```
    8261 passed, 4 skipped, 18 xfailed, 3 warnings in 518.37s (0:08:38)
    ```

    4. Other fixtures repaired under E-05's re-derivation:
    - `tests/test_generic_color_depth.py`: `GenericColorDepthTests.test_cell_g_subprocess_end_to_end` backlog fixture (`fixture_dir / ".aw" / "records" / "backlog" / "open" / "20261001-test01-01-test01-sample.backlog.md"`) gained a conformant `## Workflow history` block (`\n## Workflow history\n\n- 2026-01-01 created (aw backlog): fixture\n`).
    - `tests/test_validator_nonsurveyable_dir.py`: `_BACKLOG_CONTENT` fixture used across `ValidatorNonsurveyableDirTests` gained a conformant `## Workflow history` block (`\n## Workflow history\n\n- 2026-01-01 created (aw backlog): fixture\n`).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE `git diff agent_workflows/cli.py` and the `aw backlog check --help` description text showing the history requirement.
  - Observed evidence:
    1. git diff agent_workflows/cli.py:
    ```diff
    diff --git a/agent_workflows/cli.py b/agent_workflows/cli.py
    index 3574c48b2..17dcac935 100644
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -557,7 +557,8 @@ _DESCRIPTIONS = {
         ),
         "backlog check": (
             "Validate the backlog tree against the contract and fail closed: valid enums, "
    -        "status-mirrors-directory, gate present-and-valid iff blocked, unique id6, nonempty summary. "
    +        "status-mirrors-directory, gate present-and-valid iff blocked, unique id6, nonempty summary, "
    +        "at least one Workflow history record. "
             "--agent emits tab-separated drift records."
         ),
         "specs": (
    ```

    2. aw backlog check --help description text:
    ```
    Validate the backlog tree against the contract and fail closed: valid enums,
    status-mirrors-directory, gate present-and-valid iff blocked, unique id6,
    nonempty summary, at least one Workflow history record. --agent emits tab-
    separated drift records.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Open questions: OQ-01 resolved; none open. Scope fence: the Scope-Paths are a declaration; an edit outside them is made and justified with `--scope-reason` at finalize, not a reason to stop. Run `aw ipd begin v5m5y8` before the first edit. This plan requires explicit human approval before execution and depends on `kgv213` being executed (`- Item-Dependencies: executed:kgv213`); if that prerequisite is unmet, E-01 is `blocked` and nothing is edited. The executor is bound by the AGENTS.md execution contract: commit only the declared Scope-Paths through `aw commit <plan> -- <paths>` and verify the staged set with `git diff --cached --name-only`, never `git add -A`, never `--no-verify`, never push, and MUST paste the actual runner output for every test claim (never claim a pass not run). Before the terminal transition `aw ipd lint --phase pre-transition` must report conforming with every `V-*` carrying pasted evidence. Under `aw oc run` / `aw agy run` the runner performs finalize and the executor MUST NOT run it; only in a manual run the executor runs `aw ipd finalize v5m5y8 ... --apply`. Never hand-edit `- Status: executed`. Do not set backlog `wkpcop` to `done`.
