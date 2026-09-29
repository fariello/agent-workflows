# Review findings: plan ck0vya

- Subject-Id: ck0vya
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a8e41cc6` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0) with two `IPD-Z602` density advisories, and `--phase
review-finalize --agent` conforms after revision (exit 0, same two advisories, each examined and
recorded). No pre-review snapshot was owed: the plan was committed and unmodified, byte-identical to
its `.aw/state/lane-inputs/rev-10/` copy (`diff` reported no difference). NO PRODUCTION FILE WAS
MODIFIED BY THIS REVIEW: every probe ran against purpose-built ledger fixtures under `/tmp`, and the
only tracked files this review writes are the plan, this record, and the two backlog items PR-802
required.

**EVERY ONE OF THE PLAN'S ELEVEN AUTHORED FINDINGS REPRODUCED INDEPENDENTLY.** That is worth stating
plainly because it is unusual, and because the findings below are corrections to a fundamentally
sound plan rather than doubts about its diagnosis. F-01: `runs resume` is declared
`command_class='mutation'` while `runs next` is `read`, and `run_recovery.resume`'s whole body is
`reconstruct_state()`, `detect_unknown_outcomes()`, a conditional raise and a `ResumeReport`. F-02:
`run_viewer.RUNS_VIEWER_LEAF_NAMES` contains `resume` among nine read-only leaves and no test compares
that tuple to any `command_class`. F-03: the exit matrix reproduced on all six rows. F-04: appending a
`step_attempt` with `state='running'` raises `SchemaInvalidRecordError` with finding `RL-E030`
"attempt state must be one of ['blocked', 'failed', 'performed']", `run_state.STATE_RUNNING in
ATTEMPT_STATES` is `False`, and the two-process sequence behaves exactly as described (`run start`
prints `Started step s1 (state: running)`, the ledger's kinds stay `['run']`, and a new-process
`runs resume` reports `pending` at exit 0). F-05: all three named test files are absent from the tree
and `19313eed --stat` lists them at 224, 339 and 252 deletions; `conformance_matrix.py` survives with
its only in-tree references being its own definitions plus one comment in `command_surface.py`; and
`required_scenarios` measured on the live declaration returns `(..., 'json', 'success_preview')`
versus `(..., 'json')` under `command_class='read'`, so the delta is exactly `{'success_preview'}`
DROPPING with nothing added, as F-04/F-05a claim and contrary to the backlog item. F-06: `run_cli` has
no `import agent_schema` (its three `agent_schema` hits are all inside comments), and eight
declarations already carry a code above 2. F-07: the tree is green. F-08: the sibling matrix
reproduced exactly, including that exit 3 IS reachable on `runs next`. F-09: `command_class` is
asserted in exactly three test files and `exit_contract` in two, none naming `resume`. F-11: all nine
tuple members carry declarations, `resume` is the single one declared `mutation`, and the four
mutating verbs (`analyze`, `export`, `submit`, plus `query` which is `read` but outside the tuple) are
correctly outside it.

**PR-801 (BLOCKER): E-03's HANDLER-PURITY ASSERTION IS PROHIBITED BY THE REPOSITORY'S OWN TEST
CONTRACT, AND IS ALSO WEAK.** The item instructed the executor to "walk the AST of
`run_recovery.resume` via `inspect.getsource` and assert it contains no call to `store.append`,
`record_step_attempt`, `cancel_run`, `open`, or `write_text`". `AGENTS.md` forbids precisely this in
its own words ("NEVER write or restore tests that read production source code using `inspect`, `ast`,
regex, or substring search") and GUIDING_PRINCIPLES P16 names `inspect.getsource` and `ast.parse`
literally under "No production source inspection", adding that its one narrow exception applies only
where the text itself is the artifact under test, which production code never is. Severity is BLOCKER
rather than HIGH because executing the item as written produces a test the repository's own
contributor contract says must not exist, so the plan could not be executed faithfully and correctly
at the same time. It was also weak on its own terms: a five-name denylist passes a handler writing
through `Path.open`, `os.replace`, a helper, or any new store method, so it would have licensed the
regression it claimed to guard. Review measured the behavioral replacement and it is strictly
stronger: snapshot the ledger bytes and record count, drive the CLI, assert both unchanged.

**PR-802 (HIGH): TWO `Carrier-Declined` ROWS ASSERT THAT A CARRIER IS OWED, WHICH TRACKS THE
OBLIGATION NOWHERE.** The first reads "A carrier is genuinely owed here and OQ-01 names what it must
cover, so this row is a HANDOFF rather than a refusal"; the second reads "A carrier is owed and OQ-02
names its content". But `Carrier-Declined` is defined in `ipd_schema` as "the explicit recorded
decision not to carry it, the analogue of `aw backlog set done --blocks-release -`", so asserting an
obligation through the field that disclaims one is self-contradictory, and review confirmed no backlog
item existed for either. The consequence is concrete rather than formal: `check.ipd-uncarried-obligation`
is satisfied by a declined row, so both obligations would have passed every mechanical gate and
existed only in this plan's prose, and the first of them is a real latent bug in the run engine.
Review filed both from its own measurements. Note that `tzqvjn` auto-gated to `Blocks-Release: next`
on filing, because it is a `bug` and the repository's every-live-bug policy applies, which is itself
evidence the obligation was worth tracking.

**PR-803 (MEDIUM, UNDER-SCOPE): THE GATE CARRIED NO SCOPE FENCE.** The gate is otherwise one of the
better ones in this sweep (it has an approval summary, an honest silent-failure warning, a
do-not-re-derive note, and a reasoned statement of why no release gate applies), but it gave the
runner no declaration to reconcile the diff against, and this plan carries six distinct prohibitions
spread across its Scope statement and four Deferred rows, including one the executor is most likely
to violate by accident (writing a source-inspecting test).

**PR-804 (MEDIUM): THE EXIT-5 FIXTURE AS DESCRIBED IS NOT REPRODUCIBLE, AND A NAIVE `append` IS
REFUSED.** F-03 calls it a "hash/schema-invalid ledger", and review measured that tampering
`record_hash` OR a payload field on a single-record ledger yields exit 0, not 5, because nothing
re-derives that hash on read. Exit 5 needs a chain break across TWO records, or a `seq` gap, or an
unparseable line. Separately, building any valid fixture at all took five successive refusals
(`RL-E010` missing `schema_version`/`actor`/`parent`, `RL-E015` `run_id` shape, `RL-E020` four missing
`run` fields, `RL-E014` unknown actor role, `RL-E011` `parent` typed `None`). The sibling plan
`fuuw94` recorded the identical trap as its own F-9, so this is a known stall point in this area of
the tree and the recipe belongs in the plan.

**PR-805 (LOW): THE SUITE BASELINE HAD DRIFTED 171 TESTS AND WAS USED AS AN ACCEPTANCE BAR IN FOUR
PLACES.** Authored `3075 passed, 2 skipped`; review measured `3246 passed, 2 skipped, 3 warnings in
52.35s`. The plan also quotes the `addopts` marker as `not slow` where it is `not slow and not
livecorpus`, and its `aw check` comparison keys on the integer 4 whose MEMBERSHIP shifted between
authoring and review even though the count held.

**PR-806 (LOW): F-10's CONTENTION ANALYSIS HAD DECAYED, AND THE REPLACEMENT NEIGHBOUR IS MORE
INTERESTING.** The plan named `9vglxd` as the one pending plan declaring `command_surface.py`; it has
since executed. Re-measuring found `fuuw94` (`reviewed`, `go-pending-approval`) changing `run_cli`'s
corruption exit codes, i.e. the adjacent behavior this plan declares. The conclusion survives, but for
a different reason, and it needed verifying rather than inheriting: `fuuw94` touches neither of this
plan's paths and treats `resume` only as a control row that must already return 5, which is exactly
what this plan declares.

**PR-807 (LOW): THE TWO `IPD-Z602` DENSITY ADVISORIES NEEDED A RECORDED ANSWER.** A flagged density
advisory is an actionable right-sizing signal, not noise to pass over. Review applied the four
splitting diagnostics to E-02 and E-03 and concluded NEITHER warrants a split, for different reasons,
and recorded that reasoning in `## Scope check` so a later reader sees the question was answered
rather than ignored.

**WHAT REVIEW CHECKED AND FOUND SOUND.** The plan's central design decision, to fix the DECLARATION
and refuse to touch the code, is correct and its enforcement mechanism (V-02's before/after fixture
comparison) is the right one, especially given F-09's measurement that no existing test could detect a
behavior change here. Removing exit 3 rather than keeping it is right, and the unreachability argument
is airtight on measurement. The `(0, 2, 5, 7)` contract is admissible, and the F-06 reasoning for why
the `(0, 1, 2)` agent-schema cap does not bind is accurate. The deliberate omission of 1 follows a
real shipped precedent (`reviews decisions` carries `(0, 2)`). The decision not to import
`conformance_matrix.py` is correct and well argued. The plan is notably honest in three places most
plans are not: it FALSIFIES two of its own backlog item's claims rather than inheriting them, it
states the one way it can fail silently, and it explains why carrying no release gate is correct
rather than leaving the absence unexplained. Right-sizing at four E-items is appropriate.

Every finding is FIXED by in-place revision. None was deferred, so no escalation to a `- Blocking:
yes` question is owed and none was written. Both open questions survive review UPHELD on re-measured
evidence, each now naming the real carrier PR-802 filed.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | BLOCKER | IN-SCOPE | E. Testing / F. Principles | `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS)" clause (1) read verbatim; `GUIDING_PRINCIPLES.md` section 16 "No production source inspection", naming `inspect.getsource`, `inspect.getsourcelines`, `ast.parse` and `read_text()`; review's behavioral probe over a real fixture returning exit 0 with `bytes identical: True`, `sha256 identical: True` (`2c80457e7077a4e7`), `record count 1 -> 1`, unchanged mtime, and an unchanged directory listing (verified in a fresh directory that `runs resume` leaves no `.lock` behind) | E-03's ASSERTION (2) INSTRUCTED A PROHIBITED SOURCE-INSPECTING TEST. It required walking `run_recovery.resume`'s AST via `inspect.getsource` to assert five named calls are absent. `AGENTS.md` and P16 forbid exactly this, so the item could not be executed faithfully AND correctly. It was additionally a denylist, so a write through any unlisted mechanism would have passed the guard that claims to prevent one. | C:Low; U:Low; S:Low; F:Low; Overall:Low (review measured the behavioral replacement working, and it is strictly stronger) | FIXED | Assertion (2) rewritten to prove purity BY OBSERVATION (sha256 of the ledger bytes, record count, and no new file in the directory), with review's measurements quoted and the prohibition cited. Assertion (4) likewise re-specified to use a runtime-constant comparison or, preferred, an EXERCISED `RL-E030` refusal rather than any source read. Added F-14 and a Step-0 conventions bullet stating the prohibition. V-03 now requires `rg` over the new file for `getsource\|ast\.parse\|read_text` returning NOTHING, and Required tests carries the same check. The scope fence forbids it explicitly. |
| PR-802 | HIGH | IN-SCOPE | G. Plan executability (obligation tracking) | `ipd_schema.CARRIER_DECLINED_FIELD`'s docstring: "the explicit recorded decision NOT to carry it, the analogue of `aw backlog set done --blocks-release -`"; the two rows' own text asserting "A carrier is genuinely owed here" and "A carrier is owed"; a search of `.aw/records/backlog/` finding no item for either obligation before review filed them | TWO DEFERRED ROWS ASSERTED AN OBLIGATION THROUGH THE FIELD THAT DISCLAIMS ONE, so both were tracked nowhere and would have passed `check.ipd-uncarried-obligation` silently. One of them is a real latent run-engine bug whose `resume` docstring advertises a fail-closed guarantee that cannot fire across a process boundary. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Review filed both items from its own measurements: `tzqvjn` (`open`, `bug`, auto-gated `Blocks-Release: next`, carrying the `RL-E030` refusal, the two-process sequence and the three appendable-state sweep) and `4bicgv` (`open`, `chore`, carrying the three-verb matrix). Both rows converted to `- Carrier:` with a `Carrier-Note` recording the correction and retaining the original (correct) reasoning. Both OQ resolutions updated to name their carrier. `aw check plans` confirms both ids resolve. |
| PR-803 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | the gate as authored, carrying an approval summary, a silent-failure warning and a do-not-re-derive note, but no scope fence; six prohibitions spread across the Scope statement and four Deferred rows | THE GATE HAD NO SCOPE FENCE. The runner had no declaration to reconcile the diff against, and the prohibition an executor is likeliest to violate by accident (writing a source-inspecting test, PR-801) sat nowhere an executor looks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE naming both paths and all six negative constraints (no `run_cli` code path, no other declaration or field, no sibling-leaf correction, no `EXIT_BLOCKED` work, no conformance-harness restoration, no source-inspecting test), written as a DECLARATION with no "STOP and report" clause per the 2026-09-01 maintainer ruling. Also added the `fuuw94` awareness note (F-15). The stale `to-review` self-description was updated to the reviewed state with its approval command. |
| PR-804 | MEDIUM | IN-SCOPE | E. Testing and verification | single-record `record_hash` tamper -> exit 0; single-record payload tamper -> exit 0; two-record `prev_hash` overwrite -> exit 5 (`Broken hash chain at seq 1: expected prev_hash '668decb0...', got '00000000...'`); `seq` gap -> 5; unparseable line -> 5; five successive `SchemaInvalidRecordError` tuples (`RL-E010`, `RL-E015`, `RL-E020`, `RL-E014`, `RL-E011`) before a valid `run` record appended | THE EXIT-5 FIXTURE IS NOT REPRODUCIBLE AS DESCRIBED, AND FIXTURE CONSTRUCTION IS THE LIKELIEST STALL POINT. "hash/schema-invalid ledger" is too loose: the obvious reading (tamper a hash on one record) yields exit 0. `RunLedgerStore.append` also refuses an improvised record five different ways. The sibling plan `fuuw94` recorded the identical trap, so this is a known hazard in this area. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 with every measurement, and a paragraph in E-03 giving the exact schema recipe and all four fixtures, including an explicit note on what does NOT work and why. F-03's loose phrase corrected to "CHAIN-BROKEN ledger" with a pointer to F-12. V-02 now requires the chain-broken two-record fixture by name and states that a single-record hash tamper does not demonstrate exit 5. |
| PR-805 | LOW | IN-SCOPE | E. Testing (live-artifact criteria) | authored `3075 passed, 2 skipped, 3 warnings in 55.65s`; measured `3246 passed, 2 skipped, 3 warnings in 52.35s` at HEAD `a8e41cc6`; `pyproject.toml` `addopts` read verbatim as `-m 'not slow and not livecorpus'` against the plan's quoted `-m 'not slow'`; `-m slow` collects 202; `aw check` errors still 4 but with shifted membership | A TRANSCRIBED SUITE TOTAL WAS USED AS AN ACCEPTANCE BAR IN FOUR PLACES AND HAD DRIFTED 171 TESTS. The `addopts` marker expression was also quoted incompletely, and the `aw check` comparison keyed on an integer whose membership changed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04, its Expected outcome, Proposed change 4, Required tests and V-04 all re-specified to RE-DERIVE the baseline on the pre-change tree and judge on the PROPERTY, with review's figures marked context only. F-07 rewritten to assert the green PROPERTY with its counts as context. The `addopts` quote corrected in two places. The `aw check` item now compares the named error SET rather than the count. Added F-13 and a Step-0 bullet. |
| PR-806 | LOW | IN-SCOPE | C. Architecture and operability (cross-plan) | `find .aw/records/plans -name '*9vglxd*'` resolving under `executed/`; `rg -l command_surface .aw/records/plans/pending/` returning this plan plus `cpi6p3`, `fuuw94`, `ygb3nk`; `fuuw94`'s `- Scope-Paths: agent_workflows/run_cli.py, tests/test_run_cli_corruption_exit.py`, its `- Status: reviewed` / `- Readiness: go-pending-approval`, and its V-05 naming `status`, `next` and `resume` as control rows that must PASS pre-fix; review's measured `resume {seqgap: 5}` | F-10's CONTENTION ANALYSIS HAD DECAYED: the plan it named has executed, and a different pending plan now changes the adjacent code this plan declares. The conclusion (no real contention) survives but rests on different facts, and an executor inheriting the stale analysis would not know a neighbour exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 rewritten to record the supersession and the re-measured neighbour set. Added F-15 stating the one real interaction, that it is benign in BOTH landing orders (because `resume` already returns 5 on a broken chain), and naming the two things an executor must not do. The gate carries the same note. |
| PR-807 | LOW | IN-SCOPE | G. Plan executability (right-sizing) | `aw ipd lint` advisories: `E-02: action text may bundle multiple concerns (3 clauses: 'or an empty ledger', 'which no separate CLI invoca...', 'adding it would oblige a COD...')` and `E-03: explicit multi-part enumeration with multiple independent actions or deliverables` | TWO DENSITY ADVISORIES WENT UNANSWERED. A flagged sizing signal is an actionable finding to investigate by decomposition, never noise; leaving it unaddressed means a later reader cannot tell whether it was judged or overlooked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Applied the four splitting diagnostics to both items and recorded the conclusion in `## Scope check`: NEITHER warrants a split, E-02 because its three clauses are one tuple plus the two justifications that explain it, E-03 because its four assertions share fixtures and one falsification event so splitting would duplicate the recipe and the pre-change red run. The advisory's correctness about E-03 being the densest item is acknowledged rather than dismissed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03's purity assertion is prohibited. Should review delete the assertion, replace it, or mark the plan REPLAN? | REPLACE IT with a behavioral bytes-and-count check, measured working before writing it into the plan. | (a) Delete the assertion - rejected: purity is the plan's central CLAIM (a verb declared `read` must not write), so dropping its guard would leave the one property the reclassification asserts unpinned, which is worse than the prohibited version. (b) REPLAN - rejected: the defect is one assertion inside one E-item, and the replacement is a few lines; bounded edits fix it, which is exactly the Fix Bar's test. (c) Keep the AST walk and note the tension - rejected outright: `AGENTS.md` and P16 are hard prohibitions, not preferences, and a review that licenses one is worse than the plan that proposed it. | `AGENTS.md` clause (1) and P16's prohibition list read verbatim; review's own probe measuring the replacement (bytes, sha256, record count, mtime, directory listing all unchanged at exit 0). | yes |
| D-2 | Two Deferred rows assert an obligation through `Carrier-Declined`. Should review file the items itself, or leave that to the executor? | FILE BOTH NOW, from review's own measurements, and convert the rows to real `- Carrier:` handoffs. | (a) Leave it to the executor - rejected: `check.ipd-uncarried-obligation` refuses a `- Carrier:` naming an id6 that does not resolve, so a plan cannot honestly defer to an item that does not exist yet; the executor would face the same wall and would be improvising a filing decision mid-execution. (b) Rewrite the rows as honest declines instead - rejected: both rows state real outstanding defects, and one of them (the unreachable fail-closed guarantee) is a genuine bug whose docstring advertises a protection it cannot deliver; declining it would schedule the loss of a measured finding. (c) Raise them as `- Blocking: yes` questions - rejected: neither blocks THIS plan, whose correctness is independent of both answers. | `ipd_schema.CARRIER_DECLINED_FIELD`'s docstring defining the field as a decision NOT to carry; `check_engine`'s `check.ipd-uncarried-obligation` at `error` severity; the absence of any matching backlog item before filing; `aw check plans` confirming both new ids resolve after. | yes |
| D-3 | `tzqvjn` auto-gated to `Blocks-Release: next` on filing. Should review file it as `chore` instead to avoid gating a release on an obscure path? | NO. Leave it `bug` and let the gate stand. | (a) File it `chore` to dodge the gate - rejected as misfiling to manage a gate, which is exactly what the repository's gating-work-kind policy warns against; the defect is that a documented fail-closed guarantee cannot fire across the only boundary it exists for, which is a correctness defect and not tidiness. (b) File `bug` and clear the gate with `--blocks-release -` - rejected: review has no mandate to decide a release gate is unwarranted, and the policy says a live bug gates by default. The human may clear it with one command if they judge otherwise. | `AGENTS.md` "Every live bug gates the next release" and its ruling that classification must not be adjusted to attract or avoid attention; `run_recovery.resume`'s docstring promising the refusal; review's measurement that it cannot fire. | yes |
| D-4 | The plan carries no `- Blocks-Release:` and explains why. Does PR-802's filing of a gated `bug` change that? | NO. This plan stays ungated. | (a) Add `Blocks-Release: next` to this plan because it spawned a gated item - rejected: the gate belongs to the DEFECT (`tzqvjn`, the unreachable path), not to this declaration correction, which fixes a different thing and whose own work-kind is honestly `chore`; the inheritance rule carries a gate from a graduating item to its carrier, and `cldbus` carries none. (b) Upgrade this plan to `bug` - rejected: a declaration whose value no live test reads produces no user-perceptible impact, which is the repository's own test for `bug`. | `AGENTS.md`'s gate-inheritance rule and its user-perceptible-impact test for `bug`; backlog `cldbus` carrying `- Work-Kind: chore` and no gate; the plan's own reasoned paragraph, which review checked and upheld. | yes |
| D-5 | Two `IPD-Z602` density advisories fired. Split E-02 or E-03? | NEITHER, and record the reasoning rather than the conclusion alone. | (a) Split E-03's four assertions into separate items - rejected: they share the fixture set F-12 records and two of them exist to fail on the SAME pre-change tree, so fragments would duplicate both the recipe and the red run, and each fragment's `V-*` would demand the same evidence. (b) Split E-02's comment from its value - rejected: it would land a change in one item and its justification in another, which is the shape that produces unexplained code. (c) Dismiss the advisories because the count-based size lint passed - rejected explicitly: the workflow says a sizing signal is an actionable finding to investigate, never a thing to dismiss on a passing lint. | the four splitting diagnostics in the `/plan-review` rubric; the advisory messages read in full; the fixture-sharing and shared-falsification structure of E-03's four assertions. | yes |
| D-6 | F-10's neighbour analysis decayed. Should review re-verify the no-contention conclusion or just flag the staleness? | RE-VERIFY IT, and record the new neighbour with the measurement that makes it benign. | (a) Flag the staleness only - rejected: the conclusion an executor relies on ("no pending plan contends") would then rest on an unverified claim about a plan nobody had read. (b) Declare a cross-plan ordering dependency - rejected on measurement: `fuuw94` excludes `command_surface.py` from its scope paths and `resume` already returns 5 on a broken chain, so `(0, 2, 5, 7)` is correct in either order; asserting a dependency that does not exist would cost a scheduling decision for nothing. | `fuuw94`'s `- Scope-Paths:` and V-05 control rows read in full; review's measured sibling matrix showing `resume {seqgap: 5}` already; `9vglxd` resolving under `executed/`. | yes |
