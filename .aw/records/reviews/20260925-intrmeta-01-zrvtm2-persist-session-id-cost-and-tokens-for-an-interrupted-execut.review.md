# Review: Persist session id, cost and tokens for an interrupted execute attempt

- Subject-Id: zrvtm2
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2d4eb94b`, in the review sweep lane. The plan cites HEAD `8e74dcac`, an ancestor; every
claim was re-checked against the current tree by CONTENT rather than by the plan's line offsets, and all
of them hold. The target plan was committed and unchanged (the lane's rev-2 materialized copy is
byte-identical to the tracked file), so the pre-review snapshot was correctly skipped per Step 1.
Structural preflight `aw ipd lint --phase author --agent` reported `clean` with one advisory
(`IPD-Z602`, E-01 bundling three clauses) before review; `--phase review-finalize --agent` reports
`clean` with ZERO findings afterwards, the advisory resolved by the E-01/E-02 split.

THE DIAGNOSIS IS CORRECT AND THE FIX IS THE RIGHT SHAPE. I re-reproduced the defect rather than
trusting F-2, and I widened the reproduction to all FOUR interrupt paths by driving the real
`oc_runipd.execute_item` with a spawn that writes a `ses_probe1` / `cost 2.17` log and then raises. Every
path ends with `session_id=None cost=None tokens=None set_sessions={}` while the SAME log yields
`ses_probe1` and `(2.17, {'total': 125, ...})`, and the rendered summary table prints `$0.00` and `-`.
The statuses differ per path in a way the plan did not record and a test would have tripped over:
`StallTimeout` -> `interrupted`, `StopNowForce` -> `unknown_outcome`, `StopAtCheckpoint` -> `interrupted`,
`KeyboardInterrupt` -> `running` with the exception propagating. The plan's central premise also holds and
is what makes the fix possible at all: `attempt["log"]` is written at attempt CREATION, in the attempt
dict literal, not in the post-spawn `attempt.update({...})`, so every handler already has the path it
needs.

PR-101 IS THE ONE THAT WOULD HAVE CHANGED RUNTIME BEHAVIOR NOBODY ASKED TO CHANGE. E-01 instructed the
helper to bump `session_turn_counts` by 1, reasoning that "the turn DID consume a slot". That counter is
not bookkeeping: it is the session-ROTATION trigger, read as `session_turns >= max_items` in
`execute_item_core` and again in `oc_runipd.run_opencode`, where exceeding it sets `is_rotation` and
DISCARDS the resumable session. So bumping it on an interrupt means a killed turn can push a session over
its rotation threshold and cause the very next resume to start fresh, which is the opposite of what
`hyit04` asks for: the item's whole complaint is that an interrupted turn's session is not reusable. The
plan cited `reconcile_interrupted` as its precedent for the drift rule, and that function is also the
precedent AGAINST the bump, because it writes `set_sessions`, `state["session_id"]` and the attempt's
`session_id` and deliberately does not touch the counter. I removed the bump and made its absence a
required, separately verified property (V-02), because a diff summary will not show it and a later reader
could reasonably re-add it as an oversight.

PR-102 IS THE ERROR AN EXECUTOR WOULD HAVE HIT IN THE FIRST MINUTE. E-04 required asserting that
"`runner_shared.render_continuation_hint(...)` output (called with the host's `labels`)" contains
`ses_probe1`. The real signature is `(state, run_dir, driver_cmd=None, *, labels)`: `run_dir` is a
REQUIRED POSITIONAL argument and `labels` is keyword-only. I did not deduce this, I hit the
`TypeError: render_continuation_hint() missing 1 required keyword-only argument: 'labels'` while
reproducing the defect. The failure mode that matters is the recovery: the natural response to a
signature error inside a validation item is to drop the assertion, which would remove the only check that
the operator-visible continuity hint actually names the recovered session, i.e. the exact user-facing
symptom `hyit04` filed.

PR-103 TURNED A HEDGE INTO A TEST. E-04 said `StopAtCheckpoint` would be exercised "only if a
`CheckpointObserver` can be built without a live stream; otherwise it is covered by E-02's grep". A grep
is not coverage of an interrupt path, and the hedge was unnecessary: `CheckpointObserver` needs only a
`detector` callable, so `CheckpointObserver(detector=lambda s: False, last_checkpoint_label="E-01")`
builds and `StopAtCheckpoint(observer)` raises cleanly. I drove the full path end to end and it
reproduces the defect exactly like the other three. So all four raises are behaviorally testable, the
test count rises from 6 to 8, and a grep substitute is now explicitly not acceptable.

PR-104 ADDS THE TEST FOR THE PLAN'S LOAD-BEARING SAFETY CLAIM. The entire justification for writing
`attempt["cost"]` is that readers prefer the stored field, so no surface double-counts. The plan asserted
this from a docstring and never tested it. I measured it: `run_viewer.extract_step_usage` reads
`att.get("cost")`/`att.get("tokens")` in an EXCLUSIVE `if/else` whose else-branch reads the log, and
driving it on one item with and without the stored fields returns byte-identical tuples
(`(2.17, {...'total': 125...}, 2.17, {...}, None, {})` both ways). That is a strong result and it deserves
a regression test, because the property is invisible in the diff this plan produces and a future refactor
turning that `if/else` into two additive branches would silently start inflating every run's reported
spend. E-05 now pins it.

PR-105 CORRECTS A DEFERRED REASON THAT WAS FACTUALLY FALSE, and the correction found a second defect. The
plan deferred verifier-turn interrupts because they "would need `verification_cost` / `verification_tokens`,
keys the success path itself does not write today ... so there is no success-path contract to mirror". The
verifier success path DOES write accounting: `attempt["verify_cost"]` and `attempt["verify_tokens"]` from
`extract_log_metrics(_v_log)`. So the contract exists and a verifier interrupt really does lose that
spend. Chasing the key names turned up F-7: `render_stream.render_run_summary_table` reads
`att.get("verification_cost")` and `att.get("verification_tokens")`, which NOTHING writes anywhere in the
package, while `verify_cost`/`verify_tokens` is the name every other consumer uses (`run_viewer`,
`run_analytics*`). Those two table reads are dead, so verifier spend reaches the summary table on no path
at all. That is out of scope here (`render_stream.py` is not declared, and the defect is independent of
interrupts), but it is now the STATED reason the deferral stands: fixing the verifier interrupt half while
the reader is misnamed would produce a correct ledger no table surfaces.

PR-106 SHARPENS THE DEPENDENCY FROM "should run after" TO "cannot run before", which matters because the
plan reads as though three of four call sites merely benefit from `87jnym`. Measured: `execute_item_core`
contains NO `except KeyboardInterrupt` whatsoever, and `reconcile_item_on_interrupt` has ZERO callers in
`agent_workflows/` or `tests/`. `87jnym` is `- Status: approved` and still sits in `pending/`, so it has
not executed. The declared `executed:87jnym` edge is well-formed and the runner enforces it
(`parse_item_dependencies("executed:87jnym")` yields one `ipd` edge), so the ordering is safe; what was
missing was an instruction for the case where an executor finds the handler absent anyway. E-03 now stops
and reports rather than adding the handler, which is `87jnym`'s own declared scope (clause (a)), and V-03
requires pasted evidence that the handler exists before this plan edits it.

PR-107 records that OQ-02's premise is not yet true. It asks whether a clean-tree `KeyboardInterrupt`
popping the attempt takes its spend with it. The pop is guarded by
`attempts[-1].get("attempt") == attempt_no`, and the attempt record's key is `"number"`, so the predicate
evaluates `None == 1` and the pop NEVER FIRES on current code. `87jnym` clause (c) is precisely "make the
no-changes arm's attempt pop match the attempt record's real `"number"` key", so the question becomes live
exactly when this plan's dependency lands. Left non-blocking and open for the maintainer, as filed, but
now with the mechanism stated so nobody answers it against code that does not behave that way yet.

Both backlog items are handled correctly on the gate: `hyit04` and `pfh5qa` are each `graduated` to this
Set with `- Blocks-Release: next`, and the plan inherits the gate. One honest wrinkle I recorded rather
than smoothed over: `- From-Backlog:` can name only one item, so `pfh5qa`'s eventual close rests on the
`--evidence` route rather than the handoff route. OQ-01's resolution I re-verified against `pfh5qa`'s own
text, which does say printing `$0.00` "is the one option that is not" defensible; resolving it as COUNT IT
is faithful to the item.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | A. Correctness / C. Architecture (an unrequested runtime behavior change) | `session_turns = state.get("session_turn_counts", {}).get(raw_session, 0)` then `if session_turns >= max_items: is_rotation = True; raw_session = None` in BOTH `execute_item_core` and `oc_runipd.run_opencode`; `reconcile_interrupted` writes `set_sessions`, `state["session_id"]` and the attempt's `session_id` and does NOT touch the counter | E-01 INSTRUCTED A `session_turn_counts` BUMP, WHICH WOULD DEFEAT THE VERY ITEM THIS PLAN FIXES. That counter is the session-ROTATION trigger, not bookkeeping: exceeding `max_items` sets `is_rotation` and discards the resumable session. Bumping it on an interrupt lets a killed turn push a session over its threshold, so the next resume starts fresh, which is the opposite of `hyit04`'s request that an interrupted turn's session be reusable. The plan's own cited precedent, `reconcile_interrupted`, is the precedent AGAINST it. | C:Low; U:Low; S:Low; F:Medium-High (a resume silently losing the session the fix exists to recover); Overall:Low (removing one line) | FIXED | The bump is removed; E-02 states plainly that it must NOT be added and why, with the rotation read cited; E-04 case (1) asserts `session_turn_counts` is UNCHANGED; V-02 requires a pasted grep proving no bump, framed as a required property rather than an omission; a conventions bullet records the rotation semantics. |
| PR-102 | HIGH | IN-SCOPE | E. Testing (a validation that cannot run as written) | `inspect.signature(render_continuation_hint)` -> `(state, run_dir, driver_cmd=None, *, labels)`; calling it as the plan describes raised `TypeError: render_continuation_hint() missing 1 required keyword-only argument: 'labels'` at review | E-04 CALLS `render_continuation_hint` WITH A SIGNATURE THAT DOES NOT EXIST. It says "called with the host's `labels`", omitting the REQUIRED POSITIONAL `run_dir`; `labels` is additionally keyword-only. The error is immediate, which is the problem: the natural recovery from a `TypeError` inside a validation item is to drop the assertion, and that assertion is the only check that the operator-visible continuity hint actually names the recovered session, i.e. the exact symptom `hyit04` filed. | C:Low; U:Low; S:Low; F:Medium (dropping the only user-visible assertion); Overall:Low | FIXED | E-06 spells the call as `render_continuation_hint(state, run_dir, labels=<host labels>)` and states that the authored phrasing raises `TypeError`, hit at review; V-06 requires the hint output containing `ses_probe1`; a conventions bullet records both renderers' real signatures. |
| PR-103 | MEDIUM | IN-SCOPE | E. Testing (a grep offered as coverage of a behavior path) | `CheckpointObserver(detector=lambda s: False, last_checkpoint_label="E-01")` builds; `StopAtCheckpoint(observer)` raises `StopAtCheckpoint('level-None stop honored at safe checkpoint after event None (E-01)')`; driving it through the real `execute_item` reproduced the defect (`status=interrupted sid=None cost=None`) | E-04 HEDGED `StopAtCheckpoint` DOWN TO A GREP ON AN UNCHECKED ASSUMPTION. It said the path would be exercised only "if a `CheckpointObserver` can be built without a live stream; otherwise it is covered by E-02's grep". A grep that a call line exists is not evidence that the interrupt path writes the fields. The assumption is also false: the observer needs only a `detector` callable, so the path is fully testable and reproduces the defect like the other three. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 covers all FOUR raises with the exact constructor, raising the count from 6 to 8 tests; V-06 states a grep-only substitute for `StopAtCheckpoint` is NOT acceptable and cites the review construction; a conventions bullet records the constructor. |
| PR-104 | MEDIUM | UNDER-SCOPE | D. Anti-regression / E. Testing (the load-bearing safety claim was untested) | `run_viewer.extract_step_usage` reads `att.get("cost")`/`att.get("tokens")` in an exclusive `if ... else` whose else-branch reads `att.get("log")`; driven on one item, with and without the stored fields, it returned identical tuples `(2.17, {'total': 125, 'input': 100, 'output': 20, 'cache': 5}, 2.17, {...}, None, {})` | THE WHOLE FIX RESTS ON "READERS PREFER THE STORED FIELD, SO NOTHING DOUBLE-COUNTS", AND NO ITEM TESTED IT. The plan asserted it from a docstring. It is TRUE (I measured it), which makes it exactly the kind of invariant worth pinning: it is invisible in this plan's diff, and a future refactor turning that exclusive `if/else` into two additive branches would silently inflate every run's reported spend, with interrupted attempts counted twice. | C:Low; U:Low; S:Low; F:Medium (silent spend inflation on a later refactor); Overall:Low | FIXED | E-05 added: assert `extract_step_usage` returns EQUAL tuples for the log-only and log-plus-stored attempt shapes; V-05 requires both tuples pasted and rejects a prose claim; the conventions bullet records the measured exclusivity; the gate names it as one of three easily faked claims. |
| PR-105 | MEDIUM | IN-SCOPE | A. Correctness (a deferral resting on a false premise), and a dead reader it uncovered | Verifier success path writes `attempt["verify_cost"] = v_cost` / `attempt["verify_tokens"] = v_toks` from `extract_log_metrics(_v_log)`; `grep -rn "verification_cost\|verification_tokens" agent_workflows/` returns ONLY the two `render_stream` reads; `grep -rn "verify_cost"` returns the writer plus `run_viewer`/`run_analytics*` readers | THE VERIFIER DEFERRAL'S STATED REASON IS FALSE, AND CHASING IT FOUND A SECOND DEFECT. The plan says the verifier success path writes no accounting, so there is "no success-path contract to mirror". It does write it, as `verify_cost`/`verify_tokens`, so a verifier interrupt genuinely loses real spend. Separately, `render_run_summary_table` reads `verification_cost`/`verification_tokens`, which nothing writes anywhere, so verifier spend reaches the summary table on NO path. A deferral justified by a false fact invites the next reader to undefer it for the wrong reason. | C:Low; U:Low; S:Low; F:Low (both effects are reporting-only and out of this plan's declared surface); Overall:Low | FIXED | The Deferred entry is rewritten with the true reason: the contract exists, and the deferral stands because the dependent reader is misnamed (F-7), so a verifier fix would be unobservable until `render_stream.py` is corrected, which this plan does not declare. F-7 added with both greps. Recorded as worth a backlog item and deliberately not filed by this review. |
| PR-106 | MEDIUM | IN-SCOPE | G. Plan executability (a prerequisite understated as a preference) | `grep -rn "reconcile_item_on_interrupt" agent_workflows/ tests/` -> one def, one comment in `render_stream`, NO call; `grep -n "except KeyboardInterrupt" agent_workflows/runner_shared.py` -> comments plus `run_queue`'s own handler only; `87jnym` front matter `- Status: approved`, file in `pending/`; `parse_item_dependencies("executed:87jnym")` -> one `ipd` edge | THE FOURTH CALL SITE DOES NOT EXIST AND THE PLAN UNDERSTATES THAT. F-3 frames `87jnym` as merely not covering these fields; measured, `execute_item_core` has no `except KeyboardInterrupt` at all and `reconcile_item_on_interrupt` has zero callers, so E-02's "insert it BEFORE the `reconcile_item_on_interrupt(...)` call" names a line that is absent, and `87jnym` has not executed. The dependency edge is correct and enforced, so the ordering is safe; what was missing is what an executor should do on finding the handler absent, where the tempting action is to add it and duplicate `87jnym`'s scope. | C:Low; U:Low; S:Low; F:Medium (two plans editing the same handler); Overall:Low | FIXED | F-3 strengthened with both greps and `87jnym`'s unexecuted status; E-03 carries a verify-first instruction and a stop condition refusing to add the handler; the Scope check states it is a hard prerequisite; V-03 requires pasted evidence the handler pre-exists; the gate makes it one of two stop conditions. |
| PR-107 | LOW | IN-SCOPE | G. Plan executability (an open question whose mechanism is not yet live) + evidence hygiene | `attempts[-1].get("attempt") == attempt_no` guards the pop, while the attempt dict literal uses `"number": attempt_no`, so the predicate is `None == 1`; `87jnym` clause (c) is "make the no-changes arm's attempt pop match the attempt record's real `"number"` key"; F-1's citation gave bare `:26315`-style offsets; the plan's F-2 evidence cited a probe under `/tmp` | OQ-02 ASKS ABOUT A POP THAT CANNOT CURRENTLY FIRE, AND TWO CITATIONS ARE UNRE-DERIVABLE. The pop's key mismatch means the question becomes real only after `87jnym`, which the question does not say, so a maintainer could answer it against behavior the code does not have. Separately F-1 cited line offsets alone (which the plan's own last conventions bullet forbids and `IPD-C801` flags), and F-2's only evidence is a machine-local `/tmp` path no reviewer or executor can open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 gains a SHARPENED paragraph naming the `"attempt"`-vs-`"number"` mismatch, that the pop does not fire today, and that `87jnym` clause (c) makes it live, plus the consequence for E-06's KeyboardInterrupt cases; a conventions bullet records the key name; F-1 re-cited by quoted content; F-2 re-cited with the review reproduction across all four paths instead of the `/tmp` path. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01 instructs bumping `session_turn_counts` on an interrupt, arguing the turn consumed a slot. Keep, remove, or ask? | Remove it, and make its absence a verified property. | (a) Keep it as authored - rejected: the counter is read as the rotation trigger in two places, so a bump can make the next resume discard the session `hyit04` wants reused, defeating the plan's own purpose. (b) Ask the maintainer - rejected: the repository answers it, since `reconcile_interrupted` is the existing recovery-path precedent the helper copies and it deliberately does not bump. (c) Bump only when no rotation limit is configured - rejected as inventing a conditional nobody asked for, with a new untested branch. | the `session_turns >= max_items` reads in `execute_item_core` and `oc_runipd.run_opencode`; `reconcile_interrupted`'s body writing `set_sessions`/`session_id` and not the counter | yes |
| D-2 | E-04 hedges `StopAtCheckpoint` down to a grep on the assumption an observer needs a live stream. Accept the hedge or test the path? | Test it; all four raises are behavioral. | (a) Accept the grep - rejected: a grep that a call line exists is not evidence the path writes the fields, and this plan's whole subject is a path that has a line and writes nothing. (b) Leave it optional for the executor - rejected: an optional assertion is the first thing dropped under time pressure, and it is one of only four paths. | `CheckpointObserver(detector=lambda s: False, ...)` builds; the full path driven through the real `execute_item` reproduced `sid=None cost=None` | yes |
| D-3 | The no-double-count property is asserted from a docstring and untested. Trust it, test it, or verify only at review? | Measure it at review AND add E-05 to pin it permanently. | (a) Trust the docstring - rejected: it is the single claim the fix's safety rests on, and `pfh5qa` explicitly warns against two drifting cost derivations (P8). (b) Verify at review only - rejected: the property is invisible in this plan's diff, so nothing would stop a later refactor from making the branches additive and silently inflating every run's spend. | `extract_step_usage`'s exclusive `if/else`; identical tuples measured with and without the stored fields | yes |
| D-4 | The verifier deferral's stated reason is false (the success path DOES write `verify_cost`). Fix the reason, or extend scope to verifier interrupts? | Fix the reason and keep the deferral, on the newly found reader defect. | (a) Extend scope to verifier interrupts - rejected: the summary table reads the MISNAMED `verification_cost`, so the fix would be unobservable, and correcting the reader means editing `render_stream.py`, which this plan does not declare. (b) Leave the false reason - rejected: a deferral justified by a wrong fact invites the next reader to undefer it for the wrong reason. (c) File the backlog item for F-7 now - rejected: a review must not create the work it then cites as the carrier; the maintainer decides. | `attempt["verify_cost"] = v_cost` on the verifier success path; `verification_cost` appearing ONLY as two `render_stream` reads; `verify_cost` used by `run_viewer`/`run_analytics*` | yes |
| D-5 | `87jnym` is approved but unexecuted and the `KeyboardInterrupt` call site does not exist. Block this plan, or strengthen its handling? | Keep the declared dependency and add a verify-first instruction plus a stop condition. | (a) Mark the plan NO-GO until `87jnym` executes - rejected: the runner already enforces `executed:87jnym` at dispatch and re-checks at dispatch time, so the ordering is handled by machinery rather than by a readiness verdict; blocking would hold a correct plan for a condition the queue resolves. (b) Authorize this plan to add the handler if absent - rejected: that is `87jnym` clause (a)'s declared scope, and two plans editing one handler is how conflicting edits happen. | no `except KeyboardInterrupt` in `execute_item_core`; zero callers of `reconcile_item_on_interrupt`; `87jnym` `approved` in `pending/`; `parse_item_dependencies("executed:87jnym")` yielding a valid ipd edge | yes |
| D-6 | OQ-02 asks about a pop that cannot currently fire. Resolve it, or leave it open and sharpened? | Leave it OPEN and non-blocking for the maintainer, with the mechanism stated. | (a) Resolve it myself - rejected: it is a genuine product judgement about whether discarded spend should be visible, which `pfh5qa` explicitly flags as "a genuine question rather than a task", and the owner is the maintainer. (b) Leave the text as authored - rejected: it implies the pop fires today, so an answer could be given against behavior the code does not yet have. | `attempts[-1].get("attempt")` vs the `"number"` key, so the guard is `None == 1`; `87jnym` clause (c) | yes |
