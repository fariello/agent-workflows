# IPD: Make a maintainer ruling's existing typed reference actually resolve, instead of adding a new record type nothing would enforce

- Date: 2026-10-01
- Kind: child
- Concern: Backlog `0szu1p` asks whether a maintainer ruling that names specific artifacts should get its own typed enforceable record, and offers three options: (a) a new `decisions/` records tree with a lifecycle, checker, CLI surface and `aw attention` mapping; (b) a convention that a ruling MUST be written onto the governed artifact's fields immediately; (c) a backlog item per decided artifact. The item calls (a) "the complete answer and also the most work" and states none is obviously right. ANSWERING IT FROM CODE EVIDENCE PRODUCES A FOURTH ANSWER THE ITEM DID NOT CONSIDER, and it is cheaper than all three: a typed, machine-readable reference to a ruling ALREADY EXISTS and is already wired end to end, but it is BROKEN IN TWO MEASURED WAYS, so it has never been usable for the job. `attention_contract.GATE_KINDS` has included `decision` since the attention registry shipped; `validate_gate_ref` dispatches it to `_DECISION_ID_RE`; `backlog.validate_item` and `specs.check` both enforce it; and `set_records.promote_question_to_backlog` already constructs `Gate-Kind: decision` items. The two defects: (1) `_DECISION_ID_RE = re.compile(r"^D\d+$")` REJECTS three of the 156 decision headings that actually exist in `DECISIONS.md`, because the log disambiguates its own duplicate numbers additively and carries `D22b`, `D23b` and `D24b` (driven: `validate_gate_ref('decision', 'D22b')` returns False, so a gate citing one of those three rulings cannot be written at all); and (2) a `decision` ref is SHAPE-CHECKED AND NEVER RESOLVED, so `validate_gate_ref('decision', 'D99999')` returns True while the log stops at D156 (driven), which means a gate can cite a ruling that does not exist and nothing detects it. Fixing those two makes an EXISTING typed mechanism correct, where options (a) and (c) build a second one.
- Scope: IN: (1) widen `_DECISION_ID_RE` to `^D\d+[a-z]*$` so the additive-suffix headings the log actually uses are citable, verified against all 156 headings rather than against the author's idea of the grammar; (2) add ONE `aw check` sweep rule, `check.decision-ref-dangling`, that RESOLVES a `Gate-Kind: decision` ref against the headings parsed from `DECISIONS.md` and reports a ref naming no heading, registered `warning` and riding the existing full-sweep seam beside `check_review_dangling`; (3) add the heading parser the rule needs as a named function with the SOUNDNESS PROPERTY MEASURED, not assumed, because an unsound token extractor is exactly what sank the sibling plan `nllamb` (its F-14 measured that six lowercase alphanumerics also matches English words); (4) behavior-only tests for both halves, including the three suffixed headings as the regression case and a falsifiable negative; (5) record the ANSWER to `0szu1p` where the next author will read it, in `.aw/records/backlog/README.md` beside the existing gate documentation, so the decision does not decay into prose exactly as the 2026-09-12 ruling did; (6) a CHANGELOG entry.
  OUT: creating a `decisions/` records tree, a `decision` artifact type, a `.decision.md` facet, a `TreePolicy`, a `CLASS_MAPS` fragment or any lifecycle for rulings (option (a) is REFUSED, with the reason recorded in E-05 and argued in Findings F-07); mandating that a ruling be written onto governed artifacts' fields (option (b) is already the shipped convention for Priority/Work-Kind and needs no plan here, see F-08); filing a backlog item per decided artifact (option (c) is REFUSED as the general mechanism, see F-09); resolving the OTHER gate kinds whose refs also do not resolve (`artifact` and `todo`), which is a strictly larger contract question deferred to backlog `2rnswc`; RETROFITTING any gate onto the 15 plans the 2026-09-12 ruling named, which are terminal and unwritable and whose loss plan `nllamb` E-05 already records; changing `promote_question_to_backlog` (it is currently called from nowhere in the package, measured, so changing it would be unverifiable churn); and anything in plan `nllamb`'s scope, which this plan does not supersede.
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/check_engine.py, tests/test_decision_ref_resolution.py, tests/test_attention_contract.py, .aw/records/backlog/README.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: 0szu1p
- Set: rulingcarrier
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: jge900

## Workflow history

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `0szu1p`. Answers the item's model question with a fourth option measured from code (repair the shipped `Gate-Kind: decision` mechanism) rather than choosing among its (a)/(b)/(c). Two defects driven and recorded (F-01, F-02); filed backlog `2rnswc` as the durable carrier for the general gate-resolution question this plan deliberately leaves out.

## Goal

Make the one typed, machine-readable way to cite a maintainer ruling actually work, so a ruling can be referenced by a gate that both VALIDATES and RESOLVES, and record that answer to backlog `0szu1p` so the records model does not grow a second mechanism for a job the first one can do once two small defects are fixed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the existing decision reference correct

- [ ] E-01 Widen the decision-ref grammar in `attention_contract` so the additive-suffix headings `DECISIONS.md` actually uses are citable. Change `_DECISION_ID_RE` from `^D\d+$` to `^D\d+[a-z]*$`. Keep it anchored at both ends: an unanchored or `.*`-suffixed pattern would accept `D12-garbage` and reintroduce the shape hole this plan is narrowing. Do NOT touch `validate_gate_ref`'s dispatch, the other five per-kind validators, `GATE_KINDS`, or any other symbol in the module; the module is deliberately data-plus-validators with no file IO (measured: no `open`, `read_text`, `Path` or `rglob` appears in it) and this item must not change that.
  - Depends on: none
  - Expected outcome: `validate_gate_ref('decision', 'D22b')` returns True where it returned False before; all three of `D22b`, `D23b`, `D24b` are accepted; the two cases pinned by the existing `tests/test_attention_contract.py` gate-validator test (`D124` True, `not-a-decision` False) are unchanged; `d12`, `D`, `D1x2` and the empty string are still rejected.
  - Execution state: pending

- [ ] E-02 Add a NAMED heading parser for `DECISIONS.md` to `check_engine`, returning the set of decision ids the log actually defines. Parse ONLY headings, with an anchored multiline pattern on the `### D<n>[suffix]. ` form (the shape every one of the 156 headings uses); do NOT scan the body for bare `D<n>` tokens. THE SOUNDNESS REASON IS MEASURED AND IS THE POINT OF THIS ITEM: a bare `\bD\d+[a-z]*\b` extractor over the repository yields 4315 hits of which 145 resolve to no heading, and the false ones are overwhelmingly OTHER NAMESPACES that merely share the shape (`PR-D02` review finding ids, `IPD-D701` a retired lint code, `D401` a flake8 `noqa` code, `RR-...-D006` a release-review decision id). This is the same class of unsoundness plan `nllamb` F-14 measured in its own token extractor and is why that plan's rule half is blocked; do not repeat it. Return a set, read the file once, and fail OPEN (empty set) on a read error so a missing or unreadable log cannot make the sweep raise.
  - Depends on: none
  - Expected outcome: the parser returns exactly 156 ids from the live `DECISIONS.md`, including `D22b`/`D23b`/`D24b`; it returns an empty set rather than raising when the file is absent; and it does NOT return `D701`, `D401` or `D02`, none of which is a heading in the log.
  - Execution state: pending

- [ ] E-03 Register `check.decision-ref-dangling` in `check_engine.RULE_REGISTRY` and add the sweep that emits it. SEVERITY IS `warning`, and the choice is argued from the two shipped precedents rather than picked: `check.review-dangling` is the exact structural twin (an unresolvable cross-tree reference, swept whole-tree, registered `warning`) and its docstring states what `warning` buys, namely that NO LIFECYCLE GATE consumes the finding; `info` would be wrong because `artifact_core.drift_exit_code` exempts only `info`, so the rule could never fail anything, and the corpus is already clean (F-03) so there is no grandfathered population needing an advisory rollout tier. The sweep must: enumerate gate-carrying records through the EXISTING parsers (`backlog.parse_item` for backlog items and `specs`' gate reader for specs, which are the only two trees whose checkers enforce gates); consider only records whose `Gate-Kind` is exactly `decision`; skip a record whose ref is absent or fails `validate_gate_ref` (that is `backlog.gate-ref-invalid` / `attention.gate-malformed` already, and double-reporting one authoring mistake under two rule ids is what `check_review_dangling` explicitly refuses to do); and report a ref that is well-formed but names no heading. Wire it into the `types == ["all"]` full-sweep branch inside its own `try`/`except`, matching the fail-isolated pattern its neighbours use, so a defect here degrades the sweep rather than breaking `aw check`.
  - Depends on: E-02
  - Expected outcome: `aw check all` runs the rule; a backlog item or spec carrying `Gate-Kind: decision` with a ref naming no heading produces exactly one `check.decision-ref-dangling` finding at `warning`; a ref naming a real heading produces none; a malformed ref produces none from THIS rule; and the live corpus is unchanged (F-03).
  - Execution state: pending

### Task group 2: prove it, and record the answer

- [ ] E-04 Write `tests/test_decision_ref_resolution.py` covering both halves by BEHAVIOR, never by reading production source. Required cases: (1) each of `D22b`, `D23b`, `D24b` is accepted by `validate_gate_ref`, the regression this plan exists to fix; (2) every heading id parsed from the live `DECISIONS.md` is accepted by `validate_gate_ref`, a property test that cannot pass vacuously because it also asserts the parsed count is greater than 100; (3) the four existing rejections (`d12`, `D`, `D1x2`, empty) still fail; (4) the parser returns an empty set for an absent file; (5) the parser does NOT return a body-only token, driven on a temporary log containing `PR-D02` and `IPD-D701` in prose and exactly one real heading; (6) the sweep reports a dangling decision ref, built on a THROWAWAY tree rather than the live records, because other sessions modify the live backlog while tests run; (7) the sweep reports nothing for a resolvable ref; (8) the sweep reports nothing for a malformed ref, pinning the no-double-report boundary; (9) a falsifiable negative asserting the rule id and severity the finding actually carries. Also extend the existing gate-validator test in `tests/test_attention_contract.py` with the suffixed case, since that is where the decision-ref contract is already pinned and a reader will look there first.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: all nine cases plus the extended existing test pass; each asserts on returned values, exit codes or emitted findings, and none inspects source text, counts callers or asserts a docstring is unchanged.
  - Execution state: pending

- [ ] E-05 Record the ANSWER to backlog `0szu1p` in `.aw/records/backlog/README.md`, beside the existing gate documentation, in one short section. It must state: that a maintainer ruling is cited by `Gate-Kind: decision` with a `D<n>` ref into `DECISIONS.md`; that the ref is now both shape-validated and resolved; and that options (a) a `decisions/` records tree and (c) a backlog item per decided artifact were CONSIDERED AND REFUSED, with the reason, so the next author does not re-derive the question. The refusal reason is the measured one from F-07, not a preference: a new tree would have to be registered in `layout`, `lifecycle_dirs`, `artifact_naming`'s facet enum, `check_engine.SUPPORTED`, `attention_contract.TREE_POLICY` and `CLASS_MAPS`, `TYPE_BACKENDS`, `status_set`, `record_placement` and `artifact_core.SCAN_ROOTS`, and the backlog type alone carries roughly 7400 lines of test code, so (a) is a large permanent surface for a reference the existing gate already expresses in one line. THIS ITEM IS WHY THE PLAN EXISTS: the 2026-09-12 ruling decayed precisely because it lived only in plan prose, and a decision recorded only in this plan's own prose would decay the same way once the plan reaches `executed/`.
  - Depends on: E-01, E-03
  - Expected outcome: `.aw/records/backlog/README.md` carries the answer in a form a future author reads before re-opening the question; the three options from `0szu1p` are each named with their disposition; and no other section of the README is altered.
  - Execution state: pending

- [ ] E-06 Add a CHANGELOG entry recording the widened decision-ref grammar and the new rule, in the file's existing style, written as user-facing prose with no em or en dashes.
  - Depends on: E-01, E-03
  - Expected outcome: one entry naming both the grammar fix and `check.decision-ref-dangling`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A RULE'S SEVERITY IS A RECORDED DECISION WITH TWO SHIPPED PRECEDENTS, not a style choice. `check_engine.RULE_REGISTRY` maps each rule id to a `RuleSpec` carrying severity, assurance and determinism, and `rule_spec` returns an error-severity `_DEFAULT_RULESPEC` for anything unregistered, so an unregistered rule is silently an error. `check_review_dangling`'s docstring states the `warning` rationale this plan adopts, and `_CARRIER_LEGACY_SEVERITY` states the opposite case (`info`, chosen because `artifact_core.drift_exit_code` exempts only `info` and a `warning` would have turned the tree red on 106 grandfathered findings). This plan has no grandfathered population, so the `check_review_dangling` precedent is the applicable one.
- `attention_contract` IS DATA PLUS VALIDATORS WITH NO FILE IO, and its `class_of` mapping is documented PURE, depending only on `(tree, native_status)` and never inferring from prose, dates, mtime or lock files. Resolution needs the filesystem, so it CANNOT go in `validate_gate_ref`. The shipped split is the dangling family: shape in the contract module, resolution in a `check_engine` sweep. E-01 and E-03 follow that split, which is also why E-01 is a one-line regex change rather than a resolution hook.
- A DANGLING-REFERENCE RULE DELIBERATELY DOES NOT REPORT A MALFORMED REFERENCE. `check_review_dangling` returns early when the subject id is missing because "a missing/malformed Subject-Id is the parser's diagnostic, not this rule's", and explicitly refuses to fall back to a default type because "a defaulted type is precisely how a migration bug would hide". E-03 copies both behaviors.
- CODE IS CITED BY SYMBOL OR QUOTED STRING, with a line number only appended to one of those and never alone, because an offset expires before the plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan names a symbol or quotes content.
- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE (`AGENTS.md`, GUIDING_PRINCIPLES P16). E-04 is written to that rule, which also rules out the shape of test that already exists against `DECISIONS.md`: `tests/test_project_layout.py::test_e06` slices the D130 section and asserts fixture topic strings appear in it, a content pin on prose. E-04 adds nothing of that kind.
- THE SUITE IS RUN BARE as `python3 -m pytest`, because `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Adding `-n0` makes it several times slower and a second `-q` suppresses the `N passed` line the execution contract requires pasting.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE DECISION-REF GRAMMAR REJECTS THREE RULINGS THAT EXIST.** `_DECISION_ID_RE` is `^D\d+$`, which cannot match an additive-suffix heading, and `DECISIONS.md` carries exactly three: `### D22b.`, `### D23b.`, `### D24b.`. They exist because the log disambiguated its own duplicate numbering additively while freezing the originals, a practice the log describes in its own prose ("duplicate D-numbers disambiguated additively (D22b/D23b/D24b), originals frozen"). So a gate citing one of those three rulings cannot be written at all. | Driven: `validate_gate_ref('decision', 'D22b')` is False. Parsed all `### D<n>[suffix].` headings: 156 total, 156 distinct as strings, of which `D22b`/`D23b`/`D24b` are rejected by the shipped regex and all 156 are accepted by the widened one. |
| F-02 | **A DECISION REF IS NEVER RESOLVED.** `validate_gate_ref` dispatches `decision` to a pure regex and returns, so a well-formed ref pointing at no ruling validates. The numbering is also NOT dense, so this is not a theoretical hole: the log skips 86, 87 and 89 entirely, meaning `D86` is a well-formed ref to a ruling that does not exist. | Driven: `validate_gate_ref('decision', 'D99999')` and `('decision','D0')` both True while the log's highest heading is `D156`. Gap computed over parsed headings: missing 86, 87, 89. |
| F-03 | **THE LIVE CORPUS IS CLEAN, SO THE NEW RULE SHIPS GREEN.** Exactly one backlog item carries any gate at all, and it is `artifact`, not `decision`. No spec carries a `decision` gate. So E-03 adds a rule with ZERO findings on the live tree, which is why `warning` is safe and why no grandfathering tier is needed. | Driven over `backlog.parse_item` for every item `backlog._iter_items` yields: 1 item with a gate (`artifact` / `yvvf98` / `blocked`). Grep of `.aw/records/` for `Gate-Kind: decision` returns only prose in executed plans and research, no live metadata. |
| F-04 | **A BARE TOKEN EXTRACTOR IS UNSOUND HERE, MEASURED.** This is the single largest implementation risk and the reason E-02 is its own item. A `\bD\d+[a-z]*\b` scan over `agent_workflows/`, `tests/`, `.aw/records/` and the root docs yields 4315 hits, 145 of which resolve to no heading. Anchoring to reject a preceding `-` or word character removes most but not all (37 remain). The false positives are other namespaces sharing the shape: `PR-D02` (review finding ids), `IPD-D701` (a retired lint code, whose comment reads "IPD-D701 is RETIRED and must not be revived"), `D401` (a flake8 `noqa` code), `RR-<RUN_ID>-D<number>` (release-review decision ids). E-02 therefore parses HEADINGS ONLY, where the `### ` anchor makes the extraction exact. | Both extractors run over 3225 files. Bare: 173 distinct tokens, 25 distinct unresolved. Anchored: 165 distinct, 17 distinct unresolved. Example sites inspected for each false class. |
| F-05 | **THE MECHANISM IS ALREADY WIRED END TO END, which is what makes repair cheaper than any new type.** `decision` has been in `GATE_KINDS` since the attention registry shipped; `backlog.validate_item` enforces kind membership and then `validate_gate_ref`; `specs`' checker does the same via its own gate reader and emits `attention.gate-malformed`; `backlog.run_new` and `aw set` both accept `--gate-kind`/`--gate-ref`; `attention._backlog_record` surfaces a gate as `{"kind","ref"}` on a blocked item. Nothing new has to be built for a ruling to be citable and visible. | Symbols read. `grep -l GATE_KIND_RE` returns exactly four modules: `attention_contract`, `backlog`, `specs`, `status_set`. |
| F-06 | **THE GOVERNING SPEC ALREADY SAYS THE REF IS A STABLE IDENTIFIER, so E-01 is conformance, not a contract change.** The implemented attention-registry spec Section 8.4 states `Gate-Ref` is "validated per kind" with "`todo`/`decision` = stable repo identifiers (a TODO id / `Dnn`)". The shipped regex is NARROWER than the log's actual id grammar; widening it brings code to the spec's intent. The spec's own OQ6 ("the `Gate-Ref` validators per kind, esp. `todo`/`decision` stable-id formats") is the open question this plan closes for `decision`. No spec amendment is needed and none is declared. | Spec Section 8.4 bullets and OQ6 read in `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`. |
| F-07 | **OPTION (a) IS A LARGE PERMANENT SURFACE, measured, which is why it is refused.** A new record class must be registered in `layout._default_record_classes` (a `RecordClassDefinition` with subpath, pattern, lifecycle subdirs and aliases), `lifecycle_dirs._RAW_LIFECYCLE_SUBDIRS`, `artifact_naming.ARTIFACT_TYPE_FACETS` (a deliberately CLOSED enum) and `TYPE_FACET`, `artifact_types.TYPE_BACKENDS`, `check_engine.SUPPORTED` and `_TYPE_FACET`, `attention_contract.TREE_POLICY` and `CLASS_MAPS`, `status_set.TYPE_STATUSES`, `record_placement`, `artifact_core.SCAN_ROOTS`, plus a README contract, a CLI verb module and an `aw attention` mapping. The backlog type alone carries roughly 7400 lines of type-specific tests. And a type that is absent from `check_engine.SUPPORTED` is invisible to `artifact_adopt.repository_id6s`, hence to the mint collision set, so a half-registered type silently breaks id6 uniqueness. | Registries read at the named symbols. Test line counts summed over the seven `test_backlog*.py` modules. `artifact_adopt.repository_id6s` iterates `check_engine.SUPPORTED`. |
| F-08 | **OPTION (b) IS ALREADY SHIPPED FOR THE CASE THAT MOTIVATED THE ITEM, so it needs no plan.** The 2026-09-24 maintainer ruling that Priority and Work-Kind are "DECIDED WHERE THE WORK IS FIRST RECORDED" is enforced in code: `backlog.run_new` requires both flags with no default, and `ipd_authoring` inherits them from the item under `--from-backlog` or requires them otherwise. The item's own text concedes this ("which the shipped 2026-09-24 ruling already implies"). What (b) cannot do is cover a ruling about an artifact whose fields have no slot for it, which is the general case this plan addresses. | Comments and refusals read at `backlog.run_new` and the two `ipd_authoring` sites. |
| F-09 | **OPTION (c) DOES NOT SCALE AND IS ALREADY AVAILABLE WHEN IT FITS.** A backlog item per decided artifact means one tracked record per governed artifact, which for the 2026-09-12 ruling would have been 15 items for one ruling. The carrier mechanism it reuses is real and this plan uses it (a `decision` gate can already point a blocked item at a ruling), but as the GENERAL answer it multiplies records per decision. | `_CARRIER_TARGET_TYPES` is `("backlog", "plans")`; the 15 ruled id6 are enumerated in backlog `iguvci` and in plan `nllamb`. |
| F-10 | **THE SIBLING PLAN IS BLOCKED AND THIS PLAN DOES NOT UNBLOCK OR SUPERSEDE IT.** `nllamb` (Set `iguvci`) is `- Status: reviewed` with `- Readiness: no-go` and a `- Blocking: yes` open question, refused at every lint checkpoint. Its own recorded maintainer options include "(c) let backlog `0szu1p` subsume it". This plan deliberately takes NONE of its scope: it does not implement `unreachable_ruling_targets`, does not register `check.ipd-ruling-target-unreachable`, and does not touch `d0cbt3` or the plans README. Whether `nllamb` is descoped or retired is the maintainer's call and is listed as an open question, not assumed. | `nllamb` front matter and its E-02 marker "BLOCKED AT REVIEW: DO NOT IMPLEMENT THIS ITEM AS SPECIFIED" read in `.aw/records/plans/pending/`. |
| F-11 | **THE ONLY CONSTRUCTOR OF A DECISION GATE IS CALLED FROM NOWHERE, so it is out of scope.** `set_records.promote_question_to_backlog` builds a `Gate-Kind: decision` item with `Gate-Ref=D<number>`, and a repository-wide search finds no caller in the package, no caller in `tools/`, and no test. Changing it would be unverifiable churn, so this plan leaves it alone; it benefits from E-01 automatically, since it calls `validate_gate_ref` before writing. | Searched `.py` and `.md` outside `.aw/records/`: the only hit is the definition. `tests/` has no reference. |
| F-12 | **ONE PENDING PLAN DECLARES `attention_contract.py` AND THERE IS NO SEMANTIC COLLISION.** `r61br4` (Set `qbfor9`, `- Status: approved`) declares the file, but its subject is the `aw attention --runs` Run column vocabulary and `RUN_SORT_ORDER`; it contains no reference to `GATE_KIND`, `validate_gate_ref`, `_DECISION_ID_RE` or `Gate-Ref`. No `- Item-Dependencies:` edge is owed, and per `AGENTS.md` the runners isolate each item in its own worktree, so declared file overlap is not a runtime hazard. One pending plan declares `set_records.py` (`jbipfa`), which this plan does not touch. | Both plans' `- Scope-Paths:` read; `r61br4` searched for all four symbols with no hits. |

## Proposed changes (ordered, validatable)

1. `attention_contract._DECISION_ID_RE`: `^D\d+$` becomes `^D\d+[a-z]*$`, still anchored at both ends. One line. Nothing else in the module changes, and the module acquires no file IO.
2. `check_engine`: a named heading parser for `DECISIONS.md` returning the defined decision ids, reading the file once and failing open to an empty set.
3. `check_engine.RULE_REGISTRY`: a `check.decision-ref-dangling` entry at `warning`, matching `check.review-dangling`'s tier and rationale.
4. `check_engine`: the sweep emitting that rule, enumerating gates through the existing backlog and spec parsers, skipping absent and malformed refs, wired into the `types == ["all"]` branch in its own `try`/`except`.
5. `tests/test_decision_ref_resolution.py`: nine behavior-only cases, the sweep ones built on throwaway trees.
6. `tests/test_attention_contract.py`: the suffixed case added to the existing gate-validator test.
7. `.aw/records/backlog/README.md`: one short section recording the answer to `0szu1p` and the disposition of its three options.
8. `CHANGELOG.md`: one entry.

## Deferred / out of scope (with reason)

- RESOLVING THE OTHER GATE KINDS WHOSE REFS DO NOT RESOLVE. `artifact` is regex-shape-only (two `deferred` specs still carry `Gate-Ref: TODO.md` for content migrated away from that file, and a prior plan measured that renaming `TODO.md` away entirely leaves `aw check specs` reporting `conforms`), and `todo` accepts any `_TODO_ID_RE` token. That is a strictly larger contract question than the `decision` kind's grammar, and it needs a decision about which kinds are resolvable at all (`issue` and `external` are not, in-tree).
  - Carrier: 2rnswc
- RETROFITTING A GATE ONTO THE 15 PLANS THE 2026-09-12 RULING NAMED. All 15 are terminal and unwritable, and `AGENTS.md` forbids changing what an executed plan records. Plan `nllamb` E-05 already owns recording that loss as unrepairable.
  - Carrier-Declined: the work is impossible by repository rule rather than merely unscheduled, and the recording of the loss is already owned by `nllamb` E-05; there is nothing for a carrier to do.
- CHANGING `set_records.promote_question_to_backlog`. It is called from nowhere (F-11), so any change would be unverifiable, and it already benefits from E-01 because it calls `validate_gate_ref` before writing.
  - Carrier-Declined: no behavior change is proposed or needed; the function is correct once the grammar it already consults is correct.
- DECIDING `nllamb`'s DISPOSITION. Whether that plan is descoped to its recording half or retired is the maintainer's call (F-10, OQ-01), and this plan neither needs nor assumes an answer.
  - Carrier-Declined: the question is raised as this plan's OQ-01 for the maintainer; `nllamb` is itself a live pending plan and so is already visible in `aw attention`, needing no second carrier.

## Scope check

- Over-scope: none. Every E-item serves either the two measured defects or the recording of the answer that keeps them fixed.
- Under-scope: the plan does not make a ruling's governed-artifact list machine-checkable, which is what `nllamb` attempted and what its F-13 measured as infeasible as specified (one `selectors.resolve` per token at roughly 154ms, 92 tokens per plan). This plan makes a ruling CITABLE and its citation RESOLVABLE; it does not verify that a ruling was APPLIED to the artifacts it names. That boundary is deliberate and is stated in E-05's recorded answer so no reader mistakes the one for the other.

## Required tests / validation

- `python3 -m pytest` run BARE, with the `N passed` summary line pasted. Also the two targeted modules run directly for per-test visibility.
- `aw check all` before and after, with both outputs pasted, demonstrating no new findings on the live corpus (F-03) rather than claiming a clean tree.
- `aw ipd lint` on this plan, conforming.
- Driven evidence for each defect, before and after: the three suffixed refs and the dangling-ref case.

## Spec / documentation sync

- NO SPEC AMENDMENT IS NEEDED OR DECLARED, and `- Scope-Paths:` names no `.spec.md` file. The implemented attention-registry spec Section 8.4 already specifies the `decision` ref as a "stable repo identifier (a TODO id / `Dnn`)"; the shipped regex is narrower than the log's real id grammar, so E-01 brings code INTO conformance with the spec rather than changing the contract (F-06). The spec's OQ6 asks for exactly this validator's format, and E-05's recorded answer is where that is settled for the `decision` kind.
- `.aw/records/backlog/README.md` is updated by E-05, which is the documentation deliverable this plan treats as load-bearing rather than incidental.
- `CHANGELOG.md` is updated by E-06.

## Open questions

### OQ-01: Does repairing the shipped decision gate satisfy backlog `0szu1p`, and what then becomes of the blocked sibling plan `nllamb`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING, because every E-item here is correct on its own terms regardless of the answer: the grammar rejects three real rulings and a ref resolves against nothing, and both are defects whether or not `0szu1p` is thereby closed. The question is raised because `0szu1p` asked which of three options to take and this plan argues for a fourth, which is a scope judgement the maintainer owns. `nllamb`'s own review recorded "(c) let backlog `0szu1p` subsume it" as one of three maintainer options, so an answer here may also settle that plan's disposition; this plan takes none of its scope either way (F-10) and does not touch it.
- Carrier-Declined: the question asks the maintainer to ratify a scope judgement about THIS plan and its sibling, both of which are live pending plans already visible in `aw attention`; a carrier would add a record that duplicates what the plans themselves already surface.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a driven before-and-after for `validate_gate_ref('decision', X)` over all of `D22b`, `D23b`, `D24b` (False then True) and over the four rejections `d12`, `D`, `D1x2`, `''` (False then still False), plus `D124` (True both times, the case the existing test pins). Then paste the result of applying `validate_gate_ref` to EVERY heading id parsed from the live `DECISIONS.md`, stating the count and that zero are rejected. State explicitly that the regex is still anchored at both ends and paste a rejection of `D12-garbage` proving it. Paste `git diff` for `attention_contract.py` showing ONE changed line, and state that the module still contains no `open`, `read_text`, `Path` or `rglob`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the parser's output count against the live `DECISIONS.md` (expect 156) and the three suffixed ids present in it. Paste the parser returning an empty set for an absent path rather than raising. THEN PASTE THE SOUNDNESS COMPARISON, which is the evidence this item exists for: run the naive `\bD\d+[a-z]*\b` extractor over the same corpus and paste its total, its unresolved count, and at least three named false-positive sites from DIFFERENT namespaces (expect `PR-D02`, `IPD-D701`, `D401`); then state the heading parser's unresolved count. Do not claim soundness without the comparison. If the live heading count is no longer 156, report the number you measured rather than the number this plan predicted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `RULE_REGISTRY` entry as committed, showing severity `warning`, and state which shipped rule's precedent it follows and why `info` was rejected (that `drift_exit_code` exempts only `info`). Paste `aw check all` BEFORE and AFTER with the HEAD each was run at, showing the finding count unchanged and NO `check.decision-ref-dangling` finding on the live corpus; do not report this as a clean run if the tree already has unrelated findings, report no-worsening against your own measured baseline. Paste a driven demonstration on a throwaway tree of the three boundaries: dangling ref gives exactly one finding at `warning` with this rule id, resolvable ref gives none, malformed ref gives none from this rule. Confirm the sweep is inside its own `try`/`except` in the `types == ["all"]` branch.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_decision_ref_resolution.py tests/test_attention_contract.py` output in full, then the BARE `python3 -m pytest` summary line with its HEAD. Confirm in writing that no test in the new module reads production source via `inspect`, `ast`, regex or substring search, asserts a caller count or symbol census, or pins a docstring or comment banner, and that each case asserts on a returned value, exit code or emitted finding. Confirm the sweep cases build throwaway trees and do not read the live `.aw/records/`. Name the falsifiable negative and paste it failing when the assertion is inverted.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the added README section verbatim. Confirm it names all three of `0szu1p`'s options with an explicit disposition for each, states the measured reason (a) is refused rather than asserting a preference, and states the under-scope boundary (citable and resolvable, NOT verified-as-applied). Paste `git diff` for `.aw/records/backlog/README.md` proving no other section changed. State plainly whether the text would let a future author answer `0szu1p` without re-deriving the question, which is the whole purpose of this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the CHANGELOG entry and confirm it names both the grammar fix and the new rule id, and that it contains no em or en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, because readiness is an output of `/plan-review` and writing one at authoring time would forge a review that has not happened. It requires explicit human approval before execution.

Executing agent: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change, since other agents may be working in this checkout. Run the suite BARE and paste the actual output; do not claim a pass you did not run. On completion, move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item above carries real pasted evidence.
