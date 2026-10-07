# IPD: Prove the whole Set with one fresh-install regression over a scratch non-Python target

- Date: 2026-10-06
- Kind: child
- Concern: Set `instbugs` fixes the present-at-HEAD defects of research report `l6cbbb` across ten children, each with its own unit-level tests, but the report's defects were found TOGETHER, by one fresh install into a package.json-only target, and several of them only show up as disagreements BETWEEN children's outputs: the preset's git policy (`gi1w75`), the files actually written (`pfub72`), what the install stages (`gzsfqn`) and what `.aw/.gitignore` ignores; the installed bundle being free of dangling references (`ka0g86` check, over `xzlu9b` and `jbnkkh` content); and the research verbs composing (`zye6k4` numbering, `ic4eg0` mode, `okw4ke` check). Defects D02 and D06 and the fixed halves of D10, D13 and D15 were fixed before this Set and have no pin in it. Nothing in the suite today installs into a non-Python target and checks these outcomes end to end.
- Scope: IN: one regression test module that builds a scratch git repo containing only `package.json`, runs a fresh `aw install` with the private-target preset non-interactively, and asserts every original observation of the report is gone (D01 version consistency, D02, D03, D04, D05, D06, D07, D08, D09, D11, D12, D14, D15, N1, N2), plus the three cross-child checks; a full bare suite run; a user-facing CHANGELOG entry. OUT: re-fixing anything (a failing assertion here sends the defect back to its owning child as a corrective plan); the wheel-build proof of D01 (owned by `whz0oi`'s own test, because building a wheel is too slow for this module); D13 companion files (backlog `bh1cy5`).
- Scope-Paths: tests/test_fresh_target_install_regression.py, CHANGELOG.md
- Item-Dependencies: executed:whz0oi, executed:gzsfqn, executed:ka0g86, executed:okw4ke, executed:ic4eg0, executed:zye6k4
- Status: to-review
- Blocks-Release: f33nrj
- Work-Kind: chore
- Priority: high
- Set: instbugs
- Order: 11
- Highest E allocated: 04
- Author: antigravity/claude-opus-5.5
- Id: kck7a5

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 11 of Set `instbugs`, the whole-Set proof, from the orchestrator's Findings triage and its cross-IPD validation list.

## Goal

One test re-creates the report's situation (a fresh install into a non-Python repo) and proves every defect it found is gone and stays gone, including the ones fixed before this Set, and the full suite passes with the Set merged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [ ] E-01 Record the baseline at the execution HEAD: confirm with `aw find plans <id6>` that all six dependencies are under `executed/`; run the bare suite `python3 -m pytest` and paste the summary line; run one manual scratch install (package.json-only temp git repo, `aw install . --preset private-target -y --no-interactive`) and paste `git status --short --ignored`, `stat -c '%a %n'` of any record created, and the install log tail. STOP and report if any dependency is not executed.
  - Depends on: none
  - Expected outcome: the baseline suite summary and the manual install observations pasted with the HEAD sha.
  - Execution state: pending

### Task group 2: the regression module

- [ ] E-02 Add `tests/test_fresh_target_install_regression.py`, install-level part. One module-scoped fixture performs the scratch install once (package.json-only temp git repo, private-target preset, `-y --no-interactive`, `AW_NO_REEXEC=1`, output captured); tests then assert on the target and the captured output:
  - D01/N2: the version in the durable install snapshot equals `aw --version` from the same environment, and the snapshot holds no absolute path from the test machine.
  - D02: `git check-ignore` succeeds for `.aw/state/` and `.aw/config/local.json`.
  - D03/N1: `git status --short` after the install shows no untracked `.aw/` path in a tracked class; no "run scratch ... NOT ignored" line appears while `.aw/workflow-artifacts/` is in fact ignored.
  - D04: every path the consent plan printed exists after the install.
  - D05: no install state record exists both at the `.aw/state/` root and under `.aw/state/durable/`.
  - D06: no root `workflow-artifacts/` directory.
  - D07: the managed AGENTS.md block names no AW-only token (`python3 -m pytest`, `RELEASING.md`, `oc_runipd.py`).
  - D08/D09: no `.agents/(plans|prompts|comms|docs|workflows)` string in the output, `.gitignore`, `.aw/.gitignore` or `.aw/records/`.
  - D14: `.aw/inbox/README.md` exists and is tracked or staged while other inbox content is ignored.
  - D15: for each physical class, the preset policy recorded in `project.json`, presence on disk, the staged set and `.aw/.gitignore` agree (the TRACKING TRUTH TABLE).
  - Dangling references: `aw doctor --format json` reports zero.
  - Depends on: E-01
  - Expected outcome: every assertion passes; each assertion's message names the defect id so a regression points at its owner.
  - Execution state: pending

- [ ] E-03 Same module, research-composition part, in the same installed target under a forced `umask 022`: `aw research new --kind research-report --set newset --slug a --apply` and `aw adopt --apply` of a dropped inbox file into another new set; assert both names are `01` (D12), both modes are 644 (D11), and `aw research index --check` exits 0; then hand-edit one file's `order:` and assert `--check` now fails (D10). Measure the whole module's wall time; if it exceeds 15 s, mark it `slow` and record the measurement and the `make test-all` path in the evidence, so the default suite stays fast.
  - Depends on: E-02
  - Expected outcome: all composition assertions pass; the module's wall time and marker decision recorded.
  - Execution state: pending

### Task group 3: close

- [ ] E-04 Prove the module can fail (temporarily revert one child's fix in a scratch branch, for example restore the 0600 mode in `artifact_core.atomic_write`, and paste the defect-named failure, then discard the scratch change); add a CHANGELOG.md entry under the pending release describing the fixed install and research problems in user terms with no em or en dashes; run the bare suite `python3 -m pytest` and paste its summary against the E-01 baseline.
  - Depends on: E-03
  - Expected outcome: the mutation fails with a defect-named message; the CHANGELOG entry exists; the full suite passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `pyproject.toml` `addopts` deselects `slow` and `livecorpus` by default; `make test-all` runs everything. A slow end-to-end install test belongs under `slow` so the default suite stays fast.
- `aw` re-execs into a checkout's package when run inside a checkout; tests that drive an installed target set `AW_NO_REEXEC=1`.
- The suite already installs into temp git repos in other tests; the fixture follows that pattern and installs once per module.
- User-facing prose (CHANGELOG) carries no em or en dashes.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16): every assertion here is on installed files, git state, file modes and CLI output.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The defects were found by one composed install, not per unit. | research report `l6cbbb` (one install into a Node target); orchestrator `i99ykd` Findings table |
| F-02 | D02, D06 and the fixed halves of D10, D13, D15 have no pin in this Set. | orchestrator `i99ykd` Deferred: "`kck7a5`'s regression test pins the D02 and D06 outcomes so they cannot regress" |
| F-03 | Cross-child agreement is only observable end to end. | orchestrator `i99ykd` cross-IPD validation: "THE TRACKING TRUTH TABLE AGREES END TO END ... Performed by `kck7a5` E-02"; "THE RESEARCH VERBS COMPOSE ... Performed by `kck7a5` E-03" |
| F-04 | Wheel builds are too slow for this module. | `whz0oi` owns the wheel-build proof of D01; this module checks version consistency in the running environment |

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. Install-level regression assertions (E-02).
3. Research-composition assertions and the marker decision (E-03).
4. Mutation proof, CHANGELOG, full suite (E-04).

## Deferred / out of scope (with reason)

- D13 companion files: a feature, not a defect.
  - Carrier: bh1cy5
- The wheel-build proof of D01.
  - Carrier: whz0oi

## Scope check

- Over-scope: none.
- Under-scope: none; every row of the orchestrator's Findings table has an assertion here or a named carrier.

## Required tests / validation

- `tests/test_fresh_target_install_regression.py` (E-02, E-03) with the mutation proof (E-04).
- Bare `python3 -m pytest` summary line pasted against the E-01 baseline (E-04).

## Spec / documentation sync

- CHANGELOG.md entry (E-04). No spec change: each child carries its own spec sync.

## Open questions

### OQ-01: Should the regression run in the default suite or under `slow`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED by measurement at execution: default suite if the module runs in 15 s or less, `slow` otherwise (E-03 records the number). The maintainer has asked for a fast default suite, so a heavier module must not land in it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the six `aw find plans` lines showing `executed/`, the baseline suite summary line, and the manual install observations with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the narrowed run of the install-level tests (`python3 -m pytest -o addopts="" -m "" tests/test_fresh_target_install_regression.py -k install`) showing each defect-named test passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the narrowed run of the composition tests, the module's measured wall time, and the marker decision.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the defect-named mutation failure, the CHANGELOG entry text, and the bare-suite summary line from `python3 -m pytest` against the E-01 baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one regression module and the Set's closing suite run; it carries no fix of its own.

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit kck7a5 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. If any assertion fails because a child's fix is incomplete, do NOT fix it here: STOP, report the defect id and owning child, and leave a corrective IPD to the maintainer. On completion move the plan to `executed/` with `aw ipd set executed kck7a5`.
