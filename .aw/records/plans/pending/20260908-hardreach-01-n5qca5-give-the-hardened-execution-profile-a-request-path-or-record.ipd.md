# IPD: Give the hardened execution profile a request path or record why it has none

- Date: 2026-09-08
- Kind: child
- Concern: THE HARDENED OS-SANDBOX PROFILE IS LIVE DEAD CODE: it works, it is tested, and NOTHING CAN ASK FOR IT. `_apply_execution_profile` reads `options.get("execution_profile")` (`oc_runipd.py:4992`) and that key is never written by anything: `grep -c 'options\["execution_profile"\]\s*='` over `agent_workflows/*.py` returns exactly ONE hit and it is a COMMENT (`oc_runipd.py:5392`, "`options["execution_profile"]` is explicitly "hardened""), not an assignment. There is no CLI flag either (`grep add_argument agent_workflows/oc_runipd.py | grep -i 'profile\|sandbox\|harden'` -> ZERO). So `select_execution_profile(None, caps)` returns `"default"` on every real invocation (`host_sandbox_profile.py:1120-1122`), `_apply_execution_profile` returns `argv` unchanged, and the sandbox branch below it is unreachable in production.
  THE CAPABILITY ITSELF IS REAL, WHICH IS WHY THIS IS WORTH FIXING RATHER THAN DELETING. Measured on this Linux host at HEAD: `detect_host_capabilities("opencode")` returns `supports_os_sandbox=True` with `sandbox_mechanism="landlock"` and `probe_notes["landlock"] = "landlock jail enforced: write outside the allowed root was refused"`. That is an EXECUTED probe, not an inspection (`host_sandbox_profile.py:64-75` records why inspection was rejected: on the development host every sysctl and binary said "available" while `unshare -Umr true` and `bwrap` both actually failed). So the enforcement works on at least one real host and cannot be requested there.
  ONE OF THE ITEM'S TWO BLOCKING CONSTRAINTS IS NOW DEAD, and it is the one that made this look dangerous. The backlog item states "IT WILL REFUSE LOUDLY UNTIL `dh0uno` IS FIXED", because the hardened profile binds the MAIN checkout read-only while `dh0uno` (an inner `aw` resolving control state against the lane worktree) meant a lane turn still reached into main's state. `dh0uno` IS FIXED: it landed in `6771e590` (2026-09-02, "anchor control state on the checkout, not the cwd (closes dh0uno)"), `ipd_lifecycle.checkout_control_root` (`:188`) is now the single authority keyed on the git common dir, the item sits in `.aw/records/backlog/done/` recording the fix, and `tests/test_statefork_dh0uno.py` passes 17/17 at HEAD. The item also says `dh0uno` "is fixed by `7p9n2v`, written and tested but unmerged"; that is ALSO stale, since `7p9n2v` is in `superseded/` and the fix arrived by a different route. So the "enabling hardened mode converts a silent state fork into a hard failure" warning no longer applies.
  THE OTHER CONSTRAINT SURVIVES INTACT AND IS THE REASON THIS PLAN DOES NOT SIMPLY ADD A FLAG. Landlock is Linux-only, the maintainer's platform bar is macOS 100% MUST and Windows 95%, and research prompt `q65sz3` (cross-platform agent write-confinement, `status: todo` in its front matter, re-verified at review HEAD) is scoped at exactly this question INCLUDING the portable options that sidestep OS confinement. A Linux-only `--hardened` flag would ship a guarantee most target hosts cannot honor, and it would ship it as a bare user-facing switch, which is the shape most likely to be read as a portable promise.
  ADDED IN REVIEW, AND IT IS THE MOST LIKELY WAY THIS PLAN FAILS IN EXECUTION: `ALLOWED_PROFILE_KEYS` IS BYTE-PINNED BY A SECURITY-FENCE TEST THAT THE PLAN DID NOT DECLARE. `tests/test_runner_profiles.py::test_no_arbitrary_argv_or_credential_field_is_persistable` (`:1650-1674`) asserts the sorted key list LITERALLY as `["agent", "model", "runner", "validate", "variant", "verify_with"]`, and its own comment states the intent: "assert them literally so widening them requires editing this test and stating why". `tests/test_runner_profiles_e2e.py:841-844` asserts the SAME literal list AND binds it to `docs/runner-profiles.md`. So the profile-field outcome cannot be implemented without editing BOTH test files, and both are now declared in `Scope-Paths`. This is not a nuisance to route around: the test is a deliberate speed bump on the storable surface, and the plan must satisfy it the way `verify_with` did, by stating in the test itself why the new key does not widen the injection surface.
  AND NOTE WHICH NEIGHBOURS ARE FORBIDDEN, because it decides the field's NAME and shape. `FORBIDDEN_PROFILE_KEYS` refuses `permission` and `permissions` outright (`runner_profiles.py:215-225`), among argv/credential/prompt keys, each refused because it "would convert a convenience alias into a command-injection, credential-disclosure, or behavior-override surface". A sandbox-request field sits next to that boundary, so it must be a CLOSED ENUM or boolean naming an already-validated profile concept, never a path, a root, an argv fragment or a permission expression. The `verify_with` precedent is explicit that a REFERENCE to something already validated is safe where an inline value would not be.
- Scope: Make the hardened profile REQUESTABLE by a surface whose portability claim is honest, or record in the spec that it is deliberately unreachable and why. The request path is the whole subject: this plan changes NOTHING about what the sandbox does once selected, and adds no second enforcement mechanism. The default is NOT changed to hardened under any outcome (see OQ-01), because a Linux-only default would make every macOS and Windows run either refuse or silently degrade, and `select_execution_profile` deliberately refuses rather than degrading.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/runner_profiles.py, agent_workflows/host_sandbox_profile.py, tests/test_host_sandbox_profile.py, tests/test_hardened_profile_request.py, tests/test_runner_profiles.py, tests/test_runner_profiles_e2e.py, docs/runner-profiles.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: hardreach
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: n5qca5
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: fjs11i
- Blocks-Release: next

## Workflow history
- 2026-09-20 executed (opencode its_direct/pt3-claude-opus-5-1m-us): E-01..E-05 performed, V-01..V-05 pass with pasted evidence. THE DEAD REQUEST PATH IS CLOSED: `options["execution_profile"]` now HAS a writer, an `execution_profile` field in the operator's own `runner-profiles.json`, per OQ-01's recorded maintainer decision (the profile-field outcome; NOT a CLI flag, NOT the NEITHER branch). PREMISE RE-MEASURED AT EXECUTION HEAD AND TRUE before touching anything: zero assignments to the key at HEAD, its single occurrence a COMMENT, zero matching `add_argument` flags, while `detect_host_capabilities("opencode")` on this Linux host really returns `supports_os_sandbox=True` / `landlock` with the probe note recording a genuinely refused write, so the dead branch guarded working enforcement. IMPLEMENTATION: one optional closed-enum field (`EXECUTION_PROFILE_NAMES = ("default", "hardened")`) validated by `validate_execution_profile_name`, resolved off the APPLIED profile in `runner_profiles.resolve` with conditional provenance, and written to the EXISTING key in `initialize_run`'s `host_options`; no parallel key, no second sandbox code path, and `_apply_execution_profile`'s logic untouched (only its docstring). NO VERSION BUMP: the reader is version-agnostic about a field and a v1 document still round-trips byte-identically. BOTH PINNED SECURITY FENCES EDITED AND JUSTIFIED IN-TEST following `verify_with`'s precedent, both still LITERAL sorted-list comparisons (not loosened to subset checks), and the e2e doc binding was STRENGTHENED to assert every allowed key is named in the doc. TESTS: new `tests/test_hardened_profile_request.py` 20 passed (no skips; the unsupported-host refusal uses a CONSTRUCTED all-False capability object so it is deterministic on every platform, and the no-lane `SandboxProfileError` branch is now covered for the first time); `test_host_sandbox_profile.py` 29 passed, `test_runner_profiles.py` 72 passed, `test_runner_profiles_e2e.py` 34 passed. BARE SUITE before `1 failed, 7239 passed, 3 skipped, 2 xfailed`, after `1 failed, 7259 passed, 3 skipped, 2 xfailed`; failure-set delta BY NODE ID is EMPTY. The one failure is `test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which is NOT the failure the plan predicted (`test_reporting_contract` ParityTests PASSES here at 45 passed, and no `opencode-recovery/` tree exists in this lane) and is ENVIRONMENTAL: the lane turn exports `OPENCODE_CONFIG_CONTENT`, which the test inherits, proven by `env -u OPENCODE_CONFIG_CONTENT` making the file pass 43/43 with no code change. Left unfixed and reported as a defect-report finding instead. SCOPE: `agent_workflows/host_sandbox_profile.py` was ADDED to `Scope-Paths` at execution because E-04 and the spec-sync section both mandate the module-contract sentence while the path was omitted from the list; the edit there is DOCSTRING ONLY (23 insertions, 0 deletions). `aw sanitize --agent` clean; `aw ipd lint --phase pre-transition` conforming.
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-C01..PR-C08 all FIXED, no deferrals, no new open questions. Premise re-measured and TRUE: exactly one options[execution_profile] occurrence in the package and it is a COMMENT (oc_runipd.py:5499), no setter, no CLI flag, while detect_host_capabilities('opencode') really returns supports_os_sandbox=True / landlock with the probe note recording a real refused write. The plan's staleness corrections to backlog fjs11i also verified: dh0uno landed in 6771e590, checkout_control_root exists, test_statefork_dh0uno passes 17/17, 7p9n2v is superseded, q65sz3 is still status: todo. PR-C01 (HIGH): THE RESOLVED OUTCOME WAS UNIMPLEMENTABLE AS SCOPED - ALLOWED_PROFILE_KEYS is byte-pinned by two security-fence tests (test_runner_profiles.py:1650-1674 and test_runner_profiles_e2e.py:841-844) that each assert the sorted list LITERALLY and that the plan did not declare; the first test's own comment says the literal exists so widening it 'requires editing this test and stating why'. Both files are now declared and E-03 must satisfy the fence the way verify_with did, with an in-test justification, and may not loosen either assertion to a subset check. PR-C02 (HIGH): FORBIDDEN_PROFILE_KEYS refuses permission/permissions BY NAME, so the new field must be a closed enum or boolean and never a path, root, argv fragment or permission expression; proof those value shapes are refused is now required. PR-C03 (HIGH): the gate paragraph claimed a BLOCKING OQ-01 that 'cannot execute past E-02' while all three questions read Blocking: no and OQ-01 is resolved with a recorded 2026-09-08 maintainer decision, so an executor would have stopped to wait for an answer that already exists; corrected. PR-C04 (HIGH): the e2e suite binds the allowed-key list to docs/runner-profiles.md and forbids em/en dashes there, so the doc edit is a build dependency rather than prose. PR-C05: SCHEMA_VERSION is 2 not 1, both 1 and 2 are read, nothing is migrated, and the reader is version-agnostic about a FIELD, so no version bump is needed. PR-C06: a profile field means the agy host SILENTLY IGNORES a hardened request rather than refusing it (five profile identifiers grep to zero there), which is degradation-by-omission and must be stated in the user-facing doc; adding an agy refusal is explicitly forbidden here. PR-C07: the suite baseline was wrong in both halves (real: 1 failed, 5958 passed at test_reporting_contract ParityTests from another party's gitignored opencode-recovery/ tree; test_orchestrator_retirement passes at 112). PR-C08: the writer's seam is now named (resolve_launch_profile, resolving BEFORE the run dir exists and freezing into state[options] once) and several drifted citations re-located by symbol. Verified correct and left alone: the fail-closed resolver and OQ-02, OQ-03's refusal to change the default, the q65sz3 fence, the dead no-lane branch, and the constructed-capabilities test strategy. Four decisions recorded (D-1..D-4), all reversible. E/V counts unchanged at five each; aw ipd lint --phase review-finalize conforming. Readiness go-pending-approval: no unfixed BLOCKER/HIGH and no blocking question.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `fjs11i`, with ONE of its two stated blockers verified DEAD. The item's `dh0uno` sequencing warning is stale: `dh0uno` landed in `6771e590` (2026-09-02) via `ipd_lifecycle.checkout_control_root`, the item is in `backlog/done/`, and `tests/test_statefork_dh0uno.py` passes 17/17 at HEAD; the item's claim that the fix waits on unmerged `7p9n2v` is also stale (that plan is in `superseded/`). The PLATFORM constraint survives unchanged and is why this is authored as a decision-first plan whose default answer is a PROFILE FIELD rather than a CLI flag: `runner_profiles` already carries a per-profile schema with validated keys and an explicit rejection of unknown ones, so a capability-gated field there is expressible without adding a bare user-facing switch that reads as a portable promise. The defect itself re-verified by symbol at HEAD, not trusted from the item: the ONE `options["execution_profile"]` hit in the package is a COMMENT at `oc_runipd.py:5392`, and `detect_host_capabilities("opencode")` really does report `supports_os_sandbox=True` / `landlock` on this host, so the dead branch guards a working enforcement.

## Goal

Make a working, probe-verified sandbox capability actually requestable on hosts that can enforce it, without shipping a switch that implies a guarantee macOS and Windows cannot honor, or record the deliberate decision not to.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the live state before touching a request path

- [x] E-01 RE-MEASURE THE DEAD-CODE CLAIM AND THE CAPABILITY CLAIM BY SYMBOL, and write both down. Two independent facts must be established at the HEAD you execute against, not inherited from this plan: (a) that nothing SETS `options["execution_profile"]`, and (b) that the sandbox it guards actually enforces on this host.
  RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py` is under concurrent edit by live runs and its line numbers moved roughly seventy lines in a single day. Find `_apply_execution_profile` and `select_execution_profile` by name.
  DISTINGUISH THE COMMENT FROM AN ASSIGNMENT, because that distinction is the entire defect and a careless grep hides it. The single package hit for `options["execution_profile"]` is prose inside a comment; if you find a real assignment, this plan's premise has changed and E-02 must be re-scoped rather than executed.
  ALSO RECORD THE HOST ANSWER HONESTLY. `detect_host_capabilities("opencode")` reports `supports_os_sandbox=True` with mechanism `landlock` on the Linux host this was authored on. If your host reports False, that is CORRECT behavior and not a failure, but it changes what E-05 can demonstrate, so say so rather than reporting a test as skipped-therefore-passing.
  - Depends on: none
  - Expected outcome: a written, symbol-cited statement that the profile key has no setter and no CLI flag, that the one grep hit is a comment, and what this host's executed probe actually reports.
  - Execution state: performed

- [x] E-02 STATE, IN THE PLAN'S OWN RECORD, WHAT EACH CANDIDATE REQUEST SURFACE PROMISES A USER, and do not pick the winner. This is the analysis OQ-01 needs, and its whole value is in the portability claim each surface implies, not in implementation cost.
  THE CANDIDATES, at minimum. (1) A BARE CLI FLAG (`--hardened` / `--execution-profile hardened`): most discoverable, and the worst portability claim, because a documented flag on a cross-platform tool reads as a cross-platform guarantee and will be typed on macOS where it can only refuse. (2) A PER-PROFILE FIELD in `runner_profiles` (the `ALLOWED_PROFILE_KEYS` schema at `runner_profiles.py:126`, with `_reject_unknown_keys` at `:480` already refusing unknown keys and `parse_profile` at `:501` validating): a user opts in deliberately, per profile, in a file they wrote, which is a much weaker implied promise than a global flag. (3) BOTH, the flag overriding the profile. (4) NEITHER: leave it unreachable and say so in the spec.
  FOR EACH, NAME WHAT HAPPENS ON A HOST THAT CANNOT ENFORCE. `select_execution_profile` RAISES `HardModeUnavailableError` for an unavailable `hardened` request (`host_sandbox_profile.py:1128-1135`) and that fail-closed choice is load-bearing (x03wgn Section 8 Phase 6.3, "fail rather than silently degrading"). So every candidate must say whether the user meets a hard refusal, a warning, or a documented no-op, and refusing-by-default is the safe answer that must not be quietly softened into degradation.
  DO NOT PRE-EMPT `q65sz3`. That research prompt covers the portable mechanisms (separate clone, per-run user account, detect-and-refuse) and is `todo`. This E-item enumerates REQUEST surfaces for the mechanism that already exists; it must not propose a second enforcement mechanism, which is that research's subject.
  - Depends on: E-01
  - Expected outcome: a candidate table naming, per surface, its discoverability, the portability claim it implies, and the exact behavior on a host whose probe returns False; no surface selected.
  - Execution state: performed

### Task group 2: implement only what the decision authorizes

- [x] E-03 BUILD THE REQUEST PATH THE DECISION NAMES, wiring it to the EXISTING `options["execution_profile"]` key rather than introducing a parallel one. The key, its reader, and its fail-closed resolver all already exist and are tested; the deliverable is a writer.
  UNDER THE PROFILE-FIELD OUTCOME: add the field to `ALLOWED_PROFILE_KEYS` and validate it in `parse_profile` with the SAME shape the neighbouring fields use, then resolve it into `options["execution_profile"]` at run creation.
  YOU MUST EDIT TWO PINNED SECURITY TESTS, AND THIS IS THE ITEM'S REAL WORK RATHER THAN A CHORE. `tests/test_runner_profiles.py::test_no_arbitrary_argv_or_credential_field_is_persistable` and `tests/test_runner_profiles_e2e.py::test_every_field_the_doc_says_is_refused_really_is` each assert the sorted `ALLOWED_PROFILE_KEYS` list LITERALLY, so the field cannot land without updating both. Follow the `verify_with` precedent EXACTLY: it added itself to those literals together with an in-test comment explaining why it does not widen the injection surface. Write the equivalent justification for this field. Do NOT loosen either assertion into a subset or membership check; the literal list IS the control.
  THE E2E TEST ALSO BINDS THE SCHEMA TO THE DOC, so `docs/runner-profiles.md` must gain the field in the same change or that test fails. That is why the doc is in `Scope-Paths` and why E-04 is not merely nice-to-have prose.
  NAME AND SHAPE THE FIELD AGAINST THE FORBIDDEN LIST. `permission` and `permissions` are refused BY NAME, so do not choose a name in that family and do not accept a path, root, argv fragment or permission expression as its value. A closed enum (the profile names `select_execution_profile` already accepts) or a boolean is the shape that keeps the storable surface as narrow as it is today.
  SCHEMA VERSION, CORRECTED IN REVIEW: it is `SCHEMA_VERSION = 2` (`runner_profiles.py:150`), not 1 as this plan originally said, with `SUPPORTED_SCHEMA_VERSIONS = {1, 2}` (`:159`) and the module documenting that BOTH are read, NOTHING is migrated, and a v1 document keeps loading byte-for-byte. The reader is deliberately version-AGNOSTIC about a FIELD, which means an optional key needs no version bump at all; the `verify_with` note at `:145-157` records exactly this reasoning. Prove an existing on-disk config still loads, and do NOT bump the version for an optional field.
  UNDER THE CLI-FLAG OUTCOME: add exactly one argument and set the same key. Do NOT add a second code path into `_apply_execution_profile`.
  UNDER THE NEITHER OUTCOME: perform no wiring, and E-04 carries the whole deliverable.
  USE THE EXISTING RESOLUTION SEAM, WHICH IS ALREADY THE RIGHT SHAPE, rather than reading the profile store at the argv-building site. `resolve_launch_profile(args)` (`oc_runipd.py:2613`) resolves the launch identity ONCE before any durable side effect, delegating the whole precedence decision to `runner_profiles.resolve`, and its resolved values are frozen into `state["options"]` at the run-creation dict (`oc_runipd.py:3005`). Two properties there are load-bearing and must be preserved: resolution happens BEFORE the run directory exists, so a malformed config leaves no run id or partial state; and the options snapshot is FROZEN ONCE and never re-resolved, which is what makes a later edit to `runner-profiles.json` unable to change an existing run. A request resolved anywhere else loses both.
  RESPECT THE PRECEDENCE DISCIPLINE THE MODULE ALREADY DOCUMENTS. `verify_with` and `validate` are TRI-STATE with an explicit ladder (explicit flag > profile field > defaults > absent) and the module states plainly that "AN EXPLICIT FLAG ALWAYS WINS" because a stored default silently overriding a flag "would make the flag a lie". If no flag exists this is moot, but say so; if a flag is ever added later, the field must already sit in that ladder rather than beside it.
  KEEP THE HOST ASYMMETRY VISIBLE. `agy_runipd.py` has ZERO profile integration (measured: `execution_profile`, `host_sandbox_profile`, `runner_profiles`, `resolve_launch_profile` and `launch_profile` ALL grep to zero in that file), so whatever is added here is opencode-only BY CONSTRUCTION, not by scope choice. Say so at the site and in the docs rather than letting a reader infer parity.
  BE PRECISE THAT THIS IS NOT AN AGY REFUSAL. A profile field the agy host never reads means an agy run SILENTLY IGNORES a hardened request rather than refusing it, which is the degradation this whole design refuses elsewhere. State that consequence explicitly in E-04's prose; if the maintainer wants agy to refuse instead, that is a separate change and must not be smuggled in here.
  - Depends on: E-02
  - Expected outcome: the decided surface sets `options["execution_profile"]`; no parallel key, no second sandbox code path, no change to `_apply_execution_profile`'s logic; the opencode-only reach is stated at the site.
  - Execution state: performed

- [x] E-04 MAKE THE UNREACHABILITY OR THE REACHABILITY EXPLICIT IN WRITING, under every outcome, so the next reader is not left to grep for a setter as this graduation had to. Under a wiring outcome, document the surface, state that enforcement is Linux/Landlock-only, and state that an unsupported host REFUSES rather than degrades. Under the NEITHER outcome, record in the spec (or in `host_sandbox_profile`'s module contract, which already carries this class of statement at `:56-62`) that the profile is deliberately not requestable and why, citing the platform bar and `q65sz3`.
  DO NOT WRITE A PORTABILITY PROMISE THE CODE CANNOT KEEP. The documentation is user-facing prose: it must name the platform limit in the same breath as the capability, never after it.
  - Depends on: E-03
  - Expected outcome: prose stating either how to request hardened mode plus its platform limit and its refusal behavior, or that it is deliberately unreachable with the reason; no claim of cross-platform enforcement.
  - Execution state: performed

### Task group 3: prove the request path and prove nothing else moved

- [x] E-05 TEST THE REQUEST PATH END TO END, INCLUDING THE REFUSAL, and prove the default path is byte-unchanged. Three assertions are required under a wiring outcome: a request reaches `select_execution_profile` (so the key is genuinely consumed and not merely stored); a host whose capabilities report `supports_os_sandbox=False` gets `HardModeUnavailableError` and NOT a silent `"default"`; and an invocation that requests nothing produces the identical `argv` it produces today.
  TEST THE REFUSAL WITH A CONSTRUCTED CAPABILITY OBJECT, not by finding an unsupported host. `select_execution_profile` takes capabilities as a parameter, so an all-False `HostSandboxCapabilities` is sufficient and the test is deterministic on every platform. A test that merely SKIPS on a host with no sandbox proves nothing and must not be reported as a pass.
  ALSO ASSERT THE NO-LANE REFUSAL STILL FIRES. `_apply_execution_profile` raises `SandboxProfileError` when hardened is requested with no `work_dir`, because there would be no lane boundary to enforce. A request path that can reach that branch makes this reachable for the first time, so it needs a test rather than remaining incidentally dead.
  RUN THE TWO PINNED PROFILE SUITES EXPLICITLY, because they are the ones this change is most likely to break and the ones whose literals it must edit: `tests/test_runner_profiles.py` and `tests/test_runner_profiles_e2e.py`. Paste each summary line. A green run here is what proves the security fence was updated deliberately rather than loosened.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA BY NODE ID. THE PLAN'S BASELINE WAS WRONG IN BOTH HALVES; re-measured on main at review HEAD `261a72a2`: `1 failed, 5958 passed, 3 skipped, 2 xfailed`. The failure is NOT `tests/test_orchestrator_retirement.py`, which PASSES (`112 passed` in isolation), but `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by the GITIGNORED `opencode-recovery/` tree of another party's session transcripts. It is pre-existing and unrelated: do NOT "fix" it and do NOT delete or edit that tree, which is another party's work under the shared-checkout rule. The criterion is that the AFTER failure set minus the BEFORE set is EMPTY, compared by NODE ID rather than by count, since counts drift as other agents land tests. Also re-run `tests/test_host_sandbox_profile.py` and paste ITS summary line (measured `27 passed` at review HEAD), since that is the suite pinning the capability contract this plan makes reachable.
  - Depends on: E-04
  - Expected outcome: the request is consumed, an unsupported host refuses deterministically via constructed capabilities, the no-lane refusal is covered, the default argv is unchanged, and the bare-suite delta is empty with counts stated.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE READER AND THE RESOLVER ALREADY EXIST AND ARE FAIL-CLOSED. `_apply_execution_profile` (`oc_runipd.py`) reads the key; `select_execution_profile` (`host_sandbox_profile.py:1110`) returns `"default"` for an absent request, raises `SandboxProfileError` for an unknown name, and raises `HardModeUnavailableError` rather than degrading when `hardened` is unsupported. This plan adds a WRITER only.
- THE PROBE EXECUTES, IT DOES NOT INSPECT, and the reason is recorded in the module (`host_sandbox_profile.py:64-75`): on the development host every sysctl and binary signal said "available" while the real `unshare`/`bwrap` attempts failed. Do not add a presence-based shortcut anywhere near this code.
- `runner_profiles` REFUSES UNKNOWN KEYS BY DESIGN (`_reject_unknown_keys`, `:612`), so a profile field cannot be added by convention alone; it must be added to `ALLOWED_PROFILE_KEYS` (`:190`) and validated in `parse_profile` (`:633`).
- AND THE ALLOWED SET IS BYTE-PINNED BY TWO SECURITY TESTS: `tests/test_runner_profiles.py:1650-1674` and `tests/test_runner_profiles_e2e.py:841-844` each assert the sorted list LITERALLY, the first stating that the literal exists so that widening it "requires editing this test and stating why". `verify_with` is the precedent: it edited both literals and justified itself in-test.
- `FORBIDDEN_PROFILE_KEYS` REFUSES `permission`/`permissions` BY NAME (`:215-225`), so this field must be a closed enum or boolean, never a path, root, argv fragment or permission expression.
- SCHEMA_VERSION IS 2 WITH BOTH 1 AND 2 READ (`:150`, `:159`), nothing is migrated, and the reader is version-AGNOSTIC about a field, so an optional key needs no version bump.
- THE RESOLUTION SEAM ALREADY EXISTS: `resolve_launch_profile` (`oc_runipd.py:2613`) resolves once BEFORE the run directory exists and freezes into `state["options"]` (`:3005`), so a malformed config leaves no partial state and a later config edit cannot change an existing run.
- THE MODULE'S PRECEDENCE RULE IS EXPLICIT: "AN EXPLICIT FLAG ALWAYS WINS", because a stored default overriding a flag "would make the flag a lie".
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
| F-6 | MEDIUM | a schema exists to carry this | `runner_profiles` already has a versioned per-profile schema with an explicit unknown-key rejection, so a capability-gated field is expressible without a bare global switch. Re-located by symbol at review HEAD: `SCHEMA_VERSION` `:150`, `ALLOWED_PROFILE_KEYS` `:190`, `_reject_unknown_keys` `:612`, `parse_profile` `:633`. | `runner_profiles.py:150`, `:190`, `:612`, `:633` |
| F-10 | BLOCKER-class if unhandled (reported HIGH) | ADDING THE KEY BREAKS TWO PINNED SECURITY TESTS THE PLAN DID NOT DECLARE | `tests/test_runner_profiles.py::test_no_arbitrary_argv_or_credential_field_is_persistable` (`:1650-1674`) and `tests/test_runner_profiles_e2e.py::test_every_field_the_doc_says_is_refused_really_is` (`:841-844`) each assert `sorted(ALLOWED_PROFILE_KEYS)` LITERALLY as `["agent","model","runner","validate","variant","verify_with"]`. The first test's own comment says the literal exists "so widening them requires editing this test and stating why". Neither file was in `Scope-Paths`, so the profile-field outcome was unimplementable as scoped. | the two literal assertions; `verify_with`'s in-test justification as the precedent |
| F-11 | HIGH | THE E2E TEST BINDS THE SCHEMA TO THE DOC, so the doc edit is mandatory rather than cosmetic | `test_every_field_the_doc_says_is_refused_really_is` asserts the allowed list "is exactly what the doc lists", and a sibling test forbids em/en dashes in that doc. So `docs/runner-profiles.md` must gain the field in the SAME change or the suite fails, which upgrades E-04 from documentation to a build dependency. | `tests/test_runner_profiles_e2e.py:838-844`, `:846-850` |
| F-12 | HIGH | `permission`/`permissions` ARE FORBIDDEN KEYS, which constrains this field's name and value space | `FORBIDDEN_PROFILE_KEYS` refuses them by name among argv/credential/prompt keys, each because it "would convert a convenience alias into a command-injection, credential-disclosure, or behavior-override surface". A sandbox-request field is adjacent to that boundary, so it must be a closed enum or boolean, never a path, root, argv fragment or permission expression. The `verify_with` precedent is explicit that a reference to an already-validated concept is what makes a new key safe. | `runner_profiles.py:215-225`; the `verify_with` security rationale |
| F-13 | HIGH | THE GATE PARAGRAPH CONTRADICTED THE ARTIFACT and would have stopped an executor at E-02 | The gate said the plan "carries a BLOCKING open question (OQ-01) and therefore cannot execute past E-02", while all three questions read `- Blocking: no` and OQ-01 is `- Status: resolved` with a recorded maintainer decision. Left as written it tells an executor to wait for an answer that already exists. | plan `:149`, `:152`, `:160`, `:167` versus the gate paragraph |
| F-14 | MEDIUM | THE SUITE BASELINE IS WRONG IN BOTH HALVES and names a test that passes | Plan cites `1 failed, 5648 passed` blaming `test_orchestrator_retirement`, which passes (`112 passed`). Real: `1 failed, 5958 passed, 3 skipped, 2 xfailed` failing at `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by another party's gitignored `opencode-recovery/` tree. An executor could misread it as their own regression or clean up files that are not theirs. | bare pytest at `261a72a2` |
| F-15 | MEDIUM | SCHEMA_VERSION IS 2, NOT 1, and no version bump is needed | The plan says `SCHEMA_VERSION = 1` at `:101`. It is `2` at `:150`, with `SUPPORTED_SCHEMA_VERSIONS = {1, 2}` and the module documenting that both are read, nothing is migrated, a v1 document loads byte-for-byte, and the reader is deliberately version-AGNOSTIC about a field. So an optional key needs no bump, and the plan's migration worry is answered by existing design. | `runner_profiles.py:145-159` |
| F-16 | MEDIUM | A PROFILE FIELD MEANS AGY SILENTLY IGNORES THE REQUEST rather than refusing it | The agy host reads no profile keys at all, so a hardened request in a shared profile is a no-op there. That is degradation-by-omission, the exact failure mode `select_execution_profile` refuses by raising. The plan documents the asymmetry but does not name this consequence. | F-7's measurement plus `select_execution_profile`'s fail-closed contract |
| F-17 | LOW | several cited line numbers had drifted | The comment is at `oc_runipd.py:5499` not `:5392`; `_apply_execution_profile` is `:5030`; `runner_profiles` symbols are `:150`/`:190`/`:612`/`:633` not `:101`/`:126`/`:480`/`:501`. The plan's own re-locate-by-name instruction is correct and is now the only citation rule. | measured by symbol at review HEAD |
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
- Scope-Paths justification, ADDED AT EXECUTION: `agent_workflows/host_sandbox_profile.py` is DECLARED, one literal file, because E-04 and the spec-sync section below BOTH require the edit that was made to it and neither could be satisfied without it. That section states plainly that the module contract "must gain one sentence saying HOW hardened mode is requested (or that it deliberately cannot be), because a contract describing a capability with no reachable request path is incomplete in exactly the way that produced this item", and E-04 names `host_sandbox_profile`'s module contract at `:56-62` as a legitimate home for the recording. So the plan mandated the edit in prose while omitting the path from this list, which was an authoring oversight rather than a scope change: the ONLY change made there is the module DOCSTRING (no code, no behavior, no signature), which V-04(b) quotes in full. Declared as a literal file path rather than a directory or glob, so the widening cannot neuter the fence.
- Scope-Paths justification: `agent_workflows/oc_runipd.py` holds `_apply_execution_profile`, `resolve_launch_profile` and the run-creation site where `options` is composed, which is where a resolved request must be written (E-03); `agent_workflows/runner_profiles.py` holds `ALLOWED_PROFILE_KEYS`, `parse_profile` and `_reject_unknown_keys`, which is where a profile field must be declared and validated (E-03); `tests/test_host_sandbox_profile.py` is the existing suite pinning the capability and resolver contract this plan makes reachable, and E-05 must show it still passes; `tests/test_hardened_profile_request.py` is the new suite for the request path, the deterministic refusal, and the no-lane refusal (E-05); `docs/runner-profiles.md` is the user-facing surface where a profile field and its platform limit must be stated together (E-04). ADDED IN REVIEW: `tests/test_runner_profiles.py` and `tests/test_runner_profiles_e2e.py` are DECLARED because each asserts the sorted `ALLOWED_PROFILE_KEYS` list LITERALLY as a deliberate security fence, so the field cannot land without editing both, and the e2e file additionally binds that list to `docs/runner-profiles.md`. Omitting them made the profile-field outcome unimplementable as scoped, and editing them undeclared would have tripped the finalize scope gate. Under the NEITHER outcome the two `agent_workflows/` paths and the two pinned test files may finish UNCHANGED and the recording goes into the module contract or the spec; a declared path left untouched is the expected outcome there, acknowledged with `--scope-ack` at finalize rather than papered over with a token edit.
- Under-scope, stated rather than left as `none`: this plan does not add a portable confinement mechanism, does not change the default profile, does not alter sandbox construction or the probe ladder, does not give agy a profile system, does not touch the two declared-unprobed capabilities, and does not extend the capability snapshot's shape. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with both summary lines pasted AND the failing node ids from each. Re-measured at review HEAD `261a72a2`: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, failing at `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (another party's gitignored `opencode-recovery/` tree; pre-existing, do NOT fix, do NOT touch that tree). The plan's `1 failed, 5648 passed` blaming `test_orchestrator_retirement` is superseded: that file passes (`112 passed`). The criterion is an EMPTY after-minus-before failure set compared BY NODE ID, never an absolute count.
- `tests/test_host_sandbox_profile.py` re-run with ITS OWN summary line pasted (measured `27 passed`), since it pins the contract this plan makes reachable.
- `tests/test_runner_profiles.py` AND `tests/test_runner_profiles_e2e.py` re-run with their OWN summary lines pasted, because both assert the sorted `ALLOWED_PROFILE_KEYS` list LITERALLY and both must be edited for the field to land. Paste the diff of each literal alongside the in-test justification written for the new key, following the `verify_with` precedent.
- PROOF THE SECURITY FENCE WAS NOT LOOSENED: show that both assertions remain LITERAL sorted-list comparisons (not subset or membership checks), and that `ALLOWED_PROFILE_KEYS & FORBIDDEN_PROFILE_KEYS` is still empty.
- PROOF THE FIELD'S VALUE SPACE IS CLOSED: show that a path, an argv fragment, and a permission expression are all REFUSED by `parse_profile`, since `permission`/`permissions` are forbidden by name and this field sits next to that boundary.
- A DETERMINISTIC REFUSAL TEST built from a constructed all-False `HostSandboxCapabilities`, NOT from finding an unsupported host. A skip is not a pass and must not be reported as one.
- A DEFAULT-PATH INVARIANCE CHECK: an invocation requesting nothing produces identical `argv`.
- THE NO-LANE REFUSAL covered, since a request path makes that branch reachable for the first time.
- NEGATIVE PROOF that no parallel key was introduced: show the searches for a second profile key and for any new sandbox code path.
- Under the profile-field outcome, proof that an EXISTING on-disk `runner_profiles` config still loads unchanged, INCLUDING a `schema_version: 1` document, since `SUPPORTED_SCHEMA_VERSIONS = {1, 2}` and the module guarantees a v1 document keeps loading byte-for-byte with nothing migrated. State explicitly that no version bump was made, because the reader is version-agnostic about a FIELD.
- PROOF THE REQUEST IS RESOLVED AT THE EXISTING SEAM: show it flows through `resolve_launch_profile` / `runner_profiles.resolve` into the frozen `state["options"]` snapshot at run creation, and that resolution still happens BEFORE the run directory exists (a malformed config must leave no run id or partial state) and is FROZEN ONCE (a later edit to `runner-profiles.json` must not change an existing run).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`host_sandbox_profile.py`'s MODULE CONTRACT is the authoritative prose on what the hardened profile guarantees, and it already states the void-on-unsupported-host rule (`:56-62`) and the executed-not-inspected rule (`:64-75`). It must gain one sentence saying HOW hardened mode is requested (or that it deliberately cannot be), because a contract describing a capability with no reachable request path is incomplete in exactly the way that produced this item.

`docs/runner-profiles.md` is user-facing AND IS TEST-BOUND, which makes this edit mandatory rather than editorial: `tests/test_runner_profiles_e2e.py` asserts the allowed-key list "is exactly what the doc lists" and a sibling test asserts the doc contains no em or en dash. So under the profile-field outcome the doc MUST gain the field in the same change or the suite fails, and the no-dash rule is enforced by a test rather than only by convention.

It must name the request surface, the Linux/Landlock-only limit, and the refuse-not-degrade behavior TOGETHER, in that order, so a macOS reader learns the limit before deciding to use it. It must ALSO state that the agy host reads no profile keys, so a hardened request there is silently ignored rather than refused; a user who believes a boundary exists when it does not is the exact harm the refuse-not-degrade rule protects against, and omitting it from the doc would recreate that harm one host over.

No spec change is expected: `25kzda` 5.2 covers the runner-safety capabilities (`supports_commit_gateway`, `supports_deny_push`), not the sandbox profile's request path. If the executor finds spec text ASSERTING that the hardened profile is requestable today, that is a false claim and must be corrected in the same change; declare the spec file in `Scope-Paths` before editing it and say why in this section, per the spec-amendment rule.

## Open questions

### OQ-01: Which request surface should the hardened profile get, given that its enforcement is Linux-only?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: THE PER-PROFILE `runner_profiles` FIELD. The hardened profile becomes requestable by an opt-in field the user writes into their OWN config, not by a CLI flag and not by leaving it unreachable.
  WHY THIS SURFACE AND NOT A FLAG, which is the substance of the question rather than a cost trade: a documented CLI flag on a cross-platform tool READS AS A CROSS-PLATFORM GUARANTEE, and this enforcement is Linux-only against a stated bar of macOS 100% MUST and Windows 95%, so the flag would be typed on macOS where `select_execution_profile` can only REFUSE (correctly, since it refuses rather than silently degrading). A field in the user's own config makes a materially weaker and honest promise: you asked for it, locally, on this machine. The schema already carries it safely (`ALLOWED_PROFILE_KEYS`, `runner_profiles.py:190`, with `_reject_unknown_keys` at `:639`), so an unknown key is refused rather than ignored.
  THE MAINTAINER ASKED FOR A RECOMMENDATION AND LEANED TOWARD LEAVING IT, so the reasoning that changed the answer is recorded. FIRST, a correction: the maintainer said they lacked a way to mark an item as a "meh, maybe someday" without misusing low priority. That state EXISTS and is `parked`, which `.aw/records/backlog/README.md:17` defines as an uncommitted "maybe" hidden from the default board and excluded from `aw attention` until `--all`. SECOND, the decisive argument: the EXPENSIVE PARTS ARE ALREADY BUILT AND PASSING. The sandbox enforcement works, verified on this Linux host at HEAD by an EXECUTED probe rather than an inspection (`detect_host_capabilities("opencode")` returns `supports_os_sandbox=True`, `sandbox_mechanism="landlock"`, with the probe note recording that a write outside the allowed root was actually refused), and the path is already tested. What is missing is only a way to say yes. So the cheapest option was never "do nothing"; it was the field.
  THIRD, WHY NOT DELETE IT: this is a working, tested control that physically prevents an agent writing outside its allowed root, in a system whose premise is running agents unattended inside real repositories. Deleting discards finished work and is the only option expensive to reverse, and the occasion for wanting it is not predictable in advance.
  WHAT DOES NOT CHANGE, restated because it bounds the build: the DEFAULT stays `default` (unprotected) on every platform. A Linux-only default would make every macOS and Windows run refuse, and `select_execution_profile` deliberately refuses rather than degrading. This plan still changes NOTHING about what the sandbox does once selected and adds no second enforcement mechanism.
  ONE CAUTION CARRIED FORWARD from the question as authored: this probe ladder has already produced a fail-OPEN inference once (`909eb007`), which is why detection is an executed probe today. The new field must not reintroduce an inference; it is a REQUEST, and the existing probe remains the authority on whether the request can be honored.
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

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL output of the searches proving no setter and no CLI flag exists at your HEAD, and show that the one `options["execution_profile"]` hit is inside a comment by pasting the surrounding lines. THEN paste the ACTUAL output of `detect_host_capabilities("opencode")` on your host, showing `supports_os_sandbox`, `sandbox_mechanism` and `probe_notes`. State in one sentence whether your host can enforce, since that determines what V-05 can demonstrate.
  - Observed evidence: PREMISE RE-MEASURED AT EXECUTION HEAD `340c9174` AND TRUE, against the pristine HEAD copy of the file (`git show HEAD:agent_workflows/oc_runipd.py`) so the measurement is of the state BEFORE this plan's own edits:

    ```
    $ grep -n 'options\["execution_profile"\] *=' <HEAD copy of oc_runipd.py>
    (assignment count: 0)
    $ grep -n 'options\["execution_profile"\]' <HEAD copy of oc_runipd.py>
    5607:    # `options["execution_profile"]` is explicitly "hardened": `select_execution_profile`
    $ grep add_argument <HEAD copy of oc_runipd.py> | grep -i 'sandbox\|harden'
    (flag count: 0)
    ```

    ONE HIT, ZERO ASSIGNMENTS, AND THE HIT IS A COMMENT. Surrounding lines at HEAD line 5607 (note the leading `#` on every line, and that the enclosing block is prose describing the seam):

    ```
        # This is the ONLY hardened-mode seam in the launch path and it is inert unless
        # `options["execution_profile"]` is explicitly "hardened": `select_execution_profile`
        # returns "default" for unset/"default", so `argv` below is untouched and the default
        # launch is byte-for-byte what it was before this phase.
    ```

    SYMBOLS RE-LOCATED BY NAME, NOT BY THIS PLAN'S LINE NUMBERS (they had drifted as the plan warned): `_apply_execution_profile` at `oc_runipd.py:5055` at HEAD (the plan said `:4992`/`:5030`), `resolve_launch_profile` at `:3230` (plan said `:2613`), `select_execution_profile` at `host_sandbox_profile.py:1110`.

    THIS HOST CAN ENFORCE. Actual output of `detect_host_capabilities("opencode")`:

    ```
    supports_os_sandbox = True
    sandbox_mechanism = 'landlock'
    probe_notes = {
      "landlock": "landlock jail enforced: write outside the allowed root was refused",
      "supports_commit_gateway": "DECLARED, NOT PROBED: ...",
      "supports_deny_push": "DECLARED, NOT PROBED: ...",
      "supports_fresh_verifier_session": "fresh-verifier separation enforced: a distinct-identity run finalized and a reused-identity run was REFUSED"
    }
    ```

    IN ONE SENTENCE: this Linux host's EXECUTED probe reports it CAN enforce the sandbox (mechanism `landlock`, with the note recording that a write outside the allowed root was actually refused), so the dead branch guarded working enforcement and V-05's capable-host assertions are demonstrable here rather than merely constructed. E-01's two facts therefore both hold: the key had no writer and no flag, and the capability it guards is real.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the candidate table itself. For EACH candidate it must state, in its own cells, the implied portability claim and the exact behavior on a host whose probe returns False. Confirm in one sentence that NO candidate was selected in E-02 and that no second enforcement mechanism was proposed. If the table names fewer than the four candidates E-02 lists, say which was dropped and why.
  - Observed evidence: ALL FOUR CANDIDATES ARE PRESENT; none was dropped. The table below is E-02's analysis as performed at this HEAD.

    | Candidate | Discoverability | Portability claim it IMPLIES to a user | Exact behavior on a host whose probe returns False |
    |---|---|---|---|
    | (1) BARE CLI FLAG (`--hardened` / `--execution-profile hardened`) | HIGHEST: appears in `--help`, in docs, and in every copied command line | THE WORST, and this is the substantive objection rather than a cost one: a documented flag on a cross-platform tool reads as a CROSS-PLATFORM GUARANTEE. It would be typed on macOS, where the enforcement does not exist, against a stated bar of macOS 100% MUST and Windows 95% | HARD REFUSAL. `select_execution_profile` raises `HardModeUnavailableError` (`host_sandbox_profile.py`, verified at HEAD), so the run fails outright. Correct behavior, but the user was invited to type it by the flag's own existence |
    | (2) PER-PROFILE FIELD in `runner_profiles` | MEDIUM: found by reading `docs/runner-profiles.md` or an existing config; nothing surfaces it unbidden | MUCH WEAKER AND HONEST: "I wrote this into my own local config, on this machine." The store is USER-LOCAL and per-machine by construction (`config_dir`, never committed), so the field's scope of promise matches the enforcement's scope of reality | HARD REFUSAL, identical mechanism (the same resolver, reached through the same single seam). An operator who never writes the field never meets it |
    | (3) BOTH, the flag overriding the field | Same as (1), since the flag dominates | Same as (1): adding a weaker surface beside a flag does not weaken the flag's implied promise. It also requires a precedence tier this module's own rule demands ("AN EXPLICIT FLAG ALWAYS WINS", because a stored default overriding a flag "would make the flag a lie") | HARD REFUSAL, but with TWO paths to reach it, so the diagnostic must say which surface asked |
    | (4) NEITHER: leave it unreachable and record why | ZERO by construction | NONE, which is the only claim that cannot be wrong. But it leaves a working, probe-verified, tested control physically unusable, and leaves the next reader to grep for a setter exactly as this graduation had to | N/A: nothing can request it, so no host ever refuses |

    NO CANDIDATE WAS SELECTED IN E-02, and no second enforcement mechanism was proposed: the table enumerates REQUEST surfaces for the mechanism that already exists, and portable write-confinement (separate clone, per-run user account, detect-and-refuse) remains research prompt `q65sz3`'s subject, which is still `- Status: todo` at this HEAD. The winner came from OQ-01's RECORDED MAINTAINER DECISION of 2026-09-08 (candidate 2, the per-profile field), not from this item. The fail-closed behavior is uniform across every candidate and was NOT softened anywhere: every row that can be requested at all refuses rather than degrading.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the writer code and show it sets the EXISTING `options["execution_profile"]` key. Paste NEGATIVE proof that no parallel key and no second sandbox code path were added (show the searches). Paste the statement at the site recording that this is opencode-only, with the measurement backing it, AND the statement that an agy run therefore IGNORES rather than refuses the request. Show the request resolves through `resolve_launch_profile`/`runner_profiles.resolve` into the FROZEN `state["options"]` snapshot, with resolution still happening before the run directory exists.
    Under the profile-field outcome, additionally paste: the `ALLOWED_PROFILE_KEYS` diff; the validation added to `parse_profile`; the EDITED LITERAL in BOTH pinned tests (`tests/test_runner_profiles.py` and `tests/test_runner_profiles_e2e.py`) together with the in-test justification written for the new key, following `verify_with`'s precedent; proof both assertions remain LITERAL sorted-list comparisons rather than subset checks; proof `ALLOWED_PROFILE_KEYS & FORBIDDEN_PROFILE_KEYS` is still empty; proof a path, an argv fragment and a permission expression are all REFUSED as values; and proof a `schema_version: 1` document still loads with NO version bump made.
    Under the NEITHER outcome, state plainly that no wiring was performed and point at V-04's recording as the whole deliverable. Note that OQ-01 is resolved to the profile field, so this branch should not be taken without a new maintainer decision.
  - Observed evidence: THE PROFILE-FIELD OUTCOME WAS EXECUTED, per OQ-01's recorded maintainer decision. The NEITHER branch was not taken.

    (a) THE WRITER SETS THE EXISTING KEY, in `initialize_run`'s `host_options` (`agent_workflows/oc_runipd.py`), with no parallel key:

    ```python
            **(
                {"execution_profile": resolved_launch.execution_profile}
                if resolved_launch.execution_profile is not None
                else {}
            ),
    ```

    The audit copy in `launch_profile_record` is separate from the read path and equally conditional:

    ```python
        if resolved.execution_profile is not None:
            record["execution_profile"] = resolved.execution_profile
        return record
    ```

    (b) NEGATIVE PROOF, NO PARALLEL KEY AND NO SECOND SANDBOX CODE PATH. Counted with the opening paren so a bare import is not counted:

    ```
    $ grep -o 'select_execution_profile(' agent_workflows/oc_runipd.py | wc -l
    1
    $ grep -o '_apply_execution_profile(' agent_workflows/oc_runipd.py | wc -l
    2      # the definition plus ONE invocation in the launch path
    $ grep -o 'enter_sandbox(' agent_workflows/oc_runipd.py | wc -l
    1
    ```

    `_apply_execution_profile`'s LOGIC is unchanged (`git diff` touches only its docstring and the comment above its call site). The near-miss names `sandbox_profile`, `hardened_mode`, `execution-profile` and `use_sandbox` are all absent as string keys. Both facts are pinned by `DefaultPathInvarianceTests::test_no_PARALLEL_key_and_no_second_sandbox_code_path_were_added`.

    (c) THE OPENCODE-ONLY STATEMENT AT THE SITE, WITH ITS MEASUREMENT, AND THE AGY-IGNORES CONSEQUENCE NAMED EXPLICITLY (quoted from the writer's own comment):

    > OPENCODE ONLY BY CONSTRUCTION. `agy_runipd` contains zero references to `execution_profile`, `host_sandbox_profile`, `runner_profiles`, `resolve_launch_profile` or `launch_profile` (measured at execution HEAD), so it has no seam to carry this and an agy run SILENTLY IGNORES a stored request rather than refusing it. That is degradation-by-omission, the very thing `select_execution_profile` refuses by raising, so it is stated here and in `docs/runner-profiles.md` instead of being left for an operator to discover. Making agy refuse is a change to that host and is deliberately not smuggled in here.

    The measurement backing it, re-run at execution HEAD (all five identifiers, all zero):

    ```
    execution_profile: 0
    host_sandbox_profile: 0
    runner_profiles: 0
    resolve_launch_profile: 0
    launch_profile: 0
    ```

    Pinned by `OpencodeOnlyByConstructionTests::test_the_agy_host_reads_no_profile_identity_at_all`, which fails loudly if any of the five ever appears there.

    (d) THE REQUEST RESOLVES AT THE EXISTING SEAM, FROZEN ONCE, BEFORE THE RUN DIRECTORY EXISTS. Driven end to end against the REAL CLI with a real temporary store (no mocked layer), output verbatim:

    ```
    rc = 0
    options['execution_profile'] = 'hardened'
    launch_profile.execution_profile = 'hardened'
    launch_profile.provenance['execution_profile'] = 'profile'
    after store edit, frozen execution_profile = 'hardened'
    malformed rc = 2
    stderr tail: runipd: runner profile: unknown execution profile '/etc/passwd'; expected one of ['default', 'hardened']. 'hardened' is enforced by the OPERATING SYSTEM and is Linux/Landlock only, so a host whose executed probe cannot enforce it REFUSES the run rather than silently running unsandboxed.
    new run dirs created by the refusal: []
    plain rc = 0 | 'execution_profile' in options: False | in launch_profile: False
    ```

    Three properties are proven by those lines in order: it flows through `resolve_launch_pair` / `runner_profiles.resolve` into the frozen `state["options"]` (line 2) with its tier recorded (line 4); a LATER EDIT to `runner-profiles.json` does NOT change the in-flight run (line 5, still `hardened` after the store was repointed at a profile requesting nothing); and a MALFORMED value refuses at exit 2 leaving NO run id and NO partial state (`new run dirs created by the refusal: []`), because `resolve_launch_pair` is still the FIRST statement of `initialize_run`. The last line is the default-path shape check: a profile requesting nothing freezes neither key.

    (e) `ALLOWED_PROFILE_KEYS` DIFF:

    ```diff
     ALLOWED_PROFILE_KEYS: frozenset = frozenset(
    -    ("runner", "model", "variant", "agent", "validate", "verify_with")
    +    (
    +        "runner",
    +        "model",
    +        "variant",
    +        "agent",
    +        "validate",
    +        "verify_with",
    +        "execution_profile",
    +    )
     )
    ```

    (f) THE VALIDATION ADDED TO `parse_profile`, which delegates to a named validator so the closed vocabulary has one home:

    ```python
        execution_profile = raw.get("execution_profile")
        if execution_profile is not None:
            execution_profile = validate_execution_profile_name(execution_profile)
    ```

    ```python
    def validate_execution_profile_name(value: Any) -> str:
        if not isinstance(value, str):
            raise ProfileSchemaError(... "a NAME from a closed vocabulary" ...)
        if value not in EXECUTION_PROFILE_NAMES:
            raise ProfileSchemaError(f"unknown execution profile {value!r}; expected one of "
                                     f"{list(EXECUTION_PROFILE_NAMES)}. ...")
        return value
    ```

    (g) BOTH PINNED SECURITY TESTS EDITED, WITH AN IN-TEST JUSTIFICATION FOLLOWING `verify_with`'S PRECEDENT, AND BOTH ASSERTIONS STILL LITERAL SORTED-LIST COMPARISONS. `tests/test_runner_profiles.py::test_no_arbitrary_argv_or_credential_field_is_persistable` now reads:

    ```python
            self.assertEqual(
                sorted(RP.ALLOWED_PROFILE_KEYS),
                [
                    "agent",
                    "execution_profile",
                    "model",
                    "runner",
                    "validate",
                    "variant",
                    "verify_with",
                ],
            )
    ```

    preceded by the justification (abbreviated here; the full three-point argument is in the test): "`execution_profile` was ADDED by `hardreach` Order 01 (`n5qca5`) and is listed here deliberately, WITH THE REASON IT DOES NOT WIDEN THIS FENCE, because it sits nearer the boundary than any field before it ... 1. ITS VALUE SPACE IS A CLOSED TWO-MEMBER ENUM ... 2. IT CANNOT DESCRIBE A PERMISSION. It says WHETHER to request the jail, never WHICH paths are writable ... 3. IT IS A REQUEST, NOT A CAPABILITY CLAIM."

    `tests/test_runner_profiles_e2e.py::test_every_field_the_doc_says_is_refused_really_is` likewise keeps a literal comparison, and the doc binding was STRENGTHENED rather than loosened (it now asserts each allowed key is NAMED in the doc):

    ```python
            allowed = ["agent", "execution_profile", "model", "runner", "validate", "variant", "verify_with"]
            self.assertEqual(sorted(rp.ALLOWED_PROFILE_KEYS), allowed)
            for key in allowed:
                with self.subTest(documented=key):
                    self.assertIn(f"`{key}`", self.text, ...)
    ```

    NEITHER ASSERTION WAS WEAKENED INTO A SUBSET OR MEMBERSHIP CHECK: both remain `assertEqual(sorted(...), [literal list])`, which is the control. Confirmed by the diff above, where the only change to each is the added member and the added reason.

    (h) `ALLOWED_PROFILE_KEYS & FORBIDDEN_PROFILE_KEYS` IS STILL EMPTY: `frozenset()`, asserted both by the pinned test (unchanged line) and again from the other direction by the new suite, which additionally asserts `permission`, `permissions`, `args`, `argv` and `env` are each still in FORBIDDEN and still absent from ALLOWED.

    (i) A PATH, AN ARGV FRAGMENT AND A PERMISSION EXPRESSION ARE ALL REFUSED as values. Actual refusals, measured:

    ```
    refused '/etc/passwd'                       -> unknown execution profile '/etc/passwd'; expected one of ['default', 'hardened']
    refused '--dangerously-skip-permissions'    -> unknown execution profile ...
    refused 'write:/tmp'                        -> unknown execution profile ...
    refused 'HARDENED'                          -> unknown execution profile ...
    refused ''                                  -> unknown execution profile ''
    refused 'hardened '                         -> unknown execution profile 'hardened '
    refused {'a': 1}                            -> 'execution_profile' must be one of ['default', 'hardened'] (a NAME from a closed vocabulary)
    refused ['hardened']                        -> (same)
    refused True                                -> (same)
    refused 1                                   -> (same)
    ```

    The new suite's `test_a_path_an_argv_fragment_and_a_permission_expression_are_all_REFUSED` pins fifteen such shapes, including a lane root, a relative path, a shell fragment and an edit-permission expression.

    (j) A `schema_version: 1` DOCUMENT STILL LOADS, WITH NO VERSION BUMP MADE. Asserted by `test_a_schema_version_1_document_still_loads_with_NO_version_bump`: a v1 document carrying the new field loads, keeps declaring `schema_version == 1`, and resolves the request; a v1 document WITHOUT the field round-trips byte-identically through `from_document(...).to_document()`. `SCHEMA_VERSION` is still `2` and `SUPPORTED_SCHEMA_VERSIONS` is still `{1, 2}`; NO BUMP WAS MADE, because the reader is deliberately version-AGNOSTIC about a FIELD (the module records exactly this reasoning for `verify_with`, and F-15 corrected the plan's own stale claim that the version was 1).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the documentation or module-contract text as written. Confirm by quoting it that the platform limit appears together with the capability and NOT after it, and that the refuse-not-degrade behavior is stated. Paste a search showing the prose contains no em or en dash. Under the NEITHER outcome, quote the sentence recording the deliberate unreachability and its cited reason.
  - Observed evidence: A WIRING OUTCOME, so the recording documents HOW to request it, its platform limit, and its refusal behavior. Two artifacts were written.

    (a) `docs/runner-profiles.md`, the USER-FACING surface, as written:

    > ## Asking for the OS sandbox (Linux only, and it refuses elsewhere)
    >
    > A profile can request the HARDENED execution profile, in which the operating system, not a prompt and not a git hook, denies the agent any write outside its own lane worktree. THIS ENFORCEMENT IS LINUX ONLY: it is built on Landlock, so on macOS, on Windows, and on any Linux host where the sandbox probe cannot actually build a jail, requesting it REFUSES the run rather than running without protection.
    >
    > ```json
    > {
    >   "schema_version": 2,
    >   "profiles": {
    >     "jail": {"runner": "oc", "model": "vendor/deep-9", "execution_profile": "hardened"}
    >   }
    > }
    > ```
    >
    > Then `aw oc run as jail <selector>` runs the agent turn inside the sandbox. Omitting the field, or writing `"default"`, is the normal state and means no OS confinement, which is what every store written before this field does.
    >
    > - THE PLATFORM LIMIT AND THE CAPABILITY ARE ONE FACT, not a caveat you read afterwards. What you get is a Linux/Landlock write boundary, and nothing at all on a host that cannot enforce it.
    > - AN UNSUPPORTED HOST REFUSES; it never quietly downgrades. `aw` fails the run with a message naming your platform and what the probe found. That is deliberate: if you asked for a jail and silently got none, you would proceed believing a boundary existed, which is worse than an error.
    > - SUPPORT IS DECIDED BY AN EXECUTED PROBE, not by inspecting your kernel version or looking for a binary. [...]
    > - IT REQUIRES AN ISOLATED LANE, which is the default for `aw oc run`. [...] requesting hardened mode there refuses too.
    > - IT IS A REQUEST, NOT A SETTING THAT WIDENS ANYTHING. The field chooses between two names; it cannot name a path, a root, or a permission. [...]
    > - IT IS OPENCODE ONLY, AND ANTIGRAVITY IGNORES IT RATHER THAN REFUSING. `aw agy run` reads no launch profile at all, so a `jail` profile shared with that host runs UNSANDBOXED AND SILENT there. That is the one place in this feature where a request is dropped instead of refused, and it is stated here because believing in a boundary you do not have is exactly the harm the refusal above prevents. [...]
    > - THERE IS NO COMMAND-LINE FLAG, on purpose. A `--hardened` flag on a cross-platform tool reads as a cross-platform promise, and this one is Linux only. [...]
    > - THE DEFAULT DOES NOT CHANGE, on any platform. [...]

    THE PLATFORM LIMIT APPEARS TOGETHER WITH THE CAPABILITY AND NOT AFTER IT, confirmed by QUOTING ITS POSITION rather than merely its presence: it is in the SECTION HEADING itself ("Linux only, and it refuses elsewhere"), and then in the FIRST PARAGRAPH, in the same sentence that describes what the capability does ("THIS ENFORCEMENT IS LINUX ONLY"). So a macOS reader meets the limit before the JSON example, not after it. The new suite asserts this as a POSITION (`"LINUX ONLY" in first_para`), not as presence anywhere in the file, so a later edit that demoted it to a trailing caveat would fail.

    REFUSE-NOT-DEGRADE IS STATED, twice and unambiguously: "requesting it REFUSES the run rather than running without protection" and "AN UNSUPPORTED HOST REFUSES; it never quietly downgrades".

    NO EM OR EN DASH, measured on the section and on the whole file:

    ```
    em dash in section: False | en dash: False
    em dash whole doc: False | en dash whole doc: False
    $ docs_check.check_doc(Path('docs/runner-profiles.md'))
    docs_check findings: []
    ```

    (b) `host_sandbox_profile.py`'s MODULE CONTRACT gained the sentence the spec-sync section required, since a contract describing a capability with no reachable request path is incomplete in exactly the way that produced this item. Quoted as written:

    > HOW HARDENED MODE IS REQUESTED, which this contract previously did not say and which made the capability unreachable in practice (`hardreach` Order 01, `n5qca5`). An operator asks for it with a per-profile `execution_profile: "hardened"` field in their own `runner-profiles.json` (`runner_profiles.ALLOWED_PROFILE_KEYS`); `oc_runipd.resolve_launch_pair` resolves it and `initialize_run` freezes it into `state["options"]["execution_profile"]`, which is the key `_apply_execution_profile` reads before calling `select_execution_profile` below. Until that plan NOTHING in the package wrote that key, so this whole module's enforcement was correct, tested, and unreachable from any real invocation.
    >
    > THERE IS DELIBERATELY NO CLI FLAG, and the reason belongs in this contract because it bounds the guarantee. A documented `--hardened` flag on a cross-platform tool reads as a cross-platform GUARANTEE, and this one is Linux only against a stated platform bar of macOS 100% and Windows 95% [...] The maintainer's decision is recorded as `n5qca5` OQ-01. The DEFAULT is unchanged on every platform (Phase 6.4) [...]
    >
    > OPENCODE ONLY, AND THE OTHER HOST IGNORES RATHER THAN REFUSES. `agy_runipd` reads no launch-profile identity at all, so a stored request is INERT there: an agy run proceeds UNSANDBOXED AND SILENT. That is degradation-by-omission, the precise failure this module refuses by raising [...]

    Machine-checked presence of all four required facts in that contract:

    ```
    module contract mentions execution_profile: True
    module contract mentions runner-profiles.json: True
    module contract NO CLI FLAG: True
    module contract IGNORES RATHER THAN REFUSES: True
    ```

    NO CROSS-PLATFORM ENFORCEMENT IS CLAIMED ANYWHERE in either artifact, and the agy silent-ignore consequence is named in BOTH, per F-16.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of the new test module, including the test that constructs an all-False `HostSandboxCapabilities` and asserts `HardModeUnavailableError` (quote that assertion, so it is visibly deterministic rather than host-dependent) and the no-lane `SandboxProfileError` test. Paste the default-argv invariance assertion and its result. Paste `tests/test_host_sandbox_profile.py`'s OWN summary line (measured `27 passed` at review HEAD), AND the OWN summary lines of `tests/test_runner_profiles.py` and `tests/test_runner_profiles_e2e.py`, since both had to be edited for the field to land and a green run there is the proof the security fence was updated rather than loosened. THEN paste the BARE `python3 -m pytest` summary lines from before and after AND the failing node ids from each, stating the failure-set delta BY NODE ID; an empty delta is the criterion. Confirm the pre-existing `test_reporting_contract::ParityTests::test_only_expected_files_contain_the_full_contract_prose` failure appears in BOTH runs, was not "fixed", and that the gitignored `opencode-recovery/` tree was not touched. If any test SKIPPED on your host say so rather than counting it as a pass.
  - Observed evidence: THE NEW MODULE, all 20 tests PASSING, per node id (no skips anywhere in this module; every assertion runs on every platform):

    ```
    $ python3 -m pytest tests/test_hardened_profile_request.py -o addopts="" -v
    ExecutionProfileFieldTests::test_the_field_round_trips_through_the_real_schema PASSED
    ExecutionProfileFieldTests::test_the_vocabulary_is_closed_and_matches_the_resolver PASSED
    ExecutionProfileFieldTests::test_a_path_an_argv_fragment_and_a_permission_expression_are_all_REFUSED PASSED
    ExecutionProfileFieldTests::test_the_storable_surface_did_not_widen_beyond_this_one_name PASSED
    ExecutionProfileFieldTests::test_a_schema_version_1_document_still_loads_with_NO_version_bump PASSED
    ExecutionProfileResolutionTests::test_a_named_profile_and_a_default_profile_both_supply_the_request PASSED
    ExecutionProfileResolutionTests::test_absent_leaves_the_resolved_record_AND_the_provenance_map_unchanged PASSED
    ExecutionProfileResolutionTests::test_there_is_NO_cli_flag_and_the_resolver_takes_no_explicit_tier PASSED
    RequestReachesTheResolverTests::test_the_frozen_option_is_what_the_seam_passes_to_the_resolver PASSED
    RequestReachesTheResolverTests::test_the_whole_chain_from_a_real_store_to_the_frozen_option PASSED
    RequestReachesTheResolverTests::test_the_audit_record_omits_the_key_when_nothing_asked PASSED
    RefusalTests::test_an_unsupported_host_refuses_DETERMINISTICALLY_on_every_platform PASSED
    RefusalTests::test_the_request_path_refuses_on_an_unsupported_host_and_spawns_NOTHING PASSED
    RefusalTests::test_a_request_with_NO_LANE_refuses_because_there_is_no_boundary PASSED
    RefusalTests::test_an_unknown_requested_name_refuses_even_on_a_capable_host PASSED
    DefaultPathInvarianceTests::test_requesting_nothing_produces_the_IDENTICAL_argv PASSED
    DefaultPathInvarianceTests::test_no_PARALLEL_key_and_no_second_sandbox_code_path_were_added PASSED
    OpencodeOnlyByConstructionTests::test_the_agy_host_reads_no_profile_identity_at_all PASSED
    OpencodeOnlyByConstructionTests::test_the_user_facing_doc_states_the_limit_the_refusal_and_the_silent_agy_case PASSED
    OpencodeOnlyByConstructionTests::test_the_module_contract_says_HOW_hardened_mode_is_requested PASSED

    20 passed in 0.20s
    ```

    THE REQUEST IS CONSUMED, NOT MERELY STORED. `test_the_frozen_option_is_what_the_seam_passes_to_the_resolver` SPIES on `select_execution_profile` and asserts the frozen value arrives there, which is the assertion a store-and-ignore implementation would fail:

    ```python
            self.assertEqual(
                seen,
                ["hardened"],
                "the frozen request never reached select_execution_profile, so the field is stored "
                "and inert: exactly the defect this plan removes, one layer further along",
            )
            self.assertEqual(out[0], "JAILED", "the launch argv was not wrapped")
    ```

    THE DETERMINISTIC REFUSAL, built from a CONSTRUCTED all-False capability object and therefore host-independent. Quoted so its determinism is visible: there is no `skipIf`, no probe call, and no platform branch in it.

    ```python
        def test_an_unsupported_host_refuses_DETERMINISTICALLY_on_every_platform(self):
            incapable = HostSandboxCapabilities()
            self.assertFalse(incapable.supports_os_sandbox)
            with self.assertRaises(HardModeUnavailableError):
                select_execution_profile("hardened", incapable)
            # And it does NOT silently answer "default", which is the degradation the raise exists to
            # prevent: a caller who got "default" back would run unsandboxed believing it had asked.
            self.assertEqual(select_execution_profile(None, incapable), "default")
    ```

    Reached THROUGH the new request path too, with a `subprocess.Popen` tripwire proving nothing is spawned when the refusal fires (`test_the_request_path_refuses_on_an_unsupported_host_and_spawns_NOTHING`, asserting `spawned == []`).

    THE NO-LANE `SandboxProfileError`, reachable for the first time now a writer exists:

    ```python
                    with self.assertRaises(SandboxProfileError) as ctx:
                        driver._apply_execution_profile(
                            {"options": {"execution_profile": "hardened"}, "repo": str(Path(tmp)), "run_id": "r1"},
                            {"id6": "abc123"}, ["opencode", "run"], str(tmp), None,
                        )
            self.assertIn("isolated lane", str(ctx.exception))
    ```

    THE DEFAULT-ARGV INVARIANCE ASSERTION AND ITS RESULT. Run on a capable host (`supports_os_sandbox=True`, `landlock`) so it cannot pass by inability to sandbox, and for BOTH absent and explicit-`"default"` options:

    ```python
                    for options in ({}, {"execution_profile": "default"}):
                        with self.subTest(options=options):
                            out = driver._apply_execution_profile(...)
                            self.assertEqual(out, argv)
    ```

    Result: PASSED (`DefaultPathInvarianceTests::test_requesting_nothing_produces_the_IDENTICAL_argv`). The whole-run shape is confirmed independently by V-03(d)'s live driver line `plain rc = 0 | 'execution_profile' in options: False | in launch_profile: False`.

    THE FOUR SUITES' OWN SUMMARY LINES, each run separately:

    ```
    $ python3 -m pytest tests/test_hardened_profile_request.py -o addopts="" -q
    20 passed in 0.20s
    $ python3 -m pytest tests/test_host_sandbox_profile.py -o addopts="" -q
    29 passed in 0.70s
    $ python3 -m pytest tests/test_runner_profiles.py -o addopts="" -q
    72 passed in 0.32s
    $ python3 -m pytest tests/test_runner_profiles_e2e.py -o addopts="" -q
    34 passed in 3.81s
    ```

    A GREEN RUN IN THE TWO PINNED SUITES IS THE PROOF THE FENCE WAS UPDATED RATHER THAN LOOSENED, since both still assert `sorted(ALLOWED_PROFILE_KEYS)` against a LITERAL list (see V-03(g)) and the e2e one additionally binds that list to the doc. NOTE A DISCREPANCY WITH THE PLAN'S BASELINE, stated rather than smoothed over: the plan measured `27 passed` for `test_host_sandbox_profile.py` at review HEAD and it is `29 passed` here. That suite is NOT in this plan's diff (`git diff --name-only` below), so the two extra tests arrived from another change between review and execution; the relevant fact is that it passes.

    THE BARE SUITE, BEFORE AND AFTER, FULL SUMMARY LINES AND FAILING NODE IDS:

    ```
    BEFORE (at execution HEAD 340c9174, before any edit):
    1 failed, 7239 passed, 3 skipped, 2 xfailed, 3 warnings in 102.93s (0:01:42)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped

    AFTER (all edits in place):
    1 failed, 7259 passed, 3 skipped, 2 xfailed, 3 warnings in 94.39s (0:01:34)
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    ```

    FAILURE-SET DELTA BY NODE ID IS EMPTY: after-minus-before = {} (the single failing node id is identical in both runs). Passed count rose 7239 -> 7259, exactly the 20 tests this plan added. Skips and xfails are unchanged at 3 and 2, so nothing became conditionally skipped.

    THE PRE-EXISTING FAILURE IS A DIFFERENT ONE FROM THE PLAN'S, AND THIS IS WORTH STATING PLAINLY. The plan (F-14) predicted `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by another party's gitignored `opencode-recovery/` tree. THAT TEST PASSES HERE: `python3 -m pytest tests/test_reporting_contract.py -o addopts="" -q` -> `45 passed in 15.35s`, and no `opencode-recovery/` tree exists in this lane, so the condition that caused it is absent. The failure actually present is `test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, and it is ENVIRONMENTAL rather than a regression: the test asserts that a NON-isolated turn carries no `OPENCODE_CONFIG_CONTENT` denial policy, and this lane's own agent turn was launched by the runner WITH that variable exported, which the test inherits through `os.environ`. Proven by the environment alone, with no code change:

    ```
    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    43 passed in 4.84s
    $ python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q        # variable present
    1 failed, 42 passed in 4.73s
    ```

    It is therefore pre-existing (present in the BEFORE run, taken before any edit), unrelated to this plan's files, and I did NOT "fix" it; it is filed as a defect-report finding instead. THE GITIGNORED `opencode-recovery/` TREE WAS NOT TOUCHED, and could not have been: it does not exist in this worktree (`ls opencode-recovery` -> no such file or directory), and no path under it appears in this plan's diff.

    NO TEST WAS REPORTED AS PASSING ON THE STRENGTH OF A SKIP. The 3 skipped in both runs are pre-existing and unchanged, and none of them is in this plan's suites: the new module has zero skips, and every capability-dependent assertion in it uses a CONSTRUCTED `HostSandboxCapabilities` rather than this host's probe.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. CORRECTED IN REVIEW: this paragraph previously said the plan "carries a BLOCKING open question (OQ-01) and therefore cannot execute past E-02", which contradicted the artifact itself, since all three questions read `- Blocking: no` and OQ-01 is `- Status: resolved` by a recorded maintainer decision of 2026-09-08. The stale sentence described the plan as authored BEFORE that answer arrived, and left as written it would have told an executor to stop at E-02 and wait for a decision that had already been made.
SO THE DECISION IS MADE AND E-03's OUTCOME IS KNOWN: the per-profile `runner_profiles` field. E-02 is therefore a RECORD-THE-ANALYSIS item, not a decision gate, and E-03 executes the profile-field branch. Its other two branches are retained only so the reasoning stays legible; an executor should not read them as live alternatives to choose between. E-01 and E-02 remain worth performing because they re-establish the premise at the executing HEAD, which is the check that caught the two stale claims in the backlog item.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Re-locate every symbol in `oc_runipd.py` by NAME before editing, because that file is under concurrent edit by live runs and its line numbers move by tens of lines per day. Paste ACTUAL test output; never claim a pass that was not run, and never report a host-dependent SKIP as a pass. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence. If OQ-01 resolves to NEITHER, the plan still finalizes normally: the deliverable is then E-04's recorded decision, which is a real outcome and not a withdrawal.
