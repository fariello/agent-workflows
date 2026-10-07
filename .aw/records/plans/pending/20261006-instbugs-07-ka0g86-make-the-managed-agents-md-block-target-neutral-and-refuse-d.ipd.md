# IPD: Make the managed AGENTS.md block target-neutral and refuse dangling references in installed agent docs

- Date: 2026-10-06
- Kind: child
- Concern: Defect D07 of research report `l6cbbb`, present at HEAD `474b037a9`. `engine.agents_pointer_prose(target_layout)` emits ONE managed block that is written both into this repository's `AGENTS.md` and into every target's `AGENTS.md` (`engine.update_agents_pointer`). That block carries material that is only true of agent-workflows itself: the "HOW TO RUN THE SUITE: run it BARE, as `python3 -m pytest` (or `make test`)" paragraph and its `pyproject.toml` `addopts` reasoning; mandates to read `RELEASING.md`, `CONTRIBUTING.md` and `GUIDING_PRINCIPLES` P12/P16; a citation of the ipd-structure spec under `.aw/records/specs/` (specs are not installed into targets); and runner guarantees cited "BY SYMBOL in `oc_runipd.py` ... `runner_shared.py`", source files a target does not contain. In the scratch Node target (package.json only) the installed `AGENTS.md` is 125 lines and line 80 instructs agents to run `python3 -m pytest`, which is wrong for that project, and several mandated files do not exist. Nothing detects a managed doc that points at a path the target lacks.
- Scope: IN: split the managed block into target-neutral content (stays in `agents_pointer_prose`) and agent-workflows-only content (moves BELOW `<!-- /aw:block -->` in this repository's own `AGENTS.md`, the repo-local region that already exists and is never installed); rephrase the runner-guarantees paragraph to point at `aw host capabilities` and `aw oc run --help` instead of source symbols; point the IPD contract at the installed `.aw/records/plans/README.md` and `aw ipd --help` instead of an uninstalled spec; replace the hard-coded test command with "run the project's own test command (see `/setup-repo` or the project's docs)"; add a dangling-reference check reported by `aw doctor` and as a post-install advisory that scans the managed block and the installed READMEs for backticked repo-relative paths that do not exist in the target; tests. OUT: the retired `.agents/` strings in installed READMEs and install messages (Order 06 `jbnkkh`); the inbox README (Order 05 `xzlu9b`, which this plan's check must find present); rewriting the content of the AW-only paragraphs (they move verbatim).
- Scope-Paths: agent_workflows/engine.py, agent_workflows/doctor.py, AGENTS.md, tests/test_agents_block_target_neutral.py
- Item-Dependencies: executed:xzlu9b, executed:jbnkkh
- Status: to-review
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: high
- Set: instbugs
- Order: 7
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: ka0g86

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 07 of Set `instbugs` after reading the 125-line `AGENTS.md` a HEAD (`474b037a9`) install wrote into a package.json-only scratch target, and locating each AW-only paragraph in `engine.agents_pointer_prose`.

## Goal

The managed `AGENTS.md` block an install writes into any target contains only guidance that is true in that target, this repository keeps its own AW-only rules in its repo-local region, and `aw doctor` plus the install report flag any installed agent doc that points at a path the target does not have.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: fresh `.aw`-layout install into a temp git repo containing only `package.json`; paste `wc -l AGENTS.md`, `grep -nE "python3 -m pytest|pyproject|RELEASING.md|CONTRIBUTING.md|GUIDING_PRINCIPLES|oc_runipd.py|runner_shared.py|records/specs/" AGENTS.md`, and for every backticked repo-relative path inside the managed block whether it exists in the target. STOP and report if the block is already target-neutral.
  - Depends on: none
  - Expected outcome: the inventory of AW-only paragraphs and dangling paths pasted with the HEAD sha.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Split `engine.agents_pointer_prose`: move the AW-only paragraphs (suite-running rule, RELEASING/CONTRIBUTING/GUIDING_PRINCIPLES mandates, any source-file symbol citations) out of the function and into this repository's `AGENTS.md` BELOW `<!-- /aw:block -->`, verbatim, under the existing repo-local heading. Regenerate this repository's managed block with the normal install/update path so the managed region and the repo-local region together still say everything they said before.
  - Depends on: E-01
  - Expected outcome: `agents_pointer_prose` output names none of the E-01 AW-only tokens; this repository's `AGENTS.md` still contains every moved paragraph (in the repo-local region).
  - Execution state: pending

- [ ] E-03 Rephrase the target-neutral remainder: the runner-guarantees paragraph points at `aw host capabilities` and `aw oc run --help` rather than `oc_runipd.py`/`runner_shared.py` symbols; the IPD contract points at `.aw/records/plans/README.md` and `aw ipd --help` rather than a spec path; the test-command guidance says to use the project's own test command (discovered by `/setup-repo` or the project's docs). Both layouts (`target_layout` `aw` and `legacy`) get the matching paths.
  - Depends on: E-02
  - Expected outcome: every backticked repo-relative path in the block exists in a fresh target of either layout.
  - Execution state: pending

- [ ] E-04 Add the dangling-reference check: a probe in `agent_workflows/doctor.py` (reported by `aw doctor`, and called once at the end of install as an advisory line) that extracts backticked repo-relative paths from the managed `AGENTS.md` block and from installed READMEs (`.aw/records/**/README.md`, `.aw/inbox/README.md`) and reports each that does not exist. A small, explicit allowlist excludes placeholders (tokens containing `<`), globs (`*`), and directories the tooling creates lazily (named in one constant with a comment per entry).
  - Depends on: E-03
  - Expected outcome: a fresh target reports zero dangling references; a planted missing path is reported with its file and token.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_agents_block_target_neutral.py`: (a) fresh install of each layout into a temp git repo with only `package.json`; assert the installed managed block contains none of `python3 -m pytest`, `pyproject.toml`, `RELEASING.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES`, `oc_runipd.py`, `runner_shared.py`; (b) run `aw doctor --format json` on that target and assert zero dangling-reference findings; (c) append a backticked reference to a nonexistent `docs/missing.md` inside an installed README and assert the check reports exactly that token and file; (d) assert this repository's managed block plus repo-local region still contains the suite-running rule (driving the real render, not reading source). Prove (a) can fail by restoring one moved paragraph into `agents_pointer_prose` and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new tests pass, the mutation fails (a); no test reads production source (all assertions are on installed files and command output).
  - Execution state: pending

## Project conventions discovered (Step 0)

- This repository's `AGENTS.md` already separates a managed block (between `<!-- aw:block -->` and `<!-- /aw:block -->`) from a repo-local region below it that says "THIS SECTION IS REPO-LOCAL AND MUST NOT BE INSTALLED INTO A MANAGED TARGET REPO"; that region is the home for AW-only rules.
- `engine.agents_pointer_prose(target_layout)` and `engine.update_agents_pointer(..., target_layout=...)` already branch on layout; the fix reuses that value.
- `aw doctor` aggregates probes in `doctor.collect_doctor_report`; a new probe follows the `probe_*` pattern there.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The managed block hard-codes this repository's test command. | `engine.agents_pointer_prose` string "HOW TO RUN THE SUITE: run it BARE, as `python3 -m pytest` (or `make test`)."; scratch target `AGENTS.md` line 80 |
| F-02 | The managed block cites source files a target lacks. | `agents_pointer_prose` text "verifiable BY SYMBOL in `oc_runipd.py` or ... in `runner_shared.py`" |
| F-03 | The managed block mandates files a Node target lacks. | scratch target has no `RELEASING.md`, `CONTRIBUTING.md`, `GUIDING_PRINCIPLES.md`, nor `.aw/records/specs/` spec cited for the IPD contract |
| F-04 | Nothing detects dangling references in installed docs. | `doctor.py` probes: `probe_git`, `probe_environment`, `probe_attention`, `probe_artifacts`, `probe_artifact_audit`, `probe_sanitizer`; none scans installed docs for paths |
| F-05 | Order dependency. | the check must pass on a fresh target, which requires the inbox README (Order 05) and the de-staled READMEs (Order 06) to be present first |

## Proposed changes (ordered, validatable)

1. Move AW-only paragraphs to the repo-local region (E-02).
2. Rephrase the neutral remainder (E-03).
3. Dangling-reference probe in doctor and install advisory (E-04).
4. Behavior tests with mutation proof (E-05).

## Deferred / out of scope (with reason)

- Retired `.agents/` strings in installed READMEs and messages are fixed elsewhere.
  - Carrier: jbnkkh
- The inbox README existence is delivered elsewhere.
  - Carrier: xzlu9b
- The whole-Set fresh-install regression that re-runs this check end to end.
  - Carrier: kck7a5

## Scope check

- Over-scope: none.
- Under-scope: the check is advisory at install time (it does not fail an install), because a user's own README edits could legitimately reference paths outside the tool's knowledge; `aw doctor` reports it for follow-up.

## Required tests / validation

- `tests/test_agents_block_target_neutral.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- N/A for specs: no spec states the managed block's contents; this repository's `AGENTS.md` is updated by E-02 (content moved, not changed).

## Open questions

### OQ-01: Should the AW-only paragraphs be deleted from targets or offered as an optional preset?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: removed from targets. They describe this repository's own suite, release process and source files, which no target has; an optional preset would reintroduce dangling references. They remain in force here via the repo-local region.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `wc -l`, grep inventory and dangling-path list with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the E-01 grep re-run on a post-edit fresh target (no hits) and `grep -n "HOW TO RUN THE SUITE" AGENTS.md` in this repository showing the line now sits below `<!-- /aw:block -->`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the rephrased runner, IPD-contract and test-command paragraphs from a post-edit fresh target of each layout.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE `aw doctor` output on a fresh target (zero dangling references) and on the planted-missing-path target (the finding naming file and token), plus the install advisory line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: making the block neutral and adding the check that proves it neutral are one deliverable; the check without the cleanup would fail on every install, and the cleanup without the check would regress silently.

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit ka0g86 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed ka0g86`.
