# Review findings: plan jw6cm3

- Subject-Id: jw6cm3
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-501 (HIGH, fixed), PR-502 (MEDIUM, fixed), PR-503 (MEDIUM, fixed), PR-504 (MEDIUM, fixed), PR-505 (LOW, fixed), PR-506 (LOW, fixed)

## Round 1

Reviewed at HEAD `5367778d` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

THIS PLAN'S CENTRAL CORRECTION OF ITS OWN BACKLOG ITEM IS RIGHT, AND I RE-DERIVED EVERY LOAD-BEARING
MEASUREMENT RATHER THAN READING IT. The backlog item `ihgjii` diagnosed the two narrowing sites as
redundant belt-and-braces and offered "drop the redundant fast-path filter" as one of two remedies. The
plan says that is false and that the remedy would ship a bug. It is correct on both counts.

Mutating each site SEPARATELY, in memory, against the live 2009-record corpus reproduces fact 1's
disjointness in all eighteen cells: `killFAST` changes the type set for `setid` (`['plans']` to
`['backlog']`) and `id6` (`[]` to `['backlog']`) and NOTHING else; `killRESOLVER` changes it for `status`
(`['plans']` to `['backlog','plans','specs']`), `substring` (`['plans']` to `['backlog','plans']`) and
`stem` (`[]` to `['backlog']`) and nothing else. Fact 2 reproduces VERBATIM through the real verb,
including the precise message degradation: at HEAD `aw ipd dependencies set pz34kx none --dry-run --yes`
refuses with `No plans artifact matched 'pz34kx'`, and with the fast-path filter removed it refuses with
`Selector 'pz34kx' did not resolve to a plan`, which is a wrong-type report about a record a plans-scoped
resolver should never have surfaced. Fact 3, the plan's most important claim, reproduces: with the
resolver branch disabled the ENTIRE bare suite passes (`3346 passed, 2 skipped, 3 warnings in 105.97s`),
so three selector kinds have no regression test at all. Fact 4 reproduces. Facts 5 and 6 reproduce in
shape. F-7's two-unnarrowed-callers claim verified by reading both call sites. F-8's spec quotations are
exact: N3's paragraph does read "ONE DOCUMENTED HOLE THAT N3 MUST NOT BE READ AS CLOSING" and names only
the direct-PATH exemption, and criterion 5 does ask for "a REGRESSION TEST" singular.

I ALSO PROTOTYPED ALL FOUR INTENDED TESTS BEFORE SIGNING OFF, because a plan whose entire deliverable is
"add the missing pins" is worth nothing if the pins cannot be written. Four throwaway tests over a
fixture corpus spanning plans and backlog: all four pass at HEAD, all four fail under `killRESOLVER`, and
exactly the `id6` one fails under `killFAST`. The deliverable is achievable and provably non-vacuous.
That probe is what surfaced the two smaller findings below, and it is a throwaway, not the deliverable.

THE ONE MEASURED ERROR, which is why a HIGH finding sits on an otherwise exemplary plan. E-04 specifies
the `id6` assertion as a FAST-PATH pin and V-04 demands "pasted FAILURE under the fast-path mutation" as
its evidence. Prototyping it measures that an `id6` test fails under BOTH mutations, so that evidence
does not show what V-04 claims it shows: a `killFAST` failure on an `id6` assertion is equally produced
by the resolver mutation, and therefore isolates neither site. The plan already knew this and contradicted
itself: Goal fact 1's table records `id6` breaking in both columns and its own parenthetical explains why
("the fast path's early return is what stops the resolver being consulted at all"). The remedy is not to
weaken the item but to complete it: the `setid` kind IS fast-path-specific (it fails `killFAST` and
survives `killRESOLVER`), so E-04 now asserts the `setid` case beside the `id6` case and V-04 requires
both mutation columns for the `id6` test plus the `setid` pair that actually discriminates. Without this,
an executor would have produced honest-looking mutation evidence for a claim it did not support, in a plan
whose whole subject is that a pin can pass while proving nothing.

THREE GAPS OF MEASUREMENT, none of which changes the deliverable. FIRST, fact 5's performance figures have
drifted by roughly a factor of five in four days (`status` miss 134.52ms at authoring, 680.42ms at review)
for six percent corpus growth, and the plan presents them as flat facts. The ARGUMENT is untouched and is
in fact stronger (the ratio went from about 2500x to about 7800x), but an executor re-deriving them would
have found every number wrong and had no instruction for what to do about it. Restated so the ratio is the
durable claim and no millisecond figure is a bar. SECOND, the plan measured `killFAST` against the MODULE
only. The full-suite number is the one that makes F-4's claim precise, and it is exactly one failure, so
the coverage either side of `match_selector` is one test versus zero tests rather than a vague "some"
versus "none"; measured and added. THIRD, E-01's matrix instruction says to record the result "even if it
differs" without saying which parts are expected to differ. Every `n=` count moved between authoring and
review while every TYPE SET held, so the instruction now names the type sets as the assertion and the
counts as context, which is the repository's own live-artifact convention.

TWO SMALLER ITEMS. E-06 amends a spec whose `- Status:` is `approved` and said nothing about that, leaving
an executor to choose a mechanism; `aw specs note` is the correct verb (it appends an attributed history
record without touching status) and E-06 now names it, forbids `aw specs set` on this spec, and requires
the diff to show `- Status: approved` byte-unchanged. And the fixture helper `create_backlog` writes into
`.aw/records/backlog/<status>/` while `setUp` creates only `open` and `done`, so prototyping E-02 with a
shared `reviewed` token raised `FileNotFoundError`; recorded in E-02 so that failure is not mistaken for a
resolution bug.

ONE QUESTION THE PLAN ASSERTED RATHER THAN ARGUED, now resolved as OQ-03. The gate paragraph justifies
`chore` by quoting the item's own reasoning without testing it against fact 3, which is a strictly worse
finding than the item had (a NORMATIVE spec guarantee with zero tests, in a repository that gates releases
on known bugs). I checked it and `chore` is right: HEAD returns the CORRECT answer in every one of the
eighteen matrix cells, so nothing is user-perceptible and the repository's own test for a defect is not
met. A `bug` classification would also be self-defeating, attaching `Blocks-Release: next` to a change
that alters no runtime behavior.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | HIGH | IN-SCOPE | E. Testing / D. Anti-regression (mutation evidence that does not isolate what it claims) | Prototyped a foreign-type `id6` assertion over an unnarrowed fixture inventory and ran BOTH mutations: it FAILS under `killFAST` AND under `killRESOLVER`. A `setid` assertion on the same corpus fails `killFAST` and PASSES `killRESOLVER`. The plan's own Goal fact 1 table already shows `id6` breaking in both columns | **E-04 specifies the `id6` test as a FAST-PATH pin and V-04 demands a `killFAST` failure as its proof, but that failure is equally produced by the resolver mutation, so the evidence isolates neither site.** No single-kind `id6` test can distinguish the two sites; the only fast-path-specific kind is `setid`. In a plan whose entire subject is that a pin can pass while proving nothing, shipping a required-evidence item that cannot support its own claim is the defect that matters, and the plan contradicts its own fact 1 in doing so | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-9 records the both-mutations measurement and that `setid` is the discriminating kind. E-04 retitled off "PIN THE FAST-PATH SITE", now requires the `setid` companion assertion beside the `id6` one and explains why the obvious form is wrong. V-04 requires BOTH mutation columns for `id6` (stating that failing under both is expected, not a defect) plus the `setid` fail-under-killFAST / pass-under-killRESOLVER pair, and explicitly refuses a lone `id6` killFAST failure. The `- Scope:` line and proposed-changes entry 4 updated to match. E-05's site comment must record that `id6` alone cannot isolate either site |
| PR-502 | MEDIUM | IN-SCOPE | G. Plan executability (live-artifact figures presented as flat facts) | Re-measured at review on a 2009-record corpus against authoring's 1903: `setid` hit 0.08 -> 0.28ms, `status` miss 134.52 -> 680.42ms, `substring` miss 133.60 -> 495.47ms, filter 0.053 -> 0.0866ms | **Fact 5's four millisecond figures have moved by up to five-fold in four days for six percent corpus growth, and the plan states them without a re-derivation instruction.** The conclusion is untouched and is in fact strengthened (the filter-to-resolver ratio grew from about 2500x to about 7800x), but an executor re-deriving would find every figure wrong with nothing telling them whether that is a finding | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fact 5 rewritten with both measurement columns side by side, the RATIO named as the durable claim, an explicit "no millisecond figure here is a bar", and an instruction that a mismatch is expected and must not be reported as a finding. F-5 restated the same way |
| PR-503 | MEDIUM | IN-SCOPE | Evidence accuracy (a coverage claim measured at the wrong scope) | `killFAST` with the full bare suite: `1 failed, 3345 passed, 2 skipped in 70.04s`, the single failure being `test_scoped_setid_resolution_returns_only_the_scoped_type`. The plan measured only the module (`1 failed, 78 passed`, now 81) | **F-4 claims the fast-path site "IS pinned" on a module-scoped measurement, which cannot distinguish one pin from several and leaves the asymmetry with F-3 imprecise.** The full-suite number is what makes the finding sharp: exactly ONE test in the repository catches the fast-path mutation and ZERO catch the resolver one, so the comparison is one versus zero rather than "some" versus "none" | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal fact 4 and F-4 both carry the full-suite line beside the module line, with the one-versus-zero point stated explicitly; the module's growth from 78 to 81 noted so the drift is visible. V-01 now requires BOTH the module and full-suite summaries under the fast-path mutation, since F-4's precision rests on the latter |
| PR-504 | MEDIUM | UNDER-SCOPE | G. Plan executability (an approved-spec amendment with no named mechanism) | `.aw/records/specs/approved/20260910-2lcqno-...spec.md` carries `- Status: approved` and a `2026-09-13 approved (aw set, --by-human)` history record. `aw specs note --help`: "Append a workflow-history record to a spec WITHOUT changing its status" | **E-06 amends an APPROVED spec and says nothing about its status or how to record the amendment**, leaving an executor to pick between `aw specs set` (which would re-assert or demote an approval this plan has no authority to touch) and a hand-edited history block (which forges attribution). The amendment itself is legitimate, so the gap is the mechanism, not the intent | C:Low; U:Low; S:Medium; F:Low; Overall:Low | FIXED | E-06 now names `aw specs note` with its rationale, explicitly forbids `aw specs set` on this spec and forbids hand-editing the history, and states that the approval and N3's normative requirement are both untouched because these are corrections of fact. Its expected outcome and V-06 both require the exact invocation plus a diff confirmation that `- Status: approved` is byte-unchanged. The spec-sync section carries the same statement |
| PR-505 | LOW | IN-SCOPE | G. Plan executability (an executable-fixture trap) | Prototyping E-02 with a `reviewed` token shared across plans and backlog: `FileNotFoundError: .../.aw/records/backlog/reviewed/...`. `StatusSetTestBase.create_backlog` writes to `backlog/<status>/` and `setUp` creates only `open` and `done` | **E-02 instructs the executor to build a fixture whose several types share one status token, and the obvious choice fails with a filesystem error that looks nothing like a narrowing bug.** A cycle lost to a fixture error is cheap but avoidable, and it lands precisely on the plan's central deliverable | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-10 records the constraint and the measured error. E-02 names it, gives the working token (`open`), and offers the alternative of creating the bucket in the fixture, with an explicit warning not to assume the helper will place a plans-only status |
| PR-506 | LOW | IN-SCOPE | G. Plan executability (an unargued classification, and an unstated expectation in E-01) | Matrix re-derivation: every `n=` cell moved between authoring and review (for example `status approved` scoped `n=5` -> `n=9`, under `killRESOLVER` `n=22` -> `n=26`) while all eighteen TYPE SETS held. HEAD's type set is the scoped type in every cell | **Two small clarity gaps.** E-01 says to record the matrix "even if it differs" without saying WHICH parts are expected to differ, so an executor could report normal corpus growth as a contradiction of fact 1. And the gate paragraph justifies `chore` by quoting the backlog item's reasoning without testing it against fact 3, which is a materially worse finding than the item had (a normative guarantee with zero tests) in a repository that gates releases on known bugs | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now names the TYPE SETS as the durable assertion and the counts as context, records that every count moved at review, and notes the matrix may be derived by in-memory monkeypatching (as review did) so no file mutation risks being committed. V-01 restated to match. New OQ-03 resolves the classification question from measurement, confirming `chore`, and the gate paragraph points at it |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-501: an `id6` test cannot isolate either narrowing site. Drop the `id6` pin, retarget it, or add a discriminating companion? | ADD the `setid` companion assertion and require both mutation columns for `id6` | (a) Drop the `id6` assertion and pin the fast path with `setid` alone; (b) keep E-04 as written and let the executor paste a `killFAST` failure that does not isolate; (c) rewrite V-04 to demand only that the `id6` test fails "under at least one mutation" | Option (b) is the finding. Option (c) is worse than (b) because it would knowingly weaken the evidence bar in the one plan whose subject is vacuous pins. Option (a) is the tempting minimal fix and loses a property worth having: the `id6` case is what `run_dependencies_set_command` actually relies on for its `No plans artifact matched` refusal, measured in F-2 as the exact behavior the backlog item's remedy would have broken, so a pin on it guards a real caller even though it cannot attribute the guard to a site. Keeping both and requiring the pair is the only option that pins the caller-visible property AND supplies a mutation argument that discriminates | yes |
| D-2 | PR-502: the performance figures drifted five-fold. Update the numbers, drop them, or change what they assert? | CHANGE THE ASSERTION to the ratio; keep both measurement columns as dated history | (a) Replace authoring's figures with review's; (b) delete fact 5 as unnecessary since fact 1 already settles removability; (c) leave them | Option (a) rots identically and faster than most, since the resolver cost moved five-fold in four days. Option (b) is arguable (fact 1 does settle the question on correctness alone) but throws away the answer to the item's OWN framing, which was explicitly a performance argument, and the plan is right that rebutting the item on its own ground is worth doing. Keeping both columns shows the drift rather than hiding it, and the ratio is stable in magnitude class across a 5x absolute change, which is what makes it the durable claim | yes |
| D-3 | PR-504: the spec is `approved`. Amend it in this plan, or split the amendment out? | AMEND IT HERE, recorded with `aw specs note` | (a) Split the spec amendment into its own plan so an approved contract is not touched by a chore; (b) use `aw specs set` to re-record a status alongside the edit; (c) hand-edit the history block | Option (b) is the dangerous one and is now explicitly forbidden in E-06: re-running a transition on an approved spec either re-asserts an approval this plan has no authority to make or demotes a contract nobody asked to reopen. Option (c) forges attribution. Option (a) was weighed seriously and rejected on the repository's own rule that a plan changing behavior a spec describes SHOULD carry the amendment in the same change, plus the specific reason this spec is WHY the item existed: leaving N3 unamended keeps the approved contract licensing the exact misreading being corrected. `aw specs note` exists for precisely this case and touches no status | yes |
| D-4 | PR-506: does fact 3 (a normative guarantee with zero tests) make this a `bug` rather than a `chore`? | `chore` CONFIRMED, recorded as OQ-03 | (a) Reclassify `bug` and attach `Blocks-Release: next`, since the repository does not ship known bugs and an untested normative guarantee is a live risk; (b) leave the classification unexamined, as the plan did | Option (a) is the one I had to rule out carefully, because fact 3 IS worse than the backlog item knew. It fails on the repository's stated test: user-perceptible impact. Measured, HEAD returns the correct type set in all eighteen matrix cells, so no user can perceive anything and the defect is entirely in coverage and record. `AGENTS.md` is explicit that risk a user cannot notice is not a defect, and equally warns against over-filing. A second reason seals it: `bug` would gate a release on a change that alters no runtime behavior, while the outcome the gate exists to prevent is measurably absent. Option (b) leaves a reader unable to tell whether the classification survived the plan's own worst finding | yes |
| D-5 | Should review author the four tests, having prototyped them successfully? | NO; the prototype stays a throwaway probe outside the deliverable | (a) Promote the prototype into `tests/test_status_set.py` as part of this review, since it is measured working; (b) attach the prototype source to the plan as the intended implementation | The workflow is explicit that plan-review edits planning documents only and does not write code; a reviewer landing the tests would also destroy E-01's gate (the executor's own re-derivation) and pre-empt OQ-02, which is the executor's recorded choice about where the tests live. Option (b) is subtler and still wrong: pasting prototype source into the plan would freeze fixture details a reviewer probed in minutes into an executable contract, and the probe deliberately cut corners the deliverable must not (it lives outside the test tree and asserts nothing about corpus shape). What the prototype legitimately contributes is EVIDENCE that the work is achievable (F-11) and two measured constraints (F-9, F-10), all of which are recorded as findings the executor can act on | yes |
