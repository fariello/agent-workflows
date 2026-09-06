# IPD: setup wizard integration documentation and full regression proof

- Date: 2026-08-29
- Kind: child
- Concern: A standalone profile wizard is insufficient if normal setup never offers it, but automatically configuring or defaulting a model would be a surprising behavioral and cost change. The completed feature also spans configuration, model discovery, two CLI grammars, durable state, resume, execution/verifier argv, and existing run-ledger commands; focused child tests alone can miss cross-layer drift.
- Scope: Add an optional, default-No runner-profile step to interactive aw setup; reuse the Order-02 wizard; document all canonical configuration and run forms, precedence, storage/privacy, failure behavior, and exact examples; add end-to-end tests across setup through durable launch; run generation, complete regression, packaging, and sanitizer gates; and record coordination with pending rununify.
- Scope-Paths: agent_workflows/cli.py, tests/test_cli.py, tests/test_runner_profiles_e2e.py, docs/runner-profiles.md, docs/cli-human-guide.md, README.md
- Item-Dependencies: executed:ygzq71
- Status: approved
- Readiness: go-pending-approval
- Set: runprofile
- Order: 5
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: p7xhhm
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-05 approved (aw set): status set to approved
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

- [x] E-01 Call the reusable profile wizard once from the host-level interactive aw setup flow.
  - Depends on: none
  - Expected outcome: setup offers the requested alias/model/default workflow without silently creating profiles, selecting models, changing defaults, blocking repository installation, or reimplementing the interview.
  - Execution state: performed

- [x] E-02 Add setup interaction tests for Yes with discovered model, Yes with manual model after discovery failure, multiple profiles, profile save followed by each independent default answer, No, empty, EOF, interrupt, --yes, non-TTY, existing profiles/defaults, duplicate replacement refusal, and wizard failure after repositories were installed. Assert exact prompt order, no repeated per-repository profile prompt, and byte-identical configuration for every opt-out/failure.
  - Depends on: E-01
  - Expected outcome: tests fail if setup treats --yes as consent, asks once per repository, changes defaults implicitly, loses an existing profile, or conflates optional profile failure with install failure.
  - Execution state: performed

### Task group 2: user contract and whole-feature proof

- [x] E-03 Publish docs/runner-profiles.md as the canonical user contract and link it from the CLI guide and README.
  - Depends on: E-01
  - Expected outcome: one concise durable reference lets a user configure the three requested examples and understand every default, override, privacy, collision, and resume rule without reading implementation code.
  - Execution state: performed

- [x] E-04 Add an end-to-end mocked test that starts from an empty XDG directory, runs the setup/profile interview to create gem as OpenCode/global default, invokes aw run ipd SELECTOR and aw run as sol SELECTOR, inspects created state.json and exact execution/verifier argv, edits aliases, resumes, and proves the frozen prior resolution remains. Add negative end-to-end cases for malformed config, unavailable default runner, unknown profile, command-like profile, no accidental durable state, and non-collision with the existing run-ledger family.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the full feature cannot pass through disconnected unit mocks that never prove wizard data reaches real runner state and both turn types.
  - Execution state: performed

- [x] E-05 Run focused Set tests, every existing OpenCode/CLI/config/run-viewer regression affected by the change, the full suite exactly as repository instructions require, packaging/build checks, generated/no-drift checks, git diff --check, and aw sanitize --agent. Record OpenCode live smoke as optional: if a configured zero-risk test selector and credentials exist, capture version/model/variant and actual argv/output; otherwise state not run, never pass.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: actual pasted outputs prove deterministic acceptance, unrelated command/config/install behavior remains green, distributable packaging includes new modules/docs, and no local identifiers or credentials enter tracked artifacts.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: Paste setup tests/transcripts for Yes/manual/discovered/multiple/default choices and No/empty/EOF/interrupt/--yes/non-TTY/existing/duplicate/error cases. Show the prompt occurs exactly once after repo installation, default answers are No, every opt-out/failure preserves profile bytes, and setup still reaches orientation after clean cancellation.
  - Observed evidence: Implementation is `agent_workflows/cli.py:5485` (`_configure_runner_profiles`), called from `_run_setup` (`agent_workflows/cli.py:6521`) at `agent_workflows/cli.py:6640` AFTER the per-repo install loop and `_configure_completion`, BEFORE `_orient`. It is NOT called from `_install_one`/`_install_all` (integration test `test_install_verb_does_not_offer_the_profile_step` asserts this).
    ALL 20 NAMED CASES PASS (`python3 -m pytest -o addopts="" -p no:randomly tests/test_cli.py -k "SetupRunnerProfile" -v`, exit 0, `20 passed, 57 deselected in 11.67s`):
    ```text
    SetupRunnerProfileStepTests::test_yes_with_discovered_model_writes_the_profile_and_both_defaults PASSED
    SetupRunnerProfileStepTests::test_yes_with_manual_model_after_discovery_failure PASSED
    SetupRunnerProfileStepTests::test_multiple_profiles_in_one_session PASSED
    SetupRunnerProfileStepTests::test_each_default_answer_is_independent_of_the_save PASSED
    SetupRunnerProfileStepTests::test_declined_gate_writes_nothing PASSED
    SetupRunnerProfileStepTests::test_empty_answer_is_a_no PASSED
    SetupRunnerProfileStepTests::test_eof_at_the_gate_writes_nothing PASSED
    SetupRunnerProfileStepTests::test_eof_inside_the_interview_writes_nothing PASSED
    SetupRunnerProfileStepTests::test_interrupt_inside_the_interview_writes_nothing PASSED
    SetupRunnerProfileStepTests::test_declined_save_writes_nothing PASSED
    SetupRunnerProfileStepTests::test_yes_flag_never_prompts_and_never_writes PASSED
    SetupRunnerProfileStepTests::test_non_tty_never_prompts_and_never_writes PASSED
    SetupRunnerProfileStepTests::test_existing_profiles_and_defaults_survive_an_opt_out PASSED
    SetupRunnerProfileStepTests::test_duplicate_name_is_refused_and_the_existing_profile_survives PASSED
    SetupRunnerProfileStepTests::test_malformed_store_is_reported_and_never_overwritten PASSED
    SetupRunnerProfileStepTests::test_wizard_failure_is_reported_not_raised PASSED
    SetupRunnerProfileIntegrationTests::test_step_runs_once_after_installs_and_before_orientation PASSED
    SetupRunnerProfileIntegrationTests::test_install_verb_does_not_offer_the_profile_step PASSED
    SetupRunnerProfileIntegrationTests::test_setup_yes_writes_no_profile_store PASSED
    SetupRunnerProfileIntegrationTests::test_wizard_failure_after_installs_does_not_fail_setup PASSED
    ```
    PROMPT OCCURS EXACTLY ONCE, measured not asserted narratively: `test_step_runs_once_after_installs_and_before_orientation` spies `_install_one`/`_configure_completion`/`_configure_runner_profiles`/`_orient` on a real TWO-repo `aw setup`, then asserts `seen.count("profiles") == 1`, `index("profiles") > max(install indices)`, and `index("profiles") < index("orient")`; both repos really carry `.aw/system/VERSION`, so the ordering claim is not vacuous.
    DEFAULT IS NO: the rendered gate is `  Set up a runner profile now? [y/N] ` and only `y`/`yes` proceeds (`cli.py:5546-5553`); both wizard default questions pass `default=False` (`runner_profile_wizard.run_wizard`, `ask_yes_no(..., default=False)`).
    OPT-OUT PRESERVES BYTES, asserted by BYTE COMPARISON (`store_bytes()` = `read_bytes()` or None) rather than by inspection, so a write-then-restore implementation still fails: declined gate, empty, EOF at gate, EOF mid-interview, KeyboardInterrupt, declined save, `--yes`, non-TTY, pre-existing store + opt-out, duplicate refusal, and malformed store all compare equal to the pre-state.
    TRANSCRIPT, real code, declined path (captured live during execution):
    ```text
    Runner profiles (optional)
    A profile turns a model choice into a short alias, so you can run 'aw run as gem <selector>' instead of repeating '--model <provider/model> --variant high'. Profiles are stored only on this machine, under <config-dir>/runner-profiles.json, and nothing is written unless you confirm each step.
    SKIP           Skipped; set one up later with 'aw oc profile add'.
    declined, store exists: False
    ```
    SETUP STILL REACHES ORIENTATION AFTER CLEAN CANCELLATION: `test_wizard_failure_after_installs_does_not_fail_setup` runs the REAL step with a TTY answering `n` and asserts `aw setup` exits 0 with `You are set up` in stdout.
    NOT REIMPLEMENTED: the step calls `runner_profile_wizard.run_session` (`cli.py:5564`); it contains no question text for name/model/variant/agent, no catalog paging, no preview, and no save/default logic of its own.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Paste the focused setup-suite command, exit code, and named-case summary. Include input/output snapshots and byte comparisons for all consent polarities, multiple repositories/profiles, duplicate refusal, existing defaults, and post-install wizard failure.
  - Observed evidence: COMMAND AND EXIT CODE:
    ```text
    $ python3 -m pytest -o addopts="" -p no:randomly tests/test_cli.py -k "SetupRunnerProfile" -q
    ....................                                                     [100%]
    20 passed, 57 deselected in 11.67s
    ```
    The 20 named cases are enumerated verbatim under V-01 (16 in `SetupRunnerProfileStepTests`, 4 in `SetupRunnerProfileIntegrationTests`; `tests/test_cli.py`).
    BYTE COMPARISONS: the fixture exposes `store_bytes()` (`read_bytes()` or `None`) and every consent-polarity test asserts `assertEqual(self.store_bytes(), before)`. Covered polarities: declined gate, empty answer, EOF at gate, EOF mid-interview, KeyboardInterrupt mid-interview, declined save, `--yes`, non-TTY, and malformed store. `test_existing_profiles_and_defaults_survive_an_opt_out` seeds a store carrying `default_runner`, `defaults.profiles.oc` and a profile, then asserts the bytes are unchanged with the message `an opt-out rewrote the store`.
    INPUT/OUTPUT SNAPSHOT (declined path, real code, captured during execution):
    ```text
    Runner profiles (optional)
    A profile turns a model choice into a short alias, so you can run 'aw run as gem <selector>' ...
    SKIP           Skipped; set one up later with 'aw oc profile add'.
    ```
    `test_declined_gate_writes_nothing` additionally asserts `len(prompts) == 1`, proving the interview was never entered rather than entered and abandoned.
    MULTIPLE REPOSITORIES: `test_step_runs_once_after_installs_and_before_orientation` uses a real two-repo `aw setup` and asserts the profile step ran exactly once. MULTIPLE PROFILES: `test_multiple_profiles_in_one_session` drives two rounds through the real `run_session` and asserts `sorted(cfg.profiles) == ["gem", "sol"]` with `sol`'s model and variant correct.
    DUPLICATE REFUSAL: `test_duplicate_name_is_refused_and_the_existing_profile_survives` seeds `gem -> synthetic/original`, answers `gem` again, and asserts the bytes are unchanged, `already exists` is emitted, and the surviving model is still `synthetic/original`.
    EXISTING DEFAULTS / IMPLICIT-CHANGE GUARD: `test_each_default_answer_is_independent_of_the_save` saves a profile while DECLINING both defaults (asserting `default_profile_for("oc") is None` and `default_runner is None`), then in a second run accepts only the default profile and asserts `default_runner` is STILL None with the message `default_runner changed without consent`.
    POST-INSTALL WIZARD FAILURE: `test_wizard_failure_is_reported_not_raised` patches `run_session` to raise `RuntimeError("catalog exploded")` and asserts no exception escapes, `did not complete` plus the reason are reported, and the store bytes are unchanged; `test_wizard_failure_after_installs_does_not_fail_setup` proves the repo is still installed and the real step lets `aw setup` exit 0 reaching `You are set up`.
    NON-VACUITY (mutation check, run during execution and then REVERTED): replacing the `--yes` guard in `_configure_runner_profiles` with a dead branch makes the consent test FAIL as required:
    ```text
    E       AssertionError: Lists differ: ['  Set up a runner profile now? [y/N] ', ... 9 prompts ...] != []
    E        : --yes consented to a model choice
    FAILED tests/test_cli.py::SetupRunnerProfileStepTests::test_yes_flag_never_prompts_and_never_writes
    1 failed, 1 passed, 75 deselected in 0.25s
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Paste documentation/help searches showing every canonical command, exact precedence, local storage/privacy, provider-default variant, default-No setup, resume snapshot, recovery, and rejected spelling is documented once. Paste link/parity tests proving README/guide point to the authority and CLI help examples parse.
  - Observed evidence: AUTHORITY: `docs/runner-profiles.md` (255 lines), linked from `README.md` (new "Runner profiles" subsection) and `docs/cli-human-guide.md` (new "Naming a model once instead of on every run" subsection plus a quick-reference row). Neither linking doc forks the contract; both point at the authority.
    OQ-01 / PR-003 DISCHARGED BEFORE WRITING, verified rather than assumed: `0soncw` is in `.aw/records/plans/executed/` (`20260829-runnamecollapse-01-0soncw-...ipd.md`), and the `aw run` noun was NOT retired but SPLIT (`aw run` writes/dispatches, `aw runs` reads). The shipped parser answers directly:
    ```text
    $ python3 -m agent_workflows.cli run as --help
    Run an IPD through a host runner, choosing the host WITHOUT naming it.

    usage: aw run as <profile> [SELECTOR ...]     # named profile; the profile picks the host
           aw run ipd [SELECTOR ...]              # the configured default_runner picks the host
    ```
    So the documented grammar is the live grammar, not a retired one.
    EVERY PUBLISHED COMMAND PARSES, asserted against `cli._build_parser()` rather than eyeballed (`PublishedContractParityTests::test_every_canonical_run_form_the_doc_publishes_actually_parses`): `run as gem X`, `run ipd X`, `oc run as gem X`, `oc profile add|list|show|remove|default`, `oc profile default --clear`, plus `run_dispatch.ROUTES == ["as", "ipd"]`.
    EXACT PRECEDENCE IS ASSERTED AGAINST THE RESOLVER, not restated (`test_the_doc_states_the_precedence_the_resolver_implements`): explicit beats profile PER FIELD (`--variant max` keeps the profile's model and agent; provenance `variant=explicit`, `model=profile`), per-runner default applies unnamed (`model=default-profile`), host default when no level supplies a value (`model=host-default`), and `SHIPPED_VALIDATE_DEFAULT is False` with provenance `shipped-default` for the tri-state chain.
    STORAGE/PRIVACY: `test_the_doc_names_the_real_store_location_and_reserved_names` checks the doc names `runner-profiles.json` (equal to `rp.STORE_NAME`) and `XDG_CONFIG_HOME`. `test_every_field_the_doc_says_is_refused_really_is` proves each documented refusal (`api_key`, `token`, `args`, `env`, `command`, `prompt`) is in `rp.FORBIDDEN_PROFILE_KEYS` AND raises `ProfileSchemaError` through `parse_profile`, and that `ALLOWED_PROFILE_KEYS == [agent, model, runner, validate, variant]`, so the "no field through which a secret could be stored" claim is checked, not asserted.
    PROVIDER-DEFAULT VARIANT: documented as "provider default (store no variant)" and proven by `WizardToArgvE2E::test_yes_with_manual_model_after_discovery_failure` (`assertIsNone(cfg.profiles["gem"].variant)`).
    DEFAULT-NO SETUP: documented under "During `aw setup`" including the explicit `--yes` non-consent rule; enforced by the V-01/V-02 evidence.
    RESUME SNAPSHOT AND RECOVERY: documented under "Durability" (frozen identity, per-field provenance, `--prepare-only` inspection) and "When something is wrong" (a seven-row refusal table); both are proven by the V-04 evidence.
    REJECTED SPELLINGS DOCUMENTED ONCE: the doc states the rule ("no profile ever becomes a command") and names the rejected spellings once, phrased so no fake `aw <sub>` token is emitted; `RESERVED_PROFILE_NAMES == ["as", "default"]` is asserted equal to the schema's own set.
    DOC GATES:
    ```text
    $ python3 -c "docs_check.check_docs_dir(Path('docs'))"
    findings: 0
    $ per-file: README.md findings: 0 | docs/runner-profiles.md findings: 0 | docs/cli-human-guide.md findings: 0
    $ em/en dash scan: README.md em: 0 en: 0 | docs/runner-profiles.md em: 0 en: 0 | docs/cli-human-guide.md em: 0 en: 0
    ```
    NOTE, recorded honestly: `docs_check.check_aw_commands` initially flagged three counterexample spellings I had written as literal `aw gem` / `aw gemrun` / `aw run-gem`; the checker was RIGHT (a doc must not print a nonexistent `aw <sub>`), so the sentence was rephrased to state the rule without emitting the tokens. The three findings are now zero.
    The 7 parity tests pass (`PublishedContractParityTests`, enumerated in V-04's transcript).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Paste the end-to-end test transcript from empty synthetic XDG through setup-created defaults, generic/named launch, state.json, exact execution/verifier argv, alias mutation/deletion, and stable resume. Include negative results for malformed/unknown/missing defaults, command-like names, no partial state, and ledger-command non-collision.
  - Observed evidence: FULL TRANSCRIPT (`python3 -m pytest -o addopts="" -p no:randomly tests/test_runner_profiles_e2e.py -v`, exit 0, `30 passed in 3.06s`):
    ```text
    WizardToArgvE2E::test_setup_interview_creates_the_store_from_an_empty_xdg_directory PASSED
    WizardToArgvE2E::test_named_form_forwards_the_wizard_authored_clause PASSED
    WizardToArgvE2E::test_unqualified_form_routes_through_the_wizard_authored_default_runner PASSED
    WizardToArgvE2E::test_unqualified_form_refuses_when_the_default_runner_was_declined PASSED
    WizardToArgvE2E::test_per_field_override_keeps_the_rest_of_the_profile PASSED
    WizardToArgvE2E::test_named_and_host_explicit_forms_forward_equivalent_arguments PASSED
    WizardToArgvE2E::test_two_profiles_created_in_one_session_are_both_dispatchable PASSED
    WizardToArgvE2E::test_edited_alias_changes_later_launches PASSED
    DurableIdentityE2E::test_wizard_created_profile_lands_in_state_json_with_provenance PASSED
    DurableIdentityE2E::test_default_profile_reaches_state_without_a_named_clause PASSED
    DurableIdentityE2E::test_repointing_then_deleting_the_alias_does_not_move_a_started_run PASSED
    DurableIdentityE2E::test_controlled_negative_a_moved_store_is_observable_when_re_resolved PASSED
    NegativeE2E::test_unknown_profile_refuses_before_any_durable_state PASSED
    NegativeE2E::test_malformed_store_refuses_and_is_never_read_as_empty PASSED
    NegativeE2E::test_unqualified_dispatch_with_no_configuration_refuses_with_the_fix PASSED
    NegativeE2E::test_unknown_profile_in_the_router_refuses_without_launching PASSED
    NegativeE2E::test_wrong_runner_profile_is_not_launched_by_opencode PASSED
    NegativeE2E::test_a_declined_interview_leaves_no_store_to_dispatch_from PASSED
    NamespaceE2E::test_command_like_profile_names_dispatch_after_as PASSED
    NamespaceE2E::test_the_reading_noun_still_reaches_the_viewer_not_a_launcher PASSED
    NamespaceE2E::test_no_profile_name_became_a_command PASSED
    NamespaceE2E::test_ledger_write_verbs_are_untouched_by_a_profile_store PASSED
    NamespaceE2E::test_a_selector_that_looks_like_a_profile_stays_a_selector PASSED
    PublishedContractParityTests::test_the_authority_exists_and_is_linked_from_readme_and_the_cli_guide PASSED
    PublishedContractParityTests::test_every_canonical_run_form_the_doc_publishes_actually_parses PASSED
    PublishedContractParityTests::test_the_doc_states_the_precedence_the_resolver_implements PASSED
    PublishedContractParityTests::test_the_doc_names_the_real_store_location_and_reserved_names PASSED
    PublishedContractParityTests::test_every_field_the_doc_says_is_refused_really_is PASSED
    PublishedContractParityTests::test_the_doc_contains_no_em_or_en_dash PASSED
    PublishedContractParityTests::test_docs_check_passes_for_the_new_and_edited_docs PASSED
    ```
    EMPTY SYNTHETIC XDG IS THE PRECONDITION, not an assumption: `_EmptyXdgFixture.setUp` asserts `not rp.store_path().exists()` with the message `fixture did not start empty`. Only `oc_models.discover_models` (a subprocess call to the operator's own `opencode`) and `oc_runipd.main` (the process boundary) are stubbed; the schema, store, wizard, resolver, router, and CLI are all the shipped code.
    SETUP-CREATED DEFAULTS: `test_setup_interview_creates_the_store_from_an_empty_xdg_directory` drives the REAL `cli._configure_runner_profiles` and then reads the file from disk, asserting `schema_version == 1`, `profiles.gem.model/variant/runner`, `defaults.profiles.oc == "gem"`, `default_runner == "oc"`, and that no forbidden key string appears.
    NAMED AND GENERIC LAUNCH, EXACT ARGV: named forwards exactly `["as", "gem", "demo01"]`; unqualified forwards exactly `["demo01"]`; `--variant max` forwards `["as", "gem", "demo01", "--variant", "max"]` (the profile is NOT discarded); and `aw run as gem X` equals `aw oc run as gem X` argv-for-argv.
    STATE.JSON FROM A REAL DRIVER RUN (`--prepare-only`, real git repo, real store): `options.model == synthetic/gem-test`, `options.variant == high`, `launch_profile.requested == applied == "gem"`, `runner == "oc"`, `provenance.model == "profile"`, non-empty `config_digest`, `config_source` naming `runner-profiles.json`, and no credential-shaped key in the record. The unqualified case yields `requested is None`, `applied == "gem"`, `provenance.model == "default-profile"`.
    ALIAS MUTATION AND DELETION WITH STABLE RESUME (`test_repointing_then_deleting_the_alias_does_not_move_a_started_run`): after the run starts, `gem` is repointed to a different model through the REAL CLI (`aw oc profile add gem --model ... --replace --yes`) and then the store is DELETED outright; a real `oc_runipd status --json` subprocess still reports the frozen `model`, `variant`, and identical `config_digest` both times (failure messages `a repoint moved the run` / `a deletion moved the run`).
    NON-VACUITY of the freeze: `test_controlled_negative_a_moved_store_is_observable_when_re_resolved` proves re-resolution WOULD change both the model and the digest, so the freeze test is detecting something real. `test_edited_alias_changes_later_launches` is the complementary control: with no run in flight, an edit does take effect.
    EXECUTION AND VERIFIER TURN ARGV: owned by `3cm15q`'s `LaunchProfileFrozenTurnArgvTests`, which asserts `--model`/`--variant`/`--agent` on the execute, recovery, review, AND fresh-session verifier turns, with a mutation control proving a verifier missing `--variant` would be caught. This plan's E-04 does not duplicate that claim; it proves the layer above it (wizard bytes -> frozen state), and `tests/test_oc_runipd.py` was re-run green as part of V-05.
    NEGATIVES, all asserting NO DURABLE STATE: the helper snapshots `.aw/records/runs` before, requires exit 2, requires the directory listing to be unchanged (`a refused run left durable state behind`), and requires no `Run ID:` in stdout. Cases: unknown profile; malformed store (additionally asserting the message is NOT `no runner profile named`, which would mean it degraded to empty and would have silently launched the host default model); `aw run ipd` with nothing configured (exit 2, names `default_runner`, creates no store); unknown profile at the router (host driver never called); wrong-runner profile (host driver never called; MEASURED refusal is at schema load, `unknown runner 'agy'` / `registers: oc`, because version 1's registry admits `oc` only); and a declined interview leaving nothing to dispatch from.
    COMMAND-LIKE NAMES AND LEDGER NON-COLLISION: profiles named `status`, `show`, `evidence`, and `run` all dispatch correctly after `as`; `aw runs show` launches NO host (`an inspection verb launched a host`); no profile manufactured a command leaf (`gem`, `run gem`, `run-gem`, `rungem`, `gemrun`, `runs gem` are all absent while `run as`/`run ipd` are present); the four ledger write leaves `run start|record|cancel|finalize` remain registered; and a selector whose text equals a profile name stays a selector (`["gem"]` forwarded, no `as` clause synthesized).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Paste actual output and exit codes for all focused Set suites; affected existing regressions; bare full pytest; packaging/build plus installed-help smoke; generated/no-drift checks; git diff --check; and aw sanitize --agent. State live OpenCode smoke results with version/model/variant or explicitly not run.
  - Observed evidence: FOCUSED SET SUITES (the plan's named command):
    ```text
    $ python3 -m pytest -o addopts="" -p no:randomly tests/test_cli.py tests/test_runner_profiles_e2e.py -q
    FAILED tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw
    1 failed, 106 passed in 108.23s (0:01:48)
    ```
    THAT FAILURE IS PRE-EXISTING AND NOT MINE, proven by stashing all six of my files and re-running at bare HEAD:
    ```text
    HEAD-only run (no p7xhhm changes present):
    E       AssertionError: True is not false : No .aw/ directory remains after records removal
    FAILED tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw
    1 failed, 56 deselected in 4.60s
    ```
    It concerns deep-cleanup `.aw/` removal during uninstall, is outside this plan's Scope-Paths, and my subset alone is green (`20 passed` for the setup step, `30 passed` for the E2E file).
    AFFECTED EXISTING REGRESSIONS (the plan's named set):
    ```text
    $ python3 -m pytest -o addopts="" -p no:randomly tests/test_oc_runipd.py tests/test_oc_runipd_cli.py tests/test_config.py tests/test_run_viewer.py -q
    21 failed, 246 passed in 16.71s
    $ (same command with all six p7xhhm files stashed, i.e. bare HEAD)
    21 failed, 246 passed in 16.57s
    ```
    IDENTICAL counts with and without my changes, so this plan introduces ZERO regressions. The 21 are pre-existing (14 in `test_run_viewer.py`, which also fail in the default non-slow run, plus worktree-isolation/self-finalize cases).
    BARE FULL SUITE, exactly as AGENTS.md requires (no added flags):
    ```text
    $ python3 -m pytest
    35 failed, 5332 passed, 3 skipped, 2 xfailed in 114.93s (0:01:54)
    $ (same bare command with all six p7xhhm files stashed, i.e. bare HEAD)
    35 failed, 5332 passed, 3 skipped, 2 xfailed in 114.50s (0:01:54)
    ```
    IDENTICAL baseline. My new suites are `slow`-marked, so they are excluded from the bare run by the configured `-m 'not slow'`; run through the slow path they are green apart from the same pre-existing failure:
    ```text
    $ python3 -m pytest tests/test_runner_profiles_e2e.py tests/test_cli.py -m ''
    FAILED tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw
    1 failed, 106 passed in 13.58s
    ```
    PACKAGING/BUILD:
    ```text
    $ python3 -m build --outdir <tmp>
    Successfully built agent_workflows-1.3.0rc2.dev2064+gcf9e853c.d20260906.tar.gz and
      agent_workflows-1.3.0rc2.dev2064+gcf9e853c.d20260906-py3-none-any.whl
    ```
    Wheel contains the feature modules: `agent_workflows/runner_profiles.py` OK, `agent_workflows/runner_profile_wizard.py` OK, `agent_workflows/run_dispatch.py` OK, `agent_workflows/oc_models.py` OK.
    HONEST SCOPE NOTE on "packaging includes new docs": the distribution ships NO `docs/` and NO `tests/` AT ALL (measured: `any docs/ at all: 0`, `any tests/ at all: 0`; sdist top level is `.aw`, `.gitignore`, `LICENSE`, `NOTICE`, `PKG-INFO`, `README.md`, `agent_workflows`, `hatch_build.py`, `pyproject.toml`). So `docs/runner-profiles.md` being absent is the repository's EXISTING packaging convention, not a gap this plan introduced; `README.md` (which links to it) IS shipped. I did not widen packaging, since that is outside this plan's Scope-Paths.
    INSTALLED-HELP SMOKE from the built wheel in a clean venv:
    ```text
    $ <venv>/bin/aw run as --help
    Run an IPD through a host runner, choosing the host WITHOUT naming it.

    usage: aw run as <profile> [SELECTOR ...]     # named profile; the profile picks the host
           aw run ipd [SELECTOR ...]              # the configured default_runner picks the host
    $ <venv>/bin/aw oc profile --help
    usage: agent-workflows oc profile [-h] [--no-color] [--agent] [--json]
                                      {add,list,ls,show,remove,rm,default} ...
    ```
    GENERATED/NO-DRIFT CHECKS (the CI gates):
    ```text
    $ python3 -m pytest tests/test_cli_conformance_matrix.py tests/test_cli_quality_gates.py tests/test_cli_output_docs_rollout.py -q
    .............................                                            [100%]     (29 passed)
    $ python3 -m agent_workflows check releases --agent  -> exit 0
    $ python3 -m agent_workflows check plans --agent     -> exit 1 (PRE-EXISTING; identical exit 1 at bare HEAD with my files stashed, and NO finding names p7xhhm)
    $ aw check --agent | grep for my files -> "findings referencing my files: 0"
    ```
    GIT DIFF CHECK:
    ```text
    $ git diff --check
    git diff --check: clean (exit 0)
    ```
    SANITIZER:
    ```text
    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    sanitize exit=0
    ```
    PRE-COMMIT HOOKS on the actual commit (`eaa51f9b`): trailing whitespace Passed, end of files Passed, large files Passed, Detect hardcoded secrets Passed, ruff Passed, ruff-format Passed, no local leaks in tracked files Passed, no raw plan->executed commit Passed, no untooled plan status change Passed. (A first attempt was REJECTED by `ruff-format`; I re-verified `git diff --cached --name-only` after the failed hook per the execution contract, re-ran the focused suites on the reformatted code (`50 passed`), and only then committed.)
    LIVE OPENCODE SMOKE: NOT RUN, and explicitly not passed. `opencode` IS installed (`opencode --version` -> `1.18.27`) and a read-only catalog probe succeeds (`source: opencode-cli | available: True | count: 140`), but NO zero-risk test selector or budgeted credential is configured for this run (`AW_OC_SMOKE_SELECTOR` unset), so no paid model was launched. Substituted a ZERO-COST real-driver check instead (`--prepare-only`, synthetic model, launches no model):
    ```text
    exit: 0
      Run ID: run-20260906T104018Z-988885
      Launch: model=synthetic/smoke-model (profile); variant=high (profile); profile=gem (requested)
    frozen model/variant: synthetic/smoke-model / high
    provenance: {'agent': 'host-default', 'model': 'profile', 'runner': 'explicit', 'validate': 'shipped-default', 'variant': 'profile'}
    ```
    No local identifier, home path, hostname, or credential entered any tracked artifact (sanitizer clean above; tests use synthetic `synthetic/...` model ids and temporary XDG dirs only).
  - Result: pass


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
