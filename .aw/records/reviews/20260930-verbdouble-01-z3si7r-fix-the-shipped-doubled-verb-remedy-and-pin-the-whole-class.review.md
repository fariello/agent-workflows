# Review findings: plan z3si7r

- Subject-Id: z3si7r
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (MEDIUM, fixed), PR-906 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan file was committed and byte-identical to the lane input
(`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; `--phase review-finalize` reports `conforming` after revision. This plan's own first `- Kind:`
bullet reads `child`, so the `IPD-S407` orchestrator child-row check does not apply.

I RE-DERIVED THE DEFECT AND THE AUDIT INDEPENDENTLY rather than reading the plan's findings, and the
plan's factual core is sound throughout:

- F-01: rendering `finalize_retry_remedy` gives `aw oc run run resume <run-id>` and
  `aw agy run run resume <run-id>`, both containing `run run`. The source writes
  `f"...resume the run with \`{command} run resume <run-id>\`"`.
- F-03: the `None` fallback renders `aw oc run resume <run-id>`, correct, because its literal is
  `"aw oc"`. Both shipped hosts are broken and the fallback is not, exactly as claimed.
- The measured failure: `aw oc run run resume fake-run-id` exits 2 with
  `runipd: Ambiguous Set selector prefix: run matches [33 sets]`, so the operator is sent to a dead end.
  Verbatim confirmation of OQ-02's perceptibility argument.
- Both parsers yield `['audit', 'integrate', 'report', 'resume', 'start', 'status', 'stop']` with `run`
  absent, so E-04's parser-derived approach is available as described.
- F-04 re-verified INDEPENDENTLY: I rendered all seven host-command-carrying remedies for both hosts
  and the fallback (21 renders). Exactly one produced a doubled verb, `finalize_retry_remedy`'s
  exhausted form, on both hosts. Every sibling renders a bare id6, a real subcommand, or no suffix.
- OQ-01's citations hold: the item's reclassification clause is verbatim, `f33nrj` is the single
  `planned` release, `aw check release-gates` reports `✓ CONFORMS 518 ... errors 0 warnings 0`, and
  `check_engine.check_release_gate_consistency`'s docstring does say the gated-carrier-under-ungated-item
  asymmetry is deliberate and unreachable by construction. Baseline `119 passed in 9.94s` is exact.

TWO HIGH FINDINGS ARE BOTH ABOUT THE GUARD, WHICH IS WHERE THIS PLAN'S VALUE LIVES. The one-line fix is
trivially correct; the plan says so itself ("the plan's value is mostly in F-05's guard, which is why the
guard is not optional"). So a guard that does not bite is the failure mode that matters, and as specified
it did not bite.

PR-901 IS THE ONE THAT WOULD HAVE MADE THE GUARD VACUOUS. E-04 allowed the token after the host command
to be "a selector-shaped token". The defect's own token IS `run`: a bare alphanumeric word, which is
selector-shaped by any loose reading. I classified the actual defect string against E-04's five permitted
classes and confirmed that four of them reject `run` while the selector-shaped escape ACCEPTS it. So an
executor implementing the escape as written would ship a guard that passes on the exact string the plan
exists to remove, and the only thing standing between that and a vacuous pass was the separate
`assertNotIn("run run")`. The fix closes the escape to four classes and converts the legitimate id6 case
(which `turn_retry_remedy` really does render) into an allow-list of the VALUE the test itself supplies,
so the escape is something the test controls rather than a pattern a defect can satisfy.

PR-902 IS THAT THE `run run` BACKSTOP DOES NOT PIN THE CLASS THE ITEM ASKED FOR. The backlog item asks
for a guard refusing "a doubled verb (`run run`, `resume resume`)". Measured: the substring catches
`aw oc run run resume <run-id>` and `aw agy run run abc123` but MISSES `aw oc run resume resume <run-id>`
and `aw oc run start start`. The item's SECOND named example escapes the assertion the plan proposed as
its class guard. Fixed by requiring a generalized adjacent-duplicate-token assertion, keeping `run run`
as the direct F-01 regression pin, and adding three class-level negative controls to V-04 so the executor
must demonstrate the class is covered rather than assert it.

PR-903 IS A FACTUAL OVERSTATEMENT THAT MISDIRECTS THE WORK. Step 0 and F-05 said the guard "once existed
and was deleted ... That is why the class is currently unguarded even though a test for it was written."
I read the pre-deletion file (`git show 19313eed^:tests/test_retry_consumption.py`): the removed test
called ONLY `turn_retry_remedy`, and `finalize_retry_remedy` appears ZERO times in all 729 deleted lines.
So restoring it verbatim would have left F-01 shipping untouched. The correction matters because it
changes what E-04 must be: not a restoration but a strictly WIDER guard whose value is its coverage. The
history is also more damning than the plan's version, and worth recording accurately: a test for this
exact class existed WHILE the defect shipped in a sibling function, so single-function coverage is
demonstrably insufficient rather than merely thin.

PR-904: E-01 and E-02 are separable as written but must not be separated. E-02 alone changes the fallback
literal from `"aw oc"` to `"aw oc run"` while the interpolation still writes `{command} run resume`,
which would render `aw oc run run resume <run-id>` and thereby EXTEND the defect to the one path that is
correct today (F-03). The plan's dependency edge (E-02 depends on E-01) implies the ordering but nothing
stated the hazard, and E-02's own Expected outcome asserts the rendered string is unchanged, which is
true only if E-01 landed first.

PR-905: E-05 said a missed site "is recorded and filed rather than silently fixed", which leaves the
obligation in this plan's own prose. Once the plan reaches `executed` it classes `done` in `aw attention`,
so an obligation living only here vanishes. This is the repository's own carrier rule and the plan
otherwise observes it carefully. Fixed with a defined failure route: in-fence sites are fixed here,
out-of-fence sites get an `aw backlog new` inheriting this plan's release gate, with the new id6 cited in
V-05, and the conditional obligation is named in the deferral section.

PR-906: the gate lacked a scope fence, and its finalize instruction was unconditional
(`finalize through the tooled path (aw ipd finalize z3si7r)`) where ownership is conditional on whether a
runner drives the execution.

WHAT I DID NOT WEAKEN. The plan's insistence on RENDERED evidence over state dicts is correct and is the
lesson that found this defect in the first place; its negative-control requirement is the right instinct
and I extended rather than relaxed it; the field-rename deferral is well-reasoned with a real blast-radius
argument; and OQ-01's release-gate reasoning is careful, correctly verified against the shipped checker
rather than assumed, and honest about the item reclassification being optional rather than forced.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | E. Testing / D. Anti-regression (an escape clause that admits the defect) | E-04 permitted the next token to be "a selector-shaped token". Measured at review: the defect token is `run`; classified against E-04's classes, `absent`/`flag`/`placeholder`/`subcommand` all reject it while a bare-alnum selector test accepts it. `turn_retry_remedy` legitimately renders `{command} {id6}`, so the case is real | **E-04's guard, as specified, would PASS on the exact string this plan exists to remove.** A selector-shaped escape cannot distinguish a bare id6 from a bare verb, because both are alphanumeric words, so the class guard would be vacuous for its own motivating instance and only the separate `run run` substring would catch it | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04's escapes closed to exactly four classes with NO general selector escape; the legitimate id6 case becomes an allow-list of the VALUE the test passes, required to be distinctive and not a subcommand prefix; F-07 records the measurement; V-04 gains a negative control for `{command} run <id6>` proving the allowance did not reopen the hole |
| PR-902 | HIGH | IN-SCOPE | D. Anti-regression (the class guard does not cover the class) | Backlog `6if6ko` asks for a guard refusing "a doubled verb (`run run`, `resume resume`)". Measured at review: `assertNotIn("run run")` catches `aw oc run run resume <run-id>` and `aw agy run run abc123`, MISSES `aw oc run resume resume <run-id>` and `aw oc run start start` | **The only class-level assertion E-04 proposed misses the item's own second named example.** The plan's stated purpose is to "pin the whole class"; a substring test for one literal pins one instance, so the plan would deliver its regression pin and not its class guard | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now requires a generalized assertion that no adjacent token pair is identical, keeping `run run` as the direct F-01 pin; V-04 requires three class-level negative controls (`resume resume`, `start start`, `run <id6>`) with the rule that any passing case fails the item; F-08 records the four classified cases |
| PR-903 | MEDIUM | IN-SCOPE | A. Correctness (a factual overstatement that misdirects the deliverable) | `git show 19313eed^:tests/test_retry_consumption.py`: the deleted test calls only `turn_retry_remedy(labels, "xipfy1", retry=False)`; `grep -c finalize_retry_remedy` on that file returns 0 across all 729 deleted lines | **Step 0 and F-05 said the guard for this class "once existed and was deleted", which is not true of this defect: the deleted test would not have caught it.** That framing invites an executor to restore the old test and believe the class is closed, leaving F-01's sibling-function gap exactly as it was. The true history is stronger evidence for the plan: a test for this class existed WHILE the defect shipped elsewhere | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Step 0 bullet rewritten with the measured zero-occurrence result and the conclusion that E-04 is strictly WIDER than a restoration; new F-06 records it; the Scope, Goal and Proposed-changes wording changed from "restore" to "add" with the reason cited, so no section still describes the work as a restoration |
| PR-904 | MEDIUM | IN-SCOPE | A. Correctness (a partial application extends the defect) | E-02 changes the fallback literal to `"aw oc run"` while E-01 removes the stray `run` from the interpolation. Applying E-02 alone leaves `{command} run resume` with a verb-carrying fallback, rendering `aw oc run run resume <run-id>` | **E-02 performed without E-01 would extend the defect to the only path that renders correctly today.** The dependency edge implied ordering but no text stated the hazard, and E-02's own Expected outcome ("the rendered string is unchanged") holds only if E-01 landed first, so a partial application would silently contradict its own success criterion | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 now states the two edits are one atomic change and that no committed tree may carry E-02 without E-01, with the rendered consequence spelled out; V-02 requires the executor to state explicitly that both landed in the same edit |
| PR-905 | MEDIUM | UNDER-SCOPE | G. Plan executability (an obligation with no durable carrier) | E-05's Expected outcome said a missed site "is recorded and filed rather than silently fixed", naming no carrier mechanism. `.aw/records/plans/README.md`'s carrier gate exists because a plan reaching `executed` classes `done` in `aw attention` | **A site the execution-time audit might find had no durable carrier, so the obligation would vanish when this plan went terminal.** The audit is the only thing standing behind the two-path scope claim, which makes its failure route load-bearing rather than hypothetical | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now defines the route: in-fence sites fixed here; out-of-fence sites get `aw backlog new` inheriting `- Blocks-Release: f33nrj` with the id6 cited in V-05, explicitly not widening the plan. Deferral section gains the conditional carrier row and two `Carrier-Declined` rows for the measured-correct exclusions; Scope check declares the foreseeable out-of-fence write |
| PR-906 | LOW | UNDER-SCOPE | G. Plan executability (missing execution-contract elements) | The gate carried the path-scoped commit rule, never-push, the staged-set check and the paste-output rule, but no scope fence; and its lifecycle sentence read `finalize through the tooled path (aw ipd finalize z3si7r)` unconditionally | **No fence declared what this plan must not touch, and the finalize instruction was unconditional where ownership depends on whether a runner drives the execution.** A worker-role process in a managed lane is refused by `aw ipd begin`/`finalize`, so an unconditional instruction sends the executor into a refusal | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gains a declaration-style fence with four named negative constraints (no field rename, no `render_stream`/`runner_stop` edits, no change to the two correct siblings, no weakening of the 119 existing tests) plus make-then-justify routing, and the conditional transition-ownership paragraph |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-901: the selector-shaped escape admits the defect, but `turn_retry_remedy` genuinely renders a bare id6. Drop the escape, keep it with a tighter shape, or bind it to a value? | BIND it to the exact id6 value the test supplies, and require that value be distinctive | (a) Drop the escape entirely and let `{command} {id6}` fail the guard, forcing E-01's scope to widen into rewording two correct functions; (b) keep a shape test but tighten it (for example require a digit, or reject any token in a stoplist of verbs) | Option (a) would make the guard demand a change to two functions the plan correctly identifies as already correct, converting a one-line fix into a wording change across three renderers and moving the target E-01 matches. Option (b) is the trap restated: every shape test for "looks like an id6" is a test a bare verb can satisfy, since id6s are alphanumeric words, and a stoplist of verbs is the hand-maintained list the plan rightly rejects in favour of live parser choices. Binding to the supplied VALUE is the only option where the escape cannot be satisfied by anything the test did not itself put there, which is what makes the guard non-vacuous by construction rather than by vigilance | yes |
| D-2 | PR-902: should the class assertion replace `assertNotIn("run run")` or be added beside it? | ADD the generalized adjacent-duplicate check and KEEP the substring | (a) Replace the substring with the general check, since the general check subsumes it; (b) keep only the substring, treating the broader class as out of scope for a bug-fix plan | Option (a) is defensible and I rejected it narrowly: the substring is the DIRECT regression pin for F-01, so a future reader diffing the test can see the specific shipped defect it refuses, and a general check that someone later loosens would take the specific pin with it. Two assertions with different purposes cost one line. Option (b) contradicts the plan's own title and the item's own request, which names `resume resume` explicitly as part of the class; a plan promising to "pin the whole class" and shipping a one-literal substring would be the overclaim this repository keeps having to correct | yes |
| D-3 | PR-903: the deleted test would not have caught this bug. Correct the history, or leave it as motivation? | CORRECT it, and change every "restore" to "add" | (a) Leave the Step 0 bullet, since the deleted test IS real history and the framing is motivational; (b) correct F-05 only, leaving the Scope and Goal wording | Option (a) leaves a statement that an executor would reasonably act on by restoring the old test and concluding the class is closed, which is precisely the gap that let this defect ship. Option (b) is the incoherent middle: a plan whose Findings say the deleted guard was insufficient while its Scope and Goal promise to "restore" one leaves the executor choosing which section to believe. I verified the zero-occurrence result directly (`grep -c` on the pre-deletion file) rather than inferring it from the test body, because the whole point of the finding is that the coverage claim was unchecked | yes |
| D-4 | PR-905: should `.aw/records/backlog/` be added to `Scope-Paths` so E-05's conditional filing is in-fence? | NO: leave it undeclared and route it through `--scope-reason` | (a) Declare `.aw/records/backlog/` in `Scope-Paths`; (b) drop the filing requirement and have E-05 only record findings in V-05 | Option (a) declares a path the plan expects NOT to write, and `aw ipd finalize` then demands a `--scope-ack` for a declared-but-unmodified path on every execution where the audit is negative, which is the expected case (negative at authoring and again at review). That converts the normal path into a friction step. Option (b) is the finding. The repository's prescribed route for a foreseeable but conditional out-of-fence write is to MAKE it and justify it with `--scope-reason`, which is exactly what the sibling plan `e6f0jx` does for the same shape, so this follows an established pattern rather than inventing one | yes |
