# Review findings: plan o55eli

- Subject-Id: o55eli
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1201 (HIGH, fixed), PR-1202 (HIGH, fixed), PR-1204 (HIGH, fixed), PR-1203 (MEDIUM, fixed), PR-1207 (MEDIUM, fixed), PR-1205 (LOW, fixed), PR-1206 (LOW, fixed)

## Round 1

Reviewed at HEAD `fe6611919` in an isolated review lane. The plan file was committed and byte-identical
to the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `{"outcome":"clean","exit":0,"findings":0}`
BEFORE semantic review, and `--phase review-finalize --agent` reports `clean` after revision. The plan
is `- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply.

THE PLAN'S DESIGN IS CORRECT AND ITS HARDEST MEASUREMENTS ARE EXACT. Driven at review: `run_viewer`
carries both literal tuples and both product strings exactly as F-01 states, at the only two lines in
that file holding those spellings; the descriptors carry `id`/`argv_tokens`/`product` as claimed; the
id+argv_tokens union is exactly `{agy, agy_runipd, antigravity, oc, oc_runipd, opencode}` and is
collision-free, the single missing viewer literal IS `runagy`, and `runagy` IS in `argv_subcommands`
whose two descriptors DO share `run` and `runipd`, so F-03's conclusion (named alias, never widen the key
to `argv_subcommands`) is right on every count. `_run_host` misroutes exactly as F-02 says (`octopus` ->
`oc`, `agyx` -> `agy`) and its carrier docstring nominates this item verbatim. F-04, the central scope
decision, reproduces to the record: 338 readable `state.json` files, 253 with no `driver.id`, and the
viewer's fallback labelling them `{OpenCode: 224, Antigravity: 14, runipd: 13, ipdrunner: 2}`, with
`runipd` and `ipdrunner` matching no live descriptor id, so folding that arm into the resolver would
indeed unlabel 15 historical runs. F-05, F-06, F-08's structural claims and F-09's dangling citation all
hold. The narrowed per-file counts (63 and 66) reproduce exactly, and the target file carries exactly 12
test methods as E-04 assumes. This is a sound, well-fenced chore and I found nothing to replan.

WHAT REVIEW FOUND IS THREE DEFECTS THAT WOULD EACH HAVE COST THE EXECUTOR REAL TIME, PLUS FOUR STALE OR
MIS-PROVED CLAIMS.

PR-1201 is the substantive one. E-03 re-points `_run_host` at a resolver that accepts seven spellings,
but `_run_host` today accepts only what its two `startswith` tests match. I measured the difference:
`_run_host` returns `"unknown"` TODAY for `"opencode"`, `"antigravity"` and `"runagy"`, and after this
change all three resolve to `"oc"`/`"agy"`/`"agy"`. So the function's behavior changes on FIVE ids, not
the two the plan's Expected outcome and V-03 enumerate: two NARROW (the misrouting fix the plan was
written for) and three WIDEN. The widening is a correction rather than a regression, since the viewer
already honors those spellings and the two consumers should agree, but `_run_host`'s return value is a
grouping key interpolated into operator-facing text (`"(unrecorded, {0})"`), so shipping three
unasserted changes to it means dashboard rows move for reasons no checklist item predicted. Fixed by
enumerating all five in E-03, V-03 and the spec-sync section, in both directions.

PR-1204 would have failed the executor's own mandatory evidence step on a typo. E-05 and the Required
tests section both name `tests/test_rununify_initialize_run.py` in the per-file command; that file does
not exist, no file matching `rununify` or `initialize_run` exists in `tests/`, and pytest answers a
missing path with exit 4 having run NONE of the other files. The tell is that the same draft correctly
reports `tests/test_rununify_host_descriptor.py` as missing in F-09: a `rununify` test-naming family was
assumed rather than checked. I corrected the list to the seven real files and ran it: `255 passed`. The
same finding caught F-09 undercounting its own defect, which has TWO occurrences in `runner_shared.py`,
the second naming a class inside the missing file.

PR-1202: the suite is not green, so E-05's bar of "zero failures" is unachievable. Bare
`python3 -m pytest` gives `1 failed, 3491 passed, 2 skipped`, the failure being the same date-dependent
assertion in `tests/test_backlog.py` I have now measured across four consecutive reviews (it expects a
`2026-09-30` history line against a setter writing `2026-10-01`). F-07 asserted "THE TREE IS FULLY GREEN
... this plan has no pre-existing failure to hide behind". E-05 already said to re-derive the baseline
rather than trust the authored total, which is the right instinct; what was missing was that the
re-derived baseline is RED and the bar must therefore be a failing-node-id SET comparison.

THE REMAINING ROWS ARE ACCURACY REPAIRS WHOSE CONCLUSIONS ALL SURVIVE. PR-1203: F-07's `aw check`
characterization ("58 pre-existing errors and 0 warnings ... dangling `From-Spec` advisories") is wrong
in three ways at review (68 findings, a nonzero `warning` tier, and `check.plan-spec-link-missing` at 32
as the dominant rule), while its load-bearing half holds and I re-verified it: ZERO findings name any of
the four scope paths. PR-1205: F-02's proof that `rg gxsprh` "returns that line and nothing else" is
wrong (about 16 hits across the tree, including two other pending plans), though its conclusion is
actually strengthened, since exactly one of those is a code-side obligation naming this item. PR-1206:
the import-cost ratio is real but about half the claimed size (0.070s versus 0.170s at review, a factor
of 2.4, against the authored 0.076s versus 0.347s and "roughly five"); the lazy-import DECISION is
unaffected, and I independently confirmed the no-cycle claim by AST scan (zero module-level `run_viewer`
imports in `runner_shared`, three in-function).

ONE PATTERN IS WORTH NAMING FOR THE EXECUTOR. Four of this plan's authored figures drifted in a single
day (suite total, deselection count, `aw check` composition, import timings) while the two hardest ones
held exactly (the 253/224/14/13/2 corpus census and the 63/66 narrowed counts). The plan's own
convention already says a live count is never an acceptance bar; the drift measured here is now recorded
in that bullet as evidence for the rule rather than as an aside.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1201 | HIGH | UNDER-SCOPE | D. Anti-regression (an unasserted behavior change on operator-facing output) | `run_dashboard._run_host({"driver":{"id":X}}, [])` driven for every relevant X: TODAY `"opencode"` -> `"unknown"`, `"antigravity"` -> `"unknown"`, `"runagy"` -> `"unknown"`, while `"oc"` -> `"oc"` and `"agy"` -> `"agy"`. After E-03 the resolver accepts all three, returning `argv_tokens[0]`, i.e. `"oc"`/`"agy"`/`"agy"`. `_run_host`'s return is a grouping key and is interpolated as `"(unrecorded, {0})".format(host)` | **E-03 changes `_run_host` on FIVE ids while the plan's Expected outcome and V-03 enumerate only TWO.** Beyond the narrowing pair (`octopus`, `agyx` -> `unknown`) there is a WIDENING triple (`opencode`, `antigravity`, `runagy`, from `unknown` to the right host) that the plan never predicts. The widening is a correction, since the viewer already honors those spellings, but it moves dashboard grouping and operator-facing text, so an executor asserting only the named two would ship three unasserted output changes | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-03's Expected outcome now enumerates all five with the measured before/after for each and a note that the two directions differ in kind; a new E-03 paragraph states the five-id change set explicitly; V-03 (b) now demands all five pasted in BOTH directions plus the unchanged controls; the spec-sync section now records both user-visible changes instead of one; new finding row F-10 |
| PR-1202 | HIGH | IN-SCOPE | E. Testing and verification (an unachievable acceptance bar) | Bare `python3 -m pytest` at HEAD `fe6611919`: `1 failed, 3491 passed, 2 skipped, 3 warnings in 66.81s`, 208 deselected; failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, expecting a `2026-09-30` history line against a setter writing `2026-10-01` | **F-07 claims "THE TREE IS FULLY GREEN ... no pre-existing failure to hide behind" and E-05's bar is "zero failures"; the base is RED.** An executor meeting that bar literally cannot, and would either debug a failure they did not cause or judge the plan unexecutable. The deselection count has also moved 207 to 208 | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-07 split: its live-and-green mitigation half retained and re-verified, its "fully green" half moved to a new F-11 recording the falsification, the node id and its date-bomb cause; E-05's bar restated as a failing-node-id SET comparison with the base named RED; the Required tests bullet and V-05 (a) both restated to demand the failing set and to forbid citing either total as a bar |
| PR-1204 | HIGH | IN-SCOPE | G. Plan executability (a mandatory command naming a nonexistent path) | `ls tests/test_rununify_initialize_run.py` -> No such file or directory; `ls tests/ \| grep -i "rununify\|initialize_run"` -> empty; pytest exits 4 on a missing path and runs nothing else; `grep -rln initialize_run_core tests/` -> five files, two already named by the plan. Separately `grep -n test_rununify_host_descriptor agent_workflows/runner_shared.py` -> TWO hits, the second naming `::TheSharedModuleStaysCleanTests` | **E-05 and the Required tests section both put `tests/test_rununify_initialize_run.py` in a MANDATORY eight-file command, and it does not exist, so the literal command produces no per-file evidence at all.** The tell is that the same draft correctly reports a DIFFERENT `rununify`-named file as missing in F-09: the naming family was assumed rather than checked. F-09 also undercounts its own defect at one occurrence when there are two | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both sites corrected to the SEVEN real files, with the missing path named as removed and the exit-4 consequence stated; verified by running the corrected command (`255 passed`); E-05 now tells the executor to confirm each path exists first; F-09 corrected to two occurrences with the class-naming detail; the Deferred row restated for two citations; a new conventions bullet records the verify-the-path-first lesson; new finding row F-12 |
| PR-1203 | MEDIUM | IN-SCOPE | Evidence accuracy (a validation comparison against a wrong baseline characterization) | `aw check --agent` at review: exit 1, 68 findings; enriched severities `info` 45 / `error` 22 / `warning` 1; dominant rules `check.plan-spec-link-missing` 32 and `check.ipd-uncarried-obligation` 13. Findings naming any of the four scope paths: 0 | F-07 states "`aw check` reports 58 pre-existing errors and 0 warnings ... (they are dangling `From-Spec` advisories on other artifacts)", and all three parts are wrong at review: the count, the zero-warning claim, and the rule attribution. The LOAD-BEARING half (none in scope paths) holds, and that is what the validation item should compare | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The Required tests bullet and V-05 (e) both restated to compare the set of findings NAMING a scope path (empty in both runs, re-verified empty at review) rather than any total, with the authored figure and its characterization explicitly marked as not a bar and wrong |
| PR-1207 | MEDIUM | IN-SCOPE | Evidence accuracy (a stale live count presented as context without its drift) | Four authored figures re-measured at review: suite `3387 passed` green -> `3491 passed` with 1 failure; deselection 207 -> 208; `aw check` 58/0 -> 68 with a warning tier; imports 0.076/0.347 -> 0.070/0.170. Two held exactly: the corpus census (253 id-less, 224/14/13/2) and the narrowed counts (63, 66) | The plan already carries the right convention ("A LIVE COUNT IS NEVER AN ACCEPTANCE BAR") but states it abstractly, while four of its own figures drifted in one day. Without the measurement the convention reads as boilerplate and an executor may still reconcile against the authored numbers | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The conventions bullet now carries the measured drift of all four figures and names the two that held, so the rule is evidenced by this plan's own history; E-05 and the Required tests bullets name both the authored and the review figures as context only |
| PR-1205 | LOW | IN-SCOPE | Evidence accuracy (a correct conclusion with a false proof) | `grep -rn gxsprh` across the tree (excluding this plan and the lane inputs) returns about 16 hits: the test docstring, the graduated backlog item's three fields, executed plan `otr54d` (four lines incl. its `- Carrier:` row), that plan's review record (2), the plans INDEX, and two other pending plans (`9jkek2`, `90z361`) | F-02 states "a tree-wide search for `gxsprh` returns that line and nothing else, so this plan is the sole discharge of that obligation". The search returns many hits. The conclusion SURVIVES and is strengthened (exactly one hit is a code-side obligation naming this item as carrier, with `otr54d`'s `- Carrier:` row as the formal handoff), but a reader re-running the stated search sees 16 and may distrust the finding | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 restated to claim sole discharge of the CODE-SIDE obligation, with the correction recorded, the hit classification named, and its evidence column extended with the full re-measured `_run_host` probe including the three widening ids; new finding row F-13 |
| PR-1206 | LOW | IN-SCOPE | Evidence accuracy (an overstated multiplier on a sound decision) | Timed at review: `import agent_workflows.run_dashboard` 0.070s, `import agent_workflows.runner_shared` 0.170s (ratio about 2.4), against the authored 0.076s and 0.347s and the conclusion "would multiply its import cost by roughly five". Independently confirmed: `runner_shared` absent from `sys.modules` after importing `run_dashboard`; AST scan shows ZERO module-level `run_viewer` imports in `runner_shared` and three in-function | F-08's multiplier is about half the claimed size, and import timing is machine- and cache-dependent enough that no fixed multiplier should be asserted. The DECISION (lazy in-body import, following `_default_cache_path`) is unaffected and every structural claim around it verified | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-08 now carries both measurements, says "several-fold" rather than a fixed multiplier, states that timing is machine-dependent, notes the decision does not turn on the ratio, and records the AST no-cycle confirmation; new finding row F-14 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The widening triple (`opencode`, `antigravity`, `runagy` moving from `unknown` to a real host on the dashboard) is a behavior change the plan never intended. Accept it, or make E-03 preserve today's narrower dashboard behavior? | Accept it, and require it asserted in both directions | Preserving today's behavior by keying the dashboard on a narrower set than the viewer. REJECTED: that reintroduces a per-consumer vocabulary, which is the exact duplication this plan deletes, and it would leave the two consumers disagreeing about ids the viewer already honors. Treating it as out of scope and silent. REJECTED: `_run_host`'s return is a grouping key in operator-facing text, so an unasserted change to it is precisely the kind of silent output drift a reviewer exists to catch | `_run_host` driven on all eleven relevant ids before the change; the viewer's literal tuples already accepting all three spellings; `argv_tokens[0]` measured as `oc`/`agy`, the tokens the function already returns | yes |
| D-2 | `tests/test_rununify_initialize_run.py` does not exist. Substitute the real `initialize_run_core` coverage files, or drop the entry? | Drop it to seven files, noting that two of the seven already cover `initialize_run_core` | Substituting the three other files `grep` found (`test_run_selection_policy.py`, `test_runner_active_conflict.py`, `test_orchestrator_shape_gate.py`). REJECTED: none of them consumes a driver identity or host label, which is the stated selection criterion for this list, so adding them would dilute the evidence rather than strengthen it. Leaving it and letting the executor discover the error. REJECTED: pytest exits 4 on a missing path and runs NOTHING, so the entire mandatory per-file evidence step would silently produce no evidence | `ls` returning no such file; the corrected seven-file command run at review returning `255 passed`; `grep -rln initialize_run_core tests/` showing two of the seven already cover it | yes |
| D-3 | The base suite carries a pre-existing date-dependent failure. Fix it here? | No. Record it as the baseline the executor must capture as a node-id set | Fixing `test_release_exempt_setter_roundtrip_and_parity`. REJECTED: plan-review reviews planning documents only and must not change code or tests, and that file is outside this plan's four scope paths. Ignoring it. REJECTED: E-05's literal bar is "zero failures", which is unmeetable, so silence would leave an unexecutable acceptance criterion | plan-review's opening constraint; the reproduced failure and its `2026-09-30` versus `2026-10-01` diff; E-05's stated bar | yes |
| D-4 | Should this review correct the two dangling `tests/test_rununify_host_descriptor.py` citations in `runner_shared.py`, which the plan defers? | No. Leave them deferred, and only correct the plan's UNDERCOUNT of them | Correcting the comments. REJECTED: this workflow must not change production code, and the plan's own reasoning for deferring (keeping a one-function diff in a 37598-line module) is sound. Removing the deferral row as cosmetic. REJECTED: the defect is real and measured, and the row is the only durable record of it | `grep -n test_rununify_host_descriptor agent_workflows/runner_shared.py` -> two hits; plan-review's review-planning-documents-only constraint; the plan's existing `Carrier: gxsprh` row | yes |
