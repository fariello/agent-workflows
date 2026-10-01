# Review findings: plan guti33

- Subject-Id: guti33
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (MEDIUM, fixed), PR-906 (LOW, fixed), PR-907 (LOW, fixed)

## Round 1

Reviewed at HEAD `b7be444b7` in an isolated review lane. The plan file was committed and unmodified
(`git status --porcelain` clean for it), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `{"outcome":"clean","exit":0,"findings":0}` BEFORE semantic
review. The plan is `- Kind: child`, so the `IPD-S407` orchestrator child-row check does not apply.

THE PLAN'S CENTRAL ARGUMENT IS CORRECT AND UNUSUALLY WELL SOURCED, AND REVIEW REPRODUCED IT. Driving
`artifact_core.drift_exit_code` returns `error -> 1`, `warning -> 1`, `info -> 0`, `"" -> 1`, `[] -> 0`, so
the plan's single most load-bearing claim holds: the reviewer-recommended `warning` tier for plain `moved`
would relabel a finding while changing no behavior whatsoever, and `info` is the only advisory tier that
exists. The precedent the plan cites is verbatim in the registry (`check.stale-index-missing`: "MISSING ->
`info`, the ONLY non-failing severity ... `warning` here would still exit 1 on every fresh clone"), as is
the keep-the-registry-strict precedent (`check.ipd-uncarried-obligation`, whose `evaluate_durable_carrier`
stamps `carrier_severity_for_plan`'s per-plan tier onto a `_core.Drift(..., severity=severity)` exactly as
E-02 proposes). `enrich_drift` does read `severity=drift.severity or spec.severity`, so an explicit stamp
survives enrichment. The runner's refusal set is read from the SHARED predicate and filters to
`SCOPE_STALE_MOVED_TERMINAL`/`SCOPE_STALE_VANISHED` with no reference to severity at all, so E-02 cannot
move it. The spec paragraph the plan amends exists and says what the plan quotes. OQ-02 and OQ-03 are both
properly resolved from measurement rather than preference, and OQ-01 correctly routes a maintainer decision
with its hazard measured and a durable carrier (`es7wdp`, confirmed `open`). The design judgement here is
sound and I found nothing to replan.

WHAT REVIEW FOUND IS A CLUSTER OF ONE KIND OF ERROR, AND THE KIND MATTERS MORE THAN ANY INDIVIDUAL ROW. The
plan is built on measurements of a LIVE tree, it knows this (it already carried a re-derive rule in E-01 and
an explicit warning against comparing finding counts), and it still wrote six live figures as if they were
stable. Measured at review, one day after authoring, EVERY ONE of them had moved:

| Figure | Authoring | Review |
|---|---|---|
| live stale findings | 4 (plans `aisk5z`, `2misq5`, `dta75n`) | 2 (plans `mc6r92`, `qkwu1r`) |
| `check plans` findings | 54 | 63 |
| `aw check all` findings | 58 | 68 |
| `.aw/records/` Scope-Paths census | 78 | 76 (per-tree split reshuffled) |
| bare suite | `3312 passed, 2 skipped` | `2 failed, 3445 passed, 2 skipped` |

The last row is the consequential one and is PR-905. The others are PR-902/PR-903/PR-907 and each is fixed
by stating the stable PROPERTY and demoting the number to context.

THE ONE STRUCTURAL ERROR, PR-901, is of a different kind and is the finding most likely to have cost the
executor real time. E-02 instructed stamping a severity on "both `Drift` constructions (the resolved and
unresolved branches)" and V-02 demanded evidence of "a `severity=` argument on BOTH `Drift` constructions".
There is ONE. Walking `check_scope_path_target_stale`'s AST returns `Drift` constructions: 1, `enrich_drift`
calls: 1. The `if stale.resolved: / else:` branching computes only the `detail`/`observed`/`recovery` STRINGS
and falls through to one shared `drift.append(...)`. So an executor doing the work correctly could not
produce the evidence its own V-item demanded, and the two available responses were both bad: hunt for a
second site that does not exist, or split the shared emit into two branches to make the evidence producible,
which is a gratuitous refactor of a shared function driven by a false premise. The single-mapping instruction
survives, but it is now justified on self-documentation rather than on a nonexistent drift risk between two
branches.

PR-904 is a validation command that can PASS VACUOUSLY. The plan prescribes
`git diff -- .aw/records/specs/ | grep -nP '[\x{2013}\x{2014}]'` in three places and treats empty output as
proof of no en or em dash. Driven on a fixture containing U+2013 and U+2014: in a UTF-8 locale grep reports
both lines; under `LC_ALL=C` it FAILS with `grep: character code point value in \x{} or \o{} is too large`,
exit 2, and writes NOTHING to stdout. An executor who checks only stdout therefore records a pass over prose
that does contain a dash, and the diagnostic is invisible on stderr. The repository treats the locale as
variable (`run_evidence.DEFAULT_ENV_ALLOWLIST` captures both `LANG` and `LC_ALL`), so a UTF-8 locale is not
a safe assumption. Replaced with a decode-in-source `python3 -c` probe, and V-05 now also requires the
probe's exit status so a vacuous pass is distinguishable from a real one. NOTE this idiom appears in many
other pending plans; fixing them is not this plan's work and is not proposed.

TWO THINGS THE PLAN ASSERTED THAT I CHECKED AND STRENGTHENED RATHER THAN CORRECTED. First, the reachability
claim (F-03) is right and is right for a second reason the plan did not state: `work_cmd._validate_plan_via_engine`,
which gates `aw commit` and `aw work begin`, also calls `check_type(repo_root, "plans")` and so also cannot
see this rule, meaning the re-tier touches neither severity contract's gate behavior. Added. Second, F-11's
`vanished` false-positive shape, which authoring declined to carry on the grounds that it was "noticed" not
"measured": I REPRODUCED it on a scratch repo (a plan declaring a to-be-created `.aw/records/backlog/open/...`
path classifies `vanished`, `resolved=()`), so that half of the rationale is withdrawn. The decline still
stands, on a different measurement I took instead: driving `stale_record_scope_paths` over every pending plan
returns ZERO `moved-terminal` or `vanished` entries, so no live plan is refusable on this shape, and filing
an item would assert the predicate is WRONG, which nothing here establishes. That is PR-906, and the plan
also carried a direct self-contradiction there (prose saying the executor "must file" an item beside a
`Carrier-Declined` saying nothing is owed), now removed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | G. Plan executability (an instruction and a V-item describing code that does not exist) | `agent_workflows/check_engine.py:6327` `check_scope_path_target_stale` walked with `ast`: `Drift` constructions: 1 (line 6363, 3 positional args, 0 keywords), `enrich_drift` calls: 1. The `if stale.resolved:` / `else:` branches at `:6343`/`:6354` compute only `detail`/`observed`/`recovery` strings | **E-02 said to stamp "both `Drift` constructions (the resolved and unresolved branches)" and V-02 demanded evidence of a `severity=` argument on "BOTH"; there is exactly ONE.** An executor doing the work correctly could not satisfy its own validation item, and the two ways out are to hunt for a nonexistent site or to split the shared emit into two branches purely to make the evidence producible, which is an unjustified refactor of a function the runner's refusal path also depends on | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 and V-02 both corrected to ONE construction, with the AST measurement stated; E-02 now tells the executor to stamp every construction found from the same mapping if a concurrent refactor added one, and NOT to treat the count as a defect; the single-mapping instruction re-justified on self-documentation and future-proofing. New finding row F-13 |
| PR-902 | HIGH | IN-SCOPE | Live-artifact success criteria (re-derivation convention); evidence accuracy | `check_engine.check_scope_path_target_stale(Path("."))` driven: 2 findings, both `moved`, at `.aw/records/plans/pending/20260930-hv8zlg-01-mc6r92-...ipd.md` and `...20260930-p7dtbr-01-qkwu1r-...ipd.md`. `aw find plans aisk5z\|2misq5\|dta75n` all still `pending`; their review records (`...-aisk5z-....review.md` PR-001, `...-dta75n-....review.md` PR-D02) record the declarations being corrected | **F-01's measured population (4 findings in `aisk5z`, `2misq5`, `dta75n`) had turned over COMPLETELY in one day: the count is 2 and neither plan is one of the three.** The plan named those plans in four places (F-01, the conventions section, the Deferred section, the execution contract). The churn is not a defect in the plan's argument, it is a STRONGER version of it, but written as a fixed population it would have an executor looking for plans whose defect was already fixed | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-01 rewritten with both measurements and the explicit conclusion that the population is a regenerating STEADY STATE, so recurrence is the argument and no count is a bar; all four name-dropping sites de-named; E-01 now states that a re-derived count of ZERO is a legitimate observation and not a failure |
| PR-903 | MEDIUM | IN-SCOPE | Live-artifact success criteria; evidence accuracy | `check_engine.check_type(Path("."), "plans")` -> 63 findings (33 `plan-spec-link-missing` info, 12 `ipd-uncarried-obligation` error, 6 `ipd-carrier-finished-unverified` info, 6 `ipd-lint-diagnostic` info, 5 `lifecycle-transition-invalid` error, 1 `scope-drift` error); `check all --agent` -> `"findings":68`; `parse_scope_paths` census -> 76 entries, `specs/approved` 17 (was 14), `backlog/open` 5 (was 9), `backlog/graduated` 3 (was 0) | F-04's 54/58 and F-09's 78-with-split are all stale one day on. No V-item compared against them (the plan already forbade total-count comparison), so this is an accuracy rather than an executability defect, but F-09's figure was presented as a precise census and F-04's as a composition an executor might reconcile against | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 carries both measurements with the full re-measured per-rule-and-severity composition and names the two STABLE facts (both surfaces exit 1 at base; the non-`info` population is non-empty) as the only ones any item may use; F-09 restated as a range with the stable properties named and an explicit note that no E or V item depends on it; a new conventions bullet records the whole churn table |
| PR-904 | MEDIUM | IN-SCOPE | E. Testing and verification (a validation command that can pass vacuously) | GNU grep 3.11 on a fixture containing U+2013 and U+2014: default UTF-8 locale reports both lines (exit 0); `LC_ALL=C grep -nP '[\x{2013}\x{2014}]'` -> `grep: character code point value in \x{} or \o{} is too large`, exit 2, EMPTY stdout. `run_evidence.DEFAULT_ENV_ALLOWLIST` includes `LANG` and `LC_ALL` | **The no-dash check prescribed in E-06(5), V-05 and the Required tests section PASSES VACUOUSLY under a C locale**, because it is judged on empty stdout while the failure goes to stderr. A plan whose own spec amendment must contain no dash would then be validated by a command that checked nothing | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All THREE sites replaced with a locale-independent `python3 -c` probe decoding `\u2013`/`\u2014` in source; V-05 additionally requires the probe's exit status so a vacuous pass is detectable; new finding row F-14 and a conventions bullet prohibiting the `grep -P` idiom for this purpose. SWEEP NOTE (plan-review Step 2.4): the third occurrence, in the Required tests section, was missed on the first pass and caught by grepping the plan for the superseded token `grep -nP` after the other two were fixed, which is exactly the sweep the workflow mandates; `grep -n "grep -nP"` on the plan now returns no hit outside F-14's and the conventions bullet's prohibitions of the idiom |
| PR-905 | MEDIUM | IN-SCOPE | E. Testing and verification (a false baseline that would manufacture a regression) | Bare `python3 -m pytest` -> `2 failed, 3445 passed, 2 skipped, 3 warnings in 71.50s`. Failing: `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` (reproduces in isolation; asserts a `2026-09-30` history date against a setter writing `2026-10-01`) and `tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_two_process_lock_wait_succeeds` (PASSES in isolation, so a flake or order interaction) | **The plan asserted "The suite is GREEN at base, so ANY failure after this change is this plan's and is blocking" and the base is NOT green.** The plan did carry a fallback clause, but its primary instruction to E-06 was to compare against `3312 passed, 2 skipped`, so an executor following the stated bar would attribute two unrelated failures (one of them a date bomb, one non-deterministic) to a one-keyword change in a severity stamp | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Baseline section rewritten: the green claim withdrawn and the falsification stated, both node ids named with their distinct kinds, and the bar changed from a count to a FAILING-NODE-ID SET comparison. E-01 gains a fifth measurement (paste the pre-change failing node-id set before any edit); E-06(1) and V-06 both re-derive and compare as a set, with an explicit prohibition on comparing against `3312 passed` |
| PR-906 | LOW | IN-SCOPE | Obligation carrying (a Deferred entry contradicting its own `Carrier-Declined`) | Plan Deferred section: prose "It is a genuine defect shape and needs its own item, which this plan's executor must file rather than absorb" beside `Carrier-Declined: NOTHING IS OWED YET`. Review probe: a plan declaring an uncreated `.aw/records/backlog/open/...backlog.md` returns `StaleScopePath(..., classification='vanished', resolved=())`; `stale_record_scope_paths` over all pending plans returns ZERO `moved-terminal`/`vanished` entries | The entry told the executor to file an item and the decline immediately below said nothing was owed, so the executor's obligation was genuinely ambiguous. Separately, the decline's stated reason ("the measurement is a scratch-repo construction, not an observed incident ... a shape was noticed") understated what authoring had: review reproduced the classification independently, so the shape IS measured | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The contradictory clause removed and replaced with an explicit "this plan's executor is owed NOTHING here and must NOT file an item". The decline re-grounded on the measurement review actually took (zero live refusable entries, and the predicate's behavior is defensible rather than provably wrong), with the withdrawn half named. F-11 updated with the independent reproduction |
| PR-907 | LOW | IN-SCOPE | Evidence accuracy (figures stated with more precision than they carry) | `doctor --agent` 119 findings (F-07) and `grep -c "def test" tests/test_scope_path_target_stale.py` -> 16 (Required tests) are both live counts presented as facts; the 16 still holds, the 119 is a whole-tree total that moves with every other count measured in PR-903 | Two more live figures stated as stable. Lower severity than PR-902/903 because F-07's load-bearing half is the ZERO (which follows structurally from the single call site and so IS stable) and the 16 happened not to move | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-07 now labels the 119 as context and the zero as the structural claim; the Required tests section and V-04 both ask the executor to count the module's pre-existing tests at the executing HEAD rather than asserting 16 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan's OQ-02 resolves the advisory tier to `info` rather than the reviewing plan `6h8j1r` PR-308's recommended `warning`. Does that resolution survive independent measurement, or should the plan defer to the earlier review? | `info`, resolution upheld; no change to OQ-02 | Reverting to `warning` to honor PR-308 as written. REJECTED on measurement, not on judgement: it changes a label and no behavior, so it would not achieve the thing PR-308 asked for. Escalating the discrepancy to the maintainer. REJECTED because it is a fact question the repository answers, and asking would spend a human turn on arithmetic | `artifact_core.drift_exit_code` body is `return 1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0`; driven: `error -> 1`, `warning -> 1`, `info -> 0`, `"" -> 1`, `[] -> 0`. Registry comments for `check.stale-index-missing` and `check.ipd-uncarried-obligation` each record the identical correction independently | yes |
| D-2 | E-02/V-02 describe two `Drift` constructions where one exists. Correct the plan to ONE, or let the executor discover it? | Correct to ONE, state the AST measurement, and instruct the executor to stamp every construction found if a concurrent refactor adds one | Leaving it and relying on the executor's judgement. REJECTED: V-02 demanded evidence of a second `severity=` argument, and the cheapest way to produce evidence for a nonexistent site is to create it, i.e. split a shared emit in a function the runner's refusal path shares. Deleting the single-mapping instruction as now unmotivated. REJECTED: the mapping is still the better shape on self-documentation grounds and costs nothing | `ast` walk of `check_scope_path_target_stale`: `Drift` constructions 1 at line 6363 with 3 positional args and 0 keywords; `enrich_drift` calls 1; the branch bodies at `:6343`/`:6354` assign only strings | yes |
| D-3 | The `vanished` false-positive shape (F-11) reproduces. Does the plan now owe a backlog item for it, overriding its `Carrier-Declined`? | No item. The decline stands, but on a re-grounded basis, and the contradictory "executor must file" clause is removed | Requiring an item, which the reviewer is entitled to do under the plan's own stated terms ("a reviewer can require an item if they judge the shape real"). REJECTED on the second measurement: zero live pending plans carry a refusable entry, so nothing is broken today, and an item would assert the predicate is WRONG to refuse a path that does not exist, which is a defensible behavior rather than a measured defect. Widening this plan to cover `vanished`. REJECTED: that changes a runner REFUSAL, not a report, and is outside the item's question | Scratch-repo probe returning `classification='vanished', resolved=()`; `stale_record_scope_paths` over every pending plan returning zero `moved-terminal`/`vanished` entries; `runner_shared.execute_item`'s refusal filter membership | yes |
| D-4 | Should this review also fix the locale-dependent `grep -P '[\x{2013}\x{2014}]'` idiom in the other pending plans that use it? | No. Fix it in `guti33` only and record that the class is wider | Fixing every occurrence. REJECTED: those are other agents' in-flight plans and the shared-checkout rule forbids editing them; it would also sweep their files into this review's commit. Filing a backlog item for the class. NOT DONE by this review, which is a reviewing act and must not create work it was not asked for; recorded in F-14 so the next reader of any such plan has the measurement | AGENTS.md shared-checkout rule; plan-review Step 2.4 ("fix it in the owning plan and cross-reference it from dependent plans"); the measured grep behavior under `LC_ALL=C` | yes |
