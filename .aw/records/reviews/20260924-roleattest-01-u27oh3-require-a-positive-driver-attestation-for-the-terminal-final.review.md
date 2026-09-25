# Review findings: plan u27oh3

- Subject-Id: u27oh3
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed Order 01 of Set `roleattest`, the only child, `- Item-Dependencies: none`. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE semantic review, and
`--phase review-finalize --agent` reports `clean`, exit 0, ZERO findings after the revisions. The plan
file was committed and unchanged, so no pre-review snapshot was needed. Everything below was measured in
this lane at HEAD `f768cadd`.

THE DIAGNOSIS IS CORRECT AND THE DESIGN IS THE RIGHT SHAPE. All seven author findings were re-derived
and held. The shipped code really does gate the terminal transition on nothing but the ABSENCE of a
strippable variable (`if worker_role_active(os.environ if env is None else env):` in both `finalize`
and `retire_orchestrator`, with no positive check anywhere), a grep for any driver token really does
return nothing, and the code's own HONEST LIMIT comment names the very incident the plan cites. The
author's rejection of the two weaker alternatives (bind to the receipt's actor; lane detection alone)
is sound, and F-4 is the key insight that makes the design non-trivial: the driver's own finalize runs
INSIDE the lane (`cwd=str(repo)`, `--dir <lane>`), so a lane-root gate without token plumbing would
break the driver rather than the attacker.

THE IMPLEMENTATION INSTRUCTIONS, HOWEVER, CONTAINED TWO DEFECTS THAT WOULD HAVE INVERTED THE OUTCOME,
and both were found by running the shipped helpers rather than reading them. A security gate whose
verifier looks in the wrong place does not fail open; it fails CLOSED on the legitimate holder, which
here means refusing the driver's own finalize and stranding every lane. That is a worse operational
outcome than the bypass being closed.

```text
F-8  THE VERIFIER'S PATH CAN NEVER EXIST
     E-02 said:  checkout_control_root(repo_root) / ".aw/records/runs" / <run-id>
     measured:   checkout_control_root(.)            -> <checkout>/.aw     (.name == ".aw")
                 E-02 expression                     -> <checkout>/.aw/.aw/records/runs   exists() False
                 correct sibling                     -> <checkout>/.aw/records/runs       exists() True
     => every verification fails "missing file"; the DRIVER is refused; every lane strands

F-9  EVEN CORRECTED, IT ASSUMES ONE RECORDS BACKEND, AND IS REPO-ARGUMENT-SENSITIVE
     state_root docstring: "records_backend settings (repository, companion, home) each yield the
                            correct location"
     RecordsBackend members measured: ['home', 'companion', 'repository']
     state_root(<lane>) -> <lane>/.aw/records/runs        # LANE-LOCAL; driver never wrote here
     state_root(<main>) -> <main>/.aw/records/runs        # where the driver actually mints
     => verifier must call state_root AND collapse its repo_root to the main checkout first

F-10 E-01's STOP CONDITION WOULD HAVE FIRED ON A FALSE ALARM
     commit_lock.coordinator_worktree: mkdtemp(prefix=".aw-coordinator-", dir=str(repo_root.parent))
     probed with a real checkout + real aw/lane/abc123 lane + real coordinator worktree:
       scratch path   -> <repo>/.aw/worktrees/.aw-coordinator-pqno44ce
       under .aw/worktrees/ ?  True     <- DOES match E-01's path criterion
       on aw/lane/* ?          False    <- branch is aw/coordinator/...
     => safe for a DIFFERENT reason (coord.path never reaches a transition), not the one assumed
```

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness) / B (security) | `agent_workflows/ipd_lifecycle.py` `checkout_control_root`; plan `E-02` | THE VERIFIER'S RUNS-ROOT PATH CAN NEVER EXIST, so the gate would refuse the DRIVER rather than the agent. E-02 specified `checkout_control_root(repo_root) / ".aw/records/runs" / <run-id>`, but `checkout_control_root` returns the `.aw` DIRECTORY ITSELF (measured: `<checkout>/.aw`, `.name == ".aw"`), so the expression yields a DOUBLED segment `<checkout>/.aw/.aw/records/runs` whose `exists()` is False while the real directory `<checkout>/.aw/records/runs` exists. Every `verify_driver_attestation` call would return `(False, "missing file")`, including the driver's own, so `runner_shared.driver_finalize` would refuse on every managed run and strand every lane. This is worse than the vulnerability: the bypass is opportunistic and rare, while this would be total and immediate. An executor following E-02 literally would have written it, passed E-02's stated expected outcome only if the test minted and verified through the same wrong helper, and shipped it. | C:Low; U:Low; S:High; F:High; Overall:Medium | FIXED | E-02 rewritten to require `runner_shared.state_root` and to FORBID any hand-composed `.aw`-relative path, with both measurements recorded and the lazy-import escape named in case of a cycle. V-02 now demands the expression be pasted showing no `".aw/records/runs"` literal. |
| PR-002 | HIGH | IN-SCOPE | A (correctness) / C (architecture) | `runner_shared.state_root` docstring; `project_schema.RecordsBackend`; `runner_shared.initialize_run_core` | EVEN WITH PR-001 FIXED, A HAND-COMPOSED PATH BREAKS TWO MORE WAYS. (a) It assumes the `repository` records backend. `state_root` resolves through the project context precisely so all three backends work, and `RecordsBackend` really has three members (measured `['home','companion','repository']`), so under `home` or `companion` the driver mints where the verifier never looks. (b) `state_root` is REPO-ARGUMENT-SENSITIVE: the driver mints with the MAIN checkout (`initialize_run_core` resolves `repo = Path(args.repo)`) while the verifier runs with a LANE as `repo_root`, and `state_root(<lane>)` returns a LANE-LOCAL `<lane>/.aw/records/runs` the driver never wrote to (measured). So calling `state_root` is necessary but not sufficient: the verifier must collapse to the main worktree first. | C:Medium; U:Low; S:High; F:High; Overall:Medium | FIXED | E-02 now requires the verifier to derive its root as `state_root(checkout_control_root(repo_root).parent)` (verified at review that `checkout_control_root(<lane>).parent` IS the main checkout root), and V-02 REQUIRES a test proving a lane `repo_root` and the main `repo_root` resolve to the SAME runs directory, with both paths printed. That equality is named in the gate as the single assumption the design rests on. |
| PR-003 | HIGH | IN-SCOPE | G (executability) | `agent_workflows/commit_lock.py` `coordinator_worktree`, `COORDINATOR_WORKTREE_PREFIX`; plan `E-01` | E-01's STOP CONDITION WOULD HAVE HALTED THE PLAN ON A FALSE ALARM. It instructed the executor to stop and report if the coordinator scratch worktree is under `.aw/worktrees/` or on an `aw/lane/*` branch. Measured by building a real checkout, a real `aw/lane/abc123` lane and a real coordinator worktree from that lane: `coordinator_worktree` creates its tree at `tempfile.mkdtemp(prefix=".aw-coordinator-", dir=str(repo_root.parent))`, so from a LANE it lands at `<checkout>/.aw/worktrees/.aw-coordinator-XXXX`, which DOES satisfy the path criterion. The branch is `aw/coordinator/...`, so only one of the two criteria matches, and the plan's phrasing ("matches neither") is false. The design is nonetheless safe, but for a reason the item never states: `coord.path` is used only for git plumbing inside `_finalize_transaction` and is never passed as `repo_root` to a transition. As written, a careful executor stops; a careless one pastes a false V-01 claim. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 records the measurement, states the real safety property (no transition is ever called with the scratch path) and narrows the STOP condition to exactly that. V-01 now requires the honest path/branch report and forbids the "matches neither" wording. The false trigger was removed from `Scope check`, and the gate calls the removal out explicitly so an executor does not halt on it. |
| PR-004 | MEDIUM | IN-SCOPE | E (verification) | `ipd_lifecycle.run_finalize`; `status_set` `_life.finalize` call | E-04 ASKED THE EXECUTOR TO CONFIRM SOMETHING FALSE. It said to "confirm `run_finalize` passes the process env through (it currently calls `worker_role_active(os.environ)` itself)". Measured: `run_finalize` calls `worker_role_active(os.environ)` for its own early refusal and then calls `finalize(...)` with NO `env` argument at all; `status_set`'s call likewise passes no `env=`. Both rely on `finalize`'s internal `os.environ if env is None else env` default. The confirmation as worded fails, and an executor "fixing" it by threading `env=` would modify two undeclared files and diverge the two routes. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 rewritten to state what is actually true and to require relying on the existing default while threading NOTHING; V-04 now requires evidence that `run_finalize`'s call is unchanged and `status_set.py` unmodified; `Scope check` records both as deliberately undeclared with the verification behind it. |
| PR-005 | MEDIUM | IN-SCOPE | E (verification) | `runner_shared.dispatch_orchestrator_item` | E-05(d) AND V-05 IMPLIED A CLAIM THAT IS FALSE. `dispatch_orchestrator_item(repo: Path, ...)` passes that same `repo` to `retire_orchestrator`, and that `repo` is the MAIN checkout, never a lane, so `lane_worktree_active` is already False there and the retirement would pass the E-03 gate WITHOUT an attestation. Plumbing it is still worth doing (explicitness, and correctness if a future change retires from a lane), but a `V-*` asserting this site "would otherwise refuse" would be a false evidence claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(d) gained a note stating it is belt-and-braces and why; V-05 now forbids the stronger claim and requires the honest wording. F-12 records the mechanism. |
| PR-006 | MEDIUM | IN-SCOPE | G (executability) | `tests/` tree; plan `E-07` case (7) and a `Project conventions` bullet | THE PLAN CITES A TEST FILE THAT DOES NOT EXIST, TWICE. E-07 case (7) says to drive the child-env check "the way `tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_both_drivers_mark_only_an_isolated_turn` does, without modifying that file", and a convention bullet says that file is owned by executed plan `8b9ufm` and must not be modified. Measured: no such file (`ls tests/ \| grep -iE "worker\|role"` is empty) and no such class anywhere in `tests/`. So there is no pattern to imitate and no file to protect; an executor would spend a cycle hunting for it. The real facility is `tests/support.declare_execution_role`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 case (7) rewritten to build against the two real one-line child-env sites and to use `tests/support.declare_execution_role`; the convention bullet replaced with the measurement and a pointer to the surfaces that do exist (`tests/support.py`, `tests/test_orchestrator_retirement.py`). F-13 records both greps. |
| PR-007 | MEDIUM | IN-SCOPE | E (verification) / D (anti-regression) | `CHANGELOG.md`; `ipd_lifecycle.finalize` HONEST LIMIT comment; backlog `770fkp`, `6z5yos` | TWO STALE FACTS, ONE OF WHICH THE PLAN INSTRUCTS THE EXECUTOR TO PRESERVE. (a) E-08 says to add the entry "under Unreleased"; that heading does not exist (`grep -c Unreleased CHANGELOG.md` -> `0`; the pending heading is `## 1.3.0 (pending)`), so V-08 was unsatisfiable as written. (b) The shipped HONEST LIMIT comment E-03 must rewrite says the `env -u` habit "is driven by a real defect - lifecycle tests fail inside a lane (backlog `770fkp`/`s0303g`) - so agents will keep reaching for it until that is fixed". Measured: `770fkp` is `done` and the follow-on `6z5yos` (the remaining 31st test) is `done` too. An executor rewriting the comment would carry a fixed defect forward as live motivation, which is exactly the rot this repository's comment discipline exists to prevent. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-08 names `## 1.3.0 (pending)` with the measurement and requires re-derivation at execution; V-08 requires the heading list pasted first plus an em/en-dash check on added lines; E-03 and the `Spec / documentation sync` section now forbid repeating the stale clause and state what the current limit actually is. F-14 records both. |
| PR-008 | MEDIUM | UNDER-SCOPE | G (executability) | plan `## Approval and execution gate` | THE GATE WAS ONE PARAGRAPH FOR A SECURITY CHANGE TO THE MOST CONSEQUENTIAL TRANSITION IN THE TOOLKIT. It carried the commit discipline, the honesty rule and the OQ dispositions, but no statement of what a human is approving, no scope fence in the declaration form, no stop conditions, and no warning about the new failure mode this design introduces (mint/verify divergence stranding every lane) even though that is precisely what PR-001 and PR-002 found. It also did not say that a minted token must never be committed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Gate rewritten: what is approved and the new failure mode named explicitly, with the residual the plan honestly states; declaration-style fence naming `status_set.py`/`run_finalize` as deliberately not to be edited; three genuinely-unsafe stop conditions (mint/verify inequality, scratch path reaching a transition, an unenumerated call site); an explicit note that E-01's original false-alarm stop was REMOVED so an executor does not halt on it; the bare-`pytest` rule with the `-qq` trap; a real-lane-in-a-throwaway-repo requirement; never-commit-a-token; staged-set verification; conditional transition with no hand-rolled `git mv`; and the `c4yixg` HANDOFF verified as already satisfied. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 is a BLOCKER: the authored verifier path can never resolve. Is that `REPLAN`, or repairable with bounded edits? | Repair in place; `APPROVE WITH REVISIONS APPLIED`. | `REJECT - NEEDS REPLAN`. Rejected: the DESIGN is sound and survives untouched (per-run secret, minted outside every lane, carried only on the driver's own subprocess env, lane-scoped gate, main-checkout behavior unchanged). What was wrong is ONE path expression inside ONE E-item, and the fix is to call an existing shipped resolver instead of composing a path by hand. No scope, no declared path, and no other E-item changes. | `plan-review` Step 2.4 reserves `REPLAN` for an approach "fundamentally unsound and cannot be repaired with bounded edits". A wrong path literal in an implementation instruction is the opposite of a foundational design flaw, and the repair is smaller than the finding that produced it. | yes |
| D-2 | Should the verifier use `runner_shared.state_root`, or keep a local path derivation to avoid an `ipd_lifecycle` -> `runner_shared` import? | Use `state_root`, lazily imported if needed. | (a) Keep a hand-composed path with the doubling fixed. Rejected: PR-002 shows it silently breaks the `home` and `companion` backends, and a second derivation of the same fact is exactly the drift this repository's "one owner per rule" convention forbids. (b) Move the derivation into a third shared helper. Rejected: `state_root` already IS that helper. | `state_root`'s docstring states it exists so every records backend resolves correctly; `ipd_lifecycle` already performs lazy intra-package imports (e.g. `from agent_workflows import ipd_schema as _schema` inside `_is_implicitly_allowed`), so a cycle has a known, already-used remedy. The alternative was measured to be wrong for two of three backends. | yes |
| D-3 | E-01's false-alarm STOP (PR-003): remove it, or leave it and let the executor discover the scratch worktree is harmless? | Remove it and replace with the narrow condition that actually matters. | Leaving it as authored. Rejected: it fires on a SAFE design, and a stop costs a human round trip on a question already answered by measurement. Also rejected: deleting the concern entirely, which would lose a real hazard (a nested transition on the scratch path would self-refuse). | Measured that the scratch tree DOES match the path criterion from a lane, and that `_finalize_transaction` uses `coord.path` only for the plan mirror, `apply_status_change`, `git add` and `git commit`. So the property to verify is "no transition is called with the scratch path", which is checkable by grep and is what the narrowed trigger names. | yes |
| D-4 | Should this plan be required to author a spec, given it introduces a new security boundary and no `.spec.md` describes the lifecycle authority model? | No. Record the observation, do not make it a finding. | Raising a spec-sync finding and requiring a spec before approval. Rejected: it would invent an obligation the repository does not currently impose, and the plan's own spec-sync section already states the grep result honestly. | Re-verified at review that `grep -rln "AW-LIFECYCLE-ROLE-001\|AW_EXECUTION_ROLE" .aw/records/specs` returns nothing, so there is no spec to amend and no contract this plan contradicts. AGENTS.md obliges a plan to DECLARE a spec it amends, not to author one where none exists. Recorded as a reviewer's note in the plan so a maintainer can ask for one deliberately. | yes |
| D-5 | OQ-02 (should `aw ipd begin` get the same gate?) is `Blocking: no` with a default of NO. Accept, or widen the plan? | Accept the default; do not widen. | Adding `begin` E-items here. Rejected: it doubles the plumbing surface in a security change that already needed two corrections, and the harm the incident produced was specific to the TERMINAL transition (a consumed receipt and a forged `executed` record). | The plan's own reasoning is sound and the maintainer brief scoped it to the terminal transition. `begin` is gated by the env selector today, so this plan leaves it no weaker than it is. The asymmetry is recorded in the plan as a non-blocking OQ, which is the right disposition: it is a scope decision, not a defect. | yes |

### Measurements taken at review

```text
aw ipd lint --phase author          --agent u27oh3 -> {"outcome":"clean","exit":0,"findings":0}
aw ipd lint --phase review-finalize --agent u27oh3 -> {"outcome":"clean","exit":0,"findings":0}  (after)

THE DEFECT (F-2, F-3), confirmed:
  both finalize and retire_orchestrator gate ONLY on:
      if worker_role_active(os.environ if env is None else env):
  grep -rn "driver_token|AW_DRIVER_TOKEN|driver\.token|DRIVER_ATTEST" agent_workflows/  -> no output

F-4, confirmed (why token plumbing is mandatory):
  runner_shared.driver_finalize builds ["ipd","finalize",id6,...,"--apply","--dir",str(repo)]
  and its own comment: "`repo` here is the LANE worktree ... `cwd=str(repo)` below keeps it that
  way DELIBERATELY, because finalize must resolve paths against the tree it is finalizing"

CALL SITES (F-5), exactly as the plan states, FIVE non-definition:
  oc_runipd.py:1284   -> runner_shared.driver_finalize(
  agy_runipd.py:1247  -> runner_shared.driver_finalize(
  runner_shared.py:27469, :27692 -> driver_finalize(        (the two execute_item_core sites)
  runner_shared.py:16575 -> _lifecycle.retire_orchestrator(  (main-checkout repo, see F-12)
  status_set.py:1475  -> _life.finalize(                     (the human route)

CHILD ENV SITES (F-6), one line each:
  oc_runipd.py:3488  child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER
  agy_runipd.py:2482 same

CORRECTIONS (PR-001..PR-007):
  checkout_control_root(.)  -> <checkout>/.aw          (.name == ".aw")   # F-8
  E-02 expr  -> <checkout>/.aw/.aw/records/runs  exists False
  correct    -> <checkout>/.aw/records/runs      exists True
  state_root(<lane>) != state_root(<main>)                                # F-9
  RecordsBackend -> ['home','companion','repository']
  scratch from a lane -> <repo>/.aw/worktrees/.aw-coordinator-XXXX        # F-10
     under .aw/worktrees/ True | on aw/lane/* False (it is aw/coordinator/)
  run_finalize calls finalize(...) with NO env=                           # F-11
  dispatch_orchestrator_item(repo) -> retire_orchestrator(repo) = MAIN    # F-12
  tests/test_worker_role_refusal.py                    ABSENT            # F-13
  grep -c Unreleased CHANGELOG.md -> 0                                   # F-14a
  770fkp -> done | 6z5yos -> done | s0303g -> graduated                   # F-14b

RESIDUAL (F-15), the plan's honest limit, confirmed:
  <main>/.aw/records/runs readable from this lane by absolute path: True
  git check-ignore -v .aw/records/runs -> no match
  1o4eif and 8b9ufm both present in .aw/records/plans/executed/

HANDOFF: c4yixg has 'Blocks-Release: next' and Status graduated; this plan carries
  'From-Backlog: c4yixg' + the same 'Blocks-Release: next' -> HANDOFF route satisfied
commit 575f0b32 resolves: "lifecycle(63425h): finalize 63425h -> executed"
```

NOT RE-RUN AT REVIEW, and stated rather than implied: the repository suite. This review changed only
planning prose, so no suite baseline is claimed in either direction. E-08 re-runs the bare suite plus
five driver families at execution, which is the correct treatment.

NOT VERIFIED AT REVIEW, and recorded rather than glossed: I did not exercise a real `aw oc run` or
`aw agy run` end to end, so the claim that the corrected mint/verify path agrees for the DRIVER's
actual invocation rests on reading `initialize_run_core`'s `repo` resolution plus the measured
`state_root`/`checkout_control_root` behavior, not on a live run. That is exactly why V-02 was
strengthened to require a TEST proving the lane/main runs-directory equality rather than an argument
for it: this is the assumption the whole design rests on, and it should not reach production on a
reviewer's reasoning.

### Verdict and readiness

APPROVE WITH REVISIONS APPLIED. PR-001..PR-008 all FIXED, none deferred, none open. PR-001 was a
BLOCKER and is fixed in place (D-1); OQ-01 is resolved and OQ-02 remains `Blocking: no` with a
reviewed default (D-5), which under the 2026-09-10 maintainer ruling does not make the plan `NO-GO`.

Readiness `go-pending-approval`. What a human should weigh at approval, none of it a finding: this adds
a real security boundary to the terminal lifecycle transition, and its failure mode is asymmetric. If
the token is minted in one place and sought in another, the DRIVER is refused and every lane strands,
which is operationally worse than the opportunistic bypass being closed. Review found that exact defect
twice in the authored instructions, which is why V-02 now demands the path equality be proven by a test
rather than argued. The bypass this closes is the good-faith `env -u` kind; a malicious same-user agent
can still read the minted token by absolute path, and closing that needs the `1o4eif` sandbox, which
the plan correctly defers rather than pretending to solve.
