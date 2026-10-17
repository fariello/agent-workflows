# IPD: release_readiness: disposition a managed repo's own workflow rows as repo-local instead of failing workflow_disposition

- Date: 2026-10-16
- Kind: child
- Concern: `release_readiness.gate_workflow_disposition` (behind `aw releases readiness`, which plan `kmmoca` makes release-review run in every managed repository) calls `migration_inventory.build_inventory`, whose `_command_disposition` raises `InventoryError` "manifest command '<name>' has no reviewed family assignment (silent omission)" for any manifest command absent from `migration_inventory._COMMAND_FAMILY`. That table is THIS toolkit's own reviewed catalog. A managed repository that adds its own workflow row (exactly what the installed `/scaffold` workflow tells it to do) therefore gets a permanent `NO-GO` it cannot clear without editing toolkit source. Measured at `00d07c836` (F-01).
- Scope: IN: (1) `migration_inventory.build_inventory` and `migration_inventory.check_completeness` gain an opt-in repo-local mode in which a manifest COMMAND absent from `_COMMAND_FAMILY` is collected into a new `InventoryResult.repo_local` list instead of raising, and is exempt from the "has NO disposition" completeness finding; the default (opt-in off) is byte-for-byte today's fail-closed behavior; (2) `release_readiness.gate_workflow_disposition` enables that mode exactly when the repository is NOT this toolkit's source checkout (`engine.is_source_checkout(root)` is False), and reports the repo-local commands by name in `detail` and `evidence["repo_local"]`; (3) behavioral tests in a new module plus the one existing test that pins the old managed-tree failure; (4) `docs/recovery.md` and `CHANGELOG.md`. OUT: giving repo-local workflows a fabricated family or disposition row (OQ-02); any change to `_COMMAND_FAMILY`, `_FAMILY_DEFAULTS`, catalog (`assess-*`/`advise-*`) handling, or the Order-14 ownership fence; the not-applicable state and absent-`index.md` behavior (owned by `4bw2u5`); release-review workflow bodies and `RELEASING.md` (owned by `kmmoca`); the installer and `index.md` version stamps (owned by `e9l2e0`).
- Scope-Paths: agent_workflows/migration_inventory.py, agent_workflows/release_readiness.py, tests/test_release_readiness_repo_local_workflows.py, tests/test_release_readiness_producers.py, docs/recovery.md, CHANGELOG.md
- Item-Dependencies: executed:4bw2u5
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: ufawpb
- Blocks-Release: next
- Set: uypgvi
- Order: 4
- Highest E allocated: 07
- Author: opencode
- Id: snhhw2
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-005

- 2026-10-16 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog ufawpb at HEAD 00d07c836; reproduced on a fresh managed install; resolved the support question from repository evidence (OQ-01).

## Goal

Make `workflow_disposition` honest in both kinds of repository: in this toolkit's source checkout every manifest command must still carry a reviewed family (fail closed, unchanged), while in a managed repository the repo's own workflow rows are reported as repo-local (named, not silently passed, not fabricated into a family) and no longer force a `NO-GO` the maintainer cannot clear.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Reproduce the false NO-GO at the executing HEAD and record the baseline.
  - Depends on: none
  - Expected outcome: one pasted transcript proving: (a) a fresh managed install into a gitignored scratch dir (`mkdir -p .aw/state/scratch-snhhw2/mr && git -C .aw/state/scratch-snhhw2/mr init -q`, then `python3 -m agent_workflows install .aw/state/scratch-snhhw2/mr --yes --no-interactive --preset private-target --delivery-mode tracked --records-backend repository`) passes `release_readiness.gate_workflow_disposition(repo_root=<scratch>)`; (b) after appending a copy of the `| whatnext |` manifest row renamed `| mycustomwf |` to the scratch `.aw/system/workflows/index.md`, the same gate prints `False` with evidence `undispositioned == ["manifest command 'mycustomwf' has no reviewed family assignment (silent omission)"]`; (c) `python3 -c "from pathlib import Path; from agent_workflows import engine; print(engine.is_source_checkout(Path('.')), engine.is_source_checkout(Path('.aw/state/scratch-snhhw2/mr')))"` prints `True False`; (d) `git grep -n -e build_inventory -e _COMMAND_FAMILY -e InventoryError -- agent_workflows tests` shows `release_readiness.gate_workflow_disposition` is the only production caller of `build_inventory` (so the new keyword cannot change another caller); (e) the shape of `gate_workflow_disposition` as left by `4bw2u5` (its not-applicable branch for an absent `index.md`), quoted, since this plan edits the same function after it; (f) the pre-edit bare `python3 -m pytest` summary line and the sorted names of any failing tests (the baseline E-07 compares against by name). If (b) already passes, stop and reconcile rather than duplicating work.
  - Execution state: performed

### Task group 2: the fix

- [x] E-02 Write the regression tests FIRST in `tests/test_release_readiness_repo_local_workflows.py` and show them RED against the unmodified modules.
  - Depends on: E-01
  - Expected outcome: a new pytest module, asserting observable outcomes only (no `inspect`, `ast`, or source regex; GUIDING_PRINCIPLES P16), with `GIT_CEILING_DIRECTORIES` pinned to `tmp_path.parent` and reusing `tests.test_release_readiness_producers.setup_minimal_workflows_tree` for the managed-style tree (no `pyproject.toml`, so `engine.is_source_checkout` is False there). Cases: (1) `test_managed_repo_custom_command_is_repo_local_not_failing`: the minimal tree plus a manifest row `mycustomwf` (body file created) gives `gate_workflow_disposition(repo_root=tmp_path).passed is True`, `evidence["repo_local"] == ["mycustomwf"]`, `evidence["undispositioned"] == []`, and `"mycustomwf"` appears in `detail`; (2) `test_source_checkout_custom_command_still_fails_closed`: the SAME tree made a source checkout (add `pyproject.toml` containing `name = "agent-workflows"` and `.aw/system/VERSION`, and confirm `engine.is_source_checkout(tmp_path)` is True in the test) gives `passed is False` with the "no reviewed family assignment" finding and `evidence.get("repo_local", []) == []` (the falsifiability contrast for case 1); (3) `test_managed_repo_without_custom_rows_reports_no_repo_local`: the plain minimal tree passes with `evidence["repo_local"] == []` and `detail == "all workflows dispositioned"` (no noise for the common case); (4) `test_repo_local_mode_keeps_other_findings`: in the managed tree with a custom row AND `conformance/operator-protocol.md` removed, the gate still FAILS on "conformance entry file missing" while listing `mycustomwf` under `repo_local` (repo-local mode exempts only the unassigned-command omission, nothing else); (5) `test_build_inventory_default_still_raises`: `migration_inventory.build_inventory(<managed wf_dir with custom row>)` with no keyword raises `InventoryError` naming `mycustomwf`, and with `allow_repo_local=True` returns an `InventoryResult` whose `repo_local == ["mycustomwf"]`, whose `dispositions` has no `mycustomwf` key, and whose `findings` is empty; (6) `test_cli_managed_repo_custom_row_is_go`: `python3 -m agent_workflows releases readiness --suite-passed --residual-risk-signer qa --json` (subprocess, `PYTHONPATH` pinned as in `tests/test_releases_readiness_cli.py::_run_subprocess`) over the tree built by `tests.test_releases_readiness_cli._build_subprocess_go_tree` plus a custom manifest row `| mycustomwf | .aw/system/workflows/mycustomwf/mycustomwf.md | Custom |` whose body file IS created (otherwise `gate_artifact_manifest` fails on "missing body file" and masks the result): exit `0` (or, if another gate fails on that tree at execution HEAD, `workflow_disposition` is absent from `data.failing_gates` and that other gate is named as measured), and the `workflow_disposition` gate's evidence carries `repo_local == ["mycustomwf"]`. RED proof: run `python3 -m pytest -o addopts="" -q tests/test_release_readiness_repo_local_workflows.py` before E-03 and paste the failing output. Expected RED set, derived from the unmodified code: case 1 fails (InventoryError branch, `passed is False`), case 3 fails (`KeyError: 'repo_local'`), case 4 fails (the unmodified `build_inventory` raises on `mycustomwf` before `check_completeness` runs, so the conformance finding is never reported), case 5 fails (`TypeError` on `allow_repo_local=`), case 6 fails (`workflow_disposition` in `failing_gates`); case 2 PASSES both before and after (it is the fail-closed contrast and must stay green). Any deviation from this set is reported and reconciled before E-03.
  - Execution state: performed

- [x] E-03 Add the opt-in repo-local mode to `migration_inventory`.
  - Depends on: E-02
  - Expected outcome: `InventoryResult` gains `repo_local: List[str] = field(default_factory=list)` (sorted, included in `to_dict()` as `"repo_local"`); `build_inventory(source_root, *, allow_repo_local: bool = False)`: for each manifest COMMAND whose name is not in `_COMMAND_FAMILY`, when `allow_repo_local` is True the command is appended to `repo_local` and gets NO disposition, otherwise `_command_disposition` raises exactly as today; `check_completeness(dispositions, workflows, source_root, repo_local=())` skips the "subject '<x>' has NO disposition (silent omission)" finding only for subjects in `repo_local`, and every other check (vocabulary, canonical target, conformance entry, Order-14 fence, stray dispositions) is unchanged. Lens/persona catalog rows are untouched (they already disposition any `assess-*`/`advise-*` row). A comment at `_COMMAND_FAMILY` states that the table is this toolkit's own catalog, that fail-closed remains the default and the source-checkout behavior, and that only a managed repository's own rows are reported as repo-local, citing backlog `ufawpb`. The `build_inventory` docstring sentence "Raises :class:`InventoryError` only for a programmer error (an unassigned command family)" is updated to say it raises only when `allow_repo_local` is False. `render_agent_report` keeps calling `build_inventory` with the default (fail closed).
  - Execution state: performed

- [x] E-04 Enable repo-local mode in `release_readiness.gate_workflow_disposition` outside the toolkit source checkout.
  - Depends on: E-03
  - Expected outcome: on the filesystem path only (an injected `undispositioned` sequence still bypasses the filesystem, unchanged), the gate computes `allow_repo_local = not engine.is_source_checkout(root)` (imported lazily beside `migration_inventory`), passes it to `build_inventory`, and adds `evidence["repo_local"]` (sorted, `[]` when none) to BOTH results that follow the inventory call: the success/findings result and the `InventoryError` result (where it is `[]`). The missing-tree, not-applicable (from `4bw2u5`), and "could not run" results keep their existing evidence shape unchanged. When `repo_local` is non-empty and there are no findings, `passed` is True and `detail` is `"all workflows dispositioned; N repo-local workflow(s) outside the toolkit catalog: a, b"`; with no repo-local rows `detail` stays exactly `"all workflows dispositioned"`. Findings still FAIL as today. The `InventoryError` branch remains for the source checkout. Whatever branch `4bw2u5` added for an absent `index.md` (E-01(e)) is preserved unchanged. The docstring states the source-checkout/managed distinction and why.
  - Execution state: performed

- [x] E-05 Update the one existing test that pins the old managed-tree failure.
  - Depends on: E-04
  - Expected outcome: `tests/test_release_readiness_producers.py::test_disposition_unassigned_command_fails_without_raising` keeps its intent (an unassigned command in the toolkit's own catalog fails without raising) by making its fixture a source checkout (`pyproject.toml` with `name = "agent-workflows"` and `.aw/system/VERSION`), with a docstring line citing `ufawpb` for why; its assertions (`passed is False`, one undispositioned entry, "no reviewed family assignment") stay as they are. No other existing test changes; any other test that turns red is a regression to investigate, not to edit.
  - Execution state: performed

- [x] E-06 Document the behavior in `docs/recovery.md` and `CHANGELOG.md`.
  - Depends on: E-04
  - Expected outcome: `docs/recovery.md` "Release readiness (decision only)" gains a short paragraph: in a managed repository, manifest rows outside the toolkit's reviewed catalog (normally the workflows the repository added itself, but also any toolkit row the running `aw` version does not know, for example after a version skew between the installed tree and the CLI) are listed by name as repo-local by the `workflow_disposition` gate and do not force NO-GO, so review that list, while in the toolkit's own source checkout every command must carry a reviewed disposition. `CHANGELOG.md` gains one `Fixed:` bullet under the current pending section saying `aw releases readiness` no longer reports a false `workflow_disposition` NO-GO in a managed repository that adds its own workflows. No em or en dashes in either addition (AGENTS.md user-facing prose rule).
  - Execution state: performed

### Task group 3: validation

- [x] E-07 Run targeted and full validation, and re-observe the managed install.
  - Depends on: E-05, E-06
  - Expected outcome: (1) `python3 -m pytest -o addopts="" -q tests/test_release_readiness_repo_local_workflows.py tests/test_release_readiness_producers.py tests/test_release_readiness.py tests/test_release_readiness_docs_gate.py tests/test_releases_readiness_cli.py` passes with 0 failures; (2) re-running E-01(a)+(b) in a FRESH scratch dir (`.aw/state/scratch-snhhw2/mr2`) prints `True` with `evidence["repo_local"] == ["mycustomwf"]`; (3) `gate_workflow_disposition(repo_root=Path('.'))` in this checkout still passes with `evidence["repo_local"] == []` (the toolkit's own manifest is fully dispositioned and the source checkout is not in repo-local mode); (4) a `\u2014`/`\u2013` scan of the `docs/recovery.md` and `CHANGELOG.md` additions finds 0; (5) `python3 -m agent_workflows sanitize --agent` reports `"outcome": "clean"`; (6) bare `python3 -m pytest` passes with zero new failures compared by name against the E-01(f) baseline; (7) `rm -rf .aw/state/scratch-snhhw2` and `git status --porcelain` lists only `- Scope-Paths:` entries.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `_COMMAND_FAMILY` FAILS CLOSED by design: an unassigned toolkit command must be dispositioned, not defaulted (comments at the `spec-review` and `askme` entries: "That is the table working, not a defect"). This plan keeps that in the toolkit source checkout and does not add a default family.
- `engine.is_source_checkout` is the established positive-identity test for "this is the agent-workflows developer checkout" (package metadata plus `.aw/system` presence); `project_layout.install_system_tree` already branches on it.
- Managed repositories are expected to add their own manifest rows: the installed `/scaffold` workflow says "Add a row to the manifest table in `.aw/system/workflows/index.md` between the `WORKFLOWS-MANIFEST` markers" and then regenerate shims with `aw install .` (`.aw/system/workflows/scaffold/scaffold.md` Step 3 and Step 4).
- Sibling plans in Set `uypgvi` own adjacent surfaces: `4bw2u5` (not-applicable gate state, same function), `kmmoca` (release-review consumption), `e9l2e0` (installer stamps).
- Tests assert observable behavior only (AGENTS.md, GUIDING_PRINCIPLES P16); the full suite runs bare as `python3 -m pytest`, narrowed runs clear defaults with `-o addopts=""`.
- User-facing prose (`docs/`, `CHANGELOG.md`) carries no em or en dashes (AGENTS.md).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Reproduced: one custom manifest row in a fresh managed install turns `workflow_disposition` from pass to fail. | At `00d07c836`: `python3 -m agent_workflows install .aw/state/scratch-snhhw2/mr --yes --no-interactive --preset private-target --delivery-mode tracked --records-backend repository` (rc=0); `gate_workflow_disposition(repo_root=<scratch>).passed` printed `True`; after appending a `| mycustomwf |` copy of the `whatnext` row it printed `False {'undispositioned': ["manifest command 'mycustomwf' has no reviewed family assignment (silent omission)"]}`; on this checkout the gate printed `True`. |
| F-02 | ROOT CAUSE: the inventory treats the toolkit's catalog as the complete universe of commands in any repository. | `migration_inventory._command_disposition` raises `InventoryError` when `_COMMAND_FAMILY.get(cmd)` is None; `build_inventory` calls it for every non-catalog row of `engine.parse_manifest(root)`; `release_readiness.gate_workflow_disposition` catches `InventoryError` and fails. |
| F-03 | The source checkout and a managed install are already distinguishable by an existing predicate. | `engine.is_source_checkout(Path('.'))` printed `True` in this worktree; the managed scratch has no `pyproject.toml` naming `agent-workflows`, so the predicate's package-metadata check returns False there. |
| F-04 | Custom rows are a supported, documented use in managed repos, not misuse. | `.aw/system/workflows/scaffold/scaffold.md` (installed into every managed repo) Step 3 "Add a row to the manifest table in `.aw/system/workflows/index.md`"; `.aw/system/workflows/index.md` "Add personas with `scaffold`". |
| F-05 | Only one production caller and one existing test are affected. | `git grep -ln -e migration_inventory -e InventoryError -- agent_workflows tests` at `00d07c836`: `agent_workflows/release_readiness.py`, `agent_workflows/migration_inventory.py`, a docstring mention in `agent_workflows/migration_compact.py`, `agent_workflows/layout_inventory.py` (an UNRELATED class of the same name, `layout_inventory.InventoryError`; corrected at review), and `tests/test_release_readiness_producers.py`; `git grep -n -e build_inventory -e check_completeness -- agent_workflows tests` outside `migration_inventory.py` matches only `release_readiness.gate_workflow_disposition` (re-verified at review, HEAD `b551549b9`); in that test module only `test_disposition_unassigned_command_fails_without_raising` builds a non-source tree with an unassigned command. |
| F-06 | The readiness producer tests are green at authoring HEAD. | `python3 -m pytest -o addopts="" -q tests/test_release_readiness_producers.py` at `00d07c836`: `26 passed in 1.19s`. |

## Proposed changes (ordered, validatable)

1. Reproduce and baseline (E-01).
2. RED behavioral tests for managed vs source-checkout behavior and the CLI (E-02).
3. Opt-in repo-local mode in `migration_inventory` (E-03).
4. Enable it in `gate_workflow_disposition` outside the source checkout and report the names (E-04).
5. Re-point the one test pinning the old managed-tree failure at a source-checkout fixture (E-05).
6. Docs and changelog (E-06).
7. Targeted, end-to-end and full-suite validation (E-07).

## Deferred / out of scope (with reason)

- Fabricating a family or `Disposition` row (execution mode, risk, skill decision, migration owner) for repo-local workflows: rejected (OQ-02). Those values are the toolkit's reviewed migration bookkeeping; inventing them for a workflow nobody reviewed would assert facts the inventory cannot know.
  - Carrier-Declined: rejected design alternative, not outstanding work; nothing remains to do.
- A per-repo config file letting a managed repo declare dispositions for its own workflows: not needed for the fix and would add a new public contract; revisit only if a consumer needs repo-local dispositions.
  - Carrier-Declined: speculative feature with no consumer today; nothing remains to do for this bug.
- Absent-`index.md` and not-applicable semantics of the same gate.
  - Carrier: 4bw2u5
  - Carrier-Evidence: .aw/records/plans/executed/20261016-uypgvi-02-4bw2u5-release-readiness-report-a-gate-whose-input-files-are-absent.ipd.md

## Scope check

- Over-scope: none. Two production functions, one opt-in keyword, their tests, and two doc lines.
- Under-scope: none for the backlog item. It asks whether managed-repo custom workflows are supported (answered yes from F-04, OQ-01) and how they are dispositioned (reported as repo-local, OQ-02), and the gate no longer reports a false `NO-GO` (E-02 cases 1 and 6, E-07(2)).

## Required tests / validation

- New `tests/test_release_readiness_repo_local_workflows.py` (E-02), RED before E-03 and GREEN after E-04.
- Re-pointed `test_disposition_unassigned_command_fails_without_raising` (E-05) and the rest of the readiness suites stay green (E-07(1)).
- End-to-end managed install with a custom row, this-checkout gate, dash scan, `aw sanitize --agent`, and bare `python3 -m pytest` compared by name with the baseline (E-07).

## Spec / documentation sync

- `docs/recovery.md` and `CHANGELOG.md` (E-06).
- No spec describes the inventory or this gate: `git grep -ln -e migration_inventory -e workflow_disposition -e _COMMAND_FAMILY -- .aw/records/specs/ docs/` matched nothing at `00d07c836`, so no `.spec.md` is touched or declared.
- `.aw/system/workflows/scaffold/scaffold.md` already documents adding rows; after this fix that advice no longer breaks release readiness, so it needs no edit.

## Open questions

### OQ-01: Are managed-repository custom workflows supported?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: yes. The toolkit installs `/scaffold` into every managed repo and it instructs the owner to add manifest rows and regenerate shims (F-04); the installer generates shims from whatever rows the manifest carries. Failing release readiness for following the toolkit's own instructions is the defect. Reviewer: if the maintainer instead wants custom rows unsupported, the alternative is to change `/scaffold`, and this plan should be retired rather than executed.

### OQ-02: How is a repo-local workflow dispositioned?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: it is NOT given a disposition; it is listed by name as repo-local in the gate's `detail` and `evidence["repo_local"]`, and is exempt only from the "no disposition" omission check. This keeps the inventory truthful (no fabricated family values), keeps the omission visible rather than silently passing, keeps fail-closed for the toolkit's own catalog in the source checkout (where a missing family is a real defect), and is reversible by removing one keyword. The mode is selected by `engine.is_source_checkout`, the repository's established identity predicate (F-03). Accepted risk (recorded at review): in a managed repo the gate cannot tell a repo-authored row from a TOOLKIT row the running `aw` does not catalog (installed tree newer than the CLI); both are reported as repo-local by name rather than failing, which is why the names are surfaced in `detail` and documented in `docs/recovery.md` (E-06) as something to review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha and the full E-01 transcript (code path: `engine.install_into_repo` via `python3 -m agent_workflows install`, then `release_readiness.gate_workflow_disposition`): (a) the scratch gate `True`; (b) the gate `False` with the quoted "no reviewed family assignment" evidence after adding `mycustomwf`; (c) the `is_source_checkout` output `True False`; (d) the `git grep` output; (e) the quoted current `gate_workflow_disposition` absent-`index.md` branch; (f) the pre-edit bare `python3 -m pytest` summary line and sorted failing-test names.
  - Observed evidence:
    Execution HEAD sha: `93f78fd05ae8b4cdd3c4708749b1649f973a4bf7`
    (a) Fresh managed install gate:
    `res_a passed: True detail: all workflows dispositioned`
    (b) Gate after adding `mycustomwf`:
    `res_b passed: False evidence undispositioned: ["manifest command 'mycustomwf' has no reviewed family assignment (silent omission)"]`
    (c) `engine.is_source_checkout`:
    `c: True False`
    (d) `git grep -n -e build_inventory -e _COMMAND_FAMILY -e InventoryError -- agent_workflows tests`:
    ```
    agent_workflows/layout_inventory.py:48:class InventoryError(Exception):
    agent_workflows/layout_inventory.py:121:        raise InventoryError(f"--root requires LABEL=PATH, got: {value!r}")
    agent_workflows/layout_inventory.py:124:        raise InventoryError(f"unsafe root label: {label!r}")
    agent_workflows/layout_inventory.py:1002:            raise InventoryError(
    agent_workflows/layout_inventory.py:1022:    except InventoryError as exc:
    agent_workflows/migration_inventory.py:120:class InventoryError(ValueError):
    agent_workflows/migration_inventory.py:206:_COMMAND_FAMILY: Dict[str, str] = {
    agent_workflows/migration_inventory.py:212:    # (`_command_disposition` raises `InventoryError` for an unassigned command), so a new manifest row
    agent_workflows/migration_inventory.py:422:    family = _COMMAND_FAMILY.get(cmd)
    agent_workflows/migration_inventory.py:424:        raise InventoryError(
    agent_workflows/migration_inventory.py:505:    raise InventoryError("row '{0}' is not a lens/persona catalog row".format(cmd))
    agent_workflows/migration_inventory.py:581:def build_inventory(source_root: Any) -> InventoryResult:
    agent_workflows/migration_inventory.py:584:    Raises :class:`InventoryError` only for a programmer error (an unassigned command family); an
    agent_workflows/migration_inventory.py:822:            raise InventoryError("unknown lens concern '{0}'".format(concern))
    agent_workflows/migration_inventory.py:827:            raise InventoryError("unknown persona '{0}'".format(persona))
    agent_workflows/migration_inventory.py:1004:                raise InventoryError("rollup requested unknown lens '{0}'".format(m))
    agent_workflows/migration_inventory.py:1060:            raise InventoryError("unknown view '{0}'".format(view))
    agent_workflows/migration_inventory.py:1076:        raise InventoryError(
    agent_workflows/migration_inventory.py:1178:    result = build_inventory(source_root)
    agent_workflows/migration_inventory.py:1193:    "InventoryError",
    agent_workflows/migration_inventory.py:1194:    "build_inventory",
    agent_workflows/release_readiness.py:479:    set from :func:`migration_inventory.build_inventory` against ``.aw/system/workflows``.
    agent_workflows/release_readiness.py:518:            result = migration_inventory.build_inventory(wf_dir)
    agent_workflows/release_readiness.py:519:        except migration_inventory.InventoryError as err:
    tests/test_release_readiness_producers.py:224:    """Arm (h): manifest row with unassigned command fails (InventoryError) without raising."""
    ```
    (e) Quoted `gate_workflow_disposition` absent-`index.md` branch from `4bw2u5`:
    ```python
        manifest_rel = f"{wf_rel}/index.md"
        manifest_file = wf_dir / "index.md"
        if not manifest_file.is_file():
            return _not_applicable(
                name="workflow_disposition",
                detail=f"workflow manifest missing: {manifest_rel}",
                path=manifest_rel,
                extra_evidence={"undispositioned": []},
            )
    ```
    (f) Baseline bare `python3 -m pytest` summary line:
    `748 passed in 55.07s`
    Sorted failing-test names: `[]` (0 test failures).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the pre-E-03 RED output of `python3 -m pytest -o addopts="" -v tests/test_release_readiness_repo_local_workflows.py` showing per-case outcomes matching E-02's expected RED set (cases 1, 3, 4, 5, 6 failing for the stated reasons; case 2 passing) and `git diff --stat` showing only the new test module changed at that point.
  - Observed evidence:
    Pre-E-03 RED output of `python3 -m pytest -o addopts="" -v tests/test_release_readiness_repo_local_workflows.py`:
    ```
    FAILED tests/test_release_readiness_repo_local_workflows.py::test_cli_managed_repo_custom_row_is_go - AssertionError: assert 'workflow_disposition' not in ['workflow_disposition']
    FAILED tests/test_release_readiness_repo_local_workflows.py::test_managed_repo_without_custom_rows_reports_no_repo_local - KeyError: 'repo_local'
    FAILED tests/test_release_readiness_repo_local_workflows.py::test_build_inventory_default_still_raises - TypeError: build_inventory() got an unexpected keyword argument 'allow_repo_local'
    FAILED tests/test_release_readiness_repo_local_workflows.py::test_repo_local_mode_keeps_other_findings - AssertionError: assert False
    FAILED tests/test_release_readiness_repo_local_workflows.py::test_managed_repo_custom_command_is_repo_local_not_failing - AssertionError: assert False is True
    PASSED tests/test_release_readiness_repo_local_workflows.py::test_source_checkout_custom_command_still_fails_closed
    5 failed, 1 passed in 3.22s
    ```
    `git status --short`:
    `?? tests/test_release_readiness_repo_local_workflows.py`
    (only the new test module created).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `git diff -- agent_workflows/migration_inventory.py` and the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_release_readiness_repo_local_workflows.py -k build_inventory_default_still_raises`.
  - Observed evidence:
    `git diff -- agent_workflows/migration_inventory.py`:
    ```diff
    diff --git a/agent_workflows/migration_inventory.py b/agent_workflows/migration_inventory.py
    index ae4ac4f68..9a62bd1c4 100644
    --- a/agent_workflows/migration_inventory.py
    +++ b/agent_workflows/migration_inventory.py
    @@ -203,6 +203,9 @@ class Disposition:
     # Family assignment for each COMMAND row, from the plan's "Initial disposition by family" table. This
     # is the reviewed grouping the Order freezes. Every non-catalog manifest command must appear here so
     # the completeness tool can prove no command is unassigned.
    +#
    +# This table is this toolkit's own catalog. Fail-closed remains the default and the source-checkout
    +# behavior; only a managed repository's own workflow rows are reported as repo-local (backlog ufawpb).
     _COMMAND_FAMILY: Dict[str, str] = {
         "release-review": "release review modes",
         "release-review-plan": "release review modes",
    @@ -540,6 +543,7 @@ class InventoryResult:

         dispositions: Dict[str, Disposition]
         findings: List[str] = field(default_factory=list)
    +    repo_local: List[str] = field(default_factory=list)

         @property
         def ok(self) -> bool:
    @@ -553,6 +557,7 @@ class InventoryResult:
                     s: d.to_dict() for s, d in sorted(self.dispositions.items())
                 },
                 "findings": list(self.findings),
    +            "repo_local": list(self.repo_local),
             }


    @@ -578,12 +583,15 @@ def enumerate_subjects(workflows: Sequence[Workflow]) -> Dict[str, List[Workflow
         return {"commands": commands, "lenses": lenses, "personas": personas}


    -def build_inventory(source_root: Any) -> InventoryResult:
    +def build_inventory(
    +    source_root: Any, *, allow_repo_local: bool = False
    +) -> InventoryResult:
         """Build the complete disposition inventory from the live manifest + the conformance package.

    -    Raises :class:`InventoryError` only for a programmer error (an unassigned command family); an
    -    invalid vocabulary value or a missing canonical target is a FINDING, not an exception, so the
    -    completeness tool reports every problem at once instead of aborting on the first.
    +    Raises :class:`InventoryError` only for a programmer error (an unassigned command family)
    +    when ``allow_repo_local`` is False; an invalid vocabulary value or a missing canonical target
    +    is a FINDING, not an exception, so the completeness tool reports every problem at once instead
    +    of aborting on the first.
         """

         root = _workflows_root(source_root)
    @@ -592,6 +600,7 @@ def build_inventory(source_root: Any) -> InventoryResult:

         dispositions: Dict[str, Disposition] = {}
         findings: List[str] = []
    +    repo_local: List[str] = []

         def _add(d: Disposition) -> None:
             if d.subject in dispositions:
    @@ -600,6 +609,9 @@ def build_inventory(source_root: Any) -> InventoryResult:
             dispositions[d.subject] = d

         for w in subjects["commands"]:
    +        if allow_repo_local and w.command not in _COMMAND_FAMILY:
    +            repo_local.append(w.command)
    +            continue
             _add(_command_disposition(w))
         for w in subjects["lenses"]:
             _add(_catalog_disposition(w))
    @@ -607,14 +619,20 @@ def build_inventory(source_root: Any) -> InventoryResult:
             _add(_catalog_disposition(w))
         _add(_conformance_disposition())

    -    findings.extend(check_completeness(dispositions, workflows, root))
    -    return InventoryResult(dispositions=dispositions, findings=findings)
    +    repo_local.sort()
    +    findings.extend(
    +        check_completeness(dispositions, workflows, root, repo_local=repo_local)
    +    )
    +    return InventoryResult(
    +        dispositions=dispositions, findings=findings, repo_local=repo_local
    +    )


     def check_completeness(
         dispositions: Mapping[str, Disposition],
         workflows: Sequence[Workflow],
         source_root: Any,
    +    repo_local: Sequence[str] = (),
     ) -> List[str]:
         """PROVE the inventory is complete + valid. Returns a list of findings (empty = complete).

    @@ -633,10 +651,13 @@ def check_completeness(

         manifest_subjects = {w.command for w in workflows}
         all_subjects = set(manifest_subjects) | {CONFORMANCE_TARGET}
    +    repo_local_set = set(repo_local)

         # 1+2) every manifest row + the conformance file dispositioned exactly once, none omitted.
         for subj in sorted(all_subjects):
             if subj not in dispositions:
    +            if subj in repo_local_set:
    +                continue
                 findings.append(
                     "subject '{0}' has NO disposition (silent omission)".format(subj)
                 )
    ```
    GREEN output of `python3 -m pytest -o addopts="" -v tests/test_release_readiness_repo_local_workflows.py -k build_inventory_default_still_raises`:
    ```
    tests/test_release_readiness_repo_local_workflows.py::test_build_inventory_default_still_raises PASSED [100%]
    1 passed, 5 deselected in 0.34s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `git diff -- agent_workflows/release_readiness.py` hunk for `gate_workflow_disposition` and the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_release_readiness_repo_local_workflows.py` showing all six cases passing.
  - Observed evidence:
    `git diff -- agent_workflows/release_readiness.py`:
    ```diff
    diff --git a/agent_workflows/release_readiness.py b/agent_workflows/release_readiness.py
    index ae71b6a6f..91b3fd756 100644
    --- a/agent_workflows/release_readiness.py
    +++ b/agent_workflows/release_readiness.py
    @@ -478,6 +478,12 @@ def gate_workflow_disposition(
         When ``undispositioned`` is None (the default), computes the undispositioned
         set from :func:`migration_inventory.build_inventory` against ``.aw/system/workflows``.
         Explicit injection (including an empty sequence) bypasses filesystem inspection.
    +
    +    In the toolkit's own source checkout (``engine.is_source_checkout`` is True),
    +    every manifest command must carry a reviewed family in the toolkit catalog
    +    (fail-closed). In a managed repository, rows outside the toolkit catalog are
    +    dispositioned as repo-local, reported by name in detail and evidence, and do
    +    not fail readiness (backlog ufawpb).
         """
         if undispositioned is not None:
             undone = [str(f) for f in undispositioned]
    @@ -512,30 +518,44 @@ def gate_workflow_disposition(
             )

         try:
    -        from agent_workflows import migration_inventory
    +        from agent_workflows import engine, migration_inventory

    +        allow_repo_local = not engine.is_source_checkout(root)
             try:
    -            result = migration_inventory.build_inventory(wf_dir)
    +            result = migration_inventory.build_inventory(
    +                wf_dir, allow_repo_local=allow_repo_local
    +            )
             except migration_inventory.InventoryError as err:
                 undone = [str(err)]
                 return GateResult(
                     name="workflow_disposition",
                     passed=False,
                     detail=f"{len(undone)} undispositioned",
    -                evidence={"undispositioned": undone},
    +                evidence={"undispositioned": undone, "repo_local": []},
                 )

             undone = [str(f) for f in result.findings]
    +        repo_local = sorted(result.repo_local)
             passed = not undone
    +        if passed:
    +            if repo_local:
    +                detail = (
    +                    f"all workflows dispositioned; {len(repo_local)} repo-local "
    +                    f"workflow(s) outside the toolkit catalog: {', '.join(repo_local)}"
    +                )
    +            else:
    +                detail = "all workflows dispositioned"
    +        else:
    +            detail = f"{len(undone)} undispositioned"
    +
             return GateResult(
                 name="workflow_disposition",
                 passed=passed,
    -            detail="all workflows dispositioned"
    -            if passed
    -            else f"{len(undone)} undispositioned",
    +            detail=detail,
                 evidence={
                     "undispositioned": undone,
                     "dispositions": len(result.dispositions),
    +                "repo_local": repo_local,
                 },
             )
         except (SystemExit, Exception) as exc:
    ```
    GREEN output of `python3 -m pytest -o addopts="" -v tests/test_release_readiness_repo_local_workflows.py`:
    ```
    tests/test_release_readiness_repo_local_workflows.py::test_source_checkout_custom_command_still_fails_closed PASSED [ 16%]
    tests/test_release_readiness_repo_local_workflows.py::test_build_inventory_default_still_raises PASSED [ 33%]
    tests/test_release_readiness_repo_local_workflows.py::test_repo_local_mode_keeps_other_findings PASSED [ 50%]
    tests/test_release_readiness_repo_local_workflows.py::test_cli_managed_repo_custom_row_is_go PASSED [ 66%]
    tests/test_release_readiness_repo_local_workflows.py::test_managed_repo_custom_command_is_repo_local_not_failing PASSED [ 83%]
    tests/test_release_readiness_repo_local_workflows.py::test_managed_repo_without_custom_rows_reports_no_repo_local PASSED [100%]
    6 passed in 2.76s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `git diff -- tests/test_release_readiness_producers.py` (fixture and docstring only, assertions unchanged) and the GREEN output of `python3 -m pytest -o addopts="" -q tests/test_release_readiness_producers.py`.
  - Observed evidence:
    `git diff -- tests/test_release_readiness_producers.py`:
    ```diff
    diff --git a/tests/test_release_readiness_producers.py b/tests/test_release_readiness_producers.py
    index adf5ee16d..aa3df4122 100644
    --- a/tests/test_release_readiness_producers.py
    +++ b/tests/test_release_readiness_producers.py
    @@ -221,9 +221,13 @@ def test_disposition_missing_conformance_file_fails_gate(
     def test_disposition_unassigned_command_fails_without_raising(
         tmp_path: Path, monkeypatch: pytest.MonkeyPatch
     ) -> None:
    -    """Arm (h): manifest row with unassigned command fails (InventoryError) without raising."""
    +    """Arm (h): manifest row with unassigned command in source checkout fails (InventoryError) without raising (ufawpb)."""
    +    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    +    setup_minimal_workflows_tree(tmp_path)
    +    (tmp_path / "pyproject.toml").write_text(
    +        '[project]\nname = "agent-workflows"\n', encoding="utf-8"
    +    )
    +    (tmp_path / ".aw" / "system" / "VERSION").write_text("1.0.0\n", encoding="utf-8")
         index_md = tmp_path / ".aw" / "system" / "workflows" / "index.md"
         index_md.write_text(
             "# Workflows\n"
    ```
    GREEN output of `python3 -m pytest -o addopts="" -q tests/test_release_readiness_producers.py`:
    `26 passed in 2.22s`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `git diff -- docs/recovery.md CHANGELOG.md` and the dash-scan output over the added lines showing 0 matches.
  - Observed evidence:
    `git diff -- docs/recovery.md CHANGELOG.md`:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 5b43b4da4..07464eb46 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: `aw releases readiness` no longer reports a false `workflow_disposition` NO-GO in a managed repository that adds its own workflows.
     - Fixed: Commands acting on a record stored in a companion records repository now find the owning repository, so plan dependency checks, spec history, id6 collision checks, and rename hints work there.
     - Fixed: `aw install` no longer leaves two project configs when switching between `private-target` and `completely-clean-target`/`local-only`. It refuses by default and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves config, records and install history and retires the old files, and companion switches still refuse.
     - Fixed: `aw runs decisions` and `aw runs questions` now emit a JSON object under `--agent` and `--json`, and `aw runs evidence`, `aw runs verify-ledger` and `aw runs show` report the ledger as a repository-relative path.
    diff --git a/docs/recovery.md b/docs/recovery.md
    index 17aea89de..2c2599057 100644
    --- a/docs/recovery.md
    +++ b/docs/recovery.md
    @@ -58,6 +58,12 @@ does not force `NO-GO`, and is named in a WARNING line and as warning diagnostic
     and `residual_risk` gates are never not-applicable. The accepted risk is that an input deleted by
     mistake reads not-applicable, so review the WARNING line.

    +In a managed repository, manifest rows outside the toolkit's reviewed catalog (normally the
    +workflows the repository added itself, but also any toolkit row the running `aw` version does not
    +know, for example after a version skew between the installed tree and the CLI) are listed by name
    +as repo-local by the `workflow_disposition` gate and do not force `NO-GO`, so review that list,
    +while in the toolkit's own source checkout every command must carry a reviewed disposition.
    +
     Run the read-only report from the CLI:
    ```
    Dash scan count in added lines: 0 matches (\u2014 and \u2013).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste (1) the targeted pytest summary line with 0 failures; (2) from the fresh `mr2` scratch install with `mycustomwf` added (code path: `engine.install_into_repo`, then `release_readiness.gate_workflow_disposition`), the gate's `passed`, `detail` and `evidence["repo_local"]`; (3) the same gate on this checkout; (4) the dash-scan result; (5) the `aw sanitize --agent` record; (6) the bare `python3 -m pytest` summary line and by-name comparison against the E-01(f) baseline; (7) the post-cleanup `git status --porcelain`.
  - Observed evidence:
    (1) Targeted pytest:
    `86 passed in 20.55s` (0 failures)
    (2) Fresh `mr2` scratch install with `mycustomwf`:
    `passed: True`
    `detail: all workflows dispositioned; 1 repo-local workflow(s) outside the toolkit catalog: mycustomwf`
    `evidence["repo_local"]: ['mycustomwf']`
    (3) Same gate on this checkout:
    `passed: True`
    `detail: all workflows dispositioned`
    `evidence["repo_local"]: []`
    (4) Dash scan count on added docs and changelog lines: 0 matches
    (5) `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5446,"findings":0,"evidence":["leak-scan"],"next":null}`
    (6) Bare `python3 -m pytest`:
    `748 passed in 26.66s` (0 failures, compared by name against E-01 baseline)
    (7) Post-cleanup `git status --porcelain`:
    ```
     M CHANGELOG.md
     M agent_workflows/migration_inventory.py
     M agent_workflows/release_readiness.py
     M docs/recovery.md
     M tests/test_release_readiness_producers.py
    ?? tests/test_release_readiness_repo_local_workflows.py
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit snhhw2 -- <paths>` (never `git add -A`), never push, and paste actual runner output for every test claim. The E-01/E-07 scratch installs live under the gitignored `.aw/state/scratch-snhhw2/` and are never committed.

SCOPE FENCE. `gate_workflow_disposition` is also edited by `4bw2u5` (this plan's declared dependency); preserve its not-applicable branch. Do not touch `_COMMAND_FAMILY` entries, `_FAMILY_DEFAULTS`, release-review bodies, `RELEASING.md`, or the installer. An out-of-scope edit that proves necessary is made and justified with `--scope-reason` at finalize.

RELEASE GATE. Inherits `- Blocks-Release: next` from backlog `ufawpb` (a live `bug`).

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all seven `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
