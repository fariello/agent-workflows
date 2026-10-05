# IPD: Make the coverage probe quote the work it found and credit work assigned to a named child

- Date: 2026-10-04
- Kind: child
- Concern: The orchestrator coverage probe answers with one bare sentinel line, so every refusal says only that an orchestrator "carries work no child covers" and never which sentence. On 2026-10-03 it refused 13 orchestrators and none of the refusals was actionable. It also refuses work the orchestrator explicitly assigns to a named child: `axozpe`'s `Required tests / validation` section states "THE SET IS ONLY DEMONSTRATED COMPLETE BY A FINAL CROSS-CHILD MEASUREMENT, which Order 04 carries as the last child", and its `## Child IPDs` table maps Order 04 to `rlhmt9`, and the probe still answered "contains executions". (Note: that sentence names the child by ORDER NUMBER, not by id6; an id6-only credit rule would NOT have credited it.) The prompt (`runner_shared.PROBE_PROMPT_TEMPLATE`) lists "runs a repo-wide suite, performs a whole-Set verification" as uncovered work with no exception for an assigned owner, and says "any doubt resolves to CONTAINS EXECUTIONS". Spec `25kzda` 2.5b as amended by Order 01 (`hm1h3l`, A.3 and A.4) now requires a verdict plus verbatim quotes and the named-child credit rule. Separately, the answer is kept only in `.aw/state/runtime/orchestrator-probe-verdicts.json`, which git ignores and which expires after 30 days, so no other clone and no CI run can ever see it; the maintainer ruled on 2026-10-04 that the answer is stored in the plan itself, and `25kzda` 2.5e (added by Order 01) specifies the record.
- Scope: Change the probe's prompt, its reply parser, WHERE ITS ANSWER IS RECORDED, and its refusal rendering. IN: `PROBE_PROMPT_TEMPLATE` (answer format plus the named-child rule), `classify_probe_reply` (verdict plus `QUOTE:` lines, each validated against the excerpt), a new structured result carrying the quotes, a new module `agent_workflows/coverage_record.py` that reads and writes the coverage record IN THE PLAN (spec `25kzda` 2.5e: `- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:`, `## Coverage findings`, and the matching history line), `probe_orchestrator` reading and writing that record instead of the machine-local verdict store, retiring the store (`record_probe_verdict`, `read_probe_verdict` and their file are no longer used), excluding the record from `ipd_lifecycle.frozen_region_digest` and from the coverage fingerprint, the schema registering the three fields and the section, `ProbeOutcome` carrying quotes, and `format_orchestrator_probe_refusal`/`probe_refusal_remedy`/the recorded refusal reason rendering them; `aw runs` already renders the recorded refusal, so it shows the quotes without a change. OUT: which orchestrators are probed and when (Order 04); any status-change, lint or production consumer (Orders 03, 05, 06), including lint rule `IPD-M112` (Order 03); the excerpt's section allowlist (`PROBE_PROSE_SECTIONS`, unchanged); the could-not-ask retry rule; the fingerprint's inputs (the record stores the same `probe_cache_digest` the cache keyed on).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/coverage_record.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lifecycle.py, tests/test_orchestrator_probe_quotes.py, tests/test_coverage_record.py
- Item-Dependencies: executed:hm1h3l
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 2
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8mabmu

## Workflow history
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): revised after review. Maintainer ruling 2026-10-04: the coverage answer is stored in the plan (`25kzda` 2.5e). E-03 now writes that record (new `coverage_record` module) instead of extending the cache; new E-06 keeps the record out of both fingerprints; new E-07 switches the probe to the record and retires the cache.
- 2026-10-04 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-006. Store version made enforced on read and on write (PR-001); named-child credit extended to table Order numbers, since `axozpe` names its owner only as "Order 04" (PR-002, with `hm1h3l` A.4); partial-quote semantics aligned with spec A.3 (PR-003); `asker` 2-tuple compatibility and the shape-gate reason prefix preserved (PR-004); stale pinning-test citation corrected (PR-005); quote-copying instruction, tests and gate honesty (PR-006).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 02 of Set `gradcover`. Implements spec `25kzda` Section 2.5b bullets A.3 (verdict plus verbatim quotes) and A.4 (named-child credit) as amended by Order 01.

## Goal

Make every coverage-probe refusal name the exact passages the model judged uncovered, and stop the probe reporting work that the orchestrator assigns by id6 to a child in its own child table, without making the parser any less strict about an unusable answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the answer contract

- [ ] E-01 Rewrite `PROBE_PROMPT_TEMPLATE` so the model (a) answers with the verdict sentinel on the first line, (b) when the verdict is "contains executions", follows it with one `QUOTE: <verbatim passage>` line per uncovered obligation copied exactly from the excerpt, (c) is told that an obligation the excerpt assigns to a child listed in the `### Child IPDs table` section of the excerpt, naming that child by its id6 OR by an Order number that appears in the table's Order column (for example "Order 04 carries ..." when the table has a `04` row), is COVERED and must not be quoted, and (d) is told that assignment to an unnamed "later child", to a plan outside the table, or to the orchestrator itself does not count. Tell the model to copy each quote EXACTLY as it appears in the excerpt, including backticks, pipes and capitalization, on one line. Keep the existing "a checklist naming the children is expected" paragraph and keep the "doubt resolves to contains executions" rule, now scoped to obligations with no named owner.
  - Depends on: none
  - Expected outcome: `render_probe_prompt` output contains the `QUOTE: ` format instruction, the named-child rule, and both sentinels from the same constants the parser uses.
  - Execution state: pending

- [ ] E-02 Replace `classify_probe_reply`'s return with a structured result (verdict state plus a tuple of validated quotes) and make it strict in the new shape: first non-empty line must equal one sentinel; after "contains no executions" any further non-empty line is `unknown`; after "contains executions" every further non-empty line must start `QUOTE: ` (any other line makes the whole answer `unknown`); a `QUOTE:` line whose text does not occur in the excerpt after collapsing runs of whitespace is DISCARDED and counted, not fatal (spec `25kzda` 2.5b A.3: "A quote is valid only if ..." and "no valid quote ... is UNUSABLE"); at least one valid quote is required, else `unknown`; the discarded count is carried in the result so the refusal can say "N quoted line(s) did not match the excerpt and were discarded"; both sentinels anywhere is `unknown`; empty reply or transport failure stays `could-not-ask`. Thread the excerpt into the classifier through `ask_orchestrator_probe`. THE `asker` SEAM: `ask_orchestrator_probe` returns `(answer, detail, quotes)`; `probe_orchestrator` must also accept the existing 2-tuple `(answer, detail)` from an injected `asker` (treating quotes as empty), because the shipped doubles in `tests/test_orchestrator_shape_gate.py` and `tests/test_orchestrator_shape_composed.py` return 2-tuples and those files are not in this plan's scope. Orders 03 and 04 inject fake probes through the same seam and may return either shape.
  - Depends on: E-01
  - Expected outcome: the classifier returns `executions` with quotes for a well-formed positive answer, `no-executions` for the bare negative sentinel, and `unknown` for a positive answer with zero valid quotes, a quote not in the excerpt, a trailing line after the negative sentinel, or both sentinels.
  - Execution state: pending

### Task group 2: carry the quotes through

- [ ] E-03 Add `agent_workflows/coverage_record.py` implementing spec `25kzda` 2.5e: `read(plan_text)` returning the recorded verdict (`pass`/`fail`/absent), fingerprint, date, model and quotes, plus `is_current(plan_text)` comparing the stored fingerprint with `runner_shared.probe_cache_digest(plan_text)`; and `write(plan_path, verdict, quotes, model, tool)` that sets the three metadata fields (inserted after `- Status:` and any `- Readiness:`, replaced in place if present), replaces or removes the `## Coverage findings` section (present only on a fail, one bullet per quote, placed immediately before `## Validation and cross-check`), and appends the history line `- <date> coverage <pass|fail> (<tool>): fingerprint <first 12 hex>, model <model>`. All first-party imports function-local. Register `Coverage`, `Coverage-Fingerprint` and `Coverage-Checked` in `ipd_schema.META_RECOGNIZED` (optional, so no existing plan fails) and `## Coverage findings` as an optional section permitted in both kinds immediately before the validation section.
  - Depends on: E-02
  - Expected outcome: writing a `fail` with two quotes then reading it returns both quotes and `is_current` True; editing a checklist line makes `is_current` False; writing a `pass` removes the findings section; the plan still lints conforming after each write.
  - Execution state: pending

- [ ] E-06 Keep the record out of both fingerprints. Make `probe_cache_payload` (hence `probe_cache_digest`) ignore the coverage fields and the `## Coverage findings` section (they are metadata and a non-allowlisted section, so confirm by test rather than assume), and make `ipd_lifecycle.frozen_region_digest` unaffected by them. Write a test that records a coverage answer into a plan that has a begin receipt and asserts `receipt_is_current` is still True and `probe_cache_digest` is unchanged.
  - Depends on: E-03
  - Expected outcome: recording or rewriting a coverage answer changes neither the coverage fingerprint nor the execution-receipt fingerprint.
  - Execution state: pending

- [ ] E-07 Switch `probe_orchestrator` to the plan record and retire the store. A current `pass` or `fail` record is served with zero model calls (`cached=True`, quotes from the record); an absent or out-of-date record asks and then calls `coverage_record.write` with tool `aw <host> run`. `could-not-ask` and `unknown` write nothing. Stop calling `record_probe_verdict`/`read_probe_verdict`; delete them and `probe_verdict_store_path`'s callers in this module, or leave them unreferenced with a docstring stating they are retired by spec `25kzda` 2.5e (choose deletion if no other module imports them, and record which). Add `quotes` to `ProbeOutcome`. Because the run-start probe now WRITES the plan, note in the docstring that the write lands in the checkout the run started from and is committed by the run's existing record-commit path or left for the operator, and record which applies when measured.
  - Depends on: E-06
  - Expected outcome: a second run over an unchanged orchestrator spends zero model calls and reads its quotes from the plan; an edited orchestrator is asked again; the machine-local store file is no longer written.
  - Execution state: pending

- [ ] E-04 Render the quotes. Make the refusal reason recorded by `enforce_orchestrator_probe_gate` (and so shown by `aw runs` and the run summary), `format_orchestrator_probe_refusal`, and `probe_refusal_remedy` list, per blocking orchestrator, each quoted passage (truncated to a stated bound with an ellipsis, path-free) and the remedy "assign this obligation by id6 to a child in the `## Child IPDs` table, or add a child that performs it and a row for it; do not delete the checklist". An `unknown` outcome renders "the probe's answer was unusable" and the raw first line, bounded. KEEP the existing leading sentence of the recorded reason ("the orchestrator coverage probe reports that <ids> carr(y|ies) work no child covers") unchanged and APPEND the quotes after it, because `tests/test_orchestrator_shape_gate.py` asserts that prefix and is outside this plan's scope.
  - Depends on: E-07
  - Expected outcome: a refused run's `state.json` refusal reason and the terminal text both contain each quote and the orchestrator id6 it belongs to.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_orchestrator_probe_quotes.py` driving the real functions with an injected `asker`/`runner` double (never a real model): the classifier cases of E-02 as a table; in a second new file `tests/test_coverage_record.py`, the E-03 write/read/`is_current` cases and the E-06 two-fingerprints case; a second-run-is-free case for E-07 (asker call count 0) and an edited-plan-is-asked-again case; the 2-tuple `asker` double still working; an end-to-end `enforce_orchestrator_probe_gate` call over a fixture repo with one orchestrator whose fake host answers with a positive sentinel and one valid quote, asserting the quote appears in the recorded refusal and in the returned message; a partial-quote case (one valid, one invalid quote: `executions` with one quote and a discarded count of 1); and a named-child fixture (an orchestrator whose `Required tests / validation` says "Order 02 carries the final measurement", by Order number only, with that child in its table) whose fake host is a scripted double that checks the rendered prompt contains the child table and the named-child rule, then answers negatively, asserting the gate proceeds. Prove the test can fail by reverting E-02's quote validation and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation run fails it; no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PROMPT AND THE PARSER SHARE CONSTANTS. `PROBE_SENTINEL_EXECUTIONS` and `PROBE_SENTINEL_NO_EXECUTIONS` are named so "the PROMPT and the PARSER must not drift" (the comment above them); the `QUOTE: ` prefix must be a third named constant used by both.
- THE REAL MODEL SPAWN IS UNREACHABLE FROM TESTS BY CONSTRUCTION. `_assert_probe_spawn_is_permitted` raises under `PYTEST_CURRENT_TEST`; every test injects `runner` or `asker`.
- THE FINGERPRINT FUNCTION IS UNCHANGED. `probe_cache_digest` over `probe_cache_payload` becomes the value stored in `- Coverage-Fingerprint:`; it already covers exactly what the question reads and ignores checkbox, evidence and history edits.
- `- Readiness:` IS THE PRECEDENT for a tool-written attestation stored in the plan: recognized in `ipd_schema.META_RECOGNIZED`, optional, and defended by `ipd_lint.check_readiness_attestation` (`IPD-M107`). The coverage record follows the same pattern; Order 03 adds its lint defense (`IPD-M112`).
- KEEP NEW FIRST-PARTY IMPORTS IN `runner_shared` FUNCTION-LOCAL, as the module's probe section already does (`_probe_prose_sections` imports `ipd_schema` inside its body). The pinning test once cited for this, `tests/test_orchestrator_probe_cache.py`, no longer exists (removed by `19313eed7`, "test: trim test suite"); this is a convention, not a tested rule.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16; `tests/test_no_code_structure_pins.py`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The reply contract is a bare line. `PROBE_PROMPT_TEMPLATE` says "Reply with EXACTLY ONE of these two lines and NOTHING else", and `classify_probe_reply` returns `executions` only when `text == PROBE_SENTINEL_EXECUTIONS`. No finding text is ever available to render. | the quoted template sentence; `classify_probe_reply`'s equality tests |
| F-02 | The refusal reason is generic. `enforce_orchestrator_probe_gate` builds `reason` as "the orchestrator coverage probe reports that <ids> carry work no child covers..." and `format_orchestrator_probe_refusal` lists only ids. The 2026-10-03 `state.json` refusal records for `axozpe`, `m0kl28`, `xhr0dj` carry exactly that text and nothing else. | `run-20261003T172049Z-3698977/state.json` queue items' refusal `code: orchestrator-uncovered-work` and `reason` text |
| F-03 | The prompt has no named-owner exception. Its "WHAT *IS* WORK" paragraph lists "runs a repo-wide suite, performs a whole-Set verification or audit" unconditionally, and its hard-case rule is "any doubt resolves to CONTAINS EXECUTIONS". `axozpe`'s excerpt (rendered with `orchestrator_probe_excerpt` 2026-10-03) includes "THE SET IS ONLY DEMONSTRATED COMPLETE BY A FINAL CROSS-CHILD MEASUREMENT, which Order 04 carries as the last child rather than this plan performing it", and the probe failed it. | the quoted prompt paragraphs; the rendered excerpt; the store entry recorded 2026-10-03 for `axozpe`'s digest with `verdict: fail` |
| F-04 | The excerpt already contains the child table first (`### Child IPDs table (row cells, in document order)`), so the named-child rule needs no payload change, only a prompt instruction. | `orchestrator_probe_excerpt` renders `child_table_rows` under that heading |
| F-06 | The store's version is never read. `_read_probe_verdict_store` returns `raw.get("entries")` with no version check, and `record_probe_verdict` merges `dict(_read_probe_verdict_store(repo_root))` before writing the new `schema_version`. A constant bump alone retires nothing. | the two function bodies |
| F-05 | The store cannot be seen outside this machine. `probe_verdict_store_path` resolves to `<checkout>/.aw/state/runtime/orchestrator-probe-verdicts.json`; `.aw/.gitignore` ignores `/state/`; `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS` is 30. So CI and every other clone always miss, which is the reason the maintainer moved the answer into the plan. 46 entries exist at authoring; none survive the move, so every pending orchestrator is asked once more. | `probe_verdict_store_path`; `.aw/.gitignore`; `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS`; a count of the store's entries |

## Proposed changes (ordered, validatable)

1. Add a `PROBE_QUOTE_PREFIX = "QUOTE: "` constant and rewrite the template's ANSWER FORMAT and add a NAMED-OWNER paragraph (E-01).
2. Make the classifier return verdict plus validated quotes, strict in the new shape, with the excerpt threaded in (E-02).
3. Record the answer in the plan (E-03), keep it out of both fingerprints (E-06), and switch the probe to the plan record, retiring the store (E-07).
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
- Moving the answer into the plan discards every cached verdict once. Measured cost: one model call per pending orchestrator the next time each is probed (16 at authoring).
- `agent_workflows/ipd_schema.py` and `agent_workflows/ipd_lifecycle.py` are touched only to register the fields/section and to prove (and if needed enforce) the receipt-fingerprint exclusion.

## Required tests / validation

- Baseline: run `python3 -m pytest` BARE on a clean tree before editing; record the failing node ids.
- `python3 -m pytest -o addopts="" tests/test_orchestrator_probe_quotes.py tests/test_coverage_record.py tests/test_orchestrator_probe_payload.py tests/test_orchestrator_shape_gate.py tests/test_orchestrator_shape_composed.py tests/test_orchestrator_retirement.py -q` pasted.
- The mutation run for E-05, pasted failing then passing.
- `python3 -m pytest` BARE after the change, pasted with its `N passed` line, judged by the delta of failing node ids.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` Sections 2.5b (A.3, A.4) and 2.5e as amended by Order 01, and spec `r07vma` R9 as amended (C.1). No spec is edited here. The docstrings of the changed functions are updated to state the new contract; no user-facing document describes the probe's answer format.

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

### OQ-04: Where is the probe's answer recorded?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-10-04 by the maintainer: in the plan itself (spec `25kzda` 2.5e), not in the gitignored 30-day cache, so CI, other clones and later reviews read the same answer. This plan implements the record; Order 03 adds its lint defense.

### OQ-03: Should the named-child credit accept an Order number as well as an id6?

- Blocking: no
- Status: resolved
- Owner: plan-review (2026-10-04)
- Resolution or deferral rationale: RESOLVED: YES, when the Order number appears in the orchestrator's own child table, which the probe is sent. Measured: `axozpe`, the motivating false refusal, names its owner only as "Order 04" in both `Required tests / validation` and `Scope check`; an id6-only rule would leave it refused and the Concern's claim false. An Order number present in the table resolves to exactly one child, so it is as precise as an id6. Order 01 (`hm1h3l`) A.4 was amended in the same review to state this.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff of `PROBE_PROMPT_TEMPLATE` and the new constant. Paste the output of `render_probe_prompt` over `axozpe`'s real excerpt (from `orchestrator_probe_excerpt`), showing the `QUOTE: ` instruction, the named-child paragraph, and both sentinels.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `classify_probe_reply` and `ask_orchestrator_probe`. Paste the test run of the classifier table showing each case's expected state: positive with one valid quote, positive with zero quotes, positive whose only quote is absent from the excerpt (`unknown`), positive with one valid and one invalid quote (`executions`, one quote, discarded 1), positive with a non-`QUOTE:` trailing line (`unknown`), negative alone, negative plus a trailing line, both sentinels, empty.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new module and the schema registration diff. Paste the test run writing a `fail` with two quotes into a fixture plan, the resulting metadata lines, `## Coverage findings` section and history line as they appear in the file, the read-back with both quotes and `is_current` True, the edited-plan case with `is_current` False, and `aw ipd lint` on the fixture plan conforming after each write.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the test that records a coverage answer into a plan with a begin receipt, showing `receipt_is_current` True and `probe_cache_digest` identical before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the diff of `probe_orchestrator` and of the store's removal or retirement (and which was chosen, with a grep proving no other module imports the store functions if deleted). Paste the second-run case's asker call count (0) and quotes read from the plan, the edited-plan case's call count (1), and a check that `.aw/state/runtime/orchestrator-probe-verdicts.json` was not written by the test run.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the end-to-end test's captured refusal reason and returned message, each containing the fixture quote and the orchestrator id6, and paste the remedy text showing it names "assign ... by id6", "add a child", and forbids deleting the checklist.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test file passing with its count; paste the mutation (quote validation removed) failing it and the revert passing it; paste a grep for `inspect`, `ast.parse` and reads of `agent_workflows/*.py` in the new file returning nothing. Paste the BARE `python3 -m pytest` summary line reconciled against your own baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the declared paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Paste the ACTUAL runner output for every `V-*`; never paraphrase. Commit only the declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual test output. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`. Depends on `hm1h3l` executed (the amended spec text is the contract implemented here).
