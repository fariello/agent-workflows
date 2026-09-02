# IPD: Route a resumed turn whose lane already holds its work to verify-and-continue instead of re-executing from scratch

- Date: 2026-08-31
- Kind: child
- Concern: A resumed run re-executes work a PRIOR attempt already committed on the lane it was displaced from, producing a near-duplicate sibling commit and doubling spend, because the decision is delegated to the agent's judgment via the prompt rather than made by the driver from facts it already observes.
- Scope: Have the DRIVER classify the PRIOR attempt's (displaced) lane before dispatching a recovery turn, and route a prior lane that already holds the plan's work to a verify-and-continue turn instead of a fresh execution turn. Consumes the shipped `worktree_lease.inspect_lane` classification and the shipped INTERRUPTED SNAPSHOT convention as the completeness signal. Does NOT remove or weaken the existing recovery prompt notice, does NOT add an acknowledgement gate, does NOT adopt or mutate the displaced lane, and does NOT change first-attempt behavior.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/worktree_lease.py, tests/test_resumedupe.py
- Item-Dependencies: none
- Status: reviewed
- Set: resumedupe
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: txc9l1
- From-Backlog: k1nity

## Workflow history
- 2026-09-02 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001 BLOCKER (wrong lane classified, would have shipped inert) through PR-006 all fixed

- 2026-09-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1 at HEAD `4541aa7c`: APPROVE WITH REVISIONS APPLIED, PR-001..PR-006, all FIXED. PR-001 BLOCKER: the plan classified THE WRONG LANE and would have shipped INERT. Allocation never reuses a lane holding work (`worktree_lease.py:512-529`), so a resumed turn gets a fresh `_attemptN` lane at 0 commits while the work sits on the displaced one; measured directly (re-allocating over a lane with 1 commit returned `ntf6sx:attempt2`, `displaced_from=aw/lane/ntf6sx`, new lane `EMPTY`, old `HOLDS-WORK`). E-01 now resolves the PRIOR lane from `preserved_lane_id`/`attempts[-1]`/`displaced_from`, E-04 tells the agent the work is on another branch it may read but must not commit to, and E-06 (a2) plus V-01 add a mandatory inertness proof. PR-002 HIGH: the flagship `ntf6sx` measurement was mechanically invalid (`7e9c4444` is a MERGE whose second parent IS `5b8c0004` and which CONTAINS `fb0774b2`, so the empty diff is guaranteed by ancestry) AND the second finalize was legitimate (the merge reverted the plan from `executed/` to `pending/`); the regression case moved to the genuinely duplicated `zhr6mc` pair. PR-003 HIGH: four stale line citations, one landing on `*,`. PR-004 MEDIUM: `worktree_lease.py` added to Scope-Paths (D-1) and the plan's own open scope question ruled. PR-005 MEDIUM: OQ-01 overstated `finalize_precheck`, which deliberately does not refuse on scope. PR-006 LOW: stale suite baseline now re-measured at execution time. Review record: `.aw/records/reviews/20260901-resumedupe-01-txc9l1-route-a-resumed-turn-whose-lane-already-holds-its-work.review.md`.
- 2026-08-31 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `k1nity`. Its Q1 (put the lane's actual state in the prompt) is ALREADY BUILT and is therefore NOT this plan's remedy: `build_recovery_lane_notice` (`oc_runipd.py:3485`) already names the lane branch, its commit count, its dirty state and the snapshot convention, and the duplication was measured AFTER that landed. That finding is the whole justification for taking Q2 instead: the judgment moves to the driver, which already holds the facts. Q3's completeness signal is the shipped INTERRUPTED SNAPSHOT commit. No `Blocks-Release` gate: the item carries none, and it is wasted spend plus confusing history rather than a data-safety bug.
- 2026-08-31 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop paying for a full turn to redo work a prior attempt already committed. Telling the agent it is resuming has already been tried and is demonstrably insufficient (F-1/F-2); this plan moves the decision to the driver, which can read the prior attempt's lane without asking anyone.

THE DUPLICATION IS REAL, and the measurement was CORRECTED at review (F-8, F-9). The reviewable proof is `zhr6mc`: two sibling commits with the SAME subject `feat(runner): close a backlog item when the run executes its last carrier`, on INDEPENDENT parents (`42b38acf` parent `bcbbfb07`; `8a9b8f32` parent `144f3347`), 2118 vs 2260 insertions over the same four files. `bmh754` shows the same shape (`c823390f` parent `bcbbfb07`; `8c437188` parent `144f3347`, both touching exactly `AGENTS.md`, `check_engine.py`, `ipd_schema.py`, `test_ipd_dependency_check.py`). That is one full turn's work performed twice.

The graduating measurement was WRONG in its mechanism and MUST NOT be reused as the plan's model: `7e9c4444` is a MERGE COMMIT whose second parent IS `5b8c0004`, and `fb0774b2` is its ancestor, so `git diff fb0774b2 7e9c4444` being empty is arithmetically GUARANTEED and proves nothing about re-execution. Worse, the ntf6sx "duplicate finalize" was LEGITIMATE work, not waste: the merge's own combined diff moved the plan back from `executed/` to `pending/` (attempt 1's `Status: executed` regressed to `Status: approved`), so `3558ce1f` was re-doing a lifecycle move the merge had reverted. Building the regression test on the ntf6sx shape would pin the wrong behavior; E-06 uses `zhr6mc` instead.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: classify the lane before dispatching a recovery turn

- [ ] E-01 Add `classify_recovery_disposition(repo, item, state)` to `oc_runipd.py` returning a typed decision of `fresh-execution`, `verify-and-continue`, or `undetermined`.

  IT MUST CLASSIFY THE PRIOR ATTEMPT'S LANE, NOT THE TURN'S OWN LANE. This is the correction that makes the plan work at all (F-10, MEASURED): allocation NEVER reuses a lane holding work. `allocate_worktree` classifies an existing lane `HOLDS-WORK` and ATTEMPT-SCOPES alongside it (`worktree_lease.py:512-529`), so the resumed turn gets a BRAND-NEW `aw/lane/<id6>_attemptN` at zero commits while the work sits on the lane it was displaced from. Measured directly: after committing on lane `ntf6sx`, a second `allocate_worktree(repo, 'ntf6sx')` returned lane `ntf6sx:attempt2` (`disposition=attempt-scoped`, `displaced_from=aw/lane/ntf6sx`), and `inspect_lane` reported the new lane `EMPTY commits_ahead=0` while the old one reported `HOLDS-WORK commits_ahead=1`. A classifier keyed on the turn's own lane would therefore return `fresh-execution` ON EVERY RESUME and this plan would be INERT while appearing to work, which is exactly the failure `zwnjp3`'s "previously WRITTEN and never READ" note warns about (`oc_runipd.py:1514`).

  So resolve the lane to inspect from the DURABLE prior-attempt record, in this order, and never by reconstructing a name from the id6 (`worktree_lease.py:69-73` forbids that explicitly): (1) `item["preserved_lane_id"]`/`preserved_base`, written at `oc_runipd.py:5415-5420` for exactly this purpose; (2) failing that, the last entry of `item["attempts"]` carrying `worktree_lane_id`/`worktree_base` (`oc_runipd.py:4879-4884`); (3) failing that, the CURRENT handle's `displaced_from`, which names the lane the fresh allocation was displaced from. Compute from the SHIPPED `worktree_lease.inspect_lane` reading (`worktree_lease.py:203`), which already reports `commits_ahead`, `dirty`, the lane's own base sha and one of the five `LANE_STATES` (`worktree_lease.py:103`), and pass `base_commit=` the recorded prior base so `commits_ahead` is measured against the base that lane was actually cut from.

  Decide `verify-and-continue` only when the prior lane holds at least one commit that is NOT an INTERRUPTED SNAPSHOT; `fresh-execution` when no prior lane is recorded, or it is absent, empty, or holds only a snapshot; `undetermined` when a recorded lane cannot be read. Pure function of an inspection result: no mutation, no git writes, and NO adoption of the displaced lane.
  - Depends on: none
  - Expected outcome: given a prior lane with 2 real commits and a fresh attempt-scoped current lane at 0 commits, the decision is `verify-and-continue` (proving it read the PRIOR lane, not the current one); no recorded prior lane, or an absent/empty one, classifies `fresh-execution`; a prior lane holding ONLY an INTERRUPTED SNAPSHOT commit classifies `fresh-execution`; an unreadable recorded lane classifies `undetermined`.
  - Execution state: pending

- [ ] E-02 Distinguish a real commit from a preservation snapshot using the shipped message convention rather than a new marker: `worktree_lease.py:699-700` writes `WIP INTERRUPTED SNAPSHOT (not finished work): lane <id>`. Promote that literal to a module-level constant in `worktree_lease.py` (the correct home: it is the module that WRITES the message, and it imports neither driver while both import it, so no cycle is possible) and consume it in the new classifier plus both places that currently hardcode the phrase in prose. Those two sites are `oc_runipd.py:3759` and `agy_runipd.py:2380` (the plan's original `:3552`/`:2375` citations were STALE by roughly 200 lines and pointed at unrelated code; re-locate by symbol, `build_recovery_lane_notice`, not by line). Detect a snapshot by matching the constant PREFIX against the commit's subject line only, not a substring search of the full body, so the explanatory body text ("This is a preservation snapshot, NOT validated or reviewed work") can never make a real commit look like a snapshot. This is the completeness signal the backlog item's Q3 asks for: a snapshot means work was preserved mid-edit, so redoing it IS correct.
  - Depends on: E-01
  - Expected outcome: the literal appears exactly once as a definition; a grep proves the two driver prose sites and the classifier all reference the constant rather than re-spelling the phrase; a commit whose SUBJECT carries it is never counted as finished work, and a commit that merely quotes the phrase in its body still counts as real work.
  - Execution state: pending

- [ ] E-03 Treat `undetermined` as fresh execution, and say so where it is decided. If the lane cannot be read the driver must NOT silently skip execution, because skipping risks leaving a plan unimplemented, which is a worse failure than paying for a duplicate turn. This is a deliberate fail-toward-doing-the-work choice and is the OPPOSITE of the fail-closed stance used for lifecycle gates; record the asymmetry in a comment so a later reader does not "fix" it into a refusal.
  - Depends on: E-01
  - Expected outcome: an unreadable lane produces a fresh-execution dispatch plus a recorded reason; no code path turns an inspection failure into a skipped item.
  - Execution state: pending

### Task group 2: dispatch the verify-and-continue turn

- [ ] E-04 When the disposition is `verify-and-continue`, dispatch a turn whose prompt asks the agent to VERIFY and COMPLETE what the PRIOR lane already contains rather than to implement the plan from scratch, and pass it the prior lane's concrete facts: its branch name, its commit shas, their subjects, and the diffstat against its recorded base.

  Build this as a variant of the EXISTING recovery branch, extending `build_recovery_lane_notice` (`oc_runipd.py:3692`, NOT the stale `:3485`) rather than adding a second prompt mechanism, and keep its stated constraints: no acknowledgement gate and no refusal path, because a refusal is one more way for an unattended run to stall. `tests/test_lane_allocation_idempotent.py:709-717` PINS that constraint by scanning the function body for `input(`, `acknowledgement required` and `refuse`, so the new text must not introduce those tokens; run that test as a regression check, not just the new file.

  Follow the SHIPPED de-duplication pattern rather than inventing one: `agy_runipd.build_isolation_notice` (`agy_runipd.py:2388-2396`) imports the OpenCode implementation and delegates, and `agy_runipd.build_recovery_lane_notice` (`agy_runipd.py:2313`) is today a verbatim COPY. Make the OpenCode function the single definition and have the Antigravity twin delegate to it, so a one-runner fix cannot leave the other duplicating. `tests/test_lane_allocation_idempotent.py:355-371` already pins that both drivers expose the symbol; delegation keeps that true.

  THE PROMPT MUST BE EXPLICIT THAT THE WORK IS ON A DIFFERENT BRANCH THAN THE AGENT'S CWD, because it is: the agent runs in the fresh attempt-scoped lane while the prior work sits on the displaced branch (E-01). Tell it the prior branch by name and that it may READ it (for example `git log`/`git diff` against that ref) and must bring forward what is still correct into its OWN lane. Do NOT instruct it to `git checkout`, merge, or commit onto the displaced branch: that lane may be another attempt's preserved work and the shipped rule is to leave it byte-identical (`worktree_lease.py:518-520`, `oc_runipd.py:1691-1695`).
  - Depends on: E-02, E-03
  - Expected outcome: a `verify-and-continue` prompt contains the PRIOR lane's branch name, actual commit shas and diffstat, states that the work is on that other branch, asks for verification-and-completion into the agent's own lane, and contains no instruction to check out or commit onto the displaced branch; a `fresh-execution` recovery prompt is UNCHANGED from today's text; a first-attempt prompt is unchanged; `tests/test_lane_allocation_idempotent.py` still passes.
  - Execution state: pending

- [ ] E-05 Record the routing decision and its inputs in the run's durable state and events, so an operator can see WHY a turn was routed as it was without re-deriving it. Include the disposition, the observed `commits_ahead`, whether a snapshot was present, and the reason string. Without this, a wrong routing decision is invisible after the fact, which is the same diagnosability gap that made the original duplication take three runs to notice.
  - Depends on: E-04
  - Expected outcome: the item's state carries the disposition and its inputs, and an event records the routing; a run that routed to `verify-and-continue` is distinguishable from one that re-executed, in state alone.
  - Execution state: pending

### Task group 3: falsifiable tests

- [ ] E-06 Add `tests/test_resumedupe.py` and SABOTAGE every assertion before trusting it. Build fixtures with the REAL `worktree_lease.allocate_worktree` (as `tests/test_lane_allocation_idempotent.py` does) so the attempt-scoping in E-01 is exercised rather than assumed away by a hand-built state dict.

  Required cases: (a) THE REGRESSION CASE, reconstructing the CORRECTED `zhr6mc` shape, NOT the ntf6sx one (see Goal and F-8): allocate a lane, commit two real commits on it, allocate AGAIN for the resumed turn so the driver holds a fresh attempt-scoped lane at zero commits, and assert the routing is `verify-and-continue`. (a2) THE INERTNESS GUARD, which is the single most important assertion in the file: assert the decision is NOT `fresh-execution` in exactly that shape, and assert the inspected lane id is the PRIOR one, so a regression that reads the turn's own empty lane fails loudly instead of silently disabling the feature. (b) a prior lane holding ONLY an INTERRUPTED SNAPSHOT commit routes `fresh-execution`, proving the completeness signal works and that the plan does not blanket-skip whenever commits exist; (b2) a real commit whose BODY merely quotes the snapshot phrase still routes `verify-and-continue` (the E-02 subject-only rule). (c) no recorded prior lane, an absent prior lane, and an empty prior lane all route `fresh-execution`; (d) an unreadable recorded lane routes `fresh-execution` with a reason (E-03); (e) a FIRST attempt is untouched and its prompt is byte-identical to today's; (f) both drivers agree across the whole matrix, which after E-04's delegation means asserting the Antigravity twin resolves to the OpenCode implementation.

  Assert on the routing decision and on prompt CONTENT (the prior lane's branch name and shas present in the verify prompt), never on the mere presence of the word "recovery", which appears in unrelated prose and would pass against a stub. Also assert the classifier ran no git write: capture the prior lane's tip sha and tree state before and after and prove both unchanged.
  - Depends on: E-05
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_resumedupe.py` passes, `tests/test_lane_allocation_idempotent.py` still passes, and each case was verified to FAIL when its branch is deliberately broken.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease.inspect_lane` (`:203`) is the non-mutating lane classifier and its docstring states it "never runs a write command". It already reports `commits_ahead`, `dirty`, the lane's own base sha and one of five `LANE_STATES` (`:103`), so the driver needs no new probing.
- ALLOCATION NEVER REUSES A LANE HOLDING WORK. `allocate_worktree` (`worktree_lease.py:495`) adopts only an EMPTY lane at the requested base and otherwise ATTEMPT-SCOPES to `<id>:attemptN`, leaving the old lane byte-identical (`:512-529`). So on a resume the turn's own lane is empty and the prior work is on `handle.displaced_from`. This is the single most important convention for this plan; E-01 is built on it.
- Never reconstruct a lane branch name from an id6: `lane_branch_name`'s docstring (`worktree_lease.py:69-73`) forbids it because allocation may have attempt-scoped the name. Read the recorded `preserved_lane_id`/`worktree_lane_id` instead.
- `preserved_worktree`/`preserved_branch`/`preserved_lane_id`/`preserved_base` are written at `oc_runipd.py:5415-5420` precisely so a later turn can find a preserved lane, and `zwnjp3` recorded that they were once "WRITTEN and never READ" (`oc_runipd.py:1514`). This plan is a second legitimate consumer.
- The recovery prompt deliberately has NO acknowledgement gate and NO refusal path, stated in `build_recovery_lane_notice`'s docstring: "a refusal would be one more way for an unattended run to stall". Preserve that; `tests/test_lane_allocation_idempotent.py:709-717` enforces it by scanning the function body.
- The INTERRUPTED SNAPSHOT message is written in one place (`worktree_lease.py:699-700`) but its phrasing is hardcoded again as prose in both drivers, at `oc_runipd.py:3759` and `agy_runipd.py:2380`.
- The shipped way to share driver text is DELEGATION, not copy: `agy_runipd.build_isolation_notice` (`:2388-2396`) imports and calls the OpenCode implementation. The pending `rununify` Set owns wholesale de-duplication, so new logic must be shared this way, not copied.
- Preserving work beats tidiness: `oc_runipd.py:5409-5412` keeps a non-integrated lane on purpose under a "forward-progress rule: never discard work", and interrupt reclamation leaves a HOLDS-WORK lane "ENTIRELY ALONE" (`:1691-1695`). The plan's original `oc_runipd.py:2501` citation for this was stale and pointed at an unrelated selector function.

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The item's own first suggestion (Q1, put the lane state in the prompt) IS ALREADY BUILT, so it cannot be the fix.** `build_recovery_lane_notice` already renders the lane branch and path, "it HOLDS N commit(s) beyond its base", "its tree has uncommitted changes", and an explanation of the INTERRUPTED SNAPSHOT marker. The duplication was measured after `zwnjp3` E-11 landed that notice. | The function read in full at `oc_runipd.py:3692-3762` (line numbers corrected at review; it was cited as `:3485`). |
| F-2 | **So this is decisive evidence that informing is necessary and NOT sufficient.** The agent was told it was resuming, was told its lane already held commits, and still redid the work. That is the argument for moving the judgment to the driver (the item's Q2) rather than strengthening the prose again. | F-1 plus the measured duplication on `ntf6sx`. |
| F-3 | **The driver already has every fact it needs, so this is a routing change and not new observation machinery.** `inspect_lane` is non-mutating by contract and already returns `commits_ahead`, `dirty`, the lane base and a five-value state classification, and the prior lane's identity is already recorded durably. | `worktree_lease.py:203-214`, `LANE_STATES` at `:103`, and the `preserved_*` writes at `oc_runipd.py:5415-5420`. |
| F-4 | **A blanket "skip if commits exist" would be WRONG, and the shipped snapshot commit is the signal that makes it safe.** A turn interrupted mid-edit may have committed something incomplete, in which case redoing it is correct. `worktree_lease.py:699` writes `WIP INTERRUPTED SNAPSHOT (not finished work)` for exactly that case, explicitly "NOT validated or reviewed work", which lets the classifier separate preserved-mid-edit from finished. | `worktree_lease.py:695-706`. |
| F-5 | **The marker's phrasing is duplicated as prose in both drivers, so it can drift.** `oc_runipd.py:3759` and `agy_runipd.py:2380` each hardcode the phrase in prompt text while `worktree_lease.py:699-700` writes the actual commit message. A classifier keying on a third copy would be a fourth place to drift; E-02 collapses this to one constant. | The three cited sites (the two driver line numbers were corrected at review from `:3552`/`:2375`, which pointed at unrelated code). |
| F-6 | **Measured cost, and the honest reason this is not urgent.** Roughly one full turn per resumed item, with a turn ranging about $3 to $30 in the observed runs. Nothing is lost and the resulting trees are correct, so this is wasted spend plus a lane history a human must read at merge time. It carries no `Blocks-Release` gate, unlike `vju5ba`. | Backlog `k1nity`; the item's own NOT A DATA-SAFETY BUG note. |
| F-7 | **This compounds `vju5ba`, whose plan is ALREADY EXECUTED.** With validation off nothing self-finalizes, so lanes accumulate and resumes become more likely. `vju5ba` graduated as plan `evgi9n`, now in `.aw/records/plans/executed/` with `- Status: executed`, so its frequency-reducing effect has landed and this plan has no remaining sequencing dependency on it. `Item-Dependencies: none` is therefore correct. | `.aw/records/plans/executed/20260831-novalnomerge-01-evgi9n-...ipd.md:9`. |
| F-8 | **REVIEW FINDING: the graduating measurement was mechanically wrong and would have produced a test that pins the wrong behavior.** `7e9c4444` is a MERGE with parents `144f3347` and `5b8c0004`, and `fb0774b2` is an ancestor of it, so `git diff fb0774b2 7e9c4444` over any path is empty BY CONSTRUCTION and is not evidence of re-execution. `git log --oneline 7e9c4444 --not 144f3347 5b8c0004` returns only the merge itself, so attempt 2 authored NO duplicate feature commit for ntf6sx. Further, the second `lifecycle` commit was LEGITIMATE: the merge's own combined diff reverted the plan from `executed/` back to `pending/` and its `Status: executed` back to `Status: approved`, so `3558ce1f` re-did a lifecycle move the merge had undone. E-06 therefore uses `zhr6mc`, not `ntf6sx`. | `git cat-file -p 7e9c4444` (two parents); `git merge-base --is-ancestor fb0774b2 7e9c4444` succeeds; `git diff-tree --cc 7e9c4444`; content diff of the plan file at `5b8c0004` vs `7e9c4444`. |
| F-9 | **REVIEW FINDING: the underlying bug is nonetheless REAL, on a different pair, so the plan's purpose survives its bad citation.** `zhr6mc` has two sibling commits with the identical subject `feat(runner): close a backlog item when the run executes its last carrier` on INDEPENDENT parents (`42b38acf`->`bcbbfb07`, `8a9b8f32`->`144f3347`), 2118 vs 2260 insertions across the same four files; only the second was merged and the first was retired as "provably superseded". `bmh754` repeats the shape (`c823390f`->`bcbbfb07`, `8c437188`->`144f3347`, same four files). That is a full turn performed twice. | The two commit pairs above; retirement note in `ecec8270`. |
| F-10 | **BLOCKER REVIEW FINDING: as written the plan would have been INERT, because it classified the wrong lane.** `allocate_worktree` never reuses a lane holding work: it classifies it `HOLDS-WORK` and attempt-scopes alongside it (`worktree_lease.py:512-529`). MEASURED in a throwaway repo: after one real commit on lane `ntf6sx`, re-allocating returned `ntf6sx:attempt2` (`disposition=attempt-scoped`, `displaced_from=aw/lane/ntf6sx`), with `inspect_lane` reporting the NEW lane `EMPTY commits_ahead=0` and the OLD one `HOLDS-WORK commits_ahead=1`. A classifier reading the turn's own lane would return `fresh-execution` on every resume, shipping a feature that changes nothing while its tests passed. E-01 now resolves the PRIOR lane from `preserved_lane_id`/`attempts[-1].worktree_lane_id`/`displaced_from`, and E-06 (a2) adds an explicit inertness guard. | The measured probe; `worktree_lease.py:495-576`; `oc_runipd.py:5415-5420`. |
| F-11 | **REVIEW FINDING: three of the plan's line citations were stale, one badly enough to mislead an executor.** `oc_runipd.py:3485` is `*,` (the function is at `:3692`), `:3552` is an unrelated scheduler comment (the prose site is `:3759`), `:2501` is a selector signature rather than the never-discard rule (`:5409-5412`), and `agy_runipd.py:2375` is a bare `"",` (the prose site is `:2380`). Corrected throughout; the plan now anchors on SYMBOL names as well as lines. | `sed -n` at each cited line, run at HEAD `4541aa7c`. |

## Proposed changes (ordered, validatable)

1. A pure classifier over the shipped `inspect_lane` reading of the PRIOR attempt's (displaced) lane, resolved from durable state and never from a reconstructed name, returning a typed routing decision (E-01), with the snapshot marker collapsed to one shared constant matched on the subject line (E-02) and an explicit fail-toward-executing choice for unreadable lanes (E-03).
2. A verify-and-continue dispatch carrying the prior lane's branch, real shas and diffstat, extending the existing recovery notice with the Antigravity twin delegating to the OpenCode definition (E-04).
3. Durable recording of the routing decision and its inputs (E-05).
4. Sabotage-verified tests including a reconstruction of the measured duplication (E-06).

## Deferred / out of scope (with reason)

- **Strengthening the recovery prompt's prose further.** Explicitly rejected: F-1 shows the prompt already carries the lane facts and F-2 shows that was insufficient. More prose is the approach this plan exists to replace.
- **An acknowledgement gate requiring the agent to confirm it inspected the lane.** The maintainer chose the lightweight notice over exactly this, and `build_recovery_lane_notice`'s docstring records why: a refusal path is another way for an unattended run to stall. E-04 preserves that.
- **Automatically amending, squashing or discarding duplicate commits already on a lane.** Cleaning history is a separate concern from not creating the duplicate, and it conflicts with the shipped never-discard-work rule (`oc_runipd.py:2501`).
- **De-duplicating the two drivers.** Owned by the pending `rununify` Set; this plan adds a shared helper consumed by both.
- **Detecting duplication AFTER the fact and reporting it.** Would be useful diagnostics but does not save the spend, which is the item's point. E-05's recorded decision gives most of the diagnostic value for free.

## Scope check

- Over-scope: RULED AT REVIEW (D-1). `agent_workflows/worktree_lease.py` is now DECLARED in Scope-Paths, and E-02 defines the constant there. That module is the correct home because it is the one that WRITES the snapshot message (`:699-700`), and the dependency direction permits it: `worktree_lease.py` imports neither driver, while both drivers already import it (23 and 21 references), so there is no cycle. Defining the constant in a driver and importing it back into `worktree_lease.py` WOULD create one. The alternative of leaving it undeclared was rejected: `finalize_precheck` computes the out-of-scope delta against the declared fence (`ipd_lifecycle.py:1277-1293`) and would demand a per-path `--scope-reason` for an edit that is legitimately part of the design.
- Under-scope: no third driver exists; the recovery-notice sites are exactly `build_recovery_lane_notice` in `oc_runipd.py:3692` and `agy_runipd.py:2313`.
- In-scope-unmodified risk: none expected. All four declared paths are edited (`worktree_lease.py` by E-02, both drivers by E-02/E-04/E-05, the test file by E-06).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_resumedupe.py` for per-test counts.
- `python3 -m pytest -o addopts="" tests/test_lane_allocation_idempotent.py` as a regression check on the constraints that file pins (driver symmetry, no acknowledgement gate, snapshot description).
- The full suite BARE, `python3 -m pytest`, from the PRIMARY checkout. Re-measure the baseline on unmodified HEAD at execution time rather than trusting the recorded `3864 passed, 3 skipped, 4 xfailed`, which predates commits `8ced15ce` and `cdef9c90`. Validate in the primary checkout, never a scratch worktree (`dh0uno`).
- A real interrupted-then-resumed run showing the second turn did NOT re-do the prior attempt's work. State the proof as SIBLING-PAIR ABSENCE, not as an empty diff: paste `git log --oneline` for the prior and current lanes and show there is no pair of same-subject commits on INDEPENDENT parents (the `zhr6mc` shape, `42b38acf` vs `8a9b8f32`). Do NOT reuse the `ntf6sx` `git diff <first> <second>` form: F-8 shows an empty diff there is guaranteed by ancestry and proves nothing.
- `aw ipd lint --phase pre-transition` conforming on this plan.

## Spec / documentation sync

- No spec change: no shipped spec asserts how a recovery turn is dispatched.
- If the routing decision becomes operator-visible in the run report, the report's own documentation should name the three dispositions; otherwise N/A.

## Open questions

### OQ-01: Should `verify-and-continue` be allowed to conclude "already complete" and finalize without any further edit?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED YES AT REVIEW, but on a CORRECTED basis, because the original rationale overstated the backstop and the correction changes what E-04 must say. Two errors: the `ntf6sx` example does not support the claim (F-8: the second turn's work was a legitimate re-do of a lifecycle move the merge reverted, not a no-op), and `finalize_precheck` is at `ipd_lifecycle.py:1184`, not `:1055`. What it actually enforces, read at HEAD: a receipt whose plan-content digest still matches (`:1210-1219`), a usable `base_head` (`:1222-1228`), a fail-closed `pre-transition` lint (`:1233-1254`), and a COMPUTED two-way scope delta that it deliberately does NOT refuse on (`:1325-1327`, "The precheck itself no longer REFUSES on out-of-scope paths"). The `E-*`/`V-*` completeness requirement comes from the pre-transition LINT, not from the precheck directly. That is still a real gate, so YES stands: a verify-and-continue turn cannot finalize a plan whose checklists are unmarked or whose evidence is empty. But the gate is checklist-and-evidence shaped, so a turn that concludes "already complete" MUST still fill in evidence from the prior lane's actual work rather than asserting completion, and E-04's prompt must demand exactly that.

### OQ-02: Should the classifier also compare the lane's diff against the plan's `Scope-Paths` to judge whether the work is THIS plan's?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW as deferred, and the corrected lane model STRENGTHENS the reason rather than weakening it. Attribution is even more direct than the original rationale claimed: the prior lane is not merely "named for the item", it is the exact lane id recorded in this item's own durable state at `oc_runipd.py:5415-5420` (or `handle.displaced_from`), so a lane reached that way is this item's by construction and needs no path comparison to prove it. `finalize_precheck` still performs the authoritative reconciliation later (`ipd_lifecycle.py:1277-1305`), so a second, weaker scope judgment here could only disagree with it. Not adopted.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the classifier's decision for five constructed cases (a prior lane with 2 real commits WHILE the current lane is a fresh attempt-scoped lane at 0 commits; no prior lane recorded; prior lane absent; prior lane empty; prior lane snapshot-only) showing `verify-and-continue`, `fresh-execution`, `fresh-execution`, `fresh-execution`, `fresh-execution` respectively. THE INERTNESS PROOF IS MANDATORY: paste the resolved lane id the classifier actually inspected in case 1 and show it is the PRIOR lane, not the turn's own, alongside the `inspect_lane` reading of BOTH lanes (prior `HOLDS-WORK`, current `EMPTY`). Paste the prior lane's tip sha and `git status --porcelain` before and after the call, showing both unchanged, rather than asserting non-mutation in prose.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the constant's definition site in `worktree_lease.py` and the output of a grep proving every consumer (both driver prose sites and the classifier) references it rather than re-spelling the phrase; plus the classifier's decision on a snapshot-only prior lane showing the marker was honored, AND on a real commit whose BODY quotes the phrase showing it still routes `verify-and-continue` (the subject-only rule).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the decision and recorded reason for a deliberately unreadable lane, showing `fresh-execution` rather than a skip, and quote the comment recording the deliberate asymmetry against the fail-closed lifecycle gates.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the generated `verify-and-continue` prompt showing the PRIOR lane's branch name, ACTUAL commit shas and diffstat, and the instruction to bring work forward into the agent's own lane; confirm by grep that it contains no `git checkout`/merge/commit instruction targeting the displaced branch. Paste a `fresh-execution` recovery prompt diffed against today's text to prove it is byte-identical, and a first-attempt prompt likewise. Show the Antigravity twin DELEGATES (paste the function body) rather than duplicating. Paste the passing output of `python3 -m pytest -o addopts="" tests/test_lane_allocation_idempotent.py`, which pins the no-acknowledgement-gate constraint.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the durable state excerpt and the event record for one routed run, showing the disposition, the INSPECTED LANE ID (so a future reader can tell which lane the decision was based on), `commits_ahead`, snapshot presence and reason; confirm a re-executed run and a verify-and-continue run are distinguishable from state alone.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the COMPLETE `python3 -m pytest -o addopts="" tests/test_resumedupe.py` output with per-test names and exit code, PLUS for each of the cases (a), (a2), (b), (b2), (c), (d), (e), (f) the FAILING output produced when its branch is deliberately broken, then confirm each break was reverted. Case (a2)'s sabotage MUST be specifically "make the classifier read the turn's own lane instead of the prior one" and MUST fail, since that is the inert-feature regression. Also paste the bare full-suite summary line, re-measuring the baseline at execution time (`python3 -m pytest` on unmodified HEAD) rather than trusting the recorded `3864 passed, 3 skipped, 4 xfailed`, and explain any delta change-by-change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and requires explicit human approval before execution. It changes whether an item's work is executed at all on a resume, so there are TWO dangerous failures and neither may be waived. First, a SKIPPED implementation: E-03's fail-toward-executing choice and V-03 exist to make that direction impossible. Second, and identified at review, an INERT feature that appears to work: if the classifier reads the turn's own (freshly attempt-scoped, always empty) lane instead of the prior one, every resume routes `fresh-execution`, the tests pass, and nothing changes (F-10). E-06 case (a2) and V-01's inertness proof exist for exactly that, and are as mandatory as V-03.

Execution contract: commit only files this plan changed, path-scoped, and never push. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`). Report validation by pasting the ACTUAL runner output; never claim a test result you did not run. On completion, move this plan to `.aw/records/plans/executed/` with `- Status: executed` per the `ipd-lifecycle` workflow.

Scope fence (a DECLARATION, so the runner can reconcile afterwards): the four declared Scope-Paths are `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/worktree_lease.py`, and `tests/test_resumedupe.py`. The `worktree_lease.py` scope question is RULED (see Scope check, D-1) and needs no further decision. An edit outside that set is permitted but must be JUSTIFIED with a per-path `aw ipd finalize --scope-reason`, and a declared path left unmodified with a `--scope-ack`. Do NOT stop over a scope question. Do stop and report if a file you must edit is being changed concurrently and the two sets of changes cannot be safely combined.

Post-gate lifecycle: on completion move this plan to `.aw/records/plans/executed/` with `- Status: executed`, per the `ipd-lifecycle` workflow, only after every `V-*` above carries pasted evidence.
