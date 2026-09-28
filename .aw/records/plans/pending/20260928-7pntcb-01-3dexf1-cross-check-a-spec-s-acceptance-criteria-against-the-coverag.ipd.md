# IPD: Cross-check a spec's acceptance criteria against the coverage of the plan Set implementing it

- Date: 2026-09-28
- Kind: child
- Concern: An advisory `aw check` rule that reports a spec acceptance criterion no `From-Spec` plan demands, scoped and gated so it reproduces the one measured defect without firing on a Set that cites a different id namespace.
- Scope: IN: a criteria parser over a spec's acceptance section; a coverage predicate over the linked plans' validation-bearing sections; one `info`-severity rule registered in `RULE_REGISTRY` and reachable from the plans-content seam; a namespace-in-use gate; tests including the counterfactual pin and a negative control. OUT: any change to spec authoring conventions, any `- Covers:` metadata field, any `aw attention` view, any change to `SPEC_STATUSES` or to how a spec reaches `implemented`, and any promotion of this rule above `info`.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_spec_criteria.py, .aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: 7pntcb
- Set: 7pntcb
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: 3dexf1

## Workflow history

- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog item `7pntcb`. The scope sketch was measured before authoring rather than adopted: probes established that the sketched shape reports 22 findings of which 22 are false positives, that the motivating spec `uonrjg` is fully covered at HEAD, and that a corrected search space reproduces the human review finding exactly (TP=5, FP=0, FN=0) at the authoring commit. The plan implements the corrected shape and carries the refuting measurements as findings.

## Goal

Make the one mechanically detectable criterion-coverage failure visible at authoring time: a spec
acceptance criterion that the plan Set implementing it names nowhere, so a Set can no longer execute to
completion reporting success while a release-gating criterion was never demanded by any plan. The rule is
advisory (`info`) and is deliberately NECESSARY-not-sufficient: it proves a criterion is NAMED, never
that it is genuinely validated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the parser and the coverage predicate

- [ ] E-01 Add a spec acceptance-criteria parser to `check_engine` that returns the ordered, deduplicated list of PREFIXED criterion ids declared under a spec's acceptance-criteria heading. Match the heading case-insensitively on the substring `acceptance` at any `##`+ depth, excluding a heading containing `non-goal`, and close the section on the next heading at the same or shallower depth (the corpus has no bare `## Acceptance criteria`: measured headings include `## 13. Acceptance criteria`, `## 3b. Acceptance criteria`, `## 8. Verification and Acceptance Criteria` and `## Acceptance criteria (testable)`, so an exact-title comparison matches zero specs). Recognize exactly three row shapes, all carrying a LETTER-PREFIXED id: the bold bullet `- **A12b** ...`, the bare enumerated `A5. ...`, and the leading table cell `| AC-1 | ...`. DELIBERATELY DO NOT recognize a bare-digit id (`1.`, `2.`), for the measured reason in finding F-02.
  - Depends on: none
  - Expected outcome: driven over the 19 id6-bearing specs the parser returns prefixed ids for exactly the 8 specs that declare them and an empty list for the rest, including an empty list for a spec whose acceptance section is entirely bare-digit (`2lcqno`, `r07vma`, `z7nbn1`, `kw5y2s`) and for a spec with no acceptance heading at all (`25kzda`, `77tr3o`).
  - Execution state: pending

- [ ] E-02 Add the plan-side coverage search space, built from `ipd_lint.parse` rather than from a raw regex over the file, so a criterion id inside a code fence is not counted (`ipd_lint._structural_lines` is fence-aware). The space is the union of: every `V-*` leaf's text and every one of its indented subfield values, PLUS the body of the `## Required tests / validation` section (`ipd_schema.H_REQUIRED_TESTS`). INCLUDING THAT SECTION IS LOAD-BEARING AND IS NOT A WIDENING FOR CONVENIENCE: `ipd_lint.parse` routes leaves by enclosing H2 and populates `valid_leaves` only from `H_VALIDATION_CHILD`/`H_VALIDATION_ORCH`, so a `valid_leaves`-only space omits where plan `bn026f` actually demands criteria A15 and A16 and reports them falsely uncovered (F-03). Match an id with a token boundary that treats `-` as a word character (`(?<![0-9A-Za-z-])<id>(?![0-9A-Za-z])`) so `A1` does not match inside `A15` and `A-01` is not matched by a search for `A-0`.
  - Depends on: E-01
  - Expected outcome: for spec `uonrjg` at HEAD the space yields 25 of 25 criteria matched (0 uncovered), where a `valid_leaves`-only space yields 6 uncovered; and A15/A16 are matched in `bn026f` via its `## Required tests / validation` rows.
  - Execution state: pending

### Task group 2: the gate, the rule, and its registration

- [ ] E-03 Add the NAMESPACE-IN-USE gate: for a spec with at least one parseable prefixed criterion id and at least one linked plan, compute the matched set first, and when ZERO of the spec's criteria are matched anywhere in the search space, emit NOTHING for that spec. A Set citing a different id namespace is reporting-silent rather than reported as wholly uncovered. Measured necessity (F-04): spec `6m4kow` writes `- **A-01** (R-06) ...` and its five linked plans cite the `R-*` requirement ids, never the `A-*` criterion ids; spec `2vev8j` uses a `| AC-1 | C1 | ...` table and its one linked plan cites the `C<n>` constraint ids. Without the gate those two specs contribute all 22 of the 22 findings at HEAD and every one is a namespace mismatch, not a coverage gap. Record in the code comment that the gate's cost is a genuine false negative: a Set that names NO criterion at all is silent, which is the `7p3tt8` case from the motivating review, and that this is accepted because the alternative is a rule whose every live finding is wrong.
  - Depends on: E-02
  - Expected outcome: at HEAD the rule reports 0 findings over the whole corpus, with `6m4kow` and `2vev8j` gated rather than reported, and `uonrjg` and `7ckptx` fully covered.
  - Execution state: pending

- [ ] E-04 Emit the finding as ONE `Drift` per spec, never one per criterion, following the `evaluate_durable_carrier` idiom: name at most five uncovered ids then `(and N more)`, keep `detail` under about 60 characters for the `doctor.build_remediation` title fallback, and populate `enrich_drift`'s `observed`/`required`/`recovery` (recovery: add the criterion to a child plan's validation or `## Required tests / validation` section, never to the Order-0 parent, because a runner retires an orchestrator while SKIPPING its pre-transition E/V checkpoint). Locate the finding on the SPEC file, since the spec is the artifact whose criteria are unmet and the owning plan is not uniquely determined. Register `check.spec-criteria-uncovered` in `RULE_REGISTRY` at severity `info` with `ASSURANCE_REPOSITORY` and `DET_DETERMINISTIC`, and write the severity rationale in the entry comment: `artifact_core.drift_exit_code` exempts ONLY `info`, so `warning` would exit nonzero exactly as `error` does, and registration is not bookkeeping because an unregistered id falls back to `_DEFAULT_RULESPEC` at `error`. Claim invariant `""` with a stated reason rather than claiming an `I-*` row that does not fit. Choose the rule id to avoid the substrings `graduation` and `duplicate`, which `tests/test_graduation_view.py::NoUniquenessRuleTests` structurally prohibits.
  - Depends on: E-03
  - Expected outcome: `check_engine.rule_spec("check.spec-criteria-uncovered")` returns severity `info`; a fixture with two uncovered criteria produces exactly one `Drift` whose `rule` is that id.
  - Execution state: pending

- [ ] E-05 Wire the predicate into the plans-content seam (`check_content`, `record_type == "plans"`) inside its OWN `try/except`, matching the house pattern where every rule at a dispatch seam has its own guard so one failure cannot suppress a neighbour. The plans seam is reached by BOTH `aw check plans` and `aw check all`, and `aw check plans` is a fail-closed CI step in `tests.yml`; an `info` rule is safe there because it cannot drive a nonzero exit. Do NOT add a new CI step and do NOT add any `aw ipd lint` checkpoint, begin/finalize refusal, or dependency block: no lifecycle gate consumes this rule.
  - Depends on: E-04
  - Expected outcome: `aw check plans` and `aw check all` both reach the rule (proven by a fixture finding appearing on both surfaces), and `aw check plans` still exits 0 on this tree.
  - Execution state: pending

### Task group 3: evidence, contract, and record

- [ ] E-06 Add `tests/test_check_engine_spec_criteria.py` with, at minimum: (a) a clean fixture asserting zero findings and `drift_exit_code == 0`; (b) a POSITIVE control proving the rule can fire, with a spec declaring three criteria and a linked plan naming two; (c) a NEGATIVE control in the sense `tests/test_check_engine_release_gate.py::test_unknown_id6_still_flags_dangling` establishes, proving the reader is not broken into total silence; (d) a sentinel test that `From-Spec: -`, `none` and `unresolved` are treated as absent via `ipd_schema.source_link_is_absent`, with the fixture spec carrying a real `- Id:` so an empty-known-set guard cannot short-circuit it; (e) a bare-digit test asserting a spec whose criteria are all bare digits yields NO findings; (f) a fence test asserting a criterion id inside a code fence does not count as coverage; (g) the namespace-gate test asserting a plan set citing a foreign namespace is silent; and (h) THE COUNTERFACTUAL PIN, a fixture reproducing the motivating defect shape and asserting the uncovered set is exactly the five criteria human review found, so a future scope change that reintroduces the `valid_leaves`-only space fails a test rather than silently degrading. Then amend the invariant catalog spec (declared in `Scope-Paths`) to record this control honestly beside its family, and add one `CHANGELOG.md` line under the pending release with no em or en dashes.
  - Depends on: E-05
  - Expected outcome: the new test file passes; the full bare suite passes; `aw check` and `aw ipd lint` conform.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A RULE'S REGISTRY ENTRY IS ITS PRIMARY DOCUMENTATION, and omitting it is not a cosmetic miss. `check_engine.rule_spec` falls back to `_DEFAULT_RULESPEC`, whose docstring records it as `error`-severity and repository-class so a new rule is "never SILENTLY unclassified (fail toward visible)". An unregistered advisory rule therefore ships fail-closed at `error`.
- `info` IS THE ONLY NON-FAILING SEVERITY, measured rather than assumed. `artifact_core.drift_exit_code` returns `1 if any(getattr(d, "severity", "") != "info" for d in drift)`, and its docstring states only `info` is advisory. Several registry comments record the same driven result (`error` -> 1, `warning` -> 1, `info` -> 0, empty -> 1). The backlog item's word "advisory" therefore means `info`; writing `warning` would satisfy the spelling and defeat the requirement.
- `ipd_lint.parse` ROUTES LEAVES BY ENCLOSING H2, not by parsed kind, and `valid_leaves` is populated only from `valid_titles = {S.H_VALIDATION_CHILD, S.H_VALIDATION_ORCH}`. `## Required tests / validation` (`ipd_schema.H_REQUIRED_TESTS`) is a DIFFERENT section and is absent from `valid_leaves`. This single fact decides the plan's search space (F-03).
- THE PARSER MUST BE FENCE-AWARE, which is why E-02 builds on `ipd_lint.parse` rather than on `re.findall` over raw text: `ipd_lint._structural_lines` is fence-aware, so a `V-01` or an `A15` inside a code fence is correctly ignored. A naive regex would count a fenced example as coverage.
- A GRADUATION-SOURCE LINK HAS ABSENT SENTINELS. `ipd_schema.source_link_is_absent` treats `-`, `none` and `unresolved` (case-insensitively, after stripping quotes) as "no source item", and `check_from_spec_dangling` calls it. Skipping it reintroduces the defect plan `3cs7qg` fixed.
- FINDINGS ARE AGGREGATED PER ARTIFACT. `evaluate_durable_carrier` enumerates at most five locators then appends `(and N more)`, capped at one `Drift` per artifact per rule. A per-criterion `Drift` would let one spec add 21 lines to every `aw check` run.
- RECORD DISCOVERY IS ALREADY SHARED AND SORTED. `check_engine._iter_plan_ipds` and `_iter_spec_records` yield `(path, text)` recursively over both layouts, skipping `_SKIP_NAMES` and ignored paths; `_iter_type_files`'s comment records that sorting is load-bearing because `rglob` order is filesystem-dependent. `check_from_spec_dangling` builds a known-spec-id UNION whose docstring records that either source alone yields false positives under a redirected project layout; reuse it rather than adding a third scanner.
- A CUTOVER KEY MUST BE REGISTERED TO WORK. `config.resolve_cutover_date` falls through to `None` for an unregistered feature, and `None` grandfathers everything forever, which is why `config.KNOWN_FEATURE_CUTOVERS` exists and why its comments say leaving a key out ships the rule "as decoration". THIS PLAN ADDS NO CUTOVER KEY, because the rule is `info` corpus-wide and has nothing to grandfather (F-05).
- A SINGLE-PLAN GRADUATION IS A ONE-CHILD SET WITH NO ORCHESTRATOR, and the setid is the backlog id6: `168p5j`, `5rebcb`, `7bj5sa`, `zf999x` and `yvcdw1` are each one `-01-` child with `- Kind: child` and no Order-0 sibling.
- THE FIX FOR AN UNCOVERED CRITERION BELONGS IN A CHILD, NEVER ON THE PARENT. The motivating review drafted exactly such a parent item and removed it, because a runner retires an Order-0 orchestrator once every child is `executed` and deliberately SKIPS the pre-transition E/V checkpoint, so the item would be marked complete having never been performed. The rule's `recovery` text must say this.

## Findings

| # | Severity | Finding |
|---|---|---|
| F-01 | High | THE CORPUS CONVENTION IS NOT `A<n>`, so the item's parsing premise is too narrow. Measured over 38 spec files: only 2 use the `- **A<n>**` bullet the item names (`uonrjg` 21, `6kwd2e` 41). Only 19 of the 38 files carry a `- Id:` at all (19 are pre-cutover legacy names), and 16 of those 19 have an acceptance-ish heading, of which 8 declare PREFIXED ids across three distinct shapes (bold `- **A12b**`, bare `A5.`, table `\| AC-1 \|`) while 8 more use bare digits only. A parser recognizing one shape reaches 2 specs; recognizing three reaches 8. |
| F-02 | High | A BARE-DIGIT CRITERION ID CANNOT BE TOKEN-MATCHED, so the rule must exclude that shape rather than support it. Probe over `2lcqno` (8 bare-digit criteria, 2 linked plans, 44 V-item chunks) inspected every match site: criterion `1` matched inside `2lcqno` and `exit 1`, `2` inside `exit 2` and `2 cross-type findings`, `4` inside `Section 1 finding 4` and `pqsx96` Section 4`, `5` inside `Section 5` and `the 5 within-type descriptive findings`. Every single match was incidental prose, so bare digits produce FALSE COVERAGE (a criterion reported covered because a plan said "exit 2"), which is strictly worse than silence. Hence E-01 recognizes prefixed ids only and the 4 bare-digit specs with linked plans are silent by construction. |
| F-03 | High | THE OBVIOUS SEARCH SPACE IS WRONG AND PRODUCES FALSE FINDINGS, and this is the finding that most changes the design. Scoping coverage to `ipd_lint.parse().valid_leaves` reports spec `uonrjg` as having 6 uncovered criteria (A12b, A12c, A12d, A15, A16, A20) at HEAD. All 6 are FALSE: `parse` populates `valid_leaves` only from `H_VALIDATION_CHILD`/`H_VALIDATION_ORCH`, and plan `bn026f` demands A15 and A16 in its `## Required tests / validation` section (`- **A15** variation selectors survive ANSI stripping AND truncation`, `- **A16** the six capability profiles`). Adding that section drops `uonrjg` to 0 uncovered. Scope sensitivity measured across four spaces (doc / E+V / V / V-required-only) gave totals 21 / 23 / 28 / 41, so the choice is not a detail: it dominates the result. |
| F-04 | High | THE ITEM'S MOTIVATING INSTANCE IS ALREADY FIXED, so a rule tuned to "find something today" would be tuned to noise. The review that filed this item found A1, A4, A6, A19, A21 orphaned in Set `lifeglyph`; that was resolved 2026-09-19 by editing the children, and all 9 `uonrjg` plans are now `executed`. At HEAD the corrected-scope rule reports 0 for `uonrjg` and 0 for `7ckptx` (33 of 33 covered), and its only 22 findings are the 11 of `6m4kow` plus the 11 of `2vev8j`, ALL of which are namespace mismatches: `6m4kow` declares `- **A-01** (R-06)` and its plans cite `R-*` (0 of 11 A-ids matched, 3 to 20 R-ids per plan), `2vev8j` declares `\| AC-1 \| C1 \|` and its plan cites `C<n>` (0 of 11 AC-ids matched). So the ungated rule is 0 true positives and 22 false positives on the live tree, which is the `gjadwm` failure mode of training agents to ignore a red check. |
| F-05 | Medium | THE CORRECTED RULE IS PROVABLY CLEAN AT HEAD, so it needs NO cutover and NO grandfathering tier. With the E-03 namespace gate, corpus findings at HEAD are 0: 4 specs skip for no parseable criteria, 2 for no acceptance heading, 2 are gated for namespace mismatch, and 2 are genuinely fully covered. This avoids the `carrier_obligations` dilemma entirely (664 rows across 106 plans forced a dated `info` legacy tier), so no `KNOWN_FEATURE_CUTOVERS` key is added. The corollary is that a clean corpus makes the POSITIVE test the entire safeguard against shipping decoration, which is why E-06 demands both a firing fixture and the F-06 counterfactual pin. Severity stays `info` rather than rising to `error` on the strength of a clean tree, because the registry's own comment records that "clean is NOT a STABLE property" and because the rule is necessary-not-sufficient by construction. |
| F-06 | High | THE CORRECTED RULE REPRODUCES THE HUMAN REVIEW FINDING EXACTLY, which is the strongest available evidence that it detects the real defect and not an artifact of tuning. Re-running the predicate against the authoring commit `516eb661` ("plan(lifeglyph): author the nine-plan Set implementing spec uonrjg"), where the defect was live and review had not yet run: scope `V`-only gives TP=5 FP=4 (`A12b`, `A12c`, `A12d`, `A16`), scope `doc` gives TP=0 FN=5 (every id matched in review prose and coverage-map text rather than in a demand), and the chosen `V + Required tests` scope gives **TP=5, FP=0, FN=0**, the exact set `{A1, A4, A6, A19, A21}` that human review escalated as OQ-02. The namespace gate leaves this intact (`uonrjg` matched 20 of 25, so it reports). This measurement is pinned as a test by E-06(h). |
| F-07 | Medium | A PRIOR RESEARCH RECORD RECOMMENDS AGAINST A CHECK RULE HERE, and it must be addressed rather than ignored. Survey `vkub9o` (653 lines, 2026-09-20) measured this question and recommended option B-minus, "a documented convention for NEW specs, no check rule, no parser", plus a DIFFERENT rule: flag a plan graduated from a spec that omits `- From-Spec:` (tracked as backlog `1zknu7`). Its decisive argument is that the missing join EDGE dominates: `c4gd2h` has 37 plans mentioning it and 0 carrying `- From-Spec:`, and `6kwd2e` has 41 criteria and 0 linked plans, so no coverage mechanism can compute their coverage. This plan does NOT contradict that finding and does not claim corpus-wide coverage; it is narrower, and the two are complementary rather than competing (see OQ-01, which raises the ordering for the reviewer). What the survey did not measure is F-06, the counterfactual that the narrow rule reproduces the escalated finding exactly. |
| F-08 | Low | THE RULE IS AUTHORING-TIME BUT NO CURRENT PLAN IS IN ITS AUTHORING WINDOW. All 56 `From-Spec`-carrying plans are terminal (55 `executed`, 1 `superseded`) and ZERO pending plans carry `- From-Spec:`. So the rule's value is entirely prospective, on the next spec-implementing Set, and it can never demand an edit to a plan under `executed/` (which AGENTS.md forbids re-committing). This reinforces `info` and the report-only posture: the population it will police does not exist yet. |

## Proposed changes (ordered, validatable)

1. A criteria parser over a spec's acceptance section, three prefixed shapes only, loose heading match (E-01).
2. A fence-aware, `ipd_lint`-derived plan-side search space spanning `V-*` leaves, their subfields, and `## Required tests / validation` (E-02).
3. The namespace-in-use gate that silences a Set citing a foreign id namespace (E-03).
4. One aggregated `info` finding per spec, located on the spec, registered in `RULE_REGISTRY` with its rationale (E-04).
5. Wiring at the plans-content seam under its own `try/except`, with no new CI step and no lifecycle gate (E-05).
6. A test module including a firing positive control, a negative control, the sentinel/bare-digit/fence/gate cases, and the F-06 counterfactual pin; plus the invariant-catalog amendment and one CHANGELOG line (E-06).

## Deferred / out of scope (with reason)

- THE MISSING-`From-Spec` RULE THAT SURVEY `vkub9o` RECOMMENDS. It is a different predicate over a different population, and folding it in here would make one plan carry two independent rules.
  - Carrier: 1zknu7
- ANY SPEC-AUTHORING CONVENTION CHANGE (mandating one criterion-id namespace, or retrofitting the 8 bare-digit specs). Survey `vkub9o` measured the cost as 1 live spec for a prefixed-families rule and 11 live specs for a single mandated namespace, and this plan deliberately adapts to the corpus instead of asking the corpus to change.
  - Carrier-Declined: Nothing is owed, because this row records a DESIGN CHOICE this plan makes rather than work it drops. E-01 deliberately adapts the parser to all three shapes the corpus already uses, so the bare-digit specs are handled by exclusion (F-02) rather than left as a gap awaiting a retrofit. Naming a carrier would assert an outstanding obligation to change 11 live specs, which survey `vkub9o` recommended AGAINST and no one has accepted.
- A `- Covers:` OR `- Criteria:` PLAN METADATA FIELD. Measured: no such field exists anywhere in `.aw/records`. It would be the option-C shape survey `vkub9o` rejects, because coverage computed from plan-side declarations measures what plans CLAIM.
  - Carrier-Declined: This is a REJECTED alternative, not deferred work. Survey `vkub9o` records option C's failure mode as "a coverage number that is WRONG is worse than no number, because it is trusted", so there is no future plan that should pick this up and a carrier would misrepresent a rejection as a backlog.
- COMPUTING A SPEC'S `implemented` STATUS FROM COVERAGE, or adding an `aw attention` view. This inverts the `APPROVAL_FLOOR` design, which states it enforces "presence + format + resolvability, NOT semantic verification that the work truly happened", and would need a `SPEC_STATUSES` contract change.
  - Carrier-Declined: Rejected rather than deferred, for the reason `APPROVAL_FLOOR` states in its own words. Letting a spec reach `implemented` on the strength of plan prose would WEAKEN a gate that today demands a resolvable artifact, so this is work that should not be done at all, and naming a carrier would schedule it.
- PROMOTING THIS RULE ABOVE `info`, or wiring it into `aw ipd lint` / begin / finalize. Deliberate: the rule is necessary-not-sufficient (a named criterion may still be validated by nothing useful), so it must not gate a lifecycle transition.
  - Carrier-Declined: No obligation is outstanding. The advisory posture is the backlog item's own instruction ("Advisory severity to start") and F-05 records why a clean corpus does not justify promotion. A future tightening pass would need its own corpus measurement and its own plan; it is not owed by this one, and pre-filing it would assert a decision the maintainer has not made.
- THE GATE'S ACCEPTED FALSE NEGATIVE. A Set that names NO criterion at all is silent, which is exactly the `7p3tt8` child from the motivating review.
  - Carrier-Declined: Accepted permanently inside this plan rather than carried out of it. E-03 requires the cost be recorded in the code comment beside the gate, and V-03 measures the gate's effect both ways (0 reported with it, 22 without), so the limit is documented and evidenced where a reader of the rule will find it. The alternative is a rule whose every live finding is a namespace mismatch (F-04), so there is no better variant for a future plan to build.

## Scope check

- Over-scope: none. Every E-item maps to the backlog item's scope sketch ("a consistency rule reporting, for each spec with at least one `From-Spec` plan, the criteria no such plan names. Advisory severity to start") or to its explicit instruction to "measure the corpus BEFORE choosing a severity", which F-01 through F-06 discharge.
- Under-scope: the rule does NOT prove a criterion is genuinely validated, only that it is NAMED. This is the backlog item's own stated limit ("a token grep proves a criterion is NAMED, not that it is genuinely validated... NECESSARY-not-sufficient") and is preserved deliberately, not overlooked. It also does not reach a spec whose criteria are bare digits (4 specs with linked plans), a spec with no acceptance heading (2), or a Set citing a foreign namespace (2); each exclusion is a measured decision recorded in F-02, F-01 and F-04 respectively, and together they are why the rule is honestly a narrow backstop rather than corpus-wide coverage.
- NOT SCOPE, BUT THE REVIEWER SHOULD KNOW: `Scope-Paths` includes the invariant-catalog spec, which is at `- Status: draft`. AGENTS.md requires a plan amending a spec to declare the file, which this does, and both runners announce declared spec edits before a run and reconcile them at finalize.

## Required tests / validation

- The full suite BARE, `python3 -m pytest`, with the actual `N passed` summary line pasted. Not `-n0`, not an extra `-q`, not `-p no:randomly`.
- `tests/test_check_engine_spec_criteria.py` covering all eight cases E-06 enumerates: clean fixture (zero findings, `drift_exit_code == 0`); positive control that FIRES; negative control proving the reader is not silently broken; `From-Spec` sentinel handling with a real `- Id:` in the fixture spec; bare-digit silence; code-fence non-coverage; namespace-gate silence; and the F-06 counterfactual pin asserting the uncovered set equals `{A1, A4, A6, A19, A21}`.
- A corpus run on this tree pasting the finding count for the new rule, which must be 0, alongside the per-spec decision table (report / gated / skipped) so a reader can tell a clean spec from an exempt one.
- `aw check plans` and `aw check all` both exit 0 on this tree, with output pasted, proving the `info` rule adds no failing finding and is reachable on both surfaces.
- `aw ipd lint --phase pre-transition` conforming on this plan, output pasted.
- `aw sanitize --agent` clean, since the plan and tests cite repository paths.

## Spec / documentation sync

- `.aw/records/specs/draft/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md` is AMENDED (declared in `Scope-Paths`), because that catalog is the registry's invariant authority and the precedent is that plan `216rgg` amended it in the same commit that re-scoped a rule. WHY, stated because a spec edit changes the contract every other plan is reviewed against: this rule claims invariant `""` rather than an existing `I-*` row, and an empty claim is only honest if the catalog records WHY no row fits. The nearest rows are deliberately not claimed: `I-05` is about a plan's own validation items being evidenced at finalize, not about a SPEC's criteria being demanded by a Set; `I-07` is release-gate preservation across a handoff. The amendment records criterion coverage as a guidance-class concern whose only deterministic observable is "a criterion id is named somewhere", with the honest limit that naming is not validating.
- `CHANGELOG.md` gets one `- Added:` line under the pending release, with no em or en dashes (user-facing prose).
- NO change to `.aw/records/specs/README.md`, `AGENTS.md`, `.aw/records/plans/README.md`, `docs/`, `tests.yml`, or `config.KNOWN_FEATURE_CUTOVERS`: the rule introduces no authoring convention, no new CI step, and no cutover key (F-05).

## Open questions

### OQ-01: Should this narrow rule ship before, after, or instead of the missing-`From-Spec` rule that survey `vkub9o` recommends and backlog `1zknu7` tracks?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: 1zknu7
- Resolution or deferral rationale: NOT BLOCKING, because the two are independent predicates over different populations and this plan is correct on its own terms whichever order is chosen. Raised because the survey explicitly recommended AGAINST a criteria check rule (F-07) and a reviewer deserves that disagreement stated rather than buried. THE CASE FOR SHIPPING THIS ANYWAY, which is new evidence the survey did not have: F-06 shows the corrected rule reproduces the escalated review finding exactly (TP=5, FP=0, FN=0) at the authoring commit, so it demonstrably catches the defect that prompted the item. THE CASE FOR `1zknu7` FIRST: its edge is the precondition for coverage at all, since a spec with no `From-Spec` plan is unreachable by this rule (`6kwd2e`, 41 criteria, 0 linked plans), so `1zknu7` widens this rule's reach as a side effect. My recommendation is to ship this one and keep `1zknu7` open, since this rule is `info`, adds no gate, and is provably 0-finding at HEAD, so its downside is bounded; but the ordering is the maintainer's call on priority, not a technical blocker.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Drive the parser over every spec under `.aw/records/specs/` and paste a table of `spec-id6, heading-found, prefixed-ids-count`. It must show exactly 8 specs with a nonzero count and must show 0 for each of `2lcqno`, `r07vma`, `z7nbn1`, `kw5y2s` (bare-digit acceptance sections) and for `25kzda`, `77tr3o` (no acceptance heading). Paste ALSO the parsed id list for `uonrjg` (25 ids including `A12b`, `A12c`, `A12d`) and for `2vev8j` (11 ids, `AC-1` through `AC-11`), proving all three row shapes and the numbered/qualified headings are matched. A run that reports only a total without the per-spec breakdown does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the uncovered count for `uonrjg` at HEAD under BOTH search spaces: `valid_leaves`-only (must be 6: `A12b A12c A12d A15 A16 A20`) and the chosen `V + Required tests` space (must be 0). Then paste the two literal lines from plan `bn026f`'s `## Required tests / validation` section that name `A15` and `A16`, proving the added section is where the coverage genuinely lives and that the 6 were false. Paste a token-boundary check showing a search for `A1` does NOT match the text `A15` and a search for `A-0` does NOT match `A-01`. Paste a fence case: a plan whose only mention of a criterion id is inside a triple-backtick fence yields that criterion UNCOVERED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the per-spec decision table for the whole corpus at HEAD with columns `spec, criteria, matched, reported, decision`, showing `6m4kow` (11 criteria, 0 matched) and `2vev8j` (11 criteria, 0 matched) as GATED and contributing 0, `uonrjg` and `7ckptx` as fully covered, and a REPORTED FINDINGS TOTAL of 0. Paste ALSO the same table with the gate DISABLED, showing the total rising to 22, so the gate's effect is measured rather than asserted. Paste the evidence that those 22 are namespace mismatches and not gaps: the `6m4kow` criterion line `- **A-01** (R-06)` beside a count of `R-*` id occurrences in each of its 5 linked plans (nonzero), and the `2vev8j` `| AC-1 | C1 |` table row beside its plan's `C<n>` count.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the output of `check_engine.rule_spec("check.spec-criteria-uncovered")` showing severity `info`, assurance `ASSURANCE_REPOSITORY`, determinism `DET_DETERMINISTIC`. Paste a driven demonstration that `artifact_core.drift_exit_code` returns 0 for a list containing only this rule's finding and 1 for a `warning`-severity one, proving `info` was required rather than preferred. Paste a fixture with 7 uncovered criteria showing exactly ONE `Drift`, its `detail` under 60 characters, at most five ids named plus `(and N more)`, its location the SPEC path, and its `recovery` text naming a child plan rather than the Order-0 parent. Paste a grep proving the rule id contains neither `graduation` nor `duplicate`, and the result of `tests/test_graduation_view.py::NoUniquenessRuleTests`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: With a temporary fixture that FIRES, paste the finding appearing in BOTH `aw check plans` and `aw check all` output, proving both surfaces reach the rule. Then remove the fixture and paste `aw check plans` and `aw check all` on the real tree with their exit codes, both 0. Paste a demonstration that the rule's own `try/except` isolates it: force the predicate to raise and show `aw check plans` still reports its OTHER plans-seam findings and does not abort. Paste a grep of `tests.yml` proving no CI step was added, and a grep of `ipd_lint.py` proving no checkpoint consumes this rule id.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the actual bare `python3 -m pytest` output including the `N passed` summary line. Paste the new test file's own run listing every test name, and confirm by name that the positive control, the negative control, the sentinel case, the bare-digit case, the fence case, the namespace-gate case and the counterfactual pin are all present and passing. For the counterfactual pin, paste the asserted uncovered set and confirm it equals `{A1, A4, A6, A19, A21}`; then paste a MUTATION check, narrowing the search space back to `valid_leaves`-only and showing the pin FAILS, then restoring it and showing it passes, so the test is proven load-bearing rather than vacuous. Paste the invariant-catalog diff and the CHANGELOG diff, and confirm the CHANGELOG line contains no em or en dash. Paste `aw ipd lint --phase pre-transition` on this plan and `aw sanitize --agent`, both clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution; it must NOT be executed from this authoring turn. The executor must hold to the repository execution contract: commit ONLY the paths in `Scope-Paths` via `aw commit <plan> -- <paths>`, never `git add -A` or `-a`, never push, never create a tag or release, and paste ACTUAL runner output rather than claiming a pass. Because `Scope-Paths` declares a `.spec.md` edit, both runners will announce that declared spec edit before the run and reconcile it at finalize; the reason for the amendment is recorded in the spec-sync section above. After validation, the terminal transition is the tooled one (`aw ipd finalize`), which performs the move to `.aw/records/plans/executed/`; do not hand-edit the status or move the file.
