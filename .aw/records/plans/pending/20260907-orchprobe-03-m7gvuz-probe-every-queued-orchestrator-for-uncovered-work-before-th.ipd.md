# IPD: Probe every queued orchestrator for uncovered work before the run starts in earnest

- Date: 2026-09-07
- Kind: child
- Concern: The runner retires an orchestrator once every child is `executed`, omitting the pre-transition E/V checkpoint on the premise that its items are "performed by NOBODY" (`ipd_lifecycle.py:1825`, `ROLLUP_OMITTED_GATES`). When a parent carries work no child covers, that premise is false and the work is reported complete having never been performed OR verified. Nothing detects this. It cannot be a pattern match: the dangerous case is PROSE ("someone must migrate the database before the children run"), which matches no checklist syntax, so a syntactic rule catches only the tidy mistake and misses the harmful one. It is a semantic question, so it needs a model to answer it. A blunt syntactic rule was built and REVERTED 2026-09-07 for a second reason too: most orchestrator checklist items are legitimate orchestration, and a rule that flags them teaches agents to DELETE the checklist that makes non-runner execution complete.
- Scope: A bounded pre-run gate. IN: a short prompt per queued orchestrator returning ONE parsable line; consuming child 02's cache so an unmodified orchestrator is never re-probed; an interactive prompt when a TTY is present, a hard failure when not, and an override flag that is recorded when used; emitting child 01's refusal record so the reason and its remedy reach both surfaces. OUT: the retirement predicate and the rollup transition (`77tr3o` owns both); any `ipd_lint` rule (rejected; see Deferred); backfilling the 46 existing orchestrators.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/engine.py, tests/test_orchestrator_probe.py
- Item-Dependencies: executed:r2i1b1, executed:8tgg6g
- Status: to-review
- Set: orchprobe
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m7gvuz

## Workflow history
- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Before a run spends an agent turn, establish for every queued orchestrator whether it holds work no child covers, and refuse or prompt when it does, naming the constructive fix. Cheap by caching, honest by failing closed, and never so noisy that an operator learns to ignore it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the probe

- [ ] E-01 Write the prompt, and BIAS IT TOWARD SUSPICION. It must return exactly one line, either `ORCHESTRATOR: CONTAINS EXECUTIONS` or `ORCHESTRATOR: CONTAINS NO EXECUTIONS`, and nothing else. It must state that a checklist naming the children is EXPECTED and is not an execution, since that is the legitimate orchestration case and a prompt that misreads it would produce constant false alarms on the five live orchestrators. It must instruct that any doubt resolves to `CONTAINS EXECUTIONS`: a false alarm costs one prompt, while a false clear launders a bad state with apparent authority, which is worse than having no probe at all.
  - Depends on: none
  - Expected outcome: a prompt held as data (not inlined at a call site), with the two sentinel strings as named constants so the parser and the prompt cannot drift.
  - Execution state: pending

- [ ] E-02 Parse the reply STRICTLY and fail closed. Accept only the two exact sentinels; anything else (extra prose, a refusal, an empty reply, a truncated turn) is `unknown`, which blocks exactly as `CONTAINS EXECUTIONS` does. A permissive parser here would convert a confused model into a silent pass, which is the failure mode this whole child exists to prevent.
  - Depends on: E-01
  - Expected outcome: a tri-state result; pasted proof that a chatty or empty reply yields `unknown` and blocks.
  - Execution state: pending

- [ ] E-03 Probe only the orchestrators IN THIS RUN'S QUEUE, and consult child 02's cache first. `aw oc run all` could otherwise sweep the whole corpus; scope keeps the cost proportional to the run. A cache hit spends nothing; a miss or a digest change probes.
  - Depends on: E-02
  - Expected outcome: with 5 queued orchestrators all cached, ZERO model calls; after editing one orchestrator's E-item text, exactly ONE call.
  - Execution state: pending

### Task group 2: the gate and its voice

- [ ] E-04 Gate the run: PROMPT interactively when stdin is a TTY, FAIL when it is not, and provide an override flag for a maintainer who accepts the risk deliberately. Record the override in run state when used, so a later reader can tell an accepted risk from an unnoticed one. Site the gate BEFORE any agent turn or lane worktree is created, so a refusal costs nothing and leaves no partial state.
  - Depends on: E-03
  - Expected outcome: the three paths demonstrated; a refusal creates no run directory lease, no worktree, and no session.
  - Execution state: pending

- [ ] E-05 Emit child 01's refusal record with a REMEDY that names the constructive action: the uncovered work belongs in a child, so ADD A CHILD for it. Do NOT phrase it as "an orchestrator must not contain executions": `AGENTS.md` records that a prohibition-only message gets complied with by DELETION, and deleting these items destroys the orchestration checklist that makes non-runner execution complete. The remedy wording is the deliverable here, not a nicety.
  - Depends on: E-04
  - Expected outcome: the reason and remedy visible in both the end-of-run summary and `aw runs`, with the remedy naming child creation.
  - Execution state: pending

- [ ] E-06 Update the AGENTS.md managed block via `engine.py` (never by hand, it is generated) to state that this gate exists, what it checks, and what to do when it fires. Also amend the spec that governs the run gates so the behavior is a recorded requirement rather than undocumented code; declare that spec file in this plan's `Scope-Paths` so the amendment is announced by the pre-run spec-impact notice.
  - Depends on: E-05
  - Expected outcome: regenerated AGENTS.md, an amended spec, and a passing no-drift test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A prohibition-only message causes deletion. This is recorded in the AGENTS.md managed block and is the reason E-05 exists as its own item.
- The parent's checklist of children is LOAD-BEARING: most Sets are run by a human telling an agent "execute `<setid>`" with no runner at all, and that checklist is what makes execution ordered and complete. The probe must not flag it.
- `ipd_lint` must stay Kind-unaware: spec `77tr3o` R-5 chose the runner-side shape and rejected the linter route, and `tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken` asserts zero occurrences of "orchestrator" in `ipd_lint.py`.
- Both hosts must share one definition of anything added (`2r306y`/`818uru`), asserted by object identity, and `agy_runipd` must not gain another import from `oc_runipd` (backlog `cnwy8g`).

## Findings

| Id | Severity | Location (2026-09-07) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.py:1825`, `ROLLUP_OMITTED_GATES` | Retirement omits the E/V checkpoint on a premise nothing enforces. | source read |
| F-2 | HIGH | corpus | 46 of 130 orchestrators carry checklist items; on the five live ones the items split into legitimate orchestration and parent-only work, and only the latter is the hazard. | classified 2026-09-07 |
| F-3 | HIGH | design | The dangerous case is prose, which no pattern match sees. Hence a model, not a regex. | maintainer observation, agreed |
| F-4 | HIGH | design | A false clear is worse than no probe, so the prompt must bias toward suspicion and the parser must fail closed. | design reasoning; E-01/E-02 own it |
| F-5 | MED | `aw oc run all` | An unscoped probe could sweep the whole corpus; E-03 bounds it to the queue. | source read |

## Proposed changes (ordered, validatable)

1. E-01 and E-02 make the probe trustworthy (suspicious prompt, strict parser).
2. E-03 makes it cheap (queue-scoped, cache-first).
3. E-04 and E-05 make it act and speak correctly.
4. E-06 records the contract.

## Deferred / out of scope (with reason)

- Any `ipd_lint` rule. REJECTED and recorded so it is not retried: it cannot separate orchestration from parent-only work, its false positives push agents to delete the orchestration checklist, and it collides with `77tr3o` R-5.
- Requiring a parent to positively assert it holds no work: deferred by the maintainer 2026-09-07, because every existing orchestrator would need backfilling and an un-backfilled parent would be indistinguishable from an unsafe one, the same trade-off `77tr3o` OQ-2 rejected.
- Backfilling the 46 existing orchestrators, and changing the retirement predicate or rollup transition.
- Probing a Set executed by a bare agent with no runner: out of reach by construction, and stated in the orchestrator's Scope check rather than hidden.

## Scope check

- Over-scope: `engine.py` is in scope ONLY for the managed-block prose E-06 adds; do not touch the installer.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured there and pasted, comparing failing NODE IDS not totals. The model call must be stubbed in tests: a test that spends tokens is not a test. At least one end-to-end exercise over a fixture Set whose orchestrator carries prose-only work, because that is the case a syntactic rule cannot catch and the reason this child exists.

## Spec / documentation sync

E-06 amends the run-gate spec and regenerates the AGENTS.md managed block from `engine.py`. The amended spec file MUST appear in `Scope-Paths` so the pre-run spec-impact announcement names it.

## Open questions

### OQ-01: Which model answers the probe, and does it follow the run's profile?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: Resolve from the repository rather than by asking. `kgpptv` gives the verifier turn its own resolved profile and `f2mrsw` E-03 already resolves a per-profile `validate` tri-state, so the profile machinery exists; the executor should reuse it rather than hardcode a model, and record which profile the probe uses. A cheap model is defensible for a yes/no question, but the verdict is cached and trusted later, so the choice must be recorded with the verdict (child 02 E-03 stores the model for exactly this reason).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the prompt text, showing it names the two sentinels, states that a child checklist is expected and is not an execution, and instructs that doubt resolves to CONTAINS EXECUTIONS. Paste the sentinel constants proving prompt and parser share them.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste parser results for the two exact sentinels, plus a chatty reply, an empty reply, a truncated reply, and a reply with both sentinels: the last four must all yield `unknown` and BLOCK. Include a mutation check: loosen the parser, show a test fails, revert.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a run with all queued orchestrators cached showing ZERO model calls (a stub call counter is acceptable evidence), then edit one orchestrator's E-item text and paste the same run showing exactly ONE call.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste all three paths (interactive prompt, non-interactive failure, override accepted-and-recorded), plus proof a refusal left NO run directory, worktree, or session behind.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the summary block and the `aw runs` output for a refused run, showing the reason AND a remedy that says to add a child. Assert the message does NOT read as a bare prohibition.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the regenerated AGENTS.md passage, the spec diff, a passing no-drift test, and the pre-run spec-impact announcement naming the amended spec file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved m7gvuz --by-human --message ...`) before execution, and its `Item-Dependencies` refuse dispatch until both `r2i1b1` and `8tgg6g` are executed. Do NOT hand-write a `Readiness:` field. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
