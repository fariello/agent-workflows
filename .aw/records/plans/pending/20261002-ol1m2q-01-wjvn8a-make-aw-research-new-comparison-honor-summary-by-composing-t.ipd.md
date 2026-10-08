# IPD: Make aw research new-comparison honor --summary by composing the user subject with each document's role instead of discarding it

- Date: 2026-10-02
- Kind: child
- Concern: `aw research new-comparison` advertises `--summary` as a `One-line human summary`, accepts it, threads it into `research_cmd.plan_new_comparison`, and then throws it away. The inner `_mk(order_n, kind, model, sm)` is invoked with a HARDCODED per-document string at every one of its three call sites, and `build_frontmatter` receives `sm or summary`, so the user's value is reachable only when the hardcoded string is empty, which it never is. Measured in this lane: `aw research new-comparison . --set cmpset --slug widget-study --models gpt56,sonnet5 --summary 'MY USER SUMMARY' --apply` exits **0**, writes four documents carrying `summary: Originating prompt for the comparison set.`, `summary: gpt56 report.`, `summary: sonnet5 report.` and `summary: Synthesis of the model reports.`, and a `grep -rn 'MY USER SUMMARY'` over the whole fixture returns NOTHING. No warning, no note, no nonzero exit. The sibling verb `aw research new` honors the same flag correctly, so a user has every reason to expect this one does too.
- Scope: Make the flag live by COMPOSING rather than replacing: each planned document's `summary:` becomes `<user summary> (<role>)` when `--summary` is given, and stays exactly the present hardcoded role string when it is not. Add one module-private composer in `research_cmd.py`, call it at the three `_mk` call sites, and pin the behavior plus the no-flag non-regression in `tests/test_research_cmd_create.py`. The composition is DEGRADING: when the composed value would exceed `attention_contract.MAX_DESCRIPTIVE_LEN` the user's summary is written alone rather than a value the shipped descriptive-field contract forbids. DELIBERATELY NOT IN SCOPE: the descriptive-safety guard on this parameter, which pending plan `deftzy` owns and which this plan declares as a hard execution dependency rather than duplicating.
- Scope-Paths: agent_workflows/research_cmd.py, tests/test_research_cmd_create.py, CHANGELOG.md
- Item-Dependencies: executed:deftzy
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: ol1m2q
- Blocks-Release: next
- Set: ol1m2q
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wjvn8a
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006, all FIXED. Reviewed in lane review-sweep-run-20261007T032752Z-4094028 at HEAD ea6badb04; review record .aw/records/reviews/20261002-ol1m2q-01-wjvn8a-make-aw-research-new-comparison-honor-summary-by-composing-t.review.md. Defect re-driven and reproduces. PR-001: deftzy is executed and added only a lazy attention_contract import, so E-01 adds the module-level import; F-08/OQ-04/gate annotated satisfied. PR-002: nonexistent tests/test_research_contract.py replaced; descriptive-safety tests added to the regression set. PR-003: a bare git-init fixture writes under ~/.aw/projects/, so fixtures must set records_backend repository. PR-004: index --check baseline re-derived at execution (142 -> 179 drift). PR-005: falsification ordering made explicit. PR-006: CHANGELOG Fixed line added as E-05/V-05.

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `ol1m2q`, the carrier plan `deftzy` filed when it guarded this parameter without making it live. THE ITEM'S REPORTED DEFECT REPRODUCES EXACTLY as filed (F-01), and THE ONE DECISION THE ITEM EXPLICITLY RESERVED FOR A HUMAN IS ANSWERED FROM CORPUS EVIDENCE RATHER THAN TASTE. The item asks whether a user `--summary` should REPLACE the per-file string, PREFIX or SUFFIX it, or apply only to the `00` prompt, and guesses the last is "probably closest to the flag's intent". The corpus disagrees with that guess and the measurement is decisive: of the 8 comparison-shaped sets in this repository's research tree, 2 (`awclia`, `awnamespace`) still carry the generic placeholder on 9 documents a human never edited, so the placeholder is NOT reliably replaced by hand and a prompt-only fix would leave N+1 of every N+2 documents generically labelled (F-04). Of the 18 human-authored comparison-set summaries, 13 identify the document's ROLE or MODEL (F-05), so the role information the item worried about losing is information humans demonstrably DO write, which rules out bare replacement. Composition preserves both and is what F-06 renders. ALSO MEASURED AND NOT NAMED BY THE ITEM: a guard that judges only the USER INPUT lets a composed value breach the 300-character descriptive bound (a safe 290-character summary composes to 334, F-07), which is why the composer degrades rather than concatenating blindly; and the fix MUST NOT land before `deftzy`, because making the flag live at today's HEAD writes an injected `status:`/`blocks-release:` straight into the front matter with `validate_frontmatter` returning `[]` (F-08), which is this plan's declared `- Item-Dependencies: executed:deftzy`.

## Goal

Make `aw research new-comparison --summary` do what it says, so a user who names the subject of a comparison set gets that subject onto every document in the set instead of four generic placeholders. Compose rather than replace, so the set keeps the per-document role labels that tell a reader which file is the prompt, which is whose report, and which is the synthesis; those labels are information humans demonstrably write by hand when they edit these summaries at all (F-05), and 9 documents in this repository's own tree prove they frequently do not get around to editing them (F-04).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: compose the summary

- [x] E-01 Add a module-private composer to `agent_workflows/research_cmd.py` that takes the user's `--summary` and one document's role string and returns the value to write. Shape: `_compose_comparison_summary(user_summary: str, role: str) -> str`. Rules, in this order: an empty or whitespace-only `user_summary` returns `role` UNCHANGED (byte-identical to today's output, which is what keeps every existing caller and the whole committed corpus unaffected); otherwise the candidate is `f"{user} ({role.rstrip('.')})"` with `user` stripped; and if that candidate fails `attention_contract.is_safe_descriptive` the function returns the stripped `user_summary` ALONE.
  THE DEGRADING FALLBACK IS LOAD-BEARING, NOT DEFENSIVE PADDING, and this is the detail the backlog item does not anticipate. `deftzy` guards the INPUT, so a 290-character `--summary` is accepted as safe; composing it with the longest role string (`Originating prompt for the comparison set.`, 42 characters, costing 44 as a parenthetical) yields 334, and `A.is_safe_descriptive` on that returns **False** (F-07). Without the fallback this plan would make a guarded verb write a value the guard exists to forbid, turning a cosmetic bug fix into a contract violation. Falling back to the user's own value is the right degradation because the user's text is the information they asked for and the role string is the decoration.
  DROP THE ROLE'S TRAILING PERIOD when composing. Every one of the three shipped role strings ends in `.` (`"Originating prompt for the comparison set."`, `f"{m} report."`, `"Synthesis of the model reports."`), so composing verbatim reads `... (gpt56 report.)` with a period inside the bracket. `rstrip('.')` is deliberately applied to the ROLE ONLY and never to the user's value, which is theirs to punctuate.
  CONSULT `attention_contract` FOR THE VERDICT, do not reimplement a length test. Import it as a module-level `from agent_workflows import attention_contract as A`, matching `backlog.py`'s spelling. UPDATED AT REVIEW (PR-001): `deftzy` HAS EXECUTED, and it did NOT add a module-level import: `research_cmd._refuse_unsafe_descriptive` imports `attention_contract as _A` LAZILY inside its body. So the module-level `A` import is still absent and E-01 ADDS it (no circular-import risk: `attention_contract` imports only `lifecycle_dirs` from the package). Leave the existing lazy import inside `_refuse_unsafe_descriptive` alone; it is `deftzy`'s code and outside this item's concern.
  - Depends on: none
  - Expected outcome: `research_cmd._compose_comparison_summary("", "gpt56 report.")` returns `"gpt56 report."`; `_compose_comparison_summary("  ", "gpt56 report.")` returns `"gpt56 report."`; `_compose_comparison_summary("Which widget library", "gpt56 report.")` returns `"Which widget library (gpt56 report)"`; and `_compose_comparison_summary("u"*290, "Originating prompt for the comparison set.")` returns the bare 290-character value, with `A.is_safe_descriptive` True on every return.
  - Execution state: performed

- [x] E-02 Call the composer at the three `_mk` call sites in `research_cmd.plan_new_comparison` and REMOVE the dead `sm or summary` fallback that currently makes the bug invisible. Concretely: `_mk`'s `sm` parameter becomes the already-composed value, so its `build_frontmatter(... summary=sm or summary ...)` becomes `summary=sm`, and each call site passes `_compose_comparison_summary(summary, <role>)` where it today passes the bare role string.
  DELETE THE `or summary` RATHER THAN LEAVING IT, and the reason is the backlog item's own analysis: that expression is what made the defect look intentional, because it reads as a working fallback while being unreachable for every non-empty role string. Leaving it would preserve exactly the misleading code the item had to reason past. After this change `summary` is consumed ONLY through the composer, which gives the parameter one reader instead of two.
  KEEP `_mk`'s SIGNATURE, including the `sm` parameter name. Composing at the call site rather than inside `_mk` keeps `_mk` a pure name-and-frontmatter builder with no opinion about summaries, and keeps the three role strings visible at the three places that decide what each document IS, which is where a reader looks for them.
  - Depends on: E-01
  - Expected outcome: `aw research new-comparison . --set s --slug x --models gpt56,sonnet5 --summary 'Which widget library should we adopt' --apply` writes four documents whose `summary:` lines read `Which widget library should we adopt (Originating prompt for the comparison set)`, `... (gpt56 report)`, `... (sonnet5 report)` and `... (Synthesis of the model reports)`, where before the user value appeared in none of them. The same command with NO `--summary` writes the four present-day strings byte-identically.
  - Execution state: performed

### Task group 2: pin the behavior and the silence

- [x] E-03 Add a test to `tests/test_research_cmd_create.py::ComparisonTests` pinning the PRIMARY property: a `--summary` passed to `plan_new_comparison` reaches EVERY planned document. Assert per document that the user's exact substring is present in the rendered `summary:` value AND that the document's own role token is still present, so the test fails both if the value is discarded (today's bug) and if a future change replaces the role labels wholesale. Parse through the module's existing `_parse_frontmatter` helper and assert `R.validate_frontmatter` is `[]` on each, so a composed value that breaks the block fails here.
  ALSO PIN THE COMPOSER DIRECTLY as a unit, covering the empty, whitespace-only, normal and over-bound cases E-01 enumerates, including that the over-bound case returns the user's value ALONE and that `A.is_safe_descriptive` holds on every return. The over-bound case must be constructed from `A.MAX_DESCRIPTIVE_LEN` arithmetic rather than a copied `300`, so the test pins the predicate rather than a literal.
  Follow the module's established shape: a `tempfile` root with `R.RESEARCH_ROOT` created in `setUp`, calling `C.plan_new_comparison` directly, as `test_scaffold_order_and_tags` and `test_comparison_scaffold_prompt_has_no_status_and_reports_are_todo` already do.
  - Depends on: E-02
  ORDERING FOR THE FALSIFICATION (PR-005): write this test after E-01 but run it BEFORE applying E-02 (or against a `git worktree` at the pre-change HEAD) so V-03 can paste it RED; then apply E-02 and run it GREEN. The composer unit cases need E-01 and are expected to pass in both of those states, since E-01 is present in both.
  - Expected outcome: a primary test that FAILS against pre-E-02 code (the user substring is absent from all N+2 planned documents) and passes after, plus composer unit cases that pass once E-01 exists.
  - Execution state: performed

- [x] E-04 In the same class, pin the NO-FLAG NON-REGRESSION as an exact-string assertion, because it is the property that protects the entire committed corpus and every caller that passes no summary. With `summary` omitted, assert the planned documents carry EXACTLY `Originating prompt for the comparison set.`, `gpt56 report.`, `sonnet5 report.` and `Synthesis of the model reports.`, period included.
  THIS IS DELIBERATELY AN EXACT-STRING TEST, which is normally worth avoiding, and the justification is specific: these four strings are the OUTPUT CONTRACT this plan is changing the conditions of, and 9 documents in this repository's research tree carry them verbatim today (F-04), so a silent drift in the no-flag path would alter what a reader of those documents' siblings sees. The assertion is on a rendered OUTPUT value, not on source structure, so it is an outcome test and not a code-structure pin (AGENTS.md, GUIDING_PRINCIPLES P16).
  ALSO ASSERT THE ORDER AND KIND INVARIANTS STILL HOLD under a non-empty `--summary`: N+2 files, orders `00..N+1`, `research-prompt` at `00` with no model, one `research-report` per model in order, `reconciliation-report` with model `reconciliation` last, and the prompt still carrying NO `status:` while every other document carries `status: todo`. Those are what `test_scaffold_order_and_tags` and the status test already pin for the no-summary path; a summary must not perturb them, and nothing currently proves that because no existing test passes a summary at all.
  - Depends on: E-03
  - Expected outcome: the no-flag test passes identically before and after E-02 (proving the change is opt-in), and the order/kind/status invariants pass under a non-empty summary where today no test exercises that combination.
  - Execution state: performed

### Task group 3: record the user-visible fix

- [x] E-05 ADD exactly one `- Fixed:` line to `CHANGELOG.md` under the current `## 2.0.0 (pending)` heading, in the style of the existing `- Fixed:` entries, saying that `aw research new-comparison --summary` is now written onto every scaffolded document as `<summary> (<role>)` instead of being silently discarded, and that omitting `--summary` leaves the output unchanged. Write NO em or en dashes (user-facing prose under the AGENTS.md dash rule). ADDED AT REVIEW (PR-006): the repository records user-visible fixes in the changelog as part of the fixing plan (39 `- Fixed:` lines under the pending heading, for example executed plan `w89bo8` E-05), so deferring it to release time would be the exception, not the convention.
  - Depends on: E-02
  - Expected outcome: one added changelog line recording the user-visible behavior change, with no em or en dash.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE SIBLING VERB ALREADY DOES THIS CORRECTLY, which is the strongest argument that the defect is a defect. `research_cmd.plan_new` passes the user's `summary` straight to `build_frontmatter(... summary=summary ...)` with no interposed default, and uses it as a slug fallback (`R.kebab(slug) if slug else R.kebab(summary)`). Measured: `aw research new . --kind research-prompt --slug single-doc --summary 'A user summary for new' --apply` writes `summary: A user summary for new`. So the two creation verbs disagree about the same flag name.
- THE FRONT-MATTER DIALECT IS A HAND-WRITTEN LINE SPLITTER, NOT YAML. `research_contract.parse_frontmatter` walks lines between `---` fences doing `key, _, val = line.partition(":")`, which is why an unguarded newline in a value INJECTS a real sibling key and why this plan must not land before `deftzy` (F-08). No YAML library is imported anywhere in the package.
- THE 300-CHARACTER DESCRIPTIVE BOUND IS SHARED AND ALREADY SHIPPED. `attention_contract.MAX_DESCRIPTIVE_LEN` is 300 and `attention_contract.is_safe_descriptive` documents itself as "Section 8.8: a descriptive field is a single, bounded, control-char-free line", refusing an over-length value, an embedded `\n` or `\r`, and any match of `_CONTROL_CHAR_RE`. This plan consults that predicate and adds no second definition.
- THE GOVERNING SPEC FORBIDS TRUNCATION, WHICH CONSTRAINS THE FALLBACK. Spec `attention-registry-and-cross-tree-status` Section 8.8: "Over-length values are a contract violation, not silently truncated". So the over-bound composition case may NOT be fixed by trimming the composed string to 300; dropping the decorative role parenthetical and keeping the user's own (already guarded, already in-bound) value is the only option that violates nothing.
- THE SPEC DESCRIBES THE SCAFFOLD WITHOUT CONSTRAINING THE SUMMARY. Spec `agents-artifact-organization` Section 5.3 defines `new-comparison` as creating "the prompt at `NN=00`, one report slot per model at `NN=01..N`, and reserves a `reconciliation-report` slot" and names `--set`, `--slug`, `--models` only; `--summary` is not mentioned for this verb, and Section 5.8 fixes the eleven-field block without fixing any field's VALUE. So composing a summary amends no spec.
- THE VERB'S REFUSAL PLUMBING IS ALREADY MACHINE-READABLE and this plan needs none of it: `plan_new_comparison` returns `(None, error)` and `run_new_comparison` renders that through a `CommandResult(status="cannot-run", exit_code=2)` under `--agent`/`--json`. This plan introduces NO new refusal, so it adds no error path.
- A BARE `git init` FIXTURE DOES NOT KEEP ITS RECORDS (PR-003). Measured at review: `aw research new-comparison . ... --apply` in a fresh `git init` directory with no `.aw/config/project.json` wrote all four files under the HOME-scoped `~/.aw/projects/<name>-<hash>/records/research/`, NOT inside the fixture. That is why F-01's "grep over the whole fixture returned nothing" was true without proving the defect, and it means a hand-driven check leaves residue outside the workspace. Every fixture this plan drives MUST first write `.aw/config/project.json` containing `{"records_backend": "repository"}` (this repository's own setting), after which the files land in `<fixture>/.aw/records/research/`. Re-measured that way at review: the four `summary:` lines are the generic placeholders and `MY USER SUMMARY` is absent, so the defect still reproduces after `deftzy`.
- THE TEST MODULE TO EXTEND ALREADY EXISTS AND IS GREEN. `tests/test_research_cmd_create.py` holds `ComparisonTests` with three comparison cases and a module-level `_parse_frontmatter` helper. Measured at authoring: `python3 -m pytest tests/test_research_cmd_create.py` gives `16 passed in 7.68s`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Do not pass `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).

## Findings

All findings were DRIVEN in this lane at HEAD `b8e1e0157`, against fixtures under the gitignored `tmp/` (so nothing measured here is committed) or against this repository's own research tree where the finding is about the real corpus.

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S DEFECT REPRODUCES EXACTLY AS FILED. The flag is accepted, exits 0, and the value appears in no written file. | Driven in a `git init` fixture: `aw research new-comparison . --set cmpset --slug widget-study --models gpt56,sonnet5 --summary 'MY USER SUMMARY' --apply` printed four `wrote ...` lines and `rc=0`. `grep -n '^summary:'` over the four files returned `Originating prompt for the comparison set.`, `gpt56 report.`, `sonnet5 report.`, `Synthesis of the model reports.`. `grep -rn 'MY USER SUMMARY'` over the whole fixture exited 1 with no match. |
| F-02 | THE MECHANISM IS EXACTLY AS THE ITEM DESCRIBES, confirmed at the symbol rather than inferred. `_mk`'s fourth parameter `sm` is passed a non-empty literal at all three call sites and `build_frontmatter` receives `sm or summary`, so the right operand is unreachable. | Read of `research_cmd.plan_new_comparison`: the three calls are `_mk(0, "research-prompt", None, "Originating prompt for the comparison set.")`, `_mk(i, "research-report", m, f"{m} report.")` and `_mk(len(norm_models) + 1, "reconciliation-report", "reconciliation", "Synthesis of the model reports.")`, with `summary=sm or summary` inside `_mk`. |
| F-03 | THE SILENCE EXTENDS TO THE PREVIEW PATH, so a user cannot catch it by dry-running first. | Driven WITHOUT `--apply`: `aw research new-comparison . --set prev --slug preview-check --models gpt56 --summary 'A USER SUBJECT'` exited 0 and printed three full `would write` blocks whose `summary:` lines were the generic placeholders; the user's string appeared nowhere in the preview either. |
| F-04 | **THE ITEM'S PREFERRED OPTION IS REFUTED BY THE CORPUS.** The item guesses that applying the summary to the `00` prompt alone is "probably closest to the flag's intent". But the per-document placeholders are NOT reliably replaced by hand, so a prompt-only fix leaves most of a set generically labelled. | Measured over this repository's `.aw/records/research/**`: of 127 documents carrying a `summary:`, **9 still carry a verbatim generic comparison placeholder** (2 `Originating prompt for the comparison set.`, 6 `<model> report.`, 1 `Synthesis of the model reports.`). Grouped by set, 2 of the 8 comparison-shaped sets (those containing a `reconciliation-report`) are entirely unedited: `awclia` 5 of 5 documents and `awnamespace` 4 of 5. |
| F-05 | **BARE REPLACEMENT IS ALSO REFUTED**, because the role information it would destroy is information humans demonstrably write. | Measured over the same 8 comparison-shaped sets, excluding placeholders and `Migrated from ...` migration stubs: of **18** human-authored summaries, **13** name the document's role or model (for example `gpt-5.6 (Codex) review of the attention-registry spec`, `Gemini 3.1 Pro review of the attention-registry spec`, `Consolidated reconciliation of the gpt-5.6/Gemini/Sonnet-5 reviews ...`). So a reader of these sets relies on the summary to say which document is which, and replacing all N+2 with one identical string would remove that. |
| F-06 | COMPOSITION DELIVERS BOTH, verified by rendering it through the real manifest generator rather than by assertion. | Driven on a fixture: with all four summaries rewritten to `<user> (<role>)`, `aw research index --dir .` rendered `INDEX.md` lines `Which widget library should we adopt (Originating prompt for the comparison set)`, `... (gpt56 report)`, `... (sonnet5 report)`, `... (Synthesis of the model reports)`. The contrast cases were rendered the same way: bare replacement gives four IDENTICAL `Which widget library should we adopt` entries, and the prompt-only option leaves three of four entries reading `gpt56 report.` / `sonnet5 report.` / `Synthesis of the model reports.` with the user's subject nowhere but the prompt. |
| F-07 | **COMPOSITION CAN BREACH THE 300-CHARACTER BOUND EVEN WHEN THE USER'S INPUT IS SAFE**, which is the hazard neither the item nor `deftzy` names and which forces the degrading fallback. | Driven: `A.MAX_DESCRIPTIVE_LEN` is 300; a 290-character user summary satisfies `A.is_safe_descriptive` (True); composed with the longest role string (`Originating prompt for the comparison set.`, 42 characters, 44 as ` (...)`) the result is 334 characters and `A.is_safe_descriptive` returns **False**. Per-role suffix costs measured: 44, 33, and 30 for the longest `<model> report.` form (`gemini31prodeepthink report.`). Driving the E-01 fallback rule over users of length 0, 36, 290 and 300 against all three roles returned a safe value in every one of the 12 combinations. |
| F-08 | SATISFIED SINCE AUTHORING (PR-001): `deftzy` is now in `executed/` with `- Status: executed`, and at review HEAD `ea6badb04` `research_cmd._refuse_unsafe_descriptive` exists and `plan_new_comparison` calls it on `summary` before planning; a `--summary $'bad\nstatus: reference'` is refused with `--summary must not contain embedded newlines`. The guard judges the INPUT only (a 290-character value and a whitespace-only value both pass), so the composer's fallback (F-07) is still required. AUTHORING TEXT RETAINED: **THIS PLAN MUST NOT LAND BEFORE `deftzy`**, and that is a measured hazard rather than a sequencing preference. At today's HEAD the guard does NOT exist, so making the flag live would route an unvalidated user string into the front-matter block. | Measured: `hasattr(research_cmd, '_refuse_unsafe_descriptive')` is **False** and the module's source contains neither `is_safe_descriptive` nor `attention_contract`, so `deftzy` has not executed. Rendering `build_frontmatter(..., summary="legit\nstatus: reference\nblocks-release: next")` produces a block whose `R.parse_frontmatter` returns `status='reference'` and `blocks-release='next'` while `R.validate_frontmatter` returns `[]`. `deftzy` is `to-review`, declares `- Item-Dependencies: none`, and its `- Scope-Paths:` is `agent_workflows/research_cmd.py, tests/test_research_descriptive_safety.py`, so it is independently executable and satisfiable. |
| F-09 | THE DEPENDENCY EDGE IS WELL-FORMED AND THE TWO PLANS DO NOT COLLIDE ON A CHECKLIST, checked rather than assumed. | `ipd_schema.parse_item_dependencies('executed:deftzy')` returns a single `ItemDependency(kind='executed', target_type='ipd', status=None, id6='deftzy')` with `ready=True` and no error. The two plans share `agent_workflows/research_cmd.py`, which is expected and safe under the runner's isolated-worktree model, and they edit DISJOINT regions: `deftzy` adds a refusal helper plus guard calls on `summary`/`topic`/`consumed_by` inputs, while this plan adds a composer and changes what the three `_mk` call sites pass. `deftzy`'s own Deferred section names `ol1m2q` as this work's carrier and states it "DELIBERATELY DOES NOT FIX THIS", so the split is its author's intent. |
| F-10 | NOTHING ANYWHERE EXERCISES `--summary` ON THIS VERB, so the defect is pinned in neither direction and the no-flag path is pinned only loosely. | `grep -rn 'plan_new_comparison\|new_comparison'` over `tests/` matches four call sites, all in `tests/test_research_cmd_create.py` and NONE passing `summary=`. The only non-test documentation reference is one line in `docs/artifact-lifecycles.md` describing the verb's shape, which does not mention `--summary`. Baseline measured green: `python3 -m pytest tests/test_research_cmd_create.py` gives `16 passed in 7.68s`. |
| F-11 | (Review note, PR-004: at review HEAD the same command reports 179 diagnostics, so the count drifts; the executor takes a PRE-CHANGE rule-set baseline at the executing HEAD.) THE CHANGE IS INVISIBLE TO THE EXISTING POPULATION, because a write-path change is forward-only and the no-flag path is byte-identical by construction (E-01's first rule). | The 9 placeholder-carrying documents (F-04) are already written and are not rewritten by any verb this plan touches. `aw research index --check --agent` on this tree already reports `"outcome":"findings","exit":1` with 142 diagnostics (`frontmatter-invalid` on one unrelated assessment, two `check.stale-index-missing` for the deliberately untracked manifests, and a large `dangling-citation`/`stale-state-to-promote`/`adopted-without-consumer` population), so the executor must compare RULE SETS rather than totals and must not read that pre-existing count as a regression. |

## Proposed changes (ordered, validatable)

1. E-01: add `research_cmd._compose_comparison_summary`, returning the role unchanged for an empty user summary, `"<user> (<role sans trailing period>)"` normally, and the bare user summary when the composition would fail `A.is_safe_descriptive` (F-07).
2. E-02: pass the composed value at the three `_mk` call sites in `plan_new_comparison` and delete the now-single-reader `sm or summary` fallback that made the defect read as intentional (F-02).
3. E-03: pin that a `--summary` reaches every planned document while each role token survives, plus the composer's four cases with the bound derived from `A.MAX_DESCRIPTIVE_LEN` rather than a literal.
4. E-04: pin the no-flag path as exact strings and re-pin the order/kind/status invariants under a non-empty summary, which no existing test exercises (F-10).
5. E-05: record the user-visible fix as one `- Fixed:` line in `CHANGELOG.md` (PR-006).

## Deferred / out of scope (with reason)

- THE DESCRIPTIVE-SAFETY GUARD ON THIS PARAMETER IS NOT ADDED HERE. Measured in F-08: at HEAD the guard does not exist, and making the flag live without it writes an injected `status:`/`blocks-release:` into the block at zero `validate_frontmatter` drift. Deferred because that guard is ALREADY FULLY SPECIFIED AND AUTHORED as `deftzy` E-03, which explicitly guards `summary` on `plan_new_comparison` and records this work as its carrier; duplicating it would create a second refusal shape in the same module and would land two user-visible behavior changes in one commit. This plan instead declares the hard edge `- Item-Dependencies: executed:deftzy`, so the runner re-checks it at dispatch and marks this item `dependency-blocked` rather than running it early.
  - Carrier: deftzy
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7w6zsl-01-deftzy-refuse-an-unsafe-descriptive-value-at-every-research-write-p.ipd.md
- `aw research new`'s HANDLING OF `--summary` IS NOT TOUCHED. It already honors the flag correctly (Step 0), so there is nothing to fix on that path and widening this plan to it would be change for its own sake.
  - Carrier-Declined: Nothing is owed, because no defect was measured: driving `aw research new ... --summary 'A user summary for new' --apply` wrote `summary: A user summary for new` verbatim.
- THE 9 ALREADY-COMMITTED PLACEHOLDER SUMMARIES ARE NOT REMEDIATED. Measured in F-04 (`awclia` 5 of 5, `awnamespace` 4 of 5). Deferred because a write-path change is forward-only by construction and because rewriting them is an EDITORIAL act requiring someone who knows what those two sets were actually about, which no executor of this plan does. They are not a contract violation (the field is populated and in bound), so nothing is broken by leaving them.
  - Carrier-Declined: Nothing is owed as a defect. They are a documentation-quality residue a human may fix when next touching those sets; filing a backlog item to retro-edit two historical research sets would be make-work with no user-perceptible impact, which the repository's own `bug` test (user-perceptible impact) excludes.
- A `--summary-mode` FLAG OFFERING REPLACE / PREFIX / SUFFIX / PROMPT-ONLY IS NOT ADDED. Deferred on evidence rather than taste: F-04 and F-05 measure that two of the four candidate behaviors are actively worse for this corpus (prompt-only leaves most of a set generic; bare replacement destroys role information humans write 13 times in 18), so three of the four modes would ship a worse default behind a flag nobody would choose. Adding a mode flag also expands the verb's declared surface in `command_surface.py`, which is a public-contract change this bug fix has no mandate to make.
  - Carrier-Declined: Nothing is owed, because no user asked for the modes and no measurement supports them; the item asked for ONE decision to be made, and making it is the fix.
- THE PER-DOCUMENT ROLE STRINGS THEMSELVES ARE NOT CHANGED, reworded, or moved into a constant. They stay as the three literals at their three call sites (E-02 keeps them visible deliberately). Out of scope because E-04 pins them as the no-flag output contract, so changing them in the same plan would mean asserting and altering the same strings at once.
  - Carrier-Declined: Nothing is owed, because no defect was measured in the strings; they are serviceable role labels and 9 committed documents carry them verbatim (F-04).

## Scope check

- Over-scope: none. One new module-private function, three call-site edits plus the deletion of one dead `or summary` operand inside one existing function, new cases in one existing test class, and one `CHANGELOG.md` line (E-05). `build_frontmatter`, `_mk`'s signature, `plan_new`, `plan_new_comparison`'s parameter list, the id6 mint, `R.format_name`, the front-matter grammar, the eleven-field schema, `run_new_comparison`'s argument plumbing and error rendering, the `command_surface.py` declaration, the CLI flag definitions, `research_index`, `research_refs`, and every existing refusal are untouched. No spec, no rule id, no CLI surface.
- Under-scope, stated in full: (a) the descriptive-safety guard on this parameter is NOT added and is a hard prerequisite rather than a residue, carried by `deftzy` and declared as `- Item-Dependencies: executed:deftzy` (F-08); (b) the 9 already-committed placeholder summaries are NOT rewritten, which is deliberate and not a contract violation (F-04); (c) the role strings are not improved, because E-04 pins them in the same change; and (d) no `--summary-mode` choice is offered, because F-04 and F-05 measure three of the four candidate modes to be worse for this corpus.

## Required tests / validation

- `python3 -m pytest tests/test_research_cmd_create.py` for the edited module (run bare; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`). Measured baseline at authoring: `16 passed in 7.68s`.
- `python3 -m pytest tests/test_research_cmd_create.py tests/test_research_descriptive_safety.py tests/test_research_index.py tests/test_artifact_adopt.py` as the targeted regression set: these own the edited planner, the `deftzy` descriptive-safety guard on the same `summary` input (which must stay green with the composer in place), the manifest generator that renders the summary into `INDEX.md`, and the `aw adopt` caller of the sibling planner in the same module. CORRECTED AT REVIEW (PR-002): the authored list named `tests/test_research_contract.py`, which does not exist; `research_contract.validate_frontmatter` is exercised by `tests/test_research_index.py` and `tests/test_artifact_adopt.py` and is asserted directly by E-03. Re-derive the module list at execution rather than trusting it; report any name that no longer exists instead of silently dropping it.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression. Zero failures is the property; a differing total is expected as other work lands and is not itself a regression.
- PRE-FIX FALSIFICATION IS REQUIRED for the primary property: V-03 must show the E-03 test FAILING against pre-E-02 code, with the assertion text visible, proving the user's summary reached none of the planned documents. A test that passes before the fix proves nothing. Author the test first and run it before the E-02 edit, or run it against a separate `git worktree` at HEAD. Do NOT `git stash push -- agent_workflows/research_cmd.py`: this checkout is shared and stashing a path can swallow a co-worker's uncommitted edit to the same file.
- `aw research index --check --agent` on the repository tree, to confirm this change adds no rule. Take the PRE-CHANGE rule set at the executing HEAD before E-02 and compare the post-change rule set to it (PR-004: the count went from 142 at authoring to 179 at review, so neither number is a bar). For context only, at authoring it reported `"outcome":"findings","exit":1` with 142 diagnostics, dominated by `dangling-citation`, `stale-state-to-promote` and `adopted-without-consumer`, plus one `frontmatter-invalid` on an unrelated assessment and two `check.stale-index-missing` for the untracked manifests. Compare RULE SETS, not totals (F-11).
- A HAND-DRIVEN END-TO-END CHECK on a throwaway `git init` fixture under the gitignored `tmp/` that FIRST carries `.aw/config/project.json` = `{"records_backend": "repository"}` (PR-003; without it the files are written under `~/.aw/projects/`, outside the fixture and the workspace), removed afterwards, since the unit tests call the planner directly and the user's complaint is about the CLI: run the verb with and without `--summary`, at `--apply` and in preview, and read the resulting `summary:` lines plus the generated `INDEX.md`.

## Spec / documentation sync

N/A with reason. No `.spec.md` appears in `- Scope-Paths:` and none is owed. Spec `agents-artifact-organization` Section 5.3 specifies `new-comparison` in terms of WHICH documents it scaffolds ("the prompt at `NN=00`, one report slot per model at `NN=01..N`, and reserves a `reconciliation-report` slot") and names only `--set`, `--slug` and `--models`; it does not mention `--summary` for this verb and does not fix any summary VALUE, so honoring the flag changes nothing it asserts. Section 5.8 fixes the eleven-field block and its field order, which this plan leaves byte-identical: the same `summary:` line in the same position carries a different value. Spec `attention-registry-and-cross-tree-status` Section 8.8 is CONSULTED rather than amended, and it is what forces the degrading fallback instead of truncation ("Over-length values are a contract violation, not silently truncated"). The only user-facing documentation reference to the verb is one descriptive line in `docs/artifact-lifecycles.md` that does not mention `--summary`, so it stays accurate. The `--summary` help text (`One-line human summary.`) becomes TRUE rather than changing, so it needs no edit; a CHANGELOG `Fixed:` entry is the appropriate user-facing record and is carried by E-05 (REVISED AT REVIEW, PR-006: the authored text deferred it to release time, against the repository's practice of adding the line in the fixing plan).

## Open questions

### OQ-01: Should a user `--summary` replace the per-document role string, prefix or suffix it, or apply only to the `00` prompt?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM CORPUS MEASUREMENT, as COMPOSITION (`<user> (<role>)`), which is the suffix option in the item's enumeration. This is the one decision the backlog item explicitly reserved for a human, and it is answered here from repository evidence rather than returned, because the evidence is decisive in both directions. PROMPT-ONLY, which the item guessed was "probably closest to the flag's intent", is refuted by F-04: the per-document placeholders are demonstrably NOT replaced by hand (9 documents across 2 of this repository's 8 comparison-shaped sets still carry them verbatim), so applying the subject to the prompt alone leaves N+1 of every N+2 documents generically labelled, which is most of the problem unfixed. BARE REPLACEMENT is refuted by F-05: 13 of the 18 human-authored comparison-set summaries name the document's role or model, so that information is what readers of these sets actually rely on and four identical summaries would remove it (rendered in F-06: `INDEX.md` shows four identical entries). COMPOSITION keeps both, which F-06 renders through the real manifest generator. The ROLE is the part parenthesized rather than the user's text, because the user's text is the information and the role is the disambiguator. If the maintainer prefers a different one of the four, the change is confined to `_compose_comparison_summary` and nothing else in this plan moves.

### OQ-02: What should happen when the composed value would exceed the 300-character descriptive bound?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: DROP THE ROLE PARENTHETICAL and write the user's summary alone. The case is real rather than theoretical (F-07: a guarded, safe 290-character summary composes to 334, which `A.is_safe_descriptive` refuses), so the composer must handle it or this plan would make a guarded verb emit a value the guard forbids. The alternatives are each excluded by something already shipped: TRUNCATING the composed value is forbidden in terms by spec `attention-registry-and-cross-tree-status` Section 8.8 ("Over-length values are a contract violation, not silently truncated"); REFUSING the command would turn a bug fix into a new refusal on input `deftzy`'s guard has just declared acceptable, so a user would be refused for a summary the sibling verb accepts; and WRITING IT ANYWAY produces exactly the contract violation. Keeping the user's value and dropping the decoration is the only option that violates nothing and loses only the disambiguator, and it is self-consistent: a 290-character summary is already specific enough that the role parenthetical adds little.

### OQ-03: Should the composer live inside `_mk` or at its call sites?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: AT THE CALL SITES, with `_mk` left signature-unchanged. `_mk` is a closure whose job is to mint an id6, build the name, and render the block; giving it summary-composition logic would mean it needs to know which role string belongs to which document, which is precisely the knowledge the three call sites already express. Composing at the call site also keeps all three role literals visible at the three places that decide what each document IS, which is where a reader looks for them and where E-04's exact-string test points. The cost is three call-site edits instead of one, which is trivially small and is also what makes the E-02 diff readable as "each document now composes its summary" rather than "`_mk` grew a branch".

### OQ-04: Is `- Item-Dependencies: executed:deftzy` a genuine edge or defensive sequencing?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RE-CONFIRMED AT REVIEW (PR-001): the edge is now SATISFIED, since `deftzy` is `executed` and its guard is live at review HEAD; the edge stays declared because it remains true and costs nothing. AUTHORING RATIONALE: RESOLVED: GENUINE, and F-08 is the measurement. At HEAD the guard is absent (`hasattr(research_cmd, '_refuse_unsafe_descriptive')` is False; the module source contains neither `is_safe_descriptive` nor `attention_contract`), and rendering a newline-bearing summary through `build_frontmatter` yields a block whose `parse_frontmatter` returns `status='reference'` and `blocks-release='next'` with `validate_frontmatter` returning `[]`. So executing this plan first would convert a cosmetic defect into a live front-matter injection reachable from a documented flag, which is strictly worse than the bug it fixes. The edge is also SATISFIABLE rather than a stall: `deftzy` is `to-review`, declares `- Item-Dependencies: none`, and F-09 confirms the edge parses to a single well-formed `executed:ipd:deftzy` dependency. The two plans share one file but edit disjoint regions (F-09), and `deftzy`'s own Deferred section names `ol1m2q` as the carrier for this work, so the ordering is its author's stated intent rather than this plan's invention.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste an actual Python session calling `research_cmd._compose_comparison_summary` and showing each returned value, covering: `("", "gpt56 report.")` -> `"gpt56 report."` (byte-identical to the role); `("   ", "gpt56 report.")` -> the same, proving whitespace-only is treated as absent; `("Which widget library", "gpt56 report.")` -> `"Which widget library (gpt56 report)"`, showing the role's trailing period dropped and the user's text unpunctuated by the composer; `("Which widget library", "Originating prompt for the comparison set.")` and `("Which widget library", "Synthesis of the model reports.")` -> the corresponding composed forms. Then the OVER-BOUND case, which is MANDATORY and whose absence fails this item: a user summary of length `A.MAX_DESCRIPTIVE_LEN - 10` composed with `"Originating prompt for the comparison set."` must return the user's value ALONE, and the session must print `len()` of both the rejected candidate and the returned value plus `A.is_safe_descriptive` on each, showing False for the candidate and True for the return. Finally assert `A.is_safe_descriptive` is True on EVERY return across all cases. Also paste the helper's source showing it calls `A.is_safe_descriptive` for the verdict and does NOT reimplement a length or control-character test, and state whether the `attention_contract` import was already present from `deftzy` or added here.
  - Observed evidence:
    Actual Python session output:
    ```
    === Standard cases ===
    User: ''
    Role: 'gpt56 report.'
    Result: 'gpt56 report.'
    is_safe_descriptive: True
    ---
    User: '   '
    Role: 'gpt56 report.'
    Result: 'gpt56 report.'
    is_safe_descriptive: True
    ---
    User: 'Which widget library'
    Role: 'gpt56 report.'
    Result: 'Which widget library (gpt56 report)'
    is_safe_descriptive: True
    ---
    User: 'Which widget library'
    Role: 'Originating prompt for the comparison set.'
    Result: 'Which widget library (Originating prompt for the comparison set)'
    is_safe_descriptive: True
    ---
    User: 'Which widget library'
    Role: 'Synthesis of the model reports.'
    Result: 'Which widget library (Synthesis of the model reports)'
    is_safe_descriptive: True
    ---

    === Over-bound case ===
    MAX_DESCRIPTIVE_LEN: 300
    User length: 290
    Candidate length: 334
    Candidate is_safe_descriptive: False
    Return value length: 290
    Return value is_safe_descriptive: True
    Returned user alone: True
    ```
    Every return satisfies `A.is_safe_descriptive == True`.

    Helper source:
    ```python
    def _compose_comparison_summary(user_summary: str, role: str) -> str:
        """Compose the user's comparison summary with the document role.

        If user_summary is empty or all whitespace, returns role unchanged.
        Otherwise, candidate is f"{user} ({role.rstrip('.')})".
        If that candidate fails A.is_safe_descriptive, degrades to stripped user_summary alone.
        """
        user = user_summary.strip()
        if not user:
            return role
        candidate = f"{user} ({role.rstrip('.')})"
        if not A.is_safe_descriptive(candidate):
            return user
        return candidate
    ```
    The helper calls `A.is_safe_descriptive` for the verdict and does not reimplement a length or control-character test.
    The module-level import `from agent_workflows import attention_contract as A` was added here in `research_cmd.py:22` (pre-existing `deftzy` code had only a lazy import inside `_refuse_unsafe_descriptive`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the actual terminal output of these runs against a throwaway `git init` fixture under the gitignored `tmp/` that carries `.aw/config/project.json` = `{"records_backend": "repository"}`, and paste one `wrote ...` line proving the files landed INSIDE the fixture (PR-003); remove the fixture afterwards. (a) THE FIX: `aw research new-comparison . --set s --slug widget-study --models gpt56,sonnet5 --summary 'Which widget library should we adopt' --apply` at exit 0, followed by `grep -n '^summary:'` over the written files showing all four carrying the user's subject AND its own role parenthetical. (b) THE PRE-FIX COUNTERPART, run at HEAD or in a worktree: the same command at exit 0 with the four generic placeholders and a `grep -rn` for the user string returning NO match, which is the defect as filed (F-01). (c) THE NO-FLAG NON-REGRESSION: the same command with `--summary` omitted, showing the four present-day strings byte-identically including their trailing periods. (d) THE PREVIEW PATH: the `--summary` run WITHOUT `--apply`, showing the composed values in the rendered blocks, since F-03 measured the preview is silent today too. (e) THE MANIFEST: `aw research index --dir .` on the fixture and the resulting `INDEX.md` entries, proving the composed value renders where a human reads it. (f) paste the `summary=sm` line and the three call sites after the edit, showing the dead `or summary` operand is gone and `_mk`'s signature unchanged.
  - Observed evidence:
    All commands run against throwaway fixture carrying `.aw/config/project.json` = `{"records_backend": "repository"}`:

    (a) THE FIX:
    ```
    cmd: aw research new-comparison . --set s --slug widget-study --models gpt56,sonnet5 --summary 'Which widget library should we adopt' --apply
    exit: 0
    wrote <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-00-3x8tlt-widget-study.research-prompt.md
    wrote <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-01-okezhn-widget-study.gpt56.research-report.md
    wrote <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-02-dmkqjx-widget-study.sonnet5.research-report.md
    wrote <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-03-2xpwt9-widget-study.reconciliation.reconciliation-report.md
    next step (informational): run `aw research index` to refresh the manifest

    Grep summary:
    ./.aw/records/research/20261008-s-01-okezhn-widget-study.gpt56.research-report.md:11:summary: Which widget library should we adopt (gpt56 report)
    ./.aw/records/research/20261008-s-00-3x8tlt-widget-study.research-prompt.md:10:summary: Which widget library should we adopt (Originating prompt for the comparison set)
    ./.aw/records/research/20261008-s-03-2xpwt9-widget-study.reconciliation.reconciliation-report.md:11:summary: Which widget library should we adopt (Synthesis of the model reports)
    ./.aw/records/research/20261008-s-02-dmkqjx-widget-study.sonnet5.research-report.md:11:summary: Which widget library should we adopt (sonnet5 report)
    ```

    (b) THE PRE-FIX COUNTERPART:
    ```
    cmd: aw research new-comparison . --set s --slug widget-study --models gpt56,sonnet5 --summary 'Which widget library should we adopt' --apply
    exit: 0
    wrote <repo-root>/tmp/fixture-prefix/.aw/records/research/20261008-s-00-slm1bd-widget-study.research-prompt.md
    wrote <repo-root>/tmp/fixture-prefix/.aw/records/research/20261008-s-01-jj7ck3-widget-study.gpt56.research-report.md
    wrote <repo-root>/tmp/fixture-prefix/.aw/records/research/20261008-s-02-ubh8q7-widget-study.sonnet5.research-report.md
    wrote <repo-root>/tmp/fixture-prefix/.aw/records/research/20261008-s-03-6v8zqh-widget-study.reconciliation.reconciliation-report.md

    Grep summary:
    ./.aw/records/research/20261008-s-01-jj7ck3-widget-study.gpt56.research-report.md:11:summary: gpt56 report.
    ./.aw/records/research/20261008-s-00-slm1bd-widget-study.research-prompt.md:10:summary: Originating prompt for the comparison set.
    ./.aw/records/research/20261008-s-02-ubh8q7-widget-study.sonnet5.research-report.md:11:summary: sonnet5 report.
    ./.aw/records/research/20261008-s-03-6v8zqh-widget-study.reconciliation.reconciliation-report.md:11:summary: Synthesis of the model reports.

    grep -rn 'Which widget library should we adopt' .:
    exit code: 1, output: ''
    ```

    (c) THE NO-FLAG NON-REGRESSION:
    ```
    cmd: aw research new-comparison . --set s --slug widget-study --models gpt56,sonnet5 --apply
    exit: 0
    wrote <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-00-npfzyr-widget-study.research-prompt.md
    wrote <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-01-huj7qc-widget-study.gpt56.research-report.md
    wrote <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-02-q5lpf1-widget-study.sonnet5.research-report.md
    wrote <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-03-f2ksri-widget-study.reconciliation.reconciliation-report.md

    Grep summary:
    ./.aw/records/research/20261008-s-01-huj7qc-widget-study.gpt56.research-report.md:11:summary: gpt56 report.
    ./.aw/records/research/20261008-s-00-npfzyr-widget-study.research-prompt.md:10:summary: Originating prompt for the comparison set.
    ./.aw/records/research/20261008-s-03-f2ksri-widget-study.reconciliation.reconciliation-report.md:11:summary: Synthesis of the model reports.
    ./.aw/records/research/20261008-s-02-q5lpf1-widget-study.sonnet5.research-report.md:11:summary: sonnet5 report.
    ```

    (d) THE PREVIEW PATH:
    ```
    cmd: aw research new-comparison . --set s --slug widget-study --models gpt56,sonnet5 --summary 'Which widget library should we adopt'
    exit: 0
    --- would write <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-00-d857e9-widget-study.research-prompt.md ---
    summary: Which widget library should we adopt (Originating prompt for the comparison set)
    --- would write <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-01-jpw4st-widget-study.gpt56.research-report.md ---
    summary: Which widget library should we adopt (gpt56 report)
    --- would write <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-02-w9ekeh-widget-study.sonnet5.research-report.md ---
    summary: Which widget library should we adopt (sonnet5 report)
    --- would write <repo-root>/tmp/v02-fixture/.aw/records/research/20261008-s-03-dgn6kb-widget-study.reconciliation.reconciliation-report.md ---
    summary: Which widget library should we adopt (Synthesis of the model reports)
    ```

    (e) THE MANIFEST:
    ```
    cmd: aw research index --dir .
    exit: 0
    wrote        .aw/records/research/INDEX.json, INDEX.md (4 docs)
    INDEX.md contents:
    - `3x8tlt` [unrun] 20261008-s-00-3x8tlt-widget-study.research-prompt.md - Which widget library should we adopt (Originating prompt for the comparison set)
    - `okezhn` 20261008-s-01-okezhn-widget-study.gpt56.research-report.md - Which widget library should we adopt (gpt56 report)
    - `dmkqjx` 20261008-s-02-dmkqjx-widget-study.sonnet5.research-report.md - Which widget library should we adopt (sonnet5 report)
    - `2xpwt9` 20261008-s-03-2xpwt9-widget-study.reconciliation.reconciliation-report.md - Which widget library should we adopt (Synthesis of the model reports)
    ```
    Fixture removed cleanly.

    (f) `summary=sm` and call sites in `research_cmd.plan_new_comparison`:
    ```python
            summary=sm,
        )
        return PlannedFile(research_root / R.format_name(name), content)

    # 00 = originating prompt
    files.append(
        _mk(
            0,
            "research-prompt",
            None,
            _compose_comparison_summary(
                summary, "Originating prompt for the comparison set."
            ),
        )
    )
    # 01..N = one report per model
    for i, m in enumerate(norm_models, start=1):
        files.append(
            _mk(
                i,
                "research-report",
                m,
                _compose_comparison_summary(summary, f"{m} report."),
            )
        )
    # N+1 = reconciliation
    files.append(
        _mk(
            len(norm_models) + 1,
            "reconciliation-report",
            "reconciliation",
            _compose_comparison_summary(
                summary, "Synthesis of the model reports."
            ),
        )
    )
    return files, None
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the full `python3 -m pytest tests/test_research_cmd_create.py` output including the `N passed` summary line, naming the added tests. Then paste the PRE-FIX run of the same module showing the primary test FAILING with its assertion text visible, and state explicitly which property failed (the user substring absent from all N+2 planned documents). Confirm which added cases pass in BOTH states and why: the composer unit cases exercise code E-01 adds, so they cannot run pre-E-01 at all, and that must be reported as such rather than as a pass. Show that the over-bound case derives its length from `A.MAX_DESCRIPTIVE_LEN` arithmetic rather than a literal `300`, by pasting the test source line. Also paste, for at least one planned document, that `R.validate_frontmatter` on the parsed block returns `[]` with the composed summary in place.
  - Observed evidence:
    Post-fix run output:
    ```
    python3 -m pytest tests/test_research_cmd_create.py
    ....................                                                     [100%]
    20 passed in 5.24s
    ```
    Added tests:
    - `test_comparison_summary_reaches_all_planned_documents`
    - `test_compose_comparison_summary_unit`
    - `test_comparison_no_summary_exact_strings`
    - `test_comparison_invariants_under_non_empty_summary`

    Pre-fix falsification run output (executed after E-01/E-03 but before E-02):
    ```
    =================================== FAILURES ===================================
    ____ ComparisonTests.test_comparison_summary_reaches_all_planned_documents _____
    [gw11] linux -- Python 3.14.6 <python3>

    self = <tests.test_research_cmd_create.ComparisonTests testMethod=test_comparison_summary_reaches_all_planned_documents>

        def test_comparison_summary_reaches_all_planned_documents(self):
            user_summary = "Which widget library should we adopt"
            files, err = C.plan_new_comparison(
                research_root=self.research,
                set_id="widget-set",
                slug="widget-study",
                models=["gpt56", "sonnet5"],
                summary=user_summary,
            )
            self.assertIsNone(err)
            self.assertEqual(len(files), 4)

            role_tokens = [
                "Originating prompt for the comparison set",
                "gpt56 report",
                "sonnet5 report",
                "Synthesis of the model reports",
            ]
            for f, token in zip(files, role_tokens):
                parsed = _parse_frontmatter(f.content)
                summary_val = parsed.get("summary", "")
    >           self.assertIn(user_summary, summary_val)
    E           AssertionError: 'Which widget library should we adopt' not found in 'Originating prompt for the comparison set.'

    tests/test_research_cmd_create.py:240: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_research_cmd_create.py::ComparisonTests::test_comparison_summary_reaches_all_planned_documents
    1 failed, 19 passed in 4.55s
    ```
    Property that failed: user substring was absent from all planned documents because `_mk` hardcoded `sm` and bypassed `summary`.
    Added cases that pass in both states: `test_compose_comparison_summary_unit`, `test_comparison_no_summary_exact_strings`, and `test_comparison_invariants_under_non_empty_summary` passed before and after E-02. The composer unit test exercises E-01 code and cannot run pre-E-01 at all.
    Over-bound case length derivation (from `tests/test_research_cmd_create.py:268`):
    ```python
        long_user = "u" * (A.MAX_DESCRIPTIVE_LEN - 10)
    ```
    `R.validate_frontmatter` on planned documents with composed summaries:
    ```
    20261008-widget-set-00-yuoawc-widget-study.research-prompt.md -> summary: 'Which widget library should we adopt (Originating prompt for the comparison set)' -> validate_frontmatter: []
    20261008-widget-set-01-wpdu5b-widget-study.gpt56.research-report.md -> summary: 'Which widget library should we adopt (gpt56 report)' -> validate_frontmatter: []
    20261008-widget-set-02-2uqupo-widget-study.sonnet5.research-report.md -> summary: 'Which widget library should we adopt (sonnet5 report)' -> validate_frontmatter: []
    20261008-widget-set-03-2t99pu-widget-study.reconciliation.reconciliation-report.md -> summary: 'Which widget library should we adopt (Synthesis of the model reports)' -> validate_frontmatter: []
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the test output for the no-flag and invariant tests by name. The no-flag test must assert and show EXACT equality against `Originating prompt for the comparison set.`, `gpt56 report.`, `sonnet5 report.` and `Synthesis of the model reports.`, trailing periods included, and must PASS both before and after the E-02 edit; paste both runs, because a no-flag test that only passes afterwards would mean the change is not opt-in. The invariant test must show, under a NON-EMPTY summary, N+2 files with orders `00..N+1` and the kinds in order (`research-prompt` at `00` with `model` None, one `research-report` per model in the given order, `reconciliation-report` with model `reconciliation` last), the prompt carrying NO `status:` key and every other document carrying `status: todo`.
  Then paste the full-suite run (`python3 -m pytest`, bare) with its `N passed` line, the targeted regression set from the validation section with its own `N passed` line, and the repository-tree `aw research index --check --agent` output. For that last one paste the PRE-CHANGE rule set (taken at the executing HEAD before E-02) and the POST-CHANGE rule set, and show no rule id appears after that was absent before; authored counts (142 at authoring, 179 at review) are context only. The required property is that this plan ADDS no rule, not that the count is zero (F-11, PR-004).
  - Observed evidence:
    No-flag and invariant tests by name:
    ```
    python3 -m pytest tests/test_research_cmd_create.py -k "test_comparison_no_summary_exact_strings or test_comparison_invariants_under_non_empty_summary" -v
    ..                                                                       [100%]
    2 passed in 4.38s
    ```
    Exact equality against four strings with trailing periods:
    - `test_comparison_no_summary_exact_strings` asserts exact equality against `Originating prompt for the comparison set.`, `gpt56 report.`, `sonnet5 report.`, and `Synthesis of the model reports.`; passed both in pre-E-02 run (`1 failed, 19 passed`) and post-E-02 run (`20 passed`).
    - `test_comparison_invariants_under_non_empty_summary` asserts N+2 files, orders `00..03`, kinds and models in order (`research-prompt` None, `research-report` gpt56, `research-report` sonnet5, `reconciliation-report` reconciliation), prompt has no `status:`, other reports have `status: todo`, all `validate_frontmatter == []`.

    Full suite bare run:
    ```
    python3 -m pytest
    6637 passed, 2 skipped, 3 warnings in 922.81s (0:15:22)
    ```

    Targeted regression set:
    ```
    python3 -m pytest tests/test_research_cmd_create.py tests/test_research_descriptive_safety.py tests/test_research_index.py tests/test_artifact_adopt.py
    ........................................................................ [ 56%]
    ........................................................                 [100%]
    128 passed in 5.34s
    ```

    `aw research index --check --agent` rule set comparison:
    Pre-change rule set: `['adopted-without-consumer', 'check.stale-index-missing', 'dangling-citation', 'frontmatter-invalid', 'stale-state-to-promote']` (229 diagnostics)
    Post-change rule set: `['adopted-without-consumer', 'check.stale-index-missing', 'dangling-citation', 'frontmatter-invalid', 'stale-state-to-promote']` (229 diagnostics)
    Zero new rules added.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `git diff CHANGELOG.md` showing exactly ONE added `- Fixed:` line under the `## 2.0.0 (pending)` heading, and paste a search over that line for em and en dashes returning nothing.
  - Observed evidence:
    `git diff CHANGELOG.md`:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 6902506d9..e26f645e6 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: aw research new-comparison --summary is now written onto every scaffolded document as <summary> (<role>) instead of being silently discarded, and omitting --summary leaves the output unchanged.
     - Fixed: aw specs set and aw set now refuse to mark a spec implemented unless a resolvable evidence citation is supplied, whichever spelling is used, and aw set now accepts --evidence so that citation can be given.
     - Added: documented CommandDeclaration.exit_contract as enumerating codes produced by a command's own return path while excluding signal-derived codes (130/143), pinned by a conformance gate on the universal 130 floor (D162).
     - Fixed: aw config get --help no longer claims a nonzero exit for an unset variable.
    ```
    Dash check on added line:
    ```
    Line: '+- Fixed: aw research new-comparison --summary is now written onto every scaffolded document as <summary> (<role>) instead of being silently discarded, and omitting --summary leaves the output unchanged.'
    Has em dash: False
    Has en dash: False
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. It carries NO `- Readiness:` field and NO `- Approval:` field, because both are attestations produced by roles this authoring pass did not perform (`/plan-review` owns the first, a human owns the second); writing either here would forge it.

DEPENDENCY NOW SATISFIED (review, PR-001): `deftzy` is in `executed/`; the runner will find the edge met. The original constraint is retained as the rationale: DO NOT EXECUTE BEFORE `deftzy` REACHES `executed`. This plan declares `- Item-Dependencies: executed:deftzy` and the edge is load-bearing rather than cosmetic: F-08 measures that at HEAD the descriptive-safety guard does not exist, so making this flag live first routes an unvalidated user string into a hand-split front-matter block where a newline becomes a real `status:` or `blocks-release:` key at zero `validate_frontmatter` drift. The runner re-checks dependencies at dispatch and will mark this item `dependency-blocked` rather than run it; an agent executing by hand must honor the same order. (At authoring `deftzy` was `to-review`; it has since executed.)

Execute only the checklist above; commit through `aw commit wjvn8a -- agent_workflows/research_cmd.py tests/test_research_cmd_create.py CHANGELOG.md` and never `git add -A`, verifying the staged set before the commit because this checkout is shared. Do not push and do not tag.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every claim of a pass, never a summary you did not run. V-02 and V-03 each require a PRE-FIX run showing the defect, and a fabricated one would assert the very coverage it is meant to prove. Run the suite BARE (`python3 -m pytest`); the configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, and a second `-q` would suppress the `N passed` line this gate requires.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the three paths in `- Scope-Paths:`. If execution finds another path must change, MAKE the edit and JUSTIFY it at finalize (`--scope-reason`) rather than stopping. Do not stop and wait over a scope question. The conditions that DO warrant stopping and reporting are: a concurrent edit to `research_cmd.py` that cannot be safely combined with this change, or `deftzy` having landed a guard whose shape makes the composed value refuse where the user's input alone would not (which would mean OQ-02's fallback needs revisiting with the maintainer rather than working around).

All open questions are resolved and none is blocking (OQ-01 through OQ-04).

Before the terminal transition, `aw ipd lint --phase pre-transition` must report conforming and every `V-*` above must carry pasted evidence. The transition is then UNCONDITIONALLY owed with a CONDITIONAL owner: in a managed lane the RUNNER owns it (`aw ipd begin`/`finalize` refuse an agent there with `AW-LIFECYCLE-ROLE-001`), and only in an unmanaged or manual run does the executor run `aw ipd finalize wjvn8a --actor <agent/model> --message <summary> --apply` itself. Never hand-roll the move with `git mv` and never hand-edit `- Status: executed`.
