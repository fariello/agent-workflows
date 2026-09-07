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
