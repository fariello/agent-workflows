# IPD: Require a positive driver attestation for the terminal finalize so stripping AW_EXECUTION_ROLE no longer grants the driver's authority

- Date: 2026-09-24
- Kind: child
- Concern: THE ONLY AUTHORITY CHECK ON THE TERMINAL TRANSITION IS THE ABSENCE OF A STRIPPABLE VARIABLE. `ipd_lifecycle.finalize` and `ipd_lifecycle.retire_orchestrator` both refuse with `ROLLUP_REFUSED_WORKER_ROLE` iff `worker_role_active(env)`, i.e. iff `AW_EXECUTION_ROLE=worker` is PRESENT. Nothing positive is ever required: there is no driver token anywhere in `agent_workflows` (grep for `driver_token|AW_DRIVER_TOKEN|driver.token` returns nothing). So a lane agent that runs `env -u AW_EXECUTION_ROLE python3 -m agent_workflows ipd finalize <id6> --apply` holds exactly the driver's authority, which is what run `run-20260917T210518Z-1714328` recorded (commit `575f0b32`, receipt consumed, driver's own `driver_finalize` then refused and stranded the lane). The code states the limit itself: "the env marker is a SELECTOR, not a boundary ... the measured incident DEFEATED it with `env -u AW_EXECUTION_ROLE`". The motivation for the habit is gone (root `conftest.py` now pops `AW_EXECUTION_ROLE`, so tests no longer need `env -u`), but the verb is still open to it.
- Scope: INVERT the default for the terminal transition. Inside a LANE WORKTREE (repo root under the checkout's `.aw/worktrees/`, or HEAD on an `aw/lane/*` branch) `finalize` and `retire_orchestrator` refuse UNLESS a per-run DRIVER ATTESTATION is presented and verifies; outside a lane (a human in the main checkout) behavior is unchanged. The driver mints a random token per run into its run dir (outside every lane), and passes it ONLY on its own finalize subprocess (`runner_shared.driver_finalize`) and its own in-process `retire_orchestrator` call, never into an agent child env. The existing env-marker gate stays as a first, cheap selector. The refusal text gains a sentence saying stripping the marker does not confer driver authority and corrupts the driver's transaction. OUT: `aw ipd begin` in a lane (OQ-02), an audit signal for forged finalize commits, and any OS-sandbox or separate-principal enforcement.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_driver_attestation_gate.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Set: roleattest
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: u27oh3
- From-Backlog: c4yixg
- Blocks-Release: next
- Priority: high
- Work-Kind: security

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog c4yixg; re-measured at HEAD 877545fc that `env -u AW_EXECUTION_ROLE ... ipd finalize --apply` run from a real `aw/lane/*` worktree passes the role gate (reaches plan resolution) while the marked form is refused, and that no positive driver attestation exists. Blocks-Release: next because a lane agent performing the driver-owned terminal transition forges execution evidence (an `executed` record and lifecycle commit the driver never verified) and consumes the driver's single-use receipt.

## Goal

Make the terminal lifecycle transition from inside a lane worktree require something the driver holds and an agent does not have in its environment, so the observed good-faith `env -u` workaround (and the `aw set executed` delegation into `finalize`) is refused, while the driver's own finalize and a human finalize from the main checkout keep working.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the gate in ipd_lifecycle

- [ ] E-01 Add `ipd_lifecycle.lane_worktree_active(repo_root: Path) -> bool`: True iff the resolved `repo_root` lies under `checkout_control_root(repo_root) / ".aw" / "worktrees"`, OR `git -C repo_root symbolic-ref --short -q HEAD` starts with `aw/lane/` (reuse `worktree_lease.lane_id_from_branch` for the branch test rather than a second prefix literal). Git failure / not a checkout returns False (unchanged behavior for temp-dir callers). Confirm the coordinator scratch worktree `finalize` creates for its own mutations is NEITHER under `.aw/worktrees/` NOR on an `aw/lane/*` branch; if it is, STOP and report, since the gate runs before it exists but a nested call would self-refuse.
  - Depends on: none
  - Expected outcome: pure predicate, unit-tested True for `.aw/worktrees/<id6>` and for a worktree elsewhere on `aw/lane/x`, False for the main checkout and a non-git dir.
  - Execution state: pending

- [ ] E-02 Add the attestation primitives in `ipd_lifecycle`: constant `DRIVER_ATTEST_ENV = "AW_DRIVER_ATTEST"` (value `<run-id>:<hex-token>`), `DRIVER_ATTEST_FILENAME = "driver-attest.token"`, `mint_driver_attestation(run_dir: Path) -> str` (writes `secrets.token_hex(32)` to `run_dir/DRIVER_ATTEST_FILENAME` with mode 0600 via `os.open(..., O_CREAT|O_EXCL|O_WRONLY, 0o600)`, returns `"<run_dir.name>:<token>"`), and `verify_driver_attestation(repo_root, value) -> tuple[bool, str]`. The verifier LOCATES THE FILE ITSELF from `checkout_control_root(repo_root) / ".aw/records/runs" / <run-id>` (never from a caller-supplied path), refuses a run-id containing a path separator or `..`, and compares with `hmac.compare_digest`. Cross-check the runs-root derivation against `runner_shared.state_root` (whose docstring says repository-backed projects resolve to `<repo>/.aw/records/runs`) and do not diverge from it.
  - Depends on: none
  - Expected outcome: mint then verify returns `(True, ...)`; wrong token, unknown run-id, `../` run-id, malformed value, and missing file each return `(False, <reason>)`.
  - Execution state: pending

- [ ] E-03 Gate `ipd_lifecycle.finalize` and `ipd_lifecycle.retire_orchestrator`: add keyword `driver_attestation: Optional[str] = None` to both; immediately AFTER the existing `worker_role_active` gate and before any other gate or mutation, if `lane_worktree_active(repo_root)` and the attestation (kwarg, else `env[DRIVER_ATTEST_ENV]` where `env` defaults to `os.environ`) does not verify, return `FinalizeResult(EXIT_CANNOT_RUN, None, <msg>, evidence, (ROLLUP_REFUSED_NO_DRIVER_ATTESTATION,))` with a new typed id `ROLLUP_REFUSED_NO_DRIVER_ATTESTATION = "no-driver-attestation"` added to the refusal vocabulary beside `ROLLUP_REFUSED_WORKER_ROLE`. The message must start with `LIFECYCLE_ROLE_ERROR`, name the lane worktree, and say plainly: unsetting `AW_EXECUTION_ROLE` does NOT grant driver authority; running this yourself consumes the driver's begin receipt and strands the lane; write the outcome file and stop. Update the "HONEST LIMIT" comment in `finalize` to describe the new layer and its limit. No change to `status_set` is needed because `status_set._delegate_plan_executed_to_finalize` calls `_life.finalize` and inherits the gate; verify that rather than assuming it.
  - Depends on: E-01, E-02
  - Expected outcome: from a lane root with no/invalid attestation both functions refuse with no side effect (no journal, no commit, receipt intact); from the main checkout they behave exactly as before.
  - Execution state: pending

- [ ] E-04 Thread the CLI: `ipd_lifecycle.run_finalize` reads nothing new from argv (NO `--driver-token` flag, because argv is visible in `ps` and in agent session logs); `finalize` reads `DRIVER_ATTEST_ENV` from its `env`. Confirm `run_finalize` passes the process env through (it currently calls `worker_role_active(os.environ)` itself) and that the `aw set executed` / `aw ipd set executed` route reaches the same check.
  - Depends on: E-03
  - Expected outcome: the only way to present the attestation to the CLI is the env var set by the driver on its own subprocess.
  - Execution state: pending

### Task group 2: plumb the token through the driver's legitimate call sites (both hosts)

- [ ] E-05 Mint and carry the token in `runner_shared`: in `runner_shared.initialize_run_core` (which creates the run dir and the `run_id` state) call `ipd_lifecycle.mint_driver_attestation(run_dir)` and keep the value in the DRIVER's in-memory run state (never in `os.environ`, never in `events.jsonl` or any written state file). Then: (a) `runner_shared.driver_finalize` gains `attestation: str | None` and sets `DRIVER_ATTEST_ENV` on the env it builds for its OWN `aw ipd finalize ... --dir <lane>` subprocess only (`env = dict(env_builder()); env[DRIVER_ATTEST_ENV] = attestation`); (b) both call sites in `runner_shared.execute_item_core` (the isolated one passing `finalize_repo = Path(work_dir)` and the in-place one passing `repo`) pass it; (c) the thin wrappers `oc_runipd.driver_finalize` and `agy_runipd.driver_finalize` forward the new argument (the `getattr(driver_module, "driver_finalize")` lookup in `execute_item_core` means both signatures must change together); (d) `runner_shared.dispatch_orchestrator_item`'s in-process `_lifecycle.retire_orchestrator(repo, plan_path, actor, ...)` call passes `driver_attestation=`. Enumerate with `grep -n "driver_finalize(\|retire_orchestrator(" agent_workflows/*.py` after editing and confirm no legitimate caller is left without it.
  - Depends on: E-03
  - Expected outcome: every driver-owned terminal transition presents a verifying attestation; the token appears in no agent-visible env, file inside a lane, argv, or log.
  - Execution state: pending

- [ ] E-06 Keep the token out of every agent child env: in `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`, where `child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER` is set, also unconditionally `child_env.pop(ipd_lifecycle.DRIVER_ATTEST_ENV, None)` (defense in depth: `runner_shared.pinned_child_env` copies `os.environ`, so if an operator or a nested driver ever exports it, it must still not reach the agent). Delete the run's token file when the run finishes (success or failure) in the same place the run is closed out, best-effort.
  - Depends on: E-05
  - Expected outcome: an agent child env built while `AW_DRIVER_ATTEST` is set in the driver's `os.environ` does not contain it.
  - Execution state: pending

### Task group 3: regression tests and suite

- [ ] E-07 Create `tests/test_driver_attestation_gate.py` (use `tests/support.py` `init_repo` and the plan-text helpers pattern from `tests/test_ipd_lifecycle_cli.py`; set up a REAL `git worktree add -b aw/lane/<id6> .aw/worktrees/<id6>` lane and `aw ipd begin` the plan so a receipt exists). Cases: (1) THE INCIDENT SHAPE: `subprocess.run(["env", "-u", "AW_EXECUTION_ROLE", sys.executable, "-m", "agent_workflows", "ipd", "finalize", id6, "--actor", "a", "--message", "m", "--apply"], cwd=<lane>)` exits nonzero, output contains `no-driver-attestation` or the new message text, plan still in `pending/`, main and lane HEADs unchanged, receipt still present; (2) the `aw set executed <id6>` route from the lane cwd is refused the same way; (3) wrong token and a `../`-style run-id are refused; (4) DRIVER WITH TOKEN: mint into `<main>/.aw/records/runs/run-test/`, run the same finalize with `AW_DRIVER_ATTEST` set, exits 0 and the plan moves to `executed/`; (5) MAIN-CHECKOUT HUMAN: finalize from the main checkout with neither variable set exits 0; (6) `retire_orchestrator(<lane root>, ..., env={})` refuses with `ROLLUP_REFUSED_NO_DRIVER_ATTESTATION`; (7) the child env built by `oc_runipd.run_opencode` / `agy_runipd.run_agy_turn` (drive them the way `tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_both_drivers_mark_only_an_isolated_turn` does, without modifying that file) omits `AW_DRIVER_ATTEST` when the driver's env has it; (8) `runner_shared.driver_finalize` with a stub `argv_builder` and a `subprocess.run` capture puts the attestation in the subprocess `env` and NOT in argv. Each subprocess case passes an explicit `env=` dict built from `os.environ` so the conftest scrub does not decide the outcome.
  - Depends on: E-03, E-05, E-06
  - Expected outcome: new file passes; case (1) demonstrably fails with the E-03 gate temporarily reverted.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest` and record its summary line; also run the families that exercise the driver's real finalize in a lane (`tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_orchestrator_retirement.py`, `tests/test_orchestrate_isolation.py`, `tests/test_ipd_lifecycle_cli.py`), since a missed plumbing site shows up there as a new `no-driver-attestation` refusal. Add a CHANGELOG.md entry under Unreleased (user-facing prose: no em or en dashes).
  - Depends on: E-07
  - Expected outcome: bare suite green; named families green; CHANGELOG entry present.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The terminal gates live at the choke point, not the CLI: `finalize` covers the CLI, the rollup delegation, and `status_set._delegate_plan_executed_to_finalize` (its comment: "this one site covers all THREE callers"). The new gate goes in the same place for the same reason.
- `finalize` and `retire_orchestrator` take `env: Optional[Mapping[str, str]]` so role checks are testable without mutating `os.environ`; the attestation lookup must use the same parameter.
- Control-store paths resolve through `ipd_lifecycle.checkout_control_root`, which collapses a linked worktree to the MAIN worktree's `.aw` (the fix for a lane writing a second control store). The token file and its verification MUST use it, so a lane root and the main root agree on where the run dir is.
- `runner_shared.driver_finalize` deliberately runs with `cwd=<lane>` and `--dir <lane>` ("finalize must resolve paths against the tree it is finalizing"), so the driver's own finalize IS inside a lane and WILL hit the new gate: plumbing the token is not optional.
- Lane naming: `worktree_lease.lane_branch_name` gives `aw/lane/<id6>` and lanes live in `.aw/worktrees/<id6>` (`runner_shared` docstring at the allocator: "branch is normally `aw/lane/<id6>` in `.aw/worktrees/<id6>`").
- Root `conftest.py` pops `AW_EXECUTION_ROLE` at import, so tests needing a marked or unmarked env must pass an explicit env dict.
- `tests/test_worker_role_refusal.py` is owned by executed plan `8b9ufm`, which forbids modifying its ambient-asserting test; this plan adds a NEW file and does not touch it.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `877545fc` (`git rev-parse --short HEAD`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.finalize` role gate | From a real lane worktree, stripping the marker passes the role gate. | Probe: `git init` + `git worktree add -b aw/lane/abc123 .aw/worktrees/abc123`, then from the lane: `env AW_EXECUTION_ROLE=worker ... ipd finalize zzzzzz --apply --dir .` -> `AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes ...` exit=2; `env -u AW_EXECUTION_ROLE ... ipd finalize zzzzzz --apply --dir .` -> `error: no plan matched selector 'zzzzzz'.` exit=2, i.e. it got PAST the role gate to plan resolution. |
| F-2 | HIGH | `ipd_lifecycle.finalize`, `ipd_lifecycle.retire_orchestrator` | The only authority check is `if worker_role_active(os.environ if env is None else env):` in both; in-process probe `LC.finalize(<lane>, ..., env={})` returned `plan file not found` (gate passed), with `env={'AW_EXECUTION_ROLE':'worker'}` returned `('worker-role',)`. | code comment quoted in Concern; probe output above. |
| F-3 | HIGH | whole package | No positive attestation exists. | `grep -rn "driver.token\|driver_token\|AW_DRIVER_TOKEN" agent_workflows` -> no output. |
| F-4 | INFO | `runner_shared.driver_finalize` | The driver's own finalize runs inside the lane (`cwd=str(repo)`, `--dir <lane>`), so a lane-root gate without token plumbing would break the driver. | `execute_item_core`: `finalize_repo = Path(work_dir)` then `driver_finalize(finalize_repo, ...)`; `driver_finalize` builds `["ipd","finalize",id6,...,"--apply","--dir",str(repo)]` with `env=env_builder()`. |
| F-5 | INFO | driver call sites | Legitimate terminal-transition callers: `runner_shared.execute_item_core` -> `driver_finalize` (two sites: isolated lane and in-place), host wrappers `oc_runipd.driver_finalize` / `agy_runipd.driver_finalize` (`env_builder=pinned_child_env`), `runner_shared.dispatch_orchestrator_item` -> `_lifecycle.retire_orchestrator(repo, ...)` in-process. Human route: `status_set._delegate_plan_executed_to_finalize` -> `_life.finalize`. | `grep -n "finalize(\|retire_orchestrator(" agent_workflows/{runner_shared,oc_runipd,agy_runipd,status_set}.py`. |
| F-6 | INFO | agent child env | Both hosts build the agent env from `pinned_child_env()` (a copy of `os.environ`) and set the marker there. | `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`: `child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER`. |
| F-7 | INFO | tests | The backlog's `env -u` test motivation is gone: root `conftest.py` has `os.environ.pop("AW_EXECUTION_ROLE", None)`. No regression test for this bypass exists (removed in trim `19313eed`). | `grep -n pop conftest.py`. |

Design choice (why a token plus lane detection, not receipt provenance): the backlog's sketch 1 (bind to the receipt's `actor`) does not work, because the lane agent can pass any `--actor` and the receipt is readable from the lane via `checkout_control_root`. Lane-root detection alone is also insufficient, since the driver's own finalize runs in the lane (F-4). Requiring a capability only the driver was handed, while leaving main-checkout finalize untouched, is the smallest change that refuses the observed path and the `aw set executed` path without touching human workflows.

What this closes and what it does not, stated honestly: it CLOSES the observed opportunistic bypass (a cooperating agent stripping one variable, or calling `aw set executed`, from its lane). It does NOT stop a MALICIOUS same-user agent that reads `<main>/.aw/records/runs/<run-id>/driver-attest.token` (reachable by path from the lane) or `cd`s to the main checkout and finalizes from there; defeating that needs an OS sandbox or separate principal (`1o4eif`). The difference from today is that the bypass now requires deliberately locating and replaying a secret, which no good-faith "environment artifact" reading produces.

## Proposed changes (ordered, validatable)

1. E-01 lane-root predicate; E-02 mint/verify primitives (file located by the verifier, constant-time compare).
2. E-03 gate both terminal functions after the existing role gate, new typed refusal id and an explanatory message; E-04 env-only CLI carriage.
3. E-05 mint per run and plumb to `driver_finalize` (both `execute_item_core` sites, both host wrappers) and to the in-process `retire_orchestrator` call; E-06 scrub from agent child env and delete at run end.
4. E-07 new regression file with the exact incident command; E-08 suite plus driver families plus CHANGELOG.

## Deferred / out of scope (with reason)

- `aw ipd begin` from a lane with the marker stripped (OQ-02). Not a terminal transition, and the driver runs begin before the turn; whether to gate it identically is a scope call.
  - Carrier-Declined: Maintainer brief scopes this plan to the terminal finalize/retire; recorded as non-blocking OQ-02 for the reviewer to widen or file.
- Audit signal at integration for a finalize commit the driver did not perform (backlog sketch 4). With the tooled path gated, such a commit requires a raw hand forgery, which is sandbox territory.
  - Carrier-Declined: The gate removes the tooled route that produced the incident; detecting raw forgeries is part of the OS-sandbox enforcement already recorded in executed plan `1o4eif`.
- OS sandbox / separate principal so a malicious agent cannot read the run dir.
  - Carrier-Evidence: .aw/records/plans/executed/20260828-wtiso-07-1o4eif-phase-6-optional-os-sandbox-hard-enforcement-profile-host-ca.ipd.md
- Agent-facing prompt instruction that the runner owns finalize (backlog sketch 5). Already delivered by executed plan `8b9ufm`.
  - Carrier-Evidence: .aw/records/plans/executed/20260908-roleadv-01-8b9ufm-state-the-runner-owns-begin-finalize-role-at-turn-start-inst.ipd.md
- Removing the `AW_EXECUTION_ROLE` marker. It stays as the first selector and keeps `8b9ufm`'s refusal message path.
  - Carrier-Declined: Load-bearing for `AW-LIFECYCLE-ROLE-001` and its tests; this plan adds a layer rather than replacing one.

## Scope check

- Over-scope: none. `agent_workflows/status_set.py` is deliberately NOT declared: it inherits the gate through `_life.finalize`; if E-03 finds it does not, declare it before editing.
- Under-scope: if E-01 finds the coordinator scratch worktree matches the lane predicate, or E-05 finds a driver finalize/retire caller outside the listed sites, STOP and extend `- Scope-Paths:` before editing.

## Required tests / validation

- `python3 -m pytest tests/test_driver_attestation_gate.py -o addopts="" -q` green, and case (1) shown FAILING with the E-03 gate locally reverted.
- Driver families green: `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_orchestrator_retirement.py tests/test_orchestrate_isolation.py tests/test_ipd_lifecycle_cli.py`.
- Bare `python3 -m pytest` summary line pasted.

## Spec / documentation sync

- No `.spec.md` describes `AW-LIFECYCLE-ROLE-001` or the driver's finalize authority (`grep -rln "AW-LIFECYCLE-ROLE-001\|AW_EXECUTION_ROLE" .aw/records/specs` returned nothing), so no spec amendment. CHANGELOG.md gets a Security/Fixed entry. The "HONEST LIMIT" comments in `ipd_lifecycle.finalize` and `oc_runipd.run_opencode` are updated to describe the second layer and its remaining limit.

## Open questions

### OQ-01: Where should the attestation value be carried to the CLI subprocess?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Env var `AW_DRIVER_ATTEST` set only on the subprocess env built inside `runner_shared.driver_finalize`, not a CLI flag. argv is recorded in agent session logs and visible to `ps`, and the observed incident itself was a copied command line; an env var set on one `subprocess.run(env=...)` never appears in the agent's env (E-06 adds a pop for defense in depth). The retire path is in-process and uses the kwarg, carrying nothing through env at all.

### OQ-02: Should `aw ipd begin` from a lane get the same attestation requirement?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: NO in this plan. The incident's harm came from the terminal transition consuming the receipt; begin is run by the driver before the turn and is currently gated only by the env selector. Extending it is mechanically identical (same predicate, `driver_begin` plumbing) but widens scope beyond the brief; a reviewer may add it as E-items or file a backlog item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the unit test output for `lane_worktree_active` covering `.aw/worktrees/<id6>` True, off-tree `aw/lane/x` True, main checkout False, non-git dir False; paste the name/branch of the coordinator scratch worktree `finalize` creates, showing it matches neither lane criterion.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste test output showing mint-then-verify True and wrong-token, unknown run-id, `../` run-id, malformed value, missing file each False with a reason; paste `stat -c %a` of a minted file showing `600`; paste the grep proving `hmac.compare_digest` is used.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste in-process results of `finalize(<lane>, ..., env={}, apply=True)` and `retire_orchestrator(<lane>, ..., env={})` each returning `('no-driver-attestation',)` with HEAD and receipt unchanged; paste the new refusal message text containing the "does NOT grant driver authority" sentence; paste `aw set executed <id6>` from the lane refused.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m agent_workflows ipd finalize --help` showing no token flag, and the test case where the CLI subprocess succeeds only when `AW_DRIVER_ATTEST` is in its env.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `grep -n "driver_finalize(\|retire_orchestrator(" agent_workflows/*.py` with every non-definition call site passing the attestation; paste E-07 case (8) passing (token in subprocess env, absent from argv); paste `grep -rn AW_DRIVER_ATTEST .aw/records/runs/<a test run>/events.jsonl` or equivalent showing the token is not written to run logs.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste E-07 case (7) passing for BOTH hosts, and show it FAILING when the `pop` is removed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_driver_attestation_gate.py -o addopts="" -q` summary (all passed); paste case (1) FAILING with the E-03 gate locally reverted (and then restored); quote the exact `env -u AW_EXECUTION_ROLE ... ipd finalize <id6> ... --apply` argv the test runs.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line (N passed, 0 failed); paste the summary of the five driver/lifecycle families named in E-08; paste `git diff -- CHANGELOG.md`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. OQ-01 is resolved; OQ-02 is `Blocking: no` with a stated default. The executor commits only the paths in `- Scope-Paths:` via `aw commit u27oh3 -- <paths>`, never `git add -A`, and never pushes; test claims must paste actual runner output. In a managed lane the runner performs the terminal `aw ipd finalize` (and after this plan, it does so by presenting its driver attestation); in an unmanaged run the executor runs `aw ipd finalize u27oh3` from the main checkout only after `aw ipd lint --phase pre-transition` conforms and every V-* item carries observed evidence.
