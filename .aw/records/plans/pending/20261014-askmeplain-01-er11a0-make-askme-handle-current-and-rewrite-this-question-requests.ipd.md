# IPD: Make /askme handle current and rewrite-this-question requests, and install plain-language communication as a shared default

- Date: 2026-10-14
- Kind: child
- Concern: `/askme` is documented and generated only as an artifact-scanning command (its manifest `arg-hint` says arguments are "the artifact whose open questions to ask about"), so a maintainer's ordinary use, "/askme that question again" after an unintelligible question, has no defined behavior; the workflow body mixes active rules with dated incident history and internal vocabulary; and the general plain-language requirement lives only inside `/askme` and P12 instead of being a default every agent turn receives. Source: adopted external review research `y0vcm9`.
- Scope: Replace `.aw/system/workflows/askme/askme.md` with a procedure-only workflow that recognizes four request scopes (rewrite the previous question, ask a supplied question, examine named records, use the current conversation); move its historical rationale to a sibling `rationale.md`; update the `askme` manifest row (description + arg-hint), the index paragraph and README; make `engine.shim_body` emit a supported-alias note instead of the deprecation note for `askme` only; add an inline-request rule to `engine.agents_pointer_prose` and align its "Ask self-contained questions" paragraph; extend `reporting_contract._CONTRACT` with a communication (plain language, necessary context) section and a decision-question exception to the word cap; revise GUIDING_PRINCIPLES P12 and clarify P13; regenerate the two `askme` shims and this repo's `AGENTS.md` managed block from the generator functions (NOT via `aw install .`, which is measured unsafe and ineffective in this checkout, see E-07); add outcome tests; record DECISIONS and CHANGELOG entries; note the relocation on spec `6kwd2e`. DOES NOT change the deprecation note for any other command, the shim pointer line, `ipd_lint` behavior, or runner behavior.
- Scope-Paths: .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, .aw/system/workflows/askme/README.md, .aw/system/workflows/index.md, .opencode/commands/askme.md, .claude/commands/askme.md, agent_workflows/engine.py, agent_workflows/reporting_contract.py, agent_workflows/migration_inventory.py, docs/reporting-contract.md, GUIDING_PRINCIPLES.md, AGENTS.md, README.md, DECISIONS.md, CHANGELOG.md, tests/test_askme_command_delivery.py, .aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md, .aw/records/plans/pending/20261014-askmeplain-01-er11a0-make-askme-handle-current-and-rewrite-this-question-requests.ipd.md
- Item-Dependencies: none
- Status: approved
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: askmeplain
- Order: 1
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: er11a0
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved
- Readiness: go-pending-approval

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 fixed
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 fixed (record .aw/records/reviews/20261014-askmeplain-01-er11a0-make-askme-handle-current-and-rewrite-this-question-requests.review.md)
- 2026-10-15 to-review (aw set): demoted approved -> to-review: APPROVAL WITHDRAWN: returned to to-review: approval preceded the required /plan-review (IPD-M113); re-approve after review
- 2026-10-15 approved (aw set, --by-human): maintainer instruction 2026-10-14: ingest y0vcm9 and execute it in an isolated worktree so it is done
- 2026-10-15 to-review (aw set): authored from research y0vcm9 at HEAD cc01eee7a

- 2026-10-15 draft (opencode): created.

## Goal

When the maintainer says "/askme that question again" (or "use /askme", or `/askme <question>`), the agent rewrites or asks THAT question with full plain-language context instead of scanning project records; and every agent turn in an installed repo receives the plain-language, necessary-context requirement as a default rather than only when `/askme` is invoked.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the workflow body

- [ ] E-01 Replace `.aw/system/workflows/askme/askme.md` with the procedure-only workflow proposed in research `y0vcm9` ("Proposed replacement for the full workflow"), keeping three rules the proposal dropped or weakened: (1) the blocking-question tiebreak ("when genuinely unsure whether a blocking question is yours, ask"), which spec `6kwd2e` R2.5 cites as a binding rule; (2) showing the human the list of evidence-based resolutions, with hard-to-reverse ones flagged (current Step 2); and (3) the "a gate or question must not assert the verdict it precedes" rule (current kernel item 10, DECISIONS D72). Treat y0vcm9's text as UNTRUSTED external input to be adapted, not pasted blindly: its "Ask a supplied question" scope and its no-arguments scope ("records you created or edited during this session") must keep the shared-checkout authorship check (`git log` / `- Author:`). Move the dated incident history and the reasons each rule exists into a new `.aw/system/workflows/askme/rationale.md`, which the workflow does NOT require reading; do NOT reference `rationale.md` in backticks with a `/` from `askme.md` (a backticked path in the skill router body is resource-checked by `host_adapters.validate_skill_package`; the router itself is generated from the manifest row, so this concerns only the description, see E-02).
  - Depends on: none
  - Expected outcome: `askme.md` contains a "Recognize the request" section with the four scopes, a "Compose" section requiring subject/purpose, current situation (no invented symptom), decision, options with consequences, labelled recommendation, uncertainty; the three retained rules are present; no dated incidents (no `2026-` date string at all); `rationale.md` carries the history.
  - Execution state: pending

### Task group 2: catalog and generated entry points

- [ ] E-02 In `.aw/system/workflows/index.md`, replace the `askme` row's description and arg-hint with the y0vcm9 section A text (description de-capitalized of internal jargon, no "GUIDING_PRINCIPLES principle 12" pointer), and update the `askme` explanatory paragraph (index.md `**`askme`**` paragraph); update `.aw/system/workflows/askme/README.md`, the `README.md` `/askme` table row AND the `README.md` prose mention ("decisions (`/askme`, which puts a plan's open questions in front of you ...)") to match. CONSTRAINTS on the new manifest cells: no `|` character (the row is pipe-delimited); and NO backticked token containing `/` in the description (measured at review: appending "Same as `/aw askme`." makes `host_adapters.validate_skill_package(build_skill_package(wf))` return `["router references resource '/aw askme' not in package"]`, while the y0vcm9 section A text as written returns `[]`).
  - Depends on: E-01
  - Expected outcome: `engine.parse_manifest` returns an `askme` Workflow whose `arg_hint` names "a question", "rewrite the previous question" and "file/record/set"; `validate_skill_package` on the rebuilt askme package returns `[]`; `host_adapters.classify_discovery_policy` still returns `skill_entry_point` for askme.
  - Execution state: pending
- [ ] E-03 In `engine.shim_body`, emit for `command == "askme"` a single-line `<!-- Supported alias: ... -->` comment (stating `/askme` and `/aw askme` are equivalent and the alias is retained) instead of the deprecation notice; every other command keeps the existing deprecation notice byte-for-byte. Keep it ONE line beginning `<!--` so `engine.is_stale_shim_customized` (allowlist prefix `"<!--"`) still recognizes it as installer-owned; a wrapped multi-line comment would make the continuation line read as a user customization.
  - Depends on: none
  - Expected outcome: `shim_body("askme", ...)` contains no "Deprecation notice" and contains "Supported alias"; `shim_body("handoff", ...)` still does contain the deprecation notice byte-for-byte; `is_stale_shim_customized(shim_body("askme", ...))` is `False` for both tools.
  - Execution state: pending

### Task group 3: always-loaded instructions

- [ ] E-04 In `engine.agents_pointer_prose`, add an inline-request rule (under the "Guidelines for Antigravity & Other Agents" list) built from `workflows_dir`, telling the agent that "use /askme", "/askme that question again", "ask that again using /askme" or `/aw askme` means read and apply `{workflows_dir}/askme/askme.md`, and that "again" means rewrite the indicated question with full context, not scan unrelated records or repeat the wording. Replace "keep it screen-sized" in the "Ask self-contained questions" paragraph with "prefer short wording, but never omit information needed for an informed answer to meet a screen-size or word target". The pointer prose is installed into EVERY managed repo, so it must stay target-neutral: do not name `GUIDING_PRINCIPLES`, `pyproject.toml` or other AW-only tokens (pinned by `tests/test_agents_block_target_neutral.py` and `tests/test_suite_instruction_marker_parity.py`).
  - Depends on: E-01
  - Expected outcome: `agents_pointer_prose("aw")` names `.aw/system/workflows/askme/askme.md`; `agents_pointer_prose("legacy")` names `.agents/workflows/askme/askme.md`; neither contains "keep it screen-sized".
  - Execution state: pending
- [ ] E-05 Extend `reporting_contract._CONTRACT` (same slug `reporting`, same functions) with a COMMUNICATION paragraph (clear, concise, plain, precise, accurate, straightforward, jargon-free; applies to every response, question, progress update, plan, spec, research prompt and other authored document, internal ones included; never use an identifier, filename, acronym or link as a substitute for explaining the subject) and a DECISIONS paragraph (the routine word cap does not limit decision questions, recommendations or explanations needed to understand; repeat relevant context when the reader needs it; remove wording, not information). Retitle the section `## Communication and concise reporting` by changing `REPORTING_SECTION_TITLE` (the only test consumer, `tests/test_defect_report.py::test_prompt_integration_and_format`, reads it through that constant). Keep the slug `reporting`, `POINTER_TARGET`, `shim_pointer_line()` and `prompt_block()` unchanged. Update the module docstring (which today scopes the contract to "model-authored USER-FACING prose") and `docs/reporting-contract.md` (title and scope fence) to describe the expanded scope. The contract is appended as the LAST element of both driver prompts, so keep it compact: add the two paragraphs, do not restate y0vcm9's whole rationale.
  - Depends on: none
  - Expected outcome: `contract_text()` starts with the new title and contains both paragraphs; PRECEDENCE and COMPLETENESS paragraphs retained; ASCII only; `ROUTINE_FINAL_WORD_CAP` still referenced.
  - Execution state: pending
- [ ] E-06 Revise `GUIDING_PRINCIPLES.md` P12 per y0vcm9 section D (general requirement, no screen-size constraint, no dated account of the moved checklist, keep the do-not-repeat-the-options rule, point to `askme` for procedure). P12's current closing paragraph says the self-check list lives in "the `askme` memory kernel"; since E-01 removes the memory kernel, that pointer must be rewritten to the new "Check before sending" section (or dropped), not left dangling. Keep the D151 pointer sentence (why `aw ipd lint` refuses an open blocking question). Add the y0vcm9 section E paragraph to P13.
  - Depends on: E-01
  - Expected outcome: P12 no longer says "fit comfortably on a terminal screen" and no longer mentions a "memory kernel"; P13 states the style exception does not exempt clarity, precision, accuracy, plain language or necessary context.
  - Execution state: pending

### Task group 4: regeneration, tests, records

- [ ] E-07 Add `tests/test_askme_command_delivery.py`: (a) render both hosts' `askme` shims from the real manifest for both layouts and assert they reference the same workflow body, carry the manifest's arg-hint, carry no deprecation notice, while another command's shim still does; (b) assert `agents_pointer_prose` for both layouts names the layout's `askme/askme.md`; (c) run the installer into a temporary repo and assert both `askme.md` shims are installed and that `AGENTS.md` contains `contract_text()` verbatim and the askme path; (d) re-run the installer and assert the askme shims are unchanged and not reported as customized (no `[preserved]` tag and no "has manual modifications" warning for them). Use `engine.install_into_repo(repo, source_root, yes=True, no_color=True)` against a fresh `tests.support.init_repo` temp repo, as `tests/test_installer.py` does; mark the installer cases `pytest.mark.slow` if they exceed the fast-suite budget (the existing installer tests are `slow`), and say in V-07 which marker they carry and run them explicitly.
  THEN REGENERATE THIS REPO'S DERIVED FILES FROM THE GENERATOR FUNCTIONS, NOT WITH `aw install .`. Measured at review (throwaway clone at `d78f642c2`, generator edited to inject marker strings, then `python3 -m agent_workflows install . --no-interactive --yes --source .`): the install (1) printed "Warning: AGENTS.md#aw:pointer has manual modifications; kept your version, the regenerated section was NOT applied", because the recorded `AGENTS.md#aw:pointer` hash in `.aw/system/managed-sections.json` does not match the on-disk body even though the body equals `agents_pointer_prose("aw")` verbatim, so the E-04 text would NOT reach `AGENTS.md`; (2) APPENDED a whole new 124-line managed block to `GEMINI.md`, which carries none today; (3) touched 104 files (about 90 new `.agents/skills/` files, `.aw/config/project.json`, `.aw/system/VERSION`, `.gitignore`, `.aw/records/{releases,reviews}/.gitkeep`, an 898-line `managed-sections.json` rewrite); and (4) CREATED ITS OWN COMMIT "agent-workflows: sync via installer". (The same hazard is recorded in executed plan `diof9n` F-13.) Instead, in the worktree run a short `python3 -c` script that: writes `engine.generate_shim_members(engine.parse_manifest(Path(".aw/system/workflows")), Path(".aw/system/workflows"), target_layout="aw")[rel]` to each of `.opencode/commands/askme.md` and `.claude/commands/askme.md`; and replaces the text from `<!-- aw:block -->` through `<!-- /aw:block -->` in `AGENTS.md` with `engine.agents_managed_block(target_layout="aw")` (rstrip the trailing newline), leaving every byte outside the markers unchanged. Demonstrated at review on the same clone: that script changed exactly 3 files (`.claude/commands/askme.md` 4 lines, `.opencode/commands/askme.md` 2 lines, `AGENTS.md` 6 lines) and afterwards `agents_managed_block("aw").strip() in AGENTS.md` was `True`. Do NOT edit `GEMINI.md` or `.aw/system/managed-sections.json` (neither is in Scope-Paths any more; re-syncing the recorded hash is the separate installer defect that E-09 files).
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; `git diff --name-only` for the regeneration step lists exactly `.opencode/commands/askme.md`, `.claude/commands/askme.md` and `AGENTS.md`; `AGENTS.md` contains `engine.agents_managed_block(target_layout="aw")` verbatim and its repo-local text below `<!-- /aw:block -->` is byte-identical to HEAD; no installer commit was created.
  - Execution state: pending
- [ ] E-08 Record a `DECISIONS.md` entry numbered one past the highest existing `### D<n>` at execution time (D169 at review, when the highest was D168; re-derive, another plan may land first) covering: askme alias retained as supported; communication requirement made a shared default; history moved out of the executable body. Add a `CHANGELOG.md` entry under 2.0.0 (pending). Update the stale comments in `agent_workflows/migration_inventory.py` (both the `_COMMAND_FAMILY["askme"]` comment, "it stops asking and records a deferral instead", and the `_FAMILY_DEFAULTS["askme"]` comment, "it records the decision as deferred and says so") to match the new noninteractive branch, which keeps genuine human decisions OPEN and blocking rather than deferring them; change comments only, no values. Append an `aw specs note` to spec `6kwd2e` stating that the rules it cites as `askme` Step 1 (three-way sort), Step 3/Step 4 (record before the next question, durable recording) and Step 5 (runner branch) now live in the "Establish facts before asking", "Ask and wait", "Record project decisions" and "Explicitly noninteractive runs" sections, and that its `askme.md:NNN` line citations predate this rewrite.
  - Depends on: E-01
  - Expected outcome: the new D-entry present; CHANGELOG entry present with no em/en dashes; both migration_inventory comments updated and `python3 -c "from agent_workflows import migration_inventory"` still imports; spec `6kwd2e` history carries the note.
  - Execution state: pending
- [ ] E-09 File the installer defect E-07 works around with `aw backlog new` (`--work-kind bug`, `--priority` of your judgement, and `--blocks-release next` per the every-live-bug-gates-the-release rule): in this repository `aw install .` reports `AGENTS.md#aw:pointer` as manually modified and does NOT apply the regenerated pointer, although the on-disk section equals `engine.agents_pointer_prose("aw")` verbatim, because the hash recorded in `.aw/system/managed-sections.json` matches neither. This is the same symptom closed `done` in backlog `krwl3t` (plan `b4bvas`), so cite both and state it recurred. Do NOT fix the installer in this plan. Then replace `- Carrier: er11a0` (this plan, which owns filing it) in the `## Deferred / out of scope` row for it with `- Carrier: <new backlog id6>`.
  - Depends on: E-07
  - Expected outcome: a new open backlog item exists under `.aw/records/backlog/open/` carrying `- Work-Kind: bug` and `- Blocks-Release: next`, citing `krwl3t` and this plan; the deferral row names its id6 as `- Carrier:`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Shims are GENERATED by `engine.shim_body` from the manifest row (`engine.parse_manifest(Path(".aw/system/workflows"))` reads `index.md` columns `command | body | lens | description | arg-hint`; note the argument is the workflows dir, not `.aw/system`); CONTRIBUTING.md "Regenerating Derivative Artifacts": "Never hand-edit generated files ... `aw install .`". In THIS checkout `aw install .` is not usable for that (E-07), so the files are regenerated by calling the same generator functions the installer calls, which keeps them generator output rather than hand edits.
- The askme manifest row is also the input of the generated Agent Skill package (`host_adapters.build_skill_package`, policy `skill_entry_point` because the row has an `arg-hint`): its description becomes the SKILL.md trigger text and its semantic digest, so changing it changes the shipped skill; `validate_skill_package` must stay `[]`.
- `GEMINI.md` in this repo carries NO managed block today (only repo-local Antigravity rules); `engine.agents_managed_sections` text reaches it only if an install appends one, which this plan does not do.
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
| F-9 | `aw install .` cannot deliver the regenerated managed text to this repo's `AGENTS.md` and has large side effects (appends a block to `GEMINI.md`, ~100 unrelated files, its own commit) | review probe, see E-07; recorded hazard in executed plan `diof9n` F-13; recurrence of backlog `krwl3t` |

## Proposed changes (ordered, validatable)

E-01 through E-09 in order; each is validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Live interactive trials per host/model (y0vcm9 "Actual questions produced by agents"): a maintainer activity requiring a human answering prompts; not reproducible in an unattended execution. Recorded as not run.
  - Carrier: jymlaw
- Changing the shim pointer line or other commands' deprecation notices: separate decisions, not requested.
  - Carrier-Declined: not an obligation; no one asked for it and the current behavior for other commands is intended.
- Fixing the installer so `aw install .` applies a regenerated `AGENTS.md#aw:pointer` in this repo (stale recorded section hash; recurrence of `krwl3t`): an installer consent-semantics change affecting every managed repo, outside this plan. Filed by E-09.
  - Carrier: er11a0
- Adding a managed block to this repo's `GEMINI.md`: it carries none today, and adding one is a separate decision about that file's role, not part of this fix.
  - Carrier-Declined: not requested; this repo's `GEMINI.md` is deliberately repo-local Antigravity rules.

## Scope check

- Over-scope: none.
- Under-scope: none after review; `rationale.md` is installed with the bundle but not referenced in backticks by the router body, so `host_adapters.validate_skill_package` resource checks are unaffected. The plan file itself is in Scope-Paths because E-09 writes the carrier id6 back into it.

## Required tests / validation

`python3 -m pytest tests/test_askme_command_delivery.py -o addopts=""` (add `-m ""` if any case is marked `slow`), `python3 -m pytest tests/test_defect_report.py tests/test_installer.py tests/test_agents_block_target_neutral.py tests/test_suite_instruction_marker_parity.py tests/test_agy_skill_install.py -o addopts="" -m ""` (the existing shim, pointer, contract and skill-package suites this plan can break, several of them `slow` and so absent from the bare run), then the bare suite `python3 -m pytest`, plus `aw ipd lint`, `aw check all` and `aw sanitize --agent`. `aw check all` exits 1 at review baseline (`findings 147: error 22, warning 4, info 121`, none from this plan), so the bar is NO NEW finding attributable to this plan's paths, not exit 0.

## Spec / documentation sync

Spec `6kwd2e` receives a history note only (E-08), because its R2.5 rule (classify before escalating, measure before asking, a lean is not a decision, ask when unsure on a blocking question) is preserved in the new workflow; only the location and line citations change. The plan therefore does NOT edit the spec body; `aw specs note` appends to its `## Workflow history`, which is why the spec path is in Scope-Paths. Docs: `docs/reporting-contract.md`, askme README, `README.md` table row and prose mention, `index.md` paragraph, `GUIDING_PRINCIPLES.md` P12/P13.

## Open questions

### OQ-01: Retitle the reporting section?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: Resolved from evidence 2026-10-14: section identity is the `aw:reporting` slug, and the only consumer of the title (`tests/test_defect_report.py`) reads it through `REPORTING_SECTION_TITLE`, so retitling to reflect the broader scope is safe.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `grep -n "^## " .aw/system/workflows/askme/askme.md` showing the new section list including "Recognize the request"; pasted `grep -c "2026-" .aw/system/workflows/askme/askme.md` returning 0; pasted `grep -n "^## " .aw/system/workflows/askme/rationale.md`; and the three retained rules QUOTED from the new `askme.md` with line numbers (blocking-question tiebreak, list of self-resolved decisions with hard-to-reverse flagged, no verdict asserted before the human answers), plus the authorship-check sentence for the session-records scope.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -c` calling `engine.parse_manifest(Path(".aw/system/workflows"))` and printing the askme `description` and `arg_hint`, then printing `host_adapters.validate_skill_package(host_adapters.build_skill_package(wf))` (must be `[]`) and `host_adapters.classify_discovery_policy(wf)`; plus pasted `git diff` of the askme README, the `README.md` row and prose mention, and the `index.md` paragraph.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted passing output of the E-07 test case(s) asserting the askme shim (both tools) carries "Supported alias" and no "Deprecation notice", another command's shim still carries the deprecation notice, and `is_stale_shim_customized` is `False` on the askme shim; plus the passing `tests/test_installer.py::ShimArgumentHintTests` run (`-o addopts="" -m ""`).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output of the E-07 pointer-prose test passing for both layouts (path present, "keep it screen-sized" absent), and passing runs of `tests/test_agents_block_target_neutral.py` and `tests/test_suite_instruction_marker_parity.py` with `-o addopts="" -m ""`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -c "from agent_workflows import reporting_contract as r; t=r.contract_text(); print(t.splitlines()[0]); print(t.isascii())"` and the passing `tests/test_defect_report.py` run (driver prompts still end with the contract).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted `grep -n "terminal screen\|memory kernel" GUIDING_PRINCIPLES.md` returning nothing, the new P12 text and the P13 added paragraph quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `python3 -m pytest tests/test_askme_command_delivery.py -o addopts="" -m ""` output naming the cases for (a)-(d), and which marker the installer cases carry; the regeneration script as run; pasted `git diff --stat` and `git diff --name-only` taken immediately after the regeneration script (exactly the two askme shims and `AGENTS.md`); pasted `python3 -c` printing `engine.agents_managed_block(target_layout="aw").strip() in open("AGENTS.md").read()` as `True`; pasted `git diff HEAD -- AGENTS.md` showing changes only between the `aw:block` markers; pasted `git log --oneline` showing no "agent-workflows: sync via installer" commit; and the bare `python3 -m pytest` summary line plus the explicit `-m ""` run of the suites listed in Required tests.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted `grep -n "^### D1[6-9][0-9]" DECISIONS.md | tail -3` showing the new entry is the highest; the CHANGELOG entry quoted; `git diff agent_workflows/migration_inventory.py` showing comment-only changes; the `6kwd2e` history line quoted; and `aw check all --agent` output with `findings_by_severity` compared against the review baseline (`error 22, warning 4, info 121`), naming any finding on a path this plan changed.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: the pasted `aw backlog new` command and its output (new id6), the new item's front matter quoted (`- Work-Kind: bug`, `- Blocks-Release: next`), and the updated `- Carrier:` line in this plan's deferral row quoted.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

The maintainer instructed on 2026-10-14 to ingest research `y0vcm9` and execute it in an isolated worktree so it is done. That approval was WITHDRAWN on 2026-10-15 because it preceded this review (IPD-M113, see Workflow history); execute only after the plan is re-approved (`aw ipd set approved er11a0 --by-human -m ...`) or dispatched by an authorized runner turn. OQ-01 is resolved and no question blocks. This plan carries `- Blocks-Release: next`.

Begin: by hand, `aw work begin er11a0` (validates and allocates an isolated worktree); under `aw oc run` / `aw agy run` the runner provides the worktree. Never edit in the primary checkout, and never run `aw install .` there or in the worktree (E-07).

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`, and a declared path left unmodified is acknowledged with `--scope-ack`. STOP only for a genuinely unsafe condition: a concurrent edit to `engine.py`, `reporting_contract.py` or `AGENTS.md` that cannot be safely combined.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run.

Commits: commit only the files you changed through `aw commit er11a0 -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, run `aw ipd finalize er11a0` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
