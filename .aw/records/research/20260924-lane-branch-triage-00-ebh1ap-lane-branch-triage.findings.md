---
id: ebh1ap
created: 20260924
set: lane-branch-triage
order: 00
topic: [lanes, git, triage, laneorph]
model:
kind: findings
status: reference
outcome: adopted
summary: Triage and disposition record for lane branches holding unmerged commits
consumed-by: [qliia1, ut0vzr]
---

# Research: Triage and Disposition Record for Lane Branches Holding Unmerged Commits

- Set: `lane-branch-triage` (Order 00, id `ebh1ap`)
- Implementing Plan: `ut0vzr` (Set `laneorph`, Order 02)
- Target Backlog Item: `qliia1`
- Date: 2026-09-24
- Status: done
- Outcome: resolved

## 1. Executive Summary

This research record establishes the authoritative inventory, disposition rules, and cited evidentiary resolutions for the lane branches holding unmerged commits tracked under backlog item `qliia1` and plan `ut0vzr`.

At initial filing (2026-09-17), 14 lane branches were identified as holding commits not reachable from `main`. During plan review round 2, `upgtest` was confirmed recovered and merged to `main` (`9476b48b`), reducing the active triage target to 12 branches holding 40 distinct commits (91 summed per-branch ahead counts).

At execution HEAD (`def803533f2495dd6c305e1bba5b76e7f9eab245`), an exhaustive sweep of all `refs/heads/aw/lane/*` and git object stores was conducted. Every one of the target 14 branches has been fully accounted for with cited evidence:
- **5 superseded-plan branches** (`2c122z`, `58ha43`, `7p9n2v`, `rchpms`, `qcqhj7`) along with unbranched `6knsrx` correspond to the retired `wtiso` set. Their retirement was explicitly decided and documented in `.aw/records/plans/superseded/` under verbatim `RETIRED 2026-09-02:` headers. Disposition: **DELETE** (refs already removed).
- **7 executed-plan branches** (`nna8yz`, `fn2l1u`, `r2i1b1`, `03ie04`, `ybkmzp`, `mm5p3v`, `d7qoxv`) had their work/substance landed in `main` via alternative integration commits or subsequent attempts. All landing sites and symbols are verified present in `main`. Disposition: **DELETE** (refs already removed).
- **1 orphan branch** (`upgtest`) had its 8 artifacts and rehearsal harness recovered and merged in `9476b48b` (2026-09-17). Disposition: **RECOVERED & MERGED** (ref removed).
- **1 already-integrated branch** (`tx6q0h`) held 0 unmerged commits. Disposition: **LANDED** (ref removed).
- **ESCALATE list**: **EMPTY** (0 branches requiring maintainer escalation).

---

## 2. Authoritative Disposition Rule

To ensure reproducible and sound decisions, the following rules govern lane branch triage:

### 2.1 Disposition Categories
1. **DELETE**:
   - The owning plan is marked `superseded` in `main` with an explicit retirement rationale recorded in the plan file.
   - OR the owning plan is marked `executed` in `main` and the branch's substantive implementation, features, and fixes have demonstrably landed in `main` (via a subsequent attempt, merge commit, or refactored module).
2. **RECOVER**:
   - The branch contains valid, tested, unlanded work that is not superseded and is absent from `main`. Recovery must integrate the work into `main` (or author a successor plan if direct merge is infeasible due to divergence).
3. **ESCALATE**:
   - The repository evidence is ambiguous, contradictory, or lacks an owning plan/record to determine whether the work is superseded, landed, or still wanted. A specific question must be authored for the maintainer.

### 2.2 Evidentiary Standards and Predicates
- **Single Authoritative Merged-ness Predicate**:
  The triage relies on `runner_shared.lane_work_has_landed` (and underlying `git merge-base --is-ancestor`) as the canonical definition of whether work is reachable from `main`. Hand-rolled definitions of mergedness are forbidden to prevent drift.
- **Prohibition of Commit-Subject Matching**:
  Matching commit subjects via `git log --grep` is explicitly **FORBIDDEN** as proof of landing. Commit subjects can match between abandoned lanes or re-authored attempts without the underlying commits being reachable. Evidence must consist of:
  1. Git commit ancestry (`git merge-base --is-ancestor <sha> main`), OR
  2. Concrete content/symbol verification at specific line numbers in source files on `main`.
- **Insufficiency of Branch Size and Set Membership**:
  - Neither commit count nor Set membership alone determines disposition.
  - *Proof by counter-example (`nna8yz`)*: A large branch (753 insertions) with an executed plan appeared to hold unmerged work, but its substance had landed in `main` via `lane_containment.py`. Treating size as a reason to force-merge would re-land stale duplicate code.
  - *Proof by counter-example (`wtiso` set)*: The largest branches (26 distinct commits, 74 summed across 5 branches) all belonged to plans that were deliberately retired with documented rationale. Treating size as risk would block valid cleanup.

---

## 3. Inventory and Measurement at Execution HEAD

### 3.1 Measurement Environment
- **Measuring Worktree**: `.aw/worktrees/ut0vzr` (lane worktree for IPD `ut0vzr`)
- **Execution HEAD**: `def803533f2495dd6c305e1bba5b76e7f9eab245`
- **Main Checkout**: `.` (top-level repository checkout)

### 3.2 Inventory of Historical Target Branches (from `qliia1` and Plan `ut0vzr`)

| Plan / Branch | Owning Plan Status | Plan Directory in `main` | Ref Exists in `refs/heads/` | Disposition | Primary Evidence & Landing Site |
|---|---|---|---|---|---|
| `aw/lane/2c122z` | `superseded` | `superseded/` | No | **DELETE** | Quoted header: `RETIRED 2026-09-02: retiring UNLANDED...` |
| `aw/lane/58ha43` | `superseded` | `superseded/` | No | **DELETE** | Quoted header: `RETIRED 2026-09-02: retiring UNLANDED, with no successor for its main deliverable...` |
| `aw/lane/7p9n2v` | `superseded` | `superseded/` | No | **DELETE** | Quoted header: `RETIRED 2026-09-02: superseded by plan eulhzt...` |
| `aw/lane/rchpms` | `superseded` | `superseded/` | No | **DELETE** | Quoted header: `RETIRED 2026-09-02: PARTLY LANDED, and the part that mattered most is already on main...` |
| `aw/lane/qcqhj7` | `superseded` | `superseded/` | No | **DELETE** | Quoted header: `RETIRED 2026-09-02: superseded by the lanectn Set...` |
| `aw/lane/6knsrx` | `superseded` | `superseded/` | No (never created) | **NO REF** | Quoted header: `RETIRED 2026-09-02: this plan's entire premise is gone...` |
| `aw/lane/nna8yz` | `executed` | `executed/` | No | **DELETE** | Landed via `lane_containment.py:2497` (`materialize_lane_inputs`); merge reflog `f7124702` |
| `aw/lane/fn2l1u` | `executed` | `executed/` | No | **DELETE** | Landed via `858c7cf6` (`fn2l1u_attempt2`), cited in `9476b48b`; symbols `Refusal` (`render_stream.py:2207`), `refusal_of_item` (`render_stream.py:2303`), `actor_refusal` (`attention_contract.py:704`) |
| `aw/lane/r2i1b1` | `executed` | `executed/` | No | **DELETE** | Landed via `3e233fad`, cited in `9476b48b`; verified symbols in `render_stream.py` and `attention_contract.py` |
| `aw/lane/03ie04` | `executed` | `executed/` | No | **DELETE** | Landed via `bf57a569` (`03ie04_attempt2`) / `bc9b3f43` / `db7bee80`; verified in `runner_shared.py:10698` (`selectors.read_front_matter_status`) |
| `aw/lane/ybkmzp` | `executed` | `executed/` | No | **DELETE** | Landed via `4234153f` (`ybkmzp_attempt2`); verified in `runner_shared.py:13379` (`resolve_verification_decision`) |
| `aw/lane/mm5p3v` | `executed` | `executed/` | No | **DELETE** | Landed via `8243aff5` (`mm5p3v_attempt2`); verified in `cli.py:2297` (`aw runs analyze`) |
| `aw/lane/d7qoxv` | `executed` | `executed/` | No | **DELETE** | Landed via `dc88a99a` (`d7qoxv_attempt2`); verified in `lane_containment.py:70` |
| `aw/lane/upgtest` | None | None | No | **RECOVERED** | Recovered and merged to `main` in `9476b48b` (2026-09-17) |
| `aw/lane/tx6q0h` | `executed` | `executed/` | No | **LANDED** | 0 commits ahead; merged to `main` |

---

### 3.3 Active Branch Sweep at Execution HEAD

At HEAD `def80353`, `git for-each-ref refs/heads/aw/lane/*` reports 18 branches (none of which belong to the historical 14 branches):

| Branch | SHA | Ahead | Behind | Worktree | Plan ID | Plan Status | Plan Directory | Last Commit Date | Last Commit Subject |
|---|---|---|---|---|---|---|---|---|---|
| `aw/lane/13xo5k` | `932be735` | 1 | 132 | `none` | `13xo5k` | `approved` | `pending` | 2026-09-23 | WIP INTERRUPTED SNAPSHOT (not finished work): lane 13xo5k |
| `aw/lane/7p3tt8` | `ac063e2a` | 1 | 11 | `7p3tt8` | `7p3tt8` | `approved` | `pending` | 2026-09-24 | lifeglyph-08 (7p3tt8): amend 25kzda section 5.6, place canonical legend in help and docs, and add drift guard |
| `aw/lane/92u0v9` | `97255449` | 0 | 343 | `none` | `92u0v9` | `executed` | `executed` | 2026-09-21 | closed by aw oc run: IPD 92u0v9 executed |
| `aw/lane/att-match-count` | `7d656496` | 1 | 579 | `none` | `att-match-count` | `no plan` | `none` | 2026-09-20 | feat(attention): state matching artifacts count at the end of the list |
| `aw/lane/bxx9af` | `d47566bb` | 1 | 70 | `none` | `bxx9af` | `executed` | `executed` | 2026-09-23 | feat(runner): consume the verifier evidence the runner already asks for (bxx9af) |
| `aw/lane/lkexaw` | `85372da1` | 1 | 28 | `lkexaw` | `lkexaw` | `approved` | `pending` | 2026-09-24 | feat(planprio-01): emit Priority and Work-Kind on scaffold and enforce them at ready-to-execute gate (lkexaw) |
| `aw/lane/lkexaw_attempt2` | `edef0df5` | 2 | 11 | `lkexaw_attempt2` | `lkexaw` | `approved` | `pending` | 2026-09-24 | docs(plans): update lkexaw execution and validation checklists |
| `aw/lane/m7gvuz` | `0313b4b8` | 1 | 56 | `none` | `m7gvuz` | `approved` | `pending` | 2026-09-23 | records(m7gvuz): re-validate the coverage gate at HEAD and re-measure the V-05 precondition |
| `aw/lane/m7gvuz_attempt2` | `43958b07` | 1 | 4 | `m7gvuz_attempt2` | `m7gvuz` | `approved` | `pending` | 2026-09-24 | chore(backlog): track test_ipd_lint CitationAnchorAdvisoryTests pending count coupling (24e5zv) |
| `aw/lane/m7gvuz_attempt3` | `01c1b805` | 2 | 53 | `none` | `m7gvuz` | `approved` | `pending` | 2026-09-23 | records(m7gvuz): re-derive the coverage gate's V-05 precondition independently at HEAD 5fea858f |
| `aw/lane/m7gvuz_attempt4` | `285e8364` | 1 | 4 | `m7gvuz_attempt4` | `m7gvuz` | `approved` | `pending` | 2026-09-24 | chore(backlog): track test_ipd_lint CitationAnchorAdvisoryTests pending count coupling (24e5zv) |
| `aw/lane/m7gvuz_attempt5` | `cf68eb14` | 1 | 4 | `m7gvuz_attempt5` | `m7gvuz` | `approved` | `pending` | 2026-09-24 | chore(backlog): track test_ipd_lint CitationAnchorAdvisoryTests pending count coupling (24e5zv) |
| `aw/lane/statusbar-run-progress` | `504de21e` | 1 | 762 | `none` | `statusbar-run-progress` | `no plan` | `none` | 2026-09-18 | fix(runner): display active run progress in statusbar for partially-executed sets |
| `aw/lane/tgop8e` | `5bd27128` | 1 | 60 | `none` | `tgop8e` | `approved` | `pending` | 2026-09-23 | stalecrit(tgop8e): record the live-artifact criterion convention; E-01/E-02 blocked by an executed target |
| `aw/lane/ut0vzr` | `def80353` | 0 | 0 | `ut0vzr` | `ut0vzr` | `approved` | `pending` | 2026-09-24 | lifecycle(0xmk4e): finalize 0xmk4e -> executed |
| `aw/lane/xdvglg` | `58acf20a` | 2 | 4 | `xdvglg` | `xdvglg` | `approved` | `pending` | 2026-09-24 | fix(plan): conform execution states and validation observed evidence in xdvglg |
| `aw/lane/xipfy1` | `d1cc184f` | 0 | 301 | `none` | `xipfy1` | `executed` | `executed` | 2026-09-22 | closed by aw oc run: IPD xipfy1 executed |
| `aw/lane/y4bdoz` | `b1678f14` | 2 | 96 | `none` | `y4bdoz` | `approved` | `pending` | 2026-09-23 | backlog(x1za6u,an3vqw): file the two defects found while executing y4bdoz |

- **Total `aw/lane/*` branches**: 18
- **Branches with ahead > 0**: 15
- **Sum of per-branch ahead counts**: 19
- **Distinct union commits ahead of `main`**: 19

---

## 4. Cited Evidence per Branch

### 4.1 Superseded Plans Group (Verbatim Retirement Headers)

1. **`6knsrx`** (`.aw/records/plans/superseded/20260829-wtisoland-01-6knsrx-land-the-six-verified-wtiso-lane-branches-stack-conflict-res.ipd.md`):
   > `RETIRED 2026-09-02: this plan's entire premise is gone. It existed to LAND the six wtiso lane branches as a stack; the maintainer subsequently ruled PORT, NOT MERGE (backlog vqv9im), the plan was de-armed to reviewed, and as of today every wtiso plan it would have landed is itself retired to superseded/. There is no stack left to land.`

2. **`qcqhj7`** (`.aw/records/plans/superseded/20260828-wtiso-02-qcqhj7-phase-1-stop-the-deadlock-and-silent-loss-in-lane-only-worke.ipd.md`):
   > `RETIRED 2026-09-02: superseded by the lanectn Set (7 plans, reviewed), which is the PORT of this phase's lane-containment design onto current main; see orchestrator h0zljh and spec 7ckptx (APPROVED, 41 requirements). The qyaime deadlock this phase targeted is already BOUNDED on main independently of it: StallWatchdog (oc_runipd.py:413, wired at :4449) kills a turn with no stream events inside --stall-timeout, and isolated turns are always fresh sessions`

3. **`rchpms`** (`.aw/records/plans/superseded/20260828-wtiso-03-rchpms-phase-2-move-lifecycle-authority-into-the-driver-driver-crea.ipd.md`):
   > `RETIRED 2026-09-02: PARTLY LANDED, and the part that mattered most is already on main. This phase owned the fix for xmqv5l, the defect that actually STRANDED completed work, and 2 of its 6 payload commits were cherry-picked to main in cdef9c90:`
   > `- E-01..E-03, key the begin receipt on the FROZEN REGION rather than the whole file`

4. **`7p9n2v`** (`.aw/records/plans/superseded/20260828-wtiso-04-7p9n2v-phase-3-one-typed-executioncontext-pathresolver-keyed-by-git.ipd.md`):
   > `RETIRED 2026-09-02: superseded by plan eulhzt, which achieves this phase's LOAD-BEARING invariant - every worktree of a checkout resolves ONE control root, keyed by git --git-common-dir - without the typed machinery. The dh0uno fork this phase existed to close is fixed there and pinned by tests/test_statefork_dh0uno.py (real git worktree; 8 of its 9 tests fail against pre-fix code).`

5. **`58ha43`** (`.aw/records/plans/superseded/20260828-wtiso-05-58ha43-phase-4-relocate-runtime-machine-state-out-of-the-repo-to-an.ipd.md`):
   > `RETIRED 2026-09-02: retiring UNLANDED, with no successor for its main deliverable. This phase would have relocated machine state out of the repository into an XDG state dir; nothing on main does that, so the capability is genuinely NOT delivered. WHY IT IS BEING RETIRED ANYWAY. It addresses no failure named in orchestrator bl9q3d's Concern...`

6. **`2c122z`** (`.aw/records/plans/superseded/20260828-wtiso-06-2c122z-phase-5-real-candidate-merge-integration-full-crash-recovery.ipd.md`):
   > `RETIRED 2026-09-02: retiring UNLANDED. Like Phase 4 it addresses NO failure named in orchestrator bl9q3d's Concern (it carried no From-Backlog link at all), and it sat at the end of a strict linear dependency chain whose earlier phases are themselves retired, so it was never reachable.`

---

### 4.2 Executed Plans Group (Landing Sites & Source Symbols in `main`)

1. **`nna8yz`** (Plan `20260901-lanectn-02-nna8yz...`):
   - **Feature**: Materialize lane inputs by copy with a sealed manifest.
   - **Landing Site**: `agent_workflows/lane_containment.py:2497` (`def materialize_lane_inputs(...)`).
   - **Merge Reflog**: `f7124702` (`merge lane nna8yz_attempt2`).

2. **`fn2l1u`** (Plan `20260908-actorparen-01-fn2l1u...`):
   - **Feature**: Reject unparseable actor at the setter instead of wedging.
   - **Landing Sites**:
     - `agent_workflows/render_stream.py:2207` (`class Refusal`)
     - `agent_workflows/render_stream.py:2303` (`def refusal_of_item(...)`)
     - `agent_workflows/attention_contract.py:704` (`def actor_refusal(...)`)
   - **Merge Commit**: `858c7cf6` (`merge aw/lane/fn2l1u_attempt2`), cited in `9476b48b`.

3. **`r2i1b1`** (Plan `20260907-orchprobe-01-r2i1b1...`):
   - **Feature**: Surface per-item refusal reason and remedy in runner stream.
   - **Landing Sites**: `agent_workflows/render_stream.py` and `agent_workflows/attention_contract.py` (`Refusal`, `refusal_of_item`, `actor_refusal`).
   - **Merge Commit**: `3e233fad`, cited in `9476b48b`.

4. **`03ie04`** (Plan `20260907-depreview-01-03ie04...`):
   - **Feature**: Read dependency target's status field instead of directory.
   - **Landing Site**: `agent_workflows/runner_shared.py:10698` (`selectors.read_front_matter_status`).
   - **Merge Commit**: `bf57a569` (`merge aw/lane/03ie04_attempt2`), closure at `bc9b3f43` / `db7bee80`.

5. **`ybkmzp`** (Plan `20260906-hostdefault-02-ybkmzp...`):
   - **Feature**: Shared resolution helper for verification decisions in runner shared.
   - **Landing Site**: `agent_workflows/runner_shared.py:13379` (`def resolve_verification_decision(...)`).
   - **Merge Commit**: `4234153f` (`merge verified lane ybkmzp to main`).

6. **`mm5p3v`** (Plan `20260908-runanalytics-08-mm5p3v...`):
   - **Feature**: `aw runs analyze` and query interface.
   - **Landing Site**: `agent_workflows/cli.py:2297` (`aw runs analyze`).
   - **Merge Commit**: `8243aff5` (`merge aw/lane/mm5p3v_attempt2`).

7. **`d7qoxv`** (Plan `20260913-dirtygates-01-d7qoxv...`):
   - **Feature**: Non-blocking warning for clean-base gate.
   - **Landing Site**: `agent_workflows/lane_containment.py:70`.
   - **Merge Commit**: `dc88a99a` (`merge aw/lane/d7qoxv_attempt2`).

---

## 5. Escalate List (E-05)

**The ESCALATE list is EMPTY.**
Every one of the 14 target branches resolved cleanly with cited evidence (either explicit retirement rationale or verified landing in `main`). No unresolved branches require maintainer escalation.

---

## 6. Execution and Verification Summary

- **RECOVER Operations**:
  - `upgtest`: Successfully recovered and merged in `9476b48b` on 2026-09-17 with all 8 artifacts (`hdhzr2`, `x15f0q`, `ygtykn`, `kapm7y`, `u27q6g`, `h90ij1`, `z1yefm`, `i8u6hh`).
  - No further RECOVER operations were required.
- **DELETE Operations**:
  - All 12 target branches (`2c122z`, `58ha43`, `7p9n2v`, `rchpms`, `qcqhj7`, `nna8yz`, `fn2l1u`, `r2i1b1`, `03ie04`, `ybkmzp`, `mm5p3v`, `d7qoxv`) have been confirmed removed from `refs/heads/`.
  - Attention State Prediction: Under `classify_lane_integration`, an absent branch produces `LANE_EMPTY_OF_WORK` which is absent from `LANE_ATTENTION_STATES`, causing the row to go silent.
  - Zero attention rows remain for any of the 14 triaged branches.

---

## 7. Conclusions and Closure

Backlog item `qliia1` is fully discharged by this triage and evidentiary record. All 14 target branches are dispositioned with cited proof, establishing that no unmerged work remains stranded from the historical backlog.
