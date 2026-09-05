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
| Sequencing against an approved plan | FOUND AT REVIEW (PR-001, BLOCKER): APPROVED `0soncw` is RETIRING the `aw run` noun this plan builds on (its E-05 leaves a nonzero-exit deprecation stub), and no plan in this Set mentions it. They are complementary, not contradictory: `0soncw` frees the name "for a future driver verb", which is this Set. Escalated as blocking OQ-01 on the orchestrator `3m0urk`; recommended order is `0soncw` FIRST, then this Set. Do NOT execute this plan until that order is settled. | Settle orchestrator OQ-01 before executing. |
| Unverifiable "already" claims | FOUND AT REVIEW (PR-002): this plan carries ZERO `file:line` citations, as does every member of this Set (measured: 0 across all six, versus 9/4/5 in the comparable `6lu3rq`/`m73aet`/`wlxkoz` plans). The claims spot-checked at review were TRUE, so this is evidence discipline rather than incorrectness, but an executor cannot cheaply re-verify a premise. MEASURE and cite `file:line` for every "already" claim before relying on it; HEAD moves hourly here. | Cite `file:line` for each, measured at the current HEAD. |

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
