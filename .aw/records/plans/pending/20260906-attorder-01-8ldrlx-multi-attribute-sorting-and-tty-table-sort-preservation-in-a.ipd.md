# IPD: Multi-attribute sorting and TTY table sort preservation in aw attention

- Date: 2026-09-06
- Kind: child
- Concern: `aw attention` (and `aw next`) provides `--order-by/-o`, but in interactive TTY mode `render_table` completely overwrites the user-requested sort with its own hardcoded `visible.sort(key=...)` (`type_word, is_blocking, prio_rank, name, it.path`), rendering flags like `-o priority` a silent no-op in ordinary terminal use. Additionally, `--order-by` currently accepts only a single key from a closed set that lacks several essential artifact attributes (`readiness`, `oqs`, `rqs`, `file`, `ctime`, `mtime`), and cannot express multi-attribute composite sorting (e.g. `-o priority,status,id6`).
- Scope: Fix `render_table()` in `agent_workflows/attention.py` so it honors explicit ordering rather than resetting it with the hardcoded sort; extend `--order-by` (`-o`) in `agent_workflows/cli.py` and `agent_workflows/attention_contract.py` to accept a comma-separated list of attributes, expanding the vocabulary to include `status`, `type`, `blocking`, `priority`, `readiness`, `oqs`, `rqs`, `setid`, `id6`, `file`, `ctime`, and `mtime`; implement multi-attribute stable sorting using reverse-order stable sort passes with the deterministic `(path, id)` tiebreaker; and add unit and CLI tests in `tests/test_next_ordering.py` verifying multi-column sort sequences and TTY table sort preservation.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/cli.py, tests/test_next_ordering.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: attorder
- Order: 1
- Highest E allocated: 04
- Author: Gabriele Fariello <gabriele.fariello@gmail.com>
- Id: 8ldrlx
- Approval: 2026-09-06, human ("approved"): user approved execution in turn: 'now execute, please'

## Workflow history
- 2026-09-06 approved (aw set, --by-human): user approved execution in turn: 'now execute, please'

- 2026-09-06 reviewed (antigravity/gemini-2.5-pro): /plan-review; APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Structural lint conformed at `--phase author` and `--phase review-finalize`.
- 2026-09-06 to-review (Gabriele Fariello <gabriele.fariello@gmail.com>): created review-ready IPD for multi-attribute sorting and TTY table sort preservation.

## Goal

Enable flexible, intuitive multi-column sorting in `aw attention` (and `aw next`) via comma-separated keys on `--order-by/-o` (e.g. `-o priority,status,id6`), expanding the attribute vocabulary to cover all table columns and filesystem timestamps, while fixing the TTY table renderer to strictly preserve user-specified sort order.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fix TTY table sort erasure

- [ ] E-01 In `agent_workflows/attention.py`, update `render_table()` to accept an `order_by: Optional[str]` parameter (passed from `cmd_attention`). When `order_by` is provided and differs from `A.ORDER_CLASS`, skip the hardcoded `visible.sort(key=_sort_key)` call so the items strictly retain their caller-sorted sequence. When `order_by` is absent or `A.ORDER_CLASS`, retain the historical default table sort.
  - Depends on: none
  - Expected outcome: `render_table()` displays rows in the exact order specified by `-o` rather than resetting them to the hardcoded sort.
  - Execution state: pending

### Task group 2: Expand sort attribute vocabulary and multi-attribute parsing

- [ ] E-02 In `agent_workflows/attention_contract.py` and `agent_workflows/cli.py`, expand the ordering vocabulary to recognize `readiness`, `oqs`, `rqs`, `file`, `ctime`, and `mtime` alongside existing keys (`class`, `priority`, `date`, `set`, `order`, `blocking`, `depth`, `id6`, `path`, `status`, `tree`). In `cli.py`, replace the strict atomic `choices` check with a parser/validator that accepts comma-separated lists of keys (e.g. `priority,status,id6`), verifies every component against `_attention_order_keys()`, and raises an actionable error listing valid choices if an unknown token is supplied.
  - Depends on: none
  - Expected outcome: `aw att -o priority,status,id6` parses cleanly into a validated sequence of sort keys, while invalid keys continue to be rejected with helpful error messages.
  - Execution state: pending

### Task group 3: Multi-attribute stable sort engine

- [ ] E-03 In `agent_workflows/attention.py`, implement multi-attribute sorting across the full vocabulary (`status`, `type`, `blocking`, `priority`, `readiness`, `oqs`, `rqs`, `setid`, `id6`, `file`, `ctime`, `mtime`). For `ctime` and `mtime`, read file stat timestamps via `(repo_root / it.path).stat()` inside a `try...except OSError` block, safely returning `(_ABSENT, 0)` if the file is missing or unreadable. Apply stable sort passes in reverse order of the requested attributes, falling through to the deterministic `(path, id)` tiebreaker. Enforce explicit direction semantics: descending for `priority`, `blocking`, `oqs`, `rqs`, `ctime`, `mtime`; ascending for `status`, `type`, `setid`, `id6`, `file`; and ranked order for `readiness` (`go` > `go-pending-approval` > `no-go` > absent).
  - Depends on: E-01, E-02
  - Expected outcome: items are sorted stably according to the multi-column precedence specified by the user with robust handling of missing files.
  - Execution state: pending

### Task group 4: Suite verification and test coverage

- [ ] E-04 Add comprehensive tests in `tests/test_next_ordering.py` covering: (1) multi-column sorting precedence on fixture data, (2) TTY table output preserving explicit sort order under colored mode, (3) new attribute keys (`readiness`, `oqs`, `rqs`, `file`, `ctime`, `mtime`) including synthetic missing-file handling, and (4) verify the entire test suite passes bare (`python3 -m pytest`).
  - Depends on: E-01, E-02, E-03
  - Expected outcome: all new ordering features are pinned by unit tests and `python3 -m pytest` passes with zero regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `render_table()` in `agent_workflows/attention.py:1625-1633` currently hardcodes `visible.sort(key=_sort_key)`, which unconditionally overwrote any prior sorting performed by `cmd_attention()`.
- `ORDER_KEYS` in `agent_workflows/attention_contract.py:84-96` defines the closed vocabulary. In `agent_workflows/cli.py:3374`, `argparse` uses `choices=_attention_order_keys()`, which rejects comma-separated strings unless custom validation or comma splitting is applied before choice checking.
- Spec Section 8.5 mandates determinism: the default attention view must not read `ctime` or `mtime`. Reading `stat()` timestamps is only permitted when the user explicitly passes `ctime` or `mtime` in `-o`.
- Python's `list.sort()` is Timsort, which guarantees stability: sorting successively by keys in reverse order produces the exact multi-column hierarchy.
- `tests/test_next_ordering.py` tests `-o` exclusively with `no_color=True` or `format="json"`, which explains why the TTY table sorting bug was never caught by existing CI tests.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | In colored TTY mode, `render_table()` overwrites item ordering with a hardcoded `_sort_key` (`attention.py:1633`), making `-o priority` a silent no-op. | `agent_workflows/attention.py:1625-1633` |
| F-2 | In non-colored mode, `render_board()` partitions items into attention classes (`blocked`, `active`, `ready`), so sorting only occurs within each class section rather than globally. | `agent_workflows/attention.py:1703-1707` |
| F-3 | `cli.py:3374` restricts `--order-by` choices to single tokens via `choices=_attention_order_keys()`, preventing comma-separated composite keys. | `agent_workflows/cli.py:3374` |
| F-4 | Existing tests in `tests/test_next_ordering.py` run all test cases with `no_color=True` or `format="json"`, leaving `render_table()`'s sort behavior completely untested. | `tests/test_next_ordering.py:40-54` |
| F-5 | Several attributes displayed in the TTY table (`Readiness`, `OQs`, `RQs`) had no corresponding sort key in `ORDER_KEYS`. | `agent_workflows/attention_contract.py:84-96` |
| F-6 | `test_all_four_names_agree_under_order_by` iterates over `A.ORDER_KEYS`. Adding `ctime` and `mtime` will exercise files that may not exist on disk in synthetic test fixtures, requiring graceful `OSError` fallbacks. | `tests/test_next_ordering.py:228-234` |

## Proposed changes (ordered, validatable)

1. Update `render_table()` to accept `order_by` and skip the hardcoded re-sort when an explicit order is active (E-01).
2. Expand sort vocabulary in `attention_contract.py` and add comma-separated parsing in `cli.py` (E-02).
3. Implement multi-attribute stable sorting engine in `attention.py` with filesystem timestamp lookups and graceful missing-file fallback (E-03).
4. Add unit test coverage in `tests/test_next_ordering.py` and verify suite bare (E-04).

## Deferred / out of scope (with reason)

- Custom descending prefixes per attribute (e.g. `-o priority:desc,status:asc`) are deferred to keep the CLI syntax simple and consistent with standard comma-separated lists.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Unit tests in `tests/test_next_ordering.py` verifying multi-key sorting precedence (e.g. priority then status).
- Unit tests in `tests/test_next_ordering.py` verifying `render_table()` output preserves row order.
- Unit tests in `tests/test_next_ordering.py` asserting missing files sort gracefully under `ctime`/`mtime`.
- Full pytest suite execution without options: `python3 -m pytest`.

## Spec / documentation sync

- Update CLI help strings for `--order-by/-o` in `cli.py` to document comma-separated multi-attribute usage.

## Open questions

None. All sort keys, syntax conventions, direction semantics, and tiebreaker rules were aligned during design and review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Unit test in `tests/test_next_ordering.py` verifying that calling `render_table()` with explicitly ordered items preserves their exact sequence.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Unit test in `tests/test_next_ordering.py` verifying that comma-separated lists of keys (e.g. `priority,status,id6`) parse cleanly and reject invalid tokens.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Unit tests in `tests/test_next_ordering.py` verifying multi-attribute sort precedence on fixtures with known attributes, confirming that earlier keys take precedence over later keys, missing files are handled safely, and stable tiebreaking holds.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Full output from a bare `python3 -m pytest` run demonstrating that all existing and new tests pass without regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: The executor MUST (1) commit ONLY files changed within the declared `Scope-Paths`, path-scoped via `git commit -m msg -- <paths>`, never using `git add -A` or bare `git commit`, and never push; (2) demonstrate all unit tests pass by pasting the ACTUAL bare runner output from `python3 -m pytest`; (3) resolve all validation items V-01 through V-04 with concrete evidence; and (4) finalize lifecycle transition to `executed/` via `aw ipd finalize` once verified.
