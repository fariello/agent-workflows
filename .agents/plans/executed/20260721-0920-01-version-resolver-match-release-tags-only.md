# IPD: version resolver considers only semver release tags (`git describe --match`)

- Date: 2026-07-21
- Concern: bug (release-blocking) - git-tag-driven version resolution
- Scope: `agent_workflows/versioning.py` `_git_describe` + a regression test. Corrective fix for a latent resolver bug exposed by the `v1.2.0-recreated` tag. Does NOT touch any git tag or release.
- Status: executed
- Approval: approved by the human (repo maintainer) 2026-07-21
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after `/whatnext` execution surfaced (STOP-and-report) a pre-existing full-suite failure + 6 wheel-build skips caused by the `v1.2.0-recreated` tag. Root-caused to `_git_describe` matching a non-semver tag.
- 2026-07-21 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Verified V1/V2 against source, then EMPIRICALLY tested the proposed glob and found the MECHANISM WRONG (V3): `--match 'v[0-9]*.[0-9]*.[0-9]*'` does not exclude `v1.2.0-recreated` (fnmatch matches `0-recreated`), and the tighter `...[0-9]` rejects multi-digit patches (`v1.10.20`). Corrected the mechanism to `--match 'v[0-9]*' --exclude '*-recreated'` (empirically verified) and added a second-layer parser guard (V4) so a non-semver tag degrades to `0.0.0+gsha` instead of a `-recreated` version. Rewrote Steps 1-5 and the tests accordingly. OQ1 resolved from evidence; no open questions remain. Status -> reviewed.

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
| V3 | HIGH | Low | maintainer | plan-review PR-001/PR-002 (mechanism was wrong) | The originally-proposed glob `v[0-9]*.[0-9]*.[0-9]*` does NOT exclude `v1.2.0-recreated` (fnmatch `[0-9]*` after the last dot matches `0-recreated`); verified: `git describe --match 'v[0-9]*.[0-9]*.[0-9]*'` on a repo whose only tag is `v1.2.0-recreated` still returns it. The tighter `v[0-9]*.[0-9]*.[0-9]` rejects `-recreated` and admits rc but FAILS multi-digit patches (`v1.10.20` -> no match) - a latent regression. A single fnmatch glob cannot express "digits, optionally `-rc.N`". | empirical `git describe --match` + `python fnmatch`: `v1.2.0-recreated`=match under the loose glob; `v1.10.20`=NO match under the strict glob |
| V4 | MEDIUM | Low | maintainer | plan-review PR-003 (defense in depth) | Filtering `git describe` alone still leaves `parse_describe`/`_next_patch` able to emit a garbage version if any non-semver tag reaches it (`_next_patch` bumps the last numeric part, turning `1.2.0-recreated` into `1.3.0-recreated`). A second layer that treats a non-`X.Y.Z[rcN]` core as "no usable tag" makes a slip-through degrade safely. | `versioning.py:76-91` `_next_patch`; `:61-73` `_normalize_tag` |

## Proposed changes (ordered, validatable)

Mechanism CORRECTED at review (V3/V4): a single fnmatch glob cannot express the shape, so use a broad match + targeted exclude at `git describe` AND a second-layer guard in the parser.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | V1,V2,V3 | In `_git_describe`, filter the `git describe` candidate tags with `--match "v[0-9]*" --exclude "*-recreated"` (keep `--tags --always --dirty --long`). EMPIRICALLY VERIFIED: `--match 'v[0-9]*'` admits `v1.2.0`, `v1.10.20` (multi-digit), and `v1.2.0-rc.1`; `--exclude '*-recreated'` drops `v1.2.0-recreated`, so describe falls back to the nearest clean tag (`v1.1.0`) -> valid `1.1.1.devN+g<sha>` (becomes `1.3.0` when `v1.3.0` is tagged). `--exclude '*-recreated'` is a shape blocklist (not the literal tag) so it also catches any future `-recreated` marker. If no admitted tag is an ancestor, `--always` degrades to a bare sha (`0.0.0+gsha`), the existing safe fallback. | `agent_workflows/versioning.py` | Low | on THIS repo `python -m agent_workflows --version` returns PEP 440-valid `1.1.1.dev...`; `python -m build --wheel` succeeds; previously-skipped wheel tests run; `test_list_shows_states` passes |
| 2 | V4 | Second-layer guard in the parser so a non-semver tag that ever reaches `parse_describe` degrades safely instead of emitting a `-recreated`-style version: make `_normalize_tag`/`parse_describe` recognize a NON-conforming core (not `X.Y.Z` or `X.Y.Zrc N`) and treat it as "no usable tag" -> fall through to the `0.0.0+g<sha>` (no-tag) branch rather than bumping a non-numeric core in `_next_patch`. | `agent_workflows/versioning.py` | Low | `parse_describe("v1.2.0-recreated-3-gabc1234")` returns `0.0.0+gabc1234` (NOT `1.3.0-recreated.dev3+...`) |
| 3 | V1,V2,V3,V4 | Regression tests: (a) a `parse_describe` test asserting a non-semver tag (`v1.2.0-recreated-3-gABC`) yields `0.0.0+gABC`, not a `-recreated` base; (b) a `_git_describe` test asserting the argv includes `--match v[0-9]*` and `--exclude *-recreated`; (c) confirm rc + multi-digit-patch shapes still resolve (`v1.2.0-rc.1-...` -> `1.2.0rc1...`, `v1.10.20-...` handled). Mirror `test_versioning.py` stubbing. | `tests/test_versioning.py` | Low | tests FAIL on the old code and PASS after Steps 1-2 |
| 4 | V1 | Update the `versioning.py` module docstring `git describe` example line to include the `--match`/`--exclude` filter and one sentence on why (only semver release tags drive the version; non-conforming tags are ignored and degrade safely). | `agent_workflows/versioning.py` | Low | docstring matches the actual command; no em/en dashes |
| 5 | V1 | Add a CHANGELOG 1.3.0 "Fixed" bullet: the version resolver now considers only semver release tags (and safely ignores non-release tags), so a stray tag cannot break version derivation or the wheel build. | `CHANGELOG.md` | Low | bullet present; no em/en dashes |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | Low | n/a | Renaming/removing the `v1.2.0-recreated` git tag. Not needed once `--match` ignores it; renaming a tag that backs a pushed GitHub Release is fiddly (delete+recreate+repoint) and adds no robustness beyond the allowlist. | Optional cosmetic cleanup later; not required. |
| n/a | Low | n/a | A DECISIONS entry. The fix applies the existing D44 tag-driven-version design; the `--match` filter is an implementation hardening, not a new decision. | Record in CHANGELOG + this IPD; add a decision only if review judges it warranted. |

## Scope check

- Over-scope: none. Only the resolver + its test + docstring/CHANGELOG. No tag/release/PyPI action. The second-layer parser guard (Step 2) is in-scope defense-in-depth, not gold-plating: it is what makes the fix robust to non-`-recreated` junk tags too.
- Under-scope: RESOLVED at review - the tag-filter mechanism was corrected (V3): `--match 'v[0-9]*' --exclude '*-recreated'` (empirically verified to admit `v1.2.0`, `v1.10.20`, `v1.2.0-rc.1` and reject `v1.2.0-recreated`) plus the Step 2 parser guard, instead of the unsound single glob.

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

- OQ1 (glob for rc tags): RESOLVED empirically at review. A single fnmatch glob cannot express "digits, optionally `-rc.N`": the loose `v[0-9]*.[0-9]*.[0-9]*` wrongly matches `v1.2.0-recreated`, and the strict `v[0-9]*.[0-9]*.[0-9]` wrongly rejects multi-digit patches (`v1.10.20`). Chosen mechanism (verified with `git describe` + Python `fnmatch`): `--match 'v[0-9]*' --exclude '*-recreated'` (admits `vX.Y.Z`, `vX.Y.ZZ`, `vX.Y.Z-rc.N`; rejects `-recreated`), backed by the Step 2 parser guard for anything else that slips through. No open questions remain.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. NOTE: there is uncommitted `/whatnext` work in the tree (IPD 20260717-2317-01, Steps 1-7 done); this corrective fix is committed FIRST and separately, then the whatnext work is finalized against the now-green suite.

Recommended next steps:
1. Review this IPD (optionally `/plan-review`). Resolve OQ1 (rc glob) at review or execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, run validation, sync CHANGELOG; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.

## Workflow history (execution)

- 2026-07-21 human approval (repo maintainer): "Approved. Go." Status -> approved.
- 2026-07-21 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Steps 1-5 done in `agent_workflows/versioning.py` (`_git_describe --match 'v[0-9]*' --exclude '*-recreated'`; parser guard `_is_release_tag` so a non-release tag degrades to `0.0.0+g<sha>`; docstring) + `tests/test_versioning.py` (NonReleaseTagGuardTests) + CHANGELOG. Validation (actual): `git describe` now = `v1.1.0-230-g...` (skips `v1.2.0-recreated`); `python -m agent_workflows --version` = `1.1.1.dev230+g2734544.d20260721` (PEP 440 valid); `python -m build --wheel` SUCCEEDS; `python -m pytest -q` = 293 passed, 1 skipped (was 1 failed, 281 passed, 7 skipped: the CLI test now passes and the 6 wheel tests un-skipped). Committed path-scoped; git mv to executed/.
