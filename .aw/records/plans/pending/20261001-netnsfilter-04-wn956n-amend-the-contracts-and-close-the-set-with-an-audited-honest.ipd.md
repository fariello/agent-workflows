# IPD: Amend the contracts and close the Set with an audited honest capability report

- Date: 2026-10-01
- Kind: child
- Concern: After child 03 the repository can do something its contracts say it cannot: `host_sandbox_profile`'s module docstring states "Network scoping and container isolation are out of scope here", and spec `25kzda` 5.2 records that for the push-denial requirement "the honest answer for every host today is NO". Leaving those standing would make the contracts wrong in the direction of understating, which is safe but misleading. Amending them is the dangerous half: this area's entire history is of contracts written more generously than the mechanism warranted (`RUN-NO-PUSH` retired by `4h7tt0`, `supports_deny_push` removed by `01reg8`).
- Scope: Amend spec `25kzda` 5.2, `host_sandbox_profile`'s module docstring, and the operator documentation for the hardened profile to state exactly what the Set proved and what it did not, and AUDIT the end state for overclaim by running commands rather than reading plans. Records, documentation and verification only; no product behavior changes.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/host_sandbox_profile.py, docs/runner-profiles.md, CHANGELOG.md
- Item-Dependencies: executed:2j4pd0
- Status: draft
- From-Backlog: sv9ce4
- From-Spec: 25kzda
- Work-Kind: feature
- Priority: low
- Set: netnsfilter
- Order: 4
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wn956n

## Workflow history
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Bare pytest run green with actual summary line pasted

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored review-ready while graduating backlog `sv9ce4`. The audit's search terms are FIXED here with their authoring-time counts measured, because the sibling Set's review found that an unnamed grep lets an executor pick the narrowest term and pass honestly.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Leave the repository stating the truth about what it can now enforce: the contracts describe a probed,
per-host, destination-granular egress boundary with its limits named, and nothing anywhere claims a
universal push boundary the mechanism does not deliver.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: amend the contracts

- [ ] E-01 Amend `host_sandbox_profile`'s module docstring, which is the published-guarantees contract. Three changes: correct the sentence "Network scoping and container isolation are out of scope here", which the Set makes false; add the new capability to the runner-safety bullet list stating it is PROBED by attempt and two-sided; and state its limits in the same bullet, namely that it filters by DESTINATION against a declared allow list rather than denying push universally, that an allow-listed host remains reachable for any purpose, that it is Linux-only and opt-in, and that it gates no action. Also correct any prose that counts the runner-safety fields, since the count changes.
  - WRITE THE LIMITS INTO THE SAME BULLET AS THE CLAIM, not into a separate paragraph. The failure mode this guards against is a reader taking the claim and missing the qualification, and the module already demonstrates the pattern that works: the `supports_commit_gateway` bullet states the capability and its forbidden inference together.
  - Depends on: none
  - Expected outcome: The contract describes the new capability, what it proves, and what it does not, with the field-count prose corrected.
  - Execution state: pending

- [ ] E-02 Amend spec `25kzda` 5.2 to record that the push-denial requirement now has a PARTIAL and probed answer, replacing the standing claim that "the honest answer for every host today is NO" with what is now measurable, and stating precisely what remains unmet. PRESERVE the requirement bullet "deny push-capable network routes and withhold remote credentials" byte-for-byte: the network half is now partly answerable and the CREDENTIAL half is not addressed by this Set at all, so the bullet still describes unfinished work. Append a `## Workflow history` record with `aw specs note` naming this plan and the Set.
  - DO NOT AMEND Section 6.1's limit 4 ("No-push and hook guarantees require control of execution"). It says the design REQUIRES the engine to own process launch and deny push-capable network, and that remains an accurate statement of a requirement; editing an honest-limits entry to mention a partial boundary would be the overclaim this plan exists to catch. E-04 records a judgement on it instead.
  - DO NOT AMEND guarantee row 1 ("An actual push attempt aborts the run") TO CLAIM IT IS NOW IN FORCE. Nothing in this Set aborts a run on a push attempt: the boundary refuses a ROUTE, no finding code was added, and `run_evidence.validate_finding_table` still requires exactly 12 codes. The row may be amended only to state more precisely what is and is not enforced, never to assert the abort exists.
  - Depends on: E-01
  - Expected outcome: 5.2 states the first probed answer, its granularity, and the remaining gap, with the requirement bullet unchanged and no guarantee row upgraded.
  - Execution state: pending

- [ ] E-03 Update the operator documentation for the hardened profile in `docs/runner-profiles.md` to describe the egress boundary as an operator actually meets it: that it is OPT-IN through the profile and has no CLI flag, Linux-only, applied by the OpenCode host only, requires a declared allow list and REFUSES to start without one, and that requesting hardened on a host whose probe reports False fails closed rather than running unfiltered. Add a CHANGELOG entry for the one user-visible change, written in user-facing prose with no em or en dashes.
  - NAME THE OPENCODE-ONLY BOUND EXPLICITLY. `agy_runipd` applies no execution profile at all, so an operator running Antigravity gets no boundary from this work. Documentation that implies otherwise would be the worst kind of overclaim here, because an operator would rely on it.
  - Depends on: E-02
  - Expected outcome: An operator can tell from the documentation which runs are protected, which are not, and what they must declare for the boundary to start at all.
  - Execution state: pending

### Task group 2: audit the end state

- [ ] E-04 Audit the Set's end state for overclaim, treating it as a FALSIFICATION exercise and verifying by RUNNING commands rather than reading the plans. Check: (a) `aw host capabilities opencode` names the new capability with a note stating its limits and contains no `deny_push`; (b) `run_evidence.validate_finding_table()` still reports valid with exactly 12 codes; (c) `ACTION_CLASSES` is still `(ACTION_READ_ONLY,)` and `RUNNER_ACTION_TO_CONTRACT_ACTION` is still empty, so nothing is gated; (d) grep the spec, the module docstring and the operator documentation for sentences asserting push denial as an AVAILABLE guarantee, and judge every hit.
  - SUB-CHECK (d) MUST USE THESE FIXED TERMS, each count stated: `deny push-capable`, `push denial`, `no-push`, `deny_push`, and bare `push`. The terms are fixed here because an unnamed grep lets an executor choose the audit's own thoroughness and the cheapest choice is the narrowest; the sibling Set's review found exactly that. MEASURED AT AUTHORING on the spec: `deny push-capable` 2, `push denial` 3, `no-push` 2, `deny_push` 6, bare `push` 23. These are LIVE counts that drift as the spec is amended, including by this very plan, so RE-DERIVE them at execution and treat the figures here as context, not as the bar. Judge every hit of the first four; the bare-`push` run is a completeness sweep whose purpose is to surface a sentence the others miss, so state its count and judge only hits not already covered.
  - JUDGE BOTH OF THE SPEC'S PUSH-DENIAL SITES BY NAME, since they are not equivalent. The FIRST is 5.2's requirement bullet, which E-02 leaves byte-unchanged. The SECOND is Section 6.1 limit 4, whose body says the design "requires the engine to own process launch, deny push-capable network/credentials, own commits, and record the commit gateway". THE REQUIRED JUDGEMENT ON LIMIT 4 IS "requirement/limit, acceptable, not an available-guarantee claim", with the resolution DO-NOT-AMEND. An audit reporting ONE `deny push-capable` hit has missed a site and has not met this item.
  - Depends on: E-03
  - Expected outcome: Either a clean audit with pasted evidence per sub-check, or a NAMED overclaim to fix before the Set closes. A hit in (d) is a finding to resolve, not a note to file.
  - Execution state: pending

- [ ] E-05 Run the full validation sweep and record the Set's honest outcome in plain language: what it DID deliver (a probed per-host capability, a destination allow list, a parent-owned broker, a non-evadable confinement for opt-in hardened runs on one host) and what it did NOT (push denial, credential withholding, any gated action, any finding code, any coverage of Antigravity or non-Linux hosts). Run the bare suite, `aw ipd lint` over every plan in the Set, `aw check`, `aw sanitize --agent`, and `aw host capabilities opencode`.
  - TWO OF THESE GATES EXIT NONZERO ON THIS REPOSITORY TODAY, so "all checks pass" is NOT the bar and must not be used as one. `aw check` and `aw research index --check` both exit nonzero on large pre-existing populations this Set does not own, so an executor holding itself to a zero exit would either report a blocked run over someone else's backlog or quietly soften the criterion. THE CORRECT BAR IS A DELTA: capture each gate's finding count and rule breakdown before and after, and require that no NEW finding names an artifact this Set touched. `aw sanitize --agent` DOES exit zero, so for that one a nonzero exit is a genuine regression this Set introduced.
  - Depends on: E-04
  - Expected outcome: Every gate's output pasted with its exit status, the delta-judged gates showing no new finding attributable to this Set, and the Set's scope stated in one place without overclaiming.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A plan may amend a spec and MUST declare it in `Scope-Paths` (AGENTS.md), which is what makes both
  runners announce the declared spec edit before the run and reconcile it at finalize.
- Specs are amended through `aw specs note` for history rather than by hand-editing a history block,
  and a plan must never hand-write another role's attestation field.
- `ipd_lifecycle._is_implicitly_allowed` grants only `.aw/records/plans/**`,
  `.aw/records/plans/INDEX.md` and `.aw/records/**/index.md`, so `CHANGELOG.md` and
  `docs/runner-profiles.md` are NOT implicitly allowed and must be declared, which they are.
- No em or en dashes in USER-FACING prose (READMEs, CHANGELOG, operator docs). This plan writes
  exactly that kind of text in E-03, so the rule is live here rather than incidental.
- `run_evidence.validate_finding_table` hard-fails a code count other than 12 with `RC-COUNT`, so
  reintroducing a finding code is a spec amendment plus a shipped invariant change, never a row edit.
- Presence inference is forbidden in writing in `host_sandbox_profile`'s module docstring and again in
  `run_evidence`'s retirement comment, which also warns that a code bound to a presence check is
  "strictly worse than having no code at all".
- A `V-*` criterion that counts a LIVE artifact population must state the property and require
  re-derivation at execution rather than freezing an authoring-time number. This bites in E-04 and
  E-05: the grep counts and the checker populations both drift, and this plan itself changes the spec.
- Cite code by SYMBOL or quoted content string, never by a bare line number (`IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The module docstring will be FALSE after the Set, in the understating direction | It states "Network scoping and container isolation are out of scope here", and child 02 adds the policy module while child 03 wraps a worker in a namespace | E-01 must correct it. An understated contract is safe but misleads a reader about what the sandbox covers, and a future plan could duplicate the work believing it absent. |
| F-2 | Spec 5.2 currently records the honest answer as NO for every host | 5.2's preserved paragraph states "The requirement asks what a host can enforce, no host can, and the list records the gap so a future probed capability has somewhere to land" | E-02 is exactly the landing that paragraph anticipated, which is why the amendment belongs here rather than being deferred again. |
| F-3 | THE AUDIT'S OWN GREP DECIDES ITS THOROUGHNESS | Measured at authoring on the spec, hit counts vary by term: `deny push-capable` 2, `push denial` 3, `no-push` 2, `deny_push` 6, bare `push` 23 | An unnamed grep lets the executor pick the narrowest term and pass honestly. E-04 fixes all five terms and requires each count stated. The sibling Set's review found this identical defect in its own audit item. |
| F-4 | THE AUTHORING COUNTS ALREADY DRIFTED from the sibling Set's figures | The sibling plan `wzhe4n` recorded `no-push` at 7 and bare `push` at 28 on the same spec; measured at this authoring they are 2 and 23 | Direct proof these are LIVE populations. E-04 must re-derive rather than compare against any recorded number, and this plan amends the spec itself, which moves them again. |
| F-5 | The spec has TWO push-denial sites and they need different treatment | `grep -c "deny push-capable"` returns 2: 5.2's requirement bullet, and Section 6.1 limit 4 ("requires the engine to own process launch, deny push-capable network/credentials") | E-02 leaves the bullet byte-unchanged and does NOT amend limit 4; E-04 records the judgement. An audit reporting one hit has missed a site. |
| F-6 | Guarantee row 1 claims an abort nothing performs | Spec 5.2 guarantee row 1: "Tool/network/credential denial plus captured process policy. An actual push attempt aborts the run." No finding code aborts on a push attempt, and `RUN-NO-PUSH` was retired | E-02 must NOT upgrade this row. The Set refuses a ROUTE; it does not detect a push attempt or abort a run, and conflating the two is the precise overclaim `4h7tt0` retired. |
| F-7 | The boundary covers ONE host and OPT-IN runs only | `oc_runipd` records that `agy_runipd` has zero references to `execution_profile` or `host_sandbox_profile`; `_apply_execution_profile` returns argv unchanged unless `hardened` was requested, and there is deliberately no CLI flag | E-03 must name both bounds in operator-facing text, because an operator who believes every run is protected would rely on a boundary that is not there. |
| F-8 | Credentials are untouched by this Set | `runner_shared.pinned_child_env` is an `os.environ.copy()`, so a `GH_TOKEN` or forwarded `SSH_AUTH_SOCK` reaches the worker; `_hardened_credential_paths` covers FILES only and only in hardened mode | E-02 must keep 5.2's bullet intact precisely because its credential half is untouched, and E-05 must list credential withholding under what the Set did NOT deliver. |
| F-9 | An allow-listed host is reachable for ANY purpose | Research `akmzyq`, "what is NOT established": a proxy that allows a host allows everything at that host, and a model endpoint proxying arbitrary traffic would be a hole | This is the limit most likely to be dropped from a summary, and it is the one that bounds the whole claim. E-01 requires it in the capability bullet and E-04 audits for its absence. |

## Proposed changes (ordered, validatable)

1. Correct and extend the module docstring, with the limits in the same bullet as the claim (E-01).
2. Amend spec 5.2 to record the first probed answer and the remaining gap, preserving the requirement
   bullet and upgrading no guarantee row (E-02).
3. Document the boundary for operators with its opt-in, Linux-only and OpenCode-only bounds, and add
   the CHANGELOG entry (E-03).
4. Audit the end state for overclaim by running commands, with five fixed search terms and both spec
   sites judged (E-04).
5. Run the full sweep, judging the pre-existing-finding gates by delta, and state delivered versus
   undelivered scope in one place (E-05).

## Deferred / out of scope (with reason)

- AMENDING Section 6.1 limit 4. It states a REQUIREMENT the design has, which this Set confirms rather
  than changes.
  - Carrier-Declined: NOT WANTED. Editing an accurate honest-limits entry to mention a partial boundary
    would itself be the overclaim this plan exists to catch, so there is nothing owed to carry.
- REINTRODUCING a `RUN-NO-PUSH`-shaped finding code. Backlog `oq05nc`'s stated gate ("Only after such a
  probe exists may a finding code be reintroduced in 4.2") now has its factual precondition met for the
  first time, so this is a genuine open decision rather than a closed one.
  - Carrier: wcbpqf
- GATING any action on the new capability, which would require populating
  `RUNNER_ACTION_TO_CONTRACT_ACTION` and re-adding an action class.
  - Carrier: wcbpqf
- WITHHOLDING environment-carried credentials, the other half of 5.2's bullet (F-8).
  - Carrier: sv9ce4
- CLOSING backlog `sv9ce4` as `done`. Not this plan's to do and not correct: the runner sets
  `graduated`, which is accurate while the mechanism is built for one host and opt-in runs.
  - Carrier-Declined: Out of scope by construction; the status transition is the runner's.

## Scope check

- Over-scope: none. The spec is amended by E-02, the module docstring by E-01,
  `docs/runner-profiles.md` and `CHANGELOG.md` by E-03. E-04 and E-05 write only this plan's own
  evidence blocks, which the lifecycle allows implicitly.
- Under-scope: none, and ONE ABSENCE IS DELIBERATE. No test path is declared, because this plan adds no
  test: E-04 READS shipped behavior by running commands rather than editing code, and the behavioral
  coverage for the mechanism belongs to the children that built it. If the audit finds a real
  overclaim, the fix is a corrective plan rather than an in-scope edit here, which V-04 requires.

## Required tests / validation

- Run the suite BARE as `python3 -m pytest` and paste the actual summary line. No product behavior
  changes here, so the expectation is unchanged counts; the run establishes the Set's end state green.
- `aw ipd lint` reports conforming over all five plans in Set `netnsfilter`.
- `aw check` reports NO NEW violations, judged as a DELTA and not by exit code, with counts re-derived
  at execution because the population drifts with every plan authored in the repository.
- `aw sanitize --agent` exits zero. It does today, so a nonzero exit is a regression this Set caused,
  and this plan pastes command output including greps, which is a realistic leak vector.
- `aw host capabilities opencode` run and its ACTUAL output pasted, showing the capability and note.

## Spec / documentation sync

- Spec `25kzda` is AMENDED (declared in `Scope-Paths`) in Section 5.2, recording that the network half
  of the push-denial requirement now has a probed partial answer, naming its granularity and its
  limits. WHY this belongs in the same change as the Set: 5.2 requires descriptor entries be "backed by
  positive and fail-closed probe evidence" and states that "`supported` without current evidence is not
  sufficient", so adding the first probed entry for this requirement changes what the contract can
  claim. Leaving the spec silent would leave the next reader unable to tell a probed row from a
  declared one, which is the ambiguity that produced backlog `oq05nc`.
- `host_sandbox_profile`'s module docstring is the published-guarantees contract and is amended by
  E-01, including the sentence scoping network isolation out and the runner-safety field count.
- `docs/runner-profiles.md` is amended by E-03, which is where an operator meets the hardened profile.
- `CHANGELOG.md` gets one entry for the user-visible change, in user-facing prose with no em or en
  dashes. Declared in `Scope-Paths` because the lifecycle does not implicitly allow it.

## Open questions

### OQ-01: Should spec 5.2's single bullet be SPLIT into its network and credential halves?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wcbpqf
- Resolution or deferral rationale: OPEN and left to the maintainer, non-blocking because E-02 preserves
  the bullet byte-for-byte either way. The tension is now sharper than when the sibling Set raised the
  same question: after this Set the two halves are in genuinely different states, with the network half
  partly answerable by probe and the credential half untouched for environment-carried tokens (F-8). A
  single bullet therefore describes one requirement whose halves have different answers, which is
  precisely when a reader draws the wrong conclusion about whichever half they care about. Splitting is
  not obviously right either: the halves are complementary in practice, since a route denied without
  credentials withheld and credentials withheld without a route denied are both incomplete, and
  splitting invites one half to be marked satisfied while the other is forgotten. Carried by `wcbpqf`,
  which already holds this area's maintainer decisions including the identical question from the
  sibling Set, so the two can be settled once.

### OQ-02: Should the CHANGELOG entry describe this as a security boundary or as an opt-in capability?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: as an OPT-IN capability, naming its bounds, not as a
  security boundary. The deciding consideration is who reads a CHANGELOG and what they do with it: an
  operator reading "egress filtering boundary" in a release note may conclude their existing runs are
  now protected, and they are not, because the mechanism applies only to runs that opted into
  `hardened` on the OpenCode host on Linux (F-7). A CHANGELOG line is also the artifact most likely to
  be quoted without its qualifications, so the qualification has to be inside the sentence rather than
  nearby. The entry should say what became available and what an operator must do to get it, which is
  both accurate and more useful than a claim.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `git diff` of the module docstring showing the corrected out-of-scope sentence, the new capability bullet, and the corrected field-count prose. Quote the new bullet verbatim.
  - THE BULLET MUST CARRY ALL FOUR LIMITS or this item FAILS: destination-granular against a declared allow list rather than universal push denial; an allow-listed host reachable for any purpose; Linux-only and opt-in; gates no action. A diff adding the claim without the limits is the exact overclaim this plan exists to prevent, and it is the most likely way this plan fails while looking complete.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff` of the spec showing the amended 5.2 narrative, plus the tail of its `## Workflow history` showing the new dated record naming `wn956n`. A grep must show the requirement bullet "deny push-capable network routes and withhold remote credentials" is BYTE-UNCHANGED.
  - PROVE THE TWO NEGATIVE CONSTRAINTS HELD. Paste a diff or grep showing Section 6.1 limit 4 is unmodified, and showing guarantee row 1 was NOT upgraded to assert that a push attempt now aborts the run. Nothing in this Set aborts a run on a push attempt (F-6), so such an upgrade would assert a mechanism that does not exist; if row 1 was touched at all, quote the before and after and justify that it states the enforcement more precisely rather than claiming more.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff` of `docs/runner-profiles.md` and `CHANGELOG.md`. The documentation must state all of: opt-in through the profile with no CLI flag, Linux-only, OpenCode-only, requires a declared allow list and refuses without one, and fails closed on a host whose probe reports False. Quote the CHANGELOG entry verbatim.
  - CONFIRM THE USER-FACING PROSE RULE. State that neither diff introduces an em or en dash, and paste the check used. Both files are user-facing text, where the execution contract forbids them.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Four pasted command outputs, one per sub-check: (a) `aw host capabilities opencode` showing the capability, its note, and no `deny_push`; (b) a `python3 -c` printing `run_evidence.validate_finding_table()` and `len(run_finding_codes())` equal to 12, pasting the returned object rather than paraphrasing "valid"; (c) a `python3 -c` printing `ACTION_CLASSES` and `RUNNER_ACTION_TO_CONTRACT_ACTION`, proving nothing is gated; (d) the five fixed greps with every hit and its surrounding sentence, plus an explicit judgement on each stating whether it describes an AVAILABLE GUARANTEE (a defect to fix) or a requirement, history or limit (acceptable).
  - PASTE ALL FIVE TERM COUNTS AND NAME LIMIT 4 EXPLICITLY. The terms are `deny push-capable`, `push denial`, `no-push`, `deny_push` and bare `push`. RE-DERIVE every count rather than copying F-3's figures, which are authoring-time and which this plan's own spec amendment moves; F-4 records them already drifting from the sibling Set's numbers on the same file. The evidence must contain the words Section 6.1 limit 4 with the judgement "requirement/limit, acceptable, not an available-guarantee claim". AN AUDIT REPORTING ONE `deny push-capable` HIT FAILS THIS ITEM, since there are two sites.
  - AN EMPTY GREP WITH NO JUDGEMENT RECORDED FAILS THIS ITEM, because the check is the judgement and not the absence. If a real overclaim is found, it is a finding to FIX with a corrective plan, not a note to file, and it must be reported as a human decision point.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted actual output of `python3 -m pytest` (the summary line), `aw ipd lint` over the Set, `aw check`, `aw sanitize --agent`, and `aw host capabilities opencode`, each with its exit status. Plus the written statement of delivered versus undelivered scope.
  - THE STATEMENT MUST EXPLICITLY DENY FIVE THINGS, or this item FAILS: that push denial is enforced; that credentials are withheld beyond the existing hardened file paths; that any action is gated; that any finding code was added; and that Antigravity or non-Linux hosts are covered. A statement claiming the Set delivered push denial FAILS this item outright.
  - DO NOT REPORT "all checks pass": `aw check` cannot. Paste its finding COUNT and rule breakdown and assert the DELTA, namely no new finding naming any artifact this Set touched, with counts re-derived at execution rather than compared to a recorded number. A pasted zero-exit claim for `aw check` is evidence the command was not run. `aw sanitize --agent` MUST exit 0, since it does today.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is the Set's honesty gate, and it is the one most likely to fail by being too generous rather
than too strict. Its two jobs are to make the contracts true and to check by RUNNING things that
nothing shipped claims a boundary that does not exist. Both exist because this repository has made the
opposite mistake twice in this exact area: `RUN-NO-PUSH` promised that preflight had proved push
denial while nothing enforced it, and `supports_deny_push` was declared and never probed.

WHAT A REVIEWER SHOULD PUSH HARDEST ON. First, V-01's four limits: a capability bullet that states the
claim and drops the qualifications is how an honest mechanism becomes a misleading contract, and it is
a one-sentence mistake. Second, V-02's two negative constraints, especially guarantee row 1: the Set
refuses a ROUTE and does not detect a push attempt or abort a run, so upgrading that row would assert
a mechanism nothing implements (F-6). Third, that E-04's counts are RE-DERIVED and not copied, which
F-4 demonstrates is a live risk by showing the sibling Set's figures on the same file already stale.
Fourth, that an audit plan can only fail in one way, by running a check too narrow to find anything
and reporting the clean result honestly, which is why the terms are fixed and why an empty grep with no
recorded judgement is a failure rather than a pass.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`,
never `git add -A`, and never push. This is a SHARED CHECKOUT: verify the staged set with
`git diff --cached --name-only` before committing, unstage anything that is not yours with
`git restore --staged <path>`, and re-verify after any failed raw commit attempt. Run the suite BARE
as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE; a summary you did not produce is not
evidence, and the same hard-MUST governs every pasted gate output, grep count, and exit status these
`V-*` items demand. Paste skips explicitly rather than letting a green line hide one.

SPEC EDIT DECLARED so the runner can announce and reconcile it: this plan amends an APPROVED spec,
which is the highest-leverage change a run can make, and the reason is recorded in the spec-sync
section above. If the audit finds a real overclaim, fix it with a corrective plan rather than
annotating it, and report it: an overclaim the Set shipped is a genuine human decision point, unlike
the routine finalize answers.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence.
Reaching `executed/` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` /
`aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize`
yourself in a runner-driven execution; a HAND execution invokes it
(`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit
`- Status:` and never hand-roll a `git mv` into `executed/`. This plan must NOT set backlog `sv9ce4`
to `done`; the runner sets `graduated`.
