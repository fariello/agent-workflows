# IPD: Make research index check catch order, kind and model mismatches between filename and front matter

- Date: 2026-10-06
- Kind: child
- Concern: Defect D10 (check half) of research report `l6cbbb`, present at HEAD `474b037a9`. `research_index` reports `name-frontmatter-mismatch` only when front matter `id` differs from the filename id6 or `set` differs from the filename set id. A research file whose filename says `NN=01` and kind `research-report` but whose front matter says `order: 05` and `kind: findings` passes: in a scratch target both probes printed "index --check: clean". The filename grammar (`research_contract.parse_name`: `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md`) carries order, kind and optional model, so the check can compare all three. The rename half of D10 (renames not updating front matter) is already fixed at HEAD by `ax8eg1` (commit `e21ba4378`) and is not in scope.
- Scope: IN: extend the name-versus-front-matter comparison in `research_index` to `order` (compared as integers so `1` and `01` agree), `kind`, and `model` (only when either side carries one; absent on both is fine; present on one side only is a mismatch); one drift line per field naming both values; tests. OUT: the rename path (fixed by `ax8eg1`); adding new front-matter fields; changing the drift code name (`name-frontmatter-mismatch` is reused so existing consumers keep working).
- Scope-Paths: agent_workflows/research_index.py, tests/test_research_index_name_fm_mismatch.py
- Item-Dependencies: none
- Status: to-review
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: medium
- Set: instbugs
- Order: 8
- Highest E allocated: 04
- Author: antigravity/claude-opus-5.5
- Id: okw4ke

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 08 of Set `instbugs` after probing `aw research index --check` in a scratch target with deliberately mismatched `order` and `kind` front matter (both reported clean) and reading the comparison in `research_index`.

## Goal

`aw research index --check` fails whenever a research file's filename and front matter disagree on any identity facet the filename carries (id, set, order, kind, model), so a hand-edited or mis-adopted file cannot hide behind a clean check.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: in a temp repo with an installed `.aw` layout, create a research file with `aw research new --apply`, then edit its front matter to `order: 05`, then separately to `kind: findings`, then add `model: gpt56` to a filename without a model facet; run `aw research index --check` after each and paste the output. STOP and report if any is already flagged.
  - Depends on: none
  - Expected outcome: three "clean" results pasted with the HEAD sha.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 In `research_index`, next to the existing `id` and `set` comparisons that emit `name-frontmatter-mismatch`, add comparisons for `order` (integer compare of front matter `order` against `parsed.order`), `kind` (against `parsed.kind`) and `model` (against `parsed.model`, normalizing absent/empty to none on both sides), each emitting one drift line in the same style, e.g. "order 5 != name 01".
  - Depends on: E-01
  - Expected outcome: each E-01 probe now produces exactly one `name-frontmatter-mismatch` line naming the field and both values, and `--check` exits non-zero.
  - Execution state: pending

- [ ] E-03 Run `aw research index --check` on this repository's own `.aw/records/research/` tree and on a fresh install; any newly surfaced real mismatches in this repository are listed in the plan's evidence and fixed in their front matter (front matter follows the filename, which is the canonical identity), not suppressed.
  - Depends on: E-02
  - Expected outcome: this repository and a fresh target both check clean after the corrections, with each correction listed.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_research_index_name_fm_mismatch.py`: build a research tree in a temp dir through `aw research new --apply`, then for each of order, kind, model-present-on-one-side, assert `aw research index --check` exits non-zero and its output names the field; assert a consistent file (including `order: 1` against `NN=01`) checks clean. Prove the order case can fail by removing the order comparison and pasting the failure.
  - Depends on: E-03
  - Expected outcome: the new tests pass; the mutation fails; assertions are on CLI exit code and output only.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `research_contract.parse_name` returns a `ResearchName` carrying `set_id`, `order`, `id6`, `slug`, optional `model`, and `kind`; the comparison reuses it.
- Drift is reported as `Drift(rel, code, message)` and surfaced by `aw research index --check`; consumers key on the code, so the existing `name-frontmatter-mismatch` code is reused.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Only id and set are compared. | `research_index` block commented "# name-vs-frontmatter consistency" with `if fm.get("id") != parsed.id6:` and `if fm.get("set") != parsed.set_id:` and nothing else |
| F-02 | Mismatched order and kind pass. | scratch probe: front matter `order: 05` and, separately, `kind: findings` on a `NN=01` `.research-report.md` file; both printed "index --check: clean" |
| F-03 | The rename half is fixed. | commit `e21ba4378` (`ax8eg1`) |

## Proposed changes (ordered, validatable)

1. Add order, kind and model comparisons (E-02).
2. Correct any real mismatches the stronger check surfaces (E-03).
3. Behavior tests with mutation proof (E-04).

## Deferred / out of scope (with reason)

- The whole-Set regression asserting `index --check` is clean after the composed research verbs.
  - Carrier: kck7a5

## Scope check

- Over-scope: none.
- Under-scope: none; `date` and `slug` are not front-matter identity fields today, so there is nothing to compare.

## Required tests / validation

- `tests/test_research_index_name_fm_mismatch.py` (E-04) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- N/A: the artifact-organization spec already makes the filename the identity; this enforces it.

## Open questions

### OQ-01: When filename and front matter disagree, which one wins?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: the filename. Every `aw` verb resolves research by the filename grammar, and `aw rename`/`aw research mv` rewrite front matter to follow the name (`ax8eg1`); the check reports, and corrections edit front matter.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the three pre-edit "clean" outputs with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the same three probes post-edit, each showing its `name-frontmatter-mismatch` line and the non-zero exit status.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE `aw research index --check` on this repository and on a fresh target (clean), plus the list of corrected files if any.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one comparison block, one test file.

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit okw4ke -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed okw4ke`.
