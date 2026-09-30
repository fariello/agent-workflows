# Review findings: plan 9oj6t2

- Subject-Id: 9oj6t2
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-B01 (HIGH, fixed), PR-B02 (MEDIUM, fixed), PR-B03 (MEDIUM, fixed), PR-B04 (LOW, fixed), PR-B05 (LOW, fixed), PR-B06 (LOW, fixed)

## Round 1

Reviewed at HEAD `4e8643ab` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

THIS PLAN'S MEASUREMENTS ARE UNUSUALLY GOOD AND I VERIFIED THEM RATHER THAN TRUSTING THEM. The scanner
census reproduces BYTE-FOR-BYTE on a later HEAD: `sanctioned thin wrappers : 46 (NOT forks)`,
`REAL FORKS : 10`, `byte-identical 4`, `divergent 6`, with the same four names and both targets at
similarity `1.000` (F-1, F-2). The closure output matches F-3, including the `ABSENT-FROM-SHARED` entry for
`runner_shared` itself. Both bodies really are byte-identical between hosts (read both). F-4's retirement is
real, and `nmlx47`'s own RETIRED header says what the plan quotes. F-6 is exactly right in both halves:
`tests/test_rununify_main.py` does not exist, `oc.run_suite_check is agy.run_suite_check is
rs.run_suite_check` is True, and `oc.integrate_lane_branch is agy.integrate_lane_branch` is False. F-7's
unasserted exit contract reproduces on both hosts (`rc=1`, `stdout=''`, the same
`integrate zzzzzz REFUSED (no-lane-record): ...` on stderr). F-8's degradation is real: I deleted
`oc_runipd.handle_integrate_command` and watched the hint fall back to the by-hand sentence, then restored
it. F-10 and F-11 are correct, including the honest admission that the scanner's `StallWatchdog` count is a
predicate limitation rather than duplication. OQ-01's parameters-not-descriptor resolution is correct and
well-evidenced: I read both shared signatures and `HostLabels` does carry strings while what varies here is
a callable.

THE ONE SERIOUS GAP IS THAT THE PLAN ASSERTS ITS OWN SUCCESS IN PROSE AND NOTHING MEASURES IT. The Scope
check says the plan leaves "8 real forks by the scanner's count", which is the entire point of the work. But
both target bodies are MULTI-STATEMENT today, and that is not incidental: I drove
`tools.runner_fork_scan.is_pure_delegation` over both host `FunctionDef` nodes and got
`_integrate_stranded_lanes stmts=3 False` and `handle_integrate_command stmts=6 False`, against
`save_state stmts=1 True` in the same file as the sanctioned shape. The predicate requires ONE non-docstring
statement. So a wrapper that kept `repo = Path(state["repo"])` or `pal = Palette(should_color(sys.stdout))`
would satisfy every V-item as originally written, pass the whole suite, produce a diff that looks like a
lift, and leave `REAL FORKS` at 10 with both symbols still forked. The plan mentions `is_pure_delegation`
three times, including in the Scope check's own outcome claim, and never made it an obligation.

I CHECKED THAT THE CRITERION IS ACHIEVABLE BEFORE REQUIRING IT, because a requirement that cannot be met is
worse than none. It is. Every statement executed before the delegation is host-NEUTRAL: `repo` reads only
`state`, `repo`/`id6` in the other body are `getattr` reads of `args`, and `Palette`, `should_color` and
`append_jsonl` are `is`-identical in all three modules (measured). So each shared shell can build what it
needs and each wrapper reduces to one `return runner_shared.<shell>(...)` passing only the per-host
callables, which the predicate accepts (it constrains statement COUNT, not argument arity). That measurement
also sharpened what must be threaded: of the five bindings E-02 lists, `run_suite_check` and `append_jsonl`
are the SAME OBJECT everywhere and need not be passed at all, while `save_state` and `process_backlog_close`
must be, because although their SOURCE is byte-identical between hosts each binds its own host's
`write_report` / `run_checked` / `close_backlog_item` / `commit_backlog_close` internally. Only
`integrate_lane_branch` differs in its own source. That is now F-16.

THREE FURTHER CORRECTIONS, none touching the design. The plan twice cites
`tests/test_runner_shared.py::NoRunnerImportTests` as a shipped AST guard forbidding `runner_shared` from
importing a driver, and quotes the two production docstrings that say the same. That test DOES NOT EXIST; it
went in `19313eed` and only prose comments survive ("this module may not import a runner"). The INVARIANT is
real and worth stating in the lifted docstring, but citing an unrunnable test would send an executor looking
for a guard that is gone, and E-03 would have propagated the dead citation into new shared code. Separately,
OQ-02 rejects a census-style anti-re-fork guard by citing P16, and the citation is correct as far as it
goes, but the tree ALREADY SHIPS a per-symbol AST re-fork guard that passes today:
`test_add_output_mode_flags_not_reforked_in_hosts` parses both host modules and asserts each host's
`_add_output_mode_flags` is exactly one statement delegating to `runner_shared`. That is not the many-symbol
census table P16 most clearly forbids, and it sits in real tension with P16's "No architectural placement
pins". The answer stays NO for this plan, on the narrower and more honest basis that adding a third
production-shape assertion is a maintainer's call about P16's boundary rather than something a decision-free
lift settles. Finally the baselines drift, as in every plan in this sweep: bare `python3 -m pytest` measured
`3312 passed, 2 skipped` at review, and while the narrow three-file gate's `357 passed` held exactly, its
`24.05s` timing did not (`134.62s`).

WHAT I CHECKED AND FOUND SOUND BESIDES. Every test and fixture the plan names resolves: all five exported
fixtures exist in `tests/test_runner_shared.py`, and `HostIntegrateVerbTests`,
`HostResumeIntegratesInsteadOfDispatchingTests`, `AgyResumeIntegratesInsteadOfDispatchingTests`,
`test_this_hosts_merge_subject_says_aw_oc_run` and `LaneRemedyHintTests` are all present. The two
both-spellings tests exist but under DIFFERENT names per host, which V-03 listed as though each were on both
hosts; corrected. E-04's P16 discipline is right and the plan is right that the invariant must be asserted
behaviorally rather than as a placement pin. Both Deferred exclusions are genuine recorded decisions and
their Carrier-Declined reasoning is sound, including the unusually honest divergent-forks row that declines
to claim an in-tree citation it does not have. The plan correctly carries no `- Blocks-Release:`: its
`- Work-Kind:` is `chore`, which is not in the repository's gating set. Backlog item `baskrx` is already
`graduated` with `- Graduated-To: baskrx`, so no transition is owed, which the gate now states.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-B01 | HIGH | UNDER-SCOPE | E. Testing / G. Plan executability (the plan's own success criterion unmeasured) | Drove `tools.runner_fork_scan.is_pure_delegation` over both host `FunctionDef` nodes: `_integrate_stranded_lanes stmts=3 False`, `handle_integrate_command stmts=6 False`, against `save_state stmts=1 True` / `process_backlog_close stmts=1 True` in the same file. The predicate's body requires `len(body) == 1` after stripping the docstring. The plan's Scope check asserts the outcome "leaving 8 real forks by the scanner's count"; no `E-*` or `V-*` mentions it | **The lift has a measurable success criterion and nothing required it.** Both bodies are multi-statement, which is exactly why the scanner counts them as REAL FORKS despite classing them `BOTH-DELEGATE`. A wrapper retaining one setup line (`repo = Path(state["repo"])` or `pal = Palette(...)`) satisfies every original V-item, passes the full suite, produces a diff that reads like a lift, and leaves `REAL FORKS` at 10 with both symbols still forked. The plan's whole purpose would be unmet with complete green evidence | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Verified the reduction is REACHABLE before requiring it: every pre-delegation statement is host-neutral and `Palette`/`should_color`/`append_jsonl` are `is`-identical across all three modules (new F-13). New F-12 records the predicate baseline and the failure mode. E-01 now captures the pre-lift `is_pure_delegation` verdict and statement count as the before-value. E-02 and E-03 each require the wrapper to reduce to EXACTLY ONE non-docstring statement, naming which statements must move into the shared body. E-06 requires the scanner re-run to show `REAL FORKS 8` and `byte-identical 2` with neither lifted symbol listed. V-02, V-03 and V-06 demand that evidence, V-02 stating that a diff which merely looks smaller does not satisfy it. A first silent-failure mode added to the gate |
| PR-B02 | MEDIUM | IN-SCOPE | Evidence accuracy (a cited guard that does not exist) | `grep -rn "NoRunnerImportTests" tests/` returns nothing. The name survives only inside `oc_runipd.handle_integrate_command`'s docstring as `tests/test_runner_shared.py::NoRunnerImportTests`. The two live references to the rule in `tests/test_runner_shared.py` are prose comments, not assertions | **The plan and both production docstrings it quotes cite a shipped AST test that was deleted in `19313eed`.** The INVARIANT (`runner_shared` may not import a driver) is real and worth stating, but E-03 would have carried the dead citation into a NEW shared docstring, sending a future executor to a guard they cannot run and potentially concluding the lift broke something | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14 records the absence and distinguishes the still-true invariant from the missing test. E-03 now explicitly forbids repeating the citation in any docstring it writes, while directing that the rule itself be stated, and its Expected outcome requires confirming no new docstring cites it. V-03 requires the same confirmation |
| PR-B03 | MEDIUM | IN-SCOPE | F. Principles (a one-sided P16 citation) | `tests/test_runner_shared.py::test_add_output_mode_flags_not_reforked_in_hosts` parses BOTH host modules and asserts each host's `_add_output_mode_flags` is one non-docstring statement calling `runner_shared.add_output_mode_flags`, plus that neither calls `add_argument`; `python3 -m pytest -k add_output_mode_flags_not_reforked` -> `1 passed`. GUIDING_PRINCIPLES P16: "No architectural placement pins: Do not assert which module holds a `def` by inspecting ASTs or module dictionaries" | **OQ-02 rejects an anti-re-fork guard as P16-forbidden without acknowledging that the tree ships one and it passes.** The rejection of a many-symbol CENSUS TABLE is correct; but a single-symbol shape assertion is a different form, it exists here, and it is in genuine tension with P16. As written the resolution implies no such precedent exists, which is the kind of one-sided citation `/plan-review`'s own costlier-error rule warns about | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 records the shipped test, its passing status, and the P16 tension explicitly. OQ-02's answer STAYS NO but is re-based on a narrower and honest ground: adding a third production-shape assertion inside a plan whose premise is that it changes no behavior is a maintainer's call about P16's boundary, not something a decision-free lift may settle. The counterexample is now visible to the reviewer rather than absent |
| PR-B04 | LOW | IN-SCOPE | G. Plan executability (stale live-artifact baselines) | Re-measured at review: bare `python3 -m pytest` -> `3312 passed, 2 skipped, 3 warnings in 109.70s`; `tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` -> `357 passed in 134.62s` against the plan's `357 passed in 24.05s` | **The narrow gate's timing is stale and the bare suite has no authoring figure to compare against, while E-06 and V-06 ask for a before/after comparison.** The COUNT held at 357, which is worth recording; the timing moved by 5x. An executor comparing wall time, or comparing a bare total to a number written later, reads noise as signal | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Required-tests baseline now states that the count is the bar and the timing is noise, with both measurements recorded. E-06 and the bare-suite bullet require a FRESH baseline captured at execution HEAD with a node-id comparison, and explicitly forbid comparing against any count written in the plan. V-06 restated to match. A second silent-failure mode added to the gate |
| PR-B05 | LOW | IN-SCOPE | Evidence accuracy (two miscounts and a per-host naming error) | `git show --name-status --diff-filter=D 19313eed -- tests/` lists ELEVEN deleted `test_rununify_*` files, not four. `test_both_spellings_reach_the_same_implementation` appears only in `tests/test_oc_runipd.py`; `test_both_spellings_reach_the_shared_implementation_once` only in `tests/test_agy_runipd_cli.py` | **F-5 undercounts the deleted pin files, and V-03 names the two both-spellings tests as if each existed on both hosts.** Neither changes a decision, but V-03's wording would send an executor looking for a test that is not in the file they are told to check | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-5 corrected to eleven with the commit subject quoted. V-03 now states which name belongs to which host file and instructs naming each against its own file |
| PR-B06 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Gate as authored: no approval summary, no scope-fence disposition, no finalize ownership conditional, no silent-failure modes, and no statement of the backlog item's state or the absent release gate | **The gate lacks required execution-contract elements** and says nothing about `baskrx`'s state or why no `- Blocks-Release:` is carried, leaving a reviewer to derive both | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with a "what a human is approving" paragraph naming every review correction and every verified measurement, a make-and-then-JUSTIFY scope disposition with no stop directive for the scope case, TWO sanctioned stops (E-01's refusal condition, and an unreachable single-statement reduction, which would mean a host-varying value survives and the lift is no longer decision-free), four measured silent-failure modes, a post-gate `AW-LIFECYCLE-ROLE-001` paragraph forbidding a hand-rolled `git mv`, and a closing paragraph recording that `baskrx` is already `graduated` and that `chore` is outside the release-gating set so no gate should be added |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-B01: make the single-statement wrapper a hard requirement, or leave it as the plan's prose aspiration? | HARD REQUIREMENT, in E-02/E-03, with a before-value in E-01 and a census check in E-06 | (a) Leave it in prose and trust the executor; (b) require it only for `handle_integrate_command`, whose reduction is more obviously trivial; (c) drop the plan's "leaving 8 real forks" claim instead, so nothing is asserted that is not measured | Option (a) is what the plan did, and it is the specific hole: a 3-statement wrapper passes every test and leaves the census unchanged, so the work could be reported done having not been done. Option (b) is arbitrary once the reduction is verified reachable for both. Option (c) was genuinely tempting (removing an unmeasured claim is honest) and rejected because the claim is TRUE and achievable, so deleting it would discard the plan's actual deliverable rather than securing it. Verified reachable first: all pre-delegation statements are host-neutral and the three helper objects are `is`-identical across modules | yes |
| D-2 | PR-B01/F-16: should the shared shell take `suite_check` and `append_jsonl` as parameters, as the plan's E-02 lists? | NO for those two (they are the same object everywhere); YES for `integrate`, `save_state`, `process_backlog_close` | (a) Thread all five, as E-02 listed; (b) thread none and import them in the shared module | Measured: `oc.run_suite_check is agy.run_suite_check is rs.run_suite_check` and the same for `append_jsonl`, so passing them is a parameter nobody needs, which `li44r9`'s own rule (quoted in OQ-01) forbids. But `save_state` and `process_backlog_close` MUST be threaded even though their source text is byte-identical between hosts, because each binds its own host's `write_report`/`run_checked`/`close_backlog_item`/`commit_backlog_close` internally, which an identical-source check would miss. Option (b) is impossible for those two and for `integrate_lane_branch`, since `runner_shared` may not import a driver | yes |
| D-3 | PR-B03: OQ-02 rejects an AST re-fork guard citing P16, but the tree ships one. Change the answer, or the basis? | KEEP THE ANSWER, re-base the reasoning, and name the counterexample | (a) Reverse OQ-02 and require a per-symbol guard modelled on the shipped one; (b) leave the one-sided P16 citation; (c) file an item asking the maintainer to reconcile P16 with the shipped test | Option (a) would add a THIRD production-shape assertion inside a plan whose premise is that it changes no behavior, and P16's text plainly forbids the form, so a lift is the wrong vehicle for that precedent argument. Option (b) leaves a citation that implies the tree agrees with it when a passing test disagrees, which is exactly the one-sided-evidence failure `/plan-review`'s costlier-error rule addresses. Option (c) was considered and declined here rather than smuggled: it is a real question about a principle's boundary, but filing it would assert the repository intends to change P16, which no evidence supports and which is a maintainer's call; the honest act is to make the tension visible in the plan the maintainer is reading | yes |
| D-4 | PR-B02: the cited `NoRunnerImportTests` is gone. Should this plan restore it? | NO; forbid propagating the citation and state the invariant as a rule instead | (a) Restore the deleted test as part of this plan; (b) keep the citation, since the invariant is still true | Option (a) is out of this plan's declared scope and is itself an architectural-placement assertion, so it collides with PR-B03's reasoning and with P16 for the same reason. Option (b) is the status quo defect: a docstring pointing at a test that cannot be run teaches a future reader that the guard exists, which is worse than stating the rule plainly. The invariant remains enforced by the fact that `runner_shared` genuinely does not import either driver, which the closure output in E-01 re-establishes every run | yes |
| D-5 | Is the plan's Deferred divergent-forks row acceptable when it declines to cite in-tree evidence? | YES, unchanged; it is the most honest row in the plan | (a) Demand an in-tree citation for the large-function split's status; (b) require an item be filed for the five large functions | The row explicitly says no honest in-tree citation exists for the residue and explains why (`rununify` 07-11 each recorded `NO SPLIT WAS PERFORMED`, `a5wdne` says the next step is a maintainer DECISION about those five plans), then states plainly that there is no LIVE carrier today. Option (b) is what the row itself refuses on the ground that it would duplicate an authorization that already exists and has stalled on its merits five times, which is correct: filing a sixth would assert a decision the maintainer has not made | yes |
