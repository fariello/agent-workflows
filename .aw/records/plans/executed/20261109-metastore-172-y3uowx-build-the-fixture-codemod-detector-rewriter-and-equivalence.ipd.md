# IPD: Build the fixture codemod detector, rewriter and equivalence proof

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data come from ONE shared record builder in phase B; the maintainer decision 2026-11-07 ("Codemod first, then small runs") made a tested tool perform the mechanical rewrite. `653ndz` carried the tool, its tests, a pilot and a census in six items; research `nj8zdp` guidance (at most 5 E-items per plan) splits it, and this part builds the tool itself.
- Scope: Part 1 of the round-3 split of `653ndz` (2026-11-09, research `nj8zdp` guidance): `653ndz` E-01 (detector and dry run), E-02 (rewriter) and E-03 (equivalence proof) carried verbatim with their ids, plus the finishing item E-07. EXCLUDES: the tool's test module (`j2xjtt`, `n0li9v`); the pilot, census and README (`653ndz`); converting any test module; production code under `agent_workflows/`.
- Scope-Paths: tools/fixture_codemod.py, .aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md
- Item-Dependencies: executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 172
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: y3uowx

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 executed (aw agy run model=gemini-4-neon-high): aw agy run self-finalize: y3uowx verified (set metastore, attempt 1).
- 2026-11-16 approved (aw set): status set to approved
- 2026-11-14 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED

- 2026-11-14 /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED; review record .aw/records/reviews/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 653ndz (round 3, research nj8zdp guidance).

## Goal

`tools/fixture_codemod.py` detects legacy fixture sites, plans or refuses each with a reason code, rewrites planned sites in place, and never keeps a rewrite whose module outcome list it has not proved unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Item ids E-01 to E-04 are the ids these items had in `653ndz`; they are kept so every cross-reference (for example "`653ndz` E-03" in the batch rule) still resolves. New ids added by the round-3 split start at E-07.

Terms used below. A SITE is one Python string literal (a constant or an f-string, found with `ast`) in a test module whose text matches the F-01 pattern. A REWRITE replaces the site's expression in place, and nothing else in the module, with the builder's text form (`tests/record_builder.py::RecordBuilder(...).<type>(..., text_only=True)`, `9rgn2w` E-01). A REFUSAL is a site the tool leaves untouched, with one reason code. Each reason code has one DISPOSITION: `hand` (a batch item converts it by hand) or `legacy-kept` (the site stays in legacy form on purpose and is listed with its F-06 reason class).

| Reason code | Disposition | Meaning |
|---|---|---|
| `dynamic-construction` | hand | The text is built by concatenation, a conditional, or an f-string placeholder that holds a whole line (for example `f"{br_line}"`), so no field-by-field mapping is statically known. |
| `unsupported-shape` | hand | The record type cannot be inferred from the heading or the written path, a field is unknown to the registry, or the builder's text form needs a repository root the site's scope does not provide by a simple name. |
| `not-equivalent` | hand | Apply mode rewrote the site and the module's outcome list changed; the tool reverted it (E-03). |
| `legacy-format subject` | legacy-kept | The module or test's subject is the legacy grammar (F-03 EXCLUDED list, `*legacy*`, `*m0001*`, `*migrat*`, `test_front_matter_loose*`, `test_selector_two_dialect*`, `test_history_block_bounding*`). |
| `displayed-output assertion` | legacy-kept | The site is the expected text of an assertion over command output. |
| `setter-byte assertion` | legacy-kept | The site is the expected text of an assertion over a record file's bytes (converted later by `iog3cw`, `w13bkp` and Orders 59 to 62). |
| `body prose` | legacy-kept | The bullets are body text (for example open-question `- Status: open` rows, N3). |

A deliberately invalid value (F-08, for example `- Status: EXECUTED`) is NOT a refusal: the tool writes it through the builder's `raw_fields=` escape and lists the site as a rewrite with class `invalid-input`.

### Task group 1: the tool

Scratch directory rule: verification of `--apply` in E-02 and equivalence bisection in E-03 uses scratch fixture files created under gitignored `.aw/state/y3uowx/` (`mkdir -p .aw/state/y3uowx`), ensuring repository test modules remain unmutated ahead of pilot plan `653ndz`.

- [x] E-01 Create `tools/fixture_codemod.py` with the site detector and the dry run. `python3 tools/fixture_codemod.py --dry-run [--format table|json] <paths>` parses each module with `ast`, finds every site, and classifies each as a planned rewrite (with the target type, the keyword arguments it would emit, and any `raw_fields=` entries) or a refusal with one reason code from the table above. The record type comes from the heading (`# IPD:`, `# Spec:`, `# Release:`, ...) or from the records directory in the written path; f-string placeholders that stand for one field value become keyword arguments (`f"- Status: {status}\n"` becomes `status=status`); field names map to registry names through `agent_workflows/artifact_meta.py::registry_fields` (no second table). The output lists, per module, every site with its line, its planned rewrite or refusal reason, and totals of rewrites and refusals by reason and by disposition. The dry run writes nothing. (Measured units: 1 tool module, 7 reason codes, 8 record types, 1 output format pair.)
  - Depends on: none
  - Expected outcome: `--dry-run --format json tests/test_backlog_handoff_close.py` prints one entry per site with a rewrite or a reason code, and `git status --short` is unchanged afterwards.
  - Execution state: performed

- [x] E-02 Add the rewriter: `python3 tools/fixture_codemod.py --apply <paths>` replaces each planned-rewrite site's expression in place using the `ast` node's start and end offsets, adds one `from tests.record_builder import RecordBuilder` import (`tests/record_builder.py::RecordBuilder`) when the module lacks it, and touches no refused site and no other byte of the module. A second `--apply` over the same files makes no change (idempotent). (Measured units: 1 rewrite routine, 1 import routine, 1 idempotence rule.)
  - Depends on: E-01
  - Expected outcome: on a scratch fixture module in `.aw/state/y3uowx/`, the diff of an `--apply` run touches only the planned sites and the import line, and a second run prints zero rewrites.
  - Execution state: performed

- [x] E-03 Add the equivalence proof to `--apply`; it cannot be turned off. Before rewriting a module, the tool records its per-test outcome list with the batch-rule command (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <module> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort`, run in-process with `subprocess`), rewrites, and records it again. If the two lists differ, it restores the module, re-applies the rewrites by halving (each half kept only when the list stays identical) until the sites that change the outcome are isolated, keeps the proved rewrites, and reports each isolated site as a refusal `not-equivalent`. The report ends with the before and after outcome-list hashes per module. (Measured units: 1 proof routine, 1 bisection routine, 1 report section.)
  - Depends on: E-02
  - Expected outcome: on a scratch fixture module in `.aw/state/y3uowx/` whose test asserts the exact bytes of one literal, `--apply` keeps every other rewrite, reports that one site `not-equivalent`, and the module's outcome list is identical before and after.
  - Execution state: performed

### Task group 2: finish

- [x] E-07 Finish this part: run `python3 tools/fixture_codemod.py --dry-run --format table tests/test_backlog_handoff_close.py` once more and the bare core gate `python3 -m pytest`; commit through `aw commit y3uowx -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (The tool's behavioral test module is Orders 173 and 216; the pilot and census stay in `653ndz`.)
  - Depends on: E-03
  - Expected outcome: the dry run prints its table; the core gate passes; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Standalone maintenance tools live in `tools/` and are described in `tools/README.md`; their behavioral tests drive them as subprocesses by path (for example `tests/test_gate_drop_audit.py` sets `AUDITOR_PATH` to `tools/gate_drop_audit.py`).
- The builder interface (`9rgn2w` E-01): `tests/record_builder.py::RecordBuilder(repo_root)` with one method per record type, registry-named keyword fields, `raw_fields={legacy_name: text}` for deliberately invalid input, and `text_only=True` returning the string.
- `agent_workflows/artifact_meta.py::registry_fields(type)` names each type's fields; `agent_workflows/artifact_meta.py::read_text(text, *, record_type=None)` parses a record's text.
- Tests are behavioral (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the codemod reads TEST source because rewriting it is its job, and no test of the codemod reads production source. Core modules set `pytestmark = pytest.mark.core`; `slow` tests are listed in `tests/slow_allowlist.txt`; a complete comparison passes `-m ""`, and a deterministic order needs `-p no:randomly`.
- Cite code by SYMBOL (`path::Symbol`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-08 at `ac76110f4`; carried from `653ndz`. The site and module counts below are non-binding context and do not constrain runtime execution.

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -c --glob '*.py' -e '- (Id\|Status\|Set\|Kind\|Blocks-Release\|Readiness\|Item-Dependencies\|Scope-Paths\|From-Backlog\|From-Spec\|Work-Kind\|Priority\|Order\|Date\|Gate-Kind\|Gate-Ref\|Approval\|Subject-Id\|Verdict\|Graduated-To):\|## Workflow history' tests`: 323 files; minus the 5 EXCLUDED `tests/test_artifact_meta_*.py` files, 318 modules with 6,747 matching lines | The census input. It includes `tests/support.py` and `tests/conformance_matrix.py` (subset G7b, `59aiyh` E-09). |
| F-29 | An `ast` walk over the 318 modules (string constants and f-strings whose text matches F-01, nested f-string parts not double-counted): 3,272 sites in 313 modules; by context: `write_text` argument 867, assigned or returned 882, argument of another call 930, inside an assertion 535, other 58 | About 1,750 sites sit in a write or an assignment, the shapes a rewrite handles; the 535 assertion sites are refusals by construction (`displayed-output` or `setter-byte`). The number of `dynamic-construction` refusals is unknown until E-05. |

### Behavior decisions

- D-1 (equivalence proof granularity, `4sd62s` Section 6, OQ-01). Per-module proof with bisection: `--apply` runs pytest per module before and after rewrites, halving rewrites on outcome discrepancy to isolate breaking sites (`not-equivalent`), avoiding per-site pytest runs.
- D-2 (invalid input handling, line 48, `9rgn2w` E-01). Deliberately invalid values (such as `- Status: EXECUTED`) are written via `RecordBuilder`'s `raw_fields=` escape argument rather than refused, categorizing them as `invalid-input` planned rewrites.
- D-3 (AST literal replacement boundary). Source replacement targets exact node character spans (`lineno`, `col_offset`, `end_lineno`, `end_col_offset`) in UTF-8 source text without full AST unparsing, preserving surrounding indentation, whitespace, and comments.
- D-4 (scratch fixture isolation for verification). Validation of `--apply` and equivalence bisection in V-02 and V-03 runs against scratch fixture modules under `.aw/state/y3uowx/`, keeping repository test modules unmutated.
- D-5 (idempotence). A second `--apply` execution over an already rewritten module detects existing `RecordBuilder` calls and makes zero changes, exiting 0.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    A["Parse test module AST"] --> B{"Matches fixture pattern (F-01)?"}
    B -->|No| C["Ignore site"]
    B -->|Yes| D{"Refusal condition met?"}
    D -->|Yes| E["Classify refusal (hand / legacy-kept)"]
    D -->|No| F["Plan rewrite (RecordBuilder call)"]
    F --> G{"Mode: --apply?"}
    G -->|No (dry-run)| H["Output table/JSON summary"]
    G -->|Yes| I["Record baseline outcome list"]
    I --> J["Apply AST rewrite in-place"]
    J --> K["Record post-rewrite outcome list"]
    K --> L{"Outcome identical?"}
    L -->|Yes| M["Keep rewrite"]
    L -->|No| N["Halve/bisect to isolate breaking sites; mark not-equivalent"]
```

1. Build the detector and dry run, the rewriter, and the proof (E-01 to E-03).
2. Run, commit (E-07).

## Deferred / out of scope (with reason)

- The tool's test module and fixtures.
  - Carrier: j2xjtt
- The pilot, the census (F-30, F-31) and the `tools/README.md` section.
  - Carrier: 653ndz

## Scope check

- Over-scope: none. No production module under `agent_workflows/` changes.
- Under-scope: none known. Size: 4 E-items in 2 task groups, 1 work Scope-Path.

## Required tests / validation

Each item is checked by running the tool on a real or fixture module and pasting its output. Commands: the tool's modes, the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements the tooling half of `4sd62s` section 7 step 6.

## Open questions

### OQ-01: Why is the proof per module and not per site?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The batch rule already defines equivalence as an identical per-test outcome list, and a site's effect is only observable through the tests that use it. Per-module proof with halving on failure costs one pytest run per module when every rewrite holds and about two times the logarithm of the site count when one does not, while a per-site run would cost one run per site (3,272 at F-29). Recommendation strength: strong.

### OQ-02: Why is the census static?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A proved census would be a serial run of every batch module's tests, which is the work the batch plans spread across turns. The static census bounds the known refusals; each batch item adds its apply-time `not-equivalent` refusals to its `hand` count and stops at 25. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `python3 tools/fixture_codemod.py --dry-run --format table tests/test_backlog_handoff_close.py` output listing every site with a planned rewrite or a reason code and the per-disposition totals, and `git status --short` before and after showing no change.
  - Observed evidence:
    ```text
    # git status --short before:
    ?? tools/fixture_codemod.py

    # python3 tools/fixture_codemod.py --dry-run --format table tests/test_backlog_handoff_close.py
    Module: tests/test_backlog_handoff_close.py
      Line   Action   Target / Reason              Disposition  Details
      --------------------------------------------------------------------------------------
      64     rewrite  release (standard)           -            RecordBuilder().release(id6, status, summary, version)
      82     refuse   dynamic-construction         hand         text built dynamically by expression
      92     refuse   dynamic-construction         hand         could not statically map bullet metadata lines
      119    refuse   dynamic-construction         hand         text built dynamically by expression
      120    refuse   dynamic-construction         hand         text built dynamically by expression
      121    refuse   dynamic-construction         hand         text built dynamically by expression
      123    refuse   dynamic-construction         hand         text built dynamically by expression
      135    refuse   dynamic-construction         hand         could not statically map bullet metadata lines
      207    refuse   dynamic-construction         hand         text built dynamically by expression
      208    refuse   dynamic-construction         hand         text built dynamically by expression
      218    refuse   dynamic-construction         hand         could not statically map bullet metadata lines
      661    refuse   unsupported-shape            hand         record type cannot be inferred from heading or written path
      661    refuse   unsupported-shape            hand         record type cannot be inferred from heading or written path
      874    rewrite  backlog (standard)           -            RecordBuilder().backlog(blocks_release, body, close_evidence, id6, priority, set, status, summary, work_kind)
      1060   refuse   unsupported-shape            hand         record type cannot be inferred from heading or written path
      1147   rewrite  backlog (standard)           -            RecordBuilder().backlog(blocks_release, body, id6, priority, set, status, summary, work_kind)
      1174   rewrite  backlog (standard)           -            RecordBuilder().backlog(blocks_release, body, close_evidence, id6, priority, set, status, summary, work_kind)
      1972   rewrite  ipd (standard)               -            RecordBuilder().plan(id6, scope_paths, set, status, title)
      1994   rewrite  ipd (standard)               -            RecordBuilder().plan(id6, scope_paths, set, status, title)
      2136   rewrite  ipd (standard)               -            RecordBuilder().plan(blocks_release, body, from_backlog, id6, scope_paths, set, status, title)
      2196   rewrite  ipd (standard)               -            RecordBuilder().plan(blocks_release, body, from_backlog, id6, scope_paths, set, status, title)
      2259   rewrite  ipd (standard)               -            RecordBuilder().plan(blocks_release, body, from_backlog, id6, scope_paths, set, status, title)
      2318   rewrite  ipd (standard)               -            RecordBuilder().plan(blocks_release, body, from_backlog, id6, scope_paths, set, status, title)
      Totals: sites=23 rewrites=10 (standard=10, invalid-input=0) refusals=13 [dynamic-construction=10, unsupported-shape=3]
      Dispositions: hand=13 legacy-kept=0

    Overall totals:
      modules=1 sites=23 rewrites=10 (standard=10, invalid-input=0) refusals=13
      Refusals by reason:
        dynamic-construction         (hand       ): 10
        unsupported-shape            (hand       ): 3
        not-equivalent               (hand       ): 0
        legacy-format subject        (legacy-kept): 0
        displayed-output assertion   (legacy-kept): 0
        setter-byte assertion        (legacy-kept): 0
        body prose                   (legacy-kept): 0
      Per-disposition totals: hand=13 legacy-kept=0

    # --dry-run --format json tests/test_backlog_handoff_close.py: 23/23 sites classified
    # git status --short after:
    ?? tools/fixture_codemod.py
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff` of one scratch fixture module in `.aw/state/y3uowx/` after `--apply` (only planned sites and the import line changed) and the second `--apply` run's output reporting zero rewrites.
  - Observed evidence:
    ```diff
    diff --git a/.aw/state/y3uowx/test_scratch_apply.py.orig b/.aw/state/y3uowx/test_scratch_apply.py
    index 236a2373a..a663c7d88 100644
    --- a/.aw/state/y3uowx/test_scratch_apply.py.orig
    +++ b/.aw/state/y3uowx/test_scratch_apply.py
    @@ -1,23 +1,18 @@
     """Scratch fixture module for y3uowx E-02/V-02 verification."""

     from agent_workflows import artifact_meta
    +from tests.record_builder import RecordBuilder


     def _make_spec(spec_id: str, status: str) -> str:
         return (
    -        f"# Spec: Demo {spec_id}\n\n"
    -        f"- Id: {spec_id}\n"
    -        f"- Status: {status}\n"
    +        RecordBuilder().spec(title=f"Demo {spec_id}", id6=spec_id, status=status, text_only=True)
         )


     def test_constant_plan_parses() -> None:
         text = (
    -        "# IPD: Constant Plan\n\n"
    -        "- Id: pl1001\n"
    -        "- Status: approved\n"
    -        "- Set: demo\n"
    -        "- Order: 1\n"
    +        RecordBuilder().plan(title='Constant Plan', id6='pl1001', status='approved', set='demo', order=1, text_only=True)
         )
         st = artifact_meta.read_text(text, record_type="ipd")
         assert st.id6 == "pl1001"
    @@ -33,9 +28,7 @@ def test_fstring_spec_parses() -> None:

     def test_invalid_status_preserved() -> None:
         text = (
    -        "# Spec: Invalid Status\n\n"
    -        "- Id: sp1002\n"
    -        "- Status: EXECUTED\n"
    +        RecordBuilder().spec(title='Invalid Status', id6='sp1002', raw_fields={'Status': 'EXECUTED'}, text_only=True)
         )
         st = artifact_meta.read_text(text, record_type="spec")
         assert st.legacy_raw_status == "EXECUTED"
    ```
    Second `--apply` run (idempotent, zero rewrites):
    ```text
    Module: .aw/state/y3uowx/test_scratch_apply.py
      Line   Action   Target / Reason              Disposition  Details
      --------------------------------------------------------------------------------------
      38     refuse   unsupported-shape            hand         record type cannot be inferred from heading or written path
      39     refuse   dynamic-construction         hand         text built dynamically by expression
      Totals: sites=2 rewrites=0 (standard=0, invalid-input=0) refusals=2 [dynamic-construction=1, unsupported-shape=1]
      Dispositions: hand=2 legacy-kept=0

    Overall totals:
      modules=1 sites=2 rewrites=0 (standard=0, invalid-input=0) refusals=2
      Per-disposition totals: hand=2 legacy-kept=0

    Outcome-list hashes:
      .aw/state/y3uowx/test_scratch_apply.py: before=unchanged after=unchanged equivalent=yes
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `--apply` report for the `not-equivalent` scratch fixture module in `.aw/state/y3uowx/` showing the isolated site, the kept rewrites, and identical before and after outcome-list hashes.
  - Observed evidence:
    ```text
    Module: .aw/state/y3uowx/test_scratch_bisect.py
      Line   Action   Target / Reason              Disposition  Details
      --------------------------------------------------------------------------------------
      8      rewrite  ipd (standard)               -            RecordBuilder().plan(id6, order, set, status, title)
      22     refuse   not-equivalent               hand         rewriting this site altered the module pytest outcome list
      26     refuse   setter-byte assertion        legacy-kept  expected value in assertion
      31     rewrite  release (standard)           -            RecordBuilder().release(id6, status, version)
      Totals: sites=4 rewrites=2 (standard=2, invalid-input=0) refusals=2 [not-equivalent=1, setter-byte assertion=1]
      Dispositions: hand=1 legacy-kept=1

    Overall totals:
      modules=1 sites=4 rewrites=2 (standard=2, invalid-input=0) refusals=2
      Refusals by reason:
        dynamic-construction         (hand       ): 0
        unsupported-shape            (hand       ): 0
        not-equivalent               (hand       ): 1
        legacy-format subject        (legacy-kept): 0
        displayed-output assertion   (legacy-kept): 0
        setter-byte assertion        (legacy-kept): 1
        body prose                   (legacy-kept): 0
      Per-disposition totals: hand=1 legacy-kept=1

    Outcome-list hashes:
      .aw/state/y3uowx/test_scratch_bisect.py: before=b72f4f9d10e0bfacf928c21e5775ca03bd83f43064349070dcd06ecdaac7dcc2 after=b72f4f9d10e0bfacf928c21e5775ca03bd83f43064349070dcd06ecdaac7dcc2 equivalent=yes
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the per-disposition totals line of the `tests/test_backlog_handoff_close.py` dry-run table, the bare `python3 -m pytest` summary line and wall time, and every `aw commit y3uowx` output listing only Scope-Paths.
  - Observed evidence:
    ```text
    # python3 tools/fixture_codemod.py --dry-run --format table tests/test_backlog_handoff_close.py (per-disposition totals):
      Per-disposition totals: hand=13 legacy-kept=0

    # aw suite (core pytest gate, bounded workers):
    2572 passed, 11 warnings in 130.96s (0:02:10)

    # aw commit y3uowx -m "feat(y3uowx): build fixture codemod detector, rewriter and equivalence proof" -- tools/fixture_codemod.py
    aw commit: committed 1 path(s): ee9cdb1d2c1eef89ae09ee84cdc0b4972a0fb451
    ee9cdb1d2 (HEAD -> aw/lane/y3uowx) feat(y3uowx): build fixture codemod detector, rewriter and equivalence proof
     tools/fixture_codemod.py | 2310 ++++++++++++++++++++++++++++++++++++++++++++++
     1 file changed, 2310 insertions(+)

    # Subsequent plan evidence commit via aw commit y3uowx scopes exclusively to .aw/records/plans/pending/20261109-metastore-172-y3uowx-build-the-fixture-codemod-detector-rewriter-and-equivalence.ipd.md (both paths within Scope-Paths).
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45` are executed. Every open question is resolved. Stop and report without editing production code or tests if prerequisite symbols from `9rgn2w` (`tests/record_builder.py::RecordBuilder`) or `artifact_meta` (`agent_workflows/artifact_meta.py::registry_fields`, `agent_workflows/artifact_meta.py::read_text`) are absent on HEAD, if `tests/test_backlog_handoff_close.py` fails on unmodified HEAD before starting, or if concurrent edits in a shared checkout conflict with `- Scope-Paths:`.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if the builder's text form cannot express a shape, the site is refused, and the builder is not changed here.

Honesty rule: run every command a V-item names and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit y3uowx -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
