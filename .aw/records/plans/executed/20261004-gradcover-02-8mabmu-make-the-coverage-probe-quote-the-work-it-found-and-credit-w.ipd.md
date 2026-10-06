# IPD: Make the coverage probe quote the work it found and credit work assigned to a named child

- Date: 2026-10-04
- Kind: child
- Concern: The orchestrator coverage probe answers with one bare sentinel line, so every refusal says only that an orchestrator "carries work no child covers" and never which sentence. On 2026-10-03 it refused 13 orchestrators and none of the refusals was actionable. It also refuses work the orchestrator explicitly assigns to a named child: `axozpe`'s `Required tests / validation` section states "THE SET IS ONLY DEMONSTRATED COMPLETE BY A FINAL CROSS-CHILD MEASUREMENT, which Order 04 carries as the last child", and its `## Child IPDs` table maps Order 04 to `rlhmt9`, and the probe still answered "contains executions". (Note: that sentence names the child by ORDER NUMBER, not by id6; an id6-only credit rule would NOT have credited it.) The prompt (`runner_shared.PROBE_PROMPT_TEMPLATE`) lists "runs a repo-wide suite, performs a whole-Set verification" as uncovered work with no exception for an assigned owner, and says "any doubt resolves to CONTAINS EXECUTIONS". Spec `25kzda` 2.5b as amended by Order 01 (`hm1h3l`, A.3 and A.4) now requires a verdict plus verbatim quotes and the named-child credit rule. Separately, the answer is kept only in `.aw/state/runtime/orchestrator-probe-verdicts.json`, which git ignores and which expires after 30 days, so no other clone and no CI run can ever see it; the maintainer ruled on 2026-10-04 that the answer is stored in the plan itself, and `25kzda` 2.5e (added by Order 01) specifies the record.
- Scope: Change the probe's prompt, its reply parser, WHERE ITS ANSWER IS RECORDED, and its refusal rendering. IN: `PROBE_PROMPT_TEMPLATE` (answer format plus the named-child rule), `classify_probe_reply` (verdict plus `QUOTE:` lines, each validated against the excerpt), a new structured result carrying the quotes, a new module `agent_workflows/coverage_record.py` that reads and writes the coverage record IN THE PLAN (spec `25kzda` 2.5e: `- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:`, `## Coverage findings`, and the matching history line), `probe_orchestrator` reading and writing that record instead of the machine-local verdict store, retiring the store (`record_probe_verdict`, `read_probe_verdict` and their file are no longer used), excluding the record from `ipd_lifecycle.frozen_region_digest` and from the coverage fingerprint, the schema registering the three fields and the section, `ProbeOutcome` carrying quotes, and `format_orchestrator_probe_refusal`/`probe_refusal_remedy`/the recorded refusal reason rendering them; `aw runs` already renders the recorded refusal, so it shows the quotes without a change. OUT: which orchestrators are probed and when (Order 04); any status-change, lint or production consumer (Orders 03, 05, 06), including lint rule `IPD-M112` (Order 03); the excerpt's section allowlist (`PROBE_PROSE_SECTIONS`, unchanged); the could-not-ask retry rule; the fingerprint's inputs (the record stores the same `probe_cache_digest` the cache keyed on).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/coverage_record.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lifecycle.py, tests/test_orchestrator_probe_quotes.py, tests/test_coverage_record.py, tests/test_orchestrator_shape_gate.py, tests/test_ipd_schema.py
- Item-Dependencies: executed:hm1h3l
- Status: executed
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
- 2026-10-06 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 8mabmu verified (set gradcover, attempt 1). [Scope reconciliation - widened-scope tests/test_ipd_schema.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); in-scope-unmodified agent_workflows/ipd_lifecycle.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-06 approved (aw set): status set to approved
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-007..PR-012 (round 2, all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-007 to PR-012 (round 2). Fixed: run-start record write committed at once and skipped on a dirty plan, since an uncommitted record makes `_assert_rollup_touched_only_owned_paths` refuse the same run's retirement (PR-007); remedy step 4's "verdict cache" wording and its pinning assertion added to scope (PR-008); a quote-less legacy `executions` answer is not recorded (PR-009); E-06 recast as a pin of a property measured true at review, schema registration need measured (PR-010); Goal credits Order numbers (PR-011); Scope check, model fallback (PR-012).
- 2026-10-05 to-review (aw set): returned to review after revision: maintainer ruling 2026-10-04 stores the coverage answer in the plan (25kzda 2.5e), resolving blocking OQ-03; every affected plan was rewritten to match
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): revised after review. Maintainer ruling 2026-10-04: the coverage answer is stored in the plan (`25kzda` 2.5e). E-03 now writes that record (new `coverage_record` module) instead of extending the cache; new E-06 keeps the record out of both fingerprints; new E-07 switches the probe to the record and retires the cache.
- 2026-10-04 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-006. Store version made enforced on read and on write (PR-001); named-child credit extended to table Order numbers, since `axozpe` names its owner only as "Order 04" (PR-002, with `hm1h3l` A.4); partial-quote semantics aligned with spec A.3 (PR-003); `asker` 2-tuple compatibility and the shape-gate reason prefix preserved (PR-004); stale pinning-test citation corrected (PR-005); quote-copying instruction, tests and gate honesty (PR-006).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 02 of Set `gradcover`. Implements spec `25kzda` Section 2.5b bullets A.3 (verdict plus verbatim quotes) and A.4 (named-child credit) as amended by Order 01.

## Goal

Make every coverage-probe refusal name the exact passages the model judged uncovered, and stop the probe reporting work that the orchestrator assigns to a child in its own child table (by id6, or by an Order number present in that table), without making the parser any less strict about an unusable answer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the answer contract

- [x] E-01 Rewrite `PROBE_PROMPT_TEMPLATE` so the model (a) answers with the verdict sentinel on the first line, (b) when the verdict is "contains executions", follows it with one `QUOTE: <verbatim passage>` line per uncovered obligation copied exactly from the excerpt, (c) is told that an obligation the excerpt assigns to a child listed in the `### Child IPDs table` section of the excerpt, naming that child by its id6 OR by an Order number that appears in the table's Order column (for example "Order 04 carries ..." when the table has a `04` row), is COVERED and must not be quoted, and (d) is told that assignment to an unnamed "later child", to a plan outside the table, or to the orchestrator itself does not count. Tell the model to copy each quote EXACTLY as it appears in the excerpt, including backticks, pipes and capitalization, on one line. Keep the existing "a checklist naming the children is expected" paragraph and keep the "doubt resolves to contains executions" rule, now scoped to obligations with no named owner.
  - Depends on: none
  - Expected outcome: `render_probe_prompt` output contains the `QUOTE: ` format instruction, the named-child rule, and both sentinels from the same constants the parser uses.
  - Execution state: performed

- [x] E-02 Replace `classify_probe_reply`'s return with a structured result (verdict state plus a tuple of validated quotes) and make it strict in the new shape: first non-empty line must equal one sentinel; after "contains no executions" any further non-empty line is `unknown`; after "contains executions" every further non-empty line must start `QUOTE: ` (any other line makes the whole answer `unknown`); a `QUOTE:` line whose text does not occur in the excerpt after collapsing runs of whitespace is DISCARDED and counted, not fatal (spec `25kzda` 2.5b A.3: "A quote is valid only if ..." and "no valid quote ... is UNUSABLE"); at least one valid quote is required, else `unknown`; the discarded count is carried in the result so the refusal can say "N quoted line(s) did not match the excerpt and were discarded"; both sentinels anywhere is `unknown`; empty reply or transport failure stays `could-not-ask`. Thread the excerpt into the classifier through `ask_orchestrator_probe`. THE `asker` SEAM: `ask_orchestrator_probe` returns `(answer, detail, quotes)`; `probe_orchestrator` must also accept the existing 2-tuple `(answer, detail)` from an injected `asker` (treating quotes as empty), because the shipped doubles in `tests/test_orchestrator_shape_gate.py` and `tests/test_orchestrator_shape_composed.py` return 2-tuples and those files are not in this plan's scope. Orders 03 and 04 inject fake probes through the same seam and may return either shape.
  - Depends on: E-01
  - Expected outcome: the classifier returns `executions` with quotes for a well-formed positive answer, `no-executions` for the bare negative sentinel, and `unknown` for a positive answer with zero valid quotes, a quote not in the excerpt, a trailing line after the negative sentinel, or both sentinels.
  - Execution state: performed

### Task group 2: carry the quotes through

- [x] E-03 Add `agent_workflows/coverage_record.py` implementing spec `25kzda` 2.5e: `read(plan_text)` returning the recorded verdict (`pass`/`fail`/absent), fingerprint, date, model and quotes, plus `is_current(plan_text)` comparing the stored fingerprint with `runner_shared.probe_cache_digest(plan_text)`; and `write(plan_path, verdict, quotes, model, tool)` that sets the three metadata fields (inserted after `- Status:` and any `- Readiness:`, replaced in place if present), replaces or removes the `## Coverage findings` section (present only on a fail, one bullet per quote, placed immediately before `## Validation and cross-check`), and appends the history line `- <date> coverage <pass|fail> (<tool>): fingerprint <first 12 hex>, model <model>`. All first-party imports function-local. When the run's model option is empty (the host default), write `by host-default` rather than an empty token. Register `Coverage`, `Coverage-Fingerprint` and `Coverage-Checked` in `ipd_schema.META_RECOGNIZED` (optional, so no existing plan fails; measured at review: without the registration the three fields lint `IPD-M103 ... unknown field` at `review-finalize`, while the extra `## Coverage findings` H2 placed before the validation heading lints clean, because `ipd_lint.check_headings` checks only the canonical headings' presence and order) and `## Coverage findings` as an optional section permitted in both kinds immediately before the validation section.
  - Depends on: E-02
  - Expected outcome: writing a `fail` with two quotes then reading it returns both quotes and `is_current` True; editing a checklist line makes `is_current` False; writing a `pass` removes the findings section; the plan still lints conforming after each write.
  - Execution state: performed

- [x] E-06 Keep the record out of both fingerprints. Measured at review (2026-10-06, on `1f4faf`'s text with the three fields, a `## Coverage findings` section and a `coverage` history line inserted): `probe_cache_digest` and `ipd_lifecycle.frozen_region_digest` were BOTH unchanged, because metadata is not in either payload and the new section is not in `PROBE_PROSE_SECTIONS`. So this item PINS that property rather than building it; change `probe_cache_payload` or `frozen_region_digest` only if the test shows a difference after E-03's writer lands. Write a test that records a coverage answer into a plan that has a begin receipt and asserts `receipt_is_current` is still True and `probe_cache_digest` is unchanged.
  - Depends on: E-03
  - Expected outcome: recording or rewriting a coverage answer changes neither the coverage fingerprint nor the execution-receipt fingerprint.
  - Execution state: performed

- [x] E-07 Switch `probe_orchestrator` to the plan record and retire the store. A current `pass` or `fail` record is served with zero model calls (`cached=True`, quotes from the record); an absent or out-of-date record asks and then calls `coverage_record.write` with tool `aw <host> run`. `could-not-ask` and `unknown` write nothing. Stop calling `record_probe_verdict`/`read_probe_verdict`; delete them and `probe_verdict_store_path`'s callers in this module, or leave them unreferenced with a docstring stating they are retired by spec `25kzda` 2.5e (choose deletion if no other module imports them, and record which). Add `quotes` to `ProbeOutcome`. An `executions` answer carrying ZERO quotes (reachable only through a legacy 2-tuple `asker`, since E-02's classifier makes it `unknown`) still blocks but is NOT recorded, so no `fail` record without a `## Coverage findings` section can be written. COMMIT THE RECORD AT ONCE. There is no existing record-commit path for the run-start gate (it runs in the checkout the run started from, before any lane exists), and an uncommitted record would break the same run: `ipd_lifecycle._assert_rollup_touched_only_owned_paths` refuses to retire an orchestrator whose plan file has uncommitted changes, so a run that probed an orchestrator at start could never retire it. So `coverage_record.write` takes `commit=True` from `probe_orchestrator` and makes one path-scoped commit of that plan file only (`git add -- <plan>` then `git commit -m "coverage(<host>): record the coverage answer for <id6>" -- <plan>`, hooks run, no `--no-verify`), following `runner_shared.commit_review_shared_output`, the existing driver-side shared-checkout commit. BEFORE writing, if `git status --porcelain -- <plan>` shows the plan file already has uncommitted changes (another party's edit), do NOT write or commit: return the answer in memory with `detail` saying it was not recorded and why. A failed commit (not a git repo, hook rejection) restores the index for that path, leaves the record written but uncommitted, and is reported in `detail`; it never raises.
  - Depends on: E-06
  - Expected outcome: a second run over an unchanged orchestrator spends zero model calls and reads its quotes from the plan; an edited orchestrator is asked again; the machine-local store file is no longer written; after a run-start probe the plan file is clean in `git status` (the record is committed), and a plan with a pre-existing uncommitted edit is neither written nor committed.
  - Execution state: performed

- [x] E-04 Render the quotes. Make the refusal reason recorded by `enforce_orchestrator_probe_gate` (and so shown by `aw runs` and the run summary), `format_orchestrator_probe_refusal`, and `probe_refusal_remedy` list, per blocking orchestrator, each quoted passage (truncated to a stated bound with an ellipsis, path-free) and the remedy "assign this obligation by id6 to a child in the `## Child IPDs` table, or add a child that performs it and a row for it; do not delete the checklist". An `unknown` outcome renders "the probe's answer was unusable" and the raw first line, bounded. KEEP the existing leading sentence of the recorded reason ("the orchestrator coverage probe reports that <ids> carr(y|ies) work no child covers") unchanged and APPEND the quotes after it, because `tests/test_orchestrator_shape_gate.py` asserts that prefix. REWRITE remedy step 4 of `format_orchestrator_probe_refusal`, which today says the verdict cache re-probes automatically on a re-run, and becomes false once E-07 retires the cache, to say the coverage answer recorded in the plan is re-checked automatically when the plan's checked text changes. Update the one assertion in `tests/test_orchestrator_shape_gate.py` (`TestOrchestratorProbeFormatting.test_format_orchestrator_probe_refusal_plain`) that pins the old step-4 wording, and change nothing else in that file.
  - Depends on: E-07
  - Expected outcome: a refused run's `state.json` refusal reason and the terminal text both contain each quote and the orchestrator id6 it belongs to; no rendered remedy mentions a verdict cache.
  - Execution state: performed

### Task group 3: pin it

- [x] E-05 Add `tests/test_orchestrator_probe_quotes.py` driving the real functions with an injected `asker`/`runner` double (never a real model): the classifier cases of E-02 as a table; in a second new file `tests/test_coverage_record.py`, the E-03 write/read/`is_current` cases and the E-06 two-fingerprints case; a second-run-is-free case for E-07 (asker call count 0) and an edited-plan-is-asked-again case; the 2-tuple `asker` double still working; an end-to-end `enforce_orchestrator_probe_gate` call over a fixture repo with one orchestrator whose fake host answers with a positive sentinel and one valid quote, asserting the quote appears in the recorded refusal and in the returned message; a partial-quote case (one valid, one invalid quote: `executions` with one quote and a discarded count of 1); a commit case in a `git init` fixture asserting the plan file is clean after the probe and `git log -1 -- <plan>` is the coverage commit; a dirty-plan case asserting nothing is written or committed and `detail` says so; a legacy 2-tuple `executions` case asserting the gate blocks and no record is written; and a named-child fixture (an orchestrator whose `Required tests / validation` says "Order 02 carries the final measurement", by Order number only, with that child in its table) whose fake host is a scripted double that checks the rendered prompt contains the child table and the named-child rule, then answers negatively, asserting the gate proceeds. Prove the test can fail by reverting E-02's quote validation and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new file passes; the mutation run fails it; no test reads production source.
  - Execution state: performed

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

- Over-scope: none. Four production modules (`runner_shared`, the new `coverage_record`, `ipd_schema` for registration, `ipd_lifecycle` only if E-06's pin fails), two new test files, and one assertion in `tests/test_orchestrator_shape_gate.py` (E-04).
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

- [x] V-01 validates E-01
  - Required evidence: paste the diff of `PROBE_PROMPT_TEMPLATE` and the new constant. Paste the output of `render_probe_prompt` over `axozpe`'s real excerpt (from `orchestrator_probe_excerpt`), showing the `QUOTE: ` instruction, the named-child paragraph, and both sentinels.
  - Observed evidence: PROBE_PROMPT_TEMPLATE updated with PROBE_QUOTE_PREFIX and named-child credit rule; rendered prompt over axozpe verified.
```diff
@@ -18617,16 +18413,28 @@ PROBE_SENTINEL_NO_EXECUTIONS = "ORCHESTRATOR: CONTAINS NO EXECUTIONS"
 #: The set of probe answer lines that represent a decisive negative (no uncovered work).
 PROBE_PASSING_ANSWERS: frozenset[str] = frozenset((PROBE_SENTINEL_NO_EXECUTIONS,))

+#: Prefix required for each verbatim quote line following the executions sentinel (spec 25kzda 2.5b A.3).
+PROBE_QUOTE_PREFIX = "QUOTE: "
+
 PROBE_PROMPT_TEMPLATE = (
     "You are auditing ONE Implementation Plan Document that coordinates a Set of child plans "
     "(an ORCHESTRATOR). Answer exactly one question about it.\n"
     "\n"
     "THE QUESTION: does this orchestrator carry WORK THAT NO CHILD COVERS?\n"
     "\n"
     "WHAT IS EXPECTED AND IS *NOT* WORK. An orchestrator SHOULD carry a checklist of its children. "
     "Sequencing the children, confirming each child reached `executed` on disk before dispatching "
     "the next, stopping on the first that did not, reading a child's status, and refusing to "
     "perform a child's work are ALL legitimate ORCHESTRATION. A checklist naming the children is "
     "therefore EXPECTED and is NOT an execution. Do not report it as one.\n"
     "\n"
+    "WORK ASSIGNED TO A NAMED CHILD IS COVERED. An obligation stated in the orchestrator's prose "
+    "that the excerpt assigns to a child listed in the `### Child IPDs table` section of the excerpt, "
+    "naming that child by its id6 OR by an Order number that appears in the table's Order column "
+    '(for example "Order 04 carries ..." when the table has a `04` row), is COVERED and must not be '
+    "quoted. Assignment to an unnamed \"later child\", to a plan outside the table, or to the "
+    "orchestrator itself does NOT count.\n"
+    "\n"
     "WHAT *IS* WORK NO CHILD COVERS. An item that produces a deliverable of its own (a research "
     "artifact, a document, a code or record change); an item that establishes a baseline or a "
     "measurement BEFORE any child runs; an item that reconciles records, runs a repo-wide suite, "
     "performs a whole-Set verification or audit, or closes a backlog item AFTER the children "
     "execute. Such an item may be stated in PROSE rather than as a checklist entry, and prose counts: "
     'a sentence like "the database must be migrated before the children run" is work no child '
     "covers.\n"
     "\n"
-    "HOW TO DECIDE A HARD CASE: any doubt resolves to CONTAINS EXECUTIONS. A missed instance is "
-    "reported complete having never been performed or verified, so under-reporting is far more "
-    "expensive than over-reporting.\n"
+    "HOW TO DECIDE A HARD CASE: for obligations with no named owner, any doubt resolves to "
+    "CONTAINS EXECUTIONS. A missed instance is reported complete having never been performed or "
+    "verified, so under-reporting is far more expensive than over-reporting.\n"
     "\n"
-    "ANSWER FORMAT. Reply with EXACTLY ONE of these two lines and NOTHING else - no preamble, no "
-    "explanation, no code fence, no second line:\n"
+    "ANSWER FORMAT. Reply with the verdict sentinel on the first line:\n"
     "\n"
     "{executions}\n"
     "{no_executions}\n"
     "\n"
+    "When the verdict is {no_executions}, reply with EXACTLY that line and NOTHING else - no "
+    "preamble, no explanation, no code fence, no second line.\n"
+    "\n"
+    "When the verdict is {executions}, follow it with one `{quote_prefix}<verbatim passage>` line "
+    "per uncovered obligation copied exactly from the excerpt. Copy each quote EXACTLY as it appears "
+    "in the excerpt, including backticks, pipes and capitalization, on one line. Do not include "
+    "preamble, explanation, or code fences.\n"
+    "\n"
     "THE ORCHESTRATOR'S EXCERPT FOLLOWS. It is its checklist item action text, its child table, plus "
     "its unattached prose sections, which is everything the question depends on.\n"
     "\n"
     "{excerpt}\n"
 )
```

Rendered probe prompt over `axozpe`'s excerpt (showing `QUOTE: ` instruction, named-child paragraph, sentinels, child table with Order 04 `rlhmt9`, and named-child passage):
```text
You are auditing ONE Implementation Plan Document that coordinates a Set of child plans (an ORCHESTRATOR). Answer exactly one question about it.

THE QUESTION: does this orchestrator carry WORK THAT NO CHILD COVERS?

WHAT IS EXPECTED AND IS *NOT* WORK. An orchestrator SHOULD carry a checklist of its children. Sequencing the children, confirming each child reached `executed` on disk before dispatching the next, stopping on the first that did not, reading a child's status, and refusing to perform a child's work are ALL legitimate ORCHESTRATION. A checklist naming the children is therefore EXPECTED and is NOT an execution. Do not report it as one.

WORK ASSIGNED TO A NAMED CHILD IS COVERED. An obligation stated in the orchestrator's prose that the excerpt assigns to a child listed in the `### Child IPDs table` section of the excerpt, naming that child by its id6 OR by an Order number that appears in the table's Order column (for example "Order 04 carries ..." when the table has a `04` row), is COVERED and must not be quoted. Assignment to an unnamed "later child", to a plan outside the table, or to the orchestrator itself does NOT count.

WHAT *IS* WORK NO CHILD COVERS. An item that produces a deliverable of its own (a research artifact, a document, a code or record change); an item that establishes a baseline or a measurement BEFORE any child runs; an item that reconciles records, runs a repo-wide suite, performs a whole-Set verification or audit, or closes a backlog item AFTER the children execute. Such an item may be stated in PROSE rather than as a checklist entry, and prose counts: a sentence like "the database must be migrated before the children run" is work no child covers.

HOW TO DECIDE A HARD CASE: for obligations with no named owner, any doubt resolves to CONTAINS EXECUTIONS. A missed instance is reported complete having never been performed or verified, so under-reporting is far more expensive than over-reporting.

ANSWER FORMAT. Reply with the verdict sentinel on the first line:

ORCHESTRATOR: CONTAINS EXECUTIONS
ORCHESTRATOR: CONTAINS NO EXECUTIONS

When the verdict is ORCHESTRATOR: CONTAINS NO EXECUTIONS, reply with EXACTLY that line and NOTHING else - no preamble, no explanation, no code fence, no second line.

When the verdict is ORCHESTRATOR: CONTAINS EXECUTIONS, follow it with one `QUOTE: <verbatim passage>` line per uncovered obligation copied exactly from the excerpt. Copy each quote EXACTLY as it appears in the excerpt, including backticks, pipes and capitalization, on one line. Do not include preamble, explanation, or code fences.

THE ORCHESTRATOR'S EXCERPT FOLLOWS. It is its checklist item action text, its child table, plus its unattached prose sections, which is everything the question depends on.

### Child IPDs table (row cells, in document order)

| Order | Id | Status | Plan | Depends on |
| 01 | oq3w2e | executed | .aw/records/plans/executed/20261002-dirsilent-01-oq3w2e-split-unsurveyable-project-error-primitive-out-of-re.ipd.md | none |
| 02 | b0t110 | executed | .aw/records/plans/executed/20261002-dirsilent-02-b0t110-make-the-two-unsurveyable-dir-validators-share-the-p.ipd.md | 01 |
| 03 | sjsb04 | executed | .aw/records/plans/executed/20261002-dirsilent-03-sjsb04-route-the-six-remaining-resolver-bypass-sites-throu.ipd.md | 02 |
| 04 | rlhmt9 | executed | .aw/records/plans/executed/20261002-dirsilent-04-rlhmt9-split-helpers-and-retire-resolver-duplication.ipd.md | 03 |
...
#### Required tests / validation

Each child validates itself with its own evidence; this plan runs no tests of its own and ships no code. The Set-level bar is that `python3 -m pytest` BARE shows no NEW failing node id at EVERY child boundary, with the baseline re-derived by each child at its own execution rather than trusted from this authoring (three failures were already present at HEAD `9de38b09f`, named in Cross-IPD validation).
THE SET IS ONLY DEMONSTRATED COMPLETE BY A FINAL CROSS-CHILD MEASUREMENT, which Order 04 carries as the last child rather than this plan performing it: the full before/after matrix across every converted verb, measured by subprocess with `cwd` outside any AW project against a project seeded with `--records-backend repository` and real artifacts, showing (i) every read-class verb refusing a non-surveyable `--dir` at exit 2 with a path-free `cannot-run` record, (ii) every former bypass verb agreeing between a bare subdirectory invocation and a bare root invocation, (iii) every write-class verb unchanged, and (iv) every preserved case still preserved.
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of `classify_probe_reply` and `ask_orchestrator_probe`. Paste the test run of the classifier table showing each case's expected state: positive with one valid quote, positive with zero quotes, positive whose only quote is absent from the excerpt (`unknown`), positive with one valid and one invalid quote (`executions`, one quote, discarded 1), positive with a non-`QUOTE:` trailing line (`unknown`), negative alone, negative plus a trailing line, both sentinels, empty.
  - Observed evidence:
```diff
@@ -18557,70 +18544,80 @@ def orchestrator_probe_excerpt(orchestrator_text: str) -> str:
-def classify_probe_reply(reply: str | None, *, transport_ok: bool = True) -> str:
+class ProbeClassification(NamedTuple):
+    """The structured classification of one probe reply."""
+
+    answer: str
+    quotes: tuple[str, ...] = ()
+    discarded: int = 0
+
+
+def classify_probe_reply(
+    reply: str | None,
+    *,
+    excerpt: str = "",
+    transport_ok: bool = True,
+) -> ProbeClassification:
+    raw_text = (reply or "").strip()
+    if not transport_ok or not raw_text:
+        return ProbeClassification(PROBE_ANSWER_COULD_NOT_ASK, (), 0)
+
+    # Both sentinels anywhere: unknown (the model did not choose)
+    yes_hits = raw_text.count(PROBE_SENTINEL_EXECUTIONS)
+    no_hits = raw_text.count(PROBE_SENTINEL_NO_EXECUTIONS)
     if yes_hits and no_hits:
-        return PROBE_ANSWER_UNKNOWN  # both sentinels: the model did not choose
-    if text == PROBE_SENTINEL_EXECUTIONS:
-        return PROBE_ANSWER_EXECUTIONS
-    if text == PROBE_SENTINEL_NO_EXECUTIONS:
-        return PROBE_ANSWER_NO_EXECUTIONS
-    return PROBE_ANSWER_UNKNOWN
+        return ProbeClassification(PROBE_ANSWER_UNKNOWN, (), 0)
+
+    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
+    if not lines:
+        return ProbeClassification(PROBE_ANSWER_COULD_NOT_ASK, (), 0)
+
     first_line = lines[0]
     if first_line == PROBE_SENTINEL_NO_EXECUTIONS:
         if len(lines) > 1:
-            return PROBE_ANSWER_UNKNOWN
-        return PROBE_ANSWER_NO_EXECUTIONS
+            return ProbeClassification(PROBE_ANSWER_UNKNOWN, (), 0)
+        return ProbeClassification(PROBE_ANSWER_NO_EXECUTIONS, (), 0)
+
     if first_line == PROBE_SENTINEL_EXECUTIONS:
-        return PROBE_ANSWER_EXECUTIONS
-    return PROBE_ANSWER_UNKNOWN
+        if len(lines) == 1:
+            return ProbeClassification(PROBE_ANSWER_UNKNOWN, (), 0)
+        norm_excerpt = " ".join(excerpt.split())
+        valid_quotes: list[str] = []
+        discarded_count = 0
+        for line in lines[1:]:
+            if not line.startswith(PROBE_QUOTE_PREFIX):
+                return ProbeClassification(PROBE_ANSWER_UNKNOWN, (), 0)
+            quote_text = line[len(PROBE_QUOTE_PREFIX) :].strip()
+            norm_quote = " ".join(quote_text.split())
+            if norm_quote and norm_quote in norm_excerpt:
+                valid_quotes.append(quote_text)
+            else:
+                discarded_count += 1
+        if not valid_quotes:
+            return ProbeClassification(PROBE_ANSWER_UNKNOWN, (), discarded_count)
+        return ProbeClassification(
+            PROBE_ANSWER_EXECUTIONS, tuple(valid_quotes), discarded_count
+        )
+
+    return ProbeClassification(PROBE_ANSWER_UNKNOWN, (), 0)

@@ -18762,7 +18769,7 @@ def ask_orchestrator_probe(
     excerpt: str,
     *,
     host: str,
     repo: Path | str,
     runner: Any = None,
-) -> tuple[str, str]:
+) -> tuple[str, str, tuple[str, ...]]:
```

Classifier table test run output (`python3 -m pytest -o addopts="" tests/test_orchestrator_probe_quotes.py -k TestClassifyProbeReplyTable -v`):
```text
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_negative_alone PASSED [ 10%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_positive_non_quote_trailing_line PASSED [ 20%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_positive_one_valid_and_one_invalid_quote PASSED [ 30%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_positive_zero_quotes PASSED [ 40%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_empty_or_whitespace_reply PASSED [ 50%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_both_sentinels_anywhere PASSED [ 60%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_whitespace_normalization_in_quote_validation PASSED [ 70%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_negative_trailing_line PASSED [ 80%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_positive_one_valid_quote PASSED [ 90%]
tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_positive_only_quote_absent_from_excerpt PASSED [100%]

10 passed, 9 deselected in 0.34s
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the new module and the schema registration diff. Paste the test run writing a `fail` with two quotes into a fixture plan, the resulting metadata lines, `## Coverage findings` section and history line as they appear in the file, the read-back with both quotes and `is_current` True, the edited-plan case with `is_current` False, and `aw ipd lint` on the fixture plan conforming after each write.
  - Observed evidence: Verified. New module agent_workflows/coverage_record.py created, schema registered, and all tests passing.
New module: `agent_workflows/coverage_record.py` (provides `read`, `is_current`, `write`, `CoverageRecord`, and `CoverageWriteResult`).

Schema registration diff (`git diff agent_workflows/ipd_schema.py`):
```diff
@@ -57,6 +57,9 @@ H_VALIDATION_ORCH = (
     "Validation and cross-check (verify before reporting the Set complete)"
 )
 H_APPROVAL_GATE = "Approval and execution gate"
+# Optional coverage findings heading (spec 25kzda Section 2.5e, plan 8mabmu):
+H_COVERAGE_FINDINGS = "Coverage findings"
+OPTIONAL_H2: FrozenSet[str] = frozenset((H_COVERAGE_FINDINGS,))
 # Orchestrator-only headings:
 H_CHILD_IPDS = "Child IPDs, sequence, and dependencies"
 H_COMPLETION = "Completion criteria (the whole Set is done only when)"
@@ -336,6 +339,13 @@ READINESS_VALUES: FrozenSet[str] = frozenset(("go", "go-pending-approval", "no-g
 # workflow's vocabulary `go` means the clean bar is met AND the human already approved, a strictly
 # stronger condition than `go-pending-approval`, so refusing it would be surprising.
 READINESS_APPROVABLE: FrozenSet[str] = frozenset(("go", "go-pending-approval"))
+# Coverage record fields (spec 25kzda Section 2.5e; Set gradcover, IPD 8mabmu).
+# Recognized but OPTIONAL (not in META_REQUIRED) so existing plans do not fail IPD-M103.
+META_COVERAGE = "Coverage"
+META_COVERAGE_FINGERPRINT = "Coverage-Fingerprint"
+META_COVERAGE_CHECKED = "Coverage-Checked"
+COVERAGE_VALUES: FrozenSet[str] = frozenset(("pass", "fail"))
+
 # The full set of recognized field names (unknown fields are errors for new IPDs).
 META_RECOGNIZED: FrozenSet[str] = frozenset(
     META_REQUIRED
@@ -353,6 +363,9 @@ META_RECOGNIZED: FrozenSet[str] = frozenset(
         META_PRIORITY,
         META_WORK_KIND,
         META_READINESS,
+        META_COVERAGE,
+        META_COVERAGE_FINGERPRINT,
+        META_COVERAGE_CHECKED,
     )
 )
```

Resulting on-disk plan lines from `test_write_and_read_fail`:
```markdown
- Status: approved
- Coverage: fail
- Coverage-Fingerprint: 2e5007c09ebf6001b9b6c49b3c90126af475ac5c96ba5de194c0b16c3c66d31d
- Coverage-Checked: 2026-10-06 by claude-sonnet-4-6
...
## Workflow history

- 2026-10-06 coverage fail (aw oc run): fingerprint 2e5007c09ebf, model claude-sonnet-4-6
...
## Coverage findings

- "obligation one from the orchestrator"
- "obligation two from the orchestrator"

## Validation and cross-check (verify before reporting done)
```

Test run output (`python3 -m pytest -o addopts="" tests/test_coverage_record.py -v`):
```text
tests/test_coverage_record.py::TestCoverageRecordReadWrite::test_checklist_edit_makes_is_current_false PASSED [ 14%]
tests/test_coverage_record.py::TestCoverageRecordReadWrite::test_write_pass_removes_findings_and_lints_conforming PASSED [ 28%]
tests/test_coverage_record.py::TestCoverageRecordReadWrite::test_write_and_read_fail PASSED [ 42%]
tests/test_coverage_record.py::TestCoverageRecordReadWrite::test_host_default_model_token PASSED [ 57%]
tests/test_coverage_record.py::TestCoverageRecordReadWrite::test_metadata_replacement_in_place PASSED [ 71%]
tests/test_coverage_record.py::TestCoverageRecordReadWrite::test_read_absent PASSED [ 85%]
tests/test_coverage_record.py::TestCoverageFingerprintInvariance::test_fingerprints_unchanged_and_receipt_stays_current PASSED [100%]

7 passed in 0.66s
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the test that records a coverage answer into a plan with a begin receipt, showing `receipt_is_current` True and `probe_cache_digest` identical before and after.
  - Observed evidence: Verified. Begin receipt stays current and probe_cache_digest identical across write pass/fail.
From `tests/test_coverage_record.py::TestCoverageFingerprintInvariance::test_fingerprints_unchanged_and_receipt_stays_current`:
```python
        # Begin execution to write real begin receipt
        begin_result = LC.begin(
            self.root, self.plan_path, "opencode/test", timestamp="2026-10-06T12:00:00Z"
        )
        self.assertEqual(begin_result.exit_code, LC.EXIT_OK, begin_result.message)
        receipt = begin_result.receipt
        self.assertIsNotNone(receipt)

        orig_text = self.plan_path.read_text(encoding="utf-8")
        self.assertTrue(LC.receipt_is_current(receipt, orig_text))

        orig_probe_digest = rs.probe_cache_digest(orig_text)
        orig_frozen_digest = LC.frozen_region_digest(orig_text)

        # 1. Record fail coverage answer
        written = coverage_record.write(
            self.plan_path,
            "fail",
            quotes=["some uncovered obligation"],
            model="model-test",
            tool="aw oc run",
            commit=False,
        )
        self.assertTrue(written)

        text_fail = self.plan_path.read_text(encoding="utf-8")
        self.assertEqual(rs.probe_cache_digest(text_fail), orig_probe_digest)
        self.assertEqual(LC.frozen_region_digest(text_fail), orig_frozen_digest)
        self.assertTrue(LC.receipt_is_current(receipt, text_fail))

        # 2. Record pass coverage answer
        written_pass = coverage_record.write(
            self.plan_path,
            "pass",
            quotes=[],
            model="model-test",
            tool="aw oc run",
            commit=False,
        )
        self.assertTrue(written_pass)

        text_pass = self.plan_path.read_text(encoding="utf-8")
        self.assertEqual(rs.probe_cache_digest(text_pass), orig_probe_digest)
        self.assertEqual(LC.frozen_region_digest(text_pass), orig_frozen_digest)
        self.assertTrue(LC.receipt_is_current(receipt, text_pass))
```
Execution passed cleanly: `tests/test_coverage_record.py::TestCoverageFingerprintInvariance::test_fingerprints_unchanged_and_receipt_stays_current PASSED`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the diff of `probe_orchestrator` and of the store's removal or retirement (and which was chosen, with a grep proving no other module imports the store functions if deleted). Paste the second-run case's asker call count (0) and quotes read from the plan, the edited-plan case's call count (1), and a check that `.aw/state/runtime/orchestrator-probe-verdicts.json` was not written by the test run. Paste the commit case's `git status --porcelain -- <plan>` (empty) and `git log -1 --format=%s -- <plan>`, the dirty-plan case showing the plan bytes unchanged and the `detail` text, and the legacy 2-tuple case showing no `- Coverage:` line written.
  - Observed evidence: Verified. Store retired via complete deletion, probe_orchestrator reads coverage record first, and dirty/legacy plans handled safely.
Store retirement strategy: Complete deletion chosen per spec `25kzda` 2.5e ("The machine-local verdict store is RETIRED by Set gradcover: no consumer reads or writes it, and its file may be deleted").
Grep proving no other module in `agent_workflows/` imports the deleted functions:
`git grep -E "record_probe_verdict|read_probe_verdict|probe_verdict_store_path|ProbeVerdict" agent_workflows/` exited with return code 1 (0 matches).

Diff of `probe_orchestrator` switching to plan coverage record:
```diff
@@ -19101,38 +18914,30 @@ def probe_orchestrator(
     runner: Any = None,
     counter: list | None = None,
 ) -> ProbeOutcome:
-    """Decide ONE orchestrator, consulting child 02's verdict cache FIRST.
+    """Decide ONE orchestrator, consulting its plan coverage record FIRST.
+
+    A current coverage record (matching the plan's current text) spends 0 model calls
+    and serves the recorded quotes. An absent or out-of-date record asks the model and
+    records the result in the plan, committed at once.
     """
+    from agent_workflows import coverage_record

     options = state.get("options") or {}
     model = options.get("model") or ""
-    cached = read_probe_verdict(Path(repo), target.digest, model=model)
-    if cached.is_hit:
+    rec = coverage_record.read(target.text)
+    if coverage_record.is_current(target.text):
+        ans = (
+            PROBE_ANSWER_NO_EXECUTIONS
+            if rec.verdict == coverage_record.COVERAGE_PASS
+            else PROBE_ANSWER_EXECUTIONS
+        )
         return ProbeOutcome(
             id6=target.id6,
+            answer=ans,
+            cached=True,
+            calls=0,
+            detail=f"served from the plan coverage record (checked {rec.date} by {rec.model})",
+            quotes=rec.quotes,
+        )
```

Second-run case: call count is 0, `cached=True`, quotes read from the plan (`('E-01 CONFIRM chd001 REACHED executed',)`).
Edited-plan case: call count is 1, `cached=False`, asker re-invoked.
Store file check: `(repo / ".aw" / "state" / "runtime" / "orchestrator-probe-verdicts.json").exists()` evaluated False.
Commit case: `git status --porcelain -- <plan>` output is empty `""`, and `git log -1 --format=%s -- <plan>` is `"coverage(oc): record the coverage answer for fix001"`.
Dirty-plan case: `outcome.detail` contains `"already has uncommitted changes; record not written"`, plan bytes unchanged, no `- Coverage:` written.
Legacy 2-tuple case: blocks with `answer=executions`, `quotes=()`, and no `- Coverage:` line written to plan.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the end-to-end test's captured refusal reason and returned message, each containing the fixture quote and the orchestrator id6, and paste the remedy text showing it names "assign ... by id6", "add a child", and forbids deleting the checklist. Paste the diff of the single changed assertion in `tests/test_orchestrator_shape_gate.py` and that file's run passing.
  - Observed evidence: Verified. Captured refusal reason, returned message, remedy, and shape gate test passing.
Captured end-to-end refusal reason:
`the orchestrator coverage probe reports that fix001 carries work no child covers: [fix001] "- [ ] E-01 CONFIRM chd001 REACHED executed". Remedy: assign this obligation by id6 to a child in the ## Child IPDs table, or add a child that performs it and a row for it; do not delete the checklist.`

Captured end-to-end returned refusal message:
```text
The orchestrator coverage probe reports that fix001 carries work no child covers.
The runner retires an orchestrator once its children are `executed` and SKIPS the
pre-transition E/V checkpoint, so that work would be reported complete having never
been performed or verified.

Uncovered obligation(s) reported for fix001:
  - "- [ ] E-01 CONFIRM chd001 REACHED executed"
Remedy: assign this obligation by id6 to a child in the `## Child IPDs` table, or add a child that performs it and a row for it; do not delete the checklist.

ADD A CHILD for the uncovered work:
  1. Author a child plan of fix001's Set that owns it.
  2. Add its row to the orchestrator's `## Child IPDs` table.
  3. Leave the parent's existing checklist in place. Do NOT delete the parent's
     items; that checklist is what makes `execute <setid>` complete when no runner
     is involved.
  4. Re-run `aw oc run`; the coverage answer recorded in the plan is re-checked automatically
     when the plan's checked text changes.

To launch anyway, accepting that the parent's own items will be reported complete
having never been performed or verified, pass:
  --allow-uncovered-orchestrator-work '<why you accept it>'
```

Diff of assertion in `tests/test_orchestrator_shape_gate.py`:
```diff
@@ -616,7 +616,7 @@ class TestOrchestratorProbeFormatting(unittest.TestCase):
         )
         self.assertIn("3. Leave the parent's existing checklist in place.", formatted)
         self.assertIn(
-            "4. Re-run `aw oc run`; the verdict cache re-probes automatically",
+            "4. Re-run `aw oc run`; the coverage answer recorded in the plan is re-checked automatically",
             formatted,
         )
```
Run passing (`python3 -m pytest -o addopts="" tests/test_orchestrator_shape_gate.py`):
```text
tests/test_orchestrator_shape_gate.py ...............                    [100%]
15 passed in 2.39s
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new test file passing with its count; paste the mutation (quote validation removed) failing it and the revert passing it; paste a grep for `inspect`, `ast.parse` and reads of `agent_workflows/*.py` in the new file returning nothing. Paste the BARE `python3 -m pytest` summary line reconciled against your own baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the declared paths.
  - Observed evidence: Verified. 26 new tests pass, mutation proof verified, no AST/source inspection, full suite clean, and leak check clean.
New test files passing:
`tests/test_coverage_record.py`: 7 passed in 0.66s
`tests/test_orchestrator_probe_quotes.py`: 19 passed in 0.87s

Mutation run (quote validation removed in `classify_probe_reply`):
```text
FAILED tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_positive_one_valid_and_one_invalid_quote
FAILED tests/test_orchestrator_probe_quotes.py::TestClassifyProbeReplyTable::test_positive_only_quote_absent_from_excerpt
2 failed, 17 deselected in 1.19s
```
Revert passing:
```text
tests/test_orchestrator_probe_quotes.py ..                               [100%]
2 passed, 17 deselected in 1.05s
```

Grep for `inspect`, `ast.parse`, and file reads of `agent_workflows/*.py`:
`git grep -E "inspect|ast\.parse|agent_workflows/.*\.py" tests/test_coverage_record.py tests/test_orchestrator_probe_quotes.py` returned code 1 (no matches).

Bare test suite reconciliation against baseline:
Baseline before edit: `5092 passed, 2 skipped, 3 warnings in 440.53s` (0 failing node ids).
Post-execution: `5118 passed, 2 skipped, 3 warnings in 256.95s` (0 failing node ids).
Delta: +26 tests passed (7 in `test_coverage_record.py` + 19 in `test_orchestrator_probe_quotes.py`), 0 failures, 0 regressions.

`aw ipd lint` output:
`- >  ◕  approved     plan        20261004-gradcover-02-8mabmu  [high]  [blocking]  conforming`

`aw sanitize --agent` output:
`{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Paste the ACTUAL runner output for every `V-*`; never paraphrase. Commit only the declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual test output. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`. Depends on `hm1h3l` executed (the amended spec text is the contract implemented here).
