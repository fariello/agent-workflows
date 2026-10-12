# Review findings: plan yr3d4o

- Subject-Id: yr3d4o
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`0a56b63a6`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- Backlog `aluots` (graduated) records the maintainer's 2026-10-11 design: user as author, `AW Agent (<model>) <local+aw@domain>` as committer, `AW-Runner` trailer, honest limit. The plan matches it.
- Call sites named in F-04 exist: `commit_lock.commit_isolated` (two `["commit", "-m", message, "--", *rel]`), `ipd_lifecycle._finalize_transaction` (`["commit", "-m", commit_msg]`), `runner_shared.integrate_lane_branch` (`merge --no-ff --no-edit -m "integrate(...)"`), `runner_shared.prepare_lane_for_conflict_resolution`, `coverage_record.write`, `engine._commit_paths`, `cli._offer_commit_uninstall`.
- `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` set `_gch.RUN_ID_ENV`/`ITEM_ID6_ENV` in `child_env` (F-05).
- `runner_shared.driver_actor` / `_actor_token` already normalize model names (parentheses dropped).
- Scratch repo on git 2.43.0: `merge --no-ff` and `commit-tree` both took `GIT_COMMITTER_*` while `%an` stayed the configured user (F-06).
- Scratch repo with `commit.gpgsign=true` and a logging `gpg.program`: with `GIT_COMMITTER_*` set, gpg received `-bsau AW Agent (m) <u+aw@x.com>`; with `user.signingkey` supplied through `GIT_CONFIG_*`, gpg received `-bsau U <u@x.com>` (new F-09).
- `tests/test_git_commit_helper.py::test_trailers_on_real_commit_lifecycle` asserts a plain `offer_commit` message is byte-identical, which an unconditional `AW-Runner` trailer would break.
- `runner_shared.commit_review_lane_output` already composes `AW-Run`/`AW-Item` and `AW-Committed-By: driver` into its message.
- Spec `25kzda` names `AW-Run`/`AW-Item` as the run-ownership trailers; no spec names `AW-Runner`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Correctness / G. Coverage | `runner_shared.integrate_lane_branch` follow-up `"commit", "--no-edit", "-m", f"integrate(...)` (x2); `runner_shared.commit_review_lane_output`, `commit_review_shared_output`, `commit_spec_production_output`, `commit_spec_transition_output`, `commit_backlog_production_output`, `commit_backlog_transition_output`; `handle_review_orchestrator_readiness` `demote ... to to-review`; `worktree_lease.snapshot_lane_dirty_work` `commit-tree`; `engine.prompt_and_run_commit` | The plan's goal is "every aw-made commit", but F-04/E-03 left out these aw-made commits and merges, including two `integrate(...)` commits that the Concern itself names as unmarked. The runner finalize subprocess env was also missing, so a runner's `lifecycle(...)` commit would not carry `AW-Runner`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-08. E-03 now covers the non-runner sites, adding `engine.prompt_and_run_commit`. New E-07/V-07 cover every runner-driver merge and commit plus the finalize env. `worktree_lease.py` was added to Scope-Paths. `materialize_merge_result` is excluded, with the reason stated. |
| PR-002 | HIGH | UNDER-SCOPE | A. Correctness / B. Security | F-09 scratch-repo measurement (gpg `-bsau AW Agent (m) <u+aw@x.com>`) | Git selects the signing key from the COMMITTER ident when `user.signingkey` is unset. The agent identity would therefore make every aw commit fail for a user with `commit.gpgsign=true` and an email-keyed GPG key. That is a normal-path regression for signed-commit users. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now returns a `user.signingkey` override set to the user's own ident through `GIT_CONFIG_*` (appended to any existing count) when signing is on and no key is configured. The measured fix is cited, and E-05 (h) pins it. |
| PR-003 | MEDIUM | IN-SCOPE | D. Anti-regression | `tests/test_git_commit_helper.py::test_trailers_on_real_commit_lifecycle` (`_raw_commit_message(repo, out.commit) == message`); `runner_shared.commit_review_lane_output` trailers | An `AW-Runner` trailer added unconditionally inside `commit_isolated` would break the byte-identical plain-message contract for every non-`aw commit` caller and would invent a runner for `aw ipd set --commit`. Driver commits that already stamp `AW-Run`/`AW-Item` could also end up with duplicated keys. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now specifies one runner-resolution rule: explicit `runner=`, else a valid `AW_RUNNER`, else no trailer. Only `work_cmd` passes `aw commit`. E-02 forbids a duplicate key, and E-05 (i) pins that. |
| PR-004 | MEDIUM | IN-SCOPE | B. Privacy | plan E-06 / V-06 (live `git log -1 --format='%an <%ae> \| %cn <%ce>...'` pasted into a tracked plan) | The live proof would paste the maintainer's private email address, in two forms, into a tracked, public plan record. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The live proof is now names only, plus a pasted programmatic check that `%ce` equals `%ae` with `+aw` added. Docs use placeholder addresses. V-06 adds an `aw sanitize --agent` pass. |
| PR-005 | MEDIUM | IN-SCOPE | E. Test hermeticity | plan E-05 | The tests could inherit the developer's `user.email`, `GIT_COMMITTER_*` or `AW_*` from the environment, so the identity assertions would depend on the machine they run on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires repo-local identities and clears inherited `GIT_AUTHOR_*`/`GIT_COMMITTER_*`/`AW_*` from each test's child env. |
| PR-006 | MEDIUM | IN-SCOPE | E. Testing | plan E-04, the `work_cmd` "reads the runner from the run state" clause | No reachable mechanism was named: `work_cmd` runs inside the agent's subprocess and has no handle on the run state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now exports `AW_RUNNER`. `work_cmd._trailers_from_args` reads and validates it the same way it handles `AW_RUN_ID`, and the pop-when-absent rule is applied. |
| PR-007 | MEDIUM | IN-SCOPE | G. Live-artifact criteria | plan V-06 "the bare-suite summary line" | The full-suite evidence had no baseline comparison. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Each failing node id must now also fail at the pre-change base. A failure that passes at the base marks V-06 `failed`. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | The gate lacked the OQ status line, the scope fence, the MUST-paste honesty rule, conditional runner/executor ownership of finalize, and the no-`git mv` rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All of those were added. |
| PR-009 | LOW | IN-SCOPE | Spec sync / Evidence | spec `25kzda` (run-ownership trailers); E-02 email source | The spec-sync section said no spec governs the trailer set, but `25kzda` names `AW-Run`/`AW-Item`. E-02 also read only `git config user.email`, which ignores a `GIT_AUTHOR_EMAIL` override. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The spec-sync section now names `25kzda` and explains why it stays accurate. E-02 reads `git var GIT_AUTHOR_IDENT` in the target repo and handles an address with no `@`. OQ owners were set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a manual `aw commit` get the agent committer (OQ-02)? | Yes, keep the author's resolution | Add an `--as-human` flag now (adds surface the maintainer did not ask for) | backlog `aluots` "`aw commit` for an interactive session"; plain `git commit` stays unchanged (E-05 f) | yes |
| D-2 | How to keep signed commits working under an agent committer? | Supply `user.signingkey` = user ident through `GIT_CONFIG_*` only when signing is on and no key is set | Skip the committer override when signing is on (loses the label for signing users); document the breakage (ships a regression) | F-09 scratch-repo measurement | yes |
| D-3 | Where does `AW-Runner` come from for non-`aw commit` aw verbs? | Explicit `runner=`, else valid `AW_RUNNER`, else none | Default to `aw commit` everywhere (invents a runner and breaks byte-identical messages) | `git_commit_helper.run_item_trailers` "never synthesized" rule; `test_trailers_on_real_commit_lifecycle` | yes |
| D-4 | Split runner-driver sites into their own E-item? | Yes, new E-07/V-07 | Keep one E-03 (one item spanning six modules and two test surfaces fails the right-sizing rule) | plan right-sizing rule; rubric G conceptual density | yes |
| D-5 | Include `materialize_merge_result`'s `commit-tree`? | Exclude | Label it too (it never reaches history, so the label has no reader) | `runner_shared.materialize_merge_result` docstring: "WRITES NO REF" | yes |
