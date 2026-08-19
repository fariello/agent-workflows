# IPD: attention board shows identity stem by default, --long for full path

- Date: 2026-08-19
- Kind: child
- Concern: The awdoctor-01 board only folds a shared directory prefix into the header when EVERY item in a class group lives under one directory. In a mixed group (backlog + plans + specs + research + actions all in `ready`) the common prefix is empty, so items show their FULL repo-relative path - long and hard to scan. A tree-independent compact form is better.
- Scope: `agent_workflows/attention.py` render_board + a new `--long` flag on the attention verb; tests. No change to the machine/agent/JSON output, the scan, or the contract.
- Status: approved
- Set: awdoctorfix
- Order: 2
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 2pyjga
- Approval: maintainer (requested the stem-by-default/--long board change directly), 2026-08-19

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - the awdoctor-01 prefix-folding leaves full paths in mixed-tree class groups; switch the default human line to the compact identity stem, with --long for the full path.
- 2026-08-19 reviewed (opencode): self-review - verified render_board single call site (738), --long free on the attention parser, _CLUSTERED_RE grammar, plain/JSON-unchanged invariant, and the awdoctor-01 compact-test update.
- 2026-08-19 approved (opencode, on maintainer instruction): maintainer directly requested stem-by-default + --long.

## Goal

Make the colored human attention board show a COMPACT identity stem `YYYYMMDD-<setid>-NN-<id6>` per item by default (tree-independent, always short), and add `--long` to restore the full repo-relative path. This replaces the awdoctor-01 common-prefix folding (which failed on mixed-tree groups) with a form that is always compact.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: the stem extractor

- [ ] E-01 In `agent_workflows/attention.py`, add a helper `_identity_stem(path: str) -> str` that returns the compact identity of a board line's file: parse the BASENAME against the clustering grammar `^(\d{8})-(<setid>)-(\d{2})-([0-9a-z]{6})` and return `YYYYMMDD-<setid>-NN-<id6>` when it matches; otherwise fall back to the basename with a trailing `.md`/`.<type>.md` facet stripped (so actions like `setup-repo-v1.md` -> `setup-repo-v1`, research `*.model.kind.md` -> its stem). Pure, deterministic, no imports beyond `re`.
  - Depends on: none
  - Expected outcome: `_identity_stem(".aw/records/backlog/open/20260815-attnview-followups-01-mc5xts-attnview-deferred-followups.backlog.md") == "20260815-attnview-followups-01-mc5xts"`; `_identity_stem("aw-state/actions/open/setup-repo-v1.md") == "setup-repo-v1"`.
  - Execution state: pending

### Task group 2: wire --long + render the stem

- [ ] E-02 Add a `--long` flag to the attention parser (`agent_workflows/cli.py`, the `p_attention` block near cli.py:1429, `dest="long"`, `action="store_true"`, help "Show the full repo-relative path instead of the compact identity stem."). Give `render_board` (attention.py:563) a `long: bool = False` parameter and pass `long=getattr(args, "long", False)` at the single call site (attention.py:738). In the COLORED per-item branch, REPLACE the awdoctor-01 common-prefix folding: when `long` is False, `path_txt = _identity_stem(it.path)`; when `long` is True, `path_txt = _colorize_tree_segment(term, it.path, it.tree)` (the full path, tree-colored). Drop the group-prefix header suffix in the non-long (default) view (the stem is self-identifying); keep the class header otherwise. The plain/machine branch (`- [tree] path (status)`) and JSON are UNCHANGED.
  - Depends on: E-01
  - Expected outcome: `aw att` (colored) shows `- <markers> 20260815-attnview-followups-01-mc5xts (open) [P:_]` with NO directory; `aw att --long` shows the full `.aw/records/backlog/open/...` path; `--format json` / piped / `--agent` output is byte-for-byte unchanged.
  - Execution state: pending

### Task group 3: tests

- [ ] E-03 Add `tests/test_attention_stem.py` (`AttentionStemTests`) building `List[attention.Item]` in code: (a) `_identity_stem` returns the grammar stem for a clustered name and the facet-stripped basename for a non-clustered one; (b) the default colored board shows the stem and NOT the directory prefix for a mixed-tree group; (c) `render_board(..., long=True)` shows the full path; (d) the plain board is unchanged (still `- [tree] <full path> (status)`). Run the FULL serial suite and paste the tail. Update `tests/test_attention_compact.py` (awdoctor-01) whose assertions expect the folded-prefix-and-bare-name form: its default-view expectations become the stem form (or assert under `--long` for the full path).
  - Depends on: E-01,E-02
  - Expected outcome: the new module passes; test_attention_compact updated to the stem default; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The clustering grammar is `YYYYMMDD-<setid>-NN-<id6>-<slug>[.<type>].md` (plans_refs `_CLUSTERED_RE`). The board's compact identity is the first four fields.
- `render_board` has ONE call site (attention.py:738); `run` serves both `aw attention` and `aw todo` (todo aliases attention), so one flag wiring covers both.
- The colored HUMAN view is the only surface that changes; the plain (`- [tree] path (status)`) machine contract and JSON stay stable.

## Findings

awdoctor-01's `_common_dir_prefix` folding is empty for a mixed-tree group, so full paths leak onto the board. The identity stem is tree-independent and always compact; `--long` restores the full path for the rare case a user needs it.

## Proposed changes (ordered, validatable)

1. `_identity_stem` helper (grammar match + facet-stripped fallback).
2. `--long` flag + `render_board(long=)`; default renders the stem, `--long` the full path; retire the prefix-fold in the default view.
3. Tests + update the awdoctor-01 compact test to the stem default.

## Deferred / out of scope (with reason)

- The `?` unknown-age marker on items with no parseable last-activity date is a separate cosmetic concern (OQ-01), not this IPD.
- Sorting by priority (awdoctorfix-01 OQ-01) remains deferred.

## Scope check

- Over-scope: none (attention.py + its tests + one cli flag).
- Under-scope: does not change the `?` age marker (OQ-01).

## Required tests / validation

`tests/test_attention_stem.py` + updated `tests/test_attention_compact.py`; full serial suite green.

## Spec / documentation sync

N/A: no spec governs the board's cosmetic line form; `--long` is self-documenting via help.

## Open questions

### OQ-01: Should the `?` unknown-age marker be suppressed for trees that have no history concept?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Deferred. Some items (research at intake, seeded actions) legitimately have no parseable last-activity date; whether to show `?` or blank for them is a separate cosmetic decision, not required for the stem change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `_identity_stem` returns `20260815-attnview-followups-01-mc5xts` for the clustered backlog name and `setup-repo-v1` for the action file; shown by the new test.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: with FORCE_COLOR, `aw att` shows the stem and no directory prefix for a mixed-tree group; `aw att --long` shows the full path; `--format json` + piped + `--agent` output unchanged. Paste the live board snippets.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest tests/test_attention_stem.py tests/test_attention_compact.py -p no:xdist -q` green; full serial suite `python3 -m pytest -p no:xdist` tail pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files changed by this plan, path-scoped, never push. Run the full serial suite and paste the actual runner output as V evidence. On completion, lint `--phase pre-transition` while still approved, then flip Status to executed, add an executed workflow-history line, `git mv` to `.aw/records/plans/executed/`, and lint `--phase post-transition`. Do not mark executed until every V item is verified with concrete evidence.
