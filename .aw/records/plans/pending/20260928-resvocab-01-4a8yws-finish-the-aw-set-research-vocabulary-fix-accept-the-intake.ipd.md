# IPD: Finish the aw set research vocabulary fix: accept the intake alias and refuse a hot target that would strand a cold-sharded doc

- Date: 2026-09-28
- Kind: child
- Concern: `aw set`'s research status vocabulary is now DERIVED but still incomplete in two measured ways: it refuses the `intake` alias that `research_contract.STATUS_NORMALIZATIONS` exists to accept, and it writes a hot status onto a doc physically sitting in a cold shard without moving it and with no checker that notices.
- Scope: the research branch of `status_set.validate_transition_allowed` plus its `tests/test_status_set.py` coverage. Adds a normalization call and one placement-aware refusal. Does NOT touch `aw research promote`, the shard layout, the `research_contract` vocabularies, or the 35 pre-existing cold-status-at-hot-root docs (see Deferred).
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 5u7mug
- Blocks-Release: next
- Set: resvocab
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 4a8yws

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `5u7mug`; both defects the item measured are already fixed by executed plan `5e3nj2`, so this plan re-scopes to the two residual gaps measured 2026-09-28 against this worktree.
- 2026-09-28 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Close the two residual defects in `aw set`'s research status handling that executed plan `5e3nj2` left behind, so the setter accepts every status a research doc can legitimately hold (including the `intake` alias the contract already normalizes) and never writes a status that contradicts the file's physical tier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: accept the alias the contract already defines

- [ ] E-01 In `status_set.validate_transition_allowed`, route the research target status through `research_contract.normalize_status` before the membership test, so the `intake` alias resolves to canonical `todo` instead of being refused. Today the function compares `normalize_target_status(target_status, rec.record_type)` against `TYPE_STATUSES["research"]`, and `status_set.normalize_target_status` only rewrites `done`/`pending` and only `for record_type in ("plans", "prompts")`, so no research alias is ever applied. `research_contract.STATUS_NORMALIZATIONS` is `{"intake": "todo"}` and its docstring states that read sites call `normalize_status(raw).value` "BEFORE any map/compare/band selection"; the setter is the one WRITE site that does not, which is the defect. The normalized value must be what is written to the file, so a doc set from `intake` lands on `todo` and never on the legacy spelling. Keep the derivation intact: do not re-list statuses, and leave `TYPE_STATUSES["research"] = set(_research_contract.HOT_STATUSES)` as-is.
  - Depends on: none
  - Expected outcome: `aw set intake <research-id6>` exits 0 and writes `status: todo`, while `aw set done|open|parked <research-id6>` still exits 1 with the existing `is not valid for research` message.
  - Execution state: pending

### Task group 2: refuse a hot target that would strand a cold-sharded doc

- [ ] E-02 In the same research branch of `status_set.validate_transition_allowed`, refuse a HOT target (`todo`/`active`) when the record's path is inside a cold shard tier, naming `aw research promote <id6> --to <status>` exactly as the existing cold-target refusal does. Judge the tier from the record path relative to the resolved research root using the directory names the contract already owns (`research_contract.REFERENCE_DIR`, `research_contract.ARCHIVE_DIR`) and `research_contract.resolve_research_root`; do not hardcode the strings `"reference"`/`"archive"` a second time, and do not re-implement the shard math (`research_archive._shard_subpath` already owns it). The reason is mechanical and is the SAME reason `5e3nj2` E-09 gave for refusing a cold target: measured 2026-09-28, `record_placement.has_lifecycle_subdirs("research")` is `False` and `record_placement.target_subdir("research", s)` returns `None` for all four of `todo`/`active`/`reference`/`archive`, so `aw set` writes the status line and CANNOT move the file. `5e3nj2` blocked the cold direction and left the hot direction open, which is an asymmetry in one guard rather than a new subsystem.
  - Depends on: E-01
  - Expected outcome: `aw set active <id6-of-a-doc-in-reference/YYYYMM>` exits 1, changes no bytes, and names `aw research promote`. A hot target on a doc at the hot root is unaffected and still succeeds.
  - Execution state: pending

- [ ] E-03 Add outcome tests to `tests/test_status_set.py` in the existing `ResearchStatusSetTests` class, extending the `create_research` fixture (or adding a sibling helper) so a doc can be created inside a `reference/YYYYMM` shard, which the current helper cannot do: it writes into `self.repo_root / ".aw" / "records" / "research"` with no shard component. Cover, each asserting on exit code AND on the file's bytes: (a) `intake` accepted and written as `todo`; (b) a hot target on a cold-sharded doc refused, unchanged, with the `aw research promote` message; (c) a hot target on a hot-root doc still accepted, which is the regression guard that E-02 did not over-refuse. Show (a) and (b) FAILING against HEAD before the fix, and paste that failure output in V-03. Do not weaken or delete the four existing tests in that class; they pin the behavior `5e3nj2` shipped and must pass unmodified.
  - Depends on: E-01, E-02
  - Expected outcome: three new tests; the full `tests/test_status_set.py` file green, with the pre-existing `ResearchStatusSetTests` cases untouched.
  - Execution state: pending

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
| F-11 | Test coverage for research in `aw set` exists but pins only what `5e3nj2` shipped: four cases in `ResearchStatusSetTests` (`done` refused, `active` written, `reference` redirected, hot-on-prompt refused). No test covers an alias, and the `create_research` helper cannot place a doc in a shard at all, so E-03 must extend the fixture. | `tests/test_status_set.py` class `ResearchStatusSetTests`; helper `create_research` writes to `self.repo_root / ".aw" / "records" / "research"` with no shard component. `grep -rn "TYPE_STATUSES" tests/` matches only `test_lifecycle_dirs.py` (specs) and an unrelated comment. |

## Proposed changes (ordered, validatable)

1. E-01: normalize the research target through `research_contract.normalize_status` in `status_set.validate_transition_allowed` before the `TYPE_STATUSES` membership test, and write the normalized value. Closes F-4. Validated by V-01.
2. E-02: refuse a hot target when the record sits in a cold shard tier, with a message naming `aw research promote`, deriving the tier directory names from `research_contract`. Closes F-5/F-7. Validated by V-02.
3. E-03: extend `ResearchStatusSetTests` and its fixture with three outcome tests (alias accepted, hot-on-cold refused, hot-on-hot still accepted), shown failing against HEAD first. Closes F-11. Validated by V-03.

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

- Over-scope: none. Two files, one function, one test class.
- Under-scope: this plan does not make the F-10 population consistent and adds no checker rule, so a status-versus-tier mismatch created by any route OTHER than `aw set` (a hand edit, or the 35 existing docs) remains undetected. That is stated as the deliberate boundary above, not as an oversight; the backlog item `5u7mug` is about `aw set`'s vocabulary, and both residual gaps this plan fixes are in `aw set`.

## Required tests / validation

`python3 -m pytest tests/test_status_set.py` for the focused surface, then the BARE full suite (`python3 -m pytest`) last, with the actual `N passed` summary pasted. The E-01 and E-02 tests must be shown FAILING against HEAD before the fix, with that output pasted in V-03. The four pre-existing `ResearchStatusSetTests` cases must pass UNMODIFIED, and `tests/test_lifecycle_dirs.py` plus `tests/test_research_archive.py` must stay green as the guard that the derivation and the promote path were not disturbed. Live-corpus read-only checks: `aw set intake <id6> --dry-run` and `aw set active <id6-in-a-reference-shard> --dry-run` before and after, plus a re-run of the F-8 corpus scan to confirm it still reports zero hot-in-cold docs.

## Spec / documentation sync

Spec `5tapom` (`.aw/records/specs/approved/20260824-5tapom-01-5tapom-research-lifecycle-reliability.spec.md`) is NOT amended and is deliberately NOT in `- Scope-Paths:`. Its Section 4 non-goal already reads "No change to the filename grammar, the four `status` values ..., the shard layout", and this plan changes none of those: it accepts an alias the contract already declares and refuses a write that contradicts the shard layout the spec preserves. Both changes move the code TOWARD that spec's H2 ("state must be genuinely tool-owned, i.e. advanced and validated by tooling"), so no contract text changes. `.aw/records/research/README.md` is also unchanged: its status table already lists "`todo` (legacy `intake`)" and states that hot states stay flat at the root while cold states live in monthly shards, which is exactly the rule E-02 enforces; the README documented the intended behavior correctly and the code was the part that diverged.

## Open questions

### OQ-01: Is the backlog item's attached migration question ("any existing doc already carrying one needs a migration answer") answered?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE at authoring, which is why it is not left for the maintainer. The item required an explicit decision on whether `done`/`open`/`parked` become aliases or are dropped, "because any existing doc already carrying one needs a migration answer". The corpus answers it: the raw frontmatter `status` census over the research root is `{'reference': 67, 'todo': 13, 'active': 4, 'archive': 32}` and a grep for `^status: (done|open|parked)` returns nothing (F-9). ZERO docs carry any of the three, so no migration is owed and no alias is justified; mapping them would invent vocabulary. The one alias that IS justified is `intake`, because `research_contract.STATUS_NORMALIZATIONS` already declares it and the contract's own docstring says every read site applies it (F-4), so E-01 accepts an existing spelling rather than inventing one. The separate F-10 tier inconsistency found while measuring this is filed as backlog `zdsf35` and carried in Deferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full command and output of `aw set intake <research-id6> --dry-run` showing exit 0 and a transition line whose TARGET is `todo` (not `intake`), plus the applied (non-dry-run) run on a scratch or fixture doc showing `status: todo` in the file afterwards via a pasted `grep -n "^status:"`. Also paste `aw set done <id6> --dry-run` and `aw set parked <id6> --dry-run` still exiting 1 with `is not valid for research`, proving the alias did not widen the accepted set. Paste `python3 -c "from agent_workflows import status_set as s; print(sorted(s.TYPE_STATUSES['research']))"` still printing `['active', 'todo']`, proving the derivation was not replaced by a hand-listed set.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the command and output of `aw set active <id6-of-a-doc-under-reference/YYYYMM>` (or the fixture equivalent) showing exit 1 and a message naming `aw research promote <id6> --to active`, AND evidence the file is byte-unchanged (a pasted `git diff --stat` showing no change, or a before/after `sha256sum`). Separately paste a hot target on a HOT-ROOT doc still exiting 0 with the status written, proving the refusal is placement-scoped and did not break the normal path. Paste the F-8 corpus scan re-run reporting `HOT status sitting in COLD shard: 0`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the pre-fix FAILING output of the two new tests run against HEAD (the assertion text, not a summary claim), then the post-fix `python3 -m pytest tests/test_status_set.py` output including the `N passed` line, then the BARE `python3 -m pytest` summary line. Paste `git diff` for `tests/test_status_set.py` restricted to showing that the four pre-existing `ResearchStatusSetTests` methods (`test_set_done_refuses_for_research`, `test_set_active_writes_status_for_report`, `test_set_reference_refuses_naming_research_promote`, `test_set_hot_status_on_prompt_refuses`) are unmodified apart from any shared-fixture signature change, and state explicitly whether `create_research` was extended or a sibling helper added.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Commit only the `- Scope-Paths:` files through `aw commit 4a8yws -- agent_workflows/status_set.py tests/test_status_set.py`, never `git add -A`, and never push. This plan carries `- Blocks-Release: next`, inherited from backlog `5u7mug`. Because F-1 through F-3 show the item's ORIGINALLY MEASURED defects were already fixed by `5e3nj2`, the executor must re-run the F-4 and F-5 reproductions BEFORE implementing: if either no longer reproduces, stop and report rather than writing a guard for a bug that is gone. Backlog `5u7mug` goes to `graduated`, not `done`, at authoring time; it closes only when this plan is executed and the release gate is provably carried. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is unconditionally owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-03 carry pasted evidence.
