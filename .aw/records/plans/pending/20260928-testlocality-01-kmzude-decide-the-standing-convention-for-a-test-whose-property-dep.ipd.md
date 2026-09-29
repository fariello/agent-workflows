# IPD: Decide the standing convention for a test whose property depends on the live checkout, and fix the vacuous pass it already permits

- Date: 2026-09-28
- Kind: child
- Concern: Backlog `5mc38x` carries `OQ-01` from executed plan `zx9dkq` as a BINARY question: for a test whose property genuinely depends on the checkout location, is the answer a loud `skip` naming the condition, or synthesizing the input so the assertion runs everywhere? MEASURED IN THIS REPOSITORY, THE BINARY IS FALSE AND ITS "LOUD SKIP" PREMISE IS WRONG. A runtime skip reason is INVISIBLE in the default run: `pyproject.toml` sets `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` and configures no `-rs`/`reportchars`, so a skipping test prints `1 passed, 1 skipped` and the reason string appears ZERO times (measured 2026-09-28, both serially and under the configured `-n auto`). Meanwhile a MARKER-deselected test IS announced in every run by `tests/deselect_notice.pytest_terminal_summary`, which writes `NOTE: N tests were deselected by -m/-k and did not run ... run everything with: make test-all`, and the marker route comes BACK at the release gate, because `release-review/08-final-ship-review.md` requires `make test-all` (`-m ''`) as release evidence while NO gate re-runs a runtime skip. So the repository already contains a third option that is strictly louder than the "loud skip" the question assumes, and the question can be answered from repository evidence rather than referred to the maintainer.
- Scope: Record the decision RULE (an ordering of three options with the criteria for choosing between them) in the canonical home for test-authoring conventions, point at it from `CONTRIBUTING.md` without restating it, and apply it to the ONE genuinely location-dependent case that exists in the tree today. Does NOT add a new pytest marker (there is no test needing one, and building one now is the hypothetical-need generality P6 forbids), does NOT edit the managed `AGENTS.md` block or `engine.py`, and does NOT revisit the code-pinning half of P16.
- Scope-Paths: GUIDING_PRINCIPLES.md, CONTRIBUTING.md, tests/test_ipd_set_plan.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: 5mc38x
- Set: testlocality
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: kmzude

## Workflow history

- 2026-09-28 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `5mc38x`, which carries `OQ-01` from executed plan `zx9dkq`. The item records the question as the maintainer's, and this plan RESOLVES IT FROM REPOSITORY EVIDENCE instead, per the standing instruction to ask the human only when the repository genuinely cannot answer. It can: the item's binary (loud skip versus synthesize) rests on the premise that a skip is loud, and MEASUREMENT REFUTES THAT PREMISE in this repository (no `-rs` is configured, so the reason string is printed zero times in the default run). The same measurement surfaced the third option the binary omits (a collection-time marker, which `tests/deselect_notice.py` announces in every run and which `make test-all` restores at the release gate), and surfaced one REAL in-tree case: `tests/test_ipd_set_plan.py::TestCorpusNoRegression` skips one test on checkout location while its SIBLING passes VACUOUSLY over an empty glob. The residual genuinely-maintainer part is preserved as `OQ-01` below, and it is narrow: whether the ordering this plan records is the ordering the maintainer wants.

## Goal

Answer `OQ-01` with a written decision rule a future author and a future reviewer can both apply without
re-deriving it, and prove the rule is not vacuous by applying it to the single location-dependent test
that exists in the tree today, which currently permits a silent vacuous pass.

The rule must be usable at the moment it is needed: inside a `/plan-review` on a test nobody has written
yet. That is why it is an ordering with criteria rather than a preference.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the evidence, then record the rule

- [ ] E-01 MEASURE THE VISIBILITY OF EACH OF THE THREE OPTIONS, because the rule's whole justification is that they differ and the backlog item assumes wrongly that they do not. Four measurements, all at execution HEAD, all pasted. (a) A runtime `skip` under the CONFIGURED default (bare `python3 -m pytest`): show the summary counts AND show the reason string appearing zero times, which is what refutes "loud". (b) The same skip with `-rs` added, showing the reason IS printed, which localizes the cause to the absent `reportchars` rather than to pytest. (c) A MARKER-deselected test under the same configured default, showing `tests/deselect_notice.pytest_terminal_summary`'s `NOTE: N tests were deselected` line, i.e. the marker route announces itself where the skip route does not. (d) The CI invocation's difference: `tests.yml` runs `python -m pytest tests/ -n auto -rfEs`, so confirm that CI DOES surface skip reasons, because the rule must not claim a skip is invisible everywhere when it is visible in CI. Use a THROWAWAY probe test for (a) and (b) and DELETE it afterwards; do not leave it in `tests/`.
  - Depends on: none
  - Expected outcome: pasted output for all four measurements. Authoring baseline to reproduce or refute: (a) `1 passed, 1 skipped`, with `grep -c` on the reason string returning `0`; (b) a `SKIPPED [1] ...: <reason>` line present under `short test summary info`; (c) the `NOTE: N tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus')` line present; (d) `-rfEs` confirmed in the CI step by quoted content.
  - Execution state: pending

- [ ] E-02 WRITE THE DECISION RULE INTO `GUIDING_PRINCIPLES.md` AS A NEW SUBSECTION OF PRINCIPLE 16, not as a new principle, because a test that does not prove what it claims is the SAME concern P16 already owns (P8, one canonical place). Match the existing shape exactly: P16 is the only principle using `###` subsections (`### What is prohibited:` and `### What to do instead:`, both with a trailing colon and bolded bullet lead-ins such as `- **No count or census pins**: ...`), so add a third in that form. THE RULE, THREE OPTIONS IN PREFERENCE ORDER, each with the criterion that selects it. FIRST, SYNTHESIZE, whenever the property does not actually depend on the live checkout; this is the default and `zx9dkq` already established it is the common case, since the live root is usually a convenient SOURCE of an input rather than the subject of the assertion. SECOND, DESELECT AT COLLECTION TIME WITH A MARKER, when the property genuinely requires the live tree; preferred over a runtime skip for two measured reasons, that it is ANNOUNCED in every run by `tests/deselect_notice.py` and that `make test-all` restores it at the release gate `release-review/08-final-ship-review.md` mandates. THIRD, A RUNTIME SKIP, only when the condition cannot be known until the test body runs, and then it MUST carry a stated reason AND the author must check that no SIBLING assertion in the same class degrades to a vacuous pass under the same condition. State the measured caveat honestly rather than overclaiming: a skip reason IS visible in CI, which passes `-rfEs`, so the rule's objection is to the DEFAULT LOCAL run and to the absence of any gate that re-runs a skip, not to skips being unprintable. AND STATE THE PROHIBITION THE WHOLE RULE EXISTS TO SERVE: never weaken an assertion so it passes everywhere. CITE ONLY LIVE PRECEDENT: P16's own "Verify test sensitivity with mutation" bullet, and `DECISIONS.md` D78, which fixed a test that "had started passing vacuously" by restoring the real code path rather than relaxing the assertion. DO NOT cite `tests/test_nested_tty_noninteractive.py`, which the backlog item recommends: that file was deleted in `19313eed` for being a code-pinning test, and the quote attributed to it was never in it (Step 0). Propagating it would dangle and would recommend a forbidden approach.
  - Depends on: E-01
  - Expected outcome: a new `###` subsection inside principle 16 of `GUIDING_PRINCIPLES.md`, quoted in full, carrying the three options in preference order with their selecting criteria, the CI caveat, and the no-weakening prohibition; structurally matching the two existing `###` subsections in heading form and bullet form.
  - Execution state: pending

- [ ] E-03 ADD A POINTER BULLET TO `CONTRIBUTING.md` UNDER `## Authoring conventions`, AND DO NOT RESTATE THE RULE, because that section's own established pattern is delegation: it already reads "Keep each policy or rule in exactly one canonical place and link to it, rather than duplicating it (P8)", and its neighbouring bullets cite `GUIDING_PRINCIPLES.md` P2 and P14 by reference rather than quoting them. One bullet naming the location-dependence rule and pointing at P16 is the whole deliverable. DO NOT touch `## Self-tests (run before pushing tool changes)`: that section governs how to RUN the suite, not how to author a test, and the distinction is what keeps the two from drifting.
  - Depends on: E-02
  - Expected outcome: one new bullet quoted from `CONTRIBUTING.md`'s `## Authoring conventions` section, pointing at the P16 subsection by name and restating nothing; plus confirmation by diff that no other section of the file changed.
  - Execution state: pending

### Task group 2: apply the rule to the one real case, so it is not vacuous

- [ ] E-04 FIX THE ONE GENUINELY LOCATION-DEPENDENT CASE IN THE TREE, `TestCorpusNoRegression` in `tests/test_ipd_set_plan.py`, WHOSE REAL DEFECT IS THE SIBLING'S VACUOUS PASS RATHER THAN THE SKIP ITSELF. Both its tests enumerate the live corpus through the RELATIVE glob `.aw/records/plans/*/*.ipd.md`, which resolves against the process CWD. `test_tracked_orchestrators_mostly_parse` at least notices, calling `skipTest("no tracked orchestrators visible from the test cwd")` when the count is zero; `test_every_refusal_states_a_reason` does NOT, and loops over an empty glob asserting nothing, so it reports PASS having tested nothing. MEASURED from a CWD without the corpus: `1 passed, 1 skipped`, with the PASS being the refusal test. APPLY THE RULE AS THE RULE ORDERS IT: this property genuinely requires the live corpus, so option one (synthesize) does not apply and option two governs. Make the zero-corpus condition fail or deselect for BOTH tests rather than for one, so neither can report a green having enumerated nothing; the specific mechanism is the executor's to choose from the rule's option two and three, and whichever is chosen must leave the reason discoverable. DO NOT lower the existing `0.70` ratio floor and do not delete either test: the floor is a measured no-worsening guard whose own comment records "37 of 47 parsed (was 18 of 47 before)", and weakening it is exactly the move E-02's prohibition forbids.
  - Depends on: E-03
  - Expected outcome: both tests in the class demonstrated to no longer produce a silent green when the corpus is absent, with a pasted before-and-after from a CWD lacking the corpus (baseline to flip: `1 passed, 1 skipped` where the pass is `test_every_refusal_states_a_reason`), plus a pasted bare `python3 -m pytest` showing no new failures, plus the `0.70` floor shown unchanged by diff.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE CANONICAL HOME FOR A TEST-AUTHORING CONVENTION IS `GUIDING_PRINCIPLES.md` PRINCIPLE 16, and nothing mechanical reads it. Principle 16 is titled "Test outcomes and behavior, never code structure or text" and is the file's last principle. No `aw check` rule and no test parses this file, so an amendment carries no linter to satisfy; the cost of being wrong is that authors are misled, not that a gate breaks.
- P16 HAS NO VACUOUS-PASS RULE TODAY. Its four prohibitions are all about pinning code structure (source inspection, count or census pins, text or docstring pins, architectural placement pins). A test that passes having asserted nothing is a different failure of the same kind and is currently unaddressed, which is why E-02 extends P16 rather than amending an existing bullet.
- `CONTRIBUTING.md` DELEGATES RATHER THAN RESTATES, and says so in its own text: "Keep each policy or rule in exactly one canonical place and link to it, rather than duplicating it (P8)". Its `## Self-tests` section governs running the suite (`make test`, `make test-serial`, the `conftest.py` role scrub and `PYTHONPATH` pin) and contains no authoring rule beyond "Test only the mechanical parts, not the instruction prose".
- NO SPEC GOVERNS TEST AUTHORING, so no spec amendment is owed. The only adjacent artifact is draft spec `pqsx96` (agent-adherence invariant catalog), whose invariant `I-06` concerns test evidence being FORGEABLE ("a `tests passed` transcript is a claim, not proof") rather than how a test is written, and which states it produces no enforcement code.
- THE REPOSITORY ALREADY SOLVED THE ADJACENT PROBLEM WITH A MARKER, which is the evidence that makes option two more than a suggestion. `pyproject.toml` defines `livecorpus` for a test that "asserts a property over EVERY artifact in this repository's own .aw/records/ tree, so ANY agent writing a plan can turn it red", and records the measured cost that motivated it: one such test went red on three correctly-cleared plans and cost a run "2h 10m and $55.02 with nothing integrated". Four sites use it (`tests/test_review_record_classifier.py`, `tests/test_orchestrator_probe_payload.py`, `tests/test_ipd_lint.py`, and the notice in `tests/deselect_notice.py`).
- A DESELECT IS ANNOUNCED; A SKIP IS NOT. `tests/deselect_notice.pytest_terminal_summary` writes a `NOTE: N tests were deselected by -m/-k and did not run` line whenever the count is nonzero, and it aggregates across xdist workers via `pytest_testnodedown`, so it survives the configured `-n auto`. There is no counterpart for skips.
- THE MARKER ROUTE COMES BACK AT THE RELEASE GATE AND THE SKIP ROUTE NEVER DOES. `release-review/08-final-ship-review.md` states that release evidence "MUST come from the repository's FULL test target, running every test including every marker or category that routine/default runs deselect (in this toolkit that is `make test-all`, i.e. `python3 -m pytest tests/ -m ''`)", and that a run "that deselects test subsets or prints a notice of deselected tests ... is NOT valid release evidence". `-m ''` restores a marker; nothing restores a runtime skip.
- CI SURFACES SKIP REASONS EVEN THOUGH THE DEFAULT LOCAL RUN DOES NOT. `.github/workflows/tests.yml` runs `python -m pytest tests/ -n auto -rfEs`. This is the fact that keeps E-02 honest: the objection to a skip is about the default local run and about no gate re-running it, not about the reason being unprintable.
- THE PRECEDENT THE BACKLOG ITEM RECOMMENDS IS DEAD, AND ITS REPLACEMENT IS BETTER. The item says to cite `tests/test_nested_tty_noninteractive.py`'s docstring for the position that weakening a guard to make it pass is forbidden ("would have made this pass while silently accepting a future change that actually removed a `stdin=`"). THAT FILE NO LONGER EXISTS: it was deleted in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), and it was deleted FOR CAUSE, because it was itself a code-pinning test that `ast.parse`d production sources to count `subprocess` call sites, which is the first prohibition in P16. Worse, the quote was never in that file; it is a review's paraphrase of a `818uru` docstring. Citing it would both dangle and recommend an approach the repository has since forbidden. USE INSTEAD, both live and both stronger: `GUIDING_PRINCIPLES.md` P16's own "Verify test sensitivity with mutation" bullet ("A test is only valid if breaking the underlying behavior makes the test fail"), which is the canonical rule and sits in the very principle being amended; and `DECISIONS.md` D78, a COMMITTED maintainer decision that fixed a test which "had started passing vacuously" by restoring the real code path rather than by relaxing the assertion, and which explicitly left the product code unchanged.
- THIS PLAN'S OWN CITATION AUDIT IS PART OF THE EVIDENCE, not a digression: the dead citation was found by resolving every path this plan cites before asserting it, and the same class of defect is already tracked in the tree (backlog `pn7rw3`, whose maintainer ruling is that stale references to the deleted guards should be REMOVED rather than restored, and `ddon4j`, the same shape in an approved spec). E-02 must therefore not propagate the item's citation.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `pyproject.toml` `[tool.pytest.ini_options]` | **THE BACKLOG ITEM'S "LOUD SKIP" PREMISE IS FALSE HERE, WHICH IS WHAT DISSOLVES ITS BINARY.** `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` configures no `-rs` and no `reportchars`, so a skip reason is never printed by a default run. A skip is therefore SILENT locally, not loud, and the item's framing of "loud skip versus synthesize" compares a real option against one that does not exist by default. | measured 2026-09-28: a probe test skipping with a stated reason yields `1 passed, 1 skipped` and `grep -c` on the reason string returns `0`, both serially and under the configured `-n auto`; adding `-rs` prints `SKIPPED [1] ...: <reason>` |
| F2 | HIGH | `tests/deselect_notice.pytest_terminal_summary`; `release-review/08-final-ship-review.md` | **A THIRD OPTION EXISTS AND IS STRICTLY LOUDER THAN EITHER OF THE ITEM'S TWO.** A collection-time marker is announced in EVERY run (`NOTE: N tests were deselected by -m/-k and did not run ... run everything with: make test-all`) and is RESTORED at the release gate, which mandates `make test-all` / `-m ''`. Nothing announces or restores a runtime skip. So the honest answer to `OQ-01` is a three-way ordering, not a choice between two. | measured: the `NOTE:` line present on a default run of a `livecorpus`-marked module; the release-review text quoted in Step 0 |
| F3 | MEDIUM | `tests/test_ipd_set_plan.py` `TestCorpusNoRegression` | **THE ONE REAL IN-TREE CASE CONTAINS A SILENT VACUOUS PASS, AND THE SKIP IS THE HEALTHY HALF.** Both tests enumerate the live corpus through the relative glob `.aw/records/plans/*/*.ipd.md`, resolved against the process CWD. `test_tracked_orchestrators_mostly_parse` skips when the count is zero; `test_every_refusal_states_a_reason` loops over the empty glob and reports PASS having asserted nothing. This is the outcome the rule must forbid, and it is already happening. | measured from a CWD without the corpus: `1 passed, 1 skipped`, the PASS being `test_every_refusal_states_a_reason` (per-test `-v` output) |
| F4 | LOW | `tests/test_ipd_set_plan.py` | THAT CLASS IS ALSO AN UNMARKED LIVE-CORPUS TEST, which is the hazard `pyproject.toml`'s `livecorpus` prose documents: it asserts a ratio floor over every tracked plan, so an agent authoring a plan can turn it red and block integration for unrelated concurrent lanes. Recorded as CONTEXT for E-04's mechanism choice and NOT as a licence to widen scope into a marker audit; whether this class should carry the marker is a judgement E-04 may reach but this plan does not presuppose. | the class body's `glob.glob` plus `assertGreaterEqual(parsed / total, 0.70)`; no `pytest.mark` appears anywhere in the file |
| F5 | LOW | the tree's other skips | MOST EXISTING SKIPS ARE LEGITIMATE AND THE RULE MUST NOT CONDEMN THEM, so E-02's third option is a narrowed permission rather than a prohibition. Of 24 skip sites across 20 files, the large majority are platform or tool-capability guards (Python version floors for `sys.stdlib_module_names`, absent `bash`/`bwrap`, unavailable symlinks on unprivileged Windows, POSIX versus Windows permission models). Only four are environment-conditioned, and only F3's is about the checkout corpus. | census over `tests/**/*.py` for `skipTest`/`skipIf`/`skipUnless`/`pytest.skip`/`skipif`: 20 files of 185 `test_*.py` |
| F8 | MEDIUM | backlog `5mc38x`; `tests/test_nested_tty_noninteractive.py` (deleted) | **THE PRECEDENT THE SOURCE ITEM TELLS THIS PLAN TO CITE IS DEAD, AND CITING IT WOULD WRITE A DANGLING REFERENCE INTO THE STANDING PRINCIPLES.** The item's closing line recommends citing that file's docstring for the no-weakening position. The file was deleted in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), and deleted FOR CAUSE: it `ast.parse`d production sources to count `subprocess` call sites, which P16's first prohibition forbids. The quote was also never in it (it is a review's paraphrase of a `818uru` docstring). So the recommendation would both dangle AND point at a forbidden technique. LIVE REPLACEMENTS USED INSTEAD: P16's "Verify test sensitivity with mutation" bullet, and `DECISIONS.md` D78, which fixed a test that "had started passing vacuously" by restoring the real path rather than relaxing the assertion. | `git log --diff-filter=D` naming `19313eed`; `import ast` and `ast.parse(...read_text(...))` in the deleted file; `git log -S` showing the quote's only origins are records, never that file; `test -f` on the path fails at HEAD |
| F6 | LOW | `agent_workflows/engine.py` versus `pyproject.toml` | THE MANAGED INSTRUCTION TEXT IS STALE ABOUT THE VERY FILTER THIS RULE DEPENDS ON: the installed `HOW TO RUN THE SUITE` paragraph tells every agent that `addopts` supplies `-m 'not slow'`, while the actual value is `-m 'not slow and not livecorpus'`. An agent trusting it would not know a second category is deselected. Out of scope here (see Deferred) but recorded because it is adjacent to F2 and a reader of this plan will notice it. | the `-m 'not slow'` string literal in `engine.py`'s instruction text against `addopts` in `pyproject.toml` |
| F7 | LOW | scope and work-kind | THE VACUOUS PASS IS A TEST-QUALITY DEFECT, NOT A PRODUCT BUG, so this plan inherits `followup` from the backlog item and carries NO release gate, and that is deliberate rather than an evasion of the every-live-bug-gates-the-release rule. It changes no shipped behavior and is user-imperceptible: it weakens a guard only when the suite is run from an unusual CWD, and the guard is fully effective from the repository root, which is how every gate runs it. | the class asserts over tracked records only; no `agent_workflows/` path is in `- Scope-Paths:` |

## Proposed changes (ordered, validatable)

1. Measure the visibility of a runtime skip, the same skip with `-rs`, a marker deselect, and the CI invocation, establishing the asymmetry the rule rests on and refuting the backlog item's "loud skip" premise (E-01).
2. Record the three-option ordering with its selecting criteria as a new `###` subsection of `GUIDING_PRINCIPLES.md` principle 16, including the CI caveat and the no-weakening prohibition (E-02).
3. Point at it from `CONTRIBUTING.md` `## Authoring conventions` with one bullet and no restatement (E-03).
4. Apply the rule to `TestCorpusNoRegression` so neither of its tests can report a silent green with no corpus present, without lowering the `0.70` floor (E-04).

REVIEW NOTE ON THE SHAPE OF THIS PLAN: three of its four items are prose, and that is the correct
proportion for this item rather than an under-delivery. The backlog item states plainly that "no test in
the tree needs the answer today", so the deliverable is a decision recorded where an author and a reviewer
will find it. E-04 exists so the rule is not vacuous, and it is the smallest application that tests it.

## Deferred / out of scope (with reason)

- ADDING A NEW PYTEST MARKER FOR CHECKOUT-LOCATION DEPENDENCE. Deliberately NOT done, and the reason is a principle rather than an effort estimate: no test in the tree needs one (the backlog item says so, and F5's census confirms only F3's case is corpus-conditioned), so building one now is the hypothetical-need generality P6 forbids. There is also a real design question a speculative marker would prejudge: `livecorpus`'s stated rationale is that an AGENT WRITING A PLAN can turn the test red, whereas a checkout-location test goes red on WHERE the repository sits, and conflating two rationales under one marker would make both harder to reason about. E-02's option two therefore names the marker ROUTE and its criteria; whoever first needs it decides whether `livecorpus` fits or a new marker is warranted.
  - Carrier-Declined: this row defers NOTHING and creates no obligation. It records a decision NOT to build a mechanism, on P6 grounds, and a carrier would manufacture the speculative work the row argues against.
- AMENDING THE MANAGED `AGENTS.md` BLOCK OR `engine.py` SO THE RULE REACHES EVERY MANAGED REPOSITORY. Out of scope on blast radius: that text installs into every managed target repository, and this rule is newly written and unreviewed in practice. `GUIDING_PRINCIPLES.md` is the canonical home, the managed block already points at P16 generally, and an agent working in THIS repository reads the principles. Once the rule has survived contact with a real case, promoting a one-clause reference into the managed block is a reasonable follow-up.
  - Carrier-Declined: a promotion that is explicitly conditional on the rule first proving itself is not an outstanding obligation, and filing a carrier now would assert a commitment this plan deliberately does not make.
- FIXING THE STALE `-m 'not slow'` STRING IN THE MANAGED INSTRUCTION TEXT (F6). A real drift and a genuine defect, but it is a one-line correction in a DIFFERENT file with a different blast radius (every managed repository), and bundling it here would put an unrelated change inside a plan about test conventions. It needs its own backlog item.
  - Carrier: 3wofej
- AUDITING EVERY EXISTING SKIP AGAINST THE NEW RULE. F5 measured 24 sites and found the large majority legitimate (platform and tool-capability guards), so a full audit would mostly confirm conformance. E-04 fixes the one case the rule actually condemns. A sweep is its own plan with its own measurement if the maintainer wants one.
  - Carrier-Declined: the audit's expected yield was MEASURED at approximately zero beyond the case E-04 already fixes, so this is a scope fence rather than deferred work.

## Scope check

- Over-scope: ONE RISK NAMED. E-04 touches a test class that is also an unmarked live-corpus test (F4), and an executor could drift from "stop the vacuous pass" into "audit and mark every live-corpus test". The former is in scope, the latter is explicitly deferred above. E-04's deliverable is bounded to the two methods in that one class.
- Under-scope: the rule is recorded in `GUIDING_PRINCIPLES.md` only and is therefore NOT enforced mechanically and NOT installed into managed repositories. Both are deliberate and argued above (nothing mechanical reads that file today; blast radius). Stated here so a reviewer weighs a known limit rather than discovering it.

## Required tests / validation

1. `python3 -m pytest` BARE, pasted summary line, against a pasted pre-execution baseline taken in the SAME tree. Run it bare: `addopts` already supplies the quiet, parallel and fast-subset flags, and a second `-q` compounds to `-qq` and suppresses the `N passed` line this item requires. A managed worker lane also fails a set of lifecycle tests by design (backlog `770fkp`), so gate on NO NEW failures rather than an absolute count.
2. The four E-01 visibility measurements pasted in full, including the `grep -c` returning `0` for the skip reason under the default run, which is the single measurement the rule's justification depends on.
3. The new `GUIDING_PRINCIPLES.md` subsection quoted in full, shown to carry all three options with their selecting criteria, the CI caveat, and the no-weakening prohibition.
4. The new `CONTRIBUTING.md` bullet quoted, plus a diff confirming it restates no rule and that `## Self-tests` is untouched.
5. THE E-04 BEFORE-AND-AFTER FROM A CWD LACKING THE CORPUS, both pasted with the CWD stated. Baseline to flip: `1 passed, 1 skipped` with the PASS being `test_every_refusal_states_a_reason`. After: no silent green from either test.
6. A MUTATION CHECK ON E-04, cheap and decisive: with the corpus present, break `parse_child_table`'s success path (or the ratio input) and show the floor test FAILS, proving the fix did not convert a real assertion into an unconditional pass. A test green both before and after such a mutation is not asserting anything.
7. THE `0.70` FLOOR SHOWN UNCHANGED by diff, and no assertion in the class shown weakened. This is the plan's own compliance with the prohibition it is writing.
8. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.
9. The throwaway probe test from E-01 confirmed DELETED (`git status` clean of it), so the measurement leaves no residue in `tests/`.

## Spec / documentation sync

No spec change is owed, and that is a measured claim rather than an assumption: no spec in
`.aw/records/specs/` governs test authoring, hermeticity, or vacuous passes, and `- Scope-Paths:` declares
no `.spec.md`. The nearest artifact is draft spec `pqsx96`, whose invariant `I-06` is about test evidence
being forgeable rather than about how a test is written, and which states it produces no enforcement code.

DOCUMENTATION SYNC IS THE PLAN'S SUBSTANCE, not a side effect: E-02 amends `GUIDING_PRINCIPLES.md` and
E-03 adds the `CONTRIBUTING.md` pointer. The managed `AGENTS.md` block is deliberately NOT touched
(deferred above), so no `engine.py` change and no reinstall is implied.

## Open questions

### OQ-01: Is the three-option ordering the one the maintainer wants, given that it demotes the runtime skip the source question favored?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT AUTHORING FROM REPOSITORY EVIDENCE, and recorded as resolved rather than open DELIBERATELY, because leaving it open would assert an outstanding obligation that does not exist and would then need a durable carrier to survive this plan reaching `executed`. There is nothing to carry: the question is ANSWERED below, the answer is IMPLEMENTED by E-02, and approving this plan IS the ratification. THE ANSWER: synthesize first, deselect at collection time with a marker second, runtime skip last. THE EVIDENCE, not taste. Backlog `5mc38x` posed a binary (loud skip versus synthesize) whose "loud" premise MEASUREMENT REFUTES in this repository: `addopts` configures no `-rs`, so a skip reason is printed ZERO times by a default run (F1). And the repository already contains a strictly louder third option the binary omits, a collection-time marker, which `tests/deselect_notice.py` announces in EVERY run and which `make test-all` restores at the release gate `release-review/08-final-ship-review.md` mandates, whereas nothing announces or re-runs a skip (F2). THE HONEST LIMIT ON THAT ANSWER, stated so a reviewer can overturn it on the merits: a skip reason IS visible in CI, which passes `-rfEs`, so the case against a skip rests on the default LOCAL run and on no gate re-running it, not on the reason being unprintable. A maintainer who reads a skip as an honest declaration of a limit could reasonably rank it above a marker; that is a judgement about what a test is FOR, which is how the source item characterized the residue. IF THE REVIEWER DISAGREES, the cost is one paragraph: only E-02's ordering text changes, and E-01, E-03 and E-04 stand unaltered, since E-04 fixes a vacuous pass rather than choosing a mechanism.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all four measurements pasted at execution HEAD, each labelled with the exact command run. (a) MUST include BOTH the summary counts for a skipping probe under bare `python3 -m pytest` AND a `grep -c` (or equivalent) on the reason string returning `0`; the counts alone do NOT satisfy this item, because the zero is the finding. (b) the same probe with `-rs`, showing a `SKIPPED [1] ...: <reason>` line, which proves the cause is the absent `reportchars` rather than pytest suppressing reasons generally. (c) a marker-deselected module under bare `python3 -m pytest`, showing the `NOTE: N tests were deselected by -m/-k and did not run` line. (d) the CI step's `-rfEs` shown by quoted content from `.github/workflows/tests.yml`. PLUS confirmation the throwaway probe was deleted. If any measurement CONTRADICTS the authoring baseline, say so plainly and revise E-02's justification rather than restating the baseline: the rule must follow the measurement, not the reverse.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the new subsection quoted IN FULL from `GUIDING_PRINCIPLES.md`, and checked against four requirements, each confirmed explicitly rather than by a global assertion of conformance: it presents all THREE options in preference order; each option carries the CRITERION that selects it (not merely a description); the CI caveat is present, stating that a skip reason IS visible under `-rfEs` so the objection is to the default local run and to the absence of a re-running gate; and the no-weakening prohibition is present citing ONLY live precedent (P16's mutation-sensitivity bullet and `DECISIONS.md` D78). EVERY PATH THE NEW TEXT CITES MUST BE RESOLVED AND THE RESOLUTION PASTED (for example `test -f` or a `grep` hit per citation): this item FAILS if the text cites `tests/test_nested_tty_noninteractive.py`, which does not exist, since writing a dangling citation into the standing principles is the defect backlog `pn7rw3` already tracks. PLUS structural conformance shown by quoting the two pre-existing `###` subsection headings beside the new one, since P16's subsection form is the shape being matched.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new bullet quoted from `CONTRIBUTING.md`, plus the diff for that file showing ONLY an addition under `## Authoring conventions`. The bullet must be shown to POINT rather than restate: if it reproduces the three-option ordering it fails this item, because duplicating a rule is the drift P8 forbids and the section's own text forbids. Confirm `## Self-tests (run before pushing tool changes)` is byte-unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the before-and-after for `TestCorpusNoRegression` pasted from a CWD LACKING the corpus, with the CWD named in each, at per-test granularity so the identity of the passing test is visible (the baseline's PASS is `test_every_refusal_states_a_reason`, and a summary line alone cannot show that). After the fix, neither test may report a silent green. PLUS the run from the repository root showing both still exercise the corpus and pass. PLUS the mutation check: with the corpus present, break the parse success path and show the floor test FAILS. PLUS the diff showing the `0.70` floor unchanged and no assertion weakened. A fix that makes both tests skip everywhere does NOT satisfy this item, since it would trade a vacuous pass for no coverage at all.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (4 E-items in 2 task groups, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking: execute the three-option ordering as written and do not
re-open the choice mid-execution. SCOPE FENCE: `- Scope-Paths:` declares `GUIDING_PRINCIPLES.md`,
`CONTRIBUTING.md` and `tests/test_ipd_set_plan.py`; an out-of-scope edit must be genuinely required and
then justified to `aw ipd finalize` with a `--scope-reason` per path. THE FOUR THINGS THIS PLAN MUST NOT
DO, each a short path to a change that reads as progress and is not. FIRST, do NOT lower the `0.70` ratio
floor or delete either test in `TestCorpusNoRegression`: the floor is a measured no-worsening guard, and
weakening it is precisely the move E-02 is writing a prohibition against, so doing it inside this plan
would refute the plan. SECOND, do NOT make both tests skip unconditionally to make the class quiet; that
trades a vacuous pass for no coverage, which is worse than the defect. THIRD, do NOT add a new pytest
marker: no test needs one, and P6 forbids building for a hypothetical need (see Deferred). FOURTH, do NOT
edit the managed `AGENTS.md` block or `engine.py`; that text installs into every managed repository and is
deliberately out of scope, including the stale `-m 'not slow'` string F6 records. THE HARD-MUST HONESTY
RULE: paste the ACTUAL command output for every `V-*`. V-01(a) requires the `grep -c` returning `0`, not a
claim that the reason was absent; V-04 requires per-test output from a CWD without the corpus, since a
summary line cannot show WHICH test passed vacuously; and if a measurement contradicts this plan's
authoring baseline, revise the rule's justification and say so rather than restating the baseline. Commit
path-scoped through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until `aw ipd lint --phase
pre-transition` conforms and every `V-*` carries real observed evidence.
