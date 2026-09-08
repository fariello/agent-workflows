# Review: probe every queued orchestrator for uncovered work before the run starts (child m7gvuz, Set orchprobe)

- Subject-Id: m7gvuz
- Subject-Type: ipd
- Reviewed-At: 2026-09-07
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `4fdc691b`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions with zero
findings.

DISCLOSURE: the same agent identity authored this Set earlier in the session, so this is a self-review.
Every load-bearing claim was RE-MEASURED rather than recalled: function signatures were printed with
`inspect.signature`, payload sizes were counted off the real files, and the AGENTS.md test guard was read
in source.

METHOD. This child proposes to call a model from inside the runner, so the first question asked was not
"is the prompt good" but "can the runner make this call where the plan says to make it". Printing the two
host helpers' signatures answered that, and it answered it no. Cost was then measured rather than
characterized, since "cheap by caching" is a claim about token volume.

WHAT THE PLAN GOT RIGHT, and it is the hard part of the design. The insight that this cannot be a pattern
match is correct and well argued: the dangerous case is prose, and a syntactic rule catches only the tidy
mistake. Biasing the prompt toward suspicion and failing closed on an unparsable reply is the right
asymmetry, because a false clear launders a bad state with apparent authority while a false alarm costs
one prompt. Holding the prompt as data with the sentinels as shared constants so parser and prompt cannot
drift is the correct shape. The E-05 remedy-wording item is the best item in the Set: it correctly treats
"say what to do, not merely what is forbidden" as a deliverable rather than a nicety, on this
repository's own measured evidence that a prohibition-only message gets complied with by deletion.

THE BLOCKER IS THAT THE PROBE COULD NOT BE BUILT WHERE THE PLAN PUT IT. E-04 required the gate be sited
"BEFORE any agent turn or lane worktree is created", with the expected outcome that "a refusal creates no
run directory lease, no worktree, and no session". Measured, there is no way to satisfy that and still
call a model: the only two invocation helpers are `run_opencode(state, run_dir, item, plan_path,
prompt_path, attempt_no, ...)` and `run_agy_turn(state, run_dir, item, prompt_path, attempt_no, ...)`,
both of which REQUIRE a `run_dir` and a queue `item`, and both write their transcript to
`run_dir/sessions/<position:02d>-<id6>-attempt-N.jsonl` (`oc_runipd.attempt_log_path:4897-4905`) keyed on
`item['position']`, which exists only once the queue is frozen. There is no one-shot "ask a model a
question" helper anywhere in the package. So an executor following E-04 literally would have had to
either invent a second model-invocation path or discover mid-implementation that the instruction was
impossible. The parent's completion criterion 3 pushes the same way from the other side: it requires the
refusal be readable in `aw runs`, which reads durable run state, and a pre-directory refusal creates
none (the existing pre-queue gates raise at `oc_runipd.py:2791` and `:2871`, before `run_dir.mkdir` at
`:2880`). Resolved as D-1 by redefining "costs nothing" as what actually matters: no agent turn, no lane
worktree, no session. That is the same resolution the parent review reached independently, which is
reassuring rather than coincidental.

THE COST WAS NEVER SIZED, AND THE PLAN NEVER SAYS WHAT IS SENT. "A short prompt per queued orchestrator"
describes the instruction; it says nothing about the payload, and the payload is the cost. Measured, the
pending orchestrators run from 30,106 to 65,705 characters, roughly 7,500 to 16,400 tokens each and about
58,000 tokens for all six. So an unbounded probe would ship a 16k-token file to answer a yes/no question,
and a Set whose selling point is "cheap by caching" would be paying that on every cache miss. New E-03
bounds the input to the E-item action text plus the child table, and requires it be the SAME two inputs
child 02's digest keys on. That second half matters more than the cost: if the probe reasons over
something the digest does not cover, an edit to that thing serves a stale verdict, which is the one way
this cache can be actively wrong rather than merely wasteful.

E-06 WOULD HAVE TRIPPED A TEST THE PLAN DID NOT KNOW EXISTED. It regenerates AGENTS.md prose about the
gate, and the natural home is the `### The runners own ordering, isolation, and orchestrators` section.
That exact section is guarded unusually:
`tests/test_orchestrator_retirement.py::test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module`
slices from that heading to the next `### ` and asserts every claim fragment in a `mapping` dict is
present in the text AND backed by a named test class in the same module. New prose there therefore needs
new mapping entries and real tests behind them. The plan declared neither the test file nor the
constraint, so the executor would have regenerated the block and hit a failure whose cause is a dict it
had never read. Worth noting the guard is a good one: it exists because that same paragraph once asserted
a mechanism that had never worked.

THE SPEC OBLIGATION NAMED NO FILE. E-06 said to "amend the spec that governs the run gates", which
resolves to nothing, and the plan's `Scope-Paths` declared no `.spec.md` at all while its own spec-sync
section required the file be declared so the pre-run announcement names it (the parent's CID-6 checks
exactly that). Resolved to `77tr3o`, and the reason is not arbitrary: R-5 is the requirement whose
resolution CREATED the omission this gate compensates for. The maintainer chose shape (b) there, a
runner-owned rollup that skips the E/V checkpoint, on the premise that an orchestrator's items are
performed by nobody. This gate is the control that makes that premise checked rather than assumed, so
leaving R-5 unamended leaves an approved spec asserting a bare premise the system no longer relies on.

THE QUESTION I DID NOT RESOLVE, and it is the one that decides whether this child is a good idea. This
would be the FIRST non-deterministic gate in `aw <host> run`. Every existing gate is deterministic: the
dependency preflight, draft admission, mixed-type, capability, and the retirement predicate. And it fails
closed by design, which is correct for safety and also means a model that is unavailable, rate-limited,
timed out or merely chatty BLOCKS a run that is otherwise fine, since E-02 makes any unparsable reply
`unknown` and `unknown` blocks. That trade is real in both directions and it is a pricing decision, so it
is OQ-02 with `Blocking: yes` and three costed options; my recommendation is to split "could not ask"
from "asked and got nonsense" and to measure the false-positive rate before the gate becomes fatal.

ON SIZE, since this went from six E-items to nine. E-03 (bound the payload), E-07 (the spec amendment
split out of the doc item) and E-09 (prove both hosts actually gate) are each a distinct concern with its
own evidence, and the last one exists because this Set's own predecessor shipped an agy host that DECIDED
an orchestrator action while having no dispatch branch that read it (`pgq326`'s review), so "both hosts
share the decider" demonstrably does not imply "both hosts act".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. correctness; C. architecture; G. executability | `inspect.signature` of `oc_runipd.run_opencode:5262` and `agy_runipd.run_agy_turn:2765` (both require `run_dir` and `item`); `oc_runipd.attempt_log_path:4897-4905`; `oc_runipd.py:2791`, `:2871`, `:2880` | **THE PROBE CANNOT BE BUILT WHERE E-04 PUTS IT.** E-04 required siting before any run directory exists ("a refusal creates no run directory lease"), but both model-invocation helpers REQUIRE a `run_dir` and a queue `item`, and both log to `run_dir/sessions/<position:02d>-<id6>-attempt-N.jsonl` keyed on `item['position']`, which exists only after the queue is frozen. No one-shot model helper exists in the package. Independently, the parent's criterion 3 requires the refusal be readable in `aw runs` (durable state), which a pre-directory refusal never creates, since the existing pre-queue gates raise before `mkdir`. An executor would have had to invent a second invocation path or discover the impossibility mid-build | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-05 (renumbered) now sites the gate AFTER the run directory and BEFORE any agent turn, lane worktree or session, with the measured reason inline and "costs nothing" redefined accordingly. V-05 forbids asserting "no run directory" and instead requires an empty `sessions/`, a zero attempt count, and `aw runs` read after exit. New F-6 and a conventions bullet stating that a model call needs a run directory |
| PR-002 | HIGH | IN-SCOPE | C. operability; reliability | `runner_shared.enforce_dependency_preflight`, `enforce_draft_admission_gate`, `enforce_mixed_type_gate`, the capability gate, `decide_orchestrator_dispatch` (all deterministic); plan E-02 making any unparsable reply `unknown`, and `unknown` blocking | **THIS WOULD BE THE FIRST NON-DETERMINISTIC GATE IN `aw <host> run`, AND IT FAILS CLOSED, SO A MODEL OUTAGE BLOCKS RUNS.** Every gate the runner has today decides from repository state. This one decides from a language model, and by design an empty, chatty, truncated or unavailable reply is `unknown`, which blocks exactly as a positive finding does. That is the right safety bias AND a new run-availability failure mode, and the plan never states the trade or asks about it | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | OPEN | Escalated as OQ-02 with `- Blocking: yes` and `- Finding: PR-002`, owner maintainer, three costed options: (a) fail closed as designed, (b) split "could not ask" from "asked and got nonsense" and block only the second, (c) ship advisory-first and gate once the false-positive rate is measured. Recommendation (b) plus (c)'s measurement discipline. The gate section states execution is blocked on it. NOT FIXED because pricing a safety risk against a run-availability risk is the maintainer's call |
| PR-003 | HIGH | UNDER-SCOPE | C. operability (cost); G. executability | `len()` over each pending `Kind: orchestrator` file: 30,106 to 65,705 chars (~7,500 to ~16,400 tokens each; ~58,000 for all six) | **THE COST WAS NEVER SIZED AND THE PAYLOAD NEVER SPECIFIED.** "A short prompt per queued orchestrator" describes the instruction, not what is sent. Unbounded, the probe ships a 16k-token file to answer a yes/no question, on every cache miss, which undercuts the Set's central "cheap by caching" claim. Worse than the cost: if the probe reads content child 02's digest does not cover, an edit to that content serves a STALE verdict, which is the one way the cache is actively wrong rather than merely useless | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-03 bounds the input to the E-item action text plus the child table and REQUIRES it be the same two inputs child 02's digest keys on, with the divergence risk stated. V-03 requires the excerpt pasted beside the digest inputs plus per-orchestrator measured sizes. New F-7; Scope updated to say "bounded excerpt rather than the whole file" |
| PR-004 | HIGH | UNDER-SCOPE | D. anti-regression; E. testing | `tests/test_orchestrator_retirement.py`, `test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module` (its `paragraph()` slice and `mapping` assertions) | **E-06 WOULD HAVE TRIPPED AN EXISTING TEST THE PLAN NEVER MENTIONS.** That test slices exactly the `### The runners own ordering, isolation, and orchestrators` section this item edits and requires every claim fragment in its `mapping` dict to be present AND backed by a named test class in the same module. The plan declared neither the test file in `Scope-Paths` nor the constraint, so the executor would regenerate AGENTS.md and hit a failure whose cause is a dict it had not read. The same module holds `TheRejectedShapeWasNotTaken`, which the parent's CID-1 requires to pass UNMODIFIED | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `tests/test_orchestrator_retirement.py` added to `Scope-Paths`; E-08 states the guard, requires mapping entries plus real tests for every new claim, and flags the neighbouring "Do NOT raise" list (`AGENTS.md:44`) as needing an update if a probe refusal becomes reportable. V-08 requires the mapping test AND `TheRejectedShapeWasNotTaken` pasted passing. Scope check forbids refactoring the module or weakening that guard. New F-8 |
| PR-005 | HIGH | IN-SCOPE | C. operability; stakeholder impact | `- Status: approved` on `5e4sb6`, `h0zljh`, `rh5tt6`, `3m0urk`; parent `yeh7gc` CID-2 classification | **THIS CHILD IS WHAT MAKES THE PARENT'S BLAST RADIUS LIVE, AND IT DID NOT SAY SO.** Four orchestrators are `approved` and runnable today and each carries parent-only work, so the day this lands every run queueing one refuses or prompts, with "author a new child" as the remedy. The parent raised it; this child, which actually ships the gate, carried no mention of it at all | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | OPEN | Escalated as OQ-03 with `- Blocking: yes` and `- Finding: PR-005`, owner maintainer, explicitly inheriting the parent's OQ-02 and its three costed options, with a note that resolving it there resolves this. Added to Deferred as not-solved-here. NOT FIXED because it is the same maintainer decision |
| PR-006 | MEDIUM | IN-SCOPE | Spec synchronization; G. executability | pre-revision E-06 and `Scope-Paths` (no `.spec.md`); spec `77tr3o` R-5 (`- Status: approved`); parent CID-6 | **THE SPEC OBLIGATION NAMED NO FILE AND DECLARED NONE.** E-06 said to "amend the spec that governs the run gates", which resolves to nothing, and required the file appear in `Scope-Paths` while `Scope-Paths` listed no spec, so the item contradicted itself and the parent's CID-6 (which checks the pre-run announcement names it) could not pass | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Split the spec amendment into its own E-07 naming `77tr3o` and stating WHY (its R-5 resolution created the omission this gate compensates for, so an unamended R-5 asserts a premise the system no longer relies on); added the spec file to `Scope-Paths`; spec-sync section rewritten with the reasoning and `25kzda` 2.5/2.5a named as a possible second amendment to decide-and-record. V-07 requires the diff and the announcement |
| PR-007 | MEDIUM | UNDER-SCOPE | D. anti-regression; E. testing | `pgq326` review record (agy DECIDED `orchestrate` with no dispatch branch reading it); AST count 47 | **"BOTH HOSTS SHARE THE SYMBOL" DOES NOT MEAN "BOTH HOSTS GATE", AND THIS SET HAS ALREADY BEEN BITTEN BY EXACTLY THAT.** The plan had no item proving agy actually refuses; its conventions mention object identity only. `pgq326`'s review found the predecessor Set shipping a shared action decider while `aw agy run` had no branch reading it, so the Set could have passed an identity assertion while agy still spent an agent turn on an orchestrator | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-09 requires object identity, an unchanged oc-to-agy import count (47, measured), AND a demonstration that `aw agy run` refuses on the same fixture `aw oc run` refuses on. V-09 requires all three, naming the `pgq326` lesson |
| PR-008 | MEDIUM | IN-SCOPE | Honest documentation; G. ownership | grepped `runner_profiles` for `role` (zero hits); `oc_runipd.resolve_launch_profile:2660`; `kgpptv` `- Status: approved`, not executed | **OQ-01 CLAIMED MACHINERY THAT DOES NOT EXIST YET.** It said "`kgpptv` gives the verifier turn its own resolved profile ... so the profile machinery exists; the executor should reuse it". Measured: `runner_profiles` has NO `role` concept, `resolve_launch_profile` resolves ONE launch identity for the whole run, and `kgpptv` is approved but UNEXECUTED. An executor told to reuse a per-role resolver would find nothing and would most likely build role routing inside this child | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 narrowed to say plainly that no per-role machinery exists, that the executor must use the run's already-resolved profile and RECORD which model answered, and must NOT add role routing here; building it is listed in Deferred as `kgpptv`'s. New F-10 and a conventions bullet |
| PR-009 | LOW | UNDER-SCOPE | C. operability; logging/audit | pre-revision E-04 ("Record the override in run state when used") | **THE OVERRIDE RECORDED THE FACT AND NOT THE JUDGEMENT.** A bare boolean tells a later reader someone clicked past the gate and nothing about whether they should have. That is the same gap the remedy field closes on the refusal side, and this Set argues that case explicitly, so leaving the override unexplained is inconsistent with its own reasoning | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires a justification string supplied by the maintainer and written into run state beside the override; V-05 requires the recorded justification pasted. New F-9 |
| PR-010 | LOW | IN-SCOPE | Evidence accuracy; E. testing | re-counted corpus (46 of 47 `Kind: orchestrator`; 84 of the 130 `-00-` files are pre-`Kind` with zero E-items); measured suite baseline | Two accuracy gaps: F-2 repeated the diluted "46 of 130" denominator (which understates the incidence by roughly 3x and points the reader away from false positives being the dominant cost), and the plan carried no measured suite baseline at all despite editing a module whose one live failure is a live-repo status coupling that could be misread as caused here | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-2 rewritten with both denominators and the consequence for sizing; E-08 additionally corrects the same figure in the generated AGENTS.md text and V-08 requires it pasted; a measured baseline bullet added (`1 failed, 5632 passed, 3 skipped, 2 xfailed` at HEAD `4fdc691b`) naming the failure and warning against both misreadings. Required tests also now demand a FALSE-POSITIVE fixture (an orchestration-only orchestrator must pass) and a stub that raises if a real model call is attempted |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Where may the gate be sited, given E-04 demands "before any run directory" but a model call requires one? | AFTER the run directory exists, BEFORE any agent turn, lane worktree or session; redefine "costs nothing" as those three | Keep the pre-directory siting, rejected as measurably impossible (both helpers require `run_dir` and `item`, and log under `run_dir/sessions/` keyed on `item['position']`) and as incompatible with the parent's criterion 3, which needs durable state for `aw runs`. Build a new one-shot invocation path outside the run directory, rejected as a second model-invocation surface for one gate, which is the re-fork pattern this repo keeps paying for | `inspect.signature` of both helpers; `oc_runipd.attempt_log_path:4897-4905`; `oc_runipd.py:2791`/`:2871` raising before `:2880` mkdir; parent `yeh7gc` criterion 3 | yes |
| D-2 | What does the probe actually send? | The E-item action text plus the child table: exactly child 02's digest inputs | Send the whole orchestrator file, rejected on measurement (7.5k to 16.4k tokens each) and because it makes "cheap by caching" hollow. Send some other curated excerpt, rejected because any input the digest does not cover can change without invalidating the cache, which would serve a stale verdict; tying the two together removes that failure mode by construction | measured file sizes; child `8tgg6g` E-02's digest inputs | yes |
| D-3 | Which spec does E-07 amend, given "the spec that governs the run gates" resolves to nothing? | `77tr3o`, because its R-5 resolution created the omission this gate compensates for | `25kzda` 2.5/2.5a alone, rejected because although it houses the sibling admission gates, it is not where the skipped-checkpoint premise is recorded; leaving it unnamed for the executor, rejected because an unresolvable instruction is how a spec obligation evaporates and the parent's CID-6 would then be uncheckable. `25kzda` is kept as a possible SECOND amendment to decide and record | `77tr3o` R-5 text and `- Status: approved`; `ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']` citing R-5; parent CID-6 | yes |
| D-4 | Add an item proving agy actually GATES, when the conventions already require object identity? | YES, as E-09, requiring a demonstrated agy refusal | Rely on the object-identity assertion, rejected on this Set's own history: `pgq326`'s review measured agy DECIDING `orchestrate` while having no dispatch branch that read it, so identity passed while agy still spent an agent turn. A shared decider is necessary and not sufficient | `pgq326` review record; measured oc-to-agy import count 47 | yes |
| D-5 | Escalate the non-deterministic-gate question, or accept fail-closed as designed? | ESCALATE as OQ-02 `Blocking: yes`, recommending the availability split plus measuring the false-positive rate first | Accept (a) fail-closed silently, rejected because it adds a run-availability failure mode the plan never disclosed and this would be the runner's first model-decided gate. Decide (b) myself, rejected because loosening a fail-closed safety gate is precisely the kind of change an agent must not authorize on its own | the five existing gates all being deterministic; plan E-02 making any unparsable reply `unknown` and `unknown` blocking; ESCALATED in-plan as OQ-02 with `- Finding: PR-002`, and maintainer told 2026-09-07 in this review's final report | no |
| D-6 | Restate the parent's blast-radius question here, or leave it to the parent? | RESTATE as OQ-03 `Blocking: yes`, inheriting the parent's options | Leave it in the parent only, rejected because THIS child is the artifact that makes the four refusals live, and its own pre-execution gate is the one that should stop until the question is answered; a blocking question on the parent does not gate the child's execution | `- Status: approved` on the four; parent `yeh7gc` OQ-02; ESCALATED in-plan with `- Finding: PR-005`, and maintainer told in the final report | no |

## Round 2

Reviewed at HEAD `130d9cc7`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`). Verdict: APPROVE WITH REVISIONS APPLIED; readiness
GO - PENDING HUMAN APPROVAL. The verdict token is stated explicitly because
`plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a
negative scan when none is present.

DISCLOSURE: same agent identity as round 1, so this is a self-review. Every load-bearing claim was
RE-EXECUTED rather than re-read: signatures printed with `inspect.signature`, payload sizes counted off
the real files, the corpus re-parsed, the readiness predicates CALLED, and the suite run bare.

ROUND 1's TECHNICAL WORK HOLDS IN SUBSTANCE, AND ALL OF ITS COORDINATES ARE NOW WRONG. Both
model-invocation helpers still require `run_dir` and a queue `item`, `attempt_log_path` still keys on
`item['position']`, and the three pre-queue gates still raise before the run directory is created, so
D-1's siting stands. But `run_opencode` is at `:5304` (was `:5262`), `run_agy_turn` at `:2768` (was
`:2765`), `attempt_log_path` at `:4939` (was `:4897-4905`), the gates at `:2833`/`:2876`/`:2913` before
`mkdir` at `:2927` (was `:2791`/`:2871`/`:2880`), and `resolve_launch_profile` at `:2702` (was `:2660`).
Every citation in the plan was corrected and E-05 now says to locate the seam BY SYMBOL, since these
numbers have moved on both measurements. One thing round 1 missed entirely: `oc_runipd.py:2770-2773`
documents the pre-directory ordering as DELIBERATE ("so no ordering change can later slip a durable
write ... ahead of a refusal"), so this probe is the first gate that cannot honor a stated invariant.
That is a priced exception and now says so in the plan and in the comment the executor must leave.

THE FINDING THAT MATTERED MOST IS THAT A MAINTAINER RULING HAD NO DELIVERABLE (PR-012, F-12). On
2026-09-07 the maintainer resolved OQ-02 by splitting COULD-NOT-ASK from ASKED-AND-GOT-NONSENSE, retrying
the former to a budget and then PROCEEDING with a loud warning so a model outage cannot halt a run. No
E-item implemented any part of it. Worse, E-02 said the opposite in as many words, classifying "an empty
reply, a truncated turn" as `unknown` and blocking on it, which is exactly the fail-closed-on-outage
behavior the ruling overturned. An executor following this plan would have shipped the negation of the
decision while the plan's own question section recorded it as resolved. This is the sharpest failure mode
of a resolve-and-record workflow: the decision is durable, the obligation is not. Fixed by E-10 (its own
task group) and by making E-02 four-state, since a tri-state cannot express the split.

AND THAT RULING'S DEFAULT CONTRADICTS THE SHIPPED ONE (PR-013, F-13). It says "default 3, configurable by
flag or config variable". Measured: `--retry-budget` already exists on both hosts via the shared flag
table (`runner_shared.py:1648`), already resolves before the run directory exists (`oc_runipd.py:2815`),
its 0..10 bound has a SINGLE definition (`run_recovery.validate_retry_budget`), and its default
`DEFAULT_RETRY_LIMIT` is 2, not 3. So the executor faced an undeclared choice between adding a second
retry knob (the re-fork E-09 exists to prevent) and silently redefining an existing flag. E-10 now
requires the choice be made and recorded, preferring reuse, and forbids re-implementing the bound.

THE HAZARD BECAME REAL WHILE THE PLAN WAITED (PR-014, F-14), and this is the substantive news of round 2.
`rh5tt6` was one of the four orchestrators OQ-03 says to clear FIRST. It was not cleared. On 2026-09-08
at 00:38 `aw oc run` RETIRED it to `executed/` (commit `8b4e1570`), and the commit message states plainly
"Its own `E-*`/`V-*` items were NOT performed". Its E-02 (the repo-wide suite, leak sanitization, and an
end-to-end install proof the plan itself calls "the part no child owns") still reads
`Execution state: pending`; its V-02 still reads `Observed evidence:` blank, `Result: pending`. So a
parent-only deliverable was marked complete having been neither performed nor verified, which is the
precise failure this Set exists to prevent, occurring once more before the gate could land. Two
consequences carried into the plan: OQ-03's list is now THREE (`5e4sb6`, `h0zljh`, `3m0urk`), and "clear
first" is racing an active runner rather than working against a static corpus. Note the honest limit: the
runner behaved exactly as `77tr3o` R-5 specifies, so this is a specification gap made visible, not a bug.

THE GATE PARAGRAPH ASSERTED A BLOCKER THAT DOES NOT EXIST (PR-011, F-11), the same defect round 2 fixed on
both siblings, which makes it a class rather than an accident. It said execution "IS BLOCKED ON TWO
QUESTIONS ... OQ-02 (`Blocking: yes`) ... OQ-03 (`Blocking: yes`)". Both have carried `- Blocking: no`
and `- Status: resolved` since the maintainer's rulings. Measured: `has_unresolved_blocking_question`
returns False and `_blocking_question_ids` returns empty, so no gate reads that sentence and a maintainer
reading it would have waited for an answer they had already given. `approval_refusals` names the three
things that DO refuse: the stale `- Readiness: no-go` (which this round replaces) and round 1's PR-002 and
PR-005 recorded high/open (which this round dispositions FIXED).

THE CORPUS FIGURE IS UNSTABLE IN ONE DIRECTION AND SHOULD STOP BEING A FRACTION (PR-015). Round 1 said 46
of 47; the parent measured 48 of 48 the next day; at round 2 it is 50 of 50, i.e. 100 percent, against a
filename-`-00-` population of 134 of which 84 carry no `Kind` and no E-items. The pending orchestrators
grew from six to EIGHT and the total probe payload from ~58k to ~72k tokens in one day. Every figure in
the plan is now marked re-measure-at-execution, and E-08 is told to phrase the AGENTS.md denominator so
it does not rot (the generated text at `AGENTS.md:80`, from `engine.py:1349`, still says "46 of 130").

THE BASELINE'S FAILURE SET GREW OVERNIGHT (PR-016), which is this plan's own node-ids-not-totals rule
demonstrated against it. Round 1: `1 failed, 5632 passed`. Round 2 bare at `130d9cc7`:
`2 failed, 5655 passed, 3 skipped, 2 xfailed in 62.73s`. The new failure is
`test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`
(on `32ij2j`), joining the known `test_orchestrator_retirement.py::RealRepositorySets` one. BOTH are
tests pinned to the live plan corpus, neither is caused by this Set, and together they are the argument
for the parent's CID-2 rule that this child pin its own tests to FROZEN fixtures. The required-tests
section now says so explicitly, because `rh5tt6` left the pending corpus between rounds and a live-file
fixture here would have broken for that reason alone.

ONE INHERITED CONSISTENCY FIX: E-09 asserted object identity absolutely, while the parent's CID-3 carries
a measured carve-out for host-parameterized text (`DEPENDENCY_BLOCK_RECOVERY_HINT` is deliberately one
constant per runner, `oc_runipd.py:345` / `agy_runipd.py:400`, and a probe remedy naming a `resume`
command is that same shape). Without the carve-out E-09 would have forced a remedy naming the wrong host.

ON SIZE: nine E-items to ten. The single addition is E-10, and it is not scope creep: it implements a
decision the maintainer had already made and that no item covered, which is the definition of
under-scope. Every other round-2 finding corrected an existing item's content rather than adding work.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-002 | HIGH | IN-SCOPE | C. operability; reliability | maintainer ruling recorded in OQ-02 2026-09-07; `- Blocking: no`, `- Status: resolved` | ROUND 1's OPEN FINDING, NOW DISPOSITIONED. Round 1 escalated the "first non-deterministic gate, fails closed, so a model outage blocks a run" trade as a maintainer pricing decision. The maintainer priced it on 2026-09-07: option (b) plus a retry budget. The QUESTION is closed; what was still missing was the CODE, which is PR-012 below | C:Medium; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Closed by the maintainer's ruling plus new E-10, which implements it. No longer open, so it no longer gates |
| PR-005 | HIGH | IN-SCOPE | C. operability; stakeholder impact | maintainer ruling recorded in OQ-03 2026-09-07 (with parent `yeh7gc` OQ-02); `- Blocking: no`, `- Status: resolved` | ROUND 1's OTHER OPEN FINDING, NOW DISPOSITIONED. The maintainer ruled CLEAR FIRST on 2026-09-07, rejecting an allowlist because an operator meeting the same prompt four times learns to reach for the override. The question is closed; PR-014 records that reality moved under it | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Closed by the ruling; the surviving sequencing precondition is now a hard precondition in the gate and carries its evidence in V-05, since no code can express it |
| PR-011 | BLOCKER | IN-SCOPE | G. executability; honest documentation | `plan_readiness.has_unresolved_blocking_question` = False; `_blocking_question_ids` = empty; `approval_refusals` = 3 items, none a blocking question; OQ-02/OQ-03 own `- Blocking: no` lines | **THE GATE ASSERTED A BLOCKER THAT DOES NOT EXIST.** It said execution "IS BLOCKED ON TWO QUESTIONS ... The pre-execution checkpoint refuses while either is open", while both questions have been resolved and non-blocking since 2026-09-07. Measured, no gate reads that sentence. A maintainer reading it would have waited for an answer they already gave. Third instance in this Set (siblings `yeh7gc` PR-011, `r2i1b1` PR-010), so it is a class | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | Gate paragraph rewritten: the false claim is retracted with the predicate output that refutes it, the three REAL refusals are named from `approval_refusals`, and the surviving sequencing precondition is stated as a precondition with its evidence moved into V-05. New F-11 |
| PR-012 | BLOCKER | UNDER-SCOPE | A. correctness; C. operability; G. executability | OQ-02's resolution text vs every E-item's action text; E-02's own wording ("an empty reply, a truncated turn" -> `unknown` -> blocks) | **THE MAINTAINER'S RULING HAD NO DELIVERABLE, SO THE PLAN WOULD HAVE SHIPPED ITS NEGATION.** The 2026-09-07 ruling requires splitting COULD-NOT-ASK from ASKED-AND-GOT-NONSENSE, retrying the former to a budget, then PROCEEDING with a loud warning so a model outage cannot halt a run. NO E-item implemented it, and E-02 explicitly did the opposite. A resolved question with no item is a decision that does not ship, and here the plan recorded the decision while specifying its inverse | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | New E-10 in its own task group owns the could-not-ask path (retry, then warn-and-proceed, with the warned-past HOLE durable in `aw runs`); E-02 rewritten to return FOUR states and to classify only a DELIVERED answer as `unknown`; V-02 and new V-10 require both paths demonstrated plus a mutation check. Scope and ordered-changes updated. New F-12 |
| PR-013 | HIGH | IN-SCOPE | C. architecture (no re-fork); G. executability | `runner_shared.py:1648`; `resolve_retry_budget:1745` called at `oc_runipd.py:2815`; `run_recovery.DEFAULT_RETRY_LIMIT` printed = 2; `validate_retry_budget:136` | **THE RULING'S "DEFAULT 3" CONTRADICTS THE SHIPPED DEFAULT OF 2, AND A RETRY FLAG ALREADY EXISTS.** `--retry-budget` is registered on both hosts, resolved before the run directory exists, and its 0..10 bound has a single definition. So the executor faced an undeclared choice between a second retry knob (the re-fork E-09 exists to prevent) and silently redefining a shipped flag's meaning | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-10 states the three options (reuse and accept 2, reuse with a probe default of 3, or a separate budget), requires the choice be RECORDED, prefers reuse, and forbids re-implementing the bound. V-10 requires the measured default pasted. New F-13 |
| PR-014 | HIGH | IN-SCOPE | D. anti-regression; stakeholder impact | `.aw/records/plans/executed/20260901-wslayout-00-rh5tt6-...ipd.md` E-02 `Execution state: pending`, V-02 blank; `git show 8b4e1570` | **THE HAZARD OCCURRED AGAIN WHILE THIS PLAN SAT IN `to-review`, TO ONE OF THE VERY PLANS THE REMEDY NAMED.** `rh5tt6` was one of OQ-03's four to clear first. Instead `aw oc run` retired it to `executed/` on 2026-09-08, with a commit message stating "Its own `E-*`/`V-*` items were NOT performed", while its E-02 (repo-wide suite, leak sanitization, end-to-end install proof it calls "the part no child owns") reads pending and its V-02 is blank. The plan described this failure as a risk; it is now a measured instance, and the "clear first" plan is racing a live runner | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Concern, OQ-03 and the gate all record the instance with its commit; the list narrows to three (`5e4sb6`, `h0zljh`, `3m0urk`) with an instruction to re-derive by measurement; V-05 now carries the precondition's evidence and FAILS on early execution; the scope check puts `rh5tt6`'s unperformed E-02 explicitly OUT (a plan in `executed/` must not be edited) and hands it to the maintainer. New F-14 |
| PR-015 | MEDIUM | IN-SCOPE | Evidence accuracy | re-parsed corpus at `130d9cc7`: 50 of 50 `Kind: orchestrator`; `-00-` population 134 (84 with no `Kind`, no E-items); pending orchestrators 8, 16,715 to 65,705 chars, ~72,000 tokens total | **EVERY CORPUS FIGURE MOVED, ALWAYS THE SAME WAY, AND THE PLAN STATED THEM AS FACTS.** 46-of-47 (round 1) to 48-of-48 (parent, next day) to 50-of-50 now; pending orchestrators six to eight and ~58k to ~72k tokens in ONE day. A fraction restated in generated AGENTS.md prose will be stale before it is read, and the shipped text still says "46 of 130" (`AGENTS.md:80`, from `engine.py:1349`) | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-2 and E-03 re-measured and marked do-not-trust-at-execution; E-08 now requires the denominator be re-measured AND phrased so it does not rot (e.g. "every plan carrying `- Kind: orchestrator`") rather than shipped as a third stale fraction; V-03 requires execution-time sizes |
| PR-016 | MEDIUM | IN-SCOPE | E. testing; D. anti-regression | `python3 -m pytest` bare at `130d9cc7`: `2 failed, 5655 passed, 3 skipped, 2 xfailed`; new failure `test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` | **THE BASELINE'S FAILURE SET GREW OVERNIGHT, AND THE NEW FAILURE IS THE ANTI-PATTERN THIS CHILD WAS TOLD NOT TO REPEAT.** Round 1 recorded one failure; there are now two, both tests pinned to the live plan corpus. Combined with `rh5tt6` leaving `pending/` between rounds, a test here that read live plan files would break for reasons unrelated to the probe | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Baseline convention rewritten with both node ids, both identified as live-corpus couplings, and marked do-not-trust; required-tests gains a third requirement to pin the rule against FROZEN or synthetic fixtures and never live plan files, deriving the cases by re-classifying at execution and then freezing, plus a fourth covering E-10's availability path |
| PR-017 | LOW | IN-SCOPE | D. anti-regression; internal consistency | parent `yeh7gc` CID-3; `oc_runipd.py:345` and `agy_runipd.py:400` (`DEPENDENCY_BLOCK_RECOVERY_HINT`, two objects by design) | E-09 asserted object identity ABSOLUTELY while the parent's CID-3 carries a measured carve-out: host-parameterized text is legitimately not one object, since each runner's recovery hint names its own host's command, and a probe remedy naming a `resume` invocation is that same shape. Taken literally E-09 would have forced one remedy naming the wrong host | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09 inherits the carve-out (the composing FUNCTION is one shared object taking the host as an argument; identical strings are not required and a wrong-host remedy fails the item), and V-09 requires both rendered remedies pasted. Also told to re-measure the import count in the worktree rather than trusting 47 |
| PR-018 | LOW | IN-SCOPE | Spec synchronization; G. executability | `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` (`- Id: 25kzda`, `- Status: approved`), Sections 2.5 `:235` / 2.5a `:257`; plan `Scope-Paths` | The spec-sync section offered `25kzda` 2.5/2.5a as a possible SECOND amendment by id6 alone. That filename predates the id6-in-filename convention, so the id resolves only by grepping `- Id:`, and an executor deciding to amend it would also have had to notice `Scope-Paths` must gain the path first or the pre-run announcement (the parent's CID-6) would not name it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section now writes out the full path with the reason it is spelled out, cites the two section line numbers, re-verifies `77tr3o` R-5/OQ-1 and its `approved` status, and states that amending `25kzda` requires adding the path to `Scope-Paths` first; the scope check records it as declared-but-conditional. New F-15 |
| PR-019 | LOW | UNDER-SCOPE | C. architecture; internal consistency across the Set | `8tgg6g` round-2 F-10: `ipd_set_plan.parse_child_table` returns `{order: (dep_orders,)}`; Id swap and description rewrite leave it byte-identical | Child 02's key was corrected at ITS round 2 from the parsed order graph to row CELL text, but this child's E-03 still said only "the child table" while REQUIRING that the probe input and the cache key be the same two inputs. If the probe read row text while the key read the order graph, a row edit would serve a stale verdict, which is the exact failure E-03 exists to prevent | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now names ROW CELL TEXT explicitly, cites `8tgg6g`'s corrected E-01 and the measurement behind it; V-03 requires the pasted excerpt be shown against the row-cell inputs rather than the order graph |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-7 | The maintainer's OQ-02 ruling has no E-item and E-02 specifies its opposite. Add the item, or escalate the contradiction? | ADD IT as E-10 and make E-02 four-state. No escalation. | Escalate as a blocking question, rejected because the maintainer already DECIDED this on 2026-09-07 and asking again would be asking them to repeat themselves. Leave it to the executor, rejected because an executor reading E-02's explicit "an empty reply, a truncated turn -> `unknown` -> blocks" would implement exactly that and never see the ruling. | OQ-02's own resolution text; E-02's pre-revision wording; `AGENTS.md` graduation contract ("resolve blocking open questions from repository evidence and cite it, asking the human ONLY when the repo genuinely cannot answer") | yes |
| D-8 | The ruling says default 3; the shipped `--retry-budget` default is 2. Pick one, or make the executor decide? | MAKE THE EXECUTOR DECIDE AND RECORD, with reuse stated as preferred. | Silently set the probe default to 3, rejected because it either redefines a shipped flag's meaning or forks a second retry knob, and neither should happen without being written down. Change `DEFAULT_RETRY_LIMIT` to 3, rejected outright: it governs every retry in the runner and this child's fence does not reach it. | `runner_shared.py:1648`; `resolve_retry_budget` called at `oc_runipd.py:2815`; `DEFAULT_RETRY_LIMIT` printed = 2; `validate_retry_budget` as the single bound | yes |
| D-9 | `rh5tt6` was retired with its E-02 unperformed. Fix it, file it, or record it? | RECORD it in this plan as F-14 and route the decision to the maintainer; put it explicitly OUT of scope. | Edit `rh5tt6`, rejected because `AGENTS.md` forbids adding commits to a plan already in `executed/` and requires a corrective IPD instead. Author that corrective IPD now, rejected because this is a REVIEW (which must not modify anything beyond the plan under review) and because whether the work still matters is the maintainer's call. Say nothing, rejected: it is the strongest available evidence for this Set and it silently changed OQ-03's list. | plan file read in `executed/`; `git show 8b4e1570`; `AGENTS.md` execution contract on executed plans; plan-review's "review plans only" rule | yes |
| D-10 | Round 1's PR-002 and PR-005 are recorded high/open and block the lint gate. Dispositioned how? | FIXED, in this round's table, citing the maintainer's rulings as the resolution. | Leave them OPEN, rejected because their questions are demonstrably resolved (`has_unresolved_blocking_question` = False) and leaving them open would keep refusing the plan for a reason that no longer exists. Escalate them as `Blocking: yes` questions to satisfy `check.review-finding-unescalated`, rejected because that would re-open decisions the maintainer already made, which is the exact time-waste F-11 describes. | OQ-02 and OQ-03 resolution text and their `- Blocking: no` / `- Status: resolved` lines; `approval_refusals` naming both findings; the gate reads only the CURRENT round | yes |
| D-11 | Should this child's tests read live plan files to get the CID-2 classification? | NO. Re-classify at execution to DERIVE the cases, then FREEZE them into the test. | Read `.aw/records/plans/**` at test time, rejected on measurement: both current suite failures are live-corpus couplings, the second appeared overnight, and `rh5tt6` left `pending/` between review rounds, so such a test would break for reasons unrelated to the probe. | `python3 -m pytest` at `130d9cc7` showing both failing node ids; `rh5tt6` now in `executed/`; parent CID-2's frozen-fixture rule | yes |
