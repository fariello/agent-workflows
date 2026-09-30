# IPD: Finish the aw set research vocabulary fix: accept the intake alias and refuse a hot target that would strand a cold-sharded doc

- Date: 2026-09-28
- Kind: child
- Concern: `aw set`'s research status vocabulary is now DERIVED but still incomplete in two measured ways: it refuses the `intake` alias that `research_contract.STATUS_NORMALIZATIONS` exists to accept, and it writes a hot status onto a doc physically sitting in a cold shard without moving it and with no checker that notices.
- Scope: `status_set.normalize_target_status` (the shared alias helper, guarded to research) and the research branch of `status_set.validate_transition_allowed`, plus its `tests/test_status_set.py` coverage, which includes repairing the one pre-existing test the new refusal necessarily breaks (F-12). Adds a normalization call and one placement-aware refusal. Does NOT touch `aw research promote`, the shard layout, the `research_contract` vocabularies, or the 35 pre-existing cold-status-at-hot-root docs (see Deferred).
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 5u7mug
- Blocks-Release: next
- Set: resvocab
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 4a8yws
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): plan-review: revisions applied; PR-801..PR-805 fixed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801 (blocker), PR-802 (high), PR-803, PR-804, PR-805 (low), all FIXED. Findings recorded in `.aw/records/reviews/20260928-resvocab-01-4a8yws-...review.md`. Every measured claim F-1..F-10 reproduced exactly, including the 123/64/59 corpus split and the 35 cold-at-hot docs. Two authored items were unworkable as written. PR-801: the plan promises all four pre-existing tests pass unmodified, which is impossible, because `create_research`'s DEFAULT disposition is a cold shard and `test_set_active_writes_status_for_report` therefore asserts exactly the write E-02 must refuse (proven `AssertionError: 1 != 0`); F-11's claim that the fixture cannot shard is false, and E-03 now owns the one-argument repair. PR-802: E-01's authored change site passes validation and then writes `status: intake`, the legacy spelling it exists to eliminate, because `apply_status_change` re-normalizes independently; the change moved to the shared `normalize_target_status` (new OQ-02 records the widened blast radius). Also corrected a mis-cited symbol (`_shard_subpath` cannot classify a path) and confirmed E-02's remedy is not a dead end (`promote --to active --apply` does move a doc back to the hot root).
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `5u7mug`; both defects the item measured are already fixed by executed plan `5e3nj2`, so this plan re-scopes to the two residual gaps measured 2026-09-28 against this worktree.
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Close the two residual defects in `aw set`'s research status handling that executed plan `5e3nj2` left behind, so the setter accepts every status a research doc can legitimately hold (including the `intake` alias the contract already normalizes) and never writes a status that contradicts the file's physical tier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: accept the alias the contract already defines

- [x] E-01 Teach the research alias to `status_set.normalize_target_status`, the SHARED helper, by routing a research token through `research_contract.normalize_status`, so the `intake` alias resolves to canonical `todo` instead of being refused. Today that helper only rewrites `done`/`pending` and only `for record_type in ("plans", "prompts")`, so no research alias is ever applied, while `research_contract.STATUS_NORMALIZATIONS` is `{"intake": "todo"}` and its docstring states that read sites call `normalize_status(raw).value` "BEFORE any map/compare/band selection"; the setter is the one WRITE site that does not, which is the defect. Keep the derivation intact: do not re-list statuses, and leave `TYPE_STATUSES["research"] = set(_research_contract.HOT_STATUSES)` as-is.

  THE CHANGE SITE IS THE SHARED HELPER, NOT `validate_transition_allowed`, AND THIS IS LOAD-BEARING RATHER THAN A PREFERENCE. The authored version named `validate_transition_allowed`, and measured at review that is INSUFFICIENT for this item's own requirement: `apply_status_change` (the function that actually writes the file) calls `normalize_target_status(target_status, rec.record_type)` INDEPENDENTLY on the RAW target, so normalizing inside the validator makes `intake` pass validation and then writes the literal legacy spelling. Simulated against the shipped code, the validator-only change gave `aw set intake sc0002 -> exit 0` with the file reading `status: intake`, which is precisely the outcome this item forbids; patching the shared helper instead gave `status: todo`. `normalize_target_status` has 13 call sites, all inside `status_set.py` and none elsewhere, including the two `--dry-run`/agent preview `detail=f"status: ... -> {normalize_target_status(...)}"` sites that V-01's "TARGET is `todo`, not `intake`" requirement depends on, so the one helper is the only site that satisfies validation, the write, and the preview together. Verified at review that patching the helper leaves the full suite green (`3246 passed, 2 skipped`).
  - Depends on: none
  - Expected outcome: `aw set intake <research-id6>` exits 0 and writes `status: todo` (never `status: intake`), the dry-run preview names `todo` as the target, and `aw set done|open|parked <research-id6>` still exits 1 with the existing `is not valid for research` message.
  - Execution state: performed

### Task group 2: refuse a hot target that would strand a cold-sharded doc

- [x] E-02 In the research branch of `status_set.validate_transition_allowed`, refuse a HOT target (`todo`/`active`) when the record's path is inside a cold shard tier, naming `aw research promote <id6> --to <status>` exactly as the existing cold-target refusal does. Judge the tier from `rec.path` relative to the resolved research root using the directory names the contract already owns (`research_contract.REFERENCE_DIR`, `research_contract.ARCHIVE_DIR`) and `research_contract.resolve_research_root`; do not hardcode the strings `"reference"`/`"archive"` a second time. The tier test is "the first path segment below the research root is one of those two directory names", which needs NO shard-month arithmetic at all: ignore the authored instruction to reuse `research_archive._shard_subpath`, which measured at review is the WRONG symbol for this job (its signature is `_shard_subpath(status: str, created: str)`, so it computes a DESTINATION from a status plus a date and returns `None` for any hot status; it cannot answer "which tier is this file in?" from a path). The reason a refusal is needed at all is mechanical and is the SAME reason `5e3nj2` E-09 gave for refusing a cold target: re-measured at review, `record_placement.has_lifecycle_subdirs("research")` is `False` and `record_placement.target_subdir("research", s)` returns `None` for all four of `todo`/`active`/`reference`/`archive`, so `aw set` writes the status line and CANNOT move the file. `5e3nj2` blocked the cold direction and left the hot direction open, which is an asymmetry in one guard rather than a new subsystem. `rec.path` and the optional `repo_root` are both available in this function, so the tier can be resolved without a new parameter.

  THE REMEDY THE MESSAGE NAMES IS VERIFIED TO WORK, which matters because this refusal points at a DIFFERENT promote direction than the shipped cold-target refusal does. F-3 measured only `promote --to reference`; this item's message sends the user to `promote --to <hot status>`. Confirmed at review end to end: `aw research promote sc0001 --to active` and `--to todo` both preview exit 0, and `--to active --apply` moved the doc out of `reference/202609/` back to the hot root (`still in cold shard: False`). So the refusal is not a dead end (F-13).
  - Depends on: E-01
  - Expected outcome: `aw set active <id6-of-a-doc-in-reference/YYYYMM>` exits 1, changes no bytes, and names `aw research promote`. A hot target on a doc at the hot root is unaffected and still succeeds.
  - Execution state: performed

- [x] E-03 FIRST REPAIR THE ONE PRE-EXISTING TEST E-02 NECESSARILY BREAKS, then add the new coverage. The authored version of this item was built on a false premise and promised something impossible, both measured at review, so read this paragraph before touching the file.

  THE FIXTURE ALREADY SHARDS, AND ITS DEFAULT IS A COLD SHARD. The authored text says `create_research` "writes into `self.repo_root / '.aw' / 'records' / 'research'` with no shard component" and so "cannot place a doc in a shard at all". Measured, its signature is `create_research(filename, id6, set_id, status="active", kind="research-report", disposition="reference/202609")`, and it builds `base / disposition / filename`. So sharding is ALREADY supported and `reference/202609` is the DEFAULT; no fixture extension is required, and the correct way to place a doc at the HOT ROOT is the explicit `disposition=""` that `test_set_hot_status_on_prompt_refuses` already passes.

  CONSEQUENCE, AND IT IS A HARD CONFLICT RATHER THAN A DETAIL: because the default is a cold shard, `test_set_active_writes_status_for_report` sets the HOT status `active` on a doc sitting in `reference/202609` and asserts exit 0 plus `status: active` written. That is EXACTLY the write E-02 must refuse, so the authored promise that the four existing tests "must pass unmodified" is unsatisfiable. Proven at review by injecting the E-02 guard over the shipped `validate_transition_allowed` and running the class: `test_set_active_writes_status_for_report FAILED` with `AssertionError: 1 != 0` at `tests/test_status_set.py:2541`, the other three PASSED, and a full-suite run under the same injection reported `1 failed, 3245 passed` (so this is the ONLY collision in the tree). REPAIR IT by passing `disposition=""` so the doc sits at the hot root, which preserves the behavior that test exists to pin (a hot status IS writable on a hot-root report) and is the minimal edit; do NOT weaken its assertions and do NOT delete it. The other three cases pass untouched: two assert refusals that E-02 cannot affect, and the prompt case already uses `disposition=""`.

  THEN ADD the new outcome tests, each asserting on exit code AND on the file's bytes: (a) `intake` accepted and written as `todo` (not `intake`), which is the E-01 regression guard the review found the authored change site would have failed; (b) a hot target on a cold-sharded doc refused, byte-unchanged, with the `aw research promote` message; (c) a hot target on a hot-root doc still accepted, the guard that E-02 did not over-refuse. Show (a) and (b) FAILING against HEAD before the fix and paste that output in V-03.
  - Depends on: E-01, E-02
  - Expected outcome: three new tests; `test_set_active_writes_status_for_report` repaired by a one-argument `disposition=""` change with its assertions intact; the other three pre-existing cases byte-untouched; the full `tests/test_status_set.py` green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- DERIVE A VOCABULARY, NEVER RE-LIST IT. `status_set.TYPE_STATUSES` carries this as an explicit comment on three rows: `specs` is "DERIVED from `lifecycle_dirs.LIFECYCLE_SUBDIRS[\"specs\"]`, never re-listed", `backlog` is "DERIVED from `backlog.STATUSES`" and "identical by construction (GUIDING_PRINCIPLES P8)", and `research` is "DERIVED from `research_contract.HOT_STATUSES`". This plan preserves that property: it adds a normalization CALL and a placement refusal, and re-lists nothing.
- The research contract is OWNED by `research_contract`, which is pure and side-effect free by design ("no side effects: it does not read the filesystem, call a model, use the network, or write anything"). E-02 therefore reads the filesystem in `status_set`, not by adding I/O to the contract module.
- A refusal message should name the verb that CAN do the job. The existing cold-target refusal reads "Setting research status to '<s>' is not supported via aw set; use 'aw research promote <id> --to <s>' instead."; E-02 mirrors that shape rather than inventing a second wording.
- `aw set` is reached by two spellings and a gate installed in only one is bypassed by choosing the other; `validate_transition_allowed`'s own comments record this for specs (the positional form routes here while `--status` routes to `specs.run_set`). Research has no forked setter, so the single guard in this function is sufficient for research, which is why this plan touches one function.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | BOTH defects the backlog item measured are ALREADY FIXED, so the item as written is stale. The item reports `TYPE_STATUSES["research"]` as `{'active','done','open','parked'}`; measured now it is `{'active','todo'}`, derived from `research_contract.HOT_STATUSES`. | `python3 -c "from agent_workflows import status_set as s; print(sorted(s.TYPE_STATUSES['research']))"` -> `['active', 'todo']`. Fixed by `5e3nj2` E-09, which names this exact forked set and is `- Status: executed` in `.aw/records/plans/executed/`. |
| F-2 | Half 1 of the item (accepts non-vocabulary words) is fixed: `done`, `open`, `parked` are all refused, exit 1, no bytes changed. | `aw set done cnkyvn --dry-run` -> exit 1, "Status 'done' is not valid for research (valid: ['active', 'todo'])". Same for `open` and `parked`. |
| F-3 | Half 2 (refuses the real vocabulary) is fixed for all four statuses, but by two different routes: `todo`/`active` are accepted by `aw set`, while `reference`/`archive` are deliberately redirected to `aw research promote`, which works. | `aw set todo cnkyvn --dry-run` -> exit 0, `reference -> todo`. `aw set reference cnkyvn --dry-run` -> exit 1 naming `aw research promote cnkyvn --to reference`. `aw research promote cnkyvn --to reference` -> exit 0, "would set cnkyvn status=reference and move to reference/202607/...". |
| F-4 | RESIDUAL GAP 1: the `intake` alias is refused by the setter, though the contract exists to accept it. `research_contract.STATUS_NORMALIZATIONS` is `{'intake': 'todo'}` and `normalize_status` applies it; `status_set.normalize_target_status` applies aliases only for `("plans", "prompts")`, so the research branch never normalizes. | `aw set intake cnkyvn --dry-run` -> exit 1, "Status 'intake' is not valid for research (valid: ['active', 'todo'])". |
| F-5 | RESIDUAL GAP 2: `aw set` writes a HOT status onto a doc living in a cold shard and does not move the file, leaving status and physical tier contradicting each other. Measured in a scratch repo on a doc at `reference/202609/`. | `aw set active sc0001` -> exit 0, printed `reference -> active`; afterwards `status: active` while the file is still at `.aw/records/research/reference/202609/20260905-scr-01-sc0001-cold-doc.research-report.md`. |
| F-6 | F-5's root cause is the same one `5e3nj2` cited for blocking the cold direction, so the hot direction is an asymmetry in one guard, not a new problem. | `record_placement.has_lifecycle_subdirs("research")` is `False`; `target_subdir("research", s)` is `None` for `todo`, `active`, `reference`, `archive`. `5e3nj2` records the same measurement and concludes "`aw set` would write a cold status WITHOUT moving the file into its shard". |
| F-7 | NOTHING DETECTS the F-5 state, so it is silent rather than merely wrong. In a scratch repo that is clean before the write, `aw research index --check` is still clean after it. | Baseline `aw research index --check` -> exit 0, "index --check: clean". After `aw set active` strands the doc, regenerate index then `--check` -> exit 0, "index --check: clean". |
| F-8 | The stranding is currently only reachable through the bug, not pre-existing in the corpus: of 123 conformant docs (64 in cold shards, 59 at the hot root), ZERO carry a hot status inside a cold shard. So E-02 refuses a state no live doc is in, and needs no migration. | Corpus scan over the resolved research root comparing normalized `status` against physical tier: "HOT status sitting in COLD shard: 0". |
| F-9 | The MIGRATION QUESTION the backlog item attached ("any existing doc already carrying one needs a migration answer") is ANSWERED BY THE CORPUS: no doc carries `done`, `open`, `parked`, or `intake`. So the three non-vocabulary words need no alias and no backfill, and E-01 adds only the alias the contract already declares. | Raw frontmatter `status` census over the research root: `{'reference': 67, 'todo': 13, 'active': 4, 'archive': 32}`. `grep -rn "^status: \(done\|open\|parked\)"` over the tree returns nothing. |
| F-10 | A SEPARATE, PRE-EXISTING defect is visible in the same scan and is deliberately NOT fixed here: 35 docs carry a cold status (`reference`/`archive`) while sitting at the hot root. Shard-month placement is exact (0 mismatches) for those that are sharded, so this is a tier problem only. | Corpus scan: "COLD status sitting at HOT root: 35", "SHARD-MONTH mismatches (exact path): 0". Example: `20260726-awdeliv-00-cnkyvn-...research-report.md` is `status: reference` at the root. Unfiled when measured; filed during authoring as backlog `zdsf35` and carried in Deferred. Classed `chore` not `bug`, because the readers key on STATUS and not path: `aw find research reference` locates all 35 correctly, so the layout contradicts `.aw/records/research/README.md` without producing a wrong answer. |
| F-11 | Test coverage for research in `aw set` exists but pins only what `5e3nj2` shipped: four cases in `ResearchStatusSetTests` (`done` refused, `active` written, `reference` redirected, hot-on-prompt refused), and no test covers an alias. CORRECTED AT REVIEW: the second half of this row was FALSE. `create_research` already shards, so no fixture extension is owed; see F-12 for what that actually implies, which is worse than a wasted step. | `tests/test_status_set.py` class `ResearchStatusSetTests`; the four method names verified present. Helper signature measured: `create_research(filename, id6, set_id, status="active", kind="research-report", disposition="reference/202609")`, building `base / disposition / filename`, so a shard is not merely possible but is the DEFAULT. `grep -rn "TYPE_STATUSES" tests/` matches only `test_lifecycle_dirs.py` (specs) and an unrelated comment. |
| F-12 | REVIEW FINDING (new, BLOCKER): because the fixture's default disposition IS a cold shard, one pre-existing test asserts exactly the write E-02 must refuse, so the plan's promise that all four pass "unmodified" is unsatisfiable and E-02 cannot land without a test repair. | `test_set_active_writes_status_for_report` calls `create_research(...)` WITHOUT `disposition`, taking the `reference/202609` default, then asserts `rc == 0` and `status: active`. Injected the E-02 guard over the shipped `validate_transition_allowed` and ran the class: `test_set_active_writes_status_for_report FAILED`, `AssertionError: 1 != 0` at `tests/test_status_set.py:2541`; the other three PASSED. Full suite under the same injection: `1 failed, 3245 passed, 2 skipped`, confirming it is the only collision. E-03 now owns the repair (`disposition=""`, assertions intact). |
| F-13 | REVIEW FINDING (new, LOW, reassuring): E-02's refusal message points at a promote direction F-3 never measured, so it was worth confirming it is not a dead end. It is not. | F-3 measured only `promote --to reference`. Measured at review on a doc in `reference/202609`: `aw research promote sc0001 --to active` and `--to todo` both preview exit 0, and `--to active --apply` printed `active: sc0001 -> ...` with `still in cold shard: False` and the file present at the hot root. So a user refused by E-02 has a working remedy. |
| F-14 | REVIEW FINDING (new, HIGH): E-01's authored CHANGE SITE does not satisfy E-01's own stated requirement, and would have written the legacy spelling the item exists to prevent. | `apply_status_change` calls `normalize_target_status(target_status, rec.record_type)` INDEPENDENTLY of the validator. Patching `validate_transition_allowed` alone: `aw set intake sc0002 -> exit 0` and the file reads `status: intake`. Patching the shared `normalize_target_status` instead: the file reads `status: todo`. 13 call sites, all within `status_set.py`, including the two preview `detail=` sites V-01 depends on. Full suite green under the shared-helper patch (`3246 passed, 2 skipped`). E-01 corrected. |
| F-15 | REVIEW FINDING (new, LOW): E-02 mis-cites the symbol it says already owns the needed math. | `research_archive._shard_subpath(status: str, created: str)` computes a DESTINATION subpath from a status plus a created date and returns `None` for a hot status (`_shard_subpath('active','20260905') -> None`); it takes no path and cannot classify a file's current tier. The tier test E-02 needs is a first-path-segment comparison against `REFERENCE_DIR`/`ARCHIVE_DIR` and involves no shard-month arithmetic. E-02 corrected to say so. |
| F-16 | REVIEW FINDING (new, LOW): F-7's "NOTHING DETECTS" claim is CORRECT, and the one finding `aw check research` reports is unrelated, which is worth recording so an executor does not mistake it for detection. | Before the stranding, `aw check research --agent` reported exit 0 with `findings: 1`, the single diagnostic being `{"location":"<collisions>","rule":"check.collisions-not-checked"}`. After the stranding, byte-identical output. `aw research index --check --agent` emitted nothing (clean) after the stranding. |
| F-17 | The F-14 baseline the plan compares against has moved, so the bar must be re-derived. | Bare `python3 -m pytest` at review on this lane worktree: `3246 passed, 2 skipped, 3 warnings`. Focused `tests/test_status_set.py`: `79 items`, all pass (`4 passed, 75 deselected` for the `ResearchStatusSetTests` subset). |

## Proposed changes (ordered, validatable)

1. E-01: normalize a research target through `research_contract.normalize_status` inside the SHARED `status_set.normalize_target_status`, so validation, the write, and the preview all agree. Closes F-4; corrected per F-14. Validated by V-01.
2. E-02: refuse a hot target when the record sits in a cold shard tier, with a message naming `aw research promote`, deriving the tier directory names from `research_contract` by a first-path-segment test. Closes F-5/F-7; corrected per F-15; remedy confirmed by F-13. Validated by V-02.
3. E-03: repair `test_set_active_writes_status_for_report` (which E-02 necessarily breaks, F-12) then add three outcome tests (alias written as `todo`, hot-on-cold refused, hot-on-hot still accepted), shown failing against HEAD first. Closes F-11/F-12. Validated by V-03.

## Deferred / out of scope (with reason)

- The 35 docs carrying a cold status at the hot root (F-10) are NOT migrated or fixed here. They are a pre-existing corpus state with a different cause (this plan's E-02 refuses the write direction that would CREATE the mirror-image state; it does not move existing files), the remedy is a bulk `aw research promote` pass, and doing it here would mean this plan edits 35 records outside its `- Scope-Paths:`.
  - Carrier: zdsf35
- No new `aw check` / `aw research index --check` DRIFT rule for a status-versus-tier mismatch. F-7 shows one is warranted, and spec `5tapom` Section 5 item 2 already contemplates drift rules in that checker, but a checker rule would fire on all 35 F-10 docs immediately and so cannot land before that migration. Refusing the bad WRITE (E-02) is the part that is safe to ship alone, which is why the rule is carried with the migration rather than here.
  - Carrier: zdsf35
- No change to `aw research promote`, the shard layout, `research_contract`'s vocabularies, or `record_placement`'s research placement. F-3 shows `promote` already works for both cold statuses; teaching `record_placement` about research shards would make `aw set` able to MOVE research docs, which is a redesign of the promote/set split that `5e3nj2` deliberately decided, not a bug fix.
  - Carrier-Declined: Nothing is owed. This row records a PROHIBITION on this plan rather than outstanding work: `aw research promote` already performs both cold transitions correctly (F-3, measured), so there is no defect here to carry. Whether `aw set` should ever move a research doc is a settled design split, not deferred debt; reopening it would need a maintainer decision about the promote/set boundary, and naming a carrier would assert an obligation that does not exist.
- No `done`/`open`/`parked` aliases for research. F-9 shows no doc carries them and they are not research concepts, so mapping them would invent vocabulary rather than accept an existing spelling.
  - Carrier-Declined: No future work is owed, and filing an item would misrepresent a settled decision as an outstanding task. The backlog item asked for an explicit migration answer for these three words; the corpus ANSWERS it (raw status census is `reference`/`todo`/`active`/`archive` only, zero occurrences of the three), so there is no population to migrate and no alias to add. Recorded here so a reviewer does not read the silence as the question having been skipped.

## Scope check

- Over-scope: none. Two files and one test class, but NOT one function: corrected at review, E-01 changes `status_set.normalize_target_status` (the shared helper) while E-02 changes `status_set.validate_transition_allowed`, so two functions in the one in-scope module. That E-01 touches a helper shared by EVERY record type is the one widened blast radius in this plan, which is why V-01 additionally requires evidence that plans' `done`/`pending` aliasing is unaffected; the change is guarded to `record_type == "research"` and measured green across the full suite at review.
- Under-scope: this plan does not make the F-10 population consistent and adds no checker rule, so a status-versus-tier mismatch created by any route OTHER than `aw set` (a hand edit, or the 35 existing docs) remains undetected. That is stated as the deliberate boundary above, not as an oversight; the backlog item `5u7mug` is about `aw set`'s vocabulary, and both residual gaps this plan fixes are in `aw set`.

## Required tests / validation

`python3 -m pytest tests/test_status_set.py` for the focused surface, then the BARE full suite (`python3 -m pytest`) last, with the actual `N passed` summary pasted and compared against a baseline RE-RUN at execution time rather than a digit written here (measured at review: `3246 passed, 2 skipped`, F-17). The E-01 and E-02 tests must be shown FAILING against HEAD before the fix, with that output pasted in V-03. THREE of the four pre-existing `ResearchStatusSetTests` cases must pass BYTE-UNMODIFIED; the fourth, `test_set_active_writes_status_for_report`, REQUIRES the one-argument `disposition=""` repair because E-02 necessarily refuses what it currently asserts (F-12), and V-03 must show its assertions were preserved rather than weakened. `tests/test_lifecycle_dirs.py` plus `tests/test_research_archive.py` must stay green as the guard that the derivation and the promote path were not disturbed. Live-corpus read-only checks: `aw set intake <id6> --dry-run` and `aw set active <id6-in-a-reference-shard> --dry-run` before and after, plus a re-run of the F-8 corpus scan to confirm it still reports zero hot-in-cold docs (re-measured at review: 123 conformant docs, 64 cold / 59 hot, `HOT status sitting in COLD shard: 0`).

## Spec / documentation sync

Spec `5tapom` (`.aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md`) is NOT amended and is deliberately NOT in `- Scope-Paths:`. Its Section 4 non-goal already reads "No change to the filename grammar, the four `status` values ..., the shard layout", and this plan changes none of those: it accepts an alias the contract already declares and refuses a write that contradicts the shard layout the spec preserves. Both changes move the code TOWARD that spec's H2 ("state must be genuinely tool-owned, i.e. advanced and validated by tooling"), so no contract text changes. `.aw/records/research/README.md` is also unchanged: its status table already lists "`todo` (legacy `intake`)" and states that hot states stay flat at the root while cold states live in monthly shards, which is exactly the rule E-02 enforces; the README documented the intended behavior correctly and the code was the part that diverged.

## Open questions

### OQ-01: Is the backlog item's attached migration question ("any existing doc already carrying one needs a migration answer") answered?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE at authoring, which is why it is not left for the maintainer. The item required an explicit decision on whether `done`/`open`/`parked` become aliases or are dropped, "because any existing doc already carrying one needs a migration answer". The corpus answers it: the raw frontmatter `status` census over the research root is `{'reference': 67, 'todo': 13, 'active': 4, 'archive': 32}` and a grep for `^status: (done|open|parked)` returns nothing (F-9). ZERO docs carry any of the three, so no migration is owed and no alias is justified; mapping them would invent vocabulary. The one alias that IS justified is `intake`, because `research_contract.STATUS_NORMALIZATIONS` already declares it and the contract's own docstring says every read site applies it (F-4), so E-01 accepts an existing spelling rather than inventing one. The separate F-10 tier inconsistency found while measuring this is filed as backlog `zdsf35` and carried in Deferred.

### OQ-02: E-01 must change a helper shared by every record type. Is that acceptable, or should research get its own normalization path?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT REVIEW BY DEMONSTRATION: change the SHARED `status_set.normalize_target_status`, guarded to `record_type == "research"`. It is raised as a question because the authored plan described a narrower change site and a reviewer widening a shared helper is a judgement a maintainer may want to see. The narrow option was MEASURED AND FAILS THE ITEM'S OWN REQUIREMENT: `apply_status_change` re-derives the written value by calling `normalize_target_status` on the RAW target independently of the validator, so patching `validate_transition_allowed` alone yields `exit 0` with `status: intake` on disk, the legacy spelling E-01 exists to eliminate (F-14). A third option, teaching BOTH functions separately, was rejected as a forked predicate: it puts the same aliasing rule in two places, which is the desync shape `TYPE_STATUSES`' own "DERIVED, never re-listed" comments exist to prevent, and it would still miss the two `--dry-run`/agent preview `detail=` sites that also call the helper and that V-01's preview assertion depends on. The shared helper is the ONLY site where validation, the write, and the preview agree by construction. BLAST RADIUS, stated rather than assumed: the helper serves every record type and has 13 call sites, all inside `status_set.py` and none elsewhere, so the risk is that a research guard leaks into another type's aliasing; the guard is an explicit `record_type == "research"` branch beside the existing `("plans", "prompts")` one, and the full suite was green under exactly this patch at review (`3246 passed, 2 skipped`). V-01 additionally requires pasted evidence that plans' `done -> executed` and `pending -> to-review` still resolve. Reversible: yes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: STATE WHICH FUNCTION WAS CHANGED and confirm it is the shared `normalize_target_status` and not `validate_transition_allowed` alone (F-14: the latter passes validation and then writes `status: intake`, the exact legacy spelling this item forbids). Paste the full command and output of `aw set intake <research-id6> --dry-run` showing exit 0 and a transition line whose TARGET is `todo` (not `intake`), plus the applied (non-dry-run) run on a scratch or fixture doc showing `status: todo` in the file afterwards via a pasted `grep -n "^status:"`. That written-bytes check is the load-bearing one: a validator-only change passes the dry-run assertion and still fails here. Also paste `aw set done <id6> --dry-run` and `aw set parked <id6> --dry-run` still exiting 1 with `is not valid for research`, proving the alias did not widen the accepted set, and confirm no NON-research type's aliasing changed (paste the `plans` `done -> executed` and `pending -> to-review` cases still resolving, since the shared helper serves every type). Paste `python3 -c "from agent_workflows import status_set as s; print(sorted(s.TYPE_STATUSES['research']))"` still printing `['active', 'todo']`, proving the derivation was not replaced by a hand-listed set.
  - Observed evidence: Verified function changed to shared normalize_target_status; dry-run target is todo; applied write yields status: todo; invalid targets refused; non-research aliasing preserved.
    1. Function changed: `status_set.normalize_target_status` (the shared helper) was changed, guarded to `record_type == "research"`, routing via `_research_contract.normalize_status(norm)`. `validate_transition_allowed` was not modified for normalization alone.
    2. Dry-run output:
    ```
    $ aw set intake fedqe6 --dry-run
    aw: invoked in checkout .../agent-workflows/.aw/worktrees/4a8yws but imported agent_workflows from .../agent-workflows; re-running with .../.aw/worktrees/4a8yws's package (set AW_NO_REEXEC=1 to disable)
    -    research    20260922-runresidue-00-fedqe6  active → ◕  todo  (dry-run)
    Exit code: 0
    ```
    Target is canonical `todo` (not `intake`), exit 0.
    3. Applied non-dry-run on fixture doc:
    ```
    BEFORE:
    3:status: active
    SET RC: 0
    OUTPUT: -    research    20260928-test-01-tst001  active → ◕  todo
    AFTER:
    3:status: todo
    ```
    Grep shows `status: todo` written to disk.
    4. Rejected non-vocabulary targets:
    ```
    $ aw set done fedqe6 --dry-run
    FAIL     Validation error on 20260922-runresidue-00-fedqe6-runner-residue-per-symbol-decisions.findings.md: Status 'done' is not valid for research (valid: ['active', 'todo']). Refusing before making changes.
    Exit code: 1

    $ aw set parked fedqe6 --dry-run
    FAIL     Validation error on 20260922-runresidue-00-fedqe6-runner-residue-per-symbol-decisions.findings.md: Status 'parked' is not valid for research (valid: ['active', 'todo']). Refusing before making changes.
    Exit code: 1
    ```
    5. Non-research type aliasing preserved:
    ```
    $ python3 -c "from agent_workflows.status_set import normalize_target_status; print('done ->', normalize_target_status('done', 'plans')); print('pending ->', normalize_target_status('pending', 'plans'))"
    done -> executed
    pending -> to-review
    ```
    6. Vocabulary derivation preserved:
    ```
    $ python3 -c "from agent_workflows import status_set as s; print(sorted(s.TYPE_STATUSES['research']))"
    ['active', 'todo']
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the command and output of `aw set active <id6-of-a-doc-under-reference/YYYYMM>` (or the fixture equivalent) showing exit 1 and a message naming `aw research promote <id6> --to active`, AND evidence the file is byte-unchanged (a pasted `git diff --stat` showing no change, or a before/after `sha256sum`). Separately paste a hot target on a HOT-ROOT doc still exiting 0 with the status written, proving the refusal is placement-scoped and did not break the normal path. Confirm the tier test uses a first-path-segment comparison against `research_contract.REFERENCE_DIR`/`ARCHIVE_DIR` and that `research_archive._shard_subpath` was NOT used (F-15: wrong signature for this job). Paste the ESCAPE-HATCH check, so the refusal is demonstrably not a dead end: `aw research promote <same-id6> --to active --apply` exiting 0 and the file moved OUT of the shard to the hot root (F-13 verified this works at review; re-run it here against the changed tree). Also paste the `archive/` tier case, not only `reference/`, since both directory names gate the refusal. Paste the F-8 corpus scan re-run reporting `HOT status sitting in COLD shard: 0`.
  - Observed evidence: Hot target active on reference shard 6zf5av refused naming promote (exit 1, byte-unchanged sha256); hot target on hot root tvnq50 accepted (exit 0); archive shard rrwr0z refused; promote escape hatch confirmed working; corpus scan shows 0 hot in cold shards.
    1. Hot target on doc in reference shard refused, naming promote:
    ```
    $ aw set active 6zf5av --yes
    FAIL     Validation error on 20260810-gemini-actually-validate-playbook-00-6zf5av-gemini-actually-validate-playbook.gpt56medium.research-report.md: Setting research status to 'active' is not supported via aw set; use 'aw research promote 6zf5av --to active' instead.. Refusing before making changes.
    Exit code: 1
    ```
    File byte-unchanged:
    Before sha256: 6be8c3236f40793cc6f51a33b3fc8897ca12f529c3acb1166f27ebe3f3a52140
    After sha256:  6be8c3236f40793cc6f51a33b3fc8897ca12f529c3acb1166f27ebe3f3a52140
    git diff --stat: 0 changes.
    2. Hot target on hot-root doc still accepted:
    ```
    $ aw set active tvnq50 --dry-run
    -    research    20260903-rununify-00-tvnq50  todo → ●  active  (dry-run)
    Exit code: 0
    ```
    3. Tier test confirmation: tier check in `status_set.validate_transition_allowed` resolves research root via `_research_contract.resolve_research_root` and checks `first_seg in (_research_contract.REFERENCE_DIR, _research_contract.ARCHIVE_DIR)`; `research_archive._shard_subpath` was not used.
    4. Escape hatch check (`aw research promote sc0001 --to active --apply`):
    ```
    $ python3 -m agent_workflows.cli research promote sc0001 --to active --apply --dir <temp_repo>
    active: sc0001 -> 20260905-test-01-sc0001-sample.research-report.md
    old file exists: False
    new hot file exists: True
    Exit code: 0
    ```
    Doc moved from `reference/202609/` out to hot root.
    5. Archive tier case refused:
    ```
    $ aw set active rrwr0z --dry-run
    FAIL     Validation error on 20260712-planrev-02-rrwr0z-chatgpt-improved-v1-780-lines.gpt56.research-report.md: Setting research status to 'active' is not supported via aw set; use 'aw research promote rrwr0z --to active' instead.. Refusing before making changes.
    Exit code: 1
    ```
    6. Corpus scan re-run:
    ```
    Total conformant docs: 124
    Cold shard: 64
    Hot root: 60
    HOT status sitting in COLD shard: 0
    COLD status sitting at HOT root: 35
    ```
    `HOT status sitting in COLD shard: 0` confirmed.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the pre-fix FAILING output of the two new tests run against HEAD (the assertion text, not a summary claim), then the post-fix `python3 -m pytest tests/test_status_set.py` output including the `N passed` line, then the BARE `python3 -m pytest` summary line compared against a baseline re-run at execution time (F-17). Paste the `git diff` for `tests/test_status_set.py` and use it to state, per method, the disposition of all four pre-existing `ResearchStatusSetTests` cases: `test_set_done_refuses_for_research`, `test_set_reference_refuses_naming_research_promote` and `test_set_hot_status_on_prompt_refuses` must be BYTE-UNCHANGED, while `test_set_active_writes_status_for_report` is EXPECTED to change by exactly the `disposition=""` argument (F-12) with its `assertEqual(rc, 0)` and its `status: active` assertion intact. Confirm explicitly that `create_research` was NOT extended and no sibling helper was added, because measured at review the helper already shards by default (F-11); if the executor did add one, justify why the existing `disposition` parameter was insufficient. Finally, state that the repaired test still pins the behavior it was written for (a hot status IS writable on a hot-root report) rather than having been weakened into vacuity.
  - Observed evidence: Pre-fix failures captured against HEAD (AssertionError: 1 != 0 for intake alias, AssertionError: 0 != 1 for hot on cold shard, and AssertionError: 1 != 0 for pre-existing test under E-02); post-fix tests/test_status_set.py 82 passed; bare pytest 3249 passed, 2 skipped, 3 warnings (+3 over baseline); git diff shows 3 pre-existing tests byte-unchanged and test_set_active_writes_status_for_report repaired with disposition="".
    1. Pre-fix failing output against HEAD:
    ```
    FAILED tests/test_status_set.py::ResearchStatusSetTests::test_set_intake_alias_writes_todo_for_report - AssertionError: 1 != 0
    Captured stdout: FAIL     Validation error on 20260924-rs0005-01-rs0005-test-report.research-report.md: Status 'intake' is not valid for research (valid: ['active', 'todo']). Refusing before making changes.

    FAILED tests/test_status_set.py::ResearchStatusSetTests::test_set_hot_status_on_cold_sharded_report_refuses - AssertionError: 0 != 1
    ```
    Also confirmed F-12 pre-existing test collision under E-02 before repair:
    ```
    FAILED tests/test_status_set.py::ResearchStatusSetTests::test_set_active_writes_status_for_report - AssertionError: 1 != 0
    Captured stdout: FAIL     Validation error on 20260924-rs0002-01-rs0002-test-report.research-report.md: Setting research status to 'active' is not supported via aw set; use 'aw research promote rs0002 --to active' instead.. Refusing before making changes.
    ```
    2. Post-fix `python3 -m pytest tests/test_status_set.py` output:
    ```
    82 passed in 4.03s
    ```
    3. Bare `python3 -m pytest` full suite run:
    Baseline run at execution turn start:
    `3246 passed, 2 skipped, 3 warnings in 95.82s (0:01:35)`
    Post-fix run:
    `3249 passed, 2 skipped, 3 warnings in 53.44s`
    (+3 passed tests: `test_set_intake_alias_writes_todo_for_report`, `test_set_hot_status_on_cold_sharded_report_refuses`, `test_set_hot_status_on_hot_root_report_accepted`).
    4. Git diff for `tests/test_status_set.py` and pre-existing cases disposition:
    - `test_set_done_refuses_for_research`: BYTE-UNCHANGED
    - `test_set_reference_refuses_naming_research_promote`: BYTE-UNCHANGED
    - `test_set_hot_status_on_prompt_refuses`: BYTE-UNCHANGED
    - `test_set_active_writes_status_for_report`: repaired by adding `disposition="",` to `create_research` with `assertEqual(rc, 0)` and `self.assertIn("status: active", ...)` intact.
    - `create_research` was NOT extended and no sibling helper was added because `create_research` already accepted `disposition`.
    - Repaired test continues to verify that a hot status (`active`) is writable on a hot-root report.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Commit only the `- Scope-Paths:` files through `aw commit 4a8yws -- agent_workflows/status_set.py tests/test_status_set.py`, never `git add -A`, and never push. This plan carries `- Blocks-Release: next`, inherited from backlog `5u7mug`. Because F-1 through F-3 show the item's ORIGINALLY MEASURED defects were already fixed by `5e3nj2`, the executor must re-run the F-4 and F-5 reproductions BEFORE implementing: if either no longer reproduces, stop and report rather than writing a guard for a bug that is gone. Both reproduced at review on 2026-09-29 (`aw set intake` exit 1 `Status 'intake' is not valid for research`; `aw set active` on a `reference/202609` doc exit 0 leaving `status: active` in a cold shard), so the defects had NOT moved as of then.

READ F-12 AND F-14 BEFORE WRITING ANY CODE; they are the two ways this plan as authored would have failed. F-12 is a BLOCKER: the plan promises all four existing tests pass unmodified, and that is impossible, because the test fixture's DEFAULT disposition is a cold shard and one existing test therefore asserts precisely the write E-02 must refuse (proven: `AssertionError: 1 != 0` at `tests/test_status_set.py:2541`). Repair it as E-03 directs rather than discovering the conflict mid-execution and either weakening E-02 or deleting a test. F-14 is the second: E-01's authored change site passes validation and then writes `status: intake`, the legacy spelling the item exists to eliminate, so the change belongs in the shared `normalize_target_status`. Backlog `5u7mug` goes to `graduated`, not `done`, at authoring time; it closes only when this plan is executed and the release gate is provably carried. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is unconditionally owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-03 carry pasted evidence.
