# IPD: Make aw status use the content-aware split-brain detector so a migrated repo is not flagged

- Date: 2026-09-26
- Kind: child
- Concern: `aw status` REPORTS A FALSE SPLIT-BRAIN ON EVERY CORRECTLY MIGRATED REPO. `cli._collect_repo_status_details` sets `split_brain = True` whenever `.aw/` and `.agents/` both exist as directories (the `if has_aw and has_agents:` arm), and the human renderer in `cli` then prints the layout in bold orange with `[dual layout / split-brain - run aw migrate-layout]`. Because `.agents/skills` is the intended skills location for BOTH layouts (`engine.SKILLS_DIR = ".agents/skills"`), `.agents/` is a PERMANENT resident of a migrated repo, so the warning can never clear and it advises a migration that already ran. This is exactly the defect plan `z1yefm` E-06 fixed in `doctor.probe_environment`, which now asks the shared content-aware `engine.detect_split_brain_layout`; `aw status` was not repointed. Re-measured at HEAD `61ef21d8` on a scratch repo holding `.aw/system/VERSION` and `.agents/skills/x/SKILL.md`: `_collect_repo_status_details` -> `layout='.aw + .agents'`, `split_brain=True`; `engine.detect_split_brain_layout` -> `False`; `doctor.probe_environment(...).layout` -> `'.aw'`. The audit backlog `ovjx46` originally asked for (check_engine's own layout rules) is NEGATIVE and is recorded in Findings.
- Scope: IN: (a) `cli._collect_repo_status_details` decides `split_brain` as `has_aw and engine.detect_split_brain_layout(repo)`, mirroring `doctor.probe_environment`, and labels the layout `.aw` (not `.aw + .agents`) when `.aw` exists and the detector says no split-brain, following doctor's label precedent; (b) a behavioral consistency test that `aw status`'s collector, `doctor.probe_environment` and `engine.detect_split_brain_layout` agree on a residue-only migrated fixture, a clean migrated fixture carrying `.agents/skills`, and a genuine split-brain fixture, plus the legacy-only and no-layout controls; (c) recording the negative `check_engine` audit. OUT: any change to `engine.detect_split_brain_layout` itself, to `doctor`, to `check_engine`, to the `--json` key names, or to the renderer's wording.
- Scope-Paths: agent_workflows/cli.py, tests/test_doctor.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: ovjx46
- Blocks-Release: next
- Set: statuslayout
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 4eecvh

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ovjx46 (reclassified bug + Blocks-Release next on 2026-09-26). The check_engine audit the item asked for is negative; the same defect was found and reproduced in aw status at HEAD 61ef21d8, which is what this plan fixes.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw status`, `aw doctor` and the install guard give ONE answer to "is this repo split-brain?", so a correctly migrated repo stops showing an orange "run aw migrate-layout" warning that no action can clear.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE THE DISAGREEMENT at the executing HEAD. Build three scratch dirs under `/tmp/`: CLEAN = `.aw/system/VERSION` + `.agents/skills/x/SKILL.md`; RESIDUE = CLEAN plus empty `.agents/workflows/assess/tools/` and a non-empty `.agents/README.md`; GENUINE = CLEAN plus a non-empty `.agents/workflows/assess/assess.md`. For each, paste `cli._collect_repo_status_details(repo, "2.0.0")["layout"]` and `["split_brain"]`, `engine.detect_split_brain_layout(repo)`, and `doctor.probe_environment(repo).layout`. If CLEAN and RESIDUE already report `split_brain=False` from the collector, STOP and report the defect fixed.
  - Depends on: none
  - Expected outcome: CLEAN and RESIDUE: collector `('.aw + .agents', True)`, engine `False`, doctor `'.aw'`. GENUINE: collector `True`, engine `True`, doctor contains `split-brain`.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 REPOINT `cli._collect_repo_status_details` at the shared detector. Replace the four-arm existence ladder with the doctor shape: `if has_aw and engine.detect_split_brain_layout(repo): layout = ".aw + .agents"; split_brain = True` / `elif has_aw: layout = ".aw"` / `elif has_agents: layout = ".agents"` / `else: layout = "none"`, `split_brain = False` in every non-first arm. Keep the `.aw + .agents` label for the genuine case so the renderer (`if rd.get("split_brain"):` in the status printer) and the `--json` `layout`/`split_brain` keys are unchanged in shape. Add a comment citing `z1yefm` E-06 and `doctor.probe_environment` as the precedent and `ovjx46` as the carrier. Do not import anything new: `engine` is already imported by `cli`.
  - Depends on: E-01
  - Expected outcome: CLEAN and RESIDUE -> `('.aw', False)`; GENUINE -> `('.aw + .agents', True)`; a legacy-only `.agents` repo -> `('.agents', False)`; an empty dir -> `('none', False)`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-03 ADD A BEHAVIORAL CONSISTENCY TEST to `tests/test_doctor.py`, inside or beside `DoctorLayoutClassificationIsContentAwareTests` (whose `setUp` already builds the RESIDUE shape with `.agents/skills`). Cases, each calling the real functions: (1) RESIDUE: collector `split_brain` is `False` and `layout == ".aw"`; (2) CLEAN (RESIDUE minus the empty tool dirs and README, i.e. `.aw/system` + `.agents/skills` only): same; (3) GENUINE: collector `split_brain` is `True`; (4) for all three shapes, `collector["split_brain"] == engine.detect_split_brain_layout(root) == ("split-brain" in doctor.probe_environment(root).layout)`; (5) legacy-only (`.aw` removed): collector `layout == ".agents"`, `split_brain` `False`. Also drive the rendered human output once for RESIDUE (call the status command path with the repo as the working directory, as `tests/test_cli.py::test_status_shows_environment_readout` does via `_run(["status"])`, or call the renderer directly if the collector output is passed in) and assert the text `dual layout / split-brain` does NOT appear, then that it DOES appear for GENUINE. If driving the full `status` command cannot be pointed at a temp repo without touching global config, assert on the collector only and say so in V-03.
  - Depends on: E-02
  - Expected outcome: all cases pass; cases (1), (2), (4) and the RESIDUE render assertion FAIL against the pre-change collector; (3) and (5) pass before and after.
  - Execution state: pending

- [ ] E-04 RUN THE BARE SUITE `python3 -m pytest` before and after the change and compare failing node IDs.
  - Depends on: E-03
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The split-brain question has ONE content-aware authority: `engine.detect_split_brain_layout` ("True iff both .aw/system exists and .agents/workflows holds real content"; cruft and empty files do not count). `cli._split_brain_guard` and, since `z1yefm` E-06, `doctor.probe_environment` consume it; `doctor.probe_environment`'s comment states the goal that "`aw doctor`, `aw check`, and the install guard cannot report this condition differently".
- `aw status` already shares ONE reader with `aw doctor` for preset and backend (`h90ij1` E-05, `project_context.read_project_identity`), and `tests/test_doctor.py::...test_status_and_doctor_report_the_same_preset_and_backend` pins that agreement behaviorally. This plan extends the same agreement to layout.
- `.agents/skills` is the intended skills location for both layouts (`engine.SKILLS_DIR`), so `.agents/` existing is NOT evidence of an unmigrated repo.
- Tests exercise behavior (maintainer ruling 2026-09-26: no source-text or structure pins). Suites run BARE as `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `cli._collect_repo_status_details` | Split-brain decided from bare directory existence; every migrated repo is flagged. | Scratch `.aw/system/VERSION` + `.agents/skills/x/SKILL.md`: collector `('.aw + .agents', True)`, `engine.detect_split_brain_layout` `False`, `doctor.probe_environment(...).layout` `'.aw'`. |
| F-2 | MEDIUM | status renderer (`if rd.get("split_brain"):` arm) | The false flag is rendered as a bold orange instruction to run `aw migrate-layout`, a migration that has already run and that re-running cannot clear. | Renderer text `[dual layout / split-brain - run aw migrate-layout]` is gated solely on `rd["split_brain"]`. |
| F-3 | INFO | `check_engine` (the audit `ovjx46` asked for) | NEGATIVE: `check_engine` has no split-brain or dual-layout rule. Its only layout rules are `check.system-layout-missing` and `check.system-layout-drift`, both emitted by `check_engine.check_system_layout`, which is gated on the install marker `.aw/system/VERSION` via `engine.read_installed_version` and reads `.aw/system/layout.json`; neither consults `.agents/` existence. | `rg -n 'split.brain|detect_split_brain' agent_workflows/check_engine.py` -> no hits; `rg -n '"check\.[a-z-]*layout' agent_workflows/check_engine.py` -> only the two `system-layout-*` rule ids. |
| F-4 | INFO | tests | No test drives the status collector's layout verdict; `tests/test_doctor.py` pins only doctor against engine, and the one status/doctor agreement test covers preset and backend. | `rg -n split_brain tests` -> hits only in `tests/test_doctor.py`, none calling `_collect_repo_status_details` for layout. |
| F-5 | LOW | edge shape | A legacy repo carrying only `.aw/.gitignore` (no `.aw/system`) plus live `.agents/workflows` is labelled `.aw` by `doctor` today; after this plan `aw status` will say the same. That matches the precedent this plan mirrors, and is recorded rather than changed. | Scratch `.aw/.gitignore` + `.agents/workflows/assess/assess.md`: doctor `'.aw'`, engine `False`, collector `('.aw + .agents', True)`. |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the disagreement on three shapes.
2. E-02 repoints the status collector at `engine.detect_split_brain_layout` with doctor's labels.
3. E-03 adds a behavioral three-way agreement test plus controls.
4. E-04 runs the bare suite before and after.

## Deferred / out of scope (with reason)

- Relabelling the partial-`.aw` legacy shape of F-5 in both `doctor` and `aw status`.
  - Carrier-Declined: the maintainer's instruction for this plan is to mirror `doctor`'s established precedent; changing what both commands call that shape is a separate labelling decision with no measured user report, and the migration preflight (plan `vv6y7e`) already treats `.aw/.gitignore` as a known in-place file.
- Any change to `check_engine`.
  - Carrier-Declined: F-3 shows it carries no existence-based split-brain rule, so there is nothing to repoint.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/doctor.py` and `agent_workflows/engine.py` are READ as the precedent and authority and are not modified; if the render assertion in E-03 needs a test helper that lives in `tests/test_cli.py`, import it rather than editing that file, or declare it at finalize.
- Scope-Paths justification: `cli.py` holds the collector; `tests/test_doctor.py` already holds the doctor/engine agreement tests and the status/doctor preset agreement test, so the new three-way test sits with its siblings.

## Required tests / validation

- New behavioral cases in `tests/test_doctor.py` (E-03), with cases (1), (2), (4) and the RESIDUE render check shown FAILING against the pre-change collector.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: no spec defines `aw status`'s layout label or split-brain rule; the physical-layout contract already names `.agents/skills` as permanent, and this plan makes `aw status` agree with it. No `.spec.md` is in `- Scope-Paths:`.
- No user docs change: the documented meaning of the warning (a genuine split-brain) is unchanged; only the false positive goes away.

## Open questions

### OQ-01: Should the fix live in check_engine, as backlog ovjx46's title suggests?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No, from repository evidence (F-3): `check_engine` has no split-brain rule at all, only the two `check.system-layout-*` rules keyed on `.aw/system/VERSION` and `.aw/system/layout.json`. The hazard the item describes (a third detector disagreeing with the shared one) was found instead in `cli._collect_repo_status_details`, and the item's own history (2026-09-26 reclassification note) already names `aw status` as the surface, so this plan fixes that.

### OQ-02: What should the layout label read for a clean migrated repo that still has `.agents/skills`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `.aw`, following `doctor.probe_environment`, which returns `.aw` for exactly this shape and is pinned so by `tests/test_doctor.py::DoctorLayoutClassificationIsContentAwareTests::test_residue_only_repo_is_not_reported_split_brain` (`assertEqual(res.layout, ".aw")`). Two commands printing different labels for the same repo is the class of defect being fixed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the four values for each of CLEAN, RESIDUE and GENUINE at the executing HEAD, with the HEAD hash.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `_collect_repo_status_details`'s layout block; paste the collector's `(layout, split_brain)` for CLEAN, RESIDUE, GENUINE, legacy-only and empty after the change, matching E-02's expected outcome.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_doctor.py -o addopts="" -q` passing with its count; then the same run with the E-02 hunk temporarily reverted showing cases (1), (2), (4) and the RESIDUE render assertion FAILING and (3), (5) passing; then passing again after restoring. State whether the render assertion drove the real `status` command or the collector only, and why.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A one-block change so `aw status` asks the same content-aware question `aw doctor` already asks before it prints "dual layout / split-brain - run aw migrate-layout". A migrated repo that keeps `.agents/skills` will read `Layout: .aw` instead of an orange warning; a repo with genuinely live legacy `.agents/workflows` content is still flagged. The negative `check_engine` audit is recorded, not acted on. This graduates backlog `ovjx46` and inherits its `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/cli.py` (`_collect_repo_status_details` only) and `tests/test_doctor.py`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-03 must show the new cases FAILING against the pre-change collector. No test may assert on source text.

GENUINE STOP CONDITION: if E-01 finds the collector already agrees with the detector, retire this plan rather than execute it.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `ovjx46` `done` with `--evidence` citing the executed plan; its release gate is preserved by that handoff.
