# Review findings: plan fnbtta

- Subject-Id: fnbtta
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2f22724d1` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean (13 `IPD-C801`
advisories, all the report-subject exception the plan documents) before semantic review, and
`--phase review-finalize` was clean after revision.

Re-verified (read-only probes, no production edit):
- Parse-and-resolve of every `oc_runipd.py:`/`agy_runipd.py:` offset in `agent_workflows/runner_shared.py`: 15 offsets
  across 8 sites, of which 5 are past EOF (`oc_runipd.py` 6993, 7031, 6645, 6647, 6649; host now 5494 lines,
  `agy_runipd.py` 4200). The plan said 6; its own enumeration lists 5.
- `runner_shared.EXECUTION_SUCCESS_STATES == {'executed'}`; both hosts re-export the same object (`is` -> True).
  `git log -1 -S'EXECUTION_SUCCESS_STATES = {"executed"}'` -> `6b94a4d9d 2026-09-25 statusvocab: ...`, diff line
  `-EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}` confirmed.
- `edge_satisfied` source: 176 lines, 1 `EXECUTION_SUCCESS_STATES` mention (the deleted-shortcut comment), 0
  `success_states`.
- `EXECUTE_REPORTING_SUCCESS_STATES == frozenset({'executed', 'approved'})`.
- `outcome_precedence_disposition(None, {"disposition": "executed"})` and `(..."substantially-complete")` both return
  `fail-gate`; `TERMINAL_STATUS_ALIASES["substantially-complete"] == "fail-gate"`.
- `recover_interrupted_step` does not exist anywhere in `agent_workflows/` or `tests/`; the quoted docstring belongs to
  `runner_shared.reconcile_interrupted`.
- `git show 394238996^:agent_workflows/oc_runipd.py`: the `runnable["status"] = "dependency-blocked"` `else` arm is
  in `run_queue`'s `if runnable.get("action") == "orchestrate":` block; `_set_children_all_executed` is called there.
- `agy_runipd.py`'s `# noqa: F401 - a DELIBERATE re-export` is the `_read_id` line; the `as <same-name>` re-export
  note preceding the `runner_shared` seam (which imports `spec_impacts_for_queue as spec_impacts_for_queue`) is the
  referent the spec-edit block means.
- `tests/test_rununify_run_queue.py` is absent (deleted in `19313eed`).
- AST-equality probe (docstrings blanked, `ast.dump` compared against `git show HEAD:` blob) returns True on the
  unedited tree, demonstrating the V-03 no-code-change proof shape.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness of the plan's evidence | plan E-04/F-04/V-04 named `recover_interrupted_step`; `agent_workflows/runner_shared.py:31284` `def reconcile_interrupted` | The function E-04 edits does not exist; the quoted docstring is `reconcile_interrupted`'s. An executor would hit E-02-style "stop and reconcile" or edit by guess. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renamed every occurrence to `reconcile_interrupted`. |
| PR-002 | HIGH | IN-SCOPE | D. Domain invariant (status vocabulary) | `runner_shared.outcome_precedence_disposition` returns `"fail-gate"`; `TERMINAL_STATUS_ALIASES["substantially-complete"]`; docstring "a step recovered to `substantially-complete`" | E-04 declared the retry half of the docstring "true" and told the executor to leave it, but since `6b94a4d9d` the recovered status is `fail-gate`, and the SELF-CLAIM DOWNGRADE bullet plus `outcome_precedence_disposition` rung 2 describe a return value the code no longer produces. The plan would have shipped a corrected sentence beside the same false token. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now also corrects the recovered-status token in both docstrings, records the "dependents may proceed" effect as intended-then-removed, preserves `fduoj4` OQ-03 and the `ydbhfd` historical measurement; V-04 demands the `outcome_precedence_disposition` call output. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | `runner_shared.EXECUTE_REPORTING_SUCCESS_STATES` note ("for which `substantially-complete` legitimately counts", MEASURED exit-code paragraph) | E-03 (ii) claimed the note's argument "does not depend on the dead member"; its measured illustration does. Leaving the follow-on clause would keep a false membership claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 (ii) now covers the follow-on clause, restates the distinction on the current sets (differ by `approved`), keeps the measurement labelled pre-`6b94a4d9d`, and leaves the deleted-test citation to `3tov52`. V-03 updated. |
| PR-004 | MEDIUM | IN-SCOPE | A. Evidence count | plan Concern, F-01, E-01, E-05, OQ-01, V-01 said "6 past EOF"; F-01's own list has 5 | Census miscount; E-01 demanded the executor "reproduce" a figure the tree cannot produce, inviting a false stop. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected to 5 (and 10 non-EOF) everywhere; E-01 records the review-HEAD line counts as expected drift. |
| PR-005 | MEDIUM | IN-SCOPE | G. Executability (referents) | E-05/F-07; `agy_runipd.py` `_read_id` `# noqa: F401` line vs the `as <same-name>` re-export note; `394238996^` `oc_runipd.run_queue` | Two F-07 referents were wrong: the agy re-export anchor named the `_read_id` noqa line (unrelated, and `3tov52` territory), and the historical `else` was said to live in `_set_children_all_executed` rather than `run_queue`'s orchestrate block. The two sites were also attributed to `enforce_spec_edit_ack_gate`/`announce_run_order`, which they only follow. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 and F-07 corrected; V-05 now demands the historical construct and the quoted-note search hit. |
| PR-006 | MEDIUM | IN-SCOPE | E. Verification strength | V-03 "diff confirming the definition line is unchanged" | Nothing proved that ONLY comments/docstrings changed, which the plan's DO-NOT-CHANGE-BEHAVIOR contract requires. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-03 demands a one-off AST-equality measurement (docstrings blanked) against the pre-edit blob; demonstrated returning True at review. Not a committed test, so P16 is respected. |
| PR-007 | LOW | IN-SCOPE | Project rule (shared checkout) | E-06 "or on a stashed-clean tree"; `AGENTS.md` shared-checkout section | Suggested `git stash` for the baseline, which `AGENTS.md` forbids in a shared checkout. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline must be taken before edits; stash/reset explicitly ruled out. |
| PR-008 | LOW | IN-SCOPE | G. Traceability | Concern/Scope/E-05 cited F-02/F-04/F-06 for content living in F-03/F-04/F-05/F-06 | Stale finding cross-references. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cross-references corrected; carrier `7jl2bf` named. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should correcting the stale `substantially-complete` recovered-status token (PR-002) be in this plan's scope? | Yes, inside E-04, same file, comment-only | Defer to a new carrier; leave as-is | Same docstring E-04 already edits; plan OQ-02's own reasoning (do not ship a precise pointer beside a false statement); `outcome_precedence_disposition` returns `"fail-gate"` | yes |
| D-2 | How should V-03 prove no executable code changed without a code-pinning test? | One-off `ast.dump` equality with docstrings blanked, pasted as evidence | `git diff` grep for `#` lines (cannot see docstrings); committed test (violates P16) | Demonstrated at review: probe returns True on HEAD vs working tree | yes |
| D-3 | Which agy note is the "re-export form documented" referent? | The `as <same-name>` RE-EXPORT note preceding the `runner_shared` seam importing `spec_impacts_for_queue` | The `_read_id` `# noqa: F401` line (plan's original) | `agent_workflows/agy_runipd.py` quoted note; the `_read_id` line documents an unrelated alias | yes |
