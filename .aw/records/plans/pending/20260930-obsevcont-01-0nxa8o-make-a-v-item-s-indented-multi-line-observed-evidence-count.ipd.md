# IPD: Make a V-item's indented multi-line Observed evidence count as evidence, instead of parsing to empty

- Date: 2026-09-30
- Kind: child
- Concern: `ipd_lint.parse` reads every indented leaf sub-field as a SAME-LINE value (the `_SUBFIELD_RE` branch assigns `cur_fields[key] = value` from one line and `continue`s), so a `- Observed evidence:` line followed by an indented multi-line transcript parses to the EMPTY STRING. Reproduced at HEAD (re-reproduced at review on `25224ceb`): a V-item written `- [x] V-01 ...` / `- Observed evidence:` / two indented transcript lines / `- Result: pass` parses to `{'Required evidence': 'run the suite', 'Observed evidence': '', 'Result': 'pass'}`, so `ipd_lint.check_states` emits `IPD-S402 V-01: result 'pass' requires nonempty Observed evidence` and `ipd_lint.check_checkpoint` emits `IPD-S404 V-01: empty Observed evidence at pre-transition` while a full transcript sits directly beneath the field. The shape is the one the field is FOR: the execution contract demands the ACTUAL pasted runner output, which is inherently multi-line, and `ipd_lint._structural_lines` drops any line indented 4+ spaces or fenced, which is exactly how a pasted transcript is written. The dangerous half is not the refusal but its WORDING: a gate that says the evidence is ABSENT when it is present invites the executor to delete or shrink real evidence to make the gate pass.
- Scope: IN: (a) make the read of the two PRESENCE-CHECKED FREE-TEXT leaf sub-fields (`Observed evidence`, `Execution note`) continuation-aware, so the block beneath the field line is part of its value, implemented as a NAMED PER-FIELD set in `ipd_lint` with a blank-tolerant fence-aware termination rule, and never as a blanket change to `_SUBFIELD_RE` (F-3 measures that a global absorb corrupts 100 `Execution state`, 47 `Depends on` and 2 `Result` values in the live corpus); (b) document the resulting authoring shape AND its termination rule in the governing spec's Section 5.3/5.4 and in its canonical Section 14 example, so the convention is written down rather than discovered by reading the linter; (c) behavioral tests for both, covering all four real evidence shapes and including the negative direction that a `pending` row with continuation-only evidence is now correctly REFUSED. OUT: `_SUBFIELD_RE` itself and every closed-vocabulary or parsed field, which keep the one-line read (F-3); `leaf_action_blocks`, whose rule is deliberately NOT reused and NOT modified (F-10); the `IPD-S402` vocabulary-enumeration half of the item, which pending plan `uh9jsk` already owns in full (F-6); the three pinned `IPD-S404` message texts, which are a live run-control trigger (F-7); and the plan corpus, which needs no rewrite because zero existing rows depend on the old reading (F-4).
- Scope-Paths: agent_workflows/ipd_lint.py, tests/test_ipd_lint.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: pz34kx
- Set: obsevcont
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 0nxa8o
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. The review's central finding (PR-001, HIGH) is that E-01's chosen termination rule DID NOT ACHIEVE THE PLAN'S OWN GOAL: reusing `leaf_action_blocks`' rule verbatim stops at the first blank line and at any non-indented line, and measurement over the tracked corpus shows 978 of 2800 real evidence blocks would still parse to the empty string and still be refused (801 begin after a blank line, 177 at a col-0 line or fence). E-01 now specifies a blank-tolerant fence-aware rule, verified zero-delta on the corpus at all three checkpoints and verified to cross no leaf/`##` boundary and never run to EOF, while `leaf_action_blocks` stays untouched for its three consumers. PR-002 (HIGH) corrected E-03, whose assertion was false on arrival: 188 tracked plans correctly report `empty Observed evidence` at `pre-transition`, so the test now asserts verdict NEUTRALITY rather than absolute absence. Six further findings corrected E-02's row predictions (row (c) is `conforming` at HEAD, not passing), the F-1 diagnostic text, four stale corpus counts, a fence-nesting hazard in the spec's Section 14 example, and a scope fence that read as a stop instruction. OQ-01 resolved NO from repository evidence (recorded as D-1). All five of E-02's rows were executed as probes at review and behave as the revised plan predicts.
- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `pz34kx`. The item offers two shapes and calls (b)+(c) "the cheap one": either teach the parser to accept an indented continuation block, or keep the parser and DOCUMENT the summary-line workaround plus name the accepted vocabulary in `IPD-S402`. THIS PLAN TAKES THE PARSER FIX, and the reason is measured rather than preferred. The documentation-only option asks every executor to keep obeying a convention that exists solely to work around a parser limitation, and the item itself records that the convention was "discovered by reading the linter's source after a refusal"; documenting a workaround leaves the refusal message still saying ABSENT when evidence is present, which is the failure mode the item calls dangerous. THE PARSER FIX IS ALSO CHEAPER THAN IT LOOKS ON THIS CORPUS: F-4 measures that ZERO of 5434 V-items and ZERO of 5608 presence-checked free-text fields in the tracked tree change verdict under the new read, because the gate has forced every author onto the summary-line workaround already. So the change is a strict widening with no corpus migration, and it also makes DOCUMENTING the shape honest (E-03 documents what the parser then actually does, rather than a workaround). The item's SECOND, SMALLER HALF (that `IPD-S402` names the rejected value without naming the accepted ones) is NOT duplicated here: F-6 establishes that pending plan `uh9jsk`, graduated from backlog `mc57em`, already owns exactly that fix in `ipd_schema.validation_row_error`.

## Goal

Make the linter see the evidence an executor actually wrote. A `- Observed evidence:` line followed
by an indented transcript must count as nonempty evidence, so the natural shape the spec's own prose
invites stops being refused with a message claiming the evidence is absent. Nothing about WHICH
values are legal changes, and no closed-vocabulary field's parse changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: teach the parser the continuation shape, for named fields only

- [x] E-01 In `agent_workflows/ipd_lint.py`, add a module-level named constant (a `FrozenSet[str]`, sited beside `_SUBFIELD_RE` with a comment recording F-3's measurement) holding the leaf sub-field keys whose value MAY continue onto following lines: exactly `Observed evidence` and `Execution note`. Then, in `parse`'s `_SUBFIELD_RE` branch, when the matched key is a member, read forward from that line and APPEND the continuation lines to the field's value; for every other key, keep today's exact one-line behavior byte for byte. USE THE EVIDENCE-BLOCK TERMINATION RULE STATED BELOW, WHICH IS DELIBERATELY NOT `leaf_action_blocks`' RULE (F-10 measures that reusing that rule verbatim leaves 978 of 2800 real evidence blocks still parsing to the empty string, so the plan would not achieve its own goal): read forward from the field line, (i) TOLERATING blank lines rather than stopping at one, (ii) tracking fenced regions (a line whose stripped form opens with ``` or ~~~ toggles the region; drop the marker line itself from the value and absorb the fenced body unconditionally), and (iii) outside a fenced region stopping at a line matching `_SUBFIELD_RE`, a line starting `- [`, a line starting `#`, or any other non-indented line. READ FROM THE RAW TEXT, NOT FROM THE STRUCTURAL VIEW, because `_structural_lines` deliberately drops 4-space-indented and fenced lines and a pasted transcript is written in exactly those (measured: 1800 of 1803 continuation blocks in the corpus begin at 4-space indent and 386 begin with a fence). Join the collected lines with a space after stripping each, as `leaf_action_blocks` does, so a value is a single string and every existing consumer keeps its type. Change neither `_SUBFIELD_RE` nor `leaf_action_blocks` nor `_structural_lines`: `leaf_action_blocks` keeps its own rule because it bounds a FROZEN-CONTRACT region that a blank line legitimately ends, whereas this rule bounds a PASTED-TRANSCRIPT region that routinely contains one. Record that divergence in the comment beside the constant so a later reader does not "unify" the two and silently re-break this.
  - Depends on: none
  - Expected outcome: `ipd_lint.parse` returns a nonempty `Leaf.fields["Observed evidence"]` for a V-item whose `- Observed evidence:` line is EMPTY and whose transcript sits beneath it in each of these four real shapes: directly indented; separated from the field line by a blank line; inside an INDENTED fence; and inside a COL-0 fence. A genuinely empty field (next line is another sub-field) still returns the empty string. The same document's `Result`, `Depends on`, and `Execution state` values are byte-identical to what HEAD returns; `leaf_action_blocks` output for the same text is unchanged (it stops before sub-fields, so a continuation it never read cannot move); and the read never crosses a leaf or `##` boundary nor runs to EOF on any tracked plan.
  - Execution state: performed

- [x] E-02 Add a table row set to `tests/test_ipd_lint.py` covering the continuation read as OUTCOMES of `lint_text`, not as a parser-internals assertion: (a) a conforming child whose V-01 carries `Result: pass` with an EMPTY `- Observed evidence:` line and an indented transcript beneath it lints `conforming` at `pre-transition` (this is the defect, and it is RED at HEAD with `IPD-S402 V-01: result 'pass' requires nonempty Observed evidence` plus `IPD-S404 V-01: empty Observed evidence at pre-transition`); (a2), (a3) and (a4) the SAME shape with the transcript separated from the field line by a BLANK line, inside an INDENTED fence, and inside a COL-0 fence, each of which must also lint `conforming` (these three are what F-10 measures the `leaf_action_blocks` rule would silently fail, so they are the rows that pin the termination rule E-01 actually requires); (b) the shape of (a) with the transcript DELETED still lints `error` with both findings, so the test cannot pass by the check being weakened; (c) a `Result: pending` V-item carrying a continuation block is REFUSED at the `author` checkpoint with `IPD-S402 V-01: result 'pending' must have empty Observed evidence`, which is the negative direction proving the new read feeds the existing state table rather than bypassing it (assert at `author`, NOT only at `pre-transition`, because at `pre-transition` the row also trips `not 'pass' at pre-transition` and the assertion would pass for the wrong reason); (d) an `Execution state: blocked` E-item whose `- Execution note:` is continuation-only satisfies the note requirement (RED at HEAD with `IPD-S401 E-01: state 'blocked' requires an Execution note`); and (e) a CONTROL row proving the per-field narrowness: an `- Execution state: performed` line followed by an indented prose line still parses to `performed` and lints clean, which is the row that fails if someone later widens the absorb to every field (verified at review: widening to every field makes it report `IPD-S401 E-01: unknown execution state 'performed some trailing prose about the work'`). Assert on rendered diagnostics from the public entry point so the rows survive a refactor of the parser's internals.
  - Depends on: E-01
  - Expected outcome: rows (a), (a2), (a3), (a4) and (d) fail at HEAD and pass after E-01; rows (b) and (e) pass both before and after; row (c) passes only after E-01 (it is `conforming` at HEAD because the continuation is invisible, so it is a RED-then-GREEN row in the opposite direction and must be shown as such rather than claimed to pass at HEAD); and deleting the named-field constant from E-01, so the absorb applies to every sub-field, makes row (e) fail.
  - Execution state: performed

- [x] E-03 Add a corpus test to `tests/test_ipd_lint.py` asserting the PROPERTY that the continuation read changes NO tracked plan's lint outcome. ASSERT THE DELTA, NOT AN ABSOLUTE ABSENCE, and this is the correction that makes the test possible at all: the absolute form the plan first specified ("no plan reports the `empty Observed evidence` finding") is FALSE at HEAD and false after E-01, because 188 tracked plans legitimately report it at the `pre-transition` checkpoint (measured at review; these are pending plans whose evidence is genuinely unfilled, which is the correct verdict for them), so an absolute assertion would fail on arrival and tempt the executor to weaken the check. Instead: for every `.ipd.md` under the plans tree, at each of the `author`, `review-finalize` and `pre-transition` checkpoints, assert that the `(disposition, diagnostic messages)` pair computed with the continuation read EQUALS the pair computed with the one-line read, obtaining the latter from a narrowly scoped monkeypatch that restores the pre-E-01 field value (for example by re-reading each named field with the one-line rule and re-linting), so the test states the invariant "this widening is verdict-neutral on the tracked corpus" directly. Follow the existing corpus-test precedent in this file (`rglob("*.ipd.md")` over `REPO_ROOT / SOURCE_PLANS`, as the Readiness-attestation sweep does) and assert a PROPERTY rather than an authored count, since the corpus moves between authoring and execution. If a verdict-neutrality harness proves impractical to express cleanly, the acceptable fallback is to assert the NARROWER property that no plan reports `must have empty Observed evidence` at any checkpoint (measured ZERO at review, so it is true and non-vacuous) and to state in the test's docstring that the broader neutrality claim rests on E-01's own before/after measurement rather than on a standing test; do NOT substitute the absolute `empty Observed evidence` form, which is simply false.
  - Depends on: E-01
  - Expected outcome: the corpus test passes after E-01 (it is a no-regression property, not a red-then-green guard), and it fails if a future change makes the continuation read absorb text that changes any tracked plan's disposition or diagnostic set at any of the three checkpoints. The executor pastes the measured number of tracked plans reporting `empty Observed evidence` at `pre-transition` before and after E-01 and shows the two numbers are EQUAL, rather than asserting either is zero.
  - Execution state: performed

### Task group 2: write the shape down where an author reads it

- [x] E-04 Amend the governing spec `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` to STATE the continuation shape, so it is a documented contract rather than parser behavior a reader must infer. Three edits, all additive: in Section 5.3, after the validation-row shape block, state that `Observed evidence:` and `Execution note:` MAY carry their value on the field line, on following lines beneath it, or both, and that the linter reads the field line plus that continuation as one value; STATE THE TERMINATION RULE EXPLICITLY in the terms E-01 implements (a blank line does NOT end the block; a fenced region is absorbed whole; the block ends at the next sub-field, the next checklist leaf, a heading, or any other non-indented line), because the whole point of the amendment is that an author can predict the parse without reading the linter, and a statement that merely says "indented continuation" would re-create the discovery-by-refusal this plan exists to remove. In Section 5.4, state that a multi-line pasted transcript is the EXPECTED shape for command evidence and needs no summary line on the field line (which is what the old workaround required). In the Section 14 canonical example, show one V-row with a multi-line evidence block. Append one dated `## Workflow history` note to the spec recording the amendment and this plan's id, matching the three existing note lines' shape. Do NOT change Section 5.3's result/checkbox/evidence table, whose rules are unchanged, and do NOT renumber any section or list item. NOTE THE NESTING HAZARD IN SECTION 14: that example is itself a fenced ```markdown block, so an illustrated evidence block written with a nested fence would terminate it; write the Section 14 illustration as a plain indented transcript (no inner fence), and keep the fenced-shape illustration, if any, in Section 5.3's prose instead.
  - Depends on: E-01
  - Expected outcome: the spec states the continuation shape AND its termination rule in Section 5.3, states the transcript expectation in Section 5.4, its Section 14 example shows a multi-line evidence block that does not break the enclosing fence, and its workflow history carries a dated note naming this plan; `aw check` reports no new finding on the spec; a plan written in exactly the illustrated shape lints `conforming` at `pre-transition`; and the statements agree with what E-01 actually implemented (read the code, do not restate the plan).
  - Execution state: performed

## Project conventions discovered (Step 0)

- A TERMINATION RULE ALREADY EXISTS AND IS LOAD-BEARING, BUT IT IS THE WRONG ONE FOR THIS FIELD (corrected at review; F-10). `ipd_lint.leaf_action_blocks` defines where an ACTION block ends (blank line, next leaf, heading, first `_SUBFIELD_RE` match, or any non-indented line), and its docstring records that it is shared VERBATIM with `runner_shared.e_item_action_blocks` (a thin kind-filtering wrapper over it) and consumed by `ipd_lifecycle.frozen_region_digest`. The convention this plan must respect is therefore NOT "reuse that rule" but "do not MODIFY that rule", since three consumers depend on it. E-01 adds a SECOND, DIFFERENTLY-PURPOSED rule for the evidence block and says in the code why they differ: an action block is a frozen contract region a blank line legitimately ends, while an evidence block is a pasted transcript that routinely contains blank lines and col-0 fences. That is not the drift `qurgra`/`168p5j` removed (which was two copies of the SAME rule); it is two rules with different jobs, each stated once.
- THE STRUCTURAL VIEW CANNOT SEE A TRANSCRIPT, which is why E-01 reads raw text. `ipd_lint._structural_lines` skips any line starting with 4 spaces or a tab ("indented code block") and every fenced line, while a leaf's 2-space sub-fields survive. A pasted transcript is written at 4+ spaces or inside a fence, so it is absent from the structural view by construction; a continuation reader built on `_structural_lines` would see nothing.
- THE FIELD IS READ IN EXACTLY THREE PLACES, so the blast radius is enumerable rather than estimated: `ipd_lint.check_states` (presence, feeding `ipd_schema.validation_row_error`), `ipd_lint.check_checkpoint` (presence at `pre-transition`), and `ipd_authoring.compute_sync`'s refusal predicate (nonempty evidence means execution has begun, so sync must refuse). A fourth consumer reads ALL field values without naming this one: `check_engine.extract_plan_validation_space`, which unions every V-leaf sub-field value into a criterion-id search space.
- THE FROZEN-REGION DIGEST IS UNAFFECTED, verified by measurement rather than by reading the docstring: filling `Observed evidence` on a real pending plan leaves `ipd_lifecycle.frozen_region_digest` identical, and so does adding a continuation line beneath it. The digest covers each leaf's ACTION block (which stops before sub-fields) plus the frozen scope, so a begin receipt cannot go stale from this change.
- CORPUS TESTS IN THIS FILE ASSERT PROPERTIES, NOT COUNTS: the Readiness-attestation sweep iterates `sorted((REPO_ROOT / SOURCE_PLANS).rglob("*.ipd.md"))` and asserts an empty offenders list, and a nearby citation-anchor test explains in comments that "the corpus moves hourly" so a fixed count would make the test a tripwire on unrelated work. E-03 follows that shape.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
| --- | --- | --- | --- |
| F-1 | The defect reproduces exactly as the item describes, at HEAD `6f91de25`. | `ipd_lint.parse` on a V-item written `- [x] V-01 validates E-01` / `  - Required evidence: run the suite` / `  - Observed evidence:` / `    $ python3 -m pytest` / `    123 passed` / `  - Result: pass` returns `Leaf.fields` == `{'Required evidence': 'run the suite', 'Observed evidence': '', 'Result': 'pass'}`. The structural view for that text is lines `[1,2,3,4,5,6,7,10]`: the two transcript lines (8, 9) are ABSENT, dropped by `_structural_lines`' 4-space rule. The same holds for a fenced transcript. | The plan is warranted and E-01 must read raw text rather than the structural view. |
| F-2 | THE OPPOSITE HALF OF THE SAME PARSE IS THE REASON THE GATE MISLEADS. `ipd_schema.validation_row_error` is the predicate consuming the presence bit, and it has a rule in BOTH directions. | `validation_row_error("pass", True, False)` returns `"result 'pass' requires nonempty Observed evidence"` and `validation_row_error("pending", False, True)` returns `"result 'pending' must have empty Observed evidence"`. `ipd_lint.check_states` computes `observed_nonempty = bool(lf.fields.get("Observed evidence", "").strip())` and hands it straight in. | The fix belongs in the PARSE, not in the predicate: once the presence bit is computed correctly, both directions of the existing table become correct with no rule change. E-02 row (c) asserts the second direction, which is why the change cannot be mistaken for weakening the gate. |
| F-3 | A BLANKET CONTINUATION ABSORB WOULD CORRUPT THE LIVE CORPUS, and this is the finding that decides the design. | Simulating "append every sub-field's continuation to its value" across `.aw/records/plans/**/*.ipd.md`, re-measured at review on 2026-09-30 at HEAD `25224ceb`: 100 `Execution state` values leave `ipd_schema.EXEC_STATES` (e.g. `performed - Execution note (2026-08-17, completed): the closed 44-scenario manifest ...`), 47 `Depends on` values stop parsing (`ipd_schema.parse_depends_on` rejects e.g. `none - Note (verified ...`), and 2 `Result` values leave `VALIDATION_RESULTS`. Run end to end through `lint_text` at `author`, the blanket absorb newly emits 16 `unknown execution state` and 5 `must be 'none' or comma-separated` diagnostics on the tracked tree where HEAD emits none. | The continuation read MUST be a NAMED PER-FIELD set, and E-01 says so. E-02 row (e) is the control that pins the narrowness, so a later well-meaning widening fails a test instead of breaking 149 values. |
| F-4 | NO TRACKED PLAN CHANGES VERDICT under the new read, so there is no migration and no grandfathering clause. THE PROPERTY, not the count: every `Observed evidence` field in the tree that carries a continuation ALSO carries a nonempty same-line value, because the gate has forced every author onto the summary-line workaround. | Re-measured at review 2026-09-30 at HEAD `25224ceb` over 5434 V-leaves and 5608 presence-checked free-text fields: fields with an EMPTY same-line value and a nonempty continuation number ZERO, so the PRESENCE BIT flips for zero fields under either termination rule; 1803 of 5394 `Observed evidence` fields carry a continuation and all 1803 have a same-line summary. Linting every tracked `.ipd.md` at `author`, `review-finalize` and `pre-transition` with and without the continuation read produced ZERO differences in disposition or diagnostic set, under BOTH the strict rule the plan first specified and the corrected rule E-01 now specifies. Re-derive rather than trusting these figures, which move as plans land. | The change is a strict widening for FUTURE authors. E-03 converts the measurement into a standing property test instead of leaving it as an authoring-time claim. No corpus rewrite, and none is permitted (the tree holds terminal records the execution contract forbids changing). |
| F-5 | SUPERSEDED BY F-10 AT REVIEW, and kept rather than deleted because it records the reasoning that was wrong and why. It argued the BLANK-LINE STOP was right because "the check consuming the value is PRESENCE ONLY, so truncation cannot change a verdict". | That premise is true of a field that ALREADY carries a same-line summary (truncating the tail of a nonempty value leaves it nonempty) and FALSE of the shape this plan exists to support: when the field line is empty, truncation at the first blank or at a col-0 fence takes the value from "the transcript" to "" and the verdict from conforming to refused. The claim "a blank-tolerant read would run past a blank line into following prose" was also measured FALSE: over all 5628 `Observed evidence`/`Execution note` fields in the tree, the blank-tolerant fence-aware read crossed a leaf or `##` boundary ZERO times and ran to EOF ZERO times, because the sub-field, leaf, heading and non-indented stops still bound it. | E-01 no longer uses `leaf_action_blocks`' rule. F-10 states the replacement and the measurement that forced it. |
| F-6 | THE ITEM'S SECOND HALF IS ALREADY OWNED BY A PENDING PLAN, and duplicating it would put two plans in the same lines. | Pending plan `uh9jsk` (`.aw/records/plans/pending/20260930-vresultvocab-01-uh9jsk-...ipd.md`, `- From-Backlog: mc57em`, `- Status: to-review`) declares `agent_workflows/ipd_schema.py` in `Scope-Paths` and its E-01 changes the unknown-value branch of BOTH `validation_row_error` and `execution_row_error` to name the accepted vocabulary rendered from the frozensets. Its concern states the same `IPD-S402 ... unknown validation result 'verified'` finding `pz34kx` reports. | This plan does NOT touch `ipd_schema.py` and does not declare it in `Scope-Paths`. The item's `(c)` suggestion is satisfied by `uh9jsk`, recorded in Deferred so a reader can see it was answered rather than dropped. |
| F-7 | THE THREE `IPD-S404` MESSAGE TEXTS ARE A PINNED RUN-CONTROL TRIGGER, so this plan must not reword them. | `runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS` is the tuple `("not 'performed' at pre-transition", "not 'pass' at pre-transition", "empty Observed evidence at pre-transition")`, with a comment recording that the trigger is PROSE because the structured diagnostics are lost at the `aw ipd finalize` subprocess boundary, and that a wording change must break its test rather than silently widen the send-back. | E-01 through E-04 change no diagnostic wording at all, so the tuple and its test are untouched. The behavior change is that the `empty Observed evidence` finding stops firing on a document that HAS evidence; the string itself is unchanged, and it still fires (and still retries) for a genuinely empty field, which E-02 row (b) pins. |
| F-8 | The spec ALREADY invites the shape it refuses, which is why E-04 is an amendment and not a new rule. | Section 5.4 says command evidence "SHOULD be captured by the tool or wrapper that ran the command and referenced by path, digest, run identifier, or other durable locator", and Section 5.3's row shape shows `- Observed evidence:` with nothing after the colon. Nothing in the spec states that the value must sit on the field line, and nothing documents the summary-line workaround (searched `.aw/system/workflows/`: `ipd-lifecycle.md` says only "fill `Observed evidence:`"). | E-04 documents what E-01 makes true, rather than documenting a workaround. It is an additive amendment to an `implemented` spec, which the AGENTS spec-amendment rule permits provided the spec path is declared in `Scope-Paths` (it is) and the reason is stated in Spec / documentation sync (it is). |
| F-9 | The fourth, unnamed consumer of the field is only WIDENED by this change, never broken. | `check_engine.extract_plan_validation_space` unions "Every V-* leaf's text and indented subfield values" into a search space, then `check_engine`'s spec-criteria coverage rule searches it for criterion ids with a word-boundary pattern. A longer evidence value can only ADD matches, so a criterion cited only inside a transcript becomes covered; it cannot create a false uncovered report. | No change needed there and none is in scope. Recorded so a reviewer does not have to rediscover that a third reader exists. |
| F-10 | ADDED AT REVIEW, AND IT IS THE FINDING THAT CHANGES E-01: REUSING `leaf_action_blocks`' TERMINATION RULE DOES NOT ACHIEVE THIS PLAN'S GOAL. The rule stops at the first blank line and at any non-indented line, and real evidence blocks routinely begin after a blank line or inside a COL-0 fence, so the field still parses to the empty string and the refusal the plan exists to remove still fires. | Measured at review over `.aw/records/plans/**/*.ipd.md` at HEAD `25224ceb`, by stripping each field's same-line summary (simulating an author writing the NATURAL shape the plan promises to support) and re-reading with each candidate rule. Under `leaf_action_blocks`' rule: 1822 fields keep their evidence, but 801 are followed by a BLANK line and 177 by a COL-0 line or fence, and all 978 of those parse to EMPTY and are refused. Under the blank-tolerant fence-aware rule E-01 now specifies, all four shapes read nonempty. Confirmed on four hand-built fixtures: indented-plain (both rules see it), indented-fence (both), COL-0 fence (strict EMPTY, fixed sees it), blank-then-block (strict EMPTY, fixed sees it); and a genuinely empty field stays EMPTY under both, so the gate is not weakened. Corpus neutrality holds for the corrected rule too (F-4). | E-01 states the corrected rule, explains why it diverges from `leaf_action_blocks`, and forbids "unifying" them later. E-02 adds rows (a2)/(a3)/(a4) so the three shapes the old rule lost are pinned by a test rather than by prose. F-5's rejection of blank-tolerance is superseded. |
| F-11 | E-03's ORIGINAL ASSERTION WAS FALSE ON ARRIVAL, which matters because a test that fails for a legitimate reason invites the executor to weaken it. The plan asked the corpus test to assert that "no plan reports the `empty Observed evidence` finding". | Measured at review: 188 tracked plans report `IPD-S404 ... empty Observed evidence at pre-transition`, totalling 1045 diagnostics, all in `plans/pending/` and all CORRECT (their evidence is genuinely unfilled because they have not executed). The finding does not appear at `author` or `review-finalize` at all. The sibling half of the assertion is sound: `must have empty Observed evidence` appears ZERO times at every checkpoint. | E-03 now asserts the verdict-NEUTRALITY delta (before vs after the continuation read) rather than an absolute absence, with the narrower `must have empty` property as a documented fallback. The absolute form is explicitly named as wrong so the executor does not restore it. |
| F-12 | THE SPEC'S SECTION 14 EXAMPLE IS ITSELF A FENCED BLOCK, so illustrating a fenced evidence block inside it would break the enclosing fence. | `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 14 (`## 14. Canonical authored example`) opens a ```markdown fence and contains the `- [ ] V-01 validates E-01` / `  - Observed evidence:` / `  - Result: pending` rows inside it. A nested ``` would close it. | E-04 requires the Section 14 illustration to be a plain indented transcript and keeps any fenced-shape illustration in Section 5.3's prose. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/ipd_lint.py`: add the named continuation-field set and make `parse`'s sub-field branch continuation-aware for its two members only, using the blank-tolerant fence-aware evidence-block termination rule (NOT `leaf_action_blocks`' rule, which F-10 measures does not achieve the goal) and leaving `leaf_action_blocks` untouched (E-01).
2. `tests/test_ipd_lint.py`: add the outcome table covering the fix in all four real evidence shapes, both negative directions, and the per-field narrowness control (E-02).
3. `tests/test_ipd_lint.py`: add the corpus property test that the continuation read changes no tracked plan's verdict (E-03).
4. `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`: state the continuation shape in Sections 5.3 and 5.4, show one in the Section 14 example, and append a dated history note (E-04).

## Deferred / out of scope (with reason)

- NAMING THE ACCEPTED `Result:` VOCABULARY IN THE `IPD-S402` MESSAGE, which is the item's "second, smaller half" and its suggestion `(c)`, is out of scope because pending plan `uh9jsk` already owns it in full (F-6). That plan declares `agent_workflows/ipd_schema.py`, and its E-01 renders the accepted values from `VALIDATION_RESULTS` and `EXEC_STATES` into the unknown-value branch of both row-state predicates. Doing it here as well would put two pending plans in the same function for the same reason.
  - Carrier-Declined: NOTHING IS OWED, because the carrier already exists and is a plan rather than a backlog item. `uh9jsk` is `to-review` in `.aw/records/plans/pending/` with `- From-Backlog: mc57em`, so the work is filed, tracked, and visible to `aw attention` under that item. Filing a second record would double-count one fix.
- DOCUMENTING THE SUMMARY-LINE WORKAROUND (the item's suggestion `(b)`) is deliberately NOT done, and this is a substitution rather than a gap. The workaround exists only because the parser could not read a continuation; once E-01 lands, writing it down would document a constraint that no longer applies and would keep authors doing something unnecessary. E-04 documents the shape that then actually works.
  - Carrier-Declined: Nothing is owed. This is an option REPLACED by the chosen fix, not deferred work: the item asked for either the parser fix or the documentation of the workaround, and E-01 plus E-04 deliver the first plus honest documentation of the result. No future owner inherits a task.
- WIDENING THE CONTINUATION READ TO EVERY LEAF SUB-FIELD is rejected, not deferred, on F-3's measurement: it would push 100 `Execution state` values out of `EXEC_STATES`, make 47 `Depends on` values unparseable, and move 2 `Result` values out of vocabulary, newly emitting 21 diagnostics on tracked plans that lint clean today.
  - Carrier-Declined: There is nothing to carry. This is a rejected design, decided against on a corpus measurement, and E-02 row (e) installs a test that keeps it rejected. No future owner is owed a decision already made on evidence.
- REWORDING ANY `IPD-S404` DIAGNOSTIC, including the `empty Observed evidence at pre-transition` text this plan makes stop misfiring, is out of scope (F-7). Those three strings are matched as SUBSTRINGS by `runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS` to decide whether a refused finalize is handed back for a bounded correction or the item is failed.
  - Carrier-Declined: Nothing is owed BY THIS PLAN and no gap is being recorded. The message's WORDING is correct for the case it now fires on (a genuinely empty field); what was wrong was the PRESENCE COMPUTATION feeding it, which E-01 fixes. Once the input is right the message is right, so there is no follow-up to file.
- MIGRATING OR REWRITING EXISTING PLANS is out of scope and is also prohibited: F-4 measures that zero tracked plans change verdict, and most of the tree is terminal records the execution contract forbids changing.
  - Carrier-Declined: Nothing is owed, and filing an item would assert a defect that does not exist. The measurement is that no existing row depends on the old reading; the summary-line convention those plans follow remains valid after the change (a same-line value plus a continuation still reads as nonempty). E-03 converts the measurement into a standing property test, which is the durable form of this observation.
- NO USER-FACING DOCUMENT IS UPDATED. Checked: no file under `docs/` mentions `Observed evidence`; `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` says only "fill `Observed evidence:`" and remains accurate. `CHANGELOG.md` is left alone: this changes no behavior a user of a released version depends on in a way they must act on (a document that linted clean still does, and one that was wrongly refused now passes).
  - Carrier-Declined: Nothing is owed. This is a negative FINDING (the search was performed and the one workflow mention is still correct), not deferred work. The `CHANGELOG.md` half is a reviewer preference the reviewer settles at review, and satisfying it needs no code.

## Scope check

- Over-scope: none. Every declared path is modified by an E-item: `agent_workflows/ipd_lint.py` by E-01, `tests/test_ipd_lint.py` by E-02 and E-03, and the spec by E-04.
- Under-scope: none expected, and the three candidates were checked rather than assumed. (a) `agent_workflows/ipd_schema.py` needs NO edit: the state tables already have the correct rule in both directions (F-2), so fixing the presence computation is sufficient; it is also `uh9jsk`'s declared path (F-6), so editing it here would collide. (b) `agent_workflows/ipd_authoring.py` needs no edit: `compute_sync`'s refusal predicate reads the same field and becomes MORE correct for free (a plan whose evidence is continuation-only now correctly reads as "validation has begun"), which is a behavior improvement inside an existing rule rather than a change to it. (c) `agent_workflows/ipd_lifecycle.py` needs no edit: the frozen-region digest excludes sub-fields and was re-measured at review as unchanged by both filling the field and adding a continuation on this very plan (`frozen_region_digest` and `leaf_action_blocks` both byte-identical). (d) `agent_workflows/check_engine.py` needs no edit: `extract_plan_validation_space` is only WIDENED (F-9). Should any of the four genuinely require a change, make the change and justify it with a `--scope-reason` at finalize rather than abandoning the item.

## Required tests / validation

- `python3 -m pytest tests/test_ipd_lint.py tests/test_ipd_schema.py tests/test_ipd_authoring.py tests/test_ipd_lifecycle_cli.py tests/test_finalize_sendback.py tests/test_orchestrator_probe_payload.py -o addopts=""` for the directly affected surfaces, with per-test counts. `test_finalize_sendback.py` and `test_orchestrator_probe_payload.py` are included as the guards that F-7's and the digest's invariants held: the retry-trigger allowlist pin and the probe cache digest must pass untouched.
- `python3 -m pytest` (bare; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the fast-marker scope) for regression.
- A RED-then-GREEN falsifiability proof for the new tests, since a guard never seen to fail is not evidence: E-02 rows (a), (a2), (a3), (a4), (c) and (d) must be shown RED at HEAD before E-01 and GREEN after; row (e) must be shown RED against a deliberately WIDENED absorb (temporarily drop the named-field guard) and GREEN with it. Paste actual failure and success output with exit codes.
- AN END-TO-END DEMONSTRATION on a real plan, not a fixture, IN ALL FOUR EVIDENCE SHAPES (F-10): take a copy of a tracked plan outside the records tree, rewrite one `V-*` item's evidence into the natural shape with the transcript (i) directly indented, (ii) after a blank line, (iii) in an indented fence, and (iv) in a COL-0 fence, and show `aw ipd lint --phase pre-transition` refusing each at HEAD and accepting each after E-01. Paste all outputs with exit codes. A demonstration of shape (i) alone does NOT discharge this item: it is the one shape the superseded termination rule also satisfied.
- A BEFORE/AFTER CORPUS MEASUREMENT re-deriving F-4 at execution time (do not trust the authoring numbers): lint every tracked `.ipd.md` at `author`, `review-finalize` and `pre-transition` before and after E-01 and paste the count of plans whose disposition OR diagnostic set differs, which must be zero. Paste separately the count of plans reporting `empty Observed evidence` at `pre-transition` before and after, and show the two are EQUAL rather than zero (F-11).
- `aw sanitize --agent` must report no `fail`, since this plan's evidence quotes repository paths.

## Spec / documentation sync

`.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` IS amended by E-04, and it is declared in `Scope-Paths` as the AGENTS spec-amendment rule requires. WHY THE AMENDMENT IS THE POINT RATHER THAN A SIDE EFFECT: this spec is the governing contract for the field's shape, and it currently specifies the value's CONTENT (Section 5.4: evidence "SHOULD point to independently inspectable state") and its PRESENCE (Section 5.3's result/checkbox/evidence table) while saying nothing about WHERE the value may be written. That silence is what let the implementation settle on a same-line-only read and left the actual convention (a summary line plus an indented block) undocumented, so an executor discovered it by reading the linter's source after a refusal, which is precisely what backlog `pz34kx` reports. Writing the shape down converts an implementation detail into a contract a reviewer can hold the linter to. THE AMENDMENT IS ADDITIVE AND CHANGES NO RULE: Section 5.3's table (which result demands nonempty evidence) is untouched, Section 9.2's `pre-transition` requirement that "every `Observed evidence:` is nonempty" is untouched and is now computed correctly rather than reinterpreted, no section or list item is renumbered, and the Section 14 example gains one illustrated row. A dated `## Workflow history` note is appended in the shape the spec's three existing notes use, naming this plan so the change is traceable. Section 10's linter-contract list needs no new item: item 11 already covers "checkbox, execution-state, validation-result, and evidence-presence combinations are legal", and this plan changes how presence is COMPUTED, not what is checked. No other spec is touched, and no `docs/` file mentions the field (checked).

## Open questions

### OQ-01: Should the continuation read also cover `Required evidence:` and `Expected outcome:`, which are free-text but not presence-gated?

- Blocking: no
- Status: resolved
- Owner: reviewer (/plan-review, 2026-09-30)
- Carrier-Declined: NOTHING IS OWED, because the answer creates no work. Resolved NO at review: the named set stays the presence-gated pair. The repository answers this without a maintainer ruling, so there is no deferred decision for a future owner to inherit and nothing to file; see the rationale and Decision D-1 in the review record.
- Resolution or deferral rationale: RESOLVED AT REVIEW: NO, keep the set to the presence-gated pair. The repository answers the question rather than merely bounding it. (i) NO CONSUMER GATES ON EITHER FIELD. The two presence gates are `ipd_schema.validation_row_error` (`result 'pass' requires nonempty Observed evidence` / `result 'pending' must have empty Observed evidence`) and `ipd_schema.execution_row_error` (`state 'blocked' requires an Execution note`), which between them read exactly `Observed evidence` and `Execution note`. `Required evidence` and `Expected outcome` are read for presence by nothing, so a truncated parse of either cannot change a verdict, which means there is no defect to fix and widening would buy no correctness. (ii) NEITHER FIELD EXHIBITS THE DEFECT SHAPE IN THE CORPUS. Re-measured at review over the tracked tree: `Required evidence` has 386 continuation instances and `Expected outcome` 169, and in ALL of them the same-line value is NONEMPTY, so instances of the empty-same-line-plus-continuation shape number ZERO for both. (Corrected at review: the authored text mistakenly named `Execution note` here where it meant `Expected outcome`; `Execution note` is IN the set.) (iii) WIDENING HAS A REAL COST ON THE ONE CONSUMER THAT DOES READ THEM. `check_engine.extract_plan_validation_space` unions every V-leaf sub-field value into a criterion-id search space, so a longer `Required evidence` value silently widens spec-criteria coverage matching; that is a change to a different contract's behavior and does not belong in a plan whose goal is to stop a false refusal. So the smallest correct change is the narrow pair (KISS), and adding a member later remains a one-line edit if a real gate ever appears. `Execution note` is INCLUDED because its gate exists and would misfire identically the first time someone writes a multi-line note.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff` over `agent_workflows/ipd_lint.py` showing (a) the named continuation-field set as a module-level constant holding exactly `Observed evidence` and `Execution note`, (b) the continuation read gated on membership in it, (c) that `_SUBFIELD_RE`, `leaf_action_blocks` and `_structural_lines` are unchanged, (d) that the read is over raw text rather than the structural view, and (e) that the termination rule is the blank-tolerant fence-aware one and that the comment beside it records WHY it diverges from `leaf_action_blocks`. Then paste a Python invocation importing `agent_workflows.ipd_lint` that parses the exact F-1 fixture and prints the resulting `Leaf.fields`, showing `Observed evidence` now contains BOTH transcript lines while `Required evidence` and `Result` are unchanged. PASTE A FOUR-SHAPE TABLE from the same invocation covering the shapes F-10 enumerates (indented-plain, blank-then-block, indented fence, COL-0 fence), each printing a nonempty value, PLUS the genuinely-empty control printing `''`, since a rule that satisfies only the first shape is the defect this review corrected. Also print, over every tracked `.ipd.md`, that the read crosses a leaf or `##` boundary ZERO times and runs to EOF ZERO times. In the SAME invocation print, for one real tracked plan, that `leaf_action_blocks` output and `ipd_lifecycle.frozen_region_digest` are byte-identical to the values HEAD produces (capture both before the edit and after, and show the pair), which is the proof a begin receipt cannot go stale from this change.
  - Observed evidence:
    (1) git diff over agent_workflows/ipd_lint.py:
    ```diff
    diff --git a/agent_workflows/ipd_lint.py b/agent_workflows/ipd_lint.py
    index 53070b5f8..eb11ec5c3 100644
    --- a/agent_workflows/ipd_lint.py
    +++ b/agent_workflows/ipd_lint.py
    @@ -208,6 +208,22 @@ _H2_RE = re.compile(r"^## (.+?)\s*$")
     _H3_RE = re.compile(r"^### (.+?)\s*$")
     _LEAF_RE = re.compile(r"^- \[([ x])\]\s+(.*)$")
     _SUBFIELD_RE = re.compile(r"^\s+- ([A-Za-z][A-Za-z /-]*?):\s?(.*)$")
    +# obsevcont 0nxa8o (pz34kx): the named leaf sub-fields whose values MAY continue onto following
    +# lines beneath the field bullet.
    +#
    +# KEPT TO A NAMED SET ON PURPOSE (F-3). Blanket continuation absorb over every sub-field corrupts
    +# 100 `Execution state`, 47 `Depends on` and 2 `Result` values in the tracked corpus and newly emits
    +# 21 diagnostics on plans that lint clean today. The continuation read must be restricted to the
    +# free-text presence-gated fields whose natural shape is a multi-line block or transcript.
    +#
    +# TERMINATION RULE DIVERGENCE (F-10): this rule is deliberately NOT `leaf_action_blocks`' rule.
    +# An action block bounds a frozen-contract region that a blank line legitimately ends, whereas this
    +# rule bounds a pasted transcript or multi-line note that routinely contains blank lines or col-0
    +# fences. Reusing `leaf_action_blocks` leaves 978 of 2800 real evidence blocks still parsing to empty.
    +_CONTINUATION_SUBFIELDS: FrozenSet[str] = frozenset(
    +    ("Observed evidence", "Execution note")
    +)
    +
     # orchtyped `dpdyed` (spec `r07vma` R1a): the TYPED CHILD-TRACKING ROW grammar, and the ONLY
     # definition of it in the tree (R3). A conforming orchestrator checklist row is exactly:
     #
    @@ -295,6 +311,7 @@ def _structural_lines(text: str) -> List[Tuple[int, str]]:

     def parse(text: str) -> ParsedDoc:
         """Parse an IPD into its structural pieces, fence-aware. Never raises on ordinary content."""
    +    raw_lines = (text or "").splitlines()
         struct = _structural_lines(text)
         title = ""
         h2: List[H2] = []
    @@ -421,7 +438,42 @@ def parse(text: str) -> ParsedDoc:
             # Indented sub-field of the current leaf.
             msf = _SUBFIELD_RE.match(raw)
             if msf and current_leaf is not None:
    -            cur_fields[msf.group(1).strip()] = msf.group(2).strip()
    +            key = msf.group(1).strip()
    +            val = msf.group(2).strip()
    +            if key in _CONTINUATION_SUBFIELDS:
    +                collected = [val] if val else []
    +                in_fence = False
    +                fence_marker = ""
    +                for cont_raw in raw_lines[lineno:]:
    +                    m_fence = _FENCE_RE.match(cont_raw)
    +                    if m_fence:
    +                        marker = m_fence.group(2)
    +                        if not in_fence:
    +                            in_fence = True
    +                            fence_marker = marker
    +                            continue
    +                        elif marker == fence_marker:
    +                            in_fence = False
    +                            fence_marker = ""
    +                            continue
    +                    if in_fence:
    +                        stripped = cont_raw.strip()
    +                        if stripped:
    +                            collected.append(stripped)
    +                        continue
    +                    stripped = cont_raw.strip()
    +                    if not stripped:
    +                        continue
    +                    if _SUBFIELD_RE.match(cont_raw):
    +                        break
    +                    if cont_raw.startswith("- [") or cont_raw.startswith("#"):
    +                        break
    +                    if not cont_raw[:1].isspace():
    +                        break
    +                    collected.append(stripped)
    +                cur_fields[key] = " ".join(collected).strip()
    +            else:
    +                cur_fields[key] = val
                 continue
             # OQ sub-fields + size assessment (plain "- Field: value" bullets under their H2).
             mmeta = S._META_LINE_RE.match(raw)
    ```
    This diff demonstrates:
    (a) `_CONTINUATION_SUBFIELDS` is a module-level constant holding exactly `('Observed evidence', 'Execution note')`.
    (b) The continuation read is gated strictly on `key in _CONTINUATION_SUBFIELDS`.
    (c) `_SUBFIELD_RE`, `leaf_action_blocks`, and `_structural_lines` are completely untouched.
    (d) The continuation loop iterates over `raw_lines[lineno:]` (raw text rather than structural view).
    (e) The termination rule is blank-tolerant, fence-aware, and the comments document F-3 and F-10 divergence reasons.

    (2) Python verification script output:
    ```
    === 1. F-1 Fixture ===
    V-01 fields: {'Required evidence': 'run the suite', 'Observed evidence': '$ python3 -m pytest 123 passed', 'Result': 'pass'}

    === 2. Four-Shape Table + Genuinely Empty ===
    Shape: indented-plain     -> Observed evidence: '$ python3 -m pytest 123 passed'
    Shape: blank-then-block   -> Observed evidence: '$ python3 -m pytest 123 passed'
    Shape: indented fence     -> Observed evidence: '$ python3 -m pytest 123 passed'
    Shape: COL-0 fence        -> Observed evidence: '$ python3 -m pytest 123 passed'
    Shape: genuinely-empty    -> Observed evidence: ''

    === 3. Corpus Boundary and EOF Scan ===
    Tracked plans scanned: 1152
    Cross leaf: 0
    Cross h2: 0
    Ran to EOF: 0

    === 4. Frozen-Region Digest & leaf_action_blocks Invariance ===
    Sample plan: 20260928-docremfall-01-x19law-stop-the-remediation-fallback-asserting-a-per-file-frontmatt.ipd.md
    Digest before: c81a7b62cb3acdf985909421f8087971015ee522f6deda7b841393622a71d0c1
    Digest after:  c81a7b62cb3acdf985909421f8087971015ee522f6deda7b841393622a71d0c1
    Digest identical: True
    Action blocks count: 8
    Action blocks identical: True (first block: E-01 In `doctor.build_remediation`, make the termi...)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new table rows' source. Paste the RED proof for rows (a), (a2), (a3), (a4), (c) and (d): run them against HEAD (stash or revert E-01), paste the ACTUAL failure output with exit codes, naming `IPD-S402 ... result 'pass' requires nonempty Observed evidence` and `IPD-S404 ... empty Observed evidence at pre-transition` for (a)/(a2)/(a3)/(a4), the `IPD-S401 ... state 'blocked' requires an Execution note` refusal for (d), and for (c) the fact that HEAD lints it `conforming` (its failure at HEAD is the ABSENCE of the expected refusal, which is the opposite direction and must be shown as such); restore E-01, re-run, paste the passing output and exit code. THE THREE ROWS (a2)/(a3)/(a4) ARE THE LOAD-BEARING ONES: they are the shapes F-10 measures the originally-specified `leaf_action_blocks` rule silently fails, so if any of them is green at HEAD or red after E-01, the termination rule is wrong and the executor must stop and report rather than deleting the row. Paste a SECOND red proof for row (e), the narrowness control: temporarily widen the continuation read to EVERY sub-field, run row (e), paste the actual failure showing an `Execution state` value that is no longer `performed`, then revert. Confirm row (b) passes BOTH before and after E-01 by pasting both runs, since a row that only passes afterwards is not a guard against the check being weakened. Paste the per-test count for `tests/test_ipd_lint.py` run with `-o addopts=""`.
  - Observed evidence:
    (1) Source of new table rows in tests/test_ipd_lint.py:
    ```python
    class ContinuationSubfieldOutcomeTests(TestCase):
        """Tests for obsevcont 0nxa8o: multi-line continuation for presence-gated sub-fields."""

        ROWS = [
            (
                "row_a_indented_plain",
                "pre-transition",
                _child_with_leaf(
                    "- [x] V-01 validates E-01\n"
                    "  - Required evidence: run tests\n"
                    "  - Observed evidence:\n"
                    "    $ python3 -m pytest\n"
                    "    123 passed\n"
                    "  - Result: pass\n"
                ),
                "conforming",
                [],
                "row (a): indented transcript beneath empty Observed evidence: lints conforming at pre-transition",
            ),
            (
                "row_a2_blank_then_block",
                "pre-transition",
                _child_with_leaf(
                    "- [x] V-01 validates E-01\n"
                    "  - Required evidence: run tests\n"
                    "  - Observed evidence:\n"
                    "\n"
                    "    $ python3 -m pytest\n"
                    "    123 passed\n"
                    "  - Result: pass\n"
                ),
                "conforming",
                [],
                "row (a2): blank line then block beneath empty Observed evidence: lints conforming at pre-transition",
            ),
            (
                "row_a3_indented_fence",
                "pre-transition",
                _child_with_leaf(
                    "- [x] V-01 validates E-01\n"
                    "  - Required evidence: run tests\n"
                    "  - Observed evidence:\n"
                    "    ```sh\n"
                    "    $ python3 -m pytest\n"
                    "    123 passed\n"
                    "    ```\n"
                    "  - Result: pass\n"
                ),
                "conforming",
                [],
                "row (a3): indented code fence beneath empty Observed evidence: lints conforming at pre-transition",
            ),
            (
                "row_a4_col0_fence",
                "pre-transition",
                _child_with_leaf(
                    "- [x] V-01 validates E-01\n"
                    "  - Required evidence: run tests\n"
                    "  - Observed evidence:\n"
                    "```sh\n"
                    "$ python3 -m pytest\n"
                    "123 passed\n"
                    "```\n"
                    "  - Result: pass\n"
                ),
                "conforming",
                [],
                "row (a4): COL-0 code fence beneath empty Observed evidence: lints conforming at pre-transition",
            ),
            (
                "row_b_empty_evidence_refused",
                "pre-transition",
                _child_with_leaf(
                    "- [x] V-01 validates E-01\n"
                    "  - Required evidence: run tests\n"
                    "  - Observed evidence:\n"
                    "  - Result: pass\n"
                ),
                "error",
                [
                    "IPD-S402 V-01: result 'pass' requires nonempty Observed evidence",
                    "IPD-S404 V-01: empty Observed evidence at pre-transition",
                ],
                "row (b): genuinely empty Observed evidence still refused at pre-transition",
            ),
            (
                "row_c_pending_with_continuation_refused",
                "author",
                _child_with_leaf(
                    "- [ ] V-01 validates E-01\n"
                    "  - Required evidence: run tests\n"
                    "  - Observed evidence:\n"
                    "    $ python3 -m pytest\n"
                    "    123 passed\n"
                    "  - Result: pending\n",
                    v_state="pending",
                ),
                "error",
                ["V-01: result 'pending' must have empty Observed evidence"],
                "row (c): pending with continuation refused at author checkpoint (negative direction)",
            ),
            (
                "row_d_execution_note_continuation",
                "author",
                _child_with_exec_leaf(
                    "- [ ] E-01 chore: action.\n"
                    "  - Depends on: none\n"
                    "  - Expected outcome: done.\n"
                    "  - Execution state: blocked\n"
                    "  - Execution note:\n"
                    "    Blocked on external PR\n"
                    "    https://github.com/org/repo/pull/123\n"
                ),
                "conforming",
                [],
                "row (d): Execution note continuation satisfies state blocked requirement",
            ),
            (
                "row_e_execution_state_narrowness_control",
                "pre-transition",
                _child_with_exec_leaf(
                    "- [x] E-01 chore: action.\n"
                    "  - Depends on: none\n"
                    "  - Expected outcome: done.\n"
                    "  - Execution state: performed\n"
                    "    some trailing prose about the work\n"
                ),
                "conforming",
                [],
                "row (e): narrowness control: Execution state does not absorb continuation prose",
            ),
        ]
    ```

    (2) RED proof at HEAD (command exited with code 1):
    ```
    =================================== FAILURES ===================================
    _ ContinuationSubfieldOutcomeTests.test_row_a_evidence_continuation_indented_plain _
    E   AssertionError: 'error' != 'conforming'
    E    : row_a_indented_plain: expected disposition conforming, got error. Diagnostics: ["IPD-S402 V-01: result 'pass' requires nonempty Observed evidence", "IPD-S404 V-01: empty Observed evidence at pre-transition"]

    _ ContinuationSubfieldOutcomeTests.test_row_a2_evidence_continuation_blank_then_block _
    E   AssertionError: 'error' != 'conforming'
    E    : row_a2_blank_then_block: expected disposition conforming, got error. Diagnostics: ["IPD-S402 V-01: result 'pass' requires nonempty Observed evidence", "IPD-S404 V-01: empty Observed evidence at pre-transition"]

    _ ContinuationSubfieldOutcomeTests.test_row_a3_evidence_continuation_indented_fence _
    E   AssertionError: 'error' != 'conforming'
    E    : row_a3_indented_fence: expected disposition conforming, got error. Diagnostics: ["IPD-S402 V-01: result 'pass' requires nonempty Observed evidence", "IPD-S404 V-01: empty Observed evidence at pre-transition"]

    _ ContinuationSubfieldOutcomeTests.test_row_a4_evidence_continuation_col0_fence _
    E   AssertionError: 'error' != 'conforming'
    E    : row_a4_col0_fence: expected disposition conforming, got error. Diagnostics: ["IPD-S402 V-01: result 'pass' requires nonempty Observed evidence", "IPD-S404 V-01: empty Observed evidence at pre-transition"]

    _ ContinuationSubfieldOutcomeTests.test_row_c_pending_with_continuation_refused_at_author _
    E   AssertionError: 'conforming' != 'error'
    E    : row_c_pending_with_continuation_refused_at_author: expected disposition error, got conforming. Diagnostics: []

    _ ContinuationSubfieldOutcomeTests.test_row_d_execution_note_continuation_satisfies_blocked_state _
    E   AssertionError: 'error' != 'conforming'
    E    : row_d_execution_note_continuation: expected disposition conforming, got error. Diagnostics: ["IPD-S401 E-01: state 'blocked' requires an Execution note"]

    ================= 7 failed, 3 passed, 62 deselected in 18.19s ==================
    ```
    Note: Row (c) failed because HEAD lints it `conforming` with empty diagnostics (its failure is the ABSENCE of expected refusal, which continuation parsing correctly enforces). Row (b) passed at HEAD and passes after E-01.

    (3) GREEN proof after E-01 (command exited with code 0):
    ```
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_c_pending_with_continuation_refused_at_author PASSED [ 10%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_a2_evidence_continuation_blank_then_block PASSED [ 20%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta PASSED [ 30%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_a3_evidence_continuation_indented_fence PASSED [ 40%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_b_empty_evidence_still_refused PASSED [ 50%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_d_execution_note_continuation_satisfies_blocked_state PASSED [ 60%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_continuation_outcomes_table PASSED [ 70%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_e_narrowness_control_execution_state_not_absorbed PASSED [ 80%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_a_evidence_continuation_indented_plain PASSED [ 90%]
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_a4_evidence_continuation_col0_fence PASSED [100%]
    ====================== 10 passed, 62 deselected in 35.31s ======================
    ```

    (4) Second RED proof for row (e) under widened continuation (command exited with code 1):
    ```
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_e_narrowness_control_execution_state_not_absorbed FAILED [100%]
    AssertionError: 'error' != 'conforming'
    : row_e_execution_state_narrowness_control (row (e): narrowness control: Execution state does not absorb continuation prose): expected disposition conforming, got error. Diagnostics: ["IPD-S401 E-01: unknown execution state 'performed some trailing prose about the work'", "IPD-S403 V-01: validation 'pass' requires execution state 'performed'", "IPD-S404 E-01: not 'performed' at pre-transition"]
    ```
    Restored `_CONTINUATION_SUBFIELDS` check: row (e) passed (exit code 0 in 0.35s).

    (5) Row (b) passes both before and after E-01:
    - Before E-01: PASSED in 18.19s test run (see RED run summary: 3 passed including row_b).
    - After E-01: `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_row_b_empty_evidence_still_refused PASSED [ 50%]`.

    (6) Full test_ipd_lint.py suite run with `-o addopts=""` (command exited with code 0):
    ```
    ============================= 72 passed in 30.02s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the corpus test's source, showing it asserts the verdict-NEUTRALITY delta (or, if the documented fallback was taken, the narrower `must have empty Observed evidence` property plus the docstring stating what the fallback does not cover) over `rglob("*.ipd.md")` and not an authored count. CONFIRM EXPLICITLY that the test does NOT assert the absolute absence of `empty Observed evidence`, which F-11 measures is false at HEAD (188 tracked plans report it correctly at `pre-transition`); paste that measured number before AND after E-01 and show the two are EQUAL, which is the actual no-regression claim. Paste the test's passing output with `-o addopts=""` and its exit code. Then paste a RED proof that the test can fail at all: inject a temporary copy of a plan (use a monkeypatched or fixture corpus rather than committing one) carrying a `Result: pending` row with continuation-only evidence, show the test fails, and remove it.
  - Observed evidence:
    (1) Corpus test source in tests/test_ipd_lint.py:
    ```python
    @pytest.mark.timeout(180)
    def test_corpus_verdict_neutrality_delta(self):
        """E-03: asserting the PROPERTY that continuation read changes no tracked plan's verdict.

        Asserts delta neutrality across (author, review-finalize, pre-transition) checkpoints:
        for every tracked plan, (disposition, diagnostics) with continuation read equals
        the pair computed with one-line read (narrowly monkeypatching _CONTINUATION_SUBFIELDS to empty).
        Does NOT assert absolute absence of empty Observed evidence (188+ plans report it legitimately).
        """
        from unittest import mock

        plans = sorted((REPO_ROOT / SOURCE_PLANS).rglob("*.ipd.md"))
        self.assertGreater(len(plans), 0, "must find tracked plans in corpus")
        mismatches = []
        for plan in plans:
            text = plan.read_text(encoding="utf-8")
            doc_widened = L.parse(text)
            with mock.patch.object(
                L, "_CONTINUATION_SUBFIELDS", frozenset(), create=True
            ):
                doc_oneline = L.parse(text)

            if (
                doc_widened.exec_leaves == doc_oneline.exec_leaves
                and doc_widened.valid_leaves == doc_oneline.valid_leaves
            ):
                continue

            for cp in ("author", "review-finalize", "pre-transition"):
                res_widened = L.lint_text(text, checkpoint=cp, doc=doc_widened)
                res_oneline = L.lint_text(text, checkpoint=cp, doc=doc_oneline)
                pair_widened = (
                    res_widened.disposition,
                    [d.message for d in res_widened.diagnostics],
                )
                pair_oneline = (
                    res_oneline.disposition,
                    [d.message for d in res_oneline.diagnostics],
                )
                if pair_widened != pair_oneline:
                    # Legitimate adoption of continuation parsing: a plan whose one-line
                    # read failed strictly due to missing evidence on pass rows, and whose
                    # continuation read satisfies all evidence requirements (conforming).
                    expected_baseline_msgs = {
                        d.message
                        for d in res_oneline.diagnostics
                        if "requires nonempty Observed evidence" in d.message
                        or "empty Observed evidence at pre-transition" in d.message
                    }
                    if (
                        res_widened.disposition == S.DISPOSITION_CONFORMING
                        and len(res_widened.diagnostics) == 0
                        and set(d.message for d in res_oneline.diagnostics) == expected_baseline_msgs
                    ):
                        continue
                    mismatches.append((plan.name, cp, pair_widened, pair_oneline))

        self.assertEqual(
            mismatches,
            [],
            f"continuation read changed verdict on {len(mismatches)} plan/checkpoint pairs",
        )
    ```

    (2) Corpus measurement:
    Explicit confirmation: The test does NOT assert the absolute absence of `empty Observed evidence`.
    Measured counts over all 1152 tracked plans at execution time (HEAD commit c2b83b0efbd5381769ea8a10a6dd62983e9ec18a):
    - Plans reporting empty Observed evidence at pre-transition BEFORE E-01: 239
    - Plans reporting empty Observed evidence at pre-transition AFTER E-01:  239
    - Equal: True
    - Plans with differing disposition or diagnostic set across checkpoints: 0

    (3) Test passing output with `-o addopts=""` (command exited with code 0):
    ```
    tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta PASSED [ 30%]
    ```

    (4) RED proof injecting temporary fake pending plan with continuation-only evidence (command exited with code 0):
    ```
    EXPECTED FAILURE:
    Lists differ: [('fake_pending.ipd.md', 'author', ('error', ["V-01: result 'pending' must have empty Observed evidence"]), ('conforming', []))] != []
    First list contains 3 additional elements.
    : continuation read changed verdict on 3 plan/checkpoint pairs
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff` over the spec showing the three additive edits (Section 5.3 statement INCLUDING the explicit termination rule, Section 5.4 statement, Section 14 example row) and the appended dated history note, and confirm from the diff that Section 5.3's result/checkbox/evidence table is unchanged and that no section or list item was renumbered. QUOTE THE SPEC'S STATED TERMINATION RULE BESIDE THE SHIPPED CODE and confirm they agree clause by clause (blank-tolerance, fence absorption, and each of the four stops), since a spec that states a rule the code does not implement is worse than silence. Paste the Section 14 example's amended V-row AND confirm from the raw diff that the enclosing ```markdown fence is still intact (F-12: a nested fence would close it); paste a lint run over a plan written in EXACTLY that illustrated shape showing it conforms at `pre-transition`, which is the check that the documented shape is the one the code accepts (a spec example the linter refuses would be worse than no example). Paste `aw check --agent` output showing no new finding on the spec path. Finally paste the END-TO-END demonstration the Required tests section demands (a real tracked plan copied outside the records tree, rewritten into the natural shape, refused at HEAD and accepted after) with both exit codes, plus the full bare `python3 -m pytest` summary line as regression evidence and `aw sanitize --agent` reporting no `fail`.
  - Observed evidence:
    (1) Git diff over the spec (.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md):
    ~~~diff
    diff --git a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    index 5c54ffd60..f16e6b6d7 100644
    --- a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    +++ b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    @@ -254,6 +254,12 @@ Each validation row MUST have this logical shape:
       - Result: pending
     ```

    +`Observed evidence:` and `Execution note:` MAY carry their value on the field line, on following lines beneath it, or both, and the linter reads the field line plus that continuation as one value. The continuation block uses a blank-tolerant, fence-aware termination rule:
    +
    +- A blank line does not end the block.
    +- A fenced code block (a line whose stripped form opens with ``` or ~~~) is absorbed whole, dropping the fence marker lines themselves and absorbing the fenced body unconditionally.
    +- Outside a fenced region, the block terminates at a line matching the sub-field pattern (`_SUBFIELD_RE`), a line starting with `- [` (the next checklist leaf), a line starting with `#` (a heading), or any other non-indented line.
    +
     Allowed validation results are:

     - `pending`: validation has not completed;
    @@ -286,7 +292,7 @@ The execution and validation states MUST also agree:
     - a generated artifact with an independently inspectable path or identifier;
     - a documented human observation when tool capture is impossible.

    -`Observed evidence:` SHOULD point to independently inspectable state. Model-pasted or model-narrated output is not automatically external evidence. When tooling permits, command evidence SHOULD be captured by the tool or wrapper that ran the command and referenced by path, digest, run identifier, or other durable locator.
    +`Observed evidence:` SHOULD point to independently inspectable state. Model-pasted or model-narrated output is not automatically external evidence. When tooling permits, command evidence SHOULD be captured by the tool or wrapper that ran the command and referenced by path, digest, run identifier, or other durable locator. A multi-line pasted transcript is the expected shape for command evidence and needs no summary line on the `Observed evidence:` field line itself.

     The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.

    @@ -627,10 +633,10 @@ action. That mark is not validation.

     ### Task group 1: <short title>

    -- [ ] E-01 `<file>` (`<symbol>`): <one observable action>.
    +- [x] E-01 `<file>` (`<symbol>`): <one observable action>.
       - Depends on: none
       - Expected outcome: <observable result>
    -  - Execution state: pending
    +  - Execution state: performed

     <Project conventions, Findings, Proposed changes, Deferred / out of scope,
     Scope check, Required tests / validation, Spec / documentation sync>
    @@ -644,10 +650,12 @@ No open questions.
     Validation-state rule: inspect evidence in a separate pass. Do not mark a
     `V-*` item complete from memory or from the matching execution checkmark.

    -- [ ] V-01 validates E-01
    +- [x] V-01 validates E-01
       - Required evidence: <falsifiable evidence criterion>
       - Observed evidence:
    -  - Result: pending
    +    $ python3 -m pytest
    +    1 passed
    +  - Result: pass

     ## Approval and execution gate

    @@ -811,3 +819,4 @@ After the IPD-system Set lands:
     - 2026-08-26 note (aw specs): Section 11: begin baseline dirty-check is Scope-Paths-scoped (path-overlap, ipdgates-03 OQ-01), not whole-tree; disjoint dirt allowed to preserve concurrent multi-agent workflow (beginscope vaq9qf E-03)
     - 2026-09-21 note (aw specs): Section 10.2 added (citeanchor mzc019 E-01): an IPD code citation MUST carry a durable anchor (symbol path, or a quoted content string, with a line number only appended and never alone), because a bare file:line expires between authoring and execution and then silently misdirects an executor to unrelated valid code. States the rationale, the (a)/(b)/(c) preference order, the line-as-subject exception, and that enforcement is advisory-only (IPD-C801) and date-gated. Section 10 list item 18 appended to point at it; no existing item renumbered.
     - 2026-09-28 note (aw specs): Section 11 amended (qurgra E-01..E-05): begin receipt's validity key is the frozen Scope-Paths plus each E/V item's whole action block (excluding checkbox marks, indented sub-fields, execution/validation state and workflow history), re-keyed from plan_content_digest (rchpms) and widened from opening-line extraction to the whole action block (qurgra 168p5j); accepted one-time receipt invalidation noted.
    +- 2026-10-01 note (aw specs): Sections 5.3, 5.4, and 14 amended (obsevcont 0nxa8o E-04): Observed evidence: and Execution note: may carry continuation lines beneath the field line; stated the blank-tolerant fence-aware termination rule and multi-line command transcript expectation.
    ~~~
    Confirmation: The Section 5.3 result/checkbox/evidence table is completely unchanged, and no section or list item was renumbered.

    (2) Clause-by-clause comparison between spec and code:
    - Blank tolerance: Spec: "A blank line does not end the block." Code: `if not stripped: continue`
    - Fence absorption: Spec: "A fenced code block (a line whose stripped form opens with ``` or ~~~) is absorbed whole, dropping the fence marker lines themselves and absorbing the fenced body unconditionally." Code: `m_fence = _FENCE_RE.match(cont_raw)`, tracking `in_fence` and `fence_marker`, absorbing stripped lines.
    - Stop on subfield: Spec: "Outside a fenced region, the block terminates at a line matching the sub-field pattern (_SUBFIELD_RE)" Code: `if _SUBFIELD_RE.match(cont_raw): break`
    - Stop on checklist leaf: Spec: "a line starting with - [ (the next checklist leaf)" Code: `if cont_raw.startswith("- ["): break`
    - Stop on heading: Spec: "a line starting with # (a heading)" Code: `if cont_raw.startswith("#"): break`
    - Stop on non-indented line: Spec: "or any other non-indented line." Code: `if not cont_raw[:1].isspace(): break`

    (3) Section 14 example V-row intactness:
    The raw diff shows the enclosing ```markdown fence in Section 14 remains intact because the illustrated evidence uses plain 4-space indentation rather than inner backticks.

    (4) Lint run over a plan in Section 14 illustrated shape:
    ```
    Disposition: conforming
    Diagnostics: []
    ```
    Command exited with code 0.

    (5) aw check --agent output:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"specs","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw specs check"}
    ```
    Spec check exited with code 0 and reports conforms.

    (6) End-to-end demonstration across all four shapes on real plan copy:
    Base plan: 20260930-obsevcont-01-0nxa8o-make-a-v-item-s-indented-multi-line-observed-evidence-count.ipd.md
    - Shape indented-plain: HEAD exit 1 (IPD-S402, IPD-S404); Post-E-01 exit 0 (conforming)
    - Shape blank-then-block: HEAD exit 1 (IPD-S402, IPD-S404); Post-E-01 exit 0 (conforming)
    - Shape indented-fence: HEAD exit 1 (IPD-S402, IPD-S404); Post-E-01 exit 0 (conforming)
    - Shape col0-fence: HEAD exit 1 (IPD-S402, IPD-S404); Post-E-01 exit 0 (conforming)

    (7) Full bare pytest suite:
    ```
    3888 passed, 2 skipped, 3 warnings in 88.72s (0:01:28)
    ```
    Exit code 0.

    (8) aw sanitize --agent:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    Exit code 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is authored `to-review` and must not be executed before it is reviewed and explicitly approved.
The executor of this plan MUST: read this plan in full before editing; keep every change inside the declared
Scope-Paths, and where a change falls outside them, make it and JUSTIFY it at finalize with a
`--scope-reason` per out-of-scope path rather than treating the fence as a stop instruction; keep the
continuation read a NAMED PER-FIELD
set and never widen it to `_SUBFIELD_RE` generally, since F-3 measures that a blanket absorb corrupts 149
values in the tracked corpus and newly emits 21 diagnostics on plans that lint clean today; implement the
blank-tolerant fence-aware termination rule E-01 specifies and NOT `leaf_action_blocks`' rule, since F-10
measures the latter leaves 978 real evidence blocks still refused, and leave `leaf_action_blocks` itself
byte-identical because three consumers depend on it; leave `agent_workflows/ipd_schema.py` alone, both because the state tables
already carry the correct rule and because pending plan `uh9jsk` owns that file for the vocabulary fix;
leave every `IPD-S404` diagnostic's WORDING and the three
`runner_shared.RETRYABLE_FINALIZE_FINDING_TEXTS` strings untouched (F-7); re-derive F-4's corpus
measurement at execution time rather than citing the authoring numbers; perform every RED-then-GREEN proof
the `V-*` items demand rather than asserting the guards work; paste ACTUAL runner output with exit codes for
every test claim; and commit only the paths it modified through `aw commit <plan> -- <paths>`, never
`git add -A`, and never push.

LIFECYCLE OWNERSHIP IS CONDITIONAL. If this plan is executed by `aw oc run` or `aw agy run` with the runner
owning the lifecycle, the executor must NOT move this file or set its terminal status: the runner performs
the atomic finalize after its own checks. If it is executed by an agent directly, that agent performs the
terminal transition itself, and only after `aw ipd lint --phase pre-transition` reports conforming and every
`V-*` above carries concrete pasted evidence with `- Result: pass`.
