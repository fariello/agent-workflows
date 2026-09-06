# Review: runner-owned orchestrator retirement (spec 77tr3o)

- Subject-Id: 77tr3o
- Subject-Type: spec
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE

## Round 1

Reviewed at HEAD `844d195c`. Every factual claim in the spec was re-verified against the code and the
durable run records rather than carried over from the authoring pass.

DISCLOSURE, because it bears on how much this review is worth: I authored the spec in the same session,
so this is a self-review, not an independent one. It is recorded because the repository requires a
review record to exist before `to-review -> reviewed`, and because a re-measurement pass has real value
even when the author performs it. It is NOT evidence that a second party judged the design. The
maintainer supplied the design contract itself, so the substantive question this spec answers ("what
SHOULD the runner do") is his answer, not mine; what I verified is that the measurements are true and
the requirements are consistent with them.

VERIFIED CLAIMS, each re-run for this review:

- Zero successes, 28 deferrals. `grep -rh orchestrator-finalized .aw/records/runs/*/events.jsonl | wc -l`
  returns `0`; `orchestrator-deferred` returns `28` across 15 distinct orchestrator id6s. This is the
  spec's load-bearing measurement and it holds.
- The two refusal reasons are distinct and both reproduce. Run `run-20260905T211011Z-3780617` records
  `5e4sb6 | not-all-children-executed | unfinished: []` and `rh5tt6 | finalize-refused | unfinished: []`.
  I reproduced the `rh5tt6` path verbatim with the exact argv `finalize_orchestrator` builds
  (`oc_runipd.py:773-796`) and got the "no begin receipt" refusal; after writing a receipt with
  `aw ipd begin` I got the six `IPD-S404` E/V findings. The probe receipt was deleted and
  `.aw/state/ipd-lifecycle/` carries no `rh5tt6` entry.
- The gate predates the code it blocks. `99760832` (2026-08-24) landed the gated terminal transition;
  `801dd28a` (2026-08-27) added `finalize_orchestrator`. `git merge-base --is-ancestor` confirms the
  ordering, so the rollup was written against a gate that already refused it and has never worked.
- `dependency-blocked` is terminal. Present in `TERMINAL_STATES` (`oc_runipd.py:254-272`); the selection
  filter admits only `queued` (`oc_runipd.py:4071`, `:6919`). So the deferral is a dead end, as `kxkc04`
  states.
- The linter has no orchestrator concept. `grep -c orchestrator agent_workflows/ipd_lint.py` is `0`, and
  `check_checkpoint` (`:694-725`) applies the `pre-transition` E/V requirements unconditionally.
- The agy asymmetry is real, verified by object identity rather than by grep: `action_for`,
  `finalize_orchestrator` and `_set_children_all_executed` are all absent from `agy_runipd`, and
  `agy.determine_action('approved')` returns `'execute'` where `oc.action_for('orchestrator','approved')`
  returns `'orchestrate'`. So `aw agy run` would agent-execute an orchestrator.
- The on-disk resolver answers the Set-completeness question. `selectors.resolve(repo,'plans',<setid>)`
  plus `ipd_lint.parse` yields every member's `Id`/`Order`/`Kind`/`Status` across `pending/` and
  `executed/`, measured for `wslayout` (5 children executed), `rununify` (2 executed) and `lanectn`
  (4 executed, 2 approved).
- Section 2.5 is the spec's most important guard and it is correct. `rununify` looks complete on disk,
  yet `5e4sb6`'s child table declares a row `03+` that was never authored, so a naive
  "all existing members executed" rule would wrongly retire it. I confirmed the row exists in the plan
  text and that only children `01` and `02` resolve to files.

FINDINGS: none blocking.

- F-1 (LOW, accepted as-authored): R-5 and R-6 state WHAT must be resolved without prescribing HOW,
  and OQ-1/OQ-2 carry the alternatives. That is appropriate for a spec whose implementation choice
  genuinely needs the code in front of it, and the binding constraint (no new route by which a child
  plan reaches `executed` without evidence) is stated, which is the part that must not be left open.
- F-2 (LOW, noted): the spec asserts `AGENTS.md:42` is false as written. Verified: the managed block
  claims self-finalization works and instructs agents not to raise it. R-11 requires correcting it in
  the same change. Worth flagging that the text lives in `engine.py`'s managed-block source, not in
  `AGENTS.md` directly, so the implementing plan must edit the generator.
- F-3 (INFORMATIONAL): the spec's out-of-scope list names three adjacent live defects (`nueip1`, the
  `EXECUTION_SUCCESS_STATES` edge acceptance, and the `aw set executed` worker-role bypass that reopens
  `i452hf`). Keeping them out is right; each is separately filed or separately observable.

`aw check specs` reports `12 specs checked, 0 errors, 0 warnings` with this spec present.

Verdict APPROVE: the measurements are accurate, the requirements follow from them, and the two open
questions are genuinely implementation-time decisions rather than unresolved design.
