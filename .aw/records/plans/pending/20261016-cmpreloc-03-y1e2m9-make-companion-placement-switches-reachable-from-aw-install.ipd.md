# IPD: Make companion placement switches reachable from aw install and document them

- Date: 2026-10-16
- Kind: child
- Concern: Backlog `n9vd2h`: after Orders 01 (`xc8nae`) and 02 (`fo08zx`) the library can plan and execute a companion placement switch, but `aw install` still refuses it. Plan `ozr356` E-01 deliberately makes the companion refusal NOT suggest `--relocate` and name `n9vd2h` instead ("involves a companion repository and is not supported yet (backlog n9vd2h)"), and its E-05 case (7) asserts that a companion `--relocate --dry-run` refuses naming `companion-unsupported`. Both become false once this Set ships, and spec `20260810-1447-01` Section 8.1 item 3 (written by `ppu39q` E-04) says "companion switches refuse (backlog `n9vd2h`)". Until all three move together, the CLI, its tests and the contract would disagree.
- Scope: IN: in `install_wizard`, the companion branch of the `PlacementSwitchRequired` message becomes the same remedy message as every other pair (names `--relocate` and the `--relocate --dry-run` preview), keeping the substring `Switching config placement`; in `cli._run_install`, passing `--companion-dir` through to `plan_placement_switch`/`execute_placement_switch` for a relocation and refusing a relocation INTO the companion preset when no companion dir resolves; `placement_switch.render_plan` lines for the companion fields (companion dir, attach or detach, create, per-repository staged counts, the three Order 01 warnings); updating the `ozr356` CLI test case (7) to the new behavior; new end-to-end CLI tests; CHANGELOG, README and the spec Section 8.1 item 3 amendment. OUT: `aw storage attach|detach|move|reattach` (unchanged), moving between two companion dirs (Order 01 `companion-to-companion` blocker).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/install_wizard.py, agent_workflows/placement_switch.py, tests/test_placement_switch_cli.py, tests/test_placement_switch_companion_cli.py, CHANGELOG.md, README.md, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: executed:fo08zx, executed:ozr356
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: n9vd2h
- Set: cmpreloc
- Order: 3
- Highest E allocated: 04
- Author: opencode
- Id: y1e2m9

## Workflow history

- 2026-10-16 cross-reference (opencode, from /plan-review of fo08zx PR-001): `xc8nae` keeps `companion-unsupported` as an interim planner blocker and `fo08zx` E-06 adds only a keyword-only `allow_companion=True` library opt-in past it. THIS plan must remove the blocker and the keyword from `placement_switch.plan_placement_switch`/`execute_placement_switch` in the same change as E-01's gating of the fresh-install attach block, update the `xc8nae`/`fo08zx` tests that assert the blocker or pass the keyword (they live in `tests/test_placement_switch_companion_plan.py`, `tests/test_placement_switch_plan.py` and `tests/test_placement_switch_companion_execute.py`, which must be added to `- Scope-Paths:`), and its review should add that step explicitly. Also: `fo08zx` does NOT stage `<companion>/.aw/companion_identity.json` (absolute `git_common_dir_hash`, D92).
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cmpreloc graduating backlog n9vd2h.

## Goal

`aw install <repo> --preset public-target-private-companion --companion-dir <dir> --relocate` (and the reverse, to any other preset) previews with `--dry-run`, performs the switch, recovers with `--relocate-resume`/`--relocate-rollback`, and is documented, with the CLI, its tests and spec Section 8.1 all agreeing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: CLI

- [ ] E-01 Refusal message and companion dir plumbing. In `install_wizard`, delete the companion-specific branch `ozr356` E-01 added to the `PlacementSwitchRequired` message, so a companion pair gets the shared message ("... Preview with --relocate --dry-run, then rerun with --relocate."). In `cli._run_install`'s relocation path (`ozr356` E-02), the `policy` returned by `collect_policy_interactive(..., allow_placement_switch=...)` already carries `companion_dir` from `--companion-dir` or the existing binding (`install_wizard.resolve_policy_noninteractive` "companion = explicit_companion or existing_policy.companion_dir"); confirm at execution HEAD that `plan_placement_switch` receives it through `new_policy`, and if a relocation INTO the companion preset has `policy.companion_dir` empty, `fail` with "a switch to public-target-private-companion needs --companion-dir <path>" and `return 1` before planning (a silent default to `<repo>.aw` would create a repository the user never named). Do NOT run `cli._run_install`'s fresh-install companion attach block ("if getattr(policy, \"companion_dir\", None):") for a relocating repo: the switch (Order 02 E-02) owns attach, and running both would double-attach outside the journal; gate that block on "not relocating" and leave it unchanged otherwise.
  - Depends on: none
  - Expected outcome: a companion refusal names `--relocate`; a relocation into the companion preset without a companion dir refuses before planning; the fresh-install attach path is unchanged for non-relocating installs.
  - Execution state: pending

- [ ] E-02 Preview text. Extend `placement_switch.render_plan` (`ozr356` E-06) with, when `plan.companion_action` is set: the companion directory, "attach" or "detach", "will be created and git-initialized" when `companion_create`, staged counts per repository ("target: <n> staged, companion: <m> staged"), "project.json will be untracked in the target" / "tracked again" for `config_retrack`, and the text of every Order 01 warning (`records-leave-target-history`, `companion-left-in-place`, `config-becomes-untracked`). Words, not only color (spec Section 8 "uses words in addition to color"). No em or en dashes in any rendered string (user-facing).
  - Depends on: E-01
  - Expected outcome: `--relocate --dry-run` for a companion pair prints the companion lines and writes nothing.
  - Execution state: pending

- [ ] E-03 Docs and spec. `CHANGELOG.md` `## 2.0.0 (pending)`: one `- Added:` bullet stating that `aw install --relocate` now also switches into and out of `public-target-private-companion`, moving records between the target, the companion repository and AW home, attaching or detaching the companion, staging changes in each repository without committing, and leaving a detached companion repository in place; and that moving between two companion directories remains `aw storage move`. `README.md` `### Placement Presets and Storage Backends`, in the "Changing presets later" paragraph `ozr356` E-04 adds: one sentence and one example command for the companion case (`--companion-dir` required when switching into it). No em or en dashes in either. Spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 8.1 item 3: replace "companion switches refuse (backlog `n9vd2h`)" with the supported companion pairs (between `public-target-private-companion` and each of `private-target`, `completely-clean-target`, `local-only`), the rule that config and durable state follow the resolver (in the target for the companion preset), that changes are staged in each owning repository and never committed, that detach preserves the companion repository, and that companion-to-companion stays `aw storage move`; add a dated `## Workflow history` note; do not change the spec `- Status:`. If item 3 does not contain the `n9vd2h` sentence at execution HEAD, stop and report (the `ppu39q`/`ozr356` chain is not as planned).
  - Depends on: E-02
  - Expected outcome: CHANGELOG, README and spec describe the shipped behavior; dash check prints 0 for the added user-facing lines; `aw specs check` on the spec conforms.
  - Execution state: pending

### Task group 2: End-to-end tests

- [ ] E-04 Update `tests/test_placement_switch_cli.py` case (7) (`ozr356` E-05): `--preset public-target-private-companion --companion-dir <c> --relocate --dry-run` on a committed `private-target` repo now exits `0` and prints the companion preview, and without `--relocate` the refusal names `--relocate` and does not name `n9vd2h` (the protected behavior, a refusal without opt-in, is kept). Create `tests/test_placement_switch_companion_cli.py` (`pytestmark = pytest.mark.slow`; every case a subprocess `python3 -m agent_workflows install ...` in a scratch dir with `HOME`, `AW_HOME`, `XDG_CONFIG_HOME` inside it, `AW_NO_REEXEC=1`, `PYTHONPATH`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, `timeout=`; fresh install per test). Cases: (1) `private-target` -> companion `--relocate --dry-run -y` with a nonexistent companion path: exit `0`, output names the companion dir, "attach" and "created", target, companion path (absent) and `AW_HOME` unchanged by snapshot; (2) same with `--relocate -y`: exit `0`, `aw context --json` (subprocess) reports `preset: public-target-private-companion` and records under the companion, `x.backlog.md` staged `A` in the companion and `D` in the target, `git rev-list --count HEAD` unchanged in the target and the companion has no commits; (3) `--preset public-target-private-companion --relocate -y` with no `--companion-dir` on a `private-target` repo: exit `1`, message names `--companion-dir`, nothing written; (4) companion -> `local-only --relocate -y` on a committed companion fixture: exit `0`, records under `AW_HOME`, companion directory and `.git` still present, attachment record absent, receipt present; (5) recovery: drive `execute_placement_switch(..., fault_injection="after-attach")` in a subprocess for pair (a), then `install <repo> --preset public-target-private-companion -y` refuses naming `--relocate-resume`, then `--relocate-rollback -y` restores the pre-switch target and leaves no companion directory; (6) a dirty companion (`companion-dirty`) on companion -> `private-target` `--relocate -y`: exit `1` naming `companion-dirty`. Run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_companion_cli.py tests/test_placement_switch_cli.py tests/test_placement_switch_companion_execute.py tests/test_placement_switch_companion_plan.py tests/test_reinstall_preserves_config.py -v`, bare `python3 -m pytest`, `make test-all`, and `aw sanitize --agent`.
  - Depends on: E-03
  - Expected outcome: every case passes; full suites green; sanitizer clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- User-facing prose (CHANGELOG, README, CLI help and messages) carries no em or en dashes (`AGENTS.md` execution contract).
- A plan amending a spec lists it in `- Scope-Paths:` and says why (`AGENTS.md` "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT").
- `make test-all` is the complete gate including `slow` tests.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `ozr356` makes the companion refusal name `n9vd2h` and not `--relocate`, and tests it. | Plan `ozr356` E-01 "there the message must NOT suggest `--relocate` ... (backlog n9vd2h)"; E-05 case (7). |
| F-02 | Spec Section 8.1 item 3 says companion switches refuse. | Plan `ppu39q` E-04 item (3) "companion switches refuse (backlog `n9vd2h`)". |
| F-03 | The fresh-install path attaches a companion whenever the policy carries `companion_dir`. | `cli._run_install` "if getattr(policy, \"companion_dir\", None):" -> `storage.attach_companion(...)`, inside "if not kept_legacy and policy is not None:". |
| F-04 | The non-interactive policy carries the existing companion binding when no flag is passed. | `install_wizard.resolve_policy_noninteractive` "companion = explicit_companion or existing_policy.companion_dir". |
| F-05 | Without a binding the resolver silently defaults the companion to `<repo>.aw`. | `project_context.resolve_project_context` records branch "or f\"{repo_abs}.aw\"". |

## Proposed changes (ordered, validatable)

1. Shared refusal message, companion dir requirement, no double attach (E-01).
2. Companion preview lines (E-02).
3. CHANGELOG, README and spec 8.1 item 3 (E-03).
4. Updated and new end-to-end tests and full gates (E-04).

## Deferred / out of scope (with reason)

- Companion-to-companion moves: `aw storage move` already does this.
  - Carrier-Declined: deliberate non-goal; the planner blocker names the command.
- Interactive wizard prompts specific to relocation (for example asking for a companion dir mid-relocation): the wizard already prompts for a companion dir when the companion preset is picked (`install_wizard.collect_policy_interactive` "Enter companion directory path"), so no new prompt is needed.
  - Carrier-Declined: existing prompt covers it.

## Scope check

- Over-scope: none; the `cli.py`, `install_wizard.py` and `placement_switch.py` edits are the message, the companion-dir guard, the attach gate and the preview; the `tests/test_placement_switch_cli.py` edit retargets one case this Set makes obsolete.
- Under-scope: none; refusal, preview, execute and recovery are each reachable from `aw install` for companion pairs and tested end-to-end.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_companion_cli.py tests/test_placement_switch_cli.py -v` passes.
- All placement-switch modules and `tests/test_reinstall_preserves_config.py` pass together.
- `aw specs check` on the amended spec conforms.
- Bare `python3 -m pytest` and `make test-all` pass; `aw sanitize --agent` exits `0`.

## Spec / documentation sync

`CHANGELOG.md` and `README.md` updated (E-03). Spec edit, declared in `- Scope-Paths:`: `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 8.1 item 3. WHY: that item states companion switches refuse; once this plan ships they are supported, so the contract every later plan is reviewed against would misstate shipped behavior. The edit replaces only that clause (and adds a history note); items 4 to 7 already describe the transaction Order 02 applies to companion pairs.

## Open questions

### OQ-01: Default the companion dir to `<repo>.aw` when switching into the companion preset?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The switch may `git init` a new repository at that path (Order 01 `companion_create`), and creating a repository the user never named is a surprise that rollback can undo but the user may not notice. Requiring `--companion-dir` (or an existing binding, F-04) costs one flag. The interactive wizard already asks for it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- agent_workflows/install_wizard.py agent_workflows/cli.py`; pasted scratch refusal output (produced by `cli._run_install` -> `install_wizard.PlacementSwitchRequired`) for a companion pair naming `--relocate`, and the `--companion-dir` refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted scratch `--relocate --dry-run` output for pair `private-target` -> companion (produced by `cli._run_install` -> `placement_switch.render_plan`) with before/after snapshots of target, companion path and `AW_HOME` equal.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff -- CHANGELOG.md README.md` and a pasted Python check printing 0 em/en dashes in the added lines; pasted spec diff of Section 8.1 item 3 and the history line; pasted `aw specs check` output conforming.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `-v` output of both CLI test modules with every case PASSED; the combined five-module summary; the bare `python3 -m pytest` summary line; the `make test-all` summary line; the `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `fo08zx` and `ozr356` are executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never install into or relocate this repository, a real companion, or the real home. Paste ACTUAL runner output. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit y1e2m9 -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize y1e2m9` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
