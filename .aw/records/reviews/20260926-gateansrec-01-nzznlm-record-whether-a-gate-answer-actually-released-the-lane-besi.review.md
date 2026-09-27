# Review findings: plan nzznlm

- Subject-Id: nzznlm
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5e088a4c` in a lane worktree. Structural preflight `aw ipd lint --phase author --agent`
CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize` conforms after. No
pre-review snapshot was needed: the plan was committed and unmodified, and the lane-input copy at
`.aw/state/lane-inputs/rev-6/` is byte-identical to the tracked file.

THE PLAN'S CENTRAL MEASUREMENT IS TRUE AND I RE-DERIVED IT RATHER THAN TRUSTING IT. Driving the real
`perform_gate_answer` with each of the four tokens and a passing re-run:

```text
not-mine     release=True  integrates=True  released=<absent>  recheck_passed=None
fixed        release=True  integrates=False released=<absent>  recheck_passed=True
mine         release=False integrates=False released=<absent>  recheck_passed=None
needs-human  release=False integrates=False released=<absent>  recheck_passed=False->None
```

So the contradiction is real: a verified `fixed` integrates while its durable record says
`integrates: false`. I also drove the three edge cases E-04 prescribes and all three behave as the plan
predicts (`fixed` with an always-failing re-run -> `release False, recheck_attempts 1, recheck_passed
False`; `fixed` with `rerun_suite=None` -> `release False` and the unverified-repair summary; budget 0 ->
`release False, attempts 0`). The 17-key list in case (6) is EXACTLY the record's current key set by set
comparison (no extras, none missing), and `json.loads(json.dumps(record)) == record` is already True, so
both controls pass today as claimed. F-1 through F-4 all re-verify, including the call-site count: `rg -n
"gate_answer_record\("` across `agent_workflows/` AND `tests/` returns the definition, one docstring
mention, and exactly two calls.

WHAT I FOUND THAT THE PLAN HAD NOT, in descending order of consequence.

FIRST, AND IT IS THE ONLY WAY THIS PLAN COULD DO HARM. `runner_shared` records a MEASURED fail-open
hazard in the comment block at `GATE_ANSWER_RECORD_KEY`, guard (c): a post-merge reader keyed on the
wrong record field "would clear exactly the ids whose repair did not survive the merge, and would
release on two answers designed to refuse", because `failing_tests` is populated for EVERY answer and a
`fixed` record carries `release: True` beside its PRE-REPAIR failures. That is why
`attributed_away_failure_ids` gates on the ANSWER TOKEN (`!= GATE_ANSWER_NOT_MINE` returns `()`), and why
spec `25kzda`'s 2026-09-23 amendment makes it condition (3) of three, "two of them failing OPEN". This
plan adds a field literally named `released`, which is a plausible-looking substitute for that token
check one attribute access away, and the fail-open direction here merges unverified work into main. The
plan said nothing about it. E-02 now MUST carry the warning in the docstring (using the same "WRITING IT
IS NOT READING IT" framing the `suite_baseline` paragraph already established for an audit-only key), and
V-03 now MUST paste a grep proving no reader in the gate-2 channel consults the new key.

SECOND, THE PLAN'S CLAIM WAS WIDER THAN ITS DEFECT. The release outcome is NOT unrecorded today. The run
already appends an `events.jsonl` line whose `event` is `integration-gate-answer-released` or
`...-refused` chosen directly on `gate_outcome.release`, and sets
`item["integration_released_by_answer"]` to the answer token, which `render_stream.integration_was_refused`
actually READS in order not to report a landed run as stranded. The defect is therefore narrower and
still real: the outcome is absent from the ONE structure whose docstring calls itself "the contract a
consumer codes against", so an auditor reading `integration_gate_answer` alone sees a field that reads as
an outcome and says the opposite. The Goal now states that scope explicitly, and OQ-02 records why the key
still belongs on the record (the `suite_baseline` precedent is exactly this case: a fact obtainable
elsewhere, added here because an auditor must be able to ask it of the record in front of them).

THIRD, E-03's SECOND EDIT HAD NO TEST. The interrupted-follow-up producer is not reachable through
`perform_gate_answer`, so none of E-04's eight cases touch it and that edit would have shipped uncovered.
Measured at review, that record's four boolean fields are currently ALL False (`usable: False`, `answer:
""`, `integrates: False`, and `refuses: False`, because `""` is not in `GATE_ANSWERS_REFUSING`), so nothing
in it distinguishes "interrupted before answering" from "answered nothing" - which is precisely what
`released: False` fixes. Added E-05 and V-05.

FOURTH, A TEST-WRITING TRAP. On unmodified code `record["released"]` raises `KeyError`, so the pre-change
result is an ERROR rather than an assertion failure; pytest counts it as failing, which meets the bar, but
a case written with `.get("released", <default>)` could pass vacuously. E-04 now forbids `.get` with a
default for cases (1) to (5), and V-04 requires the executor to say which failure mode each case showed.
V-04 also now prescribes a throwaway detached worktree for the before-change run instead of an in-place
revert, and forbids `git stash` with the shared-checkout reason.

FIFTH, CONTEXT THAT CHANGES HOW MUCH ASSURANCE TO READ INTO A GREEN SUITE. `gate_answer_record` and
`perform_gate_answer` have ZERO existing direct test coverage: the only gate tests in the repository
exercise `validate_gate_answer` (11 call sites in `tests/test_runner_shared.py`). So E-04/E-05 are the
FIRST tests of either function and there is no regression net under this change. While establishing that I
found that three test classes `runner_shared`'s own docstrings cite as pinning gate behavior do not exist
anywhere in the repository, and neither do their files. That is pre-existing and orthogonal, so it is
recorded as F-7 and declined with a reason rather than adopted; its one live consequence is that E-02 must
not add a fourth citation to a nonexistent test, which V-02 now checks.

WHAT I CHECKED AND LEFT ALONE. The spec-sync claim survives, for a better-stated reason: `25kzda`
(`Status: approved`) Section 5.1 requires five facts BY DESCRIPTION ("the answer token, the agent's stated
reason, THE FAILING TEST IDENTIFIERS THE AGENT WAS SHOWN, the session that answered, and the number and
outcome of any suite re-runs") and names no keys; `released` and `recheck_passed` appear nowhere in it, and
its single `integrates` hit is the unrelated `--on-integration-blocked` flag. The additive change disturbs
none of the five. The `integrates`-rename deferral also survives: the backlog item itself lists it as
option 2 and the plan's chosen option 1 is the one the item calls "most honest, purely additive". The
under-scope note on the two host modules is correct and I confirmed it by grep rather than by reading.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | B. Security / A. Correctness (a fail-open hazard the new field makes easier to reach) | Guard (c) comment block at `runner_shared.GATE_ANSWER_RECORD_KEY`: a reader keyed on the wrong field "would clear exactly the ids whose repair did not survive the merge, and would release on two answers designed to refuse"; `attributed_away_failure_ids` body `if str(record.get("answer") or "").strip() != GATE_ANSWER_NOT_MINE: return ()`; `unattributed_merged_failures`'s two guards, both documented as failing OPEN if omitted; spec `25kzda` 2026-09-23 amendment condition (3) | **THE PLAN ADDS A FIELD WHOSE NAME IS AN INVITATION TO A MEASURED FAIL-OPEN BUG, AND SAID NOTHING ABOUT IT.** The gate-2 attribution channel must key on the ANSWER TOKEN; a future reader wanting "did this integrate?" will now find a field that answers yes for `fixed` too, and substituting it releases on answers designed to refuse. The direction matters: this arm licenses a PASS, so the failure merges unverified work into main rather than over-refusing. The plan's own Scope said "changing what `attributed_away_failure_ids` or any other reader reads" is OUT, which is correct as far as it goes and is not the same as warning the next author away from the substitution. | C:Low; U:Low; S:Low; F:Low for the chosen fix (a docstring paragraph plus one grep in validation). The RISK OF OMITTING it is High on the security axis, which is why it is fixed rather than noted. | FIXED | E-02 now requires the docstring to state that `released` is audit-only, is NOT an admissibility signal, and that the gate-2 channel keys on the token and must not be repointed, using the established `suite_baseline` "WRITING IT IS NOT READING IT" framing. V-03 gains a required anti-regression grep proving none of the three readers consults the new key, with "a hit is a fail-open regression and must be removed, not explained". Recorded as F-6; the gate carries a "THE ONE REAL RISK" paragraph; the scope fence now names the three readers as explicitly out of scope. |
| PR-002 | MEDIUM | IN-SCOPE | F. Honest documentation / G. Executability | `runner_shared.execute_item_core`: `append_jsonl(run_dir / "events.jsonl", {... "event": "integration-gate-answer-released" if gate_outcome.release else "integration-gate-answer-refused" ...})`; `item["integration_released_by_answer"] = gate_outcome.record.get("answer")`; `render_stream.integration_was_refused` returning False when that key is set | **THE PLAN'S FRAMING IMPLIED THE RELEASE OUTCOME IS UNRECORDED, AND IT IS RECORDED TWICE.** The Concern says the record holds "no field recording what actually happened" (true of that record) but the Goal and gate read as though the fact were unavailable. One of the two existing sites is actively READ by the renderer. Left as written, a reviewer could reasonably ask why the plan is needed at all, and an executor could overstate the fix in the CHANGELOG or the finalize message. The defect is real but narrower: absence from the record that declares itself the consumer contract. | C:Low; U:Low; S:Low; F:Low | FIXED | Added F-5 with both sites and the reader. The Goal now carries an explicit "SCOPE OF THE CLAIM" paragraph stating the outcome is not lost and naming what is actually being fixed. The gate carries a "WHAT THIS IS AND IS NOT" paragraph. Added OQ-02 (resolved) recording why the key still belongs on the record, citing the `suite_baseline` precedent for a fact obtainable elsewhere. Project conventions note added. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Testing | E-03 edits two producers; E-04's cases all drive `perform_gate_answer`, which cannot reach the `except (KeyboardInterrupt, StallTimeout):` site; measured at review, that record's booleans are `usable False`, `integrates False`, `refuses False`, `answer ""` | **ONE OF THE TWO EDITS HAD NO TEST SURFACE.** The interrupted-follow-up producer is unreachable through the function every test case uses, so E-03's second edit would have shipped uncovered while V-03's evidence ("the diff at each") showed only that the line was written. The measurement makes it worth testing rather than trivial: all four of that record's boolean fields are currently False, so the record cannot today distinguish an interruption from an empty answer, and `released: False` is the field that states the fail-closed outcome. | C:Low; U:Low; S:Low; F:Low | FIXED | Added E-05 (call `gate_answer_record` directly with that site's verdict and `released=False`, asserting the value AND the three sibling booleans) and V-05 requiring it to pass after and fail before, with the boolean values pasted so OQ-01's claim is visible rather than asserted. OQ-01's rationale strengthened with the measurement. |
| PR-004 | MEDIUM | IN-SCOPE | E. Testing (a vacuous-pass trap and an unsafe before-run mechanism) | Measured at review: `record["released"]` on unmodified code raises `KeyError: 'released'`, not an assertion failure; V-04 as written prescribed "the same run with E-02/E-03 temporarily reverted"; `.gitignore` ignores `.aw/worktrees/` and `tmp/` | **THE PRE-CHANGE FAILURE IS AN ERROR, AND THE PRESCRIBED WAY TO OBSERVE IT WAS AN IN-PLACE REVERT IN A SHARED CHECKOUT.** Two distinct problems. A case written as `record.get("released", <default>)` could pass vacuously, so the plan's "six failing before" is only guaranteed if the tests subscript; and an in-place revert is the single action in this plan that can lose work, with no instruction on interruption and an obvious wrong reflex (`git stash`) that would move a co-worker's changes. | C:Low; U:Low; S:Low; F:Medium-High if the in-place revert is interrupted, but the FIX is Low (prescribe a throwaway worktree) | FIXED | E-04 forbids `.get("released", <default>)` for cases (1) to (5) and requires subscripting or an explicit presence assertion. V-04 prescribes a throwaway detached worktree with the gitignored paths and the teardown command, permits an in-place revert only if restored in the next command and recorded, forbids `git stash` with the shared-checkout reason, and requires the executor to state whether each case failed by assertion or by `KeyError`. |
| PR-005 | LOW | IN-SCOPE | E. Testing (assurance overstated by omission) | `rg -l "gate_answer" tests/` -> `tests/test_runner_shared.py` only; `rg "perform_gate_answer" tests/` empty; `rg "gate_answer_record\(" tests/` empty; `rg "NothingRefusesOnTheBaseline\|TheExitCodeIsTheAuthorityAndNotTheList\|TheTwoMeasurementsAreComparable" .` empty; neither `tests/test_suite_baseline.py` nor `tests/test_suite_adjudication.py` exists; measured `tests/test_runner_shared.py` -> `93 passed in 14.51s` | **NEITHER FUNCTION THIS PLAN EDITS HAS ANY EXISTING TEST, AND THREE TESTS THE MODULE CITES AS PINNING ITS BEHAVIOR DO NOT EXIST.** "`tests/test_runner_shared.py` stays green" reads as a regression net and is not one for these two functions. The missing-test-class finding is pre-existing and orthogonal, but it has one live consequence for this plan: E-02 edits that docstring and must not add a fourth citation to a nonexistent test. | C:Low; U:Low; S:Low; F:Low | FIXED | Added F-7 with all four greps. "Required tests / validation" now states these are the first direct tests of both functions and that no regression net exists under them, records the measured 93-test baseline as the regression bar, and notes neither file is slow-marked so both run in the bare suite. The three missing classes are recorded under Deferred with a reasoned `Carrier-Declined` (pre-existing, separate scope, and filing a carrier would assert a decision nobody made). V-02 checks that E-02 adds no such citation. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | A field named `released` sits one attribute access away from a measured fail-open substitution in the gate-2 attribution channel. Widen the plan to harden those readers, warn in the docstring, or say nothing? | WARN IN THE DOCSTRING and prove the absence of such a read in validation; change no reader. | (a) Harden the readers (e.g. assert the token check in a test): rejected as over-scope. The readers are already correct and already documented with their measurements; adding assertions about code this plan does not change would widen the blast radius of an additive key into the revalidation gate, which is the highest-consequence path in the runner. (b) Say nothing: rejected outright. The hazard is recorded as MEASURED and the fail-open direction merges unverified work into main; adding the attractive nuisance without the warning is the one way this plan makes things worse. (c) Name the key something less inviting (e.g. `outcome_released`): rejected, it trades a documented hazard for a worse-named field and the backlog item's option 1 explicitly proposed `released`. | Guard (c) block at `GATE_ANSWER_RECORD_KEY`; `attributed_away_failure_ids`'s token gate; `unattributed_merged_failures`'s two fail-open guards; spec `25kzda` 2026-09-23 amendment condition (3); the `suite_baseline` "FOR AUDIT AND NOTHING ELSE" / "WRITING IT IS NOT READING IT" precedent in the same docstring | yes |
| D-2 | The release outcome is already in `events.jsonl` and `integration_released_by_answer`. Does the plan still have a defect to fix, and does it need the maintainer's view? | YES it does, and NO the maintainer need not be asked: narrow the CLAIM and keep the change, resolved from the record's own declared contract. | (a) Retire the plan as redundant: rejected. The `gate_answer_record` docstring declares itself "the contract a consumer codes against" and names `state["queue"][i]["integration_gate_answer"]` as the location; a consumer coding against it reads that dict and finds an outcome-shaped field asserting the opposite of what happened. (b) Ask the maintainer whether record-local legibility is worth one key: rejected, the repository already answered it by adding `suite_baseline` to this same record "FOR AUDIT AND NOTHING ELSE" for a fact obtainable elsewhere. (c) Leave the plan's wider framing: rejected, it would let the executor overstate the fix. | `gate_answer_record` docstring's contract and `suite_baseline` paragraphs; the `events.jsonl` event-name selection on `gate_outcome.release`; `item["integration_released_by_answer"]`; `render_stream.integration_was_refused` reading it; backlog `w51mpv` option 1 | yes |
| D-3 | E-03's interrupted-follow-up edit is unreachable from `perform_gate_answer`, so E-04 cannot test it. Add a case, or accept the diff as evidence? | ADD E-05 testing `gate_answer_record` directly with that site's verdict. | (a) Accept the diff: rejected, a pasted diff proves a line was typed and not that the value is right; this plan's whole subject is a record field that was individually defensible and wrong in context. (b) Refactor so the site is reachable through `perform_gate_answer`: rejected, that changes control flow in the interrupt handler, which is fail-closed safety code far outside an additive-key plan. | The `except (KeyboardInterrupt, StallTimeout):` block building the record directly; measured record booleans all False (`usable`/`integrates`/`refuses`/`answer`); `GATE_ANSWERS_REFUSING` excluding `""` | yes |
| D-4 | Three test classes the module's docstrings cite as pinning gate behavior do not exist. Fix, file a carrier, or record and decline? | RECORD AND DECLINE (F-7 plus a reasoned `Carrier-Declined`), with one live obligation: E-02 must add no fourth such citation. | (a) Write the three missing test classes: rejected, pre-existing, orthogonal, and a substantial piece of work with its own scope and approval; folding it in would make an additive-key plan a test-authoring plan. (b) File a backlog carrier: rejected on the repository's own standard, that a carrier must not assert work nobody has decided to do; the honest state is that a reviewer noticed stale citations in paragraphs this plan does not edit. (c) Say nothing: rejected, because E-02 edits that very docstring and a fourth dangling citation is the one way this plan could worsen it. | `rg` for all three class names across the repository: empty; `ls tests/` shows neither cited file; the citing paragraphs are the `baseline`-reaches-no-decision paragraph and the guard (c) block, neither in this plan's edit path | yes |

### Deferred and open

- (none DEFERRED among findings). All five findings were FIXED in place. PR-001 is `HIGH` and is FIXED, so
  no finding sits at or above the repository's gate threshold (no `review_findings_gate` is configured in
  `.aw/config/project.json`, so the default `HIGH` applies) unfixed, and nothing is owed an escalated
  `- Blocking: yes` question.
- No `Reversible: no` decision was taken. D-1 is the one with a security consequence, and it is reversible
  in the sense that matters: it adds a docstring paragraph and a validation grep, both of which a later
  maintainer can change freely, and it changes no reader.
- The plan's two open questions are both `resolved` and both `Blocking: no`.

HONEST LIMITS, stated because they bound what this round proves. I drove `perform_gate_answer` and
`gate_answer_record` directly with stubs; I did NOT run a real `aw oc run`/`aw agy run`, so the claim that
both hosts reach this record through the shared producers rests on the call-site grep and on
`execute_item_core` being the single write seam, not on an observed live run. I did not apply E-02 or E-03
and wrote no test, so that the shipped docstring actually carries the F-6 warning, that the new tests are
red before the change, and that the bare suite stays green are all still E-02/E-03/E-04/E-05's work and
their evidence. I ran `tests/test_runner_shared.py` (`93 passed`) but did NOT run the bare suite for this
plan, so the before/after node-ID comparison V-04 requires is unperformed by me; for a purely additive dict
key with no reader that is proportionate, and it is a hole rather than a clearance. My F-5 conclusion that
the outcome is "already recorded twice" is a reading of the write sites plus one reader
(`render_stream.integration_was_refused`); I did not survey consumers outside this repository, and the
`gate_answer_record` docstring's own statement that `<run_dir>` is gitignored means no committed corpus
exists here to check a real record against. Finally, F-7's missing test classes are reported as absent from
THIS repository at THIS HEAD; I did not investigate whether they were deleted, renamed, or never written,
and that question is deliberately left open rather than guessed at.
