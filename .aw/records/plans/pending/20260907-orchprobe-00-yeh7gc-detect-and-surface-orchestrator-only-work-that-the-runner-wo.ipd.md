# IPD: Detect and surface orchestrator-only work that the runner would retire unverified

- Date: 2026-09-07
- Kind: orchestrator
- Concern: The runner retires an Order-0 orchestrator once every child is `executed`, deliberately omitting the pre-transition E/V checkpoint (`ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`) on the premise that the parent's items are "performed by NOBODY" (`ipd_lifecycle.py:1825`). When a parent carries work no child covers, that premise is false and the work is marked complete having never been performed OR verified. THE SCALE, RE-MEASURED AT REVIEW (2026-09-07, HEAD `b8acf979`) BECAUSE THE ORIGINAL FIGURE UNDERSTATED IT BY 3x: 46 of the 47 plans carrying `- Kind: orchestrator` carry checklist items, i.e. 98 percent, not the 35 percent that "46 of 130" suggests. The 130 denominator is the filename-`-00-` population, 84 of which are pre-`Kind` legacy plans carrying ZERO E-items, so they dilute a ratio they are not members of. This matters to sizing in one direction only: the probe will run against essentially every orchestrator it meets, so its FALSE-POSITIVE rate, not its coverage, is the dominant cost. The premise was never enforced, never in the IPD spec, never in AGENTS.md, and unchecked anywhere. Durable-fix ticket: backlog `5ev6lh` (`open`), which named this Set's shape as its options (c) and (d).
- Scope: Three children: the SURFACING gap (01), the CACHE (02), the PROBE and its gate (03). IN: making a refusal reason and its remedy reach both `aw oc|agy run`'s summary and `aw runs`; a digest-keyed verdict cache; a bounded pre-run probe over queued orchestrators with an interactive prompt, a non-interactive failure, and an override. OUT: any `ipd_lint` rule (see the Rejected shapes below), any change to what the rollup transition itself does, and the retirement predicate (`77tr3o` owns it).
- Scope-Paths: none
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: orchprobe
- Order: 0
- Highest E allocated: 01
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: yeh7gc
- From-Backlog: 5ev6lh

## Workflow history
- 2026-09-07 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; PR-001..PR-010, nine FIXED and one OPEN. TWO BLOCKERS, both internal contradictions measured against the code rather than reasoned about. FIRST, criterion 3 (the refusal must be durable in the summary AND `aw runs`) was UNSATISFIABLE beside child 03's E-04 siting (refuse before the run directory exists): `initialize_run` raises at `oc_runipd.py:2791`/`:2871` BEFORE `run_dir.mkdir` at `:2880`, so today's pre-queue gates (draft admission, mixed-type) leave nothing whatever for `aw runs` to read, and a probe sited there would too. Resolved in favor of DURABILITY (D-1) on the plan's own recorded intent, and bound on the children by a new criterion 3 and CID-5. SECOND, CID-2 pinned the probe to a FALSE NEGATIVE: it required that none of the five live orchestrators be flagged, while the plan's own F-4 said their items split into orchestration AND parent-only work. Measured per item: FOUR of the five (`5e4sb6` E-01/E-02, `h0zljh` E-02/E-03, `rh5tt6` E-02, `3m0urk` E-02) carry real parent-only work and MUST be flagged; only `cczotj` is orchestration-only, and only because a maintainer ruling already moved its work into child `3v7wo6`. CID-2 is now per-ITEM with that classification as its fixture. THE OPEN ONE IS OQ-02 (`Blocking: yes`, PR-005) and it is a maintainer decision: those four orchestrators are `Status: approved` and runnable TODAY, so this Set's first live act is to refuse or prompt on four approved Sets, whose documented remedy is authoring four new children. ALSO FIXED: this orchestrator carried NO checklist of its children at all, violating the AGENTS.md rule it exists to enforce and misstating that rule as "no E-items" (PR-003, now E-01/V-01); the baseline convention was stale and FALSE at HEAD (`test_run_viewer` is 46 passed / 0 failed, not "~14 known failures", and the one real failure is in `test_orchestrator_retirement.py`, the module CID-1 depends on) (PR-004); the 46-of-130 denominator (PR-006); the missing `- From-Backlog: 5ev6lh` (PR-007); CID-3's absolute object-identity rule, which `DEPENDENCY_BLOCK_RECOVERY_HINT` already refutes by design (PR-008); an OQ owned by an "executor" an orchestrator does not have (PR-009); and a spec-sync section naming no spec (PR-010).

- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop a Set from being reported complete while work parked on its orchestrator was never performed or verified, and make every refusal this adds tell the reader WHAT to do about it. Detection is semantic, so it is an LLM probe rather than a pattern match; the probe is cached so an unmodified orchestrator is never re-probed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

THIS PARENT CARRIES ORCHESTRATION AND NOTHING BEYOND IT, which is NOT the same as carrying no items, and the difference is the rule this Set exists to enforce. `AGENTS.md` states that an Order-0 orchestrator SHOULD carry a checklist of its children, because most Sets are executed by a human telling an agent "execute `<setid>`" with no runner involved, and that checklist is what makes such an execution ordered and complete; deleting it causes exactly the lost work the rule protects against. An earlier revision of this plan declared no `E-*` items at all and described that as compliance. It was not: it was the destructive reading of the rule, applied to the plan whose job is to prevent that reading. E-01 below is orchestration (the runner performs the sequencing itself, which is precisely why the rollup may skip its checkpoint honestly). What must NOT appear here is work no child covers: a deliverable, a baseline established before any child runs, or a records reconciliation afterwards. If such a step is needed, ADD A CHILD.

### Task group 1: sequence the Set

- [ ] E-01 SEQUENCE THE THREE CHILDREN IN ORDER, confirming each is `executed` on disk before dispatching the next, and STOP on the first that does not reach `executed`. The order is fixed by consumption, not preference: 01 (`r2i1b1`) the surfacing, then 02 (`8tgg6g`) the cache, then 03 (`m7gvuz`) the probe, which consumes both. Order 02 may run before or beside 01; only 03 requires both. DO NOT PERFORM ANY CHILD'S WORK FROM HERE: if a child appears to need a change this parent could make, the child table is wrong, so fix the child.
  - Depends on: none
  - Expected outcome: all three children are `executed` on disk in an order that puts `m7gvuz` last, with none skipped and no child's work performed by this parent.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

All three children are AUTHORED and `aw ipd lint` conforming. There are NO placeholder rows: an orchestrator whose table declares a row resolving to no plan refuses retirement (`unauthored-child-rows`).

| Order | Id | Child plan | Depends on |
| --- | --- | --- | --- |
| 01 | r2i1b1 | Surface a per-item refusal reason and its remedy in the run summary and `aw runs` | none |
| 02 | 8tgg6g | Cache an orchestrator probe verdict against a content digest that ignores execution state | none |
| 03 | m7gvuz | Probe every queued orchestrator for uncovered work before the run starts in earnest | executed:r2i1b1, executed:8tgg6g |

Order 01 is first and independent because it is a DEFECT TODAY, with or without this Set: the summary's diagnostics block reports only a hardcoded allowlist of statuses, so any new refusal kind is invisible. Shipping the probe before the surfacing would produce a gate whose refusals nobody sees.

Order 02 is independent of 01 and could run in parallel; it is sequenced second only because 03 needs both.

THE 01-BEFORE-03 RATIONALE PRESUMES A DURABLE REFUSAL, so it is only sound under criterion 3 below. Child 01's surfacing reads run state; a refusal recorded nowhere is invisible to it no matter what order the children land in. See F-7.

## Completion criteria (the whole Set is done only when)

1. A run whose queue contains an orchestrator carrying work no child covers REFUSES (non-interactive) or PROMPTS (interactive) before spending an agent turn, creating a lane worktree, or opening a session for that Set.
2. The refusal names the orchestrator, states that the uncovered work belongs in a child, and tells the reader to ADD A CHILD rather than delete the items.
3. That reason is DURABLE: it is visible in BOTH `aw oc|agy run`'s end-of-run summary and in `aw runs`, not only in stdout at the moment it happened. This CONSTRAINS WHERE THE GATE MAY BE SITED and is not merely a rendering requirement. Today's pre-queue gates refuse BEFORE the run directory exists (`oc_runipd.initialize_run` raises at `:2791` and `:2871`, while `run_dir.mkdir` is at `:2880`), so their refusals are stdout-only and `aw runs` has nothing to read. The probe must therefore refuse at a point where a durable record EXISTS, recording the refusal against the item exactly as the draft-admission and mixed-type verdicts are recorded into state (`oc_runipd.py:3054-3075`). Criterion 1 still holds: no agent turn, no worktree and no session, which is what "costs nothing" has to mean here. Resolved decision D-1 of this review; child 03's E-04 as currently written says the opposite ("a refusal creates no run directory") and must be corrected at its own review.
4. Re-running against an UNMODIFIED orchestrator spends no probe tokens, and modifying the orchestrator's requirement text DOES re-probe.
5. Ticking a checkbox, filling evidence, or appending workflow history does NOT re-probe (the `xmqv5l` trap).
6. An override flag exists for a maintainer who accepts the risk deliberately, and using it is recorded.
7. The probe's verdict is correct PER ITEM, not per plan, demonstrated against the measured live corpus in CID-2. A probe that clears an orchestrator because most of its items are orchestration has failed, and so has one that flags an orchestration item.

## Cross-IPD validation

- CID-1: `ipd_lint.py` still contains ZERO occurrences of "orchestrator" after all three children, so `77tr3o` R-5's chosen shape is intact (`tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken` must pass unmodified).
- CID-2: THE PROBE IS CORRECT PER ITEM AGAINST THE MEASURED LIVE CORPUS, and this fixture replaces an earlier CID-2 that would have pinned the probe to a false negative. Classified 2026-09-07 at HEAD `b8acf979` over the five pending `Kind: orchestrator` plans carrying items. MUST BE FLAGGED (parent-only work no child covers): `5e4sb6` E-01 (produce the inventory research artifact, a deliverable) and E-02 (establish the characterization baseline BEFORE any child runs, which writes tests); `h0zljh` E-02 (run the whole-Set spec verification and write a walkthrough record) and E-03 (reconcile the records the Set closes, setting a backlog item `done`); `rh5tt6` E-02 (run the repo-wide suite and leak sanitization); `3m0urk` E-02 (perform the final CID-1..CID-8 cross-IPD audit). MUST NOT BE FLAGGED (orchestration): `3m0urk` E-01, `h0zljh` E-01, `rh5tt6` E-01, `cczotj` E-01 and E-02, and this plan's own E-01. Note `cczotj` is the ONLY orchestration-only member, and only because a maintainer ruling on its OQ-04 already moved its verification into child `3v7wo6`, which is the very remedy this Set's refusal must recommend. NO orchestrator may be EDITED by this Set to make the fixture pass: a Set that "fixes" the problem by deleting orchestration checklists has failed.
- CID-3: both hosts share one definition of every symbol this Set adds, asserted by object identity rather than by grep (the anti-re-fork discipline from `2r306y`/`818uru`). ONE CARVE-OUT, measured rather than assumed: HOST-PARAMETERIZED TEXT is legitimately not one object. `DEPENDENCY_BLOCK_RECOVERY_HINT` is defined separately in each runner (`oc_runipd.py:345`, `agy_runipd.py:399`) and the two strings differ by design, because each names its own host's recovery command; a probe REMEDY naming a `resume` invocation is the same shape. So the rule is that the FUNCTION composing a message is one shared object taking the host as an argument; it is NOT that every resulting string is identical. A child that satisfies CID-3 by emitting one remedy naming the wrong host has failed it.
- CID-4: the full suite's failing NODE IDS are unchanged from the executing worktree's own baseline, except for tests this Set adds. Measure the baseline in the executing worktree; do NOT trust the numbers in this plan, which were true only at review time.
- CID-5: THE REFUSAL SURVIVES THE REFUSAL. Paste `aw runs` output for a run that the probe refused, read AFTER the process exited, showing the reason and the remedy. This is the check that criterion 3 was honored rather than asserted; a refusal that exists only in the terminal scrollback fails it even if the wording is perfect.
- CID-6: the spec amendment child 03 owes is DECLARED where the runner can announce it. Child 03's `Scope-Paths` must list the `.spec.md` file it amends; as authored it lists none while its own E-06 and spec-sync section require the declaration. Paste the pre-run spec-impact announcement naming the file.

## Project conventions discovered (Step 0)

- The parent's checklist is LOAD-BEARING and must not be deleted. Most Sets are executed by a human telling an agent "execute `<setid>`" with no runner involved, and the parent's list of children is what makes that complete and ordered. So the rule is NOT "a parent has no checklist"; it is "a parent's checklist is its orchestration and nothing beyond it". A blunt no-items rule was built and REVERTED on 2026-09-07 for exactly this reason.
- Wording decides behavior. A gate that says "an orchestrator cannot have executions" invites the agent to DELETE the items, destroying the orchestration checklist. Every message this Set adds must name the destination: the work belongs in a child, so ADD A CHILD.
- There is a proven digest precedent, including the trap. `ipd_lifecycle.plan_content_digest` hashes whole bytes; `frozen_region_digest` exists BECAUSE that was wrong (backlog `xmqv5l`: a conforming executor must tick boxes, fill evidence, and append history, so a byte digest went stale on every correct execution). Child 02 must key on requirement text, not bytes.
- `aw ipd lint` must stay Kind-unaware. Spec `77tr3o` R-5 chose shape (b) and rejected the linter route; `tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken` asserts `ipd_lint.py` contains zero occurrences of "orchestrator".
- THE SUITE BASELINE, RE-MEASURED AT REVIEW BECAUSE THE PREVIOUS NOTE WAS STALE AND WOULD HAVE MISLED THE EXECUTOR IN BOTH DIRECTIONS. Measured bare (`python3 -m pytest`) at HEAD `b8acf979`: `1 failed, 5632 passed, 3 skipped, 2 xfailed`. `tests/test_run_viewer.py` is `46 passed` on its own, so the previous claim of "~14 known `test_run_viewer` failures from the `agrlvw` live-repo fixture" is FALSE at this HEAD; an executor trusting it would have dismissed real failures as known. The ONE failure is `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`, which asserts `{"kgpptv": "reviewed"}` while `kgpptv` now reads `- Status: approved`: a test coupled to this live repository's mutable plan statuses, not a defect this Set introduces. It sits in the SAME module CID-1 depends on, so do not read a red `test_orchestrator_retirement.py` as evidence about `TheRejectedShapeWasNotTaken`, which passes. Re-measure in the executing worktree and compare failing NODE IDS, never totals.
- Suite bare (`python3 -m pytest`); prefer an isolated worktree.

## Findings

| Id | Severity | Location (HEAD 2026-09-07) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `render_stream.py:2124-2150` | The summary's diagnostics block keys on a hardcoded status allowlist (`dependency-blocked`, `failed-safely`, `integration-blocked`, `merge-conflict`, `interrupted`). A new refusal reason produces NO diagnostic line. | source read; the block sits inside `render_run_summary_table` (`:1628-2152`) |
| F-2 | HIGH | `run_viewer.py:1497` | `aw runs`' `Issue` column is computed only from `missing_entirely`/`location_mismatch`/`status_mismatch`, all about a plan being in the wrong directory. A semantic refusal sets none, so the column reads `no`. | source read |
| F-3 | HIGH | both surfaces | Neither carries a REMEDY field. They report what happened, never what to do, so advice has nowhere to go. | source read |
| F-4 | HIGH | corpus | 46 of the 47 plans carrying `- Kind: orchestrator` carry checklist items (98 percent). The "46 of 130" framing is a diluted ratio: the 130 is the filename-`-00-` population and 84 of those are pre-`Kind` legacy plans with ZERO E-items. On the five LIVE ones the items split into legitimate orchestration and parent-only work, and only the second is the hazard; the per-item split is enumerated in CID-2. | classified 2026-09-07 at HEAD `b8acf979`; counted by parsing `- Kind:` and `- [ ] E-` across `.aw/records/plans/**` |
| F-5 | MED | `ipd_lifecycle.py:457,461` | The naive whole-file digest is a known dead end (`xmqv5l`), so the cache key must exclude execution state, checkbox marks, and history. | docstring records the measured failure |
| F-6 | MED | probe design | A false "no work here" verdict is worse than no probe, because it launders a bad state with apparent authority. The prompt must be biased toward suspicion. | design reasoning, to be validated in child 03 |
| F-7 | BLOCKER | `oc_runipd.py:2791`, `:2871`, `:2880`, `:3054-3075` | DURABILITY CONSTRAINS SITING, and the two were in contradiction. `initialize_run` raises for the draft-admission and mixed-type gates BEFORE `run_dir.mkdir`, so a pre-queue refusal leaves NOTHING for `aw runs` or the end-of-run summary to read; the durable verdict records those gates do keep are written after the directory exists. So criterion 3 (durable in both surfaces) and child 03's E-04 (`a refusal creates no run directory`) could not both hold, and the 01-before-03 sequencing rationale silently assumed the first. Resolved as D-1 toward durability, on this plan's own recorded intent ("not only in stdout at the moment it happened"). | source read; the two gates' raise sites and the mkdir line compared directly |
| F-8 | HIGH | `.aw/records/plans/pending/` | THE FIRST LIVE EFFECT OF THIS SET IS TO BLOCK FOUR APPROVED SETS. `5e4sb6`, `h0zljh`, `rh5tt6` and `3m0urk` all carry `- Status: approved` and all carry parent-only work per CID-2, so the day child 03 lands, each refuses or prompts on every run that queues it, and the documented remedy is authoring four new children. The plan deferred "backlogfilling the 46" but never stated this bounded, immediate, four-item blast radius. | `- Status:` read from each of the five pending orchestrators; per-item classification in CID-2 |
| F-9 | MED | `oc_runipd.py:345`, `agy_runipd.py:399` | An absolute one-shared-object rule is refuted in this exact area: `DEPENDENCY_BLOCK_RECOVERY_HINT` is deliberately per-host, differing only in the recovery command it names, and a probe remedy is that same shape. CID-3 needed the carve-out or it would have forced a remedy naming the wrong host. | identity check: the two constants compare unequal and are not the same object |
| F-10 | HIGH | suite baseline | The plan's baseline convention was stale and would mislead in both directions: `test_run_viewer` is 46 passed / 0 failed (not ~14 known failures), and the one real failure is a live-repo status coupling in `test_orchestrator_retirement.py`, the module CID-1 reads. | `python3 -m pytest` bare at HEAD `b8acf979`: `1 failed, 5632 passed, 3 skipped, 2 xfailed`; `python3 -m pytest tests/test_run_viewer.py`: `46 passed` |

## Proposed changes (ordered, validatable)

1. `r2i1b1` makes refusals visible and actionable in both surfaces, fixing F-1/F-2/F-3 as standalone defects.
2. `8tgg6g` adds the digest-keyed verdict store, so 03 can be cheap without being stale.
3. `m7gvuz` adds the probe and its gate, consuming both, sited per criterion 3 so its refusals are durable.

## Deferred / out of scope (with reason)

- Any `ipd_lint` rule. REJECTED SHAPE, recorded so it is not retried: a syntactic rule cannot separate legitimate orchestration from parent-only work, and its false positives push an agent to DELETE the orchestration checklist, which is the lost-work failure this Set exists to prevent. It also collides with `77tr3o` R-5's chosen shape.
- Requiring a parent to POSITIVELY assert it holds no work. Considered and deferred by the maintainer 2026-09-07: it would need backfilling across every existing orchestrator, and an un-backfilled parent would be indistinguishable from an unsafe one, which is the same trade-off `77tr3o` OQ-2 already rejected.
- Changing the rollup transition or the retirement predicate: `77tr3o` owns both.
- Backfilling the 46 existing orchestrators: this Set makes the problem visible and refusable; triaging historical plans is separate work. NOT DEFERRED, and distinguished deliberately from that backfill: the FOUR approved orchestrators of F-8 are the live blast radius, and what to do about them is OQ-02.
- Correcting the "46 of 130" figure in the generated `AGENTS.md` managed block (`engine.py:1349`). This plan declares `Scope-Paths: none` and must not edit it. Child 03's E-06 already edits that block via `engine.py`, so the corrected denominator (46 of 47 `Kind: orchestrator` plans; the other 84 are pre-`Kind` legacy `-00-` files with no E-items) belongs in that edit rather than in a separate change.

## Scope check

- Over-scope: none.
- Under-scope: the prose-work hole is only CLOSED for orchestrators in a run's queue. A Set executed by a bare agent with no runner never reaches the probe, and this Set does not claim otherwise. Also under-scope by decision rather than oversight: authoring the children that would clear the four approved orchestrators of F-8. This Set makes them refusable; clearing them is the work OQ-02 asks the maintainer to schedule.

## Required tests / validation

Each child carries its own. Set-level: after all three, a run over a Set whose orchestrator carries uncovered work must refuse (or prompt) BEFORE spending an agent turn, name the offending orchestrator, tell the reader to add a child, and have that reason readable in both the summary and `aw runs` AFTER the process exits (CID-5). Baselines are measured in the executing worktree, comparing failing node ids, never the totals recorded in this plan.

## Spec / documentation sync

The AGENTS.md paragraph stating the corrected rule (parent keeps its orchestration checklist; parent-only work goes in a NEW child) is already generated from `engine.py`.

THE SPEC AMENDMENT IS OWED AND ITS TARGET IS NAMED HERE, because "amend the spec that governs the run gates" is not a resolvable instruction. The controlling spec is `77tr3o` (`- Status: approved`, runner orchestrator retirement), whose R-5 resolution CREATED the omission this Set compensates for: a compensating control that is not recorded in the spec that authorized the omission leaves the spec still asserting an unguarded premise. If the gate is additionally specified as a run gate, `25kzda` Section 2.5/2.5a is where the sibling admission gates live and is the second candidate. Child 03 owns the amendment and must list the chosen file in its own `Scope-Paths` so the pre-run spec-impact announcement names it; CID-6 checks that it did. Backlog `5ev6lh` is the ticket this Set graduates from and should move to `graduated` when the Set is approved, not to `done`, since the code will not yet be written.

## Open questions

### OQ-01: Is a `CONTAINS EXECUTIONS` verdict cached, or only a pass?

- Blocking: no
- Status: resolved
- Owner: child 02 (`8tgg6g`) executor
- Resolution or deferral rationale: RESOLVED HERE AS A DUPLICATE, not as a design answer. The question is child 02's, is recorded verbatim as its own OQ-01, and is decided by its E-04 from the real digest function. Keeping a second copy on a plan that no agent executes means one copy goes stale and neither owner is accountable, which is the same class of defect as parking work on a parent. Read the live version in `8tgg6g`; the substance (caching a pass is the money saver; caching a fail is probably safe because a genuine fix edits the E-item text and self-invalidates the digest, but must be CONFIRMED on the implemented digest rather than assumed) is unchanged.

### OQ-02: What happens to the four APPROVED orchestrators this gate will immediately block?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-005
- Resolution or deferral rationale: NOT RESOLVABLE FROM THE REPOSITORY, and it is a scope/priority call rather than a technical one. Measured: `5e4sb6`, `h0zljh`, `rh5tt6` and `3m0urk` are `Status: approved` in `pending/` and each carries parent-only work per CID-2, so once child 03 lands, every run that queues one of them refuses (unattended) or prompts (interactive), and the remedy the message must recommend is authoring a new child for each. THREE COSTED OPTIONS. (a) SHIP AND ABSORB: land the gate, let the four prompt, and clear them as they come up. Cheapest now; the cost is that four approved Sets become un-runnable unattended until authored, and an operator who meets the prompt four times learns to reach for the override, which is how a gate stops working. (b) CLEAR FIRST: author the missing children for the four before child 03 lands. Highest up-front cost (four child plans, each needing its own review and approval) and it makes this Set's own delivery depend on unrelated Sets, but the gate then arrives on a clean corpus and its first firing is a real defect rather than known debt. (c) SHIP GATED BY AN ALLOWLIST: land the gate with the four recorded as known-and-accepted so they do not prompt, and clear them on their own schedule. Keeps the gate credible on new work; the risk is that an allowlist is a place for entries to go and never leave, so it needs an expiry or a check that it is shrinking. Recommendation: (c) with a stated expiry, falling back to (a) if an allowlist is judged not worth its mechanism. A human decides; do NOT execute child 03 while this is open.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste each child's `- Status:` line read from its file, showing all three `executed`, and paste `git log --oneline` over the plans tree showing the order in which they reached `executed` with `m7gvuz` LAST. Confirm from `git diff --stat` over this parent's own commits that it touched no file under `agent_workflows/`, which is the check that this parent performed no child's work.
    THE SET-LEVEL BEHAVIOR IS NOT VALIDATED HERE. CID-1 through CID-6 own it, and CID-5 in particular must be discharged with output read AFTER the refused run exited. Re-asserting from this parent that the gate works, without a child having recorded the evidence, is a FAILED validation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION IS BLOCKED ON OQ-02, and human approval alone does not clear it. OQ-02 is `Blocking: yes`, so the pre-execution checkpoint refuses while it is open; that is deliberate, because the question is what to do about four approved Sets this gate will immediately block, and only the maintainer can answer it.

Execution contract: commit ONLY the files a child changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: each child requires explicit human approval before execution. Do NOT hand-write a `Readiness:` field. This orchestrator is retired by the runner once all three children are `executed`. That retirement is honest because its ONLY item, E-01, is orchestration the runner performs itself by enforcing the order; it is NOT honest merely because the parent is short. If a later revision adds a step here that no child covers, the rollup will discharge it unperformed and unverified, which is the exact defect this Set exists to detect: add a child instead.
