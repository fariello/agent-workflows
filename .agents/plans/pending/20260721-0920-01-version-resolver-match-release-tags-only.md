# IPD: version resolver considers only semver release tags (`git describe --match`)

- Date: 2026-07-21
- Concern: bug (release-blocking) - git-tag-driven version resolution
- Scope: `agent_workflows/versioning.py` `_git_describe` + a regression test. Corrective fix for a latent resolver bug exposed by the `v1.2.0-recreated` tag. Does NOT touch any git tag or release.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after `/whatnext` execution surfaced (STOP-and-report) a pre-existing full-suite failure + 6 wheel-build skips caused by the `v1.2.0-recreated` tag. Root-caused to `_git_describe` matching a non-semver tag.

## Goal

Make the version resolver derive the version only from real semver RELEASE tags (`vX.Y.Z`), so a stray non-release tag near HEAD cannot produce a garbage version or block the wheel build.

Concrete failure: the `v1.2.0-recreated` tag (created to work around the permanently-blocked `v1.2.0`, DECISIONS D92 history rewrite) is the nearest tag to HEAD. `git describe --tags --long` returns `v1.2.0-recreated-109-g<sha>`; `parse_describe` splits `tag="v1.2.0-recreated"`, `_normalize_tag` strips the `v` to `1.2.0-recreated`, and `_next_patch` (finding the last purely-numeric part) bumps the `2` -> the INVALID version `1.3.0-recreated.dev109+...`. That string is not PEP 440 valid, so `python -m build` fails (6 wheel tests skip with "wheel build unavailable") and `tests/test_cli.py::ListStatusTests::test_list_shows_states` fails (the state label cannot classify it). This is a release blocker: no valid wheel can be built right now.

This is NOT a `v1.2.0-recreated`-specific band-aid: it is a permanent hardening. The resolver's contract is "derive the version from the last RELEASE tag," and this project's release tags are `vX.Y.Z` (D44). Any tag that is not a release version (a recreated marker, a personal bookmark, a CI/nightly tag, an rc typo) should not be a version source. Filtering `git describe` to semver tags encodes that intent, is transparent to future clean tags (a later `v1.3.0` matches and is used normally), is NEVER removed when a conformant tag is added, and closes the whole latent class, not just this instance.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (P8 single source of truth - one resolver drives wheel version, `aw --version`, and the baked VERSION). Zero runtime deps (stdlib only): the fix stays stdlib, no `packaging`/`setuptools-scm`.
- Versioning design: `agent_workflows/versioning.py` (D44) is the sole resolver; `hatch_build.py:41` calls `resolve_version` for the wheel version; downstream copies read the baked `.agents/workflows/VERSION`.
- Tag facts: release tags are `v1.0.0`, `v1.1.0` (clean) and the non-conforming `v1.2.0-recreated` (the banned `v1.2.0` cannot be re-created; the recreated tag backs the GitHub Release). `git describe --tags` currently returns `v1.2.0-recreated-109-g...`.
- Plans lifecycle: `.agents/plans/pending/` + `YYYYMMDD-HHMM-NN-<slug>.md`; IPD born `to-review`. No em/en dashes.
- Test convention: `tests/test_versioning.py` feeds `parse_describe` the real describe shapes and stubs `_git_describe` (lines 97-112) for the resolve path.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| V1 | HIGH | Low | maintainer / operator | release-blocking bug | `_git_describe` runs `git describe --tags --always --dirty --long` with NO tag filter, so a non-semver tag (`v1.2.0-recreated`) nearest HEAD becomes the version base and yields the invalid `1.3.0-recreated.dev...`; `python -m build` fails and a CLI test fails. | `agent_workflows/versioning.py:164-179`; live `git describe` = `v1.2.0-recreated-109-g...`; `python -m agent_workflows --version` = `1.3.0-recreated.dev...` |
| V2 | MEDIUM | Low | maintainer | latent class | Even absent this incident, ANY non-`vX.Y.Z` tag near HEAD (bookmark, CI tag, rc typo) would derail the resolver the same way. There is no guard/test for a malformed nearest tag. | `versioning.py` `_git_describe` (no `--match`); `parse_describe`/`_next_patch` bump behavior |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | V1,V2 | In `_git_describe`, add `--match "v[0-9]*.[0-9]*.[0-9]*"` to the `git describe` args so ONLY semver release tags are considered. This makes `git describe` skip `v1.2.0-recreated` and match the nearest clean tag (`v1.1.0`), yielding a valid `1.1.1.devN+g<sha>` (correct tag-driven-dev semantics; becomes `1.3.0` the moment `v1.3.0` is tagged). Keep `--tags --always --dirty --long`. Note: with `--match`, if NO semver tag is an ancestor, `--always` still degrades to a bare sha (`0.0.0+gsha`), the existing safe fallback. | `agent_workflows/versioning.py` | Low | `python -m agent_workflows --version` now returns a PEP 440-valid `1.1.1.dev...`; `python -m build --wheel` succeeds; the previously-skipped wheel tests run; `test_list_shows_states` passes |
| 2 | V2 | Add a regression test: stub/verify `_git_describe` passes the `--match` semver glob (assert the argv includes it), AND a `parse_describe`-level test that the resolver never emits a `-recreated`-style base (feed a describe whose tag would be non-semver and confirm the guard path). Mirror the existing `test_versioning.py` stubbing style. | `tests/test_versioning.py` | Low | new test FAILS without the `--match` arg and PASSES with it |
| 3 | V1 | Update the `versioning.py` module docstring's `git describe` example line to include the `--match` filter and one sentence on why (only semver release tags drive the version). | `agent_workflows/versioning.py` | Low | docstring matches the actual command; no em/en dashes |
| 4 | V1 | Add a CHANGELOG 1.3.0 "Fixed" bullet: the version resolver now considers only semver release tags, so a stray non-release tag cannot break version derivation or the wheel build. | `CHANGELOG.md` | Low | bullet present; no em/en dashes |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | Low | n/a | Renaming/removing the `v1.2.0-recreated` git tag. Not needed once `--match` ignores it; renaming a tag that backs a pushed GitHub Release is fiddly (delete+recreate+repoint) and adds no robustness beyond the allowlist. | Optional cosmetic cleanup later; not required. |
| n/a | Low | n/a | A DECISIONS entry. The fix applies the existing D44 tag-driven-version design; the `--match` filter is an implementation hardening, not a new decision. | Record in CHANGELOG + this IPD; add a decision only if review judges it warranted. |

## Scope check

- Over-scope: none. Only the resolver + its test + docstring/CHANGELOG. No tag/release/PyPI action.
- Under-scope: confirm `--match` uses a glob that matches all real release tags (`v[0-9]*.[0-9]*.[0-9]*` matches `v1.0.0`..`v1.2.0` and future `v1.3.0`; it also matches rc tags like `v1.2.0-rc.1`? NO - `-rc.1` follows the third numeric group, and the glob `v[0-9]*.[0-9]*.[0-9]*` matches a prefix then anything, so `v1.2.0-rc.1` DOES match since `[0-9]*` after the last dot matches `0-rc.1`... verify at execution and adjust the glob if rc tags must be included, since `parse_describe` already handles rc). Validate rc-tag matching explicitly in Step 2.

## Required tests / validation

- Step 2 regression test (as above), plus:
- `python -m agent_workflows --version` returns a valid `1.1.1.dev...` (PEP 440).
- `python -m build --wheel` succeeds (manually, and the previously-skipped `tests/test_packaging.py` wheel tests now run, not skip).
- `tests/test_cli.py::ListStatusTests::test_list_shows_states` passes.
- Full suite `python -m pytest -q` GREEN with the wheel tests un-skipped; paste ACTUAL output (current: 1 failed, 281 passed, 7 skipped; target: 0 failed, more passed, fewer skips).
- Confirm rc-tag handling is not broken by the glob (a `v1.2.0-rc.1` describe still resolves to `1.2.0rc1`).

## Spec / documentation sync

- `versioning.py` docstring (Step 3); `CHANGELOG.md` 1.3.0 Fixed bullet (Step 4). No API change.

## Open questions

- OQ1 (glob for rc tags): should `--match` include rc tags? `parse_describe` supports them (`v1.2.0-rc.1` -> `1.2.0rc1`), so the glob should NOT exclude a legitimately-tagged rc. Proposed glob `v[0-9]*.[0-9]*.[0-9]*` appears to match `v1.2.0-rc.1` too (trailing `[0-9]*` is a prefix match). Verify empirically at execution; if rc tags are excluded, widen the glob (e.g. `--match 'v[0-9]*'`) or add a second `--match`. Lean: verify, prefer the narrowest glob that still admits `vX.Y.Z` and `vX.Y.Z-rc.N`.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. NOTE: there is uncommitted `/whatnext` work in the tree (IPD 20260717-2317-01, Steps 1-7 done); this corrective fix is committed FIRST and separately, then the whatnext work is finalized against the now-green suite.

Recommended next steps:
1. Review this IPD (optionally `/plan-review`). Resolve OQ1 (rc glob) at review or execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, run validation, sync CHANGELOG; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
