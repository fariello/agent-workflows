# Review: wire both host dispatch paths and correct the documented claim (child pgq326, Set orchretire)

- Subject-Id: pgq326
- Subject-Type: ipd
- Reviewed-At: 2026-09-06
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `b759984b`. Structural preflight `aw ipd lint --phase author` conformed before semantic
review and `--phase review-finalize` conformed after the revisions.

TWO DISCLOSURES, both bearing on what this review is worth.

FIRST, I authored this plan in the same session, so this is a SELF-REVIEW, not an independent one.

SECOND, and more specifically: I edited this plan DURING the orchestrator's review (adding E-07/V-07
under the cross-plan rule), so part of what I reviewed here is my own prior review's output. I treated
E-07 on the same footing as the authored content rather than assuming it was already vetted. It survived,
but that is a judgement I made about my own work and a genuinely independent reviewer would be worth more
on exactly that item.

This is the Set's LAST child and the one that makes everything reachable from a real run, so the review
concentrated on two things: whether an executor following the plan literally would land in the right
code, and whether RECONSIDER as specified actually restores dispatchability. Both turned up problems.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | MEDIUM | IN-SCOPE | Evidence accuracy; G. executability | `oc_runipd.py:5829-5833` vs `:6936-6940`; `:5847` vs `:6954`; `kxkc04` lines 40, 52 | Two line citations were inherited stale from the backlog item and point ~1100 lines from the code they name. The skip-and-reconsider PRECEDENT that E-01's whole design rests on is at `:6936-6940` (the selection `for` loop that `break`s and leaves other items `queued`); `:5829-5833` is worktree-isolation prose. The drain path is the `if runnable is None:` branch at `:6954`; `:5847` is `assert_child_tool_identity` commentary. An executor following them reads the wrong function while believing the plan verified it, which is worse than no citation | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both corrected with a description of what is actually at the new lines. Added F-7 and a gate instruction to re-locate a symbol by name when a cited line does not contain what the plan claims |
| PR-302 | MEDIUM | IN-SCOPE | Evidence accuracy | `engine.py:1207`, `:1058`, `:1502`, `:1519` | E-05 placed the false AGENTS.md claim in `agents_managed_sections` "near `engine.py:1146`". It is a string literal at `:1207` inside `agents_pointer_prose` (`:1058`); `:1146` is unrelated spec-status prose and `agents_managed_sections` (`:1502`) only wraps the prose into the `aw:pointer` section. The executor would have opened the wrong function to edit the one sentence this requirement exists to fix | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now names `:1207` inside `agents_pointer_prose`, explains the wrapper's role, and cites `merge_aw_block` (`:1587`). V-05 requires the diff to show the literal edit. Added F-8 |
| PR-303 | MEDIUM | UNDER-SCOPE | A. Correctness | `oc_runipd.py:6937`, `:4039`, `:6916` | RECONSIDER was specified as "write NO status and let the next iteration re-test". Necessary, not sufficient. Selection admits an item only when `dependency_status` reports satisfied (`:6937`), and `cascade_dependency_blocked` (`:4039`) propagates `dependency-blocked` over reverse edges to a fixed point at the TOP of every iteration (`:6916`), so it can relabel the very item E-01 deliberately left `queued`, through a path E-01 never touches. "Not terminal" and "reachable again" are different properties and only the second one fixes the bug | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires verifying RE-SELECTION and checking the cascade interaction; its expected outcome demands demonstrable re-selection. V-01 requires the orchestrator's status at the top of the following iteration. Added F-6 |
| PR-304 | MEDIUM | UNDER-SCOPE | D. Anti-regression; honesty | `engine.py:1218-1219`; `AGENTS.md:43` | The AGENTS.md correction had no requirement binding each new assertion to a test, in a Set whose entire subject is a documented claim no test ever exercised. Worse, the paragraph's closing instruction lists "orchestrator finalization" among things an agent must NOT raise because "those are solved"; left as-is it would forbid reporting the cases the new mechanism deliberately REFUSES (unauthored child rows, a refusing transition), which are exactly the cases a human should hear about | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 must keep the surrounding paragraph coherent and not forbid reporting deliberate refusals. V-05 requires mapping EACH new assertion to the E-06 test that demonstrates it, with unbacked assertions deleted rather than shipped. Added to F-8 |
| PR-305 | LOW | IN-SCOPE | Evidence accuracy; E. testing | `grep -c "def test_"` per module | The cited 95-vs-21 suite asymmetry is stale: re-measured 148 + 7 oc versus 39 + 4 agy (155 vs 43). The asymmetry and the conclusion stand, the number does not. Separately, `tests/test_oc_runipd_cli.py` and `tests/test_agy_runipd_shim.py` are outside `Scope-Paths`, so an executor with a case belonging there faces an unflagged fence decision | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Conventions note re-measured with the current counts and the conclusion preserved; both out-of-fence modules named in the note and the gate, with the correct instruction (make the edit and justify it, do not force the test into the wrong module) |

No finding was DEFERRED, left OPEN, or marked REPLAN, so no escalation to a `- Blocking: yes` question
was required.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-07 was added by my own earlier review pass. Re-review it, or treat it as already vetted? | Re-reviewed it on the same footing as authored content, and disclosed the conflict in this record. | Treating it as vetted, REJECTED: a reviewer's own edit is not peer-reviewed by virtue of having been made during a review, and the whole Set exists because an unexamined claim survived. | `plan-review.md:32` (verify claims from repository evidence); this record's disclosure | yes |
| D-2 | PR-303: is the cascade interaction a finding here, or speculative until the code is written? | A finding, fixed by requiring verification rather than by prescribing an implementation. | Leaving it to the executor to notice, REJECTED because the plan's stated mechanism ("write no status") reads as complete and an executor has no prompt to look further; being wrong yields an orchestrator silently never retired, the exact bug. Prescribing a specific fix, REJECTED as premature: the right response depends on what the code does, so the plan demands evidence, not a design. | `oc_runipd.py:4039`/`:6916`/`:6937`; `plan-review.md:449-454` | yes |
| D-3 | Is PR-301 MEDIUM or HIGH? | MEDIUM. | HIGH, REJECTED: the citations are wrong but the SYMBOLS are named in prose ("the inner selection pass", "the drain path, when `runnable is None`"), so a careful executor recovers; nothing is silently incorrect in the design. Not LOW, because the whole justification for RECONSIDER rests on the precedent at the miscited line. | `plan-review.md:504-509` | yes |
| D-4 | Readiness value. | `go-pending-approval`. | `go`, REJECTED (`Status: reviewed`, no human sign-off). `no-go`, REJECTED (no open question, no unfixed BLOCKER/HIGH; OQ-01 is resolved-in-approach with the empirical answer assigned to E-03 and explicitly non-blocking because either branch proceeds). | `plan-review.md:531-546`; plan OQ-01 | yes |

No `Reversible: no` decision was taken.

### Verified claims

- The terminal-status defect is exactly as described. `dependency-blocked` is in `TERMINAL_STATES`
  (`oc_runipd.py:254-272`, the literal set includes it at `:261`) and the selection filters admit only
  `queued` (`:4071` inside the cascade, `:6919` at the loop head), so the orchestrator is excluded
  permanently. F-1 holds.
- The single `else` and both reasons hold: `:6993` opens the branch, `:7015` writes the terminal status,
  and the reason ternary distinguishes `not-all-children-executed` from `finalize-refused` in the EVENT
  only. F-2 holds.
- The agy asymmetry holds, verified by attribute presence and object identity rather than grep:
  `action_for`, `finalize_orchestrator`, `_set_children_all_executed` are all absent from `agy_runipd`
  (`hasattr` False for each), `agy.determine_action` is defined at `:1510-1514` and called at `:1783`,
  and `agy.determine_action('approved')` is `'execute'` where `oc.action_for('orchestrator','approved')`
  is `'orchestrate'`. F-3 holds.
- E-07's premise holds (my own earlier addition, re-checked): the token `orchestrate` appears nowhere in
  `agy_runipd.py` outside the `orchestrate_isolation` import, `execute_item` derives only
  `is_review = action == "review"` (`:2973`), and the queue loop calls `execute_item` unconditionally
  (`:4138`). So agy would agent-execute an orchestrator even with a shared decider.
- The AGENTS.md claim exists and is generated: the sentence is at `AGENTS.md:42` and its source literal at
  `engine.py:1207`. F-4 holds; only its location was wrong (PR-302).
- The drain path does label the remainder with per-edge reasons outside a wind-down
  (`dependency_status_detailed`, `:6965-6970`) and deliberately does NOT relabel under a wind-down
  (spec R22, no fabricated disposition), which is why E-03's two-branch shape is right and why I added
  the wind-down case to it.
- `action_for` returns `orchestrate` for `reviewed` as well as `approved`, and the queue admits
  `to-review`/`draft`/`approved`/`auto-approved` as `queued` (`:2922-2924`), consistent with what the
  orchestrator plan now records.
- The 0-vs-28 measurement, the 15 distinct orchestrators, the 103 run records, and the
  `99760832`/`801dd28a` ordering were verified in this Set's earlier reviews and hold.

### Right-sizing and conceptual density

Seven E-items across two groups, spanning both runners, the generator, and three test modules. This is
the densest child in the Set, and I considered recommending a split (task group 1 as one plan, host
symmetry plus documentation as another). I did not, for a stated reason: E-01, E-02 and E-07 must land
together or the dispatch is half-wired, E-04 without E-07 is the defect PR-001 caught, and E-05's text
must describe what E-06 demonstrates. The items are cohesive by dependency, not merely adjacent. The
`Scope-Paths` breadth is inherent to "wire both hosts" and is the reason the Set sequenced this child
last and alone.

### Not verified, and stated as such

I did not implement anything, run the suite, or exercise either runner. Every claim above is a read of a
named `path:line` at `b759984b` or the output of a read-only call. The plan's V-items must produce the
runtime evidence, and V-01/V-06/V-07 deliberately require sabotages and re-selection traces because a
passing test proves nothing about a boundary it never probes.
