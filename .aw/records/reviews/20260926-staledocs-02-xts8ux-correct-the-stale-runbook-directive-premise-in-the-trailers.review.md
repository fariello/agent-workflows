# Review findings: plan xts8ux

- Subject-Id: xts8ux
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated lane worktree. Structural preflight `aw ipd lint --phase author --detail`
CONFORMED (exit 0, no advisory) before revision. No pre-review snapshot was needed: `git status
--porcelain` was empty and the lane input under `.aw/state/lane-inputs/rev-8/` is byte-identical to
the tracked plan.

THE PREMISE IS CORRECT AND EVERY PART OF IT WAS RE-MEASURED. The stale text is there, verbatim, in
`work_cmd._trailers_from_args`: "Those are made by the agent running raw `git commit -m msg --
<path>` per the runbook directive, pass through no `offer_commit` call, and so cannot be reached by
wiring one". The directive really is gone: `grep -c "git commit -m msg"` is 0 in `oc_runipd.py`,
`agy_runipd.py`, `runner_shared.py` and `engine.py`, and the phrase survives in exactly ONE place in
the whole package, this docstring. The four replacement prompt sites all exist (`oc_runipd` runbook
directive 4, its `agy_runipd` twin, and two `runner_shared` review/verify prompt lines). The "WIRED"
half the plan preserves is genuinely wired: `runner_shared.commit_backlog_close` passes
`trailers=_gch.run_item_trailers(run_id, plan_id6)`. And F-3 holds: `aw commit --help` exposes only
`--no-color`, `--color`, `--agent`, `--json`, `--dir`, `--message/-m`, `--no-commit`, `--no-plan`, so
there is no public flag for the ids and "no ids supplied" is the accurate cause. The plan's diagnosis
is right and its replacement text is right.

**THE DEFERRAL CARRIER IS A LIVE PLAN THAT REWRITES THIS EXACT PARAGRAPH, AND IT IS FURTHER ALONG.**
This is the finding that justifies the review. The plan's Deferred section names `a6xbso` as the
`Carrier:` for the deferred work, which is correct, but it does not say what that plan actually does
to this file. `a6xbso` declares `agent_workflows/work_cmd.py` in its own `- Scope-Paths:`, and its
E-03 instruction is to "Rewrite the docstring: keep the 'no public flag' reasoning, replace the
paragraph saying the agent-commit half 'remains deferred' with a statement that the runner now
exports the ids into the agent turn and this function reads them". That is the same paragraph
`xts8ux` E-01 rewrites, to the OPPOSITE conclusion: this plan says "the runner passes no ids",
`a6xbso` makes it pass them via `AW_RUN_ID`/`AW_ITEM_ID6` and says so. `a6xbso` is `reviewed` /
`go-pending-approval` / `medium`; this plan is `to-review` / `low`. Neither plan's text mentions the
other.

I resolved it rather than escalating, because the repository answered it. Both orders are safe and
the answer is not symmetric, which is why it needed writing down. If THIS plan lands first there is
no conflict at all: `a6xbso` replaces the paragraph wholesale, so which wrong-or-right text it
replaces is immaterial, and meanwhile a known-false comment stops sitting in the tree for however
long `a6xbso` waits on human sign-off (unbounded, since it needs approval). If `a6xbso` lands first
the premise is SPENT, and executing `xts8ux` would write a NEW falsehood: the paragraph would then
correctly say the ids are supplied, and rewriting it to say they are not would reintroduce exactly
the class of defect this plan exists to fix. So the plan needed a premise check, which it did not
have. E-01 is now that check (probe the live docstring for `runbook directive` and `AW_RUN_ID`, and
check whether `a6xbso` is in `executed/`), with an explicit instruction to retire rather than edit if
the premise is spent. I deliberately did NOT add an `Item-Dependencies` edge: an edge would force an
order that neither plan needs and would wedge this one if `a6xbso` is never approved.

**THE PLAN'S POSITIVE CHECK PASSED BEFORE ANY EDIT.** V-01 required `grep -n "aw commit <plan>"
agent_workflows/work_cmd.py` to show "at least one hit inside `_trailers_from_args`", but the grep is
FILE-WIDE while the expectation is function-scoped. Measured: the string already occurs twice in the
file today, at `_default_commit_message`'s docstring and a comment further down, both OUTSIDE the
439-468 range of the function under edit. So the check returns success against the unedited file and
proves nothing. Worse, it is the only POSITIVE half of V-01 (the other grep is a negative
absence check), so the pair could report "the new text is present" when nothing had been written.
I replaced it with a docstring-scoped probe that reads the resolved docstring off the imported
object and tests four strings at once, and I measured all four against the unedited file to confirm
each one FLIPS: `'aw commit <plan> -- <paths>'` is False today and must become True, while `'runbook
directive'`, `'git commit -m msg'` and `'cannot be reached by wiring one'` are all True today and
must become False. Reading `inspect.getdoc` also cannot drift with line numbers and cannot be
satisfied by a match elsewhere in the file, which is the durable form for this kind of check.

ON MY OWN FIRST ATTEMPT AT THAT FIX, recorded because it was wrong in the same way. My initial
replacement probed for the substring `aw commit` in the docstring, and I drove it before shipping it:
it returns True against the UNEDITED docstring, because the existing text already contains "routing
agent commits through `aw commit`". So my first fix reproduced the exact defect I was fixing. The
probe now uses the full `aw commit <plan> -- <paths>` form, measured False today, and pairs it with
three negative probes so the check cannot pass on a partial edit.

ON THE STRUCTURAL CONSEQUENCE of adding a precondition item. I first added it as `E-01a`, which the
linter correctly REFUSED (`IPD-I302`: execution-section leaf must be a valid `E-*` item), so the
items were renumbered (premise check E-01, docstring rewrite E-02, suite E-03) with `V-01` added,
`Highest E allocated` raised to 03, the dependency chain rewired to E-01 -> E-02 -> E-03, and the
Proposed-changes list and Required-tests pointers updated. The E/V bijection is 3/3 and the linter
reports `conforming`.

ON THE TEST QUESTION, which the plan answered correctly and which I checked rather than accepted. No
test is added, and that is right: a test asserting docstring wording is the production-source-text
pin the maintainer ruled out on 2026-09-26 and that Set `srcguard` is removing 37 instances of. It
would also break immediately when `a6xbso` rewrites the same paragraph, which is a concrete
demonstration of why such pins are wrong rather than an abstract objection. The V-02 probe is a
one-off execution-time check pasted as evidence, not a committed assertion, and I recorded that
distinction as OQ-02 so a later reader does not mistake one for the other.

ON THE BACKLOG CLOSE, driven rather than assumed. `evaluate_blocking_close(repo, <t5ycse>, "done")`
returns `legitimate=True`, severity `ok`, "no release gate to preserve", path `DE-GATED`, because
`t5ycse` carries no `- Blocks-Release:`. That is correct rather than an omission: both the item and
the plan are `- Work-Kind: chore`, which is outside the repository's gating set (`bug`). So unlike
sibling `3rsdbj`, this close does not fail closed while the plan is pending, and the gate's
after-execution ordering is still the right instruction.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | MEDIUM | UNDER-SCOPE | A. correctness; G. executability | `a6xbso` front matter (`- Status: reviewed`, `- Readiness: go-pending-approval`, `- Priority: medium`, `- Scope-Paths:` including `agent_workflows/work_cmd.py`) and its E-03 ("replace the paragraph saying the agent-commit half 'remains deferred' with a statement that the runner now exports the ids into the agent turn and this function reads them") | **THE DEFERRAL CARRIER REWRITES THIS EXACT PARAGRAPH TO THE OPPOSITE CONCLUSION, AND IS FURTHER ALONG.** The plan names `a6xbso` as `Carrier:` without saying it declares the same file and rewrites the same paragraph. If `a6xbso` lands first, executing this plan writes a NEW falsehood (asserting no ids are supplied when they are), which is the very defect class this plan exists to remove. The plan had no premise check, so an executor would edit blindly. | C:Low; U:Low; S:Low; F:Medium (a fresh false statement in the tree); Overall:Low | FIXED | F-4 added. New E-01 probes the live docstring for `runbook directive`/`AW_RUN_ID` and checks whether `a6xbso` is executed, with an explicit STOP-and-retire instruction if the premise is spent; V-01 added; OQ-01 records why both orders are safe and why no `Item-Dependencies` edge was added (an edge would wedge this plan if `a6xbso` is never approved). The gate tells the approver the timing plainly. |
| PR-602 | MEDIUM | UNDER-SCOPE | E. verification | measured: `grep -n "aw commit <plan>" agent_workflows/work_cmd.py` returns hits at two lines today, both OUTSIDE `_trailers_from_args` (roughly 439-468); the function's docstring does not contain the string | **V-01's ONLY POSITIVE CHECK PASSED BEFORE ANY EDIT.** The expectation was function-scoped ("at least one hit inside `_trailers_from_args`") but the command was file-wide, and the string already occurs twice elsewhere. So the pair of greps could report the new text present when nothing was written, which is worse than no validation because it manufactures confidence. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-5 added. Replaced with a docstring-scoped `inspect.getdoc` probe testing four strings, each measured against the unedited file to confirm it FLIPS (`aw commit <plan> -- <paths>` False->True; `runbook directive`, `git commit -m msg`, `cannot be reached by wiring one` True->False). The negative grep also gained a `\|\| echo "absent (pass)"` pass-guard, since a bare `grep` finding nothing exits 1 and would abort a `set -e` lane on the success path. |
| PR-603 | LOW | IN-SCOPE | E. verification (the reviewer's own first fix) | driven: `'aw commit' in inspect.getdoc(work_cmd._trailers_from_args)` is True TODAY, because the existing text says "routing agent commits through `aw commit`" | **MY FIRST REPLACEMENT PROBE REPRODUCED THE DEFECT IT FIXED.** The initial substring I chose was already present in the unedited docstring, so the new check would also have passed vacuously. Caught by driving it before shipping it. Recorded rather than quietly corrected, because a reviewer who writes an unverified verification has done the thing this workflow exists to catch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The probe uses the full `aw commit <plan> -- <paths>` form (measured False today) and is paired with three negative probes, so a partial edit cannot satisfy it. |
| PR-604 | LOW | IN-SCOPE | G. executability (structural) | `aw ipd lint --phase review-finalize` -> `IPD-I302 (line 34): execution-section leaf must be a valid E-* item` after the precondition was added as `E-01a` | **THE ADDED PRECONDITION NEEDED REAL RENUMBERING, NOT A SUFFIXED ID.** An `E-01a` leaf is not a valid item id and the linter refused it, which would have blocked `aw ipd begin`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renumbered to E-01 (premise), E-02 (rewrite), E-03 (suite) with V-01 added, `Highest E allocated` raised to 03, `Depends on` rewired to E-01 -> E-02 -> E-03, and the Proposed-changes and Required-tests pointers updated. Bijection 3/3; linter `conforming`. |
| PR-605 | LOW | IN-SCOPE | F. honest documentation | sibling `staledocs` scope paths: Order 01 `3rsdbj` (six docs), Order 03 `fsme8o` (one release record); `a6xbso` also declares `work_cmd.py` | Sibling and carrier path overlap was unstated, and the one real overlap (`a6xbso`) is a staleness question rather than a contention one. Left implicit, a reader could mistake it for a runtime hazard and hold a queue over it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope-check bullet records the sibling disjointness, the `a6xbso` overlap, and explicitly that none of it is a runtime hazard because the runner isolates each item in its own worktree. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `a6xbso` rewrites the same paragraph to the opposite conclusion and is further along (PR-601). Retire this plan, add a dependency edge, or add a premise check? | ADD A PREMISE CHECK (new E-01) that stops and retires if `a6xbso` landed first. | (a) Retire this plan now as pre-superseded: rejected. `a6xbso` needs human approval and may never get it; retiring now leaves a known-false comment in the tree indefinitely, and the fix is one paragraph. (b) Add `- Item-Dependencies: executed:a6xbso`: rejected, it inverts the actual relationship. This plan does not need `a6xbso`; an edge would wedge a correct low-risk fix behind an unapproved behavior change, and if `a6xbso` executes the edge becomes pointless because the paragraph is already rewritten. (c) Fold this fix into `a6xbso`: rejected, same objection as (a) plus it grows an already-large behavior plan with an unrelated doc correction. (d) Say nothing and let the executor discover it: rejected, that is how a fresh falsehood gets written. | Read `a6xbso`'s front matter and E-03 text; compared statuses (`reviewed`/`go-pending-approval`/`medium` versus `to-review`/`low`); confirmed both name `work_cmd.py`. The runner's per-item worktree isolation is why this is a staleness question and not contention. | yes |
| D-2 | V-01's positive check passes before the edit (PR-602). Scope the grep, or replace the mechanism? | REPLACE THE MECHANISM with an `inspect.getdoc` probe over four strings. | (a) Scope the grep with a line range (`sed -n '439,468p' \| grep`): rejected, line offsets expire before execution (the repository's own `IPD-C801` convention says exactly this) and the ranges would already be wrong after the edit shifts them. (b) Keep the grep and just note the caveat: rejected, a check known to pass vacuously is not made sound by a comment. (c) Add a committed test instead: rejected, that is the source-text pin the maintainer forbade, and it would break when `a6xbso` rewrites the paragraph. | Measured that both existing `aw commit <plan>` hits lie outside the function, and measured all four replacement probes against the unedited docstring to confirm each flips. `inspect.getdoc` reads the resolved object, so it cannot drift or match elsewhere. | yes |
| D-3 | Does this plan need a test (plan's own Required-tests claim)? | NO, and record the probe-versus-pin distinction. | (a) Add a test asserting the new wording: rejected twice over. It is the production-source-text pin ruled out on 2026-09-26 and being deleted in 37 places by Set `srcguard`, AND it would go red as soon as `a6xbso` rewrites the same paragraph, which makes the general objection concrete here. (b) Assert on behavior instead: rejected as impossible; a docstring has no behavior, and `_trailers_from_args`'s behavior is deliberately unchanged by this plan. | The maintainer's 2026-09-26 ruling; Set `srcguard`'s scope; the fact that V-02's probe is an execution-time evidence check rather than a committed assertion, which is what makes it legitimate. | yes |
| D-4 | Is the absent `- Blocks-Release:` on this plan and on backlog `t5ycse` a gap? | NO; verify and move on. | (a) Add `Blocks-Release: next`: rejected, it would falsely claim the 2.0.0 release cannot ship without a docstring correction. (b) Assume it is fine without checking: rejected, sibling `3rsdbj`'s close DOES fail closed while pending, so a reader comparing the two would reasonably expect the same trap here. | AGENTS.md gates LIVE items whose `- Work-Kind:` is in the gating set (default `bug`); both item and plan are `chore`. Drove `evaluate_blocking_close(repo, <t5ycse>, "done")`: `legitimate=True`, `ok`, "no release gate to preserve", `DE-GATED`. | yes |

### Deferred and open

- (none) as unfixed findings: all five were FIXED. Nothing reached Medium-High or High Remediation
  Risk, so the Fix Bar took no deferral, and nothing reached the repository's `HIGH` escalation
  threshold, so no `- Blocking: yes` question was owed.
- The plan gained TWO resolved open questions (OQ-01 the `a6xbso` ordering, OQ-02 the test question),
  both `- Blocking: no` and both resolved from repository evidence rather than left for the human. A
  non-blocking open question does not make a plan NO-GO (maintainer ruling 2026-09-10).
- No `Reversible: no` decision was made. All four decisions are plan-text or verification-design
  choices on an unexecuted plan, each undoable by editing the plan.
- The DEFERRED work itself (supplying ids to the agent's `aw commit`) stays deferred and its carrier
  `a6xbso` is live and reviewed, so the obligation is on a real work surface rather than only in
  prose.

HONEST LIMITS, stated because they bound what this round proves. FIRST, I verified that the CURRENT
docstring text is false and that the plan's replacement premise is true; I did not and cannot verify
that the prose the executor actually writes will be accurate, because nothing tests it. That is
inherent to a docstring change and is why V-02 requires the rewritten paragraph to be PASTED for a
human to read, not merely a probe to go green. SECOND, I did not run the suite: this review changed
no code and the plan changes none (docstring only), and E-03 owns the bare run. THIRD, on the
`a6xbso` collision I read that plan's front matter and its E-03 instruction; I did not audit its
other seven scope paths for further overlap with `staledocs`, so a second collision phrased
differently could exist, though `work_cmd.py` is the only path the two share. FOURTH, my claim that
the stale phrase occurs exactly once in the package is a grep over `agent_workflows/*.py` for two
specific strings ("runbook directive", "git commit -m msg"); a paraphrase of the same false premise
elsewhere would not have matched.
