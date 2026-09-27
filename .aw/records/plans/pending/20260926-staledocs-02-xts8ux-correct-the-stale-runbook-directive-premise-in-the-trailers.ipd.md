# IPD: Correct the stale runbook-directive premise in the _trailers_from_args docstring

- Date: 2026-09-26
- Kind: child
- Concern: The docstring of `work_cmd._trailers_from_args` explains why agent code commits carry no `AW-Run`/`AW-Item` trailers by saying the agent commits with raw `git commit -m msg -- <path>` "per the runbook directive". That directive was removed by plan y9vpvv (commitguard Order 02): every driver prompt now instructs `aw commit <plan> -- <paths>`. The conclusion (agent commits are untrailered) is still true; the stated cause is false, so a reader trying to close the gap is pointed at a directive that no longer exists.
- Scope: IN: the docstring of `agent_workflows/work_cmd._trailers_from_args` only. OUT: any behavior change, any new flag, wiring run/item ids into the agent's `aw commit` (that is the gap the docstring documents, and closing it is a separate design decision), the driver prompts.
- Scope-Paths: agent_workflows/work_cmd.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: t5ycse
- Set: staledocs
- Order: 2
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: xts8ux

## Workflow history
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-605 all FIXED. Premise re-measured: the stale phrase occurs exactly once in the package and aw commit exposes no id flag. Found that deferral carrier a6xbso is a live reviewed plan rewriting this same paragraph to the opposite conclusion, so added a premise-check E-01 that stops and retires if it landed first; replaced V-01's positive grep, which passed before any edit, with a four-probe docstring check measured to flip.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog t5ycse: Rewrite the _trailers_from_args docstring to name the real gap (aw commit gets no run/item ids).

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the `_trailers_from_args` docstring state the real remaining gap: the runner now instructs the agent to commit through `aw commit <plan> -- <paths>`, but supplies no run id or item id6 to that command, so the agent's code commits (the `base_head..HEAD` range `ipd_lifecycle` reads) still carry no `AW-Run`/`AW-Item` trailers.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Rewrite the docstring paragraph

- [ ] E-01 CHECK WHICH WORLD YOU ARE IN BEFORE EDITING (added in review, F-4). Run `python3 -c "import inspect; from agent_workflows import work_cmd as w; d = inspect.getdoc(w._trailers_from_args); [print(f'{p!r}: {p in d}') for p in ('runbook directive','AW_RUN_ID')]"` and `ls .aw/records/plans/executed/ | grep a6xbso || echo "a6xbso not executed (pass)"`. GENUINE STOP CONDITION: if `runbook directive` is already absent, or `AW_RUN_ID` is already present, or `a6xbso` is in `executed/`, then plan `a6xbso` has landed first and rewrote this paragraph to say the ids ARE now supplied. In that world this plan's premise is SPENT and executing it would write a new falsehood (see OQ-01). Do NOT edit: report it and retire this plan as superseded by `a6xbso`.
  - Depends on: none
  - Expected outcome: measured in review at this HEAD, `runbook directive` is `True`, `AW_RUN_ID` is `False`, and `a6xbso` is in `pending/` (`reviewed`, awaiting approval), so the premise holds and E-01 proceeds.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/work_cmd._trailers_from_args`, rewrite the paragraph beginning "THE RUNNER WIRING IS NOW PARTLY LANDED" so that: the WIRED half is unchanged (driver-side `oc_runipd.commit_backlog_close` passes `run_item_trailers(run_id, plan_id6)`); the DEFERRED half says the agent's code commits are now instructed through `aw commit <plan> -- <paths>` (the four prompt sites: the execution-directive item 4 in `oc_runipd` and `agy_runipd` default runbook text, and the two "commit through `aw commit <plan> -- <paths>`" lines in `runner_shared`'s review/verify prompts), which reaches this function, but the runner passes no `run_id`/`item_id6` (nor `trailers`) to that invocation and `aw commit` has no public flag for them, so `_trailers_from_args` returns `[]` for every agent commit. Remove the sentence claiming the commits "pass through no `offer_commit` call, and so cannot be reached by wiring one" and the "raw `git commit -m msg -- <path>` per the runbook directive" clause. Keep the final paragraph about not auto-deriving the plan id6.
  - Depends on: E-01
  - Expected outcome: the docstring names `aw commit` as the instructed path and "no ids supplied" as the cause; `grep -n "runbook directive\|git commit -m msg" agent_workflows/work_cmd.py` returns nothing.
  - Execution state: pending

### Task group 2: Verify no behavior changed

- [ ] E-03 Run the bare suite `python3 -m pytest` and confirm `git diff --stat` touches only `agent_workflows/work_cmd.py` and that the diff is inside the docstring (no code line changed).
  - Depends on: E-02
  - Expected outcome: suite passes; diff is docstring-only.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Docstrings and code comments are internal artifacts: dashes are fine, no user-facing prose rule applies.
- Commits via `aw commit xts8ux -- agent_workflows/work_cmd.py`; never push.
- Suite is run bare: `python3 -m pytest` (AGENTS.md "HOW TO RUN THE SUITE").

## Findings

| # | Location (HEAD 61ef21d8) | Finding |
| --- | --- | --- |
| F-1 | `work_cmd._trailers_from_args` (~:439-470), text "per the runbook directive, pass through no `offer_commit` call" | Stale premise, confirmed. The brief's line range ~:439-454 is right (the backlog item's :422-423 has drifted). |
| F-2 | `oc_runipd.py` "4. Commit only files you changed ... through `aw commit <plan> -- <paths>`" (~:1996), same text in `agy_runipd.py` (~:1958), `runner_shared.py` "commit through `aw commit <plan> -- <paths>`" (~:23845, ~:23938) | Confirmed. `grep -c "git commit -m msg"` is 0 in `oc_runipd.py`, `agy_runipd.py`, `runner_shared.py`, `engine.py`. |
| F-3 | `work_cmd._trailers_from_args` body: `getattr(args, "run_id", None)`, `getattr(args, "item_id6", None)` | `aw commit` exposes no `--run-id`/`--item-id6` flag (only a programmatic namespace attribute), and no prompt passes one, so the gap is exactly "no ids supplied". Confirmed; the brief's claim holds. Re-verified in review by driving `aw commit --help`: the flag list is `--no-color`, `--color`, `--agent`, `--json`, `--dir`, `--message/-m`, `--no-commit`, `--no-plan`, and nothing else. |
| F-4 | plan `a6xbso` (`.aw/records/plans/pending/20260926-trailread-01-a6xbso-stamp-aw-run-and-aw-item-trailers-on-the-agent-s-own-aw-comm.ipd.md`), its `- Scope-Paths:` and its E-03 | **THE DEFERRAL CARRIER IS A LIVE PLAN THAT REWRITES THIS EXACT PARAGRAPH, AND IT IS FURTHER ALONG THAN THIS ONE.** Found in review. This plan names `a6xbso` as the `Carrier:` for the deferred work but never says that `a6xbso` declares `agent_workflows/work_cmd.py` in its own `- Scope-Paths:` and that its E-03 instruction is to "Rewrite the docstring: keep the 'no public flag' reasoning, replace the paragraph saying the agent-commit half 'remains deferred' with a statement that the runner now exports the ids into the agent turn and this function reads them". That is the SAME paragraph this plan's E-01 rewrites, to a DIFFERENT end state. `a6xbso` is already `- Status: reviewed` with `- Readiness: go-pending-approval` and `- Priority: medium`, while this plan is `to-review` at `low`, so the more advanced plan is the one that will likely land first. Neither plan's text mentions the other. See the new OQ-01 for the ordering consequence and the non-conflict resolution. |
| F-5 | `work_cmd.py`, existing occurrences of the string `aw commit <plan>` | **V-01's SECOND GREP PASSES TODAY, BEFORE ANY EDIT.** Found in review. V-01 requires `grep -n "aw commit <plan>" agent_workflows/work_cmd.py` to show "at least one hit inside `_trailers_from_args`", but the grep is FILE-WIDE and the string already occurs twice outside that function (in `_default_commit_message`'s docstring and in a comment further down), while `_trailers_from_args` spans roughly lines 439-468. Measured in review: both existing hits are at lines outside that range, so the check returns success against the unedited file and proves nothing. A validation that is green before the work is done is worse than no validation. |

## Proposed changes (ordered, validatable)

1. E-01 confirm the premise still holds (and that `a6xbso` has not landed first).
2. E-02 rewrite the one docstring paragraph.
3. E-03 run the suite and confirm docstring-only diff.

## Deferred / out of scope (with reason)

- Supplying run/item ids to the agent's `aw commit` (env var, prompt-substituted flag, or other): a behavior and contract change with its own design questions (m73aet E-03 deliberately declined a public flag). Not this plan.
  - Carrier: a6xbso
  - CARRIER STATE, ADDED IN REVIEW (F-4): `a6xbso` is not a hypothetical follow-up. It is a LIVE plan at `- Status: reviewed` / `- Readiness: go-pending-approval` / `- Priority: medium` that declares `agent_workflows/work_cmd.py` in its own `- Scope-Paths:` and whose E-03 rewrites THIS docstring paragraph to say the ids are now supplied via `AW_RUN_ID`/`AW_ITEM_ID6`. So the deferral is real and correctly scoped, but the two plans write the same paragraph to different end states, and `a6xbso` is further along. E-01 checks for that before editing and OQ-01 records why this plan is still worth executing if it goes first.

## Scope check

- Over-scope: none.
- Under-scope: none.
- Sibling and carrier overlap on the declared path, recorded in review: plan `a6xbso` also declares `agent_workflows/work_cmd.py` and rewrites the same paragraph (F-4, OQ-01); sibling `staledocs` plans Order 01 (`3rsdbj`, six docs) and Order 03 (`fsme8o`, one release record) declare disjoint paths. NONE of this is a runtime hazard: the runner isolates each item in its own worktree and merges through the revalidation gate, so file overlap is not a reason to hold a queue. The `a6xbso` overlap is a STALENESS question (which text ends up in the tree), handled by E-01's premise check, not a contention one.

## Required tests / validation

No new test. The maintainer's standing rule is to test OUTCOMES only, and a docstring edit has no outcome to test; a test pinning docstring wording is exactly the source-text pin that rule forbids. Validation is the bare suite passing (proves nothing regressed) plus the premise check in V-01, the docstring-scoped probe in V-02, and the diff check in V-03.

## Spec / documentation sync

N/A: internal docstring only; no spec or user-facing doc describes this function.

## Open questions

### OQ-01: Plan `a6xbso` rewrites this same docstring paragraph to a different end state. Is this plan still worth executing, and in what order?

- Blocking: no
- Status: resolved
- Owner: this plan's author (resolved in review from repository evidence)
- Resolution or deferral rationale: YES, STILL WORTH EXECUTING, AND IT IS ORDER-INDEPENDENT, BUT THE EXECUTOR MUST CHECK WHICH WORLD IT IS IN FIRST (E-01 now does). The situation, measured in review: `a6xbso` (Set `trailread`, Order 1) declares `agent_workflows/work_cmd.py` in its `- Scope-Paths:` and its E-03 says to "replace the paragraph saying the agent-commit half 'remains deferred' with a statement that the runner now exports the ids into the agent turn and this function reads them". That is this plan's target paragraph, rewritten to say the gap is CLOSED rather than, as here, that the gap is real but differently caused. `a6xbso` is `reviewed` / `go-pending-approval` / `medium`; this plan is `to-review` / `low`.
  - IF `a6xbso` LANDS FIRST: this plan's premise is spent. The stale "runbook directive" clause will already be gone, and rewriting the paragraph to say "the runner passes no ids" would be a NEW false statement, since `a6xbso` makes it pass them via `AW_RUN_ID`/`AW_ITEM_ID6`. In that world the correct action is to RETIRE this plan as superseded rather than execute it, and E-01's stop condition now says exactly that.
  - IF THIS PLAN LANDS FIRST: no conflict and no wasted work. `a6xbso`'s E-03 replaces the paragraph wholesale, so it does not matter which wrong-or-right text it replaces; this plan meanwhile fixes a live falsehood that would otherwise sit in the tree for as long as `a6xbso` awaits approval, which is unbounded (it needs human sign-off).
  - WHY NOT JUST FOLD THIS INTO `a6xbso`: because `a6xbso` may never be approved, and its scope is a behavior change (env-var channel, both hosts' child env, conftest scrub, new tests) while this is a one-paragraph correction of a false statement. Making a factual doc fix wait on an unapproved behavior change leaves a known-false comment in the tree indefinitely.
  - NOT A RUNTIME HAZARD: the runner isolates each item in its own worktree and merges through the revalidation gate, so two plans naming `work_cmd.py` is not a concurrency problem. This is a STALENESS question about which text ends up in the tree, not a file-contention one.

### OQ-02: Should this plan add a test?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO. A test asserting docstring wording is precisely the production-source-text pin the maintainer ruled out on 2026-09-26 and that Set `srcguard` is removing 37 instances of. The V-01 docstring probe is a one-off EXECUTION-TIME check pasted as evidence, not a committed test, which is the distinction that makes it legitimate: it proves this edit happened without pinning the text against every future edit (including `a6xbso`'s, which would break such a pin immediately).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the two-probe output (`'runbook directive': True` and `'AW_RUN_ID': False` are the values measured in review at this HEAD) and the `a6xbso` disposition line. If either probe reads the other way, or `a6xbso` appears under `executed/`, paste that and STOP: the premise is spent and the plan is to be retired as superseded, not executed (OQ-01).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the rewritten paragraph and the output of `grep -n "runbook directive\|git commit -m msg" agent_workflows/work_cmd.py` (expected: empty; a bare `grep` finding nothing exits 1, which is the PASS case and aborts a `set -e` lane, so append `|| echo "absent (pass)"`). THEN, instead of the authored file-wide `aw commit <plan>` grep, which PASSES TODAY against the unedited file (F-5), run this docstring-scoped check and paste its output verbatim:

```sh
python3 -c "import inspect; from agent_workflows import work_cmd as w; d = inspect.getdoc(w._trailers_from_args); [print(f'{p!r}: {p in d}') for p in ('aw commit <plan> -- <paths>','runbook directive','git commit -m msg','cannot be reached by wiring one')]; print(); print(d)"
```

Required result: the FIRST probe `True` and the other THREE `False`, then the printed docstring showing the new wording. Each of the four was measured against the UNEDITED file in review and reads the opposite way today (`False, True, True, True`), so all four flip and none of them can pass vacuously. Reading the resolved docstring off the imported object is the durable form: it cannot drift with line numbers and cannot be satisfied by a match elsewhere in the file.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (expected `N passed`, no failures) and `git diff --stat` showing only `agent_workflows/work_cmd.py`, plus `git diff -U0 agent_workflows/work_cmd.py` showing every changed line lies inside the docstring.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a docstring-only edit in one function; no behavior change. The conclusion the docstring reaches (agent code commits carry no trailers) is TRUE today and stays; only the stated CAUSE changes, from a runbook directive that plan `y9vpvv` removed to the real one, which is that nothing supplies the ids to `aw commit` and no public flag exists for them. Verified in review: `aw commit --help` exposes only `--no-color`, `--color`, `--agent`, `--json`, `--dir`, `--message/-m`, `--no-commit`, `--no-plan`; the stale phrase occurs exactly once in the whole package; and the four prompt sites the new text cites all exist.

WHAT THE APPROVER SHOULD KNOW ABOUT TIMING (found in review, F-4). Plan `a6xbso` rewrites this SAME paragraph to a different end state (it makes the runner export `AW_RUN_ID`/`AW_ITEM_ID6`, so the gap this docstring describes is CLOSED rather than merely re-explained), and `a6xbso` is already `reviewed` / `go-pending-approval` / `medium` against this plan's `to-review` / `low`. Both orders are safe and neither wastes work: if this lands first, `a6xbso` replaces the paragraph wholesale anyway; if `a6xbso` lands first, this plan's premise is SPENT and E-01 stops rather than writing a fresh falsehood, and the right action is to retire this plan as superseded. Approving this plan is therefore not a bet on which lands first. What it buys is that a known-false comment does not sit in the tree for however long `a6xbso` waits on human sign-off.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/work_cmd.py`, docstring of `_trailers_from_args` only. Do not expand scope casually; if the work genuinely requires another file, make the edit and JUSTIFY it at finalize with `--scope-reason`. Genuine stop conditions: (a) E-01 finds the premise already spent (see above and OQ-01); (b) an unresolvable concurrent edit to `work_cmd.py`.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for the suite; never claim a pass that was not run. THE DOCSTRING CHECK MUST DISCRIMINATE: V-02's four probes were each measured against the unedited file and all four flip, so a check that passes without the edit is a FAILED validation (the authored file-wide `aw commit <plan>` grep was exactly that, F-5).

Commit ONLY `agent_workflows/work_cmd.py` through `aw commit xts8ux -- agent_workflows/work_cmd.py`; never `git add -A`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, transition with `aw ipd finalize xts8ux --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). Then set backlog `t5ycse` done citing the executed plan.
