# IPD: Give the specs and releases checkers the unsafe descriptive field rule the backlog tree already has

- Date: 2026-09-29
- Kind: child
- Concern: `specs.validate_spec` applies `attention_contract.is_safe_descriptive` to `- Gate-Summary:` ONLY, and `releases.validate_release` applies it to nothing, so the field each tree actually surfaces to a human and to an agent is unchecked. Measured in this lane: a 900-character `- Scope:` and a `- Scope:` containing ANSI escape bytes each pass `aw specs check` clean, and the ANSI case reaches a terminal RAW through `aw attention --details --no-color` while `aw attention --format json` still reports `"valid": true`. That violates Section 8.8's "the renderers never emit raw control characters". The release half is the same defect through a different field: measured at review, `releases.parse_release` resolves a record's summary to its `## Summary` PROSE paragraph when no `- Summary:` bullet exists (which is every committed record), and an ANSI-bearing prose summary reaches `aw releases show` and `aw releases list` raw at zero checker drift. Two COMMITTED specs already carry an over-length `- Scope:` (366 and 314 characters), which is why this needs a deliberate decision about the existing population rather than only a new rule.
- Scope: Judge the descriptive field each tree actually surfaces under the catalogued `attention.unsafe-field` id: `- Scope:`/`- Summary:` in `specs.validate_spec`, the effective summary in `releases.validate_release`. Register the id; repair the two committed violations rather than grandfathering.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/releases.py, agent_workflows/check_engine.py, tests/test_specs_releases_unsafe_field.py, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: qbz8i1
- Blocks-Release: next
- Set: qbz8i1
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ynhst5
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901 (HIGH, fixed), PR-902 (MEDIUM, fixed), PR-903 (MEDIUM, fixed), PR-904 (LOW, fixed), PR-905 (LOW, fixed), PR-906 (LOW, fixed). All eleven authored findings re-driven at HEAD `009ae490` and all reproduce; three new findings DRIVEN at review (F-12, F-13, F-14) and folded into the plan. PR-901 rewrote E-03: the release rule judged the `- Summary:` BULLET only, and `releases.parse_release` resolves a record's summary to the `## Summary` PROSE paragraph when no bullet exists, which is every committed record, so the authored rule had ZERO coverage of the live tree while claiming `aw check releases` stayed clean. E-03 now judges the effective summary with split strictness (full predicate on the bullet, control characters only on the prose), because the one committed record's effective summary is 457 characters and a length bound would fail a clean checkout at `error`. New OQ-04 records that decision and its three rejected alternatives. Full findings and decisions: `.aw/records/reviews/20260930-qbz8i1-03-ynhst5-give-the-specs-and-releases-checkers-the-unsafe-descriptive.review.md`.
- 2026-09-30 reviewed (aw set): status set to reviewed
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `qbz8i1`, which names this half explicitly ("Closing the specs half therefore needs a new checker rule as well as a write-path guard, which is new policy and is why dtg7dz declined to fold it in"). Measured that it needs NO new rule id, because `attention.unsafe-field` is already in the closed `RULE_IDS` catalog and already used by `specs.validate_spec` for `Gate-Summary`, so the change is widening an existing rule's field coverage rather than minting policy. Also censused the whole population and found exactly two violations, which changed the design from grandfathering to fixing them.
- 2026-09-29 draft (opencode): created.

## Goal

Make the specs and releases checkers judge the descriptive fields those trees actually render, so an over-length or control-character value is a named finding rather than silently valid text that reaches a human terminal unescaped. Close the part of the trust boundary a checker CAN close, and state plainly the part it cannot.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: repair the existing population FIRST

- [x] E-01 Shorten the `- Scope:` value of the two committed specs that violate the bound, BEFORE any rule exists, so the tree is clean when the rule lands and the rule can ship fail-closed with no grandfather tier. The two are `20260730-2152-01-agents-artifact-organization.spec.md` (366 characters, `- Status: implemented`) and `20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md` (314, `- Status: approved`). Reduce each to at most `A.MAX_DESCRIPTIVE_LEN` (300) while preserving its meaning.
  THIS ORDERING IS THE WHOLE REASON THIS IS ITEM ONE, AND THERE ARE TWO INDEPENDENT REASONS FOR IT. FIRST, CI: if the rule landed first, `aw check specs` would exit 1 on a clean checkout and fail CI, forcing either a grandfather tier (added complexity, and a permanent excuse) or a same-commit fix (which mixes a records edit with a code change in one diff a reviewer cannot separate). SECOND, LIFECYCLE DEADLOCK: `specs.run_set` re-runs `validate_spec` on the prospective text and refuses a nonconforming result, so after E-02 neither of these two specs could be transitioned through `aw specs set` at all until its `- Scope:` was hand-shortened; the `approved` one is a live artifact a run may need to move. Fixing first makes the rule's arrival a no-op on the tree, which is also the evidence V-05 demands.
  EDIT THESE TWO FILES BY HAND, NOT THROUGH `aw specs set`. This is a text repair to one metadata line, not a status transition, and the setter's job is transitions; pointing it at a conformance repair would append a spurious `## Workflow history` record asserting a lifecycle event that did not occur. `aw commit ynhst5 -- <the two spec paths>` is still the commit route.
  DO NOT DELETE INFORMATION TO MEET THE BOUND. A `- Scope:` line is a summary of a spec whose body states the detail, so compress the summary; if a value genuinely cannot be said in 300 characters, that is an argument to reconsider the bound (OQ-02), not to truncate the meaning. Neither of these two needs that: both currently pack two sentences into the field. Do NOT edit any other part of either spec, and specifically do NOT touch the `implemented` spec's `- Status:` or history; a records repair is not a lifecycle transition.
  - Depends on: none
  - Expected outcome: both `- Scope:` values are at most 300 characters and still describe the same scope; `python3 -c` over the whole specs tree reports ZERO values failing `A.is_safe_descriptive`, where it reported 2 before.
  - Execution state: performed

### Task group 2: widen the rule's field coverage

- [x] E-02 In `specs.validate_spec`, judge `- Scope:` and `- Summary:` with `A.is_safe_descriptive` and report the EXISTING `attention.unsafe-field` rule id on failure, alongside the `Gate-Summary` check already there. Read the values from the METADATA REGION ONLY, using whatever bounded reader the function already uses for its other bullets, so a `- Scope:` shown as an EXAMPLE inside the spec body is not judged as metadata.
  THE METADATA-REGION BOUND IS NOT OPTIONAL AND HAS A TEST THAT WILL CATCH ITS ABSENCE. `tests/test_specs_verbs.py::test_body_gate_example_is_not_a_real_gate` pins exactly this property for gate bullets, with the comment "only the metadata block (before the first `## `) counts", and specs in this repository routinely quote metadata bullets inside their own prose. An unbounded regex over the whole document would flag those quotations.
  DO NOT MINT A NEW RULE ID. `attention.unsafe-field` is already a member of the closed `attention_contract.RULE_IDS` catalog, is already documented there as covering "control-char / over-length / newline / non-http issue url", and is already emitted by this same function for `Gate-Summary`. Adding a `spec.summary-unsafe` sibling would fork the vocabulary for one tree; `tests/test_attention_contract.py` also asserts the catalog's membership and minimum size, so a new id is a catalog change this plan does not need.
  THE BLAST RADIUS IS WIDER THAN `aw check`, and an executor must know it before running E-02 rather than discovering it from a refusal. `validate_spec` has FOUR consumers: `check_engine` (via `aw check specs`), `specs.run_check` (via `aw specs check`), `attention._spec_record` (so a drift becomes an `aw attention` violation and the item is DROPPED from the view), and `runner_shared`'s run pre-flight (which reports `[RUN-STRUCTURE-PREFLIGHT] spec <id6> ... violates <rule>` and blocks the spec's dispatch). On top of that, `specs.run_set` and `specs.run_migrate` each re-run `validate_spec` on the PROSPECTIVE text and REFUSE a nonconforming result byte-identically. Driven at review: a spec with a 400-character `- Scope:` validates clean today, so `aw specs set` accepts it; after E-02 that same spec cannot be TRANSITIONED AT ALL until its `- Scope:` is hand-shortened, because the residual check refuses on a pre-existing nonconformity that has nothing to do with the flag being set. This is correct fail-closed behavior and it is the second, independent reason E-01 must precede the rule (the first being CI): a spec the new rule rejects cannot be moved through its own lifecycle to fix itself.
  Keep the drift DETAIL escaped through `A.escape_detail`, as the neighbouring gate drifts in this function already do, and do NOT include the offending value itself in the detail: the value is the untrusted text, and echoing it into a `location<TAB>rule<TAB>detail` record would push the injection into the agent surface the rule exists to protect.
  STATE THE RESIDUAL HOLE THE METADATA BOUND LEAVES, so the plan's own limit is recorded rather than discovered later. `attention._extract_detail` searches the WHOLE document (`(?mi)^-\s*Scope:\s*(.+)$` with no metadata bound) and cascades `Summary -> Scope -> Concern -> Question -> Title -> H1`. Driven at review: a spec with NO metadata `- Scope:` but a body `- Scope: red\x1b[31mINJECTED\x1b[0m` after a `## ` heading has `validate_spec == []`, `_extract_detail` returns that ANSI value, `aw attention --details --no-color` emits the literal escape bytes, and `aw attention --format json` reports `"valid": true`. The same holds for an ANSI-bearing `# ` H1 when the cascade falls through to `title`. THIS IS NOT A REASON TO DROP THE METADATA BOUND (F-11 and `test_body_gate_example_is_not_a_real_gate` make the bound correct: a quoted example is not metadata, and judging body prose would produce false findings on documentary quotations). It is a reason to state that the CHECKER and the RENDERER read different regions, which is a renderer-side divergence carried by `llnvwj` (the escaping half of Section 8.8), not a defect in the bounded read this item specifies. Record it in the item's comment so the next reader does not conclude the checker covers the renderer's input set.
  - Depends on: E-01
  - Expected outcome: a spec whose `- Scope:` is 301 characters, or contains a BEL or an ANSI ESC, yields exactly one `attention.unsafe-field` drift from `validate_spec`, while a spec quoting `- Scope:` inside its body after a `## ` heading yields none; and `test_body_gate_example_is_not_a_real_gate` still passes.
  - Execution state: performed

- [x] E-03 In `releases.validate_release`, judge the release's EFFECTIVE summary (the value `releases.parse_release` actually resolves, which is the `- Summary:` bullet when present ELSE the `## Summary` prose paragraph) with the `attention.unsafe-field` id, applying the FULL predicate to the bullet form and a CONTROL-CHARACTER-ONLY (line-integrity) check to the prose form. The module currently imports no `attention_contract`, so add that import; it validates only `- Id:`, `- Status:` and `- Version:` today.
  JUDGE WHAT THE RENDERERS ACTUALLY EMIT, NOT ONLY THE BULLET, and this is a correction to the authored item rather than a widening of it. Driven at review: on the ONE committed release record, `releases.parse_release(...).summary` resolves to the 457-character `## Summary` PROSE paragraph, and `aw releases show`/`aw releases list` print that value on the `Summary:` line. So a bullet-only rule has ZERO coverage of the live release tree, which makes its Expected outcome ("`aw check releases` stays clean") true for the wrong reason: nothing is checked at all. Driven with an ANSI-bearing prose summary, `aw releases show aaaaaa` emitted the literal bytes `Summary: red\x1b[31mINJECTED\x1b[0m` while `validate_release` returned `[]`, which is exactly the Section 8.8 violation ("The renderers never emit raw control characters") this plan exists to make a named finding.
  THE TWO FORMS GET DIFFERENT STRICTNESS FOR A MEASURED REASON, NOT AS A COMPROMISE. The 300-character bound is right for a one-line bullet a writer chose to make one line. It is WRONG for a prose paragraph: the one committed record's effective summary is 457 characters and control-char-free, so applying the full predicate to the prose form would fail `aw check releases` on the clean tree at `error` severity and reintroduce exactly the grandfather-tier problem OQ-01 resolved by cleaning the specs tree first. Line integrity alone (`A._CONTROL_CHAR_RE`) fires on zero committed records while still closing the escape-injection vector the renderers expose. Apply the control-char test to the COLLAPSED one-line value `_summary_section` returns (it already joins the paragraph's lines with spaces, so an embedded newline is structurally impossible there and is not a vector to test for).
  EMIT ONE DRIFT, NOT TWO, and make the DETAIL name which form was judged, since the two carry different bounds and a reader must be able to tell a length failure on a bullet from a control-character failure in prose without opening the file. Keep the detail value-free per OQ-03.
  - Depends on: E-02
  - Expected outcome: a release record whose `- Summary:` BULLET is over-length or control-char-bearing yields exactly one `attention.unsafe-field` drift; a record whose `## Summary` PROSE contains a control character yields exactly one `attention.unsafe-field` drift naming the prose form; the committed `2.0.0` record (457-character control-char-free prose) yields NONE and `aw check releases` exit code stays 0; and a 400-character prose summary also yields none, proving the prose form is deliberately unbounded in length.
  - Execution state: performed

- [x] E-04 Register `attention.unsafe-field` in `check_engine.RULE_REGISTRY` at severity `error`, assurance `ASSURANCE_REPOSITORY`, determinism `DET_DETERMINISTIC`, with a comment stating why each value was chosen and why registration is not bookkeeping.
  REGISTRATION CHANGES NOTHING ABOUT THE EXIT CODE TODAY AND IS STILL REQUIRED, which is the subtlety to record in the comment: an unregistered id falls through to `_DEFAULT_RULESPEC`, which is already `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`, so the observable severity is identical. What registration buys is that the severity becomes DECLARED rather than inherited, so a future change to the default cannot silently reclassify this rule. The in-repo precedent for making exactly this reasoning explicit is the `check.stale-index-missing` / `check.stale-index-stale` pair, whose comment records that an unregistered rule "silently did" fall through to the default.
  `error` IS CORRECT AND THE ALTERNATIVE WAS CONSIDERED: `drift_exit_code` exempts ONLY `info`, so `info` would make the rule advisory and non-failing, and the governing spec's F10 states these violations ARE failures ("violations of any of these are stable named `--check` failures"). E-01 having already cleaned the tree means `error` costs nothing on a clean checkout, which is the condition that makes a grandfather tier unnecessary here and distinguishes this case from `check.ipd-uncarried-obligation`, which needed one because 106 plans were non-conforming.
  Leave the `invariant` field EMPTY rather than guessing an id: the Phase-0 catalog invariant this maps to is Section 8.8's output-safety property, and no existing registry entry claims it, so inventing a mapping would be a false trace. Say so in the comment, as the `stale-index` entries do with their own empty invariants.
  - Depends on: E-03
  - Expected outcome: `check_engine.rulespec("attention.unsafe-field")` (or the registry lookup the module exposes) returns the declared `RuleSpec` rather than `_DEFAULT_RULESPEC`, with `severity == "error"`, and `aw check specs` / `aw check releases` exit codes are unchanged on a clean tree.
  - Execution state: performed

### Task group 3: pin the coverage and the honest limit

- [x] E-05 Add `tests/test_specs_releases_unsafe_field.py` pinning the new coverage for all four Section 8.8 shapes that a checker CAN see (over-length, BEL, ANSI ESC, and a C1 control), on `- Scope:` and `- Summary:` for specs and on the release BULLET form, each asserting exactly the `attention.unsafe-field` id; plus the release PROSE form, which takes CONTROL-CHARACTER cases only (the three control shapes flag; a 400-character prose summary does NOT, which is the assertion that pins E-03's deliberate length asymmetry). Follow the established fixture-driven template `test_each_violation_fixture_flags` in `tests/test_specs_verbs.py`, which maps a fixture filename to an expected rule id, and the existing `tests/fixtures/attnview/violations/unsafe-field.md` fixture, which already pins this id for `Gate-Summary`.
  THE TEST MUST PIN TWO LIMITS, and this is the part that keeps the record honest. FIRST, the NEWLINE limit: assert that a spec whose `- Scope:` was produced by NEWLINE INJECTION (a safe `- Scope: legit` line followed by a smuggled `- Blocks-Release: next` bullet) yields NO `attention.unsafe-field` drift, with a comment naming F-05 and pointing at Order 01 as the only place that vector can be closed. SECOND, the READ-REGION limit (F-14): assert that a spec with NO metadata `- Scope:` but an ANSI-bearing `- Scope:` in its BODY yields NO drift from `validate_spec` WHILE `attention._extract_detail` on the same text returns that ANSI value, with a comment naming `llnvwj` as the carrier. That second assertion is a two-sided pin and is the point: it proves the checker is correct (the bound is deliberate, F-11) and simultaneously proves the renderer's input set is wider, so no later reader concludes from this module that `aw attention` is safe. A reader must not be able to conclude from this test module that the checker closed either injection.
  TEST OUTCOMES, NOT CODE STRUCTURE (AGENTS.md, GUIDING_PRINCIPLES P16). Every assertion here drives `validate_spec`, `validate_release`, `_extract_detail` or a CLI and asserts on returned drift, exit codes or emitted bytes. Do NOT assert on `inspect.getsource`, a call count, a symbol census, or the presence of any comment or docstring; specifically, the E-04 registry assertion must read `check_engine.rule_spec("attention.unsafe-field")` and compare the returned `RuleSpec` fields, never grep the module text for the entry.
  Non-regressions: the `Gate-Summary` case still flags (the existing fixture must keep passing); the metadata-region bound holds (a body-quoted `- Scope:` does not flag); every spec in `tests/fixtures/attnview/specs-valid/` still validates clean; the ACTUAL committed `2.0.0` release record validates clean through `validate_release` (a live-artifact assertion, so it must read the record from the repository rather than hard-coding its 457-character length); and the registry entry is asserted to exist with severity `error` rather than assumed.
  - Depends on: E-04
  - Expected outcome: a new module whose over-length and control-character cases FAIL against pre-E-02/E-03 code (`validate_spec` and `validate_release` both return `[]`) and PASS after; whose two LIMIT cases (newline injection, body-region read) pass in BOTH states, documenting what is not closed; and whose non-regression cases pass in both.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE RULE ID ALREADY EXISTS, so this is field-coverage widening and not new policy, which is a material correction to the backlog item's framing ("needs a new checker rule ... which is new policy"). `attention.unsafe-field` is a member of `attention_contract.RULE_IDS`, documented there as "control-char / over-length / newline / non-http issue url", and `specs.validate_spec` already emits it for `Gate-Summary`.
- THE CLOSED CATALOG IS PINNED BY A TEST, so minting a sibling id is not a free choice: `tests/test_attention_contract.py` iterates `A.RULE_IDS` and asserts specific members plus a minimum size. The catalog's own comment states that consumers "MUST use these ids; they do NOT free-hand new ones".
- THE METADATA-REGION BOUND IS AN ESTABLISHED, TESTED PROPERTY of this validator: `test_body_gate_example_is_not_a_real_gate` asserts that gate bullets shown as an example after a `## ` heading are not read as real metadata. Any new field read must respect the same bound or that test's sibling property breaks for `- Scope:`.
- AN UNREGISTERED RULE ID ALREADY BEHAVES AS `error`, because `_DEFAULT_RULESPEC` is `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`. So E-04 is about making the severity DECLARED, not about changing behavior; the `check.stale-index-*` entries record exactly this reasoning for their own case.
- `drift_exit_code` EXEMPTS ONLY `info`, measured in its own source ("an `info`-severity finding is ADVISORY ... only error/warning-class findings drive the nonzero exit"). So a `warning` tier is NOT advisory here and `info` is the only non-failing severity, which is what makes the E-01-first ordering necessary rather than optional.
- THE GOVERNING SPEC ALREADY REQUIRES THIS, so no spec amendment is needed. Spec `attention-registry-and-cross-tree-status` Section 8.8 requires bounded single-line control-char-free descriptive fields; F10 makes violations "stable named `--check` failures"; A14 requires "hostile-string fixtures" for a newline, an ANSI/control character, a Markdown-table-breaking string and an over-length value, which E-05 supplies for these two trees.
- `releases.py` DELIBERATELY HAS NO `check` VERB, and its module docstring says so ("There is deliberately NO `run_check`: `aw check releases` already validates release records through `check_engine` -> `validate_release`"). So E-03's change reaches users through `aw check releases` and must not add a second entry point.
- A RELEASE'S SUMMARY IS RESOLVED BY A FALLBACK, and `parse_release` is the authority on which form wins: `msum = _SUMMARY_RE.search(text)` first, then `if not summary: summary = _summary_section(text)`. `_summary_section` COLLAPSES the paragraph ("collapsed to one line", joining with spaces), which is why E-03's prose check needs no newline test. `ReleaseRecord.summary` is what `run_show` prints on its `Summary:` line and what `run_list` puts in its table column, so the resolved value, not the bullet, is the field with a human surface.
- `validate_release` EMITS `str(path)` AS ITS DRIFT LOCATION while `validate_spec` routes through `specs.drift_location` to a repo-relative POSIX path, for the reason that function's own docstring records (Section 8.5 "forbids an absolute path on any output surface"). `check_engine._iter_type_files` passes ABSOLUTE paths to both. The absolute value does not currently reach a user because `check_engine.finding_dict` relativizes against `repo_root` before serializing, so this is a latent asymmetry rather than a live leak, and it is NOT this plan's to fix: E-03 adds a drift to a function whose location handling it inherits unchanged. Recorded so an executor does not "helpfully" change the location shape while adding a rule, which would be an undeclared behavior change to three existing drifts.
- BOTH VALIDATORS ARE ALSO CALLED BY THE RUNNER'S PRE-FLIGHT, not only by `aw check`: `runner_shared` validates a queued spec with `specs.validate_spec` and reports `[RUN-STRUCTURE-PREFLIGHT] ... violates {d.rule}` for any non-`info` drift, and `specs.run_set`/`run_migrate` re-run `validate_spec` in memory and REFUSE a result that would not conform. So widening the rule makes an over-length or control-char `- Scope:` refuse a `aw specs set` and block a spec from being dispatched by `aw oc run`. That is the correct behavior and it is a wider blast radius than `aw check` alone; it is also why E-01 must land first (a spec the new rule rejects could not be transitioned to fix it).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `aw check plans` REPORTS ONE ADVISORY AGAINST THIS PLAN AND IT MUST NOT BE "FIXED". `check.plan-spec-link-missing` fires with `Fix: aw ipd set ynhst5 --from-spec r07vma`, because the rule nudges any PENDING plan citing a resolvable spec id6 while carrying no `- From-Spec:`, and this plan's `- Scope-Paths:` legitimately names `r07vma`'s file as an E-01 RECORDS REPAIR target. DO NOT run that command: this plan did not graduate from `r07vma`, and writing the link would assert a spec-to-plan handoff that never happened. The rule is registered `info` precisely for this case, and its own comment records why ("citing a spec as a constraint does not necessarily mean graduating from it"); `drift_exit_code` exempts `info`, so it drives no exit code. Verified pre-existing at review: the advisory fires on the plan as authored, before any review edit.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'` (AGENTS.md).

## Findings

F-01 through F-11 were DRIVEN by the AUTHORING lane at HEAD `f4b00263`: the census figures over the real records trees, the behavioral ones against temporary fixture repositories. F-12 through F-14 were DRIVEN by `/plan-review` at HEAD `009ae490` and each CHANGED an item, so they are recorded here rather than only in the review record. Every authored finding was RE-DRIVEN at review and all reproduce, with two corrections noted in place (F-09's registry entry count and F-11's body-quotation population, both live counts rather than the claims they support).

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
| F-09 | AN UNREGISTERED ID ALREADY RESOLVES TO `error`, so E-04 changes no exit code and its value is purely that the severity stops being inherited. | Driven: `'attention.unsafe-field' in check_engine.RULE_REGISTRY` is **False**, while `_DEFAULT_RULESPEC` is `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`. So the rule already behaves as an error today wherever it fires. THE REGISTRY SIZE IS A LIVE COUNT AND IS NOT THE CLAIM: 52 entries measured at authoring HEAD `f4b00263`, 56 at review HEAD `009ae490` (both re-derived at review; the authored figure was correct at its own HEAD). The DURABLE claim is the ABSENCE of this one id plus the default's severity, which are both properties rather than counts. Do not treat any entry count as an acceptance bar. |
| F-10 | NO TEST PINS DESCRIPTIVE SAFETY FOR `- Scope:` OR A RELEASE `- Summary:`; the only coverage is the `Gate-Summary` fixture. | `grep -rn "unsafe-field" tests/` matches `tests/test_attention_contract.py` (catalog membership plus a `Gate-Summary` fixture) and `tests/test_specs_verbs.py` (the fixture-to-rule map). The fixture `tests/fixtures/attnview/violations/unsafe-field.md` carries an over-length `- Gate-Summary:` and nothing else. |
| F-11 | THE METADATA-REGION BOUND MATTERS IN PRACTICE, not just in principle, because specs here quote metadata bullets in their own prose. An unbounded read would produce false findings. | `tests/test_specs_verbs.py::test_body_gate_example_is_not_a_real_gate` exists precisely for this, asserting that a spec showing `- Status: deferred` and `- Gate-*` bullets inside a fenced example after a `## ` heading yields `[]`. THE PRECISE SHAPE, re-derived at review because the authored wording overstated it: the LIVE quoted population is `- Status:` 36, `- Gate-Kind:`/`- Gate-Ref:`/`- Gate-Summary:` 1 each, and `- Scope:`/`- Summary:` **0**, so no committed spec quotes a `- Scope:` bullet in body prose TODAY. The bound is still required, because the one spec quoting `- Gate-Summary:` in its body proves the documentary practice is live and would extend to `- Scope:` the moment a spec documents the field, and because the cited test pins the property for the sibling bullets. |
| F-12 | THE RELEASE TREE'S EFFECTIVE SUMMARY IS THE PROSE FORM, so a bullet-only rule has ZERO coverage of the live tree and the authored E-03's "stays clean" outcome was true for the wrong reason. Driven at review; this is what changed E-03. | Driven: `releases.parse_release` on the ONE committed record resolves `summary` to the 457-character `## Summary` prose paragraph (`is_safe_descriptive` **False** on length, control chars **0**, newlines **0**, because `_summary_section` collapses the paragraph to one line). `- Summary:` bullets in the whole release tree: **0**. So the authored rule would have fired on nothing. With an ANSI-bearing prose summary, `aw releases show aaaaaa` printed the literal bytes `Summary: red\x1b[31mINJECTED\x1b[0m` and `aw releases list` the same, while `validate_release` returned `[]`. |
| F-13 | THE FULL PREDICATE ON THE PROSE FORM WOULD FAIL THE CLEAN TREE, which is why E-03 splits strictness rather than applying one rule. | Driven: `A.is_safe_descriptive` on the committed record's 457-character effective summary returns **False** on LENGTH alone. At `error` severity (E-04) that exits 1 on a clean checkout, reintroducing the exact grandfather-tier problem OQ-01 avoided by cleaning the specs tree first. A control-character-only test on the same value passes, and fires on zero committed records, while still closing the measured renderer vector in F-12. |
| F-14 | THE CHECKER AND THE RENDERER READ DIFFERENT REGIONS, so the metadata-bounded read this plan specifies does NOT cover the renderer's input set. Recorded as an honest limit, not repaired here. | Driven: `attention._extract_detail` searches the WHOLE document (`(?mi)^-\s*Scope:\s*(.+)$`, no metadata bound) and cascades `Summary -> Scope -> Concern -> Question -> Title -> H1`. A spec with no metadata `- Scope:` but a body `- Scope: red\x1b[31mINJECTED\x1b[0m` after a `## ` heading yields `validate_spec == []`, `_extract_detail == ('scope', 'red\x1b[31mINJECTED\x1b[0m')`, raw escape bytes in `aw attention --details --no-color`, and `"valid": true` in `--format json`. Same for an ANSI `# ` H1 reaching the `title` fallback (`title: 9.9.9\x1b[31mINJ\x1b[0m` observed on a release). Live cascade census over the 38 specs: `scope` 21, `title` 16, `summary` 1, zero unsafe. |

## Proposed changes (ordered, validatable)

1. E-01: shorten the two over-length committed `- Scope:` values (F-06, F-07), so the tree is clean before any rule exists and no grandfather tier is needed.
2. E-02: judge `- Scope:` and `- Summary:` in `specs.validate_spec` with the existing `attention.unsafe-field` id, read from the metadata region only, with the detail escaped and the offending value NOT echoed.
3. E-03: judge the release's EFFECTIVE summary in `releases.validate_release` with the same id: the full predicate on the `- Summary:` bullet, line integrity only on the `## Summary` prose form, because the prose form is what the one committed record actually surfaces and a length bound on it would fail the clean tree (F-12, F-13, OQ-04).
4. E-04: register the id in `RULE_REGISTRY` at `error` with an empty invariant and a comment recording why registration matters despite not changing today's behavior (F-09).
5. E-05: pin the four checker-visible shapes on the specs fields and the release bullet, pin control characters only on the release prose form plus a 400-character prose case that must NOT flag, pin BOTH limits explicitly (the NEWLINE vector F-05 and the READ-REGION divergence F-14), and keep the existing `Gate-Summary` fixture and metadata-region properties green.

## Deferred / out of scope (with reason)

- THE NEWLINE INJECTION VECTOR IS NOT CLOSED BY THIS PLAN AND CANNOT BE. F-05 measured why: the value is split into separate lines before any checker sees it, so the predicate is handed only the safe half and correctly passes. This is the single most important limit of this plan and E-05 pins it as a test so the record cannot later be misread as having closed it.
  - Carrier: uz05bl
  - Carrier-Evidence: .aw/records/plans/executed/20260929-qbz8i1-01-uz05bl-refuse-an-unsafe-descriptive-value-at-every-specs-and-releas.ipd.md
- HISTORY-RECORD MESSAGES ARE NOT BOUNDED by this plan, on either tree. Measured over the specs tree: 59 of 146 committed history messages exceed 300 characters, median 235, max 2594, and 0 contain a control character. So bounding them would make `aw check specs` fail on 40.4 percent of the tree's own history, and no checker anywhere in this repository bounds a history message. A LINE-INTEGRITY rule for them (control characters only, no length) would be measurably safe, but it is a new policy for a different field class than the one this plan is scoped to.
  - Carrier-Declined: Nothing is owed, because no measured harm survives unowned: the WRITE-PATH half of history-message safety, which is where the forgery vector actually enters, is closed for these two trees by Order 01 (`uz05bl` E-03) and for the shared positional setter by `nw9dmz`. What a checker rule would additionally catch is a HAND-EDITED control character in a history line, for which this census found zero instances across 146 records and which no measurement here shows causing harm. Filing a carrier would schedule a new field-class policy on the strength of no evidence.
- THE MARKDOWN-ESCAPING HALF OF SECTION 8.8 IS NOT IMPLEMENTED. The spec requires that "The Markdown board escapes Markdown metacharacters deterministically so a field cannot break the table, inject a link/image, or start a new block", and this plan adds no escaping to any renderer; it only makes over-length and control-character values a named finding. A pipe character in a `- Scope:` can still break a rendered table.
  - Carrier: llnvwj
- THE CHECKER'S READ REGION IS NARROWER THAN THE RENDERER'S, so a control character can still reach `aw attention` through a path this plan's metadata-bounded read cannot see. F-14 measured both vectors: a BODY `- Scope:` bullet (the renderer's regex is unbounded; the checker's is bounded at the first `## `) and an ANSI-bearing `# ` H1 reaching the cascade's `title` fallback. Narrowing the CHECKER is not the fix (F-11: judging body prose would flag documentary quotations, and `test_body_gate_example_is_not_a_real_gate` pins that property), so the correct closure is renderer-side: the renderer should sanitize or refuse what it emits rather than trusting a validator that reads a different region.
  - Carrier: llnvwj
  - Carrier-Note: this is the SAME renderer-side obligation as the Markdown row above and belongs to the same carrier, whose own text already names "WHICH surfaces escape" as one of the two undecided questions and explicitly records that `A.escape_detail` does NOT touch C0/C1 controls. That item is `- Priority: low`/`- Work-Kind: chore` on the reasoning that its measured payload (a pipe) has no demonstrated user-visible breakage; the ANSI vector measured here is STRONGER than that (raw escape bytes do reach a terminal, which Section 8.8 forbids outright), so whoever triages `llnvwj` should re-judge its priority against this evidence rather than inheriting the pipe-only assessment. Flagged rather than re-prioritized here, because a reviewer editing another tree's item is outside this plan's fence.
- ANY NEW RULE ID (for example a `spec.summary-unsafe` mirroring `backlog.summary-unsafe`) IS DELIBERATELY NOT MINTED, so the two trees report the SAME finding under different ids (`backlog.summary-unsafe` on backlog, `attention.unsafe-field` here). That asymmetry is pre-existing and this plan preserves rather than resolves it.
  - Carrier-Declined: Nothing is owed because the current state is correct rather than deferred: `attention.unsafe-field` is the id the closed `RULE_IDS` catalog already designates for this violation class, the catalog's own comment forbids free-handing new ids, and `tests/test_attention_contract.py` pins the catalog. Minting a specs-specific sibling would fork the vocabulary to make two trees look symmetrical, which is a cosmetic gain traded against the single-vocabulary property the catalog exists to enforce. The backlog tree's differently-named id predates the catalog's use here and renaming it is a separate compatibility question no finding in this plan raises.
- WIDENING THE SAME CHECK TO OTHER TREES (`research`, `prompts`, `walkthroughs`, `roadmaps`) is out of scope. Each has its own front-matter dialect (research is YAML, prompts is an HTML comment), its own field names, and its own validator, so a sweep would be several unrelated validator changes in one commit.
  - Carrier: 7w6zsl

## Scope check

- Over-scope: none. Two field reads added to one validator, one effective-summary read added to a second, one registry entry, one new test module, and two one-line records repairs. No new rule id, no change to `is_safe_descriptive` or `MAX_DESCRIPTIVE_LEN`, no change to any renderer, no change to `RULE_IDS`, no new command, and no change to any write path (Order 01 owns those).
- Under-scope, stated in full because this plan closes only what a checker can reach: (a) the NEWLINE vector stays open at the checker and is closed only by Order 01, which is the plan's defining limit (F-05); (b) history-record messages stay unbounded and unjudged on both trees; (c) Markdown metacharacter escaping is still unimplemented, so the Section 8.8 renderer obligation is only partly met, carried by `llnvwj`; (d) other records trees keep no descriptive-field rule, carried by `7w6zsl`; (e) a release `## Summary` PROSE section is judged for LINE INTEGRITY ONLY and is deliberately unbounded in LENGTH, because the one committed record's effective summary is 457 characters and a length bound would fail the clean tree at `error` (F-12, F-13, OQ-04); (f) the backlog tree keeps its differently-named `backlog.summary-unsafe` id, so the vocabulary stays asymmetric across trees; (g) the checker's metadata-bounded read is narrower than the renderer's whole-document read, so a body `- Scope:` bullet or an ANSI `# ` H1 still reaches `aw attention` raw, carried by `llnvwj` (F-14).

## Required tests / validation

- `python3 -m pytest tests/test_specs_releases_unsafe_field.py` for the new module (run bare; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`).
- `python3 -m pytest tests/test_specs_verbs.py tests/test_attention_contract.py tests/test_releases.py tests/test_releases_cli.py tests/test_check_engine_spec_criteria.py tests/test_doctor.py` as the targeted regression set: these own the validator being widened, the closed rule catalog and its `Gate-Summary` fixture, the release validator, and the doctor's rule-to-remediation table which keys on rule ids.
- `python3 -m pytest` (full fast suite) to prove no order-dependent or cross-module regression.
- `aw specs check --agent`, `aw check specs --agent`, `aw check releases --agent` and `aw check all` must add NO `attention.unsafe-field` finding and change no EXIT CODE on the repository tree AFTER E-01, which is the evidence that shipping at `error` needs no grandfather tier. THE BAR IS AN EXIT CODE AND A RULE SET, NOT A COUNT: `aw check specs`/`aw check releases` each already emit one pre-existing `check.collisions-not-checked` advisory at exit 0, and `aw check all` already exits 1 with 59 unrelated plans-tree findings (both measured at review HEAD `009ae490`). Re-derive every figure at execution; see V-05 for the full baseline.
- PRE-FIX FALSIFICATION IS REQUIRED ON BOTH VALIDATORS: V-05 must show the over-length and control-character cases FAILING against pre-fix code with `validate_spec` AND `validate_release` returning `[]`, including the release PROSE case, whose pre-fix counterpart is what distinguishes the corrected E-03 from the authored bullet-only version (F-12). Obtain that run by authoring the test module first, or against a separate `git worktree` at HEAD; do NOT `git stash push -- agent_workflows/specs.py`, since this checkout is shared and stashing a path can swallow a co-worker's uncommitted edit.
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
- Resolution or deferral rationale: RESOLVED: yes, keep 300, and do not touch the constant. 20 of 22 committed `- Scope:` values already fit (median 171.5, re-derived unchanged at review), so the bound is empirically livable rather than aspirational, and both exceptions are two-sentence values whose second sentence belongs in the body (F-07). The constant is also SHARED: `A.MAX_DESCRIPTIVE_LEN` governs backlog summaries, gate refs, gate summaries and evidence citations across every tree, and `backlog.validate_item` already enforces it with ZERO `backlog.summary-unsafe` findings across the whole tree (763 items at review HEAD `009ae490`; the plan authored 674, a live count that grows and is not the claim), so raising it to accommodate two spec lines would loosen a contract five trees currently satisfy. NON-BLOCKING because nothing in this plan depends on the number: E-02 asks the predicate for a verdict and never reads the constant, so a future decision to change the bound needs no change here. If a reviewer disagrees, the right move is a separate change to the shared constant with its own cross-tree measurement, not a spec-tree exemption.

### OQ-04: Should the release `## Summary` PROSE form be judged, and if so by the same bound as the bullet?

- Blocking: no
- Status: resolved
- Owner: plan-review (reviewer's own judgement; recorded as decision D-1 in the review record)
- Resolution or deferral rationale: RESOLVED AT REVIEW, and it CHANGED E-03. YES judge it, and NO not by the same bound: full predicate on the bullet, control characters only on the prose. The authored plan judged the bullet alone on the reasoning that "a prose section is a body, not a descriptive field", which is sound as a category argument and wrong as a description of this code: `releases.parse_release` resolves `summary` to the bullet ELSE the prose paragraph, and `ReleaseRecord.summary` is what `aw releases show`/`aw releases list` print, so the prose form IS the descriptive field for every record that lacks a bullet, which today is ALL of them (F-12: zero `- Summary:` bullets in the tree). A bullet-only rule therefore had zero coverage of the live tree while its Expected outcome claimed `aw check releases` stayed clean, which was true only because nothing was being checked. THE SPLIT STRICTNESS IS FORCED BY MEASUREMENT, not chosen for balance (F-13): the one committed record's effective summary is 457 characters, so the full predicate at `error` severity fails a clean checkout and reintroduces the grandfather-tier problem OQ-01 exists to avoid, while the control-character test fires on zero records and still closes the measured `aw releases show` escape vector. THE ALTERNATIVES REJECTED: (a) bullet-only as authored, rejected because it ships a rule with no live coverage inside a plan whose subject is closing an unchecked surface; (b) full predicate on both, rejected on the 457-character measurement; (c) raise the bound for the prose form, rejected because it forks a shared constant OQ-02 just declined to touch. NON-BLOCKING because the mechanism is fully specified in E-03 and demonstrated on both cases at review, so nothing is left for a human to decide.

### OQ-03: Should the drift detail include the offending value, so a human can see what was wrong?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: no, and the reason is the rule's own purpose. The detail lands in the `location<TAB>rule<TAB>detail` agent record and in human output, so echoing an untrusted over-length or ANSI-bearing value would push the exact payload this rule exists to flag into the surface it exists to protect, and for a control-character value it would emit the raw escape into a terminal even as it reports that doing so is a violation. `A.escape_detail` escapes tab, newline and backslash to keep the record one line, and deliberately does NOT strip C0/C1 controls, so escaping is not sufficient protection. The existing sibling detail is already value-free and descriptive ("Gate-Summary is over-length or has control chars/newlines"), so E-02 follows it. The residue is that a user must open the file to see the offending value, which is acceptable because the finding names the file and the field.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a `git diff` of the two specs showing ONLY the `- Scope:` line changed in each, and paste the before and after character counts for both (before: 366 and 314; after: each at most 300, with the actual numbers). Paste the full before and after text of each value so a reviewer can judge that meaning was preserved rather than truncated. Then paste the output of a census over the WHOLE specs tree showing ZERO `- Scope:`/`- Summary:`/`- Gate-Summary:` values failing `A.is_safe_descriptive`, where it previously reported 2. THIS MUST BE RUN BEFORE E-02 EXISTS: state explicitly that the rule was not yet in the tree when this evidence was captured, since E-01's whole purpose is to precede it. Also confirm from the diff that neither spec's `- Status:` line nor its `## Workflow history` was touched.
  - Observed evidence: PASS. Evidence captured BEFORE E-02 existed in code: the rule was not yet in the tree when this evidence was captured.
    git diff of the two specs showing ONLY the `- Scope:` line changed in each:
    ```diff
    diff --git a/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md b/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    index 221251bc1..c8464204a 100644
    --- a/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    +++ b/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    @@ -5,7 +5,7 @@
     - Id: r07vma
     - Author: opencode/its_direct/pt3-claude-opus-5-1m-us
     - From-Spec: 77tr3o
    -- Scope: An Order-0 orchestrator may hold only child-tracking items; one shared parser enforces AUTHORING CONFORMANCE deterministically, plan-review repairs violations in a bounded loop, and a run re-parses and refuses with every finding at once. ADDITIVE to the existing semantic coverage probe, which it does not replace.
    +- Scope: An Order-0 orchestrator may hold only child-tracking items; one shared parser enforces AUTHORING CONFORMANCE deterministically, plan-review repairs violations in a bounded loop, and a run refuses with all findings at once. ADDITIVE to the existing semantic coverage probe, which it does not replace.
     - Parent: `.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md` (`77tr3o`,
       `approved`), which owns runner-owned retirement. This spec ADDS a deterministic authoring-conformance
       control beside that spec's R-12 semantic probe. It leaves R-1 through R-12 intact and does NOT retire
    diff --git a/.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md b/.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md
    index 912f4a422..33d672080 100644
    --- a/.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md
    +++ b/.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md
    @@ -3,7 +3,7 @@
     - Date: 2026-07-30
     - Status: implemented
     - Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
    -- Scope: a GENERAL principle for organizing the durable, growing artifact trees under `.agents/` (research, plans, prompts, comms, walkthroughs) so a human and an agent can answer "what did we find / decide about X?" and "what still needs attention?" cheaply and at scale. IMPLEMENTATION is scoped to `.agents/docs/research/` first; the other areas are named future adopters.
    +- Scope: A GENERAL principle for organizing durable artifact trees under `.agents/` (research, plans, prompts, comms, walkthroughs) to answer topic and attention queries cheaply at scale. IMPLEMENTATION is scoped to `.agents/docs/research/` first; the other areas are named future adopters.

     This spec is the load-bearing rationale document. It captures the problem, the measured evidence, the full criteria, the chosen design and WHY, the trade-offs considered, and the migration outline, so the follow-on IPD Set can be authored and reviewed against a single source of truth. It deliberately records reasoning, not just conclusions.
    ```
    Confirming from diff: neither spec's `- Status:` line nor its `## Workflow history` was touched.
    Character counts and full text before and after:
    Spec 1 (20260730-2152-01-agents-artifact-organization.spec.md):
      Before count: 366
      Before text:  `a GENERAL principle for organizing the durable, growing artifact trees under `.agents/` (research, plans, prompts, comms, walkthroughs) so a human and an agent can answer "what did we find / decide about X?" and "what still needs attention?" cheaply and at scale. IMPLEMENTATION is scoped to `.agents/docs/research/` first; the other areas are named future adopters.`
      After count:  281
      After text:   `A GENERAL principle for organizing durable artifact trees under `.agents/` (research, plans, prompts, comms, walkthroughs) to answer topic and attention queries cheaply at scale. IMPLEMENTATION is scoped to `.agents/docs/research/` first; the other areas are named future adopters.`

    Spec 2 (20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md):
      Before count: 314
      Before text:  `An Order-0 orchestrator may hold only child-tracking items; one shared parser enforces AUTHORING CONFORMANCE deterministically, plan-review repairs violations in a bounded loop, and a run re-parses and refuses with every finding at once. ADDITIVE to the existing semantic coverage probe, which it does not replace.`
      After count:  299
      After text:   `An Order-0 orchestrator may hold only child-tracking items; one shared parser enforces AUTHORING CONFORMANCE deterministically, plan-review repairs violations in a bounded loop, and a run refuses with all findings at once. ADDITIVE to the existing semantic coverage probe, which it does not replace.`

    Census across the WHOLE specs tree before E-02:
    ```
    Total fields checked: 26
    Failures count: 0
    ```
    (Prior to E-01 repair, failures count was 2).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a Python session calling `specs.validate_spec` on fixtures and showing the returned drift for each: a 301-character `- Scope:` yielding exactly one `attention.unsafe-field`; a `- Scope:` containing BEL yielding the same; one containing ANSI ESC yielding the same; one containing a C1 control yielding the same; a 300-character `- Scope:` yielding `[]` (the boundary); an over-length `- Summary:` yielding the finding. Then paste the METADATA-REGION proof: a spec that quotes `- Scope: <301 chars>` inside a fenced block AFTER a `## ` heading yielding `[]`, plus the passing output of `tests/test_specs_verbs.py::test_body_gate_example_is_not_a_real_gate`. Finally paste the emitted drift's DETAIL string showing it does NOT contain the offending value (OQ-03), and the source showing `A.escape_detail` is applied as the neighbouring gate drifts do.
  - Observed evidence: PASS. Python session calling specs.validate_spec on test cases confirms unsafe-field drifts:
    ```python
    >>> from pathlib import Path
    >>> from agent_workflows import specs
    >>> template = '''# Spec: Sample Spec
    ...
    ... - Date: 2026-08-08
    ... - Status: draft
    ... - Author: test
    ... {meta}
    ...
    ... ## Workflow history
    ... - 2026-08-08 draft (test): created.
    ... {body}
    ... '''
    >>> specs.validate_spec(Path('tests/s.md'), template.format(meta='- Scope: ' + ('x' * 301), body=''))
    [Drift(location='tests/s.md', rule='attention.unsafe-field', detail='Scope is over-length or has control chars/newlines')]
    >>> specs.validate_spec(Path('tests/s.md'), template.format(meta='- Scope: scope\x07value', body=''))
    [Drift(location='tests/s.md', rule='attention.unsafe-field', detail='Scope is over-length or has control chars/newlines')]
    >>> specs.validate_spec(Path('tests/s.md'), template.format(meta='- Scope: scope\x1b[31minjected\x1b[0m', body=''))
    [Drift(location='tests/s.md', rule='attention.unsafe-field', detail='Scope is over-length or has control chars/newlines')]
    >>> specs.validate_spec(Path('tests/s.md'), template.format(meta='- Scope: scope\x85value', body=''))
    [Drift(location='tests/s.md', rule='attention.unsafe-field', detail='Scope is over-length or has control chars/newlines')]
    >>> specs.validate_spec(Path('tests/s.md'), template.format(meta='- Scope: ' + ('x' * 300), body=''))
    []
    >>> specs.validate_spec(Path('tests/s.md'), template.format(meta='- Summary: ' + ('x' * 301), body=''))
    [Drift(location='tests/s.md', rule='attention.unsafe-field', detail='Summary is over-length or has control chars/newlines')]
    >>> specs.validate_spec(Path('tests/s.md'), template.format(meta='', body='## 1. Doc\n\n```\n- Scope: ' + ('x' * 301) + '\n```\n'))
    []
    ```
    Passing output of `tests/test_specs_verbs.py::CheckTests::test_body_gate_example_is_not_a_real_gate`:
    ```
    $ python3 -m pytest tests/test_specs_verbs.py::CheckTests::test_body_gate_example_is_not_a_real_gate
    .                                                                        [100%]
    1 passed in 2.03s
    ```
    Detail string confirmation:
    Emitted drift detail is `Scope is over-length or has control chars/newlines` (or `Summary is over-length or has control chars/newlines`). It does NOT contain the offending value.
    Source in `agent_workflows/specs.py`:
    ```python
    scope = _read_scope(lines)
    if scope is not None and not A.is_safe_descriptive(scope):
        drift.append(
            core.Drift(
                loc,
                "attention.unsafe-field",
                A.escape_detail("Scope is over-length or has control chars/newlines"),
            )
        )

    spec_summary = _read_summary(lines)
    if spec_summary is not None and not A.is_safe_descriptive(spec_summary):
        drift.append(
            core.Drift(
                loc,
                "attention.unsafe-field",
                A.escape_detail("Summary is over-length or has control chars/newlines"),
            )
        )
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a Python session calling `releases.validate_release` on each of SIX cases and showing the returned drift: (1) an over-length `- Summary:` BULLET yielding exactly one `attention.unsafe-field`; (2) a control-char-bearing BULLET yielding the same; (3) a conforming bullet yielding `[]`; (4) a `## Summary` PROSE section containing an ANSI ESC yielding exactly one `attention.unsafe-field` whose detail names the PROSE form; (5) a 400-character control-char-free PROSE section yielding `[]`, which is the evidence that the prose form is deliberately unbounded in length (F-13, OQ-04); (6) the ACTUAL committed `2.0.0` record yielding `[]`, with its effective summary length pasted beside it so a reader can see the 457-character value passing BY DESIGN rather than by accident. Then paste `aw check releases --agent` on the repository tree with its exit code showing 0.
  TWO PRE-FIX COUNTERPARTS ARE MANDATORY, NOT ONE, and omitting the prose one fails this item: case (1) showing `[]` at HEAD proves the bullet rule is new coverage, and case (4) showing `[]` at HEAD proves the PROSE rule is new coverage. A run that pastes only the bullet counterpart cannot distinguish the corrected E-03 from the authored bullet-only version, which F-12 measured as having zero coverage of the live tree. Also paste the measured renderer vector this closes: `aw releases show <id6>` on the case-(4) fixture BEFORE the fix, showing the literal escape bytes on its `Summary:` line, so the record states what the rule is for.
  - Observed evidence: PASS. Six cases in releases.validate_release verified with two pre-fix counterparts at HEAD:
    ```python
    >>> releases.validate_release(Path('tests/case1.release.md'), case1_text) # over-length bullet
    []
    >>> releases.validate_release(Path('tests/case4.release.md'), case4_text) # prose with ANSI ESC
    []
    ```
    Measured renderer vector before fix (`aw releases show <id6>` on case-4 fixture emitting raw ANSI escapes):
    ```
    Raw stdout repr from run_show:
    'release 9.9.9 (rcase4)\n  Status:  planned\n  Version: 9.9.9\n  Id:      rcase4\n  Path:    .aw/records/releases/20260930-rcase4-01-rcase4-inj.release.md\n  Summary: red\x1b[31mINJECTED\x1b[0m\n\nrelease-blockers (0)\n  none outstanding\n\nworkflow history\n  - 2026-09-30 created: fixture\n'
    Summary line repr: '  Summary: red\x1b[31mINJECTED\x1b[0m'
    ```

    Post-fix Python session calling `releases.validate_release` on SIX cases:
    ```python
    >>> # Case 1: Over-length Summary bullet (> 300 chars)
    >>> releases.validate_release(p1, case1_text)
    [Drift(location='tests/rel_case1.release.md', rule='attention.unsafe-field', detail='Summary bullet is over-length or has control chars/newlines')]
    >>> # Case 2: Control-char-bearing Summary bullet (BEL)
    >>> releases.validate_release(p2, case2_text)
    [Drift(location='tests/rel_case2.release.md', rule='attention.unsafe-field', detail='Summary bullet is over-length or has control chars/newlines')]
    >>> # Case 3: Conforming Summary bullet
    >>> releases.validate_release(p3, case3_text)
    []
    >>> # Case 4: ## Summary PROSE section containing ANSI ESC
    >>> releases.validate_release(p4, case4_text)
    [Drift(location='tests/rel_case4.release.md', rule='attention.unsafe-field', detail='Summary prose contains control characters')]
    >>> # Case 5: 400-char control-char-free PROSE section (pins deliberate length asymmetry)
    >>> releases.validate_release(p5, case5_text)
    []
    >>> # Case 6: Actual committed 2.0.0 record (.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md)
    >>> # Effective summary length: 457 characters
    >>> releases.validate_release(p200, txt200)
    []
    ```

    `aw check releases --agent` on repository tree:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"releases","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":null}
    ```
    Exit code: 0.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a Python session showing `'attention.unsafe-field' in check_engine.RULE_REGISTRY` is now `True` and the returned `RuleSpec`, with `severity == "error"`, `assurance == ASSURANCE_REPOSITORY`, `determinism == DET_DETERMINISTIC` and an EMPTY invariant. Paste the same lookup from HEAD showing `False`, and paste `_DEFAULT_RULESPEC` so the claim that the observable severity is unchanged (F-09) is visible rather than asserted. Then MEASURE the exit code the severity implies rather than reasoning about it: paste `artifact_core.drift_exit_code([...])` for a single `attention.unsafe-field` drift showing 1, and paste the registered comment showing it records why registration matters despite not changing today's behavior and why the invariant is empty.
  - Observed evidence: PASS. 'attention.unsafe-field' registered in check_engine.RULE_REGISTRY at error severity:
    Lookup from HEAD showing False:
    ```python
    >>> 'attention.unsafe-field' in check_engine.RULE_REGISTRY
    False
    ```
    Default RuleSpec showing inherited error severity:
    ```python
    >>> check_engine._DEFAULT_RULESPEC
    RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='')
    ```

    Post-fix Python session:
    ```python
    >>> from agent_workflows import check_engine, artifact_core as core
    >>> 'attention.unsafe-field' in check_engine.RULE_REGISTRY
    True
    >>> spec = check_engine.rule_spec('attention.unsafe-field')
    >>> spec
    RuleSpec(severity='error', assurance='repository', determinism='deterministic', invariant='')
    >>> spec.severity
    'error'
    >>> spec.assurance
    'repository'
    >>> spec.determinism
    'deterministic'
    >>> repr(spec.invariant)
    "''"
    >>> d = core.Drift('some/spec.md', 'attention.unsafe-field', 'Scope is over-length or has control chars/newlines')
    >>> core.drift_exit_code([d])
    1
    ```

    Registered comment in `agent_workflows/check_engine.py`:
    ```python
    # IPD ynhst5 E-04: bounded, single-line, control-char-free descriptive fields across specs,
    # releases, and gates (spec attention-registry-and-cross-tree-status Section 8.8, F10).
    #
    # Severity `error` is chosen because violations of Section 8.8 are stable named `--check` failures
    # (F10); `info` would make the rule advisory and non-failing (artifact_core.drift_exit_code exempts
    # ONLY `info`), and `warning` would fail the gate identically while stating a weaker contract.
    # E-01 having already cleaned the two committed spec violations first means `error` costs nothing
    # on a clean checkout, which is the condition that makes a grandfather tier unnecessary here and
    # distinguishes this case from `check.ipd-uncarried-obligation`, which needed one because 106 plans
    # were non-conforming.
    #
    # REGISTRATION IS NOT BOOKKEEPING: an unregistered rule falls through to `_DEFAULT_RULESPEC`, which
    # is already `RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")`, so the observable
    # severity and exit code are identical today. What registration buys is that the severity becomes
    # DECLARED rather than inherited, so a future change to the default cannot silently reclassify this
    # rule. The in-repo precedent for making exactly this reasoning explicit is the
    # `check.stale-index-missing` / `check.stale-index-stale` pair, whose comment records that an
    # unregistered rule "silently did" fall through to the default.
    #
    # Invariant is `""`: the Phase-0 catalog in spec pqsx96 has no invariant covering output-safety or
    # descriptive field integrity, and inventing one would be a false trace. Precedent: the
    # `stale-index` entries with their own empty invariants.
    #
    # Deterministic: pure string length and regex control-character predicates against declared fields;
    # no inference, hence DET_DETERMINISTIC. Assurance is ASSURANCE_REPOSITORY.
    "attention.unsafe-field": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the full `python3 -m pytest tests/test_specs_releases_unsafe_field.py` output including the `N passed` line. Then paste the PRE-FIX run showing the over-length and control-character cases FAILING with `validate_spec`/`validate_release` returning `[]` in the assertion text. STATE WHICH CASES PASSED IN BOTH STATES and why: BOTH limit cases must pass before and after (the NEWLINE-INJECTION case because F-05 proves no checker can see it, and the BODY-REGION case because F-14 proves the checker deliberately does not read there), and a run where either fails after the fix means the test was written against the wrong property. Also paste: the existing `tests/fixtures/attnview/violations/unsafe-field.md` `Gate-Summary` case still flagging; every `tests/fixtures/attnview/specs-valid/` spec still clean; the bare full-suite run with its `N passed` line.
  THE TREE-LEVEL EVIDENCE IS AN EXIT-CODE CLAIM, NOT A ZERO-FINDING CLAIM, and stating it the other way would send an executor chasing a pre-existing advisory. Paste `aw specs check --agent`, `aw check specs --agent`, `aw check releases --agent` and `aw check all` with their EXIT CODES. Measured at review HEAD `009ae490` so the executor knows the baseline: `aw specs check --agent` is `"checked":38,"findings":0` exit 0; `aw check specs --agent` and `aw check releases --agent` each report `"outcome":"conforms","findings":1` exit 0, where the single finding is the pre-existing `{"location":"<collisions>","rule":"check.collisions-not-checked"}` advisory that has nothing to do with this plan; and `aw check all` exits **1** today with 59 pre-existing findings across the plans tree, NONE of them `attention.unsafe-field`. So the required property is that THIS PLAN ADDS NO `attention.unsafe-field` FINDING and changes no exit code, not that any command reports zero. Re-derive every count at execution and compare the RULE SETS before and after rather than the totals, since the plans-tree finding count drifts with every landed change.
  - Observed evidence: PASS. tests/test_specs_releases_unsafe_field.py passes 14/14, pre-fix counterpart demonstrated, full suite passes:
    Full bare `python3 -m pytest tests/test_specs_releases_unsafe_field.py` post-fix output:
    ```
    $ python3 -m pytest tests/test_specs_releases_unsafe_field.py
    ..............                                                           [100%]
    14 passed in 4.95s
    ```

    Pre-fix falsification run:
    ```
    $ python3 -m pytest tests/test_specs_releases_unsafe_field.py
    =========================== short test summary info ============================
    FAILED tests/test_specs_releases_unsafe_field.py::TestSpecsReleasesUnsafeField::test_spec_scope_unsafe_shapes
    FAILED tests/test_specs_releases_unsafe_field.py::TestSpecsReleasesUnsafeField::test_release_bullet_unsafe_shapes
    FAILED tests/test_specs_releases_unsafe_field.py::TestSpecsReleasesUnsafeField::test_release_prose_unsafe_shapes_and_length_asymmetry
    FAILED tests/test_specs_releases_unsafe_field.py::TestSpecsReleasesUnsafeField::test_rule_registry_entry
    FAILED tests/test_specs_releases_unsafe_field.py::TestSpecsReleasesUnsafeField::test_spec_summary_unsafe_shapes
    5 failed, 9 passed in 5.74s
    ```
    Assertion failure sample showing pre-fix `validate_spec` returning `[]` on over-length Scope:
    ```
    E           AssertionError: Lists differ: [] != ['attention.unsafe-field']
    E           Second list contains 1 additional elements.
    E           First extra element 0:
    E           'attention.unsafe-field'
    E           - []
    E           + ['attention.unsafe-field'] : Summary over-length should yield exactly attention.unsafe-field, got []
    ```
    Cases that passed in BOTH states:
    1. `test_newline_injection_limit`: passed before and after, because F-05 proves no checker can see newline-split content across lines; closing this vector is Order 01 / uz05bl's write-path responsibility.
    2. `test_read_region_limit_body_scope`: passed before and after, because F-14 proves the checker deliberately bounds metadata reading before the first `## ` heading (F-11) while `attention._extract_detail` searches the whole document; carrier `llnvwj` owns escaping what the renderer emits.
    3. Non-regression fixtures:
       - `test_non_regression_gate_summary_fixture` (Gate-Summary in `tests/fixtures/attnview/violations/unsafe-field.md` still flags)
       - `test_non_regression_metadata_region_bound` (body-quoted Scope does not flag)
       - `test_non_regression_valid_specs_fixtures` (all 9 specs in `tests/fixtures/attnview/specs-valid/` clean)
       - `test_non_regression_live_committed_release` (committed 2.0.0 record validates clean)
       - Conforming boundary tests (`test_spec_scope_conforming_boundary`, `test_spec_summary_conforming`, `test_release_bullet_conforming`).

    Bare full-suite run:
    ```
    $ python3 -m pytest
    4377 passed, 2 skipped, 3 warnings in 264.04s (0:04:24)
    ```

    Repository tree checks:
    - `aw specs check --agent`:
      ```json
      {"schema":"aw.agent/v1","kind":"result","cmd":"specs check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":39,"findings":0,"evidence":["specs"],"next":null}
      ```
      Exit code: 0.
    - `aw check specs --agent`:
      ```json
      {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"specs","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw specs check"}
      ```
      Exit code: 0.
    - `aw check releases --agent`:
      ```json
      {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"releases","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":null}
      ```
      Exit code: 0.
    - `aw check all --agent`:
      Outcome: `findings`, Exit code: 1, Total findings: 72 (identical to pre-change baseline).
      Unique rules: `['check.ipd-carrier-finished-unverified', 'check.ipd-lint-diagnostic', 'check.ipd-uncarried-obligation', 'check.lifecycle-transition-invalid', 'check.name-nonconformant', 'check.plan-spec-link-missing', 'check.review-decision-unescalated', 'check.scope-drift', 'check.scope-path-target-stale', 'check.spec-criteria-uncovered', 'check.system-layout-missing']`.
      `attention.unsafe-field` in rules: **False**.
      This confirms this plan adds NO `attention.unsafe-field` finding and changes no exit code.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. `- Readiness: go-pending-approval` was written by `/plan-review` on 2026-09-30 as that review's output and is NOT an author-written value; the plan carries no `- Approval:` field, because that is a human's attestation and writing one here would forge it.

Execute only the checklist above; commit through `aw commit ynhst5 -- agent_workflows/specs.py agent_workflows/releases.py agent_workflows/check_engine.py tests/test_specs_releases_unsafe_field.py .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md` and never `git add -A`, verifying the staged set before each commit because this checkout is shared. Do not push and do not tag.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every claim of a pass, never a summary you did not run. This plan's own V-items require PRE-FIX FAILING runs on BOTH validators, and a fabricated one would assert the very defect coverage it is meant to prove. Run the suite BARE (`python3 -m pytest`); the configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, and a second `-q` would suppress the `N passed` line this gate requires.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the six paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, MAKE the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Do not stop and wait over a scope question. The one condition that DOES warrant stopping and reporting is a genuinely unsafe one: a concurrent edit to `specs.py` (which siblings Order 01 and Order 02 also touch) that cannot be safely combined with this change.

All open questions are resolved and none is blocking (OQ-01, OQ-02, OQ-03, and OQ-04 added at review).

Before the terminal transition, `aw ipd lint --phase pre-transition` must report conforming and every `V-*` above must carry pasted evidence. The transition is then UNCONDITIONALLY owed with a CONDITIONAL owner: in a managed lane the RUNNER owns it (`aw ipd begin`/`finalize` refuse an agent there with `AW-LIFECYCLE-ROLE-001`), and only in an unmanaged or manual run does the executor run `aw ipd finalize ynhst5 --actor <agent/model> --message <summary> --apply` itself. Never hand-roll the move with `git mv` and never hand-edit `- Status: executed`.

TWO DECLARED SPEC EDITS: this plan's `- Scope-Paths:` names two `.spec.md` files, which the runners announce before the run starts and reconcile at run end. They are E-01 conformance repairs to a single summary line each, not contract amendments; see the Spec / documentation sync section for why that is legitimate and what it deliberately does not touch.

INDEPENDENCE: this plan declares `- Item-Dependencies: none` and is independent of its siblings. It edits `specs.validate_spec`, `releases.validate_release` and `check_engine.RULE_REGISTRY`; Order 01 and Order 02 edit `specs.run_new`/`run_set`/`run_note`, which are different functions in one of the same files. If run in parallel lanes the merge-and-revalidate gate sees both edits to `specs.py`; they are in disjoint functions, so that is a normal merge rather than a hazard. ORDER RELATIVE TO ORDER 01 IS WORTH NOTING even though it is not a dependency: if Order 01 lands first, the injection fixture E-05 needs can no longer be produced through the verb, so E-05 must build it by rendering a string (`specs._render_new_spec`) or by writing the fixture bytes directly, which is what that item already specifies.
