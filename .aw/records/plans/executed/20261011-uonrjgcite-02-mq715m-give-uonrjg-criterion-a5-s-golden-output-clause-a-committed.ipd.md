# IPD: Give uonrjg criterion A5's golden-output clause a committed referent

- Date: 2026-10-11
- Kind: child
- Concern: Spec `uonrjg` criterion A5 says the emoji forms `⚠️` and `↩️` must not occur in "lifecycle constants or golden output", but "golden output" has no defined referent: plan `xtensb` covered it only by rendering, so an emoji-presentation glyph could land in a committed snapshot file with nothing failing, and a later reader will re-raise the same question (backlog `0rnvj6`).
- Scope: Amend A5 in spec `uonrjg` so "golden output" is defined as BOTH the rendered output of the shared lifecycle helpers at every tier and Unicode mode AND every committed golden fixture file under `tests/`; extend the existing A5 test to scan the committed golden corpus so the second half is asserted, including any lifecycle snapshot corpus added later. No production code, renderer, glyph, or mapping changes.
- Scope-Paths: .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, tests/test_lifecycle_style.py
- Item-Dependencies: executed:xtensb
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: 0rnvj6
- From-Spec: uonrjg
- Set: uonrjgcite
- Order: 2
- Highest E allocated: 04
- Author: aw oc run model=agent
- Id: mq715m

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: mq715m verified (set uonrjgcite, attempt 2).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-12 draft (aw oc run model=agent): created.
- 2026-10-12 to-review (aw oc run model=agent): authored from backlog `0rnvj6` (raised as `xtensb` OQ-01); both closing routes the item names are combined: A5 is amended to define "golden output", and the committed golden corpus that already exists is scanned so the definition is asserted rather than only stated.

## Goal

Close the open question `xtensb` OQ-01 left behind, so criterion A5 means one checkable thing. The item
offers two closing routes: rule that rendered output is the whole obligation, or add a corpus and assert
over it. This plan takes both halves of that choice at once because the repository already has the second
route's surface: a committed golden corpus exists at `tests/fixtures/conformance_goldens/` (12 `*.golden`
files, pinned by `tests/test_cli_quality_gates.py`). It is not a lifecycle-row corpus today, but it IS
committed golden output that renders human glyphs. Scanning every committed `*.golden` file under `tests/`
costs one test, binds any lifecycle snapshot corpus added later automatically, and lets A5's text say
plainly what it covers.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Assert A5 over the committed golden corpus

- [x] E-01 In `tests/test_lifecycle_style.py`, add a test method to the existing class `CriterionA5VariationSelectorTests`. It discovers every committed golden fixture by globbing `**/*.golden` under the repository's `tests/` directory, reads each as UTF-8, and asserts that neither emoji-presentation sequence occurs: `"\u26a0\ufe0f"` (`⚠️`) and `"\u21a9\ufe0f"` (`↩️`). The failure message must name the offending file and the sequence. Put the discovery root in a module-level constant (for example `_GOLDEN_SCAN_ROOT = Path(__file__).resolve().parent`) so the counterfactual in V-01 can redirect it with `mock.patch.object` rather than writing a bad file into the real tree.
  NON-VACUITY: the test must also assert that it found AT LEAST ONE golden file, so a renamed or moved corpus fails loudly instead of the scan silently passing over nothing. Do NOT pin the count (12 at authoring): a count bar is the structure-pinning P16 forbids, and it would fail on every legitimate golden added or removed.
  NOT CODE-PINNING: the scanned files are committed TEST FIXTURES, i.e. the golden output A5 names, and not production source. This reads no `agent_workflows/` file and uses no `inspect` or `ast` (`AGENTS.md` execution contract; `GUIDING_PRINCIPLES` P16).
  READ THE ROOT AT CALL TIME: the test body must reference the module global (e.g. `_GOLDEN_SCAN_ROOT.glob("**/*.golden")` inside the method), never a default argument or class attribute bound at import, or the V-01 `mock.patch.object` counterfactual silently scans the real tree.
  SCAN BOTH SPELLINGS OF EACH SEQUENCE. `JsonRenderer.render` (`agent_workflows/renderers.py`) calls `json.dumps(result.to_dict(), indent=2)` with the default `ensure_ascii=True`, so an emoji reaching a `*.json.golden` is committed as the ASCII text `\u26a0\ufe0f` (backslash-u escapes), never as the literal code points (measured at review: `json.dumps("\u26a0\ufe0f")` prints `"\u26a0\ufe0f"`). A literal-only scan is therefore blind to one third of the corpus. For each file assert neither the literal sequence nor its JSON escape form occurs, comparing the escape form case-insensitively (`text.lower()` against `"\\u26a0\\ufe0f"` and `"\\u21a9\\ufe0f"`), since a JSON encoder may emit upper-case hex.
  SCAN ONLY THE TWO EMOJI SEQUENCES, not a bare `U+FE0F`. A5 names `⚠️` and `↩️`; a blanket `U+FE0F` ban over fixture files would be a new requirement the spec does not state, and an unrelated fixture could legitimately carry one.
  - Depends on: none
  - Expected outcome: a committed golden fixture containing `⚠️` or `↩️`, either as literal code points or as a JSON `\uXXXX` escape pair, fails the suite with the file named, and an empty or vanished corpus fails rather than passing vacuously.
  - Execution state: performed

### Task group 2: Amend A5 so the obligation is stated

- [x] E-02 In the spec, amend criterion A5 (the line beginning "- **A5** `⚠️` and `↩️` do not occur in lifecycle constants or golden output.") by appending a definition, without changing the criterion's requirement: "golden output" means (a) the output of the shared lifecycle renderers `Term.format_lifecycle_marker` and `Term.style_lifecycle_text` for every stage in `lifecycle_style.STAGE_ORDER` at all three color depths and both Unicode modes, and (b) every committed golden fixture file (`*.golden`) under `tests/`, matched both as literal code points and as their JSON `\uXXXX` escape form (the JSON goldens are written ASCII-escaped), which today is the `tests/fixtures/conformance_goldens/` corpus and which automatically includes any lifecycle snapshot corpus added later provided it uses the `.golden` suffix. Cite the asserting tests by CLASS name (`tests/test_lifecycle_style.py` `CriterionA5VariationSelectorTests`), not by line. State in one sentence that this closes `xtensb` OQ-01 / backlog `0rnvj6` so a later reader does not re-raise it, and that a future snapshot corpus using a different suffix must either adopt `.golden` or extend this clause.
  - Depends on: E-01
  - Expected outcome: A5 names its two referents and the test that asserts each, and its requirement (the two sequences must not occur) is unchanged.
  - Execution state: performed

- [x] E-03 Record the amendment with `aw specs note <spec path> --message <msg>` (the verb takes a PATH), in one note naming plan `mq715m` and backlog `0rnvj6`, stating WHAT changed (A5 gained a definition of "golden output" with two referents; a committed-golden scan was added) and WHAT did not (no criterion requirement, stage, color, glyph, or mapping). Use `aw specs note`, NOT `aw specs set`: the spec is `approved` and release-gating, and `xtensb` E-06 records the same reasoning. Do not hand-edit `## Workflow history`.
  - Depends on: E-02
  - Expected outcome: the spec's history records the amendment through the tooled path, and its `- Status:` stays `approved`.
  - Execution state: performed

### Task group 3: Whole-change validation

- [x] E-04 Run the whole-change gate: bare `python3 -m pytest` (the spec is parsed by `tests/test_lifecycle_style.py` for its Section 5 table and by `check_engine`'s criteria-coverage rule, so a malformed edit can fail tests far from this plan), `aw check`, `git diff --check`, and `aw ipd lint --phase pre-transition` on this plan. Inspect the staged set before committing and confirm it is exactly the two `Scope-Paths` entries; commit through `aw commit mq715m -- <paths>`. The plan file's own E/V state edits are not part of that commit; they travel with the lifecycle transition.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the full fast suite and repository checks pass with no regression against a baseline measured on the same HEAD before editing, the plan lints conforming, and the commit contains only the two declared paths.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (`AGENTS.md`, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE
  IT"). The spec file is in `- Scope-Paths:` so both runners announce the edit and finalize reconciles it.
- NO CODE-PINNING TESTS (`AGENTS.md` execution contract; `GUIDING_PRINCIPLES` P16). The new scan reads
  committed test fixtures, which are the artifact A5 names; it reads no production source.
- A SPEC AMENDMENT IS RECORDED WITH `aw specs note`, not `aw specs set` and not a hand edit (precedent:
  `xtensb` E-06, and the spec's own history line dated 2026-10-08).
- GOLDENS ARE REGENERATED DELIBERATELY: `tests/test_cli_quality_gates.py` rewrites them only under
  `AW_CONFORMANCE_UPDATE_GOLDENS=1` (its `_read_or_write_golden`). So a regenerated golden that picked up
  an emoji glyph is exactly the path the new scan guards: the regeneration passes its own byte gate by
  construction, and only an independent content assertion can catch it.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at authoring HEAD `cddecbc12`.

- F1. A COMMITTED GOLDEN CORPUS EXISTS, CONTRARY TO THE ITEM'S PREMISE AS WORDED. The item says "No
  committed lifecycle golden-file corpus exists to scan". That is true of LIFECYCLE ROWS specifically, but
  `find tests -name '*.golden'` returns 12 files, all under `tests/fixtures/conformance_goldens/`
  (`check_findings`, `error_cannot_run`, `mutation_preview`, `read_clean`, each in `.agent`, `.human`,
  `.json`). No `*.snap` or `*snapshot*` corpus exists anywhere under `tests/`.
- F2. THAT CORPUS IS CLEAN TODAY. A UTF-8 scan of all 12 files for `"\u26a0\ufe0f"`, `"\u21a9\ufe0f"`, and
  bare `"\ufe0f"` returned False for every file and every sequence. Re-measured at review (HEAD
  `613ce0471`): same result, and no golden contains any `\u` escape text at all, so the JSON-escape arm
  E-01 adds is also clean. So E-01's new assertion passes at HEAD and needs no fixture change.
- F3. IT DOES RENDER HUMAN GLYPHS. `read_clean.human.golden` begins "✓ CONFORMS  repository is current",
  the `✓` coming from `term`'s role glyph table (the `"ok": "✓"` row). These are command-outcome role
  glyphs, which spec A18 keeps independent of lifecycle, but they are the same glyph family a lifecycle
  regression would leak through, which is why scanning the whole corpus rather than a lifecycle-only
  subset is the right fence.
- F4. THE EXISTING A5 GUARD COVERS ONLY THE RENDERED HALF. `CriterionA5VariationSelectorTests` (added by
  `xtensb` E-04) asserts constants, `MULTI_CODEPOINT_GLYPHS`, and rendered output across depths and modes;
  it reads no committed file. Baseline: `python3 -m pytest tests/test_lifecycle_style.py
  tests/test_cli_quality_gates.py` reported `29 passed` at authoring (context only; re-derive before
  editing).
- F5. THE ONLY EMOJI WARNING FORM IN THE PACKAGE IS OUT OF SCOPE. `agent_workflows/engine.py` carries
  "⚠️ **DO NOT EDIT THESE FILES MANUALLY.**" in a generated-README string, which `xtensb` F5 already ruled
  not a lifecycle constant. It is not a golden fixture either, so E-01 does not reach it, correctly.

## Proposed changes (ordered, validatable)

1. Add the committed-golden scan to `CriterionA5VariationSelectorTests` (E-01).
2. Amend A5 to define "golden output" with its two referents and the test asserting each (E-02).
3. Record the amendment with `aw specs note` (E-03).
4. Run the whole-change gate and commit the two declared paths (E-04).

## Deferred / out of scope (with reason)

- CREATING A LIFECYCLE-ROW SNAPSHOT CORPUS. Not needed to close the question: the item's concern is that a
  FUTURE corpus would be unguarded, and E-01 guards any future `*.golden` corpus automatically. Building one
  now would be new test infrastructure no criterion requires.
  - Carrier-Declined: nothing is outstanding. The risk the item names (an emoji glyph entering a committed snapshot unguarded) is closed by E-01 for every `.golden` file present or future, and E-02 records the suffix condition so a corpus using another suffix is told to extend the clause.
- BANNING BARE `U+FE0F` IN FIXTURES. A5 names two sequences; widening it to a blanket ban is a new
  requirement, and requirements are not changed by this plan.
  - Carrier-Declined: nothing is outstanding. No defect motivates the wider ban (F2 measured zero occurrences), and inventing a requirement in an approved spec is a maintainer decision this item did not ask for.
- `tests/test_cli_quality_gates.py` IS NOT EDITED. The scan belongs beside the A5 guard it extends; the
  golden byte gate is untouched.
  - Carrier-Declined: nothing is outstanding. The byte gate already pins the goldens; this plan adds an independent content assertion in the lifecycle test file and needs no change there.

## Scope check

- Over-scope: none. Two paths: the spec (A5 definition, E-02, E-03) and `tests/test_lifecycle_style.py`
  (the scan, E-01).
- Under-scope: a future snapshot corpus that does NOT use the `.golden` suffix would escape the scan. E-02
  states that condition inside A5 itself, so the obligation to extend is recorded where a corpus author
  reads it rather than left implicit.

## Required tests / validation

- `python3 -m pytest tests/test_lifecycle_style.py -o addopts=""` for the extended A5 class with real
  per-test counts.
- `python3 -m pytest tests/test_lifecycle_style.py tests/test_cli_quality_gates.py tests/test_term.py
  tests/test_check_engine_spec_criteria.py` for the golden gate, lifecycle surface, and criteria-coverage
  neighbours.
- Bare `python3 -m pytest` for the full fast suite.
- `aw check` and `aw ipd lint --phase pre-transition` on this plan.
- The counterfactual in V-01 proving the scan bites, and the vacuity check proving an empty corpus fails.

## Spec / documentation sync

- `.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`
  is AMENDED by E-02 and declared in `Scope-Paths`. WHY: A5 is a release-gating criterion whose second
  clause has no stated referent, and the gap has already cost one open question (`xtensb` OQ-01) and one
  backlog item (`0rnvj6`). Defining the referent in the criterion, beside the test that asserts it, is what
  stops it being re-raised. The requirement itself (the two emoji sequences must not occur) is unchanged;
  only its coverage is stated. The spec's `- Status:` is NOT touched (E-03).
- No user-facing docs change.

## Open questions

### OQ-01: Which of the item's two closing routes should be taken?

- Blocking: no
- Status: resolved
- Owner: plan author (confirmed by /plan-review 2026-10-12, review decision D-1)
- Resolution or deferral rationale: BOTH, resolved from repository evidence. The item offers "a ruling that
  the rendered-output assertion is the whole of A5's 'golden output' obligation" OR "the addition of a
  lifecycle snapshot corpus together with an A5 assertion over it". F1 shows a committed golden corpus
  already exists, so the assertion half needs no new corpus, and scanning it is cheap, reversible, and
  covers future corpora. Ruling rendered output alone to be the whole obligation would leave the exact
  hole the item describes (a regenerated golden picking up `⚠️` with nothing failing, see the
  `_read_or_write_golden` convention above). A reviewer who prefers the narrower ruling can drop E-01 and
  shorten E-02's definition to referent (a). `/plan-review` (2026-10-12) kept both: the scan is one
  reversible test over committed fixtures, and the narrower ruling leaves the regeneration hole open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the new test's node id and the `python3 -m pytest tests/test_lifecycle_style.py -o addopts=""` output showing it passing with the real count. Then paste TWO scratch counterfactuals run in-process with `unittest.mock.patch.object` on the discovery-root constant (no edit left on disk, confirmed by `git status --short` pasted afterwards): (1) the root redirected to a temp directory holding one `x.golden` containing `"\u26a0\ufe0f"`, showing the test FAILS and its message names `x.golden`; repeat with `"\u21a9\ufe0f"`; (1b) the root redirected to a temp directory holding one `x.json.golden` whose content is `json.dumps("\u26a0\ufe0f")` (the ASCII escape text, confirmed by pasting the file bytes), showing the test FAILS and names `x.json.golden`; (2) the root redirected to an empty temp directory, showing the test FAILS on the non-vacuity assertion. Paste the diff hunk proving the test reads only `*.golden` files under `tests/` and imports nothing from `inspect` or `ast`.
  - Observed evidence:
    Node id: `tests/test_lifecycle_style.py::CriterionA5VariationSelectorTests::test_committed_golden_fixtures_contain_no_emoji_variation_selector`
    ```
    $ python3 -m pytest tests/test_lifecycle_style.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3573627366
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 2 items                                                             collected 16 items

    tests/test_lifecycle_style.py ................                           [100%]

    ============================== 16 passed in 2.34s ==============================
    ```
    In-process counterfactuals run via scratch script with `mock.patch.object`:
    ```
    === Counterfactual 1a: \u26a0\ufe0f ===
    AssertionError as expected:
     '⚠️' unexpectedly found in 'prefix ⚠️ suffix' : Committed golden fixture x.golden contains emoji presentation sequence '⚠️'

    === Counterfactual 1a (repeat): \u21a9\ufe0f ===
    AssertionError as expected:
     '↩️' unexpectedly found in 'prefix ↩️ suffix' : Committed golden fixture x.golden contains emoji presentation sequence '↩️'

    === Counterfactual 1b: json.dumps("\u26a0\ufe0f") ===
    File bytes: b'"\\u26a0\\ufe0f"'
    AssertionError as expected:
     '\\u26a0\\ufe0f' unexpectedly found in '"\\u26a0\\ufe0f"' : Committed golden fixture x.json.golden contains JSON escaped emoji sequence '\\u26a0\\ufe0f'

    === Counterfactual 2: empty temp directory ===
    AssertionError as expected:
     [] is not true : No *.golden fixture files found under /tmp/tmpgfasyuec; corpus moved or vanished?
    ```
    Confirmed no edit left on disk:
    ```
    $ git status --short
    # (no untracked files)
    ```
    Diff hunk for `tests/test_lifecycle_style.py` showing only `*.golden` discovery under `tests/` and no `inspect` or `ast` imports:
    ```diff
    @@ -38,6 +38,7 @@ SPEC_PATH = next(
             "20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md"
         )
     )
    +_GOLDEN_SCAN_ROOT = Path(__file__).resolve().parent

     # The five prompt LANES. Prompt status is carried by DIRECTORY, not by an enum: `prompts.py` defines
     # only `DEFAULT_STATUS` and `PROMPT_KINDS`, so there is no `prompts.STATUSES` to enumerate (plan
    @@ -567,6 +568,34 @@ class CriterionA5VariationSelectorTests(unittest.TestCase):
                             f"style_lifecycle_text carries U+FE0F for {stage} (depth={depth}, unicode={unicode_mode})",
                         )

    +    def test_committed_golden_fixtures_contain_no_emoji_variation_selector(
    +        self,
    +    ):
    +        golden_files = sorted(_GOLDEN_SCAN_ROOT.glob("**/*.golden"))
    +        self.assertTrue(
    +            golden_files,
    +            f"No *.golden fixture files found under {_GOLDEN_SCAN_ROOT}; corpus moved or vanished?",
    +        )
    +
    +        banned_literal_sequences = ("\u26a0\ufe0f", "\u21a9\ufe0f")
    +        banned_escaped_sequences = ("\\u26a0\\ufe0f", "\\u21a9\\ufe0f")
    +
    +        for golden_file in golden_files:
    +            text = golden_file.read_text(encoding="utf-8")
    +            for seq in banned_literal_sequences:
    +                self.assertNotIn(
    +                    seq,
    +                    text,
    +                    f"Committed golden fixture {golden_file.name} contains emoji presentation sequence {repr(seq)}",
    +                )
    +            text_lower = text.lower()
    +            for esc in banned_escaped_sequences:
    +                self.assertNotIn(
    +                    esc,
    +                    text_lower,
    +                    f"Committed golden fixture {golden_file.name} contains JSON escaped emoji sequence {repr(esc)}",
    +                )
    +
     class CriterionA19WorkKindIndependenceTests(unittest.TestCase):
         """Spec uonrjg criterion A19: work-kind has no effect on lifecycle resolution or presentation."""
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff` of the spec showing the A5 line's requirement text unchanged and the appended definition naming referents (a) and (b), the class `CriterionA5VariationSelectorTests`, the `.golden` suffix condition, and the closing reference to `xtensb` OQ-01 / backlog `0rnvj6`. Paste `grep -noE '[A-Za-z_/.-]+\.(py|md|json):[0-9]+' ` over the amended A5 block showing it introduces no bare line-offset citation.
  - Observed evidence:
    Spec diff for A5 block:
    ```diff
    @@ -810,6 +811,16 @@ through the merge-and-revalidate gate. Those four are ordinary rebase friction a
     - **A4** Blocked renders with text-form `⚠︎`; failed renders with `✘`; retry or recovery renders with
       text-form `↩︎`; reusable renders with `↻`.
     - **A5** `⚠️` and `↩️` do not occur in lifecycle constants or golden output.
    +  "golden output" means (a) the output of the shared lifecycle renderers
    +  `Term.format_lifecycle_marker` and `Term.style_lifecycle_text` for every stage in
    +  `lifecycle_style.STAGE_ORDER` at all three color depths and both Unicode modes, and (b) every
    +  committed golden fixture file (`*.golden`) under `tests/`, matched both as literal code points and
    +  as their JSON `\uXXXX` escape form (the JSON goldens are written ASCII-escaped), which today is the
    +  `tests/fixtures/conformance_goldens/` corpus and which automatically includes any lifecycle snapshot
    +  corpus added later provided it uses the `.golden` suffix. Both referents are asserted by class
    +  `CriterionA5VariationSelectorTests` in `tests/test_lifecycle_style.py`. This closes `xtensb` OQ-01 /
    +  backlog `0rnvj6` so a later reader does not re-raise it, and a future snapshot corpus using a
    +  different suffix must either adopt `.golden` or extend this clause.
     - **A6** In artifact-only views, plans display draft through approved as `○`, `◔`, `◑`, and `◕`, then
       executed as `✓`.
     - **A7** A live executing approved plan displays `▶` and the word `executing` without changing the plan's
    ```
    No bare line-offset citations in amended A5 block:
    ```
    $ sed -n '812,826p' .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md | grep -noE '[A-Za-z_/.-]+\.(py|md|json):[0-9]+'
    # (no matches found, exit code 1)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the exact `aw specs note` command and its output, and the resulting new line in the spec's `## Workflow history` naming `mq715m` and `0rnvj6`. Paste the spec front-matter diff (or its absence) proving `- Status: approved` and `- Blocks-Release: next` are unchanged.
  - Observed evidence:
    `aw specs note` command and resulting history line:
    ```
    $ aw specs note .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md --message "AMENDED 2026-10-13 (plan mq715m / backlog 0rnvj6): A5 gained a definition of 'golden output' with two referents (the rendered output of shared lifecycle renderers across stages, depths, and modes, and every committed *.golden fixture under tests/ matched both as literal code points and JSON \uXXXX escapes); a committed-golden scan was added to tests/test_lifecycle_style.py CriterionA5VariationSelectorTests; no criterion requirement, stage, color, glyph, or mapping changed."
    noted .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md

    Recorded in spec history:
    - 2026-10-13 note (aw specs): AMENDED 2026-10-13 (plan mq715m / backlog 0rnvj6): A5 gained a definition of 'golden output' with two referents (the rendered output of shared lifecycle renderers across stages, depths, and modes, and every committed *.golden fixture under tests/ matched both as literal code points and JSON \uXXXX escapes); a committed-golden scan was added to tests/test_lifecycle_style.py CriterionA5VariationSelectorTests; no criterion requirement, stage, color, glyph, or mapping changed.
    ```
    Front-matter diff is absent; header is unchanged:
    ```
    # Spec: Cross-artifact lifecycle symbols and ANSI status styling

    - Kind: spec
    - Date: 2026-09-13
    - Id: uonrjg
    - Status: approved
    - Blocks-Release: next
    - Approved-By: human (gabriele.fariello@gmail.com) via aw specs set (2026-09-13)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste bare `python3 -m pytest` output including the `N passed` summary line, with failures compared BY NAME against a baseline run on the same HEAD before editing (zero new failures). Paste `aw check` output, `git diff --check` (empty), `aw ipd lint --phase pre-transition` reporting conforming, and `git diff --cached --name-only` before the commit showing exactly the two `Scope-Paths` entries.
  - Observed evidence:
    Full test suite output:
    ```
    $ python3 -m pytest
    8064 passed, 4 skipped, 18 xfailed, 3 warnings in 893.98s (0:14:53)
    Zero failures compared by name against baseline.
    ```
    `aw check`:
    ```
    $ aw check
    Touched artifacts clean (all diagnostics are pre-existing issues elsewhere in repository).
    ```
    `git diff --check`:
    ```
    $ git diff --check
    # (empty, exit 0)
    ```
    `aw ipd lint --phase pre-transition`:
    ```
    $ aw ipd lint --phase pre-transition .aw/records/plans/pending/20261011-uonrjgcite-02-mq715m-give-uonrjg-criterion-a5-s-golden-output-clause-a-committed.ipd.md
    -    ◕  approved     plan        20261011-uonrjgcite-02-mq715m  [low]  conforming
    ```
    `git diff --cached --name-only` before commit:
    ```
    .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
    tests/test_lifecycle_style.py
    ```
    Committed in commit `1dd6f62c9d044a74bf1f6e621b0ef97f1a5f4c97`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. It is low-risk: one test
added, one approved spec criterion given a definition, no production code touched. The sensitive act is
amending an `approved`, release-gating spec, which `AGENTS.md` permits when declared in `Scope-Paths`, as
here; E-03 records it with `aw specs note` so the spec's `- Status:` never moves.

Execution contract:
- Open questions: OQ-01 is resolved; none are open.
- Scope fence: `- Scope-Paths:` is a declaration, not a stop condition. If an edit outside it proves
  necessary, make it and justify it at finalize with `--scope-reason <path>=<why>`; a declared path left
  unmodified needs `--scope-ack`.
- Commit only the two `Scope-Paths` entries through `aw commit mq715m -- <paths>`; never `git add -A`;
  never push. Verify the staged set before committing and re-verify after any failed commit.
- You MUST paste ACTUAL runner output; never claim a result you did not run, and do not mark a `V-*`
  `pass` from its E-item checkmark.
- Lifecycle: after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan moves
  to `executed/` through the tooled lifecycle, never a hand `git mv`. Under `aw oc run` / `aw agy run` the
  driver self-finalizes and the executor does NOT run `aw ipd finalize`; when executing by hand outside a
  runner, the executor runs `aw ipd finalize mq715m`.
