RETIRED 2026-08-31: DUPLICATE ID6, and its work had ALREADY LANDED. This file is a second copy of plan `ntf6sx`, whose executed twin is `.aw/records/plans/executed/20260829-terseout-01-ntf6sx-make-coding-agent-reporting-concise-across-opencode-agy-code.ipd.md`. Same `- Id:`, same title, and the two shared an id6, which made `selectors.resolve_for_mutation` refuse `ntf6sx` outright ("a id6 collision matching multiple files (a data bug to fix, not overridable by --force)") and made `aw attention` report VIEW INVALID with `attention.duplicate-id`, so the whole board was non-authoritative. MEASURED CAUSE, not inferred: the twin was finalized to `executed/` at 2026-08-30 20:04:27 (`3558ce1f`), and THIS copy was authored into `pending/` at 23:27:42 (`edac667d`), 3.5 hours LATER, by a different agent (codex gpt-5.6) re-writing a plan whose work had already shipped. That is the shape backlog `k1nity` describes. RESIDUE: none. All five of its E-items were verified already shipped at HEAD `cd09d469`: E-01 `reporting_contract.prompt_block()` exists, E-02 the `aw:reporting` managed section is in `AGENTS.md`, E-03 both drivers call `reporting_contract.prompt_block()` twice each, E-04 `tests/test_reporting_contract.py` exists, E-05 `docs/reporting-contract.md` exists. Retired, not deleted, and NOT filed under `executed/`, because THIS file never ran; its twin did. Filed alongside backlog `wx95o4` (cross-type id6 minting and D140 enforcement) and `h2ceme` (`aw find` must flag a duplicate id6), which cover why nothing prevented or surfaced this at authoring time.

# IPD: Make coding-agent reporting concise across OpenCode, Agy, Codex CLI, and Claude CLI

- Date: 2026-08-29
- Kind: child
- Concern: Coding agents invoked directly or through agent-workflows routinely spend too many tokens on preambles, routine-action narration, praise, recaps, closing offers, and multi-paragraph explanations of simple outcomes. The repository has no portable reporting contract separating concise user-facing communication from complete engineering execution. Host-specific settings cannot solve this consistently because OpenCode, Agy/Antigravity, Codex CLI, and Claude CLI load different instruction surfaces and provider-specific verbosity parameters are inconsistent.
- Scope: Define one host-neutral concise-reporting contract; render it into installed managed instructions and OpenCode/Claude command shims; inject it into OpenCode and Agy IPD-driver execution and verification turns; document precedence and limits; regenerate owned artifacts; and add reachability, parity, no-clobber, and prompt-construction tests. The contract governs conversational progress and final responses, not the completeness of code, tests, IPDs, reports, JSON outcomes, safety warnings, or workflow-required evidence.
- Scope-Paths: agent_workflows/reporting_contract.py, agent_workflows/engine.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/, docs/, README.md, AGENTS.md, .opencode/commands/**, .claude/commands/**, .aw/system/managed-sections.json
- Item-Dependencies: none
- Status: superseded
- Set: terseout
- Order: 1
- Highest E allocated: 05
- Author: codex gpt-5.6
- Id: zi3t8l
- Supersedes-Note: re-identified 2026-08-31 from the duplicated id6 `ntf6sx`, which its EXECUTED twin owns; per DECISIONS.md D140 an id6 is the unique identity of exactly ONE file, so this retired copy carries its own. References to `ntf6sx` in the banner and history below are deliberate REFERENCES to that twin, not this file's identity.

## Workflow history
- 2026-09-01 superseded (aw set): RETIRED: duplicate id6 whose work had already landed. Second copy of ntf6sx; the executed twin finalized at 20:04 (3558ce1f) and this copy was authored at 23:27 (edac667d) by a different agent re-writing already-shipped work. All five E-items verified shipped. The collision made resolve_for_mutation refuse ntf6sx entirely and made aw attention report VIEW INVALID.

- 2026-08-29 to-review (codex gpt-5.6): authored a review-ready cross-host concise-reporting plan from current installer, shim, and runner architecture.
- 2026-08-29 draft (codex gpt-5.6): created.

## Goal

Make concise, essential-information-only user-facing reporting the portable default for agent-workflows across OpenCode, Agy/Antigravity, Codex CLI, and Claude CLI, while preserving full analysis, implementation, testing, evidence, safety, and required deliverables. Reduce reporting verbosity without truncation, weaker work, global user-configuration edits, or reliance on one provider's model options.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: define and distribute one reporting contract

- [ ] E-01 Add `agent_workflows/reporting_contract.py` as the host-neutral source of truth for the exact contract and any compact embedding helper. The contract MUST say: lead with the outcome; begin binary answers with `Yes.` or `No.`; use one sentence when sufficient; omit preambles, praise, request restatement, routine narration, recap, and closing offers; use plain direct language; report only material outcomes, changed files, verification, and blockers; omit empty categories; keep routine finals at or below 100 words; and keep progress to one short sentence only when materially useful. It MUST also say that explicit user or controlling-workflow requirements override the default; required evidence, safety warnings, destructive-action confirmations, structured outcomes, and durable artifacts stay complete; and concision applies to reporting, not analysis, implementation, testing, or correctness.
  - Depends on: none
  - Expected outcome: one importable provider-neutral contract defines the behavior and cannot reasonably be read as permission to perform less work or omit mandatory evidence.
  - Execution state: pending

- [ ] E-02 Render the shared contract as a separately owned managed section such as `aw:reporting` in `AGENTS.md` and existing native files handled by the installer, preserving foreign content and the rule that absent `CLAUDE.md`/`GEMINI.md` files are not created. Put the same contract, or a tested semantically identical compact form derived from the same source, in generated OpenCode and Claude command shims so Claude workflow commands receive it even without a root `CLAUDE.md`. Workflow-specific required output takes precedence: be concise within it, never delete required fields.
  - Depends on: E-01
  - Expected outcome: direct OpenCode and Codex sessions receive the contract through `AGENTS.md`; existing native files receive it without losing user prose; and OpenCode/Claude workflow commands receive it through generated shims.
  - Execution state: pending

- [ ] E-03 Inject the shared contract into execution and independent-verification prompts built by `oc_runipd.py` and `agy_runipd.py`, not manually copied fragments. Ensure review turns receive it through a reliable existing surface without corrupting `/plan-review <path>` parsing. Preserve the required JSON schemas, actual-output evidence, lifecycle instructions, and safety rules.
  - Depends on: E-01
  - Expected outcome: fresh `aw oc run` and `aw agy run` worker/verifier sessions receive the contract even if a host incompletely loads repository instructions, while machine outcomes and evidence retain full schemas.
  - Execution state: pending

### Task group 2: prove portability and prevent drift

- [ ] E-04 Add focused tests for the contract source, managed-section rendering, installer update/idempotence/no-clobber behavior, OpenCode and Claude shim generation, and OpenCode/Agy execution and verifier prompt construction. Prove the completeness safeguards exist, the 100-word default yields to explicit requirements, existing native files preserve foreign prose, absent native files stay absent, and JSON outcome requirements remain unchanged. Add parity assertions so no host surface retains an obsolete hand-copied contract.
  - Depends on: E-02, E-03
  - Expected outcome: deterministic tests fail if a supported host path loses the contract, installer updates damage user content, contract copies drift, or concise reporting weakens required structured output.
  - Execution state: pending

- [ ] E-05 Document the portable default, exact delivery surfaces, explicit-detail override, and why token caps, temperature changes, global home-directory edits, and provider-only fields are not the cross-host mechanism. Regenerate installer-owned `AGENTS.md`, `.opencode/commands/**`, `.claude/commands/**`, and `.aw/system/managed-sections.json` from source, never by hand.
  - Depends on: E-02, E-03
  - Expected outcome: maintainers can identify the source of truth, understand coverage and precedence, and reproduce generated artifacts using the normal installer flow.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows.engine.agents_pointer_prose()` supplies the installer-owned block. `agents_managed_sections()` currently emits one `aw:pointer` section; `update_agents_pointer()` merges it into the selected `AGENTS.md` plus existing `CLAUDE.md`/`GEMINI.md` without creating absent native files (`agent_workflows/engine.py:1037-1215,1389-1415,2283-2375`). A separate `aw:reporting` section fits the ownership model.
- `.opencode/commands/*.md` and `.claude/commands/*.md` come from `shim_body()` and `aw_dispatcher_shim()` (`agent_workflows/engine.py:735-1035`). OpenCode uses `agent: build`; Claude uses `argument-hint`; both use `$ARGUMENTS`. Reporting changes must preserve those grammars.
- `aw oc run` and `aw agy run` build fresh execution and verifier prompts independently (`agent_workflows/oc_runipd.py:1452-1624`; `agent_workflows/agy_runipd.py:1550-1716`). They already embed critical safeguards because fresh workers must not depend only on ambient host behavior.
- OpenCode and Codex consume repository `AGENTS.md`. Claude's generated command shim is the repository-owned workflow surface when no `CLAUDE.md` exists. Agy is covered by its driver prompt. The installer deliberately does not create absent native instruction files (`tests/test_installer.py:661-668`).
- CLI human versus `aw.agent/v1` output already has a separate compact-output contract (`docs/cli-output-contract.md`). This plan governs model-authored conversational prose and must not reduce JSONL fields.
- README's 2.x direction names broader host support and lower token cost. Prompt reachability tests can prove delivery, not perfect compliance by probabilistic models.

## Findings

| Finding | Evidence | Consequence |
| --- | --- | --- |
| No repository-wide concise-reporting rule exists. | Searches find prose-style and CLI-output guidance, but no cross-host conversational contract. | Add an explicit contract instead of relying on model personality or task suffixes. |
| One OpenCode setting cannot cover the requested hosts. | The repository has different OpenCode/Claude shims, OpenCode/Agy prompt builders, and Codex `AGENTS.md` loading. | Use existing portable instruction surfaces. |
| A blunt output-token cap is unsafe. | Lifecycle and verifier prompts require complete JSON, actual runner output, evidence, and blockers. | Use a prose default with explicit exceptions, never truncation. |
| Ambient instructions alone are weaker for fresh runner turns. | Both runners intentionally embed critical rules in full prompts. | Inject the contract into workers and verifiers too. |
| Copying prose across adapters risks drift. | Managed sections, two shim types, and two drivers need the same semantics. | Use one module plus parity tests. |
| Delivery is deterministic; obedience is probabilistic. | Installer and prompt bytes can be asserted; live model output varies and needs credentials. | Gate on reachability/parity; keep live smoke tests optional and honestly reported. |

## Proposed changes (ordered, validatable)

1. Create the shared contract with explicit completeness and precedence safeguards.
2. Add a managed instruction section and render it into native command shims.
3. Add it to both driver worker/verifier prompt families without changing schemas.
4. Add parity, installer-safety, and prompt regression tests.
5. Document the policy and regenerate owned artifacts through supported tooling.

A compliant routine final normally contains only the result, changed files when material, actual verification status, and blockers. It excludes greetings, “I'll…”, praise, narrated searches/reads, restatement, redundant summary, and “let me know if…”. When a workflow requires a long report or pasted evidence, produce it completely and keep surrounding prose concise.

## Deferred / out of scope (with reason)

- Global files such as `~/.config/opencode/AGENTS.md`, `~/.claude/CLAUDE.md`, or Codex home configuration: repository installation must not overwrite personal cross-project preferences.
- Provider fields such as OpenAI `textVerbosity`, temperature, or Claude output-style selection: not portable across all four hosts.
- Low output-token limits or truncation: may cut off errors, evidence, or JSON.
- Changes to reasoning effort, tool calls, steps, test scope, implementation depth, or verifier rigor: concision applies only to reporting.
- `aw` CLI human/JSONL redesign: already governed separately.
- Mandatory live-model CI: credentials, network, cost, version drift, and probabilism make it nondeterministic. A maintainer may run the smoke matrix.
- Creating missing `CLAUDE.md`/`GEMINI.md`: generated Claude shims provide workflow coverage and the installer intentionally avoids creating native files merely for managed prose.

## Scope check

- Over-scope: no global configuration, provider tuning, truncation, CLI redesign, or reduced execution/testing.
- Under-scope: OpenCode is covered by `AGENTS.md`, shims, and `aw oc run`; Agy by `aw agy run`; Codex CLI by `AGENTS.md`; Claude CLI by generated commands and existing `CLAUDE.md` when present. Ad hoc Claude sessions with no `CLAUDE.md` and no agent-workflows command remain outside the product's invocation surface.

## Required tests / validation

- Unit tests for the canonical contract and every safeguard.
- Installer tests for fresh install, update, idempotence, separate managed-section ownership, foreign-prose preservation, and no creation of absent native files.
- Shim tests for OpenCode and Claude frontmatter and `$ARGUMENTS` semantics.
- Prompt tests for OpenCode/Agy workers and verifiers, plus review reachability without slash-command corruption.
- Parity tests proving all embedded surfaces derive from or match the source.
- Regression assertions for JSON outcome fields, evidence requirements, and lifecycle rules.
- Existing generation/no-drift check for `AGENTS.md`, shims, and manifest.
- `python3 -m pytest -p no:randomly`.
- `aw sanitize --agent`.
- Optional live smoke matrix when CLIs and credentials exist: one trivial yes/no query and completed-change task through OpenCode, `aw oc run`, `aw agy run`, Codex CLI, and a Claude command. Record directness, narration, applicable 100-word limit, and preserved evidence. Unavailable hosts are `not run`, never `pass`.

## Spec / documentation sync

- Add a concise section to the appropriate README/docs page describing the default, override, and host coverage.
- Identify the contract source and distinguish model prose from CLI output modes.
- Add a decision/spec pointer if current conventions require one; do not duplicate the contract.
- Regenerate all owned adapters and manifest bytes.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted focused-test output showing the module imports and the exact contract contains every brevity rule plus exceptions for requested/required detail, evidence, safety, structured outcomes, durable artifacts, and full execution/testing. Include a source search showing no second independently maintained full production contract.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Pasted focused installer/shim test output proving: installed `AGENTS.md` contains exactly one separately marked reporting section; existing `CLAUDE.md` and `GEMINI.md` receive it while byte-preserving foreign prose; absent native files remain absent; a second install is byte-idempotent; generated OpenCode and Claude shims retain valid host-specific frontmatter and `$ARGUMENTS`; and deliberately changing one rendered copy makes the parity test fail.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Pasted OpenCode/Agy prompt-builder test output proving the contract appears in every execution and verifier prompt from both drivers; review prompts still resolve exactly one `/plan-review <path>` without treating prose as path arguments; and required JSON keys, actual-output requirements, lifecycle rules, and `pushed: false` remain present. Include a parity assertion showing both drivers import the shared source.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Pasted output from the complete focused regression set naming tests for foreign-content preservation, absent-native behavior, idempotence, override/completeness semantics, schema preservation, and parity. Also paste a negative test demonstrating that removal of a required safeguard or host embedding is detected through a fixture or controlled mock.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Pasted `git diff --check`; the normal generated-artifact/no-drift check showing `AGENTS.md`, OpenCode/Claude shims, and `.aw/system/managed-sections.json` match generators; a search showing docs point to `agent_workflows/reporting_contract.py` without forking its prose; `python3 -m pytest -p no:randomly` with exit 0 and actual summary; and `aw sanitize --agent` clean. If live smokes run, paste host/model/version and measured response shape; otherwise state `not run` without weakening deterministic acceptance.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one cohesive concern, portable concise reporting, implemented through existing managed-instruction, shim, and driver-prompt adapters.

Execution contract:

1. Human approval is required. There are no unresolved questions.
2. Scope fence: touch only `Scope-Paths`. Preserve foreign instruction content and generated ownership. Do not add global writes, provider tuning, truncation, or reduced work. If another production area is needed, STOP and report.
3. Semantics fence: concise governs user-facing progress and final prose. It MUST NOT omit code, documents, IPDs, JSON, safety, confirmations, test output, evidence, blockers, or workflow fields. Explicit user/workflow requirements override 100 words; remain concise within them.
4. Host fence: retain OpenCode `agent: build`, Claude-compatible frontmatter, `$ARGUMENTS`, Codex `AGENTS.md`, and Agy lifecycle/outcome behavior.
5. Honesty: reachability tests do not guarantee model obedience. Live smokes must record actual host/model/version/output; unavailable means `not run`.
6. Validation: run focused tests, full suite, generation/no-drift, and leak sanitizer. Paste ACTUAL output; unrun is not pass.
7. Commit only this plan's files, path-scoped; check `git diff --cached --name-only`; never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
8. Lifecycle: after all E/V items pass, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. The transition is not an E-item.
