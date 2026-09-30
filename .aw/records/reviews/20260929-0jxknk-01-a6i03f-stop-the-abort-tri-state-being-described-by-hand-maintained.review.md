# Review findings: plan a6i03f

- Subject-Id: a6i03f
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-701 (HIGH, open), PR-702 (HIGH, fixed), PR-703 (MEDIUM, fixed), PR-704 (MEDIUM, fixed), PR-705 (LOW, fixed)

## Round 1

Reviewed at HEAD `5ffa2852` in an isolated review lane. The plan file was tracked, unmodified, and
byte-identical to the lane input (`diff` reported no difference), so no pre-review snapshot was needed.
Structural preflight `aw ipd lint --phase author --agent` reported `outcome: clean`, exit 0, ZERO findings
and no `IPD-Z602` density advisory BEFORE semantic review. After revision the linter reports `error` with
`IPD-Q501`, which is the INTENDED outcome of this review rather than a defect: the blocking question this
review added is what stops execution, and that refusal is the whole point of the escalation.

EVERY ONE OF THIS PLAN'S THIRTEEN MEASUREMENTS REPRODUCED, SEVERAL CHARACTER FOR CHARACTER. I re-ran the
work rather than reading the numbers. F-01: `Counter(r.abort for r in RUN_FINDING_CODES)` is
`Counter({'never': 6, 'conditional': 4, 'always': 2})` and both prose sites still read 2/5/5, quoted at
`run_evidence.py` as "two of the 12 codes abort UNCONDITIONALLY; five abort ONLY under a named 4.1 class;
five never abort" and "spec 4.1 licenses five of the 12 codes". All three member lists match E-01's
exactly. F-02: no file under `tests/` references `RUN_FINDING_CODES`, `may_abort_run`, `ABORT_CLASSES`,
`validate_finding_table`, `abort_classes_for`, `spec_message_for` or `bound_run_finding_codes`, and
`git show 19313eed --stat` lists `tests/test_run_evidence_completion.py | 1722 ----`. F-04 reproduced at
all four historical commits including the single moment prose and table agreed (`4f7f5461`, 2/5/5 with
prose 2/5/5). F-05: the derivation over the parsed spec table yields `derivation mismatches: []`,
`verbatim action mismatches: []`, `verbatim message mismatches: []` across all twelve rows, with
`REFUSE RUN at freeze before any session` correctly deriving `never`. F-06's mutation reproduced verbatim:
`under mutation, partitions agree: False` and `per-row mismatch: [('RUN-CROSS-TREE', 'conditional',
'always')]`. F-07: the parsed classes equal `list(ABORT_CLASSES)` in order and `accessor disagreements:
[]`. F-08, F-09, F-12 and F-13 all confirmed, including `REFUSE RUN` occurring exactly once in the spec
and no other module in `agent_workflows/` referencing any of these symbols. E-02's proposed placement
(after `abort_classes_for`, before `bound_run_finding_codes`) is exactly right, `Dict` is already
imported, and `abort_partition` does not yet exist.

SO THE ANALYSIS IS SOUND AND THE REMEDY IS THE RIGHT ONE. The reasoning in OQ-01 in particular is
correct and well argued: a pinned 2/5/5 would have gone red for commit `544ba188`, whose change was right
and maintainer-approved, and no spec states the partition, so pinning it would invent a contract while
the row COUNT legitimately stays hard-coded because the spec names it as one. I verified both halves.

WHAT REVIEW FOUND IS A COLLISION THE PLAN COULD NOT SEE, AND IT IS WHY THIS VERDICT IS NOT AN APPROVAL
(PR-701). The plan correctly identifies `dorm45` as a near-duplicate item and correctly declines to close
it. But it records `dorm45` as `- Status: open`, and it is `graduated`, with `- Graduated-To: dorm45` and
a live carrier: `.aw/records/plans/pending/20260929-dorm45-01-xjmjq4-pin-the-run-abort-partition-to-the-spec-action-text-instead.ipd.md`.
That plan's E-03 rewrites the SAME `# ---- abort semantics (spec 25kzda 4.1)` comment AND the SAME
`may_abort_run` docstring, for the same reason, and its E-04 adds a spec-action derivation test differing
mainly in filename. Its own F5 independently records the second prose site. NEITHER PLAN NAMES THE OTHER'S
PLAN: this one names the item but not `xjmjq4`, and `xjmjq4` contains no occurrence of `0jxknk` or
`a6i03f`. Both are `to-review`; neither had a review record before this one. Two plans, one file, one
defect, mutual blindness.

AND THE CHOICE BETWEEN THEM IS SUBSTANTIVE RATHER THAN A TIE-BREAK, WHICH IS WHY I DID NOT RESOLVE IT
MYSELF. They diverge on one real axis. This plan derives from the SPEC FILE, so it also catches a row
whose `action` drifted from the spec's bytes, and it enforces only in a test. `xjmjq4` derives from
`row.action` ALONE (weaker authority: a row reworded away from the spec derives consistently and passes)
but additionally extends `validate_finding_table` with an `RC-ABORT-DERIVATION` code, so its guard runs at
RUNTIME. That runtime guard is stronger where it applies AND it edits a self-check this plan's own gate
explicitly forbids touching, and it cannot read the spec because an installed package has no `.aw/` tree,
which is exactly why this plan's E-04 must `skipTest`. The accessors they add are different functions, not
alternatives. Choosing therefore means deciding whether a `low`/`chore` fix should reach into a runtime
self-check, which is a risk-appetite judgement belonging to the maintainer, not a fact in the repository.
I raised it as OQ-04 with `- Blocking: yes` and `- Finding: PR-701`.

THE SMALLER CORRECTIONS WOULD EACH HAVE COST AN EXECUTION TURN (PR-703). E-05 names the spec heading as
`#### Exhaustive ABORT RUN set`; it is actually ``#### Exhaustive `ABORT RUN` set`` with backticks, so the
literal `text.index(...)` the item implies raises `ValueError`. My parse succeeded only after restoring
them. E-04 says to glob `*-25kzda-*.spec.md` "under `.aw/records/specs/`" while the shape it cites globs
`approved/` specifically and the spec lives there, so a non-recursive glob one level up matches zero files
and the exactly-one assertion FAILS rather than skips.

WHAT I DELIBERATELY DID NOT FLAG. The plan's evidence discipline is excellent and its self-awareness is
unusual: it inverts the backlog item's own first-suggested remedy on measured grounds and says so, it
records that the item's named precedent test no longer exists, it identifies P16's spec-versus-source
distinction as load-bearing and lands on the right side of it, it refuses to fix the `REFUSE RUN` glossary
gap it found and explains why, and its OQ-03 raises the "is this worth a run" question against its own
interest. I left OQ-03 open and non-blocking: it is correctly owned and OQ-04 subsumes it. I left the
five-item structure alone; each item has one deliverable and the linter raised no density advisory. I did
not flag the absence of `- Readiness:`, which is correct at `to-review`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | IN-SCOPE | C (duplicate work path); G (records accuracy) | plan F-10 ("`dorm45` ... Its `- Status:` is `open`"); `.aw/records/backlog/graduated/20260922-dorm45-01-dorm45-run-evidence-abort-tally-drift.backlog.md` carrying `- Status: graduated` / `- Graduated-To: dorm45`; `.aw/records/plans/pending/20260929-dorm45-01-xjmjq4-...ipd.md` with `- From-Backlog: dorm45`, `- Status: to-review`, E-03 rewriting the same comment and the same `may_abort_run` docstring, E-04 adding a spec-action derivation test; `grep` for `0jxknk`/`a6i03f` in `xjmjq4` returning nothing | **A SECOND PENDING PLAN FIXES THIS SAME DEFECT IN THE SAME FILE AND NEITHER PLAN KNOWS OF THE OTHER.** `dorm45` is not `open`, it is `graduated` to `xjmjq4`, whose E-03 edits the identical two prose sites. If both execute, the second finds its work done and its scope reconciliation will not match. The two also differ on a real design axis (spec-file authority plus test-only enforcement here, versus row-text authority plus a runtime `validate_finding_table` extension there), so the choice is substantive and one plan's gate forbids what the other's E-item requires | C:Low; U:Low; S:Low; F:Medium; Overall:Medium-High (functionality: resolving it means retiring one of two authored plans or merging them, which is a scope-and-priority judgement no repository evidence settles) | OPEN | ESCALATED, not silently fixed. New F-10 (rewritten, severity raised LOW -> HIGH) and new F-14 record the measured facts and the three honest options (execute this and retire `xjmjq4`; execute `xjmjq4` and retire this; merge both). New **OQ-04** carries `- Blocking: yes`, `- Owner: maintainer`, `- Finding: PR-701` and `- Carrier: xjmjq4`, so `aw ipd lint` now reports `error` with `IPD-Q501` at every checkpoint and `aw ipd begin` refuses until a human answers. The `- Carrier:` was added after `aw check plans` reported `check.ipd-uncarried-obligation` against the new question; `xjmjq4` is the correct carrier because the obligation IS that plan's disposition. Note the plan carried a PRE-EXISTING `check.review-finding-unescalated` before this review (measured by stashing the edits), which the escalation also clears. The Deferred row's `Carrier-Declined` replaced with `Carrier: xjmjq4`; the gate leads with the refusal and states plainly that nothing MEASURED is in doubt |
| PR-702 | HIGH | IN-SCOPE | G (records accuracy) | plan F-10 and its Deferred row, both stating `dorm45` is `open` and that a maintainer "can close it citing this plan's evidence once executed" | **THE DUPLICATE ITEM'S STATUS IS WRONG, AND THE OBLIGATION DERIVED FROM IT IS THEREFORE WRONG TOO.** Because `dorm45` is `graduated` rather than `open`, the action the plan reserves for a maintainer (close the duplicate item) is not the live question; the live question is which carrier plan executes. A reader acting on the plan as written would look for an item to close and find one already handed off | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 corrected with the measured front matter; the Deferred row rewritten to say `dorm45` needs no closing by this plan and to point at OQ-04; the backlog-handoff paragraph corrected, and `0jxknk`'s own `graduated` status and `chore` work-kind confirmed so the no-gate claim is verified rather than asserted |
| PR-703 | MEDIUM | IN-SCOPE | E (testing); G (executability) | plan E-05 ("spec 4.1's `#### Exhaustive ABORT RUN set` table"); actual heading ``#### Exhaustive `ABORT RUN` set``; plan E-04 ("glob `*-25kzda-*.spec.md` under `.aw/records/specs/`"); `tests/test_runner_shared.py` composing `repo_root / ".aw" / "records" / "specs" / "approved"` | **TWO CITATIONS DO NOT RESOLVE AS WRITTEN AND WOULD EACH COST AN EXECUTION TURN.** The heading search omits the backticks and raises `ValueError`; the glob points one directory above where the spec lives, so the exactly-one assertion fails instead of skipping. Review hit the first directly and fixed it before its parse succeeded | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 with both measurements. E-04 now names `approved/` explicitly, explains why neither the parent directory nor a recursive glob is correct (zero matches versus risking a superseded copy), and records the measured table shape (12 rows, 5 cells, `Action` LAST). E-05 now quotes the backticked heading and notes the sibling heading is correct as cited |
| PR-704 | MEDIUM | IN-SCOPE | E (testing); live-artifact convention | plan F-12 / Required tests / V-05 (`3246 passed, 2 skipped, 3 warnings in 47.09s` at HEAD `3f167c17`); review bare run at HEAD `5ffa2852`: `3330 passed, 2 skipped, 3 warnings in 151.53s` | **THE BASELINE MOVED 84 PASSES IN A DAY.** The plan already instructs re-derivation, correctly, but a reader reconciling against the single transcribed figure would report a spurious delta on a plan whose expected delta is only the new file's cases | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both baselines recorded with their HEADs in F-12, Required tests and V-05, with the 84-pass movement stated as the measured reason for node-id reconciliation rather than as a caution |
| PR-705 | LOW | IN-SCOPE | G (gate completeness) | plan gate ("This plan is `to-review`. It requires `/plan-review` and then explicit human approval"); the new OQ-04 | **AFTER THE ESCALATION THE GATE NO LONGER DESCRIBED THE PLAN'S ACTUAL STATE.** A gate saying only "needs review then approval" understates a plan that `aw ipd begin` will now refuse, and an executor reaching it would discover the refusal rather than being told | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now leads with the `IPD-Q501` refusal, names OQ-04 as its cause and the maintainer's answer as the only thing that clears it, states that `- Readiness:` is ABSENT rather than `no-go` and why, and records that OQ-04 subsumes OQ-03 so the maintainer answers one question and not two |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Two pending plans fix the same defect in the same file. Should the reviewer pick one, or escalate? | Escalate as a BLOCKING open question and pick neither | (a) Resolve it myself in favour of `a6i03f` (the plan under review) and recommend retiring `xjmjq4`, rejected because it would retire another author's unreviewed plan on my own authority, and because `xjmjq4` carries a genuinely stronger runtime guard this plan declines, so preferring the plan I happen to be reviewing would be selection bias with a real cost. (b) Resolve in favour of `xjmjq4`, rejected for the mirror reason and because its derivation authority is measurably weaker. (c) Note it in prose only, rejected because prose reaches no gate: both plans would remain dispatchable and an unattended run could execute both | The workflow forbids inventing a decision that requires the human, and this one turns on whether a `low`/`chore` item should reach into a runtime self-check, which is risk appetite rather than fact. `- Blocking: yes` makes `aw ipd lint` fail closed at every checkpoint (verified: disposition went `conforming` -> `error` with `IPD-Q501`), which is the mechanism that actually prevents the double execution | yes |
| D-2 | Is the collision a `REJECT - NEEDS REPLAN`, since a whole second plan may supersede this one? | No: `REVIEWED - OPEN QUESTIONS` | Mark REPLAN, rejected because the approach is NOT unsound: every measurement reproduced, the remedy is right, and the deliverable is the stronger of the two on derivation authority. REPLAN would assert the plan needs re-authoring when what it needs is a disposition decision between two sound plans | The verdict vocabulary reserves REPLAN for an approach that cannot be repaired with bounded edits. Here the bounded edits were applied (F-10 corrected, F-14 and F-15 added, citations fixed) and what remains is a human choice, which is exactly what `REVIEWED - OPEN QUESTIONS` plus `NO-GO` records | yes |
| D-3 | Should the reviewer fold `xjmjq4`'s runtime `validate_finding_table` cross-check into this plan, since it is the stronger guard? | No: name it in F-14 as one of the merge options and leave it to OQ-04 | Add it as a new E-item here, rejected on two grounds: this plan's own gate says "DO NOT TOUCH `validate_finding_table`" and a reviewer adding an E-item that violates the plan's stated prohibition is incoherent; and it widens a two-file chore into a production runtime change, which is the exact scope question OQ-04 asks the maintainer | The two enforcement sites are a real trade (runtime catches every caller but cannot read the spec; a test can read the spec but only runs in the repo), and F-14 records it so whoever answers OQ-04 decides with the measurement rather than re-deriving it | yes |
| D-4 | `dorm45` is `graduated`, so is any obligation owed to it by this plan? | No obligation; replace the `Carrier-Declined` with `Carrier: xjmjq4` | Leave the `Carrier-Declined` (which reasoned that filing a carrier would create an item saying "close another item"), rejected because that reasoning was built on the item being `open`; with a real carrier plan in existence the honest record points at it. Also considered filing a new item to track the collision, rejected because OQ-04 plus PR-701 already carry it and the collision cannot outlive the disposition decision | The durable-carrier rule wants a resolvable pointer for a deferred obligation, and `xjmjq4` is a live pending plan, so it is the correct and available carrier | yes |
| D-5 | OQ-03 (is this worth a run at all) is open and non-blocking. Escalate it too, or leave it? | Leave it open and non-blocking | Make it blocking, rejected because the 2026-09-10 maintainer ruling is explicit that a non-blocking question must not hold a plan, and because OQ-04 already blocks, so a second blocking question adds no gate and costs the maintainer a second decision. Resolve it myself, rejected because it is a priority judgement | Any answer to OQ-04 answers OQ-03 as a side effect (all three of OQ-04's options decide whether this plan runs), so the honest move is to say so in the gate and ask once. Recorded in the gate as "OQ-04 subsumes OQ-03" | yes |
