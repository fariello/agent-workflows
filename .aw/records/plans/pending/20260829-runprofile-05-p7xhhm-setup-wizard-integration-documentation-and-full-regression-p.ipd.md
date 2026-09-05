# IPD: setup wizard integration documentation and full regression proof

- Date: 2026-08-29
- Kind: child
- Concern: A standalone profile wizard is insufficient if normal setup never offers it, but automatically configuring or defaulting a model would be a surprising behavioral and cost change. The completed feature also spans configuration, model discovery, two CLI grammars, durable state, resume, execution/verifier argv, and existing run-ledger commands; focused child tests alone can miss cross-layer drift.
- Scope: Add an optional, default-No runner-profile step to interactive aw setup; reuse the Order-02 wizard; document all canonical configuration and run forms, precedence, storage/privacy, failure behavior, and exact examples; add end-to-end tests across setup through durable launch; run generation, complete regression, packaging, and sanitizer gates; and record coordination with pending rununify.
- Scope-Paths: agent_workflows/cli.py, tests/test_cli.py, tests/test_runner_profiles_e2e.py, docs/runner-profiles.md, docs/cli-human-guide.md, README.md
- Item-Dependencies: executed:ygzq71
- Status: reviewed
- Readiness: go-pending-approval
- Set: runprofile
- Order: 5
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: p7xhhm

## Workflow history
- 2026-09-04 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): READINESS BOOKKEEPING, no scope or content change. Added the `- Readiness:` front-matter field, which postdates this plan (the field is a later addition to the review contract, `plan-review.md:377-398`, and automation FAILS CLOSED when it is absent, so a clean plan without it is simply never picked up). Value `go-pending-approval`.
  AND SUPERSEDED THE STALE `REVIEWED - OPEN QUESTIONS` VERDICT, which is the substantive half. That verdict was correct when written on 2026-09-01: the Set carried ONE blocking question, OQ-01, asking whether approved `runnamecollapse-01` (`0soncw`) had to land first, and the maintainer answered ORDER: `0soncw` FIRST, which made the Set depend on `0soncw` reaching `executed` AND inherited `0soncw`'s own unresolved blocking question. BOTH CONDITIONS ARE NOW DISCHARGED, verified rather than assumed: `0soncw` is in `.aw/records/plans/executed/` with `Status: executed`, and its three open questions (OQ-01 permanence, OQ-02 noun placement, OQ-03 subcommand-versus-viewer disambiguation, the one that gated this Set) are all `Status: resolved`. This plan's own OQ-01 is `Status: resolved`, and `aw ipd lint` reports no unresolved blocking question. So the verdict is stated here as APPROVE WITH REVISIONS APPLIED, superseding the neutral one, on the maintainer's 2026-09-04 reading that the outstanding record was bookkeeping rather than an unanswered question. NO re-review of the plan's technical content was performed in this pass and none is claimed: round 1's findings and their fixes stand as recorded.

- 2026-09-01 reviewed (aw set): plan-review round 1 (whole Set): REVIEWED - OPEN QUESTIONS. Blocking OQ on the aw run noun retirement by approved 0soncw; f2mrsw additionally APPROVE WITH REVISIONS APPLIED for the two maintainer-directed validate findings. See .aw/records/reviews/.
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1 (whole `runprofile` Set, 6 plans, reviewed together at HEAD 6a29f9c0): REVIEWED - OPEN QUESTIONS. BLOCKER PR-001, escalated ONCE as blocking OQ-01 on the orchestrator 3m0urk: this Set builds its entire grammar on the `aw run` noun (measured: `aw run as` x16, `aw run ipd` x12) that APPROVED 0soncw is RETIRING behind a nonzero-exit deprecation stub, and NO plan in the Set mentions 0soncw even once. They are COMPLEMENTARY not contradictory (0soncw frees the name "for a future driver verb", which is this Set), so the fix is ORDER: 0soncw first, then this Set. Reversed, `aw run as gem` would start exiting nonzero. Not agent-resolvable: a cross-Set order decision, and 0soncw itself still carries an unresolved blocking OQ-03. PR-002 MEDIUM, fixed: the Set carries ZERO file:line citations across all six plans (versus 9/4/5 in the comparable 6lu3rq/m73aet/wlxkoz); spot-checked claims were TRUE so this is evidence discipline, and each plan now requires measuring and citing every "already" claim. PR-003 MEDIUM, fixed: this child PUBLISHES the `aw run as` grammar to users (docs/runner-profiles.md, docs/cli-human-guide.md, README.md), so a wrong OQ-01 answer would ship documentation telling readers to run a command that exits nonzero; a stale doc outlives a merge conflict. Doc writes are now conditional on OQ-01 and must be confirmed against the shipped parser and docs_check. Review artifact: .aw/records/reviews/20260831-runprofile-*-p7xhhm-*.review.md

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
| Sequencing against an approved plan | FOUND AT REVIEW (PR-001, BLOCKER): APPROVED `0soncw` is RETIRING the `aw run` noun this plan builds on (its E-05 leaves a nonzero-exit deprecation stub), and no plan in this Set mentions it. They are complementary, not contradictory: `0soncw` frees the name "for a future driver verb", which is this Set. Escalated as blocking OQ-01 on the orchestrator `3m0urk`; recommended order is `0soncw` FIRST, then this Set. Do NOT execute this plan until that order is settled. | Settle orchestrator OQ-01 before executing. |
| Unverifiable "already" claims | FOUND AT REVIEW (PR-002): this plan carries ZERO `file:line` citations, as does every member of this Set (measured: 0 across all six, versus 9/4/5 in the comparable `6lu3rq`/`m73aet`/`wlxkoz` plans). The claims spot-checked at review were TRUE, so this is evidence discipline rather than incorrectness, but an executor cannot cheaply re-verify a premise. MEASURE and cite `file:line` for every "already" claim before relying on it; HEAD moves hourly here. | Cite `file:line` for each, measured at the current HEAD. |
| Publishing a grammar that may be retired | FOUND AT REVIEW (PR-003): this plan writes `docs/runner-profiles.md`, `docs/cli-human-guide.md` and `README.md`, i.e. it PUBLISHES the `aw run as` grammar to users. If OQ-01 resolves the wrong way the committed docs would tell a reader to run a command that exits nonzero. A stale doc outlives a merge conflict. `docs_check.check_aw_commands` also validates `aw <sub>` mentions against `known_subcommands()`. | Make the doc writes CONDITIONAL on OQ-01; confirm the final verb spelling against the shipped parser and `docs_check` immediately before writing. |

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

### OQ-01: Must APPROVED `runnamecollapse-01` (`0soncw`) land BEFORE this plan?

- Blocking: yes
- Status: resolved
- Owner: none
- Finding: PR-001
- Resolution or deferral rationale: MAINTAINER DECIDED 2026-08-31: ORDER IS `0soncw` FIRST, THEN THIS SET. The rename vacates the `aw run` noun (leaving its deprecation stub), and this Set then claims the vacated name for real dispatch. This is the order both plans were designed for and the only one in which nothing breaks. CONSEQUENCE, stated plainly: this Set now DEPENDS on `0soncw` reaching `executed`, and `0soncw` itself carries an unresolved blocking question (how `aw runs` distinguishes a subcommand from a viewer target), so that question gates this Set too. Do NOT execute any member of this Set until `0soncw` has landed. ORIGINAL FINDING AS RAISED: RAISED AT REVIEW as a BLOCKER, not agent-resolvable. This plan builds on the `aw run` noun that APPROVED `0soncw` is RETIRING behind a nonzero-exit deprecation stub, and no plan in this Set mentions `0soncw`. The two are COMPLEMENTARY (`0soncw` frees the name "for a future driver verb", which is this Set), so the fix is ORDER, not redesign: recommended `0soncw` FIRST, then this Set. Reversed, `aw run as <profile>` would begin exiting nonzero. A human must answer because it is a cross-Set execution-order decision AND `0soncw` carries its own unresolved blocking OQ-03. THE SET-LEVEL QUESTION IS OQ-01 ON THE ORCHESTRATOR `3m0urk`; this copy exists because the review-finding escalation gate requires the plan carrying the open finding to name it, and answering the orchestrator's OQ-01 answers this one too. Do not answer them differently.

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
