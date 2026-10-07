# IPD: Close the two measured positional specs set gate bypasses by unioning the refusals

- Date: 2026-10-01
- Kind: child
- Concern: Two gates on `aw specs set` are reachable through only ONE of that verb's two spellings, and in both cases the spelling that SKIPS the gate is the shorter, more idiomatic one an agent is likelier to type. MEASURED 2026-10-01 at HEAD `ec857565a` in scratch repositories over identical fixtures. (1) `aw specs set <path> --status implemented` on an `implementing` spec exits 1 with `requires a resolvable --evidence citation` and writes nothing, while `aw specs set implemented <id6>` exits 0 and relocates the file into `specs/implemented/`. `AGENTS.md` states as policy that an agent "may NOT set `implemented` (needs cited evidence)", so the positional spelling lets an agent assert a spec is implemented with no cited executed IPD, which is a forged attestation of the same class the `Readiness` and `--by-human` rules exist to prevent. Filed `h4fiwa`. (2) `aw specs set <path> --status deferred --gate-kind bogus-kind --gate-ref x` exits 1 and writes nothing, while the positional spelling exits 0 and writes `- Gate-Kind: bogus-kind` to disk, producing a spec that violates the typed-gate contract `AGENTS.md` states ("A `deferred` spec MUST carry a typed gate") and converting a fail-closed refusal into an at-rest checker finding. Filed `fv4b6s`. Both are the fourth and fifth instances of the recurring class backlog `fcnz1r` documents.
- Scope: IN: make both refusals fire on BOTH spellings by having the shared engine consume the SAME predicates `specs.run_set` already consumes, never a second copy; author outcome tests pinning each refusal on both spellings; close the two carriers with cited evidence. OUT, each with a reason recorded under "Deferred": moving either spelling's dispatch route (children 04, 05, gated on spec `wy9aru` OQ-1); the third `specs.run_set`-only refusal (the post-write `validate_spec` conformance check), which is a different shape and is carried by child 04; every axis `wy9aru` Section 7 assigns elsewhere.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/specs.py, tests/test_specs_set_gate_parity.py, CHANGELOG.md
- Item-Dependencies: executed:afdmn6
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: wy9aru
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- From-Backlog: fcnz1r
- Set: setdisp
- Order: 3
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m1jlwm

## Workflow history
- 2026-10-07 /plan-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005 (all fixed; F-02 already closed by `ju3rhs` so E-02 is confirm-only; carriers close via HANDOFF; record `.aw/records/reviews/20261007-setdisp-03-m1jlwm-close-the-two-measured-positional-specs-set-gate-bypasses-by.review.md`)
- 2026-10-07 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by new Order 06 7zb4ny; coverage pass recorded; open questions are non-blocking executor measurements
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: The bare suite pytest after the final child compared by name against baseline
- 2026-10-01 same-status (aw set): status unchanged (to-review)

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `fcnz1r` under spec `wy9aru`. Both bypasses were MEASURED, not inferred, by driving both spellings over identical fixtures at HEAD `ec857565a`; each was filed as its own release-gated carrier (`h4fiwa`, `fv4b6s`) so the gate is not silently absorbed into the `chore`-classified parent item. This plan carries `- Work-Kind: bug` and `- Blocks-Release: next` accordingly (`AGENTS.md`: every live bug gates the next release).
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the `implemented`-needs-evidence gate and the `deferred`-needs-a-valid-typed-gate refusal
unbypassable, so that neither can be defeated by choosing the other spelling of the same verb, and so
no spec reaches `implemented` or carries an out-of-vocabulary gate kind without the gate having run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

RE-MEASURED AT REVIEW 2026-10-07 (scratch repo, lane package pinned with `PYTHONPATH` and `AW_NO_REEXEC=1`): the POSITIONAL `aw specs set implemented abc123` on an `implementing` spec with no `--evidence` still exits 0 and relocates the file into `specs/implemented/`, so the F-01 bypass is LIVE. The POSITIONAL `aw specs set deferred def456 --gate-kind bogus-kind --gate-ref x` now refuses ("aw set: --gate-kind must be one of [...]. Refusing before making changes.") and the file stays in `approved/` with no `Gate-*` line, so the F-02 bypass is ALREADY CLOSED, by executed plan `ju3rhs` (Set `setdispgate`, `From-Backlog: fv4b6s`), which put `attention_contract.validate_gate_flags` into `status_set.validate_transition_allowed` for both specs and backlog and pinned eight surfaces in `tests/test_gate_pair_validation_parity.py` (12 passed at review). The F-01 fix is ALSO carried outside this Set, by `wdyz5n` (`approved`, `From-Backlog: h4fiwa`, `- Item-Dependencies: none`), which will likely execute before this plan. Both carrier items, `h4fiwa` and `fv4b6s`, are `graduated` to those plans. So THIS PLAN CONSUMES AND PINS rather than re-implementing whatever has already landed, which is the rule orchestrator `63zo2f` OQ-02 and both `setdispgate` plans already state ("whichever executes second must consume ... rather than add a second copy").

### Task group 1: the evidence gate

- [ ] E-01 FIRST, CHECK WHETHER `wdyz5n` IS IN `.aw/records/plans/executed/`. IF IT IS, perform no production edit for this item: re-measure the positional and `--status` spellings (the three cases in the expected outcome) and record that `wdyz5n` installed the refusal; this item is then `performed` as a confirmation. IF IT IS NOT, implement as follows, and note in the evidence that `wdyz5n` must then consume this branch (and that the untyped `aw set implemented <id6>` surface stays unsatisfiable until `wdyz5n` E-02 registers `--evidence` on `aw set`, which is not this plan's scope). Make the `implementing -> implemented` evidence requirement fire on the POSITIONAL spelling, by having `status_set.validate_transition_allowed` consume the same authority-table condition and the same resolvability predicate that `specs.run_set` already consumes. `specs.run_set` reads `auth.get("evidence")` and then requires `_evidence_resolvable(path, ev)`; `status_set.validate_transition_allowed` consults the same authority table for other conditions but has NO evidence branch at all.

    CONSUME THE EXISTING PREDICATE; DO NOT WRITE A SECOND ONE. This is the whole point of the Set: the three prior instances of this class were each fixed by duplicating the behavior, and that is why a fourth and fifth exist. `specs._evidence_resolvable` is the predicate; make it reachable (it is module-private today) and call it. The precedent is exact and is documented in `specs.run_set`'s own comments: the `->reviewed` attestation and the `approved` gate are BOTH reached from both spellings by consuming one shared predicate, each with a comment stating that "a gate installed in only one of them is bypassed by choosing the other spelling".

    THE REFUSAL MUST BE BYTE-COMPATIBLE IN SUBSTANCE, NOT NECESSARILY IN PREFIX. `specs.run_set` writes `aw specs set: implementing -> implemented requires a resolvable --evidence citation (an existing .agents/plans/executed/ IPD path); refused.` The shared engine serves four verbs, so its prefix differs; preserve the REASON text and the exit code 1, and keep the refusal WRITE-NOTHING (the file must not move and must not be rewritten).

    NOTE THE STALE PATH IN THAT MESSAGE AND DO NOT PROPAGATE IT BLINDLY: it names `.agents/plans/executed/`, the pre-`.aw/` layout. Check what `_evidence_resolvable` actually accepts before copying the wording; if the predicate accepts `.aw/records/plans/executed/` while the message names the old path, the message is a second, smaller defect. Fix the wording only if the predicate's behavior proves it wrong, state which, and do not change the predicate's acceptance set here (that would be a contract change needing its own review).
  - Depends on: none
  - Expected outcome: `aw specs set implemented <id6>` with no `--evidence` exits 1 and leaves the spec in `implementing/` byte-identical; with an `--evidence` citation that does not resolve, exits 1 and writes nothing; with a resolvable citation, exits 0 and relocates the file; `aw specs set <path> --status implemented` behaves identically in all three cases; and the evidence states which plan (`wdyz5n` or this one) installed the refusal, with exactly one implementation of it.
  - Execution state: pending

### Task group 2: the deferred gate validation

- [ ] E-02 CONFIRM, DO NOT RE-IMPLEMENT: executed plan `ju3rhs` already installed this refusal in the shared engine (`status_set.validate_transition_allowed` calls `attention_contract.validate_gate_flags`, which checks kind membership, `validate_gate_ref` and a safe `--gate-summary`) and already extended it to `backlog` (OQ-02, resolved). Perform NO production edit for this item. Re-measure the four cases in the expected outcome on both spellings and record the result; if any case does NOT refuse, that is a regression of `ju3rhs` to report with its evidence and fix here by consuming `validate_gate_flags`, never by a second copy. The original authoring text follows for context. Make the `deferred` gate-pair VALIDATION fire on the POSITIONAL spelling. `specs.run_set` refuses unless the kind is in `attention_contract.GATE_KINDS` AND `attention_contract.validate_gate_ref(gk, gr)` passes, and separately refuses an unsafe `--gate-summary`. The shared engine's gate handling clears and writes the gate fields via its status-to-gate map but validates NEITHER the kind nor the ref shape.

    VALIDATE IN THE SHARED ENGINE, not in a per-verb wrapper, because the engine is what WRITES the fields. A wrapper that validates before delegating leaves the engine still capable of writing an invalid gate for any future caller, which is the same unreachable-fix shape as `43p53n`.

    THE VALIDATION IS TYPE-SCOPED AND THAT SCOPING MUST BE DELIBERATE, NOT INCIDENTAL. The engine serves plans, specs, backlog items and prompts, and its gate handling is driven by a per-type status map; `backlog` also has a gated status with a typed gate pair. Check whether `backlog.run_set` already validates its own gate pair before deciding whether this validation applies to backlog too: if backlog ALREADY refuses an invalid kind, extending the shared validation to it is behavior-preserving and correct; if it does NOT, then extending it is a THIRD bug fix that this plan has not measured and must not smuggle in. Measure it, state the answer, and if backlog turns out to have the same hole, FILE IT as its own carrier rather than fixing it here.

    THE UNSAFE-`--gate-summary` REFUSAL IS PART OF THE SAME GATE and must come with it, since the shared engine writes `Gate-Summary` while `backlog.run_set` does not handle that field at all.
  - Depends on: none
  - Expected outcome: `aw specs set deferred <id6> --gate-kind bogus-kind --gate-ref x` exits 1, the spec does not move, and no `Gate-Kind`/`Gate-Ref` line is written; the same call with a VALID kind and ref exits 0, relocates the spec, and writes both fields; an unsafe `--gate-summary` is refused on both spellings; and no production line changed for this item (the `ju3rhs` refusal consumed as is). `backlog` already validates (OQ-02).
  - Execution state: pending

### Task group 3: pin both refusals on both spellings

- [ ] E-03 Author `tests/test_specs_set_gate_parity.py` pinning BOTH refusals on BOTH spellings. Every test drives a CLI surface via `cli.main` and asserts on the exit code, the file's LOCATION, and the file's CONTENT; none may read production source with `inspect`/`ast`/regex, count callers, or assert docstring text (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). Pass `--no-commit` on every invocation.

    For the EVIDENCE gate, cover on each spelling: (a) no `--evidence` refuses, rc 1, file unchanged AND still in `implementing/`; (b) an unresolvable `--evidence` refuses identically; (c) a RESOLVABLE `--evidence` succeeds and relocates. Case (c) is not optional: without it, a "fix" that refuses unconditionally would pass (a) and (b) while breaking the verb entirely, and that is the single likeliest way to get this wrong.

    For the DEFERRED gate, DO NOT RE-AUTHOR cases already pinned by `tests/test_gate_pair_validation_parity.py` (from `ju3rhs`; its `test_surface_1_specs_set_flag_deferred` and `test_surface_2_specs_set_positional_deferred` already drive `bogus-kind` on both spellings and assert nothing written). Add to the new module ONLY the cases that file does not already cover, from: (d) an out-of-vocabulary `--gate-kind` refuses, rc 1, no gate field written, file not moved; (e) a malformed `--gate-ref` for a valid kind refuses; (f) a valid pair succeeds and writes both fields; (g) an unsafe `--gate-summary` refuses. Read that file first and state per case whether it is covered there (cite the test) or added here.

    ASSERT THE ABSENCE OF THE WRITE, NOT ONLY THE EXIT CODE. The measured defect in `fv4b6s` is that a file ON DISK ends up carrying `- Gate-Kind: bogus-kind`; a test that checks only `rc == 1` would pass against a half-fix that refuses after writing. Read the file back and assert the gate lines are absent and the status directory is unchanged.
  - Depends on: E-01, E-02
  - Expected outcome: a new module whose evidence cases (a)-(c), and whichever deferred cases (d)-(g) are not already covered by `tests/test_gate_pair_validation_parity.py`, pass on BOTH spellings, with every refusal case asserting the file's content and location as well as the exit code. Base-commit sensitivity: if this plan implemented E-01, cases (a) and (b) demonstrably FAIL on the base commit for the positional spelling, with the output pasted; if `wdyz5n` implemented it, demonstrate sensitivity instead by temporarily reverting that refusal in a throwaway edit (reverted before commit, `git status` clean afterwards) and pasting the failure. Case (d) is NOT demanded to fail on base, because `ju3rhs` already closed it at the base this plan executes on.
  - Execution state: pending

- [ ] E-04 Confirm the existing specs coverage still passes and that no test PINNED the bypass as correct behavior. Run `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_specs_from_backlog.py`, `tests/test_spec_review_attestation.py` and `tests/test_status_set.py` individually and paste each result.

    THE SPECIFIC RISK THIS ITEM EXISTS TO CATCH: a test that drives the positional spelling to reach `implemented` as a FIXTURE STEP, rather than as the behavior under test. Such a test passes today because the gate does not fire, and E-01 breaks it. That is NOT a regression, and the correct repair is to give the fixture a resolvable `--evidence` citation (or to construct the `implemented` state directly), never to weaken the gate. If one is found, repair it that way and say so explicitly in the evidence; a fixture that needs a gate disabled is telling you the fixture is wrong, not the gate.
  - Depends on: E-01, E-02
  - Expected outcome: each named module's result pasted; any test broken by the newly-firing gates identified by name, repaired by supplying legitimate evidence or constructing the state directly, with the repair described and justified; no gate weakened to make a test pass.
  - Execution state: pending

### Task group 4: close the carriers and record the fix

- [ ] E-05 CORRECTED AT REVIEW: BOTH CARRIERS ARE `graduated` TO OTHER PLANS (`h4fiwa` to `wdyz5n`, `fv4b6s` to `ju3rhs`), which carry their `From-Backlog` gates, so the HANDOFF route closes them when those plans execute, and THIS PLAN DOES NOT CLOSE EITHER unless the corresponding carrier plan was retired to `superseded/` without executing (in which case use the SATISFIED route below, citing this plan's executed path). Record each item's `- Status:` read back and which route applies. Likewise add a `CHANGELOG.md` entry ONLY for a refusal no existing entry describes: `ju3rhs` already wrote the gate-kind entry ("`aw specs set`, `aw backlog set`, and `aw set` now refuse a Gate-Kind outside the documented vocabulary"), and `wdyz5n` declares `CHANGELOG.md` for the evidence refusal; if both entries exist, add none and say so. The original authoring text follows, and applies only in the superseded-carrier case. Both `h4fiwa` and `fv4b6s` carry `- Blocks-Release: next`, so closing them is GATED: `aw backlog set done <item>` fails closed unless the gate is provably preserved or released. Use the SATISFIED route, citing this plan's executed path: `aw backlog set done h4fiwa --evidence <this plan's executed path>` and the same for `fv4b6s`. Do NOT clear the gate with `--blocks-release -` (that releases a gate the fix actually satisfied, discarding the record that the release was blocked for a real reason), and do NOT hand-edit either item.

    THE ORDER MATTERS AND IT IS NOT NEGOTIABLE: the evidence citation must resolve, so this item runs only after the plan has moved to `.aw/records/plans/executed/`. If the transition has not happened yet, the close will refuse, which is correct behavior and not an obstacle to work around.

    The `CHANGELOG.md` entry describes the USER-VISIBLE effect of both fixes in the file's established voice: `aw specs set` now refuses to mark a spec implemented without a resolvable evidence citation, and refuses an invalid gate kind, whichever spelling is used. Name no private predicate, and write no em or en dashes (user-facing prose, `AGENTS.md`). This IS a behavior change a user can hit (a command that used to succeed now refuses), so it must be in the changelog; that is the difference between this child and child 01.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: each carrier's status and route recorded (HANDOFF via its executed carrier plan, or SATISFIED via this plan only if that carrier plan was superseded), never closed by clearing the gate; at most one new CHANGELOG entry, only for a refusal no existing entry describes, containing no em or en dash.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16, spec `wy9aru` S1). A gate is verified by DRIVING the verb and reading the exit code plus the file on disk, never by asserting that a call to a predicate appears in the source.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; `-n0` is forbidden and a second `-q` suppresses the `N passed` line this plan requires pasted.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane worktree it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` invocation so the lane's own code runs and the notice does not pollute pasted evidence.
- A release-blocking backlog item CANNOT be closed casually: `aw backlog set done` fails closed on an item carrying `- Blocks-Release:` unless the gate is HANDED OFF (a carrier plan with `- From-Backlog:` and the same gate, executed), SATISFIED (a resolvable in-tree `--evidence` citation), or explicitly DE-GATED. E-05 uses SATISFIED, which is why it must run after this plan is in `executed/`.
- `AGENTS.md` withholds the `implemented` spec status from an agent even where the transition table permits an executor. The gate this plan makes unbypassable is therefore enforcing an existing stated policy, not inventing one. Two pending plans in the tree (`uuh71v`, and the not-executed `mi4s9f`) explicitly stop short of `implemented` and PROPOSE the command for a maintainer, which is the behavior the gate assumes.
- `specs.run_set` carries comments at BOTH of its shared-predicate call sites stating the principle this plan applies: a gate in only one of the two forked paths "is bypassed by choosing the other". The fix shape is therefore established in the codebase, not invented here.

## Findings

Rows marked MEASURED were reproduced by driving the real surfaces in scratch git repositories at HEAD `ec857565a`, with the fixture reset between spellings.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH (MEASURED) | Identical `implementing` spec fixture. `aw specs set <path> --status implemented` -> rc 1, stderr `aw specs set: implementing -> implemented requires a resolvable --evidence citation (an existing .agents/plans/executed/ IPD path); refused.`, file still at `specs/implementing/...`. `aw specs set implemented abc123` -> rc 0, stdout `implementing -> implemented`, file now at `specs/implemented/...`. | **A POLICY GATE IS DEFEATED BY CHOOSING THE SHORTER SPELLING.** `AGENTS.md` states an agent "may NOT set `implemented` (needs cited evidence)". `specs.run_set` enforces it via `auth.get("evidence")` plus `_evidence_resolvable`; `status_set.validate_transition_allowed` has no evidence branch. The asymmetry favors the bypass: the positional spelling is shorter and is what the repository's own docs use elsewhere. Filed `h4fiwa` (release-gated). |
| F-02 | MEDIUM (MEASURED) | Identical `approved` spec fixture, invalid kind. `--status deferred --gate-kind bogus-kind --gate-ref x` -> rc 1, `deferred requires a valid --gate-kind and --gate-ref`, nothing written. Positional, same arguments -> rc 0, file at `specs/deferred/...` carrying `- Gate-Kind: bogus-kind` and `- Gate-Ref: x`. | **THE POSITIONAL PATH WRITES A GATE OUTSIDE THE VOCABULARY, TURNING A FAIL-CLOSED REFUSAL INTO AN AT-REST FINDING.** `specs.run_set` validates kind membership and ref shape; the shared engine's gate handling only clears and writes. The window between writing the invalid record and someone running the checker is unbounded. Filed `fv4b6s` (release-gated). RE-MEASURED AT REVIEW 2026-10-07: CLOSED by executed plan `ju3rhs`; the positional spelling now refuses and writes nothing. |
| F-03 | MEDIUM (STALE MESSAGE) | The refusal text in F-01 names `.agents/plans/executed/`, which is the PRE-`.aw/` layout path. The repository's plans live under `.aw/records/plans/executed/`. | **THE EXISTING REFUSAL MESSAGE MAY NAME A PATH THAT NO LONGER EXISTS**, which would make a correct refusal unactionable: a user told to cite `.agents/plans/executed/...` cannot, because that directory is gone. E-01 requires checking what `_evidence_resolvable` ACCEPTS before copying the wording, and fixing the message only if the predicate proves it wrong. Do not change the predicate's acceptance set, which would be a contract change. |
| F-04 | MEDIUM (FIX SHAPE ALREADY ESTABLISHED) | `specs.run_set` contains two comments at its shared-predicate call sites stating that this function "is a FORK of `status_set`'s path reached by the `--status` spelling" and that "a gate installed in only one of them is bypassed by choosing the other spelling, so the SAME shared predicate is consumed here rather than a second copy of the logic". | **THE CODEBASE ALREADY KNOWS THE RULE AND ALREADY APPLIES IT TWICE; THESE TWO GATES ARE WHERE IT WAS NOT APPLIED.** The `->reviewed` attestation and the `approved` gate are both reached from both spellings through one predicate. So this plan's fix is the established pattern extended to two more gates, not a new approach, and any reviewer can check it against two in-tree examples. |
| F-05 | MEDIUM (TEST RISK) | `tests/test_specs_verbs.py` makes thirteen direct `specs.run_set` calls, and `tests/test_specs_status_dirs.py`, `tests/test_specs_from_backlog.py` and `tests/test_spec_review_attestation.py` drive specs transitions extensively. | **A TEST MAY REACH `implemented` THROUGH THE POSITIONAL SPELLING AS A FIXTURE STEP**, which passes today only because the gate does not fire. E-01 would break it, and the break is CORRECT. E-04 exists to find such a test and repair it by supplying legitimate evidence, never by weakening the gate. Recorded explicitly because "a test broke, so loosen the change" is the tempting and wrong response. |
| F-06 | LOW (SCOPE BOUNDARY) | `specs.run_set` also performs a post-write `validate_spec` conformance refusal (in-memory, byte-identical refusal) that the shared engine does not. | **A THIRD `specs.run_set`-ONLY REFUSAL EXISTS AND IS DELIBERATELY NOT FIXED HERE.** It is a different shape: the other two are PRE-write gates on specific transitions, while this one re-validates the whole rendered result. Folding it in would widen a measured two-bug fix into an unmeasured three-bug one. Carried by child 04, which moves the whole specs path. |
| F-07 | N/A (BASELINE) | `python3 -m pytest` at HEAD `ec857565a`: `3512 passed, 2 skipped, 3 warnings in 111.12s (0:01:51)`. | **THE BASE IS GREEN AT THIS HEAD, AND THAT IS TIME-DEPENDENT**: one existing cross-spelling test is red whenever the local and UTC dates differ (`2wae2x`). RE-DERIVE the baseline and compare failure SETS BY NAME, never against this count. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/status_set.py` + `agent_workflows/specs.py`: the shared engine consumes the existing evidence-resolvability predicate, so `implementing -> implemented` refuses without a resolvable citation on both spellings (E-01).
2. No production edit: confirm `ju3rhs`'s shared-engine `deferred` gate validation refuses on both spellings (E-02).
3. `tests/test_specs_set_gate_parity.py`: the evidence cases on both spellings, plus only those deferred cases `tests/test_gate_pair_validation_parity.py` does not already pin, every refusal case asserting content and location as well as exit code (E-03).
4. Existing specs test modules: any fixture that reached `implemented` through the bypass is repaired with legitimate evidence (E-04).
5. `CHANGELOG.md`: an entry only for a refusal no existing entry describes; carriers `h4fiwa`/`fv4b6s` close via HANDOFF through `wdyz5n`/`ju3rhs`, not here, unless a carrier plan was superseded (E-05).

## Deferred / out of scope (with reason)

- THE DISPATCH ROUTE IS NOT MOVED. Both engines still exist and `cli.main` still forks on `--status`. This child UNIONS two refusals across the fork rather than removing the fork, deliberately: the two bugs are release-gated and must be fixable NOW, while removing the fork is gated on spec `wy9aru` OQ-1, which is BLOCKING on a maintainer call about the sidecar. Shipping the gate fix behind that call would hold a release blocker hostage to a design question.
  - Carrier: 63zo2f
- THE THIRD `specs.run_set`-ONLY REFUSAL (the post-write `validate_spec` conformance check) IS NOT UNIONED HERE (F-06). It is a whole-result re-validation rather than a per-transition gate, it was not among the two measured bypasses, and folding it in would turn a measured fix into a partly speculative one.
  - Carrier: m94eht
- THE STALE `.agents/plans/executed/` PATH IN THE REFUSAL MESSAGE IS FIXED ONLY IF MEASUREMENT PROVES IT WRONG (F-03), and the predicate's ACCEPTANCE SET is not changed either way. Widening or narrowing what counts as resolvable evidence is a contract change about what satisfies a policy gate, and it deserves its own review rather than riding along inside a bypass fix.
  - Carrier-Declined: deliberately not filed in advance, because F-03 may prove the message correct; E-01 requires stating the measured answer, and filing a carrier then is cheap and better informed than filing one now for a defect that may not exist
- EVERY AXIS SPEC `wy9aru` SECTION 7 ASSIGNS ELSEWHERE is untouched: the clock, the history label, the dedup asymmetry, the sidecar order, the dead `apply` read, the defaulted message.
  - Carrier: wy9aru
- A BACKLOG GATE-VALIDATION HOLE, IF ONE EXISTS, IS FILED RATHER THAN FIXED. E-02 requires measuring whether `backlog.run_set` validates its own gate pair. If it does not, that is a third bug this plan has not measured and must not smuggle into a fix whose scope was reviewed around two.
  - Carrier-Declined: conditional on a measurement E-02 performs; the item requires filing a carrier at that moment if the hole is real, which is the honest sequence rather than pre-filing a speculative item

## Scope check

- Over-scope: none. Every declared path is edited by a numbered item: `agent_workflows/status_set.py` (E-01, E-02), `agent_workflows/specs.py` (E-01), `tests/test_specs_set_gate_parity.py` (E-03), `CHANGELOG.md` (E-05).
- Under-scope: E-04 may repair an existing test module (one of `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_specs_from_backlog.py`, `tests/test_spec_review_attestation.py`, `tests/test_status_set.py`) if the newly-firing gate breaks a fixture. Which, if any, is not knowable at authoring time (F-05 establishes the risk, not its target), so the path cannot be declared now. Declare the actual path during execution if the finalize scope reconciliation requires it and record the widening in the transition message; this note is the authorization. E-05 also writes to two backlog items under `.aw/records/backlog/`, whose paths ARE knowable (`h4fiwa`, `fv4b6s`) but which are closed through `aw backlog set`, a tooled lifecycle transition rather than a hand edit. The plan's own file needs no declaration (implicit lifecycle-artifact allowance, spec `ipd-structure-and-linting` Section 4.5).

## Required tests / validation

- The BARE suite: `python3 -m pytest`, with the `N passed` line pasted. RE-DERIVE the baseline before any edit and compare FAILURE SETS BY NAME, not counts (F-07).
- The new `tests/test_specs_set_gate_parity.py` run alone with `-o addopts=""`, every case named, plus the BASE-COMMIT demonstration that cases (a), (b) and (d) FAIL for the positional spelling before the fix (via `git stash` or a scratch checkout), with the failure output pasted.
- The five existing specs-related modules named in E-04, each run individually with its result pasted, and any repair justified in the evidence.
- A direct re-measurement of both original bypasses AFTER the fix, pasted: the exact commands from F-01 and F-02 must now refuse on both spellings, and the legitimate forms must still succeed.
- `AW_NO_REEXEC=1 aw specs check`, `AW_NO_REEXEC=1 aw backlog check` and `AW_NO_REEXEC=1 aw sanitize --agent`, each expected to exit 0.
- `AW_NO_REEXEC=1 aw check release-gates`, with its result pasted, since this plan closes two release-gated items.
- `AW_NO_REEXEC=1 aw check` and `AW_NO_REEXEC=1 aw attention --check`: BOTH exit 1 on PRE-EXISTING conditions unrelated to this plan, so the honest bar is an UNCHANGED FINDING SET plus the expected disappearance of the two closed carriers from the live blocker set. Re-derive before and after. Do not "fix" another plan's finding or another lane's state.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Verify the staged set against this plan's `Scope-Paths` before committing.

## Spec / documentation sync

Spec `wy9aru` (`to-review`) governs this Set and is NOT edited by this child. This plan implements its
Section 4.7 (refusals are UNIONED, never averaged) for the first two rows of that section's table, and
its AC-2 names these two bypasses explicitly as acceptance criteria. No requirement changes, so no
amendment is owed.

`AGENTS.md` already states both policies this plan makes enforceable (an agent "may NOT set
`implemented` (needs cited evidence)"; "A `deferred` spec MUST carry a typed gate"), so no
documentation change is needed: the code is being brought up to the documented contract, not the
reverse. `CHANGELOG.md` records the user-visible refusals (E-05).

## Open questions

### OQ-01: does `_evidence_resolvable` accept `.aw/records/plans/executed/` paths, making the refusal message's `.agents/plans/executed/` wording stale?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (2026-10-07 /plan-review)
- Resolution or deferral rationale: RESOLVED AT REVIEW: YES. `specs._evidence_resolvable` returns True when the resolved candidate contains `.agents/plans/executed` OR `.aw/records/plans/executed` (its final `return` line; docstring "Layout-aware: the executed-IPD tree is `.agents/plans/executed/` (legacy) or `.aw/records/plans/executed/`"). So the refusal message in `specs.run_set` ("an existing .agents/plans/executed/ IPD path") is STALE wording, a small second defect: whichever plan installs the shared-engine refusal must word it as `.aw/records/plans/executed/` (naming the legacy path as also accepted is optional), without changing the acceptance set. Original rationale follows. F-03 establishes the message names a pre-`.aw/` path while the repository's plans live under `.aw/records/plans/executed/`. If the predicate accepts the current layout, the message is a second small defect and E-01 corrects the wording; if the predicate accepts only the old path, the GATE is broken in a larger way than this plan measured and that must be filed rather than fixed inline. Answerable by one direct call to the predicate at execution time. It cannot change this plan's design (the shared engine consumes the predicate either way), only whether a wording fix or a new carrier is owed.

### OQ-02: does `backlog.run_set` validate its own gate pair against the vocabulary, or does the backlog path share the hole E-02 fixes for specs?

- Blocking: no
- Status: resolved
- Owner: plan reviewer (2026-10-07 /plan-review)
- Resolution or deferral rationale: RESOLVED AT REVIEW: the backlog path is ALREADY validated in the shared engine by executed plan `ju3rhs` (its `- Scope-Paths:` includes `agent_workflows/backlog.py`, and `tests/test_gate_pair_validation_parity.py` surfaces 5 to 8 drive `bogus-kind` against `blocked` on the backlog spellings). No carrier is owed and E-02 performs no edit. Original rationale follows. E-02 places the gate validation in the SHARED engine, which serves backlog items too, so the answer decides whether that placement is behavior-preserving for backlog (if backlog already validates) or a third, unmeasured bug fix (if it does not). E-02 requires measuring it and FILING a carrier rather than fixing it inline if the hole is real, so either answer has a defined action and neither blocks. Resolve before E-02 and record the measurement.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted rc and stderr for `aw specs set implemented <id6>` with (a) no `--evidence`, (b) an unresolvable `--evidence`, (c) a resolvable `--evidence`, each with the spec's path read back afterwards proving it did or did not move; the same three for the `--status` spelling; and the answer to OQ-01 with the predicate call that produced it.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted rc and stderr for `aw specs set deferred <id6>` with an out-of-vocabulary `--gate-kind`, with a malformed `--gate-ref`, with an unsafe `--gate-summary`, and with a valid pair; for each refusal, the file read back showing NO `Gate-Kind`/`Gate-Ref` line and an unchanged status directory; the same set for the `--status` spelling; and a statement that no production line changed for E-02 (`git diff` of the plan's commits showing no gate-validation hunk), or, if a case failed, the regression evidence and the consume-only fix.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_specs_set_gate_parity.py -o addopts=""` output naming all cases as passed; plus, per E-03, either the base-commit run showing (a) and (b) FAILING for the positional spelling, or the throwaway-revert failure if `wdyz5n` installed the refusal; and the per-case table stating which of (d)-(g) were added here and which are covered by a named test in `tests/test_gate_pair_validation_parity.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted individual results for `tests/test_specs_verbs.py`, `tests/test_specs_status_dirs.py`, `tests/test_specs_from_backlog.py`, `tests/test_spec_review_attestation.py` and `tests/test_status_set.py`; plus, for any test the newly-firing gate broke, its name, the repair, and an explicit statement that the repair supplied legitimate evidence or constructed the state directly and did NOT weaken the gate.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: both items' `- Status:` and `- Blocks-Release:` lines read back, with the location of each carrier plan (`wdyz5n`, `ju3rhs`) and the route that applies; pasted `aw backlog set done ... --evidence` output ONLY for an item whose carrier plan was superseded; pasted `aw check release-gates` result; the existing CHANGELOG entries quoted, plus any new hunk diffed with a grep for em and en dashes returning nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before any
execution. It carries `- Blocks-Release: next` because it fixes two live bugs (`AGENTS.md`: we do not
ship known bugs), and it is NOT gated on spec `wy9aru`'s open questions: it unions two refusals across
the existing fork rather than removing the fork, so it can be reviewed, approved and executed while
OQ-1 awaits the maintainer. That independence is deliberate, so a release blocker is not held hostage
to a design question.

Execution contract (`AGENTS.md`): commit ONLY the files this plan changed, limited to its declared
`Scope-Paths` plus any E-04 repair declared at execution time, through `aw commit <plan> -- <paths>`;
never `git add -A`, never `-a`, never `--no-verify`, and never push. Paste ACTUAL runner output for
every test claim. Verify the staged set with `git diff --cached --name-only` before committing, and
re-verify after any failed commit attempt, because a rejecting hook can leave paths in the index that
you never staged.

Post-gate lifecycle: on completion, `aw ipd lint --phase pre-transition` must report conforming and
every `V-*` above must carry pasted evidence before the plan moves to
`.aw/records/plans/executed/`. Under `aw oc run` / `aw agy run` the runner performs `aw ipd begin` and
`aw ipd finalize`; by hand, transition with `aw ipd finalize m1jlwm --actor <agent/model> --message <...> --apply`,
never a hand-rolled `git mv`. The `- Scope-Paths:` list is a declaration for the finalize scope
reconciliation, not a stop condition: an out-of-scope edit (for example an E-04 fixture repair) is made and
justified with `--scope-reason`, and a declared path left untouched (likely `agent_workflows/specs.py` and
`CHANGELOG.md` if `wdyz5n` landed first) is acknowledged with `--scope-ack`. E-05's carrier closes, if any, run AFTER that move, because the evidence
citation must resolve. Do not set the backlog item `fcnz1r` to any status: the orchestrator `63zo2f`
owns its disposition.
