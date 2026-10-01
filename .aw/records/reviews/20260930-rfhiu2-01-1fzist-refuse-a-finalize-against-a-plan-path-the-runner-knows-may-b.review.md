# Review: Refuse a finalize against a plan path the runner knows may be stale

- Subject-Id: 1fzist
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `62b18f47` by importing the shipped modules and driving the real
predicates against temporary git repositories, including a real `git worktree` pair. The target plan
was committed and unchanged before review, so the pre-review snapshot was correctly skipped per
Step 1. Structural preflight `aw ipd lint --phase author` reported `conforming` before review and
`--phase review-finalize` reported `conforming` after the revisions.

THE PLAN'S THESIS IS CORRECT AND ITS MEASUREMENTS REPRODUCE. I re-ran every finding rather than
reading them. F-1 reproduces (`finalize_precheck` raises `FileNotFoundError`, and
`issubclass(FileNotFoundError, runner_shared.DriverError)` is `False` because `DriverError` extends
`RuntimeError`). F-2 reproduces by AST: the enclosing `try` at `runner_shared.py` lines 31675-34718
has ZERO `except` handlers and only a `finally`, both hosts' `run_queue` handle exactly
`ToolIdentityError`/`KeyboardInterrupt`/`StopNowForce`/`StopAtCheckpoint`/`DriverError` around
`execute_item`, and each `main` ends `except Exception as exc: print(...); raise`; driving
`finalize_with_contention_retry` against a nonexistent path propagated `FileNotFoundError`. F-3
reproduces on a real lane. F-4 reproduces exactly as written (`finalize_outcome(rc=1)` returns `0`
with "the terminal transition already succeeded", control `pending/` returns `1`). F-7's five-site
count reproduces by AST at lines 31463, 31516, 31550, 33951, 34437. F-9 reproduces (zero test
matches; `tests/test_finidem_double_finalize.py` does not exist). The `Work-Kind: bug`
reclassification is justified on the item's own second trigger, and `Blocks-Release: next` follows
from the repository's every-live-bug rule.

THE DOMINANT FINDING IS THAT THE PLAN'S OWN FIX WAS INCOMPLETE, and it is incomplete in the
direction that matters most: E-04 proposed an EXISTENCE check on `finalize_already_done`, and an
existence check does not touch the false-success shape the runner actually produces. Measured on a
real `git worktree` lane branched before the plan existed, with main's copy in `executed/`: the
substituted path EXISTS, `finalize_already_done(lane, mainpath)` is `True`, and
`finalize_outcome(lane, mainpath, 1, "refused")` returns `0`. The plan would therefore have shipped
a guard that passes its own test, closes the minor ghost-path shape, and leaves the default lane
geometry wide open. PR-001 adds the containment requirement and the controls that keep the
legitimate `finidem` no-op from regressing. This is the one finding that would have cost a second
plan had it shipped as written.

TWO SMALLER CORRECTIONS OF FACT, both measured. The plan asserted `wtiso_gate` is a caller of
`finalize_precheck`; it is not (its only `ipd_lifecycle` call is `_scope_match`, and its own
docstring records that `check_scope` has zero product callers deliberately). And the plan presented
the `FileNotFoundError` crash as unguarded, where `ipd_lifecycle.finalize` already carries
`if not plan_path.is_file(): return FinalizeResult(EXIT_CANNOT_RUN, ...)` before its precheck call.
Neither weakens the fix: the direct callers (`compute_scope_reconciliation`,
`record_item_spec_edits`) bypass `finalize`'s guard entirely, which is the route F-2 measured. Both
are recorded so a later reader is not sent looking for a regression that cannot exist, and so E-05
reuses the existing message wording rather than minting a third phrasing for one fact.

ONE DURABILITY HAZARD THE PLAN DID NOT SEE. `render_stream.record_refusal` writes a SINGLE slot and
a later call replaces it wholesale (driven at review: recording the new code then
`TURN_RETRY_REFUSAL_CODE` leaves `refusal_of_item(item).code == "turn-retry"`), and
`handle_turn_failure_retry` runs for every execute turn AFTER both finalize arms. E-02's refusal is
therefore not durable by construction, and the plan's evidence requirement would have been
satisfied by an assertion made at the arm that proves nothing about what a human later reads.
PR-004 moves the assertion to end-of-turn and names the in-fence lever if it does not survive.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Correctness; E. Testing | `agent_workflows/runner_shared.py` `finalize_already_done`; `ipd_lifecycle.plan_already_finalized`; plan E-04 | E-04's EXISTENCE check misses the DOMINANT false-success shape. Measured on a real `git worktree` pair: the substituted path EXISTS in main while `repo` is the lane, `finalize_already_done(lane, mainpath) -> True`, `finalize_outcome(lane, mainpath, 1, "refused") -> 0`. An existence-only guard closes the ghost-path case F-4 measured and leaves the runner's DEFAULT lane geometry open, while passing the plan's own test. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-04 now requires EXISTENCE **and** CONTAINMENT in `repo`, implemented with the `relative_to`-in-a-`try` shape `_repo_relative` already uses. Added F-10 with the measurement and the same-tree control. E-06 row (b) split into (b1) ghost and (b2) wrong-tree-on-a-real-worktree, each red-then-green, plus two controls green at both points. V-04 demands the before/after pair for the wrong-tree case and the non-normalized-spelling control. Gate prose now names the strand-your-own-work risk if containment is implemented against the wrong tree. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness; C. Architecture | plan E-02 "Choose the disposition from the EXISTING vocabulary"; `runner_shared.TURN_RETRY_CLASSIFICATION`; `turn_failure_is_retryable` | E-02 left the disposition token to the executor while only forbidding a NOVEL one. The two plausible existing tokens are not equivalent: `partial`'s recorded non-retryable reason is about a turn that RAN and fell short and explicitly names plan `dy9ymn` as its future owner, so a later widening of `partial` would start re-dispatching an item whose plan the runner cannot locate; `fail-gate`'s reason describes this fact exactly. Both are non-retryable TODAY, so the hazard is latent rather than live. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now mandates `fail-gate`, with the reasoning against `partial` required in the code comment. Added a Project-conventions bullet recording that the disposition vocabulary is closed and each token carries a recorded retry verdict. V-02 now requires `turn_failure_is_retryable`'s answer for the chosen token to be pasted. |
| PR-003 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | `agent_workflows/wtiso_gate.py` (AST: only `ipd_lifecycle._scope_match` is called); plan E-05 | E-05 claimed `wtiso_gate` is a caller of `finalize_precheck`. It is not. The module delegates the scope MATCHER, and its `check_scope` is documented as having ZERO product callers deliberately. The real callers are `runner_shared.compute_scope_reconciliation`, `record_item_spec_edits`, and `ipd_lifecycle.finalize`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05's caller list corrected to the three real callers. Added F-12 recording the measurement and why no `wtiso_gate` regression can exist, so a reader does not go looking for one. |
| PR-004 | MEDIUM | UNDER-SCOPE | A. Correctness; E. Testing | `render_stream.record_refusal` (single `REFUSAL_KEY` assignment); `runner_shared.handle_turn_failure_retry`; plan E-02/E-06 | E-02's refusal is NOT durable: `record_refusal` writes one slot and a later call replaces it (driven at review: the new code is displaced by `turn-retry`), and `handle_turn_failure_retry` runs after both finalize arms for every execute turn. The plan's evidence requirement could be satisfied by an assertion at the arm, which proves nothing about what a human later reads in `aw runs`. | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | E-02 now requires the refusal to survive to END OF TURN and names the in-fence lever (`turn_failure_is_retryable`'s existing `finalize_refusal` early-out). E-06 row (a) and V-02 now assert after `execute_item_core` RETURNS. Added F-11 with the measurement, and a Deferred entry declining to convert the slot into a list with the reason stated. |
| PR-005 | LOW | IN-SCOPE | Step 1 evidence accuracy | `ipd_lifecycle.finalize` `if not plan_path.is_file(): return FinalizeResult(EXIT_CANNOT_RUN, None, f"plan file not found: {plan_path}")` | The plan presented the missing-plan crash as unguarded. `finalize` already guards it one layer above `finalize_precheck`. This does not weaken E-05 (the direct callers bypass `finalize` entirely, which is the route F-2 measured), but leaving it unstated overstates the defect and invites E-05 to mint a third message wording for a fact the tree already phrases twice. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 with the measurement and the reason E-05 is still required. E-05 now reuses `finalize`'s existing `plan file not found:` wording and `begin`'s unreadable-case wording rather than inventing one. V-05 additionally requires the `finalize_with_contention_retry` before/after pair, which is the route the guard above does not cover. |
| PR-006 | LOW | IN-SCOPE | G. Plan executability | plan gate "ONE EXECUTION HAZARD IS WORTH NAMING" | The gate cited only `driver_finalize`'s import pin as the boundary keeping the lane's in-progress edits out of their own gate. That pin covers the `aw ipd finalize` SUBPROCESS, so it protects E-05 but says nothing about E-02 and E-04, which run in the COORDINATOR process. The gate also omitted E-04 from the list of items on the self-finalize path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to name BOTH boundaries and which item each protects, to include E-04, and to add E-04's specific strand-your-own-work risk with the controls V-04 demands against it. |
| PR-007 | LOW | IN-SCOPE | G. Plan executability (scope fence) | plan Scope check, Under-scope clause | The under-scope clause ended "stop and report rather than broadening scope", which contradicts the 2026-09-01 maintainer ruling that an out-of-scope edit is to be MADE and then JUSTIFIED (a fence is a declaration, and `aw ipd finalize` already refuses without a `--scope-reason` per out-of-scope path). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Clause now instructs the executor to make the edit and justify it with a `--scope-reason`, and names `agent_workflows/render_stream.py` as the one path a legitimate PR-004 remedy might require. Candidate list extended to cover `render_stream.py` and `plan_already_finalized`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should E-04's guard be existence-only (as authored), containment-only, or both? | BOTH, with containment judged against `repo` by `resolve()`+`relative_to` in a `try`. | Existence-only, rejected because it leaves the dominant wrong-tree shape open (measured). Containment-only, rejected because the ghost-path shape F-4 measured is real and a ghost inside `repo` would still pass. Teaching `plan_bucket` to do IO, rejected outright. Changing `plan_already_finalized`, rejected because it receives no notion of the caller's tree and its `executed/`-without-commit tolerance is the measured `finidem` incident's own shape. | Measured on a real `git worktree` pair at HEAD `62b18f47`: existing+uncontained path yields `finalize_already_done -> True`, `finalize_outcome(rc=1) -> 0`; the same-tree control yields `0` and must stay `0`. `runner_shared.plan_bucket` docstring ("does no IO and must not learn to"); `ipd_lifecycle.plan_already_finalized` docstring. | yes |
| D-2 | Which existing disposition token should E-02 write, given the plan only forbade a novel one? | `fail-gate`. | `partial` (the verify-side twin's token), rejected because its recorded non-retryable reason describes a turn that RAN and fell short and names plan `dy9ymn` as future owner, so a later widening would re-dispatch an item whose plan cannot be located. Minting a new token, already forbidden by the plan and by `run_viewer`'s bare-dash rendering. | `runner_shared.TURN_RETRY_CLASSIFICATION` rows for `fail-gate` ("lifecycle gate or clean-base gate refused; not a host failure to retry without human action") and `partial`; driven at review, both return non-retryable today. `TERMINAL_STATES` contains `fail-gate`. | yes |
| D-3 | Is PR-004's single-slot refusal overwrite a defect to file, or a constraint to work within? | A constraint to work within; no item filed. | Filing a backlog item to make the slot a list, rejected: `record_refusal` documents itself as THE ONE WRITER paired with ONE reader precisely so they cannot drift, and a list changes what every consumer reads (including `run_viewer.step_refusal`) for a benefit this plan does not need, since the LAST refusal is the operative one for a human deciding what to do next. | `render_stream.record_refusal` (unconditional single-key assignment) and its docstring; `runner_shared.turn_failure_is_retryable`'s existing early-out for an item carrying `finalize_refusal`, which is the in-fence lever. | yes |
| D-4 | Does `_repo_relative`'s absolute-path fallback (F-3) need its own carrier? | No carrier; recorded as a declined deferral naming what was and was not measured. | Filing an item to make `_repo_relative` refuse, rejected because E-04's containment guard closes the one measured consumer, and `_repo_relative` is called throughout the lifecycle module where a refusal would change every scope comparison. Silently omitting it, rejected as the review did measure the edge. | `ipd_lifecycle._repo_relative` (returns `path.resolve().as_posix()` on `ValueError`); measured at review that `_is_implicitly_allowed` also answers True for an absolute `plan_rel`. | yes |
| D-5 | Does OQ-01 (historical occurrence count) block, given `.aw/records/runs/` is absent from the lane? | Non-blocking; left `open` with `Owner: maintainer` as authored. | Converting it to a blocking question, rejected because `IPD-Q501` would then refuse the plan at every checkpoint for a measurement that changes no E-item. Resolving it myself, impossible: confirmed `.aw/records/runs` does not exist in this lane and `.aw/.gitignore:14` matches `records/runs/`. | `.aw/.gitignore:14`; `ls .aw/records/runs` -> No such file or directory. Maintainer ruling 2026-09-10 (plan `qhy3i3` OQ-01): a non-blocking open question does not make a plan NO-GO. The item's second reclassification trigger is independently satisfied by F-1..F-4. | yes |
| D-6 | Is `Kind: child` on a lone `-01` plan with no `-00` parent a finding? | Not a finding. | Flagging it as a missing orchestrator, rejected after measuring the population. | Surveyed every `20260930-*-01-*.ipd.md` in `pending/`: all carry `Kind: child` and a single-member Set. A single-child Set needs no orchestrator, and the repository norm confirms it. | yes |

No `Reversible: no` decisions were made, so no escalation was required under the irreversible-decision
rule. No finding was left `OPEN` or `DEFERRED` at or above the `HIGH` gate threshold, so no
`- Blocking: yes` escalation question was added to the plan.
