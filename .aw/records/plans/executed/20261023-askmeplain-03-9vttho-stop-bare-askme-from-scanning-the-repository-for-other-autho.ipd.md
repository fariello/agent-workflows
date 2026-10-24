# IPD: Stop bare /askme from scanning the repository for other authors' open questions

- Date: 2026-10-23
- Kind: child
- Concern: Live trials (plan `lkn1zt`, findings `auwidn`, row T05) showed that `/askme` with no arguments and no outstanding conversational question makes three of four host/model combinations SCAN THE REPOSITORY for open questions: Claude Code + Sonnet 5 ran `grep -rln "Blocking: yes" .aw/records/plans/pending/ .aw/records/specs/`; Antigravity + Gemini 3.8 Flash ran `aw attention`, `find .aw/records -type f -mmin -120` and `grep -rn "Status: open"`; OpenCode + Gemini 3.8 Flash ran `aw attention` and grepped every record for `^### OQ-`. Two of them (Antigravity, OpenCode + Gemini) then asked the human all three open questions of a plan they had not authored, without checking authorship or asking whether that plan was meant. The workflow already says "Do not scan the entire repository by default" (`askme.md` "Recognize the request" item 4); the instruction is present and is not followed. OpenCode + opus, given the same input, did no search and reported nothing to ask (T05 pass). The effect on a user: a bare `/askme` in a shared checkout can put another agent's or human's decisions to the wrong person and record answers in their records.
- Scope: IN: rewrite the no-argument scope rule in `askme.md` so the permitted search is defined positively and narrowly (this conversation; records this session created or edited, identified by this session's own edits, not by searching), name the forbidden actions concretely (running `aw attention`, recursive grep or find over `.aw/records`, reading records the session did not touch), and state the required output when both scopes are empty (say so, offer the three ways to point at a subject, and stop); mirror the rule in `rationale.md`; add a behavioral test that the installed workflow body carries the rule (the generated shims only point at that body via `engine.shim_body` and need no change). OUT: changes to any host's tool permissions; a runtime enforcement layer (research `y0vcm9`: "Start with these source and instruction changes before adding a new enforcement service"); the other defects found by `lkn1zt` (separate plans `lf4j52`, `wfy9ii`, `l5f2hg`, `pkz19w`).
- Scope-Paths: .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, tests/test_askme_command_delivery.py, CHANGELOG.md
- Item-Dependencies: executed:lkn1zt
- Status: executed
- Readiness: go-pending-approval
- Blocks-Release: next
- Work-Kind: bug
- Priority: high
- Set: askmeplain
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9vttho

## Workflow history
- 2026-10-24 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 9vttho verified (set askmeplain, attempt 1).
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-23 to-review (aw set): authored review-ready from lkn1zt findings auwidn (D-8)

- 2026-10-23 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make a bare `/askme` look only at the current conversation and at records this session itself created or edited, so it never searches the repository and never puts another author's open questions to the user without asking.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the rule

- [x] E-01 Rewrite item 4 of `## Recognize the request` in `.aw/system/workflows/askme/askme.md` (the paragraph beginning "**Use the current conversation.**"). Keep its two permitted sources (the outstanding question in this conversation; unanswered questions in records this session created or edited), and add, in direct language: (a) "records this session created or edited" means records whose edits appear in this conversation's own tool calls; establish them from the conversation, not by searching; (b) do not run `aw attention`, `aw find`, or any recursive search (`grep -r`, `find`, `git log --all`) over `.aw/records` to discover questions; (c) if both sources are empty, say so in one or two sentences, list the three ways to point `/askme` at a subject (a question, a record or set id, or an explicit request to scan), and stop without asking a question; (d) a record found any other way is not this session's even if it carries open questions. (e) these limits apply only to the no-argument case: items 2 and 3 and an explicit user request to scan ("look through the repo for open questions") are unaffected. Replace item 4's current sentence "In a shared checkout, confirm authorship before treating a record or question as yours (`git log` and the record's `- Author:` line settle it)." because in the no-argument case the session's own edits are known from the conversation and a `git log` search is exactly what (b) forbids; leave the separate shared-checkout paragraph in `## Establish facts before asking` unchanged, since it still governs records reached through item 3. Keep the existing "Do not scan the entire repository by default" sentence or fold it into (b). Mirror the reasoning in `.aw/system/workflows/askme/rationale.md` in one short paragraph citing `lkn1zt` T05.
  - Depends on: none
  - Expected outcome: item 4 states (a) to (e) and no longer tells the agent to run `git log` to find its own records; `rationale.md` gains one paragraph explaining why; no other section of `askme.md` changes.
  - Execution state: performed
- [x] E-02 Add a new test method to `AskmeCommandDeliveryTests` in `tests/test_askme_command_delivery.py` that runs `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)` into a fresh `tests.support.init_repo` temp repo (the `test_installer_delivers_and_preserves_askme_shims` pattern) and asserts that the INSTALLED `<repo>/.aw/system/workflows/askme/askme.md` contains the no-scan rule's operative phrases: the conversation-only source of (a), the prohibition on `aw attention` and recursive search of (b), and the empty-scope stop of (c); and that it no longer contains the replaced `git log` authorship sentence of (e). Assert on the installed file's text as delivered output, not on the source file in the repository. Mark it `@pytest.mark.slow`, like its installer sibling: one install takes about 5 s (measured at review: the file's 3 tests ran in `5.60s`), so it belongs to the thorough tier and is not collected by the bare core-tier run.
  - Depends on: E-01
  - Expected outcome: the test passes against the edited body and fails against the pre-E-01 body.
  - Execution state: performed
- [x] E-03 Add a CHANGELOG entry under the topmost pending release section (`## 2.0.0 (pending)`, which already holds the earlier `/askme` bullet beginning "- Changed: /askme is retained as a supported command alias") describing the user-visible change (bare `/askme` no longer searches the repository and says there is nothing to ask). Use the section's `- Fixed: ` prefix convention. Plain language, no em or en dashes (user-facing prose).
  - Depends on: E-01
  - Expected outcome: one bullet under the topmost `## ... (pending)` heading.
  - Execution state: performed
- [x] E-04 Run the new test file with the marker filter cleared, `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` (clearing `addopts` drops `-m 'not slow ...'`, so the slow installer tests run), then the bare core-tier gate `python3 -m pytest`. The bare run does not collect this file (measured at review: 0 of its tests in `python3 -m pytest --co`), so it is the regression gate for the rest of the repository, not evidence for the new test.
  - Depends on: E-02, E-03
  - Expected outcome: both runs report no failures.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The workflow body is `.aw/system/workflows/askme/askme.md`; host shims (`.opencode/commands/askme.md`, `.claude/commands/askme.md`) only say "Read and execute @.aw/system/workflows/askme/askme.md" (`engine.shim_body`), so a body edit reaches both slash-command hosts without regenerating shims. Antigravity uses the read-and-execute fallback on the same file.
- Existing delivery tests live in `tests/test_askme_command_delivery.py` (`AskmeCommandDeliveryTests`), including an installer round trip through `tests.support.init_repo`.
- Tests must assert on behavior and outputs, not on source text read with `inspect`/regex (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); asserting on the INSTALLED workflow file an installer run produced is an output assertion.
- Every live bug gates the next release (AGENTS.md "Every live bug gates the next release"), hence `- Blocks-Release: next`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Three of four combinations scanned on bare `/askme` | findings `auwidn` T05 rows for Claude Code, Antigravity, OpenCode + gem (commands quoted there) |
| F-2 | Two then asked another author's questions without checking authorship | `auwidn` Antigravity T05 and OpenCode + gem T05: "It never checked the fixture's authorship" |
| F-3 | The current rule exists and is not followed | `askme.md` item 4: "Do not scan the entire repository by default." |
| F-4 | One combination followed it | `auwidn` OpenCode + opus T05: "read `askme.md` only. No grep, no scan" |

## Proposed changes (ordered, validatable)

E-01 (rule), E-02 (test), E-03 (changelog), E-04 (suite), each validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Re-running the T05 live trial on all hosts after the change: a live trial needs an attended session and is not automatable; recorded as a follow-up for the maintainer.
  - Carrier-Declined: re-verification is a maintainer-attended act, not plan work; `lkn1zt`'s method can be re-used.

## Scope check

- Over-scope: none.
- Under-scope: none. Checked at review: the shim argument text and the `askme` index row ("without arguments use the outstanding question in the current conversation, otherwise this session's unanswered project questions", `.aw/system/workflows/index.md` `| askme |` row, rendered by `engine.shim_body`) already match the narrowed rule, so neither needs an edit. Sibling plans `lf4j52`, `wfy9ii`, `l5f2hg`, `pkz19w` edit other sections of the same files; E-01 touches only item 4.

## Required tests / validation

The new installer-output test (E-02), run by path with `-o addopts=""` because it is `slow`, plus the bare `python3 -m pytest` (E-04), outputs pasted. Honest limit: the test proves the rule is DELIVERED to an installed repo, not that an agent obeys it; research `y0vcm9` ("Automated checks can establish that instructions were generated and delivered. They cannot prove that the resulting explanation is understandable.") and the T05 evidence that the old rule was present and ignored both say so. Behavioral confirmation is the attended re-run recorded under Deferred.

Invariants and the test that maps to each:
- I-1 Item 2 and item 3 scopes and an explicit scan request still work: E-01 (e) and V-01's diff showing items 1 to 3 unchanged.
- I-2 The shared-checkout authorship rule for records reached through item 3 survives: V-01's diff showing `## Establish facts before asking` unchanged.
- I-3 The installed body carries the new rule and not the replaced `git log` sentence: E-02 test, with V-02's pre-change failure proving sensitivity.

## Spec / documentation sync

N/A for specs: no spec governs the askme body's scope wording (er11a0 changed the same section without a spec edit). `rationale.md` is the workflow's own design note and is updated in E-01; `CHANGELOG.md` in E-03.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git diff -- .aw/system/workflows/askme/askme.md .aw/system/workflows/askme/rationale.md` showing item 4 with (a) to (d) and the rationale paragraph, and no other section of `askme.md` changed.
  - Observed evidence:
```diff
diff --git a/.aw/system/workflows/askme/askme.md b/.aw/system/workflows/askme/askme.md
index cc70dfd0c..8b47517ca 100644
--- a/.aw/system/workflows/askme/askme.md
+++ b/.aw/system/workflows/askme/askme.md
@@ -26,9 +26,18 @@ Choose the scope from the user's request:
 4. **Use the current conversation.** With no arguments, ask the outstanding
    question in the current conversation, if there is one. Otherwise,
    examine unanswered questions in records you created or edited during
-   this session. In a shared checkout, confirm authorship before treating a
-   record or question as yours (`git log` and the record's `- Author:` line
-   settle it). Do not scan the entire repository by default.
+   this session. "Records this session created or edited" means records
+   whose edits appear in this conversation's own tool calls; establish them
+   from the conversation, not by searching. Do not scan the entire repository
+   by default: do not run `aw attention`, `aw find`, or any recursive search
+   (`grep -r`, `find`, `git log --all`) over `.aw/records` to discover
+   questions. A record found any other way is not this session's even if it
+   carries open questions. If both sources are empty, say so in one or two
+   sentences, list the three ways to point `/askme` at a subject (a question,
+   a record or set id, or an explicit request to scan), and stop without
+   asking a question. These limits apply only to the no-argument case: items 2
+   and 3 and an explicit user request to scan ("look through the repo for
+   open questions") are unaffected.

 Treat conversational arguments as instructions about the question, not
 automatically as a filename or identifier. If the reference is genuinely
diff --git a/.aw/system/workflows/askme/rationale.md b/.aw/system/workflows/askme/rationale.md
index 1aa0ddfb6..bb948068b 100644
--- a/.aw/system/workflows/askme/rationale.md
+++ b/.aw/system/workflows/askme/rationale.md
@@ -35,3 +35,8 @@ If the choice depends on a quantity (e.g. how many files or plans are affected),
 ## Incomprehension reports and free-text responses

 When a user reports incomprehension ("I have zero context here", "what is X?", "I did not understand a single word of that"), the prompt was defective. On 2026-09-08, the maintainer used the free-text option of the question tool to reply: "I wanted to pick write your own and say I did not understand a single word of your explanation." A report of incomprehension is not a decision, and recording it as a user resolution would misrepresent confusion as consent.
+
+## Repository scans on bare /askme
+
+Live trials in plan `lkn1zt` (findings `auwidn`, trial T05) showed that invoking `/askme` without arguments led multiple host and model combinations to scan the repository using `aw attention`, recursive `grep`, and `find` when no conversational question was pending. In a shared checkout, this caused agents to discover and ask open questions from plans authored by other agents or humans without confirming authorship. The no-argument scope rule therefore restricts candidate records strictly to those whose edits appear in the current conversation's own tool calls, explicitly forbids repository-wide discovery searches, and requires stopping with instructions when both conversational and session sources are empty.
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` showing the new test passing, and pasted output of the same test run against the pre-E-01 body (e.g. `git stash` of only `askme.md`, or a temporary revert) showing it failing. Produce the pre-change run WITHOUT `git stash` (shared-checkout rule): `cp .aw/system/workflows/askme/askme.md /tmp/opencode/askme.new && git show HEAD:.aw/system/workflows/askme/askme.md > .aw/system/workflows/askme/askme.md`, run the test, then `cp /tmp/opencode/askme.new .aw/system/workflows/askme/askme.md` and paste `git diff --stat -- .aw/system/workflows/askme/askme.md` proving the edit is restored. Also paste the test's `@pytest.mark.slow` line.
  - Observed evidence: Verified new test passes with restored askme.md and fails against pre-E-01 body.
    1. Passing run: `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v`
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=2670875251
rootdir: <repo_root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 4 items

tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_agents_pointer_prose_names_askme PASSED [ 25%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_and_preserves_askme_shims PASSED [ 50%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_askme_shims_rendered_from_manifest PASSED [ 75%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_no_scan_rule PASSED [100%]
============================== 4 passed in 13.04s ==============================
```
    2. Failing run against pre-E-01 body:
```
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_agents_pointer_prose_names_askme PASSED [ 25%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_and_preserves_askme_shims PASSED [ 50%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_installer_delivers_askme_no_scan_rule FAILED [ 75%]
tests/test_askme_command_delivery.py::AskmeCommandDeliveryTests::test_askme_shims_rendered_from_manifest PASSED [100%]

=================================== FAILURES ===================================
_____ AskmeCommandDeliveryTests.test_installer_delivers_askme_no_scan_rule _____

self = <tests.test_askme_command_delivery.AskmeCommandDeliveryTests testMethod=test_installer_delivers_askme_no_scan_rule>
...
>           self.assertIn(
                "whose edits appear in this conversation's own tool calls",
                installed_words,
            )
E           AssertionError: "whose edits appear in this conversation's own tool calls" not found in ...
========================= 1 failed, 3 passed in 13.00s =========================
```
    3. Restored edit check:
```
$ git diff --stat -- .aw/system/workflows/askme/askme.md
 .aw/system/workflows/askme/askme.md | 15 ++++++++++++---
 1 file changed, 12 insertions(+), 3 deletions(-)
```
    4. `@pytest.mark.slow` line in `tests/test_askme_command_delivery.py`:
```python
    @pytest.mark.slow
    def test_installer_delivers_askme_no_scan_rule(self):
```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `git diff -- CHANGELOG.md` showing the bullet under the topmost pending heading.
  - Observed evidence:
```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index ce696905a..ee219af1c 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -92,6 +92,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
 - Changed: `aw reviews decisions`, `aw record-history`, and `aw graduation` now refuse at exit 2 with an `aw.agent/v1` cannot-run outcome a selector naming no artifact in any tracked tree, while keeping legitimate empty answers at exit 0. `aw ipd recheck-readiness` moves from exit 1 to exit 2 for unresolved or non-plan selectors and now refuses a mixed invocation before re-checking or writing anything. Standing vocabulary queries remain exempt at exit 0 across all four verbs.
 - Changed: `aw show <ref>` now refuses at exit 2 with an `aw.agent/v1` cannot-run outcome a selector naming no artifact anywhere in the repository, answers exit 0 when a standing-status token or a real but non-displayed artifact has nothing to show, and no longer exits 1.
 - Changed: /askme is retained as a supported command alias instead of carrying a deprecation notice; its workflow is rewritten as a procedure-only runbook recognizing four request scopes (rewrite previous question, ask supplied question, examine specified records, use current conversation) with history moved to rationale.md; and plain-language communication requirements are installed as a shared default across all authored documents via reporting_contract and AGENTS.md.
+- Fixed: bare /askme no longer searches the repository or asks other authors' open questions when no conversational question is pending. It now limits candidate records to those edited in the current conversation, and explains how to point /askme at a subject when both conversational and session sources are empty.
 - Added: every commit and merge created by `aw` now keeps the user as author and records `AW Agent (<model>) <local+aw@domain>` as committer (or `local+tag-aw@domain` when already tagged), stamps `AW-Runner` (`aw oc run`, `aw agy run`, or `aw commit`) alongside `AW-Run` and `AW-Item` when known, exports the agent committer identity and `AW_RUNNER` into runner agent turns, and preserves commit signing by supplying `user.signingkey` from the author identity when `commit.gpgsign` is enabled with no explicit key (see `docs/commit-identity.md`).
```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted final summary lines of BOTH E-04 runs (`python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` and bare `python3 -m pytest`), each showing no failures.
  - Observed evidence: Both test runs completed with zero failures.
    1. Final summary line of `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v`:
```
============================== 4 passed in 15.49s ==============================
```
    2. Final summary line of bare `python3 -m pytest`:
```
1681 passed, 11 warnings in 144.22s (0:02:24)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Tests assert observable behavior (the installed file an installer run produced), never production source read with `inspect`, `ast` or regex (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). Commit only files you changed, through `aw commit 9vttho -- <paths>`, and verify `git diff --cached --name-only` lists only your paths; never `git add -A`, never `git stash`, never push or tag. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Lifecycle: after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize 9vttho --actor <agent/model> --message <summary> --apply` itself.
