# Review: Make the deferral ladder honor its injected validation runner instead of accepting it and discarding it

- Subject-Id: vfcnyd
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `95bf7ca1`, working tree clean. `aw ipd lint --phase author --agent` reported
`clean` before any edit, so the structural gate passed and every finding below is semantic. Suite
baseline taken before any edit: `3387 passed, 2 skipped, 3 warnings in 68.46s`.

THIS IS AN UNUSUALLY WELL EVIDENCED PLAN AND ITS CENTRAL DECISION IS CORRECT. Nine of its ten
findings reproduce as written, several of them exactly, and the one that decides the plan's whole
direction (F-4) reproduces decisively.

F-1 reproduces to the number: `reattempt_deferred_integrations` has 14 keyword-only parameters and 9
required ones including `validation_runner_for`, and an AST walk finds ZERO `ast.Name` loads of that
identifier inside the body, ZERO across `agent_workflows/`, exactly ONE `ast.keyword` and exactly ONE
`ast.arg`, both in `runner_shared.py`. F-2 reproduces: `_integrate` calls
`make_validation_runner(state, run_dir, item, ...)` on the LIVE item while the discarded lambda passes
`dict(item)`. F-4, THE DECIDING FINDING, reproduces on the mechanism that matters: driving the factory
with `dict(item)` writes `post_merge_revalidation` onto the copy and leaves
`REVALIDATION_CACHE_KEY not in item`, and because `revalidation_was_unmeasured` reads that record off
the LIVE item, the copy arm returns False where the live arm returns True; `record_integration_refusal`
gates its `fail-merge` to `merge-unchecked` reclassification on exactly that predicate. So option (a)
as the parameter is written really would report a harness fault as a measured merge conflict. F-5, F-6,
F-7, F-8 and F-9 all hold: the deletion is verbatim-applicable (verified in memory: both target strings
occur exactly once, the result parses, and the arity drops to eight required), neither host re-exports
the ladder, the only residual mention afterward is precisely the `attributed_away_failure_ids`
docstring F-6 predicts, and `tests/test_forkresid_shared_shells.py` really does pass in 0.33s through
the fail-closed arm.

I ALSO VERIFIED THE PLAN'S PRESCRIPTIONS ARE FEASIBLE, which is where the real findings are. Driving
both hosts through `retry_deferred_integrations` on a fixture built as E-01 specifies produced
`suite calls=1`, a path under `<run_dir>/revalidation/revalidate-<tree>`, and the record on the LIVE
item, on `oc` and `agy` alike. Both E-02 mutations redden it: mutation (i) yields 0 suite calls, and
mutation (ii) yields 1 suite call with the record absent from the live item, confirming the plan's
claim that (ii) is caught by the live-item assertion SPECIFICALLY.

FOUR PROBLEMS, one of which would have cost the executor a debugging detour and one of which is a
straightforward measurement error.

FIRST, E-01 PRESCRIBES A FIXTURE THAT SILENTLY DEPENDS ON A `git rev-parse` FALLBACK IT NEVER NAMES.
The item says the fixture must carry `worktree_base`/`worktree_branch` on the latest attempt because
`resolve_lane_endpoints` reads the attempt first. True as far as it goes, but that function resolves
`head` from `item["lane_head"]`/`item["preserved_head"]` ONLY, and neither is an attempt field:
measured, an attempt-only fixture returns `('abc123', 'aw/lane/x', '')`. The fixture works anyway,
because the factory recovers with `git rev-parse <branch>` when `head` is empty and `repo_raw` is set,
which means the fixture's real requirements are a resolvable `state["repo"]` AND a branch that exists
in that repo. An executor who builds the fixture the item describes and omits the real base commit or
the real branch lands in the fail-closed arm with the suite never invoked, which is precisely the
vacuous-pass trap E-01 exists to avoid. PR-101.

SECOND, AND THIS IS THE ONE THAT WOULD HAVE COST TIME, E-01's stub suite checker has an UNSTATED
RETURN CONTRACT and the obvious guess is wrong. `make_integration_validation_runner` reads
`result.passing`, `result.reason`, `result.failures` and `result.exit_code` by `getattr`, so a stub
returning a tuple (the natural shape, and what `run_suite_check`'s own callers destructure elsewhere)
yields `passing=False` by default and the runner refuses. Measured: a tuple-returning stub produced
`verdict=False` with a reason about a `not-started` suite baseline, which reads like a fixture bug and
is not one. An attribute-carrying stub produced `verdict=True`. E-01 named none of this. PR-102.

THIRD, F-3's CALL-SITE COUNT IS WRONG. It says "all eight of its call sites pass a 2-arity callable".
Measured at HEAD: `integrate_under_repository_lock` has TEN production call sites in `runner_shared.py`
plus four in `tests/test_concurrent_driver_guard.py`. The SUBSTANCE is untouched and in fact stronger
(all ten pass a 2-arity `integrate` and none passes a runner; the function's parameter list contains no
runner at all), which is exactly why the number should be right: the finding is load-bearing for
OQ-01's rejection of option (a). PR-103.

FOURTH, THE PLAN NEVER STATES THAT THE REVIEW PATH HAS NO RUNNER AT ALL, which a reader of E-03 will
wonder about within a minute. `_integrate_review` calls `integrate_review_lane_branch(repo, handle,
id6)` with THREE arguments and no runner, because a review revalidates nothing. That asymmetry is the
strongest available evidence that a per-item runner injection at the ladder is the wrong shape, and the
plan's "Deferred" section declines the generality without citing it. PR-104.

Two smaller items: the plan's own history inherits the backlog item's "two host call sites" framing in
one place while correcting it everywhere else (PR-105), and V-03 asks for a repository-wide search
returning ZERO hits at a point where exactly one hit legitimately remains until E-04 lands (PR-106).

SEPARATELY, THE PLAN ARRIVED FAILING `aw check plans` on history ordering (PR-107), exactly as the
previous plan in this review sweep did. `aw ipd lint` reported `clean` at `author` across it, so the
structural preflight does not cover this class. Two independent plans carrying the identical defect
points at the authoring path rather than at either author, and is worth a maintainer's attention even
though each instance is a one-line fix.

NOTE ON GRADE AND GATE. `- Work-Kind: bug` and `- Blocks-Release: next` are inherited from `iv4n2c`
and are KEPT. I considered whether an inert parameter with no reachable wrong behavior is really a
release blocker, and it is defensible on this repository's own rule: F-4 measures that the one
direction a future caller would take it produces a WRONG REFUSAL KIND shown to an operator, so the
latent defect has a user-perceptible failure mode rather than being pure tidiness. Recorded as decision
D-3 rather than silently accepted.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | E. Testing / G. Plan executability | `runner_shared.resolve_lane_endpoints` (`head` reads `item["lane_head"]`/`item["preserved_head"]` only); `make_integration_validation_runner`'s `if not head and branch and repo_raw: _run_git(..., ["rev-parse", branch])`; measured `resolve_lane_endpoints({"attempts":[{"worktree_base":"abc123","worktree_branch":"aw/lane/x"}]}) -> ('abc123', 'aw/lane/x', '')` | E-01'S FIXTURE PRESCRIPTION IS INCOMPLETE IN THE DIRECTION THAT PRODUCES A VACUOUS PASS. The item requires `worktree_base`/`worktree_branch` on the latest attempt and justifies it by `resolve_lane_endpoints` reading the attempt first, which is true but does not reach `head`: that value comes only from two ITEM keys, neither of which is an attempt field, so an attempt-only fixture resolves `head` to the empty string. The fixture works solely because the factory falls back to `git rev-parse <branch>`, which needs `state["repo"]` set AND the branch to exist in that repository. Neither requirement is stated. An executor who satisfies the stated requirement but not the unstated ones lands in the fail-closed arm with ZERO suite invocations, which is exactly the vacuous pass F-9 disqualifies the existing module for. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now states all three fixture requirements (a real base commit reachable as `state["repo"]`, a real lane branch resolvable by `rev-parse`, and the attempt fields), names the `rev-parse` fallback as the mechanism that makes `head` resolvable, and requires the test to ASSERT the suite ran (count 1) precisely so a fixture regression cannot pass vacuously. V-01 requires the resolved endpoint triple to be pasted. Added F-10. |
| PR-102 | HIGH | IN-SCOPE | E. Testing / G. Plan executability | `make_integration_validation_runner`: `passed = bool(getattr(result, "passing", False))`, plus `getattr(result, "reason", ...)`, `getattr(result, "failures", ())`, `getattr(result, "exit_code", 0)`; measured both stub shapes | E-01 SPECIFIES AN INJECTED `run_suite_check` STUB AND NEVER STATES ITS RETURN CONTRACT, AND THE NATURAL GUESS FAILS SILENTLY. The factory reads four ATTRIBUTES off the result by `getattr` with defaults, so a stub returning a tuple gets `passing=False` and the runner refuses. Measured: a tuple-returning stub yields `verdict=False` with a reason naming a `not-started` suite baseline, which reads like a fixture defect and sends the executor into `revalidation_baseline_for`; an attribute-carrying stub yields `verdict=True`. Worse for this plan specifically, the failing shape still invokes the suite once and still records on the live item, so E-01's three stated assertions can all PASS while the verdict is wrong, hiding the mistake until E-02's mutations behave confusingly. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now names the four attributes the stub must carry and states that a tuple-returning stub is read as failing. Added F-11 with both measurements. V-01 requires the stub definition to be pasted. |
| PR-103 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | AST census of `integrate_under_repository_lock` call sites: 10 in `agent_workflows/runner_shared.py`, 4 in `tests/test_concurrent_driver_guard.py`; its parameter list is `(repo, item, handle, *, state, holder_label, integrate, progress, run_checked, timeout, sleep, now)` | F-3 SAYS "ALL EIGHT OF ITS CALL SITES"; THERE ARE TEN IN PRODUCTION. The substance is unaffected and is actually stronger than stated: every one of the ten passes a 2-arity `integrate` (four named `_publish`, four lambdas, two `do_integrate`) and NONE passes a runner, and the function has no runner parameter to pass one to. The number matters because F-3 is load-bearing for OQ-01's rejection of option (a): a reader who re-counts and gets ten may distrust the finding that carries the plan's decision. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 corrected to ten production sites (plus four in the guard test) with the arity breakdown, and restated so the decisive fact is the absent runner parameter rather than the count. |
| PR-104 | MEDIUM | UNDER-SCOPE | C. Architecture | `runner_shared.retry_deferred_integrations`'s `_integrate_review`, whose whole body is `return integrate_review_lane_branch(repo, handle, str(item.get("id6") or ""))` (3 args, no runner), beside `_integrate`'s 4-argument call | THE PLAN OMITS ITS OWN STRONGEST ARCHITECTURAL ARGUMENT. The ladder already dispatches to a review adapter that takes NO validation runner, because a review revalidates nothing. So the two adapters the ladder chooses between disagree about whether a runner exists at all, which is decisive evidence that a single ladder-level `validation_runner_for` is the wrong shape: it could not be meaningful for one of the two paths it would serve. The plan's Deferred section declines the generality on GUIDING_PRINCIPLES P6 (no speculative generality) without citing this, leaving the strongest reason unstated and inviting a future reader to re-add the parameter. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-12 recording the asymmetry; the Deferred row declining a genuine per-item choice now cites it; E-04(a) must state it in the docstring, so the rejected alternative is refused on a structural reason and not only on a measurement. |
| PR-107 | HIGH | IN-SCOPE | G. Plan executability / lifecycle | `aw check plans --agent` at HEAD `95bf7ca1` listed this plan under `check.lifecycle-transition-invalid`; `ipd_lifecycle._plan_status_events` on the AS-COMMITTED text (`git show HEAD:<path>`) derives `[to-review, draft]`; the checker assumes newest-first | THE PLAN ARRIVED FAILING THE REPOSITORY'S OWN CROSS-TREE CHECK. Its `## Workflow history` had the `draft` line ABOVE the `to-review` line, so the derived status stream read `to-review -> draft`, a backwards transition. Verified against `git show HEAD:<path>` that this predated the review. `aw ipd lint` reported `clean` at `author` straight through it, so the deterministic structural preflight gives no warning for this class and is not a substitute for `aw check plans`. This is the SECOND plan in this review sweep carrying the identical defect, which suggests an authoring-template or generator issue rather than a one-off slip. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Swapped the two lines into newest-first order. Verified: `_plan_status_events` now derives `draft -> to-review -> reviewed`, and `aw check plans --agent` reports 0 findings naming this plan (repository total went 56 -> 55). |
| PR-105 | LOW | IN-SCOPE | Step 1 evidence accuracy | Backlog `iv4n2c` says "the two host call sites that dutifully pass a lambda (oc_runipd.py:2727, agy_runipd.py:1639)"; measured: `grep -c validation_runner_for` is 0 in both host modules and 3 in `runner_shared.py`; the plan's Concern correctly says "its one producer" | THE PLAN CORRECTS THE ITEM'S STALE TWO-HOST FRAMING EVERYWHERE EXCEPT ONE PLACE. F-6 quotes the `attributed_away_failure_ids` docstring's "Both hosts' deferral re-attempt lambdas" without noting that the plural is itself already stale (the lambdas were consolidated into the shared ladder), so E-04(b)'s replacement text could reproduce the same stale plurality in a different sentence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 now records that the docstring's "Both hosts'" plural is ALREADY stale at HEAD, independently of this plan, and E-04(b) is instructed not to carry the plurality into the replacement. |
| PR-106 | LOW | IN-SCOPE | E. Testing / internal consistency | V-03 as authored demands a search "restricted to `agent_workflows/` and `tests/` returning ZERO hits"; measured after applying E-03's two deletions in memory, exactly ONE hit remains, in `attributed_away_failure_ids`' docstring, which is E-04's job to remove | V-03 DEMANDS AN IMPOSSIBLE RESULT AT ITS OWN CHECKPOINT. E-03 removes the code occurrences and E-04 removes the docstring one, so a zero-hit search cannot succeed until E-04 lands. As written an executor validating E-03 in order either records a failure against correct work or is pushed to do E-04's edit early and validate it in the wrong item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 now expects exactly ONE remaining hit, names it as the `attributed_away_failure_ids` docstring, and requires that it be a DOCSTRING hit and no code hit; the zero-hit assertion is V-04's, where it is achievable. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-101/PR-102: should the reviewer supply the missing fixture and stub contracts, or escalate them as blocking questions? | Supply them, having demonstrated each on a real fixture and pasted the measurements into the plan | Escalate as blocking OQs, which would hold a release-gating bug on a maintainer for facts the repository answers; leave them for the executor to discover, which is the debugging detour the review exists to prevent | The repository answers both without judgement: `resolve_lane_endpoints`' body shows `head` reads two item keys, the factory's `rev-parse` fallback is right there, and the four `getattr` reads define the stub contract. I drove both hosts end to end and both E-02 mutations to confirm. No scope, priority or risk call is involved | yes |
| D-2 | Does the plan's decision (option (b), deletion) survive independent re-measurement, or should the review reopen OQ-01? | It survives; OQ-01 stays `resolved` and is strengthened rather than reopened | Reopen OQ-01 as blocking so the maintainer picks between the two options; rewrite the plan to honor the parameter correctly (option (a) done properly) | F-4's mechanism reproduces decisively: the copy arm leaves `REVALIDATION_CACHE_KEY` absent, so `revalidation_was_unmeasured` returns False where the live arm returns True, and `record_integration_refusal` gates the `fail-merge`->`merge-unchecked` reclassification on exactly that. PR-104 adds that the review adapter takes no runner at all, so a ladder-level injection could not be meaningful for one of the two paths. Both point the same way | yes |
| D-3 | `- Work-Kind: bug` with `- Blocks-Release: next` for a parameter that is inert today: keep the gate or question it? | Keep both, and record the reasoning rather than accepting it silently | Ask the maintainer to re-grade it as a `chore`, since no shipped behavior is currently wrong | The repository's rule keys on user-perceptible impact, and F-4 measures a real one in the one direction a future caller would take the parameter: an operator would be shown `fail-merge` (a measured merge conflict) for a harness fault that could not measure, with the record explaining it written to a discarded dict. A latent defect with a measured wrong-answer failure mode is defensibly a bug. The gate is also inherited from `iv4n2c`, and AGENTS.md requires inheritance rather than re-decision | yes |
| D-4 | PR-106: fix V-03's impossible zero-hit assertion by relaxing it, or by moving E-04's docstring edit into E-03? | Relax V-03 to expect exactly one docstring hit and keep the zero-hit assertion in V-04 | Merge E-04(b) into E-03 so a zero-hit search succeeds at that checkpoint | The two edits have genuinely different subjects (code versus a falsified justification elsewhere in the module) and the plan's E/V bijection is otherwise clean; merging them to satisfy a validation string would make one item carry two concerns, which the right-sizing rule forbids | yes |

### Round 1 close

All seven findings FIXED in place. No finding is left `OPEN` or `DEFERRED`, so no escalation to a
`- Blocking: yes` question is owed under the gate threshold. Both pre-existing open questions (OQ-01,
OQ-02) were independently re-verified and remain correctly `resolved`; no new open question was
created.
