# IPD: Give the hardened execution profile a request path or record why it has none

- Date: 2026-09-08
- Kind: child
- Concern: THE HARDENED OS-SANDBOX PROFILE IS LIVE DEAD CODE: it works, it is tested, and NOTHING CAN ASK FOR IT. `_apply_execution_profile` reads `options.get("execution_profile")` (`oc_runipd.py:4992`) and that key is never written by anything: `grep -c 'options\["execution_profile"\]\s*='` over `agent_workflows/*.py` returns exactly ONE hit and it is a COMMENT (`oc_runipd.py:5392`, "`options["execution_profile"]` is explicitly "hardened""), not an assignment. There is no CLI flag either (`grep add_argument agent_workflows/oc_runipd.py | grep -i 'profile\|sandbox\|harden'` -> ZERO). So `select_execution_profile(None, caps)` returns `"default"` on every real invocation (`host_sandbox_profile.py:1120-1122`), `_apply_execution_profile` returns `argv` unchanged, and the sandbox branch below it is unreachable in production.
  THE CAPABILITY ITSELF IS REAL, WHICH IS WHY THIS IS WORTH FIXING RATHER THAN DELETING. Measured on this Linux host at HEAD: `detect_host_capabilities("opencode")` returns `supports_os_sandbox=True` with `sandbox_mechanism="landlock"` and `probe_notes["landlock"] = "landlock jail enforced: write outside the allowed root was refused"`. That is an EXECUTED probe, not an inspection (`host_sandbox_profile.py:64-75` records why inspection was rejected: on the development host every sysctl and binary said "available" while `unshare -Umr true` and `bwrap` both actually failed). So the enforcement works on at least one real host and cannot be requested there.
  ONE OF THE ITEM'S TWO BLOCKING CONSTRAINTS IS NOW DEAD, and it is the one that made this look dangerous. The backlog item states "IT WILL REFUSE LOUDLY UNTIL `dh0uno` IS FIXED", because the hardened profile binds the MAIN checkout read-only while `dh0uno` (an inner `aw` resolving control state against the lane worktree) meant a lane turn still reached into main's state. `dh0uno` IS FIXED: it landed in `6771e590` (2026-09-02, "anchor control state on the checkout, not the cwd (closes dh0uno)"), `ipd_lifecycle.checkout_control_root` (`:188`) is now the single authority keyed on the git common dir, the item sits in `.aw/records/backlog/done/` recording the fix, and `tests/test_statefork_dh0uno.py` passes 17/17 at HEAD. The item also says `dh0uno` "is fixed by `7p9n2v`, written and tested but unmerged"; that is ALSO stale, since `7p9n2v` is in `superseded/` and the fix arrived by a different route. So the "enabling hardened mode converts a silent state fork into a hard failure" warning no longer applies.
  THE OTHER CONSTRAINT SURVIVES INTACT AND IS THE REASON THIS PLAN DOES NOT SIMPLY ADD A FLAG. Landlock is Linux-only, the maintainer's platform bar is macOS 100% MUST and Windows 95%, and research prompt `q65sz3` (cross-platform agent write-confinement, `- Status: todo`) is scoped at exactly this question INCLUDING the portable options that sidestep OS confinement. A Linux-only `--hardened` flag would ship a guarantee most target hosts cannot honor, and it would ship it as a bare user-facing switch, which is the shape most likely to be read as a portable promise.
- Scope: Make the hardened profile REQUESTABLE by a surface whose portability claim is honest, or record in the spec that it is deliberately unreachable and why. The request path is the whole subject: this plan changes NOTHING about what the sandbox does once selected, and adds no second enforcement mechanism. The default is NOT changed to hardened under any outcome (see OQ-01), because a Linux-only default would make every macOS and Windows run either refuse or silently degrade, and `select_execution_profile` deliberately refuses rather than degrading.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/runner_profiles.py, tests/test_host_sandbox_profile.py, tests/test_hardened_profile_request.py, docs/runner-profiles.md
- Item-Dependencies: none
- Status: to-review
- Set: hardreach
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: n5qca5
- From-Backlog: fjs11i
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `fjs11i`, with ONE of its two stated blockers verified DEAD. The item's `dh0uno` sequencing warning is stale: `dh0uno` landed in `6771e590` (2026-09-02) via `ipd_lifecycle.checkout_control_root`, the item is in `backlog/done/`, and `tests/test_statefork_dh0uno.py` passes 17/17 at HEAD; the item's claim that the fix waits on unmerged `7p9n2v` is also stale (that plan is in `superseded/`). The PLATFORM constraint survives unchanged and is why this is authored as a decision-first plan whose default answer is a PROFILE FIELD rather than a CLI flag: `runner_profiles` already carries a per-profile schema with validated keys and an explicit rejection of unknown ones, so a capability-gated field there is expressible without adding a bare user-facing switch that reads as a portable promise. The defect itself re-verified by symbol at HEAD, not trusted from the item: the ONE `options["execution_profile"]` hit in the package is a COMMENT at `oc_runipd.py:5392`, and `detect_host_capabilities("opencode")` really does report `supports_os_sandbox=True` / `landlock` on this host, so the dead branch guards a working enforcement.

## Goal

Make a working, probe-verified sandbox capability actually requestable on hosts that can enforce it, without shipping a switch that implies a guarantee macOS and Windows cannot honor, or record the deliberate decision not to.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the live state before touching a request path

- [ ] E-01 RE-MEASURE THE DEAD-CODE CLAIM AND THE CAPABILITY CLAIM BY SYMBOL, and write both down. Two independent facts must be established at the HEAD you execute against, not inherited from this plan: (a) that nothing SETS `options["execution_profile"]`, and (b) that the sandbox it guards actually enforces on this host.
  RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` is under concurrent edit by live runs and its line numbers moved roughly seventy lines in a single day. Find `_apply_execution_profile` and `select_execution_profile` by name.
  DISTINGUISH THE COMMENT FROM AN ASSIGNMENT, because that distinction is the entire defect and a careless grep hides it. The single package hit for `options["execution_profile"]` is prose inside a comment; if you find a real assignment, this plan's premise has changed and E-02 must be re-scoped rather than executed.
  ALSO RECORD THE HOST ANSWER HONESTLY. `detect_host_capabilities("opencode")` reports `supports_os_sandbox=True` with mechanism `landlock` on the Linux host this was authored on. If your host reports False, that is CORRECT behavior and not a failure, but it changes what E-05 can demonstrate, so say so rather than reporting a test as skipped-therefore-passing.
  - Depends on: none
  - Expected outcome: a written, symbol-cited statement that the profile key has no setter and no CLI flag, that the one grep hit is a comment, and what this host's executed probe actually reports.
  - Execution state: pending

- [ ] E-02 STATE, IN THE PLAN'S OWN RECORD, WHAT EACH CANDIDATE REQUEST SURFACE PROMISES A USER, and do not pick the winner. This is the analysis OQ-01 needs, and its whole value is in the portability claim each surface implies, not in implementation cost.
  THE CANDIDATES, at minimum. (1) A BARE CLI FLAG (`--hardened` / `--execution-profile hardened`): most discoverable, and the worst portability claim, because a documented flag on a cross-platform tool reads as a cross-platform guarantee and will be typed on macOS where it can only refuse. (2) A PER-PROFILE FIELD in `runner_profiles` (the `ALLOWED_PROFILE_KEYS` schema at `runner_profiles.py:126`, with `_reject_unknown_keys` at `:480` already refusing unknown keys and `parse_profile` at `:501` validating): a user opts in deliberately, per profile, in a file they wrote, which is a much weaker implied promise than a global flag. (3) BOTH, the flag overriding the profile. (4) NEITHER: leave it unreachable and say so in the spec.
  FOR EACH, NAME WHAT HAPPENS ON A HOST THAT CANNOT ENFORCE. `select_execution_profile` RAISES `HardModeUnavailableError` for an unavailable `hardened` request (`host_sandbox_profile.py:1128-1135`) and that fail-closed choice is load-bearing (x03wgn Section 8 Phase 6.3, "fail rather than silently degrading"). So every candidate must say whether the user meets a hard refusal, a warning, or a documented no-op, and refusing-by-default is the safe answer that must not be quietly softened into degradation.
  DO NOT PRE-EMPT `q65sz3`. That research prompt covers the portable mechanisms (separate clone, per-run user account, detect-and-refuse) and is `todo`. This E-item enumerates REQUEST surfaces for the mechanism that already exists; it must not propose a second enforcement mechanism, which is that research's subject.
  - Depends on: E-01
  - Expected outcome: a candidate table naming, per surface, its discoverability, the portability claim it implies, and the exact behavior on a host whose probe returns False; no surface selected.
  - Execution state: pending

### Task group 2: implement only what the decision authorizes

- [ ] E-03 BUILD THE REQUEST PATH THE DECISION NAMES, wiring it to the EXISTING `options["execution_profile"]` key rather than introducing a parallel one. The key, its reader, and its fail-closed resolver all already exist and are tested; the deliverable is a writer.
  UNDER THE PROFILE-FIELD OUTCOME: add the field to `ALLOWED_PROFILE_KEYS` and validate it in `parse_profile` with the SAME shape the neighbouring fields use, then resolve it into `options["execution_profile"]` at run creation. Note the schema carries `SCHEMA_VERSION = 1` (`runner_profiles.py:101`) and `save` consults `_on_disk_version` (`:703`); adding an OPTIONAL key must not invalidate an existing on-disk config, and a test must prove an existing config still loads.
  UNDER THE CLI-FLAG OUTCOME: add exactly one argument and set the same key. Do NOT add a second code path into `_apply_execution_profile`.
  UNDER THE NEITHER OUTCOME: perform no wiring, and E-04 carries the whole deliverable.
  KEEP THE HOST ASYMMETRY VISIBLE. `agy_runipd.py` has ZERO profile integration (measured: `execution_profile`, `host_sandbox_profile`, `runner_profiles`, `resolve_launch_profile` and `launch_profile` ALL grep to zero in that file), so whatever is added here is opencode-only BY CONSTRUCTION, not by scope choice. Say so at the site and in the docs rather than letting a reader infer parity.
  - Depends on: E-02
  - Expected outcome: the decided surface sets `options["execution_profile"]`; no parallel key, no second sandbox code path, no change to `_apply_execution_profile`'s logic; the opencode-only reach is stated at the site.
  - Execution state: pending

- [ ] E-04 MAKE THE UNREACHABILITY OR THE REACHABILITY EXPLICIT IN WRITING, under every outcome, so the next reader is not left to grep for a setter as this graduation had to. Under a wiring outcome, document the surface, state that enforcement is Linux/Landlock-only, and state that an unsupported host REFUSES rather than degrades. Under the NEITHER outcome, record in the spec (or in `host_sandbox_profile`'s module contract, which already carries this class of statement at `:56-62`) that the profile is deliberately not requestable and why, citing the platform bar and `q65sz3`.
  DO NOT WRITE A PORTABILITY PROMISE THE CODE CANNOT KEEP. The documentation is user-facing prose: it must name the platform limit in the same breath as the capability, never after it.
  - Depends on: E-03
  - Expected outcome: prose stating either how to request hardened mode plus its platform limit and its refusal behavior, or that it is deliberately unreachable with the reason; no claim of cross-platform enforcement.
  - Execution state: pending

### Task group 3: prove the request path and prove nothing else moved

- [ ] E-05 TEST THE REQUEST PATH END TO END, INCLUDING THE REFUSAL, and prove the default path is byte-unchanged. Three assertions are required under a wiring outcome: a request reaches `select_execution_profile` (so the key is genuinely consumed and not merely stored); a host whose capabilities report `supports_os_sandbox=False` gets `HardModeUnavailableError` and NOT a silent `"default"`; and an invocation that requests nothing produces the identical `argv` it produces today.
  TEST THE REFUSAL WITH A CONSTRUCTED CAPABILITY OBJECT, not by finding an unsupported host. `select_execution_profile` takes capabilities as a parameter, so an all-False `HostSandboxCapabilities` is sufficient and the test is deterministic on every platform. A test that merely SKIPS on a host with no sandbox proves nothing and must not be reported as a pass.
  ALSO ASSERT THE NO-LANE REFUSAL STILL FIRES. `_apply_execution_profile` raises `SandboxProfileError` when hardened is requested with no `work_dir`, because there would be no lane boundary to enforce. A request path that can reach that branch makes this reachable for the first time, so it needs a test rather than remaining incidentally dead.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case that asserts against a sibling plan's live status. Inside a lane worktree roughly 32 further failures are environmental (tests reading live repo state). The criterion is that the AFTER failure set minus the BEFORE set is EMPTY, never an absolute count. Also re-run `tests/test_host_sandbox_profile.py` and paste ITS summary line, since that is the suite pinning the capability contract this plan makes reachable.
  - Depends on: E-04
  - Expected outcome: the request is consumed, an unsupported host refuses deterministically via constructed capabilities, the no-lane refusal is covered, the default argv is unchanged, and the bare-suite delta is empty with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE READER AND THE RESOLVER ALREADY EXIST AND ARE FAIL-CLOSED. `_apply_execution_profile` (`oc_runipd.py`) reads the key; `select_execution_profile` (`host_sandbox_profile.py:1110`) returns `"default"` for an absent request, raises `SandboxProfileError` for an unknown name, and raises `HardModeUnavailableError` rather than degrading when `hardened` is unsupported. This plan adds a WRITER only.
- THE PROBE EXECUTES, IT DOES NOT INSPECT, and the reason is recorded in the module (`host_sandbox_profile.py:64-75`): on the development host every sysctl and binary signal said "available" while the real `unshare`/`bwrap` attempts failed. Do not add a presence-based shortcut anywhere near this code.
- `runner_profiles` REFUSES UNKNOWN KEYS BY DESIGN (`_reject_unknown_keys`, `:480`), so a profile field cannot be added by convention alone; it must be added to `ALLOWED_PROFILE_KEYS` (`:126`) and validated in `parse_profile` (`:501`).
- THE AGY HOST HAS NO PROFILE INTEGRATION AT ALL (measured: five separate identifiers all grep to zero in `agy_runipd.py`), so any profile-borne capability is opencode-only by construction. `kgpptv` records the same asymmetry for `verify_with`.
- `dh0uno` IS FIXED (`6771e590`), so the item's sequencing warning is void; `checkout_control_root` (`ipd_lifecycle.py:188`) is now the single control-root authority and `tests/test_statefork_dh0uno.py` passes 17/17.
- BOTH RUNNER FILES ARE UNDER CONCURRENT EDIT. Re-locate every symbol by name before editing.
- Run the suite BARE. `pyproject.toml` `addopts` already supplies quiet, parallel, fast-subset flags.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the defect is real | The profile key has NO setter and NO CLI flag. The single package occurrence of `options["execution_profile"]` is a COMMENT, not an assignment, so the sandbox branch is unreachable in production. | `grep -c 'options\["execution_profile"\]' agent_workflows/*.py` -> 1 hit, at `oc_runipd.py:5392`, inside a comment; `grep add_argument agent_workflows/oc_runipd.py \| grep -i 'profile\|sandbox\|harden'` -> 0 |
| F-2 | HIGH | the capability is real | The dead branch guards WORKING enforcement, so this is a wiring gap and not dead weight to delete. `detect_host_capabilities("opencode")` on this Linux host: `supports_os_sandbox=True`, `sandbox_mechanism="landlock"`, `probe_notes["landlock"]="landlock jail enforced: write outside the allowed root was refused"`. | executed at HEAD in the graduation worktree |
| F-3 | HIGH | half the item's blocking rationale is DEAD | The item says hardened mode must wait for `dh0uno` and that `dh0uno` waits on unmerged `7p9n2v`. BOTH are stale: `dh0uno` landed in `6771e590` (2026-09-02) via `ipd_lifecycle.checkout_control_root`, its item is in `backlog/done/`, `tests/test_statefork_dh0uno.py` passes 17/17, and `7p9n2v` is in `superseded/` (the fix arrived by another route). | `git log -1 6771e590`; `ipd_lifecycle.py:188`; `aw find 7p9n2v`; test run |
| F-4 | HIGH | the surviving constraint is the platform bar | Landlock is Linux-only against a macOS-100%/Windows-95% bar, and `q65sz3` (`- Status: todo`) is scoped at exactly the portable-confinement question. This is why the plan is decision-first and why a bare flag is a candidate rather than the answer. | item text; `aw find q65sz3` |
| F-5 | MEDIUM | fail-closed must survive | An unsupported `hardened` request RAISES rather than returning `"default"`, deliberately (x03wgn Section 8 Phase 6.3). A request path must not soften that into a warning-and-degrade. | `host_sandbox_profile.py:1128-1135` |
| F-6 | MEDIUM | a schema exists to carry this | `runner_profiles` already has a versioned per-profile schema with an explicit unknown-key rejection, so a capability-gated field is expressible without a bare global switch. | `runner_profiles.py:101`, `:126`, `:480`, `:501` |
| F-7 | MEDIUM | opencode-only by construction | Five profile-related identifiers ALL grep to zero in `agy_runipd.py`, so a profile-borne request cannot reach the agy host regardless of scope choice. | `grep -c` over `agy_runipd.py` for `execution_profile`, `host_sandbox_profile`, `runner_profiles`, `resolve_launch_profile`, `launch_profile` -> 0 each |
| F-8 | MEDIUM | the no-lane branch is also dead today | `_apply_execution_profile` raises `SandboxProfileError` when hardened is requested without `work_dir`. With no request path that branch has never run in production, so a request path makes it live and it needs a test. | `_apply_execution_profile` body |
| F-9 | LOW | the ladder has already been corrected once | `909eb007` closed two fail-OPEN holes in this same probe ladder after Phase 6 merged, which is the empirical case for gating the request path behind a decision rather than adding a flag opportunistically. | item text; `git log 909eb007` |

## Proposed changes (ordered, validatable)

1. Re-measure the missing-setter claim and this host's probe answer by symbol (E-01).
2. Enumerate request surfaces by the portability claim each implies, choosing none (E-02).
3. Wire the decided surface to the existing key, with no parallel key and no second sandbox path (E-03).
4. State the reachability (or the deliberate unreachability) and the platform limit in writing (E-04).
5. Prove the request is consumed, the unsupported host refuses deterministically, and the default argv is unchanged (E-05).

## Deferred / out of scope (with reason)

- ANY SECOND ENFORCEMENT MECHANISM, portable or otherwise. `q65sz3` owns cross-platform write confinement (separate clone, per-run user account, detect-and-refuse) and is still `todo`. This plan makes the EXISTING Linux mechanism requestable; it does not answer what macOS and Windows should get, and a plan that tried would pre-empt research the maintainer commissioned for that question.
- CHANGING THE DEFAULT TO HARDENED. Excluded under every outcome, because the enforcement is Linux-only and an unsupported host REFUSES rather than degrades, so a hardened default would make every macOS and Windows run fail. Whether the default should ever change is a maintainer decision that belongs after `q65sz3`.
- ANY CHANGE TO WHAT THE SANDBOX DOES ONCE SELECTED. The jail construction, the discovery-then-execution split, and the probe ladder are `1o4eif`'s work, are tested, and are correct. This plan touches the request path only.
- GIVING THE AGY HOST A PROFILE SYSTEM. That host has no profile integration at all, and building one is `rununify`/`runprofile` territory, not a side effect of adding one field. The asymmetry is DOCUMENTED here (E-03) rather than fixed.
- THE `supports_commit_gateway` / `supports_deny_push` CAPABILITIES. Declared-and-never-probed by deliberate decision, and `RUN-NO-PUSH` is `4h7tt0`'s subject. Different capabilities, different plan.
- REPAIRING THE `probe_notes` VOCABULARY OR THE CAPABILITY SNAPSHOT SHAPE. Untouched; this plan reads capabilities, it does not extend them.

## Scope check

- Over-scope: none. One writer for an existing key, one optional schema field, documentation, and tests.
- Scope-Paths justification: `agent_workflows/oc_runipd.py` holds `_apply_execution_profile` and the run-creation site where `options` is composed, which is the only place a resolved request can be written (E-03); `agent_workflows/runner_profiles.py` holds `ALLOWED_PROFILE_KEYS`, `parse_profile` and `_reject_unknown_keys`, which is where a profile field must be declared and validated under the profile-field outcome (E-03); `tests/test_host_sandbox_profile.py` is the existing suite pinning the capability and resolver contract this plan makes reachable, and E-05 must show it still passes; `tests/test_hardened_profile_request.py` is the new suite for the request path, the deterministic refusal, and the no-lane refusal (E-05); `docs/runner-profiles.md` is the user-facing surface where a profile field and its platform limit must be stated together (E-04). Under the NEITHER outcome the two `agent_workflows/` paths may finish UNCHANGED and the recording goes into the module contract or the spec; a declared path left untouched is the expected outcome there, not an incomplete item.
- Under-scope, stated rather than left as `none`: this plan does not add a portable confinement mechanism, does not change the default profile, does not alter sandbox construction or the probe ladder, does not give agy a profile system, does not touch the two declared-unprobed capabilities, and does not extend the capability snapshot's shape. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and both counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed` (the pre-existing `test_orchestrator_retirement` case). In a lane, roughly 32 additional failures are environmental. The criterion is an EMPTY after-minus-before failure set, never an absolute count.
- `tests/test_host_sandbox_profile.py` re-run with ITS OWN summary line pasted, since it pins the contract this plan makes reachable.
- A DETERMINISTIC REFUSAL TEST built from a constructed all-False `HostSandboxCapabilities`, NOT from finding an unsupported host. A skip is not a pass and must not be reported as one.
- A DEFAULT-PATH INVARIANCE CHECK: an invocation requesting nothing produces identical `argv`.
- THE NO-LANE REFUSAL covered, since a request path makes that branch reachable for the first time.
- NEGATIVE PROOF that no parallel key was introduced: show the searches for a second profile key and for any new sandbox code path.
- Under the profile-field outcome, proof that an EXISTING on-disk `runner_profiles` config still loads unchanged (the schema is versioned and `save` consults `_on_disk_version`).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`host_sandbox_profile.py`'s MODULE CONTRACT is the authoritative prose on what the hardened profile guarantees, and it already states the void-on-unsupported-host rule (`:56-62`) and the executed-not-inspected rule (`:64-75`). It must gain one sentence saying HOW hardened mode is requested (or that it deliberately cannot be), because a contract describing a capability with no reachable request path is incomplete in exactly the way that produced this item.

`docs/runner-profiles.md` is user-facing. Under a wiring outcome it must name the request surface, the Linux/Landlock-only limit, and the refuse-not-degrade behavior TOGETHER, in that order, so a macOS reader learns the limit before deciding to use it. Write no em or en dashes in this prose.

No spec change is expected: `25kzda` 5.2 covers the runner-safety capabilities (`supports_commit_gateway`, `supports_deny_push`), not the sandbox profile's request path. If the executor finds spec text ASSERTING that the hardened profile is requestable today, that is a false claim and must be corrected in the same change; declare the spec file in `Scope-Paths` before editing it and say why in this section, per the spec-amendment rule.

## Open questions

### OQ-01: Which request surface should the hardened profile get, given that its enforcement is Linux-only?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT AGENT-RESOLVABLE, and the reason is that every candidate makes a different PROMISE to a user rather than a different implementation trade. A bare CLI flag is the most discoverable and the most misleading, because a documented flag on a cross-platform tool reads as a cross-platform guarantee and will be typed on macOS where it can only refuse. A per-profile `runner_profiles` field is a deliberate opt-in written into the user's own config, which is a materially weaker implied promise, and the schema already exists to carry it with unknown-key rejection. Leaving it unreachable and SAYING SO is also legitimate, and is what `q65sz3` being `todo` argues for. The choice binds a portability claim on a product whose stated bar is macOS 100% MUST and Windows 95%, and the repository has already paid once for a fail-OPEN inference in this exact probe ladder (`909eb007`), so it is the maintainer's call. E-01 and E-02 gather the evidence; nothing after E-02 may be built until this is answered.

### OQ-02: Should requesting hardened mode on an unsupported host refuse, warn, or no-op?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REFUSE, because that is already the shipped decision and it is recorded with its reason. `select_execution_profile` raises `HardModeUnavailableError` rather than returning `"default"`, and the docstring cites x03wgn Section 8 Phase 6.3 ("fail rather than silently degrading when hard mode is requested but unavailable"). A request path must not soften that: a user who asked for a jail and silently got none is strictly worse off than one who got an error, since they would proceed believing a boundary exists. This is settled by existing code and needs no new decision; E-05 pins it with a constructed all-False capability object so the assertion holds on every platform.

### OQ-03: Should the default execution profile change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, and it is out of scope under every outcome of OQ-01. The enforcement is Linux-only and an unsupported request REFUSES rather than degrades, so a hardened default would make every macOS and Windows run fail outright. The item deliberately left the default undecided; this plan keeps it undecided rather than settling it as a side effect of adding a request path, and the question properly belongs after `q65sz3` reports on portable confinement.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL output of the searches proving no setter and no CLI flag exists at your HEAD, and show that the one `options["execution_profile"]` hit is inside a comment by pasting the surrounding lines. THEN paste the ACTUAL output of `detect_host_capabilities("opencode")` on your host, showing `supports_os_sandbox`, `sandbox_mechanism` and `probe_notes`. State in one sentence whether your host can enforce, since that determines what V-05 can demonstrate.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the candidate table itself. For EACH candidate it must state, in its own cells, the implied portability claim and the exact behavior on a host whose probe returns False. Confirm in one sentence that NO candidate was selected in E-02 and that no second enforcement mechanism was proposed. If the table names fewer than the four candidates E-02 lists, say which was dropped and why.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the writer code and show it sets the EXISTING `options["execution_profile"]` key. Paste NEGATIVE proof that no parallel key and no second sandbox code path were added (show the searches). Paste the statement at the site recording that this is opencode-only, with the measurement backing it. Under the profile-field outcome, additionally paste the `ALLOWED_PROFILE_KEYS` diff and the validation added to `parse_profile`. Under the NEITHER outcome, state plainly that no wiring was performed and point at V-04's recording as the whole deliverable.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the documentation or module-contract text as written. Confirm by quoting it that the platform limit appears together with the capability and NOT after it, and that the refuse-not-degrade behavior is stated. Paste a search showing the prose contains no em or en dash. Under the NEITHER outcome, quote the sentence recording the deliberate unreachability and its cited reason.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of the new test module, including the test that constructs an all-False `HostSandboxCapabilities` and asserts `HardModeUnavailableError` (quote that assertion, so it is visibly deterministic rather than host-dependent) and the no-lane `SandboxProfileError` test. Paste the default-argv invariance assertion and its result. Paste `tests/test_host_sandbox_profile.py`'s OWN summary line. THEN paste the BARE `python3 -m pytest` summary lines from before and after, and state the failure-set delta explicitly; an empty delta is the criterion, and if any test SKIPPED on your host say so rather than counting it as a pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan carries a BLOCKING open question (OQ-01) and therefore cannot execute past E-02 until the maintainer answers it. That is deliberate: the surviving half of the backlog item's rationale is a portability decision, and the pre-execution gate that refuses a plan holding an unresolved `Blocking: yes` question is the correct mechanism to hold it. E-01 and E-02 are evidence-gathering and are safe to perform first; E-03 onward are conditional on the answer, and the NEITHER outcome legitimately leaves both `agent_workflows/` paths unchanged.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol in `oc_runipd.py` by NAME before editing, because that file is under concurrent edit by live runs and its line numbers move by tens of lines per day. Paste ACTUAL test output; never claim a pass that was not run, and never report a host-dependent SKIP as a pass. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence. If OQ-01 resolves to NEITHER, the plan still finalizes normally: the deliverable is then E-04's recorded decision, which is a real outcome and not a withdrawal.
