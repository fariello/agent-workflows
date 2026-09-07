# IPD: Detect and surface orchestrator-only work that the runner would retire unverified

- Date: 2026-09-07
- Kind: orchestrator
- Concern: The runner retires an Order-0 orchestrator once every child is `executed`, deliberately omitting the pre-transition E/V checkpoint (`ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`) on the premise that the parent's items are "performed by NOBODY" (`ipd_lifecycle.py:1825`). When a parent carries work no child covers, that premise is false and the work is marked complete having never been performed OR verified. Measured 2026-09-07: 46 of 130 orchestrators carry checklist items. The premise was never enforced, never in the IPD spec, never in AGENTS.md, and unchecked anywhere.
- Scope: Three children: the SURFACING gap (01), the CACHE (02), the PROBE and its gate (03). IN: making a refusal reason and its remedy reach both `aw oc|agy run`'s summary and `aw runs`; a digest-keyed verdict cache; a bounded pre-run probe over queued orchestrators with an interactive prompt, a non-interactive failure, and an override. OUT: any `ipd_lint` rule (see the Rejected shapes below), any change to what the rollup transition itself does, and the retirement predicate (`77tr3o` owns it).
- Scope-Paths: none
- Item-Dependencies: none
- Status: to-review
- Set: orchprobe
- Order: 0
- Highest E allocated: 00
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: yeh7gc

## Workflow history
- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop a Set from being reported complete while work parked on its orchestrator was never performed or verified, and make every refusal this adds tell the reader WHAT to do about it. Detection is semantic, so it is an LLM probe rather than a pattern match; the probe is cached so an unmodified orchestrator is never re-probed.

## Detailed Implementation Checklist (TODO)

This orchestrator holds ORCHESTRATION ONLY, per the rule this Set exists to enforce. It declares no `E-*` items; each child carries its own work and its own validation. The child table is in the next section.

## Child IPDs, sequence, and dependencies

| Order | Id | Child plan | Depends on |
| --- | --- | --- | --- |
| 01 | r2i1b1 | Surface a per-item refusal reason and its remedy in the run summary and `aw runs` | none |
| 02 | 8tgg6g | Cache an orchestrator probe verdict against a content digest that ignores execution state | none |
| 03 | m7gvuz | Probe every queued orchestrator for uncovered work before the run starts in earnest | executed:r2i1b1, executed:8tgg6g |

Order 01 is first and independent because it is a DEFECT TODAY, with or without this Set: the summary's diagnostics block reports only a hardcoded allowlist of statuses, so any new refusal kind is invisible. Shipping the probe before the surfacing would produce a gate whose refusals nobody sees.

Order 02 is independent of 01 and could run in parallel; it is sequenced second only because 03 needs both.

## Completion criteria (the whole Set is done only when)

1. A run whose queue contains an orchestrator carrying work no child covers REFUSES (non-interactive) or PROMPTS (interactive) before spending an agent turn on that Set.
2. The refusal names the orchestrator, states that the uncovered work belongs in a child, and tells the reader to ADD A CHILD rather than delete the items.
3. That reason is visible in BOTH `aw oc|agy run`'s end-of-run summary and in `aw runs`, not only in stdout at the moment it happened.
4. Re-running against an UNMODIFIED orchestrator spends no probe tokens, and modifying the orchestrator's requirement text DOES re-probe.
5. Ticking a checkbox, filling evidence, or appending workflow history does NOT re-probe (the `xmqv5l` trap).
6. An override flag exists for a maintainer who accepts the risk deliberately, and using it is recorded.

## Cross-IPD validation

- CID-1: `ipd_lint.py` still contains ZERO occurrences of "orchestrator" after all three children, so `77tr3o` R-5's chosen shape is intact (`tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken` must pass unmodified).
- CID-2: the five live orchestrators carrying legitimate orchestration checklists are NOT flagged by the probe, and none of them was edited by this Set. A Set that "fixes" the problem by deleting orchestration checklists has failed.
- CID-3: both hosts share one definition of every symbol this Set adds, asserted by object identity rather than by grep (the anti-re-fork discipline from `2r306y`/`818uru`).
- CID-4: the full suite's failing NODE IDS are unchanged from the executing worktree's own baseline, except for tests this Set adds.

## Project conventions discovered (Step 0)

- The parent's checklist is LOAD-BEARING and must not be deleted. Most Sets are executed by a human telling an agent "execute `<setid>`" with no runner involved, and the parent's list of children is what makes that complete and ordered. So the rule is NOT "a parent has no checklist"; it is "a parent's checklist is its orchestration and nothing beyond it". A blunt no-items rule was built and REVERTED on 2026-09-07 for exactly this reason.
- Wording decides behavior. A gate that says "an orchestrator cannot have executions" invites the agent to DELETE the items, destroying the orchestration checklist. Every message this Set adds must name the destination: the work belongs in a child, so ADD A CHILD.
- There is a proven digest precedent, including the trap. `ipd_lifecycle.plan_content_digest` hashes whole bytes; `frozen_region_digest` exists BECAUSE that was wrong (backlog `xmqv5l`: a conforming executor must tick boxes, fill evidence, and append history, so a byte digest went stale on every correct execution). Child 02 must key on requirement text, not bytes.
- `aw ipd lint` must stay Kind-unaware. Spec `77tr3o` R-5 chose shape (b) and rejected the linter route; `tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken` asserts `ipd_lint.py` contains zero occurrences of "orchestrator".
- Suite bare (`python3 -m pytest`); prefer an isolated worktree; ~14 `test_run_viewer` failures are the known `agrlvw` live-repo fixture and are not caused by a change here.

## Findings

| Id | Severity | Location (HEAD 2026-09-07) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `render_stream.py:2124-2150` | The summary's diagnostics block keys on a hardcoded status allowlist (`dependency-blocked`, `failed-safely`, `integration-blocked`, `merge-conflict`, `interrupted`). A new refusal reason produces NO diagnostic line. | source read |
| F-2 | HIGH | `run_viewer.py:1497` | `aw runs`' `Issue` column is computed only from `missing_entirely`/`location_mismatch`/`status_mismatch`, all about a plan being in the wrong directory. A semantic refusal sets none, so the column reads `no`. | source read |
| F-3 | HIGH | both surfaces | Neither carries a REMEDY field. They report what happened, never what to do, so advice has nowhere to go. | source read |
| F-4 | HIGH | corpus | 46 of 130 orchestrators carry checklist items; on the five live ones the items split into legitimate orchestration ("Execute the six children in the Order below") and parent-only work ("Establish the CHARACTERIZATION BASELINE BEFORE any child runs"). Only the second is the hazard. | classified 2026-09-07 |
| F-5 | MED | `ipd_lifecycle.py:457,461` | The naive whole-file digest is a known dead end (`xmqv5l`), so the cache key must exclude execution state, checkbox marks, and history. | docstring records the measured failure |
| F-6 | MED | probe design | A false "no work here" verdict is worse than no probe, because it launders a bad state with apparent authority. The prompt must be biased toward suspicion. | design reasoning, to be validated in child 03 |

## Proposed changes (ordered, validatable)

1. `r2i1b1` makes refusals visible and actionable in both surfaces, fixing F-1/F-2/F-3 as standalone defects.
2. `8tgg6g` adds the digest-keyed verdict store, so 03 can be cheap without being stale.
3. `m7gvuz` adds the probe and its gate, consuming both.

## Deferred / out of scope (with reason)

- Any `ipd_lint` rule. REJECTED SHAPE, recorded so it is not retried: a syntactic rule cannot separate legitimate orchestration from parent-only work, and its false positives push an agent to DELETE the orchestration checklist, which is the lost-work failure this Set exists to prevent. It also collides with `77tr3o` R-5's chosen shape.
- Requiring a parent to POSITIVELY assert it holds no work. Considered and deferred by the maintainer 2026-09-07: it would need backfilling across every existing orchestrator, and an un-backfilled parent would be indistinguishable from an unsafe one, which is the same trade-off `77tr3o` OQ-2 already rejected.
- Changing the rollup transition or the retirement predicate: `77tr3o` owns both.
- Backfilling the 46 existing orchestrators: this Set makes the problem visible and refusable; triaging historical plans is separate work.

## Scope check

- Over-scope: none.
- Under-scope: the prose-work hole is only CLOSED for orchestrators in a run's queue. A Set executed by a bare agent with no runner never reaches the probe, and this Set does not claim otherwise.

## Required tests / validation

Each child carries its own. Set-level: after all three, a run over a Set whose orchestrator carries uncovered work must refuse (or prompt) BEFORE spending an agent turn, name the offending orchestrator, tell the reader to add a child, and have that reason visible in both the summary and `aw runs`.

## Spec / documentation sync

The AGENTS.md paragraph stating the corrected rule (parent keeps its orchestration checklist; parent-only work goes in a NEW child) is already generated from `engine.py`. A spec amendment for the probe gate belongs to child 03, which owns the behavior.

## Open questions

### OQ-01: Is a `CONTAINS EXECUTIONS` verdict cached, or only a pass?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: Child 02 decides and records. Caching a PASS is the money saver. Caching a FAIL is probably safe because a fix changes the requirement text and so self-invalidates the digest, but the executor must confirm that on the real digest function rather than assume it, since a pinned stale FAIL would block a corrected orchestrator.

## Validation and cross-check (verify before reporting the Set complete)

No `V-*` items: this orchestrator declares no `E-*` items, and the E/V bijection holds trivially. Each child carries its own validation, and the Set-level checks are CID-1 through CID-4 above.

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files a child changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: each child requires explicit human approval before execution. Do NOT hand-write a `Readiness:` field. This orchestrator is retired by the runner once all three children are `executed`; it carries no work of its own, which is the premise that makes that retirement honest.
