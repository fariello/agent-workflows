# IPD: Pin the RUN-* abort partition to the spec action text instead of a hand-maintained comment tally

- Date: 2026-09-29
- Kind: child
- Concern: The `RUN-*` abort tri-state partition in `agent_workflows/run_evidence.py` is documented by a hand-written sentence and enforced by nothing, so it has now drifted four times while the neighbouring code-count invariant, which IS enforced, stayed correct.
- Scope: Replace the hand-maintained abort tally in `run_evidence.py` with a computed derivation plus a behavioral test that pins each row's `abort` tri-state to the row's own verbatim spec action text, and restore behavioral coverage for the abort invariants whose only tests were deleted by the suite trim.
- Scope-Paths: agent_workflows/run_evidence.py, tests/test_run_finding_abort_partition.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: dorm45
- Set: dorm45
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: xjmjq4

## Workflow history

- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `dorm45`. Re-measured the partition at this HEAD and found the comment had rotted a THIRD time since the item was filed (it reads 2/5/5, the table holds 2/4/6), and found the backlog's "three tests" premise is no longer true: the enforcing test file was deleted by the suite trim. Both corrections are recorded in Findings rather than folded silently into the item's framing.

## Goal

Make the `RUN-*` abort partition self-evidently correct instead of asserted: derive each row's `abort` tri-state from the row's own verbatim spec-4.2 action string in a test, so a future edit that changes a row's action or tri-state without the other fails loudly, and replace the prose tally with a pointer to that enforcement. This closes backlog `dorm45`'s generalizable concern, that an unenforced hand count rotted silently next to an enforced one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the partition to the spec action text

- [ ] E-01 Add a module-level derivation helper to `agent_workflows/run_evidence.py` that computes a row's abort tri-state from its verbatim `action` string alone: split the action on `;`, select the segments containing `ABORT RUN`, return `ABORT_NEVER` when there are none, `ABORT_ALWAYS` when any such segment is exactly `ABORT RUN`, and `ABORT_CONDITIONAL` otherwise (a qualified `ABORT RUN only for ...` / `ABORT RUN for ...`). Document that the stored `abort` field stays the readable index and this helper is the cross-check, so the spec text remains the single authority.
  - Depends on: none
  - Expected outcome: A public helper (for example `derive_abort_from_action`) exists in `run_evidence.py` and returns the stored tri-state for all 12 rows; no existing symbol's behavior changes.
  - Execution state: pending

- [ ] E-02 Extend `validate_finding_table` with a new finding code (for example `RC-ABORT-DERIVATION`) that fails any row whose stored `abort` disagrees with `derive_abort_from_action(row.action)`, naming the code, the stored value, and the derived value. Place it beside the existing `RC-COUNT` / abort-tri-state checks so the table keeps reporting its own invalidity at runtime, which is the property the spec's Section 4.2 transcription note already relies on for the code count.
  - Depends on: E-01
  - Expected outcome: `validate_finding_table()` still returns a passing result on the shipped table, and returns a finding naming the offending code when a row's stored tri-state is perturbed away from its action text.
  - Execution state: pending

- [ ] E-03 Replace the hand-maintained tally in the `# ---- abort semantics (spec 25kzda 4.1)` comment with prose that states the RULE (how the tri-state follows from the action text) and names the enforcing symbols, carrying NO per-state count. Keep the existing paragraph's load-bearing reasoning (why the action matters as much as the message, and why collapsing the tri-state into a boolean is the error it prevents) and keep its recorded drift history, appending this occurrence. Apply the same treatment to `may_abort_run`'s docstring, which carries its own independent copy of the same count ("five of the 12 codes").
  - Depends on: E-02
  - Expected outcome: No count of always/conditional/never rows survives anywhere in `run_evidence.py`; both sites point at the enforcement instead, and the prior drift record is preserved rather than overwritten.
  - Execution state: pending

### Task group 2: restore the deleted behavioral coverage

- [ ] E-04 Add `tests/test_run_finding_abort_partition.py` covering the abort invariants by OUTCOME: (a) every row's stored `abort` equals the value derived from its own verbatim action text; (b) `may_abort_run` is true for exactly the `always` and `conditional` rows and false for every `never` row; (c) a conditional row is never reported as unconditional, and every aborting row names at least one member of `ABORT_CLASSES` while every never-aborting row names none; (d) `validate_finding_table` returns the `RC-ABORT-DERIVATION` finding when a row is perturbed (built with `_replace` on the NamedTuple and patched into the table, restored afterwards), proving the gate actually fires rather than passing vacuously. Assert on returned values and findings only; do not read module source with `inspect`, `ast`, regex, or substring search, and do not assert on comment text or symbol censuses.
  - Depends on: E-03
  - Expected outcome: A new test module passes, and its perturbation case fails the table when the stored tri-state and the action text disagree.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The abort tri-state is stored per row on `run_evidence.RunFindingCode` (fields `abort` and `abort_classes`) and is described in its docstring as "derived tri-state over `action` ... an INDEX over the verbatim string, not a new policy". That self-description is precisely what makes a mechanical derivation legitimate rather than an invention: this plan enforces a relationship the module already claims.
- The module already demonstrates the pattern this plan extends: `validate_finding_table` hard-fails `len(RUN_FINDING_CODES) != 12` with finding code `RC-COUNT`, and spec `25kzda` Section 4.2 records that invariant as contractual ("THE TABLE'S CODE COUNT IS ITSELF PART OF THE CONTRACT"). The abort partition gets the same treatment, so the fix matches an established in-repo convention.
- Spec `25kzda` Section 4.1 closes with "No other FINDING may abort the whole queue" and enumerates six abort classes, transcribed verbatim into `run_evidence.ABORT_CLASSES`. Section 4.2's table supplies each row's Action cell, which is the string the derivation reads.
- `AGENTS.md` forbids code-pinning tests (GUIDING_PRINCIPLES P16): tests must exercise code and assert on real outputs, never read production source with `inspect`/`ast`/regex or assert that comment text is unchanged. E-04 is written to respect this, which also rules out the tempting shortcut of testing the comment's wording directly.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
| --- | --- | --- | --- |
| F1 | The comment has drifted AGAIN since backlog `dorm45` was filed. It now reads "two of the 12 codes abort UNCONDITIONALLY; five abort ONLY under a named 4.1 class; five never abort", but the shipped table holds `Counter({'never': 6, 'conditional': 4, 'always': 2})`. Measured at this HEAD by importing `run_evidence` and counting `row.abort` over `RUN_FINDING_CODES`. | Quoted comment string "two of the 12 codes abort UNCONDITIONALLY" in `run_evidence.py`; measured counter output reproduced in V-03. | Confirms the item's thesis empirically and raises the drift count to four events. A one-off recount would rot a fifth time, so E-01..E-03 remove the count rather than correct it. |
| F2 | The drift was introduced by commit `544ba188` ("work(jdn790): Refuse the whole run at freeze time on an undetermined action..."), whose only `run_evidence.py` change flipped one row from `abort=ABORT_CONDITIONAL, abort_classes=("Identity or type ambiguity",)` to `abort=ABORT_NEVER, abort_classes=()`. That row is `RUN-STRUCTURE-PREFLIGHT`, whose action is `REFUSE RUN at freeze before any session`, so the NEW value is correct and only the prose is wrong. | `git show 544ba188 -- agent_workflows/run_evidence.py` shows exactly that four-line change and no comment edit. | The defect is the unenforced prose, not the table. The plan must not "fix" the table; it must make a change like `544ba188` impossible to land silently. E-02's gate would have failed that commit. |
| F3 | The backlog item's premise that the neighbouring counts are enforced by "validate_finding_table's RC-COUNT plus three tests" is now only HALF true. `RC-COUNT` still ships, but the tests are GONE: `tests/test_run_evidence_completion.py` (85 test methods, including `test_abort_tristate_agrees_with_the_specs_action_text`, `test_conditional_abort_is_not_reported_as_unconditional`, `test_no_code_aborts_outside_the_six_enumerated_classes`, and `test_spec_defines_exactly_twelve_run_codes`) was deleted by commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). No test in the tree references `RUN_FINDING_CODES`, `validate_finding_table`, or `may_abort_run` today. | `git show 19313eed --stat -- tests/` lists `tests/test_run_evidence_completion.py | 1722 ---------`; `grep -rln` for those symbols under `tests/` returns nothing; `git show 19313eed^:tests/test_run_evidence_completion.py` still contains the named methods. | The fix is larger than a comment edit: a test asserting the action/tri-state agreement once EXISTED and was removed. E-04 restores that coverage in a dedicated module, so this plan closes a real coverage hole rather than only tidying prose. |
| F4 | The derivation is mechanically sound on the shipped data. Deriving the tri-state from the action text alone (segments containing `ABORT RUN`; bare `ABORT RUN` means always, qualified means conditional, absent means never) reproduces the stored value for all 12 rows with zero mismatches. Verified by scripted comparison against `row.abort`. | Scripted derivation output, all 12 rows `OK`, reproduced in V-01. | E-01's rule is not speculative: the cross-check passes on arrival, so E-02 can be a hard failure rather than a warning without needing any row's data changed. |
| F5 | The count is duplicated at a SECOND site that the item does not mention: `may_abort_run`'s docstring independently asserts "spec 4.1 licenses five of the 12 codes to abort only under a named abort class". Five is wrong by the same measurement as F1 (four are conditional). | Quoted docstring string "licenses five of the 12 codes" in `run_evidence.py`; same counter as F1. | Fixing only the comment block would leave an equally wrong count in a docstring that operators and callers read. E-03 covers both sites, which is why it names them explicitly. |

## Proposed changes (ordered, validatable)

1. Add the derivation helper to `run_evidence.py` (E-01). Pure function over the `action` string, no dependency on the stored field, so it is a genuine cross-check and not a tautology.
2. Gate the table on it inside `validate_finding_table` under a new `RC-*` finding code (E-02), matching how `RC-COUNT` gates the row count.
3. Rewrite both count-bearing prose sites to state the rule and name the enforcer, preserving the existing reasoning and drift history and appending this occurrence (E-03).
4. Add behavioral tests for the partition, including a perturbation case that proves the new gate fires (E-04).

## Deferred / out of scope (with reason)

- Binding any `RUN-*` code to a live consumer. The module states plainly that no live run emits these codes yet (deferred by `wlxkoz` OQ-01). This plan is about keeping the vocabulary honest, not wiring it.
  - Carrier-Declined: This is an upstream design deferral owned by `wlxkoz` OQ-01 and recorded in the module itself ("NO CONSUMER YET, STATED PLAINLY"), not an obligation this plan creates. Nothing about pinning the abort partition makes the binding more or less due.
- Restoring the other coverage lost with `tests/test_run_evidence_completion.py`. That file held 85 test methods across completion evaluation, verbatim message transcription, and binding states; only the abort-partition subset is in scope here, because that is what backlog `dorm45` concerns. This is a REAL outstanding obligation, not a dismissal, so it is handed to the existing carriers rather than declined (see Open questions OQ-01).
  - Carrier: xvp5vx, 089bq4
- Amending spec `25kzda`. Section 4.1 and the Section 4.2 table are the authority this plan derives FROM and it changes no contract, so no `.spec.md` file is touched and none is declared in `- Scope-Paths:`.
  - Carrier-Declined: Nothing is outstanding: this plan changes no contract the spec states, so there is no amendment owed. The separate, genuine defect that Section 4.2 cites a DELETED test as its byte-equality guard is already owned by backlog `089bq4`, which is carried on the coverage row above.
- Refactoring the `EV-*` taxonomy into the same convention. Explicitly out of scope for `wlxkoz` and untouched here.
  - Carrier-Declined: A pre-existing scope boundary declared by `wlxkoz` ("It does NOT refactor `EV-*` into it (out of scope for `wlxkoz`)"), not work this plan defers. The `EV-*` codes are referenced only as bindings and are neither renamed nor touched.

## Scope check

- Over-scope: none. The two declared paths are the module carrying the defect and the new test file that pins it.
- Under-scope: the abort partition only. The code-count invariant already has `RC-COUNT` and needs nothing; the binding-state and message-transcription invariants lost their tests in the same deletion (F3) and are deliberately left to a separate item, so this plan does not restore all 85 deleted methods.

## Required tests / validation

- `python3 -m pytest tests/test_run_finding_abort_partition.py` for the new module, run bare so the configured `addopts` apply.
- `python3 -m pytest` (bare, full fast suite) to prove the `run_evidence.py` changes regress nothing, with the `N passed` summary line pasted.
- A scripted re-measurement of the partition and the derivation agreement, output pasted, so the numbers in Findings are reproducible at execution time rather than trusted from authoring time.
- A perturbation check proving `validate_finding_table` reports the new finding when a row's stored tri-state disagrees with its action text, which is what distinguishes a live gate from a vacuous pass.

## Spec / documentation sync

N/A for spec files: this plan derives from spec `25kzda` Sections 4.1 and 4.2 and changes no contract, adds no code, and removes no row, so no `.spec.md` is edited and none is declared in `- Scope-Paths:`. The new `RC-ABORT-DERIVATION` code is an INTERNAL table-validation finding (a sibling of the existing `RC-COUNT`, `RC-DUPLICATE`, `RC-NAME`), not a member of Section 4.2's public `RUN-*` operator vocabulary, so Section 4.2's twelve-code contract and its `RC-COUNT` note are both untouched. Documentation sync is confined to the two in-module prose sites named in E-03.

## Open questions

### OQ-01: Should the rest of the coverage deleted with `tests/test_run_evidence_completion.py` be restored, and by whom?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved from repository evidence, not deferred to the human, and it needs no NEW backlog item because two open items already own it. F3 establishes that commit `19313eed` deleted 85 test methods covering completion evaluation, verbatim message transcription, and binding states in addition to the abort partition. This plan restores only the abort-partition subset, because that is backlog `dorm45`'s concern and because silently absorbing the other 80-odd methods would be an unreviewable scope expansion. The remainder is handed to the existing carriers named on the Deferred row: `xvp5vx` ("audit what properties lost their only guard in the 19313eed suite trim", the general audit, which explicitly directs that only genuine behavioral outcomes be triaged and that code-pinning tests never be restored) and `089bq4` ("Spec 25kzda 4.2 claims tests/test_run_evidence_completion.py enforces byte equality ... but that file was deleted", which owns the message-transcription half specifically). Both were read at authoring time and both are `open`. Nothing in this plan depends on either being done first, so this question does not block execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the output of a script that imports `run_evidence`, calls the new derivation helper on every row's `action`, and prints `code`, stored `abort`, and derived value for all 12 rows plus a final agreement boolean. Every row must read OK and the boolean must be True. Must show 12 rows, since a helper that silently returned the stored field would also print OK, so also paste a call of the helper on a literal action string (for example `"FAIL ITEM after containment; ABORT RUN only for ownership conflict"` returning `conditional` and `"ABORT RUN"` returning `always`) to prove it reads the text and not the field.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste output showing `validate_finding_table()` reports no findings on the shipped table, THEN paste output from a perturbation run where one row's stored `abort` is replaced (via `NamedTuple._replace`) with a value contradicting its action text and `validate_finding_table()` returns a finding whose code is the new `RC-ABORT-DERIVATION` and whose message names the offending code plus both values. A passing-only run is insufficient evidence: it cannot distinguish a live gate from one that never fires.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste a `grep -n` over `agent_workflows/run_evidence.py` for the count words (`two of the`, `five`, `eight`, `three never`, `of the 12`) showing that no per-state tally of always/conditional/never rows remains at either the abort-semantics comment or `may_abort_run`'s docstring, together with the replacement prose for both sites quoted in full. Also paste the measured `Counter` over `row.abort` for the record, and confirm by quotation that the pre-existing drift history (the "counts moved twice" record) is still present with this occurrence appended, since preserving it is part of the required outcome.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the actual bare `python3 -m pytest tests/test_run_finding_abort_partition.py` output showing every test passing, and the actual bare `python3 -m pytest` summary line (`N passed`) for the full fast suite. Also confirm by quotation from the new test file that no test reads production source via `inspect`, `ast`, regex, or substring search over module text, and that each test asserts on returned values or findings, per GUIDING_PRINCIPLES P16.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; do not execute it from this status. On approval, execute it under the standard contract: commit only the two paths declared in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A` and never push, and paste real runner output for every test claim rather than asserting success. Do not mark any `V-*` item complete without the concrete evidence its Required-evidence block demands; V-02 and V-04 in particular are written so that a passing run alone does not satisfy them. On completion, run `aw ipd lint --phase pre-transition` and move the plan to `.aw/records/plans/executed/` only once it conforms and every `V-*` item reads `pass` with observed evidence. Backlog `dorm45` is set `graduated` by the runner on verification; do not set it `done` here, since the code is not written until this plan executes.
