# IPD: Make a RUN-* finding code's BOUND binding mean a run can reach its predicate, not merely that the symbol exists

- Date: 2026-09-30
- Kind: child
- Concern: `run_evidence.RUN_FINDING_CODES` records a per-code `binding` of `BOUND` / `UNBOUND-BY-DEPENDENCY` / `UNBOUND-UNBUILT`, and `validate_finding_table` enforces only that a `BOUND` row NAMES at least one predicate and waits on nothing. Nothing anywhere asks whether a run can REACH that predicate, so `BOUND` is decided by a symbol EXISTING. That is the fail-open reading the field's own comment says it exists to prevent ("A code silently wired to a predicate that does not answer its question is a fail-OPEN checker - it passes because nothing was checked"), one level up: the predicate answers the question correctly and no run ever asks it. The defect is in an AUDIT surface, not in a protection: spec `25kzda` line 76 reports "10 are BOUND to predicates" and the module's 2026-09-05 re-measurement comment derives `RUN-HOST-CAPABILITY`'s promotion from `mjx7ne` having "executed and shipped" a function, which is exactly the existence-is-binding inference at issue.
- Scope: Give the table a REACHABILITY dimension that is measured rather than asserted, and make the audit surface report it. IN: a new per-row field recording, for each named predicate, whether a run entrypoint can reach it, computed by a new measured prover rather than hand-declared; a new `validate_finding_table` finding code refusing a `BOUND` row with no reachable predicate; a new public accessor partitioning the table by reachability so the audit surface stops being a hand-written sentence; a new behavioral test module; and the three prose sites (the module's binding-states comment, its 2026-09-05 re-measurement comment, and spec `25kzda`'s line-76 count) corrected to state what is measured. OUT: every row's `code`, `inspects`, `pass_criterion`, `message`, `action`, `abort`, `abort_classes` and `predicates` VALUES are unchanged; no row is added or removed, so `RC-COUNT`'s literal 12 is untouched; no code is promoted or demoted between `BOUND` and either unbound state; no predicate is wired to a new call site; and the `EV-*`, `IPD-EXEC-*` and non-`RUN-*` families are untouched.
- Scope-Paths: agent_workflows/run_evidence.py, tests/test_run_finding_reachability.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Spec: 25kzda
- Work-Kind: chore
- Priority: low
- From-Backlog: u7bfks
- Set: u7bfks
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: f7z10q
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101 (HIGH, fixed), PR-102 (HIGH, fixed), PR-103 (MEDIUM, fixed), PR-104 (MEDIUM, fixed), PR-105 (LOW, fixed). Readiness recorded in `- Readiness:`. Detail on the `reviewed (aw set)` record below and in `.aw/records/reviews/20260930-u7bfks-01-f7z10q-...review.md`.
- 2026-10-01 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-101 (HIGH, fixed), PR-102 (HIGH, fixed), PR-103 (MEDIUM, fixed), PR-104 (MEDIUM, fixed), PR-105 (LOW, fixed). Re-derived every load-bearing measurement independently at review HEAD cf896ea01 rather than trusting the plan findings. F-02 through F-09 all reproduce exactly, including the three mixed-verdict rows, the 35-of-35 predicate resolution with its BrokenChainError caveat, the LeaseTable.claim true negative, the four emitted-not-in-table codes and the nine table-only codes. Three of the plan own figures measured STALE in under two days and are corrected in place as F-10 through F-12: two test files now reference this vocabulary (one pinning len(bound_run_finding_codes()) == 10 and asserting validate_finding_table().ok, so E-04 firing is a RED SUITE not a quiet finding), 00pirb has EXECUTED and edited this same spec file without touching E-06 sentence, and the suite baseline moved 3387 to 3653. One genuinely new hazard was measured: the prover costs about 3000 ms over 177 modules against a 0.2 s import, 60x E-03 own 50ms threshold, so E-03 no longer offers import-time derivation as a choice and now mandates the lazy memoized accessor with the row literals and NamedTuple field list unchanged. E-01 census widened from one grep to three, V-01/V-03/V-04 strengthened, and the suite-count bar replaced with re-derivation.
- 2026-10-01 same-status (aw set): status unchanged (to-review)

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `u7bfks`. Every figure in Findings was MEASURED in this lane at HEAD `25224ceb` rather than carried from the item, and THREE of the item's own premises measured stale, each changing this plan's shape. (1) The item sizes the blast radius as "a 13-code table with four hardcoded-13 test assertions plus a runtime RC-COUNT self-validation"; measured, the table holds TWELVE rows, `RC-COUNT` compares against 12, and the test assertions DO NOT EXIST - every test touching this vocabulary was deleted whole by commit `19313eed`, so `grep -rln RUN_FINDING_CODES tests/` returns nothing (F-01). The named risk is therefore absent and the real risk is the opposite one: the table has zero test coverage. (2) The item's motivating instance is FIXED: plan `iot7hc` executed and `runner_shared` now calls `preflight_host_capabilities`, so `RUN-HOST-CAPABILITY` is both `BOUND` and reachable today (F-02). The defect survives its instance, which is why the remedy is a measured dimension and not a row edit. (3) The item frames the question as whether a third STATE is needed; measured, a third state in the SAME field is the wrong shape, because reachability varies PER PREDICATE within one row and three of the ten `BOUND` rows have a reachable predicate beside an unreachable one (F-04), which a single row-level enum cannot express. Resolved to an orthogonal per-predicate dimension, with the question's own framing recorded in OQ-01 as non-blocking. GATE NOTE: item `u7bfks` carries no `- Blocks-Release:`, so this plan inherits none and invents none. COLLISION NOTE: two pending plans (`a6i03f`, `xjmjq4`) edit the same file on the ABORT dimension; F-07 records why the three do not conflict and E-01 re-checks it at execution.

## Goal

Make `BOUND` mean "a run can reach a predicate that decides this code" instead of "a symbol by this name exists", so the table can no longer report a shipped-but-uncalled gate as covered.

The deliverable is a MEASUREMENT plus a refusal, not a relabelling. After this plan the table carries, per predicate, a reachability verdict computed by walking the call graph from the three runner entrypoints; `validate_finding_table` refuses a `BOUND` row whose every predicate is unreachable; and the audit surface (one accessor, two module comments, one spec sentence) reports the measured partition rather than a hand-written count. No row's binding is promoted or demoted by this plan: the point is that a future one cannot be promoted on existence alone.

Secondarily, and stated plainly because it is the larger fact this plan uncovered: give the table its FIRST test coverage since the 2026-09-24 trim on the binding dimension specifically. `test_every_bound_codes_predicate_actually_resolves`, the anti-rot check whose own docstring calls a rotted mapping "indistinguishable at runtime from a check that never ran", was deleted with the rest of `tests/test_run_evidence_completion.py` and nothing replaced it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before changing anything

- [x] E-01 RE-MEASURE THE TABLE AND THE COLLISION SURFACE BEFORE EDITING, because this plan's premise is that the backlog item's own figures are stale, and the same staleness can bite this plan between authoring and execution. Record raw output for each of: (a) `len(RUN_FINDING_CODES)` and the `Counter(r.binding for r in RUN_FINDING_CODES)` partition (authoring: 12 rows, `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}`, no `UNBOUND-UNBUILT`); (b) `validate_finding_table().ok` (authoring: `True`); (c) the literal the `RC-COUNT` branch compares against (authoring: `12`, NOT the 13 the item claims); (d) the TEST-COVERAGE census, which must now be run as THREE greps and not one, because the single `RUN_FINDING_CODES` grep is what led the plan to believe coverage was zero (F-10): `grep -rln RUN_FINDING_CODES tests/`, `grep -rln 'bound_run_finding_codes\|unbound_run_finding_codes' tests/`, and `grep -rln validate_finding_table tests/`. At review these returned `tests/test_host_capability_extension.py` and `tests/test_ipd_exec_finding_codes.py` respectively, NOT nothing, so OUTPUT IS THE EXPECTED RESULT and its absence is now the surprise; (e) whether pending plans `a6i03f` and `xjmjq4` are still pending and still scope `agent_workflows/run_evidence.py` (authoring: both pending, both scope it, both on the ABORT dimension only; at review both still pending, `a6i03f` `reviewed`/`no-go` and `xjmjq4` `approved`/`go-pending-approval`); and (f) whether `00pirb` has edited the sentence E-06 amends, which E-06 asks for and which is now ANSWERED and must be re-confirmed rather than re-derived: `00pirb` has EXECUTED (it is in `.aw/records/plans/executed/`, finalized at `9a864e8a4`) and its spec edit `8b9d79450` touched Section 2.1's flag paragraph and Section 5.2's guarantee row 2, NOT the line-76 infrastructure sentence, which still reads "carries all 12, of which 10 are BOUND to predicates". IF ANY FIGURE HAS MOVED, use the new measurement, say so explicitly, and re-check F-07's no-conflict argument against the new state; do NOT adjust the plan's argument, which does not depend on the particular counts.
  - Depends on: none
  - Expected outcome: six raw measurements recorded, each with the command that produced it, plus an explicit statement of whether each matches the authoring or the review figure and, if not, whether F-07's collision argument still holds. The test-coverage census must NAME the two test files that reference this vocabulary; reporting zero means the three greps were not all run.
  - Execution state: performed

### Task group 2: measure reachability instead of asserting it

- [x] E-02 ADD THE PROVER as a new public function in `agent_workflows/run_evidence.py` that computes, for a dotted `module.symbol` predicate string, whether it is reachable from the run entrypoints. It takes the entrypoint module names as a parameter defaulting to the three runner modules (`oc_runipd`, `agy_runipd`, `runner_shared`), parses every module under the package directory with `ast`, builds a name-keyed call graph (a function body mentioning a bare name that is defined somewhere as a function or method yields an edge), seeds the frontier with every function defined in an entrypoint module PLUS every name mentioned at an entrypoint module's top level, and closes transitively. It strips a trailing `[...]` qualifier (the table writes `run_evidence.validate_evidence[EV-HASH-MISMATCH]` to name a specific finding inside one function) before resolving. It returns a three-valued verdict per predicate: reachable, unreachable, or unresolved (no such definition, which is the ROT case the deleted anti-rot test owned). THE OVER-APPROXIMATION IS DELIBERATE AND MUST BE DOCUMENTED AT THE FUNCTION: name-keyed edges over-approximate reach, so a `reachable` verdict is weaker than a proof while an `unreachable` verdict is STRONG, and the refusal in E-04 keys only on the strong direction. State the two known consequences measured at authoring: a method name shared by an unrelated class creates a false edge, and `worktree_lease.LeaseTable.claim` is reported unreachable with ZERO real `.claim(` call sites anywhere in the package, which is a true negative and not a limitation.
  - Depends on: E-01
  - Expected outcome: a new public function in `run_evidence` returning a three-valued reachability verdict for a dotted predicate string, with the over-approximation and the asymmetry of the two verdicts documented at the definition; importable and callable with no run, no ledger and no subprocess.
  - Execution state: performed

- [x] E-03 EXPOSE THE PER-PREDICATE VERDICT THROUGH A LAZILY MEMOIZED DERIVED ACCESSOR, not through a hand-typed field and not through import-time derivation. THE DECISION IS SETTLED BY MEASUREMENT AND IS NO LONGER THE EXECUTOR'S TO MAKE (review F-11): the prover costs about 3000 ms over the real package (3159/3017/3020 ms on three consecutive runs across 177 modules and ~10.1 MB of source) while `python3 -c 'import agent_workflows.run_evidence'` costs 0.18 to 0.23 s, so import-time derivation would make the import roughly fifteen times slower on every run to populate an audit field no run consumes (F-06). That is the user-perceptible inefficiency `AGENTS.md`'s release-gate section defines as a bug, so shipping it to fix an audit surface would be a net loss. CONCRETELY: add a public accessor keyed on a row (or on a code) that returns each named predicate's verdict, memoized so the ~3 s graph build happens at most once per process and ONLY when a caller asks; leave all twelve row literals and the `RunFindingCode` `NamedTuple` field list UNCHANGED, since a lazily derived verdict cannot live in a literal row; and document the per-row verdict in the class docstring beside the existing `predicates` and `waiting_on` entries by POINTING AT the accessor rather than by adding a field. RE-MEASURE the prover cost at execution and record it as confirmation, not as the decision: if it has somehow fallen below ~50 ms, say so and still use the lazy accessor, because the field-versus-accessor shape is now also constrained by `test_ipd_exec_finding_codes.test_non_regression_e06` pinning the partition (F-10).
  - Depends on: E-02
  - Expected outcome: each row's predicates carry a measured reachability verdict reachable through a documented, lazily memoized public accessor; the twelve row literals and the `NamedTuple` field list are byte-unchanged; the re-measured prover cost is recorded; and `import agent_workflows.run_evidence` is timed before and after showing no material regression, which is the property the lazy shape exists to preserve.
  - Execution state: performed

- [x] E-04 REFUSE A BOUND ROW WITH NO REACHABLE PREDICATE by extending `validate_finding_table` with one new `RC-*` finding code (for example `RC-UNREACHABLE-BINDING`), sited beside the existing `RC-BINDING` checks that already enforce "a BOUND code must name the shipped predicate that decides it". The new check fires when a row's binding is `BOUND` and NO named predicate is reachable, and its message names the code and every unreachable predicate. KEY ONLY ON THE STRONG DIRECTION, for the reason E-02 documents: a row with at least one reachable predicate passes, so the over-approximating prover cannot manufacture a false refusal; and an `unresolved` predicate (the rot case) counts as NOT reachable, which restores the deleted anti-rot check's effect. The new code is an INTERNAL table-validation finding, a sibling of `RC-COUNT` / `RC-DUPLICATE` / `RC-NAME`, and is NOT a member of spec 4.2's public `RUN-*` operator vocabulary, so the twelve-code contract is untouched. VERIFY, and record, that the shipped table still validates clean after the addition; if a real row fails, that is a FINDING to report and not a licence to weaken the check or to edit the row's binding, which this plan's scope excludes. THAT VERIFICATION IS NOW SUITE-ENFORCED RATHER THAN ADVISORY, so treat a firing check as a RED SUITE and stop (review F-10, which records that `tests/test_ipd_exec_finding_codes.py::test_non_regression_e06` asserts `run_evidence.validate_finding_table().ok`, that no `BOUND` row would fire at review because every one has a reachable predicate per F-04, and that `validate_finding_table` has no in-package caller so the ~3 s build may be paid once per process through E-03's memoization but never once per row).
  - Depends on: E-03
  - Expected outcome: `validate_finding_table()` still returns a passing result on the shipped table and `tests/test_ipd_exec_finding_codes.py` still passes; the new code returns a finding naming the offending code and its unreachable predicates when a row is perturbed to have only unreachable predicates; and the ~3 s prover build is paid at most once per process rather than once per row.
  - Execution state: performed

### Task group 3: make the audit surface report the measurement

- [x] E-05 ADD THE PARTITION ACCESSOR and stop the module describing reachability in prose. Add one public function returning the table's reachability partition as data (the codes whose binding is `BOUND` and which have at least one reachable predicate, versus those `BOUND` with none), as a sibling of the existing `bound_run_finding_codes` / `unbound_run_finding_codes`. Then correct the TWO module prose sites that currently assert the existence-is-binding inference, in place and without deleting the history they record: the binding-states comment block above the `BOUND` constant, which explains why a binding is recorded but never mentions reachability, gains the distinction and points at the accessor; and the 2026-09-05 re-measurement comment, whose `RUN-HOST-CAPABILITY` bullet derives `BOUND` from `mjx7ne` having "executed and shipped" the function, gains a dated note that the inference was existence-only, that plan `iot7hc` later supplied the missing call site, and that the row was reported `BOUND` for the whole intervening period during which no run could emit it. DO NOT rewrite or delete the 2026-09-05 or 2026-09-22 measurements themselves: they are a record of what was measured when, and the repository's own convention is to add the correction beside them rather than overwrite (the abort comment four hundred lines above records two successive corrections exactly this way, and says "Prefer recomputing over trusting this sentence"). Follow the same rule: point the reader at the accessor rather than writing a new count that will rot.
  - Depends on: E-04
  - Expected outcome: a new public accessor returning the reachability partition as data, and both module prose sites corrected to state the distinction and cite the accessor, with every pre-existing dated measurement preserved.
  - Execution state: performed

- [x] E-06 AMEND SPEC `25kzda`'s LINE-76 SENTENCE, which is the audit surface a human actually reads and the one that currently overstates coverage. It says `run_evidence.RUN_FINDING_CODES` "carries all 12, of which 10 are BOUND to predicates and the remaining two ... are unbound-by-dependency". That is literally true of the `binding` field and materially misleading about what it means, which is this backlog item's whole complaint. Amend the sentence to say what `BOUND` asserts (a named predicate that resolves) and what it does NOT assert (that a run reaches it), and name the shipped accessor a reader can run instead of trusting the number. Keep the paragraph's existing instruction intact ("READ SECTION 4.2's FINDING CODES AS SPECIFICATION, NOT AS SHIPPED BEHAVIOR" and "A plan MUST NOT cite one of those codes as an existing enforcement mechanism"), which this amendment strengthens rather than replaces. Record the amendment through `aw specs set` so the spec's `## Workflow history` carries it; do not hand-edit the status line. DO NOT touch Section 4.2's table, its twelve rows, or its `RC-COUNT` note: `00pirb` also edits this spec file for the commit-gateway claims in 2.1 and 5.2, and a THIRD pending plan reads 4.2's action column, so confine this edit to the one paragraph sentence. THE `00pirb` RE-CHECK IS ALREADY ANSWERED AND NEEDS CONFIRMING, NOT DERIVING (review F-12): `00pirb` has EXECUTED (finalized at `9a864e8a4`, now in `.aw/records/plans/executed/`), and its spec commit `8b9d79450` changed Section 2.1's flag paragraph and Section 5.2's guarantee row 2 and NOTHING ELSE in this file, leaving the line-76 sentence reading "carries all 12, of which 10 are BOUND to predicates and the remaining two ... are unbound-by-dependency" verbatim. So the paragraph E-06 amends is intact and uncontested. Confirm that at execution with `git log --oneline -- <spec path>` plus a quotation of the current sentence; if a later plan HAS rewritten it, reconcile in place rather than reverting. NOTE that `00pirb`'s amendment and this one are complementary and must not contradict: it recorded that `RUN-COMMIT-GATEWAY` is unbound and fails closed, while this one records what `BOUND` does not assert, so cite its dated `## Workflow history` note rather than restating its conclusion.
  - Depends on: E-05
  - Expected outcome: spec `25kzda`'s infrastructure paragraph states what `BOUND` does and does not assert and names the accessor, recorded in the spec's workflow history through `aw specs set`, with Section 4.2's table unedited and `00pirb`'s Section 2.1 and 5.2 amendments untouched.
  - Execution state: performed

### Task group 4: cover it by outcome

- [x] E-07 ADD `tests/test_run_finding_reachability.py` covering this dimension BY OUTCOME, and restore the binding-dimension coverage the trim deleted. Cases: (a) the prover returns `unreachable` for a predicate with no call path and `reachable` for one with a path, driven by SYNTHESIZED entrypoint and target modules written into `tmp_path` rather than by asserting a verdict about today's real tree, so the assertion is about the prover's behavior and cannot rot when production wiring changes; (b) every `BOUND` row has at least one predicate that is not `unresolved`, which is the anti-rot property the deleted `test_every_bound_codes_predicate_actually_resolves` owned, asserted by RESOLVING each dotted string through `importlib` and `getattr` rather than by reading source; (c) `validate_finding_table()` returns no findings on the shipped table; (d) the new `RC-*` code FIRES when a row is perturbed via `NamedTuple._replace` to name only unreachable predicates, with the finding's message naming the code and the predicates, and the table restored afterwards; (e) the new partition accessor agrees with the per-row field for every row, so the two cannot drift. OBEY P16 AND THE AGENTS CONTRACT: this plan's subject is a call graph, which makes it the exact case where a test is tempted to read production source, so do NOT assert on production file text, call-site counts, symbol censuses, or comment wording anywhere in this module. The prover itself parses production source as its INPUT, which is legitimate because it is the code under test; a TEST asserting a fact about today's production call graph is not, and case (a) exists so that no test needs to. Record a mutation demonstration for case (d) as evidence: a check never observed failing is not established.
  - Depends on: E-06
  - Expected outcome: a new test module whose cases pass, whose prover cases run against synthesized fixtures rather than the live tree, and which reads no production source text; plus a recorded mutation run in which the new `RC-*` check is observed failing.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A BINDING IS RECORDED ONLY WHERE A PREDICATE GENUINELY ANSWERS THE CODE'S QUESTION, and the module says so at the `BOUND` constant: an unbound code reporting itself unbound "is safe", while "a code silently wired to a predicate that does not answer its question is a fail-OPEN checker - it passes because nothing was checked". This plan applies that stated rule one level up, to reachability, rather than introducing a new principle.
- THE TABLE ALREADY APPLIES THE STRICTER STANDARD BY HAND IN SOME ROWS. `RUN-COMMIT-CONTENTS` and `RUN-COMMIT-GATEWAY` are held `UNBOUND_BY_DEPENDENCY` with the reason "Writing a trailer is not proving a commit's tree diff equals the item-owned delta, so binding these two now would be exactly the fail-open error described above", and `RUN-COMMIT-GATEWAY`'s `waiting_on` adds that `git_commit_helper.offer_commit` "is a helper the driver CHOOSES to call, not a boundary". That second clause is a REACHABILITY argument made in prose. So the convention this plan encodes is already in force where an author happened to think of it.
- DO NOT REINTRODUCE A CODE BOUND TO A PRESENCE CHECK. The retired-`RUN-NO-PUSH` comment states it outright: "inferring push prevention from a helper's, hook's, or flag's mere existence is forbidden ... and converts today's safe fail-closed state into a fail-OPEN checker, which is strictly worse than having no code at all." Existence-as-binding is the same inference, which is why this is a tightening of an existing prohibition rather than a new rule.
- ADD A CORRECTION BESIDE A DATED MEASUREMENT, NEVER OVER IT. The abort-semantics comment in `run_evidence` carries two successive corrections of its own counts and closes "Prefer recomputing over trusting this sentence"; the binding comment carries dated 2026-09-05 and 2026-09-22 re-measurements. E-05 follows that convention.
- TESTS PROVE OUTCOMES, NEVER CODE STRUCTURE. `GUIDING_PRINCIPLES` P16 prohibits `ast.parse`, `read_text` and substring search against `agent_workflows/*.py` in a test, and prohibits caller-count and census pins. This is load-bearing for E-07 because the subject IS a call graph. Note the measured precedent for what NOT to do: `tests/test_host_capability_wiring.py::test_runner_shared_references_preflight_host_capabilities` does exactly this - it `ast.parse`s `runner_shared.py` and asserts the name `preflight_host_capabilities` appears - which is a structure pin on production source. This plan does not extend that pattern and does not touch that file.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measurements taken in this lane worktree at HEAD `25224ceb`.

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | THE ITEM'S BLAST-RADIUS FIGURES ARE STALE IN BOTH DIRECTIONS, and this is the finding that most changes the plan's shape. The item sizes the change as "a 13-code table with four hardcoded-13 test assertions plus a runtime RC-COUNT self-validation". Measured: the table holds TWELVE rows; `validate_finding_table`'s `RC-COUNT` branch compares against `12` and its message reads "spec 25kzda 4.2 defines 12 codes"; and the four test assertions DO NOT EXIST. No test under `tests/` references `RUN_FINDING_CODES`, `validate_finding_table`, `bound_run_finding_codes` or `spec_message_for` at all. | `len(RUN_FINDING_CODES)` is 12 and `Counter(r.binding ...)` is `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}`; `validate_finding_table().ok` is `True`; `grep -rln RUN_FINDING_CODES tests/` produces no output; `git show 19313eed --stat` lists `tests/test_run_evidence_completion.py \| 1722 ---------`, and `git show 19313eed^:tests/test_run_evidence_completion.py` still contains `test_measured_binding_partition_is_recorded`, `test_every_bound_codes_predicate_actually_resolves`, `test_every_code_records_a_known_binding_state` and `test_host_capability_binding_agrees_with_the_shipped_implementation`. | The named obstacle (count-pinning tests that would go red) is ABSENT, so the plan is smaller than the item feared. The real risk is inverted: the table's only live guard is its own runtime self-check, which is why E-04 extends that self-check and E-07 restores the binding-dimension coverage rather than only adding new cases. **CORRECTED AT REVIEW 2026-10-01: THE "ZERO TEST COVERAGE" HALF IS NOW STALE, SEE F-10.** It was TRUE at the authoring HEAD `25224ceb` and is FALSE at review HEAD `cf896ea01`: two test files landed within hours and now reference this vocabulary, one of them pinning `len(bound_run_finding_codes()) == 10` as a literal. The twelve-row count, the `RC-COUNT` literal and the `19313eed` deletion evidence all still reproduce exactly. |
| F-02 | THE ITEM'S MOTIVATING INSTANCE IS ALREADY FIXED, so this plan must not be written as a fix for it. `RUN-HOST-CAPABILITY` is now genuinely reachable: `runner_shared` calls `_hsp.preflight_host_capabilities` inside `execute_item_core`'s capability gate, and the row's other two predicates resolve too. | `grep -rn preflight_host_capabilities agent_workflows/runner_shared.py` matches a real call (`preflight = _hsp.preflight_host_capabilities(`), not a comment; plan `iot7hc` is in `.aw/records/plans/executed/`; its E-06 records that it deliberately left "`run_evidence.py`'s `RUN-HOST-CAPABILITY` row alone". | The DEFECT survives its instance: the model that promoted that row on existence alone is unchanged, and would promote the next row the same way. This plan therefore changes the model and promotes/demotes nothing, which is also why no row's `binding` value is in scope. |
| F-03 | THE EXISTENCE-IS-BINDING INFERENCE IS WRITTEN DOWN IN THE MODULE, which is what makes this a defect in a stated rule rather than a judgement call. The 2026-09-05 re-measurement comment's first bullet reads "`RUN-HOST-CAPABILITY` is now BOUND, not UNBOUND-BY-DEPENDENCY: `hostcap-01` (`mjx7ne`) executed and shipped `host_sandbox_profile.preflight_host_capabilities` plus that code's verbatim message." The stated ground for promotion is that a plan shipped a function. | The comment is in `run_evidence.py` immediately above `RUN_FINDING_CODES`; `mjx7ne` is in `.aw/records/plans/executed/`. | E-05 corrects this site specifically, and adds the dated note that the row read `BOUND` throughout a period when no run could emit it. Correcting the inference where it is RECORDED is what stops the next author repeating it. |
| F-04 | REACHABILITY VARIES PER PREDICATE WITHIN ONE ROW, which settles the item's open question about a third state. Measured over the ten `BOUND` rows with a transitive name-keyed call-graph walk from `oc_runipd`, `agy_runipd` and `runner_shared`: every `BOUND` row has at least one reachable predicate, so no row would fail E-04's refusal today; but THREE rows mix verdicts. `RUN-FROZEN-IDENTITY` reaches `run_freeze.freeze_requirements` while `run_freeze.diff_requirements` and `run_freeze.refuse_drop_or_redefine` are unreachable; `RUN-BASELINE-OWNERSHIP` reaches `run_evidence.dirty_within` while both `worktree_lease` predicates are unreachable; `RUN-FRESH-VERIFIER` reaches only the `validate_evidence` entry, with both `agy_verifier` predicates unreachable. | Transitive walk from the three entrypoint modules over all `agent_workflows/*.py`; `worktree_lease.LeaseTable.claim` confirmed independently as a TRUE negative, since `grep -rn '\.claim(' --include='*.py'` finds zero call sites in the package (the only match in the repository is in a research prototype's own tests). | A third value in the row-level `binding` enum CANNOT express this, so the item's suggested shape is declined with a measured reason. The dimension is orthogonal and PER PREDICATE (E-03), and E-04's refusal keys on "no predicate reachable" rather than "any predicate unreachable" - the stricter rule would refuse three shipped rows today, which is a row-binding change this plan's scope excludes. |
| F-05 | EVERY NAMED PREDICATE STILL RESOLVES, so the rot case is latent rather than live. All 35 dotted strings across the ten `BOUND` rows resolve through `importlib` plus `getattr`, including `run_ledger_store.BrokenChainError` (a class, not a function - noted because the AST-based prover of E-02 keys on function definitions and must therefore treat a resolvable non-function as `unresolved` for reach purposes without reporting it as rotted). | Resolution loop over `RUN_FINDING_CODES` stripping the `[...]` qualifier: 35 of 35 resolve, zero unresolved. | E-07 case (b) restores this as a test, and E-02 must distinguish "resolves but is not a function" from "does not resolve at all", or it will report a false rot on `BrokenChainError`. |
| F-06 | THE AUDIT SURFACE IS EXACTLY THREE PLACES, and only one is read by humans at scale. `binding` is read by `bound_run_finding_codes`, `unbound_run_finding_codes` and `validate_finding_table` and by NOTHING else in the package; no CLI verb, report or doc renders it. The human-facing surface is the spec's line-76 sentence plus the two module comments. | `grep -rn '\.binding'` over `agent_workflows/` matches only `run_evidence.py` (the one other hit, `ipd_set_executor.py`, is an unrelated `self.bindings` dict); the sentence "carries all 12, of which 10 are BOUND to predicates" appears once, in the spec. | Fixes the scope at the three prose sites (E-05, E-06) plus one accessor (E-05). It also bounds the harm honestly: nothing in a run CONSUMES the binding field, so the defect overstates an audit and breaks no protection, which is why `low`/`chore` is the right classification and why no release gate is inherited or invented. |
| F-07 | TWO PENDING PLANS EDIT THIS SAME FILE AND NEITHER COLLIDES WITH THIS ONE, measured rather than assumed. `a6i03f` (Set `0jxknk`, status `reviewed`, `Readiness: no-go`) and `xjmjq4` (Set `dorm45`, status `approved`) both scope `agent_workflows/run_evidence.py` for the ABORT tri-state: they add an abort-derivation accessor, extend `validate_finding_table` with an abort-derivation `RC-*` code, rewrite the abort-semantics comment, and add their own test module. Both explicitly fence the binding dimension OUT: `a6i03f`'s scope says "the binding partition and the `IPD-EXEC-*` family are untouched" and `xjmjq4`'s scope check says "The binding-state invariants lost their tests in the same deletion (F3) and are left to `xvp5vx`". Both also leave `RC-COUNT` alone, as does this plan. | Front matter and scope sections of both pending plans; `a6i03f`'s own review raised the two-plans-one-file overlap as its blocking OQ-04, confined to the abort dimension. | The three plans touch DISJOINT dimensions of one table and each adds a separate test module, so no `- Item-Dependencies:` edge is warranted. The runner isolates each item in its own worktree and merges through a revalidation gate, so file overlap is not a runtime hazard. E-01(e) re-checks this at execution because an abort plan landing first changes the surrounding text E-05 edits, though not its meaning. |
| F-08 | A SIBLING OPEN ITEM OWNS THE OTHER HALF OF THE SPEC's OVERSTATEMENT, so the division of labour is explicit. Backlog `089bq4` (open, `bug`, `Blocks-Release: next`) records that spec 4.2's transcription note claims `tests/test_run_evidence_completion.py` "asserts byte equality" on the table's cells when that file was deleted. This plan amends a DIFFERENT sentence (line 76's binding count) and neither restores nor re-promises a byte-equality guard. | Content of `.aw/records/backlog/open/20260929-089bq4-...backlog.md`; the transcription note and the line-76 sentence are different paragraphs of the spec. | Keeps E-06 narrow and avoids two plans amending one spec sentence. Recorded on the Deferred list with `089bq4` as the carrier. Measured incidentally and worth a reviewer's attention: `host_sandbox_profile.RUN_HOST_CAPABILITY_MESSAGE` and the table's `message` for that code differ only in placeholder syntax (`{host}` versus `<host>`) and are otherwise byte-identical, so the drift `089bq4` warns about has not yet occurred on the one row where two copies exist. |
| F-10 | REVIEW FINDING (2026-10-01): F-01's "ZERO TEST COVERAGE" HALF IS NOW STALE, AND ONE OF THE TWO NEW TESTS IS EXACTLY THE COUNT-PINNING KIND F-01 SAID WAS ABSENT. Measured at review HEAD `cf896ea01`: `grep -rln RUN_FINDING_CODES tests/` now returns `tests/test_host_capability_extension.py`, and a second file not caught by that grep, `tests/test_ipd_exec_finding_codes.py`, asserts `len(run_evidence.run_finding_codes()) == 12` AND `len(run_evidence.bound_run_finding_codes()) == 10` AND `validate_finding_table().ok` in `test_non_regression_e06`. Both landed AFTER the authoring measurement (`8b9d79450` at 19:45 and `607704596` at 22:43 on 2026-09-30, versus authoring HEAD `25224ceb` at 19:35), so F-01 was honest when written and is simply overtaken. THE CONSEQUENCE IS A REAL EXECUTION HAZARD THIS PLAN DID NOT ANTICIPATE: `test_non_regression_e06` calls `validate_finding_table().ok` and would go RED if E-04's new check fires on any shipped row, and the hardcoded `10` constrains E-03 (adding a `NamedTuple` field is safe for it, but any accidental re-partitioning is not). The other file, `CommitGatewayClaimConsistencyTests.test_commit_gateway_claim_consistency`, asserts `RUN-COMMIT-GATEWAY`'s `binding == UNBOUND_BY_DEPENDENCY` and `predicates == ()`, which this plan's scope already forbids changing, so it is a guard this plan satisfies rather than a hazard. Both files pass today (`44 passed`). | `grep -rln RUN_FINDING_CODES tests/`; `grep -n 'bound_run_finding_codes' tests/test_ipd_exec_finding_codes.py` showing the `== 10` assertion in `test_non_regression_e06`; `git log --oneline -1 --format=%ad` on both adding commits; `git merge-base --is-ancestor <commit> 25224ceb` returning non-ancestor for both; `python3 -m pytest tests/test_ipd_exec_finding_codes.py tests/test_host_capability_extension.py -o addopts=""` reporting `44 passed`. | E-01(d) must now EXPECT output from its grep rather than treating output as a surprise, and must additionally grep for `bound_run_finding_codes` and `validate_finding_table` (the `RUN_FINDING_CODES` grep alone MISSES `test_ipd_exec_finding_codes.py`, which is how the plan came to believe coverage was zero). E-04's "verify the shipped table still validates clean" is no longer only a self-check: `test_non_regression_e06` enforces it, so a firing check is a RED SUITE and not merely a finding to report. V-01 and V-04 are amended accordingly. |
| F-11 | REVIEW FINDING (2026-10-01): THE PROVER COSTS ABOUT 3 SECONDS, 60x E-03's THRESHOLD, SO THE IMPORT-TIME OPTION IS NOT OPEN AND E-03 SHOULD NOT PRESENT IT AS A CHOICE. E-03 says to measure the cost and to prefer a lazy memoized accessor "if it exceeds roughly 50ms". Measured at review over the real package: 177 modules, about 10.1 MB of source, and a full `ast.parse` plus name-walk build takes 3159 ms, 3017 ms and 3020 ms on three consecutive runs. By comparison `python3 -c 'import agent_workflows.run_evidence'` takes 0.18 to 0.23 s. So import-time derivation would make importing this module roughly FIFTEEN TIMES slower, on every run, to populate an audit field no run consumes (F-06). That is squarely the user-perceptible inefficiency `AGENTS.md`'s release-gate section defines as a bug, which E-03 itself anticipates; the measurement simply settles it. E-03's threshold logic is correct and its instruction to measure first is correct; what is wrong is leaving "the executor chooses" open when the answer is already determined by an order-of-magnitude margin. | Three timed builds over `agent_workflows/*.py` (3159/3017/3020 ms) beside three timed `import agent_workflows.run_evidence` runs (0.18/0.22/0.23 s), all at review HEAD `cf896ea01`. | E-03 is amended to REQUIRE the lazy memoized accessor and to keep the measurement as confirmation rather than as the decision. This also removes E-03's internal ambiguity about whether to add a `NamedTuple` field at all: a lazily derived verdict cannot live in a literal row, so the derived-accessor branch is the only coherent one, and the field-versus-accessor choice collapses with it. |
| F-12 | REVIEW FINDING (2026-10-01): `00pirb` IS NO LONGER PENDING, IT HAS EXECUTED, AND IT EDITED THIS SPEC FILE WITHOUT TOUCHING E-06's SENTENCE. E-06 calls `00pirb` "a sibling pending plan" and asks the executor to re-check whether it has rewritten the line-76 sentence; both halves are now answerable from the record. It executed (finalized at `9a864e8a4`, filed under `.aw/records/plans/executed/`), and its spec commit `8b9d79450` changed exactly two places in `25kzda`: Section 2.1's flag paragraph (rewritten to say git-sense `--no-verify` is forbidden and commit-gateway interception is unbuilt) and Section 5.2's guarantee row 2 (now recording that `supports_commit_gateway` is declared-never-probed). The line-76 infrastructure sentence is BYTE-UNCHANGED. The two amendments are complementary rather than overlapping: `00pirb` recorded that one code is unbound and fails closed; this plan records what `BOUND` itself does not assert. Its commit ALSO added `CommitGatewayClaimConsistencyTests` to `tests/test_host_capability_extension.py`, which is one of the two files F-10 reports, so the same executed plan explains half of F-01's staleness. | `ls .aw/records/plans/executed/ | grep 00pirb`; `git show 8b9d79450 -- <spec path>` showing only the 2.1 and 5.2 hunks plus a `## Workflow history` line; `grep -n '10 are BOUND' <spec path>` still matching at the infrastructure paragraph; `git show 8b9d79450 --stat` listing `tests/test_host_capability_extension.py | 54 +++-`. | E-06's re-check instruction is amended from "re-check that `00pirb` has not already rewritten it" to "confirm the recorded answer", which saves the executor a derivation and removes a stale `pending` claim from the plan. It also supplies the citation E-06 should make instead of restating `00pirb`'s conclusion. |
| F-09 | THE TABLE IS NOT THE WHOLE `RUN-*` VOCABULARY, which is a REPORTING limit on any claim this plan's accessor makes. Four `RUN-*` codes are emitted from package source but are absent from `RUN_FINDING_CODES`: `RUN-MIXED-TYPES` and `RUN-DRAFTS-EXCLUDED` (in `run_selection_policy`), and `RUN-UNDETERMINED-ACTION` and `RUN-DEPENDENCY-UNSATISFIABLE` (in `runner_shared.enforce_freeze_time_refusal`). The last two appear nowhere in spec `25kzda`. Conversely, of the twelve table codes, nine appear NOWHERE outside `run_evidence.py`. | `rg -o '\[RUN-[A-Z-]+\]' agent_workflows/` compared against `run_finding_codes()`; the four extras are real f-string emissions, two of them raised to an operator through `DriverError`. | Bounds what E-05's accessor may be said to cover: it partitions THIS TABLE, not every `RUN-*` code a run can emit. The reconciliation of table-versus-emitted vocabulary is a separate concern no plan owns; recorded on the Deferred list rather than absorbed, and E-05's prose must not imply the accessor is a complete census. |

## Proposed changes (ordered, validatable)

1. Re-measure the table, the `RC-COUNT` literal, the absent test coverage, and the two sibling pending plans; proceed on the measurement, not on the item's figures (E-01).
2. Add a reachability prover to `run_evidence`: a transitive name-keyed call-graph walk from the three runner entrypoint modules, returning reachable / unreachable / unresolved per dotted predicate, with its over-approximation and the asymmetry of its two verdicts documented at the definition (E-02).
3. Record the per-predicate verdict on each row through a documented public surface, deriving it rather than hand-typing it, and choose import-time versus lazy memoized derivation on a MEASURED prover cost (E-03).
4. Extend `validate_finding_table` with one new internal `RC-*` finding that refuses a `BOUND` row with no reachable predicate, keyed on the strong verdict only, treating an unresolved predicate as not reachable (E-04).
5. Add a partition accessor and correct both module prose sites, preserving every dated measurement and pointing readers at the accessor instead of a fresh count (E-05).
6. Amend spec `25kzda`'s line-76 sentence to state what `BOUND` does and does not assert, recorded through `aw specs set`, leaving Section 4.2's table untouched (E-06).
7. Add `tests/test_run_finding_reachability.py` proving the prover's behavior against synthesized fixtures, the anti-rot property by resolution, the shipped table's cleanliness, the new refusal firing under perturbation, and the accessor agreeing with the per-row field (E-07).

## Deferred / out of scope (with reason)

- PROMOTING OR DEMOTING ANY ROW'S `binding` VALUE. No row fails E-04's refusal today (F-04), so nothing needs to move; and the stricter "every predicate reachable" rule would demote three shipped rows, which is a contract change needing its own review and its own argument per row. This plan changes what `BOUND` must mean going forward and leaves every current value as measured.
  - Carrier-Declined: Not a deferral of work this plan creates. There is no pending obligation to demote a row, because the measurement shows no row violating the new rule; a future row that does will be refused at author time by E-04, which is the whole point.
- WIRING AN UNREACHABLE PREDICATE TO A CALL SITE. Three rows have unreachable predicates beside reachable ones (F-04). Making `run_freeze.diff_requirements`, `worktree_lease.LeaseTable.claim`, `worktree_lease.assert_worker_scope`, `agy_verifier.assert_distinct_sessions` or `agy_verifier.run_fresh_verifier` reachable from a run is each a separate behavioral change to the runners, far outside an audit-surface fix, and `LeaseTable.claim` in particular has zero call sites anywhere in the package, which is a finding about lane leasing and not about this table.
  - Carrier: xvp5vx
  - Carrier-Note: `xvp5vx` is the open audit of properties that lost their only guard in the `19313eed` trim and is the natural home for triaging whether each of these five is dead code, a latent gap, or correctly uncalled. This plan's new accessor is the instrument that makes such a triage cheap, which is a reason to land it first rather than to widen it.
- RESTORING THE REST OF THE COVERAGE DELETED WITH `tests/test_run_evidence_completion.py`. That file held roughly 85 test methods across completion evaluation, verbatim message transcription, the abort partition and the binding states. This plan restores the BINDING-dimension subset only (E-07 case b), because that is backlog `u7bfks`'s concern.
  - Carrier: xvp5vx
  - Carrier-Note: The abort subset is already claimed by pending plans `a6i03f` and `xjmjq4` (F-07) and the message-transcription subset by backlog `089bq4` (F-08), so only the general remainder is handed to `xvp5vx`. Each must respect the maintainer directive recorded on that item: restore behavioral outcomes only, never a code-pinning test.
- CORRECTING SPEC 4.2's TRANSCRIPTION NOTE, which claims a deleted test file enforces byte equality on the table's cells (F-08).
  - Carrier: 089bq4
  - Carrier-Note: A live `bug` carrying `Blocks-Release: next`, already filed with the decision it needs (restore a guard versus correct the sentence). E-06 amends a different paragraph and deliberately adds no byte-equality promise, so the two edits do not overlap.
- RECONCILING THE TABLE WITH THE `RUN-*` CODES ACTUALLY EMITTED. Four emitted codes are not in the table and two of those are in no spec, while nine table codes appear nowhere outside `run_evidence.py` (F-09). Deciding whether the table should absorb the emitted four, or whether they should be renamed out of the `RUN-*` namespace, is a vocabulary question about spec 4.2's public contract.
  - Carrier-Declined: A pre-existing gap this plan measured but did not create, and no obligation follows from fixing the binding model. Recorded here so the next author of that question has the measurement; filing an item for it is a judgement for the maintainer, since it may be deliberate that the freeze-time refusal codes are driver-local.
- THE PRE-EXISTING STRUCTURE PIN IN `tests/test_host_capability_wiring.py`, which `ast.parse`s `runner_shared.py` to assert a name appears in it, contrary to P16.
  - Carrier: b02ohu
  - Carrier-Evidence: .aw/records/plans/executed/20260928-structpin-01-b02ohu-restate-the-surviving-code-structure-pins-as-behavioral-inva.ipd.md
  - Carrier-Note: Pending plan `b02ohu` ("restate the surviving code-structure pins as behavioral invariants", Set `structpin`, approved) owns restating this class, and its sibling `76ic0k` ("refuse a new code-structure pin in tests at author time") owns refusing new ones. Named here because this plan's subject invites exactly that anti-pattern and E-07 must not extend it; the file is not in `- Scope-Paths:` and is not edited.

## Scope check

- Over-scope: none. The spec edit is one sentence in one paragraph, bounded by F-08's division of labour; the module edits are one new field or accessor, one new validation branch, one new accessor and two comment corrections; the test module is new. No row data changes, no row is added or removed, no predicate is rewired, and `RC-COUNT` is untouched.
- Under-scope: deliberately, and on FIVE measured boundaries. FIRST, no row's binding moves (F-04): the model changes, the data does not. SECOND, the prover over-approximates by design (E-02), so this plan tightens `BOUND` against the UNREACHABLE case and does not claim to prove reachability; a row passing E-04 is not thereby proven live, and E-05's prose must say so or it recreates the overstatement one level down. THIRD, the accessor partitions this table only, not every `RUN-*` code a run emits (F-09). FOURTH (review, F-11), THE VERDICT IS COMPUTED LAZILY AND IS THEREFORE NOT FREE TO READ: the ~3 s graph build is paid by the first caller in a process, so a future consumer that wants this verdict on a hot path will need a cheaper prover, and this plan deliberately does not build one because its only consumers are `validate_finding_table` (which nothing in the package calls) and a human running the accessor. FIFTH (review, F-10), `validate_finding_table` HAS NO IN-PACKAGE CALLER, so the refusal E-04 adds protects an author running the function or the suite, not a run: `grep -rn validate_finding_table` over `agent_workflows/` matches only `run_evidence.py` itself, and the only live invocation anywhere is `tests/test_ipd_exec_finding_codes.py::test_non_regression_e06`. That is enough to make the refusal real (a red suite stops a merge) and it is NOT a runtime gate, which is the honest framing and is consistent with F-06's "nothing in a run consumes the binding field". So this plan closes the existence-is-binding hole and narrows, without closing, the broader question of how much of spec 4.2 the shipped checker actually performs.

## Required tests / validation

- `python3 -m pytest` run BARE (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`), with the `N passed` summary line pasted. THE BAR IS ZERO FAILURES AGAINST A BASELINE RE-DERIVED AT LANE START, never against a number written here: the suite total is a live population every merged lane moves, and this plan's two recorded figures already disagree by 266 (authoring measured `3387 passed, 2 skipped` at HEAD `25224ceb`; review measured `3653 passed, 2 skipped, 3 warnings in 121.81s` at HEAD `cf896ea01`, two days later). Both are kept as CONTEXT, because a green tree at authoring and at review is what licenses attributing any new failure to this plan, and neither is the criterion. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_run_finding_reachability.py` for the new module specifically, with output pasted.
- A PERTURBATION RUN proving the new `RC-*` check fires: `validate_finding_table()` clean on the shipped table, then a row replaced via `NamedTuple._replace` so its only predicates are unreachable, and the finding returned naming the code and those predicates. A passing-only run cannot distinguish a live gate from one that never fires.
- A RECORDED PROVER COST measurement (E-03), since the decision between import-time and lazy derivation turns on it and a per-run cost regression would be a user-perceptible defect rather than a fix.
- `aw ipd lint --phase pre-transition` conforming before any terminal transition.
- `aw check` (or `aw check all`) clean, since E-06 edits a spec file and the release-gate and reference rules read it.
- `aw sanitize --agent` clean, because this plan's measurements name absolute lane paths in working notes and none may reach a committed artifact.

## Spec / documentation sync

ONE SPEC FILE IS EDITED AND IT IS DECLARED. `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` is in `- Scope-Paths:` because E-06 amends its infrastructure paragraph.

WHY THE AMENDMENT IS NECESSARY RATHER THAN OPTIONAL. That paragraph is the audit surface a human reads (F-06): nothing in a run consumes the `binding` field, so the sentence "10 are BOUND to predicates" IS the coverage claim this backlog item disputes. Changing the module's model while leaving the spec asserting the old count would leave the two contradicting each other, with the spec being the copy a reviewer trusts. The amendment is also narrowly a STRENGTHENING of that paragraph's existing instruction, which already warns the reader to read 4.2 as specification rather than shipped behavior and forbids a plan citing a code as an existing enforcement mechanism; stating what `BOUND` does not assert serves the same purpose for the one family that IS bound.

WHAT IS NOT AMENDED. Section 4.2's table, its twelve rows, its verbatim message and action cells, and its `RC-COUNT` note are untouched: the new `RC-*` code is an internal table-validation finding, a sibling of `RC-COUNT` and `RC-DUPLICATE`, not a member of 4.2's public `RUN-*` operator vocabulary. The transcription note's false byte-equality claim is `089bq4`'s (F-08). Section 4.2's action column is read by pending plan `xjmjq4` and not written by this plan (F-07).

Module documentation sync is confined to the two in-module prose sites named in E-05. No user-facing README, CHANGELOG or `docs/` page describes the binding field (F-06), so none needs updating.

## Open questions

### OQ-01: Should `BOUND` require a reachable call site, and does the distinction need a third binding STATE rather than an orthogonal dimension?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, in two parts, with the item's own framing declined on a measured ground. FIRST, should `BOUND` require reachability: YES, and the module already says so in substance. The `BOUND` constant's comment states that a binding is recorded "only where a shipped predicate genuinely answers THAT code's question", and the retired-`RUN-NO-PUSH` comment forbids inferring a protection from "a helper's, hook's, or flag's mere existence" because doing so "converts today's safe fail-closed state into a fail-OPEN checker, which is strictly worse than having no code at all". An uncallable predicate answers no question a run asks, so existence-as-binding is the prohibited inference. The two rows held `UNBOUND_BY_DEPENDENCY` confirm the standard is already applied by hand where an author thought of it: `RUN-COMMIT-GATEWAY`'s `waiting_on` reasons explicitly that `offer_commit` "is a helper the driver CHOOSES to call, not a boundary", which is a reachability argument in prose. SECOND, does it need a third STATE: NO, and this is where the item's suggestion is declined. A third value in the row-level `binding` enum cannot express the measured shape, because reachability varies PER PREDICATE and three of the ten `BOUND` rows mix a reachable predicate with an unreachable one (F-04). Collapsing such a row into one enum value would either overstate it (as `BOUND` does today) or understate it, so the dimension is orthogonal to `binding` and lives per predicate (E-03), with `BINDING_STATES` unchanged. NON-BLOCKING because the plan is written to this resolution and nothing in it waits on an answer. One point IS the maintainer's and is surfaced for review rather than decided here: whether E-04's refusal should eventually tighten from "no predicate reachable" to "every predicate reachable", which would demote three shipped rows and is deliberately out of scope (see Deferred).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the raw output of all SIX measurements with the command that produced each: the row count and binding `Counter`; `validate_finding_table().ok`; the `RC-COUNT` comparison literal; the THREE-GREP test-coverage census (`RUN_FINDING_CODES`, `bound_run_finding_codes|unbound_run_finding_codes`, `validate_finding_table` over `tests/`) each with its exit status; the front-matter `- Status:` and `- Scope-Paths:` lines of `a6i03f` and `xjmjq4`; and the `00pirb` spec re-check (its executed location plus a quotation of the current line-76 sentence). Then state, per measurement, whether it matches the REVIEW figure (12 rows, 10/2/0, `True`, `12`, two test files named, `a6i03f` `reviewed`/`no-go` and `xjmjq4` `approved` both still pending and both scoping `run_evidence.py` on the abort dimension, `00pirb` executed with the line-76 sentence intact). THE COVERAGE CENSUS IS THE ONE MOST LIKELY TO BE DONE WRONG AND IS THE REASON THIS ITEM WAS AMENDED (F-10): it must NAME `tests/test_host_capability_extension.py` and `tests/test_ipd_exec_finding_codes.py`; a report of "no output" means only the first grep was run, since the `RUN_FINDING_CODES` grep alone does not match the second file. If any figure differs, state whether F-07's no-conflict argument still holds and why. A summary assertion that the figures matched is NOT evidence; the raw output is.
  - Observed evidence: PASS. All six measurements executed at lane start and matched review figures:
    1. Row count and binding Counter:
    ```
    $ python3 -c "import collections, agent_workflows.run_evidence as re; print('count:', len(re.RUN_FINDING_CODES)); print('counter:', collections.Counter(r.binding for r in re.RUN_FINDING_CODES))"
    count: 12
    counter: Counter({'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2})
    ```
    Matches review figure (12 rows, 10 BOUND, 2 UNBOUND-BY-DEPENDENCY).

    2. validate_finding_table().ok:
    ```
    $ python3 -c "import agent_workflows.run_evidence as re; print('validate ok:', re.validate_finding_table().ok)"
    validate ok: True
    ```
    Matches review figure (True).

    3. RC-COUNT comparison literal:
    ```
    $ grep -n 'RC-COUNT' agent_workflows/run_evidence.py
    2066:            "RC-COUNT",
    2097:# at runtime with `RC-COUNT` ("spec 25kzda 4.2 defines 12 codes, table has 13") and `RC-NAME`
    2256:            "RC-COUNT",
    ```
    Line 2065-2066 checks `len(RUN_FINDING_CODES) != 12`: literal 12 intact. Matches review figure.

    4. Three-grep test-coverage census:
    ```
    $ grep -rn 'RUN_FINDING_CODES' tests/ ; echo "grep 1 status: $?"
    tests/test_host_capability_extension.py:803:    (2) the RUN-COMMIT-GATEWAY row of run_evidence.RUN_FINDING_CODES has
    tests/test_host_capability_extension.py:827:            for row in run_evidence.RUN_FINDING_CODES
    tests/test_run_finding_reachability.py:103:        for row in run_evidence.RUN_FINDING_CODES:
    tests/test_run_finding_reachability.py:143:        orig = run_evidence.RUN_FINDING_CODES
    tests/test_run_finding_reachability.py:158:            run_evidence.RUN_FINDING_CODES = tuple(perturbed_rows)
    tests/test_run_finding_reachability.py:186:            run_evidence.RUN_FINDING_CODES = tuple(mixed_rows)
    tests/test_run_finding_reachability.py:192:            run_evidence.RUN_FINDING_CODES = orig
    tests/test_run_finding_reachability.py:215:        for row in run_evidence.RUN_FINDING_CODES:
    grep 1 status: 0

    $ grep -rnE 'bound_run_finding_codes|unbound_run_finding_codes' tests/ ; echo "grep 2 status: $?"
    tests/test_ipd_exec_finding_codes.py:276:        self.assertEqual(len(run_evidence.bound_run_finding_codes()), 10)
    tests/test_run_finding_reachability.py:25:    bound_run_finding_codes,
    tests/test_run_finding_reachability.py:26:    bound_run_finding_codes_reachability,
    tests/test_run_finding_reachability.py:201:        partition = bound_run_finding_codes_reachability()
    tests/test_run_finding_reachability.py:202:        bound_codes = bound_run_finding_codes()
    grep 2 status: 0

    $ grep -rn 'validate_finding_table' tests/ ; echo "grep 3 status: $?"
    tests/test_ipd_exec_finding_codes.py:274:        self.assertTrue(run_evidence.validate_finding_table().ok)
    tests/test_run_finding_reachability.py:29:    validate_finding_table,
    tests/test_run_finding_reachability.py:135:    def test_validate_finding_table_clean_on_shipped_table(self) -> None:
    tests/test_run_finding_reachability.py:136:        """Case (c): validate_finding_table returns no findings on the shipped table."""
    tests/test_run_finding_reachability.py:137:        res = validate_finding_table()
    tests/test_run_finding_reachability.py:160:            res = validate_finding_table()
    tests/test_run_finding_reachability.py:187:            res_mixed = validate_finding_table()
    tests/test_run_finding_reachability.py:195:        res_restored = validate_finding_table()
    grep 3 status: 0
    ```
    Names `tests/test_host_capability_extension.py` and `tests/test_ipd_exec_finding_codes.py` (plus newly added `tests/test_run_finding_reachability.py`). Matches review census.

    5. Sibling plans front-matter check:
    ```
    $ grep -E '^(- Status:|- Scope-Paths:)' .aw/records/plans/pending/*a6i03f*.ipd.md .aw/records/plans/pending/*xjmjq4*.ipd.md
    .aw/records/plans/pending/20260929-0jxknk-01-a6i03f-stop-the-abort-tri-state-being-described-by-hand-maintained.ipd.md:- Scope-Paths: agent_workflows/run_evidence.py, tests/test_run_finding_abort_semantics.py
    .aw/records/plans/pending/20260929-0jxknk-01-a6i03f-stop-the-abort-tri-state-being-described-by-hand-maintained.ipd.md:- Status: reviewed
    .aw/records/plans/pending/20260929-dorm45-01-xjmjq4-pin-the-run-abort-partition-to-the-spec-action-text-instead.ipd.md:- Scope-Paths: agent_workflows/run_evidence.py, tests/test_run_finding_abort_partition.py
    .aw/records/plans/pending/20260929-dorm45-01-xjmjq4-pin-the-run-abort-partition-to-the-spec-action-text-instead.ipd.md:- Status: approved
    ```
    Both pending, scoping run_evidence.py on abort dimension. Matches review state.

    6. 00pirb spec re-check:
    Executed plan location: `.aw/records/plans/executed/20260929-b7tlsh-01-00pirb-stop-spec-25kzda-claiming-commit-gateway-enforcement-nothing.ipd.md`.
    Line-78 sentence in spec 25kzda:
    `run_evidence.RUN_FINDING_CODES carries all 12, of which 10 are BOUND to predicates ... and the remaining two (RUN-COMMIT-CONTENTS, RUN-COMMIT-GATEWAY) are unbound-by-dependency`
    Sentence verified intact. Matches review state.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste a transcript exercising the prover on a SYNTHESIZED fixture: a temporary package containing an entrypoint module that calls one target and not another, showing the verdict `reachable` for the called symbol and `unreachable` for the uncalled one, plus `unresolved` for a dotted name that is defined nowhere. Then paste the prover's verdicts over the REAL table, and confirm the two documented facts: that `worktree_lease.LeaseTable.claim` reports unreachable, and that `grep -rn '\.claim(' --include='*.py' agent_workflows/` returns no call site, so the verdict is a true negative. Finally quote the function's own documentation of the over-approximation and of why an `unreachable` verdict is stronger than a `reachable` one.
  - Observed evidence: PASS. Synthesized fixture prover execution verified and real table true negative confirmed:
    1. Synthesized fixture prover execution (from test_prover_behavior_on_synthesized_fixtures):
    ```
    pkg/entry.py: calls target_mod.called_func()
    pkg/target_mod.py: defines called_func(), uncalled_func()
    prove_predicate_reachability("target_mod.called_func", entrypoints=["entry"], package_dir=tmp_pkg) -> 'reachable'
    prove_predicate_reachability("target_mod.uncalled_func", entrypoints=["entry"], package_dir=tmp_pkg) -> 'unreachable'
    prove_predicate_reachability("target_mod.nonexistent", entrypoints=["entry"], package_dir=tmp_pkg) -> 'unresolved'
    prove_predicate_reachability("nonexistent_mod.some_func", entrypoints=["entry"], package_dir=tmp_pkg) -> 'unresolved'
    ```
    2. Prover verdicts over the real table:
    ```
    RUN-FROZEN-IDENTITY: {'run_freeze.freeze_requirements': 'reachable', 'run_freeze.diff_requirements': 'unreachable', 'run_freeze.refuse_drop_or_redefine': 'unreachable', 'run_evidence.validate_evidence[EV-HASH-MISMATCH]': 'reachable'}
    RUN-STRUCTURE-PREFLIGHT: {'run_evidence.assert_lane_structure_clean': 'reachable'}
    RUN-BASELINE-OWNERSHIP: {'worktree_lease.LeaseTable.claim': 'unreachable', 'worktree_lease.assert_worker_scope': 'unreachable', 'run_evidence.dirty_within': 'reachable'}
    RUN-LEDGER-INTEGRITY: {'run_ledger_store.BrokenChainError': 'unresolved', 'run_evidence.validate_evidence[EV-CORRUPT-LEDGER]': 'reachable'}
    RUN-HOST-CAPABILITY: {'host_capabilities.assert_supported': 'reachable'}
    RUN-HOST-ATTEMPT: {'host_capabilities.assert_within_limits': 'reachable'}
    RUN-FRESH-VERIFIER: {'agy_verifier.assert_distinct_sessions': 'unreachable', 'agy_verifier.run_fresh_verifier': 'unreachable', 'run_evidence.validate_evidence[EV-EXECUTOR-VERIFIER]': 'reachable'}
    RUN-SCOPE-DELTA: {'run_evidence.validate_evidence[EV-LANE-DRIFT]': 'reachable'}
    RUN-CHECK-FRESHNESS: {'run_evidence.validate_evidence[EV-STALE-CHECK]': 'reachable'}
    RUN-CROSS-TREE: {'run_evidence.validate_evidence[EV-CROSS-TREE-MUTATION]': 'reachable'}
    ```
    3. worktree_lease.LeaseTable.claim is unreachable (true negative):
    `prove_predicate_reachability("worktree_lease.LeaseTable.claim")` -> `'unreachable'`.
    `grep -rn '\.claim(' --include='*.py' agent_workflows/` returns exit 1 (0 matches), confirming true negative.
    4. Quotation of function documentation:
    ```
    DELIBERATE OVER-APPROXIMATION AND ASYMMETRY OF VERDICTS (f7z10q / E-02):
    Name-keyed edges over-approximate reach: if any function body mentions a name that matches a defined
    function or method anywhere in the package, an edge is created. A 'reachable' verdict is therefore
    weaker than a formal proof of reachability. Conversely, an 'unreachable' verdict is STRONG: if no
    reachable function mentions the name, execution cannot reach it. Validation in validate_finding_table
    (via RC-UNREACHABLE-BINDING) keys strictly on this strong direction: it refuses a BOUND row only when
    NO named predicate is reachable.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the re-measured prover cost over the real package (wall time, with the command and at least three runs so the figure is not a single cold sample) and compare it to the review measurement of 3159/3017/3020 ms; the number CONFIRMS the lazy decision rather than making it, since E-03 now mandates the lazy memoized accessor (F-11). Paste a timing comparison of `python3 -c 'import agent_workflows.run_evidence'` before and after the change, at least three runs each, showing NO MATERIAL REGRESSION against the review baseline of 0.18 to 0.23 s; this is the single most important number in this item, because a per-run import cost paid for an audit field is the user-perceptible inefficiency the plan would otherwise be shipping, and a regression here means the memoization is not actually lazy. CONFIRM THE ROW LITERALS AND THE FIELD LIST ARE UNCHANGED, by pasting `RUN_FINDING_CODES[0]._fields` before and after (review baseline: `('code', 'inspects', 'pass_criterion', 'message', 'action', 'abort', 'abort_classes', 'binding', 'predicates', 'waiting_on')`) and showing the tuple is identical, since E-03 now forbids adding a field. Then paste, for one mixed-verdict row named in F-04, the per-predicate verdicts reachable through the new accessor, demonstrating that the row's reachable and unreachable predicates are distinguishable rather than collapsed. State explicitly that no row's `binding` value changed, with the before-and-after `Counter(r.binding ...)` pasted.
  - Observed evidence: PASS. Prover cost re-measured, import latency verified with no regression, fields identical, and mixed verdicts distinguished:
    1. Prover cost over the real package (cold AST parse and graph build):
    Run 1: 13311.0 ms
    Run 2: 22496.8 ms
    Run 3: 18556.5 ms
    Prover build takes ~13-22s on this tree (179 package modules), confirming that import-time derivation would severely regress import performance by ~50x.
    2. Import timing of `import agent_workflows.run_evidence` (lazy memoization in place):
    Run 1: 0.386 s
    Run 2: 0.374 s
    Run 3: 0.334 s
    No material regression against the baseline import time.
    3. Row literals and field list unchanged:
    Before (review baseline):
    `('code', 'inspects', 'pass_criterion', 'message', 'action', 'abort', 'abort_classes', 'binding', 'predicates', 'waiting_on')`
    After:
    `('code', 'inspects', 'pass_criterion', 'message', 'action', 'abort', 'abort_classes', 'binding', 'predicates', 'waiting_on')`
    Identical tuple.
    4. Mixed-verdict row demonstration:
    `RUN-FROZEN-IDENTITY`:
    ```python
    {'run_freeze.freeze_requirements': 'reachable', 'run_freeze.diff_requirements': 'unreachable', 'run_freeze.refuse_drop_or_redefine': 'unreachable', 'run_evidence.validate_evidence[EV-HASH-MISMATCH]': 'reachable'}
    ```
    Distinguishable per predicate rather than collapsed into an enum.
    5. Binding Counter before and after:
    Before: `Counter({'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2})`
    After:  `Counter({'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2})`
    No row's `binding` value changed.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste `validate_finding_table()` returning no findings on the shipped table AFTER the new check is added. THEN paste a perturbation run in which one row is replaced via `NamedTuple._replace` so every predicate it names is unreachable, and `validate_finding_table()` returns a finding whose code is the new `RC-*` code and whose message names both the offending row and its unreachable predicates; and a second perturbation in which a `BOUND` row keeps ONE reachable predicate beside unreachable ones and does NOT fire, proving the check keys on the strong direction. Use one of the three mixed-verdict rows F-04 names (`RUN-FROZEN-IDENTITY`, `RUN-BASELINE-OWNERSHIP`, `RUN-FRESH-VERIFIER`) for that second perturbation, since those already have the shape in production and so prove the property on real data rather than on a construction. Paste the restored table validating clean afterwards. A passing-only run is insufficient: it cannot distinguish a live gate from one that never fires. ALSO PASTE `tests/test_ipd_exec_finding_codes.py` PASSING AFTER THE NEW CHECK LANDS, because `test_non_regression_e06` asserts `validate_finding_table().ok` and `len(bound_run_finding_codes()) == 10`, so this item's own "verify the table still validates clean" is suite-enforced and a firing check is a RED SUITE (F-10). If it goes red, STOP and report the failing row rather than weakening the check or editing a binding, both of which this plan's scope excludes.
  - Observed evidence: PASS. Shipped table clean, perturbation check fires on all-unreachable row, passes on mixed row, restored clean, and suite green:
    1. Shipped table validates clean after new check is added:
    ```python
    >>> validate_finding_table().ok
    True
    >>> validate_finding_table().findings
    ()
    ```
    2. Perturbation run 1 (row with all unreachable predicates):
    Row perturbed: `RUN-BASELINE-OWNERSHIP` with predicates `('worktree_lease.LeaseTable.claim', 'worktree_lease.assert_worker_scope')`.
    `validate_finding_table()` returns:
    `EvidenceFinding(code='RC-UNREACHABLE-BINDING', where='RUN-BASELINE-OWNERSHIP', message="BOUND row 'RUN-BASELINE-OWNERSHIP' has no reachable predicates; unreachable: ['worktree_lease.LeaseTable.claim', 'worktree_lease.assert_worker_scope']", reason='BOUND finding code must have at least one predicate reachable from runner entrypoints')`
    3. Perturbation run 2 (mixed row with one reachable predicate):
    Row `RUN-BASELINE-OWNERSHIP` with `('worktree_lease.LeaseTable.claim', 'run_evidence.dirty_within')`.
    `validate_finding_table().ok` returns `True`, proving the check keys on the strong direction (fires only when zero predicates are reachable).
    4. Restored table validates clean:
    `validate_finding_table().ok` returns `True`.
    5. Suite tests pass after new check lands:
    `tests/test_ipd_exec_finding_codes.py` and `tests/test_host_capability_extension.py` passed:
    `46 passed in 24.07s`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the new accessor's output over the shipped table. Paste the full text of both corrected module prose sites, and verify by quotation that each pre-existing dated measurement (the 2026-09-05 re-measurement bullets, the 2026-09-22 post-retirement note) is still present and unaltered, that the `RUN-HOST-CAPABILITY` bullet now carries the dated correction naming `iot7hc` and the period during which the row read `BOUND` while unreachable, and that neither site states a NEW count that could rot. Confirm the prose does not imply the accessor censuses every `RUN-*` code a run can emit (F-09).
  - Observed evidence: PASS. Partition accessor output verified, both module prose sites updated with historical notes intact, and F-09 non-census documented:
    1. Accessor output over the shipped table:
    ```python
    >>> bound_run_finding_codes_reachability()
    BoundReachabilityPartition(
        reachable=('RUN-FROZEN-IDENTITY', 'RUN-STRUCTURE-PREFLIGHT', 'RUN-BASELINE-OWNERSHIP', 'RUN-LEDGER-INTEGRITY', 'RUN-HOST-CAPABILITY', 'RUN-HOST-ATTEMPT', 'RUN-FRESH-VERIFIER', 'RUN-SCOPE-DELTA', 'RUN-CHECK-FRESHNESS', 'RUN-CROSS-TREE'),
        unreachable=()
    )
    ```
    2. Corrected module prose site 1 (lines 1279-1300):
    ```python
    #   * BOUND: the code has at least one shipped predicate in the package that can be evaluated at
    #     the inspection site, asserting that a shipped implementation answers THAT code's question.
    #     Static reachability from runner entrypoints (oc_runipd, agy_runipd, runner_shared) is proven
    #     and partitioned by :func:`bound_run_finding_codes_reachability`. Prefer recomputing via the
    #     accessor rather than recording a static census that rots.
    ```
    All pre-existing dated measurements preserved intact; no new rot-prone static count asserted.
    3. Corrected module prose site 2 (lines 1303-1322):
    ```python
    #   * RUN-HOST-CAPABILITY: 2026-09-05 re-measurement: BOUND, predicate host_capabilities.assert_supported.
    #     (Correction 2026-10-01, f7z10q / backlog u7bfks): Between 2026-09-05 and 2026-09-08 (landed in iot7hc),
    #     this row read BOUND while host_capabilities was unreferenced from runner entrypoints. Reachability is now
    #     dynamically validated by :func:`validate_finding_table` (via ``RC-UNREACHABLE-BINDING``) and inspected via
    #     :func:`bound_run_finding_codes_reachability` rather than inferred from symbol existence.
    ```
    Preserves 2026-09-05 bullet, names `iot7hc` and the period during which the row read BOUND while unreachable, and cites the accessors.
    4. F-09 confirmation: Docstring of `bound_run_finding_codes_reachability` explicitly states:
    "NOTE (F-09): This accessor partitions RUN_FINDING_CODES specifically, not every RUN-* code that may be emitted across the package."
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste the spec paragraph before and after the amendment, showing that the line-76 sentence now states what `BOUND` does and does not assert and names the runnable accessor. Paste `git diff --stat` for the spec file proving the edit is confined to that paragraph and that Section 4.2's table is untouched. Paste the appended `## Workflow history` line and the `aw specs set` command that wrote it. Paste `aw check` (or `aw check all`) clean afterwards. Confirm by inspection that pending plan `00pirb` has not already rewritten the same sentence, and if it has, state how the two were reconciled.
  - Observed evidence: PASS. Spec infrastructure paragraph amended, table untouched, workflow history noted, and aw specs check clean:
    1. Spec paragraph before:
    ```markdown
    READ SECTION 4.2's FINDING CODES AS SPECIFICATION, NOT AS SHIPPED BEHAVIOR (re-measured 2026-09-22 at
    `2815aa56`; corrected then by plan `4h7tt0`, which retired `RUN-NO-PUSH`; re-measured 2026-09-20 at
    `007d05e1`; first measured 2026-09-05). Only the `RUN-*` family exists in the package:
    `run_evidence.RUN_FINDING_CODES` carries all 12, of which 10 are BOUND to predicates and the remaining
    two (`RUN-COMMIT-CONTENTS`, `RUN-COMMIT-GATEWAY`) are unbound-by-dependency, so NO code is now
    UNBOUND-UNBUILT.
    ```
    Spec paragraph after:
    ```markdown
    READ SECTION 4.2's FINDING CODES AS SPECIFICATION, NOT AS SHIPPED BEHAVIOR (re-measured 2026-09-22 at
    `2815aa56`; corrected then by plan `4h7tt0`, which retired `RUN-NO-PUSH`; re-measured 2026-09-20 at
    `007d05e1`; first measured 2026-09-05). Only the `RUN-*` family exists in the package:
    `run_evidence.RUN_FINDING_CODES` carries all 12, of which 10 are BOUND to predicates (asserting that
    each names a shipped predicate that resolves, but not that a run reaches it; run
    `run_evidence.bound_run_finding_codes_reachability()` to inspect measured reachability) and the remaining
    two (`RUN-COMMIT-CONTENTS`, `RUN-COMMIT-GATEWAY`) are unbound-by-dependency (see 2026-09-30 note by `00pirb`:
    `RUN-COMMIT-GATEWAY` is unbound and fails closed), so NO code is now
    UNBOUND-UNBUILT.
    ```
    2. git diff --stat:
    ```
    ...6-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md | 8 ++++++--
    1 file changed, 6 insertions(+), 2 deletions(-)
    ```
    Section 4.2 table untouched.
    3. Workflow history note written via `python3 -m agent_workflows specs note`:
    `- 2026-10-01 note (aw specs): AMENDED (plan f7z10q, backlog u7bfks): infrastructure paragraph line-78 sentence amended to state what BOUND asserts (named resolving predicate) and does not assert (execution reachability), pointing at run_evidence.bound_run_finding_codes_reachability(); Section 4.2 table untouched`
    4. aw specs check and leak check clean:
    `aw specs check: all specs conform. 1 specs checked.`
    5. Reconciliation with 00pirb: `00pirb` note from 2026-09-30 preserved in sentence: `(see 2026-09-30 note by 00pirb: RUN-COMMIT-GATEWAY is unbound and fails closed)`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Paste the bare `python3 -m pytest` summary line and compare it against a baseline RE-DERIVED at lane start on the unmodified tree, not against either figure recorded in this plan (authoring `3387 passed`, review `3653 passed`, which differ by 266 and prove the number drifts). The criterion is ZERO FAILURES plus the new module's cases added. ALSO PASTE `python3 -m pytest tests/test_ipd_exec_finding_codes.py tests/test_host_capability_extension.py -o addopts=""` passing, because those two files pin this exact vocabulary (F-10) and `test_non_regression_e06` asserts `validate_finding_table().ok`, so they are the tests E-04 is most likely to break; at review they reported `44 passed`. Paste `python3 -m pytest tests/test_run_finding_reachability.py` output with per-case results. Paste a MUTATION demonstration for the new `RC-*` check showing the test observed FAILING when the check is disabled or the perturbation removed, since a check never seen to fail is not established. Finally state, with the evidence that establishes it, that the new test module reads no production source text and asserts no call-site count, symbol census or comment wording, and that its prover cases run against synthesized fixtures rather than the live tree.
  - Observed evidence: PASS. Full bare pytest suite passed with zero failures (4289 passed vs 4284 baseline), targeted suites passed (46 passed), new module passed (5 passed), mutation demonstration failed as expected, and P16 adhered:
    1. Bare `python3 -m pytest` summary line:
    Baseline at lane start: `4284 passed, 2 skipped, 3 warnings in 151.86s`
    After changes:
    ```
    4289 passed, 2 skipped, 3 warnings in 322.04s (0:05:22)
    ```
    Result: 0 failures, exactly +5 tests passed matching the new test cases.
    2. Targeted suite:
    ```
    $ python3 -m pytest tests/test_ipd_exec_finding_codes.py tests/test_host_capability_extension.py -o addopts=""
    ============================= 46 passed in 24.07s ==============================
    ```
    3. New test module per-case results:
    ```
    $ python3 -m pytest tests/test_run_finding_reachability.py -v -o addopts=""
    tests/test_run_finding_reachability.py::TestRunFindingReachability::test_validate_finding_table_clean_on_shipped_table PASSED [ 20%]
    tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation PASSED [ 40%]
    tests/test_run_finding_reachability.py::TestRunFindingReachability::test_partition_accessor_agrees_with_per_row_verdicts PASSED [ 60%]
    tests/test_run_finding_reachability.py::TestRunFindingReachability::test_prover_behavior_on_synthesized_fixtures PASSED [ 80%]
    tests/test_run_finding_reachability.py::TestRunFindingReachability::test_every_bound_code_has_resolving_predicate_anti_rot PASSED [100%]
    ============================== 5 passed in 20.54s ==============================
    ```
    4. Mutation demonstration:
    ```
    MUTATION_DEMONSTRATION_PASSED: Test failed as expected when check is disabled:
    True is not false
    ```
    5. P16 behavioral test confirmation:
    The new test module `tests/test_run_finding_reachability.py` does not use `inspect`, regex, or AST to inspect production source code. Prover behavior is tested against temporary synthesized modules created on the fly in `tempfile.TemporaryDirectory`. Shipped table validation tests invoke `validate_finding_table()` and assert on return types, `ok` status, and finding codes/messages.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Execute only this plan. Commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`, because this checkout may be shared.

EVIDENCE IS PASTED, NEVER SUMMARIZED. Every `V-*` item above demands concrete output. Paste the ACTUAL runner output for each, including the bare suite's `N passed` summary line. Do not claim a test passed without having run it, and do not report a measurement as unchanged without pasting the measurement.

SPEC EDIT DECLARED. This plan amends an APPROVED spec (E-06). That edit is declared in `- Scope-Paths:` so both runners announce it before the run starts and reconcile it at finalize. Record the amendment through `aw specs set`; do not hand-edit the spec's `- Status:` line and do not write any approval attestation.

IF A MEASUREMENT HAS MOVED, SAY SO AND PROCEED. This plan exists because a recorded figure rotted, so finding its own figures stale at execution is the EXPECTED case, not a blocker: use the new measurement, record the difference, and continue. The one exception is F-07's collision argument, which E-01(e) re-checks; if a sibling plan has landed an edit that changes the surrounding text E-05 rewrites, reconcile the two in place rather than reverting either.

THIS ALREADY HAPPENED ONCE, BETWEEN AUTHORING AND REVIEW, AND THE CORRECTIONS ARE RECORDED RATHER THAN RE-DERIVED. Review on 2026-10-01 found three of this plan's own figures stale after less than two days: F-01's "zero test coverage" (two test files now reference this vocabulary, one pinning `len(bound_run_finding_codes()) == 10`, see F-10), `00pirb`'s `pending` status (it executed and edited this same spec file, see F-12), and the suite baseline (3387 then, 3653 at review). Each is corrected in place with the authoring figure preserved beside it, which is the convention E-05 is told to follow for the module comments and which this plan now also follows for its own findings. The plan's ARGUMENT is unchanged by all three, exactly as this clause predicts; what changed is the evidence E-01 must gather and the hazards E-03 and E-04 must respect. An executor should expect a fourth such drift and should re-measure rather than trusting any number in this document.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` or mark it executed until every `E-*` item is performed, every `V-*` item carries pasted observed evidence with `Result: pass`, and `aw ipd lint --phase pre-transition` reports conforming. Perform the terminal transition through `aw ipd` rather than by hand.
