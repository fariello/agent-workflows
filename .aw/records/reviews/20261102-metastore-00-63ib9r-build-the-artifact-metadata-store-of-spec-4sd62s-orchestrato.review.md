# Review findings: plan 63ib9r

- Subject-Id: 63ib9r
- Subject-Type: ipd
- Reviewed-At: 2026-11-13
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `949d698c3` in a non-interactive runner review-sweep lane worktree. The lane-input copy (revision 3) was byte-identical to the tracked plan, which was committed and unmodified, so no pre-review snapshot was needed. `aw ipd lint --phase author` and `aw ipd coverage 63ib9r` were clean before the edits. After the edits, `--phase review-finalize` reported `IPD-S408`, because the text had changed and the coverage fingerprint was stale. Coverage repair attempt 1 re-ran `aw ipd coverage 63ib9r`, which reported "ready for review" and recorded the new fingerprint `96fe24cd857b`; lint was then clean. Rows: 13 -> 13, so no row was deleted.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Child table rows 10 and 11; E-10, E-11 | Dependencies missing `xexn45` (row 10) and `1ajqaa`, `dcerjg` (row 11) | Match each child's `- Item-Dependencies:` | PR-001. |
| Completion criteria, writers and cutover lines | Omitted the phase-B AC-3 and AC-6, and the real AC-1 and AC-30(2) | Added, matching `xexn45` and `cxxmyv` | PR-002. |
| OQ-01 | `Owner: none`; split decision pending child reviews | `Owner: plan author`; both child reviews declined the split | PR-003. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step R1

- Checked: every child file name in the table exists under `pending/`; each child's `- Item-Dependencies:` value; the AC ownership sections of `xexn45`, `1ajqaa`, `59aiyh` and `cxxmyv`; the review records of `tve77h` and `dcerjg` for the split decision; spec `4sd62s` section 7 steps 1 to 9 against the Scope check; `runner_shared` `_freeze_attended_hold` for the `not-run` claim about Order 13 under an unattended run.
- Rows 10 and 11 disagreed with the children (PR-001). `59aiyh` declares `executed:tve77h, executed:xexn45`. `9o83cr` declares `executed:ffceq0, executed:t4gl15, executed:59aiyh, executed:1ajqaa, executed:dcerjg`.
- The paragraph under the table says an unattended run holds Order 13 `not-run`. `runner_shared._freeze_attended_hold` sets `q_entry["status"] = "not-run"`, which matches.

### Step R2

- Checked: the E/V bijection is 13/13; each `V-*` demands pasted `aw find plans <id6>` output, which is reachable by construction.
- E-items now mirror the corrected child dependencies.
- The checklist is orchestration only. It holds no work that a child does not cover, and `aw ipd coverage` agrees.
- Gate: it includes the human-approval rule, the pasted-output rule, conditional finalize ownership (the runner retires the plan, or a hand run uses `aw ipd finalize`), a path-scoped `aw commit` and no push. It has no hand `git mv`.
- `IPD-S407`: none reported. `IPD-S408`: repaired in attempt 1 (see the round preamble).

### Step R7

- Checked the whole Set. Every step of spec section 7 has exactly one owner. The `Carrier:` rows across the children close on a sibling or on `nq1src`/`f4p4vn`. `cxxmyv`'s reviewed scope matches its row 13.
- The phase-B AC-3 and AC-6 forms belong to `xexn45` (its AC table: "`cxxmyv` re-demonstrates on logs"), and the completion criteria omitted them (PR-002).
- `cxxmyv`'s review (round 1) added AC-1 and AC-30(2) to its real-repository list, so the cutover criterion is updated to match.

### Step S5

- Checked: OQ-01 is a reviewer-and-author decision, not the maintainer's. Both child reviews have since declined the split (`tve77h` D-1, `dcerjg` D-2), so the resolution stands. No question needs the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | R7 / child table | `59aiyh` "- Item-Dependencies: executed:tve77h, executed:xexn45"; `9o83cr` "- Item-Dependencies: executed:ffceq0, executed:t4gl15, executed:59aiyh, executed:1ajqaa, executed:dcerjg" | Rows 10 and 11 and E-10/E-11 understated the children's dependencies, so a hand executor following table order could run `59aiyh` before `xexn45`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rows and E-item `Depends on` now match the children. |
| PR-002 | LOW | IN-SCOPE | R7 / completion criteria | `xexn45` AC table rows AC-3 and AC-6; `cxxmyv` "Owns, finally on the real repository ... AC-1 ... AC-30 cases 2 and 3" | The criteria omitted ACs the children own. | Overall:Low | FIXED | Added. |
| PR-003 | LOW | IN-SCOPE | S5 owner rule | OQ-01 "- Owner: none"; `tve77h` review D-1; `dcerjg` review D-2 | The owner field did not name who decided, and the deferred check is now complete. | Overall:Low | FIXED | `Owner: plan author`; resolution cites both review decisions. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which source is authoritative for a child's dependencies, the table or the child? | The child's `- Item-Dependencies:` (what the runner reads) | Edit the children to match the table | `runner_shared` dependency checks read the child's field | yes |

## Round 2

This re-review ran at HEAD `fb593df2d` in the non-interactive runner review-sweep lane (`run-20261112T223412Z-2790820`, item `03-63ib9r`, `attempt-1`) following the 2026-11-07 spec `4sd62s` C12 amendment and the 2026-11-07/2026-11-09 Set splits (`212` children). The tracked plan was clean at preflight, so the pre-review snapshot was skipped unchanged. Preflight `aw ipd lint --phase author` passed (`0` errors, `0` warnings, `2` `IPD-C802` advisories) and `aw ipd coverage 63ib9r` reported ready for review. After applying the Round 2 prose revisions, `--phase review-finalize` reported only `IPD-S408` (stale coverage fingerprint). Coverage repair attempt 1 (`aw ipd coverage --no-commit 63ib9r`) reported ready for review and recorded fingerprint `702f3b688c5b`. Rows: `212 -> 212`, so zero checklist or child-table rows were deleted.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter (`- Concern:`, `- Scope:`, `- Readiness:`), writing-standard pointer, `## Workflow history`, and `## Goal` | Claimed "None of it exists yet" and "thirteen children"; lacked `- Readiness:` and the writing-standard reference note; contained a blank line inside `## Workflow history` | States `4` executed and `208` pending children across `212` children (`14` top-level families), sets `- Readiness: go-pending-approval`, adds the writing-standard note, removes the stray blank line, and cites `g5hpbb`, `tub3ir`, `5qyba0`, and `cxxmyv` in `## Goal` | PR-006, PR-007. |
| `## Child IPDs, sequence, and dependencies` post-table prose and diagram | Omitted Orders `12` and `14` from split families; named only Order `13` as `Attended: required`; had no Requirement 12(b) diagram | Includes Orders `12` and `14`, names all three `Attended: required` plans (`tub3ir`, `5qyba0`, `cxxmyv`), and adds a `mermaid` `flowchart TD` of the 14-family Phase A / Phase B / Phase C dependency DAG | PR-005, PR-006, PR-007. |
| `## Completion criteria`, `## Cross-IPD validation`, `## Deferred / out of scope`, `## Scope check`, `## Required tests / validation`, and `OQ-01` | Omitted C12 / 5.2a / `AC-42` / step 3a (`g5hpbb`, `9vf2iv`, `6oi2nu`, `3g20ms`, `bv4kkj`) and split cutover seams (`clors0`, `2k5t16`..`0zylig`, `tub3ir`, `33vxoi`, `5qyba0`); duplicated "the run index" in `Deferred` | Adds the `g5hpbb` family `AC-42` completion criterion and section 7 step 3a scope mapping, traces split pre-cutover seams into `cxxmyv`, deduplicates `Deferred` (`37am1y`/`nq1src` vs `bfuzs6`/`f4p4vn`), and notes `dcerjg`'s later Set-wide split in `OQ-01` | PR-004, PR-006. |
| `## Validation and cross-check` rule line and `## Approval and execution gate` | Used two em dashes (`IPD-C802`); instructed hand execution in "table order (Order 13 attended)" | Replaces em dashes with parentheses and directs hand execution to follow `- Item-Dependencies:` topological order with `tub3ir`, `5qyba0`, and `cxxmyv` run attended in the main checkout | PR-005, PR-007. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step R1

- Checked: `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md` (all `2,451` original lines), `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (including the 2026-11-07 C12, section 5.2a, `AC-42`, and section 7 step 3a amendments and the 2026-11-01 `37am1y`/`bfuzs6` split), all `212` `Set: metastore` child IPDs on disk (`4` under `executed/`, `208` under `pending/`), referenced artifacts `2vev8j` (`superseded`), `ms06pi` (`graduated`), `nj8zdp` (`active`), `37am1y` (`to-review`), `bfuzs6` (`to-review`), `nq1src` (`open`), and `f4p4vn` (`open`), and `agent_workflows/orchestrator_readiness.py` and `agent_workflows/runner_shared.py`.
- Every one of the `212` rows in `## Child IPDs` resolves to an existing `Set: metastore` child plan with exact filename, `Order`, `- From-Spec: 4sd62s`, `- Blocks-Release: next`, and `- Item-Dependencies:` parity.
- Three children carry `- Attended: required` on disk (`tub3ir` Order 254, `5qyba0` Order 260, and `cxxmyv` Order 13), whereas the orchestrator prose named only Order 13 (`PR-005`).

### Step R2

- Checked: `E-01..E-212` <-> `V-01..V-212` bijection (`212/212`), `Depends on:` parity with every child's `- Item-Dependencies:` (`0` mismatches), cycle-freeness of the 212-node DAG (`0` cycles; all `211` other children are transitive prerequisites of `cxxmyv`), `CONFIRM <id6> REACHED executed` row conformance, `## Approval and execution gate` rules, `IPD-S407`, and `IPD-S408`.
- Fixed the broken hand-execution instruction in `## Approval and execution gate` ("table order") so hand execution follows `- Item-Dependencies:` topological order (`PR-005`).
- `IPD-S407`: none reported. `IPD-S408`: repaired in attempt 1 via `aw ipd coverage --no-commit 63ib9r` (fingerprint `702f3b688c5b`).

### Step R7

- Checked: full Set rollup across all `212` children against spec `4sd62s` acceptance criteria (`AC-1` through `AC-42`) and section 7 steps `1`, `2`, `3`, `3a`, `4`, `5`, `6`, `7`, `8`, `9`, and OQ-4; `Carrier:` closure across all `212` children (every deferred item resolves inside `Set: metastore` or to `nq1src`/`f4p4vn`); and open-question status across all `212` children (`0` `Status: open` questions).
- Spec `4sd62s` has `45` AC identifiers: `4` (`AC-25`, `AC-35`, `AC-37`, `AC-38`) were split on 2026-11-01 to specs `37am1y` (`nq1src`) and `bfuzs6` (`f4p4vn`), `40` were already mapped in `63ib9r`, and `AC-42` (added 2026-11-07 with C12, section 5.2a, and step 3a, owned by `g5hpbb` and parts `9vf2iv`, `6oi2nu`, `3g20ms`, `bv4kkj`) was missing from `## Completion criteria`, `## Cross-IPD validation`, and `## Scope check` (`PR-004`). Added all missing C12/step-3a and split-cutover references by child `id6`.

### Step S5

- Checked: `OQ-01` remains resolved (`Blocking: no`, `Owner: plan author`), updated only to note `dcerjg`'s subsequent Set-wide split. All Round 2 findings (`PR-004`..`PR-007`) are concrete alignment fixes against approved spec `4sd62s` and the `212` children on disk with `Low` remediation risk. Zero questions require human decision (`questions: []`).

### Pass 2

- Re-read `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md` across all modified sections and verified `E-01..E-212` and `V-01..V-212` remain intact with `Execution state: pending` and `Result: pending`.
- Verified `aw ipd coverage --no-commit 63ib9r` (`ready for review`, fingerprint `702f3b688c5b`), `aw ipd lint --phase review-finalize --agent` (`clean`, `0` errors, `0` warnings, `0` advisories), zero em/en dashes, zero absolute paths, zero file-scheme URIs, and complete compliance with `.aw/system/workflows/technical-writing/technical-writing.md` Requirements 1-12.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-004 | HIGH | UNDER-SCOPE | R7 / spec 4sd62s C12, 5.2a, AC-42, step 3a | `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md:34,1338-1367`; `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md:215-225,301,2097-2101` | After the 2026-11-07 spec `4sd62s` C12 amendment and child-table regeneration adding `g5hpbb` (`9vf2iv`, `6oi2nu`, `3g20ms`, `bv4kkj`), `Completion criteria`, `Cross-IPD validation`, and `Scope check` still omitted `AC-42`, section 7 step 3a, and the split pre-cutover seams (`clors0`, `2k5t16`..`0zylig`, `tub3ir`, `33vxoi`, `5qyba0`) consumed by `cxxmyv`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the `g5hpbb` family `AC-42` criterion, added section 7 step 3a to `Scope check`, and traced C12 and split pre-cutover seams into `cxxmyv` in `Cross-IPD validation`. |
| PR-005 | HIGH | IN-SCOPE | R2 / R7 hand-execution order and attended gating | `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md:1334,2451`; `tub3ir` line 22; `5qyba0` line 22 | `Approval and execution gate` instructed hand executors to run children in table row order (invalid because rows 04-13 depend on split parts at Orders 14-299), and both prose sections claimed only Order 13 (`cxxmyv`) is `Attended: required`, omitting `tub3ir` (Order 254) and `5qyba0` (Order 260). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Directed hand execution to follow `- Item-Dependencies:` topological order and named all three `Attended: required` children (`tub3ir`, `5qyba0`, `cxxmyv`). |
| PR-006 | MEDIUM | IN-SCOPE | R1 / R7 stale counts, Phase-A state, and split families | `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md:5-6,43,1332,1359-1362,1380` | `- Concern:`, `- Scope:`, and `Goal` still said "None of it exists yet" and "thirteen children" (`4` children are `executed` and the Set has `212` children across `14` families); line 1332 omitted Orders `12` and `14` from split families; `Deferred` duplicated "the run index"; and `OQ-01` omitted `dcerjg`'s later Set-wide split. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated front-matter summary, `Goal`, split-family list, `Deferred` (`37am1y`/`nq1src` and `bfuzs6`/`f4p4vn`), and `OQ-01` to match the 212-child Set on disk. |
| PR-007 | LOW | IN-SCOPE | Proofreading / writing standard req 12(b) and IPD-C802 | `.aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md:23,1332-1335,1384`; `.aw/system/workflows/technical-writing/technical-writing.md:223-244` | The orchestrator described a 3-phase branching dependency DAG across 14 families and an attended cutover chain without a Requirement 12(b) diagram, lacked the writing-standard reference note, and had two `IPD-C802` em dashes on line 1384. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the writing-standard note, added a `mermaid` `flowchart TD` of the 14-family DAG matching `Child IPDs`, and replaced both em dashes with parentheses (`0` advisories). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-2 | At what granularity should the Requirement 12(b) Mermaid diagram depict the 212-child `metastore` DAG? | Depict the 14 top-level family capstones plus cross-family seam `clors0` and the attended cutover chain (`tub3ir`, `2k5t16`..`0zylig` + `33vxoi`, `5qyba0`, `cxxmyv`) across Phases A, B, and C | Render all 212 nodes in one Mermaid block or omit the diagram | Each capstone depends on every split part in its family, so family-level edges plus `clors0` and the attended cutover chain capture the exact cross-family execution order legibly while the 212-row `Child IPDs` table remains normative | yes |
| D-3 | Should `E-01`, `E-02`, `E-03`, and `E-06` be marked `performed` during review because `7ehv8l`, `tve77h`, `1ajqaa`, and `2xwb9b` are already `executed` on disk? | Leave all `E-01..E-212` `Execution state: pending` and `V-01..V-212` `Result: pending`, while noting the four executed children in `- Concern:` | Mark `E-01`, `E-02`, `E-03`, and `E-06` `performed` during `/plan-review` | `steps/s7-finalize.md` forbids claiming execution during review, and `runner_shared` retires an orchestrator automatically once all 212 children are `executed` on disk | yes |
