# IPD: Refresh the run_analytics_cli query-summary comment now that a --fields projection preserves next

- Date: 2026-10-12
- Kind: child
- Concern: The comment block above the `render_summary` call in `run_analytics_cli._emit_query_agent` justifies the call's no-context shape with "The summary takes no field projection because `next` is not in `agent_schema._PRESERVED_FIELDS`, so projecting this record could drop the paging continuation". Plan `6rcby1` (executed) added `next` to `_PRESERVED_FIELDS`, and the renderer independently retains `next` on a summary (`AgentRenderer.render_summary`, "IPD okiso1 E-03"), so that causal claim is now false and the comment misdescribes live behavior.
- Scope: Rewrite that one comment block so it describes the post-fix reality: a projection is now a no-op on this summary record, the call is kept as shipped, and the load-bearing reason for the call's SHAPE is that the summary carries the query engine's counts (the neighbouring `THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S` block), not a paging workaround. Comment lines only; no executable statement in `agent_workflows/run_analytics_cli.py` changes, the `render_summary` call and its arguments stay byte-identical, and no test, spec, or doc is touched.
- Scope-Paths: agent_workflows/run_analytics_cli.py, .aw/records/plans/pending/20261012-d6u2hz-01-gbizqt-refresh-the-run-analytics-cli-query-summary-comment-now-that.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: d6u2hz
- Set: d6u2hz
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: gbizqt
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-003
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog d6u2hz; prerequisite 6rcby1 confirmed executed; F-01..F-05 measured at HEAD 114af0797.

## Goal

Make the comment above `_emit_query_agent`'s `render_summary` call true again, describing why the call has its shape in terms that do not depend on a since-fixed projection defect, so the comment stops tracking a defect that no longer exists (third invalidation in the `gygujf` -> `mcdvx0` -> `6rcby1` lineage the backlog item records).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline, then rewrite the comment

- [x] E-03 Record the BEFORE baseline that E-02 compares against, with the tree still unedited (perform this FIRST; it carries the higher id only because it was added at review). (1) Capture `aw runs query overview --agent --fields cmd` and `aw runs query overview --agent` stdout to files under the gitignored `.aw/state/`. (2) Run `python3 -m pytest -o addopts="" -q tests/test_run_analytics_cli.py` and record its summary line. This file holds the outcome pin for this exact call path (F-05: `test_emit_query_agent_bounded_preserves_next_under_fields_projection` drives `_emit_query_agent` with `--fields cmd` and a `next`), which the `overview` captures do not reach, because in a repo without an analytics cache `overview` emits a summary with no `next`. (3) Run the bare suite `python3 -m pytest` and record its summary line and the named FAILURE SET.
  - Depends on: none
  - Expected outcome: two saved captures, the targeted-file summary line, and the bare-suite summary with its named failure set, all taken before any edit.
  - Execution state: performed


- [x] E-01 Replace the comment block in `run_analytics_cli._emit_query_agent` that begins `# THE SUMMARY IS RENDERED WITHOUT THE FIELD PROJECTION, DELIBERATELY, TO PRESERVE PAGINATION.` and ends immediately above `parts.append(` with a block that: (a) leads with a capitalized claim line in the file's existing style stating the summary is rendered from the engine's counts and its call is kept as shipped; (b) states that a `--fields` projection is now a no-op on this record, because `agent_schema._PRESERVED_FIELDS` retains `total`/`emitted`/`omitted` and `next` (plan `6rcby1`, backlog `kkjrqr`) and `AgentRenderer.render_summary` retains `next` on a summary regardless; (c) says the shape is justified by the counts reason given in the `THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S` block above, by pointing at it rather than repeating it; (d) keeps a one-line history note that earlier versions of this call worked around a crash (`gygujf`/`3f4ayi`) and then a dropped `next` (`6rcby1`/`kkjrqr`), both fixed. Before editing, RE-MEASURE F-02 (the projection-equivalence probe in Findings); if any projection now changes the record, STOP and report instead of writing (b), because the rationale would be false. Do not touch the `render_summary` call, its arguments, or any other line.
  - Depends on: E-03
  - Expected outcome: The block no longer contains the phrase "`next` is not in `agent_schema._PRESERVED_FIELDS`" or any claim that projecting could drop the paging continuation; it states (a)-(d); `git diff -- agent_workflows/run_analytics_cli.py` contains only comment or blank `+`/`-` lines.
  - Execution state: performed

### Task group 2: prove inertness

- [x] E-02 Prove the change is behavior-neutral as the last act before commit, against the E-03 baseline. FIRST, re-capture `aw runs query overview --agent --fields cmd` and `aw runs query overview --agent` after E-01 and `diff` each against its E-03 capture. SECOND, re-run `python3 -m pytest -o addopts="" -q tests/test_run_analytics_cli.py` and require the same summary as E-03. THIRD, run the suite BARE as `python3 -m pytest` after E-01, record its summary line and the named FAILURE SET; the bar is that it equals E-03's failure set (do NOT require green, do NOT fix or `TZ`-mask any pre-existing failure, which belongs to other parties). FOURTH, mechanically confirm every `+`/`-` line in `git diff -- agent_workflows/run_analytics_cli.py` matches `^[+-]\s*#` or `^[+-]\s*$`, and that `git diff --stat` names no other source file.
  - Depends on: E-01, E-03
  - Expected outcome: Both command-output pairs byte-identical; the targeted file's summary unchanged; identical named failure sets before and after; a comment-only diff touching only `agent_workflows/run_analytics_cli.py`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Comment style in `agent_workflows/run_analytics_cli.py` leads with a capitalized claim line then justifies it (`THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S, and the distinction is load-bearing.`, `A CAVEAT IS PART OF THE ANSWER.`); the replacement keeps that shape.
- Code comments are exempt from the no-dash rule (execution contract); no effort is spent avoiding them.
- P16 (`GUIDING_PRINCIPLES`) forbids a test that pins comment text, so no comment-text test is added; the comment is verified by reading (V-01) and the change by an inertness proof (V-02).
- Suite runs BARE as `python3 -m pytest` per AGENTS.md repo-local contract; no `-n0`, extra `-q`, or `-p no:randomly`.

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-01 | Prerequisite satisfied: `6rcby1` is executed and `next` is in `_PRESERVED_FIELDS`. The backlog item's "DO NOT START THIS UNTIL `6rcby1` IS EXECUTED" gate is met. | `.aw/records/plans/executed/20261001-kkjrqr-01-6rcby1-preserve-a-summary-s-next-paging-continuation-through-a-fiel.ipd.md` carries `- Status: executed`. `agent_schema._PRESERVED_FIELDS = _MANDATORY_FIELDS \| {"applied", "total", "emitted", "omitted", "next"}` at HEAD `114af0797`. |
| F-02 | A projection is now a NO-OP on this summary record, so the comment's first justification is false, not merely weakened. | At HEAD `114af0797`, `AgentRenderer().render_summary('runs query', total=5, emitted=2, omitted=3, outcome='partial', exit_code=0, next_cmd='aw runs query metrics --limit 5', complete=False, context=OutputContext(mode=OutputMode.AGENT, fields=f))` equals the no-context rendering for `f` in `['cmd']`, `['total']`, `['outcome']`, `['a']` (all printed `True`); the unprojected record is `{"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"partial","exit":0,"total":5,"emitted":2,"omitted":3,"complete":false,"next":"aw runs query metrics --limit 5"}`. |
| F-03 | `next` is retained by TWO independent mechanisms, so the replacement comment should name both rather than credit only `6rcby1`. `AgentRenderer.render_summary` re-adds `next` (and `diagnostics`) after `filter_record_fields` under the comment "IPD okiso1 E-03: retain next and diagnostics on a summary regardless of projection". | `agent_workflows/renderers.py`, `AgentRenderer.render_summary`; introduced in commit `a2f55c630` ("okiso1: make aw find --agent emit a real aw.agent/v1 record stream ..."). |
| F-04 | The surviving justification is about the summary's COUNTS, already stated in the neighbouring block: "`render_stream` derives `omitted` from ITS OWN `--limit` truncation ... So the items are rendered individually and the summary is built from `result.total`/`result.emitted`/`result.omitted`". Strictly, that reason justifies calling `render_summary` with engine counts instead of `render_stream`; it does not by itself require omitting `ctx`. Given F-02, omitting `ctx` is now merely equivalent. The comment must say this honestly rather than invent a projection reason. | `_emit_query_agent`, block beginning `# THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S`. |
| F-05 | The existing behavioral pin `test_emit_query_agent_bounded_preserves_next_under_fields_projection` (added by `mcdvx0` E-04) still passes as an OUTCOME test, but its recorded falsifier (pass `ctx`, observe `next` missing) no longer fails because of F-02/F-03. The test still asserts a true, user-relevant property and needs no change; it is noted so the executor does not misread a non-failing falsifier as a defect. | `tests/test_run_analytics_cli.py::RunAnalyticsCliUxTests::test_emit_query_agent_bounded_preserves_next_under_fields_projection`; `mcdvx0` V-04 falsifier output `'next' not found in {...}` predates `6rcby1`. |

## Proposed changes (ordered, validatable)

0. E-03: record the before-baseline (validated by V-03).
1. E-01: rewrite the one comment block in `_emit_query_agent` per F-02..F-04 (validated by V-01).
2. E-02: prove byte-identical output, unchanged failure set, and comment-only diff (validated by V-02).

## Deferred / out of scope (with reason)

- CHANGING the `render_summary` call to pass `ctx` (now equivalent per F-02) is declined: the backlog item states "the call shape is right; only its first justification expires", and a code change would turn a prose fix into a behavior change with its own validation burden.
  - Carrier-Declined: No future work exists; the call is correct as written, and a carrier would imply someone should change it.
- Updating `test_emit_query_agent_bounded_preserves_next_under_fields_projection` or its docstring is declined (F-05): it pins a true outcome and does not mention the comment's rationale.
  - Carrier-Declined: The test is correct; nothing remains to do.

## Scope check

- Over-scope: none. One comment block in one file.
- Under-scope: none. Every claim in the stale block is replaced; the neighbouring counts block is already accurate and is referenced, not edited.

## Required tests / validation

No test can or may pin comment text (P16), and no new behavior exists to test. Validation is: V-01 reads the new block against (a)-(d) and re-runs the F-02 probe at commit time; V-02 proves inertness by byte-identical command output, an unchanged bare-suite failure set, and a mechanically comment-only diff. The existing outcome test (F-05) continues to run in the suite.

## Spec / documentation sync

N/A. No spec governs an internal code comment and no user-facing document describes this call; `docs/cli-agent-protocol.md` and `docs/cli-output-contract.md` were already updated for `next` retention by `6rcby1`. No `.spec.md` is touched.

## Open questions

### OQ-01: Should the replacement say the call omits `ctx` "because the counts must be the engine's, full stop", as the backlog item suggests?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, refining the suggestion without changing the item's requirement (describe post-fix reality, not a workaround). F-04: the counts reason justifies building the summary with `render_summary` from `result.total`/`result.emitted`/`result.omitted` rather than via `render_stream`; passing `ctx` would not alter those counts (they are explicit arguments and are in `_PRESERVED_FIELDS`). Saying the counts are why `ctx` is omitted would plant the same kind of false causal claim this item exists to remove. So the comment states that the shape rests on the counts reason, that projection is a no-op here (F-02), and that the call is kept as shipped.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste the full new comment block from its lead line to `parts.append(` and quote the sentence satisfying each of (a)-(d) in E-01; confirm by quoting that the strings "`next` is not in" and "could drop the paging continuation" are absent. Paste `git diff -- agent_workflows/run_analytics_cli.py` in full. Paste the output of the F-02 probe re-run at commit time (code path: `agent_workflows.renderers.AgentRenderer.render_summary`; `OutputContext` and `OutputMode` import from `agent_workflows.result_types`) showing `True` for each projection.
  - Observed evidence:
    Full new comment block in `agent_workflows/run_analytics_cli.py` (_emit_query_agent):
    ```python
    # THE SUMMARY IS RENDERED FROM THE ENGINE'S COUNTS AND ITS CALL IS KEPT AS SHIPPED.
    #
    # A `--fields` projection is now a no-op on this record, because `agent_schema._PRESERVED_FIELDS`
    # retains `total`/`emitted`/`omitted` and `next` (plan `6rcby1`, backlog `kkjrqr`), and
    # `AgentRenderer.render_summary` retains `next` on a summary regardless.
    #
    # The call shape is justified by the counts reason given in the `THE SUMMARY CARRIES THE QUERY'S
    # COUNTS, NOT THE STREAM'S` block above, pointing to that block rather than repeating it.
    #
    # History: earlier versions of this call worked around a crash (`gygujf`/`3f4ayi`) and then a dropped `next` (`6rcby1`/`kkjrqr`), both fixed.
    parts.append(
    ```

    Quoted sentences satisfying (a)-(d) in E-01:
    - (a) Capitalized claim line: `# THE SUMMARY IS RENDERED FROM THE ENGINE'S COUNTS AND ITS CALL IS KEPT AS SHIPPED.`
    - (b) Projection is a no-op: `A `--fields` projection is now a no-op on this record, because `agent_schema._PRESERVED_FIELDS` retains `total`/`emitted`/`omitted` and `next` (plan `6rcby1`, backlog `kkjrqr`), and `AgentRenderer.render_summary` retains `next` on a summary regardless.`
    - (c) Justified by counts reason: `The call shape is justified by the counts reason given in the `THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S` block above, pointing to that block rather than repeating it.`
    - (d) History note: `# History: earlier versions of this call worked around a crash (`gygujf`/`3f4ayi`) and then a dropped `next` (`6rcby1`/`kkjrqr`), both fixed.`

    Absence check:
    - String "`next` is not in": confirmed absent via grep (exit 1).
    - String "could drop the paging continuation": confirmed absent via grep (exit 1).

    Full `git diff -- agent_workflows/run_analytics_cli.py`:
    ```diff
    diff --git a/agent_workflows/run_analytics_cli.py b/agent_workflows/run_analytics_cli.py
    index 74e9945e1..c66c6ec8f 100644
    --- a/agent_workflows/run_analytics_cli.py
    +++ b/agent_workflows/run_analytics_cli.py
    @@ -255,19 +255,16 @@ def _emit_query_agent(result: query_mod.QueryResult, args: argparse.Namespace) -
         renderer = AgentRenderer()
         parts = [renderer.render_item(row, "runs query", ctx) for row in rows]
         total = max(result.total, result.emitted)
    -    # THE SUMMARY IS RENDERED WITHOUT THE FIELD PROJECTION, DELIBERATELY, TO PRESERVE PAGINATION.
    +    # THE SUMMARY IS RENDERED FROM THE ENGINE'S COUNTS AND ITS CALL IS KEPT AS SHIPPED.
         #
    -    # The summary takes no field projection because `next` is not in `agent_schema._PRESERVED_FIELDS`,
    -    # so projecting this record could drop the paging continuation and emit a truncated answer
    -    # (`complete: false` with `omitted > 0`) that tells the caller nothing about how to get the rest,
    -    # which is the one field on this record a caller cannot reconstruct.
    +    # A `--fields` projection is now a no-op on this record, because `agent_schema._PRESERVED_FIELDS`
    +    # retains `total`/`emitted`/`omitted` and `next` (plan `6rcby1`, backlog `kkjrqr`), and
    +    # `AgentRenderer.render_summary` retains `next` on a summary regardless.
         #
    -    # The counts are NOT the reason: `_PRESERVED_FIELDS` retains `total`/`emitted`/`omitted` through
    -    # any projection, so they are safe either way.
    +    # The call shape is justified by the counts reason given in the `THE SUMMARY CARRIES THE QUERY'S
    +    # COUNTS, NOT THE STREAM'S` block above, pointing to that block rather than repeating it.
         #
    -    # History: a defect where passing `ctx` crashed with a missing required field under `--fields`
    -    # previously forced this shape as well, but that defect was fixed in plan `gygujf` (backlog
    -    # `3f4ayi`) and no longer applies here.
    +    # History: earlier versions of this call worked around a crash (`gygujf`/`3f4ayi`) and then a dropped `next` (`6rcby1`/`kkjrqr`), both fixed.
         parts.append(
             renderer.render_summary(
                 "runs query",
    ```

    Output of F-02 probe re-run at commit time:
    ```
    ['cmd'] True
    ['total'] True
    ['outcome'] True
    ['a'] True
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the after captures of `aw runs query overview --agent --fields cmd` and `aw runs query overview --agent` and the `diff` exit status against each E-03 capture (code path: `run_analytics_cli._emit_query_agent`, produced by E-02's captures). Paste the after summary line of `tests/test_run_analytics_cli.py` beside E-03's. Paste the after bare `python3 -m pytest` summary line with its named failure set and state it equals E-03's. Paste the output of the comment-only check (e.g. `git diff -U0 -- agent_workflows/run_analytics_cli.py | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' | grep -vE '^[+-]\s*(#|$)'` returning nothing, with its exit status) and `git diff --stat`.
  - Observed evidence:
    After capture: `aw runs query overview --agent --fields cmd`
    ```json
    {"schema":"aw.agent/v1","kind":"item","cmd":"runs query"}
    {"schema":"aw.agent/v1","kind":"item","cmd":"runs query"}
    {"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}
    ```

    After capture: `aw runs query overview --agent`
    ```json
    {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","payload":{"cached_runs":0,"complete_runs":0,"incomplete_runs":0,"unreadable_entries":0,"quality_flag_counts":{},"required_analyses":4,"refused_analyses":4,"cache_schema_version":1,"analytics_root_exists":false}}
    {"schema":"aw.agent/v1","kind":"item","cmd":"runs query","caveats":["a refused analysis is a measured power judgement from Order 06, not a query error"]}
    {"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}
    ```

    Diff exit status against E-03 captures:
    - `diff -u .aw/state/before_overview_fields_cmd.txt .aw/state/after_overview_fields_cmd.txt`: exit 0
    - `diff -u .aw/state/before_overview.txt .aw/state/after_overview.txt`: exit 0
    Both command-output pairs are byte-identical.

    Targeted test summary (`tests/test_run_analytics_cli.py`):
    - BEFORE (E-03): `11 passed in 8.13s`
    - AFTER (E-02): `11 passed in 5.43s`
    Summary is identical: 11 passed.

    Bare `python3 -m pytest` test summary and named failure set:
    - BEFORE (E-03): `7921 passed, 4 skipped, 18 xfailed, 3 warnings in 1026.04s (0:17:06)`; failure set: empty (0 failed).
    - AFTER (E-02): `7921 passed, 4 skipped, 18 xfailed, 3 warnings in 1034.14s (0:17:14)`; failure set: empty (0 failed).
    Failure set is identical (0 failed).

    Comment-only diff check:
    ```sh
    git diff -U0 -- agent_workflows/run_analytics_cli.py | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' | grep -vE '^[+-]\s*(#|$)'
    ```
    Output: empty (exit status 1: no non-comment, non-empty additions or deletions).

    Git diff stat:
    ```
    agent_workflows/run_analytics_cli.py | 17 +++++++----------
    1 file changed, 7 insertions(+), 10 deletions(-)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the two BEFORE captures (or their paths under `.aw/state/` plus their first and last lines), the BEFORE `tests/test_run_analytics_cli.py` summary line, and the BEFORE bare `python3 -m pytest` summary line with its named failure set, plus `git status --short -- agent_workflows/run_analytics_cli.py` returning nothing at that moment, showing they were taken on the unedited tree.
  - Observed evidence:
    Status before edit:
    `git status --short -- agent_workflows/run_analytics_cli.py` returned nothing (clean unedited tree).

    Two BEFORE captures:
    - Path `.aw/state/before_overview_fields_cmd.txt`:
      First line: `{"schema":"aw.agent/v1","kind":"item","cmd":"runs query"}`
      Last line: `{"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}`
    - Path `.aw/state/before_overview.txt`:
      First line: `{"schema":"aw.agent/v1","kind":"item","cmd":"runs query","payload":{"cached_runs":0,"complete_runs":0,"incomplete_runs":0,"unreadable_entries":0,"quality_flag_counts":{},"required_analyses":4,"refused_analyses":4,"cache_schema_version":1,"analytics_root_exists":false}}`
      Last line: `{"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}`

    BEFORE `tests/test_run_analytics_cli.py` summary line:
    `11 passed in 8.13s`

    BEFORE bare `python3 -m pytest` summary line and named failure set:
    `7921 passed, 4 skipped, 18 xfailed, 3 warnings in 1026.04s (0:17:06)`
    Failure set: empty (0 failed).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; no blocking question remains.
- Order: E-03 (baseline) first, then E-01, then E-02.
- Scope fence: the declared `- Scope-Paths:` are `agent_workflows/run_analytics_cli.py` and this plan. This is a declaration, not a stop condition: an out-of-scope edit that proves necessary is made and justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). The one real risk is OVERREACH: any executable line in the diff means E-01 exceeded its mandate and must be redone as prose only. The E-01 STOP, if the F-02 probe shows a projection changes the record, stays: the comment's rationale would then be false.
- Honesty: every `Observed evidence` MUST paste the ACTUAL command output; never claim a pass that was not run.
- Commit: path-scoped via `aw commit gbizqt -- agent_workflows/run_analytics_cli.py <this plan>`; never `git add -A`/`-a`/`--no-verify`, never push.
- Lifecycle: start with `aw ipd begin gbizqt --actor <you>`. The terminal transition to `executed/` happens only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. Under `aw oc run`/`aw agy run` the runner performs that transition, so the executor must NOT run `aw ipd finalize` itself. When executing by hand, run `aw ipd finalize gbizqt --actor <you> --message <msg> --apply` (never a hand `git mv` to `executed/`). Backlog item `d6u2hz` is transitioned by the runner, not by this plan.
