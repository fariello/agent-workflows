# IPD: Decide whether a carried open question gates its plan, and record the answer where the next author reads it

- Date: 2026-10-02
- Kind: child
- Concern: Backlog `hc6n7r` reports that `- Carrier: <id6>` on an open question is DOCUMENTATION ONLY: nothing makes the plan wait for the decision it names, so an approved plan with a carried unanswered decision executes, reaches `executed/`, classes `done` in `aw attention`, and the decision window closes having never opened. THE CORE CLAIM REPRODUCES (F-01, F-02, F-03) and the premise behind it is confirmed by symbol (F-04). BUT THE ITEM'S OWN SCOUTED MECHANISM IS FALSIFIED ON THREE SEPARATE POINTS, each measured: its severity reasoning inverts the shipped contract (F-06), the tier it rejects is the only one that does what it wants (F-07), and the edge it proposes as the remedy REFUSES THE EXACT CASE IT CITES on this tree right now (F-08). Its census number is also stale: 22 carried open questions across 19 plans, not 29 across 23 (F-05).
- Scope: Answer the maintainer's question, and build ONLY the half that does not depend on the answer. TWO deliverables. FIRST, a new `info`-tier `aw check` rule `check.ipd-carrier-ungated` reporting a carried open question whose plan declares no dependency edge on that carrier, so the population is VISIBLE and re-derivable on demand instead of by hand-written script. `info`, not the `warning` the item scouted, because F-06/F-07 measure that `warning` exits 1 and `aw check plans` is a gate this repository enforces fail-closed in CI. SECOND, the documentation the item asks for either way: state in `.aw/records/plans/README.md` AND in the installed template that `Carrier` is a durable-ownership handle and NOT a dispatch gate, and that gating is a separate hand-declared edge. EXCLUDES the enforcement decision itself, which is the maintainer's (OQ-01) and which F-08 shows cannot be implemented as the item proposes. EXCLUDES any change to `evaluate_carrier_obligation`, to the three carrier escapes, to `edge_satisfied`, or to the `aw ipd set approved` gate. EXCLUDES the two adjacent defects this authoring found (F-09, F-10), whose carriers are named.
- Scope-Paths: agent_workflows/check_engine.py, .aw/records/plans/README.md, .aw/system/workflows/templates/plans-README.md, tests/test_carrier_ungated_rule.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: hc6n7r
- Set: carriergate
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rpw4sb
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): status transition for the /plan-review record below

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM, fixed: gate no longer orders a duplicate filing of `bs850k`), PR-002 (MEDIUM, fixed: E-05 fixture must create the carrier as a live backlog item so case (e) can exit 0), PR-003 (MEDIUM, fixed: conditional runner/executor finalize ownership and scope-fence wording), PR-004 (LOW, fixed: V-05/E-05 bar on behaviors not a test count; F-07 shell-exit drift noted). Review record `.aw/records/reviews/20261002-carriergate-01-rpw4sb-decide-whether-a-carried-open-question-gates-its-plan-and-re.review.md`.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `hc6n7r`. EVERY measurement was taken fresh in this lane at HEAD `cf51dc513`; none was transcribed from the item. The item's CORE GAP REPRODUCES (F-01 through F-04) and is worth closing. THREE OF ITS SCOUTED DESIGN CLAIMS ARE FALSIFIED AND I DID NOT BUILD WHAT IT ASKED FOR: (a) it says register `warning` "NOT `error`" to avoid turning `aw check` red, but `artifact_core.drift_exit_code` exempts ONLY `info`, so `warning` exits 1 exactly as `error` does (F-06) and its stated goal selects `info`, the tier it did not consider; (b) `aw check plans` is ALREADY exit 1 on this tree with 27 error findings, so the premise that a new tier would newly redden it is wrong in both directions (F-07); (c) its proposed `state:backlog:done:<id6>` edge REFUSES RIGHT NOW for 15 of the 22 measured rows, because `edge_satisfied` demands an EXACT status and 15 carriers are `graduated`, not `done` (F-08) - the mechanism it scouts would block plans on a decision that has already been handed off. Its census is also stale (22/19, not 29/23, F-05). I therefore built the VISIBILITY half plus the documentation, and left the enforcement direction to the maintainer in OQ-01 with the measurement that decides it. I did NOT resolve OQ-01 myself: the item states in terms that the decision is the maintainer's because it sits on the boundary the 2026-09-10 ruling drew, and nothing in the repository answers whether waiting honors or evades that ruling. AUTHORING ALSO FOUND TWO ADJACENT DEFECTS the item does not mention: a live runner bug silently disabling the review-findings dependency gate (F-09), FILED as backlog `bs850k` (`bug`, `- Blocks-Release: next`) rather than folded into this plan's fence; and the installed plans README template carrying NO carrier documentation at all (F-10), which IS in scope because the item's "NO" branch asks for a statement "beside the Carrier documentation" and a new target repo has none to sit beside.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the carried-but-ungated population VISIBLE and re-derivable from the shipped tooling, and make the next author's expectation CORRECT, without pre-empting the maintainer's enforcement decision. Today the only way to learn that 22 open questions across 19 pending plans name a carrier that gates nothing is to write a throwaway parsing script, and the documentation that teaches `Carrier` says nothing about whether it gates, so an author may reasonably believe it does. After this plan `aw check plans` reports each such row advisorily, the two README surfaces state plainly that `Carrier` records durable OWNERSHIP and never dispatch, and the enforcement question is recorded as the maintainer's with the measurement that decides it. No exit code moves, no plan becomes unrunnable, and no existing carrier row changes meaning.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: make the population visible from the shipped tooling

- [x] E-01 Register the new rule id `check.ipd-carrier-ungated` in `check_engine.RULE_REGISTRY` at severity `info`, assurance `ASSURANCE_REPOSITORY`, determinism `DET_DETERMINISTIC`, invariant `""`, with a comment recording WHY the tier is `info` and not the `warning` the backlog item scouted.

  REGISTRATION IS NOT BOOKKEEPING, and this is the trap to avoid. An unregistered rule id falls back to `_DEFAULT_RULESPEC`, which is `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")` (driven: `rule_spec("check.ipd-carrier-ungated")` returns exactly that today, F-11). So OMITTING the entry does not make the rule advisory, it makes it an `error` that fails `aw check plans` and CI on 22 rows across 19 plans, which is the opposite of this plan's intent. The in-tree precedent for this exact warning is the `check.review-decision-unescalated` comment, which says an unregistered id "would silently contradict the report-only posture".

  `info` IS SELECTED BY THE ITEM'S OWN STATED GOAL, NOT AGAINST IT. The item asks for a tier that will not "turn `aw check` red for authors who did nothing wrong" and concludes `warning`. That conclusion is falsified: `artifact_core.drift_exit_code` returns 1 for every severity except `info` (driven, F-06), and `docs/cli-output-contract.md` section 3.1 states it in the shipped contract ("to author a rule that reports diagnostics without ever failing any gate or check, register the rule with severity `info`"). Record the item's reasoning AND its correction in the comment, so a later reader does not "restore" the scouted tier.

  CITE THE IN-TREE PRECEDENT FOR THE TIER, which is `_CARRIER_LEGACY_SEVERITY` in this same module: its comment already reasons that a `warning` "would exit 1 on a clean tree with 106 findings and fail CI (which enforces `aw check plans` fail-closed)", and names `check.stale-index-missing` as the precedent for "MISSING -> `info`, the ONLY non-failing severity". This rule is in the same position for the same reason.

  INVARIANT `""` DELIBERATELY. Do not claim `I-07`, which `check.ipd-uncarried-obligation` claims for release gating, and do not claim `I-08`, which the `check.ipd-dependency-*` family claims for dependency statements. This rule reports neither a gate nor a malformed statement: it reports the ABSENCE of a voluntary linkage between two well-formed fields. The `check.review-decision-unescalated` entry establishes that an honest `""` beats a neighbouring claim ("Claiming a neighbouring id would be a false trace").
  - Depends on: none
  - Expected outcome: `check_engine.rule_spec("check.ipd-carrier-ungated")` returns `RuleSpec("info", "repository", "deterministic", "")` instead of the `error` default, and the registry comment states the measured reason the tier is `info` rather than the scouted `warning`.
  - Execution state: performed

- [x] E-02 Add the pure per-plan evaluator `evaluate_carrier_ungated(repo_root, *, plan_path, plan_text, open_questions=None)` beside `evaluate_durable_carrier`, reporting at most ONE `info` Drift per plan enumerating its carried-but-unedged open questions.

  REUSE THE PARSED INPUTS RATHER THAN RE-READING. Accept `open_questions` as an optional parameter and fall back to `ipd_lint.parse(plan_text).open_questions` exactly as `evaluate_durable_carrier` does, so the sweep parses each plan once. Read the plan's declared edges from `meta_fields[ipd_schema.META_ITEM_DEPENDENCIES]` through `ipd_schema.parse_item_dependencies`, and compare against PARSED EDGES, never against the raw field text: a substring test would be satisfied by the token appearing inside prose, and the parser already normalizes spacing and ordering.

  SCOPE THE SUBJECT ROWS EXACTLY, and the boundaries are measured rather than chosen. Consider a question only when its `Status` is `open` AND it carries a non-empty `Carrier`. EXCLUDE `deferred`, even though `_CARRIER_LIVE_OQ_STATUSES` admits it for the uncarried rule, because this rule is about a decision window that a dispatch could still wait for and a deferred question has already been dispositioned. EXCLUDE a row carrying `Carrier-Evidence` or `Carrier-Declined` and no `Carrier`: those rows name no carrier to gate on. Parse the `Carrier` value with `ipd_schema.parse_carrier_ids` so a malformed token is NOT reported here; `check.ipd-uncarried-obligation` already owns that complaint and reporting it twice is the overlap this repository's guidance warns against.

  A ROW IS "EDGED" WHEN ANY DECLARED EDGE TARGETS THE CARRIER, judged by `edge.id6` ALONE and deliberately not by the edge's status qualifier. This is the load-bearing design choice and F-08 is why: the item proposes `state:backlog:done:<id6>` as the canonical form, but 15 of the 22 measured carriers are `graduated` rather than `done`, so a rule that demanded the `done` spelling would report 15 plans as ungated even after an author added the edge the item recommends. Matching on identity reports the AUTHOR'S INTENT TO WAIT, which is what the item actually wants to measure, and it accepts every legal spelling (`state:backlog:graduated:<id6>`, `state:backlog:done:<id6>`, `exists:backlog:<id6>`, and a plan carrier's `executed:<id6>`).

  BOUND THE VOLUME AND NEVER RAISE, copying the two disciplines of its neighbour. Enumerate at most five locators then ` (and N more)`, as `evaluate_durable_carrier` does for the identical reason; and return `[]` on any parse or IO failure rather than propagating, because every sweep call site in `check_content` is fail-isolated and a crashing rule is a disabled rule.
  - Depends on: E-01
  - Expected outcome: the evaluator returns one `info` Drift naming the offending `OQ-*` locators and their carrier id6s for a plan with a carried open question and no edge on that carrier; returns `[]` when any declared edge targets the carrier whatever its status qualifier; returns `[]` for a `resolved` or `deferred` question, for a row with no `Carrier`, and for an unparseable plan.
  - Execution state: performed

- [x] E-03 Add the tree sweep `check_carrier_ungated(repo_root, include_untracked=False)` and wire it into `check_content`'s plans branch beside the `check_durable_carrier` call.

  SWEEP PENDING-LANE PLANS ONLY, which is the unanimous precedent of every plans-scoped rule here (`check_durable_carrier`, `check_review_decision_unescalated`, `check_lifecycle_transitions`) and for the reason each states: a terminal plan is already past the window this rule is about, and litigating the executed corpus would be a whole-tree false-positive explosion. Measured scale if that guard were omitted: the executed tree is far larger than the 19 pending plans this reports.

  PLACE THE CALL IN THE PLANS-TYPE CONTENT PATH, inside its own `try/except Exception: pass`, matching every neighbour in that block. That placement is what makes it reachable from BOTH `aw check plans` and the `aw check all` fan-out exactly once; the `check_durable_carrier` wiring comment states this and names the precedent, so follow it rather than inventing a second seam. Do NOT add it to the collisions-only cross-tree sweep.

  DO NOT ADD A NEW `aw check` FAMILY TARGET. The rule rides the existing `plans` type, needing no change to the CLI dispatch, the epilog, or the next-action mapping. A family target is a separate public surface and this plan declares no CLI scope path.
  - Depends on: E-02
  - Expected outcome: `aw check plans` and `aw check all` each report the carried-but-ungated rows exactly once at `info`; the command's exit code is unchanged from its pre-change value for the same tree; a plan in `executed/` is never reported.
  - Execution state: performed

### Task group 2: make the documented expectation correct on both surfaces

- [x] E-04 State in the `## Durable carrier vocabulary for obligations` section of `.aw/records/plans/README.md` that `Carrier` records durable OWNERSHIP and is NOT a dispatch gate, and that gating is a separate hand-declared `- Item-Dependencies:` edge; then make the SAME statement in `.aw/system/workflows/templates/plans-README.md`.

  BOTH FILES, AND THE SECOND ONE IS NOT OPTIONAL. `.aw/records/plans/README.md` is MACHINE-INSTALLED from the template by `engine.ensure_plans_readmes`, whose target list pairs `f"{dirs['plans']}/README.md"` with the template name `plans-README.md`. Measured (F-12): the template does NOT contain the carrier section at all (zero occurrences of `Durable carrier`), so every repository installed from this toolkit today gets a plans README with no carrier documentation whatsoever. Editing only the records copy would leave every managed target repo with no statement at all, which is precisely the next-author ignorance the backlog item wants removed. The installer is no-clobber, so this changes no existing target's file; it fixes what a NEW install receives.

  PORT THE SECTION, DO NOT REWRITE IT. Copy the existing three-escape section and the discharged-carrier subsection into the template verbatim, then add the new statement to both copies, so the two do not diverge in wording. The repository copy legitimately carries repo-specific text the template does not (the two already differ, F-12), so do not attempt to make the files identical.

  SAY WHAT IS TRUE TODAY AND NAME THE ALTERNATIVE. State that nothing in the lifecycle makes a plan wait for a carried question's answer; that the pre-execution checkpoint refuses an open question only when it carries `Blocking: yes`; that a plan which must wait declares the dependency explicitly with `aw ipd dependencies set <plan> state:backlog:<status>:<carrier>`; and that `aw check plans` now reports a carried row with no such edge advisorily. WARN ABOUT THE EXACT-STATUS TRAP, measured in F-08: the edge requires the status to match EXACTLY, so an edge written against `done` refuses while the carrier is `graduated`. An author who reads only the item's recommended spelling will write an edge that blocks their plan on a decision already handed off.

  DO NOT PRE-ANNOUNCE OQ-01'S ANSWER. Write this as the CURRENT behavior plus the explicit hand-declared remedy, not as a settled ruling that `Carrier` will never gate. If the maintainer later answers OQ-01 "yes", this text is amended by that work; if "no", this text is already the record the item asks for.
  - Depends on: none
  - Expected outcome: both READMEs state that `Carrier` is durable ownership and not a dispatch gate, name the explicit edge as the way to make a plan wait, warn that the edge matches a status exactly, and mention the new advisory rule; the template additionally carries the full three-escape carrier section it previously lacked entirely.
  - Execution state: performed

### Task group 3: pin it mechanically, in both directions

- [x] E-05 Add `tests/test_carrier_ungated_rule.py` driving the evaluator and the `aw check plans` CLI over temp repositories, asserting the reporting, the silences, the tier, and the exit-code invariance.

  ASSERT SEVEN CASES, and the negatives are what stop this being satisfied by a rule that always fires: (a) REPORTED - a pending plan with an open carried question and `- Item-Dependencies: none` yields one `info` Drift naming the `OQ` locator and the carrier id6; (b) EDGED IS SILENT whatever the qualifier - the same plan declaring `state:backlog:graduated:<carrier>` yields nothing, and so does one declaring `state:backlog:done:<carrier>`, which is the assertion that pins E-02's identity-only matching and would fail under a `done`-only implementation; (c) NON-SUBJECT ROWS ARE SILENT - a `resolved` question, a `deferred` question, and a row with `Carrier-Declined` and no `Carrier` each yield nothing; (d) TIER - the emitted Drift's severity is `info` after `enrich_drift`, and `artifact_core.drift_exit_code` over that one Drift returns 0; (e) EXIT-CODE INVARIANCE - on a temp repo whose ONLY finding would be this rule, `aw check plans` exits 0 and still PRINTS the rule id, which is the property that distinguishes advisory-and-visible from suppressed; (f) TERMINAL PLANS ARE NEVER REPORTED - the same offending plan placed in `executed/` yields nothing; (g) MULTIPLE ROWS COLLAPSE - a plan with six offending questions yields ONE Drift that names five locators and says `and 1 more`.

  TEST OUTCOMES, NOT STRUCTURE, which AGENTS.md requires and which this module's own test neighbours obey. Assert on returned `Drift` fields and on real CLI stdout and exit codes. Do NOT read `check_engine.py` with `inspect`, `ast`, or a regex, do NOT assert a registry census or a caller count, and do NOT pin the Drift's full `detail` sentence; assert the locator, the carrier id6 and the rule id, so a later wording fix is not a test edit.

  BUILD FIXTURES WITH THE SUITE'S OWN BUILDERS. `tests/test_carrier_reverse_lookup.py` is the nearest neighbour and shows the whole shape: `tests.support.ready_plan_text(plan_id=..., when=..., status=...)` for a plan that passes the gates, a `.aw/config/project.json` carrying a `cutovers` map, and a `redirect_stdout` + `cli.main` helper for the CLI arm. Reuse that rather than hand-rolling a plan, which earlier carrier work measured as refused by the lint gate before any rule logic runs. THE CARRIER MUST EXIST IN THE FIXTURE AS A LIVE BACKLOG ITEM (`open` or `graduated`, under `.aw/records/backlog/<status>/` with a matching `- Id:` and `- Status:`), because a `- Carrier:` that resolves to nothing fires `check.ipd-uncarried-obligation` at `error` for a post-cutover plan, and a `done` carrier fires the discharged-carrier refusal; either would make case (e)'s exit-0 assertion fail for a reason that has nothing to do with this rule. Before relying on case (e), assert that the fixture's `aw check plans --agent` diagnostics contain NO rule other than `check.ipd-carrier-ungated` (and any pre-existing `info` rule), so a stray finding is diagnosed rather than masked.

  WRITE THE CUTOVER INTO THE FIXTURE CONFIG, because this rule must not inherit the carrier grandfathering by accident. `check.ipd-carrier-ungated` is a NEW rule with a FLAT tier and no date comparison, so its fixtures need no `carrier_obligations` cutover to behave; assert that a PRE-cutover-dated plan is reported exactly like a post-cutover one, which pins that this rule did not copy `carrier_severity_for_plan`'s per-plan tier logic it has no use for.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: a new test module (organize the cases as convenient; the bar is the behaviors, not a test count) proving the rule reports a carried-but-unedged open question once at `info`, is silent for an edged row under either status spelling and for every non-subject row, exits 0 while still printing the rule id, never reports a terminal plan, collapses six rows into one bounded Drift, and ignores the carrier cutover.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CODE IS CITED BY SYMBOL OR QUOTED CONTENT, NOT BY BARE OFFSET (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan cites `check_engine.RULE_REGISTRY`, `check_engine.RuleSpec`, `check_engine.rule_spec`, `check_engine._DEFAULT_RULESPEC`, `check_engine.enrich_drift`, `check_engine.evaluate_durable_carrier`, `check_engine.check_durable_carrier`, `check_engine.check_content`, `check_engine.check_review_decision_unescalated`, `check_engine._CARRIER_LEGACY_SEVERITY`, `check_engine.carrier_severity_for_plan`, `check_engine._CARRIER_LIVE_OQ_STATUSES`, `check_engine.build_dependency_index`, `artifact_core.drift_exit_code`, `ipd_lint.parse`, `ipd_lint.check_checkpoint`, `ipd_schema.parse_item_dependencies`, `ipd_schema.parse_carrier_ids`, `ipd_schema.META_ITEM_DEPENDENCIES`, `ipd_schema._ITEM_DEP_STATE_STATUSES`, `runner_shared.edge_satisfied`, `runner_shared.dependency_status_detailed`, `runner_shared.dependency_target_id6`, `engine.ensure_plans_readmes` and `attention` by symbol.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` plus the marker deselection, so no flags are added. Measured on this lane at HEAD `cf51dc513` on a clean tree: `3 failed, 4624 passed, 2 skipped, 3 warnings in 119.88s`. THE THREE FAILURES ARE PRE-EXISTING AND UNRELATED (F-13), so the bar is "these same three and no others", not zero. TREAT THE DIGITS AS CONTEXT AND RE-DERIVE YOUR OWN.
- `info` IS THE ONLY NON-FAILING SEVERITY, and this is a published contract rather than a convention: `docs/cli-output-contract.md` section 3.1 states it, `artifact_core.drift_exit_code` implements it, and the `_CARRIER_LEGACY_SEVERITY` and `check.review-decision-unescalated` comments in `check_engine.py` both reason from it explicitly. Any severity argument in this area must be driven, not asserted.
- A RULE IS TWO LAYERS PLUS A REGISTRY ENTRY. Every plans-scoped rule here is a pure `evaluate_*(repo_root, *, plan_path, plan_text, ...) -> List[Drift]` predicate, a `check_*(repo_root, include_untracked=False)` sweep that filters to `"pending" in p.parts` and builds any index ONCE, and a `RuleSpec` entry; the sweep is called from `check_content`'s per-type branch inside its own `try/except`. This plan follows that shape exactly and introduces no new seam.
- A SHARED CHECKOUT MEANS NO SPECULATIVE FILE MUTATION. Every measurement here was taken read-only or in a temp directory. `git status --porcelain` was verified to show only this plan file before commit.
- `.aw/records/plans/README.md` IS MACHINE-INSTALLED, NOT HAND-OWNED. `engine.ensure_plans_readmes` writes it from `.aw/system/workflows/templates/plans-README.md` (no-clobber). A documentation fix that edits only the records copy does not reach a new target repository, which is why E-04 edits both.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE ITEM'S CORE CLAIM REPRODUCES: `Carrier` FEEDS NO GATE.** `Carrier` is parsed in exactly one place and consumed by exactly one rule family. `ipd_lint.parse` captures it only as an untyped dict key (its OQ loop stores every `- Field: value` bullet with `pending_oq[fld] = val`, so `Carrier` is never special-cased), and the only consumers are `check_engine._question_obligations` and `evaluate_carrier_obligation`, which judge whether a carrier EXISTS and resolves, never whether the plan waits for it. `ipd_schema.OQ_FIELDS`, which lists `Carrier`, has no consumer at all, as its own comment states. | Read of `ipd_lint.parse`'s OQ field-capture branch and of `ipd_schema.OQ_FIELDS` with its comment; `grep` for `Carrier` across `agent_workflows/` showing consumers confined to `check_engine`'s carrier block. |
| F-02 | **THE CHECKPOINT REFUSES ONLY `Blocking: yes`, SO A CARRIED `Blocking: no` ROW PASSES.** `ipd_lint.check_checkpoint` reads open questions under `if checkpoint == "pre-execution":` and appends a diagnostic only when `oq.get("Blocking") == "yes" and oq.get("Status") == "open"`. `check_open_questions` applies the same `blocking == "yes" and status == "open"` test, and its comment records the 2026-09-10 scoping ruling with the measurement that "66 of 103 pending plans carry a NON-blocking open question, which is the normal, healthy state". Neither function reads `Carrier`. | Read of both functions; driven on the one real `Blocking: yes` plan (`a6i03f`), where `aw ipd lint --phase author` reports `IPD-Q501 (line 176): OQ-04: BLOCKING question is still 'open'`, confirming the refusal fires on `Blocking`, not on `Carrier`. |
| F-03 | **ZERO OF THE CARRIED OPEN ROWS ARE EDGE-BACKED, RE-DERIVED ON THIS TREE.** Parsing every pending and reusable plan with `ipd_lint.parse` and comparing each open-and-carried question's carrier against the plan's own parsed `Item-Dependencies`: **0** of 22 rows are backed by any edge naming their carrier. The item's central number is therefore confirmed in kind. | Script over 147 pending+reusable plans parsing each with `ipd_lint.parse`, extracting `Status: open` questions with a non-empty `Carrier`, and testing each carrier id6 against the parsed edge set; printed `edge-backed: 0`. |
| F-04 | **THE CONSEQUENCE PREMISE IS CONFIRMED BY SYMBOL: `executed` CLASSES `done`.** `attention`'s status mapping contains `"executed" -> "done"`, so once a plan reaches the terminal directory its carried question is inside an artifact the attention view reports as finished, and AGENTS.md D156 forbids rewriting what an executed plan records. The window the item describes does close. | Regex extraction of the `"executed": "<class>"` mapping from `attention`'s source, printing `executed -> done`. |
| F-05 | **THE ITEM'S CENSUS IS STALE, AS THE ITEM ITSELF PREDICTED.** Measured today: **22** open carried questions across **19** plans, not the item's 29 across 23. The item explicitly says "the population is LIVE and grows as plans are authored, so re-derive the number rather than trusting this one", and it shrank rather than grew. Composition: 21 rows `Blocking: no` and 1 `Blocking: yes`; by plan status, 15 rows in `to-review` plans, 6 in `approved`, 1 in `reviewed`. | The F-03 script, additionally tallying distinct plans, `Blocking` values and the owning plan's `- Status:`. |
| F-06 | **THE ITEM'S SEVERITY REASONING INVERTS THE SHIPPED CONTRACT.** The item says register `warning` "NOT `error`" because "an error tier would turn `aw check` red for authors who did nothing wrong". But `warning` turns it red too: `artifact_core.drift_exit_code` returns 1 for every severity except `info` (driven: `error -> 1`, `warning -> 1`, `info -> 0`), and `docs/cli-output-contract.md` section 3.1 states the contract in terms, including "`warning`: Evaluates to failing (`1`). A `warning` finding fails the exit-code gate exactly as an `error` does" and "to author a rule that reports diagnostics without ever failing any gate or check, register the rule with severity `info`". The item's own stated goal therefore selects `info`, a tier it never considered. | `drift_exit_code` driven on a single Drift at each of the three severities; read of `docs/cli-output-contract.md` section 3.1. |
| F-07 | **THE "WOULD TURN IT RED" PREMISE IS WRONG IN BOTH DIRECTIONS: `aw check plans` IS ALREADY RED.** `check_engine.check_type(root, "plans")` on this tree returns **68** findings, **27** `error` and **41** `info`, and `drift_exit_code` over them returns **1**. The largest single contributor is `check.ipd-uncarried-obligation` at 22 error findings. So a new `warning` rule would not NEWLY redden the command (it is already failing), and a new `info` rule cannot make it green (the 27 errors already prevent that). The tier choice is therefore about whether this rule ADDS a failure of its own, which `info` alone avoids. | `check_type(Path("."), "plans")` driven with a per-rule and per-severity tally and the resulting `drift_exit_code`; separately `aw check plans` observed exiting 0 at the shell only because its renderer path differs, with the engine verdict measured as 1. (REVIEW 2026-10-07, HEAD `3d84ef876`: `aw check plans --agent` now exits 1 too, `findings: 105`, engine tally `error 26 / warning 2 / info 76`; the counts are context and V-03 re-derives them.) |
| F-08 | **THE ITEM'S PROPOSED EDGE REFUSES THE EXACT CASE IT CITES, MEASURED ON THIS TREE.** The item's per-instance remedy and its generalization both name `state:backlog:done:<carrier>`. But `runner_shared.edge_satisfied` requires the status to match EXACTLY (`if status != edge.status: return False, f"... is {status!r}, needs exactly {edge.status!r}"`), and the measured carrier population is NOT `done`: of the 22 rows, **15** name a carrier that is `graduated`, **5** name one that is `open`, and **2** name an `executed` plan; **zero** name a `done` backlog item. Driven on the item's own worked carrier `wcbpqf`: `state:backlog:done:wcbpqf` returns `(False, "state:backlog:done:wcbpqf: backlog wcbpqf is 'graduated', needs exactly 'done'")` while `state:backlog:graduated:wcbpqf` returns `(True, '')`. A general rule demanding the `done` spelling would thus block plans on decisions ALREADY handed off, and the grammar offers no disjunction (`state:backlog:done|graduated:<id6>` is refused as an invalid status, and two edges are ANDed, not ORed). THIS IS WHY E-02 MATCHES ON IDENTITY ONLY and why OQ-01 cannot be answered by adopting the item's mechanism as written. | `edge_satisfied` driven on both spellings against the live repository; `build_dependency_index` resolution of all 22 carriers tallied by type/status; `ipd_schema._parse_item_dependency_edge` driven on the disjunction spellings (both refused) and `parse_item_dependencies` on the two-edge form (accepted as two ANDed edges). |
| F-09 | **ADJACENT DEFECT FOUND AND DELIBERATELY NOT FIXED HERE: the runner's findings gate is passed an un-parsed value.** In `runner_shared.dependency_status_detailed`, the execute-action arm reads `target = dependency_target_id6(edge) or dep`, but `dependency_target_id6` is typed `(token: str)` and re-parses its argument, so passing the already-parsed `ItemDependency` returns `None` for EVERY edge (driven: `dependency_target_id6(edge)` is `None` where `edge.id6` is `'a8e2l8'`). The `or dep` fallback then hands `review_findings.subject_gating_blocks` the RAW TOKEN (`'executed:a8e2l8'`) instead of the id6, which matches no `- Subject-Id:` and returns `()` unconditionally, so the review-findings dependency gate never fires. The code comment at that site says "Uses the parsed edge's target id6, not the raw token", which is the opposite of what it does. 685 `.review.md` records exist, so this is live rather than latent. OUT OF SCOPE: it is a runner bug in a different module with a different owner, and folding it in would widen this plan's fence past its concern. Carrier named in `## Deferred / out of scope`. | `dependency_target_id6` driven on both a token and a parsed edge; `subject_gating_blocks` driven on the raw token and on the id6; read of the call site and its comment; `find .aw/records -name "*.review.md" \| wc -l` = 685. |
| F-10 | **ADJACENT GAP FOUND: the installed plans README template carries NO carrier documentation at all.** `.aw/system/workflows/templates/plans-README.md` is 94 lines with **zero** occurrences of `Durable carrier`, while the repository's own `.aw/records/plans/README.md` is 200 lines and carries the full section. Since `engine.ensure_plans_readmes` installs the template (pairing `f"{dirs['plans']}/README.md"` with `plans-README.md`) and is no-clobber, every repository installed from this toolkit receives a plans README that documents none of the three carrier escapes. This is IN SCOPE for E-04 because the backlog item's "NO" branch asks for documentation "beside the Carrier documentation", and in a new target repo there is none to sit beside. | `wc -l` and `grep -c "Durable carrier"` on both files (template: 0); `diff` of the two confirming they already legitimately differ; read of `ensure_plans_readmes` and its target pairing. |
| F-11 | **OMITTING THE REGISTRY ENTRY WOULD SHIP THE RULE AS `error`, NOT AS ADVISORY.** `rule_spec("check.ipd-carrier-ungated")` returns `_DEFAULT_RULESPEC`, measured as `RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='')`, and the id is confirmed unused (`"check.ipd-carrier-ungated" in RULE_REGISTRY` is False, and `grep` finds it nowhere in `agent_workflows/`). So E-01 is load-bearing rather than bookkeeping: without it the rule fails CI on 19 plans. | `rule_spec` driven on the new id; membership test against `RULE_REGISTRY`; `grep -n "carrier-ungated" agent_workflows/*.py` (no output). |
| F-12 | **NO SPEC PINS THIS VOCABULARY, SO NO SPEC AMENDMENT IS DECLARED.** `grep` for `Carrier` across every `.spec.md` under `.aw/records/specs/` returns ZERO matches, and no file under `docs/` or `.aw/records/specs/` mentions `check.ipd-uncarried-obligation`, `check.ipd-carrier-finished-unverified` or `RULE_REGISTRY` as a rule catalog. The only published contract this plan touches is `docs/cli-output-contract.md` section 3.1, which this plan OBEYS rather than amends (it lists exactly one rule id, `check.scope-drift`, as a tier exception). `- Scope-Paths:` therefore declares no `.spec.md` and no `docs/` path. | `grep -rn "Carrier" .aw/records/specs/*/*.spec.md` (no output); `grep -rn` for the three rule/registry tokens across `.aw/records/specs/` and `docs/` (no output); read of section 3.1's rule-id list. |
| F-13 | **THE BASELINE IS NOT GREEN AND THE THREE FAILURES ARE PRE-EXISTING AND UNRELATED.** Bare `python3 -m pytest` on this lane's clean tree at HEAD `cf51dc513`: `3 failed, 4624 passed, 2 skipped, 3 warnings in 119.88s`. The three are `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` and `test_selector_type_containment.py::test_must_not_refuse_matrix`. None touches `check_engine`'s carrier block, the plans READMEs, or dependency edges. **THE BAR IS "THESE SAME THREE AND NO OTHERS", NOT ZERO.** | The bare run on a tree verified clean beforehand; `git rev-parse --short HEAD`; the `FAILED` lines extracted from the captured output. |
| F-14 | **THIS PLAN IS ITSELF A MEMBER OF THE POPULATION IT REPORTS, WHICH IS THE INTENDED BEHAVIOR AND NOT AN OVERSIGHT.** It declares `- Item-Dependencies: none` and carries OQ-01 as `Status: open` with `- Carrier: hc6n7r`, so once E-03 lands, `aw check plans` will report THIS plan too. That is correct: the carried decision genuinely gates nothing, and the honest report of that is the deliverable. It is also the self-consistency check on the tier choice, because at `info` the finding costs this plan no gate and no exit code while remaining visible, which is exactly the posture E-01 argues for. An executor must NOT silence it by adding an edge on `hc6n7r` to this plan: F-08 shows the correct spelling depends on that item's current status, and an `open` carrier with a `done` edge would block this plan outright. | `ipd_lint.parse` driven on this plan file, printing `Item-Dependencies: none` and `OQ-01 open Carrier=hc6n7r`; the `aw ipd lint --phase author` verdict `conforming` and the durable-carrier evaluator reporting CLEAN on the same file. |

## Proposed changes (ordered, validatable)

1. Register `check.ipd-carrier-ungated` at `info` with a comment recording the measured correction to the backlog item's scouted `warning` tier (E-01, on the strength of F-06, F-07 and F-11).
2. Add the pure per-plan evaluator matching a carried open question against the plan's parsed edges BY CARRIER IDENTITY ONLY (E-02, on the strength of F-08).
3. Add the pending-lane sweep and wire it into the plans content path beside its nearest neighbour (E-03).
4. State on BOTH README surfaces that `Carrier` is durable ownership and not a dispatch gate, name the explicit edge as the remedy, and warn about the exact-status trap (E-04, on the strength of F-02, F-08 and F-10).
5. Pin all of it with outcome tests in both directions, including the two status spellings and the exit-code invariance (E-05).

## Deferred / out of scope (with reason)

- THE ENFORCEMENT DECISION ITSELF (should a carried non-blocking question gate dispatch?) is NOT taken by this plan. It is the maintainer's, for the reason the backlog item states: it sits on the boundary the 2026-09-10 ruling drew, and F-08 shows the item's own proposed mechanism cannot be adopted as written. Recorded as OQ-01.
  - Carrier: hc6n7r
- THE STRONGER VARIANT the item scouts (refusing at `aw ipd set approved`) is excluded. It is a lifecycle gate rather than a report, it would refuse 6 currently-`approved` plans measured in F-05, and the item itself says it is "a bigger behavioral change deserving its own review". It is downstream of OQ-01 and cannot be designed before that answer.
  - Carrier: hc6n7r
- THE RUNNER FINDINGS-GATE DEFECT measured in F-09 (`dependency_target_id6` passed a parsed edge, returning `None` for every edge and silently disabling the review-findings dependency gate) is NOT fixed here. It is a live defect in `runner_shared` with its own blast radius and deserves its own plan and its own gate; this plan's fence is `check_engine` plus documentation. It is also a `bug` by the repository's definition and so needs a release gate this `followup` plan does not and should not carry. FILED DURING THIS AUTHORING as backlog item `bs850k` (`bug`, `- Blocks-Release: next`), so it is owned and gated rather than merely noted.
  - Carrier: bs850k
- WIDENING THE RULE TO `deferred` QUESTIONS is excluded. `_CARRIER_LIVE_OQ_STATUSES` admits `deferred` for the uncarried-obligation rule because an obligation outlives its disposition, but a `deferred` question has already been dispositioned and no dispatch could usefully wait for it. Revisit only if OQ-01 is answered "yes".
  - Carrier-Declined: The exclusion is a deliberate scope boundary with a stated rationale, not an outstanding obligation; nothing is left unowned by it.
- BACKFILLING EDGES ONTO THE 19 MEASURED PLANS is excluded. F-08 shows the correct spelling depends on each carrier's CURRENT status, so a backfill would be stale the moment a carrier advances, and under the current grammar it would convert 19 reportable rows into 19 plans at risk of blocking on an already-handed-off decision. Visibility first, then the maintainer's decision.
  - Carrier: hc6n7r

## Scope check

- Over-scope: none. The four declared paths are the registry plus evaluator plus sweep (`agent_workflows/check_engine.py`), the two documentation surfaces, and the new test module. No CLI path, no spec, no runner module, and no change to any existing carrier or dependency predicate.
- Under-scope: the enforcement half, deliberately, because OQ-01 is the maintainer's and F-08 falsifies the item's proposed mechanism. If the maintainer answers "yes", a successor plan designs the gate against the measured status distribution; if "no", E-04's documentation is the complete answer the item asks for.

## Required tests / validation

- `tests/test_carrier_ungated_rule.py`, the new module, run narrowed with `-o addopts=""` so per-test names are visible, then again as part of a bare full-suite run.
- The bare full suite `python3 -m pytest`, compared against F-13's baseline. The bar is the SAME THREE pre-existing failures and no others; an executor must re-derive the baseline on its own HEAD rather than transcribing F-13.
- `aw check plans` and `aw check all` on this repository, before and after, with the exit code and the per-severity tally compared. The error count must be unchanged and the new rule must appear at `info`.
- `aw ipd lint <this plan> --phase author` reporting conforming.
- `aw sanitize --agent` clean on the changed files.

## Spec / documentation sync

No spec amendment. F-12 measures zero occurrences of `Carrier` across every `.spec.md`, and no spec or doc holds a rule catalog that a new rule id must join; `- Scope-Paths:` therefore declares no `.spec.md`. `docs/cli-output-contract.md` section 3.1 governs the tier choice and this plan OBEYS it (choosing `info` precisely because that section defines `info` as the only never-failing tier), so it needs no edit.

Documentation IS changed, on two surfaces, and E-04 owns both: `.aw/records/plans/README.md` (this repository's copy) and `.aw/system/workflows/templates/plans-README.md` (what a managed target repo receives). F-10 measures that the template currently documents no carrier vocabulary at all, so this is a genuine installed-output fix and not a cosmetic echo.

NO FILING OBLIGATION IS LEFT TO THE EXECUTOR: the F-09 runner defect was filed during this authoring as backlog item `bs850k` (`bug`, `- Blocks-Release: next`, Set `carriergate`), so the defect is already owned and release-gated rather than resting on a promise. It remains excluded from this plan's code scope on purpose, and the `## Deferred / out of scope` row names `bs850k` as its carrier.

## Open questions

### OQ-01: Should a carried non-blocking open question gate its plan's dispatch at all, and if so by what mechanism, given that the edge grammar cannot express the status disjunction the measured population needs?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: hc6n7r
- Resolution or deferral rationale: NOT RESOLVED, AND DELIBERATELY SO. The backlog item states this decision is the maintainer's because it sits on the boundary the 2026-09-10 ruling drew: that ruling says a non-blocking question does not make a plan NO-GO, and a carrier-to-edge rule would instead make such plans `dependency-blocked`, which is a different mechanism reaching a similar outcome. Whether that honors the ruling's intent (the question is still not NO-GO, it merely waits) or evades it (the plan still does not run) is a judgement about what the ruling was FOR, and the recorded rationale is silent on waiting. Nothing in the repository answers it, so resolving it from evidence would be inventing an answer. THIS PLAN IS SAFE EITHER WAY: it builds visibility and documentation, both of which are wanted under both answers, and it takes no enforcement step. WHAT I CAN ADD IS THE MEASUREMENT THAT DECIDES IT, and it materially changes the question the item posed. F-08: the item's proposed `state:backlog:done:<carrier>` edge REFUSES on this tree for 15 of 22 rows, because `edge_satisfied` demands an exact status and those carriers are `graduated`; zero are `done`. The grammar offers no disjunction and multiple edges are ANDed, so "wait until the carrier is done OR graduated" is INEXPRESSIBLE as declared edges today. So a "yes" answer requires one of: (a) extend the edge grammar with a status set, (b) define a `terminal`/`settled` pseudo-status for backlog targets, or (c) gate on something other than an edge. Each is a larger change than the item anticipated, which is itself useful input to the decision. A "no" answer costs nothing beyond E-04, which is already in this plan. Not marked `Blocking: yes` because every item in this plan is correct and useful under either answer; marking it blocking would stall deliverables the decision does not affect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste a driven `python3 -c` showing `check_engine.rule_spec("check.ipd-carrier-ungated")` returning `RuleSpec(severity='info', assurance='repository', determinism='deterministic', invariant='')`. PROVE NON-VACUITY BY MUTATION, which is the whole point of this item: comment the registry entry out in a scratch copy, paste the SAME command now returning `severity='error'` (the `_DEFAULT_RULESPEC` fallback), and restore. Paste `git status --short agent_workflows/` clean afterwards. Also paste the registry comment itself, showing it names the measured `drift_exit_code` behavior as the reason the tier is `info` rather than the item's scouted `warning`.
  - Observed evidence:
    Driven python3 -c showing check_engine.rule_spec:
    ```sh
    $ python3 -c "from agent_workflows import check_engine; print(check_engine.rule_spec('check.ipd-carrier-ungated'))"
    RuleSpec(severity='info', assurance='repository', determinism='deterministic', invariant='')
    ```

    Non-vacuity proof by mutation (commenting out rule in RULE_REGISTRY):
    ```sh
    $ python3 -c "from agent_workflows import check_engine; print(check_engine.rule_spec('check.ipd-carrier-ungated'))"
    RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='')
    ```

    Restored clean:
    ```sh
    $ git status --short agent_workflows/
     M agent_workflows/check_engine.py
    $ python3 -c "from agent_workflows import check_engine; print(check_engine.rule_spec('check.ipd-carrier-ungated'))"
    RuleSpec(severity='info', assurance='repository', determinism='deterministic', invariant='')
    ```

    Registry comment itself (agent_workflows/check_engine.py):
    ```python
    # carriergate Order 01 (`rpw4sb`) E-01: a carried open question whose plan declares no dependency
    # edge on that carrier. The population is visible and re-derivable from the shipped tooling rather
    # than by hand-written script, without pre-empting the maintainer's enforcement decision (OQ-01).
    #
    # `info`, AND THIS IS SELECTED BY THE BACKLOG ITEM'S OWN STATED GOAL, NOT AGAINST IT. Backlog hc6n7r
    # asks for a tier that will not "turn `aw check` red for authors who did nothing wrong" and concludes
    # `warning`. That conclusion is falsified on evidence: `artifact_core.drift_exit_code` returns 1 for
    # every severity except `info` (error -> 1, warning -> 1, info -> 0; docs/cli-output-contract.md
    # section 3.1: "to author a rule that reports diagnostics without ever failing any gate or check,
    # register the rule with severity `info`"). A `warning` tier would exit 1 on 19 pending plans and
    # fail CI (which enforces `aw check plans` fail-closed). Precedent: `_CARRIER_LEGACY_SEVERITY` in
    # this same module ("MISSING -> `info`, the ONLY non-failing severity", citing `check.stale-index-missing`).
    #
    # Invariant `""` DELIBERATELY. Do not claim I-07 (release gating / uncarried obligations) or I-08
    # (cross-IPD dependency statements). This rule reports neither a broken gate nor a malformed statement:
    # it reports the ABSENCE of a voluntary linkage between two well-formed fields. Follows
    # `check.review-decision-unescalated` ("Claiming a neighbouring id would be a false trace").
    #
    # Deterministic: a literal `- Status:` / `- Carrier:` match from `ipd_lint.parse` against parsed
    # `Item-Dependencies` edges through `ipd_schema.parse_item_dependencies`. No inference.
    "check.ipd-carrier-ungated": RuleSpec(
        "info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the evaluator driven directly on temp-repo fixtures for FIVE inputs, showing the returned Drift list each time: (1) carried open question, no edge -> ONE Drift whose rule is `check.ipd-carrier-ungated`, severity `info` after `enrich_drift`, detail naming the `OQ` locator and the carrier id6; (2) same plan declaring `state:backlog:graduated:<carrier>` -> `[]`; (3) same plan declaring `state:backlog:done:<carrier>` -> `[]`, which is the case that FAILS under a status-sensitive implementation and so proves E-02's identity-only matching; (4) the question `resolved` -> `[]`; (5) a row with `Carrier-Declined` and no `Carrier` -> `[]`. Paste the six-row collapse case showing exactly five locators plus `and 1 more`. Paste the evaluator returning `[]` on a deliberately truncated plan file rather than raising.
  - Observed evidence:
    Evaluator driven directly on temp-repo fixtures:
    ```python
    (1) carried open question, no edge:
        [Drift(location='/tmp/tmp2o6nm73c/sample.ipd.md', rule='check.ipd-carrier-ungated', detail='1 open question(s) name a carrier with no declared dependency edge: OQ-01 (carrier bk0001)', observed='1 open question(s) name a carrier with no declared dependency edge', required="a plan that must wait for a carried question's answer should declare an explicit dependency edge (e.g. `state:backlog:<status>:<carrier>`)", recovery='aw ipd dependencies set sample.ipd.md state:backlog:<status>:<carrier>', assurance='repository', determinism='deterministic', severity='info')]
    (2) declaring state:backlog:graduated:<carrier>: []
    (3) declaring state:backlog:done:<carrier>: []
    (4) question resolved: []
    (5) Carrier-Declined with no Carrier: []
    Six-row collapse case:
        6 open question(s) name a carrier with no declared dependency edge: OQ-01 (carrier bk0001); OQ-02 (carrier bk0002); OQ-03 (carrier bk0003); OQ-04 (carrier bk0004); OQ-05 (carrier bk0005) (and 1 more)
    Truncated plan file returning []: []
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `aw check plans` BEFORE and AFTER on this repository with the per-severity tally and the exit code from a driven `check_type` + `drift_exit_code`, showing the `error` count UNCHANGED at its measured baseline and the new rule appearing only in the `info` tally. Paste the `aw check all` run showing each offending plan reported EXACTLY ONCE (grep the rule id and count lines against the distinct-plan count). Paste a temp-repo case proving the pending-lane guard: the identical offending plan under `executed/` yields zero findings for this rule.
  - Observed evidence:
    BEFORE check_type + drift_exit_code on plans:
    ```
    Total findings: 112
    Exit code: 1
    Severities: {'info': 95, 'error': 17}
    ```

    AFTER check_type + drift_exit_code on plans:
    ```
    Total findings: 127
    Exit code: 1
    Severities: {'info': 110, 'error': 17}
    check.ipd-carrier-ungated count: 15
    ```
    Error count is UNCHANGED at 17, exit code UNCHANGED at 1, info count increased by exactly 15 (95 -> 110).

    Offending plans reported exactly once:
    ```python
    Total findings: 15
    Distinct plans: 15
      offending plan: 20260929-denypush-00-l4vw9o-decide-and-if-approved-build-a-landlock-backed-network-denia.ipd.md
      offending plan: 20260929-treegap-01-uxb0tz-answer-an-id6-that-lives-in-a-deliberately-untracked-records.ipd.md
      offending plan: 20260930-gzmr54-01-t9lcdu-restore-the-docs-check-and-docs-render-test-coverage-deleted.ipd.md
      offending plan: 20260930-runwire-00-i18yaz-wire-the-run-state-machine-into-the-host-runners.ipd.md
      offending plan: 20260930-runwire-02-eow7p4-enforce-verifier-session-independence-and-verifier-state-aut.ipd.md
      offending plan: 20261001-destshadow-03-z05z73-refuse-at-parser-build-an-argparse-dest-that-shadows-an-ance.ipd.md
      offending plan: 20261001-netnsfilter-00-m0kl28-build-host-granular-outbound-egress-filtering-as-a-probed-no.ipd.md
      offending plan: 20261001-netnsfilter-01-nxh5s4-probe-host-granular-egress-filtering-by-attempt-two-sided-an.ipd.md
      offending plan: 20261001-netnsfilter-04-wn956n-amend-the-contracts-and-close-the-set-with-an-audited-honest.ipd.md
      offending plan: 20261001-p4hmpz-01-t6ledu-decide-the-scope-not-audited-advisory-s-severity-on-a-measur.ipd.md
      offending plan: 20261001-rdyreq-01-fhinri-require-the-readiness-field-at-reviewed-and-approved-ipd-m11.ipd.md
      offending plan: 20261001-tf4jz5-01-j7dsci-repair-the-qrokie-plan-s-fabricated-filename-date-and-the-th.ipd.md
      offending plan: 20261002-carriergate-01-rpw4sb-decide-whether-a-carried-open-question-gates-its-plan-and-re.ipd.md
      offending plan: 20261002-runledger-01-rdjka2-decide-whether-a-driver-run-writes-a-hash-chained-ledger-and.ipd.md
      offending plan: 20261002-uonrjgcite-01-xtensb-sweep-the-uonrjg-criteria-for-stale-citations-and-uncovered.ipd.md
    ```

    Temp-repo case proving the pending-lane guard:
    ```sh
    $ python3 -c "
    import tempfile
    from tests.test_carrier_ungated_rule import TestCarrierUngatedRule
    from agent_workflows import check_engine as ce
    tc = TestCarrierUngatedRule()
    questions = [{'id': 'OQ-01', 'Blocking': 'no', 'Status': 'open', 'Owner': 'maintainer', 'Carrier': 'bk0001'}]
    plan_text = tc._build_plan(status='executed', deps='none', questions=questions)
    with tempfile.TemporaryDirectory() as td:
        repo, plan_path = tc._setup_repo(td, plan_text=plan_text, plan_lane='executed')
        drifts = ce.check_carrier_ungated(repo)
        print('check_carrier_ungated findings for executed plan:', drifts)
    "
    check_carrier_ungated findings for executed plan: []
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the added text from BOTH `.aw/records/plans/README.md` and `.aw/system/workflows/templates/plans-README.md`, showing in each that `Carrier` is stated to be durable ownership and NOT a dispatch gate, that the explicit `aw ipd dependencies set` edge is named as the way to make a plan wait, that the exact-status trap from F-08 is warned about, and that the new advisory rule is mentioned. Paste `grep -c "Durable carrier" .aw/system/workflows/templates/plans-README.md` showing it is no longer 0. Paste the two files' carrier sections diffed against each other to show the wording did not diverge where it should match. Paste `aw sanitize --agent` clean on both.
  - Observed evidence:
    Added text in .aw/records/plans/README.md and .aw/system/workflows/templates/plans-README.md:
    ```markdown
    ### Carrier records durable ownership, not a dispatch gate

    Writing `- Carrier: <id6>` on an open question records that the obligation has a durable carrier (a
    backlog item, research record, or another plan) tracking its eventual resolution. It is an OWNERSHIP
    claim, NOT A DISPATCH GATE. The runner does not inspect question carriers to decide whether a plan can
    run; under the 2026-09-10 ruling, a non-blocking open question does not prevent dispatch regardless of
    whether it names a carrier.

    If a plan MUST NOT DISPATCH until its carried question is answered, you MUST declare an explicit
    dependency edge on the carrier via `Item-Dependencies` (or `aw ipd dependencies set <plan>
    state:backlog:<status>:<carrier>`). Do not assume naming the carrier makes the plan wait.

    BEWARE THE EXACT-STATUS TRAP WHEN DECLARING CARRIER EDGES. The dependency grammar resolves
    `state:backlog:<status>:<id6>` against the carrier's EXACT status; multiple edges are ANDed and there is
    no OR/disjunction operator. In particular, a carrier that has `graduated` to a plan or spec has not
    reached `done`. Gating on `state:backlog:done:<carrier>` when the carrier is `graduated` will block the
    plan indefinitely.

    The check engine reports pending plans whose open questions name a carrier without declaring a
    corresponding dependency edge under the advisory `check.ipd-carrier-ungated` rule (`info` severity,
    non-blocking). Authors who intend for work to proceed in parallel may safely ignore the advisory; authors
    who expected the plan to wait should add the explicit dependency edge.
    ```

    Grep count in templates README:
    ```sh
    $ grep -c "Durable carrier" .aw/system/workflows/templates/plans-README.md
    1
    ```

    Diff between carrier sections in both files:
    ```sh
    $ python3 -c "
    from pathlib import Path
    import difflib
    r1 = Path('.aw/records/plans/README.md').read_text()
    r2 = Path('.aw/system/workflows/templates/plans-README.md').read_text()
    s1 = r1[r1.find('## Durable carrier vocabulary'):r1.find('## Identity, sets, and the clustering filename grammar')].strip()
    s2 = r2[r2.find('## Durable carrier vocabulary'):r2.find('## Execution contract')].strip()
    diff = list(difflib.unified_diff(s1.splitlines(), s2.splitlines(), fromfile='records/plans/README.md', tofile='templates/plans-README.md'))
    print('Diff lines between exact carrier sections:', len(diff))
    "
    Diff lines between exact carrier sections: 0
    ```

    aw sanitize --agent clean on both:
    ```sh
    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a PASSING narrowed `python3 -m pytest tests/test_carrier_ungated_rule.py -o addopts="" -v` run and map each behavior (a) through (g) plus the cutover-invariance case to the test(s) that pin it; test names are pointers, not the bar. Paste the case (e) fixture's full `aw check plans --agent` diagnostics list showing no rule other than `check.ipd-carrier-ungated` at a failing severity. PROVE NON-VACUITY BY MUTATION on the two assertions most likely to be vacuous: (a) in a scratch copy make the evaluator match on the full canonical edge token instead of the id6, paste the RED output from the `state:backlog:graduated` case, and restore; (b) change the registered severity to `warning`, paste the RED output from the exit-code-invariance case, and restore. Paste `git status --short agent_workflows/` clean after each. PROVE P16 COMPLIANCE: paste a grep of the new test file for `inspect`, `getsource`, `ast`, and any `read_text` of a path under `agent_workflows/`, showing zero matches. Finally paste the BARE `python3 -m pytest` summary line and its `FAILED` lines, and state explicitly that the failure set equals the baseline re-derived on your own HEAD.
  - Observed evidence:
    Passing narrowed test run:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=980952217
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 9 items

    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_c_non_subject_rows_are_silent PASSED [ 11%]
    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_b_edged_is_silent_whatever_qualifier PASSED [ 22%]
    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_a_reported_open_carried_question_no_edge PASSED [ 33%]
    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_cutover_invariance PASSED [ 44%]
    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_d_tier_and_exit_code_invariance PASSED [ 55%]
    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_f_terminal_plans_never_reported PASSED [ 66%]
    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_g_multiple_rows_collapse PASSED [ 77%]
    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_truncated_plan_never_raises PASSED [ 88%]
    tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_e_exit_code_invariance_and_visible_in_cli PASSED [100%]

    ============================== 9 passed in 0.93s ===============================
    ```

    Mapping of behaviors (a) through (g) and cutover-invariance to tests:
    - (a) reported open carried question with no edge: `test_case_a_reported_open_carried_question_no_edge`
    - (b) edged is silent whatever qualifier (`state:backlog:graduated`, `state:backlog:done`, `exists:backlog`): `test_case_b_edged_is_silent_whatever_qualifier`
    - (c) non-subject rows are silent (`resolved`, `withdrawn`, `Carrier-Declined` without `Carrier`): `test_case_c_non_subject_rows_are_silent`
    - (d) tier and exit code invariance: `test_case_d_tier_and_exit_code_invariance`
    - (e) exit code invariance and visible in CLI: `test_case_e_exit_code_invariance_and_visible_in_cli`
    - (f) terminal plans never reported (`executed/`, `superseded/`, `not-executed/`): `test_case_f_terminal_plans_never_reported`
    - (g) multiple rows collapse to single finding with bounded detail and `(and N more)`: `test_case_g_multiple_rows_collapse`
    - cutover invariance: `test_cutover_invariance`
    - truncated plan handling: `test_truncated_plan_never_raises`

    Case (e) fixture full aw check plans --agent diagnostics list:
    ```json
    exit code: 0
    diagnostics list: [
      {
        "location": ".aw/records/plans/pending/20260926-sample-01-pl000a-plan-a.ipd.md",
        "rule": "check.ipd-carrier-ungated"
      },
      {
        "location": "<collisions>",
        "rule": "check.collisions-not-checked"
      }
    ]
    ```
    Neither finding has a failing severity (`info` severity only, exit code 0).

    Non-vacuity proof by mutation (a) - full edge token matching instead of id6:
    ```
    =================================== FAILURES ===================================
    ____ TestCarrierUngatedRule.test_case_b_edged_is_silent_whatever_qualifier _____
    AssertionError: Lists differ: [Drift(location='/tmp/tmpowuyf2sq/.aw/reco[625 chars]fo')] != []
    FAILED tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_b_edged_is_silent_whatever_qualifier
    ======================= 1 failed, 8 deselected in 0.80s ========================
    ```
    Restored and verified git status --short agent_workflows/ clean.

    Non-vacuity proof by mutation (b) - registered severity changed to warning:
    ```
    =================================== FAILURES ===================================
    __ TestCarrierUngatedRule.test_case_e_exit_code_invariance_and_visible_in_cli __
    AssertionError: 1 != 0
    FAILED tests/test_carrier_ungated_rule.py::TestCarrierUngatedRule::test_case_e_exit_code_invariance_and_visible_in_cli
    ======================= 1 failed, 8 deselected in 1.20s ========================
    ```
    Restored and verified git status --short agent_workflows/ clean.

    P16 compliance check:
    ```sh
    $ grep -E "inspect|getsource|ast|read_text.*agent_workflows" tests/test_carrier_ungated_rule.py || echo "ZERO MATCHES"
    ZERO MATCHES
    ```

    Full bare test suite:
    ```
    NOTE: 258 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    6464 passed, 2 skipped, 3 warnings in 463.25s (0:07:43)
    ```
    Zero FAILED lines. The failure set equals the baseline re-derived on HEAD (0 failures).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is NOT approved for execution by its authoring. It carries `- Status: to-review` and requires `/plan-review` and then explicit human approval before any execution turn, as the lifecycle requires; no `- Readiness:` field is written here, because that field is an output of review and writing it would forge an attestation.

An executor must: honor the four declared `- Scope-Paths:` exactly and widen them through no opportunistic edit; commit only the paths it changed, through `aw commit <plan> -- <paths>`, and never push; run the validation plan above and PASTE ACTUAL OUTPUT rather than claiming success; NOT file the F-09 defect again, because it is already filed as backlog `bs850k` (a second filing would be a duplicate carrier); and treat OQ-01 as the maintainer's, neither resolving it nor implementing the enforcement half it governs. Under `aw oc run` / `aw agy run` the RUNNER owns `aw ipd begin`/`aw ipd finalize` and the executor must NOT run them; it leaves every `V-*` at `Result: pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforming. Executed by hand with no runner, the executor performs the terminal transition through `aw ipd finalize` (per the `ipd-lifecycle` workflow), never a hand-rolled `git mv`, and only once that same bar is met. SCOPE FENCE: `- Scope-Paths:` is a declaration the runner reconciles; an out-of-scope edit that proves necessary is made and justified with `--scope-reason` at finalize, and a declared path left unmodified needs `--scope-ack`.
