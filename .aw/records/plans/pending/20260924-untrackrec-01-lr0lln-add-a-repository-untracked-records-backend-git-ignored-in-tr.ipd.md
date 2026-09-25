# IPD: Add a repository-untracked records backend (git-ignored in-tree .aw/records)

- Date: 2026-09-24
- Kind: child
- Concern: There is no way to keep AW records inside the target working tree without tracking them: `repository` commits them, and `home`/`companion` move them out of the tree. Users who want in-tree, editor-visible, never-committed records have no supported backend.
- Scope: Add one records backend value `repository-untracked`, resolve it to `<target>/.aw/records` with an ignored Git policy and honest `unversioned` durability, write an anchored `/records/` line into the framework-owned `.aw/.gitignore` at install, keep the record scanners able to see a git-ignored records root, warn that such records are not durable across clones, and amend the canonical storage spec.
- Scope-Paths: agent_workflows/project_schema.py, agent_workflows/project_context.py, agent_workflows/storage.py, agent_workflows/install_wizard.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/artifact_core.py, tests/test_project_context.py, tests/test_records_untracked_backend.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: low
- Id: lr0lln
- From-Backlog: hsixiz
- Set: untrackrec
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog hsixiz; re-measured the backend enum and resolver branches, and probed that a git-ignored `.aw/records/` makes `aw attention` report zero items.

## Goal

Offer `--records-backend repository-untracked`: records live at `<target>/.aw/records/` like `repository`, but git ignores them, AW never stages them, the durability state honestly reads `unversioned`, and `aw` tells the user these records do not survive a fresh clone.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Backend value and resolution

- [ ] E-01 Add `REPOSITORY_UNTRACKED = "repository-untracked"` to `project_schema.RecordsBackend` (so `RECORDS_BACKENDS` and every `choices=[r.value for r in RecordsBackend]` flag pick it up), and in `project_context.resolve_project_context` resolve it to: records root `<repo>/.aw/records` (same branch as `REPOSITORY`), `git_policies[records] = GitPolicy.IGNORED`, `durability_state = DurabilityState.UNVERSIONED` (unless `records_root/.git` exists, then `LOCAL_GIT`, as today's non-repository branch does), `commit_destinations["records"] = None`. Extend the clean-delta invariant ("clean-delta delivery mode MUST NOT use 'repository' records backend") to refuse `repository-untracked` too, with the same `PathSecurityError`. Add tests to `tests/test_project_context.py` asserting each resolved value and the clean-delta refusal, plus `assertIn("repository-untracked", RECORDS_BACKENDS)` in `test_canonical_enums_and_constants`.
  - Depends on: none
  - Expected outcome: `resolve_project_context(..., records_backend="repository-untracked")` returns records root `<repo>/.aw/records`, git policy `ignored`, durability `unversioned`, records commit destination `None`; clean-delta plus this backend raises.
  - Execution state: pending

- [ ] E-02 In `install_wizard.ProjectPolicy`: when `records_backend == repository-untracked`, `__post_init__` sets `placements[records] = Placement.TARGET_IGNORED` and `git_policies[records] = GitPolicy.IGNORED` (overriding the preset's `target-tracked`), and `validate` refuses it with `clean-delta` exactly as it refuses `repository`. Update the `--records-backend` missing-field hint in `collect_policy_interactive` ("--records-backend (home | companion | repository)") and the two `--records-backend` help strings in `cli.py` ("repository (default), companion, home.") to name the new value. Test in `tests/test_records_untracked_backend.py`.
  - Depends on: E-01
  - Expected outcome: `ProjectPolicy(records_backend="repository-untracked").placements["records"] == "target-ignored"`; `ProjectPolicy(delivery_mode="clean-delta", records_backend="repository-untracked").validate()` raises `InvalidPolicyError`.
  - Execution state: pending

### Task group 2: Ignore rule and scanner visibility

- [ ] E-03 Add `engine.ensure_untracked_records_ignore(repo_root) -> bool`: call `_ensure_aw_gitignore(repo_root)` first, then append the ANCHORED line `/records/` (with a one-line comment naming the backend and that records are not durable across clones) to `.aw/.gitignore` if absent; return True iff it wrote. Anchored for the same reason `/inbox/` is anchored in `_AW_GITIGNORE_TEMPLATE`. Call it from `cli._run_install` in the block that calls `install_wizard.persist_project_policy`, only when `policy.records_backend == repository-untracked`. The default template is NOT changed, so `repository` installs are unaffected. Test: helper writes the line once (idempotent second call returns False), and `git check-ignore .aw/records/plans/pending/x.md` exits 0 in a temp repo after it runs.
  - Depends on: E-02
  - Expected outcome: `.aw/.gitignore` contains exactly one `/records/` line after two calls; git reports the records tree ignored; a `repository` backend repo's `.aw/.gitignore` has no `/records/` line.
  - Execution state: pending

- [ ] E-04 Keep scanners able to see an ignored records root. Measured: with `records/` in `.aw/.gitignore`, `artifact_core.get_ignored_dirs` returns `.aw/records`, `artifact_core.is_ignored_path` returns True for `.aw/records/plans/pending/x.ipd.md`, and `aw attention --format json` returns `"items": []` (the same repo without the rule lists the plan). In `artifact_core.get_ignored_dirs`, discard the exact entry `.aw/records` from the git-reported set (a whole-records ignore can only come from this backend; nested lanes stay excluded by the existing `"untracked" in rel_parts` rule and `DEFAULT_IGNORED_DIR_NAMES` `.aw/records/runs`). Test: in a temp repo with the E-03 rule and one pending plan, `is_ignored_path` is False for the plan, True for `.aw/records/prompts/untracked/x.md` and `.aw/records/runs/x/state.json`, and `attention` lists the plan. Show this test FAILING before the `get_ignored_dirs` change.
  - Depends on: E-03
  - Expected outcome: `aw attention` sees records under an ignored `.aw/records/`; untracked lanes and runs stay hidden.
  - Execution state: pending

### Task group 3: Warning, install, spec

- [ ] E-05 Warn about durability in both surfaces a user reads: (a) `storage.get_storage_status` gets a `repository-untracked` branch before the generic ones, keeping `durability_state` from observation (`unversioned`/`local-git`) and setting the recommendation to a string containing "not durable across clones" and naming `.aw/records/` as git-ignored; (b) `install_wizard.render_pre_write_plan` adds a yellow `[WARNING] Records are git-ignored in this working tree (repository-untracked); they are not durable across clones and are lost if this checkout is deleted.` line, and `cli._run_install` emits the same text via `term.status("warn", ...)` after writing the ignore rule. Test both strings.
  - Depends on: E-04
  - Expected outcome: `aw storage status` (text and `--format json` recommendation) and the install plan both carry "not durable across clones" for this backend and not for `repository`.
  - Execution state: pending

- [ ] E-06 End-to-end install test: in a temp git repo run `python3 -m agent_workflows install <tmp> --preset private-target --records-backend repository-untracked --yes` (the flag shape `_run_install` already accepts), then assert exit 0, `.aw/config/project.json` has `"records_backend": "repository-untracked"`, `.aw/.gitignore` contains `/records/`, and `git -C <tmp> ls-files .aw/records` is empty. If any install step stages a record path with a raw `git add` and aborts on the ignore rule, route that call through `engine.git_add_optional` (the tolerant helper already used for ignored destinations) and name the call site in the evidence.
  - Depends on: E-05
  - Expected outcome: install succeeds, records exist on disk, nothing under `.aw/records` is tracked.
  - Execution state: pending

- [ ] E-07 Amend Section 5 of the canonical storage spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` with the `repository-untracked` contract: `records` may take `target-ignored` when this backend is explicitly selected; the path is in-tree, ignored by an anchored `/records/` line in `.aw/.gitignore`, never staged, observed as `unversioned`/`local-git` (never `repository-managed`), refused with clean-delta, and not durable across clones. Record the amendment via `python3 -m agent_workflows specs note <path> --message "..."` citing `lr0lln`.
  - Depends on: E-06
  - Expected outcome: the spec names `repository-untracked` and its workflow history carries a note citing `lr0lln`.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest`.
  - Depends on: E-07
  - Expected outcome: the summary line reports 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Backends are one enum, `project_schema.RecordsBackend` (`HOME`, `COMPANION`, `REPOSITORY`); `RECORDS_BACKENDS` and the install flags derive from it, so adding a member propagates.
- The installer owns `.aw/.gitignore` and never the root `.gitignore` (`engine._ensure_aw_gitignore` docstring: "it is NOT the user's root `.gitignore`"). Patterns that could match at depth are anchored (`/inbox/`).
- Placement vocabulary already has `target-ignored` (`project_schema.Placement.TARGET_IGNORED`) and git policy `ignored` (`GitPolicy.IGNORED`); no new enum beyond the backend value is needed.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- F-01: `project_context.resolve_project_context` maps anything that is not `repository`/`companion` to the HOME records root (`else:  # HOME`), so an unknown backend would silently land in AW_HOME; the new value needs its own branch.
- F-02 (measured, probe under `/tmp/opencode/g2/probe-untrackrec/`): with `.aw/.gitignore` = `records/`, `aw attention --format json` printed `"items": []`; after removing the rule the same repo listed `abc123` as `ready`. Cause: `artifact_core.get_ignored_dirs` returned `.aw/records`. `plans_index.scan_plans` rooted at the plans dir still found the plan, so the blindness is in repo-rooted scanners. This is why E-04 exists.
- F-03: the storage spec named in the task (`20260809-2211-01-...storage-wizard-and-state.spec.md`) is `Status: superseded` by `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (`Status: implemented`, `Canonical: true`). Amending a superseded spec changes no live contract, so E-07 amends the canonical successor.
- F-04: `record_producers.resolve_record_routing` sets `allow_git = backend == RecordsBackend.REPOSITORY.value`, so the new backend already gets no commit destination; no change needed there.

## Proposed changes (ordered, validatable)

1. Enum value plus resolver branch (E-01).
2. Policy placement override and flag text (E-02).
3. Anchored ignore rule written only for this backend (E-03).
4. Scanner fix so ignored records remain visible (E-04).
5. Durability warning in storage status and install (E-05).
6. End-to-end install check (E-06).
7. Spec amendment (E-07), then the suite (E-08).

## Deferred / out of scope (with reason)

- Migration to or from `repository-untracked` (`aw migrate --target-backend`, whose `choices=["home", "companion", "repository"]` is hardcoded in `cli.py`): moving records between tracked and ignored states is a separate, riskier flow.
  - Carrier-Declined: low-priority feature; file a backlog item only if a user asks for backend cutover.
- An interactive wizard menu entry and a dedicated preset: the flag is the smallest surface; presets are a spec-level table.
  - Carrier-Declined: flag-only is sufficient for the backlog ask.
- An `aw doctor` check that flags tracked files under an ignored records root.
  - Carrier-Declined: `git add -f` bypass is already documented as advisory in the `aw:untracked` gitignore section; no evidence of demand.

## Scope check

- Over-scope: none.
- Under-scope: E-04 is beyond the literal ask but required: without it the backend makes `aw attention` go blind (F-02).

## Required tests / validation

- `tests/test_project_context.py`: resolution values and clean-delta refusal (E-01).
- `tests/test_records_untracked_backend.py` (new): policy override (E-02), ignore rule (E-03), scanner visibility (E-04, shown failing first), warnings (E-05), end-to-end install (E-06).
- Bare suite (E-08).

## Spec / documentation sync

- Amend `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 5 (declared in Scope-Paths). Why: the spec currently restricts `target-ignored` to `config_local` and `state_runtime`, so this backend would violate the written contract without the amendment. The superseded `20260809-2211-01` spec is left untouched (F-03).

## Open questions

### OQ-01: Which spec file to amend

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: The task names the superseded `20260809-2211-01` spec; default is to amend its canonical successor `20260810-1447-01` (F-03). The maintainer may redirect at review.

### OQ-02: Backend value name

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default `repository-untracked`, matching the backlog title and the existing `*-untracked` placement vocabulary (`home-untracked`, `companion-untracked`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_project_context.py -q` output showing the new resolution tests passing, and the passing names of the tests asserting records root `.aw/records`, git policy `ignored`, durability `unversioned`, commit destination `None`, and the clean-delta `PathSecurityError`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the passing output of the policy tests in `tests/test_records_untracked_backend.py` (placement `target-ignored`, clean-delta `InvalidPolicyError`), and `python3 -m agent_workflows install --help` output showing `repository-untracked` in the `--records-backend` choices.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste passing test output for the ignore-rule tests, plus `grep -c '^/records/$' <tmp>/.aw/.gitignore` printing `1` after two helper calls and `git -C <tmp> check-ignore -v .aw/records/plans/pending/x.md` naming `.aw/.gitignore`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the scanner-visibility test FAILING with the `get_ignored_dirs` change reverted (stash-free: comment out the discard line, run, restore), then PASSING with it; the passing run must include the `attention` assertion listing the plan and the untracked/runs paths still ignored.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste passing test output asserting "not durable across clones" in the `get_storage_status` recommendation and in `render_pre_write_plan` output for `repository-untracked`, and its absence for `repository`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste passing output of the end-to-end install test, including the asserted empty `git ls-files .aw/records` result and `"records_backend": "repository-untracked"` in `project.json`; name any `git_add_optional` call site changed, or state none was needed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff -- .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` showing the Section 5 edit and the new workflow-history note citing `lr0lln`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only Scope-Paths files through `aw commit lr0lln -- <paths>`; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
