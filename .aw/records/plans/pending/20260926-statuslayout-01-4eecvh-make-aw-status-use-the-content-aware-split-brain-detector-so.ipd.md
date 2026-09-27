# IPD: Make aw status use the content-aware split-brain detector so a migrated repo is not flagged

- Date: 2026-09-26
- Kind: child
- Concern: `aw status` REPORTS A FALSE SPLIT-BRAIN ON EVERY CORRECTLY MIGRATED REPO. `cli._collect_repo_status_details` sets `split_brain = True` whenever `.aw/` and `.agents/` both exist as directories (the `if has_aw and has_agents:` arm), and the human renderer in `cli` then prints the layout in bold orange with `[dual layout / split-brain - run aw migrate-layout]`. Because `.agents/skills` is the intended skills location for BOTH layouts (`engine.SKILLS_DIR = ".agents/skills"`), `.agents/` is a PERMANENT resident of a migrated repo, so the warning can never clear and it advises a migration that already ran. This is exactly the defect plan `z1yefm` E-06 fixed in `doctor.probe_environment`, which now asks the shared content-aware `engine.detect_split_brain_layout`; `aw status` was not repointed. Re-measured at HEAD `61ef21d8` on a scratch repo holding `.aw/system/VERSION` and `.agents/skills/x/SKILL.md`: `_collect_repo_status_details` -> `layout='.aw + .agents'`, `split_brain=True`; `engine.detect_split_brain_layout` -> `False`; `doctor.probe_environment(...).layout` -> `'.aw'`. The audit backlog `ovjx46` originally asked for (check_engine's own layout rules) is NEGATIVE and is recorded in Findings.
- Scope: IN: (a) `cli._collect_repo_status_details` decides `split_brain` as `has_aw and engine.detect_split_brain_layout(repo)`, mirroring `doctor.probe_environment`, and labels the layout `.aw` (not `.aw + .agents`) when `.aw` exists and the detector says no split-brain, following doctor's label precedent; (b) a behavioral consistency test that `aw status`'s collector, `doctor.probe_environment` and `engine.detect_split_brain_layout` agree on a residue-only migrated fixture, a clean migrated fixture carrying `.agents/skills`, and a genuine split-brain fixture, plus the legacy-only and no-layout controls; (c) recording the negative `check_engine` audit. OUT: any change to `engine.detect_split_brain_layout` itself, to `doctor`, to `check_engine`, to the `--json` key names, or to the renderer's wording.
- Scope-Paths: agent_workflows/cli.py, tests/test_doctor.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
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
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003 all FIXED in place. Defect independently re-measured at HEAD 8b64b198 (the collector returns the identical split-brain verdict on clean, residue and genuine shapes; engine and doctor disagree with it) and the false warning reproduced through the real status command. Structural lint conformed before and after. Findings and decisions D-1..D-3 recorded in .aw/records/reviews/20260926-statuslayout-01-4eecvh-make-aw-status-use-the-content-aware-split-brain-detector-so.review.md

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ovjx46 (reclassified bug + Blocks-Release next on 2026-09-26). The check_engine audit the item asked for is negative; the same defect was found and reproduced in aw status at HEAD 61ef21d8, which is what this plan fixes.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw status`, `aw doctor` and the install guard give ONE answer to "is this repo split-brain?", so a correctly migrated repo stops showing an orange "run aw migrate-layout" warning that no action can clear.

SCOPE OF THAT CLAIM, stated because an earlier draft overstated it (revised at review, PR-001). Those THREE surfaces are the ones a user meets when asking "is my repo healthy?", and after this plan they agree. A FOURTH classifier exists and will still disagree: `upgrade_rehearsal.detect_layout` answers a DIFFERENT question with a different vocabulary (`dual` / `aw+litter` / `legacy`) over `upgrade_rehearsal.has_files`, which counts a zero-byte or cruft file as live where `engine.detect_split_brain_layout` does not (F-6, measured). That is recorded, not fixed here.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE THE DISAGREEMENT at the executing HEAD. Build the fixtures with `tempfile.TemporaryDirectory()` in one throwaway `python3 -` script, NOT as hand-made dirs under `/tmp/`: the sandbox may refuse a bare `/tmp` path (measured at review, where `/tmp/<name>` was denied and `tempfile` inside the interpreter worked), and a temp dir cleans itself up. Shapes: CLEAN = `.aw/system/VERSION` + `.agents/skills/x/SKILL.md`; RESIDUE = CLEAN plus empty `.agents/workflows/assess/tools/` and a non-empty `.agents/README.md`; GENUINE = CLEAN plus a non-empty `.agents/workflows/assess/assess.md`. For each, paste `cli._collect_repo_status_details(repo, "2.0.0")["layout"]` and `["split_brain"]`, `engine.detect_split_brain_layout(repo)`, and `doctor.probe_environment(repo).layout`. If CLEAN and RESIDUE already report `split_brain=False` from the collector, STOP and report the defect fixed.
  - Depends on: none
  - Expected outcome: CLEAN and RESIDUE: collector `('.aw + .agents', True)`, engine `False`, doctor `'.aw'`. GENUINE: collector `('.aw + .agents', True)`, engine `True`, doctor contains `split-brain`. Note the collector's verdict is IDENTICAL across all three, which is the defect: it carries no information about content.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 REPOINT `cli._collect_repo_status_details` at the shared detector. Replace the four-arm existence ladder with the doctor shape: `if has_aw and engine.detect_split_brain_layout(repo): layout = ".aw + .agents"; split_brain = True` / `elif has_aw: layout = ".aw"` / `elif has_agents: layout = ".agents"` / `else: layout = "none"`, `split_brain = False` in every non-first arm. Keep the `.aw + .agents` label for the genuine case so the renderer (`if rd.get("split_brain"):` in the status printer) and the `--json` `layout`/`split_brain` keys are unchanged in shape. Add a comment citing `z1yefm` E-06 and `doctor.probe_environment` as the precedent and `ovjx46` as the carrier. Do not import anything new: `engine` is already imported by `cli`.
  - Depends on: E-01
  - Expected outcome: CLEAN and RESIDUE -> `('.aw', False)`; GENUINE -> `('.aw + .agents', True)`; a legacy-only `.agents` repo -> `('.agents', False)`; an empty dir -> `('none', False)`.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-03 ADD A BEHAVIORAL CONSISTENCY TEST to `tests/test_doctor.py`, inside or beside `DoctorLayoutClassificationIsContentAwareTests` (whose `setUp` already builds the RESIDUE shape with `.agents/skills`). Cases, each calling the real functions: (1) RESIDUE: collector `split_brain` is `False` and `layout == ".aw"`; (2) CLEAN (RESIDUE minus the empty tool dirs and README, i.e. `.aw/system` + `.agents/skills` only): same; (3) GENUINE: collector `split_brain` is `True`; (4) for all three shapes, `collector["split_brain"] == engine.detect_split_brain_layout(root) == ("split-brain" in doctor.probe_environment(root).layout)`; (5) legacy-only (`.aw` removed): collector `layout == ".agents"`, `split_brain` `False`. Also drive the RENDERED human output, because the user-visible symptom is a line of text and no test asserts on it today (F-4).

  THE RENDER MECHANISM IS PRESCRIBED, NOT LEFT TO THE EXECUTOR, and it was PROVEN AT REVIEW rather than assumed (PR-002; the earlier "if it cannot be done, assert on the collector only and say so" hedge is removed, since the escape it offered would have dropped the only assertion covering the symptom). Both of these were executed at review against the unfixed code and both printed the false warning, so either is acceptable:
  - `mock.patch.object(cli, "_repos_for_report", return_value=[repo])` around `cli.main(["status"])`, stdout captured, which needs no config file at all; or
  - `config.set_repo_setting(cfg, "installed", [str(repo)])` + `config.save(cfg)` with `XDG_CONFIG_HOME` pointed at a temp dir, which is what `tests/test_cli.py::CliTestBase.setUp` does.
  Set `NO_COLOR=1` and strip ANSI (`re.sub(r"\033\[[0-9;]*m", "", out)`) before asserting: the warning is emitted through `term.color256(..., 208, bold=True)`, so a raw-substring assertion is brittle against escape codes. Do NOT put the render case in `tests/test_cli.py`: that module is `pytestmark = pytest.mark.slow` (`tests/test_cli.py:29`), so a case added there would NOT run in the bare suite E-04 uses as its gate, and would silently never execute. `tests/test_doctor.py` carries no `pytestmark` and runs bare. Restore any environment variable you set in `tearDown`.

  Assert the text `dual layout / split-brain` does NOT appear for RESIDUE, and DOES appear for GENUINE.
  - Depends on: E-02
  - Expected outcome: all cases pass; cases (1), (2), (4) and BOTH render assertions' RESIDUE half FAIL against the pre-change collector; (3) and (5) pass before and after. Measured at review on the unfixed code: RESIDUE and GENUINE both render `Layout:    .aw + .agents [dual layout / split-brain - run aw migrate-layout]`, so the RESIDUE render assertion is genuinely red before the fix and is not vacuous.
  - Execution state: pending

- [ ] E-04 RUN THE BARE SUITE `python3 -m pytest` before and after the change and compare failing node IDs. Bare means bare: do NOT add `-n0`, a second `-q`, or `-p no:randomly`. Baseline measured at review on this lane: `2501 passed, 2 skipped, 3 warnings in 59.95s`. RE-DERIVE that number rather than matching it (a live population that drifts with every merge); the BAR is the failing-node-set comparison, not the count.
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
| F-5 | LOW | edge shape | A legacy repo carrying only `.aw/.gitignore` (no `.aw/system`) plus live `.agents/workflows` is labelled `.aw` by `doctor` today; after this plan `aw status` will say the same. That matches the precedent this plan mirrors, and is recorded rather than changed. | Scratch `.aw/.gitignore` + `.agents/workflows/assess/assess.md`: doctor `'.aw'`, engine `False`, collector `('.aw + .agents', True)`. Re-measured at review: identical. |
| F-6 | LOW | `upgrade_rehearsal.detect_layout` (added at review, PR-001) | A FOURTH layout classifier exists and does NOT consume the shared detector: it walks `upgrade_rehearsal.has_files`, which counts ANY file including a zero-byte or cruft one, where `engine.is_ignored_source_path` + the `st_size > 0` test in `engine.detect_split_brain_layout` deliberately do not. So it reports `dual` on shapes the shared detector calls clean. It is OUT of scope and is recorded, not fixed: it answers a different question (a rehearsal-harness classification with its own five-value vocabulary, whose own docstring already notes "`aw doctor` may still call it dual"), it is not a surface a user consults to judge repo health, and `upgrade_rehearsal.py` is outside `- Scope-Paths:`. | Measured at review, `.aw/system/VERSION` present in each case: a `__pycache__/x.pyc` under `.agents/workflows` -> engine `False`, rehearsal `'dual'`, doctor `'.aw'`; a ZERO-BYTE `assess/empty.md` -> engine `False`, rehearsal `'dual'`, doctor `'.aw'`; a live `assess/assess.md` -> engine `True`, rehearsal `'dual'`, doctor contains `split-brain`. |
| F-7 | INFO | performance of the new call (added at review) | Repointing adds a filesystem walk to a command that previously did four `is_dir()` calls, so it is worth stating it is not a user-perceptible cost (the repo's own bug bar, AGENTS.md "inefficiency a user can notice is a defect"). It is not, by three measurements. The walk also SHORT-CIRCUITS on the first qualifying file, so the genuine split-brain case is the cheapest, not the most expensive. | Measured at review: clean migrated repo (no `.agents/workflows`) 17 us/call; realistic residue shape (4 empty tool dirs) 120 us/call; a deliberately pathological 1200-file all-zero-byte tree, which cannot short-circuit, 23.7 ms/call. `aw status` already calls `attention.scan(repo)` per repo, which is orders of magnitude more work. |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the disagreement on three shapes (temp dirs built in-process, not hand-made `/tmp` paths).
2. E-02 repoints the status collector at `engine.detect_split_brain_layout` with doctor's labels.
3. E-03 adds a behavioral three-way agreement test plus controls, plus the RENDER assertion on the user-visible warning line, in the bare-running `tests/test_doctor.py`.
4. E-04 runs the bare suite before and after.

No source-text or structure assertion appears anywhere in this plan (maintainer ruling 2026-09-26): every check drives a real function or the real command.

## Deferred / out of scope (with reason)

- Relabelling the partial-`.aw` legacy shape of F-5 in both `doctor` and `aw status`.
  - Carrier-Declined: the maintainer's instruction for this plan is to mirror `doctor`'s established precedent; changing what both commands call that shape is a separate labelling decision with no measured user report, and the migration preflight (plan `vv6y7e`) already treats `.aw/.gitignore` as a known in-place file.
- Any change to `check_engine`.
  - Carrier-Declined: F-3 shows it carries no existence-based split-brain rule, so there is nothing to repoint.
- Aligning `upgrade_rehearsal.detect_layout` with the shared detector (F-6, added at review).
  - Carrier-Declined: this is a DELIBERATE divergence, not an unfixed defect, so there is nothing to hand off. `detect_layout` answers a different question with a different five-value vocabulary (`aw` / `legacy` / `dual` / `aw+litter` / `none`) for a rehearsal harness whose own `derive_observations` docstring says it is "Descriptive, never a pass/fail verdict" and which already tells its reader that "`aw doctor` may still call it dual". Its `has_files` counting a zero-byte file is also arguably CORRECT for its purpose: a rehearsal wants to know whether a migration left anything behind at all, where the health question wants to know whether live workflow content exists. No user consults it to judge repo health, so it produces none of the false warning this plan fixes. If a future reader disagrees, the right move is a backlog item against `upgrade_rehearsal.py`, not widening this one-block plan.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/doctor.py` and `agent_workflows/engine.py` are READ as the precedent and authority and are not modified. The E-03 render case needs NO helper from `tests/test_cli.py` (revised at review, PR-002): both prescribed mechanisms use only `unittest.mock`, `config`, and stdlib capture, so nothing is imported from that module and it is not edited. Importing from it would also be undesirable rather than merely unnecessary, since it is `pytestmark = pytest.mark.slow`.
- Scope-Paths justification: `cli.py` holds the collector; `tests/test_doctor.py` already holds the doctor/engine agreement tests and the status/doctor preset agreement test, so the new three-way test sits with its siblings.

## Required tests / validation

- New behavioral cases in `tests/test_doctor.py` (E-03), with cases (1), (2), (4) and the RESIDUE render check shown FAILING against the pre-change collector.
- Every new case lands in `tests/test_doctor.py`, which carries NO `pytestmark`, so all of it runs in the bare suite. A case placed in `tests/test_cli.py` or `tests/test_installer.py` would be `slow`-marked and excluded from the bare run (`pyproject.toml` `addopts` `-m 'not slow'`), i.e. written but never executed by E-04's gate.
- Bare `python3 -m pytest` before and after; compare failing node IDs.
- No source-text assertion anywhere: every case calls the real `cli._collect_repo_status_details`, `engine.detect_split_brain_layout`, `doctor.probe_environment`, or the real `status` command, and asserts on returned values or rendered output (maintainer ruling 2026-09-26).

## Spec / documentation sync

- N/A for specs: no spec defines `aw status`'s layout label or split-brain rule; the physical-layout contract already names `.agents/skills` as permanent, and this plan makes `aw status` agree with it. No `.spec.md` is in `- Scope-Paths:`. VERIFIED AT REVIEW: `rg 'split.brain|dual layout' .aw/records/specs/` returns no hits, and the one spec naming the path (`20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`) lists `.agents/skills/` among the host-mandated discovery paths that are "permitted", which is the premise this plan relies on rather than changes.
- No user docs change, VERIFIED AT REVIEW rather than asserted: `rg 'split.brain|dual layout|Layout:' docs/` returns no hits, so no document describes this line, and `docs/cli-output-contract.md` does not name the `layout` or `split_brain` keys. The `--json` / `--agent` payload keys are unchanged in NAME and TYPE (only the computed VALUE changes, and only for a repo the old code misclassified), so no published-contract amendment is owed.

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
- Resolution or deferral rationale: `.aw`, following `doctor.probe_environment`, which returns `.aw` for exactly this shape and is pinned so by `tests/test_doctor.py::DoctorLayoutClassificationIsContentAwareTests::test_residue_only_repo_is_not_reported_split_brain` (`assertEqual(res.layout, ".aw")`). Two commands printing different labels for the same repo is the class of defect being fixed. CONFIRMED AT REVIEW by reading that assertion and by driving `doctor.probe_environment` on the same fixture shape.

### OQ-03: A fourth classifier (`upgrade_rehearsal.detect_layout`) still disagrees. Does this plan's Goal require fixing it?

- Blocking: no
- Status: resolved
- Owner: reviewer (raised and resolved at review from F-6)
- Resolution or deferral rationale: No. Resolved from repository evidence rather than by asking, because the harness DOCUMENTS the divergence as intended rather than treating it as a bug: `derive_observations`'s `aw+litter` branch tells its reader the state is "Directory litter, not a split-brain layout, though 'aw doctor' may still call it dual", and the function's docstring says its output is "Descriptive, never a pass/fail verdict". So the two answers are deliberately different answers to different questions, and the Goal's claim was narrowed (PR-001) to the three HEALTH surfaces a user actually consults rather than widened to include a rehearsal harness. Measured shapes are in F-6; the disposition is recorded as a reasoned `Carrier-Declined` under "Deferred / out of scope". If a future reader wants them unified, that is an item against `upgrade_rehearsal.py`, which is outside this plan's `- Scope-Paths:`.

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
  - Required evidence: paste `python3 -m pytest tests/test_doctor.py -o addopts="" -q` passing with its count. Then paste a BEFORE-FIX run showing cases (1), (2), (4) and the RESIDUE render assertion FAILING while (3) and (5) pass. Finally re-paste the passing run.

    HOW TO OBTAIN THE BEFORE-FIX RUN (prescribed at review, PR-003, because the mechanism decides whether the fix can be lost). Preferred: check the NEW TEST FILE STATE out into a throwaway detached worktree at the pre-change commit, i.e. `git worktree add --detach .aw/tmp/4eecvh-head <pre-change-commit>`, copy the new test module in, run there, then `git worktree remove --force .aw/tmp/4eecvh-head`. `.aw/worktrees/` and `tmp/` are gitignored (`.gitignore:73`, `.gitignore:42`). Acceptable alternative: temporarily revert ONLY the E-02 hunk in place, run, and restore it. If you take the alternative, restore it IMMEDIATELY in the next command, and note in the evidence that you did: an interrupted restore leaves the repo carrying the bug with a test suite that fails, which is worse than either end state. Do NOT use `git stash`: this is a SHARED CHECKOUT and stashing would move another party's uncommitted work.

    A CONTROL THAT ALSO FAILS MEANS THE TEST IS BROKEN, not that the fix is bigger: cases (3) and (5) must pass in BOTH runs. If either fails before the fix, report it rather than adjusting the assertion to make it green.

    State which of the two prescribed render mechanisms E-03 used (`mock.patch.object(cli, "_repos_for_report", ...)` or the `XDG_CONFIG_HOME` + `config.save` route), and confirm the assertion ran against ANSI-stripped output with `NO_COLOR=1`.
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

THE BEHAVIOR CHANGE A HUMAN SHOULD WEIGH, stated plainly because it is the only thing here that could surprise anyone. `--json` / `--agent` consumers of `aw status` keep the same key NAMES and TYPES, but a repo that today reports `layout: ".aw + .agents"` / `split_brain: true` will report `layout: ".aw"` / `split_brain: false` after this change. That is the POINT (the old value was wrong), and `aw doctor` has already reported the corrected answer for the same repo since `z1yefm`, so this removes a divergence rather than creating one. No in-repo consumer asserts on those values (F-4, re-verified at review: the only `_collect_repo_status_details` caller in `tests/` reads `preset`/`backend`).

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/cli.py` (`_collect_repo_status_details` only) and `tests/test_doctor.py`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-03 must show the new cases FAILING against the pre-change collector. No test may assert on source text.

GENUINE STOP CONDITION: if E-01 finds the collector already agrees with the detector, retire this plan rather than execute it. As of this review the defect is LIVE and reproduced (F-1, F-2 re-measured), so this is a guard against someone else landing the same fix first, not an expected outcome.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `ovjx46` `done` with `--evidence` citing the executed plan; its release gate is preserved by that handoff.
