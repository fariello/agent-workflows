# IPD: host-neutral run-as dispatch and default runner routing

- Date: 2026-08-29
- Kind: child
- Concern: The desired concise surface is aw run as gem, but aw run already owns a substantial fixed run-ledger command family. Treating profile names as dynamic top-level or run subcommands would collide with status/report/current commands and future syntax; treating unknown run tokens as selectors would make future command additions silently reinterpret existing invocations. A generic route also needs a defined default runner and must delegate without changing host-runner semantics.
- Scope: Add fixed, collision-safe aw run as PROFILE SELECTOR and aw run ipd SELECTOR subcommands. Resolve a named profile or configured default runner/profile through the shared domain, dispatch only to registered host adapters, forward selectors/direct structured overrides exactly once, retain all existing aw run ledger commands, and fail closed with actionable configuration help.
- Scope-Paths: agent_workflows/run_dispatch.py, agent_workflows/cli.py, tests/test_run_dispatch.py, tests/test_cli.py
- Item-Dependencies: executed:3cm15q
- Status: to-review
- Set: runprofile
- Order: 4
- Highest E allocated: 04
- Author: codex gpt-5.6
- Id: ygzq71

## Workflow history

- 2026-08-30 to-review (codex gpt-5.6): authored to add the fixed as namespace without dynamic-command collisions.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Provide the short host-neutral command the user selected:

    aw run as gem SELECTOR

Also provide an unqualified default route without overloading unknown tokens:

    aw run ipd SELECTOR

Existing commands such as aw run status, show, evidence, start, and verify-ledger must remain byte-for-byte routed to their current ledger implementation.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: fixed grammar and dispatch registry

- [ ] E-01 Register fixed aw run as and aw run ipd parser entries under the existing run family.
  - Depends on: none
  - Expected outcome: profile names exist only as data after the literal as token, while current/future command namespaces remain protected.
  - Execution state: pending

- [ ] E-02 Create run_dispatch.py with a small explicit runner registry and adapter functions. For v1, oc delegates to oc_runipd.main using its accepted canonical start/as/direct-field grammar; no shell subprocess or reconstructed prompt is introduced. Named dispatch derives runner from the profile and verifies registration; default dispatch requires a valid default_runner and per-runner/default resolution. Unknown/unimplemented runners fail with exact setup commands and never fall back to OpenCode.
  - Depends on: E-01
  - Expected outcome: generic syntax is a thin deterministic router, not a second runner, parser fork, or optimistic host detector.
  - Execution state: pending

### Task group 2: parity and namespace protection

- [ ] E-03 Define and test exact parity pairs: aw run as gem X and aw oc run as gem X reach oc_runipd.main with equivalent normalized arguments; aw run ipd X and aw oc run X are equivalent when oc and gem are configured defaults; explicit --model/--variant/--agent overrides survive generic dispatch exactly once. Preserve exit codes, stdout/stderr ownership, interruption handling, and machine-output flags by returning the host runner's result directly.
  - Depends on: E-01, E-02
  - Expected outcome: generic routing adds no behavioral layer beyond runner/profile selection.
  - Execution state: pending

- [ ] E-04 Add adversarial parser/dispatch tests with profiles named status, report, run, show, evidence, and future-command; prove real aw run status/report/show/evidence/start/verify-ledger still select their original handlers while aw run as status selects the profile. Prove aw status, aw gem, aw gemrun, aw run gem, aw run-gem, aw run:gem, and aw rungem are not created/interpreted as aliases; a selector equal to gem under aw run ipd remains a selector; missing profile/default/runner and malformed config fail before host invocation.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a regression test fails if an implementation buys terseness by consuming command namespace, guessing from unknown tokens, or changing ledger routing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- agent_workflows/cli.py already registers aw run as the run-ledger family with many fixed subcommands. Dynamic subparsers are incompatible with the user's no-collision requirement.
- aw oc run delegates argparse.REMAINDER to oc_runipd.main. The generic adapter should delegate to that same authoritative parser rather than duplicate its selector/session/implicit-start logic.
- The top-level CLI consistently returns delegated exit codes and centralizes KeyboardInterrupt/EOF handling.
- The Order-01 schema records default_runner separately from per-runner defaults; this supports default generic routing without guessing.
- rununify explicitly defers a unified top-level aw run facade and forbids behavior change. This new behavior is a separate Set and must be inventoried/preserved by rununify later.

## Findings

| Candidate | Collision behavior | Decision |
|---|---|---|
| aw gem | Profile occupies top-level command namespace. | Prohibited. |
| aw gemrun / aw rungem | Every profile manufactures a command and completion surface. | Prohibited. |
| aw run gem | gem conflicts with current/future run subcommands and selectors. | Prohibited. |
| aw run-gem / aw run:gem | Dynamic command token with unusual completion/help behavior. | Prohibited. |
| aw run as gem | Only as is fixed syntax; gem is data in a bounded position. | Canonical. |
| aw run ipd | Fixed explicit default-runner operation; selectors remain bounded. | Canonical default form. |

## Proposed changes (ordered, validatable)

1. Add only the two fixed parser entries.
2. Delegate through a registered host adapter.
3. Prove host-specific/generic parity and override preservation.
4. Lock down command namespace with adversarial names and rejected spellings.

## Deferred / out of scope (with reason)

- Bare aw run SELECTOR is excluded because unknown-token fallback would collide with current/future fixed run commands.
- Additional runner adapters are deferred until their typed flags and durable-state behavior exist.
- Dynamic command generation, shell aliases, completion aliases, and alternate with/using/w spellings are excluded. as is the sole canonical spelling.
- Unifying host runner implementations remains rununify work; this router calls the current authority.

## Scope check

- Over-scope: no profile storage/wizard changes, OpenCode runner internals, setup integration, Agy changes, or documentation beyond command help.
- Under-scope: explicit profile route, default route, registered dispatch, direct overrides, parity, errors, and namespace non-collision are included.

## Required tests / validation

- python3 -m pytest -p no:randomly tests/test_run_dispatch.py tests/test_cli.py -q
- Parser/help snapshots for the full existing aw run family plus as/ipd.
- Mock delegation parity with exact argv and exit code.
- Negative invocation matrix for every rejected dynamic spelling and missing configuration state.
- Existing run-ledger command tests to prove no routing regression.

## Spec / documentation sync

- Update aw run help/epilog with canonical as and ipd examples while retaining every ledger example.
- Broader runner-profile documentation is Order 05.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste parser/help tests proving only fixed as and ipd were added; named/default selectors and structured overrides parse; existing run subcommands retain their handlers; and no dynamic profile command/subcommand is registered. Include the parser result for aw run as status X versus aw run status X.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste adapter-registry tests showing named runner derivation, default_runner resolution, OpenCode delegation to oc_runipd.main with no subprocess/shell/prompt duplication, direct returned exit codes, and explicit failures for missing/unknown/unimplemented runners with no host invocation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste exact mock-call parity for aw run as gem X versus aw oc run as gem X and aw run ipd X versus defaulted aw oc run X. Show model/variant/agent overrides appear exactly once and stdout/stderr/exit ownership remains delegated.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the adversarial command matrix for profiles status/report/run/show/evidence/future-command, existing run-ledger handlers, selector gem under run ipd, malformed/missing config, and every prohibited dynamic spelling. Include full existing run-family test output proving no routing regression.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Human approval is required; there are no unresolved questions.
2. Orders 01 through 03 must be executed. If oc_runipd's as grammar is absent, STOP rather than duplicate it.
3. Touch only Scope-Paths. Preserve every existing aw run subcommand and its current dispatch/exit behavior.
4. The literal as namespace is the only named-profile route. Do not add convenience aliases or unknown-token inference.
5. Run every named focused and existing run-family test and paste ACTUAL output with exit codes; unrun is not pass.
6. Commit only this plan's files, path-scoped; inspect git diff --cached --name-only; never use git add -A, bare git add, git commit -a, --no-verify, or push.
7. After every E/V item passes, run aw ipd lint --phase pre-transition, then aw ipd finalize PLAN --actor AGENT/MODEL --message SUMMARY --apply. Lifecycle transition is not an E-item.
