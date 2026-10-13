# IPD: Retarget the two stale severity-tier citations left pointing at cli-output-contract Section 3.1 after u28vqb renumbered it to 3.2

- Date: 2026-10-11
- Kind: child
- Concern: backlog `2cqs11` warned that approved plan `u28vqb` would collide with the existing `docs/cli-output-contract.md` `### 3.1 Severity Tier Contract and Gate Semantics`, either by duplicating the heading or by renumbering a cross-referenced section. `u28vqb` has since EXECUTED (commit `e0b8d9bb8`) and took the renumber option: the run-execution vocabulary is now `### 3.1 Run-Execution Exit Vocabulary` and the severity section is now `### 3.2 Severity Tier Contract and Gate Semantics`. The heading collision is therefore resolved, and the only measured residue is two code comments in `agent_workflows/check_engine.py` that still cite "Section 3.1" for severity-tier content that now lives in Section 3.2.
- Scope: IN: (1) retarget the two `check_engine.py` comments (the `check.plan-date-filename` rationale beginning "WHY `info` AND NOT `warning`" and the `check.ipd-carrier-ungated` rationale quoting "to author a rule that reports diagnostics without ever failing any gate or check") from Section 3.1 to Section 3.2 of `docs/cli-output-contract.md`, citing the section by its title as well as its number so the next renumber is detectable; (2) re-measure the whole tree at execution time for any other live reference to the severity contract by the old number, and retarget any found the same way (an edit outside Scope-Paths is made and then justified at finalize with `--scope-reason`, not a reason to stop). OUT: any change to `docs/cli-output-contract.md` headings or prose (already correct at HEAD); any edit to executed plan `u28vqb` (an executed record is never rewritten; F-04 here records its stale F-01 framing instead); any rule behavior or severity change.
- Scope-Paths: agent_workflows/check_engine.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: 2cqs11
- Set: runexitvocab
- Order: 2
- Highest E allocated: 03
- Author: OpenCode Claude Opus
- Id: p1kbhl
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-12 draft (OpenCode Claude Opus): created.
- 2026-10-12 to-review (OpenCode Claude Opus): authored from backlog 2cqs11 after re-measuring HEAD; collision already resolved by u28vqb's execution, residue is two stale code-comment citations.

## Goal

Make every live in-tree pointer to the severity tier contract name the section it actually lives in (`docs/cli-output-contract.md` Section 3.2) now that executed plan `u28vqb` renumbered it, so a reader following a `check_engine.py` rationale lands on the severity rules and not on the run-exit vocabulary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure, retarget, regress

- [x] E-01 Re-measure HEAD before editing: list the `^## |^### ` headings of `docs/cli-output-contract.md` under Section 3, and run `rg -n "3\.1" --glob '!.aw/records/plans/executed/**' --glob '!.aw/records/runs/**' --glob '!.aw/state/**' --glob '!.aw/records/research/**' .` filtered to lines mentioning `cli-output-contract`, severity, `warning` or `info`, and classify each hit (run-exit citation to 3.1 is correct; severity citation to 3.1 is stale). STOP and report (do not edit) only if Section 3.2 is no longer `Severity Tier Contract and Gate Semantics`, since then the retarget destination itself is wrong. A further stale severity citation found OUTSIDE `agent_workflows/check_engine.py` is NOT a stop condition: retarget it in E-02 the same way and justify the path at finalize with `--scope-reason <path>=<why>` (the scope fence is a declaration, not a stop directive).
  - Depends on: none
  - Expected outcome: the heading census shows `### 3.1 Run-Execution Exit Vocabulary` then `### 3.2 Severity Tier Contract and Gate Semantics`, and every stale severity citation is listed by path (at authoring and re-measured at review, HEAD `924e40840`, exactly the two `check_engine.py` comments; re-derive, do not assume).
  - Execution state: performed
- [x] E-02 In `agent_workflows/check_engine.py`, change the two comment citations from "Section 3.1" / "section 3.1" to "Section 3.2 (Severity Tier Contract and Gate Semantics)", leaving every quoted phrase, rule key, `RuleSpec` value and all surrounding text unchanged. The inserted title adds about 45 characters to lines already 99 and 101 characters wide, so re-wrap WITHIN each of the two comment blocks as needed to keep the surrounding width; re-wrapping is the only other permitted change. Retarget any further stale citation E-01 found the same way.
  - Depends on: E-01
  - Expected outcome: `git diff` on `agent_workflows/check_engine.py` shows changes confined to the two comment blocks (every changed line starts with `#` after indentation) and no code change; the comment text, read with line breaks removed, differs only by the section number and inserted title.
  - Execution state: performed
- [x] E-03 Run the check-engine regression tests and the severity contract tests to confirm the comment-only edit changed no behavior.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_check_engine.py tests/test_check_engine_plan_date_filename.py tests/test_severity_tier_contract.py tests/test_exit_vocabulary_boundary.py` reports no failures (69 passed at review HEAD `924e40840`, context only), and `git diff --check` is empty.
  - Execution state: performed

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
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Adding a test that pins section numbers inside code comments: that would be a code-pinning test, which the repository's test policy forbids.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Renaming or re-anchoring any `docs/cli-output-contract.md` heading: the doc is already correct and every link resolves (F-02).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none. One file, comment-only.
- Under-scope: none known; E-01 re-measures, and any further stale severity citation is retargeted in E-02 and justified at finalize with `--scope-reason`.

## Required tests / validation

- `python3 -m pytest tests/test_check_engine.py tests/test_check_engine_plan_date_filename.py tests/test_severity_tier_contract.py tests/test_exit_vocabulary_boundary.py` passes (V-03).
- The tree-wide grep shows no remaining severity citation to Section 3.1 (V-02).

## Spec / documentation sync

N/A: no spec or user-facing document changes. `docs/cli-output-contract.md` is already correct at HEAD (F-01, F-02); only code comments are touched, so no CHANGELOG entry is warranted.

## Open questions

### OQ-01: Should the backlog's recommended action (pick 3.2 or a titled subsection before running runexitvocab) still be applied?

- Blocking: no
- Status: resolved
- Owner: plan author (confirmed by /plan-review 2026-10-12)
- Resolution or deferral rationale: No. It was overtaken by events: `u28vqb` executed and itself moved severity to 3.2 and placed the run vocabulary at 3.1 (F-01), with every doc link resolving (F-02). The only surviving harm is two stale code-comment citations (F-03), which this plan fixes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `^## |^### ` heading list for Section 3 of `docs/cli-output-contract.md` and the filtered tree-wide `3\.1` grep output, and state which lines are severity citations.
  - Observed evidence:
    1. Heading list for Section 3 of `docs/cli-output-contract.md`:
    ```
    163:## 3. Exit Code Semantics
    182:### 3.1 Run-Execution Exit Vocabulary
    205:#### Disagreement on Codes 3 and 4
    213:### 3.2 Severity Tier Contract and Gate Semantics
    217:#### The Exit-Code Contract (Findings Gates)
    227:#### The Second Contract: Per-Gate Lifecycle Behavior
    239:#### Summary for Rule Authors
    ```

    2. Filtered tree-wide `3\.1` grep output:
    ```
    $ rg -n "3\.1" --glob '!.aw/records/plans/executed/**' --glob '!.aw/records/runs/**' --glob '!.aw/state/**' --glob '!.aw/records/research/**' . | grep -E "cli-output-contract|severity|warning|info"
    ./README.md:202:structured), or `--no-color` (human, no ANSI). Exit codes for standard commands follow a three-state classification: `0` clean, `1` findings, `2` cannot run (run-execution commands use a wider vocabulary; see [CLI Output Mode Contract Section 3.1](docs/cli-output-contract.md#31-run-execution-exit-vocabulary)). See the [Human TTY guide](docs/cli-human-guide.md), the
    ./docs/cli-output-contract.md:178:- **Verbs emitting bare JSON or non-agent payloads**: Verbs that do not emit `aw.agent/v1` records (such as `run_cli._emit_error` machine payloads on `aw runs` commands, which emit bare JSON dictionaries without envelope fields) are not bound by the three-state rule. Across the 164 command declarations in the inventory, 10 declarations declare exit codes outside `{0, 1, 2}`, all belonging to the run-execution and lifecycle family (`aw run`, `aw runs`, `aw oc runipd`, `aw agy runipd`, and `aw ipd execute-set`). These commands carry a separate, wider exit vocabulary documented in Section 3.1 below. The two vocabularies are not unified into a single schema.
    ./docs/cli-output-contract.md:182:### 3.1 Run-Execution Exit Vocabulary
    ./docs/cli-human-guide.md:83:Commands in the run-execution family (`aw run` and `aw runs`) use a wider exit vocabulary (codes 0 through 7) to distinguish operational and workflow states; see [CLI Output Mode Contract Section 3.1](cli-output-contract.md#31-run-execution-exit-vocabulary) for details.
    ./docs/cli-migration.md:124:- Confirm the exit codes your script branches on still mean the same thing: for standard commands, `0` clean, `1` findings, `2` cannot run. (If your script invokes run-execution commands such as `aw run` or `aw runs`, verify its handling against the wider exit vocabulary in [CLI Output Mode Contract Section 3.1](cli-output-contract.md#31-run-execution-exit-vocabulary)).
    ./docs/cli-agent-protocol.md:29:| `exit` | The agent record exit classification: `0`, `1`, or `2` (a contract of the `aw.agent/v1` envelope; non-agent run commands carry a wider exit vocabulary documented in [CLI Output Mode Contract Section 3.1](cli-output-contract.md#31-run-execution-exit-vocabulary)). |
    ./DECISIONS.md:2218:- **Decision:** (1) Rewire the `/assess local-leaks` lens to CONSUME `--agent`: the canonical invocation is `aw check-local-leaks . --agent --warn` (+ `--wheel`/`--history`), documented as one tab-separated `location\trule\tseverity` record per finding on stdout (exit 1 if any fail); triage reads the engine's `severity` field off the records instead of re-classifying, while the human JUDGMENT step (which emails/usernames are intended-public vs leaks) stays and cites P12. (2) Add a `Leak-sanitizer awareness` section to the installer-stamped `AGENTS.md` template so every repo (with or without a hook) is told to run `aw sanitize --agent` before hand-judging identity leaks. (3) Add a SEPARATE, off-the-default-path writer `engine.create_local_leaks_backstop(..., install_ci, install_hook, dry_run)` that `/setup-repo` gates behind two explicit interactive asks (user ALWAYS asked; hook prompt default `[Y/n]`, CI prompt default `[y/N]`; a decline installs nothing). The target-repo CI template installs `agent-workflows` UNPINNED on Python 3.12 (with an air-gapped/pinned caveat); the pre-commit hook is whole-tree (`pass_filenames: false`) and, if the target already has a `.pre-commit-config.yaml`, is NEVER edited (the hook block is handed back to merge). No-clobber, dry-run aware; the always-on `create_setup_artifacts` created-count is unchanged. This completes the leak-sanitizer Set (Orders 1-3).
    ./agent_workflows/check_engine.py:289:    # WHY `info` AND NOT `warning`: `docs/cli-output-contract.md` Section 3.1 states that `warning`
    ```
    (plus line 788 in `agent_workflows/check_engine.py`, which continues the `docs/cli-output-contract.md` citation from line 787: `section 3.1: "to author a rule that reports diagnostics without ever failing any gate or check, register the rule with severity `info`"`).

    3. Classification:
    The citations in `README.md`, `docs/cli-output-contract.md`, `docs/cli-human-guide.md`, `docs/cli-migration.md`, and `docs/cli-agent-protocol.md` correctly reference the run-execution exit vocabulary in Section 3.1. `DECISIONS.md` mentions `severity` in the leak-sanitizer decision and Python `3.12`. Only the two comment citations in `agent_workflows/check_engine.py` (lines 289 and 788) are severity-tier citations to Section 3.1 and thus stale.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/check_engine.py` showing every changed line is a comment line inside the two named blocks (the `check.plan-date-filename` and `check.ipd-carrier-ungated` rationales) and no non-comment change, plus the diff of any further path E-01 found, then paste `rg -n "Section 3\.1|section 3\.1" agent_workflows/check_engine.py` returning nothing and `rg -n "Section 3\.2" agent_workflows/check_engine.py` returning the two retargeted lines.
  - Observed evidence:
    1. `git diff agent_workflows/check_engine.py`:
    ```diff
    diff --git a/agent_workflows/check_engine.py b/agent_workflows/check_engine.py
    index 14d783c05..402133243 100644
    --- a/agent_workflows/check_engine.py
    +++ b/agent_workflows/check_engine.py
    @@ -286,11 +286,12 @@ RULE_REGISTRY: Dict[str, RuleSpec] = {
         # IPD wyk11f (backlog mt6j1p): advisory check comparing each clustered plan's filename date
         # against its own `- Date:` metadata.
         #
    -    # WHY `info` AND NOT `warning`: `docs/cli-output-contract.md` Section 3.1 states that `warning`
    -    # fails the exit-code gate exactly as an `error` does, and that `info` is the ONLY severity tier
    -    # that does not contribute to exit 1. The violating population is measured empty, so a gating
    -    # rule would fail CI on an unrelated future change before any true positive was evaluated. `info`
    -    # ships the rule as an advisory tripwire without changing any exit code today.
    +    # WHY `info` AND NOT `warning`: `docs/cli-output-contract.md` Section 3.2 (Severity Tier
    +    # Contract and Gate Semantics) states that `warning` fails the exit-code gate exactly as an
    +    # `error` does, and that `info` is the ONLY severity tier that does not contribute to exit 1.
    +    # The violating population is measured empty, so a gating rule would fail CI on an unrelated
    +    # future change before any true positive was evaluated. `info` ships the rule as an advisory
    +    # tripwire without changing any exit code today.
         #
         # Invariant is `""`: no catalog invariant in spec `pqsx96` covers agreement between a filename
         # date and its own front-matter `- Date:` (I-09 is filename grammar shape; I-16/I-17 are setid
    @@ -785,10 +786,11 @@ RULE_REGISTRY: Dict[str, RuleSpec] = {
         # asks for a tier that will not "turn `aw check` red for authors who did nothing wrong" and concludes
         # `warning`. That conclusion is falsified on evidence: `artifact_core.drift_exit_code` returns 1 for
         # every severity except `info` (error -> 1, warning -> 1, info -> 0; docs/cli-output-contract.md
    -    # section 3.1: "to author a rule that reports diagnostics without ever failing any gate or check,
    -    # register the rule with severity `info`"). A `warning` tier would exit 1 on 19 pending plans and
    -    # fail CI (which enforces `aw check plans` fail-closed). Precedent: `_CARRIER_LEGACY_SEVERITY` in
    -    # this same module ("MISSING -> `info`, the ONLY non-failing severity", citing `check.stale-index-missing`).
    +    # Section 3.2 (Severity Tier Contract and Gate Semantics): "to author a rule that reports
    +    # diagnostics without ever failing any gate or check, register the rule with severity `info`").
    +    # A `warning` tier would exit 1 on 19 pending plans and fail CI (which enforces `aw check plans`
    +    # fail-closed). Precedent: `_CARRIER_LEGACY_SEVERITY` in this same module ("MISSING -> `info`,
    +    # the ONLY non-failing severity", citing `check.stale-index-missing`).
         #
         # Invariant `""` DELIBERATELY. Do not claim I-07 (release gating / uncarried obligations) or I-08
         # (cross-IPD dependency statements). This rule reports neither a broken gate nor a malformed statement:
    ```

    2. Diff of further paths found by E-01: None (no other stale severity citations exist).

    3. `rg -n "Section 3\.1|section 3\.1" agent_workflows/check_engine.py`:
    Returned exit code 1 (no matches).

    4. `rg -n "Section 3\.2" agent_workflows/check_engine.py`:
    ```
    289:    # WHY `info` AND NOT `warning`: `docs/cli-output-contract.md` Section 3.2 (Severity Tier
    789:    # Section 3.2 (Severity Tier Contract and Gate Semantics): "to author a rule that reports
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste the actual pytest summary line for the four named test files showing none failed, and the (empty) `git diff --check` output.
  - Observed evidence:
    1. Pytest summary line:
    ```
    69 passed in 16.88s
    ```
    (Full invocation: `python3 -m pytest tests/test_check_engine.py tests/test_check_engine_plan_date_filename.py tests/test_severity_tier_contract.py tests/test_exit_vocabulary_boundary.py`)

    2. `git diff --check` output:
    (empty, exit code 0)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval.

Execution contract:
- Open questions: OQ-01 is resolved; none are open.
- Scope fence: `- Scope-Paths:` is a declaration, not a stop condition. An out-of-scope edit (for example a further stale citation E-01 finds) is made and justified at finalize with `--scope-reason <path>=<why>`; a declared path left unmodified needs `--scope-ack`. The only stop condition is E-01's (Section 3.2 no longer the severity section).
- Commit only the edited source path(s) through `aw commit p1kbhl -- <paths>`; never `git add -A`; never push. Check `git diff --cached --name-only` before committing and re-check after any failed commit. The plan file's own E/V state travels with the lifecycle transition.
- You MUST paste ACTUAL runner output; never claim a result you did not run, and never mark a `V-*` `pass` from its E-item checkmark.
- Lifecycle: begin with `aw ipd begin`. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan moves to `executed/` through the tooled lifecycle, never a hand `git mv`. Under `aw oc run` / `aw agy run` the driver self-finalizes and the executor does NOT run `aw ipd finalize`; when executing by hand outside a runner, the executor runs `aw ipd finalize p1kbhl`.
