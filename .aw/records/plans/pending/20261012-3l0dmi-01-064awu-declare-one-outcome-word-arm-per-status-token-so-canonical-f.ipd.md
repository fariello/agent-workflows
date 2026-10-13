# IPD: Declare one outcome-word arm per status token so canonical fail-gate and its legacy aliases agree by decision, not by accident

- Date: 2026-10-12
- Kind: child
- Concern: `render_stream.render_run_summary_table`'s OUTCOME-WORD ladder (the `elif` chain that picks `INTERRUPTED` / `FAILED` / `BLOCKED` / `COMPLETED` / `NO WORK PERFORMED` / `STRANDED` / `PARTIAL` / `QUEUED`) renders DIFFERENT words for spellings that `runner_shared.TERMINAL_STATUS_ALIASES` declares to be the SAME state. Measured at HEAD `b1b2fab2b` by calling the real function on one-item queues: canonical `fail-gate` renders `BLOCKED`, while its legacy aliases render `FAILED` (`failed-safely`), `COMPLETED` (`substantially-complete`) and `BLOCKED` (`blocked`); canonical `fail-verify` renders `FAILED` while its alias `partial` renders `PARTIAL`; canonical `not-run` renders `BLOCKED` while its alias `not-attempted` renders `QUEUED`. Nothing in the code says which of these differences are intended. Plan `fr19jr` found the `fail-gate` case (its F-04), measured that the obvious fix (add `fail-gate` to the `FAILED` arm) contradicts a shipped behavioral test, and the maintainer ruled (its OQ-05, carrier `3l0dmi`) that the reconciliation be tracked here.
- Scope: IN: (1) replace the ladder's two hand-listed literal status tuples (and its success tuple and `interrupted` test) with ONE declared, total table mapping every runner terminal status token to the outcome class it contributes, preserving every currently rendered word byte-for-byte; (2) record, beside that table, each legacy alias whose word DELIBERATELY differs from its canonical token's word, each with its reason and citation; (3) a behavioral test module that renders every token through the real function and asserts the declared words, that the table covers `runner_shared.TERMINAL_STATES`, and that every alias either agrees with its canonical token or is a declared divergence; (4) two backlog items for the two adjacent defects found while measuring that this plan deliberately does not fix. OUT: changing any rendered word (see OQ-01), the run exit code, the per-row Status cell, the diagnostics block, `run_dashboard._outcome`, and any writer of a status token.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_outcome_word_ladder.py, .aw/records/backlog/open/
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: 3l0dmi
- Set: 3l0dmi
- Order: 1
- Highest E allocated: 05
- Author: agent
- Id: 064awu
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Re-measured F-02 at HEAD 04ba026c0 (24 tokens, 10 aliases, words reproduce), F-04/F-05 citations, scanner Total flagged sites: 0 (1 exempt).

- 2026-10-12 draft (agent): created.
- 2026-10-12 to-review (agent): authored from backlog `3l0dmi` (plan production turn); all findings measured against HEAD `b1b2fab2b`; OQ-01 resolved from repository evidence with the reasoning recorded for maintainer review.

## Goal

Make the outcome-word ladder's treatment of every status spelling a DECLARED decision rather than an accident of which literals were typed into which `elif` arm, so the canonical `fail-gate` and its legacy aliases agree wherever they should and differ only where a recorded reason says they must, and so the next token added to the vocabulary cannot silently fall through to `PARTIAL`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the declared table and the ladder that reads it

- [x] E-01 Add a module-level constant `RUN_OUTCOME_CLASS_BY_STATUS: Mapping[str, str]` to `agent_workflows/render_stream.py`, beside `STRANDED_OUTCOME` / `NO_WORK_OUTCOME`, mapping EVERY token in `runner_shared.TERMINAL_STATES` (the 24 tokens listed in Findings F-02) to exactly one class string among five module constants defined with it: `OUTCOME_CLASS_SUCCESS`, `OUTCOME_CLASS_FAILED`, `OUTCOME_CLASS_BLOCKED`, `OUTCOME_CLASS_INTERRUPTED`, `OUTCOME_CLASS_NONE` (none = contributes no class, so the item reaches only the `PARTIAL`/`QUEUED` tail as today). The assignment MUST reproduce today's ladder exactly: success = `executed`, `reviewed`, `approved`, `substantially-complete`; failed = `failed`, `failed-safely`, `fail-lane`, `fail-verify`, `fail-merge`, `integration-blocked`, `merge-conflict`, `merge-needs-human`, `merge-refused`; blocked = `blocked`, `dependency-blocked`, `fail-gate`, `fail-begin`, `fail-depend`, `not-run`; interrupted = `interrupted`; none = `partial`, `not-attempted`, `retired`, `already-landed`. Define it with literal strings in this module, NOT by importing `runner_shared` at module level: `runner_shared` imports `render_stream` at module level, so a module-level reverse import cycles (the reason `INTEGRATION_EARNED_SIGNALS` is a mirrored copy and the reason `render_run_summary_table` imports `canonical_terminal_status` function-locally). Wrap it in `types.MappingProxyType` so it is read-only at runtime.
  - Depends on: none
  - Expected outcome: `python3 -c "import agent_workflows.render_stream as r; print(len(r.RUN_OUTCOME_CLASS_BY_STATUS))"` prints `24` and exits 0 (no import cycle); the table's class for each token equals the Findings F-02 class.
  - Execution state: performed
- [x] E-02 Add, beside the table, `DECLARED_OUTCOME_ALIAS_DIVERGENCES: Mapping[str, str]` mapping each legacy alias whose class DIFFERS from its canonical token's class to a one-line reason that cites the record establishing it. Exactly four entries, from Findings F-03: `failed-safely` (FAILED vs canonical `fail-gate` BLOCKED: the alias is lossy, `failed-safely` meant a nonzero-exit or retry-exhausted turn, and it is STILL WRITTEN today by `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`, `runner_shared.TURN_RETRY_EXHAUSTED_STATUS`, `lane_containment.BOUND_EXPIRY_DISPOSITION` and both hosts' `except DriverError` handlers (`oc_runipd.run_queue`, `agy_runipd.run_queue`: `runnable["status"] = "failed-safely"`), and the comment on `FINALIZE_RETRY_EXHAUSTED_STATUS` chose it because it "is already rendered `FAILED` by the summary"; cite `fr19jr` F-08 and backlog `79d4ix`); `substantially-complete` (success vs BLOCKED: pinned `COMPLETED` by plan `4po0sc`, and its non-landing case is caught by the `refusal_of_item` / `work_did_not_land` guards rather than by the status; cite `zzcrlo`, `ys1dor`, `4po0sc`); `partial` (none vs canonical `fail-verify` FAILED: a historical `partial` meant exit 0 with incomplete work and renders `PARTIAL`; cite `qvfd4l` OQ-03, which made the same raw-first call for `run_dashboard._outcome`); `not-attempted` (none vs canonical `not-run` BLOCKED: pinned `QUEUED` by plan `4po0sc`'s E-02 placement shapes; note spec `uonrjg` 7.2 puts BOTH spellings in stage `abandoned`, so this divergence rests on `4po0sc`, not on the spec). Add a comment block above both constants stating the RULE in prose: a legacy alias is classified by what its spelling MEANT when it was written, because `TERMINAL_STATUS_ALIASES` is lossy (three distinct historical meanings fold into `fail-gate`) and a run summary must be reproducible from the run's own record without re-labelling history; the canonical `fail-gate` is `BLOCKED` per OQ-01.
  - Depends on: E-01
  - Expected outcome: `DECLARED_OUTCOME_ALIAS_DIVERGENCES` has exactly the four keys `failed-safely`, `substantially-complete`, `partial`, `not-attempted`, each with a non-empty reason naming at least one id6.
  - Execution state: performed
- [x] E-03 Rewrite the four status tests of the outcome-word ladder inside `render_stream.render_run_summary_table` (the `interrupted` arm, the `FAILED` arm, the `BLOCKED` arm, and the two success-tuple membership tests in the `COMPLETED` and `NO WORK PERFORMED` arms) to read `RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))` against the class constants instead of literal tuples. Preserve the arm ORDER and every non-status guard exactly as they are (`exit_reason` first, `total_items > 0`, `refusal_of_item`, `work_did_not_land`, `queue_performed_no_work`, and the placement comments explaining why each guard sits where it does). A status absent from the table (an unknown future token) must behave as today's literal tuples do for an unknown token, which is class none. Do NOT touch the progress-count canonicalization, the per-row Status cell, the outcome COLOR selection, or the diagnostics block.
  - Depends on: E-01
  - Expected outcome: For every token in `runner_shared.TERMINAL_STATES`, with and without one attempt and with and without a recorded refusal, the rendered `Outcome:` word is IDENTICAL before and after the change; the existing suites `tests/test_zero_dispatch_outcome.py` and `tests/test_run_summary_table.py` pass unmodified.
  - Execution state: performed

### Task group 2: the behavioral guard

- [x] E-04 Create `tests/test_outcome_word_ladder.py` exercising the REAL `render_stream.render_run_summary_table` on synthesized one-item `state` dicts (same shape as `tests/test_zero_dispatch_outcome.py`'s `_item`/`_state` helpers, rebuilt locally rather than imported from another test module) and parsing the `Outcome:` word from the plain rendered text. Four test cases: (a) WORD TABLE: for every token in `runner_shared.TERMINAL_STATES`, at zero attempts (`attempts=[]`) and at one attempt (`attempts=[{"number": 1}]`; `attempts` is a LIST, an int raises `TypeError` in the renderer), each without and with a recorded refusal (`render_stream.record_refusal`), the rendered word equals a literal expected-word table written in the test (from Findings F-02: four words per token; note `reviewed` at zero attempts is `NO WORK PERFORMED` without a refusal and `QUEUED` with one, and every success-class token renders `PARTIAL` once a refusal is recorded); (b) TOTALITY: `set(runner_shared.TERMINAL_STATES) <= set(render_stream.RUN_OUTCOME_CLASS_BY_STATUS)`, so a token added to the vocabulary without a declared class fails here instead of silently rendering `PARTIAL`; (c) ALIAS AGREEMENT: for every `(legacy, canonical)` in `runner_shared.TERMINAL_STATUS_ALIASES`, the rendered word for `legacy` equals the rendered word for `canonical` UNLESS `legacy` is a key of `render_stream.DECLARED_OUTCOME_ALIAS_DIVERGENCES`, and every key of that mapping is a real alias whose word DOES differ (so a stale divergence entry fails too); (d) CANONICAL FAIL-GATE: a `fail-gate` item renders `BLOCKED` with and without a recorded refusal and with and without attempts, beside `failed-safely` rendering `FAILED`, so OQ-01's decision is asserted directly. Do NOT read production source text, `inspect`, or `ast` (GUIDING_PRINCIPLES P16); cases (b) and (c) read production DATA constants, the precedent being `runner_shared.INTENTIONALLY_UNMAPPED_DRIVER_STATUSES`, kept "beside the table as production data so totality tests read the production decision".
  - Depends on: E-02, E-03
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_outcome_word_ladder.py -q` reports all cases passed; mutating the table (moving `fail-gate` to the failed class) turns cases (a), (c) and (d) red; deleting one divergence entry turns case (c) red; adding a token to a local copy of the vocabulary absent from the table turns case (b) red.
  - Execution state: performed

### Task group 3: hand-off of the adjacent defects

- [x] E-05 File two backlog items with `aw backlog new --apply` (never hand-written), both `--work-kind followup --priority low`, each body citing this plan `064awu` and the measurement: (i) "Discriminate a live `fail-gate` written for a nonzero-exit turn from one written for a gate refusal in the run summary outcome word" (Findings F-05: since `cyamvi`, `reconcile_disposition`'s nonzero-exit fallback and its executed-claim-not-moved branch write `fail-gate` where they wrote `failed-safely` / `substantially-complete`, so such a run now reads `BLOCKED` where it read `FAILED` / `COMPLETED`); (ii) "Give the BLOCKED outcome word its own color instead of the cyan else-branch" (Findings F-06). Do not set `--blocks-release`: neither is filed `bug` (see F-05 and F-06 for the severity reasoning).
  - Depends on: none
  - Expected outcome: two new files under `.aw/records/backlog/open/`, both reported conforming by `aw backlog check`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `render_stream` imports no first-party module that imports it back; `runner_shared` imports `render_stream` at module level, so `render_stream` mirrors constants it needs (`INTEGRATION_EARNED_SIGNALS`, `MALFORMED_ENTRY_TOKEN`) and imports `runner_shared.canonical_terminal_status` function-locally inside `render_run_summary_table`. E-01 follows the mirrored-copy pattern and E-04's case (b) is the cross-check that keeps the copy from going stale, exactly as `test_run_summary_table.py` cross-checks `INTEGRATION_EARNED_SIGNALS`.
- The ladder's arm ORDER is load-bearing and is documented inline (`zzcrlo`, `ys1dor`, `b7oicl`/`4po0sc` comments: "Placement last is load-bearing"). E-03 changes only how a status is classified, never the order.
- Legacy run-status tokens are read-forever because a run directory is a durable record (`runner_shared.LEGACY_INTEGRATION_STATUS_ALIASES` docstring; spec `25kzda` 2026-09-25 amendment). Raw-first classification of a lossy alias is established precedent: `run_dashboard._outcome` carries `aw: dead-status-token-exempt qvfd4l Raw token must be checked before canonicalization`.
- `tools/dead_status_token_scan.py` (from `fr19jr`) scans `if`/`elif` chains for legacy literals lacking their canonical twin and runs as a CI step; HEAD reports `Total flagged sites: 0 (1 exempt)`. After E-03 the ladder holds no status literals, so it cannot regress that count.
- Tests assert behavior by driving the real function (GUIDING_PRINCIPLES P16); suite runs bare as `python3 -m pytest`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The ladder classifies statuses with four hand-typed literal sets in one function: the `interrupted` equality, the `FAILED` tuple (`"failed", "failed-safely", "fail-lane", "fail-verify", "fail-merge", "integration-blocked", "merge-conflict", "merge-needs-human", "merge-refused"`), the `BLOCKED` tuple (`"blocked", "dependency-blocked", "fail-gate", "fail-begin", "fail-depend", "not-run"`), and the success tuple `("executed", "reviewed", "approved", "substantially-complete")` repeated in two arms. Tokens in none of them (`partial`, `not-attempted`, `retired`, `already-landed`) fall to `PARTIAL`/`QUEUED` with no statement that this is intended. | Read `render_stream.render_run_summary_table` at HEAD `b1b2fab2b`, block beginning `# Outcome label`. |
| F-02 | Measured words, every token in `runner_shared.TERMINAL_STATES`, one-item queue, no refusal, `[attempts=[], attempts=[{"number": 1}]]`: `already-landed` PARTIAL/PARTIAL; `approved` COMPLETED/COMPLETED; `blocked` BLOCKED/BLOCKED; `dependency-blocked` BLOCKED/BLOCKED; `executed` COMPLETED/COMPLETED; `fail-begin` BLOCKED/BLOCKED; `fail-depend` BLOCKED/BLOCKED; `fail-gate` BLOCKED/BLOCKED; `fail-lane` FAILED/FAILED; `fail-merge` FAILED/FAILED; `fail-verify` FAILED/FAILED; `failed` FAILED/FAILED; `failed-safely` FAILED/FAILED; `integration-blocked` FAILED/FAILED; `interrupted` INTERRUPTED/INTERRUPTED; `merge-conflict` FAILED/FAILED; `merge-needs-human` FAILED/FAILED; `merge-refused` FAILED/FAILED; `not-attempted` QUEUED/QUEUED; `not-run` BLOCKED/BLOCKED; `partial` PARTIAL/PARTIAL; `retired` PARTIAL/PARTIAL; `reviewed` NO WORK PERFORMED/COMPLETED; `substantially-complete` COMPLETED/COMPLETED. A recorded refusal changes EVERY success-class token and nothing else: `executed`, `approved`, `substantially-complete` COMPLETED -> PARTIAL at both attempt counts; `reviewed` NO WORK PERFORMED -> QUEUED at zero attempts and COMPLETED -> PARTIAL at one; all other tokens, including `fail-gate`, `blocked`, `failed-safely`, are unchanged by it (re-measured at review, HEAD `04ba026c0`). | `python3` driving `render_stream.render_run_summary_table(_state([_item(status=st, attempts=a)]), pal=render_stream.Palette(False))` for `a in ([], [{"number": 1}])` with the `tests/test_zero_dispatch_outcome.py` helpers, for `st in sorted(runner_shared.TERMINAL_STATES)`; refusal via `render_stream.record_refusal(item, code="x", reason="y", remedy="z")`. |
| F-03 | Of the ten `TERMINAL_STATUS_ALIASES` pairs, SIX agree (`blocked`/`fail-gate` BLOCKED; `dependency-blocked`/`fail-depend` BLOCKED; `integration-blocked`, `merge-conflict`, `merge-needs-human`, `merge-refused` / `fail-merge` FAILED) and FOUR disagree: `failed-safely` FAILED vs `fail-gate` BLOCKED; `substantially-complete` COMPLETED vs `fail-gate` BLOCKED; `partial` PARTIAL vs `fail-verify` FAILED; `not-attempted` QUEUED vs `not-run` BLOCKED. The backlog item names only the `fail-gate` family; the other two disagreements are the same shape and are in scope for the same reason. | F-02's table joined with `runner_shared.TERMINAL_STATUS_ALIASES` (read at HEAD, `canonical_terminal_status`). |
| F-04 | The canonical `fail-gate` word is PINNED `BLOCKED` by two shipped behavioral tests and agrees with the normative stage table. `tests/test_zero_dispatch_outcome.py::ZeroDispatchOutcomeRegressionFenceTests::test_regression_blocked_and_fail_gate_status_renders_blocked` (plan `4po0sc`, row "11. Blocked item (fail-gate) \| BLOCKED") and `test_review_relabel_fence_failure_and_blocked_statuses_retain_words` (`"fail-gate": "BLOCKED"`, `"failed-safely": "FAILED"`). Spec `uonrjg` Section 7.2 "Runner item outcomes" maps `fail-gate` to stage `blocked` and `failed-safely` to stage `failed`, and `lifecycle_style._RUNNER_ITEM_PAIRS` implements it (`("fail-gate", BLOCKED)`, `("failed-safely", FAILED)`). So the current ladder already AGREES with the spec on both `fail-gate` and `failed-safely`; that divergence is a property of the lossy alias, not a ladder bug. LIMIT, measured at review: the outcome word is a RUN-level verdict with its own vocabulary and is NOT a 1:1 projection of the 7.2 stage, so agreement holds for this pair only. 7.2 puts `fail-lane`, `fail-merge`, `merge-needs-human`, `merge-refused` in `blocked` (ladder: FAILED), `not-run` and `not-attempted` both in `abandoned` (ladder: BLOCKED / QUEUED), and `partial` / `substantially-complete` in `recovering`. Those differences are pre-existing, outside this plan's word-preserving scope, and are not cited as spec support for any divergence. | Read both tests and the 7.2 table row `` `fail-gate`, `fail-begin`, `fail-lane`, ... \| blocked `` and `` `fail-verify`, `failed`, `failed-safely` \| failed ``. |
| F-05 | The LIVE `fail-gate` token has several producers with different meanings, and two of them inherited it from tokens that rendered differently. Gate refusals awaiting a human write `fail-gate` (`clean_base_refusal`, `scope_target_refused`, host-capability preflight, agent proposal with `NEEDS_INPUT_KEY`) and read naturally as BLOCKED. But `runner_shared.reconcile_disposition` also returns `"fail-gate"` for a nonzero exit (`return ("fail-verify" if exit_code == 0 else "fail-gate"), outcome`) and `outcome_precedence_disposition` returns it for an agent claiming `executed` without the plan reaching `executed/`; before `cyamvi` (commit `6b94a4d9d`) those returned `failed-safely` and `substantially-complete`. So a crashed turn renders `BLOCKED` today where it rendered `FAILED` before the rename. Discriminating them needs a recorded field (exit code, refusal code), not a token change, so it is a separate design and is filed by E-05 rather than fixed here. SEVERITY: the word is still a non-success word, the exit code (`runner_stop.deliberate_stop_exit_code` via `item_reached_success`) is unaffected, and the diagnostics block names the item, so it does not meet the user-perceptible-impact test for `bug`. | `git show 6b94a4d9d -- agent_workflows/runner_shared.py`: `-    return ("partial" if exit_code == 0 else "failed-safely"), outcome` / `+    return ("fail-verify" if exit_code == 0 else "fail-gate"), outcome`, and `-            return "substantially-complete"` / `+            return "fail-gate"`. Producers read in `runner_shared.execute_item_core`. |
| F-06 | The `BLOCKED` outcome word renders CYAN, the color-selection's else-branch, because no branch names it; the code's own `ys1dor` E-02 comment warns that "an unhandled outcome word looks deliberate while being wrong". Spec `uonrjg` gives stage `blocked` orange 208. Out of scope here (this plan does not touch color); filed by E-05. | `render_stream.render_run_summary_table(..., pal=render_stream.Palette(True))`: `fail-gate` -> SGR `36` `BLOCKED`; `failed-safely` -> SGR `31` `FAILED`; `partial` -> SGR `33` `PARTIAL`. |
| F-07 | No contention: no OTHER pending plan declares `agent_workflows/render_stream.py` or the new test path in `- Scope-Paths:`. | `rg -l "^- Scope-Paths:.*(render_stream|test_outcome_word_ladder)" .aw/records/plans/pending/` prints only this plan (re-run at review, HEAD `04ba026c0`). |

## Proposed changes (ordered, validatable)

1. E-01: the total, read-only status-to-class table in `render_stream`, reproducing F-02.
2. E-02: the four declared alias divergences from F-03, each with its reason and citation, plus the prose rule.
3. E-03: the ladder reads the table; arm order and every non-status guard untouched; words byte-identical.
4. E-04: `tests/test_outcome_word_ladder.py`, the word table, totality, alias-agreement and canonical-`fail-gate` cases.
5. E-05: backlog items for F-05 and F-06.

## Deferred / out of scope (with reason)

- Changing any rendered word, including making canonical `fail-gate` read `FAILED`:
  - Carrier-Declined: rejected by OQ-01 (contradicts spec `uonrjg` 7.2 and two shipped tests, and would relabel every gate refusal).
- Discriminating a nonzero-exit `fail-gate` from a gate-refusal `fail-gate` (F-05):
  - Carrier: 1h98o3
- `BLOCKED`'s cyan color (F-06):
  - Carrier: pyezbc
- Migrating the live `failed-safely` writers:
  - Carrier: 79d4ix
- `run_dashboard._outcome` and `run_viewer` filters:
  - Carrier-Declined: separate surfaces with their own recorded decisions (`qvfd4l` OQ-03).

## Scope check

- Over-scope: none. `render_stream.py` is touched only at two new constants and the ladder's status tests; the new test module is the guard; `.aw/records/backlog/open/` is declared only for E-05's two filings.
- Under-scope: none. Every alias pair (F-03) and every terminal token (F-02) is covered by E-01/E-02 and asserted by E-04; the two adjacent defects have carriers via E-05.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_outcome_word_ladder.py -q` passes, plus the mutation runs E-04 names.
- `tests/test_zero_dispatch_outcome.py`, `tests/test_run_summary_table.py`, `tests/test_dead_status_token_scan.py`, `tests/test_terminal_status_vocabulary.py` pass UNMODIFIED.
- `python3 -c "import agent_workflows.render_stream"` exits 0 (no cycle).
- `python3 tools/dead_status_token_scan.py` still reports `Total flagged sites: 0`.
- Full suite run bare: `python3 -m pytest`.

## Spec / documentation sync

N/A, checked rather than assumed. No `.spec.md` is in `- Scope-Paths:` because no contract changes: spec `uonrjg` Section 7.2 already classifies `fail-gate` as `blocked` and `failed-safely` as `failed`, and this plan makes the outcome ladder's agreement with it explicit without moving any token; spec `25kzda` does not enumerate outcome words; and every rendered word is byte-identical, so no user-facing doc or `CHANGELOG.md` entry describes a change.

## Open questions

### OQ-01: Which word should a canonical `fail-gate` item render, and should its legacy aliases be forced to agree with it?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: canonical `fail-gate` stays `BLOCKED`, and the legacy aliases keep their historical words as DECLARED divergences rather than being canonicalized. Options weighed: (a) move `fail-gate` to `FAILED` (what `fr19jr` E-05 proposed); (b) canonicalize every alias first so `failed-safely`/`substantially-complete` become `BLOCKED`; (c) keep the words and declare the divergences. (a) is refused on evidence: spec `uonrjg` 7.2 is normative and puts `fail-gate` in `blocked` (and `failed-safely` in `failed`; F-04 records that this pairwise agreement is the only spec support claimed, since the outcome word is not a 1:1 projection of the stage), two shipped tests pin `BLOCKED` (F-04), and the majority of live producers are gate refusals awaiting a human (F-05), which `FAILED` would mislabel. (b) is refused because `TERMINAL_STATUS_ALIASES` is lossy (three historical meanings fold into `fail-gate`), because it would re-label already-recorded runs (`ys1dor`'s "a run summary is a statement about what THAT RUN DID" rule), because `failed-safely` is still WRITTEN today by retry-exhausted and driver-error paths whose comments promise it renders `FAILED` (F-05, `79d4ix`), and because it flips `4po0sc`'s pinned `substantially-complete` -> `COMPLETED` and `not-attempted` -> `QUEUED`. (c) changes no output, keeps the `fail-gate`/`failed-safely` agreement with the spec, and converts an accident into a reviewed table that a test enforces. The residual genuine defect (a live nonzero-exit `fail-gate` reading `BLOCKED`) is a producer-discrimination problem and is carried by E-05. Human review requested: if the maintainer prefers (a) or (b), only E-01's class assignments and E-04's expected-word table change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the actual output of `python3 -c "import agent_workflows.render_stream as r, agent_workflows.runner_shared as s; print(len(r.RUN_OUTCOME_CLASS_BY_STATUS)); print(sorted(set(s.TERMINAL_STATES) - set(r.RUN_OUTCOME_CLASS_BY_STATUS))); print(sorted(r.RUN_OUTCOME_CLASS_BY_STATUS.items()))"`, which must print `24`, `[]`, and a mapping whose classes equal Findings F-02; and paste the `git diff` hunk adding the table, showing it is a `MappingProxyType` and imports nothing from `runner_shared` at module level.
  - Observed evidence:
    Actual command output:
    ```
    24
    []
    [('already-landed', 'none'), ('approved', 'success'), ('blocked', 'blocked'), ('dependency-blocked', 'blocked'), ('executed', 'success'), ('fail-begin', 'blocked'), ('fail-depend', 'blocked'), ('fail-gate', 'blocked'), ('fail-lane', 'failed'), ('fail-merge', 'failed'), ('fail-verify', 'failed'), ('failed', 'failed'), ('failed-safely', 'failed'), ('integration-blocked', 'failed'), ('interrupted', 'interrupted'), ('merge-conflict', 'failed'), ('merge-needs-human', 'failed'), ('merge-refused', 'failed'), ('not-attempted', 'none'), ('not-run', 'blocked'), ('partial', 'none'), ('retired', 'none'), ('reviewed', 'success'), ('substantially-complete', 'success')]
    ```
    Git diff hunk showing MappingProxyType and standard library types import:
    ```diff
    @@ -34,6 +34,7 @@ import signal
     import sys
     import threading
     import time
    +import types
     from collections.abc import Mapping, Sequence
     from dataclasses import dataclass
     from pathlib import Path
    @@ -3025,6 +3026,88 @@ MALFORMED_ENTRY_TOKEN = "malformed-entry"
     #: Placeholder marker in summary table cells for fields that could not be read from a non-mapping queue entry.
     UNREADABLE_MARKER = "(unreadable)"

    +#: Outcome classes used by :func:`render_run_summary_table`'s outcome-word ladder.
    +OUTCOME_CLASS_SUCCESS: str = "success"
    +OUTCOME_CLASS_FAILED: str = "failed"
    +OUTCOME_CLASS_BLOCKED: str = "blocked"
    +OUTCOME_CLASS_INTERRUPTED: str = "interrupted"
    +OUTCOME_CLASS_NONE: str = "none"
    +
    +# --------------------------------------------------------------------------------------------------
    +# Outcome-word ladder status classification (IPD 064awu)
    +#
    +# RULE: A legacy alias is classified by what its spelling MEANT when it was written,
    +# because TERMINAL_STATUS_ALIASES is lossy (three distinct historical meanings fold
    +# into fail-gate) and a run summary must be reproducible from the run's own record
    +# without re-labelling history; the canonical fail-gate is BLOCKED per OQ-01.
    +# --------------------------------------------------------------------------------------------------
    +
    +#: Total mapping of every terminal runner status token in runner_shared.TERMINAL_STATES
    +#: to exactly one outcome class. Defined with literal strings here rather than importing
    +#: runner_shared at module level to avoid an import cycle (runner_shared imports render_stream
    +#: at module level).
    +RUN_OUTCOME_CLASS_BY_STATUS: Mapping[str, str] = types.MappingProxyType(
    +    {
    +        # Success class: executed, reviewed, approved, substantially-complete
    +        "executed": OUTCOME_CLASS_SUCCESS,
    +        "reviewed": OUTCOME_CLASS_SUCCESS,
    +        "approved": OUTCOME_CLASS_SUCCESS,
    +        "substantially-complete": OUTCOME_CLASS_SUCCESS,
    +        # Failed class: failed, failed-safely, fail-lane, fail-verify, fail-merge,
    +        # integration-blocked, merge-conflict, merge-needs-human, merge-refused
    +        "failed": OUTCOME_CLASS_FAILED,
    +        "failed-safely": OUTCOME_CLASS_FAILED,
    +        "fail-lane": OUTCOME_CLASS_FAILED,
    +        "fail-verify": OUTCOME_CLASS_FAILED,
    +        "fail-merge": OUTCOME_CLASS_FAILED,
    +        "integration-blocked": OUTCOME_CLASS_FAILED,
    +        "merge-conflict": OUTCOME_CLASS_FAILED,
    +        "merge-needs-human": OUTCOME_CLASS_FAILED,
    +        "merge-refused": OUTCOME_CLASS_FAILED,
    +        # Blocked class: blocked, dependency-blocked, fail-gate, fail-begin, fail-depend, not-run
    +        "blocked": OUTCOME_CLASS_BLOCKED,
    +        "dependency-blocked": OUTCOME_CLASS_BLOCKED,
    +        "fail-gate": OUTCOME_CLASS_BLOCKED,
    +        "fail-begin": OUTCOME_CLASS_BLOCKED,
    +        "fail-depend": OUTCOME_CLASS_BLOCKED,
    +        "not-run": OUTCOME_CLASS_BLOCKED,
    +        # Interrupted class: interrupted
    +        "interrupted": OUTCOME_CLASS_INTERRUPTED,
    +        # None class (contributes no class, reaches PARTIAL/QUEUED tail):
    +        # partial, not-attempted, retired, already-landed
    +        "partial": OUTCOME_CLASS_NONE,
    +        "not-attempted": OUTCOME_CLASS_NONE,
    +        "retired": OUTCOME_CLASS_NONE,
    +        "already-landed": OUTCOME_CLASS_NONE,
    +    }
    +)
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste the actual output of `python3 -c "import agent_workflows.render_stream as r; [print(k, '->', v) for k, v in sorted(r.DECLARED_OUTCOME_ALIAS_DIVERGENCES.items())]"`, which must list exactly `failed-safely`, `not-attempted`, `partial`, `substantially-complete`, each reason naming at least one id6; and paste the comment block stating the rule.
  - Observed evidence:
    Actual command output:
    ```
    failed-safely -> FAILED vs canonical fail-gate BLOCKED: the alias is lossy, failed-safely meant a nonzero-exit or retry-exhausted turn, and it is still written today by retry and error handlers (cite fr19jr F-08 and backlog 79d4ix)
    not-attempted -> none vs canonical not-run BLOCKED: pinned QUEUED by plan 4po0sc's E-02 placement shapes (note spec uonrjg 7.2 puts both spellings in stage abandoned, so this divergence rests on 4po0sc, not on the spec)
    partial -> none vs canonical fail-verify FAILED: a historical partial meant exit 0 with incomplete work and renders PARTIAL (cite qvfd4l OQ-03 raw-first precedent)
    substantially-complete -> success vs canonical fail-gate BLOCKED: pinned COMPLETED by plan 4po0sc, and its non-landing case is caught by the refusal_of_item / work_did_not_land guards rather than by the status (cite zzcrlo, ys1dor, 4po0sc)
    ```
    Comment block stating the rule:
    ```python
    # --------------------------------------------------------------------------------------------------
    # Outcome-word ladder status classification (IPD 064awu)
    #
    # RULE: A legacy alias is classified by what its spelling MEANT when it was written,
    # because TERMINAL_STATUS_ALIASES is lossy (three distinct historical meanings fold
    # into fail-gate) and a run summary must be reproducible from the run's own record
    # without re-labelling history; the canonical fail-gate is BLOCKED per OQ-01.
    # --------------------------------------------------------------------------------------------------
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste a BEFORE/AFTER word table produced by one script run twice, once against the pre-change base commit (via a temporary `git worktree add` of the base, never `git stash`) and once against the post-change tree, rendering every `runner_shared.TERMINAL_STATES` token at `attempts=[]` and `attempts=[{"number": 1}]`, with and without `record_refusal` (96 words); run each time with `PYTHONPATH=<that tree>` and `AW_NO_REEXEC=1`, and paste the script's first output line printing `agent_workflows.__file__` for BOTH runs showing two DIFFERENT trees (measured at review: a script run from outside the tree without `PYTHONPATH` imports the editable-installed main-checkout package, so both runs would measure the same code and the diff would be trivially empty); the two tables must be identical line for line (a `diff` of the two outputs printing nothing is sufficient evidence if the diff command and its empty output are pasted). Also paste the `git diff` of the ladder showing arm order and the `exit_reason`, `total_items > 0`, `refusal_of_item`, `work_did_not_land`, `queue_performed_no_work` guards unchanged, and the actual `python3 -m pytest -o addopts="" tests/test_zero_dispatch_outcome.py tests/test_run_summary_table.py -q` summary line with those files unmodified (`git diff --stat` on them empty).
  - Observed evidence:
    Base tree first output line:
    ```
    /tmp/wt-064awu-base/agent_workflows/__init__.py
    ```
    Post-change tree first output line:
    ```
    .aw/worktrees/064awu/agent_workflows/__init__.py
    ```
    Diff of 96 outcome words:
    ```
    $ diff <(tail -n +2 /tmp/words_base.txt) <(tail -n +2 /tmp/words_post.txt)
    ```
    (empty output, exit code 0)

    Ladder git diff showing arm order and guards preserved:
    ```diff
    @@ -3881,45 +3964,31 @@ def render_run_summary_table(
         if exit_reason:
             outcome_str = exit_reason
         elif any(
    -        isinstance(it, Mapping) and it.get("status") == "interrupted" for it in queue
    +        isinstance(it, Mapping)
    +        and RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))
    +        == OUTCOME_CLASS_INTERRUPTED
    +        for it in queue
         ):
             outcome_str = "INTERRUPTED"
         elif any(
             isinstance(it, Mapping)
    -        and it.get("status")
    -        in (
    -            "failed",
    -            "failed-safely",
    -            "fail-lane",
    -            "fail-verify",
    -            "fail-merge",
    -            "integration-blocked",
    -            "merge-conflict",
    -            "merge-needs-human",
    -            "merge-refused",
    -        )
    +        and RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))
    +        == OUTCOME_CLASS_FAILED
             for it in queue
         ):
             outcome_str = "FAILED"
         elif any(
             isinstance(it, Mapping)
    -        and it.get("status")
    -        in (
    -            "blocked",
    -            "dependency-blocked",
    -            "fail-gate",
    -            "fail-begin",
    -            "fail-depend",
    -            "not-run",
    -        )
    +        and RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))
    +        == OUTCOME_CLASS_BLOCKED
             for it in queue
         ):
             outcome_str = "BLOCKED"
         elif (
             all(
                 isinstance(it, Mapping)
    -            and it.get("status")
    -            in ("executed", "reviewed", "approved", "substantially-complete")
    +            and RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))
    +            == OUTCOME_CLASS_SUCCESS
                 for it in queue
             )
             and total_items > 0
    @@ -3971,8 +4040,8 @@ def render_run_summary_table(
         elif (
             all(
                 isinstance(it, Mapping)
    -            and it.get("status")
    -            in ("executed", "reviewed", "approved", "substantially-complete")
    +            and RUN_OUTCOME_CLASS_BY_STATUS.get(it.get("status"))
    +            == OUTCOME_CLASS_SUCCESS
                 for it in queue
             )
             and total_items > 0
    ```

    `git diff --stat tests/test_zero_dispatch_outcome.py tests/test_run_summary_table.py` is empty (unmodified).
    Actual test summary:
    ```
    ...............................                                          [100%]
    31 passed in 2.42s
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the actual `python3 -m pytest -o addopts="" tests/test_outcome_word_ladder.py -q` output with its `N passed` line; then paste the three MUTATION runs, each a red run followed by revert: (1) `fail-gate` moved to the failed class -> cases (a), (c), (d) fail; (2) the `partial` divergence entry deleted -> case (c) fails; (3) one token removed from `RUN_OUTCOME_CLASS_BY_STATUS` -> case (b) fails. Paste `git diff --stat` after reverting showing only the intended changes remain. Paste `rg -n "^\s*(import|from) (inspect|ast)\b|read_text\(|getsource" tests/test_outcome_word_ladder.py` returning nothing (no production-source reading; the pattern is anchored so a docstring mentioning the word does not false-positive).
  - Observed evidence:
    Passing test run:
    ```
    ....                                                                     [100%]
    4 passed in 0.59s
    ```

    Mutation 1: `fail-gate` moved to failed class:
    ```
    FAILED tests/test_outcome_word_ladder.py::OutcomeWordLadderBehavioralFenceTests::test_case_c_alias_agreement
    FAILED tests/test_outcome_word_ladder.py::OutcomeWordLadderBehavioralFenceTests::test_case_a_word_table
    FAILED tests/test_outcome_word_ladder.py::OutcomeWordLadderBehavioralFenceTests::test_case_d_canonical_fail_gate
    3 failed, 1 passed in 0.27s
    ```

    Mutation 2: `partial` divergence entry deleted:
    ```
    FAILED tests/test_outcome_word_ladder.py::OutcomeWordLadderBehavioralFenceTests::test_case_c_alias_agreement
    1 failed, 3 passed in 0.31s
    ```

    Mutation 3: `not-attempted` removed from `RUN_OUTCOME_CLASS_BY_STATUS`:
    ```
    FAILED tests/test_outcome_word_ladder.py::OutcomeWordLadderBehavioralFenceTests::test_case_b_totality
    1 failed, 3 passed in 0.86s
    ```

    `git diff --stat` after reverting mutations:
    ```
     agent_workflows/render_stream.py | 121 ++++++++++++++++++++++++++++++---------
     1 file changed, 95 insertions(+), 26 deletions(-)
    ```

    Source inspection pattern check:
    ```
    $ rg -n "^\s*(import|from) (inspect|ast)\b|read_text\(|getsource" tests/test_outcome_word_ladder.py
    (empty output, exit code 1)
    ```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste the two `aw backlog new ... --apply` invocations and their output naming the written files, the first ten lines of each file showing `- Work-Kind: followup`, no `- Blocks-Release:`, and a body citing `064awu`; and paste `aw backlog check` reporting conforming.
  - Observed evidence:
    Invocations and outputs:
    ```
    $ aw backlog new --work-kind followup --priority low --summary "Discriminate a live fail-gate written for a nonzero-exit turn from one written for a gate refusal in the run summary outcome word" --body "..." --apply
    aw backlog new: wrote .aw/records/backlog/open/20261012-1h98o3-01-1h98o3-discriminate-a-live-fail-gate-written-for-a-nonzer.backlog.md

    $ aw backlog new --work-kind followup --priority low --summary "Give the BLOCKED outcome word its own color instead of the cyan else-branch" --body "..." --apply
    aw backlog new: wrote .aw/records/backlog/open/20261012-pyezbc-01-pyezbc-give-the-blocked-outcome-word-its-own-color-instea.backlog.md
    ```

    First ten lines of `.aw/records/backlog/open/20261012-1h98o3-01-1h98o3-discriminate-a-live-fail-gate-written-for-a-nonzer.backlog.md`:
    ```markdown
    - Id: 1h98o3
    - Status: open
    - Set: 1h98o3
    - Priority: low
    - Work-Kind: followup
    - Summary: Discriminate a live fail-gate written for a nonzero-exit turn from one written for a gate refusal in the run summary outcome word

    ## Workflow history
    - 2026-10-13 created (aw backlog): Discriminate a live fail-gate written for a nonzero-exit turn from one written for a gate refusal in the run summary outcome word
    ```

    First ten lines of `.aw/records/backlog/open/20261012-pyezbc-01-pyezbc-give-the-blocked-outcome-word-its-own-color-instea.backlog.md`:
    ```markdown
    - Id: pyezbc
    - Status: open
    - Set: pyezbc
    - Priority: low
    - Work-Kind: followup
    - Summary: Give the BLOCKED outcome word its own color instead of the cyan else-branch

    ## Workflow history
    - 2026-10-13 created (aw backlog): Give the BLOCKED outcome word its own color instead of the cyan else-branch
    ```

    `aw backlog check`:
    ```
    aw backlog check: all backlog items conform. 988 backlog items checked.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the paths in `- Scope-Paths:`, through `aw commit 064awu -- <paths>`, never `git add -A` and never a push. Paste ACTUAL runner output for every claim of a passing test. Before the final validation, also run the full suite BARE as `python3 -m pytest` and paste its summary line, and run `python3 tools/dead_status_token_scan.py` and paste its `Total flagged sites:` line.

ONE THING THIS PLAN MUST NOT DO: change a rendered outcome word. If, while executing, a token's word differs before and after E-03, that is a FAILED V-03 to be fixed in E-03, never reconciled by editing E-04's expected table or an existing test. Changing a word is OQ-01's decision and requires the maintainer to reopen it.

POST-GATE LIFECYCLE. On completion every `E-*` must read `performed` and every `V-*` `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` must report conforming; only then does the plan move to `.aw/records/plans/executed/` through the tooled transition (under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; a human-driven execution runs `aw ipd finalize 064awu --actor <agent/model> --message <summary> --apply`). Backlog item `3l0dmi` is advanced by the runner's backlog-close step, never by hand.
