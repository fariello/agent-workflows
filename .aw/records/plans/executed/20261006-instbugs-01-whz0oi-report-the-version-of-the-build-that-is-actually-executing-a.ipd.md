# IPD: Report the version of the build that is actually executing, and warn when an installed build is stale

- Date: 2026-10-06
- Kind: child
- Concern: Defect D01 of research report `l6cbbb`, reproduced at HEAD `474b037a9`: a wheel built from HEAD into a throwaway venv reports `pip show agent-workflows` -> `Version: 1.3.0rc2.dev8193+g474b037a9` while `aw --version` (run from `/tmp` with `AW_NO_REEXEC=1`) prints `agent-workflows 1.2.1`, and the installer writes `1.2.1` into the target's `.aw/system/VERSION` (scratch target: `cat .aw/system/VERSION` -> `1.2.1`). The wheel METADATA version comes from `hatch_build.VERSION` (git-resolved), but `[tool.hatch.build.targets.wheel.force-include]` copies the COMMITTED `.aw/system/VERSION` verbatim into `agent_workflows/_data/.aw/system/VERSION`, and `agent_workflows/__init__._resolve_own_version` reads that bundled file for any installed package. So every installed build reports whatever version string was last committed, and a user running August code is told they run 1.2.1. Nothing tells a user that a local-directory build is behind the checkout it came from.
- Scope: IN: (1) bake the build-time resolved version into the wheel's bundled `VERSION` so the bundled file, the dist METADATA and the version an install writes into a target all agree; (2) make `_resolve_own_version` prefer the installed distribution's own metadata version when the package runs from an installed distribution, keeping the bundled file as fallback; (3) an `aw doctor` signal that warns when the installed distribution was built from a local directory (`direct_url.json` with a `file://` url and no `editable` flag) whose git HEAD differs from the build's `+g<sha>`, naming the rebuild command. OUT: changing the git-tag-driven version scheme (D44); a warning on every `aw` invocation (see Scope check); registry or editable installs (both run the code they report).
- Scope-Paths: hatch_build.py, pyproject.toml, agent_workflows/__init__.py, agent_workflows/versioning.py, agent_workflows/doctor.py, agent_workflows/cli.py, tests/test_installed_version_reporting.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: instbugs
- Order: 1
- Highest E allocated: 06
- Author: antigravity/claude-opus-5.5
- Id: whz0oi

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: whz0oi verified (set instbugs, attempt 1).
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0
- 2026-10-07 reviewed (aw set): plan-review

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007. Reviewed at HEAD `aa139e584` in an isolated review-sweep lane; plan committed and byte-identical to the lane input, so no pre-review snapshot. Demonstrated with hatchling 1.32.4 that a hook `force_include` file entry overrides the directory force-include (F-06) and that an sdist-built wheel's `metadata.version` comes from `PKG-INFO` while the `code` source falls back to the stale file (F-05). Fixed: hook bakes `self.metadata.version`, not `hatch_build.VERSION` (PR-001); E-03 resolves the sibling dist-info, not first-on-`sys.path` (PR-002); `--version` note split to E-06 with `cli.py` in Scope-Paths and V-06 (PR-003); E-04 failure and edge cases, git timeout, Drift plus remediation surface (PR-004); `- Blocks-Release: next` added per the live-bug rule (PR-005); gate gains honesty rule, scope fence, conditional finalize ownership, and V-02/V-04 gain sdist and re-exec evidence (PR-006); deferred row `Carrier: none (...)` was malformed and failed `check.ipd-uncarried-obligation` at error, replaced with `Carrier-Declined:` (PR-007).
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 01 of Set `instbugs` after reproducing D01 at HEAD `474b037a9`; the cause is a stale bundled VERSION file, not the git-at-runtime cause the report guessed.

## Goal

An installed `aw` reports the version of the code that is executing, the same string `pip show` reports and the same string it writes into a target, and `aw doctor` tells a user whose local-directory build is behind its source checkout exactly how to rebuild.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish the defect

- [x] E-01 Re-measure D01 at the execution HEAD before any edit: build the tree into a throwaway venv under a temp dir (`python3 -m venv <tmp>/v && <tmp>/v/bin/pip install .`), then from a directory outside the checkout with `AW_NO_REEXEC=1` record `pip show agent-workflows | grep ^Version`, `aw --version`, and the content of `<site-packages>/agent_workflows/_data/.aw/system/VERSION`.
  - Depends on: none
  - Expected outcome: the three strings pasted; the defect holds if `aw --version` differs from the pip version. STOP and report if they already agree.
  - Execution state: performed

### Task group 2: make the reported version true

- [x] E-02 Bake the resolved version into the bundled VERSION at wheel build time: add a hatchling build hook (a `BuildHookInterface` subclass named `CustomBuildHook` in `hatch_build.py`, inside the existing `try: ... except ImportError` hatchling guard, registered under `[tool.hatch.build.hooks.custom]` in `pyproject.toml`). In `initialize(version, build_data)`, when `self.target_name == "wheel"`, write `self.metadata.version` (NOT `hatch_build.VERSION`; see Findings F-05) plus a trailing newline to a generated temp file, and set `build_data["force_include"][<temp file>] = "agent_workflows/_data/.aw/system/VERSION"`, so the committed `.aw/system/VERSION` in the source tree is never modified. Keep the actual write in a small module-level function (`write_bundled_version(version, out_dir) -> Path`) so E-05(a) can call it without hatchling. The sdist target is untouched (it ships the committed file, and a wheel built from that sdist re-bakes via this same hook).
  - Depends on: E-01
  - Expected outcome: a freshly built wheel's bundled VERSION equals its METADATA `Version`, for a wheel built from the git tree AND for a wheel built from an sdist of it; the working tree's `.aw/system/VERSION` is byte-identical before and after a build.
  - Execution state: performed

- [x] E-03 In `agent_workflows/__init__._resolve_own_version`, when `packaged_source_root()` is not None (installed package), look up the distribution that OWNS this module rather than any distribution named `agent-workflows` on `sys.path` (a second copy elsewhere on `sys.path` must not answer): locate the `agent_workflows-*.dist-info` directory that is a sibling of this package's directory (`Path(__file__).resolve().parent.parent`), read it with `importlib.metadata.Distribution.at(...)`, and return its `.version`. If no sibling dist-info resolves, fall back to the bundled VERSION exactly as today. Never raise (the function's existing contract). The source-checkout branch is unchanged. Do not add a module-level import cost to the source-checkout path: import `importlib.metadata` inside the installed branch only.
  - Depends on: E-02
  - Expected outcome: an installed build reports its own distribution's version even if a stale bundled VERSION were shipped; a source checkout still reports the git-described version.
  - Execution state: performed

- [x] E-04 Add an `aw doctor` signal `doctor.stale-build` emitted from `doctor.probe_environment` as a `core.Drift` beside the existing `doctor.version-*` and `doctor.pypi-update-available` drift, with a matching `build_remediation` branch (title, `summary_fix`, `command`) so the human and `--agent` renderings both carry the remedy. Detection, in a helper in `doctor.py` that takes the dist-info path as an argument (so E-05 can drive it): read the running distribution's `direct_url.json` (the same sibling dist-info E-03 locates); when its url is `file://<dir>`, `dir_info.editable` is not true, `<dir>` is a git work tree, and its `git rev-parse --short=<len of the build sha> HEAD` differs from the `+g<sha>` local segment of the running version, report both shas, the commit distance if `git rev-list --count <build-sha>..HEAD` succeeds, and the remedy `pip install <dir>`. When the build sha is not an object in `<dir>` (history rewritten, different clone), still warn, omit the distance, and say so. A `.d<date>` dirty segment in the running version is ignored for the comparison. No signal for editable, registry (no `direct_url.json`), non-`file://`, missing directory, non-git directory, a version with no `+g<sha>` segment, or a `git` that fails or times out. Every `git` call carries a timeout (5 seconds) and its failure yields no signal, never an exception out of the probe.
  - Depends on: E-03
  - Expected outcome: a stale local build produces exactly one `doctor.stale-build` drift naming both shas and the rebuild command; a current build, an editable install, a registry install and each unparseable case produce none.
  - Execution state: performed

- [x] E-06 Make `aw --version` append one line noting a stale build only when the E-04 helper fires: replace the `action="version"` argument in `cli._build_parser` with an action (or an early check in `cli.main` before parsing) that prints `agent-workflows <version>` and then, only when `direct_url.json` exists for the running distribution and the E-04 check reports stale, a second line naming the rebuild command. The staleness check must run ONLY when `--version`/`-V` is actually requested, never at parser construction, so no other `aw` command pays a `git` call. The first output line is byte-identical to today's for every non-stale case.
  - Depends on: E-04
  - Expected outcome: `aw --version` on a stale local build prints the version line plus one stale note; on a current, editable or registry build it prints only the version line; no other command invokes `git rev-parse` because of this change.
  - Execution state: performed

### Task group 3: pin it

- [x] E-05 Add `tests/test_installed_version_reporting.py`: (a) call `hatch_build.write_bundled_version` against a temp directory and assert the generated VERSION content equals the supplied version and that the source `.aw/system/VERSION` is unchanged; (b) build a synthetic site-packages under `tempfile` with a fake `agent_workflows-9.9.9.dev1+gabc1234.dist-info` (METADATA, RECORD, `direct_url.json` pointing at a temp git repo whose HEAD is a different commit) and drive the E-04 helper, asserting the drift, its shas and its remedy text; repeat with `editable: true`, with no `direct_url.json` (registry), with a non-git directory, and with a version lacking `+g<sha>`, asserting no drift; and drive the E-06 `--version` path via `cli.main(["--version"])` with the helper pointed at the stale fixture, asserting the second line, and at a current fixture, asserting exactly one line; (c) one `@pytest.mark.slow` end-to-end test that builds the wheel (`python -m build --wheel`, skipping via `unittest.SkipTest` when `build` is not importable, the `tests/test_packaging.py` precedent) into a temp venv and asserts, from a cwd outside the checkout with `AW_NO_REEXEC=1`, that `aw --version` equals the dist-info version and that the bundled `_data/.aw/system/VERSION` equals it too. Prove (b) can fail by inverting the sha comparison and pasting the failure, then restore.
  - Depends on: E-06
  - Expected outcome: the fast tests pass; the slow test passes when run with `-m slow`; the mutation fails (b); no test reads production source.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Versioning has ONE authority, `versioning.resolve_version` (DECISIONS D44); `hatch_build.VERSION` already calls it, so the build hook reuses that value rather than resolving again.
- Zero runtime dependencies (D46): `importlib.metadata` is stdlib; no `hatch-vcs`.
- `aw` re-execs into the checkout's package when invoked inside a checkout (observed message "re-running with <checkout>'s package (set AW_NO_REEXEC=1 to disable)"), so reproduction and tests must run outside the checkout or set `AW_NO_REEXEC=1`.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The bundled VERSION in a HEAD wheel is the committed `1.2.1`, while METADATA is `1.3.0rc2.dev8193+g474b037a9`. | `cat <site>/agent_workflows/_data/.aw/system/VERSION` -> `1.2.1`; `cat .aw/system/VERSION` in the checkout -> `1.2.1`; `pip show` -> `1.3.0rc2.dev8193+g474b037a9` |
| F-02 | The `hatch_build` docstring states the intended invariant ("The WHEEL version must equal `agent_workflows.versioning.resolve_version` and what `make version-file` bakes into `.aw/system/VERSION`"), but `make version-file` is a manual step and the wheel build never runs it. | `hatch_build.py` module docstring; `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` `".aw/system" = "agent_workflows/_data/.aw/system"` |
| F-03 | The installer propagates the wrong string into targets. | scratch target `.aw/system/VERSION` -> `1.2.1` |
| F-04 | `doctor` already reports installed-versus-packaged for the REPO marker (`res.installed_version` from `engine.read_installed_version`, `res.packaged_version` from `versioning.resolve_version`), so the new signal sits beside an existing one rather than inventing a surface. | `doctor.probe_environment` fields `installed_version`, `packaged_version`; drift `doctor.pypi-update-available` with its `build_remediation` branch |
| F-05 | (review) In a wheel built FROM AN SDIST, hatchling takes the dist version from the sdist's `PKG-INFO`, while `hatch_build.VERSION` falls back to the committed VERSION file (no git), so baking `hatch_build.VERSION` would reproduce D01 for sdist-built wheels. `self.metadata.version` inside the hook is the correct value in both cases. | Review probe with hatchling 1.32.4: project with a `code` version source reading a `1.2.1` file and a `PKG-INFO` of `1.3.0rc2.dev5+gabc1234`; hook printed `metadata.version= 1.3.0rc2.dev5+gabc1234  code VERSION= 1.2.1`; wheel named `fi-1.3.0rc2.dev5+gabc1234` and its bundled VERSION `b'1.3.0rc2.dev5+gabc1234\n'`. `hatchling/metadata/core.py` reads `PKG-INFO` from the project root for dynamic fields. |
| F-06 | (review) A build hook's `build_data["force_include"]` entry for a single file overrides the same path supplied by the directory-level `[tool.hatch.build.targets.wheel.force-include]`, with no duplicate entry. | Review probe: dir force-include `"data" = "pkg/_data/system"` (VERSION `1.2.1`) plus hook entry for `pkg/_data/system/VERSION`; wheel namelist had exactly one `pkg/_data/system/VERSION`, content `b'9.9.9\n'`; source file still `1.2.1`. |
| F-07 | (review) `importlib.metadata.version("agent-workflows")` resolves the FIRST matching distribution on `sys.path`, not the one this module was imported from, so with two copies installed it can report the wrong one; resolving the sibling dist-info with `Distribution.at` avoids that. | `importlib.metadata` resolves by name over `sys.path`; a local `pip install` writes `direct_url.json` `{"dir_info": {}, "url": "file:///..."}` into the sibling `<name>-<ver>.dist-info` (review probe on a local-dir install). |
| F-08 | (review) `aw --version` is an argparse `action="version"` with a string fixed at parser build, so the conditional stale note needs its own action or an early check; this edits `cli.py`, which the original `Scope-Paths` omitted. | `cli._build_parser`: `parser.add_argument("-V", "--version", action="version", version=f"agent-workflows {__version__}", ...)` |

## Proposed changes (ordered, validatable)

1. Build hook writes the hook's resolved metadata version into the bundled VERSION (E-02).
2. Installed package reports its own sibling dist-info version (E-03).
3. `doctor.stale-build` signal with remedy (E-04).
4. Conditional `aw --version` stale note (E-06).
5. Tests including a slow end-to-end wheel build (E-05).

## Deferred / out of scope (with reason)

- A STALENESS CHECK ON EVERY `aw` INVOCATION. Every command would pay a `git` subprocess against a directory that may be on a slow mount; `aw doctor` and `aw --version` are where a user asks this question.
  - Carrier-Declined: deliberately not done; `aw doctor` and `aw --version` (E-04, E-06) are the surfaces where a user asks this question, so no follow-up obligation exists.

## Scope check

- Over-scope: none.
- Under-scope: the committed `.aw/system/VERSION` remains a manually baked file for source and sdist use; this plan makes the WHEEL independent of whether it was refreshed.

## Required tests / validation

- `tests/test_installed_version_reporting.py` (E-05), including the mutation proof.
- Bare `python3 -m pytest` with the actual summary line pasted, compared with a pre-edit baseline in the same worktree.
- The slow test run explicitly with `python3 -m pytest -o addopts="" -m slow tests/test_installed_version_reporting.py` and its output pasted.

## Spec / documentation sync

- Update the `agent_workflows/__init__.py` module docstring ("an installed wheel reads its baked VERSION") to state that an installed wheel reports its distribution version.
- Update the `hatch_build.py` docstring to state that the build hook bakes the version, replacing the reliance on `make version-file`, and to list the build hook as the third plugin the file hosts.
- Update the `_resolve_own_version` docstring's "Installed wheel" bullet to the sibling-dist-info rule and its fallback.
- No spec governs these surfaces (no `.spec.md` in Scope-Paths); `DECISIONS.md` D44 already names the resolver as the single authority, which this plan preserves, so no decision record changes.

## Open questions

### OQ-01: Should the wheel version and the committed VERSION file be forced equal in CI instead?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: no. A dev build's version changes with every commit (`.devN+g<sha>`), so a committed file can never equal it; only the build can know the value. Baking at build time removes the class of skew entirely.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `pip show` version, `aw --version` output and bundled VERSION content, with the HEAD sha.
  - Observed evidence:
    HEAD SHA: ded43ab96e8a5dfe6d52b741332ec237f5549e8c
    pip show agent-workflows: Version: 1.3.0rc2.dev8751+gded43ab96
    aw --version: agent-workflows 1.2.1
    Bundled VERSION: 1.2.1
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: after rebuilding, PASTE the bundled VERSION content and `pip show` version (equal), and `git diff --stat -- .aw/system/VERSION` showing no change. Then build an sdist (`python3 -m build --sdist`), build a wheel FROM that sdist, and PASTE that wheel's bundled VERSION and METADATA `Version` (equal, and not the committed `1.2.1` unless HEAD is that tag).
  - Observed evidence:
    Rebuilding wheel:
    Wheel bundled VERSION: 1.3.0rc2.dev8751+gded43ab96.d20261008
    Pip show version: Version: 1.3.0rc2.dev8751+gded43ab96.d20261008
    git diff --stat -- .aw/system/VERSION: (empty diff, 0 files changed)
    Building sdist and wheel from sdist:
    Built sdist: agent_workflows-1.3.0rc2.dev8751+gded43ab96.d20261008.tar.gz
    Sdist-built wheel bundled VERSION: 1.3.0rc2.dev8751+gded43ab96.d20261008
    Sdist-built wheel METADATA: Version: 1.3.0rc2.dev8751+gded43ab96.d20261008
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE `aw --version` from outside the checkout with `AW_NO_REEXEC=1`, equal to the `pip show` version, and `python3 -c "import agent_workflows; print(agent_workflows.__version__)"` run inside the checkout showing the git-described version.
  - Observed evidence:
    Installed venv outside checkout with AW_NO_REEXEC=1:
    PIP_VER: Version: 1.3.0rc2.dev8751+gded43ab96.d20261008
    AW_VER: agent-workflows 1.3.0rc2.dev8751+gded43ab96.d20261008
    Inside checkout:
    python3 -c "import agent_workflows; print(agent_workflows.__version__)":
    1.3.0rc2.dev8751+gded43ab96.d20261008
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: run from a cwd outside the checkout with `AW_NO_REEXEC=1` (otherwise `aw` re-execs into the checkout's package and the probe sees no dist-info). PASTE `aw doctor` output from a venv whose local build is at least one commit behind its source (make one throwaway commit in a temp clone, build from it, then add a commit) showing the `doctor.stale-build` warning with both shas and the rebuild command; and PASTE `aw doctor` from a current build showing no such line.
  - Observed evidence:
    Stale build commit: 68fb26488c, clone HEAD: f207e2916c
    aw doctor output (stale):
      1. Installed build is behind local source checkout (1 file)
         Fix: pip install /tmp/aw-v04-wKz5PT/clone
    aw doctor --agent output (stale):
      {"schema":"aw.agent/v1","kind":"result","cmd":"doctor","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":3,"evidence":["git","env","attention","sanitizer","artifacts"],"diagnostics":[{"location":"<build>","rule":"doctor.stale-build"},{"location":"<sanitizer>","rule":"doctor.probe-failed"},{"location":"<version>","rule":"doctor.version-not-installed"}],"next":"pip install /tmp/aw-v04-agent-1JOILf/clone"}
    aw doctor output (current, after pip install):
      No 'doctor.stale-build' or 'Installed build is behind local source checkout' finding reported.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE `aw --version` from the stale venv built for V-04 (version line plus the stale note naming the rebuild command) and from the current venv (exactly the version line). Reachable via E-06's new `--version` path in `cli`, which calls the E-04 helper.
  - Observed evidence:
    aw --version output (stale):
    agent-workflows 1.3.0rc2.dev8752+g68fb26488
    warning: build is stale; rebuild with 'pip install /tmp/aw-v04-wKz5PT/clone'
    aw --version output (current):
    agent-workflows 1.3.0rc2.dev8753+gf207e2916
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file (fast tests) and of the slow test, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
    Fast tests narrowed run:
    python3 -m pytest tests/test_installed_version_reporting.py
    8 passed in 5.43s
    Slow test narrowed run:
    python3 -m pytest -o addopts="" -m slow tests/test_installed_version_reporting.py
    1 passed, 8 deselected in 19.98s
    Mutation failure (inverting build SHA comparison check):
    .....FFF                                                                 [100%]
    =================================== FAILURES ===================================
    _______ InstalledVersionReportingTests.test_stale_build_drift_detection ________
    3 failed, 5 passed in 6.12s
    Bare-suite summary line:
    6618 passed, 2 skipped, 3 warnings in 857.69s (0:14:17)
    (Baseline: 6610 passed, 2 skipped, 3 warnings in 565.38s; net +8 passed tests).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in dependency order (E-01, E-02, E-03, E-04, E-06, E-05). Commit only files changed for this plan through `aw commit whz0oi -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output does not satisfy any item. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize whz0oi`, never by a hand `git mv`.
