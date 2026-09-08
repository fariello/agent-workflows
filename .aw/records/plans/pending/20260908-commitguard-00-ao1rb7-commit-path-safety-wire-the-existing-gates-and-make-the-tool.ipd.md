# IPD: Commit-path safety: wire the existing gates and make the tooled path mandatory

- Date: 2026-09-08
- Kind: orchestrator
- Concern: Backlog item `wjl471` contains two independently valuable halves with very different risk profiles, and running them as one plan would couple a near-free configuration change to a contract change that rewrites the guidance installed into every managed repo. Its FINDING 2 is that four of six shipped gate verbs are invoked by nothing and no `pre-push` hook exists at all, which is pure wiring of working code. Its MAINTAINER RULING of 2026-09-01 is that the commit contract must say MUST rather than PREFER, which cannot land honestly until `aw commit` has a plan-less form to comply with and until the retry its wording DESCRIBES actually exists.
- Scope: Orchestration only. Sequence the two children, hold the Set's shared constraint (the honest-limit disclosure rule), and define what makes the whole Set complete. Every deliverable belongs to a child; this parent performs no implementation work of its own.
- Scope-Paths: .aw/records/plans/pending/20260908-commitguard-01-kbqpkn-wire-the-four-unwired-gates-and-install-the-missing-pre-push.ipd.md, .aw/records/plans/pending/20260908-commitguard-02-y9vpvv-add-a-plan-less-aw-commit-and-land-the-ruled-must-wording.ipd.md
- Item-Dependencies: none
- Status: to-review
- Set: commitguard
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ao1rb7
- From-Backlog: wjl471

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `wjl471` as the Order-00 parent of a two-child Set. WHY A SET RATHER THAN ONE PLAN: the item's two halves have different risk, different prerequisites and different reviewers' concerns. Order 01 (`kbqpkn`) wires four gates that already work and depends on nothing, so it can land immediately. Order 02 (`y9vpvv`) replaces two paragraphs of the managed block that is installed into EVERY managed repo, and carries the item's own HARD ORDERING CONSTRAINT that its retry sentence must not ship before the retry exists; it therefore declares `Item-Dependencies: executed:lqly9m` (the graduated `egqt32` plan). Coupling them would block the free half behind the gated half. WHAT IS DELIBERATELY NOT IN THIS SET: the item's FINDING 1, the agent-context detector and the new commit guard, with its four open questions (where the guard lives, what accident it catches, how it phrases the refusal, how an override is audited). That is a real design needing a maintainer ruling on shape, and the item itself says the gate wiring "may catch most of the remaining accidents at near-zero cost", so the cheap wins are separated from the design. VERIFIED AT HEAD `a2e0438a` that both halves are live: the four gates each appear ZERO times in `.pre-commit-config.yaml` while the two wired ones appear, the only installed git hook is `pre-commit`, `aw commit` still refuses without a plan selector (`work_cmd.py:138`), and the PREFER paragraph still carries the "immune to this by construction" claim (`engine.py:1252-1256`).
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Land the two halves of `wjl471` in the right order: turn on the guards that already work, and make the tooled commit path mandatory only once it is compliable and only once the contract's descriptive claims are true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the children and hold the Set-wide constraint

- [ ] E-01 Execute Order 01 (`kbqpkn`, wire the four unwired gates and install the `pre-push` stage) and confirm it reports conforming before proceeding. It depends on nothing, so it goes first and its value does not wait on the contract half. This item is ORCHESTRATION: the deliverables are the child's, and this parent's job is to confirm the child ran and passed rather than to perform any wiring itself.
  - Depends on: none
  - Expected outcome: `kbqpkn` is `executed` with every `V-*` carrying observed evidence.
  - Execution state: pending

- [ ] E-02 Execute Order 02 (`y9vpvv`, plan-less `aw commit` plus the ruled MUST wording) only after its declared dependency is satisfied, and confirm it reports conforming. It declares `Item-Dependencies: executed:lqly9m`, which encodes the item's hard ordering constraint; its own E-05 re-proves the retry by behavior at execution time and provides the documented fallback (ship the imperative, withhold the descriptive sentence) if the retry is absent. Do NOT relax that edge to make the Set finish sooner: the whole reason it exists is to stop the managed block describing behavior the code lacks.
  - Depends on: E-01
  - Expected outcome: `y9vpvv` is `executed` with the wording landed and its retry claim either proven or explicitly withheld.
  - Execution state: pending

- [ ] E-03 Enforce the Set-wide HONESTY CONSTRAINT across both children's output, because it is the one requirement the item says "still matters" and it spans them: "a bypassable guard must never be DESCRIBED as a boundary, because that is how a fail-open check comes to be trusted." Order 01 turns bypassable gates ON, and Order 02 rewrites the paragraph that describes the commit path's guarantees, so both can violate it independently. After both children complete, re-read the shipped disclosures and the shipped wording together and confirm no sentence claims a boundary that `--no-verify` defeats. This is a CROSS-CHILD CHECK that neither child can perform alone, which is why it belongs here rather than being pushed down.
  - Depends on: E-02
  - Expected outcome: a stated confirmation that every gate disclosure and every contract sentence shipped by this Set describes local, bypassable feedback accurately, with any offending sentence corrected.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | `20260908-commitguard-01-kbqpkn-wire-the-four-unwired-gates-and-install-the-missing-pre-push.ipd.md` | Confirms each unwired gate's intent, proves it runs clean, registers the cleared ones, installs the `pre-push` stage so the push gate can fire, and adds a declared-list wiring test | none |
| 02 | `20260908-commitguard-02-y9vpvv-add-a-plan-less-aw-commit-and-land-the-ruled-must-wording.ipd.md` | Adds `aw commit --no-plan` so the MUST is compliable, lands the ruled MUST wording verbatim, and applies the companion narrowing | `executed:lqly9m` (the graduated `egqt32` retry) |

The two children are otherwise INDEPENDENT: Order 01 touches `.pre-commit-config.yaml` and the wiring test, Order 02 touches the commit verb and the managed block. They share no source file, so Order 01 need not wait on Order 02's dependency.

## Completion criteria (the whole Set is done only when)

- Every gate whose exclusion was found to be an OVERSIGHT is registered and demonstrably fires; every gate whose exclusion was found to be DELIBERATE is documented as such and left alone.
- A `pre-push` hook stage is installed and the push gate fires on push and not on commit.
- `aw commit --no-plan -m <msg> -- <paths>` commits through `offer_commit` with the skipped protections named, and still excludes a concurrent agent's staged files.
- `engine.py` carries the ruled MUST wording verbatim and `AGENTS.md` renders it, with the descriptive retry sentence present only if the retry was demonstrated.
- The `git reset`/`git stash` prohibition is byte-identical to before.
- No sentence shipped by either child describes a bypassable guard as an authority boundary.

## Cross-IPD validation

- NO DOUBLE-EDIT of `.pre-commit-config.yaml`: only Order 01 touches it, and approved sibling plan `29wvmj` E-06 also edits it for `pre-merge-commit`, so Order 01 must extend that list rather than replace it. Confirm after both land that `default_install_hook_types` contains every stage all three changes intended.
- NO CONTRADICTION between the wiring and the wording: Order 01 makes more gates fire on commit, and Order 02's wording tells agents the tooled path costs no round trip. If a newly wired gate REFUSES (rather than rewrites), that is correct and the wording's retry claim does not cover it; confirm the wording does not imply otherwise.
- ONE SOURCE FOR THE MANAGED BLOCK: `AGENTS.md` is generated from `engine.py`. Confirm the committed `AGENTS.md` matches a fresh regeneration, so the Set does not leave a hand-edited block behind.

## Deferred / out of scope (with reason)

- THE AGENT-CONTEXT DETECTOR AND THE NEW COMMIT GUARD (the item's FINDING 1 and OQ-1 through OQ-4). The item's environment-marker matrix across five agent hosts is durable evidence and is committed with the item, but the guard itself needs a maintainer ruling on where it lives (pre-commit hook sees the staged set but not the INTENT; a `git` wrapper sees intent but is invasive; reading `reflog` is too late), what accident it catches, and how an override is recorded. None of that is required to wire four working gates or to land a wording ruling.
- SETTING `AI_AGENT` OURSELVES IN THE DRIVERS. Part of the detection design.
- `mjx7ne`'s `commit_gateway` / `deny_push` HOST CAPABILITIES, which the item notes grep to zero enforcement. A separate open item.
- THE OS-LEVEL CONFINEMENT QUESTION (research prompt `q65sz3`). The item explicitly does not depend on it.
- `suugsf`, `a8eufb`, `077yqc`. Related open items about the contract not warning about a shared checkout and about finalize misattributing a concurrent agent's files; all outside this Set.

## Scope check

- Over-scope: none. This parent's `Scope-Paths` are its two children, and it performs no implementation.
- Under-scope: the new guard and the detector are deliberately not in this Set (see Deferred), so `wjl471` will remain open after this Set completes unless the maintainer decides the wiring plus the wording is the whole answer.

## Required tests / validation

- Each child's own validation must pass on its own terms; this parent adds no test of its own.
- After both children land: `pre-commit run --all-files` clean, the bare `python3 -m pytest` summary line pasted and compared to the baseline (1 failed, 5648 passed on `main`, the known `test_orchestrator_retirement` failure), and a fresh `AGENTS.md` regeneration producing no diff.

## Open questions

### OQ-01: After this Set lands, is `wjl471` closed or does it stay open for the guard?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED because it is a scope judgement, and recorded so the item is not closed by accident. This Set delivers the item's FINDING 2 and its MAINTAINER RULING in full, but NOT its FINDING 1 (the agent-detecting guard), which is the item's headline. RECOMMENDATION: keep `wjl471` open after this Set, or split the guard into its own item carrying the environment-marker evidence table, since that table is the durable record and the raw dumps it cites are gitignored and local-only. Closing the item on this Set alone would lose the guard design and the five-host measurement with it.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `kbqpkn`'s final status showing `executed`, and paste its `V-01` through `V-06` observed-evidence blocks (or a summary quoting each) demonstrating they carry real pasted evidence rather than assertions.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `y9vpvv`'s final status showing `executed`, paste the evidence that its `Item-Dependencies: executed:lqly9m` edge was SATISFIED at dispatch (not waived), and state which E-05 outcome occurred (retry demonstrated and full wording shipped, or retry absent and the descriptive sentence withheld).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste every disclosure sentence shipped by Order 01 and every contract sentence shipped by Order 02, and for each state whether it describes a bypassable local check accurately. Paste any sentence corrected as a result. A blanket assertion that "the disclosures are fine" does not satisfy this item; the sentences must be quoted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This orchestrator is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. Each child carries its own approval gate and must be approved on its own terms; approving the parent does not approve the children.

This parent holds ORCHESTRATION ONLY: E-01 and E-02 sequence the children and E-03 is a cross-child honesty check that neither child can perform alone. No implementation work lives here, so a runner that retires this parent once both children are `executed` skips nothing that was never performed elsewhere.

Execution contract: each child commits only its own `Scope-Paths`, path-scoped, never `git add -A`, never push. When both children are `executed` and E-03's cross-child check carries pasted evidence, this parent may be retired to `.aw/records/plans/executed/` through `aw ipd finalize`. Note OQ-01: retiring this Set does NOT by itself close backlog item `wjl471`, which retains the guard design.
