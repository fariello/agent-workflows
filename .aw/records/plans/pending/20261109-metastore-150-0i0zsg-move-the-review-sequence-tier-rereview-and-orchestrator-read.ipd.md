# IPD: Move the review sequence, tier, rereview and orchestrator readiness reads onto artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Split from `2zpw22` (Order 36) in round 3 of the metastore re-split, per research `nj8zdp` guidance: `2zpw22` E-02 named 13 distinct units (seven modules and nine baseline modules) in one item. Spec `4sd62s` C5a requires every record module to read metadata through the cache. Measured 2026-11-07 at `ac76110f4`: `review_sequence` (13 sites in 5 functions), `review_tier` (3 in 1) and `review_rereview` (5 in 2) read through `ParsedDoc.meta_fields` and `ipd_schema.read_readiness`, and `orchestrator_readiness` (8 in 4) through `_BATCH_META_RE` and `meta_fields`.
- Scope: The review-sequence and orchestration subset of `2zpw22` E-02, carried unchanged and divided by module family: `review_sequence`, `review_tier` and `review_rereview` (E-01); `orchestrator_readiness` (E-02). EXCLUDES: the review findings, audit and reviews modules (`y4spqy`); `production_checks`, `work_cmd` and `artifact_adopt` (`awmsyq`, Order 154); the WRITE half of `review_sequence.restore_pre_s7_plan` (Order 07); the residual audit (kept in `2zpw22`).
- Scope-Paths: agent_workflows/review_sequence.py, agent_workflows/review_tier.py, agent_workflows/review_rereview.py, agent_workflows/orchestrator_readiness.py, tests/test_readers_review_modules.py, .aw/records/plans/pending/20261109-metastore-150-0i0zsg-move-the-review-sequence-tier-rereview-and-orchestrator-read.ipd.md
- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:h58z9n, executed:tve77h, executed:xexn45, executed:y4spqy
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 150
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0i0zsg

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 2zpw22 (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The review sequence, review tier, re-review and orchestrator readiness modules read plan metadata only through `artifact_meta.read`/`query`/`history` (or `artifact_meta.read_text` for in-memory snapshots), with each move pinned before and after.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The pin-first rule of `ffceq0` applies (carried from `t4gl15` through `2zpw22`): BEFORE the edit, a behavioral test pins the reader's current observable behavior and runs green on the unmodified code; AFTER the edit, the same test runs unchanged. Save each item's per-test outcome list under the gitignored `.aw/state/t4gl15/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/t4gl15/<file>`) before the move and into the matching after file after it. Run a new module's `-k` selection as its own command. Tests go in `tests/test_readers_review_modules.py` (created by `y4spqy`); none reads production source.

Commit through `aw commit 0i0zsg -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.

### Task group 1: sequence and orchestration modules

- [ ] E-01 (carried from `2zpw22` E-02, review-sequence subset) Pin, then move, `review_sequence` (`count_verdict_bearing_entries`, `restore_pre_s7_plan` status and readiness reads, the snapshot verdict checks), `review_tier` (`meta_fields` reads) and `review_rereview` (`meta_fields` reads, the `ipd_schema.read_readiness` call) onto `artifact_meta.read`/`query`/`history`, or `artifact_meta.read_text` for before/after snapshot strings that are not files. `restore_pre_s7_plan` still WRITES plan text and is a writer for Order 07; only its reads move here. Pin in `tests/test_readers_review_modules.py` and run `tests/test_review_sequence.py`, `tests/test_review_sequence_runner.py`, `tests/test_review_tier.py` and `tests/test_review_rereview.py` green before and after (outcome lists `E-12a-before.txt`/`E-12a-after.txt`).
  - Depends on: none
  - Expected outcome: all listed modules pass before and after; none of the three modules contains a `^-` metadata regex call.
  - Execution state: pending

- [ ] E-02 (carried from `2zpw22` E-02, orchestration subset) Pin, then move, `orchestrator_readiness` (`_BATCH_META_RE`, `meta_fields` reads) onto `artifact_meta.read`/`query`. Pin in `tests/test_readers_review_modules.py` and run `tests/test_orchestrator_readiness.py` green before and after (outcome lists `E-12b-before.txt`/`E-12b-after.txt`).
  - Depends on: E-01
  - Expected outcome: the module passes before and after; `orchestrator_readiness` contains no `^-` metadata regex call.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

Carried from `2zpw22` Step 0:

- Interface names: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)`, from `tve77h`; `artifact_meta.read_text(text, *, record_type=None)` (added by `cdglt1`) and decision D-1 from `ffceq0`.
- Cite code by SYMBOL (`module.function`), never a bare line number (advisory `IPD-C801`).

## Findings

Carried from `2zpw22` (measured 2026-11-07 at `ac76110f4`):

| Id | Evidence | Finding |
|---|---|---|
| F-02 | AST pass over `rg` hits of each module's reader symbols (`meta_fields`, `read_readiness(`, `_BATCH_META_RE`, plus the `^-` regex pattern): `review_sequence` 13 sites in 5 functions, `review_tier` 3 in 1, `review_rereview` 5 in 2, `orchestrator_readiness` 8 in 4 | E-01: 8 functions; E-02: 4 functions. |

Size (round 3): measured with `ipd_schema.count_named_units`, each item names at most 7 distinct units; 5 work Scope-Paths.

READER LEDGER (this part's subset of the `2zpw22` row, copied from `t4gl15`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `review_sequence`, `review_tier`, `review_rereview`, `orchestrator_readiness` | `meta_fields`, `read_readiness` and module-local regex reads | `tests/test_review_sequence.py`, `tests/test_review_sequence_runner.py`, `tests/test_review_tier.py`, `tests/test_review_rereview.py`, `tests/test_orchestrator_readiness.py` | cached fields or `read_text` for snapshots |

DECISIONS (copied from `t4gl15` through `2zpw22`, whose text is authoritative): D-1 PLAN records return the canonical normalized status (`plans.normalize_status` of the first token); every other type keeps its raw single-token status.

## Proposed changes (ordered, validatable)

1. Pin then move the review sequence, tier and re-review modules (E-01).
2. Pin then move the orchestrator readiness module (E-02).

## Deferred / out of scope (with reason)

- The WRITE half of `review_sequence.restore_pre_s7_plan`.
  - Carrier: xexn45
- The residual audit of these modules.
  - Carrier: 2zpw22

## Scope check

- Over-scope: none.
- Under-scope: none known. This part carries the review-sequence and orchestration subset of `2zpw22` E-02 unchanged; the production-check, work and adoption subset is in `awmsyq`, and together they equal the original list.

## Required tests / validation

Tests added to `tests/test_readers_review_modules.py` (core). Commands: every module named in E-01 and E-02, the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change. Implements the review-sequence and orchestration part of `4sd62s` C5a.

## Open questions

### OQ-01: How was the `2zpw22` E-02 module list partitioned?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: By module family: the four review and orchestration modules (which read plan readiness and review state) here, and the three record-shaped readers (`production_checks`, `work_cmd`, `artifact_adopt`) in `awmsyq`. The nine baseline modules follow their modules. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `diff .aw/state/t4gl15/E-12a-before.txt .aw/state/t4gl15/E-12a-after.txt` (outcome lists of `tests/test_review_sequence.py tests/test_review_sequence_runner.py tests/test_review_tier.py tests/test_review_rereview.py`) printing nothing, `python3 -m pytest -o addopts="" -v tests/test_readers_review_modules.py -k "sequence or tier or rereview"` all PASSED, and the empty output of `rg -n "re\.\w+\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/review_sequence.py agent_workflows/review_tier.py agent_workflows/review_rereview.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `diff .aw/state/t4gl15/E-12b-before.txt .aw/state/t4gl15/E-12b-after.txt` (outcome list of `tests/test_orchestrator_readiness.py`) printing nothing, `python3 -m pytest -o addopts="" -v tests/test_readers_review_modules.py -k orchestrator` all PASSED, and the empty output of `rg -n "re\.\w+\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/orchestrator_readiness.py`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every `- Item-Dependencies:` edge is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every reader move is pin-first.

Honesty rule: run the named modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 0i0zsg -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
