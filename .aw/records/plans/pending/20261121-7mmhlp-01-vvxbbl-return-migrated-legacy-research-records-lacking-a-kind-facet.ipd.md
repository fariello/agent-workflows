# IPD: Return migrated legacy research records lacking a kind facet from aw find

- Date: 2026-11-21
- Kind: child
- Concern: `agent_workflows/cli.py::_find_type_records` (the `artifact_type == "research"` branch) skips every file for which `agent_workflows/research_contract.py::parse_name(p.name, repo_root=repo_root)` returns `None`. When `aw migrate metadata` mints an `id6` for a legacy research note whose filename has no `.<kind>.md` facet (such as `20260708-survey-notes.md` renamed to `research/20260708-<id6>-01-<id6>-survey-notes.md` in `tests/migration_corpus.py::legacy_agents_layout`), querying `aw find <minted_id6> --agent` resolves the selector (exit 0) and then drops the record in `_find_type_records`, returning `total: 0` with zero items even though `artifact_meta.query` indexes the record with `not st.id_derived`.
- Scope: Update the `artifact_type == "research"` branch of `agent_workflows/cli.py::_find_type_records` to look up `st = state_by_path.get(p.resolve())` before dropping on `parsed is None`, falling back to `artifact_meta.State` (`st.id6`, `st.set_id`, `st.order_nn`) when `st is not None and not st.id_derived`, while still skipping unmigrated id-less research files where `parsed is None` and (`st is None` or `st.id_derived` is True). Add behavioral regression tests in `tests/test_find_filters.py` verifying `aw find <minted_id6> --agent` and `aw find research --agent` return a migrated legacy research record lacking a kind facet while still skipping an unmigrated id-less research file. EXCLUDES: changing `m0001_renames` filename rules and status-less research conversion (`fnabjy` / `s4utmv`).
- Scope-Paths: agent_workflows/cli.py, tests/test_find_filters.py, .aw/records/plans/pending/20261121-7mmhlp-01-vvxbbl-return-migrated-legacy-research-records-lacking-a-kind-facet.ipd.md
- Item-Dependencies: none
- Status: to-review
- Short-Description: Fall back to artifact_meta state in cli._find_type_records when research_contract.parse_name returns None for a migrated research record with a non-derived id6.
- Work-Kind: bug
- Priority: medium
- From-Backlog: 7mmhlp
- Blocks-Release: next
- Set: 7mmhlp
- Order: 1
- Highest E allocated: 02
- Author: antigravity/gemini
- Id: vvxbbl

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-21 to-review (aw set): Authored review-ready child plan graduated from backlog 7mmhlp
- 2026-11-21 draft (antigravity/gemini): created.

## Goal

Make `aw find` return migrated legacy research records that carry a real non-derived `id6` in `artifact_meta.State` even when their filename lacks a research `.<kind>.md` facet, without re-admitting unmigrated id-less prose files.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Research find fallback onto artifact_meta.State

- [ ] E-01 Update the `artifact_type == "research"` loop in `agent_workflows/cli.py::_find_type_records`:
  1. Look up `st = state_by_path.get(p.resolve())` and keep the existing `if st is None or st.id_derived: continue` guard so unmigrated id-less files stay excluded.
  2. Call `parsed, _ = _rc.parse_name(p.name, repo_root=repo_root)`, but do NOT `continue` when `parsed is None` if `st.id6` is non-empty and `not st.id_derived` (a log-backed or explicitly ID-bearing research record). When `parsed is None` and `not st.id6`, `continue`.
  3. Derive `res_id = st.id6 or (parsed.id6 if parsed else "")`, `set_val = st.set_id or (parsed.set_id if parsed else None)`, and `order_val = st.order_nn if st.order_nn is not None else (parsed.order if (parsed and parsed.order is not None) else 0)`.
  - Depends on: none
  - Expected outcome: `aw find <minted_id6>` and `aw find research` emit migrated legacy research records lacking a kind facet using their `artifact_meta.State` metadata while continuing to exclude unmigrated id-less files.
  - Execution state: pending

- [ ] E-02 Add behavioral tests in `tests/test_find_filters.py` exercising a fixture repository containing: (a) a migrated v2 research record at `.aw/records/research/20260708-ab12cd-01-ab12cd-survey-notes.md` (with `meta/ab12cd.jsonl` and no `.<kind>.md` facet), and (b) an unmigrated id-less research prose file `.aw/records/research/20260708-unmigrated-notes.md` without a log or front-matter `id`. Assert via real CLI invocation (`aw find ab12cd --agent` and `aw find research --agent`) that `ab12cd` is returned (`total == 1`, `id6 == "ab12cd"`) and the unmigrated id-less file is not returned. Run `python3 -m pytest -o addopts="" -v tests/test_find_filters.py tests/test_find_agent_stream.py tests/test_find_single_read.py`, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition` on this plan, and `aw sanitize --agent`.
  - Depends on: E-01
  - Expected outcome: All targeted find tests, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition`, and `aw sanitize --agent` pass with zero regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/cli.py::_find_type_records` queries `artifact_meta` once per call (`state_by_path = _query_by_path("research")`) and resolves selectors through `selectors._resolve_selectors_with_kinds` before filtering rows in the `artifact_type == "research"` loop.
- Previously, `if parsed is None: continue` ran BEFORE checking `state_by_path`, discarding any migrated research file whose renamed filename omitted a `.<kind>.md` facet even though `selectors` matched its minted `id6` and `artifact_meta.query` returned its `State`.
- Note on pre-migration parity: unmigrated id-less files have `st.id_derived == True`, so keeping `if st is None or st.id_derived: continue` preserves pre-migration exclusion exactly.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `cli._find_type_records` drops migrated legacy research files lacking a `.<kind>.md` facet before consulting `state_by_path`. | `agent_workflows/cli.py::_find_type_records`; measured during IPD `60mazt` on `legacy_agents_layout`, where `aw find <minted_id6> --agent` exited 0 with `total: 0, emitted: 0`. |

## Proposed changes (ordered, validatable)

1. Check `state_by_path` and fall back to `artifact_meta.State` fields when `research_contract.parse_name` returns `None` for a non-derived research record in `agent_workflows/cli.py::_find_type_records` (`E-01`).
2. Add behavioral tests in `tests/test_find_filters.py` and run all validation gates (`E-02`).

## Deferred / out of scope (with reason)

- Changing `m0001_renames` to invent a synthetic research kind facet on legacy files: not needed once `cli._find_type_records` honors `artifact_meta.State`, and avoids fabricating ungrounded kind metadata.

## Scope check

- Over-scope: none. Only `agent_workflows/cli.py`, `tests/test_find_filters.py`, and this plan are modified.
- Under-scope: none. Preserves all existing filters (`--id`, `--set`, `--topic`, `--status`, `--status-not`) and pre-migration id-less exclusion.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_find_filters.py tests/test_find_agent_stream.py tests/test_find_single_read.py`
- `aw suite` (core tier passes)
- `make typecheck` (0 mypy errors)
- `aw ipd lint --phase pre-transition` on this plan (`outcome: "clean"`)
- `aw sanitize --agent` (`outcome: "clean"`)

## Spec / documentation sync

N/A: brings `aw find research` into compliance with spec `4sd62s` (where `artifact_meta` is the authority for migrated record identity and metadata).

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result (which are reachable by construction), name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff agent_workflows/cli.py` summary showing the `artifact_type == "research"` branch falls back to `artifact_meta.State` when `parsed is None` and `not st.id_derived` while still skipping `st is None or st.id_derived`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste actual output from `python3 -m pytest -o addopts="" -v tests/test_find_filters.py tests/test_find_agent_stream.py tests/test_find_single_read.py`, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition` on this plan, and `aw sanitize --agent`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute after review and approval (`approved` or `auto-approved`). Commit only files changed for this plan through `aw commit vvxbbl -- <paths>` (never `git add -A`, bare `git add`, `git commit -a`, or `--no-verify`; never push). Finalize to `.aw/records/plans/executed/` only via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
