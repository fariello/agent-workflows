# IPD: Refresh the stale crash-workaround comment in run_analytics_cli._emit_query_agent now that the --fields projection defect is fixed

- Date: 2026-09-30
- Kind: child
- Concern: `run_analytics_cli._emit_query_agent` carries a comment block above its `render_summary` call asserting that passing the output context with `ctx.fields` set RAISES `ValueError: Invalid aw.agent/v1 record: Summary record missing required field 'total'`, that the defect "lives in `renderers.py` / `agent_schema.py`" outside the authoring plan's scope, and that it "is REPORTED ... and NOT fixed here". Plan `gygujf` fixed exactly that defect, so the comment now tells a reader a live bug exists where none does. Measured at this HEAD: the call it says crashes returns a valid record carrying `total`/`emitted`/`omitted`. The comment additionally names `agent_schema._MANDATORY_FIELDS` as the set the projector preserves, which `gygujf` superseded with `_PRESERVED_FIELDS`, so the citation points at the wrong constant.
- Scope: Rewrite the stale crash narrative in that one comment block so it describes live behavior, and state the reason the no-context call SURVIVES on its own terms. Authoring measurement CORRECTS the reason the two carrier items propose: counts are no longer the differentiator, because `_PRESERVED_FIELDS` now retains `total`/`emitted`/`omitted` through any projection, so a projected summary keeps its counts either way; the field the projection actually drops is `next`, the paging continuation. The comment must therefore rest on `next` rather than repeat a counts rationale this plan measured false. Prose only: the `render_summary` call, its arguments, and every other executable line are untouched, and no command's output changes. Also closes duplicate carrier `o8vgss`, which describes the same comment.
- Scope-Paths: agent_workflows/run_analytics_cli.py, .aw/records/backlog/open/20260929-o8vgss-01-o8vgss-stale-projection-workaround-comment.backlog.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: cm80ge
- Set: cm80ge
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: mcdvx0

## Workflow history

- 2026-09-30 to-review (opencode): authored from backlog item `cm80ge`. Every claim in the item was re-measured at this HEAD rather than carried over; the item's core claim (the crash is gone, so the comment is stale) was CONFIRMED. Authoring measurement REJECTED the item's suggested replacement rationale: both `cm80ge` and the duplicate `o8vgss` propose keeping the "summary reports engine counts, not stream counts" paragraph as the surviving reason, but `gygujf` made `_PRESERVED_FIELDS` retain `total`/`emitted`/`omitted` under EVERY projection, so passing the context would NOT project the counts away and that rationale no longer distinguishes the two calls (F-03). The real surviving difference is `next`, which is not in `_PRESERVED_FIELDS` and IS dropped (F-04). Writing the item's suggested fix verbatim would have replaced one false claim with another. Found duplicate carrier `o8vgss` covering the same comment and folded it in (F-06). Filed backlog `kkjrqr` during authoring for the defect F-10 measured on the way to F-04: dropping `next` can strand an agent's pagination, which is a real bug this plan only DESCRIBES and does not fix.
- 2026-09-30 draft (opencode): created.

## Goal

Make the comment above `_emit_query_agent`'s `render_summary` call describe the code as it actually behaves: the crash it documents is fixed, and the no-context call persists for a reason that is still true and worth stating.

THE POINT IS THE TRAP, NOT THE TIDINESS. This comment is unusually detailed and confident, and it names a specific `ValueError` with a specific cause. That is what makes it dangerous now: a maintainer who reads it believes an unfixed defect exists in `renderers.py`/`agent_schema.py`, and the natural responses are to re-file it (which is how `cm80ge` and `o8vgss` both came to exist as separate items for one comment) or to copy the "workaround" into a new call site that does not need one. A comment that is merely absent misleads nobody; this one actively argues for a false conclusion.

WHAT THE FIX MAY NOT DO, and this is the constraint that makes it a prose change. The no-context call is NOT to be "corrected" into passing `ctx`. It stays exactly as it is. Only the narrative changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the comment describe live behavior

- [ ] E-01 In `agent_workflows/run_analytics_cli.py`, rewrite the comment block in `run_analytics_cli._emit_query_agent` that begins `THE SUMMARY IS RENDERED WITHOUT THE FIELD PROJECTION, DELIBERATELY, AND THIS WORKS AROUND A` and runs to just above the `parts.append(renderer.render_summary(` call. DELETE the three stale paragraphs: the `Measured:` paragraph asserting the `ValueError` (false per F-01, and its `_MANDATORY_FIELDS` citation names the superseded constant per F-02), the `This is NOT caused by this plan:` paragraph (its Scope-Paths reasoning belonged to the authoring plan and reads as a live report of an unfixed bug), and the trailing `Projecting a summary's counts away would be wrong anyway:` paragraph (F-05: true about the counts but no longer the reason for THIS call, and duplicative of the neighboring block). WRITE IN THEIR PLACE a short block resting on the ONE difference that survives, per F-04: the summary takes no field projection because `next` is not in `agent_schema._PRESERVED_FIELDS`, so projecting this record could drop the paging continuation and emit a truncated answer (`complete: false` with `omitted > 0`) that tells the caller nothing about how to get the rest, which is the one field on this record a caller cannot reconstruct. State that the counts are NOT the reason, explicitly and in one clause, because that is the plausible-but-wrong rationale two separate carrier items already reached (F-03): `_PRESERVED_FIELDS` retains `total`/`emitted`/`omitted` through any projection, so they are safe either way. CITE the fixed defect as history in a form a reader can look up (backlog `3f4ayi`, plan `gygujf`) and say plainly that it USED to also force this shape and no longer does, so a reader who finds this comment while chasing that `ValueError` learns it is closed instead of re-filing it a third time. Keep the existing capitalized-lead comment style of the function's neighbors. Do NOT restate the `emitted + omitted == total` invariant here: the adjacent `THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S` block already owns it. TOUCH NO EXECUTABLE LINE: the `parts.append(...)` call, all eight of its keyword arguments, `total = max(result.total, result.emitted)`, and every other statement in the function stay byte-identical, because this plan asserts the call is CORRECT and is only fixing the account of why.
  - Depends on: none
  - Expected outcome: The comment block above `_emit_query_agent`'s `render_summary` call no longer asserts any `ValueError`, no longer says a defect is unfixed or out of scope, and no longer cites `_MANDATORY_FIELDS`; it gives the `next` rationale, explicitly disclaims the counts rationale, and cites `3f4ayi`/`gygujf` as closed history. `git diff` for this file shows comment lines only, with zero changes to any line ending in a statement.
  - Execution state: pending

- [ ] E-02 Close duplicate carrier `o8vgss` (F-06) so the tree does not keep an open item whose subject E-01 just removed. Run `aw backlog set done .aw/records/backlog/open/20260929-o8vgss-01-o8vgss-stale-projection-workaround-comment.backlog.md --evidence <this plan's path>`, which cites an in-tree artifact as the satisfying evidence. The item carries NO `- Blocks-Release:` gate (verify this before the call, and if that is somehow untrue STOP and report rather than closing it, because a gated close has its own predicate and its own legitimacy rules). Record in its history that the comment it describes was fixed by this plan, not that the item was mistaken: `o8vgss`'s measurement was CORRECT, it simply arrived at the same live defect from a second direction, and its note about the counts rationale being "arguably still correct on its own separate ground" is the very inference F-03 measured false, which is worth recording as the reason this plan rests on `next` instead. If `aw backlog set done` refuses for any reason, do NOT hand-edit the record: report the refusal verbatim and leave the item open, since E-01 stands on its own without it.
  - Depends on: E-01
  - Expected outcome: `o8vgss` is `- Status: done` under `.aw/records/backlog/done/`, moved by the tool with an appended history line citing this plan, and `aw check` reports no new violation. Alternatively, a verbatim refusal is reported and the item is untouched.
  - Execution state: pending

- [ ] E-03 Prove the change is inert as the LAST act before commit, since E-01's whole claim is that no behavior changes. THREE CHECKS. FIRST, byte-identical output: capture `aw runs query overview --agent --fields cmd` and `aw runs query overview --agent` before and after E-01 and diff the two pairs; each must be identical, which is what "comment-only" means operationally. SECOND, run the suite BARE as `python3 -m pytest` (the configured `addopts` already supply `-q -n auto`; do not add flags) and confirm it still reports `3387 passed, 2 skipped` or more, against the F-08 baseline; paste the actual summary line. THIRD, confirm the diff's shape mechanically rather than by eye: `git diff --stat` must name `agent_workflows/run_analytics_cli.py` only among source files, and every added or removed line in `git diff -- agent_workflows/run_analytics_cli.py` must be a comment line (matching `^[+-]\s*#` or a blank), with NO added or removed executable statement. If any executable line appears in that diff, E-01 overreached: revert it and redo E-01 as prose only.
  - Depends on: E-02
  - Expected outcome: Both command outputs are byte-identical before and after; the suite summary line is pasted and is at or above the F-08 baseline with no new failure; the diff touches one source file and contains comment lines only.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The execution contract forbids em and en dashes in USER-FACING prose but explicitly exempts code comments, so this plan's deliverable is under no dash restriction. It does not add any regardless, matching the surrounding comment style in `run_analytics_cli`.
- Comment style in `agent_workflows/run_analytics_cli.py` states a claim in a capitalized lead line, then justifies it. `_emit_query_agent`'s neighbors follow this (`THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S, and the distinction is load-bearing.`, and `A CAVEAT IS PART OF THE ANSWER.`). The replacement keeps that shape rather than inventing a new one.
- P16 of `GUIDING_PRINCIPLES` forbids tests that pin code structure, including asserting that specific comment text remains unchanged. This plan therefore adds NO test, and V-01 verifies the deliverable by reading the diff, not by a tripwire. See "Required tests / validation".

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-01 | The comment's central claim is FALSE at this HEAD. It says `render_summary(..., context=ctx)` with `ctx.fields` set raises `ValueError: Invalid aw.agent/v1 record: Summary record missing required field 'total'`. | Called `AgentRenderer().render_summary('runs query', total=3, emitted=2, omitted=1, outcome='ok', exit_code=0, next_cmd=None, complete=False, context=OutputContext(mode=OutputMode.AGENT, fields=['outcome']))`. No exception; returned `{"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"ok","exit":0,"total":3,"emitted":2,"omitted":1,"complete":false}`. |
| F-02 | The fix is present and is the one `gygujf` describes. `agent_schema` defines `_PRESERVED_FIELDS = _MANDATORY_FIELDS \| {"applied", "total", "emitted", "omitted"}` and `filter_record_fields` uses it in its `allowed` expression. So the comment's citation of `_MANDATORY_FIELDS` as the set "`filter_record_fields` preserves" now names the wrong constant. | `agent_schema._PRESERVED_FIELDS`; `sorted(_PRESERVED_FIELDS)` is `['applied','cmd','complete','emitted','exit','kind','omitted','outcome','schema','total','verified']`. Plan `gygujf` is in `.aw/records/plans/executed/` with `- Status: executed`. |
| F-03 | THE REPLACEMENT RATIONALE BOTH CARRIER ITEMS SUGGEST IS ALSO FALSE, which is the finding that changes this plan's deliverable. Both propose keeping the counts argument (projecting the counts away would defeat `emitted + omitted == total`) as the surviving reason for the no-context call. But `_PRESERVED_FIELDS` retains `total`/`emitted`/`omitted`, so passing `ctx` does NOT project them away. The invariant is safe either way and cannot distinguish the two calls. | `render_summary` with `fields=['cmd']`, with `fields=['total']`, and with no context all returned `total`/`emitted`/`omitted` intact. Confirmed end to end: `aw runs query overview --agent --fields cmd` emitted `{"schema":"aw.agent/v1","kind":"summary","cmd":"runs query","outcome":"clean","exit":0,"total":0,"emitted":0,"omitted":0,"complete":true}`. |
| F-04 | THE REAL SURVIVING DIFFERENCE IS `next`, not the counts. `next` is absent from `_PRESERVED_FIELDS`, so a projection drops it unless the caller names it. On a bounded query that is the paging continuation, so passing `ctx` could emit a truncated answer (`complete: false`, `omitted > 0`) with no command to retrieve the rest. | `'next' in _PRESERVED_FIELDS` is `False`. Same call with `fields=['cmd']` and `next_cmd='aw runs query --offset 2'` returned a record with NO `next` key, while `fields=['next']` and the no-context call both retained it. `run_analytics_query` sets `next_command` only `if omitted:`, and `_emit_query_agent` passes `next_cmd=result.next_command or None`. |
| F-05 | The comment's last paragraph (the `emitted + omitted == total` invariant) is still TRUE as a statement about why the counts matter, even though F-03 shows it no longer explains this call's shape. It also now duplicates the neighboring `THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S` block, which makes the same point about the same call. Keeping both verbatim would leave two adjacent paragraphs arguing one point. | Both blocks sit in `_emit_query_agent` above the same `render_summary` call. `docs/cli-agent-protocol.md` already states the invariant for readers, under `## Token control`. |
| F-06 | `cm80ge` IS DUPLICATED by backlog item `o8vgss` (`- Status: open`, `Set: o8vgss`, filed 2026-09-29 from plan `wqiofa`/backlog `un6ppd`), which describes the same comment in the same function for the same reason. Two carriers for one comment is itself a symptom of F-01: each author hit the stale comment independently. Fixing the comment without closing `o8vgss` leaves an open item whose subject no longer exists. | `.aw/records/backlog/open/20260929-o8vgss-01-o8vgss-stale-projection-workaround-comment.backlog.md`: "the --fields projection workaround comment in run_analytics_cli._emit_query_agent asserts a defect that gygujf already fixed". |
| F-07 | No test pins this comment's text, so the change cannot break the suite, and no test needs to change. Nothing else in the tree repeats the stale claim. | No match for `_emit_query_agent` anywhere under `tests/`. `grep -rln "Summary record missing required field"` across `--include=*.py --include=*.md` matches only `agent_schema.py`, `run_analytics_cli.py`, and the backlog records themselves. |
| F-08 | Suite baseline at this HEAD is GREEN, so any failure after this change is attributable to it. | Bare `python3 -m pytest`: `3387 passed, 2 skipped, 3 warnings in 135.75s`. |
| F-10 | THE `next` DROP IS A REAL DEFECT IN ITS OWN RIGHT, not merely an asymmetry worth mentioning in a comment, which is why this plan files a carrier for it rather than only describing it. `next` is not required by `validate_agent_record`, so a projected summary without it is still VALID, which is exactly why `gygujf` was right not to add it to `_PRESERVED_FIELDS`. But a summary reporting `complete: false` with `omitted > 0` and no `next` tells an agent its answer is incomplete while withholding the only field that says how to continue, and that field is NOT reconstructible by the caller because it encodes the view, the active filters and `--limit min(total, MAX_ROW_LIMIT)`. Filed as backlog `kkjrqr` (`bug`, auto-gated `Blocks-Release: next`). This plan does not fix it. | `'next' in _PRESERVED_FIELDS` is `False`; `render_summary(..., next_cmd='aw runs query --offset 2', complete=False, context=OutputContext(fields=['cmd']))` returned a record ending `..."complete":false}` with no `next`, while the no-context call retained it. `run_analytics_query` builds `next_command` only `if omitted:`. `docs/cli-agent-protocol.md` tells readers "A projection never yields a record that fails validation, so `--fields` is safe to pass on any command". |
| F-09 | `gygujf` itself ANTICIPATED this work and scoped it here. Its E-04 requires confirming `_emit_query_agent` is unchanged and records that "the comment block above it is now partly stale, which is `cm80ge`'s work and not this plan's". So this plan is the intended carrier, not a rediscovery. | `.aw/records/plans/executed/20260928-3f4ayi-01-gygujf-make-an-aw-agent-v1-field-projection-preserve-every-per-kind.ipd.md`, E-04. |

## Proposed changes (ordered, validatable)

1. Replace the stale crash narrative in `_emit_query_agent` with a statement of the surviving reason resting on `next` (F-04), not on the counts (F-03), citing `3f4ayi`/`gygujf` as the record of the fixed defect. Fold the now-duplicated invariant paragraph into the neighboring block rather than keeping both (F-05).
2. Close duplicate carrier `o8vgss` against this plan (F-06).
3. Verify no behavior changed: identical bytes out of every affected command, and a green suite (F-07, F-08).

## Deferred / out of scope (with reason)

- MAKING THE PROJECTION PRESERVE `next`, or otherwise changing `_PRESERVED_FIELDS`, is OUT OF SCOPE. F-04 establishes that `next` is droppable, and F-10 measures why that is worth fixing: a truncated answer (`complete: false`, `omitted > 0`) can reach an agent with no continuation command, and `next` is not reconstructible from the record. That is a change to the `aw.agent/v1` projection contract and belongs to `agent_schema.py` with its own measurement, its own behavioral test, and the documentation sync `gygujf` had to do; it is not a comment refresh. This plan DESCRIBES current behavior accurately and changes none of it.
  - Carrier: kkjrqr
- CHANGING THE `render_summary` CALL to pass `ctx` is explicitly refused. Both carrier items say the call's current behavior must not change, and F-04 gives it a live justification independent of the fixed crash.
  - Carrier-Declined: This is not deferred work, it is the plan's central constraint. There is no future task here to carry: the call is correct as written and this plan exists to make the comment say so accurately. A carrier would imply someone should later change the call, which is the opposite of the finding.
- CORRECTING `docs/cli-agent-protocol.md`'s statement of the retained set is unnecessary: its `--fields` bullet already describes the post-`gygujf` behavior, including the four additionally retained fields, because `gygujf`'s E-03 updated it. Verified at this HEAD.
  - Carrier-Declined: No work remains on the retained-set wording, which is already correct. The SEPARATE question of whether that document's "safe to pass on any command" framing should also mention the dropped `next` is part of the contract decision carried by `kkjrqr` (it lists amending that framing as candidate fix (c)), so it is owned there rather than duplicated here.
- No test is added, by P16. See "Required tests / validation" for why a tripwire here would be a structure-pinning test and therefore forbidden.
  - Carrier-Declined: A forbidden test is not deferred work and must never acquire a carrier, because a carrier would schedule the very P16 violation this bullet refuses. The deliverable's verification is V-01 (reading the diff) plus E-03's inertness proof, which is the correct validation shape for a comment, not a postponed one.

## Scope check

- Over-scope: none. One comment block in one function, plus the duplicate carrier E-02 closes. Both files are declared in `- Scope-Paths:`.
- Under-scope: The `next` projection asymmetry F-04 measured is left as live behavior, deliberately and with reason stated above; this plan documents it rather than resolving it. `cm80ge` itself is transitioned by the runner, not by this plan.

## Required tests / validation

NO TEST IS ADDED, AND THAT IS A DELIBERATE CONSEQUENCE OF P16. The only test that could pin this deliverable would assert on comment text in a production source file, which `GUIDING_PRINCIPLES` P16 and the execution contract forbid in terms ("NEVER assert that specific text, docstrings, or comment banners remain unchanged in a script"). A comment cannot be validated by a behavioral test, because a correct comment and a stale one produce identical behavior; that is precisely why this defect survived `gygujf`. So the deliverable is validated by READING (V-01), and the suite's role here is inverted: it proves the change did NOTHING, not that it did something.

Validation therefore rests on three legs: the diff contains comment lines only (mechanically checked, E-03 third check), every affected command emits byte-identical output (E-03 first check), and the full suite stays at or above its green baseline of `3387 passed, 2 skipped` (E-03 second check, F-08).

## Spec / documentation sync

N/A. No spec governs the wording of an internal code comment, and no `.spec.md` file is touched, so nothing is declared in `- Scope-Paths:` for a spec amendment. The one user-facing document that describes `--fields` projection, `docs/cli-agent-protocol.md`, was already reconciled with live behavior by `gygujf`'s E-03 and is verified correct at this HEAD (see "Deferred / out of scope"), so this plan has no documentation debt to settle.

## Open questions

### OQ-01: Should the replacement comment rest on `next` (this plan) or on the counts (as both carrier items suggest)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, against both items. `cm80ge` says to "replace the crash-workaround paragraphs with a short statement of the surviving reason (the summary reports engine counts, not stream counts, so it deliberately takes no field projection)", and `o8vgss` reaches the same conclusion independently. F-03 measures that rationale FALSE: `_PRESERVED_FIELDS` retains `total`/`emitted`/`omitted` under every projection, so passing `ctx` would not project the counts away and the counts cannot be what distinguishes the two calls. Writing the suggested text would have replaced one confidently wrong comment with another, which is the exact failure this item exists to fix. F-04 supplies the difference that does survive: `next` is not preserved. This plan therefore rests on `next` and explicitly disclaims the counts, so the next reader does not re-derive the same wrong answer a third time. A reviewer who disagrees should dispute the F-03/F-04 measurements, which are reproducible in three lines.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the FULL comment block as it now stands in `_emit_query_agent`, from its lead line to the `parts.append(` call, and confirm against it, by quoting: (a) it contains no `ValueError`, no `Summary record missing required field`, and no `_MANDATORY_FIELDS`; (b) it contains no claim that a defect is unfixed, reported elsewhere, or out of some plan's scope; (c) it states the `next` rationale, naming `next` and `_PRESERVED_FIELDS`, and says a projection could drop the paging continuation; (d) it explicitly says the counts are NOT the reason and are preserved regardless; (e) it cites `3f4ayi` and `gygujf` as closed history. ALSO paste `git diff -- agent_workflows/run_analytics_cli.py` in full and confirm every `+`/`-` line is a comment or blank line, with the `render_summary` call and its arguments unchanged. Then RE-RUN the F-01 probe (`render_summary` with `fields=['outcome']`) and paste the returned record, to confirm the comment's new account still matches live behavior at commit time rather than at authoring time.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `aw find backlog o8vgss` (or the equivalent) showing the item at `- Status: done` under `.aw/records/backlog/done/`, plus its appended history line showing it was closed with this plan as evidence, plus the actual `aw backlog set done ...` command output. Confirm by quoting its front matter that it carried no `- Blocks-Release:` field. If the close was refused instead, paste the refusal verbatim and confirm the item file is unmodified (`git status` clean for that path).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the before/after captures of `aw runs query overview --agent --fields cmd` and `aw runs query overview --agent` together with the `diff` exit status or output proving each pair identical. Paste the bare `python3 -m pytest` summary line (for example `3387 passed, 2 skipped ... in ...s`) and confirm it is at or above the F-08 baseline with no new failure; a narrowed or flag-modified run does not satisfy this. Paste `git diff --stat` showing `agent_workflows/run_analytics_cli.py` as the only source file changed (the backlog record moved by E-02 may also appear).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; do not execute it from this authoring turn. Execution follows the repository execution contract: commit only the paths named in `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` or `-a`, never `--no-verify`, and never push. Paste actual runner output for the suite rather than claiming success.

The one risk worth a reviewer's attention is OVERREACH, not breakage: this is a prose change whose entire correctness claim is that no behavior moved, so E-03's mechanical diff check (comment lines only) and byte-identical command output are the gate, and a diff containing any executable line means E-01 exceeded its mandate and must be redone. The second thing to check is the F-03/F-04 measurements, since they overrule the fix both carrier items proposed; if they are wrong, the deliverable's rationale is wrong.

Post-gate lifecycle: after every `V-*` item is verified with pasted evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` through the tooled transition. Backlog item `cm80ge` is transitioned by the runner; this plan does not set its status.
