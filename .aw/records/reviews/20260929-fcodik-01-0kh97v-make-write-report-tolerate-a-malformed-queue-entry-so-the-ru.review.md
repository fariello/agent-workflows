# Review findings: plan 0kh97v

- Subject-Id: 0kh97v
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-201 (HIGH, fixed), PR-202 (HIGH, fixed), PR-203 (MEDIUM, fixed), PR-204 (MEDIUM, fixed), PR-205 (MEDIUM, fixed), PR-206 (MEDIUM, fixed), PR-207 (LOW, fixed)

## Round 1

Reviewed at HEAD `374aa8fa` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` after revision.

THE PLAN IS UNUSUALLY WELL MEASURED AND ITS CENTRAL CORRECTION OF THE BACKLOG ITEM IS RIGHT. I re-ran
every probe rather than reading its numbers. F-01 reproduces exactly on both hosts (`TypeError: string
indices must be integers, not 'str'`, frame `write_report`, expression
`counts[item["status"]] = counts.get(item["status"], 0) + 1`). F-02's seven-site census is correct, and so
is its sharpest sub-claim: probing the four section helpers individually gives `AttributeError` from
`render_transient_dependency_waits` (`item.get(TRANSIENT_DEPENDENCY_WAIT_KEY)`),
`format_verifier_evidence_section` (`pos = item.get("position", 1)`),
`format_generated_next_actions_section` (`item.get("generated_next_actions")`) and
`lane_containment.format_preserved_lanes` (`item.get("preserved_worktree")`), while
`render_zero_work_notes` alone returns `[]`, exactly as F-04 says and for the reason it says. F-03's
`save_state` claim verified (its last statement is `write_report(run_dir, state)`, and the injected-real
call raises). F-06 verified in the SHIPPED report format: a spliced placeholder row round-trips through
`run_viewer.load_run_summary` to `counts == {'malformed-entry': 1}`, `status == 'malformed-entry'`,
`position == 1`, precisely as claimed. F-07, F-08, F-09 and F-11 all verified. I also went further than the
plan and PROTOTYPED the whole fix, which confirmed both halves of its central promise: the malformed state
renders a complete report, and a rich well-formed state renders BYTE-IDENTICALLY (recorded as new F-14).

So this is not a plan that needed rescuing. What review found is a set of instructions that are
individually unexecutable or factually wrong in ways an executor would hit at the keyboard, plus a stale
baseline and an unrecorded coordination with a sibling plan that has since been reviewed.

THE TWO THAT WOULD HAVE STOPPED AN EXECUTOR. PR-201: E-03 instructs the executor to fill the placeholder
row's `#` column "from the loop's own enumeration index". There is no such index. The row loop is
`for item in state["queue"]:` and `enumerate` appears nowhere in `write_report`'s body (measured: three
queue loops, zero `enumerate`). The instruction as written cannot be followed, and the two obvious
improvisations are both wrong: `item["position"]` is the unreadable field that motivated the row, and a
hand-maintained counter is a second source of truth for a number the loop already implies. The fix is a
loop-header conversion to `enumerate(state["queue"], 1)`, which is the ONE structural change this plan
makes to a line well-formed runs execute, so it now says so explicitly and records that my prototype
measured it byte-neutral. PR-202: F-05 asserts "THE FIX ADDS NO IMPORT" and E-03 repeats "which the module
already imports at top level". True of `runner_shared`; FALSE of `lane_containment`, which E-05 edits and
which imports only `Callable, Sequence` from `collections.abc` and contains zero occurrences of the string
`Mapping`. Following the plan literally produces a `NameError` at the first call of the guarded function.
Both the finding and E-05 now carry the import obligation.

THE SIBLING LANDSCAPE MOVED UNDER THE PLAN (PR-205, PR-206). F-10 states `s438xd` is `- Status: open`. It
is `graduated`, with `- Graduated-To: s438xd` and a 2026-09-29 history line naming run
`run-20260929T021205Z-3914774: 165lkb`; that plan `165lkb` is itself already `- Status: reviewed` with
`- Readiness: go-pending-approval`. Because F-10 believed only one sibling had graduated, it never checked
`165lkb` for fence overlap, which is now the check that matters. I measured it: `165lkb` declares
`render_stream.py` plus `tests/test_run_summary_malformed_entry.py`, `cup9r7` declares
`run_selection_policy.py` plus its test, and neither names `runner_shared.py`, `lane_containment.py`, or
this plan's test file. So the conclusion survives intact and the correction strengthens it. Worse than the
status error, though, is what the missed sibling contains: `165lkb` introduces a malformed-entry status
token of the SAME SPELLING as this plan's, and its own F-12 already names `0kh97v` and explains why the two
cannot be one constant. The coordination was recorded on one side only, so a future reader of
`runner_shared` finds an undocumented duplicate string literal and will reasonably try to deduplicate it.
E-02 now carries the reciprocal note and Deferred carries the sharing question with its reasoning.

While checking that, I found the sibling's stated reason OVERSTATED and recorded it rather than repeating
it: `165lkb` F-12 says `runner_shared` imports `render_stream` "at module level, so the reverse import
would cycle". The import is LAZY, inside a function body, and importing both modules in either order
succeeds today (verified in a subprocess). The conclusion still holds on the weaker sufficient ground that
`render_stream`'s header declares a deliberate first-party-import allowlist. Correcting `165lkb` is not
this plan's business; not propagating its error is.

TWO SMALLER ONES AND A NUANCE. PR-204: E-04 justifies its skip by saying all three helpers "already
document" returning `[]` so an unaffected report is byte-identical. Two do; `format_generated_next_actions_section`
does not carry that sentence, so the item now adds it there rather than citing a precedent that helper
lacks. PR-203: the validation instructed comparing the suite against F-12's `3246 passed`. Re-measured at
review: `3278 passed, 2 skipped` — the tree gained 32 tests between authoring and review, which is normal
in a shared checkout and is exactly the live-count-as-acceptance-bar antipattern. The bar is now a baseline
captured in the executing lane. PR-207: the gate instructed a move to `executed/` and carried no scope
fence; both replaced with the tooled `aw ipd finalize` path, the `AW-LIFECYCLE-ROLE-001` runner-ownership
condition, the `fcodik` gate-handoff ordering, and a scope declaration. I also recorded a nuance the plan
had slightly wrong in spirit (new F-15): `save_state` writes `state.json` BEFORE it raises, so durable
state survives and the run stays resumable. That makes the defect report-loss, not state-loss, which is
what the plan should claim and now does.

WHAT I DELIBERATELY DID NOT FLAG. The plan's six E-items for what is ultimately seven guards could read as
over-structured, and the crash-walk demonstrations (paste the test still failing with the frame MOVED,
twice) could read as ceremony. They are neither. The backlog item's own fix direction would have produced
exactly the guard-the-first-site outcome that leaves the deliverable false, and the two intermediate reds
are the only evidence distinguishing this plan from that one. Keeping them is right. I also left OQ-01 and
OQ-02 resolved as authored: both are correctly resolved from repository evidence, OQ-01's count-and-render
answer is backed by `c4gd2h` R22 (verified: "A stopped item is never recorded as executed, complete, or
successful") and by the measured availability of the bucket, and OQ-02's fence answer follows from all
three callers reaching one body.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | G (executability) | plan E-03 ("keep the `#` column filled from the loop's own enumeration index"); `runner_shared.write_report` row loop reads `for item in state["queue"]:`; `enumerate` occurs zero times in the function body | The instruction names an enumeration index that does not exist, so it cannot be followed. The two plausible improvisations are both wrong: `item["position"]` is the unreadable field, and a hand counter duplicates a number the loop implies | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires converting the loop header to `enumerate(state["queue"], 1)`, names it as the one structural edit to a well-formed-run line, records the prototype's byte-neutrality result, and forbids both improvisations |
| PR-202 | HIGH | IN-SCOPE | A (correctness) | plan F-05 ("THE FIX ADDS NO IMPORT") and E-03 ("which the module already imports at top level"); `grep -c Mapping agent_workflows/lane_containment.py` returns 0; its import reads `from collections.abc import Callable, Sequence` | True for `runner_shared`, false for `lane_containment`, which E-05 edits. Following the plan literally yields `NameError` at the first call of the guarded function | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 corrected to state the asymmetry with its measurement; E-05 now requires adding `Mapping` to that module's `collections.abc` import first; E-03's phrasing scoped to `runner_shared` |
| PR-203 | MEDIUM | IN-SCOPE | E (testing); live-artifact-count convention | plan F-12 (`3246 passed, 2 skipped`) versus review's bare run at HEAD `374aa8fa`: `3278 passed, 2 skipped, 3 warnings in 144.34s` | The validation instructed comparing against a count captured at authoring, already stale by 32 tests, so a clean run would read as a regression. This is the live-artifact-count-as-acceptance-bar antipattern | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 rewritten with both measurements; Required tests and V-06 now require a baseline captured in the executing lane, with the bar stated as no newly failing test rather than a reproduced total |
| PR-204 | MEDIUM | IN-SCOPE | D (invariants) | plan E-04 ("all three already document that they return `[]` ... byte-identical"); the phrase is present in `render_transient_dependency_waits` and `format_verifier_evidence_section` docstrings and ABSENT from `format_generated_next_actions_section` | The justification cites a precedent one of the three helpers does not carry | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now says two of three carry it, and requires ADDING the byte-identity sentence to the third rather than asserting it already had one |
| PR-205 | MEDIUM | IN-SCOPE | G (executability); concurrency | plan F-10 ("`s438xd` is `open`"); `aw find backlog s438xd` reports `graduated` with `- Graduated-To: s438xd` and a 2026-09-29 history line naming `165lkb`; `165lkb` is `- Status: reviewed`, `- Readiness: go-pending-approval` | F-10's status fact is wrong, and because it assumed one graduated sibling it never checked the second sibling PLAN for fence overlap, which is now the load-bearing check | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-10 rewritten with both corrections and the measured overlap for BOTH sibling plans (`165lkb`: `render_stream.py` + its test; `cup9r7`: `run_selection_policy.py` + its test; neither names this plan's three paths) |
| PR-206 | MEDIUM | UNDER-SCOPE | C (architecture) | `165lkb` E-02 adds a render-facing malformed-entry token to `render_stream`; its F-12 names `0kh97v` and explains the forced duplication; this plan's E-02 carried no reciprocal note | Two plans independently introduce identical string literals with the coordination documented on one side only, so a future reader finds an unexplained duplicate and will try to merge them | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 (including that the sibling's cycle rationale is overstated: the import is lazy and both orders import fine, though its conclusion survives on the allowlist); E-02 now requires the reciprocal note; added a Deferred row for the sharing question with `Carrier-Declined` and its reasoning |
| PR-207 | LOW | UNDER-SCOPE | G (execution contract) | plan gate ("move this plan to `.aw/records/plans/executed/`"); no scope fence present; `ipd_lifecycle` `AW-LIFECYCLE-ROLE-001` | The gate instructed a hand move to `executed/`, which the lifecycle contract forbids, and declared no scope surface for a two-module edit inside a 37000-line file | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now requires `aw ipd finalize ... --apply` with runner ownership and the `AW-LIFECYCLE-ROLE-001` path, states the `fcodik` gate-handoff ordering, and carries a scope declaration naming the intended surface in both modules |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the placeholder row's `#` column be filled, given the loop has no index? | Convert the row loop to `enumerate(state["queue"], 1)` and read the index only inside the new branch | Reuse `item["position"]` with a fallback; maintain a hand counter; leave the `#` cell as `?` | `position` is the unreadable field that motivates the row, so it cannot supply the number; a hand counter is a second source of truth for what the loop already implies. `?` was rejected because F-06's measured round-trip shows the parser falls back to the step index anyway, so the honest number is available at no cost. The conversion was prototyped and the well-formed report stayed byte-identical | yes |
| D-2 | Should this plan attempt to share ONE token constant with sibling plan `165lkb` rather than duplicate the spelling? | No: document the duplication on both sides, share nothing | Import the constant in one direction; hoist it to a third module | `165lkb` is already `reviewed` awaiting approval, so editing its fence collides with in-flight work, which is the same prohibition this plan's gate states for `cup9r7`. The import direction is also constrained: `render_stream`'s header declares a first-party-import allowlist and `runner_shared` reaches it only lazily, so a module-level back-import would create the cycle that lazy import avoids. A third home is worth deciding only when a third consumer appears | yes |
| D-3 | Should the review correct sibling plan `165lkb`'s overstated cycle rationale (it says the import is module-level; it is lazy)? | No: record the correction in THIS plan's F-13 and leave `165lkb` untouched | Edit `165lkb`'s F-12 | `165lkb` is a reviewed plan awaiting approval and is not in this review's ledger; editing it would modify an artifact this run was not asked to review. Recording the measurement here prevents this plan from propagating the error, which is the part within scope. Its conclusion is correct on other grounds, so nothing unsafe follows from leaving it | yes |
| D-4 | What should the suite acceptance bar be, given the authored baseline is stale? | A baseline captured in the executing lane; bar is no newly failing test plus the new file's additions | Update F-12's number to 3278; drop the suite comparison | Updating the number just moves the staleness, since more work will land before execution; dropping the comparison loses the regression signal. Re-deriving in-lane is what the repository's own live-artifact convention requires for a count that drifts | yes |
| D-5 | Is E-03's `enumerate` conversion a violation of the plan's own "change no other executable line" prohibition? | No, but it must be declared | Treat it as out of scope and find an index-free approach | The conversion touches a line well-formed runs execute, so the prohibition genuinely bears on it; but the index is read only inside the non-mapping branch, and a prototype rendering a rich well-formed state (dependency blocks plus preserved lanes exercised) produced a byte-identical report. Declaring it beats hiding it, since a reviewer of the diff will see the header change and must know it was intended | yes |
