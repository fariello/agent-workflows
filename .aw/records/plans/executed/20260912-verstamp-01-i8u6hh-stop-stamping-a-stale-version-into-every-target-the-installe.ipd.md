# IPD: Stop stamping a stale VERSION into every target: the installer copies the baked file verbatim, bypassing the resolver

- Date: 2026-09-12
- Kind: child
- Concern: The installer treats VERSION as an ordinary file member and copies its bytes verbatim from the source tree, so an install from a dev checkout stamps whatever the last `make version-file` baked (here `1.2.1`) rather than the version of the code being installed. `read_version()` already resolves the correct value from git but is not consulted on the write path, so `versioning.status()` then reports freshly upgraded repos as STALE.
- Scope: Make the VERSION written into a target reflect the framework actually being installed, by resolving the value on the write path instead of copying bytes. Decide and implement the dev-checkout policy, and record the manifest's `installed_version` consistently.
- Scope-Paths: agent_workflows/engine.py, tests/test_installer.py
- Item-Dependencies: none
- Status: executed
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Readiness: go-pending-approval
- Set: verstamp
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: i8u6hh
- From-Backlog: ygtykn

## Workflow history
- 2026-09-23 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: i8u6hh verified (set verstamp, attempt 1).
- 2026-09-23 approved (aw set): Backfilled Priority and Work-Kind by inheritance from source backlog item ygtykn (planprio Order 02, plan 8u6770, E-03); no lifecycle transition occurred.
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-18 reviewed (aw set): status set to reviewed
- 2026-09-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-09-12 to-review (opencode): authored from backlog item ygtykn; write-path root cause verified in-tree.
- 2026-09-12 draft (opencode): created.

## Goal

Make an installed repo's VERSION marker describe the framework it actually received, so the currency classification that drives `aw list-repos`, `aw status`, `aw doctor`, and the downgrade preflight is trustworthy. Today every one of the maintainer's 31 repos reports STALE immediately after being updated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Decide the policy, then implement it on the write path

- [x] E-01 Record the chosen dev-checkout policy in this plan (resolving OQ-01) before changing code, since the code shape follows from it. The two candidates are: (a) always write `read_version(source_root)`, which for a dirty/ahead checkout is a `.devN+g<sha>` string that cannot be mistaken for a release; or (b) write the resolved version but warn when it disagrees with the baked file. Do not invent a third behavior without recording why.
  - Depends on: none
  - Expected outcome: OQ-01 marked resolved with the chosen option and its rationale, matching what E-02 implements.
  - Execution state: performed
  - Execution note: Chose option (a): write `read_version(source_root)` UNCONDITIONALLY, with no divergence warning. OQ-01 below is marked resolved with the rationale. Recorded as decision D-01 in the run's decisions register.
- [x] E-02 In `agent_workflows/engine.py`, make the VERSION member's CONTENT come from `read_version(source_root)` rather than from a verbatim byte copy of the source file. The member is emitted by `collect_source_members` (engine.py:734-740) and its bytes are read via `_member_source_path`, which special-cases VERSION to the nested sibling (engine.py:296-308); that read is the point where the resolved value must be substituted. Preserve the existing trailing-newline shape of the file so a re-install is not reported as a spurious modification.
  - Depends on: E-01
  - Expected outcome: installing from a dirty dev checkout writes the resolved version (e.g. `1.3.0rc2.dev2553+g87759153`) into the target's `.aw/system/VERSION`, not `1.2.1`.
  - Execution state: performed
  - Execution note: Added `_member_source_bytes(source_root, source_relative, source_path)` beside `_member_source_path` in `agent_workflows/engine.py`: it returns a verbatim `read_bytes()` for every member except VERSION, for which it returns `read_version(source_root)` re-encoded with the source file's own trailing terminator (`\r\n`, `\n`, or none) so the newline shape is preserved. BOTH byte-read sites now call it: the install path in `install_all` and the diff PREVIEW in `show_install_diffs`. The preview was included deliberately (not in the plan's letter but required by its intent): had it kept a raw `read_bytes()`, `--dry-run` would advertise a VERSION the install would not write.
- [x] E-03 CONFIRM (do not assume) that the manifest's `installed_version` follows the file automatically, and add no code if it does. It is assigned `read_installed_version(repo_root) or ""` at engine.py:5885, i.e. it READS BACK the just-written target file rather than deriving the version independently, so fixing E-02 should fix the manifest with no further change. This item exists to VERIFY that inference against a real install, because the alternative (two independent derivations) is the failure mode this plan is correcting elsewhere. Record which it turned out to be.
  - Depends on: E-02
  - Expected outcome: for one install, the target's VERSION file and `managed-sections.json`'s `installed_version` are byte-identical strings, achieved with no manifest-specific code change; or, if they diverge, a named reason and the minimal fix.
  - Execution state: performed
  - Execution note: CONFIRMED the read-back inference, and added NO code. The manifest is assigned `read_installed_version(repo_root) or ""` (engine.py, in `install_into_repo`'s post-write step), which reads the just-written TARGET file, so it inherited the corrected value automatically. Verified on a real install (V-03 evidence) and again through the end-to-end rehearsal, where the `manifest-version-unchanged` observation stopped firing at the same time as `version-unchanged`. So it was the single-derivation case, not two independent derivations.
### Task group 2: Regression test

- [x] E-04 Add a test asserting that an install stamps the RESOLVED version, not the baked file's contents. Construct it so it cannot pass vacuously: seed a source whose baked VERSION file differs from what `read_version` resolves, install, and assert the target received the resolved value. This is the exact condition that produced the defect and that no existing test covers.
  - Depends on: E-02, E-03
  - Expected outcome: a named test that fails against pre-fix code and passes after.
  - Execution state: performed
  - Execution note: Added `ResolvedVersionStampTests` to `tests/test_installer.py` (three tests). It cannot pass vacuously: the fixture builds a source whose baked VERSION reads `1.2.1` while the tree is a real git work tree tagged `v7.3.0`, so the resolver answers `7.3.0`, and `test_the_fixture_actually_diverges` ASSERTS that divergence exists before the other tests rely on it. Kept separate from `NestedSourceSiblingVersionTests`, which asserts the opposite equality (installed == the source sibling) and remains correct there because its source is a NON-GIT tree where the resolver's only answer IS the file.
## Project conventions discovered (Step 0)

- VERSION is a DERIVED artifact, regenerated by `make version-file` from the git tag, and explicitly "no longer hand-edited" (engine.py:322-323 docstring). So changing what the installer WRITES does not conflict with any hand-maintained value.
- Release procedure bakes before tagging: `make version-file VERSION=<X.Y.Z>`, commit, then tag (RELEASING.md:46). This is why a RELEASE install is already correct and why this defect is dev-checkout-specific.
- `read_version()` already implements the right precedence: it prefers the git-tag resolver when the source is a real work tree of this project and falls back to the baked file for a copied-out install or unpacked wheel (engine.py:311-330). The fix is to CONSULT it on the write path, not to write new resolution logic.
- `versioning.status()` maps installed-vs-packaged to `not-installed`/`unknown`/`dev`/`stale`/`ahead`/`current` (versioning.py:362) and is consumed by `cli.py` preflight (cli.py:5058), list/status (cli.py:6108, :6152, :6189), and `doctor.py:372`. A wrong stamp therefore propagates to every currency surface.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Measured on nine real repos: an upgrade stamps the OLD version. | Installed VERSION after upgrade `1.2.1`; manifest `installed_version` `1.2.1`; running package `1.3.0rc2.dev2553+g87759153`. |
| F-02 | ROOT CAUSE: VERSION is copied as an ordinary file member, so no resolver runs. | `collect_source_members` appends VERSION as a member (engine.py:734-740) and `_member_source_path` maps it back to the on-disk sibling for a verbatim byte read (engine.py:296-308). The write path never calls `read_version`. |
| F-03 | The correct value is already computable at install time; it is simply not used for the stamp. | `read_version(source_root)` returns `1.3.0rc2.dev2549+g91418d1f.d20260912` for this checkout, while `.aw/system/VERSION` on disk contains `1.2.1`. |
| F-04 | The symptom is user-visible across the whole fleet, not cosmetic. | `aw list-repos` reports `STALE` for all 31 configured repos, including ones just updated; the same classification drives doctor and the downgrade preflight. |
| F-05 | A RELEASE install is NOT affected, which bounds the severity. | RELEASING.md:46 bakes the intended version before tagging, so a tagged tree's VERSION equals its tag. This is why the item is medium, not release-blocking. |
| F-06 | No existing test covers a divergence between the baked file and the resolved version. | The installer suite asserts VERSION is PRESENT and copied (e.g. the `read_installed_version` all-locations test at tests/test_installer.py:2531), never that its VALUE matches the code installed. |

## Proposed changes (ordered, validatable)

1. Record the dev-checkout policy decision (E-01), since E-02's shape depends on it.
2. Substitute the resolved version for the verbatim byte copy at the VERSION read point (E-02).
3. Verify the manifest inherits the corrected value through its existing read-back, adding code only if it does not (E-03).
4. Add the divergence test that the current suite lacks (E-04).

## Deferred / out of scope (with reason)

- The stale `1.2.1` currently committed in this repo's own `.aw/system/VERSION` is NOT re-baked here. That is a release-time action (`make version-file`) governed by RELEASING.md and gated on a human GO; doing it inside this plan would forge a release step. Note the interaction plainly: until it is re-baked, this repo's own source VERSION stays behind the resolver's value, which is precisely the divergence E-04 tests.
- `versioning.status()` and its `dev`/`unknown` classifications are not changed. If the resolved value is a `.devN` string, `status()` already has a `dev` class for it; whether the fleet then reads `dev` instead of `stale` is an OUTPUT of this fix, not a separate change.
- Manifest row accumulation across upgrades (135 rows against 90 files, recorded in plan `8fhjjc` F-10) is a different manifest defect and is not in scope.

## Scope check

- Over-scope: none. One value substitution on the write path, one manifest consistency fix, one test.
- Under-scope: this plan does not re-bake this repo's VERSION (deferred above with reason), so `aw list-repos` may continue to report `dev`/`stale` for the fleet until a release bakes it. V-04 requires stating the post-fix classification explicitly so that residual behavior is observed rather than assumed fixed.

## Required tests / validation

- `python3 -m pytest tests/test_installer.py -o addopts=""` must pass, including the new test. The installer suite is marked slow and is DESELECTED by a bare `python3 -m pytest`, so the explicit path with cleared addopts is required.
- The new test must be confirmed RED before the fix and GREEN after.
- An END-TO-END rehearsal, because a synthetic fixture is what hid this defect: `tools/aw_upgrade_test.py new <legacy-repo> -y -- --to-aw` then `probe`, showing the stamped version now matches the running package and the `version-unchanged`/`manifest-version-unchanged` observations no longer fire.
- Full suite: `python3 -m pytest` must show no NEW failures against the pre-existing baseline. Four failures are already present on untouched HEAD (three `oc profile` undeclared-leaf failures in `tests/test_command_surface_declarations.py` and `tests/test_cli_conformance_matrix.py`, plus `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory`), verified on a pristine worktree of HEAD; they must not be counted as regressions or fixed here.

## Spec / documentation sync

No `.spec.md` file is amended, so none is declared in `Scope-Paths`. No public flag or output format changes. If E-01 selects the warn-on-divergence variant, the warning text is new user-facing output and must be worded as plain prose without em or en dashes, per the repository's user-facing-prose rule.

## Open questions

### OQ-01: For a dev checkout, should the stamp be the resolved `.devN` version, or the baked file with a warning?

- Blocking: no
- Status: resolved
- Owner: opencode (to be settled by E-01 from the evidence below), escalate to the maintainer only if the evidence is genuinely ambiguous
- Resolution or deferral rationale: The repository evidence points at the resolved value: `read_version`'s own docstring states the resolver exists so that "a dirty/ahead checkout reports a `.devN` string that cannot be mistaken for a release" (engine.py:315-317), and `versioning.status()` already has a dedicated `dev` class, so a `.devN` stamp is a state the consumers are built to handle. Not blocking, because either option fixes the reported defect (a stamp that misdescribes the installed code); the choice affects only how a dev install is LABELLED. E-01 must record the decision before E-02 so the implementation is not retrofitted to a choice never stated.
- RESOLVED (E-01, 2026-09-23): OPTION (a), write `read_version(source_root)` UNCONDITIONALLY, with NO divergence warning. Three pieces of in-tree evidence decided it. FIRST, the resolver's contract already says a `.devN+g<sha>` string is the INTENDED answer for a dirty or ahead checkout precisely because it "cannot be mistaken for a release" (engine.py `read_version` docstring), so writing it is the resolver being used as designed rather than a new behavior. SECOND, `versioning.status()` has a dedicated `dev` class distinct from `stale`, so a dev stamp is a state every consumer (`aw list-repos`, `aw status`, `aw doctor`, the downgrade preflight) is already built to classify; measured post-fix, a just-upgraded repo moves from `stale` to `dev`, which is the honest label for a dev install. THIRD, option (b)'s warning would fire on EVERY install from EVERY dev checkout, since the baked file only equals the resolver at a tagged commit (RELEASING.md bakes before tagging), making it unconditional noise that carries no decision for the operator; and it would add new user-facing output, which is a larger public-surface change than this bug fix needs. Rejected any third behavior: writing the baked bytes with a warning was considered and dropped because it LEAVES THE DEFECT IN PLACE, which is the one outcome the plan's Goal forbids.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: quote the OQ-01 resolution text as committed, and confirm in one sentence that E-02's implementation matches the option chosen there (not merely that a decision exists).
  - Observed evidence: OQ-01 `- Status:` now reads `resolved`, and its committed resolution line opens: "RESOLVED (E-01, 2026-09-23): OPTION (a), write `read_version(source_root)` UNCONDITIONALLY, with NO divergence warning." E-02's implementation MATCHES that option rather than merely existing: `_member_source_bytes` returns `read_version(source_root).encode("utf-8")` for the VERSION member on every call with no conditional and no comparison against the baked file, and a repo-wide check confirms the rejected variant was not built, since the diff adds no warning emitter at all:

    ```
    $ git diff -- agent_workflows/engine.py | grep -nEi '^\+.*(warn|stderr)'
    (no output)
    ```

    So the code writes the resolved value unconditionally and warns never, which is exactly option (a) and not option (b).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste, for one install into a throwaway target from this dev checkout, all three values side by side: `read_version(source_root)`, the target's `.aw/system/VERSION` contents, and `aw --version`. The first two must agree. Pre-fix, the file read `1.2.1` while the resolver returned a `1.3.0rc2.dev*` string; show that divergence is gone.
  - Observed evidence: one real install from this dev checkout into a throwaway git target, via `engine.install_into_repo(target, resolve_source_root(Path('.')))`:

    ```
    read_version(source_root)      = '1.3.0rc2.dev3716+g0189db24.d20260923'
    target .aw/system/VERSION      = '1.3.0rc2.dev3716+g0189db24.d20260923\n'
    manifest installed_version     = '1.3.0rc2.dev3716+g0189db24.d20260923'
    source baked .aw/system/VERSION= '1.2.1\n'
    --- aw --version ---
    agent-workflows 1.3.0rc2.dev3716+g0189db24.d20260923
    ```

    The resolver, the stamped target file, and `aw --version` all agree on `1.3.0rc2.dev3716+g0189db24.d20260923`. The divergence is GONE while its CAUSE is still present: the source's baked file still reads `1.2.1`, so the target is no longer inheriting it. Pre-fix the same measurement on this tree gave `target .aw/system/VERSION = '1.2.1\n'` against the same resolver value, reproduced under the RED run in V-04 (`AssertionError: '1.2.1\n' != '7.3.0\n'`).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the target's VERSION file contents and the `installed_version` field from its `managed-sections.json` for the SAME install, showing byte-identical strings.
  - Observed evidence: from the SAME install as V-02 (the two values printed in one run, quoted above and repeated here side by side):

    ```
    target .aw/system/VERSION   = '1.3.0rc2.dev3716+g0189db24.d20260923\n'
    manifest installed_version  = '1.3.0rc2.dev3716+g0189db24.d20260923'
    ```

    Byte-identical as strings (the file carries the trailing newline the manifest field does not, since `read_installed_version` strips it). Achieved with NO manifest-specific code change, confirming the plan's inference: `git diff -- agent_workflows/engine.py` touches only `_member_source_bytes` and its two call sites, and the `manifest.installed_version = read_installed_version(repo_root) or ""` assignment is unmodified. Independently corroborated by the end-to-end rehearsal in V-04, where `manifest-version-unchanged` stopped firing without the manifest code being touched.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the RED run (new test failing pre-fix, with its assertion message) and the GREEN run post-fix including the `N passed` line. Then paste an end-to-end `tools/aw_upgrade_test.py new <repo> -y -- --to-aw` probe output showing the `version-unchanged` and `manifest-version-unchanged` observations no longer appear, and state what `aw list-repos` now reports for a just-updated repo (`current` or `dev`), so the residual fleet-wide classification is observed rather than assumed.
  - Observed evidence: RED, run against a pristine `git archive HEAD` tree carrying the NEW test but the UNFIXED engine (the contract forbids stashing in a shared checkout, so the pre-fix state was reproduced by exporting HEAD rather than by reverting the working tree):

    ```
    E       AssertionError: '1.2.1\n' != '7.3.0\n'
    E       - 1.2.1
    E       + 7.3.0
    E        : the target was stamped '1.2.1\n'; the source's baked file holds '1.2.1\n' while the
    code being installed resolves to '7.3.0'. FIX: VERSION is the one DERIVED install member, so its
    content must come from `read_version(source_root)` and not from a verbatim byte copy. [...]

    FAILED tests/test_installer.py::ResolvedVersionStampTests::test_install_stamps_the_resolved_version_and_the_manifest_follows
    ========================= 1 failed, 2 passed in 0.95s ==========================
    ```

    The two that passed RED are the fixture-divergence guard and the idempotence test, which are correctly version-agnostic pre-fix; the stamping claim is the one that fails, which is the intended falsifiability.

    GREEN, same test against the fixed engine:

    ```
    tests/test_installer.py::ResolvedVersionStampTests::test_the_fixture_actually_diverges PASSED [ 33%]
    tests/test_installer.py::ResolvedVersionStampTests::test_a_second_install_is_idempotent PASSED [ 66%]
    tests/test_installer.py::ResolvedVersionStampTests::test_install_stamps_the_resolved_version_and_the_manifest_follows PASSED [100%]

    ============================== 3 passed in 0.83s ===============================
    ```

    Full installer suite, `python3 -m pytest tests/test_installer.py -o addopts=""`:

    ```
    FAILED tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
    FAILED tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed
    ================== 2 failed, 115 passed in 174.09s (0:02:54) ===================
    ```

    Both failures are PRE-EXISTING, not regressions, and were re-verified on a pristine export of untouched HEAD in this same worktree, failing identically there (`2 failed, 8 passed in 27.30s`). The first is named in the plan's declared baseline. The second is NOT in that baseline but is not new either: its own docstring declares it a pre-existing failure verified at HEAD commit `6123749b` (the gitignored `.aw/workflow-artifacts/README.md` is classified at-risk, so `all_recoverable` is False). Recorded as decision D-02 and reported as a defect-report finding, since the plan's baseline understates the count by one.

    END-TO-END rehearsal, `tools/aw_upgrade_test.py new ansurv -y -- --to-aw` (run with `PYTHONPATH` pinned to this worktree, because the rehearsal tool spawns `python3 -m agent_workflows` and would otherwise import the editable install from the MAIN checkout and rehearse code without the fix; that mistake was made once and caught, see decision D-03):

    ```
    Baseline: version=1.2.1 layout=legacy (clean)
    install: exit=0 in 5.76s
    After:    version=1.3.0rc2.dev3716+g0189db24.d20260923 (.aw/system/VERSION) layout=aw+litter
    Manifest: installed_version=1.3.0rc2.dev3716+g0189db24.d20260923 rows=307 schema=2

    Observations (evidence, not verdicts):
      [empty-legacy-dirs] Migrated to .aw, but 9 empty directory(ies) remain under .agents/. [...]
      [legacy-leftovers] 93 file(s) still under .agents/ after a MIGRATING run [...]
      [orphaned-skills] 92 file(s) remain under .agents/skills/ [...]
    ```

    Both `version-unchanged` and `manifest-version-unchanged` are ABSENT from the observation list, where the pre-fix run of the same command on the same repo reported them explicitly ("Installed VERSION is still 1.2.1 after the upgrade", "Manifest still records installed_version=1.2.1"). The three surviving observations are pre-existing legacy-litter findings unrelated to versioning.

    RESIDUAL FLEET CLASSIFICATION, observed rather than assumed: a just-updated repo now reports `dev`, NOT `current`.

    ```
    packaged:  1.3.0rc2.dev3716+g0189db24.d20260923
    installed: 1.3.0rc2.dev3716+g0189db24.d20260923
    status: dev

    BEFORE the fix, installed was 1.2.1 -> stale
    ```

    So `aw list-repos` moves a freshly upgraded repo from `stale` to `dev`. That is the CORRECT label for an install from an untagged dev checkout and is the outcome the plan's Deferred section predicted; reaching `current` requires a release to bake VERSION, which this plan deliberately does not do.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`Status: approved`) before any code change. The executor must: commit only the files listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`), never `git add -A` and never push; paste ACTUAL runner output for every `V-*` item; and must NOT run `make version-file` or otherwise re-bake this repository's VERSION, which is a release-time action gated on a human GO under RELEASING.md. Post-gate lifecycle: once every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` reports conforming, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`, never a raw `git mv` plus commit. Backlog item `ygtykn` closes only after this plan is executed; it carries no release gate (see F-05), so it does not block 2.0.0.
