# IPD: Build and prove the test-fixture codemod

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder (`tests/record_builder.py`, built by `9rgn2w`, Order 37) in phase B, so that the cutover (Order 13, `cxxmyv`) changes the builder and not hundreds of test files. Measured 2026-11-08 at `ac76110f4`: the F-01 `rg -c` pattern matches 6,747 lines in 318 batch modules (323 files minus the 5 EXCLUDED `tests/test_artifact_meta_*.py`); a Python `ast` walk over the same 318 files finds 3,272 string-literal sites (2,636 plain constants, 636 f-strings) that carry at least one legacy bullet or `## Workflow history`, of which 867 are the argument of a `write_text` call, 882 are assigned or returned, 930 are passed to another call and 535 sit inside an assertion. The batch plans (`x05v02`, `7qxey9`, `nbfg7w`, `1upea0`) each held items such as "convert these 17 modules, 738 lines" that hide hundreds of hand edits. Maintainer decision 2026-11-07 ("Codemod first, then small runs"): build a tested tool that performs the mechanical rewrite, and size each batch item by the tool's measured refusals, not by line counts.
- Scope: FINISHING PART after the round-3 split (2026-11-09, research `nj8zdp` guidance): the pilot and the census tables F-30 and F-31 (E-05) and the README section, gates and commit (E-06). The tool moved to `y3uowx`, its tests to `j2xjtt` and `n0li9v`. Before the round-3 split: A standalone tool `tools/fixture_codemod.py` with a static site detector, a dry run, an apply mode that rewrites only sites whose module outcome list it proved unchanged, its behavioral test module and fixtures, a throwaway pilot on three real modules, and a census over all 318 batch modules recorded as tracked Findings tables F-30 (per module) and F-31 (per batch subset) that the batch plans cite. EXCLUDES: converting any test module on `main` (the batch plans Orders 38 to 40, 50, and `59aiyh` E-09); the builder itself (`9rgn2w`); setter-byte assertion conversion (`iog3cw`, `w13bkp`, Orders 59 to 62); production code under `agent_workflows/`.
- Scope-Paths: tools/README.md, .aw/records/plans/pending/20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md
- Item-Dependencies: executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45, executed:y3uowx, executed:j2xjtt, executed:n0li9v
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

- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01, E-02, E-03 moved to y3uowx; E-04 moved to j2xjtt (cases a, b, c, e, f, g, h) and n0li9v (case d); kept E-05 and E-06.
- 2026-11-08 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): created per maintainer decision 2026-11-07 ("Codemod first, then small runs"); the batch plans x05v02, 7qxey9, nbfg7w and 1upea0 run this tool and hand-convert only its census refusals.

## Goal

After the round-3 split this plan pilots the finished tool and writes the census. The family goal: A tested `tools/fixture_codemod.py` rewrites inline legacy fixture text in test modules into `tests/record_builder.py` calls, never rewrites a site whose module outcome list it has not proved unchanged, and a tracked census tells each batch item exactly how many refusals it must convert by hand.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Split note (round 3, 2026-11-09, research `nj8zdp` guidance): items E-01, E-02 and E-03 moved to Order 172 (`y3uowx`) and E-04 to Orders 173 (`j2xjtt`) and 216 (`n0li9v`) with their ids; this plan keeps the pilot and census (E-05) and the finish (E-06).

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

### Task group 2: pilot, census and finish

- [ ] E-05 Pilot and census. PILOT: in a throwaway `git worktree add .aw/state/653ndz/pilot HEAD`, run `--apply` on `tests/test_backlog_handoff_close.py`, `tests/test_check_engine.py` and `tests/test_status_set.py` (three families, chosen because F-01 ranks them among the densest), paste each module's before and after outcome-list hash (identical) and its rewrite and refusal totals, then remove the worktree; nothing from the pilot is committed. CENSUS: run `--dry-run --format json` over all 318 batch modules (the F-01 `rg -l` list minus the 5 EXCLUDED files, saved as `.aw/state/653ndz/census-files.txt`) and write two tracked tables into this plan's Findings: F-30, one row per module (module, batch subset id and converting plan id6 from F-32, sites, rewrites, `invalid-input` rewrites, refusals by reason code, `hand` total, `legacy-kept` total), generated by the tool's `--census-markdown` output rather than typed; and F-31, one row per batch subset (G1a, G1b, G2a, G2b, G3a, G3b, G4a, G4b, G4c, G5a, G5b, G6a, G6b, G6c, G7a, G7b) with the same totals summed and the carrying plan's id6. The dry run is static, so F-31 cannot contain apply-time `not-equivalent` refusals; each batch item adds those to its own `hand` count. Any subset whose F-31 `hand` total exceeds 25 is named in F-31's last column as "re-split before approval". (Measured units: 3 pilot modules, 1 census run over 318 modules generated mechanically, 2 tables.)
  - Depends on: none
  - Expected outcome: three identical pilot hash pairs; F-30 has 318 rows and F-31 has 16 rows whose site totals equal F-30's; every over-25 subset is flagged.
  - Execution state: pending

- [ ] E-06 Finish: add a `tools/fixture_codemod.py` section to `tools/README.md` (purpose, the three modes, the reason-code table, the rule that `--apply` always proves); run `tests/test_fixture_codemod.py` (written by Orders 173 and 216) and the bare core gate `python3 -m pytest`, and `aw sanitize --agent`; commit through `aw commit 653ndz -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
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
| F-32 | Batch subsets and their carrying plans after the 2026-11-08 restructuring: G1a, G1b, G2a, G2b `x05v02`; G3b, G4a, G4b, G4c `7qxey9`; G5b, G6a, G6b, G6c `nbfg7w`; G3a, G5a, G7a `1upea0`; G7b `59aiyh` E-09. Round-3 split 2026-11-09: each of those plans now keeps at most 8 of its modules and names the chunk plan (Orders 175 to 212) of every other module in its own table F-41; F-30 labels each row with the subset AND the plan that converts it, read from those F-41 tables | E-05 labels each F-30 row with its subset from the module lists named in those items. |

## Proposed changes (ordered, validatable)

1. Pilot on three real modules, then run the census (E-05).
2. Document, run the gates, commit (E-06).

## Deferred / out of scope (with reason)

- Moved to y3uowx (round-3 split 2026-11-09 per research nj8zdp guidance): E-01 (detector and dry run), E-02 (rewriter), E-03 (equivalence proof).
  - Carrier: y3uowx
- Moved to j2xjtt (round-3 split 2026-11-09 per research nj8zdp guidance): E-04 test cases (a), (b), (c), (e), (f), (g), (h) and the 10 s bound.
  - Carrier: j2xjtt
- Moved to n0li9v (round-3 split 2026-11-09 per research nj8zdp guidance): E-04 test case (d), one fixture per refusal reason code.
  - Carrier: n0li9v
- Converting the batch modules on `main`: the batch plans run this tool.
  - Carrier: x05v02
- The setter-byte assertion helper and its conversions.
  - Carrier: iog3cw

## Scope check

- Over-scope: none. No production module under `agent_workflows/` changes; the pilot's conversions are discarded.
- Under-scope: none known. Size after the round-3 split: 2 E-items, 1 work Scope-Path (`tools/README.md`).

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

Execute only after human approval (`Status: approved`) and after `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`, `y3uowx`, `j2xjtt`, `n0li9v` are executed. OQ-01 and OQ-02 are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` is out of this plan's purpose: if the builder's text form cannot express a shape, the site is refused, and the builder is not changed here.

Honesty rule: run the tool, its tests, the pilot and the bare `python3 -m pytest` core gate, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 653ndz -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
