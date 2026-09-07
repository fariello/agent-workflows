# IPD: Add an integrate verb and make resume merge finished lanes instead of re-dispatching them

- Date: 2026-09-06
- Kind: child
- Concern: TWO DEFECTS, ONE FIX. FIRST, no re-integrate path exists: when a lane finishes, verifies, finalizes, and then fails to integrate, there is NO verb that retries just the merge. Confirmed at HEAD `15445857`: `grep '"integrate"'` over `cli.py` and both runners returns nothing. The only routes are a full agent re-run (paid, slow) or a hand merge (outside the tooling, no record). SECOND, and worse, `resume --retry-incomplete` RE-DISPATCHES finished work as full agent turns: it flips `integration-blocked` and `merge-conflict` items to `queued` with `recovery_next=True` (`oc_runipd.py:6913-6936`), and no code path anywhere says "this lane is already verified, just retry the merge".
  THE RE-DISPATCH IS ACTIVELY HARMFUL, not merely wasteful. The lane still exists and holds commits, so `allocate_worktree` classifies it `HOLDS-WORK` (`worktree_lease.py:153`, `:573`) and attempt-scopes to `aw/lane/<id6>_attempt2`, ORPHANING the finished lane. That is the duplicate-work failure `k1nity` measured (byte-identical duplicate commits on 3+ resumed runs). MEASURED IN THIS REPOSITORY TONIGHT: `mm6wuz` accumulated THREE lanes (`aw/lane/mm6wuz`, `_attempt2`, `_attempt3`), and its work was recovered by hand from the third. Worse still, the plan may already be in `executed/` ON the lane while main believes it was never executed, so a fresh turn starts against a plan whose state disagrees between trees.
  A BARE `resume` DOES NOTHING AT ALL, which is the other half of the trap: `integration-blocked` is in `TERMINAL_STATES` (`oc_runipd.py:301-313`), so those items are not `queued` and are never selected. So the operator's two options are "nothing happens" and "reproduce finished work as paid turns".
  THE COST IS MEASURED, TWICE. Run `run-20260905T050043Z-639569` stranded four verified lanes that all merged clean against main; recovering them took a full session of hand merges. Tonight `mm6wuz` stranded $39.42 of verified work and needed another hand recovery (`0f8abfab`, `b2bda903`). In both cases a `git merge` would have completed in seconds.
- Scope: Add `aw <host> integrate <id6>` on both hosts to re-attempt integration for a named verified lane with NO agent turn, routed through the existing merge-and-revalidate gate; then make `resume` call it automatically, BEFORE an item is ever eligible for re-dispatch, so finished work is merged rather than reproduced. Build the verb first, then have resume call it.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_cli_conformance_matrix.py
- Item-Dependencies: executed:51vw4y
- Status: to-review
- Set: integpath
- Order: 4
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: rl67b0
- From-Backlog: yocdq4
- Blocks-Release: next

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `yocdq4` as the fourth child of the `integpath` Set, on the maintainer's ruling to shape the four `integdefer` items as one Set with the hook fix first. Every claim re-verified at HEAD `15445857` rather than trusted, since the item is from 2026-09-05 and both runners churned heavily. CONFIRMED STILL TRUE: no `integrate` verb exists anywhere; `integration-blocked` is still terminal (`oc_runipd.py:301-313`); the `--retry-incomplete` branch still flips those items to `queued` with `recovery_next=True` (`:6913-6936`); `LANE_HOLDS_WORK` still drives attempt-scoping (`worktree_lease.py:153`, `:573`). TWO CORRECTIONS TO THE ITEM. Its ordering note says `txc9l1` is "approved, pending" and cannot land until this is resolved; `txc9l1` has since EXECUTED, so that note is moot and its concern (routing a resumed turn whose lane holds work to a verify-and-continue turn) is now shipped, which makes Part B's "before dispatch is even considered" requirement narrower and clearer rather than redundant: `txc9l1` acts once a turn IS being dispatched, this acts before dispatch is contemplated at all. Its state-of-the-lanes paragraph is also now HISTORICAL: all four cited branches are deleted and all four plans are in `executed/`, recovered by hand last session, so this plan reproduces the condition synthetically. FRESH EVIDENCE THE ITEM COULD NOT HAVE HAD: tonight `mm6wuz` stranded $39.42 with THREE accumulated lanes, which is the item's predicted orphaning measured in the wild.

## Goal

Make recovering a verified-but-unintegrated lane cost one merge instead of one agent turn, and make `resume` do it automatically so nobody has to know the verb exists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the explicit verb (Part A)

- [ ] E-01 Add the shared re-integration entry point to `runner_shared.py`: given a repo and an id6, locate that lane, verify it is a genuine verified-and-finalized lane, and re-attempt integration through the shared integration function child 02 extracted. Place it beside that function so the verb and the in-run path are ONE implementation.
  RE-VERIFICATION IS MANDATORY AND IS THE WHOLE SAFETY ARGUMENT. A lane verified against yesterday's main is not verified against today's. Route every attempt through `orchestrate_isolation.execute_merge_and_revalidate_gate`, which already encodes "per-lane green never implies integrated green". Do NOT shortcut to a bare `git merge` because `git merge-tree` came back clean: that proves absence of TEXTUAL conflict and says nothing about whether the suite still passes. The backlog item is explicit that its own `merge-tree` evidence was offered as proof the work is RECOVERABLE, never that it is SAFE to merge unverified.
  REFUSE, DO NOT GUESS, WHEN THE LANE IS NOT WHAT IT CLAIMS. A missing branch, a lane holding no commits, a lane whose plan is not finalized on it: each is a distinct refusal with its own message, not a silent no-op and not an attempt. `worktree_lease`'s existing classification (`ABSENT`/`EMPTY`/`HOLDS-WORK`/`FOREIGN`, `:141-153`) already names these states; consume it rather than writing a second classifier.
  - Depends on: none
  - Expected outcome: one shared function re-attempts integration for a named lane, always through the revalidate gate, refusing with a specific reason for each not-a-verified-lane case; no second integration implementation exists.
  - Execution state: pending

- [ ] E-02 Expose it as `aw <host> integrate <id6>` on BOTH hosts, and register it in the implicit-start subcommand set. THE SECOND HALF IS NOT OPTIONAL: both drivers rewrite a first token that is not a known subcommand into `start <token>` (`oc_runipd.py:7878-7886`), so an unregistered `integrate` would be swallowed as a SELECTOR and silently launch a run. `runstop` recorded exactly this hazard for `stop`: "`stop <run-id> --now` would be rewritten to `start stop <run-id> --now`, i.e. it would LAUNCH a run", and a test asserts the bare form is not rewritten in both drivers. Add `integrate` to the set in both, and add the same guard test.
  DECLARE IT THROUGH THE CLI SURFACE the repository already uses, so `aw <host> integrate` appears in `--help` and in the conformance matrix rather than existing as an undocumented path. `tests/test_cli_conformance_matrix.py` is in Scope-Paths for that reason.
  NO AGENT TURN, and say so in the help text. The verb's entire value is that it costs a merge rather than a paid turn; an operator who cannot tell that from `--help` will reach for a re-run instead.
  - Depends on: E-01
  - Expected outcome: `aw oc integrate <id6>` and `aw agy integrate <id6>` both work, appear in `--help`, are registered in both implicit-start subcommand sets, and are pinned by a not-rewritten test on both hosts.
  - Execution state: pending

### Task group 2: resume merges instead of re-dispatching (Part B)

- [ ] E-03 On resume, attempt INTEGRATION ONLY for an item in `integration-blocked` or `merge-conflict` whose lane still exists and is verified, BEFORE that item is ever eligible for re-dispatch. This must run ahead of the `--retry-incomplete` requeue (`oc_runipd.py:6913-6936`), because once an item is flipped to `queued` with `recovery_next=True` the cheap path is already lost.
  THIS MUST NOT BE BEHIND A FLAG. The alternative default is silent re-dispatch of finished work, which is strictly worse, and the backlog item says so directly. Empirically, this alone would have resolved all four items in the measured run.
  CALL E-01's FUNCTION, do not reimplement. One code path for the verb and for resume is the point of building A before B.
  A SUCCESSFUL INTEGRATION MUST UPDATE THE ITEM'S STATE HONESTLY, and a failed one must leave it exactly as it was, with its lane preserved. Do not invent a disposition: on success the item reaches the same state an in-run integration produces; on failure it stays terminal and the operator still has the verb.
  - Depends on: E-02
  - Expected outcome: a bare resume merges an already-verified lane with no agent turn; a lane that cannot be integrated is left untouched with its branch preserved; no flag is required to get the safe behavior.
  - Execution state: pending

- [ ] E-04 Make the re-dispatch path REACHABLE ONLY when integration genuinely cannot help, so the orphaning stops. After E-03, an item that still holds an unintegrated verified lane must NOT be attempt-scoped into a second lane by `--retry-incomplete`.
  THE ORPHANING MECHANISM IS MEASURED, so this item has a concrete target: `allocate_worktree` classifies an existing lane with commits as `HOLDS-WORK` and attempt-scopes to `_attempt2` (`worktree_lease.py:573`), which is how `mm6wuz` reached THREE lanes tonight and how `k1nity` measured byte-identical duplicate commits across 3+ resumed runs.
  DO NOT DELETE OR RECLAIM A LANE to avoid the attempt-scope. The lane is the preserved evidence and this repository's policy is to leave such state alone; the fix is to integrate it, not to clear the way for redoing it.
  PRESERVE `--retry-incomplete` FOR WHAT IT IS FOR: an item that genuinely needs another agent turn (a real failure, an unfinished turn) must still be retryable. This item narrows the flag's reach to those cases rather than removing it.
  - Depends on: E-03
  - Expected outcome: an item whose verified lane is merely unintegrated is integrated rather than re-dispatched; no second lane is allocated for it; `--retry-incomplete` still retries items that genuinely need a turn.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Test the VERB deterministically on both hosts: a verified finalized lane integrates; a missing branch refuses with a named reason; a lane holding no commits refuses; a lane whose plan is not finalized refuses; and every successful attempt provably ran the revalidate gate rather than a bare merge.
  ASSERT THE GATE RAN. This is the safety-critical assertion of the whole plan: name the gate function and show it was invoked, because a bare `git merge` would pass every other assertion in this item while discarding the guarantee.
  ASSERT THE IMPLICIT-START GUARD on both hosts: a bare `integrate` token must NOT be rewritten into `start integrate`, mirroring the existing `stop` test.
  - Depends on: E-04
  - Expected outcome: five verb cases pinned per host; the revalidate gate is proven to run; the not-rewritten guard passes on both drivers.
  - Execution state: pending

- [ ] E-06 Test RESUME's automatic path, which is where the expensive failure lives. Build a run whose item is `integration-blocked` with a verified lane present, then resume it and assert: the lane INTEGRATES, NO agent turn is dispatched, and NO second lane is allocated.
  ASSERT THE ABSENCE OF A TURN AND OF A SECOND LANE EXPLICITLY. Those two absences ARE the fix; a test that only checks the item ended up integrated would pass even if resume had paid for a full turn to get there. Assert no `_attempt2` branch exists afterwards.
  ALSO ASSERT THE NEGATIVE CASE: an item that genuinely needs a turn (not an unintegrated lane) is still re-dispatched under `--retry-incomplete`, so E-04 narrowed the flag rather than breaking it.
  - Depends on: E-05
  - Expected outcome: resume integrates with zero turns and zero new lanes; a genuinely incomplete item is still retryable; both absences are asserted directly.
  - Execution state: pending

- [ ] E-07 Reproduce the MEASURED INCIDENTS synthetically and show they are now survived, on both hosts, then run the suite bare. Two shapes, both from this repository's own history:
  (a) THE FOUR-LANE CASE (`run-20260905T050043Z-639569`): four items verified and finalized on their lanes, refused integration on transient dirt, all merging clean afterwards. Show each recovered by the verb with no agent turn.
  (b) THE THREE-LANE CASE (`mm6wuz`, tonight): an item whose lane holds verified work and which accumulated `_attempt2` and `_attempt3` across resumes. Show that after this plan a resume integrates the FIRST lane instead of allocating a second.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. MEASURE YOUR OWN BEFORE-BASELINE: the suite is NOT green at HEAD, so the criterion is that the AFTER failure set minus the BEFORE set is EMPTY. VALIDATE IN THE REAL CHECKOUT: `tests/test_run_viewer.py` reads the gitignored `.aw/records/runs/` and fails in a bare worktree.
  - Depends on: E-06
  - Expected outcome: both historical shapes are survived on both hosts with no paid turns and no orphaned lanes; bare suite delta empty with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- NO `integrate` VERB EXISTS: `grep '"integrate"'` over `cli.py`, `oc_runipd.py` and `agy_runipd.py` returns nothing at HEAD `15445857`.
- THE IMPLICIT-START SHIM WILL SWALLOW AN UNREGISTERED VERB. Both drivers rewrite an unknown first token into `start <token>` (`oc_runipd.py:7878-7886`), and `runstop` recorded the measured hazard for `stop`: the bare form "would LAUNCH a run" with the verb as a selector. Registration plus a not-rewritten test is mandatory, on both hosts. Note `mm6wuz` (executed tonight) REMOVED `-v`/`--version` from that set, so the set's membership is current as cited.
- `integration-blocked` IS TERMINAL (`oc_runipd.py:301-313`), so a bare resume does nothing with such an item; only `--retry-incomplete` touches it, and that flips it to `queued` with `recovery_next=True` (`:6913-6936`).
- THE ORPHANING IS A CLASSIFICATION CONSEQUENCE: an existing lane with commits is `HOLDS-WORK` and gets attempt-scoped to `_attempt2` (`worktree_lease.py:153`, `:573`), which is why re-dispatch abandons finished work rather than resuming it.
- INFORMING AN AGENT IS NECESSARY AND NOT SUFFICIENT: `k1nity` measured byte-identical duplicate commits on 3+ resumed runs DESPITE an explicit recovery notice (`runner_shared.py` `build_recovery_lane_notice`). So the fix must be a deterministic code path, never a prompt.
- `txc9l1` HAS EXECUTED and routes a resumed turn whose lane holds work to a verify-and-continue turn. It is complementary, not redundant: it acts once a turn IS being dispatched, whereas this plan's Part B must act BEFORE dispatch is contemplated, because the cheapest correct action is a merge with no turn at all.
- THE REVALIDATE GATE IS THE EXISTING AUTHORITY: `orchestrate_isolation.execute_merge_and_revalidate_gate` already encodes "per-lane green never implies integrated green". Reuse it; never substitute `git merge-tree` cleanliness for it.
- Run the suite BARE: `python3 -m pytest`. Validate `test_run_viewer.py` in the REAL checkout.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | No re-integrate verb exists on either host or in the CLI. | `grep '"integrate"'` over `cli.py`, `oc_runipd.py`, `agy_runipd.py` at HEAD `15445857`: no output |
| F-2 | A bare resume cannot help: `integration-blocked` is in `TERMINAL_STATES`, so the item is never `queued` and never selected. | `oc_runipd.py:301-313` |
| F-3 | `--retry-incomplete` flips `integration-blocked` and `merge-conflict` to `queued` with `recovery_next=True` and re-dispatches them as FULL AGENT TURNS; no code path retries only the merge. | `oc_runipd.py:6913-6936` |
| F-4 | **THE ORPHANING MECHANISM.** An existing lane holding commits classifies as `HOLDS-WORK` and is attempt-scoped to `_attempt2`, abandoning the finished lane. | `worktree_lease.py:153`, `:573` |
| F-5 | **MEASURED TONIGHT, the item's prediction realized:** `mm6wuz` accumulated THREE lanes (`aw/lane/mm6wuz`, `_attempt2`, `_attempt3`) and $39.42 of verified work was recovered by hand from the third. | `git branch --list 'aw/lane/mm6wuz*'`; commits `0f8abfab`, `b2bda903` |
| F-6 | THE FOUR-LANE INCIDENT: `run-20260905T050043Z-639569` stranded four verified lanes that all merged clean against main; recovery took a full session of hand merges. | backlog `yocdq4`, `5wdoze` |
| F-7 | The duplicate-work failure class is measured and prompt-resistant: `k1nity` observed byte-identical duplicate commits on 3+ resumed runs despite an explicit notice. | `k1nity`; `runner_shared.py` `build_recovery_lane_notice` |
| F-8 | **THE ITEM'S ORDERING NOTE IS NOW MOOT:** it says `txc9l1` is "approved, pending" and blocked behind this work; `txc9l1` has EXECUTED. Its concern is complementary rather than overlapping (it acts at dispatch, this acts before dispatch). | `ls .aw/records/plans/executed/*txc9l1*` |
| F-9 | **THE ITEM'S LANE EVIDENCE IS HISTORICAL:** all four cited branches are deleted and all four plans are in `executed/`, so the conditions must be reproduced synthetically. | `git rev-parse --verify` fails for all four |
| F-10 | The implicit-start shim is a live hazard for a new verb, with a recorded precedent: an unregistered `stop` "would be rewritten to `start stop <run-id> --now`, i.e. it would LAUNCH a run". | `oc_runipd.py:7878-7886`; `runstop` `71vjbn` E-03 |

## Proposed changes (ordered, validatable)

1. One shared re-integration function, always through the revalidate gate, with a specific refusal per not-a-verified-lane case (E-01).
2. Expose `aw <host> integrate <id6>` on both hosts, registered in both implicit-start subcommand sets with a not-rewritten guard (E-02).
3. Resume attempts integration-only BEFORE re-dispatch eligibility, unflagged (E-03).
4. Narrow re-dispatch so an unintegrated verified lane is never attempt-scoped into a second lane (E-04).
5. Pin the verb's five cases per host, including proof the gate ran (E-05).
6. Pin resume's automatic path, asserting the absence of a turn and of a second lane (E-06).
7. Reproduce both measured incidents and show them survived; run the suite bare (E-07).

## Deferred / out of scope (with reason)

- THE DEFERRAL LADDER. Child 03 (`51vw4y`) owns deferring and re-attempting DURING a run; this child owns recovering AFTER one ended. Declared as `Item-Dependencies: executed:51vw4y` because the ladder's non-terminal status and its re-attempt path are what this verb reuses; building the verb first would mean writing the re-attempt twice.
- THE STARTUP DIRTY-BASE GATE (`p8ni63`). Prevention rather than recovery, and a separate refusal surface with its own consent flag.
- THE EXECUTED-TRANSITION HOOK (`rnl3b7`, child 01 `29wvmj`). The item's own ordering note warns that a re-integrate verb tripping that hook on every invocation would be unusable, which is exactly why the hook fix is child 01 of this Set and lands first.
- DELETING OR RECLAIMING ORPHANED LANES. `mm6wuz` left three; tidying them is not this plan's business and the repository's policy is to leave such state alone. The fix is that new ones stop being created.
- MAKING THE VERB WORK ON A LANE FROM A DIFFERENT REPOSITORY OR A FOREIGN BRANCH. `worktree_lease` already classifies `FOREIGN`; this plan refuses that case rather than handling it.
- CHANGING WHAT `--retry-incomplete` MEANS for genuinely incomplete items. E-04 narrows its reach to those cases; it does not redefine or remove the flag.

## Scope check

- Over-scope: none. One shared module, both drivers, the CLI surface, and four test modules.
- Scope-Paths justification: `runner_shared.py` holds the shared re-integration function (E-01) beside the integration function child 02 extracted; `oc_runipd.py` and `agy_runipd.py` each need the verb, the subcommand-set registration, and the resume ordering change (E-02..E-04); `cli.py` carries the host verb surface; `tests/test_runner_shared.py` covers the shared function, each driver's suite its own host, and `tests/test_cli_conformance_matrix.py` pins the declared surface.
- BOTH DRIVER MODULES ARE THE HIGHEST-CONTENTION FILES IN THE REPOSITORY, and three siblings in this Set also declare them. Children are SEQUENTIAL by the Set's own constraint; expect drift, re-locate by symbol, and expect to rebase and re-run the full suite after any merge.
- Under-scope, stated rather than left as `none`: this child does not add the ladder, the startup gate, or the hook fix; does not clean up existing orphaned lanes; does not handle foreign lanes; and does not redefine `--retry-incomplete`. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. MEASURE YOUR OWN BEFORE-BASELINE: the suite is NOT green at HEAD (`1 failed, 5612 passed` at authoring, the failure being pre-existing `test_orchestrator_retirement::RealRepositorySets`), so the criterion is that the AFTER failure set minus the BEFORE set is EMPTY.
- Targeted: `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_cli_conformance_matrix.py`.
- A LIVE VERB DEMONSTRATION on BOTH hosts in a throwaway repository: a verified finalized lane recovered by `aw <host> integrate <id6>` with the merge commit on main pasted and NO agent turn spent.
- A LIVE RESUME DEMONSTRATION: an `integration-blocked` item with a verified lane, resumed, showing the merge happened, `git branch --list` showing NO `_attempt2`, and the run record showing no turn dispatched.
- VALIDATE IN THE REAL CHECKOUT for `tests/test_run_viewer.py` (reads the gitignored `.aw/records/runs/`).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `25kzda` owns the run command surface and its verbs. Adding `integrate` is a NEW verb on that surface, so the spec's command table must be checked: if it enumerates the host verbs, add this one; if the spec does not enumerate them, no change is needed. Verify by reading rather than assuming, and do NOT edit the spec's §4.2 finding-code table under any circumstances (it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change).

The verb's `--help` text must state plainly that it costs NO agent turn and that it re-runs the revalidate gate, since both facts are what make an operator choose it over a re-run.

A CHANGELOG entry is warranted: this adds an operator-facing verb and changes what a bare `resume` does. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: Should `resume`'s automatic integration be attempted for `merge-conflict` items as well as `integration-blocked`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, ATTEMPT BOTH, because the attempt is cheap and the outcome is authoritative. `merge-conflict` means the gate previously found a real conflict against the main of that moment; main has since moved, so the conflict may be gone and the only way to know is to run the gate again. The cost of trying is one gate run with no agent turn, and a failure leaves the item exactly as it was with its lane preserved. Refusing to retry a `merge-conflict` would leave the more expensive path (a paid re-dispatch that orphans the lane) as the only route for the case most likely to need help. Both states are already in the `--retry-incomplete` list together (`oc_runipd.py:6913-6936`), so treating them alike here matches the existing grouping.

### OQ-02: Should the verb require the run id, or find the lane from the id6 alone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE id6 ALONE, with the run id optional. The lane branch name is derived from the id6 (`aw/lane/<id6>`), so the id6 is sufficient to locate the work, and the item's strongest stated use case is "a lane stranded by an OLDER run" where the operator may not remember or have the run id. Requiring it would make the verb useless in exactly that case. A run id may be accepted to disambiguate attempt-scoped lanes (`_attempt2`, `_attempt3`), which `mm6wuz` proves can exist; when several candidates match and no run id is given, REFUSE and list them rather than guessing, since picking the wrong lane would integrate the wrong work.

### OQ-03: What should the verb do when the lane merges clean but the revalidate gate fails?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REFUSE, leave main untouched, preserve the lane, and report the gate's findings. That is exactly what the in-run path already does on a non-passing gate result, and the verb must not be a softer door into main than the runner is: if the verb could merge what the runner refused, every future stranding would be "resolved" by reaching for the verb. This is also why E-01 forbids substituting `git merge-tree` cleanliness for the gate. The operator's recourse is the same as today's: resolve on the preserved lane branch, or decide the failure is unrelated and act deliberately.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the shared function's signature and body. Paste FOUR refusals with their distinct messages: absent branch, empty lane, plan not finalized on the lane, foreign lane. Paste a successful attempt AND name the gate function, showing it was invoked; state in one sentence why `git merge-tree` cleanliness is not an acceptable substitute. Confirm `worktree_lease`'s existing classification is consumed rather than a second classifier written.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw oc integrate --help` and `aw agy integrate --help`, both showing the no-agent-turn statement. Paste the subcommand-set diff for BOTH drivers showing `integrate` registered. Paste the not-rewritten guard test passing on both hosts, and paste what a bare `integrate` token does (it must NOT launch a run), measured UNPIPED. Paste the conformance-matrix entry.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a resume of an `integration-blocked` item with a verified lane showing the merge happened with NO flag passed. Paste the run record showing NO agent turn was dispatched. Paste the ordering proof: the integration attempt occurs BEFORE the `--retry-incomplete` requeue, quoted from the code. Paste the failure case showing the item unchanged and its lane still present.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git branch --list 'aw/lane/<id6>*'` after a resume of an unintegrated verified lane, showing NO `_attempt2` was created. Paste the contrast: an item that genuinely needs a turn IS still re-dispatched under `--retry-incomplete`. Confirm no lane was deleted or reclaimed to achieve this, quoting the code path.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL output of the five verb cases per host. For the success case, paste proof the revalidate gate ran (not a bare merge) and state how you proved it. Paste the implicit-start guard results for both drivers.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: THE TWO ABSENCES ARE THE FIX, so paste both explicitly: zero agent turns dispatched, and zero new lane branches. A paste showing only that the item ended integrated is a FAILED validation, since a paid re-dispatch could also produce that. Paste the negative case proving `--retry-incomplete` still retries a genuinely incomplete item.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste both historical shapes reproduced and survived on BOTH hosts: (a) four verified lanes each recovered by the verb with no agent turn; (b) an item with a verified lane resumed WITHOUT allocating a second lane, contrasted against the pre-fix behavior which allocates `_attempt2`. Paste the BARE `python3 -m pytest` summary with before/after counts and show the AFTER-minus-BEFORE failure set is EMPTY. If the agy host could not be demonstrated, SAY SO PLAINLY rather than inferring from the oc result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

DEPENDENCY: this child declares `- Item-Dependencies: executed:51vw4y` and MUST NOT run before child 03. The ladder establishes the non-terminal status and the re-attempt path this verb reuses; building the verb first would mean writing the re-attempt logic twice, into the same two high-contention files. The runner re-checks dependencies at dispatch, so a queued-together Set is safe.

Scope fence: touch ONLY the eight paths in `Scope-Paths`. Do NOT substitute `git merge-tree` cleanliness for the revalidate gate. Do NOT make the verb a softer door into main than the in-run path (OQ-03). Do NOT delete, reclaim, or clean up any lane branch or worktree. Do NOT put the resume behavior behind a flag. Do NOT redefine or remove `--retry-incomplete`. Do NOT edit spec `25kzda`, and never its finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT and both driver modules are the highest-contention files in it: run `aw runs` before starting, and if a driver file is being changed under you and the two sets of changes cannot be safely combined, STOP and report rather than overwriting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

BASELINE HONESTY: the suite is NOT green at HEAD and this plan does not make it green. Judge yourself on the DELTA, and do not report the pre-existing `test_orchestrator_retirement` failure as yours.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find the implicit-start subcommand sets, the `--retry-incomplete` requeue branch, `TERMINAL_STATES`, `allocate_worktree`'s lane classification, and `execute_merge_and_revalidate_gate` by name.

THE ITEM THAT MATTERS MOST IS V-06's TWO ABSENCES. This plan exists because resume PAYS FOR A TURN and ORPHANS A LANE where a merge would do. A test asserting only that the item ended integrated would pass identically if resume had spent $39 to get there, which is the bug. Assert zero turns and zero new lanes, directly.

THE SECOND-MOST IMPORTANT IS V-01's GATE PROOF. The tempting shortcut is a bare `git merge` once `merge-tree` reports clean, and every functional test would still pass. That would silently discard "per-lane green never implies integrated green" and turn this verb into a way to land unvalidated work in main. If you find yourself calling `git merge` without the gate, stop.

On completion, close backlog `yocdq4`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits.
