# IPD: Refuse an over-bound detail in the Drift constructor itself, once the live population is clean

- Date: 2026-10-01
- Kind: child
- Concern: Backlog `0livgf` residue 1. Nothing structurally enforces the Section 8.8 descriptive bound on a composed drift detail: `artifact_core.Drift` does not validate its own `detail`, `attention_contract.is_safe_descriptive` is applied to no composed detail anywhere, and the only thing holding the bound is one per-site test on one producer (added by executed plan `mc6r92`). So a future edit to ANY of the 171 detail assemblies can re-break the bound and nothing will catch it. The item records why `mc6r92` declined to close this: a producer-side refusal would red the live over-bound population at once, which is a repository-wide contract change rather than a wording fix.
- Scope: Make `artifact_core.Drift` REFUSE an over-bound, multi-line or control-character-bearing `detail` at construction, after the live population is clean, and amend spec Section 8.8 to extend its subject from an authored artifact field to a tool-composed drift detail. Includes bringing the two over-bound `check_engine` rules into bound, since the refusal cannot land while they violate it. EXCLUDES changing `MAX_DESCRIPTIVE_LEN` or `is_safe_descriptive`, excludes the lane producer (Order 01 owns it), and excludes the board's per-surface escaping bullet (pending plan `qpw45x` owns it).
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, tests/test_drift_detail_bound.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, CHANGELOG.md
- Item-Dependencies: executed:9sbfea
- Status: reviewed
- Readiness: no-go
- Work-Kind: chore
- Priority: low
- From-Backlog: 0livgf
- Set: driftbound
- Order: 2
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 62pkkg

## Workflow history
- 2026-10-07 reviewed (aw set): /plan-review REVIEWED - OPEN QUESTIONS; PR-001 escalated as blocking OQ-06

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-007. Reviewed at HEAD `baf4983ed`; plan byte-identical to lane input. PR-001 (HIGH, OPEN, escalated as blocking OQ-06): F-05/F-06 were wrong; a raising `Drift` is SWALLOWED by `check_type` and `ipd_lint._merge_durable_carrier`, so one over-bound finding silently drops every carrier finding (measured 96 -> 49 plans findings, including 21 `error`) and the pre-transition gate loses its blocking finding, while details echoing AUTHORED values (`specs.validate_spec` Gate-Ref) crash `aw check all` with exit 2. A clean live population cannot make a production `ValueError` safe. Fixed: population re-measured after `7stpjm`/`lxcexr` (PR-002), finished carriers cited (PR-003), stale `ynhst5`/bidi prose (PR-004), live-corpus census test (PR-005), gate ownership (PR-006), scope of authored-echo producers (PR-007).
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `0livgf`, owning residue 1 (no producer-side refusal); Order 01 owns residue 2. FOUR AUTHORING MEASUREMENTS CORRECT OR EXTEND THE ITEM. (1) ITS CITATION IS WRONG: `agent_workflows.core.Drift` does not exist, the symbol is `artifact_core.Drift` reached through the alias `core` (F-01). (2) THE POPULATION HAS MORE THAN DOUBLED, from the 12 findings the item records to 25 of 71, longest 974, and the split matters because 15 are `info`-severity and advisory (F-02); Order 02 must re-derive rather than inherit either number. (3) A NAIVE REFUSAL DOES NOT MERELY RED FINDINGS, IT CRASHES THE CHECKER, which the item does not say and which is the single most important finding here: driven in this lane, a raising `Drift` constructor propagates the exception OUT of `check_durable_carrier` on the FIRST over-bound finding, so `aw check` dies instead of reporting, and the same evaluator backs `aw ipd lint --phase pre-transition`, so it would also break a plan transition (F-05, F-06). That is why E-01 and E-02 clean the population BEFORE E-04 adds the refusal, and why the order is a correctness constraint rather than tidiness. (4) THE ITEM'S IMPLIED MECHANISM IS BLOCKED AS STATED but a working route exists: a `typing.NamedTuple` refuses a `__new__` override in its own class body, and measurement found that an intermediate base class accepts one while preserving every consumer API including `_replace`, `_asdict`, tuple indexing and sorting (F-07, F-08). This also contradicts a reading that the refusal must come at the cost of the tuple interface.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the Section 8.8 descriptive bound a property the `Drift` type enforces rather than a property one test observes at one site, so a future edit to any detail assembly is refused at construction instead of shipping an over-bound finding; and record in the spec that the bound governs a tool-composed detail, not only an authored artifact field.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measure the real population, then clean it

- [ ] E-01 Re-derive the over-bound population at execution HEAD and record it: the total finding count, how many exceed `MAX_DESCRIPTIVE_LEN`, the longest, and the per-rule and per-severity breakdown. Do this across `aw check all`, `aw attention --check`, `aw doctor`, and `aw ipd lint` over the pending plans, not `aw check all` alone.
  THE NUMBER IN THE BACKLOG ITEM IS ALREADY STALE BY A FACTOR OF TWO AND WILL BE STALER AT EXECUTION. The item says 12; measured here it is 25 of 71 (F-02). It moves because the population is a function of how many pending plans carry uncarried obligations, which changes daily. So no number in this plan is an acceptance bar, and E-04's gate is "the live population is empty", re-measured, never "25 are fixed".
  SWEEP MORE THAN `aw check all`, because the refusal binds EVERY producer and the census must too. F-03 counts 171 construction sites across 10 production modules; a site that never fires in `aw check all` (a doctor probe failure path, a research-index frontmatter error) can still construct an over-bound detail at runtime. Drive each surface and record which ones produce a finding at all.
  - Depends on: none
  - Expected outcome: a recorded per-surface, per-rule, per-severity census at execution HEAD with the commands that produced it, plus an explicit list of which rules are over bound and which surfaces could not be exercised.
  - Execution state: pending

- [ ] E-02 Bring the over-bound `check_engine` details into bound at the producer, without losing a locator an operator needs. The two rules measured today are `check.ipd-uncarried-obligation` and `check.ipd-carrier-finished-unverified`, both composed in `check_engine.evaluate_durable_carrier`.
  REVIEW UPDATE (PR-002): executed plan `lxcexr` already replaced the fixed `[:5]` cap with a budget, so the only remaining over-bound case (measured 2026-10-07) is its deliberate `# Floor of one locator (OQ-01)` clause: one obligation whose single reason body exceeds the budget (329 characters on `qtz0us`). `lxcexr` OQ-01 kept it over bound ON PURPOSE because a count-only detail is unactionable, and named `0livgf` as the owner. So E-02's real work is a MARKED elision INSIDE that one floor clause (keep the locator, elide the body's tail with a visible marker, full text via `recovery`), not re-tuning the cap. The paragraphs below describe the pre-`lxcexr` code and are retained as context.
  BOTH DETAILS ALREADY ELIDE AND THE ELISION IS SIMPLY SET TOO LOOSE. The function takes `rule_failures[:5]` and appends `(and N more)`, with the constant beside `_IPD_LINT_SHOWN` recording the reason a cap exists at all. So this is a change to HOW MUCH is enumerated, not the introduction of elision, and the honest fix is to spend a budget rather than to count rows: five short reasons fit easily while five long ones reach 974 characters.
  PREFER REUSING `attention_contract.compose_bounded_detail`, which Order 01 adds for exactly this shape (a prefix, a joined enumeration, and a marked elision), rather than writing a second bounded-composition scheme in `check_engine`. Order 01's OQ-04 deliberately left this decision here. If you instead reduce the cap, say WHY the composer did not fit, and measure what an operator loses.
  THE `recovery` FIELD IS WHERE THE FULL LIST LIVES, and that is already the design: `_IPD_LINT_SHOWN`'s comment says "The full list always remains one command away via the `recovery` field". So an elision here costs the operator a command, not information, which is what makes it acceptable under Section 8.8's refusal to truncate silently.
  DO NOT CHANGE WHICH OBLIGATIONS FAIL, the rule ids, or `carrier_severity_for_plan`'s per-plan severity. A change that made fewer plans fail would be the easy way to make this item pass and would silently weaken a shipped gate.
  - Depends on: E-01
  - Expected outcome: every finding from every surface in the E-01 census satisfies `A.is_safe_descriptive`, re-measured with the same commands; the set of plans that FAIL each rule is unchanged (paste the before and after locator lists); and the `recovery` field still names the command that shows the full list.
  - Execution state: pending

- [ ] E-03 Bring the remaining producers into bound, specifically the five `doctor` probe-failure details that currently hard-truncate an exception string and the `doctor.leak-*` detail that truncates a snippet.
  THESE ARE ALREADY TRUNCATING AND THAT IS ITSELF A CONTRACT PROBLEM, not merely a length one. Section 8.8 says "Over-length values are a contract violation, not silently truncated", and `doctor` slices an exception message to a fixed width with no marker, so a reader cannot tell a complete message from a cut one. Replace the bare slice with a MARKED elision so the cut is visible. This is a small change but it is the difference between obeying the spec and coincidentally fitting it.
  CHECK, DO NOT ASSUME, THAT A FIXED SLICE IS ENOUGH. A truncated exception is bounded, but the detail it sits in is a composed f-string (a prefix plus the slice), so the TOTAL is what must fit. Re-derive each site's worst total rather than trusting the slice width.
  - Depends on: E-01
  - Expected outcome: every `doctor` detail is within the bound by arithmetic over its composed total, and every truncation it performs carries a visible marker; the E-01 doctor census is clean when re-run.
  - Execution state: pending

### Task group 2: the structural refusal

- [ ] E-04 In `agent_workflows/artifact_core.py`, make `Drift` REFUSE a `detail` that fails `attention_contract.is_safe_descriptive`, raising a `ValueError` naming the rule, the offending length and the bound. Preserve every consumer API the type has today.
  DO THIS ONLY AFTER E-01 THROUGH E-03 LEAVE THE POPULATION EMPTY, AND VERIFY THAT RATHER THAN ASSUMING IT. The ordering is a correctness constraint: F-05 measures that with a raising constructor the exception propagates OUT of `check_durable_carrier` on the first over-bound finding, so `aw check` crashes rather than reporting. F-06 measures the same evaluator backing `aw ipd lint --phase pre-transition`, so landing the refusal early would break the plan transition gate, including this very plan's.
  THE MECHANISM IS NOT THE OBVIOUS ONE AND THE OBVIOUS ONE IS IMPOSSIBLE. A `typing.NamedTuple` REFUSES a `__new__` in its own class body (measured: `AttributeError: Cannot overwrite NamedTuple attribute __new__`, and a `super()` call raises `TypeError` about unsupported `super()` in a NamedTuple method). The working route, measured in this lane, is an intermediate base: declare the fields on a private `NamedTuple` base and have `Drift` subclass it with a validating `__new__` that calls the base's `__new__` directly rather than through `super()`. F-07 and F-08 record that this preserves `isinstance(d, tuple)`, positional indexing, `_asdict`, `_fields`, sorting and field annotations.
  OVERRIDE `_make` AND VERIFY `_replace`, OR THE REFUSAL HAS A HOLE THE REPOSITORY ACTUALLY USES. Measured: with only `__new__` overridden, `_replace` and `_make` BYPASS the check; with `_make` also overridden to route through the constructor, both refuse. This matters concretely rather than theoretically, because `check_engine.enrich_drift` returns `drift._replace(...)` and is the path EVERY enriched finding flows through, so a `_replace` that skips validation skips it for most of the repository's findings.
  VALIDATE THE SAME THREE THINGS `is_safe_descriptive` DOES, by CALLING it rather than re-deriving them. A second length or control-character rule here could disagree with the predicate, producing a value the checker calls unsafe and the constructor accepts, or the reverse. One definition, two readers. F-09 confirms the import direction is acyclic.
  THE EXCEPTION MESSAGE MUST BE ACTIONABLE, naming the rule id, the actual length, the bound, and which of the three conditions failed. A bare `ValueError` on a 171-site type would be a debugging trap.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `artifact_core.Drift(loc, rule, "x" * 301)` raises `ValueError` naming the rule, length and bound; so do a newline-bearing and a control-character-bearing detail; `d._replace(detail=<over-bound>)` and `Drift._make([...])` also raise; a conforming construction is unchanged; and `isinstance(d, tuple)`, `d[2]`, `d._asdict()`, `d._fields` and sorting all behave exactly as before.
  - Execution state: pending

- [ ] E-05 Add `tests/test_drift_detail_bound.py` covering the refusal behaviorally: each of the three failing conditions, each of the three construction routes (`Drift(...)`, `_replace`, `_make`), the preserved tuple API, and a REGRESSION case asserting that every surface in the E-01 census is clean.
  THE CENSUS CASE IS THE ONE THAT MAKES THIS STRUCTURAL RATHER THAN THREE MORE UNIT TESTS, and it is what the backlog item is actually asking for. Drive the real surfaces (`aw check all`, `aw attention --check`, `aw doctor`) and assert that each returns findings whose details all satisfy the bound. RUN THEM OVER A FIXTURE TREE that deliberately triggers the longest producers (a multi-carrier floor obligation, an over-long authored `Gate-Ref`), NOT over this repository's live records; a case that reads the live corpus must carry the `livecorpus` marker, which the default run deselects, so it cannot be the regression guard (PR-005). That single test is what a future edit to any of the 171 assemblies trips over, and it is the thing `mc6r92` could not add because the population was dirty.
  ASSERT THE PRESERVED API EXPLICITLY, because the mechanism change is the risk here. A test that only checks the refusal would stay green if the fix broke `_asdict`, and `attention` serializes drift with `[d._asdict() for d in drift]` on two payload paths, so that break would be a shipped defect in the `--json` output.
  NO SOURCE INTROSPECTION, per GUIDING_PRINCIPLES P16 and the repository's code-pinning prohibition: construct values, call the real surfaces, and assert on raised exceptions, returned strings and exit codes. Do not assert that `artifact_core` contains a `__new__`, do not count call sites, and do not pin a docstring.
  - Depends on: E-04
  - Expected outcome: a new test module whose refusal cases FAIL against the pre-E-04 type (paste that run) and pass after; the census case passes only with E-02 and E-03 landed; and the full suite is green.
  - Execution state: pending

### Task group 3: record the extended contract

- [ ] E-06 Amend spec Section 8.8 to state that the bound governs a TOOL-COMPOSED drift `detail` as well as an authored descriptive field, and that a producer cannot construct a violating one. Add a dated amendment note in the spec's own style.
  THIS AMENDMENT IS REQUIRED RATHER THAN OPTIONAL, AND THE REASON IS A GAP IN THE SPEC THAT THE BACKLOG ITEM DOES NOT NOTICE. Section 8.8's subject sentence names "Descriptive metadata (`Gate-Summary`, `- Status:` neighbours, paths, URLs, and any future tree metadata)", which is a list of AUTHORED artifact fields. The only place the spec mentions a drift detail is Section 8.3, which requires ESCAPING the `location<TAB>rule<TAB>detail` record and says nothing about bounding it. So a reader can reasonably hold that the bound never governed a composed detail at all, and shipping a refusal without the amendment would enforce a contract the spec does not state (F-10). The amendment is what makes the refusal legitimate rather than inventive.
  SAY WHAT THE REFUSAL COSTS, in the amendment text. A producer that cannot construct an over-bound detail must elide, and an elision loses information from the line. Record that the full information remains reachable through the `recovery` field and the named command, which is the argument that makes the trade honest.
  DO NOT WEAKEN THE EXISTING BULLETS, and in particular do not relax "Over-length values are a contract violation, not silently truncated" to accommodate E-02 and E-03. Those items add MARKED elision, which is the opposite of silent truncation; if the amendment ends up needing to soften that sentence, the implementation took the wrong route and should be revisited rather than the contract loosened.
  DO NOT TOUCH THE SPEC'S `- Status:` OR ITS `## Workflow history` as a lifecycle act, and do not run `aw specs set`. This is a content amendment, not a transition; appending a dated amendment note in the body style the spec already uses is correct, and a lifecycle call here would assert an event that did not happen.
  NOTE THE SPEC IS LEGACY-NAMED AND CARRIES NO `- Id:`, so cite it by filename or slug (`attention-registry-and-cross-tree-status`) and never by an id6 it does not have. Pre-cutover spec names are grandfathered; do NOT rename it as a side effect of this plan.
  - Depends on: E-04
  - Expected outcome: Section 8.8 states that the bound covers a tool-composed drift detail, names the refusal as the enforcement point, records the elision trade, and leaves every existing bullet intact; the spec's `- Status:` and `## Workflow history` are unchanged; and `aw check` reports no new finding on the amended spec.
  - Execution state: pending

- [ ] E-07 Add a `CHANGELOG.md` entry recording the enforced bound and what a consumer may now see elided, and check the remaining per-site pin for redundancy.
  SAY WHAT A USER NOTICES, which is the only thing a changelog entry is for here: a very long `aw check` finding now ends in a marked elision with the full list one command away, and a tool that constructs a finding is refused rather than shipping an over-bound line.
  CHECK WHETHER ORDER 01's PER-SITE ASSERTIONS ARE NOW REDUNDANT, AND LEAVE THEM IF THEY ARE NOT. The constructor refusal makes an over-bound lane detail impossible, so the lane bound assertions become belt and braces. KEEP THEM: they assert the composer's behavior (what gets elided and that live rows are unchanged), which the constructor refusal does not cover, and deleting coverage because a stronger guard exists is how the repository lost tests before. Record the judgement rather than acting on it silently.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: one `CHANGELOG.md` entry in the existing style; and a recorded statement of whether any existing bound assertion is now redundant, with the decision to keep or remove each and the reason.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- A CHECK MUST NEVER CRASH, AND THIS IS STATED REPEATEDLY IN THE CODE THIS PLAN EDITS. `check_engine.evaluate_durable_carrier`'s docstring ends "Never raises", and the same promise appears on at least four other evaluators in that module, one spelling it out as "a crashing check is a" worse outcome than a missing finding. `evaluate_ipd_lint_diagnostics` says "a plan that cannot be read or linted yields no finding rather than breaking the" sweep. A refusal added at the `Drift` constructor is therefore in direct tension with the module's stated contract, which is exactly why the population must be clean before it lands.
- A CHECK THAT FAILS ON CORRECT BEHAVIOR IS A CHECK OPERATORS BYPASS. The governing spec states this in its requirement F3a ("TWO EXCLUSIONS ARE NORMATIVE, because a check that fails on correct behavior is a check operators bypass"), and `attention.lane_drift_severity`'s docstring records the measured consequence: ten lanes held the board at `VIEW INVALID` indefinitely, which "teaches an operator to stop reading it". The same reasoning forbids landing a refusal over a dirty population.
- THE OPTIONAL `Drift` FIELDS WERE ADDED UNDER AN EXPLICIT NON-BREAKING CONSTRAINT and the docstring states it: "every existing producer constructs `Drift(location, rule, detail)` positionally and every existing consumer reads those three attributes, so they are UNCHANGED". Any mechanism change here inherits that constraint, which is why E-04's expected outcome enumerates the preserved APIs rather than assuming them.
- ELISION WITH A VISIBLE MARKER IS THE IN-REPO PATTERN: `evaluate_durable_carrier` shows five then `(and N more)`, `_IPD_LINT_SHOWN` does the same with the reason recorded beside the constant, `lane_containment` formats `a, b, c, ... and N more`, and `term.truncate_visible` takes an explicit `ellipsis`. A bare fixed-width slice (as `doctor` currently does) is the outlier, not the convention.
- `info` SEVERITY IS ADVISORY AND DOES NOT FAIL THE GATE: `artifact_core.drift_exit_code` exempts exactly `info`. This matters for the census because 15 of the 25 over-bound findings measured here are `info`, so most of the population is not currently failing anything, which makes it easy to overlook and is not a reason to leave it.
- THE SUITE RUNS BARE: `python3 -m pytest`, with `addopts` already supplying `-q -n auto --dist=worksteal` and the marker deselection. Do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).

## Findings

Every finding below was driven in this lane at HEAD `f5bba04b`. Each names the command or snippet that produced it.

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **THE BACKLOG ITEM'S CENTRAL CITATION IS WRONG AND IS CORRECTED HERE.** The item names `agent_workflows.core.Drift` twice. There is no `agent_workflows/core.py`. The symbol is `artifact_core.Drift`; `attention`, `backlog` and `doctor` import the module as `core`, which is where the name came from. | `ls agent_workflows/core.py` reports no such file. `agent_workflows/artifact_core.py` defines `class Drift(NamedTuple)` with `location`, `rule`, `detail` plus six optional metadata fields defaulting to `""`. |
| F-02 | **SUPERSEDED AT REVIEW (PR-002): executed plan `lxcexr` (backlog `7stpjm`, `done`) made `evaluate_durable_carrier` budget-driven with a floor of ONE locator; re-measured 2026-10-07 the ONLY over-bound details are the floor case, 329 characters on pending plan `qtz0us` (`check all` 2 of 226, `doctor` 4 of 821, `attention --check` 0 of 11). Authoring text follows.** THE POPULATION HAS MORE THAN DOUBLED since the item was filed, and the severity split matters. 25 of 71 `aw check all` findings exceed the bound (the item says 12 of 60), longest 974 (the item says 942), still exactly two rules: `check.ipd-uncarried-obligation` (10, `error`) and `check.ipd-carrier-finished-unverified` (15, `info`). | `python3 -m agent_workflows check all --json`, exit 1; counted over `diagnostics` with `len(detail) > A.MAX_DESCRIPTIVE_LEN`. |
| F-03 | The blast radius is 171 production construction sites across 10 modules, plus 51 in 7 test modules. So the refusal is a repository-wide contract change exactly as the item says, and the test suite is part of the migration surface. | Counted `Drift(` and `_core.Drift(`/`core.Drift(` constructions: `check_engine` 63, `backlog` 21, `attention` 18, `doctor` 18, `research_index` 13, `releases` 12, `specs` 11, `plans_index` 7, `prompts_index` 4, `result_types` 1. |
| F-04 | Both over-bound rules come from ONE function and ALREADY elide, so E-02 is tuning an existing mechanism rather than introducing one. | AT REVIEW: `rule_failures[:5]` is gone; `evaluate_durable_carrier` now spends `_ac.MAX_DESCRIPTIVE_LEN` as a budget over grouped clauses and, when nothing fits, keeps a `# Floor of one locator (OQ-01)` clause unelided, which is the sole remaining over-bound producer (PR-002). |
| F-05 | **CORRECTED AT REVIEW (PR-001): A RAISE ESCAPES `check_durable_carrier`, BUT `aw check` DOES NOT DIE; IT SILENTLY DROPS EVERY CARRIER FINDING, which is worse.** `check_engine.check_type` wraps the call in `try: drift.extend(check_durable_carrier(...)) except Exception: pass`, so one over-bound finding on one plan discards the whole sweep's carrier findings. Measured at review with a strict constructor patched in: `check_type(repo, "plans")` went from 96 findings to 49, losing all 26 `check.ipd-carrier-finished-unverified` and all 21 `check.ipd-uncarried-obligation` (`error`) findings, while only 2 details were over bound. Other producers are NOT fail-isolated: a 444-character `Gate-Ref` echoed by `specs.validate_spec` raised out of `check_type("specs")`, and `cli.main(["check","all","--agent"])` with that producer raising returned exit 2. | Driven: monkeypatched `artifact_core.Drift` to raise above the bound, then called `check_engine.check_durable_carrier(Path('.'))`; the exception escaped the call after exactly one construction, on `check.ipd-carrier-finished-unverified` at 519 characters. |
| F-06 | **CORRECTED AT REVIEW (PR-001): the same evaluator backs the PLAN TRANSITION GATE, and a raise there is SWALLOWED, so the gate silently PASSES what it should block.** `ipd_lint._merge_durable_carrier` catches `Exception` ("a repo-scan failure never masks the pure lint result"). Measured: on pending plan `1u4olp` the pre-transition lint carried a blocking `6 obligation(s) name no durable carrier` finding; with the refusal simulated on that detail the finding vanished and nothing replaced it. | `evaluate_durable_carrier`'s docstring: "`aw check` (via `check_durable_carrier`) and `aw ipd lint --phase pre-transition` (via `ipd_lint._merge_durable_carrier`) both call THIS function". `ipd_lint._merge_durable_carrier` delegates to it. |
| F-07 | **THE OBVIOUS MECHANISM IS IMPOSSIBLE: a `typing.NamedTuple` refuses a `__new__` override in its own body.** | Driven on this interpreter: defining `__new__` in a `NamedTuple` body raises `AttributeError: Cannot overwrite NamedTuple attribute __new__`, and using `super()` inside a NamedTuple method raises `TypeError: uses of super() and __class__ are unsupported in methods of NamedTuple subclasses`. |
| F-08 | **A WORKING MECHANISM EXISTS AND PRESERVES EVERY CONSUMER API, which contradicts a reading that the refusal must cost the tuple interface.** An intermediate `NamedTuple` base plus a subclass whose `__new__` calls the base's `__new__` directly validates at construction while keeping `isinstance(d, tuple)`, positional indexing, `_asdict`, `_fields`, sorting and field annotations. Overriding `_make` closes the `_replace`/`_make` bypass. | Driven: with only `__new__` overridden, `_replace` and `_make` BYPASS the check; adding a `_make` classmethod that routes through the constructor makes all three (`ctor`, `_replace`, `_make`) refuse, while `d._replace(severity="info")` on a conforming detail still works and `_asdict()` still returns every field. |
| F-09 | The validation can call `is_safe_descriptive` without an import cycle, so the refusal reuses the ONE predicate rather than re-deriving the rules. | `attention_contract` imports only `re`, typing and `lifecycle_dirs`; `lifecycle_dirs` loads only `versioning`, `_compat` and the package root. Importing `attention_contract` and `artifact_core` in either order succeeds. |
| F-10 | **SECTION 8.8's SUBJECT IS AN AUTHORED ARTIFACT FIELD, NOT A COMPOSED DRIFT DETAIL, so the refusal needs the E-06 amendment to be legitimate.** The section opens on "Descriptive metadata (`Gate-Summary`, `- Status:` neighbours, paths, URLs, and any future tree metadata)". The spec's only mention of a drift detail is Section 8.3, which requires ESCAPING the `location<TAB>rule<TAB>detail` record and says nothing about bounding it. | The spec `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`, Section 8.8 bullets and its requirement F10 and criterion A14; Section 8.3's "the `--agent`/`--check` violation record stays the house `location<TAB>rule<TAB>detail` form". The file is legacy-named, `- Status: implemented`, and carries no `- Id:`. |
| F-17 | **DETAILS THAT ECHO AUTHORED VALUES ARE UNBOUNDED BY ANY TOOL EDIT, so "clean the population first" cannot make a raising constructor safe (PR-001, PR-007).** The bound on these is a function of what an author writes next, not of producer code. | `specs.validate_spec` composes `A.escape_detail(f"invalid Gate-Ref for {kind}: {ref!r}")`; `research_index` composes `f"{e.field}: {e.message}"` and `f"id {fm.get('id')} != name {parsed.id6}"`; measured at review a 400-character `Gate-Ref` produced a 444-character detail. None of these files is in `- Scope-Paths:`. |
| F-11 | `doctor` ALREADY TRUNCATES and does so with no marker, which Section 8.8 names as the wrong remedy. Five probe-failure sites slice an exception to a fixed width and one slices a leak snippet. | `doctor` constructs `core.Drift("<git>", "doctor.probe-failed", str(exc)[:120])` and four siblings for `<version>`, `<attention>`, `<artifacts>` and `<sanitizer>`, plus a `doctor.leak-*` detail built from `f"{f.severity}: {f.snippet[:120]}"`. |
| F-12 | `enrich_drift` is the path nearly every finding flows through and it uses `_replace`, which is why the `_replace` bypass in F-08 is a live hole rather than a theoretical one. | `check_engine.enrich_drift` returns `drift._replace(observed=..., required=..., recovery=..., assurance=..., determinism=..., severity=...)`, and `evaluate_durable_carrier` wraps both of its `Drift` constructions in it. |
| F-13 | Two `attention` payload paths serialize drift with `_asdict`, so a mechanism that broke the namedtuple API would be a shipped `--json` defect, not an internal detail. | `attention` builds `"drift": [d._asdict() for d in drift]` on two payload paths; `tests/test_artifact_adopt.py` also calls `d._asdict()`. |
| F-14 | **A LIVE SET EXPLICITLY EXCLUDES THE CHANGE THIS PLAN MUST NOT MAKE**, which bounds the design: the refusal must reuse the predicate, not alter it. | Pending orchestrator `xhr0dj` (Set `qbz8i1`) excludes, "in every child without exception: minting a new rule id, changing `attention_contract.is_safe_descriptive` or `MAX_DESCRIPTIVE_LEN`". Its child `ynhst5` has since EXECUTED (review 2026-10-07, PR-004), so its `check_engine.py` edits are already on the tree E-01 measures. |
| F-15 | A live pending plan is amending the SAME spec section, in a different bullet, so E-06 must amend rather than rewrite and must expect a neighbouring edit. | Pending plan `qpw45x` (Set `llnvwj`) declares the same spec file in `- Scope-Paths:` and amends Section 8.8's Markdown-escaping bullet, adding `neutralize_control_characters` and `escape_markdown_inline` to `attention_contract`. |
| F-16 | 15 of the 25 over-bound findings are `info` and therefore do not currently fail any gate, which is why this population survived unnoticed. | `artifact_core.drift_exit_code` returns 1 only when some finding's severity is not `info`; the `check.ipd-carrier-finished-unverified` RuleSpec carries `severity='info'`. |

## Proposed changes (ordered, validatable)

1. Re-derive the over-bound census across every drift-producing surface (E-01).
2. Bring the two `check_engine` carrier-rule details into bound, preferably through Order 01's composer (E-02).
3. Bring the `doctor` probe and leak details into bound with marked elision (E-03).
4. Make `Drift` refuse a non-conforming detail at construction, closing the `_replace` and `_make` bypasses (E-04).
5. Cover the refusal and the preserved tuple API behaviorally, plus a whole-surface census regression (E-05).
6. Amend spec Section 8.8 to extend the bound to a tool-composed detail and name the enforcement point (E-06).
7. Record the change and judge the now-redundant per-site pins (E-07).

## Deferred / out of scope (with reason)

- **Bounding the stranded-lane detail by construction.** That is residue 2 of the same backlog item and is this Set's Order 01, which this plan declares as `- Item-Dependencies: executed:9sbfea`. The edge is load-bearing rather than cosmetic: the lane producer's worst reachable composition is 370 characters (Order 01's F-04), so a refusal landing first would raise inside `aw attention --check` on a sufficiently long worktree path.
  - Carrier: 0livgf
- **The 25-finding population as a standing concern.** This plan FIXES the live instances (E-02, E-03) and makes recurrence impossible (E-04), which is what closes it; but the item that tracks the population is `7stpjm`, and that item's own routes (reduce the enumeration cap, summarize repeated clauses, bound at the producer) are the menu E-02 chooses from. It stays carried until E-02 actually lands, because this plan could legitimately be cut back to the refusal alone and leave the population. STATUS AT REVIEW (2026-10-07): `7stpjm` is `done`, closed by executed plan `lxcexr`; the one residual floor case is E-02's to fix (PR-002, PR-003).
  - Carrier: 7stpjm
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7stpjm-01-lxcexr-bring-every-carrier-obligation-check-detail-inside-the-secti.ipd.md
- **Changing `MAX_DESCRIPTIVE_LEN` or `is_safe_descriptive`.** Not done, and not merely out of taste: F-14 records that a live Set excludes exactly this in every child, and widening or narrowing the predicate would change what `aw specs check`, `aw backlog check` and `aw attention --check` reject across every tree. The refusal here reuses the predicate unchanged.
  - Carrier-Declined: nothing is owed, because no defect is being deferred. The predicate is correct for its purpose and this plan needs no change to it; the bidi widening `3jez8u` tracked has since shipped through executed plan `0obt4k` without this plan (PR-004).
- **The 883 authored artifact descriptive fields that exceed the bound.** Disjoint from this plan by construction: those are AUTHORED fields in tracked artifacts, not tool-composed drift details, and the refusal added here binds only the `Drift` constructor. Enforcing the bound on authored fields at `error` would deadlock the lifecycle, which that item measures.
  - Carrier: tapqf2
- **Markdown-escaping or control-character-neutralizing any renderer.** A different Section 8.8 bullet (deterministic escaping per surface) owned by live pending plan `qpw45x` (F-15). This plan's refusal makes an unsafe value unconstructable, which is complementary to escaping at render and not a substitute for it.
  - Carrier: llnvwj
- **Bidi control characters, which Section 8.8 names.** At authoring `_CONTROL_CHAR_RE` did not match them; executed plan `0obt4k` (backlog `3jez8u`, `done`) has since widened it to `\u202a-\u202e\u2066-\u2069`. This plan still reuses the predicate UNCHANGED and so inherits the widened reading (PR-004).
  - Carrier: 3jez8u
  - Carrier-Evidence: .aw/records/plans/executed/20261002-3jez8u-01-0obt4k-widen-the-section-8-8-control-character-predicate-to-reject.ipd.md

## Scope check

- Over-scope: none. Every declared path is written by at least one E-item: `artifact_core.py` by E-04, `check_engine.py` by E-02, `doctor.py` by E-03, the new test module by E-05, the spec by E-06, and `CHANGELOG.md` by E-07.
- Under-scope: residue 1 of backlog `0livgf` is fully covered (the bound becomes a property of the type, not of one test). NOT covered, each with a reason recorded in Deferred above: residue 2 (Order 01, declared as a dependency), the authored-field population (`tapqf2`), per-surface escaping (`qpw45x`), and bidi controls (`3jez8u`).

## Required tests / validation

- `python3 -m pytest tests/test_drift_detail_bound.py` must pass, and its refusal cases must FAIL against the pre-E-04 type with both runs pasted.
- The BARE full suite `python3 -m pytest`, with the `N passed` summary line pasted. The 51 test-module construction sites make a suite-wide regression the primary risk of E-04.
- `python3 -m agent_workflows check all`, `attention --check`, `doctor` and `ipd lint` over the pending plans: each must exit with the SAME code as before this plan and produce findings that all satisfy `A.is_safe_descriptive`. A crash is a failure of E-04's ordering, not a flake.
- `aw ipd lint --phase pre-transition` on a real plan, proving the transition gate still functions with the refusal live (F-06 is the hazard this checks).
- The before-and-after locator lists for both carrier rules, proving E-02 changed the detail text and not which plans fail.
- `aw check` and `aw ipd lint` on this plan.

## Spec / documentation sync

E-06 amends `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` Section 8.8, and the file is declared in `- Scope-Paths:` per the AGENTS.md rule so both runners announce the declared spec edit before the run and reconcile it at run end. WHY THE AMENDMENT IS LOAD-BEARING: F-10 measures that Section 8.8's subject is a list of AUTHORED artifact fields and that the spec's only mention of a drift detail (Section 8.3) requires escaping rather than bounding. So the bound this plan ENFORCES on a composed detail is not stated by the spec today, and shipping the refusal without the amendment would enforce an unwritten contract. The amendment NARROWS nothing and weakens no bullet; it extends one sentence's subject and names the enforcement point. Order 01 deliberately amends no spec, so exactly one plan in this Set edits this file.

`CHANGELOG.md` (E-07) records the user-visible effect: a very long finding now ends in a marked elision with the full list one command away.

## Open questions

### OQ-01: Must the population be clean before the refusal lands, or can the refusal degrade gracefully instead?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: REVIEW NOTE (PR-001): the measurement below was wrong (the raise is swallowed, silently dropping findings, rather than crashing), and the clean-first ordering is still necessary but is NOT sufficient; see blocking OQ-06. RESOLVED as CLEAN FIRST, on a measurement that upgrades the item's own reasoning. The item says a refusal "would red 12 live `aw check all` findings at once", which implies the cost is noisy failures. F-05 measures something worse: the exception propagates OUT of `check_durable_carrier`, so `aw check` CRASHES on the first over-bound finding rather than reporting 25 of them, and F-06 shows the same evaluator backing `aw ipd lint --phase pre-transition`, so the plan transition gate breaks too. The graceful-degradation alternative was considered and rejected: catching the refusal at each producer and substituting a placeholder would put a `try` around 171 construction sites and would silently discard findings, which is strictly worse than the gap being closed. The ordering E-01 through E-04 is therefore a correctness constraint, and E-04's gate is a re-measured empty population rather than a fixed count.

### OQ-02: Which mechanism, given a `NamedTuple` cannot take a `__new__` in its own body?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: RESOLVED as the INTERMEDIATE BASE route, measured rather than reasoned. Three candidates were driven in this lane. (a) `__new__` in the `NamedTuple` body: IMPOSSIBLE, raises at class definition time (F-07). (b) A frozen dataclass: rejected because it breaks `isinstance(d, tuple)`, positional indexing, `_asdict` and `_replace`, and F-12 and F-13 measure that `enrich_drift` depends on `_replace` while two `attention` payload paths depend on `_asdict`. (c) A private `NamedTuple` base plus a validating subclass: WORKS and preserves all of it (F-08), with `_make` also overridden to close the bypass. Route (c) is chosen. Note this corrects a plausible but wrong conclusion that the refusal must cost the tuple interface; measurement says it costs nothing but an extra class.

### OQ-03: Does the refusal belong at the constructor, or at a validating factory every producer must call?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: RESOLVED as THE CONSTRUCTOR, because the backlog item's complaint is specifically that enforcement is not STRUCTURAL. A factory function plus a test asserting every producer routes through it would leave the type itself permissive, so a new producer written next year that constructs `Drift(...)` directly is unguarded, and the guard would be exactly the kind of code-structure assertion the repository prohibits (a census of call sites rather than a behavior). The constructor cannot be bypassed by a new caller, which is the property being bought. The cost is that the refusal is a `ValueError` at runtime rather than a lint finding, which is why E-04 requires an actionable message and why E-01 through E-03 must leave the population empty first.

### OQ-04: Should E-02 reuse Order 01's composer, or reduce the enumeration cap?

- Blocking: no
- Status: open
- Owner: the executor of E-02, who must decide and record it; escalate to the maintainer only if both routes lose a locator an operator needs
- Resolution or deferral rationale: DELIBERATELY LEFT OPEN FOR THE EXECUTOR TO DECIDE AND RECORD, because it needs a measurement this plan has not taken and the two routes are genuinely close. Reusing `attention_contract.compose_bounded_detail` (Order 01) handles the shape exactly and keeps one bounded-composition scheme in the repository; reducing `rule_failures[:5]` to a smaller cap is simpler and needs no new dependency, and is the route backlog `7stpjm` names as "the cheapest real win". What decides it is what an operator loses: a budget spends characters on as many locators as fit, while a cap drops whole locators regardless of length, and 10 of the over-bound findings are `error`-severity rows a maintainer acts on. THIS IS NOT BLOCKING because either route satisfies E-02's expected outcome and the choice is recorded in evidence; it is open rather than resolved because resolving it from this chair would be a guess dressed as a decision.
- Carrier-Declined: nothing is owed beyond this plan. The question is answered INSIDE E-02 by the executor, whose evidence must name the route and the measurement behind it, so there is no work outliving this plan for a carrier to hold.

### OQ-05: Does E-02 race the `approved` plan `ynhst5`, which also declares `check_engine.py`?

- Blocking: no
- Status: resolved
- Owner: this plan
- Resolution or deferral rationale: MOOT AT REVIEW (2026-10-07, PR-004): `ynhst5` has executed, so its edits are already on the tree. Original reasoning: RESOLVED as NO RACE, and no dependency edge is declared on it. F-14 records the overlap: `ynhst5` is `approved` and declares `agent_workflows/check_engine.py` among its paths, where it registers `attention.unsafe-field` in the rule registry and adds unsafe-field checking for the specs and releases trees. E-02 edits `evaluate_durable_carrier`'s detail composition, a different function, and this plan mints no rule id and touches no registry entry. The runner isolates each execute item in its own worktree and merges through a revalidation gate, so same-file edits in different functions are not a hazard. One real interaction is worth stating: if `ynhst5` lands first it may ADD findings to the census E-01 takes, so E-01 must be re-run at execution rather than trusting F-02, which E-01 already requires for an unrelated reason.

### OQ-06: What must `Drift` do with a non-conforming detail at runtime, given a raise either silently drops findings or crashes the checker?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: ESCALATED AT REVIEW (2026-10-07). E-04 as written raises `ValueError` in production. Measured (F-05, F-06, F-17): where a caller is fail-isolated, the raise DROPS that evaluator's whole sweep silently (96 -> 49 findings; a blocking pre-transition finding disappears, so a gate passes what it should refuse); where it is not, `aw check all` exits 2. And because several details echo AUTHORED values (`Gate-Ref`, frontmatter ids), a future author, not a future code edit, can trigger it, so an empty live population does not make the raise safe. Options: (a) the constructor NORMALIZES rather than raises: marked elision to `MAX_DESCRIPTIVE_LEN` and control-character neutralization, so every detail is conforming by construction and nothing is lost silently (the elision is visible; full text via `recovery`); E-06 then names normalization as the enforcement point. (b) raise only under a strict mode enabled in the test suite, normalize in production, so tests catch a producer regression while users never lose findings. (c) keep the production raise and additionally make every producer of authored-echo details pre-bound its input and every caller report rather than swallow the exception, which widens `- Scope-Paths:` to at least `specs`, `research_index`, `backlog`, `ipd_lint` and the `check_type` fan-out. Reviewer recommendation: (b), which keeps the item's structural-refusal intent and the "a check must never crash" contract. Answering this rewrites E-04, E-05, E-06 and V-04, so it must be answered before approval.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the per-surface census with the exact command for each of `aw check all`, `aw attention --check`, `aw doctor` and `aw ipd lint` over the pending plans: total findings, count exceeding `A.MAX_DESCRIPTIVE_LEN`, the longest length, and the per-rule and per-severity breakdown. State explicitly how each figure differs from F-02 and name any surface that could not be exercised and why. Do NOT proceed to E-04 on the strength of F-02's numbers.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the re-run census for every surface showing ZERO findings exceeding the bound. Paste the before-and-after locator lists for `check.ipd-uncarried-obligation` and `check.ipd-carrier-finished-unverified`, showing the SAME set of plans failing each rule (a changed set fails this item). State which route OQ-04 was resolved to, with the measurement behind it. Paste one full before-and-after detail string for each rule so a reviewer can judge what an operator lost. Paste `git diff` showing the rule ids and `carrier_severity_for_plan` are unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the arithmetic for each changed `doctor` site showing its composed worst-case total within the bound (not merely the slice width). Paste a driven example of a probe failure whose message exceeds the slice, showing the visible elision marker in the emitted detail. Paste the `aw doctor` census re-run showing no over-bound finding.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a `python3 -c` session showing `ValueError` raised, with its message, for an over-bound detail, a newline-bearing detail and a control-character-bearing detail, via ALL THREE routes (`Drift(...)`, `d._replace(detail=...)`, `Drift._make([...])`). Paste the SAME session showing a conforming construction succeeds and that `isinstance(d, tuple)`, `d[2]`, `d._asdict()`, `d._fields`, `sorted([...])` and `d._replace(severity="info")` all behave as before. Paste `git diff` showing the validation CALLS `is_safe_descriptive` rather than re-deriving the rules, and that `attention_contract` is unmodified. Paste the exit codes of `aw check all`, `aw attention --check` and `aw doctor` showing each matches its pre-change value and that NONE crashed, AND paste the per-rule finding counts before and after showing NO rule's count dropped (a swallowed refusal shows up as a silent drop, not a crash; F-05).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the FAILING run of `python3 -m pytest tests/test_drift_detail_bound.py -o addopts=""` against the pre-E-04 type (naming exactly how the revert was done), then the PASSING run after restoring. Paste the BARE full-suite `python3 -m pytest` with its `N passed` summary line, and name any test that needed changing because it constructed an over-bound fixture detail. Paste the output of `aw ipd lint --phase pre-transition` on a real plan, proving the transition gate still works (F-06). Confirm by inspection and state explicitly that the new module contains no `inspect`, `ast`, regex-over-source, symbol census or line-count assertion (GUIDING_PRINCIPLES P16), and that the whole-surface census case is present.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the spec diff showing Section 8.8 now states the bound covers a tool-composed drift detail and names the constructor refusal as the enforcement point. Confirm by inspection that NO existing bullet was weakened, in particular that "Over-length values are a contract violation, not silently truncated" is byte-identical, and that requirement F10 and criterion A14 are unchanged. Confirm the spec's `- Status:` and `## Workflow history` are unchanged and that no `aw specs set` was run. Confirm the file was NOT renamed. Paste `aw check` output showing no new finding on the amended spec.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `CHANGELOG.md` entry and confirm it names what a user notices rather than the internal mechanism. Paste the recorded redundancy judgement for each existing bound assertion (including Order 01's lane cases), naming each as kept or removed with the reason; a removal with no reason fails this item. Paste `aw sanitize --agent` showing no finding on the changed files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change with an ordering that cannot be split: the refusal is the deliverable, and E-01 through E-03 exist because measurement proved the refusal CRASHES the checker over a dirty population (F-05). Landing the cleanup without the refusal would leave the gap the backlog item filed; landing the refusal without the cleanup would break `aw check` and the plan transition gate. The spec amendment must ship with the refusal because the contract it enforces is not written down today (F-10).

Execution requires explicit human approval first; this plan is authored `to-review` and carries no `- Readiness:` field, which is `/plan-review`'s output to write and never the author's. It declares `- Item-Dependencies: executed:9sbfea` and the edge is load-bearing: the lane producer's worst reachable composition exceeds the bound today, so a refusal landing before Order 01 would raise inside `aw attention --check`. The runner re-checks dependencies at dispatch and will mark this item `dependency-blocked` rather than run it early; an agent executing the Set by hand must honor the same order. Commit through `aw commit 62pkkg -- <paths>` with only this plan's declared paths, never `git add -A` and never a push. PASTE THE ACTUAL RUNNER OUTPUT for every claim; a green suite claimed without its pasted output does not satisfy the execution contract. `- Scope-Paths:` is a DECLARATION the runner reconciles, not a stop condition: an out-of-scope edit is made and then justified at finalize with `--scope-reason <path>=<why>`. POST-GATE LIFECYCLE MOVE (PR-006): once `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence, the transition is tooled; when `aw oc run`/`aw agy run` dispatched this plan the runner performs `aw ipd begin`/`aw ipd finalize` itself (an in-lane call is refused by design), and in a manual run the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Blocking OQ-06 must be answered before approval.
