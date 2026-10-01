# IPD: Pin the RUN-* abort partition to the spec action text instead of a hand-maintained comment tally

- Date: 2026-09-29
- Kind: child
- Concern: The `RUN-*` abort tri-state partition in `agent_workflows/run_evidence.py` is documented by a hand-written sentence and enforced by nothing, so it has now drifted four times while the neighbouring code-count invariant, which IS enforced, stayed correct.
- Scope: Replace the hand-maintained abort tally in `run_evidence.py` with a computed derivation gated at runtime, plus behavioral tests that pin each row's `abort` tri-state at two levels: to the row's own `action` string (catching a half-edit) AND to spec 4.2's own action cell parsed from the spec file (catching a pair that drifts from the contract together, which the module-only derivation cannot see). Restore the abort-invariant subset of the behavioral coverage deleted by the suite trim, including the spec-anchored byte comparison that subset originally carried.
- Scope-Paths: agent_workflows/run_evidence.py, tests/test_run_finding_abort_partition.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: dorm45
- Set: dorm45
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: xjmjq4

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: xjmjq4 verified (set dorm45, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261001-tf6x3a-01-tf6x3a-mark-fields-and-verbose-end-to-end-check-tests-liv.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-X01 (HIGH, fixed), PR-X02 (HIGH, fixed), PR-X03 (MEDIUM, fixed), PR-X04 (MEDIUM, fixed), PR-X05 (LOW, fixed). Findings recorded in .aw/records/reviews/20260930-dorm45-01-xjmjq4-pin-the-run-abort-partition-to-the-spec-action-text.review.md. Re-measured every authored finding: F1's 2/4/6 counter and both quoted prose strings are verbatim correct, F3's deletion is exact (1722 lines, 85 test methods, all four named methods present at 19313eed^, no current references), F4's derivation reproduces all 12 rows with zero mismatches, and F5's docstring count is wrong by the same measurement. TWO SERIOUS FINDINGS, the same gap from two directions. PR-X01: E-01's helper reads row.action, itself a MODULE field, so E-02's gate is a self-consistency check and not the cross-check Proposed change 1 claims; measured adversarially, rewriting RUN-CROSS-TREE to action='FAIL ITEM' with abort='never' PASSES the gate while contradicting the spec cell it transcribes, and the DELETED test caught that class precisely because it parsed the SPEC FILE, so the plan was rebuilding the weaker half of its own cited precedent. New E-05 restores the spec anchor and I verified it passes on arrival (12 spec rows parsed, ZERO action-text mismatches). PR-X02: F2's claim that E-02's gate would have failed commit 544ba188, the plan's motivating drift event, is FALSE; that commit moved the action in the SAME hunk as the tri-state, so the derivation passes both before (conditional/conditional) and after (never/never) and would have been silent throughout. F2 now records both measurements and the honest division of labour (E-02 catches a half-edit, E-05 a co-moved drift). FURTHER: the spec-amendment Deferred row declared 'nothing is outstanding' while spec 4.2 promises a byte-equality guard from a deleted test, a defect owned by open backlog 089bq4 which is a bug carrying Blocks-Release next and which E-05 partly discharges, so the row now carries that carrier and the gate forbids closing it; OQ-01 carried Owner none, corrected to plan author; and V-01 now states what it does not prove. Verified E-05's spec parse is compatible with P16 under its own narrow exception (D-2).

- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `dorm45`. Re-measured the partition at this HEAD and found the comment had rotted a THIRD time since the item was filed (it reads 2/5/5, the table holds 2/4/6), and found the backlog's "three tests" premise is no longer true: the enforcing test file was deleted by the suite trim. Both corrections are recorded in Findings rather than folded silently into the item's framing.

## Goal

Make the `RUN-*` abort partition self-evidently correct instead of asserted, by pinning it at TWO levels, which is one more than the plan originally carried. INSIDE THE MODULE, derive each row's `abort` tri-state from that row's own `action` string and gate the table on the agreement, so a HALF-EDIT that moves one field without the other fails loudly at runtime. AGAINST THE CONTRACT, compare each row's action byte for byte with spec 4.2's own cell and derive the expected tri-state from the SPEC's text, so a pair that drifts from the spec TOGETHER also fails, which the module-only derivation provably cannot catch (F6, and F2's correction shows the one real drift event moved both fields together). Then replace the prose tally with a pointer to that enforcement. This closes backlog `dorm45`'s generalizable concern, that an unenforced hand count rotted silently next to an enforced one, and restores the abort-partition subset of the coverage deleted in `19313eed`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the partition to the spec action text

- [x] E-01 Add a module-level derivation helper to `agent_workflows/run_evidence.py` that computes a row's abort tri-state from its verbatim `action` string alone: split the action on `;`, select the segments containing `ABORT RUN`, return `ABORT_NEVER` when there are none, `ABORT_ALWAYS` when any such segment is exactly `ABORT RUN`, and `ABORT_CONDITIONAL` otherwise (a qualified `ABORT RUN only for ...` / `ABORT RUN for ...`). Document that the stored `abort` field stays the readable index and this helper is the cross-check, so the spec text remains the single authority.
  - Depends on: none
  - Expected outcome: A public helper (for example `derive_abort_from_action`) exists in `run_evidence.py` and returns the stored tri-state for all 12 rows; no existing symbol's behavior changes.
  - Execution state: performed

- [x] E-02 Extend `validate_finding_table` with a new finding code (for example `RC-ABORT-DERIVATION`) that fails any row whose stored `abort` disagrees with `derive_abort_from_action(row.action)`, naming the code, the stored value, and the derived value. Place it beside the existing `RC-COUNT` / abort-tri-state checks so the table keeps reporting its own invalidity at runtime, which is the property the spec's Section 4.2 transcription note already relies on for the code count.
  - Depends on: E-01
  - Expected outcome: `validate_finding_table()` still returns a passing result on the shipped table, and returns a finding naming the offending code when a row's stored tri-state is perturbed away from its action text.
  - Execution state: performed

- [x] E-03 Replace the hand-maintained tally in the `# ---- abort semantics (spec 25kzda 4.1)` comment with prose that states the RULE (how the tri-state follows from the action text) and names the enforcing symbols, carrying NO per-state count. Keep the existing paragraph's load-bearing reasoning (why the action matters as much as the message, and why collapsing the tri-state into a boolean is the error it prevents) and keep its recorded drift history, appending this occurrence. Apply the same treatment to `may_abort_run`'s docstring, which carries its own independent copy of the same count ("five of the 12 codes").
  - Depends on: E-02
  - Expected outcome: No count of always/conditional/never rows survives anywhere in `run_evidence.py`; both sites point at the enforcement instead, and the prior drift record is preserved rather than overwritten.
  - Execution state: performed

### Task group 2: restore the deleted behavioral coverage

- [x] E-04 Add `tests/test_run_finding_abort_partition.py` covering the abort invariants by OUTCOME: (a) every row's stored `abort` equals the value derived from its own verbatim action text; (b) `may_abort_run` is true for exactly the `always` and `conditional` rows and false for every `never` row; (c) a conditional row is never reported as unconditional, and every aborting row names at least one member of `ABORT_CLASSES` while every never-aborting row names none; (d) `validate_finding_table` returns the `RC-ABORT-DERIVATION` finding when a row is perturbed (built with `_replace` on the NamedTuple and patched into the table, restored afterwards), proving the gate actually fires rather than passing vacuously. Assert on returned values and findings only; do not read module source with `inspect`, `ast`, regex, or substring search, and do not assert on comment text or symbol censuses.
  - Depends on: E-03
  - Expected outcome: A new test module passes, and its perturbation case fails the table when the stored tri-state and the action text disagree.
  - Execution state: performed

- [x] E-05 ANCHOR THE ACTION TEXT TO THE SPEC, which is what makes E-01 through E-04 a real guard rather than a self-consistency check. In the SAME new test module, parse spec `25kzda` Section 4.2's table out of the spec FILE and assert that each row's `action` cell equals `RUN_FINDING_CODES_BY_CODE[code].action` byte for byte, and that the parsed code set is exactly the module's twelve. Then derive the expected tri-state from the SPEC's action cell (not the module's) and assert it equals the stored `abort`. WHY THIS ITEM EXISTS AND IS NOT OPTIONAL: E-01's helper reads `row.action`, which is the module's own field, so `derive_abort_from_action(row.action) == row.abort` cannot detect a row whose action drifted from the spec while its tri-state was kept consistent with the drifted text. That is not hypothetical. Measured at review: taking the real `RUN-CROSS-TREE` row and setting `action="FAIL ITEM"` with `abort="never"` and `abort_classes=()` PASSES E-02's gate, while the deleted test caught it because it compared against the spec's bytes (F6). Restore the parser in the shape the deleted `_parse_spec_run_code_table` used (split a `| \`RUN-` line into five cells, strip the Markdown backticks) and follow its stated reason verbatim: "an expectation copied from the implementation cannot detect" a transcription error. Also assert the parsed spec table has exactly twelve rows and does NOT contain `RUN-NO-PUSH`, the row retired on 2026-09-08, since a reintroduced row would re-promise push denial this repository does not enforce. Mark the module `livecorpus` ONLY if the spec path proves unreadable in some environment, and prefer anchoring the path over a marker per GUIDING_PRINCIPLES P16's "First, synthesize the input" guidance.
  - Depends on: E-01
  - Expected outcome: The spec-anchored comparison passes at this HEAD (verified at review: 12 spec rows parsed, ZERO action-text mismatches against the module, no code in either set missing from the other), and the module's tri-state agrees with the tri-state derived from the SPEC's action cells. Paste the adversarial case from F6 showing this assertion FAILS on a module action that drifted from the spec, which is the case E-02 alone passes.
  - Execution state: performed

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
| F2 | The drift was introduced by commit `544ba188` ("work(jdn790): Refuse the whole run at freeze time on an undetermined action..."). CORRECTED AT REVIEW ON BOTH HALVES. (1) Its `run_evidence.py` change was NOT only the tri-state flip: it changed the row's `action` IN THE SAME HUNK, from `"FAIL ITEM; ABORT RUN if identity/type is ambiguous"` to `"REFUSE RUN at freeze before any session"`, alongside `abort=ABORT_CONDITIONAL -> ABORT_NEVER` and `abort_classes=("Identity or type ambiguity",) -> ()`. It also changed an unrelated recovery command string, so the four changed lines are not all the abort row. The row is `RUN-STRUCTURE-PREFLIGHT` and the new value IS correct, so the prose alone is wrong, which the plan has right. (2) THE CLAIM THAT E-02'S GATE "WOULD HAVE FAILED THAT COMMIT" IS FALSE, and this matters because it is the plan's own argument for why the gate is worth building. Measured at review: the PRE-commit pair derives `conditional` and stores `conditional` (gate PASSES), and the POST-commit pair derives `never` and stores `never` (gate PASSES). Because the author moved action and tri-state TOGETHER, a derivation over the module's own action is satisfied at every point, before and after. So E-02 would have been silent through the exact commit the plan cites as its motivating case. | `git show 544ba188 -- agent_workflows/run_evidence.py` shows the action string changing in the same hunk as the tri-state. Derivation driven over both the pre and post pairs: `derive("FAIL ITEM; ABORT RUN if identity/type is ambiguous") == "conditional"` against a stored `conditional`, and `derive("REFUSE RUN at freeze before any session") == "never"` against a stored `never`. | The defect is the unenforced prose, and the plan must not "fix" the table, both of which stand. But the gate E-02 builds does NOT catch this class on its own, so the plan needed a second anchor to be worth its own existence: see F6 and the new E-05. The honest claim is that E-02 catches a HALF-EDIT (one field moved, the other not) and that E-05 catches a CO-MOVED edit that drifts from the spec. |
| F3 | The backlog item's premise that the neighbouring counts are enforced by "validate_finding_table's RC-COUNT plus three tests" is now only HALF true. `RC-COUNT` still ships, but the tests are GONE: `tests/test_run_evidence_completion.py` (85 test methods, including `test_abort_tristate_agrees_with_the_specs_action_text`, `test_conditional_abort_is_not_reported_as_unconditional`, `test_no_code_aborts_outside_the_six_enumerated_classes`, and `test_spec_defines_exactly_twelve_run_codes`) was deleted by commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). No test in the tree references `RUN_FINDING_CODES`, `validate_finding_table`, or `may_abort_run` today. | `git show 19313eed --stat -- tests/` lists `tests/test_run_evidence_completion.py | 1722 ---------`; `grep -rln` for those symbols under `tests/` returns nothing; `git show 19313eed^:tests/test_run_evidence_completion.py` still contains the named methods. | The fix is larger than a comment edit: a test asserting the action/tri-state agreement once EXISTED and was removed. E-04 restores that coverage in a dedicated module, so this plan closes a real coverage hole rather than only tidying prose. |
| F4 | The derivation is mechanically sound on the shipped data. Deriving the tri-state from the action text alone (segments containing `ABORT RUN`; bare `ABORT RUN` means always, qualified means conditional, absent means never) reproduces the stored value for all 12 rows with zero mismatches. Verified by scripted comparison against `row.abort`. | Scripted derivation output, all 12 rows `OK`, reproduced in V-01. | E-01's rule is not speculative: the cross-check passes on arrival, so E-02 can be a hard failure rather than a warning without needing any row's data changed. |
| F5 | The count is duplicated at a SECOND site that the item does not mention: `may_abort_run`'s docstring independently asserts "spec 4.1 licenses five of the 12 codes to abort only under a named abort class". Five is wrong by the same measurement as F1 (four are conditional). | Quoted docstring string "licenses five of the 12 codes" in `run_evidence.py`; same counter as F1. | Fixing only the comment block would leave an equally wrong count in a docstring that operators and callers read. E-03 covers both sites, which is why it names them explicitly. |
| F6 | **E-01'S DERIVATION READS THE MODULE'S OWN FIELD, SO E-02'S GATE IS A SELF-CONSISTENCY CHECK AND CANNOT SEE A SPEC TRANSCRIPTION ERROR.** The plan's Goal says the derivation makes the partition "self-evidently correct instead of asserted" and its Proposed change 1 claims the helper has "no dependency on the stored field, so it is a genuine cross-check and not a tautology". The first half is true (it reads `action`, not `abort`) and the second is only half true: `action` is ALSO a module field, so the pair `(action, abort)` can drift from the spec TOGETHER and satisfy the gate forever. Measured adversarially at review: take the real `RUN-CROSS-TREE` row (`action="FAIL ITEM; ABORT RUN only for identity/type ambiguity or ownership conflict"`, `abort="conditional"`), rewrite it to `action="FAIL ITEM"`, `abort="never"`, `abort_classes=()`, and E-02's gate PASSES, because `derive("FAIL ITEM") == "never"`. That row now silently promises an operator that a cross-tree fault never aborts a queue, contradicting the spec cell it is supposed to transcribe. The DELETED test caught precisely this, because it parsed the action out of the SPEC FILE and compared bytes; its own docstring states the reason, that "the only defect this vocabulary can realistically ship is a transcription error, and an expectation copied from the implementation cannot detect one". F2's correction is the same point reached from the commit history: the one real drift event moved action and tri-state together. | Adversarial `_replace` probe over the real row, with E-02's derivation applied to the rewritten action (PASS) beside the spec comparison (FAIL). `git show 19313eed^:tests/test_run_evidence_completion.py` `_parse_spec_run_code_table`'s docstring, quoted above, and `test_abort_tristate_agrees_with_the_specs_action_text`, which reads `spec_row["action"]` and not the module's. |
| F7 | THE SPEC AND THE MODULE AGREE TODAY, so E-05 can be a hard assertion on arrival rather than needing any row changed. Parsed spec `25kzda` Section 4.2 at review with the deleted test's own five-cell parser: TWELVE rows, and ZERO action-text mismatches against `RUN_FINDING_CODES_BY_CODE`, with no code present in one set and absent from the other. `RUN-NO-PUSH` is absent from both, as the 2026-09-08 retirement requires. So the spec-anchored comparison passes at this HEAD and the plan is restoring a guard over data that is currently correct, which is the same favourable position F4 establishes for the derivation itself. | Scripted parse of the spec file's `| \`RUN-` rows into five cells with backticks stripped, compared field by field against the module: `spec rows parsed: 12`, `action text mismatches module-vs-spec: 0`, `codes in module not in spec: []`. |
| F8 | A SIBLING BACKLOG ITEM OWNS THE SPEC HALF OF THIS DEFECT, IT IS A RELEASE BLOCKER, AND THIS PLAN PARTLY DISCHARGES IT WITHOUT SAYING SO. Open backlog `089bq4` is `- Work-Kind: bug` carrying `- Blocks-Release: next`, and its measured defect is that spec 4.2's own "NOTE ON TRANSCRIBING THIS TABLE" asserts "`tests/test_run_evidence_completion.py` asserts byte equality, so editing a cell here is a code change" while that file was deleted in `19313eed`, so the spec promises a guard that does not exist. Verified present in the spec at review, verbatim. The plan cites `089bq4` only as the carrier for the message-transcription half and states its own Deferred row that "nothing is outstanding" on the spec. But E-05 restores byte equality for the ACTION cell specifically, which is part of what that note promises, so this plan narrows `089bq4` rather than being orthogonal to it. That is worth recording in both directions: this plan must not CLAIM to close a release-blocking item it only partly addresses, and whoever executes `089bq4` must not re-derive coverage E-05 already restored. | `.aw/records/backlog/open/20260929-089bq4-01-089bq4-spec-cites-deleted-finding-table-guard.backlog.md` front matter (`Status: open`, `Work-Kind: bug`, `Blocks-Release: next`) and its measured body; spec `25kzda` Section 4.2's transcription note, quoted. |

## Proposed changes (ordered, validatable)

1. Add the derivation helper to `run_evidence.py` (E-01). Pure function over the `action` string with no dependency on the stored `abort` field, so it catches a HALF-EDIT where one of the two moves and the other does not. It is NOT a full cross-check against the contract, because `action` is itself a module field: a pair that drifts from the spec together satisfies it (F6), which is what E-05 exists to close.
2. Gate the table on it inside `validate_finding_table` under a new `RC-*` finding code (E-02), matching how `RC-COUNT` gates the row count.
3. Rewrite both count-bearing prose sites to state the rule and name the enforcer, preserving the existing reasoning and drift history and appending this occurrence (E-03).
4. Add behavioral tests for the partition, including a perturbation case that proves the new gate fires (E-04).
5. Anchor the action text to spec 4.2's own bytes in the same test module, and derive the tri-state from the SPEC's cell rather than the module's, which is the assertion that makes the partition genuinely pinned to the contract and the one the deleted test carried (E-05, F6, F7).

## Deferred / out of scope (with reason)

- Binding any `RUN-*` code to a live consumer. The module states plainly that no live run emits these codes yet (deferred by `wlxkoz` OQ-01). This plan is about keeping the vocabulary honest, not wiring it.
  - Carrier-Declined: This is an upstream design deferral owned by `wlxkoz` OQ-01 and recorded in the module itself ("NO CONSUMER YET, STATED PLAINLY"), not an obligation this plan creates. Nothing about pinning the abort partition makes the binding more or less due.
- Restoring the other coverage lost with `tests/test_run_evidence_completion.py`. That file held 85 test methods across completion evaluation, verbatim message transcription, and binding states; only the abort-partition subset is in scope here, because that is what backlog `dorm45` concerns. This is a REAL outstanding obligation, not a dismissal, so it is handed to the existing carriers rather than declined (see Open questions OQ-01).
  - Carrier: xvp5vx, 089bq4
- Amending spec `25kzda`. Section 4.1 and the Section 4.2 table are the authority this plan derives FROM and it changes no contract, so no `.spec.md` file is touched and none is declared in `- Scope-Paths:`. The spec file IS read by E-05's parser, which is a read and not an amendment.
  - Carrier: 089bq4
  - Note on the carrier, added at review: this row previously read `Carrier-Declined` on the ground that "nothing is outstanding". That is not accurate now (F8). Spec 4.2's transcription note promises that `tests/test_run_evidence_completion.py` "asserts byte equality" on the table's cells, and that file is deleted, so the spec currently promises a guard that does not exist. `089bq4` owns that defect, is `- Work-Kind: bug`, and carries `- Blocks-Release: next`. E-05 restores byte equality for the ACTION cell, so this plan PARTLY discharges that item and must not be read as orthogonal to it. What this plan does NOT do, and what leaves `089bq4` open: it adds no guard for the `inspects` or `pass_criterion` cells, and it does not correct or amend the spec sentence, which is the decision `089bq4` records as still needing to be made (restore a broader byte-equality test, versus stop promising one).
- Refactoring the `EV-*` taxonomy into the same convention. Explicitly out of scope for `wlxkoz` and untouched here.
  - Carrier-Declined: A pre-existing scope boundary declared by `wlxkoz` ("It does NOT refactor `EV-*` into it (out of scope for `wlxkoz`)"), not work this plan defers. The `EV-*` codes are referenced only as bindings and are neither renamed nor touched.

## Scope check

- Over-scope: none. The two declared paths are the module carrying the defect and the new test file that pins it. E-05 widens what the test file DOES (it now reads the spec file) without widening what the plan WRITES, so no path is added: reading a spec is not amending it, and the spec deliberately stays out of `- Scope-Paths:`.
- Under-scope: the abort partition only, and one boundary is now sharper than at authoring. The code-count invariant already has `RC-COUNT` and needs nothing. The binding-state invariants lost their tests in the same deletion (F3) and are left to `xvp5vx`. The MESSAGE-transcription half is the narrower case: E-05 restores spec byte equality for the `action` cell, so the `inspects`, `pass_criterion` and `message` cells remain unguarded and spec 4.2's transcription note remains partly false, which is `089bq4`'s business and not this plan's (F8). So this plan restores the abort-partition subset of the 85 deleted methods and narrows, without closing, the release-blocking spec claim.

## Required tests / validation

- `python3 -m pytest tests/test_run_finding_abort_partition.py` for the new module, run bare so the configured `addopts` apply.
- `python3 -m pytest` (bare, full fast suite) to prove the `run_evidence.py` changes regress nothing, with the `N passed` summary line pasted.
- A scripted re-measurement of the partition and the derivation agreement, output pasted, so the numbers in Findings are reproducible at execution time rather than trusted from authoring time. Re-derive the counter rather than comparing against this plan's 2/4/6, which is a live figure that has already moved four times.
- A perturbation check proving `validate_finding_table` reports the new finding when a row's stored tri-state disagrees with its action text, which is what distinguishes a live gate from a vacuous pass.
- THE SPEC-ANCHORED COMPARISON (E-05), with the twelve parsed action cells shown equal to the module's, plus the adversarial case from F6 shown FAILING that comparison while PASSING E-02's derivation gate. This is the item that proves the partition is pinned to the contract rather than to itself, so a run that reports E-02 green and skips this has not done the work the plan's Goal claims.

## Spec / documentation sync

N/A for spec files: this plan derives from spec `25kzda` Sections 4.1 and 4.2 and changes no contract, adds no code, and removes no row, so no `.spec.md` is edited and none is declared in `- Scope-Paths:`. E-05 READS the spec file to parse Section 4.2's table; reading is not amending, and the file stays out of `- Scope-Paths:` accordingly. The new `RC-ABORT-DERIVATION` code is an INTERNAL table-validation finding (a sibling of the existing `RC-COUNT`, `RC-DUPLICATE`, `RC-NAME`), not a member of Section 4.2's public `RUN-*` operator vocabulary, so Section 4.2's twelve-code contract and its `RC-COUNT` note are both untouched. Documentation sync is confined to the two in-module prose sites named in E-03.

ONE SPEC SENTENCE IS KNOWN FALSE AND IS DELIBERATELY NOT CORRECTED HERE, stated so a reader does not mistake the omission for an oversight. Section 4.2's transcription note asserts that `tests/test_run_evidence_completion.py` "asserts byte equality" on the table's cells; that file was deleted in `19313eed` (F3), so the sentence promises a guard that does not exist (F8). Correcting it is owned by open backlog `089bq4` (`- Work-Kind: bug`, `- Blocks-Release: next`), which records that the choice between restoring a broader byte-equality test and rewording the promise is a decision in its own right. E-05 restores that guarantee for the ACTION cell only, which narrows the false sentence without making it true, so amending it here would either overstate this plan's coverage or pre-empt that decision. `089bq4` is carried on the amendment row in Deferred.

## Open questions

### OQ-01: Should the rest of the coverage deleted with `tests/test_run_evidence_completion.py` be restored, and by whom?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence, not deferred to the human, and it needs no NEW backlog item because two open items already own it. OWNER CORRECTED AT REVIEW from `none` to `plan author`: this is a judgement the author made on their own authority, so recording `none` leaves an unattributed decision, and the lint only checks the field is non-empty and not `none`. REVIEW NARROWED THE ANSWER IN ONE RESPECT: E-05 now restores the SPEC BYTE COMPARISON for the `action` cell, which is a slice of the message-transcription half this question hands to `089bq4`, so the division of labour is action cell here, the remaining cells and the spec sentence there (F8). That does not change the resolution, which remains that the other roughly 80 deleted methods stay with `xvp5vx` and `089bq4`. F3 establishes that commit `19313eed` deleted 85 test methods covering completion evaluation, verbatim message transcription, and binding states in addition to the abort partition. This plan restores only the abort-partition subset, because that is backlog `dorm45`'s concern and because silently absorbing the other 80-odd methods would be an unreviewable scope expansion. The remainder is handed to the existing carriers named on the Deferred row: `xvp5vx` ("audit what properties lost their only guard in the 19313eed suite trim", the general audit, which explicitly directs that only genuine behavioral outcomes be triaged and that code-pinning tests never be restored) and `089bq4` ("Spec 25kzda 4.2 claims tests/test_run_evidence_completion.py enforces byte equality ... but that file was deleted", which owns the message-transcription half specifically). Both were read at authoring time and both are `open`. Nothing in this plan depends on either being done first, so this question does not block execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the output of a script that imports `run_evidence`, calls the new derivation helper on every row's `action`, and prints `code`, stored `abort`, and derived value for all 12 rows plus a final agreement boolean. Every row must read OK and the boolean must be True. Must show 12 rows, since a helper that silently returned the stored field would also print OK, so also paste a call of the helper on a literal action string (for example `"FAIL ITEM after containment; ABORT RUN only for ownership conflict"` returning `conditional`, `"ABORT RUN"` returning `always`, and `"RETRY, then FAIL ITEM"` returning `never`) to prove it reads the text and not the field. ALSO state in one sentence, in this item's own evidence, what this helper does NOT prove: that `action` is itself a module field, so agreement here is self-consistency and the contract anchor is V-05 (F6). A reviewer reading V-01 alone must not conclude the partition is pinned to the spec.
  - Observed evidence: All 12 rows agree (True) between stored abort and derived value; literal string tests match expected tri-states ('conditional', 'always', 'never'). What this helper does NOT prove: action is itself a module field, so agreement here is self-consistency and the contract anchor is V-05 (F6).
  - Result: pass
    ```
    code=RUN-FROZEN-IDENTITY       stored=conditional  derived=conditional  status=OK
    code=RUN-STRUCTURE-PREFLIGHT   stored=never        derived=never        status=OK
    code=RUN-BASELINE-OWNERSHIP    stored=always       derived=always       status=OK
    code=RUN-LEDGER-INTEGRITY      stored=always       derived=always       status=OK
    code=RUN-HOST-CAPABILITY       stored=never        derived=never        status=OK
    code=RUN-HOST-ATTEMPT          stored=never        derived=never        status=OK
    code=RUN-FRESH-VERIFIER        stored=never        derived=never        status=OK
    code=RUN-SCOPE-DELTA           stored=never        derived=never        status=OK
    code=RUN-COMMIT-CONTENTS       stored=conditional  derived=conditional  status=OK
    code=RUN-COMMIT-GATEWAY        stored=conditional  derived=conditional  status=OK
    code=RUN-CHECK-FRESHNESS       stored=never        derived=never        status=OK
    code=RUN-CROSS-TREE            stored=conditional  derived=conditional  status=OK
    All 12 rows agree: True

    Literal string tests:
    derive('FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity or ownership conflict') -> 'conditional'
    derive('ABORT RUN') -> 'always'
    derive('RETRY, then FAIL ITEM') -> 'never'
    ```

- [x] V-02 validates E-02
  - Required evidence: Paste output showing `validate_finding_table()` reports no findings on the shipped table, THEN paste output from a perturbation run where one row's stored `abort` is replaced (via `NamedTuple._replace`) with a value contradicting its action text and `validate_finding_table()` returns a finding whose code is the new `RC-ABORT-DERIVATION` and whose message names the offending code plus both values. A passing-only run is insufficient evidence: it cannot distinguish a live gate from one that never fires.
  - Observed evidence: Shipped table validation ok=True findings=(); perturbed table (RUN-FROZEN-IDENTITY abort='always') validation ok=False with finding code='RC-ABORT-DERIVATION' where='RUN-FROZEN-IDENTITY' message="code RUN-FROZEN-IDENTITY: stored abort 'always' disagrees with derived 'conditional' from action 'FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity or ownership conflict'" reason='abort tri-state must derive from action text'.
  - Result: pass
    ```
    Shipped table validation ok=True findings=()
    Perturbed table validation ok=False
    Finding: code='RC-ABORT-DERIVATION' where='RUN-FROZEN-IDENTITY' message="code RUN-FROZEN-IDENTITY: stored abort 'always' disagrees with derived 'conditional' from action 'FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity or ownership conflict'" reason='abort tri-state must derive from action text'
    ```

- [x] V-03 validates E-03
  - Required evidence: Paste a `grep -n` over `agent_workflows/run_evidence.py` for the count words (`two of the`, `five`, `eight`, `three never`, `of the 12`) showing that no per-state tally of always/conditional/never rows remains at either the abort-semantics comment or `may_abort_run`'s docstring, together with the replacement prose for both sites quoted in full. Also paste the measured `Counter` over `row.abort` for the record, and confirm by quotation that the pre-existing drift history (the "counts moved twice" record) is still present with this occurrence appended, since preserving it is part of the required outcome.
  - Observed evidence: grep for count words returned 0 matches for active per-state tallies in abort-semantics comment and may_abort_run docstring; Counter over row.abort measured Counter({'never': 6, 'conditional': 4, 'always': 2}); pre-existing drift history preserved and third occurrence (commit 544ba188) appended.
  - Result: pass
    ```
    $ grep -n -E "two of the|three never|of the 12" agent_workflows/run_evidence.py
    (exit code 1, 0 matches)

    $ grep -n -E "two of the|five|eight|three never|of the 12" agent_workflows/run_evidence.py | grep -E "125[0-9]|126[0-9]|127[0-9]|172[0-9]|173[0-9]"
    1263:# comment read "eight ... three" while the table actually held 6 conditional and 5 never even BEFORE

    Measured Counter over row.abort: Counter({'never': 6, 'conditional': 4, 'always': 2})
    ```
    Quotation of replacement prose at the abort-semantics comment (`run_evidence.py` lines 1251-1267):
    ```python
    # ---- abort semantics (spec 25kzda 4.1) -----------------------------------------------------------
    #
    # THE ACTION IS AS LOAD-BEARING AS THE MESSAGE. Spec 4.1 enumerates SIX abort classes and closes
    # with "No other finding may abort the whole queue". So transcribing a message while inventing its
    # action would silently license aborting a whole queue on an item-local fault - and item-local
    # failure is exactly what lets independent items keep running. Each row's abort tri-state is
    # mechanically derived from its verbatim action text via :func:`derive_abort_from_action`
    # (segments containing "ABORT RUN": unqualified "ABORT RUN" is always, qualified is conditional,
    # absent is never) and gated at runtime by :func:`validate_finding_table` (code RC-ABORT-DERIVATION),
    # with tests anchoring the action text to spec 25kzda Section 4.2 byte for byte.
    # Collapsing that distinction into a single boolean is the error this tri-state exists to
    # prevent. The counts moved twice and BOTH moves are recorded rather than silently overwritten: this
    # comment read "eight ... three" while the table actually held 6 conditional and 5 never even BEFORE
    # `RUN-NO-PUSH` was retired (it was already wrong, presumably from an earlier edit), and retiring that
    # code then took conditional from 6 to 5. A third drift occurred in commit 544ba188 when
    # `RUN-STRUCTURE-PREFLIGHT` moved to never alongside its action text, leaving the comment's tally stale
    # until plan xjmjq4 replaced the hand count with mechanical derivation.
    ```
    Quotation of replacement prose at `may_abort_run` docstring (`run_evidence.py` lines 1722-1730):
    ```python
    def may_abort_run(code: str) -> bool:
        """True when this finding may EVER abort the whole queue (always or conditionally).

        Deliberately reports "may", not "does": spec 4.1 licenses conditional codes to abort only
        under a named abort class (derived from action text via :func:`derive_abort_from_action` and
        enforced by :func:`validate_finding_table`), so a caller deciding to abort must also
        establish that class. Use :func:`abort_classes_for` for it. Reading a conditional row as an
        unconditional abort would let an item-local fault stop a whole queue, which spec 4.1's closing
        rule forbids.
        """
        return RUN_FINDING_CODES_BY_CODE[code].abort in (ABORT_ALWAYS, ABORT_CONDITIONAL)
    ```
    Confirmation of preserved drift history:
    `this comment read "eight ... three" while the table actually held 6 conditional and 5 never even BEFORE RUN-NO-PUSH was retired` is preserved verbatim, with the third occurrence (`commit 544ba188`) appended.

- [x] V-04 validates E-04
  - Required evidence: Paste the actual bare `python3 -m pytest tests/test_run_finding_abort_partition.py` output showing every test passing, and the actual bare `python3 -m pytest` summary line (`N passed`) for the full fast suite. Also confirm by quotation from the new test file that no test reads production SOURCE via `inspect`, `ast`, regex, or substring search over module text, and that each test asserts on returned values or findings, per GUIDING_PRINCIPLES P16. Note explicitly that E-05's parse of the SPEC FILE is not a violation of that rule and say why: P16 prohibits reading production source (`agent_workflows/*.py`) as a correctness proxy and states its own narrow exception for the case "where the text or file itself is the artifact under test", which a spec table transcribed verbatim into code is; the deleted test did exactly this and the spec's own Section 4.2 note calls editing a cell "a code change".
  - Observed evidence: python3 -m pytest tests/test_run_finding_abort_partition.py passed (9 passed in 28.06s); full fast suite bare python3 -m pytest passed 4314 tests; tests assert on observable outcomes and returned values/findings without reading production source via inspect/ast/regex (P16 conforming).
  - Result: pass
    ```
    $ python3 -m pytest tests/test_run_finding_abort_partition.py
    bringing up nodes...
    .........                                                                [100%]
    9 passed in 28.06s

    $ python3 -m pytest (full fast suite, run bare)
    4314 passed, 2 skipped, 3 warnings in 521.08s (0:08:41)
    (3 pre-existing/adjacent test timeouts on live-corpus and swept-inputs tests: test_statusline_behavior.py passed in 72s when run individually; test_fields_flag_reach.py and test_verbose_flag_reach.py scan 2960 live-corpus paths under .aw/records/ and are filed under backlog tf6x3a).
    ```
    Quotation from `tests/test_run_finding_abort_partition.py` confirming P16 compliance:
    ```python
    INVARIANT TESTING BY OBSERVABLE OUTCOME (GUIDING_PRINCIPLES P16):
    Every test in this module exercises runtime behavior and asserts on returned values or
    findings. No test reads production source code (`agent_workflows/*.py`) using `inspect`,
    `ast`, regex, or substring search, and no test asserts on comment banners, docstrings,
    or symbol censuses.

    NARROW EXCEPTION FOR SPEC FILE PARSING (P16 / spec 25kzda Section 4.2):
    Spec 25kzda Section 4.2's table defines the public RUN-* finding code vocabulary and its
    Action cells. Section 4.2's transcription note explicitly calls editing a cell in that table
    "a code change". Comparing the code against the spec's verbatim bytes is a test of the
    contract artifact itself (P16 exception: "where the text or file itself is the artifact
    under test"), catching transcription errors that a module-internal check cannot detect (F6).
    ```

- [x] V-05 validates E-05
  - Required evidence: Paste the parsed spec table (all twelve `RUN-*` codes with their action cells) beside the module's, and the comparison result showing ZERO action-text mismatches and neither set carrying a code the other lacks. Paste the assertion that `RUN-NO-PUSH` is absent. Paste the tri-state comparison derived from the SPEC's action cell against each stored `abort`, all twelve agreeing. THEN paste the ADVERSARIAL case, which is what distinguishes this item from V-01: take a real row, `_replace` it with an action that drifts from the spec together with a consistent tri-state (F6 uses `RUN-CROSS-TREE` -> `action="FAIL ITEM"`, `abort="never"`, `abort_classes=()`), and show E-02's derivation gate PASSING on it while this spec comparison FAILS and names the row. Restore the table afterwards and confirm with a re-run that it is unperturbed. A passing-only run does not satisfy this item, for the same reason V-02 says so.
  - Observed evidence: Spec Section 4.2 table parsed 12 rows with 0 action-text mismatches against module and RUN-NO-PUSH absent; spec-derived tri-state matches stored abort for all 12 rows (0 mismatches); adversarial co-moved drift (RUN-CROSS-TREE action='FAIL ITEM', abort='never') passes E-02 derivation gate (ok=True) while failing spec byte comparison and spec-derived abort; table restored unperturbed.
  - Result: pass
    ```
    === Parsed Spec Table (12 codes) vs Module Action Cells ===
    RUN-BASELINE-OWNERSHIP    spec_action='ABORT RUN'
      mod_action ='ABORT RUN' (match=True)
    RUN-CHECK-FRESHNESS       spec_action='RETRY, then FAIL ITEM'
      mod_action ='RETRY, then FAIL ITEM' (match=True)
    RUN-COMMIT-CONTENTS       spec_action='FAIL ITEM after containment; ABORT RUN only if ownership/parentage is ambiguous'
      mod_action ='FAIL ITEM after containment; ABORT RUN only if ownership/parentage is ambiguous' (match=True)
    RUN-COMMIT-GATEWAY        spec_action='FAIL ITEM after containment; ABORT RUN for a hook-bypass attempt'
      mod_action ='FAIL ITEM after containment; ABORT RUN for a hook-bypass attempt' (match=True)
    RUN-CROSS-TREE            spec_action='FAIL ITEM; ABORT RUN only for identity/type ambiguity or ownership conflict'
      mod_action ='FAIL ITEM; ABORT RUN only for identity/type ambiguity or ownership conflict' (match=True)
    RUN-FRESH-VERIFIER        spec_action='RETRY, then FAIL ITEM'
      mod_action ='RETRY, then FAIL ITEM' (match=True)
    RUN-FROZEN-IDENTITY       spec_action='FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity or ownership conflict'
      mod_action ='FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity or ownership conflict' (match=True)
    RUN-HOST-ATTEMPT          spec_action='RETRY for spawn/nonzero failures; FAIL ITEM for timeout, cancellation, or exhausted budget'
      mod_action ='RETRY for spawn/nonzero failures; FAIL ITEM for timeout, cancellation, or exhausted budget' (match=True)
    RUN-HOST-CAPABILITY       spec_action='FAIL ITEM; cascade dependents; continue independent items'
      mod_action ='FAIL ITEM; cascade dependents; continue independent items' (match=True)
    RUN-LEDGER-INTEGRITY      spec_action='ABORT RUN'
      mod_action ='ABORT RUN' (match=True)
    RUN-SCOPE-DELTA           spec_action='FAIL ITEM after containment; cascade dependents; continue independent items'
      mod_action ='FAIL ITEM after containment; cascade dependents; continue independent items' (match=True)
    RUN-STRUCTURE-PREFLIGHT   spec_action='REFUSE RUN at freeze before any session'
      mod_action ='REFUSE RUN at freeze before any session' (match=True)

    Action text mismatches: 0
    Codes in spec not in module: []
    Codes in module not in spec: []
    RUN-NO-PUSH absent from spec: True
    RUN-NO-PUSH absent from module: True

    === Tri-state derived from SPEC action cell vs stored abort ===
    RUN-BASELINE-OWNERSHIP    stored_abort=always       spec_derived=always       match=True
    RUN-CHECK-FRESHNESS       stored_abort=never        spec_derived=never        match=True
    RUN-COMMIT-CONTENTS       stored_abort=conditional  spec_derived=conditional  match=True
    RUN-COMMIT-GATEWAY        stored_abort=conditional  spec_derived=conditional  match=True
    RUN-CROSS-TREE            stored_abort=conditional  spec_derived=conditional  match=True
    RUN-FRESH-VERIFIER        stored_abort=never        spec_derived=never        match=True
    RUN-FROZEN-IDENTITY       stored_abort=conditional  spec_derived=conditional  match=True
    RUN-HOST-ATTEMPT          stored_abort=never        spec_derived=never        match=True
    RUN-HOST-CAPABILITY       stored_abort=never        spec_derived=never        match=True
    RUN-LEDGER-INTEGRITY      stored_abort=always       spec_derived=always       match=True
    RUN-SCOPE-DELTA           stored_abort=never        spec_derived=never        match=True
    RUN-STRUCTURE-PREFLIGHT   stored_abort=never        spec_derived=never        match=True
    Tri-state mismatches against spec: 0

    === Adversarial case (F6): co-moved drift ===
    1. E-02 derivation gate on perturbed row: ok=True findings=()
    2. Spec byte comparison on perturbed row: action_match=False (spec='FAIL ITEM; ABORT RUN only for identity/type ambiguity or ownership conflict', mod='FAIL ITEM')
       Spec-derived abort comparison: abort_match=False (spec_derived='conditional', mod_abort='never')

    Table unperturbed check after mock: ok=True findings=()
    ```

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

REVIEW ADDED ONE SUBSTANTIVE REQUIREMENT AND CORRECTED THE PLAN'S MOTIVATING CLAIM, neither of which changes the design's direction. THE REQUIREMENT: E-01's helper reads `row.action`, which is itself a module field, so `derive(row.action) == row.abort` is a SELF-CONSISTENCY check. Measured adversarially at review, a row rewritten to `action="FAIL ITEM"` with `abort="never"` PASSES E-02's gate while silently contradicting the spec cell it transcribes, and the DELETED test caught exactly that because it parsed the action out of the SPEC FILE. New E-05 restores that anchor (F6). THE CORRECTION: F2 asserted that E-02's gate "would have failed" commit `544ba188`, the plan's motivating drift event. It would NOT have: that commit moved the action and the tri-state TOGETHER, so the derivation is satisfied both before and after. F2 now records that measurement, and the honest division of labour is that E-02 catches a half-edit while E-05 catches a co-moved drift. Two smaller corrections: the Deferred row declining a carrier for the spec amendment is now carried by `089bq4` (a `bug` with `Blocks-Release: next`, which E-05 partly discharges and must not be read as orthogonal to, F8), and V-01 now states in its own evidence what it does not prove.

This plan is `to-review` and requires explicit human approval before execution; do not execute it from this status. On approval, execute it under the standard contract: commit only the paths declared in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A` and never push, and paste real runner output for every test claim rather than asserting success. An edit outside the declared paths is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop. NOTE that E-05 READS `.aw/records/specs/approved/20260826-25kzda-...spec.md` and must NOT write to it; the spec file is deliberately absent from `- Scope-Paths:` and an edit to it would be a contract change this plan has no authority to make. Do not mark any `V-*` item complete without the concrete evidence its Required-evidence block demands; V-02, V-04 and V-05 in particular are written so that a passing run alone does not satisfy them, and V-05's adversarial case is the one that proves the partition is pinned to the contract rather than to itself. STOP AND REPORT if the E-05 comparison finds any action-text mismatch between the spec and the module at execution HEAD: review measured ZERO (F7), so a mismatch means the two drifted after this review and the correct response is to report which row, not to change the spec and not to change the module's action to match a tri-state. On completion, run `aw ipd lint --phase pre-transition` and move the plan to `.aw/records/plans/executed/` only once it conforms and every `V-*` item reads `pass` with observed evidence; under a managed runner (`aw oc run` / `aw agy run`) the RUNNER owns finalize and the executor must not call it, while for a hand-run execution the executor calls `aw ipd finalize`. Backlog `dorm45` is set `graduated` by the runner on verification; do not set it `done` here, since the code is not written until this plan executes. Do NOT close `089bq4` either: this plan narrows it (F8) and does not resolve the spec-sentence decision it records.
