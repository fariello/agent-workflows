# IPD: versioned user-local runner profile schema and resolution

- Date: 2026-08-29
- Kind: child
- Concern: Runner/model shortcuts need a canonical, safe, user-local representation before any CLI accepts `as <profile>`. Reusing shell aliases, arbitrary argv strings, tracked project policy, the unrelated workflow transport-profile schema, or the main user-config allowlist would create command injection, public leakage of private model identifiers, schema collisions, or silent fallback to an unintended model.
- Scope: Add a dedicated versioned launch-profile domain and atomic XDG-backed store. Define strict validation, collision-safe names, default-runner and per-runner-default semantics, deterministic resolution/precedence, inspectable provenance, and fail-closed error behavior. Version 1 supports OpenCode (`oc`) while leaving an explicit registry seam for later hosts.
- Scope-Paths: agent_workflows/runner_profiles.py, tests/test_runner_profiles.py
- Item-Dependencies: none
- Status: to-review
- Set: runprofile
- Order: 1
- Highest E allocated: 04
- Author: codex gpt-5.6
- Id: f2mrsw

## Workflow history

- 2026-08-30 to-review (codex gpt-5.6): authored as the configuration and resolution foundation for collision-safe named runner profiles.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Create one small, independently tested source of truth for named runner profiles such as `gem`, `sonnet`, and `sol`. A profile binds a runner to structured launch fields without storing executable command strings, credentials, repository-tracked private identifiers, or behavior-changing prompt content.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: schema and persistence

- [ ] E-01 Create `agent_workflows/runner_profiles.py` with immutable typed records for a launch profile, the stored configuration, a resolved launch, and stable error classes. Define schema version 1 as `{schema_version, default_runner, defaults, profiles}` where each profile has `runner`, required exact `model`, optional `variant`, and optional `agent`; version 1 runner canonicalization maps `opencode` to `oc` and otherwise accepts only registered runners. Define profile-name grammar as lowercase letters/digits/hyphens beginning with a letter, bounded in length, with structural words `as` and `default` reserved; names such as `status`, `report`, and `run` remain legal because names are resolved only after `as`.
  - Depends on: none
  - Expected outcome: one importable schema can represent the three requested OpenCode profiles and future registered runners without allowing arbitrary argv, environment, executable, prompt, permission, token, API-key, or unknown fields.
  - Execution state: pending

- [ ] E-02 Implement an XDG-aware user-local store at `<config_dir>/runner-profiles.json`, separate from tracked `.aw/config/**` and separate from the pending main `config.json` restructuring. Reads distinguish absent from malformed; malformed/unsupported configuration raises an actionable error and MUST NOT silently behave as empty. Writes validate the entire new document, create the parent safely, preserve an existing valid file on failure, and use temp-file plus `os.replace` atomicity. Do not read, log, copy, or persist provider credentials.
  - Depends on: E-01
  - Expected outcome: private/custom model identifiers remain local to the user, interrupted writes cannot truncate configuration, and invalid configuration cannot launch an unintended default model.
  - Execution state: pending

### Task group 2: deterministic mutation and resolution

- [ ] E-03 Implement pure add/replace/remove/set-default operations and deterministic resolution. A default profile reference must resolve to an existing profile for that runner; removing a referenced profile must require an explicit clear/replacement decision. Resolution precedence is exact: explicit CLI field > explicitly named profile > per-runner default profile > host default/no argument. Generic dispatch additionally requires `default_runner` when no named profile supplies a runner. Return the requested profile name, config source, config digest, resolved runner/model/variant/agent, and a per-field source map so state/reporting can explain every value.
  - Depends on: E-01, E-02
  - Expected outcome: callers receive one auditable resolved launch, default references never dangle, and no branch guesses a model or runner when configuration is missing or broken.
  - Execution state: pending

- [ ] E-04 Implement the exhaustive runner-profile test matrix specified under Required tests / validation.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a focused suite fails on silent fallback, schema widening, dangling defaults, precedence inversion, partial writes, namespace over-reservation, or any arbitrary-argv design.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/config.py` has a fixed allowlist and a pending `reposcfg` migration that will restructure it. A separate `runner-profiles.json` avoids coupling this feature to that migration and prevents private gateway/model identifiers from entering tracked project configuration.
- `config.config_dir()` already establishes the XDG/HOME location convention. Reuse its resolved directory behavior, but do not widen `config.py`'s unrelated schema.
- Existing modules use stdlib-only dataclasses/named tuples, explicit exception types, temp-file atomic replacement, and deterministic JSON; follow those conventions.
- `workflow_profile.py` governs compiled-workflow transport semantics, and `benchmark_runners.ModelProfile` governs benchmark identity. Neither is a launch-alias configuration and neither may be overloaded.
- The CLI and runner invoke subprocesses with argv lists. The profile layer returns structured fields only and never invokes a process.

## Findings

| Finding | Consequence | Required control |
|---|---|---|
| One requested model ID is institution-specific. | Tracking profiles in the repository can disclose local topology in a public project. | User-local XDG storage is the version-1 authority. |
| Aliases will later dispatch commands. | A raw `args` string becomes a command-injection and quoting surface. | Fixed structured fields; unknown keys fail. |
| Defaults can outlive a deleted profile. | Silent fallback may run a costly or weaker model than intended. | Referential integrity and fail-closed resolution. |
| An existing config migration is pending. | Editing the primary config schema now creates avoidable conflict and migration ordering. | Dedicated versioned file. |
| Resume must be stable after configuration edits. | Re-resolving an alias mid-run changes execution identity. | Resolution returns a digest and complete snapshot for durable state. |

## Proposed changes (ordered, validatable)

1. Define the minimal launch-profile data model and strict validator.
2. Add an atomic user-local versioned store.
3. Add referentially safe mutations and explicit precedence resolution.
4. Prove malformed, adversarial, and precedence cases with unit tests.

## Deferred / out of scope (with reason)

- Arbitrary default argument arrays, environment variables, executable paths, prompts, permissions, and secrets are excluded because they materially expand the security and compatibility surface.
- Tracked/shared project profiles are deferred. A later design may add an explicit repository layer with disclosure safeguards and precedence rules; version 1 solves the user's local runner choice.
- Agy/Codex/Claude launch fields are deferred until their runner adapters define equivalent typed capabilities. The registry seam is included, but version 1 must not claim unsupported parity.
- Modifying OpenCode's own configuration or agent definitions is excluded. AW owns only its launch-profile file.

## Scope check

- Over-scope: no CLI, wizard, process launch, runner state, project config, or documentation changes.
- Under-scope: schema, storage, mutation integrity, defaults, provenance, and all resolution behavior needed by later children are included.

## Required tests / validation

- `python3 -m pytest -p no:randomly tests/test_runner_profiles.py -q`
- Fault-injection test proving an interrupted replacement leaves the previous bytes intact.
- Table-driven invalid-schema and precedence matrices with named cases.
- Search proving the module contains no `shell=True`, `eval`, `exec`, secret fields, or arbitrary `args` persistence.

## Spec / documentation sync

- Module docstring is the schema authority for version 1.
- User-facing commands and documentation land in later Set children; do not duplicate their prose here.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the schema/record definitions and table-driven test names proving the requested three profiles parse; `status`/`report`/`run` names are legal; `as`/`default` are rejected; `opencode` canonicalizes to `oc`; exact `provider/model` is required; and unknown, argv, environment, prompt, permission, token, or API-key fields fail validation.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste XDG path-resolution and store tests proving absent versus malformed distinction, unsupported-version failure, no tracked-project writes, deterministic bytes/digest, atomic replacement, and fault injection that leaves prior valid bytes unchanged. Include a search/test showing credentials and unknown fields are neither resolved nor persisted.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste table-driven mutation/resolution output for add/duplicate/replace/remove/default-clear/default-dangling cases and every precedence tier. Show one resolved record with name, source, digest, runner, model, variant, agent, and per-field provenance; show malformed or missing required generic defaults fail rather than fall back.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the complete focused-suite command, exit code, and summary, naming the invalid-schema, atomic-fault, precedence, command-like-name, and arbitrary-argv negative tests. Also paste the source search proving no shell=True/eval/exec or arbitrary command-string execution exists.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Human approval is required; there are no unresolved questions.
2. Requires no prior Set child. If the dedicated config path or schema must change, update this plan and re-review rather than improvising a second source of truth.
3. Touch only `Scope-Paths`. Do not modify `config.py`, project configuration, OpenCode configuration, or any runner/CLI file.
4. Preserve structured-only semantics: no arbitrary argv, shell fragments, credentials, executable selection, or prompt/permission settings.
5. Run every named focused test and paste ACTUAL command output with exit codes; unrun is not pass.
6. Commit only this plan's files, path-scoped; inspect `git diff --cached --name-only`; never use `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
7. After every E/V item passes, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Lifecycle transition is not an E-item.
