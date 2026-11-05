# IPD: Build the artifact metadata store of spec 4sd62s (orchestrator)

- Date: 2026-11-02
- Kind: orchestrator
- Concern: Spec `4sd62s` (artifact metadata store, approved 2026-11-02, `Blocks-Release: next`) replaces hand-editable bullet metadata and `## Workflow history` sections with tracked per-artifact event logs, a SQLite read cache and one interface, `artifact_meta`, ending with a one-commit attended cutover (spec section 7). None of it exists yet.
- Scope: Orchestration only: sequence the thirteen children below and confirm each reaches `executed`. No code, test or record work of its own.
- Scope-Paths: .aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md
- Item-Dependencies: none
- Status: to-review
- From-Spec: 4sd62s
- Coverage: pass
- Coverage-Fingerprint: b5e3d8673f4a0f16c3cf9c8e81270fd96a2ed933797803bc58c327c3e79e2447
- Coverage-Checked: 2026-11-05 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 0
- Highest E allocated: 13
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 63ib9r

## Workflow history
- 2026-11-05 to-review (aw set): authored review-ready: orchestrates spec 4sd62s across 13 children; coverage pass

- 2026-11-05 coverage pass (aw oc run): fingerprint b5e3d8673f4a, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-05 coverage fail (aw oc run): fingerprint c66561f7c8ed, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Build spec `4sd62s` as thirteen independently executable children in the facade-first order of spec section 7, ending with the attended cutover commit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Children

- [ ] E-01 CONFIRM 7ehv8l REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans 7ehv8l` shows it under `executed/`.
  - Execution state: pending

- [ ] E-02 CONFIRM tve77h REACHED executed
  - Depends on: none
  - Expected outcome: `aw find plans tve77h` shows it under `executed/`.
  - Execution state: pending

- [ ] E-03 CONFIRM 1ajqaa REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans 1ajqaa` shows it under `executed/`.
  - Execution state: pending

- [ ] E-04 CONFIRM dcerjg REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans dcerjg` shows it under `executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM ya4ee4 REACHED executed
  - Depends on: E-04
  - Expected outcome: `aw find plans ya4ee4` shows it under `executed/`.
  - Execution state: pending

- [ ] E-06 CONFIRM 2xwb9b REACHED executed
  - Depends on: E-02, E-01
  - Expected outcome: `aw find plans 2xwb9b` shows it under `executed/`.
  - Execution state: pending

- [ ] E-07 CONFIRM xexn45 REACHED executed
  - Depends on: E-02, E-06
  - Expected outcome: `aw find plans xexn45` shows it under `executed/`.
  - Execution state: pending

- [ ] E-08 CONFIRM ffceq0 REACHED executed
  - Depends on: E-02, E-07
  - Expected outcome: `aw find plans ffceq0` shows it under `executed/`.
  - Execution state: pending

- [ ] E-09 CONFIRM t4gl15 REACHED executed
  - Depends on: E-02, E-07, E-08
  - Expected outcome: `aw find plans t4gl15` shows it under `executed/`.
  - Execution state: pending

- [ ] E-10 CONFIRM 59aiyh REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans 59aiyh` shows it under `executed/`.
  - Execution state: pending

- [ ] E-11 CONFIRM 9o83cr REACHED executed
  - Depends on: E-08, E-09, E-10
  - Expected outcome: `aw find plans 9o83cr` shows it under `executed/`.
  - Execution state: pending

- [ ] E-12 CONFIRM 90iqr1 REACHED executed
  - Depends on: E-11
  - Expected outcome: `aw find plans 90iqr1` shows it under `executed/`.
  - Execution state: pending

- [ ] E-13 CONFIRM cxxmyv REACHED executed
  - Depends on: E-12, E-04, E-05, E-03
  - Expected outcome: `aw find plans cxxmyv` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `7ehv8l` | `20261102-metastore-01-7ehv8l-supersede-spec-2vev8j-and-re-home-backlog-ms06pi-s-release-g.ipd.md` | Supersede spec 2vev8j and re-home backlog ms06pi's release gate to 4sd62s. | none |
| 02 | `tve77h` | `20261102-metastore-02-tve77h-build-the-artifact-meta-core-registry-event-schema-append-ke.ipd.md` | Build the artifact_meta core: registry, event schema, append key, SQLite cache, legacy loader. | none |
| 03 | `1ajqaa` | `20261102-metastore-03-1ajqaa-serve-aw-show-history-aw-show-format-json-and-aw-index-rebui.ipd.md` | Serve aw show --history, aw show --format json and aw index rebuild through artifact_meta. | `executed:tve77h` |
| 04 | `dcerjg` | `20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md` | Build the migration chain and the m0001 dry run with census, renames, citations and round trip. | `executed:tve77h` |
| 05 | `ya4ee4` | `20261102-metastore-05-ya4ee4-build-the-short-description-journal-and-the-tool-less-saniti.ipd.md` | Build the short-description journal and the tool-less sanitized generation prompt. | `executed:dcerjg` |
| 06 | `2xwb9b` | `20261102-metastore-06-2xwb9b-move-the-status-set-setter-engine-onto-artifact-meta.ipd.md` | Move the status_set setter engine onto artifact_meta. | `executed:tve77h`, `executed:7ehv8l` |
| 07 | `xexn45` | `20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md` | Move the remaining metadata writers onto artifact_meta. | `executed:tve77h`, `executed:2xwb9b` |
| 08 | `ffceq0` | `20261102-metastore-08-ffceq0-move-selectors-check-engine-attention-and-ipd-lint-reads-ont.ipd.md` | Move selectors, check_engine, attention and ipd_lint reads onto artifact_meta. | `executed:tve77h`, `executed:xexn45` |
| 09 | `t4gl15` | `20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md` | Move runner, gate, hook and module reads onto artifact_meta and read_at. | `executed:tve77h`, `executed:xexn45`, `executed:ffceq0` |
| 10 | `59aiyh` | `20261102-metastore-10-59aiyh-move-test-data-to-one-shared-record-builder-over-artifact-me.ipd.md` | Move test data to one shared record builder over artifact_meta. | `executed:tve77h` |
| 11 | `9o83cr` | `20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md` | Delete INDEX and STATUS code and every legacy parser outside artifact_meta. | `executed:ffceq0`, `executed:t4gl15`, `executed:59aiyh` |
| 12 | `90iqr1` | `20261102-metastore-12-90iqr1-rewrite-documents-managed-block-templates-and-quickstarts-fo.ipd.md` | Rewrite documents, managed block, templates and quickstarts for the log format. | `executed:9o83cr` |
| 13 | `cxxmyv` | `20261102-metastore-13-cxxmyv-perform-the-attended-metadata-cutover-commit.ipd.md` | Perform the attended metadata cutover commit. | `executed:90iqr1`, `executed:dcerjg`, `executed:ya4ee4`, `executed:1ajqaa` |

Phase A (Orders 01 to 05) adds code on today's format and moves no caller; Order 01 is records only. Phase B (Orders 06 to 11) moves every writer and reader onto `artifact_meta` while the on-disk format stays the legacy bullet block, so `main` has one format at every merge (spec C10a). Order 12 prepares the post-cutover documentation as a patch file that never reaches the live documents before the cutover. Order 13 is `Attended: required`: it runs in the maintainer's main checkout, which holds the history sidecar, so an `--unattended` run holds it `not-run` and this orchestrator cannot retire until Order 13 has been run attended.

## Completion criteria (the whole Set is done only when)

- Spec `2vev8j` is superseded and backlog `ms06pi`'s release gate is carried by `4sd62s`. Owner: `7ehv8l`.
- `artifact_meta` provides the registry, event schema, `append` key, path rule, cache and legacy loader (AC-4, AC-5, AC-8, AC-17, AC-18, AC-23, AC-24, AC-26, AC-33, AC-39). Owner: `tve77h`.
- `aw show --history`, `aw show --format json` and `aw index rebuild` exist (AC-2 on a fixture). Owner: `1ajqaa`.
- Migration `m0001` is built and proven on a copy (AC-10, AC-11, AC-14, AC-14a(5), AC-19, AC-20, AC-22(1), AC-27, AC-28, AC-29, AC-30, AC-32, AC-40, AC-41). Owner: `dcerjg`.
- Short descriptions are generated tool-less and sanitized through the journal (AC-36 cases 3, 4, 5, 7). Owner: `ya4ee4`.
- Every writer goes through `artifact_meta` (AC-15, AC-14a(1-4), AC-21, AC-31 phase-B form). Owners: `2xwb9b`, `xexn45`.
- Every reader goes through `artifact_meta` or `read_at` (AC-1a, AC-7, AC-9 reader part, AC-12). Owners: `ffceq0`, `t4gl15`.
- Test data uses one shared record builder. Owner: `59aiyh`.
- No legacy parser or INDEX/STATUS code remains outside `artifact_meta` (AC-1, AC-9). Owner: `9o83cr`.
- The post-cutover documentation is ready as an applicable patch. Owner: `90iqr1`.
- The cutover commit has landed and the real-repository criteria are demonstrated (AC-1b, AC-13, AC-16, and the real forms of AC-2, AC-3, AC-6, AC-7, AC-9, AC-10, AC-11, AC-22(2), AC-30(3), AC-31, AC-34, AC-36(6), AC-41). Owner: `cxxmyv`.

## Cross-IPD validation

- Interface consistency is owned by the phase-B children themselves: `2xwb9b`, `xexn45`, `ffceq0`, `t4gl15` and `59aiyh` each call the `artifact_meta` names `tve77h` defines, and each of their `V-*` items runs its moved consumers' existing tests against that interface.
- The migration `cxxmyv` runs is the one `dcerjg` proved on a copy, with the description journal of `ya4ee4`.
- The documentation `cxxmyv` lands is `90iqr1`'s patch, guarded until then by `90iqr1`'s apply test.
- Post-merge revalidation of each child is the runner's merge-and-revalidate gate, not work of this plan.

## Deferred / out of scope (with reason)

- The execution record (`finalize` and `turn` events, per-item cost) and the run index were split out of `4sd62s` on 2026-11-01 and are implemented after this Set's cutover.
  - Carrier: nq1src
- The run index.
  - Carrier: f4p4vn

## Scope check

- Over-scope: none.
- Under-scope: none. Every step of spec section 7 has a child: step 1 `tve77h`, step 2 `1ajqaa`, step 3 `dcerjg` and `ya4ee4`, step 4 `2xwb9b` and `xexn45`, step 5 `ffceq0` and `t4gl15`, step 6 `59aiyh`, step 7 `9o83cr`, step 8 `90iqr1`, step 9 `cxxmyv`, and the OQ-4 supersede step `7ehv8l`.

## Required tests / validation

This plan runs no tests. Each child runs its own suites; `cxxmyv` performs the whole-repository demonstration at the cutover.

## Open questions

### OQ-01: Should Orders 02 and 04 be split now, as their own open questions propose?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Not now. Both are within the size limits (18 and 16 E-items, 5 task groups), and each records a concrete split point; `/plan-review` of each child decides. A split adds rows to this table before approval, so it cannot leave an unauthored row. Recommendation strength: medium.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw find plans 7ehv8l` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw find plans tve77h` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans 1ajqaa` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw find plans dcerjg` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw find plans ya4ee4` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw find plans 2xwb9b` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `aw find plans xexn45` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `aw find plans ffceq0` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `aw find plans t4gl15` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `aw find plans 59aiyh` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `aw find plans 9o83cr` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste `aw find plans 90iqr1` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `aw find plans cxxmyv` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) of this plan and of each child. This plan performs no work of its own; each child carries its own scope fence, test evidence and path-scoped `aw commit`. Each `V-*` item MUST paste the actual `aw find plans <id6>` output. Under `aw oc run` / `aw agy run` the runner retires this plan once every child is `executed` on disk. When executing by hand, run the children in table order (Order 13 attended), then confirm each, run `aw ipd lint --phase pre-transition` and `aw ipd finalize` on this plan. Commit only through `aw commit 63ib9r -- <paths>`; never push.
