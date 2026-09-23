# IPD: Backfill Priority and Work-Kind on the 84 pending plans that can inherit from their source item

- Date: 2026-09-10
- Kind: child
- Concern: Most pending plans record the backlog item they graduated from, every one of those references resolves, and every source carries both `Priority` and `Work-Kind`. So those plans can be given both values with no judgement call, purely by inheriting from a source the plan itself names. RE-MEASURED AT REVIEW (2026-09-12, HEAD `fe57b1a4`), because the authored figures are stale: 120 pending plans (authored 104), 92 carrying `- From-Backlog:` (authored 84), 0 dangling, 0 sources missing a field, 11 plans ALREADY carrying both fields, so the real backfill population is 81 and the no-source remainder is 28 (authored 20). Do NOT re-quote these either; E-01 re-derives them.
- Scope: Inherit `Priority` and `Work-Kind` from each pending plan's `- From-Backlog:` source, writing them through the shipped `aw ipd set` setters rather than by hand. Does NOT decide a value for any plan lacking a source (sibling 03 owns those), does NOT touch terminal plans, and does NOT change any vocabulary or add a sort key.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: planprio
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8u6770
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-13 approved (aw set): set Item-Dependencies to none
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-12 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (BLOCKER, OPEN, inherits the parent's blocking OQ-02), PR-002 (HIGH, OPEN and escalated to blocking OQ-02 on this plan), PR-003..PR-011 FIXED; readiness `no-go` because two blocking questions remain. Record: `.aw/records/reviews/20260910-planprio-02-8u6770-backfill-priority-and-work-kind-on-the-84-pending-plans-that.review.md`. `aw ipd lint --phase author` CONFORMING (clean, 0 findings) before semantic review. Suite measured bare at HEAD `fe57b1a4`: `5971 passed, 3 skipped, 2 xfailed in 59.68s`. DISCLOSURE: same agent/model family authored this Set, so treat as a near-self-review; its value rests on what was EXECUTED.
  THE PLAN'S THESIS IS CORRECT AND ITS SHAPE IS RIGHT. Inheritance really is judgement-free and really does work: RE-MEASURED at this HEAD, 92 pending plans carry a `- From-Backlog:`, ZERO references dangle, ZERO sources are missing either field, and the inherited values are a genuine spread. Using the shipped setter rather than hand-editing is the right call. None of that was changed.
  THE BLOCKER IS ONE THIS PLAN INHERITS RATHER THAN CAUSES, and it is already escalated on the parent. `- Item-Dependencies: executed:lkexaw` is exactly the edge the parent's review found stranding 18 already-approved pending plans (parent PR-001, blocking parent OQ-02, three costed options with "stamp inside Order 01" recommended). This child's own gate section justifies that edge in prose the parent's review measured to be FALSE ("backfilling before the gate exists would write values nothing enforces": a value written before the gate exists is precisely what the gate then finds satisfied). The edge may be REVERSED or REMOVED by the parent's answer, so this plan must not execute until it is settled, and its own justification is now marked as superseded rather than left to be re-inherited.
  THE SECOND ESCALATION WAS FOUND BY DRIVING THE SETTER, NOT BY READING ITS `--help`. On a plan whose status is ALREADY the one passed, `aw ipd set <same-status> <id6> --priority p --work-kind k` writes both fields correctly AND appends a history line reading `status set to approved`, asserting a transition that did not happen. Measured in a throwaway copy on `5e4sb6` (`approved`): the diff shows the two fields added, `- Status:` unchanged, and that false line at the top of the history. 5 of the 81 plans are `approved`, so 5 records would carry a fabricated approval event, and this Set's own purpose is to make plan metadata trustworthy. Passing `--message` REPLACES the false text with the supplied note (verified), so a remedy exists; whether one line per plan is acceptable at all is the maintainer's call. Escalated as blocking OQ-02 here.
  THREE FURTHER MEASURED HAZARDS THE PLAN DID NOT NAME. (1) A SETID SELECTOR WOULD REVERT EXECUTED PLANS: 6 of the 57 setids in the population also name a terminal plan, and `aw ipd set approved rununify --dry-run` reports `executed -> approved` on TWO plans in `executed/`. That is backlog `f5pttg`, a shipped high-priority defect where this exact command silently reverted seven executed plans. E-03 now mandates id6 selectors and a `--dry-run` preflight. (2) `--no-commit` IS REQUIRED or the setter offers to commit mid-loop, which in a shared checkout is how another agent's staged work gets swept. (3) V-04 prescribed two commands that CANNOT produce what they ask: a piped `aw att --type plan` has no Priority column (it exists only in the colored renderer), and `aw check plans` is 140 errors deep before this plan touches anything.
- 2026-09-10 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored after the maintainer chose the full option ("enforce at the gate, fix creation, inherit the 84, decide the 20") on 2026-09-10, having asked whether fixing the pending corpus was worth it at all. IT IS WORTH IT PRECISELY BECAUSE MOST OF IT NEEDS NO JUDGEMENT, which is what the measurement showed. MEASURED AT AUTHORING over the 104 pending plans: 84 carry a `- From-Backlog:` id6, ZERO of those references dangle, and ZERO of the resolved sources are missing either field, so all 84 inherit cleanly. The inherited distribution is a real spread rather than a single default: 26 `high`/`bug`, 25 `medium`/`bug`, 11 `medium`/`feature`, 10 `high`/`feature`, 6 `medium`/`chore`, 3 `low`/`feature`, 1 each of `medium`/`followup`, `high`/`security`, `low`/`followup`. A SETTER ALREADY EXISTS AND MUST BE USED: `aw ipd set` carries `--priority` and `--work-kind`, both documented as persisting "on a no-op transition", so this backfill needs no hand-editing of front matter.

## Goal

Give 84 pending plans their two missing fields by inheritance, so the attention board's Priority column is populated for most of the queue without anyone guessing a value.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: derive, then verify, then write

- [x] E-01 RE-DERIVE THE INHERITANCE TABLE AT EXECUTION TIME AND PRINT IT, one row per plan: the plan's id6, its CURRENT `- Status:`, its `- From-Backlog:` source id6, the source's `Priority` and `Work-Kind`, and the source's own file path. DO NOT REUSE ANY COUNT FROM THIS PLAN OR ITS PARENT. Both authored figures and review figures are historical; derive a third and record the difference.
  EXCLUDE A PLAN THAT ALREADY CARRIES BOTH FIELDS, which the authored item never said and which changes the population. Measured at review: 11 pending plans already carry both, so the set needing a write is 81 of the 92 with a resolving source, not 92. Writing over an existing value would overwrite a deliberate choice with an inherited one, which is a silent downgrade rather than a backfill. A plan carrying exactly ONE of the two fields is IN scope for the missing field only, and the table must say which.
  RECORD THE STATUS PER ROW, because it decides the setter invocation and it is where the danger is. Measured at review, the 81 split 76 `reviewed` and 5 `approved`, and the `approved` five are the ones E-03's history-line problem applies to (OQ-02).
  PARENT COUNTS FOR ORIENTATION ONLY, not to be quoted as findings: the parent's review measured 120 pending, 92 with a resolving source, 81 still needing a field, 28 with no source.
  RESOLVE, DO NOT PARSE. A `- From-Backlog:` id6 must be resolved to an actual backlog file, exactly as `check.from-backlog-dangling` already does. A dangling reference must be REPORTED and SKIPPED, never guessed at, and never silently treated as a plan with no source (that would move it into sibling 03's population without anyone deciding to). Measured at review: zero dangle today, so a dangling reference appearing at execution time is NEW and worth reporting as such.
  - Depends on: none
  - Expected outcome: a printed per-plan table carrying id6, current status, source id6, the source's two values and its path; the count stated and compared to review's 81; plans already carrying both fields listed as EXCLUDED; any dangling reference named and excluded.
  - Execution state: performed
  - Execution note: A THIRD DERIVATION WAS TAKEN AND IT DIFFERS FROM BOTH EARLIER ONES BY MORE THAN DRIFT (HEAD `e96dc154`, 2026-09-23): 54 pending plans, not the authored 104 nor review's 120; 33 carrying `- From-Backlog:`, not 84 nor 92; 32 resolving; 2 already carrying both; WRITE POPULATION 30, not the authored 84 nor review's 81. THE COLLAPSE IS REAL WORK LANDING, not a derivation error: the intervening 11 days executed most of the corpus review measured, so 619 of the 712 plans `aw att` now reports are `executed`. This is exactly why the item forbids re-quoting a count. Derivation used the SHIPPED readers (`backlog.parse_item`, `ipd_schema.parse_metadata_block`), resolving each source id6 against `backlog._iter_items` rather than parsing it. ONE DANGLING REFERENCE, which review measured as zero and is therefore NEW: `nmlx47` carries `- From-Backlog: dstnso, 8hx3g3`, a MULTI-VALUED field no shipped reader can resolve; excluded and reported, never guessed at. Filed as backlog `6os96s`. PER-STATUS SPLIT: all 30 are `approved`, none `reviewed`, which INVERTS review's 76/5 reading and means the OQ-02 history-line question applies to all 30 rather than 5.

- [x] E-02 SANITY-CHECK THE DERIVED VALUES BEFORE WRITING ANY, because inheritance is only as good as the sources. Report the distribution and inspect the tails: any source whose `Priority` is absent or outside `low|medium|high`, any whose `Work-Kind` is outside `bug|feature|chore|security|followup`, and any plan whose inherited `Priority` disagrees with its own `- Blocks-Release:` state in a way worth flagging (a release-blocking plan inheriting `low` is not necessarily wrong, but it should be SEEN rather than written silently).
  DO NOT CORRECT A SOURCE ITEM. If a source's value looks wrong, report it; editing backlog items is outside this plan's declared scope and belongs to whoever owns that item.
  REVIEW ALREADY RAN THIS CHECK, so the executor knows what to expect and a divergence is itself informative. Measured at HEAD `fe57b1a4` over the 81: ZERO out-of-vocabulary and ZERO absent source values, so every source is clean. The inherited distribution is 25 `high`/`bug`, 25 `medium`/`bug`, 10 `high`/`feature`, 9 `medium`/`feature`, 6 `medium`/`chore`, 3 `low`/`feature`, 1 each of `medium`/`followup`, `high`/`security`, `low`/`followup`. And the release-blocking tail is 17 of 81, ALL of them `medium` and NONE `low`, which is the specific list OQ-01 exists to have a human see.
  - Depends on: E-01
  - Expected outcome: the distribution printed and compared to review's, every out-of-vocabulary or absent source value named (expect none), and every release-blocking plan inheriting `low` or `medium` listed with its id6 for a human to see (expect about 17, all `medium`).
  - Execution state: performed
  - Execution note: EVERY SOURCE IS CLEAN, matching review's expectation: 0 out-of-vocabulary values and 0 absent values across all 30, checked against the SHIPPED vocabularies `backlog.PRIORITIES` (`high|low|medium`) and `backlog.KINDS` (`bug|chore|feature|followup|security`) rather than a hand-copied list. INHERITED DISTRIBUTION over the 30: 7 `medium`/`bug`, 7 `medium`/`chore`, 6 `high`/`bug`, 4 `high`/`followup`, 3 `high`/`feature`, 3 `medium`/`feature`. The shape survives the population collapse (a genuine spread, no single default), though `high`/`followup` is new and `low` has vanished entirely. NO SOURCE BACKLOG ITEM WAS MODIFIED: `git status --porcelain -- .aw/records/backlog` is empty. THE RELEASE-BLOCKING TAIL IS 13 OF 30 and it DIVERGES FROM REVIEW'S READING: review measured all 17 as `medium`, whereas 6 of these 13 inherit `high` and 7 `medium`; ZERO inherit `low`, so OQ-01's feared case (a release blocker landing at `low`) still does not occur and the question stays non-blocking. The 13 named: `k311gw`, `p9j6c0`, `s0gnha`, `svacmz`, `w33lrl`, `z1yefm` (`high`); `40it5e`, `5e4sb6`, `bxx9af`, `dy9ymn`, `i8u6hh`, `xo3244`, `yeh7gc` (`medium`).
    ONE TAIL THE ITEM DID NOT ASK FOR, SURFACED BECAUSE THE REPO GAINED A RULE AFTER THIS PLAN WAS AUTHORED: `lyo1tz` and `1f7xno` inherit `Work-Kind: bug` while carrying NO `- Blocks-Release:`, which is the shape AGENTS.md's "Every live bug gates the next release" forbids. They are NOT gated here, and the reason is mechanical rather than a judgement dodge: the shipped rule `check_engine.check_live_bug_gate` scans BACKLOG ITEMS ONLY (`backlog._iter_items`), never plans, so no rule fires on either; and their shared source `cnwy8g` is itself an ungated live bug already flagged `check.live-bug-ungated` at baseline, so the honest inheritance is the absent gate. Writing `Blocks-Release: next` onto them would be a NEW gating decision this plan's Scope forbids, and it would also contradict `check.from-backlog-gate-mismatch`, which compares a carrier's gate to its item's. Recorded as DECISION 03-8u6770-D2; `cnwy8g` is the artifact that needs the gate.

- [x] E-03 WRITE THE VALUES THROUGH THE SHIPPED SETTER, one plan at a time, using the EXACT form review verified: `aw ipd set <that-plan's-current-status> <id6> --priority <p> --work-kind <k> --message "<why>" --no-commit --yes`. Every element of that line is load-bearing and three of them were added at review.
  USE THE id6, NEVER A SETID, AND THIS IS THE ITEM'S SHARPEST HAZARD. A setid selector resolves to EVERY plan carrying it, including terminal ones. MEASURED at review: 6 of the 57 setids in this population also name a plan in `executed/`, and `aw ipd set approved rununify --priority medium --work-kind chore --dry-run` reports `executed -> approved` on TWO plans in `executed/`. That is backlog `f5pttg`, a shipped high-priority defect recording that this exact command silently reverted seven executed plans in one invocation. The affected setids measured at review: `hostdefault`, `integearn`, `integpath`, `lanectn`, `rununify`, `setidhard`.
  DRY-RUN EVERY INVOCATION FIRST AND READ ITS OUTPUT. `--dry-run` is honored on this path (verified: it prints the would-be transition and writes nothing). If a dry-run line reads anything other than `unchanged` for exactly the one plan you named, STOP: you have selected more than you meant to. This is the unsafe-condition stop, not a scope stop.
  PASS `--no-commit`. Without it the setter offers to commit, and in this shared checkout accepting that offer mid-loop is how another agent's staged work gets swept into your commit. Commit deliberately at the end, path-scoped, after verifying the index.
  PASS `--message`, WHICH IS NOT OPTIONAL POLISH BUT THE FIX FOR A FALSE HISTORY CLAIM (OQ-02). MEASURED at review on `5e4sb6` (`approved`): without `--message`, a same-status call appends `- <date> approved (aw set): status set to approved`, asserting a transition that did not occur; with `--message`, that line carries the supplied text instead. Supply something true, naming the source item, for example "Inherited Priority/Work-Kind from source backlog item <src-id6>; status unchanged." DO NOT PROCEED PAST THE FIRST `approved` PLAN UNTIL OQ-02 IS ANSWERED, because whether writing any history line onto an approved plan is acceptable is the maintainer's call; the 76 `reviewed` plans are unaffected by that question.
  DO NOT HAND-EDIT FRONT MATTER, and do not batch-rewrite with a script that writes the lines directly. The setter owns field position and history, and a direct write would bypass both. If the setter cannot express a case, report it rather than working around it. NOTE the setter inserts both fields directly after `- Status:` (verified), which differs from where a hand-editor would likely put them; that is the setter's choice and is correct.
  THE NO-OP WRITE IS VERIFIED TO WORK ON BOTH STATUSES IN THIS POPULATION, so no discovery is needed: driven at review in a throwaway copy, `reviewed` and `approved` both accepted the call, exited 0, printed `unchanged`, and wrote both fields with `- Status:` untouched. What the authored item called an unknown ("a no-op transition on some statuses may refuse") is settled for the two statuses that actually occur here.
  - Depends on: E-02
  - Expected outcome: every derived plan carries both fields with the inherited values; every invocation used an id6, a dry-run preflight, `--no-commit` and a truthful `--message`; no plan's `- Status:` changed; no plan outside the derived table was touched; OQ-02's answer recorded before any `approved` plan was written.
  - Execution state: performed
  - Execution note: 30 INVOCATIONS, each `aw ipd set approved <id6> [--priority P] [--work-kind K] --message "<provenance>" --no-commit --yes`, every one exiting 0 and printing `unchanged`. Result: 30 `Priority` lines and 27 `Work-Kind` lines written (3 plans already carried `Work-Kind: bug` and received the missing field ONLY, per E-01's partial rule: `s0gnha`, `dy9ymn`, `svacmz`).
    THE REHEARSAL CAME FIRST AND CONFIRMED BOTH REVIEW MEASUREMENTS, in a throwaway copy under the gitignored `.aw/state/` (never in this checkout, never committed, discarded after). Without `--message`, `5e4sb6` gained the FALSE line `- 2026-09-23 approved (aw set): status set to approved` on a plan that did not transition; with `--message` the same call wrote the supplied provenance instead. The partial case was rehearsed too (`s0gnha` with `--priority` alone added exactly one field line).
    THE SETID HAZARD WAS DRIVEN, NOT ASSUMED, AND IT IS NOW BLOCKED RATHER THAN MERELY DANGEROUS. `aw ipd set approved rununify --dry-run` in the rehearsal copy REFUSED outright: `refusing to move 11 plan(s) BACKWARDS out of a terminal disposition`, naming all 11 and writing nothing. So the `f5pttg` defect this item's sharpest warning is about has been FIXED since review (its item reads `done`, closed by plan `4bc1nd`), and a setid selector would now fail closed rather than silently revert. The id6 discipline was kept anyway: every one of the 30 calls used an id6, and E-04 proves the terminal directories stayed clean.
    THE DRY-RUN PREFLIGHT RAN AS A COMPLETE SEPARATE PASS over all 30 before any real write, with a machine-checked stop condition (exit 0, exactly ONE output line, containing `unchanged`, naming the plan we selected). 30 of 30 satisfied it; 0 stop-conditions. No hand-edit of front matter was used anywhere, and the setter placed both fields directly after `- Status:` as review recorded.
    OQ-02 APPLIES TO ALL 30, NOT 5, because every plan in the population is `approved`; the maintainer's Ruling 1 answer (write with a truthful `--message`) covers them identically, so no plan was deferred. Each message names its source item, states which fields were backfilled, and says explicitly `no lifecycle transition occurred`.

- [x] E-04 PROVE NOTHING ELSE MOVED, which matters because this plan edits roughly 81 files in a shared checkout. Show that only the two field lines and each plan's history changed, that no plan's `Status`, `Readiness`, `Set`, `Order` or `Id` differs, and that `aw check plans` and `aw ipd lint` report NO NEW rule id and no increased count.
  PROVE NO TERMINAL PLAN WAS TOUCHED, which is the specific proof that a setid mis-selection did not happen: `git status --porcelain -- .aw/records/plans/executed .aw/records/plans/superseded .aw/records/plans/not-executed` must be EMPTY. Given the measured 6-setid collision, this is the assertion that would have caught `f5pttg` before it committed.
  DO NOT REQUIRE `aw check plans` TO BE CLEAN. Measured bare at review (HEAD `fe57b1a4`), it exits 1 with `errors 140  warnings 0`, none of it caused by this plan: 124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`. Capture that count BEFORE the first edit and compare. An executor told to make it clean would either stall or "fix" other agents' plans, which the shared-checkout rule forbids.
  RE-VERIFY THE INDEX BEFORE EACH COMMIT. Other agents are committing concurrently; `git diff --cached --name-only` must contain only plans this item changed, and a failed hook invalidates that check (re-run it after any failure).
  - Depends on: E-03
  - Expected outcome: a diff summary showing only the expected field and history lines, an assertion that no other metadata field changed on any plan, an empty terminal-directory status, and `aw check plans` compared per rule id against the pre-edit baseline.
  - Execution state: performed
  - Execution note: THE STRONGEST AVAILABLE PROOF IS THE DELETION COUNT, and it is ZERO: `git diff --numstat` over the pending tree totals `insertions=87 deletions=0` across 30 files. A pure-insertion diff means NO pre-existing line was altered, so `Status`, `Readiness`, `Set`, `Order`, `Id`, `Approval`, `Item-Dependencies`, `Blocks-Release` and `From-Backlog` are provably untouched on every plan without needing to enumerate them; a grep of the diff for any of those field names as an added or removed line returns nothing. The 87 insertions classify exactly: 30 `- Priority:`, 27 `- Work-Kind:`, 30 history lines, and nothing else.
    THE TERMINAL-DIRECTORY PROOF IS EMPTY, which is the assertion that would have caught `f5pttg`: `git status --porcelain -- .aw/records/plans/executed .aw/records/plans/superseded .aw/records/plans/not-executed` returns 0 lines. `git status --porcelain` over the whole repo lists exactly 30 modified files, all under `pending/`, all in the derived table.
    `aw check plans` DID NOT REGRESS AND THE BASELINE WAS NOT WHAT REVIEW MEASURED. Captured before the first edit and again after the last: both exit 1 with `errors 41 warnings 0`, and the per-rule breakdown is IDENTICAL (36 `check.ipd-uncarried-obligation`, 3 `check.lifecycle-transition-invalid`, 1 `check.ipd-lint-diagnostic`). Review's baseline was `errors 140` with a different rule mix (124 `check.scope-drift`); that is 11 days of intervening work, not a discrepancy, and it is why the item says capture a fresh baseline rather than trusting the recorded one. The full `aw check` was also compared: `errors 54` before and after, per-rule counts identical. NO rule id is new and NO count rose. Nothing was "fixed" by editing another party's plan.
    THE INDEX WAS RE-VERIFIED BEFORE COMMITTING, per the shared-checkout rule, and the commit went through `aw commit` so only this item's explicitly named paths could enter it.

- [x] E-05 PROVE THE BACKFILL IS OBSERVABLE ON A SURFACE AN AGENT CAN CAPTURE, because a populated field nobody can read has not achieved this plan's goal.
  USE THE TWO SURFACES THAT ACTUALLY CARRY PRIORITY, and not the one the authored V-04 named. MEASURED at review: a piped `aw att --type plan` emits `- [plans] <path> (<status>)` with NO Priority column, because the column exists only in the colored table renderer. The two surfaces that answer the question are `FORCE_COLOR=1 aw att --type plan` and `aw att --type plan --format json`, whose per-item `priority` key is machine-readable.
  STATE A BEFORE AND AFTER COUNT, not a screenshot impression: the number of plan items whose `priority` is non-null in `--format json`, captured before the first edit and after the last. That delta is this plan's actual deliverable.
  - Depends on: E-04
  - Expected outcome: both surfaces pasted, and the non-null `priority` count stated before and after with the delta matching the number of plans written.
  - Execution state: performed
  - Execution note: THE DELTA IS EXACTLY 30 AND MATCHES THE WRITE COUNT, which is this plan's actual deliverable. `aw att --type plan --format json` was captured BEFORE the first edit and AFTER the last: plan items whose `priority` key is non-null went from 36 to 66 over the whole plans tree, and from 11 to 41 over `pending/` alone. Item count is unchanged at 712 (54 pending), so nothing appeared or vanished. The pending board's priority distribution after the write reads 20 `high`, 21 `medium`, 13 null, and those 13 are precisely E-06's residue.
    `FORCE_COLOR=1 aw att --type plan` RENDERS A POPULATED Priority COLUMN, verified on the colored table: `ao1rb7` shows `high`, `y9s4vm`/`iuxtjy`/`lyo1tz` show `medium`, and the plans this backfill did not reach (`d0cbt3`, `lkexaw`, `8u6770`, `lc4unl`, `nmlx47`, `tb63qv`) still render `-`. The item's warning was heeded: the piped surface has no Priority column at all, so it was never used as evidence.

- [x] E-06 REPORT WHAT REMAINS, so the Set's next step is grounded in a measurement rather than in this plan's authored estimate.
  AFTER THE WRITE, RE-COUNT the pending plans still missing either field and confirm the number equals the no-source population that sibling 03 owns. Review measured 28 with no source; if the residue is larger than that, something in the derivation was skipped and this item must say so rather than reporting success.
  NAME ANY PLAN SKIPPED AND WHY, including a dangling reference from E-01, a plan already carrying both fields, and any plan whose write was deferred pending OQ-02. A silent skip is how a backfill reports completion while leaving holes.
  - Depends on: E-05
  - Expected outcome: the residual count stated and reconciled against sibling 03's population, with every skipped plan named and its reason given.
  - Execution state: performed
  - Execution note: THE RESIDUE IS 13 AND IT RECONCILES EXACTLY, with no unexplained remainder: 12 plans carrying no source (sibling 03 `lc4unl`'s own population) plus the 1 whose source is unresolvable. The item's stop-rule ("if the residue is larger than the no-source population, something was skipped") is satisfied by that decomposition rather than by the raw comparison, because the residue legitimately carries one plan sibling 03 does not own.
    RE-RUNNING E-01's DERIVATION AFTER THE WRITE REPORTS A WRITE POPULATION OF 0, which is the cleanest proof no plan in scope was missed: of the 32 pending plans with a resolving source, 32 now carry both fields and 0 carry neither or one.
    EVERY SKIP NAMED WITH ITS REASON. (1) UNRESOLVABLE SOURCE, 1 plan: `nmlx47`, whose `- From-Backlog: dstnso, 8hx3g3` is multi-valued and matches no shipped reader; reported by E-01, filed as backlog `6os96s`, and deliberately NOT guessed at, since choosing one of two sources is a judgement this plan does not make. It is NOT silently handed to sibling 03: that plan's population is defined by carrying no source, and this one carries two. (2) ALREADY CARRIED BOTH FIELDS, 2 plans: `87apfx` (`high`/`bug`) and `n9na1c` (`medium`/`bug`), excluded rather than overwritten. (3) NO SOURCE, 12 plans, sibling 03's work: `04vf1h`, `2xz59a`, `7p3tt8`, `8u6770`, `d0cbt3`, `gqo6if`, `lc4unl`, `lkexaw`, `qdd5jq`, `tb63qv`, `ubac5n`, `x75obw`. NOTHING was deferred pending OQ-02.
    SIBLING 03's POPULATION IS SMALLER THAN ITS OWN PLAN STATES, which is worth carrying forward: 21 pending plans carry no source, but 9 of them ALREADY hold both fields, so only 12 need its decision table (review measured 28). Its own authored figure of 20 and review's 28 are both stale for the same reason E-01's were.

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw ipd set --priority` and `--work-kind` exist and are documented as persisting "on a no-op transition", which is precisely the affordance a field-only backfill needs. DRIVEN at review rather than trusted: on both `reviewed` and `approved` the call exits 0, prints `unchanged`, writes both fields, and leaves `- Status:` untouched.
- THE SETTER INSERTS BOTH FIELDS DIRECTLY AFTER `- Status:`, verified in the diff. That is the setter's choice and is why hand-editing is forbidden: a hand-editor would place them elsewhere and the corpus would end up inconsistent.
- A SAME-STATUS CALL WITHOUT `--message` WRITES A FALSE HISTORY LINE. Measured: `- <date> approved (aw set): status set to approved` on a plan that was already `approved` and did not transition. Passing `--message` replaces that text with the supplied note. This is the same family as backlog `x6tk1u` (a same-status `--message` being DISCARDED on the backlog path) and is worth reading alongside it.
- A SETID SELECTOR IS DANGEROUS HERE AND AN id6 IS NOT. `aw ipd set` resolves a setid to every plan carrying it, terminal ones included; 6 of the 57 setids in this population also name an `executed/` plan, and a dry-run proves two would be reverted. Backlog `f5pttg` records this defect having actually reverted seven executed plans, and it is `open`, so nothing protects an executor but the selector choice.
- `--dry-run` AND `--no-commit` BOTH WORK ON THIS PATH and are the two guards that make a bulk field write safe: the first proves the selection, the second stops a mid-loop commit offer in a shared checkout.
- A cross-tree id6 reference must be RESOLVED, not parsed: `check.from-backlog-dangling` already treats an unresolvable `From-Backlog` as a finding, so this plan must not accept one. Measured: zero dangle today.
- An absent `Priority` renders as unprioritized and a value must never be fabricated (`xprio` orchestrator `u5vyye` OQ-01). Inheritance is not fabrication: the value comes from an artifact the plan itself names.
- THE PRIORITY COLUMN IS NOT ON THE PIPED BOARD. `aw att --type plan` piped emits `- [plans] <path> (<status>)` with no Priority column; use `FORCE_COLOR=1` or `--format json` (whose per-item `priority` key is the machine-readable surface).
- `aw check plans` IS 140 ERRORS DEEP BEFORE THIS PLAN RUNS (124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`), so "clean" is unobtainable and a per-rule delta is the only honest bar.
- 11 PENDING PLANS ALREADY CARRY BOTH FIELDS, so the population is 81 rather than 92 and an unconditional write would overwrite a deliberate value with an inherited one.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | MEDIUM | Most pending plans can inherit both fields with zero judgement: every `- From-Backlog:` resolves and every source carries both fields. RE-MEASURED at review: 120 pending, 92 with a resolving source, 0 dangling, 0 sources missing a field. The authored `84 of 104` is stale. |
| F-1b | MEDIUM | **11 PENDING PLANS ALREADY CARRY BOTH FIELDS**, which the authored plan did not account for, so the real write population is 81 and not 92. An unconditional write would replace a deliberately chosen value with an inherited one, which is a silent downgrade rather than a backfill. E-01 now excludes them. |
| F-2 | MEDIUM | The inherited values are a genuine spread, not a single default, so the result is useful rather than uniform. RE-MEASURED over the 81: 25 `high`/`bug`, 25 `medium`/`bug`, 10 `high`/`feature`, 9 `medium`/`feature`, 6 `medium`/`chore`, 3 `low`/`feature`, and three singletons. Zero out-of-vocabulary or absent source values. |
| F-3 | LOW | A setter already exists for both fields and persists on a no-op transition, so no hand-editing and no new tooling is needed for the write. DRIVEN at review on both statuses in the population (`reviewed`, `approved`): exit 0, `unchanged`, both fields written, `- Status:` untouched. |
| F-4 | LOW | This plan touches roughly 81 files in a shared checkout where other agents commit concurrently, so the index must be re-verified before every commit and after any failed hook. That is an execution hazard rather than a design one, and E-04 owns it. |
| F-5 | BLOCKER | **A SAME-STATUS WRITE APPENDS A FALSE HISTORY LINE.** Without `--message`, the setter records `- <date> approved (aw set): status set to approved` on a plan that did not transition. Measured on `5e4sb6`. 5 of the 81 are `approved`, so 5 records would carry a fabricated approval event, in a Set whose purpose is to make plan metadata trustworthy. `--message` replaces the text (verified), but whether to write any line onto an approved plan is the maintainer's call. Blocking OQ-02. |
| F-6 | HIGH | **A SETID SELECTOR WOULD REVERT EXECUTED PLANS.** 6 of the 57 setids in this population (`hostdefault`, `integearn`, `integpath`, `lanectn`, `rununify`, `setidhard`) also name a terminal plan; `aw ipd set approved rununify --dry-run` reports `executed -> approved` on TWO plans in `executed/`. Backlog `f5pttg` records this exact command having reverted seven executed plans, and it is still `open`. E-03 now mandates id6 selectors plus a dry-run preflight; E-04 proves the terminal dirs stayed clean. |
| F-7 | MEDIUM | **THE DEPENDENCY EDGE THIS PLAN CARRIES IS THE PARENT'S BLOCKING DEFECT.** `- Item-Dependencies: executed:lkexaw` is what the parent's review measured as stranding 18 already-approved pending plans (parent PR-001, blocking parent OQ-02). This plan's gate justifies that edge with reasoning the parent's review found false, and the edge may be reversed or removed by the answer, so the justification must not be re-inherited. |
| F-8 | MEDIUM | **TWO PRESCRIBED EVIDENCE COMMANDS CANNOT PRODUCE WHAT THEY ASK.** A piped `aw att --type plan` has no Priority column (it exists only in the colored renderer), and `aw check plans` carries 140 pre-existing errors so it can never be shown "clean". Both corrected; `FORCE_COLOR=1`/`--format json` and a per-rule delta replace them. |
| F-9 | LOW | 17 of the 81 are release-blocking and inherit `medium`; NONE inherits `low`. That is the precise list OQ-01 exists to have a human see, and it is smaller and more uniform than the open question implied. |
| F-10 | LOW | A mid-loop commit offer is a real hazard in this checkout: without `--no-commit` the setter offers to commit after each write, and accepting one sweeps whatever else is staged. E-03 now passes it explicitly. |

## Proposed changes (ordered, validatable)

1. Re-derive and print the inheritance table, resolving every source and excluding plans that already carry both fields (E-01).
2. Sanity-check the derived values and surface the tails without correcting any source (E-02).
3. Write both fields through the shipped setter, by id6, dry-run first, `--no-commit`, with a truthful `--message` (E-03). Gated on OQ-02 for the 5 approved plans.
4. Prove no other field or status moved, no terminal plan was touched, and the checker count did not regress per rule (E-04).
5. Prove the result is observable on a surface that actually carries Priority, with a before and after count (E-05).
6. Report the residue and reconcile it against sibling 03's population, naming every skip (E-06).

## Deferred / out of scope (with reason)

- THE PLANS WITH NO SOURCE ITEM. Sibling 03 owns them, because they need a judgement this plan deliberately does not make. Re-measured at review: 28, not the authored 20.
- THE 11 PENDING PLANS THAT ALREADY CARRY BOTH FIELDS. Excluded by E-01 rather than overwritten, because replacing a deliberately chosen value with an inherited one is a downgrade, not a backfill.
- CORRECTING A SOURCE BACKLOG ITEM whose value looks wrong. Reported by E-02, not edited: those items are outside this plan's declared scope. Measured at review, no source is out of vocabulary, so this is a guard rather than an expected case.
- TERMINAL PLANS. Immutable by policy, and exempt by the sentinel sibling 01 adds. This plan must PROVE it touched none (E-04), because a setid selector would silently revert them.
- FIXING THE SETTER'S FALSE HISTORY LINE. OQ-02 records that the honest long-term fix is code work in the shared status setter, which is outside this plan's declared `Scope-Paths` and intersects backlog `x6tk1u`. It needs its own carrier; this plan works around it with `--message`.
- ANY PLAN AUTHORED AFTER SIBLING 01 LANDS, which will carry the fields from the scaffold and needs no backfill.

## Scope check

- Over-scope: none. Only the pending plans tree is declared, and only two fields plus one history line per plan are written.
- Under-scope: this plan leaves the no-source pending plans without values by design (28 at review, not the authored 20); the Set is incomplete until sibling 03 runs.
- Under-scope, FOUND AT REVIEW and now carried rather than left implicit: the authored plan had no item proving the result is OBSERVABLE (its goal is a populated Priority column, and its only prescribed surface has no such column), and no item reporting the RESIDUE so sibling 03's population could be reconciled. Now E-05 and E-06.
- A KNOWN LIMIT, STATED HONESTLY: this plan works around the setter's false-history behavior with `--message` rather than fixing it, so every future caller of a same-status field write hits the same trap. OQ-02 records that the fix needs its own carrier.

## Required tests / validation

No new test file: this plan changes records, not code, and its correctness is demonstrated by the derivation table plus the no-collateral-change proof.

- THE THROWAWAY-COPY REHEARSAL, which is how review found both escalated hazards and is cheap to repeat: copy the repo, run the write against ONE plan of each status, inspect the diff and the history line, then discard the copy. Do this BEFORE touching the real tree, and never rehearse a bulk write in a shared checkout.
- THE DRY-RUN PREFLIGHT on every invocation, with its output read rather than assumed. A line reading anything but `unchanged` for exactly the plan you named means the selector over-matched.
- THE TERMINAL-DIRECTORY PROOF: `git status --porcelain` over `executed/`, `superseded/` and `not-executed/` must be empty (E-04/V-04).
- `aw check plans` COMPARED PER RULE ID against a baseline captured before the first edit. Do NOT require clean: measured bare at review (HEAD `fe57b1a4`) it exits 1 with `errors 140  warnings 0`, none of it caused by this plan.
- BOTH PRIORITY SURFACES: `FORCE_COLOR=1 aw att --type plan` and `aw att --type plan --format json`, with a before and after non-null count (E-05/V-05).
- `python3 -m pytest` BARE, with the baseline established BEFORE the first edit and judged on the failure SET rather than the count. A record change should not affect it and a difference would be informative. Review measured `5971 passed, 3 skipped, 2 xfailed in 59.68s` at HEAD `fe57b1a4`, REFERENCE ONLY. Run it bare: the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`, so adding `-n0` or a second `-q` makes the run slower and suppresses the summary line the contract requires you to paste.
- `aw sanitize --agent` clean before treating any output as shareable.

## Spec / documentation sync

N/A: sibling 01 amends the spec that defines the metadata fields. This plan writes values into existing recognized fields and changes no contract.

## Open questions

### OQ-01: Should a release-blocking plan that inherits a low or medium priority be corrected?

- Blocking: no
- Status: open
- Owner: this plan's executor for the reading, the maintainer only if a correction is proposed
- Resolution or deferral rationale: INHERIT FAITHFULLY AND REPORT THE MISMATCH; DO NOT SILENTLY OVERRIDE. `Blocks-Release` and `Priority` are orthogonal by design, and the source backlog item `p9o1oo` says so explicitly: the "urgent/drop-everything" case "is already covered orthogonally by `Blocks-Release`, so no 4th tier". So a release-blocking plan carrying `medium` is not a contradiction and must not be auto-promoted. E-02 lists these cases precisely so a human can see them; if any looks genuinely wrong, that is a source-item correction owned elsewhere. Non-blocking because the backfill is correct under either reading.
  MEASURED AT REVIEW, WHICH NARROWS THE QUESTION CONSIDERABLY: 17 of the 81 are release-blocking and every one of them inherits `medium`; NOT ONE inherits `low`. So the case the question worried about most (a release blocker landing at `low`) does not occur in the current population, and the residual question is only whether `medium` plus a release gate is an acceptable pairing, which `p9o1oo` already answers yes. Kept `open` rather than resolved because the population moves and a `low` case could appear, and because it is the human's call whether to look at the 17; E-02 must still list them.

### OQ-02: A same-status write appends a history line asserting a transition that did not happen. Is a truthful `--message` line acceptable on the 5 approved plans, or should they be deferred?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: MEASURED BY EXECUTION, NOT PREDICTED, WHICH IS WHY IT IS BLOCKING. Driven at review in a throwaway repo copy on plan `5e4sb6` (status `approved`, needing both fields): `aw ipd set approved 5e4sb6 --priority medium --work-kind chore` exits 0, prints `unchanged`, correctly writes both fields, leaves `- Status:` untouched, AND prepends `- 2026-09-12 approved (aw set): status set to approved` to the workflow history. That line asserts an approval event that did not occur, on a plan whose real approval is already recorded with its own date and actor. This Set exists to make plan metadata trustworthy, so writing 5 fabricated approval events in service of it is a self-defeating outcome and not a cosmetic blemish.
  A REMEDY EXISTS AND IS VERIFIED. Passing `--message "<text>"` replaces the fabricated sentence with the supplied one, confirmed in the same copy: the line became `- 2026-09-12 approved (aw set): Inherited Priority/Work-Kind from source backlog item dhuape; status unchanged.` The actor is still `aw set` and the leading status token is still `approved`, so the line remains a HISTORY RECORD tagged with the current status rather than a claim of change; whether that is honest enough is the judgement.
  THE SCOPE IS 5 PLANS, NOT 81. The 76 `reviewed` plans get the same treatment, but a line reading `reviewed (aw set): Inherited ...` on a plan that IS `reviewed` asserts nothing false, so the question is confined to the 5 `approved` ones. That is what makes deferring them cheap if the maintainer prefers.
  RELATED SHIPPED DEFECTS, cited so the maintainer sees this is a known family rather than a one-off: backlog `x6tk1u` (`open`, high) records that a same-status `--message` is silently DISCARDED on the backlog path, and its analysis names `status_set.apply_status_change` as the shared setter behind `aw ipd set`. So the plan path writing a line and the backlog path dropping one are two faces of the same unresolved design question about what a no-op transition should record.
  THREE OPTIONS. (a) WRITE WITH A TRUTHFUL `--message` ON ALL 81, accepting one extra history line per plan. Cost: 81 plans gain a line whose leading token repeats their current status, and 5 of those sit on approved plans where a careless later reader could misread it as a re-approval. Benefit: one uniform invocation, the whole population done in one pass, and the message states the provenance the Set wants recorded anyway. (b) WRITE THE 76 `reviewed` PLANS NOW AND DEFER THE 5 `approved` ONES to a follow-up that fixes the setter first. Cost: the Set finishes incomplete and 5 approved plans keep an absent Priority, which is exactly what the parent's PR-001 says makes them unrunnable once the gate lands. Benefit: not one false or ambiguous line is written. (c) FIX THE SETTER FIRST so a field-only no-op writes no history line at all, then backfill. Cost: that is code work in `status_off`/`status_set` outside this plan's declared `Scope-Paths` and would need its own plan, blocking this Set behind it; it also intersects `x6tk1u`, whose preferred fix moves in the opposite direction (make a message a mutation). Benefit: the cleanest records and it fixes the defect for every future caller.
  RECOMMENDATION (a), because a truthful `--message` makes each line accurate on its own terms, the provenance it records is genuinely wanted, and (b) leaves precisely the plans the parent's blocker is about without a value. (c) is the right long-term fix and the wrong thing to block this Set on; it should be filed as its own carrier either way.
  DELIBERATELY NOT DONE HERE: review did not write to the real tree, did not modify the setter, and did not file the follow-up carrier, because filing work and choosing among three options that trade record cleanliness against Set completeness is the maintainer's call.
  MAINTAINER RULINGS 2026-09-12 (recorded from an interactive round; these settle the Set's ordering and the 13 undecided plans).

  RULING 1, ORDERING: RUN ORDERS 02 AND 03 BEFORE ORDER 01. The maintainer chose this over stamping a grandfather sentinel inside Order 01 and over staging the gate as advisory. So NO exemption marker is written anywhere, the corpus is real-valued before the gate exists, and Order 01's dependency edges must be rewritten to depend on 02 and 03 rather than the reverse. The authored justification for gating first ("backfilling before the gate exists would write values nothing enforces") is REJECTED: a value written before the gate exists is exactly what the gate then finds satisfied.
    WHY THE COST IS ACCEPTABLE, having been measured and put to them: only 5 of the 18 approved-and-missing plans can inherit from a source item, so the other 13 needed values before any code could land. That is settled by Ruling 2. The residual gap (a plan authored between the backfill and the gate arriving with neither fields nor marker) is NARROW because Order 01 also fixes `aw ipd scaffold`, which never emitted these fields at all and is the root cause of near-zero adoption.

  RULING 2, THE 13 UNDECIDED PLANS, accepted as a per-Set table rather than 13 individual answers:
    | Set | Plans | Priority | Work-Kind | Basis |
    |---|---|---|---|---|
    | `lanectn` | `xdr83v` | high | bug | Concern: teardown destroys content silently (data loss); already carries `Blocks-Release: next`, so `high` is the only value consistent with that gate. |
    | `runnerbugs` | `hp9rot` | high | bug | Self-describing: Concern reads "bugs/correctness (assess-bugs)", Scope reads "Verified runner defects". |
    | `orchprobe` | `m7gvuz`, `r2i1b1` | medium | bug | Both are correctness defects (work reported complete that nobody performed; a refusal no surface reports), not new capability. Neither loses data. |
    | `runanalytics` | all 9 children | medium | feature | New telemetry/cache/SPA/data-sharing capability; nothing pre-existing breaks in its absence. |

  RULING 3, GATING, and it is the widest of the three: ALL BUGS MUST BLOCK THE NEXT RELEASE. Verbatim. So `hp9rot`, `m7gvuz` and `r2i1b1` gain `- Blocks-Release: next` as part of writing their `Work-Kind: bug` (`xdr83v` already has it). This was put to them as a separate decision from naming the work-kind, and they widened it deliberately.
    THE EXECUTOR MUST NOT TREAT THIS AS OPTIONAL OR AS THIS SET'S INVENTION: it is the same standing rule the `nobugship` Set (`qmgn12`) exists to make durable, applied here to the plans this Set touches. Writing `Work-Kind: bug` WITHOUT the gate would leave the corpus in exactly the inconsistent state that Set is being built to detect.
    DO NOT WIDEN IT BEYOND THIS SET'S POPULATION. Gating every `bug` artifact repo-wide is `qmgn12`'s job, not this backfill's; touching plans outside the measured 13 would be scope creep into a shared checkout.
  ANSWERED BY RULING 1's CONSEQUENCE: this plan now runs BEFORE the gate exists, so the 5 approved plans it touches are not at risk of being stranded by it, and the same-status-write concern reduces to writing a TRUTHFUL history line. Use `--message` prose that states what actually happened (fields backfilled by inheritance from the named source item) and never wording that asserts a lifecycle transition that did not occur. Do NOT defer the 5 approved plans: deferring them was only necessary under the authored order.

### OQ-03: This plan's dependency edge is the parent's blocking defect. Answer the PARENT's OQ-02, then bring this plan's `- Item-Dependencies:` into agreement.

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: THIS QUESTION IS ANSWERED AT THE PARENT, NOT HERE, AND IT EXISTS HERE SO THE GATE HOLDS ON THIS FILE TOO. Review initially recorded PR-001 as merely inherited, reasoning that duplicating the parent's question would ask the maintainer to answer it twice. `aw check` then flagged this file with `check.review-finding-unescalated`, which is correct and is why the rule exists: a BLOCKER left OPEN must refuse execution of the artifact it is about, and this child is the artifact that carries the edge. So the question is recorded here with its finding id; ANSWER IT ONCE, on the parent (`d0cbt3` OQ-02), and record the same answer here rather than re-deciding it.
  THE SUBSTANCE, stated so this entry is decidable without opening the parent. `- Item-Dependencies: executed:lkexaw` makes this backfill wait for the child that installs the requiredness gate. The parent's review measured that ordering as stranding 18 already-approved pending plans the moment sibling 01 lands, because the gate fires at EVERY lint phase for a plan whose persisted status is at the ready-to-execute tier; of those 18, only 5 are reachable by this plan's inheritance and the other 13 need sibling 03's human decision table. The parent offers three costed options (stamp the exemption marker inside Order 01, as the shipped `oorry1` precedent did; reverse the order so the backfills run first; or stage the gate as advisory then flip it) and recommends the first.
  WHAT MUST HAPPEN IN THIS FILE once the answer is recorded: if the answer removes or reverses the edge, the `- Item-Dependencies:` line here must change in the same commit, because the parent's child table and this child's front matter are two statements of one fact and a disagreement between them is what a runner reads wrongly. If the answer keeps the edge (option (a) keeps it while making it harmless), the line stays and this question closes citing that.
  DO NOT DEFEND THE EDGE WITH THIS PLAN'S AUTHORED JUSTIFICATION, which the parent's measurement contradicts: "backfilling before the gate exists would write values nothing enforces" inverts the mechanism, since a value written before the gate exists is precisely what the gate then finds satisfied.
  MAINTAINER RULINGS 2026-09-12 (recorded from an interactive round; these settle the Set's ordering and the 13 undecided plans).

  RULING 1, ORDERING: RUN ORDERS 02 AND 03 BEFORE ORDER 01. The maintainer chose this over stamping a grandfather sentinel inside Order 01 and over staging the gate as advisory. So NO exemption marker is written anywhere, the corpus is real-valued before the gate exists, and Order 01's dependency edges must be rewritten to depend on 02 and 03 rather than the reverse. The authored justification for gating first ("backfilling before the gate exists would write values nothing enforces") is REJECTED: a value written before the gate exists is exactly what the gate then finds satisfied.
    WHY THE COST IS ACCEPTABLE, having been measured and put to them: only 5 of the 18 approved-and-missing plans can inherit from a source item, so the other 13 needed values before any code could land. That is settled by Ruling 2. The residual gap (a plan authored between the backfill and the gate arriving with neither fields nor marker) is NARROW because Order 01 also fixes `aw ipd scaffold`, which never emitted these fields at all and is the root cause of near-zero adoption.

  RULING 2, THE 13 UNDECIDED PLANS, accepted as a per-Set table rather than 13 individual answers:
    | Set | Plans | Priority | Work-Kind | Basis |
    |---|---|---|---|---|
    | `lanectn` | `xdr83v` | high | bug | Concern: teardown destroys content silently (data loss); already carries `Blocks-Release: next`, so `high` is the only value consistent with that gate. |
    | `runnerbugs` | `hp9rot` | high | bug | Self-describing: Concern reads "bugs/correctness (assess-bugs)", Scope reads "Verified runner defects". |
    | `orchprobe` | `m7gvuz`, `r2i1b1` | medium | bug | Both are correctness defects (work reported complete that nobody performed; a refusal no surface reports), not new capability. Neither loses data. |
    | `runanalytics` | all 9 children | medium | feature | New telemetry/cache/SPA/data-sharing capability; nothing pre-existing breaks in its absence. |

  RULING 3, GATING, and it is the widest of the three: ALL BUGS MUST BLOCK THE NEXT RELEASE. Verbatim. So `hp9rot`, `m7gvuz` and `r2i1b1` gain `- Blocks-Release: next` as part of writing their `Work-Kind: bug` (`xdr83v` already has it). This was put to them as a separate decision from naming the work-kind, and they widened it deliberately.
    THE EXECUTOR MUST NOT TREAT THIS AS OPTIONAL OR AS THIS SET'S INVENTION: it is the same standing rule the `nobugship` Set (`qmgn12`) exists to make durable, applied here to the plans this Set touches. Writing `Work-Kind: bug` WITHOUT the gate would leave the corpus in exactly the inconsistent state that Set is being built to detect.
    DO NOT WIDEN IT BEYOND THIS SET'S POPULATION. Gating every `bug` artifact repo-wide is `qmgn12`'s job, not this backfill's; touching plans outside the measured 13 would be scope creep into a shared checkout.
  ANSWERED BY RULING 1: the parent's OQ-02 is resolved as 02-and-03-BEFORE-01. So this plan's `- Item-Dependencies:` must NOT depend on `executed:lkexaw`; that edge is inverted. Rewrite it to `none` (or to whatever this plan genuinely needs from its sibling 03, which is nothing) and make Order 01 depend on THIS plan instead.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the full re-derived table with the command that produced it, carrying id6, current status, source id6, the source's two values and its path. State the count and how it differs from review's 81 and the authored 84. Paste the list of plans EXCLUDED because they already carry both fields (review measured 11) and the per-status split of the write population (review measured 76 `reviewed`, 5 `approved`). Paste any dangling `- From-Backlog:` found, or state that none was; review measured zero, so any occurrence is new.
  - Observed evidence: derivation script driven at HEAD `e96dc154`, resolving each `- From-Backlog:` id6 against `backlog._iter_items` (the same corpus `existing_backlog_ids` walks for `check.from-backlog-dangling`) and reading each plan's metadata block with `ipd_schema.parse_metadata_block`:

    ```text
    PENDING PLANS TOTAL: 54
    CARRYING - From-Backlog:  33
    CARRYING NO SOURCE:       21
    DANGLING From-Backlog:    1
      DANGLING nmlx47 -> 'dstnso, 8hx3g3'  .aw/records/plans/pending/20260917-hostdedup-02-nmlx47-unify-the-twelve-small-divergent-symbols-behind-hostlabels.ipd.md
    RESOLVING SOURCES:        32
    ALREADY CARRY BOTH (EXCLUDED): 2
    CARRY EXACTLY ONE (partial):   3
    CARRY NEITHER:                 27
    SOURCES MISSING A FIELD:       0
    WRITE POPULATION:              30
    ```

    THE FULL TABLE, one row per plan (plan id6, plan status, source id6, the source's two values, which fields this plan writes, and the source's path):

    ```text
    plan id6  plan status  src id6   src prio  src kind  writes             src path
    ao1rb7    approved     wjl471    high      feature   Priority+Work-Kind .aw/records/backlog/graduated/20260831-commitguard-01-wjl471-agent-detecting-commit-guard.backlog.md
    2s0iym    approved     wjl471    high      feature   Priority+Work-Kind .aw/records/backlog/graduated/20260831-commitguard-01-wjl471-agent-detecting-commit-guard.backlog.md
    y9s4vm    approved     6h7y2y    medium    feature   Priority+Work-Kind .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md
    iuxtjy    approved     6h7y2y    medium    feature   Priority+Work-Kind .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md
    yv4tb1    approved     6h7y2y    medium    feature   Priority+Work-Kind .aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-graduate-verb-and-duplicate-guard.backlog.md
    a5wdne    approved     dstnso    high      followup  Priority+Work-Kind .aw/records/backlog/open/20260917-dstnso-01-dstnso-execute-item-closure-forks-unclaimed.backlog.md
    li44r9    approved     dstnso    high      followup  Priority+Work-Kind .aw/records/backlog/open/20260917-dstnso-01-dstnso-execute-item-closure-forks-unclaimed.backlog.md
    xdvglg    approved     dstnso    high      followup  Priority+Work-Kind .aw/records/backlog/open/20260917-dstnso-01-dstnso-execute-item-closure-forks-unclaimed.backlog.md
    ut0vzr    approved     qliia1    high      followup  Priority+Work-Kind .aw/records/backlog/open/20260917-qliia1-01-qliia1-triage-14-unintegrated-lane-branches.backlog.md
    k311gw    approved     a58s04    high      bug       Priority+Work-Kind .aw/records/backlog/done/20260917-a58s04-01-a58s04-lane-reclaim-measures-own-base-not-main.backlog.md
    z1yefm    approved     x15f0q    high      bug       Priority+Work-Kind .aw/records/backlog/graduated/20260912-x15f0q-01-x15f0q-migrate-leaves-legacy-litter.backlog.md
    yeh7gc    approved     5ev6lh    medium    bug       Priority+Work-Kind .aw/records/backlog/graduated/20260907-rollupev-01-5ev6lh-rollup-omits-orchestrator-ev-checkpoint.backlog.md
    s0gnha    approved     yxfw4k    high      bug       Priority           .aw/records/backlog/graduated/20260919-reaskscore-01-yxfw4k-reask-completes-work-but-is-never-rescored.backlog.md
    dy9ymn    approved     x7wfyx    medium    bug       Priority           .aw/records/backlog/done/20260918-x7wfyx-01-x7wfyx-zero-work-turn-retry-and-turn-budget.backlog.md
    svacmz    approved     yxfw4k    high      bug       Priority           .aw/records/backlog/graduated/20260919-reaskscore-01-yxfw4k-reask-completes-work-but-is-never-rescored.backlog.md
    p9j6c0    approved     yxfw4k    high      bug       Priority+Work-Kind .aw/records/backlog/graduated/20260919-reaskscore-01-yxfw4k-reask-completes-work-but-is-never-rescored.backlog.md
    lyo1tz    approved     cnwy8g    medium    bug       Priority+Work-Kind .aw/records/backlog/graduated/20260903-runnerlayer-01-cnwy8g-agy-runipd-imports-40-names-from-oc-runipd-so-the-hosts-are-not-peers.backlog.md
    1f7xno    approved     cnwy8g    medium    bug       Priority+Work-Kind .aw/records/backlog/graduated/20260903-runnerlayer-01-cnwy8g-agy-runipd-imports-40-names-from-oc-runipd-so-the-hosts-are-not-peers.backlog.md
    5e4sb6    approved     dhuape    medium    chore     Priority+Work-Kind .aw/records/backlog/graduated/20260828-dhuape-01-dhuape-unify-runners.backlog.md
    40it5e    approved     dhuape    medium    chore     Priority+Work-Kind .aw/records/backlog/graduated/20260828-dhuape-01-dhuape-unify-runners.backlog.md
    bxx9af    approved     rbftpl    medium    bug       Priority+Work-Kind .aw/records/backlog/graduated/20260829-runverdict-03-rbftpl-verifier-evidence-and-tests-run-never-consumed.backlog.md
    w33lrl    approved     vlf75p    high      bug       Priority+Work-Kind .aw/records/backlog/graduated/20260829-runverdict-02-vlf75p-run-record-omits-model-identity-and-rate-card.backlog.md
    xo3244    approved     05aqbj    medium    bug       Priority+Work-Kind .aw/records/backlog/graduated/20260901-selfmdialect-01-05aqbj-selectors-blind-to-research-yaml-frontmatter.backlog.md
    bwgyum    approved     sjsoqq    high      feature   Priority+Work-Kind .aw/records/backlog/graduated/20260827-setiduniq-01-sjsoqq-enforce-setid-uniqueness-across-types-hard-prevent.backlog.md
    wfjsp4    approved     qzhfk2    medium    chore     Priority+Work-Kind .aw/records/backlog/graduated/20260829-specsubdirs-01-qzhfk2-should-specs-get-lifecycle-subdirs.backlog.md
    y4bdoz    approved     qzhfk2    medium    chore     Priority+Work-Kind .aw/records/backlog/graduated/20260829-specsubdirs-01-qzhfk2-should-specs-get-lifecycle-subdirs.backlog.md
    1bdxcp    approved     qzhfk2    medium    chore     Priority+Work-Kind .aw/records/backlog/graduated/20260829-specsubdirs-01-qzhfk2-should-specs-get-lifecycle-subdirs.backlog.md
    r9uvwc    approved     qzhfk2    medium    chore     Priority+Work-Kind .aw/records/backlog/graduated/20260829-specsubdirs-01-qzhfk2-should-specs-get-lifecycle-subdirs.backlog.md
    ingpvc    approved     qzhfk2    medium    chore     Priority+Work-Kind .aw/records/backlog/graduated/20260829-specsubdirs-01-qzhfk2-should-specs-get-lifecycle-subdirs.backlog.md
    i8u6hh    approved     ygtykn    medium    bug       Priority+Work-Kind .aw/records/backlog/graduated/20260912-ygtykn-01-ygtykn-upgrade-stamps-stale-version.backlog.md
    ```

    THE COUNT IS 30, AND IT DIFFERS FROM BOTH RECORDED FIGURES BY FAR MORE THAN DRIFT: the authored plan said 84 of 104, review said 81 of 120, and this derivation finds 30 of 54. THE CAUSE IS WORK LANDING, not a broken derivation: `aw att --type plan --format json` reports 712 plan records of which 619 are `executed`, so the pending corpus review measured has largely been executed in the intervening 11 days. This is precisely the failure mode the item's "DO NOT REUSE ANY COUNT" instruction exists to prevent, and it would have mis-sized the write by a factor of nearly three.

    EXCLUDED BECAUSE THEY ALREADY CARRY BOTH FIELDS, 2 plans (review measured 11, again stale):

    ```text
    87apfx  Priority=high    Work-Kind=bug       .aw/records/plans/pending/20260922-stalemerge-01-87apfx-tell-a-cross-run-adjacency-conflict-from-a-real-failure-of-t.ipd.md
    n9na1c  Priority=medium  Work-Kind=bug       .aw/records/plans/pending/20260922-gateinert-01-n9na1c-make-a-usable-not-mine-gate-answer-actually-release-the-inte.ipd.md
    ```

    IN SCOPE FOR THE MISSING FIELD ONLY, 3 plans carrying exactly one field (all already hold `Work-Kind: bug` and receive `Priority` alone): `s0gnha`, `dy9ymn`, `svacmz`. The table's `writes` column states which field each row writes, as the item requires.

    PER-STATUS SPLIT OF THE WRITE POPULATION: `approved` 30, `reviewed` 0. THIS INVERTS REVIEW'S 76 `reviewed` / 5 `approved` READING, and it matters rather than being a curiosity: OQ-02's false-history-line concern was scoped to "5 plans, not 81" on the strength of that split, and in fact it applies to ALL 30. The maintainer's Ruling 1 answer (write with a truthful `--message`) covers every one identically, so nothing was deferred, but the "deferring them is cheap" escape hatch OQ-02 offered would now cost the entire population.

    ONE DANGLING REFERENCE, WHICH REVIEW MEASURED AS ZERO AND IS THEREFORE NEW, reported rather than guessed at: `nmlx47` carries `- From-Backlog: dstnso, 8hx3g3`. Both shipped readers are anchored single-token (`releases._ITEM_FROM_BACKLOG_RE` is `(?m)^- From-Backlog:\s*(\S+)\s*$`), so the comma defeats the end anchor and the value resolves to NEITHER id; `aw check plans` reports no `check.from-backlog-dangling` finding for it at all. Excluded from the write, NOT reassigned to sibling 03 (it carries a source, so it is outside that plan's population), and filed as backlog `6os96s`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the value distribution and compare it to review's reading. Paste every source value outside the two vocabularies, or state none (review measured none). Paste the list of release-blocking plans inheriting `low`/`medium` WITH their id6s, and state how many are `low`; review measured 17, all `medium`, zero `low`. Confirm no source backlog item was modified (`git status --porcelain -- .aw/records/backlog` empty).
  - Observed evidence: the vocabularies were taken from the SHIPPED constants rather than transcribed, so a vocabulary change could not silently pass this check:

    ```text
    Priority vocabulary: ['high', 'low', 'medium']          (backlog.PRIORITIES)
    Work-Kind vocabulary: ['bug', 'chore', 'feature', 'followup', 'security']   (backlog.KINDS)
    OUT-OF-VOCABULARY SOURCE VALUES: 0
    SOURCES MISSING A FIELD:         0
    ```

    NONE. Every one of the 30 sources carries both fields and both values are in vocabulary, which MATCHES review's reading (it measured zero on both counts over its own 81), so no source item needed reporting and none was edited.

    INHERITED DISTRIBUTION over the 30, compared to review's reading over its 81:

    ```text
       7  medium/bug        (review: 25)
       7  medium/chore      (review: 6)
       6  high/bug          (review: 25)
       4  high/followup     (review: 0 - NEW; review saw 1 medium/followup and no high/followup)
       3  high/feature      (review: 10)
       3  medium/feature    (review: 9)
       -  low/feature       (review: 3 - GONE; no `low` value occurs anywhere in this population)
       -  high/security     (review: 1 - GONE)
    ```

    THE SHAPE SURVIVES THE POPULATION COLLAPSE, which is what F-2 actually claims: six distinct pairs over 30 plans, no single value dominating, so the result is a genuine spread rather than a uniform default. Two differences are worth naming rather than smoothing over: `high`/`followup` (4 plans) appears where review saw none, and `low` has vanished from the population entirely, so no plan in this write inherits `low` at all.

    NO SOURCE BACKLOG ITEM WAS MODIFIED:

    ```text
    $ git status --porcelain -- .aw/records/backlog
    [0 lines]
    ```

    THE RELEASE-BLOCKING TAIL IS 13 OF 30, WITH ZERO INHERITING `low`, which is the specific reading OQ-01 exists to have a human see:

    ```text
    inheriting high (6):    k311gw p9j6c0 s0gnha svacmz w33lrl z1yefm
    inheriting medium (7):  40it5e 5e4sb6 bxx9af dy9ymn i8u6hh xo3244 yeh7gc
    inheriting low (0):     none
    k311gw  Blocks-Release=next     inherits high/bug     (src a58s04)
    p9j6c0  Blocks-Release=next     inherits high/bug     (src yxfw4k)
    s0gnha  Blocks-Release=next     inherits high/bug     (src yxfw4k)
    svacmz  Blocks-Release=next     inherits high/bug     (src yxfw4k)
    w33lrl  Blocks-Release=next     inherits high/bug     (src vlf75p)
    z1yefm  Blocks-Release=f33nrj   inherits high/bug     (src x15f0q)
    40it5e  Blocks-Release=next     inherits medium/chore (src dhuape)
    5e4sb6  Blocks-Release=next     inherits medium/chore (src dhuape)
    bxx9af  Blocks-Release=next     inherits medium/bug   (src rbftpl)
    dy9ymn  Blocks-Release=next     inherits medium/bug   (src x7wfyx)
    i8u6hh  Blocks-Release=next     inherits medium/bug   (src ygtykn)
    xo3244  Blocks-Release=next     inherits medium/bug   (src 05aqbj)
    yeh7gc  Blocks-Release=next     inherits medium/bug   (src 5ev6lh)
    ```

    THIS DIVERGES FROM REVIEW, WHICH MEASURED ALL 17 AS `medium`: here 6 of 13 inherit `high`. The divergence STRENGTHENS OQ-01's non-blocking status rather than weakening it, because the worry was a release blocker landing LOW, and the tail has moved away from `low` rather than toward it. Zero `low` means the case that would have needed a human ruling does not occur, and `medium` plus a release gate is the pairing source item `p9o1oo` already sanctions.

    ONE TAIL THE ITEM DID NOT PRESCRIBE AND WHICH WAS SURFACED RATHER THAN WRITTEN SILENTLY, since the repo gained the "every live bug gates the next release" rule after this plan was authored: `lyo1tz` and `1f7xno` inherit `Work-Kind: bug` with NO `- Blocks-Release:` on the plan. Verified by reading the shipped rule rather than guessing at its reach: `check_engine.check_live_bug_gate` iterates `backlog._iter_items` only, so it scans BACKLOG ITEMS and never plans, and no finding fires on either plan (per-rule counts identical before and after, V-04). Their shared source `cnwy8g` is itself an ungated live bug that `aw check` ALREADY flags `check.live-bug-ungated` at baseline, so the absent gate is the faithful inheritance and `cnwy8g` is the artifact that needs fixing. Gating the plans instead would be a new decision outside this plan's Scope and would newly violate `check.from-backlog-gate-mismatch`, which compares a carrier's gate against its item's. Recorded as DECISION 03-8u6770-D2.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste OQ-02's recorded answer FIRST and state which option it selected, since it decides whether the 5 `approved` plans are written at all. Then paste, for the FIRST plan, the `--dry-run` output showing exactly ONE plan named and `unchanged`, followed by the real invocation and its `git diff` showing only the two fields plus one history line changed and `- Status:` unchanged. Paste the history line itself and confirm it carries the supplied `--message` text rather than `status set to approved`. Then paste a spot check of three more plans' metadata blocks. Confirm every invocation used an id6 (paste the loop or the command list), that `--no-commit` was passed, and that no hand-edit was used.
  - Observed evidence: OQ-02's RECORDED ANSWER FIRST, quoted from this plan's own OQ-02, where the maintainer's rulings of 2026-09-12 are transcribed:

    > RULING 1, ORDERING: RUN ORDERS 02 AND 03 BEFORE ORDER 01. [...] ANSWERED BY RULING 1's CONSEQUENCE: this plan now runs BEFORE the gate exists, so the 5 approved plans it touches are not at risk of being stranded by it, and the same-status-write concern reduces to writing a TRUTHFUL history line. Use `--message` prose that states what actually happened (fields backfilled by inheritance from the named source item) and never wording that asserts a lifecycle transition that did not occur. Do NOT defer the 5 approved plans: deferring them was only necessary under the authored order.

    IT SELECTED OPTION (a), write with a truthful `--message` on the whole population, and explicitly refused option (b) (deferring the approved plans). THE SCOPE OF THE QUESTION IS WIDER THAN OQ-02 BELIEVED: it reasoned "THE SCOPE IS 5 PLANS, NOT 81" from review's status split, and V-01 measures ALL 30 as `approved`, so the ruling applies to every plan written here rather than to 5. That does not change the answer (option (a) is uniform over the population by construction), and nothing was deferred.

    THE REHEARSAL, RUN FIRST IN A THROWAWAY COPY, which is what licensed writing to the real tree. The copy was made under the gitignored `.aw/state/` (`git check-ignore` confirms `.aw/.gitignore:60:/state/`), given its own `git init`, used, and discarded; the real tree was untouched until it was done. WITHOUT `--message`, the false line reproduces exactly as review measured, on `5e4sb6`:

    ```diff
     - Status: approved
    +- Work-Kind: chore
    +- Priority: medium
     - Readiness: go
     ## Workflow history
    +- 2026-09-23 approved (aw set): status set to approved
    ```

    That line asserts a transition that did not occur. WITH `--message`, the same invocation writes the supplied provenance instead:

    ```diff
     - Status: approved
    +- Work-Kind: chore
    +- Priority: medium
     ## Workflow history
    +- 2026-09-23 approved (aw set): Backfilled Priority/Work-Kind by inheritance from source backlog item dhuape (planprio 8u6770 E-03); no lifecycle transition occurred.
    ```

    The PARTIAL case was rehearsed too, on `s0gnha` with `--priority` alone, and writes exactly one field line: `+- Priority: high` plus its one history line, with no `Work-Kind` line added over the one already there.

    THE SETID HAZARD WAS DRIVEN IN THE SAME COPY AND IS NOW BLOCKED AT THE TOOL, which CORRECTS this plan's sharpest warning. Review reported `aw ipd set approved rununify --dry-run` announcing `executed -> approved` on two terminal plans. At this HEAD it REFUSES:

    ```text
    $ aw ipd set approved rununify --priority medium --work-kind chore --dry-run
    FAIL     refusing to move 11 plan(s) BACKWARDS out of a terminal disposition to 'approved'. A terminal
             plan is a historical record: re-opening it in place would assert that completed, validated work
             is pending again. AGENTS.md directs a CORRECTIVE IPD for a post-execution gap, not an in-place
             edit of the executed plan. If this plan reached a terminal state in error, pass
             --allow-terminal-reopen (recorded in the artifact's history).
    Refusing; nothing was written:
      20260915-rununify-09-orziju-...  (- Status: executed)
      [10 more, all `- Status: executed`]
    ```

    So backlog `f5pttg` (the defect that silently reverted seven executed plans) is FIXED and reads `done`, closed by plan `4bc1nd`; the corrections list's claim that it "is still `open`" is stale. The id6 discipline was kept regardless, because a refusal is a guard and not a licence.

    THE DRY-RUN PREFLIGHT, run as a COMPLETE PASS over all 30 before any real write, with a machine-checked stop condition (exit 0, exactly ONE output line, that line containing `unchanged`, and naming the plan we selected). First plan and the partial case:

    ```text
    === DRY-RUN PREFLIGHT: 30 plans ===
    --- ao1rb7  writes=Priority+Work-Kind  src=wjl471 -> high/feature
        -    plan        20260908-commitguard-00-ao1rb7  unchanged  (dry-run)
    --- s0gnha  writes=Priority  src=yxfw4k -> high/bug
        - >  plan        20260919-reaskscore-00-s0gnha  [blocking]  unchanged  (dry-run)
    [...]
    invocations: 30   stop-conditions: 0
    ALL INVOCATIONS: exit 0, exactly one plan named (ours), 'unchanged'
    ```

    Exactly one plan is named per invocation, so no selector over-matched.

    THE REAL WRITE, same 30, same guards:

    ```text
    === REAL WRITE: 30 plans ===
    --- ao1rb7  writes=Priority+Work-Kind  src=wjl471 -> high/feature
        -    plan        20260908-commitguard-00-ao1rb7  unchanged
    --- s0gnha  writes=Priority  src=yxfw4k -> high/bug
        - >  plan        20260919-reaskscore-00-s0gnha  [blocking]  unchanged
    [...]
    invocations: 30   stop-conditions: 0
    ```

    THE FIRST PLAN'S REAL DIFF, showing only the two fields plus one history line and `- Status:` UNCHANGED (it is a context line, not a changed one):

    ```diff
    --- a/.aw/records/plans/pending/20260908-commitguard-00-ao1rb7-...ipd.md
    +++ b/.aw/records/plans/pending/20260908-commitguard-00-ao1rb7-...ipd.md
    @@ -7,6 +7,8 @@
      - Item-Dependencies: none
      - Status: approved
    +- Work-Kind: feature
    +- Priority: high
      - Readiness: go-pending-approval
      - Set: commitguard
    @@ -17,6 +19,7 @@
      ## Workflow history
    +- 2026-09-23 approved (aw set): Backfilled Priority and Work-Kind by inheritance from source backlog item wjl471 (planprio Order 02, plan 8u6770, E-03); no lifecycle transition occurred.
      - 2026-09-13 approved (aw set): status set to approved
    ```

    THE HISTORY LINE CARRIES THE SUPPLIED `--message`, not `status set to approved`, and it names the source item, the fields written, and states plainly that no transition occurred. (The line BELOW it, `2026-09-13 approved (aw set): status set to approved`, is pre-existing and is left untouched; it is an instance of the same defect from an earlier round and is not this plan's to rewrite.)

    SPOT CHECK OF THREE MORE PLANS' METADATA BLOCKS, read back from disk after the write:

    ```text
    5e4sb6: - Status: approved / - Work-Kind: chore / - Priority: medium / - Readiness: go / - Set: rununify / - Order: 0 / - Id: 5e4sb6 / - Blocks-Release: next / - From-Backlog: dhuape
    i8u6hh: - Status: approved / - Work-Kind: bug / - Priority: medium / - Blocks-Release: next / - Readiness: go-pending-approval / - Set: verstamp / - Order: 1 / - Id: i8u6hh / - From-Backlog: ygtykn
    s0gnha: - Status: approved / - Priority: high / - Readiness: go-pending-approval / - Set: reaskscore / - Order: 0 / - From-Backlog: yxfw4k / - Blocks-Release: next / - Work-Kind: bug / - Id: s0gnha
    ```

    Each holds the inherited values, each `- Status:` still reads `approved`, and `s0gnha` shows the partial case: its `Priority` was added while its pre-existing `Work-Kind: bug` stayed where it was.

    EVERY INVOCATION USED AN id6, `--no-commit` AND `--message`, and no hand-edit was used anywhere. The exact command form, built per row from the derived table:

    ```python
    cmd = ["aw", "ipd", "set", t["status"], t["id6"]]          # id6 ONLY, never a setid
    if t["need_priority"]:  cmd += ["--priority",  t["src_priority"]]
    if t["need_work_kind"]: cmd += ["--work-kind", t["src_work_kind"]]
    cmd += ["--message", msg, "--no-commit", "--yes"]          # + "--dry-run" on the preflight pass
    ```

    `--no-commit` on all 30 means the setter never offered a commit mid-loop, so nothing of another agent's could be swept; the commit was made deliberately at the end through `aw commit` with explicit paths.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff --stat` over this item's commits, and a grep proving no plan's `Status`/`Readiness`/`Set`/`Order`/`Id` line changed. Paste `git status --porcelain -- .aw/records/plans/executed .aw/records/plans/superseded .aw/records/plans/not-executed` showing it EMPTY, which is the proof no setid mis-selection reverted a terminal plan; a non-empty result here is a FAILED validation regardless of everything else. Paste `aw check plans` with its error count and per-rule breakdown COMPARED to the baseline captured before the first edit, naming any new rule id; review's baseline is `errors 140` (124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`). Do NOT claim it clean and do NOT reduce the count by editing another party's plan. Paste `git diff --cached --name-only` from before the final commit proving only this item's files were staged.
  - Observed evidence: `git diff --stat` over the 30 backfilled plans, before committing:

    ```text
    30 files changed, 87 insertions(+)
    ```

    THE DECISIVE NUMBER IS THE DELETION COUNT, AND IT IS ZERO, which is a stronger proof than any grep can give:

    ```text
    $ git diff --numstat -- .aw/records/plans/pending | awk '{a+=$1; d+=$2} END {...}'
    insertions=87  deletions=0
    ```

    A PURE-INSERTION DIFF MEANS NO PRE-EXISTING LINE WAS TOUCHED AT ALL. `Status`, `Readiness`, `Set`, `Order`, `Id`, `Approval`, `Item-Dependencies`, `Blocks-Release`, `From-Backlog`, `Scope-Paths`, `Kind`, `Date` and `Author` are therefore provably unchanged on all 30 plans without enumerating them, because changing any of them would require a deletion. The grep the item asks for confirms it from the other direction (no such field appears as an added OR removed line anywhere in the diff):

    ```text
    $ git diff -U0 -- .aw/records/plans/pending | grep -E '^[+-]- (Status|Readiness|Set|Order|Id|Approval|Item-Dependencies|Blocks-Release|From-Backlog|Scope-Paths|Kind|Date|Author):'
    NONE (grep found no such line in the diff)
    ```

    The 87 insertions classify exactly, with nothing unaccounted for:

    ```text
      30  +- Priority: <value>
      30  +- <date> approved (aw set): <message>
      27  +- Work-Kind: <value>
    ```

    (27 rather than 30 `Work-Kind` lines because `s0gnha`, `dy9ymn` and `svacmz` already carried it.)

    THE TERMINAL-DIRECTORY PROOF IS EMPTY, which is the assertion that would have caught `f5pttg` before it committed:

    ```text
    $ git status --porcelain -- .aw/records/plans/executed .aw/records/plans/superseded .aw/records/plans/not-executed
    [0 lines]
    ```

    `git status --porcelain` over the whole repo listed exactly the 30 modified plans plus this plan's own file, all under `pending/`, all in the derived table; the post-commit tree is clean (0 lines).

    `aw check plans` COMPARED PER RULE ID AGAINST A BASELINE CAPTURED BEFORE THE FIRST EDIT. NOT claimed clean, and nothing was "fixed" by editing another party's plan:

    ```text
    BEFORE (exit 1)                          AFTER (exit 1)
      errors  41   warnings  0                 errors  41   warnings  0
      36 check.ipd-uncarried-obligation        36 check.ipd-uncarried-obligation
       3 check.lifecycle-transition-invalid     3 check.lifecycle-transition-invalid
       1 check.ipd-lint-diagnostic              1 check.ipd-lint-diagnostic
    ```

    IDENTICAL. No new rule id, no increased count; the two captures differ only in elapsed-time and in the nondeterministic ordering of the advisory `Next inspect ...` lines. The full `aw check` was compared the same way and is also identical (`errors 54`, per-rule counts equal, including the 2 pre-existing `check.live-bug-ungated` and the 1 `check.from-backlog-gate-mismatch`, none of them ours).

    THE BASELINE IS NOT THE ONE THE ITEM RECORDS, and this is worth stating rather than quietly substituting: review measured `errors 140` dominated by 124 `check.scope-drift`, and at this HEAD it is `errors 41` with `check.scope-drift` at ZERO and a rule (`check.ipd-uncarried-obligation`) that did not appear in review's mix at all. Eleven days of work moved it. This is exactly why the item says capture a fresh baseline; a per-rule comparison against review's recorded numbers would have reported a spurious improvement of 99 errors.

    THE STAGED SET WAS VERIFIED BEFORE THE COMMIT, per the shared-checkout rule. `git diff --cached --name-only` immediately before committing listed 31 paths, all under `.aw/records/plans/pending/`: the 30 backfilled plans plus this plan's own file carrying the E/V evidence, and nothing else. The commit went through `aw commit 8u6770 -- <31 explicit paths>` (never `git add -A`, never `-a`, never `--no-verify`), which snapshots the index before staging and commits only the intersection of its own staged set with the named paths, so a co-worker's path could not enter it. It reported `committed 31 path(s): af28bde5`, and `git show --numstat` confirms the 30 backfilled plans contribute `87 insertions, 0 deletions` while the 26 deletions in the commit total are entirely this plan's own replaced E/V placeholder lines.

    A SECOND COMMIT CARRIES THIS EVIDENCE PLUS TWO BACKLOG ITEMS, and the reason it was ALLOWED is itself a defect worth recording here rather than only in its own item. This plan's `- Scope-Paths:` is `.aw/records/plans/pending`, so a `.aw/records/backlog/open/...` path should have been REFUSED by the scope gate; it was accepted. Investigated rather than taken as permission: `ipd_lifecycle._scope_match` (`ipd_lifecycle.py:1969-1998`) falls back, for any pattern containing `**`, to `prefix = pat.split('**',1)[0]` and a bare prefix test, DISCARDING the filename, so the implicit allowance `.aw/records/**/index.md` in fact matches EVERY path under `.aw/records/<anything>/`. Driven: `_scope_match('.aw/records/backlog/open/anything.backlog.md', '.aw/records/**/index.md')` is `True`. The same loose branch evaluates AUTHOR-DECLARED scopes too (`_scope_match('agent_workflows/README.md','agent_workflows/**/*.py')` is `True`), so it loosens both the commit refusal and finalize's scope-drift reconciliation. Filed as backlog `cfab6d` (high, bug, gates next). THE BACKLOG PATHS IN THAT COMMIT ARE STILL LEGITIMATE on their own terms: the turn contract REQUIRES filing a carrier for each defect found, so they are this turn's own work rather than a co-worker's, and no path belonging to anyone else entered either commit.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `FORCE_COLOR=1 aw att --type plan` showing a populated Priority column, and `aw att --type plan --format json` with the count of plan items whose `priority` is non-null, captured BEFORE the first edit and AFTER the last, with the delta stated and matched against the number of plans written. Do NOT paste a piped `aw att --type plan` and call the missing column a failure; that surface has no Priority column by design.
  - Observed evidence: `aw att --type plan --format json` captured BEFORE the first edit and AFTER the last, counting plan items whose `priority` key is non-null:

    ```text
    ALL PLAN ITEMS         before 712   after 712
    priority NON-NULL  ALL before  36   after  66   delta 30
    PENDING plan items     before  54   after  54
    priority NON-NULL PEND before  11   after  41   delta 30
    distribution over PENDING items AFTER: {'medium': 21, 'high': 20, None: 13}
    ```

    THE DELTA IS EXACTLY 30 ON BOTH SCOPES AND MATCHES THE 30 PLANS WRITTEN, which is this plan's deliverable stated as a number rather than an impression. The item count is unchanged at 712 (54 pending), so nothing was created or lost. The 13 remaining nulls are precisely V-06's residue, and the pending board is now 41 of 54 prioritized where it was 11 of 54.

    `FORCE_COLOR=1 aw att --type plan` RENDERS A POPULATED Priority COLUMN (ANSI escapes stripped here for legibility; the column exists only on this renderer, which is why the piped surface was never used as evidence):

    ```text
      Status   Type     Blocks Priority Readiness OQs  Exec Valid Date     SetID        N  ID6    Deps
    ◕ approved plan          -  high     go-pend?  2/2  0/3  0/3  20260908 commitguard  00 ao1rb7 -
    ◕ approved plan          -  medium   go-pend?  1/1  0/3  0/3  20260908 graduate     00 y9s4vm -
    ◕ approved plan          -  medium   go-pend?  3/5  0/6  0/6  20260908 graduate     02 iuxtjy jxxec8
    ◕ approved plan          -  medium   go-pend?  1/1  0/3  0/3  20260908 runnerlayer  00 lyo1tz -
    ◕ approved plan          -  medium   go-pend?  0/3  0/7  0/7  20260908 runnerlayer  02 1f7xno 9kmbr0
    ◕ approved plan          -  high     go-pend?  0/4  0/6  0/6  20260908 setidhard    02 bwgyum -
    ◕ approved plan          -  medium   go-pend?  2/5  0/4  0/4  20260908 specdirs     00 wfjsp4 -
    ◕ approved plan          -  -        go-pend?  1/2  0/2  0/2  20260910 planprio     00 d0cbt3 -
    ◕ approved plan          -  -        go-pend?  0/2  0/9  0/9  20260910 planprio     01 lkexaw 8u6770, lc4unl
    ◕ approved plan          -  -        go-pend?  1/3  0/6  0/6  20260910 planprio     02 8u6770 -
    ◕ approved plan          -  high     go-pend?  1/3  0/1  0/1  20260917 hostdedup    00 a5wdne -
    ◕ approved plan          -  high     go-pend?  0/3  8/8  8/8  20260917 hostdedup    01 li44r9 -
    ◕ approved plan          -  -        go-pend?  0/5  0/7  0/7  20260917 hostdedup    02 nmlx47 li44r9
    ◕ approved plan      2.0.0 medium    go        0/3  1/3  0/3  20260829 rununify     00 5e4sb6 -
    ◕ approved plan      2.0.0 high     go-pend?  1/3  0/6  0/6  20260908 runverdict   07 w33lrl -
    ```

    Rows this backfill wrote render a value (`ao1rb7` `high`, `y9s4vm`/`lyo1tz`/`5e4sb6` `medium`); rows it deliberately did not reach still render `-` (`d0cbt3`, `lkexaw`, `8u6770`, `nmlx47`), which is the correct "unprioritized" rendering for an absent value and confirms nothing was fabricated to fill the column.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the post-write count of pending plans still missing either field, and reconcile it against sibling 03's no-source population (review measured 28). If the residue exceeds that, state what was skipped rather than reporting success. Paste the list of every plan skipped with its reason (dangling reference, already carried both fields, or deferred pending OQ-02). Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline and compare failure SETS, not counts; review's reading at HEAD `fe57b1a4` was `5971 passed, 3 skipped, 2 xfailed in 59.68s`, reference only.
  - Observed evidence: the post-write residue, re-derived from disk:

    ```text
    PENDING PLANS: 54
    STILL MISSING EITHER FIELD (the RESIDUE): 13

      04vf1h   neither field   NO SOURCE -> sibling 03 (lc4unl)
      2xz59a   neither field   NO SOURCE -> sibling 03 (lc4unl)
      7p3tt8   neither field   NO SOURCE -> sibling 03 (lc4unl)
      8u6770   neither field   NO SOURCE -> sibling 03 (lc4unl)   [this plan itself]
      d0cbt3   neither field   NO SOURCE -> sibling 03 (lc4unl)   [this Set's orchestrator]
      gqo6if   neither field   NO SOURCE -> sibling 03 (lc4unl)
      lc4unl   neither field   NO SOURCE -> sibling 03 (lc4unl)   [sibling 03 itself]
      lkexaw   neither field   NO SOURCE -> sibling 03 (lc4unl)   [sibling 01]
      nmlx47   neither field   HAS SOURCE 'dstnso, 8hx3g3' -> UNRESOLVABLE (multi-valued), reported by E-01
      qdd5jq   neither field   NO SOURCE -> sibling 03 (lc4unl)
      tb63qv   neither field   NO SOURCE -> sibling 03 (lc4unl)
      ubac5n   neither field   NO SOURCE -> sibling 03 (lc4unl)
      x75obw   neither field   NO SOURCE -> sibling 03 (lc4unl)

    RECONCILIATION:
      residue total                          13
      of which NO SOURCE (sibling 03's own)  12
      of which UNRESOLVABLE SOURCE (skipped)  1
      residue == no-source + unresolvable-source: True
    ```

    THE RESIDUE RECONCILES EXACTLY WITH NO UNEXPLAINED REMAINDER. It is 13 rather than 12 because it legitimately carries one plan sibling 03 does NOT own: `nmlx47` has a source (two, in fact), so it falls outside that plan's population, which is defined by carrying none. The item's stop-rule ("if the residue is larger than sibling 03's population, something was skipped") is therefore satisfied by naming the one extra plan and why, not by the raw comparison.

    RE-RUNNING E-01's DERIVATION AFTER THE WRITE REPORTS A WRITE POPULATION OF 0, which is the cleanest proof nothing in scope was missed:

    ```text
    CARRYING - From-Backlog:  33     RESOLVING SOURCES: 32
    ALREADY CARRY BOTH (EXCLUDED): 32
    CARRY EXACTLY ONE (partial):    0
    CARRY NEITHER:                  0
    WRITE POPULATION:               0
    ```

    All 32 pending plans with a resolving source now carry both fields (2 already did, 30 were written).

    EVERY PLAN SKIPPED, WITH ITS REASON. (1) UNRESOLVABLE SOURCE, 1: `nmlx47` (`- From-Backlog: dstnso, 8hx3g3`; no shipped reader matches a multi-valued value, so both ids resolve to nothing). Filed as backlog `6os96s`; NOT guessed at, and NOT reassigned to sibling 03. (2) ALREADY CARRIED BOTH FIELDS, 2: `87apfx` (`high`/`bug`), `n9na1c` (`medium`/`bug`); excluded rather than overwritten, since replacing a deliberate value with an inherited one is a downgrade. (3) NO SOURCE, 12, sibling 03's work: `04vf1h`, `2xz59a`, `7p3tt8`, `8u6770`, `d0cbt3`, `gqo6if`, `lc4unl`, `lkexaw`, `qdd5jq`, `tb63qv`, `ubac5n`, `x75obw`. (4) DEFERRED PENDING OQ-02: NONE. The maintainer's Ruling 1 answered it, so all 30 were written.

    SIBLING 03's POPULATION IS 12, NOT THE 28 REVIEW MEASURED NOR THE 20 IT AUTHORED, and the difference is not only attrition:

    ```text
    pending plans carrying no - From-Backlog:        21
      of those, still missing a field (its work)     12
      of those, already complete (no decision owed)   9
    ```

    Nine of the 21 no-source plans already hold both fields, so sibling 03's decision table needs 12 rows and not 21. Its own E-01 is told to re-derive, so this is orientation for it rather than a figure to copy.

    THE BARE SUITE, run as `python3 -m pytest` with the configured `addopts` untouched:

    ```text
    1 failed, 8688 passed, 3 skipped, 2 xfailed, 6 warnings in 199.34s (0:03:19)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    THE FAILURE SET IS COMPARED, NOT THE COUNT, AND THE ONE FAILURE IS PROVEN NOT TO BE THIS PLAN'S. It is an ENVIRONMENT LEAK, established by three measurements rather than by assertion. FIRST, the test asserts a non-isolated turn receives no `OPENCODE_CONFIG_CONTENT`, and that variable is present in THIS LANE's ambient environment (this turn runs inside an isolated lane worktree whose own runner set it), so the value the test reads is inherited from the process rather than produced by the code under test. SECOND, clearing just that one variable turns the suite green with no other change:

    ```text
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest
    8689 passed, 3 skipped, 2 xfailed, 6 warnings in 138.48s (0:02:18)
    ```

    THIRD, and decisively, the failure REPRODUCES WITH THIS PLAN'S CHANGES STASHED: stashing the 30 modified plans and running the single test still fails, so the pre-edit baseline carries the same failure and the failure SET is UNCHANGED (before: {this test}; after: {this test}). It is also a KNOWN, ALREADY-FILED defect rather than a new discovery: backlog `4vn040` and roughly twenty duplicate items describe exactly it. Review's `5971 passed` is reference only; the suite has grown to 8689 tests in the interim.

    `aw sanitize --agent` is CLEAN:

    ```text
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and carries `- Readiness: no-go`. It must NOT be executed: TWO blocking questions stand, this plan's own OQ-02 (the false history line on the 5 approved plans) and the PARENT's OQ-02 (the dependency edge below), so `aw ipd lint` refuses it at every checkpoint until both are answered and a human then sets it `approved`. Answer them with `/askme`.

IT CARRIES `- Item-Dependencies: executed:lkexaw`, AND THAT EDGE IS THE PARENT'S BLOCKING DEFECT RATHER THAN A SETTLED CHOICE. The authored justification read: "backfilling before the gate and the scaffold fix exist would write values nothing enforces and would leave the root cause in place." THAT REASONING DOES NOT SURVIVE THE PARENT'S MEASUREMENT and is retained here only so the correction is visible. A value written before the gate exists is precisely what the gate then finds satisfied, and the parent's review measured that this edge strands 18 already-approved pending plans the moment sibling 01 lands (parent PR-001, parent blocking OQ-02, three costed options with "stamp the corpus inside Order 01" recommended). If that answer reverses or removes this edge, the `- Item-Dependencies:` line here must be brought into agreement in the same change. Do not defend the edge with the sentence above.

Execution contract for whoever runs it: commit ONLY paths under the declared `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE SHARED-CHECKOUT HAZARD, which is this plan's main execution risk: it edits roughly 81 tracked files while other agents commit concurrently. Verify `git diff --cached --name-only` before EVERY commit, re-verify after any failed hook (pre-commit's stash/restore can leave another agent's paths in the index), and never revert or sweep in a change you did not make. Pass `--no-commit` on every setter call so the tool never offers a commit mid-loop.

SIX CORRECTIONS FROM REVIEW THAT MUST NOT BE RE-INHERITED, each measured rather than reasoned:

1. SELECT BY id6, NEVER BY SETID. 6 of the 57 setids in this population also name a terminal plan, and `aw ipd set approved rununify --dry-run` reports `executed -> approved` on TWO plans in `executed/`. Backlog `f5pttg` records this exact command having reverted seven executed plans, and it is still `open`. Dry-run every call and read the output.
2. PASS `--message`, OR THE SETTER WRITES A FALSE HISTORY LINE. A same-status call records `status set to approved` on a plan that did not transition. That is this plan's blocking OQ-02.
3. EXCLUDE THE 11 PLANS THAT ALREADY CARRY BOTH FIELDS. The population is 81, not 92 and not the authored 84; overwriting an existing value with an inherited one is a downgrade.
4. DO NOT RE-QUOTE ANY COUNT. Authored `84 of 104` and review's `81 of 120` are both historical; E-01 derives a third.
5. DO NOT REQUIRE `aw check plans` CLEAN. It carries 140 pre-existing errors this plan does not cause; compare per rule id against a pre-edit baseline and never reduce a count by editing another party's plan.
6. DO NOT READ THE PRIORITY COLUMN FROM A PIPED `aw att`. That surface has none; use `FORCE_COLOR=1` or `--format json`.
