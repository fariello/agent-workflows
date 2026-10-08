# IPD: Give the research checker the unsafe descriptive field rule, and repair the three over-length committed summaries

- Date: 2026-10-02
- Kind: child
- Concern: `research_contract.validate_frontmatter` applies NO output-safety predicate to any field, so an over-length or control-character-bearing descriptive value is unchecked and reaches a terminal and a committed manifest raw. Measured in this lane at HEAD `f81b44e62`: a research doc whose `summary:` is `red<ESC>[31mINJECTED<ESC>[0m` yields `validate_frontmatter == []`, `aw check research --agent` `"outcome":"conforms"` exit 0, and `aw research index --check` exit 0 clean, while `aw attention --format json` reports `"detail_text": "red\u001b[31mINJECTED\u001b[0m"` with `"valid": true` and `"violations": []`, and `aw research index` WRITES those bytes into the generated `INDEX.md` (4 ESC bytes). Spec `attention-registry-and-cross-tree-status` Section 8.8 states "the renderers never emit raw control characters", so this is a live violation of an implemented contract. Three COMMITTED summaries already exceed the 300-character bound (395, 351, 320), which forces an explicit repair-or-grandfather decision rather than only a new rule.
- Scope: Judge the research tree's descriptive front-matter values with the shared `attention_contract.is_safe_descriptive` predicate under the already-catalogued `attention.unsafe-field` id, emitted from `research_index.check_drift` (NOT from `validate_frontmatter`, which would DROP the doc from the index); repair the three over-length committed summaries FIRST so the rule ships fail-closed with no grandfather tier. The id is already in `RULE_IDS` and already registered in `RULE_REGISTRY` at `error`, so this mints no policy.
- Scope-Paths: agent_workflows/research_index.py, tests/test_research_unsafe_field.py, .aw/records/research/reference/202609/20260905-hostskill-04-6asl6q-host-skill-runtime-discovery-and-authoring.reconciliation.reconciliation-report.md, .aw/records/research/reference/202609/20260905-awmetastore-05-6mye7n-where-aw-metadata-should-live.reconciliation.reconciliation-report.md, .aw/records/research/archive/202609/20260905-awmetastore-06-g5f3zq-aw-artifact-metadata-storage-research-report.gemini31prodeepthink.research-report.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: cvxbbu
- Blocks-Release: next
- Set: cvxbbu
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: xnogdl
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004, all FIXED. Reviewed in lane review-sweep-run-20261007T032752Z-4094028 at HEAD 250466250; review record .aw/records/reviews/20261002-cvxbbu-01-xnogdl-give-the-research-checker-the-unsafe-descriptive-field-rule.review.md. Census, registry, F-06 drop and F-07 gate re-measured and hold. PR-001: executed jnpl08 now reports the injected duplicate status via research.frontmatter-key-repeated, so E-05 LIMIT ONE asserts that and the unreported blocks-release residue. PR-002: LIMIT TWO no longer pins raw aw attention output, which reviewed plan qpw45x will change. PR-003: stale deftzy evidence path, CLI driver and baseline counts refreshed. PR-004: E-03 stop narrowed to the no-consumer case.

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `cvxbbu`, the checker-half carrier filed by pending plan `deftzy` (Set `7w6zsl`), which closes the research WRITE paths. Every claim the item makes REPRODUCES at HEAD `f81b44e62`: `validate_frontmatter` judges `summary` for nothing, the ANSI value passes all three gates, the bytes reach `INDEX.md` and `aw attention`, and the census still finds exactly 3 over-bound summaries (n grew 124 -> 127, same three files, median still 108). TWO AUTHORED CORRECTIONS to the item, both measured. FIRST, the item says the rule "probably needs no minting" because `attention.unsafe-field` is catalogued and `ynhst5` "is registering it": that registration has LANDED, so `check_engine.RULE_REGISTRY` already carries it at `error` and E-04 of the sibling is DONE; this plan adds a call site only and touches no registry. SECOND, and this is the design-deciding finding the item does not contain: emitting the rule from `validate_frontmatter` would make every offending doc `frontmatter-invalid`, which `research_index._doc_entry` treats as fatal and DROPS the doc from the index entirely (driven: entries fell 1 -> 0 on a fixture), so the fix would delete three records from the manifest to report a summary-length problem. The emitter therefore belongs in `check_drift`, beside the four existing research drift rules. Also measured and recorded as context rather than scope: default `aw check research` reaches NO research content validator at all, because the `research` branch of `check_engine.check_content` is gated `if dirs and include_retired`, exactly as its `plans` twin is.

## Goal

Make an over-length or control-character-bearing research descriptive value a named, fail-closed `aw check` finding instead of silently valid text that reaches a human terminal and a committed `INDEX.md` unescaped. Close the part of the Section 8.8 trust boundary a CHECKER can reach, repair the three records that already violate it, and state plainly the part no checker can reach.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: repair the existing population FIRST

- [x] E-01 Shorten the `summary:` value of the three committed research docs that exceed `A.MAX_DESCRIPTIVE_LEN` (300), BEFORE any rule exists, so the tree is clean when the rule lands and the rule can ship fail-closed with no grandfather tier. The three, with lengths measured at authoring: `20260905-hostskill-04-6asl6q-...reconciliation-report.md` (395, `status: reference`), `20260905-awmetastore-05-6mye7n-...reconciliation-report.md` (351, `status: reference`), and `20260905-awmetastore-06-g5f3zq-...gemini31prodeepthink.research-report.md` (320, `status: archive`). Reduce each to at most 300 characters while preserving its meaning.
  THIS ORDERING IS THE WHOLE REASON THIS IS ITEM ONE, AND THE REASON IS CI, NOT TIDINESS. The `attention.unsafe-field` id is ALREADY REGISTERED at `error` severity (F-04), and `artifact_core.drift_exit_code` exempts only `info`, so if the rule landed first, `aw research index --check` would gain three `error` findings on a clean checkout. Fixing first makes the rule's arrival a no-op on the tree, which is also the evidence V-01 demands. THE SIBLING'S SECOND REASON DOES NOT APPLY HERE and must not be copied: `ynhst5` E-01 also had a LIFECYCLE DEADLOCK argument, because `specs.run_set` re-runs `validate_spec` on prospective text and would refuse to transition an offending spec. No research verb re-validates on transition this way (`aw research promote`/`set-outcome`/`set-priority` edit front-matter lines directly), and this plan's rule lives in `check_drift` rather than in `validate_frontmatter`, so no research record is ever locked out of its own lifecycle by the new finding. Stating this difference matters because it is the only argument that would survive a decision to grandfather instead.
  EDIT THESE THREE FILES BY HAND, NOT THROUGH ANY `aw research` VERB. This is a text repair to one front-matter line, not a status transition or a regroup; `aw research set-outcome`/`promote` exist to move a record through its lifecycle, and pointing one at a conformance repair would rewrite state that is correct. `aw commit xnogdl -- <the three paths>` is still the commit route.
  DO NOT DELETE INFORMATION TO MEET THE BOUND, and do not touch the body. A `summary:` is a one-line abstract of a document whose body carries the detail, so compress the summary; all three currently pack multiple sentences into the field. Do NOT edit any other front-matter key, and specifically do NOT alter `status:`, `outcome:`, `consumed-by:` or the document body. One of the three (`g5f3zq`) sits under `archive/` and one (`6mye7n`) carries `outcome: adopted`; a records repair is not a promotion, a re-adoption, or an un-archiving.
  - Depends on: none
  - Expected outcome: all three `summary:` values are at most 300 characters and still describe the same document; a census over the whole research tree reports ZERO `summary:` values failing `A.is_safe_descriptive`, where it reported 3 before; and `aw research index --check` gains no new finding relative to its pre-repair baseline.
  - Execution state: performed

### Task group 2: emit the rule where it cannot destroy the index

- [x] E-02 In `research_index.check_drift`, judge each indexed entry's descriptive values with `A.is_safe_descriptive` and emit the EXISTING `attention.unsafe-field` rule id on failure, enriched through `_ce.enrich_drift` exactly as the four neighbouring research drift rules are. Judge `summary`, each `topic` TOKEN, and each `consumed-by` TOKEN. Add the `attention_contract` import to the module.
  EMIT FROM `check_drift`, NOT FROM `validate_frontmatter`, AND THIS IS THE LOAD-BEARING DESIGN DECISION OF THE PLAN. `research_index._doc_entry` treats a non-empty `validate_frontmatter` result as FATAL: it returns `(None, [Drift(rel, "frontmatter-invalid", ...)])`, so the document yields NO `DocEntry` and is DROPPED from the manifest. Driven on a fixture (F-06): adding an unsafe-summary error to `validate_frontmatter` took the indexed entry count from 1 to 0. On the real tree that would delete three records from `INDEX.json`/`INDEX.md` as the means of reporting that their summaries are too long, which is a worse outcome than the defect. `check_drift` runs AFTER `_scan_docs` and reports against entries that remain indexed, which is where the four existing content rules (`stale-state-to-promote`, `dangling-consumed-by`, `adopted-without-consumer`, `unrecognized-model`) all live for the same reason.
  USE THE CATALOGUED ID AND DO NOT MINT ONE. `attention.unsafe-field` is a member of the closed `attention_contract.RULE_IDS` catalog, is documented there as "control-char / over-length / newline / non-http issue url", and is ALREADY EMITTED for this violation class by `specs.validate_spec` and `releases.validate_release`. Note the deliberate asymmetry this accepts: the four existing research rules are BARE ids (`stale-state-to-promote`, not `research.stale-state`), while this one is namespaced, because it is a cross-tree id borrowed from the catalog rather than a research-local rule. That is correct and is NOT a reason to rename it to a bare `unsafe-field`; OQ-02 records the alternatives.
  ENRICH AT THE EMITTER. The module's own comment states why: "Severity is stamped at the emitter ... neither `run_index` nor `check_engine.check_content` enriches these findings, so an un-enriched `severity=""` would still fail the gate". Verified at authoring that an unenriched drift already exits 1 via `drift_exit_code`, so enrichment is about making the severity DECLARED rather than accidental, matching the three neighbours that call `_ce.enrich_drift`. Note `dangling-consumed-by` is emitted WITHOUT enrichment today; follow the enriched majority, and do not "fix" that one here.
  KEEP THE DETAIL VALUE-FREE. Name the FIELD and the failing PROPERTY, never the offending value: the detail lands in the `location<TAB>rule<TAB>detail` agent record and in human output, so echoing an ANSI-bearing value would push the exact payload this rule exists to flag into the surface it protects, and `A.escape_detail` escapes only tab, newline and backslash, NOT C0/C1 controls. For a length failure the detail MAY carry the measured length, which is a number and not attacker-controlled text. Follow the sibling's wording so a user meets one vocabulary across trees.
  - Depends on: E-01
  - Expected outcome: an indexed research doc whose `summary` is 301 characters, or contains a BEL, an ANSI ESC, or a C1 control, yields exactly one `attention.unsafe-field` drift from `check_drift` with `severity == "error"`; a 300-character summary yields none; an unsafe `topic` or `consumed-by` token yields one naming that field; the doc REMAINS in the returned entry list in every case; and the detail contains neither the offending value nor a raw control byte.
  - Execution state: performed

- [x] E-03 Verify, and record as pasted evidence rather than as an assertion, that the new rule reaches its consumers and changes no exit code on the repaired tree. Make no code change in this item unless the verification exposes a gap. If the gap is that the rule reaches NONE of its intended consumers, STOP and report, because the emitter placement then needs re-deciding (the gate names this condition). Any narrower gap is to be FIXED and, if it touches a path outside `- Scope-Paths:`, JUSTIFIED at finalize with `--scope-reason` (REVISED AT REVIEW, PR-004: a stop over a scope question contradicts the scope-fence ruling).
  CHECK ALL THREE CONSUMERS, because `check_drift` has more than one caller and they do not agree on what they run. (a) `aw research index --check` calls `check_drift` directly and is the surface where the rule actually gates. (b) `aw check research` reaches it through `check_engine.check_content`, whose `research` branch is gated `if dirs and include_retired`, so the DEFAULT invocation runs NO research content validator at all and the rule is invisible there until `--all` is passed. (c) `aw check all` fans out through the same branch. MEASURED AT AUTHORING on a fixture: `check_content(include_retired=False)` returned 0 drifts while `include_retired=True` returned the 2 `check.stale-index-missing` findings, proving the gate. THIS GATE IS PRE-EXISTING AND SYMMETRIC WITH `plans` (whose branch carries the identical `if dirs and include_retired`), so it is NOT this plan's defect and NOT this plan's to change; removing it would turn `aw check research` from a names/refs check into a full content check and alter the exit code of an unrelated command. Record it so no reviewer concludes from a clean default `aw check research` that the rule does not work.
  - Depends on: E-02
  - Expected outcome: the rule is demonstrated firing through `aw research index --check` (exit 1 on an unsafe fixture) and through `aw check research --all`, and demonstrated NOT firing on the repaired repository tree, with the pre-existing `include_retired` gate documented rather than altered.
  - Execution state: performed

### Task group 3: pin the coverage and the honest limits

- [x] E-04 Add `tests/test_research_unsafe_field.py` pinning the new coverage for every Section 8.8 shape a checker CAN see, driving `research_index.check_drift` against temporary fixture repositories: over-length, BEL, ANSI ESC and a C1 control on `summary`; an unsafe `topic` token; an unsafe `consumed-by` token; the exact 300/301 boundary; and each case asserting the `attention.unsafe-field` id and `severity == "error"`.
  PIN THE NON-DESTRUCTION PROPERTY, which is this plan's central design choice and the one a later refactor is most likely to undo: assert for each unsafe case that the document is STILL PRESENT in the entries `_scan_docs`/`check_drift` return, and that NO `frontmatter-invalid` drift is emitted for it. A test that only checks the finding fires would pass equally for the destructive `validate_frontmatter` placement that F-06 measured dropping the doc. Name F-06 in the test's comment.
  TEST OUTCOMES, NOT CODE STRUCTURE (AGENTS.md, GUIDING_PRINCIPLES P16). Every assertion must drive `check_drift`, `validate_frontmatter` or a CLI and assert on returned drift, entry lists, exit codes or emitted bytes. Do NOT assert on `inspect.getsource`, a call count, a symbol census, or the presence of any comment; the registry assertion must read `check_engine.rule_spec("attention.unsafe-field")` and compare `RuleSpec` fields rather than grepping the module text.
  - Depends on: E-03
  - Expected outcome: a new module whose over-length and control-character cases FAIL against pre-E-02 code (`check_drift` returns no `attention.unsafe-field` drift) and PASS after; whose non-destruction assertions pass after; and whose boundary case proves 300 accepted and 301 refused.
  - Execution state: performed

- [x] E-05 In the same module, pin the two LIMITS and the non-regressions, because this is what keeps the record honest about what a checker cannot do.
  LIMIT ONE, THE NEWLINE VECTOR, which the backlog item itself names and which THIS RULE cannot close. REVISED AT REVIEW (PR-001): executed plan `jnpl08` (`7d4bgs`) now emits `research.frontmatter-key-repeated` from `check_drift` for any key that appears twice, so the vector is PARTLY visible to a checker: an injected key that DUPLICATES a legitimate one (`status`) is reported, while an injected key the legitimate block does not carry (`blocks-release`) is reported by NOTHING. Measured at review HEAD `250466250` on the block below: `check_drift` rule set `['check.stale-index-missing', 'research.frontmatter-key-repeated']`, the document still indexed. So assert ALL of: NO `attention.unsafe-field` drift; exactly one `research.frontmatter-key-repeated` drift, naming `status`; and NO drift of any rule naming `blocks-release`, which is the residue no checker reaches. Assert that a front-matter block produced by newline injection (a `summary: legit` line followed by a smuggled `status: reference` and `blocks-release: next`) yields NO `attention.unsafe-field` drift, because `parse_frontmatter` splits the value into separate lines BEFORE any validation runs and hands the checker only the safe half. Driven at authoring (F-05): the checker sees `summary == 'legit'`, `is_safe_descriptive` is correctly True, `validate_frontmatter` is `[]`, AND the injected `status` WINS the reader's last-wins race so the record reports `status: reference`. Assert that last-wins override too, so the test records the severity rather than just the blind spot, and name `deftzy` as the write-path carrier in the comment. A reader must not be able to conclude from this module that the injection is closed.
  LIMIT TWO, THE RULE REPORTS AND DOES NOT SANITIZE. Assert the observable property that is stable whatever the renderers later do: running `check_drift` (and `aw research index --check`) on an unsafe fixture leaves the document's bytes UNCHANGED on disk and does not alter the value the index entry carries, so the rule makes the condition a named finding and repairs nothing. REVISED AT REVIEW (PR-002): do NOT assert that `aw attention` emits the bytes RAW. That is a known defect, and reviewed plan `llnvwj` (`qpw45x`, E-01 `neutralize_control_characters` applied to `detail_text`) is set to change it, so such an assertion would pin accidental behavior the project intends to replace and would go red the day that plan lands. Name `llnvwj` as the escaping carrier in the test comment instead.
  Non-regressions, each naming why it could plausibly break: (a) the three repaired records and the whole live research tree produce ZERO `attention.unsafe-field` findings, read from the repository rather than from hard-coded lengths; (b) the four existing research drift rules still fire on their own fixtures, since this item adds a loop over the same entries; (c) a doc with an empty `topic: []` and `consumed-by: []` yields nothing, since a per-token loop over an empty list must not fault; (d) `validate_frontmatter` is UNCHANGED, asserted by driving it directly with an unsafe summary and observing `[]`, which is the deliberate under-scope E-02 names and the thing that keeps the doc indexed.
  - Depends on: E-04
  - Expected outcome: both limit cases pass in the post-fix state, and the parts of them that do not concern `attention.unsafe-field` (the `frontmatter-key-repeated` finding, the unreported `blocks-release`, the unchanged bytes) pass in the pre-fix state too, documenting what is not closed; all four non-regression groups pass; and (d) asserts `validate_frontmatter` still returns `[]` for an unsafe summary, proving the emitter placement.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE RULE ID EXISTS AND IS ALREADY REGISTERED, so this plan adds a CALL SITE and mints nothing. This is a material correction to the backlog item, which says the id "is NOT in `check_engine.RULE_REGISTRY`" and that the sibling "is registering it". That sibling (`ynhst5`) is now `executed`, and the entry is present at `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")` (F-04). So E-04 of the sibling is DONE and this plan must not re-add it.
- A `validate_frontmatter` ERROR IS FATAL TO INDEXING, which is the fact that decides where the rule goes. `research_index._doc_entry` returns `(None, [Drift(..., "frontmatter-invalid", ...)])` on any validation error, so the document produces no `DocEntry` at all. Emitting a cosmetic-severity finding through a fatal channel would remove the record from the manifest (F-06).
- THE FOUR EXISTING RESEARCH CONTENT RULES ALL LIVE IN `check_drift`, not in the contract: `STALE_STATE_RULE`, `DANGLING_CONSUMED_RULE`, `ADOPTED_NO_CONSUMER_RULE` and `UNRECOGNIZED_MODEL_RULE` are module constants emitted there, and the `unrecognized-model` comment states the principle explicitly ("Emitted in check_drift ONLY (never in `_doc_entry` or `_scan_docs`), so the regenerate branch of `run_index` is not blocked"). This plan follows that established placement.
- THE RESEARCH RULE IDS ARE BARE, WHILE THE CATALOGUED ONE IS NAMESPACED, so this plan introduces a deliberate naming asymmetry inside one module rather than a new convention. The four above carry no prefix; `attention.unsafe-field` does, because it is a cross-tree catalog id. OQ-02 records why borrowing beats renaming.
- SEVERITY IS STAMPED AT THE EMITTER IN THIS MODULE, by its own recorded reasoning: "neither `run_index` nor `check_engine.check_content` enriches these findings, so an un-enriched `severity=''` would still fail the gate on a merely-absent manifest". Three of the four neighbours call `_ce.enrich_drift`; `DANGLING_CONSUMED_RULE` does not, which is a pre-existing inconsistency this plan follows the majority of rather than fixing.
- `aw check research` REACHES NO RESEARCH CONTENT VALIDATOR BY DEFAULT. The `research` branch of `check_engine.check_content` is gated `if dirs and include_retired`, and `cli.py` derives that from `--all` (`include_retired = bool(getattr(args, "all", False))`). Measured: default returned 0 drifts where `--all` returned 2. The `plans` branch carries the identical gate, so this is a deliberate repository-wide shape, not a research bug, and it is out of scope (E-03 documents it).
- `is_safe_descriptive` IS THE SHARED PREDICATE AND NEEDS NO CHANGE: it bounds length at `MAX_DESCRIPTIVE_LEN` (300), rejects `\n`/`\r`, and rejects `_CONTROL_CHAR_RE`. This plan consults it and does not fork or re-implement its conditions.
- THE GOVERNING SPEC ALREADY REQUIRES THIS, so no spec amendment is needed. Spec `attention-registry-and-cross-tree-status` Section 8.8 requires bounded single-line control-char-free descriptive fields; its F10 makes violations "stable named `--check` failures"; its A14 requires hostile-string fixtures of exactly these shapes, which E-04 supplies for this tree.
- THE RESEARCH FRONT-MATTER SCHEMA IS SPEC-GOVERNED AND UNTOUCHED. Spec `agents-artifact-organization` Section 5.8 fixes the eleven-field block, and `research_contract.FRONTMATTER_FIELDS` is that list. A new drift rule adds no field, changes no order, and alters no grammar.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal`. Do not pass `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).

## Findings

All findings were DRIVEN in this lane at HEAD `f81b44e62`: the census figures over the real `.aw/records/research/` tree, the behavioral ones against temporary fixture repositories under the gitignored `tmp/`, so nothing measured here is committed.

| # | Finding | Evidence |
|---|---|---|
| F-01 | (Review note, PR-003: executed plan `deftzy` now REFUSES the driver below, `aw research new: --summary must not contain control characters`, so at review HEAD the defect is reachable only through a hand-written or pre-existing file, which is how E-04/E-05 already build fixtures; `validate_frontmatter` still returns `[]` for such a value.) THE ITEM'S REPORTED DEFECT REPRODUCES EXACTLY. `research_contract.validate_frontmatter` applies no output-safety predicate to any field, so an ANSI-bearing `summary` is accepted. | Driven: `aw research new . --kind findings --slug x --summary $'red\x1b[31mINJECTED\x1b[0m' --apply` exited **0**; the written file contains **2 ESC bytes**; `parse_frontmatter` returned `summary == 'red\x1b[31mINJECTED\x1b[0m'`; `A.is_safe_descriptive` on it is **False** while `R.validate_frontmatter(fm)` returned **`[]`**. Reading the function confirms it judges `summary` for presence only, and checks `id`/`created`/`order` shapes, `topic`/`consumed-by` list-ness, and `model`/`kind`/`status`/`outcome`/`priority` vocabularies. |
| F-02 | EVERY GATE PASSES IT, so the raw bytes reach a terminal and a COMMITTED MANIFEST. | Driven on an isolated fixture repo: `aw check research --agent` reported `"outcome":"conforms","exit":0` (its one finding the unrelated pre-existing `check.collisions-not-checked`); `aw research index --check` exited **0** reporting `clean`; `aw research index` WROTE the bytes into the generated `INDEX.md` (**4 ESC bytes** in the file); `aw attention --details --no-color` printed `summary: red^[[31mINJECTED^[[0m`; and `aw attention --format json` reported `"detail_text": "red\u001b[31mINJECTED\u001b[0m"` with **`valid: True`** and **`violations: []`**. Section 8.8 states "the renderers never emit raw control characters". |
| F-03 | THE CENSUS REPRODUCES AND CONSTRAINS THE FIX. THE DURABLE CLAIM IS THE PROPORTION AND THE FILE SET, not the counts, which grow as records land. | Measured over every parsable `summary:` in `.aw/records/research/**/*.md`: **n=127** (the item measured 124), **3 exceed 300** and they are the SAME three files the item names, at **395** (`6asl6q`, `status: reference`), **351** (`6mye7n`, `status: reference`, `outcome: adopted`), **320** (`g5f3zq`, `status: archive`); **0** carry a control character; median **108**. Every `topic` token is within bound (max **25**) and every `consumed-by` token is (max **6**), with zero unsafe in either. So three records need repair and no token does. |
| F-04 | THE ID IS ALREADY REGISTERED, CORRECTING THE ITEM. The item says it "is NOT in `check_engine.RULE_REGISTRY`" and that `ynhst5` "is registering it"; that plan is now `executed` and the entry has landed. | Driven: `'attention.unsafe-field' in check_engine.RULE_REGISTRY` is **True**, returning `RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='')`. The id is also a member of `attention_contract.RULE_IDS` and is emitted today by `specs.validate_spec` (three sites) and `releases.validate_release` (two sites). So this plan adds a call site and touches no registry. Separately, `artifact_core.drift_exit_code` returns **1** for this rule both unenriched and enriched, so it gates either way. |
| F-05 | PARTLY SUPERSEDED AT REVIEW (PR-001): executed plan `jnpl08` now reports a REPEATED key from `check_drift`, so the injected duplicate `status` is a `research.frontmatter-key-repeated` finding at review HEAD; an injected NON-duplicate key (`blocks-release`) is still reported by nothing, and `attention.unsafe-field` still cannot see either. AUTHORING TEXT RETAINED: THE NEWLINE VECTOR IS UNREACHABLE FROM ANY CHECKER, so this plan CANNOT close the injection the item reports, and the item is right to say so. The severity is also HIGHER than a blind spot: the smuggled key WINS. | Driven on an injected block (`summary: legit` then `status: reference` then `blocks-release: next`): `parse_frontmatter` returns `summary == 'legit'`, a safe bounded control-char-free line, so `is_safe_descriptive` is correctly **True** and `validate_frontmatter` is **`[]`**. Meanwhile `status` resolves to **`'reference'`**, not the legitimate `todo`, because `parse_frontmatter` is a line-wise `key, _, val = line.partition(":")` splitter with LAST-WINS semantics, and `blocks-release` resolves to **`'next'`**. The unsplit value exists only at the write path, which is `deftzy`'s scope. |
| F-06 | **EMITTING FROM `validate_frontmatter` WOULD DROP THE DOCUMENT FROM THE INDEX**, which is the design-deciding finding and is not in the backlog item. | Driven: `research_index._doc_entry` returns `(None, [Drift(rel, "frontmatter-invalid", ...)])` whenever `validate_frontmatter` is non-empty. Patching an unsafe-summary error into `validate_frontmatter` on a one-doc fixture took `_scan_docs` from **`entries: 1`** to **`entries: 0`**, emitting `frontmatter-invalid` in its place. On the real tree all three offenders are CURRENTLY INDEXED (verified present among **126** indexed entries), so that placement would delete three records from `INDEX.json`/`INDEX.md` as the means of reporting a summary-length problem. `check_drift` runs after `_scan_docs` and reports against entries that remain indexed. |
| F-07 | DEFAULT `aw check research` RUNS NO RESEARCH CONTENT VALIDATOR, so the rule's visibility there depends on a flag. Pre-existing and symmetric with `plans`; recorded, not fixed. | The `research` branch of `check_engine.check_content` reads `if dirs and include_retired: drift.extend(_ridx.check_drift(...))`, and `cli.py` sets `include_retired = bool(getattr(args, "all", False))`. Driven on a fixture with the manifests deleted: `check_content(include_retired=False)` returned **0** drifts; `include_retired=True` returned **2** (`check.stale-index-missing` twice). The `plans` branch carries the byte-identical `if dirs and include_retired` gate. |
| F-08 | (Review note, PR-003: at review HEAD `250466250` `aw research index --check` is exit 1 with `dangling-citation` 122, `adopted-without-consumer` 35, `stale-state-to-promote` 19, `check.stale-index-missing` 2, `frontmatter-invalid` 1; the counts drifted, the rule set did not. The census is n=129 with the same three offenders.) THE REPOSITORY BASELINES, so an executor does not chase a pre-existing finding. THESE ARE EXIT-CODE AND RULE-SET CLAIMS, NOT COUNTS. | Driven on the real tree: `aw check research --agent` reports `"outcome":"conforms","findings":1` exit **0**, the one finding the pre-existing `check.collisions-not-checked` advisory. `aw check research --all --agent` reports `"findings":136` exit **0**. `aw research index --check` exits **1** with **135** findings whose rule histogram is `dangling-citation` 78, `adopted-without-consumer` 35, `stale-state-to-promote` 19, `check.stale-index-missing` 2, `frontmatter-invalid` 1. NONE is `attention.unsafe-field`. Re-derive at execution and compare RULE SETS, not totals. |
| F-09 | NO TEST ANYWHERE PINS RESEARCH DESCRIPTIVE SAFETY, so nothing pins the current behavior in either direction. | `grep -rn "unsafe-field" agent_workflows/*.py` matches only the catalog, the registry, `specs.py` and `releases.py`; no research module. The specs/releases coverage added by `ynhst5` lives in `tests/test_specs_releases_unsafe_field.py` and exercises those two trees only. |
| F-10 | THE DETAIL MUST STAY VALUE-FREE, because `escape_detail` is not protection. | Read directly: `attention_contract.escape_detail` applies `_AGENT_ESCAPES` to keep the record one line and does NOT strip C0/C1 controls. So echoing an ANSI-bearing value into a drift detail would emit the raw escape into a terminal even as it reports that doing so is a violation. The sibling's shipped details are already value-free and descriptive. |

## Proposed changes (ordered, validatable)

1. E-01: shorten the three over-length committed `summary:` values (F-03), so the tree is clean before the already-`error`-registered rule can fire on it.
2. E-02: emit `attention.unsafe-field` from `research_index.check_drift` for `summary` and each `topic`/`consumed-by` token, enriched at the emitter, with a value-free detail, and NOT from `validate_frontmatter` because that would drop the document from the index (F-06).
3. E-03: verify the rule reaches `aw research index --check` and `aw check research --all`, and record the pre-existing `include_retired` gate (F-07) rather than changing it.
4. E-04: pin every checker-visible shape plus the 300/301 boundary, and pin the NON-DESTRUCTION property that distinguishes the chosen emitter from the rejected one.
5. E-05: pin both limits explicitly (the NEWLINE vector F-05 including its last-wins override, and the renderer's wider read) and the four non-regression groups.

## Deferred / out of scope (with reason)

- THE NEWLINE INJECTION VECTOR IS NOT CLOSED BY THIS PLAN AND CANNOT BE. F-05 measured why: `parse_frontmatter` splits the value into separate lines before any checker sees it, so the predicate is handed only the safe half and correctly passes, while the smuggled key wins the reader's last-wins race. This is the single most important limit of this plan, the backlog item states it explicitly, and E-05 pins it as a test so the record cannot later be misread as having closed it.
  - Carrier: 7w6zsl
  - Carrier-Evidence: .aw/records/plans/executed/20261001-7w6zsl-01-deftzy-refuse-an-unsafe-descriptive-value-at-every-research-write-p.ipd.md
- THE `include_retired` GATE ON RESEARCH CONTENT CHECKING IS NOT CHANGED, so default `aw check research` still runs no content validator and the new rule surfaces there only under `--all` (F-07). Deliberate: the gate is pre-existing, is byte-identical to the one on the `plans` branch, and removing it would change the exit code and runtime of an unrelated command by turning a names/refs check into a full content check. That is a cross-tree policy decision about what `aw check <type>` means, not collateral of adding one rule.
  - Carrier-Declined: Nothing is owed, because no harm is measured and the rule still gates where it matters: `aw research index --check` calls `check_drift` DIRECTLY and ungated, so the finding is fail-closed on the surface the research tree actually uses and in CI. A carrier would schedule a repository-wide redefinition of `aw check <type>` on the strength of no measured defect.
- THE RENDERERS ARE NOT MADE SAFE, only the condition is made a finding. A value this rule flags is still emitted raw by `aw attention --details` and still written into `INDEX.md` by `aw research index` (F-02); the rule reports it rather than escaping it. The Markdown-escaping half of Section 8.8 ("a field cannot break the table, inject a link/image, or start a new block") is likewise unimplemented, so a pipe in a `summary` can still break a rendered table.
  - Carrier: llnvwj
- `parse_frontmatter`'s LAST-WINS DUPLICATE-KEY SEMANTICS ARE NOT CHANGED. That property is what makes an injected `status:` OVERRIDE the legitimate one (F-05). UPDATED AT REVIEW: the carrier has EXECUTED and delivered the second defence as a REPORT (`research.frontmatter-key-repeated` in `check_drift`) without changing the reader's semantics; E-05 LIMIT ONE now asserts it. Deferred because changing the shared reader affects every research consumer (`research_index`, `research_archive`, `selectors`, `attention`, `releases`).
  - Carrier: jnpl08
- THE `DANGLING_CONSUMED_RULE` EMITTER'S MISSING `enrich_drift` CALL IS NOT FIXED, even though E-02 adds an enriched emitter three lines away from it. Deliberate: it is a pre-existing inconsistency in a rule this plan does not otherwise touch, its severity resolves through the registry at every consumer that enriches, and fixing it would change the serialized severity of an existing finding inside a commit whose subject is a different rule.
  - Carrier-Declined: Nothing is owed, because no incorrect verdict was measured: `drift_exit_code` returns 1 for an unenriched drift (F-04), so the gate behaves identically today and the residue is a metadata field on a finding that already fails. Filing a carrier would schedule cosmetic work on no evidence.
- THE OTHER UNVALIDATED RESEARCH FIELDS ARE NOT WIDENED INTO. `validate_frontmatter` judges `model`/`kind`/`status`/`outcome`/`priority` against vocabularies and `id`/`created`/`order` against shapes, which already bound them; this plan adds no new judgement to any of them. `--date`'s injection and path traversal are a different defect class whose fix is date-format validation, and `A.is_safe_descriptive('../../../../ESCAPED')` returns True so this plan's predicate provably cannot detect the traversal half.
  - Carrier: m5csyi
- WIDENING THE SAME CHECK TO THE REMAINING TREES (`prompts`, `walkthroughs`, `roadmaps`) is out of scope. Each has its own dialect (prompts is an HTML comment), its own field names and its own validator, so a sweep would be several unrelated validator changes in one commit. `prompts` was additionally measured SAFE by `deftzy` F-15 (every newline-bearing prompt flag flattens into one line with no injected field).
  - Carrier-Declined: Nothing is owed for `prompts`, because a fresh measurement found no defect; `walkthroughs` and `roadmaps` have no descriptive front-matter writer or validator to widen, so there is no measured surface to carry.

## Scope check

- Over-scope: none. One new loop over entries already computed in ONE function (`research_index.check_drift`), one import, one new test module, and three one-line records repairs. No new rule id, no `RULE_IDS` change, no `RULE_REGISTRY` change (F-04: already registered), no change to `is_safe_descriptive` or `MAX_DESCRIPTIVE_LEN`, no change to `validate_frontmatter`, no change to `parse_frontmatter`, no change to any renderer or write path, no change to the `include_retired` gate, and no new command.
- Under-scope, stated in full because this plan closes only what a checker can reach: (a) the NEWLINE vector stays open and is closed only at the write path by `deftzy`, which is this plan's defining limit and is pinned as a test (F-05); (b) the renderers still emit a flagged value raw and still write it into `INDEX.md`, and Markdown metacharacter escaping remains unimplemented, carried by `llnvwj`; (c) `parse_frontmatter` keeps its last-wins duplicate-key semantics; `jnpl08` (executed) reports a duplicated key, but an injected NON-duplicate key is still reported by nothing; (d) default `aw check research` still runs no research content validator, so the rule surfaces there only under `--all`, deliberately unchanged (F-07); (e) `--date`'s injection and traversal are untouched, carried by `m5csyi`; (f) `prompts`, `walkthroughs` and `roadmaps` gain no rule; and (g) the `dangling-consumed-by` emitter keeps its missing enrichment.

## Required tests / validation

- `python3 -m pytest tests/test_research_unsafe_field.py` for the new module (run bare; `addopts` already supplies `-q -n auto --dist=worksteal`).
- `python3 -m pytest tests/test_research_index.py tests/test_research_cmd_create.py tests/test_research_archive.py tests/test_attention_contract.py tests/test_specs_releases_unsafe_field.py tests/test_check_engine_spec_criteria.py tests/test_doctor.py` as the targeted regression set: these own the index module being edited, the research creation and archive paths that round-trip through it, the predicate and closed catalog, the sibling trees' coverage of the same rule id, and the doctor's rule-to-remediation table which keys on rule ids. Re-derive the module list at execution; report any name that no longer exists rather than silently dropping it.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression. What must hold is zero failures; a differing total is expected as other work lands and is not by itself a regression.
- EXIT CODES AND RULE SETS ON THE REPOSITORY TREE AFTER E-01, not finding counts. `aw research index --check`, `aw check research --agent`, `aw check research --all --agent` and `aw check all` must add NO `attention.unsafe-field` finding and change no EXIT CODE. The measured baseline is in F-08: `aw check research` exit 0 with 1 pre-existing advisory, `aw check research --all` exit 0 with 136 findings, and `aw research index --check` exit **1** with 135 findings across five pre-existing rules. Re-derive every figure at execution and compare the RULE SETS before and after, since the totals drift with every landed change.
- PRE-FIX FALSIFICATION IS REQUIRED: V-04 must show the new tests FAILING against pre-E-02 code with `check_drift` returning no `attention.unsafe-field` drift. Obtain that run by authoring the test module first, or against a separate `git worktree` at HEAD; do NOT `git stash push -- agent_workflows/research_index.py`, since this checkout is shared and stashing a path can swallow a co-worker's uncommitted edit.
- E-01 MUST BE VALIDATED SEPARATELY AND BEFORE the rule lands (V-01), because its whole purpose is to make the tree clean in advance; validating it only after E-02 would not distinguish "the tree was cleaned" from "the rule does not fire".

## Spec / documentation sync

N/A with reason, and this was checked rather than assumed. This plan makes a checker enforce a contract the governing spec ALREADY states, so no `.spec.md` is amended and no spec path appears in `- Scope-Paths:`. Spec `attention-registry-and-cross-tree-status` Section 8.8 already requires bounded single-line control-char-free descriptive fields, its F10 already classes violations as "stable named `--check` failures", and its A14 already requires the hostile-string fixtures E-04 supplies for this tree. The rule id is already in the closed `RULE_IDS` catalog AND already registered in `RULE_REGISTRY` (F-04), so neither needs amendment. Spec `agents-artifact-organization` Section 5.8 fixes the eleven-field front-matter block and is UNAFFECTED: a new drift rule adds no field, changes no order and alters no grammar.

NOTE on the item's own expectation: the backlog item anticipated that whichever of this plan and `ynhst5` "lands second should reuse rather than re-decide" the registry entry. `ynhst5` landed first, so this plan reuses its entry and registers nothing. The sibling `deftzy` likewise notes that "the checker carrier `cvxbbu` is the artifact that may need a spec amendment, since it adds a rule id"; measured, it does not, because the id was already catalogued and is now also registered.

THREE `.aw/records/research/` PATHS DO APPEAR IN `- Scope-Paths:`, and they are E-01 RECORDS REPAIRS, not contract amendments: the three committed docs whose `summary:` exceeds the bound (F-03). They are declared because the runners reconcile declared versus actual edits and report an undeclared records change at run end even when benign. No edit changes a status, an outcome, a consumer list, or any body text; each shortens one summary line so the artifact obeys the contract it is already subject to.

## Open questions

### OQ-01: Repair the three over-length summaries, or grandfather them with a cutover tier?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM THE CENSUS: repair them, and do it FIRST. The decision turns on population size, which is why F-03 censused rather than estimated: there are exactly THREE violations out of 127 summaries, all on `summary:`, all control-char-free, and all multi-sentence values whose detail is restated in the document body. Against that, a grandfather tier means a per-artifact severity downgrade plus a cutover date, and it leaves a permanent exemption whose only beneficiaries are three records a short edit fixes. The precedent that needed a tier (`check.ipd-uncarried-obligation`) needed it for 106 plans; three is not that. The sibling `ynhst5` faced the same choice at n=2 on the specs tree and chose repair, and the backlog item itself says that precedent "is worth following unless a reason not to appears"; none appeared. Repairing first also lets the rule fire at the `error` severity it is ALREADY REGISTERED at (F-04) with zero findings on a clean checkout, which is both simpler and the stronger validation (V-01). THE COST, stated plainly: one of the three sits under `archive/` and one carries `outcome: adopted`, which the repository treats as settled records. That is acceptable ONLY because the edit is a conformance repair to a summary line that changes no status, no outcome, no consumer list and no body, and E-01 forbids touching anything else.

### OQ-02: Use the catalogued `attention.unsafe-field` id, or a bare research-local id matching the module's four existing rules?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: use `attention.unsafe-field`. The tension is real and worth recording, because this plan knowingly puts a namespaced id beside four bare ones (`stale-state-to-promote`, `dangling-consumed-by`, `adopted-without-consumer`, `unrecognized-model`) in one module. Three reasons decide it. FIRST, the catalog is CLOSED and its own comment states consumers "MUST use these ids; they do NOT free-hand new ones", with `tests/test_attention_contract.py` asserting membership and a minimum size, so a bare `unsafe-field` would be a catalog change this plan does not need. SECOND, the id is ALREADY the designated vocabulary for exactly this violation class and is already emitted for it by `specs.validate_spec` and `releases.validate_release` (F-04), so reusing it means one finding name across three trees and one doctor remediation entry. THIRD, it is already REGISTERED at `error`, so reuse inherits a declared severity rather than a defaulted one. The rejected alternative was a bare `unsafe-field` for intra-module consistency: that buys cosmetic symmetry inside one file and pays with a forked cross-tree vocabulary, which is the exact trade the catalog exists to prevent. NON-BLOCKING because nothing else in the plan depends on the choice.

### OQ-03: Should the rule be emitted from `validate_frontmatter` (the contract) or `check_drift` (the index)?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT: `check_drift`, and this is the plan's load-bearing decision rather than a style preference. The contract placement is the intuitive one (the predicate judges a front-matter value, and `validate_frontmatter` is the front-matter validator) and it is MEASURABLY WRONG here, because `research_index._doc_entry` treats any `validate_frontmatter` error as FATAL and returns no `DocEntry`, so the document is DROPPED from the manifest. Driven (F-06): patching the check into `validate_frontmatter` took a fixture's indexed entries from 1 to 0, and all three real offenders are currently indexed among 126 entries, so that placement would delete three records from `INDEX.json`/`INDEX.md` as the means of reporting that their summaries are too long. `check_drift` runs after `_scan_docs`, reports against entries that remain indexed, and is where all four existing research content rules already live for the same documented reason ("Emitted in check_drift ONLY ... so the regenerate branch of `run_index` is not blocked"). THE RESIDUE OF THIS CHOICE, stated so it is not discovered later: `validate_frontmatter` remains the function a reader would expect to own this check and does not, so E-05(d) asserts it still returns `[]` for an unsafe summary to make the placement deliberate and visible rather than look like an omission. NON-BLOCKING because the mechanism is fully specified in E-02 and demonstrated on a fixture.

### OQ-04: Should the drift detail include the offending value, so a human can see what was wrong?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: no, except for a measured LENGTH, and the reason is the rule's own purpose. The detail lands in the `location<TAB>rule<TAB>detail` agent record and in human output, so echoing an untrusted over-length or ANSI-bearing value would push the exact payload this rule exists to flag into the surface it exists to protect, and for a control-character value it would emit the raw escape into a terminal even as it reports that doing so is a violation. Escaping is not sufficient protection: `A.escape_detail` escapes tab, newline and backslash to keep the record one line and deliberately does NOT strip C0/C1 controls (F-10). A measured LENGTH is exempt because a number is not attacker-controlled text and is the one fact that makes a length finding actionable without opening the file. The sibling's shipped details are already value-free and descriptive, so E-02 follows that wording. The residue is that a user must open the file to see the offending value, which is acceptable because the finding names the file and the field.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste a `git diff` of the three research docs showing ONLY the `summary:` line changed in each, and paste the before and after character counts for all three (before: 395, 351, 320; after: each at most 300, with the actual numbers). Paste the full before and after text of each value so a reviewer can judge that meaning was preserved rather than truncated. Then paste the output of a census over the WHOLE research tree showing ZERO `summary:`/`topic`/`consumed-by` values failing `A.is_safe_descriptive`, where it previously reported 3. THIS MUST BE RUN BEFORE E-02 EXISTS: state explicitly that the rule was not yet in the tree when this evidence was captured, since E-01's whole purpose is to precede it. Also confirm from the diff that no `status:`, `outcome:` or `consumed-by:` line and no body text was touched in any of the three, and that the `archive/`-resident file was not moved.
  - Observed evidence:
    `git diff` of the three research documents:
    ```diff
    diff --git a/.aw/records/research/archive/202609/20260905-awmetastore-06-g5f3zq-aw-artifact-metadata-storage-research-report.gemini31prodeepthink.research-report.md b/.aw/records/research/archive/202609/20260905-awmetastore-06-g5f3zq-aw-artifact-metadata-storage-research-report.gemini31prodeepthink.research-report.md
    index 60367a2ff..cce571d35 100644
    --- a/.aw/records/research/archive/202609/20260905-awmetastore-06-g5f3zq-aw-artifact-metadata-storage-research-report.gemini31prodeepthink.research-report.md
    +++ b/.aw/records/research/archive/202609/20260905-awmetastore-06-g5f3zq-aw-artifact-metadata-storage-research-report.gemini31prodeepthink.research-report.md
    @@ -8,7 +8,7 @@ model: gemini31prodeepthink
     kind: research-report
     status: archive
     outcome: rejected
    -summary: Gemini 3.1 Pro Deep Think: a fifth answer to prompt 27rjro, DELIBERATELY EXCLUDED from reconciliation 6mye7n on the maintainer instruction because its own author note records that network restrictions prevented it reading the repository, so it reasoned from the prompt prose alone; adopted 2026-09-20 for provenance only
    +summary: Gemini 3.1 Pro Deep Think: fifth answer to prompt 27rjro, excluded from reconciliation 6mye7n by maintainer instruction because network restrictions prevented repo access (reasoned from prompt prose alone); adopted 2026-09-20 for provenance only
     consumed-by: []
     ---

    diff --git a/.aw/records/research/reference/202609/20260905-awmetastore-05-6mye7n-where-aw-metadata-should-live.reconciliation.reconciliation-report.md b/.aw/records/research/reference/202609/20260905-awmetastore-05-6mye7n-where-aw-metadata-should-live.reconciliation.reconciliation-report.md
    index 46b666761..4ce90cc6f 100644
    --- a/.aw/records/research/reference/202609/20260905-awmetastore-05-6mye7n-where-aw-metadata-should-live.reconciliation.reconciliation-report.md
    +++ b/.aw/records/research/reference/202609/20260905-awmetastore-05-6mye7n-where-aw-metadata-should-live.reconciliation.reconciliation-report.md
    @@ -8,7 +8,7 @@ model: reconciliation
     kind: reconciliation-report
     status: reference
     outcome: adopted
    -summary: Consolidated finding across GPT-5.6 Sol High, Sonnet 5 High, Gemini 3.1 Pro High and Gemini 3.8 Flash High: all four converge on inline front matter plus git-tracked per-artifact JSONL history keyed by id6, ordered by an explicit per-artifact seq rather than by date; the live-verified disagreements are the inline residue, IPD-S405, and write locking
    +summary: Consolidated finding across GPT-5.6, Sonnet 5, Gemini 3.1 Pro and Gemini 3.8 Flash: all four converge on inline front matter plus git-tracked per-artifact JSONL history keyed by id6, ordered by explicit seq rather than date; live disagreements are inline residue, IPD-S405, and write locking
     consumed-by: [ms06pi, tk1gqo]
     ---

    diff --git a/.aw/records/research/reference/202609/20260905-hostskill-04-6asl6q-host-skill-runtime-discovery-and-authoring.reconciliation.reconciliation-report.md b/.aw/records/research/reference/202609/20260905-hostskill-04-6asl6q-host-skill-runtime-discovery-and-authoring.reconciliation.reconciliation-report.md
    index 769d77679..04af8e81b 100644
    --- a/.aw/records/research/reference/202609/20260905-hostskill-04-6asl6q-host-skill-runtime-discovery-and-authoring.reconciliation.reconciliation-report.md
    +++ b/.aw/records/research/reference/202609/20260905-hostskill-04-6asl6q-host-skill-runtime-discovery-and-authoring.reconciliation.reconciliation-report.md
    @@ -8,7 +8,7 @@ model: reconciliation
     kind: reconciliation-report
     status: reference
     outcome: none-yet
    -summary: Consolidated finding across GPT-5.6 Sol High, Sonnet 5 High and Gemini 3.1 Pro Deep Think: .agents/skills is a real shipped discovery path in at least seven hosts and is NOT aspirational, the per-package verify_digest.py is called by nothing and should go, and the Antigravity directory name is UNRESOLVED (plural vs singular) pending an empirical test on opencode, codex, agy, claude and hermes
    +summary: Consolidated finding across GPT-5.6, Sonnet 5, Gemini 3.1 Pro: .agents/skills is a shipped discovery path in >=7 hosts (not aspirational); per-package verify_digest.py is uncalled and should go; the Antigravity directory name is unresolved (plural vs singular) pending empirical host tests
     consumed-by: []
     ---
    ```

    Character counts and full text before and after:
    1. `6asl6q`:
       Before: 395 characters
       `Consolidated finding across GPT-5.6 Sol High, Sonnet 5 High and Gemini 3.1 Pro Deep Think: .agents/skills is a real shipped discovery path in at least seven hosts and is NOT aspirational, the per-package verify_digest.py is called by nothing and should go, and the Antigravity directory name is UNRESOLVED (plural vs singular) pending an empirical test on opencode, codex, agy, claude and hermes`
       After: 289 characters (<= 300)
       `Consolidated finding across GPT-5.6, Sonnet 5, Gemini 3.1 Pro: .agents/skills is a shipped discovery path in >=7 hosts (not aspirational); per-package verify_digest.py is uncalled and should go; the Antigravity directory name is unresolved (plural vs singular) pending empirical host tests`

    2. `6mye7n`:
       Before: 351 characters
       `Consolidated finding across GPT-5.6 Sol High, Sonnet 5 High, Gemini 3.1 Pro High and Gemini 3.8 Flash High: all four converge on inline front matter plus git-tracked per-artifact JSONL history keyed by id6, ordered by an explicit per-artifact seq rather than by date; the live-verified disagreements are the inline residue, IPD-S405, and write locking`
       After: 291 characters (<= 300)
       `Consolidated finding across GPT-5.6, Sonnet 5, Gemini 3.1 Pro and Gemini 3.8 Flash: all four converge on inline front matter plus git-tracked per-artifact JSONL history keyed by id6, ordered by explicit seq rather than date; live disagreements are inline residue, IPD-S405, and write locking`

    3. `g5f3zq`:
       Before: 320 characters
       `Gemini 3.1 Pro Deep Think: a fifth answer to prompt 27rjro, DELIBERATELY EXCLUDED from reconciliation 6mye7n on the maintainer instruction because its own author note records that network restrictions prevented it reading the repository, so it reasoned from the prompt prose alone; adopted 2026-09-20 for provenance only`
       After: 245 characters (<= 300)
       `Gemini 3.1 Pro Deep Think: fifth answer to prompt 27rjro, excluded from reconciliation 6mye7n by maintainer instruction because network restrictions prevented repo access (reasoned from prompt prose alone); adopted 2026-09-20 for provenance only`

    Census over whole research tree (run BEFORE E-02 existed; the rule was not yet in the tree when this was captured):
    ```
    Total docs censused: 129
    Unsafe count: 0
    ```
    Confirmed from the diff: only the `summary:` line was modified in each file; no `status:`, `outcome:`, `consumed-by:` or document body line was touched in any of the three, and the `archive/`-resident file was not moved.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a Python session calling `research_index.check_drift` on fixture repositories and showing the returned drift for each: a 301-character `summary` yielding exactly one `attention.unsafe-field`; a `summary` containing BEL yielding the same; one containing an ANSI ESC yielding the same; one containing a C1 control yielding the same; a 300-character `summary` yielding none (the boundary); an unsafe `topic` token yielding one naming that field; an unsafe `consumed-by` token yielding one naming that field. For each drift paste `severity`, showing `error` from the emitter's own `enrich_drift` call rather than from a later consumer.
  THE NON-DESTRUCTION EVIDENCE IS MANDATORY AND ITS ABSENCE FAILS THIS ITEM, because it is the property that distinguishes the chosen emitter from the rejected one (F-06, OQ-03): for every unsafe case above, paste the entry list from the same scan showing the document is STILL INDEXED and that NO `frontmatter-invalid` drift was emitted for it. Also paste `R.validate_frontmatter(fm)` on the same unsafe fixture returning `[]`, proving the contract function was not changed. Finally paste each emitted DETAIL string showing it contains neither the offending value nor a raw control byte (a measured length is permitted per OQ-04), and paste the source showing `_ce.enrich_drift` is applied as the neighbouring rules do.
  - Observed evidence:
    Interactive Python session calling `research_index.check_drift` on fixture repositories:
    ```
    === Case: 301-char summary ===
    Indexed entries count: 1 (id6=['tst001'])
    Scan drift rules: []
    validate_frontmatter: []
    Drift count (attention.unsafe-field): 1
      rule: attention.unsafe-field
      severity: error
      detail: Summary is over-length or has control chars/newlines
      detail has raw control chars: False

    === Case: BEL summary ===
    Indexed entries count: 1 (id6=['tst001'])
    Scan drift rules: []
    validate_frontmatter: []
    Drift count (attention.unsafe-field): 1
      rule: attention.unsafe-field
      severity: error
      detail: Summary is over-length or has control chars/newlines
      detail has raw control chars: False

    === Case: ANSI ESC summary ===
    Indexed entries count: 1 (id6=['tst001'])
    Scan drift rules: []
    validate_frontmatter: []
    Drift count (attention.unsafe-field): 1
      rule: attention.unsafe-field
      severity: error
      detail: Summary is over-length or has control chars/newlines
      detail has raw control chars: False

    === Case: C1 control summary ===
    Indexed entries count: 1 (id6=['tst001'])
    Scan drift rules: []
    validate_frontmatter: []
    Drift count (attention.unsafe-field): 1
      rule: attention.unsafe-field
      severity: error
      detail: Summary is over-length or has control chars/newlines
      detail has raw control chars: False

    === Case: 300-char summary (boundary) ===
    Indexed entries count: 1 (id6=['tst001'])
    Scan drift rules: []
    validate_frontmatter: []
    Drift count (attention.unsafe-field): 0

    === Case: unsafe topic token ===
    Indexed entries count: 1 (id6=['tst001'])
    Scan drift rules: []
    validate_frontmatter: []
    Drift count (attention.unsafe-field): 1
      rule: attention.unsafe-field
      severity: error
      detail: Topic is over-length or has control chars/newlines
      detail has raw control chars: False

    === Case: unsafe consumed-by token ===
    Indexed entries count: 1 (id6=['tst001'])
    Scan drift rules: []
    validate_frontmatter: []
    Drift count (attention.unsafe-field): 1
      rule: attention.unsafe-field
      severity: error
      detail: Consumed-by is over-length or has control chars/newlines
      detail has raw control chars: False
    ```

    Non-destruction evidence: in every unsafe case above, `Indexed entries count: 1 (id6=['tst001'])`, `Scan drift rules: []` (no `frontmatter-invalid`), and `validate_frontmatter(fm)` returned `[]`.
    Detail strings: value-free, containing neither the offending value nor raw control characters.
    Emitter source showing `_ce.enrich_drift`:
    ```python
    for e in entries:
        if not A.is_safe_descriptive(e.summary):
            drift.append(
                _ce.enrich_drift(
                    Drift(
                        e.path,
                        "attention.unsafe-field",
                        A.escape_detail(
                            "Summary is over-length or has control chars/newlines"
                        ),
                    )
                )
            )
        for t in e.topic:
            if not A.is_safe_descriptive(str(t)):
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            "attention.unsafe-field",
                            A.escape_detail(
                                "Topic is over-length or has control chars/newlines"
                            ),
                        )
                    )
                )
        for c in e.consumed_by:
            if not A.is_safe_descriptive(str(c)):
                drift.append(
                    _ce.enrich_drift(
                        Drift(
                            e.path,
                            "attention.unsafe-field",
                            A.escape_detail(
                                "Consumed-by is over-length or has control chars/newlines"
                            ),
                        )
                    )
                )
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste, on an unsafe FIXTURE repo, `aw research index --check` exiting 1 with the `attention.unsafe-field` finding, and `aw check research --all --agent` reporting it. Then paste `aw check research --agent` (DEFAULT, no `--all`) on that same unsafe fixture showing the rule does NOT appear, together with a `check_content(repo, "research", include_retired=False)` versus `include_retired=True` comparison, so the pre-existing gate (F-07) is documented as measured behavior rather than asserted. State explicitly that the gate was NOT changed by this plan and that the `plans` branch carries the identical condition.
  Then paste, on the REPAIRED REPOSITORY tree, `aw research index --check`, `aw check research --agent`, `aw check research --all --agent` and `aw check all` with their EXIT CODES and their RULE SETS. THE BAR IS AN EXIT CODE AND A RULE SET, NOT A COUNT, compared against a PRE-CHANGE rule set you capture at the executing HEAD before E-02 (PR-003). For context only, the authoring F-08 baseline was `aw check research` exit 0 with one pre-existing `check.collisions-not-checked` advisory, `aw check research --all` exit 0 with 136 findings, and `aw research index --check` exit 1 with 135 findings across `dangling-citation` (78), `adopted-without-consumer` (35), `stale-state-to-promote` (19), `check.stale-index-missing` (2) and `frontmatter-invalid` (1). Re-derive every figure at execution and show the rule set is UNCHANGED and contains no `attention.unsafe-field`; do not report a differing total as a regression.
  - Observed evidence:
    On an unsafe fixture repository:
    `aw research index --check --dir tmp/v03_fixture` exited 1:
    ```
    20261002-test-01-uns001-test.notes.md: attention.unsafe-field: Summary is over-length or has control chars/newlines
    ```
    `aw check research --all --agent --dir tmp/v03_fixture` exited 1:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"research","findings":2,"evidence":["inventory","rules"],"diagnostics":[{"location":"20261002-test-01-uns001-test.notes.md","rule":"attention.unsafe-field"},{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"inspect 20261002-test-01-uns001-test.notes.md frontmatter and schema conformity."}
    ```
    `aw check research --agent --dir tmp/v03_fixture` (default, no `--all`) exited 0:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"research","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw research find"}
    ```
    `check_content` comparison proving the `include_retired` gate:
    ```
    check_content include_retired=False drift count: 0
    check_content include_retired=True drift count: 1
    check_content include_retired=True rules: ['attention.unsafe-field']
    ```
    The `include_retired` gate was NOT changed by this plan and the `plans` branch carries the identical condition.

    On the REPAIRED REPOSITORY tree:
    `aw research index --check`: exit code 1; rule set unchanged:
    ```
    Total drifts: 225
      adopted-without-consumer: 35
      check.stale-index-missing: 2
      dangling-citation: 168
      frontmatter-invalid: 1
      stale-state-to-promote: 19
    ```
    `aw check research --agent`: exit code 0; rule set `['check.collisions-not-checked']`.
    `aw check research --all --agent`: exit code 1; findings: 226; rule set: `['adopted-without-consumer', 'check.collisions-not-checked', 'check.stale-index-missing', 'dangling-citation', 'frontmatter-invalid', 'stale-state-to-promote']`; `attention.unsafe-field` present: False.
    `aw check all`: exit code 1 (pre-existing repo status); research domain findings contain 0 `attention.unsafe-field`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the full `python3 -m pytest tests/test_research_unsafe_field.py` output including the `N passed` line. Then paste the PRE-FIX run showing the over-length and control-character cases FAILING, with the assertion text showing `check_drift` returned no `attention.unsafe-field` drift. State how the pre-fix run was obtained (test module authored first, or a separate `git worktree` at HEAD) and confirm `git stash` was not used on a shared checkout. Paste the boundary assertions proving 300 accepted and 301 refused, and paste the registry assertion reading `check_engine.rule_spec("attention.unsafe-field")` and comparing `RuleSpec` fields rather than grepping module text.
  - Observed evidence:
    Pre-fix test run (obtained by authoring `tests/test_research_unsafe_field.py` first against unedited `research_index.py`, without using `git stash` on this shared checkout):
    ```
    FAILED tests/test_research_unsafe_field.py::TestResearchUnsafeField::test_summary_boundary_300_and_301
    FAILED tests/test_research_unsafe_field.py::TestResearchUnsafeField::test_summary_unsafe_shapes
    FAILED tests/test_research_unsafe_field.py::TestResearchUnsafeField::test_topic_token_unsafe_shape
    FAILED tests/test_research_unsafe_field.py::TestResearchUnsafeField::test_consumed_by_token_unsafe_shape
    4 failed, 7 passed in 16.47s
    ```
    Failure details from pre-fix run:
    ```
    AssertionError: 0 != 1 : 301-char summary must yield attention.unsafe-field
    AssertionError: 0 != 1 : Summary over-length should yield exactly one attention.unsafe-field, got []
    AssertionError: 0 != 1 (topic token)
    AssertionError: 0 != 1 (consumed-by token)
    ```

    Post-fix test run:
    ```
    python3 -m pytest tests/test_research_unsafe_field.py
    ...........                                                              [100%]
    11 passed in 8.51s
    ```

    Boundary assertions from test:
    ```python
    # 300 characters is conforming
    self._write_doc(id6="bnd300", summary="x" * 300)
    self._regen()
    drifts_300 = I.check_drift(self.root, self.rroot)
    unsafe_300 = [d for d in drifts_300 if d.rule == "attention.unsafe-field"]
    self.assertEqual(unsafe_300, [], "300-char summary must not yield attention.unsafe-field")

    # 301 characters is refused
    shutil.rmtree(self.rroot, ignore_errors=True)
    self.rroot.mkdir(parents=True, exist_ok=True)
    self._write_doc(id6="bnd301", summary="x" * 301)
    self._regen()
    drifts_301 = I.check_drift(self.root, self.rroot)
    unsafe_301 = [d for d in drifts_301 if d.rule == "attention.unsafe-field"]
    self.assertEqual(len(unsafe_301), 1, "301-char summary must yield attention.unsafe-field")
    self.assertEqual(unsafe_301[0].severity, "error")
    ```

    Registry assertion:
    ```python
    spec = check_engine.rule_spec("attention.unsafe-field")
    self.assertEqual(spec.severity, "error")
    self.assertEqual(spec.assurance, check_engine.ASSURANCE_REPOSITORY)
    self.assertEqual(spec.determinism, check_engine.DET_DETERMINISTIC)
    self.assertEqual(spec.invariant, "")
    self.assertIn("attention.unsafe-field", check_engine.RULE_REGISTRY)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the two LIMIT tests passing after the fix, and the parts of them that do not concern `attention.unsafe-field` passing before it too, and STATE WHY: the NEWLINE case because `attention.unsafe-field` cannot see the injected half while `jnpl08`'s `research.frontmatter-key-repeated` catches only the duplicated `status` and nothing catches `blocks-release`; the no-sanitize case because this plan reports rather than repairs. For the newline case paste the returned drift list showing those three facts, and the measured last-wins override (the record resolving to `status: reference` and `blocks-release: next` while `summary` reads `legit` and `validate_frontmatter` returns `[]`). For the no-sanitize case paste the fixture's bytes (or a hash) before and after the `check_drift` run, identical, and confirm the test makes NO assertion that `aw attention` emits raw bytes (PR-002).
  Then paste the four non-regression groups: (a) zero `attention.unsafe-field` findings across the live repaired research tree, read from the repository rather than from hard-coded lengths; (b) the four existing research drift rules still firing on their own fixtures; (c) a doc with empty `topic: []`/`consumed-by: []` yielding nothing and not faulting; (d) `validate_frontmatter` returning `[]` for an unsafe summary. Finally paste the bare full-suite run with its `N passed` line.
  - Observed evidence:
    Two limit tests passing in `tests/test_research_unsafe_field.py`:
    - LIMIT ONE: `test_limit_one_newline_injection_and_last_wins` passed both before and after the fix because `attention.unsafe-field` cannot see the injected newline, while `research.frontmatter-key-repeated` (from executed `jnpl08`) catches `status` and nothing catches `blocks-release`.
      Measured:
      `fm.get("summary") == "legit"`
      `A.is_safe_descriptive(fm.get("summary")) is True`
      `R.validate_frontmatter(fm) == []`
      `fm.get("status") == "reference"` (last-wins override)
      `fm.get("blocks-release") == "next"`
      `check_drift` returns: `[Drift(location='20261002-test-01-nl0001-test-doc.notes.md', rule='research.frontmatter-key-repeated', detail="frontmatter key 'status' appears 2 times")]`
      No `attention.unsafe-field` drift; no drift naming `blocks-release`.
    - LIMIT TWO: `test_limit_two_no_sanitization_bytes_unchanged` passed:
      `bytes_before == bytes_after` holds identically on disk, and index entry `summary` carries exact raw text. No assertion is made on `aw attention` emitting raw bytes.

    Four non-regression groups:
    (a) `test_non_regression_live_research_tree_clean`: 0 `attention.unsafe-field` findings across live research tree.
    (b) `test_non_regression_existing_four_drift_rules`: `adopted-without-consumer`, `dangling-consumed-by`, and `unrecognized-model` all fire on their own fixtures.
    (c) `test_non_regression_empty_lists_no_fault`: doc with `topic: []` and `consumed_by: []` yields no findings and does not fault.
    (d) `test_non_regression_validate_frontmatter_unchanged`: `validate_frontmatter` with 301-character summary returns `[]`.

    Bare full-suite run:
    ```
    python3 -m pytest
    6589 passed, 2 skipped, 3 warnings in 525.31s (0:08:45)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. It carries no `- Readiness:` field, because that is `/plan-review`'s output and an author-written value would forge a review that did not happen, and no `- Approval:` field, because that is a human's attestation.

Execute only the checklist above; commit through `aw commit xnogdl -- agent_workflows/research_index.py tests/test_research_unsafe_field.py .aw/records/research/reference/202609/20260905-hostskill-04-6asl6q-host-skill-runtime-discovery-and-authoring.reconciliation.reconciliation-report.md .aw/records/research/reference/202609/20260905-awmetastore-05-6mye7n-where-aw-metadata-should-live.reconciliation.reconciliation-report.md .aw/records/research/archive/202609/20260905-awmetastore-06-g5f3zq-aw-artifact-metadata-storage-research-report.gemini31prodeepthink.research-report.md` and never `git add -A`, verifying the staged set before each commit because this checkout is shared. Do not push and do not tag.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every claim of a pass, never a summary you did not run. This plan's V-items require a PRE-FIX FAILING run (V-04) and a BEFORE-THE-RULE census (V-01), and a fabricated one would assert the very coverage it is meant to prove. Run the suite BARE (`python3 -m pytest`); the configured `addopts` already supplies `-q -n auto --dist=worksteal`, and a second `-q` would suppress the `N passed` line this gate requires.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the five paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, MAKE the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Do not stop and wait over a scope question. Two conditions DO warrant stopping and reporting: a concurrent edit to `research_index.py` that cannot be safely combined with this change, and the E-03 verification exposing that the rule reaches none of its intended consumers, which would mean the emitter placement needs re-deciding rather than patching.

All open questions are resolved and none is blocking (OQ-01 through OQ-04).

THREE DECLARED RECORDS EDITS: this plan's `- Scope-Paths:` names three `.aw/records/research/` files, which the runners reconcile at run end. They are E-01 conformance repairs to a single `summary:` line each, not content or lifecycle changes; see the Spec / documentation sync section for why that is legitimate and what it deliberately does not touch. No `.spec.md` is declared, because no spec is amended (F-04).

INDEPENDENCE: this plan declares `- Item-Dependencies: none` and is the only member of Set `cvxbbu`. It edits `research_index.check_drift`; the sibling carrier `deftzy` (Set `7w6zsl`) edits `research_cmd.py` planner functions, a different module, so the two can run in either order or in parallel lanes. ORDER RELATIVE TO `deftzy` IS WORTH NOTING even though it is not a dependency: `deftzy` HAS LANDED (executed; confirmed at review), so the unsafe fixtures this plan's tests need can no longer be produced through `aw research new`, so E-04 and E-05 must build them by writing the front-matter bytes directly or by calling `research_cmd.build_frontmatter`, which is what those items already specify.
