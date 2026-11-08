# IPD: Write short_description at creation and add the aw describe setter

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` 4.2 SHORT DESCRIPTION and AC-36 case 1 require every creating command to accept `--summary` and write it as `short_description`, and require a setter for an existing record. Measured: `aw ipd scaffold --help` and `aw prompts new --help` show no `--summary`, and no `aw describe` verb exists (`rg -n "\"describe\"" agent_workflows/cli.py agent_workflows/command_surface.py`: no match). This is a part of `xexn45`, split 2026-11-07.
- Scope: Add `--summary` to `aw ipd scaffold` and `aw prompts new`; make the seven creating commands write `short_description` in their `create` event; register `Short-Description` in `ipd_schema.META_RECOGNIZED` (`xexn45` E-03). Add `aw describe <id6> --summary|--clear [--apply]` (`xexn45` E-04). Depends on `g6tw94` and `n5sxxk`, which move the creating commands onto `artifact_meta.create`. EXCLUDES: the `CHANGELOG.md` line (`xexn45` E-14).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/ipd_schema.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/specs.py, agent_workflows/backlog.py, agent_workflows/releases.py, agent_workflows/research_cmd.py, agent_workflows/artifact_adopt.py, agent_workflows/ipd_authoring.py, agent_workflows/prompts.py, docs/cli-output-contract.md, tests/test_writers_create_summary.py, .aw/records/plans/pending/20261107-metastore-24-6e93gt-write-short-description-at-creation-and-add-the-aw-describe.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827, executed:g6tw94, executed:n5sxxk
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 24
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6e93gt

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from xexn45 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every creating command can write a short description at creation, and `aw describe` sets or clears it on any existing record, all through `artifact_meta`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/6e93gt/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/6e93gt/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: short description at creation and the setter

- [ ] E-01 Write `short_description` at creation (AC-36 case 1): add `--summary` to `aw ipd scaffold` and `aw prompts new` (registered in `cli` and `command_surface`); make every creating command (`aw backlog new --summary`, `aw specs new --summary`, `aw releases new --summary`, `aw research new --summary`, `aw adopt --summary`, `aw ipd scaffold --summary`, `aw prompts new --summary`) write the value as `short_description` in the `create` event when it passes `attention_contract.refuse_unsafe_descriptive` at `MAX_DESCRIPTIVE_LEN` (300); for `aw specs new`, a `--summary` over 300 characters (still accepted up to `MAX_PROSE_DESCRIPTIVE_LEN` today) is written only to the body summary and writes no `short_description` (4.2 SHORT DESCRIPTION). In phase B the legacy writer renders the field as a `- Short-Description:` bullet (a prompt: a `Short-Description:` comment key), registered in `ipd_schema.META_RECOGNIZED` (plans; otherwise `IPD-M103`). The other types have no unknown-bullet check today (`specs.validate_spec`, `backlog._render_item`, `releases.validate_release`; research validates only its required YAML keys in `research_contract.FRONTMATTER_FIELDS`), so for them the gate is a test: each `tests/test_writers_create_summary.py` case runs `aw check all --agent` on its fixture and asserts no diagnostic names the new field. Research writes the value as a `short-description:` YAML key, not a bullet (see OQ-02). Test module `tests/test_writers_create_summary.py`.
  - Depends on: none
  - Expected outcome: for each of the seven commands, `--summary "Adds a widget."` then `artifact_meta.read(<id6>).fields["short_description"] == "Adds a widget."`; a 301-character value, a newline value and a control-character value each exit nonzero with no file written; a 400-character `aw specs new --summary` writes the body summary and no `short_description`.
  - Execution state: pending

- [ ] E-02 Add the short-description setter `aw describe <id6> --summary <text> [--apply]` and `aw describe <id6> --clear [--apply]` (preview by default), registered in `cli`, `command_surface` and `docs/cli-output-contract.md`. It appends one `set` (or `unset`) of `short_description` through `artifact_meta.append` with no status change and is accepted on a terminal record (OQ-30: a terminal log accepts a `set` or `unset` of `short_description`). It resolves the selector through `selectors.resolve` and refuses zero or several matches with exit 2 (the `zyj8io` convention). Test module `tests/test_writers_create_summary.py`.
  - Depends on: E-01
  - Expected outcome: `aw describe <id6> --summary X` previews and writes nothing; `--apply` writes the field and one history line; the same call on an executed plan succeeds; `--clear --apply` removes it; an unknown id6 exits 2.
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
| F-01 | `rg -n "\"--summary\"" agent_workflows/cli.py`: research new, research comparison, backlog new, specs new, releases new and adopt carry it; scaffold and prompts new do not | Two new options, five existing ones rewired. |
| F-02 | `rg -n "Short-Description" agent_workflows/ipd_schema.py`: no match; `agent_workflows/artifact_meta.py` already maps `Short-Description` to `short_description` | `ipd_schema.py` must be edited; `xexn45` did not declare it in `- Scope-Paths:`, so this part declares it. |
| F-03 | Hidden units of E-01: 2 new CLI options, 7 command modules, `ipd_schema.META_RECOGNIZED`, `command_surface`, the legacy rendering in three forms (bullet, prompt comment key, research YAML key), 11 new test cases: about 24 units | At the limit, kept whole because the seven commands share one test module and one acceptance case (AC-36 case 1). |
| F-04 | Hidden units of E-02: one new verb, `cli`, `command_surface`, `docs/cli-output-contract.md`, five transcript cases: about 9 units | Within the limit. |

## Proposed changes (ordered, validatable)

1. `--summary` at creation (E-01).
2. The `aw describe` setter (E-02).

## Deferred / out of scope (with reason)

- The final merge-independence test, the AC-21 obligations test, the raw-write audit (F-09), the `docs/cli-output-contract.md` and `CHANGELOG.md` lines, and the full-suite gates of the writer move.
  - Carrier: xexn45
- The walkthrough-creating command `aw walkthrough new` (named in `xexn45` Deferred), which lands with the documents that describe it.
  - Carrier: 90iqr1

## Scope check

- Over-scope: none.
- Under-scope: none. 14 Scope-Paths entries exceed the 12-entry guide; see the cohesion rationale.

## Required tests / validation

New core test module: `tests/test_writers_create_summary.py` (fixtures in `tmp_path`, real CLI, never reads source).

Contributes to `4sd62s` AC-36 case 1 (`cxxmyv` re-demonstrates the full criterion).

## Spec / documentation sync

`docs/cli-output-contract.md` gains the `aw describe` leaf (E-02). `xexn45` E-14 reconciles it with the two `--summary` options and adds the `CHANGELOG.md` line. No spec change: this implements `4sd62s` 4.2 SHORT DESCRIPTION as written.

## Open questions

### OQ-02: How does `short_description` appear on disk in phase B?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: As a `- Short-Description:` bullet (a `Short-Description:` key inside a prompt's comment; a `short-description:` YAML key in research front matter), registered as a recognized field in `ipd_schema.META_RECOGNIZED` and proven unflagged for the other types by `aw check all --agent` (E-03). Evidence: phase B has one on-disk format (C10a), the legacy loader reads bullets (tve77h E-11) so the value survives a cache rebuild, and an unregistered bullet is lint error `IPD-M103` on plans. The alternative (no on-disk form until the cutover) would make AC-36 case 1 untestable through `read()` after a cache deletion. The migration (dcerjg) maps the bullet to `short_description` with `description_source` absent (written by a command, not generated), and the census lists it. Recommendation strength: strong.
- Note: carried unchanged from `xexn45` with its id, so the item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py -k "summary and not describe"` with one PASSED test per creating command (seven) asserting `artifact_meta.read(id6).fields["short_description"]`, the three refusal tests (301 characters, newline, control character) each asserting exit code nonzero and `git status --porcelain` empty, and the 400-character `aw specs new --summary` test asserting no `short_description` and the body summary present; plus `aw ipd scaffold --help` and `aw prompts new --help` lines showing `--summary`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the transcript in a fixture repository: `aw describe <id6> --summary "Adds a widget."` (preview, exit 0, `git status --porcelain` empty), the same with `--apply` (exit 0, `git diff` shows one `- Short-Description:` line and one history line), the same on an executed plan (exit 0), `--clear --apply` (bullet removed), and `aw describe zzzzzz --summary x; echo $?` printing `2`; plus `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py -k describe` all PASSED.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 14 Scope-Paths entries against a guide of about 12: seven of them are the seven creating-command modules, each receiving the same one-field change (pass `--summary` into the `create` event) and all driven by one test module for one acceptance case (AC-36 case 1). Splitting them would put one acceptance case and one test module across plans with no smaller seam. E-count (2) and task groups (1) are well inside the thresholds.

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 6e93gt -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 6e93gt` itself.
