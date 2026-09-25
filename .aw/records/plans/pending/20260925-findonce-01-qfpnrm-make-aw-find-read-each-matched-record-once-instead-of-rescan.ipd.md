# IPD: Make aw find read each matched record once instead of rescanning the whole plans and research trees

- Date: 2026-09-25
- Kind: child
- Concern: `aw find plans <selector>` (and `aw find research <selector>`) open every record in the tree twice: once in the resolver's bounded header read and again in a full-tree display rescan, costing about 130ms of a user-visible ~600ms command.
- Scope: Replace the whole-tree `plans_index.scan_plans` / `research_index._scan_docs` call on the SELECTOR branch of `cli._find_type_records` with a per-path entry builder applied only to the resolver's matched paths; the no-selector branch, the matching semantics, and the displayed output stay byte-identical.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/plans_index.py, agent_workflows/research_index.py, agent_workflows/selectors.py, tests/test_find_single_read.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 59t9x5
- Blocks-Release: next
- Set: findonce
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: qfpnrm

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 59t9x5; re-measured with an audit hook at HEAD: 1508 record opens for 754 plans (every one twice) on `find plans <id6>`, scan_plans 129.6ms of a 316.3ms warm in-process run, 0.61s best cold subprocess.

## Goal

Remove the redundant second read of every record that `aw find <type> <selector>` performs for the `plans` and `research` types, so the command opens each record once plus each MATCHED record once, and drops the ~130ms display rescan, without changing a single byte of output or which records match.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and guard

- [ ] E-01 Capture the BEFORE baseline, before touching code: under `/tmp/opencode/findonce-baseline/`, save `python3 -m agent_workflows find <type> <sel>` stdout for the fixed selector corpus `plans wqq8ua`, `plans wtiso`, `plans stopladder`, `plans executed`, `plans ctrl`, `plans` (no selector), `research <any research id6 from aw find research>`, `research` (no selector), `specs c4gd2h`, `backlog 59t9x5`; also run the audit-hook open counter (`sys.addaudithook` counting `open` events on `.aw/records/**.md`, as in `/tmp/opencode/g3/probe-findonce/count.py`) on `find plans wqq8ua` and `find research <id6>` and the best-of-5 in-process timer wrapping `plans_index.scan_plans` (as in `.../probe-findonce/split.py`).
  - Depends on: none
  - Expected outcome: ten stdout files plus a text file with the open counts and timings; plans open count equals twice the plan count.
  - Execution state: pending

- [ ] E-02 Add `tests/test_find_single_read.py` with a tmp-repo fixture of about 6 plans (two sharing a Set, one executed, one in a `executed/YYYYMM/` shard, one whose `- Status:` has trailing prose so `plans_index._META_RE["Status"]` and `selectors._STATUS_RE` disagree) and 3 research docs. Tests: (a) `find plans <id6>` opens each plan file at most twice and NON-matched plan files exactly once (audit hook counting per path), (b) the same for `find research <id6>`, (c) `find plans <setid>` output lines equal the lines produced by filtering a full `scan_plans` by the matched paths (the old algorithm, computed inside the test as the oracle), including ordering and the shard's disposition, (d) the Status-disagreement record still MATCHES per the resolver and DISPLAYS the whole-file `plans_index` status.
  - Depends on: E-01
  - Expected outcome: tests (a) and (b) FAIL at HEAD (non-matched files opened twice); (c) and (d) pass at HEAD, pinning current behavior.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 In `plans_index`, extract the per-file body of `scan_plans` into `plan_entry(plans_dir: Path, p: Path) -> Optional[Tuple[PlanEntry, List[_core.Drift]]]` returning None for a path `scan_plans` would skip (`_EXCLUDE_NAMES`, `_core.is_ignored_path`, or not under `plans_dir`); make `scan_plans` a loop over it. Do the same in `research_index`: `_doc_entry(research_root, p)` extracted from `_scan_docs`, preserving every skip and drift branch (non-conformant name, missing/invalid frontmatter).
  - Depends on: E-02
  - Expected outcome: pure refactor; `tests/test_plans_index.py` and E-02's tests unchanged in result.
  - Execution state: pending

- [ ] E-04 In `cli._find_type_records`, on the `plans` branch move `pi.scan_plans(plans_dir)` INTO the `else:` (no-selector) arm; on the selector arm build `results` from `pi.plan_entry(plans_dir, p)` for each resolved matched path, drop Nones, and sort by the same key `scan_plans` iterates in (`sorted` over `Path` objects relative to `plans_dir`, NOT the string sort `_resolve_selectors_with_kinds` returns), then apply the existing `pi.query` filter unchanged. Mirror this on the `research` branch with `ri._doc_entry`. Leave the display loop, `highlight_tokens`, and the `paw8so` comment block intact; update the `selectors.py` "WHERE THE REAL COST IS" note to say the double read was removed by `qfpnrm`.
  - Depends on: E-03
  - Expected outcome: E-02 (a)-(d) pass; each non-matched record is opened once.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Re-run E-01's selector corpus into `/tmp/opencode/findonce-after/` and `diff -r` against the baseline; re-run the open counter and the in-process timer on the same commands.
  - Depends on: E-04
  - Expected outcome: empty diff; plans opens about N_plans + matched (not 2 x N_plans); in-process time drops by roughly the old `scan_plans` share.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-05
  - Expected outcome: all pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw find` returns ARTIFACTS, not references (`selectors.py` header note, plan `826o13` E-01); `_PRECEDENCE` is frozen semantics. This plan does not touch `selectors.resolve`.
- `plans_index` (display, whole file, `(.+?)` Status) and `selectors` (matching, bounded header, `(\S+)` Status) DELIBERATELY disagree; the `paw8so` comment in `_find_type_records` states the whole-file display answer is authoritative. Keeping both readers, each for its current role, preserves that.
- The old find tests (`tests/test_cli_find.py`, `tests/test_selector_zero_open.py`) were removed by `19313eed` ("trim test suite"), so this plan adds a new focused file rather than extending them.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

Measured 2026-09-25 in the worktree at HEAD of `feat/graduate-batch3`, warm:

| Command | Record opens | Unique | Opened >= 2x | Note |
|---|---|---|---|---|
| `find plans 4awwg4` | 1508 | 754 | 754 | every plan twice |
| `find plans wqq8ua` | 1509 | 754 | 754 | |
| `find plans` (no selector) | 754 | 754 | 0 | only `scan_plans` runs |
| `find research 4awwg4` | 248 | 124 | 124 | same defect on research |
| `find specs 4awwg4` | 37 | 37 | 0 | generic branch reads matched only |
| `find backlog 4awwg4` | 606 | 604 | 1 | generic branch fine |

- BEFORE (the number V-05 compares against): `find plans wqq8ua` best-of-5 in-process 316.3ms, of which `plans_index.scan_plans` 129.6ms and `selectors.resolve` 89.3ms; cold subprocess best of 7 0.61s (median 0.66s); `aw --version` floor 0.35s.
- Cause: `_find_type_records` calls `pi.scan_plans(plans_dir)` (whole-tree `read_text`) BEFORE branching on `selectors_list`, then keeps only entries whose path is in the resolver's matched set. The research branch does the same with `ri._scan_docs`. The generic branch already reads only `matched_paths`, which is the shape this plan adopts.
- The backlog's caution that unifying the two readers changes matching is honored by NOT unifying them: matching stays in `resolve`, display fields still come from the whole-file `plans_index` parse, just for matched files only.

## Proposed changes (ordered, validatable)

1. Baseline outputs, opens, and timings (E-01).
2. Regression tests pinning open counts and output equivalence (E-02).
3. Per-file entry builders in `plans_index` and `research_index` (E-03).
4. Selector branch uses them on matched paths only, sorted in `scan_plans` order (E-04).
5. Byte-diff and re-measure (E-05), full suite (E-06).

## Deferred / out of scope (with reason)

- Interpreter start plus `import agent_workflows.cli` (the ~0.35s `--version` floor) dominates the remaining cost and is a separate concern.
  - Carrier-Declined: not a double read; the backlog explicitly says this item cannot take `find` below that floor, and no measured defect is filed for it here.
- Correcting stale `wtiso` counts in older records.
  - Carrier: kx9md1

## Scope check

- Over-scope: none; specs/backlog/other generic types are already single-read and untouched.
- Under-scope: the `research` branch has the identical defect (248 opens / 124 docs) and is included, since leaving it would leave the same bug live under the same gate.

## Required tests / validation

New `tests/test_find_single_read.py` (E-02) with open-count assertions that fail at HEAD, output-equivalence oracle tests, the live-corpus byte diff (E-05), a re-measure of opens and time against the Findings numbers, and the bare suite.

## Spec / documentation sync

No spec governs `find`'s read strategy; output is unchanged. Only the in-code note in `selectors.py` ("WHERE THE REAL COST IS") is updated so it stops pointing at a fixed defect. N/A for user docs.

## Open questions

### OQ-01: Should the backlog `find` path also be checked for the one doubly-opened record?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: measured 606 opens / 604 unique on `find backlog`; one extra open is not a perceptible cost and comes from the generic branch's `read_text` of a matched file, which is the intended single display read. No action.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `ls /tmp/opencode/findonce-baseline/` listing the ten stdout files, and the pasted counter lines showing `opens=` equal to 2 x `unique=` for `find plans wqq8ua` and `find research <id6>`, plus the pasted `scan_plans=` timing line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_find_single_read.py -q` run BEFORE E-03/E-04 showing tests (a) and (b) FAILED with an open count of 2 for a non-matched file, and (c) and (d) passed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_plans_index.py tests/test_find_single_read.py -q` summary after E-03 alone, with the same pass/fail split as V-02 (refactor changes nothing), and `git diff --stat` showing only `plans_index.py` and `research_index.py` changed by this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_find_single_read.py -q` showing all tests passed, and `grep -n "scan_plans(plans_dir)" agent_workflows/cli.py` showing the call only inside the no-selector arm.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted empty output of `diff -r /tmp/opencode/findonce-baseline /tmp/opencode/findonce-after`; pasted AFTER counter line for `find plans wqq8ua` showing `opens=` at most `unique=` plus the matched count (BEFORE 1509) and for `find research <id6>` (BEFORE 248); pasted AFTER in-process timing line (BEFORE total 316.3ms with scan_plans 129.6ms) showing no `scan_plans` time on the selector path and total reduced by roughly that amount; and a best-of-7 cold subprocess time for `python3 -m agent_workflows find plans wqq8ua` (BEFORE 0.61s).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the pasted final summary line of bare `python3 -m pytest` showing `N passed` and no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `- Status: approved`. Commit through `aw commit qfpnrm -- <Scope-Paths>`; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries observed evidence.
