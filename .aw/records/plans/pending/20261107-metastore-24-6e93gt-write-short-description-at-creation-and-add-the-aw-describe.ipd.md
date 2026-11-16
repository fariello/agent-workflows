# IPD: Write short_description at creation and add the aw describe setter

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` 4.2 SHORT DESCRIPTION and AC-36 case 1 require every creating command to accept `--summary` and write it as `short_description`, and require a setter for an existing record. Measured: `aw ipd scaffold --help` and `aw prompts new --help` show no `--summary`, and no `aw describe` verb exists (`rg -n "\"describe\"" agent_workflows/cli.py agent_workflows/command_surface.py`: no match). This is a part of `xexn45`, split 2026-11-07.
- Scope: FINISHING PART of the short-description work (`xexn45` E-03 and E-04). Round-3 split 2026-11-09 per research `nj8zdp`: `--summary` at creation now lives in `fekdwv` (Order 124, backlog, specs, releases), `bir7xm` (125, research, adopt) and `py2vu9` (126, plan scaffold, prompts, `ipd_schema.META_RECOGNIZED`), and `aw describe` in `h06gs7` (136). This plan keeps the AC-36 case 1 cross-check (E-03): all seven creating commands and the setter, once, in one run. EXCLUDES: the `CHANGELOG.md` line (`xexn45` E-14).
- Scope-Paths: .aw/records/plans/pending/20261107-metastore-24-6e93gt-write-short-description-at-creation-and-add-the-aw-describe.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94, executed:n5sxxk, executed:fekdwv, executed:bir7xm, executed:py2vu9, executed:h06gs7
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: simple
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 24
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6e93gt
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-16 approved (aw set): status set to approved
- 2026-11-14 reviewed (antigravity/claude-opus-5.5): plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 FIXED

- 2026-11-14 /plan-review (antigravity/claude-opus-5.5): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 FIXED; review record .aw/records/reviews/20261107-metastore-24-6e93gt-write-short-description-at-creation-and-add-the-aw-describe.review.md
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01 (split by command), E-02 moved to fekdwv, bir7xm, py2vu9, h06gs7.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

After its four parts run, every creating command writes a short description at creation and `aw describe` sets or clears it; this plan proves the whole of AC-36 case 1 in one run.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

No move item and no code edit: this plan has one read-only cross-check item (E-03), so the pin-first rule of the parent `xexn45` does not apply here; the four parts (`fekdwv`, `bir7xm`, `py2vu9`, `h06gs7`) carry their own pin-first steps and write every test this plan reads.

### Task group 1: AC-36 case 1 cross-check

- [ ] E-03 Cross-check AC-36 case 1 across all four parts: run `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py` once and build a table in Findings (F-05) with one row per creating command (`aw backlog new`, `aw specs new`, `aw releases new`, `aw research new`, `aw adopt`, `aw ipd scaffold`, `aw prompts new`) and one row for `aw describe`, each naming its stored-value test and its refusal tests by id. The refusal tests differ for `aw specs new` by design (`fekdwv` E-02): a 301-character `--summary` succeeds and stores no `short_description`, and the refusals are the 4301-character, newline and control-character values; every other creating command refuses a 301-character, newline and control-character value. A command with no stored-value test is a defect of the part that owns it (`fekdwv`, `bir7xm`, `py2vu9`, `h06gs7`): stop and report it rather than editing here.
  - Depends on: none
  - Expected outcome: F-05 has eight rows, each naming PASSED test ids; no row is empty.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `history`, `query`, `resolve`, `read_at`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`, `repair`. Order 02's `append`/`create` are log-format and "switched on at the cutover"; Order 21 (`7yr827`) adds the phase-B branch (`write_legacy`) that Order 13 removes.
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
| F-01 | `rg -n "\"--summary\"" agent_workflows/cli.py`: research new, research comparison, backlog new, specs new, releases new and adopt carry it; scaffold and prompts new do not | Two new options, five existing ones rewired. |
| F-02 | `rg -n "Short-Description" agent_workflows/ipd_schema.py`: no match; `agent_workflows/artifact_meta.py` already maps `Short-Description` to `short_description` | `ipd_schema.py` must be edited; `xexn45` did not declare it in `- Scope-Paths:`, so `py2vu9` declares it. |
| F-03 | Historical (pre-split; E-01 now lives in `fekdwv`, `bir7xm` and `py2vu9`). Hidden units of E-01: 2 new CLI options, 7 command modules, `ipd_schema.META_RECOGNIZED`, `command_surface`, the legacy rendering in three forms (bullet, prompt comment key, research YAML key), 11 new test cases: about 24 units | At the limit, kept whole because the seven commands share one test module and one acceptance case (AC-36 case 1). |
| F-04 | Historical (pre-split; E-02 now lives in `h06gs7`). Hidden units of E-02: one new verb, `cli`, `command_surface`, `docs/cli-output-contract.md`, five transcript cases: about 9 units | Within the limit. |
| F-05 | (filled by E-03) one row per creating command and `aw describe`, with its PASSED test ids | The AC-36 case 1 cross-check. |

## Proposed changes (ordered, validatable)

1. `--summary` at creation, in three parts (`fekdwv`, `bir7xm`, `py2vu9`).
2. The `aw describe` setter (`h06gs7`).
3. The AC-36 case 1 cross-check (E-03).

## Deferred / out of scope (with reason)

- E-01 backlog, specs and releases subset (`aw backlog new`, `aw specs new` with the over-300 rule, `aw releases new`) and the creation of `tests/test_writers_create_summary.py`: Moved to fekdwv (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: fekdwv
- E-01 research and adopt subset (`aw research new` with the `short-description:` YAML key, `aw adopt`): Moved to bir7xm (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: bir7xm
- E-01 scaffold and prompts subset (the two new `--summary` options in `cli` and `command_surface`, the `Short-Description` entry in `ipd_schema.META_RECOGNIZED`, the prompt comment key): Moved to py2vu9 (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: py2vu9
- E-02 (`aw describe` with `docs/cli-output-contract.md`): Moved to h06gs7 (round-3 split 2026-11-09 per research nj8zdp guidance)
  - Carrier: h06gs7
- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` reconciliation of the `--summary` options and the `CHANGELOG.md` line, and the full-suite gates of the writer move.
  - Carrier: xexn45
- The walkthrough-creating command `aw walkthrough new` (named in `xexn45` Deferred), which lands with the documents that describe it.
  - Carrier: 90iqr1

## Scope check

- Over-scope: none.
- Under-scope: none. Every command of the original E-01 and the whole of E-02 lives in exactly one of the four parts. Plan size after the split: 1 E-item, no code path.

## Required tests / validation

No new module and no code edit; `tests/test_writers_create_summary.py` is created by `fekdwv` and extended by `bir7xm`, `py2vu9` and `h06gs7`. Contributes to `4sd62s` AC-36 case 1 (`cxxmyv` re-demonstrates the full criterion).

## Spec / documentation sync

None here. `h06gs7` adds the `aw describe` leaf to `docs/cli-output-contract.md`; `xexn45` E-14 reconciles it with the two `--summary` options and adds the `CHANGELOG.md` line. No spec change: the parts implement `4sd62s` 4.2 SHORT DESCRIPTION as written.

## Open questions

### OQ-02: How does `short_description` appear on disk in phase B?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: As a `- Short-Description:` bullet (a `Short-Description:` key inside a prompt's comment; a `short-description:` YAML key in research front matter), registered as a recognized field in `ipd_schema.META_RECOGNIZED` and proven unflagged for the other types by `aw check all --agent` (`bir7xm` E-01 and E-02; `py2vu9` E-01 for `IPD-M103` on plans). Evidence: phase B has one on-disk format (C10a), the legacy loader reads bullets (tve77h E-11) so the value survives a cache rebuild, and an unregistered bullet is lint error `IPD-M103` on plans. The alternative (no on-disk form until the cutover) would make AC-36 case 1 untestable through `read()` after a cache deletion. The migration (dcerjg) maps the bullet to `short_description` with `description_source` absent (written by a command, not generated), and the census lists it. Recommendation strength: strong.
- Note: carried unchanged from `xexn45` with its id, so the item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-03 validates E-03
  - Required evidence: paste the `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py` output and the filled F-05 table: for each of the seven creating commands, its stored-value test id and its 301-character, newline and control-character refusal test ids, each PASSED (for `aw specs new`, instead its 301-character accepted-without-`short_description` test id and its 4301-character, newline and control-character refusal test ids, per `fekdwv` E-02); for `aw describe`, its preview, apply, executed-plan, clear and unknown-id6 test ids, each PASSED.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 6e93gt -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 6e93gt` itself.
