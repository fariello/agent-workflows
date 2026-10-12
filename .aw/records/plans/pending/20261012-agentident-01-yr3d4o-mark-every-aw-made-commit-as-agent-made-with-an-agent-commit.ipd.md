# IPD: Mark every aw-made commit as agent-made with an agent committer identity and runner trailers

- Date: 2026-10-12
- Kind: child
- Concern: You cannot tell from `git log` which commits an agent made and which you made. Every commit is authored and committed as the user. The only agent marker is an `AW-Run:` trailer, and most aw-made commits lack it: measured 2026-10-11, 2,509 of 9,520 commits on `main` carry it, and only 127 of the last 300. Unmarked aw-made commits include runner merges (`integrate(...)`), plan finalize commits (`lifecycle(...)`), some runner work commits (e.g. `0dd8c3a3e`), and everything an interactive agent session commits through `aw commit`.
- Scope: Every commit and merge that aw makes keeps the user as AUTHOR and records `AW Agent (<model>) <local+aw@domain>` as COMMITTER, where the address is the user's own email with `+aw` added before the `@`. Every such commit carries the trailers `AW-Runner: <runner>` (`aw oc run`, `aw agy run` or `aw commit`) plus `AW-Run` and `AW-Item` when they are known. A commit the user makes with plain `git commit` is unchanged. No new accounts, keys, GitHub settings or required configuration.
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/commit_lock.py, agent_workflows/ipd_lifecycle.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/work_cmd.py, agent_workflows/coverage_record.py, agent_workflows/engine.py, agent_workflows/cli.py, tests/test_agent_commit_identity.py, docs/commit-identity.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: aluots
- Set: agentident
- Order: 1
- Highest E allocated: 06
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: yr3d4o

## Workflow history
- 2026-10-12 to-review (aw set): authored from backlog aluots on the maintainer's instruction (plans preferred to backlog items); design decided by the maintainer 2026-10-11

- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every aw-made commit identifiable as agent work at a glance, with `git log --format='%an | %cn'` and the trailers, while the user stays the author, nobody has to create an account, and commits the user makes by hand are untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: one definition of the agent identity

- [ ] E-01 MEASURE FIRST, then build. In a throwaway repo, make one commit through each path listed in E-03 on unmodified code and record each commit's `%an <%ae> | %cn <%ce>` and trailers (`git log -1 --format='%(trailers)'`). Expected: author and committer are both the repo's user identity everywhere; `AW-Run` appears only where a run id was available. This is the before-state that E-05's tests must show changed.
  - Depends on: none
  - Expected outcome: a pasted table of path -> author, committer, trailers on unmodified code.
  - Execution state: pending

- [ ] E-02 Add ONE helper in `git_commit_helper` that returns the git environment and trailer set for an aw-made commit, and nothing else computes them:
  - COMMITTER NAME: `AW Agent (<model>)`. `<model>` is the run's resolved model (`options["model"]`, the value `runner_shared.driver_actor` already renders) or, outside a run, the `AW_AGENT_MODEL` environment variable when set; otherwise `unknown`. Never guessed.
  - COMMITTER EMAIL: the user's email from `git config user.email` with `+aw` inserted before the `@` (`a@b.com` -> `a+aw@b.com`). If the address already has a `+` tag, append `-aw` to the tag rather than adding a second `+`. If there is no user email at all, set no committer override and let git behave exactly as it does today (the commit would fail or succeed the same way it would have).
  - AUTHOR: never set. Git's normal identity applies, so the user stays the author.
  - TRAILERS: `AW-Runner: <runner>`, plus `AW-Run` and `AW-Item` from `run_item_trailers` when present. The runner value is `aw oc run`, `aw agy run` or `aw commit`; an unknown caller writes no `AW-Runner` rather than a made-up one.
  - Model names are sanitized for use in an identity: strip newlines, `<`, `>` and parentheses, and collapse whitespace, so `Gemini 3.8 Flash (High)` becomes `Gemini 3.8 Flash High`.
  - Depends on: E-01
  - Expected outcome: a pure function, unit-tested in E-05, that maps (user email, model, runner, run id, item id) to the env overrides and trailer lines.
  - Execution state: pending

### Task group 2: use it on every aw commit path

- [ ] E-03 Apply the helper on every path where aw itself creates a commit or merge. Each must pass the env overrides to its `git commit` / `git merge` subprocess and append the trailers to its message (merges take trailers in the `-m` message):
  - `commit_lock.commit_isolated` (both `git commit` calls), which `git_commit_helper.offer_commit` and `aw commit` use;
  - `ipd_lifecycle._finalize_transaction` (the `lifecycle(...)` finalize commit);
  - `runner_shared` lane integration (`git merge --no-ff ... -m "integrate(...)"`) and `prepare_lane_for_conflict_resolution`'s merge commit;
  - `coverage_record.write`, `engine._commit_paths`, and `cli._offer_commit_uninstall`.
  The shared runner `git_commit_helper._git` / `runner_shared._run_git` stay generic; the env is passed by the commit and merge call sites, so reads, `merge --ff-only` and every non-commit git call are untouched. A fast-forward creates no commit and needs nothing.
  - Depends on: E-02
  - Expected outcome: every listed call site creates commits whose committer is the agent identity and whose message carries the trailers; no other git call changes.
  - Execution state: pending

- [ ] E-04 Make the AGENT'S OWN commits inside a run carry the identity too. Both runners already build the agent child environment in one place and export `AW_RUN_ID` / `AW_ITEM_ID6` there (`oc_runipd` and `agy_runipd`, beside `git_commit_helper.RUN_ID_ENV`). Also export `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL` and `AW_AGENT_MODEL` from the E-02 helper, with runner `aw oc run` or `aw agy run`. Any `git commit` the agent runs in its lane then gets the agent committer automatically. `work_cmd`, which reads `AW_RUN_ID` for trailers, also reads the runner from the run state so its commits carry `AW-Runner`.
  - Depends on: E-02
  - Expected outcome: a commit made by a scripted agent inside a runner turn has the agent committer, the user author, and `AW-Run`, `AW-Item`, `AW-Runner`.
  - Execution state: pending

### Task group 3: pin and document

- [ ] E-05 Add `tests/test_agent_commit_identity.py`, driving real git in `tmp_path` repos and asserting on `git log` output, never on source text. Cases: (a) the helper's mapping table: plain address, already-tagged address, missing email, model sanitizing, unknown model, unknown runner; (b) `aw commit` through `cli.main` yields author = repo user, committer = `AW Agent (<model>) <user+aw@...>`, trailer `AW-Runner: aw commit`; (c) a finalize through `ipd_lifecycle.finalize` yields the same identity and `AW-Runner`; (d) a lane integration merge through the runner's integrate path yields the identity and trailers on the merge commit; (e) the oc and agy agent child envs contain the committer variables and `AW_AGENT_MODEL`, and a scripted agent's `git commit` in the lane gets them; (f) a plain `git commit` in the same repo, outside aw, keeps author = committer = user, proving nothing global changed; (g) with no `user.email` configured, aw sets no committer override. Cases (b)-(d) must FAIL on the base commit; show it.
  - Depends on: E-03, E-04
  - Expected outcome: the module passes, and (b)-(d) are shown failing before the change.
  - Execution state: pending

- [ ] E-06 Document and prove. Write `docs/commit-identity.md` (short: what the committer and trailers mean, how to filter agent commits with `git log --committer='AW Agent'` and `git log --format='%h %an | %cn %(trailers:key=AW-Runner,valueonly)'`, and the honest limit). Add a CHANGELOG entry. Both are user-facing: no em or en dashes. Run the existing `tests/test_commit_run_trailers_env.py`, `tests/test_finalize_trailer_attribution.py` and `tests/test_git_commit_helper.py`, then the bare suite. Then make one real `aw commit` in this repository and paste its `git log -1 --format='%an <%ae> | %cn <%ce>%n%(trailers)'`.
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
| F-06 | Git reads the committer from the environment for commits and merges. | `GIT_COMMITTER_NAME` / `GIT_COMMITTER_EMAIL` (git-commit(1), git-merge(1) "ENVIRONMENT"). |
| F-07 | No existing doc describes the trailers. | `grep -rln "AW-Run" docs/` returns nothing. |

## Proposed changes (ordered, validatable)

1. One helper for the identity and trailers (E-02).
2. Every aw commit and merge path uses it (E-03).
3. The runners hand it to the agent's own commits (E-04).
4. Tests, doc, CHANGELOG, live proof (E-05, E-06).

## Deferred / out of scope (with reason)

- Separate GitHub accounts, deploy keys, credential hiding, branch protection, PR requirements: considered with the maintainer on 2026-10-11 and declined; the toolkit must stay zero-setup.
- Rewriting existing history to add the identity: not requested. The maintainer asked for this change only (2026-10-11), after weighing a history rewrite for the 320 `Test` commits as low value.
- Preventing an agent from running raw `git commit` with the user's identity: not enforceable without a separate OS user; the label is accepted as sufficient.

## Scope check

- Over-scope: none. Each declared path is a call site in F-04/F-05, the helper's home, the new test module, the new doc, or the CHANGELOG.
- Under-scope: none known. If E-01 finds an aw commit path not in F-04, add it to E-03 and to Scope-Paths before changing code, and record it in Findings.

## Required tests / validation

- `tests/test_agent_commit_identity.py` (new), with (b)-(d) shown failing on the base commit.
- `tests/test_commit_run_trailers_env.py`, `tests/test_finalize_trailer_attribution.py`, `tests/test_git_commit_helper.py` passing.
- Bare suite `python3 -m pytest`.
- One live `aw commit` in this repository, with its author, committer and trailers pasted.

## Spec / documentation sync

No spec governs commit identity or the trailer set, so none is amended. The trailers are documented for the first time in `docs/commit-identity.md`, and the change is announced in `CHANGELOG.md`.

## Open questions

### OQ-01: How does an interactive agent session say which model it is?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: Resolved on repository evidence: there is no reliable way to detect the model of an interactive session from inside aw (this session exposes only `OPENCODE`, `OPENCODE_PID` and `AGENT` in its environment, none naming a model). So outside a run the model comes from `AW_AGENT_MODEL` when the session sets it, and is otherwise `unknown` (E-02). Never guessing follows the existing rule for trailer values (`git_commit_helper.run_item_trailers`). Reversible: a later change could teach host integrations to set `AW_AGENT_MODEL`.

### OQ-02: Should `aw commit` used by a human by hand also get the agent committer?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: Resolved by the author as an INFERENCE, not a maintainer ruling: the maintainer said (2026-10-11) that almost all work is agent-driven and that corrections are made by telling an agent, so `aw commit` is in practice the agent's commit path. A human committing by hand uses plain `git commit`, which E-05 (f) proves is unchanged. Reversible and cheap to change: if the maintainer wants a human-run `aw commit` to keep the user as committer, the helper needs a way to tell the two apart (e.g. an explicit `--as-human` flag), and that is the review's call.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the before-state table (path -> author, committer, trailers) from the throwaway repo on unmodified code.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the helper's unit-test output for every mapping row in E-05 (a).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git log -1 --format='%an <%ae> | %cn <%ce>%n%(trailers)'` for a commit from each E-03 call site, produced by E-05 (b)-(d) or by driving the remaining sites directly.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the oc and agy agent child env keys showing the committer variables and `AW_AGENT_MODEL`, and the scripted lane commit's author, committer and trailers (E-05 (e)).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_agent_commit_identity.py -v` passing, and cases (b)-(d) failing against a worktree at the base commit.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the three existing modules passing, the bare-suite summary line, the doc and CHANGELOG diffs, and the live `aw commit`'s `git log -1` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved yr3d4o --by-human`). Commit only the Scope-Paths files, through `aw commit yr3d4o -- <paths>`; never push. Paste actual runner output for every test claim. After every `V-*` passes, finalize with `aw ipd finalize yr3d4o` (or let the runner self-finalize); backlog `aluots` closes through the From-Backlog handoff when this plan executes.
