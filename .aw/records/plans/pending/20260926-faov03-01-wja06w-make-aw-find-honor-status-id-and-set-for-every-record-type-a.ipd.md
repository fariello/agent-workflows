# IPD: Make aw find honor --status, --id and --set for every record type and refuse an invalid status

- Date: 2026-09-26
- Kind: child
- Concern: `cli._find_type_records`'s generic branch (the "All other types: specs, prompts, backlog, walkthroughs, roadmaps, comms, releases" branch, which also serves `reviews` and `other`) never reads `--status`, `--id` or `--set`, so the filter flags are silently ignored for every type except `plans` and `research`. Measured at HEAD `f46b6775`: `aw find specs --status to-review` returns 38 rows (the same 38 as unfiltered, of which only 2 are `to-review`), `aw find specs --status bogusvalue` returns 38 at exit 0, `aw find specs --id 4sd62s` returns 38, and `aw find backlog --set closescope` returns all 617 (one item carries that Set). A caller cannot tell a filtered answer from an unfiltered one. Separately, NO branch validates `--status`: `aw find plans --status bogusvalue` and `aw find research --status bogus` both print "no matching ..." at exit 0, indistinguishable from a real empty answer.
- Scope: IN: (a) filter the generic branch on `--status` (via `selectors._read_status`), `--id` (`selectors._read_id`) and `--set` (`selectors._read_setid`), both with and without positional selectors, reusing the text the branch already reads; (b) validate `--status` in `cli._run_find` BEFORE any scan against the type's canonical enum, refusing with exit 2 and a message listing the valid values, for `specs` (`attention_contract.SPEC_STATUSES`), `backlog` (`backlog.STATUSES`), `releases` (`releases.RELEASE_STATUSES`), `plans` (`plans.RECOGNIZED` plus the plans disposition words `aw find plans` accepts today, see OQ-02) and `research` (`research_contract.normalize_status`, which already accepts the legacy `intake` spelling); for `all`, refuse only a value in NO type's enum; (c) a new `tests/test_find_filters.py` on a temp repo. OUT: types with no canonical status enum (`prompts`, `walkthroughs`, `roadmaps`, `comms`, `reviews`, `other`) are FILTERED but not validated (OQ-01); the plans and research SELECTOR-branch read restructuring (plan `qfpnrm`); `--topic` for non-research types; the SQLite cache (spec `4sd62s`).
- Scope-Paths: agent_workflows/cli.py, tests/test_find_filters.py
- Item-Dependencies: executed:qfpnrm
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: faov03
- Blocks-Release: next
- Set: faov03
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: wja06w

## Workflow history

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED; review record `.aw/records/reviews/20260926-faov03-01-wja06w-make-aw-find-honor-status-id-and-set-for-every-record-type-a.review.md`. All of F-1..F-6 re-verified at lane HEAD 9f33c5c4 and every fail-open mode reproduced (specs --status/--id and backlog --set each return the unfiltered count; plans/research bogus statuses exit 0); the dependency `executed:qfpnrm` is satisfied and the post-qfpnrm generic branch is shaped as E-03 assumes; all five status enums and the `intake` normalization exist as named; the `cannot-run` exit-2 refusal shape E-04 wants has a working precedent in the sibling `search` verb. THREE SUBSTANTIVE FIXES: E-04's `all` rule contradicted the plan's own OQ-01 and would have refused a value its single-type query accepts, because `ARTIFACT_TYPES` always spans the six enum-less types (F-7, rule corrected so any enum-less type disables validation, and E-02 case (9) reversed to assert acceptance); for six of the nine generic types NO record has a readable `- Status:`, so `--status` now returns ZERO there and case (10) asserted the opposite (F-8, with the same shape for `--id` on reviews/comms, F-9); and `_read_status` neither case-normalizes nor survives a prose-carrying status line, so the filter now compares case-insensitively (F-10). Also de-counted three drifted live figures and corrected the stale test-file inventory (F-11). `aw ipd lint --phase review-finalize` conforming, 0 findings.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog faov03. Re-measured at HEAD f46b6775: specs --status to-review/bogusvalue/--id 4sd62s each 38 rows (unfiltered 38), backlog --set closescope 617 (unfiltered 617), plans --status bogusvalue and research --status bogus both exit 0 "no matching". Ordered after qfpnrm (Set findonce), which restructures the plans/research branches of the same function.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw find <type> --status/--id/--set` returns only the records matching the filter for every type, and a `--status` value no record of that type can carry is refused at exit 2 with the valid values, so an empty answer always means "none match" and never "your filter was ignored or misspelled".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and tests first

- [ ] E-01 RE-MEASURE at the executing HEAD (after `qfpnrm` landed) and paste row counts and exit codes for: `aw find specs`, `aw find specs --status to-review`, `aw find specs --status bogusvalue`, `aw find specs --id 4sd62s`, `aw find backlog`, `aw find backlog --set closescope`, `aw find backlog --status open`, `aw find releases --status planned`, `aw find plans --status bogusvalue`, `aw find research --status bogus`, `aw find all --status bogusvalue` (the case whose expected answer review CHANGED to accept-and-empty; capture its HEAD behavior so the after-comparison is honest), and `aw find plans --status approved` (a control that already filters). Also read the `qfpnrm`-modified `cli._find_type_records` and paste its current generic-branch body, so E-03 edits the code as it now is. If `qfpnrm` changed the generic branch's shape, adapt E-03 to it rather than restoring the old shape.
  - Depends on: none
  - Expected outcome: the generic-branch filtered counts equal the unfiltered counts; the two bogus-status runs exit 0; the plans control filters.
  - Execution state: pending

- [ ] E-02 ADD `tests/test_find_filters.py` BEFORE the fix. Build a temp repo with `.aw/records/specs/<status>/` specs (at least `to-review` x2, `approved` x1, each with `- Id:`, `- Status:`, `- Set:`), `.aw/records/backlog/open/` and `done/` items with distinct Sets, one release record, and two plans with different statuses. Drive the REAL CLI in-process (`cli.main([... , "--dir", str(tmp), "-p"])` capturing stdout, and `--json` for the exit-code/status assertions) and assert: (1) `find specs --status to-review` prints exactly the two to-review paths; (2) `find specs --id <id6>` prints exactly one; (3) `find backlog --set <setid>` prints only that Set's items; (4) `find specs <selector> --status approved` (selector plus flag) intersects; (5) `find specs --status bogusvalue` exits 2 and its message lists the spec statuses; (6) `find plans --status bogusvalue` exits 2; (7) `find research --status intake` is ACCEPTED (legacy spelling, exits 0); (8) `find backlog --status open` exits 0 and prints only open items; (9) `find all --status open` is accepted (valid for backlog) AND `find all --status bogusvalue` is ALSO accepted at exit 0 with an empty result - NOT refused. This reverses the authored expectation after review measured that refusing it contradicts OQ-01: `all` always spans the six enum-less types, so validating it would make the broad query stricter than the narrow one (`find walkthroughs --status bogusvalue` accepts the same value). Assert BOTH halves - the accepted-and-empty result and exit 0 - and state the reason in the test, because the naive expectation is the opposite and a later reader will otherwise "fix" it; (10) `find walkthroughs --status anything` is ACCEPTED (exit 0, no enum, so no refusal per OQ-01) and returns ZERO rows, which review measured to be the only possible outcome for that type because all 24 walkthrough records lack a readable `- Status:`. Assert zero rows AND exit 0, and comment why, so the case documents the real behavior rather than the word "filters"; (11) `find specs` with no flags prints every spec (the unchanged path). Put a module docstring stating that these tests are the BEHAVIOR spec `4sd62s`'s SQLite-cache rewrite of `aw find` must preserve.
  - Depends on: E-01
  - Expected outcome: FAIL at HEAD: (1)-(6), (8)'s filtering, (10)'s filtering. PASS both before and after (guards, not proofs of the fix): (7), (9) and (11) - note (9) now asserts ACCEPTANCE, which already holds at HEAD, so it guards against the over-strict `all` validation review rejected rather than proving new behavior. Say which group each case is in, in the test module docstring; a guard that FAILS at HEAD means its fixture or expectation is wrong.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 FILTER THE GENERIC BRANCH. In `cli._find_type_records`'s generic branch, read `explicit_status = getattr(args, "status", None)`, `explicit_id`, `explicit_set` and, inside the existing per-path loop that already reads `text`, `continue` past a record whose `sel_mod._read_status(text)` differs from `explicit_status`, whose `sel_mod._read_id(text)` differs from `explicit_id`, or whose `sel_mod._read_setid(text)` differs from `explicit_set`, each only when that flag is given. This applies to both the selector and no-selector arms because they share the loop. Use the same readers the branch already uses for display, so the filter and the printed status column can never disagree.
    TREAT AN UNREADABLE FIELD AS A NON-MATCH, AND DOCUMENT WHAT THAT COSTS, because review measured the cost to be large and entirely concentrated in the types this plan is widening. For SIX of the nine generic types EVERY record's status is unreadable by `_read_status` (walkthroughs 24/24, reviews 367/367, comms 7/7, roadmaps 1/1, other 4/4, prompts 16/17 - they carry no `- Status:` field at all), so after this change `--status` on any of them returns ZERO rows, always. That is honest (none match) and is strictly better than today's silent ignore-and-return-everything, but it must be STATED rather than discovered: E-02 case (10) must assert exactly that (a walkthrough query returns zero, not "filters"), and the refusal-free path for those types (OQ-01) is what keeps it an empty answer instead of an error. `--id` has the same shape for reviews (0/367) and comms (0/7), which carry `Subject-Id:` rather than `- Id:`, so `--id` on those types will likewise return zero; walkthroughs are 9/24. Add one line to the branch's comment recording both measurements, and do NOT "fix" it here by reaching for a looser reader or a second field: the `_STATUS_RE` parity comment makes the strict reader a matching contract, and widening it is a different change with its own blast radius.
    THE READER IS NOT CASE-NORMALIZING (measured: `_read_status` returns `'EXECUTED'` verbatim for `- Status: EXECUTED`, and one plan in this repo declares exactly that), and it returns `None` for a status line carrying trailing prose (measured: `- Status: draft (aw set): status set to draft` -> `None`, a shape `tests/test_find_single_read.py` pins as legitimate). Compare case-insensitively on both sides (`.strip().lower()`), so `--status executed` matches an uppercase declaration, and accept that a prose-carrying status is a non-match for the reason above. Do NOT touch the `plans` or `research` branches' filtering (their `query` helpers already apply these flags).
  - Depends on: E-02
  - Expected outcome: E-02 (1)-(4), (8)'s filter and (10) pass.
  - Execution state: pending

- [ ] E-04 VALIDATE `--status` UP FRONT. Add `cli._find_valid_statuses(artifact_type) -> Optional[FrozenSet[str]]` returning the type's canonical enum (specs `attention_contract.SPEC_STATUSES`; backlog `backlog.STATUSES`; releases `frozenset(releases.RELEASE_STATUSES)`; plans `plans.RECOGNIZED | {"pending", "reusable"}` per OQ-02; research `research_contract.STATUSES | set(research_contract.STATUS_NORMALIZATIONS)`) or `None` for a type with no enum. In `cli._run_find`, after `types` is computed and BEFORE the scan loop, when `--status` is given: collect the enums of the resolved types; if ANY resolved type has NO enum, DO NOT VALIDATE AT ALL (accept and let the filter answer), and otherwise refuse when the value is in none of the collected enums. THE "ANY TYPE WITHOUT AN ENUM DISABLES VALIDATION" RULE IS LOAD-BEARING AND REPLACES THE AUTHORED "at least one type has an enum" RULE, which review measured to contradict OQ-01: `at.ARTIFACT_TYPES` spans all eleven types, so `all` always includes the six enum-less ones, and under the authored rule `aw find all --status <v>` would REFUSE any value outside the 25-value union of the five enums, while `aw find walkthroughs --status <v>` ACCEPTS the very same value because walkthroughs have no enum. Same value, opposite answers, with the broader query being the stricter one - which is backwards, and it would refuse a legitimate lookup for a status only an enum-less type carries. Under the corrected rule `all` never validates (it always spans an enum-less type), so a misspelling under `all` returns an honest empty answer rather than a false refusal; single-type and multi-type-without-`all` queries over enum-bearing types still validate, which is where the defect F-4 actually bites. Render the refusal as a `CommandResult(command="find", status="cannot-run", exit_code=2, ...)` on the `--agent`/`--json` surfaces and as `term.status("fail", ...)` plus return 2 on the human and `--paths` surfaces (stdout stays empty so a `-p` consumer sees no path). The message names the value, the type(s), and the sorted valid values. For a multi-type query whose types ALL have enums, the union is the valid set, so a status only one of them carries still filters the others to nothing, which is correct. For `all`, validation is OFF per the rule above; say so in the code comment and in the refusal's own absence, so a later reader does not "restore" a union check for `all` and reintroduce the contradiction.
  - Depends on: E-03
  - Expected outcome: E-02 (5) and (6) pass (the two refusals); (7) and (9) still pass, which is what proves validation did NOT become over-strict for the legacy spelling or for `all`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 RE-RUN E-01's live commands and paste counts and exit codes, and run `python3 -m pytest tests/test_find_filters.py -o addopts="" -q`.
  - Depends on: E-04
  - Expected outcome, all counts RE-DERIVED at execution rather than compared against a number written here (these are live populations and three have already drifted: review re-measured to-review specs as 1 not 2, backlog as 628 not 617, and `plans --status approved` as 11 not 24): `specs --status to-review` equals a direct count of specs whose `- Status:` is `to-review`; `specs --id 4sd62s` is 1; `backlog --set closescope` equals a direct count of backlog records carrying that Set; the THREE SINGLE-TYPE bogus-status runs (`specs`, `plans`, `research`) exit 2, while `all --status bogusvalue` exits 0 EMPTY per the corrected E-04 rule; `plans --status approved` matches E-01's own re-measured count.
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` before and after the change and compare failing node IDs.
  - Depends on: E-05
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The plans and research branches already filter via `plans_index.query` and `research_index.query`; the generic branch alone does not. `runner_shared` (the `5slbpi` D4 comment above `discover_specs`) and spec `6m4kow`'s honest-limits section both record that two plans routed AROUND this defect instead of fixing it.
- Canonical status enums already exist, one per type, and are reused rather than re-spelled: `attention_contract.SPEC_STATUSES` (from `lifecycle_dirs.LIFECYCLE_SUBDIRS["specs"]`), `backlog.STATUSES`, `releases.RELEASE_STATUSES`, `plans.RECOGNIZED`, `research_contract.STATUSES` with `STATUS_NORMALIZATIONS`.
- `aw find plans` displays `e.disposition or e.status`, and `plans_index.query` filters `status` against the front-matter `- Status:`; the directory words `pending`/`reusable` are displayed but are not `- Status:` values (`cli._PLANS_DISPOSITION_STAGE` comment).
- The dual-audience exit contract: 0 clean, 1 findings, 2 cannot-run; `CommandResult(status="cannot-run", exit_code=2)` is the existing refusal shape (for example in the `ipd board` no-project path).
- `selectors._read_status` / `_read_id` / `_read_setid` are the strict, region-bounded readers the find display already uses; the `_STATUS_RE` parity comment records that their strictness is a matching contract, so the filter must use them rather than a looser reader.
- The old find tests were deleted in `19313eed` (`tests/test_cli_find.py` 688 lines and `tests/test_find_collision_surface.py`). The surviving `tests/test_cli_find.py` (110 lines) covers research status and a symlinked root; `qfpnrm` added `tests/test_find_single_read.py` (436 lines), which calls `cli._find_type_records` directly for plans and research. Neither passes `--status`.
- Spec `4sd62s` (artifact metadata store, `reviewed`) will replace `aw find`'s scanning with a SQLite cache; `tests/test_find_filters.py` is written against the CLI surface, not internals, so it survives that rewrite and defines what it must preserve.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only. Bare `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `f46b6775` (row counts from `aw find ... | wc -l`). F-1 through F-6 are the author's; every one was RE-VERIFIED at lane HEAD `9f33c5c4` during review and every fail-open mode reproduced (see F-11 for the three counts that drifted). F-7 through F-11 were added by `/plan-review` on 2026-09-26.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `cli._find_type_records` generic branch | `--status` ignored. | `find specs` 38; `find specs --status to-review` 38; live spec statuses: to-review 2, approved 13, implemented 15, ... |
| F-2 | HIGH | same | `--id` ignored. | `find specs --id 4sd62s` 38 |
| F-3 | HIGH | same | `--set` ignored. | `find backlog` 617; `find backlog --set closescope` 617; one backlog record carries `- Set: closescope` |
| F-4 | MEDIUM | `cli._run_find` (all branches) | An invalid `--status` is accepted silently at exit 0. | `find specs --status bogusvalue` exit 0 (38 rows); `find plans --status bogusvalue` exit 0 "no matching plans"; `find research --status bogus` exit 0 "no matching research" |
| F-5 | INFO | control | Plans filter correctly. | `find plans --status approved` 24 lines, a strict subset |
| F-6 | INFO | tests | No test covers the filter flags on the generic branch, and no existing test passes `--status` at all (so E-04's validation cannot break one). | `tests/test_cli_find.py` (110 lines at review; research status + a symlinked-root case) and `tests/test_find_single_read.py` (436 lines, added by `qfpnrm`); neither uses the `--status` flag. See F-11 |
| F-7 | HIGH | E-04's `all` rule as authored | "at least one type has an enum and the value is in none of them -> refuse" CONTRADICTS OQ-01. `at.ARTIFACT_TYPES` spans all eleven types, so `all` ALWAYS includes the six enum-less ones; under that rule `aw find all --status ran` would be REFUSED (not in the 25-value union of the five enums) while `aw find walkthroughs --status ran` is ACCEPTED, making the broader query the stricter one and refusing a legitimate lookup for a status only an enum-less type carries. Fixed at review: ANY resolved type without an enum disables validation, so `all` never validates. | union of the five enums = 25 values; `ARTIFACT_TYPES` = 11 types incl. walkthroughs/reviews/comms/roadmaps/other which have no enum |
| F-8 | HIGH | E-03's filter, for the six status-less types | After the fix `--status` on six of the nine generic types returns ZERO rows ALWAYS, because no record of those types has a readable `- Status:`. Honest (and better than today's ignore-and-return-everything) but previously unstated, and it makes E-02 case (10)'s "is accepted and filters" misleading. Stated at review and case (10) rewritten to assert zero rows. | `_read_status` unreadable per type: walkthroughs 24/24, reviews 367/367, comms 7/7, roadmaps 1/1, other 4/4, prompts 16/17; specs 0/38, backlog 0/628, releases 0/1 |
| F-9 | MEDIUM | E-03's `--id` filter | Same shape for `--id`: reviews carry `Subject-Id:` and comms carry no id field, so `--id` on those types returns zero after the fix. Not a defect in the change, but it belongs in the branch comment beside F-8 rather than being discovered later. | readable `- Id:`: reviews 0/367, comms 0/7, walkthroughs 9/24 |
| F-10 | MEDIUM | `selectors._read_status` | The reader is NOT case-normalizing and returns `None` for a status line carrying trailing prose, so an exact-equality filter would miss both shapes. Both occur in this repo. Fixed at review by requiring a case-insensitive compare and by recording the prose case as a deliberate non-match. | `_read_status('- Status: EXECUTED')` -> `'EXECUTED'` (plan `vfa1tl` declares that); `_read_status('- Status: draft (aw set): status set to draft')` -> `None`, a shape `tests/test_find_single_read.py::test_d_...` pins as legitimate |
| F-11 | LOW | F-6 as authored; live counts | F-6 said `tests/` holds only `test_cli_find.py` (94 lines); it is 110 lines, and `qfpnrm` added `tests/test_find_single_read.py` (436 lines), which the plan does not mention. Neither passes `--status`, so E-04 cannot break them, but the new file DOES exercise `cli._find_type_records` directly and its status-disagreement case is what surfaced F-10. Three row counts also drifted between authoring and review (to-review specs 2->1, backlog 617->628, `plans --status approved` 24->11), so all counts are now re-derived rather than asserted. | `wc -l tests/test_cli_find.py` -> 110; `tests/test_find_single_read.py` -> 436; no `--status` flag in either; live re-measurement at review |

## Proposed changes (ordered, validatable)

1. E-01 re-measures after `qfpnrm`.
2. E-02 adds behavioral tests first.
3. E-03 filters the generic branch on status, id and Set.
4. E-04 refuses an out-of-enum `--status` at exit 2, all branches.
5. E-05 re-measures live; E-06 bare suite.

## Deferred / out of scope (with reason)

- Validating `--status` for types with no canonical enum (`prompts`, `walkthroughs`, `roadmaps`, `comms`, `reviews`, `other`).
  - Carrier-Declined: no enum exists in code for them (prompts carry `draft`/`superseded` by convention only; walkthroughs carry none), so any list would be invented here. They are FILTERED, so an unmatched value returns an honest empty answer.
- Replacing the scan with a cache.
  - Carrier-Declined: owned by approved-for-2.0.0 spec 4sd62s (section 4.5 replaces the whole-corpus rescans in `aw find` with the SQLite cache); a spec is not an accepted carrier type, and this plan's tests are the behavior that rewrite must preserve.

## Scope check

- Over-scope: none.
- Under-scope: `plans_index.py` and `research_index.py` are not declared: their `query` helpers already filter; validation lives in `cli._run_find`.
- Scope-Paths justification: `cli.py` holds both functions; the test file is new.

## Required tests / validation

- `tests/test_find_filters.py` (new): the eleven cases in E-02, shown failing before the fix where stated.
- Live re-measurement in E-05.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- No spec is amended. Spec `6m4kow`'s honest-limits bullet ("`aw find specs --status` is broken and STILL broken") becomes stale once this lands; it is NOT edited here (a spec edit in a bug fix would need declaring, and the bullet is history as much as status). After execution, record the fix with `aw specs note` on `6m4kow` naming this plan; that is a note, not a contract change.
- Spec `4sd62s`: no edit. Its rewrite of `aw find` must keep `tests/test_find_filters.py` passing; stated in the test module docstring (E-02) and here.
- The `runner_shared` comment above `discover_specs` explaining why `5slbpi` avoided `--status` becomes stale but is not in scope; it describes a past decision accurately.

## Open questions

### OQ-01: Refuse, filter, or ignore `--status` for a type with no status enum?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: FILTER without validation, from repository evidence: the generic branch already reads and DISPLAYS `_read_status` for every type, so filtering on the displayed value is consistent, while refusing would need an enum that does not exist in code for those types (see Deferred). Ignoring is the defect itself. TWO CONSEQUENCES MADE EXPLICIT AT REVIEW, because this resolution is what forces both. FIRST, it decides the `all` case: `all` always spans an enum-less type, so validating `all` would contradict this answer by refusing a value that the same value's single-type query accepts; hence E-04's corrected rule that any enum-less type in the resolved set disables validation (F-7). SECOND, for six of the nine generic types NO record carries a readable `- Status:`, so "filtered" means an unconditional ZERO rows for them (F-8). Both are honest outcomes and both are strictly better than today's silent ignore, but neither was stated and E-02 case (10) asserted the opposite of the second.

### OQ-02: Which `--status` values are valid for `plans`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `plans.RECOGNIZED` plus the directory words `pending` and `reusable`. `RECOGNIZED` is the readiness/terminal enum `plans_index.query` filters against. `reusable` is already in it; `pending` is not a `- Status:` value, so `--status pending` returns nothing today, but it is displayed in the status column (`cli._PLANS_DISPOSITION_STAGE`), so a reader copying a displayed word must not be refused as "invalid". Accepting it keeps the refusal to values the tool never shows. Changing `pending` to MATCH the directory is a behavior change to the plans filter and out of scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste each E-01 command with its row count and exit code, `qfpnrm`'s `- Status:` line, and the generic-branch body as read.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_find_filters.py -o addopts="" -q` at HEAD BEFORE E-03/E-04, showing the listed cases FAILING and (7), (11) passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the generic-branch diff (including the case-insensitive compare and the comment recording F-8/F-9's unreadable-field measurements) and the test run showing (1)-(4), (8) and (10) passing. Also paste `aw find walkthroughs --status anything -p` returning ZERO rows at exit 0, and `aw find reviews --id <any-id6> -p` returning zero, so the two documented dead ends are shown to be honest empty answers rather than errors.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `_find_valid_statuses` / `_run_find` diff, including the comment stating that an enum-less type in the resolved set disables validation and why (F-7). Paste `aw find specs --status bogusvalue --json` showing `"exit_code": 2` and the valid values; the human-surface message with `echo $?` printing 2; `aw find specs --status bogusvalue -p` showing EMPTY stdout with rc 2; and `aw find all --status bogusvalue` showing exit 0 with no rows (NOT a refusal). Paste the full test file passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the E-01 commands re-run with counts and exit codes, each filtered count compared against a direct count RE-DERIVED at execution (for example `grep -rl "^- Status: to-review" .aw/records/specs --include='*.spec.md' | wc -l`); do not compare against any count written in this plan, since three have already drifted (F-11). Include the `all --status bogusvalue` run showing exit 0.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw find` starts honoring `--status`, `--id` and `--set` for specs, backlog, releases, prompts, walkthroughs, roadmaps, comms, reviews and other (today they are ignored), and `--status` with a value outside the type's enum is refused at exit 2 for every type that has an enum, including plans and research (today such a value exits 0). This is a user-visible behavior change: a script that relied on `--status` doing nothing will now get filtered output, and one passing a misspelled status will now get exit 2. Graduates backlog `faov03` and inherits its `- Blocks-Release: next`. Runs after `qfpnrm` (`- Item-Dependencies: executed:qfpnrm`), which restructures the same function and is already `executed`, so the edge is satisfied.

WHAT REVIEW CHANGED, and two of the three are things an approver should weigh. FIRST, `aw find all --status <misspelling>` will NOT be refused: it returns an empty result at exit 0. The authored rule would have refused it, and review measured that to contradict this plan's own OQ-01, because `all` always spans the six types that have no status enum, so refusing there would make the broad query stricter than the narrow one for the identical value (F-7). Validation therefore applies to single-type and all-enum-bearing queries, which is where the defect actually bites. SECOND, for SIX of the nine newly-filtered types (`walkthroughs`, `reviews`, `comms`, `roadmaps`, `other`, and 16 of 17 `prompts`) NO record carries a readable `- Status:`, so `--status` on them now returns ZERO rows rather than everything (F-8); `--id` behaves the same way for `reviews` and `comms`, which carry `Subject-Id:` instead (F-9). That is the honest answer and it is what fixing the bug means, but it is a bigger visible change for those types than "filters correctly" suggests. THIRD, the filter compares case-insensitively, because the shared reader is not normalizing and at least one record in this repo declares an uppercase status (F-10).

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/cli.py` (`_find_type_records`' generic branch, a new `_find_valid_statuses`, and the validation step in `_run_find`) and the new `tests/test_find_filters.py`. If an edit outside those paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-02 must show the new tests FAILING before the fix.

Commit ONLY through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize`. Then add the `aw specs note` on `6m4kow` described in the spec-sync section, and close backlog `faov03` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
