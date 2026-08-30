# IPD: Make coding-agent reporting concise across OpenCode, Agy, Codex CLI, and Claude CLI

- Date: 2026-08-29
- Kind: child
- Concern: Coding agents invoked directly or through agent-workflows routinely spend too many tokens on preambles, routine-action narration, praise, recaps, closing offers, and multi-paragraph explanations of simple outcomes. The repository has no portable reporting contract separating concise user-facing communication from complete engineering execution. Host-specific settings cannot solve this consistently because OpenCode, Agy/Antigravity, Codex CLI, and Claude CLI load different instruction surfaces and provider-specific verbosity parameters are inconsistent.
- Scope: Define one host-neutral concise-reporting contract; render it into installed managed instructions as a separately owned `aw:reporting` section; deliver it to Claude/OpenCode command sessions by POINTER (not by duplicating prose into 48 shims); inject it into OpenCode and Agy IPD-driver execution, verification, AND review turns; resolve the workflow-required-report precedence conflict explicitly; document precedence and limits; regenerate owned artifacts; and add reachability, parity, no-clobber, and prompt-construction tests. The contract governs conversational progress and final responses, not the completeness of code, tests, IPDs, reports, JSON outcomes, safety warnings, or workflow-required evidence.
- Scope-Paths: agent_workflows/reporting_contract.py, agent_workflows/engine.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/, docs/, README.md, AGENTS.md, .opencode/commands/**, .claude/commands/**
- Item-Dependencies: none
- Status: reviewed
- Priority: high
- Set: terseout
- Order: 1
- Highest E allocated: 09
- Author: codex gpt-5.6
- Id: ntf6sx

## Workflow history

- 2026-08-29 draft (codex gpt-5.6): created.
- 2026-08-29 to-review (codex gpt-5.6): authored a review-ready cross-host concise-reporting plan from current installer, shim, and runner architecture.
- 2026-08-29 to-review (aw set): status set to to-review
- 2026-08-30 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 fixed in place (shim prose duplication replaced with a pointer after measuring +83% shim growth against the stated token-cost goal, review-turn injection reworked around the bare-slash-command constraint, workflow-required-report precedence conflict resolved, unimplemented `managed_sections` manifest claim corrected, per-section decline path covered, E-items split 05 -> 09).
- 2026-08-30 reviewed (aw set): status set to reviewed

## Goal

Make concise, essential-information-only user-facing reporting the portable default for agent-workflows across OpenCode, Agy/Antigravity, Codex CLI, and Claude CLI, while preserving full analysis, implementation, testing, evidence, safety, and required deliverables. Reduce reporting verbosity without truncation, weaker work, global user-configuration edits, or reliance on one provider's model options.

Net-token constraint (added during review, and binding on the design): this plan exists to LOWER token cost, a stated 2.x direction (`README.md:15`). A delivery mechanism that costs more input tokens on every invocation than it saves in output tokens defeats its own purpose. Measured: the contract prose is roughly 735 bytes (~183 tokens); embedding it in all 48 generated shims (24 OpenCode + 24 Claude) would add ~35KB to a 42.7KB shim corpus, an 83% increase, and would be re-read on every single command invocation. Therefore full contract prose is rendered ONCE per instruction surface and command shims carry a one-line POINTER, not a copy. Any E-item that would duplicate the prose per-shim must be rejected at execution time.

Precedence conflict that must be resolved, not left implicit: several installed workflows REQUIRE a long, literally-specified final report. `plan-review` mandates a full findings table and states that a specific section "MUST be the literal final output" (`.aw/system/workflows/plan-review/plan-review.md:443`, `:492`); `release-review`, `plan-review-long`, and `exec-set` carry comparable required-report sections. A 100-word default reaching those same sessions is a direct contradiction, so the contract must state the override in a way a model resolves correctly WITHOUT weakening either rule (E-06).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: define and distribute one reporting contract

- [ ] E-01 Add `agent_workflows/reporting_contract.py` as the host-neutral source of truth for the exact contract and any compact embedding helper. The contract MUST say: lead with the outcome; begin binary answers with `Yes.` or `No.`; use one sentence when sufficient; omit preambles, praise, request restatement, routine narration, recap, and closing offers; use plain direct language; report only material outcomes, changed files, verification, and blockers; omit empty categories; keep routine finals at or below 100 words; and keep progress to one short sentence only when materially useful. It MUST also say that explicit user or controlling-workflow requirements override the default; required evidence, safety warnings, destructive-action confirmations, structured outcomes, and durable artifacts stay complete; and concision applies to reporting, not analysis, implementation, testing, or correctness.
  - Depends on: none
  - Expected outcome: one importable provider-neutral contract defines the behavior and cannot reasonably be read as permission to perform less work or omit mandatory evidence.
  - Execution state: pending

- [ ] E-02 Render the contract as a separately owned `aw:reporting` managed section in `AGENTS.md` and in existing native files.
  - Depends on: E-01
  - Expected outcome: `agents_managed_sections()` (`agent_workflows/engine.py:1389-1402`) returns a SECOND `AwSection` with slug `reporting` alongside `AW_POINTER_SLUG`, so `merge_aw_block` writes both. Verified this is the intended extension point: the docstring already states "consumer IPDs add sibling sections". Existing `CLAUDE.md`/`GEMINI.md` receive it through the same mirror path; absent native files are still NOT created (`tests/test_installer.py:660-668`). Foreign prose outside the block and sibling sections such as `AGENT-PLANS` stay byte-identical. Add the slug constant next to `AW_POINTER_SLUG` (`agent_workflows/engine.py:221`) rather than inlining a string literal.
  - Execution state: pending

- [ ] E-03 Deliver the contract to command shims by POINTER, not by duplicating the prose.
  - Depends on: E-02
  - Expected outcome: `shim_body()` and `aw_dispatcher_shim()` (`agent_workflows/engine.py:733`, `:858`) gain ONE short line referencing the contract (the `AGENTS.md#aw:reporting` section, in the same "read and execute" style the shims already use for workflow bodies at `.opencode/commands/plan-review.md:8`). Rationale, measured during review: full prose in 48 shims adds ~35KB to a 42.7KB corpus (+83%), re-read on EVERY invocation, which contradicts the token-cost goal in `README.md:15`. The original E-02 wording permitted this duplication ("Put the same contract ... in generated OpenCode and Claude command shims"); it is now explicitly forbidden. Host grammars are preserved exactly: OpenCode keeps `agent: build`, Claude keeps `argument-hint:`, both keep `$ARGUMENTS` and the `If the user provided arguments` line that `engine.py:907-958` self-checks.
  - Execution state: pending

- [ ] E-04 Inject the contract into the two drivers' EXECUTION and VERIFIER prompts from the shared source.
  - Depends on: E-01
  - Expected outcome: `build_prompt()` and `build_verifier_prompt()` in both drivers (`agent_workflows/oc_runipd.py:1571`, `:1661`; `agent_workflows/agy_runipd.py:1653`, `:1737`) import and embed the contract from `reporting_contract.py` rather than a hand-copied fragment. Note the plan's original line citations (`oc_runipd.py:1452-1624`, `agy_runipd.py:1550-1716`) no longer match; use the symbol names, not line numbers. Required JSON schemas, actual-output evidence requirements, lifecycle instructions, `pushed: false`, and the concurrent-work warning remain present and unmodified.
  - Execution state: pending

- [ ] E-05 Handle the REVIEW-turn surface, which cannot take appended prose.
  - Depends on: E-04
  - Expected outcome: `build_review_prompt()` in both drivers returns EXACTLY the string `f"/plan-review {rel_path}"` (`agent_workflows/oc_runipd.py:1557-1569`, `agent_workflows/agy_runipd.py:1639-1651`) and the value is passed as a single argv element after `--` (`agent_workflows/oc_runipd.py:1874-1882`), so appending contract prose would make the slash command's `$ARGUMENTS` absorb it as path arguments. The original E-03 assumed a "reliable existing surface" without naming one. Resolution: do NOT modify the review prompt string; the review turn inherits the contract from the E-03 shim pointer plus the E-02 `AGENTS.md` section, and the plan records that as the deliberate mechanism. If a future change must add prose there, it goes on a separate line AFTER the command, never on the command line itself.
  - Execution state: pending

- [ ] E-06 Encode the workflow-required-report override so brevity cannot suppress a mandated report.
  - Depends on: E-01
  - Expected outcome: the contract states the precedence in operational, testable terms: when a controlling workflow specifies a required report format, that format is produced IN FULL and the word cap does not apply to it. Concrete conflict this resolves: `plan-review` requires a full findings table and declares a section "MUST be the literal final output" (`.aw/system/workflows/plan-review/plan-review.md:443`, `:492`); `release-review`, `plan-review-long`, and `exec-set` have comparable required reports. The 100-word default MUST be phrased so it never reads as license to truncate one of those. Include the inverse guard too: brevity is not an excuse to skip pasting actual runner output required by the execution contract.
  - Execution state: pending

### Task group 2: prove portability and prevent drift

- [ ] E-07 Add contract-source, managed-section, and installer-safety tests.
  - Depends on: E-02
  - Expected outcome: tests prove the module imports; the contract text contains every brevity rule AND every completeness exception; `AGENTS.md` gains exactly one `aw:reporting` section; a second install is byte-idempotent; existing `CLAUDE.md`/`GEMINI.md` receive the section with foreign prose byte-preserved; absent native files stay absent; a user-edited `aw:reporting` body is PRESERVED not clobbered, and a `declined` tombstone for `AGENTS.md#aw:reporting` OMITS it (both paths already exist in `_apply_section_consent`, `agent_workflows/engine.py:1554-1590`, and must be covered since this is the first sibling section to exercise them).
  - Execution state: pending

- [ ] E-08 Add shim-pointer, driver-prompt, and parity/anti-duplication tests.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: tests assert OpenCode and Claude shims contain the pointer and retain valid host frontmatter plus `$ARGUMENTS`; both drivers' execution and verifier prompts contain the contract and still carry required JSON keys and evidence rules; `build_review_prompt` output still matches `^/plan-review \S+$` exactly (the E-05 regression guard); a parity test fails if any surface carries a second independently maintained copy of the prose; and a BUDGET test asserts per-shim growth stays within a stated small bound, so the E-03 decision cannot silently regress into duplication.
  - Execution state: pending

- [ ] E-09 Document the default, the delivery surfaces, and the rejected alternatives; regenerate owned artifacts.
  - Depends on: E-07, E-08
  - Expected outcome: docs/README describe the default, the override, per-host coverage, and why global home-directory edits, provider-only fields (`textVerbosity`, temperature), and output-token caps are not the mechanism. Docs POINT to `agent_workflows/reporting_contract.py` without forking its prose. Regenerate `AGENTS.md`, `.opencode/commands/**`, and `.claude/commands/**` through the installer, never by hand. Scope correction: `.aw/system/managed-sections.json` is NOT hand-regenerated and was removed from Scope-Paths; its `managed_sections` map is currently RESERVED AND UNPOPULATED (`agent_workflows/manifest.py:151-153` says "round-tripped but not populated here"; the live file's `managed_sections` is `{}`). Section hashes are recorded through `manifest.record(...)` during a normal install (`agent_workflows/engine.py:1587`), so the manifest changes as a SIDE EFFECT of running the installer. Do not claim to regenerate a map the code does not populate.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows.engine.agents_pointer_prose()` supplies the installer-owned block. `agents_managed_sections()` currently emits one `aw:pointer` section; `update_agents_pointer()` merges it into the selected `AGENTS.md` plus existing `CLAUDE.md`/`GEMINI.md` without creating absent native files (`agent_workflows/engine.py:1037`, `:1389`, `:2283`). A separate `aw:reporting` section fits the ownership model; verified the docstring at `engine.py:1392-1395` explicitly anticipates "consumer IPDs add sibling sections".
- Per-section consent and drift protection already exist in `_apply_section_consent()` (`agent_workflows/engine.py:1554-1590`): a `declined` tombstone omits a section and a user-edited body is preserved rather than clobbered. `aw:reporting` will be the FIRST sibling section to exercise these paths, so they need explicit coverage (E-07).
- `.opencode/commands/*.md` and `.claude/commands/*.md` come from `shim_body()` and `aw_dispatcher_shim()` (`agent_workflows/engine.py:733`, `:858`). OpenCode emits `agent: build` (`:829`); Claude emits `argument-hint:` (`:822-824`); both use `$ARGUMENTS`, and `engine.py:907-958` self-checks the pairing of `argument-hint`/`$ARGUMENTS`/`If the user provided arguments`. Reporting changes must preserve those grammars.
- Shim scale, measured: 24 OpenCode + 24 Claude command files totaling 42,701 bytes, individual shims roughly 600-830 bytes (`.opencode/commands/plan-review.md` is 604). This is why the contract is delivered to shims by pointer (E-03) rather than by copy.
- `aw oc run` and `aw agy run` build fresh execution and verifier prompts independently (`agent_workflows/oc_runipd.py:1571`/`:1661`; `agent_workflows/agy_runipd.py:1653`/`:1737`). They already embed critical safeguards because fresh workers must not depend only on ambient host behavior. The line ranges cited in the original draft were stale; use symbol names.
- REVIEW turns are different in kind: `build_review_prompt()` returns only `f"/plan-review {rel_path}"` (`agent_workflows/oc_runipd.py:1557-1569`, `agent_workflows/agy_runipd.py:1639-1651`) and that string is handed to the host as one argv element after `--` (`agent_workflows/oc_runipd.py:1874-1882`). Prose cannot be appended to it without being consumed as `$ARGUMENTS` path arguments (E-05).
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

Findings added during plan review (each verified against the code):

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Copying the contract into every shim would defeat the plan's own token goal. | Contract prose ~735 bytes (~183 tokens); 48 shims totaling 42,701 bytes; duplication is +35KB, or +83%, re-read per invocation, against the "lower token cost" direction at `README.md:15`. | E-03 rewritten to a one-line pointer; E-08 adds a budget test so duplication cannot creep back. |
| The review turn cannot carry appended prose, and the original plan did not say how it would. | `build_review_prompt()` returns exactly `/plan-review <path>` (`oc_runipd.py:1557-1569`, `agy_runipd.py:1639-1651`), delivered as one argv element after `--` (`oc_runipd.py:1874-1882`); appended prose becomes `$ARGUMENTS`. | New E-05 fixes the mechanism as inheritance via shim + `AGENTS.md`, forbids touching the command string, and E-08 asserts the exact-match regex. |
| A 100-word cap directly contradicts workflows that mandate long reports. | `plan-review` requires a full findings table and "MUST be the literal final output" (`.aw/system/workflows/plan-review/plan-review.md:443`, `:492`); `release-review`, `plan-review-long`, `exec-set` similar. | New E-06 makes the override operational and testable in both directions (no truncated reports, no skipped pasted evidence). |
| The plan claimed it would regenerate a manifest map the code never populates. | `agent_workflows/manifest.py:151-153` states `managed_sections` is "round-tripped but not populated here"; the live `.aw/system/managed-sections.json` has `managed_sections: {}`. | E-09 corrected; the path was removed from Scope-Paths and the real mechanism (`manifest.record` during install, `engine.py:1587`) documented. |
| `aw:reporting` is the first sibling section, so the consent/drift paths are newly load-bearing. | `_apply_section_consent()` handles `declined` tombstones and preserves user-edited bodies (`engine.py:1554-1590`) but has only ever run with one section. | E-07 requires explicit coverage of decline and user-edit-preservation for the new slug. |
| Cited line ranges were already stale, risking a misdirected edit. | Draft cited `oc_runipd.py:1452-1624` and `agy_runipd.py:1550-1716`; actual builders are at `oc_runipd.py:1571`/`:1661` and `agy_runipd.py:1653`/`:1737`. | E-04 instructs the executor to bind to symbol names, not line numbers. |
| The plan's own example prose uses curly typography it tells agents to avoid. | Line in "Proposed changes" used curly quotes and an ellipsis character. | Normalized to straight quotes so the shipped example does not model the opposite of its own plain-language rule. |

## Proposed changes (ordered, validatable)

1. Create the shared contract with explicit completeness and precedence safeguards (E-01, E-06).
2. Add a separately owned `aw:reporting` managed section (E-02) and give shims a one-line pointer to it, never a copy (E-03).
3. Add the contract to both drivers' execution and verifier prompts without changing schemas (E-04), leaving the review command string untouched (E-05).
4. Add parity, budget, installer-safety, consent/drift, and prompt regression tests (E-07, E-08).
5. Document the policy and rejected alternatives, and regenerate owned artifacts through the installer (E-09).

A compliant routine final normally contains only the result, changed files when material, actual verification status, and blockers. It excludes greetings, "I'll ...", praise, narrated searches/reads, restatement, redundant summary, and "let me know if ...". When a workflow requires a long report or pasted evidence, produce it completely and keep surrounding prose concise.

## Deferred / out of scope (with reason)

- Global files such as `~/.config/opencode/AGENTS.md`, `~/.claude/CLAUDE.md`, or Codex home configuration: repository installation must not overwrite personal cross-project preferences.
- Provider fields such as OpenAI `textVerbosity`, temperature, or Claude output-style selection: not portable across all four hosts.
- Low output-token limits or truncation: may cut off errors, evidence, or JSON.
- Changes to reasoning effort, tool calls, steps, test scope, implementation depth, or verifier rigor: concision applies only to reporting.
- `aw` CLI human/JSONL redesign: already governed separately.
- Mandatory live-model CI: credentials, network, cost, version drift, and probabilism make it nondeterministic. A maintainer may run the smoke matrix.
- Creating missing `CLAUDE.md`/`GEMINI.md`: generated Claude shims provide workflow coverage and the installer intentionally avoids creating native files merely for managed prose.

## Scope check

- Over-scope: no global configuration, provider tuning, truncation, CLI redesign, or reduced execution/testing. Removed during review: per-shim duplication of the contract prose (E-03 now uses a pointer, on measured token grounds) and hand-regeneration of `.aw/system/managed-sections.json` (an unpopulated reserved map, so the claim was unfounded).
- Under-scope: OpenCode is covered by `AGENTS.md`, shims, and `aw oc run`; Agy by `aw agy run`; Codex CLI by `AGENTS.md`; Claude CLI by generated commands and existing `CLAUDE.md` when present. Ad hoc Claude sessions with no `CLAUDE.md` and no agent-workflows command remain outside the product's invocation surface.
- Under-scope added during review: the workflow-required-report precedence conflict (E-06), the review-turn delivery mechanism (E-05), first-sibling-section consent/drift coverage (E-07), and a shim size budget guard (E-08).

## Required tests / validation

- Unit tests for the canonical contract and every safeguard.
- Installer tests for fresh install, update, idempotence, separate managed-section ownership, foreign-prose preservation, and no creation of absent native files.
- First-sibling-section consent tests: `declined` tombstone omission and user-edit preservation for `AGENTS.md#aw:reporting`.
- Shim tests for OpenCode and Claude frontmatter and `$ARGUMENTS` semantics, plus the pointer presence.
- A shim SIZE BUDGET test (baseline: 42,701 bytes across 48 files) so the pointer decision cannot regress into per-shim duplication.
- Prompt tests for OpenCode/Agy workers and verifiers, plus a `build_review_prompt` exact-match test (`^/plan-review \S+$`) proving no prose leaked onto the slash-command line.
- Parity tests proving all embedded surfaces derive from or match the source, demonstrated FAILING once before passing.
- Regression assertions for JSON outcome fields, evidence requirements, and lifecycle rules.
- Existing generation/no-drift check for `AGENTS.md` and the shims. (Not `managed-sections.json`: its `managed_sections` map is reserved and unpopulated; it changes only as a side effect of an install.)
- `python3 -m pytest -p no:randomly`.
- `aw sanitize --agent`.
- Optional live smoke matrix when CLIs and credentials exist: one trivial yes/no query and completed-change task through OpenCode, `aw oc run`, `aw agy run`, Codex CLI, and a Claude command. Record directness, narration, applicable 100-word limit, and preserved evidence. Unavailable hosts are `not run`, never `pass`.

## Spec / documentation sync

- Add a concise section to the appropriate README/docs page describing the default, override, and host coverage.
- Identify the contract source and distinguish model prose from CLI output modes (`docs/cli-output-contract.md` governs `aw` CLI bytes; this contract governs model-authored prose; neither may be read as licensing fewer JSONL fields).
- Add a decision/spec pointer if current conventions require one; do not duplicate the contract. Record the E-03 pointer-not-copy choice and its measured basis so a later maintainer does not "simplify" it back into duplication.
- Regenerate the owned adapters (`AGENTS.md`, `.opencode/commands/**`, `.claude/commands/**`) through the installer.

## Open questions

### OQ-01: Shim delivery mechanism, pointer versus embedded prose

- Blocking: no
- Status: resolved
- Owner: plan-review
- Resolution or deferral rationale: resolved from repository evidence rather than escalated. The original E-02 allowed embedding the contract (or a compact form) directly in all 48 generated shims. Measured: contract prose ~735 bytes against a 42,701-byte shim corpus across 24 OpenCode + 24 Claude files, so duplication costs ~+35KB (+83%) of input re-read on every invocation, contradicting the "lower token cost" 2.x direction (`README.md:15`). A one-line pointer in the shim, in the same "read and execute" idiom the shims already use (`.opencode/commands/plan-review.md:8`), delivers the same reachability at a fraction of the cost, and `AGENTS.md` already carries the full section for hosts that read it. Decision: pointer in shims, full prose once per instruction surface, with a budget test (E-08) to prevent regression. Residual risk stated honestly: a host that loads a command shim WITHOUT resolving the pointer gets a weaker signal than embedded prose would give; this is accepted because the deterministic tests can prove pointer presence, and the alternative measurably harms the plan's own goal.

### OQ-02: Interaction between the 100-word default and workflows that mandate long reports

- Blocking: no
- Status: resolved
- Owner: plan-review
- Resolution or deferral rationale: resolved from repository evidence. `plan-review` requires a full findings table and states a section "MUST be the literal final output" (`.aw/system/workflows/plan-review/plan-review.md:443`, `:492`), and `release-review`, `plan-review-long`, and `exec-set` carry comparable required reports; those same sessions receive the contract. The original plan mentioned precedence only in passing. Decision: E-06 makes the override explicit and operational (a workflow-specified report is produced in full and the cap does not apply to it), with the inverse guard that brevity never licenses skipping required pasted evidence, and V-06 requires the two rules to be quoted side by side. This is a wording/precedence matter the repository fully determines, so it needed no maintainer input.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted focused-test output showing the module imports and the exact contract contains every brevity rule plus exceptions for requested/required detail, evidence, safety, structured outcomes, durable artifacts, and full execution/testing. Include a source search showing no second independently maintained full production contract.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Pasted installer test output proving installed `AGENTS.md` contains exactly ONE `aw:reporting` section alongside `aw:pointer`; existing `CLAUDE.md`/`GEMINI.md` receive it with foreign prose byte-preserved; absent native files remain absent; a second install is byte-idempotent. Also paste the rendered `AGENTS.md` block markers showing the `AGENT-PLANS` sibling and any user prose unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste one generated OpenCode shim and one Claude shim in full, showing the one-line pointer, intact `agent: build` / `argument-hint:` frontmatter, and `$ARGUMENTS`. Paste the measured byte delta: `cat .opencode/commands/*.md .claude/commands/*.md | wc -c` before and after, with the increase within the stated budget (baseline 42,701 bytes). A result near +35KB means the prose was duplicated and V-03 FAILS.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Pasted prompt-builder test output proving the contract text appears in `build_prompt` AND `build_verifier_prompt` output for BOTH drivers, plus assertions that required JSON keys, actual-output evidence requirements, lifecycle rules, and `pushed: false` are still present. Include a parity assertion showing both drivers import from `reporting_contract.py` rather than embedding a literal.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Paste the actual return value of `build_review_prompt(...)` from both drivers, showing it matches `^/plan-review \S+$` with no trailing prose, plus the passing test that enforces that regex. Also paste `git diff` for the two `build_review_prompt` functions showing NO functional change to the returned string.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Paste the contract text section covering precedence, plus a test asserting it names the required-report override explicitly. Then paste a reasoning check: quote the contract's override sentence next to `plan-review.md:492` ("MUST be the literal final output") and state why a model reading both produces the full report. Also paste the inverse assertion that brevity does not license skipping pasted runner output.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Pasted focused test output naming the tests for contract completeness, single `aw:reporting` section, idempotence, foreign-prose preservation, absent-native behavior, AND the two first-time-exercised consent paths: a `declined` tombstone for `AGENTS.md#aw:reporting` omitting the section, and a user-edited `aw:reporting` body being preserved rather than clobbered.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: Pasted output of the full focused regression set, including the parity test, the `build_review_prompt` exact-match test, and the shim budget test. Also paste a NEGATIVE demonstration: temporarily duplicate the prose into a shim (or mutate one rendered copy) and show the parity/budget test FAILING, then show it passing after revert. A guard never observed failing is not proven.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: Pasted `git diff --check`; the generated-artifact/no-drift check for `AGENTS.md` and the OpenCode/Claude shims (NOT a hand-regenerated `managed-sections.json`, which is out of scope); a search showing docs point to `agent_workflows/reporting_contract.py` without forking its prose; `python3 -m pytest -p no:randomly` with exit 0 and the actual summary line; and `aw sanitize --agent` clean. If live smokes run, paste host/model/version and measured response shape; otherwise state `not run` without weakening deterministic acceptance.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one cohesive concern, portable concise reporting, implemented through existing managed-instruction, shim, and driver-prompt adapters.

Execution contract:

1. Human approval is required. OQ-01 and OQ-02 are resolved from repository evidence; there are no unresolved questions.
2. Scope fence: touch only `Scope-Paths`. Preserve foreign instruction content and generated ownership. Do not add global writes, provider tuning, truncation, or reduced work. Do NOT hand-edit `.aw/system/managed-sections.json` (removed from scope; it changes only as an install side effect). If another production area is needed, STOP and report.
3. Semantics fence: concise governs user-facing progress and final prose. It MUST NOT omit code, documents, IPDs, JSON, safety, confirmations, test output, evidence, blockers, or workflow fields. Explicit user/workflow requirements override 100 words; remain concise within them.
4. Token fence (binding): do NOT embed the full contract prose in generated command shims. Shims get a one-line pointer. Duplication measured at +83% of the shim corpus and would defeat the plan's own token-cost goal; the E-08 budget test enforces this.
5. Review-turn fence: `build_review_prompt()` must keep returning exactly `/plan-review <path>`. Never append prose to that string; it is passed as a single argv element and would be parsed as `$ARGUMENTS`.
6. Host fence: retain OpenCode `agent: build`, Claude-compatible frontmatter, `$ARGUMENTS`, Codex `AGENTS.md`, and Agy lifecycle/outcome behavior.
7. Honesty: reachability tests do not guarantee model obedience. Live smokes must record actual host/model/version/output; unavailable means `not run`. A parity or budget guard that was never observed failing is not proven (see V-08).
8. Validation: run focused tests, full suite, generation/no-drift, and leak sanitizer. Paste ACTUAL output; unrun is not pass.
9. Commit only this plan's files, path-scoped; check `git diff --cached --name-only`; never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push. Other agents are working in this same checkout: unstage anything you did not modify rather than sweeping a co-worker's pending edits into your commit.
10. Lifecycle: after all E/V items pass, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. The transition is not an E-item.
