# IPD: Bound check_engine status reads and is_retired to the metadata region's first Status bullet

- Date: 2026-09-26
- Kind: child
- Concern: `check_engine._status_meta` and `check_engine.is_retired` both run `_STATUS_META_RE` (`(?m)^- Status:\s*(\S+)\s*$`) over the WHOLE file and take the first match, so a record with no front-matter `- Status:` that quotes one (in a fence, an open-question block, a findings table row) is read as carrying the quoted status. `_status_meta` feeds `check_status_untooled` (staged and HEAD status) and the backlog done-gate backstop (`if _status_meta(staged_text) != "done"`); `is_retired` decides whether a record is hidden from `_iter_type_files`, the setid-collision pass, the carrier gate-mismatch check and the dependency-statement sweep. kecxnb applies the metadata-region-first-bullet rule to the executed-transition hook; after it lands the hook is stricter than these siblings.
- Scope: IN: one helper returning the first `- Status:` value inside `selectors.metadata_region(text)`; `_status_meta` and `is_retired` use it; outcome tests; a before/after diff of `aw attention` and `aw check all`. OUT: other `_PLAN_STATUS_RE` readers (they already search `_metadata_region`); YAML `status:` reading; the hook (kecxnb).
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_status_meta.py
- Item-Dependencies: executed:kecxnb
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: pyk78c
- Blocks-Release: next
- Set: fencegate
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ahq0mq

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog pyk78c: bound _status_meta and is_retired to the metadata region's first Status bullet; measured corpus impact is one research record (ebh1ap).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A record's status, for untooled-change detection, the backlog close backstop and retirement, is the first `- Status:` bullet of its own metadata region and never a line it merely quotes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one bounded reader

- [ ] E-01 Capture the BEFORE state: `python3 -m agent_workflows attention --format json > /tmp/opencode/ahq0mq-attention-before.json` and `python3 -m agent_workflows check all --agent > /tmp/opencode/ahq0mq-check-before.jsonl` (exit codes noted; findings are expected, this is a baseline). Then in `agent_workflows/check_engine.py` add `_metadata_status(text: str | None) -> str | None`: `_STATUS_META_RE.search(_metadata_region(text))`, lowercased and stripped, None when absent. `search` returns the FIRST match in the region, which is the first-bullet rule; that matters because `selectors.metadata_region` returns the whole text for a record with no `##` heading (kecxnb F-4). Make `_status_meta` return `_metadata_status(text)` and make `is_retired` use `_metadata_status(text) in _RETIRED_STATUSES`. Leave `_STATUS_META_RE` itself unchanged.
  - Depends on: none
  - Expected outcome: both readers ignore any `- Status:` below the metadata region.
  - Execution state: pending

- [ ] E-02 Add `tests/test_check_engine_status_meta.py` (outcome cases): (a) plan text with no front-matter status, a `## Goal` heading, and a fenced block containing `- Status: executed` -> `_status_meta` is None and `is_retired(<file>)` is False; (b) front matter `- Status: approved` plus the same fenced quote -> `approved`; (c) headingless plan whose first bullet is `- Status: approved` and which later quotes `- Status: executed` -> `approved`; (d) end to end with a temp git repo: commit a plan at `approved` with a `## Workflow history` line, then stage an edit that ONLY adds a fenced `- Status: executed` quote in the body -> `check_engine.check_status_untooled(repo)` returns no drift; (e) `is_retired` on a non-retired-path file whose metadata says `- Status: executed` -> True (the real signal still works). For `is_retired`, write files under a temp dir whose path contains none of `_RETIRED_PATH_SEGMENTS`.
  - Depends on: E-01
  - Expected outcome: five cases pass; (a) and (c) fail against the pre-change readers.
  - Execution state: pending

- [ ] E-03 Capture the AFTER state with the same two commands to `...-after` files and diff them (`diff <(python3 -m json.tool before) <(python3 -m json.tool after)` for attention; `diff` of the sorted check JSONL). Expected, from the authoring sweep over `.aw/records/**/*.md` (F-2): exactly one record changes retirement, research `20260924-lane-branch-triage-00-ebh1ap-lane-branch-triage.findings.md` (YAML `status: reference`, body `- Status: done`), which was hidden as retired and now becomes visible to research-type checks and the attention view; nine further records change their `_status_meta` value from a quoted body status to None, none of which is a plan, so `check_status_untooled` and the backlog backstop see no difference on the current tree. Explain every line of both diffs; any change not attributable to ebh1ap is a finding to report.
  - Depends on: E-02
  - Expected outcome: diffs limited to ebh1ap-attributable lines, each explained.
  - Execution state: pending

- [ ] E-04 Run the bare suite `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.metadata_region` is the ONE metadata boundary every identity/status reader is bounded to (its docstring); `check_engine._metadata_region` is this module's accessor for it, already used by `_read_declared_id` and by `_PLAN_STATUS_RE.search(_metadata_region(text))` in the graduation index.
- kecxnb (fencegate-01, approved) applies the same first-bullet-in-region rule to the executed-transition hook; this plan aligns the sibling readers and so depends on it for a consistent landing order.
- `metadata_region` returns the leading YAML fence only for YAML-front-matter records (research, roadmaps), so for those records a body `- Status:` line is outside the region by design.
- Tests assert OUTCOMES only (maintainer rule).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `check_engine._status_meta`, `check_engine.is_retired` | Both search the whole file. | `m = _STATUS_META_RE.search(text)` in each |
| F-2 | INFO | corpus sweep | Comparing whole-file vs metadata-region first match over every `.aw/records/**/*.md` on disk: 10 records differ, all toward None: research `kdr9kv` (open), `fpt0dg` (open), `ebh1ap` (done), `27rjro` (reviewed), `takpys` (reviewed); reviews `uvwqvz` (open) and `reviews/README.md` (open); gitignored run records `run-20260925T174509Z-636951/decisions-and-questions.md` (Resolved), `run-20260923T024621Z-3869306/.../06-bwgyum-...execution-report.md` (graduated), `run-20260924T050407Z-3108751/.../02-lkexaw-...execution-report.md` (draft). Only `ebh1ap` changes retirement (`done` is in `_RETIRED_STATUSES`). No plan differs. | sweep script: `R.search(t)` vs `R.search(selectors.metadata_region(t))` |
| F-3 | INFO | brief correction | The brief says "~10 research/review/run/README files whose retirement changes"; measured, 10 change their read status but only 1 (`ebh1ap`) changes retirement. | F-2 |
| F-4 | INFO | `is_retired` callers | `_iter_type_files` (default `include_retired=False`), the setid-collision visibility filter, the carrier gate-mismatch skip, and the dependency-statement target filter. | `if not include_retired and is_retired(p, record_type)`, `caller_visible = include_retired or not is_retired(p, record_type)`, `if is_retired(p): continue`, `[pt for pt in all_plans if not is_retired(pt[0])]` |

## Proposed changes (ordered, validatable)

1. E-01: baseline, then the bounded helper used by both readers.
2. E-02: outcome tests.
3. E-03: before/after diff, explained.
4. E-04: bare suite.

## Deferred / out of scope (with reason)

- Reading YAML `status:` in `is_retired` so research records retire by their own front matter: a separate behavior change with its own corpus impact.
  - Carrier-Declined: not a defect of the fence-quoting class; no item requests it.

## Scope check

- Over-scope: `is_retired` is beyond the backlog item's `_status_meta` wording; included because it is the same whole-file read with the same fix (brief).
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_check_engine_status_meta.py -v`; the E-03 diffs; bare suite. Test rule: outcomes only.

## Spec / documentation sync

N/A: the ipd-lifecycle spec already defines a record's status as its metadata `- Status:`; this makes two readers conform.

## Open questions

### OQ-01: Should ebh1ap's newly visible state be fixed in this plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. It is another party's research record; if it produces a finding after the change, report it in E-03 and leave the record untouched (shared-checkout rule).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff; paste `python3 -c` driving `_status_meta` on (a) and (c) from E-02 showing `None` and `approved`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test run showing 5 passed; revert E-01 IN THE WORKTREE and paste (a) and (c) FAILING on the status assertion (not an import error); restore.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both diffs in full (attention JSON and check JSONL) and one sentence per differing line attributing it to ebh1ap or flagging it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed; name any failure as pre-existing (with evidence at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. Two readers in `check_engine` stop reading status lines below a record's metadata region. Measured effect on today's tree: one research record (`ebh1ap`) stops being treated as retired and becomes visible to checks and `aw attention`; no plan's read status changes. The executor proves the effect with before/after diffs.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if the E-03 diff shows a PLAN changing status or retirement, or a new `aw check` error severity finding not attributable to ebh1ap, stop and report before committing.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); the `/tmp` baseline files are not committed. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `pyk78c` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`.
