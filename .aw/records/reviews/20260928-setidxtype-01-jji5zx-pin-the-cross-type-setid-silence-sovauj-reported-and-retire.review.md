# Review findings: plan jji5zx

- Subject-Id: jji5zx
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a6bdeafd` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after revision. No pre-review snapshot was owed: the plan was committed and unmodified, and the
lane-input snapshot is byte-identical to the tracked file. NO production code and no tracked record
other than the plan was modified by this review; in particular `agent_workflows/check_engine.py` was
never written to, which matters here because the plan's own validation originally asked an executor
to edit it (see PR-A02). Every measurement was taken against throwaway trees under the system temp
dir via the test module's own helpers.

THE PLAN'S CENTRAL JUDGEMENT IS CORRECT AND ITS EVIDENCE HOLDS, which is the main thing a reviewer
owes a plan that declines to do what its backlog item asked. F-1 re-driven: the exact `sovauj`
fixture (a pending plan declaring `- Set: integpath (...)` plus a walkthrough declaring the same and
its own `- Id:`) returns `[]` from `check_collisions` at BOTH `include_retired=False` and `True`, and
`[]` from the full sweep. F-2 re-driven: `git merge-base --is-ancestor c6648722 HEAD` succeeds and
`rg -c "different type" agent_workflows/check_engine.py` finds nothing. F-3 re-driven: the parity
test's `assertNotIn`/`assertIn` pair on `setid_coll_finding` does pin the retired-population
behavior the item's second proposal would have retargeted. F-4 holds (no row pairs plans with
walkthroughs). F-5 holds and is the finding that makes E-01 worth writing: two walkthroughs sharing a
setid with DIFFERENT descriptives do report `check.setid-collision`, so the within-type arm is
genuinely reachable for this type and the new clean row is not vacuous. F-6 and F-7 hold. Re-aiming
the plan at the regression pin plus the stale prose, and saying plainly in the gate that the reviewer
should reject rather than amend if F-1 is disbelieved, is exactly the right shape.

WHAT REVIEW FOUND IS ONE WRONG MEASUREMENT THAT WOULD HAVE FAILED THE NEW ROW, ONE VALIDATION STEP
THAT COULD HAVE DAMAGED A SHARED CHECKOUT, three record-accuracy errors, and one open question
addressed to the reviewer that is now answered.

**THE NEW ROW'S EXPECTED SET IS WRONG AND WOULD HAVE FAILED ON ARRIVAL (PR-A01, HIGH).** Step 0
records "Measured for this plan's fixture: the full sweep yields exactly
`['check.ipd-draft-ready-to-review']`". Re-measured with this module's own `_tree`/`_plan_text`
helpers across four variants, both `check_collisions` and `check_types(root, ["all"])` return `[]`,
with and without a parenthetical descriptive on either side. The one-element prediction is reachable
only by passing `status="draft"` to `_plan_text`, which this plan never asks for and which the
EXISTING cross-type row does not do either (it takes the helper's `approved` default and expects
`(HISTORY_MISSING,)`, that finding coming from its synthetic SPEC, not from the plan). The runner
compares `_rules(all_drift) != sorted(expected)` exactly, so the authored tuple fails; and because a
failing CLEAN row sets `clean_row_broken`, the failure would present as the cross-type carve-out
being broken rather than as a wrong expectation, which is the most misleading possible failure mode
for this particular row.

**V-01's FALSIFICATION INSTRUCTS AN EDIT THAT COULD DAMAGE A SHARED CHECKOUT (PR-A02, HIGH).** V-01
requires "the diff that temporarily restores the cross-type comparison" in
`agent_workflows/check_engine.py`, then a revert. That module is outside `- Scope-Paths:` by this
plan's own deliberate choice ("Explicitly NOT changed"), this is a shared checkout, and TWO other
pending plans declare that exact file (`jpn6hy`, `ghna7l`) while `tl2b2r` declares this plan's own
`tests/test_check_engine.py`. A write-then-revert can race a co-worker's in-flight edit, and a failed
revert leaves the repository's own collision rule mutated while every suite still passes. The
falsification is sound and load-bearing, so it must be kept: demonstrated at review WITHOUT touching
the tree by enumerating the fixture through `check_engine._iter_type_files` and `_parse_setid` and
grouping by setid alone, which reports `setid 'topic' held by 2 files across types
['plans','walkthroughs']` while `check_collisions` on the same tree returns `[]`.

**THREE RECORD-ACCURACY ERRORS (PR-A03, MEDIUM; PR-A04, MEDIUM; PR-A05, LOW).** F-6 says six
walkthroughs declare `- Set:` and V-03 asks for "all six lines with the corrected descriptives";
measured, the sixth declarer is `5gdzyz` (`20260831-locksafe-01-...`), whose `- Set: locksafe` is a
bare token with no descriptive and no false clause, correctly absent from `- Scope-Paths:` and which
must stay byte-unchanged - while `u8tiox`, which IS in `- Scope-Paths:`, declares no `- Set:` line at
all and is in scope for E-04's history line only. Separately, `u8tiox` carries a THIRD now-false
passage the plan never names, in its `- Date:` block, asserting that `check.setid-collision` "treats
a setid as owned by ONE record type" and that a walkthrough declaring the plan's setid "is reported
as a cross-type collision with it" - the reversed rule stated as current fact. E-04 is right not to
rewrite it, which makes the appended history line the only remedy, so that line must name the removed
arm and the true rule rather than merely pointing at `jji5zx`. And F-8's baseline of 5 findings is
spent: re-measured the sweep reports 3 with a different rule mix, though its load-bearing half
(`check.setid-collision` count 0) is re-confirmed.

**OQ-01 WAS ADDRESSED TO THE REVIEWER AND IS NOW RESOLVED (PR-A06).** It asked whether the five
corrected descriptives should keep their long explanatory form. Answer: KEEP IT. The author's
reasoning is accepted and strengthened by two pieces of evidence - the passage answers a question
that remains non-obvious after the fix (why the walkthrough's Set differs from its subject plan's,
given the setid slot and `Target-Id` carry different things), and deleting explanations is precisely
how the five reversed clauses arose; while `5gdzyz` demonstrates the terse form is also legitimate in
this tree, making this a style choice that does not justify churning five files. Verified harmless:
`_parse_setid` takes the first token before `(` and treats the parenthetical opaquely, and the rule
fires only on a within-type descriptive MISMATCH, which five distinct setids cannot trigger.

Every finding is FIXED. No finding was deferred, so no escalation to a `- Blocking: yes` question is
owed, and OQ-01 moving from `open` to `resolved` removes the plan's only outstanding question. All
four authored `Carrier-Declined` rows were checked against evidence and all four are legitimate; the
strongest is the rejected second fix, where three independent sources (the module's own comment, the
parity test asserting on two surfaces, and open item `e2j5w4`'s explicit "keep the setid pass on the
caller's corpus") endorse the behavior it would have changed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | HIGH | IN-SCOPE | E. Testing and verification | plan Step 0 ("the full sweep yields exactly `['check.ipd-draft-ready-to-review']`"); driven `check_types(root,['all'])` -> `[]` on four fixture variants; the `draft`-status variant alone -> `['check.ipd-draft-ready-to-review']`; the existing row "one setid used by a plan and a spec" expecting `(HISTORY_MISSING,)` at the `approved` default; runner's `_rules(all_drift) != sorted(expected)` and its `clean_row_broken` flag | THE NEW ROW'S EXPECTED SET IS WRONG AND FAILS ON ARRIVAL. The measured set is `()`, not a one-element tuple; the authored value is reachable only via `status="draft"`, which neither this plan nor the existing cross-type row uses. Because a failing CLEAN row sets `clean_row_broken`, the failure would read as the cross-type carve-out being broken rather than as a wrong expectation - the most misleading failure possible for this row. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (correct one tuple and require re-driving) | FIXED | Step 0's measurement replaced with the re-driven `()` and the explanation of where the authored figure came from. E-01 now specifies `()`, forbids `status="draft"`, and requires re-driving at execution. Added F-9. V-01 requires showing the tuple is `()`. |
| PR-A02 | HIGH | IN-SCOPE | B. Security and safety (shared checkout) | plan V-01 ("the diff that temporarily restores the cross-type comparison ... `git diff --stat agent_workflows/check_engine.py` empty"); the plan's own "Explicitly NOT changed: `agent_workflows/check_engine.py`"; `jpn6hy` and `ghna7l` `- Scope-Paths:` both declaring that file; `tl2b2r` declaring `tests/test_check_engine.py`; AGENTS.md shared-checkout rule | V-01 INSTRUCTS EDITING AN UNDECLARED MODULE THAT TWO OTHER PENDING PLANS DECLARE. In a shared checkout a write-then-revert can race a co-worker's edit, and a failed revert leaves the repository's own collision rule mutated with every suite still green. The plan is internally contradictory too: it declares that module explicitly NOT changed and then asks for it to be changed. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium (substitute a route demonstrated at review; no evidence value lost) | FIXED | V-01 and the Required-tests bullet now mandate an in-memory route (scratch re-keying probe or in-process monkeypatch), with the review's own demonstration recorded, and require `git status --porcelain agent_workflows/check_engine.py` EMPTY as a stronger proof than a revert. Added F-10. The gate carries a dedicated paragraph naming this as the one way the plan can do real damage. A Scope-check bullet declares the three live co-editors. |
| PR-A03 | MEDIUM | IN-SCOPE | A. Correctness (record accuracy) | `rg -n "^- Set:" .aw/records/walkthroughs/` -> six lines: five `*closure` plus `5gdzyz`'s bare `- Set: locksafe`; `rg -n "^- Set:"` on `u8tiox` -> no match; `rg -c "may not reuse the Set id"` -> exactly the five | F-6 AND V-03 MISDESCRIBE THE SIX DECLARERS. V-03 asks for "all six lines with the corrected descriptives", but only five carry a descriptive to correct; the sixth (`5gdzyz`) is a bare token with no false clause, is correctly undeclared, and must stay byte-unchanged. Meanwhile `u8tiox`, which IS declared, has no `- Set:` line at all. An executor reading V-03 literally would either edit an undeclared file or hunt for a seventh. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 corrected to name `5gdzyz` as the sixth declarer and to state `u8tiox` declares none. V-03 now distinguishes the five corrected descriptives from `5gdzyz`'s untouched bare token and requires an empty `git status --porcelain` for it. A Scope-check bullet states the same. |
| PR-A04 | MEDIUM | IN-SCOPE | A. Correctness (documentation honesty) | `u8tiox`'s `- Date:` block: "`check.setid-collision` treats a setid as owned by ONE record type ... a walkthrough declaring `- Set: integpath` is reported as a cross-type collision with it (measured 2026-09-18)" | `u8tiox` CARRIES A THIRD NOW-FALSE PASSAGE THE PLAN DOES NOT NAME, and it states the reversed rule as CURRENT FACT rather than as history. E-04 correctly refuses to rewrite it (it is the primary-source record), which makes the appended history line the only remedy available - so a line that merely points at `jji5zx` leaves a reader of that sentence still believing it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11. E-04 now requires the appended line to name the removed arm (`c6648722`), the true rule (D153 / `2lcqno` N1), that the `- Set:` omission is no longer necessary though still permitted, and that the paragraphs below are retained as the pre-fix record. V-04 requires confirming the line does this rather than only naming the plan. |
| PR-A05 | LOW | IN-SCOPE | E. Testing (live-artifact baseline) | driven `check_types(Path('.'),['all'])` -> 3 findings (`check.ipd-uncarried-obligation`, `check.ipd-carrier-finished-unverified`, `check.system-layout-missing`), `check.setid-collision` count 0; bare suite -> `3127 passed, 2 skipped, 3 warnings in 78.55s`; the two collision modules -> `40 passed` | F-8's BASELINE IS SPENT. It records 5 findings including a `check.ipd-lint-diagnostic` that is no longer present; the total is now 3 with a different mix. The load-bearing half survives, so no conclusion moves, but V-04 asks the executor to compare against the stale total, which is the drifting-live-count trap the repository's own convention warns about. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-8 marked superseded with its surviving half stated; added F-12 with the re-driven figures. Required tests and V-04 now set the bar at `check.setid-collision` staying 0 and require the suite baseline to be re-measured in-lane immediately before the change. |
| PR-A06 | LOW | IN-SCOPE | F. KISS and UX (reviewer-addressed question) | plan OQ-01 (`Status: open`, `Owner: reviewer`); `5gdzyz`'s bare `- Set: locksafe`; `check_engine._parse_setid` taking the first token before `(` and treating the parenthetical opaquely; the rule firing only on a within-type descriptive mismatch | OQ-01 WAS ADDRESSED TO THE REVIEWER AND LEFT UNANSWERED, so the plan carried an open question whose only possible owner was the reviewing pass. Leaving it open would have made an otherwise clean plan carry an unresolved question into approval for no reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved to KEEP THE LONG FORM, with the author's reasoning accepted and two supporting pieces of evidence added (the explanation is still needed after the fix; `5gdzyz` shows terse is also legitimate, so this is style not correctness). Owner set to the reviewing pass, status `resolved`, mechanical harmlessness verified via `_parse_setid`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The new row's authored expected set does not reproduce. Correct the tuple, or change the fixture to match the authored figure? | CORRECT THE TUPLE to `()` and keep the fixture mirroring the existing cross-type row. | (a) Pass `status="draft"` to `_plan_text` so the authored `['check.ipd-draft-ready-to-review']` becomes true - rejected: it adds an unrelated content finding to a row whose entire subject is the ABSENCE of a collision, and it diverges from the sibling cross-type row it is meant to parallel. (b) Loosen the runner to ignore incidental findings - rejected outright: the file's own header states rows pin the exact set on purpose, and loosening it would let a content rule silently stop firing tree-wide. | Driven `check_types(root,['all'])` -> `[]` across four variants; the `draft` variant alone producing the authored finding; the existing row's `(HISTORY_MISSING,)` at the `approved` default; the runner's exact comparison and `clean_row_broken` flag. | yes |
| D-2 | V-01's falsification requires the broken behavior. Edit `check_engine.py` and revert, or reproduce the keying out of tree? | REPRODUCE IT OUT OF TREE: a scratch probe re-keying by setid alone, or an in-process monkeypatch. | (a) Edit and revert as authored - rejected: the module is outside `- Scope-Paths:` by the plan's own declaration, two other pending plans declare it, and in a shared checkout a failed revert leaves the collision rule mutated while the suite stays green. (b) Drop the falsification - rejected: it is the only thing that distinguishes this clean row from a row that would pass against any implementation, which is the plan's own stated reason for requiring it. (c) Use `git stash` - rejected for the same shared-checkout reason AGENTS.md gives, and it is broader than the edit it would protect against. | Demonstrated at review: grouping the fixture's records by setid alone reports the cross-type pair while `check_collisions` returns `[]`; `jpn6hy` / `ghna7l` / `tl2b2r` scope paths; AGENTS.md shared-checkout rule; the plan's own "Explicitly NOT changed" line. | yes |
| D-3 | OQ-01 (addressed to the reviewer): keep the long descriptive form, or collapse to a terse one? | KEEP THE LONG FORM with the false clause replaced by the true rule. | (a) Collapse to a bare token like `5gdzyz` - rejected: the passage answers a question that is still non-obvious after the fix (why the walkthrough's Set differs from its subject plan's), and removing explanations is how the five reversed clauses arose in the first place. (b) Delete the parenthetical entirely - rejected as (a) plus a loss of the `Target-Id` pointer the descriptive carries. (c) Leave the question open for the maintainer - rejected: it is a wording choice inside an edit this plan makes either way, with no correctness content, so holding an otherwise clean plan for it would waste a round trip. | `5gdzyz`'s bare form proving terse is legitimate (so this is style, not correctness); `check_engine._parse_setid` treating the parenthetical opaquely; the rule firing only on a within-type descriptive mismatch, which five distinct setids cannot trigger; the five reversed clauses as evidence of what omitted explanation costs. | yes |
| D-4 | `u8tiox`'s third false passage cannot be rewritten (primary-source record). How is it neutralized? | REQUIRE THE APPENDED HISTORY LINE TO CARRY THE CORRECTION explicitly: the removed arm, the true rule, and that the omission is no longer necessary. | (a) Rewrite the passage - rejected: it is the primary-source record of the defect as it then behaved, and AGENTS.md's own convention is to append rather than rewrite an executed record's narrative. (b) Let the history line just cite `jji5zx` - rejected: the passage states the reversed rule as current fact, so a bare pointer leaves a reader of that sentence believing it, which is the exact harm this plan exists to remove from the other five files. | The passage read verbatim at review; E-04's own (correct) prohibition on rewriting it; the five closure walkthroughs as the precedent for what an uncorrected false clause propagates into. | yes |
