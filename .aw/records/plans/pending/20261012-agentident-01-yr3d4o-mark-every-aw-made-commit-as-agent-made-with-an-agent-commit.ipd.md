# IPD: Mark every aw-made commit as agent-made with an agent committer identity and runner trailers

- Date: 2026-10-12
- Kind: child
- Concern: You cannot tell from `git log` which commits an agent made and which you made. Every commit is authored and committed as the user. The only agent marker is an `AW-Run:` trailer, and most aw-made commits lack it: measured 2026-10-11, 2,509 of 9,520 commits on `main` carry it, and only 127 of the last 300. Unmarked aw-made commits include runner merges (`integrate(...)`), plan finalize commits (`lifecycle(...)`), some runner work commits (e.g. `0dd8c3a3e`), and everything an interactive agent session commits through `aw commit`.
- Scope: Every commit and merge that aw makes keeps the user as AUTHOR and records `AW Agent (<model>) <local+aw@domain>` as COMMITTER, where the address is the user's own email with `+aw` added before the `@`. Each such commit carries `AW-Runner: <runner>` (`aw oc run`, `aw agy run` or `aw commit`) when the runner is known, plus `AW-Run` and `AW-Item` when they are known; a commit from another aw verb (e.g. `aw ipd set --commit`) outside a run gets the committer label and no invented runner. A commit the user makes with plain `git commit` is unchanged. No new accounts, keys, GitHub settings or required configuration.
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/commit_lock.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/work_cmd.py, agent_workflows/coverage_record.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/worktree_lease.py, tests/test_agent_commit_identity.py, docs/commit-identity.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: aluots
- Set: agentident
- Order: 1
- Highest E allocated: 07
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: yr3d4o
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 fixed.
- 2026-10-12 to-review (aw set): authored from backlog aluots on the maintainer's instruction (plans preferred to backlog items); design decided by the maintainer 2026-10-11

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every aw-made commit identifiable as agent work at a glance, with `git log --format='%an | %cn'` and the trailers, while the user stays the author, nobody has to create an account, and commits the user makes by hand are untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: one definition of the agent identity

- [ ] E-01 MEASURE FIRST, then build. In a throwaway repo (with `user.name`/`user.email` set locally), make one commit through each path listed in E-03 that can be driven directly on unmodified code (at minimum `aw commit`, `ipd_lifecycle.finalize`, a lane integration `--no-ff` merge, and `engine._commit_paths`; name any site not driven and why) and record each commit's `%an <%ae> | %cn <%ce>` and trailers (`git log -1 --format='%(trailers)'`). Expected: author and committer are both the repo's user identity everywhere; `AW-Run` appears only where a run id was available. This is the before-state that E-05's tests must show changed.
  - Depends on: none
  - Expected outcome: a pasted table of path -> author, committer, trailers on unmodified code.
  - Execution state: pending

- [ ] E-02 Add ONE helper in `git_commit_helper` that returns the git environment and trailer set for an aw-made commit, and nothing else computes them:
  - COMMITTER NAME: `AW Agent (<model>)`. `<model>` is the run's resolved model (`options["model"]`, the value `runner_shared.driver_actor` already renders) or, outside a run, the `AW_AGENT_MODEL` environment variable when set; otherwise `unknown`. Never guessed.
  - COMMITTER EMAIL: the user's email from `git config user.email` with `+aw` inserted before the `@` (`a@b.com` -> `a+aw@b.com`). If the address already has a `+` tag, append `-aw` to the tag rather than adding a second `+`. Read the email with `git var GIT_AUTHOR_IDENT` (or `git config user.email`) in the TARGET repo, so a `GIT_AUTHOR_EMAIL` env override and a repo-local `user.email` are both honored. If there is no user email at all, or it has no `@`, set no committer override and let git behave exactly as it does today (the commit would fail or succeed the same way it would have).
  - SIGNING: when the repo has `commit.gpgsign=true` and no `user.signingkey`, git selects the signing key from the COMMITTER ident (measured at review: with `GIT_COMMITTER_*` set, `gpg -bsau` received `AW Agent (m) <u+aw@x.com>`), so the agent identity would break signed commits. When `commit.gpgsign` is true and `user.signingkey` is unset, the helper also returns a git config override (`GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_<n>`/`GIT_CONFIG_VALUE_<n>`, APPENDED to any count already in the env) setting `user.signingkey` to the user's own `Name <email>` ident (measured: gpg then received `U <u@x.com>`). An already-configured `user.signingkey` is left alone.
  - NO DOUBLE TRAILER: the trailer composer must not add an `AW-Runner`, `AW-Run` or `AW-Item` key the message already carries (e.g. `commit_review_lane_output` already stamps `AW-Run`/`AW-Item` and `AW-Committed-By: driver`).
  - AUTHOR: never set. Git's normal identity applies, so the user stays the author.
  - TRAILERS: `AW-Runner: <runner>`, plus `AW-Run` and `AW-Item` from `run_item_trailers` when present. The runner value is `aw oc run`, `aw agy run` or `aw commit`; an unknown caller writes no `AW-Runner` rather than a made-up one.
  - Model names are sanitized for use in an identity: strip newlines, `<`, `>` and parentheses, and collapse whitespace, so `Gemini 3.8 Flash (High)` becomes `Gemini 3.8 Flash High`.
  - Depends on: E-01
  - Expected outcome: a pure function, unit-tested in E-05, that maps (user email, model, runner, run id, item id, signing config) to the env overrides and trailer lines.
  - Execution state: pending

### Task group 2: use it on every aw commit path

- [ ] E-03 Apply the helper on every NON-RUNNER path where aw itself creates a commit (the runner driver's merges and commits are E-07). Each must pass the env overrides to its `git commit` / `git merge` subprocess and append the trailers to its message (merges take trailers in the `-m` message):
  - `commit_lock.commit_isolated` (both `git commit` calls), which `git_commit_helper.offer_commit` and `aw commit` use;
  - `ipd_lifecycle._finalize_transaction` (the `lifecycle(...)` finalize commit);
  - `coverage_record.write`, `engine._commit_paths`, `engine.prompt_and_run_commit` (the installer's `agent-workflows: sync via installer` commit), and `cli._offer_commit_uninstall`.
  The runner-driver merge and commit sites are E-07, not this item. `runner_shared.materialize_merge_result`'s `commit-tree` is EXCLUDED on purpose: it makes an ephemeral, unreferenced commit used only to build a revalidation worktree, never a commit that reaches history. Calls to `offer_commit` from other modules (`status_set`, `plans_archive`, `research_archive`, `cli`) get the agent COMMITTER through `commit_lock.commit_isolated` with no edit to those modules. RUNNER RESOLUTION (one rule, applied inside the E-02 helper): an explicit `runner=` argument wins; else a valid `AW_RUNNER` env value; else NO `AW-Runner` trailer. `offer_commit` and `commit_isolated` gain an optional `runner: Optional[str] = None`; only `work_cmd` (`aw commit`) passes `aw commit`, and `runner_shared` passes its host. So a manual `aw ipd set --commit` gets the committer label but no runner trailer, rather than a made-up one.
  If execution finds an aw commit or merge path not listed here, add it to this list and Scope-Paths, and record it in Findings, before changing code.
  The shared runner `git_commit_helper._git` / `runner_shared._run_git` stay generic; the env is passed by the commit and merge call sites, so reads, `merge --ff-only` and every non-commit git call are untouched. A fast-forward creates no commit and needs nothing.
  - Depends on: E-02
  - Expected outcome: every listed call site creates commits whose committer is the agent identity and whose message carries the trailers exactly once; no other git call changes; no existing test needs editing: with no explicit runner and no `AW_RUNNER` in the env, the message is byte-identical to today (e.g. `tests/test_git_commit_helper.py::test_trailers_on_real_commit_lifecycle` asserts a plain `offer_commit` message is unchanged), and the committer env does not touch the message. A pre-existing test failing because of this change is a defect in the change, not in the test.
  - Execution state: pending

- [ ] E-07 Apply the E-02 helper on the RUNNER DRIVER's own merge and commit sites, with runner `aw oc run` or `aw agy run` taken from the caller's `host_label` (both hosts pass their `HostLabels.command`), passing the env overrides to each `_run_git` call and the trailers in each message:
  - `runner_shared.integrate_lane_branch`: the `git merge --no-ff ... -m "integrate(...)"` AND both of its follow-up `git commit --no-edit -m "integrate(...)..."` calls (the records-only re-derivation commit and the kept-both-sides workflow-history commit);
  - `runner_shared.prepare_lane_for_conflict_resolution`'s `merge --no-ff --no-commit` + `commit` pair;
  - the driver's own runner commits in `runner_shared`: `commit_review_lane_output`, `commit_review_shared_output`, `commit_spec_production_output`, `commit_spec_transition_output`, `commit_backlog_production_output`, `commit_backlog_transition_output`, and the `demote <id6> to to-review` commit in `handle_review_orchestrator_readiness`;
  - `worktree_lease.snapshot_lane_dirty_work` (a plumbing `commit-tree`, which also honors `GIT_COMMITTER_*`; verified at review);
  - the driver's FINALIZE subprocess (the `"finalize"` argv built in `runner_shared` with `env = dict(env_builder())`): add the E-02 committer env plus `AW_RUNNER` and `AW_AGENT_MODEL` to that `env`, so the `lifecycle(...)` commit a runner finalize makes is labelled and carries `AW-Runner`.
  `runner_shared._run_git` stays generic; only these call sites pass the env. Signatures of the host wrappers (`oc_runipd.integrate_lane_branch`, `agy_runipd.integrate_lane_branch`) stay unchanged (`tests/test_runner_shared.py` asserts their kwonly lists are empty), so the runner value and model are derived inside `runner_shared` from `host_label` and the run state the shared function already receives or can read.
  - Depends on: E-02
  - Expected outcome: every runner-driver merge and commit listed here has the agent committer, the user author, and `AW-Runner` (plus `AW-Run`/`AW-Item` when known) exactly once; `merge --ff-only`, `merge --abort` and `materialize_merge_result` are unchanged.
  - Execution state: pending

- [ ] E-04 Make the AGENT'S OWN commits inside a run carry the identity too. Both runners already build the agent child environment in one place and export `AW_RUN_ID` / `AW_ITEM_ID6` there (`oc_runipd.run_opencode` and `agy_runipd.run_agy_turn`, beside `git_commit_helper.RUN_ID_ENV`). Also export `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL` and `AW_AGENT_MODEL` from the E-02 helper, with runner `aw oc run` or `aw agy run`. Any `git commit` the agent runs in its lane then gets the agent committer automatically. Also export an `AW_RUNNER` variable carrying the runner value; `work_cmd._trailers_from_args`, which already reads `AW_RUN_ID` for trailers, reads `AW_RUNNER` the same way (validated against the three known values; an unknown value is dropped with a stderr warning, matching its `AW_RUN_ID` handling) and otherwise uses `aw commit`. The same pop-when-absent rule the runners apply to `AW_RUN_ID` applies to these variables, so an outer run's identity never leaks into a nested driver.
  - Depends on: E-02
  - Expected outcome: a commit made by a scripted agent inside a runner turn has the agent committer, the user author, and `AW-Run`, `AW-Item`, `AW-Runner`.
  - Execution state: pending

### Task group 3: pin and document

- [ ] E-05 Add `tests/test_agent_commit_identity.py`, driving real git in `tmp_path` repos and asserting on `git log` output, never on source text. Cases: (a) the helper's mapping table: plain address, already-tagged address, missing email, model sanitizing, unknown model, unknown runner; (b) `aw commit` through `cli.main` yields author = repo user, committer = `AW Agent (<model>) <user+aw@...>`, trailer `AW-Runner: aw commit`; (c) a finalize through `ipd_lifecycle.finalize` yields the agent committer, and with `AW_RUNNER=aw oc run` set (as the E-07 finalize env sets it) also `AW-Runner: aw oc run`, while without it carries no `AW-Runner` (the runner-resolution rule in E-03); (d) a lane integration merge through `runner_shared.integrate_lane_branch` (non-ff case: main advanced past the lane base) yields the identity and trailers on the merge commit; (e) the oc and agy agent child envs contain the committer variables and `AW_AGENT_MODEL`, and a scripted agent's `git commit` in the lane gets them; (f) a plain `git commit` in the same repo, outside aw, keeps author = committer = user, proving nothing global changed; (g) with no `user.email` configured, aw sets no committer override; (h) with `commit.gpgsign=true`, no `user.signingkey`, and `gpg.program` pointed at a scratch script that logs its arguments, the key requested is the USER's ident, not the agent's; (i) a driver commit whose message already carries `AW-Run`/`AW-Item` (`runner_shared.commit_review_lane_output`) has each key exactly once. Cases (b)-(d) must FAIL on the base commit; show it. Each test sets its own `user.name`/`user.email` with `git config --local` in its `tmp_path` repo and clears inherited `GIT_AUTHOR_*`/`GIT_COMMITTER_*`/`AW_*` from its child env, so it never depends on the developer's identity.
  - Depends on: E-03, E-04, E-07
  - Expected outcome: the module passes, and (b)-(d) are shown failing before the change.
  - Execution state: pending

- [ ] E-06 Document and prove. Write `docs/commit-identity.md` (short: what the committer and trailers mean, how to filter agent commits with `git log --committer='AW Agent'` and `git log --format='%h %an | %cn %(trailers:key=AW-Runner,valueonly)'`, and the honest limit). Add a CHANGELOG entry. Both are user-facing: no em or en dashes. Run the existing `tests/test_commit_run_trailers_env.py`, `tests/test_finalize_trailer_attribution.py` and `tests/test_git_commit_helper.py`, then the bare suite. Then make one real `aw commit` in this repository and paste its `git log -1 --format='%an | %cn%n%(trailers)'` (names only: the plan record is tracked and public, so do not paste the email addresses; instead state that `%ce` equals `%ae` with `+aw` inserted, checked by `python3 -c` comparing the two values). The docs use only placeholder addresses such as `you@example.com`.
  - Depends on: E-05
  - Expected outcome: the three existing modules and the bare suite pass, and the live commit shows the user as author and the agent as committer with the trailers.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite: run BARE as `python3 -m pytest`; narrowed runs use `-o addopts=""`. Tests drive real surfaces and assert on outputs, never read source (`AGENTS.md`, GUIDING_PRINCIPLES P16).
- Commit through `aw commit <plan> -- <paths>`; never push.
- Trailer values must come from live run state, never be synthesized (`git_commit_helper.run_item_trailers` docstring). The same rule applies to the model and runner here: unknown stays unknown.
- One git subprocess wrapper exists (`git_commit_helper._git`); `ipd_lifecycle._git` and `commit_lock._git` delegate to it. Keep it generic.
- User-facing prose (CHANGELOG, docs) carries no em or en dashes.
- Cite code by SYMBOL; line numbers drift.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Author and committer are the user on every commit. | `git log --format='%an | %cn'` on `main`. |
| F-02 | Agent markers cover a minority of aw-made commits. | 2,509 of 9,520 commits on `main` carry `AW-Run`; 127 of the last 300 (measured 2026-10-11). |
| F-03 | Unmarked aw-made commit types. | Recent `integrate(...)`, `lifecycle(...)` and some `work(...)` commits (e.g. `0dd8c3a3e`) carry no trailer; every interactive-session `aw commit` has none because no run id exists. |
| F-04 | aw-made commit and merge call sites. | `commit_lock.commit_isolated`, `ipd_lifecycle._finalize_transaction`, `runner_shared` lane integration and `prepare_lane_for_conflict_resolution`, `coverage_record.write`, `engine._commit_paths`, `cli._offer_commit_uninstall`. |
| F-05 | The runners already build the agent's env in one place. | `oc_runipd` and `agy_runipd` set `git_commit_helper.RUN_ID_ENV` / `ITEM_ID6_ENV` in the agent child env. |
| F-06 | Git reads the committer from the environment for commits and merges. | `GIT_COMMITTER_NAME` / `GIT_COMMITTER_EMAIL` (git-commit(1), git-merge(1) "ENVIRONMENT"). Verified at review on git 2.43.0: a `merge --no-ff` and a `commit-tree` both took the env committer while the author stayed the configured user. |
| F-07 | No existing doc describes the trailers. | `grep -rln "AW-Run" docs/` returns nothing. |
| F-08 | Added at review: aw-made commits not in the authored F-04 list. | `runner_shared.integrate_lane_branch` follow-up `commit --no-edit -m "integrate(...)"` calls; `runner_shared.commit_review_lane_output` and its five sibling `commit_*_output` functions; `handle_review_orchestrator_readiness` `demote ... to to-review` commit; `worktree_lease.snapshot_lane_dirty_work` `commit-tree`; `engine.prompt_and_run_commit`. |
| F-09 | Added at review: git picks the signing key from the committer ident when `user.signingkey` is unset. | Scratch repo with `commit.gpgsign=true` and a logging `gpg.program`: with `GIT_COMMITTER_*` set the key requested was `AW Agent (m) <u+aw@x.com>`; with `user.signingkey` supplied through `GIT_CONFIG_*` it was `U <u@x.com>`. |

## Proposed changes (ordered, validatable)

1. One helper for the identity and trailers (E-02).
2. Every aw commit path uses it (E-03), and every runner-driver merge and commit (E-07).
3. The runners hand it to the agent's own commits (E-04).
4. Tests, doc, CHANGELOG, live proof (E-05, E-06).

## Deferred / out of scope (with reason)

- Separate GitHub accounts, deploy keys, credential hiding, branch protection, PR requirements: considered with the maintainer on 2026-10-11 and declined; the toolkit must stay zero-setup.
- Rewriting existing history to add the identity: not requested. The maintainer asked for this change only (2026-10-11), after weighing a history rewrite for the 320 `Test` commits as low value.
- Preventing an agent from running raw `git commit` with the user's identity: not enforceable without a separate OS user; the label is accepted as sufficient.

## Scope check

- Over-scope: none. Each declared path is a call site in F-04/F-05, the helper's home, the new test module, the new doc, or the CHANGELOG.
- Under-scope: the review found five call-site groups missing from the authored list (F-08) and the signing interaction (F-09); both are now in E-02/E-03 and Scope-Paths. If execution finds another aw commit path, add it to E-03 and to Scope-Paths before changing code, and record it in Findings.

## Required tests / validation

- `tests/test_agent_commit_identity.py` (new), with (b)-(d) shown failing on the base commit.
- `tests/test_commit_run_trailers_env.py`, `tests/test_finalize_trailer_attribution.py`, `tests/test_git_commit_helper.py` passing.
- Bare suite `python3 -m pytest`.
- One live `aw commit` in this repository, with its author, committer and trailers pasted.

## Spec / documentation sync

No spec governs commit identity or the `AW-Runner` trailer, so none is amended. Spec `25kzda` names `AW-Run`/`AW-Item` as the run-ownership trailers and says the checker finds run-owned commits by them; this plan adds a key beside them and changes neither, so that spec stays accurate. The trailers are documented for the first time in `docs/commit-identity.md`, and the change is announced in `CHANGELOG.md`.

## Open questions

### OQ-01: How does an interactive agent session say which model it is?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved on repository evidence: there is no reliable way to detect the model of an interactive session from inside aw (this session exposes only `OPENCODE`, `OPENCODE_PID` and `AGENT` in its environment, none naming a model). So outside a run the model comes from `AW_AGENT_MODEL` when the session sets it, and is otherwise `unknown` (E-02). Never guessing follows the existing rule for trailer values (`git_commit_helper.run_item_trailers`). Reversible: a later change could teach host integrations to set `AW_AGENT_MODEL`.

### OQ-02: Should `aw commit` used by a human by hand also get the agent committer?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved by the author as an INFERENCE, not a maintainer ruling: the maintainer said (2026-10-11) that almost all work is agent-driven and that corrections are made by telling an agent, so `aw commit` is in practice the agent's commit path. A human committing by hand uses plain `git commit`, which E-05 (f) proves is unchanged. Reversible and cheap to change: if the maintainer wants a human-run `aw commit` to keep the user as committer, the helper needs a way to tell the two apart (e.g. an explicit `--as-human` flag), and that is the review's call.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the before-state table (path -> author, committer, trailers) from the throwaway repo on unmodified code, naming any E-03 site not driven and why.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the helper's unit-test output for every mapping row in E-05 (a), plus the signing-override row (h) and the no-double-trailer row (i).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git log -1 --format='%an <%ae> | %cn <%ce>%n%(trailers)'` (fixture identities only) for a commit from each E-03 call site, produced by E-05 (b)-(d) or by driving the remaining sites directly; name each site and the test or command that drove it; any site not driven is a `failed` result, not a skip.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the oc and agy agent child env keys showing the committer variables and `AW_AGENT_MODEL`, and the scripted lane commit's author, committer and trailers (E-05 (e)).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_agent_commit_identity.py -v` passing, and cases (b)-(d) failing against a worktree at the base commit (the new test file copied into it).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the three existing modules passing; the bare-suite summary line with its FAILED node-id list, where each failing id is also shown failing at the pre-change base commit (any failure that passes at the base is caused by this change and makes the result `failed`); the doc and CHANGELOG diffs with a dash check finding no em or en dash; `aw sanitize --agent` on the changed files reporting no new finding; and the live `aw commit`'s names-only `git log -1` output plus the email-relationship check.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git log -1 --format='%an <%ae> | %cn <%ce>%n%(trailers)'` (fixture identities only) for the commit produced by each E-07 site, naming the test or command that drove it (E-05 (d) covers the non-ff integrate merge; drive `commit_review_lane_output`, a `commit_*_output` sibling, `prepare_lane_for_conflict_resolution` and `snapshot_lane_dirty_work` directly in `tmp_path` repos). Show `AW-Runner` appears once and `AW-Run`/`AW-Item` appear at most once on the `commit_review_lane_output` commit. Any site not driven is a `failed` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved yr3d4o --by-human`). OQ-01 and OQ-02 are resolved; no open question remains. Scope fence: `- Scope-Paths:` declares every path this plan may change; an edit outside it must be justified at finalize via `--scope-reason`. Commit only the Scope-Paths files, through `aw commit yr3d4o -- <paths>`; never `git add -A`, never push. Every test claim MUST be backed by the ACTUAL pasted runner output; never claim a run you did not perform. Lifecycle: in a managed lane the runner owns `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd begin yr3d4o`, fill every `V-*` with pasted output, confirm `aw ipd lint --phase pre-transition` conforms, then `aw ipd finalize yr3d4o`; never hand-roll a `git mv` into `executed/`. backlog `aluots` closes through the From-Backlog handoff when this plan executes.
