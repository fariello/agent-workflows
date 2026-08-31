# IPD: setup wizard integration documentation and full regression proof

- Date: 2026-08-29
- Kind: child
- Concern: A standalone profile wizard is insufficient if normal setup never offers it, but automatically configuring or defaulting a model would be a surprising behavioral and cost change. The completed feature also spans configuration, model discovery, two CLI grammars, durable state, resume, execution/verifier argv, and existing run-ledger commands; focused child tests alone can miss cross-layer drift.
- Scope: Add an optional, default-No runner-profile step to interactive aw setup; reuse the Order-02 wizard; document all canonical configuration and run forms, precedence, storage/privacy, failure behavior, and exact examples; add end-to-end tests across setup through durable launch; run generation, complete regression, packaging, and sanitizer gates; and record coordination with pending rununify.
- Scope-Paths: agent_workflows/cli.py, tests/test_cli.py, tests/test_runner_profiles_e2e.py, docs/runner-profiles.md, docs/cli-human-guide.md, README.md
- Item-Dependencies: executed:ygzq71
- Status: to-review
- Set: runprofile
- Order: 5
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: p7xhhm

## Workflow history

- 2026-08-30 to-review (codex gpt-5.6): authored as the setup, documentation, and whole-feature proof gate.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Make profile setup discoverable without changing anyone's runner/model by default, then prove the complete requested experience from wizard choice to exact OpenCode execution and stable resume.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: optional setup integration

- [ ] E-01 Call the reusable profile wizard once from the host-level interactive aw setup flow.
  - Depends on: none
  - Expected outcome: setup offers the requested alias/model/default workflow without silently creating profiles, selecting models, changing defaults, blocking repository installation, or reimplementing the interview.
  - Execution state: pending

- [ ] E-02 Add setup interaction tests for Yes with discovered model, Yes with manual model after discovery failure, multiple profiles, profile save followed by each independent default answer, No, empty, EOF, interrupt, --yes, non-TTY, existing profiles/defaults, duplicate replacement refusal, and wizard failure after repositories were installed. Assert exact prompt order, no repeated per-repository profile prompt, and byte-identical configuration for every opt-out/failure.
  - Depends on: E-01
  - Expected outcome: tests fail if setup treats --yes as consent, asks once per repository, changes defaults implicitly, loses an existing profile, or conflates optional profile failure with install failure.
  - Execution state: pending

### Task group 2: user contract and whole-feature proof

- [ ] E-03 Publish docs/runner-profiles.md as the canonical user contract and link it from the CLI guide and README.
  - Depends on: E-01
  - Expected outcome: one concise durable reference lets a user configure the three requested examples and understand every default, override, privacy, collision, and resume rule without reading implementation code.
  - Execution state: pending

- [ ] E-04 Add an end-to-end mocked test that starts from an empty XDG directory, runs the setup/profile interview to create gem as OpenCode/global default, invokes aw run ipd SELECTOR and aw run as sol SELECTOR, inspects created state.json and exact execution/verifier argv, edits aliases, resumes, and proves the frozen prior resolution remains. Add negative end-to-end cases for malformed config, unavailable default runner, unknown profile, command-like profile, no accidental durable state, and non-collision with the existing run-ledger family.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the full feature cannot pass through disconnected unit mocks that never prove wizard data reaches real runner state and both turn types.
  - Execution state: pending

- [ ] E-05 Run focused Set tests, every existing OpenCode/CLI/config/run-viewer regression affected by the change, the full suite exactly as repository instructions require, packaging/build checks, generated/no-drift checks, git diff --check, and aw sanitize --agent. Record OpenCode live smoke as optional: if a configured zero-risk test selector and credentials exist, capture version/model/variant and actual argv/output; otherwise state not run, never pass.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: actual pasted outputs prove deterministic acceptance, unrelated command/config/install behavior remains green, distributable packaging includes new modules/docs, and no local identifiers or credentials enter tracked artifacts.
  - Execution state: pending

## Project conventions discovered (Step 0)

- aw setup currently performs repository discovery/install, then one host-level shell-completion question, then orientation. Runner profiles are likewise user-level and must be asked once, not per target repository.
- --yes is appropriate for preauthorized install mutations but cannot consent to an optional model/default choice. The completion setup already provides a safe-default precedent.
- AGENTS.md requires the full suite invocation to be bare, actual output pasted, and sanitizer output consumed rather than judged manually.
- User-facing documentation may not use em/en dashes under repository conventions.
- The profile file is local and should never be copied into fixtures containing the user's actual model identifiers; tests use synthetic XDG directories and synthetic identifiers.
- rununify will later remeasure current runner behavior. Documentation must identify this Set by stable IDs so unification review can verify the profile/variant behavior was preserved.

## Findings

| Cross-layer gap | Green-washed claim | Required end-to-end evidence |
|---|---|---|
| Wizard to runner | Wizard saved successfully. | Saved profile appears in exact execution/verifier argv. |
| Default selection | Default flag exists. | aw run ipd dispatches the configured runner/profile. |
| Resume durability | Profile recorded in state. | Alias is edited/deleted and resume still uses frozen values. |
| Collision safety | Parser accepts as. | Existing run status/report/show and command-like aliases coexist. |
| Opt-in setup | Prompt defaults No. | --yes/non-TTY/EOF/empty all write no profile/default. |
| Packaging | Source tests pass. | Built artifact includes modules and installed CLI help works. |

## Proposed changes (ordered, validatable)

1. Add exactly one optional setup hook.
2. Test every setup consent and failure branch.
3. Publish the canonical UX and exclusions.
4. Prove the entire data/dispatch/state/argv/resume chain.
5. Run repository-wide and distribution gates with actual output.

## Deferred / out of scope (with reason)

- Automatic profile creation or default selection is excluded.
- Installing/changing OpenCode providers, authentication, network refresh, or global OpenCode configuration is excluded.
- Live paid-model smoke is optional and cannot replace deterministic tests.
- Repository-shared profiles and non-OpenCode runner adapters remain future work.
- Restoring alternate spellings or dynamic shortcuts is excluded; as is canonical.

## Scope check

- Over-scope: no schema, storage, model-discovery, runner internals, generic dispatcher internals, Agy, or project policy changes.
- Under-scope: setup discoverability, consent polarity, docs, end-to-end proof, packaging, full regression, generation, and sanitizer are included.

## Required tests / validation

- python3 -m pytest -p no:randomly tests/test_cli.py tests/test_runner_profiles_e2e.py -q
- All focused tests added by Orders 01 through 04.
- Existing tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py, tests/test_config.py, tests/test_run_viewer.py, and CLI conformance/help suites.
- python3 -m pytest -p no:randomly
- Repository packaging/build command documented in pyproject/CONTRIBUTING.
- Generated/no-drift checks used by CI.
- git diff --check
- aw sanitize --agent

## Spec / documentation sync

- docs/runner-profiles.md is the user-facing authority.
- README and cli-human-guide link to it rather than forking the full contract.
- CLI help examples must match tested canonical syntax and reject undocumented aliases.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste setup tests/transcripts for Yes/manual/discovered/multiple/default choices and No/empty/EOF/interrupt/--yes/non-TTY/existing/duplicate/error cases. Show the prompt occurs exactly once after repo installation, default answers are No, every opt-out/failure preserves profile bytes, and setup still reaches orientation after clean cancellation.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste the focused setup-suite command, exit code, and named-case summary. Include input/output snapshots and byte comparisons for all consent polarities, multiple repositories/profiles, duplicate refusal, existing defaults, and post-install wizard failure.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste documentation/help searches showing every canonical command, exact precedence, local storage/privacy, provider-default variant, default-No setup, resume snapshot, recovery, and rejected spelling is documented once. Paste link/parity tests proving README/guide point to the authority and CLI help examples parse.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the end-to-end test transcript from empty synthetic XDG through setup-created defaults, generic/named launch, state.json, exact execution/verifier argv, alias mutation/deletion, and stable resume. Include negative results for malformed/unknown/missing defaults, command-like names, no partial state, and ledger-command non-collision.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Paste actual output and exit codes for all focused Set suites; affected existing regressions; bare full pytest; packaging/build plus installed-help smoke; generated/no-drift checks; git diff --check; and aw sanitize --agent. State live OpenCode smoke results with version/model/variant or explicitly not run.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Human approval is required; there are no unresolved questions.
2. Orders 01 through 04 must be executed and green. Reuse their APIs; do not duplicate schema, wizard, resolver, or dispatcher behavior.
3. Touch only Scope-Paths. The setup hook is user-level, optional, TTY-only, once per setup invocation, and default No.
4. Do not include real private profile configuration, credentials, hostnames, home paths, or live session identifiers in tracked docs/tests.
5. Run every named focused, regression, full-suite, packaging, generation, diff, and sanitizer command and paste ACTUAL output with exit codes. Optional live smoke must be labeled honestly.
6. Commit only this plan's files, path-scoped; inspect git diff --cached --name-only; never use git add -A, bare git add, git commit -a, --no-verify, or push.
7. After every E/V item passes, run aw ipd lint --phase pre-transition, then aw ipd finalize PLAN --actor AGENT/MODEL --message SUMMARY --apply. Lifecycle transition is not an E-item.
