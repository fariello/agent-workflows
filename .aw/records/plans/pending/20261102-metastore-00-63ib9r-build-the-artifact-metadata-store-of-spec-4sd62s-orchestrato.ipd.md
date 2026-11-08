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
- Coverage-Fingerprint: 5ee2b9b89d8cfcf55ea03736d7f2c70f6b0959df95e67e12e9ea731944386b14
- Coverage-Checked: 2026-11-08 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 0
- Highest E allocated: 54
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 63ib9r
- Review-Depth: orchestrator

## Workflow history
- 2026-11-08 coverage pass (aw oc run): fingerprint 5ee2b9b89d8c, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): child table and checklist regenerated for the step-complexity split (54 children; Orders 15-62 are split parts plus the 653ndz codemod; ordering by dependency edges).
- 2026-11-07 coverage pass (aw oc run): fingerprint 979ef50d956a, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-11-07 to-review (aw set): demoted approved -> to-review: APPROVAL WITHDRAWN: maintainer direction 2026-11-07: paused before re-review; the metastore plans MUST build the tools that migrate ANY repo from ANY prior format (.agents layout, id-less/untitled records, no sidecar), not only this repository. Re-review against the amended spec 4sd62s before re-approval.
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 FIXED; review record .aw/records/reviews/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.review.md
- 2026-11-06 coverage pass (aw oc run): fingerprint 96fe24cd857b, model uri/its_direct/pt3-claude-opus-5.5-1m-us
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
  - Depends on: E-02, E-15, E-16, E-17, E-18, E-19
  - Expected outcome: `aw find plans dcerjg` shows it under `executed/`.
  - Execution state: pending

- [ ] E-05 CONFIRM ya4ee4 REACHED executed
  - Depends on: E-04, E-20
  - Expected outcome: `aw find plans ya4ee4` shows it under `executed/`.
  - Execution state: pending

- [ ] E-06 CONFIRM 2xwb9b REACHED executed
  - Depends on: E-02, E-01
  - Expected outcome: `aw find plans 2xwb9b` shows it under `executed/`.
  - Execution state: pending

- [ ] E-07 CONFIRM xexn45 REACHED executed
  - Depends on: E-02, E-06, E-21, E-22, E-23, E-24, E-25, E-26
  - Expected outcome: `aw find plans xexn45` shows it under `executed/`.
  - Execution state: pending

- [ ] E-08 CONFIRM ffceq0 REACHED executed
  - Depends on: E-02, E-07, E-14, E-27, E-28, E-29, E-30, E-31, E-32
  - Expected outcome: `aw find plans ffceq0` shows it under `executed/`.
  - Execution state: pending

- [ ] E-09 CONFIRM t4gl15 REACHED executed
  - Depends on: E-02, E-07, E-08, E-14, E-36, E-33, E-35, E-34
  - Expected outcome: `aw find plans t4gl15` shows it under `executed/`.
  - Execution state: pending

- [ ] E-10 CONFIRM 59aiyh REACHED executed
  - Depends on: E-02, E-07, E-14, E-50, E-39, E-37, E-40, E-38, E-49
  - Expected outcome: `aw find plans 59aiyh` shows it under `executed/`.
  - Execution state: pending

- [ ] E-11 CONFIRM 9o83cr REACHED executed
  - Depends on: E-08, E-09, E-10, E-03, E-04, E-14, E-46, E-48, E-45, E-43, E-41, E-42
  - Expected outcome: `aw find plans 9o83cr` shows it under `executed/`.
  - Execution state: pending

- [ ] E-12 CONFIRM 90iqr1 REACHED executed
  - Depends on: E-11
  - Expected outcome: `aw find plans 90iqr1` shows it under `executed/`.
  - Execution state: pending

- [ ] E-14 CONFIRM g5hpbb REACHED executed
  - Depends on: E-04
  - Expected outcome: `aw find plans g5hpbb` shows it under `executed/`.
  - Execution state: pending

- [ ] E-13 CONFIRM cxxmyv REACHED executed
  - Depends on: E-12, E-04, E-05, E-03, E-14, E-51, E-53, E-48, E-44, E-52, E-47, E-54
  - Expected outcome: `aw find plans cxxmyv` shows it under `executed/`.
  - Execution state: pending

### Task group 2: split parts (added 2026-11-07)

- [ ] E-15 CONFIRM vxevph REACHED executed
  - Depends on: E-02
  - Expected outcome: `aw find plans vxevph` shows it under `executed/`.
  - Execution state: pending

- [ ] E-16 CONFIRM 1vfqdu REACHED executed
  - Depends on: E-02, E-15
  - Expected outcome: `aw find plans 1vfqdu` shows it under `executed/`.
  - Execution state: pending

- [ ] E-17 CONFIRM dky26u REACHED executed
  - Depends on: E-02, E-15
  - Expected outcome: `aw find plans dky26u` shows it under `executed/`.
  - Execution state: pending

- [ ] E-18 CONFIRM ghhzb6 REACHED executed
  - Depends on: E-02, E-15, E-17
  - Expected outcome: `aw find plans ghhzb6` shows it under `executed/`.
  - Execution state: pending

- [ ] E-19 CONFIRM hpedmn REACHED executed
  - Depends on: E-02, E-15, E-17, E-18
  - Expected outcome: `aw find plans hpedmn` shows it under `executed/`.
  - Execution state: pending

- [ ] E-20 CONFIRM odeo9z REACHED executed
  - Depends on: E-04
  - Expected outcome: `aw find plans odeo9z` shows it under `executed/`.
  - Execution state: pending

- [ ] E-21 CONFIRM 7yr827 REACHED executed
  - Depends on: E-02, E-06
  - Expected outcome: `aw find plans 7yr827` shows it under `executed/`.
  - Execution state: pending

- [ ] E-22 CONFIRM g6tw94 REACHED executed
  - Depends on: E-02, E-06, E-21
  - Expected outcome: `aw find plans g6tw94` shows it under `executed/`.
  - Execution state: pending

- [ ] E-23 CONFIRM n5sxxk REACHED executed
  - Depends on: E-02, E-06, E-21, E-22
  - Expected outcome: `aw find plans n5sxxk` shows it under `executed/`.
  - Execution state: pending

- [ ] E-24 CONFIRM 6e93gt REACHED executed
  - Depends on: E-02, E-06, E-21, E-22, E-23
  - Expected outcome: `aw find plans 6e93gt` shows it under `executed/`.
  - Execution state: pending

- [ ] E-25 CONFIRM bsl45u REACHED executed
  - Depends on: E-02, E-06, E-21
  - Expected outcome: `aw find plans bsl45u` shows it under `executed/`.
  - Execution state: pending

- [ ] E-26 CONFIRM 8q27jt REACHED executed
  - Depends on: E-02, E-06, E-21
  - Expected outcome: `aw find plans 8q27jt` shows it under `executed/`.
  - Execution state: pending

- [ ] E-27 CONFIRM r81uvz REACHED executed
  - Depends on: E-14, E-02, E-07
  - Expected outcome: `aw find plans r81uvz` shows it under `executed/`.
  - Execution state: pending

- [ ] E-28 CONFIRM dqutt8 REACHED executed
  - Depends on: E-14, E-02, E-07, E-27, E-29, E-30, E-31, E-32
  - Expected outcome: `aw find plans dqutt8` shows it under `executed/`.
  - Execution state: pending

- [ ] E-29 CONFIRM w1cs3p REACHED executed
  - Depends on: E-14, E-02, E-07
  - Expected outcome: `aw find plans w1cs3p` shows it under `executed/`.
  - Execution state: pending

- [ ] E-30 CONFIRM na188y REACHED executed
  - Depends on: E-14, E-02, E-07
  - Expected outcome: `aw find plans na188y` shows it under `executed/`.
  - Execution state: pending

- [ ] E-31 CONFIRM i3b5zu REACHED executed
  - Depends on: E-14, E-02, E-07
  - Expected outcome: `aw find plans i3b5zu` shows it under `executed/`.
  - Execution state: pending

- [ ] E-32 CONFIRM ebrc4t REACHED executed
  - Depends on: E-14, E-02, E-07, E-29, E-30, E-31
  - Expected outcome: `aw find plans ebrc4t` shows it under `executed/`.
  - Execution state: pending

- [ ] E-33 CONFIRM h58z9n REACHED executed
  - Depends on: E-08, E-14, E-02, E-07
  - Expected outcome: `aw find plans h58z9n` shows it under `executed/`.
  - Execution state: pending

- [ ] E-34 CONFIRM y97k46 REACHED executed
  - Depends on: E-08, E-14, E-33, E-02, E-07
  - Expected outcome: `aw find plans y97k46` shows it under `executed/`.
  - Execution state: pending

- [ ] E-35 CONFIRM jd7874 REACHED executed
  - Depends on: E-08, E-14, E-33, E-02, E-07
  - Expected outcome: `aw find plans jd7874` shows it under `executed/`.
  - Execution state: pending

- [ ] E-36 CONFIRM 2zpw22 REACHED executed
  - Depends on: E-08, E-14, E-33, E-02, E-07
  - Expected outcome: `aw find plans 2zpw22` shows it under `executed/`.
  - Execution state: pending

- [ ] E-37 CONFIRM 9rgn2w REACHED executed
  - Depends on: E-14, E-02, E-07
  - Expected outcome: `aw find plans 9rgn2w` shows it under `executed/`.
  - Execution state: pending

- [ ] E-38 CONFIRM x05v02 REACHED executed
  - Depends on: E-49, E-37, E-14, E-02, E-07
  - Expected outcome: `aw find plans x05v02` shows it under `executed/`.
  - Execution state: pending

- [ ] E-39 CONFIRM 7qxey9 REACHED executed
  - Depends on: E-49, E-37, E-14, E-02, E-07
  - Expected outcome: `aw find plans 7qxey9` shows it under `executed/`.
  - Execution state: pending

- [ ] E-40 CONFIRM nbfg7w REACHED executed
  - Depends on: E-49, E-37, E-14, E-02, E-07
  - Expected outcome: `aw find plans nbfg7w` shows it under `executed/`.
  - Execution state: pending

- [ ] E-41 CONFIRM q6epwc REACHED executed
  - Depends on: E-03, E-10, E-04, E-08, E-14, E-09
  - Expected outcome: `aw find plans q6epwc` shows it under `executed/`.
  - Execution state: pending

- [ ] E-42 CONFIRM snin8q REACHED executed
  - Depends on: E-03, E-10, E-04, E-08, E-14, E-41, E-09
  - Expected outcome: `aw find plans snin8q` shows it under `executed/`.
  - Execution state: pending

- [ ] E-43 CONFIRM k6jd6l REACHED executed
  - Depends on: E-03, E-10, E-04, E-08, E-14, E-09
  - Expected outcome: `aw find plans k6jd6l` shows it under `executed/`.
  - Execution state: pending

- [ ] E-44 CONFIRM iog3cw REACHED executed
  - Depends on: E-03, E-10, E-12, E-04, E-14, E-05
  - Expected outcome: `aw find plans iog3cw` shows it under `executed/`.
  - Execution state: pending

- [ ] E-45 CONFIRM e8420v REACHED executed
  - Depends on: E-03, E-10, E-04, E-08, E-14, E-43, E-09
  - Expected outcome: `aw find plans e8420v` shows it under `executed/`.
  - Execution state: pending

- [ ] E-46 CONFIRM 0xsx2n REACHED executed
  - Depends on: E-03, E-10, E-04, E-08, E-14, E-43, E-09
  - Expected outcome: `aw find plans 0xsx2n` shows it under `executed/`.
  - Execution state: pending

- [ ] E-47 CONFIRM w13bkp REACHED executed
  - Depends on: E-03, E-10, E-12, E-04, E-14, E-44, E-05
  - Expected outcome: `aw find plans w13bkp` shows it under `executed/`.
  - Execution state: pending

- [ ] E-48 CONFIRM clors0 REACHED executed
  - Depends on: E-03, E-04, E-08, E-14, E-09, E-07, E-05
  - Expected outcome: `aw find plans clors0` shows it under `executed/`.
  - Execution state: pending

- [ ] E-49 CONFIRM 653ndz REACHED executed
  - Depends on: E-37, E-14, E-02, E-07
  - Expected outcome: `aw find plans 653ndz` shows it under `executed/`.
  - Execution state: pending

- [ ] E-50 CONFIRM 1upea0 REACHED executed
  - Depends on: E-49, E-37, E-14, E-02, E-07
  - Expected outcome: `aw find plans 1upea0` shows it under `executed/`.
  - Execution state: pending

- [ ] E-51 CONFIRM 87rvs2 REACHED executed
  - Depends on: E-03, E-10, E-12, E-04, E-14, E-44, E-05
  - Expected outcome: `aw find plans 87rvs2` shows it under `executed/`.
  - Execution state: pending

- [ ] E-52 CONFIRM rdg0qv REACHED executed
  - Depends on: E-03, E-10, E-12, E-04, E-14, E-44, E-05
  - Expected outcome: `aw find plans rdg0qv` shows it under `executed/`.
  - Execution state: pending

- [ ] E-53 CONFIRM aqc3m6 REACHED executed
  - Depends on: E-03, E-10, E-12, E-04, E-14, E-44, E-05
  - Expected outcome: `aw find plans aqc3m6` shows it under `executed/`.
  - Execution state: pending

- [ ] E-54 CONFIRM zgyna1 REACHED executed
  - Depends on: E-03, E-10, E-12, E-04, E-14, E-44, E-05
  - Expected outcome: `aw find plans zgyna1` shows it under `executed/`.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `7ehv8l` | `20261102-metastore-01-7ehv8l-supersede-spec-2vev8j-and-re-home-backlog-ms06pi-s-release-g.ipd.md` | Supersede spec 2vev8j and re-home backlog ms06pi's release gate to 4sd62s. | none |
| 02 | `tve77h` | `20261102-metastore-02-tve77h-build-the-artifact-meta-core-registry-event-schema-append-ke.ipd.md` | Build the artifact_meta core: registry, event schema, append key, SQLite cache, legacy loader. | none |
| 03 | `1ajqaa` | `20261102-metastore-03-1ajqaa-serve-aw-show-history-aw-show-format-json-and-aw-index-rebui.ipd.md` | Serve aw show --history, aw show --format json and aw index rebuild through artifact_meta. | `executed:tve77h` |
| 04 | `dcerjg` | `20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md` | Build the migration chain and the m0001 dry run with census, renames, citations and round trip. | `executed:tve77h`, `executed:vxevph`, `executed:1vfqdu`, `executed:dky26u`, `executed:ghhzb6`, `executed:hpedmn` |
| 05 | `ya4ee4` | `20261102-metastore-05-ya4ee4-build-the-short-description-journal-and-the-tool-less-saniti.ipd.md` | Build the short-description journal and the tool-less sanitized generation prompt. | `executed:dcerjg`, `executed:odeo9z` |
| 06 | `2xwb9b` | `20261102-metastore-06-2xwb9b-move-the-status-set-setter-engine-onto-artifact-meta.ipd.md` | Move the status_set setter engine onto artifact_meta. | `executed:tve77h`, `executed:7ehv8l` |
| 07 | `xexn45` | `20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md` | Move the remaining metadata writers onto artifact_meta. | `executed:tve77h`, `executed:2xwb9b`, `executed:7yr827`, `executed:g6tw94`, `executed:n5sxxk`, `executed:6e93gt`, `executed:bsl45u`, `executed:8q27jt` |
| 08 | `ffceq0` | `20261102-metastore-08-ffceq0-move-selectors-check-engine-attention-and-ipd-lint-reads-ont.ipd.md` | Move selectors, check_engine, attention and ipd_lint reads onto artifact_meta. | `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45`, `executed:r81uvz`, `executed:dqutt8`, `executed:w1cs3p`, `executed:na188y`, `executed:i3b5zu`, `executed:ebrc4t` |
| 09 | `t4gl15` | `20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md` | Move runner, gate, hook and module reads onto artifact_meta and read_at. | `executed:2zpw22`, `executed:ffceq0`, `executed:g5hpbb`, `executed:h58z9n`, `executed:jd7874`, `executed:tve77h`, `executed:xexn45`, `executed:y97k46` |
| 10 | `59aiyh` | `20261102-metastore-10-59aiyh-move-test-data-to-one-shared-record-builder-over-artifact-me.ipd.md` | Move test data to one shared record builder over artifact_meta. | `executed:1upea0`, `executed:7qxey9`, `executed:9rgn2w`, `executed:g5hpbb`, `executed:nbfg7w`, `executed:tve77h`, `executed:x05v02`, `executed:xexn45`, `executed:653ndz` |
| 11 | `9o83cr` | `20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md` | Delete INDEX and STATUS code and every legacy parser outside artifact_meta. | `executed:0xsx2n`, `executed:1ajqaa`, `executed:clors0`, `executed:59aiyh`, `executed:dcerjg`, `executed:e8420v`, `executed:ffceq0`, `executed:g5hpbb`, `executed:k6jd6l`, `executed:q6epwc`, `executed:snin8q`, `executed:t4gl15` |
| 12 | `90iqr1` | `20261102-metastore-12-90iqr1-rewrite-documents-managed-block-templates-and-quickstarts-fo.ipd.md` | Rewrite documents, managed block, templates and quickstarts for the log format. | `executed:9o83cr` |
| 13 | `cxxmyv` | `20261102-metastore-13-cxxmyv-perform-the-attended-metadata-cutover-commit.ipd.md` | Perform the attended metadata cutover commit. | `executed:1ajqaa`, `executed:87rvs2`, `executed:90iqr1`, `executed:aqc3m6`, `executed:clors0`, `executed:dcerjg`, `executed:g5hpbb`, `executed:iog3cw`, `executed:rdg0qv`, `executed:w13bkp`, `executed:ya4ee4`, `executed:zgyna1` |
| 14 | `g5hpbb` | `20261107-metastore-14-g5hpbb-make-aw-migrate-metadata-migrate-any-repository-from-any-pri.ipd.md` | Make `aw migrate metadata` migrate any repository from any prior format (spec C12, 5.2a, AC-42), and make the phase-A cache read every shape. Runs AFTER 04 and BEFORE 08, 09, 10, 11 and 13, by dependency edge (the number is only the next free Order; added 2026-11-07). | `executed:dcerjg` |
| 15 | `vxevph` | `20261107-metastore-15-vxevph-build-the-migration-chain-metadata-schema-stamp-m0001-prefli.ipd.md` | Build the migration chain, metadata_schema stamp, m0001 preflight, migration journal and sidecar import. | `executed:tve77h` |
| 16 | `1vfqdu` | `20261107-metastore-16-1vfqdu-add-the-aw-migrate-command-group-bare-aw-migrate-and-the-ins.ipd.md` | Add the aw migrate command group, bare aw migrate, and the install pending-migration prompt. | `executed:tve77h`, `executed:vxevph` |
| 17 | `dky26u` | `20261107-metastore-17-dky26u-build-the-m0001-legacy-name-rename-map-and-citation-rewrite.ipd.md` | Build the m0001 legacy-name rename map and citation rewrite. | `executed:tve77h`, `executed:vxevph` |
| 18 | `ghhzb6` | `20261107-metastore-18-ghhzb6-build-the-m0001-log-builder-and-convert-plans-backlog-items.ipd.md` | Build the m0001 log builder and convert plans, backlog items, releases, specs and staged prompts. | `executed:tve77h`, `executed:vxevph`, `executed:dky26u` |
| 19 | `hpedmn` | `20261107-metastore-19-hpedmn-build-the-m0001-review-events-and-convert-research-records-w.ipd.md` | Build the m0001 review events and convert research records, walkthroughs, the roadmap and review files. | `executed:tve77h`, `executed:vxevph`, `executed:dky26u`, `executed:ghhzb6` |
| 20 | `odeo9z` | `20261107-metastore-20-odeo9z-build-the-m0001-description-journal-tool-less-model-call-and.ipd.md` | Build the m0001 description journal, tool-less model call and description validation. | `executed:dcerjg` |
| 21 | `7yr827` | `20261107-metastore-21-7yr827-add-the-phase-b-legacy-writer-and-move-the-runner-writer-hel.ipd.md` | Add the phase-B legacy writer and move the runner writer helpers onto it. | `executed:tve77h`, `executed:2xwb9b` |
| 22 | `g6tw94` | `20261107-metastore-22-g6tw94-move-the-specs-backlog-and-releases-create-note-and-setter-w.ipd.md` | Move the specs, backlog and releases create, note and setter writers onto artifact_meta. | `executed:tve77h`, `executed:2xwb9b`, `executed:7yr827` |
| 23 | `n5sxxk` | `20261107-metastore-23-n5sxxk-move-the-prompts-scaffold-research-adopt-and-set-records-cre.ipd.md` | Move the prompts, scaffold, research, adopt and set_records create, note and setter writers onto artifact_meta. | `executed:tve77h`, `executed:2xwb9b`, `executed:7yr827`, `executed:g6tw94` |
| 24 | `6e93gt` | `20261107-metastore-24-6e93gt-write-short-description-at-creation-and-add-the-aw-describe.ipd.md` | Write short_description at creation and add the aw describe setter. | `executed:tve77h`, `executed:2xwb9b`, `executed:7yr827`, `executed:g6tw94`, `executed:n5sxxk` |
| 25 | `bsl45u` | `20261107-metastore-25-bsl45u-move-the-rename-regroup-and-archive-field-writers-onto-artif.ipd.md` | Move the rename, regroup and archive field writers onto artifact_meta. | `executed:tve77h`, `executed:2xwb9b`, `executed:7yr827` |
| 26 | `8q27jt` | `20261107-metastore-26-8q27jt-move-the-attestation-finalize-scope-and-retirement-writers-o.ipd.md` | Move the attestation, finalize scope and retirement writers onto artifact_meta. | `executed:tve77h`, `executed:2xwb9b`, `executed:7yr827` |
| 27 | `r81uvz` | `20261107-metastore-27-r81uvz-move-selectors-aw-find-aw-ipd-board-and-status-set-reads-ont.ipd.md` | Move selectors, aw find, aw ipd board and status_set reads onto artifact_meta. | `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 28 | `dqutt8` | `20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md` | Move the attention and ipd_lint reads onto artifact_meta. | `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45`, `executed:r81uvz`, `executed:w1cs3p`, `executed:na188y`, `executed:i3b5zu`, `executed:ebrc4t` |
| 29 | `w1cs3p` | `20261107-metastore-29-w1cs3p-move-the-check-engine-identity-set-date-and-from-spec-reader.ipd.md` | Move the check_engine identity, Set, date and From-Spec readers onto artifact_meta. | `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 30 | `na188y` | `20261107-metastore-30-na188y-move-the-check-engine-plan-rule-and-review-readers-onto-arti.ipd.md` | Move the check_engine plan-rule and review readers onto artifact_meta. | `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 31 | `i3b5zu` | `20261107-metastore-31-i3b5zu-move-the-check-engine-release-gate-and-from-backlog-readers.ipd.md` | Move the check_engine release-gate and From-Backlog readers onto artifact_meta. | `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 32 | `ebrc4t` | `20261107-metastore-32-ebrc4t-move-the-check-engine-graduation-and-handoff-readers-onto-ar.ipd.md` | Move the check_engine graduation and handoff readers onto artifact_meta and unify the record skip list. | `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45`, `executed:w1cs3p`, `executed:na188y`, `executed:i3b5zu` |
| 33 | `h58z9n` | `20261107-metastore-33-h58z9n-move-the-check-engine-hook-and-setter-git-content-readers-on.ipd.md` | Move the check_engine, hook and setter git-content readers onto read_at. | `executed:ffceq0`, `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 34 | `y97k46` | `20261107-metastore-34-y97k46-pin-the-runner-reads-and-move-the-runner-selection-and-git-c.ipd.md` | Pin the runner reads and move the runner selection and execution reads onto artifact_meta. | `executed:ffceq0`, `executed:g5hpbb`, `executed:h58z9n`, `executed:tve77h`, `executed:xexn45` |
| 35 | `jd7874` | `20261107-metastore-35-jd7874-move-the-plans-research-and-prompts-module-reads-onto-artifa.ipd.md` | Move the plans, research and prompts module reads onto artifact_meta. | `executed:ffceq0`, `executed:g5hpbb`, `executed:h58z9n`, `executed:tve77h`, `executed:xexn45` |
| 36 | `2zpw22` | `20261107-metastore-36-2zpw22-move-the-review-orchestration-production-check-and-work-modu.ipd.md` | Move the review, orchestration, production-check and work module reads onto artifact_meta. | `executed:ffceq0`, `executed:g5hpbb`, `executed:h58z9n`, `executed:tve77h`, `executed:xexn45` |
| 37 | `9rgn2w` | `20261107-metastore-37-9rgn2w-add-the-shared-test-record-builder-and-convert-the-tracked-r.ipd.md` | Add the shared test record builder and convert the tracked record fixtures. | `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 38 | `x05v02` | `20261107-metastore-38-x05v02-move-backlog-release-gate-check-engine-production-and-setter.ipd.md` | Move backlog, release-gate, check-engine, production and setter test data onto the record builder. | `executed:653ndz`, `executed:9rgn2w`, `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 39 | `7qxey9` | `20261107-metastore-39-7qxey9-move-spec-plan-lifecycle-orchestration-and-runner-test-data.ipd.md` | Move spec, plan, lifecycle, orchestration and runner test data onto the record builder. | `executed:653ndz`, `executed:9rgn2w`, `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 40 | `nbfg7w` | `20261107-metastore-40-nbfg7w-move-runner-family-reader-record-surface-review-and-unmatche.ipd.md` | Move runner-family, reader, record-surface, review and unmatched test data onto the record builder. | `executed:653ndz`, `executed:9rgn2w`, `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 41 | `q6epwc` | `20261108-metastore-41-q6epwc-make-the-typed-aw-index-spellings-aliases-and-stop-index-reg.ipd.md` | Make the typed aw index spellings aliases and stop INDEX regeneration and the stale-index rules. | `executed:1ajqaa`, `executed:59aiyh`, `executed:dcerjg`, `executed:ffceq0`, `executed:g5hpbb`, `executed:t4gl15` |
| 42 | `snin8q` | `20261108-metastore-42-snin8q-delete-the-index-writers-the-status-code-and-the-audit-index.ipd.md` | Delete the INDEX writers, the STATUS code and the audit index cache. | `executed:1ajqaa`, `executed:59aiyh`, `executed:dcerjg`, `executed:ffceq0`, `executed:g5hpbb`, `executed:q6epwc`, `executed:t4gl15` |
| 43 | `k6jd6l` | `20261108-metastore-43-k6jd6l-fold-the-value-writers-into-artifact-meta-delete-the-writer.ipd.md` | Fold the value writers into artifact_meta, delete the writer adapters and record text readers, and move the borrowed grammars. | `executed:1ajqaa`, `executed:59aiyh`, `executed:dcerjg`, `executed:ffceq0`, `executed:g5hpbb`, `executed:t4gl15` |
| 44 | `iog3cw` | `20261108-metastore-44-iog3cw-add-the-format-aware-field-assertion-helper-and-move-the-fir.ipd.md` | Add the format-aware field assertion helper and move the first setter-byte test assertions onto it. | `executed:1ajqaa`, `executed:59aiyh`, `executed:90iqr1`, `executed:dcerjg`, `executed:g5hpbb`, `executed:ya4ee4` |
| 45 | `e8420v` | `20261108-metastore-45-e8420v-delete-the-check-engine-runner-setter-and-release-metadata-p.ipd.md` | Delete the check_engine, runner, setter and release metadata parsers and regular expressions. | `executed:1ajqaa`, `executed:59aiyh`, `executed:dcerjg`, `executed:ffceq0`, `executed:g5hpbb`, `executed:k6jd6l`, `executed:t4gl15` |
| 46 | `0xsx2n` | `20261108-metastore-46-0xsx2n-delete-the-remaining-plans-family-ipd-family-and-module-meta.ipd.md` | Delete the remaining plans-family, ipd-family and module metadata regular expressions. | `executed:1ajqaa`, `executed:59aiyh`, `executed:dcerjg`, `executed:ffceq0`, `executed:g5hpbb`, `executed:k6jd6l`, `executed:t4gl15` |
| 47 | `w13bkp` | `20261108-metastore-47-w13bkp-move-the-remaining-setter-byte-test-assertions-onto-the-form.ipd.md` | Move the remaining setter-byte test assertions onto the format-aware field assertion helper. | `executed:1ajqaa`, `executed:59aiyh`, `executed:90iqr1`, `executed:dcerjg`, `executed:g5hpbb`, `executed:iog3cw`, `executed:ya4ee4` |
| 48 | `clors0` | `20261108-metastore-48-clors0-build-the-dormant-log-format-gates-readers-event-overrides-c.ipd.md` | Build the dormant log-format gates, readers, event overrides, commands and option aliases for the cutover. | `executed:1ajqaa`, `executed:dcerjg`, `executed:ffceq0`, `executed:g5hpbb`, `executed:t4gl15`, `executed:xexn45`, `executed:ya4ee4` |
| 49 | `653ndz` | `20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md` | Build and prove the test-fixture codemod. | `executed:9rgn2w`, `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 50 | `1upea0` | `20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md` | Move setter, runner-lane and first-half unmatched test data onto the record builder with the fixture codemod. | `executed:653ndz`, `executed:9rgn2w`, `executed:g5hpbb`, `executed:tve77h`, `executed:xexn45` |
| 59 | `87rvs2` | `20261108-metastore-59-87rvs2-move-setter-byte-assertions-of-batches-s05-to-s07-onto-the-f.ipd.md` | Move setter-byte assertions of batches S05 to S07 onto the format-aware field helper. | `executed:1ajqaa`, `executed:59aiyh`, `executed:90iqr1`, `executed:dcerjg`, `executed:g5hpbb`, `executed:iog3cw`, `executed:ya4ee4` |
| 60 | `rdg0qv` | `20261108-metastore-60-rdg0qv-move-setter-byte-assertions-of-batches-s08-to-s10-onto-the-f.ipd.md` | Move setter-byte assertions of batches S08 to S10 onto the format-aware field helper. | `executed:1ajqaa`, `executed:59aiyh`, `executed:90iqr1`, `executed:dcerjg`, `executed:g5hpbb`, `executed:iog3cw`, `executed:ya4ee4` |
| 61 | `aqc3m6` | `20261108-metastore-61-aqc3m6-move-setter-byte-assertions-of-batches-s15-to-s17-onto-the-f.ipd.md` | Move setter-byte assertions of batches S15 to S17 onto the format-aware field helper. | `executed:1ajqaa`, `executed:59aiyh`, `executed:90iqr1`, `executed:dcerjg`, `executed:g5hpbb`, `executed:iog3cw`, `executed:ya4ee4` |
| 62 | `zgyna1` | `20261108-metastore-62-zgyna1-move-the-test-status-set-setter-byte-assertions-of-batches-s.ipd.md` | Move the test_status_set setter-byte assertions of batches S18 to S20 onto the format-aware field helper. | `executed:1ajqaa`, `executed:59aiyh`, `executed:90iqr1`, `executed:dcerjg`, `executed:g5hpbb`, `executed:iog3cw`, `executed:ya4ee4` |

SPLIT 2026-11-07 (maintainer step-complexity rule: no single E/V item may hide hundreds of steps). Orders 15 to 62 are parts split out of Orders 04, 05, 07, 08, 09, 10, 11 and 13; each original keeps its id6 as its family's LAST part and depends on every part, so an `executed:<original>` edge still means the whole family is done. Order numbers past 14 are only the next free numbers: the runner orders by the dependency edges in this table (dependency depth first), not by Order.

Phase A (Orders 01 to 05, plus Order 14 added 2026-11-07 for spec C12, and their split parts) adds code on today's format and moves no caller; Order 01 is records only. Phase B (Orders 06 to 11) moves every writer and reader onto `artifact_meta` while the on-disk format stays the legacy bullet block, so `main` has one format at every merge (spec C10a). Order 12 prepares the post-cutover documentation as a patch file that never reaches the live documents before the cutover. Order 13 is `Attended: required`: it runs in the maintainer's main checkout, which holds the history sidecar, so an `--unattended` run holds it `not-run` and this orchestrator cannot retire until Order 13 has been run attended.

## Completion criteria (the whole Set is done only when)

- Spec `2vev8j` is superseded and backlog `ms06pi`'s release gate is carried by `4sd62s`. Owner: `7ehv8l`.
- `artifact_meta` provides the registry, event schema, `append` key, path rule, cache and legacy loader (AC-4, AC-5, AC-8, AC-17, AC-18, AC-23, AC-24, AC-26, AC-33, AC-39). Owner: `tve77h`.
- `aw show --history`, `aw show --format json` and `aw index rebuild` exist (AC-2 on a fixture). Owner: `1ajqaa`.
- Migration `m0001` is built and proven on a copy (AC-10, AC-11, AC-14, AC-14a(5), AC-19, AC-20, AC-22(1), AC-27, AC-28, AC-29, AC-30, AC-32, AC-40, AC-41). Owner: `dcerjg`.
- Short descriptions are generated tool-less and sanitized through the journal (AC-36 cases 3, 4, 5, 7). Owner: `ya4ee4`.
- Every writer goes through `artifact_meta` (AC-15, AC-14a(1-4), AC-21, and the phase-B forms of AC-3, AC-6 and AC-31). Owners: `2xwb9b`, `xexn45`.
- Every reader goes through `artifact_meta` or `read_at` (AC-1a, AC-7, AC-9 reader part, AC-12). Owners: `ffceq0`, `t4gl15`.
- Test data uses one shared record builder. Owner: `59aiyh`.
- No legacy parser or INDEX/STATUS code remains outside `artifact_meta` (AC-1, AC-9). Owner: `9o83cr`.
- The post-cutover documentation is ready as an applicable patch. Owner: `90iqr1`.
- The cutover commit has landed and the real-repository criteria are demonstrated (AC-1b, AC-13, AC-16, and the real forms of AC-1, AC-2, AC-3, AC-6, AC-7, AC-9, AC-10, AC-11, AC-22(2), AC-30(2), AC-30(3), AC-31, AC-34, AC-36(6), AC-41). Owner: `cxxmyv`.

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
- Owner: plan author
- Resolution or deferral rationale: Not now. Both are within the size limits (18 and 16 E-items, 5 task groups), and each records a concrete split point; `/plan-review` of each child decides. A split adds rows to this table before approval, so it cannot leave an unauthored row. Recommendation strength: medium. Confirmed 2026-11-06: the `/plan-review` of `tve77h` (decision D-1) and of `dcerjg` (decision D-2) each declined the split.

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

- [ ] V-14 validates E-14
  - Required evidence: paste `aw find plans g5hpbb` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: paste `aw find plans vxevph` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-16 validates E-16
  - Required evidence: paste `aw find plans 1vfqdu` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: paste `aw find plans dky26u` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-18 validates E-18
  - Required evidence: paste `aw find plans ghhzb6` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-19 validates E-19
  - Required evidence: paste `aw find plans hpedmn` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-20 validates E-20
  - Required evidence: paste `aw find plans odeo9z` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-21 validates E-21
  - Required evidence: paste `aw find plans 7yr827` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-22 validates E-22
  - Required evidence: paste `aw find plans g6tw94` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-23 validates E-23
  - Required evidence: paste `aw find plans n5sxxk` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-24 validates E-24
  - Required evidence: paste `aw find plans 6e93gt` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-25 validates E-25
  - Required evidence: paste `aw find plans bsl45u` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-26 validates E-26
  - Required evidence: paste `aw find plans 8q27jt` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-27 validates E-27
  - Required evidence: paste `aw find plans r81uvz` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-28 validates E-28
  - Required evidence: paste `aw find plans dqutt8` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-29 validates E-29
  - Required evidence: paste `aw find plans w1cs3p` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-30 validates E-30
  - Required evidence: paste `aw find plans na188y` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-31 validates E-31
  - Required evidence: paste `aw find plans i3b5zu` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-32 validates E-32
  - Required evidence: paste `aw find plans ebrc4t` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-33 validates E-33
  - Required evidence: paste `aw find plans h58z9n` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-34 validates E-34
  - Required evidence: paste `aw find plans y97k46` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-35 validates E-35
  - Required evidence: paste `aw find plans jd7874` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-36 validates E-36
  - Required evidence: paste `aw find plans 2zpw22` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-37 validates E-37
  - Required evidence: paste `aw find plans 9rgn2w` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-38 validates E-38
  - Required evidence: paste `aw find plans x05v02` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-39 validates E-39
  - Required evidence: paste `aw find plans 7qxey9` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-40 validates E-40
  - Required evidence: paste `aw find plans nbfg7w` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-41 validates E-41
  - Required evidence: paste `aw find plans q6epwc` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-42 validates E-42
  - Required evidence: paste `aw find plans snin8q` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-43 validates E-43
  - Required evidence: paste `aw find plans k6jd6l` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-44 validates E-44
  - Required evidence: paste `aw find plans iog3cw` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-45 validates E-45
  - Required evidence: paste `aw find plans e8420v` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-46 validates E-46
  - Required evidence: paste `aw find plans 0xsx2n` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-47 validates E-47
  - Required evidence: paste `aw find plans w13bkp` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-48 validates E-48
  - Required evidence: paste `aw find plans clors0` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-49 validates E-49
  - Required evidence: paste `aw find plans 653ndz` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-50 validates E-50
  - Required evidence: paste `aw find plans 1upea0` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-51 validates E-51
  - Required evidence: paste `aw find plans 87rvs2` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-52 validates E-52
  - Required evidence: paste `aw find plans rdg0qv` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-53 validates E-53
  - Required evidence: paste `aw find plans aqc3m6` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-54 validates E-54
  - Required evidence: paste `aw find plans zgyna1` output showing the plan under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: An orchestrator's items are one CONFIRM-executed check per child and carry no work of their own; the item count equals the child count (54 after the 2026-11-07 step-complexity split). Splitting the orchestrator would not shrink any unit of work, only scatter the Set's completion checklist.

Execute only after explicit human approval (`Status: approved`) of this plan and of each child. This plan performs no work of its own; each child carries its own scope fence, test evidence and path-scoped `aw commit`. Each `V-*` item MUST paste the actual `aw find plans <id6>` output. Under `aw oc run` / `aw agy run` the runner retires this plan once every child is `executed` on disk. When executing by hand, run the children in table order (Order 13 attended), then confirm each, run `aw ipd lint --phase pre-transition` and `aw ipd finalize` on this plan. Commit only through `aw commit 63ib9r -- <paths>`; never push.
