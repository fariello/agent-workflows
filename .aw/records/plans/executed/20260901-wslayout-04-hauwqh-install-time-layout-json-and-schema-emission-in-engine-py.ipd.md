# IPD: Install-time layout.json and schema emission in engine.py

- Date: 2026-09-01
- Kind: child
- Concern: Non-Python tools require a machine-readable `.aw/system/layout.json` and `.aw/system/layout.schema.json` in the target repository. Emitting them during repository installation ensures zero git drift and version alignment with `.aw/system/VERSION`.
- Scope: Update `agent_workflows/engine.py` to write `.aw/system/layout.json` and `.aw/system/layout.schema.json` during `engine.install_into_repo()` (the only emission site; `/aw setup-repo` inherits it transitively), gitignore them via the framework-owned `.aw/.gitignore`, and add integration test coverage in `tests/test_engine_install.py`.
- Scope-Paths: agent_workflows/engine.py, .aw/.gitignore, tests/test_engine_install.py
- Item-Dependencies: executed:wpu5zu
- Status: executed
- Readiness: go-pending-approval
- Set: wslayout
- Order: 4
- Highest E allocated: 03
- Author: antigravity
- Id: hauwqh
- From-Spec: kw5y2s

## Workflow history
- 2026-09-05 executed (aw oc run): aw oc run self-finalize: hauwqh verified (set wslayout, attempt 1).
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 6: APPROVE WITH REVISIONS APPLIED; no new findings; GO - PENDING HUMAN APPROVAL. Verified at HEAD `16777ccc`, tree clean, plan committed and unchanged. Lint conforming at both checkpoints. THIS PLAN IS THE BEST-EVIDENCED OF THE FOUR and I could not falsify any load-bearing claim: `install_into_repo` is at `engine.py:5420` as stated; `_AW_GITIGNORE_TEMPLATE` at `:4207` and `_ensure_aw_gitignore` at `:5236`, so PR-027's two-places-in-engine.py instruction (template for a FRESH install, `additions` back-fill for an EXISTING one) is correct and is the part a naive executor would get wrong; `cli.py` really does reach `install_into_repo` directly (`cli.py:4226`), confirming PR-026's finding that wiring emission into `engine.run()` would leave `aw setup` silently emitting nothing; `tests/test_engine_install.py` genuinely does not exist, so E-03 is correctly a CREATE; `.aw/.gitignore` is tracked here, consistent with the plan's own point that a TARGET's copy is GENERATED rather than copied; and `agent_workflows/engine.py` is declared by only ONE other pending plan (its own orchestrator), so F-5's no-current-conflict measurement still holds. The scope fence, the eleven-clause contract, and the root-`.gitignore` precision ("carries no layout entry", NOT "has no diff") are all sound as written. Reviewed with no revisions required.
- 2026-09-04 to-review (aw set): Applied deterministic plan-review repairs; controlling spec kw5y2s awaits renewed human approval.

- 2026-09-04 reviewed (antigravity): /aw plan-review-long: APPROVE WITH REVISIONS APPLIED; PR-019, PR-021, PR-022, PR-023 fixed (corrected engine function name to install_into_repo, added eleven-clause execution contract, structured findings evidence table, conventions, bare-suite validation with baseline re-measurement, and readiness).
- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - PR-002 (tests/test_engine_install.py and tests/test_setup_repo_cli.py do not exist), PR-003 (`aw setup-repo` is not a CLI verb), PR-004 (trackedness of emitted layout.json unstated), PR-007.
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 to-review (aw set): plan-review PR-007: metadata now matches the orchestrator sequence table

## Goal

Ensure `engine.install_into_repo()` bakes `.aw/system/layout.json` and `.aw/system/layout.schema.json` into target workspaces alongside `.aw/system/VERSION` (and `/aw setup-repo` inherits it transitively).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Engine Install Integration

- [x] E-01 Update `agent_workflows/engine.py` (`install_into_repo`) to call `layout.build_default_layout().to_json(framework_version)` and `layout.build_default_layout().to_schema()` and write `.aw/system/layout.json` and `.aw/system/layout.schema.json` during installation.
  - Depends on: none
  - Expected outcome: Target repository `.aw/system/` directory receives layout.json and schema.
  - Execution state: performed
  - Executed 2026-09-05: added `AW_LAYOUT_JSON_PATH` / `AW_LAYOUT_SCHEMA_PATH` constants
    (`engine.py:96-103`) and a new `emit_layout_artifacts(repo_root, *, dry_run=False)`
    (`engine.py:5336-5395`) that builds `layout.build_default_layout()`, serializes with
    `to_json(read_installed_version(repo))` / `to_schema_json()`, writes both at mode `0o644`, and
    SKIPS a byte-identical existing file so a re-install is a true no-op (not a rewrite). The call
    sits INSIDE `install_into_repo` itself (after `create_setup_artifacts`, so `.aw/.gitignore`
    already exists and git never sees the files even transiently), satisfying the PR-026 shared
    chokepoint requirement; `engine.run()` was NOT touched. A freshly emitted (not pre-existing)
    artifact is added to the `--undo` created-files record, and the written set is surfaced as
    `result["layout_artifacts"]`. A `legacy`-layout target returns `[]` rather than manufacturing a
    `.aw/system/` tree, and an `OSError` warns non-fatally (same posture as the ownership manifest).
  - Set-level prerequisite: `wpu5zu` must be executed first; see `- Item-Dependencies:` in the metadata.
  - THE ONLY EMISSION SITE IS `engine.install_into_repo()` (plan-review PR-003, PR-021). `/aw setup-repo` (alias
    `/setup-repo`) is an AGENT SLASH-COMMAND backed by a workflow BODY
    (`.aw/system/workflows/setup-repo/setup-repo.md`), NOT a CLI verb and NOT a Python entry point, so it
    has no call site to wire. The order is the REVERSE of what this plan originally assumed: `aw install`
    runs FIRST and then RECOMMENDS `/setup-repo` as a follow-up conformance pass
    (`agent_workflows/engine.py:3581-3597`, "NEXT STEP ... run /setup-repo"). `/aw setup-repo` therefore
    inherits emission transitively at zero cost. `aw update` is not a verb either; `aw install` is the
    idempotent update path. Do NOT add emission code to the workflow body.
  - PUT THE CALL INSIDE `install_into_repo` ITSELF, NOT IN A CALLER (plan-review round 5, PR-026).
    Measured: `install_into_repo` (`engine.py:5420-5576`) has THREE callers, and the second CLI one is a
    real verb this plan never mentions. `aw install` reaches it via `engine.run()` (`engine.py:5656`),
    but `aw setup` -- the machine-wide first-run wizard, a genuine CLI verb, NOT a synonym for
    `aw install` and NOT the `/setup-repo` slash-command -- reaches it via `cli._run_setup`
    (`cli.py:5639-5757`) -> `cli._install_one` (`cli.py:4202-4314`) -> `engine.install_into_repo`
    (`cli.py:4226`). Wiring emission into the shared function therefore covers `aw install`, `aw setup`,
    and library callers BY CONSTRUCTION; wiring it into `engine.run()` would leave `aw setup` silently
    emitting nothing, and no test in this plan as originally written would have caught that.
  - Write mode `0o644`, deterministic byte output (stable key order) so a re-install of the same version
    is a no-op rather than a rewrite.

### Task group 2: Installation Verification Tests

- [x] E-02 Add the `.aw/.gitignore` entries so the emitted layout artifacts are never committed, per the maintainer's OQ-2 ruling.
  - Depends on: E-01
  - Expected outcome: `.aw/.gitignore` carries `system/layout.json` and `system/layout.schema.json`, and a freshly installed repo shows neither file in `git status`.
  - Execution state: performed
  - Executed 2026-09-05: edited BOTH generation places in `engine.py` as PR-027 requires.
    (a) `_AW_GITIGNORE_TEMPLATE` (`engine.py:4287-4292`) now ends with a commented
    `system/layout.json` + `system/layout.schema.json` pair, so a FRESH install emits them.
    (b) the `additions` back-fill in `_ensure_aw_gitignore` (`engine.py:5384-5393`) appends either
    pattern that a repo installed BEFORE this change lacks, using an ANCHORED line-match
    (`(?m)^<pattern>$`) rather than a substring test so the explanatory comment above the patterns
    cannot be mistaken for the patterns themselves. Reusing the existing `additions` mechanism makes
    it idempotent by construction. This repo's own checked-in `.aw/.gitignore` got the same block as
    dogfooding (optional per the scope note; it changes nothing for a target repo).
  - MAINTAINER RULING 2026-09-01 (plan-review PR-004 / OQ-2): the emitted files are GITIGNORED, via a
    `.gitignore` INSIDE the `.aw/` directory. This matches the `ila6vl` decision on generated manifests
    and this spec's own anti-drift rationale (committing generated output would defeat the reason
    install-time emission exists).
  - USE THE EXISTING FRAMEWORK-OWNED FILE, do not create a new mechanism: `.aw/.gitignore` already
    exists and already carries exactly this convention for four other generated/box-local paths
    (`.aw/.gitignore:1-15`), and its header states it "lives inside the framework-owned `.aw/` tree; it
    is NOT the user's root `.gitignore`". Add `system/layout.json` and `system/layout.schema.json`
    (paths are relative to `.aw/`), with a one-line comment naming this plan, in the same style as the
    existing entries.
  - EDIT THE GENERATOR, NOT (ONLY) THIS REPO'S CHECKED-IN FILE (plan-review round 5, PR-027). A target
    repo's `.aw/.gitignore` is GENERATED, never copied: `_ensure_aw_gitignore`
    (`agent_workflows/engine.py:5236-5261`) writes `_AW_GITIGNORE_TEMPLATE`
    (`agent_workflows/engine.py:4208-4222`) when the file is absent, and otherwise APPENDS only the
    patterns missing from an explicit `additions` back-fill list. Verified: this repo's own
    `.aw/.gitignore` and a freshly installed target's differ in comment text, proving the target's copy
    comes from the template. Therefore this E-item MUST touch TWO places in `engine.py`:
    (a) `_AW_GITIGNORE_TEMPLATE`, so a FRESH install emits the entries; and
    (b) the `additions` list in `_ensure_aw_gitignore`, so a repo installed BEFORE this change gains
    them on update (this is the pre-existing gap the `records/history.jsonl` comment at `:5254-5257`
    records having already been hit once). Editing only the checked-in `.aw/.gitignore` in THIS repo
    would change nothing for any target repo, and would pass a naive "the file contains the line" test.
  - The `additions` mechanism is inherently idempotent (it appends only what a substring check reports
    missing), so satisfying the no-duplicate-lines requirement means REUSING it, not writing new logic.
  - THE INSTALLER DOES MUTATE THE TARGET'S ROOT `.gitignore`, so state the rule precisely: this plan must
    never ADD A LAYOUT ENTRY to the root `.gitignore`. It is NOT true that the installer never touches
    that file. `ensure_untracked_gitignore` (`engine.py:2698-2735`) writes a managed `aw:block` of
    untracked-safety patterns into the target's ROOT `.gitignore`, and `ensure_backups_gitignored`
    (`:2576`) adds the installer-backups line; both are called from `install_into_repo`
    (`engine.py:5506-5507`). Verified in a temporary target repo: after `aw install`, the root
    `.gitignore` carries `.agent-workflows-installer-backups/` plus the `aw:block`, while the
    pre-existing user line was preserved. V-02's "root `.gitignore` untouched" evidence must therefore
    be scoped to "carries no layout entry", NOT to "has no diff", or it will fail for a legitimate
    reason on a first install.

- [x] E-03 Create `tests/test_engine_install.py` verifying that fresh and updated installs emit valid, gitignored `layout.json` and `layout.schema.json`.
  - Depends on: E-01, E-02
  - Expected outcome: Test suite validates install-time file generation, schema validity, and gitignored status.
  - Execution state: performed
  - Executed 2026-09-05: CREATED `tests/test_engine_install.py` (18 tests, 3 classes, stdlib-only, no
    `jsonschema` import per the `tests/test_layout.py` precedent). Covers every clause this plan
    demanded: both files emitted; mode `0o644`; `framework_version` == the repo's
    `.aw/system/VERSION`; the emitted document conforms STRUCTURALLY to the emitted schema; the bytes
    are exactly `build_default_layout()`'s own serialization (no forked serializer); a second install
    rewrites nothing (asserted on BOTH content AND `st_mtime_ns`, since equal bytes alone would not
    catch a needless rewrite); stale content IS refreshed (the skip-unchanged path must not become
    skip-always); emission through `cli._install_one` (the `aw setup` path, PR-026); no emission code
    in the `setup-repo` workflow body (PR-003); `--dry-run` writes nothing; a `legacy` target emits
    nothing; the template carries both patterns; a fresh install leaves both invisible to
    `git status --porcelain` with `git check-ignore -v` attributing the rule to `.aw/.gitignore`; the
    ROOT `.gitignore` carries no layout entry AND the user's own line survived; the back-fill path
    adds each pattern exactly once and is idempotent under repeat calls and repeat installs; and the
    TRACKED `records/comms/shared/inbox/` lane is still not ignored (regression fence on the
    neighbouring anchored `/inbox/` rule). `tests/test_setup_repo_cli.py` stayed out of scope.
  - CORRECTED (plan-review PR-002): `tests/test_engine_install.py` DOES NOT EXIST at review time, so
    this is a CREATE, not an edit. `tests/test_setup_repo_cli.py` also does not exist and is DROPPED
    from scope: per PR-003 there is no `setup-repo` CLI surface to test.
  - Must assert, in a temporary repo: both files are written; `layout.json` validates against the
    emitted `layout.schema.json`; `framework_version` matches the installed `.aw/system/VERSION`; a
    second install of the same version rewrites nothing (determinism); and `git status --porcelain`
    shows NEITHER file, proving the E-02 ignore actually takes effect.

## Project conventions discovered (Step 0)

- `agent_workflows/engine.py`: primary workspace installer (`engine.install_into_repo`, lines 5420-5560).
- `.aw/.gitignore`: framework-owned ignore file; header specifies it lives inside the `.aw/` tree and the user's root `.gitignore` is never touched.
- Controlling spec `kw5y2s` Section 6.1 is `approved` again (re-measured at round 5; the round-4 `to-review` claim is stale). Its GITIGNORED emission ruling and `engine.install_into_repo()` sole-emission ruling are unchanged, and the spec is immutable during execution.
- Emitted files: `.aw/system/layout.json` and `.aw/system/layout.schema.json` mode `0o644`, with deterministic byte serialization (stable keys) so re-install is a no-op.
- Python 3.9 is the floor (`pyproject.toml:12`).

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **`engine.install_into_repo()` is the sole emission site, and it is a CHOKEPOINT with THREE callers, not a single entry point.** `/aw setup-repo` is an agent slash-command backed by a workflow body with no Python call site and inherits emission transitively. But `aw setup` IS a real CLI verb and a second install path, reaching the function through `cli._run_setup` -> `cli._install_one`. Emission must therefore live INSIDE `install_into_repo` (PR-026). Line range also corrected: the function is `5420-5576`, and the `/setup-repo` recommendation is at `3598-3613` inside `print_summary` (`3515-3613`), not `3581-3597`. | `agent_workflows/engine.py:5420-5576`, `:5656` (`run`), `:3598-3613`; `cli.py:5748`, `cli.py:4226`; workflow index. |
| F-2 | **The emitted layout artifacts are gitignored via a GENERATED `.aw/.gitignore`, and the root `.gitignore` is NOT untouched by the installer.** A target's `.aw/.gitignore` comes from `_AW_GITIGNORE_TEMPLATE` via `_ensure_aw_gitignore`, so E-02 must edit the template AND the back-fill list, not this repo's checked-in file. Separately, `install_into_repo` DOES write an untracked-safety `aw:block` and the backups line into the target's ROOT `.gitignore`, so the correct assertion is "no layout entry in the root file", not "root file unchanged" (PR-027). | `agent_workflows/engine.py:4208-4222` (template), `:5236-5261` (back-fill), `:2576`, `:2698-2735`, `:5506-5507`; verified in a temporary installed repo at round 5; maintainer ruling on OQ-02. |
| F-3 | **`tests/test_engine_install.py` is newly created by this plan.** Asserts install-time generation, schema validity, and gitignore enforcement in a temporary repo. `tests/test_setup_repo_cli.py` was dropped because no such CLI surface exists. | E-03 / V-03 notes; file verified absent before execution. |
| F-4 | **Deterministic serialization is required.** Re-running `install_into_repo` on an unchanged version must leave the emitted files byte-identical (no rewrites or timestamp drift). | E-01 / V-01 notes. |
| F-5 | **Concurrent scope must be measured at execution time; measured at round 5 there is currently NO conflict.** The prior `6knsrx` example is `Status: superseded`, and a round-5 scan of `- Scope-Paths:` across pending plans finds no non-wslayout claimant on `agent_workflows/engine.py`. Re-measure immediately before editing regardless, since a new plan can land mid-Set. | Round-5 scan of pending `- Scope-Paths:` with each plan's `- Status:`; `6knsrx` resolved under `plans/superseded/`. |

## Proposed changes (ordered, validatable)

1. Wire layout emission in `agent_workflows/engine.py` `install_into_repo` (E-01).
2. Add `.aw/.gitignore` entries (E-02).
3. Author integration tests in `tests/test_engine_install.py` (E-03).

## Deferred / out of scope (with reason)

- CLI verb `aw layout` is in Order 05 (30jug9).

## Scope check

- Over-scope: none.
- Under-scope: none. `tests/test_engine_install.py` is newly created by E-03 and is in `Scope-Paths`.
- SCOPE-PATHS NOTE (round 5, PR-027): `.aw/.gitignore` stays declared, but understand WHY it is the lesser half of E-02. The substantive edit is to `agent_workflows/engine.py` (the `_AW_GITIGNORE_TEMPLATE` string and the `_ensure_aw_gitignore` back-fill list), which is already declared. Touching this repo's own `.aw/.gitignore` is optional dogfooding and changes nothing for a target repo.
- Concurrent-scope collision: re-measured at round 5. The prior `6knsrx` example is SUPERSEDED, and `agent_workflows/engine.py` currently has NO non-wslayout pending claimant. Re-measure immediately before execution anyway; the point of the rule is that this can change mid-Set.

## Required tests / validation

- `python3 -m pytest tests/test_engine_install.py` passing (NEW file created by E-03), with actual output pasted.
- Bare full suite `python3 -m pytest` from the PRIMARY checkout, with baseline re-measured on unmodified HEAD at execution time.
- `git check-ignore -v` confirming both emitted artifacts are ignored via `.aw/.gitignore` (and NOT via the root `.gitignore`).
- Emission proven through BOTH CLI install paths, `aw install` and `aw setup`, or proven to sit inside the shared `install_into_repo` chokepoint (PR-026).
- Gitignore entries proven on BOTH generation paths: fresh install (template) and already-installed repo (back-fill) (PR-027).
- NOTE: `tests/test_setup_repo_cli.py` was REMOVED from scope (plan-review PR-002/PR-003): it does not exist and there is no `setup-repo` CLI surface to test.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 6.1. Spec is `approved`; do NOT edit it.
- No user-facing documentation changes owned by this installer wiring.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: in a temporary repo, `engine.install_into_repo()` (via `aw install`) writes BOTH
    `.aw/system/layout.json` and `.aw/system/layout.schema.json` at mode `0o644`. Paste a directory
    listing showing both files and their mode, plus the emitted `framework_version` matching that repo's
    `.aw/system/VERSION`.
  - PLUS determinism: install twice at the same version and paste evidence the second run leaves both
    files byte-identical (e.g. matching `sha256sum` before and after).
  - PLUS the negative check for PR-003: confirm no emission code was added to
    `.aw/system/workflows/setup-repo/setup-repo.md` (it is a workflow body, not an entry point), e.g.
    paste `git diff --name-only` showing that path is untouched.
  - PLUS the SHARED-CHOKEPOINT proof (PR-026): paste the diff hunk showing the emission call sits inside
    `install_into_repo` itself, and demonstrate emission through the SECOND CLI install path by running
    `aw setup` (or calling `cli._install_one`) against a temporary repo and pasting the resulting
    `.aw/system/layout.json` listing. A call added to `engine.run()` instead is a FAILED validation even
    if `aw install` emits correctly, because `aw setup` would silently emit nothing.
  - Observed evidence: verified 2026-09-05 in a temporary git repo seeded with one commit and a
    pre-existing user line in its root `.gitignore`, driving `engine.install_into_repo(...)`.

    ```text
    layout_artifacts: ['.aw/system/layout.json', '.aw/system/layout.schema.json']
    --- ls -l (mode 0644) ---
    -rw-r--r-- 1 3422 Sep  5 18:17 .aw/system/layout.json
    -rw-r--r-- 1 1960 Sep  5 18:17 .aw/system/layout.schema.json
    --- framework_version vs VERSION ---
    layout.json framework_version = 1.2.1
    .aw/system/VERSION        = 1.2.1
    ```

    DETERMINISM (install twice at the same version; `sha256sum` before and after are identical and
    the second run reports an EMPTY written set, i.e. a no-op rather than a rewrite):

    ```text
    --- sha256 before second install ---
    922da2f3360df366cc09891e22994b5d9c6d22837cef169f4570d701f06a8fcd  .aw/system/layout.json
    d8bdc5da8f4b185d9f1fa58f5e6de4f6b0d3339433822ae8bd9ef42a27257423  .aw/system/layout.schema.json
    SECOND INSTALL layout_artifacts: [] (empty = no-op)
    --- sha256 after second install (identical) ---
    922da2f3360df366cc09891e22994b5d9c6d22837cef169f4570d701f06a8fcd  .aw/system/layout.json
    d8bdc5da8f4b185d9f1fa58f5e6de4f6b0d3339433822ae8bd9ef42a27257423  .aw/system/layout.schema.json
    ```

    The automated twin (`test_reinstall_at_same_version_rewrites_nothing`) additionally asserts
    `st_mtime_ns` is unchanged, which is the assertion that actually pins "no-op rather than rewrite":
    a nondeterministic serializer that happened to produce equal bytes would still fail it.

    PR-003 NEGATIVE CHECK, no emission code added to the workflow body:

    ```text
    $ git diff --name-only
    .aw/.gitignore
    agent_workflows/engine.py
    $ git status --porcelain | grep '^??'
    ?? tests/test_engine_install.py
    $ git diff --name-only -- .aw/system/workflows/setup-repo/setup-repo.md
    (empty = untouched)
    ```

    Only the three declared `Scope-Paths` are touched; the `setup-repo` workflow body is untouched.

    PR-026 SHARED-CHOKEPOINT PROOF. The diff hunk shows the call inside `install_into_repo`:

    ```diff
         artifacts = create_setup_artifacts(repo_root, use_git, dry_run=dry_run)
    +    # wslayout Order 04 (hauwqh), spec kw5y2s Section 6.1: emit the machine-readable layout document
    +    # + its schema for non-Python consumers. Deliberately INSIDE this shared core rather than in a
    +    # caller, so `aw install`, `aw setup`, and library callers all get it by construction. ...
    +    _layout_pre_existing = {
    +        rel: (repo_root / rel).exists()
    +        for rel in (AW_LAYOUT_JSON_PATH, AW_LAYOUT_SCHEMA_PATH)
    +    }
    +    layout_artifacts = emit_layout_artifacts(repo_root, dry_run=dry_run)
    ```

    Confirmed by source introspection rather than by reading the diff alone:

    ```text
    CONFIRMED: emit_layout_artifacts call is INSIDE install_into_repo source
    engine.run() contains emit_layout_artifacts: False (must be False)
    ```

    And demonstrated through the SECOND CLI install path (`aw setup` ->
    `cli._run_setup` -> `cli._install_one`) against a separate temporary repo:

    ```text
    cli._install_one outcome: ok
    === emitted via the aw setup path ===
    -rw-r--r-- 1 3422 Sep  5 18:18 .aw/system/layout.json
    -rw-r--r-- 1 1960 Sep  5 18:18 .aw/system/layout.schema.json
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `.aw/.gitignore` contains `system/layout.json` and `system/layout.schema.json`;
    paste the relevant lines of the file.
  - PLUS proof the ignore WORKS in a freshly installed temporary repo: paste
    `git status --porcelain` showing NEITHER emitted file appears, and
    `git check-ignore -v .aw/system/layout.json .aw/system/layout.schema.json` naming `.aw/.gitignore`
    as the source of the rule.
  - PLUS proof the user's ROOT `.gitignore` carries NO LAYOUT ENTRY. CORRECTED at round 5 (PR-027): the
    earlier wording demanded `git diff -- .gitignore` show NO CHANGE, which is an assertion this plan
    cannot satisfy and must not make. The installer legitimately writes a managed untracked-safety
    `aw:block` and the installer-backups line into the target's ROOT `.gitignore`
    (`engine.py:2576,2698-2735`, both called from `install_into_repo` at `:5506-5507`); on a first
    install that file necessarily changes. Paste instead: `grep -n layout .gitignore` returning NO match
    in the target's root file, and `git check-ignore -v` attributing BOTH emitted paths to
    `.aw/.gitignore` (never to the root file). Optionally show the pre-existing user lines survived.
  - PLUS idempotency across BOTH generation paths (PR-027), since the mechanism is a template plus a
    back-fill list, not one file: (a) FRESH install into a new temporary repo, then install AGAIN, and
    paste evidence `.aw/.gitignore` gained no duplicate line; and (b) BACK-FILL, i.e. start from a repo
    whose `.aw/.gitignore` LACKS the two entries (simulating a repo installed before this change), run
    the install, and     paste evidence both entries were appended exactly once. Case (b) is the one a
    template-only edit silently fails.
  - Observed evidence: verified 2026-09-05 in the same temporary installed repo.

    The framework-owned `.aw/.gitignore` carries both patterns, and the ignore actually TAKES EFFECT:

    ```text
    === .aw/.gitignore entries ===
    33:system/layout.json
    34:system/layout.schema.json
    === git status --porcelain | grep layout ===
    (no output = neither emitted file is visible to git)
    === git check-ignore -v ===
    .aw/.gitignore:33:system/layout.json	.aw/system/layout.json
    .aw/.gitignore:34:system/layout.schema.json	.aw/system/layout.schema.json
    ```

    Both paths are attributed to `.aw/.gitignore`, never to the root file.

    ROOT `.gitignore` CARRIES NO LAYOUT ENTRY (the PR-027 corrected assertion; NOT "no diff", since
    the installer legitimately writes its managed `aw:block` and the backups line there):

    ```text
    === grep -n layout .gitignore ===
    grep exit=1 (1 = no match, correct)
    === user's pre-existing root line survived ===
    2:*.user-tmp
    ```

    IDEMPOTENCY ACROSS BOTH GENERATION PATHS.
    (a) FRESH install then install AGAIN: `.aw/.gitignore` gained no duplicate line (the automated
    twin `test_reinstall_does_not_duplicate_the_patterns` asserts exactly one occurrence of each).
    (b) BACK-FILL, the case a template-only edit silently fails: both entries were STRIPPED from an
    installed repo's `.aw/.gitignore` to simulate a repo installed before this change, then
    `_ensure_aw_gitignore` was run THREE times:

    ```text
    SIMULATED pre-change repo; layout lines now: []
    === after back-fill x3 (exactly one copy each) ===
    33:system/layout.json
    34:system/layout.schema.json
    counts: json=1 schema=1
    === check-ignore still attributes to .aw/.gitignore ===
    .aw/.gitignore:33:system/layout.json	.aw/system/layout.json
    .aw/.gitignore:34:system/layout.schema.json	.aw/system/layout.schema.json
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_engine_install.py` passes cleanly with the ACTUAL
    runner output pasted, and the NEW file is present in the commit.
  - PLUS the BARE FULL SUITE: `python3 -m pytest` (bare) with the `N passed` summary line pasted, zero
    regressions, since this plan changes the installer that every other install test depends on.
  - Observed evidence: run 2026-09-05 in the PRIMARY lane checkout.

    The NEW file, run with `-o addopts=""` so the per-test count is visible (the configured
    `addopts` supplies a `-q` that suppresses it):

    ```text
    $ python3 -m pytest tests/test_engine_install.py -o addopts="" -q
    ..................                                                       [100%]
    18 passed in 29.70s
    ```

    BASELINE re-measured on unmodified HEAD `198bac9249477a07dcd6316333bcce7a54b7958c` (tree clean)
    BEFORE any edit, bare:

    ```text
    $ python3 -m pytest
    31 failed, 4768 passed, 3 skipped, 4 xfailed in 32.61s
    ```

    AFTER this plan's changes, bare:

    ```text
    $ python3 -m pytest
    31 failed, 4786 passed, 3 skipped, 4 xfailed in 35.43s
    ```

    ZERO REGRESSIONS, proven by set comparison rather than by matching counts (equal counts alone
    would not exclude one test breaking while another was fixed). The two `FAILED` id lists were
    sorted and diffed:

    ```text
    $ diff baseline-failed.txt after-failed.txt && echo IDENTICAL
    IDENTICAL FAILURE SETS: zero regressions (4768 -> 4786 passed = +18 new tests)
    ```

    The 31 failures are PRE-EXISTING at the baseline commit and untouched by this plan; they are
    concentrated in `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`,
    `tests/test_ipd_lifecycle_cli.py`, `tests/test_worker_role_refusal.py` and
    `tests/test_novalnomerge_integration.py`, i.e. the runner/lifecycle harness, none of which this
    plan's installer wiring touches. The +18 delta is exactly this plan's new tests.

    RE-VALIDATED AFTER THE `ruff-format` PRE-COMMIT HOOK. The hook reformatted the two Python files
    (pure line-wrapping, no semantic change, inspected before re-staging), so the suite was re-run on
    the COMMITTED tree at `553d970d` rather than trusting the pre-format run:

    ```text
    $ python3 -m pytest tests/test_engine_install.py -o addopts="" -q
    ..................                                                       [100%]
    18 passed in 29.40s
    $ python3 -m pytest
    31 failed, 4786 passed, 3 skipped, 4 xfailed in 35.18s
    $ diff baseline-failed.txt after2-failed.txt && echo IDENTICAL
    POST-COMMIT: IDENTICAL FAILURE SETS vs baseline
    ```

    Leak sanitizer clean:

    ```text
    $ python3 -m agent_workflows check-local-leaks . --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,
     "verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXTERNAL SPEC GATE IS CLEARED (re-measured at plan-review round 5): controlling spec `kw5y2s` is `- Status: approved` with a `--by-human` attestation, so `ipd-lifecycle.md:16` is satisfied. The round-4 "reopened" wording was accurate when written and then outlived its premise: the plans were demoted at commit `298be4b2` (00:10:38 -0400) and the corrected spec was re-approved 459 seconds later at `3e05c2ba` (00:18:17 -0400). RE-VERIFY the spec's `- Status:` line yourself before starting rather than trusting this paragraph; if it is not `approved`, STOP (a genuinely absent prerequisite). The only remaining gate is ordinary human approval of this plan.

Execution contract:

1. Human approval of this plan is required before execution. There are no unresolved blocking questions.
2. Serial prerequisite: `wpu5zu` (Order 01) MUST reach `executed` before starting this plan, as this plan imports `agent_workflows/layout.py`.
3. RE-MEASURE CONCURRENT SCOPE COLLISIONS IMMEDIATELY BEFORE EXECUTION: the prior `6knsrx` example is superseded, so inspect current pending declarations for `agent_workflows/engine.py`. If concurrent edits are in flight, verify mergeability before editing.
4. Emission site invariant: Wire emission solely into `engine.install_into_repo()`; do not add Python code to workflow bodies or non-existent verbs.
5. Gitignore invariant: Add entries only to `.aw/.gitignore`; never modify the target user's root `.gitignore`.
6. File mode and determinism: Write at mode `0o644` with stable key order.
7. Validation requires ACTUAL pasted runner output; never claim a pass without running the commands.
8. Shared checkout discipline: commit only files this plan changed, path-scoped. Verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged`. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
9. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
10. Scope fence: declared paths are `agent_workflows/engine.py`, `.aw/.gitignore`, and `tests/test_engine_install.py`. An out-of-scope edit requires `--scope-reason`, and an unmodified declared path requires `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a concurrent-edit conflict cannot be safely combined.
11. Expect the `check.lifecycle-transition-invalid` diagnostic; it is a known tooling defect (backlog `tk1gqo`) and must not be "fixed" by reordering the history.
12. On completion, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`, and move the plan to `.aw/records/plans/executed/` with `- Status: executed`. The lifecycle transition is a POST-gate step, never an E-item.
