# Review findings: plan 8o709f

- Subject-Id: 8o709f
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (HIGH, fixed), PR-804 (MEDIUM, fixed), PR-805 (MEDIUM, fixed), PR-806 (LOW, fixed), PR-807 (LOW, fixed), PR-808 (LOW, fixed)

## Round 1

Reviewed at HEAD `56f7ab2d` in an isolated review lane. The plan file was committed and byte-identical
to the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE
semantic review; `--phase review-finalize --agent` reports `conforming` after revision, including the
new `E-07`/`E-08` and `V-07`/`V-08` pairs.

THE PLAN'S PREMISE IS CORRECT AND WELL EVIDENCED, and most of its detail work survives review intact.
I verified the enumeration rather than trusting it: parsing the module with `ast`, `execute_item_core`
spans lines 30461-34475 and holds exactly nine `contextlib.suppress` blocks, seven blanket and two
already `(DriverError, OSError)`, which is F-1 as written. F-4 holds: `build_lane_outcome`'s docstring
does warn that simplifying its three calls "would stop them raising `DriverError`". F-5 holds
precisely: `lane_containment.collect_lane_submissions` contains ZERO `try`/`except`, raises nothing,
and does carry the three `assert ... is not None` statements the plan cites, so `suppress(OSError)` is
the right tuple there. F-3 reproduces exactly: `dirty_tree_overlap(repo, [])` returns `[]` and
`poll_for_integration_window(repo, [])` returns `cleared=True, bound='dirt-cleared', polls=0`, so an
empty field really does buy a false clear-verdict. F-6 holds: the only `tests/` references to
`build_lane_outcome` are name-census entries in `tests/test_runner_shared.py`, never a behavioral
exercise. E-03's tuple is right, verified against `queue_artifact_path`'s three `raise DriverError`
sites and the `relative_to` that follows.

THREE CLAIMS DID NOT SURVIVE, and the first is the one that matters most because it is a GAP rather
than a wording error. PR-801: the plan missed a SECOND call site of the very function its defect was
filed about. `runner_shared.py:32382` calls `build_lane_outcome(repo, wt_handle, item["id6"])` inside
a bare `try: ... except Exception: pass`, seeds `gate_changed_files` from
`item.get("integration_changed_files")` and overwrites it. Before `h5pyqa` bound the host wrapper
this site raised the identical `TypeError` on every gate question and silently produced an empty file
list. The consequence of missing it is exact and bad: had this plan shipped as authored, its own
`cv5n6t` regression test (E-06) would have gone green while the identical defect stayed live one
screen away, which is the precise failure mode the plan exists to prevent. New E-07 narrows it to
`except DriverError:`; new V-07 demands the propagating-`TypeError` run and the sabotage check.

PR-802: E-02's stated premise is FALSE, and the plan's ordering rationale rested on it. The plan
argues the refusal arm "demonstrably runs with `wt_handle=None`", inferring reachability from the
neighbouring `branch=wt_handle.branch if wt_handle else None`. It does not. The block at line 34032
is nested inside `if self_finalize and work_dir and wt_handle is not None and integration.earned:`
(line 33697), and an assignment scan over that range finds no rebinding of `wt_handle`; the nearest
preceding `wt_handle = None` is line 33685, BEFORE the guard, which is exactly why the guard
re-tests it. So the `AttributeError` F-2 reproduced was measured in a direct call, not on the product
path, and E-01 was never unsafe without E-02. Three consequences applied: E-02's dependency on E-01
dropped, its comment obliged to say "defence in depth against future re-nesting" rather than implying
a live fix, and its SABOTAGE CHECK REMOVED, because a check that can only pass by faking an
unreachable state proves nothing. I kept the guard itself: the enclosing condition is ~335 lines
above the call, and that distance is a real re-nesting hazard worth one cheap line.

PR-803 is the finding I expect to be argued with, so I state the measurement plainly. E-05 proposed
narrowing the suite-baseline `collect` call to `suppress(OSError)`. That tuple would miss the
exception most likely to escape. `SuiteBaselineRun.collect` contains ZERO `try`/`except`; its "NEVER
raises" promise rests on three internal `contextlib.suppress(Exception)` blocks, and
`self._extract(self._stdout, self._stderr)` sits OUTSIDE all of them. `self._extract` is an INJECTED
host callable (`baseline_extractor = getattr(driver_module, "extract_suite_failures", None)`, passed
as `start_suite_baseline(..., extract_failures=baseline_extractor)`), which makes its likeliest
failure a `TypeError`/`AttributeError` from signature drift - the exact class this whole plan exists
to expose, and exactly what `OSError` does not catch. Narrowing to `(OSError, TypeError,
AttributeError)` is so close to blanket that it buys nothing while LOOKING principled, which is worse
than honest blanket. So the item is reversed: keep the block blanket, and spend the edit on a comment
naming the unguarded injected call so the next reader fixes the CALLEE. The adjacent "A MISSING OR
FAILED BASELINE IS NOT A FAILED ITEM" rule independently forbids letting this fail a turn.

PR-804 is a scope-honesty finding. F-1's "seven blocks" counts one SPELLING. Measured by `ast`, the
function also holds EIGHTEEN `except Exception` handlers, six of them bare `pass` swallows
indistinguishable in effect from a blanket suppress (30909, 31524, 32384, 33266, 33361, 33498), the
rest assigning fallbacks. I did NOT demand a sweep: that would be a far larger change with weaker
per-site justification, and only 32384 carries a measured defect. But shipping this plan would
otherwise let "we narrowed the suppress blocks in `execute_item_core`" read as a completeness claim
the code does not support, so new E-08 records the true census, names every site deliberately left
alone, and must re-derive the numbers at execution HEAD since a 4000-line function shifts under any
edit.

I ALSO FIXED FIVE PRE-EXISTING `check.ipd-uncarried-obligation` VIOLATIONS (PR-806). Every deferred
row lacked a `Carrier-Declined` reason, so `aw check` flagged the plan; each now carries a specific
declination rather than boilerplate, and the one that genuinely needs discussion (the unguarded
`_extract`, a NEW row I added from F-10) says openly that its remedy is undecided between guarding
the call and correcting the docstring. `check.ipd-uncarried-obligation` now reports CLEAN for this
plan. PR-807 corrected `he9x6j`, which the plan twice calls "still open" and which is `graduated`.

ONE THING I DELIBERATELY DID NOT CHANGE: the plan's decision to narrow rather than remove, and its
rule that a missed exception class is added to the tuple rather than answered by restoring blanket
form. That is the right instinct, and PR-803 is that same rule applied honestly to a site where the
surface is not enumerable.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | A. Correctness / E. Testing | `runner_shared.py:32382` calls `build_lane_outcome(repo, wt_handle, item["id6"]).changed_files` inside a bare `except Exception: pass` (line 32384); it seeds `gate_changed_files` from `item.get("integration_changed_files")` (line 32377) and overwrites it; already `None`-guarded by its own `if wt_handle is not None:` | The census MISSED a second call site of the same function, carrying the identical `TypeError` exposure and feeding the same field's consumer. As authored, E-06's `cv5n6t` regression test would pass while the identical defect stayed live one screen away | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-8. New E-07 narrows it to `except DriverError:` keeping its comment and existing `None` guard; new V-07 demands a propagating-`TypeError` run, a quiet-`DriverError` run and the sabotage check; E-06 extended to cover both arms and its `Depends on` updated to `E-01, E-07` |
| PR-802 | HIGH | IN-SCOPE | D. Anti-regression / G. Executability | Block at `runner_shared.py:34032` is nested in `if self_finalize and work_dir and wt_handle is not None and integration.earned:` (33697); assignment scan over 33697-34032 finds no rebinding; nearest preceding `wt_handle = None` is 33685, before the guard | E-02's premise that the arm "demonstrably runs with `wt_handle=None`" is FALSE, so the `AttributeError` is unreachable at this site and E-01 was never unsafe without E-02. The plan's ordering rationale ("which is why the two ship together") rested on this | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-7; F-2 corrected to withdraw the reachability claim. E-02 retained as defence in depth with an honest comment obligation, its `Depends on` dropped to `none`, and its SABOTAGE CHECK REMOVED (it could only pass by faking an unreachable state). V-02 rewritten to demand the reachability measurement instead, and to treat a contradicting measurement as a reportable finding |
| PR-803 | HIGH | IN-SCOPE | A. Correctness / F. KISS | `SuiteBaselineRun.collect` has ZERO `try`/`except` (ast-parsed); `self._extract(self._stdout, self._stderr)` sits outside all three internal `suppress` blocks; `self._extract` is bound from `getattr(driver_module, "extract_suite_failures", None)` and passed via `start_suite_baseline(..., extract_failures=...)`; both hosts define it | E-05's proposed `suppress(OSError)` would MISS the likeliest escape, an injected-callable `TypeError`, which is the very drift class this plan exists to expose. A narrow tuple here would look principled and catch nothing | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-10. E-05 REVERSED to keep the block blanket and spend the edit on a comment naming the unguarded injected call so the next reader fixes the CALLEE; V-05 rewritten to demand the reversal evidence and to state that a pasted `suppress(OSError)` is now a FAILED validation; OQ-01's resolution updated with the changed answer and its reason; new Deferred row for the `_extract` hole |
| PR-804 | MEDIUM | UNDER-SCOPE | G. Executability / honest documentation | ast parse at `56f7ab2d`: `execute_item_core` spans 30461-34475, nine `suppress` blocks (7 blanket, 2 narrowed), EIGHTEEN `except Exception` handlers of which six are bare `pass` (30909, 31524, 32384, 33266, 33361, 33498) | F-1's "seven blocks" counts one spelling, so "we narrowed the suppress blocks in `execute_item_core`" would read as a completeness claim the code does not support | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-9. New E-08 records the true census (method named, re-derived at execution HEAD) and states per site why it is untouched; V-08 demands the ast output rather than a grep; F-1, Scope and Scope check annotated; Goal gains two explicit bounds |
| PR-805 | MEDIUM | IN-SCOPE | G. Execution contract | The gate read "append the workflow-history line, set the terminal `Status: executed`, and `git mv` this plan to `.aw/records/plans/executed/` ... via `aw ipd finalize`"; `ipd_lifecycle.LIFECYCLE_ROLE_ERROR` defines `AW-LIFECYCLE-ROLE-001` for the managed-lane case | The gate instructed a hand-rolled `git mv` and a terminal `Status:` edit beside the tooled verb, and carried no paste-the-actual-output honesty rule, no path-scoped commit/never-push clause, and no runner-versus-executor ownership of the transition | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: tooled `aw ipd begin`/`aw ipd finalize` only, no hand `git mv` or hand `- Status:`, runner ownership with the `AW-LIFECYCLE-ROLE-001` refusal path, path-scoped `aw commit` and never-push, the hard-MUST paste rule, the `--scope-reason` rule for an out-of-scope edit (made-then-justified, not stop), one genuinely-unsafe stop condition, and the `cv5n6t` gate-inheritance note |
| PR-806 | LOW | IN-SCOPE | Repository rules | `check_engine.check_durable_carrier` reported `check.ipd-uncarried-obligation`: "5 obligation(s) name no durable carrier: deferred row 1..5" | Five pre-existing deferred rows carried no `Carrier-Declined` reason, so the plan failed a shipped consistency check | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A specific declination written for each row (not boilerplate), plus a sixth new row for F-10's `_extract` hole whose declination states openly that its remedy is undecided. `check_durable_carrier` now reports CLEAN for this plan |
| PR-808 | LOW | IN-SCOPE | Repository rules | `attention_contract.newest_history_record` documents newest-first as "THE WRITER'S CONTRACT" and `ipd_lifecycle._plan_status_events` reverses records on that premise; the plan's two records were `draft` then `to-review` in file order | The plan's `## Workflow history` was written OLDEST-FIRST, inverting the repository's newest-first contract. Latent while unread, but it surfaced as `check.lifecycle-transition-invalid` ("backwards transition 'to-review' -> 'draft'") the moment a third record was prepended, so any future history writer would have tripped it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The two pre-existing records REORDERED to newest-first with their text preserved verbatim (no content changed, only line order), and the review record prepended above them. `check_lifecycle_transitions` now reports CLEAN for this plan |
| PR-807 | LOW | IN-SCOPE | Step 1 evidence accuracy | `.aw/records/backlog/graduated/20260920-he9x6j-01-he9x6j-tool-event-output-text-missing.backlog.md` carries `- Status: graduated` | The plan twice states the sibling defect `he9x6j` is "still open" / "remains OPEN" | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-11; both the Concern and the Deferred row corrected to `graduated`, and the Deferred row's declination now rests on the item's own durable existence |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan missed a second `build_lane_outcome` call site. Add it here, or file it separately? | Add it here as E-07 | File separately (rejected: it is the SAME call, same defect, same field consumer, and leaving it would let this plan's own regression test pass while the bug lived on); ignore it (rejected outright) | `runner_shared.py:32382` with its bare `except Exception: pass` at 32384; the `cv5n6t` mechanism recorded in the comment at 30543-30550 | yes |
| D-2 | E-02's reachability premise is false. Drop the guard, or keep it with a corrected reason? | Keep it, relabelled as defence in depth, dependency dropped, sabotage check removed | Drop the guard entirely (rejected: the enclosing condition is ~335 lines above the call, so a future re-nesting would silently reintroduce the hazard for one cheap line); keep it with the original justification (rejected: it asserts a live defect that measurement disproves) | Enclosing guard `runner_shared.py:33697`; no rebinding over 33697-34032; preceding `wt_handle = None` at 33685 | yes |
| D-3 | E-05: narrow `collect` to `OSError`, narrow to a wider tuple, remove the block, or keep it blanket and document? | Keep blanket, spend the edit on a comment naming the unguarded injected `_extract` | `suppress(OSError)` (rejected: misses the likeliest escape); `(OSError, TypeError, AttributeError)` (rejected: indistinguishable from blanket in practice while looking principled); remove the block (rejected: the adjacent "A MISSING OR FAILED BASELINE IS NOT A FAILED ITEM" rule forbids failing a turn over a diagnostic aid) | `collect` has zero `try`/`except`; `_extract` unguarded and bound via `getattr(driver_module, "extract_suite_failures", None)`; the in-code rule quoted at the call site | yes |
| D-4 | Should review demand narrowing the other eighteen `except Exception` handlers it measured? | No: record the census (E-08), narrow only 32384 | Demand a full sweep (rejected: far larger change, weaker per-site justification, and only 32384 carries a MEASURED defect); say nothing (rejected: the plan's summary would then overclaim) | ast census at `56f7ab2d`; the backlog item `cv5n6t` scopes its ask to an audit of `execute_item_core`, which a written census satisfies | yes |
| D-5 | Is the `_extract` hole (F-10) something this plan must fix? | No: record it in a Deferred row and in the shipped comment, remedy undecided | Fix it here (rejected: `SuiteBaselineRun` is outside the declared `execute_item_core` scope and the fix belongs in the callee); file a backlog item now (rejected as the reviewer's unilateral choice between two legitimate remedies - guard the call, or correct the docstring - which is a contract judgement) | F-10's measurement; the plan's declared `Scope-Paths` and its stated `execute_item_core` bound | yes |
