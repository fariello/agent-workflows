# Review findings: plan c6f6sj

- Subject-Id: c6f6sj
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `b4ca10b1f`. The plan was committed and byte-identical to the lane input, so no
pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and
`--phase review-finalize` clean after revision.

Re-verified by reading and by scratch-repo CLI probes (tempfile repos built with the
`tests/test_releases_line_writers.py` `_setup_test_repo` fixture; no production edit):
- `specs._offer_specs_set_commit` (`agent_workflows/specs.py:1028`) and `status_set._offer_self_commit`
  (`agent_workflows/status_set.py:1812`) are as the plan describes: same reset, same `assume_yes`, same
  `on_unrelated_staged="scope"`, `print` vs `sys.stdout.write`. `canonical_type("specs") == "specs"`.
- Both inheritance copies print `aw set: inherited - Blocks-Release:` (`status_set.py:1296`, `specs.py:964`);
  `aw specs set <path> --status to-review --from-backlog bkl001` printed `aw set: inherited ...` (F-02 confirmed).
- `--status ... --commit` and positional `--commit` both produced `chore(specs): set status to-review`
  as a single `R051 draft/... -> to-review/...` entry, with an unrelated staged `other.txt` left staged.
- `--yes --agent` without `--commit` created no commit on either spelling.
- Explicit `--blocks-release -` suppressed inheritance on both spellings; a resolvable ungated item exited 0,
  status changed, no gate written, on both spellings.
- An UNRESOLVABLE `--from-backlog` is refused on both spellings (`izh17y`), pinned by
  `test_cli_specs_set_refuse_unresolvable_backlog_id` / `test_cli_ipd_set_refuse_unresolvable_backlog_id`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D. Anti-regression | `agent_workflows/specs.py:942` `unresolvable backlog id` (exit 2); `agent_workflows/status_set.py:1253` `raise ValueError`; plan E-04(e), V-02 | E-04(e)/V-02 demanded exit 0 and no gate for an UNRESOLVABLE `--from-backlog`. Both spellings deliberately refuse that (izh17y) and existing tests pin it; the demand was unsatisfiable without deleting a shipped guard. The write-never-refuse property concerns an un-inheritable GATE. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04(e), E-02 outcome, V-02, V-04 retargeted to a resolvable ungated item; V-02 also requires showing the unresolvable refusal still holds; F-06 added. |
| PR-002 | MEDIUM | UNDER-SCOPE | E. Testing | `tests/test_releases_line_writers.py:532` `assertIn("aw set: inherited - Blocks-Release: relaaa", ...)` on the `--status` path | The prefix correction turns an existing test red, and that file was not in Scope-Paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to Scope-Paths and to E-04 (change only that string; the positional twin at :431 stays); V-04 requires it passing; F-07 added. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing (probe feasibility) | `agent_workflows/git_commit_helper.py:534` `on_unrelated_staged: str = "scope"` | E-03's probe "drop `on_unrelated_staged="scope"`" is a no-op because `scope` is the default; case (c) would not fail. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Probe redefined as flipping it to `"refuse"` in E-01, E-03, V-03 and conventions. |
| PR-004 | MEDIUM | IN-SCOPE | G. Executability | `agent_workflows/status_set.py:767` lazy `import specs`; `specs.py:846` function-local `from agent_workflows.status_set import ...`; `status_set.py:1282-1298` works on `new_lines` | Plan did not say where the shared helpers live or the inheritance helper's signature (list vs text, where the guards sit, whether the unresolvable refusal moves). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/E-02 now name `status_set` as home (spec wy9aru 4.1), function-local import, text-in/text-out signature, guards inside, refusal stays per-caller. |
| PR-005 | LOW | IN-SCOPE | E. Testing | `specs.py:1023` `touched_paths = [src_rel, dest_rel] if moving else [src_rel]`; probe showed `R051 draft/... -> to-review/...` | "exactly the spec file staged" mis-describes a transition that relocates the spec; an executor asserting one path would fail or narrow the paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/E-03 now expect a single rename via `git show --name-status`; legal-transition and fixture guidance added. |
| PR-006 | LOW | IN-SCOPE | G. Open questions | `tests/test_status_set.py:758` `patch("sys.stdout", buf)`; no `builtins.print` patch in tests | OQ-01 answerable from the repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved; executor re-runs the search in V-01. |
| PR-007 | LOW | UNDER-SCOPE | G. Execution contract | plan "Approval and execution gate"; `pyproject.toml:205` addopts | Gate lacked begin/finalize ownership (runner vs hand), scope-reason/ack fence wording; conventions misquoted addopts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added; addopts corrected. |
| PR-008 | LOW | IN-SCOPE | G. Executability | `CHANGELOG.md:7` and `:109` both `(pending)` | "the pending-release heading" is ambiguous. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 names the topmost pending heading and `- Fixed:` voice. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should E-04(e) keep demanding exit 0 for an unresolvable id? | No; test a resolvable ungated item and keep the refusal | Remove the izh17y refusal | `specs.py:930-946`, `status_set.py:1242-1255`, existing refuse tests | yes |
| D-2 | Where do the shared helpers live? | `status_set`, reached by function-local import | A new module; `specs` | spec wy9aru 4.1; `specs.py:846` precedent | yes |
| D-3 | Update the existing `aw set:` assertion on the `--status` path? | Yes, that one string only | Leave it (red suite) | `tests/test_releases_line_writers.py:532` | yes |
| D-4 | OQ-01 answer | No test patches the sink by name | Leave open for executor | search of `tests/`; `tests/test_status_set.py:758` | yes |
