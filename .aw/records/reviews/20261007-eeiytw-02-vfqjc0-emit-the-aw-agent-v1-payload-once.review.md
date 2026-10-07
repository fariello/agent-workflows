# Review findings: plan vfqjc0

- Subject-Id: vfqjc0
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-201 (HIGH, fixed), PR-202 (MEDIUM, fixed), PR-203 (MEDIUM, fixed), PR-204 (LOW, fixed), PR-205 (MEDIUM, fixed), PR-206 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `ad1c191f4`. The plan was committed and byte-identical to the lane
input, so there was no pre-review snapshot. `aw ipd lint --phase author --agent` was `clean` before review and
`--phase review-finalize` was `clean` after revision. The plan is a `- Kind: child`. Order 01 `x7unul` is `reviewed`
(hardened earlier in this sweep), and its review corrected facts this plan relies on.

Verified: the doc contradiction (Section 5 `"complete":false`, Section 11.3 `complete: true`); the goldens; that
`CommandResult.to_agent_record` emits `applied` explicitly, normalizes paths through `data["repo_root"]` (a probe with an
absolute path rendered it repo-relative), and keeps `exit: 2` + `kind: error` with changes and diagnostics both present
(the `all` mixed shape is representable); and that `_run_noun_verb` already receives `context`. The probe and CLI
measurements are pasted in the plan's F-12..F-15.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | HIGH | IN-SCOPE | A/F data completeness | `result_types.CommandResult.to_agent_record` compact `changes` = `{"kind","path"}` only, integer above 5 | E-02 put the rename destination only in `Change.detail`, which the compact `--agent` record drops, so a default `--agent` consumer never learns the new name. A `noop` target would also be reported as a change. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now puts the destination in `target` for a single-target run (multi-target runs are documented as `--json`/`--verbose`) and excludes `noop`. E-06(c), V-02(f) and F-12 updated. |
| PR-202 | MEDIUM | UNDER-SCOPE | G Goal coverage | `cli._nv_resolve_types` / `fn is None` early returns; measured `rename nosuchtype ... --json` prints `FAIL ...` and no record | The early refusals never reach the aggregation, so "every refusal" was not covered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now emits a `cannot-run` record and suppresses `term.status` in machine mode. Argparse errors are excluded. E-06(d2), V-03(f) and F-13 updated. |
| PR-203 | MEDIUM | UNDER-SCOPE | F/UX stdout purity | `artifact_refs.filter_test_edits_interactive` (`print` plus `input(...)`) | Under a TTY, a `--json` apply whose citation rewrites touch `tests/` prompts on stdout ahead of the payload. E-04 did not name this writer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires machine mode to take the non-interactive branch. E-06(d3), V-04(e) and F-14 updated. |
| PR-204 | LOW | IN-SCOPE | G ambiguity | Doc Section 5 `"cmd":"rename plans"` vs golden `"cmd":"rename"` | The `cmd` values were left to the executor, and the two reference shapes disagree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now fixes `cmd` as the verb plus the type as typed, following the doc and the `check <type>` precedent. V-05(e) and F-15 updated. |
| PR-205 | MEDIUM | IN-SCOPE | Cross-plan consistency | Order 01 `x7unul` review F-10 | E-05 assumed `research_refs` produces the frontmatter lines. They actually come from the nested index refusal and can name other documents, and they come with a note. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 corrected: the note maps to Evidence, and the summary must not attribute the diagnostics to the renamed file. V-05(e) updated. |
| PR-206 | LOW | IN-SCOPE | Evidence drift | `87m438` is in `executed/`; 34 `MutationResult(` sites | The gate named a stale concurrent-edit plan, and E-04 repeated the stale count of "19". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both corrected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the rename destination go in the compact record? | `target` = new path for a single target; `--json`/`--verbose` for many. | Change `to_agent_record`'s compact shape to include `detail`: it is shared by every command, and the reviewed `.agent` golden omits it. | `result_types.CommandResult.to_agent_record`; golden | yes |
| D-2 | What is the `cmd` value? | Verb plus the type as typed (`rename plans`, `research mv`). | Bare verb, as in the golden: the golden is unread, the doc outranks it, and `check <type>` is precedent. | `docs/cli-output-contract.md` Section 5; `_run_check` | yes |
| D-3 | How is the test-citation prompt handled in machine mode? | Take the non-interactive branch (rewrite all edits, no prompt). | Refuse the rewrite in machine mode: that changes the mutation's effect based on output format. | `artifact_refs.filter_test_edits_interactive` non-interactive branch returns all edits | yes |
