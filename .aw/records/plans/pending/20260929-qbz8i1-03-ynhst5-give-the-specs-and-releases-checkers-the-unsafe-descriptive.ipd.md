# IPD: Give the specs and releases checkers the unsafe descriptive field rule the backlog tree already has

- Date: 2026-09-29
- Kind: child
- Concern: `specs.validate_spec` applies `attention_contract.is_safe_descriptive` to `- Gate-Summary:` ONLY, and `releases.validate_release` applies it to nothing, so the field each tree actually surfaces to a human and to an agent is unchecked. Measured in this lane: a 900-character `- Scope:` and a `- Scope:` containing ANSI escape bytes each pass `aw specs check` clean, and the ANSI case reaches a terminal RAW through `aw attention --details --no-color` while `aw attention --format json` still reports `"valid": true`. That violates Section 8.8's "the renderers never emit raw control characters". Two COMMITTED specs already carry an over-length `- Scope:` (366 and 314 characters), which is why this needs a deliberate decision about the existing population rather than only a new rule.
- Scope: Extend `specs.validate_spec` to judge `- Scope:` and `- Summary:` with the already-catalogued `attention.unsafe-field` rule id, extend `releases.validate_release` to judge `- Summary:`, register the id in `check_engine.RULE_REGISTRY` so it carries an explicit severity instead of falling through to the default, and FIX the two pre-existing violations in place rather than grandfathering them. DELIBERATELY NOT COVERED: the newline vector, which F-05 proves NO checker can see and which Order 01 closes at the write path; and any new rule id, since `attention.unsafe-field` already exists in the closed catalog.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/releases.py, agent_workflows/check_engine.py, tests/test_specs_releases_unsafe_field.py, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: qbz8i1
- Blocks-Release: next
- Set: qbz8i1
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ynhst5

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `qbz8i1`, which names this half explicitly ("Closing the specs half therefore needs a new checker rule as well as a write-path guard, which is new policy and is why dtg7dz declined to fold it in"). Measured that it needs NO new rule id, because `attention.unsafe-field` is already in the closed `RULE_IDS` catalog and already used by `specs.validate_spec` for `Gate-Summary`, so the change is widening an existing rule's field coverage rather than minting policy. Also censused the whole population and found exactly two violations, which changed the design from grandfathering to fixing them.
- 2026-09-29 draft (opencode): created.

## Goal

Make the specs and releases checkers judge the descriptive fields those trees actually render, so an over-length or control-character value is a named finding rather than silently valid text that reaches a human terminal unescaped. Close the part of the trust boundary a checker CAN close, and state plainly the part it cannot.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: repair the existing population FIRST

- [ ] E-01 Shorten the `- Scope:` value of the two committed specs that violate the bound, BEFORE any rule exists, so the tree is clean when the rule lands and the rule can ship fail-closed with no grandfather tier. The two are `20260730-2152-01-agents-artifact-organization.spec.md` (366 characters, `- Status: implemented`) and `20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md` (314, `- Status: approved`). Reduce each to at most `A.MAX_DESCRIPTIVE_LEN` (300) while preserving its meaning.
  THIS ORDERING IS THE WHOLE REASON THIS IS ITEM ONE. If the rule landed first, `aw check specs` would exit 1 on a clean checkout and fail CI, forcing either a grandfather tier (added complexity, and a permanent excuse) or a same-commit fix (which mixes a records edit with a code change in one diff a reviewer cannot separate). Fixing first makes the rule's arrival a no-op on the tree, which is also the evidence V-05 demands.
  DO NOT DELETE INFORMATION TO MEET THE BOUND. A `- Scope:` line is a summary of a spec whose body states the detail, so compress the summary; if a value genuinely cannot be said in 300 characters, that is an argument to reconsider the bound (OQ-02), not to truncate the meaning. Neither of these two needs that: both currently pack two sentences into the field. Do NOT edit any other part of either spec, and specifically do NOT touch the `implemented` spec's `- Status:` or history; a records repair is not a lifecycle transition.
  - Depends on: none
  - Expected outcome: both `- Scope:` values are at most 300 characters and still describe the same scope; `python3 -c` over the whole specs tree reports ZERO values failing `A.is_safe_descriptive`, where it reported 2 before.
  - Execution state: pending

### Task group 2: widen the rule's field coverage

- [ ] E-02 In `specs.validate_spec`, judge `- Scope:` and `- Summary:` with `A.is_safe_descriptive` and report the EXISTING `attention.unsafe-field` rule id on failure, alongside the `Gate-Summary` check already there. Read the values from the METADATA REGION ONLY, using whatever bounded reader the function already uses for its other bullets, so a `- Scope:` shown as an EXAMPLE inside the spec body is not judged as metadata.
  THE METADATA-REGION BOUND IS NOT OPTIONAL AND HAS A TEST THAT WILL CATCH ITS ABSENCE. `tests/test_specs_verbs.py::test_body_gate_example_is_not_a_real_gate` pins exactly this property for gate bullets, with the comment "only the metadata block (before the first `## `) counts", and specs in this repository routinely quote metadata bullets inside their own prose. An unbounded regex over the whole document would flag those quotations.
  DO NOT MINT A NEW RULE ID. `attention.unsafe-field` is already a member of the closed `attention_contract.RULE_IDS` catalog, is already documented there as covering "control-char / over-length / newline / non-http issue url", and is already emitted by this same function for `Gate-Summary`. Adding a `spec.summary-unsafe` sibling would fork the vocabulary for one tree; `tests/test_attention_contract.py` also asserts the catalog's membership and minimum size, so a new id is a catalog change this plan does not need.
  Keep the drift DETAIL escaped through `A.escape_detail`, as the neighbouring gate drifts in this function already do, and do NOT include the offending value itself in the detail: the value is the untrusted text, and echoing it into a `location<TAB>rule<TAB>detail` record would push the injection into the agent surface the rule exists to protect.
  - Depends on: E-01
  - Expected outcome: a spec whose `- Scope:` is 301 characters, or contains a BEL or an ANSI ESC, yields exactly one `attention.unsafe-field` drift from `validate_spec`, while a spec quoting `- Scope:` inside its body after a `## ` heading yields none; and `test_body_gate_example_is_not_a_real_gate` still passes.
  - Execution state: pending

- [ ] E-03 In `releases.validate_release`, judge `- Summary:` with the same predicate and the same `attention.unsafe-field` id. The module currently imports no `attention_contract`, so add that import; it validates only `- Id:`, `- Status:` and `- Version:` today.
  ACCEPT BOTH SUMMARY DIALECTS OR JUDGE ONLY THE BULLET ONE, AND SAY WHICH. `releases._SUMMARY_RE` matches the `- Summary:` bullet that `plan_release` writes, and the module's own comment records that a release summary "lives either as a `- Summary:` bullet ... or as a `## Summary` prose section (the shape the hand-authored 2.0.0 record uses)". The single committed release record uses the PROSE form, so it has no bullet to judge and this rule will not fire on it either way. Judge the BULLET form only, because a prose section is a body, not a descriptive field, and bounding a prose section to 300 characters would be a new and wrong policy.
  - Depends on: E-02
  - Expected outcome: a release record whose `- Summary:` bullet is over-length or control-char-bearing yields one `attention.unsafe-field` drift, while the committed `2.0.0` record (which carries a `## Summary` prose section and no bullet) yields none and `aw check releases` stays clean.
  - Execution state: pending

- [ ] E-04 Register `attention.unsafe-field` in `check_engine.RULE_REGISTRY` at severity `error`, assurance `ASSURANCE_REPOSITORY`, determinism `DET_DETERMINISTIC`, with a comment stating why each value was chosen and why registration is not bookkeeping.
  REGISTRATION CHANGES NOTHING ABOUT THE EXIT CODE TODAY AND IS STILL REQUIRED, which is the subtlety to record in the comment: an unregistered id falls through to `_DEFAULT_RULESPEC`, which is already `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`, so the observable severity is identical. What registration buys is that the severity becomes DECLARED rather than inherited, so a future change to the default cannot silently reclassify this rule. The in-repo precedent for making exactly this reasoning explicit is the `check.stale-index-missing` / `check.stale-index-stale` pair, whose comment records that an unregistered rule "silently did" fall through to the default.
  `error` IS CORRECT AND THE ALTERNATIVE WAS CONSIDERED: `drift_exit_code` exempts ONLY `info`, so `info` would make the rule advisory and non-failing, and the governing spec's F10 states these violations ARE failures ("violations of any of these are stable named `--check` failures"). E-01 having already cleaned the tree means `error` costs nothing on a clean checkout, which is the condition that makes a grandfather tier unnecessary here and distinguishes this case from `check.ipd-uncarried-obligation`, which needed one because 106 plans were non-conforming.
  Leave the `invariant` field EMPTY rather than guessing an id: the Phase-0 catalog invariant this maps to is Section 8.8's output-safety property, and no existing registry entry claims it, so inventing a mapping would be a false trace. Say so in the comment, as the `stale-index` entries do with their own empty invariants.
  - Depends on: E-03
  - Expected outcome: `check_engine.rulespec("attention.unsafe-field")` (or the registry lookup the module exposes) returns the declared `RuleSpec` rather than `_DEFAULT_RULESPEC`, with `severity == "error"`, and `aw check specs` / `aw check releases` exit codes are unchanged on a clean tree.
  - Execution state: pending

### Task group 3: pin the coverage and the honest limit

- [ ] E-05 Add `tests/test_specs_releases_unsafe_field.py` pinning the new coverage for all four Section 8.8 shapes that a checker CAN see (over-length, BEL, ANSI ESC, and a C1 control), on `- Scope:` and `- Summary:` for specs and `- Summary:` for releases, each asserting exactly the `attention.unsafe-field` id. Follow the established fixture-driven template `test_each_violation_fixture_flags` in `tests/test_specs_verbs.py`, which maps a fixture filename to an expected rule id, and the existing `tests/fixtures/attnview/violations/unsafe-field.md` fixture, which already pins this id for `Gate-Summary`.
  THE TEST MUST ALSO PIN THE LIMIT, and this is the part that keeps the record honest: assert that a spec whose `- Scope:` was produced by NEWLINE INJECTION (a safe `- Scope: legit` line followed by a smuggled `- Blocks-Release: next` bullet) yields NO `attention.unsafe-field` drift, with a comment naming F-05 and pointing at Order 01 as the only place that vector can be closed. A reader must not be able to conclude from this test module that the checker closed injection.
  Non-regressions: the `Gate-Summary` case still flags (the existing fixture must keep passing); the metadata-region bound holds (a body-quoted `- Scope:` does not flag); every spec in `tests/fixtures/attnview/specs-valid/` still validates clean; and the registry entry is asserted to exist with severity `error` rather than assumed.
  - Depends on: E-04
  - Expected outcome: a new module whose over-length and control-character cases FAIL against pre-E-02 code (`validate_spec` returns `[]`) and PASS after; whose injection case passes in BOTH states, documenting the limit; and whose non-regression cases pass in both.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE RULE ID ALREADY EXISTS, so this is field-coverage widening and not new policy, which is a material correction to the backlog item's framing ("needs a new checker rule ... which is new policy"). `attention.unsafe-field` is a member of `attention_contract.RULE_IDS`, documented there as "control-char / over-length / newline / non-http issue url", and `specs.validate_spec` already emits it for `Gate-Summary`.
- THE CLOSED CATALOG IS PINNED BY A TEST, so minting a sibling id is not a free choice: `tests/test_attention_contract.py` iterates `A.RULE_IDS` and asserts specific members plus a minimum size. The catalog's own comment states that consumers "MUST use these ids; they do NOT free-hand new ones".
- THE METADATA-REGION BOUND IS AN ESTABLISHED, TESTED PROPERTY of this validator: `test_body_gate_example_is_not_a_real_gate` asserts that gate bullets shown as an example after a `## ` heading are not read as real metadata. Any new field read must respect the same bound or that test's sibling property breaks for `- Scope:`.
- AN UNREGISTERED RULE ID ALREADY BEHAVES AS `error`, because `_DEFAULT_RULESPEC` is `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`. So E-04 is about making the severity DECLARED, not about changing behavior; the `check.stale-index-*` entries record exactly this reasoning for their own case.
- `drift_exit_code` EXEMPTS ONLY `info`, measured in its own source ("an `info`-severity finding is ADVISORY ... only error/warning-class findings drive the nonzero exit"). So a `warning` tier is NOT advisory here and `info` is the only non-failing severity, which is what makes the E-01-first ordering necessary rather than optional.
- THE GOVERNING SPEC ALREADY REQUIRES THIS, so no spec amendment is needed. Spec `attention-registry-and-cross-tree-status` Section 8.8 requires bounded single-line control-char-free descriptive fields; F10 makes violations "stable named `--check` failures"; A14 requires "hostile-string fixtures" for a newline, an ANSI/control character, a Markdown-table-breaking string and an over-length value, which E-05 supplies for these two trees.
- `releases.py` DELIBERATELY HAS NO `check` VERB, and its module docstring says so ("There is deliberately NO `run_check`: `aw check releases` already validates release records through `check_engine` -> `validate_release`"). So E-03's change reaches users through `aw check releases` and must not add a second entry point.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'` (AGENTS.md).

## Findings

All findings were DRIVEN in this lane at HEAD `f4b00263`: the census figures over the real records trees, the behavioral ones against temporary fixture repositories.

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE SPECS TREE HAS NO BOUND ON THE FIELD IT ACTUALLY SURFACES. A 900-character `--summary` writes a 909-character `- Scope:` line that `validate_spec` and `aw specs check` both accept. | Driven: `aw specs new --summary <900 chars> --apply` exited 0; the written `- Scope:` line measured 909 characters; `specs.validate_spec` returned `[]`; `aw specs check --agent` reported `"outcome":"clean","checked":1,"findings":0`. `A.MAX_DESCRIPTIVE_LEN` is 300. |
| F-02 | CONTROL CHARACTERS PASS TOO, AND REACH A HUMAN TERMINAL RAW, which is the trust-boundary half of Section 8.8 rather than a tidiness issue. | Driven: a `- Scope:` of `a\x07b` produced `validate_spec` `[]` and `specs check` clean. A `- Scope:` of `red\x1b[31mINJECTED\x1b[0m` produced `aw attention --details --no-color` output containing the literal bytes `'scope: red\x1b[31mINJECTED\x1b[0m'`, and `aw attention --format json` reported `"valid": true` with `"violations": []` and `detail_text` carrying the raw escape. Section 8.8 states "The renderers never emit raw control characters". |
| F-03 | `releases.validate_release` CHECKS NO DESCRIPTIVE FIELD AT ALL; it validates three metadata fields and nothing else. | Driven: `aw releases new --summary <900 chars> --apply` and `--summary 'a\x1b[31mred'` each exited 0 with `validate_release` returning `[]`; the written file's bytes contain `- Summary: a\x1b[31mred`. The function's own body reports only `release.id-missing`, `release.status-missing`, `release.status-invalid` and `release.version-missing`. |
| F-04 | THE RULE ID NEEDED ALREADY EXISTS AND IS ALREADY EMITTED BY THIS VALIDATOR, so the backlog item's "needs a new checker rule ... new policy" framing is wrong and this plan mints nothing. | `attention.unsafe-field` is a member of `A.RULE_IDS` with the inline comment "control-char / over-length / newline / non-http issue url", and `specs.validate_spec` already emits it with the detail "Gate-Summary is over-length or has control chars/newlines". `grep -rn "unsafe-field" agent_workflows/*.py` matches exactly two files: the catalog and that one specs site. |
| F-05 | THE NEWLINE VECTOR IS UNREACHABLE FROM ANY CHECKER, so this plan CANNOT close the injection the backlog item reports, and must not be read as doing so. | Driven: on a spec written with `--summary $'legit\n- Blocks-Release: next'`, the value `validate_spec` sees for `- Scope:` is `'legit'`, a safe bounded control-char-free line, so the predicate passes correctly and `validate_spec` returns `[]` while the smuggled `- Blocks-Release: next` parses as the record's real gate (`aw releases show next` lists it as a blocker). The unsplit value exists only at the write path, which is Order 01's scope. |
| F-06 | EXACTLY TWO COMMITTED ARTIFACTS VIOLATE THE BOUND, both on `- Scope:` and both control-char-free, so the population is small enough to FIX rather than grandfather. | Censused every `- Scope:`, `- Summary:`, `- Gate-Summary:` and `- Concern:` value across all 38 specs and the 1 release record: `- Scope:` n=22 with 2 unsafe (366 characters in `20260730-2152-01-agents-artifact-organization.spec.md`, status `implemented`; 314 in `20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md`, status `approved`); `- Summary:` n=1 unsafe 0; `- Gate-Summary:` n=3 unsafe 0; `- Concern:` n=0. The release tree has ZERO `- Summary:` bullets, because its one record uses the `## Summary` prose form. |
| F-07 | BOTH OFFENDING VALUES ARE COMPRESSIBLE WITHOUT LOSING INFORMATION, so E-01 is a real fix rather than a truncation. Each packs two sentences into a one-line summary field whose body already carries the detail. | Read directly: the 366-character one is a general-principle sentence plus a separate "IMPLEMENTATION is scoped to ... first; the other areas are named future adopters" sentence; the 314-character one is a three-clause sentence plus "ADDITIVE to the existing semantic coverage probe, which it does not replace." Both specs' bodies state these points at length. |
| F-08 | `info` WOULD MAKE THE RULE ADVISORY AND IS THEREFORE WRONG HERE, and `warning` is NOT advisory despite the word, so the severity choice is constrained rather than free. | `artifact_core.drift_exit_code` returns 1 "if any(getattr(d, 'severity', '') != 'info' ...)", i.e. only `info` is exempt. Spec Section 8.8/F10 requires these be `--check` failures. The `check.ipd-uncarried-obligation` comment records the same measurement ("a `warning` grandfather tier would exit 1 with 106 findings ... and fail the CI"). |
| F-09 | AN UNREGISTERED ID ALREADY RESOLVES TO `error`, so E-04 changes no exit code and its value is purely that the severity stops being inherited. | Driven: the registry has 52 entries and `'attention.unsafe-field' in check_engine.RULE_REGISTRY` is **False**, while `_DEFAULT_RULESPEC` is `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`. So the rule already behaves as an error today wherever it fires. |
| F-10 | NO TEST PINS DESCRIPTIVE SAFETY FOR `- Scope:` OR A RELEASE `- Summary:`; the only coverage is the `Gate-Summary` fixture. | `grep -rn "unsafe-field" tests/` matches `tests/test_attention_contract.py` (catalog membership plus a `Gate-Summary` fixture) and `tests/test_specs_verbs.py` (the fixture-to-rule map). The fixture `tests/fixtures/attnview/violations/unsafe-field.md` carries an over-length `- Gate-Summary:` and nothing else. |
| F-11 | THE METADATA-REGION BOUND MATTERS IN PRACTICE, not just in principle, because specs here quote metadata bullets in their own prose. An unbounded read would produce false findings. | `tests/test_specs_verbs.py::test_body_gate_example_is_not_a_real_gate` exists precisely for this, asserting that a spec showing `- Status: deferred` and `- Gate-*` bullets inside a fenced example after a `## ` heading yields `[]`. The `.aw/records/specs/` tree contains specs that quote `- Scope:`-style bullets in body prose for the same documentary reason. |

## Proposed changes (ordered, validatable)

1. E-01: shorten the two over-length committed `- Scope:` values (F-06, F-07), so the tree is clean before any rule exists and no grandfather tier is needed.
2. E-02: judge `- Scope:` and `- Summary:` in `specs.validate_spec` with the existing `attention.unsafe-field` id, read from the metadata region only, with the detail escaped and the offending value NOT echoed.
3. E-03: judge the `- Summary:` bullet in `releases.validate_release` with the same id, leaving the `## Summary` prose form alone by decision.
4. E-04: register the id in `RULE_REGISTRY` at `error` with an empty invariant and a comment recording why registration matters despite not changing today's behavior (F-09).
5. E-05: pin the four checker-visible shapes on all three fields, pin the NEWLINE LIMIT explicitly (F-05), and keep the existing `Gate-Summary` fixture and metadata-region properties green.

## Deferred / out of scope (with reason)

- THE NEWLINE INJECTION VECTOR IS NOT CLOSED BY THIS PLAN AND CANNOT BE. F-05 measured why: the value is split into separate lines before any checker sees it, so the predicate is handed only the safe half and correctly passes. This is the single most important limit of this plan and E-05 pins it as a test so the record cannot later be misread as having closed it.
  - Carrier: uz05bl
- HISTORY-RECORD MESSAGES ARE NOT BOUNDED by this plan, on either tree. Measured over the specs tree: 59 of 146 committed history messages exceed 300 characters, median 235, max 2594, and 0 contain a control character. So bounding them would make `aw check specs` fail on 40.4 percent of the tree's own history, and no checker anywhere in this repository bounds a history message. A LINE-INTEGRITY rule for them (control characters only, no length) would be measurably safe, but it is a new policy for a different field class than the one this plan is scoped to.
  - Carrier-Declined: Nothing is owed, because no measured harm survives unowned: the WRITE-PATH half of history-message safety, which is where the forgery vector actually enters, is closed for these two trees by Order 01 (`uz05bl` E-03) and for the shared positional setter by `nw9dmz`. What a checker rule would additionally catch is a HAND-EDITED control character in a history line, for which this census found zero instances across 146 records and which no measurement here shows causing harm. Filing a carrier would schedule a new field-class policy on the strength of no evidence.
- THE MARKDOWN-ESCAPING HALF OF SECTION 8.8 IS NOT IMPLEMENTED. The spec requires that "The Markdown board escapes Markdown metacharacters deterministically so a field cannot break the table, inject a link/image, or start a new block", and this plan adds no escaping to any renderer; it only makes over-length and control-character values a named finding. A pipe character in a `- Scope:` can still break a rendered table.
  - Carrier: llnvwj
- ANY NEW RULE ID (for example a `spec.summary-unsafe` mirroring `backlog.summary-unsafe`) IS DELIBERATELY NOT MINTED, so the two trees report the SAME finding under different ids (`backlog.summary-unsafe` on backlog, `attention.unsafe-field` here). That asymmetry is pre-existing and this plan preserves rather than resolves it.
  - Carrier-Declined: Nothing is owed because the current state is correct rather than deferred: `attention.unsafe-field` is the id the closed `RULE_IDS` catalog already designates for this violation class, the catalog's own comment forbids free-handing new ids, and `tests/test_attention_contract.py` pins the catalog. Minting a specs-specific sibling would fork the vocabulary to make two trees look symmetrical, which is a cosmetic gain traded against the single-vocabulary property the catalog exists to enforce. The backlog tree's differently-named id predates the catalog's use here and renaming it is a separate compatibility question no finding in this plan raises.
- WIDENING THE SAME CHECK TO OTHER TREES (`research`, `prompts`, `walkthroughs`, `roadmaps`) is out of scope. Each has its own front-matter dialect (research is YAML, prompts is an HTML comment), its own field names, and its own validator, so a sweep would be several unrelated validator changes in one commit.
  - Carrier: 7w6zsl

## Scope check

- Over-scope: none. Two field reads added to one validator, one added to a second, one registry entry, one new test module, and two one-line records repairs. No new rule id, no change to `is_safe_descriptive` or `MAX_DESCRIPTIVE_LEN`, no change to any renderer, no change to `RULE_IDS`, no new command, and no change to any write path (Order 01 owns those).
- Under-scope, stated in full because this plan closes only what a checker can reach: (a) the NEWLINE vector stays open at the checker and is closed only by Order 01, which is the plan's defining limit (F-05); (b) history-record messages stay unbounded and unjudged on both trees; (c) Markdown metacharacter escaping is still unimplemented, so the Section 8.8 renderer obligation is only partly met, carried by `llnvwj`; (d) other records trees keep no descriptive-field rule, carried by `7w6zsl`; (e) a release `## Summary` PROSE section is judged by nothing, by decision; (f) the backlog tree keeps its differently-named `backlog.summary-unsafe` id, so the vocabulary stays asymmetric across trees.

## Required tests / validation

- `python3 -m pytest tests/test_specs_releases_unsafe_field.py` for the new module (run bare; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`).
- `python3 -m pytest tests/test_specs_verbs.py tests/test_attention_contract.py tests/test_releases.py tests/test_releases_cli.py tests/test_check_engine_spec_criteria.py tests/test_doctor.py` as the targeted regression set: these own the validator being widened, the closed rule catalog and its `Gate-Summary` fixture, the release validator, and the doctor's rule-to-remediation table which keys on rule ids.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression.
- `aw specs check --agent`, `aw check specs --agent`, `aw check releases --agent` and `aw check all` must ALL report clean/conforms on the repository tree AFTER E-01, which is the evidence that shipping at `error` needs no grandfather tier. Re-derive the `checked` counts at execution rather than trusting this plan's figures.
- PRE-FIX FALSIFICATION IS REQUIRED: V-05 must show the over-length and control-character cases FAILING against pre-E-02 code with `validate_spec` returning `[]`. Obtain that run by authoring the test module first, or against a separate `git worktree` at HEAD; do NOT `git stash push -- agent_workflows/specs.py`, since this checkout is shared and stashing a path can swallow a co-worker's uncommitted edit.
- E-01 MUST BE VALIDATED SEPARATELY AND BEFORE the rule lands (V-01), because its whole purpose is to make the tree clean in advance; validating it only after E-02 would not distinguish "the tree was cleaned" from "the rule does not fire".

## Spec / documentation sync

N/A with reason, and this was checked rather than assumed. This plan makes the checkers enforce a contract the governing spec ALREADY states, so no `.spec.md` is amended and no spec path appears in `- Scope-Paths:` for an AMENDMENT reason. Spec `attention-registry-and-cross-tree-status` Section 8.8 already requires bounded single-line control-char-free descriptive fields, its F10 already makes violations "stable named `--check` failures", and its A14 already requires the hostile-string fixtures E-05 supplies. The rule id is already in the closed catalog (F-04), so the catalog needs no amendment either.

TWO `.spec.md` PATHS DO APPEAR IN `- Scope-Paths:`, and they are there as E-01 RECORDS REPAIRS, not as contract amendments: the two committed specs whose `- Scope:` value exceeds the bound (F-06). They are declared because the runners announce and reconcile declared spec edits, and an undeclared spec change is reported at run end even when benign. Neither edit changes any normative statement, any status, or any history record; each shortens one summary line so the artifact obeys the contract it is already subject to. The `implemented` one in particular is NOT being reopened: editing a record to conform is not a lifecycle transition.

## Open questions

### OQ-01: Fix the two over-length specs, or grandfather them with a staged severity tier?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE CENSUS: fix them, and do it FIRST. The decision turns entirely on population size, which is why F-06 censused rather than estimated: there are exactly TWO violations, both on `- Scope:`, both control-char-free, and both compressible without information loss (F-07). Against that, a grandfather tier means adding a per-artifact severity downgrade (the `check.ipd-uncarried-obligation` shape) plus a cutover date, and it leaves a permanent exemption whose only beneficiaries are two records a five-minute edit fixes. The precedent that needed a tier needed it for 106 plans; two is not that. Fixing first also means the rule can ship at `error` with zero findings on a clean checkout, which is both simpler and the stronger validation (V-05). THE COST OF THIS CHOICE, stated plainly: it edits a spec whose status is `implemented` and one whose status is `approved`, which the repository treats as settled records. That is acceptable ONLY because the edit is a conformance repair to a summary line and changes no normative statement, no status and no history, and E-01 forbids touching anything else; it would NOT be acceptable for a change to what either spec requires.

### OQ-02: Is `MAX_DESCRIPTIVE_LEN` of 300 the right bound for a `- Scope:` line, given two of 22 exceed it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: yes, keep 300, and do not touch the constant. 20 of 22 committed `- Scope:` values already fit (median 171.5), so the bound is empirically livable rather than aspirational, and both exceptions are two-sentence values whose second sentence belongs in the body (F-07). The constant is also SHARED: `A.MAX_DESCRIPTIVE_LEN` governs backlog summaries, gate refs, gate summaries and evidence citations across every tree, and `backlog.validate_item` already enforces it on 674 items with zero findings, so raising it to accommodate two spec lines would loosen a contract five trees currently satisfy. NON-BLOCKING because nothing in this plan depends on the number: E-02 asks the predicate for a verdict and never reads the constant, so a future decision to change the bound needs no change here. If a reviewer disagrees, the right move is a separate change to the shared constant with its own cross-tree measurement, not a spec-tree exemption.

### OQ-03: Should the drift detail include the offending value, so a human can see what was wrong?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: no, and the reason is the rule's own purpose. The detail lands in the `location<TAB>rule<TAB>detail` agent record and in human output, so echoing an untrusted over-length or ANSI-bearing value would push the exact payload this rule exists to flag into the surface it exists to protect, and for a control-character value it would emit the raw escape into a terminal even as it reports that doing so is a violation. `A.escape_detail` escapes tab, newline and backslash to keep the record one line, and deliberately does NOT strip C0/C1 controls, so escaping is not sufficient protection. The existing sibling detail is already value-free and descriptive ("Gate-Summary is over-length or has control chars/newlines"), so E-02 follows it. The residue is that a user must open the file to see the offending value, which is acceptable because the finding names the file and the field.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a `git diff` of the two specs showing ONLY the `- Scope:` line changed in each, and paste the before and after character counts for both (before: 366 and 314; after: each at most 300, with the actual numbers). Paste the full before and after text of each value so a reviewer can judge that meaning was preserved rather than truncated. Then paste the output of a census over the WHOLE specs tree showing ZERO `- Scope:`/`- Summary:`/`- Gate-Summary:` values failing `A.is_safe_descriptive`, where it previously reported 2. THIS MUST BE RUN BEFORE E-02 EXISTS: state explicitly that the rule was not yet in the tree when this evidence was captured, since E-01's whole purpose is to precede it. Also confirm from the diff that neither spec's `- Status:` line nor its `## Workflow history` was touched.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a Python session calling `specs.validate_spec` on fixtures and showing the returned drift for each: a 301-character `- Scope:` yielding exactly one `attention.unsafe-field`; a `- Scope:` containing BEL yielding the same; one containing ANSI ESC yielding the same; one containing a C1 control yielding the same; a 300-character `- Scope:` yielding `[]` (the boundary); an over-length `- Summary:` yielding the finding. Then paste the METADATA-REGION proof: a spec that quotes `- Scope: <301 chars>` inside a fenced block AFTER a `## ` heading yielding `[]`, plus the passing output of `tests/test_specs_verbs.py::test_body_gate_example_is_not_a_real_gate`. Finally paste the emitted drift's DETAIL string showing it does NOT contain the offending value (OQ-03), and the source showing `A.escape_detail` is applied as the neighbouring gate drifts do.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a Python session calling `releases.validate_release` on an over-length `- Summary:` bullet and on a control-char-bearing one, each yielding exactly one `attention.unsafe-field` drift, and on a conforming one yielding `[]`. Then paste `releases.validate_release` run against the ACTUAL committed `2.0.0` record showing `[]`, confirming the `## Summary` prose form is untouched as E-03 decided, and `aw check releases --agent` on the repository tree reporting clean. Also paste the pre-fix counterpart for the over-length case showing `[]`, proving the rule is new coverage rather than something that already fired.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a Python session showing `'attention.unsafe-field' in check_engine.RULE_REGISTRY` is now `True` and the returned `RuleSpec`, with `severity == "error"`, `assurance == ASSURANCE_REPOSITORY`, `determinism == DET_DETERMINISTIC` and an EMPTY invariant. Paste the same lookup from HEAD showing `False`, and paste `_DEFAULT_RULESPEC` so the claim that the observable severity is unchanged (F-09) is visible rather than asserted. Then MEASURE the exit code the severity implies rather than reasoning about it: paste `artifact_core.drift_exit_code([...])` for a single `attention.unsafe-field` drift showing 1, and paste the registered comment showing it records why registration matters despite not changing today's behavior and why the invariant is empty.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the full `python3 -m pytest tests/test_specs_releases_unsafe_field.py` output including the `N passed` line. Then paste the PRE-FIX run showing the over-length and control-character cases FAILING with `validate_spec` returning `[]` in the assertion text. STATE WHICH CASES PASSED IN BOTH STATES and why: the NEWLINE-INJECTION case must pass before and after, because F-05 proves no checker can see it, and a run where it fails after the fix means the test was written against the wrong property. Also paste: the existing `tests/fixtures/attnview/violations/unsafe-field.md` `Gate-Summary` case still flagging; every `tests/fixtures/attnview/specs-valid/` spec still clean; the bare full-suite run with its `N passed` line; and `aw specs check --agent`, `aw check specs --agent`, `aw check releases --agent` and `aw check all` on the repository tree all reporting clean/conforms, which is the evidence that `error` severity needed no grandfather tier.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, and `- Readiness:` is deliberately ABSENT because that field is an output of `/plan-review`, not of authoring. Execute only the checklist above; commit through `aw commit <this plan> -- <the paths in Scope-Paths>` and never `git add -A`, verifying the staged set before each commit because this checkout is shared. Do not push and do not tag. After every `V-*` item carries pasted evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled transition (`aw ipd set executed`), never by hand.

TWO DECLARED SPEC EDITS: this plan's `- Scope-Paths:` names two `.spec.md` files, which the runners announce before the run starts and reconcile at run end. They are E-01 conformance repairs to a single summary line each, not contract amendments; see the Spec / documentation sync section for why that is legitimate and what it deliberately does not touch.

INDEPENDENCE: this plan declares `- Item-Dependencies: none` and is independent of its siblings. It edits `specs.validate_spec`, `releases.validate_release` and `check_engine.RULE_REGISTRY`; Order 01 and Order 02 edit `specs.run_new`/`run_set`/`run_note`, which are different functions in one of the same files. If run in parallel lanes the merge-and-revalidate gate sees both edits to `specs.py`; they are in disjoint functions, so that is a normal merge rather than a hazard. ORDER RELATIVE TO ORDER 01 IS WORTH NOTING even though it is not a dependency: if Order 01 lands first, the injection fixture E-05 needs can no longer be produced through the verb, so E-05 must build it by rendering a string (`specs._render_new_spec`) or by writing the fixture bytes directly, which is what that item already specifies.
