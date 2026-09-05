# IPD: let the verifier turn resolve its own profile

- Date: 2026-09-05
- Kind: child
- Concern: THE VERIFIER TURN IS FORCED TO REUSE THE EXECUTOR'S MODEL, and the `runprofile` Set makes that a rule rather than an accident. `3cm15q` E-04 requires "every normal execution, recovery execution, review, and independent fresh-session verifier appends `--model` and `--variant` from the frozen state", and its findings table lists "Profile only affects first turn" as a defect to PREVENT, so one frozen model identity covers every turn. That is right for reproducibility and wrong for the maintainer's actual workflow: the point of an independent skeptical verifier is that it is INDEPENDENT, and a second opinion from the same model is the one opinion least likely to catch what the first missed. The maintainer's stated need (2026-09-05) is per-model routing: have a cheaper/faster model execute and a stronger model verify, or have a strong model execute and skip verification entirely because it was measured to require no material corrections. Neither is expressible today: both turns call `run_opencode` (`oc_runipd.py:4808` execute, `:4994` verifier), which reads one shared `options["model"]` (`:4158-4159`), and `verifier_model`/`validator_model`/per-role model routing all grep to ZERO across the package.
- Scope: Let the VERIFIER turn resolve its own launch profile instead of inheriting the executor's, defaulting to "same as the executor" so no existing invocation changes. Adds an optional `verify_with` profile reference to the `runner_profiles` schema, resolves it once at run creation, freezes it into durable state beside the executor's resolution, and uses it for the verifier turn's argv only. EXCLUDES cross-HOST verification (executing under one runner and verifying under another), which is deliberately deferred per the maintainer's 2026-09-05 decision and recorded in OQ-01 with the measured reason it is smaller than it looks; excludes any change to what the verifier turn DOES or how its result is judged; excludes the `validate` tri-state precedence chain (`f2mrsw` E-03 owns it) and the bypass-flag conformance question (`ki6tom`).
- Scope-Paths: agent_workflows/runner_profiles.py, agent_workflows/oc_runipd.py, tests/test_runner_profiles.py, tests/test_oc_runipd.py
- Item-Dependencies: executed:3cm15q
- Status: to-review
- Set: runprofile
- Order: 6
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: kgpptv
- Blocks-Release: next

## Workflow history

- 2026-09-05 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after a discussion that started from `ki6tom` (the spec-2.1 bypass-flag conformance plan) and turned out to be about a missing capability rather than a wording question. THE CHAIN, recorded because it explains why this plan exists at Order 6 of an already-approved Set: `ki6tom` proposes deleting `--no-verify` and `--dangerous` to satisfy spec `25kzda`'s flat prohibition; the maintainer's response was that `--dangerous` is OPERATIONALLY REQUIRED on agy (without it that host stalls on permission prompts nearly always and gets killed) and that verification should depend on WHICH MODEL did the work, since Opus was measured needing 0% material corrections after validation while a cheaper model plausibly benefits from a stronger checker. So `--no-verify` is the crude form of a routing decision, and deleting it before the routing exists would remove the only control available. SEARCHED FIRST rather than assuming net-new (`aw search " gem " --files`): the `runprofile` Set already builds the alias domain the maintainer remembered, and it already carries two of the three needed pieces. `f2mrsw` E-01 defines schema v1 `{schema_version, default_runner, defaults, profiles}` where a profile BINDS A RUNNER plus `model`/`variant`/`agent`, and E-03 already resolves an optional per-profile `validate` tri-state through an explicit precedence chain (CLI flag > profile > defaults > shipped), both added at review at the maintainer's own direction. `ygzq71` builds a host ADAPTER REGISTRY. THE ONE GAP, measured across all six plans: `verifier (model|profile|runner)` and equivalents grep to ZERO, so nothing gives the verifier its own identity. ONE CORRECTION TO MY OWN EARLIER ASSESSMENT, recorded so the bad reasoning is not reused: I told the maintainer cross-host verification was "a much bigger lift" on the assumption that the two hosts kept incompatible run state. That is FALSE at HEAD `4763eb8d`: both runners import 29 symbols from `runner_shared` including `save_state` and `state_root` (the `818uru` extraction), so the state format is already shared. What is genuinely per-host is the verifier turn itself (`runner_shared` contains ZERO verifier logic; each host builds its own prompt at `oc_runipd.py:3735` and `agy_runipd.py:2037`) plus one known unfinished seam, `save_state`'s `write_report` marked `(DIVERGED)` at `runner_shared.py:56`. That is an adapter-shaped problem, which is what `ygzq71` already builds, so cross-host is deferred by CHOICE (OQ-01) and not because it is expensive.

## Goal

Let a run execute with one model and verify with another, so the independent verifier can be genuinely independent, without changing any existing invocation's behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: schema and resolution

- [ ] E-01 Add an OPTIONAL `verify_with` profile reference to the `runner_profiles` schema (`f2mrsw` E-01's version 1 object), on a profile and on the top-level `defaults`, and resolve it deterministically.
  IT IS A PROFILE REFERENCE, NOT AN INLINE MODEL. Storing a bare model string here would fork the one place a launch identity is defined and let a verifier launch bypass the schema's own validation (`f2mrsw` forbids arbitrary argv, environment, executable, prompt, permission, token and API-key fields, and an inline verifier model would be the first field to escape that). A reference reuses the whole validated profile, including its `agent` and `variant`.
  ABSENT MEANS "SAME AS THE EXECUTOR", and that is the entire backward-compatibility story: every profile written before this change, and every run started without one, resolves the verifier to the executor's own frozen launch and behaves exactly as it does today. Use the SAME tri-state discipline `f2mrsw` E-03 already mandates for `validate`: absent at one level falls through to the next, and absent overall is NOT an error and NOT a null model.
  FOLLOW THE PRECEDENCE CHAIN THAT ALREADY EXISTS rather than inventing a second one: profile's own `verify_with` > `defaults.verify_with` > same-as-executor. Do NOT add a CLI flag in this item (E-02 owns that) and do NOT reorder the existing `validate` chain.
  REFUSE A SELF-REFERENCE OR A CYCLE explicitly (`gem` verifying with `gem` is harmless but `verify_with` pointing at a profile whose own `verify_with` points back is a resolution loop), and refuse a reference to a nonexistent profile with the same error class `f2mrsw` uses for a dangling `default_runner`.
  - Depends on: none
  - Expected outcome: the schema accepts an optional `verify_with` at both levels; resolution yields one auditable verifier launch or explicitly "same as executor"; dangling references, self-cycles, and unknown profiles are refused with typed errors; an absent value never means `false` or `null`.
  - Execution state: pending

- [ ] E-02 Freeze BOTH resolutions into durable run state at run creation, and add the CLI override.
  THE FREEZE IS THE LOAD-BEARING PART, and it is why this plan sits behind `3cm15q`: that plan's E-04 establishes that "Resume MUST NOT reload runner-profiles.json; editing, deleting, or repointing `gem` after run creation cannot alter that run." The verifier resolution inherits that rule exactly. Store it BESIDE the executor's frozen launch, never derived on demand, so a resumed verifier turn uses the model the run was created with even if the profile changed since.
  ADD `--verify-with <profile>` on `run`/`start`, and on `resume` with `default=None` so an omitted flag cannot clobber the frozen value, which is the pattern the runners already use for `--full-auto`.
  DO NOT INVENT A "NO VERIFIER MODEL" SENTINEL. Whether verification happens at all is the `validate` tri-state (`f2mrsw` E-03), a SEPARATE control; this field only says WHICH profile verifies when it does. Conflating them would give two independent switches for one behavior, which is the defect `f2mrsw` E-03's precedence chain exists to prevent.
  - Depends on: E-01
  - Expected outcome: both resolutions are frozen at creation and visible in run state; `--verify-with` parses on start and on resume with `default=None`; a resumed run uses the frozen verifier launch after the source profile is edited or deleted; `validate` and `verify_with` remain independent.
  - Execution state: pending

### Task group 2: use it, and only for the verifier turn

- [ ] E-03 Make the verifier turn's argv use the frozen VERIFIER launch while every other turn keeps the executor's.
  THE PRECISE SEAM, measured: `run_opencode` (`oc_runipd.py:4108`) builds one argv from `options` and is called by BOTH the execute turn (`:4808`) and the verifier turn (`:4994`), appending `--model` from `options["model"]` at `:4158-4159`. So the change is to let the verifier call site supply its own launch rather than reading the shared one. Keep ONE argv builder: a second builder for the verifier is how the two hosts' flag surfaces diverged in the first place.
  ONLY THE INDEPENDENT FRESH-SESSION VERIFIER CHANGES. `3cm15q` E-04 names four turn kinds (normal execution, recovery execution, review, verifier); the first three keep the executor's frozen model, and a plan review turn is NOT a verifier turn even though both are read-mostly. Prove that distinction in tests rather than assuming the call sites are obvious.
  MIND THE SESSION AND WORKTREE COUPLING: the verifier already forces a fresh session and, when isolated, runs in the WORKTREE (`oc_runipd.py:3004` region on agy, and the oc equivalent), so changing the model must not disturb which directory the turn runs in or whether the session is fresh. A model swap that silently reused the executor's session would destroy the independence this plan exists to create.
  - Depends on: E-02
  - Expected outcome: the verifier turn's argv carries the verifier launch's model/variant/agent; execution, recovery, and review turns carry the executor's; one argv builder serves all; fresh-session and worktree behavior is unchanged.
  - Execution state: pending

- [ ] E-04 Prove the end-to-end routing and the no-op default, and record the honest limit.
  TWO CASES ARE LOAD-BEARING AND ONE IS EASY TO FAKE. (a) A profile with `verify_with` produces DIFFERENT models in the execute and verifier argv, shown side by side from one run. (b) A profile WITHOUT it produces IDENTICAL argv to today, which is the backward-compatibility claim and the one a reviewer should distrust most, because a test that only checks case (a) would pass while every existing user's runs changed.
  STATE THE LIMIT PLAINLY IN THE PLAN'S OWN REPORT: this delivers cross-MODEL verification on ONE host. Cross-HOST (execute under agy, verify under oc) is NOT delivered, is deferred by choice, and is recorded in OQ-01 with its measured cost. Do not describe this as "verify with any runner".
  - Depends on: E-03
  - Expected outcome: differing execute/verifier models demonstrated from one run; an unset `verify_with` demonstrated byte-identical to current behavior; the cross-host limit stated rather than implied.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A PROFILE ALREADY BINDS A RUNNER. `f2mrsw` schema v1 is `{schema_version, default_runner, defaults, profiles}` with each profile carrying `runner` plus required `model` and optional `variant`/`agent`. So `gem` -> agy and `opus` -> oc is the EXISTING design, not something this plan adds; the maintainer's intuition about the alias JSON carrying the runner was already correct.
- THE `validate` TRI-STATE ALREADY EXISTS, added to `f2mrsw` E-01/E-03 at review at the maintainer's direction, with an explicit precedence chain and an explicit warning that absent must not be read as `false`. This plan reuses that discipline and must not duplicate or reorder the chain.
- ONE FROZEN IDENTITY PER RUN IS AN INTENTIONAL INVARIANT (`3cm15q` E-04), not an oversight: resume must not re-resolve `runner-profiles.json`. This plan adds a SECOND frozen identity, it does not make either of them dynamic.
- `run_opencode` IS ONE ARGV BUILDER SERVING EVERY TURN (`oc_runipd.py:4108`, called at `:4808` and `:4994`). Adding fields there reaches all turn types, which is why `3cm15q`'s conventions note says "tests must prove every caller".
- THE STATE FORMAT IS ALREADY SHARED ACROSS HOSTS: both runners import 29 symbols from `runner_shared`, including `save_state` and `state_root`. The verifier TURN is not shared (zero verifier logic in `runner_shared`), and `save_state`'s `write_report` is explicitly marked `(DIVERGED)` at `runner_shared.py:56`.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | **THE VERIFIER IS REQUIRED TO REUSE THE EXECUTOR'S MODEL, BY RULE.** `3cm15q` E-04 makes every turn including the verifier append the same frozen `--model`/`--variant`, and its findings table lists "Profile only affects first turn" as a defect to prevent. So this is a deliberate invariant that must be AMENDED rather than worked around, which is why this plan also amends that plan. | `3cm15q` E-04 and its findings row "Profile only affects first turn / Happy-path execution works; verifier differs." |
| F-2 | PER-ROLE MODEL ROUTING DOES NOT EXIST ANYWHERE. `verifier_model`, `validator_model`, and role-to-model routing all grep to zero in `oc_runipd.py` and `runner_shared.py`; the only model input is `options["model"]`, appended once at `:4158-4159` for whichever turn is calling. | `grep -nE "verifier_model|validator_model|role.*model"` over both modules returns nothing; `oc_runipd.py:4158-4159` |
| F-3 | BOTH TURNS SHARE ONE LAUNCHER, which is what makes this a small change: the fix is at the CALL SITE, not a new subprocess path. | `run_opencode:4108`; execute call `:4808`; verifier call `:4994` |
| F-4 | TWO OF THE THREE PIECES ARE ALREADY PLANNED AND APPROVED, so this plan is an extension rather than a new capability: the alias/profile domain with a runner binding (`f2mrsw`) and the per-profile `validate` tri-state with its precedence chain (`f2mrsw` E-03). All six `runprofile` plans are `Status: approved`. | `f2mrsw` E-01 (schema v1, `runner` + `model`/`variant`/`agent`, optional `validate`), E-03 (precedence chain); `aw find plans --status approved` |
| F-5 | NO RUNPROFILE PLAN MENTIONS A VERIFIER MODEL: searched all six for `verifier (model|profile|runner)`, "different model", "validator model", and equivalents; zero hits in every one. So the gap is real and unowned rather than hidden in a sibling. | measured across `3m0urk`, `f2mrsw`, `p0l1to`, `3cm15q`, `ygzq71`, `p7xhhm` |
| F-6 | **CROSS-HOST IS SMALLER THAN I FIRST CLAIMED, and the correction is recorded so the wrong reason is not reused.** I told the maintainer it was "a much bigger lift" assuming incompatible per-host run state; that is false, the state format is shared via `runner_shared` (29 symbols each, including `save_state`). The genuine cost is that the verifier turn is per-host (no verifier logic in `runner_shared`; separate prompt builders) plus the `(DIVERGED)` `write_report` seam. That is adapter-shaped work, which `ygzq71` already builds. | `runner_shared.py:56` (`write_report` DIVERGED); `oc_runipd.py:3735` and `agy_runipd.py:2037` (separate `build_verifier_prompt`); `ygzq71` host adapter registry |
| F-7 | THE OPERATIONAL DRIVER IS MEASURED, NOT HYPOTHETICAL: the maintainer reports Opus required 0% material changes after validation, so verifying Opus work with Opus is spend for no observed benefit, while a cheaper executor plausibly benefits from a stronger checker. Recorded as the maintainer's measurement rather than as a repository fact, since the repo holds no such benchmark. | maintainer statement 2026-09-05; no in-repo benchmark exists to cite, which is itself worth stating |
| F-8 | THIS UNBLOCKS `ki6tom` RATHER THAN COMPETING WITH IT. `ki6tom` is blocked on OQ-01 (delete `--no-verify` or not) and cannot resolve while that flag is the only way to skip a redundant verification. Once `validate` and `verify_with` are configurable per profile, "skip verification for Opus" is configuration and the flag's removal becomes a real option instead of a capability loss. | `ki6tom` OQ-01 (`Blocking: yes`, `Status: open`); `f2mrsw` E-03 `validate` chain; this plan's E-01 |

## Proposed changes (ordered, validatable)

1. Optional `verify_with` profile reference at profile and `defaults` level, with tri-state fall-through and typed refusals for dangling/self-cyclic references (E-01).
2. Both launches frozen into run state at creation; `--verify-with` on start and on resume with `default=None` (E-02).
3. The verifier call site uses the frozen verifier launch; every other turn keeps the executor's; one argv builder (E-03).
4. End-to-end proof of differing models AND of the byte-identical no-op default, with the cross-host limit stated (E-04).

## Deferred / out of scope (with reason)

- CROSS-HOST VERIFICATION (execute under agy, verify under oc). DEFERRED BY THE MAINTAINER'S EXPLICIT 2026-09-05 CHOICE, not by cost: F-6 records that the shared state format makes it adapter-shaped work on top of `ygzq71`'s registry. Recorded in OQ-01 so the deferral carries its real reason and the earlier "much bigger lift" claim is corrected rather than inherited.
- THE `validate` TRI-STATE AND ITS PRECEDENCE CHAIN: `f2mrsw` E-01/E-03 own it. This plan's field says WHICH profile verifies, never WHETHER verification happens; E-02 forbids conflating them.
- THE BYPASS-FLAG CONFORMANCE QUESTION (`--no-verify`, `--dangerous`, spec `25kzda` 2.1's prohibition): `ki6tom` owns it. This plan makes that question answerable (F-8) and deliberately does not answer it.
- ANY CHANGE TO WHAT THE VERIFIER DOES or how its result is judged. The verifier prompt, its skeptical framing, and the deterministic completion check are untouched; only which model receives the prompt changes.
- A CLI FLAG FOR AN INLINE VERIFIER MODEL (e.g. `--verify-model gpt-x`). E-01 takes a profile REFERENCE deliberately, so an inline model would be the first field to escape the schema's validation. If it is ever wanted, it is a separate decision with its own review.
- MODEL COST OR PRICING AWARENESS. `aw oc update-models` syncs pricing, and routing by cost is an obvious follow-on, but nothing here reads price and no plan should imply it does.

## Scope check

- Over-scope: none. Every edit adds one optional schema field, freezes it, uses it at exactly one call site, or proves the result.
- Under-scope, DELIBERATE and stated plainly: this delivers cross-MODEL verification on ONE host only. A user wanting Gemini-under-agy to execute and Opus-under-oc to verify still cannot, and E-04 must say so rather than letting "verify with a different profile" imply "with a different runner".
- Under-scope: no cost or capability awareness informs the routing; the operator picks the verifier profile explicitly.

## Required tests / validation

- THE NO-OP DEFAULT IS THE LOAD-BEARING TEST: a profile without `verify_with`, and a run started with no profile at all, produce argv byte-identical to current behavior for every turn. A suite that only proves the new routing works would pass while silently changing every existing user's runs.
- Differing execute/verifier models demonstrated from ONE run, argv pasted side by side.
- Only the INDEPENDENT FRESH-SESSION VERIFIER differs: execution, recovery, and review turns still carry the executor's model, each shown explicitly (a review turn is not a verifier turn).
- Fresh-session and worktree behavior unchanged for the verifier turn; a model swap must not reuse the executor's session, which would destroy the independence being purchased.
- Resume uses the FROZEN verifier launch after the source profile is edited, repointed, and deleted (the `3cm15q` E-04 rule extended to the new field).
- `--verify-with` on start and on resume with `default=None`; an omitted flag on resume does not clobber the frozen value.
- Typed refusals: dangling reference, self-cycle, unknown profile; absent at every level resolves to same-as-executor and is NOT an error.
- `validate` and `verify_with` proven INDEPENDENT: verification off with a verifier profile set, and on with it absent.
- Full suite BARE (`python3 -m pytest`), compared against your own pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree (backlog `dh0uno`).
- `aw check all` NO-WORSENING against your own fresh baseline; do NOT claim it passes.

## Spec / documentation sync

- `3cm15q` E-04 currently requires the verifier to use the executor's frozen model. This plan AMENDS that item so it does not forbid what this enables; the amendment is recorded in `3cm15q`'s own history because it is an `approved` plan carrying human sign-off and a silent edit would erase that.
- Spec `25kzda` governs the runner surface but does NOT address per-role model routing; check whether it needs a sentence, and if so amend it with `aw specs note` rather than diverging. State the finding either way.
- The profile documentation `p0l1to` and `p7xhhm` produce must describe `verify_with`, or those plans' docs will document a schema that has since grown a field.
- `ki6tom`'s OQ-01 should be annotated to note that this plan supplies the capability its answer depends on (F-8). Annotate, do not answer it.

## Open questions

### OQ-01: Should verification be routable to a different HOST, not just a different model?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-05 by the maintainer: NOT NOW, cross-model on one host is enough for this plan, and cross-host is a later decision. Recorded rather than dropped because the maintainer explicitly asked why an earlier assessment called it "a much bigger lift" and that assessment was WRONG. The correction, so the bad reason is not reused: the two hosts already share the run-state format (29 `runner_shared` symbols each, including `save_state` and `state_root`, from the `818uru` extraction), so there is no incompatible-state problem. The genuine costs are narrower: the verifier turn is per-host (zero verifier logic in `runner_shared`; separate `build_verifier_prompt` at `oc_runipd.py:3735` and `agy_runipd.py:2037`), the verifier runs in the executor's worktree when isolated, and `save_state`'s `write_report` is an unfinished `(DIVERGED)` seam. That is adapter-shaped work on top of the registry `ygzq71` already builds, so a future plan should be scoped as "route the verifier through the host adapter", not as a runner rewrite. The maintainer's operational reason for eventually wanting it is also recorded: Gemini Flash appears to perform better under agy than under opencode, plausibly because Google trains those models heavily in Antigravity's native tool environment, though the maintainer states this as observation rather than measured evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the schema accepting `verify_with` at BOTH the profile and `defaults` levels, and the resolution result for each precedence case (profile's own, `defaults`, absent-so-same-as-executor). Paste the typed refusals for a dangling reference, a self-cycle, and an unknown profile. Prove explicitly that an ABSENT value resolves to same-as-executor and is neither an error nor a null model, since conflating absent with `false` is the exact defect `f2mrsw` E-03 warns about for `validate`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste run state showing BOTH frozen launches side by side. Paste a resume that uses the frozen verifier launch after the source profile was edited, repointed, and deleted, which is `3cm15q` E-04's rule extended to this field. Paste `--verify-with` in `--help` for start and resume, and a resume with the flag OMITTED showing the frozen value survived. Paste evidence that `validate` and `verify_with` are INDEPENDENT: verification off with a verifier profile set, and on with none.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the execute-turn argv and the verifier-turn argv from ONE run, showing different models. Then paste the recovery and REVIEW turn argv showing they carry the EXECUTOR's model, since a review turn is read-mostly like a verifier turn and is the likeliest thing to be changed by mistake. Paste evidence one argv builder still serves every turn (no second builder). Paste evidence the verifier still forces a fresh session and still runs in the worktree when isolated.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: THE BACKWARD-COMPATIBILITY PROOF FIRST, because it is the one a reviewer should distrust most: a profile WITHOUT `verify_with`, and a run with NO profile, producing argv byte-identical to pre-change behavior for every turn kind. A green suite that only exercises the new routing would pass while changing every existing user's runs. Then the differing-models demonstration. Then state the cross-host limit explicitly and confirm no report or help text implies "verify with any runner". Then the bare full suite with counts compared against your own pre-change measurement, and `aw check all` no-worsening against your own baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 4 E-leaves across 2 task groups, one concern: the verifier turn gets its own launch identity. Task group 1 is the data (schema field, then the freeze); task group 2 is the use (one call site, then the proof). E-01 and E-02 are separate because resolution is pure and the freeze touches durable run state and resume, which is where `3cm15q`'s no-re-resolution rule lives. E-03 and E-04 are separate because the call-site change is small while the proof has to cover four turn kinds plus the no-op default, and folding them would let "the new routing works" stand in for "nothing else changed".

Open questions: OQ-01 (cross-host routing) is RESOLVED as deferred, with the earlier incorrect cost assessment corrected in the record. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution. It depends on `- Item-Dependencies: executed:3cm15q`, which is not merely ordering: `3cm15q` establishes the frozen-launch mechanism and the no-re-resolution-on-resume rule that this plan extends to a second launch, and it is the plan whose E-04 this plan amends.

Scope fence: touch ONLY `agent_workflows/runner_profiles.py`, `agent_workflows/oc_runipd.py`, `tests/test_runner_profiles.py`, and `tests/test_oc_runipd.py`. Do NOT implement cross-host verification (OQ-01 defers it). Do NOT add an inline verifier model field or flag; the reference is to a PROFILE. Do NOT touch the `validate` tri-state or its precedence chain (`f2mrsw` E-03 owns it), and do NOT conflate `verify_with` with whether verification happens. Do NOT change the verifier prompt, its framing, or the deterministic completion check. Do NOT add a second argv builder. Do NOT make either frozen launch dynamic on resume. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is V-04's byte-identical no-op default, because a suite proving only the new routing would also pass if every existing run had silently changed model. Do NOT report this as "verify with any runner": it is cross-MODEL on ONE host, and the cross-host limit must be stated in the plan's own report. Do NOT claim `aw check all` passes; the bar is no-worsening against your own fresh baseline. Do NOT cite the 0%-material-corrections figure as a repository measurement; it is the maintainer's observation and the repo holds no such benchmark (F-7).

Execution contract: RE-READ `oc_runipd.py` and locate `run_opencode` and both of its call sites BY SYMBOL, never by the line numbers in this plan: it is one of the highest-contention files in the repo and several pending plans declare it. Commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption, since a failed hook invalidates the check. If a co-worker's in-flight change cannot be safely combined with an edit, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
