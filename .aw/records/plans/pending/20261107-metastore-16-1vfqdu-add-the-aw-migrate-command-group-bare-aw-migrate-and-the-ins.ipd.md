# IPD: Add the aw migrate command group, bare aw migrate, and the install pending-migration prompt

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` 5.1 asks for one `aw migrate <name>` family and for `aw install` to offer a pending migration. Today the only migration verbs are the top-level `aw migrate-layout` and `aw specs migrate` (`cli.build_parser`); `aw install`'s `-y/--yes` is documented as "Skip preflight confirmations." The maintainer added on 2026-11-07 that a bare `aw migrate` runs every pending step in order (layout first when a legacy `.agents/` tree exists, then metadata), dry-run by default. Plan `dcerjg` owned the CLI work; it was split 2026-11-07 per the maintainer's step-complexity rule.
- Scope: Add the `aw migrate` group with `metadata` and `layout` leaves (`dcerjg` E-02), the bare-`aw migrate` runner over every pending step (new, maintainer requirement), and the `aw install`/`aw setup` pending-migration question and `--migrate` (`dcerjg` E-03), with their tests (a subset of `dcerjg` E-14). EXCLUDES: the chain, stamp, preflight and journal (`vxevph`); every `m0001` step body (`dky26u`, `ghhzb6`, `hpedmn`, `dcerjg`); the `--describe-*` options (`odeo9z`).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/completion.py, agent_workflows/engine.py, agent_workflows/migrations/chain.py, tests/test_migrate_cli.py, tests/test_install_migrate_prompt.py, tests/test_completion.py, .aw/records/plans/pending/20261107-metastore-16-1vfqdu-add-the-aw-migrate-command-group-bare-aw-migrate-and-the-ins.ipd.md
- Item-Dependencies: executed:tve77h, executed:vxevph
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 16
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1vfqdu

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 review per research nj8zdp; within the guidance, no items moved; V-01 and V-04 evidence now name each module's node ids beside the summary lines.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from dcerjg per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

One `aw migrate` family exists: `aw migrate layout`, `aw migrate metadata`, and a bare `aw migrate` that previews or performs every pending step in order; `aw install` and `aw setup` report a pending migration and run it only on a terminal yes or `--migrate`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the command group and bare aw migrate

- [ ] E-01 Add the `aw migrate` command group in `cli.build_parser` with leaves `metadata` (dry run by default; `--apply`, `--force`, `--force-worktree`, `--agent`, `--json`) and `layout` (the same arguments and dispatch as `aw migrate-layout`, which stays as an alias printing no new warning). Declare both leaves in `command_surface` (`metadata` as `command_class="mutation"`, `mutation_gate="confirmation"`, `human_recipe="preview"`, mirroring the `migrate-layout` declaration) and add the `layout` positional choices to `completion` the way `migrate-layout action` is handled.
  - Depends on: none
  - Expected outcome: `aw migrate --help` lists `metadata` and `layout`; `aw migrate layout status` and `aw migrate-layout status` produce identical output; `tests/test_command_surface_declarations.py` reports no undeclared leaf.
  - Execution state: pending

- [ ] E-02 Make a bare `aw migrate` (no subcommand) run every PENDING migration step in order, as one more leaf-free entry point of the group E-01 creates (maintainer requirement 2026-11-07). The order is fixed: first the layout stage when the repository holds a legacy `.agents/` tree (detected the way `aw migrate layout` already detects it: `layout_inventory._default_roots(repo)` returns the `agents` root, or `engine.detect_split_brain_layout(repo)` is True), then the metadata stage when `chain.MIGRATIONS` reports `m0001` pending (`Migration.is_pending(repo)`). It is a DRY RUN by default: it prints, per step, the step name, whether it is pending, and that step's own dry-run report (the layout `plan` view and the `aw migrate metadata` dry run), and writes nothing outside the gitignored journal directory. `--apply` performs the pending steps in the same order, each through its own existing entry point (`MigrationManager.execute_migration` for layout, `m0001_metadata_v2.run(..., apply=True)` for metadata), and stops at the first step that refuses or fails, naming it, without starting the next. `--force` and `--force-worktree` pass through to the metadata step only, exactly as `aw migrate metadata` takes them; `--agent` and `--json` emit one record per step. A repository with nothing pending prints "nothing to migrate" and exits 0. Because the group root now takes action, declare the bare form in `command_surface` (`command_class="mutation"`, `mutation_gate="confirmation"`, `human_recipe="preview"`, as E-01 declares `metadata`) and make the parser dispatch the bare group to this runner rather than to `_show_family_help`.
  - Depends on: E-01
  - Expected outcome: in `tmp_path` repositories: a repository with a legacy `.agents/` tree and legacy records lists the layout step then the metadata step and changes no tracked byte; the same with `--apply` runs the layout step, then the metadata step, in that order; a repository with only `.aw/` legacy records lists only the metadata step; a fully migrated repository prints "nothing to migrate"; when the layout step refuses under `--apply`, the metadata step does not start.
  - Execution state: pending

### Task group 2: the install prompt

- [ ] E-03 Add the pending-migration step to `aw install` and `aw setup` (`cli._run_install`, `cli._install_all`, `cli._run_setup`, and the `engine` install path they call): after the bundle install, if the repository has NO legacy records and no stamp, write `metadata_schema: CURRENT_METADATA_SCHEMA` and report nothing pending (5.3); otherwise list each pending migration and, only when stdin and stdout are a terminal, ask "Run migration 0001 metadata-v2 now? [y/N]"; with no terminal, print the pending migration and the exact command `aw migrate metadata`. `-y/--yes` never answers this question. Add `--migrate` to `install` and `setup`, which answers yes without a terminal and passes neither `--force` nor `--force-worktree`. A repository with legacy records is never stamped by install.
  - Depends on: E-01
  - Expected outcome: the four AC-28 cases and AC-11 cases (2) and (3) hold in tmp repositories, with every record byte-identical whenever the migration does not run.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add the test modules for E-01 to E-03, moved here from `dcerjg` E-14 (subset: the CLI half of `tests/test_migrations_chain.py` and `tests/test_install_migrate_prompt.py`), all on `tmp_path` fixture repositories built with real `git init`, calling the real `aw` CLI leaves and asserting on outputs, exit codes and file bytes (no source reading): `tests/test_migrate_cli.py` (E-01: `aw migrate --help`, `aw migrate layout status` equal to `aw migrate-layout status`; E-02: the five bare-`aw migrate` cases of its Expected outcome); `tests/test_install_migrate_prompt.py` (AC-28 with a pseudo-terminal for the yes and no cases, and AC-11 cases 2 and 3 with `CURRENT_METADATA_SCHEMA` patched to 2). Update `tests/test_completion.py`'s positional-choices expectation for the new `migrate layout action` choices. Mark each `core`; any module whose slowest test exceeds 2 s in `--durations=10` is marked `slow` instead and named in V-04.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: both modules and `tests/test_command_surface_declarations.py` and `tests/test_completion.py` pass under `python3 -m pytest -o addopts="" -n auto <modules>`; the bare core gate stays inside its 30 s budget.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Transactional migrations reuse `layout_migration.MigrationManager` (`_acquire_lock`, `_save_transaction`, `_load_transaction`, `resume_migration`, `rollback_migration`); spec 5.1 forbids new journal or lock components (carried from `dcerjg` Step 0).
- Path roots come from `project_context.resolve_project_context` (`config_project`, `state_durable`, `records`), never `<repo>/.aw/...` literals (spec 4.5, 5.1).
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); new modules set `pytestmark = pytest.mark.core` unless the `--durations=10` rule of `dcerjg` E-14 moves one to `slow`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- Every CLI leaf must be declared in `command_surface` (`command_surface.find_undeclared_leaves`, enforced by `tests/test_command_surface_declarations.py`); `migrate-layout`'s declaration is the template for a mutation verb with a confirmation gate (carried from `dcerjg` Step 0).
- A family root is not a leaf (`command_surface.discover_parser_leaves` reports only parsers without subparsers), and bare-invokable roots such as `aw runs` and `aw ipd` are deliberately undeclared; bare `aw migrate` is different because it MUTATES under `--apply`, so E-02 declares it and the plan's V-04 runs `tests/test_command_surface_declarations.py` to prove the declaration is accepted.

## Findings

| Id | Evidence (measured 2026-11-07 in this worktree) | Finding |
|---|---|---|
| F-01 | `rg -n "migrate-layout\|migrate_layout" agent_workflows/cli.py agent_workflows/command_surface.py agent_workflows/completion.py \| wc -l`: 29; `rg -n '"migrate-layout"' agent_workflows/cli.py`: parser at `cli.build_parser` (`sub.add_parser("migrate-layout", ...)`), dispatch `if args.command == "migrate-layout"`, help table entry | E-01: 1 group parser, 2 leaves, 2 declarations, 1 completion entry, 1 dispatch: about 7 units. |
| F-02 | `rg -n "def _run_migrate_layout\|def _split_brain_guard" agent_workflows/cli.py`; `rg -n "def detect_split_brain_layout" agent_workflows/engine.py`; `layout_inventory.DEFAULT_ROOTS` lists `("agents", ".agents")` | E-02 reuses the existing layout detection and entry points: 1 runner, 2 step adapters, 1 declaration, 1 dispatch change, 5 behaviors: about 10 units. |
| F-03 | `rg -n "def (_run_install\|_install_all\|_run_setup)\b" agent_workflows/cli.py`: 3; `rg -n "Skip preflight confirmations\|Install without per-repo prompts" agent_workflows/cli.py`: 2; `engine.install_into_repo` is the one engine call | E-03: 3 call sites, 1 engine path, 2 `--migrate` flags, 4 AC-28 behaviors: about 10 units. |
| F-04 | `tests/test_completion.py` asserts `with_choices == ["completion", "migrate-layout", "path"]` | Adding `migrate layout`'s positional choices changes that expectation, so the test file is in scope. |

## Proposed changes (ordered, validatable)

1. E-01: the group and its two leaves.
2. E-02: bare `aw migrate`.
3. E-03: the install prompt and `--migrate`.
4. E-04: tests.

## Deferred / out of scope (with reason)

- The chain, the stamp, the preflight and the journal this CLI calls.
  - Carrier: vxevph
- The `--describe-host`, `--describe-model`, `--describe-limit` and `--no-describe` options on `aw migrate metadata`.
  - Carrier: ya4ee4
- The CHANGELOG line for the family (it names `aw migrate`, `aw migrate layout` and `aw install --migrate`).
  - Carrier: dcerjg

## Scope check

- Over-scope: none. `migrations/chain.py` is touched only if E-02 needs a public `pending_migrations(repo)` helper over `MIGRATIONS`.
- Under-scope: none for `dcerjg` E-02 and E-03, the bare-`aw migrate` requirement, AC-11 cases 2 and 3, and AC-28 cases 1 to 4.

## Required tests / validation

New modules (all `core` unless E-04's duration rule moves one to `slow`): `tests/test_migrate_cli.py`, `tests/test_install_migrate_prompt.py`. Existing: `tests/test_command_surface_declarations.py`, `tests/test_completion.py`, `tests/test_migrate_layout_cli.py`. Gate: bare `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements `4sd62s` 5.1 (naming, install question, `--migrate`). The bare `aw migrate` runner is a maintainer requirement of 2026-11-07 that 5.1's "one `aw migrate <name>` family" admits; user documentation lands with `90iqr1`.

## Open questions

### OQ-06: Does `aw migrate-layout` become `aw migrate layout` (5.1, research `ffi66q`)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `dcerjg` OQ-06 (resolved there): yes, as an added spelling; `aw migrate layout` dispatches to the existing `cli._run_migrate_layout`, and `aw migrate-layout` stays as an alias with unchanged output.

- Note: carried unchanged from `dcerjg` with its id, so item text that cites it still resolves.

### OQ-07: Does bare `aw migrate --apply` run the layout stage that `g5hpbb` later chains into `aw migrate metadata`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, and the two do not conflict. Bare `aw migrate` sequences the two existing entry points; `g5hpbb` E-06 later makes `aw migrate metadata` itself run the layout stage first inside one journal. After `g5hpbb`, the bare runner's layout step finds nothing pending when metadata already ran it, so no step runs twice; E-02's Expected outcome already covers the nothing-pending case.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw migrate --help` output listing `metadata` and `layout`; `diff <(aw migrate layout status) <(aw migrate-layout status)` printing nothing; and `python3 -m pytest -o addopts="" -v tests/test_command_surface_declarations.py tests/test_completion.py` with each module's node ids PASSED and 0 failed, including the declaration check covering the `migrate metadata` and `migrate layout` leaves.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_migrate_cli.py -k bare` with one PASSED test per E-02 case (legacy layout plus legacy records lists layout then metadata with a SHA-256 tree listing equal before and after; `--apply` runs layout then metadata in that order, shown by the per-step records; `.aw/`-only repository lists only metadata; migrated repository prints "nothing to migrate"; a refused layout step leaves the metadata step unstarted); and the `aw migrate --help` usage line showing the group accepts no subcommand plus `--apply`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_install_migrate_prompt.py` with each AC-28 case (terminal no, terminal yes, no terminal, `--yes`, `install all --yes`, `--migrate` with a step-1 condition true) and AC-11 cases 2 and 3 PASSED, each asserting record bytes by SHA-256 before and after.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -n auto tests/test_migrate_cli.py tests/test_install_migrate_prompt.py tests/test_command_surface_declarations.py tests/test_completion.py --durations=10 -rA` PASSED node ids for each of the four modules, the summary with 0 failed and the durations table, naming any module marked `slow`; and the bare `python3 -m pytest` summary line inside the 30 s budget.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: this plan NEVER runs `aw migrate metadata --apply` (or bare `aw migrate --apply`) in this checkout. Every apply is on a `tmp_path` fixture repository. If an apply would touch this checkout's records, stop and report: that is a genuinely unsafe condition, not a scope question.

Honesty rule: run the named test modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 1vfqdu -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 1vfqdu` itself.
