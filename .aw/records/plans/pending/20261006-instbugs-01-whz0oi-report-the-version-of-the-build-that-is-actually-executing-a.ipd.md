# IPD: Report the version of the build that is actually executing, and warn when an installed build is stale

- Date: 2026-10-06
- Kind: child
- Concern: Defect D01 of research report `l6cbbb`, reproduced at HEAD `474b037a9`: a wheel built from HEAD into a throwaway venv reports `pip show agent-workflows` -> `Version: 1.3.0rc2.dev8193+g474b037a9` while `aw --version` (run from `/tmp` with `AW_NO_REEXEC=1`) prints `agent-workflows 1.2.1`, and the installer writes `1.2.1` into the target's `.aw/system/VERSION` (scratch target: `cat .aw/system/VERSION` -> `1.2.1`). The wheel METADATA version comes from `hatch_build.VERSION` (git-resolved), but `[tool.hatch.build.targets.wheel.force-include]` copies the COMMITTED `.aw/system/VERSION` verbatim into `agent_workflows/_data/.aw/system/VERSION`, and `agent_workflows/__init__._resolve_own_version` reads that bundled file for any installed package. So every installed build reports whatever version string was last committed, and a user running August code is told they run 1.2.1. Nothing tells a user that a local-directory build is behind the checkout it came from.
- Scope: IN: (1) bake the build-time resolved version into the wheel's bundled `VERSION` so the bundled file, the dist METADATA and the version an install writes into a target all agree; (2) make `_resolve_own_version` prefer the installed distribution's own metadata version when the package runs from an installed distribution, keeping the bundled file as fallback; (3) an `aw doctor` signal that warns when the installed distribution was built from a local directory (`direct_url.json` with a `file://` url and no `editable` flag) whose git HEAD differs from the build's `+g<sha>`, naming the rebuild command. OUT: changing the git-tag-driven version scheme (D44); a warning on every `aw` invocation (see Scope check); registry or editable installs (both run the code they report).
- Scope-Paths: hatch_build.py, pyproject.toml, agent_workflows/__init__.py, agent_workflows/versioning.py, agent_workflows/doctor.py, tests/test_installed_version_reporting.py
- Item-Dependencies: none
- Status: to-review
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: high
- Set: instbugs
- Order: 1
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: whz0oi

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 01 of Set `instbugs` after reproducing D01 at HEAD `474b037a9`; the cause is a stale bundled VERSION file, not the git-at-runtime cause the report guessed.

## Goal

An installed `aw` reports the version of the code that is executing, the same string `pip show` reports and the same string it writes into a target, and `aw doctor` tells a user whose local-directory build is behind its source checkout exactly how to rebuild.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish the defect

- [ ] E-01 Re-measure D01 at the execution HEAD before any edit: build the tree into a throwaway venv under a temp dir (`python3 -m venv <tmp>/v && <tmp>/v/bin/pip install .`), then from a directory outside the checkout with `AW_NO_REEXEC=1` record `pip show agent-workflows | grep ^Version`, `aw --version`, and the content of `<site-packages>/agent_workflows/_data/.aw/system/VERSION`.
  - Depends on: none
  - Expected outcome: the three strings pasted; the defect holds if `aw --version` differs from the pip version. STOP and report if they already agree.
  - Execution state: pending

### Task group 2: make the reported version true

- [ ] E-02 Bake the resolved version into the bundled VERSION at wheel build time: add a hatchling build hook (a `BuildHookInterface` subclass in `hatch_build.py`, registered under `[tool.hatch.build.hooks.custom]` in `pyproject.toml`) that writes `hatch_build.VERSION` into the wheel's `agent_workflows/_data/.aw/system/VERSION` (via `build_data["force_include"]` pointing at a generated temp file, so the committed `.aw/system/VERSION` in the source tree is never modified). Keep the sdist fallback described in the `hatch_build` docstring working.
  - Depends on: E-01
  - Expected outcome: a freshly built wheel's bundled VERSION equals its METADATA `Version`; the working tree's `.aw/system/VERSION` is byte-identical before and after a build.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/__init__._resolve_own_version`, when `packaged_source_root()` is not None (installed package), return `importlib.metadata.version("agent-workflows")` if the distribution resolves and its files include this module, else fall back to the bundled VERSION as today. The source-checkout branch is unchanged.
  - Depends on: E-02
  - Expected outcome: an installed build reports its distribution version even if a stale bundled VERSION were shipped; a source checkout still reports the git-described version.
  - Execution state: pending

- [ ] E-04 Add an `aw doctor` signal `doctor.stale-build` (warn severity, human and `--agent` renderings): read the running distribution's `direct_url.json`; when its url is `file://<dir>`, `dir_info.editable` is not true, `<dir>` is a git work tree, and its `git rev-parse --short HEAD` differs from the `+g<sha>` local segment of the running version, report both shas, the commit distance if `git rev-list --count <sha>..HEAD` succeeds, and the remedy `pip install <dir>` (or `make install` if the repo documents one). No signal for editable, registry, or unparseable cases. Mention the warning in `aw --version` output only when that same cheap check fires (one `git rev-parse` call, skipped when `direct_url.json` is absent).
  - Depends on: E-03
  - Expected outcome: a stale local build produces one warning naming the rebuild command; a current build, an editable install and a registry install produce none.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_installed_version_reporting.py`: (a) call the build hook's version-writing function against a temp build directory and assert the generated VERSION content equals the supplied resolved version and that the source `.aw/system/VERSION` is unchanged; (b) build a synthetic site-packages under `tempfile` with a fake `agent_workflows-9.9.9.dev1+gabc1234.dist-info` (METADATA, RECORD, `direct_url.json` pointing at a temp git repo whose HEAD is a different commit) and drive the doctor signal function, asserting the warning, its shas and its remedy text; repeat with `editable: true` and with a registry install (no `direct_url.json`) asserting no warning; (c) one `@pytest.mark.slow` end-to-end test that builds the wheel into a temp venv and asserts `aw --version` equals `pip show`'s version. Prove (b) can fail by inverting the sha comparison and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the fast tests pass in under a few seconds; the slow test passes when run with `-m slow`; the mutation fails (b); no test reads production source.
  - Execution state: pending

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
| F-04 | `doctor` already reports installed-versus-packaged for the REPO marker (`res.installed_version` from `engine.read_installed_version`, `res.packaged_version` from `versioning.resolve_version`), so the new signal sits beside an existing one rather than inventing a surface. | `doctor.py` fields `installed_version`, `packaged_version` |

## Proposed changes (ordered, validatable)

1. Build hook writes the resolved version into the wheel's bundled VERSION (E-02).
2. Installed package prefers distribution metadata (E-03).
3. `doctor.stale-build` signal and the conditional `--version` note (E-04).
4. Tests including a slow end-to-end wheel build (E-05).

## Deferred / out of scope (with reason)

- A STALENESS CHECK ON EVERY `aw` INVOCATION. Every command would pay a `git` subprocess against a directory that may be on a slow mount; `aw doctor` and `aw --version` are where a user asks this question.
  - Carrier: none (deliberately not done)

## Scope check

- Over-scope: none.
- Under-scope: the committed `.aw/system/VERSION` remains a manually baked file for source and sdist use; this plan makes the WHEEL independent of whether it was refreshed.

## Required tests / validation

- `tests/test_installed_version_reporting.py` (E-05), including the mutation proof.
- Bare `python3 -m pytest` with the actual summary line pasted, compared with a pre-edit baseline in the same worktree.
- The slow test run explicitly with `python3 -m pytest -o addopts="" -m slow tests/test_installed_version_reporting.py` and its output pasted.

## Spec / documentation sync

- Update the `agent_workflows/__init__.py` module docstring ("an installed wheel reads its baked VERSION") to state that an installed wheel reports its distribution version.
- Update the `hatch_build.py` docstring to state that the build hook bakes the version, replacing the reliance on `make version-file`.

## Open questions

### OQ-01: Should the wheel version and the committed VERSION file be forced equal in CI instead?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: no. A dev build's version changes with every commit (`.devN+g<sha>`), so a committed file can never equal it; only the build can know the value. Baking at build time removes the class of skew entirely.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `pip show` version, `aw --version` output and bundled VERSION content, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: after rebuilding, PASTE the bundled VERSION content and `pip show` version (equal), and `git diff --stat -- .aw/system/VERSION` showing no change.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE `aw --version` from outside the checkout with `AW_NO_REEXEC=1`, equal to the `pip show` version, and `python3 -c "import agent_workflows; print(agent_workflows.__version__)"` run inside the checkout showing the git-described version.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE `aw doctor` output from a venv whose local build is at least one commit behind its source (make one throwaway commit in a temp clone, build from it, then add a commit) showing the `doctor.stale-build` warning with both shas and the rebuild command; and PASTE `aw doctor` from a current build showing no such line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file (fast tests) and of the slow test, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit whz0oi -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed whz0oi`.
