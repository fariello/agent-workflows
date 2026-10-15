# Review findings: plan yfo6z6

- Subject-Id: yfo6z6
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `4ead57c34`. The plan was committed and unchanged (sha256 matched the sealed lane input `0f1636ed...`), so no snapshot was needed. `aw ipd lint --phase author` was clean before review. `--phase review-finalize` is clean after the revisions. `--phase pre-transition` no longer reports `check.ipd-uncarried-obligation`; only the expected `IPD-S404` errors remain.

Verified against code:

- `agent_workflows/work_cmd.py` `run_commit` calls `_gch.offer_commit(repo_root, paths, ..., on_unrelated_staged="scope", ...)` and has no other commit path.
- The `if no_plan:` comment carries the stale "no live guard currently asserts this" line cited by E-03.
- `19313eed7^:tests/test_work_primitives.py` holds `_GitArgvRecorder`, `test_commit_delegates_to_the_one_shared_commit_helper` and `test_commit_holds_no_forked_git_commit_path_of_its_own`, as Findings state.
- `ev7t1w` row S-27 exists.

Prototype of E-01/E-02 under the gitignored `.aw/state/` (deleted afterwards), mutations via a `-p` plugin:

| Run | Result |
|---|---|
| unmutated (both delegation modes, co-worker, both no-fork modes, sanity) | `5 passed` |
| `work_cmd._gch` rebound to a shim whose `offer_commit` runs its own `git add` + `git commit` | `2 failed, 3 passed` (delegation `0 != 1`; no-fork exit `0 != 1`) |

A plan-mode co-worker probe also left `tests/other.py` staged and out of HEAD.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | G. Lifecycle gate | pre-transition lint `check.ipd-uncarried-obligation: 2 obligation(s) name no durable carrier` | Neither Deferred row had a carrier, so the plan could never finalize. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a reasoned `Carrier-Declined` to both rows. The rule is cleared. |
| PR-002 | MEDIUM | IN-SCOPE | E. Test executability | prototype: a second mode re-committing an unchanged `src/feature.py` returns `nothing-to-commit` (exit 1) | E-01 drives two modes against one fixture without saying that each needs a fresh change. The assertion `git show --name-only HEAD` "lists no other path" also includes the header and subject lines. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires a fresh change or one method per mode, and uses `--format=` for an exact path list. |
| PR-003 | LOW | IN-SCOPE | E. Mutation hygiene | E-03 edits the same file the V-02 mutation edits | The mutation recipe did not order the revert relative to E-03, so a revert could wipe the comment edit or leave the mutant in place. It also did not say the mutant must report `committed`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified the mutant shape and the ordering (revert, then E-03), plus the measured result. The full suite now runs last. |
| PR-004 | LOW | IN-SCOPE | E. Evidence precision | V-01 grep `inspect|ast\.|read_text\(.*work_cmd` | The pattern matches prose (for example "last.") and misses a `read_text` on a variable path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Tightened to imports and attribute use, `getsource` and any `read_text(`, with each hit justified. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | old gate paragraph; OQ-01 `Owner: none` | The gate lacked the hard-MUST paste rule, the scope fence, `aw ipd begin`, and the runner/hand finalize split. It also implied a hand move to `executed/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with the standard contract (no stop-on-scope wording). The owner is set to the plan author. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the deleted `assertIs(work_cmd._gch, gch)` identity check be restored? | No. The spy and no-fork tests prove routing behaviourally. | Restore it (rejected: a module-identity assertion pins structure, not outcome, under P16) | `19313eed7^:tests/test_work_primitives.py` `test_commit_delegates_to_the_one_shared_commit_helper`; AGENTS.md P16 | yes |
