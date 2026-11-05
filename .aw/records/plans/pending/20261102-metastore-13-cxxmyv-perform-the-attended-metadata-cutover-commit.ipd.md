# IPD: Perform the attended metadata cutover commit

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` section 7 step 9 and section 5.2 require ONE attended commit that switches `artifact_meta` from the legacy bullet-block format to per-artifact event logs, runs migration `m0001` on this repository in the checkout that holds the gitignored history sidecar, applies the post-cutover documentation, and stamps `metadata_schema: 2`. Every earlier child deferred its log-format half here (measured 2026-11-02: deferral rows naming `Carrier: cxxmyv` in all 12 sibling plans), because C10a forbids a second on-disk format on `main` before this commit.
- Scope: The code switch to the log format and every deferred log-format item; the real migration on this repository; the documentation patch of `90iqr1`; the two commands documented there; and the final real-repository demonstrations of the acceptance criteria the earlier children proved on fixtures. One commit, attended by the maintainer.
- Scope-Paths: .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, agent_workflows/, tests/, .aw/records/, .aw/system/workflows/, .aw/.gitignore, .aw/config/project.json, .aw/AGENT_QUICKSTART.md, .aw/QUICKSTART.md, docs/, AGENTS.md, CHANGELOG.md, .aw/records/plans/pending/20261102-metastore-13-cxxmyv-perform-the-attended-metadata-cutover-commit.ipd.md
- Item-Dependencies: executed:90iqr1, executed:dcerjg, executed:ya4ee4, executed:1ajqaa
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Attended: required
- Set: metastore
- Order: 13
- Highest E allocated: 13
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: cxxmyv

## Workflow history
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Land the hard cutover: after this one commit the toolkit reads and writes only the event-log format, every record of this repository is migrated, the documentation describes commands instead of field syntax, and the acceptance criteria that need the real migrated repository are demonstrated on it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: decisions and preflight

- [ ] E-01 Apply the two recorded decisions before the code switch: pick the description model by this plan's OQ-02 rule from `ya4ee4`'s 40-record trial result and record the chosen host and model here; and implement OQ-01 in `artifact_meta`'s writer and the setters: every event carries an `overrides` list for `--allow-open-questions`, `--allow-terminal-reopen` and `--allow-unresolvable-release-sentinel`, and `aw specs set --date` is refused with a message once `metadata_schema` is 2.
  - Depends on: none
  - Expected outcome: the chosen model is recorded; a setter run with an override flag writes `overrides`; `aw specs set --date` refuses on a migrated fixture.
  - Execution state: pending

- [ ] E-02 In the maintainer's main checkout (never a runner lane), with the maintainer present, run `aw migrate metadata` (dry run) on the current tree and paste: the preflight lines (uncommitted record changes, integration lock, unmerged lanes, linked-worktree check, sidecar present with its record count, AC-22 case 2), the field census (AC-20), the rename map for the 34 legacy-timestamp records with `wvlk84` as `awphysical-17` (AC-41 case 1), the citation-rewrite report per location (OQ-27), the description-journal status (records with and without a description, OQ-22), and the round-trip result. The maintainer reviews the generated descriptions in the journal before E-11.
  - Depends on: E-01
  - Expected outcome: a clean dry run whose census has no `unknown-field` or unparseable value and whose description journal is complete or lists each deliberate absence.
  - Execution state: pending

### Task group 2: switch the code to the log format (one working tree, not yet committed)

- [ ] E-03 Switch `artifact_meta`'s loader and writer to the log format: `append` and `create` write `meta/<id6>.jsonl` with the 4.3 write order (log, in-file mirror, disposition, cache), the loader reads logs, and the legacy loader moves unchanged into `agent_workflows/migrations/m0001_metadata_v2.py`. Delete the legacy branch of `append` with `LegacyRender` and the path-keyed target (`2xwb9b`), switch `write_legacy` off (`xexn45`), and set `CURRENT_METADATA_SCHEMA` to 2 (`dcerjg`).
  - Depends on: E-02
  - Expected outcome: no module outside `migrations/m0001_metadata_v2.py` can produce a bullet block or a `## Workflow history` line.
  - Execution state: pending

- [ ] E-04 Turn on the log-only writers: path-bearing events and `rename` events for `aw rename`, `aw group` and `aw archive plans`, retiring the rename ledger (`xexn45`, AC-31, AC-34); retire `record_history.append`, `append_advisory` and `append_rename`, and remove `records/history.jsonl` from the `.aw/.gitignore` template, the `engine._ensure_aw_gitignore` adder and `placement_switch.py` (`dcerjg`, `9o83cr`, AC-30 case 2); delete the on-disk `INDEX.*` files, the tracked `plans/STATUS.md`, the INDEX ignore lines and the skip-name entries that protected scans from them (`9o83cr`).
  - Depends on: E-03
  - Expected outcome: a spec setter, a backlog setter, a rename and a group create no `history.jsonl`; no INDEX file exists.
  - Execution state: pending

- [ ] E-05 Put the gates and readers in their post-cutover form: "mirrored status differs from replayed state" and "staged log violates append rules" in `check_engine` and the hooks, the executed transition accepted only as a finalize append or a rollup-retirement append (`t4gl15`, AC-16 case 2); the terminal-log rules of the `meta/*.jsonl` append-only hook that OQ-30 allows (`9o83cr`); `last_history_at` from the newest post-cutover event with `last_history_precision`, and the logged-path drift row of `aw check meta` (`ffceq0`); and the `->reviewed` gate-only attestation rule (spec 4.4, SR-601).
  - Depends on: E-03
  - Expected outcome: each gate refuses its post-cutover violation in a fixture and accepts the allowed appends.
  - Execution state: pending

- [ ] E-06 Build the two commands documented by `90iqr1`: `aw reviews record` (appends one `review` event per spec 4.1a, with `review_kind`, `verdict`, optional `readiness` and `review_depth`; refuses `readiness` on a refinement event and any verdict outside the vocabulary of its kind) and `aw walkthrough new` (creates a walkthrough with its log over `set_records.write_walkthrough`), plus the `aw meta repair` CLI verb over `artifact_meta.repair` (`tve77h`).
  - Depends on: E-03
  - Expected outcome: `--help` of each command shows the documented arguments; behavioral tests pass.
  - Execution state: pending

- [ ] E-07 Switch the shared test record builder to `RECORD_FORMAT = "log"` and convert the setter-byte assertions to `artifact_meta.read` plus the in-file mirror (`59aiyh`); keep the legacy-format tests that must keep literal input (the legacy loader, migration round-trip and conversion tests) pointing at `m0001`.
  - Depends on: E-03
  - Expected outcome: the bare core gate passes on the switched tree before the migration runs.
  - Execution state: pending

- [ ] E-08 Apply the `90iqr1` documentation patch with `git apply .aw/system/cutover/metastore-docs.cutover.patch` (regenerate it from `90iqr1`'s scratch-worktree steps if it no longer applies), and delete the patch file and `tests/test_metastore_cutover_patch.py`, whose job ends here.
  - Depends on: E-06
  - Expected outcome: the documents, managed block, templates and quickstarts describe the log-format commands; the patch file is gone.
  - Execution state: pending

### Task group 3: run the migration and commit

- [ ] E-09 Run the full thorough tier `make test-all` and the bare core gate on the switched, not-yet-migrated tree, then `aw migrate metadata` (dry run) once more on this exact tree; any failure or census refusal stops the cutover here with nothing committed.
  - Depends on: E-04, E-05, E-07, E-08
  - Expected outcome: both test tiers pass; the dry run is clean.
  - Execution state: pending

- [ ] E-10 With the maintainer present, run `aw migrate metadata --apply` in the main checkout. Acquire the integration lock through the migration (5.2 step 1); do not pass `--force` or `--force-worktree` unless the maintainer explicitly decides to and the override is recorded. The migration renames, converts, rewrites citations, writes the terminal-exception marker, runs `aw check meta` and `aw sanitize --agent` on the staged tree (5.2 step 6), writes `metadata_schema: 2`, and makes its one commit through `aw commit --no-plan` with its own path list, folding in the code, test and documentation changes of E-03 to E-08.
  - Depends on: E-09
  - Expected outcome: one commit; `aw check meta` reports no findings; the sanitizer reports no `fail`; `aw migrate metadata --apply` run again changes nothing (AC-10).
  - Execution state: pending

### Task group 4: demonstrate on the real repository

- [ ] E-11 Demonstrate on the migrated repository the criteria that need it: AC-1b (thorough tier summary at the cutover commit; no migrated record has a bullet block; no `meta/` directory existed before), AC-2 (`git clone --depth 1` plus `aw show <id6> --history` on a migrated plan with several events), AC-3 (two-branch merge of different artifacts' status changes), AC-6 (a real transition's diff), AC-7 (zero `aw check meta` findings), AC-9 (`git ls-files` shows no INDEX or STATUS file), AC-16 (the commit passed every installed gate without `--no-verify`; a later raw edit to an executed plan is refused), AC-31 (rename and group events; no sidecar created), AC-34 (path history of a renamed legacy record shows the old path then the new one), AC-36 case 6 (the real census of descriptions), AC-41 (no legacy-timestamp artifact filename; no two plans share Set and order).
  - Depends on: E-10
  - Expected outcome: each criterion's required evidence pasted from the real repository.
  - Execution state: pending

- [ ] E-12 Measure AC-13 by the AGENTS.md end-to-end rule, warm and cold: bytes an agent reads for one plan, and the end-to-end time of `aw find` and `aw attention`, before (recorded in E-02 on the unmigrated tree) and after; the size of a typical executed plan's log and the time of one append to it; and the short-description generation cost from the journal.
  - Depends on: E-10
  - Expected outcome: a before and after table with the commands used; no target value is asserted (the spec sets none).
  - Execution state: pending

- [ ] E-13 Add one `CHANGELOG.md` entry for the metadata cutover (no em or en dashes), set this plan's status through the tooled finalize, and confirm the orchestrator `63ib9r` can be retired.
  - Depends on: E-11, E-12
  - Expected outcome: `aw ipd finalize cxxmyv` succeeds after every `V-*` is `pass`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The cutover runs in the checkout that holds `.aw/records/history.jsonl` (spec 5.2 step 1, 3c); a runner lane has no sidecar, so this plan is `Attended: required` and is never dispatched unattended.
- Hand publishes to `main` hold the integration lock (AGENTS.md "Before you publish to main by hand"); the migration acquires it itself (5.2 step 1).
- Commits go through `aw commit`; the migration's commit uses `aw commit --no-plan` with its own path list (5.2 step 7).
- The thorough tier is `make test-all`; the core tier is bare `python3 -m pytest` (AGENTS.md repository development contract).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -n 'Carrier: cxxmyv' .aw/records/plans/pending/20261102-metastore-*.ipd.md` (2026-11-02) | Every sibling defers its log-format half here; E-03 to E-08 and E-11 cover each deferred row. |
| F-02 | `ya4ee4` OQ-02 and `2xwb9b` OQ-02 | Two maintainer questions are open and must be answered before the code switch (E-01). |
| F-03 | `90iqr1` E-08 to E-10 | The documentation arrives as a patch file guarded by a core test; this plan applies it and retires the guard. |
| F-04 | spec `4sd62s` 5.2 steps 0 to 7 | The migration itself is built and proven on a copy by `dcerjg`; this plan runs it for real. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: decisions and a real dry run.
2. E-03 to E-08: the code and documentation switch in one working tree.
3. E-09, E-10: both test tiers, then the attended migration commit.
4. E-11 to E-13: real-repository demonstrations, measurements, changelog, finalize.

## Deferred / out of scope (with reason)

- The execution record (`finalize` and `turn` events) and the run index: separate specs, implemented after this cutover through the registry.
  - Carrier: nq1src
- The run index tables.
  - Carrier: f4p4vn

## Scope check

- Over-scope: none.
- Under-scope: none. Each `Carrier: cxxmyv` row from F-01 maps to E-03 (loader and writer switch, `append` legacy branch, `write_legacy`, schema stamp), E-04 (rename events, sidecar retirement, INDEX and STATUS files), E-05 (post-cutover gates, `last_history_at`, path drift, `->reviewed`), E-06 (two commands, `aw meta repair`), E-07 (test builder), E-08 (documentation patch) and E-11 (real-repository AC demonstrations, including AC-2 from `1ajqaa`, AC-22 case 2 and AC-30 case 3 from `dcerjg`, AC-36 case 6 from `ya4ee4`, AC-7 from `ffceq0`, AC-16 case 2 from `t4gl15`). The leak-sanitizer note of `t4gl15` is covered by E-10's sanitizer run.

## Required tests / validation

- Owns, finally on the real repository: AC-1b, AC-13, AC-16, and the real-repository forms of AC-2, AC-3, AC-6, AC-7, AC-9, AC-10, AC-11, AC-22 case 2, AC-30 case 3, AC-31, AC-34, AC-36 case 6 and AC-41. Each was first proven on fixtures by the child named in the Scope check.
- Commands: `make test-all` and bare `python3 -m pytest` before the migration (E-09); `aw check meta`, `aw sanitize --agent` and a second `--apply` after it (E-10); the AC evidence of E-11; the AC-13 table of E-12.

## Spec / documentation sync

No spec change. This plan executes spec `4sd62s` section 7 step 9 and section 5.2, and lands the section 5.4 documentation prepared by `90iqr1`, including the AGENTS.md executed-plan rule amendment of 5.2 step 4a.

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
  - Required evidence: quote the recorded model choice with the trial figures it rests on, and paste a test run showing an event with `overrides: ["allow-open-questions"]` and `aw specs set --date` refused with its message on a migrated fixture.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the full dry-run output of `aw migrate metadata` from the main checkout: preflight lines including the sidecar record count, the census with zero `unknown-field`, the 34-row rename map showing `wvlk84` as `awphysical-17`, the citation report per location, the description-journal counts, and the round-trip result; plus the maintainer's statement that the descriptions were reviewed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n -e '^- (Status|Id|Set):' -e '## Workflow history' agent_workflows/` showing matches only under `agent_workflows/migrations/`, the diff hunk setting `CURRENT_METADATA_SCHEMA = 2`, and a fixture test run showing `append` writes `meta/<id6>.jsonl` with the 4.3 write order.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a test run in which a spec setter, a backlog setter, `aw rename` and `aw group` each append the expected event and `ls .aw/records/history.jsonl` fails afterwards; and `git ls-files | rg 'INDEX\.(json|md)|plans/STATUS\.md'` returning nothing on the switched tree.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v` of the gate and hook tests showing a raw transition into `executed` refused, a finalize append and a rollup-retirement append accepted, a non-append log edit refused, an OQ-30 terminal append accepted, a refinement-only spec refused `->reviewed`, and `aw check meta` reporting a planted `path-drift`.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `aw reviews record --help`, `aw walkthrough new --help` and `aw meta repair --help`, and the pytest summary of their behavioral tests including the refusal of `readiness` on a refinement event.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the diff hunk setting `RECORD_FORMAT = "log"` in the shared builder and the bare core gate summary line on the switched tree.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste `git apply --stat` of the patch, `git status --short` showing the patch file and `tests/test_metastore_cutover_patch.py` deleted, and `rg -n '^- (Status|Readiness):' AGENTS.md` returning only quoted legacy examples.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste the `make test-all` summary line, the bare core gate summary line, and the second dry run's clean result on the same tree.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste the `aw migrate metadata --apply` output including the lock acquisition, `aw check meta` with no findings, the `aw sanitize --agent` result with no `fail`, the commit hash, and the output of a second `--apply` showing no change.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: paste, per criterion, the command and its output from the real repository: AC-1b, AC-2, AC-3, AC-6, AC-7, AC-9, AC-16, AC-31, AC-34, AC-36 case 6 and AC-41, each labelled with its AC id.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: paste the AC-13 table with warm and cold values before (from the E-02 tree) and after, each row naming the exact command run, plus the log size, append time and generation cost lines.
  - Observed evidence:
  - Result: pending
- [ ] V-13 validates E-13
  - Required evidence: paste the `CHANGELOG.md` diff hunk and the `aw ipd finalize cxxmyv` output.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one indivisible commit (C10a, spec 5.2): splitting it would put two formats on `main`.

Execute only with the maintainer present, in the main checkout that holds the history sidecar, after `90iqr1`, `dcerjg`, `ya4ee4` and `1ajqaa` are `executed` and OQ-01 and OQ-02 are answered. The runner must not dispatch this plan unattended (`- Attended: required`). Commit only through the migration's `aw commit --no-plan` path list and this plan's own `aw commit cxxmyv -- <paths>` for its records; never push. Paste the actual output of every test tier, the dry runs, the apply, the sanitizer and each AC demonstration. The lifecycle move is `aw ipd finalize`, which refuses until every `V-*` is `pass` with observed evidence.
