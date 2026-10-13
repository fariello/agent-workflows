# IPD: Make agy_run.resolve_ipd recursive so sharded plans resolve

- Date: 2026-10-11
- Kind: child
- Concern: `agy_run._candidate_plans` enumerates candidate plans with a NON-RECURSIVE `plans_base.glob("*.md")` over `.agents/plans/<state>` and `.aw/records/plans/<state>`, so a plan that `aw archive plans --apply` has moved into a `YYYYMM/` shard (`plans_archive._shard_target`, by design) is invisible to `agy_run.resolve_ipd` for every selector except an exact existing path. Re-measured in this lane at HEAD `cedb25f80` in a temp git repo: with an executed plan at `.aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md`, `resolve_ipd(root, "ab12cd", ("executed",))` raises `No IPD matching 'ab12cd' found in plan states: executed.`, the exact path resolves (via the `direct.is_file()` early return), and positional `resolve_mode_and_target(root, parse_args(["--audit-only", "ab12cd"]))` returns `('prompt', 'ab12cd', '')`, i.e. a valid plan id6 is SILENTLY executed as an inline prompt. Dormant today (all five plan disposition dirs have zero subdirectories, measured) but live on the first archive sweep. Two further measured defects of the same flat loop: `resolve_ipd(root, "README.md", ("pending",))` resolves the pending README as an IPD, and the loop has no ignored-path filter, which non-recursion was masking.
- Scope: Give plans ONE canonical "which files are plans" enumerator, `plans_index.plan_files(plans_dir)`, extracted from the recursive, ignored-path-filtered, `_EXCLUDE_NAMES`-skipping walk `plans_index.scan_plans` already performs, make `scan_plans` consume it (behavior unchanged), and make `agy_run._candidate_plans` delegate to it, keeping only files whose top-level disposition is in the requested states and that lie inside the repository root. Add a collected behavioral test module under `tests/`. Does NOT change the matching semantics, either error message, the `direct.is_file()` early return, the function signatures, any caller, or `resolve_spec`.
- Scope-Paths: agent_workflows/agy_run.py, agent_workflows/plans_index.py, tests/test_agy_run_resolve_ipd_recursive.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: mlcbk9
- Blocks-Release: next
- Set: mlcbk9
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: m734rl
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Reviewed at HEAD 7e9129224. Duplicate id6 across a shard measured to silently misresolve at base, so E-02 (8) split into red (8a) with its own id6 and green (8b); ambiguity renderer fixed to relative_to(root.resolve()); plan_files takes optional ignored_dirs; exclude written before first resolver call (lru_cache); base bare-suite run moved into E-01. Record: .aw/records/reviews/20261011-mlcbk9-01-m734rl-make-agy-run-resolve-ipd-recursive-so-sharded-plans-resolve.review.md.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `mlcbk9`, graduating it. Every claim in the item was re-measured in this lane at HEAD `cedb25f80` (F-01, F-02). The item left the canonical-source choice open; resolved here from repository evidence as OQ-01 (extract `plans_index.plan_files`, F-03, F-04). Two extra defects measured that the item does not state: README resolution (F-05) and the missing ignored-path filter (F-06).

## Goal

After this plan, `aw agy exec <id6>`, `--ipd <id6>`, `--ipd <bare filename>` and the Turn-2 audit lookup (`resolve_ipd(root, plan_id, ("executed",))` in `agy_run.run`) all resolve a plan sitting in a `<disposition>/YYYYMM/` shard, through one plan-enumeration definition shared with the plans manifest, so the next layout change cannot break the runner's resolver without also breaking `aw index plans`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: establish the failing baseline

- [x] E-01 CAPTURE THE REPRODUCTION AT THE BASE COMMIT, before any edit.

  Build a throwaway temp git repo (inside the gitignored `tmp/` of the workspace or the system temp dir; never under the tracked tree) containing `.aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md` and `.aw/records/plans/pending/README.md`. In process (`AW_NO_REEXEC=1 python3 -c ...`, resolved root), capture verbatim: (1) `agy_run.resolve_ipd(root, "ab12cd", ("executed",))` raising `ScriptError` `No IPD matching 'ab12cd' found in plan states: executed.`; (2) the same for the bare filename `20260901-set-01-ab12cd-thing.ipd.md`; (3) the exact path `.aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md` RESOLVING (must keep working); (4) `agy_run.resolve_mode_and_target(root, agy_run.parse_args(["--audit-only", "ab12cd"]))` returning `('prompt', 'ab12cd', '')`; (5) `agy_run.resolve_ipd(root, "README.md", ("pending",))` returning the pending README; (6) with a second plan `.aw/records/plans/executed/20260801-set-02-dd44ee-other.ipd.md` and `.aw/records/plans/executed/202609/20260901-set-03-dd44ee-dup.ipd.md`, `resolve_ipd(root, "dd44ee", ("executed",))` SILENTLY returning the top-level one instead of raising `is ambiguous` (F-09). Also run `python3 -m pytest tools/test_agy_run.py -o addopts="" -q` and keep its summary line (the module is NOT collected by the default suite, `testpaths = ["tests"]`), and run the bare `python3 -m pytest` NOW, before any edit, keeping its summary line and sorted failing test ids as the base for E-05's delta.

  NEVER LAUNCH A REAL AGENT. These probes call resolver functions only; if a CLI probe is added, pass `--agy <stub> --no-audit` where `<stub>` is a throwaway executable that prints argv and exits 1 (the a6ootg E-01 pattern).
  - Depends on: none
  - Expected outcome: five pasted defect captures, one pasted must-keep-working resolution, the base commit hash, the `tools/test_agy_run.py` summary line, and the base bare-suite summary line with its failing ids.
  - Execution state: performed

- [x] E-02 WRITE `tests/test_agy_run_resolve_ipd_recursive.py` AND SHOW IT RED BEFORE ANY PRODUCTION EDIT.

  Under `tests/` so a gate collects it (`pyproject.toml` `testpaths = ["tests"]`; CI runs `python -m pytest tests/`). Drive a fixture git repo built in `setUp` (copy the `init_repo` shape from `tests/test_agy_run_resolve_spec_recursive.py`, including its `_temp_base_dir` helper so no path component is `tmp`, and its `AW_HOME` sandbox). Assert, each by calling `agy_run.resolve_ipd` / `agy_run.resolve_mode_and_target` and checking the real return value or raised exception:
  (1) a plan in `.aw/records/plans/executed/202609/` resolves by bare id6 with states `("executed",)`;
  (2) the same plan resolves by bare filename;
  (3) the same plan is NOT returned for states `("pending",)` (disposition is the TOP-LEVEL dir, not the shard);
  (4) a flat `.agents/plans/pending/` legacy plan still resolves by id6 (the `tools/test_agy_run.py` fixture shape);
  (5a) a plan under `.aw/records/plans/pending/untracked/` is NOT resolvable (hardcoded `untracked` rule in `artifact_core.is_ignored_path`);
  (5b) a plan under `.aw/records/plans/pending/scratch/` ignored ONLY by a rule in the fixture's `.git/info/exclude` is NOT resolvable (proves the `get_ignored_dirs` git path is consulted);
  (6) `README.md` in `pending/` is NOT resolvable as an IPD by bare name `README.md`;
  (7) positional `resolve_mode_and_target(root, parse_args(["--audit-only", "ab12cd"]))` returns mode `ipd` with the repo-relative sharded path;
  (8a) two plans sharing a DIFFERENT id6 (e.g. `dd44ee`) across `executed/` and `executed/202609/` raise `is ambiguous` listing both repo-relative paths (today the flat glob sees only the top-level one and SILENTLY returns it, F-09);
  (8b) preserved semantics: an exact existing path still resolves; a path in a disallowed state still raises `not in an allowed plan state`.

  FIXTURE RULES: every id6 is used by exactly the assertions that name it, so (1), (2) and (7) see ONE `ab12cd` plan and (8a) uses its own id6; write `.git/info/exclude` in `setUp` BEFORE the first resolver call, because `artifact_core._cached_ignored_dirs` is an `lru_cache` keyed on the plans dir's own (absent) `.gitignore`/`.git/info/exclude` mtimes, so a rule added after the first call in the same process is not seen (each test's fresh temp root is a fresh cache key).

  NO STATIC ANALYSIS (GUIDING_PRINCIPLES P16): never read `agy_run.py` or `plans_index.py` source, never assert `rglob` appears, never count callers.
  - Depends on: E-01
  - Expected outcome: a collected module whose assertions (1), (2), (6), (7) and (8a) FAIL at the base commit and whose (3), (4), (5a), (5b) and (8b) PASS there (exclusions hold vacuously before the fix because the flat glob cannot descend), with the red output pasted verbatim.
  - Execution state: performed

### Task group 2: one canonical plan enumerator

- [x] E-03 EXTRACT `plans_index.plan_files(plans_dir) -> List[Path]` AND MAKE `plans_index.scan_plans` CONSUME IT.

  Move the walk out of `scan_plans` into a public function `plan_files(plans_dir, *, ignored_dirs=None)`: return `[]` when `plans_dir` is not a dir; when `ignored_dirs` is None compute `_core.get_ignored_dirs(plans_dir)` once (`scan_plans` computes it itself and passes it to both `plan_files` and `plan_entry`, so the git subprocess still runs once per scan, the F-6 rule `plan_entry`'s docstring records); return `sorted` `plans_dir.rglob("*.md")` minus `p.name in _EXCLUDE_NAMES` minus `_core.is_ignored_path(p, plans_dir, ignored_dirs)`. These are exactly the two filters `plan_entry` applies today (its `_EXCLUDE_NAMES` / `is_ignored_path` early-return), so `scan_plans` keeping its `plan_entry` call over `plan_files(...)` produces an identical entry list. Keep `plan_entry`'s own filter (it is also called directly by `cli.py`'s `aw find plans` path with explicit paths). Give `plan_files` a docstring stating it is THE definition of which files are plans, that recursion and the ignored-path filter are COUPLED (a recursive walk without the filter returns box-local `untracked/` plans; cite backlog `mlcbk9` and the `specs._spec_files` docstring that records the same lesson), and that disposition is `rel.parts[0]`. Do not change `scan_plans`' signature, return type, or ordering.
  - Depends on: E-02
  - Expected outcome: `plans_index.plan_files` exists and is used by `scan_plans`; `tests/test_plans_index.py` (including `test_recursive_scan_sees_sharded_plan`) passes unchanged; the live repo's `scan_plans` entry count is identical before and after.
  - Execution state: performed

- [x] E-04 DELEGATE `agy_run._candidate_plans` TO `plans_index.plan_files`.

  For each of the two existing bases (`root / ".agents" / "plans"` and `root / ".aw" / "records" / "plans"`, kept HARDCODED and in-repo exactly as today; do NOT switch to `record_producers.resolve_record_path`, which can return an out-of-repo dir under a `home` backend and would break `relative_posix` / the ambiguity renderer, the a6ootg F-10 lesson), call `plans_index.plan_files(base)` and keep `p` only when `p.relative_to(base).parts[0] in states`. Then resolve and fence: `sorted({p.resolve() for p in ... if p.resolve().is_relative_to(root.resolve())})`. Import `plans_index` LOCALLY inside the function, matching the module's existing local imports of `specs` and `agy_sessions` (no top-level package import exists in `agy_run`). Because candidates are now RESOLVED paths, change the ambiguity renderer in `resolve_ipd` from `p.relative_to(root)` to `p.relative_to(root.resolve())`, unconditionally: with an unresolved `root` (a symlinked temp dir, or a relative `Path(".")`) the old expression would raise an uncaught `ValueError` instead of the `is ambiguous` `ScriptError`. That rendering change is the ONLY edit to `resolve_ipd`'s body. Leave the three matching branches (`.md`/path name match, `-{id6}-` substring, exact name), both error messages and the `direct.is_file()` early return EXACTLY as found, and say so in a comment citing `mlcbk9`.
  - Depends on: E-03
  - Expected outcome: every E-02 assertion passes; `tools/test_agy_run.py` passes at its E-01 count; matching expressions and both message texts unchanged.
  - Execution state: performed

### Task group 3: prove nothing else moved

- [x] E-05 RUN `tools/test_agy_run.py` BY NAME, `tests/test_plans_index.py`, `tests/test_plans_archive.py`, AND THE BARE FULL SUITE BEFORE AND AFTER.

  `python3 -m pytest tools/test_agy_run.py -o addopts="" -q` (uncollected by default, so run by name), `python3 -m pytest tests/test_plans_index.py tests/test_plans_archive.py tests/test_agy_run_resolve_ipd_recursive.py tests/test_agy_run_resolve_spec_recursive.py`, then the bare `python3 -m pytest` with NO added flags (AGENTS.md: no `-n0`, no extra `-q`, no `-p no:randomly`) at the end, compared with the base run E-01 captured before any edit. The bar is an EMPTY failure-set delta stated as test ids, not a count comparison. Also re-run the E-01 in-process probes after the fix and paste them.
  - Depends on: E-04
  - Expected outcome: targeted modules pass; two bare-suite summary lines pasted; failure-set delta explicitly empty; E-01 probes now resolve (`ipd` mode, sharded path) and README raises.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE BARE SUITE IS THE CONTRACT: `python3 -m pytest` with no added flags (`AGENTS.md`, repository development contract).
- `testpaths = ["tests"]` (`pyproject.toml`): `tools/test_agy_run.py` is not collected by any gate, so new coverage goes under `tests/` (a6ootg F-04, still true).
- NO CODE-PINNING TESTS (GUIDING_PRINCIPLES P16): behavior only.
- ONE DEFINITION PER CONCEPT: `specs._spec_files` is the precedent for a single, recursion-plus-ignore-filter enumerator; this plan creates its plans twin rather than a third copy of `rglob` in `agy_run`.
- `agy_run` imports package siblings LOCALLY inside functions (`from agent_workflows import specs` in `resolve_spec`, `agy_sessions` in `run`).
- `requires-python = ">=3.9"`, so `Path.is_relative_to` is available (already used by `agy_run.resolve_spec`).

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | THE DEFECT REPRODUCES AS FILED. Temp git repo with `.aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md`: `resolve_ipd(root, "ab12cd", ("executed",))` -> `ScriptError No IPD matching 'ab12cd' found in plan states: executed.`; exact path -> resolves to `.aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md`. Cause: `_candidate_plans` calls `plans_base.glob("*.md")` per state dir. | In-process run at HEAD `cedb25f80`. |
| F-02 | SILENT MISROUTING CONFIRMED. `resolve_mode_and_target(root, parse_args(["--audit-only", "ab12cd"]))` -> `('prompt', 'ab12cd', '')`, because the positional path wraps `resolve_ipd` in `except ScriptError: pass` and then `resolve_spec`, then falls back to `return "prompt", target_str, ""`. The Turn-2 audit lookup in `agy_run.run` (`resolve_ipd(root, plan_id, ("executed",))` then fallback to `("pending",)`) would also miss a sharded executed copy. | Same run; `resolve_mode_and_target` and `run` read. |
| F-03 | NO PUBLIC CANONICAL PLAN ENUMERATOR EXISTS, BUT ONE WALK IS ALREADY THE MANIFEST'S. Recursive walks today: `plans_index.scan_plans` (rglob + `_EXCLUDE_NAMES` + `is_ignored_path` via `plan_entry`, then PARSES each file), `plans_archive.sweep_candidates` (rglob + `_EXCLUDE_NAMES`, NO ignore filter), `ipd_lint._iter_plan_files` (rglob + `_NON_IPD_BASENAMES`, NO ignore filter, resolves via `resolve_record_path`), `ipd_lint._default_pending_files` (pending only). Only `scan_plans` has the full filter set, and its docstring and `plans_archive`'s both promise "sharded plans stay visible". | Grep for `rglob` in the three modules; each body read. |
| F-04 | DELEGATING TO `scan_plans` ITSELF IS WRONG, EXTRACTING ITS WALK IS RIGHT. `scan_plans` reads and regex-parses every file: measured 0.297s / 0.265s on this repo's 1348 plans, versus 0.074s for the bare filtered walk (1347 files). The resolver needs paths, not metadata. Extracting the walk as `plan_files` keeps one definition (scan_plans consumes it) without paying the parse. 74ms inside a command that then spawns an agent turn is not user-perceptible, so no caching. | Both timed in process at HEAD `cedb25f80`. |
| F-05 | THE FLAT LOOP RESOLVES `README.md` AS AN IPD. Temp repo with `.aw/records/plans/pending/README.md`: `resolve_ipd(root, "README.md", ("pending",))` -> `.aw/records/plans/pending/README.md`. Every disposition dir in this repo carries a `README.md`. `plan_files` skips `_EXCLUDE_NAMES` (`INDEX.json`, `INDEX.md`, `STATUS.md`, `README.md`), fixing this. | Same temp repo; `ls .aw/records/plans/*/`. |
| F-06 | A RECURSIVE WALK NEEDS THE IGNORE FILTER. A prototype of `plan_files` over a temp repo with `pending/untracked/<plan>` and `pending/scratch/<plan>` (the latter ignored only by `.git/info/exclude`) returned only the sharded executed plan, so both the hardcoded `untracked` rule and the `git ls-files --ignored` path of `artifact_core.get_ignored_dirs` work when the root passed is the plans dir. | Prototype run in process. |
| F-07 | STATES ARE TOP-LEVEL DISPOSITIONS. `resolve_ipd`'s direct branch already checks `rel.parts[0] in states` relative to the plans root, so it accepts sharded exact paths; the candidate branch must use the same rule (`relative_to(base).parts[0]`) rather than enumerating per-state dirs, matching `plans_index.plan_entry`'s `disposition = rel.split("/", 1)[0]`. | `resolve_ipd` and `plan_entry` read. |
| F-09 | A DUPLICATE id6 ACROSS A SHARD SILENTLY MISRESOLVES TODAY. Review fixture (2026-10-12, HEAD `7e9129224`) with `executed/20260801-set-02-ab12cd-other.ipd.md` and `executed/202609/20260901-set-01-ab12cd-thing.ipd.md`: `resolve_ipd(root, "ab12cd", ("executed",))` returned the top-level `...-other.ipd.md` with no ambiguity error, and the positional path returned `('ipd', '.aw/records/plans/executed/20260801-set-02-ab12cd-other.ipd.md', '')`. So the ambiguity assertion is RED at base, not green. | In-process review probe. |
| F-10 | THE PROPOSED FILTER WORKS ON BOTH BASES. Same review fixture plus `pending/untracked/<plan>`, `pending/scratch/<plan>` (ignored only via `.git/info/exclude` `scratch/`), `pending/README.md`, and a legacy `.agents/plans/pending/<plan>`: the E-03 expression (`rglob` minus `_EXCLUDE_NAMES` minus `is_ignored_path(p, base, get_ignored_dirs(base))`) returned exactly the two `executed/` plans for `.aw/records/plans` (with `get_ignored_dirs` reporting `pending/scratch`) and exactly the legacy plan for `.agents/plans`. | In-process review probe. |
| F-08 | NO SPEC GOVERNS THIS. Specs mentioning `plans_index` (`sidecar-metadata-and-history`, `command-surface-redesign`, `attention-registry...`, metastore `4sd62s`) concern parsers and dispatch, none specifies resolver enumeration or forbids adding a function; `sidecar` requires parsers keep working unchanged, which E-03 preserves. No `.spec.md` is in Scope-Paths. | Grep across `.aw/records/specs/` for `resolve_ipd`, `_candidate_plans`, `scan_plans`, `plans_index`. |

## Proposed changes (ordered, validatable)

1. E-01 captures the reproduction (id6, filename, positional misroute, README) at the base commit.
2. E-02 adds `tests/test_agy_run_resolve_ipd_recursive.py` and shows it red.
3. E-03 extracts `plans_index.plan_files` and makes `scan_plans` use it with identical output.
4. E-04 makes `agy_run._candidate_plans` delegate to `plan_files`, filtered by top-level disposition and fenced to the repo root, with matching unchanged.
5. E-05 proves no regression across the targeted modules and the bare suite.

## Deferred / out of scope (with reason)

- MIGRATING `plans_archive.sweep_candidates` AND `ipd_lint._iter_plan_files` ONTO `plan_files` (F-03). Both lack the ignore filter, but changing them changes which plans the archive sweep moves and which the linter checks, a separate regression surface; this plan creates the canonical source they can adopt.
  - Carrier-Declined: neither has a measured user-visible failure today (`untracked/` plans are box-local and rare), so filing would be speculative; the canonical helper now exists for whoever next touches them.
- MOVING `tools/test_agy_run.py` UNDER `tests/`. Already carried by backlog `n8adhb` (a6ootg deferral).
  - Carrier: n8adhb
- TIGHTENING `resolve_ipd`'s `-{id6}-` substring match. Pre-existing, loud on ambiguity, independent of enumeration.
  - Carrier-Declined: it raises `is ambiguous` listing candidates rather than misresolving, so there is no defect to carry.

## Scope check

- Over-scope: none. `agent_workflows/plans_index.py` gains `plan_files` and `scan_plans` consumes it (E-03); `agent_workflows/agy_run.py` changes only `_candidate_plans` and the ambiguity renderer in `resolve_ipd` (`relative_to(root.resolve())`, E-04); `tests/test_agy_run_resolve_ipd_recursive.py` is new (E-02). Not edited: `artifact_core.py`, `plans_archive.py`, `ipd_lint.py`, `cli.py`, `tools/test_agy_run.py`, any spec.
- Under-scope: `plans_index.plan_entry` is also called by `cli.py`'s `aw find plans` explicit-path branch, so its own filter must stay; E-03 says so. The fixture must be a real git repo for `get_ignored_dirs`; E-02 uses `init_repo`.

## Required tests / validation

- New `tests/test_agy_run_resolve_ipd_recursive.py` (E-02 assertions 1-8b), red before for (1), (2), (6), (7), (8a), green after.
- `tests/test_plans_index.py`, `tests/test_plans_archive.py`, `tests/test_agy_run_resolve_spec_recursive.py` passing.
- `tools/test_agy_run.py` run by name, zero failures at its E-01 count.
- Live `scan_plans` entry count identical before/after E-03.
- Bare `python3 -m pytest` before and after with an empty failure-set delta by test id.
- `aw ipd lint` conforming at author and `--phase pre-transition`.

## Spec / documentation sync

N/A: no spec specifies how the agy runner enumerates plan candidates (F-08), and no user-facing doc advertises the broken behavior. No `.spec.md` is declared, so the run must announce no declared spec edits. The `plan_files` docstring records the recursion-plus-filter coupling for future readers.

## Open questions

### OQ-01: Which plan-enumeration source becomes canonical for `resolve_ipd`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Extract `plans_index.plan_files` from `scan_plans`' walk and delegate to it. Of the existing recursive walks only `scan_plans` applies both `_EXCLUDE_NAMES` and `is_ignored_path` (F-03), and it is the manifest the archive docstring promises keeps shards visible; delegating to `scan_plans` directly costs a full parse (F-04), so the walk is extracted and shared instead. Keeping the bases hardcoded in `agy_run` (not `resolve_record_path`) preserves in-repo scope (a6ootg F-10).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Paste the base commit hash, the fixture layout, and the verbatim output of all six E-01 probes (id6 and filename `ScriptError`, exact path resolving, positional `('prompt', 'ab12cd', '')`, README resolving, duplicate `dd44ee` silently returning one path), plus the `tools/test_agy_run.py` summary line and the base bare-suite summary line with its sorted failing ids. Produced by `agy_run.resolve_ipd` / `agy_run.resolve_mode_and_target` called in process.
  - Observed evidence: Verified.
    - `Base commit hash`: `73682920494e97c396e0304533a0fc8d917b1d52`
    - `Fixture layout`:
      ```
      <root>/
        .aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md
        .aw/records/plans/executed/20260801-set-02-dd44ee-other.ipd.md
        .aw/records/plans/executed/202609/20260901-set-03-dd44ee-dup.ipd.md
        .aw/records/plans/pending/README.md
      ```
    - `In-process probes at base commit`:
      ```
      --- PROBE 1 ---
      Raised: ScriptError: No IPD matching 'ab12cd' found in plan states: executed.
      --- PROBE 2 ---
      Raised: ScriptError: No IPD matching '20260901-set-01-ab12cd-thing.ipd.md' found in plan states: executed.
      --- PROBE 3 ---
      Resolved: .aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md
      --- PROBE 4 ---
      Returned: ('prompt', 'ab12cd', '')
      --- PROBE 5 ---
      Resolved: .aw/records/plans/pending/README.md
      --- PROBE 6 ---
      Resolved: .aw/records/plans/executed/20260801-set-02-dd44ee-other.ipd.md
      ```
    - `tools/test_agy_run.py` (relocated to `tests/test_agy_run.py` by a2748e441) summary line:
      `44 passed in 1.47s`
    - `Base bare-suite summary line`:
      `7994 passed, 4 skipped, 18 xfailed, 3 warnings in 1012.57s (0:16:52)`
    - `Sorted failing test ids`: `[]` (empty)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the pytest output of `tests/test_agy_run_resolve_ipd_recursive.py` at the base commit showing (1), (2), (6), (7) and (8a) failing and the rest passing, and quote that the module contains no source reading (`inspect`/`ast`/`read_text` of production modules).
  - Observed evidence: Verified.
    - `Base commit test run`:
      ```
      FAILED tests/test_agy_run_resolve_ipd_recursive.py::TestAgyRunResolveIpdRecursive::test_06_readme_not_resolvable_as_ipd
      FAILED tests/test_agy_run_resolve_ipd_recursive.py::TestAgyRunResolveIpdRecursive::test_08a_duplicate_id6_across_shard_raises_ambiguous
      FAILED tests/test_agy_run_resolve_ipd_recursive.py::TestAgyRunResolveIpdRecursive::test_01_resolve_sharded_plan_by_bare_id6
      FAILED tests/test_agy_run_resolve_ipd_recursive.py::TestAgyRunResolveIpdRecursive::test_02_resolve_sharded_plan_by_bare_filename
      FAILED tests/test_agy_run_resolve_ipd_recursive.py::TestAgyRunResolveIpdRecursive::test_07_positional_audit_resolves_sharded_plan
      ========================= 5 failed, 5 passed in 3.16s ==========================
      ```
    - `Passing assertions at base`: (3) `test_03_sharded_plan_not_returned_for_wrong_state`, (4) `test_04_flat_legacy_plan_resolves_by_id6`, (5a) `test_05a_untracked_plan_not_resolvable`, (5b) `test_05b_scratch_plan_ignored_by_exclude_not_resolvable`, (8b) `test_08b_preserved_exact_path_and_disallowed_state`.
    - `No source reading confirmation`: `tests/test_agy_run_resolve_ipd_recursive.py` imports neither `inspect` nor `ast`, never performs `read_text` or AST inspection on production modules, and verifies observable runtime resolution outputs and exceptions only.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the `git diff` of `agent_workflows/plans_index.py`, the `tests/test_plans_index.py` pass line, and the live `len(plans_index.scan_plans(Path(".aw/records/plans").resolve())[0])` before and after (must be equal).
  - Observed evidence:
    - `git diff agent_workflows/plans_index.py`:
      ```diff
      diff --git a/agent_workflows/plans_index.py b/agent_workflows/plans_index.py
      index 077952b2c..cf8b9da6c 100644
      --- a/agent_workflows/plans_index.py
      +++ b/agent_workflows/plans_index.py
      @@ -127,6 +127,32 @@ def plan_entry(
           return entry, drift


      +def plan_files(
      +    plans_dir: Path, *, ignored_dirs: Optional[set[str]] = None
      +) -> List[Path]:
      +    """Return sorted list of plan file Paths under ``plans_dir``.
      +
      +    This is THE canonical definition of which files are plans.
      +    Recursion (`rglob`) and the ignored-path filter are COUPLED: a recursive walk without
      +    the ignored-path filter returns box-local `untracked/` plans that are never committed.
      +    (See backlog item `mlcbk9` and `specs._spec_files` docstring recording the same lesson.)
      +
      +    Skips `_EXCLUDE_NAMES` (`INDEX.json`, `INDEX.md`, `STATUS.md`, `README.md`) and any path
      +    matching `_core.is_ignored_path(p, plans_dir, ignored_dirs)`.
      +    For any returned plan `p`, its top-level lifecycle disposition is `p.relative_to(plans_dir).parts[0]`.
      +    """
      +    if not plans_dir.is_dir():
      +        return []
      +    if ignored_dirs is None:
      +        ignored_dirs = _core.get_ignored_dirs(plans_dir)
      +    return [
      +        p
      +        for p in sorted(plans_dir.rglob("*.md"))
      +        if p.name not in _EXCLUDE_NAMES
      +        and not _core.is_ignored_path(p, plans_dir, ignored_dirs)
      +    ]
      +
      +
       def scan_plans(plans_dir: Path) -> Tuple[List[PlanEntry], List[_core.Drift]]:
           """Recursively scan every plan under ``plans_dir``; return (entries, drift).

      @@ -141,7 +167,7 @@ def scan_plans(plans_dir: Path) -> Tuple[List[PlanEntry], List[_core.Drift]]:
           if not plans_dir.is_dir():
               return entries, drift
           ignored_dirs = _core.get_ignored_dirs(plans_dir)
      -    for p in sorted(plans_dir.rglob("*.md")):
      +    for p in plan_files(plans_dir, ignored_dirs=ignored_dirs):
               res = plan_entry(plans_dir, p, ignored_dirs=ignored_dirs)
               if res is not None:
                   entry, item_drift = res
      ```
    - `tests/test_plans_index.py` pass line: `18 passed in 2.00s`
    - Live `len(plans_index.scan_plans(Path(".aw/records/plans").resolve())[0])`:
      - Before edit: `1462`
      - After edit: `1462` (equal)
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the `git diff` of `agent_workflows/agy_run.py` showing the three matching expressions and both error message texts unchanged, the renderer now `relative_to(root.resolve())`, and a local `plans_index` import; paste the new module passing in full; paste the `tools/test_agy_run.py` summary at its E-01 count with zero failures.
  - Observed evidence:
    - `git diff agent_workflows/agy_run.py`:
      ```diff
      diff --git a/agent_workflows/agy_run.py b/agent_workflows/agy_run.py
      index 2454606dc..7f5910b91 100755
      --- a/agent_workflows/agy_run.py
      +++ b/agent_workflows/agy_run.py
      @@ -326,15 +326,38 @@ def repository_root(start: Path) -> Path:


       def _candidate_plans(root: Path, states: Iterable[str]) -> list[Path]:
      -    found: list[Path] = []
      -    for state in set(states):
      -        for plans_base in (
      -            root / ".agents" / "plans" / state,
      -            root / ".aw" / "records" / "plans" / state,
      -        ):
      -            if plans_base.is_dir():
      -                found.extend(plans_base.glob("*.md"))
      -    return sorted(set(found))
      +    # Backlog mlcbk9 / IPD m734rl: Delegate enumeration to plans_index.plan_files rather
      +    # than re-implementing a recursive walk. Non-recursion in the previous glob masked
      +    # the lack of an ignored-path filter; plans_index.plan_files couples the recursive walk,
      +    # the mandatory ignored-path filter (artifact_core.is_ignored_path), the exclusion
      +    # of non-plan files (README.md, INDEX.md, STATUS.md), and legacy root compatibility.
      +    # We import locally to avoid introducing top-level package imports in agy_run.
      +    from agent_workflows import plans_index
      +
      +    resolved_root = root.resolve()
      +    target_states = set(states)
      +    candidates: list[Path] = []
      +    for plans_base in (
      +        root / ".agents" / "plans",
      +        root / ".aw" / "records" / "plans",
      +    ):
      +        if not plans_base.is_dir():
      +            continue
      +        for p in plans_index.plan_files(plans_base):
      +            try:
      +                rel = p.relative_to(plans_base)
      +                if rel.parts and rel.parts[0] in target_states:
      +                    candidates.append(p)
      +            except ValueError:
      +                continue
      +
      +    return sorted(
      +        {
      +            p.resolve()
      +            for p in candidates
      +            if p.resolve().is_relative_to(resolved_root)
      +        }
      +    )


       def _is_id6(value: str) -> bool:
      @@ -368,6 +391,8 @@ def resolve_ipd(root: Path, value: str, states: Iterable[str]) -> Path:
                   )
               return resolved

      +    # Backlog mlcbk9: Matching branches, error messages, and direct.is_file()
      +    # are preserved unchanged. Ambiguity rendering uses root.resolve().
           candidates = _candidate_plans(root, states)
           if value.endswith(".md") or "/" in value or "\\" in value:
               matches = [p for p in candidates if p.name == supplied.name]
      @@ -382,7 +407,7 @@ def resolve_ipd(root: Path, value: str, states: Iterable[str]) -> Path:
                   f"No IPD matching {value!r} found in plan states: {state_text}."
               )
           if len(matches) > 1:
      -        rendered = "\n".join(f"  - {p.relative_to(root)}" for p in matches)
      +        rendered = "\n".join(f"  - {p.relative_to(root.resolve())}" for p in matches)
               raise ScriptError(f"IPD reference {value!r} is ambiguous:\n{rendered}")
           return matches[0].resolve()
      ```
    - New module passing in full:
      `10 passed in 2.65s` (`tests/test_agy_run_resolve_ipd_recursive.py`)
    - `tests/test_agy_run.py` summary at E-01 count with zero failures:
      `44 passed in 1.35s`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste the targeted-module pytest output, the two bare `python3 -m pytest` summary lines (before and after), the failure-set delta stated as test ids (must be empty), and the re-run E-01 probes now returning the sharded path, mode `ipd`, `ScriptError` for README, and `is ambiguous` listing both `dd44ee` paths.
  - Observed evidence: Verified.
    - `Targeted-module pytest output`:
      `52 passed in 4.85s` (`tests/test_plans_index.py`, `tests/test_plans_archive.py`, `tests/test_agy_run_resolve_ipd_recursive.py`, `tests/test_agy_run_resolve_spec_recursive.py`)
    - `Bare python3 -m pytest summary lines`:
      - Before: `7994 passed, 4 skipped, 18 xfailed, 3 warnings in 1012.57s (0:16:52)`
      - After: `8004 passed, 4 skipped, 18 xfailed, 3 warnings in 946.62s (0:15:46)`
    - `Failure-set delta stated as test ids`:
      `empty` (`set()`)
    - `Re-run E-01 in-process probes after fix`:
      ```
      --- PROBE 1 ---
      Resolved: .aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md
      --- PROBE 2 ---
      Resolved: .aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md
      --- PROBE 3 ---
      Resolved: .aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md
      --- PROBE 4 ---
      Returned: ('ipd', '.aw/records/plans/executed/202609/20260901-set-01-ab12cd-thing.ipd.md', '')
      --- PROBE 5 ---
      Raised: ScriptError: No IPD matching 'README.md' found in plan states: pending.
      --- PROBE 6 ---
      Raised: ScriptError: IPD reference 'dd44ee' is ambiguous:
        - .aw/records/plans/executed/20260801-set-02-dd44ee-other.ipd.md
        - .aw/records/plans/executed/202609/20260901-set-03-dd44ee-dup.ipd.md
      ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. OQ-01 is resolved; none remain open. Commit only the `- Scope-Paths:` files plus this plan, through `aw commit <plan> -- <paths>`, verifying `git diff --cached --name-only` lists only those; never `git add -A`, never `-a`, never push. Paste ACTUAL runner output for every test claim. No `.spec.md` is declared and none may be edited.

SCOPE FENCE (declared for runner reconciliation): `agent_workflows/plans_index.py` (E-03), `agent_workflows/agy_run.py` (E-04), `tests/test_agy_run_resolve_ipd_recursive.py` (E-02). Do NOT edit `artifact_core.py`, `plans_archive.py`, `ipd_lint.py`, `cli.py`, `specs.py` or `tools/test_agy_run.py`; a necessary out-of-scope edit is made and justified to `aw ipd finalize` with `--scope-reason`.

NEVER LAUNCH A REAL AGENT: every `aw agy exec` probe uses `--agy <stub> --no-audit`.

DO NOT TIGHTEN MATCHING and do not migrate other walkers (deferred section).

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` has pasted evidence, require `aw ipd lint --phase pre-transition` conforming, then reach `executed/` through `aw ipd finalize` (the runner performs it under `aw oc run` / `aw agy run`; by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-`git mv` or hand-edit `- Status: executed`. Backlog `mlcbk9` is set `graduated` by the authoring runner; do not set it `done` from this plan and do not clear its `Blocks-Release`.
