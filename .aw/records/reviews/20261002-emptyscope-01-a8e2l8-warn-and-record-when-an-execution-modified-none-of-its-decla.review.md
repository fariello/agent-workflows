# Review: Warn and record when an execution modified none of its declared Scope-Paths

- Subject-Id: a8e2l8
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Target plan was committed and unchanged (lane input identical to the pending copy), so the pre-review snapshot was skipped. `aw ipd lint --phase author` clean before edits; `--phase review-finalize` clean after.

Re-verified at lane HEAD `601c3be29`: the `compute_scope_reconciliation` auto-ack comprehension; the `if status != "partial": return status` guard in `handle_zero_work_retry`; the `in_scope_unmodified` loop and `"grandfathered": not scope_paths` key in `finalize_precheck`; the two-note fold site in `finalize`; `_disregarded_history_note`'s 5-path cap; zero audit tokens in `retire_orchestrator`; the `s2ufeo` "committed in b78501b before the begin baseline" ack; `9iiqmm`'s bare history line; `z8ex9f` approved. Reproduced F-04 end to end in a temp repo (exit 0, note present in history line and lifecycle commit).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness / reachability (A, G) | `agent_workflows/ipd_lifecycle.py` `_complete_after_commit` "Consume the begin receipt"; `agent_workflows/runner_shared.py` `turn_attempted_nothing` "the lane holds {commits_ahead} commit(s) beyond its base, which is work" | E-04 was unreachable twice over. After a self-finalize the receipt is gone, so `finalize_precheck` returns exit 1 `receipt-consumed-already-finalized` with no `scope_audit` (probed). And a self-finalized turn always made the lifecycle commit, so the conjunctive predicate always refuses (probed `commits_ahead=1` -> `attempted_nothing=False`). The widening could only record "work was done", the opposite of the intended signal, and V-04/V-05(f,g) were unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed E-04 and V-04; dropped `runner_shared.py` from Scope-Paths; added F-13 with probe evidence and a Deferred row (carrier `gmbdxe`) saying a sound runner signal must read the record, not recompute the audit; reworded title, Scope, Goal, Under-scope, OQ-01, spec-sync. |
| PR-002 | MEDIUM | IN-SCOPE | Testing (E) | plan E-05 "ASSERT SEVEN CASES", validation step 6(iii), V-05 "all seven tests" | After PR-001, cases (f)/(g) and mutation (iii) targeted removed code; the bar also pinned a test count. The 5-path cap demanded by V-02 had no test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renumbered to E-04/V-04; six behaviours (a)-(f) with (f) the volume cap; mutation (iii) now lifts the cap; V-04 maps tests to behaviours rather than a count; (e) demands concrete expected values. |
| PR-003 | LOW | UNDER-SCOPE | Anti-regression (D) | plan F-06 dirty-uncommitted shape; `finalize_precheck` `scope_paths` from receipt | V-01 did not cover the dirty-uncommitted shape the plan's own F-06 relies on, and E-01 did not note that a widened-only or out-of-scope-only execution also reads `True`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 adds shape (d); E-01 records the widened/out-of-scope edge and binds E-02's wording to it. |
| PR-004 | LOW | IN-SCOPE | Execution contract (G) | plan Scope check "stop and report"; gate lacked finalize ownership | Scope fence carried stop-style wording contrary to the 2026-09-01 ruling, and the gate did not state who runs `aw ipd finalize`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with record-as-failed-V wording and justify-at-finalize; added conditional runner/executor finalize ownership and no hand `git mv`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Repair E-04 (re-target the runner signal) or remove it? | Remove and defer to `gmbdxe` | Re-key the widening on the new history note (a new design the item has not chosen, and still blocked by the predicate refusing any committed turn); widen to compute the audit before finalize (needs host-side seam changes in both drivers) | Probes in F-13; `turn_attempted_nothing` conjunction; `gmbdxe` stays live for OQ-01 | yes |
