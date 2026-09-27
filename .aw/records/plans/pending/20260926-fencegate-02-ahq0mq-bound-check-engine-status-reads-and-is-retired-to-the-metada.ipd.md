# IPD: Bound check_engine status reads and is_retired to the metadata region's first Status bullet

- Date: 2026-09-26
- Kind: child
- Concern: `check_engine._status_meta` and `check_engine.is_retired` both run `_STATUS_META_RE` (`(?m)^- Status:\s*(\S+)\s*$`) over the WHOLE file and take the first match, so a record with no front-matter `- Status:` that quotes one (in a fence, an open-question block, a findings table row) is read as carrying the quoted status. `_status_meta` feeds `check_status_untooled` (staged and HEAD status) and the backlog done-gate backstop (`if _status_meta(staged_text) != "done"`); `is_retired` decides whether a record is hidden from `_iter_type_files`, the setid-collision pass, the carrier gate-mismatch check and the dependency-statement sweep. kecxnb applies the metadata-region-first-bullet rule to the executed-transition hook; after it lands the hook is stricter than these siblings.
- Scope: IN: one helper returning the first `- Status:` value inside `selectors.metadata_region(text)`; `_status_meta` and `is_retired` use it; outcome tests; a before/after diff of `aw attention` and `aw check all`. OUT: other `_PLAN_STATUS_RE` readers (they already search `_metadata_region`); YAML `status:` reading; the hook (kecxnb).
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_status_meta.py
- Item-Dependencies: executed:kecxnb
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: pyk78c
- Blocks-Release: next
- Set: fencegate
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: ahq0mq
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 all FIXED. Every source claim verified exact and the defect demonstrated (whole-file read returns executed where the region-bounded read returns None). PR-002 is the main correction: the plan's predicted effect does not exist, measured by simulating the change, aw attention is BYTE-IDENTICAL and never calls is_retired, ebh1ap is already in that view classified from its YAML front matter, and aw check all reports the same 4 pre-existing findings; the only change is internal (_iter_type_files research 91 to 92, producing no finding). Reframed as correctness-by-construction with E-03 now confirming the ABSENCE of a diff. PR-003 adds the _iter_type_files count as the only positive proof, since an empty diff is otherwise indistinguishable from work never done. PR-001: only case (a) of five discriminates, so the other four are relabelled controls and V-02 may no longer claim (c) fails. PR-004 corrects the 10-vs-7 record count (three are gitignored run records). Findings and decisions D-1..D-3 in .aw/records/reviews/20260926-fencegate-02-ahq0mq-bound-check-engine-status-reads-and-is-retired-to-the-metada.review.md
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog pyk78c: bound _status_meta and is_retired to the metadata region's first Status bullet; measured corpus impact is one research record (ebh1ap).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A record's status, for untooled-change detection, the backlog close backstop and retirement, is the first `- Status:` bullet of its own metadata region and never a line it merely quotes.

WHAT THIS BUYS, STATED HONESTLY AFTER REVIEW MEASURED IT (PR-002). There is NO observable change on today's tree: `aw attention` is byte-identical, `aw check all` reports the same findings, and no plan's read status differs. The value is prospective and structural: these two readers join the rest of the toolkit in being bounded to `selectors.metadata_region`, so a FUTURE record that quotes a status (in a fence, an open-question block, a findings row) cannot be mis-hidden as retired or mis-read by the untooled-change detector. That is a real defect class in a repository whose records routinely document their own metadata format, and it is also why this plan is correctly `- Priority: low`. Do NOT expect a visible before/after difference; E-03 exists to CONFIRM its absence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one bounded reader

- [ ] E-01 Capture the BEFORE state: `python3 -m agent_workflows attention --format json > /tmp/opencode/ahq0mq-attention-before.json` and `python3 -m agent_workflows check all --agent > /tmp/opencode/ahq0mq-check-before.jsonl` (exit codes noted; findings are expected, this is a baseline). Then in `agent_workflows/check_engine.py` add `_metadata_status(text: str | None) -> str | None`: `_STATUS_META_RE.search(_metadata_region(text))`, lowercased and stripped, None when absent. `search` returns the FIRST match in the region, which is the first-bullet rule; that matters because `selectors.metadata_region` returns the whole text for a record with no `##` heading (kecxnb F-4). Make `_status_meta` return `_metadata_status(text)` and make `is_retired` use `_metadata_status(text) in _RETIRED_STATUSES`. Leave `_STATUS_META_RE` itself unchanged.
  - Depends on: none
  - Expected outcome: both readers ignore any `- Status:` below the metadata region.
  - Execution state: pending

- [ ] E-02 Add `tests/test_check_engine_status_meta.py` (outcome cases): (a) plan text with no front-matter status, a `## Goal` heading, and a fenced block containing `- Status: executed` -> `_status_meta` is None and `is_retired(<file>)` is False; (b) front matter `- Status: approved` plus the same fenced quote -> `approved`; (c) headingless plan whose first bullet is `- Status: approved` and which later quotes `- Status: executed` -> `approved`; (d) end to end with a temp git repo: commit a plan at `approved` with a `## Workflow history` line, then stage an edit that ONLY adds a fenced `- Status: executed` quote in the body -> `check_engine.check_status_untooled(repo)` returns no drift. EXECUTED AT REVIEW AND IT IS A CONTROL, NOT A REGRESSION TEST (PR-001): pre-fix drift is already `[]`, because the plan carries a REAL front-matter `- Status: approved` and `search` returns it first on BOTH sides (`HEAD _status_meta: approved`, `STAGED _status_meta: approved`), so no status delta exists to flag. Keep it (an end-to-end control over the real git-backed path is worth having, and it would catch a future reader that started matching the LAST occurrence) but do NOT present it as proving the fix. If you want a case where the untooled detector's verdict actually CHANGES, it must be a plan with NO front-matter `- Status:` at all, and note such a plan is already structurally invalid, which is a reason no such case is required here; (e) `is_retired` on a non-retired-path file whose metadata says `- Status: executed` -> True (the real signal still works). For `is_retired`, write files under a temp dir whose path contains none of `_RETIRED_PATH_SEGMENTS`.
  WHICH CASES ACTUALLY DISCRIMINATE, MEASURED AT REVIEW (PR-001), because four of the five pass identically before and after and a plan that claims otherwise sends the executor hunting a phantom. Driving the whole-file read against the region-bounded read on each shape:

  ```text
  DISCRIMINATES  before=executed   after=None        (a) no front-matter status + ## Goal + fenced quote
  vacuous        before=approved   after=approved    (b) front matter approved + same fenced quote
  vacuous        before=approved   after=approved    (c) HEADINGLESS, first bullet approved, later quotes executed
  vacuous        before=executed   after=executed    (e) metadata says executed (real signal)
  ```

  So (a) is the ONLY case that fails pre-change. (c) is vacuous for a REASON worth keeping rather than deleting: `selectors.metadata_region` returns the WHOLE text for a headingless record, so the region-bounded read sees the quoted line too and only `search`'s FIRST-match semantics keep the answer right. That makes (c) a genuine guard against someone "improving" the helper into a last-match or findall-based read, which would silently break exactly this shape. KEEP (b), (c) and (e) as CONTROLS and label them as such in the test's docstrings, stating that each is expected to pass before AND after; a control mislabelled as a regression test is what makes a suite look stronger than it is.
  - Depends on: E-01
  - Expected outcome: five cases pass. (a) FAILS against the pre-change reader. (b), (c), (d) and (e) pass before AND after by design, as controls. See E-02's measured table and the note on (d) below.
  - Execution state: pending

- [ ] E-03 Capture the AFTER state with the same two commands to `...-after` files and diff them (`diff <(python3 -m json.tool before) <(python3 -m json.tool after)` for attention; `diff` of the sorted check JSONL).

  THE EXPECTED DIFF IS EMPTY ON BOTH SURFACES, AND THAT IS THE CORRECT OUTCOME (corrected at review, PR-002 and PR-003; the earlier prediction that ebh1ap "becomes visible to research-type checks and the attention view" was MEASURED FALSE). Simulated at review by patching `is_retired` and `_status_meta` to the region-bounded form and driving the real commands:
  - `aw attention --format json` is BYTE-IDENTICAL (1385256 bytes both sides). `attention.py` never calls `is_retired` at all (`'is_retired' in inspect.getsource(attention)` is False), and ebh1ap is ALREADY in the view today, classified from its YAML front matter: `{"id": "ebh1ap", "tree": "research", "native_status": "reference", "attention_class": "done"}`. It therefore cannot "become visible"; it was never hidden there.
  - `aw check all --agent` reports the SAME 4 findings before and after, with an empty symmetric difference. The 4 are pre-existing and unrelated (three `check.id6-identity-slot` on walkthroughs, one `check.system-layout-missing`).
  - The one real internal change is confirmed and is invisible from outside: `_iter_type_files(repo, 'research')` yields 91 paths before and 92 after, the single newly-yielded path being ebh1ap, and no check that consumes it produces a finding for it (verified individually across `check_collisions`, `check_content`, `check_id_outside_metadata_region`, `check_name_identity`, `check_names`, `check_setid_length`, `check_lifecycle_transitions`: all unchanged).

  So E-03's job is to CONFIRM NO OBSERVABLE CHANGE, plus the one internal count change. RE-DERIVE all of it at execution (the corpus moves); the BAR is that every difference is explained, not that the numbers match. A non-empty diff on either surface is a finding to report, and a PLAN appearing in either diff is the stop condition below.
  - Depends on: E-02
  - Expected outcome: both diffs EMPTY; the `_iter_type_files(repo, 'research')` count rises by exactly one (ebh1ap) and no finding is produced for it. Any other difference is reported.
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
| F-4b | INFO (added at review) | F-2's count, re-derived | F-2's sweep is CORRECT but its 10 includes 3 GITIGNORED run records that do not exist in a fresh clone or an isolated lane. Re-derived at review over `.aw/records/**/*.md` only: 7 records change their read status, all toward None, and they are exactly F-2's first 7 (`kdr9kv`, `fpt0dg`, `ebh1ap`, `27rjro`, `takpys`, reviews `uvwqvz`, `reviews/README.md`). The 3 run records were absent here (`.aw/workflow-artifacts/runs/` does not exist in this lane), which is why the numbers differ; neither figure is wrong, they count different populations. Only `ebh1ap` changes retirement, exactly as F-2 says. E-03 must therefore expect 7-plus-or-minus-run-records rather than a fixed 10. | Sweep over `.aw/records` only: 7 changes, printed with before/after values; `find .aw -maxdepth 3 -name 'run-*' -type d` -> nothing. |
| F-2 | INFO | corpus sweep | Comparing whole-file vs metadata-region first match over every `.aw/records/**/*.md` on disk: 10 records differ, all toward None: research `kdr9kv` (open), `fpt0dg` (open), `ebh1ap` (done), `27rjro` (reviewed), `takpys` (reviewed); reviews `uvwqvz` (open) and `reviews/README.md` (open); gitignored run records `run-20260925T174509Z-636951/decisions-and-questions.md` (Resolved), `run-20260923T024621Z-3869306/.../06-bwgyum-...execution-report.md` (graduated), `run-20260924T050407Z-3108751/.../02-lkexaw-...execution-report.md` (draft). Only `ebh1ap` changes retirement (`done` is in `_RETIRED_STATUSES`). No plan differs. | sweep script: `R.search(t)` vs `R.search(selectors.metadata_region(t))` |
| F-3 | INFO | brief correction | The brief says "~10 research/review/run/README files whose retirement changes"; measured, 10 change their read status but only 1 (`ebh1ap`) changes retirement. | F-2 |
| F-5 | MEDIUM (added at review, PR-002) | `attention.py` / the plan's own effect claim | THE PLAN'S PREDICTED USER-VISIBLE EFFECT DOES NOT EXIST. It says ebh1ap "was hidden as retired and now becomes visible to research-type checks and the attention view", and the gate repeated it. Both halves are false. `attention.py` NEVER calls `is_retired`, so this change cannot alter its output, and ebh1ap is ALREADY in the attention view today, classified from its YAML front matter. Nor does any check produce a finding for the newly-yielded file. The change is still correct, but it is correctness-by-construction with no observable effect on today's tree, and saying otherwise would have had a human approve a benefit that is not delivered and an executor hunt a diff that cannot appear. | Simulated at review by patching both readers to the region-bounded form: `aw attention --format json` BYTE-IDENTICAL (1385256 bytes both sides); `'is_retired' in inspect.getsource(attention)` -> False; the live view already contains `{"id": "ebh1ap", "tree": "research", "native_status": "reference", "attention_class": "done"}`; `aw check all --agent` -> same 4 findings, empty symmetric difference; `_iter_type_files(repo,'research')` 91 -> 92 with ebh1ap the only addition and no finding for it; seven individual checks that consume it all unchanged. |
| F-6 | LOW (added at review, PR-001) | `tests/test_check_engine_status_meta.py` as specified | FOUR OF E-02's FIVE CASES ARE CONTROLS, NOT REGRESSION TESTS, and the plan labelled two of them as failing pre-change. Measured before-vs-after per shape: only (a) discriminates (`executed` -> `None`); (b), (c) and (e) are identical on both sides, and the end-to-end (d) already returns `[]` pre-fix because the plan carries a real front-matter `- Status: approved` that `search` finds first on both sides. (c) is vacuous for an instructive reason worth keeping: `metadata_region` returns the WHOLE text for a headingless record, so only `search`'s first-match semantics keep that answer right, which makes (c) a guard against a future last-match or findall rewrite. | Ran each shape through both readers: `DISCRIMINATES before=executed after=None (a)`; `vacuous before=approved after=approved (b)`; `vacuous before=approved after=approved (c)`; `vacuous before=executed after=executed (e)`. For (d), in a temp git repo: `PRE-FIX check_status_untooled drift: []`, `HEAD _status_meta: approved`, `STAGED _status_meta: approved`. |
| F-4 | INFO | `is_retired` callers | `_iter_type_files` (default `include_retired=False`), the setid-collision visibility filter, the carrier gate-mismatch skip, and the dependency-statement target filter. | `if not include_retired and is_retired(p, record_type)`, `caller_visible = include_retired or not is_retired(p, record_type)`, `if is_retired(p): continue`, `[pt for pt in all_plans if not is_retired(pt[0])]` |

## Proposed changes (ordered, validatable)

1. E-01: baseline, then the bounded helper used by both readers.
2. E-02: outcome tests, ONE regression case (a) plus four labelled controls (F-6).
3. E-03: before/after diff, expected EMPTY on both surfaces, plus the `_iter_type_files` count as the only positive proof the change landed (F-5).
4. E-04: bare suite.

No test asserts on source text or structure (maintainer rule): every case drives the real `_status_meta`, `is_retired`, or `check_status_untooled` and asserts on the returned value.

## Deferred / out of scope (with reason)

- Reading YAML `status:` in `is_retired` so research records retire by their own front matter: a separate behavior change with its own corpus impact.
  - Carrier-Declined: not a defect of the fence-quoting class; no item requests it.

## Scope check

- Over-scope: `is_retired` is beyond the backlog item's `_status_meta` wording; included because it is the same whole-file read with the same fix (brief). Reaffirmed at review: `is_retired` is in fact the ONLY one of the two with any measurable effect on the current corpus (the single `_iter_type_files` addition), so excluding it would have left the plan with literally nothing to demonstrate.
- Under-scope: none.
- Scope-Paths note: `agent_workflows/check_engine.py` and one NEW test module. No `.spec.md` is in `- Scope-Paths:`, so this run declares no spec edit. The `/tmp/opencode/` baseline files E-01 and E-03 write are scratch and are not committed; that directory exists and is writable (verified at review), while a bare `/tmp/<name>` path may be refused by the sandbox, so keep the `/tmp/opencode/` prefix exactly as written.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_check_engine_status_meta.py -v`; the E-03 diffs; bare suite. Test rule: outcomes only.
- The new test module must carry NO `pytestmark = pytest.mark.slow`, or `pyproject.toml`'s configured `-m 'not slow'` excludes it from E-04's bare run and the module is written but never executed by its own gate.
- Exactly ONE of the five cases is a regression test (a). Label the other four as CONTROLS in their docstrings, each stating it is expected to pass before AND after (F-6). A suite that presents four controls as regression tests overstates its own coverage, which is the failure this review measured in the plan's Expected outcome.
- Bare `python3 -m pytest`, with no added `-n0`, second `-q`, or `-p no:randomly`. Baseline measured at review on this lane: `2501 passed, 2 skipped, 3 warnings in 59.95s`; RE-DERIVE it rather than matching the number, and compare failing node sets rather than counts.
- Pre-existing `aw check all` baseline measured at review: exit 1 with 4 findings (three `check.id6-identity-slot` on walkthroughs, one `check.system-layout-missing` on `.aw/system/layout.json`). These are unrelated to this plan and must be named as pre-existing, not investigated.

## Spec / documentation sync

N/A: the ipd-lifecycle spec already defines a record's status as its metadata `- Status:`; this makes two readers conform.

## Open questions

### OQ-01: Should ebh1ap's newly visible state be fixed in this plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. It is another party's research record; if it produces a finding after the change, report it in E-03 and leave the record untouched (shared-checkout rule). SETTLED FURTHER AT REVIEW: the question is moot on today's tree, because ebh1ap produces NO finding once visible (verified individually across the seven checks that consume `_iter_type_files`), and it was never hidden from `aw attention` at all. So there is nothing to fix and nothing to report beyond the count change.

### OQ-02: Is a change with no observable effect on the current tree worth executing at all?

- Blocking: no
- Status: resolved
- Owner: reviewer (raised and resolved at review from F-5)
- Resolution or deferral rationale: YES, but it must be SOLD AS WHAT IT IS. Review measured that the plan's claimed user-visible benefit does not exist (attention byte-identical, `check all` unchanged, no plan affected), which raises the fair question of whether to retire the plan instead. It should still execute, for two reasons that do not depend on a visible diff. FIRST, the defect is real and latent: both readers match `- Status:` anywhere in a file, and this repository's records routinely QUOTE metadata blocks as prose, so the next record that does so in a non-retired-path location is mis-read. `selectors.metadata_region`'s own docstring states the principle ("a document that merely QUOTES a metadata block ... cannot be read as ASSERTING the quoted values. Identity comes from where an artifact declares it"), and these two readers are the remaining holdouts. SECOND, the sibling `kecxnb` already applied this rule to the executed-transition hook, so leaving these two unbounded means one repository with two different answers to "what is this record's status?", which is the divergence class this toolkit repeatedly pays for. What review CHANGED is the framing: the Goal, the gate and E-03 now say there is no observable effect and E-03's job is to confirm its absence, so nobody approves a benefit that is not delivered or hunts a diff that cannot appear.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff; paste `python3 -c` driving `_status_meta` on (a) and (c) from E-02 showing `None` and `approved`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test run showing 5 passed. Then revert E-01 IN THE WORKTREE and paste the pre-change run, which must show (a) FAILING on the status assertion (not an import error) and (b), (c), (d), (e) still PASSING; restore and paste the passing run again. Do NOT claim (c) fails pre-change: measured at review it passes on both sides, and asserting otherwise would be evidence of a run that did not happen (F-6). State per case whether it is the REGRESSION test (a) or a CONTROL (the other four), and for (c) state the reason it is a control worth keeping (`metadata_region` returns the whole text for a headingless record, so only `search`'s first-match semantics keep it right).

    THE REVERT IS THE ONLY DESTRUCTIVE STEP IN THIS PLAN, so bound it: revert ONLY the E-01 hunk, restore it in the NEXT command, and note in the evidence that you did. Do NOT use `git stash` (shared checkout, it would move a co-worker's uncommitted work). A throwaway detached worktree at the pre-change commit (`git worktree add --detach .aw/tmp/ahq0mq-head <commit>`, `.aw/worktrees/`/`tmp/` are gitignored) is an equally acceptable and safer substitute.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste both diffs. The EXPECTED result is that both are EMPTY (measured at review: attention byte-identical, `check all` same 4 findings), so paste the `diff` commands with their empty output plus the two exit codes rather than describing them. Then paste the ONE internal change that does occur, as the positive proof the fix took effect at all: `len(list(check_engine._iter_type_files(repo, "research")))` before and after, which must rise by exactly one, with the newly-yielded path shown to be ebh1ap. Without that count, an empty diff is indistinguishable from a change that was never applied, which is the specific false-green this item must avoid. Explain any non-empty line; RE-DERIVE every number (the corpus moves).
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

WHAT A HUMAN IS APPROVING. Two readers in `check_engine` stop reading status lines below a record's metadata region, so a record that merely QUOTES a status is no longer read as asserting it. This is a CORRECTNESS-BY-CONSTRUCTION change with NO observable effect on today's tree, and that framing is the review's correction of the plan's original claim (PR-002): measured at review, `aw attention --format json` is byte-identical, `aw check all` reports the same 4 pre-existing findings, and the only change is internal (one more research file enters `_iter_type_files`, producing no finding). `aw attention` is untouched because it never calls `is_retired` and already classifies ebh1ap from its YAML front matter as `done`. So the value here is that a FUTURE record which quotes a status cannot be mis-hidden or mis-flagged, not any fix visible today. No plan's read status changes; measured, no plan differs at all.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if the E-03 diff shows a PLAN changing status or retirement, or ANY new `aw check` finding, stop and report before committing. Note the bar is tighter than the plan originally set it ("not attributable to ebh1ap"): measured at review, the expected diff is EMPTY on both surfaces and ebh1ap itself produces no finding, so there is no legitimate ebh1ap-attributable diff line to wave through. A non-empty diff means something the review did not predict.

FALSE-GREEN WARNING, the counterpart of that stop condition: because the expected diff is empty, an executor who never actually applied E-01 would produce evidence indistinguishable from success. That is why V-03 requires the `_iter_type_files(repo, "research")` count to rise by exactly one; it is the only positive proof in this plan that the change took effect.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); the `/tmp` baseline files are not committed. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `pyk78c` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`.
