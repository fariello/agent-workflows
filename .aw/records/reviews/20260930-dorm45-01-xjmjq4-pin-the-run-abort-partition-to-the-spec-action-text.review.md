# Review findings: plan xjmjq4

- Subject-Id: xjmjq4
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-X01 (HIGH, fixed), PR-X02 (HIGH, fixed), PR-X03 (MEDIUM, fixed), PR-X04 (MEDIUM, fixed), PR-X05 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `2121b176`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author` reported `conforming` BEFORE semantic review and again at `review-finalize`
after revision; `aw check` reports zero findings against this plan both before and after. The plan is
`- Kind: child`, so the `IPD-S407` orchestrator row check does not apply.

THE DIAGNOSIS IS RIGHT AND I RE-MEASURED ALL OF IT. Four of the five authored findings reproduce exactly:

- F1: the shipped table holds `Counter({'never': 6, 'conditional': 4, 'always': 2})` while the comment
  still reads "two of the 12 codes abort UNCONDITIONALLY; five abort ONLY under a named 4.1 class; five
  never abort". Both the count and the quoted string are verbatim correct.
- F3: `19313eed` deleted `tests/test_run_evidence_completion.py` (1722 lines, 85 `def test_` methods), all
  four named methods existed in it (`test_spec_defines_exactly_twelve_run_codes`,
  `test_no_code_aborts_outside_the_six_enumerated_classes`,
  `test_abort_tristate_agrees_with_the_specs_action_text`,
  `test_conditional_abort_is_not_reported_as_unconditional`), and `grep -rln` for `RUN_FINDING_CODES`,
  `validate_finding_table` and `may_abort_run` over `tests/` returns nothing today.
- F4: the derivation rule reproduces the stored tri-state for all 12 rows with ZERO mismatches, and the
  literal probes behave (`"ABORT RUN"` -> always, a qualified clause -> conditional, no clause -> never).
- F5: `may_abort_run`'s docstring does independently carry "licenses five of the 12 codes", wrong by the
  same measurement.

The carriers are all real and all `open` (`xvp5vx`, `089bq4`), `dorm45` is `graduated`, and the drift
history the plan wants preserved ("The counts moved twice and BOTH moves are recorded") is present in the
comment as quoted.

TWO SERIOUS FINDINGS, and they are the same defect seen from two directions.

PR-X01 is the design gap. E-01's helper reads `row.action`, and the plan's Proposed change 1 claims it has
"no dependency on the stored field, so it is a genuine cross-check and not a tautology". The first clause is
true and the conclusion does not follow: `action` is ALSO a module field, so the PAIR can drift from the
spec together and satisfy the gate forever. I measured it adversarially. Take the real `RUN-CROSS-TREE` row
(`action="FAIL ITEM; ABORT RUN only for identity/type ambiguity or ownership conflict"`,
`abort="conditional"`) and rewrite it to `action="FAIL ITEM"`, `abort="never"`, `abort_classes=()`: E-02's
gate PASSES, because `derive("FAIL ITEM") == "never"`. That row now tells an operator a cross-tree fault
never aborts a queue, contradicting the spec cell it exists to transcribe. The DELETED test caught this
class precisely because it parsed the action out of the SPEC FILE and compared bytes, and its own docstring
states the reason better than I can: "the only defect this vocabulary can realistically ship is a
transcription error, and an expectation copied from the implementation cannot detect one". So the plan was
about to rebuild the weaker half of what was deleted while citing the deleted test as its precedent. New
E-05 restores the spec anchor, and I verified it can be a hard assertion on arrival: parsing spec 4.2 with
the deleted test's own five-cell parser yields twelve rows with ZERO action-text mismatches against the
module and no code present in one set and absent from the other (F7).

PR-X02 is the same gap reached from the commit history, and it falsifies the plan's motivating claim. F2
asserted that E-02's gate "would have failed that commit", naming `544ba188` as the drift event. It would
not have. Reading the diff, that commit changed the row's `action` IN THE SAME HUNK as its tri-state
(`"FAIL ITEM; ABORT RUN if identity/type is ambiguous"` -> `"REFUSE RUN at freeze before any session"`,
`ABORT_CONDITIONAL` -> `ABORT_NEVER`, `("Identity or type ambiguity",)` -> `()`). Driving the derivation
over both pairs: pre-commit derives `conditional` against a stored `conditional` (PASS), post-commit derives
`never` against a stored `never` (PASS). The gate is silent through the whole event. F2's other claim, that
"its only `run_evidence.py` change" was the four-line tri-state flip, is also inexact: one of those lines is
an unrelated recovery-command string. The plan's conclusions survive (the defect is the unenforced prose,
and the table must not be "fixed"), but its argument for the gate did not, and the honest division of labour
is now stated: E-02 catches a HALF-EDIT, E-05 catches a CO-MOVED drift.

THREE SMALLER FINDINGS.

PR-X03: the Deferred row for spec amendment carried `Carrier-Declined: Nothing is outstanding`, which is not
accurate. Spec 4.2's transcription note asserts that `tests/test_run_evidence_completion.py` "asserts byte
equality" on the table's cells, and that file is deleted, so the spec promises a guard that does not exist.
That is owned by open backlog `089bq4`, which is `- Work-Kind: bug` carrying `- Blocks-Release: next`. E-05
restores byte equality for the ACTION cell, so this plan PARTLY discharges a release blocker while its own
prose called the matter settled. The row now carries `- Carrier: 089bq4` with an explicit statement of what
this plan does and does not do, and the gate forbids closing that item.

PR-X04: OQ-01 was `resolved` with `- Owner: none`. A question the author resolved on their own authority must
record who resolved it; `none` leaves an unattributed decision, and the lint only checks the field is
non-empty and not `none`, so nothing mechanical would have caught it. Corrected to `plan author`, with the
narrowing E-05 introduces recorded in the rationale.

PR-X05: V-01's evidence block asks for exactly the right probes but lets a reader conclude the partition is
pinned to the spec once they pass. It now states in its own evidence what it does not prove.

NOTHING ELSE WAS FOUND WRONG. The plan's refusal to "fix" the table is correct and important, and its
reading of the module's own self-description ("an INDEX over the verbatim string, not a new policy") as
licence for a mechanical derivation is sound: the plan enforces a relationship the module already claims.
The `RC-ABORT-DERIVATION` code is correctly characterized as an internal sibling of `RC-COUNT` rather than a
member of the public `RUN-*` vocabulary, so Section 4.2's twelve-code contract is genuinely untouched. The
P16 analysis is careful and correct, including ruling out the tempting shortcut of testing the comment's
wording; E-05's spec parse is compatible with P16 under its own stated exception for the case where "the
text or file itself is the artifact under test", which a table transcribed verbatim into code is, and the
spec's own note calls editing a cell "a code change". E-03's instruction to preserve the existing drift
history rather than overwrite it is the right call and rare.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-X01 | HIGH | UNDER-SCOPE | Rubric D (anti-regression), E (testing) | plan E-01, E-02, Proposed change 1; `git show 19313eed^:tests/test_run_evidence_completion.py` `_parse_spec_run_code_table` docstring and `test_abort_tristate_agrees_with_the_specs_action_text` | E-01's helper reads `row.action`, itself a module field, so E-02's gate is a SELF-CONSISTENCY check, not the cross-check the plan claims. Measured: rewriting the real `RUN-CROSS-TREE` row to `action="FAIL ITEM"`, `abort="never"` PASSES the gate while contradicting the spec cell it transcribes. The deleted test caught this class by parsing the SPEC FILE, so the plan was rebuilding the weaker half of what it cites as precedent. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-05 parses spec 4.2's table from the spec file, asserts byte equality on each `action` cell, derives the tri-state from the SPEC's text, and asserts the twelve-code set with `RUN-NO-PUSH` absent. New V-05 requires the adversarial case shown FAILING there while PASSING E-02. Goal, Scope, Proposed changes and Scope check restated as a two-level pin. New F6, F7. |
| PR-X02 | HIGH | IN-SCOPE | Rubric A (correctness), Step 1 evidence | plan F2; `git show 544ba188 -- agent_workflows/run_evidence.py`; derivation driven over both pairs | F2's claim that E-02's gate "would have failed that commit" is FALSE. `544ba188` moved the row's `action` in the SAME hunk as its tri-state, so the derivation PASSES both before (`conditional`/`conditional`) and after (`never`/`never`). The gate is silent through the plan's own motivating drift event. F2's "only change was that four-line flip" is also inexact: one of those lines is an unrelated recovery-command string. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F2 rewritten with both measurements and an explicit statement that the gate would have been silent, preserving the two conclusions that do hold. The division of labour (E-02 catches a half-edit, E-05 a co-moved drift) is now stated in F2, the Goal, and the gate. |
| PR-X03 | MEDIUM | IN-SCOPE | Project rule (release gate), Rubric G | plan Deferred spec-amendment row; `.aw/records/backlog/open/20260929-089bq4-...backlog.md`; spec `25kzda` Section 4.2 transcription note | The spec-amendment row declared `Carrier-Declined: Nothing is outstanding`. Spec 4.2 asserts a deleted test "asserts byte equality" on the table, so the spec promises a nonexistent guard; that defect is open backlog `089bq4`, a `bug` carrying `Blocks-Release: next`. E-05 restores byte equality for the ACTION cell, so the plan partly discharges a release blocker while calling the matter settled. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Row converted to `- Carrier: 089bq4` with a note stating exactly what E-05 covers (the action cell) and what it does not (the other cells, and the spec sentence itself). Spec-sync section records the known-false sentence and why it is deliberately not corrected here. Gate forbids closing `089bq4`. New F8. |
| PR-X04 | MEDIUM | IN-SCOPE | Workflow rule (open questions) | plan OQ-01 | OQ-01 was `resolved` with `- Owner: none`, leaving an unattributed decision on the author's own authority. Nothing mechanical catches it: the lint checks only that the field is non-empty and not `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner corrected to `plan author`, with the correction recorded in the rationale and the narrowing E-05 introduces stated (action cell here; remaining cells and spec sentence with `089bq4`). |
| PR-X05 | LOW | IN-SCOPE | Rubric E (testing evidence) | plan V-01 | V-01 asks for the right probes but a reader who sees them pass could conclude the partition is pinned to the contract, which is exactly the inference PR-X01 shows is wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now requires stating in its own evidence that `action` is a module field, that agreement there is self-consistency, and that V-05 is the contract anchor. A third literal probe added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02's gate cannot see a spec transcription error. Add a spec anchor, replace the derivation with one, or accept the limit and say so? | ADD the spec anchor as a new E-05, keeping E-01/E-02 unchanged. | (a) Replace the module derivation with a spec-only comparison: rejected, because the runtime gate inside `validate_finding_table` is what makes the table "report itself invalid at runtime", which is the property spec 4.2 already relies on for `RC-COUNT` and the convention this plan is matching. (b) Accept the limit and document it: rejected, because the plan's Goal promises the partition is "self-evidently correct instead of asserted", and the deleted test the plan cites as precedent did the stronger thing, so accepting the weaker one would knowingly under-restore. | The deleted `_parse_spec_run_code_table` docstring ("an expectation copied from the implementation cannot detect" a transcription error); the adversarial `_replace` probe; F7's measurement that the spec and module agree today so the assertion passes on arrival. | yes |
| D-2 | Does E-05's parse of the spec file violate GUIDING_PRINCIPLES P16's ban on reading files as a correctness proxy? | NO. Permitted under P16's own narrow exception, and recorded in V-04 so it is not re-litigated. | Treating it as forbidden and asserting the spec cells as hardcoded literals in the test: rejected, and it is the exact anti-pattern the deleted test warned against, since an expectation copied from the implementation (or hand-copied from the spec at authoring time) cannot detect the drift the test exists to catch. | P16's "The one narrow exception": content verification is permissible "where the text or file itself is the artifact under test". Spec 4.2's own note says its cells are transcribed verbatim and that "editing a cell here is a code change". The deleted test did this and passed. | yes |
| D-3 | The spec sentence promising a byte-equality guard is measurably false. Correct it here, since this plan touches the same subject? | NO. Record it, carry it on `089bq4`, and state why it is not corrected. | Amending the sentence in this plan: rejected on two grounds. It would require putting a `.spec.md` in `- Scope-Paths:`, which this plan deliberately avoids because it changes no contract; and E-05 makes the sentence only PARTLY true (action cell alone), so any rewording either overstates this plan's coverage or pre-empts the restore-versus-reword decision `089bq4` exists to make. | `089bq4`'s body, which records that choice as the open decision; spec 4.2's note as it currently reads; this plan's own scope fence. | yes |
| D-4 | OQ-01 carried `Owner: none`. Resolve the ownership myself or ask? | Set it to `plan author`, the party who actually made the call. | Setting it to `maintainer`: rejected and would be a false attestation, since no maintainer answered this; the workflow's own guidance records a measured case where a false `Owner: maintainer` passed every mechanical check. Setting it to the reviewer: rejected, the AUTHOR resolved it at authoring time and review only narrowed the boundary. | The plan's own workflow history showing the resolution was authored, not asked; `ipd_lint`'s `has_owner`, which checks non-empty and not `none` and never inspects the value. | yes |

No `Reversible: no` decision was taken in this round. OQ-01 is `resolved`; no question is left `open`, so no escalation is required.
