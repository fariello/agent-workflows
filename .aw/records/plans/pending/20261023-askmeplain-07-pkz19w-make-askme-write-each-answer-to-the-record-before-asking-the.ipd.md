# IPD: Make askme write each answer to the record before asking the next question

- Date: 2026-10-23
- Kind: child
- Concern: Live trial T12 on Claude Code + Sonnet 5 (plan `lkn1zt`, findings `auwidn`, D-9, counted from the T05 run with maintainer approval) asked three open questions one at a time but held all three answers in the conversation and wrote them together only after the third ("All three open questions on plan `m4rcyy` are now answered. Recording the decisions in the plan now."). If the session had been interrupted after the second answer, both earlier decisions would have been lost. The workflow already says "Record the answer before asking the next question." (`askme.md` "Record project decisions"), but the line sits at the END of the recording bullets, far from "Ask and wait" where the next question is composed. The same host recorded each answer first in T06, and the other three combinations did so in every multi-question row (tool sequences `question, edit, question, edit, ...` in OpenCode + gem T04, Antigravity T04), so the behavior is inconsistent rather than absent.
- Scope: IN: in `askme.md` `## Ask and wait`, add an explicit ordering step: after a definite answer, write it to the record (per "Record project decisions") and only then compose or ask the next question; batching answers to write at the end is not allowed; in `## Finish`, say the final report summarizes records already written, not a write step. Mirror the reasoning in `rationale.md`; add a behavioral installer-output test. OUT: other `lkn1zt` defects (plans `9vttho`, `lf4j52`, `wfy9ii`, `l5f2hg`).
- Scope-Paths: .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, tests/test_askme_command_delivery.py, tests/slow_allowlist.txt, CHANGELOG.md
- Item-Dependencies: executed:lkn1zt
- Status: approved
- Readiness: go-pending-approval
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: askmeplain
- Order: 7
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: pkz19w
- Approval: 2026-10-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-007 fixed (review record .aw/records/reviews/20261023-askmeplain-07-pkz19w-make-askme-write-each-answer-to-the-record-before-asking-the.review.md)
- 2026-10-23 to-review (aw set): authored review-ready from lkn1zt findings auwidn (D-9)

- 2026-10-23 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every host persist each answer to its record before asking the next question, so an interrupted session never loses a decision the user already made.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rule

- [x] E-01 In `.aw/system/workflows/askme/askme.md` `## Ask and wait`, add a short paragraph immediately after the paragraph beginning "If the user both makes an unambiguous choice" (sibling plan `l5f2hg` also adds a sentence to this section; place this paragraph relative to that anchor, not to the section end), containing verbatim the sentence "Write each definite answer to its record before you compose or ask the next question." and stating, in direct language, that answers must not be held in the conversation to be written together later, because an interrupted session would lose them; it points to "Record project decisions" for how to write the answer. In `## Finish`, replace "After the answers are recorded, report the decisions" with wording that says each answer was already written to its record when it was given, and that the report only summarizes those records. Add one `## Writing each answer before the next question` section to `.aw/system/workflows/askme/rationale.md` in the file's existing dated-incident style: a live trial on Claude Code with Sonnet 5 (October 2026; use the date from findings `auwidn` if it records one, else the month) asked three questions one at a time, held all three answers, and wrote them only after the third ("All three open questions on plan `m4rcyy` are now answered. Recording the decisions in the plan now."), while the same host wrote each answer first in another session. `rationale.md` is installed into other repositories, so the paragraph must make sense without any id6 (the file has none today); do NOT cite `lkn1zt` or `auwidn` there. Leave `## Explicitly noninteractive runs` unchanged (that branch asks nothing).
  - Depends on: none
  - Expected outcome: the ordering paragraph with the exact sentence, the Finish wording, and the rationale section are present; the existing "Record the answer before asking the next question." bullet in `## Record project decisions` stays.
  - Execution state: performed
- [x] E-02 BEFORE applying E-01's `askme.md` edit, add a test method to `AskmeCommandDeliveryTests` in `tests/test_askme_command_delivery.py` that installs into a temporary repo (`tests.support.init_repo`, then `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)` under `redirect_stdout`, as `test_installer_delivers_and_preserves_askme_shims` does), reads the INSTALLED `.aw/system/workflows/askme/askme.md`, slices the `## Ask and wait` section (from that heading to the next line starting `## `), and asserts the slice contains "Write each definite answer to its record before you compose or ask the next question." Mark it `@pytest.mark.slow` (a full install takes about 3s; the sibling installer test is marked the same way) and add its node id with a one-line reason to `tests/slow_allowlist.txt` so the slow-test report stays clean. Run it once now with `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` and keep the FAILED output; after E-01 run it again. Then add one `- Fixed:` CHANGELOG bullet under the topmost pending heading (`## 2.0.0 (pending)`): `/askme` now writes each answer to its record before asking the next question (plain language, no em or en dashes).
  - Depends on: none
  - Expected outcome: the new test fails before E-01 and passes after it; the allowlist line and the CHANGELOG bullet are present.
  - Execution state: performed
- [x] E-03 Run `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` (clearing `addopts` is required, because the default `-m 'not slow'` would deselect the new test), then the bare core gate `python3 -m pytest`.
  - Depends on: E-01, E-02
  - Expected outcome: every test in the file passes, including the new one, and the slow-test report lists 0 unlisted tests; the bare gate reports no failures.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The workflow body `.aw/system/workflows/askme/askme.md` is referenced by every host shim (`engine.shim_body`).
- Delivery tests: `tests/test_askme_command_delivery.py`; assertions on installed output only.
- Every live bug gates the next release, hence `- Blocks-Release: next`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Answers batched until the end | `auwidn` Claude Code T12 (via T05): "Recording the decisions in the plan now." after the third answer |
| F-2 | Same host recorded per answer in another session | `auwidn` Claude Code T06 |
| F-3 | Other hosts record per answer | `auwidn` OpenCode + gem T12 ("tool sequence `question, edit, question, edit, question, edit`"), Antigravity T12 ("an `edit_file` writing each resolution before the next `ask_question`"), OpenCode + opus T12 (via T04, "wrote each resolution to the record before the next prompt") |
| F-5 | The installed body is the source body, and `rationale.md` ships too | Review-time probe: `engine.install_into_repo` into a temp repo produced `.aw/system/workflows/askme/` = `README.md`, `askme.md`, `rationale.md`, with `askme.md` byte-identical to the source; `rationale.md` contains no id6 today |
| F-6 | A full install test is slow | `python3 -m pytest -o addopts="" --durations=3 tests/test_askme_command_delivery.py`: `test_installer_delivers_and_preserves_askme_shims` 3.08s, `@pytest.mark.slow`, listed in `tests/slow_allowlist.txt`; the report threshold is 2.0s (`conftest.py` `AW_SLOW_REPORT_SECONDS`) |
| F-4 | The rule exists, positioned away from the asking step | `askme.md` "Record project decisions": "Record the answer before asking the next question." |

## Proposed changes (ordered, validatable)

E-01 to E-03, each validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Live re-run of T12 on Claude Code: maintainer-attended act.
  - Carrier-Declined: re-verification reuses `lkn1zt`'s method at the maintainer's discretion.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Invariant: a host following the installed `askme.md` is told, at the point it composes the next question, to write the previous answer first. Pinned by the E-02 installer-output test, which fails on the pre-change body and passes after E-01. Commands: `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` and the bare `python3 -m pytest` (E-03), outputs pasted. Whether hosts actually change behavior is not provable by a unit test; that is the deferred live re-run.

## Spec / documentation sync

N/A for specs: the askme workflow body is not spec-governed (sibling plans `lf4j52` and `l5f2hg` edit the same body without a spec). `rationale.md` in E-01; `CHANGELOG.md` in E-02.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git diff -- .aw/system/workflows/askme/askme.md .aw/system/workflows/askme/rationale.md` hunks showing the ordering paragraph (with the exact sentence) after the "If the user both makes an unambiguous choice" paragraph in `## Ask and wait`, the replaced Finish wording, the new rationale section; `grep -n "Record the answer before asking the next question." .aw/system/workflows/askme/askme.md` still matching; and `git diff -U0 -- .aw/system/workflows/askme/rationale.md | grep '^+' | grep -E '\b(lkn1zt|auwidn)\b'` returning nothing.
  - Observed evidence:
```diff
diff --git a/.aw/system/workflows/askme/askme.md b/.aw/system/workflows/askme/askme.md
index 8b47517ca..7fd1e1df3 100644
--- a/.aw/system/workflows/askme/askme.md
+++ b/.aw/system/workflows/askme/askme.md
@@ -158,6 +158,11 @@ If the user both makes an unambiguous choice and criticizes the wording,
 record the choice and fix the wording. If the choice is uncertain, clarify
 it before recording a resolution. Do not invent a reason the user did not give.

+Write each definite answer to its record before you compose or ask the next question.
+Do not hold answers in the conversation to write together later, because an
+interrupted session would lose earlier decisions. See "Record project decisions"
+below for how to write each answer to the record.
+
 ## Record project decisions

 For a question raised in a record's `## Open questions` section:
@@ -203,8 +208,9 @@ For a single conversational question, ask it directly without a preliminary
 inventory report. For a collection of project questions, give a short count
 only if it helps the user understand the scope.

-After the answers are recorded, report the decisions and any work still
-blocked. Show the list of evidence-based resolutions you decided alone,
-with hard-to-reverse ones flagged, so nothing was chosen silently. Identify
+Each answer was already written to its record when it was given; this final
+report only summarizes those records and identifies any work still blocked.
+Show the list of evidence-based resolutions you decided alone, with
+hard-to-reverse ones flagged, so nothing was chosen silently. Identify
 evidence-based resolutions separately from user choices. Do not report
 completion while required human answers are still missing.
diff --git a/.aw/system/workflows/askme/rationale.md b/.aw/system/workflows/askme/rationale.md
index bb948068b..7fed43bc2 100644
--- a/.aw/system/workflows/askme/rationale.md
+++ b/.aw/system/workflows/askme/rationale.md
@@ -40,3 +40,7 @@ When a user reports incomprehension ("I have zero context here", "what is X?", "

 Live trials in plan `lkn1zt` (findings `auwidn`, trial T05) showed that invoking `/askme` without arguments led multiple host and model combinations to scan the repository using `aw attention`, recursive `grep`, and `find` when no conversational question was pending. In a shared checkout, this caused agents to discover and ask open questions from plans authored by other agents or humans without confirming authorship. The no-argument scope rule therefore restricts candidate records strictly to those whose edits appear in the current conversation's own tool calls, explicitly forbids repository-wide discovery searches, and requires stopping with instructions when both conversational and session sources are empty.

+## Writing each answer before the next question
+
+In a live trial on Claude Code with Sonnet 5 on 2026-10-20, an agent asked three open questions one at a time, but held all three answers in the conversation and wrote them to the plan only after the third ("All three open questions on plan `m4rcyy` are now answered. Recording the decisions in the plan now."). If the session had been interrupted after the first or second answer, those earlier decisions would have been lost. The same host wrote each answer first in another session, showing that the behavior was inconsistent. The workflow therefore requires persisting each definite answer to its record before composing or asking the next question.
```
```sh
$ grep -n "Record the answer before asking the next question." .aw/system/workflows/askme/askme.md
175:- Record the answer before asking the next question.
```
```sh
$ git diff -U0 -- .aw/system/workflows/askme/rationale.md | grep '^+' | grep -E '\b(lkn1zt|auwidn)\b'
(exit code 1, 0 matches)
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` output from BEFORE E-01 showing the new test FAILED on its assertion (not on an error), the test's asserting line quoted, and the `git diff` of `tests/slow_allowlist.txt` and `CHANGELOG.md` (one added line each, no em or en dash).
  - Observed evidence: Verified new test failed on assertion before E-01 and slow_allowlist.txt/CHANGELOG.md each contain one added line.
    1. Failed test runner output before E-01:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=156270945
rootdir: <repo>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 5 items

tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_and_preserves_askme_shims PASSED [ 20%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_agents_pointer_prose_names_askme PASSED [ 40%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_write_before_ask_rule FAILED [ 60%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_no_scan_rule PASSED [ 80%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_askme_shims_rendered_from_manifest PASSED [100%]

=================================== FAILURES ===================================
_ AskmeCommandDeliveryTests.test_installer_delivers_askme_write_before_ask_rule _

self = <tests.test_askme_command_delivery.AskmeCommandDeliveryTests testMethod=test_installer_delivers_askme_write_before_ask_rule>

    @pytest.mark.slow
    def test_installer_delivers_askme_write_before_ask_rule(self):
        """Assert installer delivers askme.md with write-each-answer-before-next-question rule in ## Ask and wait."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td) / "target")

            with redirect_stdout(io.StringIO()):
                engine.install_into_repo(
                    repo, SOURCE_WORKFLOWS, yes=True, no_color=True
                )

            installed_askme = (
                repo / ".aw" / "system" / "workflows" / "askme" / "askme.md"
            )
            self.assertTrue(
                installed_askme.is_file(),
                "Installed askme workflow body must exist",
            )
            installed_text = installed_askme.read_text(encoding="utf-8")
            start_idx = installed_text.find("## Ask and wait")
            self.assertNotEqual(start_idx, -1, "## Ask and wait heading must exist")
            end_idx = installed_text.find("\n## ", start_idx + len("## Ask and wait"))
            section = (
                installed_text[start_idx:end_idx]
                if end_idx != -1
                else installed_text[start_idx:]
            )
>           self.assertIn(
                "Write each definite answer to its record before you compose or ask the next question.",
                section,
            )
E           AssertionError: 'Write each definite answer to its record before you compose or ask the next question.' not found in "## Ask and wait\n\nUse the host's interactive question tool when available and appropriate.\nUse the question and option-description fields to carry the required\ncontext; do not leave it only in a progress message or surrounding chat.\nIf the tool is unavailable or inadequate, ask in chat and wait for a reply.\n\nDo not continue dependent work, treat silence as consent, select your own\nrecommendation for the user, or report the decision as complete while\nwaiting. Continue independent work only when it does not presume an answer.\n\nIf the user says they do not understand, rewrite the question from scratch\nwith the missing context and clearer wording. A complaint or clarification\nrequest is not a decision. Apply this rule to free-text tool responses too.\n\nIf the user both makes an unambiguous choice and criticizes the wording,\nrecord the choice and fix the wording. If the choice is uncertain, clarify\nit before recording a resolution. Do not invent a reason the user did not give.\n"

tests/test_askme_command_delivery.py:256: AssertionError
============================== SLOW TESTS REPORT ===============================
WARNING: 1 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
    2.36s  tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_no_scan_rule
=========================== short test summary info ============================
FAILED tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_write_before_ask_rule
========================= 1 failed, 4 passed in 8.18s ==========================
```
    2. Asserting line quoted:
```python
            self.assertIn(
                "Write each definite answer to its record before you compose or ask the next question.",
                section,
            )
```
    3. `git diff` of `tests/slow_allowlist.txt` and `CHANGELOG.md` (one added line each, no em or en dash):
```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index dedde3214..34bf3dabf 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Fixed: /askme now writes each answer to its record before asking the next question.
 - Fixed: `aw partition -t plans` no longer refuses a batch because of a Set whose orchestrator has already been executed. Such a Set has nothing left to keep together, so its plans that match the selection are scheduled, its other plans are ignored instead of being reported as blocking, and its plans are balanced across shards like any others. Declared plan dependencies are still enforced.
 - Added: Notification channels now show question groups. In full mode each distinct question appears once, with how many plans asked it and the group answer command, the `aw.notify/v1` JSON gains `distinct_count` and per-entry group fields, and one Telegram reply or button press answers every parked plan that asked the question. Terse text is unchanged.
 - Added: `aw notify` command family (setup telegram, setup webhook, setup command, status, disable, test, listen) for configuring and managing outbound runner notifications and live command listening. Includes `docs/notifications.md` user guide.
diff --git a/tests/slow_allowlist.txt b/tests/slow_allowlist.txt
index f4dd92fc1..14d06ab08 100644
--- a/tests/slow_allowlist.txt
+++ b/tests/slow_allowlist.txt
@@ -20,6 +20,7 @@ tests/test_agy_skill_install.py::AgySkillInstallTests::test_install_emits_aw_rou
 tests/test_agy_skill_install.py::AgySkillInstallTests::test_install_idempotence	Full repo install/uninstall filesystem fixture tree lifecycle
 tests/test_agy_skill_install.py::AgySkillInstallTests::test_router_lists_every_non_catalog_verb	Full repo install/uninstall filesystem fixture tree lifecycle
 tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_and_preserves_askme_shims	Full repo install/uninstall filesystem fixture tree lifecycle
+tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_write_before_ask_rule	Full repo install/uninstall filesystem fixture tree lifecycle
 tests/test_attempt_lane_facts.py::AttemptLaneFactsTests::test_case_1_oc_host_integrated_isolated_turn	Subprocess CLI execution and isolated worktree integration boundary
 tests/test_attempt_lane_facts.py::AttemptLaneFactsTests::test_case_2_oc_host_refused_isolated_turn	Subprocess CLI execution and isolated worktree integration boundary
 tests/test_attention.py::NameGrammarAgreesWithTheNamingAuthorityTests::test_name_grammar_agrees_with_naming_authority	Repository diagnostics and check engine evaluation across fixture
```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` output after E-01 with every test PASSED including the new one, and its `SLOW TESTS REPORT` line reading 0 unlisted; pasted final summary line of the bare `python3 -m pytest` run (and any budget block verbatim) showing no failures.
  - Observed evidence: Verified delivery tests pass and full regression suite passed with zero failures.
    1. `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v`:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=1354893012
rootdir: <repo>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 5 items

tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_askme_shims_rendered_from_manifest PASSED [ 20%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_agents_pointer_prose_names_askme PASSED [ 40%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_no_scan_rule PASSED [ 60%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_and_preserves_askme_shims PASSED [ 80%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_write_before_ask_rule PASSED [100%]
============================== SLOW TESTS REPORT ===============================

WARNING: 1 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
    3.00s  tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_no_scan_rule
============================== 5 passed in 10.69s ==============================
```
    Note on SLOW TESTS REPORT: The newly added test `test_installer_delivers_askme_write_before_ask_rule` was properly allowlisted and introduced 0 unlisted slow tests. Sibling test `test_installer_delivers_askme_no_scan_rule` (authored in 9vttho) exceeded 2.0s due to being omitted from `tests/slow_allowlist.txt` in 9vttho; this has been filed as adjacent backlog defect ucuh2h (see D-01).

    2. Final summary line of bare `python3 -m pytest` run and budget block:
```
================================ CORE TIER BUDGET EXCEEDED ================================
Core tier wall time: 86.09s exceeded budget of 30.00s.
Host 1-minute load average: 18.52 on 12 CPUs
Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
Top 10 slowest core tests:
   1.   8.90s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
   2.   8.09s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
   3.   7.33s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
   4.   7.33s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
   5.   5.98s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
   6.   5.56s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
   7.   5.03s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
   8.   4.06s  tests/test_notify_cli.py::test_listen_lifecycle_and_answering
   9.   3.96s  tests/test_ipd_lint.py::ReadinessAttestationTests::test_every_readiness_carrying_plan_in_the_tree_is_attested
  10.   2.98s  tests/test_status_set.py::TestDryRunMachineDisposition::test_dry_run_backlog_item_typed_and_untyped_spellings
===========================================================================================

1740 passed, 11 warnings in 86.08s (0:01:26)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Open questions: none.

Scope fence: the files in `- Scope-Paths:` are the declared edit set; an edit outside it must be made and then justified at finalize (`--scope-reason`), and a declared path left unmodified acknowledged (`--scope-ack`).

Honesty: when reporting tests passed, you MUST paste the ACTUAL runner output; never claim a result you did not observe.

Commits: only the Scope-Paths files, through `aw commit pkz19w -- <paths>`; never `git add -A`, never push, never tag.

Lifecycle: when executed by hand, the executor finalizes with `aw ipd finalize pkz19w --actor <agent/model> --message <summary> --apply`, only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. When a runner (`aw oc run` / `aw agy run`) dispatched it, the runner owns finalize. Never `git mv` the plan to `executed/`.
