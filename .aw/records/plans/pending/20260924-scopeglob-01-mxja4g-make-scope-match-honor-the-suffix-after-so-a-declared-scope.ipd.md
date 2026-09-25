# IPD: Make _scope_match honor the suffix after '**' so a declared Scope-Paths glob cannot admit every file under its directory

- Date: 2026-09-24
- Kind: child
- Concern: `ipd_lifecycle._scope_match` is the ONE predicate behind every Scope-Paths fence in the toolkit: the pre-commit refusal in `work_cmd.run_commit` (via `work_cmd._in_scope`), the finalize scope reconciliation in `ipd_lifecycle.finalize_precheck` (directly and via `ipd_lifecycle._working_tree_path_is_owned` / `ipd_lifecycle._is_implicitly_allowed`), the begin baseline dirty check (`dirty_within(str(repo_root), scope_paths, _scope_match)`), the post-execution scope-drift rule in `check_engine` (`_life._scope_match(c, pat)`), and `wtiso_gate.check_scope`. For any pattern containing `**` that `fnmatch` rejects, it falls back to `prefix = pat.split("**", 1)[0].rstrip("/")` and returns a bare directory-prefix test, DISCARDING the suffix. Re-measured at HEAD `877545fc`: `_scope_match('tests/anything.txt', 'tests/**/*.py')` and `_scope_match('agent_workflows/README.md', 'agent_workflows/**/*.py')` are `True`, and the implicit allowance `.aw/records/**/index.md` admits ANY path under `.aw/records/`, e.g. `.aw/records/backlog/open/x.md`. The hole is not theoretical: 10 backlog files in 5 `work:` commits since 2026-09-22 entered plan-governed commits ONLY through that allowance (F-5). A second, smaller gap in the same branch: plain `fnmatch` lets `*` cross `/`, so `tests/*.py` admits `tests/sub/a.py`, contradicting the function's own comment "`dir/*.py` should not match nested" (F-3).
- Scope: IN: replace the glob branch of `ipd_lifecycle._scope_match` with a small pure, segment-aware matcher (`**` = zero or more whole segments, `*`/`?`/`[...]` confined to one segment, the remainder after `**` must match); keep the `dir/`, `dir/**`, and literal/bare-directory branches byte-equivalent in behavior; add a focused unit-test module pinning the backlog's rows plus positive `dir/**` and zero-segment `**` cases and the `aw commit` incident row; add one sentence to spec `ipd-structure-and-linting` Section 4.5 stating the matching semantics. OUT: the separate `fnmatch` fences in `orchestrate_isolation` and `verify_roles` (different grammar, fail-closed direction, F-7), renaming the lowercase `index.md` allowance (OQ-02), and adding any new implicit allowance for backlog filing (OQ-01).
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_scope_match.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
- Item-Dependencies: none
- Status: to-review
- Set: scopeglob
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: mxja4g
- From-Backlog: cfab6d
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog cfab6d; re-measured all four suffix-dropping rows and the two must-refuse rows at HEAD 877545fc, measured zero narrowing across all 438 plans declaring Scope-Paths, found 10 backlog files committed only through the hole since 2026-09-22, and ran the full bare suite with a segment-aware matcher patched in (1826 passed, identical to baseline).

## Goal

Make every Scope-Paths fence mean exactly what the plan author wrote: a `**` pattern must still require its suffix to match, and a single `*` must stay inside one path segment, so `aw commit` and the finalize scope gate stop silently accepting paths no plan declared.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the defect before changing it

- [ ] E-01 RE-MEASURE the defect rows at the execution HEAD before editing anything. Run a throwaway probe (under `/tmp/`, not committed) calling `ipd_lifecycle._scope_match` on the rows in the Findings table (F-1, F-2, F-3) and on the two must-refuse rows (`.aw/records/specs/x.spec.md` vs `.aw/records/plans/**`; any path outside the declared prefix). If any row already returns the CORRECT value, stop and report: the defect has been fixed by someone else.
  - Depends on: none
  - Expected outcome: the probe output shows the four suffix-dropping rows `True`, `tests/sub/a.py` vs `tests/*.py` `True`, and the `.aw/records/plans/**` vs spec row `False`, matching the Findings table.
  - Execution state: pending

### Task group 2: the matcher

- [ ] E-02 REPLACE the glob branch of `ipd_lifecycle._scope_match` (the block under `if "*" in pat or "?" in pat or "[" in pat:`) with a call to a new private pure helper, e.g. `ipd_lifecycle._glob_segments_match(path_segments, pattern_segments)`. Semantics: split both path and pattern on `/`; a pattern segment exactly `**` matches ZERO OR MORE whole path segments; every other pattern segment is matched against exactly ONE path segment with `fnmatch.fnmatch` (per segment, so `*`, `?`, `[...]` cannot cross `/`, and platform case behavior is unchanged from today's `fnmatch.fnmatch`); the match succeeds only when both sequences are fully consumed. Implement iteratively or with memoization so a pattern with several `**` segments cannot go exponential. DELETE the `split("**", 1)` prefix fallback entirely. Leave the `pat.endswith("/")`, `pat.endswith("/**")`, and literal branches unchanged (they are correct and the blast-radius probe relied on them being unchanged). Rewrite the docstring and the inline comment so they state the semantics above instead of "fnmatch handles `**` loosely". Do NOT change `scope_entry_is_literal_file`, `_entry_is_bare_directory`, or `ipd_schema.SCOPE_PATHS_IMPLICIT_ALLOWANCES`.
  - Depends on: E-01
  - Expected outcome: `_scope_match` returns `False` for every F-1/F-2/F-3 row and `True` for `tests/test_a.py` and `tests/s/t/a.py` vs `tests/**/*.py`, `.aw/records/index.md` and `.aw/records/plans/index.md` vs `.aw/records/**/index.md`, `a` and `a/b` vs `a/**`; no `split("**"` remains in the function.
  - Execution state: pending

### Task group 3: tests

- [ ] E-03 ADD `tests/test_scope_match.py`: a table-driven unit test over `ipd_lifecycle._scope_match` (pure, no filesystem, no git) containing at minimum: the FOUR backlog rows as must-REFUSE (`.aw/records/backlog/open/anything.backlog.md`, a `.spec.md`, a research file, and a comms inbox file, each vs `.aw/records/**/index.md`; plus `tests/anything.txt` vs `tests/**/*.py` and `agent_workflows/README.md` vs `agent_workflows/**/*.py`); the must-keep-refusing row `.aw/records/specs/x.spec.md` vs `.aw/records/plans/**`; the single-star row `tests/sub/a.py` vs `tests/*.py` must-REFUSE; and must-ACCEPT rows for `dir/**` (`a` and `a/b/c` vs `a/**`), zero-segment `**` (`tests/a.py` vs `tests/**/*.py`, `.aw/records/index.md` vs `.aw/records/**/index.md`), multi-segment `**` (`tests/x/y/a.py`), a trailing-slash dir (`tests/`), a bare dir literal (`agent_workflows` vs `agent_workflows/x.py`), and a pattern with two `**` segments. Each row carries a one-line reason so a failure message says which semantic broke. Include one row asserting a pathological pattern (e.g. `a/**/**/**/**/**/**/z` against a 30-segment non-matching path) returns `False` quickly, to pin E-02's no-exponential requirement.
  - Depends on: E-02
  - Expected outcome: the module passes against the fixed matcher, and at least the six must-refuse rows FAIL when E-02's change is temporarily reverted.
  - Execution state: pending

- [ ] E-04 ADD, in the same `tests/test_scope_match.py`, a small class pinning the two CALLERS that make this a fence: `work_cmd._in_scope('.aw/records/backlog/open/<x>.backlog.md', ['.aw/records/plans/pending'], '<plan_rel>')` must be `False` (this is the exact incident that surfaced `cfab6d` under plan `8u6770`), and `ipd_lifecycle._is_implicitly_allowed` must still be `True` for the plan file itself, for `.aw/records/plans/INDEX.md`, and for a path under `.aw/records/plans/executed/`, and `False` for a backlog, spec, and research path. This proves the fix keeps the three implicit allowances' intended meaning (F-6) while closing the hole.
  - Depends on: E-02
  - Expected outcome: the caller class passes after E-02; the `_in_scope` backlog row and the `_is_implicitly_allowed` backlog/spec/research rows FAIL with E-02 reverted.
  - Execution state: pending

### Task group 4: contract and regression

- [ ] E-05 AMEND spec `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 4.5 ("Value grammar" bullet list): add ONE sentence defining match semantics, namely that `**` as a whole segment matches zero or more path segments, any other glob character matches within a single segment only, and the portion after `**` must match. Re-run the blast-radius probe from Findings F-4 (every plan under `.aw/records/plans/` with a `- Scope-Paths:` value, old matcher vs new, over `git ls-files`) and record the count of plans whose effective scope narrowed.
  - Depends on: E-02
  - Expected outcome: one added sentence in Section 4.5, nothing else in the spec changed; the probe reports 0 narrowed plans (or, if a newly authored plan narrows, it is named in the V-05 evidence with the paths it loses).
  - Execution state: pending

- [ ] E-06 RUN the bare suite `python3 -m pytest` (no extra flags) after E-02..E-05.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: summary line with 0 failed; count equals the pre-change baseline plus the new tests.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_lifecycle._scope_match` owns the Scope-Paths matching grammar and every fence DELEGATES to it rather than restating it: `wtiso_gate` says "THE MATCHING RULE IS NOT RESTATED HERE. `ipd_lifecycle._scope_match` owns the Scope-Paths grammar", and `work_cmd._in_scope`, `check_engine`, `dirty_within` all call it. So a fix in this one function fixes every fence; there are NO other copies with the suffix-dropping fallback (`grep -rn 'split("\*\*"' agent_workflows/` finds only this function).
- `ipd_schema._scope_path_entry_error` (the Scope-Paths GRAMMAR validator) already treats `docs/**/*.md` as a legal bounded pathspec (`tests/test_ipd_schema.py` row "a glob at DEPTH with `**` in the middle is legal"); this plan changes MATCHING only, not which entries are legal.
- The implicit allowances are `ipd_schema.SCOPE_PATHS_IMPLICIT_ALLOWANCES`: `.aw/records/plans/**` ("the plan file itself moving through the lifecycle"), `.aw/records/plans/INDEX.md` ("the plans index refresh"), `.aw/records/**/index.md` ("a records-tree manifest/index refresh"). `tests/test_ipd_schema.py` asserts each is a legal pathspec and that one covers `.aw/records/plans/`.
- The four generated manifests (`records/plans/INDEX.{json,md}`, `records/research/INDEX.{json,md}`) are gitignored in `.aw/.gitignore` ("Written as four ANCHORED specific paths"), so they never appear in `git status --porcelain` or in a commit and never reach the fence.
- Commit via `aw commit mxja4g -- <paths>`; run the suite bare.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `877545fc` in this worktree with `python3` calling `agent_workflows.ipd_lifecycle._scope_match` directly (probe scripts under `/tmp/opencode/probe-scopeglob/`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle._scope_match`, `**` fallback | The implicit allowance `.aw/records/**/index.md` admits every path under `.aw/records/`. | probe output: `True .aw/records/backlog/open/anything.backlog.md .aw/records/**/index.md`; `True .aw/records/specs/x.spec.md .aw/records/**/index.md`. Over `git ls-files`: 1147 tracked paths are admitted by the allowances today and NOT by a correct matcher (e.g. `.aw/records/README.md`, `.aw/records/backlog/README.md`). |
| F-2 | HIGH | same | A DECLARED `**`-with-suffix entry degenerates to a directory prefix. | probe: `True tests/anything.txt tests/**/*.py`; `True agent_workflows/README.md agent_workflows/**/*.py`. Backlog claim HOLDS. |
| F-3 | MED | `ipd_lifecycle._scope_match`, `fnmatch.fnmatch(p, pat)` | Single `*` crosses `/`, so `dir/*.py` admits nested files, contradicting the function's own comment "`dir/*.py` should not match nested". Not in the backlog item; same branch, same fix. | probe: `True tests/sub/test_a.py tests/*.py`; `python3 -c "import fnmatch;print(fnmatch.fnmatch('tests/sub/a.py','tests/*.py'))"` -> `True`. |
| F-4 | INFO (blast radius) | every plan's `- Scope-Paths:` | ZERO plans narrow. Compared old vs segment-aware matcher over all `git ls-files` for every plan with a `- Scope-Paths:` value. The 12 glob entries in the whole plans tree are ALL trailing `/**` (e.g. `agent_workflows/**`, `tests/**`, `.opencode/commands/**`), which take the unchanged `endswith("/**")` branch; no pending plan declares any glob. | probe output: `pending plans with Scope-Paths: 10 narrowed: 0`, `executed ... 400 narrowed: 0`, `superseded ... 27 narrowed: 0`, `not-executed ... 1 narrowed: 0`. So no currently-passing finalize can start refusing on DECLARED scope. |
| F-5 | HIGH (behavior change) | `work_cmd.run_commit` via `work_cmd._in_scope` | The hole is ACTIVELY USED. Since 2026-09-22, 10 backlog files in 5 `work:` commits (`b369e3a3`, `14afd939`, `c23a02a1`, `de4ba4de`, `908db905`) were admitted into plan-governed commits ONLY via `.aw/records/**/index.md`. After the fix, `aw commit <plan>` will REFUSE a backlog file filed alongside plan work; the agent must commit it with `aw commit --no-plan` or declare it. That is the intended fence, but it is user-visible (OQ-01). Finalize is not blocked: such a path becomes `out_of_scope` and `runner_shared.compute_scope_reconciliation` supplies the `--scope-reason` automatically. | history probe over `git log --since=2026-08-01 --name-only`: 10 rows `ONLY-VIA-HOLE .aw/records/backlog/open/...`, 1 row `declared` (a spec). `python3 -c "...work_cmd._in_scope('.aw/records/backlog/open/20260922-x.backlog.md',['.aw/records/plans/pending'],...)"` -> `True` today. |
| F-6 | INFO | `ipd_schema.SCOPE_PATHS_IMPLICIT_ALLOWANCES` | The fix preserves each allowance's stated meaning. `.aw/records/plans/**` and `.aw/records/plans/INDEX.md` take unchanged branches (literal / trailing `/**`). `.aw/records/**/index.md` keeps matching any lowercase `index.md` at any depth including zero (`.aw/records/index.md` -> `True`). NO tracked file named `index.md` exists under `.aw/records/` (`git ls-files .aw/records \| grep -iE '/index\.(md\|json)$'` -> empty), and the real manifests are uppercase `INDEX.*` and gitignored, so after the fix this allowance matches nothing present today. It was never what admitted `research/INDEX.md` legitimately; only the hole did. | probe: `True True .aw/records/index.md`, `True True .aw/records/plans/index.md`; `git check-ignore -v .aw/records/research/INDEX.md` -> `.aw/.gitignore:48:records/research/INDEX.md`. |
| F-7 | LOW | `orchestrate_isolation.execute_merge_and_revalidate_gate` (`fnmatch.fnmatch(f, pat) for pat in declared_scope`), `verify_roles.procedure_scope_audit` (`fnmatch.fnmatch(path, a_pat)`) | Two OTHER scope fences use raw `fnmatch`, not `_scope_match`. They do NOT share the suffix-dropping bug (`fnmatch.fnmatch('tests/a.txt','tests/**/*.py')` -> `False`). Their divergence is `*` crossing `/` and `dir/**/*.py` NOT matching the zero-segment `dir/a.py`, i.e. mostly fail-closed. The only runtime caller of the merge gate (`runner_shared`, `execute_merge_and_revalidate_gate(... full_validation_runner=validation_runner,)`) passes NO `declared_scope`, so that branch is inert in production. Out of scope. | `grep -rn "declared_scope=" agent_workflows/runner_shared.py` -> no match; python probe above. |
| F-8 | INFO | suite | A segment-aware matcher breaks NO existing test. Full bare suite with the new matcher monkeypatched in via a `-p` plugin's `pytest_configure`: identical to baseline. No existing test references `_scope_match` with a `**`-suffix or `dir/*` pattern (only `tests/test_ipd_lifecycle_cli.py` touches scope matching, with literal paths). | `PYTHONPATH=/tmp/opencode/probe-scopeglob python3 -m pytest -p scopeprobe` -> `1826 passed, 1 skipped, 3 warnings in 25.92s`; baseline `python3 -m pytest` -> `1826 passed, 1 skipped, 3 warnings in 27.16s`. |

## Proposed changes (ordered, validatable)

1. E-01 re-confirms F-1..F-3 at execution HEAD.
2. E-02 replaces the glob branch with a pure segment-aware helper and deletes the prefix fallback.
3. E-03 pins matcher semantics with a table including the backlog's rows, `dir/**`, zero-segment `**`, and a no-blowup row.
4. E-04 pins the two fence callers, including the `8u6770` incident and the three implicit allowances.
5. E-05 states the semantics in spec Section 4.5 and re-runs the blast-radius probe.
6. E-06 runs the bare suite.

## Deferred / out of scope (with reason)

- Converging `orchestrate_isolation.execute_merge_and_revalidate_gate` and `verify_roles.procedure_scope_audit` onto `_scope_match` (F-7). They do not have this defect, the merge-gate branch is inert in production, and `verify_roles` evaluates a workflow `allowed_paths` fence whose grammar is not Scope-Paths.
  - Carrier-Declined: Different fence grammar without the suffix-dropping defect; the only production caller of the merge gate passes no declared_scope. Not an outstanding obligation of this item.
- Renaming the implicit allowance `.aw/records/**/index.md` to match the real uppercase `INDEX.*` manifests (OQ-02). Those manifests are gitignored and never reach the fence, so the rename changes nothing observable today.
  - Carrier-Declined: No observable effect while the manifests are gitignored (`.aw/.gitignore` anchored rules); a maintainer may revisit if a tracked lowercase index is ever introduced.
- Adding an implicit allowance for backlog items filed during execution (OQ-01).
  - Carrier-Declined: Would widen the fence the spec defines as "A plan's own lifecycle artifacts" only; default is to keep that meaning and commit such files with `aw commit --no-plan`.

## Scope check

- Over-scope: F-3 (single `*` confined to one segment) is not named in `cfab6d`, but it lives in the same branch E-02 rewrites, the function's own comment already states it as intended behavior, and F-4 measured zero plans narrowing from it. Splitting it out would require E-02 to deliberately re-implement a known bug.
- Under-scope: none. `grep -rn 'split("\*\*"' agent_workflows/` finds only `_scope_match`; every Scope-Paths fence delegates to it (Project conventions).

## Required tests / validation

- `python3 -m pytest tests/test_scope_match.py -o addopts="" -q` passing, and the must-refuse rows shown FAILING with E-02 reverted (proves the test can fail).
- `python3 -m pytest tests/test_ipd_schema.py tests/test_ipd_lifecycle_cli.py -o addopts="" -q` still passing (grammar and lifecycle callers).
- The blast-radius probe re-run (E-05) reporting narrowed-plan counts.
- Bare `python3 -m pytest` summary line pasted.

## Spec / documentation sync

- Spec `ipd-structure-and-linting` (`.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`) Section 4.5 lists `docs/**/*.md` as legal but never says what it MATCHES; that silence is what let a directory-prefix implementation pass as conforming. E-05 adds one sentence stating the segment semantics so the contract every fence is reviewed against is explicit. Declared in `- Scope-Paths:` per the spec-amendment rule. The implicit-allowance sentence in the same section is unchanged, because F-6 shows the fix preserves its meaning.
- `wtiso_gate.check_scope`'s docstring lists "`dir/**`, and fnmatch globs" as the grammar; it stays accurate enough (it delegates) and is not edited.

## Open questions

### OQ-01: Should backlog items filed during a plan's execution become an implicit allowance, now that the hole that silently admitted them closes?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default, which the plan proceeds with: NO new allowance. Spec Section 4.5 limits implicit allowances to "A plan's own lifecycle artifacts", and `cfab6d` itself was filed precisely because `aw commit 8u6770` accepted a backlog path under a plan whose declared scope was `.aw/records/plans/pending`, which the filer treated as a defect. F-5 measured the practical cost: about 10 files across 5 commits in two days would instead need a separate `aw commit --no-plan`. Finalize is unaffected because the runner auto-supplies `--scope-reason`. The maintainer may choose to add `.aw/records/backlog/**` as an allowance later; that is a scope-policy decision and a separate change.

### OQ-02: Should the `.aw/records/**/index.md` allowance be corrected to the real uppercase manifest names?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: leave it. F-6 shows no tracked `index.md` exists under `.aw/records/` and the real `INDEX.*` manifests are gitignored, so neither spelling ever reaches the fence today; changing it is cosmetic and would also require amending the spec's allowance sentence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the probe command and its full output at the execution HEAD (`git rev-parse --short HEAD` pasted too), showing `True` for the four F-1/F-2 rows and the F-3 row, and `False` for `.aw/records/specs/x.spec.md` vs `.aw/records/plans/**`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- agent_workflows/ipd_lifecycle.py` showing the prefix fallback removed and the helper added; paste `grep -n 'split("\*\*"' agent_workflows/ipd_lifecycle.py` returning nothing; paste the same E-01 probe re-run now showing `False` for every defect row and `True` for the positive rows listed in E-02's expected outcome.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_scope_match.py -o addopts="" -q` summary showing all passed; then, with E-02's hunk temporarily reverted (`git stash` is forbidden in a shared checkout, so revert by hand or copy the old function into a throwaway patch), paste the same command showing the must-refuse rows FAILING; then paste the passing run again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the caller-class run (`python3 -m pytest tests/test_scope_match.py -o addopts="" -q -k <class name>`) passing, and the same run FAILING on the `_in_scope` backlog row and the `_is_implicitly_allowed` backlog/spec/research rows with E-02 reverted; paste `python3 -m pytest tests/test_ipd_schema.py tests/test_ipd_lifecycle_cli.py -o addopts="" -q` summary still passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff -- .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` showing exactly one added sentence in Section 4.5; paste the blast-radius probe command and its per-directory output lines (`<dir> plans with Scope-Paths: N narrowed: M`), naming any narrowed plan and the paths it loses.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest`, showing 0 failed and a passed count at least the baseline `1826 passed` plus the new tests.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. OQ-01 and OQ-02 are `Blocking: no` and the plan proceeds on their stated defaults. The executor commits only the `- Scope-Paths:` paths via `aw commit mxja4g -- <paths>`, never `git add -A`, and never pushes; test claims paste actual runner output. After every V-* passes and `aw ipd lint --phase pre-transition` conforms, finalize with `aw ipd finalize` to move the plan to `.aw/records/plans/executed/`, and close backlog `cfab6d` via the From-Backlog handoff.
