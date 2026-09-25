# Review: Make the executed-transition hook read only the plan's own Status line

- Subject-Id: kecxnb
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `3243791b`. The plan cites `0c2e7970`, an ancestor; both were checked and
the measurements agree. The target plan was committed and unchanged, so the pre-review snapshot was
correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming` (exit 0) BEFORE review and again at `--phase review-finalize` afterwards.

THE PLAN IS CORRECT, ITS FIX IS THE RIGHT ONE, AND I PROVED BOTH RATHER THAN READING THEM. F-1 holds:
`_has_executed_status` matches a fenced `- Status: executed` and returns True for a plan whose own
status is `approved`. The chosen mechanism is also right, and its docstring says so in the plan's own
terms: `selectors.metadata_region` exists precisely so that "a document that merely QUOTES a metadata
block ... cannot be read as ASSERTING the quoted values." F-2's caveat is unusually careful and I
checked it specifically because a hedged claim is where an error hides: `check_engine._status_meta`
does take the first match, so it is indeed correct FOR A PLAN WITH FRONT-MATTER STATUS, and it is
wrong for one without. That residual half is now carried as item `pyk78c`.

THE STRONGEST EVIDENCE I ADDED IS A COMPATIBILITY PROOF THE PLAN DID NOT CLAIM. This hook's own test
suite, 1267 lines and six tests, was deleted by `19313eed`, so the plan proposes changing a gate that
currently has ZERO test coverage. I recovered that suite from `19313eed^` and ran it: `6 passed in
3.65s` against today's hook. Then I monkeypatched the plan's PROPOSED implementation in and ran the
same six: `6 passed` again. So the change is behavior-compatible with the hook's end-to-end refusal
verdicts, its merge-aware evidence paths, and its pre-commit registration. That is the single most
useful fact for an approver of a gate change with no coverage, and E-01 now carries it.

THE DOMINANT CORRECTION IS PR-901, WHICH NARROWS THE CONCERN AND THEREBY FIXES THE TEST. The Concern
says a plan "that quotes that line (as lifecycle docs and reviews do) is refused". Measured, two of
those three implied triggers cannot happen. The hook reads ONLY `.aw/records/plans/**/*.ipd.md`
(`_is_plan_path` returns False for the lifecycle doc and for a `.review.md`), so a doc or review
quoting the line is invisible to it. And detection is a HEAD-versus-staged DELTA, so staging an
ordinary edit to a plan that ALREADY contains the quote yields `check() -> (0, [])`; I built that
scenario and confirmed it. The live trigger is exactly one thing: a commit that ADDS the quote to a
plan whose own status is not executed. I built that too, and it is refused with exit 1 and
`gained '- Status: executed'` plus advice to run `aw ipd finalize`, which is nonsense for a plan that
is not transitioning. This matters beyond accuracy: E-02's four unit cases never touch `check()`, so
without an end-to-end case the plan would fix the function while nothing proved the COMMIT is accepted.
E-02 now carries that case.

THE SECOND MATERIAL FINDING IS PR-902, AN IMPLEMENTATION TRAP IN E-01'S OWN MECHANISM.
`metadata_region` returns the WHOLE input when a record presents no `##` heading; that is deliberate
and its docstring records it as correct for 25 of 1614 tracked records. So "read the status from the
metadata region" is satisfiable by an any-match-in-region scan that is STILL WRONG for a headingless
plan: measured, such a plan returns False under a first-bullet implementation and True under
any-match. E-01's wording did say "first", so this is a hardening rather than a contradiction, but the
distinction was unexplained and is exactly what a faster model would drop. It is LATENT, not live: 0
of 776 tracked plans lack a `##` heading, and I measured that rather than assuming it. V-01 now
requires the headingless case, which is the only one of the five that separates a correct
implementation from a plausible wrong one.

PR-903 IS A COVERAGE-PROVENANCE PROBLEM, and it is the finding most likely to mislead a future reader.
E-02 creates `tests/test_executed_transition_gate.py`, the exact path of the 1267-line suite that
`19313eed` deleted. Four unit cases at that path will read, to anyone who looks later, as the tests for
this hook. They are not: the deleted suite covered the end-to-end verdicts, both git merge stages, and
the pre-commit config registration, and it still passes. The plan is right not to restore it here, but
the file must say what it is. E-02 now requires that docstring, F-5 records the measurement, and the
restoration is carried as item `ove09p`.

ON SEVERITY, which I checked because the plan files this as a `bug` with `Blocks-Release: next` and a
MED finding: MED is honest and I kept it. The hook's own refusal text says `--no-verify` bypasses it and
names `aw check`/`aw doctor` as the backstop, so a false refusal costs an operator time rather than
permanently blocking them. I added the reason it is not merely cosmetic either, and it is the argument
an approver should see: a gate that refuses legitimate commits trains an operator to reach for
`--no-verify`, which disables the gate for the genuine transitions it exists to catch. That is a real
cost and it is now stated in the gate rather than left implicit.

ONE DIRECTIONAL CHECK worth recording because it is the thing that could have made this change
dangerous: the fix makes the hook strictly MORE PERMISSIVE, so the question is whether it loosens the
real gate. It does not. Cases (b) metadata `executed`, (c) metadata `done`, and (d) metadata `executed`
with an OQ block's own `- Status: open` below all still return True under the proposed implementation,
verified individually. A stop condition now covers the case where any of them does not.

I also verified the two mechanical worries a reviewer should not leave to the executor: `selectors`
does not import the hook (no circular import) and importing it costs about 1ms, so the pre-commit path
is not measurably slowed; and the module constants `_STATUS_EXECUTED_LINE` / `_STATUS_DONE_LINE` are
used at exactly one site, the line being replaced, so the change orphans them. The scope fence now says
to either keep them in use or remove them and declare which, rather than leaving a dead constant behind.

Backlog item `4vhe5o` carries `- Blocks-Release: next`; the plan correctly inherits it, so the gate is
preserved by the handoff, and the gate now says so explicitly. Items `ove09p` and `pyk78c` were filed
at review and stay open with their own state.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | MEDIUM | IN-SCOPE | A. Correctness / E. Testing | `_is_plan_path` on the lifecycle doc and on a `.review.md` -> `False`; staging an ordinary edit to a plan already containing the quote -> `check()` returns `(0, [])`; staging the commit that ADDS the quote -> exit 1 with `gained '- Status: executed'` and finalize advice | THE CONCERN OVERSTATES THE TRIGGER, AND THE OVERSTATEMENT HIDES THE MISSING TEST. Two of the three implied triggers cannot occur: the hook reads only plan paths, so a lifecycle doc or review record quoting the line is invisible to it, and detection is a HEAD-versus-staged delta, so an ordinary edit to a plan that already contains the quote is not reported. The one live trigger is a commit that ADDS the quote to a non-executed plan. Because the plan never identified that, E-02's four unit cases exercise `_has_executed_status` in isolation and nothing proves the COMMIT is accepted, which is the defect a human actually experiences. | C:Low; U:Low; S:Low; F:Medium (a function-level fix with no end-to-end proof); Overall:Low | FIXED | Concern rewritten with the measured trigger and the two non-triggers; F-3 added; E-02 now requires an end-to-end case asserting `check()` returns `(0, [])` for that exact staged commit, and V-02 requires both it and its reverted-code counterpart. |
| PR-902 | MEDIUM | IN-SCOPE | A. Correctness (an implementation trap in the chosen mechanism) | `metadata_region` docstring: header exhaustion yields the whole input, correct for 25 of 1614 records; driven on a headingless plan with metadata `approved` + fenced `executed`: first-bullet -> False, any-match -> True; 0 of 776 tracked plans lack a `##` heading | "READ THE STATUS FROM THE METADATA REGION" IS SATISFIABLE BY AN IMPLEMENTATION THAT IS STILL WRONG. For a record with no `##` heading the region is the WHOLE input by design, so an any-match-in-region scan reproduces the original defect. E-01 did say "first", but the reason was unstated, which is exactly the detail a weaker executor drops, and no validation item would have caught it: the plan's own (a) and (b) cases both pass under the wrong implementation. | C:Low; U:Low; S:Low; F:Medium (a plausible implementation silently half-fixes the bug); Overall:Low | FIXED | E-01 now explains why the FIRST bullet is load-bearing, cites the docstring and the 0-of-776 measurement marking it latent rather than live, and V-01 requires the headingless case as the discriminating evidence. Added F-4 and a conventions bullet. |
| PR-903 | LOW | UNDER-SCOPE | E. Testing (coverage provenance) | `git show 19313eed^:tests/test_executed_transition_gate.py` -> 1267 lines, 6 tests covering staged verdicts, merge-aware evidence, both git stages and pre-commit registration; recovered and run -> `6 passed in 3.65s` | E-02 RECREATES THE PATH OF A DELETED SUITE, SO FOUR UNIT CASES WILL LATER READ AS THIS HOOK'S COVERAGE. The gate currently has ZERO tests because `19313eed` deleted them, and the deleted ones still pass. Adding four narrow cases at that exact path is right for this plan's scope but silently misrepresents the coverage state unless the file says what it is. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 requires a module docstring stating it is a NEW narrow file and not the restored suite; F-5 records the measurement; the restoration is carried as item `ove09p`, filed at review. V-02 requires confirming the docstring. |
| PR-904 | LOW | UNDER-SCOPE | D. Anti-regression (a compatibility proof the plan did not make) | The six recovered tests -> `6 passed` against today's hook; the same six with the PROPOSED implementation monkeypatched in -> `6 passed`; cases (b) `executed`, (c) `done`, (d) `executed` + OQ `open` all -> True under the proposal | A GATE WITH NO TEST COVERAGE WAS BEING CHANGED WITH NO REGRESSION ARGUMENT, and the change is in the PERMISSIVE direction, which is the direction that can quietly disable a gate. The plan asserted the metadata case "still does" count but offered no evidence, and nothing addressed whether the hook's other behaviors survive. | C:Low; U:Low; S:Medium (a permissive change to a bypass-prevention gate); F:Low; Overall:Low | FIXED | E-01 now records the measured compatibility proof (the deleted suite run against the proposed implementation, `6 passed`); the gate states the change is strictly more permissive in exactly one situation and that (b)/(c)/(d) still return True; a stop condition refuses the change if any of those three flips to False. |
| PR-905 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: two sentences, no scope fence, no approval paragraph, no stop conditions, an UNCONDITIONAL finalize instruction; `_STATUS_EXECUTED_LINE`/`_STATUS_DONE_LINE` used at exactly one site, the line being replaced | THE GATE CARRIED ONLY THE COMMIT RULE, AND THE CHANGE ORPHANS TWO MODULE CONSTANTS NOBODY WAS TOLD ABOUT. No scope fence (so finalize reconciliation had nothing to reconcile against), no statement of what approval means for a gate change, no stop conditions, and finalize instructed unconditionally rather than with runner/executor ownership. Separately, both status constants become dead once the loop they serve is replaced, and an unremarked dead constant is how a reader later mistakes the old matching rule for live code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: an approval paragraph (including the permissive direction and the honest MED severity with the `--no-verify` habit as the real harm), a per-path scope fence naming the untouched functions and the orphaned constants as a declare-which decision, the honesty rule naming the two easiest-to-fake claims, two genuine stop conditions (a loosened real gate; a circular import or slowdown rather than inlining a second boundary rule), conditional runner/executor finalize ownership, and the `4vhe5o` close with its inherited release gate stated. |
| PR-906 | LOW | OVER-SCOPE (recorded, not absorbed) | A. Correctness (the other half of the plan's own F-2) | `check_engine._status_meta` on a plan with NO front-matter Status that quotes `- Status: executed` in a fence -> `'executed'`; consumed by `check.status-untooled`; the proposed hook fix returns False for that same input | THE PLAN'S F-2 IS HALF THE STORY AND SAYS SO CAREFULLY, BUT THE OTHER HALF IS A REAL DEFECT. `_status_meta` reads the first `- Status:` anywhere in the file rather than within the metadata region, so a plan with no front-matter Status that quotes the line reads as `executed` there. After this plan lands, the HOOK is strictly stricter than its sibling detector, which is an asymmetry worth recording rather than discovering later. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded and carried rather than repaired in place: a different module with a different consumer, and absorbing it would widen a one-function hook fix into a `check_engine` change. Filed as item `pyk78c` (`bug`, `Blocks-Release: next` per the live-bug gate) and recorded in Deferred with that carrier; the scope fence names `check_engine.py` as expected-unmodified. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan proposes changing a gate that has no test coverage. Accept its correctness argument, or establish a regression baseline first? | Recover the deleted suite, run it against today's hook AND against the proposed implementation, and record both results in the plan. | (a) Accept the plan's assertion that the metadata case "still does" count - rejected: that is the whole risk surface of a permissive change to a bypass-prevention gate, and no evidence was offered. (b) Read the hook and reason about it - rejected: reading shows intent, and the six deleted tests cover merge stages and hook registration that no amount of reading the one function would exercise. | recovered suite -> `6 passed in 3.65s`; the same six with the proposal monkeypatched -> `6 passed`; cases (b)/(c)/(d) -> True | yes |
| D-2 | Should the Concern's "as lifecycle docs and reviews do" framing stand? | No: narrow it to the measured trigger (a commit ADDING the quote to a non-executed PLAN). | (a) Leave it - rejected on measurement: `_is_plan_path` excludes docs and reviews outright, so two thirds of the stated trigger cannot occur and an executor would look for a failure mode that does not exist. (b) Narrow it silently - rejected: the narrowing is what reveals E-02's missing end-to-end case, so the reasoning has to be visible. | `_is_plan_path` -> False for the lifecycle doc and a `.review.md`; ordinary edit -> `check()` `(0, [])`; the adding commit -> exit 1 `gained '- Status: executed'` | yes |
| D-3 | E-02 recreates the path of a 1267-line deleted suite with four unit cases. Restore the suite, add the four, or both? | Add the four plus one end-to-end case, require the file to declare what it is, and carry the restoration separately. | (a) Restore the full suite here - rejected: it is 1267 lines against a one-function fix, and the maintainer has not ruled on restoring it; that decision belongs to its own item. (b) Add the four silently - rejected: four cases at that exact path misrepresent the coverage of a gate whose end-to-end and merge-stage tests are gone. (c) Use a different filename to avoid the confusion - rejected: the canonical path is the right home, and a second name would fragment the hook's tests permanently. | the recovered suite's 6 tests and their subjects; `6 passed` at review; item `ove09p` filed and resolvable | yes |
| D-4 | Two adjacent defects found at review (the deleted suite, `_status_meta`'s unbounded read): fix, absorb, or carry? | Carry both as filed backlog items and declare the touched-not modules in the scope fence. | (a) Fix `_status_meta` here - rejected: a different module with a different consumer (`check.status-untooled`), so it needs its own validation and would widen a narrow hook fix. (b) Mention them in prose only - rejected: untracked prose is invisible to the attention view, so both would be rediscovered rather than scheduled, and a `Carrier` naming nothing is a false handoff claim. (c) Reuse one carrier for both - rejected: they are independent concerns with different work kinds and priorities. | `_status_meta` driven -> `'executed'` on a no-front-matter-Status plan; items `ove09p` and `pyk78c` filed and both resolving | yes |
