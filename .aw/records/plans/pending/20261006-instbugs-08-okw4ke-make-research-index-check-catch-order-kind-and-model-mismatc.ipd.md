# IPD: Make research index check catch order, kind and model mismatches between filename and front matter

- Date: 2026-10-06
- Kind: child
- Concern: Defect D10 (check half) of research report `l6cbbb`, present at HEAD `474b037a9`. `research_index` reports `name-frontmatter-mismatch` only when front matter `id` differs from the filename id6 or `set` differs from the filename set id. A research file whose filename says `NN=01` and kind `research-report` but whose front matter says `order: 05` and `kind: findings` passes: in a scratch target both probes printed "index --check: clean". The filename grammar (`research_contract.parse_name`: `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md`) carries order, kind and optional model, so the check can compare all three. The rename half of D10 (renames not updating front matter) is already fixed at HEAD by `ax8eg1` (commit `e21ba4378`) and is not in scope.
- Scope: IN: extend the name-versus-front-matter comparison in `research_index._doc_entry` to `order` (plain string compare: `validate_frontmatter` already rejects any `order` that is not a two-digit `NN` string and returns before the comparison, so both sides are canonical `NN`), `kind` (front matter normalized through `research_contract.normalize_kind` before comparing, since `parse_name` already normalizes the filename side), and `model` (front matter normalized through `research_contract.normalize_model`; compared ONLY when the filename carries a model facet, because spec `20260730-2152-01` Section 4.4 makes the facet optional in the name and always present in front matter, so a front-matter-only model is legal); one drift line per field naming both values; tests. OUT: the rename path (fixed by `ax8eg1`); adding new front-matter fields; changing the drift code name (`name-frontmatter-mismatch` is reused so existing consumers keep working).
- Scope-Paths: agent_workflows/research_index.py, tests/test_research_index_name_fm_mismatch.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: medium
- Set: instbugs
- Order: 8
- Highest E allocated: 04
- Author: antigravity/claude-opus-5.5
- Id: okw4ke
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Reviewed at lane HEAD `5d7909cc6`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Reproduced D10's check half in a scratch `private-target` install (F-04) and applied the proposed rules to this repo's 128 valid research records (F-05, 0 hits). Fixed: `order: 1` cannot reach the comparison because `validate_frontmatter` rejects it first, so the integer compare and the `order: 1` clean test were unreachable (PR-001); model-on-one-side rule contradicted spec Section 4.4, which makes a front-matter-only model legal; now compared only when the name carries the facet (PR-002); kind and model front matter normalized like `parse_name` so legacy aliases are not false mismatches (PR-003); E-03 demanded a clean `--check` on this repo, which exits 1 for unrelated drift; bar narrowed to the `name-frontmatter-mismatch` subset (PR-004); E-01/V-01 probes made concrete and reproducible, with the model-name case added (PR-005); `- Blocks-Release: next` per the live-bug rule (PR-006); gate gains honesty rule, scope fence, temp HOME, conditional finalize ownership and replaces `aw ipd set executed` (PR-007). `aw check research`/`all` not reporting this drift class recorded in Scope check and reported to the maintainer.
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 08 of Set `instbugs` after probing `aw research index --check` in a scratch target with deliberately mismatched `order` and `kind` front matter (both reported clean) and reading the comparison in `research_index`.

## Goal

`aw research index --check` fails whenever a research file's filename and front matter disagree on any identity facet the filename carries (id, set, order, kind, model), so a hand-edited or mis-adopted file cannot hide behind a clean check.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: in a temp git repo installed with `AW_NO_REEXEC=1 HOME=<tmp> aw install . -y --preset private-target`, create two research files with `aw research new --set prb --kind research-report --apply` (one plain, one with `--model gpt56`, which puts the facet in the name) and run `aw research index` once. Then, one probe at a time and restoring the file after each: (a) plain file front matter `order: 01` -> `order: 05`; (b) plain file `kind: research-report` -> `kind: findings`; (c) model file `model: gpt56` -> `model: sonnet5`; (d) model file `model: gpt56` -> `model:` (empty). Run `aw research index --check` after each and paste output and exit status. If any probe is already flagged `name-frontmatter-mismatch`, record that and drop that field from E-02.
  - Depends on: none
  - Expected outcome: four "clean" exit-0 results pasted with the HEAD sha (reproduced at review: (a), (b), (d) and a `model: reconciliation` swap all exited 0 with no mismatch line).
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 In `research_index._doc_entry`, directly after the existing `id` and `set` comparisons (the block commented "# name-vs-frontmatter consistency"), add three comparisons emitting `name-frontmatter-mismatch` in the same message style: `order` (`fm.get("order") != parsed.order`, e.g. "order 05 != name 01"); `kind` (`normalize_kind(fm kind).value != parsed.kind`, so a legacy alias such as `kind: research` on a `.research-report.md` file is NOT a mismatch); `model`, only when `parsed.model` is not None (`normalize_model(fm model, repo_root=repo_root).value` against `parsed.model`, with an empty or absent front matter `model` reported as e.g. "model (empty) != name gpt56"). Do NOT flag a front matter `model` on a filename with no model facet (spec Section 4.4).
  - Depends on: E-01
  - Expected outcome: each E-01 probe now produces exactly one `name-frontmatter-mismatch` line naming the field and both values, and `--check` exits non-zero; a front-matter-only model and a normalized kind alias still check clean.
  - Execution state: pending

- [ ] E-03 Run `aw research index --check` on this repository's own research tree and on a fresh install. This repository's check is NOT clean for unrelated reasons (at review HEAD `5d7909cc6` it exits 1 with `dangling-citation`, `adopted-without-consumer`, `stale-state-to-promote` and one `frontmatter-invalid` line, none in scope), so the bar here is the `name-frontmatter-mismatch` subset: re-derive it at execution by filtering the output for that code. Any such line is a real mismatch: list it and correct the file's front matter to follow the filename (the canonical identity, OQ-01), not suppress it. A correction edits a research file outside `- Scope-Paths:`; justify it at finalize with `--scope-reason`.
  - Depends on: E-02
  - Expected outcome: zero `name-frontmatter-mismatch` lines in this repository after any corrections (each correction listed; at review the new rules applied by hand to the 128 valid records found none), and the fresh target prints "index --check: clean".
  - Execution state: pending

### Task group 3: pin it

- [ ] E-04 Add `tests/test_research_index_name_fm_mismatch.py`: build a research tree in a temp git repo through `aw research new --apply` driven as a subprocess with `HOME`/`XDG_CONFIG_HOME` isolated to the temp dir (precedent: `tests/test_research_date_containment.py` `setUp`). Flagged cases (assert exit non-zero and a `name-frontmatter-mismatch` line naming the field): order `05` on `NN=01`; kind `findings` on `.research-report.md`; model `sonnet5` and model empty on a `.gpt56.` name. Clean cases (assert exit 0 and no `name-frontmatter-mismatch`): the untouched files; `kind: research` on `.research-report.md`; `model: gpt56` on a name without a model facet. Prove the order case can fail by removing the order comparison and pasting the failure, then restore it.
  - Depends on: E-03
  - Expected outcome: the new tests pass; the mutation fails; assertions are on CLI exit code and output only (P16).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `research_contract.parse_name` returns a `ResearchName` carrying `set_id`, `order`, `id6`, `slug`, optional `model`, and `kind`; `kind` and `model` are already normalized there (`normalize_kind`, `normalize_model`), so the front matter side must be normalized the same way before comparing.
- `research_contract.validate_frontmatter` runs first in `_doc_entry` and returns early on any error; it already requires `order` to match `\A\d{2}\Z` ("order must be a two-digit string NN"), so `order: 1` is `frontmatter-invalid` today and never reaches the comparison.
- Spec `20260730-2152-01-agents-artifact-organization` Section 4.4: "`<model>` is present ONLY when authorship disambiguation matters, and always ALSO recorded in frontmatter (`model:`)". A front matter model without a name facet is legal.
- Drift is reported as `Drift(rel, code, message)` and surfaced by `aw research index --check`; consumers key on the code, so the existing `name-frontmatter-mismatch` code is reused.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Only id and set are compared. | `research_index` block commented "# name-vs-frontmatter consistency" with `if fm.get("id") != parsed.id6:` and `if fm.get("set") != parsed.set_id:` and nothing else |
| F-02 | Mismatched order and kind pass. | scratch probe: front matter `order: 05` and, separately, `kind: findings` on a `NN=01` `.research-report.md` file; both printed "index --check: clean" |
| F-03 | The rename half is fixed. | commit `e21ba4378` (`ax8eg1`) |
| F-04 | Reproduced at review HEAD `5d7909cc6`. | scratch `private-target` install, `aw research new` x2, `aw research index`: `order: 05`, `kind: findings`, `kind: research`, `model: reconciliation` and empty `model:` on a `.gpt56.` name, and `model: gpt56` on a name without a model facet, all exited 0 with no mismatch line; `order: 1` exited 1 with "frontmatter-invalid: order: order must be a two-digit string NN"; a changed `id` printed "name-frontmatter-mismatch: id zzzzz9 != name fuclk7" |
| F-05 | No live record would be newly flagged. | the proposed order/normalized-kind/name-side-model rules applied through `parse_name`/`parse_frontmatter`/`validate_frontmatter` to this repo's 128 front-matter-valid research records: 0 hits |

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
- Out of scope, observed at review: `aw check research` and `aw check all` do not report `name-frontmatter-mismatch` at all (a changed `id` exited 0 under both), because `check_engine.check_content` runs `research_index.check_drift` only when `include_retired` is set. This plan's goal is `aw research index --check`; the `aw check` surface is reported to the maintainer, not changed here.

## Required tests / validation

- `tests/test_research_index_name_fm_mismatch.py` (E-04) with the mutation proof; narrowed run as `python3 -m pytest -o addopts="" tests/test_research_index_name_fm_mismatch.py`.
- Existing `tests/test_research_index.py` still passes (it pins the id/set half of `name-frontmatter-mismatch`).
- Bare `python3 -m pytest` summary line pasted, before the edit and after.

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
  - Required evidence: PASTE the four pre-edit probe outputs (a)-(d) with exit status and the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the same four probes post-edit, each showing its one `name-frontmatter-mismatch` line naming the field and both values and the non-zero exit status, plus the two clean controls (`kind: research` on `.research-report.md`; `model: gpt56` on a name without a model facet) exiting 0, and the `git diff` of `agent_workflows/research_index.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE `aw research index --check 2>&1 | grep -c name-frontmatter-mismatch` on this repository (0, after any corrections) and the full fresh-target output ("index --check: clean"), plus the list of corrected files and their front matter diffs, or "none".
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the narrowed run of the new test file (all flagged and clean cases passing), the mutation failure output for the order case, the narrowed run of `tests/test_research_index.py`, and the bare `python3 -m pytest` summary line before and after.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one comparison block, one test file.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in order (E-01, E-02, E-03, E-04). Commit only files changed for this plan through `aw commit okw4ke -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output satisfies no item. Run every scratch install and `aw` subprocess with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit (for example an E-03 front matter correction) is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize okw4ke`, never by a hand `git mv`.
