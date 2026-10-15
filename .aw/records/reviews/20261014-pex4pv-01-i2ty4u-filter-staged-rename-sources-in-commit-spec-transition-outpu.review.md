# Review findings: plan i2ty4u

- Subject-Id: i2ty4u
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane. The plan was committed and unchanged (`a276ac80e`), so no snapshot was needed. `aw ipd lint --phase author` was clean before and after the revisions, and pre-transition lint reports only the expected not-yet-executed `IPD-S404` items (no carrier finding).

Three throwaway probes ran under the gitignored `.aw/state/` and were deleted afterwards:

- Unit shapes at HEAD. Staged `git mv` case: `specs set --no-commit` (with a linked `pln010` plan) left `RM approved/... -> implementing/...` plus `?? .aw/records/history.jsonl`. `commit_spec_transition_output` returned a sha, and HEAD read `transition(spec): move spc010 -> implementing` with trailers `AW-Run: r1`, `AW-Item: spc010`, `AW-Committed-By: driver` and `R075`. Without the linked plan, `specs set` refused with `[no-handoff]`. Unstaged move: ` D` + `??` gave a sha and `R089`. Note: `specs note <abs path>` followed by `is_note=True` gave `note(spec): record planned stage for spc010`. `specs note ... --dir` exited 2 with `unrecognized arguments`.
- End to end on both hosts, current code against the emulated pre-fix `git add -- *allowed`. Non-isolated runs: current code recorded `spec_transition_commit` and the `spec-transition-committed` event; under the mutation neither was recorded, `RM` stayed staged, and the item still ended `executed`. Isolated runs: current code put the spec in `implementing/` with no `preserved_worktree`; under the mutation the spec stayed in `approved/`, `preserved_worktree` was set, and the item still ended `executed`.
- The `_in_index` branch. On an unstaged move, the successful commit is the same with or without the branch. With a rejecting pre-commit hook, the index is left as ` D <old>` + `A  <new>` without the branch and as `R  <old> -> <new>` with it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Verification feasibility | old E-02 subcase 2 and E-03 sensitivity (2): "assert that immediately after `git add` the index already holds a single staged rename"; `runner_shared.commit_spec_transition_output` commits with `git commit ... -- *allowed`; review probe (successful commit is `R089` either way) | Sensitivity check (2) was satisfiable only through a `_run_git` spy that inspects the intermediate index, which is an implementation-step pin. The outcome-level consequence of the `_in_index` branch was never named. The finding also overstated the branch: with no hook the commit is the same either way. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced the spy with an observable outcome. Subcase (2b) uses a rejecting pre-commit hook and asserts the `R  <old> -> <new>` index left behind. Sensitivity (2) now targets (2b), and F-03 states the branch is consistency and failure-state hygiene. |
| PR-002 | HIGH | IN-SCOPE | G. Executability | `aw specs note --help` (no `--dir`); probe exit 2 `unrecognized arguments: --dir`; runner invokes `specs note <rel>` with `cwd=target_tree` (`runner_shared.execute_item_core`) | Subcase 3 called `cli.main(["specs", "note", new_rel, ..., "--dir", ...])`, which exits 2, so the note case could never pass as written. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Uses the absolute spec path without `--dir` and asserts rc 0 (demonstrated). |
| PR-003 | MEDIUM | IN-SCOPE | G. Right-sizing | old E-02 bundled a new unit test plus edits to two end-to-end tests with different harnesses | One E-item covered two independent test surfaces and three deliverables. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split it into E-02 (unit) and E-03 (end to end). The old E-03 became E-04, with matching V-02..V-04, and Proposed changes, Required tests and the gate were all reconciled. |
| PR-004 | MEDIUM | IN-SCOPE | E. Test precision | probe: `specs set` leaves `?? .aw/records/history.jsonl`; `[no-handoff]` refusal without a linked plan | Subcase 1's "no tracked entries" was ambiguous next to the setter's untracked history file. The need for the linked plan was not explained. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The assertion now allows only `??` lines. The linked plan is required and the reason recorded. `specs set` rc is asserted. |
| PR-005 | LOW | IN-SCOPE | Evidence drift | `def offer_commit(` at `git_commit_helper.py:972` (plan said 1192); `def commit_backlog_transition_output(` at `runner_shared.py:4129` (plan said 4160); `if bkl_trans_commit:` near `runner_shared.py:37030` (plan said 41913) | The anchors resolve; only the line numbers had drifted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected the line hints. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract and lifecycle | `## Approval and execution gate`; `- Scope-Paths:`; Deferred row `Carrier-Declined: deliberate non-goal ... as described above`; OQ-01 `Owner: Antigravity` | Several pieces were missing or weak. The gate had no scope fence, no `--by-human` approval step, no never-tag rule, no staged-set check, and no rule that the E-04 mutations are never committed. The plan file was not in Scope-Paths. The carrier reason was boilerplate. The owner named an agent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the full contract and the plan path. Gave the carrier a substantive reason (E-03 now makes a silent `None` fail the suite). Set the owner to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the tests prove the `_in_index` branch matters without pinning internals? | A rejected-commit subcase (pre-commit hook exits 1) asserting the index state left behind | Keep the `_run_git` spy (pins an internal step; P16); drop the branch from scope (would diverge from the two sibling call sites) | Review probe above; `git_commit_helper._in_index` docstring; AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE" | yes |
| D-2 | Split old E-02? | Split into unit (E-02) and end-to-end (E-03) items | Keep bundled | plan-review rubric G right-sizing (a), (b) | yes |
| D-3 | Make a `None` return a `fail-gate` disposition? | Keep it deferred, with a substantive `Carrier-Declined` | Add to scope (changes spec 25kzda 5.5 production contract, outside `pex4pv`) | Backlog `pex4pv` Solution section scopes the fix to `commit_spec_transition_output` | yes |
| D-4 | Accept OQ-01 resolution? | Yes, as authored (owner corrected to plan author) | Reopen | `git show a6a86e1d81`; backlog `pex4pv` is `graduated` with `Blocks-Release: next` | yes |
