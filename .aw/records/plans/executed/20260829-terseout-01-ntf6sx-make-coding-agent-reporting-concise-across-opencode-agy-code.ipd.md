# IPD: Make coding-agent reporting concise across OpenCode, Agy, Codex CLI, and Claude CLI

- Date: 2026-08-29
- Kind: child
- Concern: Coding agents invoked directly or through agent-workflows routinely spend too many tokens on preambles, routine-action narration, praise, recaps, closing offers, and multi-paragraph explanations of simple outcomes. The repository has no portable reporting contract separating concise user-facing communication from complete engineering execution. Host-specific settings cannot solve this consistently because OpenCode, Agy/Antigravity, Codex CLI, and Claude CLI load different instruction surfaces and provider-specific verbosity parameters are inconsistent.
- Scope: Define one host-neutral concise-reporting contract; render it into installed managed instructions as a separately owned `aw:reporting` section; deliver it to Claude/OpenCode command sessions by POINTER (not by duplicating prose into 48 shims); inject it into OpenCode and Agy IPD-driver execution, verification, AND review turns; resolve the workflow-required-report precedence conflict explicitly; document precedence and limits; regenerate owned artifacts; and add reachability, parity, no-clobber, and prompt-construction tests. The contract governs conversational progress and final responses, not the completeness of code, tests, IPDs, reports, JSON outcomes, safety warnings, or workflow-required evidence.
- Scope-Paths: agent_workflows/reporting_contract.py, agent_workflows/engine.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/, docs/, README.md, AGENTS.md, .opencode/commands/**, .claude/commands/**
- Item-Dependencies: none
- Status: executed
- Priority: high
- Set: terseout
- Order: 1
- Highest E allocated: 09
- Author: codex gpt-5.6
- Id: ntf6sx

## Workflow history
- 2026-08-30 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): One portable concise-reporting contract delivered via the aw:reporting managed section, a pointer line in all 48 command shims, and both drivers' worker/verifier prompts; review command string untouched; 53 new tests with observed-failing budget and parity guards; full suite 3628 passed with only the 15 pre-existing test_run_viewer failures. [Scope reconciliation - in-scope-unmodified .claude/commands/**: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified .opencode/commands/**: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified AGENTS.md: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified README.md: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified agent_workflows/agy_runipd.py: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified agent_workflows/engine.py: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified agent_workflows/oc_runipd.py: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified agent_workflows/reporting_contract.py: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified docs/: modified-in-commit-fb0774b2-before-begin-receipt-was-written; in-scope-unmodified tests/: modified-in-commit-fb0774b2-before-begin-receipt-was-written]
- 2026-08-30 approved (aw set, --by-human): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).

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

- [x] E-01 Add `agent_workflows/reporting_contract.py` as the host-neutral source of truth for the exact contract and any compact embedding helper. The contract MUST say: lead with the outcome; begin binary answers with `Yes.` or `No.`; use one sentence when sufficient; omit preambles, praise, request restatement, routine narration, recap, and closing offers; use plain direct language; report only material outcomes, changed files, verification, and blockers; omit empty categories; keep routine finals at or below 100 words; and keep progress to one short sentence only when materially useful. It MUST also say that explicit user or controlling-workflow requirements override the default; required evidence, safety warnings, destructive-action confirmations, structured outcomes, and durable artifacts stay complete; and concision applies to reporting, not analysis, implementation, testing, or correctness.
  - Depends on: none
  - Expected outcome: one importable provider-neutral contract defines the behavior and cannot reasonably be read as permission to perform less work or omit mandatory evidence.
  - Execution state: performed
  - Execution note: done. Added `agent_workflows/reporting_contract.py` with `contract_text()`, `shim_pointer_line()`, `prompt_block()`, and the `REPORTING_SLUG`/`POINTER_TARGET`/`ROUTINE_FINAL_WORD_CAP` constants. Contract prose is 1,707 bytes, pure ASCII, and states every brevity rule plus the completeness exceptions.

- [x] E-02 Render the contract as a separately owned `aw:reporting` managed section in `AGENTS.md` and in existing native files.
  - Depends on: E-01
  - Expected outcome: `agents_managed_sections()` (`agent_workflows/engine.py:1389-1402`) returns a SECOND `AwSection` with slug `reporting` alongside `AW_POINTER_SLUG`, so `merge_aw_block` writes both. Verified this is the intended extension point: the docstring already states "consumer IPDs add sibling sections". Existing `CLAUDE.md`/`GEMINI.md` receive it through the same mirror path; absent native files are still NOT created (`tests/test_installer.py:660-668`). Foreign prose outside the block and sibling sections such as `AGENT-PLANS` stay byte-identical. Add the slug constant next to `AW_POINTER_SLUG` (`agent_workflows/engine.py:221`) rather than inlining a string literal.
  - Execution state: performed
  - Execution note: done. Added `AW_REPORTING_SLUG = reporting_contract.REPORTING_SLUG` next to `AW_POINTER_SLUG` (engine.py:222-226) and a SECOND `AwSection` in `agents_managed_sections()` whose body is `reporting_contract.contract_text()`. Order is `[pointer, reporting]`; native mirrors go through the same `update_agents_pointer` path; absent native files are still not created.

- [x] E-03 Deliver the contract to command shims by POINTER, not by duplicating the prose.
  - Depends on: E-02
  - Expected outcome: `shim_body()` and `aw_dispatcher_shim()` (`agent_workflows/engine.py:733`, `:858`) gain ONE short line referencing the contract (the `AGENTS.md#aw:reporting` section, in the same "read and execute" style the shims already use for workflow bodies at `.opencode/commands/plan-review.md:8`). Rationale, measured during review: full prose in 48 shims adds ~35KB to a 42.7KB corpus (+83%), re-read on EVERY invocation, which contradicts the token-cost goal in `README.md:15`. The original E-02 wording permitted this duplication ("Put the same contract ... in generated OpenCode and Claude command shims"); it is now explicitly forbidden. Host grammars are preserved exactly: OpenCode keeps `agent: build`, Claude keeps `argument-hint:`, both keep `$ARGUMENTS` and the `If the user provided arguments` line that `engine.py:907-958` self-checks.
  - Execution state: performed
  - Execution note: done by POINTER. `shim_body()` and `aw_dispatcher_shim()` each append `reporting_contract.shim_pointer_line()` (92 bytes, one line). Full prose is NOT in any shim. Also added the pointer prefix to the `is_stale_shim_customized` structural allowlist so a regenerated shim is not misflagged as user-edited. Measured corpus 42,709 -> 46,941 bytes (+4,232, ~88/file) versus +81,936 (+192%) for duplication.

- [x] E-04 Inject the contract into the two drivers' EXECUTION and VERIFIER prompts from the shared source.
  - Depends on: E-01
  - Expected outcome: `build_prompt()` and `build_verifier_prompt()` in both drivers (`agent_workflows/oc_runipd.py:1571`, `:1661`; `agent_workflows/agy_runipd.py:1653`, `:1737`) import and embed the contract from `reporting_contract.py` rather than a hand-copied fragment. Note the plan's original line citations (`oc_runipd.py:1452-1624`, `agy_runipd.py:1550-1716`) no longer match; use the symbol names, not line numbers. Required JSON schemas, actual-output evidence requirements, lifecycle instructions, `pushed: false`, and the concurrent-work warning remain present and unmodified.
  - Execution state: performed
  - Execution note: done. Bound to SYMBOL names, not line numbers, as the plan instructed. Both drivers now `from agent_workflows import reporting_contract` and end `build_prompt`/`build_verifier_prompt` with `{reporting_contract.prompt_block()}`. Required JSON keys, evidence rules, lifecycle text, `pushed: false`, and the Concurrent Work section are unchanged.

- [x] E-05 Handle the REVIEW-turn surface, which cannot take appended prose.
  - Depends on: E-04
  - Expected outcome: `build_review_prompt()` in both drivers returns EXACTLY the string `f"/plan-review {rel_path}"` (`agent_workflows/oc_runipd.py:1557-1569`, `agent_workflows/agy_runipd.py:1639-1651`) and the value is passed as a single argv element after `--` (`agent_workflows/oc_runipd.py:1874-1882`), so appending contract prose would make the slash command's `$ARGUMENTS` absorb it as path arguments. The original E-03 assumed a "reliable existing surface" without naming one. Resolution: do NOT modify the review prompt string; the review turn inherits the contract from the E-03 shim pointer plus the E-02 `AGENTS.md` section, and the plan records that as the deliberate mechanism. If a future change must add prose there, it goes on a separate line AFTER the command, never on the command line itself.
  - Execution state: performed
  - Execution note: done as INHERITANCE, with NO change to the returned string. `build_review_prompt` in both drivers still returns exactly `f"/plan-review {rel_path}"`; only a docstring was added recording why prose must never be appended (single argv element, absorbed as `$ARGUMENTS`) and that the review turn inherits the contract from the shim pointer plus `AGENTS.md#aw:reporting`.

- [x] E-06 Encode the workflow-required-report override so brevity cannot suppress a mandated report.
  - Depends on: E-01
  - Expected outcome: the contract states the precedence in operational, testable terms: when a controlling workflow specifies a required report format, that format is produced IN FULL and the word cap does not apply to it. Concrete conflict this resolves: `plan-review` requires a full findings table and declares a section "MUST be the literal final output" (`.aw/system/workflows/plan-review/plan-review.md:443`, `:492`); `release-review`, `plan-review-long`, and `exec-set` have comparable required reports. The 100-word default MUST be phrased so it never reads as license to truncate one of those. Include the inverse guard too: brevity is not an excuse to skip pasting actual runner output required by the execution contract.
  - Execution state: performed
  - Execution note: done. The contract carries a `PRECEDENCE` paragraph: an explicit user request or a controlling workflow's required report OVERRIDES the default, that report is produced IN FULL, and the 100-word cap does not apply to it. It names `plan-review`'s "literal final output" and `release-review`'s final report, and carries the inverse guard that brevity never licenses skipping the ACTUAL runner output.

### Task group 2: prove portability and prevent drift

- [x] E-07 Add contract-source, managed-section, and installer-safety tests.
  - Depends on: E-02
  - Expected outcome: tests prove the module imports; the contract text contains every brevity rule AND every completeness exception; `AGENTS.md` gains exactly one `aw:reporting` section; a second install is byte-idempotent; existing `CLAUDE.md`/`GEMINI.md` receive the section with foreign prose byte-preserved; absent native files stay absent; a user-edited `aw:reporting` body is PRESERVED not clobbered, and a `declined` tombstone for `AGENTS.md#aw:reporting` OMITS it (both paths already exist in `_apply_section_consent`, `agent_workflows/engine.py:1554-1590`, and must be covered since this is the first sibling section to exercise them).
  - Execution state: performed
  - Execution note: done. `tests/test_reporting_contract.py` adds 53 tests, including both first-time-exercised consent paths (a `declined` tombstone for `AGENTS.md#aw:reporting` omits it while the sibling `aw:pointer` survives; a user-edited body is preserved not clobbered), byte-idempotence, native mirroring with foreign prose preserved, absent-native behavior, and the foreign `AGENT-PLANS` sibling staying byte-identical.

- [x] E-08 Add shim-pointer, driver-prompt, and parity/anti-duplication tests.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: tests assert OpenCode and Claude shims contain the pointer and retain valid host frontmatter plus `$ARGUMENTS`; both drivers' execution and verifier prompts contain the contract and still carry required JSON keys and evidence rules; `build_review_prompt` output still matches `^/plan-review \S+$` exactly (the E-05 regression guard); a parity test fails if any surface carries a second independently maintained copy of the prose; and a BUDGET test asserts per-shim growth stays within a stated small bound, so the E-03 decision cannot silently regress into duplication.
  - Execution state: performed
  - Execution note: done. Same file covers shim pointer presence/absence-of-prose/host grammar across all 48 shims, both drivers' exec+verifier prompts with their required keys retained, the `^/plan-review \S+$` exact-match guard, parity (all rendered surfaces byte-equal to the source; only the module holds the prose), and a size BUDGET. Both guards were OBSERVED FAILING under injected regressions and passing after revert (see V-08).

- [x] E-09 Document the default, the delivery surfaces, and the rejected alternatives; regenerate owned artifacts.
  - Depends on: E-07, E-08
  - Expected outcome: docs/README describe the default, the override, per-host coverage, and why global home-directory edits, provider-only fields (`textVerbosity`, temperature), and output-token caps are not the mechanism. Docs POINT to `agent_workflows/reporting_contract.py` without forking its prose. Regenerate `AGENTS.md`, `.opencode/commands/**`, and `.claude/commands/**` through the installer, never by hand. Scope correction: `.aw/system/managed-sections.json` is NOT hand-regenerated and was removed from Scope-Paths; its `managed_sections` map is currently RESERVED AND UNPOPULATED (`agent_workflows/manifest.py:151-153` says "round-tripped but not populated here"; the live file's `managed_sections` is `{}`). Section hashes are recorded through `manifest.record(...)` during a normal install (`agent_workflows/engine.py:1587`), so the manifest changes as a SIDE EFFECT of running the installer. Do not claim to regenerate a map the code does not populate.
  - Execution state: performed
  - Execution note: done. Added `docs/reporting-contract.md` (linked from `docs/README.md`), a README section, a CHANGELOG entry, and DECISIONS D149. Docs POINT at `agent_workflows/reporting_contract.py` without forking its prose. `AGENTS.md` and all 47 shims regenerated THROUGH the installer (run in a throwaway copy, Scope-Paths outputs copied back; see decision 01-ntf6sx-D2). `.aw/system/managed-sections.json` was NOT hand-edited, per the plan's scope correction.

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

- [x] V-01 validates E-01
  - Required evidence: Pasted focused-test output showing the module imports and the exact contract contains every brevity rule plus exceptions for requested/required detail, evidence, safety, structured outcomes, durable artifacts, and full execution/testing. Include a source search showing no second independently maintained full production contract.
  - Observed evidence: `pytest tests/test_reporting_contract.py::ContractSourceTests` -> `7 passed`; contract is 1,707 bytes, pure ASCII, and `grep -rln` finds its opening sentence in exactly ONE production module. Full output below.
  - Result: pass

    Evidence detail for V-01:

    `python3 -m pytest tests/test_reporting_contract.py::ContractSourceTests -o addopts="" -q`:
    ```text
    .......                                                                  [100%]
    7 passed in 0.11s
    ```
    The 7 tests are: module imports and returns stable text; every brevity rule present; every completeness exception present; cannot be read as permission to do less; word-cap constant matches the prose; pure ASCII; and no second independently maintained production copy. That last one greps every `agent_workflows/**/*.py` for the contract's opening sentence and asserts the owner list is exactly `['agent_workflows/reporting_contract.py']`:
    ```text
    $ grep -rln "Report to the user concisely." agent_workflows/
    agent_workflows/reporting_contract.py
    ```
    Contract size and ASCII check:
    ```text
    $ python3 -c "from agent_workflows import reporting_contract as rc; t=rc.contract_text(); print(len(t.encode()),'bytes'); print('non-ascii:', sorted({c for c in t if ord(c)>127}))"
    1707 bytes
    non-ascii: []
    ```
- [x] V-02 validates E-02
  - Required evidence: Pasted installer test output proving installed `AGENTS.md` contains exactly ONE `aw:reporting` section alongside `aw:pointer`; existing `CLAUDE.md`/`GEMINI.md` receive it with foreign prose byte-preserved; absent native files remain absent; a second install is byte-idempotent. Also paste the rendered `AGENTS.md` block markers showing the `AGENT-PLANS` sibling and any user prose unchanged.
  - Observed evidence: `pytest ...ManagedSectionTests ...InstallerSafetyTests` -> `14 passed`; generator emits `['aw:block','aw:pointer','aw:reporting','/aw:block']`; the `AGENTS.md` diff is exactly the 25-line new section with the `AGENT-PLANS` sibling untouched. Full output below.
  - Result: pass

    Evidence detail for V-02:

    `python3 -m pytest tests/test_reporting_contract.py::ManagedSectionTests tests/test_reporting_contract.py::InstallerSafetyTests -o addopts="" -q`:
    ```text
    ..............                                                           [100%]
    14 passed in 17.32s
    ```
    Covers: exactly one `aw:reporting` marker alongside `aw:pointer` on a fresh install; second install byte-idempotent; existing `CLAUDE.md`/`GEMINI.md` receive it with the user's prose byte-preserved; absent native files stay absent; a foreign `AGENT-PLANS:BEGIN/END` block byte-identical after install.

    Section order from the generator:
    ```text
    $ python3 -c "from agent_workflows import engine as E; import re; print(re.findall(r'<!-- (/?aw:[a-z]*) -->', E.agents_managed_block(target_layout='aw')))"
    ['aw:block', 'aw:pointer', 'aw:reporting', '/aw:block']
    ```
    The rendered `AGENTS.md` diff is ONLY the new section (no sibling touched, no user prose reflowed):
    ```text
    $ git diff --stat -- AGENTS.md
     AGENTS.md | 25 +++++++++++++++++++++++++
     1 file changed, 25 insertions(+)

    $ git diff -- AGENTS.md | head -8
    @@ -63,6 +63,31 @@ ... ### Authoring and executing IPDs
     ... `aw ipd lint --phase pre-transition` conforms and every validation item is verified ...
    +<!-- aw:reporting -->
    +## Concise reporting (user-facing prose)
    +
    +Report to the user concisely. Lead with the OUTCOME. Begin a yes/no answer with `Yes.` or
    ```
    The `AGENT-PLANS` sibling and the closing wrapper are unchanged around it:
    ```text
     <!-- /aw:block -->

     <!-- AGENT-PLANS:BEGIN -->
    ```
- [x] V-03 validates E-03
  - Required evidence: Paste one generated OpenCode shim and one Claude shim in full, showing the one-line pointer, intact `agent: build` / `argument-hint:` frontmatter, and `$ARGUMENTS`. Paste the measured byte delta: `cat .opencode/commands/*.md .claude/commands/*.md | wc -c` before and after, with the increase within the stated budget (baseline 42,701 bytes). A result near +35KB means the prose was duplicated and V-03 FAILS.
  - Observed evidence: Both generated shims pasted in full below with the ONE pointer line, intact `agent: build` / `argument-hint:` frontmatter, and `$ARGUMENTS`. Measured corpus 42,709 -> 46,941 bytes (+4,232, ~88/file) versus +81,936 (+192%) for duplication, so V-03 PASSES.
  - Result: pass

    Evidence detail for V-03:

    Generated OpenCode shim in full (`.opencode/commands/plan-review.md`), showing the ONE pointer line, intact `agent: build` frontmatter, and `$ARGUMENTS`:
    ```text
    ---
    description: Pre-execution plan reviewer: review and improve a proposed implementation plan before any code is written (edits planning documents only). Single-file version.
    agent: build
    ---

    <!-- Deprecation notice: `/plan-review` is deprecated; prefer `/aw plan-review`. This alias continues to work for now but will eventually be pruned. -->

    Read and execute @.aw/system/workflows/plan-review/plan-review.md.

    If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

    Treat the referenced file as the controlling instruction and follow it fully.
    Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
    ```
    Generated Claude shim in full (`.claude/commands/plan-review.md`), showing `argument-hint:` and NO `agent:`:
    ```text
    ---
    description: Pre-execution plan reviewer: review and improve a proposed implementation plan before any code is written (edits planning documents only). Single-file version.
    argument-hint: "[optional target path or flags]"
    ---

    <!-- Deprecation notice: `/plan-review` is deprecated; prefer `/aw plan-review`. This alias continues to work for now but will eventually be pruned. -->

    Read and execute @.aw/system/workflows/plan-review/plan-review.md.

    If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

    Treat the referenced file as the controlling instruction and follow it fully.
    Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
    ```
    Measured byte delta (baseline 42,701 stated in the plan; the actual committed corpus at HEAD measured 42,709):
    ```text
    BEFORE:  $ for f in $(git ls-files .opencode/commands .claude/commands); do git show "HEAD:$f"; done | wc -c
    42709
    AFTER:   $ cat .opencode/commands/*.md .claude/commands/*.md | wc -c
    46941
    delta: 4232 bytes across 48 files = 88.2 per file
    ```
    Duplication would have cost `1707 x 48 = 81936` bytes (+192%). The measured +4,232 is 5% of that, so V-03 PASSES (a result near +35KB or worse would have failed it). Every added line across all 48 shims is the same single pointer:
    ```text
    $ git diff -- .opencode/commands .claude/commands | grep "^+" | grep -v "^+++" | sort -u
    +Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
    ```
    Host grammar validated programmatically for all 48 (in `ShimPointerTests::test_host_grammars_are_preserved`, part of the 12 passing tests pasted under V-08).
- [x] V-04 validates E-04
  - Required evidence: Pasted prompt-builder test output proving the contract text appears in `build_prompt` AND `build_verifier_prompt` output for BOTH drivers, plus assertions that required JSON keys, actual-output evidence requirements, lifecycle rules, and `pushed: false` are still present. Include a parity assertion showing both drivers import from `reporting_contract.py` rather than embedding a literal.
  - Observed evidence: `pytest ...DriverPromptTests ...ParityTests ...PrecedenceTests ...DocumentationTests` -> `20 passed`; contract reaches `build_prompt` AND `build_verifier_prompt` in BOTH drivers with all required JSON keys, evidence rules, and `pushed: false` retained; both drivers import the module and contain zero copies of the prose. Full output below.
  - Result: pass

    Evidence detail for V-04:

    `python3 -m pytest tests/test_reporting_contract.py::DriverPromptTests tests/test_reporting_contract.py::ParityTests tests/test_reporting_contract.py::PrecedenceTests tests/test_reporting_contract.py::DocumentationTests -o addopts="" -q`:
    ```text
    ....................                                                     [100%]
    20 passed in 0.24s
    ```
    Direct reachability check across all four prompt surfaces:
    ```text
    $ python3 -c "
    from agent_workflows import oc_runipd, agy_runipd
    from pathlib import Path
    item={'position':1,'id6':'abc123','setid':'demo','attempts':[]}; state={'run_id':'run-x','repo':'.'}
    for mod in (oc_runipd, agy_runipd):
        p=mod.build_prompt(item,state,Path('/tmp/run'),Path('/tmp/plan.md'),False)
        v=mod.build_verifier_prompt(item,state,Path('/tmp/run'),Path('/tmp/plan.md'))
        r=mod.build_review_prompt(item,state,Path('/tmp/run'),Path('/tmp/plan.md'),Path('/tmp'))
        print(mod.__name__,'exec:', '## Concise reporting' in p, 'verifier:', '## Concise reporting' in v, 'review:', repr(r))"
    agent_workflows.oc_runipd exec: True verifier: True review: '/plan-review plan.md'
    agent_workflows.agy_runipd exec: True verifier: True review: '/plan-review plan.md'
    ```
    `test_execution_prompts_retain_required_json_keys_and_rules` asserts each execution prompt still carries `"schema_version": 1`, `"disposition"`, `"files_changed"`, `"tests"`, `"decision_ids"`, `"deferred_question_ids"`, `"incomplete_requirements"`, `"recommended_next_action"`, `"pushed": false`, `## Concurrent Work`, `git diff --cached --name-only`, and `path-scoped`. `test_verifier_prompts_retain_evidence_requirements` asserts the verdict enum, "Paste the actual runner output with exit code.", the Evidence Table section, and the closing line. `test_prompts_are_pure_ascii` passes for all four.

    Parity assertion that both drivers IMPORT rather than embed a literal (`test_drivers_import_the_module_rather_than_inlining_the_prose`):
    ```text
    $ grep -n "reporting_contract" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py | grep -v "^.*#"
    agent_workflows/oc_runipd.py:45:from agent_workflows import reporting_contract
    agent_workflows/oc_runipd.py:2974:{reporting_contract.prompt_block()}"""
    agent_workflows/oc_runipd.py:3043:{reporting_contract.prompt_block()}"""
    agent_workflows/agy_runipd.py:52:from agent_workflows import reporting_contract
    agent_workflows/agy_runipd.py:2406:{reporting_contract.prompt_block()}"""
    agent_workflows/agy_runipd.py:2475:{reporting_contract.prompt_block()}"""
    $ grep -c "Report to the user concisely." agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:0
    agent_workflows/agy_runipd.py:0
    ```
- [x] V-05 validates E-05
  - Required evidence: Paste the actual return value of `build_review_prompt(...)` from both drivers, showing it matches `^/plan-review \S+$` with no trailing prose, plus the passing test that enforces that regex. Also paste `git diff` for the two `build_review_prompt` functions showing NO functional change to the returned string.
  - Observed evidence: Both drivers return exactly `/plan-review plans/plan.ipd.md`, matching `^/plan-review \S+$`; the `git diff` for both functions shows docstring-only additions with the returned expression untouched. Full output below.
  - Result: pass

    Evidence detail for V-05:

    Actual return values from both drivers, matching `^/plan-review \S+$` with no trailing prose:
    ```text
    $ python3 -c "
    import re
    from agent_workflows import oc_runipd, agy_runipd
    from pathlib import Path
    item={'position':1,'id6':'abc123','setid':'demo','attempts':[]}; state={'run_id':'run-x','repo':'.'}
    for mod in (oc_runipd, agy_runipd):
        v=mod.build_review_prompt(item,state,Path('/tmp/run'),Path('/tmp/repo/plans/plan.ipd.md'),Path('/tmp/repo'))
        print(mod.__name__, repr(v), bool(re.match(r'^/plan-review \\S+$', v)))"
    agent_workflows.oc_runipd '/plan-review plans/plan.ipd.md' True
    agent_workflows.agy_runipd '/plan-review plans/plan.ipd.md' True
    ```
    The enforcing test is `DriverPromptTests::test_review_prompt_is_exactly_the_slash_command` (passing, in the 20 above); it asserts the regex, the exact expected string, and the absence of contract prose.

    `git diff` for the two `build_review_prompt` functions, showing NO functional change to the returned string (docstring additions only; the `return f"/plan-review {rel_path}"` line and the `try/except ValueError` body are untouched):
    ```text
    @@ agent_workflows/agy_runipd.py: def build_review_prompt(
         repo: Path,
     ) -> str:
    +    """Return EXACTLY the slash command for a review turn: `/plan-review <relative path>`.
    +
    +    Deliberately prose-free (terseout `ntf6sx` E-05), symmetric with the OpenCode driver. The
    +    value is one argv element, so appended prose would be consumed as the slash command's
    +    `$ARGUMENTS`. The review turn inherits the concise-reporting contract from the generated
    +    command shim's pointer plus the installed `AGENTS.md#aw:reporting` section.
    +    """
    +
         try:
             rel_path = str(plan_path.relative_to(repo))
         except ValueError:

    @@ agent_workflows/oc_runipd.py: def build_review_prompt(
         repo: Path,
     ) -> str:
    +    """Return EXACTLY the slash command for a review turn: `/plan-review <relative path>`.
    +
    +    Deliberately prose-free (terseout `ntf6sx` E-05). This value is handed to the host as ONE
    +    argv element after `--`, so anything appended to it is absorbed by the slash command's
    +    `$ARGUMENTS` and parsed as additional path arguments. Never append instructions here; the
    +    review turn inherits the concise-reporting contract from the generated command shim's
    +    pointer line plus the installed `AGENTS.md#aw:reporting` section. If a future change truly
    +    must add prose to a review turn, it goes on a separate line AFTER the command, never on
    +    the command line itself.
    +    """
    +
         try:
             rel_path = str(plan_path.relative_to(repo))
         except ValueError:
    ```
    No `+`/`-` line in either diff touches the returned expression.
- [x] V-06 validates E-06
  - Required evidence: Paste the contract text section covering precedence, plus a test asserting it names the required-report override explicitly. Then paste a reasoning check: quote the contract's override sentence next to `plan-review.md:492` ("MUST be the literal final output") and state why a model reading both produces the full report. Also paste the inverse assertion that brevity does not license skipping pasted runner output.
  - Observed evidence: Precedence paragraph pasted below with the passing `PrecedenceTests` (4 tests), the reasoning check placing the contract's override sentence beside `plan-review.md:39`, and the inverse assertion on pasted runner output.
  - Result: pass

    Evidence detail for V-06:

    The contract's precedence section, verbatim from `reporting_contract.contract_text()`:
    ```text
    PRECEDENCE (this default is not the top rule). An explicit user request, or a controlling
    workflow that specifies a required report, OVERRIDES the default. When a workflow mandates a
    report (for example `plan-review`'s findings table and the enumeration it calls "the literal
    final output", or `release-review`'s final report), produce that report IN FULL and do NOT
    apply the 100-word cap to it; be concise only in the prose around it.
    Brevity NEVER licenses truncating a mandated report, and it NEVER licenses skipping the
    ACTUAL runner output the execution contract requires you to paste.
    ```
    The asserting tests (`PrecedenceTests`, 4 tests, in the 20 passing above) check: `PRECEDENCE` + `required report` + `IN FULL` + the exact `do NOT apply the 100-word cap to it` phrase; that it names `plan-review`, `literal final output`, and `release-review` concretely; the inverse guard (`NEVER licenses truncating a mandated report` and `ACTUAL runner output`); and that the quoted workflow rule STILL EXISTS in the repo, so the contract cannot silently quote a rule that has moved:
    ```text
    $ grep -n "literal final output" .aw/system/workflows/plan-review/plan-review.md
    39:8. The reviewed/not-reviewed enumeration is the literal final output.
    ```
    Reasoning check, the two rules side by side:
    (a) `plan-review.md:39` says: "The reviewed/not-reviewed enumeration is the literal final output."
    (b) the contract says: "When a workflow mandates a report ... produce that report IN FULL and do NOT apply the 100-word cap to it; be concise only in the prose around it."

    A model reading both produces the full enumeration because the contract does not merely permit the longer output, it SCOPES ITSELF OUT of that output: the cap is declared inapplicable to a workflow-specified report, and the sentence immediately after removes the remaining ambiguity by naming truncation of a mandated report as never licensed. The residual instruction the model can still act on is "be concise only in the prose AROUND it", which is satisfiable without shortening the report. The inverse assertion covers the other failure direction (dropping pasted runner output to look terse) with "it NEVER licenses skipping the ACTUAL runner output the execution contract requires you to paste."

    Note: the contract heading level is `##` deliberately, so the same bytes read correctly both as a managed section inside an instruction file and as a section of a driver prompt.
- [x] V-07 validates E-07
  - Required evidence: Pasted focused test output naming the tests for contract completeness, single `aw:reporting` section, idempotence, foreign-prose preservation, absent-native behavior, AND the two first-time-exercised consent paths: a `declined` tombstone for `AGENTS.md#aw:reporting` omitting the section, and a user-edited `aw:reporting` body being preserved rather than clobbered.
  - Observed evidence: `pytest -v` names all 14 installer/section tests below, including the two FIRST-TIME-EXERCISED consent paths: a `declined` tombstone omits `aw:reporting` while `aw:pointer` survives, and a user-edited body is preserved not clobbered.
  - Result: pass

    Evidence detail for V-07:

    `python3 -m pytest tests/test_reporting_contract.py -o addopts="" -v` (relevant subset; full run below under V-09). The 14 `ManagedSectionTests`+`InstallerSafetyTests` results pasted under V-02 include, by name:
    ```text
    tests/test_reporting_contract.py::InstallerSafetyTests::test_fresh_install_writes_exactly_one_reporting_section PASSED
    tests/test_reporting_contract.py::InstallerSafetyTests::test_second_install_is_byte_idempotent PASSED
    tests/test_reporting_contract.py::InstallerSafetyTests::test_existing_native_files_get_the_section_with_foreign_prose_preserved PASSED
    tests/test_reporting_contract.py::InstallerSafetyTests::test_absent_native_files_are_still_not_created PASSED
    tests/test_reporting_contract.py::InstallerSafetyTests::test_foreign_sibling_block_stays_byte_identical PASSED
    tests/test_reporting_contract.py::InstallerSafetyTests::test_declined_reporting_section_is_omitted_but_pointer_stays PASSED
    tests/test_reporting_contract.py::InstallerSafetyTests::test_user_edited_reporting_body_is_preserved_not_clobbered PASSED
    tests/test_reporting_contract.py::InstallerSafetyTests::test_manifest_records_the_new_section_hash_as_an_install_side_effect PASSED
    tests/test_reporting_contract.py::ManagedSectionTests::test_two_sections_are_emitted_pointer_then_reporting PASSED
    tests/test_reporting_contract.py::ManagedSectionTests::test_rendered_block_carries_exactly_one_reporting_marker PASSED
    tests/test_reporting_contract.py::ManagedSectionTests::test_reporting_body_is_the_contract_verbatim PASSED
    tests/test_reporting_contract.py::ManagedSectionTests::test_block_round_trips_through_the_parser PASSED
    tests/test_reporting_contract.py::ManagedSectionTests::test_slug_constant_comes_from_the_contract_module PASSED
    tests/test_reporting_contract.py::ManagedSectionTests::test_this_repos_agents_md_carries_the_section_inside_the_block PASSED
    ```
    The two FIRST-TIME-EXERCISED consent paths are covered explicitly, and each asserts the sibling is unaffected:
    - `test_declined_reporting_section_is_omitted_but_pointer_stays` writes a `declined` tombstone for `AGENTS.md#aw:reporting`, reinstalls, and asserts `<!-- aw:reporting -->` is ABSENT while `<!-- aw:pointer -->` is still present (declining one sibling must not drop the other).
    - `test_user_edited_reporting_body_is_preserved_not_clobbered` replaces the section body with "MY OWN REPORTING RULE: be as verbose as you like.", reinstalls, and asserts the user's text SURVIVES, the generated sentence does NOT return, and the sibling `aw:pointer` is still refreshed normally.

    `test_manifest_records_the_new_section_hash_as_an_install_side_effect` proves the manifest gains `AGENTS.md#aw:reporting` through `manifest.record(...)` during a normal install, confirming E-09's scope correction (the hash is an install side effect, not a hand-regenerated map).
- [x] V-08 validates E-08
  - Required evidence: Pasted output of the full focused regression set, including the parity test, the `build_review_prompt` exact-match test, and the shim budget test. Also paste a NEGATIVE demonstration: temporarily duplicate the prose into a shim (or mutate one rendered copy) and show the parity/budget test FAILING, then show it passing after revert. A guard never observed failing is not proven.
  - Observed evidence: `pytest tests/test_reporting_contract.py` -> `53 passed`. BOTH guards were OBSERVED FAILING under injected regressions (budget: `123105 not less than or equal to 50381`; parity: 5 failures on a paraphrased copy) and passing after revert. Full output below.
  - Result: pass

    Evidence detail for V-08:

    Full focused regression set:
    ```text
    $ python3 -m pytest tests/test_reporting_contract.py -o addopts="" -q
    .....................................................                    [100%]
    53 passed in 17.18s
    ```
    Includes the parity tests, the `build_review_prompt` exact-match test, and the shim budget test (all named in the `-v` listing under V-01/V-02/V-04/V-07).

    NEGATIVE DEMONSTRATION 1, budget/pointer guards. Injected the exact regression E-03 forbids by swapping `shim_pointer_line()` for `contract_text()` in `shim_body`:
    ```text
    $ python3 -m pytest tests/test_reporting_contract.py -o addopts="" -q
    FAILED tests/test_reporting_contract.py::ShimPointerTests::test_no_shim_embeds_the_full_contract_prose
    FAILED tests/test_reporting_contract.py::ShimPointerTests::test_shim_corpus_size_budget
    FAILED tests/test_reporting_contract.py::ShimPointerTests::test_pointer_bearing_shim_is_not_flagged_as_user_customized
    FAILED tests/test_reporting_contract.py::ShimPointerTests::test_every_generated_shim_carries_the_pointer
    4 failed, 49 passed in 19.82s

    E       AssertionError: 123105 not less than or equal to 50381 : shim corpus is 123105 bytes
            across 48 files, over the 50381-byte ceiling (baseline 42701 + 160/file). The contract
            prose was probably duplicated into the shims; E-03 requires a pointer.
    ```
    After revert:
    ```text
    $ python3 -m pytest tests/test_reporting_contract.py -o addopts="" -q
    .....................................................                    [100%]
    53 passed in 17.26s
    ```
    NEGATIVE DEMONSTRATION 2, parity guards. Injected a hand-maintained PARAPHRASE into `agy_runipd`'s execution prompt ("Report to the user concisely. Lead with a preamble if you like.") instead of calling the module:
    ```text
    $ python3 -m pytest tests/test_reporting_contract.py -o addopts="" -q
    FAILED tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose
    FAILED tests/test_reporting_contract.py::ParityTests::test_all_prose_surfaces_are_byte_equal_to_the_source
    FAILED tests/test_reporting_contract.py::ParityTests::test_drivers_import_the_module_rather_than_inlining_the_prose
    FAILED tests/test_reporting_contract.py::ContractSourceTests::test_no_second_independently_maintained_production_copy
    FAILED tests/test_reporting_contract.py::DriverPromptTests::test_execution_prompts_carry_the_contract
    5 failed, 48 passed in 17.37s
    ```
    After revert:
    ```text
    $ python3 -m pytest tests/test_reporting_contract.py -o addopts="" -q
    .....................................................                    [100%]
    53 passed in 17.26s
    ```
    Both guards have therefore been OBSERVED FAILING and then passing, so neither is an unproven assertion. A third guard, `test_budget_guard_actually_fails_on_duplication`, keeps a synthetic version of demonstration 1 in the suite permanently.

    Pre-existing tests updated (not weakened) for the new shim tail, per decision 01-ntf6sx-D1:
    ```text
    $ python3 -m pytest tests/test_command_shims.py tests/test_installer.py -m ''
    148 passed in 37.45s   (test_installer.py)
    9 passed              (test_command_shims.py, in the combined run below)
    ```
- [x] V-09 validates E-09
  - Required evidence: Pasted `git diff --check`; the generated-artifact/no-drift check for `AGENTS.md` and the OpenCode/Claude shims (NOT a hand-regenerated `managed-sections.json`, which is out of scope); a search showing docs point to `agent_workflows/reporting_contract.py` without forking its prose; `python3 -m pytest -p no:randomly` with exit 0 and the actual summary line; and `aw sanitize --agent` clean. If live smokes run, paste host/model/version and measured response shape; otherwise state `not run` without weakening deterministic acceptance.
  - Observed evidence: `git diff --check` exit 0; zero shim drift versus the generator; `AGENTS.md` contains the generated block verbatim; docs point at the module with zero forked prose; `aw sanitize --agent` clean. Full suite `15 failed, 3628 passed`, where all 15 are PRE-EXISTING `test_run_viewer` failures proven unrelated two ways. Live smoke matrix NOT RUN. Full output below.
  - Result: pass

    Evidence detail for V-09:

    `git diff --check`:
    ```text
    $ git diff --check; echo "exit=$?"
    exit=0
    ```
    Generated-artifact / no-drift check for `AGENTS.md` and the shims. The tracked artifacts equal what the generator produces (the `--dry-run` reports the pointer block already current, and the byte-level regeneration is a no-op):
    ```text
    $ python3 -c "
    from agent_workflows import engine as E
    from tests.support import SOURCE_WORKFLOWS
    from pathlib import Path
    wfs=E.parse_manifest(SOURCE_WORKFLOWS)
    gen=E.generate_shim_members(wfs, SOURCE_WORKFLOWS, target_layout='aw')
    drift=[r for r,c in gen.items() if Path(r).is_file() and Path(r).read_text()!=c]
    print('shim drift vs generator:', drift)
    blk=E.agents_managed_block(target_layout='aw')
    txt=Path('AGENTS.md').read_text()
    print('AGENTS.md contains the generated block verbatim:', blk.strip('\n') in txt)"
    shim drift vs generator: []
    AGENTS.md contains the generated block verbatim: True
    ```
    (NOT a hand-regenerated `managed-sections.json`: out of scope, and its `managed_sections` map remains the reserved, unpopulated `{}`.)

    Docs point at the source without forking its prose:
    ```text
    $ grep -n "reporting_contract.py" docs/reporting-contract.md | head -3
    13:agent_workflows/reporting_contract.py
    $ grep -c "Report to the user concisely." docs/reporting-contract.md README.md CHANGELOG.md DECISIONS.md
    docs/reporting-contract.md:0
    README.md:0
    CHANGELOG.md:0
    DECISIONS.md:0
    $ python3 -c "
    from agent_workflows import docs_check as dc; from pathlib import Path
    print('doc findings:', dc.check_doc(Path('docs/reporting-contract.md')))"
    doc findings: []
    ```
    Full suite:
    ```text
    $ python3 -m pytest
    15 failed, 3628 passed, 3 skipped, 4 xfailed in 29.26s
    ```
    The 15 failures are ALL `tests/test_run_viewer.py` and are PRE-EXISTING, cwd-dependent, and unrelated to this plan. Proven two ways. (1) A pristine copy of HEAD in a separate directory fails the SAME 15 with none of this plan's changes present:
    ```text
    $ cd /tmp/opencode/ntf6sx-head && python3 -m pytest tests/test_run_viewer.py
    15 failed, 30 passed in 2.21s
    ```
    (2) Stashing this plan's entire change set in the worktree reproduces the same 15:
    ```text
    $ git stash push -u -- agent_workflows tests docs AGENTS.md .opencode .claude
    $ python3 -m pytest tests/test_run_viewer.py
    15 failed, 21 passed in 2.06s
    $ git stash pop
    ```
    Every failure message is `AssertionError: ... not found in 'no matching runs found'` (the test expects run records discoverable from the process cwd). This plan touches no run-viewer code and adds no run records. HONEST STATEMENT: the suite is NOT green; it is green on everything this plan affects, with the 15 unrelated failures unchanged in count and identity before and after.

    Targeted confirmation of the affected areas, all passing:
    ```text
    $ python3 -m pytest tests/test_command_shims.py tests/test_migration_compact_shims.py tests/test_exec_set_workflow.py tests/test_shared_checkout_contract.py tests/test_agent_contract_test_invocation.py tests/test_docs.py tests/test_reporting_contract.py
    142 passed in 6.13s

    $ python3 -m pytest tests/test_installer.py -m ''
    148 passed in 37.45s
    ```
    Leak sanitizer:
    ```text
    $ aw sanitize --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    exit=0
    ```
    PRECONDITION REPAIR disclosed (decision 01-ntf6sx-D4, NOT part of this plan's design): the
    `pre-commit` `ruff` hook rejected every commit touching `agent_workflows/agy_runipd.py` on 12
    PRE-EXISTING `F821 Undefined name` errors (`checkpoint_observer` x7, `observer` x5), reproduced
    identically in a pristine copy of HEAD. Since E-04 must edit that file, the plan could not be
    committed at all until they were resolved. `oc_runipd` binds BOTH `observer` and
    `checkpoint_observer`; `agy_runipd` binds ONLY `checkpoint_observer` (its own comment says agy
    needs no progress observer), and only `CheckpointObserver` carries the attributes every call
    site uses, so the binding was mechanically determined, not designed. Falsifiably safe:
    ```text
    $ comm -23 before.txt after.txt        # fail -> pass
    FAILED tests/test_runner_stop_level3.py::AgyDriverParityTests::test_agy_stops_at_its_own_step_update_done_checkpoint
    FAILED tests/test_runner_stop_level4.py::AgyDriverParityTests::test_agy_is_cut_immediately_and_records_the_same_indeterminacy
    $ comm -13 before.txt after.txt        # pass -> fail (regressions)
    (none)
    $ wc -l < before.txt; wc -l < after.txt
    21
    19
    ```
    The 19 remaining `runner_stop` failures are a pre-existing defect in the runstop Set that this
    plan did NOT touch and does NOT claim to fix.

    Live smoke matrix: NOT RUN. This turn is a non-interactive driver turn with no separate host credentials to exercise OpenCode, Codex CLI, a Claude command, and Agy independently, and the plan's execution contract item 7 requires that an unavailable host be recorded as `not run` rather than `pass`. Deterministic acceptance is unaffected: reachability is proven byte-wise above; model OBEDIENCE is explicitly not claimed.


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
