# IPD: Retarget the two stale severity-tier citations left pointing at cli-output-contract Section 3.1 after u28vqb renumbered it to 3.2

- Date: 2026-10-11
- Kind: child
- Concern: backlog `2cqs11` warned that approved plan `u28vqb` would collide with the existing `docs/cli-output-contract.md` `### 3.1 Severity Tier Contract and Gate Semantics`, either by duplicating the heading or by renumbering a cross-referenced section. `u28vqb` has since EXECUTED (commit `e0b8d9bb8`) and took the renumber option: the run-execution vocabulary is now `### 3.1 Run-Execution Exit Vocabulary` and the severity section is now `### 3.2 Severity Tier Contract and Gate Semantics`. The heading collision is therefore resolved, and the only measured residue is two code comments in `agent_workflows/check_engine.py` that still cite "Section 3.1" for severity-tier content that now lives in Section 3.2.
- Scope: IN: (1) retarget the two `check_engine.py` comments (the `check.plan-date-filename` rationale beginning "WHY `info` AND NOT `warning`" and the `check.ipd-carrier-ungated` rationale quoting "to author a rule that reports diagnostics without ever failing any gate or check") from Section 3.1 to Section 3.2 of `docs/cli-output-contract.md`, citing the section by its title as well as its number so the next renumber is detectable; (2) re-measure the whole tree at execution time for any other live reference to the severity contract by the old number, and stop and report if one exists outside this plan's Scope-Paths. OUT: any change to `docs/cli-output-contract.md` headings or prose (already correct at HEAD); any edit to executed plan `u28vqb` (an executed record is never rewritten; F-03 here records its stale F-01 framing instead); any rule behavior or severity change.
- Scope-Paths: agent_workflows/check_engine.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: 2cqs11
- Set: runexitvocab
- Order: 2
- Highest E allocated: 03
- Author: OpenCode Claude Opus
- Id: p1kbhl

## Workflow history

- 2026-10-12 draft (OpenCode Claude Opus): created.
- 2026-10-12 to-review (OpenCode Claude Opus): authored from backlog 2cqs11 after re-measuring HEAD; collision already resolved by u28vqb's execution, residue is two stale code-comment citations.

## Goal

Make every live in-tree pointer to the severity tier contract name the section it actually lives in (`docs/cli-output-contract.md` Section 3.2) now that executed plan `u28vqb` renumbered it, so a reader following a `check_engine.py` rationale lands on the severity rules and not on the run-exit vocabulary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure, retarget, regress

- [ ] E-01 Re-measure HEAD before editing: list the `^## |^### ` headings of `docs/cli-output-contract.md` under Section 3, and run `rg -n "3\.1" --glob '!.aw/records/plans/executed/**' --glob '!.aw/records/runs/**' --glob '!.aw/state/**' --glob '!.aw/records/research/**' .` filtered to lines mentioning `cli-output-contract`, severity, `warning` or `info`. STOP and report (do not edit) if Section 3.2 is no longer `Severity Tier Contract and Gate Semantics`, or if any live reference to the severity contract by the old number exists outside `agent_workflows/check_engine.py`.
  - Depends on: none
  - Expected outcome: the heading census shows `### 3.1 Run-Execution Exit Vocabulary` then `### 3.2 Severity Tier Contract and Gate Semantics`, and the only stale severity citations are the two `check_engine.py` comments named in Scope.
  - Execution state: pending
- [ ] E-02 In `agent_workflows/check_engine.py`, change the two comment citations from "Section 3.1" / "section 3.1" to "Section 3.2 (Severity Tier Contract and Gate Semantics)", leaving every quoted phrase, rule key, `RuleSpec` value and all surrounding text unchanged.
  - Depends on: E-01
  - Expected outcome: `git diff` on `agent_workflows/check_engine.py` shows exactly two changed comment lines and no code change.
  - Execution state: pending
- [ ] E-03 Run the check-engine regression tests and the severity contract tests to confirm the comment-only edit changed no behavior.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_check_engine.py tests/test_check_engine_plan_date_filename.py tests/test_severity_tier_contract.py tests/test_exit_vocabulary_boundary.py` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). The two target comments are therefore identified by the rule key they annotate (`check.plan-date-filename`, `check.ipd-carrier-ungated`) and a quoted phrase.
- Executed plans are never rewritten (AGENTS.md execution contract); a stale finding inside one is recorded by a later plan, not corrected in place.
- Commits go through `aw commit <plan> -- <paths>`; the suite runs bare (`python3 -m pytest`), narrowed runs by named test files.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | **THE BACKLOG ITEM'S COLLISION IS ALREADY RESOLVED AT HEAD.** `u28vqb` is in `.aw/records/plans/executed/` with `- Status: executed` (history: "2026-10-08 executed (aw agy run ...)"), and its commit `e0b8d9bb8` ("chore(runexitvocab): u28vqb scope three-state exit claim and declare run exit vocabulary") is the commit that introduced the `### 3.2 Severity` heading. Heading census now: `## 3. Exit Code Semantics`, `### 3.1 Run-Execution Exit Vocabulary`, `#### Disagreement on Codes 3 and 4`, `### 3.2 Severity Tier Contract and Gate Semantics` and its three `####` children. No duplicate heading exists. So the backlog's RECOMMENDED ACTION ("pick the next free number or a titled subsection, and refresh F-01, before runexitvocab is run") can no longer be applied as written; the executor chose the renumber branch the item warned about | `grep -n "^##\+ " docs/cli-output-contract.md`; `git log -S"### 3.2 Severity" -- docs/cli-output-contract.md` |
| F-02 | **ALL FOUR DOC POINTERS RESOLVE TO THE NEW ANCHOR, SO THE RENUMBER BROKE NO MARKDOWN LINK.** `README.md`, `docs/cli-human-guide.md`, `docs/cli-migration.md` and `docs/cli-agent-protocol.md` all link `cli-output-contract.md#31-run-execution-exit-vocabulary`, which matches the new `### 3.1` heading; spec `25kzda` 5.6 row 4 also cites Section 3.1 for the run tables, correctly. No markdown link anywhere targets a severity anchor (`rg severity-tier` returns only `tests/test_severity_tier_contract.py`'s docstring and CHANGELOG prose with no section number) | `rg -n "cli-output-contract" ... \| rg "3\.[12]\|#3"` transcript |
| F-03 | **TWO CODE COMMENTS STILL CITE THE OLD NUMBER FOR SEVERITY CONTENT, AND THAT IS THE WHOLE RESIDUE.** `check_engine.py`'s `check.plan-date-filename` comment says "`docs/cli-output-contract.md` Section 3.1 states that `warning` fails the exit-code gate exactly as an `error` does" (added by `7685367a3`, plan `wyk11f`), and the `check.ipd-carrier-ungated` comment quotes "docs/cli-output-contract.md section 3.1: \"to author a rule that reports diagnostics without ever failing any gate or check, register the rule with severity `info`\"" (added by `2d6247e41`, plan `rpw4sb`). Both quoted sentences now live in Section 3.2 (doc lines starting "- `warning`: Evaluates to failing" and "Practical consequence: to author a rule"). Following either citation now lands a reader on the run-exit tables. The `3.1` references in `tests/test_plan_review_feasibility_rule.py` are about the plan-review workflow file, not this document, and are out of scope | `rg -n "Section 3\.1\|section 3\.1" agent_workflows/ tests/`; `git log -S` for each comment |
| F-04 | **`u28vqb`'s F-01 FRAMING IS STALE IN AN EXECUTED RECORD AND IS NOT EDITED HERE.** The backlog's second drift (F-01 asserting `rwvzqm` pending and Section 3 unamended) was true when `u28vqb` was reviewed and false by its execution; `rwvzqm` is in `executed/`. Rewriting an executed plan's findings is forbidden by the execution contract, and the shipped Section 3 text is what matters to readers. This finding is the durable record of the drift | `ls .aw/records/plans/executed/*rwvzqm*`; AGENTS.md "Never change what a plan already in executed/ RECORDS" |

## Proposed changes (ordered, validatable)

1. Re-measure the heading census and the tree-wide citation set (E-01), stopping on any surprise.
2. Retarget the two `check_engine.py` comments to Section 3.2 by number and title (E-02).
3. Run the named regression tests (E-03).

## Deferred / out of scope (with reason)

- Editing `u28vqb`'s F-01/F-15 text: forbidden for an executed plan (F-04).
- Adding a test that pins section numbers inside code comments: that would be a code-pinning test, which the repository's test policy forbids.
- Renaming or re-anchoring any `docs/cli-output-contract.md` heading: the doc is already correct and every link resolves (F-02).

## Scope check

- Over-scope: none. One file, comment-only.
- Under-scope: none known; E-01 re-measures and stops if a further stale reference appears outside Scope-Paths.

## Required tests / validation

- `python3 -m pytest tests/test_check_engine.py tests/test_check_engine_plan_date_filename.py tests/test_severity_tier_contract.py tests/test_exit_vocabulary_boundary.py` passes (V-03).
- The tree-wide grep shows no remaining severity citation to Section 3.1 (V-02).

## Spec / documentation sync

N/A: no spec or user-facing document changes. `docs/cli-output-contract.md` is already correct at HEAD (F-01, F-02); only code comments are touched, so no CHANGELOG entry is warranted.

## Open questions

### OQ-01: Should the backlog's recommended action (pick 3.2 or a titled subsection before running runexitvocab) still be applied?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. It was overtaken by events: `u28vqb` executed and itself moved severity to 3.2 and placed the run vocabulary at 3.1 (F-01), with every doc link resolving (F-02). The only surviving harm is two stale code-comment citations (F-03), which this plan fixes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `^## |^### ` heading list for Section 3 of `docs/cli-output-contract.md` and the filtered tree-wide `3\.1` grep output, and state which lines are severity citations.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/check_engine.py` showing exactly two comment lines changed and no non-comment change, then paste `rg -n "Section 3\.1|section 3\.1" agent_workflows/check_engine.py` returning nothing and `rg -n "Section 3\.2" agent_workflows/check_engine.py` returning the two retargeted lines.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the actual pytest summary line for the four named test files showing all passed and none failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Follow the IPD lifecycle (`aw ipd begin` / finalize through the runner or `aw ipd set`), commit only `agent_workflows/check_engine.py` and this plan through `aw commit p1kbhl -- <paths>`, never push, and move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and V-01 through V-03 carry pasted evidence with `Result: pass`.
