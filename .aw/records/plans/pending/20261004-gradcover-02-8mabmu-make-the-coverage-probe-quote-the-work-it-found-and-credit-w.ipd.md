# IPD: Make the coverage probe quote the work it found and credit work assigned to a named child

- Date: 2026-10-04
- Kind: child
- Concern: The orchestrator coverage probe answers with one bare sentinel line, so every refusal says only that an orchestrator "carries work no child covers" and never which sentence. On 2026-10-03 it refused 13 orchestrators and none of the refusals was actionable. It also refuses work the orchestrator explicitly assigns to a named child: `axozpe`'s `Scope check` and `Required tests / validation` sections state that Order 04 `rlhmt9` carries the final cross-child measurement, and the probe still answered "contains executions". The prompt (`runner_shared.PROBE_PROMPT_TEMPLATE`) lists "runs a repo-wide suite, performs a whole-Set verification" as uncovered work with no exception for an assigned owner, and says "any doubt resolves to CONTAINS EXECUTIONS". Spec `25kzda` 2.5b as amended by Order 01 (`hm1h3l`, A.3 and A.4) now requires a verdict plus verbatim quotes and the named-child credit rule.
- Scope: Change the probe's prompt, its reply parser, its verdict store entry, and its refusal rendering. IN: `PROBE_PROMPT_TEMPLATE` (answer format plus the named-child rule), `classify_probe_reply` (verdict plus `QUOTE:` lines, each validated against the excerpt), a new structured result carrying the quotes, `record_probe_verdict`/`read_probe_verdict` storing and returning quotes (schema version bumped, old entries read as misses), `ProbeOutcome` carrying quotes, and `format_orchestrator_probe_refusal`/`probe_refusal_remedy`/the recorded refusal reason rendering them; `aw runs` already renders the recorded refusal, so it shows the quotes without a change. OUT: which orchestrators are probed and when (Order 04); any status-change, lint or production consumer (Orders 03, 05, 06); the excerpt's section allowlist (`PROBE_PROSE_SECTIONS`, unchanged); the could-not-ask retry rule; the cache digest inputs.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_orchestrator_probe_quotes.py
- Item-Dependencies: executed:hm1h3l
- Status: to-review
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8mabmu

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 02 of Set `gradcover`. Implements spec `25kzda` Section 2.5b bullets A.3 (verdict plus verbatim quotes) and A.4 (named-child credit) as amended by Order 01.

## Goal

Make every coverage-probe refusal name the exact passages the model judged uncovered, and stop the probe reporting work that the orchestrator assigns by id6 to a child in its own child table, without making the parser any less strict about an unusable answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the answer contract

- [ ] E-01 Rewrite `PROBE_PROMPT_TEMPLATE` so the model (a) answers with the verdict sentinel on the first line, (b) when the verdict is "contains executions", follows it with one `QUOTE: <verbatim passage>` line per uncovered obligation copied exactly from the excerpt, (c) is told that an obligation the excerpt assigns by id6 to a child listed in the `### Child IPDs table` section of the excerpt is COVERED and must not be quoted, and (d) is told that assignment to an unnamed "later child", to a plan outside the table, or to the orchestrator itself does not count. Keep the existing "a checklist naming the children is expected" paragraph and keep the "doubt resolves to contains executions" rule, now scoped to obligations with no named owner.
  - Depends on: none
  - Expected outcome: `render_probe_prompt` output contains the `QUOTE: ` format instruction, the named-child rule, and both sentinels from the same constants the parser uses.
  - Execution state: pending

- [ ] E-02 Replace `classify_probe_reply`'s return with a structured result (verdict state plus a tuple of validated quotes) and make it strict in the new shape: first non-empty line must equal one sentinel; after "contains no executions" any further non-empty line is `unknown`; after "contains executions" every further non-empty line must start `QUOTE: ` and its text must occur in the excerpt after collapsing runs of whitespace, and at least one valid quote is required, else `unknown`; both sentinels anywhere is `unknown`; empty reply or transport failure stays `could-not-ask`. Thread the excerpt into the classifier through `ask_orchestrator_probe`. Keep a thin compatibility accessor so existing callers that only need the state keep working.
  - Depends on: E-01
  - Expected outcome: the classifier returns `executions` with quotes for a well-formed positive answer, `no-executions` for the bare negative sentinel, and `unknown` for a positive answer with zero valid quotes, a quote not in the excerpt, a trailing line after the negative sentinel, or both sentinels.
  - Execution state: pending

### Task group 2: carry the quotes through

- [ ] E-03 Store quotes with the verdict. Add a `quotes` list to each verdict-store entry written by `record_probe_verdict`, return it from `read_probe_verdict` on `ProbeVerdict`, bump `PROBE_VERDICT_STORE_SCHEMA_VERSION`, and make an entry written under the previous schema read as a miss (`unreadable-entry`) so no pre-change verdict is served (every old verdict was produced by the old prompt and has no quotes). Add `quotes` to `ProbeOutcome` and populate it from both a live answer and a cache hit.
  - Depends on: E-02
  - Expected outcome: a recorded `fail` verdict round-trips its quotes through the store; an old-schema entry is a miss; a `pass` entry carries an empty quote list.
  - Execution state: pending

- [ ] E-04 Render the quotes. Make the refusal reason recorded by `enforce_orchestrator_probe_gate` (and so shown by `aw runs` and the run summary), `format_orchestrator_probe_refusal`, and `probe_refusal_remedy` list, per blocking orchestrator, each quoted passage (truncated to a stated bound with an ellipsis, path-free) and the remedy "assign this obligation by id6 to a child in the `## Child IPDs` table, or add a child that performs it and a row for it; do not delete the checklist". An `unknown` outcome renders "the probe's answer was unusable" and the raw first line, bounded.
  - Depends on: E-03
  - Expected outcome: a refused run's `state.json` refusal reason and the terminal text both contain each quote and the orchestrator id6 it belongs to.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_orchestrator_probe_quotes.py` driving the real functions with an injected `asker`/`runner` double (never a real model): the classifier cases of E-02 as a table; a store round-trip and old-schema miss for E-03; an end-to-end `enforce_orchestrator_probe_gate` call over a fixture repo with one orchestrator whose fake host answers with a positive sentinel and one valid quote, asserting the quote appears in the recorded refusal and in the returned message; and a named-child fixture (an orchestrator whose `Required tests / validation` says "Order 02 `<child-id6>` carries the final measurement", with that child in its table) whose fake host is a scripted double that checks the rendered prompt contains the child table and the named-child rule, then answers negatively, asserting the gate proceeds. Prove the test can fail by reverting E-02's quote validation and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation run fails it; no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PROMPT AND THE PARSER SHARE CONSTANTS. `PROBE_SENTINEL_EXECUTIONS` and `PROBE_SENTINEL_NO_EXECUTIONS` are named so "the PROMPT and the PARSER must not drift" (the comment above them); the `QUOTE: ` prefix must be a third named constant used by both.
- THE REAL MODEL SPAWN IS UNREACHABLE FROM TESTS BY CONSTRUCTION. `_assert_probe_spawn_is_permitted` raises under `PYTEST_CURRENT_TEST`; every test injects `runner` or `asker`.
- THE CACHE KEY IS UNCHANGED. `probe_cache_digest` covers `probe_cache_payload`; this plan changes the prompt and the stored value, not the key. The schema bump is what invalidates old answers, because they were produced by a prompt that could not quote.
- `runner_shared` HAS A PINNED IMPORT SET. `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared` asserts the module-level first-party imports by set equality; any new import must be function-local.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16; `tests/test_no_code_structure_pins.py`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The reply contract is a bare line. `PROBE_PROMPT_TEMPLATE` says "Reply with EXACTLY ONE of these two lines and NOTHING else", and `classify_probe_reply` returns `executions` only when `text == PROBE_SENTINEL_EXECUTIONS`. No finding text is ever available to render. | the quoted template sentence; `classify_probe_reply`'s equality tests |
| F-02 | The refusal reason is generic. `enforce_orchestrator_probe_gate` builds `reason` as "the orchestrator coverage probe reports that <ids> carry work no child covers..." and `format_orchestrator_probe_refusal` lists only ids. The 2026-10-03 `state.json` refusal records for `axozpe`, `m0kl28`, `xhr0dj` carry exactly that text and nothing else. | `run-20261003T172049Z-3698977/state.json` queue items' refusal `code: orchestrator-uncovered-work` and `reason` text |
| F-03 | The prompt has no named-owner exception. Its "WHAT *IS* WORK" paragraph lists "runs a repo-wide suite, performs a whole-Set verification or audit" unconditionally, and its hard-case rule is "any doubt resolves to CONTAINS EXECUTIONS". `axozpe`'s excerpt (rendered with `orchestrator_probe_excerpt` 2026-10-03) includes "THE SET IS ONLY DEMONSTRATED COMPLETE BY A FINAL CROSS-CHILD MEASUREMENT, which Order 04 carries as the last child rather than this plan performing it", and the probe failed it. | the quoted prompt paragraphs; the rendered excerpt; the store entry recorded 2026-10-03 for `axozpe`'s digest with `verdict: fail` |
| F-04 | The excerpt already contains the child table first (`### Child IPDs table (row cells, in document order)`), so the named-child rule needs no payload change, only a prompt instruction. | `orchestrator_probe_excerpt` renders `child_table_rows` under that heading |
| F-05 | The store has a schema version and a reader that already treats unusable entries as misses (`PROBE_STALE_CORRUPT`). Bumping the version is the supported way to retire every old answer. 46 entries exist at authoring; 13 `fail` since 2026-10-02. | `PROBE_VERDICT_STORE_SCHEMA_VERSION`; `read_probe_verdict` docstring rule 1; a count of `.aw/state/runtime/orchestrator-probe-verdicts.json` entries by verdict and date |

## Proposed changes (ordered, validatable)

1. Add a `PROBE_QUOTE_PREFIX = "QUOTE: "` constant and rewrite the template's ANSWER FORMAT and add a NAMED-OWNER paragraph (E-01).
2. Make the classifier return verdict plus validated quotes, strict in the new shape, with the excerpt threaded in (E-02).
3. Store and serve quotes; bump the store schema (E-03).
4. Render quotes in the recorded refusal and the terminal text (E-04).
5. Pin it with fake-host tests and a mutation proof (E-05).

## Deferred / out of scope (with reason)

- WHICH ORCHESTRATORS THE RUN PROBES. Order 04.
  - Carrier: 5etev3
- USING THE QUOTES IN A STATUS SETTER, LINT RULE OR PRODUCTION CHECK. Orders 03, 05, 06.
  - Carrier: qs00nc
- WIDENING OR NARROWING `PROBE_PROSE_SECTIONS`. The named-child rule addresses the false refusals without changing what is sent; changing the allowlist would also move every digest for an unmeasured benefit.
  - Carrier-Declined: no measured defect in the allowlist itself

## Scope check

- Over-scope: none. One production module and one new test file.
- Under-scope: after this plan the probe still runs on review-only runs; that is Order 04. A reader must not conclude the 2026-10-03 symptom is fixed by this plan alone.
- The schema bump discards every cached verdict once. Measured cost: one model call per pending orchestrator the next time each is probed (16 at authoring).

## Required tests / validation

- Baseline: run `python3 -m pytest` BARE on a clean tree before editing; record the failing node ids.
- `python3 -m pytest -o addopts="" tests/test_orchestrator_probe_quotes.py tests/test_orchestrator_probe_payload.py tests/test_orchestrator_shape_gate.py tests/test_orchestrator_shape_composed.py tests/test_orchestrator_retirement.py -q` pasted.
- The mutation run for E-05, pasted failing then passing.
- `python3 -m pytest` BARE after the change, pasted with its `N passed` line, judged by the delta of failing node ids.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` Section 2.5b as amended by Order 01 (A.3, A.4) and spec `r07vma` R9 as amended (C.1). No spec is edited here. The docstrings of the changed functions are updated to state the new contract; no user-facing document describes the probe's answer format.

## Open questions

### OQ-01: Should quote validation be exact substring or whitespace-normalized?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: whitespace-normalized substring (collapse every run of whitespace to one space on both sides, then substring). The excerpt is rendered with wrapped prose and table pipes, and a model copying a passage across a line break would fail an exact match while being faithful. Anything looser (case folding, fuzzy matching) would let a paraphrase pass as a quote, which defeats the point of requiring evidence.

### OQ-02: Should a positive verdict with zero valid quotes block or be treated as could-not-ask?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: BLOCK as `unknown`. The answer was delivered, so it is not an availability failure; `25kzda` 2.5b already rules that a delivered but unusable answer blocks. Treating it as could-not-ask would let a model that refuses to quote silently warn past the gate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `PROBE_PROMPT_TEMPLATE` and the new constant. Paste the output of `render_probe_prompt` over `axozpe`'s real excerpt (from `orchestrator_probe_excerpt`), showing the `QUOTE: ` instruction, the named-child paragraph, and both sentinels.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `classify_probe_reply` and `ask_orchestrator_probe`. Paste the test run of the classifier table showing each case's expected state: positive with one valid quote, positive with zero quotes, positive with a quote absent from the excerpt, negative alone, negative plus a trailing line, both sentinels, empty.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the store functions and the schema constant. Paste a test or REPL run recording a `fail` with two quotes and reading it back with both quotes; paste an old-schema entry reading as a miss with `stale_reason` `unreadable-entry`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the end-to-end test's captured refusal reason and returned message, each containing the fixture quote and the orchestrator id6, and paste the remedy text showing it names "assign ... by id6", "add a child", and forbids deleting the checklist.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test file passing with its count; paste the mutation (quote validation removed) failing it and the revert passing it; paste a grep for `inspect`, `ast.parse` and reads of `agent_workflows/*.py` in the new file returning nothing. Paste the BARE `python3 -m pytest` summary line reconciled against your own baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the two declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only the declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual test output. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`. Depends on `hm1h3l` executed (the amended spec text is the contract implemented here).
