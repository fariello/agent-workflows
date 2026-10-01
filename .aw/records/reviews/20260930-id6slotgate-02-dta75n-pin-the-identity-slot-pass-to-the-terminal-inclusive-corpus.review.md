# Review findings: plan dta75n

- Subject-Id: dta75n
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-D01 (HIGH, fixed), PR-D02 (HIGH, fixed), PR-D03 (HIGH, fixed), PR-D04 (MEDIUM, fixed), PR-D05 (MEDIUM, fixed), PR-D06 (MEDIUM, fixed), PR-D07 (LOW, fixed), PR-D08 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5b03be28c`. The plan file was committed and byte-identical to the
lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, one `IPD-Z602` advisory) BEFORE semantic review;
`--phase review-finalize --agent` now reports `clean` with ZERO findings. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

I RE-RAN ALL FIVE AUTHORING FACTS RATHER THAN READING THEM, and every MECHANISM reproduces. This is a strong
plan whose analysis I could not fault on substance:

- Fact 1: `check_collisions(root)` and `check_collisions(root, include_retired=True)` both return `Counter()`.
- Fact 2: `check_collisions` enumerates with a hardcoded `include_retired=True`, `records.append` is unguarded,
  and `caller_visible` is computed AFTER the append and gates only the setid pass. The shouted docstring
  paragraph "BOTH IDENTITY PASSES IGNORE THE LIVENESS FILTER; THE SETID PASS DOES NOT" is present and cites
  `sk7ggr` E-05 and `t0jyb2`.
- Fact 3: the four-axis synthetic probe returns `default=1 widened=1` on every axis, and I additionally
  captured the EXACT rule set per axis (`Counter({'check.id6-identity-slot': 1})`), which confirms E-02's
  predicted `(IDENTITY_SLOT,)` for both new rows rather than leaving it to be discovered.
- Fact 4: re-guarding `records.append` and running the bare suite reds the parity test. All four other files
  naming this rule stay green under the mutation.
- Fact 5: evaluating the parity test's three assertions directly under the mutation gives
  `PARITY assertion (1) True`, `(2) True`, `slot finding present in check_default: False`, exactly as claimed.
  The fragility argument is therefore measured, not asserted.

F-6 also verifies: `CollisionTests.COLLISIONS` holds 11 rows and a path sweep finds NO fixture under
`executed/`, `done/`, `superseded/`, `not-executed/` or `graduated/`. The Scope check's CLI claim verifies too:
driving `python -m agent_workflows check all --agent` on a synthetic repo with an executed plan owning `aaa111`
and a live walkthrough squatting it exits 1 and reports the finding with the D140 remediation in `next`. The
cited spec `2lcqno` acceptance criterion 4 reads as quoted, and `.aw/records/walkthroughs/README.md` carries
the D140 mandate it is cited for.

THREE DEFECTS, EACH OF WHICH WOULD HAVE COST AN EXECUTION PASS. All three are about the plan's INTERFACE with
the current tree rather than about its reasoning, which is why the verdict is a revision rather than a replan.

PR-D01 is the sharpest, because the plan's own safety mechanism misfires. E-01 told the executor to STOP and
report, with "the correct response is a fresh plan", if "the mutation reds more than the single parity test".
Measured: the UNMUTATED suite already reports `1 failed, 3426 passed, 2 skipped` on
`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a filed
time-dependent local-versus-UTC history-clock defect owned by backlog `fnb8pl` (`open`, `bug`,
`Blocks-Release: next`). Under the mutation the suite reports `2 failed, 3426 passed`. So the trigger fires on
a tree the plan IS correctly authored against, and following it would discard a sound plan and waste the pass.
The stop condition is now a DELTA computed against a baseline captured in the same item, and E-01 explicitly
forbids stopping merely because more than one test fails.

PR-D02 is the one the repository's own checker already reports. The plan declared
`.aw/records/backlog/open/20260921-id6slotgate-01-e2j5w4-...backlog.md` in `- Scope-Paths:`, but the item sits
in `graduated/` (the runner graduated it, recorded in the item's own history as "graduated by run
run-20260930T053024Z-3198670: dta75n"). `ce.stale_record_scope_paths` returns
`StaleScopePath(..., classification='moved', resolved=('.aw/records/backlog/graduated/...',))`, and `aw check`
reports `check.scope-path-target-stale` against this plan at severity `error`. The mechanical consequence is
worse than untidiness: `ipd_lifecycle._scope_match` returns False for the real path against the declared
pattern and `_is_implicitly_allowed` also returns False, so `aw commit <plan> -- <real path>` would have
REFUSED the very file E-04 was instructed to edit. This is the identical defect the sibling plan's review
caught as its own PR-001, so the Set had the lesson available.

PR-D03 is a Set-level duplication. E-04 told this plan to append the dated measurement correction to
`e2j5w4`; sibling `aisk5z` (Order 01, same Set, ALREADY `- Status: approved` with
`- Readiness: go-pending-approval`) carries E-05 "CORRECT BOTH BACKLOG ITEMS' MEASUREMENTS", which appends to
`mw0s1y` AND `e2j5w4` through `aw backlog note`, selects by id6, and declares the correct `graduated/` path.
Two approved plans writing the same correction to one record either duplicates the paragraph or races it.
Combined with PR-D02 the cheapest correct fix is to remove the record from THIS plan entirely, which is what I
did: the path is out of `- Scope-Paths:`, E-04 is now a write-nothing verification, and the Deferred row's
existing `Carrier: aisk5z` already carries the obligation. I verified this costs the release gate nothing:
this plan is `e2j5w4`'s SOLE `- From-Backlog:` carrier (`aisk5z` carries `mw0s1y`), so the gate is discharged
by this plan reaching `executed` on the strength of its test coverage, not by the prose edit.

THREE COUNT CORRECTIONS AND TWO SMALLER FIXES.

PR-D04: fact 4's per-file figures are stale (`tests/test_check_engine.py` 49 versus a measured 50,
`tests/test_doctor.py` 35 versus 37), as is its whole-suite `3245 passed` (3426 at review). The PROPERTY the
fact rests on is unaffected and I confirmed it, so these are drift rather than error, but V-01 told the
executor to paste these four summaries and the natural reading is a comparison. Fact 4 now carries the
re-measured figures labelled as context with an explicit re-derive instruction.

PR-D05: E-02's expected outcome and V-02 asserted the table "holds 13 rows", an absolute against a live
population another lane can change. Restated as a BEFORE and AFTER count showing growth of exactly two, which
is the property that actually matters and cannot go stale.

PR-D06: V-05 required "no new failure" against a baseline but did not acknowledge that the baseline itself is
red, and E-01's baseline evidence did not require NAMING the failing ids, so the delta comparison V-05 demands
was not actually supportable from the evidence E-01 collected. V-01 now requires the baseline failures named,
V-05 states the `fnb8pl` failure is expected in both runs, and both forbid claiming a green suite or fixing
that defect.

PR-D07: the gate instructed the executor to "let the runner set backlog item `e2j5w4` to `graduated`". It is
already `graduated` with `- Graduated-To: id6slotgate`, so that instruction is spent and reads as though a
write is still owed. Replaced with the observed state plus the sole-carrier finding.

PR-D08: the gate unconditionally instructed moving the plan to `executed/` "through the tooled lifecycle
transition". Under `aw oc run` / `aw agy run` the RUNNER owns that transition. Rewritten to the house form
(unconditionally owed, conditional owner), which also removes the risk of an executor racing the runner. The
`IPD-Z602` density advisory on E-02 (present at `author`, before my edits) was cleared by moving the row
specifications into sub-bullets rather than splitting the item, since two rows in one table is one concern.

ONE THING I CHECKED AND DID NOT FLAG. The plan's D140 deconfliction is correct: `aisk5z` E-04 owns the
DECISIONS D140 `sk7ggr` parenthetical append, and this plan deliberately stays out of it. The stale
parenthetical really is still in `DECISIONS.md` ("its setid and identity-slot neighbours deliberately do NOT"),
and routing it to the sibling rather than contending over one bullet is the right call.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-D01 | HIGH | IN-SCOPE | G. Plan executability (stop condition) | plan E-01 "STOP ... if the mutation reds more than the single parity test"; measured unmutated `1 failed, 3426 passed`, mutated `2 failed, 3426 passed`; `.aw/records/backlog/open/20260930-fnb8pl-01-fnb8pl-unify-the-history-date-clock-across-both-backlog-s.backlog.md` | The plan's own refusal trigger fires on the tree it is correctly authored against, because the baseline already carries one unrelated failure (`fnb8pl`'s local-versus-UTC history clock). The prescribed response, "a fresh plan", would discard a sound plan and waste the execution pass. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Stop condition restated as a DELTA against a baseline captured in the same item, with the pre-existing failure named and an explicit instruction not to stop merely because more than one test fails. Recorded as F-8. |
| PR-D02 | HIGH | IN-SCOPE | G. Plan executability (declared path does not exist) | `ce.stale_record_scope_paths` returns `classification='moved'` resolving to `graduated/`; `aw check` reports `check.scope-path-target-stale` at `error`; `ipd_lifecycle._scope_match` and `_is_implicitly_allowed` both return False for the real path | The declared backlog `- Scope-Paths:` entry points at `open/` while the item sits in `graduated/`, so `aw commit <plan> -- <real path>` would have REFUSED E-04's own deliverable while the declared path sat unmodified. The repository's own checker reports it at error severity. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The backlog path was REMOVED from `- Scope-Paths:` rather than retargeted, because PR-D03 shows the edit itself is the sibling's. `ce.stale_record_scope_paths` now returns `[]` and `aw check` names this plan on no rule. Recorded as F-10. |
| PR-D03 | HIGH | OVER-SCOPE | C. Architecture (duplicate path) | plan E-04; `aisk5z` front matter (`- Status: approved`, `- Readiness: go-pending-approval`) and its E-05 appending to BOTH `mw0s1y` and `e2j5w4` by id6 at the `graduated/` path; `.aw/records/reviews/20260929-id6slotgate-01-aisk5z-...review.md` PR-001 and D-4 | Two plans in one Set were each instructed to append the same measurement correction to one record, and the lower-Order one is already approved and already correctly targeted. The authored E-04 tried to manage the collision with an ordering rule rather than removing it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 converted to a write-nothing VERIFICATION; the Deferred row's `Carrier: aisk5z` now explicitly names the record correction among what the sibling owns; V-04 inverted to require that NO backlog file is modified. Verified this costs the gate nothing: this plan is `e2j5w4`'s sole `- From-Backlog:` carrier. Recorded as F-11. |
| PR-D04 | MEDIUM | IN-SCOPE | G. Plan executability (live counts) | plan Goal fact 4 (`49 passed`, `35 passed`, `3245 passed`); re-measured 50, 37, 3426 | Three absolute counts had drifted, and V-01 instructed the executor to paste exactly these four per-file summaries, which invites a comparison that would read ordinary growth as a discrepancy. The property the fact rests on (all four files green under mutation) is unaffected and was re-confirmed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fact 4 carries the re-measured figures labelled as context with an explicit re-derive instruction; V-01 forbids comparing against the printed figures. Recorded as F-9. |
| PR-D05 | MEDIUM | IN-SCOPE | G. Plan executability (live counts) | plan E-02 expected outcome and V-02 ("holds 13 rows"); measured table size 11 | A fixed total asserted against a live table another lane can extend. The durable property is the GROWTH, not the total. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Restated as a BEFORE and AFTER count showing growth of exactly two, with 13 given only as the review-time value. |
| PR-D06 | MEDIUM | UNDER-SCOPE | E. Testing and verification | plan V-05 ("no new failure") against E-01's baseline evidence, which required only a summary line | V-05's delta comparison was not supportable from the evidence E-01 collected, because the baseline requirement never asked for the failing ids, and neither item acknowledged that the baseline is red. An executor would have had to claim a green suite or stall. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now requires baseline failures NAMED; V-05 and the validation list state the `fnb8pl` failure is expected in both runs, forbid claiming green, and forbid fixing that out-of-scope defect. |
| PR-D07 | LOW | IN-SCOPE | G. Plan executability (spent instruction) | plan gate "let the runner set backlog item `e2j5w4` to `graduated`"; the item's own `- Status: graduated`, `- Graduated-To: id6slotgate` | The instruction describes a write that already happened, so it reads as though a status change is still owed and invites a redundant or conflicting act. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the observed state, plus the verified sole-carrier fact that makes the gate's discharge path explicit. |
| PR-D08 | LOW | IN-SCOPE | G. Plan executability (execution contract) | plan gate "move this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition" | Stated unconditionally, but under `aw oc run` / `aw agy run` the RUNNER owns the transition, so an executor obeying this would duplicate or race it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to the house conditional-owner form; hand-edited status lines and hand-rolled `git mv` stay forbidden. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The stop condition fires on the current tree (PR-D01). Relax it, or leave it and let the executor judge? | Restate it as a DELTA against a baseline captured in the same item, naming the pre-existing failure. | Leave it and trust the executor to recognize the unrelated failure (the plan's wording says the response is "a fresh plan", so the honest reading is a stop); drop the stop condition entirely (loses a real guard against executing against a tree where the behavior fix is absent). | Measured: unmutated `1 failed, 3426 passed` on `tests/test_backlog.py::...test_release_exempt_setter_roundtrip_and_parity`, owned by backlog `fnb8pl` as an `open` `bug`; mutated `2 failed`. The delta form is STRICTER about the regression it exists to catch (it admits no extra failure attributable to the mutation) while no longer firing on unrelated baseline redness. | yes |
| D-2 | The declared backlog path is stale AND the edit duplicates the sibling (PR-D02, PR-D03). Retarget the path, or remove the record from this plan? | REMOVE it from `- Scope-Paths:` and convert E-04 to a write-nothing verification. | Retarget to `graduated/` and keep the append with an ordering rule (what the authored E-04 attempted); declare both forms (declares a path that cannot exist). | `aisk5z` is already `approved` and its E-05 appends to `e2j5w4` by id6 at the correct path, so retargeting leaves two approved plans writing one record. Removal costs the gate nothing: this plan is `e2j5w4`'s SOLE `- From-Backlog:` carrier (verified: `aisk5z` carries `mw0s1y`), so the handoff predicate discharges the gate on this plan reaching `executed`. After the change `ce.stale_record_scope_paths` returns `[]` and `aw check` names this plan on no rule. | yes |
| D-3 | E-02 trips the `IPD-Z602` density advisory. Split the item, or restructure the text? | Restructure into sub-bullets, keeping one action sentence. | Split into two E-items, one per table row. | Adding two rows to ONE table in one file is one concern executable in one pass, and splitting would create an interleaved state where the table is half-extended while the mutation probe in E-04/V-02 runs. Confirmed by re-running `ipd_schema.e_item_density_advisory`: `None` for every E-item after the restructure, and `aw ipd lint --phase review-finalize` reports zero findings. | yes |
| D-4 | Should the stale per-file and table counts be corrected in place or re-derived at execution? | Keep them as labelled CONTEXT and require re-derivation. | Overwrite them with the review-time figures as the new bar (recreates the same staleness next week); delete them (loses the context that makes fact 4 readable). | The plan's own conventions section cites the live-count re-derivation rule, and the figures are a LIVE population: the suite grew by 181 tests and the table may grow by another lane's row. Stating the property plus a re-derive instruction is the form that cannot go stale. | yes |

No `Reversible: no` decision was taken in this round, so no escalation is owed under the irreversible-decision rule.

### Escalations

None. Every finding is `FIXED`, so no finding at or above the `HIGH` gate threshold is left `OPEN` or
`DEFERRED` and no `- Blocking: yes` question is owed.
