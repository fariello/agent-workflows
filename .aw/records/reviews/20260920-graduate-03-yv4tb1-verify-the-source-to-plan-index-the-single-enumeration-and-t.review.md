# Review: verify the source-to-plan index, the single enumeration, and the backlog ledger, child yv4tb1 (Set graduate)

- Subject-Id: yv4tb1
- Subject-Type: ipd
- Reviewed-At: 2026-09-21
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed in an isolated lane worktree at HEAD `cd2e6adb`. `aw ipd lint --phase author` CONFORMING
before semantic review and `--phase review-finalize` CONFORMING after revision, so nothing found here
is structural.

DISCLOSURE: the same agent/model authored this plan, so this is a SELF-REVIEW, and its value rests on
RUNNING the plan's own mechanisms rather than re-reading its prose. That choice is what produced the
two serious findings, and one of them fired ON me: I ran the command this plan instructs an executor to
run and it mutated committed records.

THE PLAN'S CENTRAL INSIGHT IS CORRECT AND STRONGER THAN IT CLAIMED. Re-measured live:
`evaluate_backlog_close(repo, '6h7y2y', [])` returns `close=False` naming FOUR unexecuted IPD carriers,
and the fourth is `yv4tb1` ITSELF, so the predicate cannot fire while the plan that verifies the item
is pending. Neither `dispatch_orchestrator_item` nor `ipd_lifecycle.retire_orchestrator` contains the
string `backlog` (introspection), so no runner path closes the item on retirement. The plan's thesis
that an agent-executed child is the only legitimate place for this close is therefore sound, and the
deliberate-transition design follows from a measured mechanism rather than from caution.

THE FIRST SERIOUS FINDING IS A COMMAND THAT IS BOTH MALFORMED AND, IN ITS OBVIOUS CORRECTED FORM,
DESTRUCTIVE. E-04 prescribed `aw backlog set done <item> --status done`, which mixes the two mutually
exclusive spellings: with `--status` present the positional is the SELECTOR, so `done` is the selector
and the real id6 is ignored (exit 2, "selector 'done' is ambiguous (status)"). The natural next move for
a careful executor is to add `--dry-run` and check. THAT IGNORES THE FLAG AND PERFORMS THE TRANSITION.
It closed backlog `6h7y2y` from `graduated` to `done`, deleted the tracked file, wrote an untracked
copy under `done/`, and printed only `aw backlog set: <name> -> done` with no preview. I reverted it
(`rm` plus `git restore`), then reproduced it deliberately to confirm determinism, and reverted again.
Nothing was committed. Root cause is a one-word flag mismatch: `cli.py:12636` routes the `--status`
form to `backlog.run_set`, whose only write guard is `if not getattr(args, "apply", True)`
(`backlog.py:838`), and `aw backlog set` defines NO `--apply` flag, so the guard is unreachable; the
positional form routes to `status_set.run_set_command`, which reads `dry_run` (`status_set.py:1667`) and
previews correctly. Filed as backlog `19lmbe` (`bug`, `Blocks-Release: next`) with the reproduction and
the root cause. E-04 now mandates the positional spelling for SAFETY, requires a preview plus a
`git status` check first, and tells the executor how to recognize and revert an accidental mutation.

THE SECOND SERIOUS FINDING IS AN ASSERTION THAT CANNOT BE PERFORMED. E-02 required proving that "the
review sweep and the plan action resolve the same spec set", but `discover_specs` has exactly ONE caller
in `agent_workflows/` (`runner_shared.py:5564`) and the plan action resolves no specs at all, because
`enforce_requested_action` raises before resolution (`:14486`, `ACTION_IMPLEMENTED =
frozenset(("review",))` at `:14028`). There is no second surface to compare. Child 02's own E-02 states
that recording non-resolution and stopping is a legitimate outcome, so the comparison is CONDITIONAL on
a sibling that may deliberately not build it. Left as written, the most likely executor behavior was to
assert agreement between one real surface and one imagined one, which is a false pass of precisely the
kind this Set exists to prevent. E-02 now branches explicitly and forbids a fabricated comparison.

PR-104 WOULD HAVE STRANDED THE EXPECTED BRANCH. The plan's own likeliest outcome is NO backlog
transition (the item is already correct if child 02 deferred), and in that branch BOTH declared
`Scope-Paths` entries are declared-but-unmodified, which `aw ipd finalize` refuses without a
`--scope-ack` each. The bad escape available to an executor hitting that refusal is to perform the close
so a path looks touched, which would close a backlog item to tidy a scope report: the exact inversion
this plan exists to prevent. The scope check now names the acks and forbids it.

DISCLOSED SUITE FALLOUT FROM MY OWN EARLIER REVIEW, because it is my change and not a pre-existing
condition. My first review this session advanced sibling `2s0iym` to `reviewed`, which turned
`tests/test_orchestrator_retirement.py::RealRepositorySets::test_every_live_set_reaches_its_measured_verdict_for_its_measured_reason`
red: that row pins the LITERAL statuses of `commitguard`'s children. The test's own guidance is explicit
("RE-MEASURE and re-point the row ... NEVER to loosen the assertion"), so I re-pointed the two pinned
values and recorded why. The refusal reason (`RETIRE_REFUSED_UNFINISHED_CHILDREN`) and the child count
(3) are unchanged, so no property moved. Full suite afterwards: `1 failed, 7942 passed, 3 skipped,
2 xfailed`, the remaining failure being the ambient-environment `test_turn_bounds.py` case.

SCOPE: only this plan was a candidate. Read as evidence: `agent_workflows/backlog.py` (`run_set`
`:644-847`, the guard `:838`), `agent_workflows/cli.py` (`:12630-12651`),
`agent_workflows/status_set.py` (`:1667`, `:1283`), `agent_workflows/runner_shared.py`
(`discover_specs` `:5464`, its sole caller `:5564`, `ACTION_CHOICES`/`ACTION_IMPLEMENTED`
`:14027-14028`, `enforce_requested_action` `:14486`, scope auto-reconcile `:14195-14221`),
`agent_workflows/oc_runipd.py` (`process_backlog_close` `:1892`, call `:2715`, `evaluate_backlog_close`),
`agent_workflows/agy_runipd.py:1644`, `agent_workflows/ipd_lifecycle.py` (`:2108-2112`, `:3461-3464`),
`agent_workflows/check_engine.py`, `tests/test_spec_review_attestation.py:1707-1750`,
`tests/test_orchestrator_retirement.py:1566-1591`, `tests/test_turn_bounds.py:295-315`, sibling plans
`y9s4vm`, `jxxec8`, `iuxtjy`, `bwgyum`, and backlog `6h7y2y`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | BLOCKER | IN-SCOPE | A. Correctness / B. Safety | `agent_workflows/backlog.py:838`; `agent_workflows/cli.py:12636` | E-04's prescribed close command was MALFORMED (`set done <item> --status done` parses `done` as the selector, exit 2) and its natural `--dry-run` variant IGNORES the flag and MUTATES the tree. It closed `6h7y2y` graduated->done during this review; reverted and reproduced. Root cause: the `--status` handler guards on a nonexistent `apply` flag. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now mandates the POSITIONAL spelling `aw backlog set done 6h7y2y`, requires a `--dry-run` preview plus `git status` confirmation first, and documents how to recognize/revert an accidental mutation. The underlying defect is filed as backlog `19lmbe` (`bug`, `Blocks-Release: next`) and declared out of scope with a carrier. |
| PR-102 | HIGH | IN-SCOPE | E. Testing and verification | `agent_workflows/runner_shared.py:5564,14486,14028` | E-02's "the review sweep and the plan action resolve the same spec set" is NOT PERFORMABLE: `discover_specs` has one caller and the plan action resolves no specs (it raises first). An executor would likely assert agreement against a surface that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now branches on what child 02 actually shipped, requires an explicit SINGLE-SURFACE verdict citing the sibling's recorded decision when the second surface was not built, and V-02 FAILS a comparison presented as if two surfaces existed. |
| PR-103 | HIGH | IN-SCOPE | A. Correctness | live `evaluate_backlog_close(Path('.'), '6h7y2y', [])` | The plan recorded THREE blocking carriers; the predicate names FOUR, the fourth being `yv4tb1` itself. Understating this weakened the plan's own argument, since being a carrier is exactly why the close can never fire automatically here. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Step 0 and Findings corrected to four carriers, naming this plan, with the consequence stated (a deliberate tooled transition is required, not a defect). |
| PR-104 | MEDIUM | UNDER-SCOPE | G. Plan executability | `agent_workflows/ipd_lifecycle.py:2108-2112,3461-3464` | In the plan's OWN expected no-transition branch, both declared `Scope-Paths` are declared-but-unmodified and finalize refuses without a `--scope-ack` each. The available bad escape is closing the item to satisfy the fence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope check now names both `--scope-ack` flags, states the refusal is normal, and explicitly forbids transitioning the item to tidy the scope report. Noted a runner auto-acknowledges (`runner_shared.py:14215-14219`). |
| PR-105 | MEDIUM | IN-SCOPE | A. Correctness | measured during the accidental transition | The `graduated/` path in `Scope-Paths` is a SNAPSHOT: a `done` transition deletes it. The plan told the executor to read the item at that literal path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires resolving the item BY id6 at execution time, and warns that an item found in `done/` with a bare `status -> done` line may be an accidental `19lmbe` mutation rather than this Set's work. |
| PR-106 | MEDIUM | IN-SCOPE | E. Testing and verification | `aw backlog check` -> `16 violation(s)` | "‘aw backlog check` clean after any transition" is an UNREACHABLE bar: the tree already reports 16 pre-existing `backlog.id-duplicate` violations on other parties' items. An executor could read it as licence to fix another party's records. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Validation now judges on the DELTA, records the 16 pre-existing violations, and requires naming any violation that mentions `6h7y2y`. |
| PR-107 | LOW | IN-SCOPE | A. Correctness | `grep -n process_backlog_close`; `grep -n "def discover_specs"` | Three stale citations: `process_backlog_close` is called at `oc_runipd.py:2715` and `agy_runipd.py:1644` (not `:2680`/`:1608`), and `discover_specs` is at `runner_shared.py:5464` (not `:5460`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three corrected, with an added instruction to verify by SYMBOL rather than by line number, since the plan's own cited lines had drifted. |
| PR-108 | LOW | IN-SCOPE | E. Testing and verification | `tests/test_spec_review_attestation.py:1707` | "The AST guard" is ambiguous: the repo has several AST-walking tests. The intended one is `test_enumeration_reuses_the_shared_authority`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Named exactly in E-02, the conventions list, and V-02, with its two assertions described and its passing run recorded (`1 passed, 32 deselected in 0.45s`). |
| PR-109 | MEDIUM | UNDER-SCOPE | G. Plan executability (execution contract) | plan gate section | The gate lacked the "paste the ACTUAL output" honesty rule and a declaration-style scope fence, and instructed `aw ipd finalize` UNCONDITIONALLY, which is wrong when a runner owns begin/finalize. It also still advertised the dangerous `--status` spelling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now carries the paste-actual-output rule (with emphasis on the two branch-dependent items), a declaration-style fence naming the genuinely stop-worthy conditions, conditional finalize ownership, and the positional backlog spelling. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which `aw backlog set` spelling should E-04 mandate? | The POSITIONAL form, plus a mandatory `--dry-run` preview and `git status` check. | (a) Keep the `--status` form and warn about the bug, which leaves a tree-mutating command as the instruction; (b) require a hand edit, which the untooled-status gate exists to refuse. | Measured: the positional form routes to `status_set` and honors `dry_run` (`status_set.py:1667`); the `--status` form routes to `backlog.run_set` whose guard reads a nonexistent flag (`backlog.py:838`, `cli.py:12636`). | yes |
| D-2 | Should this review fix the `--dry-run` defect it discovered? | No: file it as backlog `19lmbe` and route the plan around it. | Fixing `backlog.py` here, rejected because a review may not change product code and because a verification plan editing the setter it depends on couples the fix to its only user. | Workflow rule "Review plans only. Do not change code"; the defect is independent of this plan's subject. | yes |
| D-3 | Is the accidental `6h7y2y` transition acceptable to leave, since `done` may eventually be correct? | No: revert fully and report. | Leaving it on the reasoning that the Set may close it later, rejected because the Set has not run and the history line would assert work that did not happen. | The three siblings are all `approved` and unexecuted, so no evidence supports `done`; AGENTS.md forbids committing another party's or unintended changes. | no |
| D-4 | How should E-02 handle a comparison whose second surface may not exist? | Branch explicitly, and forbid a fabricated comparison; require a SINGLE-SURFACE verdict citing child 02's decision. | (a) Drop the comparison, losing the parent's CID-2 property; (b) keep it unconditional, which invites asserting agreement with a nonexistent surface. | `discover_specs` has one caller (`runner_shared.py:5564`); `enforce_requested_action` raises at `:14486`; child 02's E-02 permits stopping short and its OQ-03 permits a follow-on Set. | yes |
| D-5 | Should the plan pre-authorize the no-transition finalize branch? | Yes: name both `--scope-ack` flags and forbid transitioning to satisfy the fence. | Saying nothing, which leaves the refusal to be met with the worst available workaround (closing a backlog item to tidy a scope report). | `ipd_lifecycle.py:3461-3464` refuses per untouched declared path, computed at `:2108-2112`. | yes |
| D-6 | What is the right `aw backlog check` bar? | The DELTA, with the 16 pre-existing violations recorded and any `6h7y2y` mention named. | "Clean", rejected as unreachable and as an implicit invitation to edit other parties' records in a shared checkout. | Measured `16 violation(s)`, all `backlog.id-duplicate`, none naming `6h7y2y`. | yes |
| D-7 | How to handle the `test_orchestrator_retirement.py` row my earlier review turned red? | RE-POINT the two pinned status values and record why. | (a) Loosen the assertion, which the test forbids in its own message; (b) revert `2s0iym` to `to-review`, which would undo a legitimate review to make a test green. | `tests/test_orchestrator_retirement.py:1574-1590` instructs "RE-MEASURE and re-point the row ... NEVER to loosen the assertion"; refusal reason and child count unchanged, so no property moved. | yes |
| D-8 | Is OQ-01 (who files the follow-on) resolvable from evidence? | Partly: resolve the MECHANICS, leave the authority preference to the maintainer. | Resolving it fully myself, rejected because "may this plan widen its own scope" is a convention the maintainer owns. | Measured that `aw backlog new --apply` lands only a one-line history (so the body must be written after) and writes to an undeclared path (so `--scope-reason` is required); the repository bug-gating rule decides the `Blocks-Release` question. | yes |
| D-9 | Is the plan's approach sound, or does the orchestrator-coverage premise need re-litigating? | Sound; no REPLAN. Every finding is an instruction-level repair. | REPLAN, rejected because the four-carrier measurement and the absent backlog call in both retirement paths confirm the premise exactly. | Live `evaluate_backlog_close` reason string; `'backlog' in inspect.getsource(...)` False for both `dispatch_orchestrator_item` and `retire_orchestrator`. | yes |

D-3 IS MARKED IRREVERSIBLE AND IS ESCALATED HERE RATHER THAN AS A BLOCKING QUESTION, because the act it
concerns is already complete and fully reverted, so a blocking question in the plan would gate future
work on a decision that is spent. The escalation is therefore DIRECT DISCLOSURE TO THE MAINTAINER in
this record and in the final report: during review I ran a command that closed backlog `6h7y2y` and I
reverted it; nothing was committed; the tree is byte-identical to HEAD for that item. It is recorded as
irreversible because a committed wrong close could not have been cleanly undone, which is precisely why
it is reported rather than merely noted.

No finding was left `OPEN` or `DEFERRED`, so no finding requires escalation as a blocking question
under the gate threshold (`HIGH`). The plan's single open question (OQ-01) is `Blocking: no` and was
NARROWED, not resolved, per D-8.
