# IPD: Extend the placement-switch planner to companion pairs

- Date: 2026-10-16
- Kind: child
- Concern: Backlog `n9vd2h`: the cfgreloc planner (`placement_switch.plan_placement_switch`, plan `xvlemm` E-01/E-02) returns an empty plan with `blockers=["companion-unsupported"]` whenever either side is `public-target-private-companion`. A companion switch involves a SECOND git repository (the companion, which holds `records/`) and a companion identity (`storage.create_companion_identity`, `storage.write_local_attachment_record`), neither of which the cfgreloc census models. Before an executor can move anything, the planner must compute a frozen, side-effect-free plan for the six companion pairs (companion to and from `private-target`, `completely-clean-target`, `local-only`), naming which git repository owns each source and destination, and every companion-specific blocker.
- Scope: IN: additive fields on `placement_switch.SwitchItem` (`source_git`, `dest_git` in `target`/`companion`/`None`) and `placement_switch.SwitchPlan` (`companion_dir`, `companion_action` in `attach`/`detach`/`None`, `companion_create`, `config_retrack` in `untrack`/`track`/`None`), a new `direction` value `in-place` and a `retire_side` of `None` for the two pairs whose config directory does not change; replacing the `companion-unsupported` SHORT-CIRCUIT with a fully populated companion census while KEEPING `companion-unsupported` as an ordinary blocker on every companion plan (the interim safety gate; Order 02 `fo08zx` adds an `allow_companion` library opt-in past it and Order 03 `y1e2m9` removes it from the default path, see E-02 and Deferred); companion blockers `companion-not-git`, `companion-dirty`, `companion-unmerged`, `companion-preflight`, `companion-to-companion`; tests. OUT: executing (Order 02 `fo08zx`), CLI and docs (Order 03 `y1e2m9`), moving a companion binding between two companion directories (`aw storage move`, `storage.move_companion`).
- Scope-Paths: agent_workflows/placement_switch.py, tests/test_placement_switch_companion_plan.py, tests/test_placement_switch_plan.py
- Item-Dependencies: executed:xvlemm
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: n9vd2h
- Set: cmpreloc
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: xc8nae
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cmpreloc graduating backlog n9vd2h.

## Goal

`plan_placement_switch` answers, for every switch into or out of `public-target-private-companion`, exactly which files move between the target, the companion and `AW_HOME`, which git repository stages each change, whether the companion is attached or detached, and whether the switch is safe now, with no side effects, so the executor (Order 02) and the CLI preview (Order 03) consume one computed plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Planner

- [ ] E-01 Companion census in `agent_workflows/placement_switch.py`. Add the additive fields named in Scope with defaults that keep every cfgreloc plan byte-identical in `to_dict()` apart from the new keys (`source_git`/`dest_git` default `"target"` for in-tree paths and `None` for `AW_HOME` paths, computed for cfgreloc items too so Order 02 has one staging rule). Remove the `companion-unsupported` short-circuit (the early return with no items) and, when exactly one side is `public-target-private-companion`, build the plan from the physical roots `project_context.resolve_project_context` resolves for each side (old: stored policy; new: `new_policy` including `companion_dir`, defaulting as the resolver does to `f"{repo_abs}.aw"`), NOT from the placement labels: the companion preset's labels say `config_project: companion-tracked` while the resolver places config at `<repo>/.aw/config/project.json` and durable state at `<repo>/.aw/state/durable` (F-01), and readers follow the resolver. Per pair:
  (a) `private-target` -> companion (`direction="in-place"`, `companion_action="attach"`, `retire_side=None`, `config_retrack="untrack"`): `config_project` one `rewrite` item in place (same path); `config_local` `rewrite` adding `companion_dir`; every file under `<repo>/.aw/records` -> `move` to `<companion>/records/<rel>` with `source_git="target"`, `dest_git="companion"` (the `INDEX.json`/`INDEX.md` discard rule from `xvlemm` E-01 unchanged); `state_durable` and `state_runtime` not items (same directory on both sides, F-01).
  (b) companion -> `private-target` (`in-place`, `detach`, `retire_side=None`, `config_retrack="track"`): mirror of (a), records from `<companion>/records` to `<repo>/.aw/records`, `source_git="companion"`, `dest_git="target"`; `config_local` `rewrite` dropping `companion_dir`; the attachment record `<repo>/.aw/state/durable/companion_attachment.json` a `discard` item.
  (c) companion -> `completely-clean-target`/`local-only` (`direction="to-home"`, `detach`, `retire_side="target"`): config and durable install history exactly as the cfgreloc `to-home` census, records from `<companion>/records` to `<AW_HOME>/projects/<id>/records` with `source_git="companion"`, `dest_git=None`, attachment record `discard`.
  (d) `completely-clean-target`/`local-only` -> companion (`direction="to-target"`, `attach`, `retire_side="home"`): config and durable history exactly as the cfgreloc `to-target` census, records from the home records root to `<companion>/records` with `dest_git="companion"`.
  `config_retrack` is `None` for (c) and (d): in (c) the old in-tree `project.json` is removed by the cfgreloc rule keyed on its `tracked` flag (untracked after a fresh companion install, F-02), and in (d) the new in-tree `project.json` is a `rewrite` destination that must end untracked, as a fresh companion install leaves it (F-02); the planner records `config_retrack=None` and the `config_project` item's `dest_git=None` (not staged), so Order 02, which stages by `dest_git`, never stages it. Both sides companion with the SAME canonical `companion_dir` stays `not-a-placement-switch` (the `ppu39q` label branch sees equal labels and the path branch equal dirs). ORDERING: the `companion-to-companion` check (E-02) runs BEFORE the `not-a-placement-switch` short-circuit, because `install_wizard.config_placement_switch` returns `None` for two companion policies (equal labels, equal in-tree config dir), so a check placed after it is unreachable.
  Target dirty check on a companion SOURCE (pairs (b), (c)): the `xvlemm` `dirty-aw-tree` blocker (`git status --porcelain -- .aw` non-empty) fires on every fresh companion install, because that install leaves `?? .aw/config/project.json` untracked by design (F-02, F-07). For an old side of `public-target-private-companion`, exclude EXACTLY that one untracked entry (`?? .aw/config/project.json`, or `?? .aw/config/` when it is the only untracked path under that directory) from `dirty-aw-tree`; every other entry still blocks.
  Set `companion_create=True` when the companion directory does not exist (Order 02 creates it and runs `git init`, mirroring `cli._run_install`'s "if getattr(policy, \"create_companion\", False) or not comp_p.exists():"). Record `tracked` per item from the SOURCE repository (`git ls-files -z` in the target or in the companion, whichever is `source_git`). Every git subprocess, in either repository, runs with `GIT_OPTIONAL_LOCKS=0` and `-c core.fsmonitor=false` (`xvlemm` F-05).
  - Depends on: none
  - Expected outcome: for each of the six pairs the plan names the right direction, companion action, retire side, and per-item source/destination repository; a cfgreloc (non-companion) plan is unchanged except for the new keys.
  - Execution state: pending

- [ ] E-02 Companion blockers and warnings, each a stable id plus a human message, computed without writing: `companion-unsupported` KEPT on every plan where exactly one side is `public-target-private-companion` (message names backlog `n9vd2h` and that the executor does not yet support companion switches), now beside a fully populated census instead of an empty one. It is the interim safety gate: once this plan executes, the cfgreloc executor (`6u755v`, which refuses any plan with a blocker) and the `ozr356` `--relocate` path would otherwise run a companion plan with no attach, no detach and no companion staging, and `ozr356` E-05 case (7) asserts a companion `--relocate --dry-run` names `companion-unsupported`, so removing it here would break that test in the bare suite whenever `ozr356` executed first. Order 02 (`fo08zx` E-06) adds a keyword-only `allow_companion=True` opt-in past it for library callers and its own tests; Order 03 (`y1e2m9`) removes it from the default path together with the CLI gating that makes that safe (amended at the `fo08zx` review, PR-001). `companion-to-companion` (both sides companion with different `companion_dir`; message names `aw storage move`), `companion-not-git` (companion directory exists and is not the TOP of its own repository: `git -C <companion> rev-parse --show-toplevel` fails or its canonical path differs from the canonical companion dir; a bare `rev-parse --git-dir` is NOT enough, because it succeeds for a plain directory nested inside some other repository and reports that parent's `.git`, F-08, so the switch would stage records into the wrong repository; the switch will not `git init` a directory the user already owns), `companion-dirty` (`git status --porcelain` in the companion non-empty; message names the remedy, commit or clean the companion first, since a fresh companion install leaves it uncommitted, F-04), `companion-unmerged` (any `U` entry there), `companion-preflight` (for `attach` only: `storage.validate_companion_preflight(repo, companion_dir, backend="companion", aw_home=aw_home)` raises `StorageSecurityError` or `IdentityConflictError`; the message carries the exception text; called WHETHER OR NOT the companion directory exists, because its traversal and nesting checks are pure path logic that must also refuse a not-yet-existing companion inside the target, and it never writes, F-03, F-09), and the generic `destination-not-empty` applied to `<companion>/records/**` for `attach` (a non-empty records tree in the companion that is not hash-identical blocks, so two projects' records are never merged). Warnings: `records-leave-target-history` for (a) with the count of tracked target records (they stay in the public target's git history; the switch cannot rewrite history), `companion-left-in-place` for every `detach` (the companion repository, its `.aw/companion_identity.json` and its `.gitignore` are left on disk, matching `storage.detach_companion` "without deleting companion data"), and `config-becomes-untracked` for (a) (the in-tree `project.json` is untracked by the switch, matching what a fresh companion install leaves, F-02).
  - Depends on: E-01
  - Expected outcome: each blocker is produced by exactly its minimal condition and absent otherwise; a plan with a blocker is still fully populated.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-03 Create `tests/test_placement_switch_companion_plan.py` (`unittest.TestCase`, `pytestmark = pytest.mark.slow`; scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`, `AW_NO_REEXEC=1`, `PYTHONPATH`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*`; one FRESH real `python3 -m agent_workflows install <repo> --preset <p> [--companion-dir <c>] -y --no-interactive` subprocess per test after an `--allow-empty` initial commit, never a `copytree`, `xvlemm` review PR-004). For companion fixtures, `git -C <companion> add -A && git commit` after the install (a fresh install leaves the companion uncommitted, F-04), and commit a user record `records/backlog/open/x.backlog.md` there; for target fixtures commit `.aw/records/backlog/open/x.backlog.md`. Cases: census for each of the six pairs (direction, `companion_action`, `retire_side`, `config_retrack`, the `x.backlog.md` item's source, destination, `source_git`, `dest_git` and `tracked`); `companion_create` true for a nonexistent companion path; each E-02 blocker by its minimal condition (`companion-not-git`: an existing plain directory OUTSIDE any repository, AND a plain directory nested inside an unrelated scratch git repository, F-08; `companion-dirty`: an untracked file in the companion; `destination-not-empty`: an existing `records/backlog/open/y.backlog.md` in the attach target companion; `companion-preflight`: a companion whose `.aw/companion_identity.json` names another `project_id`, AND a NONEXISTENT `--companion-dir` inside the target repo, F-09; `companion-to-companion`: two companion policies with different `companion_dir`, asserted present and `not-a-placement-switch` absent) and absent on the clean fixture, where the blocker list is EXACTLY `["companion-unsupported"]`; `companion-unsupported` present on all six pairs and absent on every cfgreloc pair; the same-`companion_dir` companion request yields `not-a-placement-switch`; on a FRESH companion install (no edits) the pair (b) and (c) plans do NOT carry `dirty-aw-tree` (F-07), while adding one untracked, non-ignored file `<repo>/.aw/stray.txt` makes `dirty-aw-tree` appear; pair (d)'s `config_project` item has `dest_git=None` and `config_retrack is None`; warnings counts; purity: `(path, mtime_ns, size)` snapshot of the target (including `.git/`), the companion (including `.git/`) and `AW_HOME`, before and after `plan_placement_switch`, identical. Mutation proof (temporary, restored, never committed): (M1) set `dest_git="target"` for companion destinations; the pair (a) census assertion must fail. (M2) replace the `show-toplevel` equality check with a bare `rev-parse --git-dir` success check; the nested-plain-directory `companion-not-git` case must fail. Update the one `xvlemm` case in `tests/test_placement_switch_plan.py` that asserts `companion-unsupported` for a `private-target` repo given a `public-target-private-companion` policy: it now asserts the pair (a) census (`direction == "in-place"`, `companion_action == "attach"`, a non-empty item list, `companion-unsupported` still in `blockers`, no `not-a-placement-switch` blocker), so the behavior that case protected (a companion request is recognized as a placement switch, never a same-placement refresh) is kept. Run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_companion_plan.py tests/test_placement_switch_plan.py -v` and bare `python3 -m pytest`.
  - Depends on: E-02
  - Expected outcome: all cases pass, purity snapshots identical, M1 and M2 each fail then pass after restore, and the cfgreloc planner tests still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `placement_switch.py` is created by Set `cfgreloc` (`xvlemm` E-01); this plan extends it and must keep its cfgreloc tests green.
- Planner purity: every git subprocess with `GIT_OPTIONAL_LOCKS=0` (`xvlemm` F-05) and a whole-tree mtime snapshot test.
- Subprocess install fixtures are installed fresh per test (`xvlemm` E-03 copy note).
- Tests exercise behavior, never source text (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE").

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | For `public-target-private-companion` the resolver puts config and durable state IN THE TARGET and only records in the companion, despite the `companion-tracked` labels. | Authoring probe (scratch dirs): after `install --preset public-target-private-companion --companion-dir <s>/comp -y --no-interactive`, `resolve_project_context(...).physical_classes` printed `config_project: /r/.aw/config/project.json`, `state_durable: /r/.aw/state/durable`, `records: /comp/records`; `project_config_dir` printed `/r/.aw/config`. Source: `project_context.resolve_project_context` "elif resolved_delivery_mode == DeliveryMode.TRACKED.value: config_root = ..." and the `RecordsBackend.COMPANION` records branch; `install_wizard.get_preset_defaults` returns `DeliveryMode.TRACKED.value` for the companion preset. |
| F-02 | A fresh companion install leaves the target's `.aw/config/project.json` UNTRACKED (not ignored), while `private-target` tracks it. | Same probe: `git -C r status --porcelain` printed `?? .aw/config/`; `git check-ignore -v .aw/config/project.json` exit `1`; `git ls-files .aw/config` empty. |
| F-03 | `storage.validate_companion_preflight` is read-only and raises typed errors for identity and nesting conflicts. | Its body: `raise StorageSecurityError` for traversal/nesting, `raise IdentityConflictError` when `ident["project_id"] != target_project_id`; it runs `git --no-optional-locks ... status --porcelain` and `git ls-files`, and writes nothing. |
| F-04 | A fresh companion install does not commit in the companion. | Same probe: `git -C comp log` printed "does not have any commits yet"; `git -C comp status --porcelain` printed `?? .aw/`, `?? .gitignore`, `?? records/`. |
| F-05 | The companion's own `.gitignore` ignores only `.aw/config/local.json` and `.aw/state/runtime/`. | `storage.materialize_companion_storage` `ignore_content = ".aw/config/local.json\n.aw/state/runtime/\n"`; probe `cat comp/.gitignore` printed the same two lines. So `records/runs/**`, `records/history.jsonl` and `records/*/untracked/**` are NOT ignored in a companion (Order 02 handles staging). |
| F-06 | The ppu39q detector flags companion pairs by label even when the config dir is unchanged. | Plan `ppu39q` E-02 (b) `reason="label"`; F-06 there: "the companion preset resolves its config writer in-tree". |
| F-07 | The `xvlemm` `dirty-aw-tree` rule fires on every fresh companion install. | Review probe (scratch, fresh `install --preset public-target-private-companion --companion-dir <s>/comp -y --no-interactive` after an `--allow-empty` commit): `GIT_OPTIONAL_LOCKS=0 git -C r status --porcelain -- .aw` printed `?? .aw/config/`; with `-uall`, `?? .aw/config/project.json`. `xvlemm` E-02 defines `dirty-aw-tree` as that command being non-empty. |
| F-08 | `git rev-parse --git-dir` succeeds for a plain directory nested inside another repository. | Review probe: `git init parent; mkdir parent/comp; git -C parent/comp rev-parse --git-dir` printed `<s>/parent/.git`, exit `0`; `--show-toplevel` printed `<s>/parent`, not the companion dir. |
| F-09 | `storage.validate_companion_preflight` refuses a nested companion without the directory existing, and writes nothing. | Review probe: for `<repo>/nested-comp` (absent) it raised `StorageSecurityError ... cannot resolve inside target repo`; for an absent `<s>/newcomp` it returned `valid: True`; a `find -printf '%p %T@ %s'` snapshot of the scratch tree was identical before and after, and `newcomp` was not created. |
| F-10 | A companion switch with no `companion-unsupported` gate would be executable by the cfgreloc executor and CLI before Order 02 ships. | `6u755v` E-03 refuses only "when the plan has any blocker"; `ozr356` E-03 calls `execute_placement_switch` on `--relocate`; `ozr356` E-05 case (7) asserts a companion `--relocate --dry-run` "refuses naming `companion-unsupported`"; neither `ozr356` nor `6u755v` depends on `xc8nae`, so they may execute in either order. |

## Proposed changes (ordered, validatable)

1. Additive plan fields and the six-pair companion census (E-01).
2. Companion blockers and warnings (E-02).
3. Tests with purity snapshots and a mutation proof (E-03).

## Deferred / out of scope (with reason)

- Executing a companion switch, including the `allow_companion` opt-in past the interim `companion-unsupported` blocker this plan keeps (E-02, F-10): Order 02.
  - Carrier: fo08zx
- Removing `companion-unsupported` from the default path, with the CLI gating that makes it safe: Order 03.
  - Carrier: y1e2m9
- CLI reachability, preview text, docs and the spec amendment: Order 03.
  - Carrier: y1e2m9
- Moving a binding between two companion directories: already `aw storage move` (`storage.move_companion`); the planner blocks it with `companion-to-companion` naming that command.
  - Carrier-Declined: deliberate non-goal; an existing verb owns it.

## Scope check

- Over-scope: none; the new fields are additive and the cfgreloc census is untouched apart from the computed `source_git`/`dest_git` values. `tests/test_placement_switch_plan.py` is edited only to retarget the single `companion-unsupported` case this plan makes obsolete.
- Under-scope: none; all six pairs the backlog item names (into or out of the companion preset, from or to each other preset) have a census case and a test.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_companion_plan.py tests/test_placement_switch_plan.py -v` passes, purity included.
- Mutation M1 fails the pair (a) census case and M2 fails the nested `companion-not-git` case, each then passes after restore.
- Bare `python3 -m pytest` passes.

## Spec / documentation sync

N/A: internal module with no user-facing surface; Order 03 (`y1e2m9`) amends spec `20260810-1447-01` Section 8.1 item 3 once the switch is reachable.

## Open questions

### OQ-01: Follow the companion preset's placement labels or the resolver's physical roots?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The resolver's physical roots (F-01). Every reader resolves through `resolve_project_context`/`project_config_dir`, and the cfgreloc invariant is that the reader and the writer agree. Moving config into the companion would make the planner disagree with what a fresh companion install produces and with every reader. Changing where the companion preset puts config is a separate decision outside `n9vd2h`.

### OQ-02: Should the switch create a missing companion repository?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes when the directory does not exist (`companion_create=True`; Order 02 creates it and runs `git init`, and rollback deletes it), because that is what `cli._run_install` already does for a fresh companion install. No when the directory exists but is not a git repository (`companion-not-git` blocker), because initializing a directory the user already owns is not reversible in a way rollback can prove.

### OQ-03: Remove `companion-unsupported` in this plan, or keep it as an interim blocker until the executor supports companion pairs?

- Blocking: no
- Status: resolved
- Owner: plan author (resolved at /plan-review, PR-001)
- Resolution or deferral rationale: Keep it as an ordinary blocker beside the full census (F-10). This plan is read-only and its siblings `6u755v`/`ozr356` do not depend on it, so dropping the blocker here would let the cfgreloc executor run a companion plan with no attach, detach or companion staging, and would break `ozr356` E-05 case (7). Amended at the `fo08zx` review (its PR-001, OQ-03): `fo08zx` E-06 adds an `allow_companion=True` library opt-in, and `y1e2m9` removes the blocker from the default path in the same change that gates `cli._run_install`'s fresh-install attach, because lifting it with executor support alone would open `aw install --relocate` before the CLI is safe.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- agent_workflows/placement_switch.py` showing the removed short-circuit and the new fields; pasted `json.dumps(plan.to_dict(), indent=2)` (first item of each kind) for scratch pairs (a) and (c), produced by `placement_switch.plan_placement_switch`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted per-blocker probe output (blocker id list for each minimal condition, including the nested-plain-directory `companion-not-git` case and the nonexistent-nested `companion-preflight` case, and exactly `["companion-unsupported"]` for the clean fixture of each of the six pairs; a cfgreloc pair without `companion-unsupported`; a fresh companion install's pair (b) plan without `dirty-aw-tree`), produced by `placement_switch.plan_placement_switch`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `-v` runner output of both planner modules with every case PASSED; pasted M1 and M2 failure lines, `git diff --stat` after each restore, and the passing re-runs; pasted bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `xvlemm` is executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never install into this repository or touch the real home. Paste ACTUAL runner output. Mutation proofs are temporary and MUST NOT be committed. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit xc8nae -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize xc8nae` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
