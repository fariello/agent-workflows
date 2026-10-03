# Review: Strike the seven dangling test_run_flag_surface citations in runner_shared

- Subject-Id: 8wpjeq
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged (`dfa7eff03`), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `749efe321`:

- The file is absent and was deleted by `19313eed7`.
- `b1e304bc7` (2026-09-18) removed both `test_no_owned_flag_is_absent_from_the_spec` and `test_the_mixed_type_call_site_was_not_duplicated`.
- The re-derived spec-vs-table diff gives `['--action'] []`.
- `--on-conflict` accepts `ask`, which is outside the canonical four.

The central finding is that `git log -G test_run_flag_surface -- agent_workflows/runner_shared.py` names `972817ced` (`work(h65phz)`, plan `h65phz` executed). That commit rewrote all seven sites and spec 5.3a after this plan was authored at `af30ba67f`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Premise / executability (G) | `git show 972817ced -- agent_workflows/runner_shared.py` rewrote all 7 sites; executed `h65phz` E-05 "Correct ALL SEVEN `runner_shared.py` SITES"; `grep -c test_run_flag_surface` still `7` | The plan's central edit already landed under another plan. E-03 to E-05 described editing text that no longer exists. The E-05 bar "`grep -c` returns `0`" cannot be met, because the corrected wording names the deleted file as history. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a REVIEW UPDATE block. E-03 and E-04 now verify that the `h65phz` wording is already satisfied. E-03 to E-05, Proposed changes, Scope check, and V-03 to V-05 are re-targeted at the measured residue. The bar is now "no occurrence asserts a LIVE guard". |
| PR-002 | MEDIUM | IN-SCOPE | Correctness of prose (A) | `runner_shared.initialize_run_core` comment "`...::test_the_mixed_type_call_site_was_not_duplicated`, deleted in `19313eed`"; `git log -S "def test_the_mixed_type_call_site_was_not_duplicated"` gives `b1e304bc7` | `972817ced` introduced the exact new false attribution that F-04 warned against. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(a) re-attributes it to `b1e304bc7`, and V-05(2) demands the `git log -S` proof. |
| PR-003 | MEDIUM | IN-SCOPE | Correctness of prose (A) | the seven `972817ced` sites say "(carrier: backlog `xvp5vx`)"; `.aw/records/backlog/done/*xvp5vx*` `- Status: done` (closed by audit plan `oyh28b`) | The rewritten sites name a `done` audit item as the live coverage carrier, which is a smaller version of the same false-ownership claim. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 replaces the pointer with one non-owning phrasing at all seven sites. V-03 demands before and after greps. |
| PR-004 | MEDIUM | IN-SCOPE | Evidence accuracy (A) | `grep -rn "row.dest: False\|for row in RUN_POLICY_FLAGS" tests/` returns nothing; `_supplied` docstring "the idiom the shipped contract test uses in four places" | The plan asserted that the two `{dest: False}` idiom references were "NOT defective". Their premise, that a shipped test uses the idiom, is false at HEAD. The `repo`-passing claims also lacked a measurement step: the only `repo=` call in `tests/` calls the function directly. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05(c) now requires measuring both premises before keeping either sentence, and records the review measurement. |
| PR-005 | MEDIUM | IN-SCOPE | Validation honesty (E) | V-05(4) "parses `git show HEAD:...`"; V-05(5) "`N passed` equals ... exactly" | The AST proof compared against a symbolic `HEAD`, which is meaningless once the edit is committed. The exact pass-count bar fails when load-sensitive nodes flake (`wc5c5e`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now records `<base>` before editing, compares against `<base>`, and uses the bar "no failed node absent from the baseline". |
| PR-006 | LOW | IN-SCOPE | Concurrency notes / OQ owner | pending plans `57v89t` (`reviewed`, owns the `woxgyo` region) and `1dkj1n` (`reviewed`, declares `runner_shared.py`); OQ-01 `Owner: none` | The execution-time conditions omitted two sibling plans that touch the same file. OQ-01 had no owner. The spec-sync section still called 5.3a stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `57v89t` and `1dkj1n` to the "already landed" condition. OQ-01 is now `Owner: plan author`. Spec sync and F-08 now record the `972817ced` correction. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should this plan be retired as superseded by `h65phz`, or narrowed to the residue? | Narrow it to the measured residue | Retire as superseded (this would leave PR-002, PR-003 and PR-004 unowned) | `972817ced` diff; the residue was measured at review | yes |
| D-2 | Should the `h65phz` wording at the seven sites be re-worded to this plan's original phrasing? | No; accept it and fix only the carrier pointer | Full re-wording (churn on shipped prose, a taste-only change) | The `h65phz` text already states the obligation and that the surface is unguarded | yes |
