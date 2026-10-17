# IPD: Keep this repo's AGENTS.md section records in step with joint generator edits

- Date: 2026-10-17
- Kind: child
- Concern: In this repository `aw install .` reports `AGENTS.md#aw:pointer` as manually modified and does not apply a regenerated pointer, because the section hash recorded in `.aw/system/managed-sections.json` matches neither the on-disk body nor the generator. Plan `b4bvas` (backlog `krwl3t`) fixed the installer so a section whose disk body equals the generator SELF-HEALS its record on the next install. That fix is correct and still in place, but in THIS repo the self-heal never runs: changes to the managed text land as joint commits that edit `engine.agents_pointer_prose` / `reporting_contract` AND rewrite `AGENTS.md` by script (the full installer is measured unsafe here, see `b4bvas` F-6 and `er11a0` E-07), and nothing re-records the hash. The stale record then turns the NEXT generator change into a "manual modifications" warning (case 3) and the change silently fails to land. Measured now at HEAD `3812c4002`: BOTH `AGENTS.md` sections are stale (`aw:pointer` recorded `0fbbebcf`, on-disk = generated `bc256612`; `aw:reporting` recorded `2ab6fbfb`, on-disk = generated `46970f75`).
- Scope: IN: a repo-local tool `tools/regen_agents_block.py` (run as `python3 -m tools.regen_agents_block`, with `--check`) that rewrites ONLY the `aw:block` region of this repo's `AGENTS.md` from the generator and re-records each section hash through the installer's own `engine.merge_aw_block` path, never touching native mirror files (`GEMINI.md`, `CLAUDE.md`) or any other manifest key; a behavioral guard test that drives `merge_aw_block` against this repo's live `AGENTS.md` and manifest with a perturbed generator and asserts the change lands with no warning (the symptom itself), plus synthesized-repo tests for the tool; a one-time reconciliation of this repo via the tool; contributor docs naming the tool as the owner of the managed block; a DECISIONS entry recording why `b4bvas`'s declined equality guard is now added. OUT: any change to `engine._apply_section_consent` (its four-case logic is correct, verified below), the full `aw install .` path and its raw self-commit, `GEMINI.md`'s missing block, any hand edit of `AGENTS.md` or the manifest.
- Scope-Paths: tools/regen_agents_block.py, tests/test_agents_section_records.py, AGENTS.md, .aw/system/managed-sections.json, CONTRIBUTING.md, tools/README.md, DECISIONS.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: q3ogs0
- Blocks-Release: next
- Set: q3ogs0
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: l5t4vx

## Workflow history
- 2026-10-17 to-review (aw set): graduated from backlog q3ogs0; re-measured at HEAD 3812c4002 that both AGENTS.md section records are stale while on-disk equals the generator, that a perturbed generator does not land against the live manifest and does once reconciled in memory, and traced the staleness to joint generator+AGENTS.md commits that bypass the installer


## Goal

Make every future change to the managed `AGENTS.md` text in this repository land through a tooled path that re-records the section hashes, and fail the routine test gate the moment a commit leaves them stale, so the `krwl3t`/`q3ogs0` freeze cannot silently recur a third time.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: failing-first tests

- [ ] E-01 Create `tests/test_agents_section_records.py` (module `pytestmark = pytest.mark.core`; all cases are in-process and use `tempfile`, so they fit the core budget). Cases: (a) LIVE GUARD: load this repo's `.aw/system/managed-sections.json` with `manifest.load` into memory (never save), read this repo's `AGENTS.md`, build `engine.agents_managed_sections("aw")`, and for EACH section append one sentinel line to that section only; call `engine.merge_aw_block(text, perturbed, manifest=m, file_key="AGENTS.md", warnings=w)` and assert, per section, that the sentinel appears in the result and `w` is empty. On failure the message must name the remedy `python3 -m tools.regen_agents_block` and the stale key. (b) SYNTHESIZED: in a `tempfile` repo with `.aw/system/` present, an `AGENTS.md` carrying foreign text above and below an `aw:block` whose sections equal the generator, a manifest whose two `AGENTS.md#aw:*` records are deliberately wrong plus one unrelated `files` entry, and a `GEMINI.md` with no block: calling the tool's `reconcile(repo_root)` leaves `AGENTS.md` byte-identical, makes each recorded hash equal `manifest.hash_content` of the on-disk body, leaves the unrelated entry and `GEMINI.md` byte-identical, and a second call reports no change. (c) SYNTHESIZED: with the managed region differing from the generator (simulating a generator edit), `reconcile` rewrites only the region between the markers to `engine.agents_managed_block(target_layout="aw")`, keeps foreign text byte-identical, and records hashes; `reconcile(repo_root, check=True)` beforehand returns a nonzero/"stale" result and writes nothing. (d) SYNTHESIZED: an `AGENTS.md` with two `aw:block` openers is refused (`parse_aw_block(...).ambiguous`) with nothing written. Run against the UNMODIFIED tree before E-02.
  - Depends on: none
  - Expected outcome: (a) FAILS on both sections with the case-3 warning (the live defect); (b)-(d) fail with an import error for `tools.regen_agents_block`. If (a) PASSES, someone has already reconciled the manifest: stop and re-measure before continuing (stop condition 2).
  - Execution state: pending

### Task group 2: the tool

- [ ] E-02 Create `tools/regen_agents_block.py` with `reconcile(repo_root: Path, *, check: bool = False) -> dict` and a `main(argv)` (`argparse`, `--check`, `--dir`, default repo root = cwd; exit 0 when current or reconciled, 1 when `--check` finds staleness, 2 when refused). Implementation: resolve layout with `engine.resolve_target_layout`, the file with `engine.resolve_agents_file`, the manifest path with `manifest.resolve_manifest_path`; refuse when `parse_aw_block` reports `not found` or `ambiguous`; compute `new_text` by `engine.merge_aw_block(existing, desired, manifest=None)` (the documented `manifest is None -> write desired` branch, so a stale record cannot hold the region back); then RECORD by calling `engine.merge_aw_block(new_text, desired, manifest=m, file_key=rel, warnings=w)`, which hits consent case 1 (disk equals desired) and records each hash through the installer's own code, so the tool never computes or writes a hash itself; assert `w` is empty. Write `AGENTS.md` only if `new_text != existing`, save the manifest with `manifest.save` only if a section record changed, and return `{"file": rel, "text_changed": bool, "records_changed": [keys]}`. Do NOT call `engine.update_agents_pointer` (it mirrors into `GEMINI.md`, measured: dry run reports "would be updated (appended pointer to existing GEMINI.md)"). Module docstring states it is repo-local developer tooling for the framework's own checkout, not shipped (`pyproject.toml` `packages = ["agent_workflows"]`).
  - Depends on: E-01
  - Expected outcome: E-01 (b)-(d) pass; (a) still fails (the live manifest is not yet reconciled).
  - Execution state: pending

### Task group 3: reconcile this repo

- [ ] E-03 Run `python3 -m tools.regen_agents_block --check` (expect exit 1 naming both `AGENTS.md#aw:*` keys), then `python3 -m tools.regen_agents_block`, then `--check` again (expect exit 0). Commit `.aw/system/managed-sections.json` (and `AGENTS.md` only if the tool changed it, which happens only if another plan changed the generator first).
  - Depends on: E-02
  - Expected outcome: `git diff -- .aw/system/managed-sections.json` shows exactly the `sha256` lines of the `AGENTS.md#aw:pointer` and `AGENTS.md#aw:reporting` entries moving to the hashes of the on-disk bodies; no other key moves; E-01 (a) now passes.
  - Execution state: pending

### Task group 4: documentation

- [ ] E-04 Record the ownership rule: in `CONTRIBUTING.md` `### Regenerating Derivative Artifacts` add a bullet "**Managed AGENTS.md block (`<!-- aw:block -->` region) and its section hashes**: `python3 -m tools.regen_agents_block` after any change to the generator (`engine.agents_pointer_prose`, `reporting_contract`); never edit the region by hand or script it directly", and add `AGENTS.md` (managed region) to the **Generated** row of the classification table; add a `## \`regen_agents_block.py\`` section to `tools/README.md` with usage and exit codes; add the next free `DECISIONS.md` entry (re-derive; `D174` is highest at authoring, so `D175`) recording that `b4bvas`'s declined "guard test that this repo's pointer equals the generator" is now added, because its premise (F-7: "this fix self-heals on the next install") does not hold in a repo where the installer is not run, as `q3ogs0` measured.
  - Depends on: E-03
  - Expected outcome: the three files carry the rule; `grep -n "regen_agents_block" CONTRIBUTING.md tools/README.md DECISIONS.md` hits each.
  - Execution state: pending

### Task group 5: suite

- [ ] E-05 Run `python3 -m pytest tests/test_agents_section_records.py tests/test_section_consent.py -o addopts="" -q` and `python3 -m pytest tests/test_agents_block_target_neutral.py tests/test_askme_command_delivery.py -o addopts="" -m ""`, then the bare suite `python3 -m pytest`.
  - Depends on: E-04
  - Expected outcome: 0 failed in each.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Section consent lives in `engine._apply_section_consent`, reached only through `engine.merge_aw_block`; since `b4bvas` it has four ordered cases (disk == desired: adopt and re-record; disk == recorded: refresh; record exists and matches neither: preserve and warn; no record: preserve and warn), and `manifest is None` writes desired. The tool relies on the first and last of these, both covered by `tests/test_section_consent.py` (12 passed at authoring).
- Hashes are normalized (`manifest.hash_content`); records are written by `Manifest.record(key, body, kind="section", host="", logical_id=slug)` inside `_apply_section_consent`. Writing a hash any other way would assert the installer wrote something it did not (`b4bvas` gate: "NEVER HAND-EDIT `AGENTS.md` OR `.aw/system/managed-sections.json`").
- `engine.update_agents_pointer` also mirrors the block into EXISTING native files; this repo's `GEMINI.md` exists with no block, so that function would append one (measured dry run). Hence the tool targets `AGENTS.md` only.
- Repo-local tools live in `tools/`, are not packaged (`pyproject.toml` `packages = ["agent_workflows"]`), and are imported by tests as `tools.<module>` (precedent `tests/test_dead_status_token_scan.py`: `from tools.dead_status_token_scan import ...`; `tools/` has no `__init__.py`, namespace import works).
- Bare `python3 -m pytest` runs only `core`-marked tests (`conftest.py` `pytest_collection_modifyitems`, marker defined in `pyproject.toml`); the routine gate is the runner merge gate.
- Generated-file ownership is documented in `CONTRIBUTING.md` `## File Classification and Ownership` / `### Regenerating Derivative Artifacts` ("Never hand-edit generated files. Use the owning CLI verb"), which today names no owner for the `AGENTS.md` managed block.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `3812c4002` in this lane.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `.aw/system/managed-sections.json` `AGENTS.md#aw:*` | Both section records are stale while disk equals the generator. | `parse_aw_block(AGENTS.md)`: pointer `bc256612`, reporting `46970f75`; `agents_managed_sections("aw")`: same; recorded: pointer `0fbbebcf`, reporting `2ab6fbfb`. `.gitignore#aw:untracked` is consistent (`137d080a` both). |
| F-2 | HIGH | symptom | A generator change does not land against the live manifest, and does land once the record is reconciled. | in-memory probe appending a line to the pointer section: `stale record: False 1` (not applied, one warning); after one in-memory `merge_aw_block` with the current generator: `after reconcile: True 0`. |
| F-3 | HIGH | root cause (history) | Joint commits edit generator and `AGENTS.md` without re-recording. Pointer: `15df1952f` left record == disk `0fbbebcf`; `74e77c5c4` / `64ccf6758` / `37d37ee4e` changed the on-disk pointer (`3c9852d5`, `81286a94`, `bc256612`) with the record frozen at `0fbbebcf`. Reporting: `37d37ee4e` and `7591a72cf` changed it (`81640865`, `46970f75`) with the record frozen at `2ab6fbfb`. | per-commit `git show <c>:AGENTS.md` / `git show <c>:.aw/system/managed-sections.json` hash table; `git show --stat 7591a72cf` touches `AGENTS.md` and `engine.py` but not the manifest. |
| F-4 | INFO | `engine._apply_section_consent` | The installer logic is correct; no engine change is needed. | `tests/test_section_consent.py`: `12 passed`; the live in-memory `merge_aw_block` with the current generator re-records both keys (diff of a saved temp copy moved exactly the two `sha256` lines). |
| F-5 | MED | `b4bvas` deferred row | `b4bvas` declined the equality guard on the premise "a joint generator-plus-AGENTS.md edit self-heals" on the next install; in this repo nobody runs the installer (`er11a0` E-07 regenerated by script instead, citing measured side effects), so the premise is false here. | `b4bvas` `## Deferred / out of scope`, second row; `er11a0` E-07 text. |
| F-6 | INFO | `engine.update_agents_pointer` | Unsuitable as the reconcile path in this repo: it would append a block to `GEMINI.md`. | dry run: `'GEMINI.md': 'would be updated (appended pointer to existing GEMINI.md) [dry-run]'`. |

## Proposed changes (ordered, validatable)

1. E-01: failing-first live guard plus synthesized tool tests.
2. E-02: `tools/regen_agents_block.py` reusing `merge_aw_block` for both the rewrite and the recording.
3. E-03: reconcile this repo with the tool.
4. E-04: CONTRIBUTING, tools README, DECISIONS.
5. E-05: targeted and bare suites.

## Deferred / out of scope (with reason)

- Appending the managed block to `GEMINI.md` (it has none; the full installer would add one).
  - Carrier-Declined: Whether this repo's `GEMINI.md` should carry the managed block is a separate content decision, unrelated to the stale-record defect; the tool deliberately leaves it untouched.
- Making the full `aw install .` safe to run in this checkout (its broad file sync and raw self-commit, `b4bvas` F-6).
  - Carrier-Declined: Already recorded as an observation in executed `b4bvas` and `er11a0`; the tool removes this repo's need to run it for the managed block, which is all `q3ogs0` requires.
- A first-class `aw` CLI verb for section reconciliation in managed repos.
  - Carrier-Declined: Managed target repos self-heal through the normal install (`b4bvas` case 1); the defect is specific to the framework's own checkout, where a repo-local tool suffices without a new command surface.

## Scope check

- Over-scope: none. `AGENTS.md` is declared because the tool rewrites its managed region if a generator change lands before execution; otherwise it is declared-but-unmodified and acknowledged at finalize.
- Under-scope: none. No product code changes; target repos are unaffected.

## Required tests / validation

- `python3 -m pytest tests/test_agents_section_records.py -o addopts="" -q` failing first (E-01), then passing (E-02 for the synthesized cases, E-03 for the live guard).
- Mutation check of the guard: in a `tempfile` copy of the live manifest, restore one stale hash and show case (a)'s helper reports the failure naming the key (the live files are not touched).
- `python3 -m tools.regen_agents_block --check` exit 1 before E-03 and exit 0 after.
- `tests/test_section_consent.py`, `tests/test_agents_block_target_neutral.py`, `tests/test_askme_command_delivery.py` green; bare `python3 -m pytest` summary pasted.

## Spec / documentation sync

- No `.spec.md` governs section consent or this repo's managed-block regeneration (policy of record is `DECISIONS.md` D104 and D155 plus `.aw/system/README.md` `## Managed sections`, per `b4bvas` Step 0). No spec is amended.
- `CONTRIBUTING.md`, `tools/README.md` and a new `DECISIONS.md` entry are updated (E-04). `.aw/system/README.md` is unchanged: it describes installer behavior in target repos, which this plan does not alter.

## Open questions

### OQ-01: Should the live guard run in the core tier (blocking every lane's merge gate) or be deselected like `livecorpus`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Core. P16 ("When tests depend on the live checkout or environment") prefers a marker deselect only for blast-radius isolation, where a red test would block unrelated lanes. Here the test can go red only through a change to the generator or to `AGENTS.md`'s managed region, which is exactly the lane that must fix it, and its message names the one-command fix; once E-03 lands main is green, so it cannot block an unrelated lane. A deselected guard would run only at `make test-all`, after the stale record had already merged, which is how `krwl3t` recurred. A maintainer preferring `livecorpus` can say so at review.
- Carrier-Declined: Resolved from repository evidence with no residual work.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest tests/test_agents_section_records.py -o addopts="" -q` run BEFORE E-02, listing the failing test names: the live-guard case must fail with the case-3 warning naming `AGENTS.md#aw:pointer` and/or `AGENTS.md#aw:reporting`, and the synthesized cases must fail on the missing `tools.regen_agents_block` import.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the same command after E-02 showing the synthesized cases passing and only the live guard still failing; paste `grep -n "update_agents_pointer\|hash_content\|\.record(" tools/regen_agents_block.py` returning nothing (the tool neither mirrors native files nor writes a hash itself); paste the guard mutation check (tempfile manifest copy with one hash restored to a stale value) showing the guard's helper reports that key.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `--check` output and exit code before (1, naming both keys) and after (0); paste `git diff -- AGENTS.md .aw/system/managed-sections.json` from before the commit showing only the two `AGENTS.md#aw:*` `sha256` lines moved (re-derive the live hashes; the property is that each recorded hash equals the on-disk body hash and no other key moved); paste the live-guard test now passing; paste the `aw commit` output.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the diffs of `CONTRIBUTING.md`, `tools/README.md`, `DECISIONS.md`; paste the highest decision number re-derived at execution and the number used; paste `git diff -- CONTRIBUTING.md tools/README.md | grep "^+" | grep -nP "[\x{2013}\x{2014}]"` returning nothing (these are contributor-facing docs).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the summary lines of the two targeted runs and of bare `python3 -m pytest`, each showing 0 failed; any pre-existing failure must be named with its tracking backlog id and shown failing on main without this plan's changes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
- Right-sizing: `aw ipd lint` raises advisory `IPD-Z602` on E-04 (three files). Considered and declined: E-04 is one concern (document that the tool owns the managed block), documentation only, one `V-*` verifies all three edits together; splitting would create three items that must say the same thing.

This plan is `to-review` and requires explicit human approval before execution. OQ-01 is resolved with a stated default and does not block.

WHAT A HUMAN IS APPROVING: a repo-local developer tool that owns this checkout's managed `AGENTS.md` region and its recorded hashes, a core-tier test that fails any change leaving those hashes stale, and a one-time reconciliation of `.aw/system/managed-sections.json`. No shipped code changes; managed target repos are unaffected.

ORDERING: E-01 is failing-first; run it against the unmodified tree and record the failures before writing the tool. The live guard passes only after E-03, so a live-guard failure between E-02 and E-03 is expected.

STOP CONDITIONS: (1) E-03 moves any manifest key other than `AGENTS.md#aw:pointer` / `AGENTS.md#aw:reporting`, or changes `AGENTS.md` outside the `aw:block` markers; (2) E-01's live guard already passes against the unmodified tree, meaning someone reconciled the manifest and this plan's measurements must be re-derived; (3) the full `aw install .` is reached for any reason (it self-commits a broad sync with raw `git commit`, `b4bvas` F-6).

NEVER HAND-EDIT `AGENTS.md` OR `.aw/system/managed-sections.json`; E-03 goes through the tool, which records through `engine.merge_aw_block`.

SCOPE FENCE (a DECLARATION, not a stop): the declared paths are exactly `- Scope-Paths:`. Make whatever edit the work needs, then JUSTIFY it: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.

COMMITS: only declared paths via `aw commit l5t4vx -- <paths>`, never `git add -A`, never push; verify `git diff --cached --name-only` before each commit. Paste ACTUAL runner output; run the suite BARE.

The terminal lifecycle move is finalized by the runner in a managed lane, or by the executor with `aw ipd finalize` in an unmanaged run, only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. Backlog `q3ogs0` closes through the `- From-Backlog:` handoff (this plan carries `- From-Backlog: q3ogs0` and `- Blocks-Release: next`).
