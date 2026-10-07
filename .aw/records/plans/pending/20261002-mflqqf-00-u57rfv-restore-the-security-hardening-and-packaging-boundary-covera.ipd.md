# IPD: Restore the security-hardening and packaging boundary coverage, and fix the loopback fail-open it exposes

- Date: 2026-10-02
- Kind: orchestrator
- Concern: BACKLOG ITEM `mflqqf` NAMES TWO INDEPENDENT BOUNDARY SURFACES THAT LOST THEIR TEST GUARDS IN THE SAME COMMIT, and re-measuring both at HEAD `4fbbc8386` changed what the work is on BOTH halves, which is why this is a Set of two rather than one plan. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24) deleted `tests/test_security_hardening.py` (1190 lines) and `tests/test_packaging.py` (503 lines). ON THE SECURITY HALF the item's measurement still holds exactly (`rg -l security_hardening tests/` returns nothing), but a PURE RESTORATION WOULD HAVE BEEN GREEN AND UNINFORMATIVE: I recovered the deleted suite into gitignored scratch and it passed, `10 passed in 0.29s`. So I probed the uncovered checkers directly and found a LIVE FAIL-OPEN that the deleted suite could never have caught, because it carried no such row: `check_local_server_binding` tests loopback with the bare string prefix `startswith("127.")`, so the attacker-controlled hostnames `127.0.0.1.evil.com`, `127.evil.com` and `127.0.0.1@evil.com` are each ACCEPTED as loopback while `docs/security.md` tells a reader the checker "refuses a bind to a routable address". ON THE PACKAGING HALF the item's measurement is PARTLY STALE: `tests/test_packaging.py` is BACK, 183 lines restored by `2edb9ff8e` (plan `iocyf3`), and it does build the wheel and assert its contents, so there is nothing to restore there. The remaining gap is narrower and I measured which parts: nothing in the tree builds an SDIST at all, nothing asserts the three console scripts, and nothing asserts the browser assets are present in either artifact, which is the one that matters most because hatchling drops a gitignored asset at exit 0 with no warning (reproduced at authoring).
- Scope: Orchestrate the two children that close the measured remainder of item `mflqqf`: Order 01 restores the security-hardening boundary coverage, fixes the loopback fail-open, covers the module's single production integration point, and corrects the document that overclaims; Order 02 adds only the packaging properties the already-restored wheel guard does not reach. This plan itself touches no product file and performs no work of its own beyond confirming its children and the cross-child properties stated below. Out of scope for the whole Set: wiring any boundary checker into `aw check` or a hook, the `RedactionPolicy` case-sensitivity defect (recorded by Order 01, lives in another module), restoring the deleted benchmark arms, and re-asserting the two packaging properties `tests/test_packaging.py` already covers.
- Scope-Paths: .aw/records/plans/pending/20261002-mflqqf-00-u57rfv-restore-the-security-hardening-and-packaging-boundary-covera.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: dfe4410d16c2d74d826e0745a1d60db25ee7db7620ce8da425c15d19c50f6914
- Coverage-Checked: 2026-10-07 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: security
- Priority: high
- From-Backlog: mflqqf
- Set: mflqqf
- Order: 0
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: u57rfv

## Workflow history
- 2026-10-07 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004. Reviewed at HEAD 5ce4a3f2e. d0lg63 evidence range corrected to V-01..V-06; single-child criteria owners narrowed; mflqqf's actual open state recorded and the gate aligned with OQ-02; stale child-approval sentence restated. Coverage repair 2 attempts, passing. Review record .aw/records/reviews/20261002-mflqqf-00-u57rfv-restore-the-security-hardening-and-packaging-boundary-covera.review.md.
- 2026-10-07 coverage pass (aw oc run): fingerprint dfe4410d16c2, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 coverage fail (aw oc run): fingerprint f0d280890d0c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 to-review (aw set): returned to review: both children executed; criteria and cross-checks lead with owner and measured result; coverage pass recorded
- 2026-10-07 coverage pass (aw oc run): fingerprint 1ad7d6bd8bc7, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 coverage fail (aw oc run): fingerprint 059f37be057f, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): both children are executed; the cross-child checks were measured against them and recorded under Cross-IPD validation.
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: This plan runs no test itself; validation is an inspection of what the children actually produced

- 2026-10-06 coverage fail (aw oc run): fingerprint 7b7957ed9248, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `mflqqf` in lane worktree `mflqqf` at HEAD `4fbbc8386`. FOUR MEASUREMENTS SHAPED THIS SET, and two of them contradict the item.
  FIRST, THE SECURITY HALF OF THE ITEM HOLDS EXACTLY: all seven named checkers have zero test callers, and the deleted suite is real and gone.
  SECOND, A PURE RESTORATION WOULD HAVE BEEN WORTHLESS AND I DID NOT SHIP ONE. The recovered suite PASSES against current source (`10 passed`), so restoring it would have added a green file and found nothing. Probing the uncovered surface directly found a fail-open the deleted suite had no row for, and that is now the sharpest item in Order 01.
  THIRD, THE PACKAGING HALF OF THE ITEM IS PARTLY STALE AND A PLAN THAT TRUSTED IT WOULD HAVE DUPLICATED SHIPPED WORK. `tests/test_packaging.py` was restored by `2edb9ff8e` after the item was written. Order 02 therefore asserts NOTHING that file already asserts, and its Scope says so explicitly so a reviewer can check the non-overlap.
  FOURTH, THE BASE IS NOT GREEN, which changes the bar every child must be judged against. Bare `python3 -m pytest` gave `5 failed, 4622 passed, 2 skipped in 410.45s`; three failures are filed (`6bolin`, `8jeh4x`, `bxnhdj`) and TWO ARE NOT, and those two PASS IN ISOLATION (`2 passed in 118.59s`), so they are load-sensitive under `-n auto` rather than standing. Both children therefore set the bar at "no newly failing test" with a mandatory isolated re-run of every red node, never at "green".
  THE TWO CHILDREN ARE GENUINELY INDEPENDENT AND SHARE NO PATH, so neither depends on the other and they may be approved, reviewed and executed separately or in parallel.
  NO SPEC IS AMENDED, and no `.spec.md` appears in any child's `- Scope-Paths:`.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Address the measured remainder of backlog item `mflqqf` (the item closes through the runner's normal backlog close once both carriers are executed, never by hand from this plan): give the seven security boundary checkers and the packaging distribution contract real test callers again, and fix the one live fail-open that probing the uncovered security surface exposed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: orchestration of the mflqqf Set

- [ ] E-01 CONFIRM gqyold REACHED executed
  - Depends on: none
  Confirm child 01 (`gqyold`, restore the security-hardening boundary coverage and close the loopback prefix fail-open) is `executed` with its own validation evidence present, and confirm the cross-child properties: both children carry `- From-Backlog: mflqqf`, neither declares a `- Blocks-Release:` gate (the source item carries none, and the repository's release-gating work-kind set is `bug` alone, which `security` is not in), and their `- Scope-Paths:` are DISJOINT, which must be checked and stated rather than assumed. Confirm specifically that child 01's V-02 shows the four prefix-confusion rows failing BEFORE its fix and passing after, since a fix validated only after the fact does not demonstrate it addressed the measured defect.
  - Expected outcome: child 01 is `executed` with V-01..V-07 carrying pasted evidence; the child rows below resolve to real files on disk; the three cross-child properties are checked and reported, including an explicit statement that the two children's declared path sets do not intersect; no product file is touched by this item.
  - Execution state: pending

- [ ] E-02 CONFIRM d0lg63 REACHED executed
  - Depends on: none
  Confirm child 02 (`d0lg63`, add the packaging properties the restored wheel guard does not reach) is `executed`, and confirm the Set-wide NON-DUPLICATION property that this child's whole scope decision rests on: the new packaging file asserts neither of the two properties `tests/test_packaging.py` already covers (the ship-versus-dev boundary and the runtime-dependency allowlist), so the Set added coverage without creating a second place to update when the dependency allowlist legitimately changes. This is explicitly NOT dependent on E-01: the two children share no path and neither needs the other's result.
  - Expected outcome: child 02 is `executed` with V-01..V-06 carrying pasted evidence, each V-item including the FALSIFIABILITY demonstration that child requires (its arms are all expected green on arrival, so a passing run alone proves nothing); and the non-duplication property is reported by naming what the existing guard asserts beside what the new file asserts, rather than claimed.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `gqyold` | `20261002-mflqqf-01-gqyold-restore-the-security-hardening-boundary-coverage-as-outcome.ipd.md` | Restores behavioral coverage for the seven boundary checkers, the aggregate and the two canonical-scanner adapters as one per-module test file; adds the four prefix-confusion refusal rows the deleted suite never carried; fixes `check_local_server_binding` to test an ADDRESS rather than a string prefix, preserving the whole existing holding set; gives `host_runner.redact_worker_output` its first test caller; and corrects the two false claims in `docs/security.md`. | none |
| 02 | `d0lg63` | `20261002-mflqqf-02-d0lg63-restore-the-packaging-boundary-coverage-the-wheel-guard-does.ipd.md` | Adds the packaging properties nothing reaches today, in one new file: the SDIST allowlist (nothing in the tree builds an sdist at all), the three console scripts mapped to `agent_workflows.cli:main`, and the browser assets present and non-empty in both artifacts with an honesty guard against `run_analytics_spa.REQUIRED_ASSETS` plus the reproduced gitignore-silent-drop hazard. Asserts nothing the restored wheel guard already asserts. | none |

## Completion criteria (the whole Set is done only when)

1. [Owner: gqyold and d0lg63, both executed] BOTH children are `executed` and filed under `.aw/records/plans/executed/`, each with every `V-*` carrying concrete pasted evidence rather than an assertion: `gqyold` with V-01..V-07, `d0lg63` with V-01..V-06.
2. [Owner: gqyold and d0lg63, both executed] EVERY BOUNDARY CHECKER HAS A TEST CALLER, which is the item's own first measurement inverted. All seven `check_*` functions in `agent_workflows/security_hardening.py`, plus `run_boundary_checks` and the two scanner adapters, are driven by a committed test that asserts on the returned `BoundaryResult`, and `rg -l security_hardening tests/` returns a file where it returned nothing.
3. [Owner: gqyold and d0lg63, both executed] EACH BOUNDARY IS PINNED IN THE REFUSING DIRECTION, not only the holding one. Every table carries both a holding and a refusing row, because `ok=True` is the PERMISSIVE answer and a checker degraded to "always allow" is the realistic regression; child 01's V-01 proves this with a negative control that forces a checker permissive and shows the refusal rows breaking.
4. [Owner: gqyold, executed] THE LOOPBACK FAIL-OPEN IS CLOSED AND THE GATE WAS NARROWED, NOT REPLACED. `check_local_server_binding` refuses `127.0.0.1.evil.com`, `127.evil.com`, `127.0.0.1@evil.com` and `127.0.0.1 evil.com`, AND still holds for all five legitimate spellings (`127.0.0.1`, `::1`, `localhost`, `127.1.2.3`, the surrounding-whitespace form), with the `127.0.0.0/8` verdict decided explicitly rather than changed silently.
5. [Owner: gqyold, executed] THE MODULE'S ONE PRODUCTION WIRING IS COVERED. `host_runner.redact_worker_output` has a test caller pinning its ACTUAL behavior, including the measured fact that a planted home path yields `ok=False` while the returned text is NOT masked, so the module docstring's "masked/blocked" overclaim is recorded as an observable rather than carried forward as a belief.
6. [Owner: d0lg63, executed] THE PACKAGING DISTRIBUTION CONTRACT IS CHECKED ON BOTH ARTIFACTS. An sdist is built and asserted (where nothing built one before), the three console scripts are asserted to MAP to `agent_workflows.cli:main` rather than merely appear, and the browser assets are asserted present and non-empty in both wheel and sdist with a guard that fails if the module's declared asset list grows without the test's.
7. [Owner: d0lg63, executed] NO COVERAGE IS DUPLICATED. The new packaging file asserts neither property `tests/test_packaging.py` already covers, reported by naming both sides.
8. [Owner: gqyold, executed] THE TWO FALSE DOCUMENT CLAIMS ARE GONE. `docs/security.md` no longer says these boundaries ship "without dedicated test coverage (tracked in backlog item mflqqf)", and no longer describes the loopback gate as more absolute than the code enforces.
9. [Owner: gqyold and d0lg63, both executed] NO NEWLY FAILING TEST, measured against each executor's OWN execution-base baseline, with every red node re-run in isolation and classified as filed-and-pre-existing (naming the backlog id), load-sensitive, or NEW. "Green" is NOT the bar and must not be reported as achieved by excluding a node.

## Cross-IPD validation

MEASURED 2026-10-07 AGAINST THE EXECUTED CHILDREN (both `gqyold` and `d0lg63` are `executed`, every `V-*` `Result: pass`): the paths their commits changed are disjoint (`gqyold`: `agent_workflows/security_hardening.py`, `docs/security.md`, `tests/test_security_hardening.py`, `tests/test_host_runner_redaction.py`; `d0lg63`: `tests/test_packaging_distribution.py`), each matching its declared `- Scope-Paths:`; no `.spec.md` was changed and `docs/security.md` is declared by `gqyold`; neither carries `- Blocks-Release:`; both carry `- From-Backlog: mflqqf`, and backlog `mflqqf` reads `- Status: open` (not closed on one carrier's evidence); both children's evidence records `git status --short` empty after their test runs. Each check below therefore holds; the original wording is kept for the record.

- [Measured 2026-10-07: holds; owner: gqyold and d0lg63, both executed] THE TWO CHILDREN'S DECLARED PATH SETS ARE DISJOINT, which is what makes them independently approvable and parallel-safe. Child 01 declares `tests/test_security_hardening.py`, `tests/test_host_runner_redaction.py`, `agent_workflows/security_hardening.py` and `docs/security.md`; child 02 declares `tests/test_packaging_distribution.py` alone. No path appears in both. Verify this against the files on disk rather than against this table.
- [Measured 2026-10-07: holds; owner: gqyold and d0lg63, both executed] NEITHER CHILD DECLARES A RELEASE GATE, AND THAT IS CORRECT RATHER THAN AN OMISSION. Backlog item `mflqqf` carries no `- Blocks-Release:`, and the repository's release-gating work-kind set is `bug` alone, so a `security` item is not auto-gated and the children must NOT invent a gate. Confirm no child acquired one.
- [Measured 2026-10-07: holds; owner: gqyold and d0lg63, both executed] BOTH CHILDREN CARRY `- From-Backlog: mflqqf`, so the graduation handoff is machine-readable from either. CONFIRM THE ITEM IS NOT CLOSED BY EITHER CHILD ALONE: the item has TWO carriers, so a close on one carrier's evidence would drop the other half. (Review 2026-10-07, a state note and not work of this Set: the item currently reads `- Status: open`, because the 2026-10-06 coverage demotion of this plan reopened it; its own history line names the remedy, which is a backlog-tier act by the graduation verb and is performed by no plan in this Set.)
- [Measured 2026-10-07: holds; owner: gqyold and d0lg63, both executed] THE BASELINE DISCIPLINE IS IDENTICAL IN BOTH CHILDREN AND MUST STAY SO. Both set the bar at "no newly failing test" with a mandatory isolated re-run, both forbid reporting green by exclusion, and both forbid comparing against any count written in a plan. If one child is revised to claim a green baseline, that is drift and must be caught here.
- [Measured 2026-10-07: holds; owner: gqyold and d0lg63, both executed] NO SPEC IS AMENDED BY EITHER CHILD and no `.spec.md` appears in either `- Scope-Paths:`. Child 01 does amend a DOCUMENT (`docs/security.md`) and declares it; confirm the declaration is still present, since an undeclared spec or doc edit is what the finalize scope gate exists to catch.
- [Measured 2026-10-07: holds; owner: gqyold and d0lg63, both executed] THE ONE SHARED TEST-METHOD RULE: no test in either child may write into the repository tree. Both children require every filesystem input and every built distribution to live under `tmp_path` or `tempfile`, and both require `git status --short` empty after their runs. Confirm both children's evidence shows it.

## Deferred / out of scope (with reason)

- Wiring any boundary checker into `aw check`, a pre-commit hook, or a release gate is out of scope for the whole Set. Six of the seven checkers have no production caller at all, which child 01 measures; giving them one is a wiring decision with its own design question (what refuses, where, and with what operator message), not test restoration.
  - Carrier-Declined: NOT AN OBLIGATION THIS SET CREATES. Item `mflqqf` asks for coverage of the shipped boundaries, not for them to be enforced anywhere new, so a carrier here would invent scope the item never had. The checkers' lack of callers is MEASURED and recorded by child 01's F-09, so the fact is durable even though no obligation is filed.
- The `RedactionPolicy` CASE-SENSITIVE sensitive-key match is recorded by child 01 with a reproducing probe and left unfixed, because it lives in `agent_workflows/run_ledger_store.py`, which neither child declares, and changing a shared redaction policy's matching is a behavior change for every ledger caller.
  - Carrier: go20fk
- The `host_runner.redact_worker_output` masking gap is PINNED BY A TEST, NOT FIXED, for a reason worth stating at Set level: the current behavior may be CORRECT (the `BoundaryResult` is the fail-closed signal and the module DOCSTRING is the thing that overclaims), so the carrier states BOTH remedies and asks which rather than asserting a defect. Child 01 makes the behavior observable so the decision rests on a measurement.
  - Carrier: fe6aro
- The deleted `tests/test_run_analytics_packaging.py` performance-baseline arms are not restored. They measure scan latency, peak heap, report size and telemetry overhead, which are benchmarks rather than boundaries, and item `mflqqf` is about the security checkers and the packaging boundary.
  - Carrier-Declined: Not a gap this item owns, so no obligation outlives the Set. A latency baseline is neither a security boundary nor a packaging boundary, and filing a carrier would assert an obligation item `mflqqf` never created. A reviewer who wants the benchmarks restored should file that on its own evidence.
- The two properties `tests/test_packaging.py` already covers are deliberately not re-asserted, which is child 02's central scope decision and follows from the item's packaging measurement being stale.
  - Carrier-Declined: NOTHING IS OUTSTANDING. Both properties are asserted by a committed test (`tests/test_packaging.py`, restored by `2edb9ff8e`), so this row records a declined duplication rather than undone work.
- The two UNFILED load-sensitive suite failures found while baselining (`test_verbose_flag_reach`, `test_typecheck_gate`) are not fixed by this Set, but they are no longer unfiled: the measurement is immortalized with its triage question rather than left in plan prose, because a baseline observation that lives only inside an executed plan vanishes from `aw attention` the moment the plan closes. Both children still instruct the executor to re-measure and report rather than accept a green expectation.
  - Carrier: wc5c5e

## Scope check

- Over-scope: none. This plan declares only its own file and performs no product change. Each child's scope is bounded by its numbered items, and the Set adds exactly the coverage the item's two measurements call for, minus the half that was already restored.
- Under-scope: Deliberate and named above. No checker gains a production caller, the `RedactionPolicy` defect and the `redact_worker_output` masking gap are recorded rather than fixed, the benchmark arms stay out, and the two already-covered packaging properties are not duplicated. A reviewer who wants any of these in scope should say so before approval, since each would change a child's declared `- Scope-Paths:`.
- THIS ORCHESTRATOR CARRIES NO WORK OF ITS OWN, which is the property the runner's coverage gate checks. Both E-items are confirmations of a child plus cross-child property checks; every deliverable in this Set is owned by a child. There is no baseline to establish before a child runs and no record to reconcile afterwards that is not a child's own finalize.

## Required tests / validation

This plan runs no test itself. Both children are executed, and the inspection of what they produced was performed on 2026-10-07 and is recorded under Cross-IPD validation; what follows is the original description of that inspection, a REVIEW of pasted child evidence and not a re-run of it.

[Owner: gqyold and d0lg63, each in its own V-items; both executed] The Set-wide bar is "NO NEWLY FAILING TEST" measured against each executor's own execution-base baseline, never "green", because the base was measured red at authoring with two unfiled load-sensitive nodes. Every red node in any child's run must have an isolated re-run pasted and a classification. A child that reports green by excluding a node has not satisfied its own contract and must not be accepted here.

## Open questions

### OQ-01: Should the two children execute in sequence or may they run in parallel?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE DECLARED PATHS: they may run in PARALLEL, and neither child declares an `- Item-Dependencies:` edge on the other. Their path sets are disjoint (child 01 takes two new test files, one source module and one document; child 02 takes one new test file), so there is no file either could contend on, and neither needs the other's result. The runner isolates each execute item in its own worktree by default and returns changes through the merge-and-revalidate gate, so even a shared path would not be the hazard it looks like; here there is not even a shared path. Not blocking: sequential execution is equally correct and costs only wall-clock time.

### OQ-02: Should backlog item `mflqqf` close `done` when both children execute, or stay open for the findings the Set records but does not fix?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, AND THE RESOLUTION CHANGED BECAUSE THE AUTHORING TURN REMOVED THE REASON TO HESITATE. The question was whether the item must stay open to own the sharp edges this Set records but does not fix. It need not: each of those findings now has its OWN durable carrier (`go20fk` for the `RedactionPolicy` case sensitivity, `fe6aro` for the `redact_worker_output` masking overclaim, `wc5c5e` for the load-sensitive suite nodes), so closing `mflqqf` drops nothing, which was the only real risk. The item's own subject, restored coverage on the two boundary surfaces, is fully delivered by the two children. So `mflqqf` may close `done` once BOTH carriers are `executed`, and until then it stays `graduated` because a close on one carrier's evidence would drop the other half. Note the mechanical constraint that makes this safe either way: the item carries no `- Blocks-Release:` gate, so no close-legitimacy gate is at stake.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: Paste the on-disk location of child 01 proving it reached `.aw/records/plans/executed/`, and paste its V-01..V-07 `Result` lines showing none is `pending`. Paste the specific cross-child checks as OUTPUT, not as claims: the `- From-Backlog:` line from both children, the absence of a `- Blocks-Release:` line in both, and the two `- Scope-Paths:` lines side by side so a reviewer can see the sets do not intersect. Paste child 01's V-02 before-and-after pair for the prefix-confusion rows, since the whole fail-open fix rests on that failure having been observed BEFORE the fix. Confirm and state that this item changed no product file.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the on-disk location of child 02 proving it reached `.aw/records/plans/executed/`, and paste its V-01..V-06 `Result` lines showing none is `pending`. Paste at least one of its FALSIFIABILITY demonstrations in full (a perturbed expectation producing a real failure, then restored with `git status --short` empty), because every arm in that child is expected green on arrival and a passing run alone is not evidence. Paste the NON-DUPLICATION check as output: the test method names in `tests/test_packaging.py` beside those in `tests/test_packaging_distribution.py`, so a reviewer can see no property is asserted twice. State explicitly whether an sdist is now built by the suite where none was before.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; it writes no `- Readiness:` field, since that is `/plan-review`'s output and never an author's to assert. Each child required its own approval; both are now `executed`, so approving this orchestrator authorizes only its two confirmation items.

EXECUTION CONTRACT. This plan performs ORCHESTRATION ONLY and touches no product file: both E-items are confirmations of a child plus the cross-child property checks above. Commit only the one declared `- Scope-Paths:` entry and only through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`; do not push; do not create a tag or release. Do not perform, re-run, or re-validate a child's work here: if a child's evidence is missing or its `Result` is `pending`, this plan's item is `blocked` and the child must be run, not patched over. UNDER A RUNNER THIS PLAN IS NOT AGENT-EXECUTED: `aw oc run` and `aw agy run` retire an orchestrator once every child of the Set is `executed` on disk, spending no agent turn, so its presence in a queue is correct and needs no human step.

SCOPE FENCE. The declared `- Scope-Paths:` is this plan's own file. If a cross-child check reveals a genuine inconsistency, REPORT it rather than fixing it here; correcting a child's content from the orchestrator would edit a path this plan does not declare and would hide the drift the check exists to surface.

POST-GATE LIFECYCLE MOVE. The finalize obligation is unconditional: this plan does not reach `.aw/records/plans/executed/` until both `V-*` items carry pasted evidence with a non-pending `Result`, every completion criterion above is met, and `aw ipd lint --phase pre-transition` reports conforming. OWNERSHIP IS CONDITIONAL: under `aw oc run` or `aw agy run` the RUNNER performs the retirement; by hand outside a runner the executor performs it via `aw ipd finalize`. Never hand-edit the status line and never hand-move the file. THIS SET IS THE GRADUATION CARRIER FOR BACKLOG ITEM `mflqqf` ACROSS TWO CHILDREN, so neither child closes the item alone. The item currently reads `- Status: open` (reopened by the 2026-10-06 coverage demotion), and re-graduating or closing it is a backlog-tier act outside this Set; with both carriers already `executed`, the item may close `done` per OQ-02's resolution, since each recorded-but-unfixed finding has its own carrier (`go20fk`, `fe6aro`, `wc5c5e`).
