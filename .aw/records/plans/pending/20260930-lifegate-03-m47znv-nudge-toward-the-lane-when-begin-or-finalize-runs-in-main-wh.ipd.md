# IPD: Nudge toward the lane when begin or finalize runs in main while a lane for that plan exists

- Date: 2026-09-30
- Kind: child
- Concern: Order 02 removes the location rule entirely, so begin and finalize become legal anywhere: inside a lane, on a feature branch, or in main. That is the correct refusal behavior and it loses one genuinely useful signal. Backlog `dvonrn` D1 records that doing the transition in the lane or branch is PREFERRED, because the plan's move to `executed/` then travels with the code and lands on main in one reviewed merge, and the runner itself already works that way (`runner_shared` finalizes with `finalize_repo = Path(work_dir)` when a lane handle exists, syncing the receipt into the worktree first). After Order 02 nothing tells a human who finalizes in main that a lane for that same plan is sitting right there, so the reviewed-merge shape is lost silently and the lifecycle commit lands on main separately from the code it records. D1 answers this with a NUDGE, never a refusal, and that distinction is the whole design: a refusal here would reintroduce the location rule Order 02 just deleted, in a politer costume.
- Scope: Print ONE advisory line when `begin` or `finalize` runs in the main checkout while a lane or feature branch for that same plan exists, saying that finalizing there keeps main cleaner. It is advisory ONLY: it never changes an exit code, never withholds a transition, never gates anything, and never asks a question. Uses the lane records that already exist (the `.aw/worktrees/` lane directories and their owner records, and the plan's own lane branch name) to answer "does a lane for this plan exist", which is a DIFFERENT and weaker question than Order 01's liveness predicate answers and deliberately does not reuse it. EXCLUDES every refusal and every change to any gate: if this plan changes what any verb accepts or refuses, it is wrong. EXCLUDES the holder check, the token deletion and the override, all of which are Order 02's. EXCLUDES making the preference enforceable in any way.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_lifecycle_lane_nudge.py
- Item-Dependencies: executed:e25iy9
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: dvonrn
- Blocks-Release: next
- Set: lifegate
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: m47znv

## Workflow history

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored while graduating backlog `dvonrn`, whose D1-D8 were settled with the maintainer on 2026-09-26. TWO measurements in this lane shaped the plan beyond what D1 states. FIRST, the nudge's question is NOT the holder predicate's question, and conflating them would be a real defect: Order 01's predicate reports whether a LIVE RUN holds the plan, and by construction returns NOT HELD for a lane whose run has ended, which is precisely the case the nudge exists to mention (an existing lane, no live run, a human about to finalize in main). So this plan reads the lane records directly and must not reuse the predicate; E-02 states that and V-02 pins it with a case where the predicate says NOT HELD and the nudge still fires. SECOND, the output channel is constrained by an existing measured hazard rather than free choice: `ipd_lifecycle`'s CLI handlers emit structured `aw.agent/v1` JSONL or full JSON when `--agent` or `--json` is selected, and `driver_finalize` PARSES finalize's stdout (`parse_finalize_payload`), while `nested_aw_message` exists because a refusal prints on stdout and advisories print on stderr, and it strips the `checkout_pin` advisory notice by prefix so that notice cannot be mistaken for a refusal reason. A new line on stdout would therefore land inside a payload a driver parses. E-03 takes the same shape that notice already takes: stderr, suppressed in machine-readable modes.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Keep the useful half of the deleted location rule, as information, after Order 02 removes its power to
refuse.

WHY THIS IS WORTH A PLAN AT ALL, since it is one printed line. The preference it states is not cosmetic:
when the lifecycle transition happens in the lane, the plan's move to `executed/` is part of the same
change as the code it records, and both reach main in one reviewed merge. When it happens in main while a
lane exists, the plan says `executed` on main before the lane's code arrives, and the record and the work
land separately. The runner already does the preferred thing for its own turns, which is why this gap only
affects a human or an agent acting by hand, which is exactly the population P15 says our guidance exists
to help.

WHY IT MUST NOT BE A REFUSAL, stated as a fence rather than a preference. D1 is explicit: "NUDGE, never a
refusal". A refusal keyed on "a lane for this plan exists" would be the location rule Order 02 deleted,
with a different input: it would block a human finalizing in main whenever an old lane directory happened
to survive, which is a stale-artifact condition rather than evidence anyone is working. P15 names the
alternative it wants here ("Tell the actor early and plainly whose step something is") and the opposite it
forbids ("Key checks on the real condition ... rather than on a proxy"). A lane's EXISTENCE is a proxy; a
live run holding the plan is the real condition, and Order 02 already keys the refusal on that.

FOUR FACTS ESTABLISHED AT AUTHORING. The executor re-measures each (E-01).

1. THE RUNNER ALREADY FINALIZES IN THE LANE, so the nudge recommends the shape the tooling already
   prefers rather than inventing one. `runner_shared` computes the finalize repo as the lane work
   directory when a worktree handle exists, syncs the begin receipt into that worktree, and finalizes
   there; `driver_finalize`'s own comment calls that site "THE primary lane-shadowed site" and records
   that `cwd` stays the lane DELIBERATELY "because finalize must resolve paths against the tree it is
   finalizing".

2. THE LANE RECORDS NEEDED ALREADY EXIST, and they are the right input for an existence question. Lane
   directories live under `worktree_lease.WORKTREES_SUBDIR` (`.aw/worktrees`), owner records under
   `OWNERS_SUBDIR` (`.aw/worktrees/.owners`), the branch name is derived by
   `worktree_lease.lane_branch_name`, and `lane_id_from_branch` inverts it. These answer "does a lane for
   this plan exist" without any liveness claim, which is all the nudge needs.

3. THE NUDGE'S QUESTION IS NOT THE HOLDER PREDICATE'S QUESTION. Order 01's predicate returns NOT HELD
   when no live run holds the plan, which is true for a lane whose run has ended. That is the main case
   the nudge addresses, so reusing the predicate would make the nudge silent exactly when it is wanted.

4. STDOUT IS CARRYING CONTRACTS AND MUST NOT BE WIDENED. `ipd_lifecycle`'s handlers emit `aw.agent/v1`
   JSONL or JSON under `--agent` / `--json`; `runner_shared.parse_finalize_payload` parses finalize's
   stdout; and `nested_aw_message` keeps BOTH streams because "lifecycle verbs print their refusal
   (`error: AW-LIFECYCLE-ROLE-001 ...`) on STDOUT, while stderr carries only advisory notices such as the
   checkout-mismatch line from `checkout_pin`", then drops every line starting with that notice prefix so
   an advisory cannot be misread as a refusal reason. The precedent for a new advisory is therefore
   settled: stderr, and silent in machine-readable modes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the inputs and the channel

- [ ] E-01 RE-DERIVE THE FOUR FACTS IN YOUR OWN LANE, and confirm Order 02 landed: read `ipd_lifecycle.begin` and `finalize` as they now stand and paste the check sequence, confirming the worker-label check and the holder check are present and that no location test remains. Then read the lane-record surface (`worktree_lease.WORKTREES_SUBDIR`, `OWNERS_SUBDIR`, `lane_branch_name`, `lane_id_from_branch`, `read_lane_owner`) and state exactly which of them answers "does a lane or feature branch for THIS PLAN exist" without making a liveness claim. Then read Order 01's predicate and state, in one sentence, why it is the wrong input here. Finally enumerate the output channels of both CLI handlers, pasting the `--agent` / `--json` branch and the `checkout_pin` advisory-notice prefix that `nested_aw_message` strips.
  - Depends on: none
  - Expected outcome: the pasted post-Order-02 check sequences; the named lane-record inputs with the liveness-free one identified; the one-sentence statement of why the holder predicate is wrong here; and the pasted structured-output branch plus the stripped advisory prefix. If any location test survives in either function, STOP and report: Order 02 is incomplete and this plan would build on a gate that should not exist.
  - Execution state: pending

### Task group 2: answer the existence question and say it once

- [ ] E-02 ADD THE LANE-EXISTS QUERY as a small read-only helper that answers, for one plan id6, whether a lane worktree or a lane branch for that plan exists, and returns enough to NAME it in a message. It MUST make no liveness claim and MUST NOT call Order 01's holder predicate, for fact 3's reason: the predicate reports NOT HELD for a lane whose run has ended, which is the main case this nudge serves. Derive the lane identity through `worktree_lease`'s own helpers rather than reconstructing a name from an id6 by hand, which that module explicitly forbids ("Callers must NOT reconstruct this by hand from an id6 ... read `handle.branch` instead"); `lane_id_from_branch` is the sanctioned inspection direction and is documented as "NOT the forbidden reconstruct a name from an id6". It must be TOTAL: any read error, missing directory, or unreadable record yields "no lane found" and never an exception, because a nudge that can raise would convert an advisory into a failed transition.
  - Depends on: E-01
  - Expected outcome: the helper driven against four fixtures (a lane directory present, a lane branch present with no directory, neither present, and an unreadable lane record) returning the lane identity or nothing and never raising; plus a driven case where Order 01's predicate reports NOT HELD and this helper still reports the lane, proving the two questions are distinct.
  - Execution state: pending

- [ ] E-03 EMIT THE ONE ADVISORY LINE from `begin` and `finalize` when the caller is in the MAIN checkout and a lane for that plan exists, phrased as D1 specifies ("a lane for this plan exists; finalizing there keeps main cleaner") and naming the lane so the reader can act. Put it on STDERR and suppress it entirely in `--agent` and `--json` modes, following the `checkout_pin` advisory precedent fact 4 measures: stdout carries a parsed payload and a refusal contract, and a driver strips known advisory prefixes rather than tolerating arbitrary new lines. Emit it AT MOST ONCE per invocation. It MUST NOT change the exit code, must not withhold or delay the transition, and must not prompt: assert that by construction in the code's placement, not only in the message's wording. Say in a comment that this is D1's nudge and that making it a refusal would reintroduce the location rule Order 02 deleted, so a future author does not "strengthen" it.
  - Depends on: E-02
  - Expected outcome: the line pasted as a human-mode caller sees it, with the exit code shown unchanged from the no-lane case; the same invocation under `--agent` and under `--json` shown producing byte-identical structured output to the no-lane case; and the pasted comment stating the never-a-refusal fence.
  - Execution state: pending

- [ ] E-04 ADD THE BEHAVIORAL TEST FILE `tests/test_lifecycle_lane_nudge.py`. Drive the real verbs and assert on rendered output and exit codes: the nudge appears in main when a lane exists; it does NOT appear when no lane exists; it does NOT appear when the caller IS in the lane (there is nothing to nudge toward); it appears for BOTH `begin` and `finalize`; it is absent from `--agent` and `--json` output while the structured payload is byte-identical to the no-lane case; the exit code is identical with and without the nudge in every arm; and THE CENTRAL CASE, that a lane whose run has ENDED still produces the nudge, which is what proves the plan did not wire itself to the liveness predicate. Assert on returned values, exit codes and rendered text only: do not read module source, do not census callers, do not assert which module defines a symbol (AGENTS.md; GUIDING_PRINCIPLES P16).
  - Depends on: E-03
  - Expected outcome: a new passing test file with its bare `python3 -m pytest` output pasted, plus the mutation demonstration V-04 requires showing each arm is sensitive.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here is by symbol or quoted string.
- STDOUT IS A CONTRACT SURFACE FOR THESE VERBS, stderr is the advisory channel. `_refuse_worker_role_verb` writes to stderr explicitly because it is "the diagnostic channel, so a caller parsing stdout for structured output is unaffected"; `nested_aw_message` keeps both streams and strips the `checkout_pin` notice by prefix. E-03 follows that established split rather than inventing a channel.
- A READ MUST NOT MUTATE (GUIDING_PRINCIPLES P10). The lane-exists query is read-only and total; E-02 requires it to swallow every read error into "no lane found".
- NEVER RECONSTRUCT A LANE NAME FROM AN id6 BY HAND (`worktree_lease.lane_branch_name`: "Callers must NOT reconstruct this by hand from an id6, because allocation may attempt-scope the name"). E-02 inspects through `lane_id_from_branch`, which that module documents as the sanctioned inspection direction.
- GUARD AGAINST HONEST MISTAKES, NEVER AGAINST A MALICIOUS AGENT (GUIDING_PRINCIPLES P15). This plan is the purest instance of P15's "WHAT TO BUILD INSTEAD" list: it tells the actor plainly what the preferred shape is and refuses nothing at all.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). The tempting test here is "assert the nudge helper does not import the holder predicate", which is a structure pin; E-04 pins the BEHAVIOR that distinction produces instead, by asserting the nudge still fires when the run has ended.
- COMMENTS AND PLANS ARE NOT USER-FACING PROSE (GUIDING_PRINCIPLES P13). The advisory LINE this plan emits IS user-facing, so it carries no em or en dashes; the code comments around it are exempt.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The runner already finalizes inside the lane | `finalize_repo` is the lane work directory when a worktree handle exists; the receipt is synced into the worktree first; `driver_finalize`'s comment calls it "THE primary lane-shadowed site" | The nudge recommends the shape the tooling already prefers; only hand-run transitions lack it |
| F-2 | The lane-existence records already exist and make no liveness claim | `WORKTREES_SUBDIR`, `OWNERS_SUBDIR`, `lane_branch_name`, `lane_id_from_branch`, `read_lane_owner` | E-02 needs no new record and no new state; it reads what allocation already wrote |
| F-3 | The holder predicate answers a DIFFERENT question and would silence the nudge | Order 01's predicate returns NOT HELD when no live run holds the plan, which is true of a lane whose run ended | Reusing it would make the nudge silent in its main case; E-02 forbids the reuse and V-02 pins the distinction |
| F-4 | Finalize's stdout is parsed by the driver | `runner_shared.parse_finalize_payload` reads finalize's stdout and rewrites it into summary plus diagnostics | A new stdout line could land inside a parsed payload; E-03 uses stderr |
| F-5 | The advisory-on-stderr precedent is established and even has a stripping rule | `nested_aw_message` keeps both streams because refusals print on stdout while stderr "carries only advisory notices such as the checkout-mismatch line from `checkout_pin`", and it drops every line with that notice prefix | E-03 takes the same shape, so a driver cannot mistake the nudge for a refusal reason |
| F-6 | The structured modes must stay byte-identical | Both handlers emit `aw.agent/v1` JSONL or full JSON under `--agent` / `--json` | E-03 suppresses the nudge there, and V-04 asserts byte-identical payloads rather than merely "no nudge visible" |
| F-7 | A lane name must not be rebuilt from an id6 by hand | `lane_branch_name`: "Callers must NOT reconstruct this by hand from an id6, because allocation may attempt-scope the name (see `allocate_worktree`)"; `lane_id_from_branch` is documented as the legitimate inverse for inspection | E-02 inspects rather than constructs; a hand-built name would miss an attempt-scoped lane, making the nudge silently unreliable |
| F-8 | A raising nudge would break a transition it is not allowed to affect | The nudge runs inside `begin` and `finalize`, which perform the transition | E-02 requires the query to be total; an exception would convert an advisory into a failed lifecycle verb |

## Proposed changes (ordered, validatable)

1. Re-derive the four facts, confirm Order 02 landed, and identify the liveness-free lane input (E-01).
2. Add the total, read-only lane-exists query that makes no liveness claim (E-02).
3. Emit the single stderr advisory from `begin` and `finalize`, suppressed in machine-readable modes (E-03).
4. Add the behavioral test file, including the ended-run case that proves the two questions stayed distinct (E-04).

## Deferred / out of scope (with reason)

- ANY REFUSAL, GATE, PROMPT OR EXIT-CODE CHANGE. D1 requires a nudge and never a refusal, and a refusal keyed on a lane's mere existence would be the location rule Order 02 deleted, keyed on a stale artifact rather than on anyone actually working.
  - Carrier-Declined: Nothing is owed because the maintainer decided this in D1. Filing an item would assert the repository intends to make the preference enforceable, which is the opposite of the decision and of P15's guidance to key checks on the real condition.
- THE HOLDER CHECK, THE TOKEN DELETION, THE `--take-over` OVERRIDE AND THE SPEC AMENDMENTS. All Order 02's, and this plan depends on that plan being executed.
  - Carrier: e25iy9
- THE `driver.lock` MACHINE FIELD AND THE LIVENESS PREDICATE. Order 01's, and deliberately not consumed here (F-3).
  - Carrier: urv602
- A NUDGE ON ANY OTHER VERB (`aw set executed`, `aw ipd set executed`, orchestrator retirement). D1 names begin and finalize, and the others are either the runner's own step (retirement) or delegate into finalize, where the nudge already fires from the core function. The executor should CONFIRM the delegation case rather than assume it: if `aw set executed` reaches `finalize` and the nudge is emitted from inside `finalize`, the coverage is free, and V-03 records which it is.
  - Carrier-Declined: Nothing is owed because either the coverage is already free through the delegation (in which case there is no work) or D1's scope deliberately excludes it. The plan requires the executor to record which, so a future reader is not left guessing.
- MAKING THE PREFERRED SHAPE THE DEFAULT BY MOVING THE TRANSITION AUTOMATICALLY. Attractive and firmly out of scope: silently performing a lifecycle transition in a different tree than the one the operator invoked in would be a surprising side effect, and the runner already does it deliberately for its own turns where it owns both trees.
  - Carrier-Declined: Nothing is owed because this is a rejected design rather than latent work. The operator's chosen tree is theirs to choose; P15's prescription here is to inform, and filing an item would assert an intent to act on the operator's behalf without being asked.
- CHANGING THE RUNNER'S OWN IN-LANE FINALIZE. F-1 shows it is already the preferred shape and D1 says it "stays".
  - Carrier-Declined: Nothing is owed because no defect was found; the measurement confirms the existing behavior is the one being recommended.

## Scope check

- Over-scope: none. `agent_workflows/ipd_lifecycle.py` holds both verbs that emit the line and is the natural home for a lifecycle-local advisory. `tests/test_lifecycle_lane_nudge.py` is the one new test surface.
- Under-scope: `agent_workflows/worktree_lease.py` is NOT declared: E-02 CONSUMES its existing helpers and adds nothing to it. If measurement shows the lane-existence question genuinely needs a new helper in that module (because inspecting from outside would duplicate its naming rules, which F-7 forbids), that is a scope change to stop and re-declare rather than absorb, and it is the most likely place this plan's fence is tested. `agent_workflows/cli.py` is not declared: the nudge needs no flag, and adding one would make it configurable, which nothing asks for. `agent_workflows/runner_shared.py` is not declared: the runner already finalizes in the lane (F-1) and will therefore never see the nudge, so nothing changes there. No spec path is declared: the nudge refuses nothing, so it changes no contract any spec states, and D8's search found no spec describing this surface. `CHANGELOG.md` is not declared, for the reason given in Spec / documentation sync.

## Required tests / validation

- `tests/test_lifecycle_lane_nudge.py` is the plan's own surface and must cover every arm named in E-04: present in main with a lane, absent with no lane, absent when invoked inside the lane, present for both verbs, suppressed with byte-identical payloads under `--agent` and `--json`, identical exit codes in every arm, and the ended-run case still nudging.
- THE ENDED-RUN CASE IS THE ACCEPTANCE TEST FOR THIS PLAN'S CENTRAL DESIGN DECISION and must be a case rather than a claim: it is the only assertion that distinguishes a nudge reading the lane records from one wired to the liveness predicate (F-3), and an implementation that took the easy path would pass every other arm.
- THE EXIT-CODE INVARIANCE MUST BE ASSERTED IN EVERY ARM, not once. The plan's core promise is that nothing about the transition changes, and an exit code is the cheapest place that promise could break.
- THE MUTATION DEMONSTRATION IS REQUIRED. For each arm, break the implementation in the smallest way that should flip it (wire the query to the holder predicate; emit on stdout; emit under `--agent`; let the query raise instead of returning nothing) and paste the resulting failure, then restore. The stdout mutation matters most: F-4 shows a driver parses that stream, so this is the failure mode with a blast radius beyond this plan.
- THE LIFECYCLE AND RUNNER SUITES MUST STILL PASS, since E-03 edits two functions the whole runner depends on. Name and run at minimum the `ipd_lifecycle` CLI suites, `tests/test_runner_finalize_message.py`, `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`, and paste each summary; a stray line on the wrong stream surfaces in the runner suites rather than here.
- The full suite, run BARE as `python3 -m pytest` (AGENTS.md), with the actual `N passed` line pasted, plus the pre-edit baseline from the same bare invocation. Do not add `-q`, `-n0` or `-p no:randomly`.

## Spec / documentation sync

- NO SPEC IS AMENDED, and this is a consequence of the plan's own fence rather than an oversight. A spec states a contract about what a surface requires, refuses or guarantees; this plan changes none of those, because the nudge is advisory and cannot affect an outcome. The two specs the Set touches (`7ckptx` R4.5 and A11, `llbr2b` 3.2 and C-8) describe the REFUSAL, which Order 02 changes and amends in the same change. Backlog `dvonrn` D8's exhaustive `.spec.md` search found nothing describing a lane-preference advisory, since none existed.
- NO CHANGELOG ENTRY, deliberately, and the reasoning is worth stating because a new user-visible line looks like an obvious entry. The Set's user-visible change is the replaced refusal, which Order 02's entry describes in full; a separate entry for one advisory line would fragment one change across two entries. If the reviewer prefers it mentioned, the correct home is a clause inside Order 02's entry rather than a new one, and Order 02 declares `CHANGELOG.md` while this plan does not.
- NO DOCUMENTATION UPDATE. No file under `docs/` describes the lifecycle verbs' advisory output; the `checkout_pin` notice that sets the precedent is likewise undocumented outside code. The executor confirms by search rather than assumption.
- THE COMMENT AT THE EMISSION SITE IS THE DURABLE RECORD (E-03), and it carries a specific obligation: it must say that this is D1's nudge and that making it a refusal would reintroduce the location rule Order 02 deleted. That sentence is the only thing standing between a future author and a well-intentioned "strengthening" that undoes the Set.

## Open questions

### OQ-01: Should the nudge also fire on a feature branch that is not a lane, rather than only in the main checkout?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: The plan fires it in the main checkout only, and the reason is that the nudge's value is the reviewed-merge shape: on a feature branch the plan's move ALREADY travels with the code and lands in one merge, so the preferred property holds and there is nothing to recommend. D1 supports this reading: it lists "inside a lane, on a feature branch, or in main" as all allowed, and describes the nudge only for the case where "begin/finalize runs in main and a lane or feature branch for the same plan exists". The counter-case is a feature branch that is NOT the branch whose lane holds the plan, where the record and the code would still separate; that is narrow and the message would be hard to phrase usefully without naming two branches. NOT BLOCKING because the arm is additive: widening the condition later changes one predicate and adds one test case, and the wrong choice costs a missing advisory rather than any incorrect behavior, since the nudge refuses nothing.
- Carrier-Declined: No carrier is owed under either answer. Both conditions are realizable in this plan as written, nothing is left unbuilt, and the consequence of the narrower reading is one fewer advisory line in a case where the preferred property largely already holds.

### OQ-02: Should the advisory be suppressible, by a flag or an environment variable?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: No, and deliberately: it is already silent in every non-interactive consumer (suppressed under `--agent` and `--json`, and on stderr where a driver strips known advisory prefixes), so the only audience that sees it is a human at a terminal, which is the audience it is for. A suppression flag would add a configuration surface whose only function is to hide one line from the person it was written for, and GUIDING_PRINCIPLES P6 counsels against building for a need nobody has expressed. Against that: a scripted human workflow that parses stderr could find it noisy, and the repository does have precedent for honoring `AW_NONINTERACTIVE` and CI signals. NOT BLOCKING because adding a suppression later is purely additive and because no measured need exists today; the plan states the reasoning rather than leaving the absence unexplained.
- Carrier-Declined: No carrier is owed. This is a rejected addition rather than latent work: filing it would assert the repository intends a configuration surface for a single advisory line, and nothing in the backlog item or the decisions asks for one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted post-Order-02 check sequences of `begin` and `finalize`, with an explicit statement that the worker-label and holder checks are present and NO location test remains (a STOP if one does); the named lane-record inputs with the liveness-free one identified; the one-sentence statement of why Order 01's predicate is the wrong input here; and the pasted `--agent` / `--json` output branch plus the `checkout_pin` advisory prefix that `nested_aw_message` strips.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the helper driven against four fixtures (lane directory present, lane branch present with no directory, neither, unreadable lane record) with each returned value pasted and no exception raised in any arm. Plus THE DISTINCTION CASE: a fixture where Order 01's predicate reports NOT HELD and this helper still reports the lane, with both results pasted side by side. Plus evidence the lane identity was obtained through `worktree_lease`'s own helpers rather than a hand-built name, shown by the driven result for an attempt-scoped lane name.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the advisory line as a human-mode caller sees it, pasted, for BOTH `begin` and `finalize`, with the exit code shown identical to the no-lane invocation; the same invocations under `--agent` and `--json` with their structured payloads shown BYTE-IDENTICAL to the no-lane case; proof the line is on stderr and not stdout; proof it appears at most once per invocation; and the pasted comment stating the never-a-refusal fence. Plus the recorded answer for the `aw set executed` delegation: state whether the nudge fires there because it is emitted inside `finalize`, with the driven evidence either way.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new test file's bare `python3 -m pytest` output pasted; the pre-edit and post-edit full-suite `N passed` lines from bare runs; the named lifecycle and runner suite summaries (`tests/test_runner_finalize_message.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py` at minimum). Plus every arm asserted, explicitly including the ENDED-RUN case still nudging and exit-code invariance in EVERY arm. Plus the mutation demonstration: for each arm, the pasted failure produced by the smallest breaking change (wire the query to the holder predicate; emit on stdout; emit under `--agent`; let the query raise) and confirmation the code was restored. Plus an explicit statement that no test reads module source, censuses callers, or asserts which module defines a symbol.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the paths declared in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`: this checkout is shared.

THIS PLAN MUST NOT REFUSE ANYTHING. That is the property to check hardest, because it is the one a well-meaning executor is most likely to improve away. No exit code changes, no transition is withheld, no prompt is asked, and the query cannot raise. If the nudge can affect an outcome, the plan is wrong and the location rule Order 02 deleted has come back in a politer costume.

DO NOT WIRE THE NUDGE TO ORDER 01's LIVENESS PREDICATE. It is the obvious reuse and it is backwards: that predicate reports NOT HELD for a lane whose run has ended, which is the main case this nudge serves, so the reuse would make the advisory silent exactly when it is wanted. V-02 and V-04 both pin the distinction with driven cases, so the shortcut fails the validation rather than passing quietly.

STDERR, NOT STDOUT. A driver parses finalize's stdout into a payload and both handlers emit machine-readable output there. A line on stdout would land inside something a runner reads.

POST-GATE LIFECYCLE MOVE. Do NOT perform a hand-rolled terminal move. In a managed lane the runner performs `aw ipd begin` and `aw ipd finalize`; in an unmanaged or manual run the executor finalizes with `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` after `aw ipd lint --phase pre-transition` reports conforming and every `V-*` above carries concrete pasted evidence. Never `git mv` the plan and never hand-edit `- Status:`.
