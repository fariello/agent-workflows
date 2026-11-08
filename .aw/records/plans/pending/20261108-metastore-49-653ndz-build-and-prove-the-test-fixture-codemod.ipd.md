# IPD: Build and prove the test-fixture codemod

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder (`tests/record_builder.py`, built by `9rgn2w`, Order 37) in phase B, so that the cutover (Order 13, `cxxmyv`) changes the builder and not hundreds of test files. Measured 2026-11-08 at `ac76110f4`: the F-01 `rg -c` pattern matches 6,747 lines in 318 batch modules (323 files minus the 5 EXCLUDED `tests/test_artifact_meta_*.py`); a Python `ast` walk over the same 318 files finds 3,272 string-literal sites (2,636 plain constants, 636 f-strings) that carry at least one legacy bullet or `## Workflow history`, of which 867 are the argument of a `write_text` call, 882 are assigned or returned, 930 are passed to another call and 535 sit inside an assertion. The batch plans (`x05v02`, `7qxey9`, `nbfg7w`, `1upea0`) each held items such as "convert these 17 modules, 738 lines" that hide hundreds of hand edits. Maintainer decision 2026-11-07 ("Codemod first, then small runs"): build a tested tool that performs the mechanical rewrite, and size each batch item by the tool's measured refusals, not by line counts.
- Scope: A standalone tool `tools/fixture_codemod.py` with a static site detector, a dry run, an apply mode that rewrites only sites whose module outcome list it proved unchanged, its behavioral test module and fixtures, a throwaway pilot on three real modules, and a census over all 318 batch modules recorded as tracked Findings tables F-30 (per module) and F-31 (per batch subset) that the batch plans cite. EXCLUDES: converting any test module on `main` (the batch plans Orders 38 to 40, 50, and `59aiyh` E-09); the builder itself (`9rgn2w`); setter-byte assertion conversion (`iog3cw`, `w13bkp`, Orders 59 to 62); production code under `agent_workflows/`.
- Scope-Paths: tools/fixture_codemod.py, tests/test_fixture_codemod.py, tests/fixtures/fixture_codemod/**, tools/README.md, tests/slow_allowlist.txt, .aw/records/plans/pending/20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md
- Item-Dependencies: executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 49
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 653ndz

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-08 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): created per maintainer decision 2026-11-07 ("Codemod first, then small runs"); the batch plans x05v02, 7qxey9, nbfg7w and 1upea0 run this tool and hand-convert only its census refusals.

## Goal

A tested `tools/fixture_codemod.py` rewrites inline legacy fixture text in test modules into `tests/record_builder.py` calls, never rewrites a site whose module outcome list it has not proved unchanged, and a tracked census tells each batch item exactly how many refusals it must convert by hand.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Terms used below. A SITE is one Python string literal (a constant or an f-string, found with `ast`) in a test module whose text matches the F-01 pattern. A REWRITE replaces the site's expression in place, and nothing else in the module, with the builder's text form (`RecordBuilder(...).<type>(..., text_only=True)`, `9rgn2w` E-01). A REFUSAL is a site the tool leaves untouched, with one reason code. Each reason code has one DISPOSITION: `hand` (a batch item converts it by hand) or `legacy-kept` (the site stays in legacy form on purpose and is listed with its F-06 reason class).

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

- [ ] E-01 Create `tools/fixture_codemod.py` with the site detector and the dry run. `python3 tools/fixture_codemod.py --dry-run [--format table|json] <paths>` parses each module with `ast`, finds every site, and classifies each as a planned rewrite (with the target type, the keyword arguments it would emit, and any `raw_fields=` entries) or a refusal with one reason code from the table above. The record type comes from the heading (`# IPD:`, `# Spec:`, `# Release:`, ...) or from the records directory in the written path; f-string placeholders that stand for one field value become keyword arguments (`f"- Status: {status}\n"` becomes `status=status`); field names map to registry names through `artifact_meta.registry_fields` (no second table). The output lists, per module, every site with its line, its planned rewrite or refusal reason, and totals of rewrites and refusals by reason and by disposition. The dry run writes nothing. (Measured units: 1 tool module, 7 reason codes, 8 record types, 1 output format pair.)
  - Depends on: none
  - Expected outcome: `--dry-run --format json tests/test_backlog_handoff_close.py` prints one entry per site with a rewrite or a reason code, and `git status --short` is unchanged afterwards.
  - Execution state: pending
- [ ] E-02 Add the rewriter: `python3 tools/fixture_codemod.py --apply <paths>` replaces each planned-rewrite site's expression in place using the `ast` node's start and end offsets, adds one `from tests.record_builder import RecordBuilder` import when the module lacks it, and touches no refused site and no other byte of the module. A second `--apply` over the same files makes no change (idempotent). (Measured units: 1 rewrite routine, 1 import routine, 1 idempotence rule.)
  - Depends on: E-01
  - Expected outcome: on a fixture module, the diff of an `--apply` run touches only the planned sites and the import line, and a second run prints zero rewrites.
  - Execution state: pending
- [ ] E-03 Add the equivalence proof to `--apply`; it cannot be turned off. Before rewriting a module, the tool records its per-test outcome list with the batch-rule command (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <module> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort`, run in-process with `subprocess`), rewrites, and records it again. If the two lists differ, it restores the module, re-applies the rewrites by halving (each half kept only when the list stays identical) until the sites that change the outcome are isolated, keeps the proved rewrites, and reports each isolated site as a refusal `not-equivalent`. The report ends with the before and after outcome-list hashes per module. (Measured units: 1 proof routine, 1 bisection routine, 1 report section.)
  - Depends on: E-02
  - Expected outcome: on a fixture module whose test asserts the exact bytes of one literal, `--apply` keeps every other rewrite, reports that one site `not-equivalent`, and the module's outcome list is identical before and after.
  - Execution state: pending
- [ ] E-04 Add `tests/test_fixture_codemod.py` and fixture modules under `tests/fixtures/fixture_codemod/`. Tests drive the tool as a subprocess on copies of the fixtures in a temporary repository made with `tests/support.py` `init_repo` and assert on its output and on the rewritten files: (a) a plain constant metadata block becomes a builder call; (b) an f-string with field placeholders becomes keyword arguments; (c) an invalid value goes through `raw_fields=` and is listed `invalid-input`; (d) one fixture per refusal reason code produces exactly that code and leaves the site byte-identical; (e) `--dry-run` writes nothing; (f) a second `--apply` changes nothing; (g) the `not-equivalent` case of E-03 is isolated and reverted while the other rewrites stay; (h) the rewritten fixture module's own tests pass. No test reads production source. If the module's wall time under `-n 0` exceeds 10 s (E-03 starts pytest subprocesses), the subprocess cases move to a second module listed in `tests/slow_allowlist.txt` and the core module keeps (a) to (f). (Measured units: 8 test groups, about 12 fixture modules.)
  - Depends on: E-03
  - Expected outcome: `python3 -m pytest -o addopts="" -n 0 -v tests/test_fixture_codemod.py` passes every case.
  - Execution state: pending

### Task group 2: pilot, census and finish

- [ ] E-05 Pilot and census. PILOT: in a throwaway `git worktree add .aw/state/653ndz/pilot HEAD`, run `--apply` on `tests/test_backlog_handoff_close.py`, `tests/test_check_engine.py` and `tests/test_status_set.py` (three families, chosen because F-01 ranks them among the densest), paste each module's before and after outcome-list hash (identical) and its rewrite and refusal totals, then remove the worktree; nothing from the pilot is committed. CENSUS: run `--dry-run --format json` over all 318 batch modules (the F-01 `rg -l` list minus the 5 EXCLUDED files, saved as `.aw/state/653ndz/census-files.txt`) and write two tracked tables into this plan's Findings: F-30, one row per module (module, batch subset id from F-32, sites, rewrites, `invalid-input` rewrites, refusals by reason code, `hand` total, `legacy-kept` total), generated by the tool's `--census-markdown` output rather than typed; and F-31, one row per batch subset (G1a, G1b, G2a, G2b, G3a, G3b, G4a, G4b, G4c, G5a, G5b, G6a, G6b, G6c, G7a, G7b) with the same totals summed and the carrying plan's id6. The dry run is static, so F-31 cannot contain apply-time `not-equivalent` refusals; each batch item adds those to its own `hand` count. Any subset whose F-31 `hand` total exceeds 25 is named in F-31's last column as "re-split before approval". (Measured units: 3 pilot modules, 1 census run over 318 modules generated mechanically, 2 tables.)
  - Depends on: E-04
  - Expected outcome: three identical pilot hash pairs; F-30 has 318 rows and F-31 has 16 rows whose site totals equal F-30's; every over-25 subset is flagged.
  - Execution state: pending
- [ ] E-06 Finish: add a `tools/fixture_codemod.py` section to `tools/README.md` (purpose, the three modes, the reason-code table, the rule that `--apply` always proves); run `tests/test_fixture_codemod.py` and the bare core gate `python3 -m pytest`, and `aw sanitize --agent`; commit through `aw commit 653ndz -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-05
  - Expected outcome: all runs pass; F-30 and F-31 are committed in this plan; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Standalone maintenance tools live in `tools/` and are described in `tools/README.md`; their behavioral tests drive them as subprocesses by path (for example `tests/test_gate_drop_audit.py` sets `AUDITOR_PATH` to `tools/gate_drop_audit.py`).
- The builder interface (`9rgn2w` E-01): `RecordBuilder(repo_root)` with one method per record type, registry-named keyword fields, `raw_fields={legacy_name: text}` for deliberately invalid input, and `text_only=True` returning the string.
- `artifact_meta.registry_fields(type)` names each type's fields; `artifact_meta.read_text(text, *, record_type=None)` parses a record's text.
- Tests are behavioral (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the codemod reads TEST source because rewriting it is its job, and no test of the codemod reads production source. Core modules set `pytestmark = pytest.mark.core`; `slow` tests are listed in `tests/slow_allowlist.txt`; a complete comparison passes `-m ""`, and a deterministic order needs `-p no:randomly`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-08 at `ac76110f4`.

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -c --glob '*.py' -e '- (Id\|Status\|Set\|Kind\|Blocks-Release\|Readiness\|Item-Dependencies\|Scope-Paths\|From-Backlog\|From-Spec\|Work-Kind\|Priority\|Order\|Date\|Gate-Kind\|Gate-Ref\|Approval\|Subject-Id\|Verdict\|Graduated-To):\|## Workflow history' tests`: 323 files; minus the 5 EXCLUDED `tests/test_artifact_meta_*.py` files, 318 modules with 6,747 matching lines | The census input. It includes `tests/support.py` and `tests/conformance_matrix.py` (subset G7b, `59aiyh` E-09). |
| F-29 | An `ast` walk over the 318 modules (string constants and f-strings whose text matches F-01, nested f-string parts not double-counted): 3,272 sites in 313 modules; by context: `write_text` argument 867, assigned or returned 882, argument of another call 930, inside an assertion 535, other 58 | About 1,750 sites sit in a write or an assignment, the shapes a rewrite handles; the 535 assertion sites are refusals by construction (`displayed-output` or `setter-byte`). The number of `dynamic-construction` refusals is unknown until E-05. |
| F-30 | (written by E-05) per-module census | Cited by every batch item. |
| F-31 | (written by E-05) per-subset census | Cited by every batch item as its `hand` count. |
| F-32 | Batch subsets and their carrying plans after the 2026-11-08 restructuring: G1a, G1b, G2a, G2b `x05v02`; G3b, G4a, G4b, G4c `7qxey9`; G5b, G6a, G6b, G6c `nbfg7w`; G3a, G5a, G7a `1upea0`; G7b `59aiyh` E-09 | E-05 labels each F-30 row with its subset from the module lists named in those items. |

## Proposed changes (ordered, validatable)

1. Build the detector and dry run, the rewriter, and the proof (E-01 to E-03).
2. Test the tool (E-04).
3. Pilot on three real modules, then run the census (E-05).
4. Document, run the gates, commit (E-06).

## Deferred / out of scope (with reason)

- Converting the batch modules on `main`: the batch plans run this tool.
  - Carrier: x05v02
- The setter-byte assertion helper and its conversions.
  - Carrier: iog3cw

## Scope check

- Over-scope: none. No production module under `agent_workflows/` changes; the pilot's conversions are discarded.
- Under-scope: none known. Size: 6 E-items in 2 task groups, 6 Scope-Paths entries; per-item units are listed in each item, none above about 16.

## Required tests / validation

New test module `tests/test_fixture_codemod.py` (behavioral: subprocess runs over fixture modules, asserting output and rewritten bytes). The pilot proves equivalence on real modules by outcome-list identity. Commands: `tests/test_fixture_codemod.py`, the bare core gate `python3 -m pytest`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change; `tools/README.md` gains the tool's section (E-06). Implements the tooling half of `4sd62s` section 7 step 6.

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

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 tools/fixture_codemod.py --dry-run --format table tests/test_backlog_handoff_close.py` output listing every site with a planned rewrite or a reason code and the per-disposition totals, and `git status --short` before and after showing no change.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` of one fixture module after `--apply` (only planned sites and the import line changed) and the second `--apply` run's output reporting zero rewrites.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `--apply` report for the `not-equivalent` fixture module showing the isolated site, the kept rewrites, and identical before and after outcome-list hashes.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_fixture_codemod.py` with every case (a) to (h) PASSED and the total duration (under 10 s, or the moved slow module named in `tests/slow_allowlist.txt` with its own PASSED run), and `rg -n "inspect\.|getsource" tests/test_fixture_codemod.py` empty.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the three pilot modules' before and after outcome-list hashes (each pair identical) with their rewrite and refusal totals and `git worktree list` showing the pilot worktree removed; `wc -l .aw/state/653ndz/census-files.txt` printing 318; F-30 (318 rows) and F-31 (16 rows) as written, with a one-line check that F-31's site total equals the sum of F-30's; and every subset flagged "re-split before approval".
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the `tools/README.md` diff, the `tests/test_fixture_codemod.py` run, the bare `python3 -m pytest` summary line and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit 653ndz` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `9rgn2w`, `g5hpbb`, `tve77h` and `xexn45` are executed. OQ-01 and OQ-02 are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` is out of this plan's purpose: if the builder's text form cannot express a shape, the site is refused, and the builder is not changed here.

Honesty rule: run the tool, its tests, the pilot and the bare `python3 -m pytest` core gate, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 653ndz -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
