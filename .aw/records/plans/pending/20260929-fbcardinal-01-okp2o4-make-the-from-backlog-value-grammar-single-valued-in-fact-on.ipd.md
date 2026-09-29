# IPD: Make the From-Backlog value grammar single-valued in fact: one shared classifier, every reader agreeing, a malformed value flagged instead of silently invisible

- Date: 2026-09-29
- Kind: child
- Concern: A multi-valued `- From-Backlog: a, b` is INVISIBLE to every reader of the field, so a plan graduated from two items resolves to NEITHER and its release-gate handoff silently vanishes. Reproduced at HEAD `5af09743` on the one corpus artifact carrying two source ids (`nmlx47`): `check_engine.find_from_backlog_artifacts('dstnso')` returns four plans and NOT `nmlx47`, `find_from_backlog_artifacts('8hx3g3')` returns `[]`, and `check_engine._from_backlog_carrier_index` lists `nmlx47` as a carrier for NEITHER id (measured: `carrier index membership of nmlx47 -> []`). WORSE THAN A PARSE MISS, because the carrier index is exactly what the close-legitimacy predicate consults: a handoff that LOOKS recorded in the plan is absent from the gate, so `check_engine.evaluate_blocking_close` refuses a legitimate close (fail-closed, benign) while `check.live-bug-ungated` flags an item whose carrier genuinely exists (a false positive that trains people to ignore the rule), and `check.from-backlog-dangling` reports NOTHING rather than flagging an unparseable value (measured: `releases.check_from_backlog` returns 0 findings against the corpus). FIVE READERS DISAGREE ON THE SAME BYTES, which is the real defect: on `a, b` the four `\S+`-anchored patterns (`releases._ITEM_FROM_BACKLOG_RE`, `check_engine._META_FROM_BACKLOG_RE`, `production_checks._ITEM_FROM_BACKLOG_RE`, `selectors._TYPED_SUBJECT_RE`) all match NOTHING and read the field as ABSENT, while on the no-space form `a,b` the first three CAPTURE THE JUNK TOKEN `'dstnso,8hx3g3'` and `runner_shared._read_from_backlog` returns `None` for it, so `aw check` and the runner reach OPPOSITE conclusions about one file. The writer is also not idempotent on such a value: `releases.set_from_backlog_line(text, 'cccccc')` applied to a text already carrying `- From-Backlog: aaaaaa, bbbbbb` leaves TWO `- From-Backlog:` lines (measured: `count of From-Backlog lines: 2`), because its `\S+` strip regex cannot match what a previous call wrote.
- Scope: Ratify the field as SINGLE-VALUED (the direction every in-force artifact already asserts) and make that true IN FACT rather than only in a comment, by introducing ONE shared value classifier in `ipd_schema` that all readers consult, so a comma-bearing or otherwise non-id6 value is FLAGGED by `check.from-backlog-malformed` instead of silently reading as absent or as a junk token. Repair the non-idempotent writer strip. Resolve the single corpus artifact (`nmlx47`) by deleting a value that no longer carries anything (its forward links already record the truth). Deliberately NOT extended to `From-Spec` beyond the shared classifier's availability, and NOT a multi-valued redesign: see "Deferred / out of scope".
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/releases.py, agent_workflows/check_engine.py, agent_workflows/production_checks.py, agent_workflows/runner_shared.py, tests/test_from_backlog_cardinality.py, tests/test_check_engine_release_gate.py, .aw/records/plans/superseded/20260917-hostdedup-02-nmlx47-unify-the-twelve-small-divergent-symbols-behind-hostlabels.ipd.md, .aw/records/backlog/README.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 6os96s
- Blocks-Release: next
- Set: fbcardinal
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: okp2o4

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): created by graduating backlog item `6os96s`, with the cardinality question the item posed RESOLVED from repository evidence (single-valued; see OQ-01) rather than deferred to the human.

## Goal

Make `- From-Backlog:` single-valued IN FACT: one shared classifier decides whether a value is a usable id6, every reader consults it and therefore agrees, and a value that is neither a usable id6 nor an absent sentinel is REPORTED (`check.from-backlog-malformed`) instead of silently reading as absent by four readers and as a junk token by three. The invariant this buys: no artifact can record a graduation handoff that the release gate cannot see.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one classifier, every reader consulting it

- [ ] E-01 Add a shared three-way `From-Backlog`/`From-Spec` value classifier to `agent_workflows/ipd_schema.py`, beside `source_link_is_absent` and the `SOURCE_LINK_ABSENT_SENTINELS` it owns. It must return a distinguishable verdict for each of: absent (None/empty/a sentinel, delegated to the EXISTING `source_link_is_absent`), a usable single id6 (judged by the EXISTING `artifact_core.is_valid_id6`), and malformed (anything else, including any comma-bearing or multi-token value). Write NO new regex and NO new id6 pattern; a fifth id6 validator is the second mechanism GUIDING_PRINCIPLES P8 forbids. Document in the comment block that the field is single-valued IN FACT as of this plan and that `Graduated-To` remains the one multi-valued link field.
  - Depends on: none
  - Expected outcome: `ipd_schema` exposes one classifier whose verdict on `'dstnso, 8hx3g3'` and on `'dstnso,8hx3g3'` is malformed, on each of `-`/`none`/`unresolved` (any case, quoted or not) is absent, and on `'dstnso'` is a usable id6; `artifact_core.is_valid_id6` and `source_link_is_absent` are the only judgement primitives it calls.
  - Execution state: pending

- [ ] E-02 Re-point every value READER at the E-01 classifier so the five surfaces cannot disagree (F-2): `check_engine._from_backlog_value` (the single private reader feeding `find_from_backlog_plans`, `find_from_backlog_specs`, `_from_backlog_carrier_index` and `release_gate_warnings`), the two consumers of `production_checks._ITEM_FROM_BACKLOG_RE` (`_check_ipd_conformance` and `backlog_graduate_count`), and `runner_shared._read_from_backlog`. A malformed value must yield "no usable link" everywhere rather than the junk token three readers capture today on the no-space form. Keep each reader's own field-LINE extraction as is where it is already correct (`runner_shared._read_from_backlog` must keep reading through `ipd_lint.parse().meta_fields` per its docstring, "THE FIELD NAME IS THE SCHEMA'S, NOT A LOCAL REGEX"); change only the VALUE judgement, and widen a line pattern only where it must capture a multi-token value in order to classify it.
  - Depends on: E-01
  - Expected outcome: for both `a, b` and `a,b`, all of `check_engine._from_backlog_value`, `production_checks`' two consumers and `runner_shared._read_from_backlog` report no usable link; none returns `'dstnso,8hx3g3'`; and behavior on a valid id6 and on every sentinel is byte-for-byte unchanged.
  - Execution state: pending

- [ ] E-03 Make `releases.set_from_backlog_line` idempotent on ANY prior value by widening its `_FROM_BACKLOG_LINE_RE` strip to tolerate a multi-token value, following the shape `_GRADUATED_TO_LINE_RE` already uses (`[^\n]*`). Preserve everything else the function documents: the `'-'`/None clearing semantics, the insert anchors (after `- Status:`, falling back to `- Id:`), and the mirror relationship with `set_blocks_release_line` and `set_graduated_to_line`. Note in the comment that the `\S+` form could not strip what a previous call had written (F-6).
  - Depends on: none
  - Expected outcome: applying `set_from_backlog_line` twice to a text already carrying `- From-Backlog: aaaaaa, bbbbbb` leaves exactly ONE `- From-Backlog:` line carrying the latest value, and `ipd_schema.parse_metadata_block` reports no `duplicate field` error; clearing with `'-'` removes it.
  - Execution state: pending

### Task group 2: the finding, the corpus, the proof

- [ ] E-04 Add `check.from-backlog-malformed` and report it from `releases.check_from_backlog`, keeping SHAPE and RESOLUTION as separate findings exactly as `check_graduated_to` does for its own two rules. Register the id in `check_engine.RULE_REGISTRY` at `error` severity with the same assurance/determinism class and the same `I-07` invariant its `-dangling` sibling carries (a value the gate cannot read breaks the same gate-preservation invariant), and add it to `RELEASE_GATE_RULES` so `aw check release-gates` covers it. Emit the malformed finding WITHOUT consulting the known-backlog-id set, so it stays correct on a tree with no backlog corpus and does not spread the empty-corpus gap that function's docstring warns against. Do NOT widen `-dangling` to cover the shape case, and do not add a rule id containing the substring `duplicate` (the `graduate` view's structural prohibition recorded in `RULE_REGISTRY`).
  - Depends on: E-01
  - Expected outcome: `releases.check_from_backlog` reports `check.from-backlog-malformed` for an artifact carrying `- From-Backlog: aaaaaa, bbbbbb`, reports `check.from-backlog-dangling` (and NOT malformed) for a well-formed id6 naming no item, and reports NEITHER for a valid resolving id6 or a sentinel; the new id appears in `RULE_REGISTRY` and in `RELEASE_GATE_RULES`.
  - Execution state: pending

- [ ] E-05 Resolve the one corpus offender: delete the `- From-Backlog: dstnso, 8hx3g3` line from the superseded plan `nmlx47`, leaving no back-link rather than arbitrarily keeping one of two sources. This is the honest resolution on the evidence (F-5): both `dstnso` and `8hx3g3` already record this graduation forward as `- Graduated-To: forkresid`, the plan is `superseded` and carries no `- Blocks-Release:`, and its own history records that it was superseded and its remainder REFUSED, so a back-link asserting a completed handoff through it would be false. Append a dated `## Workflow history` line recording the removal and pointing at this plan; per the execution contract, do NOT alter anything the plan RECORDS (its items, evidence, results or status).
  - Depends on: E-04
  - Expected outcome: `nmlx47` carries no `- From-Backlog:` line, one appended history line naming `okp2o4`, and no other byte changed; the corpus contains zero non-id6 `From-Backlog` values, so `aw check` is clean with the new rule active.
  - Execution state: pending

- [ ] E-06 Add `tests/test_from_backlog_cardinality.py` as a BEHAVIORAL cross-reader parity test (no `inspect`, no `ast`, no source-text assertions; drive the functions and the CLI and assert on returned values, findings and exit codes). It must cover, as a matrix over the real inputs `'dstnso, 8hx3g3'`, `'dstnso,8hx3g3'`, each member of `SOURCE_LINK_ABSENT_SENTINELS` (including a quoted and an upper-case spelling) and a valid id6: (a) every reader from E-02 agrees on every input; (b) a multi-valued value is NOT silently invisible to `_from_backlog_carrier_index` but is reported by the E-04 rule; (c) the writer idempotency from E-03; and (d) a REGRESSION reproduction of F-1 built as a fixture (a plan carrying two source ids plus a blocking item) asserting the carrier index and `evaluate_blocking_close` no longer read the file as carrying nothing silently. Extend `tests/test_check_engine_release_gate.py::test_whole_family_rules_constant` for the new member of `RELEASE_GATE_RULES`.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the new file passes; the existing 27 tests in `tests/test_check_engine_release_gate.py` still pass with the family constant updated; each assertion fails if its corresponding change is reverted.
  - Execution state: pending

- [ ] E-07 Record the ratified grammar and the new rule for humans: state in `.aw/records/backlog/README.md`, beside the existing "the ONE item it came from" text, that a value naming more than one source is REFUSED by `check.from-backlog-malformed` rather than silently ignored, and that `-` clears the field (leaving the `Graduated-To` multi-valued paragraph untouched so the contrast stays legible). Add a `CHANGELOG.md` entry. Write no em or en dashes in this user-facing prose.
  - Depends on: E-04
  - Expected outcome: a reader of `.aw/records/backlog/README.md` learns both the cardinality and the consequence of violating it; `CHANGELOG.md` names the new rule.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE DIRECTION IS ALREADY DECIDED BY IN-FORCE ARTIFACTS, so this plan ratifies rather than chooses. `ipd_schema.META_FROM_BACKLOG`'s comment calls it "an optional, single-valued link field naming the backlog item id6"; the APPROVED spec `2lcqno` states "pointing at its single source" and "a child has exactly one source"; `.aw/records/backlog/README.md` says `- From-Backlog: <id6>` names "the ONE item it came from" and "a child plan has exactly one source"; and the setter surface takes one value (`aw ipd scaffold --from-backlog FROM_BACKLOG`, whose help reads "Backlog item id6 this plan graduates from"). NOTE the backlog item's claim that the schema comment says "single-valued" TWICE is wrong: it says it once for `From-Backlog` and once for its `From-Spec` sibling, which are two fields. The conclusion is unaffected.
- `Graduated-To` IS THE PRECEDENT FOR EVERY DESIGN CHOICE HERE, and it is a precedent to FOLLOW rather than to copy blindly. It is the one field deliberately MULTI-valued (`ipd_schema.META_GRADUATED_TO`: "It is MULTI-VALUED (`<setid>[, <setid>...]`), which is the one structural difference from every other link field here"). Its `releases.check_graduated_to` docstring already RECORDS the measurement this plan re-derives: on `- Graduated-To: first, second` both sibling single-token patterns "match NOTHING, because `\S+` cannot span the space and the `$` anchor then fails. So a copied regex does not under-validate a two-entry field, it reports it as ABSENT and the file as CLEAN." It also establishes the rule that SHAPE and RESOLUTION are separate findings ("`check.graduated-to-malformed` - a token that is not a valid setid at all... Reported SEPARATELY and never as dangling, because 'does not resolve to a real Set' sends a reader hunting for a missing Set when the real defect is in the token"), which is exactly why E-04 adds a new rule id rather than widening `check.from-backlog-dangling`.
- NO NEW id6 VALIDATOR MAY BE WRITTEN (GUIDING_PRINCIPLES P8, "a second mechanism... is the drift P8 forbids", quoted in `releases.check_graduated_to`). The canonical predicate already exists as `artifact_core.is_valid_id6` over `artifact_core.ID6_RE`. Four near-duplicates are already in the tree (`check_engine._ID6_RE`, `runner_shared.ID6_RE`, `ipd_schema.CARRIER_ID6_RE`, `research_contract.ID6_RE` which correctly re-exports the core one), so the classifier must consume the existing authority and add no fifth.
- THE ABSENT-SENTINEL VOCABULARY IS OWNED AND SHARED. `ipd_schema.SOURCE_LINK_ABSENT_SENTINELS` is `frozenset({"-", "none", "unresolved"})` and `ipd_schema.source_link_is_absent` applies it case-insensitively after stripping quotes, for BOTH `From-Backlog` and `From-Spec`. The new classifier must be built ON that function, never beside it, and `tests/test_check_engine_release_gate.py::test_regression_guard_all_readers_honor_schema_sentinels` already pins that six public readers honor it (that guard covers SENTINELS only, never multi-value or duplicate-bullet input, which is the hole E-06 fills).
- A TERMINAL CARRIER IS ALREADY SKIPPED BY THE GATE RULES BUT NOT BY THE DANGLING SCAN, which decides where the new finding can legitimately fire. `check_engine.check_release_gate_consistency` skips a retired carrier deliberately ("a finished plan's gate is history, not a live claim"), whereas `releases.check_from_backlog` applies no `is_retired` filter at all (verified: no `is_retired` reference in `releases.py`). Since the only corpus offender is retired, E-04's new rule would fire on it, which is precisely why E-05 resolves that file in the same change rather than leaving `aw check` red.
- THE TWO BACK-LINK TWINS DISAGREE ON EMPTY-CORPUS FAIL-SAFETY AND MUST KEEP DISAGREEING. `releases.check_from_backlog`'s own docstring records that on a tree with no backlog corpus the spec-side twin returns 0 findings while this function "returned 1 FALSE finding, having no such guard", and instructs: "Do NOT 'harmonize' that guard away to match this function; the difference is a known gap here, not a standard to spread." A MALFORMED finding is exempt from that hazard by construction (it is a pure shape judgement needing no corpus), so E-04 must emit it WITHOUT consulting `known`, and must not add a corpus guard that would suppress it.
- THE SCAFFOLD PATH ALREADY REFUSES A MULTI-VALUED VALUE AND THE SETTER PATH DOES NOT. `ipd_authoring.run_scaffold` resolves `--from-backlog` through `backlog.find_item` and exits 2 when it names no item (measured: `backlog.find_item(r, "aaaaaa, bbbbbb")` returns `None`), while `status_set.py`'s write path documents itself as "a WRITE, NEVER A REFUSAL". That asymmetry is why the check surface, not the writer, is the load-bearing place to flag the value.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measurements taken in this worktree at HEAD `5af09743`.

| Id | Finding | Evidence |
|---|---|---|
| F-1 | The defect reproduces exactly as filed. `find_from_backlog_artifacts('dstnso')` returns 4 plans, none of them `nmlx47`; `find_from_backlog_artifacts('8hx3g3')` returns `[]`; and `_from_backlog_carrier_index` lists `nmlx47` under no key at all. | Driven in-process: `carrier index membership of nmlx47 -> []`, `8hx3g3 carriers: []`. |
| F-2 | FIVE readers, THREE different answers, on the same bytes. On `a, b`: `releases._ITEM_FROM_BACKLOG_RE`, `check_engine._META_FROM_BACKLOG_RE`, `production_checks._ITEM_FROM_BACKLOG_RE`, `selectors._TYPED_SUBJECT_RE` and `runner_shared._read_from_backlog` ALL yield `None`. On `a,b`: the first three capture `'dstnso,8hx3g3'` while `selectors._TYPED_SUBJECT_RE` and `runner_shared._read_from_backlog` still yield `None`. So on the no-space form `aw check` sees a dangling id and the runner sees no link. | Tabulated in-process over all five readers for both forms. |
| F-3 | `check.from-backlog-dangling` reports NOTHING today, so the corpus reads clean while containing an unreadable value. | `releases.check_from_backlog(repo)` -> `0` findings. |
| F-4 | Exactly ONE artifact in the whole records tree carries a non-id6 `From-Backlog` value, and it is RETIRED. Scanning every `.md` under `.aw/records/{plans,specs,backlog}`: 0 non-retired artifacts have a non-id6 value; 1 retired one does, `nmlx47` (`- From-Backlog: dstnso, 8hx3g3`), now in `plans/superseded/` with `- Status: superseded` and NO `- Blocks-Release:` line. So the fix's blast radius on live artifacts is zero and it cannot break a live gate. | Scan output: `NON-RETIRED ... : 0`, `RETIRED ... : 1`. |
| F-5 | `nmlx47`'s value has nothing left to preserve, which is what makes E-05 a deletion rather than a judgement call. Both named ids resolve, and BOTH already record this graduation through the forward link, pointing at a DIFFERENT Set than `nmlx47`'s own: `dstnso` is `- Status: done` with `- Graduated-To: forkresid`, and `8hx3g3` is `- Status: graduated` with `- Graduated-To: forkresid`, while `nmlx47` is `- Set: hostdedup`. The relationship is therefore already recorded correctly elsewhere, and the back-link on a superseded plan asserts a handoff that demonstrably did not happen through it (its own history says it was "Superseded by 1f7xno ... and REFUSED for the remainder"). | `releases.parse_graduated_to` on both items -> `['forkresid']`. |
| F-6 | The writer is NOT IDEMPOTENT on a multi-valued value, an additional defect the item did not name. `releases.set_from_backlog_line` strips via `_FROM_BACKLOG_LINE_RE` (`\S+`-anchored), which cannot match the `a, b` line a previous call wrote, so a subsequent set APPENDS: the result carries two `- From-Backlog:` lines and `ipd_schema.parse_metadata_block` returns `MetaError(field='From-Backlog', message='duplicate field')` (lint `IPD-M102`), with first-wins semantics silently choosing between them. | `count of From-Backlog lines: 2` after a second `set_from_backlog_line`. |
| F-7 | Duplicate BULLETS are already handled and need no work here, which bounds the plan. `ipd_schema.parse_metadata_block` flags a second `- From-Backlog:` bullet as a duplicate field, surfaced by `ipd_lint` as `IPD-M102`, and the corpus contains no artifact with two bullets of the field. The uncovered case is exclusively the multi-token VALUE. | `parse_metadata_block` output above; corpus census found no repeated bullet. |
| F-8 | `ipd_lint` never names the field, so there is no lint-side value validation to change: `rg "From-Backlog" agent_workflows/ipd_lint.py` exits 1. Validation belongs on the `aw check` surface, exactly as `ipd_schema`'s comment directs ("value validation ... lives in the `aw check` surface (check.from-backlog-dangling), not the schema layer"). | Zero matches. |
| F-9 | Baseline for the test file this plan extends is green: `tests/test_check_engine_release_gate.py` reports `27 passed`. | `python3 -m pytest tests/test_check_engine_release_gate.py -x` -> `27 passed in 3.79s`. |

## Proposed changes (ordered, validatable)

1. Add ONE shared value classifier to `ipd_schema` (the module that already owns `META_FROM_BACKLOG` and `source_link_is_absent`), returning a three-way verdict: absent, a usable id6, or malformed. Built on the existing `ipd_schema.source_link_is_absent` and the existing `artifact_core.is_valid_id6`; no new regex and no fifth id6 pattern (E-01).
2. Re-point the readers at it so they cannot disagree: `check_engine._from_backlog_value` (which alone feeds `find_from_backlog_plans`, `find_from_backlog_specs`, `_from_backlog_carrier_index` and `release_gate_warnings`), `production_checks._ITEM_FROM_BACKLOG_RE`'s two consumers, and `runner_shared._read_from_backlog`. Each must return "no usable link" for a malformed value rather than a junk token, so the carrier index, the checker and the runner agree on every input (E-02).
3. Fix the writer's strip so `set_from_backlog_line` is idempotent on ANY prior value, matching how `_GRADUATED_TO_LINE_RE` already tolerates `[^\n]*` where its back-link twin demands `\S+` (E-03).
4. Add `check.from-backlog-malformed`, registered in `check_engine.RULE_REGISTRY` and added to `RELEASE_GATE_RULES`, reported by `releases.check_from_backlog` SEPARATELY from `-dangling` and without consulting the known-id corpus (E-04).
5. Resolve `nmlx47` by deleting its `- From-Backlog:` line, since both its sources already record this graduation via `- Graduated-To: forkresid` and the plan is superseded and gateless (E-05).
6. Add a behavioral cross-reader parity test over the real inputs (`a, b`, `a,b`, each sentinel, a valid id6), asserting all readers agree, plus reachability of the new rule and the writer's idempotency (E-06).
7. Record the ratified grammar where a human reads it, and note the new rule in `CHANGELOG.md` (E-07).

## Deferred / out of scope (with reason)

- MAKING THE FIELD MULTI-VALUED is deliberately NOT done. It is the alternative the backlog item names, and it is refused on evidence, not taste: it would require amending the APPROVED spec `2lcqno` ("its single source", "a child has exactly one source"), `.aw/records/backlog/README.md`, `.aw/records/specs/README.md`, both `ipd_schema` comments, and the carrier-matching description in `llbr2b`; it would leave "the SAME `Blocks-Release`" undefined when two sources carry different gates; and it would buy nothing measurable, since the only artifact that ever used the form is retired and its relationship is already recorded correctly through the forward link (F-4, F-5). Reopening it needs a maintainer ruling plus a spec amendment, not a code change.
- EXTENDING THE MALFORMED RULE TO `From-Spec` is out of scope. The corpus census found 61 `From-Spec` values and ZERO non-conforming, so there is no measured defect to fix; the E-01 classifier is written to serve both fields, so the spec-side twin can adopt it in one line when someone has a reason. Doing it here would be the opportunistic scope-broadening the execution contract forbids.
- HARMONIZING THE EMPTY-CORPUS FAIL-SAFETY GAP between `check_from_backlog` and `check_from_spec_dangling` is out of scope and explicitly warned against in `check_from_backlog`'s own docstring ("Do NOT 'harmonize' that guard away ... the difference is a known gap here, not a standard to spread"). E-04 sidesteps it by making the malformed finding corpus-independent.
- COLLAPSING THE FOUR NEAR-DUPLICATE id6 PATTERNS (`check_engine._ID6_RE`, `runner_shared.ID6_RE`, `ipd_schema.CARRIER_ID6_RE` against the canonical `artifact_core.ID6_RE`) is a real P8 violation but a separate one with its own blast radius. This plan adds no fifth and routes its own judgement through the canonical predicate.

## Scope check

- Over-scope: none. `From-Spec` is left alone beyond gaining access to the shared classifier (see Deferred), `ipd_lint` is untouched (F-8 shows it never names the field), and the duplicate-BULLET case is untouched because `ipd_schema.parse_metadata_block` already reports it as `IPD-M102` (F-7).
- Under-scope: the plan does not make `status_set.py`'s writer REFUSE a malformed value, which would be the belt-and-braces fix on the write side. That path documents itself as "a WRITE, NEVER A REFUSAL", so changing its posture is a separate decision; the check surface catches the value either way, which is what the gate consumes. Recorded rather than silently omitted.

## Required tests / validation

- `python3 -m pytest tests/test_from_backlog_cardinality.py` (new; the cross-reader parity matrix, the malformed-rule reachability, the writer idempotency, and the F-1 regression reproduction).
- `python3 -m pytest tests/test_check_engine_release_gate.py` (27 passing at baseline per F-9, including `test_whole_family_rules_constant` which E-06 updates and `test_regression_guard_all_readers_honor_schema_sentinels` which must still pass unchanged, proving the sentinel contract survived).
- `python3 -m pytest tests/test_ipd_schema.py tests/test_backlog_handoff_close.py tests/test_specs_from_backlog.py tests/test_backlog_production.py tests/test_graduation_forward_links.py tests/test_carrier_scan_single_item_contract.py` (the readers and writers E-02/E-03 touch, plus the AST call-site guard over the carrier scans).
- `python3 -m pytest` BARE, per the execution contract (no added flags: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`), with the `N passed` summary line pasted.
- `aw check` and `aw check release-gates` on this worktree, exit 0, proving the new rule is silent on a corpus E-05 has cleaned.
- `aw ipd lint` on this plan, conforming.
- The reproduction from F-1 re-run after the change: `find_from_backlog_artifacts` / `_from_backlog_carrier_index` on a FIXTURE carrying two ids must no longer read as silently absent.

## Spec / documentation sync

NO SPEC AMENDMENT IS REQUIRED, and this is a positive finding rather than an omission. The chosen direction is what every in-force artifact already asserts: the approved spec `2lcqno` states the child has "exactly one source", and `.aw/records/backlog/README.md`, `.aw/records/specs/README.md` and both `ipd_schema` comments agree. This plan makes the code match the contract instead of changing the contract, so no `.spec.md` file appears in `- Scope-Paths:`. The superseded spec `4w7d6s` (which originated the G2/G4 single-source rule) must NOT be edited: it is the historical record and `2lcqno` carried its content forward. Had the multi-valued direction been chosen, `2lcqno` would have needed amending, which is one of the reasons it was refused (see Deferred).

Documentation that DOES change: `.aw/records/backlog/README.md` gains the consequence of violating the cardinality (E-07), and `CHANGELOG.md` names the new rule. `ipd_schema`'s own comment is updated in E-01 to say the grammar is enforced in fact rather than merely asserted.

## Open questions

### OQ-01: Is `- From-Backlog:` single-valued or multi-valued?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as SINGLE-VALUED, which is why this plan carries no blocking question. The backlog item posed this as the first thing to decide. Four in-force sources agree: the approved spec `2lcqno` ("pointing at its single source", "a child has exactly one source"), `.aw/records/backlog/README.md` ("the ONE item it came from", "a child plan has exactly one source"), `ipd_schema.META_FROM_BACKLOG`'s comment ("single-valued"), and the single-value setter surface (`--from-backlog FROM_BACKLOG`, "Backlog item id6 this plan graduates from"). The corpus agrees too: 499 of 500 front-matter values are a single bare id6, and the one exception is retired, gateless, and has its relationship already recorded through `- Graduated-To: forkresid` on BOTH its sources (F-4, F-5). The multi-valued reading would require amending an approved spec and two READMEs to serve zero live artifacts. A maintainer who wants the opposite answer can say so at review; the decision is recorded here rather than silently assumed.

### OQ-02: Should the malformed value be REFUSED at write time as well as flagged at check time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NOT in this plan, recorded as under-scope above. The scaffold path already refuses (`ipd_authoring.run_scaffold` resolves through `backlog.find_item` and exits 2, measured returning `None` for `'aaaaaa, bbbbbb'`), while `status_set.py`'s path documents itself as "a WRITE, NEVER A REFUSAL" for reasons its comment gives. Changing that posture is a policy decision about the setter, not a fix for this defect: the check surface is what the release gate consumes, so flagging there closes the invariant. E-03 still repairs that path's real bug (non-idempotent strip, F-6).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a driven transcript of the E-01 classifier over the full input matrix showing malformed for `'dstnso, 8hx3g3'` AND `'dstnso,8hx3g3'`, absent for each of `-`/`none`/`unresolved` plus a quoted and an upper-case spelling, and a usable id6 for `'dstnso'`. Also paste a grep proving no new id6 regex was added (the count of id6 patterns in the package is unchanged) and that the classifier calls `artifact_core.is_valid_id6` and `ipd_schema.source_link_is_absent`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the F-2 reader table RE-RUN after the change, over all readers and both comma forms, showing every reader reporting no usable link and NONE returning `'dstnso,8hx3g3'`; plus the same table for a valid id6 and for each sentinel showing behavior unchanged from baseline. Paste the passing run of the reader-owning test files named in "Required tests".
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a transcript applying `releases.set_from_backlog_line` twice (first writing `'aaaaaa, bbbbbb'`, then `'cccccc'`) showing exactly ONE `- From-Backlog:` line carrying `cccccc` afterwards and `ipd_schema.parse_metadata_block` returning an empty error list (contrast with the measured `count of From-Backlog lines: 2` at baseline), plus a clearing case with `'-'` removing the line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `releases.check_from_backlog` output on a scratch fixture containing all four cases (multi-valued, well-formed-but-dangling, valid-and-resolving, sentinel) showing `check.from-backlog-malformed` for the first ONLY, `check.from-backlog-dangling` for the second ONLY, and nothing for the last two. Paste the `RULE_REGISTRY` entry showing `error`/`I-07` and the updated `RELEASE_GATE_RULES` tuple. Paste a run on a fixture with NO backlog corpus proving the malformed finding still fires (corpus-independence) while confirming no new corpus guard was added.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff` for the `nmlx47` file showing ONLY the `- From-Backlog:` line removed plus one appended history line, and nothing else changed (no item, evidence, result or status touched). Paste the corpus re-scan showing 0 non-id6 `From-Backlog` values across `.aw/records/{plans,specs,backlog}` (baseline: 1 retired). Paste `aw check` and `aw check release-gates` at exit 0.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the full passing output of `python3 -m pytest tests/test_from_backlog_cardinality.py` and of `tests/test_check_engine_release_gate.py` (>= the baseline 27, with `test_regression_guard_all_readers_honor_schema_sentinels` passing unchanged). Paste the BARE `python3 -m pytest` summary line. Paste a REVERT PROBE: temporarily undo the E-02 reader change and show the new test FAILING, then restore it and show it passing, proving the test is not vacuous.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `git diff` of `.aw/records/backlog/README.md` and `CHANGELOG.md` showing the cardinality consequence and the new rule id, with the `Graduated-To` multi-valued paragraph unchanged. Paste `aw sanitize --agent` exiting 0 over the changed files and confirm the added user-facing prose contains no em or en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change with one invariant behind it (no artifact may record a graduation handoff the release gate cannot see), so it is a single child rather than a Set: the classifier, the readers, the rule and the corpus repair are not independently shippable, because adding the rule before cleaning `nmlx47` would leave `aw check` red and cleaning `nmlx47` before adding the rule would leave the hole open with nothing to catch a recurrence. E-05 is deliberately ordered after E-04 for that reason.

Execution contract: commit only the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never push. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL output; a claim of passing tests without pasted output does not satisfy any `V-*` item here. Every test authored under E-06 must test observable behavior, never code structure: no `inspect`, no `ast`, no regex over production source, no symbol censuses (GUIDING_PRINCIPLES P16). One deliberate exception to note for the reviewer: V-01's "no new id6 regex" evidence is a grep over source, which is EVIDENCE PASTED INTO THIS PLAN for a human to read, not an assertion in a committed test; do not encode it as one.

Post-gate lifecycle: this plan requires explicit human approval before execution (`- Status: to-review` -> reviewed -> approved). Execute only through the tooled lifecycle (`aw ipd begin` / the runner's finalize), and do not move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item above carries concrete pasted evidence. Its release gate (`- Blocks-Release: next`) is inherited from backlog item `6os96s` and must not be cleared; on execution the item becomes the backlog setter's business (`graduated`, never `done`, until this plan is executed).
