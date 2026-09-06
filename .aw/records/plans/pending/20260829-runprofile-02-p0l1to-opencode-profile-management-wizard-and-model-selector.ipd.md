# IPD: OpenCode profile management wizard and model selector

- Date: 2026-08-29
- Kind: child
- Concern: A storage API alone does not provide a usable or safe way to create aliases. Users need a reusable word-oriented profile command, an interactive model/variant selector, exact previews, explicit default questions, and deterministic noninteractive controls. Model discovery can fail, return a very large list, include ANSI/noise, or omit private models, so the wizard must degrade to manual entry without fabricating support.
- Scope: Add OpenCode profile-management commands and a reusable wizard. Discover models from the user's actual OpenCode installation/configuration without refreshing or mutating it, offer filtering and exact manual entry, collect a provider-specific variant without overclaiming validation, preview the resolved launch, persist atomically through the Order-01 API, and manage per-OpenCode/global defaults explicitly.
- Scope-Paths: agent_workflows/runner_profile_wizard.py, agent_workflows/oc_models.py, agent_workflows/cli.py, tests/test_runner_profile_wizard.py, tests/test_oc_profile_cli.py
- Item-Dependencies: executed:f2mrsw
- Status: approved
- Readiness: go-pending-approval
- Set: runprofile
- Order: 2
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: p0l1to
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-04 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): READINESS BOOKKEEPING, no scope or content change. Added the `- Readiness:` front-matter field, which postdates this plan (the field is a later addition to the review contract, `plan-review.md:377-398`, and automation FAILS CLOSED when it is absent, so a clean plan without it is simply never picked up). Value `go-pending-approval`.
  AND SUPERSEDED THE STALE `REVIEWED - OPEN QUESTIONS` VERDICT, which is the substantive half. That verdict was correct when written on 2026-09-01: the Set carried ONE blocking question, OQ-01, asking whether approved `runnamecollapse-01` (`0soncw`) had to land first, and the maintainer answered ORDER: `0soncw` FIRST, which made the Set depend on `0soncw` reaching `executed` AND inherited `0soncw`'s own unresolved blocking question. BOTH CONDITIONS ARE NOW DISCHARGED, verified rather than assumed: `0soncw` is in `.aw/records/plans/executed/` with `Status: executed`, and its three open questions (OQ-01 permanence, OQ-02 noun placement, OQ-03 subcommand-versus-viewer disambiguation, the one that gated this Set) are all `Status: resolved`. This plan's own OQ-01 is `Status: resolved`, and `aw ipd lint` reports no unresolved blocking question. So the verdict is stated here as APPROVE WITH REVISIONS APPLIED, superseding the neutral one, on the maintainer's 2026-09-04 reading that the outstanding record was bookkeeping rather than an unanswered question. NO re-review of the plan's technical content was performed in this pass and none is claimed: round 1's findings and their fixes stand as recorded.

- 2026-09-01 reviewed (aw set): plan-review round 1 (whole Set): REVIEWED - OPEN QUESTIONS. Blocking OQ on the aw run noun retirement by approved 0soncw; f2mrsw additionally APPROVE WITH REVISIONS APPLIED for the two maintainer-directed validate findings. See .aw/records/reviews/.
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1 (whole `runprofile` Set, 6 plans, reviewed together at HEAD 6a29f9c0): REVIEWED - OPEN QUESTIONS. BLOCKER PR-001, escalated ONCE as blocking OQ-01 on the orchestrator 3m0urk: this Set builds its entire grammar on the `aw run` noun (measured: `aw run as` x16, `aw run ipd` x12) that APPROVED 0soncw is RETIRING behind a nonzero-exit deprecation stub, and NO plan in the Set mentions 0soncw even once. They are COMPLEMENTARY not contradictory (0soncw frees the name "for a future driver verb", which is this Set), so the fix is ORDER: 0soncw first, then this Set. Reversed, `aw run as gem` would start exiting nonzero. Not agent-resolvable: a cross-Set order decision, and 0soncw itself still carries an unresolved blocking OQ-03. PR-002 MEDIUM, fixed: the Set carries ZERO file:line citations across all six plans (versus 9/4/5 in the comparable 6lu3rq/m73aet/wlxkoz); spot-checked claims were TRUE so this is evidence discipline, and each plan now requires measuring and citing every "already" claim. Verified TRUE that oc_models.py already ships (591 lines, exposes resolve_config_path) and that the plan correctly says to reuse it rather than fork path rules. Contended path: cli.py, shared with six approved plans. Review artifact: .aw/records/reviews/20260831-runprofile-*-p0l1to-*.review.md

- 2026-08-30 to-review (codex gpt-5.6): authored as the reusable OpenCode profile wizard and management surface.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Let a user create gem, sonnet, or sol without editing JSON or remembering flags. The wizard must select from the models OpenCode can actually see when possible, always allow an exact manual model, show the exact structured expansion, and ask separately before changing defaults.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: model discovery and reusable interview

- [x] E-01 Add a read-only model-catalog function at the existing OpenCode boundary. Invoke the configured OpenCode executable as an argv list with shell=False, a bounded timeout, captured output, and no refresh/write flags; normalize ANSI and whitespace; accept only exact nonempty provider/model records; deduplicate deterministically. Treat missing binary, timeout, nonzero exit, malformed output, and empty results as explicit unavailable diagnostics, never an empty successful catalog. Reuse existing OpenCode config-path helpers only as a no-secret fallback for statically declared model IDs.
  - Depends on: none
  - Expected outcome: the wizard can list the user's public and private configured models without network refresh, configuration mutation, credential output, shell evaluation, or false success.
  - Execution state: performed

- [x] E-02 Create runner_profile_wizard.py as a dependency-injected TTY interview that can be unit-tested with scripted input/output. It asks for/validates a profile name; supports case-insensitive substring filtering and bounded/paged numeric selection for large model catalogs; always offers exact manual provider/model entry; offers Provider default (stored as no variant), common low|medium|high|max choices labeled provider/model-specific, and exact custom variant entry; then prints the exact profile and equivalent OpenCode argv fields before a default-No save confirmation.
  - Depends on: E-01
  - Expected outcome: a user can select the requested three models and variants even when discovery is unavailable or incomplete, while cancellation/EOF/invalid input writes nothing.
  - Execution state: performed

### Task group 2: profile verbs and default questions

- [x] E-03 Add aw oc profile add|list|show|remove|default as a fixed CLI namespace. add [NAME] starts the wizard on a TTY, prompting for NAME when omitted; a complete noninteractive form accepts structured --model, optional --variant, optional --agent, and explicit --yes, with --replace required to overwrite. default NAME sets the OpenCode default; default --clear clears it. All commands use Order-01 storage/mutation functions, return actionable nonzero errors, and never alter OpenCode configuration.
  - Depends on: E-01, E-02
  - Expected outcome: profile lifecycle is discoverable and scriptable without dynamic commands, hand-edited JSON, ambiguous overwrites, or shell aliases.
  - Execution state: performed

- [x] E-04 After a profile is saved, ask two separate default-No questions: Make NAME the default OpenCode profile? and, only when appropriate, Make OpenCode the default IPD runner? Apply the accepted profile plus accepted defaults in one validated atomic write; declining either question must preserve its prior value. Permit repeated Configure another profile? only in the explicit wizard/session caller, not as an automatic loop inside noninteractive commands.
  - Depends on: E-02, E-03
  - Expected outcome: setting an alias never silently changes unqualified runs, while users can intentionally establish both requested defaults during the same interview.
  - Execution state: performed

- [x] E-05 Add interaction and CLI tests for successful discovered/manual flows, filtering/paging, common/custom/provider-default variants, first-profile and existing-default cases, exact preview, invalid inputs/retry limits, cancel/empty/EOF/interrupt, discovery failures, no-TTY incomplete invocation, duplicate/replace/remove/default integrity, JSON/agent-safe listing, and assertions that default-No or failed flows leave the config bytes unchanged.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: tests fail if the wizard green-washes discovery failure, hides the exact expansion, writes after cancellation, assumes a default, leaks credentials, overwrites an alias, or cannot select a private/manual model.
  - Execution state: performed

## Project conventions discovered (Step 0)

RE-MEASURED AT EXECUTION (PR-002's falsifier: "cite `file:line` for each, measured at the current
HEAD"). All five premises below were verified at HEAD `f0c7f023`; every one HELD and none had drifted.

- aw oc is a fixed host command group in agent_workflows/cli.py; unlike aw oc run, structured profile-management verbs belong in that parser and dispatcher rather than the runner's REMAINDER parser. VERIFIED: the group is declared at `agent_workflows/cli.py:3305` with its subparsers at `:3318`; `runipd` uses `argparse.REMAINDER` while `update-models` declares structured flags and dispatches from the parsed namespace, so `profile` follows `update-models`. The REMAINDER choice is deliberate and documented in place: the runner's own parser must own its flag set or the two drift. A profile verb has no second parser to stay in step with, so REMAINDER would only cost `--help`, completion, and argparse's error messages.
- oc_models.resolve_config_path() already mirrors OpenCode configuration discovery and deliberately avoids exposing resolved credentials. Extend/reuse read-only discovery rather than forking path rules. VERIFIED: `agent_workflows/oc_models.py:96` (the file was 591 lines before this plan, 867 after). Its precedence is `$OPENCODE_CONFIG` -> a project `opencode.json`/`.jsonc` walking up from cwd -> `$XDG_CONFIG_HOME/opencode/` -> `~/.config/opencode/`. E-01 REUSES it for the fallback rather than re-deriving those rules.
- The current aw setup completion prompt is host-level and TTY-aware. This child creates a reusable wizard; Order 05 decides where setup calls it. VERIFIED: the shell-completion offer at `agent_workflows/cli.py:5149-5170` is gated on `args.yes or not sys.stdin.isatty()` and handles `EOFError`. This plan adds NO setup call site; `run_wizard`/`run_session` are the reusable entry points Order 05 will call.
- Repository prompts must be self-contained, default behavior explicit, and EOF/KeyboardInterrupt handled cleanly by the existing CLI boundary. VERIFIED: `_confirm` at `agent_workflows/cli.py:4524` renders `[y/N]` and returns False on `EOFError`; `cli.main` at `:10345` catches `KeyboardInterrupt`/`EOFError` and returns 130 rather than dumping a traceback. The wizard converts both into `WizardCancelled` locally so a cancel is a typed no-write result rather than an exception crossing the boundary.
- The OpenCode CLI documents opencode models as the model inventory command and --variant as provider-specific. The wizard must not pretend every common value works for every model. VERIFIED against the installed binary, not from memory: `opencode models --help` says "list all available models" and carries a `--refresh` flag documented as "refresh the models cache from models.dev" (hence its place in `FORBIDDEN_CATALOG_FLAGS`); `opencode run --help` documents `--variant` verbatim as "model variant (provider-specific reasoning effort, e.g., high, max, minimal)". The variant menu quotes that provider-specific framing and stores "provider default" as NO variant. Also measured: `opencode models | wc -l` = 140 on this machine, which is why paging is required rather than optional.
- The runner's argv order is `--model`, `--variant`, `--agent`, each appended only when set (`agent_workflows/oc_runipd.py:5068-5073`). `opencode_argv_fields` mirrors exactly that, so the preview is the REAL expansion rather than a plausible-looking one.

## Findings

| Risk | Superficial implementation | Required falsifier |
|---|---|---|
| Huge model catalog | Dump every model and ask for a number. | Filter/paging tests with hundreds of entries. |
| Private model missing from catalog | Refuse profile creation. | Manual exact-ID path succeeds after discovery failure. |
| Variant support unknown | Claim a selected value is supported. | UI labels it provider-specific and preserves exact manual choice. |
| Duplicate alias | Silently overwrite. | Existing bytes unchanged without --replace. |
| Default side effect | First profile automatically becomes default. | Both default questions are separate and default No. |
| Shell/config exposure | Build a shell string or print provider credentials. | argv-list mock and redaction assertions. |
| Sequencing against an approved plan | FOUND AT REVIEW (PR-001, BLOCKER): APPROVED `0soncw` is RETIRING the `aw run` noun this plan builds on (its E-05 leaves a nonzero-exit deprecation stub), and no plan in this Set mentions it. They are complementary, not contradictory: `0soncw` frees the name "for a future driver verb", which is this Set. Escalated as blocking OQ-01 on the orchestrator `3m0urk`; recommended order is `0soncw` FIRST, then this Set. Do NOT execute this plan until that order is settled. | Settle orchestrator OQ-01 before executing. |
| Unverifiable "already" claims | FOUND AT REVIEW (PR-002): this plan carries ZERO `file:line` citations, as does every member of this Set (measured: 0 across all six, versus 9/4/5 in the comparable `6lu3rq`/`m73aet`/`wlxkoz` plans). The claims spot-checked at review were TRUE, so this is evidence discipline rather than incorrectness, but an executor cannot cheaply re-verify a premise. MEASURE and cite `file:line` for every "already" claim before relying on it; HEAD moves hourly here. DISCHARGED AT EXECUTION: every premise re-measured at HEAD `f0c7f023` and cited in the "Project conventions discovered" section below; all five held, none had drifted. | Cite `file:line` for each, measured at the current HEAD. |
| ADDED AT EXECUTION: a shared argparse action mutated in place | Declare the plan's "optional `--agent`" on the `add` subparser, matching the profile field's name. | MEASURED DEFECT, not a style call: argparse `parents=` SHARES the action OBJECT and `_AwArgumentParser`'s `conflict_handler="resolve"` mutates it IN PLACE, so declaring `--agent` on a `parents=[common]` subparser EMPTIED the repo-wide machine-output flag's option strings (`agent_workflows/cli.py:729`). Measured consequences: `aw attention` then parsed with `agent=True` permanently on, and `aw oc profile add --agent build` reported "unrecognized arguments: --agent". Spelled `--oc-agent` instead (same capability); `test_the_repo_wide_agent_output_flag_is_intact` is the standing guard. |

## Proposed changes (ordered, validatable)

1. Add safe read-only model discovery.
2. Build the reusable dependency-injected interview.
3. Add fixed profile-management verbs and atomic default choices.
4. Test every affirmative, negative, interrupted, and unavailable path.

## Deferred / out of scope (with reason)

- Network refresh, pricing sync, and OpenCode config writes remain owned by aw oc update-models; profile creation is read-only toward OpenCode.
- Rich terminal fuzzy-search dependencies are excluded; deterministic substring filtering and paging are sufficient and stdlib-only.
- Live validation by launching a paid model is excluded. The wizard validates shape and discovered membership, not provider authorization or future availability.
- Broader aw setup integration is Order 05 so this child remains reusable and independently testable.

## Scope check

- Over-scope: no runner launch/state behavior, generic aw run dispatch, setup integration, tracked configuration, or documentation.
- Under-scope: add/list/show/remove/default, interactive and noninteractive creation, model and variant selection, previews, defaults, no-clobber, and failure handling are included.

## Required tests / validation

- python3 -m pytest -p no:randomly tests/test_runner_profile_wizard.py tests/test_oc_profile_cli.py -q
- Mocked subprocess assertions for argv, timeout, shell=False, nonzero/garbage output, and no refresh.
- Scripted input/output transcripts for discovered, filtered, manual, cancelled, EOF, duplicate, and default flows.
- Byte-comparison assertions that every declined/failed path leaves prior configuration unchanged.

## Spec / documentation sync

- CLI help is updated for aw oc profile.
- User guide and setup documentation are reserved for Order 05 to avoid duplicating unfinished UX prose.

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
  - Required evidence: Paste focused tests showing the exact opencode models argv with shell=False and timeout; ANSI/noise normalization; exact provider/model filtering; deterministic dedupe; config fallback without secret resolution; and distinct missing/timeout/nonzero/malformed/empty diagnostics. Include a negative assertion that neither --refresh nor a write flag is issued.
  - Observed evidence: IMPLEMENTATION: `agent_workflows/oc_models.py` gains `discover_models`, `catalog_argv`,
    `parse_models_output`, `models_from_config`, `catalog_from_config`, `strip_ansi`, the `ModelCatalog`
    NamedTuple, and six named `CATALOG_*` diagnostics. `ModelCatalog.available` is `bool(models)`, so a
    "successful empty catalog" is UNREPRESENTABLE rather than merely discouraged.

    ACTUAL OUTPUT, `python3 -m pytest tests/test_runner_profile_wizard.py -o addopts="" -v -k
    "CatalogArgv or CatalogParsing or CatalogDiagnostic or CatalogConfigFallback"`:

    ```
    CatalogArgvTests::test_argv_is_exactly_the_read_only_probe PASSED
    CatalogArgvTests::test_no_refresh_or_write_flag_is_ever_issued PASSED
    CatalogArgvTests::test_argv_builder_refuses_a_smuggled_forbidden_flag PASSED
    CatalogArgvTests::test_shell_is_false_and_the_timeout_is_bounded PASSED
    CatalogArgvTests::test_default_timeout_is_finite PASSED
    CatalogParsingTests::test_ansi_and_noise_are_normalized_and_only_exact_records_survive PASSED
    CatalogParsingTests::test_dedupe_is_deterministic_and_first_seen PASSED
    CatalogParsingTests::test_the_accepted_grammar_is_the_profile_schemas_own PASSED
    CatalogParsingTests::test_strip_ansi_removes_csi_and_osc PASSED
    CatalogDiagnosticTests::test_missing_binary PASSED
    CatalogDiagnosticTests::test_timeout PASSED
    CatalogDiagnosticTests::test_nonzero_exit PASSED
    CatalogDiagnosticTests::test_malformed_output PASSED
    CatalogDiagnosticTests::test_empty_output PASSED
    CatalogDiagnosticTests::test_oserror_is_a_missing_binary_not_a_crash PASSED
    CatalogDiagnosticTests::test_a_successful_empty_catalog_is_unrepresentable PASSED
    CatalogDiagnosticTests::test_every_diagnostic_reason_is_distinct PASSED
    CatalogConfigFallbackTests::test_only_provider_model_keys_are_read_and_no_secret_escapes PASSED
    CatalogConfigFallbackTests::test_fallback_supplies_ids_and_still_reports_why_the_cli_failed PASSED
    CatalogConfigFallbackTests::test_no_config_is_its_own_reason PASSED
    CatalogConfigFallbackTests::test_garbage_config_is_not_an_exception PASSED
    CatalogConfigFallbackTests::test_config_fallback_never_resolves_an_api_key PASSED
    ======================= 22 passed, 64 deselected in 0.15s ======================
    ```

    THE NEGATIVE ASSERTION, as required: `test_no_refresh_or_write_flag_is_ever_issued` asserts the
    recorded argv equals `["opencode", "models"]` and contains none of `FORBIDDEN_CATALOG_FLAGS`
    (`--refresh`, `--apply`, `--write`, `--update`). `test_shell_is_false_and_the_timeout_is_bounded`
    asserts `shell is False`, `timeout == 7.5`, `capture_output is True`, `text is True`,
    `check is False` on the injected runner's recorded kwargs.

    NO-SECRET FALLBACK, asserted structurally not textually: `test_config_fallback_never_resolves_an_api_key`
    walks the AST of all three fallback functions and asserts `resolve_api_key` is never CALLED and that
    no string literal `apiKey`/`options`/`headers`/`Authorization` appears in code (docstrings excluded,
    since a comment naming what is deliberately NOT read is the documentation this boundary should carry).

    AGAINST THE REAL INSTALLATION (not only mocks), `python3 -c` on this machine:

    ```
    source: opencode-cli | reason: '' | count: 140
    first 3: ('opencode/big-pickle', 'opencode/ling-3.0-flash-fin-free', 'opencode/mimo-v2.5-free')
    argv: ['opencode', 'models']
    missing binary -> False executable-not-found
    ```

    MUTATION-TESTED, so the tests are proven falsifiers rather than assumed ones. Replacing the
    `FileNotFoundError` branch with `return ModelCatalog(models=(), source=CATALOG_SOURCE_CLI)` (the exact
    green-washing this item forbids) produced:

    ```
    FAILED tests/test_runner_profile_wizard.py::CatalogConfigFallbackTests::test_fallback_supplies_ids_and_still_reports_why_the_cli_failed
    FAILED tests/test_runner_profile_wizard.py::CatalogDiagnosticTests::test_missing_binary
    2 failed, 84 passed in 0.30s
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Paste scripted interview transcripts/tests for small and 200-entry filtered/paged catalogs, exact manual fallback, provider-default/common/custom variants, exact preview, invalid retry, cancel/empty/EOF/interrupt, and discovery unavailable. Show every non-save path leaves the config absent or byte-identical.
  - Observed evidence: IMPLEMENTATION: `agent_workflows/runner_profile_wizard.py` (new). Every input, output,
    the catalog, and the store read/write arrive as injected `WizardIO` fields, so the module calls no
    `input()`, `print()`, `subprocess`, or `store_path()` of its own and the whole interview runs from a
    scripted transcript with no TTY.

    ACTUAL OUTPUT, `python3 -m pytest tests/test_runner_profile_wizard.py -o addopts="" -v -k
    "FilterAndPage or ManualEntry or Variant or Preview or ProfileName or YesNo or Interview or NonSave"`
    (42 passed; the 200-entry, manual-fallback, variant, preview, retry and cancel branches):

    ```
    FilterAndPageTests::test_filter_is_case_insensitive_substring_and_order_preserving PASSED
    FilterAndPageTests::test_a_200_entry_catalog_is_paged_not_dumped PASSED
    FilterAndPageTests::test_paging_forward_then_picking_uses_absolute_numbering PASSED
    FilterAndPageTests::test_paging_backward_is_bounded_not_wrapped PASSED
    FilterAndPageTests::test_filtering_a_200_entry_catalog_narrows_the_choice PASSED
    FilterAndPageTests::test_a_filter_matching_nothing_is_reported_and_recoverable PASSED
    FilterAndPageTests::test_out_of_range_and_garbage_are_reported_then_retried PASSED
    ManualEntryTests::test_manual_entry_is_reachable_from_a_working_catalog PASSED
    ManualEntryTests::test_manual_entry_is_the_only_path_when_discovery_failed PASSED
    ManualEntryTests::test_an_invalid_manual_model_is_rejected_with_the_schemas_message PASSED
    ManualEntryTests::test_manual_entry_gives_up_after_a_bounded_number_of_attempts PASSED
    VariantTests::test_provider_default_stores_no_variant PASSED
    VariantTests::test_empty_input_takes_the_provider_default PASSED
    VariantTests::test_every_common_variant_is_selectable PASSED
    VariantTests::test_a_custom_exact_variant_is_preserved_verbatim PASSED
    VariantTests::test_the_menu_labels_variants_provider_specific_and_does_not_overclaim PASSED
    VariantTests::test_an_invalid_custom_variant_is_refused_by_the_schemas_own_validator PASSED
    VariantTests::test_the_field_validator_routes_through_the_public_schema_api PASSED
    PreviewTests::test_the_argv_preview_matches_the_runners_own_flag_order PASSED
    PreviewTests::test_absent_fields_emit_no_flag_at_all PASSED
    PreviewTests::test_the_preview_shows_the_exact_stored_fields_and_the_exact_launch PASSED
    PreviewTests::test_a_provider_default_variant_is_shown_as_such_not_as_a_guess PASSED
    ProfileNameTests::test_the_grammar_is_the_schemas_own_and_bad_names_retry PASSED
    ProfileNameTests::test_an_existing_name_is_refused_without_replace PASSED
    ProfileNameTests::test_replace_permits_the_existing_name PASSED
    YesNoTests::test_empty_input_takes_the_rendered_default PASSED
    YesNoTests::test_the_default_is_rendered_explicitly PASSED
    YesNoTests::test_eof_is_a_cancel_not_a_silent_yes PASSED
    YesNoTests::test_a_quit_word_cancels PASSED
    InterviewTests::test_a_discovered_flow_saves_exactly_once PASSED
    InterviewTests::test_the_preview_precedes_the_save_question PASSED
    InterviewTests::test_a_manual_model_and_a_custom_variant_round_trip PASSED
    InterviewTests::test_a_preseeded_name_skips_the_name_question PASSED
    InterviewTests::test_an_existing_preseeded_name_refuses_without_replace_and_writes_nothing PASSED
    NonSaveWritesNothingTests::test_declining_the_save_question_writes_nothing PASSED
    NonSaveWritesNothingTests::test_the_save_question_defaults_to_no_on_empty_input PASSED
    NonSaveWritesNothingTests::test_an_explicit_quit_word_cancels PASSED
    NonSaveWritesNothingTests::test_eof_cancels PASSED
    NonSaveWritesNothingTests::test_a_keyboard_interrupt_cancels_cleanly PASSED
    NonSaveWritesNothingTests::test_no_writer_means_no_write_is_even_possible PASSED
    NonSaveWritesNothingTests::test_a_write_failure_is_reported_and_not_claimed_as_saved PASSED
    NonSaveWritesNothingTests::test_an_unreadable_config_is_reported_not_treated_as_empty PASSED
    ```

    THE 200-ENTRY CASE IS MEASURED, not asserted loosely: `test_a_200_entry_catalog_is_paged_not_dumped`
    counts the rendered `[n]` lines and asserts exactly `PAGE_SIZE` (20) of 200 are shown plus the header
    `page 1/10`. `test_filtering_a_200_entry_catalog_narrows_the_choice` asserts the header reads
    `Models (100 matching 'model-1')` and that entry 1 of the FILTERED list is `vendor0/model-100`, i.e.
    numbering restarts within the filter and is not the full list's first item.

    BYTE-IDENTICAL, proven by comparing REAL FILE BYTES (`ByteIdenticalConfigTests` writes a seeded
    store with `RP.save`, records `read_bytes()`, runs the interview, re-reads):

    ```
    ByteIdenticalConfigTests::test_declined_save_leaves_the_bytes_identical PASSED
    ByteIdenticalConfigTests::test_cancel_leaves_the_bytes_identical PASSED
    ByteIdenticalConfigTests::test_eof_leaves_the_bytes_identical PASSED
    ByteIdenticalConfigTests::test_interrupt_leaves_the_bytes_identical PASSED
    ByteIdenticalConfigTests::test_declining_the_defaults_still_changes_only_the_profiles_block PASSED
    ByteIdenticalConfigTests::test_an_absent_config_stays_absent_after_a_decline PASSED
    ```

    DISCOVERY UNAVAILABLE, END TO END AGAINST THE REAL SCHEMA AND A REAL FILE (binary absent, private
    three-segment model typed exactly, XDG redirected to a temp dir). ACTUAL transcript:

    ```
    PROMPT Profile name (e.g. gem): sonnet
    Model discovery is unavailable (executable-not-found: 'opencode-not-installed' was not found on PATH).
    Enter the exact provider/model identifier you want to use.
    PROMPT Exact provider/model (e.g. google/gemini-3.7-flash): uri/its_direct/pt3-claude-sonnet-5-1m-us
    ...
    PROMPT Variant [1]: 3
    PROMPT OpenCode agent (optional; press Enter for none):
    Profile 'sonnet' will be stored as:
      runner:  oc
      model:   uri/its_direct/pt3-claude-sonnet-5-1m-us
      variant: medium
      agent:   (none)
    Equivalent OpenCode launch:
      opencode run --model uri/its_direct/pt3-claude-sonnet-5-1m-us --variant medium
    PROMPT Save profile 'sonnet'? [y/N] y
    === saved: True | model: uri/its_direct/pt3-claude-sonnet-5-1m-us | variant: medium
    ```

    So the private-model case the plan's findings table calls out ("Private model missing from catalog /
    Refuse profile creation") is discharged: total discovery failure still creates the profile.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Paste CLI help and focused add/list/show/remove/default tests for interactive and fully noninteractive forms, JSON/agent-safe output, duplicate refusal, explicit replace, remove-default integrity, clear-default, non-TTY incomplete refusal, exact exit codes, and proof existing aw oc run/update-models routing remains unchanged.
  - Observed evidence: ACTUAL CLI HELP, `python3 -m agent_workflows oc profile --help`:

    ```
    usage: agent-workflows oc profile [-h] [--no-color] [--agent] [--json]
                                      {add,list,ls,show,remove,rm,default} ...

    positional arguments:
      {add,list,ls,show,remove,rm,default}
        add                 Create a profile: interactive wizard on a TTY, or
                            fully specified with --model/--yes.
        list (ls)           List every profile with its model, variant, agent, and
                            which one is the default.
        show                Show one profile and the exact OpenCode launch it
                            expands to.
        remove (rm)         Remove a profile; removing the default one requires an
                            explicit decision.
        default             Set or clear the default OpenCode profile (used when
                            you name none).
    ```

    ACTUAL OUTPUT, `python3 -m pytest tests/test_oc_profile_cli.py -o addopts="" -v` (49 passed):

    ```
    ParserSurfaceTests::test_oc_help_lists_the_profile_verb PASSED
    ParserSurfaceTests::test_profile_help_lists_every_verb PASSED
    ParserSurfaceTests::test_add_help_shows_every_flag PASSED
    ParserSurfaceTests::test_help_does_not_overclaim_variant_support_or_opencode_mutation PASSED
    ParserSurfaceTests::test_the_verbs_are_FIXED_so_a_profile_name_is_never_a_command PASSED
    ParserSurfaceTests::test_command_like_profile_names_remain_legal_arguments PASSED
    ParserSurfaceTests::test_the_repo_wide_agent_output_flag_is_intact PASSED
    ParserSurfaceTests::test_bare_profile_shows_family_help_rather_than_acting PASSED
    NeighbouringVerbsUnchangedTests::test_oc_run_still_forwards_its_REMAINDER_verbatim PASSED
    NeighbouringVerbsUnchangedTests::test_oc_update_models_still_dispatches_from_the_namespace PASSED
    NeighbouringVerbsUnchangedTests::test_profile_dispatch_does_not_reach_the_runner PASSED
    AddTests::test_the_complete_noninteractive_form_saves PASSED
    AddTests::test_an_agent_is_stored_via_oc_agent PASSED
    AddTests::test_no_variant_means_the_provider_default_and_stores_nothing PASSED
    AddTests::test_a_duplicate_is_refused_and_the_bytes_are_unchanged PASSED
    AddTests::test_replace_is_the_explicit_opt_in_to_overwrite PASSED
    AddTests::test_without_a_tty_an_incomplete_add_refuses_and_writes_nothing PASSED
    AddTests::test_the_noninteractive_form_requires_yes PASSED
    AddTests::test_model_without_a_name_is_refused PASSED
    AddTests::test_yes_cannot_preconfirm_the_interactive_form PASSED
    AddTests::test_an_invalid_model_is_refused_with_the_schemas_message PASSED
    AddTests::test_an_invalid_profile_name_is_refused PASSED
    AddTests::test_a_reserved_grammar_word_cannot_be_a_profile_name PASSED
    AddTests::test_add_never_sets_a_default_implicitly PASSED
    AddTests::test_set_default_is_the_explicit_opt_in_and_is_ONE_write PASSED
    AddTests::test_add_never_touches_opencode_configuration PASSED
    AddTests::test_the_interactive_form_runs_the_wizard PASSED
    AddTests::test_a_declined_wizard_exits_nonzero_without_claiming_success PASSED
    ListShowTests::test_an_empty_list_is_a_clean_result_not_an_error PASSED
    ListShowTests::test_list_json_carries_every_profile_and_the_default PASSED
    ListShowTests::test_list_agent_output_is_one_jsonl_record PASSED
    ListShowTests::test_no_machine_record_leaks_a_home_path PASSED
    ListShowTests::test_the_store_path_is_home_preserved_when_under_home PASSED
    ListShowTests::test_show_prints_the_exact_launch PASSED
    ListShowTests::test_show_of_an_unknown_profile_is_an_actionable_exit_2 PASSED
    ListShowTests::test_a_malformed_store_is_reported_not_treated_as_empty PASSED
    ListShowTests::test_json_output_carries_no_credential_shaped_field PASSED
    RemoveTests::test_remove_deletes_the_profile PASSED
    RemoveTests::test_removing_the_default_demands_an_explicit_decision PASSED
    RemoveTests::test_clear_default_is_one_of_the_two_explicit_decisions PASSED
    RemoveTests::test_a_replacement_is_the_other_explicit_decision PASSED
    RemoveTests::test_removing_an_unknown_profile_is_exit_2 PASSED
    RemoveTests::test_without_a_tty_remove_requires_yes PASSED
    DefaultTests::test_default_sets_the_profile PASSED
    DefaultTests::test_clear_removes_it PASSED
    DefaultTests::test_naming_an_unknown_profile_is_exit_2_and_changes_nothing PASSED
    DefaultTests::test_a_name_and_clear_together_are_refused PASSED
    DefaultTests::test_neither_a_name_nor_clear_is_refused PASSED
    DefaultTests::test_default_json_reports_the_new_value PASSED
    49 passed in 2.35s
    ```

    EXACT EXIT CODES, from a live run against a temp XDG store:

    ```
    $ aw oc profile add gem --model other/model --yes      # duplicate
    error: profile 'gem' already exists; pass replace=True (CLI: --replace) to overwrite it
    RC=2      unchanged: yes           # sha256 of the store identical before/after
    $ aw oc profile remove gem --yes                        # gem is the default
    error: profile 'gem' is the default for ['oc']. Decide explicitly: clear the default
    (clear_default=True) or name a replacement (replacement=<profile>). Removing it silently
    would fall back to the host default model.
    RC=2
    $ aw oc profile remove gem --yes --clear-default
    Removed profile 'gem'.                                  RC=0
    $ aw oc profile show gem
    error: no runner profile named 'gem' (known profiles: (none)). Create it with 'aw oc profile add gem'.
    RC=2
    $ aw oc profile add nope                                # non-TTY, incomplete
    error: no TTY and no --model: the noninteractive form needs at least '--model <provider/model> --yes'.
    Nothing was written.                                    RC=2
    ```

    NEIGHBOURING ROUTING UNCHANGED, asserted on the call not merely the exit code:
    `test_oc_run_still_forwards_its_REMAINDER_verbatim` patches `oc_runipd.main` and asserts it received
    exactly `["somesel", "--action", "review", "--weird-flag"]`; `test_oc_update_models_still_dispatches_from_the_namespace`
    asserts `oc_models.run(["--apply"])`.

    A DEFECT FOUND AND FIXED DURING THIS ITEM, recorded because it is a real regression this validation
    caught rather than a stylistic choice. The plan says `add` takes "optional --agent". Declaring
    `--agent` on a `parents=[common]` subparser does NOT merely shadow the repo-wide machine-output flag:
    argparse `parents=` SHARES the action OBJECT, and this file's `conflict_handler="resolve"`
    (`_AwArgumentParser.__init__`) then mutates that shared object IN PLACE. MEASURED: after adding it,
    `common`'s own `--agent` option strings were EMPTIED, `aw attention` parsed with `agent=True`
    permanently on, and `aw oc profile add --agent build` reported "unrecognized arguments: --agent".
    The field is therefore spelled `--oc-agent` (same capability, no collision) and
    `test_the_repo_wide_agent_output_flag_is_intact` is a standing regression guard asserting
    `parse_args(["attention"]).agent is False` and that exactly one action owns `["--agent"]`.

    MUTATION-TESTED: forcing `add_profile(..., replace=True)` (a silent overwrite) produced
    `FAILED tests/test_oc_profile_cli.py::AddTests::test_a_duplicate_is_refused_and_the_bytes_are_unchanged
    1 failed, 48 passed`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Paste tests showing the save, OpenCode-default, and global-default questions are separate and default No; all accepted changes land in one atomic write; declining either preserves its previous value; first/existing-profile cases behave identically; and Configure another profile is invoked only by an explicit interactive session.
  - Observed evidence: ACTUAL OUTPUT, `python3 -m pytest tests/test_runner_profile_wizard.py -o addopts="" -v
    -k "DefaultQuestion or SessionLoop"`:

    ```
    DefaultQuestionTests::test_both_default_questions_are_asked_separately PASSED
    DefaultQuestionTests::test_both_default_questions_render_and_take_no PASSED
    DefaultQuestionTests::test_the_first_profile_does_not_become_the_default_automatically PASSED
    DefaultQuestionTests::test_accepting_both_defaults_lands_in_ONE_atomic_write PASSED
    DefaultQuestionTests::test_declining_the_profile_default_preserves_the_previous_one PASSED
    DefaultQuestionTests::test_declining_the_runner_default_preserves_the_previous_value PASSED
    DefaultQuestionTests::test_an_existing_default_of_the_same_name_is_not_re_asked PASSED
    DefaultQuestionTests::test_ask_defaults_false_suppresses_both_questions PASSED
    SessionLoopTests::test_the_loop_is_opt_in_and_run_wizard_never_loops PASSED
    SessionLoopTests::test_the_session_asks_between_rounds_and_stops_on_no PASSED
    SessionLoopTests::test_the_session_can_configure_two_profiles PASSED
    SessionLoopTests::test_the_session_stops_on_cancel PASSED
    ```

    SEPARATE, AND COUNTED: `test_both_default_questions_are_asked_separately` asserts BOTH prompt strings
    are present AND that exactly TWO default-bearing questions were asked, so a single combined
    "make this the default and the default runner?" question fails the test.

    DEFAULT NO, RENDERED: `test_both_default_questions_render_and_take_no` answers both with EMPTY input
    and asserts the written config has `default_profile_for("oc") is None` and `default_runner is None`,
    then asserts every default-bearing prompt literally contains `[y/N]`.

    ONE ATOMIC WRITE: `test_accepting_both_defaults_lands_in_ONE_atomic_write` answers y/y and asserts
    `len(store.writes) == 1` while both defaults are present in that single document. On the CLI side
    `test_set_default_is_the_explicit_opt_in_and_is_ONE_write` wraps `runner_profiles.save` and asserts
    `call_count == 1`.

    DECLINING PRESERVES THE PRIOR VALUE: `test_declining_the_profile_default_preserves_the_previous_one`
    seeds `sol` as the default, saves a new `gem` while declining, and asserts the written default is
    still `sol`. `test_declining_the_runner_default_preserves_the_previous_value` seeds
    `default_runner = oc` and asserts the runner question is NOT asked at all (it would change nothing)
    while the stored value survives.

    THE LOOP IS OPT-IN: `test_the_loop_is_opt_in_and_run_wizard_never_loops` asserts no prompt contains
    "another profile" during a plain `run_wizard`; only `run_session` asks it. The noninteractive CLI
    `add` path never calls `run_session`.

    LIVE END-TO-END, both questions answered differently in one interview (XDG redirected to a temp dir,
    real `opencode models`, real `RP.save`). ACTUAL transcript tail and resulting file:

    ```
    PROMPT Save profile 'gem'? [y/N] y
    PROMPT Make 'gem' the default OpenCode profile? [y/N] y
    PROMPT Make OpenCode the default IPD runner? [y/N] n
    Saved profile 'gem'. Use it with: aw oc run as gem
    'gem' is now your default OpenCode profile.
    === saved: True | default_profile: True | default_runner: False
    === on disk: {
      "defaults": { "profiles": { "oc": "gem" } },
      "profiles": { "gem": { "model": "opencode/big-pickle", "runner": "oc", "variant": "high" } },
      "schema_version": 1
    }
    ```

    The accepted profile-default is present and the DECLINED runner-default is absent (no
    `default_runner` key), which is the independence this item requires.

    MUTATION-TESTED: hard-coding `make_default_profile = True` (the "first profile silently becomes the
    default" side effect the plan's findings table names) produced 6 failures including
    `test_the_first_profile_does_not_become_the_default_automatically`,
    `test_both_default_questions_are_asked_separately`, and
    `test_declining_the_profile_default_preserves_the_previous_one`.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Paste the complete focused-suite command, exit code, and summary with test names covering every interaction/error branch. Include byte comparisons for cancelled/failed/default-No flows and captured output searched for sentinel credentials to prove none were printed.
  - Observed evidence: THE PLAN'S NAMED FOCUSED COMMAND, run verbatim with its exit code:

    ```
    $ python3 -m pytest -p no:randomly tests/test_runner_profile_wizard.py tests/test_oc_profile_cli.py -q -o addopts=""
    ........................................................................ [ 53%]
    ...............................................................          [100%]
    135 passed in 2.43s
    EXIT=0
    ```

    (`-o addopts=""` is needed because the repo's configured `addopts` already supplies `-q`, and a second
    `-q` compounds into `-qq`, which SUPPRESSES the `N passed` summary line this item requires.)

    THE FULL SUITE, run BARE per the repo contract (`python3 -m pytest`):

    ```
    31 failed, 5036 passed, 3 skipped, 4 xfailed in 38.20s
    ```

    THE 31 FAILURES ARE PRE-EXISTING AND NOT MINE, verified rather than asserted. I removed my five files
    (restoring `cli.py`/`oc_models.py` and moving the three new files aside), re-ran bare, and got the
    IDENTICAL failure set:

    ```
    baseline (my changes absent):  31 failed, 4901 passed, 3 skipped, 4 xfailed
      14 tests/test_run_viewer.py       7 tests/test_oc_runipd.py
       6 tests/test_agy_runipd_cli.py   2 tests/test_ipd_lifecycle_cli.py
       1 tests/test_worker_role_refusal.py   1 tests/test_novalnomerge_integration.py

    with my changes:               31 failed, 5036 passed, 3 skipped, 4 xfailed
      (same six files, same per-file counts; passing count +135, exactly my new tests)
    ```

    No file I touched appears in the failure list, and the per-file distribution is unchanged.

    NEIGHBOURING SUITES FOR THE MODULES I EDITED:

    ```
    $ python3 -m pytest tests/test_runner_profiles.py tests/test_oc_models.py tests/test_oc_models_cli.py -o addopts="" -q
    118 passed in 0.84s
    ```

    BYTE COMPARISONS, at both layers. Wizard layer (`ByteIdenticalConfigTests`) seeds a real store, records
    `read_bytes()`, runs the interview, and re-reads for declined-save / cancel / EOF / interrupt, plus
    "an absent config stays absent". CLI layer asserts the same for a refused duplicate
    (`test_a_duplicate_is_refused_and_the_bytes_are_unchanged`), a refused remove-of-default, an unknown
    remove, an unknown default, and a non-TTY refusal. A live sha256 check confirmed it outside pytest:
    `unchanged: yes`.

    SENTINEL CREDENTIAL SEARCH: `test_no_wizard_output_contains_a_sentinel_credential` puts
    `sk-sentinel-must-never-be-printed-9999` in the environment, runs a full save-with-both-defaults
    interview, and asserts the sentinel and the string `apiKey` appear in NEITHER the emitted lines, NOR
    the prompts, NOR the result messages. `test_json_output_carries_no_credential_shaped_field` asserts
    `apiKey`/`api_key`/`token`/`secret`/`Authorization` are absent from `--json` output.
    `test_only_provider_model_keys_are_read_and_no_secret_escapes` seeds the sentinel as a provider
    `apiKey` in a config and asserts the returned model ids do not contain it.

    STATIC AUDITS: `test_the_wizard_never_shells_out_or_evaluates_text` (no `shell=True`, `os.system`,
    `eval(`, `exec(`), `test_the_wizard_reads_no_environment_variable`, and
    `test_the_wizard_never_writes_opencode_configuration` (no `write_config`, `opencode.json`, `--refresh`).

    REPO GATES:

    ```
    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,
     "verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    SANITIZE_EXIT=0

    $ git diff --check     -> clean
    $ pre-commit run ruff       --files <my 5 files>  -> Passed
    $ pre-commit run ruff-format --files <my 5 files> -> reformatted (applied; 135 tests still pass)
    ```

    ANTI-GREENWASH NOTE: three mutants were injected and each was caught (see V-01, V-03, V-04), so these
    tests are demonstrated falsifiers rather than assumed ones.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

1. Human approval is required; there are no unresolved questions.
2. Order 01 (f2mrsw) must be executed. If its module/API is absent or materially different, STOP and report rather than recreating profile storage here.
3. Touch only Scope-Paths. Preserve aw oc run REMAINDER forwarding and aw oc update-models behavior.
4. Never print credentials, mutate OpenCode configuration, refresh the network catalog by default, evaluate shell text, or auto-select defaults.
5. Run every named focused test and paste ACTUAL output with exit codes; unrun is not pass.
6. Commit only this plan's files, path-scoped; inspect git diff --cached --name-only; never use git add -A, bare git add, git commit -a, --no-verify, or push.
7. After every E/V item passes, run aw ipd lint --phase pre-transition, then aw ipd finalize PLAN --actor AGENT/MODEL --message SUMMARY --apply. Lifecycle transition is not an E-item.
