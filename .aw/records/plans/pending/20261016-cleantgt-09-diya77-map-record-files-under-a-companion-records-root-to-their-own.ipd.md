# IPD: Map record files under a companion records root to their owning repository

- Date: 2026-10-16
- Kind: child
- Concern: Plan `ki6t17` (backlog `4uw2a6`) adds `project_context.record_owner_root`, the inverse of `project_context.project_records_dir`, and routes thirteen record-file-to-root walkers through it, but only for records under `AW_HOME/projects/<id>/records/`; for any other path it returns `None` and the walker's `.aw`/`.agents`/`.git` parent climb runs. Backlog `miq4mi` asked whether a record under a COMPANION records root (`records_backend: companion`, records at `<companion_dir>/records`, default `<repo>.aw/records`) misroutes the same way. Measured at HEAD `36c9f21ff` on a real `aw install --preset public-target-private-companion`: it does (F-01..F-05). The walkers return the record's own directory, the companion root, or cwd instead of the target; `aw ipd lint --phase pre-execution` reports a FALSE `check.ipd-dependency-dangling` for an existing sibling plan; `aw specs note` creates a stray `.aw/records/history.jsonl` INSIDE the companion's `records/specs/draft/` directory; and `check_engine._identity_rename_hint` suggests nothing.
- Scope: IN: (1) extending `project_context.record_owner_root` with a companion branch: for a path that lies under a `records` directory whose parent is not `.aw`/`.agents` (cheap string fast path), try in order a cwd-anchored candidate, the default sibling-companion convention (`<X>.aw/records/...` -> candidate `<X>`), and every `registry.json` `target_paths` entry, ACCEPTING a candidate only when the path lies under `project_records_dir(candidate)` and that candidate's resolved `records_backend` is `companion`; (2) a behavioral test module; (3) a placement-spec amendment and a CHANGELOG line. Because `ki6t17` routes every walker through the resolver, no walker module is edited here. OUT: writing any back-pointer into the companion repository or the target (OQ-01); a custom (non-sibling) `--companion-dir` resolved from an unrelated cwd for a project not attached via `aw project attach` (a documented limit, pinned by a test); the walkers themselves and the AW_HOME branch (owned by `ki6t17`); the companion installer's placement of `config/project.json` (F-06, not a walker defect).
- Scope-Paths: agent_workflows/project_context.py, tests/test_companion_record_owner_root.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md, CHANGELOG.md
- Item-Dependencies: executed:ki6t17
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: miq4mi
- Set: cleantgt
- Order: 9
- Highest E allocated: 05
- Author: opencode
- Id: diya77

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog miq4mi at HEAD 36c9f21ff; measured the walkers on a real public-target-private-companion install.

## Goal

Make a record that lives under a companion records root resolve to its owning target repository through the same verified resolver `ki6t17` introduces, so companion-backed projects get correct dependency resolution, history sidecars, id6 collision sets, and rename hints, with byte-identical behavior for in-tree and AW_HOME records.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure after ki6t17

- [ ] E-01 Re-measure the companion misroute at the executing HEAD, with `ki6t17` executed.
  - Depends on: none
  - Expected outcome: one pasted transcript from a scratch tree under `/tmp` (NOT inside this checkout: F-07 of `ki6t17` shows an AW_HOME or companion inside a checkout lets the climb land on that checkout) with `HOME`, `AW_HOME=$HOME/.aw`, `XDG_CONFIG_HOME`, `AW_NO_REEXEC=1`, `AW_IPD_AUTHOR=probe`, `PYTHONPATH=<workspace>` and `GIT_CEILING_DIRECTORIES=<scratch>` exported: `git init` a target `<S>/t` with one empty commit, `python3 -m agent_workflows install . --preset public-target-private-companion -y --no-interactive`, then from the target: (a) `aw ipd scaffold --kind child --set probe --order 1|2 --priority low --work-kind chore --apply` (writes under `<S>/t.aw/records/plans/pending/`), set both `to-review`, point plan 2's `- Item-Dependencies:` at `executed:<plan-1-id6>`, run `aw ipd lint --phase pre-execution <plan-2>` and show `check.ipd-dependency-dangling ... no ipd artifact has id6 <plan-1-id6>`, and with `executed:zzzzzz` show it too (falsifiability); (b) `aw specs new --title "Probe spec" --slug probe-spec --apply`, `aw specs note <spec> --message hello`, then `find <S> -name history.jsonl`, showing whether the sidecar lands at `<S>/t.aw/records/history.jsonl` (correct) or elsewhere; (c) a `python3 -c` probe printing `project_context.record_owner_root`, `artifact_core.repo_root_of`, `specs._repo_root_of`, `specs._spec_repo_root`, `status_set._repo_root_of`, `record_placement._find_repo_root` for plan 1, once from the target cwd and once from `<S>/else`, and `check_engine._identity_rename_hint("plans", <id6>, "Id", False, <plan-1>)`; (d) the same probe after `git -C <S>/t.aw init` (a real private companion is a git repo; F-03); (e) the pre-edit bare `python3 -m pytest` summary line with sorted failing names (the E-05 baseline), and the warm `python3 -m agent_workflows ipd lint --all --agent` wall time in this repository (run twice, report the second). If `ki6t17`'s execution already fixed any of (a)..(d), record it and narrow E-03 rather than re-implementing.
  - Execution state: pending

### Task group 2: tests, then the resolver branch

- [ ] E-02 Write `tests/test_companion_record_owner_root.py` FIRST and show it RED against the unmodified resolver.
  - Depends on: E-01
  - Expected outcome: a behavioral test module (no `inspect`, `ast`, or regex over `.py` sources; every tree under `tmp_path`; `HOME`, `AW_HOME`, `XDG_CONFIG_HOME` isolated via `monkeypatch` for in-process calls and an explicit env for subprocesses, reusing the subprocess-install shape of `tests/test_clean_target_config_home.py`; `GIT_CEILING_DIRECTORIES` set to `tmp_path`). Fixtures: (C1) a real `public-target-private-companion` install of `tmp_path/t` by subprocess `aw install`, giving the default sibling companion `tmp_path/t.aw`, with one scaffolded child plan and, where named, `git init` of the companion; (C2) the same install with `--companion-dir tmp_path/priv/records-repo` (a non-sibling companion); (C3) a repository-backed install. Tests:
    1. `test_sibling_companion_record_maps_to_target_from_target_cwd` (C1, cwd = target): `project_context.record_owner_root(<plan>)` equals the target root.
    2. `test_sibling_companion_record_maps_from_unrelated_cwd` (C1, cwd = `tmp_path/else`): same answer, via the sibling convention.
    3. `test_sibling_companion_with_git_maps_to_target` (C1 after `git init` of the companion, cwd elsewhere): same answer (the climb alone would stop at the companion root).
    4. `test_custom_companion_dir_from_target_cwd` (C2, cwd = target): equals the target; with cwd elsewhere and no registry entry it returns `None` (documented limit, OQ-01); after `project_registry.register_or_update_project(<target>, <aw_home>, project_id=<derived id>, records_backend="companion")` it equals the target from cwd elsewhere.
    5. `test_companion_candidate_rejected_without_records_match`: (a) a directory `tmp_path/u.aw/records/plans/pending/x.ipd.md` whose sibling `tmp_path/u` is a plain git repo with no agent-workflows install returns `None`; (b) C1 after `mv t t2` from an unrelated cwd returns `None` and does not raise; (c) a C3 repository whose tree happens to contain `docs/records/x.md` returns `None` for that file (a `records` dir that is not the candidate's records root is refused).
    6. `test_in_tree_and_home_records_unchanged`: for a C3 in-tree plan the resolver returns `None` (the walkers keep their climb), and for a `ki6t17` AW_HOME record it returns exactly what `ki6t17`'s branch returns (no regression of the AW_HOME branch).
    7. `test_walkers_return_target_for_companion_record` (C1 with companion git, cwd elsewhere): `artifact_core.repo_root_of`, `specs._repo_root_of`, `specs._spec_repo_root`, `status_set._repo_root_of`, `record_placement._find_repo_root` each equal the target; `check_engine._identity_rename_hint("plans", <id6>, "Id", False, <plan>)` returns `aw rename plans <id6> --to-id6 --apply`.
    8. `test_ipd_lint_resolves_companion_sibling_dependency` (C1, subprocess from the target): the E-01(a) pair prints no `check.ipd-dependency-dangling`; `executed:zzzzzz` DOES print it.
    9. `test_specs_note_history_lands_in_companion_records_root` (C1, subprocess from the target): `aw specs new --apply` then `aw specs note <spec> --message x` exits 0, `tmp_path/t.aw/records/history.jsonl` contains the spec id6, and no other `history.jsonl` exists under `tmp_path` (in particular none under `t.aw/records/specs/`).
    RED proof: run `python3 -m pytest -o addopts="" -q tests/test_companion_record_owner_root.py` BEFORE E-03 and paste the failing output (expected: items 1..4, 7..9 failing on assertions; items 5 and 6 may already pass because the unextended resolver returns `None`, and say so).
  - Execution state: pending

- [ ] E-03 Extend `project_context.record_owner_root` with the companion branch.
  - Depends on: E-02
  - Expected outcome: in `agent_workflows/project_context.py`, after `ki6t17`'s AW_HOME branch returns `None`, a companion branch: FAST PATH (no I/O) returns `None` unless the path's parts contain a `records` component whose immediately preceding component is neither `.aw` nor `.agents`, so every in-tree record in this repository pays only that string check. Otherwise, candidates in order: (1) `find_project_root(Path.cwd())`, then `checkout_main_root` of it when it is a linked worktree; (2) for the nearest ancestor named `records` whose parent directory name ends in `.aw` and is longer than `.aw`, the sibling directory with that suffix stripped, when it exists (the installer's default `f"{repo_abs}.aw"`, `project_context.resolve_project_context` records-root rule); (3) each existing-directory `target_paths` entry of every entry in `project_registry.load_registry(project_registry.get_registry_path(aw_home))` whose `records_backend` is `companion`. A candidate is ACCEPTED only when its resolved records backend is `companion` and `path` lies under `_canonical_path(project_records_dir(candidate, aw_home=aw_home))`. Returns the first accepted candidate, else `None`. Same totality rule as the AW_HOME branch (`OSError`, `ValueError`, `RuntimeError`, `ProjectContextError`, JSON errors yield `None`); no writes, no subprocesses, no network. The docstring's companion-limit sentence (`miq4mi`) is replaced by a description of the companion branch, its three candidates, its verification rule, and the custom-companion-dir limit.
  - Execution state: pending

### Task group 3: contract, docs, and validation

- [ ] E-04 Amend the placement spec and add a CHANGELOG line.
  - Depends on: E-03
  - Expected outcome: `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` gains one `AMENDED <date> (cleantgt diya77, backlog miq4mi):` paragraph directly after `ki6t17`'s amendment, stating: a record path under a companion records root maps to its owning repository through the same `project_context.record_owner_root`; candidates are cwd, the default sibling `<repo>.aw` convention, and `registry.json` `target_paths`; every candidate is accepted only when the records-root accessor maps it to a companion records root containing the path; nothing is written into the companion or the target; a custom companion directory resolves from an unrelated cwd only once the project is attached. `CHANGELOG.md` gains one `- Fixed:` line under `## 2.0.0 (pending)` saying that commands acting on a record stored in a companion records repository now find the owning repository, so plan dependency checks, spec history, id6 collision checks, and rename hints work there. No em or en dashes in the CHANGELOG line (user-facing prose, AGENTS.md).
  - Execution state: pending

- [ ] E-05 Run the targeted suites, the end-to-end re-measure, docs and leak checks, the timing check, and the bare suite.
  - Depends on: E-04
  - Expected outcome: (1) `python3 -m pytest -o addopts="" -q tests/test_companion_record_owner_root.py tests/test_record_owner_root.py tests/test_project_context.py tests/test_project_registry.py tests/test_record_placement.py tests/test_ipd_lint.py tests/test_check_engine.py tests/test_clean_target_config_home.py` passes; (2) the E-01 transcript re-run shows (a) no dangling diagnostic for the real sibling and the diagnostic for `zzzzzz`, (b) the sidecar at `<S>/t.aw/records/history.jsonl` and no other `history.jsonl`, (c) and (d) every walker printing the target root from both cwds and the hint present; (3) `python3 -m agent_workflows sanitize --agent` reports `"outcome": "clean"`; (4) a dash scan of the added CHANGELOG line finds no `\u2014`/`\u2013`; (5) bare `python3 -m pytest` passes with zero new failures compared by name against the E-01 baseline; (6) warm `ipd lint --all --agent` in this repository shows no slowdown over 5% against E-01's time (the fast path keeps in-tree records off the companion branch); a larger slowdown is investigated before claiming done.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The records location is decided by ONE accessor, `project_context.project_records_dir` (plan `kfnfji`); `ki6t17` adds its inverse `record_owner_root` with a verify-against-the-accessor rule, and this plan extends that same function rather than adding a second resolver.
- `project_context.resolve_project_context` computes a companion records root as `companion_dir or local-binding companion_dir or f"{repo_abs}.aw"` joined with `records`; that default is what makes the sibling candidate sound.
- `registry.json` is written only by `aw project attach|move` (`ki6t17` F-06, OQ-01); this plan reads it and does not change who writes it.
- Tests assert observable behavior (return values, exit codes, files written, printed diagnostics), never source structure (AGENTS.md, GUIDING_PRINCIPLES P16).
- Narrowed runs clear defaults with `-o addopts=""`; the routine gate is bare `python3 -m pytest` (AGENTS.md repo-local contract).
- A spec edit is declared in `- Scope-Paths:` and justified in the spec-sync section (AGENTS.md, "A PLAN MAY AMEND A SPEC").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Under a companion backend, the Group A walkers return the record's own directory, its parent, or cwd, never the target. | At `36c9f21ff`, scratch `<S>` under `/tmp` with `HOME=<S>/h`, `AW_HOME=<S>/h/.aw`, `GIT_CEILING_DIRECTORIES=<S>`, after `python3 -m agent_workflows install . --preset public-target-private-companion -y --no-interactive` in `<S>/t` and `aw ipd scaffold --kind child --set probe --order 1 ... --apply` writing `<S>/t.aw/records/plans/pending/20261016-probe-01-pwxqc4-probe-1.ipd.md`: from cwd `<S>/t`, `artifact_core.repo_root_of` printed the plan file itself, `specs._repo_root_of` and `record_placement._find_repo_root` printed `<S>/t.aw/records/plans/pending`, `specs._spec_repo_root` printed `.`, and `status_set._repo_root_of` printed `<S>/t` (its cwd fallback, correct only by accident: from cwd `<S>/else` it printed `<S>/else`). `project_context.project_records_dir(<S>/t)` printed `<S>/t.aw/records`. |
| F-02 | `aw ipd lint` reports a FALSE dangling dependency for an existing sibling plan in companion records. | Same tree, plans `pwxqc4` and `2kkudw` set `to-review`, `2kkudw` given `- Item-Dependencies: executed:pwxqc4`: `aw ipd lint --phase pre-execution <2kkudw>` printed `! check.ipd-dependency-dangling: executed:pwxqc4: no ipd artifact has id6 pwxqc4`; `executed:zzzzzz` printed the same diagnostic for `zzzzzz`. |
| F-03 | A companion that is a git repository (the normal private-companion case) stops every climb at the companion root. | Same tree after `git -C <S>/t.aw init`: `artifact_core.repo_root_of`, `record_placement._find_repo_root`, and `status_set._repo_root_of` all printed `<S>/t.aw`, the companion, not the target. |
| F-04 | `aw specs note` writes a stray history sidecar INSIDE the companion records tree. | Same tree, before the companion `git init`: `aw specs new --title "Probe spec" --slug probe-spec --apply` wrote `<S>/t.aw/records/specs/draft/20261016-raaeec-01-raaeec-probe-spec.spec.md`; `aw specs note <spec> --message hello` then created `<S>/t.aw/records/specs/draft/.aw/records/history.jsonl` (a new `.aw` directory inside the records tree), because `specs._repo_root_of` fell back to the spec's parent directory and `project_records_dir` of that directory is its own `.aw/records`. |
| F-05 | `_identity_rename_hint` suggests nothing for a companion record. | Same tree, in-process: `check_engine._identity_rename_hint("plans", "pwxqc4", "Id", False, <plan>)` returned `''` (the in-tree analogue returns `aw rename plans <id6> --to-id6 --apply`, `ki6t17` F-05). |
| F-06 | The companion install has no back-pointer from companion to target, so the resolver needs the sibling convention or the registry. | Same tree: `<S>/t.aw` held only `records/`; `<S>/t/.aw/config/local.json` read `"companion_dir": null, "common_dir": null`; `project.json` (`records_backend: companion`) was written into the target, untracked; no `registry.json` existed under `<S>/h/.aw`. The default companion path is `f"{repo_abs}.aw"` in `project_context.resolve_project_context`. Where `project.json` lives is an installer placement question, not a walker defect, and is left out. |
| F-07 | `aw ipd coverage` from the target root does not misroute under a companion backend. | Same tree: `aw ipd coverage pwxqc4` printed `error: no orchestrator plans selected among targets`, the correct per-plan outcome for a child plan, because `orchestrator_readiness.run_coverage` climbs from cwd (which reaches the target's in-tree `.aw`), not from the record. No coverage change is needed. |
| F-08 | `aw ipd lint --all` in the companion target found the companion plans. | Same tree: `python3 -m agent_workflows ipd lint --all --agent` from `<S>/t` reported `outcome: clean` with a diagnostic located at `records/plans/pending/20261016-probe-01-pwxqc4-probe-1.ipd.md`, so plan discovery already goes through `project_records_dir`; only the per-record root walk misroutes. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the misroute at the executing HEAD with `ki6t17` executed.
2. E-02 writes the behavioral tests first and records them RED.
3. E-03 extends `project_context.record_owner_root` with a verified companion branch.
4. E-04 amends the placement spec and the CHANGELOG.
5. E-05 validates (targeted suites, end-to-end re-measure, sanitize, timing, bare suite).

## Deferred / out of scope (with reason)

- A custom (non-sibling) companion directory resolved from an unrelated cwd for a project that was never attached returns `None` and keeps the climb (OQ-01); pinned by E-02 item 4, no carrier needed unless a user reports it.
  - Carrier-Declined: documented limit pinned by a test; writing a back-pointer into a tracked companion repository is a larger contract change than this low-priority followup warrants.
- Where the companion installer writes `config/project.json` (F-06) is a placement question unrelated to record-to-root walking.
  - Carrier-Declined: not a defect measured here; the measured install worked end to end for discovery (F-08).

## Scope check

- Over-scope: none. `project_context.py` holds the resolver being extended, the test module is new, the placement spec owns the records-root contract the resolver inverts, and the CHANGELOG records the user-visible fix.
- Under-scope: none for the backlog item. Every walker reaches the resolver through `ki6t17`'s routing (hence `executed:ki6t17`), so extending the resolver fixes F-01..F-05 without touching walker modules; `run_coverage` and lint discovery were measured correct (F-07, F-08). If E-01 shows a walker that `ki6t17` did not route, that edit is made with `--scope-reason` and recorded.

## Required tests / validation

- `tests/test_companion_record_owner_root.py` (E-02), RED before E-03 and GREEN after it.
- `tests/test_record_owner_root.py` (from `ki6t17`) still green, the touched-area suites, the end-to-end re-measure, `aw sanitize --agent`, the dash scan, the timing check, and bare `python3 -m pytest` (E-05).

## Spec / documentation sync

- `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` gains a dated `AMENDED` paragraph (E-04). WHY: that spec owns where records live for each backend, including the companion default `<repo>.aw/records`, and `ki6t17` amends it to state the inverse mapping for AW_HOME records; extending the inverse to companion roots, and stating its candidates and its limit, is a contract other plans and reviewers read, so it belongs beside `ki6t17`'s paragraph. It changes no existing rule.
- `CHANGELOG.md` gains one `- Fixed:` line (E-04).
- No `docs/` page describes record-to-root resolution, so no `docs/` change.

## Open questions

### OQ-01: Should a companion install write a back-pointer so a custom companion directory resolves from any cwd?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: no. The companion is a separate, usually tracked, private repository (`public-target-private-companion`), so a pointer written into it is a new tracked file in someone else's history, and the target is public, so a pointer there leaks the private path. The default sibling layout (`f"{repo_abs}.aw"`, `project_context.resolve_project_context`) is resolvable with no pointer at all, and an attached project resolves through `registry.json`, which this plan reads. The residual case (custom companion dir, unrelated cwd, never attached) degrades to today's climb, and E-02 item 4 pins it. Reversible.
- Carrier-Declined: resolved from repository evidence; the residual limit is pinned by a test.

### OQ-02: Can the sibling candidate misattribute a record to an unrelated directory that merely happens to be named `<X>` beside `<X>.aw`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED by construction: a candidate is accepted only when its own resolved records backend is `companion` and `project_records_dir(candidate)` contains the record, so an unrelated `<X>` (no install, or a different backend, or a custom companion elsewhere) is refused. E-02 item 5 exercises both an uninstalled sibling and a moved target. Reversible.
- Carrier-Declined: resolved by construction and covered by E-02 item 5.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha, `ki6t17`'s `- Status:` line showing `executed`, and the full E-01 transcript (code paths: `aw install`, `ipd_lint.lint_file`, `specs._sidecar_append`, `project_context.record_owner_root`, the five Group A walkers, `check_engine._identity_rename_hint`): (a) both dangling diagnostic lines; (b) the `find ... history.jsonl` output; (c) and (d) the probe's printed roots from both cwds and the hint; (e) the bare-suite baseline summary with sorted failing names and the warm `ipd lint --all` timing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the pre-E-03 RED output of `python3 -m pytest -o addopts="" -q tests/test_companion_record_owner_root.py` and `git diff --stat` showing only the new test file changed at that point.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` hunk extending `record_owner_root` and the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_companion_record_owner_root.py tests/test_record_owner_root.py`, showing all nine companion tests and every `ki6t17` test passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `git diff` for the spec and `CHANGELOG.md`, and the dash-scan output for the CHANGELOG addition showing zero `\u2014`/`\u2013`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste (1) the targeted pytest summary line; (2) the re-run E-01 transcript lines (a)..(d) (code paths as V-01) showing the fixed behavior; (3) the `aw sanitize --agent` record; (4) the dash-scan result; (5) the bare `python3 -m pytest` summary line and the by-name comparison against the E-01 baseline; (6) the before and after warm `ipd lint --all` wall times.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit diya77 -- <paths>` (never `git add -A`), never push, and paste actual runner output for every test claim. Scratch installs live under `/tmp` and are never committed.

DEPENDENCY. `ki6t17` must be executed first: it creates `record_owner_root` and routes every walker through it. This plan extends that function only.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all five `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
