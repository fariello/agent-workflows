# Review findings: plan b02ohu

- Subject-Id: b02ohu
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `7547091e` in a lane worktree. Structural preflight `aw ipd lint --phase author` reported
`conforming` with TWO `IPD-Z602` density advisories (E-04, E-06); after revision `--phase review-finalize`
reports `conforming` with ONE (E-06), and both were examined on merits rather than deferred to, since the
linter's own contract is that a passing count check does not clear conceptual density. No pre-review
snapshot was owed: the plan was committed and unmodified, and the lane-input copy under
`.aw/state/lane-inputs/rev-19/` is byte-identical. Bare suite at review HEAD: `3246 passed, 2 skipped, 3
warnings in 51.21s`. NO PRODUCTION FILE OR TEST WAS MODIFIED by this review; every measurement was a read,
a scan over `tests/`, or an in-process probe that restored what it patched in a `finally`.

THIS PLAN IS EXCEPTIONALLY WELL MEASURED AND I RE-RAN EVERY LOAD-BEARING CLAIM. All of the following
reproduce at review HEAD.

The whole-suite scan returns the SAME four files and 23 hits the plan records
(`test_carrier_scan_single_item_contract.py` 7, `test_host_capability_wiring.py` 5,
`test_interactivity_resolver.py` 4, `test_runner_shared.py` 7). The per-test attribution inside
`tests/test_runner_shared.py` is unchanged in substance, with only line offsets moved, which the plan
itself predicted and which is why it cites by symbol.

E-03's mechanism WORKS FOR ALL FIVE DELEGATIONS, which is the plan's most consequential claim. Patching
`term.is_interactive` to `True` then `False`, each of `artifact_adopt.leak_gate_is_interactive(environ={})`,
`git_commit_helper._is_interactive()`, `runner_stop.interrupt_menu_is_safe()`,
`runner_shared.is_interactive_run()` and `engine.is_interactive_session(SimpleNamespace(yes=False))`
returned `True` then `False`. The `yes=True` short circuit also reproduces: `False` even under a `True`
patch. I additionally confirmed WHY the patch reaches them, which the plan does not state: all five call
through a module attribute (`from agent_workflows import term as _term` then `_term.is_interactive(...)`),
so none is bound by a from-import that a module-level patch would miss.

E-05's refutation of the obvious `vars()` fix reproduces EXACTLY: 39 common UPPER names, 38 of them the
identical object as `runner_shared`'s, and exactly ONE genuine co-definition, `DEFAULT_STALL_TIMEOUT`, equal
to `900.0` in all three modules. The identity-partition design is the right answer and the plan is right
that the naive substitution would have widened the test from 1 real subject to 39 mostly vacuous ones.

E-04's surface claim reproduces once its recipe is corrected (see PR-301): with `verbose_help` supplied the
reference yields `['--help','--quiet','--raw','--verbose','-h','-v']` with one exclusive group
`['--quiet','--raw']`, and BOTH hosts' `start` AND `resume` subparsers each yield output-mode options
`['--quiet','--raw','--verbose','-v']` with the same single group. Both hosts refuse `--raw --quiet` at exit
2 with the quoted stderr lines, `runipd start: error: argument --quiet: not allowed with argument --raw` and
the `runagy start:` equivalent.

D1, D2 and D3 all confirm. `OneSharedPredicateTests`' body is exactly `[Expr, Assign, Assign]` with zero
test methods and both tables at 1 reference. The nine `tests/test_runner_shared.py` tables measure
1,1,1,1,1,2,2,2,2 exactly as recorded, and I verified the set is genuinely CLOSED: the two remaining
references are `**`-splats into `ALL_SHARED_RUN_CHECKED_CALLERS`, itself dead, and two comment mentions.
The plan's partition is careful in a way worth noting: it deletes `LANE_INTEGRATION_WRAPPED` (1 reference,
dead) while leaving `LANE_INTEGRATION_MOVED` (3 references, live) alone.

E-01'S PREMISE IS CONFIRMED LIVE, which V-01 rightly made a stop condition:
`runner_shared.RUNNER_ACTION_TO_CONTRACT_ACTION` exists, so the `pytest.skip` guard does not fire, and the
file runs `4 passed` with the retained behavioral sibling PASSED by name rather than skipped.

I ALSO CHECKED A MECHANISM THE PLAN'S OWN SCAN DOES NOT COVER. P16 names `read_text()` alongside the
`inspect`/`ast` forms, and the plan's scan omits it. An independent AST scan for a `read_text` call whose
source segment names `agent_workflows` finds exactly TWO sites, `tests/test_leak_sanitizer.py` and
`tests/test_local_leaks.py`, both already named by this plan as sanctioned exceptions. The plan's stated
aliased-import bound also holds: no test file uses `from ast import`, `from inspect import`, `import ast as`
or `import inspect as`. So the completeness claim survives a mechanism the plan did not scan for.

THE DEFERRED WALKTHROUGH TRIPWIRE IS REAL AND IMMINENT, and the plan is right to flag it while refusing to
fix it here. `tests/test_walkthrough_id6.py` still asserts `len(all_files) == 24` and `len(exempt) == 11`,
the records tree holds exactly 24 non-README walkthroughs, and the file passes today, so it is one
walkthrough from red in the default suite. Its carrier `zf1m48` exists and reads `- Status: open`,
`- Work-Kind: bug`, `- Blocks-Release: next`. Excluding it is correct (a records census, not a code-structure
pin) and the gate is preserved rather than dropped.

THE SET'S ORDERING IS SOUND. Order 02 (`76ic0k`) declares `- Item-Dependencies: executed:b02ohu`, gives the
same red-on-arrival reasoning, allowlists exactly the one sanctioned exception this plan names, and
explicitly declines to allowlist the three `read_text` files because they call none of the flagged forms. I
found no contradiction between the two plans.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | MEDIUM | IN-SCOPE | E (testing) / G (executability) | plan E-04; `inspect.signature(runner_shared.add_output_mode_flags)` | E-04's reference-surface step, "`add_output_mode_flags` applied to a bare `ArgumentParser`", cannot be executed: `verbose_help: str` is keyword-only with NO default, so the call raises `TypeError: missing 1 required keyword-only argument: 'verbose_help'` (reproduced at review). The measured SURFACE is correct once the keyword is supplied, so the claim survives and only the recipe was wrong; left as written, an executor hits a `TypeError` on the first line of the largest rewrite | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now states the real signature, directs the executor to pass `verbose_help="<any string>"` (noting the help VALUES are owned by the retained `test_output_mode_help_text_pinned_by_value_per_host`), and carries the review's re-measurement of all four subparser surfaces agreeing with the reference. New F-R-1 |
| PR-302 | MEDIUM | IN-SCOPE | A (correctness) / D (anti-regression) | plan OQ-01; `oc_runipd._add_output_mode_flags`, `agy_runipd._add_output_mode_flags` | OQ-01 authorized E-04 to "add the `assertIs`-style identity assertion if the executor finds the shared registrar is referenced by name in both hosts". It is not, and the assertion would FAIL: each host holds a thin WRAPPER, so `host._add_output_mode_flags is runner_shared.add_output_mode_flags` is `False` on both, and neither host exposes `add_output_mode_flags` by name. The wrapper exists precisely to supply host-specific help text, making identity impossible by construction, unlike the three genuinely re-exported symbols in the `tests/test_recovone_single_definition.py` precedent OQ-01 cites. A resolved open question that authorizes a red test is worse than an open one | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | OQ-01's identity addition WITHDRAWN with the measurement and the wrapper's own docstring quoted; the resolution now explains that the surface-and-refusal agreement serves the maintenance motive instead. New F-R-2 |
| PR-303 | LOW | IN-SCOPE | G / right-sizing | `aw ipd lint --phase author` `IPD-Z602` on E-04 and E-06 | Two density advisories were unaddressed in the plan. The rubric requires these be judged semantically, and a maintainer or reviewer reading a bare advisory cannot tell whether it was examined or missed | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate now records a reasoned decision for each. E-04 is one concern (one replacement test, one property, one perturbation; splitting the option set from the refusal would duplicate over the same four subparsers, which P8 forbids). E-06 is three files but ONE act (removing data whose reader was already deleted) over ONE verification surface, and the real hazard the advisory points at (three items sharing `tests/test_runner_shared.py`) is already handled inside the item by the before-deletion re-measurement and by ordering E-06 last. E-04's advisory cleared after the PR-301 edit; E-06's remains and is now explicitly examined |
| PR-304 | LOW | IN-SCOPE | G / Step 4 | plan gate, LIFECYCLE paragraph | No conditional runner/executor ownership of `aw ipd finalize`, and no instruction about the graduating backlog item | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conditional-ownership wording added, plus the `5zyuc8` `graduated`-not-`done` obligation |
| PR-305 | LOW | IN-SCOPE | F (honest documentation) | plan Required tests baseline | The pasted authoring baseline (`3235 passed`) is already eleven tests stale, and while the plan does say to re-derive, a reader reconciling a delta against the printed figure would mis-attribute the difference | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The re-derive instruction now carries the review measurement (`3246 passed, 2 skipped` at HEAD `7547091e`) and states plainly that neither number is the bar, the reconciled delta is |

No finding was DEFERRED and none was left OPEN, so no escalation to a `- Blocking: yes` question is owed
(`check.review-finding-unescalated` satisfied vacuously). No `BLOCKER` and no `HIGH` was found: both
MEDIUMs are recipe-level defects in an otherwise correct plan, and every premise-level claim reproduced.

WHAT I DELIBERATELY DID NOT FLAG. The gate's "STOP and report" directive is CORRECT here and must not be
removed: it fires on a genuinely unsafe condition (a replacement that needs a production edit to pass has
found a real defect), which the 2026-09-01 ruling explicitly preserves as a different case from a scope
question. The plan's three `Explicitly NOT in scope` categories are each right on inspection: the LEGITIMATE
censuses assert operator-visible contracts or self-extending relations, the BEHAVIORAL rows use
`inspect.signature` on a CALLABLE rather than reading source, and the sanctioned exception is correctly
identified and correctly left for Order 02 to allowlist rather than delete. E-02's retention of the
`inspect.signature` assertions in the same test is the right call for the same reason. The two runtime-data
literals deferred to `aaoapo` are genuinely out of this carrier's scope.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | OQ-01 was already marked `resolved` but authorized an assertion that would fail. Reopen the question, or withdraw the unachievable clause? | Withdraw the clause, keep the question resolved | Reopening OQ-01 as `Blocking: yes`, rejected because the QUESTION (should a behaviorally-indistinguishable re-fork be permitted) is correctly answered YES from P16, and only the optional addition was wrong; reopening would stall a plan over a clause that simply should not exist | `GUIDING_PRINCIPLES.md` P16's prohibition on architectural placement pins; measured at review that both hosts wrap rather than re-export, with the wrapper docstring stating why | yes |
| D-2 | E-06 carries a density advisory and touches three files. Split it, or keep it whole with a recorded rationale? | Keep whole, record the rationale in the gate | Splitting into three items, rejected because the three parts are one act (deleting data whose reader is gone) over one verification surface, so splitting would triple the re-measurement and the suite run for no added signal | the rubric's own density diagnostics applied to the item: one concern, one test-surface, one focused pass; V-06 already covers all three without becoming three verifications | yes |
| D-3 | The plan's scan omits `read_text()`, which P16 names. Is the completeness claim in E-07/V-07 therefore overstated? | No; confirmed sufficient by an independent scan, recorded rather than changing E-07 | Widening E-07's scan to include `read_text`, rejected because Order 02 E-03 already records, with its own measurement (99 files), why flagging `read_text` would produce mass false positives; duplicating that judgement here would pre-empt the plan that owns it | independent AST scan at review found exactly two `read_text` sites naming `agent_workflows`, both already declared sanctioned exceptions; Order 02 E-03's recorded bound | yes |
| D-4 | Should the imminent `test_walkthrough_id6.py` tripwire be pulled into this plan, given it is one walkthrough from turning the default suite red? | No; leave it with carrier `zf1m48` | Adding it here, rejected because it is a census over the RECORDS tree rather than over code structure, so it is outside this carrier's stated scope, and the execution contract forbids opportunistic widening; its carrier already exists as a release-blocking bug so the gate is not lost | verified at review: both literals live, tree at exactly 24, file passes, `zf1m48` reads `open`/`bug`/`Blocks-Release: next` | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
