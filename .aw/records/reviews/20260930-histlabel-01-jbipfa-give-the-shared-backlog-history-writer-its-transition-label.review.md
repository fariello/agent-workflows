# Review findings: plan jbipfa

- Subject-Id: jbipfa
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `7f8b85ea`. The plan file was committed and unmodified in the
lane (`git status --porcelain` empty), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review, and
`--phase review-finalize` reports `clean` after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator child-row check does not apply.

THE PLAN'S CENTRAL DIAGNOSIS IS CORRECT AND I RE-DROVE EVERY FINDING RATHER THAN TRUSTING IT. The
asymmetry is real, the design is right, and the fix is the right size. Specifically reproduced:

- F-01 reproduces exactly. Driving both spellings over identical `open` items: `--status` writes
  `- 2026-09-30 set (aw backlog): m`, positional writes `- 2026-10-01 graduated (aw set): m`.
  `_reattach_history` hardcodes `new_record = f"- {today} set (aw backlog): {msg}"`;
  `apply_status_change` builds `f"- {today} {status_tag} ({actor}): {message}"` with
  `status_tag = norm_status`.
- F-03 reproduces. `_reattach_history` has exactly two callers, `backlog.run_set` and
  `set_records.close_on_answer`, and the plan updates both, so the defaulted parameter is the right
  call and a required one would be gratuitous.
- F-05 reproduces and is the plan's strongest design argument. With a status-ONLY label the existing
  parity test still fails, because `apply_status_change` tags a true same-status write `same-status`
  deliberately; the `same-status` discrimination is required, not gold-plating.
- F-06 reproduces (two identical same-status `--status` calls append two records; the positional
  spelling dedupes), and is correctly FILED as `r74211` rather than fixed. `aw find r74211` resolves.
- F-08 reproduces: `eikajx`'s E-01 prose and its review record's D-3 both record the acceptance and the
  filing of `awqzuh`, so this plan discharges a deliberate debt rather than contradicting a decision.

I DEMONSTRATED THE PRESCRIBED MECHANISM RATHER THAN DESCRIBING IT, with a throwaway probe of E-01
through E-03 that was then reverted (`git status --porcelain` empty afterwards, `tests/test_backlog.py`
re-run). Measured parity table, label column only:

```
graduated  --status=- 2026-09-30 graduated (aw backlog): m     positional=- 2026-10-01 graduated (aw set): m     EQUAL=True
open       --status=- 2026-09-30 same-status (aw backlog): m   positional=- 2026-10-01 same-status (aw set): m   EQUAL=True
done       --status=- 2026-09-30 done (aw backlog): m          positional=- 2026-10-01 done (aw set): m          EQUAL=True
ALL THREE AGREE: True        (date and actor normalized by shape; see PR-001)
```

and the legacy default is preserved:

```
_reattach_history(old, old, "done", "msg")                -> - 2026-09-30 set (aw backlog): msg
_reattach_history(old, old, "done", "msg", label="done")  -> - 2026-09-30 done (aw backlog): msg
```

THE DOMINANT FINDING IS A PRE-EXISTING RED TEST THE PLAN TREATED AS GREEN (PR-001). One of the two
tests E-04 edits fails at the BASE COMMIT, and not for any reason connected to the label. Two writers
read two different clocks, so a cross-spelling whole-record comparison is red for the part of every day
when the local and UTC dates disagree. That is already filed three times as a release-blocking bug, and
one of those items (`fnb8pl`) explicitly records that THIS plan "would not fix the clock skew". The
plan's F-04 asserted the opposite baseline (`44 passed`), so an executor would have edited the test,
seen it still red, and had no written reason to look past the label. Fixed by requiring shape-based date
normalization in E-04 and E-05, a both-timezone demonstration in V-04 and V-05, and a Deferred row
carrying `fnb8pl`; the clock fix itself stays OUT, since absorbing another item's gated work inside a
`chore` would hide a live release blocker.

ONE CONCLUSION WAS INVERTED AND IS WITHDRAWN (PR-003). F-07's facts reproduce but its reading did not.
`backlog_graduate_legitimacy` clause 4 tests `if "graduated" not in newest` against the WHOLE record
line, so once the label IS `graduated` the clause cannot fail on a graduated item: this change makes it
TAUTOLOGICAL, which is a weakening, not the "strictly more correct" the plan claimed. It is nonetheless
acceptable, and I did not block on it: the positional path has had that property since it was written
(measured CLEAN at base on the same message), the clause's second half already matches any six-letter
word (`metadata only` satisfies it), and the runner's real message carries the word independently. So
the change equalizes two paths rather than introducing the weakness. Recorded, with its measurement,
and explicitly declined a carrier because the correct fix needs a decision about what that clause
should test, which is not this plan's to make.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E (testing/verification); D (anti-regression) | `agent_workflows/backlog.py:1831` (`_reattach_history`, `datetime.date.today().isoformat()`) versus `agent_workflows/status_set.py:894` (`apply_status_change`, `datetime.datetime.now(datetime.timezone.utc).date()`); `tests/test_backlog.py:1658` (`test_release_exempt_setter_roundtrip_and_parity`) | One of the two tests E-04 edits is ALREADY FAILING at the base commit, for a reason unrelated to the label: the two writers stamp dates from DIFFERENT CLOCKS (local versus UTC), so a cross-spelling whole-record comparison is red whenever the two dates differ. Measured at base: `1 failed, 43 passed`, diff is purely the date; `TZ=UTC` passes. F-04 asserted base was `44 passed`, so E-04 would have had the executor edit this test, see it still red, and chase the label. E-05's new module would have inherited the same time-dependence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now REQUIRES shape-based date normalization (regex on `^- \d{4}-\d{2}-\d{2} `, never a second clock read) with the measured base failure quoted and both prohibited shortcuts named (`TZ` in the test; changing `backlog.py` to UTC). E-05 extends the same requirement to every cross-spelling comparison. V-04 and V-05 require green under BOTH the local timezone and `TZ=UTC`, plus the base-commit run. F-09 added; Deferred row added carrying `fnb8pl`; Scope line and Required-tests updated. |
| PR-002 | MEDIUM | IN-SCOPE | G (plan executability) | `.aw/records/plans/pending/20260930-histlabel-01-jbipfa-...ipd.md` F-04 row | F-04's measured baseline was wrong in a way that would mislead an executor: it claimed `tests/test_backlog.py` was green at base (`44 passed`) and that the probe caused exactly 2 failures. Re-derived with an independent probe at HEAD `7f8b85ea`: base is `1 failed, 43 passed` and the probe run is `2 failed, 3438 passed, 2 skipped`, so the probe adds ONE failure. The row's load-bearing claim (no other test depends on the old label) does hold. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 rewritten with the re-derived numbers, distinguishing the one test this change breaks from the one that was already red, and keeping the re-derive-at-execution instruction with an added requirement to record the base failure SET by name. |
| PR-003 | MEDIUM | IN-SCOPE | A (correctness); D (anti-regression) | `agent_workflows/production_checks.py:589` (`backlog_graduate_legitimacy`, `if "graduated" not in newest`) and `:591` (`re.search(r"[a-z0-9]{6}\|run-[0-9a-zA-Z]+", newest)`) | F-07's conclusion is INVERTED. Giving the `--status` path a `graduated` label does not make that check "strictly more correct": clause 4 greps the WHOLE record line for the word, so once the label supplies it the clause can never fail on a graduated item. That is a weakening. Measured: `set` label + message `metadata only` -> FINDING; `graduated` label + same message -> CLEAN; and the positional spelling, which already writes `graduated`, is ALREADY CLEAN at base. Clause 4's second half is near-vacuous too (`metadata only` and `status -> graduated` both satisfy the regex). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 rewritten: facts kept, conclusion withdrawn and replaced with the measured tautology, plus why the net effect is still acceptable (pre-existing on the sibling path; live runner message satisfies the clause on its own text). Deferred row added with an explicit carrier DECLINE and the reason (the repair needs a contract decision about what the clause should test). No E-item changed; the plan's behavior is unaffected. |
| PR-004 | LOW | IN-SCOPE | E (testing/verification) | `agent_workflows/backlog.py:1832` (`msg = message.strip() or f"status -> {new_status}"`) versus `agent_workflows/status_set.py:922` (`default_message = f"status set to {norm_status}"`) | A FOURTH asymmetry exists that no item covered and that a whole-record cross-spelling comparison would trip on: with no `--message`, the `--status` spelling defaults to `status -> graduated` and the positional spelling to `status set to graduated`. The plan's parity claims and new tests compare whole records, so this needed stating. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 added with both measured records. E-02 records the divergence; E-05 now requires every cross-spelling test to pass an EXPLICIT `--message` so the defaulted divergence is never in the comparison. Deferred row added with an explicit carrier decline (cosmetic, no consumer, and a fourth near-duplicate item on one function would add triage cost without information). |
| PR-005 | LOW | IN-SCOPE | G (live-artifact criteria) | plan F-02 row; re-measured corpus | F-02's corpus counts had already drifted between the backlog item (`set` 318, 2026-09-28) and authoring (476, 2026-09-30), and drifted again by review hours later the same day (517, total 1837). The row half-acknowledged this but still led with a specific number, and the plan's title line and Scope quoted `476` as if it were a property. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 re-measured and restated so the DOMINANCE of the status-naming convention is the finding and the count is explicitly context, naming all three measurements and instructing the reader to quote none of them. Scope line changed from `476 EXISTING records` to `EXISTING records`. No item asserted a count, so no acceptance criterion needed changing. |
| PR-006 | LOW | IN-SCOPE | G (live-artifact criteria) | plan Required-tests section; `aw check` re-run at HEAD `7f8b85ea` | The authoring-time `aw check` baseline (58 findings across 8 named rules) is a drifting live population recorded as if it were stable, and it had already drifted: review measures 51 findings across a partly different rule mix (two rules gone, one new). An executor comparing against the written numbers would see a spurious delta. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required-tests re-measured and restated: the review numbers are given as CONTEXT, the authoring drift is named, and the bar is explicitly the before-set and after-set being identical TO EACH OTHER on the tree as found. The three exit-0 gates were re-verified exit 0 at review. |
| PR-007 | LOW | UNDER-SCOPE | G (plan executability) | plan `## Deferred / out of scope` section | Three things review established are out of scope had no Deferred row, so each was a silent exclusion rather than a recorded decision: the date-clock skew (PR-001), the defaulted-message divergence (PR-004), and the `backlog_graduate_legitimacy` tautology (PR-003). The repository's convention requires each to carry a `Carrier:` or an explicit `Carrier-Declined:` with a reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Three Deferred rows added: the clock skew carrying `fnb8pl`, and the other two with explicit `Carrier-Declined:` reasons rather than silent omission. Scope line extended to name the clock skew as OUT. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | One of the two tests this plan edits is already red at base on a local-versus-UTC clock skew. Fix the clock here, pin `TZ` in the test, or normalize the date and leave the clock alone? | NORMALIZE THE DATE BY SHAPE in every cross-spelling comparison and leave the clock untouched, carried by `fnb8pl`. | (a) Fix the clock in `backlog.py` - rejected: it is already filed THREE times as a live release-blocking `bug` (`fnb8pl`, `lq2w86`, `2wae2x`), and `fnb8pl`'s own record states this plan "would not fix the clock skew", so absorbing it would silently take another item's gated work; it also touches five `date.today()` sites and changes the date on every future backlog record, a far wider blast radius than a label change. (b) Set `TZ=UTC` in the test - rejected: that hides a live release-blocking bug behind a test-only environment variable, leaving the product defect unobserved. (c) Leave the test time-dependent - rejected: the plan would then ship a label fix whose own regression pin is red for part of every day for an unrelated reason, which is exactly the confusion that produced F-04's wrong baseline. | measured base `1 failed, 43 passed` versus `TZ=UTC` green; `agent_workflows/backlog.py:1831` local clock against `agent_workflows/status_set.py:894` UTC clock; `fnb8pl` / `lq2w86` / `2wae2x` all `open` with `- Blocks-Release: next`; demonstrated at review that date+actor shape normalization makes all three parity rows agree. | yes |
| D-2 | F-07's conclusion is inverted: the change makes a production check's clause tautological rather than stronger. Does that block the plan? | NO. Withdraw the claim, record the measured tautology, and proceed. | (a) Block until the clause is repaired - rejected: the weakness is PRE-EXISTING on the positional spelling (measured CLEAN at base on the same message), so this plan equalizes two paths rather than creating the hole, and gating a label fix on another function's contract decision is scope creep with no safety gain. (b) Repair the clause inside this plan - rejected: deciding what "history cites the generated artifacts" should test is a judgement about that check's contract (its second half already matches any six-letter word), belongs with that check, and would widen a `chore` into a production-check redesign. (c) Leave F-07 as authored - rejected outright: it tells an executor the change strengthens a consumer when it measurably weakens one, and a plan that mis-states its own blast radius invites an unchecked assumption. | driven output of `backlog_graduate_legitimacy` over crafted graduated items in scratch git repos (FINDING with `set` label, CLEAN with `graduated` label, CLEAN at base for the positional label); `production_checks.py:589` clause-4 whole-line containment; `:591` regex matching any six-letter word; the runner's real message `graduated by run run-X: abc123` satisfying the clause independently. | yes |
| D-3 | Seven findings, three MEDIUM, none BLOCKER or HIGH. Does this plan go NO-GO? | NO. All seven were FIXED by in-place revision, so readiness is `go-pending-approval`. | (a) NO-GO on the three MEDIUMs - rejected: severity is for reporting and the Fix Bar alone decides fixing; every fix here is Low Remediation Risk on all four axes (correct a baseline, add a test normalization, withdraw a claim, re-measure three drifting counts, add three Deferred rows) and not one changes the plan's design or shipped behavior. (b) REPLAN - rejected: the central diagnosis reproduces exactly, the design including the `same-status` discrimination is correct and was demonstrated end to end, and every defect was in a stated baseline or a conclusion, all repairable with bounded edits. (c) Escalate as `- Blocking: yes` - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the `HIGH` threshold, and nothing is left unfixed at any severity. | the `plan-review` Fix Bar and readiness vocabulary; `aw ipd lint --phase review-finalize --agent` conforming after revision; `review_findings_gate` absent from `.aw/config/project.json` so the default `HIGH` threshold applies; the demonstrated post-fix parity table and preserved legacy default. | yes |
