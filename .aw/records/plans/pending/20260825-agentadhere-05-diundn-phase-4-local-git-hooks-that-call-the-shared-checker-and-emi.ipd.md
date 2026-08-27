# IPD: Phase 4: local git hooks that call the shared checker and emit teaching errors

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 4 + section 7.7: local git hooks give immediate, self-correcting feedback (High confidence as feedback, Med-low as a hard boundary - local, not cloned by default, skippable with `--no-verify`). The toolkit already has two commit-scoped gates (`hooks/status_untooled_gate.py`, `hooks/executed_transition_gate.py`) that delegate to `check_engine` rules, but there is no systematic pre-commit/pre-push layer calling the full phase-1 engine over the staged index + declared scope, and refusals do not uniformly TEACH the recovery path.
- Scope: Add/extend local git hooks that call the SHARED phase-1 engine (never a forked policy): (1) a pre-commit hook that runs the checker against the staged INDEX and the declared scope (Scope-Paths comparison from phase 3), refusing out-of-scope or invariant-violating staged trees with a TEACHING error (name the violated invariant + the exact `aw ...` recovery command, findings 4.4); (2) a pre-push hook that explains missing authorization and prevents accidental pushes (convenience/feedback, NOT an authority boundary); (3) fail-closed for security-sensitive rules where the host supports it; (4) contract tests for each hook (coverage, alternate tool paths, malformed input, disablement, fail-open behavior). Follow the established pattern: each hook `check(repo_root)` delegates to a single `check_engine` rule so hook and `aw check` never diverge (status_untooled_gate.py:33). Honest limits documented (local only, `--no-verify`); the authoritative boundary is phase-5 CI.
- Scope-Paths: agent_workflows/hooks/, agent_workflows/check_engine.py, agent_workflows/engine.py, tests/
- Status: approved
- Set: agentadhere
- Order: 5
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: diundn
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 approved (aw set): status set to approved

- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 gate execution contract added, PR-002 V-01..V-03 concrete falsifiable evidence, PR-003 OQ-01 resolved (opt-in, idempotent/no-clobber), PR-004 no-fork/no-divergence proofs required, PR-005 Status draft->reviewed, PR-006 split E-01 into pre-commit + pre-push (distinct test-surfaces)
- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add local pre-commit/pre-push git hooks that call the shared phase-1 engine over the staged index + declared scope and refuse violations with teaching errors (violated invariant + exact recovery command), fail-closed where supported, with honest local-only limits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pre-commit hook

- [ ] E-01 Add a pre-commit hook that runs the phase-1 `check_engine` against the STAGED INDEX + declared `Scope-Paths` (the phase-3 scope comparison), refusing an out-of-scope or invariant-violating staged tree with a TEACHING error (name the violated invariant + the exact `aw ...` recovery command, findings 4.4). Follow the established pattern: the hook's `check(repo_root)` delegates to a SINGLE `check_engine` rule (status_untooled_gate.py:33) so the hook and `aw check` can never diverge; do NOT fork a policy. Fail-closed for security-sensitive rules where the host supports it. Enforce the INVARIANT (staged paths within declared scope), not the command syntax (a hook cannot reconstruct `git add -A`, findings 5.3). Add idempotent, no-clobber install wiring in `engine.py` mirroring `create_backlog_close_gate_hook` (OQ-01 opt-in decision).
  - Depends on: none
  - Expected outcome: a staged commit that violates an invariant or touches out-of-scope paths is refused (exit 1) with a teaching message naming the invariant + recovery command; the hook delegates to one shared `check_engine` rule.
  - Execution state: pending

### Task group 2: pre-push hook

- [ ] E-02 Add a pre-push hook that explains missing authorization and prevents accidental pushes - CONVENIENCE/FEEDBACK ONLY, explicitly NOT an authority boundary (local, cloned-by-default-no, skippable with `--no-verify`; the authoritative boundary is phase-5 CI). Same delegation pattern (single `check_engine` rule, no forked policy). Document the honest local-only limit in the refusal message and the installer docs.
  - Depends on: none
  - Expected outcome: a push without authorization is prevented/explained with a message that honestly states the hook is local-only and bypassable (not an authority boundary); the hook delegates to the shared engine.
  - Execution state: pending

### Task group 3: contract tests

- [ ] E-03 Add contract tests per hook: coverage (violation refused, clean passes), alternate tool paths, malformed input, disablement (`--no-verify`), and fail-open/fail-closed behavior; assert the teaching message names the invariant + the exact recovery command, and that both hooks and `aw check` produce the SAME finding for the same tree (no divergence).
  - Depends on: E-02
  - Expected outcome: each hook passes its contract test matrix; hook output and `aw check` agree on the same rule for the same tree.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `hooks/status_untooled_gate.py` (check + main, delegating to `check_engine.check_status_untooled`) and `hooks/executed_transition_gate.py` are the templates; install wiring for hooks lives in `engine.py`.
- Findings 7.7: fail closed for security-sensitive rules where the host supports it; local hooks are feedback, not authority; the authoritative boundary is CI (phase 5).
- Findings 5.3: a pre-commit hook can inspect the staged INDEX and enforce "staged paths within declared scope" but cannot reliably reconstruct the exact command (`git add -A`); enforce the invariant, not the syntax.

## Findings

The engine + two gate precedents exist; Phase 4 generalizes to a pre-commit/pre-push layer over the full engine with uniform teaching errors, honestly scoped as local feedback.

## Proposed changes (ordered, validatable)

1. `hooks/`: pre-commit (staged index + scope) and pre-push (authorization) delegating to `check_engine`.
2. `engine.py`: install wiring for the hooks (idempotent).
3. `tests/`: per-hook contract matrix + teaching-message assertions.

## Deferred / out of scope (with reason)

- Treating hooks as an authority boundary: explicitly NOT (local, skippable) - CI is the authority (phase 5).
- Host-specific pre-tool adapters (Claude/Codex/etc.): phase 6 (deferred set).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- A staged commit violating an invariant / declared scope is refused (exit 1) with a teaching message naming the invariant + recovery command.
- A pre-push without authorization is prevented/explained.
- Contract matrix per hook: coverage, alternate paths, malformed input, disablement, fail-open; security-sensitive rules fail closed where supported.
- Hook and `aw check` never diverge (same rule).

## Spec / documentation sync

- Document the hooks + honest local-only limits (`--no-verify`) in the installer docs and AGENTS.md.

## Open questions

### OQ-01: Install these hooks by default, or opt-in like the bklggrad hook?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED - OPT-IN, aligning with the established `bklggrad` pattern: install via an idempotent, no-clobber `engine.create_*_hook(repo, install=True)` writer (mirroring `create_backlog_close_gate_hook`), NEVER installed by default and NEVER clobbering a user's existing `.pre-commit-config.yaml` (the installer hands the user the hook block to merge). This keeps the toolkit's honest stance that local hooks are opt-in feedback, not an imposed authority boundary. E-01 encodes the idempotent/no-clobber install; V-01(d) proves it. Not a blocker.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) a staged tree touching a path OUTSIDE the plan's declared `Scope-Paths` is refused by the pre-commit hook with exit 1 and a TEACHING message that names the violated invariant AND the exact `aw ...` recovery command (paste the hook output); (b) a clean, in-scope staged tree PASSES (paste output, exit 0); (c) NO-FORK proof: the hook's `check(repo_root)` delegates to a single `check_engine` rule and defines no parallel policy (paste the import/grep, mirroring status_untooled_gate.py:33); (d) install wiring is idempotent + no-clobber (run install twice, paste output showing the second run does not duplicate/clobber).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: (a) a push attempt without authorization is prevented/explained by the pre-push hook (paste output); (b) the refusal message HONESTLY states the hook is local-only and bypassable with `--no-verify` and is NOT an authority boundary (paste the message text); (c) NO-FORK proof: the pre-push hook delegates to the shared `check_engine` (paste the import/grep).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: (a) the per-hook contract matrix passes - paste the test run covering: violation-refused, clean-passes, alternate tool path, malformed input, disablement (`--no-verify`), and fail-open/fail-closed; (b) DIVERGENCE proof: a test asserts the hook and `aw check` produce the SAME rule id/finding for the same tree (paste the assertion output); (c) the teaching-message assertion (invariant name + exact recovery command) passes for each hook.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: three E-items, each a single focused pass with its own verification surface - E-01 (pre-commit hook over staged index + declared scope), E-02 (pre-push authorization/feedback hook), E-03 (per-hook contract-test matrix + no-divergence proof). All three center on the same shared `check_engine` and the established hook-delegation pattern, so they form one cohesive child.

### Open questions resolved

- OQ-01 (install by default vs. opt-in like bklggrad): RESOLVED - OPT-IN, via an idempotent/no-clobber `engine.create_*_hook(install=True)` writer mirroring `create_backlog_close_gate_hook`; never default-installed, never clobbers a user's `.pre-commit-config.yaml`. Encoded in E-01, proven by V-01(d).

### Execution contract

- Scope fence: touch ONLY the files in `Scope-Paths` - `agent_workflows/hooks/`, `agent_workflows/check_engine.py`, `agent_workflows/engine.py`, and `tests/`. REUSE the established hook pattern (each `check(repo_root)` delegates to a SINGLE `check_engine` rule, status_untooled_gate.py:33) and the phase-3 scope comparison; do NOT fork a policy, and do NOT build the phase-2 commands, phase-3 event-state, or phase-5 CI. If the work seems to need files outside this fence, STOP and report.
- No-fork MUST: hook refusals and `aw check` MUST come from the SAME `check_engine` rule so they can never diverge (V-01c/V-02c/V-03b prove it). Do NOT reimplement policy inside a hook.
- Authority honesty (hard MUST): these hooks are LOCAL feedback, NOT an authority boundary - they are not cloned by default and are skippable with `--no-verify`. The refusal messages and docs MUST say so; the authoritative boundary is phase-5 CI. Do NOT present a local hook as tamper-proof.
- Honesty rule (hard MUST): when a V-item reports a test/hook/`aw check` run passed, paste the ACTUAL runner output; never claim a pass you did not run.
- Commit rule: commit ONLY this child's own changed files, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically).
