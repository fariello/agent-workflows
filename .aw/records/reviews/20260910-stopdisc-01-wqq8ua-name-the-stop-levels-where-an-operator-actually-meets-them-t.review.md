# Review: name the stop levels where an operator actually meets them, child wqq8ua (Set stopdisc)

- Subject-Id: wqq8ua
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `6882f7c6`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review, and `--phase review-finalize` CONFORMED after the revisions. No open questions
remain (OQ-01 was already resolved; OQ-02 is resolved at review from evidence). No product code was
modified by this review.

DISCLOSURE: the plan was authored by the same model family, so this is close to a self-review and is worth
less than an independent one. Its value therefore rests on what was EXECUTED. Fifteen things were run:
`oc run stop --help` on both hosts; `render_request_accepted`; `SIGINT_LADDER` and `SIGTERM_LEVEL`;
`interrupt_menu_is_safe` and `_sigint` read in full; the menu's four choices evaluated to their recorded
levels; `start --help` grepped for stop/interrupt/ctrl on both hosts; both hosts' continuity footers
rendered on both branches; the interrupt-message sites and their exit codes; the `resume` subparser's
formatter, plus a minimal argparse reproduction of the reflow; the six shipped footer tests and the four
`assertNotIn` assertions; spec `c4gd2h` R12 and its amendment note plus `git log` on the spec file; backlog
`4awwg4`'s front matter; the joint stop suite; and the bare full suite.

THE PLAN'S NARROWING DISCIPLINE IS EXEMPLARY AND I KEPT ALL OF IT. It graduated an item most of whose asks
had already shipped and, rather than rebuilding them, ran the code and cut them. Every cut re-verified
correct: the `stop` verb's help really does render four per-level descriptions and four worked commands;
`render_request_accepted` really does return the level, the awaited boundary and the exact escalation
command, verbatim as quoted; the run-level help really does match nothing for stop, interrupt or ctrl on
both hosts; the footer really does mention stopping nowhere; and the interrupt message really is the two
quoted sentences with exit codes 143 and 130 intact. F-2 through F-10 all hold. The three surviving
surfaces are the right scope, and the refusal to duplicate the `stop` verb's per-level text is the correct
reading of P8.

THE FINDING THAT MOST CHANGES THE PLAN IS THAT ITS OWN BLOCKING DISCOVERY HAS EXPIRED. F-1 asserts that the
interactive Ctrl-C menu contradicts spec `c4gd2h` R12, calls that a pending maintainer decision, and shapes
E-01 entirely around not saying anything that conflict would make untrue. R12 WAS AMENDED ON THE
MAINTAINER'S DECISION on 2026-09-09, in commit `bc2ed703`, one day after this plan was authored: it now
specifies TWO paths, R12.1 the interactive four-choice menu and R12.2 the `SIGINT_LADDER`, and states that
"both must reach level 1 on a first press". The spec's own amendment note argues the change on the merits
and calls the two-stream predicate a safety FIX rather than a documentation of shipped code. So the conflict
is resolved, in favor of the code, and the plan's central constraint no longer exists.

TWO MORE OF F-1's FACTS ARE ALSO WRONG, AND BOTH WOULD HAVE PROPAGATED INTO OPERATOR-FACING TEXT. The
interactive gate is not `sys.stdin.isatty()`: it is `interrupt_menu_is_safe`, which requires a TTY on BOTH
streams and the absence of `AW_NONINTERACTIVE`/`CI`, and whose docstring records the 1h49m finalize wedge
that the one-stream predicate caused elsewhere in this repository. And the menu has FOUR choices, not three,
whose SECOND records `LEVEL_AFTER_CALL`, i.e. level 1: evaluated directly, choice 1 records nothing and the
run resumes, choice 2 is level 1, choices 3 and 4 are level 4. So "on a TTY the first Ctrl-C is level 4, not
level 1" is false, and an E-01 written to avoid claiming a gentle first press would have avoided claiming
something TRUE. The plan's cited test also pins the wrong thing: `tests/test_interrupt_menu.py:332-355`
asserts `main`'s messages; the level mapping is asserted at `:380-400`.

THREE MECHANICAL BLOCKERS WOULD EACH HAVE SURFACED MID-EXECUTION. First, four shipped assertions constrain
the footer wording: three `assertNotIn` calls in `ContinuationHintTests` and one in an end-to-end
successful-run test forbid the substrings `resume` and `aw runs` on specific branches, so a stop line
containing either breaks a test the fence forbids weakening. OQ-01 chose a branch without noticing this.
Second, the `resume` subparser lacks `RawDescriptionHelpFormatter` on both hosts while `start` has it, so
argparse reflows a multi-line description onto one line and inlines the indented command; I proved this with
a minimal reproduction. E-04's "verify by running --help" would have caught the symptom but the plan gave no
remedy, and the remedy is a real (if behavior-neutral) code edit the fence should authorize. Third, the two
footers are ALREADY not identical, so E-02's "identical wording" had to be scoped to the stopping sentence,
and agy's footer has zero test coverage today against oc's six, making E-05's agy assertions new ground
rather than a mirror.

Also corrected: both stated baselines. The full suite is `1 failed, 5958 passed, 3 skipped, 2 xfailed`, not
`1 failed, 5648 passed`, and the test the plan blames PASSES with 112 tests; the real failure is the
reporting-contract parity test caused by another party's gitignored `opencode-recovery/` tree, which the
shared-checkout rule forbids touching. The joint stop-suite baseline is `74 passed`, not 72.

Nine findings, all FIXED in place, no deferrals. OQ-02 resolved from evidence, which added two test files to
`Scope-Paths` (where the existing harnesses and the constraining assertions live) rather than leaving a
finalize-time justification. E-items and V-items unchanged at five each, bijection intact.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | Evidence accuracy; G. executability | spec `c4gd2h:105-110` and its `:13` amendment note; `git log` on the spec file -> `bc2ed703` (2026-09-09) | **THE PLAN'S BLOCKING DISCOVERY (F-1) HAS EXPIRED: R12 WAS AMENDED TO SPECIFY BOTH PATHS.** F-1 says the interactive menu contradicts R12 and that resolving it is a pending maintainer decision, and E-01, the Deferred section and the spec-sync section are all built on that. The maintainer amended R12 one day after authoring into R12.1 (menu) and R12.2 (ladder), so the shipped behavior is the specified behavior and the constraint is gone | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-1 marked RETRACTED and superseded by new F-11; Concern paragraph rewritten to retract the claim and state what changed; E-01's truth condition replaced with the two-path one; Deferred entry struck with the reason; spec-sync rewritten; gate updated. New F-11 |
| PR-202 | HIGH | IN-SCOPE | Evidence accuracy; B. security lens | `runner_stop.py:1792-1833`, `:2007` | **THE INTERACTIVE GATE IS NOT `sys.stdin.isatty()`.** It is `interrupt_menu_is_safe`: a TTY on BOTH streams plus no `AW_NONINTERACTIVE`/`CI`, failing safe to the ladder, with `AW_FORCE_INTERACTIVE_INTERRUPT=1` unable to beat the CI signal. Its docstring records the measured 1h49m finalize wedge the one-stream predicate caused. A plan writing operator text about when the menu appears would have described the wrong condition | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 and the conventions section carry the real predicate; V-01 requires the current source pasted. New F-12 |
| PR-203 | HIGH | IN-SCOPE | Evidence accuracy | `runner_stop.py:1777-1780`, `:1864-1891`, `:2013-2022`; `tests/test_interrupt_menu.py:380-400` versus the plan's cited `:332-355` | **THE MENU HAS FOUR CHOICES AND ITS SECOND REACHES LEVEL 1, so "the first Ctrl-C is level 4" is false.** Evaluated: choice 1 records nothing and resumes; choice 2 records `LEVEL_AFTER_CALL` (1); choices 3 and 4 record `LEVEL_NOW_FORCE` (4). The plan's cited test asserts `main`'s messages, not the level mapping. E-03's reasoning about what "just happened" was built on the wrong mapping | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01, E-03 and the conventions section carry the measured mapping; E-03 now notes this handler is reached only by choices 3 and 4 or the ladder's terminal rung, so "asked to stop hard" IS accurate there. New F-13 |
| PR-204 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | `tests/test_oc_runipd.py:1944`, `:1959`, `:1963`, `:230` | **FOUR SHIPPED ASSERTIONS CONSTRAIN THE FOOTER WORDING AND THE PLAN NEVER MENTIONS THEM.** Three `assertNotIn("resume"/"aw runs", hint)` in `ContinuationHintTests` plus one `assertNotIn("resume", result.stdout)` in an end-to-end successful-run test. A stop line containing either substring on the wrong branch fails a test the fence forbids weakening, and OQ-01 picked a branch without knowing | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 carries the assertions, a verified compliant wording, and an instruction to STOP rather than edit a test; V-02 requires those tests pasted green and unmodified; gate forbids relaxing them. New F-14 |
| PR-205 | HIGH | UNDER-SCOPE | G. executability; F. UX | `oc_runipd.py:7759-7764` vs `:7905-7909`; `agy_runipd.py:4680-4685` vs `:4808-4812`; minimal argparse reproduction | **`resume` LACKS `RawDescriptionHelpFormatter` ON BOTH HOSTS, so E-04's paragraph reflows onto one line.** `start` has the formatter and `resume` does not, so argparse collapses the description and inlines the indented command. The plan would have shipped mangled help on the very surface it exists to improve | C:Low; U:Medium; S:Low; F:Medium; Overall:Low | FIXED | E-04 states the defect, offers two remedies (add the formatter, or a reflow-proof single sentence), requires the choice stated; V-04 makes the rendered `resume --help` the decisive evidence; the gate authorizes the formatter edit as the one permitted non-text change. New F-16 |
| PR-206 | MEDIUM | IN-SCOPE | C. architecture; E. testing | `render_continuation_hint is` -> False; sources differ by 449 chars; `tests/test_oc_runipd.py:1929-1992` (six tests) versus no agy coverage | **"IDENTICAL WORDING ACROSS HOSTS" IS NOT ACHIEVABLE AS STATED, because the two footers already differ** in function object, source and rendered host label/command prefix. The requirement had to be scoped to the stopping sentence modulo `{cmd}`. Also, agy's footer has no test coverage, so E-05's agy assertions are new rather than mirrored | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 scopes "identical" to the stopping sentence, warns against restructuring the footer or adding an unguarded shared symbol, and notes the agy coverage gap; V-02 and V-05 updated. New F-15 |
| PR-207 | MEDIUM | IN-SCOPE | E. testing; D. anti-regression | bare pytest -> `1 failed, 5958 passed, 3 skipped, 2 xfailed`; `tests/test_orchestrator_retirement.py` -> `112 passed`; joint stop suite -> `74 passed`; `.gitignore:49` | **BOTH STATED BASELINES ARE WRONG AND ONE BLAMES A TEST THAT PASSES.** The full suite is 310 higher than claimed, the named failure is green, and the real failure comes from another party's gitignored transcript tree. An executor holding these numbers could read drift as regression or delete files that are not theirs | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions, required-tests and V-05 carry both re-measured baselines, the real node id, its cause, and an explicit prohibition on touching that tree. New F-18 |
| PR-208 | MEDIUM | IN-SCOPE | G. executability; scope discipline | `tests/test_interrupt_menu.py:328-360`; `tests/test_oc_runipd.py:1929-1992`; the plan's three-path `Scope-Paths` | **OQ-02 LEFT TEST PLACEMENT OPEN WHILE ONE OF ITS TWO ARGUMENTS HAD EVAPORATED**, and either answer changes `Scope-Paths`. It reasoned that reusing `test_interrupt_menu.py` risks entangling new assertions with the CONTESTED interactive behavior; that behavior is no longer contested (PR-201). Meanwhile both harnesses E-05 needs already exist in files the plan does not declare | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 RESOLVED: interrupt-message assertions beside the existing ones in `test_interrupt_menu.py`, footer assertions beside `ContinuationHintTests`, help assertions in the declared `test_runner_stop_triggers.py`. Both files ADDED to `- Scope-Paths:`; scope check and gate updated (add only, never modify) |
| PR-209 | LOW | IN-SCOPE | Evidence accuracy | backlog `4awwg4` front matter (`open`, `Priority: low`) and its Summary | **THE SEPARATELY-FILED ITEM IS NOW STALE FOR ITS PRIMARY CLAIM**, still asserting that the TTY path "contradict[s] spec c4gd2h R12" after the amendment settled it. The plan presents itself as coexisting with a live conflict tracked there | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Concern and Deferred record that `4awwg4` is stale and should be re-read against the amended R12, and state plainly that this plan no longer depends on its outcome. New F-17 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-1's premise is dead. Retract the finding, or delete it? | Mark it RETRACTED in place, superseded by F-11..F-13, keeping the original text struck through | Deleting the row; leaving it and only adding a correction elsewhere | A plan's findings table is a record of what was believed and when, and this plan's own history explains its shape by reference to F-1. Deleting it would make the Concern's retraction paragraph unintelligible; leaving it uncorrected would let an executor act on a resolved conflict. Retraction preserves both the audit trail and the correction | yes |
| D-2 | Does the expired premise warrant `REJECT - NEEDS REPLAN`? | No: APPROVE WITH REVISIONS APPLIED | REPLAN on the ground that E-01's whole basis changed | The three surviving surfaces (F-4, F-5, F-6) are independently re-verified and unaffected by the spec amendment; E-02 through E-05 needed sharpening, not redesign; and the amendment makes the plan's job EASIER (more may be truthfully said), not impossible. That is bounded revision | yes |
| D-3 | OQ-02 placement: resolve it, or leave it to the executor as authored? | Resolve it, and add the two test files to `Scope-Paths` | Leaving it open; resolving it toward a single new file | One of the question's two arguments had expired (PR-201), and the remaining evidence is decisive: both harnesses E-05 needs already exist, and the four constraining assertions live in one of the undeclared files. Leaving it open would also leave `Scope-Paths` knowingly incomplete, which the finalize gate reconciles against reality. A single new file is still permitted, stated as such | yes |
| D-4 | E-04's reflow problem: mandate adding `RawDescriptionHelpFormatter`, or allow a single-sentence pointer? | Allow either, require the choice stated and the rendered output pasted | Mandating the formatter edit; mandating a single sentence | Both remedies are correct and the trade-off is real: the formatter gives consistent multi-line help on both hosts but is a code edit in a text-only plan, while a single sentence is purely textual but weaker. The fence now authorizes the formatter explicitly so the executor is not forced to choose between a mangled paragraph and an unauthorized edit | yes |
| D-5 | Should the reviewer fix the environmental suite failure (another party's gitignored `opencode-recovery/` tree)? | No: record it, name the cause and the tracking item, forbid touching it | Deleting the tree; adjusting the parity test | It is another party's gitignored session transcripts in a shared checkout, which the shared-checkout rule forbids cleaning up; it is already tracked as backlog `8kttqq` (`open`); and it is outside both this plan's `Scope-Paths` and a review's authority, since reviews change plans and not code | yes |
