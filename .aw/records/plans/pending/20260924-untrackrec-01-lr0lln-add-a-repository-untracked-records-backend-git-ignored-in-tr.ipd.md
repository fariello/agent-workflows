# IPD: Add a repository-untracked records backend (git-ignored in-tree .aw/records)

- Date: 2026-09-24
- Kind: child
- Concern: There is no way to keep AW records inside the target working tree without tracking them: `repository` commits them, and `home`/`companion` move them out of the tree. Users who want in-tree, editor-visible, never-committed records have no supported backend.
- Scope: Add one records backend value `repository-untracked`, resolve it to `<target>/.aw/records` with an ignored Git policy and honest `unversioned` durability, repair the pre-existing `record_producers.get_git_owner` crash the new value would hit, write an anchored `/records/` line into the framework-owned `.aw/.gitignore` at install, keep the record scanners able to see a git-ignored records root, refuse the backend on a repo that already TRACKS records, warn that such records are not durable across clones, and amend the canonical storage spec.
- Scope-Paths: agent_workflows/project_schema.py, agent_workflows/project_context.py, agent_workflows/storage.py, agent_workflows/install_wizard.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/artifact_core.py, agent_workflows/record_producers.py, agent_workflows/project_layout.py, tests/test_project_context.py, tests/test_records_untracked_backend.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- Id: lr0lln
- From-Backlog: hsixiz
- Set: untrackrec
- Order: 1
- Highest E allocated: 13
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us

## Workflow history
- 2026-09-25 reviewed (aw set): plan-review complete: PR-501..PR-510 all fixed; 13 items, 13:13 E/V bijection; OQ-01/OQ-02 resolved from evidence; findings and decisions in .aw/records/reviews/20260924-untrackrec-01-lr0lln-...review.md

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501..PR-510, all FIXED. Added E-02 (repair the pre-existing `get_git_owner` `AttributeError` the new value hits), E-03 (the storage-boundary and layout-materialization dispatch sites), E-06 (refuse the backend on a repo that already TRACKS records, which gitignore cannot untrack), and the `aw setup` half of E-11; scoped E-08's `get_ignored_dirs` discard to the repo's RECORDED backend so a user's own `.aw/records/` ignore is not overridden; required E-04's placement override to survive an explicit preset fill; line-anchored E-07's presence test; split for right-sizing into 13 items with a 13:13 E/V bijection; corrected `Highest E allocated` (IPD-I304); rewrote the gate with the full execution contract; resolved OQ-01 and OQ-02 from in-tree evidence and carried both, clearing an error-severity `check.ipd-uncarried-obligation`. Findings and five recorded decisions in `.aw/records/reviews/20260924-untrackrec-01-lr0lln-...review.md`.
- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog hsixiz; re-measured the backend enum and resolver branches, and probed that a git-ignored `.aw/records/` makes `aw attention` report zero items.

## Goal

Offer `--records-backend repository-untracked`: records live at `<target>/.aw/records/` like `repository`, but git ignores them, AW never stages them, the durability state honestly reads `unversioned`, and `aw` tells the user these records do not survive a fresh clone.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Backend value and resolution

- [ ] E-01 Add `REPOSITORY_UNTRACKED = "repository-untracked"` to `project_schema.RecordsBackend` (so `RECORDS_BACKENDS` and every `choices=[r.value for r in RecordsBackend]` flag pick it up), and in `project_context.resolve_project_context` resolve it to: records root `<repo>/.aw/records` (same branch as `REPOSITORY`), `git_policies[records] = GitPolicy.IGNORED`, `durability_state = DurabilityState.UNVERSIONED` (unless `records_root/.git` exists, then `LOCAL_GIT`, as today's non-repository branch does), `commit_destinations["records"] = None`. Extend the clean-delta invariant ("clean-delta delivery mode MUST NOT use 'repository' records backend") to refuse `repository-untracked` too, with the same `PathSecurityError`. FOUR SEPARATE BRANCHES in that one function must each be extended, because each tests `== RecordsBackend.REPOSITORY.value` and the new value would otherwise fall into the `else: # HOME` path (F-01): the records-root branch, the `git_policies[RootClass.RECORDS]` ternary, the durability branch, and the `records_dest` branch. Add tests to `tests/test_project_context.py` asserting each resolved value and the clean-delta refusal, plus `assertIn("repository-untracked", RECORDS_BACKENDS)` in `test_canonical_enums_and_constants` (the test already asserts the other three by name, so follow its shape).
  - Depends on: none
  - Expected outcome: `resolve_project_context(..., records_backend="repository-untracked")` returns records root `<repo>/.aw/records`, git policy `ignored`, durability `unversioned`, records commit destination `None`; clean-delta plus this backend raises.
  - Execution state: pending

- [ ] E-02 Repair `record_producers.get_git_owner`, which CRASHES on this backend, before anything routes through it. Measured at review: its `elif` reads `elif "companion" in backend or backend == RecordsBackend.COMPANION_TRACKED.value:` and `RecordsBackend` has NO `COMPANION_TRACKED` member (`COMPANION_TRACKED` is a `Placement`, not a `RecordsBackend`), so the attribute lookup raises `AttributeError: type object 'RecordsBackend' has no attribute 'COMPANION_TRACKED'` for EVERY backend that reaches it. It is latent today only because Python short-circuits the `or` for `companion` and the `if` above catches `repository`; `home` already crashes and so would `repository-untracked`. Delete the dead `COMPANION_TRACKED` disjunct (keep the `"companion" in backend` substring test) and add an explicit `repository-untracked` case returning `None`, since nothing may stage these records. Test both in `tests/test_records_untracked_backend.py`: `get_git_owner("plans", ...)` returns `None` for `repository-untracked` AND for `home` (the pre-existing crash), and still `"target"` for `repository` and `"companion"` for `companion`.
  - Depends on: E-01
  - Expected outcome: `get_git_owner` returns `None` for `repository-untracked` and `home`, unchanged for `repository`/`companion`; no `AttributeError` on any member of `RECORDS_BACKENDS`.
  - Execution state: pending

- [ ] E-03 Route the backend through the two remaining resolvers that dispatch on it, so it is not silently mis-served. (a) `storage.validate_storage_boundaries` refuses an in-target path for `HOME`/`COMPANION`; `repository-untracked` is legitimately in-target, so it must NOT be added to that tuple - add a comment stating that explicitly so a later reader does not "fix" the omission. (b) `project_layout.materialize_project_layout` creates the records dir for `REPOSITORY` and for the `(HOME, COMPANION)` tuple; add `REPOSITORY_UNTRACKED` so the dir is created (it is in-tree and must exist on disk). Test that `materialize_project_layout` with this backend creates `<repo>/.aw/records` and that `get_storage_status` does not raise `StorageSecurityError`.
  - Depends on: E-02
  - Expected outcome: `materialize_project_layout(..., repository-untracked)` creates the in-tree records dir; `validate_storage_boundaries` accepts the in-target path and carries the comment saying why.
  - Execution state: pending

- [ ] E-04 In `install_wizard.ProjectPolicy`: when `records_backend == repository-untracked`, `__post_init__` sets `placements[records] = Placement.TARGET_IGNORED` and `git_policies[records] = GitPolicy.IGNORED` (overriding the preset's `target-tracked`), and `validate` refuses it with `clean-delta` exactly as it refuses `repository`. NOTE the override must survive `__post_init__`'s existing guard, which fills `placements`/`git_policies` from the preset ONLY when they are empty: an explicitly-passed `placements` dict is left alone today, so the backend override has to run AFTER that fill and unconditionally, or a caller passing preset placements (which `resolve_policy_noninteractive` does, `placements=pls, git_policies=gps`) keeps `target-tracked`. The dataclass is `frozen=True`, so use `object.__setattr__` as the existing code does.
  - Depends on: E-03
  - Expected outcome: `ProjectPolicy(records_backend="repository-untracked").placements["records"] == "target-ignored"`, AND the same with explicit preset `placements=`/`git_policies=` passed in; `ProjectPolicy(delivery_mode="clean-delta", records_backend="repository-untracked").validate()` raises `InvalidPolicyError`.
  - Execution state: pending

- [ ] E-05 Name the new value in the three user-facing flag texts that enumerate backends: the `--records-backend` missing-field hint in `install_wizard.resolve_policy_noninteractive` (currently the string `"--records-backend (home | companion | repository)"`) and the two `--records-backend` help strings in `cli.py` (both currently `"Select records storage location: repository (default), companion, home."`). Do NOT touch `aw migrate --target-backend`, whose `choices=["home", "companion", "repository"]` is deliberately out of scope (see Deferred). Test the `install --help` output and the hint string.
  - Depends on: E-04
  - Expected outcome: `python3 -m agent_workflows install --help` lists `repository-untracked` in the `--records-backend` choices; the noninteractive hint names it; `aw migrate --help` still offers only the three old values.
  - Execution state: pending

### Task group 2: Ignore rule and scanner visibility

- [ ] E-06 REFUSE the backend on a repo that already TRACKS records, because selecting it there produces a silently broken half-state rather than an ignored tree. Measured at review in a temp repo: with `.aw/records/plans/pending/p.ipd.md` already committed and `/records/` then added to `.aw/.gitignore`, `git ls-files .aw/records` STILL lists the file and `git status` still reports it modified (gitignore does not untrack), while a NEW file gets `git add` exit 1 with "The following paths are ignored". So the repo ends with some records tracked, some untrackable, and no command that reconciles them. In `install_wizard.ProjectPolicy.validate` (or a helper it calls, since `validate` has no repo path - pass the repo root from `cli._run_install` before `persist_project_policy` if needed), refuse with a clear `InvalidPolicyError` naming `aw migrate` when `git -C <repo> ls-files .aw/records` is non-empty and the requested backend is `repository-untracked`. Test: refusal on a repo with a tracked record; acceptance on a repo with none.
  - Depends on: E-05
  - Expected outcome: selecting the backend on a records-tracking repo fails BEFORE any write, with a message naming the tracked path and the migration route; a clean repo is accepted.
  - Execution state: pending

- [ ] E-07 Add `engine.ensure_untracked_records_ignore(repo_root) -> bool`: call `_ensure_aw_gitignore(repo_root)` first, then append the ANCHORED line `/records/` (with a one-line comment naming the backend and that records are not durable across clones) to `.aw/.gitignore` if absent; return True iff it wrote. Anchored for the same reason `/inbox/` is anchored in `_AW_GITIGNORE_TEMPLATE`. Match the presence test LINE-ANCHORED (`re.search(r"(?m)^/records/[ \t]*$", text)`), exactly as `_ensure_aw_gitignore` does for `/inbox/` and for the same stated reason: the explanatory comment you are adding contains the substring `records/`, so a substring test would report the line present having written only the comment. Call it from `cli._run_install` in the block that calls `install_wizard.persist_project_policy`, only when `policy.records_backend == repository-untracked`. The default template is NOT changed, so `repository` installs are unaffected.
  - Depends on: E-06
  - Expected outcome: `.aw/.gitignore` contains exactly one `/records/` line after two calls (second returns False); `git check-ignore .aw/records/plans/pending/x.md` exits 0; a `repository` backend repo's `.aw/.gitignore` has no `/records/` line.
  - Execution state: pending

- [ ] E-08 Keep scanners able to see an ignored records root, SCOPED TO THIS BACKEND. Measured at review in a temp repo with `/records/` in `.aw/.gitignore`: `artifact_core.get_ignored_dirs` returns `.aw/records` in its set, `is_ignored_path` returns True for `.aw/records/plans/pending/x.ipd.md`, and `aw attention --format json` returns `"items": []` (F-02). The fix is to discard the exact entry `.aw/records` from the git-reported set - but it MUST be conditional on the repo actually having this backend configured, NOT unconditional. Reason, measured at review: a user whose OWN root `.gitignore` says `.aw/records/` (or `.aw/`) with NO `repository-untracked` policy gets the same `.aw/records` entry from git, so an unconditional discard would start scanning a tree that user deliberately excluded, reversing their choice in a function that has no idea why the path is ignored. Gate it on `project_context.read_project_identity(repo_root)["records_backend"] == "repository-untracked"` - the ONE reader for the repo's recorded backend, which is exception-free, returns `None` for an unconfigured repo, and is the right precedence (it reads the repo's own recorded state, not a resolved default). Cache it per repo root the way `_resolved_root_str` is memoized: `get_ignored_dirs` is called ~30x per command and `read_project_identity` measured ~1.5ms per call at review, so an uncached read adds ~45ms to a ~530ms command. Nested lanes stay excluded by the existing `"untracked" in rel_parts` rule and by `DEFAULT_IGNORED_DIR_NAMES`'s `.aw/records/runs`.
  - Depends on: E-07
  - Expected outcome: with the backend configured, `aw attention` sees records under an ignored `.aw/records/` while `.aw/records/prompts/untracked/x.md` and `.aw/records/runs/x/state.json` stay hidden; with the backend NOT configured, a user's own `.aw/records/` ignore is still honored (the plan stays invisible).
  - Execution state: pending

### Task group 3: Warning, install, spec

- [ ] E-09 Warn about durability in `storage.get_storage_status`: add a `repository-untracked` branch BEFORE the generic ones, keeping `durability_state` from observation (`unversioned`/`local-git`, never `repository-managed`) and setting the recommendation to a string containing "not durable across clones" and naming `.aw/records/` as git-ignored. Place it after the `REPOSITORY` branch and before the `has_git and remote_url` chain, so an observed local git in the records dir still reports `local-git` rather than being flattened to `unversioned`.
  - Depends on: E-08
  - Expected outcome: `aw storage status` (text and `--format json` recommendation) carries "not durable across clones" for this backend and not for `repository`; durability reads `unversioned` with no records `.git` and `local-git` with one.
  - Execution state: pending

- [ ] E-10 Warn in the two INSTALL surfaces: (a) `install_wizard.render_pre_write_plan` adds a yellow `[WARNING] Records are git-ignored in this working tree (repository-untracked); they are not durable across clones and are lost if this checkout is deleted.` line in its existing `Durability & Warnings:` block; (b) `cli._run_install` emits the same text via `term.status("warn", ...)` after writing the ignore rule. Also make `render_pre_write_plan`'s own resolved-path loop correct for this backend: it derives the owner from the PLACEMENT string with `"target" in placement`, and `target-ignored` contains `target`, so the owner line is already right - assert that rather than changing it, so a later refactor cannot silently break it.
  - Depends on: E-09
  - Expected outcome: the dry-run install plan and the live install both print the "not durable across clones" warning for this backend and neither prints it for `repository`; the records row shows `[target] (ignored)`.
  - Execution state: pending

- [ ] E-11 End-to-end install test: in a temp git repo run `python3 -m agent_workflows install <tmp> --preset private-target --records-backend repository-untracked --yes` (the flag shape `_run_install` already accepts), then assert exit 0, `.aw/config/project.json` has `"records_backend": "repository-untracked"`, `.aw/.gitignore` contains `/records/`, and `git -C <tmp> ls-files .aw/records` is empty. The install scaffolds records `.gitkeep`/README files through `engine._create_if_absent`, which already calls `git_add_optional` (the tolerant helper that returns False on "ignored by" rather than aborting), so this SHOULD pass unchanged; if any step instead uses a raw `git add` and aborts, route that call through `git_add_optional` and name the call site in the evidence. ALSO cover the `aw setup` entry point, which declares the same `--records-backend` flag but is measured at review NEVER to reach `install_wizard`/`persist_project_policy` (`_run_setup` calls `_install_one` directly): either wire the flag through or make `aw setup --records-backend repository-untracked` refuse with a message naming `aw install`. A flag that is accepted and silently ignored would leave a tracked records tree while the user believes they chose otherwise.
  - Depends on: E-10
  - Expected outcome: `aw install` succeeds, records exist on disk, nothing under `.aw/records` is tracked; `aw setup --records-backend repository-untracked` either produces the same ignored state or refuses explicitly, never silently ignores the flag.
  - Execution state: pending

- [ ] E-12 Amend Section 5 of the canonical storage spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` with the `repository-untracked` contract. Section 5's `target-ignored` bullet currently reads "Only `config_local` and `state_runtime` may use it by preset", which this backend contradicts, so the amendment is REQUIRED, not cosmetic: state that `records` may also take `target-ignored` when this backend is EXPLICITLY selected (never by preset, which is what preserves the existing sentence's intent); that the path is in-tree, ignored by an anchored `/records/` line in `.aw/.gitignore`, never staged, observed as `unversioned`/`local-git` (never `repository-managed`), refused with clean-delta, refused on a repo that already tracks records, and not durable across clones. Write the BODY only; record the amendment via `python3 -m agent_workflows specs note <path> --message "..."` citing `lr0lln`, because `.aw/records/specs/README.md` forbids hand-editing the status or the workflow history.
  - Depends on: E-11
  - Expected outcome: the spec's Section 5 names `repository-untracked` with the explicit-selection qualifier, and its workflow history carries an `aw specs note` line citing `lr0lln`.
  - Execution state: pending

- [ ] E-13 Run the bare suite `python3 -m pytest`.
  - Depends on: E-12
  - Expected outcome: the summary line reports 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Backends are one enum, `project_schema.RecordsBackend` (`HOME`, `COMPANION`, `REPOSITORY`); `RECORDS_BACKENDS` and the install flags derive from it, so adding a member propagates to the FLAG CHOICES automatically - but NOT to the dispatch sites, each of which tests one value with `==` and falls through to a default. Enumerated at review: `resolve_project_context` (four branches), `record_producers.get_git_owner` and `resolve_record_routing`, `storage.validate_storage_boundaries` and `get_storage_status`, `project_layout.materialize_project_layout`, and `install_wizard` (`__post_init__`, `validate`, `render_pre_write_plan`, `resolve_policy_noninteractive`). Adding a member without visiting each is how the new value silently becomes `home`.
- `project_context.read_project_identity` is THE ONE reader for a repo's RECORDED `records_backend` (its docstring says so, and says deliberately NOT to use `resolve_project_context` for this, which layers defaults and can never answer "is this repo configured, and as what?"). Any code that must branch on the repo's own choice reads it there.
- The installer owns `.aw/.gitignore` and never the root `.gitignore` (`engine._ensure_aw_gitignore` docstring: "it is NOT the user's root `.gitignore`"). Patterns that could match at depth are anchored (`/inbox/`).
- Placement vocabulary already has `target-ignored` (`project_schema.Placement.TARGET_IGNORED`) and git policy `ignored` (`GitPolicy.IGNORED`); no new enum beyond the backend value is needed.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- F-01: `project_context.resolve_project_context` maps anything that is not `repository`/`companion` to the HOME records root (`else:  # HOME`), so an unknown backend would silently land in AW_HOME; the new value needs its own branch.
- F-02 (measured, probe under `/tmp/opencode/g2/probe-untrackrec/`): with `.aw/.gitignore` = `records/`, `aw attention --format json` printed `"items": []`; after removing the rule the same repo listed `abc123` as `ready`. Cause: `artifact_core.get_ignored_dirs` returned `.aw/records`. `plans_index.scan_plans` rooted at the plans dir still found the plan, so the blindness is in repo-rooted scanners. This is why E-04 exists.
- F-03: the storage spec named in the task (`20260809-2211-01-...storage-wizard-and-state.spec.md`) is `Status: superseded` by `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (`Status: implemented`, `Canonical: true`). Amending a superseded spec changes no live contract, so E-07 amends the canonical successor.
- F-04: `record_producers.resolve_record_routing` sets `allow_git = backend == RecordsBackend.REPOSITORY.value`, so the new backend already gets no commit destination; no change needed there. VERIFIED at review by running it with the value in `RECORDS_BACKENDS`: it returned `repository-untracked`, `allow_git_stage=False`, `commit_destination=None`.
- F-05 (measured at review): `record_producers.get_git_owner` CRASHES for this backend, and already crashes for `home`. Its `elif` reads `elif "companion" in backend or backend == RecordsBackend.COMPANION_TRACKED.value:`, and `RecordsBackend` has no `COMPANION_TRACKED` member - `COMPANION_TRACKED` belongs to `Placement`. Probe with a real project.json in a temp repo: `home` raised `AttributeError: type object 'RecordsBackend' has no attribute 'COMPANION_TRACKED'`, while `repository` returned `"target"` and `companion` returned `"companion"` (both short-circuit before the bad attribute). The new value would take the same crashing path. This is why E-02 exists and why it precedes everything that routes records.
- F-06 (measured at review): the ignore rule does NOT untrack already-tracked records, so applying this backend to a repo with committed records yields a half-state. In a temp repo with `.aw/records/plans/pending/p.ipd.md` committed, adding `/records/` to `.aw/.gitignore` left `git ls-files .aw/records` still listing the file and `git status` still reporting it modified, while `git add` on a NEW record exited 1 with "The following paths are ignored by one of your .gitignore files: .aw/records". Some records tracked, some untrackable, nothing reconciling them. This is why E-06 refuses rather than proceeding.
- F-07 (measured at review): an UNCONDITIONAL `get_ignored_dirs` discard would reverse a user's own deliberate choice. In a temp repo whose ROOT `.gitignore` says `.aw/records/` and which has NO AW policy at all, git reports `.aw/records` in the ignored set exactly as the backend's own rule does, and the discard made `is_ignored_path` return False for a plan under it. `get_ignored_dirs` cannot tell WHY a path is ignored, so the discard must be gated on the repo's recorded backend. This is why E-08 reads `read_project_identity`. Cost measured: 30 calls to `read_project_identity` took 45.3ms (~1.5ms each) against 258.2ms for 30 `get_ignored_dirs` calls, so it must be cached per repo root rather than called on every invocation.
- F-08 (measured at review): `aw setup` declares `--records-backend` with the same `choices=[r.value for r in RecordsBackend]`, but `_run_setup` never calls `install_wizard.collect_policy_interactive` or `persist_project_policy` - it goes straight to `_install_one` per discovered repo. So the flag is accepted and silently ignored on that entry point today. E-11 covers it because a silently-ignored choice here leaves a TRACKED records tree while the user believes they chose an ignored one.
- F-09: lifecycle moves survive an ignored records tree without change. `artifact_core.git_mv` falls back to `shutil.move` when `git mv` fails, and it does fail here (measured: `fatal: not under version control` on an ignored source). So `aw ipd set`/`finalize` still relocate plan files; only the staging is lost, which is the intended behavior for this backend. No change needed, recorded so a later reader does not add one.

## Proposed changes (ordered, validatable)

1. Enum value plus the four resolver branches (E-01).
2. Repair the pre-existing `get_git_owner` crash the new value hits (E-02).
3. Route the storage-boundary and layout-materialization dispatchers (E-03).
4. Policy placement override that survives an explicit preset fill (E-04).
5. Flag and hint text (E-05).
6. Refuse the backend on a repo that already tracks records (E-06).
7. Anchored, line-matched ignore rule written only for this backend (E-07).
8. Scanner fix, gated on the recorded backend, so ignored records remain visible without overriding a user's own ignore (E-08).
9. Durability warning in storage status (E-09) and in the two install surfaces (E-10).
10. End-to-end install check plus the `aw setup` entry point (E-11).
11. Spec amendment (E-12), then the suite (E-13).

## Deferred / out of scope (with reason)

- Migration to or from `repository-untracked` (`aw migrate --target-backend`, whose `choices=["home", "companion", "repository"]` is hardcoded in `cli.py`): moving records between tracked and ignored states is a separate, riskier flow. E-06's refusal is what makes this deferral safe rather than a gap: a user who needs the cutover is TOLD so at install time instead of silently landing in the F-06 half-state.
  - Carrier: hsixiz
  - Carrier-Evidence: .aw/records/backlog/graduated/20260815-hsixiz-01-hsixiz-records-backend-repo-local-untracked.backlog.md
- An interactive wizard menu entry and a dedicated preset: the flag is the smallest surface; presets are a spec-level table, and adding a preset row would require amending the Section 6 preset table rather than only the Section 5 placement vocabulary.
  - Carrier-Declined: flag-only satisfies the backlog ask, and E-12's amendment deliberately says "explicitly selected, never by preset", so no preset row is outstanding to file.
- An `aw doctor` check that flags tracked files under an ignored records root.
  - Carrier-Declined: E-06 refuses the configuration that would create this state in the first place, so the drift a doctor check would report can no longer be reached through any supported path; a `git add -f` bypass is the user's explicit override and is already documented as advisory in the `aw:untracked` gitignore section.

## Scope check

- Over-scope: none.
- Under-scope (all four added at review): E-08 is beyond the literal ask but required - without it the backend makes `aw attention` go blind (F-02). E-02 repairs a PRE-EXISTING crash (F-05) that the new value would hit on its first call, so it cannot be left for a later plan. E-06 refuses a half-state the feature would otherwise create silently (F-06). E-11's `aw setup` half covers an entry point that already accepts the flag and ignores it (F-08).

## Required tests / validation

- `tests/test_project_context.py`: the four resolved values, the enum constant, and the clean-delta refusal (E-01).
- `tests/test_records_untracked_backend.py` (new): `get_git_owner` repair including the pre-existing `home` crash (E-02), layout/boundary routing (E-03), policy override under both empty and explicit placements (E-04), flag text (E-05), tracked-records refusal (E-06), ignore rule (E-07), scanner visibility both WITH and WITHOUT the backend configured (E-08, shown failing first), storage recommendation (E-09), install warnings (E-10), end-to-end install and the `aw setup` entry point (E-11).
- Bare suite (E-13).

## Spec / documentation sync

- Amend `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 5 (declared in Scope-Paths). Why: the spec's `target-ignored` bullet reads "Only `config_local` and `state_runtime` may use it by preset", so this backend would violate the written contract without the amendment. The amendment keeps that sentence's intent by qualifying the new case as EXPLICITLY SELECTED rather than preset-reachable. Body only; the history line goes through `aw specs note`, because `.aw/records/specs/README.md` forbids hand-editing status or history. The superseded `20260809-2211-01` spec is left untouched (F-03).

## Open questions

### OQ-01: Which spec file to amend

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved from the repository at review. The task names `20260809-2211-01-...storage-wizard-and-state.spec.md`, whose own front matter reads `Status: superseded`; the successor `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` reads `Status: implemented` and `Canonical: true` and carries the live Section 5 placement vocabulary this plan contradicts. Amending the superseded file would change no live contract, so E-12 amends the canonical successor (F-03).
- Carrier-Declined: Resolved from in-tree evidence, so nothing is outstanding to carry; the decision is recorded here and in the review record's Decisions table.

### OQ-02: Backend value name

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `repository-untracked`. It matches the backlog title `hsixiz` ("repo-local-but-untracked"), and the `<container>-untracked` shape is already the repository's vocabulary for exactly this distinction in `project_schema.Placement` (`home-untracked`, `companion-untracked` beside `companion-tracked`). Choosing anything else would be the only backend value not following the placement vocabulary it maps onto.
- Carrier-Declined: A naming choice resolved from the existing vocabulary and settled by E-01; renaming later would be a new decision about a published flag value, not a deferred obligation from this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_project_context.py -q` output showing the new resolution tests passing, and the passing names of the tests asserting records root `.aw/records`, git policy `ignored`, durability `unversioned`, commit destination `None`, and the clean-delta `PathSecurityError`. Also paste the `assertIn("repository-untracked", RECORDS_BACKENDS)` test passing. All FOUR resolver branches must be covered by a named assertion; a test that only checks the records root would pass while three branches still routed to HOME.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the pre-fix reproduction FIRST - a run of `get_git_owner` against a `home`-backend temp repo showing `AttributeError: type object 'RecordsBackend' has no attribute 'COMPANION_TRACKED'` - then the passing test output showing `None` for `repository-untracked` and for `home`, `"target"` for `repository`, and `"companion"` for `companion`. The pre-fix trace is required because a fix for a crash nobody reproduced is indistinguishable from a no-op refactor.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste passing test output showing `materialize_project_layout` created `<tmp>/.aw/records` for this backend, and `get_storage_status` returning without raising `StorageSecurityError`. Paste the `validate_storage_boundaries` comment you added (the one stating why `repository-untracked` is deliberately NOT in the refusal tuple) so the reason is in the evidence and not only in the diff.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste passing output for BOTH policy construction shapes - `ProjectPolicy(records_backend="repository-untracked")` with no placements, AND the same with explicit `placements=`/`git_policies=` from `get_preset_defaults("private-target")` - each asserting `placements["records"] == "target-ignored"` and `git_policies["records"] == "ignored"`. The second case is the one that fails if the override is written inside the existing `if not self.placements` guard. Plus the clean-delta `InvalidPolicyError`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m agent_workflows install --help` output showing `repository-untracked` in the `--records-backend` choices, the passing test on the noninteractive hint string, and `python3 -m agent_workflows migrate --help` showing `--target-backend` still offering only `home`/`companion`/`repository` (positive proof the deferred surface was left alone).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste passing test output for both directions - the refusal on a temp repo with one COMMITTED file under `.aw/records` (showing the raised error text naming the tracked path and the migration route), and acceptance on a temp repo with none. Paste the `git ls-files .aw/records` output for each repo so the precondition is visible rather than asserted.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste passing test output for the ignore-rule tests, plus `grep -c '^/records/$' <tmp>/.aw/.gitignore` printing `1` after two helper calls (and the second call's `False` return), and `git -C <tmp> check-ignore -v .aw/records/plans/pending/x.md` naming `.aw/.gitignore`. Also show the line-anchored presence test working when the explanatory comment (which contains the substring `records/`) is already present but the rule line is not.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: THREE results, all pasted. (1) The scanner-visibility test FAILING with the discard reverted in the SOURCE FILE (comment the line out, run, restore; a runtime monkey-patch of `get_ignored_dirs` does not substitute, because callers hold a module reference and the function is what is under test) - plus an empty `git diff --stat agent_workflows/artifact_core.py` proving the revert. (2) The test PASSING, including the `attention` assertion listing the plan and the `prompts/untracked`/`runs` paths still ignored. (3) The NEGATIVE case: a temp repo whose ROOT `.gitignore` ignores `.aw/records/` with NO `records_backend` recorded, asserting the plan is STILL invisible - this is the assertion that proves the fix did not override a user's own choice, and without it E-08 is indistinguishable from the unconditional version F-07 rejects.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste passing test output asserting "not durable across clones" in the `get_storage_status` recommendation for `repository-untracked` and its ABSENCE for `repository`, plus the observed `durability_state` in two states: `unversioned` with no `.git` under the records root and `local-git` with one. The second state is what proves the branch did not flatten observation to a constant.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the `render_pre_write_plan` output for this backend showing the yellow warning line AND the records row reading `[target] (ignored)`, plus the same function's output for `repository` showing no such warning. Paste the `cli._run_install` warning as emitted (a dry-run or captured-output test is fine), not merely the source line.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste passing output of the end-to-end install test, including the asserted EMPTY `git ls-files .aw/records` result and `"records_backend": "repository-untracked"` in `project.json`; name any `git_add_optional` call site changed, or state explicitly that none was needed. Separately paste the `aw setup --records-backend repository-untracked` outcome and say which route was taken (wired through, or refused with a message naming `aw install`); "the flag is accepted" is not an acceptable outcome and if that is what you observe, the item is not done.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste `git diff -- .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` showing the Section 5 edit, and confirm the diff touches NEITHER the `- Status:` line NOR the `## Workflow history` section by hand. Paste the `aw specs note` command output and the resulting history line citing `lr0lln`, plus `aw specs check` reporting conforming afterwards.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run showing 0 failed. Run it BARE per AGENTS.md: no `-n0`, no extra `-q`, no `-p no:randomly`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Thirteen items, one concern: making `repository-untracked` a real backend. The count grew from eight at review because three surfaces the original plan did not reach are load-bearing for that single concern (a pre-existing crash the new value hits, a half-state the feature would create on a records-tracking repo, and a second entry point that already accepts the flag), and because two items each bundled independent test-surfaces. No item introduces a second concern.

WHAT A HUMAN IS APPROVING. A new public flag value on `aw install` that makes `.aw/records/` git-ignored in the working tree. The non-routine parts are: (a) an edit to `artifact_core.get_ignored_dirs`, which every repo-rooted record scanner depends on, so a mistake there is repo-wide invisibility of records rather than a local bug - which is why E-08 is gated on the recorded backend and V-08 demands a negative case; (b) a REFUSAL added to install policy validation (E-06), which will reject a configuration a user might ask for, deliberately, because the alternative is a silent half-state; and (c) an amendment to an `implemented` canonical spec's Section 5 placement vocabulary.

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface within each declared path: `project_schema.py` one enum member; `project_context.py` the four backend branches in `resolve_project_context`; `record_producers.py` the `get_git_owner` dispatch only; `project_layout.py` the records-dir creation tuple in `materialize_project_layout`; `storage.py` the `get_storage_status` branch plus a comment in `validate_storage_boundaries`; `install_wizard.py` `ProjectPolicy.__post_init__`/`validate`, the noninteractive hint, and `render_pre_write_plan`'s warning block; `engine.py` the new `ensure_untracked_records_ignore` helper (the `_AW_GITIGNORE_TEMPLATE` itself is NOT changed); `cli.py` the two help strings plus the `_run_install` call site and the `aw setup` decision; `artifact_core.py` the gated discard in `get_ignored_dirs`; the two test files; and the spec's Section 5 body. EXPLICITLY NOT IN SCOPE: `aw migrate --target-backend` choices, a wizard menu entry, a new preset, an `aw doctor` check, and the `_AW_GITIGNORE_TEMPLATE` default. An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-02's pre-fix `AttributeError` reproduction and V-08's source-file mutation, because both require producing a FAILURE before a fix and both are trivial to assert without performing. Run the suite bare (`python3 -m pytest`).

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: `record_producers.get_git_owner` no longer contains the `COMPANION_TRACKED` reference F-05 measured (someone else repaired it, so E-02 needs re-deriving rather than re-applying); or the Section 5 `target-ignored` sentence E-12 amends has already been changed to permit `records`.

Execute only after explicit human approval (`Status: approved`). Commit only Scope-Paths files through `aw commit lr0lln -- <paths>`; never push. LIFECYCLE TRANSITION: the plan must reach `executed/` with `aw ipd finalize`, which is UNCONDITIONALLY owed - but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence. Close backlog `hsixiz` only if it is not already `graduated` (it is), and note that it carries no `- Blocks-Release:`, so no gate handoff is owed.
