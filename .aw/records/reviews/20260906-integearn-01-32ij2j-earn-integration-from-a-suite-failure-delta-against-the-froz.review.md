# Review: earn integration from a suite-failure delta against the frozen base (child 32ij2j, Set integearn)

- Subject-Id: 32ij2j
- Subject-Type: ipd
- Reviewed-At: 2026-09-08
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REJECT - NEEDS REPLAN
- Readiness: no-go

## Round 1

Reviewed at HEAD `8b4e1570`. Structural preflight `aw ipd lint --phase author` conformed BEFORE semantic
review (exit 0, `outcome: clean`), and `--phase review-finalize` conformed after the revisions, now
additionally reporting `[blocking]` because two blocking questions were added.

METHOD, and it is the whole story here. This plan is almost entirely claims about what existing code
does, and it states that its feasibility was "MEASURED BEFORE AUTHORING, so the design is not
speculative". So nothing was read and accepted: the two load-bearing feasibility claims were RE-RUN.
`capture_command` was actually CALLED against a command printing `FAILED` lines, and the driver's
worktree isolation default was read at its source. Both claims failed. That is why this review took
longer than a citation check and why the verdict is REPLAN rather than a list of fixes.

WHAT THE PLAN GETS RIGHT, and it is worth keeping. The DIAGNOSIS is correct and well evidenced: the
gate really is binary on the whole suite (`passing` True only on exit 0, re-verified at `:3566`), the
earned branch really is the sole caller of both finalize and integration, the incident really happened
(the run record shows `suite_check {'passing': False, 'exit_code': 1}`, ten events, and not one
integration event), and the framing "did this lane make the suite worse" is the right question. The
`evgi9n` precedent is apt, the fail-closed instincts are correct, and the plan's own gate paragraph
warns precisely about the failure mode its implementation would have shipped, which is a good gate
paragraph attached to a design that cannot honor it.

THE FIRST BLOCKER: THERE IS NO OUTPUT TO PARSE, SO THE DELTA WOULD ALWAYS BE EMPTY AND EVERY LANE WOULD
EARN INTEGRATION. E-01's entire premise is reading `FAILED <nodeid>` lines out of captured stdout, and
F-8 justified it as "the substrate is already captured" because `max_output_bytes=512_000`. Measured:
`run_suite_check` reads `tool_event.get("stdout_excerpt")` and `run_evidence.build_tool_event` NEVER
WRITES THAT KEY. It writes `stdout_sha256`, `stderr_sha256`, `stdout_len`, `stderr_len`, `truncated`
and `max_bytes`; `max_output_bytes` truncates the bytes BEFORE HASHING them and persists no text.
Reproduced by calling `capture_command` on a command printing two `FAILED` lines: the returned event has
no `stdout_excerpt`, so the value bound is `""`. Two corroborations that this is live and not a reading
error: `grep -rn stdout_excerpt agent_workflows/` returns exactly ONE hit, the reader; and the real
incident's record has `summary: ""` even though its suite printed a summary line, so the EXISTING
`_SUITE_SUMMARY_RE` is already dead code for the same reason. The consequence is not a missing feature
but an inversion: a `FAILED` parser over an always-empty string returns `()`, and `() ⊆ anything` holds,
so E-03's subset test would EARN integration for every lane including one that broke everything. The
plan's own gate says "a bug that makes the delta LOOK empty would auto-integrate unverified work into
main. If you find yourself defaulting an unknown to no failures, stop." That is exactly what the code
would have done.

WHY THE TEST SUITE COULD NOT HAVE CAUGHT IT, which matters for the replacement plan. Every existing
test of this path patches `run_evidence.capture_command` and hands back a FABRICATED `stdout_excerpt`
key (`tests/test_novalnomerge_integration.py:262`, `:288`, `:312`). `test_zero_exit_passes_and_records_the_summary_line`
passes today while the production read is dead. A new test written in the same style would pass over the
new bug identically, so the replacement work needs at least one test driving the real
`capture_command`.

THE SECOND BLOCKER: THE DELTA WOULD NOT MEASURE THE LANE. `run_suite_check(repo, ...)` runs in the
PRIMARY checkout by explicit design (`dh0uno`, and the docstring is emphatic that callers MUST pass the
primary repo). Its own HONEST LIMIT paragraph already concedes it "proves THE TREE is green, not that
the lane's uncommitted state is". But `isolate_worktree` defaults TRUE, so the agent commits only on
`aw/lane/<id6>` and at gate time the primary tree does NOT contain the work under judgement. Under the
ABSOLUTE check that mismatch was merely conservative, which is the plan's complaint. A SUBSET check
inverts it into a FALSE PASS: a lane that broke every test it touched leaves the primary failing set
identical to base, so the subset holds and integration is earned. The plan cites the incident as proof
its design works, but that agent measured the lane IN THE LANE (`5563 passed`) against a clean base
clone; this plan keeps the lane side in the tree where the lane's code is absent. So the incident
validates a DIFFERENT design than the one authored.

THE SEAM THE PLAN DID NOT LOOK AT, and probably the right home. `integrate_lane_branch` already calls
`orchestrate_isolation.execute_merge_and_revalidate_gate`, whose stated job is to REVALIDATE the
combined HEAD because "per-lane green never implies integrated green". Its `full_validation_runner` is
today a hardcoded `return True` (`make_integration_validation_runner`). So the repository already has
the gate that guards main with the code actually merged, and it is inert. A no-new-failures comparison
belongs there far more naturally than in a pre-merge check over a tree that lacks the lane.

THREE SMALLER DEFECTS. The sibling is cited by the WRONG ID three times: `7m0aro` is the BACKLOG item
integearn-02 graduated from, not a plan (`aw find plans 7m0aro` -> no match; the sibling is `xtklpd`,
carrying `- From-Backlog: 7m0aro`), so an executor told to consult it as a plan finds nothing. EVERY
line citation has drifted by roughly 49 lines in `oc_runipd.py`, verified symbol by symbol; the
substance was correct at the new coordinates, and the plan's own re-locate-by-symbol instruction is why
this is LOW rather than higher. And the cited `mm6wuz` receipt no longer exists, consumed by the very
recovery finalize the plan describes, so it cannot serve as F-9's evidence even though F-9's mechanism
holds (re-verified that the receipt is consumed only at successful finalize and that the gate runs
before finalize, so a live receipt IS available at gate time).

WHY REPLAN AND NOT REVISIONS-APPLIED. Both blockers are prerequisites of the plan's own E-items rather
than gaps inside them: one requires deciding how suite output becomes reachable at all (with a
schema-versioned evidence record and a D92 leak surface in one of the options), the other requires
deciding WHERE the trust signal comes from (an architecture choice, possibly relocating the work to a
different module entirely). Neither is repairable by an in-place edit to a checklist item, and both are
maintainer decisions. The diagnosis is worth preserving verbatim, so the plan was hardened rather than
rewritten: the false premises are corrected in place and marked, the V-items now demand the evidence
that would have caught each blocker, and the gate names the minimum shape of a sound replacement.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-016 | BLOCKER | IN-SCOPE | A. correctness; B. security/leaks; E. testing; G. executability | called `capture_command` on a command printing two `FAILED` lines: no `stdout_excerpt` in the returned event, `stdout_len=62`; `run_evidence.build_tool_event:277-332`; `oc_runipd.py:3615` (sole reader); incident record `summary: ""`; `tests/test_novalnomerge_integration.py:262`,`:288`,`:312` fabricate the key | **THERE IS NO OUTPUT TO PARSE, SO THE PLAN'S CENTRAL MECHANISM WOULD EARN INTEGRATION FOR EVERY LANE UNCONDITIONALLY.** F-8 claimed the substrate was already captured because `max_output_bytes=512_000`; measured, that truncates bytes before HASHING and stores no text, and the key `run_suite_check` reads is written nowhere in the package. So `stdout` is always `""`, the existing summary regex is already dead (corroborated by the incident's empty `summary`), and a `FAILED` parser over it returns `()` for a red suite. `() ⊆ anything`, so E-03's subset test earns integration always: precisely the inversion this plan's own gate warns about. The existing tests cannot catch it because they stub `capture_command` and fabricate the key | C:Medium; U:Low; S:Medium; F:High; Overall:Medium-High | OPEN | Escalated as OQ-04 with `- Blocking: yes` and `- Finding: PR-016`, owner maintainer, four costed options with (a) recommended (capture in `run_suite_check` itself, persist no raw text). F-8 WITHDRAWN and marked false; new F-12; two conventions bullets added (the substrate, and the stub blindness). E-01 rewritten to require making output reachable FIRST and forbidding a self-authorized ledger change; E-01/E-03/E-05 now require `passing=False` with an empty set to refuse; V-01 requires a NON-EMPTY set against a genuinely red suite obtained WITHOUT stubbing. NOT FIXED: one option changes a schema-versioned evidence record and puts pytest output (absolute machine paths, D92) into a durable artifact, which is not an executor's call |
| PR-017 | BLOCKER | IN-SCOPE | A. correctness; C. architecture | `oc_runipd.py:3593-3594` (docstring concedes it proves the TREE not the lane), `:5985` (`isolate_worktree` default True), `:6456` (call passes `repo`), `:2077-2092` (`make_integration_validation_runner` returns True) | **THE LANE SIDE OF THE DELTA DOES NOT CONTAIN THE LANE, TURNING A CONSERVATIVE CHECK INTO A FALSE PASS.** The suite runs in the primary checkout by design while the agent commits only on `aw/lane/<id6>`, so the measured tree lacks the work being judged. Absolute-green tolerated that; a subset test does not: a lane that broke everything leaves the primary failing set equal to base and EARNS integration. The incident the plan cites measured the lane IN the lane, so it validates a different design than the one authored. Separately, the repository ALREADY has a combined-result revalidation gate (`execute_merge_and_revalidate_gate`) whose validation runner is an inert `return True`, which is the more natural home | C:High; U:Low; S:Medium; F:High; Overall:High | OPEN | Escalated as OQ-05 with `- Blocking: yes` and `- Finding: PR-017`, owner maintainer, four options with (b) recommended (implement the inert combined-gate runner) and (a) as the smaller step. New F-13; two conventions bullets. E-02/E-03 now state the lane side is unsettled and forbid implementing the subset test until OQ-05 answers; E-04 gains honest limit (d); E-06 and V-06 require the refusal case run with `isolate_worktree` at its DEFAULT with the break committed lane-only, since the false pass exists only in the shipped configuration; V-03 FAILS if the lane side is still the primary checkout. NOT FIXED: every option relocates the trust signal, which is an architecture decision |
| PR-018 | HIGH | IN-SCOPE | G. executability; evidence accuracy | `aw find plans 7m0aro` -> no matching plans; `grep -rln '^- Id: 7m0aro' .aw/records/plans/` -> empty; `backlog/graduated/20260906-integearn-01-7m0aro-stranded-run-reports-completed.backlog.md`; integearn-02 front matter `- Id: xtklpd`, `- From-Backlog: 7m0aro` | **THE SIBLING PLAN IS CITED BY A BACKLOG ID, THREE TIMES.** The plan names `7m0aro` as "sibling child (integearn-02)" in its Concern, Deferred and Scope-check sections. No plan carries that id; it is the backlog item the sibling graduated FROM, and the sibling plan is `xtklpd`. An executor following the reference finds nothing, and the deliberate split between "this child produces the reason" and "that child persists it" becomes unresolvable | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both LIVE references corrected to `xtklpd` with a parenthetical noting `7m0aro` is the backlog item; the third occurrence is inside a `## Workflow history` record and was deliberately left verbatim, since history is a record of what was said. New F-14 |
| PR-019 | MEDIUM | IN-SCOPE | E. testing | bare `python3 -m pytest` at `8b4e1570`: `1 failed, 5651 passed, 3 skipped, 2 xfailed`; plan records `1 failed, 5612 passed` at `15445857`; same failing node id | The recorded before-baseline is stale by 39 passes. The plan's delta criterion (after-minus-before failure set empty) is exactly right and is what makes this survivable, but an executor comparing against the RECORDED total would see a spurious mismatch | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both measurements recorded with instruction to trust neither total; new F-16; V-06 requires re-measuring its own before-baseline |
| PR-020 | LOW | IN-SCOPE | Evidence accuracy | `grep -n` per symbol at `8b4e1570`: `SuiteCheckResult` `:3558-3572` (plan `:3509-3524`), `passing` `:3566` (`:3517`), `_SUITE_SUMMARY_RE` `:3553` (`:3504`), `SUITE_CHECK_TIMEOUT_SECONDS` `:3545` (`:3496`), `max_output_bytes` `:3612` (`:3563`), oc call site `:6456` (`:6397`), earned branch `:6493` (`:6435`), agy call site `:3724` (`:3711`), agy binding `:311-313` (`:306`) | Every line citation has drifted by roughly 49 lines in `oc_runipd.py`. The SUBSTANCE was verified correct at each new coordinate (shared predicate, agy re-export binding, two call sites, sole caller of finalize and integration), and the plan already instructs re-location by symbol, so this is presentational | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Citations updated at the load-bearing sites (Concern, E-01, E-04, E-06, F-1) and F-15 records the full measured drift table; the re-locate-by-symbol instruction retained and strengthened as a conventions bullet |
| PR-021 | LOW | IN-SCOPE | Evidence accuracy | `ls .aw/state/ipd-lifecycle/` -> 30 receipts, no `mm6wuz`; `ipd_lifecycle.py:2652` (receipt unlinked on successful finalize); gate at `oc_runipd.py:6456` runs before finalize at `:6493` | F-9 cites `.aw/state/ipd-lifecycle/mm6wuz.receipt.json` as evidence that `base_head` is readable, but that receipt is GONE, consumed by the very recovery finalize the plan describes. The MECHANISM is sound (re-verified that receipts are consumed only at successful finalize and that the suite gate runs before finalize, so a live receipt is available at gate time), but the cited artifact cannot be inspected by a reader | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-9 rewritten with the correction and the ordering proof; E-02 re-verified and told to cite a LIVE receipt when validating, never `mm6wuz` |
| PR-022 | LOW | UNDER-SCOPE | C. operability; honest documentation | bare suite 165s at review; incident `suite_check` `elapsed_seconds: 78.0`; E-04 said only "a baseline suite run is not free" | The cost is asserted qualitatively while the measured numbers were available. Adding a baseline run roughly DOUBLES gate wall time per distinct base, before any lane-side run OQ-05 may add, and a plan that understates this is one an operator eventually switches off, which E-04 itself predicts | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires the measured numbers stated plainly (165s bare, 78s observed gate run, roughly doubling per distinct base) |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Is this plan repairable with bounded in-place edits, or does it need REPLAN? | REPLAN, while HARDENING the plan in place rather than rewriting it, so the sound diagnosis and evidence survive for the replacement | Revisions-applied with added E-items, rejected because both blockers are PREREQUISITES of the existing items rather than gaps inside them: one needs a decision about a schema-versioned evidence record, the other about which module owns the trust signal. Silent rewrite of the approach on my own authority, rejected because plan-review may not invent an architecture decision. Leave the plan as-is and report, rejected because an executor could pick it up and ship an always-earn gate | measured `capture_command` returning no `stdout_excerpt`; `isolate_worktree` default True with the gate reading the primary tree; the plan's own gate paragraph forbidding exactly the resulting behavior | yes |
| D-2 | Where should a no-new-failures comparison live, given the pre-merge gate measures the wrong tree? | RECOMMEND the existing combined-result gate (`execute_merge_and_revalidate_gate`, whose `full_validation_runner` is an inert `return True`), with an isolated lane-branch checkout as the smaller alternative, and ESCALATE rather than decide | Decide it myself and rewrite E-02/E-03 accordingly, rejected as an architecture choice that relocates the trust signal and may pull another module into scope. Run the lane's suite in the lane worktree, rejected on the plan's own measured `dh0uno` grounds (a lane suite is permanently red). Keep the primary-tree measurement and abandon the subset change, offered as option (c) since it preserves a useful diagnostic without the false-pass risk | `oc_runipd.py:2077-2092` (runner returns True); `orchestrate_isolation.execute_merge_and_revalidate_gate` docstring ("per-lane green never implies integrated green"); `run_suite_check` docstring honest limit; ESCALATED as OQ-05 with `- Finding: PR-017`, and maintainer told 2026-09-08 in this review's final report | no |
| D-3 | How should suite output become reachable, given nothing writes `stdout_excerpt`? | RECOMMEND capturing it inside `run_suite_check` and keeping only the parsed node-id set in memory; ESCALATE the choice | Add a persisted excerpt field to `build_tool_event`, rejected as a reviewer's call because it mutates a schema-versioned provenance record and writes pytest output (absolute machine paths, D92) into a durable artifact. Fix only the dead read so the summary works and drop set-level parsing, offered as option (d) since it is independently valuable. Leave it undecided and unflagged, rejected because E-01 would otherwise be executed against an always-empty string | `build_tool_event:277-332` (hashes and lengths only); single-hit grep for the reader; incident `summary: ""`; ESCALATED as OQ-04 with `- Finding: PR-016`, and maintainer told 2026-09-08 | no |
| D-4 | The third `7m0aro` reference sits inside `## Workflow history`. Correct it too? | NO. Correct the two LIVE references and leave the history record verbatim | Correct all three, rejected because a workflow-history line records what a past actor actually asserted, and editing it would falsify the record rather than fix a pointer. Leave all three, rejected because the Deferred and Scope-check references are live instructions an executor would follow | repository convention that `## Workflow history` is append-only narrative; the two live references are the ones an executor acts on | yes |
| D-5 | Is the plan's core DIAGNOSIS also wrong, or only its prescription? | The diagnosis is CORRECT and was preserved verbatim; only the prescription fails | Discard the whole plan as unsound, rejected because every diagnostic claim re-verified: the binary gate, the sole-caller branch, the incident's zero integration events, the `evgi9n` precedent, and the one-red-test threshold (still one at review, same node id). Treat the failed feasibility claims as invalidating the problem statement too, rejected because the problem is real and independently measurable | re-verified `passing` at `:3566`; incident `state.json` `suite_check {'passing': False, 'exit_code': 1}` and 10 events with no integration event; bare suite `1 failed` at review | yes |
