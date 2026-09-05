# IPD: versioned user-local runner profile schema and resolution

- Date: 2026-08-29
- Kind: child
- Concern: Runner/model shortcuts need a canonical, safe, user-local representation before any CLI accepts `as <profile>`. Reusing shell aliases, arbitrary argv strings, tracked project policy, the unrelated workflow transport-profile schema, or the main user-config allowlist would create command injection, public leakage of private model identifiers, schema collisions, or silent fallback to an unintended model.
- Scope: Add a dedicated versioned launch-profile domain and atomic XDG-backed store. Define strict validation, collision-safe names, default-runner and per-runner-default semantics, deterministic resolution/precedence, inspectable provenance, and fail-closed error behavior. Version 1 supports OpenCode (`oc`) while leaving an explicit registry seam for later hosts.
- Scope-Paths: agent_workflows/runner_profiles.py, tests/test_runner_profiles.py
- Item-Dependencies: executed:0soncw
- Status: executed
- Readiness: go-pending-approval
- Set: runprofile
- Order: 1
- Highest E allocated: 04
- Author: codex gpt-5.6
- Id: f2mrsw

## Workflow history
- 2026-09-05 executed (aw oc run): aw oc run self-finalize: f2mrsw verified (set runprofile, attempt 1).
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-01 reviewed (aw set): set Item-Dependencies to executed:0soncw
- 2026-09-01 reviewed (aw set): plan-review round 1 (whole Set): REVIEWED - OPEN QUESTIONS. Blocking OQ on the aw run noun retirement by approved 0soncw; f2mrsw additionally APPROVE WITH REVISIONS APPLIED for the two maintainer-directed validate findings. See .aw/records/reviews/.
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1 (whole `runprofile` Set, 6 plans, reviewed together at HEAD 6a29f9c0): REVIEWED - OPEN QUESTIONS. BLOCKER PR-001, escalated ONCE as blocking OQ-01 on the orchestrator 3m0urk: this Set builds its entire grammar on the `aw run` noun (measured: `aw run as` x16, `aw run ipd` x12) that APPROVED 0soncw is RETIRING behind a nonzero-exit deprecation stub, and NO plan in the Set mentions 0soncw even once. They are COMPLEMENTARY not contradictory (0soncw frees the name "for a future driver verb", which is this Set), so the fix is ORDER: 0soncw first, then this Set. Reversed, `aw run as gem` would start exiting nonzero. Not agent-resolvable: a cross-Set order decision, and 0soncw itself still carries an unresolved blocking OQ-03. PR-002 MEDIUM, fixed: the Set carries ZERO file:line citations across all six plans (versus 9/4/5 in the comparable 6lu3rq/m73aet/wlxkoz); spot-checked claims were TRUE so this is evidence discipline, and each plan now requires measuring and citing every "already" claim. This plan is the Set's strongest and has NO scope collision (two new files), so it is executable independently. TWO MAINTAINER-DIRECTED REVISIONS APPLIED, carrying the per-model verification default here because this plan owns the schema and depends on nothing: E-01 gains an optional TRI-STATE per-profile `validate` (plus one in `defaults`), motivated by the measured Opus-off / Gemini-on split; and E-03 gains an explicit tested PRECEDENCE chain where an explicit --validate/--no-validate flag ALWAYS beats a stored default, because an unstated precedence is how vju5ba happened and a profile silently beating a flag would reproduce it inverted. Verdict APPROVE WITH REVISIONS APPLIED (no blocking OQ of its own; the Set-level OQ-01 still gates the Set). Review artifact: .aw/records/reviews/20260831-runprofile-*-f2mrsw-*.review.md

- 2026-08-30 to-review (codex gpt-5.6): authored as the configuration and resolution foundation for collision-safe named runner profiles.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Create one small, independently tested source of truth for named runner profiles such as `gem`, `sonnet`, and `sol`. A profile binds a runner to structured launch fields without storing executable command strings, credentials, repository-tracked private identifiers, or behavior-changing prompt content.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: schema and persistence

- [x] E-01 Create `agent_workflows/runner_profiles.py` with immutable typed records for a launch profile, the stored configuration, a resolved launch, and stable error classes. Define schema version 1 as `{schema_version, default_runner, defaults, profiles}` where each profile has `runner`, required exact `model`, optional `variant`, and optional `agent`; version 1 runner canonicalization maps `opencode` to `oc` and otherwise accepts only registered runners. ADDED AT REVIEW (PR-001, maintainer-directed): each profile ALSO carries an OPTIONAL `validate` boolean, and the top-level `defaults` object carries an optional `validate` too. This is the per-model verification default: absent means "not specified at this level" and MUST NOT be conflated with `false`, so use a true tri-state (present-true / present-false / absent) rather than defaulting the field to `false` at parse time. Motivation, measured: on the maintainer's primary model an independent verifier turn added only nits for roughly 33% extra cost, so it runs with validation OFF, while Gemini needs it ON; with no per-profile field that choice is a flag the operator must remember every invocation, which is how backlog `vju5ba` went unnoticed across five overnight runs. This plan owns the schema and depends on nothing, which is why the field lands here rather than in `novalnomerge-01` (`evgi9n`), where it is explicitly deferred to this plan. Define profile-name grammar as lowercase letters/digits/hyphens beginning with a letter, bounded in length, with structural words `as` and `default` reserved; names such as `status`, `report`, and `run` remain legal because names are resolved only after `as`.
  - Depends on: none
  - Expected outcome: one importable schema can represent the three requested OpenCode profiles and future registered runners without allowing arbitrary argv, environment, executable, prompt, permission, token, API-key, or unknown fields.
  - Execution state: performed

- [x] E-02 Implement an XDG-aware user-local store at `<config_dir>/runner-profiles.json`, separate from tracked `.aw/config/**` and separate from the pending main `config.json` restructuring. Reads distinguish absent from malformed; malformed/unsupported configuration raises an actionable error and MUST NOT silently behave as empty. Writes validate the entire new document, create the parent safely, preserve an existing valid file on failure, and use temp-file plus `os.replace` atomicity. Do not read, log, copy, or persist provider credentials.
  - Depends on: E-01
  - Expected outcome: private/custom model identifiers remain local to the user, interrupted writes cannot truncate configuration, and invalid configuration cannot launch an unintended default model.
  - Execution state: performed

### Task group 2: deterministic mutation and resolution

- [x] E-03 Implement pure add/replace/remove/set-default operations and deterministic resolution. ADDED AT REVIEW (PR-002, maintainer-directed): resolution MUST also settle `validate` through an explicit, tested precedence chain, highest first: (1) an explicit `--validate`/`--no-validate` flag on the invocation, (2) the resolved profile's own `validate`, (3) the top-level `defaults.validate`, (4) the shipped default. AN EXPLICIT FLAG ALWAYS WINS; a stored default must never silently override it. This is not a nicety: an unstated precedence is exactly how `vju5ba` happened (two independently sensible defaults that quietly cancelled each other out), and a profile beating an explicit flag would reproduce that defect inverted, making the flag a lie. Because `validate` is tri-state, an ABSENT value at one level must fall through to the next rather than being read as `false`. A default profile reference must resolve to an existing profile for that runner; removing a referenced profile must require an explicit clear/replacement decision. Resolution precedence is exact: explicit CLI field > explicitly named profile > per-runner default profile > host default/no argument. Generic dispatch additionally requires `default_runner` when no named profile supplies a runner. Return the requested profile name, config source, config digest, resolved runner/model/variant/agent, and a per-field source map so state/reporting can explain every value.
  - Depends on: E-01, E-02
  - Expected outcome: callers receive one auditable resolved launch, default references never dangle, and no branch guesses a model or runner when configuration is missing or broken.
  - Execution state: performed

- [x] E-04 Implement the exhaustive runner-profile test matrix specified under Required tests / validation.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a focused suite fails on silent fallback, schema widening, dangling defaults, precedence inversion, partial writes, namespace over-reservation, or any arbitrary-argv design.
  - Execution state: performed

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
| ADDED AT REVIEW (PR-001): a profile could not say whether verification runs. | The per-model choice becomes a flag the operator must remember per invocation; measured, that is how `vju5ba` went unnoticed for five overnight runs. | An optional tri-state `validate` per profile, plus one in `defaults` (E-01). |
| ADDED AT REVIEW (PR-002): `validate` precedence was unstated. | A stored profile default could silently override an EXPLICIT `--validate`/`--no-validate` flag, reproducing `vju5ba` inverted and making the flag a lie. | A tested precedence chain, explicit flag first, with absent falling through rather than reading as `false` (E-03). |

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
- ADDED AT REVIEW (PR-001/PR-002): a `validate` PRECEDENCE matrix with one named case per level, proving an explicit flag beats a profile value, a profile value beats `defaults.validate`, `defaults.validate` beats the shipped default, and an ABSENT value at any level falls through instead of being read as `false`. Also assert the Opus-off / Gemini-on shape end to end: two profiles differing only in `validate` resolve to different verification decisions from the same command line.
- NOTE the repo suite contract: run the suite BARE (`python3 -m pytest`). The `-p no:randomly` above disables the order randomization that surfaces order-dependence bugs; prefer a bare run and add flags only with a stated reason.

## Spec / documentation sync

- Module docstring is the schema authority for version 1.
- User-facing commands and documentation land in later Set children; do not duplicate their prose here.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the schema/record definitions and table-driven test names proving the requested three profiles parse; `status`/`report`/`run` names are legal; `as`/`default` are rejected; `opencode` canonicalizes to `oc`; exact `provider/model` is required; and unknown, argv, environment, prompt, permission, token, or API-key fields fail validation.
  - Observed evidence: RECORDS AND SCHEMA (`agent_workflows/runner_profiles.py`): `LaunchProfile` (frozen dataclass:
    `runner`, `model`, `variant=None`, `agent=None`, `validate=None`), `ProfileConfig` (frozen;
    `schema_version`, `default_runner`, `default_profiles`, `validate`, `profiles`, `source`,
    `present`; its `__post_init__` wraps both mappings in `MappingProxyType` so a loaded config
    cannot be mutated in place), `ResolvedLaunch` (NamedTuple carrying `runner`/`model`/`variant`/
    `agent`/`validate` plus `requested_profile`, `applied_profile`, `config_source`,
    `config_present`, `config_digest`, `provenance`), `RunnerSpec` (the registry seam), and the
    error hierarchy `RunnerProfileError` -> `ProfileSchemaError` / `ProfileStoreError` /
    `ProfileNotFoundError` / `ProfileExistsError` / `ProfileResolutionError`.

    ACTUAL OUTPUT, `python3 -m pytest tests/test_runner_profiles.py -o addopts="" -q -s -k
    "RequestedProfilesParse or ProfileNameGrammar or RunnerCanonicalization or
    ForbiddenAndUnknownField or DocumentValidation or TriState"`:

    ```
    ..three requested profiles round-trip: ['gem', 'sol', 'sonnet']
    .tri-state preserved: present-false serialized, absent omitted
    ....unsupported version fails closed: unsupported schema_version 99; this aw understands [1]. Upgrade aw rather than editing the file: treating an unknown shape as empty would silently launch the wrong model.
    ....serialized document contains no credential-shaped field
    .forbidden-by-name fields refused (24): ['api_key', 'apikey', 'args', 'argv', 'auth', 'bearer', 'cmd', 'command', 'credential', 'credentials', 'env', 'environment', 'exec', 'executable', 'headers', 'key', 'password', 'permission', 'permissions', 'prompt', 'secret', 'shell', 'system_prompt', 'token']
    ..canonicalization: opencode/OpenCode/oc -> oc
    ..version 1 registers exactly: ['oc']; agy/codex/claude refused (no parity claim)
    ..command-like names legal: status, report, run, show, evidence, start, verify-ledger
    .reserved by the grammar: as, default
    ..
    21 passed, 54 deselected in 0.11s
    ```

    NAMED TABLE-DRIVEN TESTS: `RequestedProfilesParseTests::test_three_requested_profiles_parse_and_round_trip`
    (the three requested profiles, as SYNTHETIC identifiers per the orchestrator's requirement,
    round-trip and `to_document()` is stable), `::test_records_are_immutable`,
    `::test_optional_fields_are_omitted_not_nulled`;
    `ProfileNameGrammarTests::test_command_like_names_are_legal` (7 names incl. `status`/`report`/
    `run`), `::test_grammar_words_are_reserved` (`as`/`default`), `::test_invalid_names_are_rejected`
    (11 named cases), `::test_max_length_boundary_is_inclusive`;
    `RunnerCanonicalizationTests::test_opencode_canonicalizes_to_oc`,
    `::test_only_registered_runners_are_accepted`, `::test_profile_runner_is_stored_canonicalized`;
    `ModelAndFieldValidationTests::test_exact_provider_model_is_required` (15 named cases incl.
    `missing-provider`, `whitespace`, `quote`, `backtick`, `dollar`, `semicolon`, `pipe`,
    `backslash`), `::test_multi_segment_private_shape_is_accepted`, `::test_missing_required_fields_fail`,
    `::test_variant_and_agent_are_bounded_tokens`;
    `ForbiddenAndUnknownFieldTests::test_every_forbidden_capability_field_is_refused_by_name` (all
    24 forbidden keys above, each asserting the message says "BY DESIGN"),
    `::test_unknown_field_is_refused`, `::test_unknown_document_and_defaults_keys_are_refused`,
    `::test_a_credential_can_never_be_persisted`; `DocumentValidationTests` (3 tests);
    `TriStateValidateFieldTests` (4 tests, proving absent stays `None` and present-false is
    preserved and serialized while absent is OMITTED, so the two stay distinguishable on disk).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Paste XDG path-resolution and store tests proving absent versus malformed distinction, unsupported-version failure, no tracked-project writes, deterministic bytes/digest, atomic replacement, and fault injection that leaves prior valid bytes unchanged. Include a search/test showing credentials and unknown fields are neither resolved nor persisted.
  - Observed evidence: ACTUAL OUTPUT, `python3 -m pytest tests/test_runner_profiles.py -o addopts="" -q -s -k
    "StorePath or StoreReadWrite or AtomicFaultInjection or NoSilentFallback"`:

    ```
    broken config raises at load; no code path resolves it to a host default
    ...invalid document refused at save; previous bytes unchanged
    ...deterministic bytes; digest cb6a6b5a16a63a20...
    ..absent -> empty(present=False); malformed -> ProfileSchemaError, never empty
    ...store path under XDG: .../agent-workflows/runner-profiles.json
    .separate from config.json, inside the user config dir, never in the repo tree
    .fault injected at os.replace: prior bytes identical, no temp leak, still loadable
    ...
    16 passed, 59 deselected in 0.17s
    ```

    XDG PATH RESOLUTION: `StorePathTests::test_honors_xdg_config_home` (asserts
    `store_path() == $XDG_CONFIG_HOME/agent-workflows/runner-profiles.json`),
    `::test_falls_back_to_home_config` (asserts `~/.config/agent-workflows` and NOT `~/` itself),
    `::test_is_separate_from_the_main_config_and_not_in_the_repo` (asserts
    `store_path() != config.config_path()`, that its parent IS `config.config_dir()` so there is
    ONE XDG convention, and that the resolved path does NOT start with the repository root, which
    is the no-tracked-project-writes proof).

    ABSENT vs MALFORMED: `StoreReadWriteTests::test_absent_is_distinct_from_malformed` (absent ->
    `present=False` with empty profiles; malformed -> `ProfileSchemaError`), and
    `::test_malformed_shapes_all_raise_rather_than_degrade` across 5 named cases
    (`unsupported-version`, `unknown-key`, `bad-profile`, `dangling-default`, `json-array`).
    UNSUPPORTED VERSION: `DocumentValidationTests::test_unsupported_version_fails_closed_and_says_why`
    (message pasted in V-01) plus `StoreReadWriteTests::test_refuses_to_overwrite_a_future_version`
    (asserts "Nothing was changed" AND that the on-disk bytes are unchanged).

    DETERMINISTIC BYTES AND DIGEST: `::test_save_then_load_round_trips_with_deterministic_bytes`
    (save -> load -> save produces IDENTICAL bytes, and the reloaded digest equals the original),
    `::test_digest_changes_with_content_and_is_stable_otherwise`.

    ATOMIC REPLACEMENT AND FAULT INJECTION (the plan's named requirement): `save()` writes a temp
    file in the SAME directory then `os.replace`. `AtomicFaultInjectionTests::test_fault_during_replace_preserves_prior_bytes_and_cleans_up`
    monkeypatches `os.replace` to raise `OSError(5)`, then asserts the prior bytes are BYTE-IDENTICAL,
    no `.tmp` file leaked, and the file is still loadable with all three profiles;
    `::test_fault_during_write_preserves_prior_bytes` injects `OSError(28)` (ENOSPC) at `os.fdopen`;
    `::test_a_keyboardinterrupt_mid_write_is_not_swallowed` proves the `except BaseException`
    cleanup re-raises rather than converting an interrupt into a silent success. Also
    `::test_save_validates_the_whole_document_before_writing` (a hand-built `ProfileConfig` that
    bypassed the mutators is still refused at save, previous bytes unchanged) and
    `::test_no_leftover_temp_files_after_a_successful_write`.

    CREDENTIALS AND UNKNOWN FIELDS NEITHER RESOLVED NOR PERSISTED:
    `ForbiddenAndUnknownFieldTests::test_a_credential_can_never_be_persisted` (the serialized
    document contains none of `token`/`api_key`/`secret`/`password`/`Authorization`/`Bearer`),
    `SourceAuditTests::test_no_arbitrary_argv_or_credential_field_is_persistable` (asserts the
    ALLOWED key sets literally, so widening them requires editing the test), and
    `::test_the_module_does_not_read_credentials_from_the_environment`. Source search over
    executable lines:

    ```
    $ grep -nE "shell=True|\beval\(|\bexec\(|subprocess|os\.system|os\.popen|os\.environ|getenv" agent_workflows/runner_profiles.py
    79:Pure stdlib, no third-party imports, no network, no subprocess (D138/D139).
    ```

    The single hit is the module DOCSTRING saying it uses no subprocess; the audit test excludes
    docstrings STRUCTURALLY (an AST walk over string-literal statements), not by substring
    heuristic, and asserts the surviving code-line set is non-empty so the audit cannot go vacuous.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Paste table-driven mutation/resolution output for add/duplicate/replace/remove/default-clear/default-dangling cases and every precedence tier. Show one resolved record with name, source, digest, runner, model, variant, agent, and per-field provenance; show malformed or missing required generic defaults fail rather than fall back.
  - Observed evidence: ACTUAL OUTPUT, `python3 -m pytest tests/test_runner_profiles.py -o addopts="" -q -s -k
    "Mutation or ResolutionPrecedence or ResolvedProvenance or ValidatePrecedence"`:

    ```
    resolved record: {"agent": "build", "applied_profile": "agentful", "config_digest": "d7a761c245f0ea35...", "config_source": "runner-profiles.json", "model": "example-vendor/flash-3.7", "provenance": {"agent": "profile", "model": "profile", "runner": "explicit", "validate": "shipped-default", "variant": "profile"}, "requested_profile": "agentful", "runner": "oc", "validate": false, "variant": "high"}
    ..absent falls through (None+defaults=True -> True); present-false does not
    .level 1: explicit flag won all 18 combinations
    .level 4: shipped default False (matches --validate today)
    .level 2: profile `validate` beat `defaults.validate` in all 4 combinations
    .level 3: `defaults.validate` beat the shipped default (both polarities)
    ..same command line, different verification decision: strong=False cheap=True
    ..tier 4 host default: no model/variant/agent argument, recorded as host-default
    .tier 1 explicit: {'runner': 'explicit', 'model': 'explicit', 'variant': 'explicit', 'agent': 'explicit', 'validate': 'shipped-default'}
    .tier 2 named profile: sol {'runner': 'explicit', 'model': 'profile', 'variant': 'profile', 'agent': 'host-default', 'validate': 'shipped-default'}
    .tier 3 per-runner default: gem {'runner': 'explicit', 'model': 'default-profile', 'variant': 'default-profile', 'agent': 'host-default', 'validate': 'shipped-default'}
    .unknown profile / unregistered runner: raise, never silently fall back
    .profile named 'status' resolves after `as`, shadowing nothing
    ..generic dispatch: no default_runner -> refuse; configured -> route to oc
    ......referenced default: refuse / clear / replace, each explicit
    ..add: pure, duplicate refused, --replace honored
    ....
    29 passed, 46 deselected in 0.13s
    ```

    MUTATIONS: `MutationTests::test_add_is_pure_and_refuses_a_silent_duplicate` (asserts the input
    config is UNCHANGED, a duplicate raises `ProfileExistsError`, `replace=True` overwrites, and the
    pre-replace config still holds the old model), `::test_add_validates_through_the_schema`,
    `::test_remove_unknown_raises`, `::test_removing_a_referenced_default_requires_an_explicit_decision`
    (bare remove raises `ProfileResolutionError` saying "Decide explicitly"; `clear_default=True`
    clears it; `replacement="sol"` repoints it; a nonexistent replacement raises; passing BOTH
    raises), `::test_removing_an_unreferenced_profile_is_straightforward`,
    `::test_default_profile_setters` (set / read through the `opencode` alias / clear / clear again
    idempotently / set-unknown raises), `::test_default_runner_setter_canonicalizes_and_clears`,
    `::test_validate_default_setter_supports_unset`.

    DANGLING DEFAULTS: `::test_a_dangling_default_cannot_be_constructed_through_the_mutators` plus
    the `dangling-default` case in `StoreReadWriteTests::test_malformed_shapes_all_raise_rather_than_degrade`.
    `_validate_referential_integrity` runs on EVERY mutation (via `_replace`), on `from_document`,
    and again on `save`, and `resolve` re-proves the default resolves via `cfg.get(...)`, so no
    path yields a dangling reference.

    EVERY LAUNCH PRECEDENCE TIER (each printed above): tier 1 explicit fields beat a named profile;
    tier 2 a named profile beats the per-runner default; tier 3 the per-runner default applies with
    no profile named; tier 4 nothing configured -> `model`/`variant`/`agent` are `None` (pass NO
    argument) recorded as `host-default`, never a guess. `::test_partial_explicit_override_keeps_the_other_profile_fields`
    proves an explicit `--variant` overrides ONLY `variant` while `agent` still comes from the
    profile.

    GENERIC DISPATCH FAILS RATHER THAN FALLS BACK:
    `::test_generic_dispatch_requires_default_runner` (message asserts "does not guess"), while
    `::test_generic_dispatch_with_a_named_profile_needs_no_default_runner` shows a named profile
    supplies the runner. `::test_unknown_and_wrong_runner_profiles_fail_rather_than_fall_back`
    covers unknown profile (`ProfileNotFoundError`), unregistered runner and reserved name
    (`ProfileSchemaError`); `::test_explicit_field_values_are_validated_at_resolution` covers a
    malformed explicit `model`/`variant`/`agent`; `NoSilentFallbackTests::test_a_broken_file_never_resolves_to_the_host_default`
    closes the loop from disk.

    THE RESOLVED RECORD is pasted verbatim above from
    `ResolvedProvenanceRecordTests::test_resolved_record_carries_the_full_auditable_snapshot`,
    which loads from a REAL file on disk and asserts `config_source == str(path)`,
    `config_present is True`, `config_digest` matches `^[0-9a-f]{64}$`, the provenance keys are
    exactly `{agent, model, runner, validate, variant}`, and every provenance VALUE is in the
    closed `PROVENANCE_VALUES` vocabulary. `::test_provenance_mapping_is_read_only` proves the map
    cannot be mutated after resolution.

    THE `validate` PRECEDENCE CHAIN (E-03's review-added requirement) is proven level by level:
    level 1 an explicit flag won ALL 18 combinations of (profile in {True,False,None}) x
    (defaults in {True,False,None}) x (flag in {True,False}) with provenance `explicit`, so a
    stored default can never silently override the flag; level 2 profile beats `defaults.validate`
    in all 4 polarity combinations; level 3 `defaults.validate` beats the shipped default in both
    polarities; level 4 the shipped default `False` applies, asserted to equal
    `SHIPPED_VALIDATE_DEFAULT` and pinned to `False` so this module cannot silently change what an
    un-configured run does today (matching `oc_runipd.py`'s `--validate`
    `BooleanOptionalAction, default=False`). `::test_absent_falls_through_and_is_never_read_as_false`
    is the load-bearing case: profile ABSENT + `defaults.validate: true` resolves TRUE (had absent
    been coerced to `False` at parse time, the user's stored `true` would be silently dead), while
    present-`false` does NOT fall through because it is a decision. `::test_the_default_profile_also_supplies_validate`
    proves the per-runner default profile also feeds the chain.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Paste the complete focused-suite command, exit code, and summary, naming the invalid-schema, atomic-fault, precedence, command-like-name, and arbitrary-argv negative tests. Also paste the source search proving no shell=True/eval/exec or arbitrary command-string execution exists.
  - Observed evidence: THE FOCUSED SUITE, complete command, output and exit code:

    ```
    $ python3 -m pytest tests/test_runner_profiles.py -o addopts="" -q
    ........................................................................ [ 96%]
    ...                                                                      [100%]
    75 passed in 0.31s
    FOCUSED_EXIT=0
    ```

    `-o addopts=""` is used DELIBERATELY and only here, to clear the configured `-q -n auto
    --dist=worksteal -m 'not slow'` so this narrowed run reports its own per-test counts. The plan
    text's `-p no:randomly` was NOT used: the repo suite contract says a bare run keeps the
    order randomization that surfaces order-dependence bugs, and the plan's own note (added at
    review) says to prefer a bare run. The full suite below IS bare.

    THE NAMED NEGATIVE TESTS THIS SUITE FAILS ON:
    * invalid-schema: `DocumentValidationTests::test_schema_version_is_required_and_typed`,
      `::test_unsupported_version_fails_closed_and_says_why`, `::test_non_object_document_and_sections_fail`,
      `StoreReadWriteTests::test_malformed_shapes_all_raise_rather_than_degrade` (5 named cases),
      `ModelAndFieldValidationTests::test_exact_provider_model_is_required` (15 named cases),
      `ProfileNameGrammarTests::test_invalid_names_are_rejected` (11 named cases),
      `TriStateValidateFieldTests::test_non_boolean_validate_is_refused`.
    * atomic-fault: `AtomicFaultInjectionTests::test_fault_during_replace_preserves_prior_bytes_and_cleans_up`,
      `::test_fault_during_write_preserves_prior_bytes`,
      `::test_a_keyboardinterrupt_mid_write_is_not_swallowed`.
    * precedence: `ValidatePrecedenceMatrixTests` (7 tests, one per level plus fall-through plus the
      Opus-off / Gemini-on end-to-end shape) and `ResolutionPrecedenceTests` (10 tests, one per
      launch tier plus the failure paths).
    * command-like-name (namespace OVER-reservation): `ProfileNameGrammarTests::test_command_like_names_are_legal`
      and `ResolutionPrecedenceTests::test_a_command_like_profile_name_resolves_normally`.
    * arbitrary-argv / credential: `ForbiddenAndUnknownFieldTests::test_every_forbidden_capability_field_is_refused_by_name`
      (24 keys), `::test_unknown_field_is_refused`, `::test_a_credential_can_never_be_persisted`,
      `SourceAuditTests::test_no_arbitrary_argv_or_credential_field_is_persistable`,
      `::test_the_module_does_not_read_credentials_from_the_environment`.
    * silent fallback: `NoSilentFallbackTests` (2 tests),
      `StoreReadWriteTests::test_absent_is_distinct_from_malformed`.

    FALSIFIABILITY, measured rather than asserted. Three mutants were injected into the
    implementation and the suite re-run; each was CAUGHT, so the load-bearing tests are not
    vacuous. The implementation was restored from a byte copy after each and the suite re-verified
    green.
    * Mutant 1, absent `validate` coerced to `False` at parse time (the exact defect the plan warns
      about): `12 failed, 63 passed`, including
      `ValidatePrecedenceMatrixTests::test_absent_falls_through_and_is_never_read_as_false`,
      `::test_level_2_profile_beats_defaults`, `::test_level_3_defaults_beats_the_shipped_default`,
      `::test_level_4_shipped_default_applies_when_no_level_specified` and
      `::test_two_profiles_differing_only_in_validate_resolve_differently`.
    * Mutant 2, precedence INVERTED so a stored profile value beats the explicit flag:
      `1 failed, 74 passed` -> `ValidatePrecedenceMatrixTests::test_level_1_explicit_flag_wins_over_everything`.
    * Mutant 3, malformed JSON silently degraded to an empty config: `1 failed, 74 passed` ->
      `StoreReadWriteTests::test_absent_is_distinct_from_malformed`.
    * Restored: `75 passed in 0.27s`.

    THE SOURCE SEARCH (executable lines; the one hit is the docstring saying it uses no subprocess):

    ```
    $ grep -nE "shell=True|\beval\(|\bexec\(|subprocess|os\.system|os\.popen|os\.environ|getenv" agent_workflows/runner_profiles.py
    79:Pure stdlib, no third-party imports, no network, no subprocess (D138/D139).
    ```

    ```
    $ python3 -m pytest tests/test_runner_profiles.py -o addopts="" -q -s -k "SourceAudit"
    .storable surface is exactly: ['agent', 'model', 'runner', 'validate', 'variant'] within ['default_runner', 'defaults', 'profiles', 'schema_version']
    ...source audit: no shell=True, eval(, exec(, subprocess, os.system/popen/exec*
    .
    5 passed, 70 deselected in 0.17s
    ```

    `SourceAuditTests::test_module_imports_only_the_stdlib_and_one_first_party_helper` pins the
    import set by AST to `{__future__, hashlib, json, os, re, tempfile, dataclasses, pathlib,
    types, typing, agent_workflows}`, so a future subprocess/network import cannot enter unnoticed.

    THE FULL SUITE, BARE, WITH A NO-WORSENING COMPARISON AGAINST MY OWN BASELINE at the same
    HEAD `f59cda91294073ad72cc1db0e1d48e4a853b53cb`. Baseline was measured by moving my two new
    files ASIDE and re-running, so the comparison is against this tree without my change rather
    than against a remembered number:

    ```
    $ python3 -m pytest                       # BASELINE, my two files absent
    31 failed, 4344 passed, 3 skipped, 4 xfailed in 30.88s

    $ python3 -m pytest                       # AFTER, my two files present
    31 failed, 4419 passed, 3 skipped, 4 xfailed in 36.75s

    $ diff baseline_failures.txt after_failures.txt && echo "IDENTICAL"
    IDENTICAL
    ```

    So the FAILURE SET is byte-identical (same 31 node ids before and after) and passes rose by
    exactly the 75 tests this plan adds. HONEST STATEMENT OF WHAT THOSE 31 ARE, not a claim that
    the suite is green: they are pre-existing and environmental, caused by running inside an
    ISOLATED LANE WORKTREE where `.aw/records/runs/` does not exist (it lives in the primary
    checkout). Representative:

    ```
    $ python3 -m pytest tests/test_run_viewer.py::RunViewerTests::test_discover_run_dirs -o addopts=""
        def test_discover_run_dirs(self):
            runs = run_viewer.discover_run_dirs(Path("."))
    >       self.assertTrue(len(runs) > 0)
    E       AssertionError: False is not true
    1 failed in 0.18s
    ```

    They are in `tests/test_run_viewer.py`, `tests/test_oc_runipd.py` and
    `tests/test_novalnomerge_integration.py`, none of which this plan touches; its Scope-Paths are
    two NEW files that nothing else imports yet.

    REPO GATES: the pinned pre-commit hooks pass on both new files (`pre-commit run ruff
    --files ...` -> `Passed`; `pre-commit run ruff-format --files ...` -> `Passed`). Note the
    locally installed ruff is 0.16.3 while the repo pins 0.4.4 in `.pre-commit-config.yaml`; the
    PINNED version is the authority and is what was run. `aw sanitize --agent` ->
    `{"outcome":"clean","exit":0,"findings":0}`. `aw check all` reports no finding naming
    `runner_profiles` or `runner-profiles` (its other findings are pre-existing artifact-naming
    items across the records tree, untouched here); the bar claimed is NO-WORSENING, not that
    `aw check all` passes.
  - Result: pass


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
