# Review: Give backlog items an enumerated transition table

- Subject-Id: cc2m29
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged at lane HEAD `9e2b5a359`, so the pre-review snapshot was skipped. `aw ipd lint --phase author` and `--phase review-finalize` both came back clean.

I re-located each of these by symbol:
- `status_set.validate_transition_allowed`: the specs branch and the `->blocked` gate-pair message.
- `backlog.run_set`: `item.status = new_status` is assigned without reading the prior status.
- `attention_contract.SPEC_TRANSITIONS` and `transition_allowed`.
- `lifecycle_dirs.LIFECYCLE_SUBDIRS["backlog"]`.
- The runner's `--status open` rollback and its `handoff incomplete` remedies.
- `tests/test_backlog_gate_follows_status.py::test_route_d_done_to_open_*`.
- The sibling plans `tm8k2n` and `miimjb`, both of which declare `executed:cc2m29`.

I then measured which edges the suite actually drives. An in-process `-p` recorder under the gitignored `tmp/` logged every backlog edge on both spellings during one bare run. That run finished `4 failed, 4637 passed, 2 skipped`; the 4 failures are pre-existing and unrelated, and 3 of them also fail when run alone.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Plan executability (G), domain invariants (D) | plan E-03/F-08, which name only the `done` and `graduated` rows; the review recorder's edge table | The plan's deliverable is a refusal, but it never states which edges it refuses. The `open`, `blocked` and `parked` rows are left to the executor, so a cautious executor could ship an empty, vacuous gate and an aggressive one could break something the suite uses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Derived the candidate table from the plan's own rule ("refuse only what nothing uses") using the measured suite edges plus F-05, F-06 and F-08. Refused set: `parked->done`, `parked->graduated`, `done->blocked`, `done->parked`. E-02 re-derives this at execution time. The executor must STOP if the refused set comes out empty. Added F-16; V-03 now prints the complement. |
| PR-002 | MEDIUM | IN-SCOPE | Live-artifact criteria (G), shared-checkout safety | E-08 and V-08 "delta accounted for as exactly the tests E-07 adds"; V-07 "stashing the production change" | These count-based bars assume a green suite, but this suite has 4 pre-existing failures that vary between runs. Separately, `git stash` is unsafe in a shared checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Same-session FAILED-name comparison; a worktree, or reverting only your own patch, instead of stash. |
| PR-003 | MEDIUM | UNDER-SCOPE | Correctness (A) | E-05 versus E-07 (g)/(h), which are asserted "for BOTH spellings"; `backlog.parse_item` returns the token verbatim | E-05 had no case-fold and no requirement to run before the dry-run, so the flag spelling could not satisfy E-07 cases (g) and (h). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added both to E-05 and to V-05. |
| PR-004 | LOW | IN-SCOPE | Sequencing (G) | pending `vhiqo6` (setdisp-05) Scope-Paths `backlog.py, status_set.py`: "thin adapter delegating" | If `vhiqo6` lands first, E-05's second call site becomes redundant. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 is now conditional: if `run_set` already delegates, prove that rather than adding a second call site. |
| PR-005 | MEDIUM | UNDER-SCOPE | Execution contract (G) | plan gate | The gate was missing `aw ipd begin`, an id6 commit, a scope fence naming the dependent siblings (so the predicate name is not renamed), and the `t1gbwg` close command. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all four. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which edges should the backlog table refuse? | `parked->done`, `parked->graduated`, `done->blocked`, `done->parked`, re-derived at execution | Leave the rows to the executor (underdetermined); refuse more edges (breaks suite-driven or runner edges) | plan rule "refuse only what nothing uses"; review recorder; F-05/F-06/F-08 | yes |
| D-2 | Keep F-04's `chore` classification? | Yes. No user-perceptible wrong answer was measured. | Reclassify as `bug` with a release gate | AGENTS.md perceptibility test | yes |
