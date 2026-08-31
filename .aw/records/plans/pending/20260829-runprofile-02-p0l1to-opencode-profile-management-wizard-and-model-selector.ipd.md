# IPD: OpenCode profile management wizard and model selector

- Date: 2026-08-29
- Kind: child
- Concern: A storage API alone does not provide a usable or safe way to create aliases. Users need a reusable word-oriented profile command, an interactive model/variant selector, exact previews, explicit default questions, and deterministic noninteractive controls. Model discovery can fail, return a very large list, include ANSI/noise, or omit private models, so the wizard must degrade to manual entry without fabricating support.
- Scope: Add OpenCode profile-management commands and a reusable wizard. Discover models from the user's actual OpenCode installation/configuration without refreshing or mutating it, offer filtering and exact manual entry, collect a provider-specific variant without overclaiming validation, preview the resolved launch, persist atomically through the Order-01 API, and manage per-OpenCode/global defaults explicitly.
- Scope-Paths: agent_workflows/runner_profile_wizard.py, agent_workflows/oc_models.py, agent_workflows/cli.py, tests/test_runner_profile_wizard.py, tests/test_oc_profile_cli.py
- Item-Dependencies: executed:f2mrsw
- Status: to-review
- Set: runprofile
- Order: 2
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: p0l1to

## Workflow history

- 2026-08-30 to-review (codex gpt-5.6): authored as the reusable OpenCode profile wizard and management surface.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Let a user create gem, sonnet, or sol without editing JSON or remembering flags. The wizard must select from the models OpenCode can actually see when possible, always allow an exact manual model, show the exact structured expansion, and ask separately before changing defaults.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: model discovery and reusable interview

- [ ] E-01 Add a read-only model-catalog function at the existing OpenCode boundary. Invoke the configured OpenCode executable as an argv list with shell=False, a bounded timeout, captured output, and no refresh/write flags; normalize ANSI and whitespace; accept only exact nonempty provider/model records; deduplicate deterministically. Treat missing binary, timeout, nonzero exit, malformed output, and empty results as explicit unavailable diagnostics, never an empty successful catalog. Reuse existing OpenCode config-path helpers only as a no-secret fallback for statically declared model IDs.
  - Depends on: none
  - Expected outcome: the wizard can list the user's public and private configured models without network refresh, configuration mutation, credential output, shell evaluation, or false success.
  - Execution state: pending

- [ ] E-02 Create runner_profile_wizard.py as a dependency-injected TTY interview that can be unit-tested with scripted input/output. It asks for/validates a profile name; supports case-insensitive substring filtering and bounded/paged numeric selection for large model catalogs; always offers exact manual provider/model entry; offers Provider default (stored as no variant), common low|medium|high|max choices labeled provider/model-specific, and exact custom variant entry; then prints the exact profile and equivalent OpenCode argv fields before a default-No save confirmation.
  - Depends on: E-01
  - Expected outcome: a user can select the requested three models and variants even when discovery is unavailable or incomplete, while cancellation/EOF/invalid input writes nothing.
  - Execution state: pending

### Task group 2: profile verbs and default questions

- [ ] E-03 Add aw oc profile add|list|show|remove|default as a fixed CLI namespace. add [NAME] starts the wizard on a TTY, prompting for NAME when omitted; a complete noninteractive form accepts structured --model, optional --variant, optional --agent, and explicit --yes, with --replace required to overwrite. default NAME sets the OpenCode default; default --clear clears it. All commands use Order-01 storage/mutation functions, return actionable nonzero errors, and never alter OpenCode configuration.
  - Depends on: E-01, E-02
  - Expected outcome: profile lifecycle is discoverable and scriptable without dynamic commands, hand-edited JSON, ambiguous overwrites, or shell aliases.
  - Execution state: pending

- [ ] E-04 After a profile is saved, ask two separate default-No questions: Make NAME the default OpenCode profile? and, only when appropriate, Make OpenCode the default IPD runner? Apply the accepted profile plus accepted defaults in one validated atomic write; declining either question must preserve its prior value. Permit repeated Configure another profile? only in the explicit wizard/session caller, not as an automatic loop inside noninteractive commands.
  - Depends on: E-02, E-03
  - Expected outcome: setting an alias never silently changes unqualified runs, while users can intentionally establish both requested defaults during the same interview.
  - Execution state: pending

- [ ] E-05 Add interaction and CLI tests for successful discovered/manual flows, filtering/paging, common/custom/provider-default variants, first-profile and existing-default cases, exact preview, invalid inputs/retry limits, cancel/empty/EOF/interrupt, discovery failures, no-TTY incomplete invocation, duplicate/replace/remove/default integrity, JSON/agent-safe listing, and assertions that default-No or failed flows leave the config bytes unchanged.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: tests fail if the wizard green-washes discovery failure, hides the exact expansion, writes after cancellation, assumes a default, leaks credentials, overwrites an alias, or cannot select a private/manual model.
  - Execution state: pending

## Project conventions discovered (Step 0)

- aw oc is a fixed host command group in agent_workflows/cli.py; unlike aw oc run, structured profile-management verbs belong in that parser and dispatcher rather than the runner's REMAINDER parser.
- oc_models.resolve_config_path() already mirrors OpenCode configuration discovery and deliberately avoids exposing resolved credentials. Extend/reuse read-only discovery rather than forking path rules.
- The current aw setup completion prompt is host-level and TTY-aware. This child creates a reusable wizard; Order 05 decides where setup calls it.
- Repository prompts must be self-contained, default behavior explicit, and EOF/KeyboardInterrupt handled cleanly by the existing CLI boundary.
- The OpenCode CLI documents opencode models as the model inventory command and --variant as provider-specific. The wizard must not pretend every common value works for every model.

## Findings

| Risk | Superficial implementation | Required falsifier |
|---|---|---|
| Huge model catalog | Dump every model and ask for a number. | Filter/paging tests with hundreds of entries. |
| Private model missing from catalog | Refuse profile creation. | Manual exact-ID path succeeds after discovery failure. |
| Variant support unknown | Claim a selected value is supported. | UI labels it provider-specific and preserves exact manual choice. |
| Duplicate alias | Silently overwrite. | Existing bytes unchanged without --replace. |
| Default side effect | First profile automatically becomes default. | Both default questions are separate and default No. |
| Shell/config exposure | Build a shell string or print provider credentials. | argv-list mock and redaction assertions. |

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

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste focused tests showing the exact opencode models argv with shell=False and timeout; ANSI/noise normalization; exact provider/model filtering; deterministic dedupe; config fallback without secret resolution; and distinct missing/timeout/nonzero/malformed/empty diagnostics. Include a negative assertion that neither --refresh nor a write flag is issued.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste scripted interview transcripts/tests for small and 200-entry filtered/paged catalogs, exact manual fallback, provider-default/common/custom variants, exact preview, invalid retry, cancel/empty/EOF/interrupt, and discovery unavailable. Show every non-save path leaves the config absent or byte-identical.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste CLI help and focused add/list/show/remove/default tests for interactive and fully noninteractive forms, JSON/agent-safe output, duplicate refusal, explicit replace, remove-default integrity, clear-default, non-TTY incomplete refusal, exact exit codes, and proof existing aw oc run/update-models routing remains unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste tests showing the save, OpenCode-default, and global-default questions are separate and default No; all accepted changes land in one atomic write; declining either preserves its previous value; first/existing-profile cases behave identically; and Configure another profile is invoked only by an explicit interactive session.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Paste the complete focused-suite command, exit code, and summary with test names covering every interaction/error branch. Include byte comparisons for cancelled/failed/default-No flows and captured output searched for sentinel credentials to prove none were printed.
  - Observed evidence:
  - Result: pending


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
