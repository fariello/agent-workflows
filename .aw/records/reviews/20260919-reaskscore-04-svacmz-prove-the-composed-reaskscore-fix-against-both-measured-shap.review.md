# Review findings: plan svacmz

- Subject-Id: svacmz
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `27d399ed`. The plan on disk was byte-identical to the sealed lane input and
`git status --porcelain` was empty, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean`, 0 findings, exit 0. The watermark is unchanged at
04 (no E-item added; every finding was fixed by strengthening an existing item).

THIS PLAN SHOULD EXIST AND ITS PREMISE IS CORRECT. I verified the coverage-gate claim rather than
accepting it: the parent `s0gnha` does carry verification items no sibling covers, `grep` confirms no
child mentions SHAPE A or SHAPE B (0 hits in all three) and none mentions the collision case (the only
`collision` hits in the Set are `dy9ymn`'s OQ-04 about a retry counter and a `ty7w6o` scope-fence line,
neither being the truncated-and-rescued case), and the runner does skip the pre-transition E/V checkpoint
when it retires an orchestrator. So the two parent items would have been ticked unperformed, and E-03 is
genuinely the only place the composed fix is demonstrated. The plan's self-restraint is also right: a
fourth hand in the same predicates is a real hazard and declaring tests-and-evidence-only is the correct
shape. Note the parent has since been revised (its E-02 is now a RECEIPT CHECK over this plan's evidence
blocks rather than a duplicate verification), which resolves the duplication this plan was authored
against and makes the two files consistent.

WHERE THIS REVIEW SPENT ITS EFFORT: one blocker that stops the plan running at all and is not fixable
from inside this file, plus three items whose assertions were weaker or less satisfiable than they read.

**1. This plan cannot dispatch today, and the cause is a sibling's unresolved finding.** I ran the
evaluator rather than reasoning about it: `check_engine.evaluate_ipd_dependencies` on this file returns
`check.ipd-dependency-findings-blocked`, detail "dependency `executed:ty7w6o` resolves but does not
satisfy the edge: ty7w6o: review finding PR-001 is high/open and unresolved". `aw check` reports the same
rule against this file at `error` severity. The refusal runs through the SHARED predicate
(`runner_shared._findings_block_reason` at `runner_shared.py:10240` delegating to
`review_findings.subject_gating_blocks`, consumed for execute-action edges at `oc_runipd.py:3761-3765`),
so it is not a per-surface quirk that a different host would skip. `review_findings.subject_gating_blocks`
confirms directly: `ty7w6o` returns one HIGH/open block (PR-001), `s0gnha` returns one (PR-005), while
`skn8uk` and `dy9ymn` return clean. THE CONSEQUENCE IS THE EXACT LOSS THIS PLAN EXISTS TO PREVENT: a run
marks this item `dependency-blocked` and continues, so the Set's only end-to-end proof never executes,
reported as handled and never performed. I did not fix it here. The honest remedy is work on `ty7w6o`
(whose PR-001 is a real defect, its `aw backlog set` route printing `unchanged` and writing no history,
and whose own `- Readiness:` is `no-go`), and the two alternatives are both wrong: lowering the repository
gate threshold weakens every dependency edge to unblock one Set, and dropping the edge destroys the
merged-result property the edge exists for. Escalated as blocking OQ-02 per the gate-threshold rule
(`review_findings_gate.block_at` resolves to the `high` default, measured via
`config.read_review_findings_gate` returning None with `REVIEW_GATE_DEFAULT` = `high`).

**2. E-01 named one definition site per constant, and the site it omitted is the one that matters most
to this Set.** Two of the five names are defined more than once: `EXECUTION_SUCCESS_STATES` twice, as a
separate set literal per host (`oc_runipd.py:492`, `agy_runipd.py:563`, which
`tests/test_runner_shared.py:1407` records in terms as "EQUAL BUT NOT IDENTICAL"), and `TERMINAL_STATES`
three times (`oc_runipd.py:470`, `agy_runipd.py:541`, `runner_shared.py:12262`). Five names, eight sites.
The omitted third `TERMINAL_STATES` copy is the one `runner_shared.reconcile_disposition` actually reads
(`runner_shared.py:12575-12628`, the membership test at `:12624`), and `reconcile_disposition` is the exact
function `skn8uk` calls a SECOND time for its rescore. So a one-sided widening of the shared copy would
have changed the rescore's own verdict while passing E-01 as authored. E-02's `EQUAL_CONSTANTS` pin does
not close the gap either, for the reason in finding 3. All three copies are equal today (measured, each
the same eleven-member set).

**3. E-02 credited the cross-host pin with more than it asserts.** `EQUAL_CONSTANTS` is
`("EXECUTION_SUCCESS_STATES", "TERMINAL_STATES")` (`tests/test_rununify_run_queue.py:165`) and
`test_the_equal_constants_are_still_equal_across_hosts` (`:390`) compares `getattr(oc_runipd, name)`
against `getattr(agy_runipd, name)` and nothing else. It therefore proves the two HOST copies AGREE; it
proves nothing about their VALUE, since an identical widening of both hosts still passes, and nothing
about `runner_shared.TERMINAL_STATES`. The plan read it as covering the constants, which would have left
E-01 looking redundant when in fact neither item subsumes the other. I also named the two ordering pins
the Set actually perturbs (`test_submissions_are_collected_before_the_disposition_is_reconciled` at `:207`
and `test_the_disposition_is_reconciled_before_integration` at `:261`), because `skn8uk` declares that
file in its own `- Scope-Paths:` and a sibling editing the file that holds the safety pin is the case
worth watching: a relaxed assertion plus a new passing test leaves the file green with the guard gone.

**4. V-02 demanded an empty `git diff`, which is unsatisfiable.** Measured:
`git diff --stat 4f4aaa27..HEAD -- tests/test_rununify_run_queue.py` is already 3 insertions and 2
deletions, landed by unrelated main commits (`eee6f427` "docs: repoint 9 citations at the files their
targets actually live in", after `d4dd6b88`), and zero of those changed lines match `assert`. On top of
that, `skn8uk` legitimately edits the other pin file. So an executor following "an empty diff is the
expected and strongest result" would either report a false failure or wave the real diff through, and the
second is the dangerous outcome because it trains the reader to ignore this diff. Re-expressed as an
assertion-level bar with sibling attribution, and the baseline re-specified as the Set's own merge-base
rather than a remembered hash.

**5. E-04's general argument rested on two conditions that are vacuous for the measured shape.** It
required showing `dy9ymn`'s conjunction false on all four conditions for a rescued turn, including
"unchanged head" and "clean tree". But `dy9ymn`'s own review measured those two as TRUE BY CONSTRUCTION on
an isolated lane turn: `attempt["ending_head"]` and `attempt["ending_status"]` read
`git_head(repo)`/`git_status(repo)` on the MAIN checkout while the lane works in `work_dir`, so they hold
even for a lane that committed substantial real work, and the measured shape is an isolated lane turn. The
conclusion (the two fixes cannot collide) is correct, but the argument as written was unsound, and an
unsound proof of a true property is worse than none here because it would be cited later as settled. Re-based
onto the two load-bearing conditions: no outcome file and no lane commit. Both are violated by a rescued
turn for reasons I verified in the siblings: `skn8uk`'s rescore fires only when
`"outcome" in receipt["collected"]` (its E-02 as revised, precisely because a gate on `receipt["status"]`
passes on a lane that submitted nothing), so a rescued turn has an outcome file by definition, and SHAPE
A's rescued turn committed its work, so `commits_ahead > 0`.

**6. V-04 could have been satisfied without proving the budget was respected.** It asked for "exactly one
re-dispatch within budget" from the status alone. A retry that fired once because the code hardcoded one
attempt and a retry that fired once because the budget allowed one are indistinguishable that way, and only
the former breaks at `--retry-budget 3`. `dy9ymn` E-04 (as revised) keeps a per-item counter mirroring
`integration_attempts`, so the counter's value is observable; V-04 now requires it pasted beside each
outcome. This is the same defect class `dy9ymn`'s own V-04 was hardened against, applied here because this
plan re-verifies the same behavior on the merged result.

**CITATIONS: ALL ACCURATE, WHICH IS WORTH STATING because the three siblings each had drifted ones.**
Every citation in this plan resolves: `agy_runipd.py:541,562,563`, `runner_shared.py:6736,10897`, and
`tests/test_rununify_run_queue.py:165` all land exactly on their named targets. The plan was authored
2026-09-19 (commit `11cbbd30`), after the file growth that moved the siblings' anchors, which explains the
asymmetry. Its omissions were of ADDITIONAL sites, not wrong offsets.

I also confirmed the two claims the plan makes about its own scope are true rather than assumed: the
declared `tests/test_reaskscore_composed.py` does not yet exist (so it is a new module, consistent with
OQ-01's default), and this plan declares no `.spec.md` path, which is the parent's "NO CHILD EDITED A
SPEC" check. The Set-level suite is green at this HEAD: the three files this plan asserts on pass,
`259 passed in 23.46s` for
`tests/test_rununify_run_queue.py tests/test_rununify_execute_item_gates.py tests/test_runner_shared.py`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; C. architecture; G. executability | `check_engine.evaluate_ipd_dependencies` on this file returns `check.ipd-dependency-findings-blocked`: "dependency `executed:ty7w6o` resolves but does not satisfy the edge: ty7w6o: review finding PR-001 is high/open and unresolved". `review_findings.subject_gating_blocks` returns one HIGH/open block for `ty7w6o` and one for `s0gnha`, clean for `skn8uk`/`dy9ymn`. Refusal path `runner_shared.py:10240` -> `review_findings.subject_gating_blocks`, consumed at `oc_runipd.py:3761-3765`. Threshold `high` via `config.REVIEW_GATE_DEFAULT` | This plan cannot dispatch: its `executed:ty7w6o` edge is refused for a sibling's unresolved HIGH finding, so a run marks it `dependency-blocked` and the Set's ONLY end-to-end proof of the composed fix never executes, reported as handled and never performed. Not fixable from inside this file | C:Low; U:Low; S:Low; F:High; Overall:High | OPEN | Escalated as blocking OQ-02 with the measurement and three shapes. Recommended: resolve `ty7w6o` PR-001 (a real defect, and `ty7w6o` is `no-go` and unrunnable today anyway), which clears this edge as a side effect. Explicitly NOT recommended: lowering the repository gate threshold (weakens every edge) or dropping the edge (destroys the merged-result property). Gate paragraph now records the live block so no operator reads approval as the only barrier |
| PR-002 | HIGH | IN-SCOPE | D. anti-regression; E. testing | Five names, EIGHT sites: `oc_runipd.py:470,492`; `agy_runipd.py:541,563`; `runner_shared.py:6736,10843,10897,12262`. `reconcile_disposition` (`runner_shared.py:12575`) reads the SHARED `TERMINAL_STATES` at `:12624`, and it is the function `skn8uk` calls a second time. `tests/test_runner_shared.py:1407` records the host copies as "EQUAL BUT NOT IDENTICAL" | E-01 asserted one site per constant, so a one-sided widening of the duplicated names would pass. The omitted third `TERMINAL_STATES` copy is the one the Set's own rescore reads, making it the highest-consequence site in the list | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | E-01 and V-01 now enumerate all eight sites, require the three `TERMINAL_STATES` copies shown mutually equal, and require `EXECUTE_REPORTING_SUCCESS_STATES` shown still DERIVED from `SUCCESS_STATES` by subtraction rather than matching a literal |
| PR-003 | MEDIUM | IN-SCOPE | D. anti-regression; E. testing | `EQUAL_CONSTANTS = ("EXECUTION_SUCCESS_STATES", "TERMINAL_STATES")` (`tests/test_rununify_run_queue.py:165`); `test_the_equal_constants_are_still_equal_across_hosts` (`:390`) compares only `getattr(oc_runipd, name)` against `getattr(agy_runipd, name)` | E-02 described the pin as pinning the two constants, but it pins only cross-host AGREEMENT: an identical widening of both hosts passes, and the shared third copy is outside its reach. Read that way, E-01 looks redundant when neither item subsumes the other | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states exactly what the pin does and does not cover and that neither item subsumes the other; it also names the two ordering pins the Set perturbs and requires each be shown UNCHANGED rather than merely green, since `skn8uk` edits that file |
| PR-004 | MEDIUM | IN-SCOPE | E. testing; G. executability | `git diff --stat 4f4aaa27..HEAD -- tests/test_rununify_run_queue.py` = 3 insertions, 2 deletions from `eee6f427` (docs citation repoint); 0 changed lines match `assert`. `skn8uk` declares `tests/test_rununify_execute_item_gates.py` in its own `- Scope-Paths:` | V-02 required a `git diff` with "an empty diff the expected and strongest result", which is already false and will be more so after `skn8uk` runs, so the item forces either a false failure or a waved-through real diff | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-02 now sets an ASSERTION-LEVEL bar (each changed line shown to be comment/docstring/citation, or attributed to the sibling that changed it), re-specifies the baseline as the Set's own merge-base rather than a remembered hash, and states that a changed assertion in the gates file is expected from `skn8uk` and must be an addition or correction, never a relaxation |
| PR-005 | MEDIUM | IN-SCOPE | A. correctness; E. testing | `dy9ymn` E-01 as revised: `attempt["ending_head"]`/`["ending_status"]` are `git_head(repo)`/`git_status(repo)` on the MAIN checkout while the lane is `work_dir`, so both hold for an isolated lane that committed real work. `skn8uk` E-02 gates its rescore on `"outcome" in receipt["collected"]` | E-04/V-04 required the exclusivity argument to show all FOUR of `dy9ymn`'s conditions false for a rescued turn, but two are vacuous on the measured (isolated) shape. The conclusion is right and the argument was unsound, which is worse than none because it would later be cited as settled | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 and V-04 now argue from the two LOAD-BEARING conditions (no outcome file, no lane commit), require the mode to be named for any control using the other two, and explicitly FAIL the item for an argument resting on the vacuous pair or claiming all four are violated on an isolated lane |
| PR-006 | MEDIUM | UNDER-SCOPE | E. testing | `dy9ymn` E-04 (as revised) keeps a per-item counter mirroring `integration_attempts`; a status alone cannot distinguish a hardcoded single attempt from a budget-permitted one, and only the former breaks at `--retry-budget 3` | V-04 asked for "exactly one re-dispatch within budget" provable from the status, so it could pass against code that hardcoded one retry and ignored the budget entirely | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-04 now requires the per-item counter's value pasted beside each outcome, matching the bar `dy9ymn`'s own V-04 was hardened to |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's dependency edge is refused by a sibling's unresolved HIGH finding (PR-001). Fix it here, or escalate? | ESCALATE as blocking OQ-02, naming three shapes with a recommendation, and record the live block in the gate paragraph so no operator reads human approval as the only barrier. | (a) Drop the `executed:ty7w6o` edge to clear the gate: rejected, it silences the check while destroying the property the edge exists for, since only a post-merge dispatch can observe the MERGED result the parent asks about. (b) Lower `review_findings_gate.block_at` below `high`: rejected, a repository-wide policy change made to unblock one Set, weakening every other dependency edge. (c) Resolve `ty7w6o` PR-001 myself in this lane: rejected, this workflow reviews the named plan and must not modify a sibling, and `ty7w6o` is `Readiness: no-go` so it needs its own round regardless. | `check_engine.evaluate_ipd_dependencies` returns `check.ipd-dependency-findings-blocked` on this file; `review_findings.subject_gating_blocks` returns HIGH/open PR-001 for `ty7w6o`; shared refusal at `runner_shared.py:10240` consumed at `oc_runipd.py:3761-3765`; threshold `high` from `config.REVIEW_GATE_DEFAULT`. | yes |
| D-2 | E-01 named one site per constant while two names are multiply defined (PR-002). Add the missing sites, or rewrite the item around a cross-host pin? | ENUMERATE all eight sites explicitly in both E-01 and V-01, and require the three `TERMINAL_STATES` copies shown mutually equal. | (a) Delegate to the existing `EQUAL_CONSTANTS` pin: rejected, it compares hosts only and cannot see either the VALUE or the shared third copy. (b) Assert only the shared copy since that is what `reconcile_disposition` reads: rejected, the host copies feed the cascade and the exit code, so a one-sided edit there is exactly the silent class this item guards. (c) Leave five sites and note the duplication in prose: rejected, an item whose assertion misses a site is not strengthened by a comment. | `oc_runipd.py:470,492`; `agy_runipd.py:541,563`; `runner_shared.py:6736,10843,10897,12262`; `reconcile_disposition` reads the shared copy at `:12624`; `tests/test_runner_shared.py:1407` records the host copies as equal-not-identical. | yes |
| D-3 | V-02's empty-diff bar is unsatisfiable (PR-004). Update the baseline hash, or change the bar? | CHANGE THE BAR to assertion-level with sibling attribution, and re-specify the baseline as the Set's own merge-base rather than any hash. | (a) Pin a newer baseline hash: rejected, it rots the same way and `skn8uk` will legitimately edit the other pin file during the Set, so a file-level empty diff can never be the bar. (b) Drop the diff requirement and rely on the tests passing: rejected, that is precisely the hole, since a relaxed assertion plus a new passing test leaves the suite green with the guard removed. | `git diff --stat 4f4aaa27..HEAD` on the pin file = 3 insertions, 2 deletions from `eee6f427`, 0 assert lines; `skn8uk` declares `tests/test_rununify_execute_item_gates.py` in `- Scope-Paths:`. | yes |
| D-4 | E-04's four-condition exclusivity argument is unsound on the measured shape (PR-005). Drop the general argument, or re-base it? | RE-BASE it onto the two load-bearing conditions and require the mode to be named for any control using the vacuous pair. | (a) Drop the general-argument requirement and accept a worked example: rejected, the plan is right that an accidental ordering is the expensive failure (re-dispatching committed work), so the general argument is the point of the item. (b) Keep all four conditions: rejected, two are true by construction for a rescued isolated turn, so the proof would be invalid while reading as complete. | `dy9ymn` E-01 as revised (main-checkout `git_head`/`git_status` versus `work_dir` lane); `skn8uk` E-02's `"outcome" in receipt["collected"]` gate; SHAPE A's rescued turn commits, so `commits_ahead > 0`. | yes |
| D-5 | OQ-01 (new test module versus extending an existing one) is recorded as non-blocking with a default. Resolve it, or leave it? | LEAVE IT as the author framed it, with the new-module default. | (a) Decide it as reviewer: rejected, it is genuinely an implementation choice with both routes conforming, the value of the reconstruction is independent of its location, and V-03/V-04 demand the output rather than a path. (b) Escalate it: rejected, nothing about it needs a human and it blocks nothing. | `tests/test_reaskscore_composed.py` does not exist in the tree, consistent with the stated new-module default; V-03/V-04 demand reconstruction output, not file paths. | yes |
