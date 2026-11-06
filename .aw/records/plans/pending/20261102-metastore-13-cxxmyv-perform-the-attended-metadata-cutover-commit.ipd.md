# IPD: Perform the attended metadata cutover commit

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` section 7 step 9 and section 5.2 require ONE attended commit that switches `artifact_meta` from the legacy bullet-block format to per-artifact event logs, runs migration `m0001` on this repository in the checkout that holds the gitignored history sidecar, applies the post-cutover documentation, and stamps `metadata_schema: 2`. Every earlier child deferred its log-format half here (re-measured 2026-11-06: deferral rows naming `Carrier: cxxmyv` in 11 of the 12 sibling plans; `7ehv8l` has none), because C10a forbids a second on-disk format on `main` before this commit.
- Scope: The code switch to the log format and every deferred log-format item; the real migration on this repository; the documentation patch of `90iqr1`; the two commands documented there; and the final real-repository demonstrations of the acceptance criteria the earlier children proved on fixtures. One commit, attended by the maintainer.
- Scope-Paths: .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, agent_workflows/, tests/, .aw/records/, .aw/system/workflows/, .aw/system/cutover/, .aw/system/managed-sections.json, .aw/.gitignore, .aw/config/project.json, .aw/AGENT_QUICKSTART.md, .aw/QUICKSTART.md, docs/, AGENTS.md, CHANGELOG.md, .aw/records/plans/pending/20261102-metastore-13-cxxmyv-perform-the-attended-metadata-cutover-commit.ipd.md
- Item-Dependencies: executed:90iqr1, executed:dcerjg, executed:ya4ee4, executed:1ajqaa
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Attended: required
- Set: metastore
- Order: 13
- Highest E allocated: 17
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: cxxmyv
- Readiness: go-pending-approval
- Review-Depth: complex

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-016 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-016 FIXED; feasibility risk named: the one-commit mechanism is proven only by the E-17 rehearsal; review record .aw/records/reviews/20261102-metastore-13-cxxmyv-perform-the-attended-metadata-cutover-commit.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Land the hard cutover: after this one commit the toolkit reads and writes only the event-log format, every record of this repository is migrated, the documentation describes commands instead of field syntax, and the acceptance criteria that need the real migrated repository are demonstrated on it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: decisions and preflight

- [ ] E-01 Apply the OQ-02 decision before the code switch: from `ya4ee4`'s 40-record trial result (its E-10 table), pick the cheapest model whose output the maintainer judges accurate, and record here the chosen host, the model, the per-record mean cost and the extrapolated full-run cost and duration. This item writes no code; the OQ-01 code is E-14.
  - Depends on: none
  - Expected outcome: the chosen host and model are recorded in this plan with the trial figures they rest on and the maintainer's confirmation.
  - Execution state: pending

- [ ] E-02 In the maintainer's main checkout (never a runner lane), with the maintainer present, run `aw migrate metadata` (dry run, with the E-01 host and model) on the current, unswitched tree and paste: the preflight lines (uncommitted record changes, integration lock, unmerged lanes, linked-worktree check, sidecar present with its record count, AC-22 case 2), the field census (AC-20) including the orphan `id6` lines of the sidecar (AC-30 case 3), the rename map (34 records at authoring; the bar is that every `artifact_naming._LEGACY_TIMESTAMP_RE` artifact and walkthrough is mapped) with `wvlk84` as `awphysical-17` (AC-41 case 1), the citation-rewrite report per location (OQ-27, AC-41 case 5), the description-journal status (records with and without a description, OQ-22), and the round-trip result. On the same tree, record the AC-13 "before" values that E-12 compares against (bytes an agent reads for one named plan; end-to-end wall time of `aw find` and `aw attention`, warm and cold, with the cold-cache method stated). The maintainer reviews the generated descriptions in the journal before E-10.
  - Depends on: E-01
  - Expected outcome: a clean dry run whose census has no `unknown-field` or unparseable value and whose description journal is complete or lists each deliberate absence; the AC-13 before values are recorded.
  - Execution state: pending

### Task group 2: switch the code to the log format (one working tree, not yet committed)

- [ ] E-03 Switch `artifact_meta`'s loader and writer to the log format: `append` and `create` write `meta/<id6>.jsonl` with the spec 4.3 write order (log, in-file mirror, disposition, cache), the loader reads logs, and the legacy loader moves unchanged into `agent_workflows/migrations/m0001_metadata_v2.py`. Delete the legacy branch of `append` with `LegacyRender` and the path-keyed target (`2xwb9b`), switch `write_legacy` off and remove the value writers that `9o83cr` E-08 folded into it (`xexn45`, `9o83cr`), and set `chain.CURRENT_METADATA_SCHEMA` to 2 (`dcerjg`).
  - Depends on: E-02
  - Expected outcome: no module outside `artifact_meta.py` (log format only) and `migrations/m0001_metadata_v2.py` can produce a bullet block or a `## Workflow history` line.
  - Execution state: pending

- [ ] E-14 Implement `4sd62s` OQ-01 as spec 4.2 states it (verified at review: spec 4.2 `overrides` bullet): every event a setter writes with `--allow-open-questions`, `--allow-terminal-reopen` or `--allow-unresolvable-release-sentinel` carries an `overrides` list naming each flag given (for example `["allow-open-questions"]`), absent when none was given; `aw specs set --date` exits nonzero with a message that names the `--message` alternative once `metadata_schema` is 2. Add behavioral tests on a migrated (log-format) fixture.
  - Depends on: E-03
  - Expected outcome: a setter run with an override flag writes `overrides` on its event; a run without one writes no `overrides` key; `aw specs set --date` refuses on a migrated fixture and leaves the fixture byte-identical.
  - Execution state: pending

- [ ] E-04 Turn on the log-only writers in code: path-bearing events and `rename` events for `aw rename`, `aw group` and `aw archive plans`, retiring the rename ledger (`xexn45`, AC-31, AC-34); retire `record_history.append`, `append_advisory` and `append_rename`; remove `records/history.jsonl` and the INDEX lines from the `engine.py` `.aw/.gitignore` template, the `engine._ensure_aw_gitignore` adder and `placement_switch.py`; and remove the skip-name entries that protected scans from INDEX and STATUS files (`9o83cr` Deferred row). Do NOT edit this repository's own `.aw/.gitignore`, delete its on-disk `INDEX.*` files or `plans/STATUS.md`, or move the sidecar: migration steps 2 and 5 do that (`dcerjg` E-06 and E-11). Doing it here would un-ignore the sidecar and dirty `.aw/records/`, which the step-1 preflight refuses.
  - Depends on: E-03
  - Expected outcome: in fixtures, a spec setter, a backlog setter, a rename and a group create no `history.jsonl` and append the expected events; a fresh `aw install` into a temporary repository writes no `records/history.jsonl` or INDEX ignore line; this repository's `.aw/.gitignore`, INDEX files, `STATUS.md` and sidecar are unchanged by this item.
  - Execution state: pending

- [ ] E-05 Put the gates in their post-cutover form: "mirrored status differs from replayed state" and "staged log violates append rules" in `check_engine` and the hooks; the executed transition accepted only as a finalize append or an orchestrator rollup-retirement append (`t4gl15`, AC-16 case 2); and the terminal-log rules of the `meta/*.jsonl` append-only hook, accepting only the appends that spec OQ-30 allows (`9o83cr`). The `->reviewed` gate-only rule (SR-601) is NOT here: `2xwb9b` E-12 implements it over `artifact_meta.query`, which serves log-format review rows unchanged.
  - Depends on: E-03
  - Expected outcome: each gate refuses its post-cutover violation in a fixture and accepts the allowed appends.
  - Execution state: pending

- [ ] E-15 Put the readers in their post-cutover form (`ffceq0` Deferred row): `last_history_at` comes from the newest post-cutover event `at` with `last_history_precision` (spec 4.4), and `aw check meta` gains the logged-path drift row (spec 4.6).
  - Depends on: E-03
  - Expected outcome: on a log-format fixture, `last_history_at` equals the newest event's `at` with its precision; `aw check meta` reports a planted `path-drift` and reports nothing on the unplanted fixture.
  - Execution state: pending

- [ ] E-06 Build the two commands documented by `90iqr1`: `aw reviews record` (appends one `review` event per spec 4.1a, with `review_kind`, `verdict`, optional `readiness` and `review_depth`; refuses `readiness` on a refinement event and any verdict outside the vocabulary of its kind) and `aw walkthrough new` (creates a walkthrough with its log over `set_records.write_walkthrough`). Declare both leaves in `command_surface` as mutations and change the `aw reviews` namespace description, which today says the namespace "is read-only and writes nothing". `aw meta repair` is NOT built here: `ffceq0` E-11 builds it.
  - Depends on: E-03
  - Expected outcome: `--help` of each command shows the arguments the `90iqr1` patch documents; behavioral tests pass; `tests/test_command_surface_declarations.py` reports no undeclared leaf.
  - Execution state: pending

- [ ] E-07 Switch the shared test record builder to `RECORD_FORMAT = "log"` and convert the setter-byte assertions to `artifact_meta.read` plus the in-file mirror (`59aiyh`); keep the legacy-format tests that must keep literal input (the legacy loader, migration round-trip and conversion tests) pointing at `m0001`; and settle the `tests/fixtures/review-pilot/plans/` legacy corpus (`59aiyh` Deferred row): convert it to the log format with `m0001`'s conversion, or route `tests/test_review_pilot.py` through `m0001`, and record which.
  - Depends on: E-03
  - Expected outcome: every test that builds its own fixture passes on the switched tree. Tests that read this repository's own unmigrated records (`livecorpus` tests and tests over `REPO_ROOT`, such as `tests/test_attention.py`) are expected to be refused with "run `aw migrate metadata`" until E-10; they are listed, not fixed, here.
  - Execution state: pending

- [ ] E-08 Apply the `90iqr1` documentation patch with `git apply .aw/system/cutover/metastore-docs.cutover.patch` (regenerate it from `90iqr1`'s scratch-worktree steps if it no longer applies), and delete the patch file and `tests/test_metastore_cutover_patch.py`, whose job ends here.
  - Depends on: E-06
  - Expected outcome: the documents, managed block, templates and quickstarts describe the log-format commands; the patch file is gone.
  - Execution state: pending

- [ ] E-16 Rename every `aw` option that names the legacy `Kind` field (spec 5.4; `90iqr1` Deferred row): the plan-role option of `aw ipd scaffold`, the research-kind options of `aw research new` and `aw research mv`, and the prompt-kind option of `aw prompts new`, to `plan_role`, `research_kind` and `prompt_kind` spellings, keeping each old spelling as an alias, as `aw backlog new --kind` already does for `--work-kind`. Update the tests that `90iqr1` F-07 lists as failing on the patched tree only because they assert pre-cutover text. Re-derive both lists at execution time.
  - Depends on: E-08
  - Expected outcome: each renamed option and its alias produce the same result; every F-07 test passes on the switched, patched tree.
  - Execution state: pending

### Task group 3: run the migration and commit

- [ ] E-09 On the switched, not-yet-migrated tree, run the bare core gate and `make test-all`. The only allowed failures are tests that read this repository's own unmigrated records and fail with "run `aw migrate metadata`" (E-07); any other failure stops the cutover here. Commit this plan's own progress edits with `aw commit cxxmyv -- <this plan's path>`, so the step-1 preflight sees a clean `.aw/records/` tree, then run `aw migrate metadata` (dry run) once more on this exact tree; any census refusal stops the cutover here with nothing else committed.
  - Depends on: E-04, E-05, E-07, E-08, E-14, E-15, E-16
  - Expected outcome: both tiers pass except the listed refusals; `git status --porcelain -- .aw/records` prints nothing; the dry run is clean.
  - Execution state: pending

- [ ] E-17 Rehearse the whole cutover on a COPY before E-10 touches this checkout. `git clone --no-hardlinks` this checkout to the gitignored `tmp/cxxmyv-rehearsal`, apply the uncommitted task group 2 changes (E-03 to E-08 and E-14 to E-16) with `git diff --binary HEAD | git -C tmp/cxxmyv-rehearsal apply --index`, copy the sidecar and the description journal into the clone (so no new model call is made), and in the clone run `aw migrate metadata --apply` without `--force`, the commit through every installed hook, then the bare core gate and `make test-all` on the migrated clone. This answers the question E-10 depends on: how does the migration's one `aw commit --no-plan` include the task group 2 code, test and documentation paths, given that 5.2 step 7 commits "the migration's own list of paths" and the step-4a marker matches only the exact staged tree (`dcerjg` E-11)? If `m0001` has no way to stage extra paths, add one under `agent_workflows/migrations/` (for example an explicit path-list argument that is staged before the marker is written) and repeat the rehearsal. If the `90iqr1` patch's hunks under `.aw/records/` (the records READMEs) trip the uncommitted-records preflight, the rehearsal must show a form that needs no `--force`. Stop condition: if no form produces ONE commit containing both the migration and the task group 2 paths without `--force` and without `--no-verify`, stop before E-10 and ask the maintainer. Delete the clone afterwards.
  - Depends on: E-09
  - Expected outcome: in the clone, one commit holds the migrated records and every task group 2 path, passes every installed hook, and both test tiers pass on it with no failures; the mechanism used is recorded in this plan's `## Findings`; this checkout's `git status --porcelain` is identical before and after.
  - Execution state: pending

- [ ] E-10 With the maintainer present, first commit this plan's E-17 edits (F-08, evidence) with `aw commit cxxmyv -- <this plan's path>` so the records tree is clean again, then run `aw migrate metadata --apply` in the main checkout with the mechanism that the E-17 rehearsal proved. The migration acquires the integration lock and holds it while it runs (5.2 step 1). Do not pass `--force` or `--force-worktree` unless the maintainer explicitly decides to and the override is recorded here. The migration renames, converts, rewrites citations, writes the terminal-exception marker, runs `aw check meta` and `aw sanitize --agent` on the staged tree (5.2 step 6), writes `metadata_schema: 2`, and makes its ONE commit through `aw commit --no-plan`, whose path list includes the task group 2 changes (E-03 to E-08 and E-14 to E-16).
  - Depends on: E-17
  - Expected outcome: one commit containing the migration and every task group 2 path; `aw check meta` reports no findings; the sanitizer reports no `fail`; `aw migrate metadata --apply` run again changes nothing (AC-10).
  - Execution state: pending

### Task group 4: demonstrate on the real repository

- [ ] E-11 Demonstrate on the migrated repository the criteria that need it. Read-only checks run in this checkout; every probe that commits, merges or edits runs in a `git clone --no-hardlinks` under the gitignored `tmp/cxxmyv-demo`, deleted afterwards. AC-1 (re-run the `9o83cr` E-14 audit with its exclusion list from `9o83cr` F-21: hits only in `artifact_meta.py` and `migrations/m0001_metadata_v2.py`); AC-1b (thorough-tier summary at the cutover commit; no migrated record has a bullet block; `git ls-tree` of the parent commit shows no `meta/` directory); AC-2 (`git clone --depth 1 file://<this checkout> tmp/cxxmyv-ac2`, because a plain local path ignores `--depth`, with `git rev-list --count HEAD` printing 1, then `aw show <id6> --history` on a migrated plan with several events); AC-3 (in the demo clone, two branches change the status of different artifacts and merge without conflict); AC-6 (in the demo clone, the `git diff` of one `aw set` transition and of one finalize transition with its `unset` and scope fields); AC-7 (zero `aw check meta` findings); AC-9 (`git ls-files` and the file system show no INDEX or STATUS file; `rg` for `INDEX.json` and `STATUS.md` in `agent_workflows/` finds only the migration's cleanup code); AC-11 (the `dcerjg` AC-11 tests pass with `CURRENT_METADATA_SCHEMA` unpatched); AC-16 (the commit passed every installed hook without `--no-verify`; `python3 -m agent_workflows attention --check --agent` exits 0 on the migrated tree, without pushing; in the demo clone, a raw transition into `executed` and a non-append edit of an executed plan's log are refused); AC-30 case 2 (`git status --porcelain --ignored` shows no `records/history.jsonl`; `rg` finds no `history.jsonl` ignore line in `.aw/.gitignore`, the `engine.py` template or `placement_switch.py`); AC-31 (in the demo clone, rename and group events; no sidecar created); AC-34 (path history of a renamed legacy record shows the old path then the new one); AC-36 case 6 (the real census of descriptions); AC-41 cases 3 and 4 (no legacy-timestamp artifact or walkthrough filename; no two plans share Set and order; a history line that cited an old name displays with the current name in `aw show --history`).
  - Depends on: E-10
  - Expected outcome: each criterion's required evidence pasted from the real repository or the demo clone, as stated per criterion.
  - Execution state: pending

- [ ] E-12 Measure AC-13 by the AGENTS.md end-to-end rule, warm and cold: bytes an agent reads for one plan, and the end-to-end time of `aw find` and `aw attention`, before (recorded in E-02 on the unmigrated tree) and after, with the same plan and the same cold-cache method; the size of a typical executed plan's log and the time of one append to it (in the demo clone); and the short-description generation cost from the journal.
  - Depends on: E-10
  - Expected outcome: a before and after table with the commands used; no target value is asserted (the spec sets none).
  - Execution state: pending

- [ ] E-13 Add one `CHANGELOG.md` entry for the metadata cutover (no em or en dashes) and commit it with `aw commit cxxmyv -- CHANGELOG.md <this plan's paths>`; this is a separate commit after the cutover commit. Perform the lifecycle transition: this plan is `Attended: required`, so no runner dispatches it and the attending executor runs `aw ipd finalize cxxmyv` after every `V-*` is `pass`. Do not retire the orchestrator `63ib9r` here; its own E-13 confirms this plan reached `executed`.
  - Depends on: E-11, E-12
  - Expected outcome: `aw ipd finalize cxxmyv` succeeds after every `V-*` is `pass`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The cutover runs in the checkout that holds `.aw/records/history.jsonl` (spec 5.2 step 1, 3c); a runner lane has no sidecar, so this plan is `Attended: required` and is never dispatched unattended.
- Hand publishes to `main` hold the integration lock (AGENTS.md "Before you publish to main by hand"); the migration acquires it itself (5.2 step 1).
- Commits go through `aw commit`; the migration's commit uses `aw commit --no-plan` with its own path list (5.2 step 7). How that path list also carries the code, test and documentation changes of task group 2 is not specified by spec 5.2 or by `dcerjg`; E-17 settles it on a copy before E-10.
- `git clone --depth 1 <local path>` ignores `--depth` ("warning: --depth is ignored in local clones; use file:// instead"; measured at review: `rev-list --count` 2 for a local path, 1 for `file://`), so the AC-2 clone uses a `file://` URL.
- The step-1 preflight refuses any uncommitted change under `.aw/records/` (`dcerjg` E-04 condition (2)). This plan file, the `90iqr1` patch's records-README hunks and any sidecar or INDEX edit made before the migration would all trip it.
- The thorough tier is `make test-all`; the core tier is bare `python3 -m pytest` (AGENTS.md repository development contract).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -n 'Carrier: cxxmyv' .aw/records/plans/pending/20261102-metastore-*.ipd.md` (2026-11-02; re-run at review 2026-11-06: rows in 11 sibling plans, `tve77h`, `1ajqaa`, `dcerjg`, `ya4ee4`, `2xwb9b`, `xexn45`, `ffceq0`, `t4gl15`, `59aiyh`, `9o83cr`, `90iqr1`; `7ehv8l` has none) | Every sibling that has a log-format half defers it here; the Scope check maps each row to an E-item. |
| F-02 | `ya4ee4` OQ-02 and `2xwb9b` OQ-02 | Both maintainer questions were answered on 2026-11-02 (OQ-01, OQ-02 below); E-01 applies OQ-02 and E-14 implements OQ-01. |
| F-03 | `90iqr1` E-08 to E-10 | The documentation arrives as a patch file guarded by a core test; this plan applies it and retires the guard. |
| F-04 | spec `4sd62s` 5.2 steps 0 to 7 | The migration itself is built and proven on a copy by `dcerjg`; this plan runs it for real. |
| F-05 | `ffceq0` E-11 (`aw meta repair <id6> [--apply] [--confirm]` in `meta_cli.py`); `2xwb9b` E-12 (`review_findings.review_attestation_missing` reads gate `review` rows through `artifact_meta.query`) | `aw meta repair` and the SR-601 `->reviewed` rule are built in phase B, not here. |
| F-06 | `aw reviews --help`: "the whole namespace is read-only and writes nothing"; `cli.py` has `--kind` on `aw ipd scaffold`, `aw research new`, `aw research mv` and `aw prompts new` | E-06 must change the namespace text; E-16 renames these options. |
| F-07 | `tests/test_attention.py` `REPO_ROOT` and `att.scan(REPO_ROOT)`; `pyproject.toml` `livecorpus` marker | Some tests read this repository's own records; after the E-03 schema flip they are refused until E-10 migrates the repository, so E-09 cannot demand a fully green tree before the migration. E-17 runs both tiers on the migrated copy instead. |
| F-08 | (written by E-17) | The mechanism that puts the migration and the task group 2 changes in one commit. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: the model decision, a real dry run and the AC-13 before values.
2. E-03 to E-08 and E-14 to E-16: the code and documentation switch in one working tree.
3. E-09, E-17, E-10: both test tiers, a full rehearsal on a copy, then the attended migration commit.
4. E-11 to E-13: real-repository demonstrations, measurements, changelog, finalize.

## Deferred / out of scope (with reason)

- The execution record (`finalize` and `turn` events) and the run index: separate specs, implemented after this cutover through the registry.
  - Carrier: nq1src
- The run index tables.
  - Carrier: f4p4vn

## Scope check

- Over-scope: none.
- Under-scope: none. Each `Carrier: cxxmyv` row from F-01 maps to an E-item: `tve77h` (loader and writer switch) and `dcerjg` (legacy loader into `m0001`, `CURRENT_METADATA_SCHEMA`) to E-03; `2xwb9b` (`append` legacy branch, `LegacyRender`, path-keyed target) to E-03, and its AC-31 (2) to E-11; `xexn45` and `9o83cr` (`write_legacy`, folded value writers) to E-03; `xexn45`, `9o83cr` and `dcerjg` (rename and path events, rename ledger, sidecar writer and ignore lines, INDEX ignore lines and skip names) to E-04, with the on-disk deletions done by migration steps 2 and 5 in E-10; `t4gl15` and `9o83cr` (post-cutover gates, terminal-log hook rules) to E-05; `ffceq0` (`last_history_at`, logged-path drift) to E-15; `90iqr1` (patch, two commands, `Kind` option renames, F-07 tests) to E-06, E-08 and E-16; `59aiyh` (builder, setter-byte assertions, `review-pilot` corpus) to E-07; `9o83cr` (AC-1 audit re-run) to E-11; and the real-repository evidence (AC-2 from `1ajqaa`; AC-10, AC-11, AC-16, AC-22 case 2, AC-30 case 3 and AC-41 from `dcerjg`; AC-36 case 6 and the generation cost from `ya4ee4`; AC-7 from `ffceq0`; AC-16 case 2 from `t4gl15`) to E-02, E-10, E-11 and E-12. The leak-sanitizer note of `t4gl15` is covered by E-10's sanitizer run. OQ-01 is implemented by E-14.

## Required tests / validation

- Owns, finally on the real repository: AC-1b, AC-13, AC-16, and the real-repository forms of AC-1, AC-2, AC-3, AC-6, AC-7, AC-9, AC-10, AC-11, AC-22 case 2, AC-30 cases 2 and 3, AC-31, AC-34, AC-36 case 6 and AC-41. Each was first proven on fixtures by the child named in the Scope check.
- Commands: bare `python3 -m pytest` and `make test-all` on the switched tree (E-09) and on the migrated copy (E-17); `aw check meta`, `aw sanitize --agent` and a second `--apply` after the real apply (E-10); the AC evidence of E-11; the AC-13 table of E-12.
- New behavioral tests: E-14 (`overrides`, `--date` refusal), E-15 (`last_history_at`, path drift), E-06 (`aw reviews record`, `aw walkthrough new`), E-16 (renamed options and aliases), E-05 (post-cutover gates). Each calls the real code or CLI on a fixture and asserts on outputs, exit codes and file bytes.

## Spec / documentation sync

No spec change is planned. The OQ-01 `overrides` key and the `--date` refusal are already in spec 4.2 (verified at review). This plan executes spec `4sd62s` section 7 step 9 and section 5.2, and lands the section 5.4 documentation prepared by `90iqr1`, including the AGENTS.md executed-plan rule amendment of 5.2 step 4a. If E-17 adds a way for `m0001` to stage paths beyond its own conversion output, amend spec 5.2 step 7 ("the migration's own list of paths") in the same change to say so, because that step is the contract the AC-16 hooks and the step-4a marker are reviewed against; the spec file is in `- Scope-Paths:` for that reason.

## Open questions

### OQ-01: Where do history-only setter flags go after the cutover?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Question: `--allow-open-questions`, `--allow-terminal-reopen` and `--allow-unresolvable-release-sentinel` appear today only in the history line, and `aw specs set --date` sets the history line's day; an event's `at` is always its write time. Where do they go once history is events?
- Recommendation: a structured `overrides` list on the event, and refuse `--date`.
- Closes when: the spec and this plan state the rule.
- Resolution or deferral rationale: RESOLVED 2026-11-02 by the user via /askme: each event records any override flag in a structured `overrides` list (for example `["allow-open-questions"]`); `aw specs set --date` is refused after the cutover, because back-dating an event would misstate when it was written (the original day may still go in `--message`). Spec `4sd62s` 4.2 is amended in the same change to add the `overrides` key. No reason was given.

### OQ-02: Which host and model generate the short descriptions at the cutover?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Question: carried from `ya4ee4` OQ-02. The description generator must run tool-less (spec OQ-31); `ya4ee4` measured one opencode tool-less call on `google/gemini-3.1-flash-lite` at $0.0045 for a 32 KB plan.
- Recommendation: decide after the trial.
- Closes when: the rule is recorded (now) and applied in E-01.
- Resolution or deferral rationale: RESOLVED 2026-11-02 by the user via /askme: the cutover uses the cheapest model whose `ya4ee4` 40-record trial output the maintainer judges accurate; the default candidate is `google/gemini-3.1-flash-lite` on opencode (tool-less, OQ-31); the maintainer confirms the choice when reviewing the dry-run descriptions before `--apply`. No reason was given.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-01 validates E-01
  - Required evidence: quote the recorded host and model choice with the `ya4ee4` E-10 trial figures it rests on (per-record mean cost, extrapolated full-run cost and duration) and the maintainer's confirmation.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the full dry-run output of `aw migrate metadata` from the main checkout, with `git rev-parse --git-dir` and `git rev-parse --git-common-dir` printed beside it to show it is not a linked worktree: preflight lines including the sidecar record count (AC-22 case 2), the census with zero `unknown-field` and its orphan `id6` lines (AC-30 case 3), the rename map with one row per `_LEGACY_TIMESTAMP_RE` record (count re-derived at execution) showing `wvlk84` as `awphysical-17`, the citation report per location with its ambiguity-warning count and the list of deliberately unchanged citations, the description-journal counts, and the round-trip result; the AC-13 before values with each exact command; plus the maintainer's statement that the descriptions were reviewed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a behavioral fixture test run (pytest output with PASSED lines) showing `append` and `create` write `meta/<id6>.jsonl` and then the mirror, and that no setter run on a log-format fixture leaves a bullet block or a `## Workflow history` line in the file; the diff hunk setting `CURRENT_METADATA_SCHEMA = 2`; and `git diff --stat` showing the legacy loader removed from `artifact_meta.py` and added to `migrations/m0001_metadata_v2.py`. The repository-wide AC-1 `rg` audit is V-11's.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a fixture test run in which a spec setter, a backlog setter, `aw rename` and `aw group` each append the expected event and the fixture has no `records/history.jsonl` afterwards; a test showing a fresh `aw install` into a temporary repository writes no `records/history.jsonl` or INDEX ignore line; and `git status --porcelain --ignored -- .aw/.gitignore .aw/records/history.jsonl .aw/records/plans/STATUS.md` in this checkout showing them unchanged (the real deletions are V-10's and V-11's).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v` of the gate and hook tests showing a raw transition into `executed` refused, a finalize append and a rollup-retirement append accepted, a non-append log edit refused, a `set` of `readiness` on a terminal log refused, an OQ-30 terminal append accepted, and a mirror that differs from the replayed state reported.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `aw reviews record --help` and `aw walkthrough new --help`, the new `aw reviews --help` namespace text, the pytest summary of their behavioral tests including the refusal of `readiness` on a refinement event and of an off-vocabulary verdict, and the `tests/test_command_surface_declarations.py` summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the diff hunk setting `RECORD_FORMAT = "log"` in the shared builder; the bare core gate summary line on the switched tree with every failure listed and each one shown to be a "run `aw migrate metadata`" refusal of a test that reads this repository's own records; and the recorded `review-pilot` decision with its passing `tests/test_review_pilot.py` run.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste `git apply --stat` of the patch, `git status --short` showing the patch file and `tests/test_metastore_cutover_patch.py` deleted, and `rg -n '^- (Status|Readiness):' AGENTS.md` returning only quoted legacy examples.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste the `make test-all` and bare core gate summary lines with every failure listed and shown to be a "run `aw migrate metadata`" refusal of a test that reads this repository's own records; the `aw commit cxxmyv` output; `git status --porcelain -- .aw/records` printing nothing; and the second dry run's clean result on the same tree.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste the `aw migrate metadata --apply` output including the lock acquisition and any override (none expected), `aw check meta` with no findings, the `aw sanitize --agent` result with no `fail`, the commit hash with `git show --stat` listing both migrated records and the task group 2 paths, the hook output of that commit (no `--no-verify`), and the output of a second `--apply` showing no change.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: paste, per criterion, the command and its output, each labelled with its AC id and with where it ran (this checkout or `tmp/cxxmyv-demo`): AC-1, AC-1b, AC-2 (with `git rev-list --count HEAD` printing 1 in the clone), AC-3, AC-6, AC-7, AC-9, AC-11, AC-16 (including the `attention --check` exit code), AC-30 case 2, AC-31, AC-34, AC-36 case 6 and AC-41 cases 3 and 4; and `git status --porcelain` of this checkout before and after the demo-clone probes, equal.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: paste the AC-13 table with warm and cold values before (from the E-02 tree) and after, each row naming the exact command run, plus the log size, append time and generation cost lines.
  - Observed evidence:
  - Result: pending
- [ ] V-13 validates E-13
  - Required evidence: paste the `CHANGELOG.md` diff hunk, the `aw commit cxxmyv` output, and the `aw ipd finalize cxxmyv` output.
  - Observed evidence:
  - Result: pending
- [ ] V-14 validates E-14
  - Required evidence: paste `python3 -m pytest -o addopts="" -v` of the new tests showing an event with `overrides: ["allow-open-questions"]` after a setter run with that flag, no `overrides` key after a run without one, and `aw specs set --date` refused on a migrated fixture with its message and a byte-identical fixture.
  - Observed evidence:
  - Result: pending
- [ ] V-15 validates E-15
  - Required evidence: paste `python3 -m pytest -o addopts="" -v` of the new tests showing `last_history_at` and `last_history_precision` taken from the newest event, and `aw check meta` output on the fixture with the planted `path-drift` and on the clean fixture.
  - Observed evidence:
  - Result: pending
- [ ] V-16 validates E-16
  - Required evidence: paste the re-derived lists (the `Kind`-named options and the `90iqr1` F-07 tests), `--help` of each renamed command showing the new spelling, a test run showing each old spelling as an alias gives the same result, and the pytest summary of every F-07 test on the patched tree.
  - Observed evidence:
  - Result: pending
- [ ] V-17 validates E-17
  - Required evidence: paste, from the clone: the clone command line, the `git apply --index` result, the `aw migrate metadata --apply` output (no `--force`), the commit output with every hook result and `git show --stat` listing the migrated records and the task group 2 paths in one commit, and the bare core gate and `make test-all` summary lines with 0 failed; F-08 as written; and `git status --porcelain | sha256sum` of this checkout before and after, equal.
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one indivisible commit (C10a, spec 5.2): splitting it would put two formats on `main`.

Execute only with the maintainer present, in the main checkout that holds the history sidecar, after `90iqr1`, `dcerjg`, `ya4ee4` and `1ajqaa` are `executed`. OQ-01 and OQ-02 are resolved. The runner must not dispatch this plan unattended (`- Attended: required`).

Scope fence: `- Scope-Paths:` declares what this plan may change. The migration rewrites most of `.aw/records/`, which is declared. An edit outside the fence is made and then justified at finalize with `--scope-reason`.

Stop conditions (genuinely unsafe states, not scope questions): stop before E-10 if E-09 shows a test failure that is not an unmigrated-records refusal, if a dry run reports a census refusal, or if E-17 finds no form that makes one commit without `--force` or `--no-verify`. Stop and report if a concurrent edit to a file this plan must change cannot be combined safely.

Commits: the cutover itself is ONE commit, made by the migration's `aw commit --no-plan` with its own path list (5.2 step 7). This plan's own record edits are committed separately with `aw commit cxxmyv -- <paths>`: before the migration (E-09, so the preflight sees a clean records tree) and after it (E-13). Never `git add -A`, a bare `git add`, `git commit -a` or `--no-verify`; never push, and never run the pre-push hooks by pushing.

Honesty: paste the actual output of every test tier, the dry runs, the rehearsal, the apply, the sanitizer and each AC demonstration; never claim a result that was not run.

Lifecycle: this plan is `Attended: required`, so no runner finalizes it; the attending executor runs `aw ipd finalize cxxmyv`, which refuses until every `V-*` is `pass` with observed evidence. Never `git mv` the plan by hand.
