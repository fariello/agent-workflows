# IPD: Make /askme handle current and rewrite-this-question requests, and install plain-language communication as a shared default

- Date: 2026-10-14
- Kind: child
- Concern: `/askme` is documented and generated only as an artifact-scanning command (its manifest `arg-hint` says arguments are "the artifact whose open questions to ask about"), so a maintainer's ordinary use, "/askme that question again" after an unintelligible question, has no defined behavior; the workflow body mixes active rules with dated incident history and internal vocabulary; and the general plain-language requirement lives only inside `/askme` and P12 instead of being a default every agent turn receives. Source: adopted external review research `y0vcm9`.
- Scope: Replace `.aw/system/workflows/askme/askme.md` with a procedure-only workflow that recognizes four request scopes (rewrite the previous question, ask a supplied question, examine named records, use the current conversation); move its historical rationale to a sibling `rationale.md`; update the `askme` manifest row (description + arg-hint), the index paragraph and README; make `engine.shim_body` emit a supported-alias note instead of the deprecation note for `askme` only; add an inline-request rule to `engine.agents_pointer_prose` and align its "Ask self-contained questions" paragraph; extend `reporting_contract._CONTRACT` with a communication (plain language, necessary context) section and a decision-question exception to the word cap; revise GUIDING_PRINCIPLES P12 and clarify P13; regenerate shims and this repo's managed `AGENTS.md`/`GEMINI.md` sections via `aw install .`; add outcome tests; record DECISIONS and CHANGELOG entries; note the relocation on spec `6kwd2e`. DOES NOT change the deprecation note for any other command, the shim pointer line, `ipd_lint` behavior, or runner behavior.
- Scope-Paths: .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, .aw/system/workflows/askme/README.md, .aw/system/workflows/index.md, .opencode/commands/askme.md, .claude/commands/askme.md, agent_workflows/engine.py, agent_workflows/reporting_contract.py, agent_workflows/migration_inventory.py, docs/reporting-contract.md, GUIDING_PRINCIPLES.md, AGENTS.md, GEMINI.md, README.md, DECISIONS.md, CHANGELOG.md, tests/test_askme_command_delivery.py, .aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md, .aw/system/managed-sections.json
- Item-Dependencies: none
- Status: approved
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: askmeplain
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: er11a0
- Approval: 2026-10-15, human ("approved"): maintainer instruction 2026-10-14: ingest y0vcm9 and execute it in an isolated worktree so it is done

## Workflow history
- 2026-10-15 approved (aw set, --by-human): maintainer instruction 2026-10-14: ingest y0vcm9 and execute it in an isolated worktree so it is done
- 2026-10-15 to-review (aw set): authored from research y0vcm9 at HEAD cc01eee7a

- 2026-10-15 draft (opencode): created.

## Goal

When the maintainer says "/askme that question again" (or "use /askme", or `/askme <question>`), the agent rewrites or asks THAT question with full plain-language context instead of scanning project records; and every agent turn in an installed repo receives the plain-language, necessary-context requirement as a default rather than only when `/askme` is invoked.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the workflow body

- [ ] E-01 Replace `.aw/system/workflows/askme/askme.md` with the procedure-only workflow proposed in research `y0vcm9` ("Proposed replacement for the full workflow"), keeping two rules the proposal dropped: the blocking-question tiebreak ("when genuinely unsure whether a blocking question is yours, ask") and showing the human the list of evidence-based resolutions. Move the dated incident history and the reasons each rule exists into a new `.aw/system/workflows/askme/rationale.md`, which the workflow does NOT require reading.
  - Depends on: none
  - Expected outcome: `askme.md` contains a "Recognize the request" section with the four scopes, a "Compose" section requiring subject/purpose, current situation (no invented symptom), decision, options with consequences, labelled recommendation, uncertainty; no dated incidents; `rationale.md` carries the history.
  - Execution state: pending

### Task group 2: catalog and generated entry points

- [ ] E-02 In `.aw/system/workflows/index.md`, replace the `askme` row's description and arg-hint with the y0vcm9 section A text (description de-capitalized of internal jargon, no "GUIDING_PRINCIPLES principle 12" pointer), and update the `askme` explanatory paragraph; update `.aw/system/workflows/askme/README.md` and the `README.md` `/askme` row to match.
  - Depends on: E-01
  - Expected outcome: `engine.parse_manifest` returns an `askme` Workflow whose `arg_hint` names "a question", "rewrite the previous question" and "file/record/set".
  - Execution state: pending
- [ ] E-03 In `engine.shim_body`, emit for `command == "askme"` a `<!-- Supported alias: ... -->` comment (stating `/askme` and `/aw askme` are equivalent and the alias is retained) instead of the deprecation notice; every other command keeps the existing deprecation notice byte-for-byte.
  - Depends on: none
  - Expected outcome: `shim_body("askme", ...)` contains no "Deprecation notice"; `shim_body("handoff", ...)` still does.
  - Execution state: pending

### Task group 3: always-loaded instructions

- [ ] E-04 In `engine.agents_pointer_prose`, add an inline-request rule (under the "Guidelines for Antigravity & Other Agents" list) built from `workflows_dir`, telling the agent that "use /askme", "/askme that question again", "ask that again using /askme" or `/aw askme` means read and apply `{workflows_dir}/askme/askme.md`, and that "again" means rewrite the indicated question with full context, not scan unrelated records or repeat the wording. Replace "keep it screen-sized" in the "Ask self-contained questions" paragraph with "prefer short wording, but never omit information needed for an informed answer to meet a screen-size or word target".
  - Depends on: E-01
  - Expected outcome: `agents_pointer_prose("aw")` names `.aw/system/workflows/askme/askme.md`; `agents_pointer_prose("legacy")` names `.agents/workflows/askme/askme.md`.
  - Execution state: pending
- [ ] E-05 Extend `reporting_contract._CONTRACT` (same slug `reporting`, same functions) with a COMMUNICATION paragraph (clear, concise, plain, precise, accurate, straightforward, jargon-free; applies to every response, question, progress update, plan, spec, research prompt and other authored document, internal ones included; never use an identifier, filename, acronym or link as a substitute for explaining the subject) and a DECISIONS paragraph (the routine word cap does not limit decision questions, recommendations or explanations needed to understand; repeat relevant context when the reader needs it; remove wording, not information). Retitle the section `## Communication and concise reporting`. Update the module docstring and `docs/reporting-contract.md` to describe the expanded scope.
  - Depends on: none
  - Expected outcome: `contract_text()` starts with the new title and contains both paragraphs; PRECEDENCE and COMPLETENESS paragraphs retained; ASCII only.
  - Execution state: pending
- [ ] E-06 Revise `GUIDING_PRINCIPLES.md` P12 per y0vcm9 section D (general requirement, no screen-size constraint, no dated account of the moved checklist, keep the do-not-repeat-the-options rule, point to `askme` for procedure) and add the y0vcm9 section E paragraph to P13.
  - Depends on: E-01
  - Expected outcome: P12 no longer says "fit comfortably on a terminal screen"; P13 states the style exception does not exempt clarity, precision, accuracy, plain language or necessary context.
  - Execution state: pending

### Task group 4: regeneration, tests, records

- [ ] E-07 Add `tests/test_askme_command_delivery.py`: (a) render both hosts' `askme` shims from the real manifest for both layouts and assert they reference the same workflow body, carry the manifest's arg-hint, carry no deprecation notice, while another command's shim still does; (b) assert `agents_pointer_prose` for both layouts names the layout's `askme/askme.md`; (c) run the installer into a temporary repo and assert both `askme.md` shims are installed and that `AGENTS.md` contains `contract_text()` verbatim and the askme path; (d) re-run the installer and assert the askme shims are unchanged and not reported as customized. Then run `aw install .` in the worktree to regenerate `.opencode/commands/askme.md`, `.claude/commands/askme.md` and the managed `AGENTS.md`/`GEMINI.md` sections.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; regenerated files differ from HEAD only in the askme shims and the managed sections.
  - Execution state: pending
- [ ] E-08 Record `DECISIONS.md` D169 (askme alias retained as supported; communication requirement made a shared default; history moved out of the executable body), a `CHANGELOG.md` entry under 2.0.0 (pending), update the stale "records a deferral" comment in `migration_inventory._FAMILY_DEFAULTS["askme"]`, and append an `aw specs note` to spec `6kwd2e` stating the three-way sort it cites as `askme` Step 1 now lives in the "Establish facts before asking" section and its `askme.md:NNN` line citations predate this rewrite.
  - Depends on: E-01
  - Expected outcome: D169 present; CHANGELOG entry present with no em/en dashes; spec `6kwd2e` history carries the note.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Shims are GENERATED by `engine.shim_body` from the manifest row (`engine.parse_manifest` reads `index.md` columns `command | body | lens | description | arg-hint`); CONTRIBUTING.md "Regenerating Derivative Artifacts": "Never hand-edit generated files ... `aw install .`".
- `engine.is_stale_shim_customized` recognizes installer-owned lines by prefix, including the generic `"<!--"` prefix, so a new `<!-- Supported alias:` line is not misread as a user customization.
- The reporting contract is ONE module (`reporting_contract.contract_text`) rendered as the `aw:reporting` managed section by `engine.agents_managed_sections` and embedded in driver prompts via `reporting_contract.prompt_block` (`runner_shared`); `tests/test_defect_report.py` finds it in prompts by `RC.REPORTING_SECTION_TITLE`, so retitling via the constant is safe.
- Shims carry only `reporting_contract.shim_pointer_line()`; the shim pointer is left unchanged so 48 shims are not churned.
- P16: tests must exercise code (render, install) and assert outputs, not grep source.
- Spec `6kwd2e` R2.5 names `askme` Step 1 as the single source of the three-way sort and cites `askme.md` line ranges.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Shims define arguments only as an artifact selector | `index.md` askme row arg-hint "treat them as the artifact whose open questions to ask about (a path, an id6, or a set id)" |
| F-2 | Workflow Step 0 starts by discovering artifacts and reading `## Open questions` | `askme.md` "## Step 0: Discover" |
| F-3 | Body mixes rules with dated incidents and internal vocabulary ("memory kernel", "load-bearing") | `askme.md` "Memory kernel" items 3, 4, 7 |
| F-4 | Kernel item 3 demands a symptom even for a design choice | `askme.md` "IF YOU CANNOT STATE THE SYMPTOM, YOU DO NOT YET UNDERSTAND" |
| F-5 | P12 and the AGENTS pointer cap context at screen size | P12 "Keep the context short enough to fit comfortably on a terminal screen"; `agents_pointer_prose` "keep it screen-sized" |
| F-6 | Human presence keyed to "a real terminal" | `askme.md` Step 0 "An interactive question tool plus a real terminal means yes" |
| F-7 | Every per-workflow shim, askme included, says it "will eventually be pruned" | `engine.shim_body` "Deprecation notice" f-string |
| F-8 | The referenced `agent-communication-instructions.md` does not exist in the repo; the contract text is authored here from y0vcm9's seven-quality definition | `git grep -l agent-communication-instructions` returns nothing |

## Proposed changes (ordered, validatable)

E-01 through E-08 in order; each is validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Live interactive trials per host/model (y0vcm9 "Actual questions produced by agents"): a maintainer activity requiring a human answering prompts; not reproducible in an unattended execution. Recorded as not run.
- Changing the shim pointer line or other commands' deprecation notices: separate decisions, not requested.

## Scope check

- Over-scope: none.
- Under-scope: none; `rationale.md` is installed with the bundle but not referenced in backticks by the router body, so `host_adapters.validate_skill_package` resource checks are unaffected.

## Required tests / validation

`python3 -m pytest tests/test_askme_command_delivery.py -o addopts=""`, then the bare suite `python3 -m pytest`, plus `aw ipd lint`, `aw check all` and `aw sanitize --agent` on the changed files.

## Spec / documentation sync

Spec `6kwd2e` receives a history note only (E-08), because its R2.5 rule (classify before escalating, measure before asking, a lean is not a decision, ask when unsure on a blocking question) is preserved in the new workflow; only the location and line citations change. Docs: `docs/reporting-contract.md`, askme README, `README.md` row, `index.md` paragraph.

## Open questions

### OQ-01: Retitle the reporting section?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: Resolved from evidence 2026-10-14: section identity is the `aw:reporting` slug, and the only consumer of the title (`tests/test_defect_report.py`) reads it through `REPORTING_SECTION_TITLE`, so retitling to reflect the broader scope is safe.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `grep -n "^## " .aw/system/workflows/askme/askme.md` showing the new section list including "Recognize the request"; pasted `grep -c "2026-09" askme.md` returning 0; pasted `grep -n "^## " rationale.md`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -c` calling `engine.parse_manifest` on the bundle and printing the askme `arg_hint`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted output of the E-07 test case asserting askme lacks and another command keeps the deprecation notice, passing.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output of the E-07 pointer-prose test passing for both layouts.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -c "from agent_workflows import reporting_contract as r; t=r.contract_text(); print(t.splitlines()[0]); print(t.isascii())"` and the passing `tests/test_defect_report.py` run (driver prompts still end with the contract).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted `grep -n "terminal screen" GUIDING_PRINCIPLES.md` returning nothing and the P13 added paragraph quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `python3 -m pytest tests/test_askme_command_delivery.py -o addopts=""` output, pasted `git diff --stat` after `aw install .`, and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted `grep -n "### D169" DECISIONS.md`, the CHANGELOG entry quoted, and the `6kwd2e` history line quoted; `aw check all` exit status pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

The maintainer instructed on 2026-10-14 to ingest research `y0vcm9` and execute it in an isolated worktree so it is done; that instruction is the approval attestation. Begin with `aw work begin er11a0`; commit with `aw commit er11a0 -- <paths>`; never push. Paste ACTUAL output in each `V-*`. STOP only if a concurrent edit to `engine.py`, `reporting_contract.py` or `AGENTS.md` cannot be safely combined.
