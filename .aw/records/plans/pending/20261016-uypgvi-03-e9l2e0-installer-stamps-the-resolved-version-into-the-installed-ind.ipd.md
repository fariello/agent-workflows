# IPD: Installer stamps the resolved version into the installed index.md so artifact_manifest agrees on a dev-checkout install

- Date: 2026-10-16
- Kind: child
- Concern: An install from a development checkout writes `.aw/system/VERSION` from the resolver (`1.3.0rc2.dev...`, per i8u6hh) but copies `.aw/system/workflows/index.md` verbatim, so its `<!-- WORKFLOWS-VERSION: ... -->` and `Version: \`...\`` stamps keep the last baked value (`1.2.1`). `release_readiness.gate_artifact_manifest` then FAILS the managed repo with "version stamp mismatch", a false NO-GO, and `/list-workflows` reads a version that misdescribes the installed framework.
- Scope: IN: (1) make the installer's per-member byte producer `engine._member_source_bytes` rewrite the two version stamps in the installed `index.md` to the same `read_version(source_root)` value it already writes into VERSION, on both the install path (`engine.install_all`) and the preview path (`engine.show_install_diffs`), which share that producer; (2) behavioral regression tests in `tests/test_installer.py` (git-tagged diverging source, non-git source, idempotent re-install, and the `gate_artifact_manifest` outcome on the installed target); (3) a `CHANGELOG.md` entry. OUT: `agent_workflows/release_readiness.py` (the gate's stamp/VERSION equality check is correct and is kept; it detected a real installer inconsistency); re-baking this repository's own `.aw/system/VERSION` or `index.md` (`make version-file`, a release-time act under RELEASING.md); `versioning.status()` classifications; the `Makefile` `version-file` target (already syncs both stamps).
- Scope-Paths: agent_workflows/engine.py, tests/test_installer.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: 7rs77x
- Set: uypgvi
- Order: 3
- Highest E allocated: 05
- Author: opencode
- Id: e9l2e0
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog 7rs77x at HEAD dcb5a064d; root cause located in `engine._member_source_bytes`; decided installer-side reconciliation (OQ-01).

## Goal

Make every installed copy self-consistent: the version stamps in the installed `index.md` must equal the installed `.aw/system/VERSION`, because both are now derived from one resolver call. This removes the false `artifact_manifest` NO-GO in managed repos installed from a development checkout while keeping the gate's mismatch check meaningful.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [ ] E-01 Reproduce the mismatch at the executing HEAD and record the baseline.
  - Depends on: none
  - Expected outcome: one pasted transcript proving: (a) a fresh managed install into a gitignored scratch dir (`mkdir -p .aw/state/scratch-e9l2e0/mr && git -C .aw/state/scratch-e9l2e0/mr init -q`, then `python3 -m agent_workflows install .aw/state/scratch-e9l2e0/mr --yes --no-interactive --preset private-target --delivery-mode tracked --records-backend repository`) leaves `.aw/system/VERSION` holding the resolved dev string and `.aw/system/workflows/index.md` holding `WORKFLOWS-VERSION: 1.2.1` (print both with `cat` and `sed -n 3,4p`); (b) `python3 -c "from pathlib import Path; from agent_workflows import release_readiness as r; g=r.gate_artifact_manifest(repo_root=Path('.aw/state/scratch-e9l2e0/mr')); print(g.passed, g.evidence['problems'])"` prints `False` with the "version stamp mismatch" problem; (c) `python3 -c "from agent_workflows import engine; from pathlib import Path; print(engine.read_version(engine.resolve_source_root(Path('.'))))"` and `cat .aw/system/VERSION` in this checkout, confirming the source's baked value differs from the resolver; (d) `git grep -n "WORKFLOWS-VERSION" -- agent_workflows` shows only `release_readiness.py` reads the stamp in code (no other producer to keep in step); (e) the pre-edit bare `python3 -m pytest` summary line and the sorted names of any failing tests (the baseline E-05 compares against by name). If (a) shows the stamps already agree, stop and reconcile rather than duplicating work.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-02 Write the regression tests FIRST in `tests/test_installer.py` and show them RED against the unmodified `agent_workflows/engine.py`.
  - Depends on: E-01
  - Expected outcome: a new `unittest.TestCase` class (for example `ResolvedIndexStampTests`) modelled on `ResolvedVersionStampTests` (git-tagged source whose baked VERSION is `1.2.1` and whose tag `v7.3.0` resolves to `7.3.0`; its `index.md` additionally carries `<!-- WORKFLOWS-VERSION: 1.2.1 -->` and `Version: \`1.2.1\` (source of truth: ...)` lines above the manifest markers, and its manifest row names the body as `.aw/system/workflows/plan-review/plan-review.md`, NOT the `.agents/workflows/...` path `ResolvedVersionStampTests.MANIFEST_ROW` uses: `gate_artifact_manifest` resolves body paths against the aw-layout target, so the legacy path adds a "missing body file" problem and case (2) could never pass, measured at review), asserting observable outcomes only (no `inspect`, `ast`, or source regex): (1) after `INS.install_into_repo(target, resolved_root, yes=True, no_color=True)` the target's installed `index.md` carries `WORKFLOWS-VERSION: 7.3.0` and `Version: \`7.3.0\``, equal to the installed `.aw/system/VERSION`, and every other byte of `index.md` equals the source file (compare the text with both stamp lines substituted back); (2) `release_readiness.gate_artifact_manifest(repo_root=target)` returns `passed is True` with no "version stamp" problem (falsifiability: on the unmodified engine it fails with "version stamp mismatch"); (3) a second install reports no `index.md` member as written again and leaves its bytes unchanged (idempotence, mirroring `test_a_second_install_is_idempotent`); (4) a NON-git source (no `init_repo`, `GIT_CEILING_DIRECTORIES` set via `mock.patch.dict(os.environ, ...)` to the temp parent) installs `index.md` byte-identical to the source, because the resolver's answer there IS the baked file; (5) an `index.md` with NO stamp lines installs byte-identical (the rewrite is a no-op when nothing matches). Cases (3)-(5) are regression guards that also pass on the unmodified engine (a verbatim copy is already idempotent and byte-identical); only (1) and (2) are expected RED. RED proof: run `python3 -m pytest -o addopts="" -q tests/test_installer.py -k ResolvedIndexStamp` before E-03 and paste the failing output.
  - Execution state: pending

- [ ] E-03 Extend `engine._member_source_bytes` so the installed `index.md` carries the resolved version in both stamps.
  - Depends on: E-02
  - Expected outcome: when `source_relative == "index.md"`, the producer decodes the source bytes as UTF-8, substitutes the first match of the comment stamp and the first match of the `Version:` line with `read_version(source_root)` (the same resolved value the VERSION branch writes, computed once per call), writing the canonical forms `<!-- WORKFLOWS-VERSION: <v> -->` and `Version: \`<v>\`` that the `Makefile` `version-file` target writes. MATCH with the whitespace-tolerant patterns the consumer reads, `release_readiness.gate_artifact_manifest`'s `<!--\s*WORKFLOWS-VERSION:\s*([^\s>]+)\s*-->` and `(?m)^Version:\s*\`([^\`]+)\``, not the Makefile's stricter single-space patterns, so every stamp the gate can read is one the installer rewrites (review D-1); preserves every other byte including line endings, and returns the original bytes unchanged when neither pattern matches or the resolved value is `unknown` (so an unresolvable source never stamps `unknown` into a manifest that previously named a version). The docstring explains that `index.md` is the second derived member and why. `engine.show_install_diffs` needs no edit because it already calls the same producer; confirm by reading it. Every other member stays a verbatim copy.
  - Execution state: pending

- [ ] E-04 Record the fix in `CHANGELOG.md`.
  - Depends on: E-03
  - Expected outcome: one `Fixed:` bullet in the topmost section, `## 2.0.0 (pending)` (where the other current `Fixed:` bullets, including the `artifact_manifest` one, live; NOT the older `## 1.3.0 (pending)` section), stating that an install from a development checkout now stamps the installed `index.md` with the same resolved version as `.aw/system/VERSION`, so `aw releases readiness` no longer reports a false `artifact_manifest` version-stamp mismatch in managed repos; no em or en dashes in the added text.
  - Execution state: pending

### Task group 3: validation

- [ ] E-05 Run targeted and full validation, and re-observe the managed install.
  - Depends on: E-03, E-04
  - Expected outcome: (1) `python3 -m pytest -o addopts="" -q tests/test_installer.py tests/test_release_readiness_producers.py tests/test_release_readiness.py` passes with 0 failures; (2) re-running the E-01(a) install into a FRESH scratch dir (`.aw/state/scratch-e9l2e0/mr2`) shows the installed `index.md` stamps equal to the installed VERSION and the E-01(b) probe prints `True []` (or, if a different problem remains, names it as measured and not hidden); (3) a `\u2014`/`\u2013` scan of the `CHANGELOG.md` addition finds 0; (4) `python3 -m agent_workflows sanitize --agent` reports `"outcome": "clean"`; (5) bare `python3 -m pytest` passes with zero new failures compared by name against the E-01(e) baseline; (6) `git status --porcelain -- .aw/system/VERSION .aw/system/workflows/index.md` is empty, proving this repository's own baked files were not touched.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- VERSION is a DERIVED artifact; the installer writes the RESOLVED value, not the baked bytes (`engine._member_source_bytes` docstring, plan `i8u6hh` E-02 and OQ-01: the `.devN+g<sha>` string is written unconditionally).
- `make version-file` already treats the `index.md` stamps as derived from the same value: it rewrites `<!-- WORKFLOWS-VERSION: ... -->` and `Version: \`...\`` in lockstep with VERSION (Makefile `version-file` target; CHANGELOG "made `make version-file` sync the `index.md` version stamp"; DECISIONS REL-007). The installer was never brought into the same lockstep.
- Re-baking this repository's VERSION is a release-time act gated on a human GO (RELEASING.md "Bake-then-tag"; i8u6hh deferred section), so this plan must not do it.
- Install and preview share one byte producer so a preview never advertises bytes the install would not write (`engine.show_install_diffs` comment "The SAME byte producer the install path uses").
- Synthetic git fixtures use `tests.support.init_repo`/`git`; tests assert observable behavior only (AGENTS.md, GUIDING_PRINCIPLES P16).
- User-facing prose (`CHANGELOG.md`) carries no em or en dashes (AGENTS.md).
- The full suite runs bare as `python3 -m pytest`; narrowed runs clear defaults with `-o addopts=""` (AGENTS.md repo-local contract).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The symptom is a false `artifact_manifest` NO-GO in a managed repo installed from a dev checkout. | Backlog `7rs77x`, measured at `cb349046d` by plan `4bw2u5` OQ-02: installed VERSION `1.3.0rc2.dev10960+gcb349046d`, installed `index.md` `WORKFLOWS-VERSION 1.2.1`, gate problem "version stamp mismatch: index.md has 1.2.1 but .aw/system/VERSION has ...". |
| F-02 | ROOT CAUSE: the installer derives VERSION but byte-copies `index.md`. | `engine._member_source_bytes` returns `source_path.read_bytes()` for every member except `VERSION_FILE`, for which it returns `read_version(source_root)`. `index.md` carries two stamps of that same value and is copied verbatim. |
| F-03 | The gate is correct and should not be relaxed. | `release_readiness.gate_artifact_manifest` compares each index.md stamp with `.aw/system/VERSION`; the two disagreeing in an installed tree is a genuine inconsistency, and `/list-workflows` reads the `index.md` stamp as "the version" (`.aw/system/workflows/list-workflows/list-workflows.md`, "The version: the `<!-- WORKFLOWS-VERSION: ... -->` header line"). |
| F-04 | Only `index.md` carries the stamp in shipped content consumed by code. | `git grep -n "WORKFLOWS-VERSION" -- agent_workflows` at `dcb5a064d` matches only `agent_workflows/release_readiness.py`; the shipped stamp lives only in `.aw/system/workflows/index.md`. |
| F-05 | A correctly baked release install does NOT reproduce, so `followup` (not `bug`) stands. | A wheel or non-git copy resolves to the baked file, so VERSION and the stamp agree. A bake-then-tag tag tree has VERSION equal to its tag (RELEASING.md). Counterexample worth noting: tag `v1.3.0-rc.1` was NOT bake-then-tagged (`git show v1.3.0-rc.1:.agents/workflows/VERSION` is `1.2.1` while the resolver reports `1.3.0rc1`), so an install from that tag checkout would also mismatch. The fix covers both cases because the stamp now follows the resolver. |
| F-06 | No test covers the installed `index.md` stamp. | `git grep -n "WORKFLOWS-VERSION" -- tests` matches only `tests/test_release_readiness_producers.py` fixtures; `ResolvedVersionStampTests` in `tests/test_installer.py` asserts only VERSION and the manifest `installed_version`. |
| F-07 | The fix is sufficient for the gate, measured at review. | At `b551549b9`: a managed install gave VERSION `1.3.0rc2.dev11020+gb551549b9`, `index.md` stamps `1.2.1`, gate `False ['version stamp mismatch: ...']`. On a synthetic tagged source (`v7.3.0`, baked `1.2.1`, aw-layout body row) the unpatched gate printed `False ['version stamp mismatch: index.md has 1.2.1 but .aw/system/VERSION has 7.3.0']`; with `_member_source_bytes` patched to rewrite both stamps it printed `True []`, and a second install reported no `index.md` line written. With the legacy `.agents/workflows/...` body row the gate also reported `missing body file`. |

## Proposed changes (ordered, validatable)

1. Reproduce and baseline (E-01).
2. Add RED behavioral tests for the installed `index.md` stamps and the gate outcome (E-02).
3. Rewrite the two stamps in `engine._member_source_bytes` from the same resolved value used for VERSION (E-03).
4. CHANGELOG entry (E-04).
5. Targeted, end-to-end, and full-suite validation (E-05).

## Deferred / out of scope (with reason)

- Relaxing or changing `release_readiness.gate_artifact_manifest`: rejected (OQ-01); the check is correct and its failure was a true signal of installer inconsistency.
  - Carrier-Declined: rejected design alternative, not outstanding work; nothing remains to do.
- Re-baking this repository's own `.aw/system/VERSION` and `index.md` stamps: a release-time act under RELEASING.md gated on a human GO (same deferral as `i8u6hh`).
  - Carrier-Declined: owned by the standing RELEASING.md bake-then-tag procedure (`make version-file`), performed at every release; not a defect needing its own record.
- Reclassifying backlog `7rs77x` to `bug`: the item says to classify as bug only if it reproduces on a released install; F-05 shows a correctly baked release does not, and this plan must not modify the item's requirements.
  - Carrier-Declined: the classification condition is not met (F-05, OQ-02); nothing remains to do.

## Scope check

- Over-scope: none. One producer change, its tests, and one changelog line.
- Under-scope: none for the backlog item. It asks to decide whether the gate or the installer reconciles (decided: installer, OQ-01) and to confirm release-install behavior (F-05, by reasoning from the resolver contract; E-02 case (4) exercises the non-git, baked-file path a wheel install takes).

## Required tests / validation

- New `ResolvedIndexStampTests` in `tests/test_installer.py` (E-02), RED before E-03 and GREEN after.
- Existing `ResolvedVersionStampTests` and the release-readiness producer tests stay green (E-05(1)).
- End-to-end managed install plus `gate_artifact_manifest` probe (E-05(2)), dash scan, `aw sanitize --agent`, and bare `python3 -m pytest` compared by name with the baseline (E-05).

## Spec / documentation sync

- `CHANGELOG.md` records the fix (E-04).
- No spec describes the installed `index.md` stamp: `git grep -l "WORKFLOWS-VERSION" -- .aw/records/specs/` matched nothing at `dcb5a064d`, so no `.spec.md` is touched or declared.
- `.aw/system/workflows/list-workflows/list-workflows.md` already tells agents to read the stamp; after this fix the stamp it reads is correct, so it needs no edit.

## Open questions

### OQ-01: Should the gate or the installer reconcile the stamp?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: the installer. `make version-file` already defines the `index.md` stamps as derived from the same value as VERSION (Makefile `version-file`; DECISIONS REL-007), and `i8u6hh` made the installer derive VERSION from the resolver, leaving `index.md` as the one place that rule was not applied (F-02). Relaxing the gate would hide a real inconsistency that `/list-workflows` surfaces to users (F-03). Reversible by reverting the producer change.

### OQ-02: Does a release install reproduce the mismatch?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED by the resolver contract (F-05): a wheel or non-git install reads the baked file for both, and a bake-then-tag tree agrees by construction, so a correctly made release does not reproduce, and the inherited `followup` classification stands. A tag that skipped bake-then-tag (for example `v1.3.0-rc.1`) would reproduce; the fix covers it because the stamp now follows the resolver.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha and the full E-01 transcript (code paths: `aw install` via `engine.install_into_repo`, then `release_readiness.gate_artifact_manifest`): (a) the scratch install's VERSION and `index.md` lines 3-4; (b) the gate probe output showing `False` and the "version stamp mismatch" problem; (c) the resolver value and this checkout's baked VERSION; (d) the `git grep` output; (e) the pre-edit bare `python3 -m pytest` summary line and sorted failing-test names.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the pre-E-03 RED output of `python3 -m pytest -o addopts="" -q tests/test_installer.py -k ResolvedIndexStamp` (cases (1) and (2) failing against the unmodified engine, (2) with the "version stamp mismatch" problem and no "missing body file" problem; (3), (4) and (5) passing, which is expected because a verbatim copy is already idempotent and byte-identical) and `git diff --stat` showing only `tests/test_installer.py` changed at that point.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` hunk for `engine._member_source_bytes`, and the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_installer.py -k "ResolvedIndexStamp or ResolvedVersionStamp"` showing every case passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `git diff -- CHANGELOG.md` (the hunk header must place the bullet inside `## 2.0.0 (pending)`) and the dash-scan output over the added lines showing 0 matches.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste (1) the targeted pytest summary line with 0 failures; (2) from the fresh `mr2` scratch install (code path: `engine.install_into_repo`, then `release_readiness.gate_artifact_manifest`), the installed VERSION, the `index.md` stamp lines, and the gate probe output; (3) the dash-scan result; (4) the `aw sanitize --agent` record; (5) the bare `python3 -m pytest` summary line and the by-name comparison against the E-01(e) baseline; (6) the empty `git status --porcelain` output for this repo's baked files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit e9l2e0 -- <paths>` (never `git add -A`), never push, and paste actual runner output for every test claim. The E-01/E-05 scratch installs live under the gitignored `.aw/state/scratch-e9l2e0/` and are never committed. Do NOT run `make version-file` or otherwise re-bake this repository's VERSION or `index.md`.

SCOPE FENCE. `agent_workflows/release_readiness.py` is owned by `4bw2u5` in this Set and stays untouched here; this plan changes only the installer. An out-of-scope edit that proves necessary is made and justified with `--scope-reason` at finalize.

RELEASE GATE. Backlog `7rs77x` carries no `- Blocks-Release:`, so none is inherited.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all five `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
