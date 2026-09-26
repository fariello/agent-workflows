# IPD: Make aw find honor --status, --id and --set for every record type and refuse an invalid status

- Date: 2026-09-26
- Kind: child
- Concern: `cli._find_type_records`'s generic branch (the "All other types: specs, prompts, backlog, walkthroughs, roadmaps, comms, releases" branch, which also serves `reviews` and `other`) never reads `--status`, `--id` or `--set`, so the filter flags are silently ignored for every type except `plans` and `research`. Measured at HEAD `f46b6775`: `aw find specs --status to-review` returns 38 rows (the same 38 as unfiltered, of which only 2 are `to-review`), `aw find specs --status bogusvalue` returns 38 at exit 0, `aw find specs --id 4sd62s` returns 38, and `aw find backlog --set closescope` returns all 617 (one item carries that Set). A caller cannot tell a filtered answer from an unfiltered one. Separately, NO branch validates `--status`: `aw find plans --status bogusvalue` and `aw find research --status bogus` both print "no matching ..." at exit 0, indistinguishable from a real empty answer.
- Scope: IN: (a) filter the generic branch on `--status` (via `selectors._read_status`), `--id` (`selectors._read_id`) and `--set` (`selectors._read_setid`), both with and without positional selectors, reusing the text the branch already reads; (b) validate `--status` in `cli._run_find` BEFORE any scan against the type's canonical enum, refusing with exit 2 and a message listing the valid values, for `specs` (`attention_contract.SPEC_STATUSES`), `backlog` (`backlog.STATUSES`), `releases` (`releases.RELEASE_STATUSES`), `plans` (`plans.RECOGNIZED` plus the plans disposition words `aw find plans` accepts today, see OQ-02) and `research` (`research_contract.normalize_status`, which already accepts the legacy `intake` spelling); for `all`, refuse only a value in NO type's enum; (c) a new `tests/test_find_filters.py` on a temp repo. OUT: types with no canonical status enum (`prompts`, `walkthroughs`, `roadmaps`, `comms`, `reviews`, `other`) are FILTERED but not validated (OQ-01); the plans and research SELECTOR-branch read restructuring (plan `qfpnrm`); `--topic` for non-research types; the SQLite cache (spec `4sd62s`).
- Scope-Paths: agent_workflows/cli.py, tests/test_find_filters.py
- Item-Dependencies: executed:qfpnrm
- Status: to-review
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

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog faov03. Re-measured at HEAD f46b6775: specs --status to-review/bogusvalue/--id 4sd62s each 38 rows (unfiltered 38), backlog --set closescope 617 (unfiltered 617), plans --status bogusvalue and research --status bogus both exit 0 "no matching". Ordered after qfpnrm (Set findonce), which restructures the plans/research branches of the same function.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw find <type> --status/--id/--set` returns only the records matching the filter for every type, and a `--status` value no record of that type can carry is refused at exit 2 with the valid values, so an empty answer always means "none match" and never "your filter was ignored or misspelled".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and tests first

- [ ] E-01 RE-MEASURE at the executing HEAD (after `qfpnrm` landed) and paste row counts and exit codes for: `aw find specs`, `aw find specs --status to-review`, `aw find specs --status bogusvalue`, `aw find specs --id 4sd62s`, `aw find backlog`, `aw find backlog --set closescope`, `aw find backlog --status open`, `aw find releases --status planned`, `aw find plans --status bogusvalue`, `aw find research --status bogus`, and `aw find plans --status approved` (a control that already filters). Also read the `qfpnrm`-modified `cli._find_type_records` and paste its current generic-branch body, so E-03 edits the code as it now is. If `qfpnrm` changed the generic branch's shape, adapt E-03 to it rather than restoring the old shape.
  - Depends on: none
  - Expected outcome: the generic-branch filtered counts equal the unfiltered counts; the two bogus-status runs exit 0; the plans control filters.
  - Execution state: pending

- [ ] E-02 ADD `tests/test_find_filters.py` BEFORE the fix. Build a temp repo with `.aw/records/specs/<status>/` specs (at least `to-review` x2, `approved` x1, each with `- Id:`, `- Status:`, `- Set:`), `.aw/records/backlog/open/` and `done/` items with distinct Sets, one release record, and two plans with different statuses. Drive the REAL CLI in-process (`cli.main([... , "--dir", str(tmp), "-p"])` capturing stdout, and `--json` for the exit-code/status assertions) and assert: (1) `find specs --status to-review` prints exactly the two to-review paths; (2) `find specs --id <id6>` prints exactly one; (3) `find backlog --set <setid>` prints only that Set's items; (4) `find specs <selector> --status approved` (selector plus flag) intersects; (5) `find specs --status bogusvalue` exits 2 and its message lists the spec statuses; (6) `find plans --status bogusvalue` exits 2; (7) `find research --status intake` is ACCEPTED (legacy spelling, exits 0); (8) `find backlog --status open` exits 0 and prints only open items; (9) `find all --status open` is accepted (valid for backlog) and `find all --status bogusvalue` exits 2; (10) `find walkthroughs --status anything` is accepted and filters (no enum; see OQ-01); (11) `find specs` with no flags prints every spec (the unchanged path). Put a module docstring stating that these tests are the BEHAVIOR spec `4sd62s`'s SQLite-cache rewrite of `aw find` must preserve.
  - Depends on: E-01
  - Expected outcome: (1)-(6), (8)'s filtering, (9)'s refusal and (10)'s filtering FAIL at HEAD; (7) and (11) pass both before and after.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 FILTER THE GENERIC BRANCH. In `cli._find_type_records`'s generic branch, read `explicit_status = getattr(args, "status", None)`, `explicit_id`, `explicit_set` and, inside the existing per-path loop that already reads `text`, `continue` past a record whose `sel_mod._read_status(text)` differs from `explicit_status`, whose `sel_mod._read_id(text)` differs from `explicit_id`, or whose `sel_mod._read_setid(text)` differs from `explicit_set`, each only when that flag is given. This applies to both the selector and no-selector arms because they share the loop. Use the same readers the branch already uses for display, so the filter and the printed status column can never disagree. Do NOT touch the `plans` or `research` branches' filtering (their `query` helpers already apply these flags).
  - Depends on: E-02
  - Expected outcome: E-02 (1)-(4), (8)'s filter and (10) pass.
  - Execution state: pending

- [ ] E-04 VALIDATE `--status` UP FRONT. Add `cli._find_valid_statuses(artifact_type) -> Optional[FrozenSet[str]]` returning the type's canonical enum (specs `attention_contract.SPEC_STATUSES`; backlog `backlog.STATUSES`; releases `frozenset(releases.RELEASE_STATUSES)`; plans `plans.RECOGNIZED | {"pending", "reusable"}` per OQ-02; research `research_contract.STATUSES | set(research_contract.STATUS_NORMALIZATIONS)`) or `None` for a type with no enum. In `cli._run_find`, after `types` is computed and BEFORE the scan loop, when `--status` is given: collect the enums of the resolved types (skipping `None`); if at least one type has an enum and the value is in none of them, refuse. Render the refusal as a `CommandResult(command="find", status="cannot-run", exit_code=2, ...)` on the `--agent`/`--json` surfaces and as `term.status("fail", ...)` plus return 2 on the human and `--paths` surfaces (stdout stays empty so a `-p` consumer sees no path). The message names the value, the type(s), and the sorted valid values. For `all`, the union of enums is the valid set, so a status that only one type carries still filters the others to nothing, which is correct.
  - Depends on: E-03
  - Expected outcome: E-02 (5), (6), (9) pass; (7) passes.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 RE-RUN E-01's live commands and paste counts and exit codes, and run `python3 -m pytest tests/test_find_filters.py -o addopts="" -q`.
  - Depends on: E-04
  - Expected outcome: `specs --status to-review` equals the live number of to-review specs (2 at authoring; re-derive); `specs --id 4sd62s` is 1; `backlog --set closescope` equals the live count of that Set's items; the three bogus-status runs exit 2; `plans --status approved` unchanged from E-01.
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
- The old find tests were deleted in `19313eed` (`tests/test_cli_find.py` 688 lines and `tests/test_find_collision_surface.py`); the surviving `tests/test_cli_find.py` covers research status only.
- Spec `4sd62s` (artifact metadata store, `reviewed`) will replace `aw find`'s scanning with a SQLite cache; `tests/test_find_filters.py` is written against the CLI surface, not internals, so it survives that rewrite and defines what it must preserve.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only. Bare `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `f46b6775` (row counts from `aw find ... | wc -l`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `cli._find_type_records` generic branch | `--status` ignored. | `find specs` 38; `find specs --status to-review` 38; live spec statuses: to-review 2, approved 13, implemented 15, ... |
| F-2 | HIGH | same | `--id` ignored. | `find specs --id 4sd62s` 38 |
| F-3 | HIGH | same | `--set` ignored. | `find backlog` 617; `find backlog --set closescope` 617; one backlog record carries `- Set: closescope` |
| F-4 | MEDIUM | `cli._run_find` (all branches) | An invalid `--status` is accepted silently at exit 0. | `find specs --status bogusvalue` exit 0 (38 rows); `find plans --status bogusvalue` exit 0 "no matching plans"; `find research --status bogus` exit 0 "no matching research" |
| F-5 | INFO | control | Plans filter correctly. | `find plans --status approved` 24 lines, a strict subset |
| F-6 | INFO | tests | No test covers the filter flags on the generic branch. | `tests/` holds only `test_cli_find.py` (94 lines, research status) |

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
- Resolution or deferral rationale: FILTER without validation, from repository evidence: the generic branch already reads and DISPLAYS `_read_status` for every type, so filtering on the displayed value is consistent, while refusing would need an enum that does not exist in code for those types (see Deferred). Ignoring is the defect itself.

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
  - Required evidence: paste the generic-branch diff and the test run showing (1)-(4), (8), (10) passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `_find_valid_statuses` / `_run_find` diff; paste `aw find specs --status bogusvalue --json` showing `"exit_code": 2` and the valid values, and the human-surface message with `echo $?` printing 2; paste the full test file passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the E-01 commands re-run with counts and exit codes, each filtered count compared against a direct count (for example `grep -rl "^- Status: to-review" .aw/records/specs | wc -l`).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw find` starts honoring `--status`, `--id` and `--set` for specs, backlog, releases, prompts, walkthroughs, roadmaps, comms, reviews and other (today they are ignored), and `--status` with a value outside the type's enum is refused at exit 2 for every type that has an enum, including plans and research (today such a value exits 0). This is a user-visible behavior change: a script that relied on `--status` doing nothing will now get filtered output, and one passing a misspelled status will now get exit 2. Graduates backlog `faov03` and inherits its `- Blocks-Release: next`. Runs after `qfpnrm` (`- Item-Dependencies: executed:qfpnrm`), which restructures the same function.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/cli.py` (`_find_type_records`' generic branch, a new `_find_valid_statuses`, and the validation step in `_run_find`) and the new `tests/test_find_filters.py`. If an edit outside those paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-02 must show the new tests FAILING before the fix.

Commit ONLY through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize`. Then add the `aw specs note` on `6m4kow` described in the spec-sync section, and close backlog `faov03` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
