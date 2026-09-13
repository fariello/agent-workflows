# Review: decide and build how the runner dispatches a non-plan artifact, child mng63x (Set specdispatch)

- Subject-Id: mng63x
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `e61e9fef`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review, and that clean result is itself the subject of this review's two
BLOCKER findings: the plan was structurally perfect and had no working guard of any kind.

DISCLOSURE: same repository, same model family, and the same session that reviewed the sibling plan
`ui8b9b`, so this is close to a self-review and worth less than an independent one. Its value rests on
what was DRIVEN rather than read. Measured here: the plan copied and flipped to `approved` and linted at
all four checkpoints; `parse_scope_paths` called on the plan's own authored value; `_frozen_scope_paths`
and `_scope_match` called against three real repository paths; `authoring_placeholders_resolved` called
on the authored text and on a `TODO` variant; `is_plan_review_approved` called for all three readiness
values and for absence; `resolve_plan_path` CALLED with a real spec path and id6; the dispatch table
dumped; `discover_plans` and `build_dynamic_manifest` read; all eleven `SPEC-*` codes grepped across the
package; `Depends on` grepped across the linter and both runners; the `configured_file` and
`resolve_plan_path` call sites counted per host; `aw check --agent` run and filtered; the sibling plan's
current status read; and spec `25kzda` Sections 3.3 and 4.8 plus `6m4kow` Section 0 read in full.

THE PLAN'S PREMISE AND ITS CONSTRAINTS ARE ACCURATE, which is worth saying before the blockers, because
this is a carefully evidenced plan and its factual core survived verification. `build_dynamic_manifest`
compiles only discovered plans and `discover_plans` walks only the two plans trees, so F-2 holds.
`oc_runipd.py:2959` writes `"configured_file": plan["file"]` verbatim and `resolve_plan_path` is imported
into the oc queue path at `:221`, so F-3's citations are exact. `_SPEC_ACTIONS` routes `approved` to
`ACTION_PLAN` and OMITS `implementing` with the comment the plan quotes, so F-4 is right that two of the
three declared actions are not review turns. `spec-review` prohibition (c) says what F-5 says it says.
The scope discipline is right, the three candidate shapes in E-01 are genuinely the three shapes, and
keeping option (c) on the table is correct since `25kzda` 3.3 mandates that spec review HAPPEN, not that
a runner perform it.

THE FINDING THAT MATTERS MOST IS THAT THE PLAN'S PRIMARY GUARD DID NOT EXIST, AND ITS ABSENCE WAS
UNDETECTABLE FROM THE PLAN'S OWN TEXT. The plan asserted three separate times that its unset
`- Scope-Paths:` fence is what stops an agent building before the design ruling, and that "`aw ipd lint`
will refuse the plan until it is [filled in]". The field was not unset. It held a prose sentence, and
`parse_scope_paths` split that sentence ON ITS COMMAS into three entries, each of which passed
`_scope_path_entry_error` (no leading slash, no `..`, no root-level glob, so nothing to reject). I copied
the plan, flipped `- Status:` to `approved`, added an `Approval:` line and neutralized the unrelated
dependency edge, and `aw ipd lint --phase pre-execution` returned `conforming` at exit 0. Removing the
field ENTIRELY instead produces `IPD-M106`, so the plan was in a strictly worse position than if its
author had left the field off: the prose satisfied the gate that absence would have tripped. Worse,
`ipd_lifecycle._frozen_scope_paths` returns those three sentence fragments as the frozen execution
allowlist, and `_scope_match` matches `agent_workflows/oc_runipd.py`, `tests/test_x.py` and a `.spec.md`
path against NONE of them, so the scope fence would have failed open at `begin` and misreported every
changed path at `finalize`. There is a near miss worth recording: had the value been the literal scaffold
token `TODO`, `ipd_authoring.authoring_placeholders_resolved` would have returned False and the plan
would have been flagged as an unfinished stub. The prose value returns True.

THE SECOND BLOCKER IS THAT THE PLAN ARGUED ITSELF OUT OF THE ONE GUARD THAT DOES WORK, and it did so at
length and persuasively. OQ-01 was authored `- Blocking: yes` and then deliberately changed to `no`, with
a recorded rationale that blocking "would say the plan cannot START, which is false and would make its
own first item unreachable", relying instead on the E-item dependency graph. Both premises are false.
NOTHING enforces intra-plan E-item ordering: `parse_depends_on` and `dependency_errors` validate only
syntax, self-reference and cycles, `Depends on` appears exactly once in `ipd_lint.py` (being read) and
ZERO times in either runner. And `IPD-Q501`'s own message names asking the human as the remedy, which IS
E-01, so a blocking question never made E-01 unreachable; it refuses everything downstream of E-01, which
is exactly what the plan wanted. Measured: with `Blocking: no` the approved copy linted `conforming`;
with `Blocking: yes` the same copy is refused by `IPD-Q501` at `author` and `review-finalize` and
additionally by `IPD-S404` at `pre-execution`. I reversed a documented author decision here, which is a
thing to do carefully, so the measurement is recorded in the plan itself rather than only in this record.

TAKEN TOGETHER THOSE TWO ARE THE WHOLE POINT: a plan whose entire reason for existing is that it MUST NOT
be built before a maintainer ruling had no mechanism preventing that, while asserting three. A
`--full-auto` runner reaching it at `reviewed` would have consulted `is_plan_review_approved`, found no
`- Readiness:` field, fallen back to the history, and correctly declined only because no review had run
yet. The next review to write `go-pending-approval` would have unlocked a design-first plan for
execution. The plan now carries `- Readiness: no-go`, which `is_plan_review_approved` refuses (verified
for all three values and for absence) and which `approval_refusals` refuses with NO override, so getting
this plan approved requires a re-review that changes the readiness. That is the correct cost.

TWO CONSTRAINTS THE PLAN DID NOT HAVE AND NEEDS. First, E-04 required the turn to "satisfy the three
checks spec `25kzda` 4.8 names", and none of those three exists: all eleven `SPEC-*` codes grep to ZERO
files under `agent_workflows/`, and `25kzda`'s own preamble tells a reader to treat its codes as
specification rather than shipped behavior and to cite the shipped enforcer by symbol. So E-04 as written
would have had an executor either build three unbudgeted checks or, far more likely, claim three passing
gates that cannot run. Second, `resolve_plan_path` FAILS OPEN on a spec rather than resolving it in the
wrong tree: called with a real spec path in `configured_file` and a spec id6 it RETURNS THE SPEC PATH via
its `configured` direct-path branch, with the plans-tree selector attempt swallowed by a bare `except`.
That is worse than F-3 described, it is the silent-wrong-action shape E-02 exists to prevent, and it
argues for a typed resolver over guarding the 48 plan-shaped call sites (10 `configured_file` plus 15
`resolve_plan_path` in oc, 10 plus 13 in agy).

WHAT I DELIBERATELY LEFT ALONE. I did not answer OQ-01, and this review must not be read as narrowing it:
the maintainer reserved it, the repository supplies constraints and not an answer, and the three candidate
shapes remain genuinely open including option (c). I did not add a fence for the build items either,
because inventing one would pre-commit the design that E-01 is supposed to decide; the build items are
held by the readiness field and the blocking question instead, which is the honest shape. E-02's
insistence that a spec not be represented as a degenerate plan is right and I strengthened only its
evidence. V-01's refusal to accept a design ruling with no human attestation is the single best thing in
the plan and I left it untouched.

No product code was modified by this review. Full suite run bare: `6280 passed, 3 skipped, 2 xfailed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | BLOCKER | IN-SCOPE | G (executability), A (correctness) | `parse_scope_paths` (`ipd_schema.py:543`) split the authored prose value on its commas into 3 grammar-passing entries; `aw ipd lint --phase pre-execution` returned `conforming` exit 0 on a copy flipped to `approved`; removing the field returns `IPD-M106`; `ipd_lifecycle._frozen_scope_paths` froze the 3 fragments and `_scope_match` matched 0 of 3 real repository paths | THE PLAN'S PRIMARY GUARD DID NOT EXIST AND ITS ABSENCE WAS UNDETECTABLE FROM THE PLAN'S TEXT. The plan asserted three times that the unset `- Scope-Paths:` fence plus `aw ipd lint` would refuse it until the design was decided. The field was not unset but prose, the grammar accepted its comma-separated fragments as paths, and the linter passed the plan. So the plan was executable, and its scope fence would additionally have failed open at `begin` and misreported at `finalize`. A prose value is in a strictly WORSE position than an absent one, which `IPD-M106` refuses. Near miss: the literal token `TODO` would have been caught by `authoring_placeholders_resolved`; prose is not. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-7. `- Scope-Paths:` replaced with a single real path (the spec E-01's ruling is recorded in), the narrowest honest fence for a plan whose only executable item is a discussion. The build items are held by PR-802's and PR-803's mechanisms instead. Concern, scope check, proposed changes, V-01 and required tests all corrected; V-01 now demands the frozen allowlist MATCH a real path rather than merely lint clean. |
| PR-802 | BLOCKER | IN-SCOPE | G (executability) | `parse_depends_on`/`dependency_errors` (`ipd_schema.py:909`/`:921`) validate syntax, self-reference and cycles only; `Depends on` appears once in `ipd_lint.py:559` and zero times in either runner; with `Blocking: no` an approved copy linted `conforming`, with `yes` it is refused by `IPD-Q501` at author + review-finalize and `IPD-S404` at pre-execution | THE PLAN ARGUED ITSELF OUT OF ITS ONE WORKING GUARD. OQ-01 was authored `Blocking: yes`, then changed to `no` on the reasoning that `Depends on: E-01` already refuses downstream work and that blocking would make E-01 unreachable. Nothing enforces intra-plan E-item order (no runner reads the field), and `IPD-Q501`'s own message names asking the human, which IS E-01, so blocking never made E-01 unreachable. Combined with PR-801 the plan had NO working guard while asserting three, and a `--full-auto` runner promoting it would have dispatched a design-first plan as though the design were settled. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | New F-8. OQ-01 restored to `- Blocking: yes`, with the reversal's measurement recorded IN the plan (both premises falsified, both lint outcomes pasted) rather than quietly made, since it overrides a documented author decision. The gate paragraph's guard list was rewritten from three fictions to four verified mechanisms, three machine-enforced and one a review obligation, with that distinction stated. |
| PR-803 | HIGH | IN-SCOPE | G (executability), C (architecture) | `is_plan_review_approved` returns False for absence (verified) and `no-go`, True for `go`/`go-pending-approval`; `approval_refusals` refuses a non-approvable value with NO override; `IPD-M107` refuses an unattested value | ABSENCE OF `- Readiness:` WAS FAIL-CLOSED BUT SILENT, SO IT COULD NOT CARRY THE PLAN'S INTENT. Correct for authoring (the field is a review output and `IPD-M107` refuses a hand-written one), but indistinguishable from every un-reviewed plan and saying nothing to a human approver. The mechanism that CAN carry "not executable as authored" past a review is `no-go`, the one value that refuses both automated approval and a human `aw set approved`, with no override. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-9. `- Readiness: no-go` written as this review's own output, which is the field's legitimate author. Recorded in the plan as the first of its four real guards, with the predicate named so a later reader can re-verify rather than trust the claim. |
| PR-804 | MEDIUM | IN-SCOPE | E (testing), G (honest documentation) | zero files under `agent_workflows/` contain any of the 11 `SPEC-*` codes; `25kzda`'s preamble: read Section 4.2's codes "AS SPECIFICATION, NOT AS SHIPPED BEHAVIOR ... cite the shipped enforcer by symbol"; the shipped substitutes are `aw specs check` and `TRANSITION_AUTHORITY["->reviewed"]` with `review_record: True` | E-04 CITED THREE UNBUILT CHECKS AS THOUGH THEY WERE ENFORCEABLE GATES. It required a runner-driven spec turn to "satisfy the three checks spec `25kzda` 4.8 names"; none is bound to a predicate, and `6m4kow` A-08 merely requires they be "satisfiable". So the item silently contained either three unbudgeted deliverables or an invitation to claim three passing gates that cannot run, which is the exact skipped-gate-looks-like-a-passed-one failure F-5 warns about. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-10. E-04 re-aimed at the two gates that DO ship (`aw specs check` plus the attestation predicate, named by symbol), with binding the three codes made an explicit E-01 decision rather than an assumption. V-04 now forbids pasting "the three checks exercised by name" unless the plan built them, and requires the ruling be stated either way. E-01 gains it as a constraint the discussion must cover. |
| PR-805 | MEDIUM | IN-SCOPE | A (correctness), C (architecture) | `resolve_plan_path(repo, "<6m4kow spec path>", "6m4kow")` RETURNS the spec path via the `configured` branch (`runner_shared.py:1444`), the plans-tree attempt at `:1438` swallowed by a bare `except`; the same call with empty `configured` raises `DriverError`; 48 plan-shaped call sites across the two hosts | THE PLAN-SHAPED RESOLVER FAILS OPEN ON A SPEC RATHER THAN REFUSING, inverting the risk F-3 described. F-3 said a spec would resolve "in the wrong tree, or resolve correctly by accident"; the accident is the DEFAULT, because a queue entry always carries `configured_file` and that branch only checks `is_file()`. A function named `resolve_plan_path` returns a `.spec.md` path with no diagnostic. This also means a test asserting "a spec resolves" would PASS against unchanged code. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-11, and F-3 rewritten with the measured behavior and the 48-call-site count replacing the qualitative description. Added to E-01 as a constraint (evidence for a typed resolver over 48 per-call-site guards) and to required tests as a trap: the test must assert refusal or type-correct routing, never mere success. |
| PR-806 | LOW | IN-SCOPE | G (honest documentation) | `ui8b9b` now reads `- Status: reviewed` / `- Readiness: go-pending-approval`, not `to-review`; a copy of this plan flipped to `approved` was refused with `check.ipd-dependency-dangling: executed:ui8b9b` | F-6 CARRIED A STALE SIBLING STATUS, AND ITS ENFORCEMENT CLAIM WAS THE ONE THAT WAS TRUE. The row said `ui8b9b` is `to-review`; it has since been reviewed. More usefully, F-6's claim that the runner's dependency check enforces the order IS correct, verified by the refusal, which makes it the instructive contrast with PR-802's intra-plan `Depends on:` that enforces nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 updated with the current sibling status and the observed `check.ipd-dependency-dangling` refusal, and explicitly contrasted with F-8 so a reader sees which of the plan's two dependency mechanisms is real. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's `- Scope-Paths:` prose was silently accepted as three paths. Declare a real fence for the build items, leave the field off, or declare only what E-01 touches? | Declare ONLY the spec file E-01's ruling is recorded in. | (a) Invent a fence for E-02 to E-04 from the three candidate shapes; (b) remove the field entirely and rely on `IPD-M106` to refuse the plan at pre-execution. | (a) would pre-commit the design OQ-01 reserves for the maintainer, which is the one thing this plan exists not to do. (b) is defensible and I nearly took it, but it makes the plan's ONLY currently-executable item (E-01, a discussion that legitimately touches the spec) unfenceable, and it leaves the refusal at `pre-execution` only, while the readiness field and blocking question refuse from `author` onward. A narrow true fence plus two earlier guards is strictly stronger than an absent fence. | yes |
| D-2 | OQ-01 was authored `Blocking: yes` and deliberately changed to `no` with a recorded rationale. Reverse a documented author decision? | Yes, reverse it to `Blocking: yes`. | Respect the author's later judgement and instead add a different guard (readiness alone), leaving the field `no`. | Both premises of the recorded rationale are FALSE as measured, not merely arguable: `Depends on:` is read by no runner and enforces nothing, and `IPD-Q501` names asking the human as its remedy, which is E-01 itself, so blocking never made E-01 unreachable. And the two values were compared empirically: `no` linted `conforming` on an approved copy, `yes` is refused at three checkpoints. Leaving it `no` with readiness as the only guard would rest the plan's whole non-executability on a single field. The reversal and its measurement are recorded in the plan so the author can see why. | yes |
| D-3 | E-04 required three `25kzda` 4.8 checks that grep to zero files. Build them, drop them, or defer the choice? | Defer to E-01 explicitly, and forbid claiming them as passed meanwhile. | Rule them OUT here (gate on `aw specs check` plus the attestation predicate only); or rule them IN as three new deliverables. | Binding three named checks is real scope with its own tests, and whether it belongs in this plan depends on the shape OQ-01 chooses (option (c), not running spec review under the runner at all, would make them moot entirely). So the choice is genuinely the maintainer's ruling to imply, not mine. What is NOT deferrable is the honesty half: V-04 now refuses evidence claiming the three passed, since nothing can run them, and that closes the hazard without pre-empting the decision. | yes |
| D-4 | Should this review answer OQ-01, given it now has all the constraints measured? | No. Leave it open and blocking. | Recommend shape (a) generalize-the-queue-entry, which the `eyh1fu` precedent and PR-805's typed-resolver evidence both point toward. | The maintainer reserved this decision explicitly and the instruction to capture that loudly is the plan's whole reason for existing; an agent recommending a shape is how a reserved decision becomes a fait accompli. My measurements (PR-805's fail-open resolver, PR-804's unbuilt checks) are INPUTS to that discussion and are recorded as constraints in E-01, not as a recommendation. Option (c) also remains live on spec grounds (`25kzda` 3.3 mandates spec review happen, not that a runner perform it), and nothing I measured bears on it. | yes |

No decision this round is `Reversible: no`, so none required escalation as a blocking question. Both
BLOCKER findings were FIXED rather than deferred, so neither needed escalating either; the plan's one
remaining open question is the maintainer's reserved design decision, which was already blocking by
this review's own correction. The honest state of this plan: its constraints are accurate and now more
completely measured, its guards are real for the first time, and it is waiting on exactly the discussion
it was filed to request.
