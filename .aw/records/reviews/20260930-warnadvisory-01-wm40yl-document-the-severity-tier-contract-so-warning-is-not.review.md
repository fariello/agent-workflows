# Review findings: plan wm40yl

- Subject-Id: wm40yl
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-W01 (HIGH, fixed), PR-W02 (HIGH, fixed), PR-W07 (HIGH, fixed), PR-W03 (MEDIUM, fixed), PR-W04 (MEDIUM, fixed), PR-W05 (LOW, fixed), PR-W06 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `5bbe6011`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, one advisory finding) BEFORE semantic review;
`--phase review-finalize` reports conforming after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator row check does not apply.

WORTH RECORDING ABOUT THE PREFLIGHT ITSELF, since it bears on how much a reviewer may lean on it: the lint
reported conforming at BOTH checkpoints while `aw check` reported an `error`-severity
`check.ipd-uncarried-obligation` on this same plan for six uncarried obligations (PR-W07). The two gates ask
different questions, and a reviewer who runs only the lint will miss a project-rule violation that fails
closed elsewhere. I ran `aw check` filtered to this plan before and after, which is what surfaced it.

THE DIAGNOSIS IS CORRECT AND I RE-RAN IT RATHER THAN TRUSTING IT. The central measurement reproduces to
the value on all eight inputs: driving `artifact_core.drift_exit_code` with a one-element list gives
`error` 1, `warning` 1, `warn` 1, `info` 0, `""` 1, `"advisory"` 1, `"INFO"` 1, and `[]` 0. So `info` is
exactly the only exempt tier, the match is case-sensitive and exact, and no near-miss spelling is advisory.
The legacy three-positional `Drift("loc","rule","detail")` does construct, does carry `severity=''`, and
does yield 1, so the fail-closed claim holds. `_DEFAULT_RULESPEC` is `RuleSpec(severity='error', ...)` and
`rule_spec` on an unregistered id returns it.

F-02, F-04, F-06 and F-09 verify in full:

- F-02's three instances are all real and all say what the plan says. `76w6mq` PR-201 quotes the authored
  "WARN rather than error, or the repository would fail its own check for documenting itself" and records
  the correction to `info`. `k9awrq` PR-902 exists and the `check_engine.py` comment carries the exact
  string `DECISION 02-k9awrq-D1` with "`info`, AND THAT IS A MEASUREMENT, NOT THE PLAN'S LITERAL WORD".
  `cnzrxb` PR-001 exists and reads as quoted.
- F-04 is exactly right, which is the root cause. `docs/cli-output-contract.md` section 2 lists
  `severity` as "(`error`, `warning`, `info`)" and says nothing about what each DOES; section 3 states the
  `0`/`1`/`2` classification without mentioning severity; section 10's only `drift_exit_code` remark is
  that the classification "carries over unchanged". `CONTRIBUTING.md`'s single severity sentence is one
  rule's behavior. `GUIDING_PRINCIPLES.md` covers only the `[ERROR]`/`[WARN ]`/`[INFO ]` rendering labels.
- F-06's seven sites in six files reproduce exactly, and the split is six `non-info-fails` against one
  `warning-is-advisory`.
- F-09's own rule is proven by its own numbers moving, which is the best possible evidence for it.
- F-07's four named rule severities all re-verify unchanged (`info`, `warning`, `warning`, `error`), and
  the two shouting `DO NOT READ` comments are present.
- OQ-01's cost figure re-verifies: 12 `warning` rules, and the two staged ones carry the in-code comment
  "Staged severity is warning (which drives a nonzero exit per drift_exit_code), end state error".

TWO SERIOUS FINDINGS.

PR-W01 is the one that matters, because it is the failure mode a documentation plan cannot afford. E-02
instructed the executor to write that at the lifecycle gates, including "`aw ipd lint`'s carrier merge",
`warning` prints as a non-blocking advisory. That is FALSE. `ipd_lint`'s merge is
`(advisory if d.severity == "info" else blocking)`, so a `warning` there is BLOCKING: it applies the
exit-code shape, not the commit-gate shape. The plan's own F-06 states this correctly, calls it "a THIRD
behavior in practice", and even warns that "E-02 must not overclaim uniformity within the gate class" - so
the plan contradicts itself between a finding and the item an executor actually follows, and the item wins.
Shipping it would have published a false statement in the very document written to stop people being
misled. A second omission compounds it: at the commit gate, severity is not the only input, because
`work_cmd._validate_plan_via_engine` routes `check_engine._SCOPE_DRIFT_RULE` to the advisory list by RULE
ID ahead of the severity branch, despite that rule being registered `error` (verified both by reading the
partition loop and by `ce.rule_spec('check.scope-drift')`). A reader applying the published severity table
alone would get that rule wrong. E-02 now states each gate as its own case, requires the override, and
V-02 adds a negative check that the false sentence is absent.

PR-W02 is a class defect in the plan's own evidence. F-09 correctly forbids asserting a live findings
count, but F-05, F-07, F-08 and F-09 each state OTHER live numbers as if fixed, and three of the four had
already drifted between authoring and review: test modules referencing `drift_exit_code` 7 to 9;
package-wide references 32 to 54; registry 52 rules / 7 `info` to 56 rules / 11 `info`; live tree findings
25 (15 error / 1 warning / 9 info) to 58 (16 error / 42 info). The last is the sharpest: the `warning`
count fell to ZERO, so an executor expecting F-09's shape would see a breakdown with no warning tier and
might read that as a defect. E-01 and E-05 now re-derive rather than confirm, E-04's advisory-tier property
is pinned as `>= 1` rather than as a count, and new F-11 records which figures are STABLE across both
measurements and therefore safe for E-02 to publish.

TWO CORRECTIONS AND TWO SMALLER FIXES.

PR-W03: F-05's headline claim "no test asserts the contract as a contract" is false of the COMMIT gate.
`tests/test_work_gate_severity.py` pins that contract thoroughly in eleven passing tests, including the
warning-advisory case, the error-refusal case, the unregistered-rule fail-closed case, the mixed case, and
both `scope-drift` cases. That does not weaken the plan: it SHARPENS it, because E-04's real and unmet
target is the exit-code half. The row now says so and the module is added to Required tests as a
behavior-neutrality surface.

PR-W04: E-01's STOP condition said to halt on "a THIRD distinct predicate shape". A third behavior is
ALREADY PRESENT at base (F-10), so as written the plan halts on its own baseline. Since the correct
response is to describe it, the stop condition now fires only on a site applying neither known shape, and
the gate names finding a third behavior or a drifted count as explicitly NOT stop conditions.

PR-W05: E-03's skip branch was offered on executor preference ("if the executor judges the pointer not
worth a source edit"), which invites skipping the single highest-value line in the plan. The whole finding
this plan rests on (F-02: three authors wrong while standing at the registry) is that the registry is where
the mistake happens, so the pointer belongs there. The branch is now reserved for a genuinely blocking
condition with a recorded reason, and the reconciliation verb is corrected to `--scope-ack` for a
declared-but-unmodified path rather than `--scope-reason`.

PR-W06: E-04's fifth property ("at least one `info` rule exists") sat beside a measured count of 7 that is
now 11, with no instruction on which to assert. It now specifies the non-empty property explicitly, and
V-04 requires confirming no per-severity distribution is asserted.

NOTHING ELSE WAS FOUND WRONG. The scope fence is right and unusually well argued: keeping
`artifact_core.py`, `cli.py` and every `RuleSpec` severity out is what makes this plan behavior-neutral,
and the three named carriers (`tzjtg4` with its `cli.py`-only scope, `ct1n04`, `1dvtiq`) all exist and own
what the plan says they own. The refusal to delete the nine `check_engine.py` comments in favor of the new
document is correct. F-03's observation that `s7cu7n` moved the item's premise four days after it was filed
is real and is the reason option (a) is rejected rather than followed. OQ-01 is correctly non-blocking with
`Owner: maintainer`, and the plan is genuinely coherent under every answer to it, which is what makes
leaving it open legitimate rather than evasive. E-04's P16 compliance is sound: every assertion calls a
real function, and the monkeypatch mutation check in V-04 was verified workable without touching a tracked
file.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-W01 | HIGH | IN-SCOPE | Rubric A (correctness), G (executability) | plan E-02; `agent_workflows/ipd_lint.py` carrier merge, "(advisory if d.severity == \"info\" else blocking)"; `work_cmd._validate_plan_via_engine` partition loop; `check_engine._SCOPE_DRIFT_RULE` | E-02 told the executor to publish that `aw ipd lint`'s carrier merge treats `warning` as a non-blocking advisory. It does not: that merge blocks anything not `info`, i.e. the exit-code shape. The plan's own F-06 says so and warns against overclaiming, so the plan contradicts itself and the item an executor follows carries the false version. Also omitted: the commit gate routes `check.scope-drift` to advisory BY RULE ID despite its registered `error`, so severity is not that gate's only input. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now states the exit-code contract and EACH gate separately, requires the `check.scope-drift` override, and forbids the merged claim; its Expected outcome adds `check_engine._SCOPE_DRIFT_RULE` to the cited symbols and bars the false sentence. V-02 gains a negative check quoting the gate paragraphs. New F-10 records the measurement. |
| PR-W02 | HIGH | IN-SCOPE | Rubric G (live-artifact criteria), Step 1 evidence | plan F-05, F-07, F-08, F-09, each re-measured | F-09 forbids asserting a live findings count, but four rows state other live numbers as fixed and three had already drifted before review: test modules 7 to 9, package references 32 to 54, registry 52/7-info to 56/11-info, live findings 25 to 58 with the `warning` tier falling to ZERO. An executor confirming against these figures either reports a false mismatch or halts. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 re-derives rather than confirms and says so; E-05's reporting rule widens from findings counts to every live figure and notes that an empty warning tier is now correct; E-04 property 5 is pinned `>= 1`; F-07 and F-08 carry both measurements with the drift stated. New F-11 separates the STABLE figures (the eight verdicts, the seven sites and their six/one split, zero out-of-enum, 12 `warning` rules, the four rule severities, the `error` default) from the drifting ones. |
| PR-W03 | MEDIUM | IN-SCOPE | Rubric E (testing) | plan F-05; `tests/test_work_gate_severity.py` | F-05 claims no test asserts the contract as a contract. False of the COMMIT gate, which `tests/test_work_gate_severity.py` pins in eleven passing tests (warning-advisory, error-refusal, unregistered fail-closed, mixed, both scope-drift cases, three work_begin twins). The module count is also nine, not seven. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 rewritten to name the nine modules, credit the existing commit-gate coverage by test name with its pasted `11 passed`, and state that E-04's real target is the exit-code half. The module added to Required tests and V-04 as a behavior-neutrality surface. |
| PR-W04 | MEDIUM | IN-SCOPE | Rubric G (executability) | plan E-01 STOP condition against F-06's own text | E-01 said to STOP on "a THIRD distinct predicate shape", but a third behavior is already present at base and F-06 documents it. As written the plan halts on its own baseline, and the correct response to that shape is to describe it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now classifies sites by predicate SHAPE, states the expected six/one split, and stops only on a site applying neither shape or on `drift_exit_code` no longer exempting `info` alone. The gate names a third behavior and a drifted count as explicitly NOT stop conditions. |
| PR-W05 | LOW | IN-SCOPE | Rubric F (KISS/UX), G | plan E-03 | E-03's skip branch turned on executor preference, inviting omission of the one line placed where the mistake actually happens (F-02: three authors wrong at the registry). Its reconciliation note also named `--scope-reason`, where a declared-but-unmodified path needs `--scope-ack`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now directs the edit be made, reserves the skip for a genuinely blocking condition with a recorded specific reason, and cites `--scope-ack` for the unused declared path. |
| PR-W06 | LOW | IN-SCOPE | Rubric E (testing) | plan E-04 property 5 | Property 5 ("at least one `info` rule exists") sat beside a measured 7 that is now 11, without saying which to assert, so an executor could pin the count and produce exactly the churn E-04's own prose forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 property 5 now specifies a non-empty assertion (`>= 1`) and cites the drift; V-04 requires confirming no per-severity distribution is asserted. |
| PR-W07 | HIGH | IN-SCOPE | Structural / project rule (`check.ipd-uncarried-obligation`) | `aw check` on this plan; `check_engine.evaluate_durable_carrier`; the plan's Deferred section and OQ-01 | THE PLAN CARRIED A LIVE `error`-SEVERITY FINDING OF ITS OWN, and it is the very defect class the plan documents. `aw check` reported `check.ipd-uncarried-obligation` at `error`: six obligations (five Deferred rows plus OQ-01) named no DURABLE carrier. Every row names its owner in PROSE ("Owned by backlog `ct1n04`", "Durable carrier: this plan's OQ-01"), which reads as complete to a human and is invisible to the machine-readable field the rule requires, so once this plan reached `executed` all six would have classed `done` in `aw attention` and vanished with no record. Notably this did NOT surface in `aw ipd lint --phase author`, which reports conforming, so the structural preflight alone would not have caught it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added the machine-readable field to all six: `- Carrier: 1dvtiq` on the re-tiering row and on OQ-01 (verified `1dvtiq` is `graduated`, which is neither FINISHED nor ABANDONED, so it resolves as a legitimate HANDOFF), `- Carrier: xqm16x` on the tally row, `- Carrier: ct1n04` on the report-volume row, and a reasoned `- Carrier-Declined:` on the two rows that are DECISIONS rather than deferrals (keeping the nine comments; rejecting the rename on F-03's measurement). Re-measured after the fix: zero findings on this plan. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-02's gate statement is false for `ipd_lint`. Fix the document's instruction, or narrow the plan to the exit-code contract alone? | Fix the instruction: state the exit-code contract and each gate separately, three groups rather than two. | (a) Drop the gate contract from E-02 entirely: rejected, because the plan's Concern is that an author reaches for `warning` expecting advisory behavior, and `s7cu7n` made that expectation TRUE at two gates, so a document covering only the exit code would recreate the confusion from the other direction. (b) State "the gates vary, see the code": rejected, that is the status quo F-04 measures as the root cause. | `agent_workflows/ipd_lint.py`'s merge line; `work_cmd._validate_plan_via_engine`'s docstring and partition loop; the plan's own F-06, which already reached this conclusion. | yes |
| D-2 | Is the `check.scope-drift` rule-id override part of the published contract, or an implementation detail? | Part of it. E-02 must state it. | Omitting it as detail: rejected, because it is the one case where the published severity table gives a reader the wrong answer, and a contract document whose table has a silent exception is worse than one that names it. | `work_cmd._validate_plan_via_engine`'s loop (`if enriched.rule == _ce._SCOPE_DRIFT_RULE` ahead of the severity branch) with its in-code rationale; `ce.rule_spec('check.scope-drift').severity == 'error'`; `tests/test_work_gate_severity.py::test_commit_scope_drift_commits_with_advisory` and `::test_scope_drift_registered_severity_is_error`, both passing. | yes |
| D-3 | Three of the plan's live counts have drifted. Update the rows to review-HEAD values, or convert them to re-derived properties? | Both: record both measurements in the row (so the drift itself is the evidence) and convert every consuming item to re-derivation. | (a) Silently update to review values: rejected, that loses the drift, which is the actual finding and the justification for F-09's rule. (b) Delete the counts: rejected, they are useful as context for magnitude; what is wrong is treating them as bars. | Side-by-side re-measurement of each figure; the repository's own live-artifact convention in `.aw/system/workflows/plan-review/plan-review.md` Rubric G. | yes |
| D-5 | Two of the five Deferred rows are DECISIONS (keep the nine comments; reject the rename) rather than deferrals. Give each a `- Carrier:` or a `- Carrier-Declined:`? | `- Carrier-Declined:` with the reason, for both. | Filing a fresh backlog item for each: rejected, that would create a tracked owner for work nobody intends to do, which is the opposite of what the rule protects. Pointing both at `1dvtiq`: rejected for the rename row, because `1dvtiq` carries whether the vocabulary should change AT ALL (already carried by the re-tiering row), while this row records that ONE option is measurably premised on a falsehood, so re-pointing it would duplicate the carrier and blur two different claims. | `check_engine.evaluate_carrier_obligation`'s three escapes, where DECLINED requires only a non-empty reason and explicitly leaves the reason's merit to the reviewer; the precedent in sibling plan `vbhat9`, which uses `Carrier-Declined` for the same shape. | yes |
| D-4 | OQ-01 is `open` with `Owner: maintainer` and `Blocking: no`. Leave it open, or resolve it from repository evidence? | LEAVE OPEN. It is genuinely the maintainer's call. | Resolving it myself: rejected. The question is which vocabulary the repository SHOULD have, which is a scope and risk-appetite decision reserved to the human, and option (c) would re-tier 12 live rules and change CI behavior tree-wide. The repository bounds the cost without choosing: I verified the 12 `warning` rules and the two deliberately staged toward `error`, which shows the call is not even uniform within the 12. | Backlog `1dvtiq`'s own text ("No option is obviously right, which is why this is filed for a maintainer decision"); the 12-rule census; the `check.ipd-priority-required` in-code comment recording the staged end state. | yes |

No `Reversible: no` decision was taken in this round. OQ-01 remains `open`, `Blocking: no`, `Owner: maintainer`; it is not a finding left unfixed and so requires no escalation.
