# IPD: hpc shared-host hardening warning

- Date: 2026-08-19
- Kind: child
- Concern: Shared-host security exposure of local agent control servers is documented (D86/D87) but the installer says nothing about it; a user installing on an HPC login node or shared dev server gets no pointer to the hardening how-to.
- Scope: Emit an always-shown, one-line security pointer at install time (shared by all install entry points) that references the shared-host caveat and the hardening how-to, plus a test asserting it is emitted. The human circulation of the how-to to users is out of scope.
- Status: approved
- Set: backlog-medhigh-260819
- Order: 8
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 0zxfic
- Approval: maintainer (human), 2026-08-19: blanket-approved the backlog-medhigh-260819 Set for unattended execution.

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-19 author (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body researched and drafted; E/V allocated.
- 2026-08-19 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-08-1 stale bench_env.py path prefix corrected, PR-08-2 gate scope-fence now names DECISIONS.md + cli.py + tests + backlog file, PR-08-3 canonical serial-runner note. Anchors verified (cli.py:1975/2036/2394, engine.print_summary:3201, bench_env.py:401, how-to record present, D86/D87, backlog 3srje9). OQ-01 resolved (always-shown pointer over unreliable auto-detection - sound security posture). GO - PENDING HUMAN APPROVAL.

## Goal

Add a clear, always-shown one-line security pointer to the install flow so that anyone installing agent-workflows (including on a shared or HPC host) is told that local agent control servers can be a cross-user attack surface and is pointed at the hardening how-to. This satisfies the agent-doable half of backlog item 3srje9 (the "loud installer warning" from D86/D87); the human-owned circulation of the how-to stays with the human.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Emit the install-time security pointer

- [ ] E-01 Add a shared helper (for example `_security_pointer(term)`) in `agent_workflows/cli.py` that prints a single, plain-language security line: on a shared or multi-user host any other local user can drive your agent, and a pointer to the shared-host hardening how-to (`.aw/records/research/20260716-opencode-shared-host-hardening-howto-00-tt8ipb-opencode-shared-host-hardening-howto.howto.md`) plus DECISIONS.md D86/D87.
  - Depends on: none
  - Expected outcome: A new function exists in `agent_workflows/cli.py` that, when called with a `Term`, prints one security-pointer line via `term.status("warn", ...)`.
  - Execution state: pending
- [ ] E-02 Call the helper from the single shared per-repo install shell `_install_one` (`agent_workflows/cli.py:2036`) after `engine.print_summary(...)` and the install status line, so EVERY entry point (`aw install <dir>`, `aw install all`, `aw setup`, engine `run()`) emits it exactly once per repo without duplication.
  - Depends on: E-01
  - Expected outcome: `_install_one` invokes `_security_pointer(term)` after the summary; a single install of one repo prints the pointer exactly once.
  - Execution state: pending

### Task group 2: Documentation and decision sync

- [ ] E-03 Update DECISIONS.md D87 "Applied" line to record that the framework now ships an always-shown install-time security pointer citing D86/D87 (replacing the prior "No code change yet" note), and cite the code location.
  - Depends on: E-02
  - Expected outcome: D87 "Applied" reflects the implemented installer pointer with a `cli.py` reference.
  - Execution state: pending

### Task group 3: Test, validate, and close the backlog item

- [ ] E-04 Add an end-to-end test in `tests/test_installer.py` that runs the installer against a throwaway repo (via `run_installer`) and asserts the security-pointer line (the hardening how-to reference) is present in stdout.
  - Depends on: E-02
  - Expected outcome: A new test method exists and, when run, passes because the pointer text appears in installer stdout.
  - Execution state: pending
- [ ] E-05 Run the FULL serial test suite (canonical `make test-serial` / `python3 -m unittest discover -s tests -t .`; `python3 -m pytest -p no:xdist` equivalent only with the `.[test]` extra) and paste the actual runner output.
  - Depends on: E-04
  - Expected outcome: The full suite passes with no failures or errors.
  - Execution state: pending
- [ ] E-06 Close backlog item 3srje9 to done via `aw backlog set`, noting in the workflow-history message that the installer-pointer (code) part is complete and the human circulation of the how-to stays with the human.
  - Depends on: E-05
  - Expected outcome: `.aw/records/backlog/.../3srje9` has `Status: done` and a history line recording the code completion and the human-owned residual.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The install flow has one shared per-repo shell, `_install_one` (`agent_workflows/cli.py:2036`), used by `aw install <dir>`, `aw install all`, `aw setup`, and the engine `run()` path (D85), so a message added there is emitted once by every entry point and cannot drift.
- Preflight WARN messages are gathered by `_preflight_warnings` (`agent_workflows/cli.py:1975`) and printed via `term.status("warn", ...)`; the post-install teaching pointer is `_teach` (`agent_workflows/cli.py:2394`). These are the established patterns for install-time notices.
- End-to-end installer tests run the installer as a subprocess against throwaway git repos and assert on stdout (`tests/test_installer.py`, using `run_installer` from `tests.support`); stdout assertions such as `self.assertIn(..., proc.stdout)` are the established test shape (see `tests/test_installer.py:503`).
- HPC scheduler detection already exists in the benchmark tool `capture_hpc` (`.aw/system/workflows/benchmark/tools/bench_env.py:401`): it detects Slurm/PBS/SGE/LSF by submit-binary presence and reads `SLURM_JOB_ID`/`PBS_JOBID`/`LSB_JOBID` for "inside allocation". It is a heuristic tuned for benchmarking, not a reliable shared-host detector for install.
- User-facing prose must contain no em or en dashes (AGENTS.md execution contract); the pointer text authored here follows that rule.

## Findings

| # | Finding | Evidence |
| - | ------- | -------- |
| 1 | D86 documents that an unauthenticated local OpenCode control server is a cross-user attack surface on shared/multi-user hosts (HPC login nodes, shared dev servers, multi-tenant CI); a local user can drive your agent, read your files, and read your provider key with no prompt and no visible session. | `DECISIONS.md:2151` (D86) |
| 2 | D87 sets the shared-host guardrail and states any installer or how-to that targets shared hosts must WARN LOUDLY; its "Applied" note says "No code change yet; if we later add a shared-host install warning to the framework it will cite D86/D87." | `DECISIONS.md:2159`-`2163` (D87) |
| 3 | The hardening how-to already exists as a reference record with a loud "READ THIS FIRST" section, mitigation steps, and an operator reference architecture; it is the artifact the installer pointer should point at. | `.aw/records/research/20260716-opencode-shared-host-hardening-howto-00-tt8ipb-opencode-shared-host-hardening-howto.howto.md:14`,`21` |
| 4 | The single shared per-repo install shell is `_install_one` (`agent_workflows/cli.py:2036`), documented as the ONE per-repo orchestration all entry points use (D85), so a pointer added there is emitted once per repo by every path. | `agent_workflows/cli.py:2036`-`2052` |
| 5 | Existing install-time notice patterns: WARN preflight (`agent_workflows/cli.py:1975`) and the post-install `_teach` pointer (`agent_workflows/cli.py:2394`). | `agent_workflows/cli.py:1975`,`2394` |
| 6 | HPC detection is available but heuristic: `capture_hpc` keys off submit binaries on PATH and scheduler env vars (`.aw/system/workflows/benchmark/tools/bench_env.py:401`-`437`). This false-positives on single-user workstations that happen to have Slurm client tools installed and false-negatives on shared dev servers and multi-tenant CI (no scheduler at all), so it is not a trustworthy install-time shared-host signal. | `.aw/system/workflows/benchmark/tools/bench_env.py:401` |
| 7 | The backlog item 3srje9 is two-part: agent-doable installer warning plus human-owned circulation of the how-to. | `.aw/records/backlog/open/20260815-opencode-disclosure-01-3srje9-hpc-shared-host-warning.backlog.md:6` |

## Proposed changes (ordered, validatable)

1. Add `_security_pointer(term)` in `agent_workflows/cli.py` printing one WARN line: shared/multi-user hosts expose your local agent server to other users; see the shared-host hardening how-to and DECISIONS.md D86/D87 (E-01).
2. Call it from `_install_one` after `engine.print_summary(...)` so all install entry points emit it once per repo (E-02).
3. Update DECISIONS.md D87 "Applied" to record the shipped pointer and its `cli.py` location (E-03).
4. Add an end-to-end test asserting the pointer appears in installer stdout (E-04).
5. Run the full serial suite and paste output (E-05).
6. Close backlog 3srje9 to done, noting the human circulation residual (E-06).

## Deferred / out of scope (with reason)

- CIRCULATION of the hardening how-to to users (emailing/announcing it to the shared-host user community) is HUMAN-OWNED and out of scope. It is a communication act by the maintainer, not something the installer can perform, and D87 explicitly frames it as guidance to circulate. This IPD delivers only the code half (the install-time pointer).
- Auto-detecting an HPC or shared host and gating install behind it is deferred (see OQ-01). Reliable detection is not achievable with the available signals, and a flaky detector that stays silent on a genuinely shared host would be worse than an always-shown pointer.
- Enforcing `OPENCODE_SERVER_PASSWORD` or refusing to install on shared hosts is out of scope: D87 makes the lever loud warning plus upstream fix, not enforcement, and agent-workflows does not manage the OpenCode server lifecycle.

## Scope check

- Over-scope: none. No enforcement, no HPC auto-detection, no changes to the OpenCode server, no new documents beyond a one-line DECISIONS.md update.
- Under-scope: none for the agent-doable half. The human circulation of the how-to is intentionally excluded and recorded in Deferred / out of scope.

## Required tests / validation

- New end-to-end installer test (E-04) asserting the security-pointer line (the hardening how-to reference) is present in installer stdout, following the existing subprocess-plus-stdout pattern in `tests/test_installer.py`.
- Full serial test suite run (E-05) with actual output pasted as evidence.
- Manual confirmation that a single-repo install prints the pointer exactly once (covered by the stdout assertion and by inspecting the single call site in `_install_one`).

## Spec / documentation sync

- DECISIONS.md D87 "Applied" line updated to record the shipped installer pointer citing D86/D87 and the `cli.py` code location (E-03).
- The hardening how-to itself needs no change; the installer points at it.
- No spec under `.aw/records/specs/` governs the installer output, so no spec status change is required.

## Open questions

### OQ-01: Auto-detect a shared/HPC host, or always show a one-line pointer?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Recommend the ALWAYS-SHOWN one-line pointer, not auto-detection. The only available signals are heuristic and wrong in both directions: `capture_hpc` keys off scheduler binaries and env vars (`.aw/system/workflows/benchmark/tools/bench_env.py:401`), which false-positives on single-user boxes that have Slurm client tools and false-negatives on shared dev servers and multi-tenant CI that run no scheduler. Home-directory permission or user-count probes are equally unreliable and add filesystem work at install time. A detector that silently stays quiet on a genuinely shared host is a security regression relative to a short, always-shown pointer. The always-shown pointer is one WARN line, is honest (it does not claim to know your host), costs a single line of output on a single-user machine, and is exactly the loud-warning lever D87 calls for. If the maintainer later wants targeted escalation, that can be a follow-on that adds a stronger message when a reliable positive signal (for example `SLURM_JOB_ID` present) is seen, without ever suppressing the base pointer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The `_security_pointer` function exists in `agent_workflows/cli.py` and, called with a `Term`, prints one line containing the hardening how-to reference and a D86/D87 mention (shown by reading the function source and a direct call).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `_install_one` calls `_security_pointer(term)` after `engine.print_summary(...)`; a single-repo install emits the pointer exactly once (grep the installer stdout shows one occurrence).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: DECISIONS.md D87 "Applied" line now records the shipped installer pointer and references `cli.py` (shown by reading the updated line).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: The new test method in `tests/test_installer.py` runs and passes, asserting the pointer text in installer stdout (shown by the runner output for that test).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Pasted full-suite runner output showing zero failures and zero errors.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: The backlog record for 3srje9 shows `Status: done` and a workflow-history line noting the code completion plus the human-owned circulation residual.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (Status advances to `approved`) before any code is written. Scope fence - this plan touches only: `agent_workflows/cli.py` (the `_security_pointer` helper + its call in `_install_one`), `DECISIONS.md` (the D87 "Applied" line), `tests/test_installer.py` (the new stdout assertion), and the `3srje9` backlog file; do not expand scope, and if it seems to need more, STOP and report. On execution, follow the repo execution contract: commit only those files, path-scoped (`git commit -m msg -- agent_workflows/cli.py DECISIONS.md tests/test_installer.py <backlog-file>`), never `git add -A` and never push; paste the actual full-suite runner output as the E-05/V-05 evidence rather than claiming success; write no em or en dashes in user-facing prose. Do not mark this plan executed or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item is verified with concrete evidence. If validation fails at any point, STOP and report rather than proceeding.
