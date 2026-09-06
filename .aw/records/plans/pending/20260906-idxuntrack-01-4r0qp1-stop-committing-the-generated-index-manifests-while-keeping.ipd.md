# IPD: Stop committing the generated index manifests while keeping them refreshed

- Date: 2026-09-06
- Kind: child
- Concern: Four code sites put the generated `INDEX.json`/`INDEX.md` paths into a COMMIT path-set. Once child 02 gitignores those files, every one of them either silently no-ops or hard-fails, and the worst case is a transaction with rollback. Measured at HEAD `7f80180e`: `ipd_lifecycle.py:2340-2343` places both plans-manifest paths into `owned_paths` for the finalize lifecycle commit; `status_set.py:936-937,971-972` collects them for the `aw set` auto-refresh self-commit; `status_set.py:1122-1138` (`_index_paths_for_types`) computes them for the same purpose; `artifact_rename.py:63-74` computes them for the rename self-commit. This child removes the COMMIT half at all four sites while PRESERVING the REFRESH half, so the manifests stay current on disk and `check.stale-index` keeps working. It must land BEFORE untracking, because a `git commit -- <gitignored path>` in a journalled transaction is the sharpest failure mode in the whole change.
- Scope: The four commit-path-set sites and their tests. IN: dropping the manifest paths from `owned_paths` (`ipd_lifecycle.finalize`), from the `aw set` self-commit path list, from `_index_paths_for_types`, and from `artifact_rename`'s self-commit paths; keeping every REGENERATION call untouched; updating `tests/test_auto_index_on_mutation.py` so the refresh half stays covered rather than deleted. OUT: `.gitignore`, `git rm --cached`, the `check.stale-index` semantics decision, and the three documents (all child 02); any change to WHEN a manifest is regenerated.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/status_set.py, agent_workflows/artifact_rename.py, tests/test_auto_index_on_mutation.py
- Item-Dependencies: none
- Status: draft
- Set: idxuntrack
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: ila6vl
- Id: 4r0qp1

## Workflow history

- 2026-09-06 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-06 authored (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `ila6vl` (maintainer decision 2026-08-31 to stop tracking the generated manifests; external-consumer check answered 2026-09-06: none). Every consumer line citation on the item was RE-VERIFIED at HEAD `7f80180e` rather than trusted, and two had drifted: `ipd_lifecycle` owned_paths moved from the item's `:1630` to `:2340`, and the `status_set` auto-refresh from `:823-894` to `:936-972`. Split from the item's single scope because the COMMIT-path removal must strictly precede untracking.

## Goal

Make every code path that currently COMMITS a generated index manifest stop doing so, while leaving every path that REGENERATES one untouched. After this child, the manifests are still written and still byte-comparable on disk, but no `aw` verb tries to include them in a commit. That is the precondition that makes child 02's `git rm --cached` safe.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: remove the commit half, preserve the refresh half

- [ ] E-01 In `ipd_lifecycle.finalize`, stop putting the two plans-manifest paths into the transaction's `owned_paths`. Locate by SYMBOL (`owned_paths`, the `index_json_rel`/`index_md_rel` locals), not by the line number, which has already drifted once. Keep the manifest REGENERATION that the MUTATING phase performs; remove only the paths from the commit set. Re-read the surrounding docstring's phase list (`PREPARED -> MUTATING -> READY_TO_COMMIT -> commit -> ...`) and confirm no rollback/journal step keys on those two entries before removing them; if one does, report it rather than working around it.
  - Depends on: none
  - Expected outcome: `owned_paths` contains the plan's source and destination paths only; the finalize commit no longer names a manifest; the manifest is still refreshed on disk during the transaction.
  - Execution state: pending

- [ ] E-02 In `status_set.py`, stop returning the manifest paths for the `aw set` auto-refresh self-commit, at BOTH collection sites (the plans branch and the research branch around `:936-972`) and in `_index_paths_for_types` (`:1122-1138`). Keep every `run_index`/refresh call. `_index_paths_for_types` exists ONLY to produce self-commit paths, so decide explicitly and record which: delete the function and its call sites, or keep it returning an empty list with a docstring saying why. Prefer deletion if nothing else consumes it; prove which by grepping its callers before choosing.
  - Depends on: none
  - Expected outcome: an `aw set` status change refreshes the manifests on disk and commits only the artifact whose status changed.
  - Execution state: pending

- [ ] E-03 In `artifact_rename.py`, stop computing the manifest paths for the rename self-commit (the helper at `:63-74`). Same rule as E-02: the refresh stays, the commit-path contribution goes.
  - Depends on: none
  - Expected outcome: `aw rename <type>` refreshes the manifests and commits only the renamed artifact plus any files whose references it rewrote.
  - Execution state: pending

- [ ] E-04 Update `tests/test_auto_index_on_mutation.py` (6 test functions at HEAD) so the REFRESH half stays covered and the COMMIT half is asserted ABSENT. Do not delete a test to make it pass: for each case that currently asserts a manifest was committed, invert it to assert the manifest was refreshed on disk AND is not in the commit's path set. The point of the file is that a mutation keeps the manifest current; that guarantee must survive this change.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the module still fails if a future change stops refreshing a manifest, and now also fails if one starts committing a manifest again.
  - Execution state: pending

- [ ] E-05 Confirm no OTHER site adds a manifest to a commit path-set. Sweep for `INDEX.json`/`INDEX.md`/`INDEX_JSON`/`INDEX_MD` across `agent_workflows/` and classify every hit as writer, path constant, help text, reader, or commit-path contributor. The four in this plan's scope were found that way at HEAD `7f80180e`; a fifth appearing since is exactly the kind of thing this item's own 6-day-stale citations prove happens. Report any new one instead of silently expanding scope.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: a pasted classification of every hit, with zero unaccounted commit-path contributors, or a named new one reported for a scope decision.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The framework-owned `.aw/.gitignore` is the established mechanism for ignoring generated content, and it already carries a near-identical precedent: `system/layout.json` and `system/layout.schema.json` are gitignored with the comment "tracking generated output is exactly the git drift install-time emission exists to avoid." The maintainer chose that mechanism explicitly for `layout.json` on 2026-09-01, citing `ila6vl`. Child 02 follows it rather than the user's root `.gitignore`.
- `aw index plans --check` byte-compares an in-memory rebuild against the file ON DISK, never against git. Verified by running it at HEAD (`plans index --check: clean`, 490 plans). This is why untracking does not break the check, and it is the item's own point 6.
- The suite must be run bare (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.
- This is a shared checkout with concurrent agents and runs. Prefer an isolated worktree for execution; a measured lesson from 2026-09-06, when a co-worker's mid-run commit caused 56 unrelated failures to be misattributed to a local change.

## Findings

| Id | Severity | Location (HEAD `7f80180e`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.py:2340-2343` | Both plans-manifest paths go into `owned_paths` for the finalize lifecycle commit. This is the sharpest edge: `finalize` is a journalled transaction with rollback and a committed-incomplete resume path, so a path that cannot be committed could wedge it. | source read; `owned_paths = [plan_rel, dest_rel, index_json_rel, index_md_rel]` |
| F-2 | MED | `status_set.py:936-937,971-972` | The `aw set` auto-refresh collects manifest paths for its self-commit, for plans and research separately. | source read |
| F-3 | MED | `status_set.py:1122-1138` | `_index_paths_for_types` exists solely to compute manifest self-commit paths (docstring names jgcm68 E-05). | docstring: "Repo-relative INDEX.json/INDEX.md paths for the indexed types just refreshed" |
| F-4 | MED | `artifact_rename.py:63-74` | Computes manifest paths for the rename self-commit. | docstring: "jgcm68 self-commit paths" |
| F-5 | LOW | item `ila6vl` body | Two of the item's line citations had drifted in 6 days (`:1630` -> `:2340`; `:823-894` -> `:936-972`). The consumers are all still real. | re-verified at HEAD `7f80180e` |
| F-6 | INFO | CI | No CI workflow references INDEX at all (`local-leaks.yml`, `secret-scan.yml`, `tests.yml`), so the item's scope point 8 ("confirm nothing in CI expects a committed baseline") is already satisfied. | `grep -rn INDEX .github/` returns nothing |

## Proposed changes (ordered, validatable)

1. E-01 removes the manifest paths from the finalize transaction's commit set (highest risk first, so a problem surfaces before the cheaper edits are made).
2. E-02 and E-03 remove the same contribution from the `aw set` and `aw rename` self-commits.
3. E-04 re-points the existing test module so both halves (refresh present, commit absent) are pinned.
4. E-05 proves no fifth site exists.

## Deferred / out of scope (with reason)

- `.gitignore` entries and `git rm --cached`: child 02. Doing them here would mean this child's own validation runs against files that are simultaneously tracked and gitignored.
- The `check.stale-index` semantics decision: child 02, because it is only forced once the files are untracked.
- The three documents (`.aw/records/plans/README.md`, `.aw/records/research/README.md`, `CONTRIBUTING.md`): child 02, where the statements actually become wrong.
- Any change to regeneration TIMING or to `aw index` itself: not needed by this item and would widen the blast radius.

## Scope check

- Over-scope: none.
- Under-scope: none. This child is deliberately the code-only half; the tree-state half is child 02, which declares a dependency on this one.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, with the baseline measured in that worktree at execution time and pasted. Compare failing NODE IDS, not totals: ~35 environment-related failures are expected in any lane worktree (backlog `agrlvw`), and a concurrent co-worker commit can move the total under the executor's feet. Beyond the suite, E-01 requires an actual `aw ipd finalize` exercise (or the existing finalize tests) proving the transaction still completes with the manifests absent from `owned_paths`.

## Spec / documentation sync

N/A for this child: it changes no documented behavior. The three documents that assert the manifests are committed become wrong only once child 02 untracks them, and child 02 owns correcting them.

## Open questions

### OQ-01: Delete `_index_paths_for_types` or make it return empty?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: E-02 resolves this from repository evidence rather than asking: grep its callers, and delete it if the self-commit is the only consumer (which the docstring asserts). Either choice satisfies the goal; the executor records which and why. Not escalated to the maintainer because it is an internal-helper shape with no public contract.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the post-change `owned_paths` construction showing no manifest entries, AND pasted output of a finalize exercise (a real `aw ipd finalize` on a scratch plan, or the finalize test subset) completing successfully. Also paste a grep of the journal/rollback code proving no step keys on the removed entries.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste an `aw set` status change on a scratch artifact showing (a) the manifest file's mtime/content updated on disk, and (b) `git show --stat` of the resulting commit containing no INDEX path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste an `aw rename <type>` exercise showing the manifest refreshed on disk and absent from the resulting commit's `--stat`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the full `python3 -m pytest tests/test_auto_index_on_mutation.py -o addopts="" -q` output (passing), plus a MUTATION CHECK: temporarily re-add a manifest path to one commit set, show the module FAILS, then revert and show it passes again. A test that cannot fail is not evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the classification sweep (every `INDEX*` hit under `agent_workflows/` with its category) showing zero remaining commit-path contributors.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, because pre-commit's stash/restore can leave a co-worker's paths in the index. When reporting tests passed, paste the ACTUAL runner output.

Post-gate lifecycle: this plan requires explicit human approval (`aw ipd set approved 4r0qp1 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: it is an output of `/plan-review` and writing one forges a review that did not happen (`IPD-M107`). On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence.
