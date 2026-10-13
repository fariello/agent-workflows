# IPD: Make the readiness-invariant tests' plan fixture hermetic so a demoted live plan cannot break them

- Date: 2026-10-12
- Kind: child
- Concern: `tests/test_readiness_absence_invariant.py` properties 2, 3 and 4 run in the DEFAULT (fast) suite but take their subject plan from the LIVE `.aw/records/plans/pending/` tree, so whichever pending plan sorts first and passes a too-weak filter decides whether three non-`livecorpus` tests pass.
- Scope: Replace the live-corpus subject selection used by properties 2-4 with the module's existing synthetic plan, keep property 1 (the genuine live-corpus partition, already marked `livecorpus`) unchanged, and update the module docstring to match.
- Scope-Paths: tests/test_readiness_absence_invariant.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 110dg8
- Blocks-Release: next
- Set: 110dg8
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: rrydjy
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002 fixed.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog `110dg8` in an isolated lane at HEAD `2d77c00ee`. The defect reproduced in a scratch tree (F-03) and is LATENT on the live corpus right now (F-04): the selector today picks `o58r3r`, which passes, but the 40th live candidate `wa64wz` already has the failing shape. Fix chosen: hermetic synthetic subject for properties 2-4 (F-06), not a tighter filter (F-07).
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make properties 2, 3 and 4 of the readiness absence invariant test their predicates against a fixed, in-module synthetic plan, so the default suite's result no longer depends on which plans happen to sit in `.aw/records/plans/pending/` or how their history was written, while property 1 keeps asserting the real corpus partition under the `livecorpus` marker.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline and reproduction

- [x] E-01 Capture the baseline: run `python3 -m pytest tests/test_readiness_absence_invariant.py -o addopts="" -m ""` and the bare `python3 -m pytest` at the executing HEAD before any edit, recording the per-test result of this file and the bare run's FAILING-NODE-ID SET. Then reproduce the defect: write an UNTRACKED scratch plan into `.aw/records/plans/pending/` named so it sorts first (`00000000-zzrepro-01-zzz000-demoted.ipd.md`), built from the module's `_SYNTHETIC_PENDING_PLAN` with `- Status: draft`, `- Id: zzz000`, and a history of `- 2026-08-06 draft (aw set): demoted approved -> draft: APPROVAL WITHDRAWN: returned to authoring` above `- 2026-08-05 approved (maintainer): APPROVE for execution` above the original `created.` line (the exact shape measured in F-03). Run this file again and record that `test_linter_refuses_backfilled_readiness_field_with_m107` FAILS with `Expected backfilled text to produce error disposition, got conforming`. Leave the scratch file in place for E-03's re-run.
  - Depends on: none
  - Expected outcome: a recorded green baseline for this file, a recorded bare-suite failing-node set, and a recorded red run of property 2 caused only by the planted untracked plan.
  - Execution state: performed

### Task group 2: Hermetic subject

- [x] E-02 In `tests/test_readiness_absence_invariant.py`, make `get_field_absent_pending_plan_fixture` return the synthetic subject (`"20260803-sample-01-abc123-sample.ipd.md"`, `_SYNTHETIC_PENDING_PLAN`) unconditionally, taking no repository argument, and delete `find_field_absent_pending_plan` together with its now-unused live-tree scan. Update the three callers (properties 2, 3 and 4) to the new signature. Do NOT change any assertion, the synthetic plan's text, `check_corpus_partition`, `get_tracked_or_all_plans`, property 1, or `test_fallback_arm_forgery_shapes_and_surviving_fallback`. Amend the module docstring's property-2 line to say the backfill is inserted onto the module's synthetic field-absent pending plan (not a live one) and add one sentence stating that only property 1 reads the live corpus, which is why only it carries `livecorpus`. Remove an import only if it becomes unused (`re` and `Optional` remain used elsewhere in the module; check before removing).
  - Depends on: E-01
  - Expected outcome: properties 2-4 no longer read `.aw/records/plans/pending/`; the module's collected node-id set is identical to E-01's baseline set (re-derived at execution, not a fixed count); no assertion text changed.
  - Execution state: performed

### Task group 3: Prove the fix

- [x] E-03 With E-01's untracked scratch plan STILL planted, re-run `python3 -m pytest tests/test_readiness_absence_invariant.py -o addopts="" -m "" -v` and record that every test except possibly property 1 passes (property 1 must also pass, since the scratch plan carries no `- Readiness:`). Then delete the scratch plan, confirm `git status --short .aw/records/plans/` shows nothing from this plan, and run the bare `python3 -m pytest`, comparing its failing-node-id set with E-01's. Finally run `aw ipd lint --phase pre-transition` on this plan.
  - Depends on: E-02
  - Expected outcome: the planted demoted plan no longer turns any test red; the scratch file is gone; the bare suite introduces no new failing node id; the plan lints conforming.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `AGENTS.md` repository development contract: run the suite BARE as `python3 -m pytest`; use `-o addopts=""` for per-test counts on a narrowed run; never `-n0`, an extra `-q`, or `-p no:randomly`.
- `pyproject.toml` `[tool.pytest.ini_options]` `markers` defines `livecorpus` as a test that "asserts a property over EVERY artifact in this repository's own .aw/records/ tree, so ANY agent writing a plan can turn it red", deselected by default because a red default-suite test blocks every concurrent lane's integration. Properties 2-4 are NOT marked `livecorpus` yet read the live tree, which is the inconsistency this plan removes.
- `GUIDING_PRINCIPLES.md` P16: tests assert behavior, never read production source; and "Never weaken an assertion so it passes everywhere". This plan changes the SUBJECT, not any assertion, so the predicates are exercised exactly as hard as before.
- Origin of the live selection: executed plan `fx5op3` (`20260929-rdyabsent-01-fx5op3-...`) E-03 specified property 2 as "taking a real field-absent pending plan". `l56tyz` later added the synthetic fallback `_SYNTHETIC_PENDING_PLAN` that this plan promotes to the only subject.
- Demotion strips `- Readiness:` and writes `demoted <from> -> <to>` history lines (`status_set.apply_status_change`, executed plan `26m1nb` E-05), so demoted plans are a routine, growing population in `pending/`.

## Findings

| ID | Finding | Evidence | Consequence |
|---|---|---|---|
| F-01 | `find_field_absent_pending_plan` picks the first `pending/*.ipd.md` (sorted) that has no `- Readiness:` and no line matching `^\s*-\s*.*(?:/plan-review|reviewed\b).*$`. | `tests/test_readiness_absence_invariant.find_field_absent_pending_plan` | The filter only knows two review spellings. |
| F-02 | Property 2 asserts that inserting `- Readiness: go-pending-approval` makes `ipd_lint.lint_text` return `error` with one `IPD-M107`. `ipd_lint.check_readiness_attestation` stays SILENT whenever `ipd_lint._REVIEW_EVIDENCE_RE` (`/?plan-review(-long)?`, `APPROVE`, `NO-GO`, `REJECT`, case-insensitive) matches anywhere in the history. | `ipd_lint._REVIEW_EVIDENCE_RE`, `ipd_lint.check_readiness_attestation` | Any picked plan whose history says `APPROVE`/`REJECT`/`NO-GO` without `/plan-review` or `reviewed` makes property 2 fail. The two filters disagree. |
| F-03 | REPRODUCED the backlog's shape in a scratch tree: a `draft` plan with history `demoted approved -> draft: APPROVAL WITHDRAWN` above `approved (maintainer): APPROVE for execution`. The finder picks it; property 2 fails `Expected backfilled text to produce error disposition, got conforming`; properties 3 and 4 pass. | In-process run at `2d77c00ee` with `REPO_ROOT` pointed at the scratch tree: `P2 FAIL`, `P3 ok`, `P4 ok`. | Confirms the backlog summary: a plan demoted from `approved` breaks the default suite. |
| F-04 | The defect is LATENT on the live tree. Today the finder picks `o58r3r` and the file passes (`10 passed`). Of the 40 live field-absent, review-word-free candidates, `wa64wz` (`usggph-02`) already fails property 2's backfill check because its `to-review` record contains the prose `NO-GO`. At the filing commit `f61aa714d` the pick was `1u4olp`, a plan demoted to `draft` by `52opph`. | `python3 -m pytest tests/test_readiness_absence_invariant.py -o addopts="" -m ""` -> `10 passed in 2.37s`; candidate scan over `git ls-tree` of `pending/` at `HEAD` and `f61aa714d~1`. | Whether the default suite is green depends on filename sort order and other lanes' prose. A tighter filter would just be the next thing to chase. |
| F-05 | Before this fix, the scan also EXCLUDED 12 live plans whose properties would fail (`P2bf`, `P3orig`, `P3bf`). For example, `42ertq` and `5eygjt` had a field-absent fallback approval. | Same scan at `f61aa714d~1`, `EXCLUDED-but-breaks` rows. | The predicates under test legitimately behave differently on post-review plans, so a "real" subject has to be filtered by the exact predicates under test. That makes the selection circular. |
| F-06 | The synthetic `_SYNTHETIC_PENDING_PLAN` passes properties 2, 3 and 4 today when it is the subject. | In-process run with `find_field_absent_pending_plan` stubbed to `None`: `synthetic P2 ok`, `synthetic P3 ok`, `synthetic P4 ok`. | Promoting it to the only subject keeps every assertion intact and green. |
| F-07 | Rejected alternative: tighten the finder to require `not ipd_lint._REVIEW_EVIDENCE_RE.search(history)` and `is_plan_review_approved` False. | F-05 | That filters the subject by the very predicates under test, so the test becomes partly tautological and still depends on the live tree. Rejected. |
| F-08 | Property 1 (`test_corpus_partition_pre_review_plans_lack_readiness_field`) is the only genuine corpus assertion and is already `@pytest.mark.livecorpus`. | the decorator in the module | It is unchanged. |

## Proposed changes (ordered, validatable)

1. Baseline and reproduce with an untracked planted demoted plan (E-01, V-01).
2. Make the subject fixture hermetic and amend the docstring (E-02, V-02).
3. Re-run with the planted plan still present, remove it, and compare against the bare-suite baseline (E-03, V-03).

## Deferred / out of scope (with reason)

- Reconciling `ipd_lint._REVIEW_EVIDENCE_RE` (mention matcher) with `plan_readiness.is_review_history_entry` (structural classifier). The disagreement is real (F-02). It is a separate linter behavior question, and it is not needed to fix this test's environmental coupling.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Property 1's own live-corpus failures (for example the `to-review` plans carrying `- Readiness:` recorded in `l56tyz` F-14). That test is correctly a corpus assertion under `livecorpus`, and its violations belong to the plans that cause them.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none. One test module; no production code, spec, or record changes.
- Under-scope: none. The backlog names only this coupling, and F-04 shows the fix covers the demotion shape and the prose-verdict shape (`wa64wz`), because no live plan is read any more.

## Required tests / validation

- `python3 -m pytest tests/test_readiness_absence_invariant.py -o addopts="" -m "" -v` before the edit (green), with the planted demoted plan before the edit (property 2 red), and with the planted plan after the edit (all green). This is the regression proof and the deliberate-break control.
- Bare `python3 -m pytest` before and after, compared by FAILING-NODE-ID SET; no new failing node id.
- `aw ipd lint --phase pre-transition` on this plan.

## Spec / documentation sync

N/A. No spec or user-facing document describes how this test picks its subject. A repository grep for `find_field_absent_pending_plan`, `get_field_absent_pending_plan_fixture` and `field-absent pending` outside `executed/` and `reviews/` matched only this module. The module docstring is amended in E-02. Executed plan `fx5op3` keeps its record unchanged.

## Open questions

### OQ-01: Should properties 2-4 keep a real-plan subject and add a `livecorpus` marker instead?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: No. F-05 shows a real subject must be filtered by the predicates under test, so marking those tests `livecorpus` would move a circular test out of the default suite instead of fixing it. The properties are claims about `ipd_lint`/`plan_readiness` behavior on a field-absent plan, and a fixed synthetic plan tests that directly. The corpus claim stays in property 1.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste (a) the pre-edit `-o addopts="" -m "" -v` output for this file listing every collected node id with its result, every one PASSED (this node-id list is the baseline set; the count is whatever is collected at the executing HEAD), (b) the pre-edit bare `python3 -m pytest` summary line and its list of FAILED node ids, (c) the planted scratch file's full text, and (d) the pre-edit run with it planted showing `FAILED tests/test_readiness_absence_invariant.py::test_linter_refuses_backfilled_readiness_field_with_m107` and the assertion message `got conforming`. If (d) does not fail, the reproduction is wrong, so stop and record it rather than proceeding.
  - Observed evidence:
    (a) Pre-edit `python3 -m pytest tests/test_readiness_absence_invariant.py -o addopts="" -m "" -v`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=3632623794
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items

    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[predecessor_narrated_approve] PASSED [ 10%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[reject_then_newer_non_review_approve] PASSED [ 20%]
    tests/test_readiness_absence_invariant.py::test_corpus_partition_pre_review_plans_lack_readiness_field PASSED [ 30%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[draft_approve] PASSED [ 40%]
    tests/test_readiness_absence_invariant.py::test_auto_approve_predicate_refuses_backfill_and_exercises_fallback PASSED [ 50%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[field_present_with_review] PASSED [ 60%]
    tests/test_readiness_absence_invariant.py::test_linter_refuses_backfilled_readiness_field_with_m107 PASSED [ 70%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[genuine_review_fallback] PASSED [ 80%]
    tests/test_readiness_absence_invariant.py::test_recheck_verb_refuses_field_absent_plan PASSED [ 90%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[to_review_approve] PASSED [100%]

    ============================== 10 passed in 5.12s ==============================
    ```

    (b) Pre-edit bare `python3 -m pytest` summary line and list of FAILED node ids:
    Summary line:
    `1 failed, 8113 passed, 4 skipped, 18 xfailed, 3 warnings in 870.99s (0:14:30)`
    FAILED node ids:
    `FAILED tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository`

    (c) Planted scratch file `.aw/records/plans/pending/00000000-zzrepro-01-zzz000-demoted.ipd.md` full text:
    ```markdown
    # IPD: sample (Set x, Order 1)

    - Date: 2026-08-03
    - Kind: child
    - Concern: sample.
    - Scope: sample.
    - Status: draft
    - Work-Kind: chore
    - Priority: medium
    - Set: x
    - Order: 1
    - Highest E allocated: 01
    - Author: tester
    - Id: zzz000

    ## Workflow history

    - 2026-08-06 draft (aw set): demoted approved -> draft: APPROVAL WITHDRAWN: returned to authoring
    - 2026-08-05 approved (maintainer): APPROVE for execution
    - 2026-08-03 to-review (tester): created.

    ## Goal

    Sample goal.

    ## Detailed Implementation Checklist (TODO)

    Execution-state rule: mark performed only after doing it.

    ### Task group 1: t

    - [ ] E-01 do a thing.
      - Depends on: none
      - Expected outcome: the thing exists.
      - Execution state: pending

    ## Project conventions discovered (Step 0)

    - x

    ## Findings

    - x

    ## Proposed changes (ordered, validatable)

    - x

    ## Deferred / out of scope (with reason)

    - x

    ## Scope check

    - x

    ## Required tests / validation

    - x

    ## Spec / documentation sync

    - x

    ## Open questions

    ### OQ-01: a question

    - Blocking: no
    - Status: open
    - Owner: none
    - Resolution or deferral rationale: n/a

    ## Validation and cross-check (verify before reporting done)

    Validation-state rule: inspect evidence separately.

    - [ ] V-01 validates E-01
      - Required evidence: the thing is present at path X.
      - Observed evidence:
      - Result: pending

    ## Approval and execution gate

    - Size assessment: standard
    - Cohesion rationale: not required

    Gate prose.
    ```

    (d) Pre-edit run with planted scratch file:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2866886566
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items

    tests/test_readiness_absence_invariant.py::test_corpus_partition_pre_review_plans_lack_readiness_field PASSED [ 10%]
    tests/test_readiness_absence_invariant.py::test_auto_approve_predicate_refuses_backfill_and_exercises_fallback PASSED [ 20%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[field_present_with_review] PASSED [ 30%]
    tests/test_readiness_absence_invariant.py::test_recheck_verb_refuses_field_absent_plan PASSED [ 40%]
    tests/test_readiness_absence_invariant.py::test_linter_refuses_backfilled_readiness_field_with_m107 FAILED [ 50%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[genuine_review_fallback] PASSED [ 60%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[draft_approve] PASSED [ 70%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[predecessor_narrated_approve] PASSED [ 80%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[reject_then_newer_non_review_approve] PASSED [ 90%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[to_review_approve] PASSED [100%]

    =================================== FAILURES ===================================
    ___________ test_linter_refuses_backfilled_readiness_field_with_m107 ___________

        def test_linter_refuses_backfilled_readiness_field_with_m107():
            """Property 2: lint_text yields a blocking IPD-M107 diagnostic upon simulated backfill."""
            subject_name, orig_text = get_field_absent_pending_plan_fixture(REPO_ROOT)
            res_orig = ipd_lint.lint_text(orig_text, checkpoint="author", directory="pending")
            assert res_orig.disposition == "conforming", (
                f"Expected unmodified subject {subject_name} to be conforming, got {res_orig.disposition}: "
                f"{[d.code for d in res_orig.diagnostics]}"
            )
            assert not any(
                d.code == ipd_lint.C_READINESS_UNATTESTED for d in res_orig.diagnostics
            )

            backfilled_text = re.sub(
                r"(^-\s*Status:\s*.*$)",
                r"\1\n- Readiness: go-pending-approval",
                orig_text,
                count=1,
                flags=re.MULTILINE,
            )
            res_backfilled = ipd_lint.lint_text(
                backfilled_text, checkpoint="author", directory="pending"
            )
    >       assert (
                res_backfilled.disposition == "error"
            ), f"Expected backfilled text to produce error disposition, got {res_backfilled.disposition}"
    E       AssertionError: Expected backfilled text to produce error disposition, got conforming
    E       assert 'conforming' == 'error'
    E
    E         - error
    E         + conforming

    tests/test_readiness_absence_invariant.py:214: AssertionError
    ------------------------------- LIVE-CORPUS NOTE -------------------------------
    This test read 2 distinct live-corpus path(s) under .aw/records/ during its call phase:
      - .aw/records/plans/pending/
      - .aw/records/plans/pending/00000000-zzrepro-01-zzz000-demoted.ipd.md

    Note: .aw/records/ is a LIVE tree that any agent or concurrent run may write to. A failure here may be caused by another party's artifact rather than by this lane's change. If this test genuinely asserts a whole-corpus property across all artifacts in .aw/records/, mark it with @pytest.mark.livecorpus (defined in pyproject.toml's pytest.ini_options) so it does not block default lanes or CI.
    =========================== short test summary info ============================
    FAILED tests/test_readiness_absence_invariant.py::test_linter_refuses_backfilled_readiness_field_with_m107
    ========================= 1 failed, 9 passed in 5.76s ==========================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff tests/test_readiness_absence_invariant.py`, showing that `find_field_absent_pending_plan` is removed, `get_field_absent_pending_plan_fixture` returns the synthetic subject with no repository argument, the three callers are updated, the docstring is amended, and NO `assert` line or `_SYNTHETIC_PENDING_PLAN` text changed. Paste `python3 -m pytest tests/test_readiness_absence_invariant.py -o addopts="" -m "" --collect-only -q` listing exactly the node-id set recorded in V-01 (a), compared by name.
  - Observed evidence:
    `git diff tests/test_readiness_absence_invariant.py`:
    ```diff
    diff --git a/tests/test_readiness_absence_invariant.py b/tests/test_readiness_absence_invariant.py
    index b8a77692d..96e47b1cd 100644
    --- a/tests/test_readiness_absence_invariant.py
    +++ b/tests/test_readiness_absence_invariant.py
    @@ -4,13 +4,15 @@ Asserts the four properties underlying the decision not to backfill the optional
     `- Readiness:` front-matter field onto pending plans:
     1. Corpus partition: no tracked plan under `.aw/records/plans/` at `draft` or `to-review`
        carries a `- Readiness:` field.
    -2. Linter refusal: inserting `- Readiness: go-pending-approval` onto a field-absent pending
    -   plan yields a blocking IPD-M107 diagnostic.
    +2. Linter refusal: inserting `- Readiness: go-pending-approval` onto the module's synthetic
    +   field-absent pending plan yields a blocking IPD-M107 diagnostic.
     3. Auto-approve predicate: `is_plan_review_approved` returns False both before and after
        a backfill without history, and returns True on a field-absent plan only when an approving
        review record possessing review provenance (`is_review_history_entry`) is the newest
        history record (fallback arm).
     4. Recheck verb: `recheck_conditions` reports `may_write=False` refusing an absent field.
    +
    +Only property 1 reads the live corpus, which is why only it carries `livecorpus`.
     """

     from __future__ import annotations
    @@ -154,26 +156,8 @@ Gate prose.
     """


    -def find_field_absent_pending_plan(repo_root: Path) -> Optional[Path]:
    -    """Scan .aw/records/plans/pending/ for a pending plan lacking a - Readiness: field and review history."""
    -    pending_dir = repo_root / ".aw" / "records" / "plans" / "pending"
    -    if not pending_dir.exists():
    -        return None
    -    for p in sorted(pending_dir.glob("*.ipd.md")):
    -        text = p.read_text(encoding="utf-8")
    -        if not plan_readiness._READINESS_FIELD_PRESENT_RE.search(text):
    -            if not re.search(
-                r"^\s*-\s*.*(?:/plan-review|reviewed\b).*$", text, re.MULTILINE
    -            ):
    -                return p
    -    return None
    -
    -
    -def get_field_absent_pending_plan_fixture(repo_root: Path) -> tuple[str, str]:
    -    """Return (filename, content) of a field-absent pending plan, falling back to a synthetic plan."""
    -    subject = find_field_absent_pending_plan(repo_root)
    -    if subject is not None:
    -        return subject.name, subject.read_text(encoding="utf-8")
    +def get_field_absent_pending_plan_fixture() -> tuple[str, str]:
    +    """Return (filename, content) of a field-absent pending plan fixture."""
         return "20260803-sample-01-abc123-sample.ipd.md", _SYNTHETIC_PENDING_PLAN


    @@ -191,7 +175,7 @@ def test_corpus_partition_pre_review_plans_lack_readiness_field():

     def test_linter_refuses_backfilled_readiness_field_with_m107():
         """Property 2: lint_text yields a blocking IPD-M107 diagnostic upon simulated backfill."""
    -    subject_name, orig_text = get_field_absent_pending_plan_fixture(REPO_ROOT)
    +    subject_name, orig_text = get_field_absent_pending_plan_fixture()
         res_orig = ipd_lint.lint_text(orig_text, checkpoint="author", directory="pending")
         assert res_orig.disposition == "conforming", (
             f"Expected unmodified subject {subject_name} to be conforming, got {res_orig.disposition}: "
    @@ -228,7 +212,7 @@ def test_linter_refuses_backfilled_readiness_field_with_m107():
     def test_auto_approve_predicate_refuses_backfill_and_exercises_fallback(tmp_path: Path):
         """Property 3: is_plan_review_approved returns False before/after backfill, and True with approving review history."""
         # tmp_path is required because is_plan_review_approved takes a Path rather than text.
    -    _subject_name, orig_text = get_field_absent_pending_plan_fixture(REPO_ROOT)
    +    _subject_name, orig_text = get_field_absent_pending_plan_fixture()

         # 1. Unmodified field-absent plan -> False
         f_orig = tmp_path / "orig.ipd.md"
    @@ -357,7 +341,7 @@ def test_fallback_arm_forgery_shapes_and_surviving_fallback(
     def test_recheck_verb_refuses_field_absent_plan(tmp_path: Path):
         """Property 4: recheck_conditions reports may_write=False with an absent-field refusal."""
         # tmp_path and a temporary git repo are required because recheck_conditions takes (repo_root, plan_path).
    -    subject_name, orig_text = get_field_absent_pending_plan_fixture(REPO_ROOT)
    +    subject_name, orig_text = get_field_absent_pending_plan_fixture()

         subprocess.check_call(["git", "init", "-q"], cwd=tmp_path)
         pending_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
    ```
    No `assert` line or `_SYNTHETIC_PENDING_PLAN` text was changed.

    `python3 -m pytest tests/test_readiness_absence_invariant.py -o addopts="" -m "" --collect-only -q`:
    ```
    tests/test_readiness_absence_invariant.py::test_corpus_partition_pre_review_plans_lack_readiness_field
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[to_review_approve]
    tests/test_readiness_absence_invariant.py::test_recheck_verb_refuses_field_absent_plan
    tests/test_readiness_absence_invariant.py::test_linter_refuses_backfilled_readiness_field_with_m107
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[reject_then_newer_non_review_approve]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[genuine_review_fallback]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[draft_approve]
    tests/test_readiness_absence_invariant.py::test_auto_approve_predicate_refuses_backfill_and_exercises_fallback
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[predecessor_narrated_approve]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[field_present_with_review]

    10 tests collected in 0.50s
    ```
    The collected node-id set is identical to V-01 (a) by name.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste (a) the post-edit `-o addopts="" -m "" -v` run with the scratch plan STILL planted, showing every node id from V-01 (a) PASSED, including `test_linter_refuses_backfilled_readiness_field_with_m107` that V-01 (d) showed FAILED with the same plant (the regression proof), (b) `git status --short .aw/records/plans/` after deleting it, showing no `zzrepro` entry, (c) the post-edit bare `python3 -m pytest` summary line and FAILED node-id list, stating which ids, if any, differ from V-01 (b) and that none is in this module or caused by this change, and (d) the `aw ipd lint --phase pre-transition` output for this plan reporting conforming.
  - Observed evidence:
    (a) Post-edit `-o addopts="" -m "" -v` run with scratch plan still planted:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=415992797
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items

    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[reject_then_newer_non_review_approve] PASSED [ 10%]
    tests/test_readiness_absence_invariant.py::test_recheck_verb_refuses_field_absent_plan PASSED [ 20%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[genuine_review_fallback] PASSED [ 30%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[field_present_with_review] PASSED [ 40%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[to_review_approve] PASSED [ 50%]
    tests/test_readiness_absence_invariant.py::test_linter_refuses_backfilled_readiness_field_with_m107 PASSED [ 60%]
    tests/test_readiness_absence_invariant.py::test_corpus_partition_pre_review_plans_lack_readiness_field PASSED [ 70%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[predecessor_narrated_approve] PASSED [ 80%]
    tests/test_readiness_absence_invariant.py::test_auto_approve_predicate_refuses_backfill_and_exercises_fallback PASSED [ 90%]
    tests/test_readiness_absence_invariant.py::test_fallback_arm_forgery_shapes_and_surviving_fallback[draft_approve] PASSED [100%]

    ============================== 10 passed in 6.76s ==============================
    ```
    All 10 tests passed, including `test_linter_refuses_backfilled_readiness_field_with_m107` which previously failed with the planted demoted plan.

    (b) `git status --short .aw/records/plans/` after deleting scratch file:
    Clean output (no output, no `zzrepro` entry).

    (c) Post-edit bare `python3 -m pytest` summary line and FAILED node-id list:
    Summary line:
    `8114 passed, 4 skipped, 18 xfailed, 3 warnings in 852.54s (0:14:12)`
    FAILED node ids: None (0 failed). Differs from V-01 (b) in that the single flake in `test_host_capability_extension.py` passed in this run; none in this module or caused by this change.

    (d) `aw ipd lint --phase pre-transition` output for this plan:
    ```
    - >  ◕  approved     plan        20261012-110dg8-01-rrydjy  [medium]  [blocking]  conforming
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Follow the tooled lifecycle. In a managed lane the runner owns `aw ipd begin`/`finalize`; in a manual run use `aw ipd begin rrydjy`, perform E-01 through E-03 in order, fill every `V-*` with pasted actual output, confirm `aw ipd lint --phase pre-transition` conforms, then `aw ipd finalize rrydjy`; never hand-`git mv` the plan to `executed/`. Every test claim MUST be backed by the ACTUAL pasted runner output; never claim a run you did not perform. OQ-01 is resolved; no open question remains. Scope fence: `- Scope-Paths:` declares `tests/test_readiness_absence_invariant.py` (plus this plan); an edit outside it must be justified at finalize via `--scope-reason`. Commit only `tests/test_readiness_absence_invariant.py` and this plan through `aw commit rrydjy -- <paths>`; never `git add -A`, never push. The E-01 scratch plan is UNTRACKED and must never be staged or committed, and it must be deleted before finalize. Once this plan is executed, backlog `110dg8` closes through the HANDOFF route (this plan carries `- From-Backlog: 110dg8` and `- Blocks-Release: next`).
