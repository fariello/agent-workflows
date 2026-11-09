# IPD: Move the specs, backlog and releases create, note and setter writers onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata writer to write through `artifact_meta` in phase B. The specs, backlog and releases modules still build their `- Field:` bullets and `## Workflow history` lines by hand (measured: `specs` 14 bullet literals and 8 history references, `backlog` 29 and 18, `releases` 11 and 4). This is a part of `xexn45`, split 2026-11-07 because its create and note items each spanned seven modules and 17 or 9 test modules.
- Scope: FINISHING PART of the specs, backlog and releases writer move (`xexn45` E-02 subset A and E-05 subset A). Round-3 split 2026-11-09 per research `nj8zdp`: the moves now live in `b3l7y6` (Order 120, specs), `jlwedt` (121, backlog) and `3466h8` (134, releases); this plan keeps the family audit (E-03) that proves no module of the family still builds history text by hand. EXCLUDES: the prompts, scaffold, research, adopt and set_records writers (`n5sxxk`), `--summary` (`6e93gt`).
- Scope-Paths: .aw/records/plans/pending/20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:b3l7y6, executed:jlwedt, executed:3466h8
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 22
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: g6tw94

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01 (split by module), E-02 (split by module) moved to b3l7y6, jlwedt, 3466h8.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

After its three parts run, no create, note or field-setter path of the specs, backlog and releases modules builds metadata text by hand; this plan proves it with one audit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/g6tw94/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/g6tw94/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: family audit

- [ ] E-03 Audit the specs, backlog and releases family after its three parts: run `rg -n "Workflow history" agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/releases.py` and `rg -n "f\"- \{(date|today|hdate)\} " agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/releases.py`, label every hit with its enclosing `def`, and add a Findings row (F-05) that names each hit and its reason (a reader, a body-text edit per N3, or a call into `artifact_meta`). Any hit inside a writer named in `b3l7y6`, `jlwedt` or `3466h8` is a defect of that part: stop and report it rather than editing here.
  - Depends on: none
  - Expected outcome: F-05 lists every hit with its enclosing `def` and reason; no hit is inside `specs.run_new`, `specs._render_new_spec`, `specs.run_note`, `specs.run_migrate`, `backlog.run_new`, `backlog._render_item`, `backlog.run_note`, `backlog._reattach_history`, `releases.create_release` or `releases.plan_release`.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `history`, `query`, `resolve`, `read_at`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`, `repair`. Order 02's `append`/`create` are log-format and "switched on at the cutover"; this plan adds the phase-B branch (`write_legacy`) that Order 13 removes.
- Atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`; the lock is `platform_lock.held`; UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4).
- Today's history-insertion rules differ (F-04): `status_set._prepend_workflow_history_entry` and `backlog.run_note` insert DIRECTLY under the heading; `specs._append_history` normalizes to exactly one blank line then the record; `plan_readiness._prepend_history_entry` keeps an existing blank line and inserts after it; `coverage_record.write` inserts directly under the heading.
- The newest-history reader is `attention_contract.newest_history_record` over `attention_contract.history_block`, which drops blank lines; so the blank-line difference changes no reader result.
- Descriptive refusals: `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300 and `MAX_PROSE_DESCRIPTIVE_LEN` 4300; `specs._refuse_unsafe_descriptive(..., prose=True)` is the spec `--summary` path.
- Recognized plan bullets are `ipd_schema.META_RECOGNIZED`; an unrecognized bullet is lint error `IPD-M103` (`ipd_lint.C_META_UNKNOWN`). Backlog keeps unknown bullets in order (`backlog._render_item`, rendrop 2yqt0a).
- The prompt mirror is the single `aw-prompt` comment (`prompts.render_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`); nothing visible may precede the prompt body (spec `20260808-1958-01-prompt-purity-lint` R1/P4).
- Finalize scope evidence is `evidence["scope_reconciliation"]` with `reasons` and `widened_paths` (`ipd_lifecycle._finalize_transaction`, `runner_shared.compute_scope_reconciliation`).
- Rollup retirement is `ipd_lifecycle.retire_orchestrator` -> `_finalize_transaction` with `evidence["transition"] == "orchestrator-rollup"`.
- The rename ledger is `record_history.record_rename`, written by `artifact_rename` and `plans_refs`; the sidecar is gitignored (`.aw/.gitignore` `records/history.jsonl`).
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).

## Findings

| Id | Evidence (measured 2026-11-07 at `ac76110f4`) | Finding |
|---|---|---|
| F-01 | `rg -n "f\"- \{(date|today|hdate)\} " agent_workflows/specs.py agent_workflows/backlog.py`, attributed to the enclosing `def`: `specs.run_migrate`, `specs.run_note`, `specs._render_new_spec`, `backlog._render_item` (2), `backlog.run_note`, `backlog._reattach_history` | Seven hand-built history-line sites, all in this part. `_render_new_spec` and `_render_item` are the create renderers that E-01 replaces. |
| F-02 | Hidden units of E-01: 4 writer functions, 3 files, 9 pinned modules (`test_releases` 21, `test_releases_cli` 37, `test_backlog` 47, `test_spec_id6_filenames` 21, `test_history_date_clock` 5, `test_specs_releases_descriptive_safety` 19, `test_backlog_descriptive_safety` 19, `test_descriptive_refusal_hoist` 3, `test_history_write_order` 8 tests, counted with `rg -c "^\s*def test_"`): about 16 units | Within the 25-unit limit. |
| F-03 | Hidden units of E-02: 6 writer functions, 3 files, 6 pinned modules (`test_specs_verbs` 20, `test_backlog` 47, `test_graduation_forward_links` 9, `test_history_block_bounding` 9, `test_history_order` 7, `test_specs_date_containment` 15 tests): about 15 units | Within the limit. |
| F-04 | `tests/test_descriptive_refusal_hoist.py` exercises `specs`, `backlog`, `releases` and `research_cmd` (`rg -o` over the module: 8, 8, 7 and 4 references) | It is pinned in both this part and `n5sxxk`; a re-run is harmless and each part sees its own family green. |
| F-05 | (filled by E-03) family audit hits with their enclosing `def` and reason | Proof that the family writes no hand-built history. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-1 (blank line under the history heading). KEPT per file: the legacy writer inserts the new line after an existing blank line when one is present and directly under the heading otherwise; it never adds or removes a blank line. This keeps every existing file's shape (F-04) and matches `attention_contract.history_block`, which ignores blank lines. CHANGED: `specs._append_history`'s normalization of a missing blank line (19 specs) no longer adds one, and `specs._append_history` and `status_set._prepend_workflow_history_entry` create a missing section differently today (specs at end of file, plans before the first `##`); the legacy writer uses the `status_set` rule for every type except prompts, which keep end-of-file (pinned by `2xwb9b` E-02). Named tests: `tests/test_specs_verbs.py::test_note_appends_one_record_only` (asserts the record count, not the blank line), `tests/test_history_order.py::test_fixture_a_newest_first`, and a new `tests/test_artifact_meta_legacy_writer.py` case per insertion rule (with blank line, without, section absent) that compares full file bytes. Any existing test that pins the OLD specs normalization fails this plan's E-02 pin diff; it is then listed here by name with its changed assertion, as the PIN-FIRST RULE allows, and in no other case.
- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). The few writers with a different anchor (`coverage_record` after `- Readiness:`, `runner_shared.mark_plan_attended` at block end, `perform_coordinator_proposal_file` after `- Priority:`) change position only; no reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free). Named tests: `tests/test_coverage_record.py`, `tests/test_run_proposal_channel.py`.

## Proposed changes (ordered, validatable)

1. The moves, in three parts: specs (`b3l7y6`), backlog (`jlwedt`), releases (`3466h8`).
2. The family audit (E-03).

## Deferred / out of scope (with reason)

- E-01 specs subset (`specs.run_new`) and E-02 specs subset (`specs.run_note`, `specs.run_migrate`): Moved to b3l7y6 (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: b3l7y6
- E-01 backlog subset (`backlog.run_new`) and E-02 backlog subset (`backlog.run_note`, `backlog._reattach_history`): Moved to jlwedt (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: jlwedt
- E-01 releases subset (`releases.create_release`, `releases.plan_release`) and E-02 releases subset (`releases.set_item_dependencies_line`, `releases.set_graduated_to_line`): Moved to 3466h8 (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: 3466h8
- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` and `CHANGELOG.md` lines, and the full-suite gates of the writer move.
  - Carrier: xexn45
- The other writer families of `xexn45` (subset B of E-02 and E-05).
  - Carrier: n5sxxk

## Scope check

- Over-scope: none.
- Under-scope: none. Every writer and every pinned module of the original E-01 and E-02 lives in exactly one of `b3l7y6`, `jlwedt` and `3466h8` (shared modules are pinned in each part that touches one of their modules). `tests/test_releases_sibling_line_writers_bounding.py` was added to the releases pin list by `3466h8`. Plan size after the split: 1 E-item.

## Required tests / validation

No new module and no code edit. The pinned modules now live in the V-items of `b3l7y6`, `jlwedt` and `3466h8`; V-03 here is a search audit.

## Spec / documentation sync

None. Implements `4sd62s` section 7 step 4 for this module family; no documented behavior changes.

## Open questions

None open. Every question this work raised was resolved in `xexn45` before the split; the decisions above carry the answers.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-03 validates E-03
  - Required evidence: paste both `rg` commands of E-03 with their full output, and the filled F-05 row naming each hit's enclosing `def` and reason; for each of the ten writer functions named in the E-03 expected outcome, state that no hit falls inside it.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit g6tw94 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize g6tw94` itself.
