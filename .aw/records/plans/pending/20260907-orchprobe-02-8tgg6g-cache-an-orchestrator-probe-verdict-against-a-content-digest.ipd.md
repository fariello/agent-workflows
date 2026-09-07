# IPD: Cache an orchestrator probe verdict against a content digest that ignores execution state

- Date: 2026-09-07
- Kind: child
- Concern: Child 03 asks a model whether an orchestrator carries work no child covers. That answer costs tokens and time, and re-asking it about an UNMODIFIED orchestrator buys nothing. So the verdict needs a cache keyed on content. The naive key is a whole-file hash, and this repository has already MEASURED that as a dead end: `ipd_lifecycle.plan_content_digest` (`:457`) hashes exact bytes, and `frozen_region_digest` (`:461`) exists precisely because that made a begin receipt "go stale on every CORRECT execution" (backlog `xmqv5l`) - a conforming executor MUST tick checkboxes, fill `Observed evidence`, and append `## Workflow history`, so the byte digest changed while the reviewed contract had not. A byte-keyed probe cache would repeat that error and re-spend on every tick.
- Scope: The verdict store and its key. IN: a digest over ONLY what the probe's answer depends on (the orchestrator's E-item action text plus its child table), excluding execution state, checkbox marks, workflow history, and prose sections; a per-repo verdict store recording digest, verdict, timestamp, and the model that answered; read/write helpers with a fail-closed miss. OUT: the probe itself and its prompt (child 03), the refusal surfacing (child 01), and any change to `plan_content_digest` or `frozen_region_digest`, which other gates depend on.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_probe_cache.py
- Item-Dependencies: none
- Status: to-review
- Set: orchprobe
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 8tgg6g

## Workflow history
- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the probe cheap to keep on: an orchestrator whose meaningful content has not changed is never re-probed, while any change to what the probe reasons about does re-probe. A cache MISS must never be mistaken for a pass.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: a key that ignores what does not matter

- [ ] E-01 Build the cache key: a stable digest over the orchestrator's E-item ACTION TEXT and its `## Child IPDs` table, and nothing else. Reuse the existing extraction rather than re-parsing: `ipd_lint.parse` already separates a leaf's action text (`Leaf.text`) from its sub-fields (`Leaf.fields`) and its checkbox (`Leaf.checked`), which is the structural reason `frozen_region_digest` can exclude mutable state cleanly. Serialize deterministically (`sort_keys=True`) so the digest is stable across runs and dict ordering.
  - Depends on: none
  - Expected outcome: a digest function whose value is unchanged by ticking a box, filling evidence, or appending history, and changed by editing an E-item's action text or the child table.
  - Execution state: pending

- [ ] E-02 Prove the `xmqv5l` trap is avoided, as a first-class deliverable rather than a side effect. Take a real orchestrator, apply each mutation a conforming executor makes (tick a checkbox, fill an `Observed evidence`, append a history line, edit a prose section), and assert the digest is IDENTICAL after each. Then edit an E-item action and assert it CHANGES. This is the item that decides whether the cache is worth having.
  - Depends on: E-01
  - Expected outcome: pasted before/after digests for four no-op mutations and one real one.
  - Execution state: pending

- [ ] E-03 Add the verdict store: per-repo, holding the digest, the verdict, when it was recorded, and WHICH MODEL answered. Site it with the other runtime state (`.aw/state/runtime/`, alongside the finalize journal and locks) so it inherits the existing gitignored, box-local treatment rather than inventing a second convention. Record the model because a verdict is only as good as its author, and a future reader must be able to distrust an old one.
  - Depends on: E-01
  - Expected outcome: write-then-read round-trips; the store is gitignored; a corrupt or unreadable entry is treated as absent rather than raising.
  - Execution state: pending

- [ ] E-04 Make a MISS fail closed, and decide the FAIL-caching question OQ-01 records. A missing entry means "not probed", which child 03 must treat as blocking, never as a pass: the whole point is that silence stops meaning safe. Then determine from the real digest function whether a `CONTAINS EXECUTIONS` verdict can be safely cached (a genuine fix edits the E-item text and so self-invalidates) and record the finding either way rather than assuming it.
  - Depends on: E-01, E-03
  - Expected outcome: an explicit tri-state (`pass` / `fail` / `unknown`), with `unknown` returned for a miss, and a recorded decision on caching failures with its evidence.
  - Execution state: pending

- [ ] E-05 Confirm both hosts share every symbol added, by OBJECT IDENTITY not grep (`2r306y`/`818uru`). Do not add another name to the ~46 `agy_runipd` already imports from `oc_runipd` (backlog `cnwy8g`).
  - Depends on: E-01, E-03, E-04
  - Expected outcome: pasted proof each new symbol is one shared object defined in `runner_shared`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `frozen_region_digest`'s docstring is the design brief for this child. It documents both the failure (a byte digest punishes correct execution) and the fix (hash the reviewed contract, not the file), and it names exactly which fields are mutable state. Read it before writing E-01.
- Runtime state belongs under `.aw/state/runtime/`; `.aw/.gitignore` already keeps that tree out of git, so a verdict store there is box-local by construction with no new ignore rule.
- Do NOT modify `plan_content_digest` or `frozen_region_digest`. The begin receipt gate depends on them, and changing either would alter an unrelated safety check.

## Findings

| Id | Severity | Location (2026-09-07) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.py:461` | The whole-file digest was measured to fail for this exact reason (`xmqv5l`); a byte-keyed cache would re-spend on every checkbox tick. | docstring records the measured failure |
| F-2 | MED | `ipd_lint.py:149` | `Leaf` already separates action text from sub-fields and checkbox state, so excluding mutable state is structural, not a fragile text rule. | source read |
| F-3 | MED | `.aw/.gitignore` | The runtime tree is already gitignored, so the store needs no new ignore entry. | file read |

## Proposed changes (ordered, validatable)

1. E-01 builds the key; E-02 proves it ignores the right things.
2. E-03 adds the store; E-04 makes a miss fail closed and settles fail-caching.
3. E-05 proves one shared definition.

## Deferred / out of scope (with reason)

- The probe and its prompt: child 03 owns them, including the suspicion bias.
- Committing verdicts to git: deliberately not done. A verdict is an LLM output; keeping it box-local matches the receipt precedent and avoids a stale answer travelling to another machine. Cost accepted: a fresh clone re-probes once.
- Any change to the two existing digest functions.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured there and pasted, comparing failing NODE IDS not totals.

## Spec / documentation sync

N/A: an internal cache with no user-facing contract. Child 03 owns the spec sync for the gate.

## Open questions

### OQ-01: Is a `CONTAINS EXECUTIONS` (fail) verdict cached, or only a pass?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: E-04 decides FROM THE REAL DIGEST FUNCTION. Caching a pass is the money saver and is clearly safe. Caching a fail is probably safe because a genuine fix (moving the work into a child) edits the orchestrator's E-item text and so changes the digest, self-invalidating the entry. The executor must CONFIRM that on the implemented digest rather than assume it, because a pinned stale fail would block a corrected orchestrator, and record which was chosen with the evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the digest of one real orchestrator computed twice in separate processes, showing byte-identical output (determinism, not just repeatability within one run).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste before/after digests for FOUR no-op mutations (tick a checkbox, fill Observed evidence, append a history line, edit a prose section) showing NO change, and for an E-item action edit showing a change. This is the `xmqv5l` regression guard.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a write-then-read round trip including the recorded model; paste `git check-ignore -v` proving the store path is ignored; paste the behavior on a deliberately corrupted entry showing it reads as absent rather than raising.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a miss returning `unknown` (NOT pass), and the recorded fail-caching decision with the digest evidence behind it. Include a mutation check: make a miss return pass, show a test FAILS, revert.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted object-identity output per new symbol, plus confirmation the `agy_runipd`-from-`oc_runipd` import count did not increase.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved 8tgg6g --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
