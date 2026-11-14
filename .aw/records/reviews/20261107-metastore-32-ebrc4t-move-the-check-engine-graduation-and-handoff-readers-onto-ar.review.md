# Review findings: plan ebrc4t

- Subject-Id: ebrc4t
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/claude-opus-5.5
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `f792d7fcf` in a non-interactive runner review-sweep lane worktree. The tracked plan was committed and unmodified, so the pre-review snapshot commit was skipped. `aw ipd lint --phase author --agent` returned `clean` (0 findings) before edits; `aw ipd lint --phase review-finalize --agent` returned `clean` (0 findings) after edits. The eight `- Item-Dependencies:` exist; `i16on1` (Order 144, `reviewed`) adds `layout.RECORD_SCAN_SKIP_NAMES` (`README.md`, `INDEX.md`, `STATUS.md`) and `layout.RECORD_SCAN_EXCLUDED_DIRS` (`meta`) and creates `tests/test_readers_check_engine.py`, which does not exist yet; the gate requires it executed first.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Checklist preamble | "Every E-item that moves a reader" pin-test rule citing ledger decisions D-1 to D-5 and an unnamed baseline module set | E-03 moves no reader; outcome-list pin over seven named REGRESSION MODULES into `.aw/state/ffceq0/E-03-ebrc4t-{before,after}.txt` with an empty `diff` | PR-003 |
| E-03 | Three `releases` walkers; "Those record walkers consult both constants" | Four walkers (adds `check_graduated_to`); sites consult only `RECORD_SCAN_SKIP_NAMES` with the reason `meta/` is unreachable from their roots; update the `specs._spec_files` comment | PR-001, PR-004 |
| E-03 Expected outcome, V-03 | `rg` over assignment patterns only | Adds `rg -n '"STATUS.md"'` over the three modules (catches inline tuples), the outcome-list `diff`, three walker test modules and the core gate summary | PR-002 |
| Findings (E-03 measurement), Reader ledger and Decisions headers | "3 inline tuples"; "rows this part moves"; "decisions that govern this part's reader moves" | Notes the fourth tuple at review; labels ledger and decisions as context, only D-5 governing E-03 | PR-001, PR-003 |
| Required tests | Four modules | Seven modules with the empty outcome-list `diff` | PR-002 |
| Approval and execution gate | "Every reader move is pin-first ... copied decisions name"; transition without runner/hand ownership | E-03 pin-first sentence; conditional `aw ipd finalize ebrc4t` ownership | PR-003, PR-005 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. Internal constants only; no CLI, output, file-format or spec contract.
2. No.
3. No. One E-item over three modules.
4. Yes. `- Scope-Paths:` names `specs.py`, `releases.py`, `ipd_lint.py` and the plan.
5. Mildly. A missed or mistyped skip name would make `aw specs check`, the release gates or `aw ipd lint` read `README.md`/`INDEX.md`/`STATUS.md` as records; the outcome-list diff and the walker test modules catch it.

AW-TIER: standard

### Step R1

- Checked: `rg -n '"STATUS.md"' agent_workflows` at `f792d7fcf`: `specs._spec_files` `skip_names` set; `releases.py` inline tuples in `count_blocks_release_sentinel`, `check_blocks_release`, `check_from_backlog` AND `check_graduated_to`; `ipd_lint._NON_IPD_BASENAMES` (used once, in `_iter_plan_files`) and the inline tuple in `ipd_lint._default_pending_files`. `_NON_IPD_BASENAMES` has no importer outside `ipd_lint` and no test reference, so replacing it is safe. `layout.py` imports only `lifecycle_dirs`, so importing it from `specs`, `releases` and `ipd_lint` adds no cycle.
- Found the fourth `releases` tuple missing from E-03 (PR-001).

### Step R2

- Checked: E/V bijection (1/1), V-03 evidence sufficiency, gate contract.
- V-03's pattern `_SKIP_NAMES\s*=|_NON_IPD_BASENAMES\s*=|skip_names\s*=` cannot see an inline tuple, so a run that left the `releases` and `_default_pending_files` tuples in place would still pass V-03 (PR-002).
- Preamble and gate demanded a reader-move pin test and named decisions for an item that moves no reader, and named no baseline module (PR-003). Transition lacked runner/hand ownership (PR-005).

### Step R3

- Checked: no secret, private-data, commit, worktree or sandbox code; no security finding.

### Step R4

- Checked: every walker's root (`specs._spec_files` roots at `<records>/specs` and legacy spec roots; the four `releases` walkers at `<records>/{backlog,specs,plans}` and `.agents/` twins; `ipd_lint` at `<records>/plans` and `<records>/plans/pending`), each globbing `*.md`. None can reach `<records>/meta/`, so "consult both constants" would add dead code with unspecified semantics; a path-part `meta` check would instead risk excluding a legitimate nested directory (PR-004). Spec `4sd62s` 4.4 last bullet (one list) is satisfied by the single `RECORD_SCAN_SKIP_NAMES` definition.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Completeness of site list | `agent_workflows/releases.py::check_graduated_to` carries `"STATUS.md",` in an inline skip tuple (fourth occurrence in the module) | E-03 named three `releases` walkers; the fourth copy would survive and the "one list" goal (4.4) would fail | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names `check_graduated_to`; Findings note the fourth tuple. Strength: very strong |
| PR-002 | MEDIUM | IN-SCOPE | Validation sufficiency | ebrc4t V-03 `rg -n "_SKIP_NAMES\s*=\|_NON_IPD_BASENAMES\s*=\|skip_names\s*=..."` | The V-03 pattern matches only assignments, so leftover inline tuples pass unseen; walker test modules for `releases` were not run | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `rg -n '"STATUS.md"'` over the three modules, the outcome-list `diff`, `test_blocks_release_reader_bounding`, `test_from_backlog_cardinality`, `test_graduation_forward_links`, and the core gate. Strength: strong |
| PR-003 | LOW | IN-SCOPE | Honest documentation / executability | ebrc4t preamble "Every E-item that moves a reader follows one rule"; gate "Every reader move is pin-first"; ledger header "rows this part moves" | Pre-split text demands a reader-move pin test and ledger decisions for an item that moves no reader, and names no baseline module | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with an outcome-list pin over seven named modules; ledger and decisions labelled context. Strength: strong |
| PR-004 | LOW | IN-SCOPE | Engineering (KISS) | ebrc4t E-03 "Those record walkers consult both constants"; `layout.RECORD_SCAN_EXCLUDED_DIRS` = `meta` (`i16on1` E-01) | The excluded-directory check is unreachable from these walkers' roots and its semantics were unstated | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | These sites use only `RECORD_SCAN_SKIP_NAMES`, with the root analysis recorded (D-1). Strength: medium |
| PR-005 | LOW | UNDER-SCOPE | Execution contract | ebrc4t gate "Lifecycle transition" | Missing conditional runner/hand-executor finalize ownership | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added. Strength: strong |

### Step S5

- Checked: OQ-01 (`Blocking: no`, `resolved`), still accurate (1 E-item, 3 work Scope-Paths). No human-owned question arose.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Must the `specs`, `releases` and `ipd_lint` walkers also consult `layout.RECORD_SCAN_EXCLUDED_DIRS`? | No; they use only `RECORD_SCAN_SKIP_NAMES`, because each roots at a type directory and globs `*.md`, so `<records>/meta/` is unreachable | Add a path-part `meta` check (rejected: dead code, and a bare part match could exclude a legitimate nested `meta` directory); add a records-root-relative check (rejected: unreachable) | `agent_workflows/releases.py::count_blocks_release_sentinel` `for base in (records_root / sub, ...)`; `agent_workflows/specs.py::_spec_files` `local_specs = project_records_dir(repo_root) / "specs"`; `agent_workflows/ipd_lint.py::_default_pending_files`; `i16on1` E-01 | yes |

### Step S6

- Re-read E-03, V-03, Required tests, the gate, ledger and decisions headers after edits; `grep` for `moves a reader`, `Every reader move` and `consult both constants` found no stale sibling. No new finding.
- `AW-REVIEW: DONE`
