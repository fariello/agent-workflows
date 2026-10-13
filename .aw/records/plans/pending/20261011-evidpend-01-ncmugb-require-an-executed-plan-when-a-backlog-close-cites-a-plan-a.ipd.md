# IPD: Require an executed plan when a backlog close cites a plan as SATISFIED evidence

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `7lfe87`: the SATISFIED arm of `check_engine.evaluate_blocking_close` accepts any citation that `check_engine.resolve_evidence_artifact` resolves, and that resolver checks only that the path is safe, inside the repo, exists, and sits under a records tree. It never reads a cited plan's disposition directory, so `aw backlog set done <item> --evidence <pending plan>` closes a release-blocking item by citing work that has not shipped, while the HANDOFF arm refuses the same plan with `the work has not shipped (carrier is not executed/implemented)`.
- Scope: In the backlog close predicate's SATISFIED arm only, refuse a citation that resolves to a PLAN (a path inside a plans tree) unless the plan is in an `executed` disposition directory (the top-level disposition under the plans root, read relative to the repo root; equivalent to `check_engine._carrier_is_executed`'s IPD rule for every in-repo plan, F-09). Non-plan records artifacts (reviews, releases, walkthroughs, research, specs, backlog) stay resolvable exactly as today. The shared `resolve_evidence_artifact` keeps its behavior (its other callers are out of scope, see Deferred); its docstring is corrected. Give the refusal a specific reason, add behavioral tests on both setter spellings and the at-rest checker, and update the release-gate prose and CHANGELOG.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_backlog_close_evidence_plan_disposition.py, AGENTS.md, .aw/records/backlog/README.md, CHANGELOG.md, DECISIONS.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 7lfe87
- Blocks-Release: next
- Set: evidpend
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ncmugb
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Reviewed at HEAD bd555fd74. Close-Evidence census corrected (52 gated done items: 48 executed plans, 4 walkthrough, 0 non-executed plans); helper disposition test made repo-relative (absolute 'executed' segment not containment-safe); at-rest case requires a dated history line and names the rule; refusal hints reworded and case (h) added; base suite run moved to E-01; gate itemized. Record: .aw/records/reviews/20261011-evidpend-01-ncmugb-require-an-executed-plan-when-a-backlog-close-cites-a-plan-a.review.md.
- 2026-10-12 to-review (aw set): authored from backlog 7lfe87 at HEAD 319da03a9; defect re-measured (pending-plan citation dry-run returns outcome clean, exit 0); resolver blast radius measured; follow-up bkprhk filed for the Carrier-Evidence caller

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the SATISFIED route agree with the HANDOFF route about what counts as shipped work: a plan cited as close evidence must be executed, so a release-blocking backlog item can no longer be closed `done` by citing a pending, draft, not-executed or superseded plan. Every other evidence artifact type keeps working, and so does the legitimate "closed by this executed plan" route.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: pin the defect with outcome tests

- [x] E-01 Create `tests/test_backlog_close_evidence_plan_disposition.py`, following the scratch-repo and paired-spelling pattern of `tests/test_backlog_positional_close_gate.py` (its `_setup_repo` writes a `planned` release record, its `_create_item` writes an item with `- Blocks-Release: next`). Write plan fixtures as real `.ipd.md` files with `- Id:` and `- Status:` lines in the named bucket. Cases, each asserting the exit code, the item's final directory, and (for the predicate cases) `verdict.legitimate` and `verdict.path`: (a) evidence = a plan in `plans/pending/` with `- Status: to-review`: REFUSED on `aw backlog set <id> --status done --evidence ...` AND on `aw backlog set done <id> --evidence ...` (rc 1, item not in `done/`); (b) same for a `draft` pending plan, a plan in `plans/not-executed/`, and a plan in `plans/superseded/` (predicate level is enough for these three, `evaluate_blocking_close(repo, item, "done", evidence=...)` returning `legitimate=False`); (c) `--dry-run` with a pending-plan citation refuses (rc 1), which is the exact measured reproduction; (d) evidence = a plan in `plans/executed/`: ACCEPTED on both spellings, `verdict.path == "SATISFIED"`, item in `done/`, and its `- Close-Evidence:` line written; (e) evidence = a plan under a sharded `plans/executed/YYYYMM/` directory and under the legacy `.agents/plans/executed/`: accepted; (f) evidence = a non-plan records artifact (a `.aw/records/reviews/*.review.md` and the release record): accepted, unchanged; (g) AT REST: an item already in `backlog/done/` whose `- Close-Evidence:` cites a pending plan, in a git-committed scratch repo whose `.aw/config/project.json` sets `{"cutovers": {"release_gate_at_rest": "<a date before the item>"}}` (the shape `test_evidence_satisfied_positional_close_clean_at_rest` uses), makes `check_engine.check_release_gate_consistency(repo, at_rest=True)` return a finding list containing rule `check.blocking-item-closed-without-gate` for that item, while the same item citing an executed plan returns `[]`; the item's `## Workflow history` must carry a dated line on or after the cutover (`_item_close_date` reads the newest history date and the at-rest arm only judges items closed on or after the cutover), so write the history line explicitly rather than relying on a default; (h) the refusal reason for case (a) names the cited path and the phrase `has not shipped`, and the item file is byte-identical before and after the refused call. Run the module BEFORE E-02 and record which cases fail; (a), (b), (c), (g-pending) and (h) must FAIL at HEAD and (d), (e), (f) and (g-executed) must pass.
  - Depends on: none
  - Also run the bare `python3 -m pytest` NOW, before E-02, and keep its summary line and sorted failing node ids (E-05 compares against it).
  - Expected outcome: a new test module whose refusal cases fail at HEAD (proving they detect the defect) and whose acceptance cases pass at HEAD (proving the fix does not need to change them).
  - Execution state: performed

### Task group 2: fix the predicate

- [x] E-02 In `agent_workflows/check_engine.py`, add a small helper (suggested name `_evidence_plan_unshipped(repo_root, evidence) -> bool`) that resolves the citation the same way `resolve_evidence_artifact` does (`(Path(repo_root).resolve() / evidence).resolve()`) and returns True iff the resolved path lies inside a plans tree AND its first path component under that plans root is not `executed`. Compute both RELATIVE TO THE RESOLVED REPO ROOT, never on the absolute path: take `rel = candidate.relative_to(repo_root).parts`, the plans tree is `rel[:3] == ('.aw', 'records', 'plans')` or `rel[:2] == ('.agents', 'plans')`, and the disposition is the next part (`executed` accepts, including sharded `executed/YYYYMM/` archives). This is deliberately stricter than `_carrier_is_executed`'s absolute-path `"executed" in p.parts` (which a repo cloned under any directory named `executed` would satisfy for every plan, measured at review: `'executed' in Path('/x/executed/repo/.aw/records/plans/pending/a.ipd.md').parts` is `True`) while agreeing with it on every in-repo plan. Apply the rule to every file under a plans tree regardless of suffix (`.ipd.md` or a legacy plain `.md` plan), and treat a non-file (a plans directory itself) as unshipped. In `evaluate_blocking_close`'s SATISFIED arm (the block beginning `# SATISFIED: a resolvable evidence artifact citation`), require `resolve_evidence_artifact(...)` AND `not _evidence_plan_unshipped(...)`. When the citation resolves but names an unshipped plan, do not fall through silently to the generic refusal: return, before the `if same_gate_carriers:` refusal and regardless of whether carriers exist, a `CloseVerdict(False, "error", ...)` whose reason names the cited path and says the cited plan has not shipped (is not in `executed/`), with the same three fixes the existing final refusal offers plus "cite the plan once it is executed". Change the existing `--evidence <in-tree artifact path>` suggestion text in BOTH existing refusals to say `<in-tree artifact path; a cited plan must be executed>` so the hint no longer advertises the refused route. The runner path is unaffected: `runner_shared.evaluate_backlog_close` cites a carrier only after every IPD carrier is `executed` (overridden to its lane `executed/` path for an isolated turn, `_cited`), and `close_backlog_item` passes `--gate-dir`/`--lane-carrier-*` so HANDOFF decides first (F-07). Do NOT change `resolve_evidence_artifact`'s return value, the arm order (DE-GATED, HANDOFF, SATISFIED, refusals), the HANDOFF arm, or the lane-carrier override. Correct `resolve_evidence_artifact`'s docstring, which today says the accepted value is "an executed IPD" although the function never checks disposition: state that it checks safety, containment, existence and records-tree location only, and that the backlog close predicate adds the executed-plan rule (plan `ncmugb`) while `specs._evidence_resolvable` adds its own stricter executed-IPD rule.
  - Depends on: E-01
  - Expected outcome: every E-01 case passes; `resolve_evidence_artifact` returns the same value as before for every input (the pending-plan path still returns True from it).
  - Execution state: performed

### Task group 3: documentation and the recorded decision

- [x] E-03 Update the prose that describes the SATISFIED route so it states the new rule: in `AGENTS.md`'s repo-local `## Release gates (Blocks-Release)` section, change `(2) SATISFIED, a resolvable in-tree artifact citation` so it says a cited plan must be executed (a pending, draft, not-executed or superseded plan is refused) while other records artifacts are accepted; in `.aw/records/backlog/README.md`, amend item 1 of the "real controls on backlog transitions" list (`which requires an executed carrier handoff, satisfied evidence citation, or explicit de-gating`) to the same effect; add one `- Fixed:` line under the `## 2.0.0 (pending)` heading of `CHANGELOG.md` saying that closing a release-blocking backlog item with `--evidence` now refuses a cited plan that has not been executed, on both setter spellings. The CHANGELOG line is user-facing prose: write it with no em or en dashes. Confirm first that `AGENTS.md` line is repo-local (below `<!-- /aw:block -->`) and that `engine.py` does not carry the same sentence (measured at authoring: `rg "SATISFIED, a resolvable in-tree artifact citation"` matches only `AGENTS.md`).
  - Depends on: E-02
  - Expected outcome: the three documents describe the rule the code now enforces; no managed-block text changes.
  - Execution state: performed

- [x] E-04 Append a `DECISIONS.md` entry with the next free `D<n>` (`D162` is the last at authoring HEAD; re-check at execution) in the file's `Context` / `Decision` / `Rejected` / `Applied` shape, recording the choice the backlog item says "needs recording": (1) the executed-plan rule lives in the backlog close predicate's SATISFIED arm, not in the shared resolver, because the resolver's other caller `evaluate_carrier_obligation` would otherwise turn executed plan `wyk11f`'s `Carrier-Evidence:` row (citing pending plan `tf4jz5`, which exists) into a new error on a record that may not be edited (F-05), and that question is carried by `bkprhk`; (2) REJECTED: forbidding plan citations outright, which would remove the legitimate "closed by this executed plan" route the item explicitly protects; (3) REJECTED: reading the plan's `- Status:` field, because a plan stays in `pending/` through draft/to-review/reviewed/approved and only the disposition directory says executed (`runner_shared.plan_bucket` docstring, `_carrier_is_executed` docstring); (4) a `reusable/` plan is NOT accepted, because a standing plan does not prove a particular item shipped (OQ-01); (5) a cited SPEC is unchanged here and is part of `bkprhk`. Cite `ncmugb`, `7lfe87`, `bkprhk`.
  - Depends on: E-03
  - Expected outcome: one new, uniquely numbered `DECISIONS.md` entry carrying the five points and the three citations.
  - Execution state: performed

### Task group 4: prove no regression on the live corpus and the suite

- [x] E-05 Measure blast radius after E-02: run `aw check release-gates --agent` and `aw check --agent` and compare the per-rule diagnostic counts to the authoring baseline in F-06 (release-gates: `conforms`, 0 findings; full check: 30 findings, of which `check.blocking-item-closed-without-gate` 0 and `check.ipd-uncarried-obligation` 3). Any NEW `check.blocking-item-closed-without-gate` or `check.ipd-uncarried-obligation` finding is a regression to investigate and explain before continuing (the corpus has 52 gated `Close-Evidence:` items, 48 citing existing `executed/` plans and 4 a walkthrough, none a non-executed plan, so zero new findings is expected; re-derive this census at execution and paste it). Then run the full suite BARE (`python3 -m pytest`) before E-02 and after E-04, and compare the failing node-id sets by name.
  - Depends on: E-04
  - Expected outcome: no new release-gate or carrier findings; the post-change failing set is a subset of the pre-change failing set, and the pass count rises by the tests E-01 added.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- One shared predicate backs both setter spellings, the `aw check` release-gate rules and the opt-in hook (`AGENTS.md` "Close-legitimacy rule"): `status_set` calls `check_engine.evaluate_blocking_close` on both the `--status` and positional paths, and `set_records.close_on_answer` calls it too. Fixing the predicate therefore fixes every caller; no setter-side change is needed.
- A plan's disposition lives in its DIRECTORY, not its `- Status:` field (`runner_shared.plan_bucket` docstring: "A BUCKET IS A DIRECTORY; READINESS IS A FIELD"). `check_engine._carrier_is_executed` already encodes the IPD rule as `"executed" in p.parts`, matching sharded archives.
- Tests must exercise behavior through the CLI and the predicate, never read source (AGENTS.md, GUIDING_PRINCIPLES P16). The suite runs BARE as `python3 -m pytest`.
- `CHANGELOG.md` and `AGENTS.md` prose authored for users must contain no em or en dashes; plans, commit messages and code comments are exempt.

## Findings

| # | Finding | Evidence (measured at HEAD `319da03a9`) | Consequence |
|---|---|---|---|
| F-01 | The defect reproduces at authoring HEAD. | `aw backlog set done 7lfe87 --evidence .aw/records/plans/pending/20261011-evidpend-01-ncmugb-...ipd.md --dry-run --agent` printed `"outcome":"clean","exit":0,...,"findings":0` with this very plan, at that point `- Status: draft`, as the citation. | The fix is still needed; E-01(c) is this measurement as a test. |
| F-02 | `resolve_evidence_artifact` never reads disposition. | Its body tests `is_safe_descriptive`, containment via `relative_to`, `exists()`, and `".aw/records/" in norm or "/.agents/" in norm`. Direct call on a pending plan path returned `True`. Its docstring nonetheless says "an executed IPD, a records file, or another committed doc". | E-02 corrects the docstring and adds the rule at the predicate. |
| F-03 | HANDOFF already requires an executed plan. | `evaluate_blocking_close` HANDOFF arm: `all(_carrier_eval(_c) for _c in same_gate_carriers)` with `_carrier_is_executed` returning `"executed" in p.parts` for an `.ipd.md`; its refusal reason reads `the work has not shipped (carrier is not executed/implemented)`. | The two routes disagree; E-02 aligns SATISFIED with HANDOFF's IPD rule. |
| F-04 | The resolver has three callers. | `rg "resolve_evidence_artifact\("`: `check_engine.evaluate_blocking_close` (SATISFIED arm), `check_engine.evaluate_carrier_obligation` (`Carrier-Evidence:`), `specs._evidence_resolvable` (which then requires an `executed` plans path itself). | Tightening the shared resolver would change the carrier rule too; F-05 shows that has a cost. |
| F-05 | Tightening the shared resolver would create a new error on an immutable record. | Executed plan `20261002-mt6j1p-01-wyk11f-...ipd.md` carries `- Carrier-Evidence: .aw/records/plans/pending/20261001-tf4jz5-01-j7dsci-...ipd.md`, and that pending file EXISTS, so it resolves today. Seven other `Carrier-Evidence:` rows cite `pending/` paths that no longer exist and fail already. | Scope stays in the backlog close predicate; filed `bkprhk` for the carrier and spec question. |
| F-06 | Baseline corpus state. | `aw check release-gates --agent`: `"outcome":"conforms"`, `"findings":0`. `aw check --agent`: 30 findings; per rule `check.lifecycle-transition-unvalidated` 11, `check.ipd-uncarried-obligation` 3, `check.orchestrator-not-review-ready` 3, `check.gate-ref-discharged` 3, `check.ipd-carrier-finished-unverified` 2, `check.ipd-carrier-ungated` 2, `check.name-nonconformant` 2, one each of `spec-criteria-uncovered`, `plan-spec-link-missing`, `graduated-to-dangling`, `system-layout-missing`. Close-Evidence corpus RE-MEASURED at review (HEAD `bd555fd74`): 52 `done/` items carry both `- Blocks-Release:` and `- Close-Evidence:`; 48 cite a `.aw/records/plans/executed/...ipd.md` path (all existing), 4 cite the walkthrough `.aw/records/walkthroughs/20261009-runfix1009-01-04qifi-...walkthrough.md`; zero cite a non-executed plan. (The authoring count of 4 was wrong.) | The at-rest re-evaluation of `Close-Evidence:` (plan `f7igdu` E-04) should produce zero new findings; E-05 checks it. |
| F-07 | The runner's own close is unaffected. | `runner_shared.close_backlog_item` passes the carrier path as `--evidence`; for an isolated turn, plan `4nbvfr` (qkl8fs) routes the decision through HANDOFF with a verified lane-carrier override, which is evaluated BEFORE SATISFIED, and that plan's F-04 names the pending-path citation as a false citation that "would work". Non-isolated and post-merge, the cited path is the plan's `executed/` path. | The tightening closes the F-04 trap without touching the runner. E-05's full suite run covers the runner tests. |
| F-09 | The absolute-path `executed` segment test is not containment-safe. | Review probe: `'executed' in Path('/x/executed/repo/.aw/records/plans/pending/a-ab12cd-x.ipd.md').parts` -> `True`. E-02 therefore tests the disposition relative to the repo root. | E-02 helper is root-relative. |
| F-08 | The existing SATISFIED tests cite non-plan artifacts. | `tests/test_backlog_handoff_close.py` case 6 cites the release record with a pending From-Backlog plan present; `tests/test_backlog_positional_close_gate.py` cites `.aw/records/reviews/20260901-test.review.md`. | Both stay green under E-02 (non-plan artifacts unchanged), which E-05's suite run confirms. |

## Proposed changes (ordered, validatable)

1. E-01: add outcome tests that fail at HEAD for pending/draft/not-executed/superseded plan citations and pass for executed plans and non-plan artifacts, on both setter spellings, dry-run, and the at-rest checker.
2. E-02: refuse an unshipped-plan citation in `evaluate_blocking_close`'s SATISFIED arm with a specific reason; correct the resolver docstring.
3. E-03: update `AGENTS.md` (repo-local section), the backlog README, and `CHANGELOG.md`.
4. E-04: record the decision in `DECISIONS.md`.
5. E-05: prove no new corpus findings and no suite regressions.

## Deferred / out of scope (with reason)

- Applying the executed-plan rule to `Carrier-Evidence:` in `check_engine.evaluate_carrier_obligation`, and requiring `implemented` for a cited spec. Out of scope because a `Carrier-Evidence:` row does not drop a release gate, and because tightening it would raise a new error on executed plan `wyk11f`, which may not be edited (F-05), so it needs a grandfathering decision of its own.
  - Carrier: bkprhk
- Changing `specs._evidence_resolvable`. It already requires an executed plans path and is unaffected.
  - Carrier-Declined: no work is owed; the specs predicate is already stricter than the rule this plan adds.
- Repairing the seven `Carrier-Evidence:` rows that cite vanished `pending/` paths (F-05). They already fail resolution today and are unrelated to this plan's change.
  - Carrier-Declined: not caused or changed by this plan; the existing `check.ipd-uncarried-obligation` rule already reports any that are live findings.

## Scope check

- Over-scope: none. `check_engine.py` (E-02), the new test module (E-01), `AGENTS.md` repo-local section, backlog README and `CHANGELOG.md` (E-03), `DECISIONS.md` (E-04). E-05 changes no file.
- Under-scope: none known. The item asks for (1) a plan citation to require a terminal executed disposition, (2) non-plan artifacts to stay resolvable, (3) plan citations not to be forbidden outright, and (4) the choice to be recorded: E-02 covers (1)-(3), E-04 covers (4), E-01 proves (1)-(3).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_backlog_close_evidence_plan_disposition.py -v` before E-02 (the refusal cases fail) and after E-02 (all pass), both pasted.
- `python3 -m pytest -o addopts="" tests/test_backlog_handoff_close.py tests/test_backlog_positional_close_gate.py tests/test_specs_evidence_gate_parity.py tests/test_check_engine_release_gate.py tests/test_carrier_reverse_lookup.py` after E-02, pasted.
- The bare `python3 -m pytest` before E-02 and after E-04, summary lines pasted, failing node-id sets compared by name. Pre-existing failures are not this plan's to fix.
- `aw check release-gates --agent` and `aw check --agent` per-rule counts after E-02, compared to F-06.
- The F-01 reproduction re-run after E-02 with a pending-plan citation in a scratch repo (or `--dry-run` on a real gated item), showing a nonzero exit and the new reason text.

## Spec / documentation sync

- No `.spec.md` is amended. Spec `llbr2b` (to-review) and draft spec `pqsx96` describe SATISFIED as "a resolvable `--evidence` citation" / "resolvable in-tree evidence"; that wording stays true, because a refused pending plan is now simply not satisfying evidence, so neither contract is falsified.
- `AGENTS.md` (repo-local release-gates section), `.aw/records/backlog/README.md`, `CHANGELOG.md` and `DECISIONS.md` are updated in E-03 and E-04.

## Open questions

### OQ-01: Should a plan in `reusable/` count as shipped evidence?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED NO from repository evidence. `_carrier_is_executed` accepts only an `executed` segment for an IPD carrier, and the item asks the two routes to agree. A reusable plan is a standing recipe that runs repeatedly (`AGENTS.md` "Reusable Runs"), so its existence does not prove that the work for a particular item shipped. Recorded in E-04 point (4).

### OQ-02: Fix the shared resolver or the backlog close predicate?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: the predicate. The item frames the defect as the SATISFIED route closing a release-blocking item, and the fix shape it proposes is about that route. F-05 shows that changing the shared resolver would raise a new error on an immutable executed plan through a different caller. The carrier question is filed as `bkprhk`. Recorded in E-04 point (1).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_backlog_close_evidence_plan_disposition.py -v` output from BEFORE E-02, showing every refusal case (a), (b), (c), (h) and the pending half of (g) FAILING and every acceptance case (d), (e), (f) and the executed half of (g) PASSING, with the test names visible.
  - Observed evidence:
    `python3 -m pytest -o addopts="" tests/test_backlog_close_evidence_plan_disposition.py -v --tb=no` before E-02:
    ```
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_b_superseded_plan_refused_predicate FAILED [  6%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_f_release_artifact_accepted PASSED [ 13%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_a_pending_plan_refused_status_spelling FAILED [ 20%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_c_dry_run_pending_plan_refused FAILED [ 26%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_g_pending_plan_at_rest_flagged FAILED [ 33%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_g_executed_plan_at_rest_clean PASSED [ 40%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_e_legacy_agents_executed_plan_accepted PASSED [ 46%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_d_executed_plan_accepted_positional_spelling PASSED [ 53%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_a_pending_plan_refused_positional_spelling FAILED [ 60%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_e_sharded_executed_plan_accepted PASSED [ 66%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_f_review_artifact_accepted PASSED [ 73%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_b_not_executed_plan_refused_predicate FAILED [ 80%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_h_refusal_reason_names_path_and_unshipped_preserves_bytes FAILED [ 86%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_b_draft_pending_plan_refused_predicate FAILED [ 93%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_d_executed_plan_accepted_status_spelling PASSED [100%]
    ========================= 8 failed, 7 passed in 2.15s ==========================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (a) the same module's pasted `-v` output AFTER E-02 with every case passing; (b) the pasted run of the related modules listed under Required tests, passing; (c) a pasted `python3 -c` showing `check_engine.resolve_evidence_artifact(<root>, <pending plan path>)` still returns `True` (resolver unchanged) while `evaluate_blocking_close` on a gated item with that citation returns `legitimate=False` with the new reason text; (d) the `git diff` hunk of `evaluate_blocking_close` showing arm order DE-GATED, HANDOFF, SATISFIED is unchanged, and the corrected `resolve_evidence_artifact` docstring quoted.
  - Observed evidence:
    (a) Post E-02 module run:
    ```
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_c_dry_run_pending_plan_refused PASSED [  6%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_h_refusal_reason_names_path_and_unshipped_preserves_bytes PASSED [ 13%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_g_executed_plan_at_rest_clean PASSED [ 20%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_f_review_artifact_accepted PASSED [ 26%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_b_not_executed_plan_refused_predicate PASSED [ 33%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_b_draft_pending_plan_refused_predicate PASSED [ 40%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_g_pending_plan_at_rest_flagged PASSED [ 46%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_f_release_artifact_accepted PASSED [ 53%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_b_superseded_plan_refused_predicate PASSED [ 60%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_d_executed_plan_accepted_positional_spelling PASSED [ 66%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_a_pending_plan_refused_status_spelling PASSED [ 73%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_e_legacy_agents_executed_plan_accepted PASSED [ 80%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_a_pending_plan_refused_positional_spelling PASSED [ 86%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_e_sharded_executed_plan_accepted PASSED [ 93%]
    tests/test_backlog_close_evidence_plan_disposition.py::TestBacklogCloseEvidencePlanDisposition::test_case_d_executed_plan_accepted_status_spelling PASSED [100%]
    ============================== 15 passed in 3.56s ==============================
    ```
    (b) Related modules run:
    `python3 -m pytest -o addopts="" tests/test_backlog_handoff_close.py tests/test_backlog_positional_close_gate.py tests/test_specs_evidence_gate_parity.py tests/test_check_engine_release_gate.py tests/test_carrier_reverse_lookup.py`
    ```
    ============================= 127 passed in 31.76s =============================
    ```
    (c) python3 -c verification:
    ```
    resolve_evidence_artifact: True
    verdict.legitimate: False
    verdict.severity: error
    verdict.reason: cited evidence '.aw/records/plans/pending/20261011-evidpend-01-ncmugb-require-an-executed-plan-when-a-backlog-close-cites-a-plan-a.ipd.md' names a plan that has not shipped (is not in executed/)
    verdict.fixes: ('cite the plan once it is executed', 'hand the gate to a plan: add `- From-Backlog: <this id6>` (and the same `- Blocks-Release`) to a plan via `aw ipd set ... --from-backlog <id6>`', 'cite satisfying evidence: `aw backlog set done <item> --evidence <in-tree artifact path; a cited plan must be executed>`', 'explicitly release the gate first: `aw backlog set done <item> --blocks-release -`')
    ```
    (d) Arm order and docstring diff:
    ```diff
    --- a/agent_workflows/check_engine.py
    +++ b/agent_workflows/check_engine.py
    @@ -4967,11 +4967,11 @@ _PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2}


     def resolve_evidence_artifact(repo_root: Path, evidence: str) -> bool:
    -    """Shared evidence resolver (bklggrad orb9zb E-03): a resolvable close-evidence citation is a
    -    SAFE, in-tree, existing artifact path under the repo's records tree (an executed IPD, a records
    -    file, or another committed doc). Generalizes the specs `_evidence_resolvable` (which is
    -    executed-IPD-only) so a non-IPD backlog item (README/research/prompt/check work) can be closed
    -    `done` with a cited artifact. Path-traversal-safe: the resolved path must stay inside the repo.
    +    """Shared evidence resolver (bklggrad orb9zb E-03): checks safety, containment,
    +    existence, and records-tree location only for a close-evidence citation.
    +    The backlog close predicate adds the executed-plan rule (plan ncmugb) while
    +    specs._evidence_resolvable adds its own stricter executed-IPD rule.
    +    Path-traversal-safe: the resolved path must stay inside the repo.
    ```
    And arm order in `evaluate_blocking_close` remains DE-GATED -> HANDOFF -> SATISFIED -> refusals.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the changed sentences from `AGENTS.md`, `.aw/records/backlog/README.md` and the new `CHANGELOG.md` line quoted; pasted `git diff -U0 AGENTS.md` showing every changed line lies after the `<!-- /aw:block -->` marker; pasted `git diff -U0 CHANGELOG.md AGENTS.md .aw/records/backlog/README.md | grep '^+' | rg -c "[\u2013\u2014]"` printing nothing (or 0), so no added user-facing line carries an em or en dash.
  - Observed evidence:
    Changed sentences quoted:
    - `AGENTS.md`: `a multi-carrier item stays `graduated` until the last carrier executes; (2) SATISFIED, a resolvable in-tree artifact citation `aw backlog set done <item> --evidence <path>`, where a cited plan must be executed (a pending, draft, not-executed or superseded plan is refused) while other records artifacts are accepted; (3) DE-GATED, clear the gate first (or in the same call)`
    - `.aw/records/backlog/README.md`: `1. The release-gate close predicate on `->done` (`check_engine.evaluate_blocking_close`), which requires an executed carrier handoff, satisfied evidence citation (where a cited plan must be executed; pending, draft, not-executed or superseded plans are refused), or explicit de-gating.`
    - `CHANGELOG.md`: `- Fixed: closing a release-blocking backlog item with --evidence now refuses a cited plan that has not been executed, on both setter spellings.`
    `git diff -U0 AGENTS.md`:
    ```diff
    @@ -234 +234 @@ a multi-carrier item stays `graduated` until the last carrier executes; (2) SATI
    -`aw backlog set done <item> --evidence <path>`; (3) DE-GATED, clear the gate first (or in the same call)
    +`aw backlog set done <item> --evidence <path>`, where a cited plan must be executed (a pending, draft, not-executed or superseded plan is refused) while other records artifacts are accepted; (3) DE-GATED, clear the gate first (or in the same call)
    ```
    (Line 234 is below line 125 `<!-- /aw:block -->`).
    Dash check command output:
    `git diff -U0 CHANGELOG.md AGENTS.md .aw/records/backlog/README.md | grep '^+' | rg "[\u2013\u2014]"` produced zero matches (No em or en dashes found).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the new `DECISIONS.md` entry quoted in full, plus pasted `grep -c "^### D<n>\." DECISIONS.md` printing `1` for its number, showing the five points and the `ncmugb` / `7lfe87` / `bkprhk` citations.
  - Observed evidence:
    `DECISIONS.md` entry D165 quoted in full:
    ```markdown
    ### D165. Require an executed plan when a backlog close cites a plan as SATISFIED evidence

    - **Context:** The SATISFIED arm of `check_engine.evaluate_blocking_close` accepted any citation that `check_engine.resolve_evidence_artifact` resolved, and that resolver checked only that the path was safe, inside the repository, existed, and sat under a records tree. It did not check the cited plan's disposition directory, allowing a release-blocking backlog item to be closed `done` by citing a pending, draft, not-executed, or superseded plan, while the HANDOFF arm required all From-Backlog carriers to be executed or implemented.
    - **Decision:** In the backlog close predicate's SATISFIED arm only, refuse a citation resolving to a plan unless the plan is in an `executed` disposition directory relative to the repository root (supporting sharded archives `executed/YYYYMM/` and legacy `.agents/plans/executed/`).
      1. *Location in predicate, not resolver:* The executed-plan rule lives in `evaluate_blocking_close`'s SATISFIED arm rather than in the shared resolver `resolve_evidence_artifact`, because tightening the shared resolver would turn executed plan `wyk11f`'s `Carrier-Evidence:` row (citing pending plan `tf4jz5`, which exists) into a new error on an immutable record that may not be edited (F-05); that question is carried by `bkprhk`.
      2. *Standing plans:* A `reusable/` plan is NOT accepted, because a standing plan is a reusable recipe that runs repeatedly and does not prove that work for a particular backlog item shipped (OQ-01).
      3. *Cited specs:* A cited spec is unchanged here and remains part of `bkprhk`.
      Two alternatives were rejected:
      1. *Forbidding plan citations outright:* Rejected because it would remove the legitimate "closed by this executed plan" route protected by backlog item `7lfe87`.
      2. *Reading the plan's `- Status:` field:* Rejected because a plan stays in `pending/` through `draft`, `to-review`, `reviewed`, and `approved`, and only the disposition directory reflects execution (`runner_shared.plan_bucket` docstring, `_carrier_is_executed`).
    - **Applied:** `agent_workflows/check_engine.py` (`_evidence_plan_unshipped`, `resolve_evidence_artifact`, `evaluate_blocking_close`); `tests/test_backlog_close_evidence_plan_disposition.py`; `AGENTS.md`; `.aw/records/backlog/README.md`; `CHANGELOG.md`; `DECISIONS.md` (this entry). Executed per IPD `ncmugb` (Set `evidpend`, Order 01, backlog `7lfe87`, follow-up `bkprhk`).
    ```
    `grep -c "^### D165\." DECISIONS.md` printed `1`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: (a) the pasted re-derived Close-Evidence census (gated `done/` items, how many cite `executed/` plans, non-executed plans, non-plan artifacts) and pasted per-rule counts from `aw check release-gates --agent` and `aw check --agent` after E-02, set beside F-06, with zero new `check.blocking-item-closed-without-gate` and `check.ipd-uncarried-obligation` findings (any difference explained by name); (b) the bare `python3 -m pytest` summary lines from before E-02 and after E-04, with the failing node-id sets listed and compared; (c) the F-01 reproduction re-run showing a nonzero exit and the new refusal reason.
  - Observed evidence:
    (a) Re-derived Close-Evidence census:
    - Total gated items with Close-Evidence: 52
    - Citing executed plans: 48
    - Citing non-executed plans: 0
    - Citing non-plan artifacts: 4 (all citing walkthrough `20261009-runfix1009-01-04qifi-run-failure-recovery-2026-10-09.walkthrough.md`)
    `aw check release-gates --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"release-gates","findings":0,"evidence":["inventory","rules"],"next":"aw releases list"}`
    `aw check --agent`:
    `check.blocking-item-closed-without-gate`: 0 (matches F-06 baseline 0)
    `check.ipd-uncarried-obligation`: 0 (baseline was 3; down to 0)
    No new findings in either rule.
    (b) Bare `python3 -m pytest` comparison:
    - Pre E-02 baseline: `8114 passed, 4 skipped, 18 xfailed, 3 warnings in 1032.05s (0:17:12)` (0 failed node-ids)
    - Post E-04 suite: `1 failed, 8128 passed, 4 skipped, 18 xfailed, 3 warnings in 1025.06s (0:17:05)`
      The single failure was `test_the_verbs_write_nothing_to_the_repository` in `tests/test_host_capability_extension.py`, caused by global monkeypatching of `builtins.open` capturing concurrent `/tmp/.../completion-notice.json` writes from another xdist worker. When run in isolation, the test passed immediately (`1 passed in 2.50s`), and all 46 tests in `tests/test_host_capability_extension.py` passed (`46 passed in 3.92s`). The 15 new tests in `tests/test_backlog_close_evidence_plan_disposition.py` all passed.
    (c) F-01 reproduction re-run:
    `python3 -m agent_workflows.cli backlog set done 7lfe87 --evidence .aw/records/plans/pending/20261011-evidpend-01-ncmugb-require-an-executed-plan-when-a-backlog-close-cites-a-plan-a.ipd.md --dry-run`
    Exited with code 1 and printed:
    ```
    aw backlog set: refused: cited evidence '.aw/records/plans/pending/20261011-evidpend-01-ncmugb-require-an-executed-plan-when-a-backlog-close-cites-a-plan-a.ipd.md' names a plan that has not shipped (is not in executed/).
      - cite the plan once it is executed
      - hand the gate to a plan: add `- From-Backlog: <this id6>` (and the same `- Blocks-Release`) to a plan via `aw ipd set ... --from-backlog <id6>`
      - cite satisfying evidence: `aw backlog set done <item> --evidence <in-tree artifact path; a cited plan must be executed>`
      - explicitly release the gate first: `aw backlog set done <item> --blocks-release -`
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This is a release-gate tightening on a shared predicate, so the reviewer should check three things: that the SATISFIED arm is the right place (OQ-02, F-04, F-05), that non-plan artifacts and the runner's close path are genuinely unaffected (F-07, F-08), and that the at-rest checker produces no new findings on the live corpus (F-06, E-05).

Execution contract: OQ-01 and OQ-02 are resolved; none remain open. Scope fence (a declaration, not a stop rule): only the `Scope-Paths` files are expected to change; an out-of-scope edit that proves necessary is made and justified at finalize with `--scope-reason` (and `--scope-ack` for a declared path left unmodified). Commit only the `Scope-Paths` files, through `aw commit ncmugb -- <paths>`, never `git add -A`, never push. Edit only the repo-local `AGENTS.md` release-gates section (below `<!-- /aw:block -->`), never the managed block. This is a shared checkout: verify the staged set with `git diff --cached --name-only` before committing. Paste the actual runner output for every test claim. Lifecycle: under `aw oc run` / `aw agy run` the runner performs finalize and the lifecycle move; by hand, run `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms; never hand-`git mv` or hand-edit `- Status:`. Do not set backlog `7lfe87` `done` from this plan (the runner's HANDOFF close does that once this plan executes) and do not clear its `Blocks-Release`.
