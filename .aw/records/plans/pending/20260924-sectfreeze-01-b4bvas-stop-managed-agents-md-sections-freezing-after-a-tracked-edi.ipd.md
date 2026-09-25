# IPD: Stop managed AGENTS.md sections freezing after a tracked edit, without clobbering real user drift

- Date: 2026-09-24
- Kind: child
- Concern: `engine._apply_section_consent` decides a managed section's fate by comparing the on-disk body ONLY to the manifest's recorded hash. Two defects follow. (A) FREEZE: when a tracked commit edits a managed section to exactly what the generator now emits, the recorded hash goes stale; every later install classifies the section as user drift, preserves it, and never re-records, so no future generator change ever lands. This repo's `AGENTS.md#aw:pointer` is in that state now (recorded `7446019f`, on-disk and generated both `b8a499df`). (B) CLOBBER: with NO recorded hash the preserve branch is skipped (`manifest.recorded_hash(key) is not None`), so a genuinely user-edited section is silently overwritten. Neither path prints anything, so the user never learns a section was held back or replaced.
- Scope: IN: rewrite the per-section decision in `engine._apply_section_consent` into four explicit cases (disk equals desired: adopt and re-record; disk equals recorded: normal refresh; disk differs from both: preserve and warn by name; no record and disk differs from desired: preserve and warn), surface the warnings through `merge_aw_block` to its callers (`engine.update_agents_pointer`, `engine.ensure_untracked_gitignore`) using the same wording shape the shim path already prints; unit tests for all four cases plus the declined and absent-section cases; amend the user-facing managed-sections doc and record the decision; one-time reconciliation of THIS repo's `AGENTS.md` / manifest through the installer's own pointer code path. OUT: shim/file drift (`_shim_is_user_modified`, already correct), an interactive "take the new version" prompt for sections, any hand edit of `AGENTS.md` or `managed-sections.json`.
- Scope-Paths: agent_workflows/engine.py, tests/test_section_consent.py, .aw/system/README.md, DECISIONS.md, CHANGELOG.md, .aw/system/managed-sections.json, AGENTS.md
- Item-Dependencies: none
- Status: to-review
- Set: sectfreeze
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: b4bvas
- From-Backlog: krwl3t
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog krwl3t; re-measured at HEAD 877545fc that the pointer hash is still frozen (recorded 7446019f vs on-disk = generated b8a499df), that a simulated generator change does not land, that a stale record is never refreshed even when disk equals desired, and that a no-record user edit is clobbered.

## Goal

Make a managed section whose on-disk body already equals the generator's output self-heal (re-record its hash), keep refreshing sections the installer owns, and PRESERVE-AND-WARN on every body that matches neither the generator nor the record, including when no record exists, so installer consent state can neither freeze silently nor clobber silently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the defects before changing anything

- [ ] E-01 Write `tests/test_section_consent.py` FIRST, driving `engine._apply_section_consent` directly with `manifest.Manifest()` instances and `engine.AwSection` values (no install, no git; a `tempfile.TemporaryDirectory` round-trip through `manifest.save`/`manifest.load` for at least the frozen case, so the persisted hash is what is asserted). Cases, one test each, named for the case:
  (1) `disk == desired`, record STALE (different hash): result body is desired AND `recorded_hash(key) == hash_content(desired.body)` after the call, and NO warning emitted.
  (2) `disk == recorded`, desired differs (generator changed): result body is desired, record updated to desired, no warning.
  (3) disk differs from BOTH desired and recorded: result body is disk (preserved), record UNCHANGED, exactly one warning naming `AGENTS.md#aw:pointer`.
  (4) NO record, disk differs from desired: result body is disk, NO record written for the key (so a later install still sees it as unowned), exactly one warning naming the key.
  Plus two regression rows that must stay as today: a declined tombstone omits the section; a section absent on disk (`on_disk=[]`) writes desired and records its hash; and `manifest=None` writes desired (back-compat, documented in the docstring).
  Also one end-to-end row through `engine.merge_aw_block` showing a warning from case 3 reaches the caller-visible channel chosen in E-02.
  Run it against the UNCHANGED code and capture which rows fail: cases 1 and 4 and both warning assertions must fail; case 2, 3's body/record assertions, and the regression rows must pass.
  - Depends on: none
  - Expected outcome: the new module exists; against HEAD code it fails exactly on case 1 (stale record not refreshed), case 4 (user body clobbered) and the warning assertions, and passes the rest.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-02 Rewrite the per-section decision in `engine._apply_section_consent` as four explicit branches, evaluated in this order after the existing declined check and only when `manifest is not None and disk is not None`: (1) `disk.body == sec.body` (compare normalized via `manifest.hash_content` on both, so line-ending differences do not count as drift): append `sec`, `manifest.record(...)`; (2) `manifest.matches_recorded(key, disk.body)`: append `sec`, record; (3) recorded hash exists and matches neither: append `disk`, leave the record untouched, emit warning; (4) no recorded hash: append `disk`, write NO record, emit warning. The absent-section, `manifest is None`, and declined paths keep today's behavior. Add a keyword-only `warnings: Optional[list[str]] = None` parameter to `_apply_section_consent` and to `merge_aw_block` (threaded to every `_apply_section_consent` call inside it) that collects one message per preserved section. Message text, modelled on the shim path's `"Warning: {relative_posix} has manual modifications."` in `engine.write_file`: `"Warning: {key} has manual modifications; kept your version, the regenerated section was NOT applied. To take the new version, delete that section (from its <!-- aw:{slug} --> marker to the next marker) and re-run install."` (the remedy is real: an absent section takes the `disk is None` write path). Update the docstrings of both functions and the `merge_aw_block` consent paragraph to state the four cases.
  - Depends on: E-01
  - Expected outcome: all rows of `tests/test_section_consent.py` pass; the function's four branches are readable in order in the diff.
  - Execution state: pending

- [ ] E-03 Print the collected warnings in both callers: `engine.update_agents_pointer` (for `AGENTS.md` and each mirrored `NATIVE_AGENT_FILES` entry) and `engine.ensure_untracked_gitignore`, each passing its own list to `merge_aw_block` and printing every entry with `Term(color=False if plan.no_color else None).colorize(msg, "yellow")`, as the shim path does. Printing happens on a dry run too (the decision is the same; only the write is skipped). Add one install-level test to `tests/test_section_consent.py` that seeds a temp repo via `tests.support.init_repo` + `engine.install_into_repo(..., yes=True, no_color=True)`, hand-edits the pointer section body, re-installs with stdout captured, and asserts the named warning appears AND the edit survives.
  - Depends on: E-02
  - Expected outcome: an install over a hand-edited section prints `Warning: AGENTS.md#aw:pointer has manual modifications; ...` and keeps the edit; an install over an unedited repo prints no such line.
  - Execution state: pending

### Task group 3: docs and record

- [ ] E-04 Amend the user-facing policy: in `.aw/system/README.md` section `## Managed sections`, replace "leave a section you edited alone" with the four-case rule in plain words (matches the new template: adopted silently; matches what the installer last wrote: updated; matches neither, or no record: kept and warned by name, with the delete-and-reinstall remedy). No em/en dashes (user-facing). Add a `DECISIONS.md` entry (next free number after D154) amending D104's consent clause ("on-disk body differing from OUR recorded hash -> preserved as user drift; else written"), citing krwl3t and this plan. Add a `CHANGELOG.md` `- Fixed:` line under the pending 2.0.0 entry, no em/en dashes.
  - Depends on: E-02
  - Expected outcome: the three files describe the same four cases; `grep -n "leave a section you edited alone" .aw/system/README.md` returns nothing.
  - Execution state: pending

### Task group 4: reconcile this repo, then the suite

- [ ] E-05 One-time reconciliation of THIS repo through the installer's own pointer path, NOT a hand edit. Use the installer's AGENTS.md code path in-process, scoped so it touches only `AGENTS.md` and the section keys of the manifest:
  `python3 -c "from pathlib import Path; from agent_workflows import engine as E, manifest as M; r=Path('.').resolve(); p=r/'.aw/system/managed-sections.json'; m=M.load(p); pl=E.InstallPlan(source_root=r/'.aw/system/workflows', repo_root=r, dry_run=False, backup=False, prune=False, no_color=True, yes=True, manifest=m); print(E.update_agents_pointer(pl, use_git=False, timestamp='reconcile', target_layout=E.resolve_target_layout(r))); M.save(m, p)"`
  Rationale for not running `python3 -m agent_workflows install . -y`: measured on a throwaway clone at 877545fc it rewrote 111 existing manifest entries, touched 95 files, and committed them itself with a raw `git commit -m "agent-workflows: sync via installer"`, which violates the execution contract (`aw commit` only, Scope-Paths only). If the executor prefers the full verb, run it with `--dry-run` first and paste that it reports only `AGENTS.md`; otherwise use the scoped call above. Then paste `git diff -- AGENTS.md .aw/system/managed-sections.json`. Expected: `AGENTS.md` UNCHANGED (on-disk already equals generated), and the manifest diff is exactly the `AGENTS.md#aw:pointer` `sha256` changing `7446019f...` -> `b8a499df...` (case 1 self-heal). Commit with `aw commit b4bvas -- .aw/system/managed-sections.json` (plus `AGENTS.md` only if it changed). If `AGENTS.md` DID change, or any other manifest key changed, STOP and report instead of committing.
  - Depends on: E-03
  - Expected outcome: recorded pointer hash equals the hash of the on-disk pointer body; a re-run of the same command produces an empty diff.
  - Execution state: pending

- [ ] E-06 Run the BARE suite `python3 -m pytest` (no extra flags) after all changes.
  - Depends on: E-05
  - Expected outcome: the summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Installer section consent lives in `engine._apply_section_consent`, called only from `engine.merge_aw_block`, whose callers are `engine.update_agents_pointer` (AGENTS.md plus the CLAUDE.md/GEMINI.md mirror) and `engine.ensure_untracked_gitignore` (`.gitignore#aw:untracked`, `AW_STYLE_HASH`). Section keys are `<file>#aw:<slug>` under the manifest's `files` map; `managed_sections` is an inert reserved field (`manifest.Manifest.managed_sections`, "reserved in the schema").
- Hashing is normalized (`manifest.hash_content`: "Deterministic across line endings"); compare with it, not raw strings.
- The shim path is the precedent for drift warnings: `engine.write_file` prints `f"Warning: {relative_posix} has manual modifications."` via `Term.colorize(..., "yellow")`. The shim decision table lives in `tests/test_installer.py` `test_every_manifest_regime_decides_drift_correctly`; its no-record fallback ADOPTS structurally valid generated content, which is the analogue of case 1 here.
- No `.spec.md` defines section consent (grep of `.aw/records/specs` and `docs/` for "section consent"/"managed section" hits only `docs/reporting-contract.md`, which states `aw:reporting` edits are "not clobber[ed]", consistent with this plan, and a deferred clean-delta spec that merely cites IPD 02). The policy of record is DECISIONS `D104` plus `.aw/system/README.md` `## Managed sections`.
- `tests/test_installer.py` is a consolidated table-style module whose header forbids casual merging; new tests go in a new module.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Re-measured at HEAD `877545fc` (`git rev-parse --short HEAD`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `.aw/system/managed-sections.json` `files["AGENTS.md#aw:pointer"]` | Still frozen. The backlog item's hashes (`a9deb5a1`/`935b3f15`) are STALE; the defect is not: 91ba3d7c re-recorded once and later commits re-froze it. | probe: recorded `7446019f`; `parse_aw_block(AGENTS.md)` pointer `b8a499df`; `agents_managed_sections("aw")` pointer `b8a499df` (`eq True`); `resolve_target_layout(.)` -> `aw`. `aw:reporting` and `.gitignore#aw:untracked` are consistent (`2ab6fbfb`x3, `137d080a`x3). |
| F-2 | HIGH | `engine._apply_section_consent` | A generator change does not land. | `merge_aw_block` with the real manifest and a pointer body plus one appended line: `generator change lands: False`. |
| F-3 | HIGH | `engine._apply_section_consent` | ROOT CAUSE: when disk equals desired but the record is stale, the preserve branch fires (result is identical text, so it looks harmless) and never calls `manifest.record`, so the stale hash persists forever. | probe: `disk==desired, stale record: hash updated: False`; real install on this repo leaves `7446019f` and prints `AGENTS.md: pointer already current`. |
| F-4 | HIGH | `engine._apply_section_consent` condition `manifest.recorded_hash(key) is not None` | With no record a user-edited section is clobbered, silently. | probe with `Manifest()`: `no-record user edit kept: False`; also via `merge_aw_block`: `no-record user edit survives: False`. |
| F-5 | MED | `engine._apply_section_consent` / `engine.update_agents_pointer` | Preserving drift prints nothing; the only output is the per-file status (`pointer already current` / `refreshed pointer in ...`), so a held-back section is invisible. | `grep` for `print`/`warn` in the function body: none; installer output on this repo: `AGENTS.md: pointer already current`. |
| F-6 | INFO | `python3 -m agent_workflows install . -y` | The full installer is too broad for a reconciliation: on a throwaway clone it produced a self-made raw commit `agent-workflows: sync via installer` touching 95 files and 111 existing manifest entries, and still left the pointer at `7446019f`. | clone probe under `/tmp/opencode/probe-sectfreeze/`; `git show --stat HEAD` -> `95 files changed`; manifest compare `changed existing: 111`, pointer `('7446019f','7446019f')`. |
| F-7 | INFO | re-freeze mechanism | The commits that re-froze it edit the generator and `AGENTS.md` together (`ecd541be`, `73eef4e9` touch `engine.py` and `AGENTS.md`), leaving disk == desired: exactly case 1, which this fix self-heals on the next install. | `git show --stat` of each. |

## Proposed changes (ordered, validatable)

1. E-01: failing-first unit tests for the four cases and the unchanged regression rows.
2. E-02: four-branch decision in `_apply_section_consent`, warnings collected via a new keyword-only list threaded through `merge_aw_block`.
3. E-03: both callers print the warnings; one install-level test proves the message and the preserved edit.
4. E-04: README, DECISIONS and CHANGELOG record the amended consent rule.
5. E-05: scoped installer reconciliation of this repo, diff pasted.
6. E-06: bare suite.

## Deferred / out of scope (with reason)

- An interactive "take the regenerated version?" prompt for a drifted section (the shim path has one). The warning's delete-and-reinstall remedy is sufficient for a bug fix; a prompt is a UX feature.
  - Carrier-Declined: Feature, not part of the krwl3t defect; the printed remedy gives the user a working path today.
- A guard test that this repo's `AGENTS.md` pointer body equals `agents_managed_sections("aw")` output. With case 1 fixed, a joint generator-plus-AGENTS.md edit self-heals, so the freeze cannot recur by that route.
  - Carrier-Declined: The fix removes the recurrence mechanism (F-7); an equality guard would duplicate it.
- Running the full `install . -y` on this repo to sync the 111 drifted non-section manifest entries and 95 files (F-6), and the installer's raw `git commit` in `engine.prompt_and_run_commit`.
  - Carrier-Declined: Unrelated to section consent and outside krwl3t; noted here as an observation for the maintainer, not filed by this plan.

## Scope check

- Over-scope: none. The `.gitignore` caller is touched only to print warnings the shared function now produces; not doing so would drop them.
- Under-scope: cases 3 and 4 change behavior for every managed repo. Case 4 could hold back a pre-manifest generated section, but a sectioned `aw:block` only exists since D104, which DEPENDS ON D103 (the manifest), so a sectioned block with no record arises only from a lost or deleted manifest; legacy `AGENT-WORKFLOWS:BEGIN/END` conversion passes `on_disk=[]` in `merge_aw_block` and is unaffected. Covered by OQ-01.

## Required tests / validation

- `python3 -m pytest tests/test_section_consent.py -o addopts="" -q` failing first (E-01), passing after (E-02, E-03).
- Mutation check: revert only the E-02 branch change and show cases 1 and 4 fail again.
- Existing consent tests stay green: `python3 -m pytest tests/test_installer.py -o addopts="" -q -k "AwBlock or idempotence_and_declined or Manifest"`.
- Bare `python3 -m pytest`, summary pasted.

## Spec / documentation sync

- No `.spec.md` governs section consent (see Step 0), so no spec amendment. The policy of record is amended instead: `.aw/system/README.md` `## Managed sections` (user-facing, shipped with the system bundle), a new `DECISIONS.md` entry amending D104's consent clause, and a `CHANGELOG.md` `Fixed` line. All three are in `- Scope-Paths:`.
- `docs/reporting-contract.md` ("the installer will not clobber the edit") remains true and is strengthened by case 4; no edit needed.

## Open questions

### OQ-01: Should case 4 (no record, disk differs from desired) preserve, or adopt the generated body like the shim fallback?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Preserve and warn. The shim fallback (`engine._shim_is_user_modified`) adopts only STRUCTURALLY generated content, a test that has no analogue for free-prose sections. Adoption would reintroduce F-4's silent clobber. The realistic population of case 4 is small: sectioned blocks were introduced by D104, which depends on D103's manifest, so a no-record sectioned block implies a lost manifest; the warning names the remedy. A maintainer who wants adoption can say so at review.
- Carrier-Declined: Resolved from repository evidence with no residual work.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest tests/test_section_consent.py -o addopts="" -q` run against the UNMODIFIED `engine.py` (before E-02), with the failing test names listed; the failures must be exactly case 1, case 4 and the warning assertions, and the declined/absent/`manifest=None` rows must pass.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same command after E-02 showing all passed (except E-03's install-level test if not yet written); paste `git diff -- agent_workflows/engine.py` for `_apply_section_consent` showing the four ordered branches; paste the mutation run (E-02 branch reverted locally, then restored) showing cases 1 and 4 failing again.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the install-level test passing, and paste the captured warning line `Warning: AGENTS.md#aw:pointer has manual modifications; ...` from it; paste `python3 -m pytest tests/test_installer.py -o addopts="" -q -k "AwBlock or idempotence_and_declined or Manifest"` showing 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diffs of `.aw/system/README.md`, `DECISIONS.md`, `CHANGELOG.md`; paste `grep -n "leave a section you edited alone" .aw/system/README.md` returning nothing; paste `grep -nP "[\x{2013}\x{2014}]"` over the new README and CHANGELOG lines returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the command run and its printed status dict; paste `git diff -- AGENTS.md .aw/system/managed-sections.json` showing AGENTS.md unchanged and only the `AGENTS.md#aw:pointer` `sha256` moving `7446019f...` -> `b8a499df...`; paste a second run of the same command followed by `git diff --stat -- AGENTS.md .aw/system/managed-sections.json` empty after the commit; paste the `aw commit` output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. OQ-01 is resolved with a stated default and does not block. The executor commits only the paths in `- Scope-Paths:` through `aw commit b4bvas -- <paths>`, never `git add -A`, never pushes, and never hand-edits `AGENTS.md` or `.aw/system/managed-sections.json` (E-05 goes through the installer's pointer path). Test claims must paste actual runner output. The terminal lifecycle move is finalized by the runner in a managed lane, or by the executor with `aw ipd finalize` in an unmanaged run, only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence.
