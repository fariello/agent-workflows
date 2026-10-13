# IPD: Reconcile the runner's live failed-safely writers with spec 25kzda's legacy-token claim

- Date: 2026-10-11
- Kind: child
- Concern: Spec `25kzda`'s 2026-09-25 statusvocab amendment (and the identical note copied into seven sibling specs) says legacy terminal tokens, `failed-safely` among them, "are no longer written by the runner". That is false at HEAD: six live in-domain producers write `failed-safely`, and the spec's OWN normative Section 5.5 retry-mapping table names `failed-safely` as the disposition of three retryable host-failure classes. The spec therefore contradicts itself, and a future reader that trusts the amendment note and handles only canonical tokens would silently miss these records.
- Scope: Choose option (b) of backlog `79d4ix` (keep the writers, correct the contract), on repository evidence recorded in OQ-01. IN: add a normative paragraph to spec `25kzda` Section 5.5 stating that `failed-safely` is a LIVE runner-written token for contained host/driver failures and naming why it is not migrated; append a dated correction note through `aw specs note` to `25kzda` and to the seven sibling specs carrying the same false sentence; add a clarifying comment at `runner_shared.TERMINAL_STATUS_ALIASES`; add one behavioral test module that drives each live producer and asserts the token it writes plus the downstream behavior that depends on that spelling. OUT: migrating any writer to `fail-gate` (option a, rejected in OQ-01); changing `TERMINAL_STATUS_ALIASES`, `TERMINAL_STATES_CANONICAL`, `TURN_RETRY_CLASSIFICATION`, `runner_shutdown.KNOWN_ITEM_STATUSES` or any `--retry-incomplete` set; touching the retry predicate (owned by approved plan `ytas91`); rewriting any existing `## Workflow history` line.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md, .aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md, .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, .aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md, .aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md, .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, .aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md, agent_workflows/runner_shared.py, tests/test_failed_safely_live_writers.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 79d4ix
- From-Spec: 25kzda
- Set: 79d4ix
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: o58r3r

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: o58r3r verified (set 79d4ix, attempt 1).
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (5.5 `fix-it budget exhausted` row names an unwritten token; agent-recorded `failed-safely` canonicalization stated; E-05 cells demonstrated and made token-following; per-path specs check; OQ-01 owner corrected)
- 2026-10-12 reviewed (aw set): plan-review revisions applied (PR-001..PR-004)
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog `79d4ix`. Census re-measured at HEAD `b3a449ea6` (see F-01..F-03); option (b) selected from repository evidence (OQ-01), subject to maintainer confirmation at review/approval.

## Goal

Make spec `25kzda` (and the seven specs that copied its note) tell the truth about which terminal token the runner writes for a contained host or driver failure, and pin that spelling and the behavior that depends on it with an outcome test, so the spec and the code cannot drift apart again silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure

- [x] E-01 Re-measure the write-site census at execution HEAD, since the tree may have moved (approved plan `ytas91` touches the same producers). Run `rg -n '(\["status"\]|\["disposition"\]|"status":|"disposition":|_STATUS: str|_DISPOSITION) *=? *"failed-safely"' agent_workflows --type py` and the runtime probe `AW_NO_REEXEC=1 python3 -c "from agent_workflows import runner_shared as r, lane_containment as l, runner_shutdown as s; print(r.FINALIZE_RETRY_EXHAUSTED_STATUS, r.TURN_RETRY_EXHAUSTED_STATUS, l.BOUND_EXPIRY_DISPOSITION, 'failed-safely' in r.TERMINAL_STATES_CANONICAL, r.canonical_terminal_status('failed-safely'), sorted(r.TURN_RETRYABLE_DISPOSITIONS), 'failed-safely' in s.KNOWN_ITEM_STATUSES)"`. If the census differs from F-01 (a producer added or removed), the E-02 paragraph names the producers actually found, by symbol.
  - Depends on: none
  - Expected outcome: a census listing each live producer by symbol, and the probe output; any difference from F-01 is recorded in the plan's Findings as a dated addendum before E-02 runs.
  - Execution state: performed

### Task group 2: correct the contract

- [x] E-02 In spec `25kzda` Section 5.5, immediately after the retry-mapping table (the table whose first rows read "host spawn failure | `failed-safely`"), add a normative paragraph headed `Live legacy-spelled token: failed-safely` stating: (1) the runner STILL WRITES `failed-safely` for contained host/driver failures, naming the producers from E-01 by symbol (`oc_runipd.run_queue` and `agy_runipd.run_queue` `except DriverError` arms, `runner_shared.refuse_undispatchable_typed_entry`, `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`, `runner_shared.TURN_RETRY_EXHAUSTED_STATUS`, `lane_containment.BOUND_EXPIRY_DISPOSITION`), plus the agent outcome-schema literal in `runner_shared.build_prompt`, stating that an AGENT-RECORDED `failed-safely` is a self-claim that `runner_shared.outcome_precedence_disposition` canonicalizes to `fail-gate` (non-retryable) by design, so the raw-token rule in (3) governs RUNNER-written tokens (review PR-002); (2) it is NOT migrated to `fail-gate` because `fail-gate` is the non-retryable gate-refusal class in this same table, so a migration would silently move host failures out of the retryable class (the reason is F-04); (3) `TERMINAL_STATUS_ALIASES` maps it to `fail-gate` for DISPLAY and cross-generation grouping only, and a reader that decides RETRYABILITY or OWNERSHIP MUST key on the raw token (or on the failure-kind marker approved plan `ytas91` introduces), never on `canonical_terminal_status`; (4) the 2026-09-25 history note's "no longer written by the runner" does not apply to `failed-safely`; (5) an item whose turn or finalize correction budget is EXHAUSTED is written `failed-safely` (`TURN_RETRY_EXHAUSTED_STATUS` / `FINALIZE_RETRY_EXHAUSTED_STATUS`, with a `turn-retry` or finalize refusal record), and is NOT re-classified as retryable because `turn_failure_is_retryable` runs only at the end of a dispatched turn, while `--retry-incomplete` remains the operator's manual route. In the SAME table, change only the Disposition cell of the `fix-it budget exhausted` row from `` `fail-gate`, `budget_exhausted` `` to `` `failed-safely` (with its refusal record) ``: measured at review, no producer writes `budget_exhausted` and both exhaustion constants write `failed-safely` (review PR-001). Edit no other line of the spec.
  - Depends on: E-01
  - Expected outcome: `git diff` of the spec shows one added paragraph inside Section 5.5 and the one changed Disposition cell of the `fix-it budget exhausted` row, and no other body change; `aw specs check <spec>` conforms.
  - Execution state: performed

- [x] E-03 Append a dated correction note to spec `25kzda` and to each of the seven sibling specs carrying the identical sentence (the other seven paths in `- Scope-Paths:`) using `AW_NO_REEXEC=1 python3 -m agent_workflows specs note <path> --message "CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'."`. Do NOT edit the 2026-09-25 line itself: history is append-only. Re-run `rg -l "no longer written by the runner" .aw/records/specs` first and add a note to any additional spec it finds (declaring the path at finalize with `--scope-reason`).
  - Depends on: E-02
  - Expected outcome: each of the eight specs gains exactly one appended `note (aw specs)` line naming `o58r3r`; `git diff` shows no deleted line in any of them.
  - Execution state: performed

- [x] E-04 Add a comment block directly above `runner_shared.TERMINAL_STATUS_ALIASES` stating that `failed-safely` is a LIVE writer token (not only a historical spelling), that its alias to `fail-gate` is for display/grouping, and that retry or ownership decisions must not canonicalize it first, citing spec `25kzda` 5.5. No executable line changes.
  - Depends on: E-02
  - Expected outcome: `git diff agent_workflows/runner_shared.py` shows only added `#` comment lines.
  - Execution state: performed

### Task group 3: pin the behavior

- [x] E-05 Add `tests/test_failed_safely_live_writers.py` that EXERCISES each producer and asserts on its output, with no source introspection: (a) on BOTH hosts, `run_queue` with `execute_item` patched to raise `runner_shared.DriverError` leaves the item `failed-safely` with `driver_error` set and `run_queue` RETURNS without raising (measured at review: returns `1` on both hosts) (shape after `tests/test_typed_queue_entries.py::...test_item_local_refusal_on_both_hosts`); (b) `refuse_undispatchable_typed_entry` on a backlog item with action `review` returns True, writes `failed-safely`, and appends an `item-refused` event carrying `failed-safely`; (c) `lane_containment.bound_expiry_record(...)["disposition"] == "failed-safely"`; (d) `handle_turn_failure_retry` with a frozen budget of 0 and disposition `failed-safely` writes `failed-safely` to the item (the exhausted arm); (e) for the token OBSERVED in (a) (read from the ledger, never a literal, so the cell follows a migration), `turn_failure_is_retryable({}, token)` is `(True, ...)` while `turn_failure_is_retryable({}, canonical_terminal_status(token))` is False, which is the hazard the spec paragraph warns about; (f) a ledger whose queue item holds that token is coherent under `runner_shutdown.observe_ledger`; (g) on both hosts `run_queue(run_dir, retry_incomplete=True)` requeues an item in that state (patched `execute_item` records it was dispatched). The finalize-exhausted arm is already driven by `tests/test_finalize_sendback.py` (it asserts `FINALIZE_RETRY_EXHAUSTED_STATUS` is the returned disposition); (h) assert that value, and the statuses observed in (b), (c) and (d), each equal the token observed in (a), so the producers cannot fork apart. Every cell (a), (b), (c), (d), (f), (g) was driven once at review against HEAD with the real functions and produced the asserted outcome (see F-08).
  - Depends on: E-04
  - Expected outcome: the new module passes under `python3 -m pytest -o addopts="" tests/test_failed_safely_live_writers.py`; each sub-case fails if its producer is migrated to a different spelling.
  - Execution state: performed

### Task group 4: whole-tree checks

- [x] E-06 Run the bare suite `python3 -m pytest`, `AW_NO_REEXEC=1 python3 -m agent_workflows specs check <path> --agent` once for EACH touched spec path (the whole-tree form can report unrelated specs), and `AW_NO_REEXEC=1 python3 -m agent_workflows check release-gates --agent`; paste each.
  - Depends on: E-05
  - Expected outcome: the suite's `N passed` line with no new failure attributable to this plan; `specs check` conforming for all eight touched specs; release gates with no finding naming this plan or `79d4ix`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A plan that changes behavior a spec describes carries the spec amendment in the same change and lists the `.spec.md` in `- Scope-Paths:` (`AGENTS.md`, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT").
- Spec `## Workflow history` is append-only; corrections are new `aw specs note` lines (`aw specs note --help`: "Append a workflow-history record ... Use to log a decision, review, or correction").
- Tests assert outcomes, never source structure (`AGENTS.md` NO CODE-PINNING TESTS; GUIDING_PRINCIPLES P16).
- Run the suite bare (`AGENTS.md` repository development contract); use `AW_NO_REEXEC=1` so the in-tree package is the one measured.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Six live in-domain producers write `failed-safely` at HEAD `b3a449ea6`, matching the backlog's census. | `rg` census: `oc_runipd.run_queue` (`runnable["status"] = "failed-safely"`), `agy_runipd.run_queue` (same), `runner_shared.refuse_undispatchable_typed_entry` (`item["status"] = "failed-safely"` and its `item-refused` event), `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS` (assigned in `handle_finalize_refusal`), `runner_shared.TURN_RETRY_EXHAUSTED_STATUS` (assigned in `handle_turn_failure_retry`), `lane_containment.BOUND_EXPIRY_DISPOSITION` (returned by `bound_expiry_record`). No other legacy terminal token has a live writer (per-token `rg` count was 0 for all others; the one `dependency-blocked` hit is a comment). |
| F-02 | Runtime probe confirms the contradiction. | `failed-safely failed-safely failed-safely` / `False fail-gate ['failed-safely'] True`: the three constants resolve to `failed-safely`; it is not canonical; it canonicalizes to `fail-gate`; it is the ONLY member of `TURN_RETRYABLE_DISPOSITIONS`; it is in `KNOWN_ITEM_STATUSES`. |
| F-03 | The spec contradicts itself: its own normative 5.5 table still names `failed-safely` as a written disposition. | `25kzda` 5.5 rows "host spawn failure \| `failed-safely`", "nonzero exit or no outcome file \| `failed-safely`", "stall or turn-limit expiry \| `failed-safely`, `timeout`", versus the 2026-09-25 history note "are no longer written by the runner". The same note is copied verbatim into seven other specs (`rg -l "no longer written by the runner" .aw/records/specs`). |
| F-04 | Option (a), migrating the writers to `fail-gate`, would change retry behavior in the unsafe-for-progress direction. | `turn_failure_is_retryable({}, 'failed-safely')` -> `(True, "...retryable host-failure class")`; `turn_failure_is_retryable({}, 'fail-gate')` -> `(False, "...lifecycle gate or clean-base gate refused...")`. Backlog `vmrhj0` and superseded plan `p47qfu` measured the same and rejected simply admitting `fail-gate` as unsafe, because gate refusals also write it. |
| F-05 | Approved pending plan `ytas91` (fixfirst-04) keeps and extends `failed-safely` as the written spawn-failure disposition. | `ytas91` E-02: "set disposition `failed-safely`"; its E-06 expected outcome: "the item ends `failed-safely` with a recorded reason". Migrating the writers here would contradict an approved plan's contract. |
| F-06 | The agent-facing outcome schema also offers `failed-safely`. | `runner_shared.build_prompt` literal `"disposition": "executed\|substantially-complete\|partial\|blocked\|failed-safely"`; out of this plan's scope (agent-written, not runner-written), but named in the spec paragraph for completeness. |
| F-07 | The two `suffix="merge-conflict"` sites are prompt filename suffixes, not statuses. | `runner_shared` `write_prompt(... suffix="merge-conflict")` (two sites); excluded, as the backlog predicted. |
| F-08 | Review demonstration at HEAD `b41952ca2` (no file changed): the E-05 cells are reachable with the real functions. | `run_queue` with patched `execute_item` raising `DriverError`: `oc rv 1 failed-safely boom (True, '1 item(s), all in a defined state')`, same on agy; `run_queue(rd, True)` then dispatched `['pln001']` on both hosts; `handle_turn_failure_retry` at frozen budget 0 -> `failed-safely failed-safely turn-retry`, at budget 2 -> `queued`; `bound_expiry_record(...)["disposition"] == 'failed-safely'`; `outcome_precedence_disposition(None, {'disposition': 'failed-safely'})` -> `fail-gate`. |
| F-09 | The 5.5 table's `fix-it budget exhausted` row names a token no producer writes. | Row: "fix-it budget exhausted \| `fail-gate`, `budget_exhausted`"; `rg budget_exhausted agent_workflows` finds no producer; `TURN_RETRY_EXHAUSTED_STATUS` and `FINALIZE_RETRY_EXHAUSTED_STATUS` both resolve `failed-safely` (F-02). |

## Proposed changes (ordered, validatable)

1. Re-measure the census and probe (E-01).
2. Add the normative `failed-safely` paragraph to `25kzda` 5.5 (E-02).
3. Append correction notes to all eight specs carrying the false sentence (E-03).
4. Comment `TERMINAL_STATUS_ALIASES` (E-04).
5. Add the behavioral test module (E-05).
6. Run the suite, `specs check` and release gates (E-06).

## Deferred / out of scope (with reason)

- Migrating writers to `fail-gate` (option a): rejected on F-04/F-05; reconsider only after the retry decision keys on a failure-kind marker rather than on the token.
  - Carrier: ytas91
- Removing the `failed-safely` offer from the agent outcome schema (F-06): agent-facing contract, not a runner writer.
  - Carrier-Declined: not owed; the spec paragraph documents it and no reader defect is measured.

## Scope check

- Over-scope: none. Eight spec files (E-02 body paragraph in `25kzda` only; E-03 one appended history line each); `agent_workflows/runner_shared.py` comment lines only (E-04); one new test module (E-05).
- Under-scope: none. The seven sibling specs are included because they carry the identical false sentence; leaving them would leave the contradiction live in seven places.

## Required tests / validation

- New module `tests/test_failed_safely_live_writers.py` (E-05), driven through the real `run_queue`, `refuse_undispatchable_typed_entry`, `bound_expiry_record`, `handle_turn_failure_retry`, `turn_failure_is_retryable` and `runner_shutdown.observe_ledger`.
- Bare suite `python3 -m pytest`, `aw specs check`, and `aw check release-gates` (E-06).

## Spec / documentation sync

Spec `25kzda` Section 5.5 is AMENDED (E-02) and eight specs receive a correction note (E-03), all declared in `- Scope-Paths:`. WHY: the 2026-09-25 note asserts a writer property the code does not have, and 5.5's own table already relies on `failed-safely` being written; the amendment makes the normative text agree with both the shipped code and approved plan `ytas91`, and states the canonicalization hazard that `vmrhj0`/`p47qfu` measured so no future reader canonicalizes before deciding retryability. No user-facing docs change.

## Open questions

### OQ-01: Option (a) migrate the writers, or option (b) correct the spec?

- Blocking: no
- Status: resolved
- Owner: plan author (the maintainer confirms or overturns at approval)
- Resolution or deferral rationale: RESOLVED to option (b) from repository evidence, since this turn has no live human channel and the evidence is decisive: (1) spec `25kzda`'s own normative 5.5 table names `failed-safely` as the written disposition for three retryable classes (F-03), so the false clause is the history note, not the table; (2) migrating to `fail-gate` moves host failures into the non-retryable gate-refusal class (F-04), the exact unsafe change `vmrhj0`/`p47qfu` rejected; (3) approved plan `ytas91` writes `failed-safely` by contract (F-05). The backlog flagged this as a public-contract question for the maintainer; approving this plan is that confirmation, and a maintainer who prefers (a) should send this plan back rather than approve it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `rg` census output and the runtime probe output verbatim, and state whether they match F-01/F-02 (and the addendum if not).
  - Observed evidence:
```
rg -n '(\["status"\]|\["disposition"\]|"status":|"disposition":|_STATUS: str|_DISPOSITION) *=? *"failed-safely"' agent_workflows --type py
agent_workflows/agy_runipd.py
3571:            runnable["status"] = "failed-safely"

agent_workflows/oc_runipd.py
4262:            runnable["status"] = "failed-safely"

agent_workflows/lane_containment.py
1153:BOUND_EXPIRY_DISPOSITION = "failed-safely"

agent_workflows/runner_shared.py
2542:    item["status"] = "failed-safely"
2551:            "status": "failed-safely",
8243:FINALIZE_RETRY_EXHAUSTED_STATUS: str = "failed-safely"
9077:TURN_RETRY_EXHAUSTED_STATUS: str = "failed-safely"

AW_NO_REEXEC=1 python3 -c "from agent_workflows import runner_shared as r, lane_containment as l, runner_shutdown as s; print(r.FINALIZE_RETRY_EXHAUSTED_STATUS, r.TURN_RETRY_EXHAUSTED_STATUS, l.BOUND_EXPIRY_DISPOSITION, 'failed-safely' in r.TERMINAL_STATES_CANONICAL, r.canonical_terminal_status('failed-safely'), sorted(r.TURN_RETRYABLE_DISPOSITIONS), 'failed-safely' in s.KNOWN_ITEM_STATUSES)"
failed-safely failed-safely failed-safely False fail-gate ['failed-safely'] True
```
Census and probe match F-01 and F-02 exactly; no addendum required.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff -- .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` showing the single added 5.5 paragraph, the one changed `fix-it budget exhausted` Disposition cell, and the E-03 history line, nothing else, and `AW_NO_REEXEC=1 python3 -m agent_workflows specs check <that path>` output.
  - Observed evidence:
```diff
diff --git a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
index aed14da17..717aff5c3 100644
--- a/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
+++ b/.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
@@ -1448,9 +1448,13 @@ The normative mapping between the retry classes above and the runner's dispositi
 | unknown or non-idempotent external outcome | `unknown_outcome` | `turn_failure_is_retryable` | No | Non-idempotent external side effect at unknown state. Item stopped; independent items continue. Shipped. |
 | identity or type ambiguity | `failed` / `type_or_status_not_runnable` | queue builder / dependency preflight | No | Ambiguity in identity or type stops item (or refuses run if preflight). Independent items continue. Shipped. |
 | changed frozen requirements, EXCEPT an additive scope widening as defined in Section 5.5a | `fail-gate` | `turn_failure_is_retryable` / finalize gate | No | Frozen requirement violation (except Section 5.5a accept). Item stopped; independent items continue. Shipped. |
-| fix-it budget exhausted, or a global fix-it cap reached (needs-human) | `fail-gate`, `budget_exhausted` | runner loop / retry controller | No | All allowed fix-it attempts spent without resolution, or a global fix-it cap reached (refusal code `fix-it-cap-reached`, needs-human). Item stopped; independent items continue. Shipped. |
+| fix-it budget exhausted, or a global fix-it cap reached (needs-human) | `failed-safely` (with its refusal record) | runner loop / retry controller | No | All allowed fix-it attempts spent without resolution, or a global fix-it cap reached (refusal code `fix-it-cap-reached`, needs-human). Item stopped; independent items continue. Shipped. |
 | corrupt run ledger only | `fail-gate`, `interrupted` | `turn_failure_is_retryable` / ledger validator | No | Ledger hash/sequence/reference corruption makes all queue state untrustworthy. Aborts run. Shipped. |

+#### Live legacy-spelled token: failed-safely
+
+The runner still writes `failed-safely` for contained host/driver failures by design. Live producers writing this token are the `oc_runipd.run_queue` and `agy_runipd.run_queue` `except DriverError` arms, `runner_shared.refuse_undispatchable_typed_entry`, `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS`, `runner_shared.TURN_RETRY_EXHAUSTED_STATUS`, and `lane_containment.BOUND_EXPIRY_DISPOSITION`, along with the agent outcome-schema literal in `runner_shared.build_prompt`. An agent-recorded `failed-safely` is an agent self-claim that `runner_shared.outcome_precedence_disposition` canonicalizes to `fail-gate` (non-retryable) by design, so the raw-token rule below governs runner-written tokens. The token is not migrated to `fail-gate` because `fail-gate` is the non-retryable gate-refusal class in this same table, so a migration would silently move host failures out of the retryable class. `TERMINAL_STATUS_ALIASES` maps it to `fail-gate` for display and cross-generation grouping only, and a reader that decides retryability or ownership must key on the raw token (or on the failure-kind marker approved plan `ytas91` introduces), never on `canonical_terminal_status`. The 2026-09-25 history note's "no longer written by the runner" does not apply to `failed-safely`. An item whose turn or finalize correction budget is exhausted is written `failed-safely` (`TURN_RETRY_EXHAUSTED_STATUS` / `FINALIZE_RETRY_EXHAUSTED_STATUS`, with a `turn-retry` or finalize refusal record), and is not re-classified as retryable because `turn_failure_is_retryable` runs only at the end of a dispatched turn, while `--retry-incomplete` remains the operator's manual route.
+
 #### 5.5a Additive scope widening is a finalize-time accept, not a retry

 A CHANGED FROZEN REQUIREMENT remains never-retryable. One difference class is carved out of it, because the previous rule punished the honest act and rewarded concealment.
@@ -1727,6 +1731,7 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen

 ## Workflow history

+- 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
 - 2026-10-13 note (aw specs): amendment (c0oysi): Section 5.5 adds global fix-it caps per artifact, per Set and per run (backlog 38hwvk)
 - 2026-10-13 note (aw specs): amended Sections 2.6 and 3.3 for implementing spec re-plan turn (plan 2hgxi1)
 - 2026-10-11 note (aw specs): amendment (opencode its_direct/pt3-claude-opus-5.5-1m-us): Section 5.2 records the maintainer's 2026-10-11 decision to stop host-granular egress filtering (Set netnsfilter) and leave the push-denial host requirement open by decision.
```
```json
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff --stat` over the eight spec paths and `git diff -U0` lines for the seven sibling specs, showing exactly one added `note (aw specs)` line naming `o58r3r` per file and zero removed lines.
  - Observed evidence:
```
git diff --stat -- .aw/records/specs
 ...26-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md | 7 ++++++-
 ...0260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md | 1 +
 .../20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md    | 1 +
 ...ross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md | 1 +
 ...0260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md | 1 +
 ...0260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md | 1 +
 .../20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md      | 1 +
 .../20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md  | 1 +
 8 files changed, 13 insertions(+), 1 deletion(-)
```
```diff
diff --git a/.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md b/.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
index efe900bbd..09db01310 100644
--- a/.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
+++ b/.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
@@ -16,0 +17 @@
+- 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
diff --git a/.aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md b/.aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md
index bcfa369a9..5ae55c0b8 100644
--- a/.aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md
+++ b/.aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md
@@ -11,0 +12 @@
+- 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
diff --git a/.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md b/.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
index 8d95ed9a6..0fdfbf661 100644
--- a/.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
+++ b/.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
@@ -12,0 +13 @@
+- 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
diff --git a/.aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md b/.aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md
index cc70f8d84..e10802303 100644
--- a/.aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md
+++ b/.aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md
@@ -17,0 +18 @@
+- 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
diff --git a/.aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md b/.aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md
index 10bd715f1..c017c3506 100644
--- a/.aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md
+++ b/.aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md
@@ -12,0 +13 @@
+- 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
diff --git a/.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md b/.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
index 820142f7b..5b367a583 100644
--- a/.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
+++ b/.aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
@@ -14,0 +15 @@
+- 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
diff --git a/.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md b/.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
index b8d2ef479..809ff5714 100644
--- a/.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
+++ b/.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
@@ -13,0 +14 @@
+- 2026-10-13 note (aw specs): CORRECTION (79d4ix / o58r3r): the 2026-09-25 statusvocab note's 'no longer written by the runner' does not hold for failed-safely, which the runner still writes for contained host/driver failures by design; see spec 25kzda Section 5.5 'Live legacy-spelled token: failed-safely'.
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff -- agent_workflows/runner_shared.py` showing only added comment lines above `TERMINAL_STATUS_ALIASES`.
  - Observed evidence:
```diff
diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
index 1408264dd..96fe35c0c 100644
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -33491,6 +33491,13 @@ TERMINAL_STATES_CANONICAL: frozenset[str] = frozenset(
 # (the 179 majority out of 209 historical records, since a historical record carries no producer
 # field to re-derive from), while WRITERS pick per producer (`clean_base_refusal` -> `fail-gate`,
 # `begin_refusal` -> `fail-begin`, `worktree_error` -> `fail-lane`, verifier verdicts -> `fail-verify`).
+#
+# NOTE ON LIVE WRITER `failed-safely` (o58r3r / 79d4ix): `failed-safely` is a LIVE runner-written
+# token (not only a historical spelling) produced by host/driver exception handlers, queue refusal,
+# and correction-budget exhaustion. Its alias to `fail-gate` here is for display presentation and
+# cross-generation grouping only. Any logic deciding retryability or ownership MUST NOT canonicalize
+# it first, as canonicalizing to `fail-gate` would misclassify it as a non-retryable gate refusal.
+# See spec 25kzda Section 5.5 ("Live legacy-spelled token: failed-safely").
 TERMINAL_STATUS_ALIASES: dict[str, str] = {
     "substantially-complete": "fail-gate",
     "partial": "fail-verify",
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_failed_safely_live_writers.py` output listing each sub-case (a) to (h) passing on both hosts where applicable; the observed run/dispatch behavior is produced by the real `oc_runipd.run_queue` / `agy_runipd.run_queue`, `refuse_undispatchable_typed_entry` and `handle_turn_failure_retry` called by the test.
  - Observed evidence:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: .
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 8 items

tests/test_failed_safely_live_writers.py::TestFailedSafelyLiveWriters::test_case_c_bound_expiry_record PASSED [ 12%]
tests/test_failed_safely_live_writers.py::TestFailedSafelyLiveWriters::test_case_b_refuse_undispatchable_typed_entry PASSED [ 25%]
tests/test_failed_safely_live_writers.py::TestFailedSafelyLiveWriters::test_case_e_canonical_status_retryability_hazard PASSED [ 37%]
tests/test_failed_safely_live_writers.py::TestFailedSafelyLiveWriters::test_case_h_all_producers_consistent_with_case_a PASSED [ 50%]
tests/test_failed_safely_live_writers.py::TestFailedSafelyLiveWriters::test_case_d_handle_turn_failure_retry_exhausted PASSED [ 62%]
tests/test_failed_safely_live_writers.py::TestFailedSafelyLiveWriters::test_case_f_ledger_coherence_under_observe_ledger PASSED [ 75%]
tests/test_failed_safely_live_writers.py::TestFailedSafelyLiveWriters::test_case_a_run_queue_driver_error_on_both_hosts PASSED [ 87%]
tests/test_failed_safely_live_writers.py::TestFailedSafelyLiveWriters::test_case_g_retry_incomplete_requeues_on_both_hosts PASSED [100%]

============================== 8 passed in 19.51s ==============================
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line, the eight per-path `specs check --agent` outputs, and the `check release-gates --agent` output; name any failing test id and show it is pre-existing or unrelated.
  - Observed evidence:
```
Bare suite summary:
8102 passed, 4 skipped, 18 xfailed, 3 warnings in 1017.26s (0:16:57)
No failing tests (0 failed).

Per-path specs check:
=== .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md ===
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
=== .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md ===
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
=== .aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md ===
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
=== .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md ===
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
=== .aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md ===
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
=== .aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md ===
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
=== .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md ===
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}
=== .aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md ===
{"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1,"findings":0,"evidence":["specs"],"next":null}

Release gates:
{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"release-gates","findings":0,"evidence":["inventory","rules"],"next":"aw releases list"}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval; approving also confirms OQ-01's choice of option (b). Execution contract: commit only this plan's declared paths through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only`, never push; paste actual output into every `V-*`. The scope fence is a declaration, not a stop condition; an out-of-scope edit is justified with `--scope-reason` at finalize. Under `aw oc run` / `aw agy run` the runner performs begin/finalize; by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize`. Never hand-`git mv` the plan.
