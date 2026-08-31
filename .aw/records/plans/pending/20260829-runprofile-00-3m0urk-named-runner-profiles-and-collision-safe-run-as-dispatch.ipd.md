# IPD: named runner profiles and collision-safe run-as dispatch

- Date: 2026-08-29
- Kind: orchestrator
- Concern: Users need concise, memorable runner/model selections such as gem without repeating OpenCode --model/--variant flags, while still retaining those direct flags. The preferred syntax is aw run as gem and aw oc run as gem. A shallow implementation could create dynamic commands that collide with present/future syntax, store raw shell arguments, expose private model IDs in the repository, configure defaults without consent, affect only some runner turns, or change identity on resume.
- Scope: Coordinate a five-child Set delivering strict user-local launch profiles, an OpenCode profile/model wizard, direct model/variant and run-as support in the durable OpenCode runner, host-neutral fixed dispatch plus default routing, optional setup integration, documentation, and adversarial/end-to-end validation. The orchestrator changes no product code; it validates dependency order and the whole Set.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: to-review
- Set: runprofile
- Order: 0
- Highest E allocated: 02
- Author: codex gpt-5.6
- Id: 3m0urk

## Workflow history

- 2026-08-30 to-review (codex gpt-5.6): authored a five-child execution Set from the agreed run-as UX and current repository architecture.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Deliver a safe daily UX in which a user can create named OpenCode launch profiles with a model selector, optionally make one the default, and run IPDs with:

    aw oc run as gem SELECTOR
    aw run as gem SELECTOR
    aw oc run SELECTOR
    aw run ipd SELECTOR

Direct --model, --variant, and --agent remain available. Profile aliases never become commands, defaults require explicit consent, and durable runs never change identity because a profile was later edited.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: coordinate and prove the Set

- [ ] E-01 Execute child IPDs f2mrsw, p0l1to, 3cm15q, ygzq71, and p7xhhm in dependency order. Before each child begins, confirm every declared predecessor is in the executed lifecycle state and the child's referenced APIs/files exist; do not let a later child recreate or bypass an absent earlier layer.
  - Depends on: none
  - Expected outcome: all five children reach executed with their own E/V evidence and lifecycle commits, and each layer consumes rather than duplicates the preceding authority.
  - Execution state: pending

- [ ] E-02 Perform the final CID-1 through CID-8 cross-IPD audit against integrated HEAD.
  - Depends on: E-01
  - Expected outcome: one integrated evidence package demonstrates the complete user experience and rejects green-washed partial implementations.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Child | Responsibility | Depends on |
|---:|---|---|---|---|
| 01 | f2mrsw | Versioned user-local runner profile schema and resolution | Strict structured schema, atomic XDG store, defaults, precedence, provenance | none |
| 02 | p0l1to | OpenCode profile management wizard and model selector | Model discovery/manual selection, variant choice, CRUD/default verbs, reusable wizard | 01 |
| 03 | 3cm15q | OpenCode runner model/variant/profile/durable-state integration | Direct flags, run as grammar, frozen state, exact argv for all turns/resume | 01, 02 |
| 04 | ygzq71 | Host-neutral run-as dispatch and default runner routing | Fixed aw run as and aw run ipd syntax without dynamic command collisions | 01, 03 |
| 05 | p7xhhm | Setup wizard integration, documentation, and full regression proof | Optional setup hook, canonical docs, end-to-end/full-suite/package/sanitizer proof | 01 through 04 |

The sequence is intentionally serial. Orders 02, 04, and 05 edit cli.py; Order 03 freezes the host-specific grammar that Order 04 delegates to; and a weak executor must not improvise duplicate fallback implementations when a dependency is absent.

## Completion criteria (the whole Set is done only when)

- The three requested profiles can be created through the wizard: gem = google/gemini-3.7-flash/high; sonnet = uri/its_direct/pt3-claude-sonnet-5-1m-us/medium; sol = openai/gpt-5.6-sol/medium. Tests use synthetic equivalents and tracked artifacts contain no real local credentials.
- aw oc run supports direct --model and --variant and the canonical as clause.
- aw run as PROFILE and aw run ipd exist as fixed commands; aw PROFILE, aw PROFILErun, aw run PROFILE, run-PROFILE, run:PROFILE, and alternate with/using/w spellings do not.
- Profiles named status/report/run/show/evidence cannot shadow real commands.
- Explicit CLI fields override only matching profile fields; named profile overrides per-runner default; per-runner default applies to aw oc run; generic default routing requires configured default_runner.
- The resolved name/source/digest/runner/model/variant/agent/provenance is stored before execution and reused unchanged by all turns and resumes.
- Unknown/malformed/wrong-runner profiles fail before durable run side effects.
- Setup offers configuration once, TTY-only, default No; --yes/non-TTY/empty/EOF never create a profile or set a default.
- Existing OpenCode runner, run-ledger, setup/install, config, packaging, generated-artifact, and full test suites pass with actual output.
- rununify does not erase the new behavior: its later E-01 inventory is taken from post-runprofile HEAD and classifies/preserves the profile resolver, variant argv, and durable launch identity.

## Cross-IPD validation

- CID-1 Schema-to-wizard: every wizard field is accepted by exactly one schema field; no raw argv/secret side channel exists.
- CID-2 Wizard-to-runner: saved and default profiles produce the exact model/variant/agent argv in both execution and independent verifier turns.
- CID-3 Host-to-generic parity: aw run as gem and aw oc run as gem delegate to equivalent normalized runner arguments and exit behavior.
- CID-4 Durability: changing/deleting an alias after start does not change resume or verifier identity.
- CID-5 Namespace: current run-ledger subcommands and command-like profile names coexist; rejected shortcut spellings remain rejected.
- CID-6 Consent: every setup opt-out/unattended path writes no profile/default.
- CID-7 Distribution: installed/built package contains new modules and help/docs match tested syntax.
- CID-8 Sequencing: rununify is executed only after re-inventorying this behavior, never from its older measurement snapshot.

## Deferred / out of scope (with reason)

- Repository-tracked/shared profiles are deferred because a requested model identifier may expose institutional topology; version 1 is explicitly user-local.
- Agy, Codex, and Claude profile adapters are deferred until each has typed launch capability and durable-state semantics; version 1 must not claim unsupported parity.
- Arbitrary argv, shell fragments, executable paths, environment variables, prompts, permissions, and credentials are excluded from profiles.
- Modifying OpenCode configuration/agents/providers or refreshing its model catalog is excluded.
- Bare aw run SELECTOR and dynamic top-level/subcommand aliases are excluded to preserve command namespace.
- Live paid-model calls are optional smoke evidence, never deterministic acceptance.
- Runner deduplication is owned by rununify and follows this behavior change.

## Scope check

- Over-scope: no product paths are owned by the orchestrator; children own all implementation. No provider/authentication changes, tracked profiles, non-OpenCode adapters, or runner refactor.
- Under-scope: schema, CRUD, model/variant wizard, both canonical run-as surfaces, direct flags, defaults, setup integration, durable state/resume, collision safety, docs, packaging, and full proof are all assigned.

## Required tests / validation

- Every child-specific command and pasted evidence requirement.
- Integrated end-to-end empty-XDG wizard to generic launch to state/argv/verifier to edited-profile resume.
- Full suite: python3 -m pytest -p no:randomly
- Packaging/build and installed-help smoke.
- Generated/no-drift checks, git diff --check, and aw sanitize --agent.
- AST/search audit proving no dynamic profile commands and no arbitrary shell/argv profile execution.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the five child terminal paths, lifecycle commit IDs, pre/post-transition lint summaries, and each child's final focused-test output. Show dependency order from history/commits and confirm no child duplicated a missing predecessor API. A child merely marked executed without concrete E/V evidence fails this validation.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste the integrated CID-1 through CID-8 audit with exact commands, state excerpts, execution/verifier/resume argv, setup opt-out bytes, parser namespace matrix, package/help evidence, full-suite output, sanitizer result, and current HEAD. Cite the updated rununify inventory/review note proving it will preserve post-Set profile/variant/durable-identity behavior. Any missing layer, unrun command, or narrative-only claim fails this validation.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Human approval is required; there are no unresolved questions.
2. Execute children serially in the table order. A missing predecessor, altered API, or overlapping active edit is a child-scoped STOP; do not fabricate compatibility code.
3. The orchestrator touches only Scope-Paths and authors no product code. Product changes and commits belong to children.
4. This Set executes before rununify extracts shared runner code. If extraction has already started, STOP and re-review all runner scopes against the new boundary.
5. Never add dynamic profile commands, arbitrary argv/shell profiles, tracked private profiles, implicit defaults, or unsupported host claims.
6. Validation requires actual pasted commands, exit codes, state excerpts, exact argv, and negative-test results. Lint or unit-test structure alone is not proof of end-to-end behavior.
7. Commit only this plan's files, path-scoped; inspect git diff --cached --name-only; never use git add -A, bare git add, git commit -a, --no-verify, or push.
8. After all children and both orchestrator E/V items pass, run aw ipd lint --phase pre-transition, then aw ipd finalize PLAN --actor AGENT/MODEL --message SUMMARY --apply. Lifecycle transition is not an E-item.
