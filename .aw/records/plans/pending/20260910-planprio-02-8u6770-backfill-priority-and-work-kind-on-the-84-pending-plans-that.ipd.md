# IPD: Backfill Priority and Work-Kind on the 84 pending plans that can inherit from their source item

- Date: 2026-09-10
- Kind: child
- Concern: Most pending plans record the backlog item they graduated from, every one of those references resolves, and every source carries both `Priority` and `Work-Kind`. So those plans can be given both values with no judgement call, purely by inheriting from a source the plan itself names. RE-MEASURED AT REVIEW (2026-09-12, HEAD `fe57b1a4`), because the authored figures are stale: 120 pending plans (authored 104), 92 carrying `- From-Backlog:` (authored 84), 0 dangling, 0 sources missing a field, 11 plans ALREADY carrying both fields, so the real backfill population is 81 and the no-source remainder is 28 (authored 20). Do NOT re-quote these either; E-01 re-derives them.
- Scope: Inherit `Priority` and `Work-Kind` from each pending plan's `- From-Backlog:` source, writing them through the shipped `aw ipd set` setters rather than by hand. Does NOT decide a value for any plan lacking a source (sibling 03 owns those), does NOT touch terminal plans, and does NOT change any vocabulary or add a sort key.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: executed:lkexaw
- Status: reviewed
- Readiness: no-go
- Set: planprio
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8u6770

## Workflow history

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

- [ ] E-01 RE-DERIVE THE INHERITANCE TABLE AT EXECUTION TIME AND PRINT IT, one row per plan: the plan's id6, its CURRENT `- Status:`, its `- From-Backlog:` source id6, the source's `Priority` and `Work-Kind`, and the source's own file path. DO NOT REUSE ANY COUNT FROM THIS PLAN OR ITS PARENT. Both authored figures and review figures are historical; derive a third and record the difference.
  EXCLUDE A PLAN THAT ALREADY CARRIES BOTH FIELDS, which the authored item never said and which changes the population. Measured at review: 11 pending plans already carry both, so the set needing a write is 81 of the 92 with a resolving source, not 92. Writing over an existing value would overwrite a deliberate choice with an inherited one, which is a silent downgrade rather than a backfill. A plan carrying exactly ONE of the two fields is IN scope for the missing field only, and the table must say which.
  RECORD THE STATUS PER ROW, because it decides the setter invocation and it is where the danger is. Measured at review, the 81 split 76 `reviewed` and 5 `approved`, and the `approved` five are the ones E-03's history-line problem applies to (OQ-02).
  PARENT COUNTS FOR ORIENTATION ONLY, not to be quoted as findings: the parent's review measured 120 pending, 92 with a resolving source, 81 still needing a field, 28 with no source.
  RESOLVE, DO NOT PARSE. A `- From-Backlog:` id6 must be resolved to an actual backlog file, exactly as `check.from-backlog-dangling` already does. A dangling reference must be REPORTED and SKIPPED, never guessed at, and never silently treated as a plan with no source (that would move it into sibling 03's population without anyone deciding to). Measured at review: zero dangle today, so a dangling reference appearing at execution time is NEW and worth reporting as such.
  - Depends on: none
  - Expected outcome: a printed per-plan table carrying id6, current status, source id6, the source's two values and its path; the count stated and compared to review's 81; plans already carrying both fields listed as EXCLUDED; any dangling reference named and excluded.
  - Execution state: pending

- [ ] E-02 SANITY-CHECK THE DERIVED VALUES BEFORE WRITING ANY, because inheritance is only as good as the sources. Report the distribution and inspect the tails: any source whose `Priority` is absent or outside `low|medium|high`, any whose `Work-Kind` is outside `bug|feature|chore|security|followup`, and any plan whose inherited `Priority` disagrees with its own `- Blocks-Release:` state in a way worth flagging (a release-blocking plan inheriting `low` is not necessarily wrong, but it should be SEEN rather than written silently).
  DO NOT CORRECT A SOURCE ITEM. If a source's value looks wrong, report it; editing backlog items is outside this plan's declared scope and belongs to whoever owns that item.
  REVIEW ALREADY RAN THIS CHECK, so the executor knows what to expect and a divergence is itself informative. Measured at HEAD `fe57b1a4` over the 81: ZERO out-of-vocabulary and ZERO absent source values, so every source is clean. The inherited distribution is 25 `high`/`bug`, 25 `medium`/`bug`, 10 `high`/`feature`, 9 `medium`/`feature`, 6 `medium`/`chore`, 3 `low`/`feature`, 1 each of `medium`/`followup`, `high`/`security`, `low`/`followup`. And the release-blocking tail is 17 of 81, ALL of them `medium` and NONE `low`, which is the specific list OQ-01 exists to have a human see.
  - Depends on: E-01
  - Expected outcome: the distribution printed and compared to review's, every out-of-vocabulary or absent source value named (expect none), and every release-blocking plan inheriting `low` or `medium` listed with its id6 for a human to see (expect about 17, all `medium`).
  - Execution state: pending

- [ ] E-03 WRITE THE VALUES THROUGH THE SHIPPED SETTER, one plan at a time, using the EXACT form review verified: `aw ipd set <that-plan's-current-status> <id6> --priority <p> --work-kind <k> --message "<why>" --no-commit --yes`. Every element of that line is load-bearing and three of them were added at review.
  USE THE id6, NEVER A SETID, AND THIS IS THE ITEM'S SHARPEST HAZARD. A setid selector resolves to EVERY plan carrying it, including terminal ones. MEASURED at review: 6 of the 57 setids in this population also name a plan in `executed/`, and `aw ipd set approved rununify --priority medium --work-kind chore --dry-run` reports `executed -> approved` on TWO plans in `executed/`. That is backlog `f5pttg`, a shipped high-priority defect recording that this exact command silently reverted seven executed plans in one invocation. The affected setids measured at review: `hostdefault`, `integearn`, `integpath`, `lanectn`, `rununify`, `setidhard`.
  DRY-RUN EVERY INVOCATION FIRST AND READ ITS OUTPUT. `--dry-run` is honored on this path (verified: it prints the would-be transition and writes nothing). If a dry-run line reads anything other than `unchanged` for exactly the one plan you named, STOP: you have selected more than you meant to. This is the unsafe-condition stop, not a scope stop.
  PASS `--no-commit`. Without it the setter offers to commit, and in this shared checkout accepting that offer mid-loop is how another agent's staged work gets swept into your commit. Commit deliberately at the end, path-scoped, after verifying the index.
  PASS `--message`, WHICH IS NOT OPTIONAL POLISH BUT THE FIX FOR A FALSE HISTORY CLAIM (OQ-02). MEASURED at review on `5e4sb6` (`approved`): without `--message`, a same-status call appends `- <date> approved (aw set): status set to approved`, asserting a transition that did not occur; with `--message`, that line carries the supplied text instead. Supply something true, naming the source item, for example "Inherited Priority/Work-Kind from source backlog item <src-id6>; status unchanged." DO NOT PROCEED PAST THE FIRST `approved` PLAN UNTIL OQ-02 IS ANSWERED, because whether writing any history line onto an approved plan is acceptable is the maintainer's call; the 76 `reviewed` plans are unaffected by that question.
  DO NOT HAND-EDIT FRONT MATTER, and do not batch-rewrite with a script that writes the lines directly. The setter owns field position and history, and a direct write would bypass both. If the setter cannot express a case, report it rather than working around it. NOTE the setter inserts both fields directly after `- Status:` (verified), which differs from where a hand-editor would likely put them; that is the setter's choice and is correct.
  THE NO-OP WRITE IS VERIFIED TO WORK ON BOTH STATUSES IN THIS POPULATION, so no discovery is needed: driven at review in a throwaway copy, `reviewed` and `approved` both accepted the call, exited 0, printed `unchanged`, and wrote both fields with `- Status:` untouched. What the authored item called an unknown ("a no-op transition on some statuses may refuse") is settled for the two statuses that actually occur here.
  - Depends on: E-02
  - Expected outcome: every derived plan carries both fields with the inherited values; every invocation used an id6, a dry-run preflight, `--no-commit` and a truthful `--message`; no plan's `- Status:` changed; no plan outside the derived table was touched; OQ-02's answer recorded before any `approved` plan was written.
  - Execution state: pending

- [ ] E-04 PROVE NOTHING ELSE MOVED, which matters because this plan edits roughly 81 files in a shared checkout. Show that only the two field lines and each plan's history changed, that no plan's `Status`, `Readiness`, `Set`, `Order` or `Id` differs, and that `aw check plans` and `aw ipd lint` report NO NEW rule id and no increased count.
  PROVE NO TERMINAL PLAN WAS TOUCHED, which is the specific proof that a setid mis-selection did not happen: `git status --porcelain -- .aw/records/plans/executed .aw/records/plans/superseded .aw/records/plans/not-executed` must be EMPTY. Given the measured 6-setid collision, this is the assertion that would have caught `f5pttg` before it committed.
  DO NOT REQUIRE `aw check plans` TO BE CLEAN. Measured bare at review (HEAD `fe57b1a4`), it exits 1 with `errors 140  warnings 0`, none of it caused by this plan: 124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`. Capture that count BEFORE the first edit and compare. An executor told to make it clean would either stall or "fix" other agents' plans, which the shared-checkout rule forbids.
  RE-VERIFY THE INDEX BEFORE EACH COMMIT. Other agents are committing concurrently; `git diff --cached --name-only` must contain only plans this item changed, and a failed hook invalidates that check (re-run it after any failure).
  - Depends on: E-03
  - Expected outcome: a diff summary showing only the expected field and history lines, an assertion that no other metadata field changed on any plan, an empty terminal-directory status, and `aw check plans` compared per rule id against the pre-edit baseline.
  - Execution state: pending

- [ ] E-05 PROVE THE BACKFILL IS OBSERVABLE ON A SURFACE AN AGENT CAN CAPTURE, because a populated field nobody can read has not achieved this plan's goal.
  USE THE TWO SURFACES THAT ACTUALLY CARRY PRIORITY, and not the one the authored V-04 named. MEASURED at review: a piped `aw att --type plan` emits `- [plans] <path> (<status>)` with NO Priority column, because the column exists only in the colored table renderer. The two surfaces that answer the question are `FORCE_COLOR=1 aw att --type plan` and `aw att --type plan --format json`, whose per-item `priority` key is machine-readable.
  STATE A BEFORE AND AFTER COUNT, not a screenshot impression: the number of plan items whose `priority` is non-null in `--format json`, captured before the first edit and after the last. That delta is this plan's actual deliverable.
  - Depends on: E-04
  - Expected outcome: both surfaces pasted, and the non-null `priority` count stated before and after with the delta matching the number of plans written.
  - Execution state: pending

- [ ] E-06 REPORT WHAT REMAINS, so the Set's next step is grounded in a measurement rather than in this plan's authored estimate.
  AFTER THE WRITE, RE-COUNT the pending plans still missing either field and confirm the number equals the no-source population that sibling 03 owns. Review measured 28 with no source; if the residue is larger than that, something in the derivation was skipped and this item must say so rather than reporting success.
  NAME ANY PLAN SKIPPED AND WHY, including a dangling reference from E-01, a plan already carrying both fields, and any plan whose write was deferred pending OQ-02. A silent skip is how a backfill reports completion while leaving holes.
  - Depends on: E-05
  - Expected outcome: the residual count stated and reconciled against sibling 03's population, with every skipped plan named and its reason given.
  - Execution state: pending

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
- Status: open
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: MEASURED BY EXECUTION, NOT PREDICTED, WHICH IS WHY IT IS BLOCKING. Driven at review in a throwaway repo copy on plan `5e4sb6` (status `approved`, needing both fields): `aw ipd set approved 5e4sb6 --priority medium --work-kind chore` exits 0, prints `unchanged`, correctly writes both fields, leaves `- Status:` untouched, AND prepends `- 2026-09-12 approved (aw set): status set to approved` to the workflow history. That line asserts an approval event that did not occur, on a plan whose real approval is already recorded with its own date and actor. This Set exists to make plan metadata trustworthy, so writing 5 fabricated approval events in service of it is a self-defeating outcome and not a cosmetic blemish.
  A REMEDY EXISTS AND IS VERIFIED. Passing `--message "<text>"` replaces the fabricated sentence with the supplied one, confirmed in the same copy: the line became `- 2026-09-12 approved (aw set): Inherited Priority/Work-Kind from source backlog item dhuape; status unchanged.` The actor is still `aw set` and the leading status token is still `approved`, so the line remains a HISTORY RECORD tagged with the current status rather than a claim of change; whether that is honest enough is the judgement.
  THE SCOPE IS 5 PLANS, NOT 81. The 76 `reviewed` plans get the same treatment, but a line reading `reviewed (aw set): Inherited ...` on a plan that IS `reviewed` asserts nothing false, so the question is confined to the 5 `approved` ones. That is what makes deferring them cheap if the maintainer prefers.
  RELATED SHIPPED DEFECTS, cited so the maintainer sees this is a known family rather than a one-off: backlog `x6tk1u` (`open`, high) records that a same-status `--message` is silently DISCARDED on the backlog path, and its analysis names `status_set.apply_status_change` as the shared setter behind `aw ipd set`. So the plan path writing a line and the backlog path dropping one are two faces of the same unresolved design question about what a no-op transition should record.
  THREE OPTIONS. (a) WRITE WITH A TRUTHFUL `--message` ON ALL 81, accepting one extra history line per plan. Cost: 81 plans gain a line whose leading token repeats their current status, and 5 of those sit on approved plans where a careless later reader could misread it as a re-approval. Benefit: one uniform invocation, the whole population done in one pass, and the message states the provenance the Set wants recorded anyway. (b) WRITE THE 76 `reviewed` PLANS NOW AND DEFER THE 5 `approved` ONES to a follow-up that fixes the setter first. Cost: the Set finishes incomplete and 5 approved plans keep an absent Priority, which is exactly what the parent's PR-001 says makes them unrunnable once the gate lands. Benefit: not one false or ambiguous line is written. (c) FIX THE SETTER FIRST so a field-only no-op writes no history line at all, then backfill. Cost: that is code work in `status_off`/`status_set` outside this plan's declared `Scope-Paths` and would need its own plan, blocking this Set behind it; it also intersects `x6tk1u`, whose preferred fix moves in the opposite direction (make a message a mutation). Benefit: the cleanest records and it fixes the defect for every future caller.
  RECOMMENDATION (a), because a truthful `--message` makes each line accurate on its own terms, the provenance it records is genuinely wanted, and (b) leaves precisely the plans the parent's blocker is about without a value. (c) is the right long-term fix and the wrong thing to block this Set on; it should be filed as its own carrier either way.
  DELIBERATELY NOT DONE HERE: review did not write to the real tree, did not modify the setter, and did not file the follow-up carrier, because filing work and choosing among three options that trade record cleanliness against Set completeness is the maintainer's call.

### OQ-03: This plan's dependency edge is the parent's blocking defect. Answer the PARENT's OQ-02, then bring this plan's `- Item-Dependencies:` into agreement.

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: THIS QUESTION IS ANSWERED AT THE PARENT, NOT HERE, AND IT EXISTS HERE SO THE GATE HOLDS ON THIS FILE TOO. Review initially recorded PR-001 as merely inherited, reasoning that duplicating the parent's question would ask the maintainer to answer it twice. `aw check` then flagged this file with `check.review-finding-unescalated`, which is correct and is why the rule exists: a BLOCKER left OPEN must refuse execution of the artifact it is about, and this child is the artifact that carries the edge. So the question is recorded here with its finding id; ANSWER IT ONCE, on the parent (`d0cbt3` OQ-02), and record the same answer here rather than re-deciding it.
  THE SUBSTANCE, stated so this entry is decidable without opening the parent. `- Item-Dependencies: executed:lkexaw` makes this backfill wait for the child that installs the requiredness gate. The parent's review measured that ordering as stranding 18 already-approved pending plans the moment sibling 01 lands, because the gate fires at EVERY lint phase for a plan whose persisted status is at the ready-to-execute tier; of those 18, only 5 are reachable by this plan's inheritance and the other 13 need sibling 03's human decision table. The parent offers three costed options (stamp the exemption marker inside Order 01, as the shipped `oorry1` precedent did; reverse the order so the backfills run first; or stage the gate as advisory then flip it) and recommends the first.
  WHAT MUST HAPPEN IN THIS FILE once the answer is recorded: if the answer removes or reverses the edge, the `- Item-Dependencies:` line here must change in the same commit, because the parent's child table and this child's front matter are two statements of one fact and a disagreement between them is what a runner reads wrongly. If the answer keeps the edge (option (a) keeps it while making it harmless), the line stays and this question closes citing that.
  DO NOT DEFEND THE EDGE WITH THIS PLAN'S AUTHORED JUSTIFICATION, which the parent's measurement contradicts: "backfilling before the gate exists would write values nothing enforces" inverts the mechanism, since a value written before the gate exists is precisely what the gate then finds satisfied.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full re-derived table with the command that produced it, carrying id6, current status, source id6, the source's two values and its path. State the count and how it differs from review's 81 and the authored 84. Paste the list of plans EXCLUDED because they already carry both fields (review measured 11) and the per-status split of the write population (review measured 76 `reviewed`, 5 `approved`). Paste any dangling `- From-Backlog:` found, or state that none was; review measured zero, so any occurrence is new.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the value distribution and compare it to review's reading. Paste every source value outside the two vocabularies, or state none (review measured none). Paste the list of release-blocking plans inheriting `low`/`medium` WITH their id6s, and state how many are `low`; review measured 17, all `medium`, zero `low`. Confirm no source backlog item was modified (`git status --porcelain -- .aw/records/backlog` empty).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste OQ-02's recorded answer FIRST and state which option it selected, since it decides whether the 5 `approved` plans are written at all. Then paste, for the FIRST plan, the `--dry-run` output showing exactly ONE plan named and `unchanged`, followed by the real invocation and its `git diff` showing only the two fields plus one history line changed and `- Status:` unchanged. Paste the history line itself and confirm it carries the supplied `--message` text rather than `status set to approved`. Then paste a spot check of three more plans' metadata blocks. Confirm every invocation used an id6 (paste the loop or the command list), that `--no-commit` was passed, and that no hand-edit was used.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff --stat` over this item's commits, and a grep proving no plan's `Status`/`Readiness`/`Set`/`Order`/`Id` line changed. Paste `git status --porcelain -- .aw/records/plans/executed .aw/records/plans/superseded .aw/records/plans/not-executed` showing it EMPTY, which is the proof no setid mis-selection reverted a terminal plan; a non-empty result here is a FAILED validation regardless of everything else. Paste `aw check plans` with its error count and per-rule breakdown COMPARED to the baseline captured before the first edit, naming any new rule id; review's baseline is `errors 140` (124 `check.scope-drift`, 15 `check.lifecycle-transition-invalid`, 1 `check.review-decision-unescalated`). Do NOT claim it clean and do NOT reduce the count by editing another party's plan. Paste `git diff --cached --name-only` from before the final commit proving only this item's files were staged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `FORCE_COLOR=1 aw att --type plan` showing a populated Priority column, and `aw att --type plan --format json` with the count of plan items whose `priority` is non-null, captured BEFORE the first edit and AFTER the last, with the delta stated and matched against the number of plans written. Do NOT paste a piped `aw att --type plan` and call the missing column a failure; that surface has no Priority column by design.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the post-write count of pending plans still missing either field, and reconcile it against sibling 03's no-source population (review measured 28). If the residue exceeds that, state what was skipped rather than reporting success. Paste the list of every plan skipped with its reason (dangling reference, already carried both fields, or deferred pending OQ-02). Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline and compare failure SETS, not counts; review's reading at HEAD `fe57b1a4` was `5971 passed, 3 skipped, 2 xfailed in 59.68s`, reference only.
  - Observed evidence:
  - Result: pending

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
